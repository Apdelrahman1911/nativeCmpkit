"""Review the original UIKit alert-delegate crash against immutable Git and XML."""
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import importlib.util
import json
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
TMP = Path(__file__).resolve().parent
OUT = TMP / 'review-archive'
REV = 'c5e14c9596760fca3a2493063b295161ce5e9d36'
REPO = 'Apdelrahman1911/nativeCmpkit'
RUN, JOB, ART = 40480810709, 122110633149, 12724870552
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def document(payload):
    def unique(pairs):
        values = {}
        for key, value in pairs:
            assert key not in values
            values[key] = value
        return values
    return json.loads(payload, object_pairs_hook=unique)


assert not OUT.exists()
(OUT / 'raw').mkdir(parents=True)
run = document((TMP / 'run.json').read_bytes())
jobs = document((TMP / 'jobs.json').read_bytes())['jobs']
arts = document((TMP / 'artifacts.json').read_bytes())['artifacts']
assert run['id'] == RUN and run['head_sha'] == REV and run['run_attempt'] == 1
assert run['repository']['full_name'] == REPO and run['head_branch'] == 'development/preview-hardening'
assert run['event'] == 'workflow_dispatch' and run['status'] == 'completed' and run['conclusion'] == 'failure'
job = next(j for j in jobs if j['id'] == JOB)
assert job['status'] == 'completed' and job['conclusion'] == 'failure'
assert next(j for j in jobs if j['name'] == 'tooling')['conclusion'] == 'success'
assert next(j for j in jobs if j['name'] == 'consumer-core-io')['conclusion'] == 'skipped'
assert len(arts) == 1
art = arts[0]
raw = (TMP / f'{ART}.zip').read_bytes()
digest = 'sha256:' + sha(raw)
assert art['id'] == ART and not art['expired'] and art['workflow_run']['id'] == RUN and art['workflow_run']['head_sha'] == REV
assert len(raw) == art['size_in_bytes'] == 94381 and art['digest'] == digest
for source, destination in [('run.json', 'run-final.json'), ('jobs.json', 'jobs-final.json'), ('artifacts.json', 'artifacts-final.json')]:
    shutil.copyfile(TMP / source, OUT / destination)
(OUT / f'raw/{ART}.zip').write_bytes(raw)
records = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        meta, name = row.split(b'\t', 1)
        records[name.decode()] = meta.decode().split()


def blob(name):
    mode, kind, oid = records[name]
    assert kind == 'blob' and mode in {'100644', '100755'}
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)


with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-alert-delegate-review-', dir='/dev/shm') as directory:
    view = Path(directory)
    def materialize(name):
        path = view / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob(name))
    materialize('settings.gradle.kts')
    for name in records:
        if name.startswith(('calf-', 'sample/')) and name.endswith('/build.gradle.kts'):
            materialize(name)
    projects = lt.projects(view)
    prefixes = ['gradle/', 'convention-plugins/', 'scripts/ci/', 'scripts/native/', 'kotlin-js-store/']
    prefixes += [f'{module}/{part}/' for module in projects for part in ('src', 'native', '.cargo', 'gradle')]
    exact = set(lt.ROOT_INPUTS) | {f'{m}/{n}' for m in projects for n in ('build.gradle.kts', 'gradle.properties', 'gradle.lockfile')}
    exact |= {n for n in records if n.startswith('sample/') and n.count('/') == 2 and n.endswith('/build.gradle.kts')}
    for name in records:
        if (name in exact or any(name.startswith(p) for p in prefixes)) and not set(PurePosixPath(name).parts[:-1]) & lt.IGNORED_INPUT_DIRS:
            materialize(name)
    assert blob('scripts/ci/library_tests.py') == (ROOT / 'scripts/ci/library_tests.py').read_bytes()
    inputs = lt.snapshot_inputs(view)
    assert len(inputs) == 715
    plan = lt.plan(view, 'ios', only_modules=('calf-ui',))
    with zipfile.ZipFile(OUT / f'raw/{ART}.zip') as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        assert len(names) == len(set(names)) == 25 and sum(i.file_size for i in infos) < 64 * 1024**2
        for info in infos:
            path = PurePosixPath(info.filename)
            assert not path.is_absolute() and not set(path.parts) & {'.', '..'} and '\\' not in info.filename
            assert not info.is_dir() and not info.flag_bits & 1 and info.filename.endswith(('.json', '.xml'))
            assert info.file_size <= lt.MAX_REPORT_BYTES and stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG)
        def doc(name):
            return document(archive.read(name))
        base = 'build/ci-verification/ios-iphone/'
        receipt, runtime = doc(base + 'receipt.json'), doc(base + 'runtime.json')
        assert doc(base + 'inputs-before.json') == doc(base + 'inputs-after.json') == inputs
        assert doc(base + 'plan.json') == doc('build/ci-plan/plan.json') == plan
        assert receipt['source_revision'] == receipt['source_revision_after'] == REV
        assert receipt['source_tree_dirty'] is False and not receipt['changed_inputs'] and receipt['passed'] is False
        assert receipt['inputs_before_sha256'] == receipt['inputs_after_sha256'] == lt.input_digest(inputs)
        assert receipt['runtime_receipt_sha256'] == sha(archive.read(base + 'runtime.json'))
        assert runtime['source_revision'] == REV and runtime['source_tree_dirty'] is False
        assert runtime['host']['system'] == 'Darwin' and runtime['host']['architecture'] == 'arm64'
        assert runtime['java']['major'] == 17 and runtime['rust']['release'] == '1.98.0' and runtime['simulator']['state'] == 'Booted'
        assert receipt['command'] == lt.gradle_command('ios', plan, simulator=runtime['simulator']['udid'], root=view)
        assert receipt['execution']['exit_code'] == 1 and not receipt['execution'].get('stop_reason')
        assert receipt['quarantined_prior_reports'] == []
        assert receipt['task_execution_markers'] == {':calf-ui:iosSimulatorArm64ApplicationTest': 1}
        xmls = [n for n in names if n.endswith('.xml')]
        assert len(xmls) == 15 and len(receipt['modules']) == 1
        cases = []
        for report in receipt['modules'][0]['reports']:
            payload = archive.read(report['path'])
            assert sha(payload) == report['sha256']
            parsed = lt.junit_cases(payload)
            assert all(report[k] == v for k, v in lt.case_counts(parsed).items())
            cases.extend(parsed)
        assert set(xmls) == {r['path'] for r in receipt['modules'][0]['reports']}
        assert len({(c['classname'], c['name']) for c in cases}) == len(cases)
        assert sorted(cases, key=lambda c: (c['classname'], c['name'])) == sorted(receipt['modules'][0]['testcases'], key=lambda c: (c['classname'], c['name']))
        totals = lt.case_counts(cases)
        assert totals == receipt['totals'] == {'tests': 82, 'failures': 1, 'errors': 0, 'skipped': 0, 'passed': 81, 'executed': 82, 'not_applicable': 0, 'unexpected_skipped': 0}
        failed = [c for c in cases if c['status'] != 'passed']
        assert len(failed) == 1 and failed[0]['classname'] == 'iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.dialog.NativeAlertLifecycleTest'
        assert failed[0]['name'] == 'presentedAlertUsesLatestActionAndTextFieldCallbacks[iosSimulatorArm64]'
        required = {('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.' + cls, name + '[iosSimulatorArm64]') for cls, name in lt.IOS_APPLICATION_CASES}
        observed = {(c['classname'], c['name']) for c in cases}
        assert len(required) == 11 and required & observed == {(failed[0]['classname'], failed[0]['name'])}
        missing = [{'classname': c, 'name': n} for c, n in sorted(required - observed)]
        paths = [n for n in names if '/native-ui-application/' in n]
        assert len(paths) == 1
        app_path = paths[0]
        app = doc(app_path)
        assert app['source_revision'] == REV and app['source_tree_dirty'] is False and app['transport_passed'] is False
        assert app['application_protocol'] is None and 'startup_failure_observation' not in app
        assert app['error'] == {'phase': 'launch-and-real-test-transport', 'type': 'ValueError'}
        assert app['steps']['foreign-app-preflight']['preexisting_app_absence_verified']
        assert app['steps']['adhoc-sign-local-verification-app']['exit_code'] == 0
        assert app['steps']['adhoc-sign-local-verification-app']['remote_signing_or_publication'] is False
        assert app['steps']['install-owned-app']['installed_owned_bytes_verified'] and app['steps']['install-owned-app']['exit_code'] == 0
        assert all(app['cleanup'][k] for k in ['owned_app_identity_reverified', 'owned_app_stopped_verified', 'owned_app_absence_verified', 'owned_local_bundle_removed'])
        assert app['packages_published'] is False and app['release_readiness_certified'] is False
        spec = importlib.util.spec_from_file_location('reviewed_original_app', view / 'scripts/ci/ios_ui_application.py')
        original_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original_app)
        plist = original_app.app_information(app['bundle_id'], app['macho']['minimum_os'])
        assert plist['CADisableMinimumFrameDurationOnPhone'] is True and type(plist['CADisableMinimumFrameDurationOnPhone']) is bool
        assert sha(plistlib.dumps(plist, sort_keys=True)) == app['application_plist_sha256']
log = (TMP / 'job-log.log').read_bytes()
assert len(log) == 115516
lines = [re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ', '', line) for line in log.decode('utf-8-sig').splitlines()]
assert 'NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2' in lines
crash = 'The presentation controller of an alert controller presenting as an alert must not have its delegate modified'
assert any(crash in line for line in lines) and any('AlertDialogManager.createController' in line for line in lines)
assert not any(line.startswith('NATIVECMPKIT_UIKIT_COMPLETED ') for line in lines)
assert not any('`Info.plist`' in line and '`CADisableMinimumFrameDurationOnPhone`' in line for line in lines)
manager = blob('calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt').decode()
assert 'presentationController?.delegate = presentationDelegate' in manager and 'controller?.presentationController?.delegate = null' in manager
locations = [{'path': 'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt', 'lines': str(i + 1), 'code': line.strip()} for i, line in enumerate(manager.splitlines()) if 'presentationController?.delegate' in line]
review = {
    'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'run_id': RUN, 'run_attempt': 1,
    'source_revision': REV, 'url': run['html_url'], 'job_id': JOB, 'job_url': job['html_url'], 'run_conclusion': 'failure',
    'evidence_integrity_passed': True, 'artifact_id': ART, 'artifact_digest': digest, 'artifact_bytes': len(raw), 'artifact_members': names,
    'source_input_count': len(inputs), 'source_inputs_sha256': lt.input_digest(inputs), 'all_inputs_reconstructed_from_Git_and_before_after_match': True,
    'actual_xml_reports': len(xmls), 'totals': totals, 'failed_testcases': failed,
    'mandatory_application_methods': 11, 'mandatory_methods_observed': 1, 'mandatory_methods_passed': 0, 'mandatory_methods_missing': missing,
    'execution': receipt['execution'], 'command': receipt['command'], 'runtime': runtime,
    'application_receipt_path': app_path, 'application_macho': app['macho'],
    'reconstructed_original_plist_Boolean_and_hash_match': True, 'previous_plist_crash_not_observed': True,
    'actual_activation_observed': {'main_worker': 1, 'owned_worker': 2}, 'application_transport_passed': False, 'application_cleanup': app['cleanup'],
    'confirmed_failure': "Real UIKit raises NSInternalInconsistencyException in AlertDialogManager.createController when nativeCmpkit overwrites UIAlertController's UIKit-owned presentation delegate for Alert style. Cleanup also writes that prohibited property; it is not reached before this crash. First native alert fails, ten mandatory application methods remain absent, and the suite/transport fail despite81 prior passed methods.",
    'current_source_locations': locations, 'failure_origin': 'Production lifecycle implementation in the development branch, not the verification manifest or an upstream baseline claim.',
    'scope': 'Partial genuine iPhone26.5 simulator execution, not a successful UIKit suite, physical device, independent consumer, ABI or release gate. The81 earlier outcomes are not81 new native presentation scenarios.',
    'bounded_actual_job_diagnostics': {'log_bytes': len(log), 'log_sha256': sha(log), 'full_log_archived': False},
    'next_step': 'Preserve UIAlertController as-is: never set or clear its Alert presentation delegate or subclass/catch native exceptions. Use only supported ActionSheet popover delegation, guard callback ownership/cardinality, retain explicit Alert actions/outside-tap/disposal completion state, and execute a new immutable native suite.',
    'issues_closed': 0, 'packages_published': False, 'release_created': False, 'release_readiness_certified': False,
    'review_script_sha256': sha(Path(__file__).read_bytes())}
shutil.copyfile(Path(__file__), OUT / 'lead-review.py')
with (OUT / 'lead-independent-review.json').open('x') as stream:
    json.dump(review, stream, indent=2, sort_keys=True)
    stream.write('\n')
with (OUT / 'SHA256SUMS').open('x') as stream:
    stream.write(''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT)}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
print(json.dumps({key: review[key] for key in ['run_id', 'evidence_integrity_passed', 'source_input_count', 'actual_xml_reports', 'totals', 'mandatory_methods_passed', 'application_transport_passed']}, indent=2))
