"""Single comment/close after reviewed actual acceptance. Reconcile uncertainty read-only."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
B=Path(__file__).parent;R='Apdelrahman1911/nativeCmpkit';N=12
review=json.loads((B.parent/'important-result-review.json').read_text());assert review['passed'] and review['finding']=='NATIVE-013' and len(review['original_acceptance'])==3 and all(c['accepted'] for c in review['original_acceptance'])
assert review['source_revision']=='857088dd3de21258f65d2ba3f6a7dee62ad5540c' and review['run_id']==40619253986
assert review['whole_run_conclusion']=='success' and review['totals']['passed']==43 and review['actual_new_cookie_methods']==3
marker='<!-- nativecmpkit:direct-acceptance:NATIVE-013:857088dd -->'
body='''## Verified fix — direct closure after important native-session tests

All **three original NATIVE-013 acceptance criteria** pass at immutable **857088dd3de21258f65d2ba3f6a7dee62ad5540c**, [run40619253986](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40619253986): **43/43 actual desktop WebView methods**, eight fresh XML, zero failures/errors/skips. Three new native-cookie integration methods supplement the existing40; all11 actual JavaFX methods run. Only calf-webview on Linux/Xvfb ran.

1. A **real production JavaFX owner/WebEngine** loads a loopback login endpoint that sets an HttpOnly session in the actual JavaFX native jar. Library **getCookies** preserves the session and global handler identity; a real followup HTTP endpoint requires that same authenticated cookie. Native request headers and actual **document.cookie** prove HttpOnly is sent to HTTP but hidden from JavaScript; Secure cookies are not sent over HTTP or exposed to insecure document.cookie.
2. An application custom **CookieHandler is installed before a new native view**. Creation, library reads, unsupported full-store deletion and disposal retain its exact identity and cookie value. Toolkit is bootstrapped first; this does not claim completely fresh-JVM dependency cold initialization.
3. **Two managers run on two distinct overlapping worker threads**, storing32 values into the actual shared native jar. Both API reads, actual native HTTP request headers and actual WebEngine document.cookie retain every value. Fixture-owned cookies are individually expired and verified gone; HTTP threads terminate. No application-global store is cleared.

Root repair: CookieManager adapts the existing JavaFX/application handler without ever installing a replacement. Explicit-handler ownership is opt-in and not global; shared handler operations are synchronized. Generic handler metadata/full-store deletion limitations produce explicit unsupported behavior rather than fabricated capabilities. Existing public packages/constructor/API remain.

Review verifies743 exact own-Git inputs, before/after maps, all43 authored testcase identities, every XML/artifact hash, actual command and runtime/SDK correspondence. Required tests → source/results review → **direct closure now** → archive/index afterward. Original upstream #425 reference/body/title/labels remain intact.

Scope: actual JavaFX21/native jar/HTTP/document.cookie on Linux/Xvfb, controlled public loopback session rather than real-account/password login. Secure **HTTPS-URI cookie policy** is checked through the native handler, not an HTTPS-network/TLS certificate test. Other JavaFX/OS matrices, native sanitizers, minimum devices, dependency/legal/API-ABI/full consumers/security/release requirements remain open. No packages/releases/deployments published.

Evidence: `docs/development/evidence/github-actions/40619253986/`. Prior failed run40617556199 remains failed41/43; test-only HTML MIME correction keeps the10-second native title barriers, actual MIME assertion and every session/thread/cleanup assertion. No production change was needed for that fixture repair.

<!-- nativecmpkit:direct-acceptance:NATIVE-013:857088dd -->'''
def api(path,step,method='GET',payload=None):
 target=B/(step+'.json');assert not target.exists()
 p=subprocess.run(['gh','api','repos/'+R+'/'+path,'--method',method]+([] if payload is None else ['--input','-']),input=None if payload is None else json.dumps(payload).encode(),capture_output=True,timeout=90);target.write_bytes(p.stdout)
 assert p.returncode==0,'Uncertain API result: inspect saved response, reconcile read-only; never automatically repeat mutation'
 return json.loads(p.stdout)
before=api(f'issues/{N}','issue-before');assert before['state']=='open' and 'NATIVE-013' in before['title'] and 'pull_request' not in before
for c in review['original_acceptance']:assert c['criterion'] in before['body']
comments=api(f'issues/{N}/comments?per_page=100','comments-before');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
(B/'comment.md').write_text(body+'\n');c=api(f'issues/{N}/comments','comment-response','POST',{'body':body});read=api(f'issues/comments/{c["id"]}','comment-readback');assert read['body']==body
api(f'issues/{N}','close-response','PATCH',{'state':'closed','state_reason':'completed'})
after=api(f'issues/{N}','issue-after');assert after['state']=='closed' and after['state_reason']=='completed' and after['closed_at']
for field in ('title','body','labels'):assert before[field]==after[field],field
closed=api('issues?state=closed&sort=updated&direction=desc&per_page=100','closed-list');assert len(closed)<100
listed=[i for i in closed if 'pull_request' not in i]
result={'verified_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'issue':N,'finding':'NATIVE-013','state':'closed','state_reason':'completed','issue_url':after['html_url'],'comment_url':read['html_url'],'original_body_title_labels_preserved':True,'important_review_sha256':hashlib.sha256((B.parent/'important-result-review.json').read_bytes()).hexdigest(),'original_criteria_accepted':3,'POST_invocations':1,'PATCH_invocations':1,'direct_closure_before_repo_documentation':True,'new_issue_in_closed_collection':any(i['number']==N for i in listed),'closed_collection_count':len(listed),'repeated_mutations':0,'new_closures':1,'source_revision':review['source_revision'],'run_id':review['run_id'],'packages_releases_deployments_published':False}
if result['new_issue_in_closed_collection']:result['total_closed_issues']=len(listed)
(B/'closure-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
