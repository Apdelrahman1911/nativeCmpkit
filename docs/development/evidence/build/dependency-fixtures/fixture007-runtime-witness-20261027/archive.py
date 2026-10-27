"""Read-only recount of original actual007 files and exact frozen tool bytes.

No archived code/binary is executed; imports are the held current tool producer.
Original Gradle log hashes are retained alongside explicit path sanitization.
"""
from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,sys
ROOT=Path('/root/projects/nativeCmpKit');sys.path.insert(0,str(ROOT/'scripts/dependencies'))
import integrity as d,integrity_model as m,gradle_fixtures as g,runtime_witness as w
LIVE=Path('/dev/shm/nativecmpkit-build007-fixtures-007');META=ROOT/'build/dependency-fixture007-20261027-001'
OUT=ROOT/'docs/development/evidence/build/dependency-fixtures/fixture007-runtime-witness-20261027'
assert not OUT.exists();OUT.mkdir()
def regular(p):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=4*1024*1024
 return p.read_bytes()
def digest(data):return hashlib.sha256(data).hexdigest()
entries=[]
def put(name,data,original=None):
 assert not Path(name).is_absolute() and not set(Path(name).parts)&{'..','.'}
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(data)
 entries.append({'path':name,'sha256':digest(data),**({'original_sha256':digest(original),'sanitized':True} if original is not None else {})})
inputs=json.loads(regular(META/'inputs-before.json'));assert inputs==json.loads(regular(META/'inputs-after.json'))
assert inputs=={n:digest(regular(ROOT/n)) for n in inputs}
assert w.checkpoint_files()==json.loads(regular(ROOT/'scripts/dependencies/checkpoint-offline-008.json'))['input_files_sha256']
exits=json.loads(regular(META/'exits.json'));assert exits['suite_exit_code']==exits['witness_exit_code']==0 and exits['lead_guard'] is None and exits['source_inputs_held'] and min(exits['minimum_free_bytes'].values())>=8192*1024**2
f=json.loads(regular(LIVE/'fixture-results.json'));witness=json.loads(regular(Path(str(LIVE)+'-runtime-witness.json')))
assert w.fixture_matches(f) and f['selected_cases_observed_as_expected'] and not f['all_cases_observed_as_expected'] and not f['production_dependencies_verified']
assert [a['exit_code'] for a in f['invocation_attempts']]==[0,0,1,1,1,1] and len(f['invocation_attempts'])==6
assert witness['fixture_and_runtime_selected_subset_complete'] and witness['all_six_runtime_observations_complete'] and witness['fixture_selected_subset_matched']
assert witness['observation_attempts']==witness['completed_jcmd_commands']==12 and witness['maximum_jcmd_attempts']==12
assert witness['checkpoint_filename']=='checkpoint-offline-008.json' and witness['checkpoint_sha256']==w.CHECKPOINT_SHA256
assert witness['frozen_inputs']==w.checkpoint_files() and witness['frozen_inputs_unchanged'] and witness['observer_inputs_unchanged'] and witness['observer_inputs_sha256']==w.observer_files()
assert witness['helper_sha256']==inputs['scripts/dependencies/runtime_witness.py']
assert witness['java_executable_sha256']==m.file_sha256(Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java'))
assert witness['jcmd_executable_sha256']==m.file_sha256(Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/jcmd'))
assert witness['gradle_cli_jar_sha256']==m.file_sha256(Path('/opt/gradle/gradle-9.7.1/lib/gradle-gradle-cli-main-9.7.1.jar'))
assert witness['gradle_daemon_jar_sha256']==m.file_sha256(Path('/opt/gradle/gradle-9.7.1/lib/gradle-daemon-main-9.7.1.jar'))
assert not witness['raw_properties_or_environment_archived'] and not witness['wrapper_client_observed'] and not witness['non_gradle_cache_use_verified'] and not witness['gradle_started_or_stopped_by_witness']
assert [s['case'] for s in witness['cases']]==list(w.CASE_NAMES)
put('fixture-results.json',regular(LIVE/'fixture-results.json'));put('runtime-witness.json',regular(Path(str(LIVE)+'-runtime-witness.json')))
for name in ('preflight.json','inputs-before.json','inputs-after.json','launch.json','exits.json','suite-stdout.json','witness-stdout.json','driver.py','archive.py'):put(name,regular(META/name))
for name,sha in inputs.items():
 data=regular(META/'inputs'/name);assert digest(data)==sha;put('tool-inputs/'+name,data)
pairs=[];reviews=[]
for index,state in enumerate(witness['cases']):
 case=state['case'];base=LIVE/case;mode='bootstrap' if case=='bootstrap' else 'check'
 marker=d.load_workspace(base);run=base/f'build/dependency-integrity/{mode}'
 launch=json.loads(regular(run/'launched-process.json'));runtime=json.loads(regular(run/'graphs/root/runtime.json'));result=json.loads(regular(run/'result.json'))
 assert state['source_input_digest']==marker['source_input_digest']==result['source_input_digest']
 assert state['launcher_receipt_sha256']==digest(regular(run/'launched-process.json'))
 assert state['runtime_candidate_sha256']==state['runtime_receipt_sha256']==digest(regular(run/'graphs/root/runtime.json'))
 assert state['runtime_receipt_matched'] and w.runtime_matches(runtime,marker,mode,state['daemon'])
 assert state['client_children_inventory_complete'] is False and state['daemon_candidate_sources']==['exact-fixture-runtime']
 assert set(state['validation_reason_counts'])=={'daemon-children','runtime-candidate'}
 assert set(state['validation_reason_counts']['daemon-children'])=={'client-children-unavailable','no-eligible-daemon-at-poll'}
 assert set(state['validation_reason_counts']['runtime-candidate'])=={'runtime-receipt-not-ready'}
 assert not state['validation_reason_counts_saturated'] and all(0<n<=1024 for stage in state['validation_reason_counts'].values() for n in stage.values())
 client,daemon=state['client'],state['daemon'];ci,di=client['identity'],daemon['identity'];si=witness['suite_identity']
 assert ci['pid']==launch['pid'] and ci['parent_pid']==si['pid']==exits['suite_pid'] and ci['pid']==ci['process_group']==ci['session'] and ci['start_ticks']>=si['start_ticks']
 assert di['pid']==runtime['gradle_jvm_process_id'] and di['parent_pid']==ci['pid'] and di['pid']==di['process_group']==di['session'] and di['pid']!=ci['pid'] and di['start_ticks']>=ci['start_ticks']
 for obs in (client,daemon):
  assert obs['observed'] and obs['attempted'] and obs['executable_and_gradle_command_checked'] and obs['pidfd_live_before_and_after']
  assert obs['selected_values_match'] and obs['environment_values_matched'] and obs['properties']==m.JVM_PRIVATE_PATHS and obs['environment']==m.ENV_PRIVATE_PATHS
  assert obs['property_matches']==dict.fromkeys(m.JVM_PRIVATE_PATHS,True) and w.JDK_VERSION.fullmatch(obs['java_runtime_version'])
  assert obs['diagnostic']['exit_code']==0 and 0<=obs['diagnostic']['elapsed_seconds']<7 and obs['diagnostic']['stdout_bytes']+obs['diagnostic']['stderr_bytes']<=w.MAX_DIAGNOSTIC
  assert not obs['diagnostic']['raw_stdout_archived'] and not obs['diagnostic']['raw_stderr_archived'] and not obs['actual_cache_consumption_verified']
  assert not Path(f'/proc/{obs["identity"]["pid"]}').exists(),'Recorded PID still exists; do not signal or delete its workspace'
 pairs.append([ci['pid'],di['pid']]);binary={}
 for name,sha in marker['source_files'].items():
  data=regular(base/name);assert digest(data)==sha
  if name.startswith('scripts/dependencies/'):
   assert name in inputs and sha==inputs[name] and data==regular(OUT/'tool-inputs'/name)
  elif name.endswith('.jar'):
   module,version=Path(name).parent.parent.name,Path(name).parent.name
   assert data==g.jar_bytes(module,version)
   binary[name]={'sha256':sha,'size_bytes':len(data),'deterministic_generator':'gradle_fixtures.jar_bytes'}
  else:put(case+'/'+name,data)
 put(case+'/candidate-inputs.json',regular(base/d.MARKER))
 for prefix in ('gradle','build/dependency-integrity'):
  for p in sorted((base/prefix).rglob('*')):
   if not p.is_file() or p.is_symlink():continue
   name=p.relative_to(base).as_posix()
   if p.suffix not in ('.json','.lockfile','.xml','.log'):continue
   data=regular(p);original=None
   if p.suffix=='.log':
    original=data;data=data.replace(str(base).encode(),b'<candidate>').replace(b'/opt/gradle/gradle-9.7.1',b'<installed-gradle-9.7.1>')
   put(case+'/'+name,data,original)
 put(case+'/binary-input-hashes.json',m.json_bytes(binary))
 assert result['execution']['exit_code']==(0 if index<2 else 1) and not result['execution'].get('reason')
 assert result['execution']['process_started'] and result['execution']['reserve_mib']==8192 and result['execution']['timeout_seconds']==90 and min(result['execution']['free_bytes_before'],result['execution']['free_bytes_after'])>=8192*1024**2
 if case!='bootstrap':
  original=next(c for c in f['cases'] if c['case']==case);recount=g.classify(base,case,result);assert original==recount
  reviews.append({'case':case,'gradle_exit_code':original['gradle_exit_code'],'result_kind':original['result_kind'],'actual_expected_result_observed':original['actual_expected_result_observed'],'lock_evidence':original.get('lock_evidence')})
assert witness['fixture_result_sha256']==digest(regular(LIVE/'fixture-results.json'))
assert inputs=={n:digest(regular(ROOT/n)) for n in inputs}
summary={'schema_version':1,'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision_before_documenting':'be32a7d61bdf025cf1a115aea9ac07c8062f3623','source_tree_dirty':True,'scope':'Lead read-only reclassification/source/hash/receipt review of six actual plugin-free isolated Gradle9.7.1/JDK17 invocations and twelve distinct client/daemon selected-property observations. Not production acquisition, artifact trust, a library/native/packaged consumer test or an immutable release candidate.','evidence_integrity_passed':True,'core008_manifest_unchanged':True,'current_inputs_held_before_execution_and_after_archive':True,'suite_exit_code':0,'suite_elapsed_seconds':f['elapsed_seconds'],'witness_exit_code':0,'witness_elapsed_seconds':witness['elapsed_seconds'],'actual_gradle_invocations':6,'actual_gradle_exit_codes':[a['exit_code'] for a in f['invocation_attempts']],'cases_reclassified_against_original_bytes':reviews,'actual_client_observations':6,'actual_daemon_observations':6,'completed_jcmd_commands':12,'all_six_runtime_bindings_passed':True,'selected_fixture_and_runtime_scope_passed':True,'child_inventories_unknown_not_known_empty':6,'daemon_direct_exact_client_parent_and_self_group_session':6,'client_daemon_runtime_pid_pairs':pairs,'all_recorded_owned_pids_absent_at_review':True,'suite_and_witness_python_reaped':True,'fresh_per_case_cache':True,'raw_environment_or_jcmd_properties_archived':False,'no_global_pid_scan_or_guessed_pid':True,'no_automatic_failed_attach_retry':True,'owned_disk_reserve_mib':8192,'minimum_free_bytes':exits['minimum_free_bytes'],'library_native_or_packaged_consumer_methods_executed':0,'all_case_coverage':False,'ordinary_build_policy_installed':False,'wrapper_client_observed':False,'non_gradle_cache_consumption_verified':False,'production_dependencies_verified':False,'independent_trust_reviewed':False,'release_readiness_certified':False,'original_failed_results_rewritten':False,'issues_closed':0,'publication_performed':False,'timeout_cleanup_limitation':'Successful normal exits and exact recorded PID absence only. Actual daemon-self group/session means the original client-process-group termination is not proof that a daemon would be killed after timeout/interruption. No timeout/hostile plugin/native cache/RSS/network/filesystem sandbox or unrelated-process exclusion under forced cleanup is certified by this run.','archive_script_sha256':digest(regular(Path(__file__))),'entries':entries}
put('lead-independent-review.json',m.json_bytes(summary))
(OUT/'SHA256SUMS').write_text(''.join(f'{digest(p.read_bytes())}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({k:summary[k] for k in ('evidence_integrity_passed','suite_exit_code','actual_gradle_exit_codes','completed_jcmd_commands','all_six_runtime_bindings_passed','all_recorded_owned_pids_absent_at_review')},indent=2))
# Cleanup is a separate additive receipt, after the read-only review succeeds.
assert LIVE.parent==Path('/dev/shm') and not LIVE.is_symlink() and LIVE.resolve()==LIVE
assert not any(Path(f'/proc/{pid}').exists() for pair in pairs for pid in pair)
shutil.rmtree(LIVE)
for suffix,target in [('-runtime-witness.json','runtime-witness.json'),('-suite-stdout.json','suite-stdout.json'),('-witness-stdout.json','witness-stdout.json')]:
 p=Path(str(LIVE)+suffix);assert regular(p)==regular(OUT/target);p.unlink()
cleanup={'observed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'owned_tmpfs_fixture_and_three_outputs_removed':not LIVE.exists() and not any(Path(str(LIVE)+suffix).exists() for suffix in ('-runtime-witness.json','-suite-stdout.json','-witness-stdout.json')),'all_recorded_client_daemon_pids_absent_after_cleanup':not any(Path(f'/proc/{pid}').exists() for pair in pairs for pid in pair),'other_projects_caches_or_processes_touched':False,'free_bytes_after':{str(p):shutil.disk_usage(p).free for p in (ROOT,Path('/dev/shm'))}}
put('owned-cleanup.json',m.json_bytes(cleanup))
(OUT/'SHA256SUMS').write_text(''.join(f'{digest(p.read_bytes())}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps(cleanup,indent=2))
