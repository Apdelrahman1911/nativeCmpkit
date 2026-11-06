import os,sys,types,json,time,subprocess,selectors,signal,shutil,stat
PREVIOUS='/root/nativecmpkit-source-proposals-20261105/lead-resume-R11-P5-20261106-rh98k8cp'
HERE='/root/nativecmpkit-source-proposals-20261105/lead-resume-P6-tooling-startup-20261106-61q2z79j/mac-p5-only-failed2'
fd=os.open(PREVIOUS+'/safeio.py',os.O_RDONLY|os.O_NOATIME|os.O_NOFOLLOW)
try:data=os.read(fd,16384)
finally:os.close(fd)
s=types.ModuleType('safeio');exec(compile(data,PREVIOUS+'/safeio.py','exec'),s.__dict__)
reservation,_=s.obj(HERE+'/EXECUTION-RESERVATION.json')
m,mp=s.obj(HERE+'/PREFLIGHT-MANIFEST.json');assert mp==reservation['manifest']
runner,rp=s.read(HERE+'/RUNNER-FAILED2.py');assert rp==reservation['runner']
assert m['limits']=={'Q300':300,'cleanup30':30,'source270':270,'stdout1MiB':1048576}
for group in ('source_pins','proposal_pins','model_pins'):
    for rel,pin in m[group].items():
        _,actual=s.read(pin['path']);assert actual==pin,(group,rel)
boot='''import os,sys
p=sys.argv[1];f=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
try:
 b=os.read(f,1048577);assert len(b)<=1048576 and not os.read(f,1)
finally:os.close(f)
sys.argv=sys.argv[1:];exec(compile(b,p,'exec'),{'__name__':'__main__','__file__':p})
'''
log=HERE+'/FAILED2-ORIGINAL.log'
logfd=os.open(log,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
os.fchmod(logfd,0o600)
started=time.monotonic();deadline=started+270
env={'PATH':os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin'),'HOME':m['home'],'TMPDIR':m['tmp'],'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
p=subprocess.Popen([sys.executable,'-B','-c',boot,HERE+'/RUNNER-FAILED2.py',HERE+'/PREFLIGHT-MANIFEST.json'],cwd=m['model'],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
os.set_blocking(p.stdout.fileno(),False);sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
captured=bytearray();observed=0;eof=False;refusal=None
try:
    while not eof or p.poll() is None:
        if time.monotonic()>deadline:refusal='source270-exhausted';break
        for key,mask in sel.select(min(1,max(0,deadline-time.monotonic()))):
            chunk=os.read(p.stdout.fileno(),65536)
            if not chunk:eof=True;sel.unregister(p.stdout);break
            observed+=len(chunk)
            if observed>1048576:refusal='stdout1MiB-exceeded';break
            captured.extend(chunk);view=memoryview(chunk)
            while view:
                n=os.write(logfd,view);view=view[n:]
        if refusal:break
    if refusal:
        try:os.killpg(p.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
    else:p.wait(timeout=3)
finally:
    os.fsync(logfd);os.close(logfd);sel.close();p.stdout.close()
source_elapsed=time.monotonic()-started
try:os.killpg(p.pid,0);group_absent=False
except ProcessLookupError:group_absent=True
text=captured.decode('utf-8',errors='replace')
ends=[line for line in text.splitlines() if line.startswith('NCK_MAC_P5_FAILED2_END ')]
summary=json.loads(ends[0].split(' ',1)[1]) if len(ends)==1 else None
custody_errors=[];counts={}
for group in ('source_pins','proposal_pins','model_pins'):
    held=0
    for rel,pin in m[group].items():
        try:
            _,actual=s.read(pin['path']);assert actual==pin;held+=1
        except Exception as e:custody_errors.append({'scope':group,'path':rel,'error':type(e).__name__})
    counts[group]=held
passed=(p.returncode==0 and eof and group_absent and refusal is None and not custody_errors and
        summary is not None and summary['tests']==2 and summary['successful'] and not any(summary[k] for k in ('failures','errors','skips')) and
        text.count('NCK_MAC_P5_FAILED2_BEGIN')==1 and len(ends)==1 and source_elapsed<270)
cleanup_started=time.monotonic();cleanup_errors=[];removed=False
if passed:
    try:
        now=s.identity(os.stat(m['runtime'],follow_symlinks=False));before=m['runtime_identity']
        assert all(now[k]==before[k] for k in ('st_dev','st_ino','st_mode','st_uid','st_gid'))
        assert m['runtime'].startswith('/tmp/nck-mac-p5-failed2-') and stat.S_ISDIR(now['st_mode'])
        shutil.rmtree(m['runtime'])
        try:os.stat(m['runtime'],follow_symlinks=False)
        except FileNotFoundError:removed=True
        assert removed
    except Exception as e:cleanup_errors.append(type(e).__name__);passed=False
cleanup_elapsed=time.monotonic()-cleanup_started
if cleanup_elapsed>30 or time.monotonic()-started>300:passed=False;cleanup_errors.append('shared-budget-exhausted')
_,log_pin=s.read(log)
result={'passed':passed,'selected':m['selected'],'reused_six_not_replayed':m['reused_six'],'summary':summary,
 'child_exit':p.returncode,'child_group_absent':group_absent,'capture_eof':eof,'captured_bytes':len(captured),'observed_bytes':observed,
 'source_seconds':source_elapsed,'elapsed_seconds':time.monotonic()-started,'cleanup_seconds':cleanup_elapsed,'refusal':refusal,
 'custody':counts,'custody_errors':custody_errors,'cleanup_errors':cleanup_errors,'owned_runtime_removed':removed,
 'original_log':log_pin,'ROOT_worktree_source_writes':0,'compiler':0,'native':0,'publication':0,'original_failed8_retained':True}
s.write_once(HERE+'/FAILED2-ONCE-RESULT.json',json.dumps(result,sort_keys=True,indent=2).encode()+b'\n')
print(text);print(json.dumps(result,sort_keys=True,indent=2))
raise SystemExit(0 if passed else 1)
