import os, sys, types, json, stat, tempfile, hashlib, ast

PREVIOUS = '/root/nativecmpkit-source-proposals-20261105/lead-resume-R11-P5-20261106-rh98k8cp'
HERE = '/root/nativecmpkit-source-proposals-20261105/lead-resume-P6-tooling-startup-20261106-61q2z79j'
fd = os.open(PREVIOUS + '/safeio.py', os.O_RDONLY | os.O_NOATIME | os.O_NOFOLLOW)
try:
    data = os.read(fd, 16384)
finally:
    os.close(fd)
s = types.ModuleType('safeio')
exec(compile(data, PREVIOUS + '/safeio.py', 'exec'), s.__dict__)

old, old_pin = s.obj(PREVIOUS + '/mac-p5-important8/PREFLIGHT-MANIFEST.json')
review, review_pin = s.obj('/root/nativecmpkit-source-proposals-20261105/mac-p5-saved-results-review-astra-hf4loojc/REVIEW.json')
assert review_pin['sha256'] == '8cdabb87224f995bf600d2bea15196e12e20d9b2acba762bdc287151319986a6'
selected = review['method_outcomes']['only_failed_recovery_selection']
assert len(selected) == 2 and selected == [old['selected'][5], old['selected'][7]]
original_runner, runner_pin = s.read(PREVIOUS + '/mac-p5-important8/RUNNER-IMPORTANT8.py')
assert runner_pin['sha256'] == '2436ab48710479e54d0225f12671a0a8947004bc5fe1ff1a4ec5fdedf259deea'
runner = original_runner.decode()
changes = []

def replace(before, after):
    global runner
    assert runner.count(before) == 1, before[:100]
    runner = runner.replace(before, after, 1)
    changes.append({'before': before, 'after': after})

replace('tempfile,unittest,time\n', 'tempfile,unittest,time,tokenize\n')
replace("rawopen=os.open;rawbuiltin=builtins.open;rawio=io.open\n", "rawopen=os.open;rawbuiltin=builtins.open;rawio=io.open\n_audit_open_requests=[]\n")
replace('''def prohibited(path):
 if not isinstance(path,(str,bytes,os.PathLike)):return
 p=os.path.abspath(os.fsdecode(path))
 if 'test_javafx_ordinary_success_trace.py' in p.split('/'):raise RuntimeError('protected source/copy access refused')
 if any(p==r or p.startswith(r+'/') for r in originals):raise RuntimeError('original worktree/ROOT access refused; finite model only')
''', '''def effective_path(path,dir_fd=None):
 if type(path) is int:
  path=os.readlink('/proc/self/fd/'+str(path))
 if not isinstance(path,(str,bytes,os.PathLike)):return None
 path=os.fsdecode(path)
 if not os.path.isabs(path) and dir_fd not in (None,-1,-100):
  if type(dir_fd) is not int:raise RuntimeError('invalid directory descriptor')
  base=os.readlink('/proc/self/fd/'+str(dir_fd))
  if not os.path.isabs(base) or base.endswith(' (deleted)'):raise RuntimeError('unbound directory descriptor')
  path=base+'/'+path
 return os.path.abspath(path)

def prohibited(path,dir_fd=None):
 p=effective_path(path,dir_fd)
 if p is None:return
 if 'test_javafx_ordinary_success_trace.py' in p.split('/'):raise RuntimeError('protected source/copy access refused')
 if any(p==r or p.startswith(r+'/') for r in originals):raise RuntimeError('original worktree/ROOT access refused; finite model only')
 return p
''')
replace('''def noatime_open(path,flags,mode=0o777,*,dir_fd=None):
 request=path
 if dir_fd is not None and isinstance(path,(str,bytes,os.PathLike)) and not os.path.isabs(os.fsdecode(path)):
  base=os.readlink('/proc/self/fd/'+str(dir_fd));request=base+'/'+os.fsdecode(path)
 prohibited(request)
 if isinstance(request,(str,bytes,os.PathLike)):
  full=os.path.abspath(os.fsdecode(request))
  if full==model or full.startswith(prefix):
   if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise RuntimeError('model source write refused')
   flags|=os.O_NOATIME|os.O_NOFOLLOW
 return rawopen(path,flags,mode,dir_fd=dir_fd)
''', '''def noatime_open(path,flags,mode=0o777,*,dir_fd=None):
 full=prohibited(path,dir_fd)
 if full is not None and (full==model or full.startswith(prefix)):
  if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise RuntimeError('model source write refused')
  flags|=os.O_NOATIME|os.O_NOFOLLOW
 _audit_open_requests.append((os.fsdecode(path),full))
 try:return rawopen(path,flags,mode,dir_fd=dir_fd)
 finally:_audit_open_requests.pop()
''')
replace('builtins.open=stream(rawbuiltin);io.open=stream(rawio)\n', '''builtins.open=stream(rawbuiltin);io.open=stream(rawio)
assert tokenize._builtin_open is rawbuiltin
tokenize._builtin_open=builtins.open
''')
replace('def wrapped(path,*a,_original=original,**kw):prohibited(path);return _original(path,*a,**kw)', 'def wrapped(path,*a,_original=original,**kw):prohibited(path,kw.get("dir_fd"));return _original(path,*a,**kw)')
replace(''' if event in ('open','os.scandir','os.listdir') and args:prohibited(args[0])
 if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.path.abspath(os.fsdecode(args[0]));mode=args[1] if len(args)>1 else None;flags=args[2] if len(args)>2 else 0
  if p==model or p.startswith(prefix):
   if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (type(flags) is int and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):raise RuntimeError('readonly source model required')
 if event in ('os.remove','os.rmdir','os.rename','os.mkdir','os.chmod','os.chown','os.utime','os.truncate'):
  for p in args[:2]:
   if isinstance(p,(str,bytes,os.PathLike)):
    prohibited(p);p=os.path.abspath(os.fsdecode(p))
    if p==model or p.startswith(prefix):raise RuntimeError('model source mutation refused')
''', ''' if event in ('os.scandir','os.listdir') and args:prohibited(args[0])
 if event=='open' and args:
  request=args[0]
  if _audit_open_requests and isinstance(request,(str,bytes,os.PathLike)) and os.fsdecode(request)==_audit_open_requests[-1][0]:
   request=_audit_open_requests[-1][1]
  p=prohibited(request);mode=args[1] if len(args)>1 else None;flags=args[2] if len(args)>2 else 0
  if p is not None and (p==model or p.startswith(prefix)):
   if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (type(flags) is int and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):raise RuntimeError('readonly source model required')
 mutation_operands={'os.remove':((0,1),),'os.rmdir':((0,1),),'os.rename':((0,2),(1,3)),
                    'os.mkdir':((0,2),),'os.chmod':((0,2),),'os.chown':((0,3),),
                    'os.utime':((0,3),),'os.truncate':((0,None),)}
 for path_index,fd_index in mutation_operands.get(event,()):
  descriptor=None if fd_index is None or fd_index>=len(args) else args[fd_index]
  p=prohibited(args[path_index],descriptor)
  if p is not None and (p==model or p.startswith(prefix)):raise RuntimeError('model source mutation refused')
''')
replace("print('NCK_MAC_P5_IMPORTANT8_BEGIN',flush=True);suite=unittest.TestLoader().loadTestsFromNames(m['selected']);assert suite.countTestCases()==8", "print('NCK_MAC_P5_FAILED2_BEGIN',flush=True);suite=unittest.TestLoader().loadTestsFromNames(m['selected']);assert suite.countTestCases()==2")
replace("print('NCK_MAC_P5_IMPORTANT8_END '+json.dumps(out,sort_keys=True),flush=True)", "print('NCK_MAC_P5_FAILED2_END '+json.dumps(out,sort_keys=True),flush=True)")
replace('result.testsRun==8', 'result.testsRun==2')
ast.parse(runner)
inverse=runner
for change in reversed(changes):
    assert inverse.count(change['after']) == 1
    inverse=inverse.replace(change['after'],change['before'],1)
assert inverse.encode()==original_runner

out=HERE+'/mac-p5-only-failed2'
os.mkdir(out,0o700)
runtime=tempfile.mkdtemp(prefix='nck-mac-p5-failed2-',dir='/tmp')
os.chmod(runtime,0o700)
model=runtime+'/model'
for p in (model,runtime+'/h',runtime+'/t'):
    os.mkdir(p,0o700)
candidate={}
for rel,pin in old['source_pins'].items():
    assert not rel.startswith('/') and all(x not in ('','.','..','test_javafx_ordinary_success_trace.py') for x in rel.split('/'))
    original,actual=s.read(pin['path'])
    assert actual==pin, (rel,'original changed')
    if rel in old['proposal_pins']:
        payload,actual=s.read(old['proposal_pins'][rel]['path'])
        assert actual==old['proposal_pins'][rel], (rel,'proposal changed')
    else:
        payload=original
    assert hashlib.sha256(payload).hexdigest()==old['model_pins'][rel]['sha256']
    path=model+'/'+rel
    os.makedirs(os.path.dirname(path),mode=0o700,exist_ok=True)
    candidate[rel]=s.write_once(path,payload,stat.S_IMODE(old['model_pins'][rel]['stat']['st_mode']))
assert len(candidate)==38 and len(old['proposal_pins'])==5
m={**old,'model':model,'runtime':runtime,'home':runtime+'/h','tmp':runtime+'/t',
   'selected':selected,'model_pins':candidate,'original_failed8':old_pin,
   'independent_review':review_pin,'reused_six':review['method_outcomes']['reusable_completed_source_method_results'],
   'runtime_identity':s.identity(os.stat(runtime,follow_symlinks=False)),
   'carrier_correction':'event-specific dirfd interpretation and prebound tokenize noatime reader; no project-source changes'}
manifest_pin=s.write_once(out+'/PREFLIGHT-MANIFEST.json',json.dumps(m,sort_keys=True,separators=(',',':')).encode()+b'\n')
assert manifest_pin['size']<=524288
new_runner_pin=s.write_once(out+'/RUNNER-FAILED2.py',runner.encode())
s.write_once(out+'/CARRIER-CHANGES.json',json.dumps({'old_runner':runner_pin,'new_runner':new_runner_pin,'forward_inverse_exact':True,'changes':changes},sort_keys=True,indent=2).encode()+b'\n')
s.write_once(out+'/EXECUTION-RESERVATION.json',json.dumps({'executions_authorized':1,'selected':selected,'accepted_tests_replayed':False,'manifest':manifest_pin,'runner':new_runner_pin,**old['limits'],'project_source_changes':0},sort_keys=True,indent=2).encode()+b'\n')
print(json.dumps({'ready':True,'out':out,'runtime':runtime,'model_sources':len(candidate),'only_failed_methods':selected,'runner':new_runner_pin},indent=2))
