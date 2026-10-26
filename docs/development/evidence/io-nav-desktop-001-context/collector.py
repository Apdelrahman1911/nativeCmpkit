"""Archive fixed host-launch context without inferring full-suite or native coverage."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import sys

ROOT = Path('/root/projects/nativeCmpKit')
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests

name = sys.argv[1]
assert name in {'io-nav-desktop-001', 'io-android-host-001'}
raw = ROOT / 'build/ci-verification' / name
archive = ROOT / 'docs/development/evidence' / name
launch = ROOT / ('build/host-launch-context-' + name)
dest = ROOT / ('docs/development/evidence/' + name + '-context')
assert not dest.exists()

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

r = json.loads((raw / 'receipt.json').read_text())
c = json.loads((launch / 'launcher.json').read_text())
x = json.loads((launch / 'result.json').read_text())
before = json.loads((raw / 'inputs-before.json').read_text())
after = json.loads((raw / 'inputs-after.json').read_text())
assert before == after == library_tests.snapshot_inputs(ROOT)
assert library_tests.input_digest(before) == c['selected_input_digest'] == x['selected_input_digest_after']
assert sha(raw / 'receipt.json') == x['helper_receipt_sha256'] == sha(archive / 'receipt.json')
assert x['source_revision_after'] == r['source_revision_after'] == r['source_revision'] == c['source_revision']
assert c['suite'] == r['suite'] and c['module_subset'] == r['explicit_module_subset']
assert not r['complete_suite_requested'] and not x['selected_changes'] and not x['extra_input_changes']
assert all(sha(Path(path)) == value for path, value in x['extra_inputs_after'].items())
dest.mkdir(parents=True)
for filename in ('launcher.json', 'result.json', 'launcher-script.py'):
    with (dest / filename).open('xb') as handle:
        handle.write((launch / filename).read_bytes())
review = {
    'schema_version': 1, 'collected_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'scope': 'Additive fixed module-subset launch and executable-hash readback; no new tests or release/candidate certification.',
    'archive': str((archive / 'archive.json').relative_to(ROOT)),
    'archive_sha256': sha(archive / 'archive.json'),
    'suite': r['suite'], 'execution': r['execution'], 'library_gate_passed': r['passed'],
    'module_subset': r['explicit_module_subset'], 'complete_suite_requested': False,
    'selected_input_count': len(after), 'selected_inputs_unchanged': True,
    'selected_executable_or_driver_hashes_unchanged': True,
    'launch_command': c['command'],
    'limitations': [
        'Dirty held source at the base commit, not an immutable release candidate or process/dependency-tree attestation.',
        'Fresh tests may reuse compiled outputs according to Gradle fingerprints; inspect task outcomes rather than claiming forced recompilation.',
        'Desktop uses a task-owned Xvfb invocation. Android-host means Robolectric/JVM, not Android device or emulator execution.',
        'No full-library/native-dialog/Apple/Windows/ABI/Maven-consumer/legal/dependency gate is promoted.',
        'No remote CI, issue mutation, commit, staging, package, release or Pages operation.',
    ],
}
with (dest / 'context-review.json').open('x') as handle:
    json.dump(review, handle, indent=2, sort_keys=True)
    handle.write('\n')
with (dest / 'collector.py').open('xb') as handle:
    handle.write(Path(__file__).read_bytes())
paths = sorted(path for path in dest.rglob('*') if path.is_file())
with (dest / 'SHA256SUMS').open('x') as handle:
    handle.write(''.join(f'{sha(path)}  {path.relative_to(dest).as_posix()}\n' for path in paths))
print(json.dumps({'archive': str(dest.relative_to(ROOT)), 'sha256': sha(dest / 'context-review.json'), 'bound_files': len(paths)}, indent=2))
