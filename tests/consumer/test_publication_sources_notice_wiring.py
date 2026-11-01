"""Owning Gradle source-notice guards; no build or real artifact acceptance.

Cached KGP 2.4.20 declarations identify source tasks as org.gradle.jvm.tasks.Jar.
Gradle 9.7.1's deprecated Jar is its subclass, so selecting the deprecated type
misses the real source archives. Actual archive retention has a separate gate.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PublicationSourcesNoticeWiringTest(unittest.TestCase):
    def source(self):
        source = (ROOT / "convention-plugins/src/main/kotlin/PublicationNotices.kt").read_text()
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
        return re.sub(r"(?m)^\s*//[^\n]*", "", source)

    def test_real_kmp_sources_jar_base_receives_embedded_notice_provider(self):
        source = self.source()
        self.assertRegex(source, r"(?m)^import org\.gradle\.jvm\.tasks\.Jar\s*$")
        self.assertNotRegex(source, r"(?m)^import org\.gradle\.api\.tasks\.bundling\.Jar\s*$")
        self.assertRegex(source, r"(?m)^\s*tasks\.withType<Jar>\(\)\.configureEach\s*"
            r"\{\s*from\(prepareEmbedded\)\s*\}\s*$")

    def test_complete_notice_layouts_and_compiler_archive_boundary_are_retained(self):
        source = self.source()
        compact = re.sub(r"\s+", "", source)
        self.assertIn('valrootNotices=listOf("LICENSE","NOTICE","THIRD_PARTY_NOTICES.md").map(root::file)', compact)
        for prefix in ("META-INF/nativecmpkit", "META-INF/nativecmpkit/$moduleName"):
            self.assertIn('from(rootNotices){into("' + prefix + '")}', compact)
            self.assertIn('from(root.dir("licenses")){into("' + prefix + '/licenses")}', compact)
        self.assertIn('from(prepareCanonical)', compact)
        self.assertIn('tasks.withType<Zip>().matching{it.name.endsWith("Aar")}'
            '.configureEach{from(prepareEmbedded)}', compact)
        self.assertCountEqual(["Jar", "Zip", "PublishToMavenRepository"],
            re.findall(r"tasks\.withType<([^>]+)>\(\)", source))
        self.assertEqual(3, compact.count("duplicatesStrategy=DuplicatesStrategy.FAIL"))
        self.assertIn("isPreserveFileTimestamps=false", compact)
        self.assertIn("isReproducibleFileOrder=true", compact)


if __name__ == "__main__":
    unittest.main()
