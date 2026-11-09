"""Run with python -m access_intake --help."""
import argparse
import json
import sys
from pathlib import Path
from .config import configure
from .exports import export
from .store import Store
from .worker import run


def settings(parser):
    parser.add_argument('--provider', choices=['mock', 'openai'], default='mock')
    parser.add_argument('--model', default='gpt-4o-mini-2024-07-18')
    parser.add_argument('--timeout', type=float, default=45)
    parser.add_argument('--max-attempts', type=int, default=3)
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument('--rpm', type=float, default=60)
    parser.add_argument('--fixtures')
    parser.add_argument('--enqueue-only', action='store_true')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Prepare IT access requests for human review')
    parser.add_argument('--db', default='.state/intake.sqlite3')
    sub = parser.add_subparsers(dest='command', required=True)
    intake = sub.add_parser('intake', help='hash and enqueue JSON exports, then process')
    intake.add_argument('paths', nargs='+')
    settings(intake)
    refresh = sub.add_parser('refresh', help='apply current configuration/policy to all retained documents')
    settings(refresh)
    worker = sub.add_parser('run', help='resume pending jobs, including expired leases')
    worker.add_argument('--concurrency', type=int, default=4)
    retry = sub.add_parser('retry', help='force a fresh extraction using persisted configuration')
    retry.add_argument('document_id')
    retry.add_argument('--enqueue-only', action='store_true')
    sub.add_parser('queue', help='consistent current snapshot, including pending/errors')
    show = sub.add_parser('show')
    show.add_argument('document_id')
    history = sub.add_parser('history')
    history.add_argument('document_id')
    output = sub.add_parser('export')
    output.add_argument('--out', default='deliverables')
    evaluate = sub.add_parser('accuracy')
    evaluate.add_argument('--expected', default='tests/fixtures/expectations.json')
    evaluate.add_argument('--out', default='deliverables/accuracy.md')
    evidence = sub.add_parser('evidence')
    evidence.add_argument('--out', default='deliverables/request-evidence.json')
    args = parser.parse_args(argv)
    try:
        store = Store(args.db)
        if args.command in ('intake', 'refresh'):
            cfg = configure(args.provider, args.model, args.timeout, args.max_attempts,
                            args.concurrency, args.rpm, args.fixtures)
            if args.command == 'intake':
                paths = []
                for name in args.paths:
                    path = Path(name)
                    paths.extend(sorted(path.glob('*.json')) if path.is_dir() else [path])
                if not paths:
                    raise ValueError('no JSON exports found')
                if len({p.name for p in paths}) != len(paths):
                    raise ValueError('duplicate filenames in one intake; split batches or rename exports')
                sources = [(p.name, p.read_bytes()) for p in paths]
            else:
                sources = [(r['document_id'], r['raw']) for r in store.sources()]
            added = sum(store.enqueue(name, raw, cfg)[1] for name, raw in sources)
            print(json.dumps(dict(enqueued=added, reused=len(sources) - added)), flush=True)
            if not args.enqueue_only:
                run(store, args.concurrency)
        elif args.command == 'run':
            run(store, args.concurrency)
        elif args.command == 'retry':
            store.retry(args.document_id)
            if not args.enqueue_only:
                run(store)
        elif args.command == 'queue':
            generation, records = store.snapshot()
            print(json.dumps(dict(generation_id=generation, items=records), indent=2))
        elif args.command == 'show':
            matches = [r for r in store.snapshot()[1] if r['document_id'] == args.document_id]
            if not matches:
                raise ValueError('unknown document_id')
            print(json.dumps(matches[0], indent=2))
        elif args.command == 'history':
            print(json.dumps(store.history(args.document_id), indent=2))
        elif args.command == 'export':
            print(export(store, args.out))
        elif args.command == 'accuracy':
            from .evaluation import evaluate
            report, ok = evaluate(store, args.expected)
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(report)
            print(report)
            return 0 if ok else 1
        elif args.command == 'evidence':
            from .evaluation import evidence
            evidence(store, args.out)
        return 0
    except (ValueError, OSError) as exc:
        # Do not print arbitrary input or exception text to operational logs.
        print('Command failed: check paths, arguments and configuration; use --help.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
