"""One immutable current navigation desktop verification; minimum read-only jobs, no publication."""
from pathlib import Path
import datetime as dt,gzip,hashlib,json,subprocess,time,sys
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).parent
REPO='Apdelrahman1911/nativeCmpkit';REF='development/preview-hardening'
SHA='70114ff3d579af291c4a3028181efc7d884e23a9';PREV='ea79ab8cf30132b4b37985f175d00287382ddca8';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5'
PREFLIGHT='docs/development/evidence/ci-preflight-20261027-025/lead-review.json'
LINKS='docs/development/evidence/postfreeze025-links-20261027/review.json'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(name,x):
 with (OUT/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def get(endpoint,name):
 r=subprocess.run(['gh','api','repos/'+REPO+'/'+endpoint],cwd=ROOT,capture_output=True,timeout=90)
 if r.returncode:
  (OUT/(name+'.stderr')).write_bytes(r.stderr)
  raise AssertionError('Read-only GitHub observation failed; preserve and reconcile, never repeat mutation')
 raw=r.stdout;p=OUT/name
 if len(raw)>100000:p=p.with_suffix(p.suffix+'.gz');p.write_bytes(gzip.compress(raw,mtime=0))
 else:p.write_bytes(raw)
 return json.loads(raw)
def local():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==SHA
 assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==REF
 assert subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()=='https://github.com/'+REPO+'.git'
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
local();started=utc()
assert get('branches/main','main-before.json')['commit']['sha']==MAIN
assert get('branches/'+REF,'development-before.json')['commit']['sha']==PREV
assert get('actions/permissions','actions-permissions.json')=={'enabled':True,'allowed_actions':'all','sha_pinning_required':False}
assert get('actions/permissions/workflow','workflow-permissions.json')=={'default_workflow_permissions':'read','can_approve_pull_request_reviews':False}
pages=get('pages','pages-before.json');assert pages['status'] is None and pages['build_type']=='workflow'
assert get('releases?per_page=100','releases-before.json')==[]
workflow=get('actions/workflows/gradle.yml','workflow.json');assert workflow['state']=='active' and workflow['path']=='.github/workflows/gradle.yml'
source=(ROOT/'.github/workflows/gradle.yml').read_bytes();assert source==subprocess.check_output(['git','show',SHA+':.github/workflows/gradle.yml'],cwd=ROOT)
for token in (b'permissions:\n  contents: read',b'persist-credentials: false',b'navigation-desktop',b'  workflow_dispatch:'):
 assert token in source
assert all(t not in source for t in (b'packages: write',b'deployments: write',b'id-token: write',b'  push:'))
for path in (PREFLIGHT,LINKS):assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',SHA+':'+path],cwd=ROOT)
preflight=json.loads((ROOT/PREFLIGHT).read_bytes());links=json.loads((ROOT/LINKS).read_bytes())
assert preflight['passed'] and preflight['commands']==23 and preflight['python_tooling_methods']==1225
assert links['passed'] and links['all_other_executable_test_and_workflow_inputs_unchanged']
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt;import workflow_matrix as wm
assert len(lt.snapshot_inputs(ROOT))==726
plan=lt.plan(ROOT,'desktop',only_modules=('calf-navigation',));assert len(plan['expected'])==1 and plan['expected'][0]['module']=='calf-navigation'
assert 'calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/NavArrayParsingWorkTest.kt' in plan['expected'][0]['test_source_files']
assert wm.matrix('navigation-desktop')['include']==[{'slot':'desktop-linux-x64','suite':'desktop','runner':'ubuntu-24.04','arch':'x64','python':'python3','test-modules':'calf-navigation'}]
# No concurrent work at admission; this targeted profile owns only one library job.
for status in ('in_progress','queued','waiting','pending','requested'):
 r=get('actions/runs?status='+status+'&per_page=100',status+'-before.json')
 assert r['total_count']==0 and r['workflow_runs']==[],'Existing jobs; reconcile rather than overlap blindly'
before=get('actions/workflows/gradle.yml/runs?per_page=100','runs-before.json');old_ids={r['id'] for r in before['workflow_runs']}
save('preflight.json',{'passed':True,'source_revision':SHA,'parent_revision':PREV,'main_preserved':MAIN,
 'workflow_sha256':hashlib.sha256(source).hexdigest(),'lightweight_commands':23,'overlapping_Python_methods':1225,
 'source_inputs':726,'new_JVM_methods':2,'new_JVM_source_files':1,'profile':'navigation-desktop',
 'single_selected_library_job':True,'no_unchanged_browser_Apple_geo_or_consumer_redispatch':True,'publication_performed':False})
try:
 push=subprocess.run(['git','push','origin','HEAD:refs/heads/'+REF],cwd=ROOT,capture_output=True,timeout=180);push_exit=push.returncode
 (OUT/'push.log').write_bytes(push.stdout+push.stderr)
except subprocess.TimeoutExpired as e:
 (OUT/'push.log').write_bytes((e.stdout or b'')+(e.stderr or b''));push_exit=None
save('push.json',{'invocations':1,'exit_code':push_exit,'automatic_retry':False,'branch':REF})
assert get('branches/'+REF,'development-after-push.json')['commit']['sha']==SHA
assert get('branches/main','main-after-push.json')['commit']['sha']==MAIN
local();save('payload.json',{'ref':REF,'inputs':{'profile':'navigation-desktop'}});request_started=utc()
try:
 request=subprocess.run(['gh','api','repos/'+REPO+'/actions/workflows/gradle.yml/dispatches','--method','POST','--input',str(OUT/'payload.json')],cwd=ROOT,capture_output=True,timeout=90);request_exit=request.returncode
 (OUT/'request.stdout').write_bytes(request.stdout);(OUT/'request.stderr').write_bytes(request.stderr)
except subprocess.TimeoutExpired as e:
 (OUT/'request.stdout').write_bytes(e.stdout or b'');(OUT/'request.stderr').write_bytes(e.stderr or b'');request_exit=None
save('request.json',{'endpoint':'repos/'+REPO+'/actions/workflows/gradle.yml/dispatches','method':'POST','invocations':1,
 'started_utc':request_started,'finished_utc':utc(),'exit_code':request_exit,'automatic_retry':False})
found=None
for i in range(12):
 after=get('actions/workflows/gradle.yml/runs?per_page=100','runs-after-'+str(i)+'.json')
 matches=[r for r in after['workflow_runs'] if r['id'] not in old_ids and r['head_sha']==SHA and r['head_branch']==REF and r['event']=='workflow_dispatch' and r['workflow_id']==workflow['id']]
 assert len(matches)<=1,'Uncertain duplicate/ambiguous dispatch; read-only reconciliation, never duplicate POST'
 if matches:found=matches[0];break
 time.sleep(8)
assert found is not None,'No confirmed dispatch readback; do not repeat POST'
readback=get('actions/runs/'+str(found['id']),'run-readback.json')
assert readback['head_sha']==SHA and readback['repository']['full_name']==REPO and readback['run_attempt']==1
assert get('branches/'+REF,'development-after-dispatch.json')['commit']['sha']==SHA
assert get('branches/main','main-after-dispatch.json')['commit']['sha']==MAIN
local()
save('receipt.json',{'passed':True,'started_utc':started,'finished_utc':utc(),'source_revision':SHA,'main_preserved':MAIN,
 'run_id':found['id'],'run_attempt':1,'run_url':found['html_url'],'profile':'navigation-desktop','status':readback['status'],'conclusion':readback['conclusion'],
 'POST_invocations':1,'GitHub_dispatches':1,'request_exit':request_exit,'push_exit':push_exit,'selected_library_jobs':1,
 'source_inputs':726,'new_JVM_methods':2,'new_JVM_source_files':1,'settings_mutated':False,'issues_mutated':False,
 'packages_releases_deployments_Pages':False,'release_readiness_certified':False,
 'scope':'One current navigation-only desktop verification at exact named-ref/readback-bound immutable SHA. Source/staged tooling and local two-method diagnostic pass; dispatch is not immutable runtime success. Unchanged browser/Apple/geo/consumer profiles not repeated. Release gates remain closed.'})
print(json.dumps({'run_id':found['id'],'run_url':found['html_url'],'source_revision':SHA,'status':readback['status'],'receipt':str(OUT/'receipt.json')},indent=2),flush=True)
