"""One lead-authorized local diagnostic; no live policy adoption or publication."""
from pathlib import Path
import datetime as dt, hashlib, json, os, re, shutil, sys
ROOT=Path('/root/projects/nativeCmpKit')
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests
RUN=ROOT/'build/wasm-tooling-runtime-001'
PROPOSAL=ROOT/'scripts/dependencies/yarn/tooling-receipt-init-proposal-v2.md'
EXPECTED='e1697dc6345bc9e5fb4f2b78a2f3ea86f796929184e272fdfc634afbc32d338d'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def write(p,data):
 with p.open('x') as f:json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
assert not RUN.exists() and sha(PROPOSAL)==EXPECTED
assert os.environ.get('JAVA_HOME')=='/usr/lib/jvm/java-17-openjdk-amd64'
assert (ROOT/'scripts/ci/library_tests.py').is_file()
scoped=ROOT/'docs/development/evidence/build/yarn-fixtures/wasm-tooling-init-scope-review002.json'
scope=json.loads(scoped.read_text())
for name,rec in scope['input_hashes'].items():
 q=Path(name);q=q if q.is_absolute() else ROOT/q
 assert sha(q)==(rec['sha256'] if isinstance(rec,dict) else rec)
review=ROOT/'docs/development/evidence/review/dependency-tooling-independent.json'
r=json.loads(review.read_text())['wasm_tooling_init_scope_review']['corrected_proposal']
assert r['sha256']==EXPECTED and r['scope_decision'].startswith('GREEN for source-only')
tools=json.loads((ROOT/'docs/development/evidence/build/yarn-materialization-003/tools-and-processes.json').read_text())['tools']
toolmap={t['path']:t['sha256'] for t in tools if 'path' in t}
assert all(sha(Path(p))==h for p,h in toolmap.items())
before=library_tests.snapshot_inputs(ROOT)
assert before==json.loads((ROOT/'docs/development/evidence/js-full-003/inputs-after.json').read_text())
assert not (ROOT/'build/ci-verification/.library-tests.lock').exists()
blocks=re.findall(r'```groovy\n(.*?)\n```',PROPOSAL.read_text(),flags=re.S)
assert len(blocks)==1 and blocks[0].count('/REPLACE_WITH_LEAD_ALLOCATED_ABSOLUTE_RUN_ROOT')==1
RUN.mkdir();(RUN/'receipts').mkdir()
script=RUN/'observe-tooling.init.gradle'
script.write_text(blocks[0].replace('/REPLACE_WITH_LEAD_ALLOCATED_ABSOLUTE_RUN_ROOT',str(RUN))+'\n')
command=['./gradlew',':kotlinWasmToolingSetup','--rerun-tasks','--no-daemon','--no-parallel',
 '--no-configuration-cache','--no-build-cache','--max-workers=2','--console=plain','--info',
 '-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8','-Pkotlin.compiler.execution.strategy=in-process',
 '-Pkotlin.user.home='+str(RUN/'kotlin-user-home'),'--init-script',str(script)]
write(RUN/'inputs-before.json',before)
extra={str(p):sha(p) for p in [PROPOSAL,script,Path(__file__),ROOT/'scripts/ci/library_tests.py',scoped]}
extra.update(toolmap)
context={'schema_version':1,'created_utc':utc(),'source_revision':library_tests.git_revision(ROOT),
 'dirty_source':True,'command':command,'cwd':str(ROOT),'timeout_seconds':300,'reserve_mib':8192,
 'free_bytes_before':shutil.disk_usage(ROOT).free,'selected_input_count':len(before),
 'extra_inputs':extra,'review_at_start':{'path':str(review.relative_to(ROOT)),'sha256':sha(review),
 'decision':r['scope_decision']},'kotlin_home_existed_before':False,
 'library_tests_executed':0,'policy_adopted':False,'publication_or_remote_mutation':False,
 'scope':'One cold task-owned Wasm tooling install diagnostic. Shared Gradle/Yarn/host caches are not isolated; no egress sandbox or independent provenance claim.'}
write(RUN/'context.json',context)
start=utc();execution=library_tests.execute(ROOT,command,RUN/'gradle-info.log',300,8192);end=utc()
after=library_tests.snapshot_inputs(ROOT);write(RUN/'inputs-after.json',after)
changed=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
extra_changes=[p for p,h in extra.items() if not Path(p).is_file() or sha(Path(p))!=h]
receipt_files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in (RUN/'receipts').iterdir() if p.is_file()}
log=(RUN/'gradle-info.log').read_text(errors='replace').splitlines()
allowed=[':kotlinWasmToolingSetup',':kotlinWasmNodeJsSetup',':kotlinWasmYarnSetup']
task_lines=[l for l in log if l.startswith('> Task ')]
output_files=[]
home=RUN/'kotlin-user-home'
base=home/'kotlin-npm-tooling/yarn'
if base.is_dir():
 for dest in sorted(base.iterdir()):
  if dest.is_dir() and not dest.is_symlink() and re.fullmatch(r'[a-fA-F0-9]{32}',dest.name):
   for rel in ['package.json','yarn.lock','node_modules/.yarn-integrity']:
    p=dest/rel
    if p.is_file() and not p.is_symlink():
     output_files.append({'path':str(p.relative_to(RUN)),'sha256':sha(p),'bytes':p.stat().st_size})
result={'schema_version':1,'started_utc':start,'finished_utc':end,'execution':execution,
 'selected_input_count':len(before),'changed_inputs':changed,'extra_input_changes':extra_changes,
 'source_revision_after':library_tests.git_revision(ROOT),'receipt_files':receipt_files,
 'task_lines':task_lines,'output_files':output_files,'free_bytes_after':shutil.disk_usage(ROOT).free,
 'raw_log_sha256':sha(RUN/'gradle-info.log'),'raw_log_bytes':(RUN/'gradle-info.log').stat().st_size,
 'gradle_success':execution.get('exit_code')==0 and not execution.get('stop_reason'),
 'actual_process_argv_cwd_review_pending':True,'library_tests_executed':0,
 'ordinary_dependency_policy_verified':False,'independent_provenance_verified':False,
 'adopted_init_script_or_live_policy':False,'publication_performed':False}
write(RUN/'result.json',result)
print(json.dumps({'output':str(RUN.relative_to(ROOT)),'execution':execution,'changed_inputs':changed,
 'extra_input_changes':extra_changes,'receipt_files':list(receipt_files),'output_file_count':len(output_files),
 'library_tests_executed':0},indent=2))
sys.exit(0 if result['gradle_success'] and not changed and not extra_changes else 1)
