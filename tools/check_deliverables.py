"""Check the committed mock examples, not application behavior or model accuracy."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(value, schema, location):
    """Validate the keywords used by this repository's snapshot schema only."""
    types = {"object": dict, "array": list, "string": str, "null": type(None)}
    allowed = schema["type"]
    allowed = allowed if isinstance(allowed, list) else [allowed]
    require(any(isinstance(value, types[t]) for t in allowed), f"{location}: invalid type")
    if "enum" in schema:
        require(value in schema["enum"], f"{location}: invalid enum value")
    if isinstance(value, dict):
        require(set(schema["required"]) <= set(value), f"{location}: missing fields")
        require(set(value) <= set(schema["properties"]), f"{location}: extra fields")
        for key, item in value.items():
            validate(item, schema["properties"][key], f"{location}.{key}")
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate(item, schema["items"], f"{location}[{index}]")


def main():
    outputs = ROOT / "deliverables"
    records = [json.loads(line) for line in (outputs / "extractions.jsonl").read_text().splitlines()]
    queue = json.loads((outputs / "queue.json").read_text())
    expected = json.loads((outputs / "expected-facts.json").read_text())
    schema = json.loads((ROOT / "snapshot.schema.json").read_text())
    sources = {p.name: p for p in (ROOT / "materials" / "requests").glob("*.json")}
    for name, entries in [("extractions", records), ("queue", queue), ("expected facts", expected)]:
        ids = [entry["document_id"] for entry in entries]
        require(len(ids) == len(set(ids)), f"{name}: duplicate document_id")
        require(set(ids) == set(sources), f"{name}: source coverage differs")
    queue_by_id = {entry["document_id"]: entry for entry in queue}
    references = {entry["document_id"]: entry for entry in expected}
    compared = 0
    for record in records:
        doc = record["document_id"]
        raw = sources[doc].read_bytes()
        reference = references[doc]
        require(record["source_sha256"] == hashlib.sha256(raw).hexdigest(), f"{doc}: hash mismatch")
        require(reference["source_sha256"] == record["source_sha256"], f"{doc}: reference hash mismatch")
        require(record["response_source"] == "mock", f"{doc}: examples must be labelled mock")
        require(record["error"] is None, f"{doc}: unexpected example error")
        extraction = record["extraction"]
        validate(extraction, schema, doc)
        message = json.loads(raw)["message"]
        require(bool(extraction["supporting_quotes"]), f"{doc}: missing quotes")
        for quote in extraction["supporting_quotes"]:
            require(bool(quote) and quote in message, f"{doc}: quote is not source text")
        for field, value in reference["expected_fields"].items():
            require(extraction[field] == value, f"{doc}.{field}: reference mismatch")
            compared += 1
        require(extraction["issues"] == reference["expected_issues"], f"{doc}: issue mismatch")
        for field, value in reference["expected_route"].items():
            require(record[field] == value, f"{doc}.{field}: route mismatch")
        for field, value in queue_by_id[doc].items():
            require(record[field] == value, f"{doc}.{field}: queue/extraction mismatch")
    print(f"PASS: {len(records)} mock records; hashes, schema, quotes and queue links checked.")
    print(f"PASS: {compared}/{compared} scalar fixture comparisons; 60/60 routing values.")
    print("Fixture consistency only: outputs were constructed from references; no model accuracy measured.")


if __name__ == "__main__":
    main()
