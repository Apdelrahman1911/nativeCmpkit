"""Contained lead-only browser diagnostics; fixed suites, no remote/publication commands."""
from pathlib import Path
import datetime as dt, hashlib, json, os, re, subprocess, sys, time
ROOT=Path('/root/projects/nativeCmpKit')
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def put(p,value):
 with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')

name=sys.argv[1]
assert name in {'wasm-full-004','js-full-004'}
suite={'wasm-full-004':'wasm','js-full-004':'js'}[name]
context_dir=ROOT/('build/browser-launch-context-'+name)
output=ROOT/'build/ci-verification'/name
assert not output.exists() and not context_dir.exists()
assert not (ROOT/'build/ci-verification/.library-tests.lock').exists()
assert library_tests.git_revision(ROOT)=='94d2492e99d5cbc060409d94d9f88febd06222d5'
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='development/preview-hardening'
assert sha(ROOT/'scripts/ci/library_tests.py')=='8098c11ba7c5e0d43c0b320227e1695798726c06758d2c699adcf316112817a6'
wrapper=ROOT/'build/browser-runtime-001/chrome-for-library-tests'
browser_context=ROOT/'build/browser-runtime-001/context.json'
extra={str(browser_context):sha(browser_context),str(Path(__file__)):sha(Path(__file__))}
for item in json.loads(browser_context.read_text())['paths']:
 p=Path(item['path']);assert sha(p)==item['sha256'];extra[str(p)]=sha(p)
home='build/wasm-tooling-runtime-001/kotlin-user-home'
tooling=ROOT/home/'kotlin-npm-tooling/yarn/9c7852378f220e63c4f92e7d93026c2f'
if suite=='wasm':
 assert tooling.is_dir()
 for rel in ['package.json','yarn.lock','node_modules/kotlin-web-helpers/dist/kotlin-test-karma-runner.js','node_modules/kotlin-web-helpers/dist/static/context.html','node_modules/kotlin-web-helpers/dist/static/debug.html']:
  p=tooling/rel;extra[str(p)]=sha(p)
command=[sys.executable,'scripts/ci/library_tests.py','run','--suite',suite,'--output',str(output.relative_to(ROOT)),'--timeout','600','--reserve-mib','8192']
if suite=='wasm':command+=['--kotlin-user-home',home]
env=os.environ.copy();env['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';env['PATH']=env['JAVA_HOME']+'/bin:/root/.cargo/bin:'+env.get('PATH','');env['CHROME_BIN']=str(wrapper)
legacy_env_key='ORG_GRADLE_PROJECT_kotlin.user.home';env.pop(legacy_env_key,None)
before=library_tests.snapshot_inputs(ROOT);context_dir.mkdir(parents=True)
context={'schema_version':1,'created_utc':utc(),'suite':suite,'source_revision':library_tests.git_revision(ROOT),'dirty_source':True,'command':command,'selected_input_count':len(before),'selected_input_digest':library_tests.input_digest(before),'extra_inputs_before':extra,'explicit_nonsecret_context':{'JAVA_HOME':env['JAVA_HOME'],'CHROME_BIN':env['CHROME_BIN'],'cargo_directory_prepended_to_PATH':True,'legacy_environment_property_absent_in_child':legacy_env_key},'requested_kotlin_user_home':home if suite=='wasm' else None,'expected_tooling_destination':str(tooling) if suite=='wasm' else None,'scope':'One fixed bounded local browser diagnostic. Requested home is not effective-use proof; inspect fresh generated Karma configs. Selected dependency files and browser executables only, not whole-tree/process or independent provenance attestation. No remote CI, issue mutation, commit, release or publication.'}
put(context_dir/'launcher.json',context)
started=utc();clock=time.monotonic();run=subprocess.run(command,cwd=ROOT,env=env);ended=utc()
after=library_tests.snapshot_inputs(ROOT);extra_after={p:sha(Path(p)) if Path(p).is_file() else None for p in extra}
result={'schema_version':1,'started_utc':started,'finished_utc':ended,'exit_code':run.returncode,'elapsed_seconds':round(time.monotonic()-clock,3),'source_revision_after':library_tests.git_revision(ROOT),'selected_input_count_after':len(after),'selected_input_digest_after':library_tests.input_digest(after),'selected_changes':sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p)),'extra_inputs_after':extra_after,'extra_input_changes':sorted(p for p in extra if extra[p]!=extra_after[p]),'helper_receipt':str((output/'receipt.json').relative_to(ROOT)) if (output/'receipt.json').is_file() else None,'helper_receipt_sha256':sha(output/'receipt.json') if (output/'receipt.json').is_file() else None,'effective_tooling_home_verified_by_launcher':False}
put(context_dir/'result.json',result)
(context_dir/'launcher-script.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'launcher_context':str(context_dir.relative_to(ROOT)),'exit_code':run.returncode,'selected_changes':result['selected_changes'],'extra_input_changes':result['extra_input_changes']},indent=2),flush=True)
sys.exit(run.returncode or (1 if result['selected_changes'] or result['extra_input_changes'] else 0))
