"""Reuse inspected unchanged Android-host LocationResult/Compose regressions; close only PERM-018."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,sys,xml.etree.ElementTree as ET,zipfile
root=Path('/root/projects/nativeCmpKit');out=Path(__file__).parent
repo='Apdelrahman1911/nativeCmpkit';run_id=40414284598;issue_id=24
marker='<!-- nativecmpkit-resolution:PERM-018:40414284598 -->'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=root)
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def instant(v):return dt.datetime.fromisoformat(v.replace('Z','+00:00'))
def save(n,d):(out/n).write_text(json.dumps(d,indent=2)+'\n')
def api(name,endpoint,method='GET',body=None):
 cmd=['gh','api','repos/'+repo+'/'+endpoint,'--method',method]
 if body is not None:cmd+=['--input','-']
 r=subprocess.run(cmd,input=json.dumps(body).encode() if body is not None else None,capture_output=True,timeout=90)
 (out/(name+'.json')).write_bytes(r.stdout)
 if r.stderr:(out/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,'API failure: inspect preserved response before any retry/mutation'
 return json.loads(r.stdout)
current=git('rev-parse','HEAD').decode().strip();base=root/'docs/development/evidence/github-actions/40414284598'
review=json.loads((base/'lead-independent-review.json').read_bytes())
assert review['evidence_integrity_passed'] and review['run_id']==run_id and review['run_conclusion']=='success'
revision=review['source_revision'];slot=next(s for s in review['runtime_slots'] if s['slot']=='android-host')
assert slot['job_conclusion']=='success' and slot['execution']['exit_code']==0
paths=['calf-geo','calf-core/src/commonMain','calf-core/src/androidMain','calf-core/build.gradle.kts','convention-plugins','gradle','gradle.properties','gradlew','gradlew.bat','build.gradle.kts','settings.gradle.kts']
changed=git('diff','--name-only',revision,current,'--',*paths).decode().splitlines()
assert set(changed)=={'settings.gradle.kts','convention-plugins/src/main/kotlin/module.publication.gradle.kts'}
for path in changed:
 old=git('show',revision+':'+path);new=(root/path).read_bytes()
 expected=old.replace(b'rootProject.name = "nativeCmpkit"',b'rootProject.name = "NativeCmpKit"') if path=='settings.gradle.kts' else old.replace(b'name.set("nativeCmpkit - "',b'name.set("NativeCmpKit - "')
 assert new==expected,'Unexpected build edit: cannot reuse host evidence'
files=git('ls-tree','-r','--name-only',current,'--',*paths).decode().splitlines()
hashes={p:sha((root/p).read_bytes()) for p in files};assert all(sha(git('show',current+':'+p))==h for p,h in hashes.items())
p=base/'raw'/(str(slot['artifact_id'])+'.zip');assert 'sha256:'+sha(p.read_bytes())==slot['artifact_digest']
sys.path.insert(0,str(root/'scripts/ci'));import library_tests as lt
with zipfile.ZipFile(p) as z:
 b='build/ci-verification/android-host/'
 receipt=json.loads(z.read(b+'receipt.json'));before=json.loads(z.read(b+'inputs-before.json'));after=json.loads(z.read(b+'inputs-after.json'))
 assert before==after and not receipt['changed_inputs'] and not receipt['source_tree_dirty']
 assert receipt['source_revision']==receipt['source_revision_after']==revision and receipt['execution']['exit_code']==0 and receipt['passed']
 # Historical schema has no copied marker counters. Inspect its own fresh-test
 # initializer and fresh report outcomes, without inventing a later-schema field.
 init_path='scripts/ci/fresh-tests.init.gradle.kts';init=git('show',revision+':'+init_path)
 assert before[init_path]==sha(init) and '--init-script' in receipt['command'] and init_path in receipt['command']
 assert b'outputs.upToDateWhen { false }' in init and b'outputs.doNotCacheIf' in init and b'ignoreFailures = false' in init
 assert ':calf-geo:testAndroidHostTest' in receipt['command']
 held={p:d for p,d in hashes.items() if p in before and p not in changed};assert len(held)>=50
 assert all(before[p]==d for p,d in held.items())
 module=next(m for m in receipt['modules'] if m['module']=='calf-geo');assert module['passed']==88 and module['executed']==88
 reports=[];cases=[]
 for record in module['reports']:
  n=record['path'];assert n.startswith('calf-geo/build/test-results/testAndroidHostTest/') and n.endswith('.xml')
  raw=z.read(n);assert sha(raw)==record['sha256']
  found=lt.junit_cases(raw);assert all(c['status']=='passed' for c in found)
  tree=ET.fromstring(raw,parser=ET.XMLParser(target=lt.NoDtdBuilder()))
  assert instant(receipt['started_at_utc'])<=instant(tree.attrib['timestamp'])<=instant(receipt['finished_at_utc'])
  reports.append({'path':n,'sha256':sha(raw),'timestamp':tree.attrib['timestamp']});cases+=found
 assert len(reports)==5 and len(cases)==len({(c['classname'],c['name']) for c in cases})==88
 assert sorted(cases,key=lambda c:(c['classname'],c['name']))==sorted(module['testcases'],key=lambda c:(c['classname'],c['name']))
finding=next(f for f in json.loads((root/'docs/audit/findings/PERM.json').read_bytes()) if f['id']=='PERM-018');assert len(finding['required_tests'])==2
rows=[ [('AndroidLocationTrackerTest','realLocationResultFlowsThroughNativeAdapterIntoBothPublicStates'),('AndroidLocationTrackerTest','nativeFixesRecomposeBothPublicViewsWithoutDuplicateOrDisposedDelivery'),('LocationTrackingControllerTest','nativeFixUpdatesAllViewsFromOneSnapshot')], [('AndroidLocationSubscriptionTest','nullLastLocationDoesNotInventAZeroFix'),('AndroidLocationTrackerTest','commonFactoryCreatesAnExplicitlyUnboundAndroidTracker'),('AndroidLocationTrackerTest','onStopCancelsDeliveryAndResumeNeedsExplicitRestart'),('AndroidLocationTrackerTest','nativeFixesRecomposeBothPublicViewsWithoutDuplicateOrDisposedDelivery'),('LocationTrackingControllerTest','initialAbsenceIsNotARealZeroCoordinate'),('LocationTrackingControllerTest','noFixAfterSuccessfulRegistrationRemainsExplicit'),('LocationTrackingControllerTest','closeIsTerminalAndNoLateNativeEventMutatesClosedState'),('LocationTrackingControllerTest','duplicateAndOlderFixesDoNotReplaceNewerState')] ]
criteria=[]
for req,row in zip(finding['required_tests'],rows,strict=True):
 matched=[]
 for cls,method in row:
  found=[c for c in cases if c['classname']=='com.mohamedrejeb.calf.geo.'+cls and c['name']==method];assert len(found)==1;matched+=found
 criteria.append({'original_requirement':req,'status':'accepted','actual_cases':matched})
controller=(root/'calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LocationTrackingController.kt').read_text()
assert 'private val state = mutableStateOf(' in controller and 'val locationState: State<LatLng> = derivedStateOf { state.value.fix?.coordinates ?: UnknownCoordinates }' in controller
assert 'val extendedLocationState: State<ExtendedLocation> = derivedStateOf { state.value.fix.toLegacyLocation() }' in controller and 'Channel' not in controller
wrapper=(root/'calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt').read_text()
assert 'actual val locationState: State<LatLng> = controller.locationState' in wrapper and 'actual val extendedLocationState: State<ExtendedLocation> = controller.extendedLocationState' in wrapper
acceptance={'reviewed_utc':stamp(),'finding':'PERM-018','current_revision':current,'tested_revision':revision,'run_id':run_id,'artifact_id':slot['artifact_id'],'artifact_digest':slot['artifact_digest'],'all_two_original_criteria_accepted':True,'criteria':criteria,'actual_host_cases':88,'actual_XML_reports':reports,'command':receipt['command'],'execution':receipt['execution'],'current_affected_inputs':hashes,'historical_freshness_contract':'Old schema has no copied marker counter. Own-Git initializer disables up-to-date/test-cache reuse and propagates failures; original five XML timestamps/outcomes checked. No independent private Gradle-log marker recount claimed.','same_held_input_count':len(held),'same_input_exceptions':'Exactly two root/POM display strings; all geo production/test and dependency inputs unchanged.','source_review':'One coherent production mutable snapshot and derived compatibility views. Android session callback adapter commits valid fixes; no unconsumed private channels. Lifecycle/callback generation checks and explicit absence preserved.','reuse':'Existing immutable Android-host run re-reviewed; zero new executions.','limits':['Robolectric/API28 real Android LocationResult/Lifecycle/Compose runtime with injected GMS Tasks/transport; not installed Play Services, GPS hardware or physical/device rendering.','Recomposition uses real Composition/Recomposer and SideEffect-only applier, not rendered Compose UI.','NativeFix parameterized API23/26/34 repetitions are part of88 host executions, not88 unique methods.','Legacy missing values intentionally become documented NaN/null/time0 sentinels; unchanged descriptors are not ABI certification.','Geo remains unpublished; physical/native/minimum-platform/provider/security/API-ABI/release readiness under BUILD-006 and release-readiness remain independent.'],'publication_performed':False,'release_readiness_certified':False}
save('acceptance.json',acceptance);print('Reviewed88/88 Android-host cases,5 fresh original XML; both original PERM-018 criteria accepted.',flush=True)
issue=api('issue-before','issues/'+str(issue_id));assert issue['state']=='open' and '<!-- nativecmpkit-item:audit:PERM-018 -->' in issue['body'] and all(req in issue['body'] for req in finding['required_tests'])
comments=api('comments-before','issues/'+str(issue_id)+'/comments?per_page=100');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
body=f'''{marker}
## Verified resolution — PERM-018

Native Android LocationResult delivery now commits one coherent production `LocationTrackingSnapshot`; the retained simple/extended public State views derive from that snapshot. There are no unconsumed private channels. Absence is explicit through additive nullable fix/snapshot APIs, with documented NaN/null/time0 legacy sentinels rather than a fabricated real zero fix. Existing constructor/package/property/start/stop/bind signatures are retained; this is not ABI certification.

**Both original acceptance criteria passed:** single, consecutive and batched real Android LocationResult objects update both public views consistently; null/empty/older/duplicate fixes do not invent or duplicate data; initial no-fix, stopped/closed delivery and real Compose-runtime observation/recomposition/disposal are asserted.

[Immutable Android-host run{run_id}](https://github.com/{repo}/actions/runs/{run_id}) at `{revision}`: **88/88 geo host executions**, five fresh XML, Gradle exit0. Named cases, original XML hashes/timestamps, test command/fresh-test initializer and source were reviewed again. Current affected geo production/tests/dependencies are unchanged except two exact root/POM display strings. Existing same-input results are reused explicitly; zero new executions or repeated suites.

Closing directly after required-test/source/result review. These use real Android classes, Lifecycle, Compose Composition/Recomposer and GMS Tasks under Robolectric (tracker API28; flag tests include23/26/34), with **injected provider transport**, not installed Play Services/GPS or a physical device. The Compose applier is SideEffect-only, not rendered UI. Physical/native/minimum-platform, real provider/device, other geo findings, consumer/API-ABI/dependency/security and release gates remain independent/open under BUILD-006/release-readiness. Geo remains unpublished; no package/release/deployment published. Original issue body/title/labels/history retained.
'''
(out/'comment.md').write_text(body)
posted=api('comment-post','issues/'+str(issue_id)+'/comments','POST',{'body':body});assert posted['body']==body
patched=api('issue-patch','issues/'+str(issue_id),'PATCH',{'state':'closed','state_reason':'completed'});assert patched['state']=='closed'
after=api('issue-after','issues/'+str(issue_id));comment=api('comment-after','issues/comments/'+str(posted['id']))
assert after['state']=='closed' and comment['body']==body and after['body']==issue['body'] and after['title']==issue['title']
assert sorted(l['name'] for l in after['labels'])==sorted(l['name'] for l in issue['labels'])
save('closure.json',{'reviewed_utc':stamp(),'passed':True,'finding':'PERM-018','issue_number':issue_id,'state':'closed','closed_at':after['closed_at'],'comment_id':posted['id'],'comment_url':posted['html_url'],'source_revision':current,'tested_revision':revision,'all_two_original_criteria_accepted':True,'POST_invocations':1,'PATCH_invocations':1,'original_body_title_labels_preserved':True,'new_test_executions':0,'publication_performed':False,'release_readiness_certified':False})
print(json.dumps({'issue':issue_id,'state':after['state'],'criteria':2,'host_cases':88,'comment_url':posted['html_url']}),flush=True)
