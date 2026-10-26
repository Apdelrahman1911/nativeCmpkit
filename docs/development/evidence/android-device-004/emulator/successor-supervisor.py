from pathlib import Path
import datetime as dt,json,hashlib,os,signal,subprocess,time,shutil
root=Path('/root/projects/nativeCmpKit');out=root/'build/android-emulator/runtime-002';launch=json.loads((out/'launch.json').read_text());adb='/opt/android-sdk/platform-tools/adb';serial=launch['serial'];child=launch['pid']
def identity(pid):
 stat=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();return {'pid':pid,'ppid':int(stat[1]),'ticks':stat[19],'cwd':str(Path(f'/proc/{pid}/cwd').resolve()),'command':Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')}
owned=identity(child);assert owned['ticks']==launch['process_start_ticks']
parent=owned['ppid'];controller=identity(parent)
assert b'/tmp/nativecmpkit-emulator-runtime002.py' in controller['command'] and controller['cwd']==str(root)
assert hashlib.sha256(Path('/tmp/nativecmpkit-emulator-runtime002.py').read_bytes()).hexdigest()==launch['controller_sha256']
assert not (out/'completion.json').exists() and not (out/'boot-ready.json').exists()
assert time.time()-dt.datetime.fromisoformat(launch['started_utc']).timestamp()<590
expected_parent=controller['ticks'];expected_child=owned['ticks'];assert os.getpgid(child)==child
for sig in [signal.SIGINT,signal.SIGTERM]:
 signal.signal(sig,lambda s,f: (_ for _ in ()).throw(KeyboardInterrupt()))
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def write(name,o):
 p=out/name;temp=out/(name+'.tmp');temp.write_text(json.dumps(o,indent=2)+'\n');temp.replace(p)
def matches(pid,ticks):
 try:return identity(pid)['ticks']==ticks
 except FileNotFoundError:return False
record={'observed_utc':utc(),'operation':'Lead-supervised bounded handoff of this task-owned watchdog only; preserve the already-running read-only emulator, no security/AVD changes.','reason':'Archived prior API35 software boot took~22min; original600s bound was insufficient. Extend once rather than discard current boot/restart.','original_launch_sha256':hashlib.sha256((out/'launch.json').read_bytes()).hexdigest(),'original_controller_pid':parent,'original_controller_start_ticks':expected_parent,'owned_emulator_pid':child,'owned_emulator_start_ticks':expected_child,'new_controller_pid':os.getpid(),'extension_boot_seconds':1500,'extension_total_seconds':2400,'reserve_mib':8192,'controller_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'No tests counted at handoff. Original controller is paused only while bounded successor monitors same verified child, and resumed for ownership-checked cleanup.'}
write('supervised-extension.json',record)
paused=False;ready=False;reason='unknown';begun=time.monotonic();last_error=None
try:
 os.kill(parent,signal.SIGSTOP);paused=True
 assert matches(child,expected_child) and matches(parent,expected_parent)
 print('Bounded emulator watchdog handoff established; existing boot preserved.',flush=True)
 while True:
  if not matches(child,expected_child):reason='owned emulator ended';break
  if not matches(parent,expected_parent):reason='original watchdog ended';break
  if (out/'stop-requested').exists():reason='lead requested cleanup';break
  if shutil.disk_usage(root).free<8192*1024*1024:reason='disk reserve';break
  elapsed=time.monotonic()-begun
  if elapsed>2400:reason='extended total bound';break
  if not ready:
   if elapsed>1500:reason='extended boot bound';break
   try:
    p=subprocess.run([adb,'-s',serial,'shell','getprop','sys.boot_completed'],capture_output=True,text=True,timeout=20)
    if p.returncode==0 and p.stdout.strip()=='1':
     props={}
     for k,c in [('api',['getprop','ro.build.version.sdk']),('abi',['getprop','ro.product.cpu.abi']),('selinux',['getenforce'])]:
      q=subprocess.run([adb,'-s',serial,'shell',*c],capture_output=True,text=True,timeout=20,check=True);props[k]=q.stdout.strip()
     assert props=={'api':'35','abi':'x86_64','selinux':'Enforcing'}
     ready=True;write('extended-boot-ready.json',{'observed_utc':utc(),'serial':serial,'properties':props,'tests_executed':0,'origin':'Same task-owned read-only software emulator; original watchdog paused, bounded successor active.','extension':'supervised-extension.json','scope':'Boot/readiness only; no native-function/test result.'})
     print('Task-owned API35 emulator booted; SELinux Enforcing; zero tests claimed.',flush=True)
   except subprocess.TimeoutExpired:last_error='readiness query timed out; no success inferred'
  time.sleep(4)
finally:
 cleanup=[]
 (out/'stop-requested').touch(exist_ok=True)
 if paused and matches(parent,expected_parent):
  os.kill(parent,signal.SIGCONT);cleanup.append('resumed verified original watchdog for its own cleanup')
  for _ in range(35):
   if (out/'completion.json').exists() and not matches(child,expected_child):break
   time.sleep(1)
 if matches(child,expected_child) and os.getpgid(child)==child:
  os.killpg(child,signal.SIGTERM);cleanup.append('SIGTERM same verified emulator process group after watchdog wait')
  for _ in range(15):
   if not matches(child,expected_child):break
   time.sleep(1)
  if matches(child,expected_child):os.killpg(child,signal.SIGKILL);cleanup.append('SIGKILL same verified group after15s')
 write('extension-completion.json',{'observed_utc':utc(),'reason':reason,'booted_in_successor':ready,'last_readiness_error':last_error,'cleanup':cleanup,'same_emulator_pid_remaining':matches(child,expected_child),'same_original_controller_pid_remaining':matches(parent,expected_parent),'tests_claimed':0})
 print('Extended emulator supervisor completed: '+reason,flush=True)
