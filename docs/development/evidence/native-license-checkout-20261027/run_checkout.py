"""Finite source-held Python tooling verification; never native/legal/release clearance."""
from pathlib import Path
import datetime as dt, hashlib, json, os, re, signal, subprocess, sys, time
ROOT=Path('/root/projects/nativeCmpKit')
BASE=Path('/dev/shm/nativecmpkit-license-supplement-work-20261027')
label=sys.argv[1]
command=['/usr/bin/python3','-B',*sys.argv[2:]]
assert label.isalnum() and command[2:4] in (['-m','unittest'],[str(BASE/'test_requirement.py')]) or label.isalnum() and command[2:]==[str(BASE/'test_requirement.py')]
assert not (BASE/(label+'.json')).exists() and not (BASE/(label+'.log')).exists()
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 paths=set()
 for folder in ('tests/consumer','scripts/native'):
  paths.update(p for p in (ROOT/folder).glob('*.py') if p.is_file())
 paths.update(p for p in (ROOT/'licenses/native-dependency-supplements').rglob('*') if p.is_file())
 paths.add(BASE/'test_requirement.py')
 paths.add(ROOT/'.gitattributes')
 return {p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else 'original-red-probe/test_requirement.py':{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)}
before=snapshot();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
stage_before=hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
log=BASE/(label+'.log');start=utc();tick=time.monotonic()
with log.open('x') as out:
 process=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 try: process.wait(timeout=240)
 except BaseException:
  if process.poll() is None:
   os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
  raise
finish=utc();after=snapshot();stage_after=hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
s=log.read_text();count=re.findall(r'^Ran (\d+) tests? in [^\n]+$',s,re.M)
methods=re.findall(r'^(test_[^( ]+) \(([^)]+)\) \.\.\. (.+)$',s,re.M)
receipt={'schema_version':1,'source_revision':head,'dirty_worktree':True,'command':command,'started_utc':start,'finished_utc':finish,'elapsed_seconds':round(time.monotonic()-tick,3),'exit_code':process.returncode,'source_inputs_before':before,'source_inputs_after':after,'source_held':before==after,'staged_index_held':stage_before==stage_after,'log_sha256':sha(log),'test_methods':int(count[-1]) if count else None,'verbose_outcomes':[{'method':a,'class':b,'outcome':c} for a,b,c in methods],'unittest_summary_ok':bool(re.search(r'^OK$',s,re.M)),'passed':process.returncode==0 and before==after and stage_before==stage_after and bool(count) and bool(re.search(r'^OK$',s,re.M)),'library_native_consumer_legal_or_release_clearance':False}
(BASE/(label+'.json')).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:receipt[k] for k in ('source_revision','source_held','staged_index_held','exit_code','elapsed_seconds','test_methods','unittest_summary_ok','passed')},indent=2))
sys.exit(0 if receipt['passed'] else 1)
