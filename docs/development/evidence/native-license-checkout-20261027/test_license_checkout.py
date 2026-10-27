"""Real Git newline/whitespace fixtures; not Windows, consumer or legal tests."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CATALOG = "licenses/native-dependency-supplements/jni-sys-macros-0.4.1"
APACHE = CATALOG + "/LICENSE-APACHE"


class LicenseCheckoutContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.empty = self.root / "empty-git-policy"
        self.empty.mkdir()
        self.attributes = self.empty / "global-attributes"
        self.attributes.write_bytes(b"")
        self.git("init", "--quiet", "--template=" + str(self.empty))
        (self.root / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *arguments, expected=0):
        # No hooks, user global attributes, network or commit identities. The
        # checkout's actual .gitattributes remains the owning policy input.
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=" + str(self.empty),
             "-c", "core.attributesFile=" + str(self.attributes),
             "-c", "core.autocrlf=true",
             "-c", "core.whitespace=blank-at-eof,blank-at-eol,space-before-tab",
             *arguments], cwd=self.root, capture_output=True, timeout=30)
        if expected is not None:
            self.assertEqual(expected, result.returncode, result.stderr.decode(errors="replace"))
        return result

    def copy_public(self, relative):
        payload = (ROOT / relative).read_bytes()
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return payload

    def test_catalog_index_and_checkout_preserve_every_reviewed_byte(self):
        source = ROOT / CATALOG
        paths = sorted(path.relative_to(ROOT).as_posix()
                       for path in source.rglob("*") if path.is_file())
        self.assertEqual(8, len(paths))
        original = {path: self.copy_public(path) for path in paths}
        self.git("add", "--", ".gitattributes", *paths)
        for path, payload in original.items():
            self.assertEqual(payload, self.git("show", ":" + path).stdout)
            (self.root / path).unlink()
        self.git("checkout-index", "--force", "--", *paths)
        for path, payload in original.items():
            self.assertEqual(payload, (self.root / path).read_bytes(), path)

    def test_exact_author_apache_eof_bytes_are_not_trimmed(self):
        payload = self.copy_public(APACHE)
        self.assertTrue(payload.endswith(b"\n\n"), "Preserve the actual author's complete byte sequence")
        self.git("add", "--", ".gitattributes", APACHE)
        self.git("diff", "--cached", "--check")

    def test_exact_file_eof_exception_does_not_hide_trailing_spaces(self):
        payload = self.copy_public(APACHE)
        (self.root / APACHE).write_bytes(payload + b"Synthetic changed fixture text \n")
        self.git("add", "--", ".gitattributes", APACHE)
        result = self.git("diff", "--cached", "--check", expected=None)
        self.assertNotEqual(0, result.returncode)
        self.assertIn(b"trailing whitespace", result.stdout + result.stderr)

    def test_unrelated_source_keeps_blank_at_eof_guard(self):
        path = self.root / "tests/consumer/example.py"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"# Synthetic source fixture\n\n")
        self.git("add", "--", ".gitattributes", "tests/consumer/example.py")
        result = self.git("diff", "--cached", "--check", expected=None)
        self.assertNotEqual(0, result.returncode)
        self.assertIn(b"new blank line at EOF", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
