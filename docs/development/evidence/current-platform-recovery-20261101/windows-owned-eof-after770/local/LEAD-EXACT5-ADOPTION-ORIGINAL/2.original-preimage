# SPDX-License-Identifier: Apache-2.0
"""NEW8 grouped Stage-A source/mocked-transport controls, never native acceptance.

Only this new observer module is imported. The original native/controller/helper
and accepted8/12 tests remain read-only bytes. No network, DLL creation, subprocess
or tool execution belongs to these methods. Real Windows Job/HTTPS acquisition
requires a separately reviewed manual observational CI run.
"""
from __future__ import annotations

import ast
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import windows_ordinary_dependency_observer742 as observer

SOURCE_ROOT = Path(os.environ.get('NATIVECMPKIT_OBSERVER_TEST_SOURCE_ROOT', str(Path(__file__).resolve().parents[2])))


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


class FakeSocket:
    def __init__(self, events):
        self.events = events

    def settimeout(self, timeout):
        self.events.append(('timeout', timeout))


class FakeResponse:
    def __init__(self, body, events, status=200, headers=None, clock=None, tick=0.0):
        self.body, self.position, self.events = body, 0, events
        self.status = status
        self.headers = [('Content-Length', str(len(body)))] if headers is None else headers
        self.clock, self.tick = clock, tick
        self.closed = False

    def getheaders(self):
        self.events.append(('getheaders',))
        return self.headers

    def read1(self, count):
        self.events.append(('read1', count))
        if self.clock is not None:
            self.clock.value += self.tick
        piece = self.body[self.position:self.position + count]
        self.position += len(piece)
        return piece

    def close(self):
        self.closed = True
        self.events.append(('response-close',))


class FakeConnection:
    def __init__(self, response, events, hostname, **kwargs):
        self.response, self.events = response, events
        self.events.append(('factory', hostname, kwargs['port'], kwargs['timeout'], type(kwargs['context']).__name__))
        self.sock = FakeSocket(events)
        self.closed = False

    def connect(self):
        self.events.append(('connect',))

    def request(self, method, path, body, headers):
        self.events.append(('request', method, path, body, dict(headers)))

    def getresponse(self):
        self.events.append(('getresponse',))
        return self.response

    def close(self):
        self.closed = True
        self.events.append(('connection-close',))


class InputPipe:
    def __init__(self, events):
        self.events = events

    def write(self, value):
        self.events.append(('GO-write', value))

    def flush(self):
        self.events.append(('GO-flush',))

    def close(self):
        self.events.append(('GO-close',))


class FakeProcess:
    def __init__(self, events):
        self.pid = 742
        self.stdin = InputPipe(events)


class FakeJob:
    def __init__(self, events, fail=False, active=1):
        self.events, self.fail, self.active = events, fail, active
        self.assigned_pid = None

    def assign(self, process):
        self.events.append(('assign', process.pid))
        if self.fail:
            raise observer.ObservationRefusal('synthetic owned assignment refusal')
        self.assigned_pid = process.pid

    def active_processes(self):
        self.events.append(('accounting', self.active))
        return self.active


class WindowsObservation742Tests(unittest.TestCase):
    def setUp(self):
        self.plan, self.plan_identity = observer.load_plan(SOURCE_ROOT)
        self.source = observer.read_regular(SOURCE_ROOT, 'scripts/ci/windows_ordinary_dependency_observer742.py')[0]

    def request(self, kind):
        return next(row for row in self.plan['requests'] if row['kind'] == kind and row['url'].startswith(observer.ORIGINS['central']))

    def fake_fetch(self, body, kind='pom', status=200, headers=None, clock=None, tick=0.0, budget=None):
        clock = clock or Clock()
        budget = budget or observer.NetworkBudget(480, clock)
        events = []
        response = FakeResponse(body, events, status=status, headers=headers, clock=clock, tick=tick)
        connections = []
        def factory(hostname, **kwargs):
            connection = FakeConnection(response, events, hostname, **kwargs)
            connections.append(connection)
            return connection
        result, raw = observer.observe_one(self.request(kind), self.plan, budget, connection_factory=factory)
        return result, raw, events, response, connections, budget

    def copy_sources(self, directory):
        root = Path(directory)
        relatives = list(self.plan['source_bindings']) + [observer.PLAN,
            'scripts/ci/windows_ordinary_dependency_observer742.py', '.github/workflows/javafx-library-candidate.yml']
        for relative in relatives:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(observer.read_regular(SOURCE_ROOT, relative)[0])
        return root

    def test_fixed_source_plan_exact_seeds_no_binary_graph_or_original_replay(self):
        self.assertEqual(self.plan_identity['sha256'], observer.PLAN_SHA256)
        self.assertEqual(len(self.plan['seeds']), 20)
        self.assertEqual(len({(seed['group'], seed['module'], seed['version']) for seed in self.plan['seeds']}), 17)
        self.assertEqual(len(self.plan['requests']), 120)
        self.assertEqual(len({row['url'] for row in self.plan['requests']}), 120)
        expanded = [{'id': f"{seed['id']}:{kind}", 'seed': seed['id'], 'kind': kind,
                     'url': observer.coordinate_url(seed, kind)}
                    for seed in self.plan['seeds'] for kind in observer.KINDS]
        self.assertEqual(expanded, self.plan['requests'])
        self.assertEqual(self.plan['archive_reuse'], [])
        self.assertEqual(len(self.plan['preserved_original14']['owner8']), 8)
        self.assertEqual(len(self.plan['preserved_original14']['original6']), 6)
        for row in self.plan['requests']:
            with self.subTest(url=row['url']):
                self.assertTrue(row['url'].startswith(tuple(observer.ORIGINS.values())))
                self.assertNotIn('.jar', row['url'])
                self.assertNotIn('.zip', row['url'])
                self.assertNotIn('javafx-web', row['url'])
                self.assertNotIn('nativecmpkit-cancel', row['url'])
        self.assertEqual(self.plan['original_accepted8_12_Stop_replayed'], 0)
        self.assertIn('unacquired', next(seed['derivation'] for seed in self.plan['seeds'] if seed['module'] == 'material3'))

    def test_exact_https_coordinate_url_request_and_traversal_refusals(self):
        seed = self.plan['seeds'][0]
        for mutation in [{'repository': 'caller'}, {'group': 'x..y'}, {'group': 'x/y'}, {'module': '../a'},
            {'module': 'a%2fb'}, {'version': '1.+'}, {'version': 'LATEST'}, {'version': '1-SNAPSHOT'},
            {'version': '${caller}'}, {'version': '[1,2]'}, {'version': '1?token=x'}]:
            with self.subTest(mutation=mutation), self.assertRaises(observer.ObservationRefusal):
                observer.coordinate_url(dict(seed, **mutation), 'pom')
        for url in ['http://repo.maven.apache.org/maven2/a.pom', 'https://repo.maven.apache.org:443/maven2/a.pom',
            'https://owner:ignored@repo.maven.apache.org/maven2/a.pom', 'https://repo.maven.apache.org/maven2/a.pom?x=y',
            'https://evil.invalid/maven2/a.pom', 'https://dl.google.com/maven2/a.pom']:
            with self.subTest(url=url), self.assertRaises(observer.ObservationRefusal):
                observer.validate_request(dict(self.plan['requests'][0], url=url), self.plan)
        for path in ['', '/a', '../a', 'a/../b', 'a//b', 'a/./b', 'a\\b', 'C:a', 'a/']:
            with self.subTest(path=path), self.assertRaises(observer.ObservationRefusal):
                observer.relative_path(path)
        with self.assertRaises(observer.ObservationRefusal):
            observer.coordinate_url(seed, 'jar.sha256')

    def test_descriptor_checksum_signature_syntax_utf8_xxe_duplicate_bounds(self):
        pom = b'<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion></project>'
        self.assertTrue(observer.validate_public_text('pom', pom, 'a.pom')['descriptor_syntax_only'])
        module = b'{"formatVersion":"1.1","component":{"group":"g","module":"m","version":"1"},"variants":[]}'
        self.assertTrue(observer.validate_public_text('module', module, 'a.module')['descriptor_syntax_only'])
        checksum = b'1' * 64 + b'  a.pom\n'
        self.assertEqual(observer.validate_public_text('pom.sha256', checksum, 'a.pom.sha256')['advertised_sha256'], '1' * 64)
        armor = b'-----BEGIN PGP SIGNATURE-----\n\nAAECAw==\n-----END PGP SIGNATURE-----\n'
        details = observer.validate_public_text('pom.asc', armor, 'a.pom.asc')
        self.assertTrue(details['armored_signature_syntax_only'])
        self.assertFalse(details['signature_cryptographically_verified'])
        malformed = [('pom', b'<!DOCTYPE project [<!ENTITY x "text">]><project><modelVersion>4.0.0</modelVersion></project>'),
            ('pom', b'<html>not a descriptor</html>'), ('pom', b'<project>\x00</project>'), ('pom', b'\xff'),
            ('pom', b'PK\x03\x04'), ('module', b'{"formatVersion":"1.1","formatVersion":"1.1"}'),
            ('module', b'{"formatVersion":"1.1","component":{"group":"g","module":"m","version":"1"},"x":NaN}'),
            ('module', b'{"formatVersion":"1.1","component":{"group":"g","module":"m","version":"1"},"x":1e999}'),
            ('pom.sha256', b'1' * 63), ('pom.sha256', b'1' * 64 + b' other.pom\n'),
            ('pom.asc', armor.replace(b'SIGNATURE', b'PUBLIC KEY BLOCK')),
            ('pom.asc', armor.replace(b'AAECAw==', b'AAECAw==\n=AAAA')),
            ('pom.asc', armor.rstrip(b'\n')), ('pom.asc', armor.replace(b'AAECAw==', b'not base64'))]
        for kind, payload in malformed:
            filename = 'a.' + kind
            with self.subTest(kind=kind, length=len(payload)), self.assertRaises((ValueError, UnicodeError, observer.ET.ParseError)):
                observer.validate_public_text(kind, payload, filename)
        with self.assertRaises(observer.ObservationRefusal):
            observer.strict_json(b'[' * 129 + b'0' + b']' * 129)
        with self.assertRaises(observer.ObservationRefusal):
            observer.validate_public_text('pom', b'x' * (observer.MAX_BODY + 1), 'a.pom')

    def test_mocked_transport_refuses_redirects_credentials_compression_partial_and_caps(self):
        pom = b'<project><modelVersion>4.0.0</modelVersion></project>'
        result, raw, events, response, connections, budget = self.fake_fetch(pom)
        self.assertEqual(result['status'], 'observed')
        self.assertEqual(raw, pom)
        self.assertEqual(budget.requests, 1)
        self.assertEqual(budget.body_bytes, len(pom))
        self.assertTrue(response.closed and connections[0].closed)
        request_event = next(event for event in events if event[0] == 'request')
        self.assertEqual(request_event[1], 'GET')
        self.assertIsNone(request_event[3])
        self.assertEqual(set(request_event[4]), {'Accept', 'Accept-Encoding', 'Connection', 'User-Agent'})
        self.assertEqual(request_event[4]['Accept-Encoding'], 'identity')
        self.assertFalse(result['credential_cookie_proxy_inheritance'])
        for status in (301, 302, 307, 308, 403, 404, 500):
            with self.subTest(status=status):
                row, payload, observations, reply, conns, counted = self.fake_fetch(pom, status=status,
                    headers=[('Location', 'https://foreign.invalid/ignored'), ('Set-Cookie', 'ignored')])
                self.assertEqual(row['status'], 'refused')
                self.assertFalse(row['public_text_qualified'])
                self.assertEqual(row['http_status'], status)
                self.assertEqual(counted.requests, 1)
                self.assertEqual(len(conns), 1)
                self.assertFalse(any(event[0] == 'read1' for event in observations))
                self.assertNotIn('Location', json.dumps(row))
                self.assertEqual(payload, b'')
                self.assertTrue(reply.closed and conns[0].closed)
        for headers in [[('Content-Length', str(len(pom))), ('Content-Length', str(len(pom)))],
            [('Content-Encoding', 'gzip')], [('Content-Length', str(len(pom) + 1))],
            [('Content-Length', str(observer.MAX_BODY + 1))], [('Content-Length', '-1')]]:
            with self.subTest(headers=headers):
                row, _raw, _events, reply, conns, _counted = self.fake_fetch(pom, headers=headers)
                self.assertEqual(row['status'], 'refused')
                self.assertFalse(row['public_text_qualified'])
                self.assertTrue(reply.closed and conns[0].closed)
        clock = Clock()
        timed, raw, _events, _reply, _conns, _count = self.fake_fetch(pom, clock=clock, tick=21.0)
        self.assertEqual(timed['status'], 'refused')
        self.assertEqual(timed['exception_type'], 'TimeoutError')
        global_budget = observer.NetworkBudget(480, Clock())
        global_budget.body_bytes = observer.MAX_TOTAL_BODY
        row, raw, events, reply, conns, global_budget = self.fake_fetch(pom, budget=global_budget)
        self.assertEqual(row['status'], 'refused')
        self.assertEqual(raw, b'')
        self.assertEqual(global_budget.body_bytes, observer.MAX_TOTAL_BODY)
        self.assertFalse(any(event[0] == 'read1' for event in events))
        limit = observer.NetworkBudget(480, Clock())
        limit.requests = observer.MAX_REQUESTS
        with self.assertRaises(observer.ObservationRefusal):
            observer.observe_one(self.request('pom'), self.plan, limit, connection_factory=lambda *_args, **_kw: self.fail('No request beyond cap'))

    def test_owned_public_private_evidence_custody_collision_and_empty_cleanup_controls(self):
        with tempfile.TemporaryDirectory(prefix='observer742-') as directory:
            root = Path(directory)
            pins = {root: observer.directory_pin(root)}
            observer.create_owned(root / 'public', pins)
            observer.create_owned(root / 'private', pins)
            payload = b'<project><modelVersion>4.0.0</modelVersion></project>'
            row = observer.write_exclusive(root, 'public/000.pom', payload, pins)
            self.assertEqual(observer.read_regular(root, 'public/000.pom')[0], payload)
            self.assertEqual(row['sha256'], hashlib.sha256(payload).hexdigest())
            with self.assertRaises(FileExistsError):
                observer.write_exclusive(root, 'public/000.pom', b'changed', pins)
            self.assertEqual(observer.read_regular(root, 'public/000.pom')[0], payload)
            observer.write_exclusive(root, 'private/001.refused.bin', b'PK\x03\x04bad', pins)
            self.assertEqual(sorted(path.name for path in (root / 'public').iterdir()), ['000.pom'])
            (root / 'public/link.pom').symlink_to(root / 'public/000.pom')
            with self.assertRaises((FileExistsError, observer.ObservationRefusal)):
                observer.write_exclusive(root, 'public/link.pom', payload, pins)
            with self.assertRaises(observer.ObservationRefusal):
                observer.read_regular(root, 'public/link.pom')
            old_pin = pins[root / 'private']
            (root / 'private').rename(root / 'retained-private')
            (root / 'private').mkdir()
            self.assertNotEqual(observer.directory_pin(root / 'private'), old_pin)
            with self.assertRaises(observer.ObservationRefusal):
                observer.write_exclusive(root, 'private/cannot-write.bin', b'x', pins)
            with self.assertRaises(OSError):
                (root / 'retained-private').rmdir()
            self.assertTrue((root / 'retained-private/001.refused.bin').is_file())

    def test_installed_jdk_None_authority_and_original_native_job_source_bindings(self):
        held = observer.snapshot_sources(SOURCE_ROOT, self.plan)
        self.assertEqual(len(self.plan['source_bindings']), 14)
        self.assertEqual(len(held), 17)
        self.assertEqual(self.plan['source_bindings']['settings.gradle.kts'], {'bytes': 2472,
            'sha256': 'f46255ba97080b1b117e85cfc563d957e30d8f9ff2ff7c327fffd6c59d286bc9'})
        self.assertEqual(self.plan['source_bindings']['docs/testing/installed-jdk17-prerequisite.md'], {'bytes': 2744,
            'sha256': '7be847de00c744b0174d65090b62e6769309cc2eafa579f17794cdf92eea2959'})
        self.assertEqual(self.plan['source_bindings']['scripts/ci/javafx_ordinary_maven_consumer.py']['sha256'],
            '291100aa05c605a6eb08d079570cd28d601e896ff99bb8ab045ee88871b99fcb')
        with tempfile.TemporaryDirectory(prefix='observer742-source-') as directory:
            root = self.copy_sources(directory)
            self.assertEqual(observer.snapshot_sources(root, self.plan)[observer.PLAN]['sha256'], observer.PLAN_SHA256)
            workflow = root / '.github/workflows/javafx-library-candidate.yml'
            original = workflow.read_bytes()
            workflow.write_bytes(original.replace(b"timeout-minutes: 120", b"timeout-minutes: 119"))
            with self.assertRaises(observer.ObservationRefusal):
                observer.snapshot_sources(root, self.plan)
            workflow.write_bytes(original)
            controller = root / 'scripts/ci/javafx_ordinary_maven_consumer.py'
            controller_raw = controller.read_bytes()
            changed = controller_raw.replace(b'REVIEWED_EXPECTATIONS_SHA256 = None',
                                              b'REVIEWED_EXPECTATIONS_SHA256 = "' + b'0' * 64 + b'"')
            self.assertNotEqual(changed, controller_raw)
            controller.write_bytes(changed)
            synthetic_recipe = copy.deepcopy(self.plan)
            synthetic_recipe['source_bindings']['scripts/ci/javafx_ordinary_maven_consumer.py'] = {
                'bytes': len(changed), 'sha256': hashlib.sha256(changed).hexdigest()}
            with self.assertRaises(observer.ObservationRefusal):
                observer.snapshot_sources(root, synthetic_recipe)
            controller.write_bytes(controller_raw)
            settings = root / 'settings.gradle.kts'
            settings.write_bytes(settings.read_bytes() + b'\n// caller resolver changed\n')
            with self.assertRaises(observer.ObservationRefusal):
                observer.snapshot_sources(root, self.plan)
        self.assertIsNone(observer.NO_ADMISSION['reviewed_expectations_authority'])

    def test_job_assignment_before_GO_failure_no_GO_and_actual_limit_source_controls(self):
        events = []
        process, job = FakeProcess(events), FakeJob(events)
        observer.assigned_go(process, job)
        self.assertEqual(events, [('assign', 742), ('accounting', 1), ('GO-write', b'GO742\n'), ('GO-flush',), ('GO-close',)])
        for failed, active in ((True, 1), (False, 2), (False, 0)):
            events = []
            with self.subTest(failed=failed, active=active), self.assertRaises(observer.ObservationRefusal):
                observer.assigned_go(FakeProcess(events), FakeJob(events, fail=failed, active=active))
            self.assertFalse(any(event[0].startswith('GO') for event in events))
        self.assertEqual(observer.WindowsJob.FLAGS, 0x2000 | 0x8 | 0x100 | 0x2)
        self.assertEqual(observer.WindowsJob.MEMORY_BYTES, 256 * 1024 * 1024)
        self.assertEqual(observer.WindowsJob.CPU_100NS, 60 * 10_000_000)
        tree = ast.parse(self.source)
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        worker_source = ast.get_source_segment(self.source.decode(), functions['worker'])
        self.assertLess(worker_source.index("sys.stdin.buffer.readline(16)"), worker_source.index('verify_worker_job(job_handle)'))
        self.assertLess(worker_source.index('verify_worker_job(job_handle)'), worker_source.index('observe_one('))
        controller_source = ast.get_source_segment(self.source.decode(), functions['controller'])
        self.assertLess(controller_source.index('job = WindowsJob()'), controller_source.index('subprocess.Popen('))
        self.assertLess(controller_source.index('subprocess.Popen('), controller_source.index('assigned_go(process, job)'))
        self.assertIn("startup.lpAttributeList = {'handle_list': [int(job.handle)]}", controller_source)
        self.assertIn('job.inherit(False)', controller_source)
        self.assertIn('job.active_processes() <= 1', controller_source)
        self.assertIn('job_empty and direct_terminal and not any(thread.is_alive()', controller_source)
        self.assertIn('directory_pin(path.parent) == pins[path.parent] and directory_pin(path) == pins[path]', controller_source)
        self.assertIn('path.rmdir()', controller_source)
        self.assertNotIn('rmtree', controller_source)
        worker_limits_source = ast.get_source_segment(self.source.decode(), functions['verify_worker_job'])
        self.assertIn('api.IsProcessInJob(api.GetCurrentProcess(), handle', worker_limits_source)
        self.assertIn('result.BasicLimitInformation.LimitFlags == WindowsJob.FLAGS', worker_limits_source)
        self.assertIn('result.ProcessMemoryLimit == WindowsJob.MEMORY_BYTES', worker_limits_source)

    def test_observation_only_checksum_agreement_never_trust_policy_or_native_execution(self):
        primary = dict(self.request('pom'), public_text_qualified=True, body_sha256='a' * 64)
        checksum = dict(self.request('pom.sha256'), public_text_qualified=True, advertised_sha256='a' * 64)
        rows = [primary, checksum]
        before = copy.deepcopy(rows)
        observer.annotate_checksum_agreement(rows)
        self.assertTrue(rows[1]['advertised_descriptor_digest_agrees'])
        self.assertFalse(rows[1]['same_registry_checksum_is_independent_security_certification'])
        self.assertEqual(rows[0], before[0])
        self.assertIsNone(observer.NO_ADMISSION['reviewed_expectations_authority'])
        self.assertTrue(observer.NO_ADMISSION['observations_are_untrusted'])
        for key, value in observer.NO_ADMISSION.items():
            if key not in {'reviewed_expectations_authority', 'observations_are_untrusted'}:
                with self.subTest(key=key):
                    self.assertIs(value, False)
        with tempfile.TemporaryDirectory(prefix='observer742-env-') as directory:
            runtime = Path(directory)
            inherited = {'SYSTEMROOT': directory, 'PATH': '/not/inherited', 'HTTPS_PROXY': 'ignored', 'http_proxy': 'ignored',
                'GITHUB_TOKEN': 'ignored', 'GRADLE_USER_HOME': 'ignored', 'JAVA_HOME': 'ignored', 'SSL_CERT_FILE': 'ignored',
                'PYTHONPATH': 'ignored', 'PYTHONHOME': 'ignored'}
            actual = observer.safe_environment(runtime, Path(sys.executable).resolve(), inherited)
            self.assertEqual(set(actual), {'SYSTEMROOT', 'WINDIR', 'PATH', 'HOME', 'USERPROFILE', 'TMP', 'TEMP', 'LANG', 'LC_ALL'})
            self.assertFalse(any('ignored' in value for value in actual.values()))
        tree = ast.parse(self.source)
        imports = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
        self.assertFalse(imports & {'javafx_ordinary_maven_consumer', 'library_tests', 'webview_consumer', 'zipfile', 'tarfile',
                                    'daemon_jvm', 'runtime_context', 'failure_diagnostics'})
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        worker_source = ast.get_source_segment(self.source.decode(), functions['worker'])
        self.assertNotIn('subprocess', worker_source)
        self.assertNotIn('Gradle', worker_source)
        self.assertNotIn('verification-metadata.xml', worker_source)
        self.assertIn('original14_binaries_or_sidecars_acquired', worker_source)
        workflow = observer.read_regular(SOURCE_ROOT, '.github/workflows/javafx-library-candidate.yml')[0].decode()
        suffix = workflow.split(self.plan['workflow_preservation']['suffix_marker'])[1]
        self.assertNotIn('setup-java', suffix)
        self.assertNotIn('setup-android', suffix)
        self.assertNotIn('gradle/actions', suffix)
        self.assertNotIn('cache@', suffix)
        self.assertIn('persist-credentials: false', suffix)
        self.assertIn('contents: read', suffix)
        self.assertIn('public/*', suffix)
        self.assertNotIn('private/*', suffix)
        self.assertNotIn('private/**', suffix)
        self.assertEqual(self.plan['no_admission'], observer.NO_ADMISSION)


if __name__ == '__main__':
    unittest.main()
