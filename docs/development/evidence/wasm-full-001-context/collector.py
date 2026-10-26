from pathlib import Path
import json,hashlib,datetime as dt,re
root=Path('/root/projects/nativeCmpKit');raw=root/'build/ci-verification/wasm-full-001';dst=root/'docs/development/evidence/wasm-full-001-context'
assert set(p.name for p in dst.iterdir())=={'launcher.json','collection-attempt001.json'}
receipt=json.loads((raw/'receipt.json').read_text());launch=root/'build/wasm-browser-context-001/launcher.json';context=json.loads(launch.read_text());assert (dst/'launcher.json').read_bytes()==launch.read_bytes()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
start=dt.datetime.fromisoformat(receipt['started_at_utc']).timestamp();end=dt.datetime.fromisoformat(receipt['finished_at_utc']).timestamp()
observations=[];dirs=set()
for m in receipt['modules']:
 if not m['executed']:continue
 project=m['task'].removesuffix(':wasmJsBrowserTest').strip(':').replace(':','-')
 p=root/'build/wasm/packages'/('nativeCmpkit-'+project+'-test')/'karma.conf.js'
 s=p.read_text();prefix=re.match(r'\s*module\.exports = function\(config\) \{\s*config\.set\(',s);assert prefix
 tail=s[prefix.end():].lstrip();data,offset=json.JSONDecoder().raw_decode(tail);assert tail[offset:].lstrip().startswith(');')
 refs=[data['customContextFile'],data['customDebugFile'],*data['files']]
 roots={x.split('/node_modules/',1)[0] for x in refs if '/kotlin-npm-tooling/yarn/' in x};assert len(roots)==1;dirs.update(roots)
 assert start-2<=p.stat().st_mtime<=end+2
 picked={k:data[k] for k in ['basePath','files','frameworks','browsers','customContextFile','customDebugFile','preprocessors']}
 out=dst/'configs'/project/'config-selected.json';out.parent.mkdir(parents=True)
 with out.open('x') as f:json.dump(picked,f,indent=2);f.write('\n')
 observations.append({'module':m['module'],'task':m['task'],'raw_config':str(p.relative_to(root)),'raw_sha256':sha(p),'mtime_utc':dt.datetime.fromtimestamp(p.stat().st_mtime,dt.timezone.utc).isoformat(),'within_run_interval':True,'selected_first_literal_config':str(out.relative_to(dst)),'selected_sha256':sha(out),'tooling_root':next(iter(roots)),'total_config_set_occurrences':s.count('config.set(')})
assert len(observations)==14
assert dirs=={'/root/.kotlin/kotlin-npm-tooling/yarn/9c7852378f220e63c4f92e7d93026c2f'}
expected=Path(context['expected_tooling_destination']);actual=Path(next(iter(dirs)))
comparisons=[]
for rel in ['package.json','yarn.lock','node_modules/kotlin-web-helpers/dist/kotlin-test-karma-runner.js','node_modules/kotlin-web-helpers/dist/static/context.html','node_modules/kotlin-web-helpers/dist/static/debug.html']:
 a=actual/rel;b=expected/rel;comparisons.append({'relative_path':rel,'observed_default_path':str(a),'observed_sha256':sha(a),'prepared_path':str(b),'prepared_sha256':sha(b),'bytes_equal':a.read_bytes()==b.read_bytes()})
summary={'schema_version':1,'collected_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Additive launcher/tooling-context observation for first failed full Wasm library run; no runtime rerun, policy adoption or altered original receipt.',
 'archive':'docs/development/evidence/wasm-full-001/archive.json','archive_sha256':sha(root/'docs/development/evidence/wasm-full-001/archive.json'),
 'actual_execution':receipt['execution'],'actual_passed_cases':receipt['totals']['passed'],'modules_executed':14,'modules_requested':19,
 'intended_environment_property':context['explicit_nonsecret_gradle_project_environment_property'],
 'intended_tooling_root':str(expected),'observed_generated_karma_tooling_roots':sorted(dirs),
 'intended_cold_tooling_reuse_verified':False,'mismatch_root_cause_established':False,
 'config_observations':observations,'selected_local_output_byte_comparisons':comparisons,
 'current_sources_revalidated_by_this_supplement':False,
 'earlier_collector_failure':'collection-attempt001.json',
 'limitations':['The environment-variable intention did not bind the generated Karma paths. Do not claim the cold prepared home supplied this test run.',
 'All14 fresh generated configs name the default /root/.kotlin tooling path. Exactly five selected manifest/lock/runner/context files were compared, not entire installed dependency trees or running-process bytes.',
 'The cause of the property-path mismatch is not established by this check. Later runs should pass the already observed -Pkotlin.user.home explicitly and recheck generated configs.',
 'Recorded211 passing library cases remain real; the command failed IO/WebView compilation and5 requested modules produced no tests.',
 'The first literal config.set JSON was selected; later webpack/plugin configuration code is not represented by those selected fields.',
 'No independent dependency trust, script-suppression, frozen/closure enforcement, native, Maven consumer or release gate passed.']}
with (dst/'context-review.json').open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
(dst/'collector.py').write_bytes(Path(__file__).read_bytes())
files=sorted(p for p in dst.rglob('*') if p.is_file());(dst/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(dst).as_posix()}\n' for p in files))
print(json.dumps({'archive':str(dst.relative_to(root)),'summary_sha256':sha(dst/'context-review.json'),'configs':len(observations),'intended_home_reuse_verified':False,'selected_comparisons_equal':all(x['bytes_equal'] for x in comparisons),'bound_files':len(files)},indent=2))
