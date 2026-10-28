"""One additive progress comment per existing issue; do not change issue state/body."""
from pathlib import Path
import json, subprocess, datetime
ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).parent
REPO = 'Apdelrahman1911/nativeCmpkit'
MARKER = '<!-- nativecmpkit:targeted-verification:17db28fa:windows-and-coil -->'
BODY = '''## Important targeted verification — 2026-10-28

Immutable source **17db28fa56c5a50b1637d8abc0bf471b7e56af2c**:
- [Windows picker/share cache + actual JNI](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40606411532): **89/89 executions**, 15 fresh XML, zero failures/errors/unexpected skips; one exact macOS-only case N/A. The original Windows concurrent sharing failure from failed run40602393181 now passes. Complete private staging is published with a no-replace hard link, never a potentially replacing atomic move; open-reader identity preservation and failed/unsupported publication regressions pass in both modules. Old three-argument descriptors retained. Picker54/share35; actual ABI/diagnostic/borrowed-pointer/unsupported-owner tests executed.
- [Android Coil only](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40606422085): **5/5**, one fresh XML, zero skips. Both extra failed fixtures now complete final descriptor/close/error-origin/null-open assertions. Earlier accepted IO27 reused with **zero new IO executions**; all94 relevant module/toolchain/build inputs match f37bf141. Controlled Robolectric resolver transport is not device/provider Binder IPC.

Independent review verifies all738 exact own-Git inputs, before/after maps, artifact and XML hashes, actual commands and setup/test SDK correspondence. No successful unchanged Linux/macOS/IO suite replay. Prior whole failed runs remain failed and preserved.

**This issue remains open where its original acceptance requirements are incomplete**: Windows cross-process loaded-DLL, old-system-ABI/trusted-packager, foreign-owner/read-only/noexec/native-parent or the broader device/consumer/ABI/legal/dependency matrix are not certified. A passing cache/JNI suite does not waive those tests. No package, release or deployment was published.

Evidence: `docs/development/evidence/github-actions/40606411532/` and `40606422085/`.
''' + MARKER

def api(path, body=None):
    argv = ['gh', 'api', 'repos/' + REPO + '/' + path]
    if body is not None:
        argv += ['-X', 'POST', '--input', '-']
    p = subprocess.run(argv, input=None if body is None else json.dumps(body), text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError('GitHub request failed; reconcile stored state before retrying any mutation')
    return json.loads(p.stdout)

records = []
for number in (149, 86, 3):
    before = api(f'issues/{number}')
    assert before['state'] == 'open' and 'pull_request' not in before
    comments = []
    page = 1
    while True:
        part = api(f'issues/{number}/comments?per_page=100&page={page}')
        comments += part
        if len(part) < 100:
            break
        page += 1
    existing = [c for c in comments if MARKER in c['body']]
    assert len(existing) <= 1
    (HERE / f'issue-{number}-before.json').write_text(json.dumps(before, indent=2) + '\n')
    (HERE / f'issue-{number}-comment-draft.md').write_text(BODY + '\n')
    comment = existing[0] if existing else api(f'issues/{number}/comments', {'body': BODY})
    (HERE / f'issue-{number}-comment-response.json').write_text(json.dumps(comment, indent=2) + '\n')
    readback = api(f'issues/comments/{comment["id"]}')
    after = api(f'issues/{number}')
    assert readback['body'] == BODY and after['state'] == 'open'
    for field in ('body', 'title', 'labels'):
        assert before[field] == after[field], field
    (HERE / f'issue-{number}-after.json').write_text(json.dumps(after, indent=2) + '\n')
    records.append({'issue': number, 'comment_url': readback['html_url'], 'state': after['state'], 'POST_invocations': 0 if existing else 1, 'body_title_labels_preserved': True})
(HERE / 'readback.json').write_text(json.dumps({'reviewed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'passed': True, 'records': records, 'new_closures': 0}, indent=2) + '\n')
print(json.dumps(records, indent=2))
