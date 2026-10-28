from pathlib import Path
import datetime,hashlib,json,subprocess,sys,time,zipfile
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).parent/sys.argv[1];O.mkdir();SHA=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();assert not subprocess.check_output(['git','status','--porcelain'],cwd=R)
sys.path.insert(0,str(R/'scripts/ci'));import library_tests as lt,runtime_context as rt
before=lt.snapshot_inputs(R);(O/'inputs-before.json').write_text(json.dumps(before,indent=2)+'\n');context=rt.capture(android_package='android-37.0');(O/'runtime.json').write_text(json.dumps(context,indent=2)+'\n');assert context['source_revision']==SHA and not context['source_tree_dirty']
suites={'desktop':'desktopTest','android-host':'testAndroidHostTest'}
with zipfile.ZipFile(O/'prior-reports-not-current.zip','x') as z:
 for suite,task in suites.items():
  d=R/'calf-ui/build/test-results'/task
  if d.exists():
   for f in sorted(d.glob('TEST-*.xml')):assert f.is_file() and not f.is_symlink();z.writestr(suite+'/'+f.name,f.read_bytes());f.unlink()
command=['xvfb-run','-a','./gradlew',':calf-ui:desktopTest','--tests','com.mohamedrejeb.calf.ui.datepicker.CompactDateTransactionAcceptanceTest.nullInputClearCancelReopenAndConfirmRemainTransactional',':calf-ui:testAndroidHostTest','--tests','com.mohamedrejeb.calf.ui.datepicker.CompactDateTransactionAcceptanceTest.nullInputClearCancelReopenAndConfirmRemainTransactional','--continue','--max-workers=2','--no-daemon','--no-configuration-cache','--console=plain','-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8','-Pkotlin.compiler.execution.strategy=in-process','--init-script','scripts/ci/fresh-tests.init.gradle.kts']
started=time.time_ns();result=lt.execute(R,command,O/'actual-gradle.log',600,8192);ended=time.time_ns();after=lt.snapshot_inputs(R);(O/'inputs-after.json').write_text(json.dumps(after,indent=2)+'\n');reports=[]
for suite,task in suites.items():
 (O/suite).mkdir()
 for f in sorted((R/'calf-ui/build/test-results'/task).glob('TEST-*.xml')):
  raw=f.read_bytes();cases=lt.junit_cases(raw);(O/suite/f.name).write_bytes(raw);reports.append(dict(suite=suite,file=suite+'/'+f.name,sha256=hashlib.sha256(raw).hexdigest(),is_fresh=started<=f.stat().st_mtime_ns<=ended,cases=cases,counts=lt.case_counts(cases)))
receipt=dict(source_revision=SHA,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=command,execution=result,inputs_equal=before==after,source_revision_unchanged=SHA==subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),source_input_count=len(before),reports=reports,source_scope='Four actual public Material date-dialog transactions on desktop and Android-host. Robolectric SDK34 is not Android-device execution; no sample substitutes',packages_releases_deployments_published=False)
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2),flush=True)
assert before==after and receipt['source_revision_unchanged'] and reports and all(x['is_fresh'] for x in reports)
