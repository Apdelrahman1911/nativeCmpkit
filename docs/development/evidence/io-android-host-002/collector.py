from pathlib import Path
import json,hashlib,datetime as dt,os,re,sys,xml.etree.ElementTree as E
root=Path('/root/projects/nativeCmpKit');sys.path.insert(0,str(root/'scripts/ci'));import library_tests
name=sys.argv[1];assert re.fullmatch(r'[a-z0-9-]+',name)
source=root/'build/ci-verification'/name;dest=root/'docs/development/evidence'/name;assert not dest.exists()
r=json.loads((source/'receipt.json').read_text());before=json.loads((source/'inputs-before.json').read_text());after=json.loads((source/'inputs-after.json').read_text())
assert before==after and not r['changed_inputs'] and library_tests.snapshot_inputs(root)==after
expanded=json.loads((root/'docs/development/evidence/build/yarn-materialization-003.after-inputs.json').read_text())['files']
expanded_changes=[p for p,h in expanded.items() if not (root/p).is_file() or hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
# Later reruns may intentionally change inputs; always report exact drift, never upgrade stale validation.
dest.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
entries=[]
for n in ['inputs-before.json','inputs-after.json','plan.json','runtime.json','receipt.json']:
 p=source/n;d=dest/n;put(d,p.read_bytes());entries.append({'source':str(p.relative_to(root)),'archive':str(d.relative_to(root)),'sha256':sha(d)})
lines=(source/'gradle.log').read_text(errors='replace').splitlines();selected=[]
for l in lines:
 if l.startswith(('> Task ', 'NATIVECMPKIT_TEST_RUNTIME ', 'e: file:', 'BUILD ', 'FAILURE:', 'Execution failed for task', 'com.mohamedrejeb.calf.')) or re.fullmatch(r'\d+ tests completed(?:, \d+ failed)?',l) or re.fullmatch(r'\d+ actionable tasks: .*',l):selected.append(l)
put(dest/'gradle.sanitized.log',('\n'.join(selected)+'\n').encode())
counts={'tests':0,'passed':0,'failed':0,'skipped':0};reports=[];failures=[]
for m in r['modules']:
 for report in m['reports']:
  p=root/report['path'];assert sha(p)==report['sha256']
  cases=library_tests.junit_cases(p.read_bytes());doc=E.fromstring(p.read_bytes());elements=doc.findall('.//testcase')
  assert len(cases)==len(elements)
  clean=E.Element('testsuite',{'name':doc.attrib.get('name',m['module']),'tests':str(len(cases)),'failures':str(report['failures']),'errors':str(report['errors']),'skipped':str(report['skipped'])})
  for c,t in zip(cases,elements):
   assert c['name']==t.attrib['name'] and c['classname']==t.attrib['classname']
   n=E.SubElement(clean,'testcase',{'classname':c['classname'],'name':c['name'],'time':t.attrib.get('time','0')})
   counts['tests']+=1;counts['passed' if c['status']=='passed' else ('skipped' if c['status']=='skipped' else 'failed')]+=1
   for tag in ['failure','error','skipped']:
    old=t.find(tag)
    if old is not None:
     # Preserve reviewed failure type/message; omit host properties and console/stack bodies.
     attrs={k:v for k,v in old.attrib.items() if k in ['type','message']}
     E.SubElement(n,tag,attrs)
     if tag!='skipped':failures.append({'module':m['module'],'classname':c['classname'],'name':c['name'],'type':attrs.get('type'),'message':attrs.get('message'),'source_report':report['path'],'source_sha256':report['sha256']})
  d=dest/'reports'/m['module']/p.name;payload=E.tostring(clean,encoding='utf-8',xml_declaration=True)+b'\n';put(d,payload)
  assert library_tests.junit_cases(payload)==cases
  st=p.stat();start=dt.datetime.fromisoformat(r['started_at_utc']).timestamp();end=dt.datetime.fromisoformat(r['finished_at_utc']).timestamp();assert start-1<=st.st_mtime<=end+1
  reports.append({'source':report['path'],'raw_sha256':report['sha256'],'archive':str(d.relative_to(root)),'archive_sha256':sha(d),'source_mtime_utc':dt.datetime.fromtimestamp(st.st_mtime,dt.timezone.utc).isoformat(),'within_run_interval':True,'testcases':len(cases)})
assert counts['tests']==r['totals']['tests'] and counts['passed']==r['totals']['passed']
for n in (['chrome-for-library-tests','context.json'] if r['suite'] in ['js','wasm'] else []):
 p=root/'build/browser-runtime-001'/n;d=dest/'browser-context'/n;put(d,p.read_bytes());entries.append({'source':str(p.relative_to(root)),'archive':str(d.relative_to(root)),'sha256':sha(d)})
summary={'schema_version':1,'collected_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Actual '+('complete-requested' if r['complete_suite_requested'] else 'explicit-subset')+' library '+r['suite']+' runtime diagnostic. Original outcome is preserved; no compilation-only, stale, skipped or missing suite counted as a pass.','producer_receipt_sha256':sha(source/'receipt.json'),'source_revision':r['source_revision'],'source_tree_dirty':r['source_tree_dirty'],'command':r['command'],'execution':r['execution'],'passed':r['passed'],'started_utc':r['started_at_utc'],'finished_utc':r['finished_at_utc'],'complete_suite_requested':r['complete_suite_requested'],'outer_invocation_context':('xvfb-run -a existing helper; real Xvfb desktop context' if r['suite']=='desktop' else ('JVM Android-host tests under Robolectric; no emulator/device. Fixed lead launcher and executable hashes are recorded separately in the host context archive.' if r['suite']=='android-host' else 'Explicit local Chrome wrapper; browser version captured in runtime.json. Any requested Kotlin home must be independently checked against fresh generated Karma configurations.')),'modules_requested':len(r['modules']),'modules_with_test_execution':sum(m['executed']>0 for m in r['modules']),'totals':r['totals'],'report_count':len(reports),'failure_details':failures,'errors':r['errors'],'selected_input_count':len(before),'selected_inputs_unchanged':True,'expanded_yarn_bootstrap_input_count':len(expanded),'expanded_input_changes_since_yarn_bootstrap':expanded_changes,'input_scope_note':'Helper captures selected library/build inputs; use the explicit counts and before/after maps in this archive. The historical Yarn bootstrap freeze separately included notice/identity/license files; drift from that earlier snapshot is listed, not retroactively verified.','raw_log':{'path':str((source/'gradle.log').relative_to(root)),'sha256':sha(source/'gradle.log'),'archived':False},'sanitized_log_sha256':sha(dest/'gradle.sanitized.log'),'collector_sha256':sha(Path(__file__)),'archives':entries,'reports':reports,'limitations':['Held dirty source at base commit; not immutable candidate or hermetic builder.',('Android-host uses JVM/Robolectric, not an Android device, emulator, or SDK-minimum runtime certification.' if r['suite']=='android-host' else 'Chrome153 uses explicit local root-container --no-sandbox/--disable-dev-shm-usage wrapper for browser suites, not a production WebView policy change or browser security clearance.'),'Source/common/stub/DOM tests are not native picker dialogs or physical camera/permission functionality.','Dependency lock/install/context observations and library tests do not certify ordinary frozen/closure enforcement or independent dependency provenance.','Prior successful target suites cannot hide a failure/missing suite in this invocation.','No remote CI, Maven consumer, release, package or Pages action.']}
put(dest/'archive.json',(json.dumps(summary,indent=2)+'\n').encode())
put(dest/'collector.py',Path(__file__).read_bytes())
paths=sorted(p for p in dest.rglob('*') if p.is_file());put(dest/'SHA256SUMS',(''.join(f'{sha(p)}  {p.relative_to(dest).as_posix()}\n' for p in paths)).encode())
assert library_tests.snapshot_inputs(root)==after
print(json.dumps({'archive':str(dest.relative_to(root)),'summary_sha256':sha(dest/'archive.json'),'bound_files':len(paths),'selected_inputs':len(before),'expanded_input_changes':expanded_changes,'report_count':len(reports),'totals':r['totals'],'overall_passed':r['passed']},indent=2))
