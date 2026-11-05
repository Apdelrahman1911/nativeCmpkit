#!/usr/bin/env python3
"""Lead-owned R3 exact source adoption; accepted controls are not rerun.

The original prewrite refused on a sparse-excluded tracked JNI test leaf with
zero writes. Git sparse-checkout subsequently restored only requested tracked
dependencies. This recovery preserves original refusal and existing modes.
"""
import hashlib
import json
import os
from pathlib import Path
import stat

P5 = Path('/root/nativecmpkit-source-proposals-20261105')
BASE = Path(__file__).parent
ROOT = Path('/root/nativecmpkit-worktrees/macos-parent-lease777')
PACKET = P5 / 'picker-native-parent-lease777-r3-jni-release-ownership/SOURCE-PACKET777-R3.json'
ACCEPTANCE = P5 / 'picker-native-parent-lease777-independent-results743-r3/PASSIVE-RESULTS-REVIEW743.json'
KEYS = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(s):
    return {key: getattr(s, key) for key in KEYS}


def parents(path):
    for parent in reversed(path.parents):
        require(stat.S_ISDIR(parent.lstat().st_mode), 'Unsafe ancestor ' + str(parent))


def read(path):
    parents(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= 1048576,
                'Unsafe leaf ' + str(path))
        raw = os.pread(fd, before.st_size + 1, 0)
        require(len(raw) == before.st_size and identity(before) == identity(os.fstat(fd)) == identity(path.lstat()),
                'Read changed ' + str(path))
        return raw, dict(bytes=len(raw), sha256=sha(raw), mode=stat.S_IMODE(before.st_mode), stat9=identity(before))
    finally:
        os.close(fd)


def write_all(fd, raw):
    offset = 0
    while offset < len(raw):
        written = os.write(fd, raw[offset:])
        require(written > 0, 'Short write')
        offset += written


def emit(name, report):
    raw = (json.dumps(report, indent=2, sort_keys=True) + '\n').encode()
    fd = os.open(BASE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        write_all(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    print(name, len(raw), sha(raw), flush=True)


def main():
    report = dict(schema='nativecmpkit-lead-r3-isolated-nine-source-after-sparse794-v1', worktree=str(ROOT),
                  target_writes=0, created_new=0, Git_network_tests_compiler_native_issue_publication=0,
                  scope='Exact qualified R3 adoption only. No789 or actual JVM/macOS/ABI/consumer/whole58 acceptance.',
                  original_refusal='ORIGINAL-ADOPTION-REFUSAL794.json; zero source writes; sparse-excluded tracked leaf',
                  before={})
    try:
        raw, packet_row = read(PACKET)
        require(packet_row['sha256'] == '141e16317171471ff95c0ddfa26764afeff395e9d8f9c0b6c1ee58598cd6fff6', 'Packet drift')
        _, accepted_row = read(ACCEPTANCE)
        require(accepted_row['sha256'] == '4b07de556260d49734e7b7ef315736c61143061270b11549e907694b6f33ab59', 'Acceptance drift')
        source = json.loads(raw)['complete_original_r2_lead784_to_r3']
        require(source['counts'] == dict(existing_modified=6, new=3, candidate_sources=9, reversible_fragments=67),
                'Population drift')
        report.update(packet=packet_row, independent_saved_results=accepted_row)
        plan = []
        for row in source['existing_modified']:
            path = ROOT / row['path']
            before, current = read(path)
            post, proposed = read(PACKET.parent / row['proposed_packet_path'])
            require(current['bytes'] == row['preimage']['size'] and current['sha256'] == row['preimage']['sha256'],
                    'Current preimage ' + row['path'])
            require(proposed['bytes'] == row['postimage']['size'] and proposed['sha256'] == row['postimage']['sha256'],
                    'Source postimage ' + row['path'])
            report['before'][row['path']] = current
            plan.append((path, before, post, current, False))
        for row in source['new']:
            path = ROOT / row['path']
            require(not os.path.lexists(path), 'NEW already present ' + row['path'])
            parents(path)
            post, proposed = read(PACKET.parent / row['proposed_packet_path'])
            require(proposed['bytes'] == row['postimage']['size'] and proposed['sha256'] == row['postimage']['sha256'],
                    'NEW source postimage ' + row['path'])
            require(row['required_new_mode'] == '0o644', 'NEW mode changed')
            report['before'][row['path']] = {'absent': True}
            plan.append((path, None, post, {'mode': 0o644}, True))
        require(len(plan) == 9, 'Source count')
        emit('RECOVERY-EXACT9-PREWRITE794.json', report)
        for path, before, post, current, is_new in plan:
            flags = os.O_RDWR | os.O_NOFOLLOW | (os.O_CREAT | os.O_EXCL if is_new else 0)
            fd = os.open(path, flags, 0o644)
            try:
                if not is_new:
                    require(identity(os.fstat(fd)) == current['stat9'] == identity(path.lstat()), 'Prewrite identity drift')
                    require(os.pread(fd, len(before) + 1, 0) == before, 'Prewrite byte drift')
                write_all(fd, post)
                os.ftruncate(fd, len(post))
                if is_new:
                    os.fchmod(fd, 0o644)
                os.fsync(fd)
                if is_new:
                    report['created_new'] += 1
                else:
                    report['target_writes'] += 1
                require(os.pread(fd, len(post) + 1, 0) == post, 'Postwrite byte drift')
                require(stat.S_IMODE(os.fstat(fd).st_mode) == current['mode'], 'Postwrite mode drift')
            finally:
                os.close(fd)
        report['after'] = {}
        for path, before, post, current, is_new in plan:
            actual, final = read(path)
            require(actual == post and final['mode'] == current['mode'], 'Passive readback drift')
            report['after'][path.relative_to(ROOT).as_posix()] = final
        require(report['target_writes'] == 6 and report['created_new'] == 3, 'Write population')
        report['all9_postimages_and_existing_modes_preserved'] = True
        emit('ACTUAL-RECOVERY-R3-APPLIED-ONCE794.json', report)
    except BaseException as error:
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
        emit('RECOVERY-ORIGINAL-REFUSAL794.json', report)
        raise


if __name__ == '__main__':
    main()
