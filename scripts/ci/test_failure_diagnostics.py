"""Synthetic diagnostics fixtures; these never run Android, Gradle or UIKit."""
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

import failure_diagnostics as d


class FailureDiagnosticsTests(unittest.TestCase):
    def test_sample_xcode_source_error_is_retained_without_full_build_or_console_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "build/ci-verification/sample-platforms-apple"
            output.mkdir(parents=True)
            line = "/owned/sample/ios/Calf/ContentView.swift:18:13: error: cannot find 'Common' in scope"
            (output / "xcode.log").write_text("arbitrary application output\n" + line + "\n** BUILD FAILED **\n")
            result = d.capture(root, "build/ci-verification/sample-platforms-apple")
            row, = result["logs"]
            self.assertEqual("xcode.log", row["name"])
            self.assertEqual("", row["tail"])
            self.assertEqual(line + "\n", row["excerpts"][0]["text"])
            self.assertNotIn("arbitrary application output", str(row))
            self.assertFalse(result["test_success_inferred"])
            self.assertFalse(result["full_logs_uploaded"])

    def test_xcode_source_error_uses_existing_credential_and_excerpt_bounds(self):
        result = d.sections(["/owned/source.swift:3:2: error: password=private"])
        self.assertEqual(1, len(result))
        self.assertIn("omitted credential-related", result[0]["text"])
        self.assertNotIn("private", result[0]["text"])
        line = "/owned/source.swift:3:2: error: " + "x" * 5000
        self.assertLessEqual(len(d.sections([line])[0]["text"]), 2001)

    def test_browser_startup_and_webpack_failure_precede_missing_xml_without_a_full_log(self):
        for task in ("jsBrowserTest", "wasmJsBrowserTest"):
            lines = [f"> Task :calf-file-picker-coil:{task}",
                     "Module not found: Error: Can't resolve './skiko.mjs'",
                     "Cannot start ChromeHeadless", "password=private",
                     "> Task :calf-io:compileKotlinJs", "unrelated compilation output"]
            selected = [s for s in d.sections(lines) if s["kind"] == "browser-task"]
            self.assertEqual(1, len(selected))
            self.assertIn("./skiko.mjs", selected[0]["text"])
            self.assertIn("Cannot start ChromeHeadless", selected[0]["text"])
            self.assertNotIn("private", selected[0]["text"])
            self.assertNotIn("unrelated", selected[0]["text"])
            bounded = d.sections([lines[0], *("a" * 5000 for _ in range(500))])
            self.assertEqual(140, bounded[0]["last_line"])
            self.assertLessEqual(len(bounded[0]["text"].encode()), d.MAX_EXCERPT_BYTES + 100)

    def test_apk_assembly_failure_is_selected_without_a_full_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "build/ci-verification/slot"; output.mkdir(parents=True)
            (output / "apk-assembly.log").write_text(
                "> Task :calf-webview:compileAndroidDeviceTest FAILED\n"
                "e: file:///owned/calf-webview/src/androidDeviceTest/Fixture.kt:1:2 Unresolved reference 'click'.\n"
                "* What went wrong:\nOwning compilation failure\n* Try:\nUnrelated advice\n")
            result = d.capture(root, "build/ci-verification/slot")
            excerpts = result["logs"][0]["excerpts"]
            self.assertTrue(excerpts)
            self.assertIn("Unresolved reference 'click'", "".join(e["text"] for e in excerpts))
            self.assertNotIn("Unrelated advice", "".join(e["text"] for e in excerpts))
            self.assertFalse(result["test_success_inferred"])

    def test_kotlin_source_error_is_selected_even_without_a_gradle_summary(self):
        result = d.sections(["> Task :calf-webview:compileAndroidDeviceTest FAILED",
                             "e: file:///owned/calf-webview/src/androidDeviceTest/Fixture.kt:1:2 Unresolved reference 'click'.",
                             "arbitrary application output"])
        self.assertTrue(result)
        self.assertIn("Unresolved reference 'click'", "".join(e["text"] for e in result))
        self.assertNotIn("arbitrary application output", "".join(e["text"] for e in result))

    def test_compiler_error_selection_retains_existing_credential_filter(self):
        result = d.sections(["e: file:///owned/public.kt:1:2 password=private"])
        self.assertTrue(result)
        self.assertNotIn("private", result[0]["text"])
        self.assertIn("omitted credential-related", result[0]["text"])

    def test_actual_objc_initializer_exception_is_not_hidden_by_task_exit(self):
        line = ("*** Terminating app due to uncaught exception 'Initializer is not implemented', "
                "reason: 'init is not implemented in NativecmpkitUIKitLibraryTestDelegate'")
        result = d.sections(["> Task :calf-ui:iosSimulatorArm64ApplicationTest",
                             "unrelated application output", line,
                             "*** First throw call stack:", "private surrounding text",
                             "* What went wrong:", "application test exited with errors", "* Try:"])
        selected = [s for s in result if s["kind"] == "objc-exception"]
        self.assertEqual(1, len(selected))
        self.assertEqual(line + "\n", selected[0]["text"])
        self.assertEqual(3, selected[0]["first_line"])
        self.assertNotIn("surrounding", "".join(s["text"] for s in result))
        self.assertNotIn("unrelated application", "".join(s["text"] for s in result))

    def test_objc_exception_selection_keeps_credential_and_byte_bounds(self):
        line = "*** Terminating app due to uncaught exception 'Fixture', reason: 'password=private'"
        result = d.sections([line])
        self.assertEqual(1, len(result))
        self.assertEqual("objc-exception", result[0]["kind"])
        self.assertIn("omitted credential-related", result[0]["text"])
        self.assertNotIn("private", result[0]["text"])
        long = "*** Terminating app due to uncaught exception '" + "x" * 5000
        self.assertLessEqual(len(d.sections([long])[0]["text"]), 2001)

    def test_assembly_output_without_an_explicit_diagnostic_is_not_a_full_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "build/ci-verification/slot"; output.mkdir(parents=True)
            (output / "apk-assembly.log").write_text(
                "> Task :calf-webview:compileAndroidDeviceTest\narbitrary application output\n")
            result = d.capture(root, "build/ci-verification/slot")
            self.assertEqual([], result["logs"][0]["excerpts"])
            self.assertEqual("", result["logs"][0]["tail"])

    def test_an_early_connected_failure_is_not_hidden_by_the_final_stack(self):
        lines = ["> Task :calf-io:connectedAndroidDeviceTest", "First actual failure",
                 "> Task :calf-webview:connectedAndroidDeviceTest", "Last failure"]
        lines += ["Final unrelated stack frame"] * 400
        result = d.sections(lines)
        self.assertEqual(2, len(result))
        self.assertIn("First actual failure", result[0]["text"])
        self.assertNotIn("Last failure", result[0]["text"])

    def test_all_cause_chains_are_selected_with_their_actual_frames(self):
        result = d.sections(["Caused by: ActualFailure", "\tat owning.Contract.run(Contract.java:1)",
                             "unrelated body", "Caused by: NestedFailure", "\tat second.Frame.run(Frame.java:2)"])
        self.assertEqual(2, len(result))
        self.assertIn("owning.Contract", result[0]["text"])
        self.assertNotIn("unrelated body", result[0]["text"])

    def test_non_connected_task_output_is_not_an_arbitrary_full_log(self):
        self.assertEqual([], d.sections(["> Task :calf-io:desktopTest", "arbitrary application output"]))

    def test_explicit_failure_summary_stops_before_retry_advice(self):
        result = d.sections(["* What went wrong:", "Actual task error", "", "* Try:", "do not archive me"])
        self.assertIn("Actual task error", result[0]["text"])
        self.assertNotIn("do not archive me", result[0]["text"])

    def test_explicit_gradle_failure_location_is_bounded_and_not_retry_or_exception_output(self):
        result = d.sections(["* Where:", "Initialization script '/owned/scripts/ci/stage-webview.init.gradle.kts' line: 21",
                             "", "* What went wrong:", "WebView staging requires exactly root and desktop publications",
                             "* Try:", "unrelated retry advice", "* Exception is:", "unselected full stack"])
        location = [s for s in result if s["kind"] == "failure-location"]
        self.assertEqual(1, len(location))
        self.assertIn("stage-webview.init.gradle.kts' line: 21", location[0]["text"])
        self.assertNotIn("What went wrong", location[0]["text"])
        selected = "".join(s["text"] for s in result)
        self.assertNotIn("unrelated retry", selected)
        self.assertNotIn("full stack", selected)
        credential = d.sections(["* Where:", "Initialization script 'password=private' line: 1", "* Try:"])
        self.assertIn("omitted credential-related", credential[0]["text"])
        self.assertNotIn("private", credential[0]["text"])

    def test_credential_related_lines_and_control_characters_are_omitted(self):
        result = d.sanitized(["Authorization: private", "password=private", "?sig=private",
                              "https://user:private@host/", "Auth\x00orization: private", "benign\x00text\x1b"])
        self.assertNotIn("private", result)
        self.assertIn("benigntext", result)
        self.assertNotIn("\x00", result)
        self.assertNotIn("\x1b", result)

    def test_excerpt_bytes_lines_and_section_counts_are_bounded(self):
        value = d.sanitized(["a" * 5000] * 1000)
        self.assertLessEqual(len(value.encode()), d.MAX_EXCERPT_BYTES + 100)
        self.assertIn("truncated", value)
        self.assertEqual(d.MAX_EXCERPTS, len(d.sections(["Caused by: Fixed" for _ in range(500)])))

    def test_inventory_is_inert_and_does_not_accept_a_symlink_or_hardlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "owned"; folder.mkdir()
            file = folder / "test-result.pb"; file.write_bytes(b"not executed or decoded")
            value = d.inventory(root, "owned")
            self.assertTrue(value["complete"])
            self.assertEqual(["bytes", "path", "sha256"], sorted(value["files"][0]))
            self.assertEqual(b"not executed or decoded", file.read_bytes())
            (folder / "link").symlink_to(file)
            with self.assertRaises(ValueError): d.inventory(root, "owned")
            (folder / "link").unlink()
            os.link(file, folder / "hardlink")
            with self.assertRaises(ValueError): d.inventory(root, "owned")

    def test_inventory_omission_is_explicit_instead_of_empty_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "owned").mkdir()
            (root / "owned/result.pb").write_bytes(b"large under the modeled limit")
            with patch.object(d, "MAX_HASH_BYTES", 1):
                result = d.inventory(root, "owned")
            self.assertFalse(result["complete"])
            self.assertTrue(result["exists"])
            self.assertEqual([], result["files"])
            self.assertFalse(d.inventory(root, "missing")["exists"])

    def test_tree_entry_limit_also_bounds_empty_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "owned").mkdir()
            for i in range(10): (root / f"owned/empty-{i}").mkdir()
            with patch.object(d, "MAX_INVENTORY_FILES", 3):
                result = d.inventory(root, "owned")
            self.assertFalse(result["complete"])
            self.assertEqual([], result["files"])

    def test_capture_is_confined_requires_its_owned_output_and_never_infers_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "build/ci-verification/slot"; output.mkdir(parents=True)
            (output / "gradle.log").write_text("> Task :calf-io:connectedAndroidDeviceTest\nActual error\n")
            result = d.capture(root, "build/ci-verification/slot")
            self.assertFalse(result["test_success_inferred"])
            self.assertFalse(result["full_logs_uploaded"])
            # All six required device modules, including navigation/geo, with
            # public UTP and declared XML trees each. Assert the exact paths;
            # inventories are still never inferred as test passes.
            expected_modules = (
                "calf-io", "calf-file-picker", "calf-geo", "calf-webview", "calf-ui",
                "calf-navigation",
            )
            self.assertEqual([
                relative
                for module in expected_modules
                for relative in (
                    f"{module}/build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest",
                    f"{module}/build/outputs/androidTest-results/connected/androidMain",
                )
            ], [row["directory"] for row in result["android_result_file_inventories"]])
            with self.assertRaises(ValueError): d.capture(root, "build/ci-verification")
            with self.assertRaises(ValueError): d.capture(root, "../../outside")
            (output / "gradle.log").unlink()
            (output / "gradle.log").symlink_to(root / "missing")
            with self.assertRaises(ValueError): d.capture(root, "build/ci-verification/slot")

    def test_oversized_logs_remain_an_explicit_uninspected_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "build/ci-verification/slot"; output.mkdir(parents=True)
            (output / "gradle.log").write_text("not accepted under the modeled limit")
            with patch.object(d, "MAX_LOG_BYTES", 1):
                result = d.capture(root, "build/ci-verification/slot")
            self.assertFalse(result["logs"][0]["inspected"])
            self.assertNotIn("excerpts", result["logs"][0])


if __name__ == "__main__":
    unittest.main()
