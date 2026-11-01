"""One new static parser guard on held, pre-existing local compiled XML.

No compile/SDK/APK process/install/native invocation. These are not JUnit results.
"""
from pathlib import Path
import hashlib
import json
import unittest

import android_storage_probe as s
import android_storage_compatibility_plan as storage

HERE = Path(__file__).resolve().parent


class ExistingCompiledStorageParserRecoveryModel(unittest.TestCase):
    def test_six_existing_compiled_manifest_snapshots_match_owning_parser(self):
        observed = json.loads((HERE / 'local-compiled-source-observation.json').read_bytes())
        by_flavor = {row['flavor']: row for row in observed['local_manifests']}
        for row in storage.ROWS[:6]:
            with self.subTest(profile=row.profile):
                payload = (HERE / 'existing-local-manifests' / (row.flavor + '.xml')).read_bytes()
                self.assertEqual(by_flavor[row.flavor]['manifest_sha256'], hashlib.sha256(payload).hexdigest())
                facts = {}
                result = s.validate_manifest(payload, compiled=True, profile=row.profile, support_refusal=facts)
                self.assertTrue(result['compiled_manifest_inspected'])
                self.assertFalse(result['native_permission_or_result_inferred'])
                self.assertEqual({}, facts)


if __name__ == '__main__':
    unittest.main(verbosity=2)
