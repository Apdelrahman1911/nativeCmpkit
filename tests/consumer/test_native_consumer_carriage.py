"""NEW owned-filesystem/source-carriage controls; not library/native material passes.

The fixture's consumer/catalog/metadata bytes are genuine source-controlled
material. Its small local Git repository is only an owned test fixture, not a
trusted native producer. No existing license/notice/native test, collector or
legacy loader is executed. The isolated import recipe is tested statically;
one genuine copied-checker import smoke is recorded separately after freezing.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import native_consumer_carriage as carriage
from verify_artifacts import InvalidArtifact

ROOT = Path(__file__).resolve().parents[2]


class NativeConsumerCarriageTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / "owned-source"
        self.source.mkdir()
        paths = ["tests/consumer/" + name for name in carriage.CONSUMER_FILES]
        paths += list(carriage.MATERIAL_INPUTS)
        for relative in paths:
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        self.git("init", "--quiet")
        self.revision = self.commit()
        self.output = self.root / "independent-bundle"

    def git(self, *arguments):
        command = ["git", "-c", "core.hooksPath=/dev/null", "-c", "user.name=Owned carriage fixture",
                   "-c", "user.email=carriage-fixture@example.invalid", "-C", str(self.source), *arguments]
        return subprocess.run(command, capture_output=True, check=True, timeout=15).stdout.decode().strip()

    def commit(self):
        self.git("add", "--all")
        self.git("commit", "--quiet", "--allow-empty", "-m", "Owned inert fixture, not native producer evidence")
        return self.git("rev-parse", "HEAD")

    def prepare(self):
        return carriage.prepare(self.source, self.output, expected_source_revision=self.revision)

    def assert_refused_before_output(self):
        with self.assertRaises(InvalidArtifact):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_exact13_consumer_and22_inert_material_files_are_independent_byte_copies(self):
        report = self.prepare()
        self.assertEqual(35, len(report["files"]))
        self.assertEqual(13, report["consumer_source_count"])
        self.assertEqual(22, report["inert_original_material_count"])
        self.assertEqual(report, carriage.verify(self.source, self.output, expected_source_revision=self.revision))
        for record in report["files"]:
            original = self.source / record["source"]
            copied = self.output / record["target"]
            self.assertEqual(original.read_bytes(), copied.read_bytes())
            self.assertNotEqual(original.stat().st_ino, copied.stat().st_ino)
            self.assertEqual(1, copied.stat().st_nlink)
        self.assertEqual(36, len([path for path in self.output.rglob('*') if path.is_file()]))
        self.assertEqual("7d6b6d5b43f93ae085dc66a3377b3c7967400bf7", report["preserved_native_metadata_producer_revision"])
        self.assertNotEqual(self.revision, report["preserved_native_metadata_producer_revision"])
        for field in ("inert_context_is_native_producer_source_root", "complete_current_native_material_collection",
                      "source_authenticity_certified", "license_obligations_reviewed", "release_readiness_certified"):
            self.assertIs(report[field], False)

    def test_explicit_full_revision_exact_git_root_and_clean_source_are_required(self):
        for value in ("", "c" * 39, "f" * 40):
            with self.subTest(revision=value), self.assertRaises(InvalidArtifact):
                carriage.prepare(self.source, self.output, expected_source_revision=value)
            self.assertFalse(self.output.exists())
        with self.assertRaises(InvalidArtifact):
            carriage.prepare(self.source / 'tests', self.output, expected_source_revision=self.revision)
        (self.source / 'untracked-source-change').write_text('owned dirty fixture, not reviewed source')
        self.assert_refused_before_output()
        (self.source / 'untracked-source-change').unlink()
        helper = 'tests/consumer/native_license_legacy_winapi.py'
        (self.source / '.gitignore').write_text(helper + '\n')
        self.git('rm', '--cached', '--quiet', helper)
        self.revision = self.commit()
        self.assertEqual('', self.git('status', '--porcelain'))
        self.assert_refused_before_output()  # Ignored input is not committed carrier source.

    def test_missing_legacy_helper_cannot_produce_a_partial_consumer_bundle(self):
        (self.source / 'tests/consumer/native_license_legacy_winapi.py').unlink()
        self.revision = self.commit()  # Clean but incomplete owned fixture.
        self.assert_refused_before_output()

    def test_changed_or_self_rehashed_material_metadata_and_original_consumer_are_not_admitted(self):
        selected = (
            'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/LICENSE-MIT',
            next(path for path in carriage.MATERIAL_INPUTS if path.endswith('/calf-file-picker.json')),
            'tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedNativeConsumerTest.kt',
        )
        for path in selected:
            original = (self.source / path).read_bytes()
            with self.subTest(path=path):
                (self.source / path).write_bytes(original + b'\nCounterfeit owned fixture bytes.\n')
                self.revision = self.commit()
                self.assert_refused_before_output()
            (self.source / path).write_bytes(original)
            self.revision = self.commit()
        with self.assertRaises(TypeError):
            carriage.MATERIAL_INPUTS[selected[0]] = '0' * 64
        checker = 'tests/consumer/verify_artifacts.py'
        original = (self.source / checker).read_bytes()
        self.git('update-index', '--assume-unchanged', checker)
        (self.source / checker).write_bytes(original + b'\nCounterfeit hidden tracked edit.\n')
        self.assertEqual('', self.git('status', '--porcelain'))
        self.assert_refused_before_output()  # Git's clean status cannot replace committed-blob equality.

    def test_symlinks_hardlinks_and_nonregular_source_inputs_refuse_without_opening_a_copy(self):
        path = self.source / 'tests/consumer/native_license_legacy_winapi.py'
        original = path.read_bytes()
        held = self.root / 'owning-helper-copy'
        held.write_bytes(original)
        path.unlink(); path.symlink_to(held)
        self.revision = self.commit()
        self.assert_refused_before_output()
        path.unlink(); path.hardlink_to(held)
        self.revision = self.commit()
        self.assert_refused_before_output()
        path.unlink(); path.mkdir()
        self.revision = self.commit()
        self.assert_refused_before_output()

    def test_preexisting_inside_source_or_symlink_parent_outputs_are_never_deleted_or_merged(self):
        self.output.mkdir()
        sentinel = self.output / 'owner-file'
        sentinel.write_text('preserve me')
        with self.assertRaises(InvalidArtifact): self.prepare()
        self.assertEqual('preserve me', sentinel.read_text())
        inside = self.source / 'untracked-output'
        with self.assertRaises(InvalidArtifact):
            carriage.prepare(self.source, inside, expected_source_revision=self.revision)
        self.assertFalse(inside.exists())
        with self.assertRaises(InvalidArtifact):
            carriage.prepare(self.source, self.root / 'unused/../new-copy', expected_source_revision=self.revision)
        self.assertFalse((self.root / 'new-copy').exists())
        parent = self.root / 'linked-parent'
        parent.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(InvalidArtifact):
            carriage.prepare(self.source, parent / 'new-copy', expected_source_revision=self.revision)
        self.assertFalse((self.root / 'new-copy').exists())

    def test_source_mutation_during_copy_refuses_and_retains_owned_partial_output_without_receipt(self):
        original = carriage.verify_material
        sentinel = self.root / 'unrelated-owner-file'
        sentinel.write_text('preserve unrelated material')
        def mutate(output, inputs):
            original(output, inputs)
            (self.source / 'tests/consumer/README.md').write_text('owned source changed after capture')
        with mock.patch.object(carriage, 'verify_material', side_effect=mutate), self.assertRaises(InvalidArtifact):
            self.prepare()
        self.assertTrue(self.output.exists())
        self.assertEqual(35, len([path for path in self.output.rglob('*') if path.is_file()]))
        self.assertFalse((self.output / 'carriage.json').exists())
        self.assertEqual('preserve unrelated material', sentinel.read_text())

    def test_copied_helper_loss_tamper_or_rehashed_receipt_cannot_pass_independent_readback(self):
        report = self.prepare()
        path = self.output / 'independent-consumer/native_license_legacy_winapi.py'
        original = path.read_bytes()
        for mode in ('missing', 'tamper', 'false-gates', 'foreign-file', 'foreign-directory'):
            with self.subTest(mode=mode):
                if mode == 'missing': path.unlink()
                if mode == 'tamper': path.write_bytes(original + b'\nCounterfeit owned copy.\n')
                if mode == 'false-gates':
                    altered = dict(report)
                    altered['license_obligations_reviewed'] = True
                    (self.output / 'carriage.json').write_bytes(carriage.encoded(altered))
                if mode == 'foreign-file':
                    (self.output / 'independent-consumer/unrecorded.py').write_text('inert foreign fixture')
                if mode == 'foreign-directory':
                    (self.output / 'inert-material-context/unrecorded').mkdir()
                with self.assertRaises(InvalidArtifact):
                    carriage.verify(self.source, self.output, expected_source_revision=self.revision)
            path.write_bytes(original)
            (self.output / 'carriage.json').write_bytes(carriage.encoded(report))
            if mode == 'foreign-file': (self.output / 'independent-consumer/unrecorded.py').unlink()
            if mode == 'foreign-directory': (self.output / 'inert-material-context/unrecorded').rmdir()

    def test_isolated_stdlib_smoke_recipe_never_runs_material_collector_or_native_functions(self):
        checker = self.root / 'independent-consumer'
        command = carriage.smoke_command(checker)
        self.assertEqual([sys.executable, '-I', '-S', '-B', '-c'], command[:5])
        self.assertEqual(str(checker), command[-1])
        tree = ast.parse(command[5])
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == 'modules' for target in node.targets))
        self.assertEqual(carriage.CHECKER_MODULES, ast.literal_eval(assignment.value))
        calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        self.assertNotIn('load_supplement', calls)
        self.assertNotIn('collect', calls)
        self.assertNotIn('ArtifactVerifier', calls)
        self.assertNotIn('subprocess.run', calls)
        self.assertEqual(13, len(set(carriage.CONSUMER_FILES)))
        self.assertEqual(22, len(carriage.MATERIAL_INPUTS))
        self.assertEqual(7, len(carriage.PRESERVED_CONSUMER_INPUTS))


if __name__ == '__main__':
    unittest.main()
