# Northstar IT access-request intake

A Python CLI prepares a durable review queue from JSON message exports. It extracts facts, validates them, and routes requests to human reviewers under [the office policy](materials/office-policy.md). It never approves requests or provisions access.

Python **3.12**, SQLite and a local Linux filesystem are supported. Runtime and tests use only the standard library; `requirements.lock` records the empty third-party dependency set. Run commands from this repository root. There is no web server to install.

## Reproducible mock example

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock
python -m access_intake --db .state/demo.sqlite3 intake materials/requests examples
python -m access_intake --db .state/demo.sqlite3 queue
python -m access_intake --db .state/demo.sqlite3 show IT-004.json
python -m access_intake --db .state/demo.sqlite3 export --out deliverables
python -m access_intake --db .state/demo.sqlite3 accuracy
python -m access_intake --db .state/demo.sqlite3 evidence
python -m unittest discover -v
```

The mock provider replays handwritten Responses envelopes by SHA-256 of the decoded message, independently of filename/metadata. It supports only the 20 supplied messages and `examples/PAR-001.json`; unseen wording produces a visible `mock-fixture-missing` error. This is a reproducible development example, **not a model accuracy claim**. The separately authored source expectations are in `tests/fixtures/expectations.json`. The accuracy command exits 1 for mismatches, missing expected documents, extraction errors or failed evidence checks; command/argument errors exit 2. Intake itself exits 0 when the batch has finished even if individual records failed: inspect `queue` for document errors.

## OpenAI processing

Set the facilitator's `API_KEY` environment variable through your shell or secret manager. No other environment variables are required. Do not put credentials in source files, command arguments or committed `.env` files.

```bash
python -m access_intake --db .state/live.sqlite3 intake materials/requests examples --provider openai --model gpt-4o-mini-2024-07-18 --concurrency 4 --rpm 60 --timeout 45 --max-attempts 3
python -m access_intake --db .state/live.sqlite3 queue
python -m access_intake --db .state/live.sqlite3 accuracy --out .state/live-accuracy.md
```

The adapter uses HTTPS POST to `https://api.openai.com/v1/responses`, a pinned model snapshot by default, strict `text.format` JSON Schema, temperature 0, a 3,000-token output limit and `store: false`. `--model` accepts another Responses model supporting that configuration; availability depends on the account. The actual returned model ID is recorded on successful live results. The request format and refusal/incomplete handling follow [official OpenAI documentation](https://developers.openai.com/api/docs/guides/structured-outputs). Live service availability, costs, accuracy and throughput have **not** been measured. HTTP behavior is tested with a stub transport.

`--provider`, `--model`, `--timeout` (seconds), `--max-attempts`, `--concurrency`, `--rpm` and `--fixtures` are intake/refresh options. Defaults are mock, the model above, 45 seconds, 3 attempts, 4 workers and 60 requests/minute. `--fixtures` selects an alternate mock response file, never an accuracy oracle. The endpoint and output-token limit are deliberately fixed in `config.py`; changing them requires a configuration refresh. API_KEY is read at call time and never persisted. Operational errors contain fixed categories, HTTP status and remediation; they omit provider bodies and arbitrary exception text.

## Handover, recovery and updates

Enqueue first when operators want to run workers separately. Completed results are published independently; a second terminal can inspect the queue at any time.

```bash
python -m access_intake --db .state/live.sqlite3 intake materials/requests --provider openai --enqueue-only
python -m access_intake --db .state/live.sqlite3 run --concurrency 4
python -m access_intake --db .state/live.sqlite3 queue
python -m access_intake --db .state/live.sqlite3 history IT-001.json
python -m access_intake --db .state/live.sqlite3 retry IT-001.json
```

`run` resumes persisted pending work, waits for backoff, and recovers abandoned leases. It uses each revision's persisted model settings. Worker count is a per-process cap, controlled by `run --concurrency`. Overlapping processes on one host may share the same database; claims and a provider-wide requests/minute gate are transactional. More worker processes increase aggregate concurrent calls, so operators should agree on their combined concurrency. The rate gate spaces request starts and shares the last selected job's rate setting; use the same `--rpm` across operators. Retries count toward that gate. Slow, refused, malformed or failed messages do not prevent unrelated completions from becoming visible.

Transient HTTP 408/409/429/5xx and network failures retry up to `--max-attempts` (including the first call), using persisted exponential backoff with jitter and Retry-After capped at 300 seconds. Refusal, truncation, invalid extraction and authentication errors need operator inspection and explicit retry. All terminal errors expose `retry-extraction`; unchanged intake reuses errors as well as successes. `retry` deliberately creates a fresh revision using the exact stored configuration and original bytes, even after a success. An earlier success remains in `history`, while the latest failed attempt is current. During automatic backoff the last error remains visible with `processing_state: pending`.

Leases last `max(30, 2 × timeout + 15)` seconds (105 seconds by default). After a killed process, restart `run`; it waits until leases expire before reclaiming. Provider calls happen outside database transactions. Expired tokens cannot publish, and old workers cannot replace a newer current revision. A provider call can be repeated after a crash; database publication is fenced, external calls are not exactly once. Ctrl-C can wait for in-flight calls to stop; abrupt deployment termination relies on lease recovery.

Intake orders updates by committed database transaction, not `exported_at`. Original file bytes determine `source_sha256`; even formatting-only changes create a new source revision. Within one batch duplicate filenames are rejected; across batches the same filename is the same document. Omitted documents stay current. An unprocessed new revision appears as `pending` with null extraction; earlier results remain in history, never silently presented as its facts. Malformed JSON/missing message produces a visible document error, while valid files continue.

Refresh all retained documents after changing processing settings, prompt, schema, validation, adapter, fixtures or policy:

```bash
python -m access_intake --db .state/live.sqlite3 refresh --provider openai --model gpt-4o-mini-2024-07-18 --concurrency 4 --rpm 60
```

Refresh explicitly selects settings (the default provider remains mock). Exact unchanged source/extraction/policy fingerprints reuse the current record. Extraction fingerprints include the model request settings, prompt plus the policy's extraction section, schema, validator/adapter code and mock fixture content. Policy fingerprints include policy text and routing code. Policy-only changes reuse a valid current extraction and revalidate/reroute it; extraction-affecting changes call the provider again. `policy.py` implements ordered rules; policy prose is not an executable rule language, so changes to routing rules also require code/tests. Pending work with code/configuration drift becomes an actionable refresh error rather than being published with false provenance. Restart worker processes after deploying code changes.

## Records and exports

SQLite retains original input revisions, configurations, immutable completed attempts and current document pointers. `history` includes abandoned attempts and superseded revisions. No batch pruning or automatic history retention limit is applied. Secure the database/backups as source-message data; `.state/`, virtual environments and `.env` are ignored by Git. Back up a running database with SQLite's backup API, or stop workers before copying it and its WAL state. SQLite on NFS or across hosts is not supported; use one shared host/local disk. Authentication, multi-tenant isolation and cross-host coordination are outside this CLI's scope.

`export` captures one database snapshot and writes `extractions.jsonl`, `queue.json`, and a manifest. Each record contains identity/hash, extraction or null, status, owner, action, error, provenance, revision/attempt IDs, fingerprints, processing state and generation ID. An export lock serializes overlapping exporters on Linux. The two root filenames are individually atomically replaced; a reader opening them across publication may see different generations. Consumers needing a consistent pair should read `manifest.json` **once**, then open its two immutable generation paths. Generation IDs also detect a mismatched pair. The manifest is atomically replaced after both files exist. Database history and prior generation directories remain separate from current outputs.

The [accuracy report](deliverables/accuracy.md), [redacted request evidence](deliverables/request-evidence.json) and [verification record](deliverables/verification.md) identify mock observations and verification limits. The workload test processes 2,000 documents with mock responses; it does not establish provider capacity or a production latency target.

Entire is enabled in this repository and reports the Codex agent. Capture is paired automatically on a later commit under the facilitator's setup. Implementation does not perform the separate default-branch push or Classroom submission described in `CHALLENGE.md`; confirm capture pairing as part of that later submission.
