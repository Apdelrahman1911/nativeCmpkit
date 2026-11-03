# SPDX-License-Identifier: Apache-2.0
"""NEW shared-boundary qualification, no accepted method/native replay."""
import hashlib
import json
from pathlib import Path
import unittest

import ios_modal_ownership_source_projection as owning
import ios_modal_worker_source_projection as worker
import terminal_awt240_source_projection as terminal

ROOT = Path(__file__).resolve().parents[2]
HOST = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"


class SharedModalFixtureRecoveryControls(unittest.TestCase):
    def test_outer_worker_inverse_restores_formerly_unlisted_host_for_every_shared_historical_reader(self):
        current = (ROOT / HOST).read_bytes()
        expected = worker.current_source_before_modal_worker(HOST, current)
        self.assertEqual(expected, owning.source_before_modal_ownership(HOST, current))
        self.assertEqual(expected, owning.current_source_before_modal_ownership(HOST, current))
        self.assertEqual(expected, terminal.source_before_terminal_awt240(HOST, current))
        with self.assertRaises(ValueError): owning.current_source_before_modal_ownership(HOST, expected)
        with self.assertRaises(ValueError): terminal.source_before_terminal_awt240(HOST, current + b"\n")

    def test_pinned_original_alert_guard_is_unchanged_not_a_new_direct_worker_import_or_repin(self):
        relative = "scripts/ci/test_ui_alert_important_recovery.py"
        source = (ROOT / relative).read_bytes()
        bindings = json.loads(terminal.SPEC_PATH.read_bytes())["bindings"]
        self.assertEqual(bindings[relative]["after_sha256"], hashlib.sha256(source).hexdigest())
        self.assertNotIn(b"ios_modal_worker_source_projection", source)
        projected = terminal.source_before_terminal_awt240(relative, source)
        self.assertEqual(bindings[relative]["before_sha256"], hashlib.sha256(projected).hexdigest())
        self.assertEqual(projected, terminal.source_before_terminal_awt240(relative, projected))


if __name__ == "__main__":
    unittest.main()
