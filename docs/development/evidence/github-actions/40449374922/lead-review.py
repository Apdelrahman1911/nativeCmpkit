"""Read-only immutable source/ZIP/JSON and bounded real-job-log review.
A successful integrity check is explicitly not UIKit/library test success.
"""
from pathlib import Path, PurePosixPath
import datetime as dt,hashlib,json,re,subprocess,sys,tempfile,zipfile
ROOT=Path('/root/projects/nativeCmpKit')
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests as lt
RUN=40449374922;REV='9f05d162eb784b28e441498d81b35955ea65e8e4';ARTIFACT=12710828384
run=json.loads((OUT/'run-final.json').read_text());jobs=json.loads((OUT/'jobs-final.json').read_text())['jobs'];arts=json.loads((OUT/'artifacts-final.json').read_text())
assert run['id']==RUN and run['head_sha']==REV and run['status']=='completed' and run['conclusion']=='failure'
assert run['repository']['full_name']=='Apdelrahman1911/nativeCmpkit' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
assert len(arts['artifacts'])==arts['total_count']==1
art=arts['artifacts'][0];assert art['id']==ARTIFACT and art['name']=='library-evidence-ios-iphone' and not art['expired']
payload=(OUT/'raw'/f'{ARTIFACT}.zip').read_bytes();digest='sha256:'+hashlib.sha256(payload).hexdigest()
assert len(payload)==art['size_in_bytes']<=64*1024*1024 and digest==art['digest']=='sha256:7a98922c0e5545d87520e7a8e6e833bf54c4e1c0ebc28e662626c106c8b08397'
assert json.loads((OUT/'dispatch-body.json').read_text())=={'ref':'development/preview-hardening','inputs':{'profile':'ios-ui'}}
dispatch=json.loads((OUT/'dispatch-receipt.json').read_text());assert dispatch['expected_source_sha']==REV and dispatch['exit_code']==0 and not dispatch['dispatch_retried'] and not dispatch['packages_releases_or_deployments_requested']
assert dispatch['maximum_combined_runtime_slots']==2 and dispatch['existing_active_run_ids']==[]
for n in ['branch-before.json','branch-after.json']:assert json.loads((OUT/n).read_text())['object']['sha']==REV
assert json.loads((OUT/'main-after.json').read_text())['object']['sha']=='94d2492e99d5cbc060409d94d9f88febd06222d5'
assert json.loads((OUT/'actions-permissions.json').read_text())=={'enabled':True,'allowed_actions':'all','sha_pinning_required':False}
assert json.loads((OUT/'workflow-permissions.json').read_text())=={'default_workflow_permissions':'read','can_approve_pull_request_reviews':False}
pages=json.loads((OUT/'pages.json').read_text());assert pages['status'] is None and pages['build_type']=='workflow'
records={}
for row in subprocess.check_output(['git','ls-tree','-rz',REV],cwd=ROOT).split(b'\0'):
 if row:
  metadata,name=row.split(b'\t',1);records[name.decode()]=metadata.decode().split()
def blob(name):
 mode,kind,oid=records[name];assert kind=='blob' and mode in ('100644','100755')
 return subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-uikit-review-',dir='/dev/shm') as directory:
 view=Path(directory)
 def materialize(name):
  p=view/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(name))
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
 inputs=lt.snapshot_inputs(view);assert len(inputs)==710 and lt.input_digest(inputs)=='fc23ce343433df3f3fa5d45209f05a96f22bfb97eee1bc8b9a3a4a45247a1694'
 plan=lt.plan(view,'ios',only_modules=('calf-ui',))
 with zipfile.ZipFile(OUT/'raw'/f'{ARTIFACT}.zip') as z:
  infos=z.infolist();names=[i.filename for i in infos]
  assert len(names)==len(set(names))<=2000 and sum(i.file_size for i in infos)<=64*1024*1024
  for i in infos:
   p=PurePosixPath(i.filename);assert not p.is_absolute() and not set(p.parts)&{'.','..'} and '\\' not in i.filename
   assert not i.is_dir() and i.file_size<=lt.MAX_REPORT_BYTES and ((i.external_attr>>16)&0o170000)!=0o120000 and i.filename.endswith(('.json','.xml'))
  def doc(n):return json.loads(z.read(n))
  base='build/ci-verification/ios-iphone/'
  receipt=doc(base+'receipt.json');runtime=doc(base+'runtime.json')
  assert doc(base+'inputs-before.json')==doc(base+'inputs-after.json')==inputs
  assert doc(base+'plan.json')==doc('build/ci-plan/plan.json')==plan
  assert receipt['source_revision']==receipt['source_revision_after']==REV and not receipt['source_tree_dirty'] and not receipt['changed_inputs'] and not receipt['passed']
  assert receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(inputs)
  assert receipt['runtime_receipt_sha256']==hashlib.sha256(z.read(base+'runtime.json')).hexdigest()
  assert runtime['source_revision']==REV and runtime['host']=={'architecture':'arm64','python':'3.15.0','system':'Darwin'} and not runtime['source_tree_dirty']
  assert runtime['java']['major']==17 and runtime['rust']['release']=='1.98.0'
  assert receipt['command']==lt.gradle_command('ios',plan,simulator=runtime['simulator']['udid'],root=view)
  assert receipt['execution']['exit_code']==1 and not receipt['execution'].get('stop_reason')
  assert receipt['quarantined_prior_reports']==[] and receipt['task_execution_markers']=={':calf-ui:iosSimulatorArm64ApplicationTest':1}
  assert len(receipt['modules'])==1 and receipt['modules'][0]['reports']==[] and receipt['modules'][0]['testcases']==[]
  assert all(v==0 for v in receipt['totals'].values()) and not any(n.endswith('.xml') for n in names)
  nested=[n for n in names if '/native-ui-application/' in n];assert len(nested)==1
  app=doc(nested[0]);assert app['source_revision']==REV and not app['source_tree_dirty'] and not app['transport_passed'] and app['application_protocol'] is None
  assert app['error']=={'phase':'launch-and-real-test-transport','type':'ValueError'}
  assert app['macho']=={'architecture':'arm64','file_type':'executable','minimum_os':'15.0.0','platform':7,'sdk':'26.4.0'}
  assert app['runtime_before']['simulator']==runtime['simulator']
  assert app['steps']['foreign-app-preflight']['preexisting_app_absence_verified'] and app['steps']['foreign-app-preflight']['exit_code']==2
  assert app['steps']['adhoc-sign-local-verification-app']['exit_code']==0 and not app['steps']['adhoc-sign-local-verification-app']['remote_signing_or_publication']
  assert app['steps']['install-owned-app']['exit_code']==0 and app['steps']['install-owned-app']['installed_owned_bytes_verified']
  assert all(app['cleanup'][k] for k in ['owned_app_identity_reverified','owned_app_stopped_verified','owned_app_absence_verified','owned_local_bundle_removed'])
  assert app['cleanup']['terminate_exit_code']==3 and app['cleanup']['uninstall_exit_code']==0 and app['cleanup']['absence_status']['exit_code']==2
  assert not app['packages_published'] and not app['release_readiness_certified']
  app_path=nested[0]
# Inspect the actual public job log, not fabricated/source-only diagnostics.
log=OUT/'job-122008394985.log';log_bytes=log.read_bytes();assert len(log_bytes)<8*1024*1024
lines=log_bytes.decode('utf-8-sig',errors='strict').splitlines();clean=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ', '', s) for s in lines]
exact="*** Terminating app due to uncaught exception 'Initializer is not implemented', reason: 'init is not implemented in NativecmpkitUIKitLibraryTestDelegate'"
observed=[{'line':i+1,'text':s} for i,s in enumerate(clean) if s==exact]
assert len(observed)==2 and not any(s.startswith('NATIVECMPKIT_UIKIT_ACTIVE ') for s in clean) and not any(s.startswith('##teamcity[') for s in clean)
assert '> Task :calf-ui:linkApplicationDebugTestIosSimulatorArm64' in clean
assert 'NATIVECMPKIT_UIKIT_TRANSPORT passed=false' in clean
host=blob('calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt').decode()
assert 'class NativeUiApplicationDelegate : UIResponder(), UIApplicationDelegateProtocol' in host and 'OverrideInit' not in host
assert 'UIApplicationMain(0, null, null, NSStringFromClass(delegate))' in host
job=next(j for j in jobs if j['id']==122008394985);assert job['status']=='completed' and job['conclusion']=='failure'
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'source_revision':REV,'url':run['html_url'],'run_conclusion':'failure','job_id':job['id'],'job_url':job['html_url'],'artifact_id':ARTIFACT,'artifact_digest':digest,'artifact_members':names,'evidence_integrity_passed':True,'source_input_count':len(inputs),'source_inputs_sha256':lt.input_digest(inputs),'uploaded_xml_reports':0,'totals':receipt['totals'],'execution':receipt['execution'],'command':receipt['command'],'runtime':runtime,'application_receipt_path':app_path,'application_link_sign_install_completed':True,'application_transport_passed':False,'application_cleanup':app['cleanup'],'bounded_actual_job_diagnostics':{'log_bytes':len(log_bytes),'log_sha256':hashlib.sha256(log_bytes).hexdigest(),'full_log_archived':False,'exact_initializer_diagnostics':observed,'activation_or_teamcity_frame_observed':False},'source_location':{'path':'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt','line':184,'symbol':'NativeUiApplicationDelegate'},'root_cause':'UIApplicationMain constructs the named exported delegate via Objective-C init. The test-only Kotlin delegate declares only an ordinary Kotlin primary constructor and does not implement/export the inherited Objective-C initializer. Actual iOS reports init is not implemented before application activation or any testcase.','scope':'Failed genuine application attempt: simulator Mach-O linking, local ad-hoc sign, byte-readback installation and owned stop/uninstall/absence cleanup passed. Actual Objective-C delegate initialization crashes; zero application lifecycle/Worker/library/KGP XML methods verified. Two identical crash diagnostics are observations, not proof of a wrapper retry or production defect. Preserve original nested failed transport and final errors; no finding closure or release gate cleared.','issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':lt.sha256(Path(__file__))}
(OUT/'lead-independent-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:review[k] for k in ['run_id','evidence_integrity_passed','uploaded_xml_reports','totals','application_link_sign_install_completed','application_transport_passed']},indent=2))
