# SPDX-License-Identifier: Apache-2.0
"""Lead-only NEW4 plus changed2 OWNED-EOF6 child; six serial bounded AF_UNIX pairs.

Only observer/diagnostic and three selected source-test modules are imported.
Only exact NEW4 and owning changed2 methods execute; other accepted populations,
controllers/library_tests/Stop are never executed. This cannot qualify Windows Job,
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

OBSERVER = Path("/root/nativecmpkit-source-proposals-20261105/windows-observer-owned-eof-after770-r1/candidate/scripts/ci/windows_ordinary_dependency_observer742.py")
TEST = Path("/root/nativecmpkit-source-proposals-20261105/windows-observer-owned-eof-after770-r1/candidate/scripts/ci/test_windows_observer_owned_eof_after770.py")
OLD_TRANSPORT_TEST = Path("/root/nativecmpkit-source-proposals-20261105/windows-observer-owned-eof-after770-r1/candidate/scripts/ci/test_windows_ordinary_dependency_observer742.py")
ROUTE_TEST = Path("/root/nativecmpkit-source-proposals-20261105/windows-observer-owned-eof-after770-r1/candidate/scripts/ci/test_windows_observer_one_request_diagnostic770.py")
HELPER = Path("/root/nativecmpkit-source-proposals-20261105/windows-observer-owned-eof-after770-r1/candidate/scripts/ci/windows_observer_one_request_diagnostic770.py")
REFERENCE_ROOT = "/root/nativecmpkit-source-proposals-20261105/windows-observer-owned-eof-after770-r1/candidate"
SELECTORS = ["test_windows_observer_owned_eof_after770.WindowsObserverOwnedEOFAfter770Tests.test_NEW_real_owned_ContentLength_full_EOF_and_truncation_are_not_lifetime_shortcuts","test_windows_observer_owned_eof_after770.WindowsObserverOwnedEOFAfter770Tests.test_NEW_real_owned_chunked_full_and_missing_zero_terminator_remain_distinct","test_windows_observer_owned_eof_after770.WindowsObserverOwnedEOFAfter770Tests.test_NEW_real_closed_EOF_still_refuses_expired_deadline_and_exact_hard_cap","test_windows_observer_owned_eof_after770.WindowsObserverOwnedEOFAfter770Tests.test_NEW_open_body_timeout_OSError_and_cleanup_errors_are_never_swallowed","test_windows_ordinary_dependency_observer742.WindowsObservation742Tests.test_mocked_transport_refuses_redirects_credentials_compression_partial_and_caps","test_windows_observer_one_request_diagnostic770.WindowsOneRequestDiagnostic770Tests.test_CHANGED_route_inverse_fixed_row_and_NEW_worker_lifecycle_source"]

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
    raise RuntimeError('NEW OWNED-EOF6 denies all real network, subprocess and tool execution')

def main():
    if len(sys.argv) != 1 or os.environ.get('NATIVECMPKIT_DIAGNOSTIC_TEST_SOURCE_ROOT') != REFERENCE_ROOT:
        raise ValueError('Only the held external new observer source-test environment')
    before_threads = {thread.ident for thread in threading.enumerate()}
    # Preserve real stdlib AF_UNIX socketpair; deny every external/socket-path
    # operation. These are execution denials, not successful transport fakes.
    actual_socket = socket.socket
    actual_socketpair = socket.socketpair
    pair_socket_wraps = [0]
    current_pair_wraps = [0]
    pair_creation = [False]
    pairs_created = [0]
    owned_pairs = []
    def local_pair_socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, fileno=None):
        if (not pair_creation[0] or family != socket.AF_UNIX or type != socket.SOCK_STREAM or
            proto != 0 or type_of(fileno) is not int or fileno < 0 or current_pair_wraps[0] >= 2):
            raise RuntimeError('Only two real fd wraps inside each owning AF_UNIX pair creation')
        current_pair_wraps[0] += 1
        pair_socket_wraps[0] += 1
        return actual_socket(family, type, proto, fileno=fileno)
    def one_owned_socketpair(family=socket.AF_UNIX, type=socket.SOCK_STREAM, proto=0):
        if (family != socket.AF_UNIX or type != socket.SOCK_STREAM or proto != 0 or
            pairs_created[0] >= 6 or any(item.fileno() != -1 for item in owned_pairs)):
            raise RuntimeError('Only six serial real owned AF_UNIX pairs; earlier descriptors must be closed')
        pairs_created[0] += 1
        current_pair_wraps[0] = 0
        pair_creation[0] = True
        try:
            pair = actual_socketpair(family, type, proto)
            if current_pair_wraps[0] != 2 or len(pair) != 2 or any(item.family != socket.AF_UNIX for item in pair):
                raise RuntimeError('Exact real AF_UNIX pair and two descriptor-wrap shape')
            owned_pairs.extend(pair)
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
    sys.modules['windows_ordinary_dependency_observer742'] = helper.base
    controls = load_exact('test_windows_observer_owned_eof_after770', TEST)
    old_transport = load_exact('test_windows_ordinary_dependency_observer742', OLD_TRANSPORT_TEST)
    route = load_exact('test_windows_observer_one_request_diagnostic770', ROUTE_TEST)
    klass = controls.WindowsObserverOwnedEOFAfter770Tests
    new_methods = [selector.rsplit('.', 1)[1] for selector in SELECTORS[:4]]
    if sorted(name for name in dir(klass) if name.startswith('test_')) != sorted(new_methods):
        raise ValueError('Only the four actually authored new owning EOF methods')
    modules = {
        'test_windows_observer_owned_eof_after770': controls,
        'test_windows_ordinary_dependency_observer742': old_transport,
        'test_windows_observer_one_request_diagnostic770': route,
    }
    suite = unittest.TestSuite()
    for selector in SELECTORS:
        module_name, class_name, method = selector.split('.')
        suite.addTest(getattr(modules[module_name], class_name)(method))
    if suite.countTestCases() != 6 or len(set(SELECTORS)) != 6:
        raise ValueError('Exact NEW4 plus changed2 owning EOF suite required')
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=RecordedResult).run(suite)
    actual_external = sorted({str(Path(module.__file__).resolve()) for name, module in list(sys.modules.items())
        if name != '__main__' and isinstance(getattr(module, '__file__', None), str) and '/nativecmpkit-' in module.__file__})
    expected_external = sorted([str(OBSERVER), str(HELPER), str(TEST), str(OLD_TRANSPORT_TEST), str(ROUTE_TEST)])
    forbidden = sorted(set(sys.modules) & {'javafx_ordinary_maven_consumer', 'javafx_ordinary_dependency_expectations',
        'test_javafx_ordinary_dependency_expectations742', 'library_tests', 'webview_consumer', 'daemon_jvm',
        'runtime_context', 'failure_diagnostics', 'build_runtime_candidate', 'probe_runner'})
    remaining_threads = [{'name': thread.name, 'daemon': thread.daemon} for thread in threading.enumerate()
                         if thread.ident not in before_threads]
    statuses = ('PASS', 'FAIL', 'ERROR', 'SKIP', 'UNKNOWN')
    counts = {status: sum(row['status'] == status for row in result.methods.values()) for status in statuses}
    successful = (result.wasSuccessful() and result.testsRun == 6 and set(result.methods) == set(SELECTORS) and
        counts['PASS'] == 6 and not any(counts[status] for status in statuses if status != 'PASS') and
        not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses and
        actual_external == expected_external and not forbidden and not remaining_threads and
        pairs_created[0] == 6 and pair_socket_wraps[0] == 12 and not pair_creation[0] and
        len(owned_pairs) == 12 and all(item.fileno() == -1 for item in owned_pairs))
    data = {'schema': 'nativecmpkit-Windows-owned-EOF6-child-result-after770-r1', 'tests_run': result.testsRun,
        'suite_seconds': time.monotonic() - started, 'methods': result.methods, 'method_counts': counts,
        'subtests': result.subtests, 'subtest_count': len(result.subtests), 'failure_records': len(result.failures),
        'error_records': len(result.errors), 'skipped': len(result.skipped), 'expected_failures': len(result.expectedFailures),
        'unexpected_successes': len(result.unexpectedSuccesses), 'unittest_successful': result.wasSuccessful(),
        'successful': successful, 'forbidden_modules': forbidden, 'actual_external_modules': actual_external,
        'expected_external_modules': expected_external, 'remaining_threads': remaining_threads, 'owned_socketpairs_created': pairs_created[0],
        'real_AF_UNIX_pair_descriptor_wraps': pair_socket_wraps[0], 'pair_creation_in_progress': pair_creation[0],
        'owned_pairs_all_closed': len(owned_pairs) == 12 and all(item.fileno() == -1 for item in owned_pairs),
        'only_six_serial_owned_pairs_admitted': True, 'unique_NEW_methods': 4, 'changed_methods': 2,
        'remote_network_subprocess_and_tools_denied': True, 'source_only': True, 'owned_AF_UNIX_socketpair_boundary_only': True, 'real_trust_native_Gradle_release_clearance': False}
    print(json.dumps(data, sort_keys=True), flush=True)
    return 0 if successful else 1

if __name__ == '__main__':
    raise SystemExit(main())
