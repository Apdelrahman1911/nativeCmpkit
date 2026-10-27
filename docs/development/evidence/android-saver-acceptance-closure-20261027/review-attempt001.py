from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess,xml.etree.ElementTree as ET,zipfile
root=Path('/root/projects/nativeCmpKit'); out=Path(__file__).parent
repo='Apdelrahman1911/nativeCmpkit'; marker='<!-- nativecmpkit-resolution:IO-002:40414284598:40436756084 -->'
current=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
sha=lambda data:hashlib.sha256(data).hexdigest()
def api(name,endpoint,method='GET',body=None):
 command=['gh','api','repos/'+repo+'/'+endpoint,'--method',method]
 if body is not None: command+=['--input','-']
 run=subprocess.run(command,input=json.dumps(body).encode() if body is not None else None,capture_output=True)
 (out/(name+'.json')).write_bytes(run.stdout);(out/(name+'.stderr')).write_bytes(run.stderr)
 assert run.returncode==0, f'Failed {method}; inspect response before any retry'
 return json.loads(run.stdout)
def blob(revision,path): return subprocess.check_output(['git','show',revision+':'+path],cwd=root)
host_base=root/'docs/development/evidence/github-actions/40414284598'
dev_base=root/'docs/development/evidence/github-actions/40436756084'
host_review=json.loads((host_base/'lead-independent-review.json').read_bytes())
dev_review=json.loads((dev_base/'lead-independent-review.json').read_bytes())
assert host_review['evidence_integrity_passed'] and dev_review['evidence_integrity_passed']
assert host_review['run_conclusion']=='success' and dev_review['run_conclusion']=='failure'
host_slot=next(s for s in host_review['runtime_slots'] if s['slot']=='android-host')
assert host_slot['execution']['exit_code']==0 and host_slot['totals']['passed']==405
host_rev=host_review['source_revision'];dev_rev=dev_review['source_revision']
paths=['calf-file-picker/src/commonMain','calf-file-picker/src/androidMain','calf-file-picker/src/androidHostTest','calf-file-picker/src/androidDeviceTest','calf-core/src/commonMain','calf-core/src/androidMain','calf-io/src/commonMain','calf-io/src/androidMain','calf-core/build.gradle.kts','calf-io/build.gradle.kts','calf-file-picker/build.gradle.kts','gradle/libs.versions.toml','gradle/wrapper/gradle-wrapper.properties','gradle.properties','build.gradle.kts','convention-plugins','settings.gradle.kts']
changed=subprocess.check_output(['git','diff','--name-only',dev_rev,current,'--',*paths],cwd=root,text=True).splitlines()
assert set(changed)=={'convention-plugins/src/main/kotlin/module.publication.gradle.kts','settings.gradle.kts'}
for path in changed:
 old=blob(dev_rev,path);new=(root/path).read_bytes()
 expected=old.replace(b'rootProject.name = "nativeCmpkit"',b'rootProject.name = "NativeCmpKit"') if path=='settings.gradle.kts' else old.replace(b'name.set("nativeCmpkit - "',b'name.set("NativeCmpKit - "')
 assert new==expected,'Unexpected build change'
host_changed=subprocess.check_output(['git','diff','--name-only',host_rev,current,'--',*paths],cwd=root,text=True).splitlines()
kmp='calf-io/src/androidMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.android.kt'
assert set(host_changed)==set(changed)|{kmp}
def remove_directory_function(value):
 start=value.index(b'actual fun KmpFile.isDirectory(context: PlatformContext): Boolean {')
 end=value.index(b'/** Keep the original tree URI/grant',start)
 return value[:start]+value[end:]
assert remove_directory_function(blob(host_rev,kmp))==remove_directory_function((root/kmp).read_bytes())
# Saver ownership/copy/restoration calls .uri, not the changed metadata-only query.
saver=root/'calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt'
assert '.isDirectory(' not in saver.read_text()
source_hashes={}
for relative in subprocess.check_output(['git','ls-tree','-r','--name-only',current,'--',*paths],cwd=root,text=True).splitlines():
 if (root/relative).is_file():source_hashes[relative]=sha((root/relative).read_bytes())

def cases(base,artifact_id,digest,suffix,module):
 p=base/'raw'/f'{artifact_id}.zip'; assert 'sha256:'+sha(p.read_bytes())==digest
 with zipfile.ZipFile(p) as archive:
  reports=[n for n in archive.namelist() if n.startswith(module+'/') and suffix in n and n.endswith('.xml')]
  all_cases=[];records=[]
  for name in reports:
   raw=archive.read(name);assert b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper()
   tree=ET.fromstring(raw)
   records.append({'path':name,'sha256':sha(raw),'timestamp':tree.attrib['timestamp']})
   for case in tree.iter('testcase'):
    status='failure' if list(case.iter('failure')) else 'error' if list(case.iter('error')) else 'skipped' if list(case.iter('skipped')) else 'passed'
    all_cases.append({'classname':case.attrib['classname'],'name':case.attrib['name'],'status':status})
  assert len(all_cases)==len({(c['classname'],c['name']) for c in all_cases})
  return all_cases,records
host_cases,host_reports=cases(host_base,host_slot['artifact_id'],host_slot['artifact_digest'],'/testAndroidHostTest/','calf-file-picker')
dev_cases,dev_reports=cases(dev_base,dev_review['artifact_id'],dev_review['artifact_digest'],'/androidTest-results/','calf-file-picker')
assert len(host_cases)==35 and len(host_reports)==8 and all(c['status']=='passed' for c in host_cases)
activity=[c for c in dev_cases if c['classname'].endswith('.FileSaverActivityDeviceTest')]
assert len(activity)==8 and all(c['status']=='passed' for c in activity)
assert len(dev_cases)==25 and sum(c['status']=='passed' for c in dev_cases)==24
assert [c for c in dev_cases if c['status']!='passed']==[{'classname':'com.mohamedrejeb.calf.picker.SaveDestinationDeviceTest','name':'actualHardLinkIsNotTruncatedOrDeleted','status':'failure'}]
finding=next(f for f in json.loads((root/'docs/audit/findings/IO.json').read_bytes()) if f['id']=='IO-002')
assert len(finding['required_tests'])==5
rows=[[(host_cases,'FileSaverLauncherTest','bytesAreWrittenWhenTheResultArrivesInALaterComposition'),(host_cases,'FileSaverLauncherTest','aFileIsCopiedWhenTheResultArrivesInALaterComposition')],[(dev_cases,'FileSaverActivityDeviceTest','uriPayloadSurvivesActualHostActivityRecreationBeforeTheResult'),(dev_cases,'FileSaverActivityDeviceTest','lostBytePayloadAfterActualRecreationIsAnErrorNotEmptySuccess')],[(dev_cases,'FileSaverActivityDeviceTest','frameworkCancellationDeliversOneNullResultAndReleasesTheNextLaunch'),(host_cases,'PendingSaveSourceTest','aCompletedRequestDoesNotRestoreAsAnotherOutstandingSave')],[(host_cases,'PendingSaveSourceTest','consumeIsExactlyOnceAndRejectsOverlapUntilWriteFinishes'),(dev_cases,'FileSaverActivityDeviceTest','overlapReportsOneErrorWithoutReplacingTheAcceptedNativeRequest')],[(host_cases,'FileSaverLauncherTest','savingAMissingFileToItselfDoesNotClaimSuccess'),(dev_cases,'FileSaverActivityDeviceTest','lostBytePayloadAfterActualRecreationIsAnErrorNotEmptySuccess'),(dev_cases,'SaveDestinationDeviceTest','failedDistinctProviderSourceDeletesOnlyTheNewDocumentWithoutWritingIt')]]
criteria=[]
for requirement,row in zip(finding['required_tests'],rows,strict=True):
 matched=[]
 for available,cls,method in row:
  matches=[c for c in available if c['classname']=='com.mohamedrejeb.calf.picker.'+cls and c['name']==method]
  assert len(matches)==1 and matches[0]['status']=='passed'
  matched+=matches
 criteria.append({'original_requirement':requirement,'status':'accepted','actual_cases':matched})
prior=next(f for f in json.loads((root/'docs/development/resolutions/IO.json').read_bytes()) if f['id']=='IO-002')
acceptance={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'finding':'IO-002','current_revision':current,'host_revision':host_rev,'host_run':40414284598,'device_revision':dev_rev,'device_run':40436756084,'host35_passed':True,'native_Activity_class8_passed':True,'all_five_original_criteria_accepted':True,'criteria':criteria,'current_affected_input_sha256':source_hashes,'current_android_device_source_and_dependencies_identical_except_two_exact_display_strings':True,'host_only_additional_change':'KmpFile.isDirectory metadata query, not called by saver; all other body bytes, affected source/test/dependency inputs unchanged. Later actual device source contains this repair.','host_XML':host_reports,'device_XML':dev_reports,'prior_remaining_preserved':prior['remaining'],'reuse':'Review of already-executed immutable XML; zero new test executions and no repeat of unchanged suites.','limits':['Whole device workflow remains failed: unrelated WebView precondition and real Android hard-link setup EACCES are not waived or converted to passing.','Actual Activity recreation, not OS process death/persisted grants/physical or minimum API.','Independent hard-link/unknown identity/provider/dependency/legal/full consumer/API-ABI/release gates remain tracked under BUILD-006 and release-readiness.'],'publication_performed':False,'release_readiness_certified':False}
(out/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n');print('All five original Android saver criteria accepted; prior same-input results reused, not recounted as fresh.',flush=True)
issue=api('issue-before','issues/5');assert issue['state']=='open' and '<!-- nativecmpkit-item:audit:IO-002 -->' in issue['body']
assert all(required in issue['body'] for required in finding['required_tests'])
comments=api('comments-before','issues/5/comments?per_page=100');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
body=f'''{marker}
## Verified resolution — IO-002

The Android saver now shares one `rememberSaveable` request holder across launcher/result recompositions, consumes/clears exactly once, rejects overlapping launches and treats restored/lost ByteArray content as an error, never an empty-success save. URI state is restored; large byte payloads are not put in the Activity Bundle. Existing public launch signatures are retained.

**All five original criteria are verified:**
1. Real Compose/Robolectric launch → recompose → result preserves both bytes and KmpFile content.
2. Actual Android Activity recreation below the real child Activity restores a URI request; lost bytes fail/clean up without a write or success callback.
3. Actual cancellation yields one null result, then a new launch writes its own payload; completed state cannot restore as pending.
4. Exactly-once consumption and native overlap rejection do not replace the accepted request.
5. Missing/lost/unreadable required content cannot report a no-op save as success; actual provider failure writes nothing and cleans only the new destination.

Reviewed immutable executions: [host run40414284598](https://github.com/{repo}/actions/runs/40414284598) at `{host_rev}` (**35/35 picker host methods**, eight XML; host job exit0) and [device run40436756084](https://github.com/{repo}/actions/runs/40436756084) at `{dev_rev}` (**8/8 actual FileSaverActivityDeviceTest methods**, API35/x86_64, SELinux Enforcing). XML hashes and named cases were inspected. Current Android production/test/dependency inputs match the device revision except two exact project/POM display strings; host saver inputs also match, with only an unrelated `isDirectory` metadata repair that the saver does not call. These existing same-input results are reused explicitly; no new execution is claimed.

Closing the original five-criterion finding directly after review. **The overall device run remains failed** (24/25 picker; native hard-link fixture EACCES plus unrelated WebView history precondition); those independent coverage/security gates remain open under BUILD-006/release-readiness. OS process-death/persisted grants, physical/minimum API, broader provider/native ownership, legal/dependency, packaged consumer and API/ABI remain unverified. No package/release/deployment was published. Original issue body/labels/history are preserved.
'''
(out/'comment.md').write_text(body)
posted=api('comment-post','issues/5/comments','POST',{'body':body});assert posted['body']==body
closed=api('issue-patch','issues/5','PATCH',{'state':'closed','state_reason':'completed'});assert closed['state']=='closed'
readback=api('issue-after','issues/5');comment=api('comment-after','issues/comments/'+str(posted['id']))
assert readback['state']=='closed' and comment['body']==body
assert readback['body']==issue['body'] and readback['title']==issue['title']
assert sorted(x['name'] for x in readback['labels'])==sorted(x['name'] for x in issue['labels'])
receipt={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'finding':'IO-002','issue_number':5,'state':'closed','closed_at':readback['closed_at'],'comment_url':posted['html_url'],'comment_id':posted['id'],'POST_invocations':1,'PATCH_invocations':1,'original_body_title_labels_preserved':True,'all_five_original_criteria_accepted':True,'source_revision':current,'evidence_reused_not_rerun':True,'new_test_executions':0,'new_issue_closures':1,'publication_performed':False,'release_readiness_certified':False}
(out/'closure.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
