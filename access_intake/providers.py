"""OpenAI Responses API and explicit message-hash fixture replay."""
import copy
import json
import os
import socket
from pathlib import Path
import urllib.error
import urllib.request
from .config import SCHEMA, PROMPT, digest


class ProviderError(Exception):
    def __init__(self, code, retryable=False, retry_after=0):
        # No provider response text, credentials, source text or URLs in errors.
        super().__init__(code)
        self.retryable = retryable
        self.retry_after = retry_after


def request_body(message, document_id, config):
    e = config['extraction']
    return dict(model=e['model'], store=False, temperature=e['temperature'],
                max_output_tokens=e['max_output_tokens'], instructions=PROMPT,
                input=[dict(role='user', content=json.dumps(
                    dict(document_id=document_id, message=message)))],
                text=dict(format=dict(type='json_schema', name='access_snapshot',
                                      strict=True, schema=SCHEMA)))


def parse_response(response):
    if not isinstance(response, dict):
        raise ProviderError('malformed-response: expected object')
    if response.get('status') != 'completed' or response.get('error'):
        raise ProviderError('incomplete-response: retry or increase output budget')
    if not isinstance(response.get('output'), list):
        raise ProviderError('malformed-response: expected output array')
    texts = []
    for output in response['output']:
        if not isinstance(output, dict):
            raise ProviderError('malformed-response: output item')
        if output.get('type') != 'message':
            continue
        if output.get('status') != 'completed':
            raise ProviderError('interrupted-message: retry extraction')
        if not isinstance(output.get('content'), list):
            raise ProviderError('malformed-response: expected content array')
        for item in output['content']:
            if not isinstance(item, dict):
                raise ProviderError('malformed-response: content item')
            if item.get('type') == 'refusal':
                raise ProviderError('refusal: inspect source and retry if appropriate')
            if item.get('type') == 'output_text':
                texts.append(item.get('text'))
    if len(texts) != 1 or not isinstance(texts[0], str):
        raise ProviderError('malformed-response: expected one JSON text')
    try:
        return json.loads(texts[0])
    except (ValueError, TypeError):
        raise ProviderError('malformed-json: retry extraction') from None


class MockProvider:
    def __init__(self, config):
        self.fixtures = json.loads(Path(config['extraction']['fixtures']).read_text())

    def extract(self, message, document_id, config):
        fixture = self.fixtures.get(digest(message.encode()))
        if fixture is None:
            raise ProviderError('mock-fixture-missing: add a message-hash fixture or use openai')
        return parse_response(copy.deepcopy(fixture))


class OpenAIProvider:
    def extract(self, message, document_id, config):
        key = os.environ.get('API_KEY')
        if not key:
            raise ProviderError('API_KEY missing: set environment variable and retry')
        e = config['extraction']
        request = urllib.request.Request(e['endpoint'],
            data=json.dumps(request_body(message, document_id, config)).encode(),
            headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
            method='POST')
        try:
            with urllib.request.urlopen(request, timeout=e['timeout']) as response:
                data = json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                retry_after = min(300, max(0, float(exc.headers.get('Retry-After', 0))))
            except (ValueError, TypeError):
                retry_after = 0
            raise ProviderError(f'provider-http-{exc.code}: check service/configuration and retry',
                                exc.code in (408, 409, 429) or exc.code >= 500,
                                retry_after) from None
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
            raise ProviderError('provider-network-timeout: check connectivity and retry', True) from None
        except ValueError:
            raise ProviderError('provider-invalid-json: retry extraction') from None
        value = parse_response(data)
        if not isinstance(data.get('model'), str) or not data['model']:
            raise ProviderError('malformed-response: missing actual model identity')
        self.actual_model = data['model']
        return value


def make_provider(config):
    return MockProvider(config) if config['extraction']['provider'] == 'mock' else OpenAIProvider()
