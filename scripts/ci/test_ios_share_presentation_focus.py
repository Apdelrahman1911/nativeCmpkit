"""New Share library application source and finite-route controls; unexecuted at authoring.

Synthetic plan/source assertions, not UIKit/OS scope/recipient/browser evidence. These
never invoke SDK/Gradle/UIApplication or the sample. The library Kotlin fixtures
must be compiled/executed by the lead on held inputs.
"""
import copy
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

import ios_ui_application as app
import library_tests as lt
import workflow_matrix as wm

FOCUS = "share-ios-presentation-disposal"
MODULE = "calf-share"
PROFILE = "ios-share-presentation-disposal"
SOURCE = "calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt"
NATIVE = "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosSharePresentationOwnershipTest.kt"
CONTROLS = "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosShareRequestTest.kt"


class IosSharePresentationFocusTests(unittest.TestCase):
    def plan(self, root=lt.ROOT, minimum_modules=None):
        options = {"only_modules": (MODULE,), "focus": FOCUS}
        if minimum_modules is not None:
            options["minimum_modules"] = minimum_modules
        return lt.plan(root, "ios", **options)

    def test_owning_share_source_keeps_public_apis_and_uses_real_barriers_without_nil_cleanup(self):
        source = (lt.ROOT / SOURCE).read_text()
        for fragment in (
            "actual fun rememberShareLauncher(onResult: (ShareResult) -> Unit): ShareLauncher",
            "actual fun rememberShareOutcomeLauncher(options: ShareOptions, onResult: (ShareOutcome) -> Unit): ShareLauncher",
            "actual class ShareLauncher actual constructor(private val onLaunch: (ShareContent) -> Unit)",
            "actual fun launch(content: ShareContent) { onLaunch(content.snapshot()) }",
            "presenter.presentViewController(controller, true, completed)",
            "request.beginPresentation { completed -> dismissOwnedIosShare(controller, completed) }",
            "present(controller, request::presentationCompleted)",
            "controller.dismissViewControllerAnimated(false, completed)",
            "if (context != null && !context.isCancelled()) completed()",
            "if (active === request && !disposed)",
            "leases.forEach { it.close() }",
        ):
            self.assertIn(fragment, source)
        self.assertLess(source.index("request.beginPresentation {"), source.index("present(controller, request::presentationCompleted)"))
        dispose = source.split("    fun dispose() = onIosShareMain {", 1)[1].split("\n    }", 1)[0]
        self.assertIn("disposed = true", dispose)
        self.assertIn("active?.dispose()", dispose)
        self.assertNotIn("active = null", dispose)
        self.assertNotIn("presentingViewController", dispose)
        self.assertNotIn("else request.release()", source)
        self.assertNotIn("presenter.dismissViewController", source)
        self.assertNotIn("presentingViewController", source.split("private fun dismissOwnedIosShare", 1)[1])
        self.assertNotRegex(source, r"(?:Timer|delay|sleep)\s*\(")

    def test_new_application_plan_selects_only_13_owning_library_methods(self):
        plan = self.plan()
        item, = plan["expected"]
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual([MODULE], plan["explicit_module_subset"])
        self.assertEqual(":" + MODULE + ":" + lt.IOS_APPLICATION_TASK, item["task"])
        self.assertEqual("genuine-uikit-application", item["native_test_host"])
        self.assertEqual(MODULE + "/build/test-results/" + lt.IOS_APPLICATION_TASK, item["report_directory"])
        self.assertEqual(13, len(item["required_testcases"]))
        self.assertEqual(13, len(set((case["classname"], case["name"]) for case in item["required_testcases"])))
        self.assertEqual(lt.ui_application_focus_identities(FOCUS), item["required_testcases"])
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertIn(NATIVE, item["test_source_files"])
        self.assertIn(CONTROLS, item["test_source_files"])
        self.assertTrue(all(path.startswith("calf-share/") for path in item["test_source_files"]))
        self.assertNotIn("com.mohamedrejeb.calf.picker.", item["test_filter"])
        self.assertNotIn("sample", item["test_filter"])

    def test_cross_module_platform_wildcard_and_mutated_plan_refusals_stay_strict(self):
        plan = self.plan()
        for suite, modules in (("desktop", (MODULE,)), ("js", (MODULE,)), ("wasm", (MODULE,)),
                               ("android-device", (MODULE,)), ("ios", ("calf-ui",)),
                               ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=FOCUS)
        for key, value in (("task", ":calf-share:publish"), ("project", ":calf-file-picker"),
                           ("report_directory", "calf-share/build/test-results/wrongTask"), ("native_test_host", "sample"),
                           ("test_filter", "*"), ("required_testcases", []), ("test_source_files", [])):
            mutated = copy.deepcopy(plan)
            mutated["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                lt.validate_test_focus(mutated)
        for host_source in lt.IOS_SHARE_APPLICATION_SOURCES:
            mutated = copy.deepcopy(plan)
            mutated["expected"][0]["test_source_files"].remove(host_source)
            with self.subTest(missing_source=host_source), self.assertRaises(ValueError):
                lt.validate_test_focus(mutated)
        mutated = copy.deepcopy(plan)
        mutated["complete_suite_requested"] = True
        with self.assertRaises(ValueError):
            lt.validate_test_focus(mutated)

    def test_new_hosted_profile_keeps_one_canonical_iphone_and_refuses_broadened_or_foreign_rows(self):
        canonical = {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
                     "python": "python3", "simulator-kind": "iphone", "test-modules": MODULE,
                     "test-focus": FOCUS}
        self.assertEqual({"include": [canonical]}, wm.matrix(PROFILE))
        self.assertEqual(("ios-iphone",), wm.PROFILES[PROFILE])
        self.assertEqual(MODULE, wm.MODULE_SUBSETS[PROFILE])
        for slots in (("ios-iphone", "ios-ipad"), ("ios-ipad",), ("browser-wasm",), ()):
            with self.subTest(slots=slots), mock.patch.dict(wm.PROFILES, {PROFILE: slots}), self.assertRaises(ValueError):
                wm.matrix(PROFILE)
        with mock.patch.dict(wm.MODULE_SUBSETS, {PROFILE: "calf-ui"}), self.assertRaises(ValueError):
            wm.matrix(PROFILE)
        for key, value in (("runner", "macos-26-intel"), ("arch", "x64"), ("suite", "desktop"),
                           ("python", "python"), ("simulator-kind", "ipad")):
            slots = tuple({**slot, key: value} if slot["slot"] == "ios-iphone" else dict(slot) for slot in wm.SLOTS)
            with self.subTest(key=key), mock.patch.object(wm, "SLOTS", slots), self.assertRaises(ValueError):
                wm.matrix(PROFILE)
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        options, = re.findall(r"options: \[([^\]\n]+)\]", workflow)
        options = [option.strip() for option in options.split(",")]
        self.assertEqual(1, options.count(PROFILE))
        # Only finite receipt leaves, not apps/binaries/native logs or a new workflow/job.
        receipt = "build/ci-verification/${{ matrix.slot }}/native-share-application/*/receipt.json"
        self.assertEqual(1, workflow.count(receipt))
        self.assertEqual([receipt], [line.strip() for line in workflow.splitlines() if "native-share-application" in line])
        for preserved in ("native-ui-application", "native-picker-application", "native-webview-application"):
            self.assertIn("build/ci-verification/${{ matrix.slot }}/" + preserved + "/*/receipt.json", workflow)

    def test_full_and_focused_share_hosts_keep_owning_required_groups_and_the_existing_receipt_collector(self):
        self.assertEqual(lt.ui_application_focus_groups(FOCUS), lt.IOS_SHARE_APPLICATION_REQUIRED_GROUPS)
        self.assertEqual(13, sum(len(group["methods"]) for group in lt.IOS_SHARE_APPLICATION_REQUIRED_GROUPS))
        runner_source = (lt.ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertIn('"calf-share": IOS_SHARE_APPLICATION_REQUIRED_GROUPS}.get(expected["module"], ()))', runner_source)
        self.assertIn('host = app.APPLICATION_HOSTS[expected["module"]]', runner_source)
        self.assertIn('folder = safe_path(root, (output / host["receipt_subdirectory"]).relative_to(root).as_posix())', runner_source)
        self.assertIn('need(cases.keys() == required, "Focused application must execute exactly all selected methods")', runner_source)
        focused = self.plan()
        full = lt.plan(lt.ROOT, "ios", only_modules=(MODULE,))
        for plan in (focused, full):
            selected, = plan["expected"]
            self.assertEqual("genuine-uikit-application", selected["native_test_host"])
            # Routing control only: this deliberately mocked result is never native evidence.
            control = {"ios_applications": [], "errors": []}
            output = lt.ROOT / "build/ci-verification/share-new-routing-control"
            with mock.patch.object(lt, "collect_one_ios_application_receipt", return_value=control) as collect:
                self.assertEqual(control, lt.collect_ios_application_receipts(lt.ROOT, plan, output, 1, 2, {}, []))
                collect.assert_called_once_with(lt.ROOT, plan, output, 1, 2, {}, [], selected)
        binary = "calf-share/build/bin/iosSimulatorArm64/applicationDebugTest/application.kexe"
        self.assertEqual(MODULE, app.application_host(binary, None)["module"])

    def test_application_transport_binds_exact_share_directory_and_cannot_broaden_filter(self):
        selected, = self.plan()["expected"]
        args = sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + selected["test_filter"]]
        self.assertEqual(FOCUS, app.application_test_focus(args))
        binary = "calf-share/build/bin/iosSimulatorArm64/applicationDebugTest/application.kexe"
        self.assertEqual(MODULE, app.application_host(binary, FOCUS)["module"])
        self.assertEqual("native-share-application", app.application_host(binary, FOCUS)["receipt_subdirectory"])
        for patterns in ("*", "com.mohamedrejeb.calf.share.Wrong.method",
                         selected["test_filter"] + "," + selected["test_filter"],
                         selected["test_filter"] + "," + lt.IOS_WEBVIEW_REQUEST_CLASS + "." + lt.IOS_WEBVIEW_REQUEST_METHODS[0]):
            with self.subTest(patterns=patterns), self.assertRaises(ValueError):
                app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + patterns])
        for other in ("calf-ui", "calf-file-picker", "calf-webview"):
            path = app.APPLICATION_HOSTS[other]["binary_directory"] + "/application.kexe"
            with self.subTest(module=other), self.assertRaises(ValueError):
                app.application_host(path, FOCUS)
            self.assertEqual(other, app.application_host(path, None)["module"])

    def test_ignored_or_missing_native_declarations_cannot_admit_the_new_focus(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-share",\n)\n')
            (root / "calf-share").mkdir()
            (root / "calf-share/build.gradle.kts").write_text("// synthetic owning module only\n")
            paths = (*lt.IOS_SHARE_APPLICATION_SOURCES, NATIVE, CONTROLS)
            for relative in paths:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((lt.ROOT / relative).read_bytes())
            self.assertEqual(13, len(self.plan(root, (MODULE,))["expected"][0]["required_testcases"]))
            native = root / NATIVE
            original = native.read_text()
            native.write_text(original.replace("@Test fun ", "@Ignore\n    @Test fun ", 1))
            with self.assertRaisesRegex(ValueError, "remain enabled"):
                self.plan(root, (MODULE,))
            native.write_text(original.replace("@Test fun realAnimatedShareDisposalWaitsForNativePresentationAndDismissalBeforeLeaseRelease", "fun realAnimatedShareDisposalWaitsForNativePresentationAndDismissalBeforeLeaseRelease", 1))
            with self.assertRaises(ValueError):
                self.plan(root, (MODULE,))

    def test_native_source_uses_genuine_animations_scopes_and_main_dispatch_not_phase_assignment(self):
        source = (lt.ROOT / NATIVE).read_text()
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
        self.assertEqual(list(lt.IOS_SHARE_PRESENTATION_METHODS), methods)
        for fragment in (
            "presenter.presentViewController(controller, true)",
            "completed() // Forward the actual UIKit completion",
            "assertFalse(held.presentationCompletionObserved",
            "assertEquals(0, releases)",
            "assertSame(held, owning.currentRequest)",
            "held.presentationCompletionObserved && held.dismissalCompletionObserved",
            "releaseAfterDismissalCompletion = held.dismissalCompletionObserved",
            "nativePresentationCompletions++",
            "assertEquals(1, held.leases.size",
            "rememberShareOutcomeLauncher { outcome ->",
            "withContext(if (index == 1) Dispatchers.Default else Dispatchers.IO)",
            "runOnIdle { visible.value = false }",
            "if (prior == null) throw cleanup else if (prior !== cleanup) prior.addSuppressed(cleanup)",
        ):
            self.assertIn(fragment, source)
        self.assertNotRegex(source, r"(?:held|request)\.(?:phase|presentationCompletionObserved|dismissalCompletionObserved)\s*=(?!=)")
        self.assertNotRegex(source, r"(?:sleep|delay|usleep)\s*\(")
        self.assertNotIn("startAccessingSecurityScopedResource() = true", source)
        self.assertNotIn("sample.", source)

    def test_genuine_share_host_preserves_worker_root_cleanup_and_has_no_picker_special_case(self):
        host_path, tests_path, identity_path = lt.IOS_SHARE_APPLICATION_SOURCES
        host = (lt.ROOT / host_path).read_text()
        tests = (lt.ROOT / tests_path).read_text()
        identity = (lt.ROOT / identity_path).read_text()
        for fragment in ("UIApplicationMain(0, null, null, NSStringFromClass(delegate))",
                         "testLauncherEntryPoint(it)", "requestTermination()",
                         "workerTerminated=true", "rootHasAppeared &&", "window.rootViewController = previous",
                         "Refuse cleanup of a foreign root"):
            self.assertIn(fragment, host)
        self.assertIn("class NativeShareApplicationDelegate", host)
        self.assertIn("@OverrideInit", host)
        self.assertIn("assertIs<NativeShareApplicationDelegate>", tests)
        self.assertIn("failedAssertionPreservesCauseAndReleasesRealCompositionAndPresenter", tests)
        self.assertNotIn("NativePhotoProviderCancellationTest", host)
        self.assertNotIn("NATIVECMPKIT_UIKIT_MAIN_RETURNED", host)
        self.assertNotIn("NATIVECMPKIT_PICKER_HOST", tests)
        self.assertIn("first != null && second != null && first.objcPtr() == second.objcPtr()", identity)


if __name__ == "__main__":
    unittest.main()
