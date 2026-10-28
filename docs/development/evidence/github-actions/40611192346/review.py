"""Review important cookie acceptance; whole failed workflow remains failed."""
from pathlib import Path, PurePosixPath
import datetime as dt, hashlib, json, re, stat, subprocess, sys, zipfile
import xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit'); B=Path(__file__).parent; D=B/'40611192346'
SHA='c39d320c8f82d67e7671eb38cad19a4068f919aa'; RUN=40611192346
sys.path.insert(0,str(ROOT/'scripts/ci')); import library_tests as lt, runtime_context as rc
run=json.loads((D/'run-final.json').read_text()); jobs=json.loads((D/'jobs-final.json').read_text())['jobs']; arts=json.loads((D/'artifacts-final.json').read_text())['artifacts']
assert run['id']==RUN and run['head_sha']==SHA and run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1 and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
assert len(arts)==1 and next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
inputs=lt.snapshot_inputs(ROOT); assert len(inputs)==741 and inputs==json.loads((B/'inputs-before-dispatch.json').read_text())
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE); raw,_=p.communicate(''.join(SHA+':'+n+'\n' for n in inputs).encode()); assert p.returncode==0; off=0; blobs={}
for n,h in inputs.items():
 e=raw.index(b'\n',off); header=raw[off:e].split(); assert header[1]==b'blob'; size=int(header[2]); data=raw[e+1:e+1+size]; assert hashlib.sha256(data).hexdigest()==h,n; blobs[n]=data; off=e+size+2
assert off==len(raw)
source=blobs['calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt'].decode()
assert 'known[native] = KnownCookie(uri.host, cookie.domain == null, cookie.expiresDate)' in source and 'known[native]?.expiry' in source and 'metadata.expiry > now' in source
assert source.index('validateCookieHost(cookie, uri.host')<source.index('handler.cookieStore.add(uri, native)')
assert 'require(it in -62135596800000L..253402300799999L)' in blobs['calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieRules.kt'].decode()
assert 'metadata is unavailable' in blobs['calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/Cookie.kt'].decode()
criteria={
 'Set a cookie with a known future expiry; reads separated in time remain at the same absolute expiry.':['absoluteExpiryDoesNotDriftWithReadTime'],
 'Roundtrip returned cookie to another store without increasing lifetime.':['roundTripToAnotherRealJdkStorePreservesTheAbsoluteExpiry'],
 'Session, already-expired, near-second-boundary and overflow-sized timestamps.':['sessionPastAndSubsecondExpiryNeverInventOrExtendApiLifetime','supportedTimestampExtremesAreExactAndOverflowInputsFailBeforeMutation'],
}
f=next(r for r in json.loads((ROOT/'docs/audit/findings/NATIVE.json').read_text()) if r['id']=='NATIVE-014'); assert f['required_tests']==list(criteria)
issue=json.loads((B/'issue-before.json').read_text()); assert issue['state']=='open' and issue['number']==71 and 'NATIVE-014' in issue['title'] and all(c in issue['body'] for c in criteria)
art=arts[0]; z=D/(str(art['id'])+'.zip'); assert art['name']=='library-evidence-desktop-linux-x64' and not art['expired'] and art['workflow_run']['head_sha']==SHA and art['workflow_run']['id']==RUN
assert z.stat().st_size==art['size_in_bytes']<64*1024**2 and 'sha256:'+hashlib.sha256(z.read_bytes()).hexdigest()==art['digest']
job=next(j for j in jobs if j['name'].startswith('library-tests (desktop-linux-x64,')); assert job['conclusion']=='failure' and job['run_attempt']==1
instant=lambda s: dt.datetime.fromisoformat(s.replace('Z','+00:00'))
with zipfile.ZipFile(z) as a:
 entries=a.infolist(); assert len(entries)==len({e.filename for e in entries}) and sum(e.file_size for e in entries)<64*1024**2
 for entry in entries:
  path=PurePosixPath(entry.filename); assert not path.is_absolute() and not {'.','..'}&set(path.parts) and '\\' not in entry.filename
  assert not entry.is_dir() and not entry.flag_bits&1 and stat.S_IFMT(entry.external_attr>>16) in (0,stat.S_IFREG)
  assert entry.filename.endswith(('.json','.xml')) and entry.file_size<16*1024**2
 base='build/ci-verification/desktop-linux-x64/'
 rec=json.loads(a.read(base+'receipt.json')); rt=json.loads(a.read(base+'runtime.json')); setup=json.loads(a.read('build/ci-runtime/actual.json'))
 assert json.loads(a.read(base+'inputs-before.json'))==json.loads(a.read(base+'inputs-after.json'))==inputs
 assert rec['source_revision']==rec['source_revision_after']==SHA and not rec['source_tree_dirty'] and not rec['changed_inputs'] and not rec['passed']
 assert rec['inputs_before_sha256']==rec['inputs_after_sha256']==lt.input_digest(inputs)
 assert rec['execution']['exit_code']==1 and not rec['execution'].get('stop_reason') and rec['explicit_module_subset']==['calf-webview'] and not rec['complete_suite_requested']
 plan=lt.plan(ROOT,'desktop',only_modules=('calf-webview',)); assert json.loads(a.read(base+'plan.json'))==json.loads(a.read('build/ci-plan/plan.json'))==plan
 assert rec['command']==lt.gradle_command('desktop',plan,root=ROOT) and rec['task_execution_markers']=={':calf-webview:desktopTest':1}
 for k in ('host','java','rust','android_platform','compiler_runtime_fingerprint'): assert rt[k]==setup[k],k
 assert rt['source_revision']==SHA and not rt['source_tree_dirty'] and rt['host']['system']=='Linux' and rt['host']['architecture']=='x64' and rt['java']['major']==17 and rt['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(rt)
 start,end=instant(rec['started_at_utc']),instant(rec['finished_at_utc']); assert instant(job['started_at'])<=start<end<=instant(job['completed_at']) and instant(job['started_at'])<=instant(rt['observed_at_utc'])<=instant(job['completed_at'])
 expected=set()
 for n in plan['expected'][0]['test_source_files']:
  text=blobs[n].decode(); methods=list(re.finditer(r'@Test\s*(?:@Suppress\([^\n]*\)\s*)?fun (`[^`\n]+`|[A-Za-z][A-Za-z0-9_]*)\(',text)); assert len(methods)==len(re.findall(r'@Test\b',text)); classes=list(re.finditer(r'^class ([A-Za-z][A-Za-z0-9_]*)',text,re.M)); assert classes,n
  for m in methods:
   cls=next(c.group(1) for c in reversed(classes) if c.start()<m.start()); expected.add((cls,m.group(1).strip('`')))
 assert len(expected)==40
 xmls=[e.filename for e in entries if e.filename.endswith('.xml')]; assert len(xmls)==7
 cases=[]; failed=[]; cookies=[]
 for n in xmls:
  data=a.read(n); assert b'<!DOCTYPE' not in data and b'<!ENTITY' not in data
  report=next(r for m in rec['modules'] for r in m['reports'] if r['path']==n); assert report['sha256']==hashlib.sha256(data).hexdigest()
  root=E.fromstring(data); assert start<=instant(root.attrib['timestamp'])<=end
  for c in root.findall('.//testcase'):
   assert not any(e.tag in ('error','skipped') for e in c); cases.append(c)
   if c.get('classname').endswith('.DesktopCookieManagerTest'):
    assert not any(e.tag=='failure' for e in c); cookies.append(c.get('name').split('[')[0])
   for e in c:
    if e.tag=='failure':failed.append({'classname':c.get('classname'),'method':c.get('name').split('[')[0],'message':e.get('message'),'type':e.get('type')})
 actual={(c.get('classname').split('.')[-1],c.get('name').split('[')[0]) for c in cases}; assert len(cases)==40 and actual==expected
 assert len(cookies)==8 and {m for names in criteria.values() for m in names}<=set(cookies)
 assert len(failed)==1 and failed[0]['method']=='nativeLinkRedirectReloadAndHistoryKeepRequestedAndRestoredUrlsCurrent' and failed[0]['message']== 'org.junit.ComparisonFailure: expected:<[C]> but was:<[A]>'
 assert rec['totals']['executed']==40 and rec['totals']['passed']==39 and rec['totals']['failures']==1 and rec['totals']['errors']==rec['totals']['skipped']==0
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'finding':'NATIVE-014','issue':71,'source_revision':SHA,'run_id':RUN,'run_url':run['html_url'],'whole_run_conclusion':'failure','whole_run_totals':rec['totals'],'whole_execution':rec['execution'],'source_inputs_verified_from_exact_Git_blobs':len(inputs),'artifact_every_XML_and_before_after_verified':True,'setup_runtime_correspondence':True,'important_cookie_tests':{'executed':8,'passed':8,'failures':0,'errors':0,'skipped':0,'source_methods':8,'new_methods':3,'methods':sorted(cookies)},'original_acceptance':[{'criterion':c,'accepted':True,'methods':ms} for c,ms in criteria.items()],'independent_failed_case':failed,'command':rec['command'],'runtime':rt,'scope':'Real independent java.net.CookieManager stores; exact original absolute metadata on delayed reads/copy, independent ownership, null/session/past/epoch/subsecond elapsed expiry and years0001-9999/invalid overflow without mutation. Foreign backend expiry remains unknown. Native Max-Age remains whole-second precision.','limitations':['No JavaFX authentication/global-cookie-store/native-header or threading certification; NATIVE-012/013 remain separate','Independent real JavaFX history pageTitle test failed and must be investigated; entire workflow remains failed','No physical/minimum/native sanitizer/ABI/legal/dependency/full-consumer/release gate'],'unrelated_successful_suites_replayed':False,'packages_releases_deployments_published':False}
(B/'important-result-review.json').write_text(json.dumps(review,indent=2)+'\n'); print(json.dumps({k:review[k] for k in ('passed','finding','run_id','important_cookie_tests','original_acceptance','whole_run_conclusion','independent_failed_case')},indent=2))
