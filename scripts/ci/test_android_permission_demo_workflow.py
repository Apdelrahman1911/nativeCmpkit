"""New finite source/SDK/preparation models only. No real build, emulator, installation or CI dispatch."""
from pathlib import Path
import re
import tempfile
import unittest

import android_device_tests as device
import android_permission_demo as demo
import library_tests as lt
import workflow_matrix as workflow

ROOT = Path(__file__).resolve().parents[2]


class AndroidPermissionDemoWorkflowTest(unittest.TestCase):
    def test_workflow_provisions_only_the_exact_new_profile_api_and_explicit_actual_signer(self):
        source = (ROOT / ".github/workflows/gradle.yml").read_text()
        for profile, api in (("android-permission-demo", 35), ("android-media-selection-api33", 33), ("android-media-selection-api34", 34)):
            branches = re.findall(r"inputs\.profile == '" + profile + r"' && '([^']+)'", source)
            self.assertEqual([f"cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-{api};google_apis;x86_64"], branches)
        self.assertIn('args=(--api-level "$EMULATOR_API" --output "build/ci-verification/$SLOT")', source)
        self.assertIn('"$PYTHON" scripts/ci/android_device_tests.py "${args[@]}"', source)
        choices = re.search(r"options: \[([^\n]+)\]", source).group(1)
        self.assertEqual(set(workflow.PROFILES), {value.strip() for value in choices.split(',')})

    def test_each_new_profile_passes_the_actual_readonly_python_cli_without_creating_a_build_output(self):
        output = ROOT / "build/ci-plan"
        def snapshot():
            return sorted((str(path.relative_to(output)), path.stat().st_size, path.stat().st_mtime_ns)
                for path in output.rglob('*') if path.is_file()) if output.exists() else None
        before = snapshot()
        for profile in ("android-permission-demo", "android-media-selection-api33", "android-media-selection-api34"):
            receipt = workflow.preflight_plans(profile, root=ROOT)
            self.assertIs(receipt["source_only"], True)
            self.assertEqual(0, receipt["Gradle_builds_executed"])
            self.assertEqual(0, receipt["library_tests_executed"])
            self.assertEqual(1, len(receipt["slots"]))
            selection = receipt["slots"][0]
            self.assertEqual(0, selection["exit_code"])
            self.assertIn("plan", selection["command"])
            self.assertNotIn("run", selection["command"])
            self.assertEqual(1, selection["expected_modules"])
        self.assertEqual(before, snapshot())

    def test_new_sdk_source_models_preserve_api_abi_and_tag_exactness_without_runtime_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            emulator = root / "emulator/source.properties"
            emulator.parent.mkdir(parents=True)
            emulator.write_text("Pkg.Revision=36.2.12\n")
            for path in ("platform-tools/adb", "emulator/emulator", "cmdline-tools/23.0/bin/avdmanager"):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("synthetic inert SDK path; never executed\n")
                target.chmod(0o700)
            for api in (33, 34):
                path = root / f"system-images/android-{api}/google_apis/x86_64/source.properties"
                path.parent.mkdir(parents=True)
                original = f"AndroidVersion.ApiLevel={api}\nSystemImage.Abi=x86_64\nSystemImage.TagId=google_apis\nPkg.Revision=9\n"
                path.write_text(original)
                assets = device.sdk_assets(root, api_level=api)
                self.assertEqual(f"system-images;android-{api};google_apis;x86_64", assets["system_image"])
                for old, new in ((f"ApiLevel={api}", "ApiLevel=35"), ("Abi=x86_64", "Abi=arm64-v8a"), ("TagId=google_apis", "TagId=default")):
                    path.write_text(original.replace(old, new))
                    with self.subTest(api=api, new=new), self.assertRaises(ValueError):
                        device.sdk_assets(root, api_level=api)
                path.write_text(original)

    def test_fresh_install_source_pins_no_autogrant_or_replace_and_deferred_reporter_obligations(self):
        source = (ROOT / "scripts/ci/android_permission_demo.py").read_text()
        self.assertIn('install = self.control("install", "-t", str(apk), timeout=120)', source)
        self.assertNotIn('self.control("install", "-g"', source)
        self.assertNotIn('self.control("install", "-r"', source)
        prepared = source.split("def prepare(self)", 1)[1].split("def close(self)", 1)[0]
        self.assertLess(prepared.index("self.inspectors()"), prepared.index("lt.execute("))
        self.assertLess(prepared.index("self.readback() is None"), prepared.index("lt.execute("))
        self.assertLess(prepared.index("apk_policy=self.inspect_apk(apk)"), prepared.index("install_attempted = True"))
        self.assertIn("Source/APK changed during inspection", prepared)
        controller = (ROOT / "scripts/ci/android_device_tests.py").read_text()
        block = controller.split("if permission_demo_required:\n            permission_demo =", 1)[1].split("if focus == lt.WEBVIEW_ANDROID_MEDIA_FOCUS:", 1)[0]
        self.assertLess(block.index("permission_demo.prepare()"), block.index('output / "apk-assembly.log"'))
        self.assertIn('"reporter_compile_deferred_until_permission_demo_identity"', controller)
        self.assertIn("permission_demo.close()", controller)
        self.assertIn('result["permission_demo"].get("owned_recipient_removed") is True', controller)
        self.assertTrue(demo.source_contract(ROOT)["source_policy_verified"])


if __name__ == "__main__":
    unittest.main()
