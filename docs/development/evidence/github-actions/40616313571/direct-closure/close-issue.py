"""Single comment/close after reviewed actual acceptance. Reconcile uncertainty read-only."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
B=Path(__file__).parent;R='Apdelrahman1911/nativeCmpkit';N=95
review=json.loads((B.parent/'important-result-review.json').read_text());assert review['passed'] and review['finding']=='NAV-007' and len(review['original_acceptance'])==3 and all(c['accepted'] for c in review['original_acceptance'])
assert review['whole_run_conclusion']=='success' and review['totals']['passed']==59 and review['actual_host_methods']==16
marker='<!-- nativecmpkit:direct-acceptance:NAV-007:c0f5cafc -->'
body='''## Verified fix — direct closure after important host/restoration tests

All **three original NAV-007 acceptance criteria** pass at immutable **c0f5cafcec1c53b10f93897533c3c3875afd8282**, [run40616313571](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40616313571): **59/59 actual desktop library methods**, seven fresh XML, zero failures/errors/skips. All16 real Compose-host methods run; four new regressions address the missing original requirements. Only calf-navigation ran.

1. Duplicate public host registrations throw the exact deterministic **Duplicate navigation route 'home'** diagnostic, rather than silently selecting the first content; no stack is initialized.
2. An unknown public start route fails before initialization. A genuine **public controller Saver + serialization round-trip** containing an app-removed route fails explicitly against the new graph and preserves every saved entry ID. Later unknown navigation against an attached valid graph rejects before changing its valid entry stack.
3. The documented **explicit application-selected, potentially lossy reset** is chosen before mounting the host. A distinct controller/new entry renders fresh home state, remains visible after a rejected unknown navigation and supports normal detail/back saved-state restoration. The old restored controller is not silently edited. Business data must be migrated independently and the selected controller persisted by the application; this is not automatic lossless library recovery.

Root repair: the graph builder rejects duplicate/blank routes; the public host validates start and all stacked/restored routes before rendering; attached controller navigation validates before stack mutation. Existing public package/factory/controller methods and legacy back-stack getter remain. Fail-fast errors are an intentional observable correction, documented with upgrade instructions in `docs/development/navigation-unknown-routes.md`/ADR0004.

Review verifies742 exact own-Git inputs, before/after maps, all59 authored testcase identities, XML/artifact hashes, actual Xvfb/JVM command and runtime/SDK correspondence. Required tests → source/results review → **direct closure now** → archive/index afterward. No unrelated browser/native/device/consumer suites replayed.

Scope: real public Compose host and saver on Linux/JVM. Not Android process recreation, UIKit gestures, browser history, business-data migration, native sanitizers, minimum devices, dependency/legal/full consumers/API-ABI or release certification. Those wider gates remain open. No packages/releases/deployments published.

Evidence: `docs/development/evidence/github-actions/40616313571/`. Original issue body/title/labels and earlier failures preserved.

<!-- nativecmpkit:direct-acceptance:NAV-007:c0f5cafc -->'''
def api(path,step,method='GET',payload=None):
 target=B/(step+'.json');assert not target.exists()
 p=subprocess.run(['gh','api','repos/'+R+'/'+path,'--method',method]+([] if payload is None else ['--input','-']),input=None if payload is None else json.dumps(payload).encode(),capture_output=True,timeout=90);target.write_bytes(p.stdout)
 assert p.returncode==0,'Uncertain API result: inspect saved response, reconcile read-only; never automatically repeat mutation'
 return json.loads(p.stdout)
before=api(f'issues/{N}','issue-before');assert before['state']=='open' and 'NAV-007' in before['title'] and 'pull_request' not in before
for c in review['original_acceptance']:assert c['criterion'] in before['body']
comments=api(f'issues/{N}/comments?per_page=100','comments-before');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
(B/'comment.md').write_text(body+'\n');c=api(f'issues/{N}/comments','comment-response','POST',{'body':body});read=api(f'issues/comments/{c["id"]}','comment-readback');assert read['body']==body
api(f'issues/{N}','close-response','PATCH',{'state':'closed','state_reason':'completed'})
after=api(f'issues/{N}','issue-after');assert after['state']=='closed' and after['state_reason']=='completed' and after['closed_at']
for field in ('title','body','labels'):assert before[field]==after[field],field
closed=api('issues?state=closed&sort=updated&direction=desc&per_page=100','closed-list');assert len(closed)<100
listed=[i for i in closed if 'pull_request' not in i]
result={'verified_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'issue':N,'finding':'NAV-007','state':'closed','state_reason':'completed','issue_url':after['html_url'],'comment_url':read['html_url'],'original_body_title_labels_preserved':True,'important_review_sha256':hashlib.sha256((B.parent/'important-result-review.json').read_bytes()).hexdigest(),'original_criteria_accepted':3,'POST_invocations':1,'PATCH_invocations':1,'direct_closure_before_repo_documentation':True,'new_issue_in_closed_collection':any(i['number']==N for i in listed),'closed_collection_count':len(listed),'repeated_mutations':0,'new_closures':1,'source_revision':review['source_revision'],'run_id':review['run_id'],'packages_releases_deployments_published':False}
if result['new_issue_in_closed_collection']:result['total_closed_issues']=len(listed)
(B/'closure-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
