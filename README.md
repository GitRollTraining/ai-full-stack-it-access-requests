# AI Full Stack Challenge — IT Access Requests

## The task
Northstar Labs receives access requests as free-text messages. Build a small runnable application that uses a language model to turn those messages into structured records and a review queue for the IT team. The supplied company, people and requests are fictional.

Start with materials/office-policy.md, the 20 JSON request exports in materials/requests/, and snapshot.schema.json. Choose a CLI, service or web application as the interface.

## Required behavior
- Use a language model to extract the request details into records that conform to snapshot.schema.json.
- Validate response structure and completion status before using extracted data. Preserve exact supporting quotes and represent uncertain fields as null with an explanatory issue.
- Use message content as the source of business facts. Preserve missing values, conflicting alternatives and explicit corrections according to the policy. Keep document identity distinct from the request ID stated in the message.
- Apply the supplied review policy and display each request's status, owner and next action. Approval decisions belong to the named human reviewers.
- Record input filenames and SHA-256 hashes. Reuse unchanged results, process changed inputs and retain earlier versions. Process each message independently and make failures visible with a reproducible retry command.
- Handle malformed output, provider errors, refusal and interrupted responses explicitly. Keep model/provider settings configurable and document a supported configuration. The facilitator supplies model-provider access through environment variables.

## What to submit
| Path | Content |
|---|---|
| README.md | Setup, supported runtime/provider, exact intake/test/accuracy-check commands, environment-variable names, and how to inspect the queue |
| Source code and dependency lockfile | Runnable application, extraction prompt, schema and model request configuration |
| deliverables/extractions.jsonl | One current record per message: document_id, source_sha256, extraction (schema-conforming object, or null on error), status, owner, next_action, and error (null on success) |
| deliverables/queue.json | The review queue linked to extraction records by document_id |
| deliverables/accuracy.md | Source-derived expected fields for the 20 supplied messages and one paraphrase you author; the field-comparison procedure, exact-match counting/denominator rules, factual-error reporting and model/configuration; distinguish mocked examples from any optional live observations |
| deliverables/request-evidence.json | Credential-redacted example model request showing the model ID and configuration used, plus the implemented response handling |
| deliverables/verification.md | Verification commands and assertions, their intended comparisons, operating limits, and any observed results or repairs clearly identified as such |
| Coding-session capture | Session record paired with the submitted commit, collected through the facilitator's capture setup |

Include automated tests covering a complete request, missing dates, conflicting details, embedded instructions, provider failure, an unchanged rerun, and changed source content. Build expected results from the supplied messages and policy. Add a paraphrased synthetic request to exercise extraction on fresh wording. Specify expected facts from the source messages and policy independently of the extraction outputs being measured. Include checks for refusal or interrupted responses and a failed retry after a prior success.

## Submission
Commit and push the application, outputs and session capture. Submit the repository URL and exact commit through the Classroom assignment. The facilitator supplies the assignment and capture instructions.

Submit the implemented provider integration and source-grounded validation procedure. Use mocked responses for reproducible development examples, and label each recorded observation with its configuration and whether it used a mock or provider response.
