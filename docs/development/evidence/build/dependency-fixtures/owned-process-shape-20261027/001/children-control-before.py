"""Live known-child /proc control; no global scan, Java or diagnostic attach."""
from pathlib import Path
import hashlib,json,os,selectors,subprocess,sys,time
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/dependencies'));import runtime_witness as w
assert not (OUT/'children-control.json').exists()
process=subprocess.Popen([sys.executable,'-B','-c',"import sys; print('ready', flush=True); sys.stdin.buffer.read(1)"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
 with selectors.DefaultSelector() as selector:
  selector.register(process.stdout,selectors.EVENT_READ);assert selector.select(timeout=10)
 assert process.stdout.readline()==b'ready\n'
 parent=w.identity(os.getpid());child=w.identity(process.pid)
 assert child.parent==parent.pid and process.poll() is None
 actual=w.owned_children(parent)
 per_thread=[]
 for thread in sorted((Path('/proc')/str(parent.pid)/'task').iterdir()):
  raw=w.proc_bytes(parent.pid,f'task/{thread.name}/children',4096)
  per_thread.append({'thread_id':int(thread.name),'raw_bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'contains_known_live_child':str(child.pid) in raw.decode().split()})
 record={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'recorded_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'kernel_release':os.uname().release,'parent_identity':parent.public(),'known_child_identity':child.public(),'live_known_child_parent_matches':True,'proc_children_contains_known_child':child.pid in actual,'proc_children_count':len(actual),'per_thread_children_observations':per_thread,'read_only_known_processes':True,'java_gradle_jcmd_or_library_methods_executed':0,'scope':'Real one-child Python handshake with stable known Popen/start/parent identity. Empty per-thread children data despite live parent-matching child is an observed proc-provider limitation, not proof of Gradle daemon orphaning. No foreign scan or attach.'}
 process.stdin.write(b'x');process.stdin.flush();process.stdin.close();assert process.wait(timeout=10)==0
 record['owned_child_absent_after_completion']=not Path(f'/proc/{child.pid}').exists();assert record['owned_child_absent_after_completion']
 (OUT/'children-control.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');print(json.dumps(record,indent=2))
finally:
 if process.poll() is None:process.kill();process.wait(timeout=5)
 for p in [process.stdin,process.stdout,process.stderr]:
  if p and not p.closed:p.close()
