#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""New narrow source/interpreted models; never Java/Kotlin/TLS/native acceptance.

The preserved original method supplies the independent native witness. This
model exercises only the newly added pending Finished-write boundary and its
fatal/refusal states, not prior JavaFX/routing/pixel suites.
"""
from __future__ import annotations
import ast
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
TEST = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewTlsRenderingAcceptanceTest.kt"
HELPER = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt"
PLAN = "scripts/ci/desktop_security_plan.py"
FILE_HASHES = {'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewTlsRenderingAcceptanceTest.kt': {'after_bytes': 14057,
                                                                                                                  'after_sha256': '00698c638a729549c890240b000e64cbd88be9f6ac32d4ca067b304b1443187c',
                                                                                                                  'before_bytes': 13932,
                                                                                                                  'before_sha256': 'd6351562894951442fec8258dc95452251530e6df10d04c3e106f535a1391696'},
 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt': {'after_bytes': 25897,
                                                                                                'after_sha256': 'a7c8b3fe15c94ef5f30ccb648cdbe5a52770aad1b0bf5eeed6415a802a05c703',
                                                                                                'before_bytes': 20741,
                                                                                                'before_sha256': '1636c150d21b2a5d15d6659c04f840e4bc2a2852287e835c912aaf43271de9ea'},
 'scripts/ci/desktop_security_plan.py': {'after_bytes': 17195,
                                         'after_sha256': 'ec32060fa123a27d9e643a41fd486d238744edae7a82e18666576f226d5df777',
                                         'before_bytes': 17195,
                                         'before_sha256': '22dc3b4438873c25363dee6adf81080487211c9ef405ffd6399c87d072f7bf1d'}}
LITERALS = ({'new': 'import java.net.InetAddress\nimport java.net.SocketException\n',
  'old': 'import java.net.InetAddress\n',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '    fun assertTrustLease() = lease.assertInstalled()\n'
         '    // Called only after every original native SSL/error and zero-HTTP assertion.\n'
         '    // This confirms the endpoint-level witness, never invents a native outcome.\n'
         '    fun confirmNativeCertificateRejection() {\n'
         '        assertTrustLease()\n'
         '        trusted.assertHealthy()\n'
         '        untrusted.confirmNativeCertificateRejection()\n'
         '    }\n',
  'old': '    fun assertTrustLease() = lease.assertInstalled()\n',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '        private val connections = AtomicInteger()\n'
         '        private enum class FailurePhase { Accept, Handshake, RequestHeaders, ResponseWrite, '
         'SocketClose }\n'
         '        private data class RecordedFailure(val phase: FailurePhase, val error: Throwable)\n'
         '        private val failure = AtomicReference<RecordedFailure>()\n'
         '        private val rejectionLock = Any()\n'
         '        private val pendingFinishedWrites = mutableListOf<Throwable>()\n'
         '        private var nativeRejectionConfirmed = false // Guarded by rejectionLock; no automatic '
         'server-side confirmation.\n'
         '        private val acceptor =',
  'old': '        private val connections = AtomicInteger()\n'
         '        private val failure = AtomicReference<Throwable>()\n'
         '        private val acceptor =',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '        private fun endpointFailure(error: Throwable, phase: String) = AssertionError(\n'
         '            "Owned TLS fixture failed: endpoint=${if (trusted) "trusted" else "untrusted"} '
         'phase=$phase", error)\n'
         '        fun assertHealthy() {\n'
         '            failure.get()?.let { throw endpointFailure(it.error, it.phase.name) }\n'
         '            synchronized(rejectionLock) {\n'
         '                if (nativeRejectionConfirmed) assertRejectedEndpointStillZero()\n'
         '                if (closing.get() && pendingFinishedWrites.isNotEmpty() && '
         '!nativeRejectionConfirmed) {\n'
         '                    throw endpointFailure(pendingFinishedWrites.first(), '
         '"UnconfirmedFinishedWrite")\n'
         '                }\n'
         '            }\n'
         '        }\n'
         '        private fun assertRejectedEndpointStillZero() {\n'
         '            check(!trusted && handshakeSuccesses.get() == 0 &&\n'
         '                requests.values.all { it.get() == 0 } && responses.values.all { it.get() == 0 }) '
         '{\n'
         '                "Owned TLS fixture failed: endpoint=untrusted phase=RejectedEndpointTlsOrHttp"\n'
         '            }\n'
         '        }\n'
         '        fun confirmNativeCertificateRejection() {\n'
         '            assertHealthy()\n'
         '            synchronized(rejectionLock) {\n'
         '                check(!trusted && !closing.get() && !nativeRejectionConfirmed) {\n'
         '                    "Owned TLS fixture failed: endpoint=untrusted '
         'phase=InvalidRejectionConfirmation"\n'
         '                }\n'
         '                check(handshakeAttempts.get() >= 1) { "Native rejection needs an owned TLS '
         'attempt" }\n'
         '                assertRejectedEndpointStillZero()\n'
         '                nativeRejectionConfirmed = true\n'
         '            }\n'
         '            assertHealthy()\n'
         '        }\n'
         '        private fun record(error: Throwable, phase: FailurePhase) {\n'
         '            if (!closing.get()) failure.compareAndSet(null, RecordedFailure(phase, error))\n'
         '        }\n'
         '        private fun observedFinishedWriteAbort(error: Throwable, phase: FailurePhase, handshaken: '
         'Boolean): Boolean {\n'
         '            // Narrowly the original Linux/JDK17 TLS1.3 Finished-write Broken-pipe shape.\n'
         '            // No other SocketException, trusted endpoint, post-handshake phase or shutdown is '
         'quarantined.\n'
         '            if (trusted || handshaken || phase != FailurePhase.Handshake || closing.get() ||\n'
         '                Runtime.version().feature() != 17 || error.javaClass != '
         'SocketException::class.java ||\n'
         '                error.message != "Broken pipe") return false\n'
         '            val frames = error.stackTrace.map { it.className to it.methodName }\n'
         '            val prefix = listOf(\n'
         '                "sun.nio.ch.NioSocketImpl" to "implWrite",\n'
         '                "sun.nio.ch.NioSocketImpl" to "write",\n'
         '                "sun.nio.ch.NioSocketImpl\\$2" to "write",\n'
         '                "java.net.Socket\\$SocketOutputStream" to "write",\n'
         '                "sun.security.ssl.SSLSocketOutputRecord" to "flush",\n'
         '                "sun.security.ssl.HandshakeOutStream" to "flush",\n'
         '                "sun.security.ssl.Finished\\$T13FinishedProducer" to "onProduceFinished",\n'
         '                "sun.security.ssl.Finished\\$T13FinishedProducer" to "produce",\n'
         '            )\n'
         '            if (frames.take(prefix.size) != prefix) return false\n'
         '            val caller = listOf(\n'
         '                "sun.security.ssl.SSLSocketImpl" to "startHandshake",\n'
         '                "sun.security.ssl.SSLSocketImpl" to "startHandshake",\n'
         '                "com.mohamedrejeb.calf.ui.web.OwnedDesktopTlsFixture\\$Endpoint" to "respond",\n'
         '            )\n'
         '            return frames.windowed(caller.size).any { it == caller }\n'
         '        }\n'
         '        private fun quarantineFinishedWrite(error: Throwable) {\n'
         '            synchronized(rejectionLock) {\n'
         '                if (pendingFinishedWrites.size >= 16) {\n'
         '                    failure.compareAndSet(null, RecordedFailure(FailurePhase.Handshake, error))\n'
         '                } else {\n'
         '                    // Keep every bounded observation; neither adding it nor a prior observation '
         'is the native witness.\n'
         '                    pendingFinishedWrites.add(error)\n'
         '                }\n'
         '            }\n'
         '        }\n'
         '        private fun closeOwned(socket: SSLSocket) {\n'
         '            try { socket.close(); check(socket.isClosed); sockets.remove(socket) }\n'
         '            catch (error: Throwable) {\n'
         '                // A close/readback error is fatal even during teardown or after a confirmed '
         'native rejection.\n'
         '                failure.compareAndSet(null, RecordedFailure(FailurePhase.SocketClose, error)); '
         'throw error\n'
         '            }\n'
         '        }\n',
  'old': '        fun assertHealthy() { failure.get()?.let { throw AssertionError("Owned TLS fixture '
         'failed", it) } }\n'
         '        private fun record(error: Throwable) { if (!closing.get()) failure.compareAndSet(null, '
         'error) }\n'
         '        private fun closeOwned(socket: SSLSocket) {\n'
         '            try { socket.close(); check(socket.isClosed); sockets.remove(socket) }\n'
         '            catch (error: Throwable) { failure.compareAndSet(null, error); throw error }\n'
         '        }\n',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '                } catch (error: Throwable) {\n'
         '                    record(error, FailurePhase.Accept)\n'
         '                    socket?.let { runCatching { closeOwned(it) } }\n',
  'old': '                } catch (error: Throwable) {\n'
         '                    record(error)\n'
         '                    socket?.let { runCatching { closeOwned(it) } }\n',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '        private fun respond(socket: SSLSocket) {\n'
         '            var handshaken = false\n'
         '            var phase = FailurePhase.Handshake\n'
         '            try {\n',
  'old': '        private fun respond(socket: SSLSocket) {\n'
         '            var handshaken = false\n'
         '            try {\n',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '                handshaken = true\n'
         '                handshakeSuccesses.incrementAndGet()\n'
         '                phase = FailurePhase.RequestHeaders\n'
         '                val bytes =',
  'old': '                handshaken = true\n'
         '                handshakeSuccesses.incrementAndGet()\n'
         '                val bytes =',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '                phase = FailurePhase.ResponseWrite\n'
         '                socket.outputStream.apply { write(headers.toByteArray(StandardCharsets.US_ASCII)); '
         'write(data); flush() }\n',
  'old': '                socket.outputStream.apply { write(headers.toByteArray(StandardCharsets.US_ASCII)); '
         'write(data); flush() }\n',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '                // Keep the original negative pre-handshake SSLException/EOF boundary.\n'
         '                // The one observed Finished-write abort remains pending until ALL original\n'
         '                // native SSL/error and zero-HTTP assertions confirm this same owned endpoint.\n'
         '                // Unknown shapes retain the original fatal branch; no socket-wide suppression.\n'
         '                if (observedFinishedWriteAbort(error, phase, handshaken)) {\n'
         '                    quarantineFinishedWrite(error)\n'
         '                } else if (trusted || handshaken || (error !is SSLException && error !is '
         'EOFException)) {\n'
         '                    record(error, phase)\n'
         '                }\n',
  'old': '                // The native Worker must independently report SSL handshake failed.\n'
         '                // A negative handshake can end in a fatal alert or EOF; neither server\n'
         '                // observation alone is labelled certificate acceptance/rejection.\n'
         '                if (trusted || handshaken || (error !is SSLException && error !is EOFException)) '
         'record(error)\n',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedDesktopTlsFixture.kt'},
 {'new': '                assertEquals(0, tls.httpRequests(DesktopTlsStage.Untrusted), "Certificate '
         'rejection precedes the HTTP request")\n'
         '                tls.confirmNativeCertificateRejection() // Only after the unchanged native witness '
         'and zero-HTTP assertions.\n'
         '\n'
         '                load(DesktopTlsStage.Recovery)\n',
  'old': '                assertEquals(0, tls.httpRequests(DesktopTlsStage.Untrusted), "Certificate '
         'rejection precedes the HTTP request")\n'
         '\n'
         '                load(DesktopTlsStage.Recovery)\n',
  'path': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewTlsRenderingAcceptanceTest.kt'},
 {'new': "'00698c638a729549c890240b000e64cbd88be9f6ac32d4ca067b304b1443187c'",
  'old': "'d6351562894951442fec8258dc95452251530e6df10d04c3e106f535a1391696'",
  'path': 'scripts/ci/desktop_security_plan.py'},
 {'new': "'a7c8b3fe15c94ef5f30ccb648cdbe5a52770aad1b0bf5eeed6415a802a05c703'",
  'old': "'1636c150d21b2a5d15d6659c04f840e4bc2a2852287e835c912aaf43271de9ea'",
  'path': 'scripts/ci/desktop_security_plan.py'})


def source_contract(sources: dict[str, str] | None = None) -> dict[str, str]:
    if sources is None:
        sources = {path: (ROOT / path).read_text(encoding="utf-8") for path in FILE_HASHES}
    originals = {}
    for path, hashes in FILE_HASHES.items():
        value = sources[path]
        if hashlib.sha256(value.encode()).hexdigest() != hashes["after_sha256"]:
            raise ValueError("Unreviewed owning recovery source")
        for literal in reversed([literal for literal in LITERALS if literal["path"] == path]):
            if value.count(literal["new"]) != 1:
                raise ValueError("Nonunique or missing owning recovery literal")
            value = value.replace(literal["new"], literal["old"], 1)
        if hashlib.sha256(value.encode()).hexdigest() != hashes["before_sha256"]:
            raise ValueError("Original native/helper/parser payload changed")
        originals[path] = value
    return originals


def source_signature(helper: str) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    value = helper.split("private fun observedFinishedWriteAbort(", 1)[1].split(
        "private fun quarantineFinishedWrite(", 1)[0]
    def pairs(label: str) -> tuple[tuple[str, str], ...]:
        match = re.search(r"val " + label + r" = listOf\(\n(.*?)\n            \)", value, re.S)
        if match is None:
            raise ValueError("Missing exact observed frame signature")
        return tuple((name.replace(r"\$", "$"), method) for name, method in
                     re.findall(r'"([^"\n]+)" to "([^"\n]+)"', match.group(1)))
    return pairs("prefix"), pairs("caller")


OBSERVED_PREFIX = (
    ("sun.nio.ch.NioSocketImpl", "implWrite"),
    ("sun.nio.ch.NioSocketImpl", "write"),
    ("sun.nio.ch.NioSocketImpl$2", "write"),
    ("java.net.Socket$SocketOutputStream", "write"),
    ("sun.security.ssl.SSLSocketOutputRecord", "flush"),
    ("sun.security.ssl.HandshakeOutStream", "flush"),
    ("sun.security.ssl.Finished$T13FinishedProducer", "onProduceFinished"),
    ("sun.security.ssl.Finished$T13FinishedProducer", "produce"),
)
OBSERVED_CALLER = (
    ("sun.security.ssl.SSLSocketImpl", "startHandshake"),
    ("sun.security.ssl.SSLSocketImpl", "startHandshake"),
    ("com.mohamedrejeb.calf.ui.web.OwnedDesktopTlsFixture$Endpoint", "respond"),
)
OBSERVED_FRAMES = OBSERVED_PREFIX + (("sun.security.ssl.SSLHandshake", "produce"),) + OBSERVED_CALLER


def observed(*, trusted=False, handshaken=False, phase="Handshake", closing=False,
             java_major=17, error_class="java.net.SocketException", message="Broken pipe",
             frames=OBSERVED_FRAMES, signature=(OBSERVED_PREFIX, OBSERVED_CALLER)) -> bool:
    """Interpreted mirror of the exact source-bound new predicate, not JVM code."""
    if (trusted or handshaken or phase != "Handshake" or closing or java_major != 17 or
            error_class != "java.net.SocketException" or message != "Broken pipe"):
        return False
    prefix, caller = signature
    return (tuple(frames[:len(prefix)]) == prefix and
            any(tuple(frames[i:i + len(caller)]) == caller
                for i in range(len(frames) - len(caller) + 1)))


class EndpointModel:
    """Finite pending/witness/cleanup interleaving model; no actual socket or worker."""
    def __init__(self, *, trusted=False):
        self.trusted = trusted
        self.closing = False
        self.pending = []
        self.confirmed = False
        self.attempts = 0
        self.successes = self.requests = self.responses = 0
        self.fatal = False

    def respond(self, **fault):
        self.attempts += 1
        if observed(trusted=self.trusted, closing=self.closing, **fault):
            if len(self.pending) >= 16:
                self.fatal = True
            else:
                self.pending.append(self.attempts)
        elif not self.closing:
            # Tests use only the new Broken-pipe shape or unexpected non-SSL/EOF faults.
            # Existing negative SSLException/EOF allowances are preserved by exact inverse.
            self.fatal = True

    def zero(self):
        if self.trusted or any((self.successes, self.requests, self.responses)):
            raise ValueError("Rejected endpoint crossed TLS/HTTP")

    def healthy(self):
        if self.fatal:
            raise ValueError("Unexpected or close error remains fatal")
        if self.confirmed:
            self.zero()
        if self.closing and self.pending and not self.confirmed:
            raise ValueError("Unconfirmed Finished write is not acceptance")

    def confirm(self, *, complete_original_native_witness):
        # Synthetic Boolean only represents the unchanged native assertion sequence;
        # the actual Kotlin helper call sits strictly after all original assertions.
        if not complete_original_native_witness:
            raise ValueError("No independent native witness")
        self.healthy()
        if self.trusted or self.closing or self.confirmed or self.attempts < 1:
            raise ValueError("Invalid witness order/identity")
        self.zero()
        self.confirmed = True
        self.healthy()

    def close(self, *, close_readback_error=False):
        self.closing = True
        if close_readback_error:
            self.fatal = True  # Never exempt a close/readback failure.
        self.healthy()  # Represents the final original check after all workers/sockets drain.


class DesktopTlsFinishedWriteRecoveryModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {path: (ROOT / path).read_text(encoding="utf-8") for path in FILE_HASHES}
        cls.originals = source_contract(cls.sources)
        cls.signature = source_signature(cls.sources[HELPER])

    def test_exact_inverse_retains_every_original_native_and_parser_byte(self):
        self.assertEqual(12, len(LITERALS))
        self.assertEqual(3, len(self.originals))
        test_literals = [item for item in LITERALS if item["path"] == TEST]
        self.assertEqual(1, len(test_literals))
        # The only native-body change is one explicit gate after the last original
        # zero-HTTP assertion; no original assert/load/paint/cleanup byte is replaced.
        self.assertEqual(1, self.sources[TEST].count("tls.confirmNativeCertificateRejection()"))
        self.assertIn('assertEquals(0, tls.httpRequests(DesktopTlsStage.Untrusted), "Certificate rejection precedes the HTTP request")\n'
                      '                tls.confirmNativeCertificateRejection()', self.sources[TEST])
        plan_literals = [item for item in LITERALS if item["path"] == PLAN]
        self.assertEqual(2, len(plan_literals))
        tree = ast.parse(self.sources[PLAN])
        hashes = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "SOURCE_SHA256" for target in node.targets))
        self.assertEqual(FILE_HASHES[TEST]["after_sha256"], hashes[TEST])
        self.assertEqual(FILE_HASHES[HELPER]["after_sha256"], hashes[HELPER])

    def test_observed_prefix_and_owning_caller_are_exact_and_boundary_refuses(self):
        self.assertEqual((OBSERVED_PREFIX, OBSERVED_CALLER), self.signature)
        self.assertTrue(observed(signature=self.signature))
        variants = ({"trusted": True}, {"handshaken": True}, {"phase": "Accept"},
                    {"phase": "RequestHeaders"}, {"phase": "ResponseWrite"}, {"phase": "SocketClose"},
                    {"closing": True}, {"java_major": 21}, {"error_class": "java.net.SocketTimeoutException"},
                    {"error_class": "subclass.SocketException"}, {"message": "Connection reset"}, {"message": None})
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertFalse(observed(signature=self.signature, **variant))

    def test_missing_reordered_or_unowned_finished_frames_refuse(self):
        for index in range(len(OBSERVED_FRAMES)):
            if OBSERVED_FRAMES[index] not in OBSERVED_PREFIX + OBSERVED_CALLER:
                continue
            with self.subTest(missing_index=index):
                self.assertFalse(observed(frames=OBSERVED_FRAMES[:index] + OBSERVED_FRAMES[index + 1:]))
        for frames in ((), OBSERVED_CALLER + OBSERVED_PREFIX, tuple(reversed(OBSERVED_FRAMES)),
                       (("foreign.Writer", "write"),) + OBSERVED_FRAMES,
                       OBSERVED_PREFIX + (("foreign.Endpoint", "respond"),)):
            with self.subTest(shape=frames[:1]):
                self.assertFalse(observed(frames=frames))

    def test_pending_observation_cannot_confirm_itself_or_escape_close(self):
        model = EndpointModel()
        model.respond()
        self.assertEqual([1], model.pending)
        model.healthy()  # Allows the real engine's independent failure to become observable.
        self.assertFalse(model.confirmed)
        with self.assertRaises(ValueError):
            model.confirm(complete_original_native_witness=False)
        self.assertFalse(model.confirmed)
        with self.assertRaises(ValueError):
            model.close()
        empty = EndpointModel()
        with self.assertRaises(ValueError):
            empty.confirm(complete_original_native_witness=True)

    def test_zero_tls_http_remains_mandatory_before_and_after_native_witness(self):
        for field in ("successes", "requests", "responses"):
            for after_confirmation in (False, True):
                with self.subTest(field=field, after=after_confirmation):
                    model = EndpointModel(); model.respond()
                    if after_confirmation:
                        model.confirm(complete_original_native_witness=True)
                    setattr(model, field, 1)
                    with self.assertRaises(ValueError):
                        if after_confirmation:
                            model.close()
                        else:
                            model.confirm(complete_original_native_witness=True)
        model = EndpointModel(); model.respond(); model.confirm(complete_original_native_witness=True)
        with self.assertRaises(ValueError):
            model.confirm(complete_original_native_witness=True)

    def test_trusted_unknown_post_handshake_and_close_faults_remain_fatal(self):
        trusted = EndpointModel(trusted=True); trusted.respond()
        with self.assertRaises(ValueError):
            trusted.healthy()
        for fault in ({"message": "Connection reset"}, {"handshaken": True},
                      {"phase": "RequestHeaders"}, {"phase": "ResponseWrite"}, {"phase": "Accept"}):
            for witnessed in (False, True):
                with self.subTest(fault=fault, witnessed=witnessed):
                    model = EndpointModel(); model.respond()
                    if witnessed:
                        model.confirm(complete_original_native_witness=True)
                    model.respond(**fault)
                    with self.assertRaises(ValueError):
                        model.close()
        model = EndpointModel(); model.respond(); model.confirm(complete_original_native_witness=True)
        with self.assertRaises(ValueError):
            model.close(close_readback_error=True)

    def test_bounded_late_candidates_keep_witness_and_counters_fail_closed(self):
        for candidates_before_witness in (1, 8, 16):
            with self.subTest(candidates_before_witness=candidates_before_witness):
                model = EndpointModel()
                for _ in range(candidates_before_witness):
                    model.respond()
                model.confirm(complete_original_native_witness=True)
                for _ in range(16 - candidates_before_witness):
                    model.respond()
                self.assertEqual(list(range(1, 17)), model.pending)
                model.close()
        overflow = EndpointModel()
        for _ in range(17):
            overflow.respond()
        self.assertEqual(16, len(overflow.pending))
        with self.assertRaises(ValueError):
            overflow.confirm(complete_original_native_witness=True)
        model = EndpointModel(); model.respond(); model.confirm(complete_original_native_witness=True)
        model.respond(); model.requests = 1
        with self.assertRaises(ValueError):
            model.close()

    def test_unsafe_new_source_mutations_are_not_hash_or_parser_waived(self):
        helper = self.sources[HELPER]
        mutations = ((HELPER, helper.replace('trusted || handshaken || phase != FailurePhase.Handshake',
                                             'false || handshaken || phase != FailurePhase.Handshake', 1)),
                     (HELPER, helper.replace('error.javaClass != SocketException::class.java', 'false', 1)),
                     (HELPER, helper.replace('error.message != "Broken pipe"', 'false', 1)),
                     (HELPER, helper.replace('pendingFinishedWrites.add(error)', 'nativeRejectionConfirmed = true', 1)),
                     (HELPER, helper.replace('pendingFinishedWrites.isNotEmpty() && !nativeRejectionConfirmed', 'false', 1)),
                     (HELPER, helper.replace('RecordedFailure(FailurePhase.SocketClose, error)', 'null', 1)),
                     (TEST, self.sources[TEST].replace('tls.confirmNativeCertificateRejection()', '// omitted witness', 1)),
                     (PLAN, self.sources[PLAN] + '\n# Unreviewed parser change\n'))
        for path, mutation in mutations:
            with self.subTest(path=path, mutation_index=mutations.index((path, mutation))):
                sources = dict(self.sources); sources[path] = mutation
                with self.assertRaises(ValueError):
                    source_contract(sources)


if __name__ == "__main__":
    unittest.main()
