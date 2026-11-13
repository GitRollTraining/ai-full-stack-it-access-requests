# Extraction accuracy — draft

Status: source-authored mock examples and validation procedure prepared; no application extraction or provider run has been measured.

The reference sources are `materials/requests/*.json`, `materials/office-policy.md`, and `snapshot.schema.json`. Expected facts must be written from those sources before comparing application output. Do not build the expected answers by copying the output being assessed.

## Expected behavior for the supplied messages

All messages state request date `2026-10-22`. Document identity is the original filename, including `.json`.

| Document | Source-derived facts and important checks | Expected owner / next action | Status |
|---|---|---|---|
| IT-001.json | Maya Chen; Analytics; new Atlas staging/read; 2026-10-23–2026-11-06; Priya Shah; check weekly conversion dashboard | System Owner / review-request | review |
| IT-002.json | Owen Reed; Payments; new Ledger production/write; 2026-10-24–2026-10-25; Elena Park; correct settlement entries | Security Review / review-risk-then-owner | review |
| IT-003.json | Lina Gomez; Customer Success; new Beacon access for renewal review; Priya Shah; environment, permission, start and end dates unresolved | IT Service Desk / clarify | needs-information |
| IT-004.json | Theo Malik; Quality Engineering; new Atlas/read; 2026-10-23–2026-10-30; Nia Patel; investigate report counts; environment null because staging and production conflict | IT Service Desk / clarify | needs-information |
| IT-005.json | Ava Brooks; Design; withdrawal of IT-005; Elena Park; project cancelled; system, environment, permission, start and end dates absent | IT Service Desk / confirm-withdrawal | review |
| IT-006.json | Finn Lee; Platform; new Atlas staging/read; 2026-10-23–2026-10-24; Nia Patel; compare deployment metrics; preserve and flag the instruction-override attempt | IT Service Desk / inspect-message | review |
| IT-007.json | Grace Tan; Developer Experience; change Forge staging permission to write; 2026-10-24–2026-10-28; Nia Patel; update starter templates | Security Review / review-risk-then-owner | review |
| IT-008.json | Noah Kim; Finance; new Atlas/read; corrected environment staging; 2026-10-25–2026-10-31; Priya Shah; check billing rehearsal totals | System Owner / review-request | review |
| IT-009.json | Isla Morgan; Support; new Beacon staging/read; 2026-10-26–2026-10-29; manager null; review support examples for troubleshooting guide | IT Service Desk / clarify | needs-information |
| IT-010.json | Ben Carter; Operations; new Ledger production/read; start 2026-10-27; end null; Elena Park; investigate reconciliation totals | IT Service Desk / clarify | needs-information |
| IT-011.json | Zoe Adams; Research; new Atlas staging/read; Priya Shah; sample experiments for walkthrough; both dates null because relative dates must remain unresolved | IT Service Desk / clarify | needs-information |
| IT-012.json | Ravi Shah; Infrastructure; new Forge staging/admin; 2026-10-26–2026-10-27; Nia Patel; configuration migration rehearsal | Security Review / review-risk-then-owner | review |
| IT-013.json | Emma Wilson; Compliance; new Beacon production/read; 2026-10-28–2026-10-30; Elena Park; internal account activity audit | Security Review / review-risk-then-owner | review |
| IT-014.json | Lucas Brown; Sales Operations; new Atlas staging/read; start 2026-11-05, end 2026-11-02; Priya Shah; territory report demo; retain and flag reversed dates | IT Service Desk / clarify | needs-information |
| IT-015.json | Mia Davis; Learning; new Beacon staging/read; corrected dates 2026-10-29–2026-10-31; Elena Park; verify workshop examples | System Owner / review-request | review |
| IT-016.json | Alex Turner; Platform; stated request ID IT-061; new Forge staging/read; 2026-10-26–2026-10-28; Nia Patel; investigate pipeline timing; flag filename/ID mismatch | IT Service Desk / clarify | needs-information |
| IT-017.json | Chloe Martin; Communications; kind other; asks for form URL; system, environment, permission, dates and manager absent | IT Service Desk / clarify | needs-information |
| IT-018.json | Daniel Wright; Data Engineering; new Atlas staging/read; 2026-10-27–2026-11-03; Priya Shah; investigate workshop dataset discrepancy | System Owner / review-request | review |
| IT-019.json | Sara Ahmed; Customer Operations; change Beacon production permission to read; 2026-10-28–2026-11-04; Elena Park; review exception reports | Security Review / review-risk-then-owner | review |
| IT-020.json | Ethan Clark; Product; new Atlas staging/read; 2026-10-29–2026-11-02; manager null because Priya Shah and Elena Park conflict; feature adoption summary | IT Service Desk / clarify | needs-information |

Request IDs match filename stems except IT-016.json, whose stated ID is IT-061. Missing or conflicting scalar values are null and require explanatory issues. Supporting quotes must be exact substrings of the decoded message. Explicit corrections replace earlier values. Instruction text in IT-006 is evidence, never an instruction to the application.

## Authored paraphrase

Use a separate synthetic input named `paraphrase-001.json` with this message:

> Please log new request IT-021, dated 2026-10-22. I am Maya Chen in Analytics, reporting to Priya Shah. From 2026-10-23 through 2026-11-06, I need read permission for the staging environment of Atlas to check the weekly conversion dashboard against the revised event definitions.

Expected fields: request_id IT-021; request_date 2026-10-22; kind new; requester Maya Chen; team Analytics; system Atlas; environment staging; permission read; business_purpose “check the weekly conversion dashboard against the revised event definitions”; start_date 2026-10-23; end_date 2026-11-06; manager Priya Shah. Expected route: review / System Owner / review-request. No missing or conflicting facts.

## Comparison procedure and denominators

`expected-facts.json` records all 12 scalar fields, canonical business-purpose text, issues and expected routes for the 20 supplied messages. It was authored from the source messages before constructing the mock outputs. The paraphrase's 12 expected fields are specified above and must be added to the machine-readable reference before running a full 21-document evaluation. Freeze these references before measuring application output.

Run `env -u API_KEY python3 tools/check_deliverables.py` to check the 20 committed mock examples against the references. This is a fixture consistency check, not a model accuracy experiment. A full accuracy runner accepting fresh application outputs and the synthetic input remains to be implemented.

Compare each scalar with its reference using exact equality: case and whitespace matter; null matches only null. Do not silently normalize values. Count missing records, failed extractions and missing fields as mismatches rather than excluding them. Report supplied-message exact matches out of 240 (20 × 12), paraphrase matches out of 12, and combined matches out of 252. A fully correct document has all 12 scalar matches; report this separately out of 21.

Business-purpose exact mismatch does not by itself establish a factual error: report whether the wording is a faithful paraphrase, incomplete, or unsupported. For every mismatch report document_id, field, expected value, actual value, source quote, and interpretation. Report invented facts even if they do not affect routing.

Check supporting quotes separately for exact substring membership, coverage of extracted facts, conflicting alternatives and instruction-override evidence. Check issues for every missing/conflicting fact, identifier mismatch and invalid date order. Do not include the variable-length quote/issue arrays in the scalar denominator. Compare status, owner and next_action separately, out of 63 routing values for 21 documents.

## Run configuration and observations

No model accuracy run has been performed. Model/provider, prompt version, request settings, policy hash and schema hash provenance are not yet implemented. `extractions.jsonl` and `queue.json` contain 20 manually constructed mock examples, copied from the source-authored references; every record is labelled `response_source: mock`. Each extraction includes the full decoded source message as one exact supporting quote. No provider response or extraction algorithm produced these examples.

A future application run must record its configuration and each record's response_source. Keep mock consistency results separate from optional provider measurements; mock answers copied from references cannot establish model accuracy.
