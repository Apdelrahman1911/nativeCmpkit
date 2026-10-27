"""Original NAV-006 criterion-by-criterion immutable source/actual XML acceptance."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'docs/development/evidence/navhost-original-acceptance-20261027';REV='6ada26d3c47096ad0750a111c7e807b03230d844'
assert OUT.is_dir() and not any(OUT.iterdir()), 'No evidence file may be overwritten'
def blob(path,revision=REV):return subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT)
def sha(raw):return hashlib.sha256(raw).hexdigest()
review=json.loads((ROOT/'docs/development/evidence/github-actions/40576835737/lead-independent-review.json').read_bytes())
assert review['evidence_integrity_passed'] and review['source_revision']==REV and review['totals']['passed']==review['totals']['executed']==55
assert review['actual_xml_reports']==7 and review['setup_test_SDK_and_global_fingerprints_match'] and review['only_setup_test_context_difference_is_observed_time']
finding_file=None
for p in (ROOT/'docs/audit/findings').glob('*.json'):
 for row in json.loads(p.read_bytes()):
  if row['id']=='NAV-006':finding=row;finding_file=p.relative_to(ROOT).as_posix()
assert finding_file and (ROOT/finding_file).read_bytes()==blob(finding_file,'94d2492e99d5cbc060409d94d9f88febd06222d5')
required=finding['required_tests'];assert len(required)==3
methods=[['replacement controller is initialized and receives updated graph callbacks'],['updated closures do not lose entry state or reset a nonempty stack'],['changing start route initializes an explicitly emptied stack at the same host','updated closures do not lose entry state or reset a nonempty stack']]
actual={c['name']:c for c in review['actual_cases'] if c['classname']=='com.mohamedrejeb.calf.navigation.AdaptiveNavHostStateTest'};assert len(actual)==12
acceptance=[]
for requirement,names in zip(required,methods):
 for name in names:assert actual[name+'[desktop]']['status']=='passed'
 acceptance.append({'original_required_test':requirement,'immutable_passing_class':'com.mohamedrejeb.calf.navigation.AdaptiveNavHostStateTest','immutable_passing_methods':[name+'[desktop]' for name in names],'satisfied_in_original_scope':True})
paths=['calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt','calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt','calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/AdaptiveNavHostStateTest.kt','docs/decisions/0004-adaptive-navigation-entries.md']
current={p:sha(blob(p)) for p in paths};assert all((ROOT/p).read_bytes()==blob(p) for p in paths)
host=blob(paths[0]).decode();assert 'val graph = NavGraphBuilder().apply(builder)' in host and 'LaunchedEffect(navController, startDestination)' in host and 'if (navController.currentBackStackEntry == null) navController.navigate(startDestination)' in host
# Display exact inspected current line locations, never reuse baseline numbers.
locations=[{'path':paths[0],'line':n,'source':s.strip()} for n,s in enumerate(host.splitlines(),1) if any(term in s for term in ('val graph =','LaunchedEffect(','currentBackStackEntry == null','attachGraph(','SideEffect'))]
result={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'finding_id':'NAV-006','issue_number':94,'accepted_original_scope':True,'baseline':'af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6','original_finding_file':finding_file,'original_finding_file_sha256':sha((ROOT/finding_file).read_bytes()),'original_dependencies_preserved':finding['dependencies'],'criteria':acceptance,'immutable_run_id':40576835737,'source_revision':REV,'suite_totals':review['totals'],'host_methods_passed':12,'selected_git_inputs':727,'current_original_scope_sources_match_commit':True,'current_source_hashes':current,'inspected_host_locations':locations,'old_effect_control_and_green':'docs/development/evidence/navigation-empty-stack-20261027/lead-review.json','setup_test_SDK_and_fingerprints_match':True,'issues_closed_by_review':0,'release_readiness_certified':False,'limits':['Accepts three specified shared-host criteria on real Compose desktop, not Android/iOS UI integration or native navigation parity.','NAV-001/002 broader entry/ownership/restoration gates and NAV-004 erased getter remain separate; no dependency disposition promoted.','No whole-library API/ABI, minimum-platform, device/native-parent, dependency/legal/consumer/security or release clearance.'],'scope':'Every original NAV-006 required test is mapped to actual passing immutable host methods. Replacement controller uses current routing callbacks; outer state/closures refresh without losing state; explicitly emptied same-owner stack initializes once on start change and subsequent nonempty start change preserves entry. Original finding/body/labels/history remain; any closure follows pushed evidence and exact readback.'}
(OUT/'lead-original-acceptance-review.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');(OUT/'review.py').write_bytes(Path(__file__).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'NAV-006_original_criteria_accepted':len(acceptance),'actual_host_methods':12,'issue_closed':False,'archive':str(OUT)}))
