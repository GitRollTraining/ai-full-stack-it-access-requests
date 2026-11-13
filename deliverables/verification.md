# Verification — draft

These files prepare the deliverable structure and source-authored mock examples. The application, provider integration and application test suite have not been implemented. `extractions.jsonl` and `queue.json` contain 20 examples constructed from reference facts, not application runs. The submission is not complete.

## Commands available now

Run from the repository root, with Python 3.10 or later:

```bash
env -u API_KEY python3 -m unittest discover -s tests -v
env -u API_KEY python3 tools/check_deliverables.py
python3 -m json.tool deliverables/queue.json
python3 -m json.tool deliverables/request-evidence.json
```

The starter tests check the 20 supplied exports, the schema's request_id field, and reading a canned reply without network access. The deliverable checker checks coverage, duplicate IDs, byte hashes, schema keywords used by snapshot.schema.json, source quote membership, 240 reference scalar comparisons, 60 routing comparisons and matching queue links. It only checks the committed successful mock fixtures; it is not a general intake validator or accuracy runner. Neither command verifies application extraction, routing logic or recovery. JSON formatting commands only check that the two JSON files parse.

Observed results on 2026-11-13: all 3 starter tests passed with API_KEY unset. The deliverable checker passed for 20 mock records, including 240/240 scalar fixture comparisons and 60/60 routing comparisons. Both JSON documents parsed successfully. These observations establish fixture consistency only; the mock outputs were constructed from the reference facts. No application behavior or provider accuracy was measured.

## Required application checks

The following checks are planned, not implemented or passed:

| Situation | Required assertion |
|---|---|
| Complete request | Extract source facts into the schema and route according to the policy |
| Missing dates | Keep dates null, explain issues, route to clarification |
| Conflicting details | Keep unresolved values null and retain exact alternative quotes |
| Explicit correction | Use the corrected value without treating it as an unresolved conflict |
| Embedded instructions | Preserve evidence and route to inspect-message without following it |
| Withdrawal | Route an identified, dated withdrawal to confirm-withdrawal |
| Identifier mismatch | Preserve the stated ID and flag the mismatch with the filename |
| Refusal / interrupted response | Reject unusable extraction; show an actionable error |
| Malformed response / provider failure | Show error / IT Service Desk / retry-extraction, with null extraction |
| Unchanged rerun | Reuse matching source/configuration results and keep one current entry |
| Changed source | Create a new current version and preserve the old hash/result in history |
| Changed model, prompt, schema or policy | Refresh affected results and retain configuration provenance |
| Failed retry after success | Show the latest error; preserve the earlier success only as history |
| Stop and resume | Preserve completed work and resume pending work through the documented interface |
| Slow or failed message | Other completed messages remain available |
| Overlapping operators | Preserve one coherent current record and queue entry per source version |
| Later partial batch | Preserve earlier documents absent from the new batch |
| Output consistency | Match document_id and source_sha256 between queue and extraction records |
| Accuracy | Compare independently authored references for all 20 messages plus one paraphrase |

## Operating assumptions and limits

The target context is 200–400 daily messages and occasional batches of about 2,000, shared operators, variable model rate limits and service interruptions. No throughput, concurrency, persistence, retry or recovery guarantees have been demonstrated. Select and document the storage and worker design during implementation, then test the situations it claims to handle.

The future README must provide exact intake, queue inspection, resume, retry and accuracy commands. The facilitator's session-capture setup must be checked separately; this document is not a coding-session capture. No commit or push is performed by creating these files.
