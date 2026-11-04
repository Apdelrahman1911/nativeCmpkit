"""SDK request/abort fixtures; zero Gradle, platform or library executions.

Exercise the real runner's preparation and cleanup with an explicit stop at
runtime capture. Do not invent an SDK/runtime receipt or a passing test report.
"""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import library_tests as runner


class CaptureStopped(Exception):
    pass


class LibrarySdkContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.write("settings.gradle.kts", 'include(\n    ":calf-fixture",\n)\n')
        self.write("calf-fixture/build.gradle.kts", "// synthetic configured project\n")
        for source_set in ("commonTest", "androidDeviceTest"):
            self.write(f"calf-fixture/src/{source_set}/kotlin/Fixture.kt", "// synthetic authored input\n")

    def write(self, relative, content):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return target

    def stop_at_capture(self, suite, error):
        simulator = "11111111-1111-1111-1111-111111111111" if suite == "ios" else None
        serial = "emulator-5588" if suite == "android-device" else None
        output = f"build/ci-verification/{suite}"
        with ExitStack() as stack:
            stack.enter_context(patch.dict(runner.MINIMUM_MODULES, {suite: ("calf-fixture",)}))
            stack.enter_context(patch.object(runner, "git_revision", return_value="a" * 40))
            capture = stack.enter_context(patch.object(runner.runtime_context, "capture", side_effect=error))
            execute = stack.enter_context(patch.object(runner, "execute"))
            quarantine = stack.enter_context(patch.object(runner, "quarantine_reports"))
            with self.assertRaises(type(error)) as stopped:
                # This generic SDK fixture owns no Camera callback source. Keep
                # Android explicitly non-Camera instead of requesting the real
                # enabled callback through unrestricted aggregate discovery.
                runner.run(self.root, suite, output, simulator, 60, 1024,
                           only_modules=("calf-fixture",) if suite == "android-device" else None,
                           android_serial=serial)
            self.assertIs(stopped.exception, error)
            execute.assert_not_called()
            quarantine.assert_not_called()
        self.assertFalse((self.root / "build/ci-verification/.library-tests.lock").exists())
        self.assertFalse((self.root / output / "receipt.json").exists())
        return capture, simulator, serial

    def test_every_configured_suite_requests_the_same_official_sdk_as_setup(self):
        for suite in runner.SUITES:
            with self.subTest(suite=suite):
                capture, simulator, serial = self.stop_at_capture(suite, CaptureStopped("observed request"))
                capture.assert_called_once_with(
                    apple=suite == "ios", device=simulator, require_booted=suite == "ios",
                    android_package="android-37.0", android_serial=serial,
                    browser=suite in {"js", "wasm"},
                )

    def test_unavailable_sdk_capture_stops_before_gradle_or_report_quarantine_and_releases_lock(self):
        for suite in runner.SUITES:
            with self.subTest(suite=suite):
                report = self.write(
                    f"calf-fixture/build/test-results/{runner.SUITES[suite][0]}/TEST-prior.xml",
                    "preserve prior evidence; not a fresh report",
                )
                before = report.read_bytes()
                self.stop_at_capture(suite, ValueError("Configured SDK metadata is unavailable"))
                self.assertEqual(before, report.read_bytes())

    def test_unrestricted_android_callback_admission_precedes_sdk_capture_and_host_work(self):
        error = ValueError("Configured SDK metadata is unavailable")
        message = ("Enabled API35-only callback requires exact finite Camera selection; "
                   "unrestricted Camera/all discovery refuses before host work")
        for modules in (None, (), (runner.camera_callback.MODULE,),
                        (runner.camera_callback.MODULE, "calf-fixture")):
            with self.subTest(modules=modules), ExitStack() as stack:
                stack.enter_context(patch.dict(runner.MINIMUM_MODULES,
                                               {"android-device": ("calf-fixture",)}))
                projects = stack.enter_context(patch.object(runner, "projects"))
                command = stack.enter_context(patch.object(runner, "gradle_command"))
                revision = stack.enter_context(patch.object(runner, "git_revision"))
                inputs = stack.enter_context(patch.object(runner, "snapshot_inputs"))
                capture = stack.enter_context(patch.object(runner.runtime_context, "capture", side_effect=error))
                execute = stack.enter_context(patch.object(runner, "execute"))
                quarantine = stack.enter_context(patch.object(runner, "quarantine_reports"))
                with self.assertRaisesRegex(ValueError, "^" + message + "$") as stopped:
                    runner.run(self.root, "android-device", "build/ci-verification/refused-sdk",
                               None, 60, 1024, only_modules=modules, android_serial="emulator-5588")
                self.assertIsNot(stopped.exception, error)
                for operation in (projects, command, revision, inputs, capture, execute, quarantine):
                    operation.assert_not_called()
            self.assertFalse((self.root / "build").exists())
            self.assertFalse((self.root / runner.camera_callback.SOURCE).exists())

    def test_explicit_non_camera_android_fixture_reaches_sdk_abort_after_owned_lock_without_native_execution(self):
        output = self.root / "build/ci-verification/explicit-sdk-fixture"
        lock = self.root / "build/ci-verification/.library-tests.lock"
        report = self.write(
            "calf-fixture/build/test-results/connectedAndroidDeviceTest/TEST-prior.xml",
            "preserve prior evidence; not a fresh report",
        )
        before = report.read_bytes()
        error = ValueError("Configured SDK metadata is unavailable")

        def stop(**context):
            self.assertTrue(lock.is_file())
            plan = json.loads((output / "plan.json").read_text())
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(["calf-fixture"], plan["explicit_module_subset"])
            self.assertEqual(["calf-fixture"], [item["module"] for item in plan["expected"]])
            self.assertNotIn("explicit_test_focus", plan)
            self.assertNotIn(runner.camera_callback.CONTRACT_KEY, plan["expected"][0])
            inputs = json.loads((output / "inputs-before.json").read_text())
            self.assertEqual({
                "settings.gradle.kts", "calf-fixture/build.gradle.kts",
                "calf-fixture/src/commonTest/kotlin/Fixture.kt",
                "calf-fixture/src/androidDeviceTest/kotlin/Fixture.kt",
            }, set(inputs))
            self.assertEqual(before, report.read_bytes())
            self.assertFalse((output / "receipt.json").exists())
            raise error

        with ExitStack() as stack:
            stack.enter_context(patch.dict(runner.MINIMUM_MODULES, {"android-device": ("calf-fixture",)}))
            stack.enter_context(patch.object(runner, "git_revision", return_value="a" * 40))
            discovery = stack.enter_context(patch.object(
                runner.camera_callback, "validate_discovery", wraps=runner.camera_callback.validate_discovery))
            capture = stack.enter_context(patch.object(runner.runtime_context, "capture", side_effect=stop))
            execute = stack.enter_context(patch.object(runner, "execute"))
            quarantine = stack.enter_context(patch.object(runner, "quarantine_reports"))
            with self.assertRaises(ValueError) as stopped:
                runner.run(self.root, "android-device", output.relative_to(self.root).as_posix(),
                           None, 60, 1024, only_modules=("calf-fixture",), android_serial="emulator-5588")
            self.assertIs(stopped.exception, error)
            capture.assert_called_once_with(
                apple=False, device=None, require_booted=False, android_package="android-37.0",
                android_serial="emulator-5588", browser=False,
            )
            args = ("android-device", ("calf-fixture",), None, runner.ANDROID_CAMERA_FOCUSES)
            self.assertEqual([
                (args, {}), (args, {"declared_modules": ("calf-fixture",), "minimum_modules": None}),
            ], [(entry.args, entry.kwargs) for entry in discovery.call_args_list])
            execute.assert_not_called()
            quarantine.assert_not_called()
        self.assertFalse(lock.exists())
        self.assertFalse((output / "receipt.json").exists())
        self.assertEqual(before, report.read_bytes())

    def test_workflow_library_and_consumer_setup_keep_the_exact_official_package(self):
        workflow = (runner.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn(
            'args=(--expected-arch "$EXPECTED_ARCH" --require-clean --android-platform android-37.0)',
            workflow,
        )
        self.assertIn(
            "runtime_context.py --expected-arch x64 --require-clean --android-platform android-37.0",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
