# SPDX-License-Identifier: Apache-2.0
"""NEW source-only Windows Stop failure-frame obligations; no JVM/native execution."""

import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER_SOURCE = 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewStopFailureResources.kt'
HELPER_PREIMAGE_SHA256 = 'b698f11a05a2b8a566ccef71b57a6d3faf83443bb3e1788cabe8fca30e9396a7'
HELPER_POSTIMAGE_SHA256 = 'd643487bffff3ab744e7eb770faf60552e82e49d90982249dc26bcdccef088c5'
FIXTURE_SOURCE = 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewStopRedirectAcceptanceTest.kt'
FIXTURE_SHA256 = "8eb3cbe9e91974c423998eb3007ed64ed9d98863dcc27d0b72da901caad411a3"
HELPER_EDITS = [('import javafx.scene.web.WebEngine\n', 'import javafx.scene.web.WebEngine\nimport java.lang.management.ManagementFactory\n'), ('private val STOP_FAILURE_RESOURCE_ENTRIES = listOf(\n    "WebView" to "javafx/scene/web/WebView.class",\n    "WebEngine" to "javafx/scene/web/WebEngine.class",\n    "LoadWorker" to "javafx/scene/web/WebEngine\\$LoadWorker.class",\n    "WebPage" to "com/sun/webkit/WebPage.class",\n    "NetworkContext" to "com/sun/webkit/network/NetworkContext.class",\n    "URLLoader" to "com/sun/webkit/network/URLLoader.class",\n    "HTTP2Loader" to "com/sun/webkit/network/HTTP2Loader.class",\n    "HTTP2BodySubscriber" to "com/sun/webkit/network/HTTP2Loader\\$3.class",\n)\n', 'private val STOP_FAILURE_RESOURCE_ENTRIES = listOf(\n    "WebView" to "javafx/scene/web/WebView.class",\n    "WebEngine" to "javafx/scene/web/WebEngine.class",\n    "LoadWorker" to "javafx/scene/web/WebEngine\\$LoadWorker.class",\n    "WebPage" to "com/sun/webkit/WebPage.class",\n    "NetworkContext" to "com/sun/webkit/network/NetworkContext.class",\n    "URLLoader" to "com/sun/webkit/network/URLLoader.class",\n    "HTTP2Loader" to "com/sun/webkit/network/HTTP2Loader.class",\n    "HTTP2BodySubscriber" to "com/sun/webkit/network/HTTP2Loader\\$3.class",\n)\n\nprivate const val STOP_FAILURE_FRAME_THREAD_CAP = 256\nprivate const val STOP_FAILURE_FRAME_DEPTH_CAP = 32\nprivate const val STOP_FAILURE_FRAME_TOTAL_CAP = 8_192\nprivate const val STOP_FAILURE_FRAME_RECORD_CAP = 640\nprivate const val STOP_FAILURE_FRAME_SCOPE = "executing-method-names-only"\nprivate data class StopFailureFrameTarget(val label: String, val className: String, val methodName: String)\nprivate val STOP_FAILURE_FRAME_TARGETS = listOf(\n    StopFailureFrameTarget("urlRun", "com.sun.webkit.network.URLLoader", "run"),\n    StopFailureFrameTarget("urlResponse", "com.sun.webkit.network.URLLoader", "receiveResponse"),\n    StopFailureFrameTarget("urlClose", "com.sun.webkit.network.URLLoader", "close"),\n    StopFailureFrameTarget("urlCancel", "com.sun.webkit.network.URLLoader", "fwkCancel"),\n    StopFailureFrameTarget("http2Cancel", "com.sun.webkit.network.HTTP2Loader", "fwkCancel"),\n    StopFailureFrameTarget("http2Subscribe", "com.sun.webkit.network.HTTP2Loader\\$3", "onSubscribe"),\n    StopFailureFrameTarget("http2Next", "com.sun.webkit.network.HTTP2Loader\\$3", "onNext"),\n    StopFailureFrameTarget("http2Demand", "com.sun.webkit.network.HTTP2Loader\\$3", "requestIfNotCancelled"),\n    StopFailureFrameTarget("responseCode", "java.net.HttpURLConnection", "getResponseCode"),\n)\n'), (' * The cooperative 250ms read budget cannot preempt blocking file I/O or stderr output.\n', ' * The cooperative 250ms read budget cannot preempt blocking file I/O or stderr output.\n * Failure-frame queries share that same cooperative budget and likewise cannot preempt a\n * blocking public management call. The frame record is a method-name observation only:\n * not a loaded-Class origin, a unique held-request association, or cancellation history.\n * Missing frames stay unknown; an asynchronous pre-header HTTP2 request may have none.\n'), ('        checkStopFailureResourceBudget(startedAt)\n        val json = "{\\"schema\\":1,\\"capture\\":\\"captured\\",\\"scope\\":\\"$STOP_FAILURE_RESOURCE_SCOPE\\"," +\n', '        checkStopFailureResourceBudget(startedAt)\n        val frameSnapshot = stopFailureThreadSnapshot(startedAt)\n        val json = "{\\"schema\\":1,\\"capture\\":\\"captured\\",\\"scope\\":\\"$STOP_FAILURE_RESOURCE_SCOPE\\"," +\n'), ('            "\\"http2LoaderPropertyAtFailure\\":\\"$http2Property\\",\\"resources\\":[${resources.joinToString(",")}] }"\n', '            "\\"http2LoaderPropertyAtFailure\\":\\"$http2Property\\",\\"resources\\":[${resources.joinToString(",")}],\\"frameSnapshot\\":$frameSnapshot }"\n'), ('private fun stopFailureResourceHttp2Property(): String = try {\n    when (val value = System.getProperty("com.sun.webkit.useHTTP2Loader")) {\n        null -> "absent"\n        else -> when {\n            value.equals("true", ignoreCase = true) -> "true"\n            value.equals("false", ignoreCase = true) -> "false"\n            else -> "noncanonical"\n        }\n    }\n} catch (_: Throwable) { "unavailable" }\n', 'private fun stopFailureResourceHttp2Property(): String = try {\n    when (val value = System.getProperty("com.sun.webkit.useHTTP2Loader")) {\n        null -> "absent"\n        else -> when {\n            value.equals("true", ignoreCase = true) -> "true"\n            value.equals("false", ignoreCase = true) -> "false"\n            else -> "noncanonical"\n        }\n    }\n} catch (_: Throwable) { "unavailable" }\n\n/**\n * One public-JDK existing-thread snapshot after the original owning refusal. Counts are\n * frame occurrences, not callback/event counts. Same-stack pairs are observations of\n * method names in one returned stack, not direct call-edge or unique request proofs.\n *\n * A URLLoader response/close plus getResponseCode frame can narrow a response-code\n * API-phase hypothesis, conditional on the used bodies. No flag/private-field reads,\n * Class.forName, thread action, transport action, raw stack or originating path occurs.\n * Normal HTTP2 body Subscription cancellation remains in the unchanged JavaFX code;\n * no observed frame does not mean no loader, no cancellation, or no pending request.\n */\nprivate fun stopFailureThreadSnapshot(startedAt: Long): String {\n    var phase = "bean"\n    return try {\n        checkStopFailureResourceBudget(startedAt)\n        val bean = ManagementFactory.getThreadMXBean()\n        phase = "thread-ids"\n        checkStopFailureResourceBudget(startedAt)\n        val ids = bean.allThreadIds\n        if (ids.size > STOP_FAILURE_FRAME_THREAD_CAP) {\n            return "{\\"capture\\":\\"refused\\",\\"scope\\":\\"$STOP_FAILURE_FRAME_SCOPE\\",\\"phase\\":\\"thread-cap\\"}"\n        }\n        phase = "stack-query"\n        checkStopFailureResourceBudget(startedAt)\n        val rows = bean.getThreadInfo(ids, STOP_FAILURE_FRAME_DEPTH_CAP)\n        check(rows.size == ids.size)\n        val counts = IntArray(STOP_FAILURE_FRAME_TARGETS.size)\n        var available = 0\n        var unavailable = 0\n        var examined = 0\n        var responseWithCode = 0\n        var closeWithCode = 0\n        phase = "scan"\n        for (row in rows) {\n            checkStopFailureResourceBudget(startedAt)\n            if (row == null) { unavailable++; continue }\n            available++\n            val stack = row.stackTrace\n            check(stack.size <= STOP_FAILURE_FRAME_DEPTH_CAP)\n            check(stack.size <= STOP_FAILURE_FRAME_TOTAL_CAP - examined)\n            examined += stack.size\n            var responseSeen = false\n            var closeSeen = false\n            var codeSeen = false\n            for (frame in stack) {\n                checkStopFailureResourceBudget(startedAt)\n                for (index in STOP_FAILURE_FRAME_TARGETS.indices) {\n                    val target = STOP_FAILURE_FRAME_TARGETS[index]\n                    if (frame.className == target.className && frame.methodName == target.methodName) {\n                        counts[index]++\n                        when (target.label) {\n                            "urlResponse" -> responseSeen = true\n                            "urlClose" -> closeSeen = true\n                            "responseCode" -> codeSeen = true\n                        }\n                    }\n                }\n            }\n            if (responseSeen && codeSeen) responseWithCode++\n            if (closeSeen && codeSeen) closeWithCode++\n        }\n        phase = "record"\n        checkStopFailureResourceBudget(startedAt)\n        check(counts.all { it in 0..STOP_FAILURE_FRAME_TOTAL_CAP })\n        val values = STOP_FAILURE_FRAME_TARGETS.indices.joinToString(",") { index ->\n            "\\"${STOP_FAILURE_FRAME_TARGETS[index].label}\\":${counts[index]}"\n        }\n        val json = "{\\"capture\\":\\"captured\\",\\"scope\\":\\"$STOP_FAILURE_FRAME_SCOPE\\",\\"threads\\":${ids.size}," +\n            "\\"available\\":$available,\\"unavailable\\":$unavailable,\\"examined\\":$examined," +\n            "\\"occurrences\\":{$values},\\"responseWithCode\\":$responseWithCode,\\"closeWithCode\\":$closeWithCode}"\n        check(json.length <= STOP_FAILURE_FRAME_RECORD_CAP)\n        json\n    } catch (_: Throwable) {\n        "{\\"capture\\":\\"refused\\",\\"scope\\":\\"$STOP_FAILURE_FRAME_SCOPE\\",\\"phase\\":\\"$phase\\"}"\n    }\n}\n')]
EXPECTED_TARGETS = [('urlRun', 'com.sun.webkit.network.URLLoader', 'run'), ('urlResponse', 'com.sun.webkit.network.URLLoader', 'receiveResponse'), ('urlClose', 'com.sun.webkit.network.URLLoader', 'close'), ('urlCancel', 'com.sun.webkit.network.URLLoader', 'fwkCancel'), ('http2Cancel', 'com.sun.webkit.network.HTTP2Loader', 'fwkCancel'), ('http2Subscribe', 'com.sun.webkit.network.HTTP2Loader\\$3', 'onSubscribe'), ('http2Next', 'com.sun.webkit.network.HTTP2Loader\\$3', 'onNext'), ('http2Demand', 'com.sun.webkit.network.HTTP2Loader\\$3', 'requestIfNotCancelled'), ('responseCode', 'java.net.HttpURLConnection', 'getResponseCode')]


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def helper_text():
    return (ROOT / HELPER_SOURCE).read_text()


class DesktopWebViewStopFailureFramesSourceTest(unittest.TestCase):
    def test_new_frame_extension_inverse_preserves_original_stop_fixture_and_resource_body(self):
        text = helper_text()
        self.assertEqual(HELPER_POSTIMAGE_SHA256, digest(text))
        restored = text
        for old, new in reversed(HELPER_EDITS):
            self.assertEqual(1, restored.count(new))
            restored = restored.replace(new, old, 1)
        self.assertEqual(HELPER_PREIMAGE_SHA256, digest(restored))
        self.assertEqual(FIXTURE_SHA256, digest((ROOT / FIXTURE_SOURCE).read_text()))
        self.assertEqual(1, text.count('System.err.println('))
        self.assertIn('STOP_FAILURE_RESOURCE_MAX_RECORD_CHARS = 2_048', text)
        self.assertIn('STOP_FAILURE_RESOURCE_READ_BUDGET_NANOS = 250_000_000L', text)

    def test_new_frame_targets_are_fixed_public_readonly_counts_with_close_and_body_tail(self):
        text = helper_text()
        self.assertEqual(HELPER_POSTIMAGE_SHA256, digest(text))
        targets = re.findall(r'StopFailureFrameTarget\("([^"\n]+)", "([^"\n]+)", "([^"\n]+)"\)', text)
        self.assertEqual(EXPECTED_TARGETS, targets)
        self.assertIn('ManagementFactory.getThreadMXBean()', text)
        self.assertEqual(1, text.count('bean.allThreadIds'))
        self.assertEqual(1, text.count('bean.getThreadInfo('))
        self.assertIn('frame.className == target.className && frame.methodName == target.methodName', text)
        new_body = text.split('private fun stopFailureThreadSnapshot(startedAt: Long): String {', 1)[1]
        for forbidden in ('Class.forName(', 'getDeclared', 'setAccessible', 'setThreadCpuTimeEnabled',
                          'Thread(', '.interrupt(', '.suspend(', '.stop(', '.engine', '.cancel(',
                          'openConnection(', 'Socket(', 'System.setProperty(', '.toString(',
                          '.threadName', '.threadId', '.fileName', '.lineNumber', '.printStackTrace('):
            self.assertNotIn(forbidden, new_body)

    def test_new_frame_query_uses_existing_budget_and_finite_caps_without_new_poll_or_timeout(self):
        text = helper_text()
        self.assertEqual(HELPER_POSTIMAGE_SHA256, digest(text))
        new_body = text.split('private fun stopFailureThreadSnapshot(startedAt: Long): String {', 1)[1]
        for token in ('STOP_FAILURE_FRAME_THREAD_CAP = 256', 'STOP_FAILURE_FRAME_DEPTH_CAP = 32',
                      'STOP_FAILURE_FRAME_TOTAL_CAP = 8_192', 'STOP_FAILURE_FRAME_RECORD_CAP = 640',
                      'if (ids.size > STOP_FAILURE_FRAME_THREAD_CAP)',
                      'bean.getThreadInfo(ids, STOP_FAILURE_FRAME_DEPTH_CAP)',
                      'check(rows.size == ids.size)',
                      'check(stack.size <= STOP_FAILURE_FRAME_TOTAL_CAP - examined)',
                      'check(json.length <= STOP_FAILURE_FRAME_RECORD_CAP)'):
            self.assertIn(token, text)
        self.assertIn('checkStopFailureResourceBudget(startedAt)', new_body)
        self.assertNotIn('System.nanoTime()', new_body)
        for forbidden in ('while (', 'withTimeout(', 'Thread.sleep(', '.await(', '.join(', 'delay(',
                          'setReadTimeout(', 'getAllStackTraces(', 'dumpAllThreads('):
            self.assertNotIn(forbidden, new_body)

    def test_new_frame_pairs_and_refusal_are_not_held_origin_selector_cancel_history_or_eof_proofs(self):
        text = helper_text()
        self.assertEqual(HELPER_POSTIMAGE_SHA256, digest(text))
        self.assertEqual(1, text.count('val frameSnapshot = stopFailureThreadSnapshot(startedAt)'))
        original_checks = text.split('val frameSnapshot = stopFailureThreadSnapshot(startedAt)', 1)[0]
        self.assertIn('phase = "metadata-stability"', original_checks)
        self.assertIn('checkStopFailureResourceBudget(startedAt)', original_checks)
        self.assertIn('if (responseSeen && codeSeen) responseWithCode++', text)
        self.assertIn('if (closeSeen && codeSeen) closeWithCode++', text)
        self.assertIn('catch (_: Throwable)', text)
        for token in ('executing-method-names-only', 'unique held-request association',
                      'Missing frames stay unknown', 'no cancellation', 'frame occurrences, not callback/event counts',
                      'not direct call-edge or unique request proofs'):
            self.assertIn(token, text)
        new_body = text.split('private fun stopFailureThreadSnapshot(startedAt: Long): String {', 1)[1]
        self.assertNotIn('http2LoaderPropertyAtFailure', new_body)
        self.assertNotIn('peerEofs', new_body)
        self.assertNotIn('pending', new_body)
        self.assertNotIn('.message', new_body)


if __name__ == "__main__":
    unittest.main()
