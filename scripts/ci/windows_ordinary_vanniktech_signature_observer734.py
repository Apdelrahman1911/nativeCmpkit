# SPDX-License-Identifier: Apache-2.0
"""One NEW source-held Central detached-signature acquisition, NOT admission.

Cached authenticated source303 metadata is fixed in reviewed source, not read
from an arbitrary caller archive/file and never reGETted. At most one target is
requested; every redirect refuses without a hop or fallback. Any captured body
is PRIVATE and UNINSPECTED. No signature syntax/key/crypto or cached POM access
is granted. This is Windows runner prerequisite work, not NATIVE-005 tests.
The immutable legacy Win32/owned Job/GO/descriptor/cleanup primitives are reused
unchanged; no host, base constant or function overrides.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import stat
import subprocess
import sys
import threading
import time
import types
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = 'scripts/ci/windows_ordinary_dependency_observer742.py'
BASE_SHA256 = '23c89b500571dff6f347a349b59391e0b6c816493f08b2232130f7aa73d82c14'
BASE_BYTES = 65242
OWN_PATH = 'scripts/ci/windows_ordinary_vanniktech_signature_observer734.py'
PLAN = 'scripts/ci/windows-ordinary-signature734-plan.json'
PLAN_SHA256 = 'bf3cdca3083092e7e79ab583e34d48eb04a8e7bd1d337963e1a1aad5bf266632'
CACHE_PATH = 'scripts/ci/windows-ordinary-signature734-source303.json'
CACHE_SHA256 = '58fcf624993d8663fd87602124c94bc652ee2aba1f56a51eb86f41a314ff64cd'
CACHE_BYTES = 2813
OUTPUT = 'build/ci-verification/windows-ordinary-signature734'
CHOICE = 'windows-ordinary-dependency-observation1'
REPOSITORY = 'Apdelrahman1911/nativeCmpkit'
REF = 'refs/heads/development/javafx-ordinary-consumer1'
TOTAL_SECONDS = 90
CLEANUP_SECONDS = 15
ACQUISITION_SECONDS = 60
IO_SECONDS = 20
MAX_REQUESTS = 1
MAX_BODY = 524288
MAX_TOTAL_BODY = 524288
MAX_CAPTURE = 65536
SOURCE_LIMIT = 1048576
MAX_HEADERS = 64
MAX_HEADER_BYTES = 16384
MAX_PUBLIC_LOCATION = 2048
PLAN_SCHEMA = 'nativecmpkit-Windows-one-NEW-signature-plan734-r2'
WORKER_SCHEMA = 'nativecmpkit-Windows-one-NEW-signature-worker734-r2'
INTENT_SCHEMA = 'nativecmpkit-Windows-one-NEW-signature-intent734-r2'
CONTROLLER_SCHEMA = 'nativecmpkit-Windows-one-NEW-signature-controller734-r2'
CACHE_SCHEMA = 'nativecmpkit-Windows-signature-source303-metadata734-r2'
CACHE_KEYS = frozenset(['Location_sha256', 'NO_ADMISSION', 'REVIEWED_EXPECTATIONS_SHA256', 'basis', 'metadata_is_not_routing_or_publisher_authority', 'requires_new_lead_source_result_review_before_dispatch', 'schema', 'source_record', 'source_record_index'])
CACHED_ROW_KEYS = frozenset(['Location_header_count', 'automatic_redirects_followed', 'body_bytes', 'body_sha256', 'canonical_publisher_target_authenticated', 'close_errors', 'complete_response', 'credential_cookie_proxy_inheritance', 'evidence_role', 'exception_type', 'headers_complete', 'http_status', 'id', 'independent_trust_or_consumer_acceptance', 'kind', 'network_request_started', 'original_GET_headers_reconstructed', 'other_redirects_refused', 'public_Location', 'public_Location_is_not_routing_or_publisher_authority', 'public_text_qualified', 'publisher_provenance_qualified', 'seed', 'signature_cryptographically_verified', 'status', 'unqualified_Location_sha256', 'url'])
BASIS_SHA256 = '4fecb8049990487da1df725eac45248af638e10ffe8b45ac592ed18e93e68870'
CACHED_ROW_SHA256 = '5765ca9a3fdf6466c3bbd7b0cb48ef73c63c0a3c4ebe9cd7b20eeefc61d73ee4'
EXACT_LIMITS = {'total_seconds': 90, 'acquisition_seconds': 60, 'cleanup_seconds': 15, 'io_seconds': 20, 'max_requests': 1, 'max_body_bytes': 524288, 'max_total_body_bytes': 524288, 'max_capture_bytes': 65536}
EXACT_TARGET = {'id': 'routed-convention-vanniktech-maven-publish-central:pom.asc', 'seed': 'routed-convention-vanniktech-maven-publish-central', 'kind': 'pom.asc', 'url': 'https://repo.maven.apache.org/maven2/com/vanniktech/maven/publish/com.vanniktech.maven.publish.gradle.plugin/0.37.0/com.vanniktech.maven.publish.gradle.plugin-0.37.0.pom.asc'}
EXACT_SEED = {'id': 'routed-convention-vanniktech-maven-publish-central', 'repository': 'central', 'group': 'com.vanniktech.maven.publish', 'module': 'com.vanniktech.maven.publish.gradle.plugin', 'version': '0.37.0'}
EXACT_SOURCE_ID = 'convention-vanniktech-maven-publish:pom.asc'
EXACT_SOURCE_SEED = 'convention-vanniktech-maven-publish'
EXACT_SOURCE_URL = 'https://plugins.gradle.org/m2/com/vanniktech/maven/publish/com.vanniktech.maven.publish.gradle.plugin/0.37.0/com.vanniktech.maven.publish.gradle.plugin-0.37.0.pom.asc'
EXACT_SOURCE_COORDINATE = {'id': 'convention-vanniktech-maven-publish', 'repository': 'plugin-portal', 'group': 'com.vanniktech.maven.publish', 'module': 'com.vanniktech.maven.publish.gradle.plugin', 'version': '0.37.0'}
EXACT_LOCATION_SHA256 = '6d0184b9d70fe09728b848dd4f211681b7efc6c888856107f58729a96489e47b'
SOURCE_FALSE_FIELDS = ('automatic_redirects_followed', 'canonical_publisher_target_authenticated', 'credential_cookie_proxy_inheritance', 'independent_trust_or_consumer_acceptance', 'original_GET_headers_reconstructed', 'public_text_qualified', 'publisher_provenance_qualified', 'signature_cryptographically_verified')
OLD_RUN = b'        run: python -I -S -B scripts/ci/windows_ordinary_dependency_cause_observer734.py\n'
NEW_RUN = b'        run: python -I -S -B scripts/ci/windows_ordinary_vanniktech_signature_observer734.py\n'
OLD_UPLOAD = b'          path: build/ci-verification/windows-ordinary-cause734/public/*\n'
NEW_UPLOAD = b'          path: build/ci-verification/windows-ordinary-signature734/public/*\n'
REVIEWED_EXPECTATIONS_SHA256 = None


def _read_pinned_base_source():
    # No unchecked import/path reread: execute the exact immutable verified bytes.
    # First-stage stat/hash custody is followed by the unchanged native64/128
    # source identity checks in the real controller/worker before network GO.
    path = ROOT / BASE_PATH
    if ROOT.resolve(strict=True) != ROOT or path.resolve(strict=True) != path:
        raise ValueError('Exact owning root/base source only, no import alias')
    source_fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    def view(info):
        return tuple(getattr(info, key) for key in source_fields)
    def directory_view(info):
        return (info.st_dev, info.st_ino, info.st_mode, getattr(info, 'st_file_attributes', 0))
    parents = []
    for parent in (ROOT, ROOT / 'scripts', ROOT / 'scripts/ci'):
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
            raise ValueError('Import source directory reparse/link refused')
        parents.append((parent, directory_view(info)))
    before = path.lstat()
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != BASE_BYTES or
            getattr(before, 'st_file_attributes', 0) & 1024):
        raise ValueError('Exact bounded unshared legacy source only')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NOATIME', 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if view(opened) != view(before):
            raise ValueError('Named/descriptor import source differs')
        parts = []
        count = 0
        while True:
            part = os.read(fd, min(65536, BASE_BYTES + 1 - count))
            if not part:
                break
            parts.append(part)
            count += len(part)
            if count > BASE_BYTES:
                raise ValueError('Import source cap')
        raw = b''.join(parts)
        after_descriptor = os.fstat(fd)
    finally:
        os.close(fd)
    if view(before) != view(opened) or view(before) != view(after_descriptor) or view(before) != view(path.lstat()):
        raise ValueError('Full original source fields changed during bounded import')
    if any(directory_view(parent.lstat()) != pin for parent, pin in parents):
        raise ValueError('Import source parents changed')
    if len(raw) != BASE_BYTES or hashlib.sha256(raw).hexdigest() != BASE_SHA256:
        raise ValueError('Pinned accepted legacy source changed, never import live unreviewed bytes')
    return raw

_base_source = _read_pinned_base_source()
base = types.ModuleType('nativecmpkit_pinned_legacy_signature734')
base.__file__ = str(ROOT / BASE_PATH)
exec(compile(_base_source, base.__file__, 'exec'), base.__dict__)
del _base_source
ObservationRefusal = base.ObservationRefusal
need = base.need
digest = base.digest
bounded_time = base.bounded_time
relative_path = base.relative_path
directory_pin = base.directory_pin
read_regular = base.read_regular
strict_json = base.strict_json
coordinate_url = base.coordinate_url
validate_request = base.validate_request
create_owned = base.create_owned
write_exclusive = base.write_exclusive
json_bytes = base.json_bytes
verify_worker_job = base.verify_worker_job
WindowsJob = base.WindowsJob
assigned_go = base.assigned_go
safe_environment = base.safe_environment
manual_context = base.manual_context
NO_ADMISSION = dict(base.NO_ADMISSION)


class NetworkBudget:
    def __init__(self, deadline, clock=time.monotonic):
        self.deadline = deadline
        self.clock = clock
        self.requests = 0
        self.body_bytes = 0

    def start(self):
        bounded_time(self.deadline, 'One NEW signature acquisition deadline exhausted', self.clock)
        need(type(self.requests) is int and 0 <= self.requests < MAX_REQUESTS,
             'Exactly one NEW target; no source, POM, second hop, fallback or retry')
        self.requests += 1
        return min(self.deadline, self.clock() + IO_SECONDS)

    def receive(self, count):
        need(type(count) is int and count >= 0 and type(self.body_bytes) is int and
             0 <= self.body_bytes <= MAX_TOTAL_BODY - count,
             'One-target 512KiB aggregate raw-byte bound')
        self.body_bytes += count


def validate_plan(plan):
    need(type(plan) is dict and digest(json_bytes(plan)) == PLAN_SHA256,
         'Only the immutable owning one-NEW-target source plan, never caller authority')
    need(plan.get('schema') == PLAN_SCHEMA and plan.get('repository') == REPOSITORY and
         plan.get('ref') == REF and plan.get('choice') == CHOICE and
         plan.get('requests') == [EXACT_TARGET] and plan.get('seeds') == [EXACT_SEED] and
         coordinate_url(EXACT_SEED, 'pom.asc') == EXACT_TARGET['url'],
         'Only the exact Vanniktech Central same-GAV detached-signature target')
    limits = plan['limits']
    need(set(limits) == set(EXACT_LIMITS) and all(type(limits[key]) is int and
         limits[key] == value for key, value in EXACT_LIMITS.items()), 'Frozen one-target limits')
    need(plan['cached_source_metadata'] == {'path': CACHE_PATH, 'bytes': CACHE_BYTES,
         'sha256': CACHE_SHA256, 'record_index': 2, 'original_source_GETs_replayed': 0},
         'Source-held cached metadata only; no archive, caller file or source GET')
    need(plan['no_admission'] == NO_ADMISSION and plan['REVIEWED_EXPECTATIONS_SHA256'] is None and
         plan['independently_expected_signature_SHA256'] is None and
         plan['publisher_key_fingerprint'] is None and
         plan['payload_policy'] == 'private-uninspected-no-syntax-key-or-crypto-operation' and
         plan['cached_POM_access_authorized'] is False and
         plan['windows_runner_prerequisite_only'] is True and
         type(plan['native_webview_request_state_tests_executed']) is int and
         plan['native_webview_request_state_tests_executed'] == 0,
         'Acquisition metadata is not payload, publisher, consumer or WebView request-state acceptance')
    return plan


def validate_cached_metadata(metadata):
    need(type(metadata) is dict and set(metadata) == CACHE_KEYS and
         metadata.get('schema') == CACHE_SCHEMA and metadata.get('source_record_index') == 2 and
         type(metadata.get('source_record_index')) is int,
         'Exactly one held source303 metadata record')
    basis = metadata['basis']
    need(type(basis) is dict and digest(json_bytes(basis)) == BASIS_SHA256 and
         type(basis.get('run_id')) is int and basis['run_id'] == 42087525896 and
         type(basis.get('attempt')) is int and basis['attempt'] == 1 and
         type(basis.get('job_id')) is int and basis['job_id'] == 127456535149 and
         type(basis.get('artifact_id')) is int and basis['artifact_id'] == 13443631641 and
         basis.get('head_sha') == '20523c4f431d29ccbff2998686599301a8686fea',
         'Authenticated immutable source303 basis, not fresh or caller-supplied routing authority')
    row = metadata['source_record']
    need(type(row) is dict and set(row) == CACHED_ROW_KEYS and
         row.get('id') == EXACT_SOURCE_ID and row.get('seed') == EXACT_SOURCE_SEED and
         row.get('kind') == 'pom.asc' and row.get('url') == EXACT_SOURCE_URL and
         coordinate_url(EXACT_SOURCE_COORDINATE, 'pom.asc') == row['url'] and
         type(row.get('http_status')) is int and row['http_status'] == 303 and
         row.get('headers_complete') is True and type(row.get('Location_header_count')) is int and
         row['Location_header_count'] == 1 and row.get('public_Location') == EXACT_TARGET['url'] and
         row.get('unqualified_Location_sha256') == [] and
         metadata['Location_sha256'] == EXACT_LOCATION_SHA256 and
         digest(row['public_Location'].encode('ascii')) == EXACT_LOCATION_SHA256,
         'Actual clean unique source303 Location, exact same-GAV path and origin only')
    need(type(row.get('body_bytes')) is int and row['body_bytes'] == 0 and
         row.get('body_sha256') is None and row.get('close_errors') == [] and
         row.get('network_request_started') is True and row.get('status') == 'refused' and
         row.get('exception_type') == 'ObservationRefusal' and
         row.get('complete_response') is False and row.get('public_text_qualified') is False,
         'The old no-follow refusal is preserved; no source body or invented clean body success')
    need(all(row.get(key) is False for key in SOURCE_FALSE_FIELDS) and
         row.get('public_Location_is_not_routing_or_publisher_authority') is True and
         row.get('other_redirects_refused') is True and
         row.get('evidence_role') == 'required-provenance-if-owning-primary-selected' and
         digest(json_bytes(row)) == CACHED_ROW_SHA256,
         'Cached observations are not signing, provenance, optional-signature waiver or trust')
    need(metadata['NO_ADMISSION'] is True and metadata['REVIEWED_EXPECTATIONS_SHA256'] is None and
         metadata['metadata_is_not_routing_or_publisher_authority'] is True and
         metadata['requires_new_lead_source_result_review_before_dispatch'] is True,
         'A source proposal does not self-authorize dispatch or expected digests')
    return metadata


def validate_cached_bytes(raw):
    need(type(raw) is bytes and len(raw) == CACHE_BYTES and digest(raw) == CACHE_SHA256,
         'Exact immutable source-held cached metadata bytes and hash')
    return validate_cached_metadata(strict_json(raw))


def load_plan(root):
    raw, row = read_regular(root, PLAN)
    need(row['sha256'] == PLAN_SHA256, 'Owning one-target plan changed')
    return validate_plan(strict_json(raw)), row


def load_cached_metadata(root):
    # Fixed code-relative source endpoint. There is deliberately no CLI,
    # environment, ZIP, user archive or caller-file cache import.
    raw, row = read_regular(root, CACHE_PATH, CACHE_BYTES)
    return validate_cached_bytes(raw), row


def select_cached_target(metadata, plan):
    validate_plan(plan)
    validate_cached_metadata(metadata)
    return dict(EXACT_TARGET)


def restore_signature_workflow_routing(payload, plan):
    route = plan['workflow_routing']
    need(type(payload) is bytes and len(payload) == route['after_bytes'] and
         digest(payload) == route['after_sha256'] and payload.count(NEW_RUN) == 1 and
         payload.count(OLD_RUN) == 0 and payload.count(NEW_UPLOAD) == 1 and
         payload.count(OLD_UPLOAD) == 0,
         'Exactly two coupled observational command/public-JSON output spans')
    prior = payload.replace(NEW_RUN, OLD_RUN).replace(NEW_UPLOAD, OLD_UPLOAD)
    need(len(prior) == route['before_bytes'] and digest(prior) == route['before_sha256'] and
         route['before_bytes'] == 15299 and
         route['before_sha256'] == '204c367e1da4f234a6d7fc1131baa4b94d48be5a50f0a402b95759c92ff76e00',
         'All prior native, ordinary-consumer, private Stop, permissions and action bytes remain exact')
    return prior


def snapshot_sources(root, plan, clock=time.monotonic, deadline=None):
    validate_plan(plan)
    rows = {}
    for relative, expected in plan['source_bindings'].items():
        if deadline is not None:
            bounded_time(deadline, 'Held source custody exhausted one-target allocation', clock)
        raw, row = read_regular(root, relative)
        need(set(expected) == {'bytes', 'sha256'} and type(expected['bytes']) is int and
             (row['bytes'], row['sha256']) == (expected['bytes'], expected['sha256']),
             'Exact frozen prerequisite source changed: ' + relative)
        if relative == CACHE_PATH:
            validate_cached_bytes(raw)
        if relative == 'scripts/ci/javafx_ordinary_maven_consumer.py':
            assignments = [node for node in ast.parse(raw).body if isinstance(node, ast.Assign) and
                any(isinstance(target, ast.Name) and target.id == 'REVIEWED_EXPECTATIONS_SHA256'
                    for target in node.targets)]
            need(len(assignments) == 1 and isinstance(assignments[0].value, ast.Constant) and
                 assignments[0].value.value is None, 'Production expected authority must remain None')
        rows[relative] = row
    workflow, row = read_regular(root, '.github/workflows/javafx-library-candidate.yml')
    restore_signature_workflow_routing(workflow, plan)
    rows['.github/workflows/javafx-library-candidate.yml'] = row
    _raw, row = read_regular(root, PLAN)
    need(row['sha256'] == PLAN_SHA256, 'One-target plan changed during source custody')
    rows[PLAN] = row
    rows[OWN_PATH] = read_regular(root, OWN_PATH)[1]
    return rows


def payload_evidence_relative(row, payload):
    need(type(row) is dict and all(row.get(key) == EXACT_TARGET[key] for key in EXACT_TARGET) and
         type(payload) is bytes and type(row.get('body_bytes')) is int and
         row['body_bytes'] == len(payload) and len(payload) <= MAX_BODY and
         row.get('body_sha256') == (digest(payload) if payload else None) and
         row.get('public_text_qualified') is False and row.get('signature_syntax_inspected') is False,
         'Only bounded uninspected exact-target bytes; never public payload or staging authority')
    return 'private/000.pom.asc' if payload else None


def validate_worker_report(report, plan, before):
    validate_plan(plan)
    need(type(report) is dict and report.get('schema') == WORKER_SCHEMA and
         report.get('observational_protocol_complete') is True and report.get('no_admission') == NO_ADMISSION and
         report.get('source_inputs_before') == report.get('source_inputs_after') == before and
         report.get('source_inputs_held') is True and report.get('archive_reuse') == [] and
         report.get('windows_runner_prerequisite_only') is True and
         report.get('required_real_graph_binary_signatures_or_policy_complete') is False,
         'Source-held one-target metadata protocol, not dependency or WebView/native admission')
    for key, expected in {'requests_attempted': 1, 'planned_requests': 1,
            'new_selected_signature_target_requests': 1, 'fixed_failed18_requests_replayed': 0,
            'accepted_POM_requests_replayed': 0, 'accepted_public58_replayed': 0,
            'original_HTTP404_requests_replayed': 0, 'original14_binaries_or_sidecars_acquired': 0,
            'native_webview_request_state_tests_executed': 0}.items():
        need(type(report.get(key)) is int and report[key] == expected,
             'Exact NEW request/no-replay protocol counter: ' + key)
    need(report.get('cached_source_metadata_sha256') == CACHE_SHA256 and
         report.get('cached_source_record_sha256') == CACHED_ROW_SHA256 and
         report.get('cached_source_metadata_reused') is True and
         report.get('automatic_redirects_followed') is False and
         report.get('all_payloads_qualified_as_public_text') is False and
         report.get('signature_syntax_inspected') is False and
         report.get('cached_POM_read_or_extracted') is False,
         'Cached headers and raw acquisition cannot authorize payload inspection or second hops')
    observations = report.get('observations')
    need(type(observations) is list and len(observations) == 1 and type(observations[0]) is dict,
         'Exactly one genuine NEW target observation')
    row = observations[0]
    need({key: row.get(key) for key in EXACT_TARGET} == EXACT_TARGET and
         row.get('network_request_started') is True and type(row.get('body_bytes')) is int and
         0 <= row['body_bytes'] <= MAX_BODY and type(report.get('raw_body_bytes')) is int and
         report['raw_body_bytes'] == row['body_bytes'] and
         (row.get('http_status') is None or type(row['http_status']) is int and 100 <= row['http_status'] <= 599),
         'Exact target and bounded genuine byte/status numbers')
    need(row.get('status') in ('refused', 'captured-uninspected') and
         row.get('public_text_qualified') is False and row.get('signature_syntax_inspected') is False and
         type(row.get('complete_response')) is bool and row.get('payload_scope') == 'private-uninspected' and
         row.get('evidence_role') == 'required-provenance-if-owning-primary-selected' and
         row.get('public_Location_is_not_routing_or_publisher_authority') is True and
         row.get('other_redirects_refused') is True and all(row.get(key) is False for key in SOURCE_FALSE_FIELDS),
         'Every refused or captured target remains uninspected, unsigned and untrusted')
    need(row.get('public_Location') is None and
         type(row.get('Location_header_count')) is int and 0 <= row['Location_header_count'] <= MAX_HEADERS and
         type(row.get('unqualified_Location_sha256')) is list and
         len(row['unqualified_Location_sha256']) == row['Location_header_count'] and
         all(type(value) is str and re.fullmatch('[0-9a-f]{64}', value)
             for value in row['unqualified_Location_sha256']),
         'New server Location is count/digest ONLY, never captured URL text in public JSON')
    need(type(row.get('close_errors')) is list and
         (row.get('exception_type') is None or type(row['exception_type']) is str) and
         (row['body_bytes'] == 0 and row.get('body_sha256') is None or row['body_bytes'] > 0 and
          type(row.get('body_sha256')) is str and re.fullmatch('[0-9a-f]{64}', row['body_sha256'])),
         'Genuine reported hash/exception/close outcome, never an expected signature digest')
    if row['status'] == 'captured-uninspected':
        need(row['http_status'] == 200 and row['complete_response'] is True and row['body_bytes'] > 0 and
             row['close_errors'] == [] and row['exception_type'] is None,
             'Uninspected capture requires actual bounded200/EOF and clean closes')
    if row['body_bytes']:
        evidence = row.get('raw_evidence')
        need(type(evidence) is dict and evidence.get('path') == 'private/000.pom.asc' and
             evidence.get('bytes') == row['body_bytes'] and evidence.get('sha256') == row['body_sha256'],
             'Raw detached-signature evidence remains private and uninspected')
    else:
        need('raw_evidence' not in row, 'A zero-body refusal is not an acquired signature')


def evidence_role(row):
    if row['kind'].endswith('.sha256'):
        return 'optional-untrusted-registry-SHA256-sidecar'
    if row['kind'].endswith('.asc'):
        return 'required-provenance-if-owning-primary-selected'
    return 'required-selected-POM-descriptor' if row['kind'] == 'pom' else 'conditional-selected-Gradle-module-descriptor'

def public_location(value):
    """Expose only bounded credential/query-free public URL syntax, NOT approval."""
    if type(value) is not str:
        return None
    try:
        raw = value.encode('ascii', 'strict')
    except UnicodeError:
        return None
    if not 0 < len(raw) <= MAX_PUBLIC_LOCATION or any(c <= 32 or c >= 127 for c in raw):
        return None
    try:
        u = urllib.parse.urlsplit(value)
        good = (u.scheme == 'https' and u.username is None and u.password is None and
                u.port in (None, 443) and not u.query and not u.fragment and
                u.hostname is not None and re.fullmatch('[A-Za-z0-9][A-Za-z0-9.-]{1,253}', u.hostname) and
                '.' in u.hostname and not u.hostname.endswith('.') and
                u.path.startswith('/') and not value.endswith('?') and not value.endswith('#') and
                '%' not in value and '\\' not in value)
    except ValueError:
        return None
    return value if good else None

def bounded_response_headers(response, result):
    need(type(response.status) is int and 100 <= response.status <= 599, 'Genuine bounded HTTP status')
    headers = response.getheaders()
    need(type(headers) is list and len(headers) <= MAX_HEADERS and
         all(type(h) is tuple and len(h) == 2 and all(type(x) is str for x in h) for h in headers),
         'Bounded genuine header shape before every status refusal')
    need(sum(len(k.encode('latin-1', 'strict')) + len(v.encode('latin-1', 'strict'))
             for k, v in headers) <= MAX_HEADER_BYTES, 'Bounded public header bytes')
    locations = [value for key, value in headers if key.lower() == 'location']
    result['Location_header_count'] = len(locations)
    result['public_Location'] = None
    result['unqualified_Location_sha256'] = [digest(value.encode('utf-8')) for value in locations]
    need(len(locations) <= 1, 'Duplicate Location refused; no selection')
    need(response.status != 303 or len(locations) == 1, '303 requires its actual bounded Location')
    result['headers_complete'] = True
    return headers

def observe_one(row, plan, budget, connection_factory=None):
    validate_plan(plan)
    parsed = validate_request(row, plan)
    if connection_factory is None:
        need(os.name == 'nt', 'Real NEW signature acquisition is Windows owned-Job worker only')
    started = budget.clock()
    deadline = budget.start()
    result = dict(row, status='refused', body_bytes=0, body_sha256=None, complete_response=False,
                  public_text_qualified=False, exception_type=None, network_request_started=True,
                  http_status=None, headers_complete=False, Location_header_count=0,
                  public_Location=None, unqualified_Location_sha256=[], evidence_role=evidence_role(row),
                  public_Location_is_not_routing_or_publisher_authority=True,
                  canonical_publisher_target_authenticated=False, original_GET_headers_reconstructed=False,
                  independent_trust_or_consumer_acceptance=False, signature_syntax_inspected=False,
                  payload_scope='private-uninspected')
    connection = response = transport = None
    body = bytearray()
    try:
        factory = connection_factory or http.client.HTTPSConnection
        # No automatic redirect/proxy/auth/cookie/fallback. Exactly source-declared
        # NEW target only. Its immutable source witness is never requested again.
        connection = factory(parsed.hostname, port=443,
            timeout=min(IO_SECONDS, bounded_time(deadline, 'Request timeout', budget.clock)),
            context=ssl.create_default_context())
        connection.connect()
        transport = connection.sock
        need(transport is not None, 'Exact HTTPS connection required')
        transport.settimeout(min(IO_SECONDS, bounded_time(deadline, 'Request connect budget', budget.clock)))
        connection.request('GET', parsed.path, body=None, headers={
            'Accept': 'application/xml, application/json, text/plain, application/pgp-signature',
            'Accept-Encoding': 'identity', 'Connection': 'close',
            'User-Agent': 'NativeCmpKit-Uninspected-SignatureObserver734/2'})
        transport.settimeout(min(IO_SECONDS, bounded_time(deadline, 'Request headers budget', budget.clock)))
        response = connection.getresponse()
        result['http_status'] = response.status
        headers = bounded_response_headers(response, result)
        bounded_time(deadline, 'Changed status/header deadline', budget.clock)
        need(response.status == 200,
             'Every other redirect/non200 stays refused with bounded headers; no retry/fallback')
        lengths = [value for key, value in headers if key.lower() == 'content-length']
        encodings = [value for key, value in headers if key.lower() == 'content-encoding']
        need(len(lengths) <= 1 and len(encodings) <= 1 and
             (not encodings or encodings[0].lower() == 'identity'),
             'No duplicate length or compressed response body')
        declared = None
        if lengths:
            need(re.fullmatch('[0-9]{1,10}', lengths[0]) is not None, 'Exact bounded Content-Length')
            declared = int(lengths[0])
            need(0 < declared <= MAX_BODY, 'Response advertised body bound')
        while True:
            remaining = bounded_time(deadline, 'Request body budget', budget.clock)
            # Preserve the accepted owning-close/EOF lifetime fix. Closed
            # response skips only settimeout, never EOF/caps/framing checks.
            if not response.isclosed():
                transport.settimeout(min(IO_SECONDS, remaining))
            room = min(MAX_BODY - len(body), MAX_TOTAL_BODY - budget.body_bytes)
            need(room > 0, 'No remaining bounded raw body capacity')
            chunk = response.read1(min(65536, room))
            need(type(chunk) is bytes, 'Binary transport bytes required')
            if not chunk:
                break
            budget.receive(len(chunk))
            body.extend(chunk)
            need(len(body) <= MAX_BODY, 'Response metadata body512KiB cap exceeded')
        bounded_time(deadline, 'Measured request total exceeded20s', budget.clock)
        need(declared is None or declared == len(body), 'Partial/mismatched declared response')
        result['complete_response'] = True
        need(len(body) > 0, 'A zero body is not captured detached-signature evidence')
        result.update(status='captured-uninspected')
    except (ObservationRefusal, OSError, TimeoutError, UnicodeError, ValueError, RecursionError,
            OverflowError, ET.ParseError, http.client.HTTPException) as error:
        result['exception_type'] = type(error).__name__
    finally:
        close_errors = []
        for resource, name in ((response, 'response'), (connection, 'connection')):
            if resource is not None:
                try:
                    resource.close()
                except (OSError, http.client.HTTPException) as error:
                    close_errors.append({'resource': name, 'exception_type': type(error).__name__})
        result.update(body_bytes=len(body), body_sha256=digest(body) if body else None,
                      elapsed_seconds=budget.clock() - started, close_errors=close_errors,
                      automatic_redirects_followed=False, other_redirects_refused=True,
                      credential_cookie_proxy_inheritance=False,
                      signature_cryptographically_verified=False, publisher_provenance_qualified=False)
        if close_errors:
            result.update(status='refused', public_text_qualified=False)
    return result, bytes(body)

def worker(root, output, job_handle):
    need(sys.stdin.buffer.readline(16) == b'GO742\n', 'Owned Job assignment GO missing')
    need(os.name == 'nt', 'Real NEW signature acquisition is Windows-only and Job-contained')
    verify_worker_job(job_handle)
    started = time.monotonic()
    deadline = started + ACQUISITION_SECONDS
    plan, _identity = load_plan(root)
    before = snapshot_sources(root, plan, deadline=deadline)
    metadata, _metadata_identity = load_cached_metadata(root)
    target = select_cached_target(metadata, plan)
    pins = {output: directory_pin(output), output / 'public': directory_pin(output / 'public'),
            output / 'private': directory_pin(output / 'private')}
    budget = NetworkBudget(deadline)
    # No prefix loop, source GET, accepted POM, optional probe, retry or follow.
    observed, payload = observe_one(target, plan, budget)
    evidence = payload_evidence_relative(observed, payload)
    if evidence is not None:
        observed['raw_evidence'] = write_exclusive(output, evidence, payload, pins)
    after = snapshot_sources(root, plan, deadline=deadline)
    need(before == after, 'Held source/metadata identities changed during one-target acquisition')
    report = {'schema': WORKER_SCHEMA, 'observational_protocol_complete': True,
        'requests_attempted': budget.requests, 'planned_requests': MAX_REQUESTS,
        'new_selected_signature_target_requests': budget.requests,
        'fixed_failed18_requests_replayed': 0, 'accepted_POM_requests_replayed': 0,
        'accepted_public58_replayed': 0, 'original_HTTP404_requests_replayed': 0,
        'original14_binaries_or_sidecars_acquired': 0, 'automatic_redirects_followed': False,
        'cached_source_metadata_reused': True, 'cached_source_metadata_sha256': CACHE_SHA256,
        'cached_source_record_sha256': CACHED_ROW_SHA256,
        'all_payloads_qualified_as_public_text': False, 'signature_syntax_inspected': False,
        'cached_POM_read_or_extracted': False, 'raw_body_bytes': budget.body_bytes,
        'source_inputs_held': True, 'source_inputs_before': before, 'source_inputs_after': after,
        'observations': [observed], 'no_admission': dict(NO_ADMISSION), 'archive_reuse': [],
        'windows_runner_prerequisite_only': True, 'native_webview_request_state_tests_executed': 0,
        'elapsed_seconds': time.monotonic() - started,
        'required_real_graph_binary_signatures_or_policy_complete': False}
    need(report['elapsed_seconds'] < ACQUISITION_SECONDS, 'One-target acquisition60s bound')
    validate_worker_report(report, plan, before)
    write_exclusive(output, 'public/worker-observations.json', json_bytes(report), pins)
    print(json.dumps({'schema': report['schema'], 'observational_protocol_complete': True,
        'requests_attempted': budget.requests, 'planned_requests_max': MAX_REQUESTS,
        'cached_source_metadata_reused': True, 'original_sources_or_POM_replayed': 0,
        'signature_syntax_inspected': False, 'windows_runner_prerequisite_only': True,
        'source_inputs_held': True, 'no_admission': dict(NO_ADMISSION)}, sort_keys=True), flush=True)
    return 0


def controller(root):
    need(os.name == 'nt', 'Real NEW signature controller is Windows-only; no outputs/APIs on unsupported host')
    started = time.monotonic()
    deadline, execution_deadline = started + TOTAL_SECONDS, started + TOTAL_SECONDS - CLEANUP_SECONDS
    context = manual_context(os.environ)
    plan, plan_identity = load_plan(root)
    before = snapshot_sources(root, plan, deadline=execution_deadline)
    output = root.joinpath(*relative_path(OUTPUT).parts)
    # Existing complete/failed outputs never admit replay. Only bounded owning
    # build parents may be newly created; they are retained, not broadly removed.
    pins = {root: directory_pin(root)}
    current = root
    for part in output.relative_to(root).parts:
        next_path = current / part
        if next_path == output or not next_path.exists():
            create_owned(next_path, pins)
        else:
            pins[next_path] = directory_pin(next_path)
        current = next_path
    for name in ('public', 'private', 'runtime'):
        create_owned(output / name, pins)
    runtime = output / 'runtime'
    for name in ('home', 'tmp'):
        create_owned(runtime / name, pins)
    write_exclusive(output, 'public/source-intent.json', json_bytes({'schema': INTENT_SCHEMA,
        'context': context, 'plan_identity': plan_identity, 'source_inputs_before': before, 'no_admission': dict(NO_ADMISSION),
        'planned_requests_max': MAX_REQUESTS, 'fixed_failed18_requests_replayed': 0,
        'new_selected_signature_target_requests_max': 1, 'original62_refusals_preserved': 62,
        'original44_HTTP404_or_accepted58_replayed': 0, 'original14_reacquired': 0,
        'process_containment_not_OS_sandbox': True, 'cached_source_metadata_sha256': CACHE_SHA256,
        'cached_source_metadata_reused': True, 'accepted_POM_reGETs': 0, 'signature_syntax_inspected': False,
        'cached_POM_read_or_extracted': False, 'windows_runner_prerequisite_only': True,
        'native_webview_request_state_tests_executed': 0}), pins)
    process = job = None
    primary = None
    child_exit = None
    after = None
    cleanup = []
    threads = []
    capture_overflow = threading.Event()
    capture_errors = []
    captured = [0]
    capture_lock = threading.Lock()
    def capture(stream, relative):
        try:
            log = bytearray()
            while True:
                block = stream.read(65536)
                if not block:
                    break
                with capture_lock:
                    room = MAX_CAPTURE - captured[0]
                    portion = block[:max(0, room)]
                    log.extend(portion)
                    captured[0] += len(portion)
                    if len(portion) != len(block):
                        capture_overflow.set()
                        break
            write_exclusive(output, relative, bytes(log), pins)
        except BaseException as error:
            capture_errors.append({'stream': relative, 'exception_type': type(error).__name__})
        finally:
            stream.close()
    try:
        job = WindowsJob()
        executable = Path(sys.executable).resolve(strict=True)
        argv = [str(executable), '-I', '-S', '-B', '-u', str(Path(__file__).resolve()), '--worker', '--job-handle', str(int(job.handle))]
        startup = subprocess.STARTUPINFO()
        startup.lpAttributeList = {'handle_list': [int(job.handle)]}
        job.inherit(True)
        try:
            process = subprocess.Popen(argv, cwd=runtime, env=safe_environment(runtime, executable, os.environ),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True, startupinfo=startup)
        finally:
            job.inherit(False)
        for stream, relative in ((process.stdout, 'private/worker.stdout'), (process.stderr, 'private/worker.stderr')):
            thread = threading.Thread(target=capture, args=(stream, relative), daemon=False)
            thread.start()
            threads.append(thread)
        assigned_go(process, job)
        while process.poll() is None:
            bounded_time(execution_deadline, 'Owned observational child exceeded shared75s allocation')
            need(not capture_overflow.is_set() and not capture_errors, 'Bounded owned child streams refused')
            need(job.active_processes() <= 1, 'No descendant process or alternate tooling allowed')
            time.sleep(0.05)
        child_exit = process.wait(timeout=min(1, bounded_time(execution_deadline, 'Direct child terminal budget')))
        need(child_exit == 0, 'NEW signature observational worker protocol was not complete')
    except BaseException as error:
        primary = {'exception_type': type(error).__name__}
    finally:
        if process is not None:
            try:
                if job is not None and job.assigned_pid == process.pid:
                    job.terminate()
                    cleanup.append({'owned_job_terminated': True})
                elif process.poll() is None:
                    # Still blocked before GO; terminate only this direct owned
                    # stable Popen handle, never a guessed PID/foreign process.
                    process.terminate()
                    cleanup.append({'unassigned_direct_child_terminated': True, 'GO_sent': False})
                child_exit = process.wait(timeout=min(CLEANUP_SECONDS, bounded_time(deadline, 'Owned child cleanup reserve')))
                cleanup.append({'direct_child_terminal': True, 'exit': child_exit})
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'direct_child_terminal': False})
        job_empty = False
        if job is not None:
            try:
                while job.active_processes():
                    bounded_time(deadline, 'Owned Job empty accounting cleanup reserve')
                    time.sleep(0.02)
                job_empty = True
                cleanup.append({'owned_job_active_processes': 0})
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'owned_job_empty': False})
            try:
                job.close()  # KILL_ON_JOB_CLOSE holds even an earlier refusal.
                cleanup.append({'owned_job_handle_closed': True})
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'owned_job_handle_closed': False})
        for thread in threads:
            try:
                thread.join(timeout=bounded_time(deadline, 'Bounded capture-thread cleanup reserve'))
                need(not thread.is_alive(), 'Owned capture thread remains')
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'capture_thread_terminal': False})
        try:
            after = snapshot_sources(root, plan, deadline=deadline)
            need(before == after, 'Actual source before/after custody differs')
        except BaseException as error:
            cleanup.append({'exception_type': type(error).__name__, 'source_inputs_held': False})
        direct_terminal = process is not None and process.poll() is not None
        for path in (runtime / 'home', runtime / 'tmp', runtime):
            try:
                bounded_time(deadline, 'Owned empty runtime cleanup allocation')
                need(job_empty and direct_terminal and not any(thread.is_alive() for thread in threads),
                     'Fresh Job-empty/direct-terminal/thread-terminal precede owned runtime cleanup')
                need(directory_pin(path.parent) == pins[path.parent] and directory_pin(path) == pins[path],
                     'Fresh owning parent/child directory pins before empty removal')
                path.rmdir()  # Empty only: unexpected worker files are retained/refused, not recursively deleted.
                cleanup.append({'owned_empty_directory_removed': path.name})
            except BaseException as error:
                cleanup.append({'exception_type': type(error).__name__, 'owned_empty_directory_removed': False})
    worker_report = None
    report_error = None
    try:
        worker_payload, worker_identity = read_regular(output, 'public/worker-observations.json', MAX_BODY + SOURCE_LIMIT)
        worker_report = strict_json(worker_payload)
        validate_worker_report(worker_report, plan, before)
    except BaseException as error:
        report_error = {'exception_type': type(error).__name__}
    elapsed = time.monotonic() - started
    complete = (primary is None and report_error is None and child_exit == 0 and before == after and
                job_empty and direct_terminal and not capture_overflow.is_set() and not capture_errors and
                not any(thread.is_alive() for thread in threads) and elapsed < TOTAL_SECONDS and
                not any('exception_type' in row for row in cleanup) and worker_report is not None)
    report = {'schema': CONTROLLER_SCHEMA,
        'observational_protocol_complete': complete, 'child_exit': child_exit, 'context': context,
        'primary_refusal': primary, 'worker_receipt_refusal': report_error, 'source_inputs_held': before == after,
        'elapsed_seconds': elapsed, 'total_seconds': TOTAL_SECONDS, 'cleanup_seconds': CLEANUP_SECONDS,
        'combined_captured_bytes': captured[0], 'capture_overflow': capture_overflow.is_set(), 'capture_errors': capture_errors,
        'owned_job_empty': job_empty, 'owned_direct_child_terminal': direct_terminal, 'cleanup': cleanup,
        'no_admission': dict(NO_ADMISSION), 'original14_or_sidecars_reacquired': 0,
        'original62_refusals_preserved': 62, 'original44_HTTP404_or_accepted58_replayed': 0,
        'new_selected_signature_target_requests': None if worker_report is None else worker_report['new_selected_signature_target_requests'],
        'required_real_graph_binary_signatures_or_policy_complete': False,
        'Gradle_wrapper_Java_Rust_JAR_ZIP_native_policy_execution': 0, 'OS_sandbox_or_trusted_builder_claim': False,
        'cached_source_metadata_sha256': CACHE_SHA256, 'signature_syntax_inspected': False,
        'cached_POM_read_or_extracted': False, 'windows_runner_prerequisite_only': True,
        'native_webview_request_state_tests_executed': 0}
    write_exclusive(output, 'public/controller-result.json', json_bytes(report), pins)
    terminal_elapsed = time.monotonic() - started
    if terminal_elapsed >= TOTAL_SECONDS:
        write_exclusive(output, 'public/terminal-budget-refusal.json', json_bytes({'schema': report['schema'],
            'observational_protocol_complete': False, 'elapsed_seconds': terminal_elapsed, 'no_admission': dict(NO_ADMISSION)}), pins)
        return 2
    print(json.dumps({'schema': report['schema'], 'observational_protocol_complete': complete,
                      'no_admission': dict(NO_ADMISSION)}, sort_keys=True), flush=True)
    return 0 if complete else 2

def main():
    need(os.name == 'nt', 'Real NEW signature entry is Windows-only; no parser/outputs/APIs on unsupported host')
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--job-handle', type=int)
    args = parser.parse_args()
    if args.worker:
        need(args.job_handle is not None, 'A contained worker requires the owning inherited Job handle')
        return worker(ROOT, ROOT.joinpath(*relative_path(OUTPUT).parts), args.job_handle)
    need(args.job_handle is None, 'Job handle is internal; no caller-controlled controller options')
    return controller(ROOT)

if __name__ == '__main__':
    raise SystemExit(main())
