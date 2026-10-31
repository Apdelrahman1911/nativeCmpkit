"""Modeled exact namespace/frame checks; never actual Apple/library profile passes."""
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import apple_image_profile as p
import test_apple_image_profile as fixtures

NAMESPACE = "com.mohamedrejeb.calf.ui.utils"
CONVERSION = "kfun:" + NAMESPACE + ".ImageBitmap.toUIImage(){}"
WORKLOAD = ("kfun:" + NAMESPACE + ".UIImageMemoryDiagnosticsTest#"
            "actualLibraryConversionsRemainBoundedDuringOwnedAllocationProfile(){}")
PRIVATE = "private-allocation-frame-must-not-be-exported"


class AppleProfileFrameOwnershipTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "allocation.xml"

    def summary(self, tree):
        self.path.write_bytes(ET.tostring(tree, encoding="utf-8"))
        return p.allocation_summary(self.path)

    def frame_rows(self, values):
        tree = ET.Element("trace-query-result")
        for value in values:
            row = ET.SubElement(tree, "row")
            ET.SubElement(row, "frame", name=value, address="0x987654")
        return self.summary(tree)

    def modeled_profile(self, value):
        # Reuse fixture helpers only; none of its existing test methods are run.
        # Every native-control and profiling-tool call remains mocked.
        fixture = fixtures.AppleImageProfileTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.prepare()

        def execute(*arguments):
            result = fixture.execute(*arguments)
            command = arguments[1]
            if "--xpath" in command:
                tree = ET.Element("trace-query-result")
                row = ET.SubElement(tree, "row")
                ET.SubElement(row, "frame", name=value, address="0x987654")
                Path(command[-1]).write_bytes(ET.tostring(tree, encoding="utf-8"))
            return result

        fixture.request(execute)
        fixture.driver.close()
        return fixture

    def test_generic_basename_and_unqualified_or_foreign_workload_class_never_own_rows(self):
        values = (
            "ImageUtils.kt",
            "convert (ImageUtils.kt:42)",
            "org.example.foreign.OtherLibrary.convert ImageUtils.kt",
            "UIImageMemoryDiagnosticsTest",
            "UIImageMemoryDiagnosticsTest#actualLibraryConversionsRemainBoundedDuringOwnedAllocationProfile(){}",
            "kfun:org.example.foreign.UIImageMemoryDiagnosticsTest#actualLibraryConversionsRemainBoundedDuringOwnedAllocationProfile(){}",
        )
        summary = self.frame_rows(values)
        self.assertEqual(len(values), summary["rows"])
        self.assertEqual(0, summary["owned_allocation_rows"])
        self.assertFalse(summary["owned_library_frame_seen"])
        self.assertEqual([], summary["matched_fixed_symbols"])

    def test_namespace_prefix_suffix_and_glued_identifier_collisions_never_own_rows(self):
        values = (
            "kfun:org.example.foreign." + NAMESPACE + ".ImageBitmap.toUIImage",
            "foreign_" + NAMESPACE + ".ImageBitmap.toUIImage",
            "x" + NAMESPACE + ".ImageBitmap.toUIImage",
            "\u03bb" + NAMESPACE + ".ImageBitmap.toUIImage",
            "prefix$" + NAMESPACE + ".ImageBitmap.toUIImage",
            NAMESPACE + "Foreign.ImageBitmap.toUIImage",
            NAMESPACE + "_foreign.ImageBitmap.toUIImage",
            NAMESPACE + "$foreign.ImageBitmap.toUIImage",
            NAMESPACE + "2.ImageBitmap.toUIImage",
            NAMESPACE + "\u00e9.ImageBitmap.toUIImage",
            NAMESPACE + "-foreign ImageUtils.kt",
            NAMESPACE + "/ImageUtils.kt",
        )
        summary = self.frame_rows(values)
        self.assertEqual(len(values), summary["rows"])
        self.assertEqual(0, summary["owned_allocation_rows"])
        self.assertEqual([], summary["matched_fixed_symbols"])

    def test_exact_conversion_and_required_workload_namespace_frames_remain_owned(self):
        values = (NAMESPACE, CONVERSION, WORKLOAD,
                  "kfun:" + NAMESPACE + ".UIImageMemoryDiagnosticsTest.<init>(){}",
                  CONVERSION + " (ImageUtils.kt:42)")
        summary = self.frame_rows(values)
        self.assertEqual(len(values), summary["owned_allocation_rows"])
        self.assertTrue(summary["owned_library_frame_seen"])
        self.assertEqual(sorted(p.NATIVE_SYMBOLS), summary["matched_fixed_symbols"])

    def test_optional_class_and_filename_labels_require_whole_symbols_after_namespace_ownership(self):
        values = (CONVERSION + " " + token for token in (
            "ForeignUIImageMemoryDiagnosticsTest", "UIImageMemoryDiagnosticsTestAlias",
            "$UIImageMemoryDiagnosticsTest", "UIImageMemoryDiagnosticsTest$Foreign",
            "ForeignImageUtils.kt", "ImageUtils.kt2", "ImageUtils.kt.foreign",
            "Foreign.ImageUtils.kt", "\u03bbImageUtils.kt"))
        summary = self.frame_rows(tuple(values))
        self.assertEqual(summary["rows"], summary["owned_allocation_rows"])
        self.assertEqual([NAMESPACE], summary["matched_fixed_symbols"])

    def test_actual_frame_fields_and_explicit_frame_backtrace_references_keep_namespace_correlation(self):
        for form in ("text", "name", "fmt", "frame-ref", "backtrace-ref", "nested-backtrace"):
            with self.subTest(form=form):
                tree = ET.Element("trace-query-result")
                ET.SubElement(tree, "metadata", name=NAMESPACE)
                ET.SubElement(tree, "frame", id="owned", fmt=CONVERSION)
                ET.SubElement(tree, "frame", id="foreign", name="org.example.foreign.Other ImageUtils.kt")
                stack = ET.SubElement(tree, "backtrace", id="owned-stack")
                ET.SubElement(stack, "frame", ref="owned")
                row = ET.SubElement(tree, "row")
                if form in {"text", "name", "fmt"}:
                    frame = ET.SubElement(row, "frame")
                    if form == "text": frame.text = CONVERSION
                    else: frame.set(form, CONVERSION)
                elif form == "frame-ref": ET.SubElement(row, "frame", ref="owned")
                elif form == "backtrace-ref": ET.SubElement(row, "backtrace", ref="owned-stack")
                else:
                    nested = ET.SubElement(row, "backtrace")
                    ET.SubElement(nested, "frame", name=CONVERSION)
                rejected = ET.SubElement(tree, "row")
                ET.SubElement(rejected, "frame", ref="foreign")
                summary = self.summary(tree)
                self.assertEqual(2, summary["rows"])
                self.assertEqual(1, summary["owned_allocation_rows"])
                self.assertEqual([NAMESPACE], summary["matched_fixed_symbols"])

    def test_generic_rows_metadata_and_other_frame_fields_cannot_borrow_namespace_or_labels(self):
        tree = ET.Element("trace-query-result")
        ET.SubElement(tree, "metadata", name=NAMESPACE)
        ET.SubElement(tree, "frame", id="unused-owned", name=WORKLOAD)
        for value in ("ImageUtils.kt", "org.example.foreign.UIImageMemoryDiagnosticsTest"):
            row = ET.SubElement(tree, "row")
            ET.SubElement(row, "frame", name=value)
        metadata_row = ET.SubElement(tree, "row")
        ET.SubElement(metadata_row, "metadata", name=NAMESPACE)
        ET.SubElement(metadata_row, "frame", name="ImageUtils.kt")
        owned_row = ET.SubElement(tree, "row")
        frame = ET.SubElement(owned_row, "frame", name=CONVERSION, fmt="UIImageMemoryDiagnosticsTest ImageUtils.kt")
        frame.text = PRIVATE
        summary = self.summary(tree)
        self.assertEqual(4, summary["rows"])
        self.assertEqual(1, summary["owned_allocation_rows"])
        self.assertEqual([NAMESPACE], summary["matched_fixed_symbols"])
        self.assertNotIn(PRIVATE, json.dumps(summary))
        self.assertNotIn(CONVERSION, json.dumps(summary))

    def test_modeled_exit_zero_and_zero_leaks_cannot_pass_foreign_basename_allocations(self):
        frame = "org.example.foreign.OtherLibrary.convert ImageUtils.kt " + PRIVATE
        fixture = self.modeled_profile(frame)
        receipt = fixture.driver.receipt
        self.assertEqual(4, len(receipt["commands"]))
        self.assertTrue(all(command["exit_code"] == 0 for command in receipt["commands"]))
        self.assertEqual((0, 0), (receipt["leak_summary"]["leaks"], receipt["leak_summary"]["leaked_bytes"]))
        self.assertFalse(receipt["supported"])
        self.assertFalse(receipt["profile_passed"])
        self.assertEqual(0, receipt["exports"][0]["owned_allocation_rows"])
        self.assertTrue(receipt["errors"])
        # Attempt/cleanup validity deliberately remains distinct from profile success.
        self.assertTrue(p.validate_attempt(receipt, fixtures.DEVICE, fixtures.BUNDLE))
        self.assertTrue(receipt["owned_private_tree_removed"])
        self.assertNotIn(PRIVATE, json.dumps(receipt))
        self.assertNotIn(frame, json.dumps(receipt))
        self.assertNotIn("0x987654", json.dumps(receipt))

    def test_modeled_namespace_workload_preserves_positive_structure_and_frame_privacy(self):
        frame = WORKLOAD + " (ImageUtils.kt:42) " + PRIVATE
        fixture = self.modeled_profile(frame)
        receipt = fixture.driver.receipt
        self.assertTrue(receipt["supported"])
        self.assertTrue(receipt["profile_passed"])
        self.assertEqual(1, receipt["exports"][0]["owned_allocation_rows"])
        self.assertEqual(sorted(p.NATIVE_SYMBOLS), receipt["exports"][0]["matched_fixed_symbols"])
        self.assertTrue(p.validate_attempt(receipt, fixtures.DEVICE, fixtures.BUNDLE))
        self.assertTrue(receipt["owned_private_tree_removed"])
        self.assertTrue(receipt["owned_ack_removed"])
        self.assertTrue(receipt["owned_readiness_removed"])
        self.assertNotIn(PRIVATE, json.dumps(receipt))
        self.assertNotIn(frame, json.dumps(receipt))
        self.assertNotIn("0x987654", json.dumps(receipt))
        self.assertFalse(receipt["ASan_verified"])
        self.assertFalse(receipt["release_readiness_certified"])


if __name__ == "__main__": unittest.main()
