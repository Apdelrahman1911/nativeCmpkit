"""Read-only review of attempt 2; never overwrites attempt 1 or executes ZIP data.

Integrity is separate from the failed real UIKit application/test result.
"""
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt

RUN = 40453956549
REV = 'be32a7d61bdf025cf1a115aea9ac07c8062f3623'
ARTIFACT = 12712588575
JOB = 122027136255
run = json.loads((OUT / 'run-final.json').read_bytes())
jobs = json.loads((OUT / 'jobs-final.json').read_bytes())['jobs']
arts = json.loads((OUT / 'artifacts-final.json').read_bytes())
assert run['id'] == RUN and run['run_attempt'] == 2 and run['head_sha'] == REV
assert run['status'] == 'completed' and run['conclusion'] == 'failure'
assert run['repository']['full_name'] == 'Apdelrahman1911/nativeCmpkit'
assert run['event'] == 'workflow_dispatch' and run['head_branch'] == 'development/preview-hardening'
assert len(arts['artifacts']) == arts['total_count'] == 1
art = arts['artifacts'][0]
assert art['id'] == ARTIFACT and art['name'] == 'library-evidence-ios-iphone' and not art['expired']
payload = (OUT / 'raw' / f'{ARTIFACT}.zip').read_bytes()
digest = 'sha256:' + hashlib.sha256(payload).hexdigest()
assert len(payload) == art['size_in_bytes'] <= 64 * 1024**2
assert digest == art['digest'] == 'sha256:162126521ab01ccecb78520b8cf834fabd107647e97e92a9807564bcc5cdf239'
rerun = json.loads((OUT / 'rerun-receipt.json').read_bytes())
assert rerun['expected_source_sha'] == REV and rerun['run_id'] == RUN and rerun['expected_attempt'] == 2
assert rerun['exit_code'] == 0 and rerun['operation'] == 'rerun-failed-jobs'
assert not rerun['request_retried'] and not rerun['packages_releases_or_deployments_requested']
assert rerun['failed_job_ids'] == [122022996018] and rerun['existing_active_run_ids'] == []
assert json.loads((OUT / 'main-after.json').read_bytes())['object']['sha'] == '94d2492e99d5cbc060409d94d9f88febd06222d5'
assert json.loads((OUT / 'branch-before.json').read_bytes())['object']['sha'] == REV
assert json.loads((OUT / 'actions-permissions.json').read_bytes()) == {
    'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}
assert json.loads((OUT / 'workflow-permissions.json').read_bytes()) == {
    'default_workflow_permissions': 'read', 'can_approve_pull_request_reviews': False}
pages = json.loads((OUT / 'pages.json').read_bytes())
assert pages['status'] is None and pages['build_type'] == 'workflow'

records = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        metadata, name = row.split(b'\t', 1)
        records[name.decode()] = metadata.decode().split()

def blob(name):
    mode, kind, oid = records[name]
    assert kind == 'blob' and mode in ('100644', '100755')
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)

with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-attempt2-review-', dir='/dev/shm') as directory:
    view = Path(directory)
    def materialize(name):
        target = view / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob(name))
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
    assert len(inputs) == 710 and lt.input_digest(inputs) == '7ff8c9aa277fd71079844f01708a6db9e4b5867fc96472859647247c0c9f3cc8'
    plan = lt.plan(view, 'ios', only_modules=('calf-ui',))
    with zipfile.ZipFile(OUT / 'raw' / f'{ARTIFACT}.zip') as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        assert len(names) == len(set(names)) <= 2000 and sum(i.file_size for i in infos) <= 64 * 1024**2
        for info in infos:
            path = PurePosixPath(info.filename)
            assert not path.is_absolute() and not set(path.parts) & {'.', '..'} and '\\' not in info.filename
            assert not info.is_dir() and info.file_size <= lt.MAX_REPORT_BYTES
            assert ((info.external_attr >> 16) & 0o170000) != 0o120000 and info.filename.endswith(('.json', '.xml'))
        def doc(name):
            return json.loads(archive.read(name))
        base = 'build/ci-verification/ios-iphone/'
        receipt = doc(base + 'receipt.json')
        runtime = doc(base + 'runtime.json')
        assert doc(base + 'inputs-before.json') == doc(base + 'inputs-after.json') == inputs
        assert doc(base + 'plan.json') == doc('build/ci-plan/plan.json') == plan
        assert receipt['source_revision'] == receipt['source_revision_after'] == REV
        assert not receipt['source_tree_dirty'] and not receipt['changed_inputs'] and not receipt['passed']
        assert receipt['inputs_before_sha256'] == receipt['inputs_after_sha256'] == lt.input_digest(inputs)
        assert receipt['runtime_receipt_sha256'] == hashlib.sha256(archive.read(base + 'runtime.json')).hexdigest()
        assert runtime['source_revision'] == REV and not runtime['source_tree_dirty']
        assert runtime['host'] == {'architecture': 'arm64', 'python': '3.15.0', 'system': 'Darwin'}
        assert runtime['java']['major'] == 17 and runtime['rust']['release'] == '1.98.0'
        assert receipt['command'] == lt.gradle_command('ios', plan, simulator=runtime['simulator']['udid'], root=view)
        assert receipt['execution']['exit_code'] == 1 and not receipt['execution'].get('stop_reason')
        assert receipt['quarantined_prior_reports'] == []
        assert receipt['task_execution_markers'] == {':calf-ui:iosSimulatorArm64ApplicationTest': 1}
        assert len(receipt['modules']) == 1 and receipt['modules'][0]['reports'] == receipt['modules'][0]['testcases'] == []
        assert all(value == 0 for value in receipt['totals'].values()) and not any(n.endswith('.xml') for n in names)
        nested = [n for n in names if '/native-ui-application/' in n]
        assert len(nested) == 1
        app_path = nested[0]
        app = doc(app_path)
        assert app['source_revision'] == REV and not app['source_tree_dirty']
        assert not app['transport_passed'] and app['application_protocol'] is None
        assert app['error'] == {'phase': 'launch-and-real-test-transport', 'type': 'ValueError'}
        assert app['macho'] == {'architecture': 'arm64', 'file_type': 'executable', 'minimum_os': '15.0.0', 'platform': 7, 'sdk': '26.4.0'}
        assert app['runtime_before']['simulator'] == runtime['simulator']
        assert app['steps']['foreign-app-preflight']['preexisting_app_absence_verified']
        assert app['steps']['adhoc-sign-local-verification-app']['exit_code'] == 0
        assert not app['steps']['adhoc-sign-local-verification-app']['remote_signing_or_publication']
        assert app['steps']['install-owned-app']['exit_code'] == 0 and app['steps']['install-owned-app']['installed_owned_bytes_verified']
        assert all(app['cleanup'][key] for key in ['owned_app_identity_reverified', 'owned_app_stopped_verified', 'owned_app_absence_verified', 'owned_local_bundle_removed'])
        assert app['cleanup']['terminate_exit_code'] == 3 and app['cleanup']['uninstall_exit_code'] == 0
        assert app['cleanup']['absence_status']['exit_code'] == 2
        assert not app['packages_published'] and not app['release_readiness_certified']

download = json.loads((OUT / 'download-receipt.json').read_bytes())
log = Path(download['temporary_log']).read_bytes()
assert len(log) == download['actual_log_bytes'] < 8 * 1024**2
assert hashlib.sha256(log).hexdigest() == download['actual_log_sha256']
lines = log.decode('utf-8-sig', errors='strict').splitlines()
clean = [re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ', '', line) for line in lines]
exact = 'Uncaught Kotlin exception: kotlin.IllegalStateException: The root must be attached to the owned UIWindow'
observed = [{'line': i + 1, 'text': line} for i, line in enumerate(clean) if line == exact]
assert len(observed) == 1
assert any('kfun:com.mohamedrejeb.calf.ui.internal#requireOwnedApplicationWindow()' in line for line in clean)
assert any('NativeUiApplicationDelegate#objc:applicationDidBecomeActive:' in line for line in clean)
assert not any(line.startswith(('NATIVECMPKIT_UIKIT_ACTIVE ', '##teamcity[')) for line in clean)
assert '> Task :calf-ui:linkApplicationDebugTestIosSimulatorArm64' in clean
assert 'NATIVECMPKIT_UIKIT_TRANSPORT passed=false' in clean
host_path = 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt'
host = blob(host_path).decode()
assert '@OverrideInit\n    constructor() : super()' in host
activation = host.split('override fun applicationDidBecomeActive', 1)[1].split('private fun releaseMainLeases', 1)[0]
assert activation.index('requireOwnedApplicationWindow()') < activation.index('Worker.start(') < activation.index('NSTimer.scheduledTimer')
job = next(j for j in jobs if j['id'] == JOB)
assert job['status'] == 'completed' and job['conclusion'] == 'failure'
tooling = next(j for j in jobs if j['name'] == 'tooling')
assert tooling['conclusion'] == 'success' and tooling['completed_at'] < job['started_at']
review = {
    'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'run_id': RUN, 'run_attempt': 2,
    'source_revision': REV, 'url': run['html_url'] + '/attempts/2', 'run_conclusion': 'failure',
    'job_id': JOB, 'job_url': job['html_url'], 'artifact_id': ARTIFACT, 'artifact_digest': digest,
    'artifact_members': names, 'evidence_integrity_passed': True, 'source_input_count': len(inputs),
    'source_inputs_sha256': lt.input_digest(inputs), 'uploaded_xml_reports': 0, 'totals': receipt['totals'],
    'execution': receipt['execution'], 'command': receipt['command'], 'runtime': runtime,
    'application_receipt_path': app_path, 'application_link_sign_install_completed': True,
    'application_transport_passed': False, 'application_cleanup': app['cleanup'],
    'successful_tooling_reused_not_reexecuted': {'job_id': tooling['id'], 'completed_at': tooling['completed_at']},
    'bounded_actual_job_diagnostics': {'log_bytes': len(log), 'log_sha256': hashlib.sha256(log).hexdigest(),
        'full_log_archived': False, 'exact_attachment_diagnostics': observed, 'activation_or_teamcity_frame_observed': False},
    'source_location': {'path': host_path, 'lines': [54, 61, 210, 214], 'symbol': 'NativeUiApplicationDelegate.applicationDidBecomeActive / requireOwnedApplicationWindow'},
    'confirmed_failure': 'The repaired exported Objective-C initializer reaches applicationDidBecomeActive; its synchronous root.view.window === window readiness check throws before worker/timer startup. No test, activation marker or XML runs.',
    'root_cause_boundary': 'Activation is incorrectly assumed sufficient for immediate attachment readiness. The exact false-predicate cause (first-run-loop attachment timing versus Objective-C wrapper identity) is not yet distinguished. Do not claim a production presenter defect or silently weaken identity checks.',
    'recommended_next_step': 'Add main-loop bounded startup readiness before exactly-once worker admission, retain strict active/key/visible/root attachment checks, and emit bounded predicate observations on startup timeout. Execute a new immutable ios-ui run; do not retry the same failed application blindly.',
    'scope': 'Real linked/signed/installed UIKit application startup fails, with successful owned stop/uninstall/absence/local cleanup. Zero library/host/presenter/Worker/KGP XML methods verified. Initial Rust-DNS attempt and earlier initializer crash remain immutable. Integrity success is not runtime success.',
    'issues_closed': 0, 'packages_published': False, 'release_created': False, 'release_readiness_certified': False,
    'review_script_sha256': lt.sha256(Path(__file__)),
}
(OUT / 'lead-independent-review.json').open('x').write(json.dumps(review, indent=2, sort_keys=True) + '\n')
print(json.dumps({key: review[key] for key in ['run_id', 'run_attempt', 'evidence_integrity_passed', 'uploaded_xml_reports', 'totals', 'application_transport_passed']}, indent=2))
