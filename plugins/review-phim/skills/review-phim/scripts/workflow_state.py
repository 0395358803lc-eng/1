#!/usr/bin/env python3
"""Local approval/checkpoint guard. Never runs media or authenticates chat users."""
import argparse
import datetime
import hashlib
import json
import os
import re
import secrets
import tempfile
from contextlib import contextmanager
from pathlib import Path

GOOD = {'pass', 'skipped'}
MODES = {'transcript-only': 9, 'full-review': 40}
STAGES = (6, 9, 12, 16, 20, 24, 28, 32, 36, 39, 40)
FINISH = ('pass', 'partial', 'blocked', 'skipped')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


@contextmanager
def locked(path):
    lock = path.with_name(path.name + '.lock')
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        fd = None
        yield
    finally:
        if fd is not None:
            os.close(fd)
        lock.unlink()


def save(path, obj):
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load(path):
    d = read(path)
    need(d.get('schema_version') == 2, 'legacy state: preserve it; create a separately approved v2 job; never infer approvals')
    need(d.get('mode') in MODES, 'invalid mode')
    need([s['step'] for s in d['steps']] == list(range(1, 41)), 'invalid steps')
    need(sum(s['status'] == 'running' for s in d['steps']) <= 1, 'multiple running steps: manual recovery required')
    return d


def evidence_issues(d):
    issues = []
    for s in d['steps'][:MODES[d['mode']]]:
        if s['status'] == 'pass':
            for e in s.get('evidence', []):
                p = Path(e['path'])
                if not p.is_file() or sha(p) != e['sha256']:
                    issues.append({'step': s['step'], 'path': str(p)})
    return issues


def next_step(d):
    return next((s['step'] for s in d['steps'][:MODES[d['mode']]] if s['status'] not in GOOD), None)


def running(d):
    return next((s for s in d['steps'] if s['status'] == 'running'), None)


def check_identity(d, a):
    need(a.job_id == d['job_id'], 'wrong job')
    need(a.source_fingerprint == d['source_fingerprint'], 'source fingerprint changed; stop and review')
    need(a.config_fingerprint == d['config_fingerprint'], 'config fingerprint changed; stop and review')


def event(d, s, status, note='', evidence=()):
    attempt = s['attempt']
    d['events'].append({'event_id': secrets.token_hex(16), 'approval_id': attempt['id'],
        'job_id': d['job_id'], 'scope_type': 'step', 'stage_number': next(i for i, end in enumerate(STAGES, 1) if s['step'] <= end),
        'step_number': s['step'], 'scope_description': attempt['scope'],
        'user_approval_text': attempt['approval_text'], 'approved_at': attempt['approved_at'],
        'timestamp': now(), 'status': status, 'evidence_paths': [e['path'] for e in evidence], 'notes': note})


def sync_log(path, d):
    """Preserve external/bootstrap records and append missing committed state events.
    State is authoritative; if interrupted after state save, replay is idempotent.
    All writers to this log must acquire the same state lock.
    """
    log = path.with_name('approval_log.json')
    old = read(log) if log.exists() else []
    need(isinstance(old, list), 'invalid approval log')
    ids = {e.get('event_id'): e for e in old if isinstance(e, dict) and e.get('event_id')}
    add = []
    for e in d['events']:
        if e['event_id'] in ids:
            need(ids[e['event_id']] == e, 'approval log mismatch; stop')
        else:
            add.append(e)
    if add or not log.exists():
        save(log, old + add)


def persist(path, d):
    d['updated_at'] = now()
    save(path, d)
    sync_log(path, d)


def info(d):
    issues = evidence_issues(d)
    r = running(d)
    n = next_step(d)
    if issues:
        n = min([i['step'] for i in issues] + ([n] if n is not None else []))
    return {'job_id': d['job_id'], 'mode': d['mode'], 'next_step': n,
            'status': 'running' if r else 'stale' if issues else 'complete' if n is None else d['steps'][n-1]['status'],
            'running_step': r['step'] if r else None, 'evidence_changes': issues,
            'approval_request': d.get('request')}


def num(v):
    n = int(v)
    if not 1 <= n <= 40:
        raise argparse.ArgumentTypeError('step must be 1..40')
    return n


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    for name in ('init', 'resume', 'prepare', 'start', 'finish', 'invalidate', 'cancel'):
        q = sub.add_parser(name)
        q.add_argument('--state', required=True, type=Path)
        if name != 'resume':
            q.add_argument('--job-id', required=True)
            q.add_argument('--source-fingerprint', required=True)
            q.add_argument('--config-fingerprint', required=True)
        if name == 'init':
            q.add_argument('--mode', choices=MODES, required=True)
        if name in ('prepare', 'start', 'finish', 'cancel'):
            q.add_argument('--step', type=num, required=True)
        if name == 'prepare':
            q.add_argument('--scope', required=True)
        if name == 'start':
            q.add_argument('--approval-text', required=True)
        if name == 'finish':
            q.add_argument('--attempt-id', required=True)
            q.add_argument('--status', choices=FINISH, required=True)
            q.add_argument('--evidence', action='append', type=Path, default=[])
            q.add_argument('--note', required=True)
        if name == 'invalidate':
            q.add_argument('--from-step', type=num, required=True)
            q.add_argument('--note', required=True)
        if name == 'cancel':
            q.add_argument('--request-id', required=True)
            q.add_argument('--note', required=True)
    return p


def execute(a):
    p = a.state.resolve()
    if a.cmd == 'init':
        need(bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', a.job_id)), 'invalid job ID')
        need(bool(a.source_fingerprint.strip() and a.config_fingerprint.strip()), 'fingerprints required')
        p.parent.mkdir(parents=True, exist_ok=True)
    with locked(p):
        if a.cmd == 'init':
            need(not p.exists(), 'state already exists')
            d = {'schema_version': 2, 'job_id': a.job_id, 'mode': a.mode,
                 'source_fingerprint': a.source_fingerprint, 'config_fingerprint': a.config_fingerprint,
                 'steps': [{'step': i, 'status': 'pending' if i <= MODES[a.mode] else 'out_of_scope'} for i in range(1, 41)],
                 'request': None, 'events': [], 'history': []}
            # Validate existing log before making state durable.
            log = p.with_name('approval_log.json')
            if log.exists():
                need(isinstance(read(log), list), 'invalid approval log')
            persist(p, d)
            return info(d)
        d = load(p)
        sync_log(p, d)
        if a.cmd == 'resume':
            return info(d)
        check_identity(d, a)
        r = running(d)
        if a.cmd == 'invalidate':
            need(not r, 'running step must be reconciled before invalidation')
            need(a.from_step <= MODES[d['mode']], 'step outside mode')
            need(bool(a.note.strip()), 'reason required')
            for i in range(a.from_step-1, MODES[d['mode']]):
                s = d['steps'][i]
                if s['status'] != 'pending':
                    d['history'].append({'at': now(), 'previous': dict(s), 'reason': a.note})
                    d['steps'][i] = {'step': i+1, 'status': 'stale', 'note': a.note}
            # An outstanding request earlier than from_step also becomes invalid.
            req = d.get('request')
            if req and req['step'] < a.from_step:
                d['steps'][req['step']-1]['status'] = 'pending'
            d['request'] = None
        else:
            need(a.step <= MODES[d['mode']], 'step outside mode')
            s = d['steps'][a.step-1]
            if a.cmd == 'finish':
                need(r is s and s['attempt']['id'] == a.attempt_id, 'no matching running attempt')
                need(bool(a.note.strip()), 'report note required')
                ev = [{'path': str(e.resolve()), 'sha256': sha(e.resolve())} for e in a.evidence]
                need(a.status not in GOOD or bool(ev), 'pass/skipped requires evidence')
                if a.status == 'skipped':
                    need(a.step not in (7, 8, 9), 'mandatory transcript step cannot be skipped')
                    need(s['attempt']['scope'].startswith('BỎ QUA:'), 'skip requires explicit approved BỎ QUA scope')
                s.update(status=a.status, evidence=ev, note=a.note, updated_at=now())
                event(d, s, a.status, a.note, ev)
            else:
                need(not r, 'another attempt running; do not duplicate')
                need(not evidence_issues(d), 'evidence changed; invalidate affected step with reason first')
                need(a.step == next_step(d), 'not the next eligible step')
                req = d.get('request')
                if a.cmd == 'prepare':
                    need(bool(a.scope.strip()), 'scope required')
                    if req:
                        need(req['step'] == a.step and req['scope'] == a.scope, 'cancel old request before changing scope')
                        return info(d)
                    rid = secrets.token_hex(16)
                    stage = next(i for i, end in enumerate(STAGES, 1) if a.step <= end)
                    expected = f'PHÊ DUYỆT THỰC THI: Job {d["job_id"]}; Giai đoạn {stage}; Bước {a.step:02d}; Mã {rid}; Phạm vi: {a.scope}'
                    d['request'] = {'id': rid, 'step': a.step, 'scope': a.scope, 'expected_text': expected, 'created_at': now()}
                    s['status'] = 'waiting_approval'
                elif a.cmd == 'cancel':
                    need(req and req['id'] == a.request_id and req['step'] == a.step, 'no matching request')
                    need(bool(a.note.strip()), 'reason required')
                    d['history'].append({'at': now(), 'cancelled_request': req, 'reason': a.note})
                    d['request'] = None
                    s['status'] = 'pending'
                elif a.cmd == 'start':
                    need(req and req['step'] == a.step and s['status'] == 'waiting_approval', 'no pending approval request')
                    need(a.approval_text == req['expected_text'], 'approval must match exact current job, step, scope and request')
                    if 'attempt' in s:
                        d['history'].append({'at': now(), 'previous': dict(s)})
                    s['attempt'] = {'id': req['id'], 'scope': req['scope'], 'approval_text': a.approval_text, 'approved_at': now()}
                    s['status'] = 'running'
                    d['request'] = None
                    event(d, s, 'started')
        persist(p, d)
        result = info(d)
        if a.cmd == 'start':
            result['attempt_id'] = s['attempt']['id']
        return result


def main():
    p = parser()
    try:
        print(json.dumps(execute(p.parse_args()), ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as e:
        p.exit(2, f'BLOCKED: {e}\n')


if __name__ == '__main__':
    main()
