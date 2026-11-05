# SPDX-License-Identifier: Apache-2.0
"""Unexecuted bounded one-shot IDENTITY9 source runner; review/execute by lead only.

A source seal binds bytes, not reviewer authorization or dependency trust. No
runnable review gate is supplied by742. FIRST outputs are exclusive and retained.
Only finite NEW observer/plan/test/reference inputs are held once
before and after; no global checkout/stdlib scan, Git, network or Gradle runs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import time

HERE = Path(__file__).resolve().parent
FIXED_HERE = Path("/root/nativecmpkit-source-proposals-20261105/windows-source-identity-recovery734-r2/runner")
OUTPUT = HERE / 'FIRST-IDENTITY9-RESULTS'
FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
MAX = 4 * 1024 * 1024
TOTAL = 180
CLEANUP_RESERVE = 30
OUTPUT_CAP = 1024 * 1024
SELECTED = ["test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_new_scope_original_native_protocol_and_full_POSIXstat7_preserved","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_POSIX_reader_writer_full_crossstat7_reparse_shared_bounds_and_ancestor_refusals","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Win32_full128_ID_volume64_ABI_and_owned_vs_borrowed_handle_lifecycle","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_reader_separate_python_views_do_not_waive_native_or_own_stat_custody","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_reader_every_native_field_high_ID_and_fresh_after_read_close_drift_refused","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Win32_open_query_close_failures_fail_closed_and_keep_primary_without_borrowed_close","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_exclusive_write_complete_readback_and_explicit_owning_close_time_interval","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_exclusive_write_non_time_ID_attrs_creation_backwards_time_content_parent_refused","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_read_write_query_refusals_close_owned_CRT_fds_and_never_clear_failed_outputs"]
SELECTOR_SOURCE = Path("/root/nativecmpkit-source-proposals-20261105/windows-source-identity-recovery734-r2/NEW9-IDENTITY-SELECTORS734-R2.txt")
CONTROLLER = Path('/root/nativecmpkit-worktrees/javafx-ordinary-consumer1/scripts/ci/javafx_ordinary_maven_consumer.py')
SAFE_ROOT = "/root/nativecmpkit-source-proposals-20261105/windows-source-identity-recovery734-r2/candidate"

def sha(b):return hashlib.sha256(b).hexdigest()

def ident(s):return [getattr(s,k) for k in FIELDS]

def read(p, maximum=MAX):
 if p.resolve(strict=True)!=p:raise ValueError('Input path alias '+str(p))
 s=p.lstat();i=ident(s)
 if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size>maximum:raise ValueError('Nonordinary/bounded input '+str(p))
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  if ident(os.fstat(f.fileno()))!=i:raise ValueError('Opened input drift '+str(p))
  b=f.read(maximum+1)
  if ident(os.fstat(f.fileno()))!=i:raise ValueError('Read input drift '+str(p))
 if ident(p.lstat())!=i or len(b)!=s.st_size:raise ValueError('Closed input drift '+str(p))
 return b,{'bytes':len(b),'sha256':sha(b),'mode':format(stat.S_IMODE(s.st_mode),'04o'),'stat_identity':i}

def emit(name,v):
 b=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 fd=os.open(OUTPUT/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return {'path':str(OUTPUT/name),'sha256':sha(b),'bytes':len(b)}

def directory_identity(path):
 if not path.is_absolute() or path.resolve(strict=True)!=path:raise ValueError('Owned runtime directory path alias '+str(path))
 current=path.lstat()
 if not stat.S_ISDIR(current.st_mode) or stat.S_IMODE(current.st_mode)!=0o700 or current.st_uid!=os.getuid():raise ValueError('Nonordinary owned runtime directory '+str(path))
 return [current.st_dev,current.st_ino,current.st_mode,current.st_uid,current.st_gid]

def owned_mkdir(path):
 parent=path.parent
 if parent not in directory_pins or directory_identity(parent)!=directory_pins[parent]:raise ValueError('Owned runtime creation parent custody refused '+str(parent))
 path.mkdir(mode=0o700)
 directory_pins[path]=directory_identity(path)
 if directory_identity(parent)!=directory_pins[parent]:raise ValueError('Owned runtime creation parent drift '+str(parent))


def snapshot(expected, deadline):
    rows = {}
    for absolute, old in expected.items():
        if time.monotonic() >= deadline:
            raise TimeoutError('Bounded IDENTITY9 source custody exhausted its allocation')
        raw, current = read(Path(absolute))
        if any(current[key] != old[key] for key in ('bytes', 'sha256', 'mode')):
            raise ValueError('Frozen IDENTITY9 source endpoint changed: ' + absolute)
        if old.get('stat_identity') is not None and current['stat_identity'] != old['stat_identity']:
            raise ValueError('IDENTITY9 source identity changed: ' + absolute)
        rows[absolute] = current
    return rows


def main():
    global directory_pins
    started = time.monotonic()
    deadline = started + TOTAL
    execution_deadline = deadline - CLEANUP_RESERVE
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--source-seal-sha256', required=True)
    args = parser.parse_args()
    if HERE != FIXED_HERE:
        raise ValueError('Keep the exact external frozen runner path')
    OUTPUT.mkdir(mode=0o700)  # Existing output, even a failed attempt, forbids replay.
    directory_pins = {OUTPUT: directory_identity(OUTPUT)}
    process = None
    pin = None
    before = after = None
    child_rc = None
    primary = None
    capture_complete = capture_overflow = False
    captured = {'stdout': 0, 'stderr': 0}
    total_observed = 0
    cleanup = []
    runtime_cleanup = []
    child_report = None
    runtime = OUTPUT / 'runtime-FIRST-IDENTITY9'
    watch = selectors.DefaultSelector()
    def budget(cutoff, message):
        if time.monotonic() >= cutoff:
            raise TimeoutError(message)
    try:
        seal_raw, seal_row = read(HERE / 'RUNNER-SOURCE-SEAL734-R2.json')
        if seal_row['sha256'] != args.source_seal_sha256:
            raise ValueError('Exact lead-reviewed source-seal bytes required, not an approval flag')
        seal = json.loads(seal_raw)
        if (seal['schema'] != 'nativecmpkit-Windows-IDENTITY9-runner-source-seal734-r2' or
            seal['selectors'] != SELECTED or (len(SELECTED) != 9 or len(set(SELECTED)) != 9) or
            seal['total_seconds'] != TOTAL or seal['cleanup_reserve_seconds'] != CLEANUP_RESERVE or
            seal['combined_stdout_stderr_cap_bytes'] != OUTPUT_CAP):
            raise ValueError('Exact finite source/selection/budget recipe required')
        expected = dict(seal['external_inputs'])
        expected.update({str(HERE / relative): row for relative, row in seal['runner_files'].items()})
        expected[str(HERE / 'RUNNER-SOURCE-SEAL734-R2.json')] = seal_row
        before = snapshot(expected, execution_deadline)
        if read(SELECTOR_SOURCE)[0].decode().splitlines() != SELECTED:
            raise ValueError('The actual exact nine-selector file changed')
        controller = read(CONTROLLER)[0]
        import ast  # Standard library only; do not import the controller.
        authority = [node for node in ast.parse(controller).body if isinstance(node, ast.Assign) and
                     any(isinstance(target, ast.Name) and target.id == 'REVIEWED_EXPECTATIONS_SHA256' for target in node.targets)]
        if len(authority) != 1 or not isinstance(authority[0].value, ast.Constant) or authority[0].value.value is not None:
            raise ValueError('Production authority must stay None in this synthetic source-only cohort')
        emit('INPUTS-BEFORE.json', before)
        emit('INTENT.json', {'exact_selectors': SELECTED, 'unique_NEW_methods': 9, 'source_seal': seal_row,
             'primary_source_names': list(seal['primary_sources']), 'finite_input_count': len(before),
             'total_seconds': TOTAL, 'cleanup_reserve_seconds': CLEANUP_RESERVE,
             'combined_stdout_stderr_cap_bytes': OUTPUT_CAP, 'accepted_populations_replayed': 0,
             'ROOT_worktree_Git_GitHub_CI_Gradle_native_publication_mutations': 0,
             'synthetic_only': True, 'independent_actual_result_acceptance': False})
        owned_mkdir(runtime)
        for name in ('home', 'tmp', 'pycache'):
            owned_mkdir(runtime / name)
        environment = {'PATH': '/usr/bin:/bin', 'HOME': str(runtime / 'home'), 'TMPDIR': str(runtime / 'tmp'),
                       'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1',
                       'PYTHONNOUSERSITE': '1', 'PYTHONHASHSEED': '0',
                       'NATIVECMPKIT_OBSERVER_TEST_SOURCE_ROOT': SAFE_ROOT}
        argv = ['/usr/bin/python3.12', '-I', '-B', '-S', '-u', str(HERE / 'child_identity9_734.py')]
        emit('CHILD-COMMAND.json', {'argv': argv, 'cwd': str(runtime), 'no_parent_environment_values_exported': True,
                                   'remaining_execution_seconds': max(0, execution_deadline - time.monotonic())})
        budget(execution_deadline, 'IDENTITY9 source/runtime preflight exhausted the shared execution allocation; no child started')
        with (OUTPUT / 'stdout.log').open('xb') as stdout, (OUTPUT / 'stderr.log').open('xb') as stderr:
            os.fchmod(stdout.fileno(), 0o600)
            os.fchmod(stderr.fileno(), 0o600)
            process = subprocess.Popen(argv, cwd=runtime, env=environment, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            pin = {'pid': process.pid, 'pgid': os.getpgid(process.pid), 'session': os.getsid(process.pid)}
            if pin['pid'] != pin['pgid'] or pin['pid'] != pin['session']:
                raise ValueError('The owned child must retain its initial group/session identity')
            emit('ORIGINAL-CHILD-PIN.json', pin)
            for label, stream, target in (('stdout', process.stdout, stdout), ('stderr', process.stderr, stderr)):
                os.set_blocking(stream.fileno(), False)
                watch.register(stream, selectors.EVENT_READ, (label, target))
            while watch.get_map():
                budget(execution_deadline, 'IDENTITY9 capture exceeded its shared execution allocation')
                for key, events in watch.select(min(0.25, max(0, execution_deadline - time.monotonic()))):
                    block = os.read(key.fileobj.fileno(), 65536)
                    if not block:
                        watch.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    label, target = key.data
                    room = OUTPUT_CAP - sum(captured.values())
                    total_observed += len(block)
                    portion = block[:max(0, room)]
                    target.write(portion)
                    captured[label] += len(portion)
                    if len(portion) != len(block):
                        capture_overflow = True
                        raise ValueError('IDENTITY9 combined capture exceeded1MiB; retained first prefix is incomplete')
            while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
                budget(execution_deadline, 'IDENTITY9 unreaped child exceeded its shared execution allocation')
                time.sleep(0.05)
            capture_complete = True
    except BaseException as error:
        primary = {'type': type(error).__name__, 'message': str(error)}
    finally:
        watch.close()
        if process is not None:
            # Preserve the owned direct child unreaped until the whole group is disposed.
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    if pin is None or pin['pgid'] != process.pid or pin['session'] != process.pid:
                        raise ValueError('Owned child group pin invalid')
                    os.killpg(pin['pgid'], sig)
                    cleanup.append({'signal': sig.name, 'sent': True})
                except ProcessLookupError:
                    cleanup.append({'signal': sig.name, 'group_already_absent': True})
                except BaseException as error:
                    cleanup.append({'signal': sig.name, 'error_type': type(error).__name__, 'message': str(error)})
            try:
                budget(deadline, 'IDENTITY9 cleanup allocation exhausted before direct-child reap')
                child_rc = process.wait(timeout=min(3, max(0.001, deadline - time.monotonic())))
            except BaseException as error:
                cleanup.append({'wait_error_type': type(error).__name__})
            try:
                os.killpg(process.pid, 0)
                cleanup.append({'group_absent': False})
            except ProcessLookupError:
                cleanup.append({'group_absent': True})
            except BaseException as error:
                cleanup.append({'group_absence_error': type(error).__name__})
            for stream in (process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    try:
                        stream.close()
                    except BaseException as error:
                        cleanup.append({'pipe_close_error': type(error).__name__})
        custody_error = None
        if before is not None:
            try:
                after = snapshot(before, deadline)
                emit('INPUTS-AFTER.json', after)
            except BaseException as error:
                custody_error = {'type': type(error).__name__, 'message': str(error)}
        group_safe = process is None or any(row.get('group_absent') is True for row in cleanup)
        for name in ('home', 'tmp', 'pycache', 'runtime-FIRST-IDENTITY9'):
            path = runtime if name == 'runtime-FIRST-IDENTITY9' else runtime / name
            if path not in directory_pins:
                runtime_cleanup.append({'owned': name, 'not_created_by_wrapper': True})
                continue
            try:
                budget(deadline, 'IDENTITY9 total allocation exhausted before owned runtime cleanup')
                if not group_safe:
                    raise ValueError('Owned runtime cleanup requires group absence or no child started')
                parent = path.parent
                if parent not in directory_pins:
                    raise ValueError('Owned runtime cleanup parent not recorded')
                fresh_parent, fresh_child = directory_identity(parent), directory_identity(path)
                if fresh_parent != directory_pins[parent] or fresh_child != directory_pins[path]:
                    raise ValueError('Owned runtime cleanup parent/child identity drift')
                path.rmdir()
                runtime_cleanup.append({'owned': name, 'empty_removed': True,
                                        'fresh_parent_identity': fresh_parent, 'fresh_child_identity': fresh_child})
            except BaseException as error:
                runtime_cleanup.append({'owned': name, 'removed': False, 'error_type': type(error).__name__})
        logs = {}
        output_error = None
        try:
            for name in ('stdout.log', 'stderr.log'):
                path = OUTPUT / name
                if path.exists():
                    budget(deadline, 'IDENTITY9 total allocation exhausted before bounded log readback')
                    raw, row = read(path, OUTPUT_CAP)
                    logs[name] = row
                    if name == 'stdout.log' and capture_complete and not capture_overflow:
                        child_report = json.loads(raw)
            if len(logs) != 2 or sum(row['bytes'] for row in logs.values()) > OUTPUT_CAP:
                raise ValueError('Both complete first logs must be within the combined1MiB cap')
        except BaseException as error:
            output_error = {'type': type(error).__name__, 'message': str(error)}
        elapsed = time.monotonic() - started
        budget_error = None if elapsed < TOTAL else {'type': 'TimeoutError', 'message': 'Measured total IDENTITY9 exceeded180s; not accepted'}
        group_absent = any(row.get('group_absent') is True for row in cleanup)
        group_errors = any(any(key in row for key in ('error_type', 'wait_error_type', 'group_absence_error', 'pipe_close_error')) for row in cleanup)
        runtime_removed = len(runtime_cleanup) == 4 and all(row.get('empty_removed') is True for row in runtime_cleanup)
        report_complete = (type(child_report) is dict and child_report.get('schema') == 'nativecmpkit-Windows-IDENTITY9-child-result734-r2' and
                           child_report.get('tests_run') == 9 and set(child_report.get('methods', {})) == set(SELECTED))
        passed = (primary is None and custody_error is None and output_error is None and budget_error is None and
                  before is not None and before == after and child_rc == 0 and capture_complete and not capture_overflow and
                  group_absent and not group_errors and runtime_removed and report_complete and child_report.get('successful') is True and
                  child_report.get('method_counts') == {'PASS': 9, 'FAIL': 0, 'ERROR': 0, 'SKIP': 0, 'UNKNOWN': 0} and
                  child_report.get('failure_records') == child_report.get('error_records') == child_report.get('skipped') ==
                  child_report.get('expected_failures') == child_report.get('unexpected_successes') == 0 and
                  not child_report.get('forbidden_modules') and not child_report.get('remaining_threads'))
        result = {'schema': 'nativecmpkit-Windows-IDENTITY9-one-shot-result734-r2', 'outcome': 'passed' if passed else 'failed-or-refused',
                  'child_exit': child_rc, 'primary_refusal': primary, 'custody_refusal': custody_error,
                  'output_refusal': output_error, 'budget_refusal': budget_error, 'elapsed_seconds': elapsed,
                  'total_seconds': TOTAL, 'cleanup_reserve_seconds': CLEANUP_RESERVE,
                  'combined_stdout_stderr_cap_bytes': OUTPUT_CAP, 'captured_bytes': captured, 'observed_output_bytes': total_observed,
                  'capture_complete': capture_complete, 'capture_overflow': capture_overflow,
                  'finite_input_count': len(before) if before is not None else 0, 'inputs_before_after_held': before is not None and before == after,
                  'exact_NEW_selectors': SELECTED, 'unique_NEW_methods': 9, 'logs': logs, 'child_report': child_report,
                  'owned_group_absent': group_absent, 'cleanup': cleanup, 'runtime_cleanup': runtime_cleanup,
                  'created_runtime_directory_pins': {str(path): value for path, value in directory_pins.items() if path != OUTPUT},
                  'owned_output_parent_pin': directory_pins[OUTPUT], 'owned_runtime_removed': runtime_removed,
                  'accepted_populations_replayed': 0, 'synthetic_only': True, 'real_authority_stays_None': True,
                  'ROOT_worktree_Git_GitHub_CI_Gradle_native_publication_mutations': 0,
                  'independent_actual_result_acceptance': False, 'real_trust_native_consumer_release_ready': False}
        emit('FIRST-RESULT.json', result)
        print(json.dumps(result, sort_keys=True), flush=True)
        # Include original result emission in the total before any successful exit.
        terminal_elapsed = time.monotonic() - started
        if terminal_elapsed >= TOTAL:
            emit('TERMINAL-BUDGET-REFUSAL.json', {'type': 'TimeoutError',
                 'terminal_elapsed_seconds': terminal_elapsed,
                 'message': 'First receipt retained but full IDENTITY9 terminal allocation exceeded180s; no acceptance'})
            return 2
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
