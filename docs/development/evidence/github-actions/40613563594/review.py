"""Important public browser WebView acceptance; no build or automatic closure."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,json,re,stat,subprocess,sys,zipfile,xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit');B=Path(__file__).parent;RUN=40613563594;D=B/str(RUN);SHA='b7ba5c802ee8c8a58e813d19b5a242770aac9675'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt,runtime_context as rc
run=json.loads((D/'run-final.json').read_text());jobs=json.loads((D/'jobs-final.json').read_text())['jobs'];arts=json.loads((D/'artifacts-final.json').read_text())['artifacts']
assert run['head_sha']==SHA and run['id']==RUN and run['status']=='completed' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening' and run['run_attempt']==1
assert len(arts)==2 and next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
inputs=lt.snapshot_inputs(ROOT);assert len(inputs)==742 and inputs==json.loads((B/'inputs-before-dispatch.json').read_text())
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);raw,_=p.communicate(''.join(SHA+':'+n+'\n' for n in inputs).encode());assert p.returncode==0;off=0;blobs={}
for n,h in inputs.items():
 e=raw.index(b'\n',off);head=raw[off:e].split();assert head[1]==b'blob';size=int(head[2]);data=raw[e+1:e+1+size];assert hashlib.sha256(data).hexdigest()==h,n;blobs[n]=data;off=e+size+2
assert off==len(raw)
owner=blobs['calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt'].decode();assert 'DisposableEffect(owner) { onDispose { owner.dispose() } }' in owner and 'if (state.iframe === frame)' in owner and 'frame.removeEventListener("load", loadListener)' in owner and 'frame.removeEventListener("error", errorListener)' in owner
fixture=blobs['calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserWebViewCompositionTest.kt'].decode()
assert 'ComposeViewport(container)' in fixture and 'LocalComposeWindow.current' in fixture and 'composeWindow.dispose()' in fixture and '!old.isConnected' in fixture and 'deliveries + 2' in fixture and 'replacementOwner, state.owner' in fixture
for n in ('calf-webview/src/jsMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.js.kt','calf-webview/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.wasmJs.kt'):assert 'WebElementView(' in blobs[n].decode()
criteria={
 'Mount/unmount with a callback counter; verify exactly one onDispose.':['disposingThePublicViewportCallsOnceAndReleasesTheActuallyMountedIframe','removingAndRemountingThePublicWebViewCreatesAFreshOwnerInTheSameViewport'],
 'Retained state no longer references the old iframe after removal.':['disposingThePublicViewportCallsOnceAndReleasesTheActuallyMountedIframe','removingAndRemountingThePublicWebViewCreatesAFreshOwnerInTheSameViewport'],
 'Queued load/error events after disposal do not update a replacement view.':['queuedCapturedOldListenersCannotMutateThePublicReplacementView'],
}
f=next(r for r in json.loads((ROOT/'docs/audit/findings/NATIVE.json').read_text()) if r['id']=='NATIVE-006');assert f['required_tests']==list(criteria)
required={name for names in criteria.values() for name in names};summaries=[];sets=[]
instant=lambda s:dt.datetime.fromisoformat(s.replace('Z','+00:00'))
for slot,suite,task in [('browser-js','js',':calf-webview:jsBrowserTest'),('browser-wasm','wasm',':calf-webview:wasmJsBrowserTest')]:
 art=next(a for a in arts if a['name']=='library-evidence-'+slot);z=D/(str(art['id'])+'.zip');assert not art['expired'] and art['workflow_run']['head_sha']==SHA and art['workflow_run']['id']==RUN
 assert z.stat().st_size==art['size_in_bytes']<64*1024**2 and 'sha256:'+hashlib.sha256(z.read_bytes()).hexdigest()==art['digest']
 job=next(j for j in jobs if j['name'].startswith('library-tests ('+slot+','));assert job['status']=='completed' and job['run_attempt']==1
 with zipfile.ZipFile(z) as a:
  entries=a.infolist();assert len(entries)==len({e.filename for e in entries}) and sum(e.file_size for e in entries)<64*1024**2
  for entry in entries:
   path=PurePosixPath(entry.filename);assert not path.is_absolute() and not {'.','..'}&set(path.parts) and '\\' not in entry.filename
   assert not entry.is_dir() and not entry.flag_bits&1 and stat.S_IFMT(entry.external_attr>>16) in (0,stat.S_IFREG)
   assert entry.filename.endswith(('.json','.xml')) and entry.file_size<16*1024**2
  base='build/ci-verification/'+slot+'/';rec=json.loads(a.read(base+'receipt.json'));rt=json.loads(a.read(base+'runtime.json'));setup=json.loads(a.read('build/ci-runtime/actual.json'))
  assert json.loads(a.read(base+'inputs-before.json'))==json.loads(a.read(base+'inputs-after.json'))==inputs
  assert rec['source_revision']==rec['source_revision_after']==SHA and not rec['source_tree_dirty'] and not rec['changed_inputs']
  assert rec['inputs_before_sha256']==rec['inputs_after_sha256']==lt.input_digest(inputs)
  plan=lt.plan(ROOT,suite,only_modules=('calf-webview',));assert json.loads(a.read(base+'plan.json'))==json.loads(a.read('build/ci-plan/plan.json'))==plan
  assert rec['command']==lt.gradle_command(suite,plan,root=ROOT) and rec['command'][-1]==task and rec['task_execution_markers']=={task:1}
  assert not rec['execution'].get('stop_reason') and rec['explicit_module_subset']==['calf-webview'] and not rec['complete_suite_requested']
  for k in ('host','java','rust','android_platform','compiler_runtime_fingerprint','browser'):assert rt[k]==setup[k]
  assert rt['source_revision']==SHA and not rt['source_tree_dirty'] and rt['host']['system']=='Linux' and rt['host']['architecture']=='x64' and rt['java']['major']==17 and rt['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(rt)
  assert instant(job['started_at'])<=instant(rt['observed_at_utc'])<=instant(job['completed_at'])
  start,end=instant(rec['started_at_utc']),instant(rec['finished_at_utc']);assert instant(job['started_at'])<=start<end<=instant(job['completed_at'])
  expected=set()
  for n in plan['expected'][0]['test_source_files']:
   source=blobs[n].decode();methods=list(re.finditer(r'@Test\s*(?:@Suppress\([^\n]*\)\s*)?fun (`[^`\n]+`|[A-Za-z][A-Za-z0-9_]*)\(',source));assert len(methods)==len(re.findall(r'@Test\b',source))
   if not methods:continue
   classes=list(re.finditer(r'^class ([A-Za-z][A-Za-z0-9_]*)',source,re.M));assert classes,n
   for m in methods:expected.add((next(c.group(1) for c in reversed(classes) if c.start()<m.start()),m.group(1).strip('`')))
  assert len(expected)==33
  xmls=[e.filename for e in entries if e.filename.endswith('.xml')];assert len(xmls)==7
  cases=[];failed=[];composition=[]
  for n in xmls:
   data=a.read(n);assert b'<!DOCTYPE' not in data and b'<!ENTITY' not in data;report=next(r for m in rec['modules'] for r in m['reports'] if r['path']==n);assert report['sha256']==hashlib.sha256(data).hexdigest()
   root=E.fromstring(data);assert start<=instant(root.attrib['timestamp'])<=end
   for c in root.findall('.//testcase'):
    cases.append(c);method=c.get('name').split('[')[0]
    outcomes=[e for e in c if e.tag in ('failure','error','skipped')]
    if c.get('classname').split('.')[-1]=='BrowserWebViewCompositionTest':
     assert not outcomes,(slot,method);composition.append(method)
    for e in outcomes:failed.append({'method':method,'outcome':e.tag,'message':e.get('message')})
  actual={(c.get('classname').split('.')[-1],c.get('name').split('[')[0]) for c in cases};assert len(cases)==33 and actual==expected and set(composition)==required
  assert rec['totals']['tests']==33 and rec['totals']['errors']==rec['totals']['skipped']==0
  sets.append(actual);summaries.append({'slot':slot,'job_id':job['id'],'command':rec['command'],'execution':rec['execution'],'totals':rec['totals'],'reports':len(xmls),'all33_source_method_identities_fresh':True,'new_public_Compose_methods':3,'important_methods':sorted(required),'important_passed':3,'independent_nonrequired_failures':failed,'runtime':rt,'setup_runtime_correspondence':True})
assert sets[0]==sets[1]
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':SHA,'run_id':RUN,'run_url':run['html_url'],'whole_run_conclusion':run['conclusion'],'source_inputs_verified_from_exact_Git_blobs':len(inputs),'artifact_every_XML_and_before_after_verified':True,'totals':{'executed':sum(j['totals']['executed'] for j in summaries),'passed':sum(j['totals']['passed'] for j in summaries),'failures':sum(j['totals']['failures'] for j in summaries),'errors':0,'skipped':0,'reports':14,'source_methods':33,'new_source_methods':3,'important_executions':6,'important_passed':6},'jobs':summaries,'finding':'NATIVE-006','issue':65,'original_acceptance':[{'criterion':criterion,'accepted':True,'methods':methods} for criterion,methods in criteria.items()],'scope':'Actual public WebView through real ComposeViewport/canvas/HTML interop: full window disposal and component removal/remount with retained state, independent new owner/node, native listener removal plus original captured callbacks really delivered after replacement. No copied renderer/no-op applier. Only dependency-internal test disposal handle; trusted controlled HTML for native DOM readiness.','limitations':['Chrome JS/Wasm only, not Safari/Firefox/GC memory profiling or other WebView/sandbox/network/cookie issues','No physical/minimum/native sanitizer/ABI/legal/dependency/full-consumer/release gate'],'unrelated_suites_replayed':False,'packages_releases_deployments_published':False}
(B/'important-result-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:review[k] for k in ('passed','finding','run_id','totals','original_acceptance','whole_run_conclusion')},indent=2))
