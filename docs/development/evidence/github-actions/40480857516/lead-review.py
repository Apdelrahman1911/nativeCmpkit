"""Read original public reports/ZIP; reconstruct all selected bytes from immutable Git."""
from pathlib import Path,PurePosixPath
from io import BytesIO
import datetime as dt,hashlib,json,re,shutil,stat,subprocess,zipfile
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path('/dev/shm/nativecmpkit-consumer-result-40480857516')
DEST=ROOT/'docs/development/evidence/github-actions/40480857516'
SHA='c5e14c9596760fca3a2493063b295161ce5e9d36';RUN=40480857516;JOB=122110801103

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def document(payload):
 def unique(pairs):
  d={}
  for k,v in pairs:assert k not in d;d[k]=v
  return d
 return json.loads(payload,object_pairs_hook=unique)
run=document((OUT/'run-final.json').read_bytes());jobs=document((OUT/'jobs-final.json').read_bytes())['jobs'];artifacts=document((OUT/'artifacts-final.json').read_bytes())['artifacts']
assert run['id']==RUN and run['head_sha']==SHA and run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1
assert next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
assert next(j for j in jobs if j['id']==JOB)['conclusion']=='failure'
assert next(j for j in jobs if j['name']=='library-tests')['conclusion']=='skipped'
assert len(artifacts)==1
artifact=artifacts[0];payload=(OUT/f"{artifact['id']}.zip").read_bytes()
assert artifact['id']==12722503387 and artifact['size_in_bytes']==len(payload)==71891
assert artifact['digest']=='sha256:'+hashlib.sha256(payload).hexdigest()=='sha256:cc0092b58ca770aa495ea7ade34187373cb0bbee8d787f7ce4bd42eee2edb2cc'
assert artifact['workflow_run']['head_sha']==SHA and artifact['workflow_run']['id']==RUN
expected={'ci-runtime/consumer-core-io.json',*[f'ci-consumer/core-io-desktop/{name}.json' for name in ['fixture-copy','inputs-after','inputs-before','receipt','runtime-before']]}
with zipfile.ZipFile(BytesIO(payload)) as archive:
 infos=archive.infolist();assert len(infos)==6 and {i.filename for i in infos}==expected and sum(i.file_size for i in infos)<2*1024**2
 data={}
 for i in infos:
  assert not i.is_dir() and not i.flag_bits&1
  mode=i.external_attr>>16;assert stat.S_IFMT(mode) in (0,stat.S_IFREG)
  assert not PurePosixPath(i.filename).is_absolute() and '..' not in PurePosixPath(i.filename).parts
  data[i.filename]=document(archive.read(i))
 receipt=data['ci-consumer/core-io-desktop/receipt.json'];before=data['ci-consumer/core-io-desktop/inputs-before.json'];after=data['ci-consumer/core-io-desktop/inputs-after.json']
 fixture=data['ci-consumer/core-io-desktop/fixture-copy.json'];runtime=data['ci-consumer/core-io-desktop/runtime-before.json'];preflight=data['ci-runtime/consumer-core-io.json']
assert before==after and len(before)==receipt['source_input_count']==737
assert receipt['source_inputs_held'] and not receipt['changed_inputs'] and receipt['source_revision']==receipt['source_revision_after']==SHA and receipt['source_tree_dirty'] is False
input_hash=hashlib.sha256(''.join(f'{value}  {name}\n' for name,value in sorted(before.items())).encode()).hexdigest()
assert input_hash==receipt['inputs_before_sha256']==receipt['inputs_after_sha256']
raw=subprocess.check_output(['git','ls-tree','-rz','--full-tree',SHA],cwd=ROOT)
tree={}
for row in raw.split(b'\0'):
 if not row:continue
 meta,name=row.split(b'\t',1);mode,kind,oid=meta.split(b' ')
 if kind==b'blob':tree[name.decode()]=(mode.decode(),oid.decode())
selected=sorted(before);oids=[tree[name][1] for name in selected]
result=subprocess.run(['git','cat-file','--batch'],input=('\n'.join(oids)+'\n').encode(),cwd=ROOT,capture_output=True,timeout=90)
assert result.returncode==0
position=0
for name,oid in zip(selected,oids):
 end=result.stdout.index(b'\n',position);header=result.stdout[position:end].split();assert header[0].decode()==oid and header[1]==b'blob'
 size=int(header[2]);blob=result.stdout[end+1:end+1+size]
 assert len(blob)==size and result.stdout[end+1+size:end+2+size]==b'\n'
 assert hashlib.sha256(blob).hexdigest()==before[name],name
 position=end+2+size
assert position==len(result.stdout)
assert len(fixture)==6 and all(before['tests/consumer/io-desktop/'+name]==digest for name,digest in fixture.items())
assert runtime['source_revision']==preflight['source_revision']==SHA and runtime['source_tree_dirty'] is False
for key in ['host','java','rust','android_platform','compiler_runtime_fingerprint']:assert runtime[key]==preflight[key]
assert runtime['host']['system']=='Linux' and runtime['host']['architecture']=='x64' and runtime['java']['major']==17 and runtime['rust']['release']=='1.98.0'
assert receipt['candidate_group']=='io.github.apdelrahman1911.nativecmpkit' and receipt['candidate_version']=='0.1.0-preview.1' and receipt['publication_roots_requested']==['nativecmpkit-core','nativecmpkit-io']
assert receipt['passed'] is False and receipt['actual_consumer_methods_verified']==0 and receipt['complete_21_root_KMP_matrix_requested'] is False
assert receipt['release_readiness_certified'] is False and receipt['ordinary_dependency_trust_certified'] is False and receipt['packages_published'] is False and receipt['release_created'] is False
assert receipt['owned_lock_removed'] is True and len(receipt['executions'])==1 and receipt['error']['phase']=='real-producer-staging'
execution=receipt['executions'][0];assert execution['phase']=='real-producer-staging' and execution['execution']['exit_code']==1 and not execution['execution'].get('stop_reason')
assert execution['command'][-1]=='stageCoreIoVerificationPublications' and '-PnativecmpkitVerification=true' in execution['command'] and '-PnativeCmpkit.allowPublishing=true' not in execution['command']
log=(OUT/'job-log.log').read_text();error="Project with path ':calf-core' could not be found in project ':convention-plugins'."
assert error in log and "Settings file '/home/runner/work/nativeCmpkit/nativeCmpkit/settings.gradle.kts' line: 25" in log
assert 'NATIVECMPKIT_PARTIAL_STAGE task=' not in log
assert 'NATIVECMPKIT_PARTIAL_CONSUMER_TEST task=' not in log
assert not DEST.exists();(DEST/'raw').mkdir(parents=True)
for name in ['run-final.json','jobs-final.json','artifacts-final.json']:
 shutil.copyfile(OUT/name,DEST/name);assert sha(OUT/name)==sha(DEST/name)
shutil.copyfile(OUT/f"{artifact['id']}.zip",DEST/'raw'/f"{artifact['id']}.zip")
shutil.copyfile(Path(__file__),DEST/'lead-review.py')
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'run_attempt':1,'source_revision':SHA,'url':run['html_url'],'job_id':JOB,
 'job_url':f'https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/{RUN}/job/{JOB}','run_conclusion':'failure','evidence_integrity_passed':True,
 'artifact_id':artifact['id'],'artifact_digest':artifact['digest'],'artifact_bytes':len(payload),'artifact_members':sorted(expected),
 'source_input_count':737,'source_inputs_sha256':input_hash,'all_inputs_reconstructed_from_Git_and_before_after_match':True,'independently_copied_fixture_inputs':6,
 'runtime':runtime,'producer_execution':execution,'controller_elapsed_seconds':receipt['elapsed_seconds'],'Kotlin_consumer_methods_executed':0,'consumer_XML_reports':0,
 'four_publication_tasks_completed':False,'own_controller_lock_removed':True,'ordinary_detached_daemon_cleanup_attested':False,
 'bounded_actual_job_diagnostics':{'full_job_log_archived':False,'job_log_bytes':(OUT/'job-log.log').stat().st_size,'job_log_sha256':sha(OUT/'job-log.log'),
 'observations':['Actual Gradle9.7.1 wrapper downloaded and single-use daemon started.',"Settings plugin resolution wraps: "+error,'Init projectsEvaluated callback also applies to the included convention-plugins build; it unconditionally looks up calf-core/calf-io before checking the intended root.']},
 'next_step':'Add exact canonical producer-root binding before any flags/project/task lookup; leave included builds unmodified. Preserve all four local tasks/interlocks, seven consumer methods and complete21-root/native/ABI/legal/dependency/release gates. New immutable consumer-core-io run required, not an unchanged rerun.',
 'issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,
 'scope':'Real producer/init failure and source/fixture/runtime binding, not successful staging or any Kotlin/library/native/consumer testcase. Tooling pass and intentionally unselected library job are not test outcomes; bounded process group is not detached-daemon or ordinary dependency trust proof.'}
with (DEST/'lead-independent-review.json').open('x') as stream:json.dump(review,stream,indent=2,sort_keys=True);stream.write('\n')
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in sorted(DEST.rglob('*')) if p.is_file()))
print(json.dumps({'evidence_integrity_passed':True,'source_input_count':737,'consumer_methods':0,'producer_exit':1,'archive':str(DEST)},indent=2))
