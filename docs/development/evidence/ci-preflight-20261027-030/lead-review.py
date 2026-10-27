"""Fresh read-only recount of the held five-check navigation acceptance preflight."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt
import gzip
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path(__file__).parent
CHECKS = BASE / 'checks'
DEST = ROOT / 'docs/development/evidence/ci-preflight-20261027-030'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def held(inputs):
    for name, row in inputs.items():
        path = ROOT / name
        if row['kind'] == 'regular':
            assert path.is_file() and not path.is_symlink(), name
            assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], name
        elif row['kind'] == 'deleted':
            assert not path.exists(), name
        elif row['kind'] == 'symlink':
            assert path.is_symlink(), name
            assert hashlib.sha256(os.readlink(path).encode()).hexdigest() == row['target_sha256'], name
        else:
            raise AssertionError('Unknown input kind')

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.h1s = []

    def handle_starttag(self, tag, attrs):
        anchor = dict(attrs).get('id')
        if anchor is not None:
            self.ids.add(anchor)
        if tag == 'h1':
            self.h1s.append(anchor)

r = json.loads((CHECKS / 'checks.json').read_bytes())
before = json.loads((CHECKS / 'inputs-before.json').read_bytes())
after = json.loads((CHECKS / 'inputs-after.json').read_bytes())
assert r['passed'] and r['commands_requested'] == r['commands_completed'] == len(r['results']) == 5
assert before == after and not r['changed_inputs'] and len(before) == r['source_input_count'] == 18407
assert r['source_revision'] == r['source_revision_after'] == subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert r['driver_sha256'] == sha(BASE / 'driver.py')
assert r['staged_index_sha256_before'] == r['staged_index_sha256_after'] == hashlib.sha256(
    subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT)).hexdigest()
held(before)
assert [row['name'] for row in r['results']] == [
    'audit-structure', 'resolution-index', 'mkdocs-strict', 'cached-diff-whitespace', 'diff-whitespace']
for row in r['results']:
    assert row['execution']['exit_code'] == 0 and not row['execution'].get('stop_reason'), row['name']
    assert sha(CHECKS / row['log']) == row['log_sha256']
    assert row['unittest_count'] is None and row['unittest_summary_ok'] is None
assert r['python_unittest_executions'] == r['library_or_native_or_packaged_consumer_methods_executed'] == 0
assert r['hosted_ci_or_publication_performed'] is False
policy = r['lightweight_resource_policy']
assert policy['heavy_build8GiB_guard_lowered'] is False
assert policy['maximum_root_decrease_bytes'] == 128 * 1024 ** 2
assert policy['root_free_after'] >= policy['root_free_before'] - policy['maximum_root_decrease_bytes']
assert policy['owned_tmpfs_minimum_free_bytes'] == 2 * 1024 ** 3
assert policy['tmpfs_free_after'] >= policy['owned_tmpfs_minimum_free_bytes']

# Reuse only the target list; inspect this run's new output bytes and anchors.
previous = json.loads((ROOT / 'docs/development/evidence/ci-preflight-20261027-029/lead-review.json').read_bytes())
targets = [(row['path'], row['actual_anchor_verified']) for row in previous['actual_document_output_checks']]
page = 'development/checkpoint-navhost-verified-20261027/index.html'
new_h1 = 'nativecmpkit-immutable-nav-006-acceptance-and-complete-sdk-context'
targets += [(page, anchor) for anchor in (
    new_h1, 'actual-immutable-navigation-and-sdk-verification',
    'every-original-nav-006-criterion', 'preserved-review-failures-and-next-work')]
outputs = []
for name, anchor in targets:
    path = BASE / 'site' / name
    assert path.is_file(), name
    parser = Anchors()
    parser.feed(path.read_text())
    assert anchor in parser.ids, (name, anchor)
    if name == page:
        assert parser.h1s == [new_h1]
    outputs.append({'path': name, 'sha256': sha(path), 'actual_anchor_verified': anchor})
assert len(outputs) == 58 and len({row['path'] for row in outputs}) == 23

# Prior full Python results are not rerun or added to the zero count above.
previous_inputs = json.loads(gzip.decompress((ROOT / 'docs/development/evidence/ci-preflight-20261027-029/inputs-after.json.gz').read_bytes()))
executable_inputs = [name for name in previous_inputs if name.startswith((
    'scripts/', '.github/workflows/', 'convention-plugins/', 'gradle/', 'calf-', 'sample/'))
    or name in ('build.gradle.kts', 'settings.gradle.kts', 'gradle.properties', 'gradlew', 'gradlew.bat')]
assert executable_inputs and all(previous_inputs[name] == before[name] for name in executable_inputs)

assert not DEST.exists()
DEST.mkdir()
for name in ('checks.json', *[row['log'] for row in r['results']]):
    shutil.copyfile(CHECKS / name, DEST / name)
    assert sha(CHECKS / name) == sha(DEST / name)
for name in ('driver.py', 'lead-review.py'):
    shutil.copyfile(BASE / name, DEST / name)
compressed = []
for name in ('inputs-before.json', 'inputs-after.json'):
    raw = (CHECKS / name).read_bytes()
    path = DEST / (name + '.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    assert gzip.decompress(path.read_bytes()) == raw
    compressed.append({'path': path.name, 'gzip_sha256': sha(path),
                       'uncompressed_sha256': hashlib.sha256(raw).hexdigest()})
held(before)
review = {
    'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'passed': True,
    'source_revision': r['source_revision'], 'source_input_count': len(before),
    'source_and_staged_index_held': True, 'commands': 5, 'python_tooling_methods': 0,
    'library_native_device_or_packaged_consumer_methods_executed': 0,
    'actual_document_output_checks': outputs, 'output_anchor_count': 58, 'unique_output_files': 23,
    'executable_inputs_unchanged_since_full_preflight029': len(executable_inputs),
    'full_preflight029_methods_not_rerun': 1286,
    'compressed_input_maps': compressed, 'lightweight_resource_policy': policy,
    'local_heavy_build_capacity_certified': False, 'publication_performed': False,
    'release_readiness_certified': False, 'archive_is_additive_after_execution_not_self_certified': True,
    'scope': 'Five held lightweight audit/index/strict-docs/whitespace commands, not another full Python suite. '
             '58 actual anchors in 23 new HTML outputs reviewed. NAV executable inputs match preflight029; '
             'immutable navigation runtime is separately reviewed at run40576835737. Additive archives/links '
             'do not certify later commits, native/device/legal/dependency/consumer/API-ABI or release gates.'
}
(DEST / 'lead-review.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
(DEST / 'SHA256SUMS').write_text(''.join(f'{sha(path)}  {path.name}\n'
    for path in sorted(DEST.iterdir()) if path.is_file()))
print(json.dumps({'passed': True, 'commands': 5, 'Python_methods': 0, 'held_inputs': len(before),
                  'anchors': 58, 'HTML_outputs': 23, 'archive': str(DEST)}, indent=2))
