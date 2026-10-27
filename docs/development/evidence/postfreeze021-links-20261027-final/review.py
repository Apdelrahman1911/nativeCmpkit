"""Source/stage-held check of additive preflight links and lossless archives.

Actual file/output counts are computed, never guessed acceptance criteria.
The first reviewer hardcoded38 instead of30 files; its failed receipt is preserved.
"""
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
DEST = ROOT / 'docs/development/evidence/postfreeze021-links-20261027-final'
PREFLIGHT = ROOT / 'docs/development/evidence/ci-preflight-20261027-021'


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def snapshot():
    result = {}
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    for name in sorted(set(names.decode().split('\0')) - {''}):
        path = ROOT / name
        if path.is_symlink():
            result[name] = {'kind': 'symlink', 'target_sha256': sha(os.readlink(path).encode())}
        elif path.is_file():
            before = path.stat()
            content = path.read_bytes()
            after = path.stat()
            assert (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_ino)
            result[name] = {'kind': 'regular', 'bytes': len(content), 'sha256': sha(content)}
        elif not path.exists():
            result[name] = {'kind': 'deleted'}
        else:
            raise AssertionError('Unreviewed input kind')
    return result


assert not DEST.exists()
previous = json.loads(gzip.decompress((PREFLIGHT / 'inputs-after.json.gz').read_bytes()))
before = snapshot()
changed = sorted(name for name in previous if before.get(name) != previous[name])
assert changed == ['AGENTS.md', 'docs/development/checkpoint-gc-diagnostics-navgeo-20261027.md']
added = sorted(set(before) - set(previous))
assert added and all(name.startswith(('docs/development/evidence/ci-preflight-20261027-021/',
    'docs/development/evidence/postfreeze021-links-20261027/')) for name in added)
assert not subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT)
stage = sha(subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT))
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
started = dt.datetime.now(dt.timezone.utc).isoformat()
commands = [
    [str(ROOT / 'build/docs-verification/locked-002/venv/bin/python'), '-B', '-m', 'mkdocs', 'build', '--strict', '--site-dir', str(BASE / 'site')],
    ['python3', '-B', 'scripts/development/validate_resolutions.py', '--check'],
    ['git', 'diff', '--cached', '--check'],
    ['git', 'diff', '--check'],
]
results = []
for index, command in enumerate(commands):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=300,
        env=dict(os.environ, TMPDIR=str(BASE), PYTHONDONTWRITEBYTECODE='1'))
    path = BASE / f'{index}.log'
    path.write_bytes(result.stdout + result.stderr)
    results.append({'command': command, 'exit_code': result.returncode, 'log': path.name, 'log_sha256': sha(path.read_bytes())})
    assert result.returncode == 0, path.name


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        self.ids.update(value for key, value in attrs if key == 'id')


prior = json.loads((PREFLIGHT / 'lead-review.json').read_bytes())
outputs = []
for item in prior['actual_document_output_checks']:
    path = BASE / 'site' / item['path']
    assert path.is_file()
    parser = Anchors()
    parser.feed(path.read_text())
    assert item['actual_anchor_verified'] in parser.ids
    outputs.append({'path': item['path'], 'anchor': item['actual_anchor_verified'], 'sha256': sha(path.read_bytes())})
after = snapshot()
assert before == after and stage == sha(subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT))
assert revision == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
DEST.mkdir()
for result in results:
    shutil.copyfile(BASE / result['log'], DEST / result['log'])
shutil.copyfile(Path(__file__), DEST / 'review.py')
for name, data in [('inputs-before', before), ('inputs-after', after)]:
    content = (json.dumps(data, indent=2, sort_keys=True) + '\n').encode()
    path = DEST / (name + '.json.gz')
    path.write_bytes(gzip.compress(content, mtime=0))
    assert gzip.decompress(path.read_bytes()) == content
record = {
    'passed': True, 'started_utc': started, 'finished_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'source_revision': revision, 'source_input_count': len(before), 'previous_preflight_source_count': len(previous),
    'only_preflight_source_changes': changed, 'added_preflight_and_failed_reviewer_archive_files': added,
    'actual_added_file_count': len(added), 'all_other_executable_test_and_workflow_inputs_unchanged': True,
    'source_and_stage_held_during_this_review': True, 'staged_index_sha256': stage,
    'results': results, 'actual_output_checks': outputs, 'actual_output_anchor_count': len(outputs),
    'new_library_native_or_consumer_methods': 0, 'release_readiness_certified': False,
    'review_script_sha256': sha(Path(__file__).read_bytes()),
    'scope': 'After complete preflight021, only two additive documentation links and lossless receipt archives changed. Fresh strict MkDocs/index/both whitespace and actual anchors pass with source/stage held. All counts computed; earlier guessed38-vs-actual30 reviewer failure preserved. This archive follows execution, not circular certification of a later commit/native/runtime/dependency/release.',
}
(DEST / 'review.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
(DEST / 'SHA256SUMS').write_text(''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in sorted(DEST.iterdir()) if path.is_file()))
print(json.dumps({key: record[key] for key in ('passed', 'source_input_count', 'actual_added_file_count', 'actual_output_anchor_count', 'new_library_native_or_consumer_methods')}, indent=2))
