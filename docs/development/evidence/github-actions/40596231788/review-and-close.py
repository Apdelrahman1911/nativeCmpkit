"""Exact immutable WebView important-test review followed by direct NATIVE-001 closure."""
from collections import Counter
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,json,re,stat,subprocess,sys,xml.etree.ElementTree as ET,zipfile
root=Path('/root/projects/nativeCmpKit');out=Path(__file__).parent
source=Path('/dev/shm/nativecmpkit-ci-4fb7d886-20261027/40596231788')
repo='Apdelrahman1911/nativeCmpkit';run_id=40596231788;revision='4fb7d886d533610c7e4bf55535ea980ff050a144'
slot='desktop-linux-x64';marker='<!-- nativecmpkit-resolution:NATIVE-001:40596231788 -->'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def instant(v):
 result=dt.datetime.fromisoformat(v.replace('Z','+00:00'));assert result.utcoffset() is not None;return result
def document(raw):
 def unique(pairs):
  d={}
  for k,v in pairs:assert k not in d,'Duplicate JSON key';d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def save(name,data):(out/name).write_text(json.dumps(data,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=root)
def api(name,endpoint,method='GET',body=None):
 cmd=['gh','api','repos/'+repo+'/'+endpoint,'--method',method]
 if body is not None:cmd+=['--input','-']
 r=subprocess.run(cmd,input=json.dumps(body).encode() if body is not None else None,capture_output=True,timeout=90)
 (out/(name+'.json')).write_bytes(r.stdout)
 if r.stderr:(out/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,'API failure: inspect saved response before any retry or mutation'
 return document(r.stdout)
assert git('rev-parse','HEAD').decode().strip()==revision
run=document((source/'run-final.json').read_bytes());jobs=document((source/'jobs-final.json').read_bytes())['jobs']
artifacts=document((source/'artifacts-final.json').read_bytes())['artifacts'];collection=document((source/'collection.json').read_bytes())
assert run['id']==run_id and run['repository']['full_name']==repo and run['head_sha']==revision
assert run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening' and run['run_attempt']==1
assert run['status']=='completed' and run['conclusion']=='success'
assert collection['run_id']==run_id and collection['source_revision']==revision and collection['profile']=='webview-desktop'
assert collection['selected_job_count']==1 and collection['artifact_digests_matched']
selected=[j for j in jobs if j['name'].startswith('library-tests (')];assert len(selected)==1
job=selected[0];assert job['name']=='library-tests (desktop-linux-x64, desktop, ubuntu-24.04, x64, python3, calf-webview)'
assert job['status']=='completed' and job['conclusion']=='success' and job['run_attempt']==1
assert next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
assert next(j for j in jobs if j['name']=='consumer-core-io')['conclusion']=='skipped'
steps={s['name']:s for s in job['steps']};assert steps['Fresh actual library suite with strict nonzero receipts']['conclusion']=='success'
assert steps['Keep receipts and actual selected-task XML only; never packages']['conclusion']=='success'
assert len(artifacts)==1;a=artifacts[0]
assert a['name']=='library-evidence-'+slot and not a['expired'] and a['workflow_run']['id']==run_id and a['workflow_run']['head_sha']==revision
zip_path=source/(str(a['id'])+'.zip');assert zip_path.stat().st_size==a['size_in_bytes']<64*1024**2 and 'sha256:'+sha(zip_path.read_bytes())==a['digest']
log=source/('job-'+str(job['id'])+'-log.log');log_record=next(r for r in collection['logs'] if r['job_id']==job['id'])
assert log.stat().st_size==log_record['job_log_bytes'] and sha(log.read_bytes())==log_record['job_log_sha256'] and not log_record['job_log_to_be_committed']
sys.path.insert(0,str(root/'scripts/ci'))
import library_tests as lt, runtime_context as rc, dependency_cache_inputs as keys
# Each selected file is compared to an immutable Git blob, not only a controller's digest.
inputs=lt.snapshot_inputs(root);assert len(inputs)==734
for path,digest in inputs.items():assert sha(git('show',revision+':'+path))==digest,'Selected input differs from this exact own-Git revision'
plan=lt.plan(root,'desktop',only_modules=('calf-webview',));assert len(plan['expected'])==1
expected=plan['expected'][0];assert expected['task']==':calf-webview:desktopTest'
methods=[]
for path in expected['test_source_files']:
 raw=(root/path).read_text();found=re.findall(r'@Test\s*(?:@Suppress\([^\n]*\)\s*)?fun\s+(`[^`\n]+`|[A-Za-z_][A-Za-z0-9_]*)\s*\(',raw)
 assert len(found)==len(re.findall(r'@Test\b',raw)),'Unrecognized actual authored method'
 methods += [name.strip('`')+'[desktop]' for name in found]
assert len(methods)==37
with zipfile.ZipFile(zip_path) as z:
 entries=z.infolist();names=[e.filename for e in entries];assert len(names)==len(set(names))==15
 assert sum(e.file_size for e in entries)<64*1024**2
 for e in entries:
  p=PurePosixPath(e.filename);assert not p.is_absolute() and not {'.','..'} & set(p.parts) and '\\' not in e.filename
  assert not e.is_dir() and not e.flag_bits&1 and stat.S_IFMT(e.external_attr>>16) in {0,stat.S_IFREG}
  assert e.filename.endswith(('.json','.xml')) and e.file_size<=lt.MAX_REPORT_BYTES
 def get(n):return document(z.read(n))
 base='build/ci-verification/'+slot+'/'
 receipt=get(base+'receipt.json');before=get(base+'inputs-before.json');after=get(base+'inputs-after.json')
 assert before==after==inputs and receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(inputs)
 assert receipt['source_revision']==receipt['source_revision_after']==revision and not receipt['source_tree_dirty'] and not receipt['changed_inputs']
 assert get(base+'plan.json')==get('build/ci-plan/plan.json')==plan and receipt['explicit_module_subset']==['calf-webview']
 assert not receipt['complete_suite_requested'] and receipt['test_bearing_modules_not_requested']==plan['test_bearing_modules_not_requested']
 runtime=get(base+'runtime.json');actual=get('build/ci-runtime/actual.json')
 assert receipt['runtime_receipt_sha256']==sha(z.read(base+'runtime.json'))
 for c in (runtime,actual):
  assert c['source_revision']==revision and not c['source_tree_dirty'] and c['compiler_runtime_fingerprint']==rc.compiler_runtime_fingerprint(c)
  assert c['host']['system']=='Linux' and c['host']['architecture']=='x64' and c['java']['major']==17
  assert instant(job['started_at'])<=instant(c['observed_at_utc'])<=instant(job['completed_at'])
 assert {k for k in set(runtime)|set(actual) if runtime.get(k)!=actual.get(k)}=={'observed_at_utc'}
 assert runtime['android_platform']['package']=='platforms;android-37.0'
 dependencies=get('build/ci-runtime/library-dependencies.json');dep_inputs=keys.selected_inputs(root,'libraries');selection=keys.selection_contract(root,'calf-webview')
 assert dependencies['source_revision']==revision and dependencies['inputs']==dep_inputs and dependencies['selected_modules']==selection['modules']==['calf-webview']
 assert dependencies['dependency_inputs_sha256']==keys.fingerprint('libraries',dep_inputs) and not dependencies['compiled_or_test_results_reused']
 assert receipt['command']==lt.gradle_command('desktop',plan,root=root) and receipt['execution']['exit_code']==0 and not receipt['execution'].get('stop_reason')
 assert receipt['task_execution_markers']=={':calf-webview:desktopTest':1} and receipt['passed'] and not receipt['errors']
 assert not receipt['quarantined_prior_reports'] and not receipt['uncovered'] and not receipt['ios_applications']
 start=instant(receipt['started_at_utc']);end=instant(receipt['finished_at_utc']);assert instant(job['started_at'])<=start<end<=instant(job['completed_at'])
 module=receipt['modules'][0];assert len(receipt['modules'])==1 and module['module']=='calf-webview'
 reports=module['reports'];assert len(reports)==7 and {r['path'] for r in reports}=={n for n in names if n.endswith('.xml')}
 cases=[];xml=[]
 for r in reports:
  raw=z.read(r['path']);assert sha(raw)==r['sha256'] and r['path'].startswith(expected['report_directory']+'/')
  found=lt.junit_cases(raw);assert all(c['status']=='passed' for c in found)
  counts=lt.case_counts(found);assert all(r[k]==v for k,v in counts.items())
  t=ET.fromstring(raw,parser=ET.XMLParser(target=lt.NoDtdBuilder()));assert start<=instant(t.attrib['timestamp'])<=end
  xml.append({'path':r['path'],'sha256':sha(raw),'timestamp':t.attrib['timestamp']});cases+=found
 assert len(cases)==len({(c['classname'],c['name']) for c in cases})==37
 assert Counter(c['name'] for c in cases)==Counter(methods)
 assert sorted(cases,key=lambda c:(c['classname'],c['name']))==sorted(module['testcases'],key=lambda c:(c['classname'],c['name']))
 totals=lt.case_counts(cases);assert totals==receipt['totals'] and all(module[k]==v for k,v in totals.items())
 mandatory=['stopCancelsRealSlowLoadWithoutFeedbackLoop','repeatedStopsAfterDetachAndReattachCancelOnlyTheCurrentRealLoad']
 assert len(module['native_scenarios'])==2 and {c['method'] for c in module['native_scenarios']}==set(mandatory)
 assert all(c['disposition']=='required-executed' and c['required_on_host'] and c['host']=='linux' for c in module['native_scenarios'])
 stop_cases=[]
 for name in mandatory:
  found=[c for c in cases if c['classname']=='com.mohamedrejeb.calf.ui.web.JavaFxWebViewTest' and c['name']==name+'[desktop]'];assert len(found)==1;stop_cases+=found
 with zipfile.ZipFile(root/'docs/development/evidence/github-actions/40568592687/raw/12764597746.zip') as old:
  prior=[c for n in old.namelist() if n.startswith('calf-webview/') and n.endswith('.xml') for c in lt.junit_cases(old.read(n))]
 previous={(c['classname'],c['name']) for c in prior};now={(c['classname'],c['name']) for c in cases}
 assert len(previous)==36 and previous<now and len(now-previous)==1
 console=log.read_text()
 # Successful controller deliberately keeps child Gradle logs private; task markers
 # are its exact-source inspected assertion, not independent raw child-log recount.
 assert 'xvfb-run -a \"$PYTHON\" scripts/ci/library_tests.py' in console
 assert '\"passed\": true' in console and '\"elapsed_seconds\": 245.07' in console
production=root/'calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt'
code=production.read_text();navigate=code[code.index('suspend fun navigate('):code.index('    fun evaluate(',code.index('suspend fun navigate('))]
assert 'NavigationEvent.StopLoading -> engine.loadWorker.cancel()' in navigate and 'stopLoading()' not in navigate
assert 'suspend fun navigate(event: WebViewNavigator.NavigationEvent) = onFxThread {' in navigate
finding=next(f for f in document((root/'docs/audit/findings/NATIVE.json').read_bytes()) if f['id']=='NATIVE-001');assert len(finding['required_tests'])==2
criteria=[{'original_requirement':req,'status':'accepted','actual_cases':stop_cases,'source_review':'FX-confined explicit direct cancel branch emits no new event; source plus real cancellation transitions/one command counts, not instrumented method-call profiling.'} for req in finding['required_tests']]
acceptance={'reviewed_utc':stamp(),'finding':'NATIVE-001','run_id':run_id,'run_url':run['html_url'],'source_revision':revision,'job_id':job['id'],'artifact_id':a['id'],'artifact_digest':a['digest'],'all_734_selected_inputs_equal_exact_own_Git':True,'source_input_count':len(inputs),'source_digest':lt.input_digest(inputs),'command':receipt['command'],'execution':receipt['execution'],'runtime':runtime,'setup_test_SDK_and_global_fingerprints_match':True,'totals':totals,'XML_reports':xml,'actual_cases':cases,'all_36_previous_identities_retained':True,'mandatory_native_cases':stop_cases,'all_two_original_criteria_accepted':True,'criteria':criteria,'raw_log_sha256':sha(log.read_bytes()),'raw_log_bytes':log.stat().st_size,'raw_log_to_be_committed':False,'native_marker_evidence':'Exact source-bound controller parses the private Gradle log; successful job uploads reports/receipts, not that child log. No independent raw marker recount claimed.','limits':['Actual JavaFX production owner/JFXPanel in a visible native JFrame under Linux/Xvfb; public Compose mount/disposal/GC/cold-start certification remains separate.','Native cancellation transition counts and source one direct call are not instrumentation of every Worker invocation.','Other-host/minimum-platform, Chromium/Apple/native ownership, cookie/security, packaged consumer/API-ABI/legal/dependency/release gates remain open.'],'publication_performed':False,'release_readiness_certified':False}
save('acceptance.json',acceptance);print('Reviewed37/37 actual desktop methods,7 fresh XML,734 exact Git inputs; both NATIVE-001 criteria accepted.',flush=True)
issue=api('issue-before','issues/9');assert issue['state']=='open' and '<!-- nativecmpkit-item:audit:NATIVE-001 -->' in issue['body']
assert all(req in issue['body'] for req in finding['required_tests'])
comments=api('comments-before','issues/9/comments?per_page=100');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
body=f'''{marker}
## Verified resolution — NATIVE-001

`DesktopWebViewOwner.navigate(StopLoading)` now calls `engine.loadWorker.cancel()` explicitly on the FX thread. The stop branch has one direct native call and does not invoke `navigator.stopLoading()` or emit another event; public `stopLoading()` is retained.

**Both original criteria accepted:**
- The existing real slow-HTTP/JavaFX regression observes actual stopped loading and exactly one consumed stop command, without feedback.
- The new real native-window regression mounts the production JFXPanel/owner in a visible JFrame. Two blocked HTTP requests verify attached stop, detached queued stop delivered on reattachment, repeated idle stops and no replay on a later attachment. Actual Worker cancellation transitions and command counts are asserted; owned listeners, collectors, HTTP threads and window are cleaned up.

[Immutable Linux/Xvfb run{run_id}](https://github.com/{repo}/actions/runs/{run_id}) at `{revision}`: **37/37 actual methods**, **seven fresh XML**, all eight JavaFX methods and both mandatory stop cases passed; Gradle exit0/{receipt['execution']['elapsed_seconds']}s. Reviewed all734 selected inputs against exact own-Git blobs, command/task execution, fresh XML hashes/timestamps, retained36 previous identities and matching setup/during-test SDK/runtime fingerprints.

Closing directly after required-test/source/result review, before documentation bookkeeping. This is actual JavaFX/AWT native-window integration, not public Compose disposal/GC certification. Cancellation transitions plus the one-call source branch are not instrumented counts of every Worker invocation. Other-host/minimum-platform, Chromium/Apple/ownership, cookie/security, legal/dependency, packaged consumer/API-ABI and release gates remain independent/open. No packages, releases or deployments published. Original issue body/title/labels/history preserved.
'''
(out/'comment.md').write_text(body)
posted=api('comment-post','issues/9/comments','POST',{'body':body});assert posted['body']==body
closed=api('issue-patch','issues/9','PATCH',{'state':'closed','state_reason':'completed'});assert closed['state']=='closed'
after=api('issue-after','issues/9');comment=api('comment-after','issues/comments/'+str(posted['id']))
assert after['state']=='closed' and comment['body']==body and after['body']==issue['body'] and after['title']==issue['title']
assert sorted(l['name'] for l in after['labels'])==sorted(l['name'] for l in issue['labels'])
save('closure.json',{'reviewed_utc':stamp(),'passed':True,'finding':'NATIVE-001','issue_number':9,'state':'closed','closed_at':after['closed_at'],'comment_id':posted['id'],'comment_url':posted['html_url'],'source_revision':revision,'run_id':run_id,'all_two_original_criteria_accepted':True,'POST_invocations':1,'PATCH_invocations':1,'original_body_title_labels_preserved':True,'new_test_executions':37,'publication_performed':False,'release_readiness_certified':False})
print(json.dumps({'issue':9,'state':after['state'],'comment_url':posted['html_url'],'methods':37,'native_stop_cases':2}),flush=True)
