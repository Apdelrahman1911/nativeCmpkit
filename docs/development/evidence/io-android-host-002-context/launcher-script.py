"""Fixed, contained host regressions after the IO resource-only plugin repair."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path('/root/projects/nativeCmpKit')
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests

CONFIG = {
    'io-android-host-002': ('android-host', ('calf-io',)),
}

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def put(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')

name = sys.argv[1]
assert name in CONFIG
suite, modules = CONFIG[name]
context = ROOT / ('build/host-launch-context-' + name)
output = ROOT / 'build/ci-verification' / name
assert not context.exists() and not output.exists()
assert not (ROOT / 'build/ci-verification/.library-tests.lock').exists()
assert library_tests.git_revision(ROOT) == '94d2492e99d5cbc060409d94d9f88febd06222d5'
assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'development/preview-hardening'
assert sha(ROOT / 'scripts/ci/library_tests.py') == '8098c11ba7c5e0d43c0b320227e1695798726c06758d2c699adcf316112817a6'
before = library_tests.snapshot_inputs(ROOT)
browser_inputs = json.loads((ROOT / 'docs/development/evidence/js-full-004/inputs-after.json').read_text())
changes = sorted(path for path in browser_inputs.keys() | before.keys() if browser_inputs.get(path) != before.get(path))
assert changes == ['scripts/ci/runtime_context.py', 'scripts/ci/test_runtime_context.py']
assert before['scripts/ci/runtime_context.py'] == '3d6bfdb47a4713afb53c43a62c2a552c076e3dd323cd4777364b79657340788a'
assert before['scripts/ci/test_runtime_context.py'] == '6fe2fccaee0680edacbf0ecd69aef29d4cfe1a1253fcae32d0389ff0e7cdd866'
environment = os.environ.copy()
environment['JAVA_HOME'] = '/usr/lib/jvm/java-17-openjdk-amd64'
environment['PATH'] = environment['JAVA_HOME'] + '/bin:/root/.cargo/bin:' + environment.get('PATH', '')
environment.pop('ORG_GRADLE_PROJECT_kotlin.user.home', None)
command = [sys.executable, 'scripts/ci/library_tests.py', 'run', '--suite', suite]
for module in modules:
    command += ['--module', module]
command += ['--output', str(output.relative_to(ROOT)), '--timeout', '600', '--reserve-mib', '8192']
extra_paths = [Path(__file__), Path(environment['JAVA_HOME']) / 'bin/java']
if suite == 'desktop':
    xvfb = shutil.which('xvfb-run', path=environment['PATH'])
    assert xvfb
    command = [xvfb, '-a', *command]
    for executable in ('xvfb-run', 'Xvfb', 'xauth'):
        path = shutil.which(executable, path=environment['PATH'])
        assert path
        extra_paths.append(Path(path))
extras = {str(path): sha(path) for path in extra_paths}
context.mkdir(parents=True)
put(context / 'launcher.json', {
    'schema_version': 1, 'created_utc': utc(), 'suite': suite,
    'command': command, 'module_subset': list(modules), 'dirty_source': True,
    'source_revision': library_tests.git_revision(ROOT),
    'selected_input_count': len(before), 'selected_input_digest': library_tests.input_digest(before),
    'extra_inputs_before': extras,
    'explicit_nonsecret_context': {'JAVA_HOME': environment['JAVA_HOME'], 'cargo_directory_prepended_to_PATH': True},
    'scope': 'Fixed local module-subset regressions only, using fresh mandatory testcase/marker checks. No emulator, device, native dialogs, metadata staging, publication or full-suite claim. Desktop uses task-owned Xvfb; executable hashes are not process/tree provenance attestation.',
})
started = utc()
clock = time.monotonic()
run = subprocess.run(command, cwd=ROOT, env=environment)
after = library_tests.snapshot_inputs(ROOT)
extra_after = {path: sha(Path(path)) if Path(path).is_file() else None for path in extras}
result = {
    'schema_version': 1, 'started_utc': started, 'finished_utc': utc(),
    'exit_code': run.returncode, 'elapsed_seconds': round(time.monotonic() - clock, 3),
    'source_revision_after': library_tests.git_revision(ROOT),
    'selected_input_count_after': len(after), 'selected_input_digest_after': library_tests.input_digest(after),
    'selected_changes': sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path)),
    'extra_inputs_after': extra_after,
    'extra_input_changes': sorted(path for path in extras if extras[path] != extra_after[path]),
    'helper_receipt': str((output / 'receipt.json').relative_to(ROOT)) if (output / 'receipt.json').is_file() else None,
    'helper_receipt_sha256': sha(output / 'receipt.json') if (output / 'receipt.json').is_file() else None,
}
put(context / 'result.json', result)
with (context / 'launcher-script.py').open('xb') as handle:
    handle.write(Path(__file__).read_bytes())
print(json.dumps({'launcher_context': str(context.relative_to(ROOT)), 'exit_code': run.returncode,
                  'selected_changes': result['selected_changes'], 'extra_input_changes': result['extra_input_changes']}, indent=2), flush=True)
sys.exit(run.returncode or (1 if result['selected_changes'] or result['extra_input_changes'] else 0))
