"""Lead-only fixed IO metadata generation; no publishing, staging, signing or deployment."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = Path('/root/projects/nativeCmpKit')
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests
import runtime_context

PUBLICATIONS = ('Desktop', 'Android', 'Js', 'WasmJs')
TASKS = tuple(':calf-io:generate' + kind + 'For' + publication + 'Publication'
             for publication in PUBLICATIONS for kind in ('PomFile', 'MetadataFile'))
phase = sys.argv[1]
assert phase in {'dry-run', 'run'}
base = ROOT / 'build/io-metadata-observation-002'
out = base / phase
assert not out.exists()
assert not (ROOT / 'build/ci-verification/.library-tests.lock').exists()
assert library_tests.git_revision(ROOT) == '94d2492e99d5cbc060409d94d9f88febd06222d5'
assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'development/preview-hardening'

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def put(name, value):
    with (out / name).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')

before = library_tests.snapshot_inputs(ROOT)
if phase == 'run':
    prior = json.loads((base / 'dry-run/receipt.json').read_text())
    review = json.loads((base / 'lead-graph-review.json').read_text())
    assert prior['execution']['exit_code'] == 0 and not prior['changed_inputs']
    assert review['dry_run_receipt_sha256'] == sha(base / 'dry-run/receipt.json')
    assert review['requested_tasks'] == list(TASKS)
    assert review['observed_dry_run_graph'] == prior['observed_dry_run_graph']
    assert review['no_publish_stage_sign_deploy_or_install_tasks'] is True
    assert before == json.loads((base / 'dry-run/inputs-after.json').read_text())
out.mkdir(parents=True)
put('inputs-before.json', before)
os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-17-openjdk-amd64'
os.environ['PATH'] = os.environ['JAVA_HOME'] + '/bin:/root/.cargo/bin:' + os.environ.get('PATH', '')
os.environ.pop('ORG_GRADLE_PROJECT_kotlin.user.home', None)
context = runtime_context.capture(android_package='android-37.0')
put('runtime.json', context)
command = ['./gradlew']
for task in TASKS:
    command += [task, '--rerun']
command += ['--offline', '--no-daemon', '--no-parallel', '--no-configuration-cache', '--max-workers=2', '--console=plain']
if phase == 'dry-run':
    command += ['--dry-run']
started = dt.datetime.now(dt.timezone.utc).isoformat()
execution = library_tests.execute(ROOT, command, out / 'gradle.log', 180 if phase == 'dry-run' else 600, 8192)
finished = dt.datetime.now(dt.timezone.utc).isoformat()
after = library_tests.snapshot_inputs(ROOT)
put('inputs-after.json', after)
log = (out / 'gradle.log').read_text(errors='replace')
graph = re.findall(r'(?m)^(:[A-Za-z0-9:_-]+) SKIPPED\s*$', log) if phase == 'dry-run' else []
record = {
    'schema_version': 1, 'phase': phase, 'source_revision': context['source_revision'],
    'source_revision_after': library_tests.git_revision(ROOT), 'dirty_worktree': True,
    'started_utc': started, 'finished_utc': finished, 'command': command,
    'requested_tasks': list(TASKS), 'execution': execution,
    'selected_input_count': len(before),
    'changed_inputs': sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path)),
    'raw_log_sha256': sha(out / 'gradle.log'), 'driver_sha256': sha(Path(__file__)),
    'observed_dry_run_graph': graph,
    'library_or_native_or_consumer_testcases_executed': 0,
    'explicit_subset': ['Desktop', 'Android', 'Js', 'WasmJs'],
    'root_publication_not_requested': 'The first 10-task observation failed at core common-metadata resolution with 45 uncached artifacts. Its root POM alone is fresh; its root .module gate remains failed. This is a distinct four-target observation, not a successful rerun of the root gate or a task exclusion.',
    'root_failure_archive': 'docs/development/evidence/io-metadata-observation-001/archive.json',
    'root_failure_archive_sha256': sha(ROOT / 'docs/development/evidence/io-metadata-observation-001/archive.json'),
    'scope': 'Explicit Desktop/Android/JS/WasmJS-only local IO metadata task investigation, not an artifact publication, staging operation or ABI/equivalence certification. A dry-run is configuration/graph evidence only; actual output freshness and metadata/resource contents require separate readback.',
}
put('receipt.json', record)
with (out / 'launcher-script.py').open('xb') as handle:
    handle.write(Path(__file__).read_bytes())
print(json.dumps({'phase': phase, 'execution': execution, 'changed_inputs': record['changed_inputs'],
                  'dry_run_task_count': len(graph), 'receipt': str((out / 'receipt.json').relative_to(ROOT))}, indent=2), flush=True)
sys.exit(execution['exit_code'] or (1 if record['changed_inputs'] or record['source_revision_after'] != context['source_revision'] else 0))
