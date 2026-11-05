#!/usr/bin/env python3
"""Lead-only, once-only exact four-file adoption; no tests or remote operations."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

D = Path('/root/nativecmpkit-source-proposals-20261105/windows-one-request-diagnostic770-r1')
W = Path('/root/nativecmpkit-worktrees/javafx-ordinary-consumer1')
ROOT = Path('/root/projects/nativeCmpKit')
OUT = D / 'LEAD-EXACT4-ADOPTION770-ORIGINAL'
HEAD = 'b7c29cf03e566a8aff608a588593f7b12c9e690e'
ROOT_HEAD = '4cc34cf2e0a58eef50c583a24a157b1f2487be59'
TRACE = 'scripts/ci/test_javafx_ordinary_success_trace.py'
AUTHORITY = {
    D / 'RELATED-ONE-REQUEST-NEW4-PACKET770-R1.json':
        (29140, '2e68bb5f5373697dc0ee4d7976e9ad97e91db9d4d2dfa29f12d6685570f825b7'),
    D / 'SOURCE-AND-WORKFLOW-EXACT-INVERSE770-R1.json':
        (13083, '93895ace15ef99f169bd97237774fd14b370be3ab9b20e51db4c14eedc708ca9'),
    Path('/root/nativecmpkit-source-proposals-20261105/producer-failure-batch-classification742/diagnostic770-independent-review742/ORIGINAL-NEW4-RESULTS-ACCEPTANCE742-770-R1.json'):
        (10758, '6df23a1d34a6d9c8494b4dd2067fdb7633ad00df926f921985c15dd148eb16e7'),
}


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def identity(s):
    return {k: getattr(s, k) for k in (
        'st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
        'st_size', 'st_mtime_ns', 'st_ctime_ns')}


def read(path):
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, f'Ordinary single-link source: {path}')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        need(identity(os.fstat(fd)) == identity(before), f'Fresh opened identity: {path}')
        chunks = []
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            need(sum(map(len, chunks)) <= 1048576, 'Finite source byte cap')
        data = b''.join(chunks)
        need(identity(os.fstat(fd)) == identity(before), f'Held read identity: {path}')
    finally:
        os.close(fd)
    need(identity(path.lstat()) == identity(before), f'Closed named identity: {path}')
    return data, {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                  'mode': f'{stat.S_IMODE(before.st_mode):04o}', 'identity9': identity(before)}


def git(path, *args):
    proc = subprocess.run(['git', '-C', str(path), *args], stdin=subprocess.DEVNULL,
                          capture_output=True, check=True, timeout=15)
    need(not proc.stderr, 'Read-only Git produced unexpected stderr')
    return proc.stdout.decode().strip()


def exclusive(path, data, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.fchmod(fd, mode)
        view = memoryview(data)
        while view:
            count = os.write(fd, view)
            need(count > 0, 'Owned complete write')
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)


started = time.monotonic()
OUT.mkdir(mode=0o700)
result = {'schema': 'nativecmpkit-lead-exact4-branch-adoption770-v1',
          'lead': '/root', 'worktree': str(W), 'original_HEAD': HEAD,
          'ROOT_HEAD': ROOT_HEAD, 'started_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'written': [], 'ROOT_writes': 0, 'tests_replayed': 0, 'remote_operations': 0,
          'Windows_native_consumer_trust_issue_or_release_acceptance': False}
try:
    authority_data = {}
    for path, (size, sha) in AUTHORITY.items():
        data, record = read(path)
        need(record['bytes'] == size and record['sha256'] == sha, f'Exact authority: {path}')
        authority_data[path.name] = json.loads(data)
    packet = authority_data['RELATED-ONE-REQUEST-NEW4-PACKET770-R1.json']
    inverse = authority_data['SOURCE-AND-WORKFLOW-EXACT-INVERSE770-R1.json']
    accepted = authority_data['ORIGINAL-NEW4-RESULTS-ACCEPTANCE742-770-R1.json']
    need(accepted['status'] == 'ACCEPTED_ORIGINAL_NEW4_PASS4_LOCAL_SOURCE_CONTROLS_AND_OWNED_AF_UNIX_ONLY',
         'Genuine independently accepted original NEW4')
    need(git(W, 'rev-parse', 'HEAD') == HEAD and git(ROOT, 'rev-parse', 'HEAD') == ROOT_HEAD,
         'Exact isolated and ROOT HEADs')
    need(git(W, 'status', '--porcelain') == '?? ' + TRACE, 'Only prior unqualified trace present')
    need(git(ROOT, 'status', '--porcelain') == '', 'ROOT remains clean')
    protected = {}
    for row in packet['local_executor']['source_model19']:
        if not row.get('lead_copy_required', False):
            continue
        _, record = read(W / row['relative'])
        need(record['bytes'] == row['bytes'] and record['sha256'] == row['sha256'],
             f'Unchanged original prerequisite: {row["relative"]}')
        protected[row['relative']] = record
    need(len(protected) == 15, 'Exactly fifteen unchanged prerequisites')
    _, protected[TRACE] = read(W / TRACE)
    plans = []
    for row in packet['sources']:
        data, record = read(Path(row['path']))
        need(record['bytes'] == row['bytes'] and record['sha256'] == row['sha256'] and record['mode'] == '0644',
             f'Accepted exact candidate source: {row["relative"]}')
        path = W / row['relative']
        old_record = None
        if row['relative'] in ('scripts/ci/windows_ordinary_dependency_observer742.py', '.github/workflows/javafx-library-candidate.yml'):
            old, old_record = read(path)
            kind = 'source' if path.suffix == '.py' else 'workflow'
            expected = inverse[kind + '_preimage']
            need(old_record['bytes'] == expected['bytes'] and old_record['sha256'] == expected['sha256']
                 and old_record['mode'] == '0644', f'Exact original source and preserved mode: {path}')
            restored = data
            for fragment in reversed(inverse[kind + '_fragments']):
                after, before = fragment['new'].encode(), fragment['old'].encode()
                need(after and restored.count(after) == 1, f'Unique exact inverse fragment: {path}')
                restored = restored.replace(after, before, 1)
            need(restored == old, f'Accepted exact reversible postimage: {path}')
            exclusive(OUT / (kind + '.original-preimage'), old)
        else:
            need(not path.exists() and not path.is_symlink(), f'Exactly absent NEW source: {path}')
            need(path.parent.is_dir() and not path.parent.is_symlink(), 'Existing ordinary source parent')
        plans.append((row, path, data, record, old_record))
    need(len(plans) == 4, 'Exactly four accepted source plans')
    result['protected16_before'] = protected
    result['exact4_preflight'] = [{'relative': row['relative'], 'candidate': record, 'original': old}
                                  for row, _, _, record, old in plans]
    for row, path, data, _, before in plans:
        flags = os.O_RDWR | os.O_NOFOLLOW
        if before is None:
            flags |= os.O_CREAT | os.O_EXCL
        fd = os.open(path, flags, 0o644)
        try:
            if before is not None:
                need(identity(os.fstat(fd)) == before['identity9'], f'Prewrite original held: {path}')
            else:
                os.fchmod(fd, 0o644)
            view, offset = memoryview(data), 0
            while view:
                count = os.pwrite(fd, view, offset)
                need(count > 0, 'Complete exact source write')
                view, offset = view[count:], offset + count
            os.ftruncate(fd, len(data))
            os.fsync(fd)
            final_fd = identity(os.fstat(fd))
            if before is not None:
                need(all(final_fd[k] == before['identity9'][k] for k in
                         ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid')),
                     f'Preserved existing non-time identity and mode: {path}')
        finally:
            os.close(fd)
        final, record = read(path)
        need(final == data and record['mode'] == '0644' and record['identity9'] == final_fd,
             f'Full final exact closed source: {path}')
        result['written'].append({'relative': row['relative'], 'final': record,
                                  'writes': 1, 'existing_mode_preserved': before is not None})
    for relative, before in protected.items():
        _, after = read(W / relative)
        need(after == before, f'Unchanged protected original byte/mode/identity: {relative}')
    for row, _, _, before, _ in plans:
        _, after = read(Path(row['path']))
        need(after == before, 'Candidate primary source custody retained')
    need(git(ROOT, 'status', '--porcelain') == '' and git(ROOT, 'rev-parse', 'HEAD') == ROOT_HEAD,
         'ROOT untouched after exact isolated adoption')
    need(git(W, 'rev-parse', 'HEAD') == HEAD, 'No Git history mutation during adoption')
    result['protected16_after_equal_before'] = True
    result['candidate4_after_equal_before'] = True
    result['status'] = 'ADOPTED_EXACT4_ONCE_PRESERVED_ORIGINAL_MODES_AND_PROTECTED16'
    result['actual_exit'] = 0
except BaseException as error:
    result['status'] = 'REFUSED_OR_PARTIALLY_APPLIED_DO_NOT_REPLAY'
    result['error_type'] = type(error).__name__
    result['error'] = str(error)
    result['actual_exit'] = 2
finally:
    result['wall_seconds'] = time.monotonic() - started
    encoded = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
    exclusive(OUT / 'RESULT.json', encoded)
    print(encoded.decode(), end='')
raise SystemExit(result['actual_exit'])
