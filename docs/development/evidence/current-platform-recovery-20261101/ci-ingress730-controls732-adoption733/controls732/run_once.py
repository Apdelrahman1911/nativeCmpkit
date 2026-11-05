import argparse, hashlib, json, os, signal, stat, subprocess, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
PACKET=Path('/root/nativecmpkit-source-proposals-20261104/ci-current-source-ingress730-r1')
ROOT=Path('/root/projects/nativeCmpKit')
FIELDS=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
MAX=4*1024*1024
SEAL_SHA='8c8c3672040e4a7466f63b60ba5d231b1f01589444bfae575ccc7add4dd596e5'
SELECTION_SHA='7055b539119745ab571829a575cfd897c28e6a1cd9e5c68505041b2bcdf3e73b'
def sha(b):return hashlib.sha256(b).hexdigest()
def ident(s):return [getattr(s,k) for k in FIELDS]
def read(p):
 if p.resolve(strict=True)!=p:raise ValueError('Input path alias '+str(p))
 s=p.lstat();i=ident(s)
 if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size>MAX:raise ValueError('Nonordinary/bounded input '+str(p))
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  if ident(os.fstat(f.fileno()))!=i:raise ValueError('Opened input drift '+str(p))
  b=f.read(MAX+1)
  if ident(os.fstat(f.fileno()))!=i:raise ValueError('Read input drift '+str(p))
 if ident(p.lstat())!=i or len(b)!=s.st_size:raise ValueError('Closed input drift '+str(p))
 return b,{'bytes':len(b),'sha256':sha(b),'mode':format(stat.S_IMODE(s.st_mode),'04o'),'stat_identity':i}
def emit(name,v):
 b=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 fd=os.open(HERE/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return {'path':str(HERE/name),'sha256':sha(b),'bytes':len(b)}
def capture(base,expected):
 rows={}
 for rel,row in expected.items():
  b,current=read(base/rel)
  if current['sha256']!=row['sha256'] or current['bytes']!=row['bytes'] or current['mode']!=row['mode']:raise ValueError('Source map drift '+rel)
  expected_identity=row.get('stat_identity')
  if expected_identity is None and 'identity' in row:expected_identity=[row['identity'][key] for key in FIELDS]
  if expected_identity is not None and current['stat_identity']!=expected_identity:raise ValueError('Original source identity drift '+rel)
  rows[rel]=current
 return rows
ap=argparse.ArgumentParser()
ap.add_argument('--review-json',required=True);ap.add_argument('--review-sha256',required=True)
args=ap.parse_args()
started=time.monotonic();process=None;pin=None;primary=None;child_rc=None;cleanup=[]
try:
 review,rr=read(Path(args.review_json))
 if rr['sha256']!=args.review_sha256:raise ValueError('Independent source receipt changed')
 accepted=json.loads(review)
 seal,sr=read(PACKET/'SOURCE-SEAL730.json')
 if sr['sha256']!=SEAL_SHA:raise ValueError('Final source seal changed')
 sealed=json.loads(seal)
 for rel,row in sealed['files'].items():
  _,actual=read(PACKET/rel)
  if {k:actual[k] for k in ('bytes','sha256','mode')}!=row:raise ValueError('Sealed source changed '+rel)
 sel,_=read(PACKET/'SELECTED-UNIQUE23-CONTROLS730.json')
 if sha(sel)!=SELECTION_SHA:raise ValueError('Selection changed')
 selection=json.loads(sel)
 recipe=json.loads(read(PACKET/'LEAD-CONTROL-EXECUTION-RECIPE730.json')[0])
 if selection['unique_count']!=23 or len(recipe['argv'][7:])!=23 or recipe['argv'][:7]!=['/usr/bin/python3.12','-B','-S','-s','-m','unittest','-v']:raise ValueError('Ordinary exact23 invocation changed')
 if len(set(recipe['argv'][7:]))!=23:raise ValueError('Duplicate selected controls')
 candidate=Path(recipe['complete_finite_candidate_root'])
 expected=json.loads(read(PACKET/'FINAL-FINITE369-MAP730.json')[0])
 original=json.loads(read(PACKET/'ROOT365-PREIMAGE-CUSTODY730.json')[0])
 root_map=original['ROOT_preimages319']|original['dependency_only46']
 if len(expected)!=369 or len(root_map)!=365:raise ValueError('Finite map population changed')
 before_candidate=capture(candidate,expected);before_root=capture(ROOT,root_map)
 emit('BEFORE-CUSTODY.json',{'candidate369':before_candidate,'ROOT365':before_root})
 emit('INTENT.json',{'source_seal_sha256':SEAL_SHA,'selection_sha256':SELECTION_SHA,'review':rr,'review_path':args.review_json,'unique_selected':23,'unchanged_accepted_tests_replayed':False,'native_compiler_consumer_executions':0,'argv':recipe['argv'],'total_budget_seconds':300})
 runtime=HERE/'runtime-FIRST';runtime.mkdir(mode=0o700)
 for n in ('home','tmp','pycache'):(runtime/n).mkdir(mode=0o700)
 env={'PATH':'/usr/bin:/bin','HOME':str(runtime/'home'),'TMPDIR':str(runtime/'tmp'),'LC_ALL':'C.UTF-8','LANG':'C.UTF-8','PYTHONPATH':recipe['PYTHONPATH'],'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTHONHASHSEED':'0'}
 with open(HERE/'stdout.log','xb') as stdout,open(HERE/'stderr.log','xb') as stderr:
  process=subprocess.Popen(recipe['argv'],cwd=recipe['cwd'],env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True)
  pin={'pid':process.pid,'pgid':os.getpgid(process.pid),'session':os.getsid(process.pid)}
  emit('ORIGINAL-CHILD-PIN.json',pin)
  while True:
   result=os.waitid(os.P_PID,process.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
   if result is not None:break
   if time.monotonic()-started>=300:raise TimeoutError('Important-control cohort exceeded300s')
   if os.stat(HERE/'stdout.log').st_size+os.stat(HERE/'stderr.log').st_size>16*1024*1024:raise ValueError('Bounded control output exceeded16MiB')
   time.sleep(.05)
except BaseException as e:
 primary={'type':type(e).__name__,'message':str(e)}
finally:
 if process is not None:
  for sig in (signal.SIGTERM,signal.SIGKILL):
   try:
    if pin is None or pin['pgid']!=process.pid or pin['session']!=process.pid:raise ValueError('Owned child group pin invalid')
    os.killpg(pin['pgid'],sig);cleanup.append({'signal':sig.name,'sent':True})
   except ProcessLookupError:cleanup.append({'signal':sig.name,'group_already_absent':True})
   except BaseException as e:cleanup.append({'signal':sig.name,'error_type':type(e).__name__,'message':str(e)})
  try:child_rc=process.wait(timeout=3)
  except BaseException as e:cleanup.append({'wait_error_type':type(e).__name__})
  try:os.killpg(process.pid,0);cleanup.append({'group_absent':False})
  except ProcessLookupError:cleanup.append({'group_absent':True})
  except BaseException as e:cleanup.append({'group_absence_error':type(e).__name__})
 hold_error=None
 try:
  after_candidate=capture(candidate,before_candidate);after_root=capture(ROOT,before_root)
  emit('AFTER-CUSTODY.json',{'candidate369':after_candidate,'ROOT365':after_root})
 except BaseException as e:hold_error={'type':type(e).__name__,'message':str(e)}
 runtime_cleanup=[]
 if (HERE/'runtime-FIRST').exists():
  for n in ('home','tmp','pycache'):
   p=HERE/'runtime-FIRST'/n
   try:p.rmdir();runtime_cleanup.append({'owned':n,'empty_removed':True})
   except OSError as e:runtime_cleanup.append({'owned':n,'removed':False,'error_type':type(e).__name__})
  try:(HERE/'runtime-FIRST').rmdir()
  except OSError:pass
 logs={}
 for n in ('stdout.log','stderr.log'):
  p=HERE/n
  if p.exists():
   b=p.read_bytes();logs[n]={'bytes':len(b),'sha256':sha(b)}
 result={'outcome':'passed' if primary is None and hold_error is None and child_rc==0 and any(x.get('group_absent') is True for x in cleanup) and all(x.get('empty_removed') for x in runtime_cleanup) else 'failed','child_exit':child_rc,'primary_refusal':primary,'custody_refusal':hold_error,'elapsed_seconds':time.monotonic()-started,'source_seal_sha256':SEAL_SHA,'selection_sha256':SELECTION_SHA,'planned_unique':23,'logs':logs,'cleanup':cleanup,'runtime_cleanup':runtime_cleanup,'candidate369_and_ROOT365_held':hold_error is None,'native_compiler_consumer_executions':0,'accepted_population_replay':False}
 emit('ACTUAL-FIRST-RESULT.json',result)
 print(json.dumps(result),flush=True)
 if result['outcome']!='passed':raise SystemExit(2)
