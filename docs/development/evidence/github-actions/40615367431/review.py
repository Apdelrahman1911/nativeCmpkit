"""Important share callback acceptance: real Promise methods plus exact-input Android reuse."""
from pathlib import Path, PurePosixPath
import datetime as dt, hashlib, json, re, stat, subprocess, sys, zipfile, xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit');B=Path(__file__).parent;RUN=40615367431;D=B/str(RUN);SHA='3b01b400864d5ceee2f542b7577b68c976df2d6a'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt,runtime_context as rc
run=json.loads((D/'run-final.json').read_text());jobs=json.loads((D/'jobs-final.json').read_text())['jobs'];arts=json.loads((D/'artifacts-final.json').read_text())['artifacts']
assert run['head_sha']==SHA and run['id']==RUN and run['status']=='completed' and run['conclusion']=='success' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening' and run['run_attempt']==1
assert len(arts)==2 and next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
inputs=lt.snapshot_inputs(ROOT);assert len(inputs)==742 and inputs==json.loads((B/'inputs-before-dispatch.json').read_text())
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);raw,_=p.communicate(''.join(SHA+':'+n+'\n' for n in inputs).encode());assert p.returncode==0;off=0;blobs={}
for n,h in inputs.items():
 e=raw.index(b'\n',off);head=raw[off:e].split();assert head[1]==b'blob';size=int(head[2]);data=raw[e+1:e+1+size];assert hashlib.sha256(data).hexdigest()==h,n;blobs[n]=data;off=e+size+2
assert off==len(raw)
# Owning production error boundary, not a copied replacement implementation.
android=blobs['calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt'].decode()
assert 'val result = launchAndroidShare(context, content, options)\n    onResult(result)' in android
js=blobs['calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt'].decode()
wasm=blobs['calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt'].decode()
assert 'promise.then(' in js and 'promise.then(function() { completed(); }, function(e)' in wasm
assert not re.search(r'\}.*\.catch\(',js) and not re.search(r'\}.*\.catch\(',wasm)
owner=blobs['calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt'].decode()
assert 'if (gate.finish(token) && !disposed) onResult(result)' in owner
fixture=blobs['calf-share/src/webTest/kotlin/com/mohamedrejeb/calf/share/WebSharePromiseTest.kt'].decode()
assert fixture.count('for (mode in listOf("clipboard", "share"))')==2
assert 'legacy += it.toLegacyResult()' in fixture and 'listOf<ShareResult>(ShareResult.Success)' in fixture
assert 'assertIs<ShareOutcome.Failed>(results.single(), mode)' in fixture
for n in ('calf-share/src/jsTest/kotlin/com/mohamedrejeb/calf/share/WebShareHarness.js.kt','calf-share/src/wasmJsTest/kotlin/com/mohamedrejeb/calf/share/WebShareHarness.wasmJs.kt'):
 harness=blobs[n].decode();assert 'new Promise(' in harness and 'child.catch(function(error) { h.callbackErrors.push(String(error)); })' in harness and 'NotAllowedError' in harness
criteria={
 'Callback deliberately throws after recording Success; exactly one callback invocation is observed.':['throwingApplicationCallbackIsNotASecondPlatformResult','AndroidShareTest.throwingApplicationResultCallbackIsNotReclassifiedOrInvokedTwice'],
 'Platform start/share rejection invokes one failure and is distinct from callback failure.':['rejectedClipboardPromiseProducesOneFailureAndNoSuccess','throwingRejectedPromiseCallbackIsOneFailureAndLeavesTheOwnerReusable','AndroidShareTest.platformLaunchFailureIsOneFailureInsteadOfACompletedShare'],
 'JS/Wasm resolved/rejected promises and Android ActivityNotFoundException paths.':['clipboardSuccessWaitsForPromiseSettlement','throwingApplicationCallbackIsNotASecondPlatformResult','throwingRejectedPromiseCallbackIsOneFailureAndLeavesTheOwnerReusable','AndroidShareTest.platformLaunchFailureIsOneFailureInsteadOfACompletedShare'],
}
f=next(r for r in json.loads((ROOT/'docs/audit/findings/NATIVE.json').read_text()) if r['id']=='NATIVE-032');assert f['required_tests']==list(criteria)
required={name for methods in criteria.values() for name in methods if not name.startswith('AndroidShareTest.')};summaries=[];sets=[]
instant=lambda s:dt.datetime.fromisoformat(s.replace('Z','+00:00'))
for slot,suite,task in [('browser-js','js',':calf-share:jsBrowserTest'),('browser-wasm','wasm',':calf-share:wasmJsBrowserTest')]:
 art=next(a for a in arts if a['name']=='library-evidence-'+slot);z=D/(str(art['id'])+'.zip');assert not art['expired'] and art['workflow_run']['head_sha']==SHA and art['workflow_run']['id']==RUN
 assert z.stat().st_size==art['size_in_bytes']<64*1024**2 and 'sha256:'+hashlib.sha256(z.read_bytes()).hexdigest()==art['digest']
 job=next(j for j in jobs if j['name'].startswith('library-tests ('+slot+','));assert job['status']=='completed' and job['conclusion']=='success' and job['run_attempt']==1
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
  plan=lt.plan(ROOT,suite,only_modules=('calf-share',));assert json.loads(a.read(base+'plan.json'))==json.loads(a.read('build/ci-plan/plan.json'))==plan
  assert rec['command']==lt.gradle_command(suite,plan,root=ROOT) and rec['command'][-1]==task and rec['task_execution_markers']=={task:1}
  assert rec['passed'] and rec['execution']['exit_code']==0 and not rec['execution'].get('stop_reason') and rec['explicit_module_subset']==['calf-share'] and not rec['complete_suite_requested']
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
  assert len(expected)==18
  xmls=[e.filename for e in entries if e.filename.endswith('.xml')];assert len(xmls)==2
  cases=[];promise=[];reports=[]
  for n in xmls:
   data=a.read(n);assert b'<!DOCTYPE' not in data and b'<!ENTITY' not in data;report=next(r for m in rec['modules'] for r in m['reports'] if r['path']==n);assert report['sha256']==hashlib.sha256(data).hexdigest()
   root=E.fromstring(data);assert start<=instant(root.attrib['timestamp'])<=end
   cs=root.findall('.//testcase');reports.append({'path':n,'sha256':report['sha256'],'passed':len(cs)})
   for c in cs:
    assert not any(e.tag in ('failure','error','skipped') for e in c),(slot,c.get('name'));cases.append(c)
    if c.get('classname').split('.')[-1]=='WebSharePromiseTest':promise.append(c.get('name').split('[')[0])
  actual={(c.get('classname').split('.')[-1],c.get('name').split('[')[0]) for c in cases};assert len(cases)==18 and actual==expected and len(promise)==10 and required<=set(promise)
  assert rec['totals']['tests']==rec['totals']['executed']==rec['totals']['passed']==18 and rec['totals']['errors']==rec['totals']['skipped']==rec['totals']['failures']==0
  sets.append(actual);summaries.append({'slot':slot,'job_id':job['id'],'command':rec['command'],'execution':rec['execution'],'totals':rec['totals'],'reports':reports,'all18_source_method_identities_fresh':True,'new_Promise_methods':1,'important_methods':sorted(required),'both_share_and_clipboard_fulfilled_and_rejected_callback_error_paths':True,'runtime':rt,'setup_runtime_correspondence':True})
assert sets[0]==sets[1]
android_reuse=json.loads((B/'android-reuse-review.json').read_text());assert android_reuse['passed'] and android_reuse['current_revision_relevant_inputs_matched']==SHA and android_reuse['reused_actual_executions']==16 and android_reuse['fresh_executions']==0 and android_reuse['relevant_input_count']==16
for n,h in android_reuse['relevant_input_hashes'].items():assert inputs[n]==h and hashlib.sha256(blobs[n]).hexdigest()==h
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':SHA,'run_id':RUN,'run_url':run['html_url'],'whole_run_conclusion':run['conclusion'],'source_inputs_verified_from_exact_Git_blobs':len(inputs),'artifact_every_XML_and_before_after_verified':True,'totals':{'fresh_executed':36,'fresh_passed':36,'failures':0,'errors':0,'skipped':0,'fresh_reports':4,'browser_source_methods':18,'new_browser_source_methods':1,'reused_Android_executions':16,'new_Android_executions':0},'jobs':summaries,'Android_same_input_reuse':android_reuse,'finding':'NATIVE-032','issue':87,'original_acceptance':[{'criterion':c,'accepted':True,'methods':m} for c,m in criteria.items()],'scope':'Actual production JS/Wasm Promise settlement and owner, controlled navigator functions only. Both share and clipboard callbacks record Success then throw; rejected callbacks remain one failure and allow next launch. Actual Android platform/callback separation and ActivityNotFoundException under Robolectric reused with16 unchanged own-Git inputs.','limitations':['No real OS clipboard/share permission, user activation, chooser/recipient/device behavior','No other-engine, native sanitizer, minimum-device, distribution/API-ABI/legal/dependency/full-consumer/release certification'],'unrelated_suites_replayed':False,'packages_releases_deployments_published':False}
(B/'important-result-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:review[k] for k in ('passed','finding','run_id','totals','original_acceptance','whole_run_conclusion')},indent=2))
