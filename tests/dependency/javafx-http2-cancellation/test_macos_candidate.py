"""New failed-only macOS source/command/pin checks; zero Apple/native executions."""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

import build_runtime_candidate as candidate
import probe_runner as probe
import run_library_candidate as runner

FOCUS = "webview-desktop-stop-macos-recovery"


class MacOsCandidateTests(unittest.TestCase):
    def test_both_real_mac_architectures_select_only_failed_original_stop_not_accepted_request(self):
        for architecture, classifier in (("x86_64", "mac"), ("arm64", "mac-aarch64")):
            with self.subTest(architecture=architecture), patch.object(probe.platform, "system", return_value="Darwin"), \
                    patch.object(probe.platform, "machine", return_value=architecture):
                self.assertEqual(probe.classifier(), classifier)
                runner.library.validate_webview_desktop_request_host("Darwin", architecture, FOCUS)
                plan = runner.focused_plan(runner.ROOT, FOCUS)
                self.assertEqual(plan["expected"][0]["test_filter"], runner.SELECTOR)
                self.assertEqual(len(plan["expected"][0]["required_testcases"]), 1)
                self.assertEqual(plan["expected"][0]["required_original_xml"], 1)
                self.assertNotIn(runner.library.WEBVIEW_DESKTOP_REQUEST_SOURCE, plan["expected"][0]["test_source_files"])
                manifest = {"passed": True, "classifier": classifier, "identity": candidate.IDENTITY, "jar_sha256": "a" * 64}
                argv = runner.command(runner.ROOT, plan, runner.ROOT / "build/ci-verification/new", manifest)
                self.assertEqual(argv[0], "./gradlew")
                self.assertEqual(argv.count("--tests"), 1)
                self.assertEqual(argv[argv.index("--tests") + 1], runner.SELECTOR)
                self.assertIn("-PnativecmpkitJavaFxCandidateClassifier=" + classifier, argv)
                self.assertFalse(any("xvfb" in value or "useHTTP2Loader" in value or value == "--patch-module" for value in argv))

    def test_other_os_unknown_architecture_and_cross_mac_classifier_cannot_impersonate_native_host(self):
        for system, architecture in (("Linux", "aarch64"), ("Windows", "AMD64"), ("Darwin", "ppc64")):
            with self.subTest(system=system), self.assertRaises(ValueError):
                runner.library.validate_webview_desktop_request_host(system, architecture, FOCUS)
        with patch.object(probe.platform, "system", return_value="Darwin"), \
                patch.object(probe.platform, "machine", return_value="arm64"):
            manifest = {"passed": True, "classifier": "mac", "identity": candidate.IDENTITY, "jar_sha256": "a" * 64}
            with self.assertRaisesRegex(ValueError, "match the actual native host"):
                runner.command(runner.ROOT, runner.focused_plan(runner.ROOT, FOCUS),
                               runner.ROOT / "build/ci-verification/new", manifest)

    def test_ten_new_fixed_mac_registry_pins_and_daemon_original_digest_checks_are_exact(self):
        pins = json.loads((probe.HERE / "artifacts.json").read_text())
        init = (runner.ROOT / runner.INIT).read_text()
        for classifier in ("mac", "mac-aarch64"):
            rows = pins["platforms"][classifier]
            self.assertEqual([r["file"] for r in rows], [f"javafx-{module}-21.0.13-{classifier}.jar" for module in probe.MODULES])
            for row in rows:
                probe.validate_row(row)
                wrong = {**row, "url": row["url"].replace("repo.maven.apache.org", "example.invalid")}
                with self.assertRaises(ValueError):
                    probe.validate_row(wrong)
            self.assertIn('"' + classifier + '" to "' + rows[-1]["sha256"] + '"', init)
            self.assertIn('classifier == "' + classifier + '" && system.startsWith("Mac")', init)
        self.assertIn("candidateDigest(original) == originalSha", init)
        self.assertIn("originalFiles.filterNot { it == original } + candidate", init)

    def test_exact_single_xml_requirement_and_wrong_focus_or_manifest_still_refuse(self):
        plan = runner.focused_plan(runner.ROOT, FOCUS)
        for count in (True, 0, 2, None):
            wrong = copy.deepcopy(plan)
            wrong["expected"][0]["required_original_xml"] = count
            with self.assertRaises(ValueError):
                runner.library.validate_test_focus(wrong)
        with patch.object(probe.platform, "system", return_value="Darwin"), \
                patch.object(probe.platform, "machine", return_value="x86_64"):
            manifest = {"passed": True, "classifier": "win", "identity": candidate.IDENTITY, "jar_sha256": "a" * 64}
            with self.assertRaisesRegex(ValueError, "Invalid full-artifact"):
                runner.command(runner.ROOT, plan, runner.ROOT / "build/ci-verification/new", manifest)

    def test_platform_workflow_is_manual_single_reservation_arch_cache_bound_and_distinct_concurrency(self):
        source = (runner.ROOT / runner.WORKFLOW).read_text()
        self.assertIn("options: [linux-arm64, macos-arm64, macos-x64, windows]", source)
        self.assertIn("github.event_name == 'workflow_dispatch'", source)
        self.assertIn("inputs.platform == 'macos-arm64' && 'macos-26'", source)
        self.assertIn("inputs.platform == 'macos-x64' && 'macos-26-intel'", source)
        self.assertIn("${{ github.ref }}-${{ inputs.platform || 'windows' }}", source)
        self.assertIn("${{ env.CANDIDATE_SLOT }}-desktop-", source)
        self.assertNotIn("matrix:", source)
        self.assertNotIn("packages: write", source)
        self.assertNotIn("id-token:", source)
        self.assertNotIn("restore-keys:", source)
        self.assertNotIn("actions/cache/save", source)
        self.assertIn("--platform \"$CANDIDATE_PLATFORM\"", source)


if __name__ == "__main__":
    unittest.main()
