"""Owning source/policy guards, not package or device execution evidence."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PreviewBoundaryBatchTests(unittest.TestCase):
    def test_root_executes_the_same_version_policy_as_convention_junit_and_does_not_apply_publisher(self):
        source = (ROOT / "build.gradle.kts").read_text()
        self.assertIn('id("module.publication").apply(false)', source)
        self.assertIn('PublicationVersionPolicy.validate(nativeCmpkitVersion.get())', source)
        self.assertIn('version = nativeCmpkitVersion.get()', source)
        self.assertNotIn('require(Regex("(?:0|[1-9]', source)
        policy = ROOT / "convention-plugins/src/main/kotlin/io/github/apdelrahman1911/nativecmpkit/buildlogic/PublicationVersionPolicy.kt"
        self.assertTrue(policy.is_file())

    def test_maps_has_no_source_api_or_publisher_and_media_scheduler_are_excluded_not_permissions(self):
        settings = (ROOT / "settings.gradle.kts").read_text()
        self.assertIn('\":calf-maps\"', settings)
        for name in ('calf-media', 'calf-notifications'):
            self.assertNotIn(f'\":{name}\"', settings)
        self.assertIn('\":calf-permissions:notifications\"', settings)
        maps = (ROOT / "calf-maps/build.gradle.kts").read_text()
        self.assertNotIn('module.publication', maps)
        self.assertEqual([], list((ROOT / "calf-maps/src").rglob('*.kt')))
        modules = json.loads((ROOT / "docs/migration/identity.json").read_text())['modules']
        self.assertEqual(21, len(modules))
        self.assertTrue(all(module['source_directory'] not in {'calf-maps', 'calf-media', 'calf-notifications'} for module in modules))

    def test_future_experimental_enabling_keeps_explicit_upstream_references_and_release_gates(self):
        roadmap = (ROOT / "docs/roadmap/README.md").read_text()
        for url in ('https://github.com/MohamedRejeb/Calf/issues/27', 'https://github.com/MohamedRejeb/Calf/issues/245'):
            self.assertIn(url, roadmap)
        self.assertIn('not implemented features', roadmap)
        self.assertIn('fresh Gradle configuration, an implemented API contract', roadmap)
        self.assertIn('platform privacy/provider setup and native device tests', roadmap)

    def test_all_active_workflows_remain_manual_read_only_with_no_version_stamping_or_release_template(self):
        workflows = list((ROOT / '.github/workflows').glob('*.yml')) + list((ROOT / '.github/workflows').glob('*.yaml'))
        self.assertEqual({'gradle.yml', 'build-native-libs.yml'}, {path.name for path in workflows})
        for path in workflows:
            text = re.sub(r'(?m)^\s*#.*$', '', path.read_text())
            self.assertIn('workflow_dispatch:', text)
            self.assertIn('permissions:\n  contents: read', text)
            self.assertNotRegex(text, r'(?m)^\s*[\w-]+:\s*(?:write|write-all)\s*$')
            for forbidden in ('gh release create', 'cargo publish', 'npm publish', 'gh-deploy', 'sed -i', 'publishAndReleaseToMavenCentral'):
                self.assertNotIn(forbidden, text)


if __name__ == '__main__':
    unittest.main()
