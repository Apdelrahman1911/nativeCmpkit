"""Independent read-only reconciliation; never replay completed issue mutations."""
from pathlib import Path
import datetime as dt
import gzip
import hashlib
import json
import shutil
import subprocess

ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path(__file__).parent
APPLY = Path('/dev/shm/nativecmpkit-uikit-closures-20261027/apply')
DRY = Path('/dev/shm/nativecmpkit-uikit-closures-20261027/dry-run')
OUT = BASE / 'archive'
DEST = ROOT / 'docs/development/evidence/uikit-issue-closures-20261027'
REPO = 'Apdelrahman1911/nativeCmpkit'
REV = '70114ff3d579af291c4a3028181efc7d884e23a9'
MAIN = '94d2492e99d5cbc060409d94d9f88febd06222d5'

assert not OUT.exists() and not DEST.exists(), 'Never overwrite existing evidence'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == REV
OUT.mkdir()
receipt = json.loads((APPLY / 'receipt.json').read_bytes())
assert receipt['passed'] and receipt['issues_closed'] == receipt['comments_posted'] == 2
assert not receipt['dry_run'] and not receipt['publishing_deployment_release_or_Pages']
for directory in (APPLY, DRY):
    for row in (directory / 'SHA256SUMS').read_text().splitlines():
        digest, name = row.split('  ', 1)
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest

def read(endpoint, filename, paginate=False):
    command = ['gh', 'api', 'repos/' + REPO + '/' + endpoint]
    if paginate:
        command += ['--paginate', '--slurp']
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
    (OUT / (filename + '.stderr')).write_bytes(result.stderr)
    (OUT / (filename + '.json.gz')).write_bytes(gzip.compress(result.stdout, mtime=0))
    assert result.returncode == 0, 'Preserve failed observation; no automatic retry'
    value = json.loads(result.stdout)
    if paginate:
        assert isinstance(value, list) and all(isinstance(page, list) for page in value)
        value = [item for page in value for item in page]
        assert len({item['id'] for item in value}) == len(value)
    return value

def preserve(issue):
    return {'title': issue['title'], 'body': issue['body'],
            'labels': sorted(issue['labels'], key=lambda label: label['id'])}

reviewed = []
for row in receipt['results']:
    number = row['number']
    before = json.loads((APPLY / f'issue-{number}-before.json').read_bytes())
    after = read('issues/' + str(number), f'issue-{number}-fresh')
    comment = read('issues/comments/' + str(row['comment_id']), f'comment-{number}-fresh')
    body = (APPLY / (row['id'] + '-comment.md')).read_text()
    assert row['POST_exit_code'] == row['PATCH_exit_code'] == 0
    assert row['comment_POST_invocations'] == row['state_PATCH_invocations'] == 1
    assert after['number'] == number and after['state'] == 'closed'
    assert after['state_reason'] == 'completed' and after['closed_at'] == row['closed_at']
    assert preserve(before) == preserve(after)
    assert comment['id'] == row['comment_id'] and comment['body'] == body
    assert comment['html_url'] == row['comment_url']
    assert hashlib.sha256(body.encode()).hexdigest() == row['comment_sha256']
    comments = read('issues/' + str(number) + '/comments?per_page=100', f'comments-{number}-fresh', True)
    marker = body.splitlines()[0]
    matching = [item for item in comments if marker in (item.get('body') or '')]
    assert len(matching) == 1 and matching[0]['id'] == comment['id']
    reviewed.append({'number': number, 'id': row['id'], 'state': after['state'],
                     'comment_url': comment['html_url'], 'original_body_title_labels_unchanged': True,
                     'exact_single_resolution_marker': True})

closed = read('issues?state=closed&per_page=100', 'all-closed-issues-fresh', True)
assert all('pull_request' not in item for item in closed), 'Do not count closed PRs as issues'
numbers = sorted(item['number'] for item in closed)
assert numbers == [15, 16, 41, 42, 91, 123, 128, 136, 146, 155, 156, 160, 171]
assert read('branches/main', 'main-fresh')['commit']['sha'] == MAIN
assert read('branches/development/preview-hardening', 'development-fresh')['commit']['sha'] == REV
assert read('releases?per_page=100', 'releases-fresh') == []
assert read('pages', 'pages-fresh')['status'] is None

for directory, name in ((APPLY, 'apply'), (DRY, 'dry-run')):
    shutil.copytree(directory, OUT / name)
shutil.copyfile(Path(__file__), OUT / 'review.py')
value = {'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'passed': True,
         'source_revision': REV, 'main_preserved': MAIN, 'new_closed_issues': [128, 160],
         'exact_closure_readbacks': reviewed, 'total_closed': len(numbers),
         'all_current_closed_numbers': numbers, 'no_mutation_replayed': True,
         'publication_performed': False, 'release_readiness_certified': False,
         'scope': 'Original UI-015/UI-022 only; exact current readback and immutable pushed acceptance. '
                  'Thirteen total closed issues, not thirteen new fixes. No broader native/device, '
                  'consumer, ABI, legal, dependency, security or release clearance.'}
(OUT / 'lead-final-readback.json').write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
(OUT / 'README.md').write_text('# Exact UI-015 / UI-022 closures\n\n'
    'Issues #128 and #160 are closed after reviewed immutable UIKit evidence and pushed original '
    'acceptance. One additive comment and one state-only PATCH per issue; original titles, bodies '
    'and labels are unchanged. Independent fresh readback confirms 13 total closed issues. '
    'No mutation was replayed and no release gate is lifted.\n')
(OUT / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' +
    p.relative_to(OUT).as_posix() + '\n' for p in sorted(OUT.rglob('*'))
    if p.is_file() and p != OUT / 'SHA256SUMS'))
shutil.copytree(OUT, DEST)
assert all(p.read_bytes() == (DEST / p.relative_to(OUT)).read_bytes()
           for p in OUT.rglob('*') if p.is_file())
print(json.dumps(value, indent=2))
