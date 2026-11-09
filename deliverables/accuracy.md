# Accuracy verification

The oracle in `tests/fixtures/expectations.json` was authored from the 20 source messages and office policy before processing outputs. The fresh paraphrase is `examples/PAR-001.json`. The mock response table was authored separately and replayed by message SHA-256; the evaluator never reads mock fixtures.

Mock comparisons check fixture replay, validation, routing and evaluation plumbing. They do **not** measure language-model accuracy or generalization. No live provider accuracy run was performed for the committed artifacts.

Observed response sources: mock.

Scalar exact matches: **252/252**. Route exact matches: **63/63**. Schema/date/quote checks passed: **21/21**.

Comparison uses Python literal equality with no case, punctuation or whitespace normalization. All 12 scalar fields per expected document count, including nulls. Each of status, owner and next_action counts separately (3 per document). Missing documents, errors and missing fields count as mismatches, including expected nulls. Extra documents are excluded from the fixed denominator. Arrays are not in the scalar score; schema, nonempty literal quote provenance and date checks are reported separately.

Every scalar mismatch is a factual discrepancy requiring source review, not automatically a hallucination: a different supported business-purpose excerpt can be factually correct while failing literal equality. Review each mismatch against the decoded message, record whether it is a factual error, acceptable alternate wording or unresolved, and report that adjudication separately. The mock observation below has no scalar discrepancies; this is not a factual-error rate for a model. Routing mismatches are policy errors. Quotes alone do not establish semantic entailment, and a human must review live results.

Reproduce: `python -m access_intake --db .state/demo.sqlite3 accuracy` after intaking both supplied requests and the paraphrase. To measure live accuracy, use a separate database with `intake --provider openai`, intake the paraphrase with identical settings, and run this same command. It exits 1 on any mismatch or failed evidence check.

## Independently expected facts

| Document | Date / kind | Requester / team | System / environment / permission | Business purpose (literal excerpt) | Start / end | Manager | Expected route |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IT-001.json (stated IT-001) | 2026-10-22 / new | Maya Chen / Analytics | Atlas / staging / read | checking the weekly conversion dashboard with the new event definition changes | 2026-10-23 / 2026-11-06 | Priya Shah | review / System Owner / review-request |
| IT-002.json (stated IT-002) | 2026-10-22 / new | Owen Reed / Payments | Ledger / production / write | make the corrections at the time of our scheduled maintenance | 2026-10-24 / 2026-10-25 | Elena Park | review / Security Review / review-risk-then-owner |
| IT-003.json (stated IT-003) | 2026-10-22 / new | Lina Gomez / Customer Success | Beacon / null / null | working on the customer renewal review next week | null / null | Priya Shah | needs-information / IT Service Desk / clarify |
| IT-004.json (stated IT-004) | 2026-10-22 / new | Theo Malik / Quality Engineering | Atlas / null / read | understand why the nightly quality report shows different counts from the release checklist | 2026-10-23 / 2026-10-30 | Nia Patel | needs-information / IT Service Desk / clarify |
| IT-005.json (stated IT-005) | 2026-10-22 / withdrawal | Ava Brooks / Design | null / null / null | The project that triggered my request has been cancelled | null / null | Elena Park | review / IT Service Desk / confirm-withdrawal |
| IT-006.json (stated IT-006) | 2026-10-22 / new | Finn Lee / Platform | Atlas / staging / read | look at deployment metrics and compare them against release notes before service review | 2026-10-23 / 2026-10-24 | Nia Patel | review / IT Service Desk / inspect-message |
| IT-007.json (stated IT-007) | 2026-10-22 / change | Grace Tan / Developer Experience | Forge / staging / write | updating starter project templates | 2026-10-24 / 2026-10-28 | Nia Patel | review / Security Review / review-risk-then-owner |
| IT-008.json (stated IT-008) | 2026-10-22 / new | Noah Kim / Finance | Atlas / staging / read | check the sample billing total vs forecasting workbook before month end rehearsal | 2026-10-25 / 2026-10-31 | Priya Shah | review / System Owner / review-request |
| IT-009.json (stated IT-009) | 2026-10-22 / new | Isla Morgan / Support | Beacon / staging / read | go through example support cases before updating our troubleshooting guide | 2026-10-26 / 2026-10-29 | null | needs-information / IT Service Desk / clarify |
| IT-010.json (stated IT-010) | 2026-10-22 / new | Ben Carter / Operations | Ledger / production / read | compare the daily reconciliation report to the entries that the operations folks see | 2026-10-27 / null | Elena Park | needs-information / IT Service Desk / clarify |
| IT-011.json (stated IT-011) | 2026-10-22 / new | Zoe Adams / Research | Atlas / staging / read | looking at sample experiment records to get ready for our team walkthrough | null / null | Priya Shah | needs-information / IT Service Desk / clarify |
| IT-012.json (stated IT-012) | 2026-10-22 / new | Ravi Shah / Infrastructure | Forge / staging / admin | doing a configuration migration rehearsal before planning the wider rollout | 2026-10-26 / 2026-10-27 | Nia Patel | review / Security Review / review-risk-then-owner |
| IT-013.json (stated IT-013) | 2026-10-22 / new | Emma Wilson / Compliance | Beacon / production / read | review account activity records to help with internal audit we have scheduled | 2026-10-28 / 2026-10-30 | Elena Park | review / Security Review / review-risk-then-owner |
| IT-014.json (stated IT-014) | 2026-10-22 / new | Lucas Brown / Sales Operations | Atlas / staging / read | giving a demo of the new territory report for sales leads | 2026-11-05 / 2026-11-02 | Priya Shah | needs-information / IT Service Desk / clarify |
| IT-015.json (stated IT-015) | 2026-10-22 / new | Mia Davis / Learning | Beacon / staging / read | make sure that the sample conversations in the examples I'm building match up to the exercise handout for the Support onboarding workshop | 2026-10-29 / 2026-10-31 | Elena Park | review / System Owner / review-request |
| IT-016.json (stated IT-061) | 2026-10-22 / new | Alex Turner / Platform | Forge / staging / read | looking at the example pipeline runs to figure out why the starter project takes longer to build some of the time | 2026-10-26 / 2026-10-28 | Nia Patel | needs-information / IT Service Desk / clarify |
| IT-017.json (stated IT-017) | 2026-10-22 / other | Chloe Martin / Communications | null / null / null | Where can we find the access request form? | null / null | null | needs-information / IT Service Desk / clarify |
| IT-018.json (stated IT-018) | 2026-10-22 / new | Daniel Wright / Data Engineering | Atlas / staging / read | reviewing our sample dataset we use during our weekly analyst workshop | 2026-10-27 / 2026-11-03 | Priya Shah | review / System Owner / review-request |
| IT-019.json (stated IT-019) | 2026-10-22 / change | Sara Ahmed / Customer Operations | Beacon / production / read | view the records that make up the exception report and to explain any unusual entries | 2026-10-28 / 2026-11-04 | Elena Park | review / Security Review / review-risk-then-owner |
| IT-020.json (stated IT-020) | 2026-10-22 / new | Ethan Clark / Product | Atlas / staging / read | look at some sample usage records before I draft the summary on feature adoption | 2026-10-29 / 2026-11-02 | null | needs-information / IT Service Desk / clarify |
| PAR-001.json (stated PAR-001) | 2026-10-22 / new | Leah Stone / Analytics | Atlas / staging / read | reconcile workshop sample totals with the training workbook | 2026-10-28 / 2026-10-30 | Priya Shah | review / System Owner / review-request |

Critical source interpretations: IT-004 environment and IT-020 manager conflict without correction; IT-008 environment and IT-015 dates explicitly corrected; IT-006 override wins over all normal routes; IT-007 new permission is write and IT-019 new permission is read; IT-011 relative dates stay null; IT-014 reversed dates remain explicit; IT-016 retains IT-061 and clarifies mismatch; IT-005 withdrawal precedes missing-fact clarification.

## Discrepancies

```json
[]
```

## Recorded configuration

```json
[
  {
    "extraction": {
      "provider": "mock",
      "model": "gpt-4o-mini-2024-07-18",
      "max_output_tokens": 3000,
      "temperature": 0,
      "timeout": 45,
      "max_attempts": 3,
      "endpoint": "https://api.openai.com/v1/responses",
      "prompt_sha256": "4651d377535a5c10dae5c29e5768b0067c25d6b72b6964f99b1dc3b48d6b55bf",
      "schema_sha256": "232e006119d2bc6fd2966c81f1331c575e15eddf55b8d3b27f8141c564afb845",
      "validator_sha256": "b63c009b333c3c615e40eef684c68bcec0d6d5d6d4a84bc57fa99eba3b27a0f2",
      "adapter_sha256": "f232068d01f6d3ac35b2e585c82e609bfd1ef0c9b1b579346b777152af9ab5c7",
      "fixtures": "/home/user/ai-full-stack-it-access-requests/tests/fixtures/mock_responses.json",
      "fixtures_sha256": "6faca902bd37f72d3184479db0c479a5a5cdcc88c611ec410c520cc8108c2619"
    },
    "extract_fp": "ff5888c98cce7900478b249fddac69db1662fac35b8323da1e4f3dada2842113",
    "policy_fp": "a4b8cb4590efd4b4cb977d5ead152a7653533a057ef16c8dd7243ccd1898a237",
    "concurrency": 4,
    "rpm": 60
  }
]
```
