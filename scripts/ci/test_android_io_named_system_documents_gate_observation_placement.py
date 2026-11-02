from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import android_io_named_system_documents as source
import android_io_named_system_documents_gate_observations as gate
from android_io_named_gate_details import detail_preimage
from android_io_named_button_rendering import rendering_preimage

# One genuinely NEW owning relocation-negative obligation; no historical control imports/replay.
BASE_UI_SHA256 = '1e71a260b1bf501f3f5b7a6121f7cf7dfcc2e6d274cd2733f2f516f8aea5b19f'
AUTHORED_UI_SHA256 = '3f7288affcc1e52b8262a7c3c07fabeb2941c40fff36aa1c456ffd34419ece6e'
OWNED_ROW_CLOSING = '        } // End OWNED_FOLDER_ROW failure-only scope; original native body is unchanged.\n'
TOOLBAR_OBSERVATION = '        observe({ root -> textIn(root, resource("toolbar"), folder) }) {\n            it.text?.toString() == folder\n        }\n'


class NamedSystemIoGateObservationPlacementNewControl(unittest.TestCase):
    def test_new_relocated_row_closing_cannot_label_toolbar_timeout_as_owned_row(self):
        staged = Path(__file__).resolve().parents[2]
        authored = (staged / source.UI).read_text()
        self.assertEqual(AUTHORED_UI_SHA256, hashlib.sha256(detail_preimage(authored).encode()).hexdigest())
        self.assertEqual(1, authored.count(OWNED_ROW_CLOSING))
        self.assertEqual(1, authored.count(TOOLBAR_OBSERVATION))
        moved = authored.replace(OWNED_ROW_CLOSING, "", 1)
        moved = moved.replace(TOOLBAR_OBSERVATION, TOOLBAR_OBSERVATION + OWNED_ROW_CLOSING, 1)
        self.assertNotEqual(authored, moved)

        # This new witness explains why independent marker removal was insufficient:
        # its passive text inverse is still the held native UI, with no native relaxation.
        inverse = rendering_preimage(moved)
        for addition in gate.GATE_FAILURE_ADDITIONS:
            self.assertEqual(1, inverse.count(addition))
            inverse = inverse.replace(addition, "", 1)
        self.assertEqual(1, inverse.count(gate.GATE_FAILURE_ERROR_AFTER))
        inverse = inverse.replace(gate.GATE_FAILURE_ERROR_AFTER, gate.GATE_FAILURE_ERROR_BEFORE, 1)
        self.assertEqual(BASE_UI_SHA256, hashlib.sha256(inverse.encode()).hexdigest())
        self.assertEqual(1, inverse.count(gate.ORIGINAL_FIND_SOURCE))
        self.assertEqual(gate.gate_observation_preimage(authored), inverse)

        for reject in (gate.gate_observation_preimage, source.resource_admission_preimage):
            with self.subTest(boundary=reject.__name__):
                with self.assertRaisesRegex(ValueError, "^" + re.escape(gate.OBSERVATION_REFUSAL) + "$"):
                    reject(moved)

        with tempfile.TemporaryDirectory(prefix="nativecmpkit-gate-placement-NEW-") as temporary:
            root = Path(temporary)
            for relative in source.SOURCE_FILES:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(staged / relative, target)
            (root / source.UI).write_text(moved)
            with self.assertRaisesRegex(ValueError, "^" + re.escape(gate.OBSERVATION_REFUSAL) + "$"):
                source.source_contract(root)


if __name__ == "__main__":
    unittest.main()
