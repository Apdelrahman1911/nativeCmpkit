"""Lead's read-only source/ZIP/XML recount for the contained verification checkpoint.
No network or execution of archived code. Run ID/profile are explicit arguments.
Not a release or platform-behavior certification.
"""
from collections import Counter
import datetime as dt
import hashlib,json,os,re,subprocess,sys,tempfile,zipfile,stat
import xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath
root=Path('/root/projects/nativeCmpKit');sys.path.insert(0,str(root/'scripts/ci'))
import library_tests as lt,native_test_policy as np,workflow_matrix as wm
import dependency_cache_inputs as keys,runtime_context as rc
out=Path(__file__).parent;profile='windows'
run=json.loads((out/'run-final.json').read_text());jobs=json.loads((out/'jobs-final.json').read_text())['jobs']
artifacts=json.loads((out/'artifacts-final.json').read_text())['artifacts'];revision=run['head_sha']
assert re.fullmatch('[0-9a-f]{40}',revision)
assert run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
assert run['repository']['full_name']=='Apdelrahman1911/nativeCmpkit'
assert run['id']==40568592687 and revision=='c9ffacde892cfecd3d2784b22dbad7731490c6fc' and run['run_attempt']==1
assert run['status']=='completed' and run['conclusion']=='success'
assert len(jobs)==3 and next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
assert next(j for j in jobs if j['name']=='consumer-core-io')['conclusion']=='skipped'
# Materialize only inert, commit-bound build/source inputs to independently plan/recount.
records={}
for row in subprocess.check_output(['git','ls-tree','-rz',revision],cwd=root).split(b'\0'):
 if not row:continue
 metadata,name=row.split(b'\t',1);mode,kind,oid=metadata.decode().split();records[name.decode()] = (mode,kind,oid)
def blob(name):
 mode,kind,oid=records[name];assert kind=='blob' and mode in ('100644','100755')
 return subprocess.check_output(['git','cat-file','blob',oid],cwd=root)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-c9ff-windows-review-',dir='/dev/shm') as temp:
 view=Path(temp)
 def materialize(name):
  p=view/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(name))
 materialize('settings.gradle.kts')
 for name in records:
  if name.startswith(('calf-','sample/')) and name.endswith('/build.gradle.kts'):materialize(name)
 projects=lt.projects(view)
 prefixes=['gradle/','convention-plugins/','scripts/ci/','scripts/native/','kotlin-js-store/']
 prefixes += [f'{module}/{folder}/' for module in projects for folder in ('src','native','.cargo','gradle')]
 exact=set(lt.ROOT_INPUTS)|{f'{module}/{n}' for module in projects for n in ('build.gradle.kts','gradle.properties','gradle.lockfile')}
 exact|={name for name in records if name.startswith('sample/') and name.count('/')==2 and name.endswith('/build.gradle.kts')}
 for name in records:
  if (name in exact or any(name.startswith(p) for p in prefixes) or (name.startswith('sample/') and Path(name).name in keys.PROJECT_FILES)) and not set(PurePosixPath(name).parts[:-1])&lt.IGNORED_INPUT_DIRS:materialize(name)
 expected_inputs=lt.snapshot_inputs(view)
 assert len(expected_inputs)==726
 for name in ('library_tests.py','native_test_policy.py','workflow_matrix.py','dependency_cache_inputs.py','runtime_context.py'):
  assert (root/'scripts/ci'/name).read_bytes()==blob('scripts/ci/'+name), 'Current imported reviewer helper differs from this immutable run'
 dep_inputs=keys.selected_inputs(view,'libraries');dep_digest=keys.fingerprint('libraries',dep_inputs)
 selection=keys.selection_contract(view,'')
 reviewed=[]
 for slot in wm.matrix(profile)['include']:
  matching=[a for a in artifacts if a['name']=='library-evidence-'+slot['slot']]
  assert len(matching)==1,'Missing or duplicate selected-slot evidence'
  artifact=matching[0];assert artifact['id']==12764597746 and len(artifacts)==1
  assert artifact['workflow_run']['id']==run['id'] and artifact['workflow_run']['head_sha']==revision
  p=out/f"{artifact['id']}.zip";payload=p.read_bytes()
  assert len(payload)<=64*1024*1024 and len(payload)==artifact['size_in_bytes'] and not artifact['expired']
  digest='sha256:'+hashlib.sha256(payload).hexdigest();assert artifact['digest']==digest
  with zipfile.ZipFile(p) as archive:
   members=archive.infolist();assert len(members)==87 and sum(i.file_size for i in members)<=64*1024*1024
   names=[i.filename for i in members];assert len(names)==len(set(names))
   for i in members:
    path=PurePosixPath(i.filename)
    assert not path.is_absolute() and not set(path.parts)&{'.','..'} and '\\' not in i.filename
    assert not i.is_dir() and i.file_size<=lt.MAX_REPORT_BYTES and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG) and not i.flag_bits&1
    assert i.filename.endswith(('.json','.xml')),'Non-evidence payload must not be uploaded'
   def doc(name):
    def unique(pairs):
     obj={}
     for k,v in pairs:assert k not in obj;obj[k]=v
     return obj
    return json.loads(archive.read(name),object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
   def instant(s):
    value=dt.datetime.fromisoformat(s.replace('Z','+00:00'));assert value.utcoffset() is not None;return value
   base='build/ci-verification/'+slot['slot']+'/'
   receipt=doc(base+'receipt.json');before=doc(base+'inputs-before.json');after=doc(base+'inputs-after.json')
   assert before==after==expected_inputs
   assert receipt['source_revision']==receipt['source_revision_after']==revision and receipt['source_tree_dirty'] is False
   assert not receipt.get('changed_inputs') and not receipt.get('input_capture_error')
   assert receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(expected_inputs)
   dep=doc('build/ci-runtime/library-dependencies.json');actual=doc('build/ci-runtime/actual.json')
   assert dep['inputs']==dep_inputs and dep['dependency_input_count']==len(dep_inputs) and dep['dependency_inputs_sha256']==dep_digest
   assert dep['source_revision']==revision and dep['selection_cache_key']==selection['cache_key']=='all' and dep['selected_modules']==[]
   assert not dep['compiled_or_test_results_reused'] and not dep['ordinary_dependency_trust_certified'] and not dep['release_readiness_certified']
   runtime=doc(base+'runtime.json');assert runtime['source_revision']==revision and not runtime['source_tree_dirty']
   assert receipt['runtime_receipt_sha256']==hashlib.sha256(archive.read(base+'runtime.json')).hexdigest()
   assert runtime['host']['system']=='Windows' and runtime['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(runtime)
   assert actual['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(actual)
   assert actual['android_platform']['package']=='platforms;android-37.0' and 'android_platform' not in runtime
   context_differences={k for k in set(actual)|set(runtime) if actual.get(k)!=runtime.get(k)}
   assert context_differences=={'observed_at_utc','android_platform','compiler_runtime_fingerprint'}
   # Preserve the exact richer setup SDK observation; do not fake a during-test SDK binding.
   sdk_capture_limit={'setup_android_platform':actual['android_platform'],'test_capture_android_platform':None,'setup_fingerprint':actual['compiler_runtime_fingerprint'],'test_fingerprint':runtime['compiler_runtime_fingerprint'],'all_other_runtime_fields_identical':True,'during_test_SDK_identity_reverified':False}
   assert actual['source_revision']==revision and not actual['source_tree_dirty']
   assert runtime['host']['architecture']==slot['arch'] and runtime['java']['major']==17 and runtime['rust']['release']=='1.98.0'
   plan=lt.plan(view,slot['suite'], only_modules=tuple(slot['test-modules'].split(',')) if slot.get('test-modules') else None);assert plan==doc(base+'plan.json')==doc('build/ci-plan/plan.json')
   assert receipt['complete_suite_requested']==plan['complete_suite_requested']
   assert receipt['explicit_module_subset']==plan['explicit_module_subset']
   assert receipt['test_bearing_modules_not_requested']==plan['test_bearing_modules_not_requested']==[]
   assert len(plan['expected'])==21 and receipt['complete_suite_requested'] is True and receipt['explicit_module_subset']==[]
   assert receipt['uncovered']==plan['uncovered']==[] and receipt['quarantined_prior_reports']==[] and receipt['ios_applications']==[]
   assert receipt['task_execution_markers']=={m['task']:1 for m in plan['expected']}
   start=instant(receipt['started_at_utc']);end=instant(receipt['finished_at_utc']);assert start<end
   simulator=runtime.get('simulator',{}).get('udid') if slot['suite']=='ios' else None
   command=lt.gradle_command(slot['suite'],plan,simulator,root=view)
   if runtime['host']['system']=='Windows':command[0]='.\\gradlew.bat'
   assert receipt['command']==command
   module_reviews=[];fresh_stamps=[];all_cases=[]
   for expected in plan['expected']:
    matches=[m for m in receipt['modules'] if m['module']==expected['module']];assert len(matches)==1
    module=matches[0];cases=[];keys=set();xmls=[]
    xml_names=[n for n in names if n.startswith(expected['report_directory']+'/') and PurePosixPath(n).name.startswith('TEST-') and n.endswith('.xml')]
    assert set(xml_names)=={r['path'] for r in module['reports']}
    # Failed/missing suites stay missing, never a pass. Review the failure receipt
    # and its zero cases while retaining exact source/digest/count comparisons.
    if not xml_names:
     assert not module['reports'] and not module['testcases']
     assert all(module[key]==0 for key in lt.case_counts([]))
     assert any(e['module']==expected['module'] and e['error']=='No actual non-skipped library testcases' for e in receipt['errors'])
     assert receipt['passed'] is False and receipt['execution']['exit_code']!=0
    for n in xml_names:
     data=archive.read(n);xml_cases=lt.junit_cases(data)
     xml=ET.fromstring(data,parser=ET.XMLParser(target=lt.NoDtdBuilder()));timestamp=xml.attrib['timestamp']
     assert start<=instant(timestamp)<=end
     fresh_stamps.append({'path':n,'timestamp':timestamp,'sha256':hashlib.sha256(data).hexdigest()})
     new_keys={(c['classname'],c['name']) for c in xml_cases}
     assert not keys&new_keys;keys|=new_keys;cases+=xml_cases
     recorded=next(r for r in module['reports'] if r['path']==n)
     assert recorded['sha256']==hashlib.sha256(data).hexdigest()
     xmls.append({'path':n,'sha256':recorded['sha256'],'cases':xml_cases})
    scenarios,errors=np.apply(expected['module'],slot['suite'],cases,runtime['host']['system'],slot.get('native-ui')=='true')
    assert not errors, (expected['module'], errors)
    assert sorted(cases,key=lambda c:(c['classname'],c['name']))==sorted(module['testcases'],key=lambda c:(c['classname'],c['name'])), expected['module']
    assert scenarios==module['native_scenarios'], expected['module']
    counts=lt.case_counts(cases)
    assert all(module[k]==v for k,v in counts.items())
    for xml in xmls:
     recorded=next(r for r in module['reports'] if r['path']==xml['path'])
     assert all(recorded[k]==v for k,v in lt.case_counts(xml['cases']).items())
    all_cases.extend(cases)
    module_reviews.append({'module':expected['module'],'task':expected['task'],'report_files':len(xml_names),'missing_suite':not bool(xml_names),**counts})
   counts={k:sum(m[k] for m in module_reviews) for k in receipt['totals']}
   assert counts==receipt['totals']
   assert receipt['passed']==(receipt['execution']['exit_code']==0 and not receipt['execution'].get('stop_reason') and not receipt['errors'])
   job_matches=[j for j in jobs if j['name'].startswith('library-tests ('+slot['slot']+',')];assert len(job_matches)==1
   job=job_matches[0];assert job['id']==122416871741 and job['run_attempt']==1 and job['status']=='completed' and job['conclusion']=='success'
   assert instant(job['started_at'])<=start<end<=instant(job['completed_at'])
   for name in ('Explicit dependency/compiler/runtime/slot-keyed cache','Source-set-aware expected library tests (never samples)','Fresh actual library suite with strict nonzero receipts','Keep receipts and actual selected-task XML only; never packages'):
    assert next(s for s in job['steps'] if s['name']==name)['conclusion']=='success'
   assert len(fresh_stamps)==79 and counts=={'tests':438,'failures':0,'errors':0,'skipped':1,'passed':437,'executed':437,'not_applicable':1,'unexpected_skipped':0}
   assert len(all_cases)==len({(c['classname'],c['name']) for c in all_cases})==438
   assert [(c['classname'],c['name']) for c in all_cases if c['status']=='skipped']==[('com.mohamedrejeb.calf.share.platform.NativeShareBridgeTest','macOsPickerCancellationReleasesRealMainThreadOwners[desktop]')]
   log=(out/'job-log.log').read_text();expected_key='nativecmpkit-deps-v2-Windows-X64-'+slot['slot']+'-desktop-all-'+actual['compiler_runtime_fingerprint']+'-'+dep_digest
   cache_misses=re.findall(r'Cache not found for input keys: ([^\r\n]+)',log);cache_saves=re.findall(r'Cache saved with key: ([^\r\n]+)',log)
   assert cache_misses==cache_saves==[expected_key] and 'Cache restored successfully' not in log
   old=root/'docs/development/evidence/github-actions/40417671294';old_arts=json.loads((old/'artifacts-final.json').read_bytes())['artifacts'];old_art=next(a for a in old_arts if a['name']==artifact['name'])
   old_payload=(old/'raw'/f"{old_art['id']}.zip").read_bytes();assert 'sha256:'+hashlib.sha256(old_payload).hexdigest()==old_art['digest']
   with zipfile.ZipFile(old/'raw'/f"{old_art['id']}.zip") as prior_zip:
    prior_cases=[c for n in prior_zip.namelist() if n.endswith('.xml') for c in lt.junit_cases(prior_zip.read(n))]
   prior_ids={(c['classname'],c['name']) for c in prior_cases};current_ids={(c['classname'],c['name']) for c in all_cases};assert len(prior_ids)==427 and prior_ids<current_ids and len(current_ids-prior_ids)==11
   current_by={(c['classname'],c['name']):c for c in all_cases};repaired=[{'classname':c['classname'],'name':c['name'],'prior_status':c['status'],'current_status':current_by[(c['classname'],c['name'])]['status']} for c in prior_cases if c['status']!='passed']
   assert sum(c['current_status']=='passed' for c in repaired)==5 and sum(c['current_status']=='skipped' for c in repaired)==1
   if receipt['passed']:assert job['conclusion']=='success'
   reviewed.append({'slot':slot['slot'],'job_id':job['id'],'job_url':job['html_url'],'job_conclusion':job['conclusion'],'suite':slot['suite'],'passed':receipt['passed'],'artifact_id':artifact['id'],'artifact_digest':digest,'source_input_count':len(expected_inputs),'source_inputs_sha256':lt.input_digest(expected_inputs),'runtime':runtime,'command':command,'execution':receipt['execution'],'totals':counts,'modules':module_reviews,'sdk_capture_limit':sdk_capture_limit,'native_scenarios':[c for m in receipt['modules'] for c in m['native_scenarios']],'xml_timestamps_and_hashes':fresh_stamps,'expected_cache_key':expected_key,'cache_observation':'exact key missed then saved; no hit claim','dependency_inputs_sha256':dep_digest,'prior_full_run':40417671294,'all_prior_427_testcase_identities_retained':True,'new_testcase_identities':sorted(current_ids-prior_ids),'formerly_failed_or_skipped':repaired,'report_files':sum(m['report_files'] for m in module_reviews),'scope':receipt['scope'],'complete_suite_requested':receipt['complete_suite_requested'],'explicit_module_subset':receipt['explicit_module_subset'],'test_bearing_modules_not_requested':receipt['test_bearing_modules_not_requested']})
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':run['id'],'run_attempt':run['run_attempt'],'url':run['html_url'],'profile':profile,'source_revision':revision,'run_conclusion':run['conclusion'],'evidence_integrity_passed':True,'runtime_slots':reviewed,'total_fresh_failed_executions':sum(x['totals']['failures'] for x in reviewed),'total_fresh_error_executions':sum(x['totals']['errors'] for x in reviewed),'total_missing_suites':sum(m['missing_suite'] for x in reviewed for m in x['modules']),'total_fresh_passed_executions':sum(x['totals']['passed'] for x in reviewed),'total_host_inapplicable_cases':sum(x['totals']['not_applicable'] for x in reviewed),'total_xml_reports':sum(x['report_files'] for x in reviewed),'limits':['Repeated target executions are not distinct test methods. The workflow setup captures the official Android SDK, while this old desktop runner context omits SDK metadata. Their independently recomputed fingerprints differ only for that scope; JDK/Rust/host/source match. During-test SDK equality is NOT certified; future owning capture repair requires new immutable execution.','The archive contains only uploaded reports/JSON, not producer or consumer packages. Native DLLs/JARs and raw child Gradle logs are not uploaded; exact fresh task markers and native payload hashes are source-bound controller/test assertions, not independent raw-byte/marker recount or genuine-parent/visible-dialog proof.','Source/XML/ZIP recount does not certify native feature parity, ABI, dependency trust, legal obligations or release readiness.'],'issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':lt.sha256(Path(__file__))}
(out/'lead-independent-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:review[k] for k in ('run_id','source_revision','run_conclusion','total_fresh_passed_executions','total_fresh_failed_executions','total_missing_suites','total_host_inapplicable_cases','total_xml_reports','evidence_integrity_passed')},indent=2))
