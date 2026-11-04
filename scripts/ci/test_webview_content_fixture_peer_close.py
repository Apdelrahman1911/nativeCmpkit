# SPDX-License-Identifier: Apache-2.0
"""Exact peer-close test assertion controls; no browser/native operations."""
import errno
import unittest

from test_webview_content_policy_fixture import assert_owned_peer_closed


class Peer:
    def __init__(self, result):
        self.result, self.calls = result, []

    def recv(self, size):
        self.calls.append(size)
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


class WebViewContentFixturePeerCloseTests(unittest.TestCase):
    def test_observed_eof_is_exactly_one_read(self):
        peer = Peer(b"")
        assert_owned_peer_closed(self, peer)
        self.assertEqual([1], peer.calls)

    def test_only_exact_platform_connection_reset_is_an_admitted_close_shape(self):
        peer = Peer(ConnectionResetError(errno.ECONNRESET, "Synthetic reset"))
        assert_owned_peer_closed(self, peer)
        self.assertEqual([1], peer.calls)

    def test_nonempty_payload_and_wrong_or_missing_reset_errno_cannot_prove_close(self):
        for result in (b"x", ConnectionResetError(errno.EACCES, "Synthetic unrelated reset"), ConnectionResetError()):
            peer = Peer(result)
            with self.subTest(kind=type(result).__name__), self.assertRaises(AssertionError):
                assert_owned_peer_closed(self, peer)
            self.assertEqual([1], peer.calls)

    def test_timeout_unrelated_oserror_and_broad_exceptions_are_not_suppressed(self):
        for result in (TimeoutError("Synthetic timeout"), OSError(errno.EACCES, "Synthetic access refusal"),
                       RuntimeError("Synthetic unrelated failure")):
            peer = Peer(result)
            with self.subTest(kind=type(result).__name__), self.assertRaises(type(result)):
                assert_owned_peer_closed(self, peer)
            self.assertEqual([1], peer.calls)


if __name__ == "__main__":
    unittest.main()
