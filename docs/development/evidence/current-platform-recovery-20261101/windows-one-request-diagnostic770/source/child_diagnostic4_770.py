# SPDX-License-Identifier: Apache-2.0
"""Lead-only NEW DIAGNOSTIC4 child: imports only diagnostic/observer/NEW4; one AF_UNIX pair.

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

OBSERVER = Path("/root/nativecmpkit-source-proposals-20261105/windows-one-request-diagnostic770-r1/candidate/scripts/ci/windows_ordinary_dependency_observer742.py")
TEST = Path("/root/nativecmpkit-source-proposals-20261105/windows-one-request-diagnostic770-r1/candidate/scripts/ci/test_windows_observer_one_request_diagnostic770.py")
HELPER = Path("/root/nativecmpkit-source-proposals-20261105/windows-one-request-diagnostic770-r1/candidate/scripts/ci/windows_observer_one_request_diagnostic770.py")
REFERENCE_ROOT = "/root/nativecmpkit-source-proposals-20261105/windows-one-request-diagnostic770-r1/candidate"
SELECTORS = ["test_windows_observer_one_request_diagnostic770.WindowsOneRequestDiagnostic770Tests.test_NEW_owned_operation_errors_preserve_primary_and_bounded_integer_codes","test_windows_observer_one_request_diagnostic770.WindowsOneRequestDiagnostic770Tests.test_NEW_real_httpresponse_full_read_close_boundary_is_attributed_not_original766_cause","test_windows_observer_one_request_diagnostic770.WindowsOneRequestDiagnostic770Tests.test_NEW_sanitized_refusal_unknown_error_and_cleanup_never_promote_HTTP200","test_windows_observer_one_request_diagnostic770.WindowsOneRequestDiagnostic770Tests.test_CHANGED_route_inverse_fixed_row_and_NEW_worker_lifecycle_source"]

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
    raise RuntimeError('NEW DIAGNOSTIC4 denies all real network, subprocess and tool execution')

def main():
    if len(sys.argv) != 1 or os.environ.get('NATIVECMPKIT_DIAGNOSTIC_TEST_SOURCE_ROOT') != REFERENCE_ROOT:
        raise ValueError('Only the held external new observer source-test environment')
    before_threads = {thread.ident for thread in threading.enumerate()}
    # Preserve real stdlib AF_UNIX socketpair; deny every external/socket-path
    # operation. These are execution denials, not successful transport fakes.
    actual_socket = socket.socket
    actual_socketpair = socket.socketpair
    pair_socket_wraps = [0]
    pair_creation = [False]
    pairs_created = [0]
    def local_pair_socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, fileno=None):
        if (not pair_creation[0] or family != socket.AF_UNIX or type != socket.SOCK_STREAM or
            proto != 0 or type_of(fileno) is not int or fileno < 0 or pair_socket_wraps[0] >= 2):
            raise RuntimeError('Only the two actual owned AF_UNIX socketpair descriptor wraps')
        pair_socket_wraps[0] += 1
        return actual_socket(family, type, proto, fileno=fileno)
    def one_owned_socketpair(family=socket.AF_UNIX, type=socket.SOCK_STREAM, proto=0):
        if family != socket.AF_UNIX or type != socket.SOCK_STREAM or proto != 0 or pairs_created[0] != 0:
            raise RuntimeError('Only one real owned AF_UNIX socketpair boundary')
        pairs_created[0] += 1
        pair_creation[0] = True
        try:
            pair = actual_socketpair(family, type, proto)
            if pair_socket_wraps[0] != 2 or len(pair) != 2 or any(item.family != socket.AF_UNIX for item in pair):
                raise RuntimeError('Exact real AF_UNIX socketpair shape')
            return pair
        finally:
            pair_creation[0] = False
    def audit(event, arguments):
        if event in ('socket.connect', 'socket.bind', 'socket.sendto', 'subprocess.Popen', 'os.system', 'ctypes.dlopen'):
            raise RuntimeError('Diagnostic NEW4 denies external network, path sockets, tools and DLL loading')
        if event == 'socket.__new__' and (not pair_creation[0] or arguments[1] != socket.AF_UNIX):
            raise RuntimeError('Diagnostic NEW4 allows only actual owned AF_UNIX pair creation')
    type_of = type
    socket.socket = local_pair_socket
    socket.socketpair = one_owned_socketpair
    socket.create_connection = socket.getaddrinfo = denied
    sys.addaudithook(audit)
    subprocess.Popen = subprocess.run = subprocess.call = subprocess.check_call = subprocess.check_output = denied
    os.system = os.popen = denied
    for name in ('CDLL', 'PyDLL', 'WinDLL', 'OleDLL'):
        setattr(ctypes, name, denied)
    helper = load_exact('windows_observer_one_request_diagnostic770', HELPER)
    sys.modules['_nativecmpkit_observer742_diagnostic770'] = helper.base
    controls = load_exact('test_windows_observer_one_request_diagnostic770', TEST)
    klass = controls.WindowsOneRequestDiagnostic770Tests
    methods = [selector.rsplit('.', 1)[1] for selector in SELECTORS]
    if sorted(name for name in dir(klass) if name.startswith('test_')) != sorted(methods):
        raise ValueError('Only the four actually authored NEW diagnostic methods')
    suite = unittest.TestSuite(klass(method) for method in methods)
    if suite.countTestCases() != 4:
        raise ValueError('Exact NEW DIAGNOSTIC4 suite required')
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=RecordedResult).run(suite)
    actual_external = sorted({str(Path(module.__file__).resolve()) for name, module in list(sys.modules.items())
        if name != '__main__' and isinstance(getattr(module, '__file__', None), str) and '/nativecmpkit-' in module.__file__})
    expected_external = sorted([str(OBSERVER), str(HELPER), str(TEST)])
    forbidden = sorted(set(sys.modules) & {'javafx_ordinary_maven_consumer', 'javafx_ordinary_dependency_expectations',
        'test_javafx_ordinary_dependency_expectations742', 'library_tests', 'webview_consumer', 'daemon_jvm',
        'runtime_context', 'failure_diagnostics', 'build_runtime_candidate', 'probe_runner'})
    remaining_threads = [{'name': thread.name, 'daemon': thread.daemon} for thread in threading.enumerate()
                         if thread.ident not in before_threads]
    statuses = ('PASS', 'FAIL', 'ERROR', 'SKIP', 'UNKNOWN')
    counts = {status: sum(row['status'] == status for row in result.methods.values()) for status in statuses}
    successful = (result.wasSuccessful() and result.testsRun == 4 and set(result.methods) == set(SELECTORS) and
        counts['PASS'] == 4 and not any(counts[status] for status in statuses if status != 'PASS') and
        not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses and
        actual_external == expected_external and not forbidden and not remaining_threads and
        pairs_created[0] == 1 and pair_socket_wraps[0] == 2 and not pair_creation[0])
    data = {'schema': 'nativecmpkit-Windows-DIAGNOSTIC4-child-result770-r1', 'tests_run': result.testsRun,
        'suite_seconds': time.monotonic() - started, 'methods': result.methods, 'method_counts': counts,
        'subtests': result.subtests, 'subtest_count': len(result.subtests), 'failure_records': len(result.failures),
        'error_records': len(result.errors), 'skipped': len(result.skipped), 'expected_failures': len(result.expectedFailures),
        'unexpected_successes': len(result.unexpectedSuccesses), 'unittest_successful': result.wasSuccessful(),
        'successful': successful, 'forbidden_modules': forbidden, 'actual_external_modules': actual_external,
        'expected_external_modules': expected_external, 'remaining_threads': remaining_threads, 'owned_socketpairs_created': pairs_created[0],
        'real_AF_UNIX_pair_descriptor_wraps': pair_socket_wraps[0], 'pair_creation_in_progress': pair_creation[0],
        'remote_network_subprocess_and_tools_denied': True, 'source_only': True, 'owned_AF_UNIX_socketpair_boundary_only': True, 'real_trust_native_Gradle_release_clearance': False}
    print(json.dumps(data, sort_keys=True), flush=True)
    return 0 if successful else 1

if __name__ == '__main__':
    raise SystemExit(main())
