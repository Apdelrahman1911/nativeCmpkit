from collections import Counter
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,json,re,stat,subprocess,sys,zipfile
ROOT=Path('/root/projects/nativeCmpKit'); OUT=Path(__file__).parent
SOURCE=Path('/dev/shm/nativecmpkit-ci-android-webview-4fb7d886-20261027/40598826221')
SHA='4fb7d886d533610c7e4bf55535ea980ff050a144'; RUN=40598826221
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests as lt,runtime_context as rc,dependency_cache_inputs as dc
def digest(b):return hashlib.sha256(b).hexdigest()
def doc(b):
 def unique(pairs):
  d={}
  for k,v in pairs:
   assert k not in d,'Duplicate JSON key';d[k]=v
  return d
 return json.loads(b,object_pairs_hook=unique)
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
run=doc((SOURCE/'run-final.json').read_bytes());jobs=doc((SOURCE/'jobs-final.json').read_bytes())['jobs'];artifacts=doc((SOURCE/'artifacts-final.json').read_bytes())['artifacts']
assert run['id']==RUN and run['head_sha']==SHA and run['repository']['full_name']=='Apdelrahman1911/nativeCmpkit'
assert run['event']=='workflow_dispatch' and run['run_attempt']==1 and run['status']=='completed' and run['conclusion']=='success'
selected=[j for j in jobs if j['name'].startswith('library-tests (')];assert len(selected)==1
job=selected[0];assert job['name']=='library-tests (android-device-api35, android-device, ubuntu-24.04, x64, python3, 35, calf-webview)' and job['conclusion']=='success'
assert next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
assert next(j for j in jobs if j['name']=='consumer-core-io')['conclusion']=='skipped'
assert len(artifacts)==1;a=artifacts[0];assert a['name']=='library-evidence-android-device-api35' and not a['expired'] and a['workflow_run']['head_sha']==SHA
p=SOURCE/(str(a['id'])+'.zip');assert p.stat().st_size==a['size_in_bytes'] and 'sha256:'+digest(p.read_bytes())==a['digest']
inputs=lt.snapshot_inputs(ROOT);assert len(inputs)==734
for name,value in inputs.items():assert digest(git('show',SHA+':'+name))==value, name
plan=lt.plan(ROOT,'android-device',only_modules=('calf-webview',));assert len(plan['expected'])==1
expected=plan['expected'][0];authored=[]
for name in expected['test_source_files']:
 text=(ROOT/name).read_text();matches=re.findall(r'@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(',text)
 assert len(matches)==len(re.findall(r'@Test\b',text));authored+=matches
assert len(authored)==25
with zipfile.ZipFile(p) as z:
 names=z.namelist();assert len(names)==len(set(names))==18 and sum(e.file_size for e in z.infolist())<64*1024**2
 for e in z.infolist():
  name=PurePosixPath(e.filename)
  assert not name.is_absolute() and not {'.','..'}&set(name.parts) and '\\' not in e.filename
  assert not e.is_dir() and not e.flag_bits&1 and stat.S_IFMT(e.external_attr>>16) in {0,stat.S_IFREG}
  assert e.filename.endswith(('.json','.xml')) and e.file_size<=lt.MAX_REPORT_BYTES
 def get(n):return doc(z.read(n))
 base='build/ci-verification/android-device-api35/';receipt=get(base+'library/receipt.json');controller=get(base+'controller.json')
 assert get(base+'library/inputs-before.json')==get(base+'library/inputs-after.json')==get(base+'inputs-before.json')==get(base+'inputs-after.json')==inputs
 assert receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(inputs)
 for item in (receipt,controller):assert item['source_revision']==item['source_revision_after']==SHA and not item['source_tree_dirty'] and not item['changed_inputs'] and item['passed']
 assert not controller['packages_published'] and not controller['release_readiness_certified'] and controller['test_suite_passed']
 assert controller['emulator_shutdown']['clean_shutdown'] and controller['emulator_shutdown']['exit_code']==0 and not controller['emulator_shutdown']['forced_owned_group']
 assert all(s['exit_code']==0 for s in controller['setup_stages'].values())
 assert get(base+'library/plan.json')==get('build/ci-plan/plan.json')==plan
 assert receipt['command']==lt.gradle_command('android-device',plan,root=ROOT,android_serial='emulator-5588')
 assert receipt['execution']['exit_code']==0 and not receipt['execution'].get('stop_reason') and not receipt['errors']
 assert receipt['task_execution_markers']=={':calf-webview:connectedAndroidDeviceTest':1} and not receipt['quarantined_prior_reports'] and not receipt['uncovered']
 runtime=get(base+'library/runtime.json');actual=get('build/ci-runtime/actual.json');boot=get(base+'boot.json');assets=get(base+'sdk-assets.json')
 assert receipt['runtime_receipt_sha256']==digest(z.read(base+'library/runtime.json'))
 for value in (runtime,actual):
  assert value['source_revision']==SHA and not value['source_tree_dirty'] and value['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(value)
  assert value['android_platform']['package']=='platforms;android-37.0' and value['host']['system']=='Linux' and value['host']['architecture']=='x64' and value['java']['major']==17
 assert runtime['android_emulator']==boot==receipt['android_emulator_after']
 assert boot=={'abi':'x86_64','api_level':'35','boot_completed':'1','release':'15','selinux':'Enforcing','serial':'emulator-5588'}
 assert {k:runtime[k] for k in runtime if k not in {'observed_at_utc','compiler_runtime_fingerprint','android_emulator'}}=={k:actual[k] for k in actual if k not in {'observed_at_utc','compiler_runtime_fingerprint'}}
 deps=get('build/ci-runtime/library-dependencies.json');assert deps['inputs']==dc.selected_inputs(ROOT,'libraries') and deps['selected_modules']==['calf-webview'] and not deps['compiled_or_test_results_reused']
 assert deps['dependency_inputs_sha256']==dc.fingerprint('libraries',deps['inputs'])
 module=receipt['modules'][0];assert len(receipt['modules'])==1 and module['module']=='calf-webview'
 reports=module['reports'];assert len(reports)==1 and {r['path'] for r in reports}=={n for n in names if n.endswith('.xml')}
 cases=[]
 for report in reports:
  raw=z.read(report['path']);assert digest(raw)==report['sha256']
  found=lt.junit_cases(raw);counts=lt.case_counts(found);assert all(report[k]==v for k,v in counts.items());cases+=found
 assert len(cases)==len({(c['classname'],c['name']) for c in cases})==25 and all(c['status']=='passed' for c in cases)
 assert Counter(c['name'] for c in cases)==Counter(authored)
 assert sorted(cases,key=lambda c:(c['classname'],c['name']))==sorted(module['testcases'],key=lambda c:(c['classname'],c['name']))
 totals=lt.case_counts(cases);assert totals==receipt['totals']==controller['test_totals']
 native=[c for c in cases if c['classname']=='com.mohamedrejeb.calf.ui.web.AndroidWebViewHistoryDeviceTest'];assert len(native)==1 and native[0]['name']=='navigatorReplacementReadsRealBrowserHistoryWithoutAnotherPageEvent'
 # Read owning actual source and unweakened fixture, not just testcase names.
 production=(ROOT/'calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt').read_text()
 assert 'LaunchedEffect(view, navigator)' in production and 'consumeNavigationEvents(onAttached = {' in production
 assert 'canGoBack = webView.canGoBack()' in production and 'canGoForward = webView.canGoForward()' in production
 fixture=(ROOT/expected['test_source_files'][0]).read_text()
 for predicate in ['https://nativecmpkit.invalid/fixture','shouldInterceptRequest','performTouchInput { click(center) }','assertEquals(3, history.size','assertEquals(2, history.currentIndex)','assertEquals("true",','assertSame(native, state.webView)','assertEquals(1, created)','assertEquals(0, disposed)','assertTrue(replacement.canGoBack)','assertTrue(replacement.canGoForward)','assertEquals("\\\"#first\\\"",']:
  assert predicate in fixture,predicate
 init=(ROOT/'scripts/ci/fresh-tests.init.gradle.kts').read_text();assert 'Connected device verification requires fresh execution' in init and 'outputs.upToDateWhen { false }' in init and 'setIgnoreFailures' in init
 summary={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'run_id':RUN,'run_url':run['html_url'],'source_revision':SHA,'current_documentation_revision':git('rev-parse','HEAD').decode().strip(),'all_734_inputs_equal_exact_own_Git':True,'selected_input_digest':lt.input_digest(inputs),'artifact_id':a['id'],'artifact_digest':a['digest'],'job_id':job['id'],'command':receipt['command'],'execution':receipt['execution'],'assembly':controller['setup_stages']['apk-assembly'],'totals':totals,'reports':reports,'actual_native_case':native[0],'all_25_authored_methods_matched_fresh_XML':True,'actual_runtime':runtime,'setup_runtime':actual,'runtime_scope_difference':'Actual-test context additionally fingerprints the owned API35 emulator; all shared host/SDK fields match. Different global fingerprints are expected, not a failed equality.','sdk_assets':assets,'emulator_clean_shutdown':controller['emulator_shutdown'],'accepted_gap':'Actual Android Compose/Chromium native history restoration and navigator replacement on an enforcing API35 emulator; native URL page, real user activation, native index1/size3, actual DOM #first, no native view recreation.','limits':['25 target executions:24 common methods plus1 actual native integration; not25 independent native scenarios.','Exact WebView-provider version was not recorded; real installed provider execution is established by actual Chromium DOM/history assertions.','Fresh private-child-log marker count is source-bound controller evidence, not an independent recount from public successful job logs.','No physical/minimum-device, provider/grants, JNI/Swift/API-ABI, memory profiler, legal/dependency, full consumer or release certification.','Original failed Android saver/hard-link and inline-history archives remain unchanged.'],'publication_performed':False,'release_readiness_certified':False}
(OUT/'lead-independent-review.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'passed':True,'run_id':RUN,'executed':25,'native_methods':1,'source_inputs':734,'emulator_shutdown':'clean'},indent=2))
