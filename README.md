# AI Full Stack Challenge — IT Access Requests

This project prepares free-text IT access requests for human review. The full assignment is in [CHALLENGE.md](CHALLENGE.md).

Current status: deliverable drafts, source-authored mock examples for the 20 supplied messages, and a fixture checker are available. The intake application and model-provider integration have not been implemented. The files are not yet a complete submission.

## Setup

Use Python 3.10 or later. The existing starter tests and fixture checker use only the Python standard library and require no dependency installation or API credentials.

Run the following commands from the repository root:

```bash
python3 --version
env -u API_KEY python3 -m unittest discover -s tests -v
env -u API_KEY python3 tools/check_deliverables.py
```

The starter tests verify supplied inputs and a canned response. The checker verifies the committed mock records, hashes, schema structure, supporting quotes, reference facts, and queue links. These checks do not measure model accuracy or demonstrate application behavior.

## Submission files

| File | Current contents |
|---|---|
| [README.md](README.md) | Current setup, available checks, queue inspection and implementation gaps |
| [deliverables/extractions.jsonl](deliverables/extractions.jsonl) | 20 source-authored mock extraction records, each labelled `response_source: mock` |
| [deliverables/queue.json](deliverables/queue.json) | Matching mock review queue, linked by document ID and source hash |
| [deliverables/accuracy.md](deliverables/accuracy.md) | Source-derived expectations for the 20 messages and an authored paraphrase, with comparison rules |
| [deliverables/request-evidence.json](deliverables/request-evidence.json) | Explicitly marked draft listing the provider evidence still required |
| [deliverables/verification.md](deliverables/verification.md) | Available checks, observed results, planned application checks and operating limits |

The supporting file [deliverables/expected-facts.json](deliverables/expected-facts.json) contains machine-readable reference facts for the 20 supplied messages. Mock examples were constructed from these references; agreement between them is fixture consistency, not independent accuracy evidence.

## Inspect the queue

```bash
python3 -m json.tool deliverables/queue.json
```

Each entry shows `document_id`, `source_sha256`, `status`, `owner`, `next_action`, and `response_source`. Find its supporting extraction on the line with the same `document_id` in `deliverables/extractions.jsonl`.

## Provider configuration and remaining work

The challenge specifies `API_KEY` as the credential environment variable for a future provider integration. No code currently reads it, and no provider or model is configured. Never put a credential in the committed evidence files.

Intake, resume, retry, model configuration, history storage and full accuracy-check commands are pending application implementation. Once implemented, document the exact commands here and replace the request-evidence draft with a credential-redacted request and references to actual response-handling code. Add application tests for the cases listed in `deliverables/verification.md` and measure fresh outputs against the frozen source-derived expectations.

For the course workflow, start with [docs/00-prerequisites.md](docs/00-prerequisites.md) and follow the files in `docs/` in order. The facilitator supplies the coding-session capture instructions. The capture, source code, dependency lockfile, commit and push are separate submission requirements.
