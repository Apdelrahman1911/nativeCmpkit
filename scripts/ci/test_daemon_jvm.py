"""Source-bound parser/command fixtures, not actual daemon or library test passes."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import daemon_jvm as d
import library_tests as r

FIXTURE = dict(schema_version=1, major=17, java_version="17.0.21", java_vendor="Eclipse Adoptium",
               runtime_version="17.0.21+9", gradle_version="9.7.1", launcher_home_configured=True,
               launcher_home_matches_daemon=True)


class DaemonJvmTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.log = Path(self.temp.name) / "gradle.log"

    def observe(self, value):
        self.log.write_text("unrelated build output\n" + d.PREFIX + json.dumps(value) + "\n")
        return d.observation(self.log)

    def test_exact_daemon_versions_vendors_and_correspondence_are_retained(self):
        for vendor in ("Eclipse Adoptium", "Debian", "JetBrains s.r.o."):
            value = dict(FIXTURE, java_vendor=vendor)
            self.assertEqual(value, self.observe(value))

    def test_missing_duplicate_oversized_or_invalid_json_marker_is_rejected(self):
        for text in ("", "java version 17\n", (d.PREFIX + json.dumps(FIXTURE) + "\n") * 2,
                     d.PREFIX + "x" * 4096 + "\n", d.PREFIX + "{not JSON}\n"):
            with self.subTest(text=text[:30]), self.assertRaises(ValueError):
                self.log.write_text(text)
                d.observation(self.log)

    def test_duplicate_json_keys_unknown_fields_and_nonobject_are_rejected(self):
        for value in (dict(FIXTURE, home="do not export"), [], "version17"):
            with self.assertRaises(ValueError):
                self.observe(value)
        self.log.write_text(d.PREFIX + json.dumps(FIXTURE)[:-1] + ', "major":17}\n')
        with self.assertRaises(ValueError):
            d.observation(self.log)

    def test_wrong_major_boolean_numeric_masquerade_and_empty_vendor_fail(self):
        for key, value in (("major", 21), ("major", True), ("schema_version", True),
                           ("java_vendor", ""), ("java_version", 17), ("runtime_version", "a\nb")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.observe(dict(FIXTURE, **{key: value}))

    def test_unconfigured_and_different_launcher_are_explicit_not_guessed(self):
        self.assertIsNone(self.observe(dict(FIXTURE, launcher_home_configured=False, launcher_home_matches_daemon=None))["launcher_home_matches_daemon"])
        self.assertFalse(self.observe(dict(FIXTURE, launcher_home_matches_daemon=False))["launcher_home_matches_daemon"])
        for configured, matches in ((False, False), (True, None), (True, 1), (1, True)):
            with self.assertRaises(ValueError):
                self.observe(dict(FIXTURE, launcher_home_configured=configured, launcher_home_matches_daemon=matches))

    def test_all_real_suite_commands_include_one_actual_root_daemon_init(self):
        for suite in r.SUITES:
            plan = {"suite": suite, "expected": [{"task": ":calf-fixture:" + r.SUITES[suite][0]}]}
            kwargs = {"simulator": "11111111-1111-1111-1111-111111111111"} if suite == "ios" else {}
            if suite == "android-device": kwargs["android_serial"] = "emulator-5588"
            command = r.gradle_command(suite, plan, **kwargs)
            self.assertEqual(1, command.count("scripts/ci/daemon-jvm.init.gradle.kts"))

    def test_real_init_and_collector_do_not_export_private_home_or_environment(self):
        source = (r.ROOT / "scripts/ci/daemon-jvm.init.gradle.kts").read_text()
        self.assertIn('rootProject.name == "NativeCmpKit"', source)
        self.assertIn("Runtime.version().feature()", source)
        self.assertIn("Files.isSameFile", source)
        self.assertNotIn('daemonJsonString(System.getProperty("java.home"))', source)
        self.assertNotIn("System.getenv()", source)
        source = (r.ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertIn('receipt["gradle_daemon"] = daemon_jvm.observation', source)
        self.assertIn('"Actual root-daemon observation rejected"', source)


if __name__ == "__main__":
    unittest.main()
