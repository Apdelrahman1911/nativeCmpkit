"""One push/two scoped verification dispatches; no release/settings/issue operations."""
from pathlib import Path
import datetime as dt,gzip,hashlib,json,subprocess,time
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path('/dev/shm/nativecmpkit-dispatch-8ab48555-20261027')
REPO='Apdelrahman1911/nativeCmpkit';REF='development/preview-hardening';SHA='8ab48555a30d8fe2dbf6f422a6f2cf1bd2423c8f';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5';OLD='d2b47840e352e0e04c3ae5c19d8b81b04fd967ab'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(name,x):
 with (OUT/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def get(path,name=None):
 result=subprocess.run(['gh','api','repos/'+REPO+'/'+path],cwd=ROOT,capture_output=True,timeout=90)
 if result.returncode:
  if name:
   (OUT/(name+'.stderr')).write_bytes(result.stderr)
  raise AssertionError('Read-only GitHub preflight failed; no implicit retry or mutation')
 value=json.loads(result.stdout)
 if name:
  if len(result.stdout)>100000:(OUT/(name+'.json.gz')).write_bytes(gzip.compress(result.stdout,mtime=0))
  else:(OUT/(name+'.json')).write_bytes(result.stdout)
 return value
def branch(name,filename):return get('branches/'+name,filename)['commit']['sha']
def local():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==SHA
 assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==REF
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
 assert subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip() in {'https://github.com/'+REPO+'.git','git@github.com:'+REPO+'.git'}
 source=subprocess.check_output(['git','show',SHA+':.github/workflows/gradle.yml'],cwd=ROOT)
 assert source==(ROOT/'.github/workflows/gradle.yml').read_bytes()
 for content in [b'permissions:\n  contents: read',b'consumer-core-io',b'persist-credentials: false',b'  workflow_dispatch:']:
  assert content in source
 assert b'  push:' not in source and b'packages: write' not in source and b'deployments: write' not in source
 return hashlib.sha256(source).hexdigest()
workflow_hash=local();started=utc()
permissions=get('actions/permissions','actions-permissions');assert permissions=={'enabled':True,'allowed_actions':'all','sha_pinning_required':False}
workflow_permissions=get('actions/permissions/workflow','workflow-permissions');assert workflow_permissions=={'default_workflow_permissions':'read','can_approve_pull_request_reviews':False}
assert branch('main','main-before')==MAIN
assert branch(REF,'development-before')==OLD
workflow=get('actions/workflows/gradle.yml','workflow');assert workflow['state']=='active' and workflow['path']=='.github/workflows/gradle.yml'
pages=get('pages','pages-before');assert pages.get('status') is None and pages.get('build_type')=='workflow'
releases=get('releases?per_page=100','releases-before');assert releases==[]
for status in ['in_progress','queued','pending','requested','waiting']:
 runs=get('actions/runs?branch='+REF+'&status='+status+'&per_page=100',status+'-before')
 assert runs['total_count']==0,'Existing work on the development ref; refuse overlapping dispatch'
get('actions/runs?branch='+REF+'&per_page=100','runs-before-push')
save('preflight.json',{'passed':True,'observed_utc':utc(),'source_revision':SHA,'parent_revision':OLD,'main_preserved':MAIN,
 'workflow_sha256':workflow_hash,'profiles':['ios-ui','consumer-core-io'],'published_or_release_or_deploy_requested':False,
 'authorization':'Owner enabled all verification Actions without mandatory SHA pinning; single-agent contained publishing; minimum read-only token permissions.'})
with (OUT/'push.log').open('xb') as log:
 push=subprocess.run(['git','push','origin','HEAD:refs/heads/'+REF],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180)
assert push.returncode==0,'Push failed; do not dispatch an unpushed revision'
assert branch(REF,'development-after-push')==SHA
assert branch('main','main-after-push')==MAIN
local()
result=[]
for profile in ['ios-ui','consumer-core-io']:
 assert branch(REF,profile+'-ref-before')==SHA
 before=get('actions/runs?branch='+REF+'&per_page=100',profile+'-runs-before')
 old_ids={run['id'] for run in before['workflow_runs']}
 payload=OUT/(profile+'-payload.json');payload.write_text(json.dumps({'ref':REF,'inputs':{'profile':profile}})+'\n')
 began=utc()
 with (OUT/(profile+'-dispatch.stdout')).open('xb') as stdout,(OUT/(profile+'-dispatch.stderr')).open('xb') as stderr:
  posted=subprocess.run(['gh','api','repos/'+REPO+'/actions/workflows/gradle.yml/dispatches','--method','POST','--input',str(payload)],cwd=ROOT,stdout=stdout,stderr=stderr,timeout=90)
 save(profile+'-dispatch-result.json',{'exit_code':posted.returncode,'started_utc':began,'finished_utc':utc(),'post_invocations':1,'profile':profile,'ref':REF,'expected_head_sha':SHA,
 'stdout_sha256':hashlib.sha256((OUT/(profile+'-dispatch.stdout')).read_bytes()).hexdigest(),'stderr_sha256':hashlib.sha256((OUT/(profile+'-dispatch.stderr')).read_bytes()).hexdigest()})
 # Never repeat an uncertain POST. Reconcile actual server state first.
 assert posted.returncode==0,'Dispatch uncertain/rejected; original response preserved, no automatic retry'
 match=None
 for attempt in range(13):
  after=get('actions/runs?branch='+REF+'&per_page=100',profile+'-runs-after-'+str(attempt))
  candidates=[r for r in after['workflow_runs'] if r['id'] not in old_ids and r['head_sha']==SHA and r['head_branch']==REF and r['event']=='workflow_dispatch' and r['workflow_id']==workflow['id']]
  assert len(candidates)<=1,'Ambiguous new runs; no repeat dispatch or guessed run assignment'
  if candidates:match=candidates[0];break
  time.sleep(10)
 assert match is not None,'No definite run readback; no implicit retry'
 readback=get('actions/runs/'+str(match['id']),profile+'-run-readback')
 assert readback['id']==match['id'] and readback['head_sha']==SHA and readback['head_branch']==REF and readback['event']=='workflow_dispatch'
 assert branch(REF,profile+'-ref-after')==SHA
 row={'profile':profile,'id':match['id'],'head_sha':SHA,'run_attempt':readback['run_attempt'],'html_url':readback['html_url'],'status':readback['status'],'conclusion':readback['conclusion'],'post_invocations':1}
 result.append(row);print(json.dumps(row),flush=True)
assert branch('main','main-after-dispatch')==MAIN
local()
save('receipt.json',{'passed':True,'started_utc':started,'finished_utc':utc(),'source_revision':SHA,'main_preserved':MAIN,'workflow_sha256':workflow_hash,
 'runs':result,'GitHub_dispatches':2,'issues_mutated':0,'settings_mutated':0,'packages_published':False,'release_created':False,'deployment_requested':False,'release_readiness_certified':False,
 'scope':'Two targeted verification runs, each requested once at an unchanged named ref and readback-verified immutable head_sha. Source/tree/permissions/Pages/main preflight reviewed. Dispatch acceptance is not runtime or release success; inspect artifacts/XML and actual command/runtime/source/cleanup.'})
print(json.dumps({'dispatch_receipt':str(OUT/'receipt.json'),'runs':result},indent=2),flush=True)
