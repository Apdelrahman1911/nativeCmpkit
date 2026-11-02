"""Offline synthetic runner guards, not native execution or dependency trust."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import probe_runner as runner


class ProbeRunnerTests(unittest.TestCase):
    def row(self, payload=b"pinned fixture"):
        name = "javafx-base-21.0.13-win.jar"
        return {"file": name, "url": f"https://repo.maven.apache.org/maven2/org/openjfx/javafx-base/21.0.13/{name}",
                "bytes": len(payload), "sha256": runner.digest(payload)}

    def observations(self, kinds):
        values = []
        for kind in kinds:
            row = {"case": kind, "passed": True, "peerEofs": 1, "responseBytes": 0,
                   "cancellations": 1, "cleanupBeganBeforeEof": False, "sameEngineRecoveryRequests": 1,
                   "caseElapsedNanos": 100, "cancelToPeerNanos": 10, "parsedNativeTitle": False}
            if kind in ("plain-body", "gzip-body"):
                row.update(responseBytes=128, parsedNativeTitle=True)
            if kind == "concurrent":
                row.update(repeatedIdleCancels=3, independentRequestPassed=True, otherCancellations=0)
            values.append(row)
        values.append({"summary": True, "scenarioCount": len(kinds), "passed": len(kinds),
                       "libraryTests": 0, "privateRouteOverride": False})
        return values

    def stdout(self, rows):
        return "\n".join(json.dumps(value, separators=(",", ":")) for value in rows)

    def test_explicit_all_and_failed_only_selections(self):
        self.assertEqual(list(runner.CASES), runner.selection("all"))
        self.assertEqual(["gzip-body"], runner.selection("gzip-body"))
        self.assertEqual(["zero-header", "concurrent"], runner.selection("zero-header,concurrent"))

    def test_implicit_empty_unknown_and_duplicate_selections_refuse(self):
        for value in ("", "all,all", "unknown", "zero-header,zero-header", "zero-header,", " concurrent"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner.selection(value)

    def test_duplicate_json_and_nonfinite_values_refuse(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner.document(value)

    def test_exact_manifest_rows_validate(self):
        manifest = runner.document((runner.HERE / "artifacts.json").read_bytes())
        for row in [manifest["sources"], *manifest["platforms"]["linux"], *manifest["platforms"]["win"]]:
            runner.validate_row(row)

    def test_dependency_filename_escape_and_unpinned_version_refuse(self):
        for value in ("../javafx-base.jar", "javafx-base\\evil.jar", "javafx-base-20-win.jar", "javafx-base-21.0.13-mac-aarch32.jar"):
            row = self.row()
            row["file"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner.validate_row(row)

    def test_off_registry_http_and_extra_manifest_fields_refuse(self):
        for key, value in (("url", "https://example.invalid/javafx.jar"), ("url", self.row()["url"].replace("https:", "http:")), ("extra", 1)):
            row = self.row()
            row[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                runner.validate_row(row)

    def test_invalid_size_and_hash_refuse(self):
        for key, value in (("bytes", True), ("bytes", 0), ("bytes", runner.MAX_ARTIFACT + 1),
                           ("sha256", "F" * 64), ("sha256", "0" * 63)):
            row = self.row()
            row[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                runner.validate_row(row)

    def test_cached_exact_bytes_reuse_without_network(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(runner.urllib.request, "urlopen") as network:
            root = Path(directory)
            file = root / self.row()["file"]
            file.write_bytes(b"pinned fixture")
            self.assertEqual(file, runner.checked_artifact(root, self.row(), False))
            network.assert_not_called()

    def test_changed_cache_refuses_without_replacement_or_network(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(runner.urllib.request, "urlopen") as network:
            root = Path(directory)
            file = root / self.row()["file"]
            file.write_bytes(b"broken fixture")
            with self.assertRaises(ValueError):
                runner.checked_artifact(root, self.row(), True)
            self.assertEqual(b"broken fixture", file.read_bytes())
            network.assert_not_called()

    def test_missing_dependency_does_not_download_implicitly(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(runner.urllib.request, "urlopen") as network:
            with self.assertRaises(ValueError):
                runner.checked_artifact(Path(directory), self.row(), False)
            self.assertEqual([], list(Path(directory).iterdir()))
            network.assert_not_called()

    def test_dependency_symlink_refuses_without_following(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "foreign"
            target.write_bytes(b"pinned fixture")
            (root / self.row()["file"]).symlink_to(target)
            with self.assertRaises(ValueError):
                runner.checked_artifact(root, self.row(), False)
            self.assertEqual(b"pinned fixture", target.read_bytes())

    def test_unrecognized_upstream_source_never_patches(self):
        with self.assertRaises(ValueError):
            runner.patch_source(b"unknown source" + runner.BEFORE)

    def test_all_four_synthetic_native_rows_parse(self):
        rows = self.observations(runner.CASES)
        self.assertEqual(rows, runner.case_results("Unrelated platform warning\n" + self.stdout(rows), list(runner.CASES)))

    def test_missing_duplicate_and_wrong_order_native_rows_refuse(self):
        rows = self.observations(["zero-header", "concurrent"])
        for altered in (rows[:-1], [*rows[:1], *rows], [rows[1], rows[0], rows[2]]):
            with self.subTest(rows=altered), self.assertRaises(ValueError):
                runner.case_results(self.stdout(altered), ["zero-header", "concurrent"])

    def test_teardown_eof_and_missing_recovery_refuse(self):
        for key, value in (("peerEofs", 0), ("cleanupBeganBeforeEof", True), ("sameEngineRecoveryRequests", 0),
                           ("responseBytes", 1), ("cancellations", 2)):
            rows = self.observations(["zero-header"])
            rows[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.case_results(self.stdout(rows), ["zero-header"])

    def test_boolean_counters_and_invalid_clocks_refuse(self):
        for key, value in (("peerEofs", True), ("cancellations", True), ("sameEngineRecoveryRequests", True),
                           ("caseElapsedNanos", 0), ("cancelToPeerNanos", False)):
            rows = self.observations(["zero-header"])
            rows[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.case_results(self.stdout(rows), ["zero-header"])

    def test_unparsed_streaming_and_cross_request_cancellation_refuse(self):
        for kind, key, value in (("gzip-body", "parsedNativeTitle", False), ("plain-body", "responseBytes", 0),
                                  ("concurrent", "otherCancellations", 1), ("concurrent", "independentRequestPassed", False)):
            rows = self.observations([kind])
            rows[0][key] = value
            with self.subTest(kind=kind, key=key), self.assertRaises(ValueError):
                runner.case_results(self.stdout(rows), [kind])

    def test_fabricated_library_count_and_route_override_refuse(self):
        for key, value in (("libraryTests", 4), ("privateRouteOverride", True), ("passed", True)):
            rows = self.observations(["zero-header"])
            rows[-1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.case_results(self.stdout(rows), ["zero-header"])


class WorkflowSourceTests(unittest.TestCase):
    def source(self):
        return (runner.HERE.parents[2] / ".github/workflows/javafx-dependency-regression.yml").read_text()

    def test_only_read_permissions_and_development_branch(self):
        source = self.source()
        self.assertIn("permissions:\n  contents: read\n", source)
        self.assertNotIn(": write", source)
        self.assertIn("persist-credentials: false", source)
        self.assertIn("if: github.ref == 'refs/heads/development/preview-hardening'", source)
        self.assertNotIn("branches: [main]", source)

    def test_push_trigger_is_exact_probe_patch_and_manifest_only(self):
        source = self.source()
        section = source.split("    paths:\n", 1)[1].split("  workflow_dispatch:", 1)[0]
        self.assertEqual(["JavaFxPublicCancellationProbe.java", "cancel-response-future.patch", "artifacts.json"],
                         [line.strip().rsplit("/", 1)[1] for line in section.splitlines() if line.strip()])
        self.assertIn("inputs.platform == 'linux' && 'ubuntu-24.04' || 'windows-2025'", source)
        self.assertIn("SELECTED_CASES: ${{ inputs.cases || 'all' }}", source)

    def test_artifact_upload_never_contains_classes_jars_or_cached_tests(self):
        source = self.source()
        upload = source.split("          path: |\n", 1)[1]
        self.assertNotIn(".jar", upload)
        self.assertNotIn(".class", upload)
        self.assertNotIn("/**", upload)
        self.assertNotIn("actions/cache", source)
        self.assertIn("if-no-files-found: error", source)

    def test_public_worker_and_native_eof_not_private_routing_or_reflection(self):
        source = (runner.HERE / "JavaFxPublicCancellationProbe.java").read_text()
        self.assertIn('System.getProperty("com.sun.webkit.useHTTP2Loader") == null', source)
        self.assertIn("engine().getLoadWorker().cancel()", source)
        self.assertIn('require(value == -1, "Unexpected post-header request bytes")', source)
        self.assertIn("finished && eofs.get() == 1 && error.get() == null && !cleanup.get()", source)
        self.assertNotIn("java.lang.reflect", source)


class CheckoutRecoveryTests(unittest.TestCase):
    def test_byte_preservation_and_long_paths_precede_checkout(self):
        source = (runner.HERE.parents[2] / ".github/workflows/javafx-dependency-regression.yml").read_text()
        checkout = source.index("uses: actions/checkout@v4")
        self.assertLess(source.index("git config --global core.autocrlf false"), checkout)
        self.assertLess(source.index("git config --global core.longpaths true"), checkout)

    def test_sparse_checkout_keeps_exact_dependency_source_and_not_archived_xml(self):
        source = (runner.HERE.parents[2] / ".github/workflows/javafx-dependency-regression.yml").read_text()
        self.assertIn("sparse-checkout: tests/dependency/javafx-http2-cancellation", source)
        self.assertIn("sparse-checkout-cone-mode: true", source)
        self.assertNotIn("sparse-checkout: docs/", source)


if __name__ == "__main__":
    unittest.main()
