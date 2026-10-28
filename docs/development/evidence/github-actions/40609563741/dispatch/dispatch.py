from pathlib import Path
import datetime,hashlib,json,subprocess,time,sys,re
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).parent;R='Apdelrahman1911/nativeCmpkit';SHA='63f377f678fa3d4f0e4def26099fb5e0a6c3247a';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5'
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT).decode().strip()
assert git('rev-parse','HEAD')==SHA and git('rev-parse','main')==MAIN and git('branch','--show-current')=='development/preview-hardening' and not git('status','--porcelain')
refs=dict(line.split('\t')[::-1] for line in git('ls-remote','--heads','origin','development/preview-hardening','main').splitlines());assert refs['refs/heads/development/preview-hardening']==SHA and refs['refs/heads/main']==MAIN
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt,workflow_matrix as wm
inputs=lt.snapshot_inputs(ROOT);assert inputs==json.loads((OUT/'inputs-before-commit.json').read_text()) and len(inputs)==741
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);raw,_=p.communicate(''.join(SHA+':'+n+'\n' for n in inputs).encode());assert p.returncode==0;off=0
for n,h in inputs.items():
 e=raw.index(b'\n',off);header=raw[off:e].split();assert header[1]==b'blob';size=int(header[2]);data=raw[e+1:e+1+size];assert hashlib.sha256(data).hexdigest()==h,n;off=e+size+2
assert off==len(raw)
matrix=wm.matrix('browser-picker')['include'];assert [r['slot'] for r in matrix]==['browser-js','browser-wasm'] and all(r['test-modules']=='calf-file-picker' for r in matrix)
def api(path,step,method='GET',body=None):
 target=OUT/(step+'.response');assert not target.exists()
 p=subprocess.run(['gh','api','repos/'+R+'/'+path,'--method',method]+([] if body is None else ['--input','-']),input=None if body is None else json.dumps(body).encode(),capture_output=True,timeout=90);target.write_bytes(p.stdout);assert p.returncode==0,'Uncertain/error result: reconcile read-only, never automatically repeat a POST';return None if not p.stdout else json.loads(p.stdout)
before=api('actions/workflows/gradle.yml/runs?per_page=30','runs-before')['workflow_runs'];assert not any(x['head_sha']==SHA for x in before);prior={x['id'] for x in before}
api('actions/workflows/gradle.yml/dispatches','dispatch','POST',{'ref':'development/preview-hardening','inputs':{'profile':'browser-picker'}})
found=[]
for i in range(5):
 runs=api('actions/workflows/gradle.yml/runs?per_page=30','runs-after-'+str(i))['workflow_runs'];found=[x for x in runs if x['id'] not in prior and x['head_sha']==SHA and x['event']=='workflow_dispatch']
 if found:break
 time.sleep(2)
assert len(found)==1,'Accepted once; indexing ambiguity requires read-only reconciliation, not repeat'
run=found[0];assert run['head_branch']=='development/preview-hardening' and run['run_attempt']==1
receipt={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'source_revision':SHA,'source_input_count':len(inputs),'source_digest':lt.input_digest(inputs),'profile':'browser-picker','run_id':run['id'],'run_url':run['html_url'],'status':run['status'],'conclusion':run['conclusion'],'POST_invocations':1,'dispatch_ref':'development/preview-hardening','selected_library_jobs':2,'selected_modules':['calf-file-picker'],'new_public_Compose_methods':5,'maximum_library_jobs':2,'main_preserved':MAIN,'unchanged_IO_or_other_successful_suites_not_repeated':True,'packages_releases_deployments_published':False,'release_readiness_certified':False}
(OUT/'dispatch-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2),flush=True)
