"""Read-only source-held KLIB and actual one-method desktop evidence review."""
from pathlib import Path
import datetime as dt,hashlib,json,re,shutil,sys,xml.etree.ElementTree as ET
ROOT=Path('/root/projects/nativeCmpKit');HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests as lt
KLIB=Path('/dev/shm/nativecmpkit-tab-selection-klib-20261027-001')
DESKTOP=Path('/dev/shm/nativecmpkit-remember-properties-desktop-20261027-002')
RED=Path('/dev/shm/nativecmpkit-remember-properties-desktop-20261027-001')
CHAR=Path('/dev/shm/nativecmpkit-tab-selection-20261027')
DEST=ROOT/'docs/development/evidence/native-tab-properties-20261027'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def get(p):return json.loads(p.read_bytes())
assert not DEST.exists()
current=lt.snapshot_inputs(ROOT);assert len(current)==725
k=get(KLIB/'ui/receipt.json');d=get(DESKTOP/'receipt.json');r=get(RED/'orchestrator-failure.json')
assert k['execution']['exit_code']==0 and not k['execution'].get('stop_reason') and k['library_or_device_tests_executed']==0
assert k['selected_input_count']==d['selected_input_count']==725
assert k['selected_inputs_sha256']==d['inputs_sha256']==lt.input_digest(current)
assert k['driver_sha256']==sha(KLIB/'driver.py') and k['model_init_sha256']==sha(KLIB/'model.init.gradle')
assert k['compile_log_sha256']==sha(KLIB/'ui/compile.log') and k['source_inputs_held'] and k['copied_inputs_held']
assert k['host_disk_reserve_maintained_at_completion']
for name in ('library-inputs-before.json','library-inputs-after.json','copied-inputs-before.json','copied-inputs-after.json'):
 assert get(KLIB/'ui'/name)==current
log=(KLIB/'ui/compile.log').read_text()
assert 'BUILD SUCCESSFUL' in log and 'BUILD FAILED' not in log and '> Task :calf-ui:compileTestKotlinIosSimulatorArm64\n' in log
assert log.count('NATIVECMPKIT_CURRENT_ROOT name=NativeCmpKit')==1
assert log.count('NATIVECMPKIT_UIKIT_MODEL extra=applicationDebugTest normal=debugTest compilationShared=true')==1
assert d['execution']['exit_code']==0 and not d['execution'].get('stop_reason') and d['passed'] and d['inputs_held']
assert get(DESKTOP/'execution-before-report-review.json')['execution']==d['execution']
assert d['log_sha256']==sha(DESKTOP/'test.log') and d['driver_sha256']==sha(DESKTOP/'driver.py')
assert lt.execution_markers(DESKTOP/'test.log')=={':calf-ui:desktopTest':1}
for name in ('inputs-before.json','inputs-after.json','copied-inputs-before.json','copied-inputs-after.json'):
 assert get(DESKTOP/name)==current
assert r['driver_exit_code']==1 and r['exact_Gradle_child_exit_unretained'] and not r['overall_passed']
reports=d['module']['reports'];assert len(reports)==1
row=reports[0];p=DESKTOP/'reports'/row['path'];assert sha(p)==row['sha256']
cases=lt.junit_cases(p.read_bytes());assert cases==d['module']['testcases']
assert lt.case_counts(cases)=={'tests':1,'passed':1,'executed':1,'failures':0,'errors':0,'skipped':0,'not_applicable':0,'unexpected_skipped':0}
assert cases[0]['classname']=='com.mohamedrejeb.calf.ui.dialog.RememberAlertPropertiesTest' and cases[0]['name']=='textFieldChangesAreNotHiddenByRememberKeys'
suite=ET.fromstring(p.read_bytes(),parser=ET.XMLParser(target=lt.NoDtdBuilder()))
xml_time=dt.datetime.fromisoformat(suite.attrib['timestamp'])
# Gradle desktop XML has no offset; do not invent one for wall-clock comparison.
timestamp={'literal':suite.attrib['timestamp'],'timezone_explicit':xml_time.utcoffset() is not None,'fresh_file_mtime_checked_by_inspected_collector':True}
source=(ROOT/'calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/dialog/RememberAlertPropertiesTest.kt').read_text()
for text in ('assertSame(initial, properties)','assertNotSame(initial, properties)','assertEquals(listOf(second), properties.textFields)','assertSame(replacement, properties)'):
 assert text in source
helper='calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosProperties.kt'
assert 'remember(title, text, style, animated, severity, actions, textFields)' in (ROOT/helper).read_text()
character=get(CHAR/'source-characterization.json');assert character['status']=='confirmed-source' and character['native_tests_executed']==0
before=CHAR/'production-before.kt';assert sha(before)==character['source_sha256']
after=ROOT/character['path'];after_text=after.read_text()
assert 'onItemSelected(didSelectItem.tag.toInt())' in before.read_text() and 'onItemSelected(didSelectItem.tag.toInt())' not in after_text
assert 'if (tabBar.delegate?.objcPtr() != objcPtr()) return' in after_text and 'item.objcPtr() == didSelectItem.objcPtr()' in after_text
assert 'if (index < 0) return' in after_text and 'onItemSelected(index)' in after_text
assert len(lt.IOS_APPLICATION_CASES)==16 and len(lt.IOS_APPLICATION_SOURCES)==6
synthetic=get(CHAR/'tooling001/receipt.json');assert synthetic['exit_code']==0 and synthetic['method_counts']==['64'] and synthetic['result_OK']
review={'reviewed_utc':lt.utc_now(),'passed_evidence_integrity':True,'source_revision_before_commit':lt.git_revision(ROOT),'dirty_worktree':True,'selected_inputs':725,'inputs_sha256':lt.input_digest(current),'source_and_copied_inputs_held':True,'actual_KLIB_model_compile':k['execution'],'native_methods_executed_by_KLIB':0,'actual_scoped_desktop_test':d['execution'],'desktop_totals':lt.case_counts(cases),'testcases':cases,'literal_XML_timestamp':timestamp,'original_failed_temporary_orchestrator_preserved':True,'original_child_exit_not_retrospectively_invented':True,'owning_report_API_and_immediate_exit_receipt_corrected':True,'new_native_selection_source_defect':character,'native_selection_fix_typechecked_not_executed':True,'new_native_required_methods':16,'all_original13_required_methods_retained':True,'synthetic_helper_methods':64,'source_change_limited_to_current_selection_and_regression_contracts':True,'packages_published':False,'release_readiness_certified':False,'limitations':['One real shared-helper Compose/remember desktop method, not the full128-method UI suite.','First execution produced success output/fresh XML but its temporary orchestrator failed before retaining exact child exit; final23.01-second rerun retains exact0 and fresh reports. Both reuse the same method, not two distinct regressions.','New native membership/active-delegate defenses and iOS remember regressions compile in the full test KLIB but execute zero Apple tests. Immutable16-mandatory-method UIKit run remains necessary.','No iPad/native touch, minimum-OS, VoiceOver, API/ABI, leak/sanitizer, consumers, dependency or release certification.']}
DEST.mkdir()
for folder,src in [('klib',KLIB),('desktop-red001',RED),('desktop002',DESKTOP),('source-tooling',CHAR)]:
 shutil.copytree(src,DEST/folder)
 for file in src.rglob('*'):
  if file.is_file():assert sha(file)==sha(DEST/folder/file.relative_to(src))
shutil.copyfile(Path(__file__),DEST/'lead-review.py')
(DEST/'lead-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(file)}  {file.relative_to(DEST).as_posix()}\n' for file in sorted(DEST.rglob('*')) if file.is_file()))
print(json.dumps({key:review[key] for key in ['passed_evidence_integrity','selected_inputs','actual_KLIB_model_compile','desktop_totals','new_native_required_methods','native_selection_fix_typechecked_not_executed']},indent=2))
