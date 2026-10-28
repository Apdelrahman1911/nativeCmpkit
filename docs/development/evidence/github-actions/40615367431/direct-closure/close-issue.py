"""Single comment/close after reviewed actual acceptance. Reconcile uncertainty read-only."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
B=Path(__file__).parent;R='Apdelrahman1911/nativeCmpkit';N=87
review=json.loads((B.parent/'important-result-review.json').read_text());assert review['passed'] and review['finding']=='NATIVE-032' and len(review['original_acceptance'])==3 and all(c['accepted'] for c in review['original_acceptance'])
assert review['whole_run_conclusion']=='success' and review['totals']['fresh_passed']==36 and review['totals']['reused_Android_executions']==16
marker='<!-- nativecmpkit:direct-acceptance:NATIVE-032:3b01b400 -->'
body='''## Verified fix — direct closure after important callback tests

All **three original NATIVE-032 acceptance criteria** pass at immutable **3b01b400864d5ceee2f542b7577b68c976df2d6a**, [run40615367431](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40615367431): **JS18/18 + Wasm18/18**,36 fresh executions/four XML, zero failures/errors/skips. Only calf-share browser jobs ran.

- Both actual share and clipboard Promise helpers record literal legacy **ShareResult.Success** then deliberately throw from the application callback. Each operation delivers exactly once; callback exceptions remain downstream errors, not invented platform failures. A subsequent request proves the owner gate was released first.
- Rejected Promises deliver one **Failed** result. Deliberately throwing failure callbacks still cannot redeliver or poison the owner; subsequent fulfilled requests succeed. Ordinary rejected clipboard, AbortError dismissal, unsupported payload and synchronous platform-error regressions also pass.
- Android's actual **ActivityNotFoundException** and throwing callback methods pass in [run40414284598](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40414284598) at6eb7c66e. These **16/16 Android-host executions are reused, not new tests**: all16 relevant Android/common/core/catalog inputs and exact own-Git blobs match this revision.

Root repair: Android obtains the platform outcome inside its platform-error boundary and calls the application afterward. JS/Wasm use **then(fulfilled,rejected)** rather than callback-catching trailing catch. Browser ownership releases its token before application notification. Existing public APIs/packages and legacy result adapters remain.

Review verifies742 exact source inputs, before/after maps, every fresh XML/artifact digest, all18 browser method identities on both targets and actual command/Chrome/runtime correspondence. Required tests → source/results review → **close directly now** → archive/index afterward.

Scope: real browser Promise jobs and production interop/owners with controlled navigator functions; actual Android code under Robolectric. Not OS clipboard/share permission, transient-user-activation, chooser/recipient/device, other browser engines, native sanitizers, ABI, dependency/legal/full consumers or release certification. Those unrelated gates remain open. No packages/releases/deployments published.

Evidence: `docs/development/evidence/github-actions/40615367431/`. Original issue body/title/labels and earlier failed reports preserved.

<!-- nativecmpkit:direct-acceptance:NATIVE-032:3b01b400 -->'''
def api(path,step,method='GET',payload=None):
 target=B/(step+'.json');assert not target.exists()
 p=subprocess.run(['gh','api','repos/'+R+'/'+path,'--method',method]+([] if payload is None else ['--input','-']),input=None if payload is None else json.dumps(payload).encode(),capture_output=True,timeout=90);target.write_bytes(p.stdout)
 assert p.returncode==0,'Uncertain API result: inspect saved response, reconcile read-only; never automatically repeat mutation'
 return json.loads(p.stdout)
before=api(f'issues/{N}','issue-before');assert before['state']=='open' and 'NATIVE-032' in before['title'] and 'pull_request' not in before
for c in review['original_acceptance']:assert c['criterion'] in before['body']
comments=api(f'issues/{N}/comments?per_page=100','comments-before');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
(B/'comment.md').write_text(body+'\n');c=api(f'issues/{N}/comments','comment-response','POST',{'body':body});read=api(f'issues/comments/{c["id"]}','comment-readback');assert read['body']==body
api(f'issues/{N}','close-response','PATCH',{'state':'closed','state_reason':'completed'})
after=api(f'issues/{N}','issue-after');assert after['state']=='closed' and after['state_reason']=='completed' and after['closed_at']
for field in ('title','body','labels'):assert before[field]==after[field],field
closed=api('issues?state=closed&sort=updated&direction=desc&per_page=100','closed-list');assert len(closed)<100
listed=[i for i in closed if 'pull_request' not in i]
result={'verified_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'issue':N,'finding':'NATIVE-032','state':'closed','state_reason':'completed','issue_url':after['html_url'],'comment_url':read['html_url'],'original_body_title_labels_preserved':True,'important_review_sha256':hashlib.sha256((B.parent/'important-result-review.json').read_bytes()).hexdigest(),'original_criteria_accepted':3,'POST_invocations':1,'PATCH_invocations':1,'direct_closure_before_repo_documentation':True,'new_issue_in_closed_collection':any(i['number']==N for i in listed),'closed_collection_count':len(listed),'repeated_mutations':0,'new_closures':1,'source_revision':review['source_revision'],'run_id':review['run_id'],'packages_releases_deployments_published':False}
if result['new_issue_in_closed_collection']:result['total_closed_issues']=len(listed)
(B/'closure-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
