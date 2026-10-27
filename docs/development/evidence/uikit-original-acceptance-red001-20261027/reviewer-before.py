"""Map every original UI-015/UI-022 criterion to immutable native runtime evidence."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,shutil
ROOT=Path('/root/projects/nativeCmpKit');SOURCE=Path(__file__).parent
OUT=ROOT/'docs/development/evidence/uikit-original-acceptance-20261027'
RUN_REVIEW='docs/development/evidence/github-actions/40540209480/lead-independent-review.json'
run=json.loads((ROOT/RUN_REVIEW).read_bytes());rev='ea79ab8cf30132b4b37985f175d00287382ddca8'
assert run['evidence_integrity_passed'] and run['source_revision']==rev and run['run_id']==40540209480
assert run['totals']['tests']==run['totals']['passed']==123 and run['actual_xml_reports']==25 and run['mandatory_application_methods_passed']==16
assert run['all_current_owning_UI_build_and_platform_source_bytes_match_tested_Git'] and run['application_transport_passed']
assert run['application_completion']=={'runner_exit':0,'worker_terminated':True}
FINDINGS={'UI-015':(160,'dialog.RememberNativeAlertPropertiesTest',[['stableInputsRetainIdentityButTextFieldReplacementReachesTheCaller'],['stableInputsRetainIdentityButTextFieldReplacementReachesTheCaller']]),
 'UI-022':(128,'navigation.NativeBarOwnershipTest',[['emptyTabsClearSelectionAndRepopulationClampsIndex'],['emptyTabsClearSelectionAndRepopulationClampsIndex','selectionUsesCurrentNativeMembershipInsteadOfStaleOrMutableTags']])}
findings=json.loads((ROOT/'docs/audit/findings/UI.json').read_bytes());ledger=json.loads((ROOT/'docs/development/resolutions/UI-native.json').read_bytes());records=[];hashes={}
for fid,(number,cls,methods) in FINDINGS.items():
 original=next(r for r in findings if r['id']==fid);disposition=next(r for r in ledger if r['id']==fid)
 issue=json.loads((SOURCE/f'issue-{number}-before.json').read_bytes())
 assert issue['state']=='open' and issue['number']==number and f'<!-- nativecmpkit-item:audit:{fid} -->' in issue['body']
 assert len(original['required_tests'])==len(methods)==2
 for requirement in original['required_tests']:assert '- '+requirement in issue['body']
 rows=[]
 for requirement,names in zip(original['required_tests'],methods):
  evidence=[]
  for name in names:
   found=[c for c in run['testcases'] if c['classname']=='iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.'+cls and c['name']==name+'[iosSimulatorArm64]']
   assert len(found)==1 and found[0]['status']=='passed'
   evidence.append({'method':name,'classname':found[0]['classname'],'XML_method_name':found[0]['name'],'status':'passed','job_url':run['job_url']})
  rows.append({'requirement':requirement,'status':'passed-original-scoped-native-runtime','executed_methods':evidence})
 for path in disposition['affected_paths']:
  p=ROOT/path;tested=subprocess.check_output(['git','show',rev+':'+path],cwd=ROOT);assert p.read_bytes()==tested
  hashes[path]=hashlib.sha256(tested).hexdigest()
 records.append({'id':fid,'issue_number':number,'issue_url':issue['html_url'],'original_required_tests':original['required_tests'],'original_dependencies':original['dependencies'],'issue_body_sha256_before':hashlib.sha256(issue['body'].encode()).hexdigest(),'issue_title_before':issue['title'],'issue_labels_before':sorted(l['name'] for l in issue['labels']),'previous_status':disposition['status'],'previous_remaining_preserved_verbatim':disposition['remaining'],'requirements_review':rows,'accepted_for_original_scoped_closure':True,'scope_boundaries':['UI-015 is the shared remember-property input/identity contract, not closure of its independent UI-012 native-alert dependency.','UI-022 calls the actual production UITabBar delegate with real native items; no physical gesture/touch injection, accessibility/orientation/trait or all-version claim. Original criteria require native items/callbacks, bounds and reordering; those are actually asserted.','Programmatic setting/clearing does not fabricate callbacks; stale/foreign/replaced-delegate/mutated-tag inputs reject or map according to current native membership.','iPhone26.5 native simulator, not minimum-iOS/iPad/physical device, sanitizer/leak/general-performance/consumer/API-ABI/legal/dependency or release clearance.'],'compatibility':disposition['compatibility']})
OUT.mkdir(exist_ok=False)
for number,_,_ in FINDINGS.values():
 for ext in ('json','stderr'):
  name=f'issue-{number}-before.{ext}';shutil.copyfile(SOURCE/name,OUT/name)
shutil.copyfile(SOURCE/'original-context.json',OUT/'original-context.json');shutil.copyfile(Path(__file__),OUT/'review.py')
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'evidence_integrity_passed':True,'source_revision':rev,'immutable_run_id':40540209480,'immutable_run_review':RUN_REVIEW,'findings_accepted_for_scoped_closure':records,'owning_current_source_hashes_identical_to_runtime':hashes,'actual_native_methods':123,'actual_XML_reports':25,'mandatory_application_methods':16,'original_baseline_modified':False,'issues_mutated':False,'publication_performed':False,'release_readiness_certified':False,'scope':'All four original UI-015/UI-022 requirements map to current immutable named native methods and exact source. Previous remaining observations preserved verbatim, not silently waived; unrelated independent native/physical/consumer/ABI/legal/dependency/security gates remain. Closure requires pushed evidence and state/comment-only exact readback.'}
(OUT/'lead-original-acceptance-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
(OUT/'README.md').write_text('# UI-015 / UI-022 original scoped acceptance\n\nAll four baseline requirements are mapped to genuine current native-simulator methods at immutable ea79ab8cf30132b4b37985f175d00287382ddca8 /run40540209480. Prior remaining prose and original issue bodies are preserved. Direct native delegate callbacks are not physical touches; remember-property acceptance is independent of UI-012 alert lifecycle. No broad native/release gate passes. Close only after pushing evidence and exact additive comment/state readback.\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(OUT/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(OUT).as_posix()+'\n' for p in sorted(OUT.rglob('*')) if p.is_file()))
print(json.dumps({'accepted_original_scopes':list(FINDINGS),'original_requirements':4,'issues_closed':0,'archive':str(OUT)},indent=2))
