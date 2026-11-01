"""New API35 recovery source guards only; no SDK, build, Git or native execution."""
from __future__ import annotations

import ast
import os
from pathlib import Path
import re
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("API35_RECOVERY_FOCUS_TREE", Path(__file__).resolve().parents[2])).resolve()
METADATA = Path(os.environ.get("API35_RECOVERY_FOCUS_METADATA", TREE / "scripts/ci")).resolve()
PROFILE = "android-permission-storage-api35-recovery"
ROUTES = ("android-permission-demo", "android-storage-api35-normal", "android-storage-api35-all-files")
MODULE = "calf-permissions/core"
SDK = "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-35;google_apis;x86_64"
WORKFLOW = (TREE / ".github/workflows/gradle.yml").read_text()
MATRIX_SOURCE = (TREE / "scripts/ci/workflow_matrix.py").read_text()
BATCH_SOURCE = (TREE / "scripts/ci/android_device_batch_plan.py").read_text()


def inert_module(name, source, filename):
    module = types.ModuleType(name)
    module.__file__ = str(filename)
    return module, compile(source, str(filename), "exec")


# Execute only declarative batch/storage metadata and the unchanged matrix
# function; no library/native module or process-backed CLI is imported or run.
fixed, fixed_code = inert_module("android_device_batch_plan", BATCH_SOURCE, TREE / "scripts/ci/android_device_batch_plan.py")
storage_path = METADATA / "android_storage_compatibility_plan.py"
storage, storage_code = inert_module("android_storage_compatibility_plan", storage_path.read_text(), storage_path)
workflow, workflow_code = inert_module("api35_recovery_workflow_under_test", MATRIX_SOURCE, TREE / "scripts/ci/workflow_matrix.py")
with patch.dict(sys.modules, {fixed.__name__: fixed, storage.__name__: storage, workflow.__name__: workflow}):
    exec(fixed_code, fixed.__dict__)
    exec(storage_code, storage.__dict__)
    exec(workflow_code, workflow.__dict__)


def permission_spec():
    syntax = ast.parse((METADATA / "library_tests.py").read_text())
    value = next(node.value for node in syntax.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "ANDROID_PERMISSION_DEVICE_SPECS" for target in node.targets))
    index = next(index for index, key in enumerate(value.keys) if isinstance(key, ast.Name) and key.id == "ANDROID_PERMISSION_DEMO_FOCUS")
    return ast.literal_eval(value.values[index])


class Api35PermissionStorageRecoveryFocusTests(unittest.TestCase):
    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("Source guard attempted an external process")
        self.run_patch = patch.object(subprocess, "run", forbidden)
        self.popen_patch = patch.object(subprocess, "Popen", forbidden)
        self.run_patch.start()
        self.popen_patch.start()
        self.addCleanup(self.run_patch.stop)
        self.addCleanup(self.popen_patch.stop)

    def test_recovery_contains_only_three_existing_api35_routes_and_no_io(self):
        self.assertEqual(fixed.BATCHES[PROFILE], ROUTES)
        self.assertNotIn("android-io-reference-regressions", fixed.BATCHES[PROFILE])
        self.assertEqual([fixed.SELECTIONS[name] for name in ROUTES], [
            (35, MODULE, "android-permission-demo-contracts"),
            (35, MODULE, "android-storage-api35-normal"),
            (35, MODULE, "android-storage-api35-all-files"),
        ])
        self.assertTrue(all(type(fixed.SELECTIONS[name][0]) is int for name in ROUTES))
        self.assertEqual(fixed.MODULES[PROFILE], MODULE)

    def test_recovery_selects_one_existing_host_and_one_batch_not_a_bare_device_focus(self):
        row, = workflow.matrix(PROFILE)["include"]
        self.assertEqual(row, {"slot": "android-device-batch-permission-storage-api35-recovery",
            "suite": "android-device", "runner": "ubuntu-24.04", "arch": "x64", "python": "python3",
            "test-modules": MODULE, "android-batch": PROFILE})
        self.assertEqual(workflow.PROFILES[PROFILE], ("android-device-api35",))
        self.assertEqual(workflow.MODULE_SUBSETS[PROFILE], MODULE)
        self.assertNotIn("emulator-api", row)
        self.assertNotIn("test-focus", row)
        self.assertNotIn("serial-emulator-api", row)

    def test_recovery_sdk_and_dispatch_option_are_exactly_once_with_only_image35(self):
        branches = re.findall(r"inputs\.profile == '" + re.escape(PROFILE) + r"' && '([^']+)'", WORKFLOW)
        self.assertEqual(branches, [SDK])
        self.assertEqual(fixed.SDK_PACKAGES[PROFILE], SDK)
        self.assertEqual([item for item in SDK.split() if item.startswith("system-images;")],
                         ["system-images;android-35;google_apis;x86_64"])
        options = re.search(r"options: \[([^\n]+)\]", WORKFLOW).group(1).split(",")
        choices = [item.strip() for item in options]
        self.assertEqual(choices.count(PROFILE), 1)
        self.assertEqual(set(choices), set(workflow.PROFILES))
        self.assertEqual(len(choices), len(set(choices)))

    def test_recovery_is_exactly_five_unchanged_original_native_identities_not_io_or_media(self):
        permission = permission_spec()
        cases = [(permission["classname"], method) for method in permission["methods"]]
        cases += [(storage.CLASS, storage.row_for(name).method) for name in ROUTES[1:]]
        self.assertEqual(cases, [
            ("com.mohamedrejeb.calf.permissions.AndroidPermissionDemoDeviceTest", "callOnFreshApprovedVariantUsesPublicRequestAndActualSystemGrant"),
            ("com.mohamedrejeb.calf.permissions.AndroidPermissionDemoDeviceTest", "denialThenPermanentDenialKeepsActualRationaleAndOneResultPerRequest"),
            ("com.mohamedrejeb.calf.permissions.AndroidPermissionDemoDeviceTest", "pickersReadRealDocumentsAndImagesWithoutAllFilesOrSmsPermissions"),
            ("com.mohamedrejeb.calf.permissions.AndroidStorageCompatibilityTest", "modernAppScopedAndSafDoNotNeedAllFiles"),
            ("com.mohamedrejeb.calf.permissions.AndroidStorageCompatibilityTest", "modernManifestAloneDoesNotGrantAllFilesAndOwnedSettingRestores"),
        ])
        self.assertEqual(len(cases), 5)
        self.assertEqual(len(set(cases)), 5)
        self.assertEqual([storage.row_for(name).api for name in ROUTES[1:]], [35, 35])
        self.assertEqual([storage.row_for(name).flavor for name in ROUTES[1:]], ["modern", "allFiles"])

    def test_recovery_addition_preserves_all_original_batches_and_all_eleven_full_slots(self):
        storage_routes = ("android-storage-api28", "android-storage-api29-target28", "android-storage-api29-legacy",
                          "android-storage-api29-scoped", "android-storage-api30-normal", "android-storage-api30-all-files")
        self.assertEqual(fixed.BATCHES["android-io-permission-storage-api35"], ("android-io-reference-regressions", *ROUTES))
        self.assertEqual(fixed.BATCHES["android-storage-compatibility"], storage_routes)
        self.assertEqual(fixed.BATCHES["android-permission-storage-compatibility"],
                         ("android-media-selection-api33", "android-media-selection-api34", *storage_routes))
        self.assertEqual([row["slot"] for row in workflow.matrix("all")["include"]], [
            "desktop-linux-x64", "android-host", "browser-js", "browser-wasm", "desktop-macos-arm64", "ios-iphone",
            "desktop-windows-x64", "desktop-linux-arm64", "desktop-macos-x64", "ios-ipad", "android-device-api35",
        ])
        self.assertEqual(len(workflow.SLOTS), 11)

    def test_recovery_reuses_only_existing_batch_dispatch_without_new_runner_or_controller_branch(self):
        self.assertIn("ANDROID_BATCH: ${{ matrix.android-batch }}", WORKFLOW)
        for command in (
            '"$PYTHON" scripts/ci/android_device_batch.py plan --batch "$ANDROID_BATCH" > build/ci-plan/plan.json',
            '"$PYTHON" scripts/ci/android_device_batch.py run --batch "$ANDROID_BATCH" --output "build/ci-verification/$SLOT"',
        ):
            self.assertEqual(WORKFLOW.count(command), 1)
        self.assertEqual(WORKFLOW.count(PROFILE), 2)
        self.assertEqual(MATRIX_SOURCE.count(PROFILE), 2)
        self.assertEqual(BATCH_SOURCE.count(PROFILE), 4)
        for declaration in ("SELECTIONS",):
            value = next(node.value for node in ast.parse(BATCH_SOURCE).body if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == declaration for target in node.targets))
            self.assertNotIn(PROFILE, ast.literal_eval(value))


if __name__ == "__main__":
    unittest.main()
