"""Review once-acquired Windows TLS originals; no tests, builds or network."""
import datetime,hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path('/root/nativecmpkit-native-reviews-20261101');OUT=Path(__file__).parent
ORIGINAL=Path((BASE/'SECURITY412-CURRENT-ORIGINAL').read_text().strip());DISPATCH=Path((BASE/'SECURITY411-CURRENT-DISPATCH').read_text().strip())
REV='ae7893816f147ed7b54db0676c77e500a3346056';RUN=41545807583
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as library;import desktop_security_plan as security
checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def read(p):return json.loads(p.read_bytes())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,value):
 with (OUT/name).open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
frozen=read(DISPATCH/'library-inputs.json');before=library.snapshot_inputs(ROOT)
check('all1223 current library inputs equal immutable dispatch411 freeze',before==frozen and len(frozen)==1223)
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
raw=p.communicate(('\n'.join(REV+':'+relative for relative in frozen)+'\n').encode())[0];check('own-Git source batch exits0',p.returncode==0);pos=0
for relative,digest in frozen.items():
 end=raw.index(b'\n',pos);header=raw[pos:end].split();size=int(header[2]);start=end+1;value=raw[start:start+size];pos=start+size+1
 if header[1]!=b'blob' or sha(value)!=digest:raise AssertionError('immutable blob '+relative)
check('every1223 frozen pin equals exact complete own Git blob batch',pos==len(raw))
run=read(ORIGINAL/'run.json');check('completed original41545807583 attempt1 exact development head',tuple(run[k] for k in ('id','run_attempt','status','head_sha','head_branch','event'))==(RUN,1,'completed',REV,'development/preview-hardening','workflow_dispatch'))
acq=read(ORIGINAL/'ACQUISITION412.json');claim=read(BASE/('security-%s-attempt1-original-acquisition.claim.json'%RUN))
check('exclusive solo412 once-acquired original conclusion custody',acq['owner']==claim['owner']=='solo-lead' and acq['directory']==claim['directory']==str(ORIGINAL) and acq['no_duplicate_acquisition'] is True and acq['conclusion']==run['conclusion'])
for item in acq['files']:
 value=(ORIGINAL/item['file']).read_bytes();check('original hash '+item['file'],item['exit_code']==0 and len(value)==item['bytes'] and sha(value)==item['sha256'])
for item in acq['artifact_members']:
 value=(ORIGINAL/'evidence'/item['artifact_name']/item['name']).read_bytes()
 if len(value)!=item['bytes'] or sha(value)!=item['sha256']:raise AssertionError('cached original artifact member '+item['name'])
check('all cached artifact members rehash original412 acquisition',True)
check('no acquired graph or accepted other-method members',not any('desktop-dependencies' in r['name'] for r in acq['artifact_members']))
artifacts=read(ORIGINAL/'artifacts.json');jobs=read(ORIGINAL/'jobs.json')['jobs'];native_jobs=[j for j in jobs if j['name'].startswith('library-tests (')]
if artifacts['total_count']==0:
 check('zero artifacts only after native preparation or tooling refusal',run['conclusion']!='success')
 save('REVIEW413.json',{'schema_version':1,'run':RUN,'source_sha':REV,'original_conclusion':run['conclusion'],'checks':checks,'passive_check_count':len(checks),'native_executed':0,'native_passed':0,'XML':0,'all_native_accepted':False,'jobs':acq['jobs'],'native_replays':0,'original_redownloads':0,'release_allowed':False,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 print(json.dumps({'native_executed':0,'native_passed':0,'original_conclusion':run['conclusion'],'artifacts':0}));sys.exit(0)
check('one original Windows host artifact no accepted pair replay',artifacts['total_count']==1 and artifacts['artifacts'][0]['name']=='library-evidence-desktop-windows-x64')
check('only one selected native job and source tooling success',len(native_jobs)==1 and next(j for j in jobs if j['name']=='tooling')['conclusion']=='success')
check('all unrelated jobs remain skipped',all(j['conclusion']=='skipped' for j in jobs if j['name']!='tooling' and not j['name'].startswith('library-tests (')))
slot='desktop-windows-x64';artifact=ORIGINAL/'evidence'/('library-evidence-'+slot);native=artifact/'build/ci-verification'/slot
receipt=read(native/'receipt.json');context=read(native/'runtime.json');plan=read(native/'plan.json');focus=security.WINDOWS_TLS_RECOVERY_FOCUS;selection=security.focus_selection(focus)
check('actual Windows x64 Java17 clean immutable source/runtime',receipt['source_revision']==receipt['source_revision_after']==context['source_revision']==REV and receipt['source_tree_dirty'] is False and context['source_tree_dirty'] is False and context['host']['system']=='Windows' and context['host']['architecture']=='x64' and context['java']['major']==17)
check('actual Gradle9.7.1 daemon matches owning launcher JDK',receipt['gradle_daemon']['gradle_version']=='9.7.1' and receipt['gradle_daemon']['java_version']==context['java']['version'] and receipt['gradle_daemon']['launcher_home_matches_daemon'] is True)
check('actual1223 before-after native maps frozen digest and runtime hash held',read(native/'inputs-before.json')==read(native/'inputs-after.json')==frozen and receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==library.input_digest(frozen) and receipt['changed_inputs']==[] and receipt['runtime_receipt_sha256']==sha((native/'runtime.json').read_bytes()))
check('exact fresh single task focus subset no sample application substitute',receipt['task_execution_markers']=={':calf-webview:desktopTest':1} and receipt['explicit_module_subset']==['calf-webview'] and receipt['explicit_test_focus']==focus and receipt['complete_suite_requested'] is False and not receipt['ios_applications'])
item,=plan['expected'];check('exact current native TLS/helper/build/init source selector agreement',plan['desktop_security_fixture']==security.fixture_contract(ROOT,focus) and item['test_source_sha256']==security.selected_sources(focus) and item['required_testcases']==list(selection['required_testcases']) and item['required_original_xml']==1)
command=receipt['command'];selectors=[command[i+1] for i,arg in enumerate(command) if arg=='--tests']
check('actual command selects only failed original TLS one-class worker',selectors==list(selection['selectors']) and command.count(':calf-webview:desktopTest')==1 and command.count(security.INIT_SCRIPT)==1 and command.count(selection['isolation_property'])==1)
check('original native TLS byte-identical no trust/error/rendering predicate waiver',sha((ROOT/security.SOURCE_PATHS['tls-rendering']).read_bytes())=='00698c638a729549c890240b000e64cbd88be9f6ac32d4ca067b304b1443187c')
reports=list((artifact/'calf-webview/build/test-results/desktopTest').glob('TEST-*.xml'));check('only one original XML no accepted cookie policy or classifier-test replay',len(reports)==1)
xml=reports[0];raw=xml.read_bytes();check('safe original XML no DTD/entity',b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw);tree=ET.fromstring(raw);case,=tree.findall('testcase')
check('exact original TLS method and no XML skip',tree.attrib['tests']=='1' and tree.attrib['skipped']=='0' and case.attrib['classname']==security.SECURITY_CLASS and case.attrib['name']==security.SECURITY_METHOD+'[desktop]' and not case.findall('skipped'))
report,=receipt['modules'][0]['reports'];check('original producer XML hash and native execution interval',report['sha256']==sha(raw) and receipt['started_at_utc']<tree.attrib['timestamp']<receipt['finished_at_utc'])
problem=case.find('failure');problem=case.find('error') if problem is None else problem
native_pass=(problem is None and tree.attrib['failures']==tree.attrib['errors']=='0' and receipt['passed'] is True and receipt['execution']['exit_code']==0 and receipt['errors']==[])
check('actual nonzero original one-case execution counters',receipt['totals']['tests']==receipt['totals']['executed']==1 and receipt['totals']['skipped']==receipt['totals']['not_applicable']==receipt['totals']['unexpected_skipped']==0 and receipt['totals']['passed']==int(native_pass) and receipt['execution']['elapsed_seconds']>0)
workers=receipt.get('desktop_security_workers')
if native_pass:
 check('original strict public parser accepts isolated sequential one-case worker',workers['focus']==focus and workers['public_gradle_test_listener_boundaries_verified'] is True and workers['sequential_workers'] is True and workers['one_selected_case_per_worker'] is True and len(workers['selected_class_workers'])==1 and workers['selected_class_workers'][0]['classname']==security.SECURITY_CLASS and workers['os_worker_pid_observed'] is False and workers['os_worker_exit_or_sandbox_attested'] is False)
 check('both actual single native job and original workflow success',native_jobs[0]['conclusion']==run['conclusion']=='success')
warning=tree.find('system-err');warning=(warning.text or '') if warning is not None else ''
check('current source inputs still held through passive413 review',library.snapshot_inputs(ROOT)==before)
result={'schema_version':1,'run':RUN,'source_sha':REV,'original_conclusion':run['conclusion'],'checks':checks,'passive_check_count':len(checks),'native_executed':1,'native_passed':int(native_pass),'XML':1,'all_native_accepted':native_pass,'source_input_count':len(frozen),'execution':receipt['execution'],'java':context['java'],'gradle':'9.7.1','method':security.SECURITY_METHOD,'method_seconds':case.attrib['time'],'xml_sha256':sha(raw),'original_strict_worker':workers,'failure_type':problem.attrib.get('type') if problem is not None else None,'failure_message':problem.attrib.get('message') if problem is not None else None,'original_errors_retained':receipt['errors'],'unnamed_module_warning_retained':'Unsupported JavaFX configuration' in warning,'TLS_finished_abort_instance_or_branch_observed':False,'graph_acquisitions':0,'accepted_native_replays':0,'new_native_tests_during_review':0,'original_redownloads':0,'release_allowed':False,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'limits':['Public native TLS/error/zero-HTTP/painted-content/same-owner recovery/owned cleanup assertions qualify only if the original method passes.','No independent OS-worker PID/exit, whole-engine exploit/native-binary provenance, all protocols/physical GPU, package consumer/API-ABI, legal/security/readiness or publication certification.','Old failed Windows7 pair remains FAILED and six unchanged native passes stay accepted without replay.']}
save('REVIEW413.json',result);save('inputs-held.json',before)
print(json.dumps({'passive_checks':len(checks),'native_executed':1,'native_passed':int(native_pass),'XML':1,'Gradle':receipt['execution'],'original_conclusion':run['conclusion']},indent=2))
