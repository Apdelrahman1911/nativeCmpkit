#!/usr/bin/env python3
"""Owned source-controls supervisor. Authored only; execution needs lead authority.

Uses the actual complete worktree Library/imports, never stubs. Does not invoke
Git/Rust/Gradle/JVM/native or dispatch hosted jobs. Source controls are not native
acceptance. The only direct child command is one exact22 unittest Python process.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time

P5 = Path('/root/nativecmpkit-source-proposals-20261105')
WORKTREE = Path('/root/nativecmpkit-worktrees/macos-parent-lease777')
PACKET = P5 / 'picker-jni-actual-jvm2-ingress789-source-only-r3/SOURCE-PACKET789.json'
PACKET_SHA = '66453f9ac9c92d1b1597fc37a979ae10a2450a4edbf13bc5ac686c52c9faf4ac'
MAX_CAPTURE = 8 * 1024 * 1024
SOURCE_BUDGET_SECONDS = 300
FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_uid', 'st_gid')

class Refusal(ValueError):
    pass

def path_below(root, relative):
    if type(relative) is not str or not relative or '\\' in relative:
        raise Refusal('source-relative-path-refusal')
    path = Path(relative)
    if path.is_absolute() or any(part in ('.', '..', '.git') for part in path.parts):
        raise Refusal('source-relative-path-refusal')
    result = root / path
    if any(p.is_symlink() for p in (result, *result.parents)):
        raise Refusal('symlink-input-or-output-refusal')
    if not result.is_relative_to(root):
        raise Refusal('input-or-output-escape-refusal')
    return result

def identity(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise Refusal('symlink-input-or-output-refusal')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise Refusal('one-regular-source-or-capture-required')
        digest = hashlib.sha256()
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
        after = os.fstat(handle.fileno())
    shape = lambda value: {key: getattr(value, key) for key in FIELDS}
    if shape(before) != shape(after) or shape(after) != shape(path.lstat()):
        raise Refusal('source-or-capture-changed-during-fd-custody')
    return {'path': str(path), 'bytes': after.st_size, 'sha256': digest.hexdigest(),
            'logical_mode': oct(stat.S_IMODE(after.st_mode)), 'fd_stat9': shape(after)}

def write_json(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644), 'w') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')
    os.chmod(path, 0o644)

def original_group_state(pid):
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return 'absent'
    except OSError:
        return 'unknown'
    return 'present'

def stop_live_original(process):
    record = {'term_requested': False, 'kill_requested': False}
    if process.poll() is not None:
        record['status'] = 'already-exited-no-signals'
        return record
    try:
        if os.getsid(process.pid) != process.pid:
            record['status'] = 'unknown-live-ownership-no-signal'
            return record
        os.killpg(process.pid, signal.SIGTERM)
        record['term_requested'] = True
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if process.poll() is not None:
                record['status'] = 'exited-after-term'
                return record
            if os.getsid(process.pid) != process.pid:
                record['status'] = 'unknown-live-ownership-no-escalation'
                return record
            os.killpg(process.pid, signal.SIGKILL)
            record['kill_requested'] = True
            process.wait(timeout=30)
        record['status'] = 'original-leader-reaped'
    except (OSError, subprocess.TimeoutExpired):
        record['status'] = 'original-live-cleanup-not-established'
    return record

def review_original(stdout, stderr, selected):
    body = stdout + '\n' + stderr
    observed = []
    statuses = []
    for line in body.splitlines():
        match = re.fullmatch(r'(test_[a-zA-Z0-9_]+) \(([a-zA-Z0-9_.]+)\) \.\.\. (ok|FAIL|ERROR|skipped.*)', line)
        if match:
            canonical = match[2] if match[2].endswith('.' + match[1]) else match[2] + '.' + match[1]
            observed.append(canonical)
            statuses.append(match[3])
    summaries = re.findall(r'^Ran ([0-9]+) tests? in ([0-9]+(?:\.[0-9]+)?)s$', body, re.M)
    record = {'observed_method_names': observed, 'observed_statuses': statuses,
              'parsed_method_count': len(observed), 'summaries': summaries,
              'passed_methods': [name for name, status in zip(observed, statuses) if status == 'ok'],
              'failed_or_error_methods': [name for name, status in zip(observed, statuses) if status in ('FAIL', 'ERROR')],
              'failed_obligation_population_replayed': False}
    record['accepted_original_test_shape'] = (
        observed == selected and len(set(observed)) == 22 and statuses == ['ok'] * 22
        and len(summaries) == 1 and int(summaries[0][0]) == 22
        and re.findall(r'^OK$', body, re.M) == ['OK']
        and not re.search(r'^FAILED\b|^FAIL:|^ERROR:', body, re.M))
    record['tests'] = int(summaries[0][0]) if len(summaries) == 1 else None
    record['suite_elapsed_seconds'] = float(summaries[0][1]) if len(summaries) == 1 else None
    record['failures'] = sum(status == 'FAIL' for status in statuses)
    record['errors'] = sum(status == 'ERROR' for status in statuses)
    record['skipped'] = sum(status.startswith('skipped') for status in statuses)
    return record

def run(arguments):
    if arguments.authorization != 'LEAD-EXPLICIT-ACTUAL-WORKTREE-EXACT22-SOURCE-ONLY':
        raise Refusal('explicit-lead-exact22-source-authorization-required')
    if identity(PACKET)['sha256'] != PACKET_SHA:
        raise Refusal('immutable789-r3-packet-custody-refusal')
    packet = json.loads(PACKET.read_bytes())
    selected = packet['new_important_controls'] + packet['changed_owning_controls']
    if len(selected) != 22 or len(set(selected)) != 22:
        raise Refusal('exact-unexecuted22-selection-required')
    manifest = Path(arguments.input_manifest)
    if not manifest.is_absolute() or not manifest.is_relative_to(P5):
        raise Refusal('lead-input-manifest-must-be-confined-P5')
    manifest_identity = identity(manifest)
    authority = json.loads(manifest.read_bytes())
    expected = authority.get('inputs', authority.get('files', authority))
    if not isinstance(expected, dict) or not expected:
        raise Refusal('lead-complete-input-map-required')
    critical = {item['path'] for item in packet['modified_paths'] + packet['new_paths']}
    critical.add('rust-toolchain.toml')
    # Every actual Python source dependency under scripts/ci must be in the lead
    # map. No target modules are imported by this stdlib supervisor.
    ci = path_below(WORKTREE, 'scripts/ci')
    for base, directories, names in os.walk(ci, followlinks=False):
        directories[:] = sorted(name for name in directories if name != '__pycache__')
        for name in (*directories, *names):
            if (Path(base) / name).is_symlink():
                raise Refusal('symlink-import-tree-refusal')
        for name in names:
            if name.endswith('.py'):
                critical.add((Path(base) / name).relative_to(WORKTREE).as_posix())
    # Exact owning nine accepted R3 endpoints are supplied by the lead's map,
    # not derived from a fake Library/global source-registration fixture.
    for relative in ('calf-file-picker/native/Cargo.toml', 'calf-file-picker/native/Cargo.lock',
                     'calf-file-picker/native/src/lib.rs', 'calf-file-picker/native/src/jni_path_tests.rs',
                     'calf-file-picker/native/src/macos_parent.rs', 'calf-file-picker/native/src/macos_release_slots.rs',
                     'calf-file-picker/native/src/parent_retain_slot.rs',
                     'calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeFilePickerBridge.kt',
                     'calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt'):
        critical.add(relative)
    if not critical.issubset(expected):
        raise Refusal('lead-map-missing-actual-import-or-owning-source-dependency')
    out = path_below(P5, arguments.output)
    out.mkdir(mode=0o700)
    runtime = out / 'runtime.private'
    runtime.mkdir(mode=0o700)
    command = [sys.executable, '-B', '-m', 'unittest', *selected, '-v']
    record = {'schema': 'nativecmpkit-actual-worktree789-r3-exact22-source-original-v1',
              'passed': False, 'scope': 'Source/refusal controls only; NOT compiler/JVM/native/CI/issue/consumer acceptance.',
              'command': command, 'worktree': str(WORKTREE), 'source_revision_lead_attributed': arguments.lead_head,
              'fresh_Git_custody_by_supervisor': False, 'input_manifest': manifest_identity,
              'required_method_names': selected, 'NEW': 21, 'changed_owning_legacy': 1,
              'source_budget_seconds': SOURCE_BUDGET_SECONDS, 'aggregate_private_capture_cap_bytes': MAX_CAPTURE,
              'direct_python_processes_started': 0, 'direct_Rust_Gradle_JVM_native_or_hosted_operations': 0,
              'exit_code': None, 'capture_complete': False, 'post_exit_group_state': 'not-observed',
              'publishing_deployments_releases_issue_closure': False, 'started_monotonic': time.monotonic()}
    before, process, selector, primary = {}, None, None, None
    captures, eofs = {}, set()
    captured = 0
    stop_reason = None
    started = time.monotonic()
    def capture_inputs():
        result = {relative: identity(path_below(WORKTREE, relative)) for relative in sorted(expected)}
        for relative, value in result.items():
            expected_value = expected[relative]
            digest = expected_value if isinstance(expected_value, str) else expected_value['sha256']
            if value['sha256'] != digest:
                raise Refusal('actual-worktree-lead-input-sha-refusal')
            if isinstance(expected_value, dict) and 'logical_mode' in expected_value and value['logical_mode'] != expected_value['logical_mode']:
                raise Refusal('actual-worktree-lead-input-mode-refusal')
        for item in packet['modified_paths'] + packet['new_paths']:
            # Protected packet-copy modes are not adopted NEW creation modes.
            # Existing source modes remain the lead's exact frozen actual mode.
            required_mode = (item['create_mode_explicit'] if item['kind'] == 'add'
                             else expected[item['path']]['logical_mode'])
            if (result[item['path']]['sha256'] != item['postimage']['sha256'] or
                    result[item['path']]['logical_mode'] != required_mode or
                    expected[item['path']]['logical_mode'] != required_mode):
                raise Refusal('actual-worktree789-r3-adoption-custody-refusal')
        return result
    try:
        before = capture_inputs()
        write_json(out / 'inputs-before.json', before)
        record['selected_input_count'] = len(before)
        environment = os.environ.copy()
        environment.update(PYTHONPATH=str(ci), PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(runtime),
                           TMP=str(runtime), TEMP=str(runtime), PYTHONUNBUFFERED='1')
        for name in ('stdout', 'stderr'):
            path = out / (name + '.original.private.log')
            captures[name] = os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb')
        process = subprocess.Popen(command, cwd=WORKTREE, env=environment, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        record.update(direct_python_processes_started=1, owned_leader_pid=process.pid)
        selector = selectors.DefaultSelector()
        for name in ('stdout', 'stderr'):
            pipe = getattr(process, name)
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, name)
        while len(eofs) != 2:
            if time.monotonic() - started > SOURCE_BUDGET_SECONDS:
                stop_reason = 'source-supervision-deadline-exhausted'
                break
            exited = process.poll() is not None
            events = selector.select(0 if exited else 0.1)
            if exited and not events:
                break
            for key, event in events:
                block = os.read(key.fileobj.fileno(), 64 * 1024)
                if not block:
                    eofs.add(key.data)
                    selector.unregister(key.fileobj)
                    continue
                remaining = MAX_CAPTURE - captured
                retained = block[:remaining]
                if captures[key.data].write(retained) != len(retained):
                    raise Refusal('original-private-capture-short-write')
                captured += len(retained)
                if len(block) != len(retained):
                    stop_reason = 'aggregate-original-private-capture-cap-exhausted'
                    break
            if stop_reason:
                break
        if process.poll() is None and not stop_reason:
            process.wait(timeout=max(0.01, SOURCE_BUDGET_SECONDS - (time.monotonic() - started)))
    except BaseException as error:
        primary = error
        record.update(primary_error_type=type(error).__name__,
                      reason_code=str(error) if isinstance(error, Refusal) else 'source-supervision-error-details-private')
    finally:
        def secondary(error):
            nonlocal primary
            record.setdefault('secondary_error_types', []).append(type(error).__name__)
            if primary is None:
                primary = error
        if process is not None:
            try:
                if process.poll() is None:
                    record['owned_live_cleanup'] = stop_live_original(process)
                record['exit_code'] = process.poll()
                record['post_exit_group_state'] = original_group_state(process.pid) if record['exit_code'] is not None else 'leader-still-live'
            except BaseException as error:
                secondary(error)
            for name in ('stdout', 'stderr'):
                try:
                    getattr(process, name).close()
                except BaseException as error:
                    secondary(error)
        if selector is not None:
            try:
                selector.close()
            except BaseException as error:
                secondary(error)
        for name, handle in captures.items():
            try:
                handle.flush()
                handle.close()
                record.setdefault('original_captures', {})[name] = identity(out / (name + '.original.private.log'))
            except BaseException as error:
                secondary(error)
        record.update(captured_bytes=captured, capture_complete=eofs == {'stdout', 'stderr'} and stop_reason is None and primary is None,
                      stop_reason=stop_reason, outer_process_elapsed_seconds=round(time.monotonic() - started, 9))
        try:
            after = capture_inputs()
            write_json(out / 'inputs-after.json', after)
            record['held_inputs_exact_FDstat9_SHA_modes'] = before == after and bool(before)
            record['held_lead_input_manifest'] = identity(manifest) == manifest_identity
        except BaseException as error:
            secondary(error)
        try:
            remaining = sum(1 for _ in runtime.iterdir())
            record['owned_runtime_leftover_entries'] = remaining
            if remaining == 0:
                runtime.rmdir()
            record['owned_runtime_removed_and_absent'] = not runtime.exists()
            if remaining:
                raise Refusal('owned-runtime-leftovers-preserved-for-review')
        except BaseException as error:
            secondary(error)
        try:
            if record['capture_complete']:
                values = {}
                for name, pinned in record.get('original_captures', {}).items():
                    path = out / (name + '.original.private.log')
                    if identity(path) != pinned:
                        raise Refusal('original-output-read-custody-refusal')
                    values[name] = path.read_bytes().decode('utf-8')
                    if identity(path) != pinned:
                        raise Refusal('original-output-read-custody-refusal')
                record['original_review'] = review_original(values['stdout'], values['stderr'], selected)
            # Final source/output/runtime checks all precede this fresh deadline
            # gate. Do not reproduce789's earlier before-last-custody defect.
            elapsed = time.monotonic() - started
            record['source_supervision_total_elapsed_seconds'] = round(elapsed, 9)
            record['passed'] = bool(primary is None and elapsed <= SOURCE_BUDGET_SECONDS
                                    and record['exit_code'] == 0 and record['capture_complete']
                                    and record['post_exit_group_state'] == 'absent'
                                    and record.get('held_inputs_exact_FDstat9_SHA_modes')
                                    and record.get('held_lead_input_manifest')
                                    and record.get('owned_runtime_removed_and_absent')
                                    and record.get('original_review', {}).get('accepted_original_test_shape'))
        except BaseException as error:
            secondary(error)
        if primary is not None:
            record['passed'] = False
            record.setdefault('primary_error_type', type(primary).__name__)
        write_json(out / 'ORIGINAL-EXACT22-RESULT789-R3.json', record)
    print(json.dumps({key: record.get(key) for key in ('passed', 'exit_code', 'direct_python_processes_started',
        'selected_input_count', 'captured_bytes', 'capture_complete', 'post_exit_group_state',
        'held_inputs_exact_FDstat9_SHA_modes', 'owned_runtime_removed_and_absent', 'source_supervision_total_elapsed_seconds')}, indent=2))
    return 0 if record['passed'] else 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorization', required=True)
    parser.add_argument('--input-manifest', required=True)
    parser.add_argument('--lead-head', required=True)
    parser.add_argument('--output', required=True, help='New exclusive repository-relative P5 result directory')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-f0-9]{40}', args.lead_head):
        raise SystemExit('Exact lead-attributed HEAD is required; supervisor does not run Git.')
    raise SystemExit(run(args))
