# SPDX-License-Identifier: Apache-2.0
"""NEW4 narrow diagnostic controls; no original8/NEW9/120/Stop/JDK replay.

The only real transport boundary is an owned stdlib socketpair/HTTPResponse,
not remote HTTPS, Windows or an original766 causal reproduction. Other contexts
are genuine error/sanitization controls, never fake successful real responses.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import http.client
import json
import os
from pathlib import Path
import socket
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import windows_observer_one_request_diagnostic770 as diagnostic

SOURCE_ROOT = Path(os.environ.get('NATIVECMPKIT_DIAGNOSTIC_TEST_SOURCE_ROOT',
                                  str(Path(__file__).resolve().parents[2])))
MARKER = b'  # One-request diagnostic770: original120 is not replayed; no dependency admission.\n'


def failing(error):
    def operation(*args, **kwargs):
        raise error
    return operation


class WindowsOneRequestDiagnostic770Tests(unittest.TestCase):
    def test_NEW_owned_operation_errors_preserve_primary_and_bounded_integer_codes(self):
        for tag in sorted(diagnostic.TRANSPORT_OPERATIONS):
            with self.subTest(operation=tag):
                recorder = diagnostic.OperationRecorder()
                error = OSError(9, 'DO NOT EXPORT THIS EXCEPTION MESSAGE')
                error.winerror = 10038
                with self.assertRaises(OSError) as caught:
                    recorder.call(tag, failing(error))
                self.assertIs(caught.exception, error)
                self.assertEqual(recorder.errors, [{'operation': tag, 'errno': 9, 'winerror': 10038}])
                exported = json.dumps(recorder.errors)
                self.assertNotIn('MESSAGE', exported)
                self.assertNotIn('exception_type', exported)
        for errno, winerror in ((True, False), ('9', '10038'), (-(2**31)-1, 2**32), (None, None)):
            with self.subTest(errno=errno, winerror=winerror):
                error = OSError()
                error.errno, error.winerror = errno, winerror
                self.assertEqual(diagnostic.fault('response-read1', error),
                                 {'operation': 'response-read1', 'errno': None, 'winerror': None})
        primary, cleanup = OSError(9, 'PRIMARY MUST STAY PRIVATE'), OSError(5, 'CLEANUP MUST STAY PRIVATE')
        recorder = diagnostic.OperationRecorder()
        for tag, error in (('response-read1', primary), ('response-close', cleanup)):
            with self.assertRaises(OSError) as caught:
                recorder.call(tag, failing(error))
            self.assertIs(caught.exception, error)
        self.assertEqual(recorder.errors[0]['operation'], 'response-read1')
        self.assertEqual(recorder.errors[1]['operation'], 'response-close')
        for _ in range(diagnostic.MAX_ERRORS + 1):
            with self.assertRaises(OSError):
                recorder.call('response-read1', failing(primary))
        self.assertEqual(len(recorder.errors), diagnostic.MAX_ERRORS)
        self.assertTrue(recorder.overflow)
        with self.assertRaises(diagnostic.base.ObservationRefusal):
            recorder.call('last-operation-guessed', failing(primary))

    def test_NEW_real_httpresponse_full_read_close_boundary_is_attributed_not_original766_cause(self):
        body = b'owned-close-boundary-24!'
        self.assertEqual(len(body), 24)
        owner, peer = socket.socketpair()
        response = None
        recorder = diagnostic.OperationRecorder()
        class Phase:
            timeout_operation = 'transport-settimeout-body'
        transport = diagnostic.DelegatingTransport(owner, recorder, Phase())
        try:
            peer.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 24\r\nConnection: close\r\n\r\n' + body)
            peer.shutdown(socket.SHUT_WR)
            response = http.client.HTTPResponse(owner)
            response.begin()
            self.assertTrue(response.will_close)
            owner.close()  # Real getresponse Connection-close ownership boundary.
            delegated = diagnostic.DelegatingResponse(response, recorder)
            self.assertEqual(delegated.read1(24), body)
            self.assertTrue(response.isclosed())
            self.assertEqual(response.length, 0)
            self.assertEqual(owner.fileno(), -1)
            with self.assertRaises(OSError) as caught:
                transport.settimeout(0.25)
            self.assertEqual(recorder.errors, [{
                'operation': 'transport-settimeout-body',
                'errno': caught.exception.errno,
                'winerror': diagnostic.bounded_error_number(caught.exception, 'winerror', 0, 2**32 - 1),
            }])
            self.assertIsInstance(caught.exception.errno, int)
            self.assertEqual(caught.exception.errno, 9)
            self.assertEqual(len(recorder.errors), 1)
        finally:
            if response is not None:
                response.close()
            owner.close()
            peer.close()
        self.assertEqual(owner.fileno(), -1)
        self.assertEqual(peer.fileno(), -1)
        # Local POSIX/stdlib evidence never fills original766's missing errno.
        self.assertFalse(diagnostic.NO_ADMISSION['native_or_ordinary_consumer_qualified'])

    def test_NEW_sanitized_refusal_unknown_error_and_cleanup_never_promote_HTTP200(self):
        observed = dict(diagnostic.REQUEST, status='refused', http_status=200, body_bytes=24,
                        body_sha256=hashlib.sha256(b'owned-close-boundary-24!').hexdigest(),
                        complete_response=False, public_text_qualified=False, exception_type='OSError',
                        exception_message='NEVER EXPORT THE MESSAGE', headers={'Authorization': 'NEVER EXPORT THE HEADER'})
        recorder = diagnostic.OperationRecorder()
        for tag, error in (('transport-settimeout-body', OSError(9, 'NEVER EXPORT THE PRIMARY')),
                           ('response-close', OSError(5, 'NEVER EXPORT THE CLEANUP'))):
            with self.assertRaises(OSError):
                recorder.call(tag, failing(error))
        row = diagnostic.sanitize_observation(observed, recorder)
        self.assertEqual(set(row), diagnostic.OBSERVATION_KEYS)
        self.assertEqual(row['primary_errors'], [{'operation': 'transport-settimeout-body', 'errno': 9, 'winerror': None}])
        self.assertEqual(row['cleanup_errors'], [{'operation': 'response-close', 'errno': 5, 'winerror': None}])
        self.assertFalse(row['complete_response'])
        self.assertFalse(row['public_text_qualified'])
        self.assertFalse(row['raw_body_exported'])
        self.assertFalse(row['original766_cause_qualified'])
        self.assertTrue(row['body_retained_privately'])
        exported = json.dumps(row, sort_keys=True)
        for token in ('https://', 'url', 'headers', 'Authorization', 'NEVER EXPORT', 'exception_message', 'exception_type'):
            self.assertNotIn(token, exported)
        unknown = diagnostic.sanitize_observation(observed, diagnostic.OperationRecorder())
        self.assertTrue(unknown['unattributed_refusal'])
        self.assertEqual(unknown['primary_errors'], [])
        self.assertEqual(unknown['cleanup_errors'], [])
        self.assertFalse(unknown['public_text_qualified'])
        changed = copy.deepcopy(row)
        changed['headers'] = {}
        with self.assertRaises(diagnostic.base.ObservationRefusal):
            diagnostic.validate_diagnostic_observation(changed)
        changed = copy.deepcopy(row)
        changed['primary_errors'][0]['errno'] = True
        with self.assertRaises(diagnostic.base.ObservationRefusal):
            diagnostic.validate_diagnostic_observation(changed)
        changed = copy.deepcopy(row)
        changed['public_text_qualified'] = True
        with self.assertRaises(diagnostic.base.ObservationRefusal):
            diagnostic.validate_diagnostic_observation(changed)
        self.assertTrue(diagnostic.NO_ADMISSION['observations_are_untrusted'])
        self.assertIsNone(diagnostic.NO_ADMISSION['reviewed_expectations_authority'])
        for key, value in diagnostic.NO_ADMISSION.items():
            if key not in ('observations_are_untrusted', 'reviewed_expectations_authority'):
                self.assertIs(value, False)

    def test_CHANGED_route_inverse_fixed_row_and_NEW_worker_lifecycle_source(self):
        plan, plan_identity = diagnostic.load_plan(SOURCE_ROOT)
        self.assertEqual(plan_identity['sha256'], diagnostic.base.PLAN_SHA256)
        self.assertEqual(diagnostic.select_fixed_request(plan), plan['requests'][0])
        self.assertEqual(len(plan['requests']), 120)
        for mutation in ('shortened', 'different-first-id', 'duplicate-first-id'):
            changed = copy.deepcopy(plan)
            if mutation == 'shortened':
                changed['requests'] = changed['requests'][:1]
            elif mutation == 'different-first-id':
                changed['requests'][0]['id'] = 'caller-selected:pom'
            else:
                changed['requests'][1] = copy.deepcopy(changed['requests'][0])
            with self.subTest(mutation=mutation), self.assertRaises(diagnostic.base.ObservationRefusal):
                diagnostic.select_fixed_request(changed)
        workflow = diagnostic.read_regular(SOURCE_ROOT, '.github/workflows/javafx-library-candidate.yml')[0]
        self.assertEqual(workflow.count(MARKER), 1)
        restored = diagnostic.base.restore_diagnostic_workflow770(workflow)
        self.assertEqual((len(restored), diagnostic.digest(restored)),
                         (13748, '5f5b2ed46adaf900f157d5dab37b04087226ecd27e1cedbec88912999d574a9f'))
        self.assertEqual(diagnostic.base.restore_diagnostic_workflow770(restored), restored)
        prefix, suffix = workflow.split(MARKER)
        mutations = (
            prefix + MARKER + suffix.replace(b"python-version: '3.12'", b"python-version: '3.11'", 1),
            workflow.replace(b', windows-observer-one-request-diagnostic1]', b']', 1),
            workflow.replace(b'  public-stop:', b'  public-stop-altered:', 1),
            workflow + MARKER,
        )
        for mutation in mutations:
            with self.subTest(mutation_digest=diagnostic.digest(mutation)):
                self.assertNotEqual(mutation, workflow)
                with self.assertRaises(diagnostic.base.ObservationRefusal):
                    diagnostic.base.restore_diagnostic_workflow770(mutation)
        source = diagnostic.read_regular(SOURCE_ROOT, diagnostic.OBSERVER)[0].decode('utf-8')
        body_original = "        while True:\n            transport.settimeout(min(IO_SECONDS, bounded_time(deadline, 'Request body budget', budget.clock)))\n"
        body_lifetime = "        while True:\n            remaining = bounded_time(deadline, 'Request body budget', budget.clock)\n            # read1 may release the owning response fp and its borrowed socket.\n            # Closed lifetime skips only settimeout: still read EOF, keep caps,\n            # framing/declared-length checks and the shared deadline unchanged.\n            if not response.isclosed():\n                transport.settimeout(min(IO_SECONDS, remaining))\n"
        self.assertEqual(source.count(body_lifetime), 1)
        self.assertNotIn(body_original, source)
        source = source.replace(body_lifetime, body_original, 1)
        tree = ast.parse(source)
        inverse = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and
                       node.name == 'restore_diagnostic_workflow770')
        block = ast.get_source_segment(source, inverse) + '\n\n\n'
        self.assertEqual(source.count(block), 1)
        original_source = source.replace(block, '', 1).replace(
            '    workflow = restore_diagnostic_workflow770(workflow)\n', '', 1).encode('utf-8')
        self.assertEqual((len(original_source), diagnostic.digest(original_source)),
                         (63397, 'd73c253d6ffe75ed454f14e2888aaacf9b6dd6e6af5d09e2811c71c781d9ada6'))
        held = diagnostic.snapshot_sources(SOURCE_ROOT, plan)
        self.assertEqual(len(held), 18)
        self.assertEqual(held[diagnostic.OBSERVER]['sha256'], diagnostic.OBSERVER_SHA256)
        self.assertEqual(held[diagnostic.base.PLAN]['sha256'], diagnostic.base.PLAN_SHA256)
        own = diagnostic.read_regular(SOURCE_ROOT, 'scripts/ci/windows_observer_one_request_diagnostic770.py')[0].decode()
        own_tree = ast.parse(own)
        functions = {node.name: ast.get_source_segment(own, node) for node in own_tree.body if isinstance(node, ast.FunctionDef)}
        worker = functions['worker']
        self.assertLess(worker.index("readline(16) == b'GO742"), worker.index('base.verify_worker_job(job_handle)'))
        self.assertLess(worker.index('base.verify_worker_job(job_handle)'), worker.index('base.observe_one('))
        self.assertEqual(worker.count('base.observe_one('), 1)
        self.assertNotIn("for index, row in enumerate(plan['requests'])", worker)
        self.assertIn("budget.requests == 1", worker)
        self.assertIn("'private/only-response.bin'", worker)
        self.assertIn("'public/worker-diagnostic.json'", worker)
        controller = functions['controller']
        for required in ("job = WindowsJob()", "job.inherit(True)", "startup.lpAttributeList = {'handle_list': [int(job.handle)]}",
                         "job.inherit(False)", 'assigned_go(process, job)', 'job.active_processes() <= 1',
                         'job.terminate()', 'job.active_processes()', 'job.close()', 'before == after',
                         'job_empty and direct_terminal and not any(thread.is_alive() for thread in threads)',
                         'path.rmdir()'):
            self.assertIn(required, controller)
        self.assertNotIn('shutil.rmtree', own)
        self.assertNotIn('exception_type', own)
        self.assertNotIn('str(error)', own)
        self.assertNotIn('repr(error)', own)
        self.assertIn("'NATIVECMPKIT_DIAGNOSTIC_PLATFORM'", functions['manual_context'])
        self.assertEqual(diagnostic.TOTAL_SECONDS, 90)
        self.assertEqual(diagnostic.CLEANUP_SECONDS, 30)
        self.assertIn('public/*.json', suffix.decode())
        self.assertIn('contents: read', suffix.decode())
        self.assertIn('persist-credentials: false', suffix.decode())
        self.assertIn('run: python -I -S -B scripts/ci/windows_observer_one_request_diagnostic770.py', suffix.decode())
        for forbidden in ('private/', 'setup-java', 'setup-android', 'gradle/actions', 'cache@'):
            self.assertNotIn(forbidden, suffix.decode())


if __name__ == '__main__':
    unittest.main()
