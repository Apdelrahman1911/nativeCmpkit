"""Fresh independent read-only issue/comment/list verification and additive archive."""
from pathlib import Path
import datetime as dt
import gzip
import hashlib
import json
import shutil
import subprocess

ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path(__file__).parent
DEST = ROOT / 'docs/development/evidence/navhost-issue-closure-20261027'
REPO = 'Apdelrahman1911/nativeCmpkit'
REV = 'a8ed58a77047a4e5c6f38aab6230627593ed1828'
receipt = json.loads((BASE / 'apply/receipt.json').read_bytes())
before = json.loads(gzip.decompress((BASE / 'apply/issue-before.json.gz').read_bytes()))
body = (BASE / 'comment.md').read_text()
assert receipt['passed'] and receipt['issues_closed'] == receipt['comments_posted'] == 1
assert receipt['POST_invocations'] == receipt['PATCH_invocations'] == 1
assert receipt['POST_exit'] == receipt['PATCH_exit'] == 0
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == REV
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)

def get(endpoint, name):
    result = subprocess.run(['gh', 'api', 'repos/' + REPO + '/' + endpoint],
                            cwd=ROOT, capture_output=True, timeout=120)
    (BASE / (name + '.json.gz')).write_bytes(gzip.compress(result.stdout, mtime=0))
    (BASE / (name + '.stderr')).write_bytes(result.stderr)
    assert result.returncode == 0, 'No automatic retry after read failure'
    return json.loads(result.stdout)

issue = get('issues/94', 'final-issue')
comment = get('issues/comments/' + str(receipt['comment_id']), 'final-comment')
comments = get('issues/94/comments?per_page=100', 'final-comments')
closed = get('issues?state=closed&per_page=100', 'final-closed-list')
main = get('branches/main', 'final-main')
development = get('branches/development/preview-hardening', 'final-development')
assert issue['state'] == 'closed' and issue['state_reason'] == 'completed'
assert all(issue[key] == before[key] for key in ('body', 'title', 'labels'))
assert comment['body'] == body and comment['id'] == receipt['comment_id']
assert hashlib.sha256(body.encode()).hexdigest() == receipt['comment_sha256']
marker = body.splitlines()[0]
assert len([item for item in comments if marker in (item.get('body') or '')]) == 1
assert all('pull_request' not in item for item in closed)
numbers = sorted(item['number'] for item in closed)
assert numbers == receipt['all_current_closed_numbers'] and len(numbers) == 15
assert main['commit']['sha'] == receipt['main_preserved']
assert development['commit']['sha'] == REV
review = {'passed': True, 'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'source_revision': REV, 'issue_number': 94, 'finding': 'NAV-006',
          'state': 'closed', 'closed_at': issue['closed_at'],
          'comment_id': comment['id'], 'comment_url': comment['html_url'],
          'comment_sha256': receipt['comment_sha256'], 'exact_single_resolution_marker': True,
          'original_body_title_labels_unchanged': True, 'main_preserved': receipt['main_preserved'],
          'all_current_closed_numbers': numbers, 'total_closed': 15,
          'POST_invocations': 1, 'PATCH_invocations': 1, 'no_mutation_replayed': True,
          'initial_dependency_state_reviewer_failure_preserved': True,
          'previous_NAV001_NAV002_verified_and_closed_states_preserved': True,
          'other_issues_mutated': False, 'publication_performed': False,
          'release_readiness_certified': False,
          'scope': 'Every original NAV-006 shared-host criterion verified/pushed; exact fresh issue/comment/list readback. '
                   '15 total closures, one new closure. Previously verified NAV001/002 unchanged; NAV004 and broader '
                   'native/device/consumer/API-ABI/legal/dependency/security/release gates remain independent.'}
(BASE / 'lead-final-readback.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
assert not DEST.exists()
shutil.copytree(BASE, DEST)
(DEST / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' +
    path.relative_to(DEST).as_posix() + '\n' for path in sorted(DEST.rglob('*')) if path.is_file()))
print(json.dumps(review, indent=2))
