"""One explicitly scheduled paired fixture/witness slot, no automatic retries.

Only the original integrity driver controls Gradle. This lead wrapper retains
source/disk preflight, exact sibling CLI, original exits and bounded observations.
"""
from pathlib import Path
import datetime as dt, hashlib, json, os, shutil, signal, subprocess, sys, time
ROOT=Path('/root/projects/nativeCmpKit');os.chdir(ROOT)
sys.path.insert(0,str(ROOT/'scripts/dependencies'))
import runtime_witness as w
META=ROOT/'build/dependency-fixture007-20261027-001'
LIVE=Path('/dev/shm/nativecmpkit-build007-fixtures-007')
WITNESS=Path(str(LIVE)+'-runtime-witness.json')
SUITE_STDOUT=Path(str(LIVE)+'-suite-stdout.json')
WITNESS_STDOUT=Path(str(LIVE)+'-witness-stdout.json')
JDK=Path('/usr/lib/jvm/java-17-openjdk-amd64');GRADLE=Path('/opt/gradle/gradle-9.7.1')
def put(path,value):
 with path.open('x') as f:f.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
for path in [LIVE,WITNESS,SUITE_STDOUT,WITNESS_STDOUT]:assert not path.exists() and not path.is_symlink()
core=w.checkpoint_files();observer=w.observer_files()
inputs={**core,**{'scripts/dependencies/'+n:d for n,d in observer.items()},'scripts/dependencies/checkpoint-offline-008.json':w.CHECKPOINT_SHA256}
assert len(inputs)==10
source_review=ROOT/'docs/development/evidence/build/dependency-fixtures/observer004-tooling-20261027-002/lead-source-review.json'
review=json.loads(source_review.read_text());assert review['core008_manifest_unchanged'] and review['final_observer_python_methods_passed']==148
held=json.loads((source_review.parent/'green-inputs-before.json').read_text());assert held==inputs
put(META/'inputs-before.json',inputs)
for name in inputs:
 p=META/'inputs'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
capacity={str(p):shutil.disk_usage(p).free for p in (ROOT,LIVE.parent)}
assert min(capacity.values())>=8192*1024**2,'Disk reserve unavailable; neither subprocess launched'
put(META/'preflight.json',{'observed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'source_tree_dirty':True,'free_bytes_before':capacity,'source_held':True,'core008_manifest_unchanged':True,'source_review_sha256':hashlib.sha256(source_review.read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'exclusive_lead_scheduled_local_gradle_slot':True,'maximum_gradle_invocations':6,'total_timeout_seconds':300,'per_invocation_timeout_seconds':90,'reserve_mib':8192,'no_subagents':True,'packages_releases_or_deployments_requested':False})
suite_command=[sys.executable,'scripts/dependencies/integrity.py',*w.fixed_arguments(LIVE,GRADLE)]
env={**os.environ,'JAVA_HOME':str(JDK),'PYTHONDONTWRITEBYTECODE':'1'}
began=time.monotonic();guard=None;minimum_free=dict(capacity)
with SUITE_STDOUT.open('xb') as sf, WITNESS_STDOUT.open('xb') as wf:
 suite=subprocess.Popen(suite_command,cwd=ROOT,env=env,stdout=sf,stderr=subprocess.STDOUT)
 witness_command=[sys.executable,'scripts/dependencies/runtime_witness.py','--destination',str(LIVE),'--output',str(WITNESS),'--suite-pid',str(suite.pid),'--jdk-home',str(JDK),'--gradle-home',str(GRADLE),'--timeout','320']
 observer_process=subprocess.Popen(witness_command,cwd=ROOT,env=env,stdout=wf,stderr=subprocess.STDOUT)
 put(META/'launch.json',{'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'suite_pid':suite.pid,'witness_pid':observer_process.pid,'suite_command':suite_command,'witness_command':witness_command,'same_owned_parent':os.getpid(),'no_automatic_retry':True})
 while suite.poll() is None or observer_process.poll() is None:
  for p in (ROOT,LIVE.parent):
   free=shutil.disk_usage(p).free;minimum_free[str(p)]=min(minimum_free[str(p)],free)
   if free<8192*1024**2 and guard is None:
    guard='lead-disk-reserve-reached'
    if suite.poll() is None:suite.send_signal(signal.SIGINT)
  if time.monotonic()-began>340 and guard is None:
   guard='lead-safety-deadline-reached'
   if suite.poll() is None:suite.send_signal(signal.SIGINT)
  if time.monotonic()-began>365:
   raise RuntimeError('Owned subprocess did not finish after original bounded cleanup; do not signal unrelated processes')
  time.sleep(.25)
 suite_status=suite.wait();witness_status=observer_process.wait()
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in inputs}
put(META/'inputs-after.json',after)
receipt={'finished_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-began,3),'suite_exit_code':suite_status,'witness_exit_code':witness_status,'source_inputs_held':inputs==after,'minimum_free_bytes':minimum_free,'lead_guard':guard,'suite_pid':suite.pid,'witness_pid':observer_process.pid,'suite_python_process_reaped':suite.poll() is not None,'witness_python_process_reaped':observer_process.poll() is not None,'retry_performed':False,'library_native_or_packaged_consumer_methods_executed':0}
put(META/'exits.json',receipt)
for src,name in [(SUITE_STDOUT,'suite-stdout.json'),(WITNESS_STDOUT,'witness-stdout.json')]:shutil.copyfile(src,META/name)
print(json.dumps(receipt,sort_keys=True,indent=2))
if WITNESS.is_file():
 result=json.loads(WITNESS.read_text());print(json.dumps({k:result.get(k) for k in ['observation_attempts','completed_jcmd_commands','all_six_runtime_observations_complete','fixture_and_runtime_selected_subset_complete','stop_reason']},indent=2))
assert inputs==after
raise SystemExit(0 if suite_status==witness_status==0 and guard is None else 1)
