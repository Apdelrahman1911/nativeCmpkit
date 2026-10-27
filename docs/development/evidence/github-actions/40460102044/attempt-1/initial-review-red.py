"""Read-only pre-test hosted failure review; never executes archived data."""
from pathlib import Path, PurePosixPath
import datetime as dt, hashlib, json, re, subprocess, zipfile
ROOT=Path('/root/projects/nativeCmpKit'); OUT=Path(__file__).resolve().parent
REPO='Apdelrahman1911/nativeCmpkit'; RUN=40460102044; JOB=122042570888
REV='cebdc8f206a5e34b39e1cb8053b380ba509707c2'; ARTIFACT=12714545886

def put(name,raw):
 with (OUT/name).open('xb') as stream:stream.write(raw)

def api(endpoint,name):
 raw=subprocess.check_output(['gh','api',f'repos/{REPO}/'+endpoint],cwd=ROOT,timeout=60)
 put(name,raw);return json.loads(raw)

run=api(f'actions/runs/{RUN}','run-final.json')
jobs=api(f'actions/runs/{RUN}/attempts/1/jobs?per_page=100','jobs-final.json')['jobs']
arts=api(f'actions/runs/{RUN}/artifacts?per_page=100','artifacts-final.json')
assert run['id']==RUN and run['head_sha']==REV and run['run_attempt']==1
assert run['status']=='completed' and run['conclusion']=='failure'
assert run['repository']['full_name']==REPO and run['event']=='workflow_dispatch'
assert len(arts['artifacts'])==arts['total_count']==1
art=arts['artifacts'][0]; assert art['id']==ARTIFACT and not art['expired']
raw=subprocess.check_output(['gh','api',f'repos/{REPO}/actions/artifacts/{ARTIFACT}/zip'],cwd=ROOT,timeout=60)
assert len(raw)==art['size_in_bytes']==808
assert 'sha256:'+hashlib.sha256(raw).hexdigest()==art['digest']=='sha256:dd28c589e81834545fc5980f1c14f9a09b5e55c39dcd4197befa726d398a4d55'
put(f'raw/{ARTIFACT}.zip',raw)
with zipfile.ZipFile(OUT/f'raw/{ARTIFACT}.zip') as z:
 infos=z.infolist();assert len(infos)==1
 info=infos[0]; name=info.filename; path=PurePosixPath(name)
 assert not path.is_absolute() and not set(path.parts)&{'.','..'} and '\\' not in name
 assert not info.is_dir() and ((info.external_attr>>16)&0o170000)!=0o120000
 assert name=='build/ci-runtime/selection.json' and info.file_size<=1024*1024
 context=json.loads(z.read(name))
 assert context['source_revision']==REV and not context['source_tree_dirty']
 assert context['host']=={'architecture':'arm64','python':'3.15.0','system':'Darwin'}
 assert context['java']['major']==17 and context['rust']['release']=='1.98.0'
 assert context['xcode']=={'version':'26.6','build':'17F113'}
 assert context['simulator']['state']=='Shutdown' and context['simulator']['runtime_version']=='26.5'
log=Path('/dev/shm/nativecmpkit-uikit-preflight-review-20261027/job-122042570888.log').read_bytes()
assert len(log)==85149
lines=log.decode('utf-8-sig').splitlines()
keys=['\tData Migration Failed','subprocess.TimeoutExpired:',"##[error]Process completed with exit code 1."]
diag=[]
for i,line in enumerate(lines):
 text=re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ', '',line)
 if text==keys[0] or text.startswith(keys[1]) or text==keys[2]:diag.append({'line':i+1,'text':text})
assert len(diag)==3 and 'simctl' in diag[1]['text'] and '60 seconds' in diag[1]['text']
assert not any('> Task :' in line or 'NATIVECMPKIT_UIKIT_ACTIVE ' in line or '##teamcity[testStarted' in line for line in lines)
job=next(j for j in jobs if j['id']==JOB);assert job['conclusion']=='failure'
failed=[s for s in job['steps'] if s['conclusion']=='failure'];assert len(failed)==1 and failed[0]['number']==11
assert all(next(s for s in job['steps'] if s['number']==n)['conclusion']=='skipped' for n in (12,13,14))
tooling=next(j for j in jobs if j['name']=='tooling');assert tooling['conclusion']=='success'
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'run_attempt':1,'source_revision':REV,'url':run['html_url']+'/attempts/1','job_id':JOB,'job_url':job['html_url'],'run_conclusion':'failure','evidence_integrity_passed':True,'artifact_id':ARTIFACT,'artifact_digest':art['digest'],'artifact_bytes':len(raw),'artifact_members':[name],'selection_context':context,'actual_xml_reports':0,'library_native_or_packaged_consumer_methods_executed':0,'application_link_or_transport_attempted':False,'failed_step':failed[0]['name'],'bounded_actual_job_diagnostics':{'log_bytes':len(log),'log_sha256':hashlib.sha256(log).hexdigest(),'full_log_archived':False,'temporary_log':'/dev/shm/nativecmpkit-uikit-preflight-review-20261027/job-122042570888.log','observations':diag},'confirmed_failure':'Hosted selected simulator boot reports Data Migration Failed; subsequent exact simctl list devices --json times out after60s. Cache, planning, Gradle linking and actual library/application test steps are never reached.','root_cause_boundary':'Apple hosted simulator migration/service failed before test execution. Underlying OS/runner cause is not proven; no evidence that the changed UIKit application code caused this pre-test failure.','next_step':'One failed-job-only rerun at the exact unchanged revision on a fresh hosted runner; preserve this attempt and successful tooling. Do not weaken identity, native, no-skip, timeout or cleanup requirements. Repeated simulator failure needs owning infrastructure diagnosis.','successful_tooling_job':{'job_id':tooling['id'],'completed_at':tooling['completed_at']},'issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
put('lead-independent-review.json',(json.dumps(review,indent=2,sort_keys=True)+'\n').encode())
put('SHA256SUMS', ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT)}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS').encode())
print(json.dumps({k:review[k] for k in ['run_id','run_attempt','evidence_integrity_passed','actual_xml_reports','library_native_or_packaged_consumer_methods_executed','application_link_or_transport_attempted']}))
