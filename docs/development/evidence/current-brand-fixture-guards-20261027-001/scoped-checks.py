"""Source-held current-identity/consumer/UIKit fixture guards; not native execution."""
from pathlib import Path
import datetime as dt, hashlib, json, os, re, subprocess, sys, time
ROOT=Path('/root/projects/nativeCmpKit'); OUT=Path(__file__).resolve().parent
os.environ['PYTHONDONTWRITEBYTECODE']='1'; os.environ['TMPDIR']=str(OUT)
paths=set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0'))-{''}
# All configured verification/test/controller/current identity inputs; historical
# audit/archive bytes are checked again by the full staged preflight.
paths={p for p in paths if p.startswith(('scripts/','tests/consumer/','calf-ui/src/','calf-navigation/src/','sample/','convention-plugins/','.github/workflows/','gradle/')) or p in {'AGENTS.md','README.md','settings.gradle.kts','build.gradle.kts','mkdocs.yml','docs/migration/identity.json','docs/index.md','docs/installation.md'}}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def snap(): return {p:sha(ROOT/p) for p in sorted(paths) if (ROOT/p).is_file()}
def put(name,x): (OUT/name).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
before=snap(); put('scoped-inputs-before.json',before)
commands=[('identity',['-m','unittest','discover','-s','scripts/development','-p','test_current_identity.py','-v']),('native-readiness',['-m','unittest','discover','-s','scripts/ci','-p','test_native_interop_readiness.py','-v']),('sample-contracts',['-m','unittest','discover','-s','scripts/development','-p','test_nav_sample_contracts.py','-v']),('consumer',['-m','unittest','discover','-s','tests/consumer','-p','test_*.py','-v']),('ci',['-m','unittest','discover','-s','scripts/ci','-p','test_*.py','-v'])]
rows=[]
for name,args in commands:
 command=['/usr/bin/python3','-B',*args]; start=time.monotonic()
 result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
 log=OUT/(name+'.log'); log.write_bytes(result.stdout)
 counts=re.findall(rb'^Ran (\d+) tests? in [^\n]+$',result.stdout,re.M)
 row={'name':name,'command':command,'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'methods':int(counts[-1]) if counts else None,'log':log.name,'log_sha256':sha(log),'ok':bool(re.search(rb'^OK(?: \([^\n]*\))?$',result.stdout,re.M))}; rows.append(row); print(json.dumps(row),flush=True)
 if result.returncode: break
after=snap();put('scoped-inputs-after.json',after)
put('scoped-checks.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_worktree':True,'driver_sha256':sha(Path(__file__)),'input_count':len(before),'held':before==after,'commands':rows,'passed':len(rows)==len(commands) and before==after and all(r['exit_code']==0 and r['ok'] and r['methods'] for r in rows),'native_library_or_packaged_consumer_methods_executed':0,'published_or_closed_issues':False})
sys.exit(0 if len(rows)==len(commands) and before==after and all(r['exit_code']==0 and r['ok'] and r['methods'] for r in rows) else 1)
