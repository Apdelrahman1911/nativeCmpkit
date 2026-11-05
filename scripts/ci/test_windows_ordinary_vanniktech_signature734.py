# SPDX-License-Identifier: Apache-2.0
"""NEW one-target source/fake controls only, NEVER real network or payload review."""
import ast
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import types
import unittest

SOURCE_ROOT = Path(os.environ.get('NATIVECMPKIT_SIGNATURE734_TEST_SOURCE_ROOT',
    str(Path(__file__).resolve().parents[2])))
STATE_ROOT = Path(os.environ.get('NATIVECMPKIT_SIGNATURE734_TEST_STATE_ROOT',
    str(SOURCE_ROOT / 'build/ci-verification/signature734-NEW-controls-state')))
OWN_PATH = 'scripts/ci/windows_ordinary_vanniktech_signature_observer734.py'
OBSERVERSHA = '6d573297c1f6b5f5581b98540d490de36728cef9b043cf7ea45a509275546b1f'
OBSERVERBYTES = 49128
CRITICALSHA = 'ff425c9110024f90b8b1f2ce45426bd32737e8965d89851bdf9db7fa6495d14a'


def read_exact(path, expected_bytes, expected_sha):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size != expected_bytes:
        raise AssertionError('Only the declared immutable bounded source endpoint')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NOATIME', 0))
    try:
        raw = b''
        while True:
            part = os.read(fd, min(65536, expected_bytes + 1 - len(raw)))
            if not part:
                break
            raw += part
            if len(raw) > expected_bytes:
                raise AssertionError('Source cap')
    finally:
        os.close(fd)
    if len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise AssertionError('Exact held source bytes/hash')
    return raw


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class Socket:
    def __init__(self):
        self.timeouts = []

    def settimeout(self, value):
        self.timeouts.append(value)


class Response:
    def __init__(self, payload=b'synthetic uninspected bytes', status=200, headers=None, close_error=False):
        self.status = status
        self.headers = headers if headers is not None else [('Content-Length', str(len(payload)))]
        self.payload = payload
        self.position = 0
        self.read_sizes = []
        self.close_error = close_error
        self.closed = False

    def getheaders(self):
        return self.headers

    def isclosed(self):
        return self.position >= len(self.payload)

    def read1(self, maximum):
        self.read_sizes.append(maximum)
        result = self.payload[self.position:self.position + maximum]
        self.position += len(result)
        return result

    def close(self):
        self.closed = True
        if self.close_error:
            raise OSError('Synthetic owned-response close refusal')


class Factory:
    def __init__(self, response, clock=None, headers_after=None, close_error=False):
        self.response = response
        self.clock = clock
        self.headers_after = headers_after
        self.close_error = close_error
        self.calls = []
        self.requests = []
        self.sock = Socket()
        self.closed = False

    def __call__(self, host, **options):
        self.calls.append((host, options))
        return self

    def connect(self):
        return None

    def request(self, method, path, body, headers):
        self.requests.append((method, path, body, headers))

    def getresponse(self):
        if self.headers_after is not None:
            self.clock.now = self.headers_after
        return self.response

    def close(self):
        self.closed = True
        if self.close_error:
            raise OSError('Synthetic owned-connection close refusal')


class OneNewSignature734Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = read_exact(SOURCE_ROOT / OWN_PATH, OBSERVERBYTES, OBSERVERSHA)
        module = types.ModuleType('nativecmpkit_signature734_NEW_only')
        module.__file__ = str(SOURCE_ROOT / OWN_PATH)
        exec(compile(cls.raw, module.__file__, 'exec'), module.__dict__)
        cls.observer = module
        cls.plan_raw = read_exact(SOURCE_ROOT / module.PLAN, 6448, 'bf3cdca3083092e7e79ab583e34d48eb04a8e7bd1d337963e1a1aad5bf266632')
        cls.metadata_raw = read_exact(SOURCE_ROOT / module.CACHE_PATH, module.CACHE_BYTES, module.CACHE_SHA256)
        cls.plan0 = module.strict_json(cls.plan_raw)
        cls.metadata0 = module.strict_json(cls.metadata_raw)

    def setUp(self):
        self.o = self.observer
        self.plan = copy.deepcopy(self.plan0)
        self.metadata = copy.deepcopy(self.metadata0)

    def observe(self, response=None, factory=None, budget=None, row=None):
        response = response or Response()
        factory = factory or Factory(response)
        budget = budget or self.o.NetworkBudget(60, Clock())
        result, payload = self.o.observe_one(row or dict(self.o.EXACT_TARGET), self.plan, budget, factory)
        return result, payload, factory, budget

    def report(self, result, budget):
        row = copy.deepcopy(result)
        if row['body_bytes']:
            row['raw_evidence'] = {'path': 'private/000.pom.asc', 'bytes': row['body_bytes'], 'sha256': row['body_sha256']}
        before = {'owned-NEW-source-only-fixture': {'bytes': 1, 'sha256': '0' * 64}}
        report = {'schema': self.o.WORKER_SCHEMA, 'observational_protocol_complete': True,
            'requests_attempted': budget.requests, 'planned_requests': 1,
            'new_selected_signature_target_requests': 1, 'fixed_failed18_requests_replayed': 0,
            'accepted_POM_requests_replayed': 0, 'accepted_public58_replayed': 0,
            'original_HTTP404_requests_replayed': 0, 'original14_binaries_or_sidecars_acquired': 0,
            'native_webview_request_state_tests_executed': 0, 'cached_source_metadata_reused': True,
            'cached_source_metadata_sha256': self.o.CACHE_SHA256,
            'cached_source_record_sha256': self.o.CACHED_ROW_SHA256,
            'automatic_redirects_followed': False, 'all_payloads_qualified_as_public_text': False,
            'signature_syntax_inspected': False, 'cached_POM_read_or_extracted': False,
            'raw_body_bytes': budget.body_bytes, 'source_inputs_held': True,
            'source_inputs_before': before, 'source_inputs_after': before, 'observations': [row],
            'no_admission': dict(self.o.NO_ADMISSION), 'archive_reuse': [],
            'windows_runner_prerequisite_only': True, 'required_real_graph_binary_signatures_or_policy_complete': False}
        return report, before

    @contextlib.contextmanager
    def cache_fixture(self, raw=None, symlink=False):
        root = Path(tempfile.mkdtemp(prefix='NEW-source303-', dir=STATE_ROOT))
        scripts = root / 'scripts'
        ci = scripts / 'ci'
        scripts.mkdir(mode=0o700)
        ci.mkdir(mode=0o700)
        path = root / self.o.CACHE_PATH
        owned = root / 'owned-cache-bytes'
        target = owned if symlink else path
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            payload = raw if raw is not None else self.metadata_raw
            count = 0
            while count < len(payload):
                count += os.write(fd, payload[count:])
        finally:
            os.close(fd)
        if symlink:
            path.symlink_to(owned)
        try:
            yield root
        finally:
            path.unlink()
            if symlink:
                owned.unlink()
            ci.rmdir()
            scripts.rmdir()
            root.rmdir()

    def test_NEW01_immutable_cached_source303_selects_only_one_NEW_signature(self):
        held = self.o.validate_cached_bytes(self.metadata_raw)
        self.assertEqual(self.o.select_cached_target(held, self.plan), self.o.EXACT_TARGET)
        self.assertEqual(len(self.plan['requests']), 1)
        self.assertEqual(self.plan['requests'][0]['kind'], 'pom.asc')
        self.assertEqual(held['basis']['run_id'], 42087525896)

    def test_NEW02_cached_byte_hash_or_JSON_tamper_refuses(self):
        for raw in (self.metadata_raw + b' ', self.metadata_raw.replace(b'303', b'200', 1), b'{}'):
            with self.subTest(length=len(raw)), self.assertRaises(self.o.ObservationRefusal):
                self.o.validate_cached_bytes(raw)

    def test_NEW03_source_ID_status_bool_and_close_mismatches_refuse(self):
        for key, value in [('id', 'unrelated:pom.asc'), ('http_status', 200), ('http_status', True),
                ('Location_header_count', True), ('body_bytes', True),
                ('close_errors', [{'resource': 'response', 'exception_type': 'OSError'}]),
                ('status', 'observed'), ('exception_type', None)]:
            data = copy.deepcopy(self.metadata)
            data['source_record'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(self.o.ObservationRefusal):
                self.o.validate_cached_metadata(data)

    def test_NEW04_source_URL_GAV_Location_and_basis_mismatches_refuse(self):
        for key, value in [('url', self.o.EXACT_TARGET['url']),
                ('public_Location', self.o.EXACT_TARGET['url'].replace('/0.37.0/', '/0.36.0/')),
                ('public_Location', self.o.EXACT_TARGET['url'] + '?token=no'),
                ('public_Location', self.o.EXACT_TARGET['url'].replace('repo.maven.apache.org', 'other.example'))]:
            data = copy.deepcopy(self.metadata)
            data['source_record'][key] = value
            with self.subTest(key=key), self.assertRaises(self.o.ObservationRefusal):
                self.o.validate_cached_metadata(data)
        for key, value in [('Location_sha256', '0' * 64), ('source_record_index', 1)]:
            data = copy.deepcopy(self.metadata)
            data[key] = value
            with self.subTest(key=key), self.assertRaises(self.o.ObservationRefusal):
                self.o.validate_cached_metadata(data)
        self.metadata['basis']['run_id'] = 42087525895
        with self.assertRaises(self.o.ObservationRefusal):
            self.o.validate_cached_metadata(self.metadata)

    def test_NEW05_cached_no_follow_refusal_is_metadata_not_payload_or_admission(self):
        data = self.o.validate_cached_metadata(self.metadata)
        self.assertEqual(data['source_record']['exception_type'], 'ObservationRefusal')
        self.assertEqual(data['source_record']['status'], 'refused')
        self.assertEqual(data['source_record']['body_bytes'], 0)
        self.assertTrue(data['NO_ADMISSION'])
        self.assertIsNone(data['REVIEWED_EXPECTATIONS_SHA256'])
        self.assertIsNone(self.o.REVIEWED_EXPECTATIONS_SHA256)

    def test_NEW06_no_caller_cache_archive_extra_or_authority_field(self):
        for key, value in [('cached_source_metadata', {'path': '/tmp/caller.json'}),
                ('archive_reuse', ['caller.zip']), ('REVIEWED_EXPECTATIONS_SHA256', '0' * 64),
                ('independently_expected_signature_SHA256', '0' * 64), ('publisher_key_fingerprint', 'A' * 40)]:
            candidate = copy.deepcopy(self.plan)
            candidate[key] = value
            with self.subTest(key=key), self.assertRaises(self.o.ObservationRefusal):
                self.o.validate_plan(candidate)

    def test_NEW07_no_original_source_POM_other17_or_second_target_in_plan(self):
        for row in [self.metadata['source_record'],
                {**self.o.EXACT_TARGET, 'kind': 'pom', 'url': self.o.EXACT_TARGET['url'][:-4]},
                {**self.o.EXACT_TARGET, 'id': 'another:pom.asc'}]:
            candidate = copy.deepcopy(self.plan)
            candidate['requests'] = [row]
            with self.subTest(id=row['id']), self.assertRaises(self.o.ObservationRefusal):
                self.o.select_cached_target(self.metadata, candidate)
        self.plan['requests'].append(dict(self.o.EXACT_TARGET))
        with self.assertRaises(self.o.ObservationRefusal):
            self.o.validate_plan(self.plan)

    def test_NEW08_query_credentials_wrong_origin_or_percent_never_transport(self):
        for url in [self.o.EXACT_TARGET['url'] + '?probe=1', self.o.EXACT_TARGET['url'] + '#fragment',
                self.o.EXACT_TARGET['url'].replace('https://', 'https://user:password@'),
                self.o.EXACT_TARGET['url'].replace('repo.maven.apache.org', 'plugins.gradle.org'),
                self.o.EXACT_TARGET['url'].replace('/maven2/', '/maven2/%2e/')]:
            factory = Factory(Response())
            with self.subTest(url=url), self.assertRaises(self.o.ObservationRefusal):
                self.observe(row={**self.o.EXACT_TARGET, 'url': url}, factory=factory)
            self.assertEqual(factory.calls, [])

    def test_NEW09_fixed_source_file_tamper_and_symlink_refuse(self):
        with self.cache_fixture() as root:
            data, row = self.o.load_cached_metadata(root)
            self.assertEqual(data, self.metadata)
            self.assertEqual(row['sha256'], self.o.CACHE_SHA256)
        with self.cache_fixture(self.metadata_raw + b' ') as root:
            with self.assertRaises(self.o.ObservationRefusal):
                self.o.load_cached_metadata(root)
        with self.cache_fixture(symlink=True) as root:
            with self.assertRaises(self.o.ObservationRefusal):
                self.o.load_cached_metadata(root)

    def test_NEW10_real_nonWindows_entry_and_controller_refuse_before_outputs(self):
        if os.name == 'nt':
            self.skipTest('This particular unsupported-host control is Linux-only')
        with self.assertRaises(self.o.ObservationRefusal):
            self.o.main()
        with self.assertRaises(self.o.ObservationRefusal):
            self.o.controller(STATE_ROOT / 'never-created')
        self.assertFalse((STATE_ROOT / 'never-created').exists())

    def test_NEW11_one200_capture_stays_private_uninspected_and_no_inheritance(self):
        result, payload, factory, budget = self.observe()
        self.assertEqual(result['status'], 'captured-uninspected')
        self.assertEqual(payload, b'synthetic uninspected bytes')
        self.assertFalse(result['public_text_qualified'])
        self.assertFalse(result['signature_syntax_inspected'])
        self.assertEqual(self.o.payload_evidence_relative(result, payload), 'private/000.pom.asc')
        self.assertEqual(budget.requests, 1)
        self.assertEqual(len(factory.calls), 1)
        self.assertEqual(factory.calls[0][0], 'repo.maven.apache.org')
        self.assertEqual(factory.calls[0][1]['port'], 443)
        method, path, body, headers = factory.requests[0]
        self.assertEqual(method, 'GET')
        self.assertEqual(path, self.o.EXACT_TARGET['url'].split('repo.maven.apache.org', 1)[1])
        self.assertIsNone(body)
        self.assertEqual(headers['Accept-Encoding'], 'identity')
        self.assertFalse(any(key.lower() in ('authorization', 'cookie', 'proxy-authorization') for key in headers))
        self.assertTrue(factory.closed)
        self.assertTrue(factory.response.closed)

    def test_NEW12_target_redirects_refuse_without_body_hop_or_retry(self):
        for status in (301, 302, 303, 307, 308, 404):
            response = Response(status=status, headers=[('Location', self.o.EXACT_TARGET['url'] + '.another')])
            result, payload, factory, budget = self.observe(response)
            with self.subTest(status=status):
                self.assertEqual(result['status'], 'refused')
                self.assertEqual(result['http_status'], status)
                self.assertEqual(result['exception_type'], 'ObservationRefusal')
                self.assertEqual(payload, b'')
                self.assertEqual(response.read_sizes, [])
                self.assertEqual(len(factory.calls), budget.requests)
                self.assertEqual(budget.requests, 1)
                self.assertFalse(result['automatic_redirects_followed'])

    def test_NEW13_target_unsafe_Location_is_digest_only_and_not_followed(self):
        urls = ['https://repo.maven.apache.org/new-response-metadata-only',
                'https://other.example/new-response-metadata-only',
                'https://repo.maven.apache.org/file?credential=no', 'https://user:pass@example.com/file']
        for url in urls:
            for status in (200, 303):
                response = Response(status=status, headers=[('Location', url)])
                result, payload, factory, budget = self.observe(response)
                with self.subTest(url=url, status=status):
                    self.assertIsNone(result['public_Location'])
                    self.assertEqual(result['Location_header_count'], 1)
                    self.assertEqual(result['unqualified_Location_sha256'], [self.o.digest(url.encode())])
                    self.assertNotIn(url, json.dumps(result, sort_keys=True))
                    self.assertEqual(len(factory.calls), 1)
                    self.assertEqual(budget.requests, 1)
                    self.assertFalse(result['automatic_redirects_followed'])
                    self.assertFalse(result['signature_syntax_inspected'])
                    self.assertFalse(result['public_text_qualified'])
                    if status == 200:
                        self.assertEqual(result['status'], 'captured-uninspected')
                        self.assertEqual(payload, b'synthetic uninspected bytes')
                        self.assertEqual(self.o.payload_evidence_relative(result, payload), 'private/000.pom.asc')
                    else:
                        self.assertEqual(result['status'], 'refused')
                        self.assertEqual(payload, b'')
                        self.assertEqual(response.read_sizes, [])

    def test_NEW14_duplicate_oversized_or_bool_headers_refuse_no_body(self):
        for response in [Response(status=True), Response(status=303, headers=[]),
                Response(status=303, headers=[('Location', self.o.EXACT_TARGET['url'])] * 2),
                Response(headers=[('X', 'a')] * 65), Response(headers=[('X', 'a' * 16385)])]:
            result, payload, _factory, _budget = self.observe(response)
            self.assertEqual(result['status'], 'refused')
            self.assertEqual(result['exception_type'], 'ObservationRefusal')
            self.assertEqual(payload, b'')
            self.assertEqual(response.read_sizes, [])

    def test_NEW15_compression_duplicate_length_and_advertised_cap_refuse(self):
        for headers in [[('Content-Encoding', 'gzip')], [('Content-Length', '2')] * 2,
                [('Content-Length', '524289')], [('Content-Length', 'no')], [('Content-Length', '0')]]:
            response = Response(headers=headers)
            result, payload, _factory, _budget = self.observe(response)
            self.assertEqual(result['status'], 'refused')
            self.assertEqual(payload, b'')
            self.assertEqual(response.read_sizes, [])

    def test_NEW16_512KiB_hard_cap_retains_private_bytes_without_probe(self):
        response = Response(payload=b'x' * self.o.MAX_BODY)
        result, payload, _factory, budget = self.observe(response)
        self.assertEqual(len(payload), self.o.MAX_BODY)
        self.assertEqual(response.position, self.o.MAX_BODY)
        self.assertEqual(sum(response.read_sizes), self.o.MAX_BODY)
        self.assertEqual(budget.body_bytes, self.o.MAX_TOTAL_BODY)
        self.assertEqual(result['status'], 'refused')
        self.assertFalse(result['complete_response'])
        self.assertEqual(self.o.payload_evidence_relative(result, payload), 'private/000.pom.asc')

    def test_NEW17_max1_request_refuses_before_second_transport(self):
        budget = self.o.NetworkBudget(60, Clock())
        result, _payload, factory, _budget = self.observe(budget=budget)
        self.assertEqual(result['status'], 'captured-uninspected')
        with self.assertRaises(self.o.ObservationRefusal):
            self.observe(factory=factory, budget=budget)
        self.assertEqual(len(factory.calls), 1)
        self.assertEqual(len(factory.requests), 1)
        for value in (-1, True, self.o.MAX_TOTAL_BODY + 1):
            with self.subTest(value=value), self.assertRaises(self.o.ObservationRefusal):
                self.o.NetworkBudget(60, Clock()).receive(value)

    def test_NEW18_real20s_header_deadline_and_exhausted_acquisition_preserved(self):
        clock = Clock()
        response = Response()
        factory = Factory(response, clock=clock, headers_after=21)
        result, payload, factory, budget = self.observe(factory=factory, budget=self.o.NetworkBudget(60, clock))
        self.assertEqual(result['exception_type'], 'TimeoutError')
        self.assertEqual(payload, b'')
        self.assertEqual(response.read_sizes, [])
        self.assertTrue(factory.closed)
        self.assertTrue(response.closed)
        self.assertTrue(all(0 < timeout <= 20 for timeout in factory.sock.timeouts))
        expired = Factory(Response())
        with self.assertRaises(TimeoutError):
            self.observe(factory=expired, budget=self.o.NetworkBudget(0, Clock()))
        self.assertEqual(expired.calls, [])

    def test_NEW19_close_errors_and_partial_body_preserved_untrusted(self):
        response = Response(close_error=True)
        factory = Factory(response, close_error=True)
        result, payload, _factory, _budget = self.observe(factory=factory)
        self.assertEqual(result['status'], 'refused')
        self.assertEqual([row['resource'] for row in result['close_errors']], ['response', 'connection'])
        self.assertEqual(self.o.payload_evidence_relative(result, payload), 'private/000.pom.asc')
        partial = Response(payload=b'abc', headers=[('Content-Length', '4')])
        result, payload, _factory, _budget = self.observe(partial)
        self.assertEqual(payload, b'abc')
        self.assertEqual(result['exception_type'], 'ObservationRefusal')
        self.assertFalse(result['complete_response'])

    def test_NEW20_report_no_replay_private_payload_and_trust_counters_fail_closed(self):
        result, _payload, _factory, budget = self.observe()
        report, before = self.report(result, budget)
        self.o.validate_worker_report(report, self.plan, before)
        for key, value in [('requests_attempted', True), ('requests_attempted', 2),
                ('fixed_failed18_requests_replayed', 18), ('accepted_POM_requests_replayed', 1),
                ('cached_source_metadata_sha256', '0' * 64), ('signature_syntax_inspected', True),
                ('all_payloads_qualified_as_public_text', True), ('native_webview_request_state_tests_executed', 1)]:
            candidate = copy.deepcopy(report)
            candidate[key] = value
            with self.subTest(key=key), self.assertRaises(self.o.ObservationRefusal):
                self.o.validate_worker_report(candidate, self.plan, before)
        for key in ('public_text_qualified', 'publisher_provenance_qualified', 'signature_cryptographically_verified'):
            candidate = copy.deepcopy(report)
            candidate['observations'][0][key] = True
            with self.subTest(key=key), self.assertRaises(self.o.ObservationRefusal):
                self.o.validate_worker_report(candidate, self.plan, before)
        for key, value in [('public_Location', 'https://server.example/new-captured-location'),
                ('unqualified_Location_sha256', ['https://server.example/new-captured-location']),
                ('Location_header_count', True), ('Location_header_count', -1),
                ('Location_header_count', self.o.MAX_HEADERS + 1), ('Location_header_count', 1),
                ('unqualified_Location_sha256', ['0' * 64])]:
            candidate = copy.deepcopy(report)
            candidate['observations'][0][key] = value
            with self.subTest(Location_field=key, value=value), self.assertRaises(self.o.ObservationRefusal):
                self.o.validate_worker_report(candidate, self.plan, before)
        report['observations'][0]['raw_evidence']['path'] = 'public/000.pom.asc'
        with self.assertRaises(self.o.ObservationRefusal):
            self.o.validate_worker_report(report, self.plan, before)

    def test_NEW21_exact_owned_Job_GO_capture_cleanup_source_and_caps_preserved(self):
        text = self.raw.decode()
        tree = ast.parse(text)
        functions = {node.name: ast.get_source_segment(text, node) for node in tree.body
                     if isinstance(node, ast.FunctionDef)}
        critical = functions['controller'].split('    process = job = None\n', 1)[1].split('    worker_report = None\n', 1)[0]
        self.assertEqual(hashlib.sha256(critical.encode()).hexdigest(), CRITICALSHA)
        self.assertEqual((self.o.TOTAL_SECONDS, self.o.ACQUISITION_SECONDS, self.o.CLEANUP_SECONDS,
                          self.o.IO_SECONDS, self.o.MAX_CAPTURE), (90, 60, 15, 20, 65536))
        self.assertIn('job.active_processes() <= 1', critical)
        self.assertIn('assigned_go(process, job)', critical)
        self.assertIn('job.close()', critical)
        self.assertIn('path.rmdir()', critical)
        self.assertNotIn('rmtree', critical)
        worker_ast = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'worker')
        calls = [node for node in ast.walk(worker_ast) if isinstance(node, ast.Call) and
                 isinstance(node.func, ast.Name) and node.func.id == 'observe_one']
        self.assertEqual(len(calls), 1)

    def test_NEW22_no_signature_parser_key_payload_POM_or_new_issue_acceptance(self):
        tree = ast.parse(self.raw)
        forbidden = {'validate_public_text', 'verify_signature', 'parse_signature', 'decrypt', 'gpg', 'verify_POM'}
        calls = [node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        self.assertFalse(set(calls) & forbidden)
        self.assertFalse(self.plan['cached_POM_access_authorized'])
        self.assertTrue(self.plan['windows_runner_prerequisite_only'])
        self.assertEqual(self.plan['native_webview_request_state_tests_executed'], 0)
        self.assertEqual(len(self.plan['source_bindings']), 21)
        self.assertEqual(self.plan['source_bindings'][self.o.CACHE_PATH]['sha256'], self.o.CACHE_SHA256)
        self.assertFalse(any(path.endswith('/README.md') for path in self.plan['source_bindings']))
        self.assertEqual(self.plan['workflow_routing']['exact_modified_spans'], 2)
        self.assertTrue(self.plan['workflow_routing']['all_other_workflow_bytes_unchanged'])
        self.assertIsNone(self.plan['independently_expected_signature_SHA256'])
        self.assertIsNone(self.plan['publisher_key_fingerprint'])


if __name__ == '__main__':
    unittest.main()
