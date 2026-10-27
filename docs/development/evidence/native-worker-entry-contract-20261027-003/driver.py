from pathlib import Path
import sys,hashlib,json,subprocess,os,tempfile,shutil,datetime as dt,re
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/native-worker-entry-probe-20261027-003'
sys.path.insert(0,str(ROOT/'scripts/ci'));from library_tests import execute,sha256,write_json
KONAN=Path('/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20');src=OUT/'NativeWorkerEntryProbe.kt';java=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java').resolve();jar=KONAN/'konan/lib/kotlin-native-compiler-embeddable.jar'
assert not (OUT/'receipt.json').exists()
paths=[src,Path(__file__),java,jar,KONAN/'konan/konan.properties',KONAN/'klib/common/stdlib/default/manifest']
inputs={str(p):sha256(p) for p in paths};write_json(OUT/'inputs-before.json',inputs)
env=os.environ.copy()
for variable in ['JAVACMD','JAVA_OPTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS']:env.pop(variable,None)
env['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';env['LIBCLANG_DISABLE_CRASH_RECOVERY']='1'
version=subprocess.run([str(java),'-version'],capture_output=True,env=env,check=True).stderr.decode();assert re.search(r'version "17\.',version)
write_json(OUT/'java-runtime.json',{'direct_compiler_java_executable':str(java),'java_version_output':version,'executable_sha256':sha256(java),'compiler_entry':'org.jetbrains.kotlin.cli.utilities.MainKt konanc'})
records=[]
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-worker-entry-',dir='/dev/shm') as temporary:
    temp=Path(temporary);assert shutil.disk_usage(temp).free>8*1024**3
    data=temp/'konan-data';dependencies=data/'dependencies';dependencies.mkdir(parents=True)
    original=Path('/root/.konan/dependencies')
    for name in ['x86_64-unknown-linux-gnu-gcc-8.3.0-glibc-2.19-kernel-4.9-2','libffi-3.2.1-2-linux-x86-64','lldb-4-linux']:
        shutil.copytree(original/name,dependencies/name,symlinks=True)
    shutil.copy2(original/'.extracted',dependencies/'.extracted')
    env['KONAN_DATA_DIR']=str(data);env['TMPDIR']=str(temp)
    exe=temp/'owned-worker';linktemp=temp/'linker-temporaries';linktemp.mkdir()
    command=[str(java),'-ea','-Xmx1024m','-XX:TieredStopAtLevel=1','-Dfile.encoding=UTF-8','-Dkonan.home='+str(KONAN),'-cp',str(jar),'org.jetbrains.kotlin.cli.utilities.MainKt','konanc',str(src),'-target','linux_x64','-produce','program','-o',str(exe),'-Xtemporary-files-dir='+str(linktemp),'-Xkonan-data-dir='+str(data),'-tr','-entry','nativecmpkit.probe.customMain']
    compilation=execute(ROOT,command,OUT/'compile.log',600,8192,env=env)
    record={'compile_command':command,'compile_result':compilation,'compile_log_sha256':sha256(OUT/'compile.log') if (OUT/'compile.log').exists() else None}
    binary=exe.with_suffix('.kexe')
    if compilation['exit_code']==0:
        record['binary_sha256']=sha256(binary);record['binary_size']=binary.stat().st_size
        for name,flags,expected_exit in [('worker-pass',[],0),('worker-intentional-failure',['--nativecmpkit-probe-fail'],1)]:
            args=[str(binary),'--ktest_logger=TEAMCITY',*flags]
            result=execute(ROOT,args,OUT/(name+'.log'),60,8192,env=env)
            record_run={'name':name,'command':args,'result':result,'expected_exit':expected_exit,'log_sha256':sha256(OUT/(name+'.log')) if (OUT/(name+'.log')).exists() else None}
            records.append(record_run);write_json(OUT/'progress.json',{'compile':record,'runs':records});print(json.dumps(record_run),flush=True)
    after={p:sha256(Path(p)) for p in inputs};write_json(OUT/'inputs-after.json',after)
    receipt={'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'input_bytes_unchanged':inputs==after,'compile':record,'runs':records,'library_tests_executed':0,'ios_tests_executed':0,'scope':'Actual generated Kotlin/Native worker-body and intentional-failure propagation diagnostic on Linux, not UIKit or supported-library execution. Private tmpfs dependency store/output/linker temporaries; direct verified JDK17 executable. Negative-control failure is expected and not a library defect.','preexisting_caches_deleted':False,'release_readiness_certified':False}
    write_json(OUT/'receipt.json',receipt)
    print(json.dumps({'compile_exit':compilation['exit_code'],'runtime_exits':[r['result']['exit_code'] for r in records],'input_bytes_unchanged':inputs==after}),flush=True)
