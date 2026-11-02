# SPDX-License-Identifier: Apache-2.0
"""NEW owning source/planner controls, never JVM/UIKit/OS/recipient test passes."""
import ast
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import library_tests as lt
import terminal_awt240_source_projection as projection
import workflow_matrix as wm

ROOT = Path(__file__).resolve().parents[2]
SHARE = "calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt"
NATIVE = "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosSharePresentationOwnershipTest.kt"
SCENARIOS = "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/ShareTerminalBarrierScenarios.kt"
DESKTOP = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewStopRedirectAcceptanceTest.kt"
OWNER = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/BoundedDesktopAwtWindow.kt"
OWNER_TEST = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/BoundedDesktopAwtWindowTest.kt"
SPEC_SHA256 = "57aea63782e79cf6bce95c4d443c73bceaf2c7a4e1a4d74d963bbb82e7eb69b2"
ADDITION_SHA256 = {'calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/ShareTerminalBarrierScenarios.kt': 'c60c9aa31dc3e23734184ced80b2911ac655ec105d7197c5defad56bf8e84679', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/BoundedDesktopAwtWindow.kt': 'c7bccc89f020490ea6198b837c7a9e386b051a0926ec22e17b3557699420b082', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/BoundedDesktopAwtWindowTest.kt': '0ab669d606bc6416e892f8509a694758c5a24447f904ed439de763886597bdc5', 'scripts/ci/terminal_awt240_source_projection.py': 'e839883e8c80a49de66ff334489dadd4189b40a862d924920ffa35fc35b2ae1d'} # Exact source-only additions.


def digest(data):
    return hashlib.sha256(data).hexdigest()


def literal(text, name):
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.Assign) and
             any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(nodes) != 1:
        raise ValueError("Exact unique immutable declaration required")
    return ast.literal_eval(nodes[0].value)


class TerminalAwt240SourceControls(unittest.TestCase):
    def setUp(self):
        raw = projection.SPEC_PATH.read_bytes()
        self.assertEqual(SPEC_SHA256, digest(raw))
        self.spec = json.loads(raw)
        self.assertEqual("8a2b307e1b30f8702e7ef68d456c06f06ef0ba1a", self.spec["baseline_head"])

    def test_current_whole_images_invert_and_round_trip_all_explicit_fragments(self):
        self.assertEqual(14, len(self.spec["bindings"]))
        for rel, binding in self.spec["bindings"].items():
            current = (ROOT / rel).read_bytes()
            self.assertEqual(binding["after_sha256"], digest(current))
            restored = projection.source_before_terminal_awt240(rel, current)
            self.assertEqual(binding["before_sha256"], digest(restored))
            forward = restored
            for item in binding["fragments"]:
                self.assertEqual(1, forward.count(item["before"].encode()))
                forward = forward.replace(item["before"].encode(), item["after"].encode(), 1)
            self.assertEqual(current, forward)
        self.assertEqual("a1edf546173cd5b13f7a6eedb729a97e2c5fc554ada8834a5be3c07b75980ebf", self.spec["bindings"][SHARE]["before_sha256"])
        self.assertEqual("250b536388c872d6fd975ad009ca47a750575df28b1eb0d1981ba6d124d63b9d", self.spec["bindings"][NATIVE]["before_sha256"])
        self.assertEqual("c828401cd5e0dbae8138e5fc61e4540568e0d076d66953b746124fb104dc8a90", self.spec["bindings"][DESKTOP]["before_sha256"])

    def test_unreviewed_full_sources_partial_edits_types_and_corrupted_fragments_refuse(self):
        for rel in self.spec["bindings"]:
            raw = (ROOT / rel).read_bytes()
            for changed in (raw + b"\n", raw[:-1], b"unreviewed", None, raw.decode()):
                with self.subTest(path=rel), self.assertRaises(ValueError):
                    projection.source_before_terminal_awt240(rel, changed)
        rel = SHARE
        for field in ("before_fragment_sha256", "after_fragment_sha256", "before", "after"):
            altered = json.loads(json.dumps(self.spec))
            altered["bindings"][rel]["fragments"][0][field] += "unreviewed"
            with tempfile.TemporaryDirectory() as folder:
                file = Path(folder) / "explicitly-synthetic.json"
                file.write_text(json.dumps(altered))
                with patch.object(projection, "SPEC_PATH", file), self.assertRaises(ValueError):
                    projection.source_before_terminal_awt240(rel, (ROOT / rel).read_bytes())

    def test_current_terminal_path_keeps_first_result_native_barriers_main_queue_and_cleanup_before_reentry(self):
        text = (ROOT / SHARE).read_text()
        complete = text.split("        fun complete(deliver: () -> Unit) {", 1)[1].split("        private fun advanceDisposal", 1)[0]
        for token in ("if (disposalRequested || phase == IosShareRequestPhase.Released) return", "terminalResult = deliver",
                      "disposalRequested = true", "controller.completionWithItemsHandler = null", "advanceDisposal()"):
            self.assertIn(token, complete)
        self.assertNotIn("release()", complete)
        callback = text.split("        controller.completionWithItemsHandler = { _, completed, _, error ->", 1)[1].split("        controller.popoverPresentationController", 1)[0]
        self.assertIn("onIosShareMain {", callback)
        self.assertIn("request.complete { if (!disposed) onResult(result) }", callback)
        self.assertNotIn("active = null", callback)
        self.assertNotIn("request.release()", callback)
        self.assertIn("completed -> ShareOutcome.Completed", callback)
        self.assertIn("else -> ShareOutcome.Dismissed", callback)
        self.assertIn("error != null -> ShareOutcome.Failed", callback)
        release = text.split("        fun release() {", 1)[1].split("    private var active", 1)[0]
        self.assertLess(release.index("leases.forEach { it.close() }"), release.index("notifyOwner() }"))
        self.assertLess(release.index("notifyOwner() }"), release.index("deliver?.invoke()"))
        self.assertIn("terminalResult = null // Real owner disposal", text)
        self.assertIn("dismissNative = null", release)
        self.assertNotRegex(text, r"(?:Timer|delay|sleep)\s*\(")

    def test_corrected_public_stimulus_keeps_completed_assertions_and_requires_actual_dismissal(self):
        text = (ROOT / NATIVE).read_text()
        failed = text.split("    @Test fun publicRememberedShareMainDefaultIoReentryAndDisposalUseCurrentCallbacks()", 1)[1].split("    private fun NativeApplicationUiTest.disposalFixture", 1)[0]
        self.assertIn("verifyControlledIosShareTerminalBarriers()", failed)
        self.assertIn("active?.presentationCompletionObserved == true && active.phase == IosShareRequestPhase.Presented", failed)
        self.assertIn("completed(null, true, null, null)\n                completed(null, true, null, null)", failed)
        self.assertNotIn("dismissViewControllerAnimated", failed)
        self.assertNotIn("ownedNativeDismissalCompleted", failed)
        self.assertIn('assertTrue(request.dismissalCompletionObserved, "An activity input is not a native dismissal barrier")', failed)
        self.assertIn("assertTrue(hasNoOwnedNativePresentation(parent, native))", failed)
        for token in ("(1..index + 1).map { it to ShareOutcome.Completed }", "(1..3).map { it to ShareOutcome.Completed }",
                      "withContext(if (index == 1) Dispatchers.Default else Dispatchers.IO)", "runOnIdle { visible.value = false }",
                      "An old native block cannot deliver or clear a new generation"):
            self.assertIn(token, failed)
        self.assertNotRegex(failed, r"(?:request|held)\.(?:phase|presentationCompletionObserved|dismissalCompletionObserved)\s*=(?!=)")

    def test_four_new_controlled_regressions_and_nine_awt_tests_are_real_enabled_library_sources(self):
        for rel, expected in ADDITION_SHA256.items():
            self.assertEqual(expected, digest((ROOT / rel).read_bytes()))
        scenarios = (ROOT / SCENARIOS).read_text()
        names = ["terminalDuringPresentationWaitsForBothCompletionsAndDeduplicates", "ownerDisposalSuppressesAPendingTerminalResult",
                 "neverPresentedTerminalReleasesBeforeApplicationCode", "throwingTerminalCallbackCannotRepeatReleaseOrDelivery"]
        for name in names:
            self.assertEqual(1, scenarios.count("    " + name + "()"))
            self.assertEqual(1, scenarios.count("private fun " + name + "()"))
        self.assertIn("= onApplicationMain {", scenarios)
        self.assertIn("assertSame(failure, assertFailsWith<IllegalStateException> { complete() })", scenarios)
        self.assertNotRegex(scenarios, r"@(Test|Ignore|Disabled|IgnoredTest)\b")
        awt = (ROOT / OWNER_TEST).read_text()
        self.assertEqual(9, len(re.findall(r"@Test\s+fun\s+\w+", awt)))
        self.assertNotRegex(awt, r"@(Ignore|Disabled|IgnoredTest)\b")
        self.assertIn("throwFromDisposal in listOf(false, true)", awt)
        self.assertIn("worker.finished()", awt)

    def test_bounded_awt_ownership_preserves_original_stop_predicates_http_and_redirect_body(self):
        current = (ROOT / DESKTOP).read_text()
        old = projection.text_before_terminal_awt240(DESKTOP, current)
        start = "    @Test fun actual302RedirectAndPublicReloadKeepNativeRequestAndTerminalMetadataDistinct()"
        end = "    private suspend fun awaitFx"
        self.assertEqual(old.split(start, 1)[1].split(end, 1)[0], current.split(start, 1)[1].split(end, 1)[0])
        server = "    private enum class Endpoint"
        self.assertEqual(old.split(server, 1)[1], current.split(server, 1)[1])
        for token in ("native.engine.loadWorker.state == Worker.State.CANCELLED &&", "!native.engine.loadWorker.isRunning",
                      "state.loadingState == LoadingState.Finished", "cancellations.get() == 1", "server.peerEofs(Endpoint.StopHeld) == 1",
                      "server.pending(Endpoint.StopHeld) == 0", "navigator.stopLoading()", "withTimeout(10_000)"):
            self.assertIn(token, current)
        self.assertNotIn("SwingUtilities.invokeAndWait", current)
        self.assertIn("window.awaitCreated(30_000)", current)
        self.assertIn("window.close(10_000)", current)
        self.assertIn("withTimeout(10_000) {\n                        onFxThread", current)
        owner = (ROOT / OWNER).read_text()
        self.assertIn("creation.compareAndSet(Creation.Queued, Creation.Cancelled)", owner)
        self.assertIn("if (initializing || !disposalAttempted.compareAndSet(false, true)) return", owner)
        self.assertIn("val window = owned.get()", owner)
        self.assertLess(owner.index("window?.let(dispose)"), owner.index("owned.compareAndSet(window, null)"))
        self.assertNotIn("owned.getAndSet", owner)

    def test_finite_windows_and_share_plans_keep_one_missing_method_and_pin_owning_support(self):
        windows = lt.plan(ROOT, "desktop", only_modules=("calf-webview",), focus=lt.WEBVIEW_DESKTOP_STOP_WINDOWS_RECOVERY_FOCUS)
        selected, = windows["expected"]
        self.assertEqual([DESKTOP, OWNER], selected["test_source_files"])
        self.assertEqual({p: digest((ROOT / p).read_bytes()) for p in (DESKTOP, OWNER)}, selected["test_source_sha256"])
        self.assertEqual(1, selected["required_original_xml"])
        self.assertEqual(1, len(selected["required_testcases"]))
        self.assertNotIn("actual302Redirect", selected["test_filter"])
        self.assertNotIn("BoundedDesktopAwtWindowTest", selected["test_filter"])
        share = lt.plan(ROOT, "ios", only_modules=("calf-share",), focus=lt.IOS_SHARE_REMEMBERED_FAILURE_FOCUS)
        app, = share["expected"]
        self.assertEqual(1, len(app["required_testcases"]))
        self.assertIn(SCENARIOS, app["test_source_files"])
        self.assertIn("four NEW", share["scope"])
        self.assertTrue(lt.validate_test_focus(windows)); self.assertTrue(lt.validate_test_focus(share))
        for profile in ("webview-desktop-stop-windows-recovery", "ios-share-remembered-failure-observation"):
            self.assertEqual(1, len(wm.matrix(profile)["include"]))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
            (root / "calf-webview").mkdir()
            (root / "calf-webview/build.gradle.kts").write_text("// synthetic source-only root\n")
            for rel in (DESKTOP, OWNER, lt.WEBVIEW_DESKTOP_REQUEST_SOURCE):
                path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes((ROOT / rel).read_bytes())
            self.assertTrue(lt.validate_test_focus(lt.plan(root, "desktop", only_modules=("calf-webview",), focus=lt.WEBVIEW_DESKTOP_STOP_WINDOWS_RECOVERY_FOCUS)))
            owner = root / OWNER; owner.write_bytes(owner.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "owning source changed"):
                lt.plan(root, "desktop", only_modules=("calf-webview",), focus=lt.WEBVIEW_DESKTOP_STOP_WINDOWS_RECOVERY_FOCUS)

    def test_current_camera_maps_are_exact_and_every_before47_and_existing_method_body_is_preserved(self):
        path = "scripts/ci/test_android_camera_owned_avd_console_name.py"
        current = (ROOT / path).read_text(); old = projection.text_before_terminal_awt240(path, current)
        self.assertEqual(literal(old, "BOUND_SOURCE_BEFORE47"), literal(current, "BOUND_SOURCE_BEFORE47"))
        after = literal(current, "BOUND_SOURCE_AFTER47")
        self.assertEqual(47, len(after))
        for rel, expected in after.items():
            self.assertEqual(expected, digest((ROOT / rel).read_bytes()))
        for path in (path, "scripts/ci/test_android_camera_pre_reporter_fail_fast.py", "scripts/ci/test_android_camera205_owning_admission.py",
                     "scripts/ci/test_ios_share_owned_root_barriers.py", "scripts/ci/test_ios_share_terminal_failure_observation.py",
                     "scripts/ci/test_share_settings_fixture_recovery.py", "scripts/ci/test_ui_alert_important_recovery.py"):
            now = (ROOT / path).read_text(); was = projection.text_before_terminal_awt240(path, now)
            def methods(text):
                return {n.name: ast.dump(n, include_attributes=False) for cls in ast.parse(text).body if isinstance(cls, ast.ClassDef)
                        for n in cls.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
            self.assertEqual(methods(was), methods(now), path)


if __name__ == "__main__":
    unittest.main()
