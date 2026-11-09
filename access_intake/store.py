"""SQLite WAL ledger; calls never run inside publication transactions."""
import contextlib
import json
import sqlite3
import time
import uuid
from pathlib import Path
from .config import digest

DDL = '''
CREATE TABLE IF NOT EXISTS documents (
 document_id TEXT PRIMARY KEY, current_job INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
 id INTEGER PRIMARY KEY, document_id TEXT NOT NULL, source_sha256 TEXT NOT NULL,
 raw BLOB NOT NULL, message TEXT, input_error TEXT, config TEXT NOT NULL,
 extract_fp TEXT NOT NULL, policy_fp TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'pending', created REAL NOT NULL,
 result TEXT, cached TEXT, lease_token TEXT, lease_until REAL,
 available REAL NOT NULL DEFAULT 0, tries INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS attempts (
 id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id),
 token TEXT NOT NULL UNIQUE, started REAL NOT NULL, finished REAL,
 state TEXT NOT NULL, result TEXT
);
CREATE INDEX IF NOT EXISTS jobs_work ON jobs(state, available);
CREATE TABLE IF NOT EXISTS rate_gate (provider TEXT PRIMARY KEY, next_at REAL NOT NULL);
'''


def decode(raw):
    try:
        obj = json.loads(raw)
        if not isinstance(obj, dict) or not isinstance(obj.get('message'), str) or not obj['message'].strip():
            raise ValueError()
        return obj['message'], None
    except (ValueError, UnicodeError):
        return None, 'invalid-input: expected a JSON object with a nonempty message string; correct export and intake again'


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with contextlib.closing(self.connect()) as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript(DDL)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=30000')
        return db

    @contextlib.contextmanager
    def transaction(self):
        with contextlib.closing(self.connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def enqueue(self, document_id, raw, config, force=False):
        sha = digest(raw)
        message, error = decode(raw)
        with self.transaction() as db:
            old = db.execute('SELECT j.* FROM documents d JOIN jobs j ON j.id=d.current_job '
                             'WHERE d.document_id=?', (document_id,)).fetchone()
            if (old and not force and old['source_sha256'] == sha and
                old['extract_fp'] == config['extract_fp'] and old['policy_fp'] == config['policy_fp']):
                return old['id'], False
            cached = None
            if (old and not force and old['source_sha256'] == sha and
                old['extract_fp'] == config['extract_fp'] and old['state'] == 'done'):
                result = json.loads(old['result'])
                if result['extraction'] is not None:
                    cached = json.dumps(result)
            # The highest committed intake transaction wins. Metadata timestamps do not order revisions.
            job = db.execute('INSERT INTO jobs(document_id,source_sha256,raw,message,input_error,config,'
                             'extract_fp,policy_fp,created,cached) VALUES(?,?,?,?,?,?,?,?,?,?)',
                             (document_id, sha, raw, message, error, json.dumps(config),
                              config['extract_fp'], config['policy_fp'], time.time(), cached)).lastrowid
            db.execute('INSERT INTO documents VALUES(?,?) ON CONFLICT(document_id) '
                       'DO UPDATE SET current_job=excluded.current_job', (document_id, job))
            return job, True

    def retry(self, document_id):
        with contextlib.closing(self.connect()) as db:
            row = db.execute('SELECT j.* FROM documents d JOIN jobs j ON j.id=d.current_job '
                             'WHERE d.document_id=?', (document_id,)).fetchone()
        if row is None:
            raise ValueError('unknown document_id')
        return self.enqueue(document_id, row['raw'], json.loads(row['config']), force=True)

    def sources(self):
        with contextlib.closing(self.connect()) as db:
            return [dict(r) for r in db.execute('SELECT j.* FROM documents d JOIN jobs j ON j.id=d.current_job')]

    def claim(self):
        now = time.time()
        with self.transaction() as db:
            expired = db.execute("SELECT id,lease_token FROM jobs WHERE state='running' AND lease_until<?", (now,)).fetchall()
            for row in expired:
                db.execute("UPDATE attempts SET state='abandoned',finished=? WHERE token=? AND state='running'",
                           (now, row['lease_token']))
                db.execute("UPDATE jobs SET state='pending',lease_token=NULL,lease_until=NULL WHERE id=?", (row['id'],))
            row = db.execute("SELECT j.* FROM jobs j JOIN documents d ON d.current_job=j.id "
                             "WHERE j.state='pending' AND j.available<=? ORDER BY j.id LIMIT 1", (now,)).fetchone()
            if row is None:
                return None
            config = json.loads(row['config'])
            # Persist a shared rate gate so overlapping local operators share the budget.
            provider = config['extraction']['provider']
            gate = db.execute('SELECT next_at FROM rate_gate WHERE provider=?', (provider,)).fetchone()
            if provider != 'mock' and gate and gate['next_at'] > now:
                return None
            if provider != 'mock':
                db.execute('INSERT INTO rate_gate VALUES(?,?) ON CONFLICT(provider) DO UPDATE '
                           'SET next_at=excluded.next_at', (provider, now + 60 / config['rpm']))
            token = uuid.uuid4().hex
            lease = max(30, config['extraction']['timeout'] * 2 + 15)
            db.execute("UPDATE jobs SET state='running',lease_token=?,lease_until=?,tries=tries+1 WHERE id=?",
                       (token, now + lease, row['id']))
            attempt = db.execute("INSERT INTO attempts(job_id,token,started,state) VALUES(?,?,?,'running')",
                                 (row['id'], token, now)).lastrowid
            result = dict(row)
            result.update(lease_token=token, attempt_id=attempt, tries=row['tries'] + 1,
                          config=config)
            return result

    def finish(self, job, result, retry_delay=None):
        with self.transaction() as db:
            # Fencing: an expired or replaced token can never publish a result.
            row = db.execute('SELECT * FROM jobs WHERE id=?', (job['id'],)).fetchone()
            if row['lease_token'] != job['lease_token'] or row['state'] != 'running':
                return False
            now = time.time()
            # Reject a result finishing after expiration even if no other claimant has arrived.
            if row['lease_until'] < now:
                db.execute("UPDATE attempts SET state='abandoned',finished=? WHERE token=?",
                           (now, job['lease_token']))
                db.execute("UPDATE jobs SET state='pending',lease_token=NULL,lease_until=NULL WHERE id=?", (job['id'],))
                return False
            result['attempt_id'] = job['attempt_id']
            encoded = json.dumps(result)
            state = 'pending' if retry_delay is not None else 'done'
            db.execute("UPDATE attempts SET state=?,finished=?,result=? WHERE token=?",
                       ('error' if result['error'] else 'success', now, encoded, job['lease_token']))
            db.execute('UPDATE jobs SET state=?,result=?,available=?,lease_token=NULL,lease_until=NULL WHERE id=?',
                       (state, encoded, now + (retry_delay or 0), job['id']))
            return True

    def unfinished(self):
        with contextlib.closing(self.connect()) as db:
            return db.execute("SELECT count(*) FROM documents d JOIN jobs j ON j.id=d.current_job "
                              "WHERE j.state!='done'").fetchone()[0]

    def snapshot(self):
        with contextlib.closing(self.connect()) as db:
            db.execute('BEGIN')
            rows = db.execute('SELECT j.* FROM documents d JOIN jobs j ON j.id=d.current_job '
                              'ORDER BY j.document_id').fetchall()
            records = []
            for row in rows:
                if row['result']:
                    result = json.loads(row['result'])
                else:
                    config = json.loads(row['config'])
                    result = base_record(dict(row), config)
                    result.update(status='pending', owner='IT Service Desk', next_action='resume-processing')
                result['processing_state'] = row['state']
                records.append(result)
            # Same generation covers both current records and queue, not wall clock time.
            generation = digest(records)
            for result in records:
                result['generation_id'] = generation
            return generation, records

    def history(self, document_id):
        with contextlib.closing(self.connect()) as db:
            rows = db.execute('SELECT j.id AS revision_id,j.source_sha256,j.config,j.state AS revision_state,'
                              'a.id AS attempt_id,a.started,a.finished,a.state,a.result '
                              'FROM jobs j LEFT JOIN attempts a ON a.job_id=j.id '
                              'WHERE j.document_id=? ORDER BY j.id,a.id', (document_id,)).fetchall()
            return [{**dict(r), 'config': json.loads(r['config']),
                     'result': json.loads(r['result']) if r['result'] else None} for r in rows]


def base_record(job, config):
    e = config['extraction']
    return dict(document_id=job['document_id'], source_sha256=job['source_sha256'],
                revision_id=job['id'], extraction=None, status='error', owner='IT Service Desk',
                next_action='retry-extraction', error=None,
                response_source='mock' if e['provider'] == 'mock' else 'openai:' + e['model'],
                extract_fp=config['extract_fp'], policy_fp=config['policy_fp'])
