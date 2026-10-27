"""Real Git public-archive byte/whitespace fixtures; no network or platform tests."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = "docs/migration/upstream-updates/20991231T235959Z/source/issue.json"
DRAFT = "docs/development/upstream-sync-20991231T235959Z/drafts/upstream-0027-comment.md"


class SnapshotCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.empty = self.root / "empty-policy"
        self.empty.mkdir()
        self.global_attributes = self.empty / "global-attributes"
        self.global_attributes.write_bytes(b"")
        self.git("init", "--quiet", "--template=" + str(self.empty))
        (self.root / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())

    def git(self, *arguments, expected=0):
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=" + str(self.empty),
             "-c", "core.attributesFile=" + str(self.global_attributes),
             "-c", "core.autocrlf=true",
             "-c", "core.whitespace=blank-at-eof,blank-at-eol,space-before-tab",
             *arguments], cwd=self.root, capture_output=True, timeout=30,
        )
        if expected is not None:
            self.assertEqual(expected, result.returncode, result.stderr.decode(errors="replace"))
        return result

    def stage(self, name, payload):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        self.git("add", "--", ".gitattributes", name)
        return path

    def round_trip(self, name, payload):
        path = self.stage(name, payload)
        self.assertEqual(payload, self.git("show", ":" + name).stdout)
        path.unlink()
        self.git("checkout-index", "--force", "--", name)
        self.assertEqual(payload, path.read_bytes())

    def test_raw_dated_api_snapshot_keeps_lf_bytes_under_windows_checkout_policy(self):
        self.round_trip(SNAPSHOT, b'{"public_author_text":"a \\r\\n b"}\n')

    def test_quoted_author_draft_keeps_exact_crlf_and_trailing_space_bytes(self):
        self.round_trip(DRAFT, b"# Attributed public discussion\n\nOriginal line \r\n\tNext line\r\n\n")

    def test_archival_author_whitespace_does_not_require_trimming(self):
        self.stage(DRAFT, b"# Attributed public discussion\n\nOriginal author text \r\n\n")
        self.git("diff", "--cached", "--check")

    def test_current_docs_source_and_refresh_readme_keep_whitespace_guards(self):
        for name in (
            "docs/development/upstream-sync-20991231T235959Z/README.md",
            "docs/development/current.md", "scripts/example.py",
        ):
            with self.subTest(path=name):
                self.stage(name, b"# Current synthetic maintained text \n\n")
                result = self.git("diff", "--cached", "--check", "--", name, expected=None)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(b"trailing whitespace", result.stdout + result.stderr)
                self.assertIn(b"new blank line at EOF", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
