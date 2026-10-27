"""Use just-reviewed important suites, review two independent owning contracts, close directly."""
from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess
root=Path('/root/projects/nativeCmpKit');base=Path(__file__).parent;repo='Apdelrahman1911/nativeCmpkit'
current=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(out,n,d):(out/n).write_text(json.dumps(d,indent=2)+'\n')
def api(out,name,endpoint,method='GET',body=None):
 cmd=['gh','api','repos/'+repo+'/'+endpoint,'--method',method]
 if body is not None:cmd+=['--input','-']
 r=subprocess.run(cmd,input=json.dumps(body).encode() if body is not None else None,capture_output=True,timeout=90)
 (out/(name+'.json')).write_bytes(r.stdout)
 if r.stderr:(out/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,'API failure: inspect preserved response before any mutation retry'
 return json.loads(r.stdout)
def matched(parent,cls,methods,package):
 result=[]
 for method in methods:
  found=[c for c in parent['actual_cases'] if c['classname']==package+cls and c['name']==method]
  assert len(found)==1 and found[0]['status']=='passed';result+=found
 return result
geo=json.loads(Path('/dev/shm/nativecmpkit-geo-state-acceptance-20261027/acceptance.json').read_bytes())
web=json.loads(Path('/dev/shm/nativecmpkit-webview-acceptance-20261027/acceptance.json').read_bytes())
assert geo['current_revision']==web['source_revision']==current and geo['all_two_original_criteria_accepted'] and web['all_734_selected_inputs_equal_exact_own_Git']
# Geo's reviewed scope contains all its current files. Source-held acceptance is reused,
# not a second claim of88 executed methods; every relevant current hash still matches.
for path,digest in geo['current_affected_inputs'].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest
source=(root/'calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/AndroidLocationFix.kt').read_text()
for token in ['if (hasAccuracy())','if (hasSpeed())','if (hasBearing())','if (hasAltitude())','Build.VERSION.SDK_INT >= 26 && hasSpeedAccuracy()','Build.VERSION.SDK_INT >= 26 && hasBearingAccuracy()','Build.VERSION.SDK_INT >= 26 && hasVerticalAccuracy()','time.takeIf { it > 0L }','elapsedRealtimeNanos.takeIf { it > 0L }','Build.VERSION.SDK_INT >= 31']:
 assert token in source
# The parent geo acceptance does not duplicate all88 cases; reconstruct its exact
# already-reviewed raw XML cases with the same digest, without a test rerun.
import sys,zipfile
sys.path.insert(0,str(root/'scripts/ci'));import library_tests as lt
p=root/'docs/development/evidence/github-actions/40414284598/raw'/str(geo['artifact_id']);p=p.with_suffix('.zip')
assert 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()==geo['artifact_digest']
with zipfile.ZipFile(p) as z:
 geo['actual_cases']=[c for r in geo['actual_XML_reports'] for c in lt.junit_cases(z.read(r['path']))]
assert len(geo['actual_cases'])==88 and all(c['status']=='passed' for c in geo['actual_cases'])
flag_cases=[c for c in geo['actual_cases'] if c['classname']=='com.mohamedrejeb.calf.geo.AndroidLocationFixTest'];assert len(flag_cases)==22
assert {c['name'] for c in flag_cases}=={n+s for n in ['nativeMissingFieldsRemainIndependentlyAbsent','realZeroMeasurementsAreNotConfusedWithMissingFlags','measurementPresenceDoesNotInventAccuracyOnNewerApis','nativeAccuracyFlagCanExistWithoutItsMeasurementFlag','clearingNativeFlagsDoesNotPublishTheirDefaultZeros','unitsTimesAndNegativeAltitudeAreRetainedWithoutConversions','invalidCoordinatesDoNotBecomeAnObservedFix'] for s in ['[23]','[26]','']}|{'nativeMockFlagRemainsVisibleToConsumers'}
geo_extra=matched(geo,'LocationTrackingControllerTest',['approximateForegroundPermissionIsSufficient','duplicateAndOlderFixesDoNotReplaceNewerState','trueZeroAndIndependentlyAbsentMeasurementsArePreserved'],'com.mohamedrejeb.calf.geo.')
web_source=(root/'calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt').read_text()
for token in ['Channel<NavigationEvent>(capacity = 64)','check(attachment.tryLock())','while (true) handle(navigationEvents.receive())','attachment.unlock()','Commands already','coroutineScope.isActive']:
 assert token in web_source
for p in ['calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt','calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt','calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt','calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt']:
 assert 'consumeNavigationEvents' in (root/p).read_text()
nav_cases=matched(web,'WebViewNavigatorTest',['commandsBeforeAttachmentAreDeliveredOnlyOnce[desktop]','oneNavigatorRejectsTwoSimultaneousOwners[desktop]','attachmentSnapshotPrecedesCommandsAndRejectedOwnersCannotRunIt[desktop]'],'com.mohamedrejeb.calf.ui.web.')
items=[
 {'finding':'PERM-022','area':'PERM','issue':117,'run':40414284598,'tested_revision':geo['tested_revision'],'cases':[flag_cases,flag_cases+geo_extra],'parent':'docs/development/evidence/geo-state-acceptance-closure-20261027/acceptance.json','summary':'Android location flags, units and true zero measurements','detail':'The real Android Location mapper checks each has* flag independently, guards API26 accuracy getters and the API31 mock flag, keeps UTC/monotonic clocks distinct, preserves true zero and negative altitude, and represents missing/nonfinite values explicitly. It does not synthesize perfect-zero accuracy or measurement presence. Coarse permission and duplicate/stale fixes are separately exercised in the production controller.','result':'88/88 geo host executions in five original fresh XML, including22 AndroidLocationFix cases on API23/26/34 and named coarse/stale/true-zero controller cases. All relevant current geo/test/dependency inputs remain unchanged except two exact root/POM display strings. Existing immutable results are reused; zero new executions.','limits':'Real Android Location/GMS objects under Robolectric, injected provider transport; not GPS hardware, measured positioning accuracy or a device runtime. No consumer stale/coarse/mock policy is imposed; clients choose it. Missing legacy values use the documented NaN/null/time0 compatibility sentinels. No public signature or package is renamed; no ABI certification. Physical/minimum-device/provider/dependency/consumer/security/release gates remain independent.'},
 {'finding':'NATIVE-008','area':'NATIVE','issue':67,'run':40596231788,'tested_revision':current,'cases':[[nav_cases[0]],[nav_cases[0]],[nav_cases[1],nav_cases[2]]],'parent':'docs/development/evidence/webview-stop-acceptance-closure-20261027/acceptance.json','summary':'Consume transient navigation once and enforce one owner','detail':'The common navigator now owns a bounded64-command Channel and exclusive Mutex admission, rather than replay-one broadcast. Pre-attachment loads are retained once; a received Back/Forward/Stop is never replayed to a replacement collector. Simultaneous owners are rejected explicitly and documented; all production platform consumers use this shared contract. Headers are snapshotted and detached capability flags cleared.','result':'37/37 actual Linux desktop methods in seven fresh XML at734 exact own-Git inputs. The exact common tests consume pre-attachment Load+Back, replace the collector without replay, and reject a second owner; the actual native JavaFX/window repeated-stop/reattachment method also passes. This reuses the just-reviewed run; zero additional executions or repeated CI suites.','limits':'Common consumer ownership/queue and real JavaFX window stop integration, not actual multi-Compose-window mount/GC certification on every backend. Android Chromium history-restoration/replacement fixture remains failed and open under BUILD-006/release-readiness; its broader native-history gate is not the original shared-flow replay contract and is not waived. Original public signatures retained; bounded overflow now fails explicitly and prior replay/broadcast behavior intentionally removed. Other physical/minimum/ownership/security/consumer/ABI/release gates remain independent.'},
]
for item in items:
 out=base/item['finding'];out.mkdir();finding=next(f for f in json.loads((root/'docs/audit/findings'/str(item['area']+'.json')).read_bytes()) if f['id']==item['finding'])
 assert len(finding['required_tests'])==len(item['cases'])
 criteria=[{'original_requirement':req,'status':'accepted','actual_cases':cases} for req,cases in zip(finding['required_tests'],item['cases'],strict=True)]
 save(out,'acceptance.json',{'reviewed_utc':stamp(),'finding':item['finding'],'current_revision':current,'tested_revision':item['tested_revision'],'run_id':item['run'],'parent_review':item['parent'],'all_original_criteria_accepted':True,'criteria':criteria,'source_review':item['detail'],'reused_results':item['result'],'limits':item['limits'],'new_test_executions':0,'publication_performed':False,'release_readiness_certified':False})
 print('Accepted '+item['finding']+' original criteria; no repeat executions.',flush=True)
 issue=api(out,'issue-before','issues/'+str(item['issue']));assert issue['state']=='open' and '<!-- nativecmpkit-item:audit:'+item['finding']+' -->' in issue['body'] and all(req in issue['body'] for req in finding['required_tests'])
 marker='<!-- nativecmpkit-resolution:'+item['finding']+':'+str(item['run'])+' -->'
 comments=api(out,'comments-before','issues/'+str(item['issue'])+'/comments?per_page=100');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
 body=f'''{marker}
## Verified resolution — {item['finding']}

{item['detail']}

**All {len(criteria)} original acceptance criteria reviewed and passed.** [Immutable run{item['run']}](https://github.com/{repo}/actions/runs/{item['run']}) at `{item['tested_revision']}`: {item['result']}

Closing directly after required-test/source/result review. **Scope limits:** {item['limits']} No package/release/deployment published. Original issue body/title/labels/discussion/history preserved.
'''
 (out/'comment.md').write_text(body)
 posted=api(out,'comment-post','issues/'+str(item['issue'])+'/comments','POST',{'body':body});assert posted['body']==body
 patched=api(out,'issue-patch','issues/'+str(item['issue']),'PATCH',{'state':'closed','state_reason':'completed'});assert patched['state']=='closed'
 after=api(out,'issue-after','issues/'+str(item['issue']));comment=api(out,'comment-after','issues/comments/'+str(posted['id']))
 assert after['state']=='closed' and comment['body']==body and after['body']==issue['body'] and after['title']==issue['title']
 assert sorted(l['name'] for l in after['labels'])==sorted(l['name'] for l in issue['labels'])
 save(out,'closure.json',{'reviewed_utc':stamp(),'passed':True,'finding':item['finding'],'issue_number':item['issue'],'state':'closed','closed_at':after['closed_at'],'comment_id':posted['id'],'comment_url':posted['html_url'],'current_revision':current,'tested_revision':item['tested_revision'],'all_original_criteria_accepted':True,'POST_invocations':1,'PATCH_invocations':1,'original_body_title_labels_preserved':True,'new_test_executions':0,'publication_performed':False,'release_readiness_certified':False})
 print(json.dumps({'finding':item['finding'],'issue':item['issue'],'state':after['state'],'comment_url':posted['html_url']}),flush=True)
