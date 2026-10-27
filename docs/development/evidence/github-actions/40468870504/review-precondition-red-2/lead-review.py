"""Immutable Git/input/ZIP/XML review of the genuine UIKit app's plist crash."""
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import json
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
OUT = Path(__file__).resolve().parent
TMP = Path('/dev/shm/nativecmpkit-ios-ui-result-40468870504')
OBS = Path('/dev/shm/nativecmpkit-ios-ui-observation-40468870504-20261027-002')
REPO = 'Apdelrahman1911/nativeCmpkit'
REV = 'b5a4508a8d28f9937c456db2895b4ae09c4a9343'
RUN, JOB, ART = 40468870504, 122071043258, 12719418131
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt


def put(name, raw):
    with (OUT / name).open('xb') as stream:
        stream.write(raw)


def api(endpoint, name):
    raw = subprocess.check_output(['gh', 'api', f'repos/{REPO}/' + endpoint], cwd=ROOT, timeout=60)
    put(name, raw)
    return json.loads(raw)


run = json.loads((OBS / 'run.json').read_bytes())
jobs = json.loads((OBS / 'jobs.json').read_bytes())['jobs']
arts = json.loads((TMP / 'artifacts.json').read_bytes())
for source, dest in [(OBS / 'run.json', 'run-final.json'), (OBS / 'jobs.json', 'jobs-final.json'),
                     (TMP / 'artifacts.json', 'artifacts-final.json')]:
    put(dest, source.read_bytes())
assert run['id'] == RUN and run['head_sha'] == REV and run['run_attempt'] == 1
assert run['repository']['full_name'] == REPO and run['event'] == 'workflow_dispatch'
assert run['status'] == 'completed' and run['conclusion'] == 'failure'
assert arts['total_count'] == len(arts['artifacts']) == 1
art = arts['artifacts'][0]
raw = (TMP / f'{ART}.zip').read_bytes()
digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
assert art['id'] == ART and not art['expired'] and art['workflow_run']['head_sha'] == REV
assert len(raw) == art['size_in_bytes'] == 94111 and digest == art['digest']
put(f'raw/{ART}.zip', raw)
records = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        metadata, name = row.split(b'\t', 1)
        records[name.decode()] = metadata.decode().split()


def blob(name):
    mode, kind, oid = records[name]
    assert kind == 'blob' and mode in {'100644', '100755'}
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)


with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-plist-ci-review-', dir='/dev/shm') as directory:
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
    prefixes += [f'{m}/{f}/' for m in projects for f in ('src', 'native', '.cargo', 'gradle')]
    exact = set(lt.ROOT_INPUTS) | {f'{m}/{n}' for m in projects for n in ('build.gradle.kts', 'gradle.properties', 'gradle.lockfile')}
    exact |= {n for n in records if n.startswith('sample/') and n.count('/') == 2 and n.endswith('/build.gradle.kts')}
    for name in records:
        if (name in exact or any(name.startswith(p) for p in prefixes)) and not set(PurePosixPath(name).parts[:-1]) & lt.IGNORED_INPUT_DIRS:
            materialize(name)
    inputs = lt.snapshot_inputs(view)
    assert len(inputs) == 712
    plan = lt.plan(view, 'ios', only_modules=('calf-ui',))
    with zipfile.ZipFile(OUT / f'raw/{ART}.zip') as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        assert len(names) == len(set(names)) == 25 and sum(i.file_size for i in infos) < 64 * 1024**2
        for info in infos:
            path = PurePosixPath(info.filename)
            assert not path.is_absolute() and not set(path.parts) & {'.', '..'} and '\\' not in info.filename
            assert not info.is_dir() and info.filename.endswith(('.json', '.xml'))
            assert info.file_size <= lt.MAX_REPORT_BYTES and not stat.S_ISLNK(info.external_attr >> 16)

        def doc(name):
            return json.loads(archive.read(name))

        base = 'build/ci-verification/ios-iphone/'
        receipt, runtime = doc(base + 'receipt.json'), doc(base + 'runtime.json')
        assert doc(base + 'inputs-before.json') == doc(base + 'inputs-after.json') == inputs
        assert doc(base + 'plan.json') == doc('build/ci-plan/plan.json') == plan
        assert receipt['source_revision'] == receipt['source_revision_after'] == REV
        assert not receipt['source_tree_dirty'] and not receipt['changed_inputs'] and not receipt['passed']
        assert receipt['inputs_before_sha256'] == receipt['inputs_after_sha256'] == lt.input_digest(inputs)
        assert receipt['runtime_receipt_sha256'] == hashlib.sha256(archive.read(base + 'runtime.json')).hexdigest()
        assert runtime['source_revision'] == REV and not runtime['source_tree_dirty']
        assert runtime['host']['system'] == 'Darwin' and runtime['host']['architecture'] == 'arm64'
        assert runtime['java']['major'] == 17 and runtime['rust']['release'] == '1.98.0' and runtime['simulator']['state'] == 'Booted'
        assert receipt['command'] == lt.gradle_command('ios', plan, simulator=runtime['simulator']['udid'], root=view)
        assert receipt['execution']['exit_code'] == 1 and not receipt['execution'].get('stop_reason')
        assert receipt['quarantined_prior_reports'] == []
        assert receipt['task_execution_markers'] == {':calf-ui:iosSimulatorArm64ApplicationTest': 1}
        xmls = [n for n in names if n.endswith('.xml')]
        assert len(xmls) == 15
        cases = []
        assert len(receipt['modules']) == 1
        for report in receipt['modules'][0]['reports']:
            payload = archive.read(report['path'])
            assert hashlib.sha256(payload).hexdigest() == report['sha256']
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
        assert len(required) == 11 and len(required & observed) == 1 and required & observed == {(failed[0]['classname'], failed[0]['name'])}
        missing = [{'classname': c, 'name': n} for c, n in sorted(required - observed)]
        paths = [n for n in names if '/native-ui-application/' in n]
        assert len(paths) == 1
        app_path = paths[0]
        app = doc(app_path)
        assert app['source_revision'] == REV and not app['source_tree_dirty'] and not app['transport_passed']
        assert app['application_protocol'] is None and app['startup_failure_observation'] is None
        assert app['error'] == {'phase': 'launch-and-real-test-transport', 'type': 'ValueError'}
        assert app['steps']['foreign-app-preflight']['preexisting_app_absence_verified']
        assert app['steps']['adhoc-sign-local-verification-app']['exit_code'] == 0
        assert not app['steps']['adhoc-sign-local-verification-app']['remote_signing_or_publication']
        assert app['steps']['install-owned-app']['installed_owned_bytes_verified'] and app['steps']['install-owned-app']['exit_code'] == 0
        assert all(app['cleanup'][k] for k in ['owned_app_identity_reverified', 'owned_app_stopped_verified', 'owned_app_absence_verified', 'owned_local_bundle_removed'])
        assert not app['packages_published'] and not app['release_readiness_certified']
log = (TMP / 'job-log.log').read_bytes()
assert len(log) == 109874
lines = [re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ', '', l) for l in log.decode('utf-8-sig').splitlines()]
assert 'NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2' in lines
assert any('`Info.plist`' in l and '`CADisableMinimumFrameDurationOnPhone`' in l for l in lines)
assert not any(l.startswith('NATIVECMPKIT_UIKIT_COMPLETED ') for l in lines)
original = blob('scripts/ci/ios_ui_application.py').decode()
assert '"CADisableMinimumFrameDurationOnPhone"' not in original
job = next(j for j in jobs if j['id'] == JOB)
assert job['status'] == 'completed' and job['conclusion'] == 'failure'
tooling = next(j for j in jobs if j['name'] == 'tooling')
assert tooling['conclusion'] == 'success'
main = api('git/ref/heads/main', 'main-after.json')
assert main['object']['sha'] == '94d2492e99d5cbc060409d94d9f88febd06222d5'
actions = api('actions/permissions', 'actions-permissions.json')
assert actions['enabled'] is True and actions['allowed_actions'] == 'all' and actions['sha_pinning_required'] is False
permissions = api('actions/permissions/workflow', 'workflow-permissions.json')
assert permissions['default_workflow_permissions'] == 'read' and permissions['can_approve_pull_request_reviews'] is False
pages = api('pages', 'pages.json')
assert pages['status'] is None and pages['build_type'] == 'workflow'
review = {'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'run_id': RUN, 'run_attempt': 1,
          'source_revision': REV, 'url': run['html_url'], 'job_id': JOB, 'job_url': job['html_url'],
          'run_conclusion': 'failure', 'evidence_integrity_passed': True,
          'artifact_id': ART, 'artifact_digest': digest, 'artifact_bytes': len(raw), 'artifact_members': names,
          'source_input_count': len(inputs), 'source_inputs_sha256': lt.input_digest(inputs),
          'actual_xml_reports': len(xmls), 'totals': totals, 'failed_testcases': failed,
          'mandatory_application_methods': 11, 'mandatory_methods_observed': 1,
          'mandatory_methods_passed': 0, 'mandatory_methods_missing': missing,
          'execution': receipt['execution'], 'command': receipt['command'], 'runtime': runtime,
          'application_receipt_path': app_path, 'application_macho': app['macho'],
          'actual_activation_observed': {'main_worker': 1, 'owned_worker': 2},
          'application_transport_passed': False, 'application_cleanup': app['cleanup'],
          'confirmed_failure': 'The real app activates an owned worker, then aborts asynchronously at Compose PlistSanityCheck during the first native alert method because the generated app_information omits Boolean CADisableMinimumFrameDurationOnPhone=true. KGP records 82/81 pass/1 fail before incomplete transport; all11 mandatory app methods are not verified.',
          'scope': 'Partial genuine simulator execution, not a successful UIKit suite, physical device, consumer, ABI or release gate. The81 earlier outcomes are not81 new native application scenarios.',
          'bounded_actual_job_diagnostics': {'log_bytes': len(log), 'log_sha256': hashlib.sha256(log).hexdigest(), 'full_log_archived': False},
          'next_step': 'Repair the generated manifest with a real plist Boolean; retain Compose strict sanity check, exact native ownership, all11 mandatory methods, fresh XML and cleanup. Execute a new immutable ios-ui run; do not rerun unchanged crashing fixture or promote tooling passes.',
          'issues_closed': 0, 'packages_published': False, 'release_created': False, 'release_readiness_certified': False,
          'review_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
put('lead-independent-review.json', (json.dumps(review, indent=2, sort_keys=True) + '\n').encode())
put('SHA256SUMS', ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT)}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS').encode())
print(json.dumps({k: review[k] for k in ['run_id', 'evidence_integrity_passed', 'actual_xml_reports', 'totals', 'mandatory_methods_passed', 'application_transport_passed']}, indent=2))
