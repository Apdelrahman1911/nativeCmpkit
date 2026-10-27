"""Default dry-run; one pushed, original-scope NAV-006 closure with exact readback."""
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
REV = 'a8ed58a77047a4e5c6f38aab6230627593ed1828'
WORK_REV = '6ada26d3c47096ad0750a111c7e807b03230d844'
MAIN = '94d2492e99d5cbc060409d94d9f88febd06222d5'
ACCEPT = 'docs/development/evidence/navhost-original-acceptance-20261027/lead-original-acceptance-review.json'
WORK = 'docs/development/evidence/github-actions/40576835737/lead-independent-review.json'
PREFLIGHT = 'docs/development/evidence/ci-preflight-20261027-030/lead-review.json'
LINKS = 'docs/development/evidence/postfreeze030-links-20261027/review.json'
PRIOR_CLOSED = [15, 16, 41, 42, 91, 93, 123, 128, 136, 146, 155, 156, 160, 171]
MARKER = '<!-- nativecmpkit-resolution:NAV-006:20261027-immutable-original-host-acceptance -->'
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
    assert result.returncode == 0, 'Read-only failure; preserve and do not automatically retry'
    if not paginate:
        return json.loads(result.stdout)
    raw, decoder, position, items = result.stdout.decode(), json.JSONDecoder(), 0, []
    while position < len(raw):
        while position < len(raw) and raw[position].isspace():
            position += 1
        if position == len(raw):
            break
        page, position = decoder.raw_decode(raw, position)
        assert isinstance(page, list)
        items.extend(page)
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
    return {'title': issue['title'], 'body': issue['body'],
            'labels': sorted(issue['labels'], key=lambda item: item['id'])}

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
assert accepted['accepted_original_scope'] and accepted['current_original_scope_sources_match_commit']
assert accepted['finding_id'] == 'NAV-006' and accepted['issue_number'] == 94
assert accepted['source_revision'] == work['source_revision'] == WORK_REV
assert len(accepted['criteria']) == 3 and accepted['host_methods_passed'] == 12
assert work['evidence_integrity_passed'] and work['totals'] == {
    'errors': 0, 'executed': 55, 'failures': 0, 'not_applicable': 0, 'passed': 55,
    'skipped': 0, 'tests': 55, 'unexpected_skipped': 0}
assert work['actual_xml_reports'] == 7 and work['source_input_count'] == 727
assert work['all_previous_54_desktop_case_identities_retained']
assert work['setup_test_SDK_and_global_fingerprints_match']
for criterion in accepted['criteria']:
    assert criterion['satisfied_in_original_scope'] and criterion['immutable_passing_methods']
    for method in criterion['immutable_passing_methods']:
        matches = [case for case in work['actual_cases'] if
                   case['classname'] == criterion['immutable_passing_class'] and case['name'] == method]
        assert len(matches) == 1 and matches[0]['status'] == 'passed'
for path, digest in accepted['current_source_hashes'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    assert (ROOT / path).read_bytes() == subprocess.check_output(['git', 'show', WORK_REV + ':' + path], cwd=ROOT)
assert hashlib.sha256((ROOT / accepted['original_finding_file']).read_bytes()).hexdigest() == accepted['original_finding_file_sha256']
assert preflight['passed'] and preflight['commands'] == 5 and preflight['python_tooling_methods'] == 0
assert preflight['source_and_staged_index_held'] and preflight['output_anchor_count'] == 58
assert links['passed'] and links['all_other_executable_test_and_workflow_inputs_unchanged'] and links['source_stage_inputs_held']
ledger = json.loads((ROOT / 'docs/development/resolutions/NAV.json').read_bytes())
assert next(row for row in ledger if row['id'] == 'NAV-006')['status'] == 'verified'
assert next(row for row in ledger if row['id'] == 'NAV-006')['remaining'] == []
prior_ledger = json.loads(subprocess.check_output(
    ['git', 'show', WORK_REV + ':docs/development/resolutions/NAV.json'], cwd=ROOT))
for name in ('NAV-001', 'NAV-002'):
    current = next(row for row in ledger if row['id'] == name)
    assert current['status'] == 'verified' and current['remaining'] == []
    assert current == next(row for row in prior_ledger if row['id'] == name)
assert next(row for row in ledger if row['id'] == 'NAV-004')['status'] != 'verified'
mapping = next(row for row in json.loads((ROOT / 'docs/migration/issue-map.json').read_bytes())['items'] if row['number'] == 94)
assert mapping['finding_ids'] == ['NAV-006']
issue = get('issues/94', 'issue-before')
assert issue['state'] == 'open' and 'pull_request' not in issue and issue['title'] == mapping['title']
assert hashlib.sha256(issue['body'].encode()).hexdigest() == mapping['body_sha256']
closed_before = get('issues?state=closed&per_page=100', 'all-closed-before', True)
assert all('pull_request' not in item for item in closed_before)
assert sorted(item['number'] for item in closed_before) == PRIOR_CLOSED
comments = get('issues/94/comments?per_page=100', 'comments-before', True)
assert not any(MARKER in (comment.get('body') or '') for comment in comments), 'Existing marker: reconcile read-only, never duplicate POST'
body = (BASE / 'comment.md').read_text()
assert body.startswith(MARKER)
for path in (ACCEPT, WORK, PREFLIGHT, LINKS):
    assert 'https://github.com/' + REPO + '/blob/' + REV + '/' + path in body
save('preflight.json', {'passed': True, 'source_revision': REV, 'work_revision': WORK_REV, 'dry_run': not args.apply,
    'issue_number': 94, 'original_body_title_labels_preserved': True, 'duplicate_markers': 0,
    'original_requirements_accepted': 3, 'prior_closed_numbers': PRIOR_CLOSED,
    'other_issue_states_not_mutated': True, 'publication_performed': False})
post, patch, comment, final, numbers = None, None, None, None, PRIOR_CLOSED
if args.apply:
    fresh = get('issues/94', 'issue-immediate-before')
    assert fresh['state'] == 'open' and preserve(fresh) == preserve(issue)
    post = mutate('issues/94/comments', 'POST', 'comment', {'body': body})
    matching = [item for item in get('issues/94/comments?per_page=100', 'comments-after', True)
                if MARKER in (item.get('body') or '')]
    assert len(matching) == 1 and matching[0]['body'] == body, 'Uncertain POST; no automatic retry or closure'
    comment = get('issues/comments/' + str(matching[0]['id']), 'comment-readback')
    assert comment['body'] == body and comment['id'] == matching[0]['id']
    before_close = get('issues/94', 'issue-before-close')
    assert before_close['state'] == 'open' and preserve(before_close) == preserve(issue)
    patch = mutate('issues/94', 'PATCH', 'close', {'state': 'closed', 'state_reason': 'completed'})
    final = get('issues/94', 'issue-after')
    assert final['state'] == 'closed' and final['state_reason'] == 'completed' and preserve(final) == preserve(issue)
    current_comment = get('issues/comments/' + str(comment['id']), 'comment-final-readback')
    assert current_comment['id'] == comment['id'] and current_comment['body'] == body
    closed = get('issues?state=closed&per_page=100', 'all-closed-after', True)
    assert all('pull_request' not in item for item in closed)
    numbers = sorted(item['number'] for item in closed)
    assert numbers == sorted([*PRIOR_CLOSED, 94])
assert get('branches/main', 'main-after')['commit']['sha'] == MAIN
assert get('branches/development/preview-hardening', 'development-after')['commit']['sha'] == REV
local()
value = {'passed': True, 'dry_run': not args.apply, 'started_utc': started, 'finished_utc': utc(),
    'source_revision': REV, 'work_revision': WORK_REV, 'main_preserved': MAIN, 'issue_number': 94, 'finding': 'NAV-006',
    'issues_closed': int(args.apply), 'comments_posted': int(args.apply), 'POST_exit': post, 'PATCH_exit': patch,
    'POST_invocations': int(args.apply), 'PATCH_invocations': int(args.apply),
    'comment_id': comment['id'] if comment else None, 'comment_url': comment['html_url'] if comment else None,
    'comment_sha256': hashlib.sha256(body.encode()).hexdigest(),
    'state': final['state'] if final else issue['state'], 'original_body_title_labels_unchanged': True,
    'all_current_closed_numbers': numbers, 'total_closed': len(numbers),
    'other_issues_mutated': False, 'publication_performed': False, 'release_readiness_certified': False,
    'scope': 'Original NAV-006 three shared-host requirements only, passing immutable real Compose desktop. '
        'One additive comment/state-only closure with exact readback; NAV-001/002/004, native-device, consumer, '
        'ABI, legal, dependency, security and release gates remain separate.'}
save('receipt.json', value)
shutil.copyfile(Path(__file__), OUT / 'close.py')
shutil.copyfile(BASE / 'comment.md', OUT / 'comment.md')
(OUT / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n'
                                     for path in sorted(OUT.iterdir()) if path.is_file()))
print(json.dumps(value, indent=2), flush=True)
