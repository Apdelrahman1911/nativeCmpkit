"""One real old-controller timeout diagnostic, with separately pinned owned cleanup.

No global PID scan or arbitrary receipt-PID signaling. This dedicated Python
parent uses a temporary subreaper lease only to reap its exact pinned daemon if
its known client/controller exits first. This is not an observer workaround.
"""
from pathlib import Path
import ctypes,datetime as dt,hashlib,json,os,select,shutil,signal,subprocess,sys,time
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/dependencies'))
import integrity as d, integrity_model as m, gradle_fixtures as f, runtime_witness as w
JDK=Path('/usr/lib/jvm/java-17-openjdk-amd64');GRADLE=Path('/opt/gradle/gradle-9.7.1')
WORK=OUT/'project'
def put(name,obj):
 with (OUT/name).open('x') as stream:stream.write(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def ready(fd):return bool(select.select([fd],[],[],0)[0])
inputs={**w.checkpoint_files(),**{'scripts/dependencies/'+n:h for n,h in w.observer_files().items()},'scripts/dependencies/checkpoint-offline-008.json':w.CHECKPOINT_SHA256}
assert all(shutil.disk_usage(p).free>=8192*1024**2 for p in [ROOT,OUT])
put('inputs-before.json',inputs)
for name in inputs:
 target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
d._new_workspace_path(WORK);WORK.mkdir()
for source in d.TOOL_DIRECTORY.iterdir():
 if source.is_file() and source.suffix in {'.py','.gradle','.md'}:f.put(WORK,'scripts/dependencies/'+source.name,source.read_bytes())
f.put(WORK,'settings.gradle',b'rootProject.name = "nativecmpkit-dependency-fixture"\n')
hold='''
// Deterministic finite task-graph hold. No plugin, compiler, native or package work.
gradle.taskGraph.whenReady { graph ->
    if (!graph.hasTask(":nativeCmpkitDependencyGraph")) throw new GradleException("Unexpected owned task")
    def target = file("build/dependency-integrity/bootstrap/owned-cancel-ready.json")
    target.parentFile.mkdirs()
    target.text = groovy.json.JsonOutput.toJson([record_type: "owned-cancellation-hold", pid: ProcessHandle.current().pid(), hold_milliseconds: 60000])
    Thread.sleep(60000)
}
'''
f.put(WORK,'build.gradle',(f.BASE_BUILD+hold).encode())
for module,version in [('parent','1.0'),('leaf','1.0'),('extra','1.0')]:
 for name,raw in f.artifact_files(module,version).items():f.put(WORK,name,raw)
f.put(WORK,f'repo/{f.GROUP_DIRECTORY}/leaf/maven-metadata.xml',f.version_metadata(['1.0']))
f.put(WORK,'gradle/verification-metadata.xml',m.metadata_bytes(f.known_metadata()))
marker=f.write_marker(WORK);put('marker-before.json',marker)
suite_source=f'''from pathlib import Path
import json,os,sys
sys.path.insert(0,{str(ROOT/'scripts/dependencies')!r})
import integrity as d
os.environ['JAVA_HOME']={str(JDK)!r}
result=d.run(Path({str(WORK)!r}),entry_root='.',run_id='bootstrap',mode='bootstrap',timeout=20,reserve_mib=8192,gradle_home=Path({str(GRADLE)!r}),fresh_cache=True)
Path({str(OUT/'old-controller-result.json')!r}).write_text(json.dumps(result,indent=2,sort_keys=True)+'\\n')
'''
(OUT/'suite.py').write_text(suite_source)
libc=ctypes.CDLL(None,use_errno=True);previous=ctypes.c_int();assert libc.prctl(37,ctypes.byref(previous),0,0,0)==0
assert previous.value in [0,1] and libc.prctl(36,1,0,0,0)==0
begin=time.monotonic();suite=None;client_fd=daemon_fd=None;client=daemon=None;scope={};cleanup={};minimum={str(p):shutil.disk_usage(p).free for p in [ROOT,OUT]}
try:
 with (OUT/'suite-stdout.log').open('xb') as output:
  suite=subprocess.Popen([sys.executable,'-B',str(OUT/'suite.py')],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  put('suite-launch.json',{'pid':suite.pid,'parent_pid':os.getpid(),'command':[sys.executable,'-B',str(OUT/'suite.py')],'temporary_subreaper_previous':previous.value,'temporary_subreaper_enabled':True,'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()})
  while suite.poll() is None:
   for p in [ROOT,OUT]:
    free=shutil.disk_usage(p).free;minimum[str(p)]=min(minimum[str(p)],free)
    if free<8192*1024**2:raise OSError('Root/tmpfs disk reserve reached')
   if time.monotonic()-begin>50:raise TimeoutError('Dedicated old-controller slot exceeded safe deadline')
   launch=WORK/'build/dependency-integrity/bootstrap/launched-process.json';runtime=WORK/'build/dependency-integrity/bootstrap/graphs/root/runtime.json';stamp=WORK/'build/dependency-integrity/bootstrap/owned-cancel-ready.json'
   if daemon_fd is None and launch.is_file() and runtime.is_file() and stamp.is_file():
    launched=w.checked_json(launch);value,raw_hash=w.checked_json_digest(runtime);pid=w.runtime_candidate_pid(value,marker,'bootstrap')
    parent=w.identity(suite.pid);assert parent.parent==os.getpid()
    candidate=w.check_java(launched['pid'],role='client',workspace=WORK,marker=marker,mode='bootstrap',jdk_home=JDK,gradle_home=GRADLE,suite=parent,client=None)
    cfd=os.pidfd_open(candidate.pid)
    try:
     assert not ready(cfd) and w.identity(candidate.pid)==candidate
     child=w.check_java(pid,role='daemon',workspace=WORK,marker=marker,mode='bootstrap',jdk_home=JDK,gradle_home=GRADLE,suite=parent,client=candidate)
     hfd=os.pidfd_open(child.pid)
     try:
      assert not ready(hfd) and w.check_java(child.pid,role='daemon',workspace=WORK,marker=marker,mode='bootstrap',jdk_home=JDK,gradle_home=GRADLE,suite=parent,client=candidate)==child
      child_stamp=w.checked_json(stamp);assert child_stamp=={'record_type':'owned-cancellation-hold','pid':child.pid,'hold_milliseconds':60000}
      daemon_fd=hfd;client_fd=cfd;client=candidate;daemon=child
      scope={'client':client.public(),'daemon':daemon.public(),'runtime_receipt_sha256':raw_hash,'exact_live_parent_command_uid_jdk_cwd_environment_verified_before_pin':True,'both_pidfds_live_after_revalidation':True,'daemon_owns_separate_group_session':daemon.pid==daemon.group==daemon.session and daemon.group!=client.group,'hold_ready':True}
      put('live-owned-scope.json',scope)
     finally:
      if daemon_fd is None:os.close(hfd)
    finally:
     if client_fd is None:os.close(cfd)
   time.sleep(.05)
  code=suite.wait();put('suite-completion.json',{'exit_code':code,'elapsed_seconds':round(time.monotonic()-begin,3)})
  assert code==0 and daemon_fd is not None,'No complete pinned owner scope; do not infer cleanup'
  result=json.loads((OUT/'old-controller-result.json').read_text());assert result['execution']['reason']=='timeout'
  outcome={'old_controller_execution':result['execution'],'exact_pinned_daemon_alive_after_original_controller_returns':not ready(daemon_fd),'exact_pinned_client_exited':ready(client_fd),'source_scope':scope,'minimum_free_bytes':minimum,'actual_gradle_invocations':1,'jcmd_attempts':0,'library_native_or_packaged_consumer_methods_executed':0,'release_readiness_certified':False}
  put('red-observation.json',outcome)
finally:
 if suite is not None and suite.poll() is None:
  suite.send_signal(signal.SIGINT);suite.wait(timeout=15)
 if daemon_fd is not None:
  if not ready(daemon_fd):
   now=w.identity(daemon.pid)
   assert (now.pid,now.group,now.session,now.start_ticks)==(daemon.pid,daemon.group,daemon.session,daemon.start_ticks)
   assert now.parent in [client.pid,suite.pid,os.getpid()]
   assert Path(os.readlink(f'/proc/{now.pid}/exe'))==JDK/'bin/java'
   w.daemon_entrypoint(w.fields(w.proc_bytes(now.pid,'cmdline')),GRADLE,WORK)
   w.check_environment(w.environment(w.proc_bytes(now.pid,'environ')),WORK,JDK)
   signal.pidfd_send_signal(daemon_fd,signal.SIGTERM);cleanup['separately_pinned_daemon_term_sent']=True
   limit=time.monotonic()+10
   while not ready(daemon_fd) and time.monotonic()<limit:time.sleep(.05)
   if not ready(daemon_fd):
    signal.pidfd_send_signal(daemon_fd,signal.SIGKILL);cleanup['same_pinned_daemon_kill_sent']=True
    assert select.select([daemon_fd],[],[],10)[0]
  cleanup['pinned_daemon_exited']=ready(daemon_fd)
  try:
   pid,status=os.waitpid(daemon.pid,0);assert pid==daemon.pid
   cleanup['exact_adopted_daemon_reaped']={'pid':pid,'status':status}
  except ChildProcessError:cleanup['exact_adopted_daemon_reaped']=None
  cleanup['daemon_pid_absent']=not Path(f'/proc/{daemon.pid}').exists()
  os.close(daemon_fd);cleanup['daemon_pidfd_closed']=True
 if client_fd is not None:
  cleanup['client_exited']=ready(client_fd);cleanup['client_pid_absent']=not Path(f'/proc/{client.pid}').exists();os.close(client_fd);cleanup['client_pidfd_closed']=True
 assert libc.prctl(36,previous.value,0,0,0)==0
 current=ctypes.c_int();assert libc.prctl(37,ctypes.byref(current),0,0,0)==0 and current.value==previous.value
 cleanup['temporary_subreaper_restored']=True;put('separate-owned-cleanup.json',cleanup)
 after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in inputs};put('inputs-after.json',after);assert after==inputs
print(json.dumps({'red_observed':outcome['exact_pinned_daemon_alive_after_original_controller_returns'],'original_reason':outcome['old_controller_execution']['reason'],'cleanup':cleanup,'one_real_gradle_invocation':True,'library_methods':0},indent=2))
assert cleanup['daemon_pid_absent'] and cleanup['client_pid_absent']
