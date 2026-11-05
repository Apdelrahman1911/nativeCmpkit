# SPDX-License-Identifier: Apache-2.0
"""Lead-only NEW IDENTITY9 child: imports only the observer/new test, no network/tools.

Original controller/helper/library_tests and accepted8/12/Stop suites are bytes
only, never imported or executed. This child cannot qualify real Windows Job,
public HTTPS/provenance, policy, consumer/native, security or release readiness.
"""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import threading
import time
import unittest

OBSERVER = Path("/root/nativecmpkit-source-proposals-20261105/windows-source-identity-recovery734-r2/candidate/scripts/ci/windows_ordinary_dependency_observer742.py")
TEST = Path("/root/nativecmpkit-source-proposals-20261105/windows-source-identity-recovery734-r2/candidate/scripts/ci/test_windows_observer_identity_recovery734.py")
REFERENCE_ROOT = "/root/nativecmpkit-source-proposals-20261105/windows-source-identity-recovery734-r2/candidate"
SELECTORS = ["test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_new_scope_original_native_protocol_and_full_POSIXstat7_preserved","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_POSIX_reader_writer_full_crossstat7_reparse_shared_bounds_and_ancestor_refusals","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Win32_full128_ID_volume64_ABI_and_owned_vs_borrowed_handle_lifecycle","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_reader_separate_python_views_do_not_waive_native_or_own_stat_custody","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_reader_every_native_field_high_ID_and_fresh_after_read_close_drift_refused","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Win32_open_query_close_failures_fail_closed_and_keep_primary_without_borrowed_close","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_exclusive_write_complete_readback_and_explicit_owning_close_time_interval","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_exclusive_write_non_time_ID_attrs_creation_backwards_time_content_parent_refused","test_windows_observer_identity_recovery734.WindowsObserverIdentityRecovery734Tests.test_Windows_read_write_query_refusals_close_owned_CRT_fds_and_never_clear_failed_outputs"]

class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.methods, self.subtests, self.starts = {}, [], {}
    def startTest(self, test):
        self.starts[test.id()] = time.perf_counter()
        super().startTest(test)
    def stopTest(self, test):
        self.methods.setdefault(test.id(), {'status': 'UNKNOWN'})['seconds'] = time.perf_counter() - self.starts[test.id()]
        super().stopTest(test)
    def addSuccess(self, test):
        self.methods[test.id()] = {'status': 'PASS'}
        super().addSuccess(test)
    def addFailure(self, test, err):
        self.methods[test.id()] = {'status': 'FAIL'}
        super().addFailure(test, err)
    def addError(self, test, err):
        self.methods[test.id()] = {'status': 'ERROR'}
        super().addError(test, err)
    def addSkip(self, test, reason):
        self.methods[test.id()] = {'status': 'SKIP', 'reason': reason}
        super().addSkip(test, reason)
    def addSubTest(self, test, subtest, err):
        status = 'PASS' if err is None else ('FAIL' if issubclass(err[0], test.failureException) else 'ERROR')
        self.subtests.append({'selector': test.id(), 'case': str(subtest), 'status': status})
        if err is not None:
            self.methods[test.id()] = {'status': status}
        super().addSubTest(test, subtest, err)

def load_exact(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def denied(*_arguments, **_keywords):
    raise RuntimeError('NEW IDENTITY9 denies all real network, subprocess and tool execution')

def main():
    if len(sys.argv) != 1 or os.environ.get('NATIVECMPKIT_OBSERVER_TEST_SOURCE_ROOT') != REFERENCE_ROOT:
        raise ValueError('Only the held external new observer source-test environment')
    before_threads = {thread.ident for thread in threading.enumerate()}
    socket.socket = socket.create_connection = socket.getaddrinfo = denied
    subprocess.Popen = subprocess.run = subprocess.call = subprocess.check_call = subprocess.check_output = denied
    os.system = os.popen = denied
    for name in ('CDLL', 'PyDLL', 'WinDLL', 'OleDLL'):
        setattr(ctypes, name, denied)
    load_exact('windows_ordinary_dependency_observer742', OBSERVER)
    controls = load_exact('test_windows_observer_identity_recovery734', TEST)
    klass = controls.WindowsObserverIdentityRecovery734Tests
    methods = [selector.rsplit('.', 1)[1] for selector in SELECTORS]
    if sorted(name for name in dir(klass) if name.startswith('test_')) != sorted(methods):
        raise ValueError('Only the nine actually authored NEW observer methods')
    suite = unittest.TestSuite(klass(method) for method in methods)
    if suite.countTestCases() != 9:
        raise ValueError('Exact NEW IDENTITY9 suite required')
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=RecordedResult).run(suite)
    actual_external = sorted({str(Path(module.__file__).resolve()) for name, module in list(sys.modules.items())
        if name != '__main__' and isinstance(getattr(module, '__file__', None), str) and '/nativecmpkit-' in module.__file__})
    expected_external = sorted([str(OBSERVER), str(TEST)])
    forbidden = sorted(set(sys.modules) & {'javafx_ordinary_maven_consumer', 'javafx_ordinary_dependency_expectations',
        'test_javafx_ordinary_dependency_expectations742', 'library_tests', 'webview_consumer', 'daemon_jvm',
        'runtime_context', 'failure_diagnostics', 'build_runtime_candidate', 'probe_runner'})
    remaining_threads = [{'name': thread.name, 'daemon': thread.daemon} for thread in threading.enumerate()
                         if thread.ident not in before_threads]
    statuses = ('PASS', 'FAIL', 'ERROR', 'SKIP', 'UNKNOWN')
    counts = {status: sum(row['status'] == status for row in result.methods.values()) for status in statuses}
    successful = (result.wasSuccessful() and result.testsRun == 9 and set(result.methods) == set(SELECTORS) and
        counts['PASS'] == 9 and not any(counts[status] for status in statuses if status != 'PASS') and
        not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses and
        actual_external == expected_external and not forbidden and not remaining_threads)
    data = {'schema': 'nativecmpkit-Windows-IDENTITY9-child-result734-r2', 'tests_run': result.testsRun,
        'suite_seconds': time.monotonic() - started, 'methods': result.methods, 'method_counts': counts,
        'subtests': result.subtests, 'subtest_count': len(result.subtests), 'failure_records': len(result.failures),
        'error_records': len(result.errors), 'skipped': len(result.skipped), 'expected_failures': len(result.expectedFailures),
        'unexpected_successes': len(result.unexpectedSuccesses), 'unittest_successful': result.wasSuccessful(),
        'successful': successful, 'forbidden_modules': forbidden, 'actual_external_modules': actual_external,
        'expected_external_modules': expected_external, 'remaining_threads': remaining_threads,
        'network_subprocess_and_tools_denied': True, 'synthetic_only': True, 'real_trust_native_Gradle_release_clearance': False}
    print(json.dumps(data, sort_keys=True), flush=True)
    return 0 if successful else 1

if __name__ == '__main__':
    raise SystemExit(main())
