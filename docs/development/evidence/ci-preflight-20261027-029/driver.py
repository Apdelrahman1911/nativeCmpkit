"""Finite LIGHTWEIGHT offline preflight; no Gradle, compiler, native or publication run.

Recheck recorded root capacity; no heavy-build8GiB guard is lowered in any
build/controller. Only explicitly reviewed Python/Git/actionlint/docs checks
run here, serially, with owned TMPDIR/site output on tmpfs. Bound tmpfs reserve,
root decrease, log size, command deadline and own process group; fail fast.
"""
from pathlib import Path
import datetime as dt, hashlib, json, os, re, shutil, signal, subprocess, sys, time
ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path('/dev/shm/nativecmpkit-preflight-20261027-029')
OUT = BASE/'checks'
PYTHON='/usr/bin/python3'
DOCS=str(ROOT/'build/docs-verification/locked-002/venv/bin/python')
ROOT_BUDGET = 128*1024**2
TMPFS_RESERVE = 2*1024**3
LOG_LIMIT = 64*1024**2

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): d.update(b)
 return d.hexdigest()
def snapshot():
 files={}
 raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT,timeout=30)
 for name in sorted(set(raw.decode().split('\0'))-{''}):
  p=ROOT/name
  if p.is_symlink(): files[name]={'kind':'symlink','target_sha256':hashlib.sha256(os.readlink(p).encode()).hexdigest()}
  elif p.is_file():
   before=p.stat(); digest=sha(p); after=p.stat()
   assert (before.st_size,before.st_mtime_ns,before.st_ino,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ino,after.st_ctime_ns), 'Input changed during read'
   files[name]={'kind':'regular','sha256':digest,'bytes':before.st_size}
  elif not p.exists(): files[name]={'kind':'deleted'}
  else: raise ValueError('Nonregular input requires review')
 return files
def put(name,obj):
 with (OUT/name).open('x') as f: json.dump(obj,f,indent=2,sort_keys=True); f.write('\n')
def revision(): return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=30).strip()
def stage_digest(): return hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT,timeout=30)).hexdigest()
def stop(p):
 if p.poll() is not None:return
 try: os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError: pass
 try: p.wait(timeout=5)
 except subprocess.TimeoutExpired:
  try: os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError: pass
  p.wait(timeout=10)
def execute(argv,log,limit,initial_root_free):
 started=time.monotonic();result={}
 # This finite set is the authority boundary. No arbitrary caller-supplied tasks.
 assert argv[0] in {PYTHON,DOCS,'git','/tmp/nativecmpkit-actionlint-1.7.12/actionlint'}
 assert shutil.disk_usage(BASE).free>=TMPFS_RESERVE
 with log.open('x') as stream:
  process=subprocess.Popen(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   while process.poll() is None:
    if shutil.disk_usage(BASE).free<TMPFS_RESERVE:result['stop_reason']='Owned tmpfs reserve reached'
    elif shutil.disk_usage(ROOT).free<initial_root_free-ROOT_BUDGET:result['stop_reason']='Lightweight root-write budget reached; not the heavy-build reserve'
    elif log.stat().st_size>LOG_LIMIT:result['stop_reason']='Bounded lightweight log limit reached'
    elif time.monotonic()-started>limit:result['stop_reason']='Lightweight command deadline reached'
    if result:stop(process);break
    time.sleep(0.1)
  except BaseException:
   stop(process);raise
  result.update(exit_code=process.returncode,elapsed_seconds=round(time.monotonic()-started,3))
 return result

assert BASE.is_dir() and not BASE.is_symlink() and not OUT.exists()
assert Path(DOCS).is_file() and os.environ.get('TMPDIR')==str(BASE)
assert not (BASE/'site').exists()
OUT.mkdir();before=snapshot();put('inputs-before.json',before)
source_revision=revision();stage_before=stage_digest()
root_free=shutil.disk_usage(ROOT).free
commands=[('inventory',[PYTHON,'-B','scripts/audit/source_inventory.py','--check'],180),
 ('audit-structure',[PYTHON,'-B','scripts/audit/validate_audit.py'],180),
 ('migration-integrity',[PYTHON,'-B','scripts/migration/verify_migration.py'],240),
 ('resolution-index',[PYTHON,'-B','scripts/development/validate_resolutions.py','--check'],180),
 ('icon-generation',[PYTHON,'-B','scripts/development/generate_icon_catalogues.py','--check'],180)]
for name,folder,pattern in [('audit','scripts/audit','test_*.py'),('migration','scripts/migration','test_*.py'),
 ('development','scripts/development','test_*.py'),('upstream-sync','scripts/development','upstream_sync_tests.py'),
 ('ci','scripts/ci','test_*.py'),('native-packaging','scripts/native','test_*.py'),
 ('dependency-core','scripts/dependencies','test_integrity.py'),('dependency-observer','scripts/dependencies','test_runtime_witness.py'),
 ('dependency-owner','scripts/dependencies','test_owned_gradle.py'),('yarn-fixtures','scripts/dependencies/yarn','test_raw_yarn_fixtures.py'),
 ('consumer-tooling','tests/consumer','test_*.py'),('docs-lock-tooling','scripts/docs','test_*.py')]:
 commands.append((name,[PYTHON,'-B','-m','unittest','discover','-s',folder,'-p',pattern,'-v'],180))
code="""from pathlib import Path
import importlib.metadata as m,sys
sys.path.insert(0,'scripts/docs')
import verify_locked_environment as v
p=v.validate_provenance()
items=[a for a in p['artifacts'] if 'docs' in a['roles']]
assert items
assert all(m.version(a['name'])==a['version'] for a in items)
print('Current lock/provenance input hashes match; '+str(len(items))+' selected installed docs distributions match exact versions. This is not independent provenance.')
"""
commands.extend([('docs-installed-versions',[DOCS,'-B','-c',code],60),
 ('docs-pip-check',[DOCS,'-B','-m','pip','--disable-pip-version-check','check'],90),
 ('mkdocs-strict',[DOCS,'-B','-m','mkdocs','build','--strict','--site-dir',str(BASE/'site')],300),
 ('actionlint',['/tmp/nativecmpkit-actionlint-1.7.12/actionlint','.github/workflows/gradle.yml','.github/workflows/build-native-libs.yml'],60),
 ('cached-diff-whitespace',['git','diff','--cached','--check'],60),('diff-whitespace',['git','diff','--check'],60)])
results=[];started=utc()
for i,(name,argv,limit) in enumerate(commands):
 log=OUT/(str(i).zfill(2)+'-'+name+'.log');start=utc()
 result=execute(argv,log,limit,root_free)
 s=log.read_text(errors='replace')
 count=re.findall(r'^Ran (\d+) tests? in [^\n]+$',s,re.M)
 is_unittest='-m' in argv and 'unittest' in argv
 row={'name':name,'command':argv,'started_utc':start,'finished_utc':utc(),'execution':result,
 'log':log.name,'log_sha256':sha(log),'unittest_count':int(count[-1]) if count else None,
 'unittest_summary_ok':bool(re.search(r'^OK(?: \([^\n]*\))?$',s,re.M)) if is_unittest else None}
 results.append(row);print(json.dumps({k:row[k] for k in ['name','execution','unittest_count','unittest_summary_ok']}),flush=True)
 if result['exit_code']!=0 or result.get('stop_reason') or (is_unittest and (not row['unittest_count'] or not row['unittest_summary_ok'])):break
end=utc();after=snapshot();put('inputs-after.json',after)
changes=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
revision_after=revision();stage_after=stage_digest()
record={'schema_version':1,'source_revision':source_revision,'source_revision_after':revision_after,'dirty_worktree':True,
 'started_utc':started,'finished_utc':end,'driver_sha256':sha(Path(__file__)),'source_input_count':len(before),
 'changed_inputs':changes,'staged_index_sha256_before':stage_before,'staged_index_sha256_after':stage_after,
 'commands_requested':len(commands),'commands_completed':len(results),'results':results,
 'passed':len(results)==len(commands) and not changes and revision_after==source_revision and stage_after==stage_before and all(r['execution']['exit_code']==0 and not r['execution'].get('stop_reason') and (r['unittest_summary_ok'] is None or (r['unittest_count'] and r['unittest_summary_ok'])) for r in results),
 'python_unittest_executions':sum(r['unittest_count'] or 0 for r in results),
 'library_or_native_or_packaged_consumer_methods_executed':0,'hosted_ci_or_publication_performed':False,
 'lightweight_resource_policy':{'heavy_build8GiB_guard_lowered':False,'root_free_before':root_free,
 'root_free_after':shutil.disk_usage(ROOT).free,'maximum_root_decrease_bytes':ROOT_BUDGET,
 'owned_tmpfs_minimum_free_bytes':TMPFS_RESERVE,'tmpfs_free_after':shutil.disk_usage(BASE).free,
 'log_limit_bytes':LOG_LIMIT,'finite_command_allowlist':True,'fail_fast_on_any_nonzero':True},
 'scope':'Finite source/stage-held lightweight Python/Git/offline tooling/history/index/generator/strict local docs/actionlint only. Capacity is measured, not inferred from old prose; only owned tmpfs outputs and bounded128MiB root decrease allowed. No Gradle/compiler/native/package-consumer or publication execution. Python counts overlap prior scoped runs; not runtime/native/dependency-trust/release certification.'}
put('checks.json',record)
print(json.dumps({'passed':record['passed'],'commands':len(results),'python_tests':record['python_unittest_executions'],'changed_inputs':changes,'record':str(OUT/'checks.json')},indent=2),flush=True)
sys.exit(0 if record['passed'] else 1)
