"""Read-only reconciliation after exact closure but stale/incomplete list observation."""
from pathlib import Path
import datetime as dt
import gzip
import hashlib
import json
import shutil
import subprocess

ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path(__file__).parent
OUT = BASE / 'fresh-readback'
DEST = ROOT / 'docs/development/evidence/navcodec-issue-closure-20261027'
REPO = 'Apdelrahman1911/nativeCmpkit'
REV = 'cd51e8d626afd3fb7a5688f8b3f5db584a3bd386'
MAIN = '94d2492e99d5cbc060409d94d9f88febd06222d5'
OUT.mkdir(exist_ok=False)

def get(endpoint, name, paginate=False):
    command = ['gh', 'api', 'repos/' + REPO + '/' + endpoint, '-H', 'Cache-Control: no-cache']
    if paginate:
        command.append('--paginate')
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
    (OUT / (name + '.json.gz')).write_bytes(gzip.compress(result.stdout, mtime=0))
    (OUT / (name + '.stderr')).write_bytes(result.stderr)
    assert result.returncode == 0
    if not paginate:
        return json.loads(result.stdout)
    raw, decoder, pages, position = result.stdout.decode(), json.JSONDecoder(), [], 0
    while position < len(raw):
        while position < len(raw) and raw[position].isspace():
            position += 1
        if position == len(raw):
            break
        page, position = decoder.raw_decode(raw, position)
        assert isinstance(page, list)
        pages.append(page)
    items = [item for page in pages for item in page]
    assert len(items) == len({item['id'] for item in items})
    return items

apply = BASE / 'apply'
before = json.loads(gzip.decompress((apply / 'issue-before.json.gz').read_bytes()))
old_after = json.loads(gzip.decompress((apply / 'issue-after.json.gz').read_bytes()))
old_comment = json.loads(gzip.decompress((apply / 'comment-final-readback.json.gz').read_bytes()))
body = (BASE / 'comment.md').read_text()
assert old_after['state'] == 'closed' and old_after['state_reason'] == 'completed'
assert old_comment['body'] == body
for name in ('comment-request.json', 'close-request.json'):
    request = json.loads((apply / name).read_bytes())
    assert request['exit_code'] == 0 and request['invocations'] == 1 and not request['automatic_retry']
issue = get('issues/93', 'issue-93-fresh')
comment = get('issues/comments/' + str(old_comment['id']), 'comment-93-fresh')
assert issue['state'] == 'closed' and issue['state_reason'] == 'completed'
assert issue['closed_at'] == old_after['closed_at']
assert all(issue[key] == before[key] for key in ('title', 'body', 'labels'))
assert comment['body'] == body and comment['id'] == old_comment['id']
comments = get('issues/93/comments?per_page=100', 'comments-93-fresh', True)
marked = [item for item in comments if body.splitlines()[0] in (item.get('body') or '')]
assert len(marked) == 1 and marked[0]['id'] == comment['id']
closed = get('issues?state=closed&per_page=100&sort=updated&direction=desc', 'all-closed-issues-fresh', True)
assert all('pull_request' not in item for item in closed)
numbers = sorted(item['number'] for item in closed)
assert numbers == [15, 16, 41, 42, 91, 93, 123, 128, 136, 146, 155, 156, 160, 171]
assert get('branches/main', 'main-fresh')['commit']['sha'] == MAIN
assert get('branches/development/preview-hardening', 'development-fresh')['commit']['sha'] == REV
assert get('pages', 'pages-fresh')['status'] is None
assert get('releases?per_page=100', 'releases-fresh') == []
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == REV
failure = {'passed': False, 'closure_driver_exit_code': 1,
    'stage': 'full closed-issue-list assertion after successful exact issue/comment readback',
    'observed_list_total': 13, 'missing_from_initial_list': [93],
    'exact_issue_state_in_same_attempt': 'closed', 'POST_exit_code': 0, 'PATCH_exit_code': 0,
    'hypothesis_not_proven': 'The immediately returned list was stale or incomplete; internal GitHub/proxy consistency mechanism is not established.',
    'mutation_not_replayed': True, 'resolution': 'Separate fresh direct/comment/full-list read-only observations now agree; no closure or comment was repeated.'}
(OUT / 'initial-list-failure.json').write_text(json.dumps(failure, indent=2, sort_keys=True) + '\n')
review = {'passed': True, 'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'source_revision': REV,
    'main_preserved': MAIN, 'issue_number': 93, 'finding': 'NAV-005', 'state': 'closed',
    'closed_at': issue['closed_at'], 'comment_id': comment['id'], 'comment_url': comment['html_url'],
    'comment_sha256': hashlib.sha256(body.encode()).hexdigest(),
    'original_body_title_labels_unchanged': True, 'exact_single_resolution_marker': True,
    'POST_invocations': 1, 'PATCH_invocations': 1, 'no_mutation_replayed': True,
    'all_current_closed_numbers': numbers, 'total_closed': len(numbers),
    'initial_thirteen_item_list_failure_preserved': True, 'NAV004_or_other_issues_mutated': False,
    'publication_performed': False, 'release_readiness_certified': False,
    'scope': 'Every original NAV-005 criterion verified/pushed; exact current issue/comment and full closed-list readback. '
        'Fourteen total closed issues, not fourteen new fixes. Other native/legacy/consumer/ABI/legal/dependency/security gates remain.'}
(OUT / 'lead-final-readback.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
assert not DEST.exists()
DEST.mkdir()
for folder in ('dry-run', 'apply', 'fresh-readback'):
    shutil.copytree(BASE / folder, DEST / folder)
for name in ('close.py', 'comment.md', 'reconcile.py', 'lead-dry-review.json', 'lead-dry-review-red001.json'):
    shutil.copyfile(BASE / name, DEST / name)
shutil.copyfile(OUT / 'lead-final-readback.json', DEST / 'lead-final-readback.json')
(DEST / 'README.md').write_text('# NAV-005 exact issue closure\n\n'
    'Issue #93 is now closed after every original criterion was verified and acceptance pushed. '
    'One additive comment and one state-only PATCH; original title/body/labels preserved. '
    'The initial list assertion failed despite exact closed-state/comment readback; separate fresh '
    'direct/comment/full-list observations confirm 14 total closed issues. No mutation was replayed. '
    'The list-consistency mechanism is unproven; both observations remain. No wider release gate is cleared.\n')
(DEST / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' +
    path.relative_to(DEST).as_posix() + '\n' for path in sorted(DEST.rglob('*')) if path.is_file()))
print(json.dumps(review, indent=2), flush=True)
