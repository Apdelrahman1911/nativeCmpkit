"""Final bounded offline tooling and local documentation check; no publication."""
from pathlib import Path
import datetime as dt, hashlib, json, os, re, subprocess, sys, time
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/ci-policy-tooling-20261027-007'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests
PYTHON='/usr/bin/python3';DOCS=str(ROOT/'build/docs-verification/locked-002/venv/bin/python')
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):d.update(b)
 return d.hexdigest()
def snapshot():
 files={}
 raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT)
 for name in sorted(set(raw.decode().split('\0'))-set([''])):
  p=ROOT/name
  if p.is_symlink():files[name]={'kind':'symlink','target_sha256':hashlib.sha256(os.readlink(p).encode()).hexdigest()}
  elif p.is_file():files[name]={'kind':'regular','sha256':sha(p),'bytes':p.stat().st_size}
  elif not p.exists():files[name]={'kind':'deleted'}
  else:raise ValueError('Nonregular input requires review')
 return files
def put(name,obj):
 with (OUT/name).open('x') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
assert not OUT.exists() and Path(DOCS).is_file()
assert os.environ.get('TMPDIR') == '/dev/shm/nativecmpkit-preflight-20261027-007'
assert not Path('/dev/shm/nativecmpkit-preflight-20261027-007/site').exists()
assert not (ROOT/'build/ci-verification/.library-tests.lock').exists()
OUT.mkdir();before=snapshot();put('inputs-before.json',before)
commands=[('inventory',[PYTHON,'-B','scripts/audit/source_inventory.py','--check'],180),
 ('audit-structure',[PYTHON,'-B','scripts/audit/validate_audit.py'],180),
 ('migration-integrity',[PYTHON,'-B','scripts/migration/verify_migration.py'],240),
 ('resolution-index',[PYTHON,'-B','scripts/development/validate_resolutions.py','--check'],180),
 ('icon-generation',[PYTHON,'-B','scripts/development/generate_icon_catalogues.py','--check'],180)]
for name,folder,pattern in [('audit','scripts/audit','test_*.py'),('migration','scripts/migration','test_*.py'),
 ('development','scripts/development','test_*.py'),('upstream-sync','scripts/development','upstream_sync_tests.py'),
 ('ci','scripts/ci','test_*.py'),('native-packaging','scripts/native','test_*.py'),
 ('dependency-core','scripts/dependencies','test_integrity.py'),('dependency-observer','scripts/dependencies','test_runtime_witness.py'),
 ('yarn-fixtures','scripts/dependencies/yarn','test_raw_yarn_fixtures.py'),
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
print('Current documentation lock/provenance inputs match; '+str(len(items))+' selected installed docs distributions match exact versions. This is not independent provenance.')
"""
commands.extend([('docs-installed-versions',[DOCS,'-B','-c',code],60),
 ('docs-pip-check',[DOCS,'-B','-m','pip','--disable-pip-version-check','check'],90),
 ('mkdocs-strict',[DOCS,'-B','-m','mkdocs','build','--strict','--site-dir','/dev/shm/nativecmpkit-preflight-20261027-007/site'],300),
 ('actionlint', ['/tmp/nativecmpkit-actionlint-1.7.12/actionlint', '.github/workflows/gradle.yml', '.github/workflows/build-native-libs.yml'],60),
 ('diff-whitespace',['git','diff','--check'],60)])
results=[];started=dt.datetime.now(dt.timezone.utc).isoformat();revision=library_tests.git_revision(ROOT)
for i,(name,argv,limit) in enumerate(commands):
 log=OUT/(str(i).zfill(2)+'-'+name+'.log');start=dt.datetime.now(dt.timezone.utc).isoformat()
 result=library_tests.execute(ROOT,argv,log,limit,8192)
 s=log.read_text(errors='replace') if log.exists() else ''
 count=re.findall(r'^Ran (\d+) tests? in [^\n]+$',s,re.M)
 row={'name':name,'command':argv,'started_utc':start,'finished_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
 'execution':result,'log':str(log.relative_to(ROOT)),'log_sha256':sha(log) if log.exists() else None,
 'unittest_count':int(count[-1]) if count else None,
 'unittest_summary_ok':bool(re.search(r'^OK(?: \([^\n]*\))?$',s,re.M)) if '-m' in argv and 'unittest' in argv else None}
 results.append(row);print(json.dumps({k:row[k] for k in ['name','execution','unittest_count','unittest_summary_ok']}),flush=True)
 if result.get('stop_reason'):break
end=dt.datetime.now(dt.timezone.utc).isoformat();after=snapshot();put('inputs-after.json',after)
changes=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p));revision_after=library_tests.git_revision(ROOT)
record={'schema_version':1,'source_revision':revision,'source_revision_after':revision_after,'dirty_worktree':True,
 'started_utc':started,'finished_utc':end,'driver_sha256':sha(Path(__file__)),
 'source_input_count':len(before),'changed_inputs':changes,'commands_requested':len(commands),'commands_completed':len(results),
 'results':results,'passed':len(results)==len(commands) and not changes and revision_after==revision and all(r['execution']['exit_code']==0 and not r['execution'].get('stop_reason') for r in results),
 'python_unittest_executions':sum(r['unittest_count'] or 0 for r in results),
 'library_or_native_or_consumer_methods_executed':0,'hosted_ci_or_publication_performed':False,
 'scope':'Source-bound offline tooling fixtures, migration/archive integrity, index/generator checks and local strict MkDocs. Test counts are Python tooling, not Kotlin/native/package-consumer passes. Docs dependency versions are scoped installed observations, not independently reviewed trust.'}
put('checks.json',record);print(json.dumps({'passed':record['passed'],'commands':len(results),'python_tests':record['python_unittest_executions'],'changed_inputs':changes,'record':str((OUT/'checks.json').relative_to(ROOT))},indent=2))
sys.exit(0 if record['passed'] else 1)
