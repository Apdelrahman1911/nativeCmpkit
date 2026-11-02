"""New ARM64 failed-only source/collector guards; zero native or compiler executions."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import build_runtime_candidate as candidate
import probe_runner as probe
import run_library_candidate as runner

FOCUS = "webview-desktop-stop-linux-arm64-recovery"
CLASS = "com.mohamedrejeb.calf.ui.web.DesktopWebViewStopRedirectAcceptanceTest"
METHOD = "publicStopCancelsOneHeldNativeRequestBeforeAnyResponseAndRecoversOnTheSameOwner"


class Arm64CandidateTests(unittest.TestCase):
    def plan(self):
        return runner.focused_plan(runner.ROOT, FOCUS)

    def manifest(self):
        return {"passed": True, "classifier": "linux-aarch64", "identity": candidate.IDENTITY,
                "jar_sha256": "a" * 64}

    def collect(self, cases, *, stale=False, failure=False, extra_empty=False):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_directory = root / plan["expected"][0]["report_directory"]
            report_directory.mkdir(parents=True)
            suite = ET.Element("testsuite")
            for classname, name in cases:
                node = ET.SubElement(suite, "testcase", classname=classname, name=name)
                if failure:
                    ET.SubElement(node, "failure", message="explicit synthetic failure")
            report = report_directory / "TEST-synthetic.xml"
            report.write_bytes(ET.tostring(suite))
            now = time.time_ns()
            if stale:
                os.utime(report, ns=(now - 10_000_000_000, now - 10_000_000_000))
            if extra_empty:
                (report_directory / "TEST-empty.xml").write_bytes(b"<testsuite/>")
            return runner.library.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                Counter({":calf-webview:desktopTest": 1}), host_system="Linux")

    def test_exact_arm64_plan_excludes_both_accepted_methods_and_retains_one_original_xml(self):
        plan = self.plan()
        self.assertEqual(plan["explicit_test_focus"], FOCUS)
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(item["test_filter"], CLASS + "." + METHOD)
        self.assertEqual(item["required_testcases"], [{"classname": CLASS, "name": METHOD + "[desktop]"}])
        self.assertEqual(item["required_original_xml"], 1)
        self.assertNotIn(runner.library.WEBVIEW_DESKTOP_REQUEST_SOURCE, item["test_source_files"])

    def test_actual_linux_arm64_host_only_without_windows_or_x64_impersonation(self):
        for architecture in ("aarch64", "arm64"):
            runner.library.validate_webview_desktop_request_host("Linux", architecture, FOCUS)
            with patch.object(probe.platform, "system", return_value="Linux"), \
                    patch.object(probe.platform, "machine", return_value=architecture):
                self.assertEqual(probe.classifier(), "linux-aarch64")
        for system, architecture in (("Linux", "x86_64"), ("Windows", "AMD64"), ("Darwin", "arm64")):
            with self.subTest(system=system), self.assertRaises(ValueError):
                runner.library.validate_webview_desktop_request_host(system, architecture, FOCUS)

    def test_other_host_or_unknown_platform_refuses_before_compiler_lock_or_native_execution(self):
        with patch.object(probe, "classifier", return_value="linux"), \
                patch.object(candidate, "build") as build, patch.object(runner.os, "open") as lock:
            with self.assertRaisesRegex(ValueError, "explicitly selected Linux ARM64"):
                runner.run(argparse.Namespace(platform="linux-arm64", output="build/ci-verification/new", download=False))
        build.assert_not_called()
        lock.assert_not_called()
        with patch.object(probe, "classifier") as classify, self.assertRaisesRegex(ValueError, "Unknown explicit"):
            runner.run(argparse.Namespace(platform="linux-x64", output="build/ci-verification/new", download=False))
        classify.assert_not_called()

    def test_owned_display_exact_selector_classifier_and_serial_freshness_in_actual_command(self):
        with patch.object(runner.library.platform, "system", return_value="Linux"), \
                patch.object(runner.library.platform, "machine", return_value="aarch64"), \
                patch.object(runner.shutil, "which", return_value="/synthetic/owned-xvfb"):
            argv = runner.command(runner.ROOT, self.plan(), runner.ROOT / "build/ci-verification/new", self.manifest())
        self.assertEqual(argv[:2], ["/synthetic/owned-xvfb", "-a"])
        self.assertEqual(argv.count("--tests"), 1)
        self.assertEqual(argv[argv.index("--tests") + 1], CLASS + "." + METHOD)
        self.assertIn("-PnativecmpkitJavaFxCandidateClassifier=linux-aarch64", argv)
        for value in ("--max-workers=1", "--no-parallel", "--no-build-cache", "--no-configuration-cache"):
            self.assertIn(value, argv)
        self.assertFalse(any("useHTTP2Loader" in v or v == "--patch-module" for v in argv))

    def test_wrong_candidate_classifier_and_missing_owned_display_refuse(self):
        with patch.object(runner.library.platform, "system", return_value="Linux"), \
                patch.object(runner.library.platform, "machine", return_value="aarch64"):
            manifest = self.manifest()
            manifest["classifier"] = "win"
            with self.assertRaisesRegex(ValueError, "Invalid full-artifact"):
                runner.command(runner.ROOT, self.plan(), runner.ROOT / "build/ci-verification/new", manifest)
            with patch.object(runner.shutil, "which", return_value=None), self.assertRaisesRegex(ValueError, "owned Xvfb"):
                runner.command(runner.ROOT, self.plan(), runner.ROOT / "build/ci-verification/new", self.manifest())

    def test_missing_duplicate_mixed_empty_and_stale_xml_cannot_accept_native_stop(self):
        required = (CLASS, METHOD + "[desktop]")
        foreign = ("com.mohamedrejeb.calf.ui.web.DesktopWebViewRequestStateAcceptanceTest",
                   "twoHeldNativeTransportFailuresResetOldErrorsAndRecoverOnTheSameOwner[desktop]")
        for cases, options in (([], {}), ([required, required], {}), ([required, foreign], {}),
                               ([required], {"stale": True}), ([required], {"extra_empty": True})):
            with self.subTest(cases=cases, options=options):
                self.assertTrue(self.collect(cases, **options)["errors"])
        failed = self.collect([required], failure=True)
        self.assertEqual(failed["modules"][0]["failures"], 1)
        self.assertEqual(failed["modules"][0]["passed"], 0)

    def test_one_fresh_exact_synthetic_xml_is_structurally_admitted_not_native_evidence(self):
        result = self.collect([(CLASS, METHOD + "[desktop]")])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["modules"][0]["executed"], 1)
        self.assertEqual(result["modules"][0]["passed"], 1)

    def test_original_xml_count_and_unknown_focus_refuse_without_full_suite_fallback(self):
        for value in (0, 2, True, None):
            plan = copy.deepcopy(self.plan())
            plan["expected"][0]["required_original_xml"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner.library.validate_test_focus(plan)
        with self.assertRaisesRegex(ValueError, "Unknown failed-only"):
            runner.focused_plan(runner.ROOT, "all")

    def test_new_exact_registry_classifier_pins_preserve_all_original_linux_windows_and_java_sources(self):
        pins = probe.document((probe.HERE / "artifacts.json").read_bytes())
        self.assertEqual(set(pins["platforms"]), {"linux", "win", "linux-aarch64", "mac", "mac-aarch64"})
        for row in pins["platforms"]["linux-aarch64"]:
            probe.validate_row(row)
        self.assertEqual([r["file"] for r in pins["platforms"]["linux-aarch64"]],
                         [f"javafx-{module}-21.0.13-linux-aarch64.jar" for module in probe.MODULES])
        original = {**pins, "platforms": {k: v for k, v in pins["platforms"].items() if k in {"linux", "win"}}}
        canonical = json.dumps(original, indent=2, sort_keys=True) + "\n"
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), "493348d9d8106aa6a004b1a99484b62153e923039d844553fc16cfdf0d95b53d")
        self.assertFalse(pins["same_registry_checksums_are_independent_security_certification"])

    def test_packaging_target_is_explicit_and_unknown_target_refuses_before_any_output_or_compiler(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(probe, "classifier", return_value="linux"):
            output = Path(directory) / "candidate"
            with self.assertRaisesRegex(ValueError, "exact pinned packaging"):
                candidate.build(argparse.Namespace(output=output, target_classifier="mac-aarch32", artifact_dir=None, download=False))
            self.assertFalse(output.exists())
        source = (candidate.HERE / "build_runtime_candidate.py").read_text()
        self.assertIn('"cross_classifier_packaging_only": target != compiler_host', source)
        self.assertIn('"native_executions": 0', source)
        self.assertNotIn('os.environ["os.arch"]', source)

    def test_init_binds_real_arm64_daemon_one_exact_original_provider_and_no_route_override(self):
        source = (runner.ROOT / runner.INIT).read_text()
        self.assertIn('classifier == "linux-aarch64" && system == "Linux"', source)
        self.assertIn('architecture in setOf("aarch64", "arm64")', source)
        self.assertIn('"linux-aarch64" to "762e3bd7dfbabb418e65e3107e48fcfe7bd43437afeadd641855708f109503af"', source)
        self.assertIn('webProviders.size == 1 && webProviders.single().name == "javafx-web-21.0.13-$classifier.jar"', source)
        self.assertIn("originalFiles.filterNot { it == original } + candidate", source)
        self.assertIn("candidateDigest(original) == originalSha", source)
        self.assertIn("candidateDigest(candidate) == expected", source)
        self.assertIn("outputs.doNotCacheIf", source)
        self.assertNotIn('systemProperty("com.sun.webkit.useHTTP2Loader"', source)

    def test_push_classifier_extension_cannot_automatically_replay_accepted_native_populations(self):
        for workflow in (runner.WORKFLOW, ".github/workflows/javafx-dependency-regression.yml"):
            source = (runner.ROOT / workflow).read_text()
            self.assertIn("  push:\n    branches: [development/preview-hardening]", source)
            conditions = [line.strip() for line in source.splitlines() if line.startswith("    if:")]
            self.assertEqual(len(conditions), 1)
            self.assertIn("github.event_name == 'workflow_dispatch'", conditions[0])
            self.assertIn("permissions:\n  contents: read", source)
            self.assertNotIn("packages: write", source)
        source = (runner.ROOT / runner.WORKFLOW).read_text()
        self.assertIn("default: linux-arm64", source)
        self.assertIn("${{ env.CANDIDATE_SLOT }}-desktop-", source)
        self.assertNotIn("matrix:", source)
        self.assertNotIn("restore-keys:", source)
        self.assertNotIn("actions/cache/save", source)
        upload = source.split("name: Preserve verification receipts only", 1)[1]
        self.assertFalse(any(s in upload for s in ("*.jar", "*.class", "*.zip")))


if __name__ == "__main__":
    unittest.main()
