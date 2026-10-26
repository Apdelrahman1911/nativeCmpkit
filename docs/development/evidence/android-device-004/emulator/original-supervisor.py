from pathlib import Path
import datetime as dt,json,hashlib,os,signal,socket,subprocess,time,shutil
root=Path('/root/projects/nativeCmpKit');out=root/'build/android-emulator/runtime-002';out.mkdir(mode=0o700)
sdk=Path('/opt/android-sdk');adb=sdk/'platform-tools/adb';avdhome=root/'build/android-emulator/avds';serial='emulator-5584'
cmd=[str(sdk/'emulator/emulator'),'-avd','nativecmpkit_verification_api35','-port','5584','-accel','off','-no-window','-no-audio','-no-boot-anim','-no-snapshot','-read-only','-gpu','swiftshader','-feature','-Vulkan','-camera-back','none','-camera-front','none','-memory','1536','-cores','1','-skin','480x800','-dpi-device','160']
env={'PATH':str(sdk/'platform-tools')+':/usr/bin:/bin','HOME':'/root','ANDROID_HOME':str(sdk),'ANDROID_SDK_ROOT':str(sdk),'ANDROID_AVD_HOME':str(avdhome),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
reserve=8192*1024*1024;deadline=time.monotonic()+1800;bootdeadline=time.monotonic()+600
assert shutil.disk_usage(root).free>=reserve
assert (avdhome/'nativecmpkit_verification_api35.ini').is_file()
assert f'path={avdhome}/nativecmpkit_verification_api35.avd' in (avdhome/'nativecmpkit_verification_api35.ini').read_text()
for port in [5584,5585]:
 with socket.socket() as s:
  s.settimeout(.5);assert s.connect_ex(('127.0.0.1',port))!=0,'Emulator port already in use'
existing=subprocess.run([str(adb),'devices'],text=True,capture_output=True,timeout=20,env=env,check=True)
assert not any(line.startswith(serial+'\t') for line in existing.stdout.splitlines())
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def write(name,obj):
 p=out/name;temp=out/(name+'.tmp');temp.write_text(json.dumps(obj,indent=2)+'\n');temp.replace(p)
def ticks(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
def query(*args):
 p=subprocess.run([str(adb),'-s',serial,'shell',*args],capture_output=True,text=True,timeout=20,env=env)
 return p.stdout.strip() if p.returncode==0 else None
record={'started_utc':utc(),'command':cmd,'cwd':str(root),'serial':serial,'owned_avd_home':str(avdhome),'limits':{'boot_seconds':600,'total_seconds':1800,'disk_reserve_mib':8192,'guest_memory_mib':1536,'guest_cores':1},'scope':'Task-owned read-only/no-snapshot software emulator; boot is not test evidence. No SELinux/security setting changes, physical devices, old PIDs or unrelated process groups used.','source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'system_image_properties_sha256':hashlib.sha256((sdk/'system-images/android-35/default/x86_64/source.properties').read_bytes()).hexdigest(),'emulator_binary_sha256':hashlib.sha256((sdk/'emulator/emulator').read_bytes()).hexdigest(),'controller_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
proc=None;start=None;reason='unknown';ready=False
try:
 with (out/'boot.raw.log').open('xb') as raw:
  proc=subprocess.Popen(cmd,cwd=root,env=env,stdout=raw,stderr=subprocess.STDOUT,start_new_session=True)
  start=ticks(proc.pid);assert start is not None
  record.update(pid=proc.pid,process_group=os.getpgid(proc.pid),process_start_ticks=start)
  write('launch.json',record);print('Owned emulator started; serial='+serial+' pid='+str(proc.pid),flush=True)
  while True:
   if proc.poll() is not None:reason='emulator exited '+str(proc.returncode);break
   if shutil.disk_usage(root).free<reserve:reason='disk reserve';break
   if (out/'stop-requested').exists():reason='lead requested task-owned cleanup';break
   if time.monotonic()>deadline:reason='total runtime bound';break
   if not ready:
    if time.monotonic()>bootdeadline:reason='boot timeout';break
    try:boot=query('getprop','sys.boot_completed')
    except subprocess.TimeoutExpired:boot=None
    if boot=='1':
     props={k:query('getprop',v) for k,v in [('api','ro.build.version.sdk'),('release','ro.build.version.release'),('abi','ro.product.cpu.abi'),('boot','sys.boot_completed')]}
     enforcing=query('getenforce')
     assert props['api']=='35' and props['abi']=='x86_64' and enforcing=='Enforcing'
     ready=True;write('boot-ready.json',{'observed_utc':utc(),'serial':serial,'properties':props,'selinux':enforcing,'source_launch':'launch.json','tests_executed':0,'scope':'Readiness/runtime identity only; cameras disabled; no native functionality claim.'})
     print('Owned emulator booted API35 x86_64; SELinux Enforcing; zero tests yet.',flush=True)
   time.sleep(4)
except BaseException as e:
 reason='controller '+type(e).__name__;raise
finally:
 actions=[]
 if proc is not None and proc.poll() is None:
  if ticks(proc.pid)==start and os.getpgid(proc.pid)==proc.pid:
   os.killpg(proc.pid,signal.SIGTERM);actions.append('SIGTERM owned process group')
   try:proc.wait(timeout=15)
   except subprocess.TimeoutExpired:
    if ticks(proc.pid)==start:
     os.killpg(proc.pid,signal.SIGKILL);actions.append('SIGKILL same owned process group after15s')
    proc.wait(timeout=15)
  else:actions.append('ownership mismatch; no signal sent')
 write('completion.json',{'completed_utc':utc(),'reason':reason,'booted':ready,'cleanup_actions':actions,'child_exit_code':proc.poll() if proc else None,'original_pid_still_same':ticks(proc.pid)==start if proc and start else False,'tests_claimed':0})
 print('Emulator controller finished: '+reason+'; '+','.join(actions),flush=True)
