from pathlib import Path
import sys,os,tempfile,subprocess,json,re,shutil
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/native-application-kgp-model-20261027-001'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
JAVA=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java').resolve()
KGP=Path('/root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-gradle-plugin/2.4.20/d64b6d447eecf2b0f6d19bdd677cae3bbce37585/kotlin-gradle-plugin-2.4.20-gradle96.jar')
paths=[OUT/'settings.gradle.kts',OUT/'build.gradle.kts',Path(__file__),JAVA,KGP,ROOT/'gradlew',ROOT/'gradle/wrapper/gradle-wrapper.jar',ROOT/'gradle/wrapper/gradle-wrapper.properties']
before={str(p):lt.sha256(p) for p in paths};lt.write_json(OUT/'inputs-before.json',before)
source=lt.snapshot_inputs(ROOT);lt.write_json(OUT/'library-inputs-before.json',source)
env=os.environ.copy()
for key in ['JAVACMD','JAVA_OPTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS']:env.pop(key,None)
env['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';env['PYTHONDONTWRITEBYTECODE']='1'
version=subprocess.run([str(JAVA),'-version'],capture_output=True,check=True,env=env).stderr.decode();assert re.search(r'version "17\.',version)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-kgp-app-model-',dir='/dev/shm') as temporary:
 temp=Path(temporary);project=temp/'project';project.mkdir();user=temp/'gradle-home';(user/'caches').mkdir(parents=True)
 (user/'wrapper').symlink_to('/root/.gradle/wrapper',target_is_directory=True)
 (user/'caches/modules-2').symlink_to('/root/.gradle/caches/modules-2',target_is_directory=True)
 env.update(GRADLE_USER_HOME=str(user),TMPDIR=str(temp),KONAN_DATA_DIR=str(temp/'konan-data'))
 for name in ['settings.gradle.kts','build.gradle.kts']:shutil.copyfile(OUT/name,project/name)
 argv=[str(ROOT/'gradlew'),'-p',str(project),'--project-cache-dir',str(temp/'project-cache'),'--offline','--no-daemon','--console=plain','--no-configuration-cache','--no-parallel','--max-workers=1','-Dorg.gradle.jvmargs=-Xmx1024m -Dfile.encoding=UTF-8', '-Pkotlin.native.home=/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20','inspectOwnedApplicationModel']
 result=lt.execute(ROOT,argv,OUT/'model.log',360,8192,env=env)
 after={p:lt.sha256(Path(p)) for p in before};lt.write_json(OUT/'inputs-after.json',after)
 source_after=lt.snapshot_inputs(ROOT);lt.write_json(OUT/'library-inputs-after.json',source_after)
 lt.write_json(OUT/'receipt.json',{'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(ROOT),'command':argv,'execution':result,'java_version':version,'log_sha256':lt.sha256(OUT/'model.log') if (OUT/'model.log').exists() else None,'inputs_unchanged':before==after,'library_inputs_unchanged':source==source_after,'library_native_ios_methods_executed':0,'apple_linking_performed':False,'release_readiness_certified':False,'scope':'Actual Linux Gradle9.7.1/JDK17/KGP2.4.20 DSL/model proof for a separate custom-entry TestExecutable sharing test compilation while default binary is unchanged, with KotlinNativeHostTest/report/env binding. Owned tmpfs Gradle project and writable DSL caches; existing downloaded module/wrapper artifacts reused without deleting any unrelated cache. No native binary linking or execution, Apple application or library behavior.'})
 print(json.dumps({'exit_code':result['exit_code'],'held_probe_inputs':before==after,'held_library_inputs':source==source_after,'executed_library_methods':0}))
