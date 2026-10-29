"""Finite iOS IO/Coil selection guards, not Apple or library runtime tests."""
from pathlib import Path
import re
import tempfile
import unittest

import library_tests as runner
import workflow_matrix as matrix


def profile_options(workflow):
    """Literal owned choice list, not an adjacency/ordering requirement."""
    choices = re.findall(r"(?m)^        options: \[([^\]\n]+)\]$", workflow)
    if len(choices) != 1:
        raise ValueError("Exactly one literal verification profile list is required")
    values = [value.strip() for value in choices[0].split(",")]
    if len(values) != len(set(values)) or any(not re.fullmatch(r"[a-z][a-z0-9-]*", value) for value in values):
        raise ValueError("Invalid or duplicate verification profile")
    return values


class IosIoProfileTests(unittest.TestCase):
    def test_focused_profile_selects_only_io_and_coil_on_one_real_apple_slot(self):
        rows = matrix.matrix("ios-io")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("ios-iphone", rows[0]["slot"])
        self.assertEqual("ios", rows[0]["suite"])
        self.assertEqual("macos-26", rows[0]["runner"])
        self.assertEqual("arm64", rows[0]["arch"])
        self.assertEqual("iphone", rows[0]["simulator-kind"])
        self.assertEqual("calf-io,calf-file-picker-coil", rows[0]["test-modules"])

    def test_subset_mutation_cannot_weaken_full_apple_or_ui_profiles(self):
        row = matrix.matrix("ios-io")["include"][0]
        row["test-modules"] = "calf-ui"
        self.assertEqual("calf-io,calf-file-picker-coil", matrix.matrix("ios-io")["include"][0]["test-modules"])
        for profile in ("ios", "apple", "all"):
            self.assertTrue(all("test-modules" not in item for item in matrix.matrix(profile)["include"]))
        self.assertEqual("calf-ui", matrix.matrix("ios-ui")["include"][0]["test-modules"])
        self.assertEqual(11, len(matrix.matrix("all")["include"]))

    def test_real_subset_plan_includes_native_guards_resources_and_coil_without_ui_app(self):
        plan = runner.plan(runner.ROOT, "ios", only_modules=("calf-io", "calf-file-picker-coil"))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-io", "calf-file-picker-coil"], plan["explicit_module_subset"])
        by_module = {item["module"]: item for item in plan["expected"]}
        self.assertEqual({"calf-io", "calf-file-picker-coil"}, set(by_module))
        for item in by_module.values():
            self.assertEqual(item["project"] + ":iosSimulatorArm64Test", item["task"])
            self.assertNotIn("native_test_host", item)
        io_files = by_module["calf-io"]["test_source_files"]
        self.assertIn("calf-io/src/iosTest/kotlin/com/mohamedrejeb/calf/io/NativeGuardedCopyTest.kt", io_files)
        self.assertIn("calf-io/src/iosTest/kotlin/com/mohamedrejeb/calf/io/NativeSourceLifecycleTest.kt", io_files)
        self.assertIn("calf-file-picker-coil/src/iosTest/kotlin/com/mohamedrejeb/calf/picker/coil/NativeKmpFileFetcherTest.kt",
                      by_module["calf-file-picker-coil"]["test_source_files"])
        self.assertIn("calf-ui", plan["test_bearing_modules_not_requested"])
        self.assertIn("calf-file-picker", plan["test_bearing_modules_not_requested"])

    def test_complete_ios_suite_requires_authored_coil_tests_not_only_desktop(self):
        self.assertIn("calf-file-picker-coil", runner.MINIMUM_MODULES["ios"])
        self.assertIn("calf-file-picker-coil", {item["module"] for item in runner.plan(runner.ROOT, "ios")["expected"]})

    def test_missing_coil_source_cannot_turn_into_green_uncovered_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            modules = runner.MINIMUM_MODULES["ios"]
            lines = []
            for module in modules:
                parts = module.split("/")
                lines.append('    ":' + ':'.join(parts) + '",')
                folder = root / module
                folder.mkdir(parents=True)
                (folder / "build.gradle.kts").write_text("// synthetic fixture\n")
                if module != "calf-file-picker-coil":
                    source = folder / "src/commonTest/kotlin/Fixture.kt"
                    source.parent.mkdir(parents=True)
                    source.write_text("// synthetic test input, no native execution\n")
                if module in runner.IOS_APPLICATION_HOST_SOURCES:
                    # Honour the existing real-application source gate even in
                    # this synthetic plan; an unrelated early rejection is not
                    # evidence that missing Coil sources were detected.
                    for relative in runner.IOS_APPLICATION_HOST_SOURCES[module]:
                        source = root / relative
                        source.parent.mkdir(parents=True, exist_ok=True)
                        source.write_text("// synthetic required source path, no UIKit execution\n")
            (root / "settings.gradle.kts").write_text("include(\n" + "\n".join(lines) + "\n)\n")
            with self.assertRaisesRegex(ValueError, "calf-file-picker-coil"):
                runner.plan(root, "ios")

    def test_workflow_exposes_only_the_fixed_profile_with_read_only_verification(self):
        workflow = (runner.ROOT / ".github/workflows/gradle.yml").read_text()
        profiles = profile_options(workflow)
        self.assertIn("ios-io", profiles)
        self.assertEqual(set(matrix.PROFILES), set(profiles), "No missing or arbitrary workflow profile")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)

    def test_profile_order_and_new_owned_neighbors_do_not_remove_io_coverage(self):
        workflow = (runner.ROOT / ".github/workflows/gradle.yml").read_text()
        expected = profile_options(workflow)
        reordered = re.sub(r"(?m)^        options: \[[^\]\n]+\]$",
                           "        options: [" + ", ".join(reversed(expected)) + "]", workflow)
        self.assertIn("ios-io", profile_options(reordered))
        self.assertEqual(set(expected), set(profile_options(reordered)))
        self.assertIn("ios-date-bounds", profile_options(workflow))

    def test_missing_duplicate_or_computed_lists_cannot_pass_the_owned_choice_contract(self):
        for workflow in ("", "        options: [ios-io, ios-io]", "        options: [${{ inputs.task }}]",
                         "        options: [ios-io]\n        options: [ios]"):
            with self.assertRaises(ValueError):
                profile_options(workflow)


if __name__ == "__main__":
    unittest.main()
