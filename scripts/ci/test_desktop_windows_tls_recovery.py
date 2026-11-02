# SPDX-License-Identifier: Apache-2.0
"""NEW failed-only route/history guards; synthetic source/XML, not native TLS."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import desktop_windows_tls_source_projection as later
import desktop_policy_creation_source_projection as history
import desktop_security_plan as security
import library_tests as library
import workflow_matrix as matrix

ROOT = library.ROOT
PROFILE = security.WINDOWS_TLS_RECOVERY_PROFILE
FOCUS = security.WINDOWS_TLS_RECOVERY_FOCUS
TLS = security.SOURCE_PATHS['tls-rendering']
HELPER = security.TLS_HELPER
ORIGINAL_NATIVE_SHA256 = '00698c638a729549c890240b000e64cbd88be9f6ac32d4ca067b304b1443187c'


class DesktopWindowsTlsRecoveryControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = library.snapshot_inputs(ROOT)
        cls.bindings = later._bindings()

    @classmethod
    def tearDownClass(cls):
        if library.snapshot_inputs(ROOT) != cls.inputs:
            raise AssertionError('Held source inputs changed during NEW controls')

    def plan(self):
        return library.plan(ROOT, 'desktop', only_modules=('calf-webview',), focus=FOCUS)

    def test_six_exact_inverses_and_eleven_fragments_restore_original_complete_sources(self):
        self.assertEqual(6, len(self.bindings))
        self.assertEqual(11, sum(len(r['fragments']) for r in self.bindings.values()))
        for path, binding in self.bindings.items():
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes()
                prior = later.current_source_before_windows_tls(path, raw)
                self.assertEqual(binding['before_sha256'], hashlib.sha256(prior).hexdigest())
                self.assertEqual(binding['after_sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(prior, later.source_before_windows_tls(path, prior))
                forward = prior
                for fragment in binding['fragments']:
                    before, after = fragment['before'].encode(), fragment['after'].encode()
                    self.assertEqual(1, forward.count(before))
                    forward = forward.replace(before, after, 1)
                self.assertEqual(raw, forward)
        self.assertEqual(7, len(history._bindings()))
        self.assertEqual(18, sum(len(r['fragments']) for r in history._bindings().values()))
        self.assertEqual('51df07d4bab5a532747535d572e69c54ac289902935c6aecb6ef2b21b0950ce5', history.SPEC_SHA256)

    def test_current_history_admission_refuses_old_foreign_truncated_and_changed_images(self):
        for path in self.bindings:
            raw = (ROOT / path).read_bytes()
            prior = later.source_before_windows_tls(path, raw)
            for bad in (prior, raw[:-1], raw + b'\n', b'foreign', b''):
                with self.subTest(path=path, bytes=len(bad)), self.assertRaises(ValueError):
                    later.current_source_before_windows_tls(path, bad)
            for bad in (raw[:-1], raw + b'\n', b'foreign', b''):
                with self.subTest(path=path, bytes=len(bad)), self.assertRaises(ValueError):
                    later.source_before_windows_tls(path, bad)
        for bad in (None, bytearray(b'x'), [], 'text'):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(ValueError):
                later.current_source_before_windows_tls(HELPER, bad)
        with self.assertRaises(ValueError):
            later.source_before_windows_tls(HELPER, b'x' * (later.MAX_SOURCE_BYTES + 1))

    def test_old_policy_tls_and_root_readers_compose_without_repinning_or_native_substitution(self):
        for path, binding in history._bindings().items():
            restored = history.current_source_before_policy_creation(path, (ROOT / path).read_bytes())
            self.assertEqual(binding['before_sha256'], hashlib.sha256(restored).hexdigest())
            self.assertEqual(restored, history.source_before_policy_creation(path, restored))
        import test_desktop_tls_finished_write_recovery as old_tls
        restored = old_tls.source_contract()
        self.assertEqual(3, len(restored))
        import test_desktop_security_owned_root as owned
        self.assertTrue(owned.exact_owned_inner(owned.current_owned_script_for_history()))
        self.assertNotIn('desktop_windows_tls_source_projection', (ROOT / 'scripts/ci/desktop_security_plan.py').read_text())
        self.assertNotIn('desktop_policy_creation_source_projection', (ROOT / 'scripts/ci/desktop_security_plan.py').read_text())
        self.assertEqual(ORIGINAL_NATIVE_SHA256, hashlib.sha256((ROOT / TLS).read_bytes()).hexdigest())

    def test_only_the_original_failed_windows_tls_method_and_two_current_sources_are_selected(self):
        rows = matrix.matrix(PROFILE)['include']
        self.assertEqual([{'slot': 'desktop-windows-x64', 'suite': 'desktop', 'runner': 'windows-2025',
                          'arch': 'x64', 'python': 'python', 'test-modules': 'calf-webview', 'test-focus': FOCUS}], rows)
        plan = self.plan()
        item, = plan['expected']
        self.assertFalse(plan['complete_suite_requested'])
        self.assertEqual(['calf-webview'], plan['explicit_module_subset'])
        self.assertEqual([{'classname': security.SECURITY_CLASS, 'name': security.SECURITY_METHOD + '[desktop]'}], item['required_testcases'])
        self.assertEqual(1, item['required_original_xml'])
        self.assertEqual({TLS, HELPER}, set(item['test_source_files']))
        self.assertEqual(security.selected_sources(FOCUS), item['test_source_sha256'])
        self.assertTrue(library.validate_test_focus(plan))
        with patch('library_tests.platform.system', return_value='Windows'), patch('library_tests.platform.machine', return_value='AMD64'):
            command = library.gradle_command('desktop', plan, root=ROOT)
        self.assertEqual([security.SECURITY_CLASS + '.' + security.SECURITY_METHOD],
                         [command[i + 1] for i, arg in enumerate(command) if arg == '--tests'])
        self.assertEqual(1, command.count(':calf-webview:desktopTest'))
        self.assertEqual(1, command.count(security.INIT_SCRIPT))
        self.assertEqual(1, command.count('-PnativecmpkitDesktopSecurityFocus=' + FOCUS))

    def test_wrong_hosts_broadening_plan_and_current_native_source_mutations_are_refused(self):
        for system, arch in (('Linux', 'x86_64'), ('Linux', 'aarch64'), ('Darwin', 'arm64'), ('Windows', 'arm64'), (None, 'AMD64')):
            with self.subTest(system=system, arch=arch), self.assertRaises(ValueError):
                security.validate_host(system, arch, FOCUS)
        for slots in ((), ('desktop-linux-arm64',), ('desktop-windows-x64', 'desktop-linux-arm64'), ['desktop-windows-x64']):
            with self.subTest(slots=slots), patch.dict(matrix.PROFILES, {PROFILE: slots}), self.assertRaises(ValueError):
                matrix.matrix(PROFILE)
        with patch.dict(matrix.MODULE_SUBSETS, {PROFILE: 'calf-io'}), self.assertRaises(ValueError):
            matrix.matrix(PROFILE)
        for field, value in (('runner', 'ubuntu-24.04'), ('arch', 'arm64'), ('suite', 'android-device')):
            slots = tuple(dict(row) for row in matrix.SLOTS)
            next(row for row in slots if row['slot'] == 'desktop-windows-x64')[field] = value
            with self.subTest(field=field), patch.object(matrix, 'SLOTS', slots), self.assertRaises(ValueError):
                matrix.matrix(PROFILE)
        for key, value in (('required_original_xml', 3), ('required_testcases', []), ('task', ':calf-webview:publish'), ('test_filter', '*')):
            plan = copy.deepcopy(self.plan()); plan['expected'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                library.validate_test_focus(plan)
        ordinary_read = Path.read_bytes
        for path in (TLS, HELPER, security.INIT_SCRIPT):
            target = ROOT / path
            def changed(file):
                raw = ordinary_read(file)
                return raw + b'\n' if file == target else raw
            with self.subTest(path=path), patch.object(Path, 'read_bytes', autospec=True, side_effect=changed), self.assertRaises(ValueError):
                security.fixture_contract(ROOT, FOCUS)

    def test_strict_single_case_worker_parser_still_refuses_missing_replayed_or_failed_results(self):
        prefix = 'NATIVECMPKIT_DESKTOP_SECURITY_'; classname = security.SECURITY_CLASS
        lines = [prefix + 'SETUP task=:calf-webview:desktopTest focus=' + FOCUS + ' forks=1 forkEvery=1 classes=1',
                 prefix + 'WORKER phase=start worker=7',
                 prefix + 'CASE phase=start worker=7 classname=' + classname,
                 prefix + 'CASE phase=finish worker=7 classname=' + classname + ' tests=1 passed=1 failed=0 skipped=0 result=SUCCESS',
                 prefix + 'WORKER phase=finish worker=7 tests=1 passed=1 failed=0 skipped=0 result=SUCCESS']
        with tempfile.TemporaryDirectory(prefix='explicitly-synthetic-windows-tls-events-') as folder:
            path = Path(folder) / 'synthetic-events.log';path.write_text('\n'.join(lines) + '\n')
            report = security.worker_observation(path, FOCUS)
            self.assertEqual(1, len(report['selected_class_workers']))
            self.assertFalse(report['os_worker_pid_observed'])
            for bad in (lines[:-1], lines + [lines[-1]], [r.replace('passed=1 failed=0', 'passed=0 failed=1') for r in lines],
                        [r.replace('forkEvery=1', 'forkEvery=0') for r in lines], [lines[0], lines[2], lines[1], *lines[3:]]):
                path.write_text('\n'.join(bad) + '\n')
                with self.assertRaises(ValueError):
                    security.worker_observation(path, FOCUS)

    def test_no_graph_or_accepted_native_replay_and_workflow_permissions_remain_exact(self):
        path = '.github/workflows/gradle.yml'; raw = (ROOT / path).read_bytes()
        prior = later.current_source_before_windows_tls(path, raw).decode()
        current = raw.decode()
        self.assertEqual(prior, current.replace(PROFILE + ', ', '', 1))
        capture_if = next(r for r in current.splitlines() if "steps.plan.outcome == 'success'" in r and 'webview-desktop-security-regressions' in r)
        self.assertNotIn(PROFILE, capture_if)
        self.assertIn('permissions:\n  contents: read', current)
        self.assertIn('persist-credentials: false', current)
        self.assertNotIn('packages: write', current)
        self.assertNotIn('id-token: write', current)
        self.assertEqual(5, len(security.ROWS))
        self.assertEqual(14, sum(len(r['selected']) for r in security.ROWS))

    def test_only_known_windows_finished_write_is_added_without_confirming_native_rejection(self):
        source = (ROOT / HELPER).read_text()
        context = source.split('private fun observedFinishedWriteAbort(', 1)[1].split('private fun quarantineFinishedWrite(', 1)[0]
        self.assertIn('if (trusted || handshaken || phase != FailurePhase.Handshake || closing.get()) return false', context)
        self.assertIn('System.getProperty("os.name").startsWith("Windows")', context)
        classifier = source.split('internal fun observedDesktopTlsFinishedWrite(', 1)[1].split('internal enum class DesktopTlsStage', 1)[0]
        self.assertIn('javaFeature != 17 || error.javaClass != SocketException::class.java', classifier)
        self.assertIn('windows && error.message == "An established connection was aborted by the software in your host machine"', classifier)
        self.assertIn('error.message == "Broken pipe"', classifier)
        self.assertIn('frames.take(prefix.size) != prefix', classifier)
        self.assertIn('frames.windowed(caller.size).any { it == caller }', classifier)
        self.assertIn('closing.get() && pendingFinishedWrites.isNotEmpty() && !nativeRejectionConfirmed', source)
        self.assertIn('check(!trusted && !closing.get() && !nativeRejectionConfirmed)', source)
        self.assertIn('if (pendingFinishedWrites.size >= 16)', source)
        self.assertIn('RecordedFailure(FailurePhase.SocketClose, error)', source)
        self.assertNotIn('nativeRejectionConfirmed = true', classifier)
        self.assertEqual(ORIGINAL_NATIVE_SHA256, hashlib.sha256((ROOT / TLS).read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
