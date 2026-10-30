"""Owning profile PID/readiness regressions; synthetic tooling, never native/profile passes."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import apple_image_profile as image
import ios_ui_application as app
import library_tests as lt
import workflow_matrix as matrix
import test_ios_ui_application as frames
import test_apple_image_profile as profile_fixtures
import test_ios_application_receipts as receipt_fixtures

BUNDLE = 'io.github.apdelrahman1911.nativecmpkit.verification.ui.r' + 'a' * 12 + '.t' + 'b' * 32
PID = 12345


class ImageProfileReadinessTests(unittest.TestCase):
    def protocol(self):
        protocol = app.NativeProtocol(BUNDLE)
        protocol.feed(frames.ACTIVE)
        protocol.feed(frames.frame('testSuiteStarted', name=app.IMAGE_PROFILE_CASE[0]))
        protocol.feed(frames.frame('testStarted', name=app.IMAGE_PROFILE_CASE[1]))
        return protocol

    def driver_fixture(self):
        fixture = profile_fixtures.AppleImageProfileTests('test_real_selected_pid_and_owned_bytes_are_required_and_only_safe_summary_survives')
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        fixture.prepare()
        return fixture

    def test_owned_native_pid_starts_the_attempt_while_its_case_is_open_not_after_buffered_launch_header(self):
        protocol = app.NativeProtocol(BUNDLE)
        requests = []
        protocol.image_profile_request = requests.append
        protocol.feed(frames.ACTIVE)
        protocol.feed(frames.frame('testSuiteStarted', name=app.IMAGE_PROFILE_CASE[0]))
        protocol.feed(frames.frame('testStarted', name=app.IMAGE_PROFILE_CASE[1]))
        protocol.feed('NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=12345')
        self.assertEqual([PID], requests, 'The actual native ready PID must not await simctl console buffering')
        self.assertIsNone(protocol.observed_launch_pid)
        protocol.feed('NATIVECMPKIT_IMAGE_PROFILE phase=complete rounds=23')
        protocol.feed(frames.frame('testFinished', name=app.IMAGE_PROFILE_CASE[1]))
        protocol.feed(frames.frame('testSuiteFinished', name=app.IMAGE_PROFILE_CASE[0]))
        protocol.feed(frames.COMPLETE)
        protocol.feed(BUNDLE + ': 12345')
        self.assertEqual([PID], requests, 'A late header must not duplicate or start a completed allocation attempt')
        self.assertEqual(PID, protocol.finish(0)['observed_launch_pid'])

    def test_missing_foreign_malformed_or_duplicate_native_pid_cannot_start_or_complete_the_attempt(self):
        for marker in ('NATIVECMPKIT_IMAGE_PROFILE phase=ready',
                       'NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=0',
                       'NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=2147483648',
                       'NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=true',
                       'NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=12345 rounds=1'):
            with self.subTest(marker=marker), self.assertRaises(ValueError): self.protocol().feed(marker)
        protocol = self.protocol(); protocol.feed(BUNDLE + ': 54321')
        with self.assertRaises(ValueError): protocol.feed('NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=12345')
        protocol = self.protocol(); protocol.feed('NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=12345')
        with self.assertRaises(ValueError): protocol.feed(BUNDLE + ': 54321')
        with self.assertRaises(ValueError): protocol.feed('NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=12345')

    def test_failed_or_closed_case_and_late_header_never_start_a_postmortem_profile(self):
        protocol = self.protocol()
        requests = []
        protocol.image_profile_request = requests.append
        protocol.feed(frames.frame('testFailed', name=app.IMAGE_PROFILE_CASE[1], message='Controlled failed workload'))
        with self.assertRaises(ValueError): protocol.feed('NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=12345')
        protocol.feed(frames.frame('testFinished', name=app.IMAGE_PROFILE_CASE[1]))
        protocol.feed(frames.frame('testSuiteFinished', name=app.IMAGE_PROFILE_CASE[0]))
        protocol.feed(frames.COMPLETE)
        protocol.feed(BUNDLE + ': 12345')
        self.assertEqual([], requests)

    def test_real_transport_polls_owned_readiness_before_any_buffered_console_frames(self):
        fixture = self.driver_fixture()
        driver = fixture.driver
        protocol = app.NativeProtocol(profile_fixtures.BUNDLE)
        protocol.image_profile_request = driver.observe_native_request
        protocol.image_profile_poll = driver.poll
        lines = [frames.ACTIVE, frames.frame('testSuiteStarted', name=app.IMAGE_PROFILE_CASE[0]),
                 frames.frame('testStarted', name=app.IMAGE_PROFILE_CASE[1]),
                 'NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=12345',
                 'NATIVECMPKIT_IMAGE_PROFILE phase=complete rounds=23',
                 frames.frame('testFinished', name=app.IMAGE_PROFILE_CASE[1]),
                 frames.frame('testSuiteFinished', name=app.IMAGE_PROFILE_CASE[0]), frames.COMPLETE,
                 profile_fixtures.BUNDLE + ': 12345']
        # Genuine small Python pipe/file handoff; explicitly synthetic native PID, native
        # frames, installed bytes and Apple tool results. This is NOT a native/profile run.
        child = '''import json,os,sys,time
from pathlib import Path
ready,ack=map(Path,sys.argv[1:3])
fd=os.open(ready,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
try: os.write(fd,b"process_id=12345\\n")
finally: os.close(fd)
limit=time.monotonic()+4
while not ack.exists():
 if time.monotonic()>limit: sys.exit(17)
 time.sleep(.01)
for line in json.loads(sys.argv[3]): print(line,flush=True)
'''
        starts_before_console = []
        def execute(*args):
            starts_before_console.append(protocol.active is None)
            return fixture.execute(*args)
        output = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')
        with patch.object(app.lt, 'ROOT', fixture.root), patch.object(app.shutil, 'disk_usage', return_value=Mock(free=16 * 1024**3)), \
                patch.object(image.lt, 'execute', side_effect=execute), patch.object(app.sys, 'stdout', output):
            result = app.forward_application([sys.executable, '-B', '-c', child, str(driver.ready), str(driver.ack), json.dumps(lines)], protocol, timeout=6)
        self.assertTrue(starts_before_console and all(starts_before_console), 'No console flush/header is needed to start actual owned profiling')
        self.assertEqual(1, result['counts']['passed'])
        self.assertEqual(PID, driver.receipt['process_id'])
        self.assertTrue(driver.receipt['native_console_pid_correlated'])
        driver.close()
        self.assertTrue(image.validate_attempt(driver.receipt, profile_fixtures.DEVICE, profile_fixtures.BUNDLE))
        self.assertFalse(driver.ready.exists())

    def test_missing_readiness_never_profiles_and_unsafe_file_modes_aliases_or_payloads_fail_closed(self):
        fixture = self.driver_fixture()
        fixture.driver.poll()
        self.assertFalse(fixture.driver.started)
        with self.assertRaises(ValueError): fixture.driver.request(PID)
        self.assertEqual([], fixture.commands)
        for payload, mode in ((b'process_id=0\n', 0o600), (b'process_id=2147483648\n', 0o600),
                              (b'process_id=12345\nextra', 0o600), (b'x' * 65, 0o600),
                              (b'process_id=12345\n', 0o644)):
            fixture.driver.ready.write_bytes(payload); fixture.driver.ready.chmod(mode)
            with self.assertRaises(ValueError): fixture.driver.poll()
            self.assertFalse(fixture.driver.started)
            self.assertEqual(payload, fixture.driver.ready.read_bytes())
            fixture.driver.ready.unlink()  # Only these known deliberately invalid test fixtures.
        foreign = fixture.root / 'preserve-ready'; foreign.write_text('preserve')
        fixture.driver.ready.symlink_to(foreign)
        with self.assertRaises(ValueError): fixture.driver.poll()
        fixture.driver.close()
        self.assertEqual('preserve', foreign.read_text())
        self.assertTrue(fixture.driver.ready.is_symlink())
        self.assertFalse(image.validate_attempt(fixture.driver.receipt, profile_fixtures.DEVICE, profile_fixtures.BUNDLE))

    def test_native_and_file_pid_must_match_and_changed_owned_witness_is_preserved(self):
        fixture = self.driver_fixture()
        fixture.driver.native_console_pid = 54321
        fixture.driver.ready.write_text('process_id=12345\n'); fixture.driver.ready.chmod(0o600)
        with self.assertRaises(ValueError): fixture.driver.poll()
        self.assertEqual([], fixture.commands)
        fixture.driver.ready.unlink(); fixture.driver.native_console_pid = None
        fixture.request()
        fixture.driver.ready.write_text('process_id=54321\n')
        fixture.driver.close()
        self.assertTrue(fixture.driver.ready.exists())
        self.assertFalse(fixture.driver.receipt['profile_passed'])

    def test_preflight_failure_names_the_fixed_stage_without_exporting_raw_process_text_or_paths(self):
        for failure, stage, reason in (('app', 'verify-installed-owned-app', 'installed-app-identity-mismatch'),
                                      ('missing', 'inspect-owned-process', 'selected-process-unavailable'),
                                      ('foreign', 'verify-owned-process-executable', 'selected-process-executable-mismatch')):
            fixture = self.driver_fixture(); original = fixture.control
            def control(command, timeout):
                result = original(command, timeout)
                if failure == 'app' and command[-1] == 'app': result.returncode = 7
                if failure == 'missing' and command[0] == '/bin/ps': result.returncode = 7
                if failure == 'foreign' and command[0] == '/bin/ps': result.stdout = b'/private/foreign-process-executable\n'
                return result
            fixture.driver.control = control
            fixture.request()
            error, = fixture.driver.receipt['errors']
            self.assertEqual((stage, reason), (error['failure_stage'], error['failure_reason']))
            self.assertEqual([], fixture.commands)
            fixture.driver.close()
            self.assertNotIn('foreign-process-executable', json.dumps(fixture.driver.receipt))
            self.assertNotIn(str(fixture.data), json.dumps(fixture.driver.receipt))

    def test_one_failed_profile_workload_has_an_exact_explicit_darwin_recovery_not_accepted_stress_replay(self):
        row, = matrix.matrix('ios-image-profile-recovery')['include']
        self.assertEqual(('ios-iphone', 'calf-ui', lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS),
                         tuple(row[k] for k in ('slot', 'test-modules', 'test-focus')))
        plan = lt.plan(lt.ROOT, 'ios', only_modules=('calf-ui',), focus=lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS)
        self.assertFalse(plan['complete_suite_requested'])
        command = lt.gradle_command('ios', plan, frames.DEVICE)
        self.assertEqual(1, command.count('--tests'))
        self.assertEqual(app.IMAGE_PROFILE_CASE[0] + '.' + app.IMAGE_PROFILE_CASE[1], command[-1])
        self.assertIn('-PnativecmpkitImageMemoryDiagnostics=darwin-tools', command)
        self.assertNotIn('-PnativecmpkitImageMemoryDiagnostics=true', command)
        args = sorted(app.TEST_ARGUMENTS) + ['--ktest_gradle_filter=' + command[-1]]
        self.assertEqual(lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS, app.application_test_focus(args, 'darwin-tools'))
        with self.assertRaises(ValueError): app.application_test_focus(args)
        self.assertEqual(3, len(lt.ui_application_focus_identities(lt.IOS_IMAGE_MEMORY_FOCUS)))
        self.assertEqual(3, len(lt.ui_application_focus_identities(lt.IOS_IMAGE_DARWIN_FOCUS)))
        self.assertEqual(11, len(matrix.matrix('all')['include']))

    def test_profile_receipt_requires_exact_native_header_file_and_tool_pid_plus_original_cleanup(self):
        fixture = receipt_fixtures.IosApplicationReceipts('test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required')
        self.addCleanup(fixture.doCleanups); fixture.setUp()
        fixture.write(lt.IOS_IMAGE_MEMORY_SOURCE, (lt.ROOT / lt.IOS_IMAGE_MEMORY_SOURCE).read_bytes())
        fixture.plan = lt.plan(fixture.root, 'ios', only_modules=('calf-ui',), focus=lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS)
        cases = [{'classname': app.IMAGE_PROFILE_CASE[0], 'name': app.IMAGE_PROFILE_CASE[1], 'status': 'passed'}]
        fixture.document.update(explicit_test_focus=lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS, image_diagnostics_mode='darwin-tools',
                                strict_runtime_assertions_attested=False)
        fixture.document['application_protocol'].update(testcases=cases, counts=lt.case_counts(cases))
        fixture.modules[0]['testcases'] = fixture.xml_cases(cases); fixture.save()
        self.assertEqual([], fixture.collect()['errors'])
        original = copy.deepcopy(fixture.document)
        for change in (lambda d: d['application_protocol'].update(observed_launch_pid=54321),
                       lambda d: d['application_protocol']['image_profile_observations'][0].update(process_id=54321),
                       lambda d: d['image_memory_profile'].update(process_id=54321),
                       lambda d: d['image_memory_profile'].update(native_readiness_file_sha256='f' * 64),
                       lambda d: d['image_memory_profile'].update(owned_readiness_removed=False),
                       lambda d: d['image_memory_profile'].update(native_console_pid_correlated=False),
                       lambda d: d['cleanup'].update(owned_app_absence_verified=False),
                       lambda d: d.update(strict_runtime_assertions_attested=True)):
            fixture.document = copy.deepcopy(original); change(fixture.document); fixture.save()
            self.assertTrue(fixture.collect()['errors'])

    def test_native_handoff_keeps_original_gc_pixel_allocation_and_workload_bounds_and_accepted_bodies(self):
        source = (lt.ROOT / lt.IOS_IMAGE_MEMORY_SOURCE).read_text()
        for symbol in ('platform.posix.getpid()', 'platform.posix.O_EXCL', 'platform.posix.write(', 'platform.posix.close(',
                       'platform.posix.fflush(platform.posix.stdout)', 'import kotlinx.cinterop.usePinned',
                       'import kotlinx.cinterop.addressOf', 'NATIVECMPKIT_IMAGE_PROFILE_READY',
                       '210.seconds', 'rounds < 4096', 'rounds > 0', 'GC.collect()', 'assertSrgb(image)'):
            self.assertIn(symbol, source)
        original = subprocess.check_output(['git', 'show', 'b56ec9028747fdada79a124dea84379c2937d447:' + lt.IOS_IMAGE_MEMORY_SOURCE],
                                           cwd=lt.ROOT, text=True)
        start = '    @Test fun ' + lt.IOS_IMAGE_MEMORY_METHODS[0]
        end = '    /**\n     * Real conversions'
        self.assertEqual(original.split(start, 1)[1].split(end, 1)[0], source.split(start, 1)[1].split(end, 1)[0],
                         'The two actually accepted native stress methods are byte-identical, not rerun')
        self.assertEqual(original.split('    private class GcGate', 1)[1], source.split('    private class GcGate', 1)[1],
                         'Their shared production bridge/pixel/GC/Worker helpers stay byte-identical')


if __name__ == '__main__': unittest.main()
