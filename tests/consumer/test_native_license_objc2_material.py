"""NEW schema4/public-notice controls; never native, staging or legal approval.

The active set's public bytes are held once for this new test population. Later
mutation controls reuse that immutable context in memory, not registry archives.
Synthetic compressed/file/report fixtures are labelled and cannot attest genuine
license material. Original reports are tested only at their independently pinned
refusal boundaries; the real complete carry-forward/writer belongs to the lead.
No Git, network, Cargo, Gradle, native function or existing test body executes.
"""
from __future__ import annotations

import ast
from collections import Counter
import copy
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import carry_forward_native_licenses as carry
import collect_native_licenses as collector
import native_consumer_carriage as carriage
import native_license_material_v2 as primitives
import native_license_objc2_material as active
import native_license_supplements as supplements
import verify_artifacts as gate
from _native_test_fixtures import metadata_fixture

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / supplements.CATALOG_RELATIVE
_MATERIAL_CONTEXT = globals().get("_MATERIAL_CONTEXT")


def material_context():
    """One genuine NEW set admission; all other controls reuse held public bytes."""
    global _MATERIAL_CONTEXT
    if _MATERIAL_CONTEXT is None:
        reads, held = [], {}
        original = supplements.regular_bytes

        def observe(root, relative, maximum=supplements.MAX_FILE_BYTES):
            path = str(root / relative)
            reads.append(path)
            raw = original(root, relative, maximum)
            held[path] = raw
            return raw

        with mock.patch.object(active, 'regular_bytes', side_effect=observe), \
                mock.patch.object(primitives, 'regular_bytes', side_effect=observe):
            values = active.load_adopted_set(CATALOG, ROOT)
        contents = dict(next(iter(values.values())).contents)
        data = gate.load_json_bytes(contents['manifest.json'])
        inputs = {path: held[str(ROOT / path)] for path in active.INPUT_PATHS}
        _MATERIAL_CONTEXT = values, contents, data, inputs, tuple(reads)
    return _MATERIAL_CONTEXT


def held_reader(contents):
    reader = primitives.Reader(Path('/synthetic-held-reader-never-opened'))
    reader.contents = dict(contents)
    return reader


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def synthetic_supplement(name='objc2', shared=b'Synthetic public proof; NOT genuine material.\n'):
    """Constructor-only fixture: deliberately NOT a valid schema4 origin/index."""
    raw = b'Synthetic compressed-identity bytes; NOT a registry archive.\n'
    notice = b'Synthetic permission notice; NOT legal approval.\n'
    package = {'id': name + '@0.0.0', 'name': name, 'version': '0.0.0',
               'source_kind': 'crates.io', 'checksum': supplements.digest(raw),
               'license': 'MIT', 'license_file': None}
    record = {'catalog_path': 'LICENSE-MIT', 'output_path': 'LICENSE-MIT',
              'path': 'LICENSE-MIT', 'bytes': len(notice), 'sha256': supplements.digest(notice),
              'git_blob_oid': supplements.git_blob_oid(notice), 'license_id': 'MIT',
              'copyright_literal': 'Synthetic', 'origin': {'kind': 'synthetic-not-an-origin'}}
    manifest = {'schema_version': 4, 'package': package, 'archive_bytes': len(raw),
                'license_files': [record], 'source_origin': {'kind': 'synthetic-not-an-origin'},
                'path_in_vcs': 'synthetic', 'license_options': ['MIT'],
                'obligations': dict(active.OBLIGATIONS)}
    return active.AdoptedObjc2Supplement(name + '-0.0.0', manifest,
                                       {'manifest.json': shared, 'LICENSE-MIT': notice}), raw, package


class ActiveObjc2MaterialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values, cls.contents, cls.data, cls.inputs, cls.reads = material_context()

    def test_exact15_and_four_current_inputs_are_read_once(self):
        self.assertEqual(15, len(self.values))
        self.assertEqual(active.SELECTED_NAMES, {value.manifest['package']['name'] for value in self.values.values()})
        self.assertEqual(147, len(self.contents))
        self.assertEqual(151, len(self.reads))
        self.assertEqual({1}, set(Counter(self.reads).values()))
        self.assertEqual(active.INPUT_PATHS, set(self.inputs))
        self.assertEqual(active.REVIEWED_INDEX_SHA256, supplements.digest(self.contents['manifest.json']))

    def test_changed_and_self_rehashed_index_refuse_before_any_material_read(self):
        for changed in (self.contents['manifest.json'] + b' ',
                        encoded(self.data | {'obligations': dict(active.OBLIGATIONS, release_readiness_certified=True)})):
            with self.subTest(size=len(changed)), \
                    mock.patch.object(active, 'regular_bytes', return_value=changed) as read, \
                    mock.patch.object(active, 'validate_set', side_effect=AssertionError('No unpinned index admission')):
                with self.assertRaises(gate.InvalidArtifact):
                    active.load_adopted_set(CATALOG, ROOT)
                self.assertEqual(1, read.call_count)

    def test_current_cargo_input_change_and_missing_binding_refuse(self):
        for selected in sorted(self.inputs):
            changed = dict(self.inputs)
            changed[selected] += b'\nSynthetic changed Cargo input.\n'
            with self.subTest(path=selected), \
                    mock.patch.object(active, 'regular_bytes', side_effect=lambda root, path: changed[path]), \
                    self.assertRaises(gate.InvalidArtifact):
                active.inputs(held_reader(self.contents), self.data['inputs'], ROOT)
        with self.assertRaises(gate.InvalidArtifact):
            active.inputs(held_reader(self.contents), self.data['inputs'][:-1], ROOT)
        with self.assertRaises(gate.InvalidArtifact):
            active.load_adopted_set(CATALOG, None)

    def test_changed_raw_commit_tree_and_license_bytes_cannot_be_self_rehashed(self):
        records = [self.data['mads']['origin']['git_commit'],
                   self.data['mads']['origin']['git_trees'][0], self.data['mads']['license_files'][0]]
        for record in records:
            changed = dict(self.contents)
            changed[record['catalog_path']] += b'\nSynthetic tamper.\n'
            with self.subTest(path=record['catalog_path']), self.assertRaises(gate.InvalidArtifact):
                primitives.origin(held_reader(changed), self.data['mads']['origin'],
                                  [active.original_text(item) for item in self.data['mads']['license_files']],
                                  license_files=True)
        altered = copy.deepcopy(self.data['mads'])
        notice = altered['license_files'][0]
        changed = dict(self.contents)
        changed[notice['catalog_path']] += b'\nSynthetic rehashed notice.\n'
        notice.update(bytes=len(changed[notice['catalog_path']]), sha256=supplements.digest(changed[notice['catalog_path']]))
        with self.assertRaises(gate.InvalidArtifact):
            primitives.origin(held_reader(changed), altered['origin'],
                              [active.original_text(item) for item in altered['license_files']], license_files=True)

    def test_four_mit_only_and_eleven_trio_options_keep_all_known_notices(self):
        mit, trio = [], []
        for value in self.values.values():
            name = value.manifest['package']['name']
            entries = value.license_entries('META-INF/synthetic/' + value.identity + '/')
            option_roles = [item for item in entries if item['origin']['role'] == 'original-license-option']
            if name in active.MIT_ONLY:
                mit.append(name)
                self.assertEqual(('MIT',), value.manifest['license_options'])
                self.assertEqual(1, len(option_roles))
            else:
                trio.append(name)
                self.assertEqual(('Zlib', 'Apache-2.0', 'MIT'), value.manifest['license_options'])
                self.assertEqual(3, len(option_roles))
            inherited = [item for item in entries if item['origin']['role'] == 'retained-inherited-attribution']
            self.assertEqual(1, len(inherited))
            self.assertEqual('https://github.com/SSheldon/rust-objc', inherited[0]['origin']['repository'])
        self.assertEqual(4, len(mit)); self.assertEqual(11, len(trio))
        objc2 = self.values['objc2@0.6.5']
        copied = [item for item in objc2.license_entries('synthetic/' + objc2.identity + '/')
                  if item['origin']['role'] == 'retained-copied-source-notice']
        self.assertEqual({'LICENSE-MIT', 'LICENSE-APACHE', 'COPYRIGHT'}, {item['origin']['path'] for item in copied})
        self.assertTrue(all(item['origin']['raw_commit_verified'] is False for item in copied))

    def test_later_mads_text_yearless_steven_and_rust_pr_origins_remain_distinct(self):
        later = self.data['mads']['origin']['revision']
        self.assertEqual('ee9a7ada2131f5944b8750428e265c15632f2a19', later)
        self.assertTrue(all(row['source_origin']['revision'] != later for row in self.data['packages']))
        steven = self.data['steven']['notice_file']
        self.assertEqual('Copyright (c) Steven Sheldon', steven['copyright_literal'])
        self.assertIn(b'Copyright (c) Steven Sheldon', self.contents[steven['catalog_path']])
        self.assertEqual(3, len({active.RUST_REVISION, active.RUST_HEAD, active.RUST_MERGE}))
        research = {Path(item['catalog_path']).name: gate.load_json_bytes(self.contents[item['catalog_path']])
                    for item in self.data['research_files']}
        self.assertEqual(5, len(research['objc2-issue23-comments.json']))
        self.assertEqual(11, len(research['objc2-issue826-comments.json']))

    def test_rust_api_raw_publisher_or_merge_promotions_refuse(self):
        for field, value in (('raw_commit_verified', True), ('publisher_signature_verified', True),
                             ('fixed_revision_equals_PR_head_or_merge', True), ('revision', active.RUST_MERGE)):
            changed = copy.deepcopy(self.data['rust'])
            changed['origin'][field] = value
            with self.subTest(field=field), self.assertRaises(gate.InvalidArtifact):
                active.rust_notices(held_reader(self.contents), changed)

    def test_rust_holderless_mit_cannot_drop_full_copyright(self):
        changed = copy.deepcopy(self.data['rust'])
        changed['notice_files'] = [record for record in changed['notice_files'] if record['path'] != 'COPYRIGHT']
        with self.assertRaises(gate.InvalidArtifact):
            active.rust_notices(held_reader(self.contents), changed)
        source = self.data['rust']['copy_source']
        self.assertIn(b'https://github.com/rust-lang/rust/pull/138944', self.contents[source['catalog_path']])

    def test_generated_source_symlink_lock_and_gitignore_limits_cannot_be_promoted(self):
        fields = ('Git_generated_directory_symlink_targets_verified', 'generated_SDK_source_equivalence_verified',
                  'Cargo_lock_generation_provenance_verified', 'gitignore_is_generated_exclusion_proof')
        for field in fields:
            changed = copy.deepcopy(self.data['source_classification'])
            changed[field] = True
            with self.subTest(field=field), self.assertRaises(gate.InvalidArtifact):
                active.source_classification(held_reader(self.contents), changed, self.data['packages'])
        forwarding = [item for item in self.data['source_classification']['source_blobs'] if item['path'] == 'symlink-target']
        self.assertEqual(1, len(forwarding))
        self.assertEqual(b'../../../../crates/objc2/src/rc/retained_forwarding_impls.rs',
                         self.contents[forwarding[0]['catalog_path']])

    def test_immutable_snapshot_owns_state_and_exports_are_detached(self):
        original = next(iter(self.values.values()))
        manifest, contents = primitives._plain(original.manifest), dict(original.contents)
        held = active.AdoptedObjc2Supplement(original.identity, manifest, contents)
        expected = held.material_record('synthetic/' + original.identity + '/')
        manifest['package']['checksum'] = '0' * 64
        contents['manifest.json'] = b'Synthetic mutation.\n'
        self.assertEqual(expected, held.material_record('synthetic/' + original.identity + '/'))
        with self.assertRaises(TypeError): held.manifest['package']['checksum'] = '0' * 64
        with self.assertRaises(TypeError): held.contents['manifest.json'] = b'mutation'
        with self.assertRaises(FrozenInstanceError): held.identity = 'mutation'
        emitted = held.material_record('synthetic/' + original.identity + '/')
        emitted['source_origin']['revision'] = 'synthetic mutation'
        self.assertEqual(expected, held.material_record('synthetic/' + original.identity + '/'))

    def test_exact_shared_public_pool_is_emitted_once_per_module(self):
        outputs = []
        for value in self.values.values():
            prefix = 'META-INF/nativecmpkit/native-dependencies/calf-share/' + value.identity + '/'
            pool = value.provenance_payloads(prefix)
            self.assertEqual(147, len(pool))
            self.assertTrue(all('/_reviewed-objc2/' in path for path in pool))
            outputs.append(pool)
        self.assertTrue(all(pool == outputs[0] for pool in outputs[1:]))
        self.assertEqual(1670040, sum(map(len, outputs[0].values())))
        with self.assertRaises(gate.InvalidArtifact):
            next(iter(self.values.values())).provenance_payloads('synthetic/foreign-package/')

    def test_set_loader_holds_once_and_foreign_or_duplicate_requests_refuse(self):
        packages = [primitives._plain(value.manifest['package']) for value in self.values.values()]
        with mock.patch.object(active, 'load_adopted_set', return_value=self.values) as load:
            self.assertEqual(self.values, supplements.load_supplements(CATALOG, packages, source_root=ROOT))
            self.assertEqual(1, load.call_count)
        for rows in (packages + [packages[0]], [packages[0] | {'checksum': '0' * 64}]):
            with self.subTest(rows=len(rows)), mock.patch.object(active, 'load_adopted_set', return_value=self.values), \
                    self.assertRaises(gate.InvalidArtifact):
                supplements.load_supplements(CATALOG, rows, source_root=ROOT)

    def test_carriage_dependency_closure_and_three_inert_sources_are_unchanged(self):
        self.assertEqual(15, len(carriage.CONSUMER_FILES)); self.assertEqual(7, len(carriage.CHECKER_MODULES))
        self.assertIn('native_license_objc2_material.py', carriage.CONSUMER_FILES)
        self.assertIn('native_license_material_v2.py', carriage.CONSUMER_FILES)
        imports = {node.names[0].name for node in ast.walk(ast.parse(carriage.SMOKE_SOURCE))
                   if isinstance(node, ast.Import)}
        self.assertIn('hashlib', imports)
        literal = next(node.value for node in ast.walk(ast.parse(carriage.SMOKE_SOURCE))
                       if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'modules'
                                                               for target in node.targets))
        self.assertEqual(carriage.CHECKER_MODULES, ast.literal_eval(literal))
        held = {'native_license_material_v2.py': 'ec1b4c313997bbd9f903f74ad91338fdf611f01f09b25b9952a9e78a733a0b32',
                'native_license_material_v2.schema.json': 'f097086121f6b87926ca17300e9510ab5c97b42cd49bfcedd7c10a8589067a51',
                'test_native_license_material_v2.py': '0281403a39a55bc254ab2ffcf5712cc10c7d64b541d2a4ee2d08383d935b4a67'}
        for name, expected in held.items():
            self.assertEqual(expected, hashlib.sha256((ROOT / 'tests/consumer' / name).read_bytes()).hexdigest())
        for name, expected in carriage.PRESERVED_CONSUMER_INPUTS.items():
            self.assertEqual(expected, hashlib.sha256((ROOT / 'tests/consumer' / name).read_bytes()).hexdigest())


class SyntheticFlowAndOriginalRefusalTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.output = self.root / 'owned-output'

    def fixture(self):
        values, archives, packages = {}, {}, []
        cache = self.root / 'synthetic-cache'; cache.mkdir()
        for name in ('objc2', 'block2'):
            value, raw, package = synthetic_supplement(name)
            path = cache / (value.identity + '.crate'); path.write_bytes(raw)
            values[package['id']], archives[package['id']] = value, path
            packages.append(package)
        source = self.root / 'synthetic-source'; native = source / 'calf-file-picker/native'
        native.mkdir(parents=True)
        (source / supplements.CATALOG_RELATIVE).mkdir(parents=True)
        (native / 'Cargo.toml').write_text('[package]\nname="calf-filepicker-native"\nversion="0.1.0"\n')
        lock = 'version = 4\n'
        for package in packages:
            lock += ('[[package]]\nname="' + package['name'] + '"\nversion="' + package['version'] + '"\n'
                     'source="registry+https://github.com/rust-lang/crates.io-index"\nchecksum="' + package['checksum'] + '"\n')
        (native / 'Cargo.lock').write_text(lock)
        metadata = metadata_fixture(manifest_hash=gate.sha256(native / 'Cargo.toml'), lock_hash=gate.sha256(native / 'Cargo.lock'))
        local = metadata['packages'][1]
        metadata['packages'] = packages + [local]
        metadata['resolve'] = [{'id': local['id'], 'dependencies': [package['id'] for package in packages]}]
        metadata['resolve'] += [{'id': package['id'], 'dependencies': []} for package in packages]
        path = self.root / 'synthetic-metadata.json'; path.write_bytes(encoded(metadata))
        return source, cache, path, values, archives, packages

    def test_synthetic_archive_identity_never_invokes_tar_and_changed_bytes_or_links_refuse(self):
        value, raw, _ = synthetic_supplement()
        path = self.root / 'synthetic.crate'; path.write_bytes(raw)
        with mock.patch('tarfile.open', side_effect=AssertionError('No archive scan in schema4')):
            supplements.verify_crate_correspondence(path, value)
            for changed in (raw + b'x', b'x' * len(raw)):
                path.write_bytes(changed)
                with self.assertRaises(gate.InvalidArtifact): supplements.verify_crate_correspondence(path, value)
            path.write_bytes(raw)
            other = self.root / 'owned-hardlink'; other.hardlink_to(path)
            with self.assertRaises(gate.InvalidArtifact): supplements.verify_crate_correspondence(path, value)
            other.unlink(); path.unlink(); path.symlink_to(self.root / 'absent-owned-file')
            with self.assertRaises(gate.InvalidArtifact): supplements.verify_crate_correspondence(path, value)

    def test_synthetic_collector_uses_finite_branch_and_writes_shared_proofs_once(self):
        source, cache, metadata, values, _, _ = self.fixture()
        writes = []
        original = Path.write_bytes
        def observe(path, raw):
            writes.append(str(path)); return original(path, raw)
        with mock.patch.object(collector, 'load_supplements', return_value=values), \
                mock.patch.object(collector, 'collect_archive', side_effect=AssertionError('No accepted payload replay')), \
                mock.patch('tarfile.open', side_effect=AssertionError('No tar replay')), \
                mock.patch.object(Path, 'write_bytes', observe):
            report = collector.collect(metadata, [cache], self.output,
                                       vcs_supplements=source / supplements.CATALOG_RELATIVE, source_root=source)
        self.assertIs(report['complete_material_collection'], True)
        self.assertIs(report['license_obligations_reviewed'], False)
        shared = [path for path in writes if '/_reviewed-objc2/' in path]
        self.assertEqual(2, len(shared)); self.assertEqual(2, len(set(shared)))
        self.assertEqual(3, len(report['packages']))

    def test_synthetic_conflicting_shared_pool_refuses_before_output(self):
        source, cache, metadata, values, _, _ = self.fixture()
        changed, _, _ = synthetic_supplement('block2', b'Synthetic conflicting proof.\n')
        values['block2@0.0.0'] = changed
        with mock.patch.object(collector, 'load_supplements', return_value=values), self.assertRaises(gate.InvalidArtifact):
            collector.collect(metadata, [cache], self.output,
                              vcs_supplements=source / supplements.CATALOG_RELATIVE, source_root=source)
        self.assertFalse(self.output.exists())

    def test_synthetic_verifier_compares_records_text_and_shared_proofs_without_repeat_reads(self):
        source, _, metadata_path, values, _, packages = self.fixture()
        metadata = metadata_path.read_bytes()
        prefix = 'META-INF/nativecmpkit/native-dependencies/calf-file-picker/'
        payloads = {prefix + 'metadata.json': metadata}
        report = {'schema_version': 1, 'module': 'calf-file-picker', 'complete_material_collection': True,
                  'gaps': [], 'license_obligations_reviewed': False, 'metadata_sha256': supplements.digest(metadata),
                  'cargo_toml_sha256': gate.sha256(source / 'calf-file-picker/native/Cargo.toml'),
                  'cargo_lock_sha256': gate.sha256(source / 'calf-file-picker/native/Cargo.lock'), 'packages': []}
        for package in packages:
            value = values[package['id']]; own = prefix + value.identity + '/'
            report['packages'].append({key: package[key] for key in ('name', 'version', 'source_kind', 'license', 'checksum')}
                                     | {'files': value.license_entries(own), 'external_vcs_material': value.material_record(own)})
            payloads.update(value.provenance_payloads(own)); payloads.update(value.license_payloads(own))
        local = gate.load_json_bytes(metadata)['packages'][-1]
        report['packages'].append({key: local[key] for key in ('name', 'version', 'source_kind', 'license', 'checksum')}
                                 | {'files': []})
        report_path = prefix + 'licenses-report.json'; payloads[report_path] = encoded(report)
        class HeldArchive:
            def __init__(self, current): self.payloads, self.reads = current, Counter()
            def read(self, path): self.reads[path] += 1; return self.payloads[path]
        def inspect(current):
            verifier = object.__new__(gate.ArtifactVerifier)
            verifier.root, verifier.checks = source, []
            archive = HeldArchive(current)
            with mock.patch.object(supplements, 'load_supplements', return_value=values):
                verifier.native_notices(archive, set(current), 'calf-file-picker', 'synthetic-not-artifact-acceptance')
            return verifier.checks, archive.reads
        checks, reads = inspect(payloads)
        self.assertTrue(checks and all(item['passed'] for item in checks), checks)
        self.assertEqual({1}, {count for path, count in reads.items() if '/_reviewed-objc2/' in path})
        for mode in ('proof', 'text', 'self-rehashed-record', 'false-origin', 'extra-file'):
            changed = dict(payloads)
            altered = copy.deepcopy(report)
            if mode == 'proof': changed[next(path for path in changed if '/_reviewed-objc2/manifest.json' in path)] += b'x'
            if mode in ('text', 'self-rehashed-record'):
                record = altered['packages'][0]['files'][0]
                changed[record['path']] += b'Synthetic corruption.\n'
                if mode == 'self-rehashed-record':
                    record.update(bytes=len(changed[record['path']]), sha256=supplements.digest(changed[record['path']]))
            if mode == 'false-origin': altered['packages'][0]['external_vcs_material']['obligations']['release_readiness_certified'] = True
            if mode == 'extra-file': changed[prefix + 'foreign-owner-file'] = b'Preserve this synthetic foreign file.\n'
            changed[report_path] = encoded(altered)
            with self.subTest(mode=mode):
                checks, _ = inspect(changed)
                self.assertTrue(any(not item['passed'] for item in checks), checks)

    def original_arguments(self, module):
        base = ROOT / 'docs/development/evidence/current-platform-recovery-20261101/native-stage-prerequisites20261104'
        report = (base / 'notices-current606' / (module + '-licenses-report.json')).read_bytes()
        metadata = (base / 'metadata-current606' / (module + '.json')).read_bytes()
        inputs = {path: (ROOT / path).read_bytes() for path in active.INPUT_PATHS}
        return report, metadata, inputs

    def test_independently_pinned_original_report_metadata_and_text_refusal_boundaries(self):
        for module in carry.ORIGINALS:
            report, metadata, inputs = self.original_arguments(module)
            never = mock.Mock(side_effect=AssertionError('Changed original must refuse before notice reads'))
            for changed_report, changed_metadata in ((report + b' ', metadata), (report, metadata + b' '),
                    (encoded(gate.load_json_bytes(report) | {'complete_material_collection': True}), metadata)):
                with self.subTest(module=module, boundary='independent pin'), self.assertRaises(gate.InvalidArtifact):
                    carry.validate_original(module, changed_report, changed_metadata, never, inputs)
            self.assertEqual(0, never.call_count)
            with self.subTest(module=module, boundary='complete text'), self.assertRaises(gate.InvalidArtifact):
                carry.validate_original(module, report, metadata, lambda path: b'Synthetic corrupted original notice.\n', inputs)

    def test_known_gap_cannot_use_missing_foreign_or_inert_v2_material(self):
        value, _, package = synthetic_supplement()
        own = 'META-INF/nativecmpkit/native-dependencies/calf-share/'
        report = {'packages': [{key: package[key] for key in ('name', 'version', 'source_kind', 'license', 'checksum')}
                                | {'files': []}], 'gaps': [{'package': value.identity}], 'license_obligations_reviewed': False}
        held = carry.AcceptedOriginal('calf-share', report, {}, {own + 'licenses-report.json': b'Synthetic original failure.\n'}, {})
        altered = primitives._plain(value.manifest); altered['package']['checksum'] = '0' * 64
        foreign = active.AdoptedObjc2Supplement(value.identity, altered, value.contents)
        inert = supplements.Supplement(value.identity, dict(value.manifest, schema_version=2), dict(value.contents))
        for materials in ({}, {package['id']: foreign}, {package['id']: inert}):
            with self.subTest(materials=len(materials)), \
                    mock.patch.object(carry, 'verify_crate_correspondence', side_effect=AssertionError('Refuse before archive access')), \
                    self.assertRaises(gate.InvalidArtifact):
                carry.assemble(held, materials, {package['id']: self.root / 'never-opened.crate'})

    def test_synthetic_assembly_preserves_original_failed_state_and_final_aggregate_bound(self):
        value, raw, package = synthetic_supplement()
        path = self.root / 'synthetic.crate'; path.write_bytes(raw)
        prefix = 'META-INF/nativecmpkit/native-dependencies/calf-share/'
        record = {key: package[key] for key in ('name', 'version', 'source_kind', 'license', 'checksum')} | {'files': []}
        report = {'packages': [record], 'gaps': [{'package': value.identity}],
                  'complete_material_collection': False, 'license_obligations_reviewed': False}
        payloads = {prefix + 'licenses-report.json': b'Synthetic failed original.\n', prefix + 'ordinary/LICENSE': b'Synthetic accepted old notice.\n'}
        held = carry.AcceptedOriginal('calf-share', report, {}, payloads, {})
        with mock.patch('tarfile.open', side_effect=AssertionError('No tar replay')):
            derived, outputs = carry.assemble(held, {package['id']: value}, {package['id']: path})
        self.assertIs(held.report['complete_material_collection'], False)
        self.assertEqual(1, len(held.report['gaps']))
        self.assertEqual(payloads[prefix + 'ordinary/LICENSE'], outputs[prefix + 'ordinary/LICENSE'])
        self.assertIs(derived['complete_material_collection'], True)
        self.assertIs(derived['license_obligations_reviewed'], False)
        self.assertIs(derived['carry_forward_evidence']['release_readiness_certified'], False)
        self.assertEqual(0, derived['carry_forward_evidence']['original_notice_payload_rescans'])
        report['packages'][0]['files'] = [{'path': 'synthetic mutation'}]
        payloads[prefix + 'ordinary/LICENSE'] = b'Synthetic mutation.\n'
        self.assertEqual((), held.report['packages'][0]['files'])
        with mock.patch.object(carry, 'MAX_ALL_BYTES', 500), self.assertRaises(gate.InvalidArtifact):
            carry.assemble(held, {package['id']: value}, {package['id']: path})

    def test_synthetic_new_writer_copies_exact_owned_files_and_refuses_existing_output(self):
        payloads = {'owned/LICENSE': b'Synthetic permission notice.\n', 'owned/report.json': b'{"synthetic":true}\n'}
        carry.write_new(self.output, payloads)
        self.assertEqual(payloads, {path.relative_to(self.output).as_posix(): path.read_bytes()
                                    for path in self.output.rglob('*') if path.is_file()})
        with self.assertRaises(gate.InvalidArtifact): carry.write_new(self.output, payloads)
        self.assertEqual(payloads['owned/LICENSE'], (self.output / 'owned/LICENSE').read_bytes())

    def test_output_alias_noncanonical_unsafe_and_overlapping_paths_refuse_before_touch(self):
        linked = self.root / 'linked-parent'; linked.symlink_to(self.root, target_is_directory=True)
        for output in (linked / 'never-created', self.root / 'unused/../never-created', Path('relative-owned-output')):
            with self.subTest(path=str(output)), self.assertRaises(gate.InvalidArtifact):
                carry.write_new(output, {'LICENSE': b'Synthetic notice.\n'})
        self.assertFalse((self.root / 'never-created').exists())
        for payloads in ({'../foreign': b'Synthetic notice.\n'}, {'a': b'x', 'a/b': b'y'}, {'LICENSE': b''}):
            with self.subTest(paths=list(payloads)), self.assertRaises(gate.InvalidArtifact): carry.write_new(self.output, payloads)
        self.assertFalse(self.output.exists())
        source = self.root / 'owned-source'; source.mkdir()
        with mock.patch.object(carry, 'capture_original', side_effect=AssertionError('No original read for overlapping output')):
            for output in (source / 'output', self.root, source):
                with self.subTest(overlap=str(output)), self.assertRaises(gate.InvalidArtifact):
                    carry.carry_forward(self.root / 'original', 'calf-share', source, [self.root / 'cache'], output)

    def test_owned_inventory_rejects_foreign_files_directories_and_links_without_deleting_them(self):
        self.output.mkdir(); (self.output / 'LICENSE').write_bytes(b'Synthetic owned notice.\n')
        carry.inventory(self.output, {'LICENSE'})
        foreign = self.output / 'foreign-owner-file'; foreign.write_bytes(b'Preserve foreign owner bytes.\n')
        with self.assertRaises(gate.InvalidArtifact): carry.inventory(self.output, {'LICENSE'})
        self.assertEqual(b'Preserve foreign owner bytes.\n', foreign.read_bytes()); foreign.unlink()
        extra = self.output / 'foreign-owner-directory'; extra.mkdir()
        with self.assertRaises(gate.InvalidArtifact): carry.inventory(self.output, {'LICENSE'})
        self.assertTrue(extra.is_dir()); extra.rmdir()
        linked = self.root / 'owned-hardlink'; linked.hardlink_to(self.output / 'LICENSE')
        with self.assertRaises(gate.InvalidArtifact): carry.inventory(self.output, {'LICENSE'})
        linked.unlink(); (self.output / 'LICENSE').unlink(); (self.output / 'LICENSE').symlink_to(self.root / 'absent')
        with self.assertRaises(gate.InvalidArtifact): carry.inventory(self.output, {'LICENSE'})


if __name__ == '__main__':
    unittest.main()
