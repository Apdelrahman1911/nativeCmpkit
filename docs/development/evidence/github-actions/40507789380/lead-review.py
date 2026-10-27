"""Independent immutable UIKit process-interruption/raw-XML review; no execution."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,importlib.util,json,plistlib,re,shutil,stat,subprocess,sys,tempfile,zipfile
ROOT=Path('/root/projects/nativeCmpKit');TMP=Path(__file__).parent;OUT=TMP/'review-archive'
REV='8ab82a3fa41caad34cd7fb7a2d3722bfc25e3838';REPO='Apdelrahman1911/nativeCmpkit';RUN=40507789380;JOB=122201803933;ART=12737389835

def sha(p):return hashlib.sha256(p if isinstance(p,bytes) else p.read_bytes()).hexdigest()
def document(payload):
 def unique(pairs):
  result={}
  for k,v in pairs:assert k not in result;result[k]=v
  return result
 return json.loads(payload,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
assert not OUT.exists()
run=document((TMP/'run-final.json').read_bytes());jobs=document((TMP/'jobs-final.json').read_bytes())['jobs'];arts=document((TMP/'artifacts-final.json').read_bytes())['artifacts']
assert run['id']==RUN and run['head_sha']==REV and run['run_attempt']==1 and run['repository']['full_name']==REPO
assert run['status']=='completed' and run['conclusion']=='failure' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
job=next(j for j in jobs if j['id']==JOB);assert job['name']=='library-tests (ios-iphone, ios, macos-26, arm64, python3, iphone, calf-ui)' and job['conclusion']=='failure'
assert next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
assert next(j for j in jobs if j['name']=='consumer-core-io')['conclusion']=='skipped'
assert len(arts)==1;art=arts[0];raw=(TMP/f'{ART}.zip').read_bytes()
assert art['id']==ART and not art['expired'] and art['workflow_run']['head_sha']==REV and art['workflow_run']['id']==RUN
assert len(raw)==art['size_in_bytes'] and 'sha256:'+sha(raw)==art['digest']
records={}
for row in subprocess.check_output(['git','ls-tree','-rz',REV],cwd=ROOT).split(b'\0'):
 if row:meta,name=row.split(b'\t',1);records[name.decode()]=meta.decode().split()
def blob(name):
 mode,kind,oid=records[name];assert kind=='blob' and mode in {'100644','100755'}
 return subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-uikit8ab-review-',dir='/dev/shm') as directory:
 view=Path(directory)
 def materialize(name):
  p=view/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(name))
 materialize('settings.gradle.kts')
 for name in records:
  if name.startswith('scripts/ci/') or (name.startswith(('calf-','sample/')) and name.endswith('/build.gradle.kts')):materialize(name)
 sys.path.insert(0,str(view/'scripts/ci'))
 import library_tests as lt,dependency_cache_inputs as keys,ios_ui_application as original_app
 projects=lt.projects(view)
 prefixes=['gradle/','convention-plugins/','scripts/ci/','scripts/native/','kotlin-js-store/']
 prefixes += [f'{m}/{part}/' for m in projects for part in ('src','native','.cargo','gradle')]
 exact=set(lt.ROOT_INPUTS)|{f'{m}/{n}' for m in projects for n in ('build.gradle.kts','gradle.properties','gradle.lockfile')}
 exact|={n for n in records if n.startswith('sample/') and n.count('/')==2 and n.endswith('/build.gradle.kts')}
 for name in records:
  if (name in exact or any(name.startswith(p) for p in prefixes) or (name.startswith('sample/') and Path(name).name in keys.PROJECT_FILES)) and not set(PurePosixPath(name).parts[:-1])&lt.IGNORED_INPUT_DIRS:materialize(name)
 inputs=lt.snapshot_inputs(view);assert len(inputs)==720
 plan=lt.plan(view,'ios',only_modules=('calf-ui',));assert len(plan['expected'])==1
 with zipfile.ZipFile(TMP/f'{ART}.zip') as z:
  infos=z.infolist();names=[i.filename for i in infos]
  assert len(names)==len(set(names)) and len(names)<=64 and sum(i.file_size for i in infos)<64*1024**2
  for i in infos:
   p=PurePosixPath(i.filename)
   assert not p.is_absolute() and not {'.','..'}&set(p.parts) and '\\' not in i.filename
   assert not i.is_dir() and not i.flag_bits&1 and i.filename.endswith(('.json','.xml')) and i.file_size<=lt.MAX_REPORT_BYTES
   assert stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
  get=lambda n:document(z.read(n));base='build/ci-verification/ios-iphone/'
  receipt=get(base+'receipt.json');runtime=get(base+'runtime.json');module=receipt['modules'][0]
  assert get(base+'inputs-before.json')==get(base+'inputs-after.json')==inputs
  assert get(base+'plan.json')==get('build/ci-plan/plan.json')==plan
  assert receipt['source_revision']==receipt['source_revision_after']==REV and receipt['source_tree_dirty'] is False
  assert receipt['changed_inputs']==[] and receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(inputs)
  assert receipt['runtime_receipt_sha256']==sha(z.read(base+'runtime.json'))
  assert runtime['source_revision']==REV and runtime['source_tree_dirty'] is False
  assert runtime['host']['system']=='Darwin' and runtime['host']['architecture']=='arm64'
  assert runtime['java']['major']==17 and runtime['rust']['release']=='1.98.0' and runtime['simulator']['state']=='Booted'
  assert receipt['command']==lt.gradle_command('ios',plan,simulator=runtime['simulator']['udid'],root=view)
  assert receipt['execution']['exit_code']==1 and not receipt['execution'].get('stop_reason')
  assert receipt['quarantined_prior_reports']==[] and receipt['task_execution_markers']=={':calf-ui:iosSimulatorArm64ApplicationTest':1}
  xmls=[n for n in names if n.endswith('.xml')];assert len(xmls)==24 and len(receipt['modules'])==1
  cases=[];failures=[]
  import xml.etree.ElementTree as ET
  timestamps=[]
  for report in module['reports']:
   payload=z.read(report['path']);assert sha(payload)==report['sha256']
   parsed=lt.junit_cases(payload);assert all(report[k]==v for k,v in lt.case_counts(parsed).items());cases.extend(parsed)
   root=ET.fromstring(payload);timestamps.append({'path':report['path'],'timestamp':root.attrib.get('timestamp')})
   for case in root.iter('testcase'):
    for failure in case.findall('failure'):
     assert failure.attrib=={'message':'Unknown','type':'Unknown'} and not (failure.text or '').strip()
     failures.append({'classname':case.attrib['classname'],'name':case.attrib['name'],'time':case.attrib['time'],
                      'failure_attributes':failure.attrib,'failure_payload_sha256':sha((failure.text or '').encode()),
                      'failure_is_empty_KGP_process_interruption_not_an_inspected_Kotlin_assertion':True})
  assert set(xmls)=={r['path'] for r in module['reports']}
  assert len({(c['classname'],c['name']) for c in cases})==len(cases)
  order=lambda c:(c['classname'],c['name']);assert sorted(cases,key=order)==sorted(module['testcases'],key=order)
  totals=lt.case_counts(cases)
  assert totals==receipt['totals']=={'tests':121,'failures':1,'errors':0,'skipped':0,'passed':120,'executed':121,'not_applicable':0,'unexpected_skipped':0}
  failed=[c for c in cases if c['status']!='passed']
  expected_failed={('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.utils.UIImageConversionTest',
                    'returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected[iosSimulatorArm64]')}
  assert {(c['classname'],c['name']) for c in failed}==expected_failed and len(failures)==1
  required={('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.'+cls,name+'[iosSimulatorArm64]') for cls,name in lt.IOS_APPLICATION_CASES}
  assert len(required)==12 and required<={(c['classname'],c['name']) for c in cases}
  mandatory=[c for c in cases if (c['classname'],c['name']) in required]
  assert lt.case_counts(mandatory)['passed']==12
  state_cases=[c for c in cases if c['classname'].endswith('.TimePickerStateContractTest')]
  assert len(state_cases)==3 and all(c['status']=='passed' for c in state_cases)
  app_paths=[n for n in names if '/native-ui-application/' in n];assert len(app_paths)==1
  app_path=app_paths[0];app=get(app_path);token=PurePosixPath(app_path).parent.name
  assert re.fullmatch('[0-9a-f]{32}',token)
  assert app['bundle_id']==f'io.github.apdelrahman1911.nativecmpkit.verification.ui.r{REV[:12]}.t{token}'
  assert app['source_revision']==REV and app['source_tree_dirty'] is False and app['transport_passed'] is False
  assert app['error']=={'phase':'launch-and-real-test-transport','type':'ValueError'}
  assert app['application_protocol'] is None and receipt['ios_applications']==[]
  assert 'runtime_after' not in app and 'binary_sha256_after' not in app
  assert app['runtime_before']['source_revision']==REV and app['runtime_before']['source_tree_dirty'] is False
  assert all(app['runtime_before'].get(k)==runtime.get(k) for k in ('host','java','rust','simulator','xcode','compiler_runtime_fingerprint'))
  assert app['macho']=={'architecture':'arm64','file_type':'executable','minimum_os':'15.0.0','platform':7,'sdk':'26.4.0'}
  for k in ('binary_sha256','signed_application_executable_sha256','application_plist_sha256'):assert re.fullmatch('[0-9a-f]{64}',app[k])
  plist=original_app.app_information(app['bundle_id'],app['macho']['minimum_os'])
  assert plist['CFBundleName']=='NativeCmpKit library tests' and type(plist['CADisableMinimumFrameDurationOnPhone']) is bool and plist['CADisableMinimumFrameDurationOnPhone'] is True
  assert sha(plistlib.dumps(plist,sort_keys=True))==app['application_plist_sha256']
  steps=app['steps'];assert steps['foreign-app-preflight']['preexisting_app_absence_verified'] is True
  assert steps['adhoc-sign-local-verification-app']['exit_code']==0 and steps['adhoc-sign-local-verification-app']['remote_signing_or_publication'] is False
  assert steps['install-owned-app']['exit_code']==0 and steps['install-owned-app']['installed_owned_bytes_verified'] is True
  assert all(app['cleanup'][k] is True for k in ('owned_app_identity_reverified','owned_app_stopped_verified','owned_app_absence_verified','owned_local_bundle_removed'))
  assert app['cleanup']['uninstall_exit_code']==0 and app['cleanup']['terminate_exit_code']==3
  assert app['packages_published'] is False and app['release_readiness_certified'] is False
  assert receipt['passed'] is False and receipt['errors']==[
   {'module':'calf-ui','error':'Failed, errored or unexpected skipped tests are not accepted by this verification gate'},
   {'module':'calf-ui','error':'Genuine UIKit application evidence rejected','contract':'Application transport failed or incomplete','path':app_path}]
  diagnostics=get(base+'failure-diagnostics.json')
  assert diagnostics['full_logs_uploaded'] is False and diagnostics['test_success_inferred'] is False
  excerpts=[x for row in diagnostics['logs'] for x in row['excerpts']]
  assert any('Test running process exited unexpectedly.' in x['text'] and 'returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected' in x['text'] for x in excerpts)
  app_start=dt.datetime.fromisoformat(app['started_at_utc'].replace('Z','+00:00'))
  app_end=dt.datetime.fromisoformat(app['finished_at_utc'].replace('Z','+00:00'))
  assert 0<(app_end-app_start).total_seconds()<original_app.APP_TIMEOUT_SECONDS
  # Store literal XML times; the source-bound collector already checked fresh
  # filesystem mtimes. Do not invent a timezone on an absent XML offset.
  for row in timestamps:
   assert row['timestamp']
   value=dt.datetime.fromisoformat(row['timestamp'].replace('Z','+00:00'))
   row['timezone_explicit']=value.utcoffset() is not None
   if value.utcoffset() is not None:assert app_start<=value<=app_end
  key=get('build/ci-runtime/library-dependencies.json');selected=keys.selected_inputs(view,'libraries')
  assert key['inputs']==selected and key['dependency_inputs_sha256']==keys.fingerprint('libraries',selected) and key['source_revision']==REV
log=(TMP/'job-log.log').read_bytes()
lines=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ','',s) for s in log.decode('utf-8-sig').splitlines()]
assert lines.count('NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2')==1
assert not any(s.startswith('NATIVECMPKIT_UIKIT_COMPLETED') for s in lines)
assert sum('UIImageConversionTest.returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected' in s and ' FAILED' in s for s in lines)==1
assert not any('The presentation controller of an alert controller presenting as an alert must not have its delegate modified' in s for s in lines)
locations=[]
for path,tokens in [
 ('calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UIImageConversionTest.kt',
  ('returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected','GC.collect()')),
 ('scripts/ci/ios_ui_application.py',('receipt["application_protocol"] = forward_application','App crash/transport failure or missing complete native lifecycle')),
]:
 source=blob(path).decode()
 for number,line in enumerate(source.splitlines(),1):
  if any(token in line for token in tokens):locations.append({'path':path,'line':number,'code':line.strip()})
review={
 'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'run_attempt':1,'source_revision':REV,
 'url':run['html_url'],'run_conclusion':'failure','job_id':JOB,'job_url':job['html_url'],
 'evidence_integrity_passed':True,'artifact_id':ART,'artifact_bytes':len(raw),'artifact_digest':art['digest'],'artifact_members':names,
 'source_input_count':len(inputs),'source_inputs_sha256':lt.input_digest(inputs),'all_inputs_reconstructed_from_Git_and_before_after_match':True,
 'actual_xml_reports':len(xmls),'totals':totals,'failed_testcases':failed,'failure_details':failures,
 'mandatory_application_methods':12,'mandatory_methods_observed':12,'mandatory_methods_passed':12,'mandatory_methods_missing':[],
 'mandatory_testcases':mandatory,'fresh_time_state_model_cases_passed':state_cases,
 'execution':receipt['execution'],'command':receipt['command'],'runtime':runtime,
 'independently_recomputed_dependency_key':key['dependency_inputs_sha256'],'application_receipt_path':app_path,
 'application_macho':app['macho'],'reconstructed_current_NativeCmpKit_plist_Boolean_and_hash_match':True,
 'activation_observed_in_actual_job':{'main_worker':1,'owned_worker':2},'completion_marker_observed':False,
 'application_transport_passed':False,'complete_application_protocol_available':False,'protocol_and_raw_XML_agreement_certified':False,
 'application_error':app['error'],'application_cleanup':app['cleanup'],'app_started_utc':app['started_at_utc'],'app_finished_utc':app['finished_at_utc'],
 'literal_XML_timestamps':timestamps,'recorded_xml_mtimes_checked_by_source_bound_collector':True,
 'confirmed_result':'KGP freshly reports121 cases:120 pass, one active UIImage GC/lifetime case is marked failed/Unknown after the test process exits unexpectedly. All12 required application methods, including formerly failing dropdown and time-picker owner replacement, now pass. The application transport fails before runner/worker completion; this is not a successful native suite or proof that the interrupted method completed.',
 'root_cause':'Unverified. No Kotlin assertion, Apple crash diagnostic, native termination signal, watchdog code or stack was uploaded. The interrupted fixture invokes GC.collect on the runNativeUiTest main-thread callback after prior genuine native menu/time-picker use; memory lifetime, runtime GC/threading, OS termination and unrelated native resource cleanup remain hypotheses, not confirmed causes.',
 'next_required_evidence':'Retain all20 forced collections, native pixel/hash equality and allocation/release assertions. Add narrowly owner-bound process/protocol/crash diagnostics without raw private crash reports, then execute immutable native CI. Do not skip, increase deadlines, weaken SELinux/GC/ownership checks or claim a buffer use-after-free from Unknown alone.',
 'source_locations':locations,'bounded_actual_job_diagnostics':{'log_bytes':len(log),'log_sha256':sha(log),'full_log_archived':False},
 'limits':[
  'This is genuine iPhone26.5 simulator activation and raw fresh testcase evidence, not a completed application lifecycle. All12 required methods pass but cannot waive the interrupted GC method or missing transport completion.',
  'One failed/Unknown KGP active-test report is process-interruption evidence, not an inspected failing Kotlin assertion or a confirmed native memory exploit.',
  'The original JSON/XML archive excludes executables, private Apple diagnostic logs and raw producer logs; recorded native payload hashes cannot independently re-read unavailable bytes.',
  'No physical device/iPad/minimum-iOS/ASan/Instruments/API-ABI/consumer/legal/dependency/release gate is certified.',
 ],
 'issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,
 'review_script_sha256':sha(Path(__file__)),
}
(OUT/'raw').mkdir(parents=True)
for n in ('run-final.json','jobs-final.json','artifacts-final.json','collection.json'):shutil.copyfile(TMP/n,OUT/n)
(OUT/'raw'/f'{ART}.zip').write_bytes(raw);shutil.copyfile(Path(__file__),OUT/'lead-review.py')
with (OUT/'lead-independent-review.json').open('x') as f:json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file()))
print(json.dumps({k:review[k] for k in ('run_id','evidence_integrity_passed','source_input_count','actual_xml_reports','totals','mandatory_methods_passed','application_transport_passed')},indent=2))
