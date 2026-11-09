"""Bounded, incremental workers with durable backoff and recoverable leases."""
import concurrent.futures
import json
import random
import time
from .config import refresh_config
from .policy import route
from .providers import ProviderError, make_provider
from .store import base_record
from .validation import validate, ValidationError


def process(store, job, provider_factory=make_provider):
    config = job['config']
    result = base_record(job, config)
    retry_delay = None
    try:
        if job['input_error']:
            raise ProviderError(job['input_error'])
        current = refresh_config(config)
        if current['extract_fp'] != config['extract_fp'] or current['policy_fp'] != config['policy_fp']:
            raise ProviderError('configuration-drift: run refresh before processing with changed code/policy/fixtures')
        if job['cached']:
            cached = json.loads(job['cached'])
            extraction = cached['extraction']
            result['response_source'] = cached['response_source']
            result['rerouted_from_revision'] = cached['revision_id']
        else:
            provider = provider_factory(config)
            extraction = provider.extract(job['message'], job['document_id'], config)
            if config['extraction']['provider'] == 'openai':
                result['response_source'] = 'openai:' + provider.actual_model
        extraction, findings = validate(extraction, job['message'], job['document_id'])
        status, owner, action = route(extraction, findings)
        result.update(extraction=extraction, status=status, owner=owner, next_action=action)
    except ProviderError as exc:
        result['error'] = str(exc)
        if exc.retryable and job['tries'] < config['extraction']['max_attempts']:
            retry_delay = max(exc.retry_after, min(60, 2 ** job['tries']) + random.random())
    except ValidationError as exc:
        result['error'] = 'invalid-extraction: ' + str(exc) + '; inspect source/configuration and retry'
    except Exception:
        # Unexpected errors are isolated and sanitized. History preserves source and
        # configuration for reproduction; arbitrary exception strings may contain secrets.
        result['error'] = 'internal-processing-error: inspect local configuration/files and retry'
    store.finish(job, result, retry_delay)


def run(store, concurrency=4, provider_factory=make_provider):
    if concurrency < 1:
        raise ValueError('concurrency must be positive')
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        active = set()
        while True:
            while len(active) < concurrency:
                job = store.claim()
                if job is None:
                    break
                active.add(pool.submit(process, store, job, provider_factory))
            if active:
                done, active = concurrent.futures.wait(active, timeout=0.1,
                    return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    future.result()
            elif not store.unfinished():
                return
            else:
                time.sleep(0.1)
