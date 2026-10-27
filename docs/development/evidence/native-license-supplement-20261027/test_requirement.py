"""Small executable regression for the absent pinned-VCS supplement boundary."""
from pathlib import Path
import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest

ROOT = Path('/root/projects/nativeCmpKit')
sys.path.insert(0, str(ROOT / 'tests/consumer'))
import collect_native_licenses as collector
from _native_test_fixtures import metadata_fixture

class SupplementRequirement(unittest.TestCase):
    def test_archive_gap_can_use_only_an_explicit_checksum_bound_catalog(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as directory:
            root = Path(directory)
            cache, catalog = root / 'cache', root / 'catalog'
            cache.mkdir()
            catalog.mkdir()
            archive = cache / 'example-1.0.0.crate'
            with tarfile.open(archive, 'w:gz') as stream:
                payload = b'[package]\nname="example"\nversion="1.0.0"\nlicense="MIT"\n'
                member = tarfile.TarInfo('example-1.0.0/Cargo.toml')
                member.size = len(payload)
                stream.addfile(member, io.BytesIO(payload))
            metadata = root / 'metadata.json'
            metadata.write_text(json.dumps(metadata_fixture(checksum=hashlib.sha256(archive.read_bytes()).hexdigest())))
            # An empty explicit catalog must preserve the original fail-closed
            # missing-text gap, not invent a license or waive publication gates.
            report = collector.collect(metadata, [cache], root / 'output', vcs_supplements=catalog)
            self.assertFalse(report['complete_material_collection'])
            self.assertFalse(report['license_obligations_reviewed'])
            self.assertEqual(1, len(report['gaps']))
            self.assertEqual([], report['packages'][0]['files'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
