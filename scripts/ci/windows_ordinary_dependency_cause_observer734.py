# SPDX-License-Identifier: Apache-2.0
"""Independent cause successor: cached62 and failed18, NEVER consumer admission.

The accepted legacy observer/full120 plan stay exact. Only one fixed original
observational-job path derivative activates this separate output/plan. A fresh
clean exact source303 may allocate one explicitly declared same-GAV Central POM;
no generic redirect client, fallback, wildcard host, metadata trust or Stop replay.
The old Window Job/GO/native source identity/write-close/capture primitives are
reused from pinned immutable source, not patched or overridden.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
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
OWN_PATH = 'scripts/ci/windows_ordinary_dependency_cause_observer734.py'
PLAN = 'scripts/ci/windows-ordinary-cause734-plan.json'
PLAN_SHA256 = '58feda29d914c87557556d61d5280a3f4e75fe46c2f244a7ecb4a36d8eb30dec'
OUTPUT = 'build/ci-verification/windows-ordinary-cause734'
CHOICE = 'windows-ordinary-dependency-observation1'
REPOSITORY = 'Apdelrahman1911/nativeCmpkit'
REF = 'refs/heads/development/javafx-ordinary-consumer1'
TOTAL_SECONDS = 600
CLEANUP_SECONDS = 30
ACQUISITION_SECONDS = 420
IO_SECONDS = 20
MAX_REQUESTS = 19
MAX_BODY = 524288
MAX_TOTAL_BODY = 9961472
MAX_CAPTURE = 1048576
SOURCE_LIMIT = 1048576
ORIGINAL_WORKFLOW_BYTES = 15299
ORIGINAL_WORKFLOW_SHA256 = '5c52cf63010f18a3032f015882885b0ff57a0a1e9bc220e411fdbff138b96771'
CHANGED_WORKFLOW_BYTES = 15299
CHANGED_WORKFLOW_SHA256 = '204c367e1da4f234a6d7fc1131baa4b94d48be5a50f0a402b95759c92ff76e00'
OLD_RUN = b'        run: python -I -S -B scripts/ci/windows_ordinary_dependency_observer742.py\n'
NEW_RUN = b'        run: python -I -S -B scripts/ci/windows_ordinary_dependency_cause_observer734.py\n'
OLD_UPLOAD = b'          path: build/ci-verification/windows-ordinary-observation742/public/*\n'
NEW_UPLOAD = b'          path: build/ci-verification/windows-ordinary-cause734/public/*\n'


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
base = types.ModuleType('nativecmpkit_pinned_legacy_observer734')
base.__file__ = str(ROOT / BASE_PATH)
exec(compile(_base_source, base.__file__, 'exec'), base.__dict__)
del _base_source
# Explicit unchanged primitive bindings, not base constant/function/host overrides.
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
validate_public_text = base.validate_public_text
create_owned = base.create_owned
write_exclusive = base.write_exclusive
json_bytes = base.json_bytes
verify_worker_job = base.verify_worker_job
WindowsJob = base.WindowsJob
assigned_go = base.assigned_go
safe_environment = base.safe_environment
manual_context = base.manual_context
ORIGINS = dict(base.ORIGINS)
KINDS = tuple(base.KINDS)
NO_ADMISSION = dict(base.NO_ADMISSION)


class NetworkBudget:
    def __init__(self, deadline, clock=time.monotonic):
        self.deadline = deadline
        self.clock = clock
        self.requests = 0
        self.body_bytes = 0

    def start(self):
        bounded_time(self.deadline, 'Finite changed acquisition deadline exhausted', self.clock)
        need(self.requests < MAX_REQUESTS, 'Maximum failed18 plus one declared target count')
        self.requests += 1
        return min(self.deadline, self.clock() + IO_SECONDS)

    def receive(self, count):
        need(type(count) is int and count >= 0 and self.body_bytes + count <= MAX_TOTAL_BODY,
             'Shared19x512KiB raw metadata body bound exceeded')
        self.body_bytes += count


def restore_cause_workflow_routing(payload):
    need(type(payload) is bytes and len(payload) == CHANGED_WORKFLOW_BYTES and
         digest(payload) == CHANGED_WORKFLOW_SHA256 and payload.count(NEW_RUN) == 1 and
         payload.count(OLD_RUN) == 0 and payload.count(NEW_UPLOAD) == 1 and payload.count(OLD_UPLOAD) == 0,
         'Exactly coupled command/public-only output routing, no private/native change')
    original = payload.replace(NEW_RUN, OLD_RUN).replace(NEW_UPLOAD, OLD_UPLOAD)
    need(len(original) == ORIGINAL_WORKFLOW_BYTES and digest(original) == ORIGINAL_WORKFLOW_SHA256,
         'Every other original/native/consumer/workflow byte remains exact')
    return original


def snapshot_sources(root, plan, clock=time.monotonic, deadline=None):
    rows = {}
    for relative, expected in plan['source_bindings'].items():
        if deadline is not None:
            bounded_time(deadline, 'Source custody exhausted shared changed allocation', clock)
        raw, row = read_regular(root, relative)
        need(set(expected) == {'bytes', 'sha256'} and
             (row['bytes'], row['sha256']) == (expected['bytes'], expected['sha256']),
             'Held source prerequisite changed: ' + relative)
        rows[relative] = row
        for seed in plan['seeds']:
            for literal in seed['source_literals']:
                if literal['path'] == relative:
                    need(literal['text'].encode('utf-8') in raw, 'Exact declared seed source literal changed')
        if relative == CAUSE_BASIS_PATH:
            validate_cause_basis(strict_json(raw), plan)
        if relative == ORIGINAL_PLAN_PATH:
            original = strict_json(raw)
            need(original['schema'] == 'nativecmpkit-Windows-observation-plan742-r1' and
                 original['requests'] == plan['original_requests'] and original['seeds'] == plan['seeds'][:20] and
                 original['no_admission'] == NO_ADMISSION, 'Original120 source recipe remains exact and unexecuted')
        if relative == 'scripts/ci/javafx_ordinary_maven_consumer.py':
            assignments = [node for node in ast.parse(raw).body if isinstance(node, ast.Assign) and
                           any(isinstance(target, ast.Name) and target.id == 'REVIEWED_EXPECTATIONS_SHA256'
                               for target in node.targets)]
            need(len(assignments) == 1 and isinstance(assignments[0].value, ast.Constant) and
                 assignments[0].value.value is None, 'Production expectation authority must remain None')
    workflow, workflow_row = read_regular(root, '.github/workflows/javafx-library-candidate.yml')
    workflow = base.restore_diagnostic_workflow770(restore_cause_workflow_routing(workflow))
    recipe = plan['workflow_preservation']
    marker = recipe['suffix_marker'].encode('utf-8')
    need(workflow.count(marker) == 1, 'Only the independent appended observational job')
    prefix, suffix = workflow.split(marker)
    need(digest(marker + suffix) == recipe['suffix_sha256'], 'Independent original observation job source changed')
    old, new = recipe['options_before'].encode(), recipe['options_after'].encode()
    need(prefix.count(new) == 1, 'One exact original manual observation option, no native condition change')
    original = prefix.replace(new, old)
    need(len(original) == recipe['original_bytes'] and digest(original) == recipe['original_sha256'],
         'Original native/private Stop/ordinary bodies and conditions remain exact')
    rows['.github/workflows/javafx-library-candidate.yml'] = workflow_row
    _raw, plan_row = read_regular(root, PLAN)
    need(plan_row['sha256'] == PLAN_SHA256, 'Cause plan changed during source custody')
    rows[PLAN] = plan_row
    rows[OWN_PATH] = read_regular(root, OWN_PATH)[1]
    return rows

CAUSE_BASIS_PATH = 'docs/development/evidence/current-platform-recovery-20261101/windows-normal120-cause734/CAUSE62-METADATA-SOURCE-EXPECTATIONS734-R1.json'
CAUSE_BASIS_SHA256 = 'c0a41061083b82802076a1f2495d8593d8fec94fe1ce3d15c6cae577b131a5a3'
CAUSE_BASIS_BYTES = 89042
ORIGINAL_PLAN_PATH = 'scripts/ci/windows-ordinary-observation742-plan.json'
ORIGINAL_PLAN_SHA256 = 'e3d86c27cbb88650b306410c01a07b094c8166552f45f8b5ef1718b0cfaf5133'
ORIGINAL_WORKER_SHA256 = '65216c7cab53bbc53b3730f73b2fa8057d6aae21910a485cb62d3a6a1723a547'
EXACT_SOURCE_ID = 'convention-vanniktech-maven-publish:pom'
EXACT_TARGET_SEED = 'routed-convention-vanniktech-maven-publish-central'
EXACT_TARGET_ID = EXACT_TARGET_SEED + ':pom'
CAUSE_COUNTS = {'optional-present-primary-sha256-sidecar-absence': 14,
                'missing-format-or-dependent-probe': 27,
                'selected-origin-pom-signature-gap': 3,
                'portal-redirect-unfollowed': 18}
CAUSE_CASE_KEYS = {'id', 'seed', 'kind', 'url', 'original_http_status', 'category',
                   'primary_http_status'}
MAX_HEADERS = 64
MAX_HEADER_BYTES = 16384
MAX_PUBLIC_LOCATION = 2048
FAILED_PREFIX_REQUESTS = 18


def compact_cause_basis(basis):
    need(type(basis) is dict and
         basis.get('schema') == 'nativecmpkit-normal120-cause62-public-metadata-expectations734-r1' and
         basis.get('REVIEWED_EXPECTATIONS_SHA256') is None and basis.get('NO_ADMISSION') == NO_ADMISSION,
         'Only the exact independently scoped cached metadata basis; no trust promotion')
    cases = basis.get('cases')
    need(type(cases) is list and len(cases) == 62, 'All original62 are retained, no invented N/A')
    return [{key: row[key] for key in ('id', 'seed', 'kind', 'url', 'original_http_status', 'category')}
            | {'primary_http_status': row['primary_original_http_status']} for row in cases]


def validate_cause_plan(plan):
    need(type(plan) is dict and plan.get('schema') == 'nativecmpkit-Windows-cause-observation-plan734-r1' and
         plan.get('choice') == CHOICE and plan.get('repository') == REPOSITORY and plan.get('ref') == REF and
         plan.get('limits') == {'total_seconds': TOTAL_SECONDS, 'cleanup_seconds': CLEANUP_SECONDS,
             'acquisition_seconds': ACQUISITION_SECONDS, 'io_seconds': IO_SECONDS, 'max_requests': MAX_REQUESTS,
             'max_body_bytes': MAX_BODY, 'max_total_body_bytes': MAX_TOTAL_BODY, 'max_capture_bytes': MAX_CAPTURE} and
         plan.get('no_admission') == NO_ADMISSION and plan.get('archive_reuse') == [],
         'Exact fixed cause successor recipe/bounds; never raw archive or trust admission')
    scope = plan.get('cause_scope')
    need(scope == {'original_plan_sha256': ORIGINAL_PLAN_SHA256,
                   'original_worker_sha256': ORIGINAL_WORKER_SHA256,
                   'original_refusals_preserved': 62, 'original_HTTP404_retained_not_requested': 44,
                   'accepted_public58_replayed': 0, 'original_worker_private_stream_bytes_read': 0,
                   'original_GET_headers_reconstructed': False,
                   'classification_is_metadata_only': True,
                   'explicit_exact_target_requests_max': 1,
                   'automatic_redirects_or_fallback': False}, 'No widening of cause or original reuse scope')
    need(all(type(scope[key]) is int for key in ('original_refusals_preserved',
         'original_HTTP404_retained_not_requested', 'accepted_public58_replayed',
         'original_worker_private_stream_bytes_read', 'explicit_exact_target_requests_max')),
         'Exact integer source counters, not boolean substitutions')
    bindings = plan.get('source_bindings')
    need(type(bindings) is dict and bindings.get(CAUSE_BASIS_PATH) ==
         {'bytes': CAUSE_BASIS_BYTES, 'sha256': CAUSE_BASIS_SHA256} and
         bindings.get(ORIGINAL_PLAN_PATH) == {'bytes': 58898, 'sha256': ORIGINAL_PLAN_SHA256} and
         bindings.get(BASE_PATH) == {'bytes': BASE_BYTES, 'sha256': BASE_SHA256},
         'The original recipe and exact cause metadata basis remain held source inputs')
    need(plan.get('workflow_routing') == {
         'path': '.github/workflows/javafx-library-candidate.yml',
         'original_bytes': ORIGINAL_WORKFLOW_BYTES, 'original_sha256': ORIGINAL_WORKFLOW_SHA256,
         'changed_bytes': CHANGED_WORKFLOW_BYTES, 'changed_sha256': CHANGED_WORKFLOW_SHA256,
         'fragments': [{'original': OLD_RUN.decode('ascii'), 'changed': NEW_RUN.decode('ascii'), 'occurrences': 1},
                       {'original': OLD_UPLOAD.decode('ascii'), 'changed': NEW_UPLOAD.decode('ascii'), 'occurrences': 1}],
         'native_or_consumer_body_changes': 0},
         'Only exact inverse/forward observational command and public-output routing spans')
    seeds = plan.get('seeds')
    need(type(seeds) is list and len(seeds) == 21 and
         len({seed['id'] for seed in seeds}) == 21, 'The original20 plus one exact routed marker seed')
    expanded = []
    for index, seed in enumerate(seeds):
        need(type(seed) is dict and
             set(seed) == {'id', 'repository', 'group', 'module', 'version', 'source_literals', 'derivation'},
             'Exact declared repository-qualified seed schema')
        need(type(seed['source_literals']) is list and seed['source_literals'], 'Held source literals required')
        for literal in seed['source_literals']:
            need(type(literal) is dict and set(literal) == {'path', 'text'} and
                 literal['path'] in bindings and type(literal['text']) is str and
                 0 < len(literal['text']) <= 240, 'Only finite held literals, no recursive resolver')
        if index < 20:
            expanded.extend({'id': f"{seed['id']}:{kind}", 'seed': seed['id'], 'kind': kind,
                             'url': coordinate_url(seed, kind)} for kind in KINDS)
    need(plan.get('original_requests') == expanded and len(expanded) == 120 and
         len({row['url'] for row in expanded}) == 120, 'Original120 identity/order is preserved, not executed')
    original_rows = {row['id']: row for row in expanded}
    cases = plan.get('cause_cases')
    need(type(cases) is list and len(cases) == 62 and len({row['id'] for row in cases}) == 62,
         'The complete exact original62 cached refusal set')
    counts = {key: 0 for key in CAUSE_COUNTS}
    http = {303: 0, 404: 0}
    for row in cases:
        need(type(row) is dict and set(row) == CAUSE_CASE_KEYS and row['id'] in original_rows and
             {key: row[key] for key in ('id', 'seed', 'kind', 'url')} == original_rows[row['id']] and
             type(row['original_http_status']) is int and row['original_http_status'] in http and
             type(row['primary_http_status']) is int and row['primary_http_status'] in (200, 303, 404),
             'Exact source-derived cached refusal identity/status; no bool or caller alias')
        http[row['original_http_status']] += 1
        if row['original_http_status'] == 303:
            category = 'portal-redirect-unfollowed'
            need(row['url'].startswith(ORIGINS['plugin-portal']), 'Only original Portal redirects')
        elif row['kind'].endswith('.sha256') and row['primary_http_status'] == 200:
            category = 'optional-present-primary-sha256-sidecar-absence'
        elif row['kind'].split('.', 1)[0] == 'module':
            category = 'missing-format-or-dependent-probe'
            need(row['primary_http_status'] == 404 and row['url'].startswith(ORIGINS['central']),
                 'Absent format classification cannot waive a selected existing primary')
        else:
            category = 'selected-origin-pom-signature-gap'
            need(row['kind'] == 'pom.asc' and row['primary_http_status'] == 200 and
                 row['url'].startswith(ORIGINS['plugin-portal']),
                 'Missing selected-origin POM signatures remain required conditional gaps')
        need(row['category'] == category, 'No optional primary/signature laundering')
        counts[category] += 1
    need(counts == CAUSE_COUNTS and http == {303: 18, 404: 44}, 'All62 are accounted for without a request chase')
    prefix = [original_rows[row['id']] for row in cases if row['original_http_status'] == 303]
    source_seed = next(seed for seed in seeds[:20] if seed['id'] == EXACT_SOURCE_ID.rsplit(':', 1)[0])
    routed_seed = seeds[-1]
    need(routed_seed['id'] == EXACT_TARGET_SEED and routed_seed['repository'] == 'central' and
         all(routed_seed[key] == source_seed[key] for key in ('group', 'module', 'version', 'source_literals')),
         'Only the NEW observed same-GAV Central marker target, never implementation or signature transfer')
    target = {'id': EXACT_TARGET_ID, 'seed': EXACT_TARGET_SEED, 'kind': 'pom',
              'url': coordinate_url(routed_seed, 'pom')}
    need(len(prefix) == FAILED_PREFIX_REQUESTS and plan.get('requests') == prefix + [target] and
         len({row['url'] for row in plan['requests']}) == MAX_REQUESTS,
         'Only failed18 plus one predeclared conditional target; no accepted58 or optional404 replay')
    route = {'source_id': EXACT_SOURCE_ID, 'source_url': original_rows[EXACT_SOURCE_ID]['url'],
             'target_id': EXACT_TARGET_ID, 'target_url': target['url'], 'required_status': 303,
             'scope': 'public-text-observation-only', 'basis_sha256': CAUSE_BASIS_SHA256,
             'automatic_follow': False, 'publisher_or_policy_authority': False}
    need(plan.get('exact_observation_routes') == [route],
         'Only one exact source/status/path target; no host wildcard, query or undocumented historical URI')
    return plan


def validate_cause_basis(basis, plan):
    need(compact_cause_basis(basis) == plan['cause_cases'] and
         basis.get('category_counts') == CAUSE_COUNTS and
         basis['original_normal120']['worker_observations_sha256'] == ORIGINAL_WORKER_SHA256 and
         basis['original_normal120']['original_refusals_preserved'] is True,
         'Exact original classifications and nonadmission basis remain held')
    route = plan['exact_observation_routes'][0]
    supplied = basis.get('proposed_exact_redirect_observation_pair')
    need(type(supplied) is dict and supplied.get('source_request_id') == route['source_id'] and
         supplied.get('source_url') == route['source_url'] and supplied.get('target_url') == route['target_url'] and
         supplied.get('status') == 303 and supplied.get('public_text_observation_scope_only') is True and
         supplied.get('independent_publisher_or_policy_authority') is False and
         supplied.get('wildcard_CDN_host_route_or_historical_GET_target_authorized') is False,
         'NEW exact HEAD source metadata is not signing or blanket routing authority')


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
    if len(locations) == 1:
        result['public_Location'] = public_location(locations[0])
    result['unqualified_Location_sha256'] = [digest(value.encode('utf-8')) for value in locations
        if len(locations) != 1 or result['public_Location'] is None]
    need(len(locations) <= 1, 'Duplicate Location refused; no selection')
    need(response.status != 303 or len(locations) == 1, '303 requires its actual bounded Location')
    result['headers_complete'] = True
    return headers


def exact_redirect_matches(row, result, plan):
    return any(route['source_id'] == row['id'] and route['source_url'] == row['url'] and
               route['required_status'] == result.get('http_status') and
               result.get('headers_complete') is True and result.get('Location_header_count') == 1 and
               result.get('public_Location') == route['target_url'] and
               result.get('unqualified_Location_sha256') == []
               for route in plan['exact_observation_routes'])


def select_explicit_target(observations, plan):
    prefix = plan['requests'][:FAILED_PREFIX_REQUESTS]
    need(type(observations) is list and len(observations) == FAILED_PREFIX_REQUESTS and
         [{key: row.get(key) for key in ('id', 'seed', 'kind', 'url')} for row in observations] == prefix,
         'Fresh exact failed18 receipts before a separately declared target request')
    source = next(row for row in observations if row['id'] == EXACT_SOURCE_ID)
    source_request = next(row for row in prefix if row['id'] == EXACT_SOURCE_ID)
    return (source.get('status') == 'redirect-exact-target-observed' and
            type(source.get('body_bytes')) is int and
            source.get('body_bytes') == 0 and source.get('close_errors') == [] and
            source.get('exception_type') is None and exact_redirect_matches(source_request, source, plan))


def withheld_target(row):
    return dict(row, status='withheld-no-clean-exact-source-redirect', network_request_started=False,
                body_bytes=0, body_sha256=None, complete_response=False, public_text_qualified=False,
                http_status=None, headers_complete=False, Location_header_count=0, public_Location=None,
                unqualified_Location_sha256=[], close_errors=[], exception_type=None,
                evidence_role=evidence_role(row), automatic_redirects_followed=False,
                signature_cryptographically_verified=False, publisher_provenance_qualified=False,
                credential_cookie_proxy_inheritance=False, canonical_publisher_target_authenticated=False,
                original_GET_headers_reconstructed=False, independent_trust_or_consumer_acceptance=False)


def validate_cause_worker_report(report, plan, before):
    need(type(report) is dict and report.get('schema') == 'nativecmpkit-Windows-cause-observation-worker734-r1' and
         report.get('observational_protocol_complete') is True and report.get('no_admission') == NO_ADMISSION and
         report.get('source_inputs_before') == report.get('source_inputs_after') == before and
         type(report.get('original14_binaries_or_sidecars_acquired')) is int and report.get('original14_binaries_or_sidecars_acquired') == 0 and
         report.get('original62_cached_refusals') == plan['cause_cases'] and
         type(report.get('accepted_public58_replayed')) is int and report.get('accepted_public58_replayed') == 0 and type(report.get('original_HTTP404_requests_replayed')) is int and report.get('original_HTTP404_requests_replayed') == 0 and
         report.get('automatic_redirects_followed') is False and type(report.get('planned_requests')) is int and
         report.get('planned_requests') == MAX_REQUESTS and report.get('archive_reuse') == [] and
         type(report.get('fixed_failed18_requests')) is int and report.get('fixed_failed18_requests') == FAILED_PREFIX_REQUESTS and
         report.get('source_inputs_held') is True and
         report.get('required_real_graph_binary_signatures_or_policy_complete') is False,
         'Exact independently scoped source/metadata receipt; no full graph or dependency/native admission')
    observations = report.get('observations')
    need(type(observations) is list and len(observations) == MAX_REQUESTS and
         [{key: row.get(key) for key in ('id', 'seed', 'kind', 'url')} for row in observations] == plan['requests'],
         'Exact failed18 and explicitly retained conditional target receipt/order')
    for row in observations:
        need(row.get('evidence_role') == evidence_role(row) and row.get('signature_cryptographically_verified') is False and
             row.get('publisher_provenance_qualified') is False and row.get('automatic_redirects_followed') is False and
             row.get('credential_cookie_proxy_inheritance') is False and
             row.get('canonical_publisher_target_authenticated') is False and
             row.get('original_GET_headers_reconstructed') is False and
             row.get('independent_trust_or_consumer_acceptance') is False,
             'No optional signature laundering, historical reconstruction or output trust promotion')
        need(type(row.get('body_bytes')) is int and 0 <= row['body_bytes'] <= MAX_BODY and
             (row.get('http_status') is None or type(row['http_status']) is int),
             'Genuine bounded body/status numbers, no boolean substitutions')
        need(type(row.get('public_text_qualified')) is bool and type(row.get('complete_response')) is bool and
             (not row['public_text_qualified'] or
              (row.get('status') == 'observed' and row.get('http_status') == 200 and
               row['complete_response'] and row['body_bytes'] > 0 and
               type(row.get('body_sha256')) is str and re.fullmatch('[0-9a-f]{64}', row['body_sha256']))),
             'A header/non200/empty response can never become qualified primary text')
    need(type(report.get('raw_body_bytes')) is int and report['raw_body_bytes'] == sum(row['body_bytes'] for row in observations) and
         0 <= report['raw_body_bytes'] <= MAX_TOTAL_BODY and
         type(report.get('all_payloads_qualified_as_public_text')) is bool and
         report['all_payloads_qualified_as_public_text'] == all(row['public_text_qualified'] for row in observations),
         'Shared raw-byte and public-text counters are exact observations, not admission')
    selected = select_explicit_target(observations[:FAILED_PREFIX_REQUESTS], plan)
    need(type(report.get('requests_attempted')) is int and
         report['requests_attempted'] == FAILED_PREFIX_REQUESTS + int(selected) and
         type(report.get('explicit_one_hop_target_requests')) is int and
         report.get('explicit_one_hop_target_requests') == int(selected) and
         all(row.get('network_request_started') is True for row in observations[:FAILED_PREFIX_REQUESTS]),
         'Conditional declared target counts are not a manufactured full19 result')
    target = observations[-1]
    need(target.get('network_request_started') is selected and
         (selected or target == withheld_target(plan['requests'][-1])),
         'Without a fresh exact clean 303, target is withheld and never fetched')

def load_plan(root):
    raw, identity = read_regular(root, PLAN)
    need(identity['sha256'] == PLAN_SHA256, 'The owning fixed cause successor plan changed')
    return validate_cause_plan(strict_json(raw)), identity


def observe_one(row, plan, budget, connection_factory=None):
    validate_cause_plan(plan)
    parsed = validate_request(row, plan)
    if connection_factory is None:
        need(os.name == 'nt', 'Real changed observation is Windows owned-Job worker only')
    started = budget.clock()
    deadline = budget.start()
    result = dict(row, status='refused', body_bytes=0, body_sha256=None, complete_response=False,
                  public_text_qualified=False, exception_type=None, network_request_started=True,
                  http_status=None, headers_complete=False, Location_header_count=0,
                  public_Location=None, unqualified_Location_sha256=[], evidence_role=evidence_role(row),
                  public_Location_is_not_routing_or_publisher_authority=True,
                  canonical_publisher_target_authenticated=False, original_GET_headers_reconstructed=False,
                  independent_trust_or_consumer_acceptance=False)
    connection = response = transport = None
    body = bytearray()
    try:
        factory = connection_factory or http.client.HTTPSConnection
        # No automatic redirect/proxy/auth/cookie/fallback. Exactly source-declared
        # failed18 GETs; a separate predeclared target needs a fresh exact witness.
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
            'User-Agent': 'NativeCmpKit-Cause-TextObserver734/1'})
        transport.settimeout(min(IO_SECONDS, bounded_time(deadline, 'Request headers budget', budget.clock)))
        response = connection.getresponse()
        result['http_status'] = response.status
        headers = bounded_response_headers(response, result)
        bounded_time(deadline, 'Changed status/header deadline', budget.clock)
        if response.status == 303 and exact_redirect_matches(row, result, plan):
            # Not an automatic follow or body success. The worker allocates at
            # most one separately declared target after clean source close.
            result['status'] = 'redirect-exact-target-observed'
        else:
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
            details = validate_public_text(row['kind'], bytes(body), parsed.path.rsplit('/', 1)[1])
            result.update(details, status='observed', public_text_qualified=True)
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
    # The original real Windows host and exact owned-Job GO checks are retained.
    need(sys.stdin.buffer.readline(16) == b'GO742\n', 'Owned Job assignment GO missing')
    need(os.name == 'nt', 'Real acquisition is Windows-only and must be Job-contained')
    verify_worker_job(job_handle)
    started = time.monotonic()
    deadline = started + ACQUISITION_SECONDS
    plan, _identity = load_plan(root)
    before = snapshot_sources(root, plan, deadline=deadline)
    pins = {output: directory_pin(output), output / 'public': directory_pin(output / 'public'),
            output / 'private': directory_pin(output / 'private')}
    budget = NetworkBudget(deadline)
    results = []

    def retain(index, observed, payload):
        if payload:
            public = observed.get('public_text_qualified') is True
            name = (('public' if public else 'private') + f'/{index:03d}.' +
                    (observed['kind'] if public else 'refused.bin'))
            observed['raw_evidence'] = write_exclusive(output, name, payload, pins)
        results.append(observed)

    for index, row in enumerate(plan['requests'][:FAILED_PREFIX_REQUESTS]):
        bounded_time(deadline, 'Acquisition allocation exhausted before fixed failed18')
        retain(index, *observe_one(row, plan, budget))
    selected = select_explicit_target(results, plan)
    target = plan['requests'][-1]
    if selected:
        bounded_time(deadline, 'Separate exact target allocation exhausted')
        retain(FAILED_PREFIX_REQUESTS, *observe_one(target, plan, budget))
    else:
        retain(FAILED_PREFIX_REQUESTS, withheld_target(target), b'')
    # There is no raw accepted58 archive input or re-request. Missing optional
    # SHA256 sidecars do not authorize expectations or cross-origin agreement.
    after = snapshot_sources(root, plan, deadline=deadline)
    need(before == after, 'Actual source identities changed during changed observations')
    report = {'schema': 'nativecmpkit-Windows-cause-observation-worker734-r1',
        'observational_protocol_complete': True, 'requests_attempted': budget.requests,
        'planned_requests': MAX_REQUESTS, 'fixed_failed18_requests': FAILED_PREFIX_REQUESTS,
        'explicit_one_hop_target_requests': int(selected), 'automatic_redirects_followed': False,
        'all_payloads_qualified_as_public_text': all(row['public_text_qualified'] for row in results),
        'raw_body_bytes': budget.body_bytes, 'source_inputs_held': True,
        'source_inputs_before': before, 'source_inputs_after': after,
        'observations': results, 'no_admission': dict(NO_ADMISSION), 'archive_reuse': [],
        'original62_cached_refusals': plan['cause_cases'],
        'original_HTTP404_requests_replayed': 0, 'accepted_public58_replayed': 0,
        'original14_binaries_or_sidecars_acquired': 0, 'elapsed_seconds': time.monotonic() - started,
        'required_real_graph_binary_signatures_or_policy_complete': False}
    need(report['elapsed_seconds'] < ACQUISITION_SECONDS, 'Shared changed acquisition bound')
    validate_cause_worker_report(report, plan, before)
    write_exclusive(output, 'public/worker-observations.json', json_bytes(report), pins)
    print(json.dumps({'schema': report['schema'], 'observational_protocol_complete': True,
        'requests_attempted': budget.requests, 'planned_requests_max': MAX_REQUESTS,
        'explicit_one_hop_target_requests': int(selected), 'original_refusals_preserved': 62,
        'source_inputs_held': True, 'no_admission': dict(NO_ADMISSION)}, sort_keys=True), flush=True)
    return 0

def controller(root):
    need(os.name == 'nt', 'Real cause controller is Windows-only; no outputs/APIs on unsupported host')
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
    write_exclusive(output, 'public/source-intent.json', json_bytes({'schema': 'nativecmpkit-Windows-cause-observation-intent734-r1',
        'context': context, 'plan_identity': plan_identity, 'source_inputs_before': before, 'no_admission': dict(NO_ADMISSION),
        'planned_requests_max': MAX_REQUESTS, 'fixed_failed18_requests': FAILED_PREFIX_REQUESTS,
        'conditional_exact_target_requests_max': 1, 'original62_refusals_preserved': 62,
        'original44_HTTP404_or_accepted58_replayed': 0, 'original14_reacquired': 0,
        'process_containment_not_OS_sandbox': True}), pins)
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
            bounded_time(execution_deadline, 'Owned observational child exceeded shared570s allocation')
            need(not capture_overflow.is_set() and not capture_errors, 'Bounded owned child streams refused')
            need(job.active_processes() <= 1, 'No descendant process or alternate tooling allowed')
            time.sleep(0.05)
        child_exit = process.wait(timeout=min(1, bounded_time(execution_deadline, 'Direct child terminal budget')))
        need(child_exit == 0, 'Changed cause observational worker protocol was not complete')
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
        validate_cause_worker_report(worker_report, plan, before)
    except BaseException as error:
        report_error = {'exception_type': type(error).__name__}
    elapsed = time.monotonic() - started
    complete = (primary is None and report_error is None and child_exit == 0 and before == after and
                job_empty and direct_terminal and not capture_overflow.is_set() and not capture_errors and
                not any(thread.is_alive() for thread in threads) and elapsed < TOTAL_SECONDS and
                not any('exception_type' in row for row in cleanup) and worker_report is not None)
    report = {'schema': 'nativecmpkit-Windows-cause-observation-controller734-r1',
        'observational_protocol_complete': complete, 'child_exit': child_exit, 'context': context,
        'primary_refusal': primary, 'worker_receipt_refusal': report_error, 'source_inputs_held': before == after,
        'elapsed_seconds': elapsed, 'total_seconds': TOTAL_SECONDS, 'cleanup_seconds': CLEANUP_SECONDS,
        'combined_captured_bytes': captured[0], 'capture_overflow': capture_overflow.is_set(), 'capture_errors': capture_errors,
        'owned_job_empty': job_empty, 'owned_direct_child_terminal': direct_terminal, 'cleanup': cleanup,
        'no_admission': dict(NO_ADMISSION), 'original14_or_sidecars_reacquired': 0,
        'original62_refusals_preserved': 62, 'original44_HTTP404_or_accepted58_replayed': 0,
        'explicit_one_hop_target_requests': None if worker_report is None else worker_report['explicit_one_hop_target_requests'],
        'required_real_graph_binary_signatures_or_policy_complete': False,
        'Gradle_wrapper_Java_Rust_JAR_ZIP_native_policy_execution': 0, 'OS_sandbox_or_trusted_builder_claim': False}
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
    need(os.name == 'nt', 'Real cause entry is Windows-only; no parser/outputs/APIs on unsupported host')
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
