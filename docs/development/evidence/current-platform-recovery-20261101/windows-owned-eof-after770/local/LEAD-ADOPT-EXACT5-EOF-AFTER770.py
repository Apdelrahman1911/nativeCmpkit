#!/usr/bin/env python3
"""Lead-only exact4 existing/NEW1 adoption; refused without accepted NEW6 evidence.

No tests, network, Git writes, ROOT mutation, releases or package publication.
Preserve all partial writes and their original preimages; never replay this file.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

D = Path('/root/nativecmpkit-source-proposals-20261105/windows-observer-owned-eof-after770-r1')
W = Path('/root/nativecmpkit-worktrees/javafx-ordinary-consumer1')
ROOT = Path('/root/projects/nativeCmpKit')
OUT = D / 'LEAD-EXACT5-ADOPTION-ORIGINAL'
GATE = D / 'LEAD-EXACT5-ADOPTION-ACCEPTANCE.json'
HEAD = 'b2fdb17fe2107af6fef0cc3e3ee13df1bb757b00'
ROOT_HEAD = '4cc34cf2e0a58eef50c583a24a157b1f2487be59'
TRACE = 'scripts/ci/test_javafx_ordinary_success_trace.py'
PACKET_SHA = 'b2d9929dd0f516e64e670769cd3c824de4ff5c7df05628ccabee40de31c9610d'
INVERSE_SHA = 'caa3d27f4c13df02cc38f1a87889dee4818b6c02c4ed3044f83e03e1ad1d637b'
RESULT_SHA = '25b97c872067931875588e5d15230da947eeb0a6522014e172608c18e4d9383e'


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def identity(s):
    return {k: getattr(s, k) for k in (
        'st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
        'st_size', 'st_mtime_ns', 'st_ctime_ns')}


def read(path):
    need(path.is_absolute() and path.resolve(strict=True) == path, 'Ordinary exact path')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'Ordinary single-link source')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        need(identity(os.fstat(fd)) == identity(before), 'Fresh opened identity')
        chunks, count = [], 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            count += len(chunk)
            need(count <= 1048576, 'Finite source byte cap')
            chunks.append(chunk)
        data = b''.join(chunks)
        need(identity(os.fstat(fd)) == identity(before), 'Held read identity')
    finally:
        os.close(fd)
    need(identity(path.lstat()) == identity(before), 'Closed named identity')
    return data, {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                  'mode': f'{stat.S_IMODE(before.st_mode):04o}', 'identity9': identity(before)}


def git(path, *args):
    p = subprocess.run(['git', '-C', str(path), *args], stdin=subprocess.DEVNULL,
                       capture_output=True, check=True, timeout=15)
    need(not p.stderr, 'Unexpected read-only Git stderr')
    return p.stdout.decode().strip()


def exclusive(path, data, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.fchmod(fd, mode)
        view = memoryview(data)
        while view:
            n = os.write(fd, view)
            need(n > 0, 'Owned complete write')
            view = view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)


def bound_json(path, sha, size=None):
    data, record = read(path)
    need(record['sha256'] == sha and (size is None or record['bytes'] == size), 'Exact DATA authority')
    return json.loads(data)


def original_stat(row):
    fields = {'dev': 'st_dev', 'ino': 'st_ino', 'mode': 'st_mode', 'nlink': 'st_nlink',
              'uid': 'st_uid', 'gid': 'st_gid', 'size': 'st_size',
              'mtime_ns': 'st_mtime_ns', 'ctime_ns': 'st_ctime_ns'}
    need(set(row['stat9']) == set(fields), 'Exact original stat9 fields')
    return {fields[k]: int(v) for k, v in row['stat9'].items()}


started = time.monotonic()
OUT.mkdir(mode=0o700)
result = {'schema': 'nativecmpkit-lead-exact5-branch-adoption-after770-v1',
          'lead': '/root', 'worktree': str(W), 'original_HEAD': HEAD,
          'ROOT_HEAD': ROOT_HEAD, 'started_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'written': [], 'ROOT_writes': 0, 'tests_replayed': 0, 'remote_operations': 0,
          'Windows_native_consumer_trust_issue_or_release_acceptance': False}
try:
    gate_data, gate_record = read(GATE)
    gate = json.loads(gate_data)
    need(gate['schema'] == 'nativecmpkit-lead-Windows-EOF6-source-results-adoption-acceptance-v1'
         and gate['accepted6_source_and_original_results'] is True
         and gate['source_packet_sha256'] == PACKET_SHA
         and gate['actual_result_sha256'] == RESULT_SHA, 'Actual accepted source/results required')
    review = gate['independent_source_and_original_results_review742']
    bound_json(Path(review['path']), review['sha256'], review['bytes'])
    packet = bound_json(D / 'RELATED-OWNED-EOF-NEW4-CHANGED2-PACKET-AFTER770-R1.json', PACKET_SHA, 26826)
    inverse = bound_json(D / 'SOURCE5-EXACT-INVERSE-AFTER770-R1.json', INVERSE_SHA, 9912)
    actual = bound_json(D / 'runner/FIRST-OWNED-EOF6-RESULTS/FIRST-RESULT.json', RESULT_SHA, 22798)
    need(actual['outcome'] == 'passed' and actual['child_exit'] == 0
         and actual['tests_selected'] == 6 and actual['inputs_before_after_held'] is True
         and actual['owned_group_absent'] is True and actual['owned_runtime_removed'] is True,
         'Complete original NEW6 and owned cleanup required')
    need(git(W, 'rev-parse', 'HEAD') == HEAD and git(ROOT, 'rev-parse', 'HEAD') == ROOT_HEAD,
         'Exact isolated and ROOT HEADs')
    need(git(W, 'status', '--porcelain') == '?? ' + TRACE, 'Only prior unqualified trace may exist')
    need(git(ROOT, 'status', '--porcelain') == '', 'ROOT remains clean')
    protected = {}
    for row in packet['local_executor']['source_model21']:
        if not row.get('lead_copy_required'):
            continue
        _, rec = read(W / row['relative'])
        need((rec['bytes'], rec['sha256']) == (row['bytes'], row['sha256']), 'Unchanged original prerequisite')
        protected[row['relative']] = rec
    need(len(protected) == 16, 'Exactly sixteen unchanged prerequisites')
    _, protected[TRACE] = read(W / TRACE)
    old = {r['relative']: r for r in inverse['source4_preimages']}
    plans = []
    for row in packet['sources']:
        data, rec = read(Path(row['path']))
        need((rec['bytes'], rec['sha256'], rec['mode']) ==
             (row['bytes'], row['sha256'], '0644'), 'Exact accepted candidate source')
        path = W / row['relative']
        need(path.parent.resolve(strict=True) == path.parent, 'Ordinary source parent')
        previous = None
        if row['relative'] in old:
            before, previous = read(path)
            expected = old[row['relative']]
            need((previous['bytes'], previous['sha256'], previous['mode'], previous['identity9']) ==
                 (expected['bytes'], expected['sha256'], expected['mode'], original_stat(expected)),
                 'Original exact source/stat9/mode held')
            restored = data
            for fragment in reversed(inverse['exact_inverse_fragments'][row['relative']]):
                after, prior = fragment['new_UTF8'].encode(), fragment['old_UTF8'].encode()
                need(after and restored.count(after) == 1, 'Unique exact inverse')
                restored = restored.replace(after, prior, 1)
            need(restored == before, 'Exact complete original inverse')
            exclusive(OUT / (str(len(plans)) + '.original-preimage'), before)
        else:
            need(row['new'] is True and not path.exists() and not path.is_symlink(), 'Exactly absent NEW source')
        plans.append((row, path, data, rec, previous))
    need(len(plans) == 5 and sum(p[-1] is None for p in plans) == 1, 'Exactly existing4 plus NEW1')
    result['gate'] = gate_record
    result['protected17_before'] = protected
    for row, path, data, _, before in plans:
        fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW |
                     (os.O_CREAT | os.O_EXCL if before is None else 0), 0o644)
        try:
            if before is not None:
                need(identity(os.fstat(fd)) == before['identity9'], 'Fresh prewrite original held')
            else:
                os.fchmod(fd, 0o644)
            view, offset = memoryview(data), 0
            while view:
                n = os.pwrite(fd, view, offset)
                need(n > 0, 'Exact complete source write')
                view, offset = view[n:], offset + n
            os.ftruncate(fd, len(data))
            os.fsync(fd)
            final_fd = identity(os.fstat(fd))
            if before is not None:
                need(all(final_fd[k] == before['identity9'][k] for k in
                         ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid')), 'Preserved original mode/identity')
        finally:
            os.close(fd)
        final, rec = read(path)
        need(final == data and rec['mode'] == '0644' and rec['identity9'] == final_fd, 'Exact closed final source')
        result['written'].append({'relative': row['relative'], 'final': rec, 'writes': 1,
                                  'existing_mode_preserved': before is not None})
    for relative, before in protected.items():
        need(read(W / relative)[1] == before, 'Protected original bytes/mode/stat held')
    for row, _, _, before, _ in plans:
        need(read(Path(row['path']))[1] == before, 'Candidate source custody retained')
    need(git(ROOT, 'status', '--porcelain') == '' and git(ROOT, 'rev-parse', 'HEAD') == ROOT_HEAD,
         'ROOT untouched after isolated adoption')
    need(git(W, 'rev-parse', 'HEAD') == HEAD, 'No history mutation during adoption')
    result.update(status='ADOPTED_EXACT_EXISTING4_NEW1_ONCE_PRESERVED_MODES_AND_PROTECTED17',
                  actual_exit=0, protected17_after_equal_before=True, candidate5_held=True)
except BaseException as error:
    result.update(status='REFUSED_OR_PARTIALLY_APPLIED_DO_NOT_REPLAY', actual_exit=2,
                  error_type=type(error).__name__, error=str(error))
finally:
    result['wall_seconds'] = time.monotonic() - started
    encoded = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
    exclusive(OUT / 'RESULT.json', encoded)
    print(encoded.decode(), end='')
raise SystemExit(result['actual_exit'])
