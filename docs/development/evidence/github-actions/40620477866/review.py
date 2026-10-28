"""Review actual cold builtin alias/SDK results, not compilation or managed-issue state."""
from pathlib import Path,PurePosixPath
from collections import Counter
import datetime as dt,hashlib,json,re,stat,subprocess,sys,zipfile,xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit');B=Path(__file__).parent;RUN=40620477866;D=B/str(RUN);SHA='35f04ca404fc575927dceb676dba1cd6b84cfc06';SLOT='android-host'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt,runtime_context as rc
run=json.loads((D/'run-final.json').read_text());jobs=json.loads((D/'jobs-final.json').read_text())['jobs'];arts=json.loads((D/'artifacts-final.json').read_text())['artifacts']
assert run['head_sha']==SHA and run['id']==RUN and run['status']=='completed' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening' and run['run_attempt']==1
assert len(arts)==1 and next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
inputs=lt.snapshot_inputs(ROOT);assert len(inputs)==744 and inputs==json.loads((B/'inputs-before-dispatch.json').read_text())
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);raw,_=p.communicate(''.join(SHA+':'+n+'\n' for n in inputs).encode());assert p.returncode==0;off=0;blobs={}
for n,h in inputs.items():
 e=raw.index(b'\n',off);head=raw[off:e].split();assert head[1]==b'blob';size=int(head[2]);data=raw[e+1:e+1+size];assert hashlib.sha256(data).hexdigest()==h,n;blobs[n]=data;off=e+size+2
assert off==len(raw)
fixture=blobs['calf-permissions/core/src/androidHostTest/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionAliasTest.kt'].decode()
assert fixture.count('@Config(sdk = [28, 32, 33]')==2 and 'nativecmpkit.alias.storagefirst' in fixture and 'nativecmpkit.alias.galleryfirst' in fixture
assert 'ReadStorage must not be initialized before this cold-order test' in fixture and 'Gallery must not be initialized before this cold-order test' in fixture
assert 'Initializing the first builtin must not accidentally initialize the other one' in fixture
assert 'val first = if (readStorageFirst) Permission.ReadStorage else Permission.Gallery' in fixture and 'val second = if (readStorageFirst) Permission.Gallery else Permission.ReadStorage' in fixture
assert 'exerciseAliasRequest(listOf(gallery)' in fixture and 'exerciseAliasRequest(listOf(storage, gallery)' in fixture
assert 'exerciseAliasRequest(listOf(customFirst, customSecond, customFirst)' in fixture
assert 'Never include an unrequested global alias' in fixture and 'Callback must retain the requested object identity' in fixture and 'Every requested alias must be refreshed before delivering the callback' in fixture
assert 'Actual delayed results must not be invented before native delivery' in fixture and 'host.registry.deliver(index' in fixture and 'for (index in 0..1)' in fixture
assert 'host.close()' in fixture and 'notRequired = sdk > 32' in fixture and 'PermissionAvailability.NotRequired' in fixture
helper=blobs['calf-permissions/core/src/androidHostTest/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionCompositionTest.kt'].decode()
assert 'Robolectric.buildActivity(Activity::class.java).setup()' in helper and 'contract.createIntent(activity, input)' in helper and 'dispatchResult(launch.requestCode, Activity.RESULT_OK, intent)' in helper
build=blobs['calf-permissions/core/build.gradle.kts'].decode();assert 'sourceSets.named("androidHostTest").dependencies' in build and 'implementation(projects.calfPermissions.calfPermissionsGallery)' in build
for n in ('calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt','calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRequestPlan.kt'):
 assert 'findByAndroidString' not in blobs[n].decode()
planner=blobs['calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRequestPlan.kt'].decode();assert 'permissions.distinct().associateWith(mapping)' in planner and 'entries.mapValues' in planner
source=json.loads((B/'robolectric-source-acquisition.json').read_text());jar=B/'robolectric-4.16.1-sources.jar';assert hashlib.sha256(jar.read_bytes()).hexdigest()==source['sha256']
with zipfile.ZipFile(jar) as z:
 robo=z.read('org/robolectric/RobolectricTestRunner.java').decode();sandbox=z.read('org/robolectric/internal/SandboxManager.java').decode()
 assert 'last.dontIncludeVariantMarkersInTestName()' in robo and 'sdkPicker.selectSdks(configuration, appManifest)' in robo and 'androidConfigurer.withConfig(builder, config)' in robo
 assert 'new SandboxKey(instrumentationConfig, sdk' in sandbox and 'Objects.equals(instrumentationConfiguration, that.instrumentationConfiguration)' in sandbox
methods={'AndroidStorageFirstAliasTest':'coldReadStorageThenGalleryReturnsOnlyRequestedLogicalIdentities','AndroidGalleryFirstAliasTest':'coldGalleryThenReadStorageReturnsOnlyRequestedLogicalIdentities'}
f=next(r for r in json.loads((ROOT/'docs/audit/findings/PERM.json').read_text()) if r['id']=='PERM-002');assert len(f['required_tests'])==3
instant=lambda s:dt.datetime.fromisoformat(s.replace('Z','+00:00'))
art=arts[0];assert art['name']=='library-evidence-'+SLOT and not art['expired'] and art['workflow_run']['head_sha']==SHA and art['workflow_run']['id']==RUN
z=D/(str(art['id'])+'.zip');assert z.stat().st_size==art['size_in_bytes']<64*1024**2 and 'sha256:'+hashlib.sha256(z.read_bytes()).hexdigest()==art['digest']
job=next(j for j in jobs if j['name'].startswith('library-tests ('+SLOT+','));assert job['status']=='completed' and job['run_attempt']==1
with zipfile.ZipFile(z) as a:
 entries=a.infolist();assert len(entries)==len({e.filename for e in entries}) and sum(e.file_size for e in entries)<64*1024**2
 for entry in entries:
  path=PurePosixPath(entry.filename);assert not path.is_absolute() and not {'.','..'}&set(path.parts) and '\\' not in entry.filename
  assert not entry.is_dir() and not entry.flag_bits&1 and stat.S_IFMT(entry.external_attr>>16) in (0,stat.S_IFREG)
  assert entry.filename.endswith(('.json','.xml')) and entry.file_size<16*1024**2
 base='build/ci-verification/'+SLOT+'/';rec=json.loads(a.read(base+'receipt.json'));rt=json.loads(a.read(base+'runtime.json'));setup=json.loads(a.read('build/ci-runtime/actual.json'))
 assert json.loads(a.read(base+'inputs-before.json'))==json.loads(a.read(base+'inputs-after.json'))==inputs
 assert rec['source_revision']==rec['source_revision_after']==SHA and not rec['source_tree_dirty'] and not rec['changed_inputs']
 assert rec['inputs_before_sha256']==rec['inputs_after_sha256']==lt.input_digest(inputs)
 plan=lt.plan(ROOT,'android-host',only_modules=('calf-permissions/core',));assert json.loads(a.read(base+'plan.json'))==json.loads(a.read('build/ci-plan/plan.json'))==plan
 assert rec['command']==lt.gradle_command('android-host',plan,root=ROOT) and rec['command'][-1]==':calf-permissions:calf-permissions-core:testAndroidHostTest'
 assert rec['explicit_module_subset']==['calf-permissions/core'] and not rec['complete_suite_requested']
 for k in ('host','java','rust','android_platform','compiler_runtime_fingerprint'):assert rt[k]==setup[k]
 assert rt['source_revision']==SHA and not rt['source_tree_dirty'] and rt['host']['system']=='Linux' and rt['host']['architecture']=='x64' and rt['java']['major']==17 and rt['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(rt)
 assert instant(job['started_at'])<=instant(rt['observed_at_utc'])<=instant(job['completed_at'])
 start,end=instant(rec['started_at_utc']),instant(rec['finished_at_utc']);assert instant(job['started_at'])<=start<end<=instant(job['completed_at'])
 expected=set()
 for n in plan['expected'][0]['test_source_files']:
  text=blobs[n].decode();ms=list(re.finditer(r'@Test\s*(?:@Suppress\([^\n]*\)\s*)?fun (`[^`\n]+`|[A-Za-z][A-Za-z0-9_]*)\(',text));assert len(ms)==len(re.findall(r'@Test\b',text))
  classes=list(re.finditer(r'^class ([A-Za-z][A-Za-z0-9_]*)',text,re.M))
  for m in ms:expected.add((next(c.group(1) for c in reversed(classes) if c.start()<m.start()),m.group(1).strip('`')))
 assert len(expected)==43
 xmls=[e.filename for e in entries if e.filename.endswith('.xml')];cases=[];aliascases=[];failures=[];reports=[]
 for n in xmls:
  data=a.read(n);assert b'<!DOCTYPE' not in data and b'<!ENTITY' not in data
  report=next(r for m in rec['modules'] for r in m['reports'] if r['path']==n);assert report['sha256']==hashlib.sha256(data).hexdigest()
  root=E.fromstring(data);assert start<=instant(root.attrib['timestamp'])<=end
  cs=root.findall('.//testcase');reports.append({'path':n,'sha256':report['sha256'],'testcases':len(cs)})
  for c in cs:
   name=c.get('name');cls=c.get('classname').split('.')[-1];method=name.split('[')[0];outcomes=[{'type':e.tag,'message':e.get('message')} for e in c if e.tag in ('failure','error','skipped')]
   cases.append(c)
   if outcomes:failures.append({'class':cls,'method':name,'outcomes':outcomes})
   if cls in methods:
    sdk=int(re.search(r'\[(28|32|33)\]$',name).group(1)) if re.search(r'\[(28|32|33)\]$',name) else 33
    aliascases.append({'class':cls,'method':method,'reported_name':name,'sdk':sdk,'passed':not outcomes,'source_identity_matches':methods[cls]==method})
 actual={(c.get('classname').split('.')[-1],c.get('name').split('[')[0]) for c in cases};identities=actual==expected and len(cases)==47 and len(xmls)==7
 aliasmatrix={(c['class'],c['method'],c['sdk']) for c in aliascases}=={(cls,method,sdk) for cls,method in methods.items() for sdk in (28,32,33)} and len(aliascases)==6
 important=identities and aliasmatrix and all(c['passed'] and c['source_identity_matches'] for c in aliascases)
passed=run['conclusion']=='success' and job['conclusion']=='success' and rec['passed'] and rec['execution']['exit_code']==0 and not rec['execution'].get('stop_reason') and not failures and identities and aliasmatrix and rec['totals']['passed']==rec['totals']['tests']==rec['totals']['executed']==47 and rec['task_execution_markers']=={':calf-permissions:calf-permissions-core:testAndroidHostTest':1}
accepted=[{'criterion':criterion,'accepted':important,'methods':[{'class':c['class'],'method':c['method'],'sdk':c['sdk']} for c in aliascases]} for criterion in f['required_tests']]
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':passed,'important_acceptance_passed':important,'finding':'PERM-002','issue':18,'source_revision':SHA,'run_id':RUN,'run_url':run['html_url'],'whole_run_conclusion':run['conclusion'],'source_inputs_verified_from_exact_Git_blobs':len(inputs),'artifact_every_XML_and_before_after_verified':True,'source_43_method_identities_match':identities,'actual_6_required_SDK_cases':aliascases,'original_acceptance':accepted,'totals':rec['totals'],'reports':reports,'authored_methods':43,'fresh_runtime_executions':len(cases),'command':rec['command'],'execution':rec['execution'],'runtime':rt,'setup_runtime_correspondence':True,'Robolectric_official_source_acquisition':source,'unmarked_last_SDK_name_source':'RobolectricTestRunner.java getChildren and getName; final selected SDK33 omits suffix unless always-marker mode','failures':failures,'scope':'Real public ReadStorage/Gallery singleton initializers in both cold orders each at28/32/33, guarded fresh mappings and absent second singleton before its access. Real public Android Compose/ActivityResult factory/intent/result dispatch. Gallery-only/both/custom-only requests preserve exactly requested object/state/callback identities, both grant/deny results, SDK33 NotRequired and native deduplication. Only core host tests run; Gallery production is test dependency.','limitations':['Robolectric native-grant/dialog interception is controlled host integration,not Android OS privacy UI/physical-device authority or process recreation','Distinct instrumentation configurations select fresh sandboxes; runtime fresh-mapping preconditions must pass,not repeated already-initialized access','No Apple/desktop/browser/dependency/legal/API-ABI/full-consumer/security/release certification'],'unrelated_suites_replayed':False,'packages_releases_deployments_published':False}
(B/'important-result-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:review[k] for k in ('passed','important_acceptance_passed','finding','run_id','totals','actual_6_required_SDK_cases','failures','whole_run_conclusion')},indent=2))
assert passed and important,'Run/important requirements did not all pass; inspect actual failure before closure'
