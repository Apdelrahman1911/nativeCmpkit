from pathlib import Path
import json,subprocess,datetime,hashlib
B=Path(__file__).parent;R='Apdelrahman1911/nativeCmpkit';N=61
review=json.loads((B.parent/'important-result-review.json').read_text());assert review['passed'] and review['finding']=='IO-026' and len(review['original_acceptance'])==6 and all(c['accepted'] for c in review['original_acceptance'])
marker='<!-- nativecmpkit:direct-acceptance:IO-026:63f377f6 -->'
body='''## Verified fix — direct closure after important-test review

All **six original IO-026 acceptance criteria** pass at immutable **63f377f678fa3d4f0e4def26099fb5e0a6c3247a**, [run40609563741](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40609563741): **JS22/22 + Wasm22/22**, 44 fresh target executions of22 authored methods, ten XML, zero failures/errors/skips. Five new public-Compose methods per target supplement all existing session tests.

1. Application success callback throws: cleanup happens first; no cancellation/second result.
2. Cancellation callback throws: input and both listeners still removed exactly once.
3. Actual public launcher composition disposal **and removal from a still-live composition** remove the input; captured late handlers and a retained launcher cannot deliver/reopen.
4. Two public launch attempts report one explicit overlap error and keep the first session usable; a new launch succeeds after completion.
5. Normal cancel delivers one empty result after cleanup; two fresh inputs reselect the **same actual File through real DataTransfer/FileLists**, both delivering it once.
6. Identical source/case sets pass on actual JS and Wasm runtime implementations, both delegating to the reviewed shared owner.

Root repair separates FileList conversion from application callback delivery, uses an exactly-once terminal session, and owns DOM/listeners through the production DisposableEffect. Existing public overloads and namespaces retained. Independent review checks **all741 exact own-Git input blobs**, before/after maps, artifact/every XML hash, fresh commands/test identities and actual Chrome155/SDK/runtime correspondence. No unrelated IO/full-browser suite replay.

**Scope:** real Compose composition/disposal and real DOM/FileList/events; only native OS chooser opening is intercepted. This does **not** certify native chooser UI/user activation/automatic OS cancel-event support, Safari/Firefox, minimum/physical platforms, sanitizers, ABI, dependency/legal/full-consumer or release readiness. Those wider gates remain open, not requirements silently waived for this source/lifecycle finding.

Required tests → source/results review → **close directly now** → repository evidence/index update afterward, per the owner's instruction. Original issue body/title/labels and failed historical reports preserved.

Evidence: `docs/development/evidence/github-actions/40609563741/`.
''' + marker

def api(path,step,method='GET',payload=None):
 target=B/(step+'.json');assert not target.exists()
 p=subprocess.run(['gh','api','repos/'+R+'/'+path,'--method',method]+([] if payload is None else ['--input','-']),input=None if payload is None else json.dumps(payload).encode(),capture_output=True,timeout=90);target.write_bytes(p.stdout)
 if p.returncode:
  raise RuntimeError('Uncertain request result: inspect stored response and reconcile read-only before any repeat mutation')
 return json.loads(p.stdout)
before=api(f'issues/{N}','issue-before');assert before['state']=='open' and 'IO-026' in before['title'] and 'pull_request' not in before
comments=api(f'issues/{N}/comments?per_page=100','comments-before');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
(B/'comment.md').write_text(body+'\n')
c=api(f'issues/{N}/comments','comment-response','POST',{'body':body});read=api(f'issues/comments/{c["id"]}','comment-readback');assert read['body']==body
api(f'issues/{N}','close-response','PATCH',{'state':'closed','state_reason':'completed'})
after=api(f'issues/{N}','issue-after');assert after['state']=='closed' and after['state_reason']=='completed' and after['closed_at']
for field in ('title','body','labels'):assert before[field]==after[field],field
closed=api('issues?state=closed&per_page=100','closed-list');assert len(closed)<100;count=len([i for i in closed if 'pull_request' not in i]);assert any(i['number']==N for i in closed)
result={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'issue':N,'finding':'IO-026','state':'closed','state_reason':'completed','issue_url':after['html_url'],'comment_url':read['html_url'],'original_body_title_labels_preserved':True,'important_review_sha256':hashlib.sha256((B.parent/'important-result-review.json').read_bytes()).hexdigest(),'original_criteria_accepted':6,'POST_invocations':1,'PATCH_invocations':1,'direct_closure_before_repo_documentation':True,'total_closed_issues':count,'new_closures':1,'source_revision':review['source_revision'],'run_id':review['run_id'],'packages_releases_deployments_published':False}
(B/'closure-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
