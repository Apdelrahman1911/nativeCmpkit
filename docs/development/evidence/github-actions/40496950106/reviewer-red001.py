"""Independent immutable UIKit121-case/12-required-method artifact review; no execution."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,importlib.util,json,plistlib,re,shutil,stat,subprocess,sys,tempfile,zipfile
ROOT=Path('/root/projects/nativeCmpKit');TMP=Path(__file__).parent;OUT=TMP/'review-archive'
REV='8ab48555a30d8fe2dbf6f422a6f2cf1bd2423c8f';REPO='Apdelrahman1911/nativeCmpkit';RUN=40496950106;JOB=122164948388;ART=12731864104

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
job=next(j for j in jobs if j['id']==JOB);assert job['name']=='library-tests (ios-iphone)' and job['conclusion']=='failure'
assert next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
assert next(j for j in jobs if j['name']=='consumer-core-io')['conclusion']=='skipped'
assert len(arts)==1;art=arts[0];raw=(TMP/f'{ART}.zip').read_bytes()
assert art['id']==ART and not art['expired'] and art['workflow_run']['head_sha']==REV and art['workflow_run']['id']==RUN
assert len(raw)==art['size_in_bytes']==111859 and 'sha256:'+sha(raw)==art['digest']
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
 inputs=lt.snapshot_inputs(view);assert len(inputs)==719
 plan=lt.plan(view,'ios',only_modules=('calf-ui',));assert len(plan['modules'])==1
 with zipfile.ZipFile(TMP/f'{ART}.zip') as z:
  infos=z.infolist();names=[i.filename for i in infos]
  assert len(names)==len(set(names))==35 and sum(i.file_size for i in infos)<64*1024**2
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
  for report in module['reports']:
   payload=z.read(report['path']);assert sha(payload)==report['sha256']
   parsed=lt.junit_cases(payload);assert all(report[k]==v for k,v in lt.case_counts(parsed).items());cases.extend(parsed)
   if report['failures']:
    import xml.etree.ElementTree as ET
    root=ET.fromstring(payload)
    for case in root.iter('testcase'):
     for failure in case.findall('failure'):
      assert failure.attrib['type']=='kotlin.NoSuchElementException' and 'List is empty.' in (failure.text or '')
      failures.append({'classname':case.attrib['classname'],'name':case.attrib['name'],'message':failure.attrib['message'],'failure_payload_sha256':sha((failure.text or '').encode())})
  assert set(xmls)=={r['path'] for r in module['reports']}
  assert len({(c['classname'],c['name']) for c in cases})==len(cases)
  order=lambda c:(c['classname'],c['name']);assert sorted(cases,key=order)==sorted(module['testcases'],key=order)
  totals=lt.case_counts(cases);assert totals==receipt['totals']=={'tests':121,'failures':2,'errors':0,'skipped':0,'passed':119,'executed':121,'not_applicable':0,'unexpected_skipped':0}
  failed=[c for c in cases if c['status']!='passed']
  expected_failed={('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.dropdown.NativeDropDownLifecycleTest','expandedStateControlsActualMenuAndDismissalIsNotReportedAtOpen[iosSimulatorArm64]'),('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.timepicker.NativeTimePickerTest','replacingStateReplacesTheNativeOwnerAndNeverWritesToOldState[iosSimulatorArm64]')}
  assert {(c['classname'],c['name']) for c in failed}==expected_failed and len(failures)==2
  required={('iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.'+cls,name+'[iosSimulatorArm64]') for cls,name in lt.IOS_APPLICATION_CASES}
  observed={(c['classname'],c['name']) for c in cases};assert len(required)==12 and required<=observed
  mandatory=[c for c in cases if (c['classname'],c['name']) in required];assert lt.case_counts(mandatory)['passed']==10
  app_paths=[n for n in names if '/native-ui-application/' in n];assert len(app_paths)==1;app_path=app_paths[0];app=get(app_path)
  token=PurePosixPath(app_path).parent.name;assert re.fullmatch('[0-9a-f]{32}',token)
  assert app['bundle_id']==f'io.github.apdelrahman1911.nativecmpkit.verification.ui.r{REV[:12]}.t{token}'
  assert app['source_revision']==REV and app['source_tree_dirty'] is False and app['transport_passed'] is True and 'error' not in app
  protocol=app['application_protocol'];assert protocol['activation']=={'main_worker':1,'owned_worker':2}
  assert protocol['completion']=={'runner_exit':0,'worker_terminated':True} and protocol['process_exit']==0 and protocol['counts']==totals
  assert 0<protocol['stream_bytes']<64*1024**2 and 0<protocol['elapsed_seconds']<1800
  normalized=[{'classname':c['classname'].removeprefix('iosSimulatorArm64ApplicationTest.'),'name':c['name'].removesuffix('[iosSimulatorArm64]'),'status':c['status']} for c in cases]
  assert sorted(normalized,key=order)==sorted(protocol['testcases'],key=order)
  assert len({(c['classname'],c['name']) for c in protocol['testcases']})==121
  application=receipt['ios_applications'];assert len(application)==1 and application[0]['protocol_xml_agreement'] is True and application[0]['required_native_cases_found']==12
  assert application[0]['receipt_path']==app_path and application[0]['receipt_sha256']==sha(z.read(app_path)) and application[0]['counts']==totals
  assert receipt['errors']==[{'module':'calf-ui','error':'Failed, errored or unexpected skipped tests are not accepted by this verification gate'}] and receipt['passed'] is False
  for stamp in (app['started_at_utc'],app['finished_at_utc']):assert dt.datetime.fromisoformat(stamp.replace('Z','+00:00')).utcoffset() is not None
  for runtime_app in (app['runtime_before'],app['runtime_after']):
   assert runtime_app['source_revision']==REV and runtime_app['source_tree_dirty'] is False
   assert all(runtime_app.get(k)==runtime.get(k) for k in ('host','java','rust','simulator','xcode','compiler_runtime_fingerprint'))
  assert app['binary_sha256']==app['binary_sha256_after']==application[0]['binary_sha256']
  assert app['macho']=={'architecture':'arm64','file_type':'executable','minimum_os':'15.0.0','platform':7,'sdk':'26.4.0'}
  for k in ('binary_sha256','signed_application_executable_sha256','application_plist_sha256'):assert re.fullmatch('[0-9a-f]{64}',app[k])
  plist=original_app.app_information(app['bundle_id'],app['macho']['minimum_os'])
  assert plist['CADisableMinimumFrameDurationOnPhone'] is True and type(plist['CADisableMinimumFrameDurationOnPhone']) is bool
  assert sha(plistlib.dumps(plist,sort_keys=True))==app['application_plist_sha256']
  steps=app['steps'];assert steps['foreign-app-preflight']['preexisting_app_absence_verified'] is True
  assert steps['adhoc-sign-local-verification-app']['exit_code']==0 and steps['adhoc-sign-local-verification-app']['remote_signing_or_publication'] is False
  assert steps['install-owned-app']['exit_code']==0 and steps['install-owned-app']['installed_owned_bytes_verified'] is True
  assert all(app['cleanup'][k] is True for k in ('owned_app_identity_reverified','owned_app_stopped_verified','owned_app_absence_verified','owned_local_bundle_removed'))
  assert app['cleanup']['uninstall_exit_code']==0
  assert app['packages_published'] is False and app['release_readiness_certified'] is False
  key=get('build/ci-runtime/library-dependencies.json');selected=keys.selected_inputs(view,'library')
  assert key['inputs']==selected and key['dependency_inputs_sha256']==keys.fingerprint('library',selected) and key['source_revision']==REV
log=(TMP/'job-log.log').read_bytes();lines=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ','',s) for s in log.decode('utf-8-sig').splitlines()]
assert 'NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2' in lines
assert 'NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true' in lines
assert not any('The presentation controller of an alert controller presenting as an alert must not have its delegate modified' in s for s in lines)
assert sum('NativeDropDownLifecycleTest.expandedStateControlsActualMenuAndDismissalIsNotReportedAtOpen' in s and ' FAILED' in s for s in lines)==1
assert sum('NativeTimePickerTest.replacingStateReplacesTheNativeOwnerAndNeverWritesToOldState' in s and ' FAILED' in s for s in lines)==1
native_locations=[]
for path,match in [('calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dropdown/NativeDropDownLifecycleTest.kt','button = parent.view.menuButtons().single()'),('calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/timepicker/NativeTimePickerTest.kt','oldPicker = parent.view.datePickers().single()')]:
 text=blob(path).decode();assert match in text
 native_locations += [{'path':path,'lines':i+1,'symbol':match,'code':line.strip()} for i,line in enumerate(text.splitlines()) if match in line]
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'run_attempt':1,'source_revision':REV,'url':run['html_url'],'run_conclusion':'failure','job_id':JOB,'job_url':job['html_url'],
 'evidence_integrity_passed':True,'artifact_id':ART,'artifact_bytes':len(raw),'artifact_digest':art['digest'],'artifact_members':names,'source_input_count':len(inputs),'source_inputs_sha256':lt.input_digest(inputs),'all_inputs_reconstructed_from_Git_and_before_after_match':True,
 'actual_xml_reports':len(xmls),'totals':totals,'failed_testcases':failed,'failure_details':failures,'mandatory_application_methods':12,'mandatory_methods_observed':12,'mandatory_methods_passed':10,'mandatory_methods_missing':[],'mandatory_testcases':mandatory,
 'execution':receipt['execution'],'command':receipt['command'],'runtime':runtime,'independently_recomputed_dependency_key':key['dependency_inputs_sha256'],'application_receipt_path':app_path,'application_macho':app['macho'],'reconstructed_original_plist_Boolean_and_hash_match':True,
 'actual_activation_observed':protocol['activation'],'application_completion_observed':protocol['completion'],'protocol_and_raw_XML_agree':True,'application_transport_passed':True,'application_cleanup':app['cleanup'],
 'confirmed_failure':'Actual dropdown and time-picker application cases throw NoSuchElementException: List is empty during their first native subtree lookup, before their intended menu/replacement assertions. Both use composition idle then immediate single() on UIKitView subtrees. A deferred render/interop transaction is a source-supported timing hypothesis, not proven: retain native-view presence/attachment/ownership and all functionality assertions, await real unique subtree readiness with bounded failure diagnostics, then rerun immutable simulator execution.',
 'native_fixture_locations':native_locations,'positive_observation':'All four alert lifecycle methods and all four application-host methods pass. Previous prohibited Alert delegate assertion is not observed. Exactly twelve named application methods execute, ten pass. There are121 total methods, not121 new native-presentation scenarios.',
 'bounded_actual_job_diagnostics':{'log_bytes':len(log),'log_sha256':sha(log),'full_log_archived':False},
 'limits':['Uploaded JSON/XML are original reports, not native executable/SDK bytes; recorded signed/binary hashes cannot independently re-read unavailable payloads. Plist content/hash is independently reconstructed from Git.','Only genuine iPhone26.5 simulator application; physical-device/iPad/oldest-iOS/native-device/resource/ABI/consumer/legal/security/release gates are not certified.','Composition idle is not proof that a deferred UIKit interop insertion has committed; no silent skip, mock substitution or arbitrary time-based success.'],
 'issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':sha(Path(__file__))}
(OUT/'raw').mkdir(parents=True)
for n in ('run-final.json','jobs-final.json','artifacts-final.json','collection.json'):shutil.copyfile(TMP/n,OUT/n)
(OUT/'raw'/f'{ART}.zip').write_bytes(raw);shutil.copyfile(Path(__file__),OUT/'lead-review.py')
with (OUT/'lead-independent-review.json').open('x') as f:json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file()))
print(json.dumps({k:review[k] for k in ('run_id','evidence_integrity_passed','source_input_count','actual_xml_reports','totals','mandatory_methods_passed','application_transport_passed')},indent=2))
