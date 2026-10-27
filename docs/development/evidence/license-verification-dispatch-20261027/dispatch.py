"""One dispatch per explicit bounded verification profile; no publishing/deployment."""
from pathlib import Path
import datetime as dt,gzip,hashlib,json,subprocess,time
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent
REPO='Apdelrahman1911/nativeCmpkit';BRANCH='development/preview-hardening';REV='c9ffacde892cfecd3d2784b22dbad7731490c6fc';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5'
assert not (BASE/'receipt.json').exists()
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def get(path,label):
 command=['gh','api','repos/'+REPO+'/'+path,'-H','Cache-Control: no-cache']
 r=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=90)
 (BASE/(label+'.json.gz')).write_bytes(gzip.compress(r.stdout,mtime=0));(BASE/(label+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,(label,r.returncode)
 return json.loads(r.stdout)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==REV
assert subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()==''
assert get('branches/'+BRANCH,'development-before')['commit']['sha']==REV
assert get('branches/main','main-before')['commit']['sha']==MAIN
settings=get('actions/permissions','permissions-before');assert settings['enabled'] and settings['allowed_actions']=='all' and settings['sha_pinning_required'] is False
initial=get('actions/runs?event=workflow_dispatch&per_page=100','runs-before')
old={run['id'] for run in initial['workflow_runs']}
active=[{'id':run['id'],'revision':run['head_sha'],'status':run['status']} for run in initial['workflow_runs'] if run['status'] in ('queued','in_progress','requested','waiting','pending')]
assert not active,active
rows=[]
for profile in ('consumer-core-io','windows'):
 request=BASE/(profile+'-request.json');request.write_text(json.dumps({'ref':BRANCH,'inputs':{'profile':profile}},indent=2)+'\n')
 command=['gh','api','repos/'+REPO+'/actions/workflows/gradle.yml/dispatches','--method','POST','--input',str(request)]
 started=utc();tick=time.monotonic()
 result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=120)
 (BASE/(profile+'-dispatch.stdout')).write_bytes(result.stdout);(BASE/(profile+'-dispatch.stderr')).write_bytes(result.stderr)
 row={'profile':profile,'source_revision':REV,'request_started_utc':started,'request_finished_utc':utc(),'command':command,'exit_code':result.returncode,'invocations':1,'automatic_retry':False,'run_id':None,'request_sha256':hashlib.sha256(request.read_bytes()).hexdigest()}
 rows.append(row)
 (BASE/'receipt.json').write_text(json.dumps({'profiles':rows,'publication_or_deployment_performed':False,'scope':'Dispatch requests only; running/queued/failed is not a test pass.'},indent=2,sort_keys=True)+'\n')
 assert result.returncode==0,'Uncertain/failed request preserved; do not replay mutation'
 for attempt in range(10):
  current=get('actions/runs?event=workflow_dispatch&per_page=100',profile+'-runs-'+str(attempt))
  matches=[run for run in current['workflow_runs'] if run['id'] not in old and run['head_sha']==REV and run['head_branch']==BRANCH and run['event']=='workflow_dispatch']
  if len(matches)==1:
   run=matches[0];old.add(run['id']);row.update(run_id=run['id'],run_url=run['html_url'],observed_status=run['status'],observed_conclusion=run['conclusion']);break
  assert len(matches)<2,'Ambiguous runs; do not guess profile or replay request'
  time.sleep(5)
 assert row['run_id'] is not None,'Accepted dispatch not discovered; no replay'
 print(json.dumps(row,indent=2),flush=True)
assert get('branches/'+BRANCH,'development-after')['commit']['sha']==REV
assert get('branches/main','main-after')['commit']['sha']==MAIN
receipt={'request_execution_successful':True,'recorded_utc':utc(),'source_revision':REV,'main_preserved':MAIN,'repository':REPO,'profiles':rows,'total_POST_invocations':2,'no_mutation_replayed':True,'minimum_verification_permissions':'contents:read; no publishing/deployment/release permissions','maximum_combined_library_consumer_jobs':2,'unchanged_Android_UIKit_navigation_not_dispatched':True,'current_tests_passed':False,'publication_or_deployment_performed':False,'scope':'Two exact source-bound scoped verification requests, not result acceptance or release readiness.'}
(BASE/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({'dispatched':[{key:row[key] for key in ('profile','run_id','run_url','observed_status','observed_conclusion')} for row in rows],'source_revision':REV,'not_test_pass':True},indent=2),flush=True)
