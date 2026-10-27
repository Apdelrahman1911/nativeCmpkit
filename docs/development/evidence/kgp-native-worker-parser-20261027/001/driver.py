from pathlib import Path
import sys,hashlib,json,subprocess,os,tempfile,shutil,datetime as dt,re
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/kgp-native-worker-parser-20261027-001'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lib
KONAN=Path('/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20');java=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java').resolve();jar=KONAN/'konan/lib/kotlin-native-compiler-embeddable.jar';kgp=Path('/root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-gradle-plugin/2.4.20/d64b6d447eecf2b0f6d19bdd677cae3bbce37585/kotlin-gradle-plugin-2.4.20-gradle96.jar')
assert not (OUT/'receipt.json').exists()
paths=[OUT/n for n in ['NativeWorkerEntryProbe.kt','driver.py','settings.gradle.kts','build.gradle.kts']]+[java,jar,kgp,KONAN/'konan/konan.properties',KONAN/'klib/common/stdlib/default/manifest',ROOT/'gradlew',ROOT/'gradle/wrapper/gradle-wrapper.properties',ROOT/'gradle/wrapper/gradle-wrapper.jar']
inputs={str(p):lib.sha256(p) for p in paths};lib.write_json(OUT/'inputs-before.json',inputs)
source_before=lib.snapshot_inputs(ROOT);lib.write_json(OUT/'library-build-inputs-before.json',source_before)
env=os.environ.copy()
for key in ['JAVACMD','JAVA_OPTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS']:env.pop(key,None)
env['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';env['LIBCLANG_DISABLE_CRASH_RECOVERY']='1';env['PYTHONDONTWRITEBYTECODE']='1'
version=subprocess.run([str(java),'-version'],capture_output=True,env=env,check=True).stderr.decode();assert re.search(r'version "17\.',version)
started=lib.utc_now();record={'started_utc':started,'source_revision':lib.git_revision(ROOT),'library_methods_executed':0,'ios_methods_executed':0,'release_readiness_certified':False,'java_executable':str(java),'java_executable_sha256':lib.sha256(java),'java_version_output':version,'scope':'Actual Linux native generated-worker positive/intentional-failure runs through real KGP2.4.20 KotlinNativeHostTest/TeamCity/JUnit parsing. A diagnostic, not UIKit/application/library behavior, ABI or release evidence. Owned tmpfs dependency/project/output only, with preserved logs/XML; no native package publication.'}
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-kgp-native-parser-',dir='/dev/shm') as temporary:
 temp=Path(temporary);assert shutil.disk_usage(temp).free>8*1024**3
 data=temp/'konan-data';dependencies=data/'dependencies';dependencies.mkdir(parents=True);original=Path('/root/.konan/dependencies')
 for name in ['x86_64-unknown-linux-gnu-gcc-8.3.0-glibc-2.19-kernel-4.9-2','libffi-3.2.1-2-linux-x86-64','lldb-4-linux']:
  shutil.copytree(original/name,dependencies/name,symlinks=True)
 shutil.copy2(original/'.extracted',dependencies/'.extracted')
 env['KONAN_DATA_DIR']=str(data);env['TMPDIR']=str(temp)
 project=temp/'project';project.mkdir()
 for name in ['settings.gradle.kts','build.gradle.kts']:shutil.copyfile(OUT/name,project/name)
 binary=project/'owned-worker.kexe';linktemp=temp/'linker-temporaries';linktemp.mkdir()
 command=[str(java),'-ea','-Xmx1024m','-XX:TieredStopAtLevel=1','-Dfile.encoding=UTF-8','-Dkonan.home='+str(KONAN),'-cp',str(jar),'org.jetbrains.kotlin.cli.utilities.MainKt','konanc',str(OUT/'NativeWorkerEntryProbe.kt'),'-target','linux_x64','-produce','program','-o',str(binary),'-Xtemporary-files-dir='+str(linktemp),'-Xkonan-data-dir='+str(data),'-tr','-entry','nativecmpkit.probe.customMain']
 compilation=lib.execute(ROOT,command,OUT/'compile.log',600,8192,env=env)
 record['compile']={'command':command,'result':compilation,'log_sha256':lib.sha256(OUT/'compile.log')}
 record['runs']=[]
 if compilation['exit_code']==0:
  record['binary_sha256']=lib.sha256(binary);record['binary_bytes']=binary.stat().st_size
  for task,expected in [('nativeWorkerPositive',0),('nativeWorkerIntentionalFailure',1)]:
   argv=[str(ROOT/'gradlew'),'-p',str(project),'--project-cache-dir',str(temp/'project-cache'),'--offline','--no-daemon','--console=plain','--no-configuration-cache','--max-workers=1','--no-parallel','--info','-Dorg.gradle.jvmargs=-Xmx1024m -Dfile.encoding=UTF-8',task]
   run=lib.execute(ROOT,argv,OUT/(task+'.log'),300,8192,env=env)
   reports=[];cases=[]
   for path in sorted((project/'build/test-results'/task).glob('TEST-*.xml')):
    payload=path.read_bytes();parsed=lib.junit_cases(payload);cases.extend(parsed)
    target=OUT/'reports'/task/path.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    reports.append({'path':target.relative_to(OUT).as_posix(),'sha256':lib.sha256(target),'bytes':len(payload),'testcases':parsed})
   item={'task':task,'command':argv,'result':run,'expected_gradle_exit':expected,'log_sha256':lib.sha256(OUT/(task+'.log')),'reports':reports,'totals':{state:sum(c['status']==state for c in cases) for state in ['passed','failed','error','skipped']},'actual_fixture_executions':sum(c['status']!='skipped' for c in cases),'binary_unchanged':lib.sha256(binary)==record['binary_sha256']}
   record['runs'].append(item);lib.write_json(OUT/'progress.json',record);print(json.dumps(item),flush=True)
   if run.get('stop_reason'):break
 record['probe_inputs_unchanged_at_execution']={p:lib.sha256(Path(p)) for p in inputs}==inputs
 lib.write_json(OUT/'inputs-after.json',{p:lib.sha256(Path(p)) for p in inputs})
 source_after=lib.snapshot_inputs(ROOT);lib.write_json(OUT/'library-build-inputs-after.json',source_after);record['library_build_inputs_unchanged']=source_before==source_after
 record['owned_temporary_tree_cleaned_on_with_exit']=True
 record['finished_utc']=lib.utc_now();lib.write_json(OUT/'receipt.json',record)
print(json.dumps({'compile_exit':compilation['exit_code'],'run_exits':[r['result']['exit_code'] for r in record['runs']],'probe_inputs_unchanged':record['probe_inputs_unchanged_at_execution'],'library_build_inputs_unchanged':record['library_build_inputs_unchanged']}),flush=True)
