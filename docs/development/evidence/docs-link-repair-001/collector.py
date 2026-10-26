"""Preserve the completed documentation-link repair, including both red runs."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import ast
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = Path('/root/projects/nativeCmpKit')
BASE = ROOT / 'build/docs-link-repair-001'
DEST = ROOT / 'docs/development/evidence/docs-link-repair-001'
DRIVER = Path('/tmp/nativecmpkit-docs-link-repair-build.py')
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def snapshot():
    files = {}
    names = subprocess.check_output(
        ['git', '--no-optional-locks', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    for name in sorted(set(names.decode().split('\0')) - {''}):
        path = ROOT / name
        if path.is_symlink():
            files[name] = {'kind': 'symlink', 'target_sha256': hashlib.sha256(os.readlink(path).encode()).hexdigest()}
        elif path.is_file():
            files[name] = {'kind': 'regular', 'sha256': sha(path), 'bytes': path.stat().st_size}
        elif not path.exists():
            files[name] = {'kind': 'deleted'}
        else:
            raise ValueError('Nonregular input requires review')
    return files

def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as output:
        output.write(data)

def write_json(path, value):
    put(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())

def load(path):
    return json.loads(path.read_bytes())

assert not DEST.exists()
assert shutil.disk_usage(ROOT).free > 8192 * 1024 * 1024
docs = load(BASE / 'docs.json')
before_inputs = load(BASE / 'docs-inputs-before.json')
after_inputs = load(BASE / 'docs-inputs-after.json')
assert before_inputs == after_inputs == snapshot()
assert docs['passed'] and docs['execution']['exit_code'] == 0
assert docs['input_count'] == len(before_inputs) == 13239 and docs['changed_inputs'] == []
assert not docs['warning_lines'] and not docs['unresolved_anchor_lines']
assert len(docs['generated_target_checks']) == 5 and all(row['passed'] for row in docs['generated_target_checks'])
assert sha(DRIVER) == docs['driver_sha256']
assert sha(BASE / 'mkdocs-strict.log') == docs['log_sha256']
assert docs['source_revision'] == docs['source_revision_after'] == library_tests.git_revision(ROOT)
selected_path = ROOT / 'docs/development/evidence/io-metadata-observation-003/run/inputs-before.json'
selected = load(selected_path)
assert len(selected) == 693 and selected == library_tests.snapshot_inputs(ROOT)

original = load(BASE / 'before.json')
file_changes = []
patches = []
for relative, expected in original['files'].items():
    old = BASE / 'before-files' / relative
    new = ROOT / relative
    assert sha(old) == expected and sha(new) == before_inputs[relative]['sha256']
    file_changes.append({'path': relative, 'before_sha256': expected, 'after_sha256': sha(new),
                         'before_bytes': old.stat().st_size, 'after_bytes': new.stat().st_size})
    patches.extend(difflib.unified_diff(old.read_text().splitlines(keepends=True), new.read_text().splitlines(keepends=True),
                                       fromfile='before/' + relative, tofile='after/' + relative))
old_model = load(BASE / 'before-files/docs/development/status.json')
new_model = load(ROOT / 'docs/development/status.json')
changed_model_keys = sorted(k for k in old_model.keys() | new_model.keys() if old_model.get(k) != new_model.get(k))
assert changed_model_keys == ['generator']
assert sum(len(row['original_required_tests']) for row in new_model['items']) == 530
assert new_model['counts']['reported_statuses'] == {
    'implemented': 89, 'partially-verified': 67, 'verified': 0, 'unresolved': 8, 'not-applicable': 0}

old_test = BASE / 'before-files/scripts/development/test_validate_resolutions.py'
new_test = ROOT / 'scripts/development/test_validate_resolutions.py'
test_methods = lambda path: {node.name for node in ast.walk(ast.parse(path.read_bytes()))
                             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')}
added = sorted(test_methods(new_test) - test_methods(old_test))
assert len(added) == 3 and not test_methods(old_test) - test_methods(new_test)
red = load(BASE / 'red.json')
red002 = load(BASE / 'red002.json')
green = load(BASE / 'green.json')
assert red['exit_code'] == red002['exit_code'] == 1
assert red['test_source_sha256'] == sha(BASE / 'red-tests.py')
assert red002['test_source_sha256'] == sha(new_test)
assert red['generator_sha256'] == red002['generator_sha256'] == sha(BASE / 'before-files/scripts/development/validate_resolutions.py')
log_rows = []
for filename, record, expected_tests, expected_failures in [
    ('red.log', red, 49, 7), ('red002.log', red002, 49, 6),
    ('green-development.log', green[0], 73, None),
    ('regenerate.log', green[1], None, None), ('index-check.log', green[2], None, None)]:
    path = BASE / filename
    assert sha(path) == record['log_sha256']
    lines = path.read_text().splitlines()
    count_match = re.search(r'^Ran ([0-9]+) tests? in ', '\n'.join(lines), re.M)
    count = int(count_match[1]) if count_match else None
    assert count == expected_tests
    if expected_failures is not None:
        assert f'FAILED (failures={expected_failures})' in lines
    else:
        assert record['exit_code'] == 0
    failures = [line for line in lines if line.startswith('FAIL: ')]
    log_rows.append({'name': filename, 'sha256': sha(path), 'test_methods_run': count,
                     'failing_assertions_including_subtests': expected_failures,
                     'failing_distinct_methods': len({line.split(' (', 1)[0] for line in failures}),
                     'summary': [line for line in lines if re.match(r'^(Ran |OK$|FAILED|VALID:|CURRENT:|WROTE )', line)]})
assert len({line.split(' (', 1)[0] for line in (BASE / 'red002.log').read_text().splitlines() if line.startswith('FAIL: ')}) == 3

class Html(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.add(values['id'])
        if tag == 'a' and 'href' in values:
            self.hrefs.append(values['href'])

site = BASE / 'site'
output_paths = set()
for check in docs['generated_target_checks']:
    page = site / check['page']
    target_name, _, fragment = check['target'].partition('#')
    target = (site / target_name).resolve()
    assert target.is_file() and target.is_relative_to(site.resolve())
    html = Html()
    html.feed(page.read_text())
    for href in check['matching_hrefs']:
        assert href in html.hrefs
        uri = urlsplit(href)
        candidate = (page.parent / unquote(uri.path)).resolve()
        if candidate.is_dir():
            candidate = candidate / 'index.html'
        assert not uri.scheme and not uri.netloc and candidate == target and uri.fragment == fragment
    if fragment:
        target_html = Html()
        target_html.feed(target.read_text())
        assert fragment in target_html.ids
    else:
        assert target.read_bytes() == (ROOT / 'docs' / target_name).read_bytes()
    output_paths.update([page, target])
outputs = [{'site_path': p.relative_to(site).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size}
           for p in sorted(output_paths)]
assert snapshot() == before_inputs

DEST.mkdir(parents=True)
for filename in ['before.json', 'red.json', 'red002.json', 'green.json', 'docs.json',
                 'docs-inputs-before.json', 'docs-inputs-after.json', 'red.log', 'red002.log',
                 'green-development.log', 'regenerate.log', 'index-check.log']:
    put(DEST / filename, (BASE / filename).read_bytes())
for name in ['validate_resolutions.py', 'test_validate_resolutions.py']:
    put(DEST / ('before-' + name + '.txt'), (BASE / 'before-files/scripts/development' / name).read_bytes())
    put(DEST / ('after-' + name + '.txt'), (ROOT / 'scripts/development' / name).read_bytes())
put(DEST / 'red001-test-source.py.txt', (BASE / 'red-tests.py').read_bytes())
put(DEST / 'changes.patch.txt', ''.join(patches).encode())
put(DEST / 'docs-launcher.py', DRIVER.read_bytes())
write_json(DEST / 'log-review.json', log_rows)
write_json(DEST / 'generated-output-review.json', {'outputs': outputs, 'checks': docs['generated_target_checks'],
    'copied_json_bytes_match_source': True, 'build_output_is_not_deployed': True})
write_json(DEST / 'file-change-review.json', {'files': file_changes, 'changed_status_json_top_level_keys': changed_model_keys,
    'original_requirements_retained': 530, 'counts': new_model['counts'], 'new_test_methods': added,
    'selected_library_build_inputs': {'count': 693, 'source': str(selected_path.relative_to(ROOT)),
                                     'sha256': sha(selected_path), 'current_set_and_hashes_match': True}})
record = {
    'schema_version': 1, 'archived_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'source_revision': docs['source_revision'], 'dirty_worktree': True,
    'original_sweep': {'archive': original['failure_archive'],
                       'sha256': sha(ROOT / original['failure_archive']), 'overall_passed': False,
                       'python_tests_passed': 737, 'failed_command': 'mkdocs-strict'},
    'root_cause': 'doc_link emitted ../../docs/... for sibling documentation links, leaving MkDocs docs_dir before re-entering it. A hand-maintained upstream-status link had the same shape; two live dependency-plan links additionally used a nonexistent double-hyphen anchor.',
    'production_location': 'scripts/development/validate_resolutions.py:489-500 (doc_link)',
    'repair': 'Generate ../... for docs/ paths outside docs/development; retain same-directory and repository-file URL behavior plus Markdown/URL escaping. Correct one manual sibling link and two anchors. Regenerate indexes rather than hand-editing them.',
    'red001': {'exit_code': 1, 'test_methods_run': 49, 'failing_assertions_including_subtests': 7,
               'fixture_error': red002['fixture_correction']},
    'red002': {'exit_code': 1, 'test_methods_run': 49, 'failing_assertions_including_subtests': 6,
               'failing_distinct_methods': 3, 'repository_control_passed': True},
    'green_development': {'exit_code': 0, 'test_methods_run': 73, 'new_methods': 3, 'skipped': 0},
    'strict_docs': {'execution': docs['execution'], 'input_count': 13239, 'all_inputs_unchanged_through_archive_preflight': True,
                    'actual_link_or_anchor_targets_passed': 5, 'warnings': 0, 'unresolved_anchor_diagnostics': 0},
    'index_regeneration_and_check_passed': True, 'owner_records_or_statuses_changed': False,
    'original_acceptance_requirements_retained': 530, 'source_library_build_inputs_unchanged': 693,
    'policy_or_warning_suppression_changes': False, 'library_native_or_maven_consumer_methods_executed': 0,
    'network_deployment_publication_or_issue_mutations': 0, 'release_readiness_certified': False,
    'limitations': [
        '737 prior suite executions and 73 focused rerun executions overlap in70 development methods; do not sum as810 unique/current whole-suite tests.',
        'Tooling005 remains failed. This separate repair result does not rewrite that command outcome or its source snapshot.',
        'The strict docs input freeze includes all nonignored Git-listed files, but does not turn dirty sources into an immutable release candidate.',
        'Full red/green unit logs are archived. The strict MkDocs raw log stays task-local and hash-bound; checked target paths/output digests and empty warning/anchor summaries are preserved instead of copying its large INFO body.',
        'Additive collector evidence was absent from its own build inputs; later documentation additions need a separate lightweight strict build.',
        'No code/API/CI/native/consumer/legal/dependency/release gate is certified by a local documentation repair.'
    ]
}
write_json(DEST / 'archive.json', record)
put(DEST / 'collector.py', Path(__file__).read_bytes())
files = sorted(path for path in DEST.rglob('*') if path.is_file())
put(DEST / 'SHA256SUMS', ''.join(f'{sha(path)}  {path.relative_to(DEST).as_posix()}\n' for path in files).encode())
print(json.dumps({'archive': str(DEST.relative_to(ROOT)), 'sha256': sha(DEST / 'archive.json'),
                  'bound_files': len(files), 'development_tests_passed': 73,
                  'strict_docs_passed': True, 'actual_link_targets_passed': 5}, indent=2))
