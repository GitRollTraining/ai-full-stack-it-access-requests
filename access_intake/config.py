"""Versioned, credential-free processing configuration."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / 'snapshot.schema.json').read_text())
POLICY_TEXT = (ROOT / 'materials/office-policy.md').read_text()
EXTRACTION_RULES = POLICY_TEXT.partition('## Review queue')[0]
PROMPT = (ROOT / 'access_intake/prompt.txt').read_text() + '\nSource extraction policy:\n' + EXTRACTION_RULES
DEFAULT_FIXTURES = ROOT / 'tests/fixtures/mock_responses.json'


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def configure(provider='mock', model='gpt-4o-mini-2024-07-18', timeout=45.0,
              max_attempts=3, concurrency=4, rpm=60.0, fixtures=None):
    if provider not in ('mock', 'openai'):
        raise ValueError('provider must be mock or openai')
    if timeout <= 0 or max_attempts < 1 or concurrency < 1 or rpm <= 0:
        raise ValueError('timeout, attempts, concurrency and rpm must be positive')
    fixture_path = str(Path(fixtures or DEFAULT_FIXTURES).resolve())
    extraction = dict(provider=provider, model=model, max_output_tokens=3000,
                      temperature=0, timeout=timeout, max_attempts=max_attempts,
                      endpoint='https://api.openai.com/v1/responses',
                      prompt_sha256=digest(PROMPT), schema_sha256=digest(SCHEMA),
                      validator_sha256=digest((ROOT / 'access_intake/validation.py').read_bytes()),
                      adapter_sha256=digest((ROOT / 'access_intake/providers.py').read_bytes()))
    if provider == 'mock':
        extraction.update(fixtures=fixture_path,
                          fixtures_sha256=digest(Path(fixture_path).read_bytes()))
    policy = digest([(ROOT / 'materials/office-policy.md').read_text(),
                     (ROOT / 'access_intake/policy.py').read_text()])
    return dict(extraction=extraction, extract_fp=digest(extraction), policy_fp=policy,
                concurrency=concurrency, rpm=rpm)


def refresh_config(config):
    e = config['extraction']
    return configure(e['provider'], e['model'], e['timeout'], e['max_attempts'],
                     config['concurrency'], config['rpm'], e.get('fixtures'))
