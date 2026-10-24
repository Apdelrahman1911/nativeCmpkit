"""Offline checks for documentation-only link transformations."""
from pathlib import Path
import tempfile
import unittest
from mkdocs_repository_links import repository_link


class RepositoryLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in ("docs/audit/README.md", "docs/audit/findings/IO.json", "docs/testing/README.md", "docs/migration/upstream-metadata/raw.json", "src/file.kt", "AGENTS.md"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test")

    def rewrite(self, url):
        return repository_link(url, "audit/README.md", self.root)

    def test_normal_site_page_is_retained(self):
        self.assertEqual("../testing/README.md", self.rewrite("../testing/README.md"))

    def test_source_link_preserves_fragment_and_query(self):
        self.assertEqual("https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/src/file.kt?plain=1#L2", self.rewrite("../../src/file.kt?plain=1#L2"))

    def test_excluded_archive_and_finding_go_to_repository(self):
        for url in ("findings/IO.json", "../migration/upstream-metadata/raw.json"):
            self.assertIn("/blob/main/docs/", self.rewrite(url))

    def test_directory_uses_tree(self):
        self.assertEqual("https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/audit/findings", self.rewrite("findings/"))

    def test_external_missing_and_outside_paths_are_untouched(self):
        for url in ("https://example.test/a", "//example.test/b", "#anchor", "missing.md", "/absolute", "../../../outside.txt"):
            self.assertEqual(url, self.rewrite(url))


if __name__ == "__main__":
    unittest.main()
