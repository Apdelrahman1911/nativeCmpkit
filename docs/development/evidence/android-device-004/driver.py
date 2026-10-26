from pathlib import Path
import datetime as dt,json,hashlib,sys,subprocess,os,shutil,re
root=Path('/root/projects/nativeCmpKit');sys.path.insert(0,str(root/'scripts/ci'));import library_tests as lt
out=root/'build/ci-verification/android-device-004';assert not out.exists();out.mkdir(parents=True)
launch=json.loads((root/'build/android-emulator/runtime-002/launch.json').read_text());extension=json.loads((root/'build/android-emulator/runtime-002/supervised-extension.json').read_text())
raw=Path(f"/proc/{launch['pid']}/stat").read_text().rsplit(')',1)[1].split();assert raw[19]==launch['process_start_ticks'];assert os.getpgid(launch['pid'])==launch['pid'];assert int(raw[1])==extension['original_controller_pid']
assert not (root/'build/android-emulator/runtime-002/stop-requested').exists()
now=dt.datetime.now(dt.timezone.utc);deadline=dt.datetime.fromisoformat(extension['observed_utc'])+dt.timedelta(seconds=extension['extension_total_seconds']);assert (deadline-now).total_seconds()>990
serial=launch['serial'];adb='/opt/android-sdk/platform-tools/adb';runtime={}
for k,args in [('boot',['getprop','sys.boot_completed']),('api',['getprop','ro.build.version.sdk']),('abi',['getprop','ro.product.cpu.abi']),('selinux',['getenforce'])]:
 p=subprocess.run([adb,'-s',serial,'shell',*args],capture_output=True,text=True,timeout=20,check=True);runtime[k]=p.stdout.strip()
assert runtime=={'boot':'1','api':'35','abi':'x86_64','selinux':'Enforcing'}
def put(n,o):(out/n).write_text(json.dumps(o,indent=2)+'\n')
before=lt.snapshot_inputs(root);put('inputs-before.json',before)
put('runtime.json',{'observed_utc':now.isoformat(),'serial':serial,'properties':runtime,'emulator_launch_sha256':lt.sha256(root/'build/android-emulator/runtime-002/launch.json'),'extension_sha256':lt.sha256(root/'build/android-emulator/runtime-002/supervised-extension.json'),'scope':'Task-owned API35 x86_64 software emulator; no security or SELinux changes. Actual IO/picker device tests requested; boot is not a test.'})
old=[]
for module in ['calf-io','calf-file-picker']:
 report=root/module/'build/outputs/androidTest-results/connected/androidMain'
 if report.exists():
  assert not report.is_symlink();dest=out/'previous-reports'/module;dest.parent.mkdir(parents=True,exist_ok=True)
  for p in sorted(report.rglob('*')):
   if p.is_file():old.append({'path':str(p.relative_to(root)),'sha256':lt.sha256(p)})
  shutil.move(str(report),str(dest))
put('previous-reports.json',old)
cmd=['./gradlew',':calf-io:connectedAndroidDeviceTest','--rerun',':calf-file-picker:connectedAndroidDeviceTest','--rerun','-Pandroid.injected.device.serial='+serial,'--console=plain','--continue','--max-workers=2','--no-parallel','--no-configuration-cache','--no-build-cache']
put('plan.json',{'command':cmd,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'source_tree_dirty':True,'modules':['calf-io','calf-file-picker'],'expected_tests':{'calf-io':17,'calf-file-picker':25},'unchanged_known_limitation':'actualHardLinkIsNotTruncatedOrDeleted still requires Os.link in untrusted app; prior SELinux-denied setup retained, not skipped or replaced.','timeout_seconds':840,'reserve_mib':8192,'controller_sha256':lt.sha256(Path(__file__))})
env=os.environ.copy();env.update(JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64',ANDROID_HOME='/opt/android-sdk',ANDROID_SDK_ROOT='/opt/android-sdk',ANDROID_SERIAL=serial);env['PATH']=env['JAVA_HOME']+'/bin:/root/.cargo/bin:'+env['PATH']
print('Starting bounded fresh IO+picker device diagnostics; expected42 cases, unchanged hardlink setup limitation.',flush=True)
r=subprocess.run([sys.executable,str(root/'scripts/audit/run_bounded_build.py'),'--log',str(out/'gradle.log'),'--timeout','840','--reserve-mib','8192','--',*cmd],cwd=root,env=env)
after=lt.snapshot_inputs(root);put('inputs-after.json',after)
changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
put('collection.json',{'finished_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'guard_exit':r.returncode,'input_count':len(before),'changed_inputs':changed,'unchanged':before==after,'scope':'Raw diagnostic collection only. Actual fresh XML and failures must be independently inspected before any pass claim.'})
print(json.dumps({'guard_exit':r.returncode,'input_count':len(before),'changed_inputs':changed,'output':str(out.relative_to(root))}),flush=True)
sys.exit(r.returncode or (2 if changed else 0))
