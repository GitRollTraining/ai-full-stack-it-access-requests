# Verification record

Observed on 9 November 2026 with Python 3.12.3 on the local Linux workspace. All extraction observations below use deterministic **mock** responses. OpenAI transport behavior was exercised with stubs; no live provider request or paid accuracy run was performed.

## Commands and observations

```bash
python3 -W error::ResourceWarning -m unittest discover -v
```

Observed: **24 tests passed in 52.062 seconds**. The runtime includes a 2,000-document mock workload with eight worker threads and all other tests; it is not a provider throughput measurement. No ResourceWarning remained in the final run. The first run exposed an unclosed mock fixture file; it was repaired by using `Path.read_text()` and the suite was rerun with ResourceWarning treated as an error.

The suite checks the following independent assertions:

| Situation | Intended comparison / assertion |
| --- | --- |
| All 20 samples plus authored paraphrase | All 12 scalars and all 3 route fields equal the separately authored source expectations; successful records have null errors |
| Missing/relative dates, contradictory environment/managers, explicit corrections | Nulls/conflicts clarify; explicit corrections replace earlier values; reversed dates remain explicit and clarify |
| Embedded instructions, including withdrawal plus override | Override is inspected before withdrawal/missing facts; attempted text remains source evidence; no approval or credential exposure |
| Unchanged intake | Reuses the current revision and adds no attempt |
| Changed bytes / changed decoded message | New source SHA-256 and attempt; previous result survives in history; unknown changed mock wording becomes a visible current error |
| Batch omission | Prior documents remain current |
| Failed retry after success | Latest extraction is null with visible error; previous success remains in history |
| Provider exception | One record fails while another completes; arbitrary exception text/secret marker is absent from stored errors |
| Rate-limit, server and network errors | Correct retryability, bounded shared rate gate, persisted backoff, terminal state at retry limit |
| Refusal/interrupted/malformed output | Parser rejects partial/invalid results; refusal and interruption also produce current document errors while unaffected input succeeds |
| Killed/expired lease | Persisted work is reclaimed, abandoned attempt retained, old token cannot publish |
| Stale worker after new intake | Earlier worker result is retained historically and cannot replace newer current source |
| Overlapping operators | Two Store instances concurrently intake the same 20 files and run workers; exactly 20 current rows and one successful attempt per document |
| Fast/slow/failing messages | A second completed result is visible while the first remains running; independent failure remains isolated |
| Policy/configuration changes | Policy-only revision reuses extraction without a provider call; model setting change creates fresh extraction; stale persisted configuration is a visible refresh error |
| Invalid input/schema/quotes/dates | Malformed export is visible as an input error; wrong keys/types/enums/nonliteral quotes fail; unsupported or impossible dates become null with issues |
| Snapshot publication | Root and immutable generation files agree; queue/extraction document identities and generation IDs agree, including a pending document |
| Empty accuracy input | Every missing expected field, including null expectations, counts as a mismatch rather than inflating the score |
| OpenAI HTTP stub | Strict schema, instructions/user-envelope split, store=false, timeout, API_KEY header and actual returned model identity are handled; credentials do not enter configuration |
| 2,000-document workload | 2,000 distinct filenames finish with 2,000 current results and zero extraction errors; intentionally repeated message IDs clarify filename mismatches |

```bash
python3 -m access_intake --db .state/demo.sqlite3 intake materials/requests examples
python3 -m access_intake --db .state/demo.sqlite3 export --out deliverables
python3 -m access_intake --db .state/demo.sqlite3 accuracy
python3 -m access_intake --db .state/demo.sqlite3 evidence
python3 -m access_intake --db .state/demo.sqlite3 intake materials/requests examples
```

Observed: final unchanged rerun reported `{"enqueued": 0, "reused": 21}`. The recorded configuration is in `accuracy.md` and `request-evidence.json`: mock replay, model request template `gpt-4o-mini-2024-07-18`, timeout 45 seconds, max attempts 3, concurrency 4, rate 60/minute, output limit 3,000, temperature 0. Mock does not call that model. Exact matches were **252/252 scalar facts**, **63/63 route fields**, with **21/21 schema/date/quote checks**. Zero scalar discrepancies were observed in this fixture replay; live factual correctness remains unmeasured.

The committed current exports contain 21 records, all with `response_source: mock`, a schema-conforming extraction and `error: null`. SHA-256 is calculated from original bytes; literal supporting quotes refer to decoded message text. Previous generated snapshots live under `generations/`; runtime source revisions and attempt history live in SQLite, outside current extraction outputs.

```bash
python3 -m access_intake --db .state/handover.sqlite3 intake materials/requests --enqueue-only
python3 -m access_intake --db .state/handover.sqlite3 run
python3 -m access_intake --db .state/handover.sqlite3 retry IT-001.json --enqueue-only
python3 -m access_intake --db .state/handover.sqlite3 run
python3 -m access_intake --db .state/handover.sqlite3 export --out .state/handover-exports
python3 -m access_intake --help
```

Observed: CLI handover commands succeeded. Direct database assertions found 20 completed current records and two historical attempts for IT-001. Separate JSON assertions confirmed that the committed manifest paths contain 21 matching document identities with one generation ID and that both root convenience files equal their manifest-selected immutable versions.

`git diff --check` passed. Entire's read-only status reported enabled on the working branch, Codex as the agent and checkpoint synchronization to origin. It also labelled the listed session exited; this status alone does not establish that capture has been paired with a submitted commit. No capture setup, destructive Entire command, manual checkpoint, commit, push or Classroom submission was performed. Commit capture pairing remains a later submission check under the facilitator's instructions.

## Operating and verification limits

One shared Linux host and a local SQLite WAL database are supported. Cross-host/network-filesystem coordination, authentication and access provisioning are outside this implementation. Concurrency is bounded per worker process, while the request-start gate is shared by provider across processes; operators must coordinate total concurrency and use consistent RPM settings. A crash may duplicate an external model call, but lease fencing and current pointers protect database publication. Deployment interruption is tested by persisted lease expiration/reclamation, not by sending OS kill signals to a live paid request.

Exports come from one read transaction. Publication uses immutable generation files and an atomic manifest pointer; root filenames are individually replaced and readers needing a pair must use the manifest once. Crash/power-loss durability of a particular host/filesystem has not been fault-injected. Database revisions and generation directories grow until operators apply a separate retention policy.

Semantic interpretation of arbitrary new wording remains the model's responsibility. Schema validation, quote provenance, dates, explicit override guards and policy routing cannot independently prove that every model fact is entailed. Review live discrepancies against the source, distinguish factual errors from acceptable alternate wording, and record model/configuration for any future live evaluation. No model accuracy percentage, live latency guarantee or measured production throughput is claimed.
