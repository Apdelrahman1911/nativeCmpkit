from pathlib import Path
import datetime as dt, hashlib, json, subprocess, sys
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'docs/development/evidence/issue-progress-d849515b'; REPO='Apdelrahman1911/nativeCmpkit'
sys.path.insert(0,str(ROOT/'scripts/migration'));from github_json import json_pages
assert not OUT.exists();OUT.mkdir(parents=True)
SHA='d849515b2a1f6048ed280e44e677f532a57d4f5f';BASE=f'https://github.com/{REPO}/blob/{SHA}/docs/development/'
rows=[
(40,'ci-policy',f'''Contained development checkpoint at `{SHA}` (single-agent).

- Owner policy is reflected in AGENTS.md/ADR0005/executable checks: Actions enabled, all actions allowed, no mandatory SHA pinning; verification tokens remain read-only with checkout credentials disabled. Publishing/Pages remain gated.
- Held-source preflight: 801 Python tooling methods (121 CI methods), strict MkDocs and actionlint pass. These are not native or packaged-consumer tests.
- Previous immutable CI: core831 passes; macOS426 passes including real AppKit cancellation. iPhone332pass/16fail and WebView0 after compile failure; Windows421pass/1fail plus four unexpected filesystem-policy skips. All failures preserved.
- New owned API35 instrumentation is running as [40422019219](https://github.com/{REPO}/actions/runs/40422019219); no result is claimed yet. Its setup, actual test outcomes, identity/security and teardown are separate gates.

[Checkpoint/evidence]({BASE}checkpoint-ci-20261026.md). Dependency trust, legal/native provenance, ABI and packaged-consumer requirements remain open; no issue closure or release authorization is inferred.'''),
(55,'openable-metadata',f'''Provider metadata follow-up at `{SHA}`; also relevant to #47.

`calf-io/src/androidMain/.../KmpFile.android.kt:isDirectory` no longer sends DocumentsProvider-only MIME projections to ordinary openable providers: it uses `ContentResolver.getType`, preserving document/tree handling. New `OpenableProviderMetadataTest` exercises size/name/MIME, explicit directory MIME, nullable type and denied-type/readable-size independence.

Actual local Robolectric red24:21pass/3fail, green24/24, with held source and XML archived: [red]({BASE}evidence/openable-metadata-red-001/archive.json), [green]({BASE}evidence/openable-metadata-green-001/archive.json). This is host execution, **not proof** the original Android-device004 provider/null-size failure is fixed. API35 instrumented verification [40422019219](https://github.com/{REPO}/actions/runs/40422019219) has no reviewed result yet. Cloud/ExternalStorage/Downloads, restart/grant and other original acceptance requirements remain open.'''),
(37,'uikit-host',f'''Native test coverage checkpoint at `{SHA}`; no native issue is closed.

The preserved iPhone/iOS26.5 run executes348 tests:332pass/16fail. Seven presenter/interop tests fail before their operation because the exact Compose1.12 `runComposeUiTest.v2` uses a Skiko CanvasLayersComposeScene, not a UIKit application/controller host. Additional target/action and MIME failures remain under investigation. No fabricated LocalUIViewController, blanket skip, or sample substitute is introduced.

This commit fixes the source-confirmed unsupported lens shape crash and a single-date programmatic month-navigation regression; color test synchronization, native UIView identity and Unicode normalization fixtures are repaired without relaxing outcome assertions. All repaired Apple runtime checks are still pending a genuine library-level UIApplication/ComposeUIViewController host and simulator execution.

[Original failures and diagnosis]({BASE}checkpoint-ci-20261026.md). Full UIKit lifecycle/native outcome, iPad/minimum-iOS and accessibility acceptance remain open.'''),
(157,'displayed-month',f'''Programmatic selection/month ownership repair at `{SHA}`.

The preserved simulator failure is **after** selecting March16 while April is displayed (`NativeDateControlsTest`, line55), not initial April creation. `CalendarViewHost.preservingVisibleMonth` captures the actual native visible month, suppresses transient owner-navigation reports, and restores it around nonanimated `CalendarDatePickerBackend.setSelectedDate`. Regression assertions retain selection/null and no-spurious-month-callback requirements.

[Checkpoint]({BASE}checkpoint-ci-20261026.md). The repaired native regression has **not yet executed**; this source change does not close the issue. Legacy save/restore and compact/wheels/inline acceptance stay required.'''),
(149,'windows-cache',f'''Windows/security verification gap recorded at `{SHA}`.

[Run40417671294](https://github.com/{REPO}/actions/runs/40417671294) failed:421pass/1fail, plus one eligible AppKit N/A and **four unexpected POSIX/symlink policy skips** in picker/share caches. The unrelated Unix-only absolute-path fixture is repaired using the actual host temporary directory; Windows rerun is pending.

The skipped filesystem security cases are not counted as passes or broadened N/A. Next work is actual Windows ACL/reparse/symlink equivalents and underlying owner/private-cache enforcement, including concurrent extraction and external-file preservation. [Preserved evidence]({BASE}evidence/github-actions/40417671294/lead-independent-review.json). JNI ABI diagnostics passed on that one host, but loaded-DLL reuse, complete native payload/permission matrix and all original security acceptance remain open.'''),
(70,'apple-cookie-compile',f'''Apple compilation blocker repair at `{SHA}`.

The previous iPhone run fails production compilation at `CookieManager.ios.kt` because the native callback supplies a nullable cookie list; WebView executes **zero tests**. `cookies.orEmpty().filterIsInstance<NSHTTPCookie>()` repairs that nullable-list source error while keeping the native store and request matching logic.

Repaired Apple compilation/runtime cookie checks have not run. [Preserved run/limitations]({BASE}checkpoint-ci-20261026.md). Native HTTP request-header comparison, secure/host-only/path/expiry/duplicate-name cases remain acceptance gates; no issue closure or runtime success is claimed.''')]
receipts=[]
def call(args):
    r=subprocess.run(['gh','api',*args],cwd=ROOT,capture_output=True,timeout=90)
    if r.returncode:raise RuntimeError('GitHub response failed or uncertain; reconcile before retry')
    return r.stdout
for number,key,text in rows:
    marker=f'<!-- nativecmpkit-progress:{SHA[:8]}:{key} -->';body=marker+'\n\n'+text+'\n'
    before=json.loads(call(['--method','GET',f'repos/{REPO}/issues/{number}']))
    assert 'pull_request' not in before and before['state']=='open'
    raw=call(['--method','GET',f'repos/{REPO}/issues/{number}/comments?per_page=100','--paginate'])
    existing=[c for page in json_pages(raw.decode()) for c in page if marker in c['body']]
    assert len(existing)<=1
    request={'body':body};p=OUT/f'{number}-request.json';p.write_text(json.dumps(request,indent=2)+'\n')
    if existing:
        comment=existing[0];assert comment['body']==body
    else:comment=json.loads(call(['--method','POST',f'repos/{REPO}/issues/{number}/comments','--input',str(p)]))
    reread=json.loads(call(['--method','GET',f'repos/{REPO}/issues/comments/{comment["id"]}']))
    assert reread['body']==body
    after=json.loads(call(['--method','GET',f'repos/{REPO}/issues/{number}']))
    assert before['body']==after['body'] and before['state']==after['state'] and before['labels']==after['labels']
    receipts.append({'issue':number,'marker':marker,'comment_id':reread['id'],'comment_url':reread['html_url'],'body_sha256':hashlib.sha256(body.encode()).hexdigest(),'original_issue_body_sha256':hashlib.sha256(before['body'].encode()).hexdigest(),'original_body_state_labels_unchanged':True,'created_or_reused':'reused' if existing else 'created','readback_verified':True})
    (OUT/'progress-receipts.json').write_text(json.dumps({'observed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':SHA,'completed_comments':receipts,'issues_closed':0,'publication_performed':False},indent=2,sort_keys=True)+'\n')
(OUT/'collector.py').write_bytes(Path(__file__).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'comments_readback_verified':len(receipts),'issues_closed':0},indent=2))
