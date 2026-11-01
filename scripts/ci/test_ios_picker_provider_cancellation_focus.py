# SPDX-License-Identifier: Apache-2.0
"""Missing-only route/source/XML guards. Synthetic checks are not Foundation acceptance."""
from collections import Counter
import copy
from pathlib import Path
import re
import tempfile
import time
import unittest

import ios_ui_application as app
import library_tests as r
import workflow_matrix as matrix
from test_android_webview_request_state import body_after
import test_ios_picker_batch_focus as batch


def require_provider_witnesses(source):
    """Protect causal/public/native boundaries without pinning unrelated source formatting."""
    armed = body_after(source, "fun expectDeliberateCancellation(")
    for token in ("protect {", "clientEntered.value == 0 && clientReturned.value == 0",
                  "deliberateCancellationError == null", "deliberateCancellationError = error"):
        if token not in armed:
            raise ValueError("The native callback arm requires the locked zero/one-arm boundary")
    forwarded = body_after(source, "override fun loadFileRepresentationForTypeIdentifier(")
    steps = ("super.loadFileRepresentationForTypeIdentifier(typeIdentifier)",
             "clientEntered.incrementOwned()", "sameNativeObject(error, deliberateCancellationError)",
             "deliberateCancellationEntered.incrementOwned()", "completionHandler(url, error)",
             "clientReturned.incrementOwned()", "deliberateCancellationReturned.incrementOwned()",
             "actualProgress = progress", "return progress")
    if any(token not in forwarded for token in steps) or (
            [forwarded.index(token) for token in steps] != sorted(forwarded.index(token) for token in steps)):
        raise ValueError("Forward the genuine progress/callback unchanged and correlate entry/return identity")
    if forwarded.count("protect {") != 4 or "try { completionHandler(url, error) } finally {" not in forwarded:
        raise ValueError("Callback witnesses must share the arm lock and forward outside that lock")
    completed = body_after(source, "fun completeCancelledTransport(")
    steps = ("cancelled.value == 1", "!manager.fileExistsAtPath(partialPath)",
             'mapOf("NativeCmpKitHeldCompletionNonce" to NSUUID().UUIDString)',
             "provider.expectDeliberateCancellation(error)", "resolve(null, error)")
    if any(token not in completed for token in steps) or (
            [completed.index(token) for token in steps] != sorted(completed.index(token) for token in steps)):
        raise ValueError("Only a new retained native error disclosed by the deliberate completion acknowledges it")
    cancelled = body_after(source, "progress.cancellationHandler =")
    if ("cancelled.compareAndSet(0, 1)" not in cancelled or
            "protect { closeHandlesLocked(); removePartialLocked() }" not in cancelled):
        raise ValueError("The actual cooperative producer cancellation must close its handles before removing partial output")
    method = body_after(source, "@Test fun " + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0])
    steps = ("delegate.picker(picker, results)", "pending.firstChunkCopied.value == 1",
             "ownedDescriptorCounts(pending.sourceIdentity, partialIdentity)",
             "runOnIdle { included.value = false }", "pending.cancelled.value == 1 && pending.closedHandles.value == 2",
             "pending.completeCancelledTransport()", "pending.provider.deliberateCancellationReturned.value == 1",
             "retained.launch()")
    if any(token not in method for token in steps) or (
            [method.index(token) for token in steps] != sorted(method.index(token) for token in steps)):
        raise ValueError("Real in-flight native copy and public disposal/cleanup precede acknowledged late completion")
    required = ("override fun itemProvider(): NSItemProvider = supplied", "registerFileRepresentationForTypeIdentifier(",
                "NSItemProviderRepresentationVisibilityOwnProcess", "progress.cancellationHandler =",
                "progress.cancellable = true", "NSFileHandle.fileHandleForReadingAtPath(sourcePath)",
                "NSFileHandle.fileHandleForWritingAtPath(partialPath)", "readDataOfLength(65_536uL)",
                "progress.completedUnitCount = chunk.length.toLong()", "closeHandlesLocked(); removePartialLocked()",
                "assertTrue(delivered.isEmpty()); assertTrue(errors.isEmpty())", "assertEquals(before, pickerDirectories())",
                "ownedDescriptorCounts(pending.sourceIdentity, partialIdentity, stagedIdentity)",
                "assertContentEquals(bytes, KmpFile(NSURL.fileURLWithPath(pending.sourcePath)).readByteArray())",
                "check(provider.loadRequests.value == 1 && provider.clientEntered.value == 1)",
                "if (callbackAcknowledged) clean {", "getdtablesize()", "fstat(fd, observed.ptr)")
    if any(token not in source for token in required):
        raise ValueError("Missing genuine native producer/progress/descriptor/staging/source/cleanup witness")
    if re.search(r"\b(?:assumeTrue|assumeFalse|presentationCompleted|resume|Robolectric|mockk|Mockito)\s*\(", source):
        raise ValueError("No fake admission, continuation, mock or skipped native witness")


class IosPickerProviderCancellationFocusTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-file-picker",),
                      focus=r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS)

    def test_one_missing_method_uses_existing_genuine_app_and_one_canonical_slot(self):
        row, = matrix.matrix("ios-picker-provider-cancellation")["include"]
        self.assertEqual(("ios-iphone", "calf-file-picker", r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS),
                         tuple(row[key] for key in ("slot", "test-modules", "test-focus")))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(":calf-file-picker:" + r.IOS_APPLICATION_TASK, item["task"])
        self.assertEqual("genuine-uikit-application", item["native_test_host"])
        self.assertEqual(1, len(item["required_testcases"]))
        self.assertIn(r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE, item["test_source_files"])
        self.assertIsNone(app.profile_debug_entitlements(r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS))

    def test_exact_gradle_and_native_filters_exclude_all_accepted_old_methods(self):
        plan = self.plan()
        item, = plan["expected"]
        selector = r.IOS_PICKER_PROVIDER_CANCELLATION_CLASS + "." + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0]
        self.assertEqual(selector, item["test_filter"])
        self.assertEqual(["--tests", selector], r.gradle_command("ios", plan, simulator=batch.fixtures.DEVICE)[-2:])
        self.assertEqual(r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS,
                         app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + selector]))
        selected = {(case["classname"], case["name"])
                    for case in r.ui_application_focus_identities(r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS)}
        for focus in (r.IOS_PICKER_BOUNDARY_FOCUS, r.IOS_PICKER_RECOVERY_FOCUS, r.IOS_PICKER_ADMISSION_FOCUS):
            old = {(case["classname"], case["name"]) for case in r.ui_application_focus_identities(focus)}
            self.assertFalse(selected & old)

    def test_wrong_suite_module_omission_and_tampered_plan_refuse(self):
        for suite, modules in (("desktop", ("calf-file-picker",)), ("ios", ("calf-ui",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS)
        original = self.plan()
        for key, value in (("native_test_host", "command-line"), ("test_filter", r.IOS_PICKER_PROVIDER_CANCELLATION_CLASS),
                           ("required_testcases", []), ("task", ":calf-file-picker:iosSimulatorArm64Test")):
            changed = copy.deepcopy(original)
            changed["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(changed)

    def test_absent_ignored_duplicate_or_extra_method_declarations_refuse(self):
        helper = batch.IosPickerBatchTests("test_one_slot_exact_26_methods_no_replay_or_publishing_tasks")
        self.addCleanup(helper.doCleanups)
        fixture, _, _, _ = helper.fixture()
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        target = fixture.write(r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE, source)
        self.assertTrue(r.validate_test_focus(self.plan(fixture.root)))
        for changed in (source.replace("@Test", "@IgnoredTest", 1), source + "\n@Test fun foreign() {}\n",
                        source + "\n@Test fun " + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0] + "() {}\n"):
            target.write_text(changed)
            with self.assertRaises(ValueError): self.plan(fixture.root)
        target.unlink()
        with self.assertRaises((ValueError, FileNotFoundError)): self.plan(fixture.root)

    def test_original_single_xml_identity_is_required_not_old_cases_or_silence(self):
        plan = self.plan()
        item, = plan["expected"]
        identities = item["required_testcases"]
        def collect(cases, outcome="", markers=1, duplicate=False):
            xml = '<testsuite>' + ''.join(
                f'<testcase classname="{c["classname"]}" name="{c["name"]}">{outcome}</testcase>' for c in cases) + '</testsuite>'
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                reports = root / item["report_directory"]
                reports.mkdir(parents=True)
                (reports / "TEST-explicitly-synthetic.xml").write_text(xml)
                if duplicate: (reports / "TEST-duplicate.xml").write_text(xml)
                now = time.time_ns()
                return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                         Counter({item["task"]: markers}), host_system="Darwin")
        self.assertEqual([], collect(identities)["errors"])
        for cases in ([], identities * 2, r.ui_application_focus_identities(r.IOS_PICKER_RECOVERY_FOCUS)):
            with self.subTest(cases=len(cases)): self.assertTrue(collect(cases)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(outcome=outcome): self.assertTrue(collect(identities, outcome)["errors"])
        self.assertTrue(collect(identities, markers=0)["errors"])
        self.assertTrue(collect(identities, duplicate=True)["errors"])

    def test_source_retains_genuine_native_public_and_causal_acknowledgement_boundaries(self):
        require_provider_witnesses((r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text())

    def test_earlier_generic_cancel_or_value_equal_error_cannot_acknowledge_deliberate_completion(self):
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        mutations = (("clientEntered.value == 0 && clientReturned.value == 0", "clientReturned.value >= 0"),
                     ("deliberateCancellationError == null", "true"),
                     ("sameNativeObject(error, deliberateCancellationError)", "error == deliberateCancellationError"),
                     ("provider.expectDeliberateCancellation(error)", "provider.expectDeliberateCancellation(cancellationError())"),
                     ("resolve(null, error)", "resolve(null, cancellationError())"),
                     ("pending.provider.deliberateCancellationReturned.value == 1", "pending.provider.clientReturned.value >= 0"))
        for before, after in mutations:
            with self.subTest(removed=before), self.assertRaises(ValueError):
                require_provider_witnesses(source.replace(before, after, 1))

    def test_progress_forwarding_public_disposal_and_resource_cleanup_cannot_be_substituted(self):
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        for before, after in (("return progress", "return NSProgress(parent = null, userInfo = null)"),
                              ("completionHandler(url, error)", "completionHandler(null, cancellationError())"),
                              ("runOnIdle { included.value = false }", "pending.close()"),
                              ("closeHandlesLocked(); removePartialLocked()", "removePartialLocked()"),
                              ("if (callbackAcknowledged) clean {", "if (true) clean {")):
            with self.subTest(removed=before), self.assertRaises(ValueError):
                require_provider_witnesses(source.replace(before, after, 1))


if __name__ == "__main__":
    unittest.main()
