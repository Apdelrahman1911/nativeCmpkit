# SPDX-License-Identifier: Apache-2.0
"""NEW shared reader regressions; no accepted/native/control-method replay."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import android_external328_source_projection as external
import ios_modal_fixture_reader_projection as history
import ios_modal_worker_source_projection as worker
import terminal_awt240_source_projection as terminal

ROOT = Path(__file__).resolve().parents[2]
ALERT = "scripts/ci/test_ui_alert_container_timeout_observation.py"


class ModalFixtureReaderRecoveryControls(unittest.TestCase):
    def test_exact_single_fixture_inverse_keeps_the_live_host_comparison_and_every_old_pin(self):
        bindings = history._bindings()
        self.assertEqual({ALERT}, set(bindings))
        binding = bindings[ALERT]
        self.assertEqual(1, len(binding["fragments"]))
        current = (ROOT / ALERT).read_bytes()
        previous = history.current_source_before_worker_fixture_reader(ALERT, current)
        self.assertEqual("6de5af63c8de7327bb1dbb85f6a44011b993f381b002fc2ef030a1d8467a2fa0",
                         hashlib.sha256(previous).hexdigest())
        self.assertEqual(binding["after_sha256"], hashlib.sha256(current).hexdigest())
        forward = previous
        for fragment in binding["fragments"]:
            before, after = fragment["before"].encode(), fragment["after"].encode()
            self.assertEqual(1, forward.count(before))
            forward = forward.replace(before, after, 1)
        self.assertEqual(current, forward)
        self.assertIn(b"prior_host = current_source_before_modal_worker", current)
        self.assertNotIn(b"prior_host = current_source_before_modal_worker", previous)
        self.assertEqual(previous, history.source_before_worker_fixture_reader(ALERT, previous))
        with self.assertRaisesRegex(ValueError, "exact current"):
            history.current_source_before_worker_fixture_reader(ALERT, previous)

    def test_all_shared_readers_admit_actual_bytes_then_restore_the_original_control_without_running_old_bodies(self):
        current = (ROOT / ALERT).read_bytes()
        previous = history.current_source_before_worker_fixture_reader(ALERT, current)
        for reader in (worker.source_before_modal_worker, worker.current_source_before_modal_worker,
                       external.source_before_android_external328, external.current_source_for_history,
                       terminal.source_before_terminal_awt240):
            self.assertEqual(previous, reader(ALERT, current))
        from test_ci224_shared_source_composition import CI224SharedSourceCompositionTests
        CI224SharedSourceCompositionTests.setUpClass()
        self.assertEqual(previous, CI224SharedSourceCompositionTests.payloads[ALERT])
        CI224SharedSourceCompositionTests.tearDownClass()
        for path, expected in (
                ("scripts/ci/terminal_awt240_source_projection.py", "b7ce5b0cd5ce960371a32ab138eeeb627291ee947e1b602b76fba913fd5791c9"),
                ("scripts/ci/fixtures/terminal-awt240-source-inverse.json", "57aea63782e79cf6bce95c4d443c73bceaf2c7a4e1a4d74d963bbb82e7eb69b2"),
                ("scripts/ci/fixtures/ios-modal-worker-source-inverse.json", "8a1f2c4b0f418b9aab96f9d3c8f615acff5efce31fe457886204559fd2448d48")):
            self.assertEqual(expected, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

    def test_old_changed_partial_wrong_type_or_untrusted_manifest_cannot_replace_current_custody(self):
        current = (ROOT / ALERT).read_bytes()
        previous = history.source_before_worker_fixture_reader(ALERT, current)
        for payload in (previous, current + b"\n", current[:-1], current.replace(b"\n", b"\r\n"),
                        b"", b"foreign", None, bytearray(current), current.decode()):
            with self.subTest(kind=type(payload).__name__):
                for reader in (history.current_source_before_worker_fixture_reader,
                               worker.current_source_before_modal_worker, external.current_source_for_history):
                    with self.assertRaises(ValueError): reader(ALERT, payload)
        with self.assertRaises(ValueError):
            history.source_before_worker_fixture_reader(ALERT, b"x" * (history.MAX_SOURCE_BYTES + 1))
        unrelated = b"explicit unrelated inert control"
        self.assertIs(unrelated, history.source_before_worker_fixture_reader("unlisted", unrelated))
        with tempfile.TemporaryDirectory(prefix="explicitly-synthetic-worker-fixture-manifest-") as folder:
            changed = Path(folder) / "changed.json"
            changed.write_bytes(history.SPEC_PATH.read_bytes() + b"\n")
            with patch.object(history, "SPEC_PATH", changed), self.assertRaisesRegex(ValueError, "manifest changed"):
                history._bindings()
            link = Path(folder) / "linked.json"
            link.symlink_to(changed)
            with patch.object(history, "SPEC_PATH", link), self.assertRaisesRegex(ValueError, "ordinary"):
                history._bindings()


if __name__ == "__main__":
    unittest.main()
