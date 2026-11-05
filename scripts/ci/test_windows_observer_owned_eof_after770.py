# SPDX-License-Identifier: Apache-2.0
"""NEW4 owning EOF/lifetime regressions after diagnostic770; not remote/native.

Real HTTPResponse framing/read1/fp ownership runs over exactly six bounded owned
local AF_UNIX socketpairs, with no remote connect or global transport fake.
The last test is a negative owning-operation fixture before any body read.
No original766 body/log/result replay or retrospective cause qualification.
"""
from __future__ import annotations

import hashlib
import http.client
import os
from pathlib import Path
import socket
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import windows_observer_one_request_diagnostic770 as diagnostic

SOURCE_ROOT = Path(os.environ.get('NATIVECMPKIT_DIAGNOSTIC_TEST_SOURCE_ROOT',
                                  str(Path(__file__).resolve().parents[2])))
POM = b'<project><modelVersion>4.0.0</modelVersion></project>'


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


class OwnedResponse:
    """Delegates to the actual local stdlib parser; no successful response stub."""
    def __init__(self, actual, clock, advance):
        self.actual, self.clock, self.advance = actual, clock, advance
        self.reads = 0
        self.lifetime_views = []

    @property
    def status(self):
        return self.actual.status

    def getheaders(self):
        return self.actual.getheaders()

    def isclosed(self):
        closed = self.actual.isclosed()
        self.lifetime_views.append(closed)
        return closed

    def read1(self, count):
        self.reads += 1
        chunk = self.actual.read1(count)
        if chunk and self.advance:
            self.clock.value += self.advance
        return chunk

    def close(self):
        return self.actual.close()


class OwnedTransport:
    def __init__(self, actual):
        self.actual = actual
        self.timeouts = []

    def settimeout(self, seconds):
        self.timeouts.append((seconds, self.actual.fileno()))
        return self.actual.settimeout(seconds)


class OwnedLocalConnection:
    """Preconnected local pair only; original GET/response ownership is exercised."""
    def __init__(self, owner, clock, advance):
        self.owner, self.clock, self.advance = owner, clock, advance
        self.sock = OwnedTransport(owner)
        self.response = None
        self.requests = []
        self.closed = False

    def connect(self):
        return None

    def request(self, method, path, body, headers):
        self.requests.append((method, path, body, dict(headers)))

    def getresponse(self):
        actual = http.client.HTTPResponse(self.owner)
        self.response = OwnedResponse(actual, self.clock, self.advance)
        actual.begin()
        # Real HTTPConnection.getresponse Connection-close handoff: close its
        # socket owner while the response fp retains the actual borrowed fd.
        self.owner.close()
        return self.response

    def close(self):
        self.closed = True
        self.owner.close()


class WindowsObserverOwnedEOFAfter770Tests(unittest.TestCase):
    def setUp(self):
        self.plan, _identity = diagnostic.load_plan(SOURCE_ROOT)
        self.assertEqual(len(self.plan['requests']), 120)
        self.request = diagnostic.select_fixed_request(self.plan)

    def local_fetch(self, wire, *, advance=0.0, exact_global_cap=False):
        self.assertIs(type(wire), bytes)
        self.assertLessEqual(len(wire), 512)
        owner, peer = socket.socketpair()
        clock = Clock()
        budget = diagnostic.base.NetworkBudget(45, clock)
        if exact_global_cap:
            budget.body_bytes = diagnostic.base.MAX_TOTAL_BODY - len(POM)
        recorder = diagnostic.OperationRecorder()
        connections = []
        def factory(hostname, **kwargs):
            self.assertEqual(hostname, 'dl.google.com')
            self.assertEqual(kwargs['port'], 443)
            actual = OwnedLocalConnection(owner, clock, advance)
            connections.append(actual)
            return diagnostic.DelegatingConnection(actual, recorder)
        try:
            peer.sendall(wire)
            peer.shutdown(socket.SHUT_WR)
            observed, raw = diagnostic.base.observe_one(
                self.request, self.plan, budget, connection_factory=factory)
            row = diagnostic.sanitize_observation(observed, recorder)
            self.assertEqual(len(connections), 1)
            connection = connections[0]
            self.assertEqual(budget.requests, 1)
            self.assertEqual(connection.requests[0][0], 'GET')
            self.assertIsNone(connection.requests[0][2])
            self.assertEqual(connection.requests[0][3]['Accept-Encoding'], 'identity')
            self.assertTrue(connection.closed)
            self.assertTrue(connection.response.actual.isclosed())
            self.assertEqual(owner.fileno(), -1)
            self.assertFalse(row['raw_body_exported'])
            self.assertFalse(row['original766_cause_qualified'])
            self.assertTrue(diagnostic.NO_ADMISSION['observations_are_untrusted'])
            self.assertFalse(diagnostic.NO_ADMISSION['native_or_ordinary_consumer_qualified'])
            return observed, raw, row, connection, budget
        finally:
            for connection in connections:
                if connection.response is not None:
                    connection.response.close()
            owner.close()
            peer.close()
            self.assertEqual(owner.fileno(), -1)
            self.assertEqual(peer.fileno(), -1)

    def test_NEW_real_owned_ContentLength_full_EOF_and_truncation_are_not_lifetime_shortcuts(self):
        for truncated in (False, True):
            with self.subTest(truncated=truncated):
                declared = len(POM) + (7 if truncated else 0)
                wire = ('HTTP/1.1 200 OK\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % declared).encode() + POM
                observed, raw, row, connection, budget = self.local_fetch(wire)
                self.assertEqual(raw, POM)
                self.assertEqual(row['body_sha256'], hashlib.sha256(POM).hexdigest())
                self.assertEqual(budget.body_bytes, len(POM))
                self.assertEqual(row['http_status'], 200)
                self.assertEqual(row['primary_errors'], [])
                self.assertEqual(row['cleanup_errors'], [])
                self.assertFalse(row['operation_error_overflow'])
                self.assertEqual(connection.response.reads, 2)
                self.assertTrue(all(fd >= 0 for _seconds, fd in connection.sock.timeouts))
                if truncated:
                    self.assertEqual(row['status'], 'refused')
                    self.assertFalse(row['complete_response'])
                    self.assertFalse(row['public_text_qualified'])
                    self.assertTrue(row['unattributed_refusal'])
                    self.assertEqual(observed['exception_type'], 'ObservationRefusal')
                    self.assertEqual(connection.response.actual.length, 7)
                else:
                    self.assertEqual(row['status'], 'observed')
                    self.assertTrue(row['complete_response'])
                    self.assertTrue(row['public_text_qualified'])
                    self.assertFalse(row['unattributed_refusal'])
                    self.assertIsNone(observed['exception_type'])
                    self.assertEqual(connection.response.actual.length, 0)
                    self.assertEqual(connection.response.lifetime_views, [False, True])
                    # Two setup phases plus only one live body timeout; real
                    # read1(empty EOF) still follows the closed lifetime view.
                    self.assertEqual(len(connection.sock.timeouts), 3)

    def test_NEW_real_owned_chunked_full_and_missing_zero_terminator_remain_distinct(self):
        for truncated in (False, True):
            with self.subTest(truncated=truncated):
                wire = b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n'
                wire += ('%x\r\n' % len(POM)).encode() + POM + b'\r\n'
                if not truncated:
                    wire += b'0\r\n\r\n'
                observed, raw, row, connection, budget = self.local_fetch(wire)
                self.assertEqual(raw, POM)
                self.assertTrue(connection.response.actual.chunked)
                self.assertEqual(budget.body_bytes, len(POM))
                self.assertEqual(connection.response.reads, 2)
                self.assertFalse(row['operation_error_overflow'])
                self.assertEqual(row['cleanup_errors'], [])
                if truncated:
                    self.assertEqual(row['status'], 'refused')
                    self.assertFalse(row['complete_response'])
                    self.assertFalse(row['public_text_qualified'])
                    self.assertEqual(observed['exception_type'], 'IncompleteRead')
                    self.assertEqual(row['primary_errors'], [
                        {'operation': 'response-read1', 'errno': None, 'winerror': None}])
                else:
                    self.assertEqual(row['status'], 'observed')
                    self.assertTrue(row['complete_response'])
                    self.assertTrue(row['public_text_qualified'])
                    self.assertIsNone(observed['exception_type'])
                    self.assertEqual(row['primary_errors'], [])

    def test_NEW_real_closed_EOF_still_refuses_expired_deadline_and_exact_hard_cap(self):
        wire = ('HTTP/1.1 200 OK\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(POM)).encode() + POM
        for mode in ('deadline', 'exact-global-cap'):
            with self.subTest(mode=mode):
                observed, raw, row, connection, budget = self.local_fetch(
                    wire, advance=21.0 if mode == 'deadline' else 0.0,
                    exact_global_cap=mode == 'exact-global-cap')
                self.assertEqual(raw, POM)
                self.assertEqual(connection.response.actual.length, 0)
                self.assertEqual(connection.response.reads, 1)
                self.assertEqual(row['status'], 'refused')
                self.assertFalse(row['complete_response'])
                self.assertFalse(row['public_text_qualified'])
                self.assertEqual(row['primary_errors'], [])
                self.assertEqual(row['cleanup_errors'], [])
                self.assertTrue(row['unattributed_refusal'])
                self.assertTrue(all(fd >= 0 for _seconds, fd in connection.sock.timeouts))
                if mode == 'deadline':
                    self.assertEqual(observed['exception_type'], 'TimeoutError')
                    self.assertGreaterEqual(observed['elapsed_seconds'], 20.0)
                else:
                    self.assertEqual(observed['exception_type'], 'ObservationRefusal')
                    self.assertEqual(budget.body_bytes, diagnostic.base.MAX_TOTAL_BODY)

    def test_NEW_open_body_timeout_OSError_and_cleanup_errors_are_never_swallowed(self):
        for close_error in (False, True):
            with self.subTest(close_error=close_error):
                primary = OSError(10038, 'PRIVATE injected negative primary; not actual770 evidence')
                primary.winerror = 10038
                cleanup = OSError(5, 'PRIVATE injected negative cleanup')
                recorder = diagnostic.OperationRecorder()
                class NegativeTransport:
                    def __init__(self):
                        self.calls, self.raised = 0, None
                    def settimeout(self, seconds):
                        self.calls += 1
                        if self.calls == 3:
                            self.raised = primary
                            raise primary
                class NegativeResponse:
                    status = 200
                    def isclosed(self):
                        return False
                    def getheaders(self):
                        return [('Content-Length', str(len(POM)))]
                    def read1(self, count):
                        raise AssertionError('No fake successful response/body before negative timeout')
                    def close(self):
                        if close_error:
                            raise cleanup
                class NegativeConnection:
                    def __init__(self):
                        self.sock = NegativeTransport()
                        self.closed = False
                    def connect(self):
                        pass
                    def request(self, *args, **kwargs):
                        pass
                    def getresponse(self):
                        return NegativeResponse()
                    def close(self):
                        self.closed = True
                actual = NegativeConnection()
                def factory(hostname, **kwargs):
                    return diagnostic.DelegatingConnection(actual, recorder)
                budget = diagnostic.base.NetworkBudget(45, Clock())
                observed, raw = diagnostic.base.observe_one(
                    self.request, self.plan, budget, connection_factory=factory)
                row = diagnostic.sanitize_observation(observed, recorder)
                self.assertIs(actual.sock.raised, primary)
                self.assertEqual(actual.sock.calls, 3)
                self.assertTrue(actual.closed)
                self.assertEqual(budget.requests, 1)
                self.assertEqual(raw, b'')
                self.assertEqual(observed['exception_type'], 'OSError')
                self.assertEqual(row['status'], 'refused')
                self.assertFalse(row['complete_response'])
                self.assertFalse(row['public_text_qualified'])
                self.assertFalse(row['original766_cause_qualified'])
                self.assertEqual(row['primary_errors'], [
                    {'operation': 'transport-settimeout-body', 'errno': 10038, 'winerror': 10038}])
                self.assertEqual(row['cleanup_errors'], [
                    {'operation': 'response-close', 'errno': 5, 'winerror': None}] if close_error else [])
                self.assertNotIn('PRIVATE', str(row))
                self.assertNotIn('exception_type', row)


if __name__ == '__main__':
    unittest.main()
