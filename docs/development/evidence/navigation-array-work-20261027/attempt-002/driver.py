"""Two actual navigation library work/allocation checks, copied held sources on Linux.

Compilation caches are reused; old test XML is quarantined, never counted fresh.
No sample, iOS/device, dependency-trust, consumer or publication certification.
"""
from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,subprocess,sys,time
from collections import Counter
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests as lt
owned=Path(json.loads((ROOT/'build/android-webview-fixture-compile-20261027-001/owned.json').read_bytes())['path'])
assert owned.is_relative_to(Path('/dev/shm')) and owned.name.startswith('nativecmpkit-owned-webview-compile-')
project=owned/'project';assert project.is_dir() and not project.is_symlink()
inputs=lt.snapshot_inputs(ROOT);assert inputs==lt.snapshot_inputs(project) and len(inputs)==726
assert shutil.disk_usage(ROOT).free>=8192*1024**2 and shutil.disk_usage(project).free>=8192*1024**2
lt.write_json(OUT/'inputs-before.json',inputs)
lt.write_json(OUT/'copied-inputs-before.json',lt.snapshot_inputs(project))
reports=project/'calf-navigation/build/test-results/desktopTest'
if reports.exists():
 assert reports.is_dir() and not reports.is_symlink()
 shutil.move(str(reports),OUT/'quarantined-prior-reports')
env=os.environ.copy()
for name in ['JAVACMD','JAVA_OPTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS']:
 env.pop(name,None)
env.update(JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64',GRADLE_USER_HOME=str(owned/'gradle-home'),TMPDIR=str(owned),KONAN_DATA_DIR=str(owned/'konan-data'),PYTHONDONTWRITEBYTECODE='1')
java=Path(env['JAVA_HOME'])/'bin/java';version=subprocess.check_output([str(java),'-version'],stderr=subprocess.STDOUT,env=env).decode()
assert 'version "17.' in version
sdk=env.get('ANDROID_HOME') or env.get('ANDROID_SDK_ROOT')
if not sdk:
 lines=(ROOT/'local.properties').read_text().splitlines();matches=[s.split('=',1)[1] for s in lines if s.startswith('sdk.dir=')];assert len(matches)==1;sdk=matches[0]
assert (Path(sdk)/'platforms/android-37.0/android.jar').is_file()
env.update(ANDROID_HOME=sdk,ANDROID_SDK_ROOT=sdk)
argv=[str(ROOT/'gradlew'),'-p',str(project),'--project-cache-dir',str(owned/'project-cache'),'--offline','--no-daemon','--console=plain','--no-configuration-cache','--no-parallel','--max-workers=1','-Dorg.gradle.jvmargs=-Xmx1536m -Dfile.encoding=UTF-8','-Pkotlin.compiler.execution.strategy=in-process','--init-script',str(project/'scripts/ci/fresh-tests.init.gradle.kts'),':calf-navigation:desktopTest','--tests','com.mohamedrejeb.calf.navigation.NavArrayParsingWorkTest','--stacktrace']
start=time.time_ns();started=lt.utc_now();execution=lt.execute(project,argv,OUT/'test.log',900,8192,env=env);end=time.time_ns();finished=lt.utc_now()
after=lt.snapshot_inputs(ROOT);copied_after=lt.snapshot_inputs(project)
lt.write_json(OUT/'inputs-after.json',after);lt.write_json(OUT/'copied-inputs-after.json',copied_after)
lt.write_json(OUT/'execution-before-report-review.json', {'execution':execution,'started_utc':started,'finished_utc':finished,'command':argv})
expected={'module':'calf-navigation','project':':calf-navigation','task':':calf-navigation:desktopTest','report_directory':'calf-navigation/build/test-results/desktopTest','test_source_sets':['desktopTest'],'test_source_files':['calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/NavArrayParsingWorkTest.kt']}
collected=lt.collect_reports(project,{'suite':'desktop','expected':[expected]},start,end,lt.execution_markers(OUT/'test.log'),host_system='Linux')
lt.write_json(OUT/'collector.json', collected)
assert not collected['errors'], collected['errors']
assert len(collected['modules'])==1
parsed=collected['modules'][0]
passed=execution['exit_code']==0 and not execution.get('stop_reason') and inputs==after==copied_after and parsed['tests']==parsed['passed']==parsed['executed']==2 and parsed['failures']==parsed['errors']==parsed['skipped']==0
log=(OUT/'test.log').read_text()
assert lt.execution_markers(OUT/'test.log')==Counter({':calf-navigation:desktopTest':1})
for row in parsed['reports']:
 source=project/row['path'];target=OUT/'reports'/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);assert lt.sha256(target)==row['sha256']
record={'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(ROOT),'dirty_held_worktree':True,'started_utc':started,'finished_utc':finished,'command':argv,'execution':execution,'passed':passed,'selected_input_count':len(inputs),'inputs_sha256':lt.input_digest(inputs),'inputs_held':inputs==after==copied_after,'module':parsed,'driver_sha256':lt.sha256(Path(__file__)),'log_sha256':lt.sha256(OUT/'test.log'),'java_version':version,'java_executable_sha256':lt.sha256(java),'platform_native_or_consumer_tests':0,'release_readiness_certified':False,'scope':'Fresh two-method real navigation desktop work/allocation checks. Five array APIs read each bounded input once;12 finite JVM integer bulk-vs-legacy trials use actual thread allocation counters, retain content checks and restore the management flag. No wall-clock performance assertion, external-input bound, general latency/peak-memory, Native/device/consumer or release proof;726 copied inputs held, compiler caches only, old XML quarantined.'}
lt.write_json(OUT/'receipt.json',record)
print(json.dumps({'passed':passed,'execution':execution,'counts':{k:parsed[k] for k in ['tests','passed','executed','failures','errors','skipped']},'held':record['inputs_held']},indent=2),flush=True)
sys.exit(0 if passed else 1)
