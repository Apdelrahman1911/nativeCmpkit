"""Archive completed tooling005 outcome, preserving the strict-docs failure."""
from pathlib import Path
import datetime as dt,hashlib,json,os,re,subprocess
ROOT=Path('/root/projects/nativeCmpKit');BASE=ROOT/'build/checkpoint-verification-005';DEST=ROOT/'docs/development/evidence/tooling-005'
DRIVER=Path('/tmp/nativecmpkit-checkpoint-tooling005.py')
assert not DEST.exists()
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):d.update(b)
 return d.hexdigest()
def snapshot():
 files={}
 raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT)
 for name in sorted(set(raw.decode().split('\0'))-{''}):
  p=ROOT/name
  if p.is_symlink():files[name]={'kind':'symlink','target_sha256':hashlib.sha256(os.readlink(p).encode()).hexdigest()}
  elif p.is_file():files[name]={'kind':'regular','sha256':sha(p),'bytes':p.stat().st_size}
  elif not p.exists():files[name]={'kind':'deleted'}
  else:raise ValueError('Nonregular input requires review')
 return files
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def data(p,x):put(p,(json.dumps(x,indent=2,sort_keys=True)+'\n').encode())
r=json.loads((BASE/'checks.json').read_text());before=json.loads((BASE/'inputs-before.json').read_text());after=json.loads((BASE/'inputs-after.json').read_text())
assert before==after==snapshot() and not r['changed_inputs']
assert sha(DRIVER)==r['driver_sha256'] and r['commands_completed']==r['commands_requested']==20
rows=[]
for item in r['results']:
 p=ROOT/item['log'];assert sha(p)==item['log_sha256']
 lines=p.read_text(errors='replace').splitlines()
 summaries=[x for x in lines if re.match(r'^(?:Ran [0-9]+ tests? in |OK(?:$| \()|FAILED|WARNING\s+-|ERROR\s+-|Aborted with )',x) or 'does not contain an anchor' in x]
 headers=[]
 for line in lines:
  m=re.match(r'^(test[A-Za-z0-9_]*) \(([A-Za-z0-9_.]+)\) \.\.\. (ok|ERROR|FAIL|expected failure|unexpected success)$',line)
  if m:headers.append({'method':m[1],'id':m[2],'outcome':m[3]})
 if item['unittest_count'] is not None:
  assert item['execution']['exit_code']==0 and item['unittest_summary_ok'] and 'OK' in lines
 rows.append({'name':item['name'],'raw_log':item['log'],'raw_sha256':item['log_sha256'],'raw_log_archived':False,'execution':item['execution'],'unittest_count':item['unittest_count'],'summary_and_diagnostic_lines':summaries,'exact_single_line_case_headers':headers,'header_count_is_not_the_unittest_execution_count':True})
failed=[x['name'] for x in r['results'] if x['execution']['exit_code']!=0]
assert failed==['mkdocs-strict'] and r['passed'] is False and r['python_unittest_executions']==737
DEST.mkdir(parents=True)
for filename in ('checks.json','inputs-before.json','inputs-after.json'):put(DEST/filename,(BASE/filename).read_bytes())
put(DEST/'launcher.py',DRIVER.read_bytes());data(DEST/'command-log-review.json',rows)
record={'schema_version':1,'archived_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':r['source_revision'],'dirty_worktree':True,'started_utc':r['started_utc'],'finished_utc':r['finished_utc'],'commands_requested':20,'commands_completed':20,'commands_exit_zero':19,'overall_passed':False,'failed_commands':failed,'python_unittest_executions':737,'all_python_suites_summary_ok_without_skips':True,'source_input_count':len(before),'all_inputs_unchanged_during_run_and_before_archive':True,'producer_receipt_sha256':sha(BASE/'checks.json'),'source_input_scope':'Complete nonignored Git-listed working-tree files, including unchanged baseline files, additions, deletions and symlink target hashes; distinct from the693 selected library/build inputs.','library_native_packaged_consumer_methods_executed':0,'hosted_ci_or_publication_performed':False,'scope':'Actual offline tooling and local documentation diagnostic.737 Python tooling cases passed but the20-command sweep FAILED at strict MkDocs. Do not claim this full sweep or generated site successful. Failed link diagnostics and original source snapshot retained before repairs.','limitations':['Dirty worktree at the base commit, not an immutable release candidate.','Passing Python tool fixtures are not Kotlin/native/runtime, ordinary dependency-enforcement, ABI or Maven-consumer evidence.','All raw logs remain in the task-owned build directory and are SHA256-bound; only selected structural test headers/summaries and MkDocs link diagnostics are archived, not full terminal bodies.','This evidence is created after the input snapshot and is not included in its own source-input scope. A subsequent correction or documentation update requires its own check.']}
data(DEST/'archive.json',record);put(DEST/'collector.py',Path(__file__).read_bytes())
files=sorted(p for p in DEST.rglob('*') if p.is_file());put(DEST/'SHA256SUMS',''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in files).encode())
print(json.dumps({'archive':str(DEST.relative_to(ROOT)),'sha256':sha(DEST/'archive.json'),'bound_files':len(files),'source_inputs':len(before),'python_tests':737,'overall_passed':False},indent=2))
