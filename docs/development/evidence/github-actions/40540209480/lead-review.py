"""Independently review current immutable UIKit Git/ZIP/JUnit/protocol evidence.

Read only the maintained development source and bounded public JSON/XML; never
execute extracted artifacts, expose console bodies or replay GitHub mutations.
This records a simulator runtime pass, not leak/sanitizer or release clearance.
"""
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
SOURCE = Path('/dev/shm/nativecmpkit-ci-ea79ab8c-20261027/40540209480')
OUT = Path(__file__).parent / 'review-archive'
REPO = 'Apdelrahman1911/nativeCmpkit'
REV = 'ea79ab8cf30132b4b37985f175d00287382ddca8'
CURRENT = REV
RUN = 40540209480
JOB = 122316654541
ART = 12751563165
PRIOR_ART = None
BASE = 'build/ci-verification/ios-iphone/'
IMAGE_TEST = 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UIImageConversionTest.kt'
BRIDGE = 'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt'
OLD = ROOT / 'docs/development/evidence/github-actions/40507789380'
OLD_REV = '8ab82a3fa41caad34cd7fb7a2d3722bfc25e3838'


def sha(payload):
    return hashlib.sha256(payload if isinstance(payload, bytes) else payload.read_bytes()).hexdigest()


def document(payload):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'Duplicate JSON key'
            result[key] = value
        return result
    return json.loads(payload, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def instant(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    assert parsed.utcoffset() is not None
    return parsed


assert not OUT.exists(), 'Never overwrite previous reviewed evidence'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == CURRENT
# Review this run's own immutable Git inputs; unrelated local JVM/docs work is dirty.
current_worktree_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))
run = document((SOURCE / 'run-final.json').read_bytes())
jobs = document((SOURCE / 'jobs-final.json').read_bytes())['jobs']
arts = document((SOURCE / 'artifacts-final.json').read_bytes())['artifacts']
collection = document((SOURCE / 'collection.json').read_bytes())
assert run['id'] == RUN and run['head_sha'] == REV and run['run_attempt'] == 1
assert run['repository']['full_name'] == REPO and run['status'] == 'completed' and run['conclusion'] == 'success'
assert run['event'] == 'workflow_dispatch' and run['head_branch'] == 'development/preview-hardening'
assert {a['id'] for a in arts} == {ART}
job = next(j for j in jobs if j['id'] == JOB)
assert job['name'] == 'library-tests (ios-iphone, ios, macos-26, arm64, python3, iphone, calf-ui)'
assert job['run_attempt'] == 1 and job['status'] == 'completed' and job['conclusion'] == 'success'
tooling = next(j for j in jobs if j['name'] == 'tooling')
assert tooling['conclusion'] == 'success' and instant(run['created_at']) <= instant(tooling['started_at']) <= instant(tooling['completed_at']) <= instant(job['started_at'])
assert next(j for j in jobs if j['name'] == 'consumer-core-io')['conclusion'] == 'skipped'
assert collection['run_id'] == RUN and collection['source_revision'] == REV and collection['profile'] == 'ios-ui'
assert collection['selected_job_count'] == 1 and len(collection['logs']) == 1
assert collection['logs'][0]['job_id'] == JOB and collection['logs'][0]['job_conclusion'] == 'success'
art = next(a for a in arts if a['id'] == ART)
assert art['name'] == 'library-evidence-ios-iphone' and not art['expired']
assert art['workflow_run']['id'] == RUN and art['workflow_run']['head_sha'] == REV
assert instant(job['started_at']) <= instant(art['created_at']) <= instant(art['updated_at']) <= instant(job['completed_at'])
raw = (SOURCE / f'{ART}.zip').read_bytes()
assert len(raw) == art['size_in_bytes'] < 64 * 1024**2 and 'sha256:' + sha(raw) == art['digest']
log = SOURCE / f'job-{JOB}-log.log'
assert sha(log) == collection['logs'][0]['job_log_sha256']

records = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        metadata, name = row.split(b'\t', 1)
        records[name.decode()] = metadata.decode().split()


def blob(name, revision=None):
    if revision is not None:
        return subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT)
    mode, kind, oid = records[name]
    assert kind == 'blob' and mode in {'100644', '100755'}, name
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)


with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-ea79-ui-review-', dir='/dev/shm') as directory:
    view = Path(directory)

    def materialize(name):
        path = view / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob(name))

    materialize('settings.gradle.kts')
    for name in records:
        if name.startswith('scripts/ci/') or (name.startswith(('calf-', 'sample/')) and name.endswith('/build.gradle.kts')):
            materialize(name)
    sys.path.insert(0, str(view / 'scripts/ci'))
    import library_tests as lt
    import dependency_cache_inputs as keys
    import ios_ui_application as app_source
    projects = lt.projects(view)
    prefixes = ['gradle/', 'convention-plugins/', 'scripts/ci/', 'scripts/native/', 'kotlin-js-store/']
    prefixes += [f'{module}/{folder}/' for module in projects for folder in ('src', 'native', '.cargo', 'gradle')]
    exact = set(lt.ROOT_INPUTS) | {f'{module}/{name}' for module in projects for name in ('build.gradle.kts', 'gradle.properties', 'gradle.lockfile')}
    exact |= {name for name in records if name.startswith('sample/') and name.count('/') == 2 and name.endswith('/build.gradle.kts')}
    for name in records:
        if (name in exact or any(name.startswith(p) for p in prefixes) or
                (name.startswith('sample/') and Path(name).name in keys.PROJECT_FILES)) and not set(PurePosixPath(name).parts[:-1]) & lt.IGNORED_INPUT_DIRS:
            materialize(name)
    inputs = lt.snapshot_inputs(view)
    assert len(inputs) == 725
    test_plan = lt.plan(view, 'ios', only_modules=('calf-ui',))
    with zipfile.ZipFile(SOURCE / f'{ART}.zip') as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        assert len(names) == len(set(names)) == 35 and sum(i.file_size for i in infos) < 64 * 1024**2
        for entry in infos:
            path = PurePosixPath(entry.filename)
            assert not path.is_absolute() and not {'.', '..'} & set(path.parts) and '\\' not in entry.filename
            assert not entry.is_dir() and not entry.flag_bits & 1 and entry.filename.endswith(('.json', '.xml'))
            assert entry.file_size <= lt.MAX_REPORT_BYTES and stat.S_IFMT(entry.external_attr >> 16) in {0, stat.S_IFREG}

        def get(name):
            return document(archive.read(name))

        receipt = get(BASE + 'receipt.json')
        runtime = get(BASE + 'runtime.json')
        module = receipt['modules'][0]
        assert get(BASE + 'inputs-before.json') == get(BASE + 'inputs-after.json') == inputs
        assert receipt['source_revision'] == receipt['source_revision_after'] == REV and receipt['source_tree_dirty'] is False
        assert receipt['changed_inputs'] == [] and receipt['inputs_before_sha256'] == receipt['inputs_after_sha256'] == lt.input_digest(inputs)
        assert get(BASE + 'plan.json') == get('build/ci-plan/plan.json') == test_plan
        assert len(test_plan['expected']) == len(receipt['modules']) == 1 and module['module'] == 'calf-ui'
        assert receipt['runtime_receipt_sha256'] == sha(archive.read(BASE + 'runtime.json'))
        assert runtime['source_revision'] == REV and runtime['source_tree_dirty'] is False
        assert runtime['host']['system'] == 'Darwin' and runtime['host']['architecture'] == 'arm64'
        assert runtime['java']['major'] == 17 and runtime['rust']['release'] == '1.98.0'
        assert runtime['simulator']['state'] == 'Booted' and runtime['simulator']['runtime_version'] == '26.5'
        assert receipt['command'] == lt.gradle_command('ios', test_plan, simulator=runtime['simulator']['udid'], root=view)
        assert receipt['execution']['exit_code'] == 0 and not receipt['execution'].get('stop_reason')
        assert receipt['task_execution_markers'] == {':calf-ui:iosSimulatorArm64ApplicationTest': 1}
        assert receipt['quarantined_prior_reports'] == [] and receipt['passed'] is True and receipt['errors'] == []
        xmls = [name for name in names if name.endswith('.xml')]
        assert len(xmls) == 25 and set(xmls) == {report['path'] for report in module['reports']}
        cases, timestamps = [], []
        for report in module['reports']:
            payload = archive.read(report['path'])
            assert sha(payload) == report['sha256']
            parsed = lt.junit_cases(payload)
            assert all(report[k] == v for k, v in lt.case_counts(parsed).items())
            cases += parsed
            suite = ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
            timestamp = instant(suite.attrib['timestamp'])
            assert instant(receipt['started_at_utc']) <= timestamp <= instant(receipt['finished_at_utc'])
            assert not list(suite.iter('failure')) and not list(suite.iter('error')) and not list(suite.iter('skipped'))
            timestamps.append({'path': report['path'], 'timestamp': suite.attrib['timestamp']})
        sort = lambda c: (c['classname'], c['name'])
        assert len(cases) == len({sort(c) for c in cases}) == 123
        assert sorted(cases, key=sort) == sorted(module['testcases'], key=sort)
        totals = lt.case_counts(cases)
        assert all(module[k] == v for k, v in totals.items())
        assert totals == receipt['totals'] == {'tests': 123, 'failures': 0, 'errors': 0, 'skipped': 0,
                                               'passed': 123, 'executed': 123, 'not_applicable': 0, 'unexpected_skipped': 0}
        required = {('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.' + cls,
                     name + '[iosSimulatorArm64]') for cls, name in lt.IOS_APPLICATION_CASES}
        assert len(required) == 16 and required <= {sort(c) for c in cases}
        mandatory = [c for c in cases if sort(c) in required]
        assert all(c['status'] == 'passed' for c in mandatory)
        app_paths = [name for name in names if '/native-ui-application/' in name]
        assert len(app_paths) == 1
        app_path = app_paths[0]
        app = get(app_path)
        token = PurePosixPath(app_path).parent.name
        assert re.fullmatch('[0-9a-f]{32}', token)
        assert app['bundle_id'] == f'io.github.apdelrahman1911.nativecmpkit.verification.ui.r{REV[:12]}.t{token}'
        assert app['source_revision'] == REV and app['source_tree_dirty'] is False and app['transport_passed'] is True
        assert not {'error', 'startup_failure_observation', 'application_protocol_partial', 'owned_crash_diagnostics'} & set(app)
        assert app['packages_published'] is False and app['release_readiness_certified'] is False
        for when in ('runtime_before', 'runtime_after'):
            assert app[when]['source_revision'] == REV and app[when]['source_tree_dirty'] is False
            assert all(app[when][key] == runtime[key] for key in ('host', 'java', 'rust', 'xcode', 'apple_sdks', 'simulator', 'compiler_runtime_fingerprint'))
        assert instant(receipt['started_at_utc']) <= instant(app['started_at_utc']) <= instant(app['finished_at_utc']) <= instant(receipt['finished_at_utc'])
        assert app['macho']['architecture'] == 'arm64' and app['macho']['file_type'] == 'executable' and app['macho']['platform'] == 7
        assert app['macho']['minimum_os'] == '15.0.0' and app['macho']['sdk'] == '26.4.0'
        assert app['macho'] == app['signed_macho_identity'] and re.fullmatch('[0-9a-f-]{36}', app['macho']['executable_uuid'])
        assert app['binary_sha256'] == app['binary_sha256_after']
        for key in ('binary_sha256', 'signed_application_executable_sha256', 'application_plist_sha256'):
            assert re.fullmatch('[0-9a-f]{64}', app[key])
        plist = app_source.app_information(app['bundle_id'], app['macho']['minimum_os'])
        assert type(plist['CADisableMinimumFrameDurationOnPhone']) is bool and plist['CADisableMinimumFrameDurationOnPhone'] is True
        assert sha(plistlib.dumps(plist, sort_keys=True)) == app['application_plist_sha256']
        steps, cleanup = app['steps'], app['cleanup']
        assert steps['foreign-app-preflight']['preexisting_app_absence_verified'] is True
        assert steps['adhoc-sign-local-verification-app']['exit_code'] == 0 and steps['adhoc-sign-local-verification-app']['remote_signing_or_publication'] is False
        assert steps['install-owned-app']['exit_code'] == 0 and steps['install-owned-app']['installed_owned_bytes_verified'] is True
        assert cleanup['uninstall_exit_code'] == 0 and not any('error' in key for key in cleanup)
        assert all(cleanup[key] is True for key in ('owned_app_identity_reverified', 'owned_app_stopped_verified', 'owned_app_absence_verified', 'owned_local_bundle_removed'))
        protocol = app['application_protocol']
        assert protocol['process_exit'] == 0 and protocol['activation'] == {'main_worker': 1, 'owned_worker': 2}
        assert protocol['completion'] == {'runner_exit': 0, 'worker_terminated': True}
        assert protocol['counts'] == totals and type(protocol['observed_launch_pid']) is int and protocol['observed_launch_pid'] > 0
        assert 0 < protocol['stream_bytes'] <= app_source.MAX_STREAM_BYTES and 0 < protocol['elapsed_seconds'] < app_source.APP_TIMEOUT_SECONDS
        assert protocol['image_lifetime_observation'] == {'marker_count': 63, 'last_phase': 'verified', 'last_iteration': None,
                                                        'main_thread': True, 'retained_image_bytes_verified': True}
        normal = [{'classname': c['classname'].removeprefix('iosSimulatorArm64ApplicationTest.'),
                   'name': c['name'].removesuffix('[iosSimulatorArm64]'), 'status': c['status']} for c in cases]
        assert sorted(normal, key=sort) == sorted(protocol['testcases'], key=sort)
        transport = app['application_transport']
        assert transport['console_process_exit'] == transport['console_process_exit_after_cleanup'] == 0
        assert transport['console_cleanup_requested'] is False
        assert instant(app['started_at_utc']) <= instant(transport['started_at_utc']) <= instant(transport['finished_at_utc']) <= instant(app['finished_at_utc'])
        assert len(receipt['ios_applications']) == 1
        witness = receipt['ios_applications'][0]
        assert witness['receipt_path'] == app_path and witness['receipt_sha256'] == sha(archive.read(app_path))
        assert witness['protocol_xml_agreement'] is True and witness['counts'] == totals and witness['required_native_cases_found'] == 16
        assert witness['binary_sha256'] == app['binary_sha256'] and witness['bundle_id'] == app['bundle_id']
        key = get('build/ci-runtime/library-dependencies.json')
        selected = keys.selected_inputs(view, 'libraries')
        assert key['inputs'] == selected and key['dependency_inputs_sha256'] == keys.fingerprint('libraries', selected) and key['source_revision'] == REV

with zipfile.ZipFile(OLD / 'raw/12737389835.zip') as old_archive:
    old_receipt = document(old_archive.read(BASE + 'receipt.json'))
    assert old_receipt['source_revision'] == OLD_REV and old_receipt['totals']['tests'] == 121 and old_receipt['execution']['exit_code'] == 1
    old_identities = {(c['classname'], c['name']) for c in old_receipt['modules'][0]['testcases']}
    new_identities = {(c['classname'], c['name']) for c in cases}
    assert len(old_identities) == 121 and old_identities < new_identities
    assert new_identities - old_identities == {
        ('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.navigation.NativeBarOwnershipTest', 'selectionUsesCurrentNativeMembershipInsteadOfStaleOrMutableTags[iosSimulatorArm64]'),
        ('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.dialog.RememberNativeAlertPropertiesTest', 'stableInputsRetainIdentityButTextFieldReplacementReachesTheCaller[iosSimulatorArm64]'),
    }
    old_failures = [c for c in old_receipt['modules'][0]['testcases'] if c['status'] != 'passed']
    assert len(old_failures) == 1 and old_failures[0]['name'].startswith(app_source.IMAGE_LIFETIME_CASE[1])
image_cases = [c for c in cases if c['classname'].endswith('.UIImageConversionTest')]
assert len(image_cases) == 9 and all(c['status'] == 'passed' for c in image_cases)
assert blob(BRIDGE) == blob(BRIDGE, OLD_REV) == blob(BRIDGE, CURRENT) == (ROOT / BRIDGE).read_bytes()
instrumented = blob(IMAGE_TEST).decode()
reversed_source = instrumented.replace('import platform.Foundation.NSThread\n', '')
reversed_source = re.sub(r'^        // Finite, exact-case transport diagnostics only\. Keep real conversions,\n        // all twenty synchronous main-thread collections and pixel assertions\.\n', '', reversed_source, flags=re.M)
reversed_source = re.sub(r'^\s*println\("NATIVECMPKIT_UIKIT_IMAGE_LIFETIME[^\n]*\n', '', reversed_source, flags=re.M)
reversed_source = reversed_source.replace('repeat(20) { iteration ->\n            val ordinal = iteration + 1\n', 'repeat(20) {\n')
assert reversed_source.encode() == blob(IMAGE_TEST, OLD_REV), 'Every old conversion, forced GC and pixel assertion must remain'
assert blob(IMAGE_TEST) == blob(IMAGE_TEST, CURRENT) == (ROOT / IMAGE_TEST).read_bytes()
for name in inputs:
    if name.startswith(('calf-ui/', 'convention-plugins/')) or name in lt.ROOT_INPUTS or name.startswith('gradle/'):
        assert blob(name) == blob(name, CURRENT), name
for name in inputs:
    if name.startswith(('calf-ui/', 'calf-core/', 'convention-plugins/', 'gradle/')) or name in lt.ROOT_INPUTS or name in {'scripts/ci/library_tests.py', 'scripts/ci/ios_ui_application.py', 'scripts/ci/runtime_context.py', 'scripts/ci/native_test_policy.py', 'scripts/ci/fresh-tests.init.gradle.kts'}:
        assert blob(name) == (ROOT / name).read_bytes(), name
assert len(lt.IOS_APPLICATION_SOURCES) == 6 and all(name in inputs for name in lt.IOS_APPLICATION_SOURCES)
scopes = dict(Counter(c['classname'].removeprefix('iosSimulatorArm64ApplicationTest.') for c in cases))
review = {
    'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'source_revision': REV, 'run_id': RUN, 'run_attempt': 1,
    'url': run['html_url'], 'run_conclusion': 'success', 'job_id': JOB, 'job_url': job['html_url'],
    'evidence_integrity_passed': True, 'artifact_id': ART, 'artifact_bytes': len(raw), 'artifact_digest': art['digest'],
    'fresh_artifact_created_within_selected_attempt_job': True, 'prior_attempt_artifacts_present': False,
    'tooling_reexecuted_successfully_not_counted_as_library_methods': True, 'artifact_members': names,
    'source_input_count': len(inputs), 'source_inputs_sha256': lt.input_digest(inputs),
    'all_selected_inputs_reconstructed_from_exact_Git_and_before_after_match': True,
    'command': receipt['command'], 'execution': receipt['execution'], 'runtime': runtime,
    'actual_xml_reports': len(xmls), 'totals': totals, 'testcases': cases, 'testcase_class_counts': scopes,
    'all_121_previous_testcase_identities_retained': True, 'mandatory_application_methods_passed': 16,
    'mandatory_testcases': mandatory, 'image_conversion_methods_passed': 9, 'image_testcases': image_cases,
    'exact_reverse_diagnostics_reproduces_previous_failed_test': True,
    'all_20_original_synchronous_main_thread_GC_calls_and_pixel_assertions_preserved': True,
    'image_lifetime_observation': protocol['image_lifetime_observation'],
    'production_bridge_sha256': sha(blob(BRIDGE)), 'production_bridge_unchanged_since_failed_run_and_at_current_HEAD': True,
    'UIKit_sources_and_common_build_inputs_identical_at_current_HEAD': CURRENT,
    'unrelated_current_worktree_is_dirty': current_worktree_dirty,
    'all_current_owning_UI_build_and_platform_source_bytes_match_tested_Git': True,
    'application_receipt_path': app_path, 'application_macho': app['macho'], 'application_transport_passed': True,
    'application_protocol_XML_agreement_independently_recomputed': True,
    'application_activation': protocol['activation'], 'application_completion': protocol['completion'],
    'application_transport': transport, 'application_cleanup': cleanup,
    'app_started_utc': app['started_at_utc'], 'app_finished_utc': app['finished_at_utc'],
    'literal_XML_timestamps': timestamps, 'independently_recomputed_dependency_fingerprint': key['dependency_inputs_sha256'],
    'bounded_job_log_identity': {'bytes': log.stat().st_size, 'sha256': sha(log), 'raw_log_archived': False},
    'confirmed_result': 'All123 actual iPhone26.5 simulator cases pass in25 fresh XML, zero skips. All16 mandatory genuine application methods pass, including the current tab-selection and remember-property regressions. The preserved retained-UIImage lifetime case completes all63 finite phase markers, including all20 main-thread GC collections and final byte equality. Native runner/Worker/console exit and owned cleanup complete.',
    'earlier_interruption_root_cause': 'Still unverified. Both prior diagnostic-only retry and this current run pass with unchanged production bridge and identical original image assertions. This establishes the current exercised behavior, not the cause or repair of the prior Unknown process interruption.',
    'limits': [
        'No raw application protocol is exported. Marker ordering/exact-case/main-thread checks are source-bound transport observations; the independently archived JUnit testcase elements and protocol summaries agree, but raw frames cannot be replayed from this evidence.',
        'Native executable bytes are intentionally not archived. Mach-O and signed/installed/before-after hashes are held-source controller witnesses, not an independent redistributable binary/ABI attestation.',
        'This is iPhone26.5 simulator with Xcode26.6, not iPad, physical-device, minimum-iOS, old/current adaptive-branch equivalence, accessibility or native touch coverage for direct manager entrypoints.',
        'Release-call counters and twenty forced collections are not ASan, Instruments leak/allocation profiling, general memory-pressure, security or measured-performance clearance.',
        'One focused success after setup/runtime failures does not establish sustained CI stability, a full current-commit matrix, package consumers or a release gate.',
    ],
    'issues_closed': 0, 'packages_published': False, 'release_created': False, 'release_readiness_certified': False,
    'review_script_sha256': sha(Path(__file__)),
}
(OUT / 'raw').mkdir(parents=True)
for name in ('run-final.json', 'jobs-final.json', 'artifacts-final.json', 'collection.json'):
    shutil.copyfile(SOURCE / name, OUT / name)
(OUT / 'raw' / f'{ART}.zip').write_bytes(raw)
shutil.copyfile(Path(__file__), OUT / 'lead-review.py')
with (OUT / 'lead-independent-review.json').open('x') as handle:
    json.dump(review, handle, indent=2, sort_keys=True)
    handle.write('\n')
(OUT / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n'
                                     for p in sorted(OUT.rglob('*')) if p.is_file()))
print(json.dumps({key: review[key] for key in ('evidence_integrity_passed', 'source_input_count', 'actual_xml_reports',
                 'totals', 'mandatory_application_methods_passed', 'image_conversion_methods_passed', 'application_transport_passed')}, indent=2))
