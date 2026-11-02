"""Focused status-index portability controls; no native/library executions.

Windows relative paths use genuine PureWindowsPath semantics. Folder views are
controlled; whole-index comparisons read/write real isolated fixture bytes.
These tests are not actual Windows filesystem or hosted workflow acceptance.
"""
from __future__ import annotations

from pathlib import Path, PureWindowsPath
import tempfile
import unittest
from unittest import mock

import test_validate_resolutions as fixtures
import validate_resolutions as validator


DISCOVER = validator.discover


def windows_discovery(real_root: Path) -> dict[str, list[str]]:
    """Use actual Windows relative-path rendering with real fixture inventory."""
    windows_root = PureWindowsPath("C:/NativeCmpKit")

    class Folder:
        def __init__(self, path: Path):
            self.path = path

        def is_dir(self):
            return self.path.is_dir()

        def glob(self, pattern):
            return [windows_root / p.relative_to(real_root).as_posix()
                    for p in self.path.glob(pattern)]

    def view(_root, relative):
        # Controlled path view only; production containment is not replaced.
        local = real_root / relative.replace("\\", "/")
        if relative in (validator.FINDING_DIR, validator.LEDGER_DIR):
            return Folder(local)
        return local

    with mock.patch.object(validator, "inside_root", side_effect=view):
        return DISCOVER(windows_root)


class StatusIndexPathPortabilityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-path-portability-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative, data in fixtures.fixtures().items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(validator.canonical(data))

    def test_windows_discovery_keys_equal_posix_inventory_without_backslashes(self):
        expected = DISCOVER(self.root)
        actual = windows_discovery(self.root)
        self.assertEqual(expected, actual)
        self.assertTrue(all("\\" not in p for group in actual.values() for p in group))
        self.assertIn(fixtures.FINDINGS, actual["findings"])
        self.assertIn(fixtures.LEDGER, actual["ledgers"])

    def test_identical_fixture_bytes_produce_identical_windows_and_posix_outputs(self):
        expected = validator.build_snapshot(self.root, expected_count=3)
        with mock.patch.object(validator, "discover", side_effect=windows_discovery):
            actual = validator.build_snapshot(self.root, expected_count=3)
            self.assertEqual(expected, actual)
            self.assertEqual(validator.rendered_outputs(expected), validator.rendered_outputs(actual))
            validator.write_outputs(self.root, actual)
            self.assertEqual([], validator.check_outputs(self.root, actual))
        self.assertNotIn(b"%5C", validator.render_markdown(actual))
        self.assertEqual(0, actual["counts"]["automatic_closures"])
        self.assertEqual(0, actual["counts"]["status_promotions"])

    def test_windows_normalization_does_not_waive_ledger_or_index_staleness(self):
        with mock.patch.object(validator, "discover", side_effect=windows_discovery):
            original = validator.build_snapshot(self.root, expected_count=3)
            validator.write_outputs(self.root, original)
            ledger = self.root / fixtures.LEDGER
            ledger.write_bytes(ledger.read_bytes() + b"\n")
            changed = validator.build_snapshot(self.root, expected_count=3)
            self.assertNotEqual(original["input_fingerprint"], changed["input_fingerprint"])
            self.assertEqual([validator.OUTPUT_JSON, validator.OUTPUT_MD],
                             validator.check_outputs(self.root, changed))
            with self.assertRaises(validator.StaleSnapshotError):
                validator.assert_inputs_current(self.root, original)

    def test_candidate_workflow_records_preflight_failures_before_native_execution(self):
        root = Path(__file__).resolve().parents[2]
        text = (root / ".github/workflows/javafx-library-candidate.yml").read_text()
        step = text.split("name: Select official SDK23 and current held source plan", 1)[1]
        step = step.split("      - name: Exact configured", 1)[0]
        self.assertLess(step.index("mkdir -p build/ci-runtime"), step.index("python -B - <<'PY'"))
        self.assertIn("javafx-candidate-sdk.json", step)
        self.assertIn("| tee build/ci-runtime/javafx-candidate-index-check.log", step)
        self.assertIn("build/ci-runtime/javafx-candidate-*.log", text)
        self.assertNotIn("validate_resolutions.py --write", text)
        self.assertNotIn("continue-on-error", text)


if __name__ == "__main__":
    unittest.main()
