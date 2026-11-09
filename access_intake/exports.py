"""Coherent immutable generations, with atomically replaced manifest pointer."""
import fcntl
import json
import os
import tempfile
from pathlib import Path

QUEUE_KEYS = ('document_id', 'source_sha256', 'revision_id', 'attempt_id', 'status',
              'owner', 'next_action', 'error', 'response_source', 'processing_state', 'generation_id')


def atomic_write(path, text):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def export(store, destination):
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    # Serialize snapshot + publication across operators sharing this output directory.
    with (out / '.export.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        generation, records = store.snapshot()
        queue = dict(generation_id=generation, items=[{k: r[k] for k in QUEUE_KEYS if k in r} for r in records])
        extractions = ''.join(json.dumps(r, sort_keys=True) + '\n' for r in records)
        queue_text = json.dumps(queue, indent=2) + '\n'
        target = out / 'generations' / generation
        target.mkdir(parents=True, exist_ok=True)
        atomic_write(target / 'extractions.jsonl', extractions)
        atomic_write(target / 'queue.json', queue_text)
        atomic_write(out / 'extractions.jsonl', extractions)
        atomic_write(out / 'queue.json', queue_text)
        atomic_write(out / 'manifest.json', json.dumps(dict(generation_id=generation,
            extractions=f'generations/{generation}/extractions.jsonl',
            queue=f'generations/{generation}/queue.json'), indent=2) + '\n')
        return generation
