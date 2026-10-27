"""Bounded actual consumer Kotlin DSL help; no candidate resolution/tests/publication."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
ROOT=Path('/root/projects/nativeCmpKit')
OUT=Path(__file__).resolve().parent/'dsl-help002'
assert not OUT.exists(); OUT.mkdir()
sys.path.insert(0,str(ROOT/'scripts/ci'))
import core_io_consumer as c
before=c.inputs(ROOT)
consumer,copied=c.copy_fixture(ROOT,OUT)
env=c.environment(ROOT,OUT)
command=[str(ROOT/'gradlew'),'-p',str(consumer),'--no-daemon','--no-parallel','--no-configuration-cache','--no-build-cache','--console=plain','--max-workers=1','--dependency-verification','strict','-Dorg.gradle.jvmargs=-Xmx768m -Dfile.encoding=UTF-8','-Pkotlin.compiler.execution.strategy=in-process','-PnativecmpkitRepository='+str(ROOT/c.REPOSITORY),'-PnativecmpkitVersion='+c.VERSION,'help']
cache_before=c.producer_cache_state(ROOT)
assert cache_before['candidate_payload_group_absent']
for name,value in [('inputs-before.json',before),('fixture-copy-before.json',copied),('cache-before.json',cache_before)]:
 (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
start=time.monotonic(); result={}; log=OUT/'gradle.log'
with log.open('xb') as stream:
 process=subprocess.Popen(command,cwd=consumer,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  while process.poll() is None:
   if shutil.disk_usage(ROOT).free<8*1024**3: result['stop_reason']='Root8GiB reserve reached'
   elif shutil.disk_usage(OUT).free<2*1024**3:result['stop_reason']='Owned tmpfs2GiB reserve reached'
   elif log.stat().st_size>64*1024**2:result['stop_reason']='Bounded log limit reached'
   elif time.monotonic()-start>480:result['stop_reason']='Deadline reached'
   if result:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
    break
   time.sleep(.25)
 finally:
  if process.poll() is None:
   os.killpg(process.pid,signal.SIGTERM);process.wait(timeout=10)
result.update(exit_code=process.returncode,elapsed_seconds=round(time.monotonic()-start,3))
after=c.inputs(ROOT);copy_after={name:c.lt.sha256(consumer/name) for name in c.FIXTURE_FILES};cache_after=c.producer_cache_state(ROOT)
assert before==after and copied==copy_after and cache_after['candidate_payload_group_absent']
for name,value in [('inputs-after.json',after),('fixture-copy-after.json',copy_after),('cache-after.json',cache_after)]:
 (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
receipt={'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':c.lt.git_revision(ROOT),'source_tree_dirty':True,'command':command,'cwd':str(consumer),'execution':result,'source_input_count':len(before),'inputs_sha256':c.lt.input_digest(before),'source_inputs_held':before==after,'copied_fixture_inputs_held':copied==copy_after,'candidate_group_absent_in_producer_cache_before_after':True,'gradle_log_sha256':c.lt.sha256(log),'driver_sha256':c.lt.sha256(Path(__file__)),'candidate_staged_scope':'Existing Core-only repository from failed D2 run. Neither IO resolution nor candidate tests requested.','actual_consumer_or_library_methods_executed':0,'packages_published':False,'release_readiness_certified':False,'scope':'Actual copied consumer Kotlin DSL configuration/help only, JDK17/Gradle9.7.1 with normal official dependency acquisition, reusing the private producer dependency home for plugins without candidate resolution. NOT the fresh-child-cache seven-method packaged consumer, trust or detached-process attestation.'}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({key:receipt[key] for key in ('execution','source_input_count','source_inputs_held','actual_consumer_or_library_methods_executed')},indent=2))
sys.exit(0 if result['exit_code']==0 else 1)
