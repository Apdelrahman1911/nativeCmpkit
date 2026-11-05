#!/usr/bin/env python3
"""One NEW Windows ordinary-Maven Stop consumer; never the accepted library Stop.

Prospective source only: exact current2ee12-source intake and frozen lead707
producer/native HEAD precede isolated branch source adoption. Required reviewed
producer/Camera/Android completion remains a gate before ordinary native dispatch.
Reuses existing bounded local producer helpers, not their old consumer/test run.
Read-only hosted verification/private local staging; no remote publication/API.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET

import daemon_jvm
import failure_diagnostics
import library_tests as lt
import runtime_context
import webview_consumer as packaged
import javafx_ordinary_dependency_expectations as dependency_expectations

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = 'build/ci-verification/javafx-ordinary-windows'
FIXTURE = 'tests/consumer/javafx-ordinary-webview'
WORKFLOW = '.github/workflows/javafx-library-candidate.yml'
MANUAL_REFS = ('refs/heads/development/preview-hardening', 'refs/heads/development/javafx-ordinary-consumer1')
WINDOWS_FOCUS = 'windows-ordinary-consumer1'
DEPENDENCY = 'tests/dependency/javafx-http2-cancellation'
CLASS = 'nativecmpkit.consumer.OrdinaryCuredWebStopConsumerTest'
METHOD = 'normalMavenActivationBindsCuredPublicStopTransportAndOwnedLifetime'
MODES = ('module', 'pom')
RESERVE_MIB = 8192
METADATA_FILES = ('gradle/verification-metadata.xml',
                  'tests/consumer/javafx-ordinary-webview/gradle/verification-metadata.xml')
SOURCE_RECIPE_AUTHORITY = 'a27e4de4f217af01269d41d9bd45938b25fe0036afbfa04489f2d910782faf3f'
EXPECTATIONS_SOURCE = FIXTURE + '/gradle/reviewed-windows-staging-expectations.json'
# Deliberately unresolved. Only a separately reviewed/adopted manifest's actual
# digest can replace None; no checksum, publisher or staging trust is invented.
REVIEWED_EXPECTATIONS_SHA256 = None
# Actual checkout inputs, not a historical comparison/inverse view of settings.
INSTALLED_JDK17_INPUTS = {
    'settings.gradle.kts': (2472, 'f46255ba97080b1b117e85cfc563d957e30d8f9ff2ff7c327fffd6c59d286bc9'),
    'docs/testing/installed-jdk17-prerequisite.md': (2744, '7be847de00c744b0174d65090b62e6769309cc2eafa579f17794cdf92eea2959'),
}
# Exact source additions only, not mandatory historical commit/SHA pinning of
# actions or unrelated AGENTS/status/workflows. Runtime maps bind actual HEAD.
EXPECTED12 = {
    'docs/testing/javafx-private-maven-adoption.md': 'a32db3f15f87bffe54d17ddd2ff4aeccbbb830352d6c1ae4d1a4387bf056ebdb',
    FIXTURE + '/build.gradle.kts': '0805061c9be0c974204e81cfdfd64f66e282b251a8e95e7c6d529b98aaf6dd7d',
    FIXTURE + '/gradle.properties': 'e2a5c8e188f6aa1c2c9d0104f48715a71b5a0894d5e1fb6dcef2c2c0b57f951e',
    FIXTURE + '/settings.gradle.kts': 'd7a5915e93f177d4ee434f278c2b3a6380023304ea99e809e76f4b544724f3b3',
    FIXTURE + '/src/test/kotlin/nativecmpkit/consumer/OrdinaryCuredWebStopConsumerTest.kt': '09149718c5967b6857672d26a55d70d4c281a2c037794a759e3eb56b5a60cf48',
    DEPENDENCY + '/official-companion-supplement.json': 'a2cce99c5ad3a3628c9a042b454bc1e8b3f61eb308b392d78c5534687682e9d2',
    DEPENDENCY + '/private_web_resolution.py': '4f7c9e6ac132203852dc8ed7c4a6c1d55a5dda74b5b632c39d6ace68e94833c1',
    DEPENDENCY + '/stage_private_web.py': '07819a5019f4e92e9bc54089c789d139a93c9903dcc4fc8320a0bef331e41f59',
    DEPENDENCY + '/test_official_companion_fixture_contract.py': '775abd597a7c937c9366ca79ee396568ad43b63b82166801130fb3167c48b82a',
    DEPENDENCY + '/test_official_companion_provenance.py': '4ce193fb7348035e9484675df31abbcc9f85b8ceeb5e858583614615bf5241ac',
    DEPENDENCY + '/test_ordinary_consumer_fixture_contract.py': 'edf46f1d62f41793d0f88d93697ec39825c4ad2e86a9f46271d0c68d7e88c937',
    DEPENDENCY + '/test_private_web_adoption.py': '4a2063a7853cb490ff34757b24d16703a2d3142dc61247010c6d1dbbca79e9e3',
}
OWNERS = ('build_runtime_candidate.py', 'probe_runner.py', 'artifacts.json',
          'cancel-response-future.patch', 'NOTICE.md', 'LICENSE-GPLv2-Classpath.txt',
          'ADDITIONAL_LICENSE_INFO', 'ASSEMBLY_EXCEPTION')


def need(condition, message):
    if not condition:
        raise packaged.EvidenceError(message)


def manual_context():
    context = {'repository': os.environ.get('GITHUB_REPOSITORY'), 'event': os.environ.get('GITHUB_EVENT_NAME'),
               'ref': os.environ.get('GITHUB_REF'), 'platform': os.environ.get('NATIVECMPKIT_ORDINARY_PLATFORM')}
    need(context['repository'] == 'Apdelrahman1911/nativeCmpkit' and context['event'] == 'workflow_dispatch' and
         context['ref'] in MANUAL_REFS and context['platform'] == WINDOWS_FOCUS,
         'Only the exact repository/manual ordinary choice on the finite two development refs is admitted')
    return context


def write(path, value):
    packaged.write(path, value)  # Exclusive creation, never replace evidence.


def read(path, limit=16 * 1024**2):
    need(path.is_file() and not path.is_symlink(), 'Regular owned evidence required')
    before = path.stat()
    need(before.st_nlink == 1 and before.st_size <= limit, 'Bounded unshared evidence required')
    payload = path.read_bytes()
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Evidence changed during read')
    return payload


def dependency_metadata_preflight():
    """Both invocation roots need real metadata; syntax/checksums are not trust."""
    rows = []
    namespace = '{https://schema.gradle.org/dependency-verification}'
    for relative in METADATA_FILES:
        row = {'path': relative, 'metadata_usable': False, 'reason': 'missing'}
        try:
            path = lt.safe_path(ROOT, relative)
            if path.exists():
                payload = read(path)
                row.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), reason='unusable')
                need(not re.search(br'<!\s*(?:DOCTYPE|ENTITY)', payload, re.I), 'Unsafe verification XML refused')
                document = ET.fromstring(payload)
                configuration = document.find(namespace + 'configuration')
                components = document.find(namespace + 'components')
                need(document.tag == namespace + 'verification-metadata' and configuration is not None and
                     components is not None, 'Expected Gradle verification metadata structure')
                need(configuration.findtext(namespace + 'verify-metadata') == 'true' and
                     configuration.find(namespace + 'trusted-artifacts') is None,
                     'Metadata checks are required and artifact trust exceptions are not admitted')
                artifacts = components.findall(namespace + 'component/' + namespace + 'artifact')
                need(artifacts and all(artifact.findall(namespace + 'sha256') and
                     all(re.fullmatch('[0-9a-f]{64}', checksum.get('value', '')) is not None
                         for checksum in artifact.findall(namespace + 'sha256')) for artifact in artifacts),
                     'Nonempty exact SHA256 artifact checks required')
                row.update(metadata_usable=True, artifact_count=len(artifacts), reason='checksum-structure-only')
        except (OSError, ValueError, ET.ParseError):
            row['reason'] = 'unusable'
        rows.append(row)
    return {'schema_version': 1, 'metadata': rows,
            'metadata_usable_for_strict_execution': all(row['metadata_usable'] for row in rows),
            'independent_trust_qualified': False, 'dependencies_resolved': False,
            'scope': 'Presence/held XML/checksum structure for producer and separate -p consumer only; no graph coverage, advertised checksum/signature review, Gradle enforcement, security or release clearance'}


def dependency_expectations_preflight():
    """Pre-freeze policies must equal independently approved deterministic payloads."""
    need(type(REVIEWED_EXPECTATIONS_SHA256) is str and
         re.fullmatch('[0-9a-f]{64}', REVIEWED_EXPECTATIONS_SHA256) is not None,
         'Independently reviewed expectation manifest authority is missing; no local checksum bootstrap')
    payload = read(lt.safe_path(ROOT, EXPECTATIONS_SOURCE), dependency_expectations.MAX_MANIFEST_BYTES)
    policies = dependency_expectations.metadata_payloads(payload, REVIEWED_EXPECTATIONS_SHA256)
    need(set(policies) == set(METADATA_FILES), 'The two actual invoked roots need independently scoped policies')
    for relative, expected in policies.items():
        need(read(lt.safe_path(ROOT, relative)) == expected,
             'Metadata must be materialized and held before the cohort; no mid-run checksum or signature-policy rewrite')
    return payload  # Immutable approved input bytes, never a mutable parsed trust dictionary.


def compiler_diagnostics(output):
    """Preserve finite public compiler failures from owned logs, not transcripts."""
    need(output == lt.safe_path(ROOT, OUTPUT) and output.is_dir(), 'Exact owned ordinary diagnostics directory required')
    rows = []
    for name in ('producer.log', 'module/resolution.log', 'pom/resolution.log', 'native/consumer.log'):
        path = lt.safe_path(output, name)
        if not path.exists():
            continue
        before = path.stat()
        need(path.is_file() and before.st_nlink == 1, 'Unshared owned diagnostic log required')
        if before.st_size > failure_diagnostics.MAX_LOG_BYTES:
            rows.append({'name': name, 'bytes': before.st_size, 'inspected': False,
                         'limit': 'Log exceeds bounded diagnostic input size; original retained locally'})
            continue
        payload = read(path, failure_diagnostics.MAX_LOG_BYTES)
        excerpts = failure_diagnostics.sections(payload.decode('utf-8', errors='replace').splitlines())
        rows.append({'name': name, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                     'inspected': True, 'excerpts': excerpts,
                     'excerpt_limit_may_omit_sections': len(excerpts) == failure_diagnostics.MAX_EXCERPTS})
    return {'schema_version': 1, 'logs': rows, 'full_logs_uploaded': False,
            'compiler_or_native_success_inferred': False,
            'scope': 'Existing bounded credential-filtered source errors/Gradle causes from four owned public-fixture logs; not full logs, testcase proof or a general secret scrubber'}


def inputs():
    result = lt.snapshot_inputs(ROOT)
    for relative, (expected_bytes, expected_sha256) in INSTALLED_JDK17_INPUTS.items():
        payload = read(lt.safe_path(ROOT, relative), expected_bytes)
        actual_sha256 = hashlib.sha256(payload).hexdigest()
        need(len(payload) == expected_bytes and actual_sha256 == expected_sha256,
             'Exact installed-JDK17 settings afterimage and prerequisite source required')
        need(relative not in result or result[relative] == actual_sha256,
             'Installed-JDK17 input disagrees with actual source snapshot')
        result[relative] = actual_sha256
    for relative, expected in EXPECTED12.items():
        path = lt.safe_path(ROOT, relative)
        need(lt.sha256(path) == expected, 'Exact adopted twelve-source JavaFX union required')
        result[relative] = expected
    extra = [WORKFLOW, 'tests/consumer/verify_artifacts.py', 'docs/migration/identity.json',
             'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', *METADATA_FILES, EXPECTATIONS_SOURCE,
             'scripts/ci/javafx_ordinary_dependency_expectations.py', *(DEPENDENCY + '/' + name for name in OWNERS)]
    for relative in extra:
        result[relative] = lt.sha256(lt.safe_path(ROOT, relative))
    for path in lt.source_files(ROOT, 'licenses'):
        result[path.relative_to(ROOT).as_posix()] = lt.sha256(path)
    return dict(sorted(result.items()))


def resources():
    class Memory(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                    *[(name, ctypes.c_ulonglong) for name in ('total_physical', 'available_physical',
                      'total_page', 'available_page', 'total_virtual', 'available_virtual', 'available_extended')]]
    memory = Memory()
    memory.length = ctypes.sizeof(memory)
    need(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)) != 0, 'Actual Windows available memory observation required')
    value = {'available_physical_bytes': memory.available_physical, 'free_disk_bytes': shutil.disk_usage(ROOT).free,
             'required_bytes': RESERVE_MIB * 1024**2}
    need(min(value['available_physical_bytes'], value['free_disk_bytes']) >= value['required_bytes'],
         '8GiB free memory/disk unavailable; do not spawn heavy work')
    return value


def command(consumer, mode, private_repository, output, task):
    need(mode in MODES and task in ('observePrivateWebResolution', 'ordinaryCuredWebStop'), 'Finite ordinary-consumer command required')
    return [str(ROOT / 'gradlew.bat'), '-p', str(consumer), '--no-daemon', '--no-parallel',
            '--no-configuration-cache', '--no-build-cache', '--console=plain', '--max-workers=2',
            '--dependency-verification', 'strict', '--project-cache-dir', str(output / mode / 'project-cache'),
            '-PnativecmpkitRepository=' + str(ROOT / 'build/verification-repo'),
            '-PnativecmpkitVersion=' + packaged.VERSION, '-PnativecmpkitPrivateJavafxRepository=' + str(private_repository),
            '-PnativecmpkitJavafxClassifier=win', '-PnativecmpkitMetadataMode=' + mode, task]


def bound_resolution(verifier, mode):
    need(verifier.get('passed') is True and verifier.get('ordinary_resolution_bytes_bound') is True and
         verifier.get('official_companion_pins_bound') is True and verifier.get('production_pins_required') is True and
         verifier.get('classpath_count') == 4 and verifier.get('classifier') == 'win' and verifier.get('metadata_mode') == mode and
         verifier.get('native_executions') == 0 and verifier.get('publication_ready') is False,
         'Real production-pin graph binding required; synthetic/model reports cannot enter')


def resolution_report_held(custody):
    path = Path(custody['path'])
    before = path.stat(follow_symlinks=False)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    need(not path.is_symlink() and before.st_nlink == 1 and identity == tuple(custody['file_identity']),
         'Replaced or changed retained verifier input refused; preserve all report evidence')
    payload = read(path)
    after = path.stat(follow_symlinks=False)
    need((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) == identity and
         len(payload) == custody['bytes'] and hashlib.sha256(payload).hexdigest() == custody['sha256'],
         'Retained verifier input bytes/identity must hold; no changed report graph acceptance')
    return True


def retained_resolution(path, saved, start, end):
    before = path.stat(follow_symlinks=False)
    payload = read(path)
    after = path.stat(follow_symlinks=False)
    source_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    need(source_identity == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) and
         start - 2_000_000_000 <= before.st_mtime_ns <= end + 2_000_000_000,
         'Exactly captured original resolution report identity must be fresh and held')
    saved.parent.mkdir(parents=True, exist_ok=True)
    with saved.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        owned = os.fstat(stream.fileno())
    closed = saved.stat(follow_symlinks=False)
    need(not saved.is_symlink() and closed.st_nlink == 1 and
         (owned.st_dev, owned.st_ino) == (closed.st_dev, closed.st_ino) and closed.st_size == len(payload),
         'Closed retained input must remain the exact exclusively written owned file')
    custody = {'path': str(saved), 'source_path': str(path), 'bytes': len(payload),
               'sha256': hashlib.sha256(payload).hexdigest(), 'source_identity': list(source_identity),
               'file_identity': [closed.st_dev, closed.st_ino, closed.st_size, closed.st_mtime_ns, closed.st_ctime_ns]}

    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'Duplicate resolution JSON key refused')
            result[key] = value
        return result

    def finite(_):
        raise packaged.EvidenceError('Nonfinite resolution JSON number refused')

    observed = json.loads(payload, object_pairs_hook=unique, parse_constant=finite)
    need(isinstance(observed, dict), 'Original resolution JSON object required')
    need(resolution_report_held(custody), 'Initial retained original observation must hold before verifier work')
    return observed, custody


def fresh_resolution(consumer, output, mode, start, end, private_repository, invoke, resolution_reports):
    path = lt.safe_path(consumer, f'build/reports/private-javafx-ordinary-resolution-{mode}.json')
    observed, custody = retained_resolution(path, output / f'{mode}/resolution.json', start, end)
    resolution_reports.append(custody)
    invoke('bind-resolution-' + mode,
           [sys.executable, '-B', str(ROOT / DEPENDENCY / 'private_web_resolution.py'), '--repository', str(private_repository), '--resolution', custody['path']],
           output / mode / 'resolution-verifier.log', 180)
    verifier = json.loads(read(output / mode / 'resolution-verifier.log').decode('utf-8'))
    bound_resolution(verifier, mode)
    need(resolution_report_held(custody), 'Exact retained verifier input must hold before this graph can be returned')
    write(output / mode / 'resolution-verification.json', verifier)
    write(output / f'{mode}/resolution-input-custody.json', custody)
    return observed


def graph_signature(observed):
    signature = []
    for row in observed['resolved_artifacts']:
        filename = row['file']
        if row['group'] == packaged.GROUP:
            canonical = 'nativecmpkit-webview-desktop-' + packaged.VERSION + '.jar'
            retained = 'calf-webview-desktop-' + packaged.VERSION + '.jar'
            need(row['module'] == 'nativecmpkit-webview-desktop' and row['version'] == packaged.VERSION and
                 filename in (canonical, retained), 'Only the already byte-bound exact library metadata alias may normalize')
            filename = canonical
        signature.append(tuple(row[key] for key in ('configuration', 'group', 'module', 'version')) + (filename, row['bytes'], row['sha256']))
    return sorted(signature)  # No path/cache normalization of bytes or other artifact identities.


def fresh_native(consumer, output, start, end, log):
    expected = 'NATIVECMPKIT_ORDINARY_CURED_STOP task=:ordinaryCuredWebStop gradle=9.7.1 java=17 mode=module classifier=win methods=1'
    reports = lt.source_files(consumer, 'build/test-results/ordinaryCuredWebStop')
    reports = [path for path in reports if path.name.startswith('TEST-') and path.suffix == '.xml']
    observations, cases, errors = [], [], []
    for path in reports:
        payload = read(path)
        fresh = start - 2_000_000_000 <= path.stat().st_mtime_ns <= end + 2_000_000_000
        saved = output / 'native/junit' / path.name
        saved.parent.mkdir(parents=True, exist_ok=True)
        with saved.open('xb') as stream:
            stream.write(payload)
        row = {'path': saved.relative_to(output).as_posix(), 'sha256': hashlib.sha256(payload).hexdigest(), 'fresh': fresh}
        try:
            parsed = lt.junit_cases(payload)
            cases.extend(parsed)
            row.update(lt.case_counts(parsed))
        except (ValueError, ET.ParseError) as error:
            errors.append(type(error).__name__)
        observations.append(row)
    try:
        lines = read(log, 64 * 1024**2).decode('utf-8', errors='replace').splitlines() if log.exists() else []
    except (OSError, ValueError) as error:
        lines = []
        errors.append(type(error).__name__)
    marker_ok = Counter(line for line in lines if line.startswith('NATIVECMPKIT_ORDINARY_CURED_STOP ')) == {expected: 1}
    value = {'reports': observations, 'testcases': cases, 'totals': lt.case_counts(cases), 'XML_parse_errors': errors,
             'exact_task_marker': marker_ok, 'all_reports_fresh': bool(reports) and all(row['fresh'] for row in observations),
             'exact_source_method_passed': len(reports) == len(cases) == 1 and cases == [{'classname': CLASS, 'name': METHOD, 'status': 'passed'}]}
    write(output / 'native/test-outcomes.json', value)
    # Preserve original failed/partial/stale XML BEFORE accepting or refusing.
    return value


def run(timeout):
    output = lt.safe_path(ROOT, OUTPUT)
    need(not output.exists(), 'Fresh ordinary-consumer output required; preserve earlier failed evidence')
    output.mkdir(parents=True)
    record = {'schema_version': 1, 'kind': 'NEW-private-ordinary-Maven-Windows-consumer1', 'passed': False,
              'started_utc': lt.utc_now(), 'host': 'windows-x64', 'classifier': 'win', 'executions': [],
              'source_recipe_authority_sha256': SOURCE_RECIPE_AUTHORITY, 'accepted_private_library_Stop_replayed': False,
              'native_methods_requested': [{'class': CLASS, 'method': METHOD}], 'metadata_modes_requested': list(MODES),
              'automatic_retries': False, 'publication_ready': False, 'packages_published': False,
              'full_native_corresponding_source_complete': False, 'security_or_API_ABI_clearance': False,
              'release_readiness_certified': False, 'independent_lead_acceptance': False,
              'process_cleanup_scope': 'Existing bounded owned launcher tree; no detached-process/OS sandbox attestation'}
    began, before, staged, private_files, runtime, phase = time.monotonic(), None, None, None, None, 'preflight'
    producer_environment, private_stage_sha = None, None
    resolution_reports = []
    lock = ROOT / 'build/ci-verification/.javafx-ordinary-windows.lock'
    lock_fd = None
    repository = ROOT / 'build/verification-repo'
    private_repository = ROOT / 'build/ci-verification/private-javafx-maven/ordinary-windows'
    consumer = ROOT / FIXTURE

    def invoke(name, argv, log, phase_timeout, environment=None, preserve_failed_native=False):
        log.parent.mkdir(parents=True, exist_ok=True)
        need(not log.exists(), 'Never overwrite original command streams')
        record.setdefault('resource_admissions', {})[name] = resources()
        remaining = timeout - int(time.monotonic() - began) - 30
        need(remaining > 0, 'Whole-run budget exhausted; no command started')
        start = time.time_ns()
        result = lt.execute(ROOT, argv, log, min(remaining, phase_timeout), RESERVE_MIB,
                            env=environment if environment is not None else producer_environment)
        end = time.time_ns()
        record['executions'].append({'phase': name, 'command': argv, 'execution': result,
                                     'started_ns': start, 'ended_ns': end,
                                     'log_sha256': lt.sha256(log) if log.exists() else None})
        if not preserve_failed_native:
            need(result['exit_code'] == 0 and not result.get('stop_reason'), 'Owned verification command failed; no retry or acceptance')
        return start, end

    try:
        record['manual_dispatch'] = manual_context()
        phase = 'dependency-metadata-preflight'
        record['dependency_metadata_preflight'] = dependency_metadata_preflight()
        write(output / 'dependency-metadata-preflight.json', record['dependency_metadata_preflight'])
        need(record['dependency_metadata_preflight']['metadata_usable_for_strict_execution'],
             'Producer and standalone consumer verification metadata must exist; a strict flag is not verification. Independent trust/coverage review remains required')
        expectation_payload = dependency_expectations_preflight()
        record['reviewed_expectations_sha256'] = REVIEWED_EXPECTATIONS_SHA256
        need(os.name == 'nt' and sys.platform == 'win32', 'Actual Windows host required; no Linux/macOS impersonation')
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        runtime = runtime_context.capture(expected_arch='x64', android_package='android-37.0', require_clean=True)
        need(runtime['host']['system'] == 'Windows', 'Actual Windows-x64 runtime required')
        record['source_revision'] = runtime['source_revision']
        write(output / 'runtime-before.json', runtime)
        before = inputs()
        write(output / 'inputs-before.json', before)
        need(not repository.exists() and not repository.is_symlink() and not (consumer / 'build').exists() and
             not private_repository.exists() and not private_repository.is_symlink(), 'Fresh library/private/fixture outputs required; do not delete stale inputs')
        cache = packaged.cache_state(ROOT)
        write(output / 'producer-cache-before.json', cache)
        need(cache['candidate_group_absent'], 'Candidate group in producer cache; no build/export allowed')
        producer_environment = packaged.environment(ROOT, output)
        phase = 'two-local-library-publications'
        producer = packaged.commands(ROOT, None)
        need(producer[-1] == 'stageWebViewVerificationPublications' and 'test' not in producer,
             'Only existing exact local producer helper, never old consumer or library Stop')
        invoke(phase, producer, output / 'producer.log', 2400, producer_environment)
        record['producer_daemon'] = daemon_jvm.observation(output / 'producer.log')
        expected_tasks = {':calf-webview:publish' + name + 'PublicationToNativecmpkitVerificationRepository'
                          for name in ('KotlinMultiplatform', 'Desktop')}
        markers = re.findall(r'(?m)^NATIVECMPKIT_WEBVIEW_STAGE task=(\S+) group=' + re.escape(packaged.GROUP) +
                             r' version=' + re.escape(packaged.VERSION) + '$', read(output / 'producer.log', 64 * 1024**2).decode('utf-8', errors='replace'))
        need(len(markers) == 2 and set(markers) == expected_tasks, 'Exactly two actual local WebView producer publications required')
        staged = packaged.staged_inputs(repository)
        write(output / 'staging-before.json', staged)
        phase = 'static-local-package-inspection'
        invoke(phase, [sys.executable, '-B', str(ROOT / 'tests/consumer/verify_artifacts.py'), '--repository', str(repository),
                       '--version', packaged.VERSION, '--module', packaged.MODULE, '--target', 'desktop', '--native-platform', 'windows-x64',
                       '--expected-native-revision', record['source_revision'], '--output', str(output / 'static-packages.json')],
               output / 'static-packages.log', 180, producer_environment)
        static = packaged.read_json(output / 'static-packages.json')
        need(static.get('success') is True and static.get('modules') == [packaged.MODULE] and
             static.get('targets') == ['metadata', 'desktop'] and static.get('release_readiness_certified') is False,
             'Actual staged WebView packages required, not producer classes/project fallback')
        write(output / 'library-dependency-selectors.json', packaged.selectors(repository))
        phase = 'private-candidate-packaging-only'
        candidate = output / 'runtime-candidate'
        invoke(phase, [sys.executable, '-B', str(ROOT / DEPENDENCY / 'build_runtime_candidate.py'), '--target-classifier', 'win',
                       '--download', '--output', str(candidate)], output / 'candidate-builder.log', 900, producer_environment)
        built = packaged.read_json(candidate / 'candidate.json')
        need(built.get('passed') is True and built.get('held_inputs') is True and built.get('classifier') == 'win' and
             built.get('compiler_host_classifier') == 'win' and built.get('cross_classifier_packaging_only') is False and
             built.get('native_executions') == built.get('library_tests') == 0, 'Actual Windows packaging candidate only; no accepted native replay')
        private_repository.parent.mkdir(parents=True, exist_ok=True)
        phase = 'new-private-ordinary-Maven-staging'
        invoke(phase, [sys.executable, '-B', str(ROOT / DEPENDENCY / 'stage_private_web.py'), '--candidate-root', str(candidate),
                       '--repository', str(private_repository)], output / 'private-stage.log', 300, producer_environment)
        private_stage = packaged.read_json(private_repository / 'private-javafx-staging.json')
        need(private_stage.get('kind') == 'private-ordinary-Maven-cured-web' and private_stage.get('passed') is True and
             private_stage.get('production_contract') is True and private_stage.get('classifier') == 'win' and
             private_stage.get('publication_ready') is False and private_stage.get('full_native_corresponding_source_complete') is False and
             isinstance(private_stage.get('files'), list) and len(private_stage['files']) == 4,
             'Actual four-file production private staging receipt required')
        private_stage_sha = lt.sha256(private_repository / 'private-javafx-staging.json')
        write(output / 'private-staging.json', private_stage)
        private_files = {row['file']: {'bytes': row['bytes'], 'sha256': row['sha256']} for row in private_stage['files']}
        phase = 'compare-prior-reviewed-local-staging-expectations'
        record['local_staging_expectations'] = dependency_expectations.compare_staging(
            expectation_payload, REVIEWED_EXPECTATIONS_SHA256, staged, private_files)
        write(output / 'local-staging-expectations.json', record['local_staging_expectations'])
        record['modes'] = {}
        graphs, environments = {}, {}
        for mode in MODES:
            phase = 'ordinary-resolution-' + mode
            environments[mode] = packaged.environment(ROOT, output, mode)
            start, end = invoke(phase, command(consumer, mode, private_repository, output, 'observePrivateWebResolution'),
                                output / mode / 'resolution.log', 1200, environments[mode])
            graphs[mode] = fresh_resolution(consumer, output, mode, start, end, private_repository, invoke, resolution_reports)
            record['modes'][mode] = {'classpaths_observed_and_bound': 4, 'native_executions': 0}
        phase = 'complete-four-classpath-graph-comparison'
        need(all(resolution_report_held(custody) for custody in resolution_reports),
             'Every exact retained verifier input must hold before complete graph comparison and NEW native request')
        signatures = {mode: graph_signature(graphs[mode]) for mode in MODES}
        equal = signatures['module'] == signatures['pom']
        write(output / 'complete-graph-comparison.json', {'equal': equal, 'graphs': signatures,
              'normalization': 'Only exact library metadata alias with independently checked identical staged JAR bytes; no other identities/bytes normalized',
              'native_runs_requested': 1, 'different_graphs_require_new_missing_scope': True})
        need(equal, 'Distinct module/POM byte graph requires a separately reviewed missing-native plan; no automatic duplicate test')
        phase = 'NEW-ordinary-public-Stop-native1'
        need(not (consumer / 'build/test-results').exists(), 'No previous native XML or native execution admitted')
        start, end = invoke(phase, command(consumer, 'module', private_repository, output, 'ordinaryCuredWebStop'),
                            output / 'native/consumer.log', 1200, environments['module'], preserve_failed_native=True)
        record['native'] = fresh_native(consumer, output, start, end, output / 'native/consumer.log')
        native_execution = record['executions'][-1]['execution']
        if record['native']['all_reports_fresh'] and record['native']['exact_task_marker'] and not record['native']['XML_parse_errors']:
            record['native_execution_count'] = record['native']['totals']['executed']
        need(native_execution['exit_code'] == 0 and not native_execution.get('stop_reason') and
             record['native']['exact_task_marker'] and record['native']['all_reports_fresh'] and
             record['native']['exact_source_method_passed'] and not record['native']['XML_parse_errors'],
             'Exactly one fresh NEW ordinary-Maven native method must pass with original Gradle0; no skips/extra/old library cases')
        # The native task re-observes module resolution. Keep earlier original
        # reports and require identical actual graph bytes, not a overwritten claim.
        native_resolution_path = lt.safe_path(consumer, 'build/reports/private-javafx-ordinary-resolution-module.json')
        current, native_custody = retained_resolution(native_resolution_path, output / 'native/resolution.json', start, end)
        resolution_reports.append(native_custody)
        invoke('post-native-production-pin-graph-binding',
               [sys.executable, '-B', str(ROOT / DEPENDENCY / 'private_web_resolution.py'), '--repository', str(private_repository),
                '--resolution', native_custody['path']],
               output / 'native/resolution-verifier.log', 180, producer_environment)
        native_binding = json.loads(read(output / 'native/resolution-verifier.log').decode('utf-8'))
        bound_resolution(native_binding, 'module')
        need(resolution_report_held(native_custody), 'Exact post-native verifier input must hold before graph/native reuse acceptance')
        need(current.get('metadata_mode') == 'module' and graph_signature(current) == signatures['module'],
             'Native task must hold the exact independently admitted module byte graph')
        write(output / 'native/resolution-verification.json', native_binding)
        write(output / 'native/resolution-input-custody.json', native_custody)
        record['pom_native_result_reused_for_identical_graph_only'] = True
        # Passing source-bound XML qualifies only authored assertion coverage.
        # No detached process absence, dependency certification or lead acceptance
        # is invented from a launcher exit or a whole-job timeout declaration.
        record['passed'] = True
    except (packaged.EvidenceError, OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        record['error'] = {'phase': phase, 'type': type(error).__name__,
                           'contract': str(error) if isinstance(error, packaged.EvidenceError) else 'Owned verification phase refused; inspect retained local evidence'}
    finally:
        held = []
        try:
            write(output / 'compile-diagnostics.json', compiler_diagnostics(output))
            record['bounded_compile_diagnostics_preserved'] = True
        except (OSError, ValueError):
            record['bounded_compile_diagnostics_preserved'] = False
            held.append(False)
        if before is not None:
            try:
                after = inputs()
                write(output / 'inputs-after.json', after)
                record['source_inputs_held'] = before == after and lt.git_revision(ROOT) == record['source_revision']
                record['source_input_count'] = len(before)
                held.append(record['source_inputs_held'])
            except (OSError, ValueError):
                held.append(False)
        if staged is not None:
            try:
                after_staged = packaged.staged_inputs(repository)
                write(output / 'staging-after.json', after_staged)
                record['staged_library_inputs_held'] = staged == after_staged
                held.append(record['staged_library_inputs_held'])
            except (OSError, ValueError):
                held.append(False)
        if private_files is not None:
            try:
                after_private = {name: {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
                                 for name in private_files for payload in [read(lt.safe_path(private_repository, name))]}
                write(output / 'private-staging-after.json', after_private)
                record['private_staged_inputs_held'] = private_files == after_private and private_stage_sha == lt.sha256(private_repository / 'private-javafx-staging.json')
                held.append(record['private_staged_inputs_held'])
            except (OSError, ValueError):
                held.append(False)
        if resolution_reports:
            try:
                record['resolution_report_count'] = len(resolution_reports)
                record['resolution_reports_held'] = all(resolution_report_held(custody) for custody in resolution_reports)
                write(output / 'resolution-report-custody.json', {'inputs': resolution_reports, 'held': record['resolution_reports_held']})
                held.append(record['resolution_reports_held'])
            except (packaged.EvidenceError, OSError, ValueError):
                record['resolution_reports_held'] = False
                held.append(False)
        if runtime is not None:
            try:
                after_runtime = runtime_context.capture(expected_arch='x64', android_package='android-37.0', require_clean=True)
                write(output / 'runtime-after.json', after_runtime)
                keys = ('source_revision', 'source_tree_dirty', 'host', 'java', 'rust', 'android_platform', 'compiler_runtime_fingerprint')
                record['runtime_identity_held'] = all(runtime[key] == after_runtime[key] for key in keys)
                cache = packaged.cache_state(ROOT)
                write(output / 'producer-cache-after.json', cache)
                held.extend([record['runtime_identity_held'], cache['candidate_group_absent']])
            except (OSError, ValueError):
                held.append(False)
        if lock_fd is not None:
            owned = os.fstat(lock_fd)
            os.close(lock_fd)
            try:
                current = lock.stat(follow_symlinks=False)
                need((owned.st_dev, owned.st_ino) == (current.st_dev, current.st_ino), 'Replaced foreign lock not removed')
                lock.unlink()
                record['owned_lock_removed'] = True
            except (OSError, ValueError):
                record['owned_lock_removed'] = False
            held.append(record['owned_lock_removed'])
        record['passed'] = record['passed'] and bool(held) and all(held)
        if not all(held):
            record.setdefault('error', {'phase': 'final-input-runtime-lock-custody', 'contract': 'Final held/ownership readback refused'})
        record.update(finished_utc=lt.utc_now(), elapsed_seconds=round(time.monotonic() - began, 3),
                      eligible_for_independent_lead_original_review=record['passed'],
                      detached_process_absence_verified=False, all_five_host_graphs_verified=False,
                      dependency_verification_metadata_qualified=False,
                      scope='Only NEW Windows ordinary consumer1 plus actual module/POM graph evidence; old Windows private library Stop excluded. No full-source/security/API-ABI/default convention/public adoption/issue/release clearance')
        write(output / 'receipt.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--timeout', type=int, default=6600)
    parser.add_argument('--metadata-preflight-only', action='store_true',
                        help='Read both actual verification XMLs, report truthful blockers, and start no producer/compiler/native work')
    args = parser.parse_args()
    if args.metadata_preflight_only:
        result = dependency_metadata_preflight()
        result['reviewed_expectations_usable'] = False
        if result['metadata_usable_for_strict_execution']:
            try:
                dependency_expectations_preflight()
                result['reviewed_expectations_usable'] = True
            except (packaged.EvidenceError, OSError, ValueError):
                result['expectation_reason'] = 'missing-unapproved-or-mismatched-reviewed-policy'
        print(json.dumps(result, sort_keys=True))
        return 0 if result['metadata_usable_for_strict_execution'] and result['reviewed_expectations_usable'] else 1
    need(3600 <= args.timeout <= 6600, 'Bounded whole-run timeout required')
    result = run(args.timeout)
    print(json.dumps({key: result[key] for key in ('passed', 'native_execution_count', 'publication_ready', 'error') if key in result}, sort_keys=True))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
