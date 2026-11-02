"""Owning source/policy guards, not package or device execution evidence."""
import json
from pathlib import Path
import re
import tempfile
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

    def assert_reviewed_workflow_policy(self, root):
        workflows = list((root / '.github/workflows').glob('*.yml')) + list((root / '.github/workflows').glob('*.yaml'))
        push_paths = {
            'javafx-library-candidate.yml': (
                'tests/dependency/javafx-http2-cancellation/build_runtime_candidate.py',
                'tests/dependency/javafx-http2-cancellation/library-runtime-candidate.init.gradle.kts',
            ),
            'javafx-dependency-regression.yml': (
                'tests/dependency/javafx-http2-cancellation/JavaFxPublicCancellationProbe.java',
                'tests/dependency/javafx-http2-cancellation/cancel-response-future.patch',
                'tests/dependency/javafx-http2-cancellation/artifacts.json',
            ),
        }
        self.assertEqual({'gradle.yml', 'build-native-libs.yml', *push_paths}, {path.name for path in workflows})
        for path in workflows:
            text = re.sub(r'(?m)^\s*#.*$', '', path.read_text())
            blocks = re.findall(r'(?ms)^on:\n(.*?)(?=^\S|\Z)', text)
            self.assertEqual(1, len(blocks))
            events = re.findall(r'(?m)^  ([a-z_]+):', blocks[0])
            expected = {'workflow_dispatch', 'push'} if path.name in push_paths else {'workflow_dispatch'}
            self.assertEqual(expected, set(events))
            self.assertEqual(len(expected), len(events))
            if path.name in push_paths:
                push = re.findall(r'(?ms)^  push:\n(.*?)(?=^  [a-z_]+:|\Z)', blocks[0])
                self.assertEqual(1, len(push))
                allowed = '    branches: [development/preview-hardening]\n    paths:\n' + ''.join(
                    '      - ' + name + '\n' for name in push_paths[path.name])
                self.assertEqual(allowed.strip(), push[0].strip())
                self.assertIn("github.ref == 'refs/heads/development/preview-hardening'", text)
            self.assertIn('workflow_dispatch:', text)
            self.assertIn('permissions:\n  contents: read', text)
            self.assertNotRegex(text, r'(?m)^\s*[\w-]+:\s*(?:write|write-all)\s*$')
            for forbidden in ('gh release create', 'cargo publish', 'npm publish', 'gh-deploy', 'sed -i', 'publishAndReleaseToMavenCentral'):
                self.assertNotIn(forbidden, text)

    def test_active_workflows_use_only_reviewed_read_only_triggers_without_publication(self):
        self.assert_reviewed_workflow_policy(ROOT)

    def fixture_workflows(self):
        temporary = tempfile.TemporaryDirectory(prefix='nativecmpkit-workflow-boundary-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        directory = root / '.github/workflows'
        directory.mkdir(parents=True)
        for source in (ROOT / '.github/workflows').glob('*.yml'):
            (directory / source.name).write_bytes(source.read_bytes())
        return root

    def test_candidate_automatic_trigger_cannot_expand_branches_paths_or_events(self):
        root = self.fixture_workflows()
        path = root / '.github/workflows/javafx-library-candidate.yml'
        original = path.read_text()
        mutations = (
            original.replace('branches: [development/preview-hardening]', 'branches: [main]'),
            original.replace('paths:\n', 'paths:\n      - "**"\n', 1),
            original.replace('  workflow_dispatch:', '  release:\n  workflow_dispatch:', 1),
        )
        for number, mutation in enumerate(mutations):
            with self.subTest(mutation=number):
                path.write_text(mutation)
                with self.assertRaises(AssertionError):
                    self.assert_reviewed_workflow_policy(root)

    def test_reviewed_workflow_cannot_gain_write_permissions_publish_commands_or_unknown_files(self):
        root = self.fixture_workflows()
        directory = root / '.github/workflows'
        path = directory / 'javafx-library-candidate.yml'
        original = path.read_text()
        for mutation in (
            original.replace('  contents: read', '  contents: read\n  packages: write', 1),
            original.replace('  contents: read', '  contents: read\n  id-token: write', 1),
            original + '\n# comment ignored\n      - run: gh release create unsafe\n',
        ):
            with self.subTest(kind=mutation[-50:]):
                path.write_text(mutation)
                with self.assertRaises(AssertionError):
                    self.assert_reviewed_workflow_policy(root)
        path.write_text(original)
        (directory / 'unreviewed.yml').write_text('on:\n  workflow_dispatch:\npermissions:\n  contents: read\n')
        with self.assertRaises(AssertionError):
            self.assert_reviewed_workflow_policy(root)


if __name__ == '__main__':
    unittest.main()
