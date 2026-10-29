"""Synthetic source/XML/cleanup archival fixtures, never native application tests."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

import archive_focused_junit as archive
import library_tests as tests
import test_ios_application_receipts as fixtures


class ArchiveFocusedJunitTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.root = self.fixture.root
        self.output = fixtures.OUTPUT
        self.focus = tests.IOS_VECTOR_RENDERING_FOCUS
        self.fixture.write(tests.IOS_VECTOR_THEME_SOURCE, (tests.ROOT / tests.IOS_VECTOR_THEME_SOURCE).read_bytes())
        self.prepare()

    def write(self, name, data):
        return self.fixture.write(name, json.dumps(data) if isinstance(data, dict) else data)

    def prepare(self, status="passed"):
        plan = tests.plan(self.root, "ios", only_modules=("calf-ui",), focus=self.focus)
        case, = tests.ui_application_focus_identities(self.focus)
        xml = (f'<testsuite><testcase classname="{case["classname"]}" name="{case["name"]}">' +
               ('<failure message="synthetic failure"/>' if status == "failed" else '') + '</testcase></testsuite>').encode()
        self.report_path = archive.REPORTS + "/TEST-synthetic.xml"
        self.write(self.report_path, xml)
        cases = tests.junit_cases(xml)
        row = {"path": self.report_path, "sha256": hashlib.sha256(xml).hexdigest()}
        self.receipt = {"schema_version": 1, "suite": "ios", "source_tree_dirty": False,
                        "source_revision": "a" * 40, "source_revision_after": "a" * 40,
                        "changed_inputs": [], "explicit_test_focus": self.focus,
                        "task_execution_markers": {archive.TASK: 1}, "totals": tests.case_counts(cases),
                        "modules": [{"module": "calf-ui", "task": archive.TASK, "reports": [row], "testcases": cases}],
                        "passed": status == "passed"}
        inputs = tests.snapshot_inputs(self.root)
        self.receipt.update(inputs_before_sha256=tests.input_digest(inputs), inputs_after_sha256=tests.input_digest(inputs))
        self.write(self.output + "/plan.json", plan)
        self.write(self.output + "/inputs-before.json", inputs)
        self.write(self.output + "/inputs-after.json", inputs)
        self.write(self.output + "/receipt.json", self.receipt)
        self.fixture.document["explicit_test_focus"] = self.focus
        self.fixture.save()
        self.write(self.output + "/gradle.log", "> Task :calf-ui:linkApplicationDebugTestIosSimulatorArm64 UP-TO-DATE\n")

    def run_archive(self):
        return archive.archive(self.root, self.output)

    def save_receipt(self):
        self.write(self.output + "/receipt.json", self.receipt)

    def test_exact_xml_is_preserved_before_an_independent_second_invocation(self):
        source = self.root / self.report_path
        original = source.read_bytes()
        result = self.run_archive()
        archived = self.root / result["archived_path"]
        self.assertEqual(original, archived.read_bytes())
        self.assertEqual(original, source.read_bytes())
        source.write_text("a subsequent synthetic invocation replaced the live report")
        self.assertEqual(original, archived.read_bytes())
        self.assertEqual({archive.COMPILE_TASKS[-1]: "UP-TO-DATE"}, result["observed_compile_task_statuses"])
        self.assertFalse(result["compilation_or_native_pass_inferred_from_archival"])
        self.assertFalse(result["packages_uploaded"])

    def test_failed_xml_and_incomplete_worker_are_archived_without_success_inference(self):
        self.prepare("failed")
        self.fixture.document["transport_passed"] = False
        self.fixture.document["application_protocol"]["completion"] = None
        self.fixture.save()
        result = self.run_archive()
        self.assertEqual(1, result["actual_totals"]["failures"])
        self.assertEqual("failed", result["actual_cases"][0]["status"])
        self.assertFalse(result["compilation_or_native_pass_inferred_from_archival"])
        self.assertFalse(json.loads((self.root / self.output / "receipt.json").read_text())["passed"])

    def test_second_finite_focus_is_also_accepted_without_replaying_other_theme_cases(self):
        self.focus = tests.IOS_SYSTEM_APPEARANCE_FOCUS
        self.prepare()
        result = self.run_archive()
        self.assertEqual(1, result["actual_totals"]["tests"])
        self.assertEqual(tests.IOS_VECTOR_THEME_METHODS[-1] + "[iosSimulatorArm64]", result["actual_cases"][0]["name"])

    def test_existing_archive_cannot_be_overwritten(self):
        self.run_archive()
        with self.assertRaises(ValueError):
            self.run_archive()

    def test_duplicate_nested_keys_nonfinite_numbers_and_nonobjects_are_rejected(self):
        path = self.root / self.output / "receipt.json"
        for body in ('{"cleanup":{"owned":true,"owned":false}}',
                     '{"exit_code":NaN}', '{"exit_code":Infinity}', '[]'):
            path.write_text(body)
            with self.assertRaises(ValueError):
                archive.document(self.root, self.output + "/receipt.json")

    def test_dirty_changed_or_unbound_source_cannot_be_archived(self):
        original = copy.deepcopy(self.receipt)
        for change in (
            lambda r: r.update(source_tree_dirty=True),
            lambda r: r.update(source_revision_after="b" * 40),
            lambda r: r.update(changed_inputs=[tests.IOS_VECTOR_THEME_SOURCE]),
            lambda r: r.update(inputs_after_sha256="0" * 64),
            lambda r: r.update(input_capture_error="synthetic source failure"),
        ):
            self.receipt = copy.deepcopy(original); change(self.receipt); self.save_receipt()
            with self.assertRaises(ValueError): self.run_archive()
        self.receipt = original; self.save_receipt()
        (self.root / tests.IOS_VECTOR_THEME_SOURCE).write_text("changed synthetic source")
        with self.assertRaises(ValueError): self.run_archive()

    def test_missing_execution_wrong_counts_case_or_digest_cannot_be_hidden(self):
        original = copy.deepcopy(self.receipt)
        for change in (
            lambda r: r.update(task_execution_markers={archive.TASK: 0}),
            lambda r: r["modules"][0].update(reports=[]),
            lambda r: r["modules"][0]["reports"][0].update(sha256="0" * 64),
            lambda r: r["modules"][0]["testcases"][0].update(name="unexecuted"),
            lambda r: r["totals"].update(passed=2),
        ):
            self.receipt = copy.deepcopy(original); change(self.receipt); self.save_receipt()
            with self.assertRaises(ValueError): self.run_archive()

    def test_second_launch_requires_every_owned_cleanup_witness_even_after_failure(self):
        original = copy.deepcopy(self.fixture.document)
        for key in ("owned_app_identity_reverified", "owned_app_stopped_verified",
                    "owned_app_absence_verified", "owned_local_bundle_removed"):
            self.fixture.document = copy.deepcopy(original)
            self.fixture.document["cleanup"][key] = False
            self.fixture.save()
            with self.assertRaises(ValueError): self.run_archive()
        self.fixture.document = copy.deepcopy(original)
        self.fixture.document["cleanup"]["uninstall_exit_code"] = 1
        self.fixture.save()
        with self.assertRaises(ValueError): self.run_archive()

    def test_traversal_redirected_report_and_xml_entities_are_rejected(self):
        with self.assertRaises(ValueError): archive.archive(self.root, "../foreign")
        source = self.root / self.report_path
        original = source.read_bytes()
        foreign = self.root / "foreign.xml"; foreign.write_bytes(original)
        source.unlink(); source.symlink_to(foreign)
        with self.assertRaises(ValueError): self.run_archive()
        source.unlink()
        body = b'<!DOCTYPE testsuite [<!ENTITY x "synthetic">]><testsuite>&x;</testsuite>'
        source.write_bytes(body)
        self.receipt["modules"][0]["reports"][0]["sha256"] = hashlib.sha256(body).hexdigest()
        self.save_receipt()
        with self.assertRaises(ValueError): self.run_archive()


if __name__ == "__main__":
    unittest.main()
