from pathlib import Path
import sys,os,tempfile,subprocess,json,re,shutil
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/native-application-helper-klib-20261027-001'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
JAVA=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java').resolve()
SOURCE=ROOT/'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt'
KGP=Path('/root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-gradle-plugin/2.4.20/d64b6d447eecf2b0f6d19bdd677cae3bbce37585/kotlin-gradle-plugin-2.4.20-gradle96.jar')
paths=[OUT/'settings.gradle.kts',OUT/'build.gradle.kts',Path(__file__),SOURCE,JAVA,KGP,ROOT/'gradlew',ROOT/'gradle/wrapper/gradle-wrapper.jar',ROOT/'gradle/wrapper/gradle-wrapper.properties']
before={str(p):lt.sha256(p) for p in paths};lt.write_json(OUT/'inputs-before.json',before)
source=lt.snapshot_inputs(ROOT);lt.write_json(OUT/'library-inputs-before.json',source)
shutil.copyfile(SOURCE,OUT/SOURCE.name)
env=os.environ.copy()
for key in ['JAVACMD','JAVA_OPTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS']:env.pop(key,None)
env['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';env['PYTHONDONTWRITEBYTECODE']='1'
version=subprocess.run([str(JAVA),'-version'],capture_output=True,check=True,env=env).stderr.decode();assert re.search(r'version "17\.',version)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-application-helper-klib-',dir='/dev/shm') as temporary:
 temp=Path(temporary);project=temp/'project';project.mkdir();user=temp/'gradle-home';(user/'caches').mkdir(parents=True)
 (user/'wrapper').symlink_to('/root/.gradle/wrapper',target_is_directory=True)
 (user/'caches/modules-2').symlink_to('/root/.gradle/caches/modules-2',target_is_directory=True)
 env.update(GRADLE_USER_HOME=str(user),TMPDIR=str(temp),KONAN_DATA_DIR=str(temp/'konan-data'))
 for name in ['settings.gradle.kts','build.gradle.kts']:shutil.copyfile(OUT/name,project/name)
 target=project/'src/iosSimulatorArm64Main/kotlin'/SOURCE.name;target.parent.mkdir(parents=True);shutil.copyfile(SOURCE,target)
 argv=[str(ROOT/'gradlew'),'-p',str(project),'--project-cache-dir',str(temp/'project-cache'),'--offline','--no-daemon','--console=plain','--no-configuration-cache','--no-parallel','--max-workers=1','-Dorg.gradle.jvmargs=-Xmx1024m -Dfile.encoding=UTF-8','-Pkotlin.compiler.execution.strategy=in-process','-Pkotlin.native.jvmArgs=-Xmx1024m','-Pkotlin.native.home=/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20','compileKotlinIosSimulatorArm64']
 result=lt.execute(ROOT,argv,OUT/'compile.log',420,8192,env=env)
 outputs=[{'path':p.relative_to(project).as_posix(),'sha256':lt.sha256(p),'bytes':p.stat().st_size} for p in sorted((project/'build/classes').rglob('*')) if p.is_file()]
 after={p:lt.sha256(Path(p)) for p in before};lt.write_json(OUT/'inputs-after.json',after)
 source_after=lt.snapshot_inputs(ROOT);lt.write_json(OUT/'library-inputs-after.json',source_after)
 lt.write_json(OUT/'receipt.json',{'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(ROOT),'command':argv,'execution':result,'java_version':version,'log_sha256':lt.sha256(OUT/'compile.log') if (OUT/'compile.log').exists() else None,'inputs_unchanged':before==after,'library_inputs_unchanged':source==source_after,'library_native_ios_methods_executed':0,'apple_linking_performed':False,'compiled_outputs':outputs,'outputs_retained':False,'release_readiness_certified':False,'scope':'Actual Linux Gradle9.7.1/JDK17/Kotlin2.4.20/Compose compiler2.4.20 iOS-simulator KLIB typechecking of the byte-identical application-host/helper source with real Compose UI/runtime1.12.0 dependencies. Test-only source is copied into an isolated compile-only main source set. No test registry execution, Apple linking/application launch, production library build or native functionality pass. All writable Gradle/build/native cache/temp outputs owned tmpfs; existing downloaded module/wrapper artifacts reused without deleting unrelated caches.'})
 print(json.dumps({'exit_code':result['exit_code'],'held_probe_inputs':before==after,'held_library_inputs':source==source_after,'compiled_output_files':len(outputs),'executed_library_methods':0}))
