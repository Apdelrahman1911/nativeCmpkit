#!/usr/bin/env python3
"""NEW changed cause controls: fake transport only, no Windows/consumer admission."""
import ast
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import types
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'windows_ordinary_dependency_cause_observer734.py'
SOURCE_SHA256 = 'b4c2f4eed03238906c74aac6c2d7e0082cdf02813ad7bd53e81ad463c907e2bf'
PLAN = HERE / 'windows-ordinary-cause734-plan.json'
PLAN_SHA256 = '58feda29d914c87557556d61d5280a3f4e75fe46c2f244a7ecb4a36d8eb30dec'
CAUSE_PATH = HERE.parents[1] / 'docs/development/evidence/current-platform-recovery-20261101/windows-normal120-cause734/CAUSE62-METADATA-SOURCE-EXPECTATIONS734-R1.json'
CAUSE_SHA256 = 'c0a41061083b82802076a1f2495d8593d8fec94fe1ce3d15c6cae577b131a5a3'
NO_REAL_API_OR_SUBPROCESS = True


def read_source(path, expected):
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NOATIME', 0))
    try:
        chunks = []
        size = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            size += len(chunk)
            if size > 524288:
                raise ValueError('Control source cap')
            chunks.append(chunk)
        raw = b''.join(chunks)
    finally:
        os.close(fd)
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Sealed NEW control source identity changed')
    return raw


SOURCE_RAW = read_source(SOURCE, SOURCE_SHA256)
observer = types.ModuleType('private_new_cause_observer734')
observer.__file__ = str(SOURCE)
exec(compile(SOURCE_RAW, str(SOURCE), 'exec'), observer.__dict__)
MODEL = observer.strict_json(read_source(PLAN, PLAN_SHA256))
BASIS = observer.strict_json(read_source(CAUSE_PATH, CAUSE_SHA256))
POM = b'<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion></project>\n'


class FakeSocket:
    def __init__(self):
        self.closed = False
        self.timeouts = []

    def settimeout(self, value):
        if self.closed:
            raise OSError('Fake borrowed socket closed')
        self.timeouts.append(value)


class FakeResponse:
    def __init__(self, status, headers=None, payload=b'', close_error=False):
        self.status = status
        self.headers = [] if headers is None else headers
        self.payload = payload
        self.position = 0
        self.read_calls = []
        self.header_calls = 0
        self.closed = False
        self.close_error = close_error
        self.close_calls = 0
        self.socket = None

    def getheaders(self):
        self.header_calls += 1
        return self.headers

    def read1(self, size):
        self.read_calls.append(size)
        value = self.payload[self.position:self.position + size]
        self.position += len(value)
        if self.position == len(self.payload):
            self.closed = True
            self.socket.closed = True
        return value

    def isclosed(self):
        return self.closed

    def close(self):
        self.close_calls += 1
        self.closed = True
        if self.close_error:
            raise OSError('Fake response close failure')


class FakeConnection:
    def __init__(self, host, response, header_timeout=False, close_error=False):
        self.host = host
        self.response = response
        self.sock = FakeSocket()
        self.response.socket = self.sock
        self.requests = []
        self.connect_calls = 0
        self.close_calls = 0
        self.header_timeout = header_timeout
        self.close_error = close_error

    def connect(self):
        self.connect_calls += 1

    def request(self, method, path, body, headers):
        self.requests.append((method, path, body, headers))

    def getresponse(self):
        if self.header_timeout:
            raise TimeoutError('Fake header timeout')
        return self.response

    def close(self):
        self.close_calls += 1
        if self.close_error:
            raise OSError('Fake connection close failure')


class FakeFactory:
    def __init__(self, response, header_timeout=False, close_error=False):
        self.response = response
        self.header_timeout = header_timeout
        self.close_error = close_error
        self.connections = []

    def __call__(self, host, **_kwargs):
        connection = FakeConnection(host, self.response, self.header_timeout, self.close_error)
        self.connections.append(connection)
        return connection


def budget():
    return observer.NetworkBudget(1000.0, clock=lambda: 100.0)


def basic_observation(row):
    return dict(row, status='refused', http_status=303, headers_complete=False,
                Location_header_count=0, public_Location=None, unqualified_Location_sha256=[],
                body_bytes=0, body_sha256=None, public_text_qualified=False, complete_response=False,
                exception_type='ObservationRefusal', close_errors=[], network_request_started=True,
                evidence_role=observer.evidence_role(row), automatic_redirects_followed=False,
                signature_cryptographically_verified=False, publisher_provenance_qualified=False,
                credential_cookie_proxy_inheritance=False, canonical_publisher_target_authenticated=False,
                original_GET_headers_reconstructed=False, independent_trust_or_consumer_acceptance=False)


def prefix_observations(selected=False):
    rows = [basic_observation(row) for row in MODEL['requests'][:18]]
    if selected:
        source = next(row for row in rows if row['id'] == observer.EXACT_SOURCE_ID)
        source.update(status='redirect-exact-target-observed', headers_complete=True,
                      Location_header_count=1, public_Location=MODEL['requests'][-1]['url'],
                      exception_type=None)
    return rows


def fake_report(selected=False):
    rows = prefix_observations(selected)
    rows.append(basic_observation(MODEL['requests'][-1]) if selected else
                observer.withheld_target(MODEL['requests'][-1]))
    return {'schema': 'nativecmpkit-Windows-cause-observation-worker734-r1',
        'observational_protocol_complete': True, 'no_admission': copy.deepcopy(observer.NO_ADMISSION),
        'source_inputs_before': {}, 'source_inputs_after': {},
        'original14_binaries_or_sidecars_acquired': 0,
        'original62_cached_refusals': copy.deepcopy(MODEL['cause_cases']),
        'accepted_public58_replayed': 0, 'original_HTTP404_requests_replayed': 0,
        'archive_reuse': [], 'fixed_failed18_requests': 18, 'source_inputs_held': True,
        'raw_body_bytes': sum(row['body_bytes'] for row in rows),
        'all_payloads_qualified_as_public_text': all(row['public_text_qualified'] for row in rows),
        'required_real_graph_binary_signatures_or_policy_complete': False,
        'automatic_redirects_followed': False, 'planned_requests': 19, 'observations': rows,
        'requests_attempted': 18 + int(selected), 'explicit_one_hop_target_requests': int(selected)}


class NewCause28(unittest.TestCase):
    def response(self, status=303, headers=None, payload=b'', row=None, **kwargs):
        response = FakeResponse(status, headers, payload, kwargs.get('close_error', False))
        factory = FakeFactory(response, kwargs.get('header_timeout', False))
        measured = budget()
        observed, raw = observer.observe_one(row or MODEL['requests'][0], MODEL, measured, factory)
        return observed, raw, response, factory, measured

    def test_NEW01_all62_and_original120_preserved_without_fetch(self):
        self.assertIs(observer.validate_cause_plan(MODEL), MODEL)
        observer.validate_cause_basis(BASIS, MODEL)
        self.assertEqual(len(MODEL['original_requests']), 120)
        self.assertEqual(Counter(r['original_http_status'] for r in MODEL['cause_cases']), {404: 44, 303: 18})
        self.assertEqual(Counter(r['category'] for r in MODEL['cause_cases']), observer.CAUSE_COUNTS)

    def test_NEW02_missing_or_extra_cached_case_refuses(self):
        for cases in (MODEL['cause_cases'][:-1], MODEL['cause_cases'] + [MODEL['cause_cases'][0]]):
            plan = copy.deepcopy(MODEL)
            plan['cause_cases'] = cases
            with self.assertRaises(observer.ObservationRefusal):
                observer.validate_cause_plan(plan)

    def test_NEW03_optional_sha_never_authorizes_expected_digest(self):
        checksums = [r for r in MODEL['cause_cases'] if r['category'] == 'optional-present-primary-sha256-sidecar-absence']
        self.assertEqual(len(checksums), 14)
        self.assertTrue(all(observer.evidence_role(r) == 'optional-untrusted-registry-SHA256-sidecar' for r in checksums))
        self.assertIs(observer.NO_ADMISSION['reviewed_expectations_authority'], None)
        self.assertIs(observer.NO_ADMISSION['same_registry_checksum_is_independent_security_certification'], False)
        self.assertIs(observer.NO_ADMISSION['dependency_or_bootstrap_execution_admitted'], False)

    def test_NEW04_absent_module_dependents_not_binary_or_signature_waiver(self):
        cases = [r for r in MODEL['cause_cases'] if r['category'] == 'missing-format-or-dependent-probe']
        self.assertEqual(len(cases), 27)
        self.assertTrue(all(r['primary_http_status'] == 404 for r in cases))
        self.assertTrue(all(observer.evidence_role(r) == 'required-provenance-if-owning-primary-selected'
                            for r in cases if r['kind'] == 'module.asc'))
        self.assertFalse(BASIS['unchanged_security_boundary']['ignoreGradleMetadataRedirection_added'])

    def test_NEW05_selected_Portal_signatures_not_optional_or_cross_origin(self):
        cases = [r for r in MODEL['cause_cases'] if r['category'] == 'selected-origin-pom-signature-gap']
        self.assertEqual(len(cases), 3)
        self.assertTrue(all(observer.evidence_role(r) == 'required-provenance-if-owning-primary-selected' for r in cases))
        for pair in BASIS['origin_bound_marker_POM_pairs']:
            self.assertNotEqual(pair['central']['sha256'], pair['portal']['sha256'])
            self.assertIs(pair['signature_or_digest_transfer_authorized'], False)
        plan = copy.deepcopy(MODEL)
        case = next(r for r in plan['cause_cases'] if r['category'] == 'selected-origin-pom-signature-gap')
        case['category'] = 'optional-present-primary-sha256-sidecar-absence'
        with self.assertRaises(observer.ObservationRefusal):
            observer.validate_cause_plan(plan)

    def test_NEW06_no_wildcard_or_wrong_exact_target_route(self):
        for target in ('https://plugins-artifacts.gradle.org/*', MODEL['requests'][-1]['url'] + '.asc'):
            plan = copy.deepcopy(MODEL)
            plan['exact_observation_routes'][0]['target_url'] = target
            with self.assertRaises(observer.ObservationRefusal):
                observer.validate_cause_plan(plan)
        workflow = read_source(HERE.parents[1] / '.github/workflows/javafx-library-candidate.yml',
                               observer.CHANGED_WORKFLOW_SHA256)
        original = observer.restore_cause_workflow_routing(workflow)
        self.assertEqual(hashlib.sha256(original).hexdigest(), observer.ORIGINAL_WORKFLOW_SHA256)
        with self.assertRaises(observer.ObservationRefusal):
            observer.restore_cause_workflow_routing(workflow + b'# unrelated native-byte change\n')

    def test_NEW07_same_GAV_not_marker_implementation_substitution(self):
        plan = copy.deepcopy(MODEL)
        plan['seeds'][-1]['module'] = 'gradle-maven-publish-plugin'
        with self.assertRaises(observer.ObservationRefusal):
            observer.validate_cause_plan(plan)

    def test_NEW08_cause_basis_tamper_is_not_new_authority(self):
        basis = copy.deepcopy(BASIS)
        basis['proposed_exact_redirect_observation_pair']['independent_publisher_or_policy_authority'] = True
        with self.assertRaises(observer.ObservationRefusal):
            observer.validate_cause_basis(basis, MODEL)

    def test_NEW09_headers_retained_before_non200_without_body(self):
        observed, raw, response, factory, measured = self.response(404, [('Content-Length', '1000')])
        self.assertTrue(observed['headers_complete'])
        self.assertEqual(observed['http_status'], 404)
        self.assertFalse(observed['public_text_qualified'])
        self.assertEqual(raw, b'')
        self.assertEqual(response.read_calls, [])
        self.assertEqual(measured.requests, 1)
        self.assertEqual(len(factory.connections), 1)

    def test_NEW10_single_exact_source303_metadata_only(self):
        observed, raw, response, factory, _ = self.response(303, [('Location', MODEL['requests'][-1]['url'])])
        self.assertEqual(observed['status'], 'redirect-exact-target-observed')
        self.assertEqual(raw, b'')
        self.assertEqual(response.read_calls, [])
        self.assertEqual(len(factory.connections), 1)
        self.assertFalse(observed['canonical_publisher_target_authenticated'])
        self.assertFalse(observed['automatic_redirects_followed'])

    def test_NEW11_unapproved_public_host_is_not_followed(self):
        observed, raw, response, factory, _ = self.response(303, [('Location', 'https://unapproved.example.test/x.pom')])
        self.assertEqual(observed['public_Location'], 'https://unapproved.example.test/x.pom')
        self.assertEqual(observed['status'], 'refused')
        self.assertEqual(raw, b'')
        self.assertEqual(response.read_calls, [])
        self.assertEqual(len(factory.connections), 1)

    def test_NEW12_query_or_credentials_Location_is_digest_only(self):
        for location in ('https://repo.maven.apache.org/x?token=fake', 'https://fake:password@repo.maven.apache.org/x'):
            observed, raw, _, _, _ = self.response(303, [('Location', location)])
            self.assertIsNone(observed['public_Location'])
            self.assertEqual(observed['unqualified_Location_sha256'], [hashlib.sha256(location.encode()).hexdigest()])
            self.assertNotIn(location, json.dumps(observed))
            self.assertEqual(raw, b'')

    def test_NEW13_duplicate_Location_refuses_no_body(self):
        location = MODEL['requests'][-1]['url']
        observed, raw, response, _, _ = self.response(303, [('Location', location), ('location', location)])
        self.assertFalse(observed['headers_complete'])
        self.assertIsNone(observed['public_Location'])
        self.assertEqual(len(observed['unqualified_Location_sha256']), 2)
        self.assertEqual(raw, b'')
        self.assertEqual(response.read_calls, [])

    def test_NEW14_303_missing_Location_refuses(self):
        observed, raw, response, _, _ = self.response(303, [])
        self.assertFalse(observed['headers_complete'])
        self.assertEqual(observed['exception_type'], 'ObservationRefusal')
        self.assertEqual(raw, b'')
        self.assertEqual(response.read_calls, [])

    def test_NEW15_header_count_bytes_and_bool_status_caps(self):
        for status, headers in ((303, [('X', 'x')] * 65), (303, [('X', 'x' * 16385)]), (True, [])):
            observed, raw, response, _, _ = self.response(status, headers)
            self.assertFalse(observed['headers_complete'])
            self.assertEqual(raw, b'')
            self.assertEqual(response.read_calls, [])

    def test_NEW16_wrong_status_or_same_host_wrong_path_not_route(self):
        for status, location in ((307, MODEL['requests'][-1]['url']), (303, MODEL['requests'][-1]['url'] + '.asc')):
            observed, raw, _, factory, _ = self.response(status, [('Location', location)])
            self.assertEqual(observed['status'], 'refused')
            self.assertEqual(raw, b'')
            self.assertEqual(len(factory.connections), 1)

    def test_NEW17_target_selection_requires_fresh_complete_prefix(self):
        self.assertFalse(observer.select_explicit_target(prefix_observations(), MODEL))
        self.assertTrue(observer.select_explicit_target(prefix_observations(True), MODEL))
        with self.assertRaises(observer.ObservationRefusal):
            observer.select_explicit_target(prefix_observations(True)[:-1], MODEL)

    def test_NEW18_source_close_failure_withholds_target(self):
        observed, raw, _, factory, _ = self.response(303, [('Location', MODEL['requests'][-1]['url'])], close_error=True)
        rows = prefix_observations(True)
        rows[0] = observed
        self.assertFalse(observer.select_explicit_target(rows, MODEL))
        self.assertEqual(observed['status'], 'refused')
        self.assertEqual(raw, b'')
        self.assertEqual(factory.connections[0].close_calls, 1)

    def test_NEW19_real_Linux_entry_refuses_without_host_override(self):
        for entry in ('controller', 'main'):
            node = next(node for node in ast.parse(SOURCE_RAW).body if isinstance(node, ast.FunctionDef) and node.name == entry)
            self.assertEqual(ast.dump(node.body[0].value.args[0], include_attributes=False),
                             ast.dump(ast.parse("os.name == 'nt'", mode='eval').body, include_attributes=False))
        if os.name != 'nt':
            measured = budget()
            with self.assertRaises(observer.ObservationRefusal):
                observer.observe_one(MODEL['requests'][0], MODEL, measured)
            self.assertEqual(measured.requests, 0)
            with self.assertRaises(observer.ObservationRefusal):
                observer.controller(HERE.parents[1])
            with self.assertRaises(observer.ObservationRefusal):
                observer.main()
        # Real Windows never executes these entries in fake source controls.
        self.assertIs(NO_REAL_API_OR_SUBPROCESS, True)

    def test_NEW20_declared_target_GET_is_untrusted_POM_only(self):
        observed, raw, response, factory, measured = self.response(200, [('Content-Length', str(len(POM)))], POM,
                                                                row=MODEL['requests'][-1])
        self.assertEqual(raw, POM)
        self.assertTrue(observed['public_text_qualified'])
        self.assertEqual(observed['descriptor_kind'], 'pom')
        self.assertFalse(observed['signature_cryptographically_verified'])
        self.assertFalse(observed['publisher_provenance_qualified'])
        self.assertFalse(observed['independent_trust_or_consumer_acceptance'])
        self.assertEqual(factory.connections[0].requests[0][0], 'GET')
        self.assertEqual(measured.requests, 1)
        self.assertEqual(response.close_calls, 1)

    def test_NEW21_second_hop_target_redirect_is_refused(self):
        observed, raw, response, factory, _ = self.response(303, [('Location', 'https://plugins-artifacts.gradle.org/x.pom')],
                                                         row=MODEL['requests'][-1])
        self.assertEqual(observed['status'], 'refused')
        self.assertEqual(raw, b'')
        self.assertEqual(response.read_calls, [])
        self.assertEqual(len(factory.connections), 1)

    def test_NEW22_genuine_deadline_and_header_timeout_preserved(self):
        factory = FakeFactory(FakeResponse(303), header_timeout=True)
        measured = observer.NetworkBudget(100.0, clock=lambda: 100.0)
        with self.assertRaises(TimeoutError):
            observer.observe_one(MODEL['requests'][0], MODEL, measured, factory)
        self.assertEqual(factory.connections, [])
        observed, raw, _, factory, _ = self.response(header_timeout=True)
        self.assertEqual(observed['exception_type'], 'TimeoutError')
        self.assertEqual(raw, b'')
        self.assertEqual(factory.connections[0].close_calls, 1)

    def test_NEW23_compressed_or_duplicate_length200_no_body(self):
        for headers in ([('Content-Encoding', 'gzip')], [('Content-Length', '1'), ('content-length', '1')]):
            observed, raw, response, _, _ = self.response(200, headers, POM)
            self.assertFalse(observed['public_text_qualified'])
            self.assertEqual(raw, b'')
            self.assertEqual(response.read_calls, [])

    def test_NEW24_512KiB_hard_cap_no_probe_byte_or_promotion(self):
        observed, raw, response, _, measured = self.response(200, [], b'x' * 524288)
        self.assertEqual(len(raw), 524288)
        self.assertEqual(measured.body_bytes, 524288)
        self.assertEqual(sum(response.read_calls), 524288)
        self.assertFalse(observed['public_text_qualified'])
        self.assertEqual(observed['exception_type'], 'ObservationRefusal')

    def test_NEW25_request_max19_refuses_before_transport(self):
        measured = budget()
        measured.requests = 19
        factory = FakeFactory(FakeResponse(200, payload=POM))
        with self.assertRaises(observer.ObservationRefusal):
            observer.observe_one(MODEL['requests'][0], MODEL, measured, factory)
        self.assertEqual(factory.connections, [])

    def test_NEW26_withheld18_is_not_a_manufactured_complete19(self):
        observer.validate_cause_worker_report(fake_report(False), MODEL, {})
        observer.validate_cause_worker_report(fake_report(True), MODEL, {})
        forged = fake_report(False)
        forged['requests_attempted'] = 19
        with self.assertRaises(observer.ObservationRefusal):
            observer.validate_cause_worker_report(forged, MODEL, {})

    def test_NEW27_accepted58_URL_not_queued_or_transport_called(self):
        refused_ids = {row['id'] for row in MODEL['cause_cases']}
        accepted58 = [row for row in MODEL['original_requests'] if row['id'] not in refused_ids]
        self.assertEqual(len(accepted58), 58)
        existing = accepted58[0]
        factory = FakeFactory(FakeResponse(200, payload=POM))
        measured = budget()
        with self.assertRaises(observer.ObservationRefusal):
            observer.observe_one(existing, MODEL, measured, factory)
        self.assertEqual(factory.connections, [])
        self.assertEqual(measured.requests, 0)

    def test_NEW28_report_counter_and_trust_tamper_refuses(self):
        for key, value in (('requests_attempted', True), ('explicit_one_hop_target_requests', False),
                           ('original14_binaries_or_sidecars_acquired', False), ('accepted_public58_replayed', False),
                           ('original_HTTP404_requests_replayed', False), ('raw_body_bytes', False)):
            report = fake_report(False)
            report[key] = value
            with self.assertRaises(observer.ObservationRefusal):
                observer.validate_cause_worker_report(report, MODEL, {})
        for flag in ('publisher_provenance_qualified', 'credential_cookie_proxy_inheritance',
                     'canonical_publisher_target_authenticated', 'public_text_qualified'):
            report = fake_report(False)
            report['observations'][0][flag] = True
            with self.assertRaises(observer.ObservationRefusal):
                observer.validate_cause_worker_report(report, MODEL, {})
        report = fake_report(False)
        report['observations'][0]['body_bytes'] = False
        with self.assertRaises(observer.ObservationRefusal):
            observer.validate_cause_worker_report(report, MODEL, {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
