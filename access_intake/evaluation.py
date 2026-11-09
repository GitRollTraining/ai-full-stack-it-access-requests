"""Compare against a source-authored oracle; mock replay is not model accuracy."""
import json
from pathlib import Path
from .config import ROOT
from .providers import request_body
from .validation import validate


def evaluate(store, expected_path):
    expected = json.loads(Path(expected_path).read_text())
    records = {r['document_id']: r for r in store.snapshot()[1]}
    scalar_matches = route_matches = evidence_passes = 0
    mismatches = []
    for name, oracle in expected.items():
        record = records.get(name, {})
        facts = record.get('extraction') or {}
        for key, value in oracle['facts'].items():
            if key in facts and facts[key] == value:
                scalar_matches += 1
            else:
                mismatches.append(dict(document_id=name, field=key, expected=value, actual=facts.get(key), category='fact comparison; review source'))
        for key, value in oracle['route'].items():
            if record.get(key) == value:
                route_matches += 1
            else:
                mismatches.append(dict(document_id=name, field=key, expected=value, actual=record.get(key), category='routing error'))
        if record.get('extraction') and not record.get('error'):
            try:
                source = ROOT / ('examples' if name == 'PAR-001.json' else 'materials/requests') / name
                message = json.loads(source.read_text())['message']
                validate(facts, message, name)
                evidence_passes += 1
            except (ValueError, OSError):
                pass
    total_scalars = sum(len(v['facts']) for v in expected.values())
    total_routes = sum(len(v['route']) for v in expected.values())
    sources = sorted({r['response_source'] for r in records.values()})
    configs = {r['config'] for r in store.sources() if r['document_id'] in expected}
    lines = ['# Accuracy verification', '',
        'The oracle in `tests/fixtures/expectations.json` was authored from the 20 source messages and office policy before processing outputs. The fresh paraphrase is `examples/PAR-001.json`. The mock response table was authored separately and replayed by message SHA-256; the evaluator never reads mock fixtures.', '',
        'Mock comparisons check fixture replay, validation, routing and evaluation plumbing. They do **not** measure language-model accuracy or generalization. No live provider accuracy run was performed for the committed artifacts.', '',
        f'Observed response sources: {", ".join(sources)}.', '',
        f'Scalar exact matches: **{scalar_matches}/{total_scalars}**. Route exact matches: **{route_matches}/{total_routes}**. Schema/date/quote checks passed: **{evidence_passes}/{len(expected)}**.', '',
        'Comparison uses Python literal equality with no case, punctuation or whitespace normalization. All 12 scalar fields per expected document count, including nulls. Each of status, owner and next_action counts separately (3 per document). Missing documents, errors and missing fields count as mismatches, including expected nulls. Extra documents are excluded from the fixed denominator. Arrays are not in the scalar score; schema, nonempty literal quote provenance and date checks are reported separately.', '',
        'Every scalar mismatch is a factual discrepancy requiring source review, not automatically a hallucination: a different supported business-purpose excerpt can be factually correct while failing literal equality. Review each mismatch against the decoded message, record whether it is a factual error, acceptable alternate wording or unresolved, and report that adjudication separately. The mock observation below has no scalar discrepancies; this is not a factual-error rate for a model. Routing mismatches are policy errors. Quotes alone do not establish semantic entailment, and a human must review live results.', '',
        'Reproduce: `python -m access_intake --db .state/demo.sqlite3 accuracy` after intaking both supplied requests and the paraphrase. To measure live accuracy, use a separate database with `intake --provider openai`, intake the paraphrase with identical settings, and run this same command. It exits 1 on any mismatch or failed evidence check.', '',
        '## Independently expected facts', '',
        '| Document | Date / kind | Requester / team | System / environment / permission | Business purpose (literal excerpt) | Start / end | Manager | Expected route |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |']
    show = lambda v: 'null' if v is None else str(v).replace('|', '\\|').replace('\n', ' ')
    for name, oracle in expected.items():
        f, r = oracle['facts'], oracle['route']
        cells = [name + ' (stated ' + str(f['request_id']) + ')',
                 ' / '.join(show(f[k]) for k in ('request_date', 'kind')),
                 ' / '.join(show(f[k]) for k in ('requester', 'team')),
                 ' / '.join(show(f[k]) for k in ('system', 'environment', 'permission')),
                 show(f['business_purpose']), ' / '.join(show(f[k]) for k in ('start_date', 'end_date')),
                 show(f['manager']), ' / '.join(r[k] for k in ('status', 'owner', 'next_action'))]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', 'Critical source interpretations: IT-004 environment and IT-020 manager conflict without correction; IT-008 environment and IT-015 dates explicitly corrected; IT-006 override wins over all normal routes; IT-007 new permission is write and IT-019 new permission is read; IT-011 relative dates stay null; IT-014 reversed dates remain explicit; IT-016 retains IT-061 and clarifies mismatch; IT-005 withdrawal precedes missing-fact clarification.', '',
              '## Discrepancies', '', '```json', json.dumps(mismatches, indent=2), '```', '',
              '## Recorded configuration', '', '```json', json.dumps([json.loads(c) for c in sorted(configs)], indent=2), '```', '']
    return '\n'.join(lines), not mismatches and evidence_passes == len(expected)


def evidence(store, destination):
    sources = store.sources()
    if not sources:
        raise ValueError('intake at least one source first')
    row = sorted(sources, key=lambda r: r['document_id'])[0]
    config = json.loads(row['config'])
    observation = ('Mock replay; illustrative OpenAI HTTP request built by the production adapter. No live request sent.'
                   if config['extraction']['provider'] == 'mock' else
                   'Request reconstructed from persisted live configuration. This evidence command sends no request; inspect record provenance and errors for observed outcomes.')
    obj = dict(observation=observation,
        configuration=config,
        request=dict(method='POST', url=config['extraction']['endpoint'],
                     headers={'Authorization': 'Bearer <REDACTED:API_KEY>', 'Content-Type': 'application/json'},
                     body=request_body(row['message'], row['document_id'], config)),
        handling=dict(completion='Require completed response and completed message with exactly one JSON output_text.',
                      refusal='Refusal is an error; never route partial extraction.',
                      interrupted='Incomplete/interrupted/error responses are errors.',
                      malformed='Reject invalid JSON, schema keys/types/enums or nonliteral quotes.',
                      transient='HTTP 408/409/429/5xx and network errors use bounded persisted exponential backoff with jitter and capped Retry-After.',
                      credentials='API_KEY read at call time. Never stored; no provider response bodies in errors.',
                      failed_retry='Latest error is current; previous success remains in immutable attempt history.'))
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')
