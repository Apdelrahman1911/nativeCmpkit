"""Actual task-owned Gradle daemon topology, zero jcmd/foreign-process scans.
Two fresh plugin-free projects differ only in pre-exec Linux client subreaping.
The generated task holds a bounded acknowledgement handshake for a stat read.
This is process-shape evidence, not dependency/native/consumer test acceptance.
"""
from pathlib import Path
import ctypes,hashlib,json,os,shutil,signal,subprocess,sys,tempfile,time
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/dependencies'))
import integrity as d,integrity_model as m,runtime_witness as w
JAVA=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java').resolve();JDK=JAVA.parent.parent
GRADLE=Path('/root/.gradle/wrapper/dists/gradle-9.7.1-bin/1w1c7tv4s851m17nbqdsro2tv/gradle-9.7.1')
assert not (OUT/'receipt.json').exists() and sys.platform=='linux' and shutil.disk_usage(ROOT).free>=8192*1024**2
os.environ['JAVA_HOME']=str(JDK)
version=subprocess.run([str(JAVA),'-version'],capture_output=True,check=True).stderr.decode();assert 'version "17.' in version
libc=ctypes.CDLL(None,use_errno=True)
libc.prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong];libc.prctl.restype=ctypes.c_int
PR_SET_CHILD_SUBREAPER=36;PR_GET_CHILD_SUBREAPER=37

def enable_client_subreaper():
 flag=ctypes.c_int()
 if libc.prctl(PR_SET_CHILD_SUBREAPER,1,0,0,0)!=0 or libc.prctl(PR_GET_CHILD_SUBREAPER,ctypes.addressof(flag),0,0,0)!=0 or flag.value!=1:
  raise OSError('Task-owned Linux client subreaper setup/readback refused')

settings='rootProject.name = "nativecmpkit-owned-process-shape"\n'
build='''import groovy.json.JsonOutput
tasks.register("recordOwnedDaemonShape") {
    doLast {
        def owned = ProcessHandle.current()
        def record = [gradle_version:gradle.gradleVersion, java_major:JavaVersion.current().majorVersion,
                      runtime_pid:owned.pid(), parent_pid:owned.parent().get().pid()]
        new File(projectDir,"task-runtime.json").text = JsonOutput.toJson(record)
        def deadline = System.nanoTime() + 10_000_000_000L
        while (!new File(projectDir,"acknowledge-owned-shape").exists()) {
            if (System.nanoTime() >= deadline) throw new GradleException("Owned shape acknowledgement deadline")
            Thread.sleep(10)
        }
    }
}
'''
files=w.checkpoint_files();selected={str(ROOT/n):h for n,h in files.items()}
selected.update({str(p):m.file_sha256(p) for p in [Path(__file__),JAVA,GRADLE/'bin/gradle',GRADLE/'lib/gradle-gradle-cli-main-9.7.1.jar',GRADLE/'lib/gradle-daemon-main-9.7.1.jar']})
m.write_new(OUT/'inputs-before.json',m.json_bytes(selected));(OUT/'settings.gradle').write_text(settings);(OUT/'build.gradle').write_text(build)
rows=[];started=d.utc_now()
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-gradle-shape-',dir='/dev/shm') as directory:
 owned=Path(directory)
 for mode in ['default','client-subreaper']:
  project=owned/mode;project.mkdir();(project/'settings.gradle').write_text(settings);(project/'build.gradle').write_text(build)
  environment=d._environment(project,fresh=True)
  command=[str(GRADLE/'bin/gradle'),'recordOwnedDaemonShape','--offline','--no-daemon','--no-configuration-cache','--console=plain','--max-workers=1']
  log=OUT/(mode+'.log');record={'mode':mode,'started_utc':d.utc_now(),'subreaper_requested':mode=='client-subreaper','jcmd_attempts':0,'foreign_process_scan_performed':False}
  process=None;runtime_pid=None;runtime_fd=None
  with log.open('xb') as output:
   try:
    process=subprocess.Popen(command,cwd=project,env=environment,stdout=output,stderr=subprocess.STDOUT,
                             start_new_session=True,preexec_fn=enable_client_subreaper if mode=='client-subreaper' else None)
    record['launcher_pid']=process.pid;record['subreaper_preexec_call_returned_successfully']=mode=='client-subreaper'
    deadline=time.monotonic()+75
    while not (project/'task-runtime.json').exists():
     if process.poll() is not None:raise RuntimeError('Owned Gradle ended before shape record')
     if time.monotonic()>deadline or shutil.disk_usage(project).free<8192*1024**2:raise TimeoutError('Owned process-shape bound')
     time.sleep(.02)
    task=m.read_json(project/'task-runtime.json');assert set(task)=={'gradle_version','java_major','runtime_pid','parent_pid'} and task['gradle_version']=='9.7.1' and task['java_major']=='17'
    runtime_pid=task['runtime_pid'];assert type(runtime_pid) is int and runtime_pid>1 and runtime_pid!=process.pid
    client=w.identity(process.pid);daemon=w.identity(runtime_pid)
    assert client.parent==os.getpid() and client.pid==client.group==client.session
    assert Path(os.readlink(f'/proc/{process.pid}/exe'))==JAVA and Path(os.readlink(f'/proc/{runtime_pid}/exe'))==JAVA
    assert Path(os.readlink(f'/proc/{process.pid}/cwd'))==project and Path(os.readlink(f'/proc/{runtime_pid}/cwd')).is_relative_to(project)
    args=w.fields(w.proc_bytes(process.pid,'cmdline'));assert args==[*w.client_prefix(JDK,GRADLE),*command[1:]]
    w.check_environment(w.environment(w.proc_bytes(process.pid,'environ')),project,JDK)
    w.check_environment(w.environment(w.proc_bytes(runtime_pid,'environ')),project,JDK)
    children=w.owned_children(client)
    assert daemon.parent==task['parent_pid'] and w.identity(runtime_pid)==daemon
    record.update(task_runtime=task,client_identity=client.public(),daemon_identity=daemon.public(),client_direct_children=children,
                  runtime_is_client_child=daemon.parent==client.pid and runtime_pid in children,
                  runtime_in_client_group_and_session=daemon.group==client.group and daemon.session==client.session,
                  runtime_is_own_group_and_session=daemon.group==daemon.pid==daemon.session,
                  explicit_actual_java_command_environment_match=True)
    if daemon.parent==client.pid:
     runtime_fd=os.pidfd_open(runtime_pid,0)
    (project/'acknowledge-owned-shape').write_text('Recorded live stat; no diagnostic attach performed.\n')
    process.wait(timeout=30);record['exit_code']=process.returncode
    # Only task-receipt PIDs are checked; no /proc listing or global JVM query.
    for name,pid in [('client',process.pid),('runtime',runtime_pid)]:
     until=time.monotonic()+10
     while Path(f'/proc/{pid}').exists() and time.monotonic()<until:time.sleep(.02)
     record[name+'_absent_after_completion']=not Path(f'/proc/{pid}').exists()
    assert record['exit_code']==0 and record['client_absent_after_completion'] and record['runtime_absent_after_completion']
   except BaseException as error:
    record['error_type']=type(error).__name__
    # Release the source-generated handshake even when the observed shape is
    # not eligible. It is not evidence authorizing a foreign-PID termination.
    (project/'acknowledge-owned-shape').write_text('Release owned bounded handshake after failed observation.\n')
    if process is not None and process.poll() is None:
     try:process.wait(timeout=15)
     except subprocess.TimeoutExpired:
      with __import__('contextlib').suppress(ProcessLookupError):os.killpg(process.pid,signal.SIGTERM)
      try:process.wait(timeout=10)
      except subprocess.TimeoutExpired:
       with __import__('contextlib').suppress(ProcessLookupError):os.killpg(process.pid,signal.SIGKILL)
       process.wait()
    if runtime_fd is not None:
     # This fd was obtained only for a live exact client child; unlike a
     # guessed numeric PID it cannot target a subsequently reused process.
     with __import__('contextlib').suppress(ProcessLookupError):signal.pidfd_send_signal(runtime_fd,signal.SIGTERM)
   finally:
    if runtime_fd is not None:os.close(runtime_fd)
    record['finished_utc']=d.utc_now();record['log_sha256']=m.file_sha256(log);rows.append(record)
  m.write_new(OUT/(mode+'.json'),m.json_bytes(record))
  print(json.dumps(record),flush=True)
  if 'error_type' in record:break
after={p:m.file_sha256(Path(p)) for p in selected};m.write_new(OUT/'inputs-after.json',m.json_bytes(after))
receipt={'schema_version':1,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'started_utc':started,'finished_utc':d.utc_now(),'input_files_held':selected==after,'rows':rows,'actual_gradle_invocations':len(rows),'jcmd_attempts':0,'library_native_or_packaged_consumer_methods_executed':0,'all_owned_temp_outputs_removed':True,'release_readiness_certified':False,'scope':'Actual installed Gradle9.7.1/JDK17 task runtime and live Linux PID/parent/group/session observations in two fresh plugin-free owned projects. No external dependencies/trust, full fixtures, jcmd, foreign JVM scan, Kotlin/native/library or consumer tests. Subreaping is a proposed ownership topology, not permission to relax existing ancestry/attach gates.'}
m.write_new(OUT/'receipt.json',m.json_bytes(receipt));assert selected==after and len(rows)==2 and all('error_type' not in row for row in rows)
