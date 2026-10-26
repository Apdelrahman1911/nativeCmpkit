"""Offline parser/integrity fixtures; actual pip/MkDocs evidence is separate."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import verify_locked_environment as locked


class LockTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def parse(self, contents):
        path = self.root / "requirements.lock"
        path.write_text(contents)
        return locked.lock_entries(path)

    def test_exact_hash_pin(self):
        self.assertEqual(self.parse("# generated\na==1.2 --hash=sha256:" + "a"*64 + "\n"), {"a": ("1.2", "a"*64)})

    def test_reject_unsafe_unpinned_or_duplicate_locks(self):
        for contents in ("", "a>=1.2", "a @ https://example.com/a.whl", "--index-url https://example.com", "a==1.0 --hash=md5:123", "a==1.0 --hash=sha256:" + "a"*63, ("a==1.2 --hash=sha256:" + "a"*64 + "\n")*2):
            with self.subTest(contents=contents), self.assertRaises(ValueError):
                self.parse(contents)

    def test_current_lock_graph_is_consistent(self):
        self.assertEqual(len(locked.validate_provenance()["artifacts"]), 41)

    def test_artifact_bytes_verified(self):
        path = self.root / "asset.whl"
        path.write_bytes(b"public test artifact")
        locked.verify_bytes(path, hashlib.sha256(path.read_bytes()).hexdigest())
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            locked.verify_bytes(path, "0"*64)

    def test_symlink_artifact_rejected(self):
        path = self.root / "asset.whl"
        path.write_bytes(b"fixture")
        link = self.root / "linked.whl"
        link.symlink_to(path)
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            locked.verify_bytes(link, hashlib.sha256(path.read_bytes()).hexdigest())

    def altered_provenance(self, change):
        req = self.root / "requirements"
        req.mkdir(exist_ok=True)
        for name in ("docs.in", "docs-build.in", "docs-linux-py312.lock", "docs-build.lock", "docs-lock-provenance.json"):
            (req / name).write_bytes((locked.ROOT / "requirements" / name).read_bytes())
        data = json.loads((req / "docs-lock-provenance.json").read_text())
        change(data)
        (req / "docs-lock-provenance.json").write_text(json.dumps(data))
        return req

    def test_foreign_registry_rejected(self):
        self.altered_provenance(lambda data: data["artifacts"][0].update(url="https://example.com/"+data["artifacts"][0]["filename"]))
        with self.assertRaisesRegex(ValueError, "official HTTPS"):
            locked.validate_provenance(self.root)

    def test_false_trust_claim_rejected(self):
        self.altered_provenance(lambda data: data.update(independent_trust_reviewed=True))
        with self.assertRaisesRegex(ValueError, "trust claim"):
            locked.validate_provenance(self.root)

    def test_changed_lock_rejected(self):
        req = self.altered_provenance(lambda data: None)
        with (req / "docs-linux-py312.lock").open("a") as out:
            out.write("evil==1.0 --hash=sha256:" + "0"*64 + "\n")
        with self.assertRaisesRegex(ValueError, "changed without"):
            locked.validate_provenance(self.root)

    def test_removed_artifact_rejected(self):
        self.altered_provenance(lambda data: data["artifacts"].pop())
        with self.assertRaisesRegex(ValueError, "graph and provenance differ"):
            locked.validate_provenance(self.root)


if __name__ == "__main__":
    unittest.main()
