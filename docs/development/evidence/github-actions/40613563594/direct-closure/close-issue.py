from pathlib import Path
import json,subprocess,datetime,hashlib,time
B=Path(__file__).parent;R='Apdelrahman1911/nativeCmpkit';N=65
review=json.loads((B.parent/'important-result-review.json').read_text());assert review['passed'] and review['finding']=='NATIVE-006' and len(review['original_acceptance'])==3 and all(c['accepted'] for c in review['original_acceptance'])
marker='<!-- nativecmpkit:direct-acceptance:NATIVE-006:b7ba5c80 -->'
body="## Verified fix — direct closure after important public-component tests\n\nAll **three original NATIVE-006 acceptance criteria** pass at immutable **b7ba5c802ee8c8a58e813d19b5a242770aac9675**, [run40613563594](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40613563594): **JS33/33 + Wasm33/33**,66 fresh executions/14 XML, zero failures/errors/skips. Three new public Compose/DOM methods supplement all30 existing methods on each target.\n\n1. Mount/remove/remount the **actual public WebView inside real ComposeViewport/canvas/HTML interop**. Full window disposal and removal from a still-live composition deliver exactly one onDispose per created view; repeated fixture close does not repeat it.\n2. Retained state clears both old iframe and owner. Native DOM removal is observed through isConnected; remount uses a distinct node and owner, not a stale remembered instance.\n3. Both old native event dispatches and the **original captured load/error callback objects** are delivered after removal and replacement. The callback delivery counter proves they actually ran; replacement owner/node/loading/title/final URL/errors remain untouched. Original listener identities are removed natively.\n\nOwning source binds teardown to DisposableEffect, removes both listener objects, clears only matching state and guards late callbacks with disposed/current-frame identity. Public APIs and packages remain. Test code uses the real Compose dependency's internal window handle **only to release its own viewport**; no copied renderer or no-op/fake UI applier. Controlled trusted fixture HTML enables genuine DOM readiness, not a security-policy bypass in production.\n\nSource/results review checks **all742 exact own-Git inputs**, before/after maps, every XML/artifact hash, all33 authored identities on both targets, command and Chrome155/SDK/runtime correspondence. Required tests → review → **direct closure now** → repository archive/index afterward. No unrelated IO/other modules/native-host replay.\n\nScope: actual Chrome JS/Wasm public-component lifecycle and native DOM/listeners. This does **not** certify Firefox/Safari, GC/native-memory profiling, other WebView/network/sandbox/cookie issues, physical/minimum/native sanitizers, ABI, dependency/legal/full consumers or release readiness. Wider gates stay open. No packages/releases/deployments published.\n\nEvidence: `docs/development/evidence/github-actions/40613563594/`. Original issue body/title/labels and previous failed reports preserved.\n\n<!-- nativecmpkit:direct-acceptance:NATIVE-006:b7ba5c80 -->"

def api(path,step,method='GET',payload=None):
 target=B/(step+'.json');assert not target.exists()
 p=subprocess.run(['gh','api','repos/'+R+'/'+path,'--method',method]+([] if payload is None else ['--input','-']),input=None if payload is None else json.dumps(payload).encode(),capture_output=True,timeout=90);target.write_bytes(p.stdout)
 if p.returncode:
  raise RuntimeError('Uncertain request result: inspect stored response and reconcile read-only before any repeat mutation')
 return json.loads(p.stdout)
before=api(f'issues/{N}','issue-before');assert before['state']=='open' and 'NATIVE-006' in before['title'] and 'pull_request' not in before
comments=api(f'issues/{N}/comments?per_page=100','comments-before');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
(B/'comment.md').write_text(body+'\n')
c=api(f'issues/{N}/comments','comment-response','POST',{'body':body});read=api(f'issues/comments/{c["id"]}','comment-readback');assert read['body']==body
api(f'issues/{N}','close-response','PATCH',{'state':'closed','state_reason':'completed'})
after=api(f'issues/{N}','issue-after');assert after['state']=='closed' and after['state_reason']=='completed' and after['closed_at']
for field in ('title','body','labels'):assert before[field]==after[field],field
closed=api('issues?state=closed&sort=updated&direction=asc&per_page=100','closed-list');assert len(closed)<100
initial_omission=not any(i['number']==N for i in closed)
if initial_omission:
 time.sleep(2)
 closed=api('issues?state=closed&sort=created&direction=desc&per_page=100','closed-fresh-readback');assert len(closed)<100
assert any(i['number']==N for i in closed)
count=len([i for i in closed if 'pull_request' not in i]);assert count==28
result={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'issue':N,'finding':'NATIVE-006','state':'closed','state_reason':'completed','issue_url':after['html_url'],'comment_url':read['html_url'],'original_body_title_labels_preserved':True,'important_review_sha256':hashlib.sha256((B.parent/'important-result-review.json').read_bytes()).hexdigest(),'original_criteria_accepted':3,'POST_invocations':1,'PATCH_invocations':1,'direct_closure_before_repo_documentation':True,'initial_collection_omitted_issue':initial_omission,'repeated_mutations':0,'total_closed_issues':count,'new_closures':1,'source_revision':review['source_revision'],'run_id':review['run_id'],'packages_releases_deployments_published':False}
(B/'closure-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
