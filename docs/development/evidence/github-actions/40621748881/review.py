"""Review real JavaFX cookie/session/concurrency requirements; no automatic closure."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,json,re,stat,subprocess,sys,zipfile,xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit');B=Path(__file__).parent;RUN=40621748881;D=B/str(RUN);SHA='6dbe6ca257c85350034dbfeb120653f07ae42532';SLOT='desktop-linux-x64'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt,runtime_context as rc
run=json.loads((D/'run-final.json').read_text());jobs=json.loads((D/'jobs-final.json').read_text())['jobs'];arts=json.loads((D/'artifacts-final.json').read_text())['artifacts']
assert run['head_sha']==SHA and run['id']==RUN and run['status']=='completed' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening' and run['run_attempt']==1
assert len(arts)==1 and next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
inputs=lt.snapshot_inputs(ROOT);assert len(inputs)==745 and inputs==json.loads((B/'inputs-before-dispatch.json').read_text())
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);raw,_=p.communicate(''.join(SHA+':'+n+'\n' for n in inputs).encode());assert p.returncode==0;off=0;blobs={}
for n,h in inputs.items():
 e=raw.index(b'\n',off);head=raw[off:e].split();assert head[1]==b'blob';size=int(head[2]);data=raw[e+1:e+1+size];assert hashlib.sha256(data).hexdigest()==h,n;blobs[n]=data;off=e+size+2
assert off==len(raw)
fixture=blobs['calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/JavaFxUserAgentIntegrationTest.kt'].decode()
assert 'HttpServer.create(' in fixture and 'view.owner.load(WebContent.Url(url))' in fixture
assert 'exchange.requestHeaders.getFirst("User-Agent")' in fixture and 'requests[URI(url).path]' in fixture
assert '"document.contentType"' in fixture and 'responseHeaders.add("Content-Type", "text/html; charset=utf-8")' in fixture
assert 'NativeCmpKit-UA-A' in fixture and 'NativeCmpKit-UA-B' in fixture and 'http.loadAndAssert(view, original)' in fixture
assert 'assertNotSame(firstEngine, secondEngine)' in fixture and 'firstEngine.userAgent to secondEngine.userAgent' in fixture
assert 'http.loadAndAssert(first, defaults.first)' in fixture and 'http.loadAndAssert(second, defaults.second)' in fixture
assert 'http.loadAndAssert(second, "NativeCmpKit-UA-second")' in fixture and 'http.loadAndAssert(first, "NativeCmpKit-UA-first-again")' in fixture
assert 'withTimeout(10_000)' in fixture and 'Owned HTTP response threads must terminate' in fixture
owner=blobs['calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt'].decode()
assert 'private var defaultUserAgent: String? = null' in owner and 'defaultUserAgent = engine.userAgent' in owner and 'view.engine.userAgent = state.settings.desktopSettings.customUserAgent ?: defaultUserAgent' in owner
helper=blobs['calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/JavaFxWebViewTest.kt'].decode()
assert 'internal class Fixture' in helper and 'DesktopWebViewOwner(' in helper and 'JFXPanel()' in helper
criteria={
 'Set custom A, change to B, reset null and inspect actual request User-Agent/default engine value.':['actualHttpUserAgentChangesFromAToBAndNullRestoresTheNativeDefault'],
 'Multiple WebView instances preserve their individual defaults.':['twoActualViewsKeepIndependentDefaultsAndResetOnlyTheirOwnRequestHeaders'],
}
f=next(r for r in json.loads((ROOT/'docs/audit/findings/NATIVE.json').read_text()) if r['id']=='NATIVE-036');assert f['required_tests']==list(criteria)
required={n for names in criteria.values() for n in names};instant=lambda s:dt.datetime.fromisoformat(s.replace('Z','+00:00'))
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
 plan=lt.plan(ROOT,'desktop',only_modules=('calf-webview',));assert json.loads(a.read(base+'plan.json'))==json.loads(a.read('build/ci-plan/plan.json'))==plan
 assert rec['command']==lt.gradle_command('desktop',plan,root=ROOT) and rec['command'][-1]==':calf-webview:desktopTest' and rec['task_execution_markers']=={':calf-webview:desktopTest':1}
 assert rec['explicit_module_subset']==['calf-webview'] and not rec['complete_suite_requested'] and not rec['execution'].get('stop_reason')
 for k in ('host','java','rust','android_platform','compiler_runtime_fingerprint'):assert rt[k]==setup[k]
 assert rt['source_revision']==SHA and not rt['source_tree_dirty'] and rt['host']['system']=='Linux' and rt['host']['architecture']=='x64' and rt['java']['major']==17 and rt['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(rt)
 assert instant(job['started_at'])<=instant(rt['observed_at_utc'])<=instant(job['completed_at'])
 start,end=instant(rec['started_at_utc']),instant(rec['finished_at_utc']);assert instant(job['started_at'])<=start<end<=instant(job['completed_at'])
 expected=set()
 for n in plan['expected'][0]['test_source_files']:
  source=blobs[n].decode();methods=list(re.finditer(r'@Test\s*(?:@Suppress\([^\n]*\)\s*)?fun (`[^`\n]+`|[A-Za-z][A-Za-z0-9_]*)\(',source));assert len(methods)==len(re.findall(r'@Test\b',source))
  if not methods:continue
  classes=list(re.finditer(r'^class ([A-Za-z][A-Za-z0-9_]*)',source,re.M));assert classes,n
  for m in methods:expected.add((next(c.group(1) for c in reversed(classes) if c.start()<m.start()),m.group(1).strip('`')))
 assert len(expected)==45
 xmls=[e.filename for e in entries if e.filename.endswith('.xml')];assert len(xmls)==9
 cases=[];cookiecases=[];failures=[];reports=[]
 for n in xmls:
  data=a.read(n);assert b'<!DOCTYPE' not in data and b'<!ENTITY' not in data;report=next(r for m in rec['modules'] for r in m['reports'] if r['path']==n);assert report['sha256']==hashlib.sha256(data).hexdigest()
  root=E.fromstring(data);assert start<=instant(root.attrib['timestamp'])<=end
  cs=root.findall('.//testcase');reports.append({'path':n,'sha256':report['sha256'],'testcases':len(cs)})
  for c in cs:
   outcomes=[{'type':e.tag,'message':e.get('message')} for e in c if e.tag in ('failure','error','skipped')]
   method=c.get('name').split('[')[0];cases.append(c)
   if outcomes:failures.append({'method':method,'outcomes':outcomes})
   if c.get('classname').split('.')[-1]=='JavaFxUserAgentIntegrationTest':cookiecases.append({'method':method,'passed':not outcomes})
 actual={(c.get('classname').split('.')[-1],c.get('name').split('[')[0]) for c in cases};assert len(cases)==45 and actual==expected and len(cookiecases)==2
 assert sum(c.get('classname').split('.')[-1] in ('JavaFxWebViewTest','JavaFxCookieIntegrationTest','JavaFxUserAgentIntegrationTest') for c in cases)==13
 assert required<={h['method'] for h in cookiecases} and rec['totals']['tests']==rec['totals']['executed']==45
passed=run['conclusion']=='success' and job['conclusion']=='success' and rec['passed'] and rec['execution']['exit_code']==0 and not failures and rec['totals']['passed']==45
accepted=[{'criterion':c,'accepted':all(h['passed'] for h in cookiecases if h['method'] in methods),'methods':methods} for c,methods in criteria.items()]
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':passed,'source_revision':SHA,'run_id':RUN,'run_url':run['html_url'],'whole_run_conclusion':run['conclusion'],'source_inputs_verified_from_exact_Git_blobs':len(inputs),'artifact_every_XML_and_before_after_verified':True,'totals':rec['totals'],'reports':reports,'authored_method_identities_fresh':45,'actual_new_UserAgent_methods':2,'actual_JavaFX_methods':13,'important_methods':sorted(required),'command':rec['command'],'execution':rec['execution'],'runtime':rt,'setup_runtime_correspondence':True,'finding':'NATIVE-036','issue':152,'original_acceptance':accepted,'failures':failures,'scope':'Real production JavaFX owners/JFXPanel/engines/public settings and loopback HTTP. Actual engine values and outgoing User-Agent headers follow A-to-B-to-null native default. Two distinct engines load concurrently with separate custom agents, then each resets only its own default while the other retains its custom value. Nine actual HTTP requests agree with native/DOM/library title and HTML MIME. Owned HTTP threads terminate.','limitations':['Linux/JavaFX21 and controlled loopback HTTP,not other JavaFX/OS matrices or authenticated site behavior', 'Each native default captured separately; this host can legitimately produce equal defaults,not synthetic unequal defaults', 'Existing actual owner fixture after toolkit bootstrap,not a completely fresh-JVM cold Compose startup test', 'No sanitizer/minimum-device/distribution/API-ABI/legal/dependency/full-consumer/release certification'],'unrelated_suites_replayed':False,'packages_releases_deployments_published':False}
(B/'important-result-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:review[k] for k in ('passed','finding','run_id','totals','original_acceptance','failures','whole_run_conclusion')},indent=2))
assert passed and all(c['accepted'] for c in accepted),'Actual requirements did not pass; do not close'
