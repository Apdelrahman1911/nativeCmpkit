"""One failed-job-only rerun at exact immutable SHA; no settings or publication."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,time
ROOT=Path('/root/projects/nativeCmpKit'); BASE=Path(__file__).parent/'uikit-attempt2-request'
REPO='Apdelrahman1911/nativeCmpkit';RUN=40522929974;JOB=122255014242
SHA='202059090bbbf896d07d38a3441cf21c8888c63b';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5'
BASE.mkdir(mode=0o700)
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def get(path,name):
 with (BASE/name).open('xb') as output:
  r=subprocess.run(['gh','api','repos/'+REPO+'/'+path],cwd=ROOT,stdout=output,stderr=subprocess.PIPE,timeout=90)
 (BASE/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,'Readback failed, not automatic retry authority'
 return json.loads((BASE/name).read_bytes())
def save(name,obj):
 with (BASE/name).open('x') as f:json.dump(obj,f,sort_keys=True,indent=2);f.write('\n')
started=utc()
r=get('actions/runs/'+str(RUN),'run-before.json')
assert r['head_sha']==SHA and r['run_attempt']==1 and r['status']=='completed' and r['conclusion']=='failure' and r['repository']['full_name']==REPO
jobs=get('actions/runs/'+str(RUN)+'/jobs?per_page=100','jobs-before.json')['jobs']
assert [j['id'] for j in jobs if j['conclusion']=='failure']==[JOB]
assert next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
for status in ('in_progress','queued','waiting','pending','requested'):
 runs=get('actions/runs?status='+status+'&per_page=100',status+'-before.json')
 assert runs['total_count']==len(runs['workflow_runs'])==0,'Do not overlap unknown library workload'
assert get('branches/main','main-before.json')['commit']['sha']==MAIN
assert get('actions/permissions','actions-permissions.json')=={'enabled':True,'allowed_actions':'all','sha_pinning_required':False}
assert get('actions/permissions/workflow','workflow-permissions.json')['default_workflow_permissions']=='read'
assert get('pages','pages-before.json')['status'] is None and get('releases?per_page=100','releases-before.json')==[]
workflow=subprocess.check_output(['git','show',SHA+':.github/workflows/gradle.yml'],cwd=ROOT)
assert b'permissions:\n  contents: read' in workflow and b'persist-credentials: false' in workflow
save('preflight.json',{'passed':True,'run':RUN,'failed_job':JOB,'source_revision':SHA,'workflow_sha256':hashlib.sha256(workflow).hexdigest(),'no_successful_jobs_requested_again':True,'source_clean_deadline_checks_unchanged':True,'local_dirty_cache_repair_not_used_by_immutable_rerun':True})
save('payload.json',{'enable_debug_logging':False});request_start=utc()
try:
 with (BASE/'request.stdout').open('xb') as output:
  result=subprocess.run(['gh','api','repos/'+REPO+'/actions/jobs/'+str(JOB)+'/rerun','--method','POST','--input',str(BASE/'payload.json')],cwd=ROOT,stdout=output,stderr=subprocess.PIPE,timeout=90)
 (BASE/'request.stderr').write_bytes(result.stderr);exit_code=result.returncode
except subprocess.TimeoutExpired as error:
 (BASE/'request.stderr').write_bytes(error.stderr or b'');exit_code=None
save('request.json',{'endpoint':'repos/'+REPO+'/actions/jobs/'+str(JOB)+'/rerun','method':'POST','invocations':1,'exit_code':exit_code,'started_utc':request_start,'finished_utc':utc(),'automatic_retry':False})
found=None
for i in range(8):
 r=get('actions/runs/'+str(RUN),'run-after-'+str(i)+'.json')
 assert r['head_sha']==SHA and r['repository']['full_name']==REPO
 if r['run_attempt']==2:found=r;break
 assert r['run_attempt']==1
 time.sleep(8)
assert found is not None,'Uncertain POST, reconcile manually before any repeat request'
get('actions/runs/'+str(RUN)+'/jobs?per_page=100','jobs-after.json')
assert get('branches/main','main-after.json')['commit']['sha']==MAIN
save('receipt.json',{'passed':True,'started_utc':started,'finished_utc':utc(),'source_revision':SHA,'run_id':RUN,'run_attempt':2,'url':found['html_url'],'status':found['status'],'conclusion':found['conclusion'],'POST_invocations':1,'request_exit':exit_code,'successful_tooling_reused_not_repeated':True,'settings_mutated':False,'packages_releases_deployments_Pages_or_issue_mutations':False,'release_success_certified':False,'scope':'One failed UIKit job only, at unchanged immutable202059 SHA, after zero-library-test Git-status timeout and preceding simulator migration-error output. Root cause not established; no timeout/clean-check weakening. Acceptance/readback is not runtime success.'})
print(json.dumps({'passed':True,'run':RUN,'attempt':2,'status':found['status'],'receipt':str(BASE/'receipt.json')},indent=2),flush=True)
