"""Source-held real Compose host tests with one explicit effect-key negative control.

Offline JDK17/declared Gradle/Kotlin/Compose; bounded own group and both disks.
No package/source rewrite or release certification. Copies only reviewed inputs.
"""
from pathlib import Path
import datetime as dt,hashlib,json,os,re,shutil,signal,subprocess,sys,time
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
MODE=sys.argv[1];assert MODE in {'control001','green002'}
OUT=BASE/MODE;OUT.mkdir()
OWNED=Path(json.loads((ROOT/'build/android-webview-fixture-compile-20261027-001/owned.json').read_bytes())['path'])
assert OWNED.is_relative_to(Path('/dev/shm')) and OWNED.name.startswith('nativecmpkit-owned-webview-compile-')
PROJECT=OWNED/'project';assert PROJECT.is_dir() and not PROJECT.is_symlink()
HOST='calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt'
FIXTURE='calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/AdaptiveNavHostStateTest.kt'
root_before=lt.snapshot_inputs(ROOT);copy_before=lt.snapshot_inputs(PROJECT)
assert root_before==copy_before
original=(PROJECT/HOST).read_bytes();(OUT/'host-original.kt').write_bytes(original)
(OUT/'fixture.kt').write_bytes((ROOT/FIXTURE).read_bytes())
if MODE=='control001':
 assert original.count(b'LaunchedEffect(navController, startDestination)')==1
 mutated=original.replace(b'LaunchedEffect(navController, startDestination)',b'LaunchedEffect(Unit)')
 (PROJECT/HOST).write_bytes(mutated);(OUT/'host-control.kt').write_bytes(mutated)
executed_before=lt.snapshot_inputs(PROJECT)
assert set(executed_before)==set(root_before)
changes=[n for n in root_before if executed_before[n]!=root_before[n]]
assert changes==([HOST] if MODE=='control001' else [])
for n,values in [('inputs-before.json',root_before),('copy-executed-before.json',executed_before)]:lt.write_json(OUT/n,values)
reports=PROJECT/'calf-navigation/build/test-results/desktopTest'
if reports.exists():
 assert reports.is_dir() and not reports.is_symlink()
 shutil.move(str(reports),OUT/'quarantined-prior-reports')
env=os.environ.copy()
for n in ('JAVACMD','JAVA_OPTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS'):env.pop(n,None)
env.update(JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64',GRADLE_USER_HOME=str(OWNED/'gradle-home'),TMPDIR=str(OWNED),KONAN_DATA_DIR=str(OWNED/'konan-data'),PYTHONDONTWRITEBYTECODE='1')
java=Path(env['JAVA_HOME'])/'bin/java';version=subprocess.check_output([str(java),'-version'],stderr=subprocess.STDOUT,env=env).decode();assert 'version "17.' in version
sdk=env.get('ANDROID_HOME') or env.get('ANDROID_SDK_ROOT')
if not sdk:
 lines=(ROOT/'local.properties').read_text().splitlines();values=[s.split('=',1)[1] for s in lines if s.startswith('sdk.dir=')];assert len(values)==1;sdk=values[0]
assert (Path(sdk)/'platforms/android-37.0/android.jar').is_file();env.update(ANDROID_HOME=sdk,ANDROID_SDK_ROOT=sdk)
assert env.get('DISPLAY'), 'A real Xvfb display is required for real Compose testing'
selector='com.mohamedrejeb.calf.navigation.AdaptiveNavHostStateTest'
if MODE=='control001':selector+='.*changing start route*'
argv=[str(ROOT/'gradlew'),'-p',str(PROJECT),'--project-cache-dir',str(OWNED/'project-cache'),'--offline','--no-daemon','--console=plain','--no-configuration-cache','--no-parallel','--max-workers=1','-Dorg.gradle.jvmargs=-Xmx1536m -Dfile.encoding=UTF-8','-Pkotlin.compiler.execution.strategy=in-process','--init-script',str(PROJECT/'scripts/ci/fresh-tests.init.gradle.kts'),':calf-navigation:desktopTest','--tests',selector,'--stacktrace']
reserve=8192*1024**2;root_free=shutil.disk_usage(ROOT).free;copy_free=shutil.disk_usage(PROJECT).free
assert min(root_free,copy_free)>=reserve
started=lt.utc_now();start_ns=time.time_ns();clock=time.monotonic();execution={}
def stop(p):
 if p.poll() is not None:return
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=5)
 except subprocess.TimeoutExpired:
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  p.wait(timeout=10)
try:
 with (OUT/'test.log').open('x') as f:
  p=subprocess.Popen(argv,cwd=PROJECT,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   while p.poll() is None:
    if min(shutil.disk_usage(ROOT).free,shutil.disk_usage(PROJECT).free)<reserve:execution['stop_reason']='One8GiB reserve reached'
    elif (OUT/'test.log').stat().st_size>64*1024**2:execution['stop_reason']='64MiB own log limit'
    elif time.monotonic()-clock>600:execution['stop_reason']='600second own deadline'
    if execution:stop(p);break
    time.sleep(.2)
  except BaseException:stop(p);raise
  execution.update(exit_code=p.returncode,elapsed_seconds=round(time.monotonic()-clock,3))
 end_ns=time.time_ns();finished=lt.utc_now()
 root_after=lt.snapshot_inputs(ROOT);executed_after=lt.snapshot_inputs(PROJECT)
 lt.write_json(OUT/'inputs-after.json',root_after);lt.write_json(OUT/'copy-executed-after.json',executed_after)
 expected={'module':'calf-navigation','project':':calf-navigation','task':':calf-navigation:desktopTest','report_directory':'calf-navigation/build/test-results/desktopTest','test_source_sets':['desktopTest'],'test_source_files':[FIXTURE]}
 collected=lt.collect_reports(PROJECT,{'suite':'desktop','expected':[expected]},start_ns,end_ns,lt.execution_markers(OUT/'test.log'),host_system='Linux')
 lt.write_json(OUT/'collector.json',collected)
 for m in collected['modules']:
  for row in m['reports']:
   source=PROJECT/row['path'];dest=OUT/'reports'/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);assert lt.sha256(dest)==row['sha256']
 counts=lt.case_counts(collected['modules'][0]['testcases']) if collected['modules'] else lt.case_counts([])
 record={'recorded_utc':lt.utc_now(),'mode':MODE,'source_revision':lt.git_revision(ROOT),'dirty_held_root':True,'started_utc':started,'finished_utc':finished,'execution':execution,'command':argv,'root_inputs_held':root_before==root_after,'executed_copy_inputs_held':executed_before==executed_after,'source_input_count':len(root_before),'root_inputs_sha256':lt.input_digest(root_before),'copy_inputs_sha256':lt.input_digest(executed_before),'explicit_copy_source_changes':changes,'collector':collected,'test_counts':counts,'java_version':version,'java_executable_sha256':lt.sha256(java),'driver_sha256':lt.sha256(Path(__file__)),'log_sha256':lt.sha256(OUT/'test.log'),'reserve_bytes':reserve,'free_root_before':root_free,'free_copy_before':copy_free,'free_root_after':shutil.disk_usage(ROOT).free,'free_copy_after':shutil.disk_usage(PROJECT).free,'actual_Xvfb_display_required':True,'packages_published':False,'native_device_or_consumer_verification':False,'release_readiness_certified':False}
 lt.write_json(OUT/'receipt.json',record)
 print(json.dumps({k:record[k] for k in ('mode','execution','test_counts','root_inputs_held','executed_copy_inputs_held','explicit_copy_source_changes')},indent=2),flush=True)
 if MODE=='control001':
  assert counts['tests']==counts['executed']==counts['failures']==1 and counts['passed']==counts['errors']==counts['skipped']==0
  assert execution['exit_code']==1 and not execution.get('stop_reason')
 else:
  assert execution['exit_code']==0 and not execution.get('stop_reason') and not collected['errors']
  assert counts['tests']==counts['executed']==counts['passed']==12 and counts['failures']==counts['errors']==counts['skipped']==0
 assert root_before==root_after and executed_before==executed_after
finally:
 if MODE=='control001':(PROJECT/HOST).write_bytes(original)
