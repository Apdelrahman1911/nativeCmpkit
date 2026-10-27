"""Immutable source/ZIP/runtime review of actual bounded UIKit startup failure."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,json,re,subprocess,sys,tempfile,zipfile
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).resolve().parent
TMP=Path('/dev/shm/nativecmpkit-uikit-attempt2-review-20261027')
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
REPO='Apdelrahman1911/nativeCmpkit';RUN=40460102044;REV='cebdc8f206a5e34b39e1cb8053b380ba509707c2';JOB=122047132627;ARTIFACT=12715013978

def put(name,raw):
 with (OUT/name).open('xb') as stream:stream.write(raw)

def api(endpoint,name):
 raw=subprocess.check_output(['gh','api',f'repos/{REPO}/'+endpoint],cwd=ROOT,timeout=60);put(name,raw);return json.loads(raw)
run=api(f'actions/runs/{RUN}','run-final.json');jobs=api(f'actions/runs/{RUN}/attempts/2/jobs?per_page=100','jobs-final.json')['jobs']
arts=json.loads((TMP/'artifacts-final.json').read_bytes());put('artifacts-final.json',(TMP/'artifacts-final.json').read_bytes())
assert run['id']==RUN and run['run_attempt']==2 and run['head_sha']==REV and run['conclusion']=='failure' and run['status']=='completed'
assert run['repository']['full_name']==REPO and run['event']=='workflow_dispatch'
assert arts['total_count']==len(arts['artifacts'])==2 and {a['id'] for a in arts['artifacts']}=={ARTIFACT,12714545886}
art=next(a for a in arts['artifacts'] if a['id']==ARTIFACT);raw=(TMP/'raw'/f'{ARTIFACT}.zip').read_bytes()
assert len(raw)==art['size_in_bytes']==74788 and not art['expired']
digest='sha256:'+hashlib.sha256(raw).hexdigest();assert digest==art['digest']=='sha256:084c630c4ac0b6c3b92404e96835c13a7cad93db0940d09818a482e6fea13a44'
put(f'raw/{ARTIFACT}.zip',raw)
rerun=json.loads((OUT/'rerun-receipt.json').read_bytes());assert rerun['expected_attempt']==2 and rerun['expected_source_sha']==REV and rerun['failed_job_ids']==[122042570888] and rerun['exit_code']==0 and not rerun['request_retried']
assert json.loads((OUT/'main-after.json').read_bytes())['object']['sha']=='94d2492e99d5cbc060409d94d9f88febd06222d5'
records={}
for row in subprocess.check_output(['git','ls-tree','-rz',REV],cwd=ROOT).split(b'\0'):
 if row:
  metadata,name=row.split(b'\t',1);records[name.decode()]=metadata.decode().split()
def blob(name):
 mode,kind,oid=records[name];assert kind=='blob' and mode in ['100644','100755'];return subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-startup-failure-review-',dir='/dev/shm') as directory:
 view=Path(directory)
 def materialize(name):
  target=view/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(blob(name))
 materialize('settings.gradle.kts')
 for name in records:
  if name.startswith(('calf-','sample/')) and name.endswith('/build.gradle.kts'):materialize(name)
 projects=lt.projects(view)
 prefixes=['gradle/','convention-plugins/','scripts/ci/','scripts/native/','kotlin-js-store/']
 prefixes += [f'{m}/{f}/' for m in projects for f in ('src','native','.cargo','gradle')]
 exact=set(lt.ROOT_INPUTS)|{f'{m}/{n}' for m in projects for n in ('build.gradle.kts','gradle.properties','gradle.lockfile')}
 exact|={n for n in records if n.startswith('sample/') and n.count('/')==2 and n.endswith('/build.gradle.kts')}
 for name in records:
  if (name in exact or any(name.startswith(p) for p in prefixes)) and not set(PurePosixPath(name).parts[:-1])&lt.IGNORED_INPUT_DIRS:materialize(name)
 inputs=lt.snapshot_inputs(view);assert len(inputs)==711
 plan=lt.plan(view,'ios',only_modules=('calf-ui',))
 with zipfile.ZipFile(OUT/f'raw/{ARTIFACT}.zip') as z:
  infos=z.infolist();names=[i.filename for i in infos];assert len(names)==len(set(names))==10 and sum(i.file_size for i in infos)<=64*1024**2
  for info in infos:
   path=PurePosixPath(info.filename);assert not path.is_absolute() and not set(path.parts)&{'.','..'} and '\\' not in info.filename
   assert not info.is_dir() and info.filename.endswith('.json') and info.file_size<=lt.MAX_REPORT_BYTES and ((info.external_attr>>16)&0o170000)!=0o120000
  def doc(n):return json.loads(z.read(n))
  base='build/ci-verification/ios-iphone/';receipt=doc(base+'receipt.json');runtime=doc(base+'runtime.json')
  assert doc(base+'inputs-before.json')==doc(base+'inputs-after.json')==inputs
  assert doc(base+'plan.json')==doc('build/ci-plan/plan.json')==plan
  assert receipt['source_revision']==receipt['source_revision_after']==REV and not receipt['source_tree_dirty'] and not receipt['changed_inputs'] and not receipt['passed']
  assert receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(inputs)
  assert receipt['runtime_receipt_sha256']==hashlib.sha256(z.read(base+'runtime.json')).hexdigest()
  assert runtime['source_revision']==REV and not runtime['source_tree_dirty'] and runtime['host']['architecture']=='arm64' and runtime['host']['system']=='Darwin'
  assert runtime['java']['major']==17 and runtime['rust']['release']=='1.98.0' and runtime['simulator']['state']=='Booted'
  assert receipt['command']==lt.gradle_command('ios',plan,simulator=runtime['simulator']['udid'],root=view)
  assert receipt['execution']['exit_code']==1 and not receipt['execution'].get('stop_reason') and receipt['quarantined_prior_reports']==[]
  assert receipt['task_execution_markers']=={':calf-ui:iosSimulatorArm64ApplicationTest':1}
  assert len(receipt['modules'])==1 and receipt['modules'][0]['reports']==receipt['modules'][0]['testcases']==[]
  assert all(v==0 for v in receipt['totals'].values())
  paths=[n for n in names if '/native-ui-application/' in n];assert len(paths)==1
  app_path=paths[0];app=doc(app_path);assert app['source_revision']==REV and not app['source_tree_dirty'] and not app['transport_passed'] and app['application_protocol'] is None
  assert app['error']=={'phase':'launch-and-real-test-transport','type':'ValueError'}
  observation=app['startup_failure_observation'];assert observation=={'active':True,'hidden':False,'key':True,'root_attached':False,'root_native_equal':True,'worker_started':False}
  assert app['steps']['foreign-app-preflight']['preexisting_app_absence_verified'] and app['steps']['adhoc-sign-local-verification-app']['exit_code']==0 and not app['steps']['adhoc-sign-local-verification-app']['remote_signing_or_publication']
  assert app['steps']['install-owned-app']['exit_code']==0 and app['steps']['install-owned-app']['installed_owned_bytes_verified']
  assert all(app['cleanup'][k] for k in ['owned_app_identity_reverified','owned_app_stopped_verified','owned_app_absence_verified','owned_local_bundle_removed'])
  assert not app['packages_published'] and not app['release_readiness_certified']
log=(TMP/'job-122047132627.log').read_bytes();assert len(log)==100027
clean=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ','',line) for line in log.decode('utf-8-sig').splitlines()]
assert '> Task :calf-ui:linkApplicationDebugTestIosSimulatorArm64' in clean and 'NATIVECMPKIT_UIKIT_TRANSPORT passed=false' in clean
assert not any(line.startswith(('NATIVECMPKIT_UIKIT_ACTIVE ','##teamcity[testStarted')) for line in clean)
host=blob('calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt').decode()
assert 'attached === window' in host and 'rootNativeEqual=${attached == window}' in host and '>= 10.0' in host
parser=blob('scripts/ci/ios_ui_application.py').decode();assert 'startup_failure_observation' in parser and 'rootNativeEqual' in parser
job=next(j for j in jobs if j['id']==JOB);assert job['status']=='completed' and job['conclusion']=='failure'
tooling=next(j for j in jobs if j['name']=='tooling');assert tooling['conclusion']=='success' and tooling['started_at']=='2026-10-27T06:16:20Z' and tooling['completed_at']=='2026-10-27T06:16:52Z'
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'run_attempt':2,'source_revision':REV,'url':run['html_url']+'/attempts/2','job_id':JOB,'job_url':job['html_url'],'run_conclusion':'failure','artifact_id':ARTIFACT,'artifact_digest':digest,'artifact_bytes':len(raw),'artifact_members':names,'evidence_integrity_passed':True,'source_input_count':len(inputs),'source_inputs_sha256':lt.input_digest(inputs),'actual_xml_reports':0,'totals':receipt['totals'],'execution':receipt['execution'],'command':receipt['command'],'runtime':runtime,'application_receipt_path':app_path,'application_macho':app['macho'],'application_link_sign_install_completed':True,'application_transport_passed':False,'startup_failure_observation':observation,'application_cleanup':app['cleanup'],'successful_tooling_reused_not_reexecuted':{'attempt2_record_job_id':tooling['id'],'original_job_id':122042391116,'started_at':tooling['started_at'],'completed_at':tooling['completed_at']},'bounded_actual_job_diagnostics':{'log_bytes':len(log),'log_sha256':hashlib.sha256(log).hexdigest(),'full_log_archived':False,'temporary_log':str(TMP/'job-122047132627.log'),'actual_native_test_or_activation_frame_observed':False},'confirmed_failure':'Real app reaches the bounded main-loop readiness timeout: active/key/visible true, Kotlin referential rootAttached false, Objective-C equality rootNativeEqual true, Worker not started. No testcase/XML runs; owned app cleanup passes.','root_cause_boundary':'Disagreement persists through the10s main-loop deadline, so delaying activation alone is not a fix. Kotlin wrapper referential identity is not an appropriate assumed native-identity contract. The timeout observes Objective-C equality, not exact native pointers; do not infer pointer identity or accept semantic equality silently.','next_step':'Use an explicit exact nonnull native-object-pointer identity contract for native ownership checks, with foreign/equal-value adversarial native regressions and verified compiler API. Keep readiness/worker/transport/no-skip/cleanup gates strict; execute new immutable ios-ui CI only after source/typecheck verification.','issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
put('lead-independent-review.json',(json.dumps(review,indent=2,sort_keys=True)+'\n').encode())
put('SHA256SUMS',''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT)}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS').encode())
print(json.dumps({k:review[k] for k in ['run_id','run_attempt','evidence_integrity_passed','actual_xml_reports','startup_failure_observation','application_transport_passed']},indent=2))
