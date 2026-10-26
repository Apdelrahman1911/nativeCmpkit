"""Final contained docs/index/whitespace check; no library build or network."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = Path('/root/projects/nativeCmpKit')
OUT = ROOT / 'build/checkpoint-final-20261026'
DEST = ROOT / 'docs/development/evidence/checkpoint-final-20261026'
PYTHON = ROOT / 'build/docs-verification/locked-002/venv/bin/python'
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def put(path, data):
    with path.open('xb') as output:
        output.write(data)

def dump(path, value):
    put(path, (json.dumps(value, sort_keys=True, indent=2) + '\n').encode())

def snapshot():
    result = {}
    raw = subprocess.check_output(['git', '--no-optional-locks', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    for name in sorted(set(raw.decode().split('\0')) - {''}):
        path = ROOT / name
        if path.is_symlink():
            result[name] = {'kind': 'symlink', 'target_sha256': hashlib.sha256(os.readlink(path).encode()).hexdigest()}
        elif path.is_file():
            result[name] = {'kind': 'regular', 'sha256': sha(path), 'bytes': path.stat().st_size}
        elif not path.exists():
            result[name] = {'kind': 'deleted'}
        else:
            raise ValueError('Nonregular input requires inspection')
    return result

class Html(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if 'id' in attributes:
            self.ids.add(attributes['id'])
        if tag == 'a' and 'href' in attributes:
            self.hrefs.append(attributes['href'])

assert not OUT.exists() and not DEST.exists()
assert (ROOT / 'docs/development/evidence/review/docs-and-build-20261026/receipt.json').is_file()
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT).strip()
assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'development/preview-hardening'
OUT.mkdir(parents=True)
before = snapshot()
dump(OUT / 'inputs-before.json', before)
selected_reference = 'docs/development/evidence/io-metadata-observation-003/run/inputs-before.json'
selected = json.loads((ROOT / selected_reference).read_bytes())
selected_before_match = library_tests.snapshot_inputs(ROOT) == selected
started = dt.datetime.now(dt.timezone.utc).isoformat()
revision = library_tests.git_revision(ROOT)
tasks = [
    ('resolution-index', [sys.executable, '-B', 'scripts/development/validate_resolutions.py', '--check'], 120),
    ('mkdocs-strict', [str(PYTHON), '-B', '-m', 'mkdocs', 'build', '--strict', '--site-dir', str(OUT / 'site')], 300),
    ('diff-whitespace', ['git', 'diff', '--check'], 60),
]
results = []
for name, command, bound in tasks:
    log = OUT / (name + '.log')
    execution = library_tests.execute(ROOT, command, log, bound, 8192)
    lines = log.read_text(errors='replace').splitlines() if log.is_file() else []
    results.append({'name': name, 'command': command, 'timeout_seconds': bound, 'disk_reserve_mib': 8192,
                    'execution': execution, 'raw_log': str(log.relative_to(ROOT)),
                    'raw_log_sha256': sha(log) if log.is_file() else None,
                    'selected_diagnostic_lines': [line for line in lines if re.match(r'^(WARNING|ERROR)\s+-|^(CURRENT:|VALID:|Aborted with )', line)
                                                  or 'does not contain an anchor' in line]})

checks = []
if next(row for row in results if row['name'] == 'mkdocs-strict')['execution']['exit_code'] == 0:
    previous = json.loads((ROOT / 'docs/development/evidence/docs-link-repair-001/docs.json').read_bytes())
    requested = [(row['page'], row['target']) for row in previous['generated_target_checks']]
    requested.append(('development/index.html', 'development/checkpoint-20261026/index.html'))
    for page_name, target_name in requested:
        page = OUT / 'site' / page_name
        split_target, _, fragment = target_name.partition('#')
        target = (OUT / 'site' / split_target).resolve()
        if not page.is_file():
            checks.append({'page': page_name, 'target': target_name, 'passed': False,
                           'error': 'Generated source page is missing'})
            continue
        parsed = Html()
        parsed.feed(page.read_text())
        found = []
        for href in parsed.hrefs:
            url = urlsplit(href)
            candidate = (page.parent / unquote(url.path)).resolve()
            if candidate.is_dir():
                candidate = candidate / 'index.html'
            if not url.scheme and not url.netloc and candidate == target and url.fragment == fragment:
                found.append(href)
        anchor_ok = not fragment
        if fragment and target.is_file():
            target_html = Html()
            target_html.feed(target.read_text())
            anchor_ok = fragment in target_html.ids
        checks.append({'page': page_name, 'target': target_name, 'matching_hrefs': found,
                       'passed': bool(found) and target.is_file() and anchor_ok,
                       'page_sha256': sha(page), 'target_sha256': sha(target) if target.is_file() else None})

after = snapshot()
dump(OUT / 'inputs-after.json', after)
changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
revision_after = library_tests.git_revision(ROOT)
selected_after_match = library_tests.snapshot_inputs(ROOT) == selected
record = {'schema_version': 1, 'started_utc': started, 'finished_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'source_revision': revision, 'source_revision_after': revision_after, 'dirty_worktree': True,
    'commands_requested': len(tasks), 'commands_completed': len(results), 'results': results,
    'input_count': len(before), 'changed_inputs': changed, 'source_input_scope': 'All nonignored Git-listed regular/symlink/deleted working-tree inputs.',
    'selected_library_build_input_reference': selected_reference, 'selected_library_build_input_count': len(selected),
    'selected_library_build_inputs_match_before_and_after': selected_before_match and selected_after_match,
    'actual_generated_target_checks': checks, 'driver_sha256': sha(Path(__file__)), 'python_executable_sha256': sha(PYTHON),
    'passed': all(row['execution']['exit_code'] == 0 for row in results) and not changed and revision == revision_after
               and len(checks) == 6 and all(row['passed'] for row in checks) and selected_before_match and selected_after_match,
    'library_native_maven_consumer_methods_executed': 0, 'python_unittest_methods_executed': 0,
    'remote_mutations_or_dependency_acquisitions': 0, 'release_readiness_certified': False,
    'scope': 'Final bounded local documentation/index/whitespace check after additive handoff documentation. Not a repeat of the737 Python suite executions; those and the later73 development executions retain their own snapshots/outcomes.',
    'limitations': ['Tracked git diff whitespace is not a check of every untracked/binary candidate file.',
        'Generated site is task-local, never deployed. Excluded evidence/archive INFO notices remain expected.',
        'Dirty source hashes establish a held observation, not an immutable release candidate or hosted CI result.',
        'This new evidence archive is created after the final source snapshot and cannot certify itself. Candidate-byte inspection is separate.',
        'No native/platform, dependency trust, legal, ABI, consumer or release gate is cleared.']}
dump(OUT / 'checks.json', record)
archive_current = snapshot()
archive_preflight_changes = sorted(name for name in after.keys() | archive_current.keys() if after.get(name) != archive_current.get(name))
if archive_preflight_changes:
    dump(OUT / 'archive-preflight-changes.json', archive_preflight_changes)
    raise SystemExit('Inputs changed after verification; preserve output for review before archiving')
DEST.mkdir(parents=True)
for filename in ['checks.json', 'inputs-before.json', 'inputs-after.json']:
    put(DEST / filename, (OUT / filename).read_bytes())
put(DEST / 'launcher.py', Path(__file__).read_bytes())
dump(DEST / 'archive.json', {'schema_version': 1, 'archived_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'source_revision': revision, 'dirty_worktree': True, 'overall_passed': record['passed'],
    'commands': len(results), 'input_count': len(before), 'generated_targets_passed': sum(row['passed'] for row in checks),
    'producer_receipt_sha256': sha(OUT / 'checks.json'), 'raw_logs_archived': False,
    'raw_log_policy': 'Task-local raw logs remain hash-bound by checks.json; only selected diagnostic lines are copied.',
    'self_excluded': True, 'release_readiness_certified': False})
files = sorted(path for path in DEST.iterdir() if path.is_file())
put(DEST / 'SHA256SUMS', ''.join(f'{sha(path)}  {path.name}\n' for path in files).encode())
print(json.dumps({'archive': str(DEST.relative_to(ROOT)), 'archive_sha256': sha(DEST / 'archive.json'),
    'passed': record['passed'], 'results': [{'name': row['name'], **row['execution']} for row in results],
    'input_count': len(before), 'changed_inputs': changed, 'generated_target_checks_passed': sum(row['passed'] for row in checks)}, indent=2))
sys.exit(0 if record['passed'] else 1)
