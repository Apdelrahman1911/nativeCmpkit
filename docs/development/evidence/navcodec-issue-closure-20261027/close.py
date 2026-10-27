"""Default dry-run; exactly one evidence-backed NAV-005 closure when --apply."""
from pathlib import Path
import argparse
import datetime as dt
import gzip
import hashlib
import json
import shutil
import subprocess

ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path(__file__).parent
REPO = 'Apdelrahman1911/nativeCmpkit'
REV = 'cd51e8d626afd3fb7a5688f8b3f5db584a3bd386'
MAIN = '94d2492e99d5cbc060409d94d9f88febd06222d5'
ACCEPT = 'docs/development/evidence/navcodec-original-acceptance-20261027/lead-original-acceptance-review.json'
WORK = 'docs/development/evidence/github-actions/40549350671/lead-independent-review.json'
PREFLIGHT = 'docs/development/evidence/ci-preflight-20261027-026/lead-review.json'
LINKS = 'docs/development/evidence/postfreeze026-links-20261027/review.json'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
OUT = BASE / ('apply' if args.apply else 'dry-run')
OUT.mkdir(exist_ok=False)

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')

def get(endpoint, name, paginate=False):
    command = ['gh', 'api', 'repos/' + REPO + '/' + endpoint]
    if paginate:
        command.append('--paginate')
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
    (OUT / (name + '.stderr')).write_bytes(result.stderr)
    (OUT / (name + '.json.gz')).write_bytes(gzip.compress(result.stdout, mtime=0))
    assert result.returncode == 0, 'Read-only error; preserve and do not automatically retry'
    if not paginate:
        return json.loads(result.stdout)
    text, decoder = result.stdout.decode(), json.JSONDecoder()
    position, pages = 0, []
    while position < len(text):
        while position < len(text) and text[position].isspace():
            position += 1
        if position == len(text):
            break
        page, position = decoder.raw_decode(text, position)
        assert isinstance(page, list)
        pages.append(page)
    items = [item for page in pages for item in page]
    assert len(items) == len({item['id'] for item in items})
    return items

def mutate(endpoint, method, name, payload):
    save(name + '-payload.json', payload)
    started = utc()
    try:
        result = subprocess.run(['gh', 'api', 'repos/' + REPO + '/' + endpoint, '--method', method,
                                 '--input', str(OUT / (name + '-payload.json'))],
                                cwd=ROOT, capture_output=True, timeout=120)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = None, error.stdout or b'', error.stderr or b''
    (OUT / (name + '.stdout')).write_bytes(stdout)
    (OUT / (name + '.stderr')).write_bytes(stderr)
    save(name + '-request.json', {'endpoint': 'repos/' + REPO + '/' + endpoint, 'method': method,
        'invocations': 1, 'exit_code': code, 'started_utc': started, 'finished_utc': utc(), 'automatic_retry': False})
    return code

def preserve(issue):
    return {'title': issue['title'], 'body': issue['body'], 'labels': sorted(issue['labels'], key=lambda item: item['id'])}

def local():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == REV
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'development/preview-hardening'
    assert subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=ROOT, text=True).strip() == 'https://github.com/' + REPO + '.git'
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)

local()
started = utc()
assert get('branches/main', 'main-before')['commit']['sha'] == MAIN
assert get('branches/development/preview-hardening', 'development-before')['commit']['sha'] == REV
assert get('pages', 'pages-before')['status'] is None
assert get('releases?per_page=100', 'releases-before') == []
for path in (ACCEPT, WORK, PREFLIGHT, LINKS):
    assert (ROOT / path).read_bytes() == subprocess.check_output(['git', 'show', REV + ':' + path], cwd=ROOT)
accepted = json.loads((ROOT / ACCEPT).read_bytes())
work = json.loads((ROOT / WORK).read_bytes())
preflight = json.loads((ROOT / PREFLIGHT).read_bytes())
links = json.loads((ROOT / LINKS).read_bytes())
assert accepted['evidence_integrity_passed'] and accepted['accepted_for_original_scoped_closure']
assert accepted['finding'] == 'NAV-005' and accepted['issue_number'] == 93
assert accepted['remaining_original_acceptance_requirements'] == [] and len(accepted['requirements_review']) == 4
assert all(row['status'].startswith('passed-original-scope') and row['executed_methods']
           and all(method['actual_case']['status'] == 'passed' for method in row['executed_methods'])
           for row in accepted['requirements_review'])
assert work['evidence_integrity_passed'] and work['totals']['tests'] == work['totals']['passed'] == 54
assert work['actual_xml_reports'] == 7 and work['all_previous_52_desktop_case_identities_retained']
assert preflight['passed'] and preflight['commands'] == 23 and preflight['python_tooling_methods'] == 1225
assert links['passed'] and links['all_other_executable_test_and_workflow_inputs_unchanged'] and links['source_and_staged_index_held']
for path, digest in accepted['current_navigation_source_hashes_identical_to_work_run'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
ledger = json.loads((ROOT / 'docs/development/resolutions/NAV.json').read_bytes())
assert next(row for row in ledger if row['id'] == 'NAV-005')['status'] == 'verified'
assert next(row for row in ledger if row['id'] == 'NAV-005')['remaining'] == []
assert next(row for row in ledger if row['id'] == 'NAV-004')['status'] != 'verified'
original = json.loads((ROOT / 'docs/development/evidence/navcodec-original-acceptance-20261027/issue-93-current-before.json').read_bytes())
issue = get('issues/93', 'issue-before')
assert issue['state'] == 'open' and 'pull_request' not in issue and preserve(issue) == preserve(original)
assert hashlib.sha256(issue['body'].encode()).hexdigest() == accepted['issue_body_sha256_before']
marker = '<!-- nativecmpkit-resolution:NAV-005:20261027-immutable-original-work-acceptance -->'
comments = get('issues/93/comments?per_page=100', 'comments-before', True)
assert not any(marker in (comment.get('body') or '') for comment in comments), 'Existing marker: read-only reconcile, never duplicate POST'
body = (BASE / 'comment.md').read_text()
assert body.startswith(marker)
for path in (ACCEPT, WORK, PREFLIGHT, LINKS):
    assert 'https://github.com/' + REPO + '/blob/' + REV + '/' + path in body
save('preflight.json', {'passed': True, 'source_revision': REV, 'dry_run': not args.apply,
    'issue_number': 93, 'original_body_title_labels_unchanged': True, 'duplicate_markers': 0,
    'other_issue_states_not_mutated': True, 'publication_performed': False})
post, patch, comment, final = None, None, None, None
if args.apply:
    fresh = get('issues/93', 'issue-immediate-before')
    assert fresh['state'] == 'open' and preserve(fresh) == preserve(issue)
    post = mutate('issues/93/comments', 'POST', 'comment', {'body': body})
    matching = [item for item in get('issues/93/comments?per_page=100', 'comments-after', True)
                if marker in (item.get('body') or '')]
    assert len(matching) == 1 and matching[0]['body'] == body, 'Uncertain POST; no automatic retry or closure'
    comment = get('issues/comments/' + str(matching[0]['id']), 'comment-readback')
    assert comment['body'] == body and comment['id'] == matching[0]['id']
    before_close = get('issues/93', 'issue-before-close')
    assert before_close['state'] == 'open' and preserve(before_close) == preserve(issue)
    patch = mutate('issues/93', 'PATCH', 'close', {'state': 'closed', 'state_reason': 'completed'})
    final = get('issues/93', 'issue-after')
    assert final['state'] == 'closed' and final['state_reason'] == 'completed' and preserve(final) == preserve(issue)
    current_comment = get('issues/comments/' + str(comment['id']), 'comment-final-readback')
    assert current_comment['id'] == comment['id'] and current_comment['body'] == body
    closed = get('issues?state=closed&per_page=100', 'all-closed-issues-after', True)
    assert all('pull_request' not in item for item in closed)
    numbers = sorted(item['number'] for item in closed)
    assert numbers == [15, 16, 41, 42, 91, 93, 123, 128, 136, 146, 155, 156, 160, 171]
else:
    numbers = None
assert get('branches/main', 'main-after')['commit']['sha'] == MAIN
assert get('branches/development/preview-hardening', 'development-after')['commit']['sha'] == REV
local()
value = {'passed': True, 'dry_run': not args.apply, 'started_utc': started, 'finished_utc': utc(),
    'source_revision': REV, 'main_preserved': MAIN, 'issue_number': 93, 'finding': 'NAV-005',
    'issues_closed': int(args.apply), 'comments_posted': int(args.apply), 'POST_exit': post, 'PATCH_exit': patch,
    'POST_invocations': int(args.apply), 'PATCH_invocations': int(args.apply),
    'comment_id': comment['id'] if comment else None, 'comment_url': comment['html_url'] if comment else None,
    'comment_sha256': hashlib.sha256(body.encode()).hexdigest(),
    'state': final['state'] if final else issue['state'], 'original_body_title_labels_unchanged': True,
    'all_current_closed_numbers': numbers, 'total_closed': len(numbers) if numbers else None,
    'NAV004_or_other_issues_mutated': False, 'publication_performed': False, 'release_readiness_certified': False,
    'scope': 'Original NAV-005 only, every criterion reviewed and pushed. Exactly one additive resolution comment/state-only closure; '
        'no erased legacy-getter, native-device, consumer, ABI, legal, dependency, security or release clearance.'}
save('receipt.json', value)
shutil.copyfile(Path(__file__), OUT / 'close.py')
shutil.copyfile(BASE / 'comment.md', OUT / 'comment.md')
(OUT / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n'
                                     for path in sorted(OUT.iterdir()) if path.is_file()))
print(json.dumps(value, indent=2), flush=True)
