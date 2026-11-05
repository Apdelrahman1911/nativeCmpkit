"""NEW tiny metadata/log controls; no Gradle, native, network or target imports."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET
import os


ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / 'scripts/ci/javafx_ordinary_maven_consumer.py'
METADATA_FILES = ('gradle/verification-metadata.xml',
                  'tests/consumer/javafx-ordinary-webview/gradle/verification-metadata.xml')
NS = 'https://schema.gradle.org/dependency-verification'


def functions(path, wanted, namespace):
    """Execute only named pure owning helpers, never a controller/import/main."""
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    if {node.name for node in selected} != set(wanted):
        raise AssertionError('Missing NEW owning metadata/report helper')
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def helpers(root):
    namespace = {'Path': Path, 're': re, 'ET': ET, 'hashlib': hashlib, 'os': os,
                 'ROOT': root, 'OUTPUT': 'build/ci-verification/javafx-ordinary-windows',
                 'METADATA_FILES': METADATA_FILES,
                 'packaged': SimpleNamespace(EvidenceError=ValueError)}
    path_tools = functions(ROOT / 'scripts/ci/library_tests.py', {'safe_path'}, {'Path': Path})
    namespace['lt'] = SimpleNamespace(safe_path=path_tools['safe_path'])
    diagnostic_namespace = {'re': re, 'MAX_EXCERPT_BYTES': 24 * 1024,
                            'MAX_EXCERPTS': 24,
                            'CREDENTIAL': re.compile(r'(?i)(authorization|password|passwd|secret|token|credential|BEGIN .*PRIVATE KEY|https?://[^/\s]+@|[?&](?:sig|key|auth)=)'),
                            'TASK': re.compile(r'^> Task (:[a-zA-Z0-9:_-]+)(?:\s|$)'),
                            'XCODE_SOURCE_ERROR': re.compile(r'^[^\r\n]{1,1024}\.(?:swift|m|mm|c|h|cpp):[0-9]+:[0-9]+: (?:fatal )?error: ')}
    functions(ROOT / 'scripts/ci/failure_diagnostics.py', {'sanitized', 'sections'}, diagnostic_namespace)
    namespace['failure_diagnostics'] = SimpleNamespace(MAX_LOG_BYTES=4 * 1024**2,
        MAX_EXCERPTS=24, sections=diagnostic_namespace['sections'])
    return functions(CONTROLLER, {'need', 'read', 'dependency_metadata_preflight', 'compiler_diagnostics'}, namespace)


def metadata(verify='true', extra=''):
    return (f'<verification-metadata xmlns="{NS}"><configuration>'
            f'<verify-metadata>{verify}</verify-metadata><verify-signatures>false</verify-signatures>{extra}'
            '</configuration><components><component group="synthetic.fixture" name="only" version="1">'
            f'<artifact name="only-1.jar"><sha256 value="{"a" * 64}"/></artifact>'
            '</component></components></verification-metadata>').encode()


class JavafxOrdinaryTrustReportingTests(unittest.TestCase):
    def test_both_missing_metadata_scopes_are_reported_without_trust_or_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            observed = helpers(root)['dependency_metadata_preflight']()
            self.assertFalse(observed['metadata_usable_for_strict_execution'])
            self.assertFalse(observed['independent_trust_qualified'])
            self.assertEqual([row['path'] for row in observed['metadata']], list(METADATA_FILES))
            self.assertTrue(all(row['reason'] == 'missing' for row in observed['metadata']))
            self.assertEqual(list(root.iterdir()), [])

    def test_standalone_metadata_is_independent_and_captured_checksums_do_not_certify_trust(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            helper = helpers(root)['dependency_metadata_preflight']
            for index, name in enumerate(METADATA_FILES):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(metadata())
                observed = helper()
                self.assertIs(observed['metadata_usable_for_strict_execution'], index == 1)
                self.assertFalse(observed['independent_trust_qualified'])
                self.assertEqual(observed['metadata'][index]['sha256'], hashlib.sha256(metadata()).hexdigest())
                self.assertEqual(observed['metadata'][index]['bytes'], len(metadata()))
                self.assertEqual(observed['metadata'][index]['artifact_count'], 1)

    def test_unsafe_disabled_empty_or_bypass_metadata_never_admits_strict_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            helper = helpers(root)['dependency_metadata_preflight']
            for name in METADATA_FILES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(metadata())
            refused = (b'<broken', metadata('false'), metadata(extra='<trusted-artifacts><trust group=".*" regex="true"/></trusted-artifacts>'),
                       metadata().replace(b'<sha256 ', b'<sha1 ').replace(b'</sha256>', b'</sha1>'),
                       metadata().replace(b'a' * 64, b'z' * 64),
                       metadata().replace(b'<components>', b'<components><!--').replace(b'</components>', b'--></components>'),
                       b'<!DOCTYPE x [<!ENTITY payload "private">]>' + metadata())
            for payload in refused:
                with self.subTest(payload=payload[:60]):
                    (root / METADATA_FILES[1]).write_bytes(payload)
                    observed = helper()
                    self.assertFalse(observed['metadata_usable_for_strict_execution'])
                    self.assertFalse(observed['independent_trust_qualified'])
                    self.assertNotIn('private', str(observed))
            outside = root / 'outside.xml'
            outside.write_bytes(metadata())
            target = root / METADATA_FILES[1]
            target.unlink()
            target.symlink_to(outside)
            self.assertFalse(helper()['metadata_usable_for_strict_execution'])

    def test_owned_compiler_and_native_child_diagnostics_survive_without_full_logs_or_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / 'build/ci-verification/javafx-ordinary-windows'
            output.mkdir(parents=True)
            originals = {}
            for name in ('producer.log', 'module/resolution.log', 'pom/resolution.log', 'native/consumer.log'):
                target = output / name
                target.parent.mkdir(parents=True, exist_ok=True)
                originals[name] = (b'arbitrary private application output\n'
                    b'e: file:///owned/OrdinaryCuredWebStopConsumerTest.kt:99:1 Unresolved reference.\n'
                    b'e: credential=do-not-share\n* What went wrong:\nCompilation failed.\n* Try:\nUnrelated advice\n')
                target.write_bytes(originals[name])
            observed = helpers(root)['compiler_diagnostics'](output)
            self.assertEqual({row['name'] for row in observed['logs']}, set(originals))
            self.assertFalse(observed['full_logs_uploaded'])
            self.assertFalse(observed['compiler_or_native_success_inferred'])
            for row in observed['logs']:
                self.assertEqual(row['sha256'], hashlib.sha256(originals[row['name']]).hexdigest())
                self.assertEqual((output / row['name']).read_bytes(), originals[row['name']])
                text = str(row['excerpts'])
                self.assertIn('Unresolved reference.', text)
                self.assertIn('Compilation failed.', text)
                self.assertNotIn('do-not-share', text)
                self.assertNotIn('arbitrary private application output', text)
                self.assertNotIn('Unrelated advice', text)

    def test_oversized_and_foreign_diagnostic_paths_are_not_read_or_uploaded(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / 'build/ci-verification/javafx-ordinary-windows'
            output.mkdir(parents=True)
            target = output / 'native/consumer.log'
            target.parent.mkdir(parents=True)
            with target.open('wb') as stream:
                stream.truncate(4 * 1024**2 + 1)
            diagnostic = helpers(root)['compiler_diagnostics']
            observed = diagnostic(output)
            self.assertFalse(observed['logs'][0]['inspected'])
            self.assertNotIn('excerpts', observed['logs'][0])
            with self.assertRaises(ValueError):
                diagnostic(root)
            target.unlink()
            foreign = root / 'foreign.log'
            foreign.write_text('e: foreign secret\n')
            target.symlink_to(foreign)
            with self.assertRaises(ValueError):
                diagnostic(output)
            self.assertEqual(foreign.read_text(), 'e: foreign secret\n')

    def test_preflight_and_always_artifact_wiring_precede_heavy_work_and_keep_native_scope(self):
        source = CONTROLLER.read_text(encoding='utf-8')
        tree = ast.parse(source)
        functions_by_name = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertIn('dependency_metadata_preflight', functions_by_name)
        run = ast.unparse(functions_by_name['run'])
        self.assertLess(run.index('dependency_metadata_preflight()'), run.index('runtime_context.capture('))
        self.assertLess(run.index('compiler_diagnostics(output)'), run.index("write(output / 'receipt.json', record)"))
        self.assertIn('dependency_verification_metadata_qualified=False', run)
        workflow = (ROOT / '.github/workflows/javafx-library-candidate.yml').read_text(encoding='utf-8')
        job = workflow.split('  ordinary-windows-consumer1:\n', 1)[1]
        self.assertIn('--metadata-preflight-only', job)
        self.assertLess(job.index('--metadata-preflight-only'), job.index('rustup toolchain install'))
        self.assertIn('build/ci-runtime/javafx-ordinary-dependency-preflight.json', job)
        self.assertIn('build/ci-verification/javafx-ordinary-windows/compile-diagnostics.json', job)
        self.assertIn('if: always()', job)
        self.assertNotIn('*.log', job)
        self.assertNotIn('*.jar', job)
        self.assertNotIn('run_library_candidate.py', job)


if __name__ == '__main__':
    unittest.main(verbosity=2)
