"""Read-only reconciliation of initial collection omission; never repeats mutations."""
from pathlib import Path
import json,subprocess,datetime,hashlib
B=Path(__file__).parent;R='Apdelrahman1911/nativeCmpkit';N=61
review=json.loads((B.parent/'important-result-review.json').read_text());before=json.loads((B/'issue-before.json').read_text());old_after=json.loads((B/'issue-after.json').read_text());comment=json.loads((B/'comment-readback.json').read_text());initial=json.loads((B/'closed-list.json').read_text())
assert old_after['state']=='closed' and old_after['state_reason']=='completed' and not any(i['number']==N for i in initial)
def get(path,name):
 p=subprocess.run(['gh','api','repos/'+R+'/'+path,'-H','Cache-Control: no-cache'],capture_output=True,timeout=90);(B/name).write_bytes(p.stdout);assert p.returncode==0;return json.loads(p.stdout)
after=get(f'issues/{N}','issue-fresh-readback.json');closed=get('issues?state=closed&per_page=100&sort=updated&direction=desc','closed-fresh-readback.json');assert len(closed)<100 and any(i['number']==N and i['state']=='closed' for i in closed)
assert after['state']=='closed' and after['state_reason']=='completed'
for k in ('body','title','labels'):assert before[k]==after[k]
count=len([i for i in closed if 'pull_request' not in i])
result={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'issue':N,'finding':'IO-026','state':'closed','state_reason':'completed','issue_url':after['html_url'],'comment_url':comment['html_url'],'original_body_title_labels_preserved':True,'important_review_sha256':hashlib.sha256((B.parent/'important-result-review.json').read_bytes()).hexdigest(),'original_criteria_accepted':6,'POST_invocations':1,'PATCH_invocations':1,'direct_closure_before_repo_documentation':True,'initial_confirmation_script_exit':1,'initial_collection_omitted_issue_despite_exact_closed_readback':True,'initial_collection_cause':'Unknown; fresh different-order read-only query confirms issue and total. Initial response/assertion retained.','repeated_mutations':0,'total_closed_issues':count,'new_closures':1,'source_revision':review['source_revision'],'run_id':review['run_id'],'packages_releases_deployments_published':False}
(B/'closure-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
