"""One owning source-only boundary guard; no Objective-C/Kotlin/SDK/native call.

The private async completion may record bounded facts but must not assert/throw
through WKWebView's completion block. Actual main-thread/once/result/native WK
acceptance remains required in the unchanged genuine UIApplication methods.
"""
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
NATIVE = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewRequestAcceptanceTest.kt"
PIN_GUARD = "scripts/ci/test_ios_webview_request_dns_focus.py"
HOST = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeWebViewApplicationHost.kt"
OUTSIDE_HELPER_SHA256 = "a96d4b49bba790fdb3230d8925f29db4084d789c744ad5ee2d961e6e7a0e54f0"
HELPER_SHA256 = "5b6123f2a968ccd06e4ca3ec2725a5c1e3666cd212a49a8aa28e3012fb73e6bd"


class IosWebViewRequestCallbackBoundaryTests(unittest.TestCase):
    def test_async_helper_records_facts_then_checks_main_once_and_result_without_native_criteria_change(self):
        source = (ROOT / NATIVE).read_text()
        start = source.index("    private fun NativeApplicationUiTest.evaluate(state: WebViewState, script: String): JavascriptResult {")
        end = source.index("    private class Stage(", start)
        helper = source[start:end].rstrip("\n") + "\n"
        prefix = "state.evaluateJavascriptResult(script) {"
        self.assertEqual(1, helper.count(prefix))
        callback = helper[helper.index(prefix) + len(prefix):]
        callback = callback[:callback.index("}")]
        code = re.sub(r"//[^\n]*", "", callback)
        self.assertNotRegex(code, r"\b(?:assert[A-Za-z]*|check|require|error|throw)\b",
                            "A test failure must not escape the real Objective-C completion block")
        self.assertIn("if (!NSThread.isMainThread) offMain = true", code)
        self.assertEqual(1, code.count("calls++"))
        self.assertEqual(1, code.count("result = it"))
        self.assertIn("assertFalse(NSThread.isMainThread)", helper[:helper.index(prefix)])
        self.assertIn("waitForNative { result != null || offMain }", helper)
        checking = helper[helper.index("return onApplicationMain {"):]
        self.assertIn('assertFalse(offMain, "WebKit completion left the owned main thread")', checking)
        self.assertIn("assertEquals(1, calls)", checking)
        self.assertIn("assertNotNull(result)", checking)
        self.assertEqual(HELPER_SHA256, hashlib.sha256(helper.encode()).hexdigest())
        # Entire two native method bodies, Foundation control/counters, ownership
        # predicates and cleanup remain exact outside this one private helper.
        self.assertEqual(OUTSIDE_HELPER_SHA256,
                         hashlib.sha256(source.replace(helper, "", 1).encode()).hexdigest())
        # The combined source-bound guard must bind the owning repaired file,
        # not its uncompiled pre-repair identity. No old model suite is invoked.
        native_pin = hashlib.sha256(source.encode()).hexdigest()
        matches = re.findall('"' + re.escape(NATIVE) + r'":\s*"([0-9a-f]{64})"', (ROOT / PIN_GUARD).read_text())
        self.assertEqual([native_pin], matches)
        host = (ROOT / HOST).read_text()
        self.assertIn("dispatch_sync(dispatch_get_main_queue()) { result = runCatching(action) }", host)
        self.assertIn("return checkNotNull(result).getOrThrow()", host)
        self.assertIn("try { host.close() } catch (cleanup: Throwable)", host)
        self.assertIn("prior.addSuppressed(cleanup)", host)


if __name__ == "__main__": unittest.main()
