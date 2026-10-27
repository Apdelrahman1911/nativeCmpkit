from pathlib import Path
import sys,hashlib,json,subprocess,os,tempfile,shutil,datetime as dt
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/apple-entry-probe-20261027-001'
sys.path.insert(0,str(ROOT/'scripts/ci'));from library_tests import execute,sha256,write_json
KONAN=Path('/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20');src=OUT/'NativeEntryProbe.kt'
assert not (OUT/'receipt.json').exists()
inputs={str(p):sha256(p) for p in [src,KONAN/'bin/konanc',KONAN/'konan/konan.properties',KONAN/'klib/common/stdlib/default/manifest']}
write_json(OUT/'inputs-before.json',inputs)
env=os.environ.copy();env['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';env['JAVA_OPTS']='-Xmx1024m';records=[]
with tempfile.TemporaryDirectory(prefix='nativecmpkit-entry-probe-',dir='/dev/shm') as temporary:
    temp=Path(temporary);assert shutil.disk_usage(temp).free>4*1024**3
    env['TMPDIR']=str(temp)
    for name,flags in [('tr-custom',['-tr','-entry','nativecmpkit.probe.customMain']),('trn-custom',['-trn','-entry','nativecmpkit.probe.customMain']),('trw-custom',['-trw','-entry','nativecmpkit.probe.customMain'])]:
        compiled=temp/name;temporary_files=temp/(name+'-temp');temporary_files.mkdir()
        cmd=[str(KONAN/'bin/konanc'),str(src),'-target','linux_x64','-produce','program','-o',str(compiled),'-Xtemporary-files-dir='+str(temporary_files),*flags]
        compile_result=execute(ROOT,cmd,OUT/(name+'-compile.log'),600,8192,env=env)
        rec={'name':name,'compile_command':cmd,'compile_result':compile_result,'compile_log_sha256':sha256(OUT/(name+'-compile.log'))}
        exe=compiled.with_suffix('.kexe')
        if compile_result['exit_code']==0:
            rec['binary_sha256']=sha256(exe);rec['binary_size']=exe.stat().st_size
            rec['runtime_command']=[str(exe),'--ktest_logger=GTEST']
            rec['runtime_result']=execute(ROOT,rec['runtime_command'],OUT/(name+'-runtime.log'),60,8192,env=env)
            rec['runtime_log_sha256']=sha256(OUT/(name+'-runtime.log'))
        records.append(rec);write_json(OUT/'progress.json',{'attempts':records})
        print(json.dumps(rec),flush=True)
after={p:sha256(Path(p)) for p in inputs};write_json(OUT/'inputs-after.json',after)
write_json(OUT/'receipt.json',{'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'input_bytes_unchanged':inputs==after,'attempts':records,'library_tests_executed':0,'scope':'Actual Linux Kotlin/Native2.4.20 custom-entry/generated-runner diagnostic; zero iOS or library behavior tests. Outputs/temporary linker files used only owned tmpfs; no dependency/cache cleanup.','release_readiness_certified':False})
