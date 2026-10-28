"""Important acceptance review; no Gradle runs, automatic closure, or release gate."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,json,re,stat,subprocess,sys,zipfile,xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit');B=Path(__file__).parent;D=B/'40609563741';SHA='63f377f678fa3d4f0e4def26099fb5e0a6c3247a'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt,runtime_context as rc
run=json.loads((D/'run-final.json').read_text());jobs=json.loads((D/'jobs-final.json').read_text())['jobs'];arts=json.loads((D/'artifacts-final.json').read_text())['artifacts']
assert run['head_sha']==SHA and run['id']==40609563741 and run['status']=='completed' and run['conclusion']=='success' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening' and run['run_attempt']==1
assert len(arts)==2 and next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
inputs=lt.snapshot_inputs(ROOT);assert len(inputs)==741
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);raw,_=p.communicate(''.join(SHA+':'+n+'\n' for n in inputs).encode());assert p.returncode==0;off=0;blobs={}
for n,h in inputs.items():
 e=raw.index(b'\n',off);head=raw[off:e].split();assert head[1]==b'blob';size=int(head[2]);data=raw[e+1:e+1+size];assert hashlib.sha256(data).hexdigest()==h,n;blobs[n]=data;off=e+size+2
assert off==len(raw)
owner=blobs['calf-file-picker/src/webMain/kotlin/com.mohamedrejeb.calf/picker/BrowserPickerSession.kt'].decode()
assert 'DisposableEffect(owner) { onDispose { owner.close() } }' in owner and 'if (owner.disposed) return@launch' in owner and 'close()\n        // No user code inside the conversion catch' in owner
for n in ('calf-file-picker/src/jsMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.js.kt','calf-file-picker/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/picker/FilePickerLauncher.wasmJs.kt'):
 assert 'rememberBrowserFilePickerLauncher(type, selectionMode, onError, onResult)' in blobs[n].decode()
criteria={
 'onResult throws after success: no second callback':['successfulCallbackFailureNeverBecomesCancellationOrASecondResult'],
 'oncancel throws: node still removed':['cancellingCallbackFailureStillCleansTheElementAndListeners'],
 'Composition disposed during dialog':['publicCompositionDisposalDetachesInputAndSuppressesCapturedLateHandlers','removingPublicLauncherContentDisposesTheOwnerWithoutDisposingComposition'],
 'Two launch attempts':['overlappingPublicLaunchReportsOneErrorAndPreservesTheFirstSession','ownerRejectsOverlappingDialogsAndDisposalSuppressesLateResults'],
 'Same file reselect and normal cancellation':['theSameRealFileCanBeReselectedOnTwoFreshPublicLaunches','normalCancellationCleansBeforeTheCallbackAndAllowsAnotherPublicLaunch'],
 'JS/Wasm parity':[],
}
required={name for names in criteria.values() for name in names};summaries=[];sets=[]
def instant(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
for slot,suite,task in [('browser-js','js',':calf-file-picker:jsBrowserTest'),('browser-wasm','wasm',':calf-file-picker:wasmJsBrowserTest')]:
 art=next(a for a in arts if a['name']=='library-evidence-'+slot);z=D/(str(art['id'])+'.zip');assert not art['expired'] and art['workflow_run']['head_sha']==SHA and art['workflow_run']['id']==run['id']
 assert z.stat().st_size==art['size_in_bytes']<64*1024**2 and 'sha256:'+hashlib.sha256(z.read_bytes()).hexdigest()==art['digest']
 job=next(j for j in jobs if j['name'].startswith('library-tests ('+slot+','));assert job['conclusion']=='success' and job['status']=='completed' and job['run_attempt']==1
 with zipfile.ZipFile(z) as a:
  entries=a.infolist();assert len(entries)==len({e.filename for e in entries}) and sum(e.file_size for e in entries)<64*1024**2
  for entry in entries:
   path=PurePosixPath(entry.filename);assert not path.is_absolute() and not {'.','..'}&set(path.parts) and '\\' not in entry.filename
   assert not entry.is_dir() and not entry.flag_bits&1 and stat.S_IFMT(entry.external_attr>>16) in (0,stat.S_IFREG)
   assert entry.filename.endswith(('.json','.xml')) and entry.file_size<16*1024**2
  base='build/ci-verification/'+slot+'/';rec=json.loads(a.read(base+'receipt.json'));rt=json.loads(a.read(base+'runtime.json'));setup=json.loads(a.read('build/ci-runtime/actual.json'))
  assert json.loads(a.read(base+'inputs-before.json'))==json.loads(a.read(base+'inputs-after.json'))==inputs
  assert rec['source_revision']==rec['source_revision_after']==SHA and not rec['source_tree_dirty'] and not rec['changed_inputs'] and not rec['errors'] and rec['passed']
  assert rec['inputs_before_sha256']==rec['inputs_after_sha256']==lt.input_digest(inputs)
  plan=lt.plan(ROOT,suite,only_modules=('calf-file-picker',));assert json.loads(a.read(base+'plan.json'))==json.loads(a.read('build/ci-plan/plan.json'))==plan
  assert rec['command']==lt.gradle_command(suite,plan,root=ROOT) and rec['command'][-1]==task and rec['task_execution_markers']=={task:1}
  assert rec['execution']['exit_code']==0 and not rec['execution'].get('stop_reason') and rec['explicit_module_subset']==['calf-file-picker'] and not rec['complete_suite_requested']
  for k in ('host','java','rust','android_platform','compiler_runtime_fingerprint','browser'):assert rt[k]==setup[k]
  assert rt['source_revision']==SHA and not rt['source_tree_dirty'] and rt['host']['system']=='Linux' and rt['host']['architecture']=='x64' and rt['java']['major']==17 and rt['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(rt)
  assert instant(job['started_at'])<=instant(rt['observed_at_utc'])<=instant(job['completed_at'])
  start,end=instant(rec['started_at_utc']),instant(rec['finished_at_utc']);assert instant(job['started_at'])<=start<end<=instant(job['completed_at'])
  expected=set()
  for n in plan['expected'][0]['test_source_files']:
   source=blobs[n].decode();methods=re.findall(r'@Test\s*(?:@Suppress\([^\n]*\)\s*)?fun (`[^`\n]+`|[A-Za-z][A-Za-z0-9_]*)\(',source);assert len(methods)==len(re.findall(r'@Test\b',source))
   expected.update((Path(n).stem,m.strip('`')) for m in methods)
  assert len(expected)==22
  xmls=[e.filename for e in entries if e.filename.endswith('.xml')];assert len(xmls)==5
  cases=[]
  for n in xmls:
   data=a.read(n);assert b'<!DOCTYPE' not in data and b'<!ENTITY' not in data;report=next(r for m in rec['modules'] for r in m['reports'] if r['path']==n);assert report['sha256']==hashlib.sha256(data).hexdigest()
   root=E.fromstring(data);assert start<=instant(root.attrib['timestamp'])<=end
   fresh=root.findall('.//testcase');assert all(not any(e.tag in ('failure','error','skipped') for e in c) for c in fresh);cases+=fresh
  actual={(c.get('classname').split('.')[-1],c.get('name').split('[')[0]) for c in cases};assert len(cases)==22 and actual==expected
  assert required<={name for _,name in actual} and len([1 for cls,_ in actual if cls=='BrowserPickerCompositionTest'])==5
  assert rec['totals']['executed']==rec['totals']['passed']==22 and rec['totals']['skipped']==0
  sets.append(actual);summaries.append({'slot':slot,'suite':suite,'job_id':job['id'],'command':rec['command'],'execution':rec['execution'],'totals':rec['totals'],'reports':len(xmls),'all22_authored_methods_fresh':True,'new_public_Compose_methods':5,'important_methods':sorted(required),'runtime':rt,'setup_runtime_correspondence':True})
assert sets[0]==sets[1]
findings=json.loads((ROOT/'docs/audit/findings/io-picker.json').read_text()) if (ROOT/'docs/audit/findings/io-picker.json').exists() else [r for p in (ROOT/'docs/audit/findings').glob('*.json') for r in json.loads(p.read_text())]
f=next(r for r in findings if r['id']=='IO-026');assert f['required_tests']==list(criteria)
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':SHA,'run_id':run['id'],'run_url':run['html_url'],'whole_run_conclusion':'success','source_inputs_verified_from_exact_Git_blobs':len(inputs),'artifact_every_XML_and_before_after_verified':True,'totals':{'executed':44,'passed':44,'failures':0,'errors':0,'skipped':0,'reports':10,'source_methods':22,'new_source_methods':5},'jobs':summaries,'finding':'IO-026','original_acceptance':[{'criterion':criterion,'accepted':True,'methods':methods or ['Identical22 source/case identities; both actual JS/Wasm implementations route to the reviewed shared owner']} for criterion,methods in criteria.items()],'scope':'Real public Compose composition/disposal, DOM input, File/DataTransfer/FileList and delivered change/cancel events. Only native chooser opening is intercepted. Earlier direct owning-session callback-failure tests remain and pass.','limitations':['No native OS chooser UI/user-activation/automatic OS cancel-event or cross-browser Safari/Firefox certification','No physical/minimum/native sanitizer/ABI/legal/dependency/full-consumer/release gate'], 'unrelated_suites_replayed':False,'packages_releases_deployments_published':False}
(B/'important-result-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:review[k] for k in ('passed','finding','run_id','totals','original_acceptance')},indent=2))
