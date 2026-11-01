"""New important source/refusal tests only; all native/compile counts are ZERO here.

Temporary fixtures are copied source bytes, not executed sample code or native
proof. This suite intentionally does not replay old sample source/config checks.
"""
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

import library_tests as r
import secure_alert_input_plan as s
import test_ios_application_receipts as receipts
import workflow_matrix as matrix


def populate_bound_source_root(root: Path) -> None:
    """Owned source-only fixture; no build or application is run."""
    (root / "settings.gradle.kts").write_text('include(\n    ":calf-ui",\n    ":calf-io",\n)\n')
    for module in ("calf-ui", "calf-io"):
        folder = root / module / "src/commonTest/kotlin"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "Common.kt").write_text("// synthetic test source; never executed\n")
        (root / module / "build.gradle.kts").write_text("// synthetic build; never executed\n")
    for relative in dict.fromkeys((*r.IOS_APPLICATION_SOURCES, *s.QUALIFIED_SOURCE_SHA256, s.SCREEN, s.BUILD)):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((r.ROOT / relative).read_bytes())


class SecureAlertInputSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        populate_bound_source_root(self.root)

    def plan(self):
        return r.plan(self.root, "ios", only_modules=(s.MODULE,), focus=s.FOCUS)

    def assert_bound(self):
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        return plan

    def test_exact_original_descriptor_expression_and_real_sample_seam_are_retained(self):
        plan = self.assert_bound()
        helper = (self.root / s.HELPER).read_text()
        marker = "internal fun sampleAlertDialogInputFields(): List<AlertDialogIosTextField> = "
        self.assertEqual(1, helper.count(marker))
        expression = helper.partition(marker)[2].removesuffix("\n")
        self.assertEqual(s.ORIGINAL_DESCRIPTOR_EXPRESSION_SHA256, hashlib.sha256(expression.encode()).hexdigest())
        self.assertEqual(2, expression.count("AlertDialogIosTextField("))
        self.assertEqual(2, expression.count("onValueChange = {"))
        contract = plan["expected"][0]["secure_alert_input_contract"]
        self.assertEqual(s.QUALIFIED_SOURCE_SHA256, contract["qualified_source_sha256"])
        self.assertFalse(contract["sample_screen_compiled"])
        self.assertFalse(contract["sample_application_executed"])
        self.assertNotIn(s.SCREEN, plan["expected"][0]["test_source_files"])
        self.assertEqual(1, plan["expected"][0]["test_source_files"].count(s.HELPER))

    def test_original_full_application_cases_and_eleven_slots_remain_unmodified(self):
        self.assert_bound()
        self.assertEqual(tuple(receipts.REQUIRED), tuple(r.IOS_APPLICATION_CASES))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        complete = r.plan(self.root, "ios", minimum_modules=("calf-ui", "calf-io"))
        self.assertTrue(complete["complete_suite_requested"])
        self.assertNotIn("explicit_test_focus", complete)
        for item in complete["expected"]:
            self.assertNotIn("secure_alert_input_contract", item)
        self.assertEqual({"calf-ui", "calf-io"}, {item["module"] for item in complete["expected"]})

    def test_missing_empty_oversized_or_changed_qualified_source_cannot_fallback_to_common_tests(self):
        self.assert_bound()
        for relative in s.QUALIFIED_SOURCE_SHA256:
            target = self.root / relative
            original = target.read_bytes()
            mutations = (None, b"", original + b"\n// public source drift\n")
            if relative == s.HELPER:
                mutations += (b"x" * (s.MAX_SOURCE_BYTES + 1),)
            for changed in mutations:
                with self.subTest(source=relative, change="absent" if changed is None else "source-bytes"):
                    if target.exists(): target.unlink()
                    if changed is not None: target.write_bytes(changed)
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        self.plan()
                    if target.exists(): target.unlink()
                    target.write_bytes(original)
                    self.assert_bound()

    def test_symlink_hardlink_and_additional_sample_inputs_refuse_before_acceptance(self):
        self.assert_bound()
        helper = self.root / s.HELPER
        original = helper.read_bytes()
        other = self.root / "public-owned-helper-control.kt"
        other.write_bytes(original)
        helper.unlink(); helper.symlink_to(other)
        with self.assertRaises(ValueError): self.plan()
        helper.unlink(); helper.write_bytes(original)
        self.assert_bound()
        helper.unlink(); os.link(other, helper)
        with self.assertRaises(ValueError): self.plan()
        helper.unlink(); helper.write_bytes(original)
        self.assert_bound()
        extra = helper.parent / "AdditionalSampleSource.kt"
        extra.write_text("// public extra-source refusal control\n")
        with self.assertRaises(ValueError): self.plan()
        extra.unlink()
        self.assert_bound()

    def test_only_ios_test_may_compile_the_single_helper_not_a_sample_module_or_broader_tree(self):
        self.assert_bound()
        target = self.root / s.BUILD
        original = target.read_text()
        changes = (
            original.replace(s.BUILD_SEAM, s.BUILD_SEAM.replace('"iosTest"', '"commonTest"'), 1),
            original.replace(s.BUILD_SEAM, "// removed isolated source seam", 1),
            original + "\n" + s.BUILD_SEAM + "\n",
            original + '\nsourceSets.getByName("iosMain").kotlin.srcDir(rootProject.file("sample/common/src/commonMain"))\n',
            original + '\nsourceSets.commonTest.dependencies { implementation(projects.sample.common) }\n',
        )
        for changed in changes:
            with self.subTest(change="build-confinement"):
                target.write_text(changed)
                with self.assertRaises(ValueError): self.plan()
                target.write_text(original)
                self.assert_bound()

    def test_current_sample_import_invocation_and_no_log_policy_cannot_be_replaced(self):
        self.assert_bound()
        target = self.root / s.SCREEN
        original = target.read_text()
        for changed in (
            original.replace("import com.mohamedrejeb.calf.sample.alertinput.sampleAlertDialogInputFields", "// removed factory import", 1),
            original.replace("textFields = sampleAlertDialogInputFields()", "textFields = emptyList()", 1),
            original + '\nfun forbiddenPublicLogControl() { println("public-control") }\n',
        ):
            target.write_text(changed)
            with self.assertRaises(ValueError): self.plan()
            target.write_text(original)
            self.assert_bound()
        helper = self.root / s.HELPER
        original_helper = helper.read_text()
        # Textual injection only: no callback or public value is actually run/logged.
        helper.write_text(original_helper.replace("// Secure input must never", 'println("value=$it") // Secure input must never', 1))
        with self.assertRaises(ValueError): self.plan()
        helper.write_text(original_helper)
        self.assert_bound()

    def test_held_inputs_add_only_compiled_helper_and_originating_screen_provenance(self):
        self.assert_bound()
        unrelated = self.root / "sample/common/src/commonMain/unrelated/OtherSample.kt"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("// not a library input or callback dependency\n")
        before = r.snapshot_inputs(self.root)
        for relative in (s.HELPER, s.SCREEN):
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(), before[relative])
        self.assertNotIn(unrelated.relative_to(self.root).as_posix(), before)
        target = self.root / s.SCREEN
        target.write_bytes(target.read_bytes() + b"\n// public provenance-change control\n")
        after = r.snapshot_inputs(self.root)
        self.assertEqual({s.SCREEN}, {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)})
        self.assertNotEqual(before[s.SCREEN], self.plan()["expected"][0]["secure_alert_input_contract"]["originating_screen_sha256"])

    def test_contract_rejects_wrong_hash_schema_scope_missing_dependency_and_foreign_sample_compilation(self):
        plan = self.assert_bound()
        item = plan["expected"][0]
        original = copy.deepcopy(item["secure_alert_input_contract"])
        changes = (
            {"physical_device_verified": True}, {"sample_application_executed": True},
            {"capture_scope": "unified-system-log"}, {"schema_version": True},
            {"owning_build_sha256": "not-an-owned-hash"}, {"unknown_claim": True},
            {"qualified_source_sha256": {**s.QUALIFIED_SOURCE_SHA256, s.HELPER: "0" * 64}},
        )
        for changed in changes:
            candidate = copy.deepcopy(plan)
            candidate["expected"][0]["secure_alert_input_contract"].update(changed)
            with self.subTest(change="contract-claim"), self.assertRaises(ValueError): r.validate_test_focus(candidate)
        for sources in ([source for source in item["test_source_files"] if source != s.HELPER],
                        item["test_source_files"] + [s.HELPER], item["test_source_files"] + [s.SCREEN]):
            candidate = copy.deepcopy(plan)
            candidate["expected"][0]["test_source_files"] = sources
            with self.assertRaises(ValueError): r.validate_test_focus(candidate)
        unrelated = r.plan(self.root, "ios", only_modules=(s.MODULE,))
        unrelated["expected"][0]["secure_alert_input_contract"] = original
        with self.assertRaises(ValueError): r.validate_test_focus(unrelated)

    def test_native_main_event_pixels_and_restore_requirements_are_qualified_not_method_name_only(self):
        self.assert_bound()
        replacements = {
            s.NATIVE: (
                ("runOnIdle { keyboard.start() }", "keyboard.start()"),
                ("probe.forEach { character -> field.insertText(character.toString()) }", "field.text = probe"),
                ("keyboard.visibleEpoch > beforeEpoch", "keyboard.visibleEpoch >= 0"),
                ("securePixels[0].contentEquals(securePixels[1])", "true"),
                ("check(!plainPixels[0].contentEquals(plainPixels[1]))", "check(true)"),
            ),
            s.CAPTURE: (
                ("dup2(savedOutput, outputDescriptor)", "outputDescriptor"),
                ("dup2(savedError, errorDescriptor)", "errorDescriptor"),
                ("length in 0..maxBytes.toLong()", "length >= 0"),
                ("consoleCaptureLease.unlock()", "Unit"),
            ),
        }
        for relative, fragments in replacements.items():
            target = self.root / relative
            original = target.read_text()
            for old, new in fragments:
                self.assertIn(old, original)
                target.write_text(original.replace(old, new, 1))
                with self.subTest(source=relative, requirement="qualified-native-criterion"), self.assertRaises(ValueError): self.plan()
                target.write_text(original)
                self.assert_bound()

    def test_owning_command_refuses_postplan_helper_origin_or_build_drift_before_any_execution(self):
        plan = self.assert_bound()
        def command():
            return r.gradle_command("ios", plan, root=self.root,
                simulator="11111111-1111-1111-1111-111111111111")
        self.assertIn(":calf-ui:iosSimulatorArm64ApplicationTest", command())
        for relative in (s.HELPER, s.SCREEN, s.BUILD):
            target = self.root / relative
            original = target.read_bytes()
            target.write_bytes(original + b"\n// public postplan source drift\n")
            with self.subTest(source=relative), self.assertRaises(ValueError): command()
            target.write_bytes(original)
            self.assertIn(":calf-ui:iosSimulatorArm64ApplicationTest", command())

    def test_unconfigured_or_empty_legacy_build_cannot_be_promoted_to_the_new_focused_verification(self):
        self.assert_bound()
        build = self.root / s.BUILD
        original = build.read_bytes()
        for changed in (b"", b"// synthetic legacy build without external helper\n"):
            build.write_bytes(changed)
            self.assertEqual((), s.external_test_sources(self.root))
            ordinary = r.plan(self.root, "ios", only_modules=(s.MODULE,))
            self.assertNotIn(s.HELPER, ordinary["expected"][0]["test_source_files"])
            self.assertNotIn("secure_alert_input_contract", ordinary["expected"][0])
            with self.assertRaises(ValueError): self.plan()
            build.write_bytes(original)
            self.assert_bound()

    def test_corrected_console_control_inventory_requires_cloexec_one_stderr_overflow_and_fixed_refusals(self):
        self.assert_bound()
        helper = (self.root / s.CAPTURE).read_text()
        controls = (self.root / s.CONTROLS).read_text()
        self.assertEqual(9, len(s.CAPTURE_METHODS))
        for method in s.CAPTURE_METHODS:
            self.assertEqual(1, controls.count("@Test fun " + method + "("))
        self.assertIn("(it.last().toInt() and FD_CLOEXEC) == FD_CLOEXEC", controls)
        self.assertIn('check(fputs("s".repeat(257), nativeStderr) >= 0)', controls)
        self.assertIn("assertEquals(OwnedNativeConsoleStage.entries.toList(), control.successfulStages", controls)
        for stage in ("STDERR_FILE_ACQUIRE", "STDOUT_BACKUP_ACQUIRE", "STDERR_BACKUP_ACQUIRE", "STDOUT_READ", "STDERR_READ", "STDOUT_RESTORE", "STDERR_RESTORE", "STDOUT_FLAGS", "STDERR_FLAGS", "STDOUT_BACKUP_CLOSE", "STDERR_BACKUP_CLOSE", "STDOUT_FILE_CLOSE", "STDERR_FILE_CLOSE"):
            self.assertIn("OwnedNativeConsoleStage." + stage, helper)
            self.assertIn("OwnedNativeConsoleStage." + stage, controls)
        self.assertIn("primary.suppressedExceptions.single() === control.cleanupRefusal", controls)

    def test_controlled_entry_cannot_certify_absence_or_replace_the_genuine_native_input_capture(self):
        plan = self.assert_bound()
        native = (self.root / s.NATIVE).read_text()
        helper = (self.root / s.CAPTURE).read_text()
        self.assertNotIn("captureOwnedNativeConsoleForControl", native)
        self.assertNotIn("OwnedNativeConsoleFailureControl", native)
        self.assertIn("captureOwnedNativeConsoleImpl(maxBytes, null, action)", helper)
        self.assertIn('check(failureControl == null) { "A controlled console attempt cannot certify input absence" }', helper)
        self.assertIn("after a genuine successful restore/flags/close operation", helper.lower())
        self.assertIn("no concurrent-thread coverage", helper)
        self.assertFalse(plan["expected"][0]["secure_alert_input_contract"]["physical_device_verified"])
        self.assertEqual("current-process-stdout-stderr-only", plan["expected"][0]["secure_alert_input_contract"]["capture_scope"])

    def test_source_binding_refuses_removing_new_short_read_cleanup_and_suppression_requirements(self):
        self.assert_bound()
        replacements = {
            s.CAPTURE: (
                ("actualRead - 1UL", "actualRead"),
                ("failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDOUT_RESTORE)", "Unit"),
                ("failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDERR_FILE_CLOSE)", "Unit"),
                ("check(failureControl == null)", "check(true)"),
            ),
            s.CONTROLS: (
                ("(it.last().toInt() and FD_CLOEXEC) == FD_CLOEXEC", "true"),
                ("primary.suppressedExceptions.single() === control.cleanupRefusal", "true"),
            ),
        }
        for relative, fragments in replacements.items():
            target = self.root / relative
            original = target.read_text()
            for old, new in fragments:
                self.assertEqual(1, original.count(old))
                target.write_text(original.replace(old, new, 1))
                with self.subTest(source=relative, requirement="corrected-controlled-refusal"), self.assertRaises(ValueError): self.plan()
                target.write_text(original)
                self.assert_bound()
