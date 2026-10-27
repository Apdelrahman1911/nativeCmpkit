from pathlib import Path
import sys,hashlib,json,subprocess,os,tempfile,shutil,re
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/kgp-native-worker-parser-20261027-003';ORIGIN=ROOT/'build/kgp-native-worker-parser-20261027-002'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lib
JAVA=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java').resolve();KGP=Path('/root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-gradle-plugin/2.4.20/d64b6d447eecf2b0f6d19bdd677cae3bbce37585/kotlin-gradle-plugin-2.4.20-gradle96.jar')
origin=json.loads((ORIGIN/'receipt.json').read_bytes());origin_inputs=json.loads((ORIGIN/'inputs-before.json').read_bytes())
assert origin['compile']['result']['exit_code']==0 and origin['probe_inputs_unchanged_at_execution']
assert lib.sha256(ORIGIN/'owned-worker.kexe')==origin['binary_sha256']
assert lib.sha256(OUT/'NativeWorkerEntryProbe.kt')==lib.sha256(ORIGIN/'NativeWorkerEntryProbe.kt')==origin_inputs[str(ORIGIN/'NativeWorkerEntryProbe.kt')]
assert lib.sha256(JAVA)==origin_inputs[str(JAVA)] and lib.sha256(KGP)==origin_inputs[str(KGP)]
paths=[OUT/n for n in ['NativeWorkerEntryProbe.kt','driver.py','settings.gradle.kts','build.gradle.kts']]+[JAVA,KGP,ORIGIN/'owned-worker.kexe',ORIGIN/'receipt.json',ORIGIN/'inputs-before.json',ROOT/'gradlew',ROOT/'gradle/wrapper/gradle-wrapper.properties',ROOT/'gradle/wrapper/gradle-wrapper.jar']
inputs={str(p):lib.sha256(p) for p in paths};lib.write_json(OUT/'inputs-before.json',inputs)
source_before=lib.snapshot_inputs(ROOT);lib.write_json(OUT/'library-build-inputs-before.json',source_before)
env=os.environ.copy()
for key in ['JAVACMD','JAVA_OPTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS']:env.pop(key,None)
env['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';env['PYTHONDONTWRITEBYTECODE']='1'
version=subprocess.run([str(JAVA),'-version'],capture_output=True,env=env,check=True).stderr.decode();assert re.search(r'version "17\.',version)
record={'started_utc':lib.utc_now(),'source_revision':lib.git_revision(ROOT),'library_methods_executed':0,'ios_methods_executed':0,'release_readiness_certified':False,'java_version_output':version,'source_bound_binary_reused_from':str((ORIGIN/'receipt.json').relative_to(ROOT)),'binary_sha256':origin['binary_sha256'],'binary_bytes':origin['binary_bytes'],'compile_repeated':False,'runs':[],'scope':'Actual owned Linux Kotlin/Native2.4.20 generated-worker binary through real KGP2.4.20 KotlinNativeHostTest/TeamCity/JUnit parsing. Reuses the successfully compiled held identical-source diagnostic binary, not cached test results or fabricated reports. No UIKit/library/iOS tests or publication.'}
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-kgp-parser-reuse-',dir='/dev/shm') as temporary:
 temp=Path(temporary);env['TMPDIR']=str(temp);env['KONAN_DATA_DIR']=str(temp/'konan-data')
 project=temp/'project';project.mkdir()
 for name in ['settings.gradle.kts','build.gradle.kts']:shutil.copyfile(OUT/name,project/name)
 binary=project/'owned-worker.kexe';shutil.copyfile(ORIGIN/'owned-worker.kexe',binary);binary.chmod(0o700);assert lib.sha256(binary)==origin['binary_sha256']
 for task,expected in [('nativeWorkerPositive',0),('nativeWorkerIntentionalFailure',1)]:
  argv=[str(ROOT/'gradlew'),'-p',str(project),'--project-cache-dir',str(temp/'project-cache'),'--offline','--no-daemon','--console=plain','--no-configuration-cache','--max-workers=1','--no-parallel','--info','-Dorg.gradle.jvmargs=-Xmx1024m -Dfile.encoding=UTF-8',task]
  run=lib.execute(ROOT,argv,OUT/(task+'.log'),240,8192,env=env)
  reports=[];cases=[]
  for path in sorted((project/'build/test-results'/task).glob('TEST-*.xml')):
   payload=path.read_bytes();parsed=lib.junit_cases(payload);cases.extend(parsed)
   target=OUT/'reports'/task/path.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
   reports.append({'path':target.relative_to(OUT).as_posix(),'sha256':lib.sha256(target),'bytes':len(payload),'testcases':parsed})
  item={'task':task,'command':argv,'result':run,'expected_gradle_exit':expected,'log_sha256':lib.sha256(OUT/(task+'.log')),'reports':reports,'totals':{state:sum(c['status']==state for c in cases) for state in ['passed','failed','error','skipped']},'actual_fixture_executions':sum(c['status']!='skipped' for c in cases),'binary_unchanged':lib.sha256(binary)==record['binary_sha256']}
  record['runs'].append(item);lib.write_json(OUT/'progress.json',record);print(json.dumps(item),flush=True)
  if run.get('stop_reason') or not reports:break
 after={p:lib.sha256(Path(p)) for p in inputs};lib.write_json(OUT/'inputs-after.json',after);record['probe_inputs_unchanged_at_execution']=inputs==after
 source_after=lib.snapshot_inputs(ROOT);lib.write_json(OUT/'library-build-inputs-after.json',source_after);record['library_build_inputs_unchanged']=source_before==source_after
 record['finished_utc']=lib.utc_now();lib.write_json(OUT/'receipt.json',record)
print(json.dumps({'run_exits':[r['result']['exit_code'] for r in record['runs']],'probe_inputs_unchanged':record['probe_inputs_unchanged_at_execution'],'library_build_inputs_unchanged':record['library_build_inputs_unchanged']}),flush=True)
