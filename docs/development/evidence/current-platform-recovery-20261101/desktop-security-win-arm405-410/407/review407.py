"""Qualify cached originals and new host graphs; no tests, builds or network."""
import datetime, hashlib, json, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path('/root/projects/nativeCmpKit'); BASE=Path('/root/nativecmpkit-native-reviews-20261101'); OUT=Path(__file__).parent
ORIGINAL=Path((BASE/'SECURITY406-CURRENT-ORIGINAL').read_text().strip()); DISPATCH=Path((BASE/'SECURITY405-CURRENT-DISPATCH').read_text().strip())
REV='635202b7336429b821ef85e9261f42f5838a6a23'; RUN=41542403515
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests as library
import desktop_security_plan as security
import desktop_dependency_capture as capture
checks=[]
def check(name,value):
    if not value: raise AssertionError(name)
    checks.append(name)
def read(path): return json.loads(path.read_bytes())
def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(name,value):
    with (OUT/name).open('x') as f: json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
frozen=read(DISPATCH/'library-inputs.json'); before=library.snapshot_inputs(ROOT)
check('1219 live inputs held at immutable dispatch405 map',before==frozen and len(frozen)==1219)
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
raw=p.communicate(('\n'.join(REV+':'+relative for relative in frozen)+'\n').encode())[0]; check('own-Git source batch exits0',p.returncode==0); pos=0
for relative,digest in frozen.items():
    end=raw.index(b'\n',pos); header=raw[pos:end].split(); size=int(header[2]); start=end+1; value=raw[start:start+size];pos=start+size+1
    if header[1]!=b'blob' or sha(value)!=digest: raise AssertionError('immutable blob '+relative)
check('every1219 frozen pin equals own immutable Git blob',pos==len(raw))
run=read(ORIGINAL/'run.json'); check('completed original41542403515 attempt1 exact development head',tuple(run[k] for k in ('id','run_attempt','status','head_sha','head_branch','event'))==(RUN,1,'completed',REV,'development/preview-hardening','workflow_dispatch'))
acq=read(ORIGINAL/'ACQUISITION406.json'); claim=read(BASE/('security-%s-attempt1-original-acquisition.claim.json'%RUN))
check('exclusive solo406 acquisition once with original conclusion',acq['owner']==claim['owner']=='solo-lead' and acq['directory']==claim['directory']==str(ORIGINAL) and acq['no_duplicate_acquisition'] is True and acq['conclusion']==run['conclusion'])
for item in acq['files']:
    value=(ORIGINAL/item['file']).read_bytes();check('original hash '+item['file'],item['exit_code']==0 and len(value)==item['bytes'] and sha(value)==item['sha256'])
for item in acq['artifact_members']:
    value=(ORIGINAL/'evidence'/item['artifact_name']/item['name']).read_bytes()
    if len(value)!=item['bytes'] or sha(value)!=item['sha256']:raise AssertionError('cached original artifact member '+item['name'])
check('all original extracted members rehash acquisition406',True)
artifacts=read(ORIGINAL/'artifacts.json');slots=('desktop-windows-x64','desktop-linux-arm64')
check('exactly two original host artifacts, no accepted macOS or Linuxx64 replay',artifacts['total_count']==2 and {r['name'] for r in artifacts['artifacts']}=={'library-evidence-'+s for s in slots})
prior=ROOT/'docs/development/evidence/desktop-resolved-dependencies-20261030'; accepted=set()
for directory,name in (('runtime001','osv-runtime-query.json'),('compile-test002','osv-supplement-query.json')):
    data=read(prior/directory/name);accepted.update((q['package']['name'],q['version']) for q in data['queries'])
check('142 prior accepted Linux Maven coordinates retained',len(accepted)==142)
mac=ROOT/'docs/development/evidence/current-platform-recovery-20261101/desktop-security-originals385-395/389'
data=read(mac/'osv-macos-new-query.json'); accepted.update((q['package']['name'],q['version']) for q in data['queries'])
check('146 union Linux142 plus macOS4 accepted exact coordinates',len(accepted)==146)
additional={relative:sha(subprocess.check_output(['git','show',REV+':'+relative],cwd=ROOT)) for relative in (capture.WORKFLOW,*(r['source'] for r in capture.COLLECTORS))}
hosts=[]; new=set(); all_native=True
for slot,system,arch,classifier,count in (('desktop-windows-x64','Windows','x64','win',3),('desktop-linux-arm64','Linux','arm64','linux-aarch64',4)):
    artifact=ORIGINAL/'evidence'/('library-evidence-'+slot);native=artifact/'build/ci-verification'/slot
    receipt=read(native/'receipt.json');context=read(native/'runtime.json'); plan=read(native/'plan.json');selection=security.selection(system,arch)
    check(slot+' actual source/runtime clean host architecture Java17',receipt['source_revision']==receipt['source_revision_after']==context['source_revision']==REV and receipt['source_tree_dirty'] is False and context['source_tree_dirty'] is False and (context['host']['system'],context['host']['architecture'])==(system,arch) and context['java']['major']==17)
    check(slot+' actual matching Gradle9.7.1 launcher daemon',receipt['gradle_daemon']['gradle_version']=='9.7.1' and receipt['gradle_daemon']['java_version']==context['java']['version'] and receipt['gradle_daemon']['launcher_home_matches_daemon'] is True)
    check(slot+' actual1219 before after maps equal dispatch Git runtime hash',read(native/'inputs-before.json')==read(native/'inputs-after.json')==frozen and receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==library.input_digest(frozen) and receipt['changed_inputs']==[] and receipt['runtime_receipt_sha256']==sha((native/'runtime.json').read_bytes()))
    check(slot+' exact current native source/build/init selection',plan['desktop_security_fixture']==security.fixture_contract(ROOT,selection['focus']) and plan['expected'][0]['test_source_sha256']==security.selected_sources(selection['focus']) and plan['expected'][0]['required_testcases']==list(selection['required_testcases']) and plan['expected'][0]['required_original_xml']==count)
    check(slot+' exact fresh one task no full suite or samples',receipt['task_execution_markers']=={':calf-webview:desktopTest':1} and receipt['complete_suite_requested'] is False and receipt['explicit_module_subset']==['calf-webview'] and receipt['explicit_test_focus']==selection['focus'] and not receipt['ios_applications'])
    command=receipt['command'];selectors=[command[i+1] for i,v in enumerate(command) if v=='--tests']
    check(slot+' executed only required missing selectors and finite init',selectors==list(selection['selectors']) and command.count(':calf-webview:desktopTest')==1 and command.count(security.INIT_SCRIPT)==1 and command.count(selection['isolation_property'])==1)
    outcomes=[]; xmls=list((artifact/'calf-webview/build/test-results/desktopTest').glob('TEST-*.xml'))
    check(slot+' exactly required original XML count',len(xmls)==count)
    for key in selection['selected']:
        classname,method=security.SPECS[key];file=artifact/'calf-webview/build/test-results/desktopTest'/('TEST-'+classname+'.xml');value=file.read_bytes()
        check(slot+' XML no DTD/entity '+key,b'<!DOCTYPE' not in value and b'<!ENTITY' not in value)
        tree=ET.fromstring(value);case,=tree.findall('testcase');status='failed' if case.find('failure') is not None or case.find('error') is not None else 'passed'
        check(slot+' original native method identity and no skips '+key,tree.attrib['tests']=='1' and tree.attrib['skipped']=='0' and case.attrib['classname']==classname and case.attrib['name']==method+'[desktop]' and not case.findall('skipped'))
        report=next(r for r in receipt['modules'][0]['reports'] if r['path'].endswith(file.name))
        check(slot+' original XML hash within actual execution interval '+key,report['sha256']==sha(value) and receipt['started_at_utc']<tree.attrib['timestamp']<receipt['finished_at_utc'])
        warning=tree.find('system-err');warning=(warning.text or '') if warning is not None else '';failure=case.find('failure');error=case.find('error');problem=failure if failure is not None else error
        outcomes.append({'key':key,'classname':classname,'method':method,'status':status,'method_seconds':case.attrib['time'],'xml_sha256':sha(value),'failure_type':problem.attrib.get('type') if problem is not None else None,'failure_message':problem.attrib.get('message') if problem is not None else None,'JavaFX_unnamed_module_warning_retained':'Unsupported JavaFX configuration' in warning,'Skiko_GL_fallback_warning_retained':'OpenGL' in warning or 'GL context' in warning})
    native_pass=all(r['status']=='passed' for r in outcomes) and receipt['passed'] is True and receipt['execution']['exit_code']==0 and receipt['errors']==[]
    all_native=all_native and native_pass
    check(slot+' actual nonzero native population, no skipped/N/A',receipt['execution']['elapsed_seconds']>0 and receipt['totals']['tests']==receipt['totals']['executed']==count and receipt['totals']['skipped']==receipt['totals']['not_applicable']==receipt['totals']['unexpected_skipped']==0 and receipt['totals']['passed']==sum(r['status']=='passed' for r in outcomes))
    if native_pass:
        workers=receipt['desktop_security_workers'];required={security.SPECS[key][0] for key in selection['selected']}
        check(slot+' strict public isolated sequential single-case worker parser',workers['public_gradle_test_listener_boundaries_verified'] is True and workers['sequential_workers'] is True and workers['one_selected_case_per_worker'] is True and len(workers['selected_class_workers'])==count and {r['classname'] for r in workers['selected_class_workers']}==required and workers['os_worker_pid_observed'] is False and workers['os_worker_exit_or_sandbox_attested'] is False)
    cap=read(artifact/'build/ci-runtime/desktop-dependencies-receipt.json');map_path=artifact/'build/ci-runtime/desktop-dependencies-inputs-before.json';map_before=read(map_path)
    check(slot+' actual complete1222 graph inputs before after frozen plus3 Git',map_before=={**frozen,**additional}==read(artifact/'build/ci-runtime/desktop-dependencies-inputs-after.json') and len(map_before)==1222 and cap['inputs_before']['sha256']==cap['inputs_after']['sha256']==sha(map_path.read_bytes()))
    check(slot+' actual graph custody runtime init cleanup no native/query/publication',cap['capture_complete'] is True and cap['errors']==[] and cap['inputs_and_runtime_unchanged'] is True and cap['owned_private_inits_removed'] is True and cap['native_methods_requested']==cap['advisory_queries_requested']==0 and cap['packages_published'] is False and cap['javafx_classifier_for_independent_review']==classifier and cap['runtime']['sha256']==sha((artifact/'build/ci-runtime/actual.json').read_bytes()))
    coordinates=set();graphs=[]
    for collector,phase in zip(capture.COLLECTORS,cap['phases']):
        value=(artifact/('build/ci-runtime/desktop-dependencies-'+collector['phase']+'-graph.json')).read_bytes();stats=capture.graph(value,collector)
        check(slot+' full actual graph hashes markers collector and Gradle0 '+collector['phase'],stats==phase['observed_graph'] and phase['copied_graph']['sha256']==phase['original_graph']['sha256']==sha(value) and phase['collector_sha256']==collector['sha256'] and phase['capture_complete'] is True and phase['execution']['exit_code']==0 and phase['errors']==[] and phase['graph_markers_match'] is True)
        graph=json.loads(value)
        for row in graph['configurations']:
            coordinates.update((m['group']+':'+m['name'],m['version']) for m in row['modules'])
            if row['project']==':calf-webview' and row['configuration']=='desktopTestRuntimeClasspath':
                classified=[a for a in row['artifacts'] if a['group']=='org.openjfx' and a['filename'].endswith('-'+classifier+'.jar')]
                check(slot+' six aligned actual native-classified JavaFX21.0.13 modules',len(classified)==6 and {a['name'] for a in classified}=={'javafx-base','javafx-graphics','javafx-controls','javafx-media','javafx-web','javafx-swing'} and all(a['version']=='21.0.13' for a in classified))
        graphs.append({'phase':collector['phase'],'sha256':sha(value),**stats,'execution':phase['execution']})
    delta=coordinates-accepted;new.update(delta)
    check(slot+' actual142 exact Maven graph coordinates and only2 host deltas',len(coordinates)==142 and len(delta)==2)
    hosts.append({'slot':slot,'host':context['host'],'java':context['java'],'gradle':receipt['execution'],'native_accepted':native_pass,'outcomes':outcomes,'graphs':graphs,'reused_advisory_coordinates':len(coordinates & accepted),'new_coordinates':[{'name':n,'version':v} for n,v in sorted(delta)],'receipt_errors_retained':receipt['errors']})
expected_new={('org.jetbrains.compose.desktop:desktop-jvm-windows-x64','1.12.0'),('org.jetbrains.compose.desktop:desktop-jvm-linux-arm64','1.12.0'),('org.jetbrains.skiko:skiko-awt-runtime-windows-x64','0.150.1'),('org.jetbrains.skiko:skiko-awt-runtime-linux-arm64','0.150.1')}
check('exact4 genuinely new host Maven coordinates only',new==expected_new)
check('library inputs still held after passive review407',library.snapshot_inputs(ROOT)==before)
save('NEW-COORDINATES407.json',[{'name':n,'version':v} for n,v in sorted(new)])
save('REVIEW407.json',{'schema_version':1,'run':RUN,'source_sha':REV,'original_conclusion':run['conclusion'],'checks':checks,'passive_check_count':len(checks),'hosts':hosts,'new_native_executed':7,'new_native_passed':sum(r['status']=='passed' for h in hosts for r in h['outcomes']),'all_new_native_accepted':all_native,'graphs':4,'graph_input_count':1222,'native_input_count':1219,'new_advisory_queries_during_review':0,'new_coordinate_count':4,'original_redownloads':0,'tests_builds_or_native_replays_during_review':0,'remaining':'Only4 new advisory observations and all literal #144 criterion applicability review, if all7 native/cleanup accepted; #64 adoption is separate.','release_allowed':False,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'passive_checks':len(checks),'native_executed':7,'native_passed':sum(r['status']=='passed' for h in hosts for r in h['outcomes']),'all_native_accepted':all_native,'new_coordinates':4},indent=2))
