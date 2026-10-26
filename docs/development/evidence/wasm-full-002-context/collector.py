"""Read-only, additive browser-run context collection; never a dependency/release attestation."""
from pathlib import Path
import datetime as dt, hashlib, json, re, sys
ROOT=Path('/root/projects/nativeCmpKit')
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests
name=sys.argv[1]
assert name in {'wasm-full-002','js-full-004'}
raw=ROOT/'build/ci-verification'/name
archive=ROOT/'docs/development/evidence'/name
launch=ROOT/('build/browser-launch-context-'+name)
dest=ROOT/('docs/development/evidence/'+name+'-context')
assert not dest.exists()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
r=json.loads((raw/'receipt.json').read_text())
c=json.loads((launch/'launcher.json').read_text())
x=json.loads((launch/'result.json').read_text())
before=json.loads((raw/'inputs-before.json').read_text());after=json.loads((raw/'inputs-after.json').read_text())
assert before==after and library_tests.snapshot_inputs(ROOT)==after
assert library_tests.input_digest(before)==c['selected_input_digest']
assert library_tests.input_digest(after)==x['selected_input_digest_after']
assert sha(raw/'receipt.json')==x['helper_receipt_sha256']==sha(archive/'receipt.json')
assert x['source_revision_after']==r['source_revision_after']==r['source_revision']
assert c['suite']==r['suite'];suite=r['suite']
start=dt.datetime.fromisoformat(r['started_at_utc']).timestamp();end=dt.datetime.fromisoformat(r['finished_at_utc']).timestamp()
expected=c['expected_tooling_destination'];observations=[];errors=[];all_roots=set()
dest.mkdir(parents=True)
for n in ['launcher.json','result.json','launcher-script.py']:
 with (dest/n).open('xb') as f:f.write((launch/n).read_bytes())
for m in r['modules']:
 if not m['executed']:continue
 task='wasmJsBrowserTest' if suite=='wasm' else 'jsBrowserTest'
 project=m['task'].removesuffix(':'+task).strip(':').replace(':','-')
 p=ROOT/'build'/('wasm' if suite=='wasm' else 'js')/'packages'/('nativeCmpkit-'+project+'-test')/'karma.conf.js'
 try:
  assert p.is_file() and not p.is_symlink() and p.stat().st_size<2*1024*1024
  s=p.read_text();prefix=re.match(r'\s*module\.exports = function\(config\) \{\s*config\.set\(',s);assert prefix
  tail=s[prefix.end():].lstrip();data,offset=json.JSONDecoder().raw_decode(tail);assert tail[offset:].lstrip().startswith(');')
  refs=[data[k] for k in ['customContextFile','customDebugFile'] if k in data]+data['files']
  assert all(isinstance(ref,str) for ref in refs)
  roots={ref.split('/node_modules/',1)[0] for ref in refs if '/node_modules/' in ref};all_roots.update(roots)
  selected={k:data[k] for k in ['basePath','files','frameworks','browsers','customContextFile','customDebugFile','preprocessors'] if k in data}
  q=dest/'configs'/project/'config-selected.json';put(q,selected)
  fresh=start-2<=p.stat().st_mtime<=end+2
  if not fresh:errors.append({'module':m['module'],'error':'Generated config outside run time interval'})
  if suite=='wasm' and roots!={expected}:errors.append({'module':m['module'],'error':'Generated tooling root differs from requested prepared home'})
  observations.append({'module':m['module'],'task':m['task'],'raw_config':str(p.relative_to(ROOT)),'raw_sha256':sha(p),'mtime_utc':dt.datetime.fromtimestamp(p.stat().st_mtime,dt.timezone.utc).isoformat(),'within_run_interval':fresh,'selected_first_literal_config':str(q.relative_to(dest)),'selected_sha256':sha(q),'node_modules_roots':sorted(roots),'total_config_set_occurrences':s.count('config.set(')})
 except (OSError,AssertionError,ValueError,KeyError,TypeError) as e:
  errors.append({'module':m['module'],'error':'Unable to verify generated config','error_type':type(e).__name__})
extra_changes_now=sorted(p for p,h in x['extra_inputs_after'].items() if not Path(p).is_file() or sha(Path(p))!=h)
selected_tooling_paths=[p for p in c['extra_inputs_before'] if expected and p.startswith(expected+'/')]
prepared_unchanged=bool(selected_tooling_paths) and all(c['extra_inputs_before'][p]==x['extra_inputs_after'][p] for p in selected_tooling_paths)
summary={'schema_version':1,'collected_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Additive launcher and fresh generated Karma-config observation. No runtime rerun, dependency-policy adoption or alteration of prior evidence.','archive':str((archive/'archive.json').relative_to(ROOT)),'archive_sha256':sha(archive/'archive.json'),'suite':suite,'command':r['command'],'execution':r['execution'],'library_gate_passed':r['passed'],'passed_cases':r['totals']['passed'],'modules_requested':len(r['modules']),'modules_executed':sum(m['executed']>0 for m in r['modules']),'launcher_context_sha256':sha(dest/'launcher.json'),'launcher_result_sha256':sha(dest/'result.json'),'selected_source_input_count':len(after),'selected_sources_unchanged':True,'requested_tooling_destination':expected,'observed_node_modules_roots':sorted(all_roots),'config_observations':observations,'config_review_errors':errors,'requested_prepared_home_used_in_fresh_configs':(bool(observations) and not errors and all_roots=={expected}) if suite=='wasm' else None,'selected_prepared_tooling_file_count':len(selected_tooling_paths),'selected_prepared_tooling_files_unchanged_across_run':prepared_unchanged if suite=='wasm' else None,'extra_input_changes_during_run':x['extra_input_changes'],'extra_input_changes_at_collection':extra_changes_now,'limitations':['Generated configs bind selected launcher/tooling paths, not the entire installed dependency graph or every running-process byte.','Only the first literal config.set JSON was parsed; later executable webpack/plugin configuration is not represented by those selected fields.','Selected Chrome binaries, wrapper, locks and tooling files were hashed; shared caches and arbitrary transitive code are not hermetically attested.','Existing source/common/stub/DOM test passes do not certify native dialogs, cameras, Apple/Windows/minimum runtimes, Maven consumers, ABI, dependency integrity, or release readiness.','No remote Actions, issue update, commit, staging, Pages, package or release operation.']}
put(dest/'context-review.json',summary)
with (dest/'collector.py').open('xb') as f:f.write(Path(__file__).read_bytes())
paths=sorted(p for p in dest.rglob('*') if p.is_file())
with (dest/'SHA256SUMS').open('x') as f:f.write(''.join(f'{sha(p)}  {p.relative_to(dest).as_posix()}\n' for p in paths))
print(json.dumps({'archive':str(dest.relative_to(ROOT)),'sha256':sha(dest/'context-review.json'),'config_count':len(observations),'errors':errors,'prepared_home_used':summary['requested_prepared_home_used_in_fresh_configs'],'extra_input_changes':extra_changes_now,'bound_files':len(paths)},indent=2))
sys.exit(1 if errors or extra_changes_now else 0)
