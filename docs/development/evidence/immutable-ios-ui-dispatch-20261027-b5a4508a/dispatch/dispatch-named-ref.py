"""Preserve rejected SHA-form dispatch; dispatch frozen named ref and check actual SHA."""
from pathlib import Path
import base64,datetime as dt,hashlib,json,subprocess,time
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).resolve().parent;REPO='Apdelrahman1911/nativeCmpkit'
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip();assert sha=='b5a4508a8d28f9937c456db2895b4ae09c4a9343'
now=lambda:dt.datetime.now(dt.timezone.utc).isoformat()
(O/'sha-dispatch-rejection-observation.json').write_text(json.dumps({'recorded_utc':now(),'observation_source':'Original exec session53060 tool output; response was not separately logged at execution','command':['gh','api','-X','POST','repos/'+REPO+'/actions/workflows/gradle.yml/dispatches','-f','ref='+sha,'-f','inputs[profile]=ios-ui'],'exit_code':1,'HTTP_status':422,'message':'No ref found for: '+sha,'push_succeeded_and_read_back_before_rejection':True,'dispatch_succeeded':False,'followup':'REST dispatch requires a named branch/tag ref. Freeze development and confirm captured run head_sha exactly; do not invent an accepted SHA-form request.'},indent=2)+'\n')
def get(path,name):
 b=subprocess.check_output(['gh','api',path],cwd=R,timeout=90);(O/(name+'.json')).write_bytes(b);return json.loads(b)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=R)
assert get('repos/'+REPO+'/git/ref/heads/development/preview-hardening','named-ref-before')['object']['sha']==sha
assert get('repos/'+REPO+'/git/ref/heads/main','main-before-named-dispatch')['object']['sha']=='94d2492e99d5cbc060409d94d9f88febd06222d5'
w=get('repos/'+REPO+'/contents/.github/workflows/gradle.yml?ref='+sha,'immutable-workflow');assert base64.b64decode(w['content'])==(R/'.github/workflows/gradle.yml').read_bytes()
prior=get('repos/'+REPO+'/actions/workflows/gradle.yml/runs?per_page=20','runs-before-named-dispatch');assert not any(x['head_sha']==sha for x in prior['workflow_runs'])
assert all(x['status']=='completed' for x in prior['workflow_runs'])
start=now();cmd=['gh','api','-X','POST','repos/'+REPO+'/actions/workflows/gradle.yml/dispatches','-f','ref=development/preview-hardening','-f','inputs[profile]=ios-ui']
r=subprocess.run(cmd,cwd=R,capture_output=True,timeout=90);(O/'named-dispatch.stdout').write_bytes(r.stdout);(O/'named-dispatch.stderr').write_bytes(r.stderr)
(O/'named-dispatch-result.json').write_text(json.dumps({'started_utc':start,'finished_utc':now(),'command':cmd,'exit_code':r.returncode,'expected_immutable_source_revision':sha,'requests_including_rejected_SHA_form':2,'profile':'ios-ui','no_release_package_deployment_requested':True},indent=2)+'\n')
assert r.returncode==0,(r.returncode,r.stderr.decode())
found=[]
for i in range(12):
 runs=get('repos/'+REPO+'/actions/workflows/gradle.yml/runs?per_page=20','runs-after-named-dispatch-'+str(i))
 found=[x for x in runs['workflow_runs'] if x['head_sha']==sha and x['event']=='workflow_dispatch' and x['id'] not in {v['id'] for v in prior['workflow_runs']}]
 if found:break
 time.sleep(5)
assert len(found)==1,[(v['id'],v['head_sha']) for v in found]
run=found[0];assert run['head_branch']=='development/preview-hardening' and run['run_attempt']==1
assert get('repos/'+REPO+'/git/ref/heads/development/preview-hardening','named-ref-after')['object']['sha']==sha
(O/'run-readback.json').write_text(json.dumps({'recorded_utc':now(),'run_id':run['id'],'run_url':run['html_url'],'run_attempt':run['run_attempt'],'source_revision':run['head_sha'],'head_branch':run['head_branch'],'status_at_observation':run['status'],'conclusion_at_observation':run['conclusion'],'profile_requested':'ios-ui','immutable_SHA_capture_verified':True,'publishing_release_deployment_requested':False,'scope':'Only targeted UIKit application module; run is queued/running evidence, not passing native tests or a release gate.'},indent=2)+'\n')
print(json.dumps({'run_id':run['id'],'url':run['html_url'],'head_sha':run['head_sha'],'status':run['status'],'conclusion':run['conclusion']}))
