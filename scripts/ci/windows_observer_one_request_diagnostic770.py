# SPDX-License-Identifier: Apache-2.0
"""Private one-row operation diagnostic, not an original120 rerun or trust gate.

The real original observe_one is delegated to, not repaired or supplied a fake
successful response. Only caught owning-operation tags and bounded error numbers
leave the worker; no response bytes, URL, headers or exception message is public.
A successful diagnostic protocol is not a complete/public-text response and
does not identify original766's missing operation/errno/winerror retroactively.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
OBSERVER = 'scripts/ci/windows_ordinary_dependency_observer742.py'
OBSERVER_BYTES = 65242
OBSERVER_SHA256 = '23c89b500571dff6f347a349b59391e0b6c816493f08b2232130f7aa73d82c14'
OUTPUT = 'build/ci-verification/windows-one-request-diagnostic770'
CHOICE = 'windows-observer-one-request-diagnostic1'
REQUEST_ID = 'convention-gradlePlugin-android:pom'
REQUEST = {
    'id': REQUEST_ID, 'seed': 'convention-gradlePlugin-android', 'kind': 'pom',
    'url': 'https://dl.google.com/dl/android/maven2/com/android/tools/build/gradle/9.4.0/gradle-9.4.0.pom',
}
TOTAL_SECONDS = 90
CLEANUP_SECONDS = 30
ACQUISITION_SECONDS = 45
MAX_ERRORS = 16
TRANSPORT_OPERATIONS = frozenset((
    'connection-create', 'connection-connect', 'connection-request', 'connection-getresponse',
    'transport-settimeout-before-request', 'transport-settimeout-headers', 'transport-settimeout-body',
    'response-getheaders', 'response-read1', 'response-close', 'connection-close',
))
OPERATIONS = TRANSPORT_OPERATIONS | frozenset((
    'controller-owning-protocol', 'capture-stdout', 'capture-stderr', 'capture-stream-close',
    'direct-child-cleanup', 'job-empty-accounting', 'job-handle-close', 'capture-thread-join',
    'source-after', 'empty-runtime-remove', 'worker-receipt-read', 'diagnostic-entry',
))
spec = importlib.util.spec_from_file_location('_nativecmpkit_observer742_diagnostic770', ROOT / OBSERVER)
if spec is None or spec.loader is None:
    raise ValueError('Exact owning observer module loader required')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

# The actual owning Job, Win32 custody/writer, environment and cleanup primitives
# are reused. No native/Gradle/consumer/dependency controller is imported.
need = base.need
digest = base.digest
bounded_time = base.bounded_time
read_regular = base.read_regular
strict_json = base.strict_json
relative_path = base.relative_path
directory_pin = base.directory_pin
create_owned = base.create_owned
write_exclusive = base.write_exclusive
json_bytes = base.json_bytes
WindowsJob = base.WindowsJob
assigned_go = base.assigned_go
safe_environment = base.safe_environment
REPOSITORY = base.REPOSITORY
REF = base.REF
NO_ADMISSION = base.NO_ADMISSION
MAX_CAPTURE = base.MAX_CAPTURE
MAX_BODY = base.MAX_BODY
SOURCE_LIMIT = base.SOURCE_LIMIT
load_plan = base.load_plan


def bounded_error_number(error, field, minimum, maximum):
    try:
        value = getattr(error, field, None)
    except BaseException:
        return None
    return value if type(value) is int and minimum <= value <= maximum else None


def fault(operation, error):
    need(operation in OPERATIONS, 'Only fixed bounded owning-operation tags')
    return {
        'operation': operation,
        'errno': bounded_error_number(error, 'errno', -(2**31), 2**31 - 1),
        'winerror': bounded_error_number(error, 'winerror', 0, 2**32 - 1),
    }


class OperationRecorder:
    def __init__(self):
        self.errors = []
        self.overflow = False

    def call(self, operation, function, *args, **kwargs):
        need(operation in TRANSPORT_OPERATIONS, 'No caller or last-operation inferred tag')
        try:
            return function(*args, **kwargs)
        except BaseException as error:
            if len(self.errors) < MAX_ERRORS:
                self.errors.append(fault(operation, error))
            else:
                self.overflow = True
            raise  # Preserve the exact primary exception, never a diagnostic replacement.


class DelegatingTransport:
    def __init__(self, actual, recorder, owner):
        self.actual, self.recorder, self.owner = actual, recorder, owner

    def settimeout(self, seconds):
        return self.recorder.call(self.owner.timeout_operation, self.actual.settimeout, seconds)


class DelegatingResponse:
    def __init__(self, actual, recorder):
        self.actual, self.recorder = actual, recorder

    @property
    def status(self):
        return self.actual.status

    def isclosed(self):
        # Read-only owning lifetime, never an EOF/completeness assertion.
        return self.actual.isclosed()

    def getheaders(self):
        return self.recorder.call('response-getheaders', self.actual.getheaders)

    def read1(self, count):
        return self.recorder.call('response-read1', self.actual.read1, count)

    def close(self):
        return self.recorder.call('response-close', self.actual.close)


class DelegatingConnection:
    def __init__(self, actual, recorder):
        self.actual, self.recorder, self.transport = actual, recorder, None
        self.timeout_operation = 'transport-settimeout-before-request'

    @property
    def sock(self):
        return self.transport

    def connect(self):
        result = self.recorder.call('connection-connect', self.actual.connect)
        if self.actual.sock is not None:
            self.transport = DelegatingTransport(self.actual.sock, self.recorder, self)
        return result

    def request(self, *args, **kwargs):
        result = self.recorder.call('connection-request', self.actual.request, *args, **kwargs)
        self.timeout_operation = 'transport-settimeout-headers'
        return result

    def getresponse(self):
        response = self.recorder.call('connection-getresponse', self.actual.getresponse)
        self.timeout_operation = 'transport-settimeout-body'
        return DelegatingResponse(response, self.recorder)

    def close(self):
        return self.recorder.call('connection-close', self.actual.close)


def actual_recording_factory(recorder):
    def factory(hostname, **kwargs):
        actual = recorder.call('connection-create', http.client.HTTPSConnection, hostname, **kwargs)
        return DelegatingConnection(actual, recorder)
    return factory


def select_fixed_request(plan):
    need(type(plan) is dict and type(plan.get('requests')) is list and len(plan['requests']) == 120,
         'Original120 plan must remain complete and unmodified')
    row = plan['requests'][0]
    need(row == REQUEST and sum(entry.get('id') == REQUEST_ID for entry in plan['requests']) == 1,
         'Only original index0 convention-gradlePlugin-android:pom; no selector or caller URL')
    base.validate_request(row, plan)
    return row


def snapshot_sources(root, plan, clock=time.monotonic, deadline=None):
    rows = base.snapshot_sources(root, plan, clock=clock, deadline=deadline)
    owning = rows[OBSERVER]
    need((owning['bytes'], owning['sha256']) == (OBSERVER_BYTES, OBSERVER_SHA256),
         'Exact source-qualified diagnostic workflow inverse observer required')
    if deadline is not None:
        bounded_time(deadline, 'Diagnostic self custody exhausted shared allocation', clock)
    relative = 'scripts/ci/windows_observer_one_request_diagnostic770.py'
    rows[relative] = read_regular(root, relative)[1]
    return rows


OBSERVATION_KEYS = frozenset((
    'schema', 'request_id', 'kind', 'status', 'http_status', 'body_bytes', 'body_sha256',
    'complete_response', 'public_text_qualified', 'primary_errors', 'cleanup_errors',
    'operation_error_overflow', 'unattributed_refusal', 'body_retained_privately',
    'raw_body_exported', 'original766_cause_qualified',
))


def validate_diagnostic_observation(row):
    need(type(row) is dict and set(row) == OBSERVATION_KEYS and
         row['schema'] == 'nativecmpkit-Windows-one-request-diagnostic770-observation-r1' and
         row['request_id'] == REQUEST_ID and row['kind'] == 'pom' and row['status'] in ('observed', 'refused'),
         'Only the exact sanitized one-row schema')
    need(row['http_status'] is None or type(row['http_status']) is int and 100 <= row['http_status'] <= 599,
         'Bounded nullable integer HTTP status')
    need(type(row['body_bytes']) is int and 0 <= row['body_bytes'] <= MAX_BODY and
         (row['body_sha256'] is None if row['body_bytes'] == 0 else
          type(row['body_sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['body_sha256']) is not None),
         'Bounded body count and digest, never response bytes')
    for name in ('complete_response', 'public_text_qualified', 'operation_error_overflow', 'unattributed_refusal',
                 'body_retained_privately', 'raw_body_exported', 'original766_cause_qualified'):
        need(type(row[name]) is bool, 'Exact diagnostic booleans')
    need(row['raw_body_exported'] is False and row['original766_cause_qualified'] is False and
         row['body_retained_privately'] == (row['body_bytes'] > 0), 'Private bytes; no retroactive original cause')
    need(type(row['primary_errors']) is list and type(row['cleanup_errors']) is list and
         len(row['primary_errors']) + len(row['cleanup_errors']) <= MAX_ERRORS, 'Bounded operation-error evidence')
    for group, cleanup in ((row['primary_errors'], False), (row['cleanup_errors'], True)):
        for error in group:
            need(type(error) is dict and set(error) == {'operation', 'errno', 'winerror'} and
                 error['operation'] in TRANSPORT_OPERATIONS and
                 (error['operation'] in ('response-close', 'connection-close')) == cleanup,
                 'Exact owning primary/cleanup error tags; no messages or inferred operation')
            need(error['errno'] is None or type(error['errno']) is int and -(2**31) <= error['errno'] <= 2**31 - 1,
                 'Bounded nullable integer errno')
            need(error['winerror'] is None or type(error['winerror']) is int and 0 <= error['winerror'] <= 2**32 - 1,
                 'Bounded nullable integer winerror')
    need(row['unattributed_refusal'] ==
         (row['status'] == 'refused' and not row['primary_errors'] and not row['cleanup_errors']),
         'Uninstrumented refusal stays unattributed; no last-operation causation')
    need(not row['public_text_qualified'] or row['complete_response'] and row['status'] == 'observed' and
         not row['primary_errors'] and not row['cleanup_errors'] and not row['operation_error_overflow'],
         'Transport/syntax qualification is never inferred from HTTP200')


def sanitize_observation(observed, recorder):
    need(observed.get('id') == REQUEST_ID and observed.get('kind') == 'pom', 'Owning exact observation row')
    errors = [dict(item) for item in recorder.errors]
    cleanup = [item for item in errors if item['operation'] in ('response-close', 'connection-close')]
    primary = [item for item in errors if item['operation'] not in ('response-close', 'connection-close')]
    row = {
        'schema': 'nativecmpkit-Windows-one-request-diagnostic770-observation-r1',
        'request_id': REQUEST_ID, 'kind': 'pom', 'status': observed['status'],
        'http_status': observed.get('http_status'), 'body_bytes': observed['body_bytes'],
        'body_sha256': observed['body_sha256'], 'complete_response': observed['complete_response'],
        'public_text_qualified': observed['public_text_qualified'],
        'primary_errors': primary, 'cleanup_errors': cleanup, 'operation_error_overflow': recorder.overflow,
        'unattributed_refusal': observed['status'] == 'refused' and not primary and not cleanup,
        'body_retained_privately': observed['body_bytes'] > 0, 'raw_body_exported': False,
        'original766_cause_qualified': False,
    }
    validate_diagnostic_observation(row)
    return row


WORKER_KEYS = frozenset((
    'schema', 'diagnostic_protocol_complete', 'requests_attempted', 'planned_requests',
    'original120_plan_requests', 'raw_body_bytes', 'all_response_bodies_private',
    'source_inputs_held', 'source_inputs_before', 'source_inputs_after', 'diagnostic_observation',
    'no_admission', 'archive_reuse', 'original14_binaries_or_sidecars_acquired', 'elapsed_seconds',
))


def validate_worker_report(report, before):
    need(type(report) is dict and set(report) == WORKER_KEYS and
         report['schema'] == 'nativecmpkit-Windows-one-request-diagnostic770-worker-r1' and
         type(report['diagnostic_protocol_complete']) is bool and report.get('original120_plan_requests') == 120 and
         report.get('requests_attempted') == report.get('planned_requests') == 1 and
         report.get('source_inputs_before') == report.get('source_inputs_after') == before and
         report.get('no_admission') == NO_ADMISSION and
         report.get('all_response_bodies_private') is True and report.get('archive_reuse') == [],
         'Exact source-held one-request diagnostic, no renamed original120 success')
    validate_diagnostic_observation(report.get('diagnostic_observation'))
    need(report.get('raw_body_bytes') == report['diagnostic_observation']['body_bytes'],
         'Actual one-request network accounting and sanitized byte count agree')


def worker(root, output, job_handle):
    # Real network is unreachable until the exact owning assignment GO and
    # fresh inherited Job membership/limits/active-child verification succeed.
    need(sys.stdin.buffer.readline(16) == b'GO742\n', 'Owned Job assignment GO missing')
    need(os.name == 'nt', 'Windows-only real one-request diagnostic')
    base.verify_worker_job(job_handle)
    started = time.monotonic()
    deadline = started + ACQUISITION_SECONDS
    plan, _identity = load_plan(root)
    row = select_fixed_request(plan)
    before = snapshot_sources(root, plan, deadline=deadline)
    pins = {output: directory_pin(output), output / 'public': directory_pin(output / 'public'),
            output / 'private': directory_pin(output / 'private')}
    budget = base.NetworkBudget(deadline)
    recorder = OperationRecorder()
    observed, payload = base.observe_one(row, plan, budget, connection_factory=actual_recording_factory(recorder))
    need(budget.requests == 1, 'Exactly one original owning request, no retry or whole-plan replay')
    if payload:
        raw = write_exclusive(output, 'private/only-response.bin', payload, pins)
        need((raw['bytes'], raw['sha256']) == (observed['body_bytes'], observed['body_sha256']),
             'Exclusive private owning body agrees with actual observation count/digest')
    sanitized = sanitize_observation(observed, recorder)
    after = snapshot_sources(root, plan, deadline=deadline)
    need(before == after, 'Actual diagnostic source identities changed')
    report = {
        'schema': 'nativecmpkit-Windows-one-request-diagnostic770-worker-r1',
        'diagnostic_protocol_complete': not recorder.overflow,
        'requests_attempted': budget.requests, 'planned_requests': 1, 'original120_plan_requests': 120,
        'raw_body_bytes': budget.body_bytes, 'all_response_bodies_private': True,
        'source_inputs_held': True, 'source_inputs_before': before, 'source_inputs_after': after,
        'diagnostic_observation': sanitized, 'no_admission': dict(NO_ADMISSION), 'archive_reuse': [],
        'original14_binaries_or_sidecars_acquired': 0, 'elapsed_seconds': time.monotonic() - started,
    }
    validate_worker_report(report, before)
    need(report['elapsed_seconds'] < ACQUISITION_SECONDS, 'Measured bounded one-request diagnostic')
    write_exclusive(output, 'public/worker-diagnostic.json', json_bytes(report), pins)
    print(json.dumps({'schema': report['schema'], 'diagnostic_protocol_complete': not recorder.overflow,
                      'requests_attempted': 1, 'planned_requests': 1, 'source_inputs_held': True,
                      'no_admission': dict(NO_ADMISSION)}, sort_keys=True), flush=True)
    return 2 if recorder.overflow else 0


def manual_context(environment):
    values = {key: environment.get(key) for key in ('GITHUB_REPOSITORY', 'GITHUB_EVENT_NAME', 'GITHUB_REF',
             'NATIVECMPKIT_DIAGNOSTIC_PLATFORM', 'GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT')}
    need(values['GITHUB_REPOSITORY'] == REPOSITORY and values['GITHUB_EVENT_NAME'] == 'workflow_dispatch' and
         values['GITHUB_REF'] == REF and values['NATIVECMPKIT_DIAGNOSTIC_PLATFORM'] == CHOICE and
         type(values['GITHUB_SHA']) is str and re.fullmatch('[0-9a-f]{40}', values['GITHUB_SHA']) and
         all(type(values[key]) is str and re.fullmatch('[1-9][0-9]{0,19}', values[key])
             for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT')), 'Exact isolated manual one-request diagnostic context')
    need(os.name == 'nt' and sys.version_info[:2] == (3, 12), 'Actual Windows/Python3.12 diagnostic host')
    return values


def controller(root):
    started = time.monotonic()
    deadline, execution_deadline = started + TOTAL_SECONDS, started + TOTAL_SECONDS - CLEANUP_SECONDS
    context = manual_context(os.environ)
    plan, plan_identity = load_plan(root)
    before = snapshot_sources(root, plan, deadline=execution_deadline)
    output = root.joinpath(*relative_path(OUTPUT).parts)
    # Existing complete/failed outputs never admit replay. Only bounded owning
    # build parents may be newly created; they are retained, not broadly removed.
    pins = {root: directory_pin(root)}
    current = root
    for part in output.relative_to(root).parts:
        next_path = current / part
        if next_path == output or not next_path.exists():
            create_owned(next_path, pins)
        else:
            pins[next_path] = directory_pin(next_path)
        current = next_path
    for name in ('public', 'private', 'runtime'):
        create_owned(output / name, pins)
    runtime = output / 'runtime'
    for name in ('home', 'tmp'):
        create_owned(runtime / name, pins)
    write_exclusive(output, 'public/source-intent.json', json_bytes({'schema': 'nativecmpkit-Windows-one-request-diagnostic770-intent-r1',
        'context': context, 'plan_identity': plan_identity, 'source_inputs_before': before, 'no_admission': dict(NO_ADMISSION),
        'planned_requests': 1, 'original120_plan_requests': 120, 'fixed_request_id': REQUEST_ID, 'original14_reacquired': 0,
        'process_containment_not_OS_sandbox': True}), pins)
    process = job = None
    primary = None
    child_exit = None
    after = None
    cleanup = []
    threads = []
    capture_overflow = threading.Event()
    capture_errors = []
    captured = [0]
    capture_lock = threading.Lock()
    def capture(stream, relative):
        try:
            log = bytearray()
            while True:
                block = stream.read(65536)
                if not block:
                    break
                with capture_lock:
                    room = MAX_CAPTURE - captured[0]
                    portion = block[:max(0, room)]
                    log.extend(portion)
                    captured[0] += len(portion)
                    if len(portion) != len(block):
                        capture_overflow.set()
                        break
            write_exclusive(output, relative, bytes(log), pins)
        except BaseException as error:
            capture_errors.append(fault('capture-stdout' if relative.endswith('stdout') else 'capture-stderr', error))
        finally:
            try:
                stream.close()
            except BaseException as error:
                capture_errors.append(fault('capture-stream-close', error))
    try:
        job = WindowsJob()
        executable = Path(sys.executable).resolve(strict=True)
        argv = [str(executable), '-I', '-S', '-B', '-u', str(Path(__file__).resolve()), '--worker', '--job-handle', str(int(job.handle))]
        startup = subprocess.STARTUPINFO()
        startup.lpAttributeList = {'handle_list': [int(job.handle)]}
        job.inherit(True)
        try:
            process = subprocess.Popen(argv, cwd=runtime, env=safe_environment(runtime, executable, os.environ),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True, startupinfo=startup)
        finally:
            job.inherit(False)
        for stream, relative in ((process.stdout, 'private/worker.stdout'), (process.stderr, 'private/worker.stderr')):
            thread = threading.Thread(target=capture, args=(stream, relative), daemon=False)
            thread.start()
            threads.append(thread)
        assigned_go(process, job)
        while process.poll() is None:
            bounded_time(execution_deadline, 'Owned observational child exceeded shared60s allocation')
            need(not capture_overflow.is_set() and not capture_errors, 'Bounded owned child streams refused')
            need(job.active_processes() <= 1, 'No descendant process or alternate tooling allowed')
            time.sleep(0.05)
        child_exit = process.wait(timeout=min(1, bounded_time(execution_deadline, 'Direct child terminal budget')))
        need(child_exit == 0, 'Owning one-request diagnostic worker result was not complete')
    except BaseException as error:
        primary = fault('controller-owning-protocol', error)
    finally:
        if process is not None:
            try:
                if job is not None and job.assigned_pid == process.pid:
                    job.terminate()
                    cleanup.append({'owned_job_terminated': True})
                elif process.poll() is None:
                    # Still blocked before GO; terminate only this direct owned
                    # stable Popen handle, never a guessed PID/foreign process.
                    process.terminate()
                    cleanup.append({'unassigned_direct_child_terminated': True, 'GO_sent': False})
                child_exit = process.wait(timeout=min(CLEANUP_SECONDS, bounded_time(deadline, 'Owned child cleanup reserve')))
                cleanup.append({'direct_child_terminal': True, 'exit': child_exit})
            except BaseException as error:
                cleanup.append(dict(fault('direct-child-cleanup', error), direct_child_terminal=False))
        job_empty = False
        if job is not None:
            try:
                while job.active_processes():
                    bounded_time(deadline, 'Owned Job empty accounting cleanup reserve')
                    time.sleep(0.02)
                job_empty = True
                cleanup.append({'owned_job_active_processes': 0})
            except BaseException as error:
                cleanup.append(dict(fault('job-empty-accounting', error), owned_job_empty=False))
            try:
                job.close()  # KILL_ON_JOB_CLOSE holds even an earlier refusal.
                cleanup.append({'owned_job_handle_closed': True})
            except BaseException as error:
                cleanup.append(dict(fault('job-handle-close', error), owned_job_handle_closed=False))
        for thread in threads:
            try:
                thread.join(timeout=bounded_time(deadline, 'Bounded capture-thread cleanup reserve'))
                need(not thread.is_alive(), 'Owned capture thread remains')
            except BaseException as error:
                cleanup.append(dict(fault('capture-thread-join', error), capture_thread_terminal=False))
        try:
            after = snapshot_sources(root, plan, deadline=deadline)
            need(before == after, 'Actual source before/after custody differs')
        except BaseException as error:
            cleanup.append(dict(fault('source-after', error), source_inputs_held=False))
        direct_terminal = process is not None and process.poll() is not None
        for path in (runtime / 'home', runtime / 'tmp', runtime):
            try:
                bounded_time(deadline, 'Owned empty runtime cleanup allocation')
                need(job_empty and direct_terminal and not any(thread.is_alive() for thread in threads),
                     'Fresh Job-empty/direct-terminal/thread-terminal precede owned runtime cleanup')
                need(directory_pin(path.parent) == pins[path.parent] and directory_pin(path) == pins[path],
                     'Fresh owning parent/child directory pins before empty removal')
                path.rmdir()  # Empty only: unexpected worker files are retained/refused, not recursively deleted.
                cleanup.append({'owned_empty_directory_removed': path.name})
            except BaseException as error:
                cleanup.append(dict(fault('empty-runtime-remove', error), owned_empty_directory_removed=False))
    worker_report = None
    report_error = None
    try:
        worker_payload, worker_identity = read_regular(output, 'public/worker-diagnostic.json', SOURCE_LIMIT)
        worker_report = strict_json(worker_payload)
        validate_worker_report(worker_report, before)
        need(worker_report.get('schema') == 'nativecmpkit-Windows-one-request-diagnostic770-worker-r1' and
             worker_report.get('diagnostic_protocol_complete') is True and worker_report.get('no_admission') == NO_ADMISSION and
             worker_report.get('requests_attempted') == worker_report.get('planned_requests') == 1 and
             worker_report.get('source_inputs_before') == worker_report.get('source_inputs_after') == before and
             worker_report.get('original14_binaries_or_sidecars_acquired') == 0,
             'Exact complete untrusted worker receipt; never dependency/native admission')
    except BaseException as error:
        report_error = fault('worker-receipt-read', error)
    elapsed = time.monotonic() - started
    complete = (primary is None and report_error is None and child_exit == 0 and before == after and
                job_empty and direct_terminal and not capture_overflow.is_set() and not capture_errors and
                not any(thread.is_alive() for thread in threads) and elapsed < TOTAL_SECONDS and
                not any('operation' in row for row in cleanup) and worker_report is not None)
    report = {'schema': 'nativecmpkit-Windows-one-request-diagnostic770-controller-r1',
        'diagnostic_protocol_complete': complete, 'child_exit': child_exit, 'context': context,
        'primary_refusal': primary, 'worker_receipt_refusal': report_error, 'source_inputs_held': before == after,
        'elapsed_seconds': elapsed, 'total_seconds': TOTAL_SECONDS, 'cleanup_seconds': CLEANUP_SECONDS,
        'combined_captured_bytes': captured[0], 'capture_overflow': capture_overflow.is_set(), 'capture_errors': capture_errors,
        'owned_job_empty': job_empty, 'owned_direct_child_terminal': direct_terminal, 'cleanup': cleanup,
        'no_admission': dict(NO_ADMISSION), 'original14_or_sidecars_reacquired': 0,
        'Gradle_wrapper_Java_Rust_JAR_ZIP_native_policy_execution': 0, 'OS_sandbox_or_trusted_builder_claim': False}
    write_exclusive(output, 'public/controller-result.json', json_bytes(report), pins)
    terminal_elapsed = time.monotonic() - started
    if terminal_elapsed >= TOTAL_SECONDS:
        write_exclusive(output, 'public/terminal-budget-refusal.json', json_bytes({'schema': report['schema'],
            'diagnostic_protocol_complete': False, 'elapsed_seconds': terminal_elapsed, 'no_admission': dict(NO_ADMISSION)}), pins)
        return 2
    print(json.dumps({'schema': report['schema'], 'diagnostic_protocol_complete': complete,
                      'no_admission': dict(NO_ADMISSION)}, sort_keys=True), flush=True)
    return 0 if complete else 2


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--job-handle', type=int)
    args = parser.parse_args()
    if args.worker:
        need(args.job_handle is not None, 'A contained diagnostic worker requires the inherited owning Job handle')
        return worker(ROOT, ROOT.joinpath(*relative_path(OUTPUT).parts), args.job_handle)
    need(args.job_handle is None, 'Owning handle is internal; no caller row, URL or request count')
    return controller(ROOT)


if __name__ == '__main__':
    try:
        code = main()
    except BaseException as error:
        # No traceback/message, headers, caller URL or private stream is public.
        print(json.dumps({'schema': 'nativecmpkit-Windows-one-request-diagnostic770-entry-r1',
                          'diagnostic_protocol_complete': False,
                          'owning_refusal': fault('diagnostic-entry', error),
                          'no_admission': dict(NO_ADMISSION)}, sort_keys=True), flush=True)
        code = 2
    raise SystemExit(code)
