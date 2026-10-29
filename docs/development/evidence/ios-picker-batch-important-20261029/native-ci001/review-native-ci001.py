"""Review finite already-executed CI receipts; never execute/extract artifact code or recreate a binary."""
from collections import Counter
from pathlib import Path, PurePosixPath
import datetime as dt, hashlib, json, re, stat, subprocess, sys, zipfile
ROOT=Path('/root/projects/nativeCmpKit'); B=Path('/dev/shm/nativecmpkit-ios-picker-batch-important-20261029/github-ci001')
REV='0aa8fc10abc72fb9c1dec37a2b6ce420b1243ba6'; REPO='Apdelrahman1911/nativeCmpkit'; RUN=40826758875; JOB=123291737284
sys.path.insert(0,str(ROOT/'scripts/ci')); import library_tests as lib, runtime_context as runtime
B.mkdir(exist_ok=True)
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def get(endpoint):return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/'+endpoint],cwd=ROOT))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def instant(s):
 v=dt.datetime.fromisoformat(s.replace('Z','+00:00')); assert v.utcoffset() is not None; return v
run=get('actions/runs/'+str(RUN));jobs=get('actions/runs/'+str(RUN)+'/jobs?per_page=100');arts=get('actions/runs/'+str(RUN)+'/artifacts?per_page=100')
assert run['id']==RUN and run['head_sha']==REV and run['run_attempt']==1 and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
for name,value in [('run-final.json',run),('jobs-final.json',jobs),('artifacts-final.json',arts)]:
 if run['status']=='completed':save(B/name,value)
job=next(j for j in jobs['jobs'] if j['id']==JOB)
if run['status']!='completed' or job['status']!='completed':
 print(json.dumps({'status':run['status'],'conclusion':run['conclusion'],'native_job':job['status'],'active_steps':[s['name'] for s in job['steps'] if s['status']=='in_progress']}));sys.exit(0)
assert next(j for j in jobs['jobs'] if j['name']=='tooling')['conclusion']=='success'
assert all(j['conclusion']=='skipped' for j in jobs['jobs'] if j['name'].startswith('consumer-'))
assert len(arts['artifacts'])==1
art=arts['artifacts'][0];assert art['name']=='library-evidence-ios-iphone' and not art['expired']
assert art['workflow_run']['id']==RUN and art['workflow_run']['head_sha']==REV and 0<art['size_in_bytes']<64*1024**2
zpath=B/(str(art['id'])+'.zip')
if not zpath.exists():
 with zpath.open('xb') as f:subprocess.run(['gh','api','repos/'+REPO+'/actions/artifacts/'+str(art['id'])+'/zip'],cwd=ROOT,stdout=f,check=True)
assert zpath.stat().st_size==art['size_in_bytes'] and 'sha256:'+sha(zpath.read_bytes())==art['digest']
with zipfile.ZipFile(zpath) as z:
 entries=z.infolist();names=[e.filename for e in entries];assert len(names)==len(set(names)) and sum(e.file_size for e in entries)<64*1024**2
 for e in entries:
  p=PurePosixPath(e.filename); assert not p.is_absolute() and not {'.','..'}&set(p.parts) and '\\' not in e.filename
  assert not e.is_dir() and not e.flag_bits&1 and stat.S_IFMT(e.external_attr>>16) in {0,stat.S_IFREG} and e.file_size<=16*1024**2
  assert e.filename.endswith(('.json','.xml')) and e.filename.startswith(('build/ci-','calf-file-picker/build/test-results/'))
 def data(n):return json.loads(z.read(n))
 o='build/ci-verification/ios-iphone/'; before=data(o+'inputs-before.json'); after=data(o+'inputs-after.json');assert before==after and len(before)==850
 # One Git batch, exact historical blobs, not current HEAD or an invented source hold.
 ordered=list(before);raw=subprocess.check_output(['git','cat-file','--batch'],input=''.join(REV+':'+p+'\n' for p in ordered).encode(),cwd=ROOT);off=0;blobs={}
 for p in ordered:
  newline=raw.index(b'\n',off);head=raw[off:newline].split();assert head[1]==b'blob',p
  size=int(head[2]);body=raw[newline+1:newline+1+size];assert sha(body)==before[p],p;blobs[p]=body;off=newline+size+2
 assert off==len(raw)
 rec=data(o+'receipt.json');context=data(o+'runtime.json');setup=data('build/ci-runtime/actual.json');plan=data(o+'plan.json')
 assert rec['source_revision']==rec['source_revision_after']==REV and rec['source_tree_dirty'] is False and rec['changed_inputs']==[]
 assert rec['inputs_before_sha256']==rec['inputs_after_sha256']==lib.input_digest(before) and rec['runtime_receipt_sha256']==sha(z.read(o+'runtime.json'))
 assert not rec['complete_suite_requested'] and rec['explicit_module_subset']==['calf-file-picker'] and rec['uncovered']==[]
 assert rec['explicit_test_focus']==plan['explicit_test_focus']==lib.IOS_PICKER_BOUNDARY_FOCUS
 assert plan==data('build/ci-plan/plan.json')==lib.plan(ROOT,'ios',only_modules=('calf-file-picker',),focus=lib.IOS_PICKER_BOUNDARY_FOCUS)
 for p in ('scripts/ci/library_tests.py','scripts/ci/ios_ui_application.py','scripts/ci/runtime_context.py',*lib.IOS_PICKER_APPLICATION_SOURCES,*(g['source'] for g in lib.IOS_PICKER_BOUNDARY_GROUPS)):
  assert (ROOT/p).read_bytes()==blobs[p],p
 assert lib.validate_test_focus(plan)
 assert rec['gradle_daemon']['major']==context['java']['major']==17 and rec['gradle_daemon']['launcher_home_matches_daemon']
 assert context['source_revision']==REV and not context['source_tree_dirty'] and context['host']['system']=='Darwin' and context['host']['architecture']=='arm64'
 assert context['rust']['release']=='1.98.0' and context['simulator']['state']=='Booted' and context['simulator']['device_type'].startswith('com.apple.CoreSimulator.SimDeviceType.iPhone')
 assert runtime.UUID.fullmatch(context['simulator']['udid']) and context['compiler_runtime_fingerprint']==runtime.compiler_runtime_fingerprint(context)
 assert {k for k in set(setup)|set(context) if setup.get(k)!=context.get(k)}=={'observed_at_utc'}
 assert rec['command']==lib.gradle_command('ios',plan,simulator=context['simulator']['udid'],root=ROOT)
 assert len(rec['modules'])==1;module=rec['modules'][0];assert module['module']=='calf-file-picker' and module['task']==':calf-file-picker:iosSimulatorArm64ApplicationTest'
 assert rec['task_execution_markers']=={module['task']:1} and not rec['execution'].get('stop_reason')
 start,end=instant(rec['started_at_utc']),instant(rec['finished_at_utc']);assert instant(job['started_at'])<=start<end<=instant(job['completed_at'])
 reports=module['reports']; xml_names=[n for n in names if n.endswith('.xml')];assert len(reports)==len(xml_names)==7
 import xml.etree.ElementTree as ET
 cases=[];xml_rows=[]
 for r in reports:
  raw=z.read(r['path']);assert sha(raw)==r['sha256'] and b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw
  doc=ET.fromstring(raw);assert start<=instant(doc.attrib['timestamp'])<=end
  current=lib.junit_cases(raw);cases.extend(current);xml_rows.append({'path':r['path'],'original_sha256':sha(raw),'cases':current})
 assert cases==module['testcases'] and len(cases)==26
 required=lib.ui_application_focus_identities(lib.IOS_PICKER_BOUNDARY_FOCUS)
 assert {(c['classname'],c['name']) for c in cases}=={(c['classname'],c['name']) for c in required} and len({(c['classname'],c['name']) for c in cases})==26
 counts=lib.case_counts(cases);assert counts==rec['totals'] and counts['tests']==counts['executed']==26 and counts['skipped']==0
 info=rec['ios_applications'];assert len(info)==1 and info[0]['module']=='calf-file-picker' and info[0]['protocol_xml_agreement']
 app_path=info[0]['receipt_path'];app_raw=z.read(app_path);assert sha(app_raw)==info[0]['receipt_sha256'];app=json.loads(app_raw);token=PurePosixPath(app_path).parent.name
 assert re.fullmatch('[0-9a-f]{32}',token) and '/native-picker-application/' in app_path
 assert app['bundle_id']=='io.github.apdelrahman1911.nativecmpkit.verification.ui.r'+REV[:12]+'.t'+token
 assert app['task']==module['task'] and app['transport_passed'] is True and app['source_revision']==REV and app['source_tree_dirty'] is False
 assert app['explicit_test_focus']==plan['explicit_test_focus'] and not app['packages_published'] and not app['release_readiness_certified']
 assert not any(k in app for k in ('error','startup_failure_observation','application_protocol_partial','owned_crash_diagnostics'))
 assert app['binary_path'].startswith('calf-file-picker/build/bin/iosSimulatorArm64/applicationDebugTest/') and app['binary_path'].endswith('.kexe')
 assert app['binary_sha256']==app['binary_sha256_after']==info[0]['binary_sha256'] and re.fullmatch('[0-9a-f]{64}',app['binary_sha256'])
 assert app['macho']==app['signed_macho_identity'] and app['macho']['architecture']=='arm64' and app['macho']['platform']==7
 for k in ('signed_application_executable_sha256','application_plist_sha256'):assert re.fullmatch('[0-9a-f]{64}',app[k])
 for when in ('runtime_before','runtime_after'):
  observed=app[when];assert observed['source_revision']==REV and not observed['source_tree_dirty']
  for k in ('host','java','rust','xcode','apple_sdks','simulator'):assert observed[k]==context[k],k
 assert app['steps']['foreign-app-preflight']['preexisting_app_absence_verified']
 assert app['steps']['adhoc-sign-local-verification-app']['exit_code']==0 and not app['steps']['adhoc-sign-local-verification-app']['remote_signing_or_publication']
 assert app['steps']['install-owned-app']['exit_code']==0 and app['steps']['install-owned-app']['installed_owned_bytes_verified']
 assert app['cleanup']['uninstall_exit_code']==0 and not any('error' in k for k in app['cleanup'])
 assert all(app['cleanup'][k] for k in ('owned_app_identity_reverified','owned_app_stopped_verified','owned_app_absence_verified','owned_local_bundle_removed'))
 proto=app['application_protocol'];assert proto['process_exit']==0 and proto['activation']==info[0]['activation']
 assert proto['activation']['main_worker']!=proto['activation']['owned_worker'] and min(proto['activation'].values())>0
 assert proto['completion']=={'runner_exit':0,'worker_terminated':True}==info[0]['completion']
 assert {(c['classname'],c['name'],c['status']) for c in proto['testcases']}=={(c['classname'].removeprefix('iosSimulatorArm64ApplicationTest.'),c['name'].removesuffix('[iosSimulatorArm64]'),c['status']) for c in cases}
 assert lib.case_counts(proto['testcases'])==counts==proto['counts']==info[0]['counts']
 assert start<=instant(app['started_at_utc'])<=instant(app['finished_at_utc'])<=end
 fresh_owners={p:before[p] for p in before if p.startswith(('calf-file-picker/src/iosMain/','calf-io/src/'))}
 changed_now=[p for p,h in fresh_owners.items() if sha((ROOT/p).read_bytes())!=h]
 # New unrelated browser test was added after native checkout, not substituted into this native result.
 assert changed_now==[]
 review={'reviewed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'evidence_integrity_passed':True,'source_revision':REV,'run_id':RUN,'run_url':run['html_url'],'run_attempt':1,'workflow_conclusion':run['conclusion'],'native_job_id':JOB,'native_job_conclusion':job['conclusion'],'artifact_id':art['id'],'artifact_digest':art['digest'],'artifact_size_bytes':art['size_in_bytes'],'all_850_inputs_before_after_immutable_Git_match':True,'current_existing_owning_inputs_unchanged':True,'actual_runtime':context,'gradle_daemon':rec['gradle_daemon'],'command':rec['command'],'execution':rec['execution'],'totals':counts,'fresh_report_count':len(reports),'actual_testcases':cases,'xml_raw_hashes':xml_rows,'all_26_exact_selected_identities_discovered_once':True,'independent_protocol_XML_runtime_Worker_owned_cleanup_checked':True,'live_binary_gate_scope':'Producer recorded successful real linked binary/Mach-O/freshness checks; reports-only independent review does not recreate absent executable or reexecute live host checks. No native app/binary/ZIP payload committed.','new_or_cloned_methods':14,'existing_methods_not_previously_accepted_on_Apple':12,'unchanged_accepted_IO_Coil_native_false_write_other_host_suites_replayed':False,'publication_or_release_certified':False,'original_criteria_decisions':'Review original IO-014/IO-025 plus separate provider/swipe/export/parent/limit gates before any closure.'}
 save(B/'lead-independent-review.json',review)
 save(B/'artifact-member-inventory.json',{'id':art['id'],'digest':art['digest'],'members':[{'path':e.filename,'bytes':e.file_size,'original_sha256':sha(z.read(e.filename))} for e in entries]})
 print(json.dumps({k:review[k] for k in ('evidence_integrity_passed','run_id','workflow_conclusion','native_job_conclusion','totals','execution','fresh_report_count')},indent=2))
