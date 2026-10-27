from pathlib import Path
import sys,os,tempfile,json,subprocess,hashlib,re,datetime as dt
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/uikit-application-bindings-20261027-001';KONAN=Path('/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20');JAVA=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java').resolve()
sys.path.insert(0,str(ROOT/'scripts/ci'));from library_tests import execute,sha256,write_json
source=OUT/'UIKitApplicationProbe.kt';jar=KONAN/'konan/lib/kotlin-native-compiler-embeddable.jar';paths=[source,Path(__file__),JAVA,jar,KONAN/'konan/konan.properties',KONAN/'klib/common/stdlib/default/manifest']
inputs={str(p):sha256(p) for p in paths};write_json(OUT/'inputs-before.json',inputs)
env=os.environ.copy()
for key in ['JAVACMD','JAVA_OPTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS']:env.pop(key,None)
env['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';env['LIBCLANG_DISABLE_CRASH_RECOVERY']='1'
version=subprocess.run([str(JAVA),'-version'],env=env,capture_output=True,check=True).stderr.decode();assert re.search(r'version "17\.',version)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-uikit-bindings-',dir='/dev/shm') as temporary:
 temp=Path(temporary);env['KONAN_DATA_DIR']=str(temp/'konan-data');env['TMPDIR']=str(temp)
 command=[str(JAVA),'-ea','-Xmx1024m','-XX:TieredStopAtLevel=1','-Dfile.encoding=UTF-8','-Dkonan.home='+str(KONAN),'-cp',str(jar),'org.jetbrains.kotlin.cli.utilities.MainKt','konanc',str(source),'-target','ios_simulator_arm64','-produce','library','-o',str(temp/'probe')]
 execution=execute(ROOT,command,OUT/'compile.log',300,8192,env=env)
 output=temp/'probe.klib';after={p:sha256(Path(p)) for p in inputs};write_json(OUT/'inputs-after.json',after)
 write_json(OUT/'receipt.json',{'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'command':command,'execution':execution,'compile_log_sha256':sha256(OUT/'compile.log') if (OUT/'compile.log').exists() else None,'output_sha256':sha256(output) if output.exists() else None,'output_bytes':output.stat().st_size if output.exists() else None,'input_bytes_unchanged':inputs==after,'java_executable':str(JAVA),'java_version_output':version,'ios_runtime_methods_executed':0,'library_methods_executed':0,'apple_linking_performed':False,'release_readiness_certified':False,'scope':'Actual Linux Kotlin/Native2.4.20 iOS-simulator KLIB binding/lowering diagnostic for a test-only UIKit delegate/main/worker/teardown entry. No Apple linking, application install/launch or executed UIKit/library behavior; owned tmpfs output only.'})
 print(json.dumps({'exit_code':execution['exit_code'],'input_bytes_unchanged':inputs==after,'ios_methods_executed':0,'log':str(OUT/'compile.log')}))
