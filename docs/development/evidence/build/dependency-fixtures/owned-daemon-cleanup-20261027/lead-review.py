"""Read-only archive/review. No JVMs, Gradle, signal, attach or archive execution."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,re,subprocess,sys,zipfile
ROOT=Path('/root/projects/nativeCmpKit');SRC=Path('/dev/shm/nativecmpkit-owned-cleanup-suite-20261027-001/cases');OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/dependencies'))
import integrity as d,integrity_model as m,runtime_witness as w,owned_cleanup_fixtures as f
frozen=m.read_json(SRC/'inputs-before.json');assert frozen==m.read_json(SRC/'inputs-after.json')==f.inputs()
result=m.read_json(SRC/'result.json');assert result['passed'] and result['actual_gradle_invocations']==5 and result['jcmd_attempts']==0
assert [r['case'] for r in result['cases']]==list(f.CASES)
selected={};log_observations=[];pids=[];waits=[]
def take(p):
 name=p.relative_to(SRC).as_posix();assert name not in selected;selected[name]=p.read_bytes()
for p in (SRC/'source').rglob('*'):
 if p.is_file():
  n=p.relative_to(SRC/'source').as_posix();assert n in frozen and m.file_sha256(p)==frozen[n];take(p)
assert set(p.relative_to(SRC/'source').as_posix() for p in (SRC/'source').rglob('*') if p.is_file())==set(frozen)
for n in ['inputs-before.json','inputs-after.json','result.json']:take(SRC/n)
for case in f.CASES:
 slot=SRC/case;workspace=slot/'project';marker=m.read_json(slot/'marker-before.json');assert d.load_workspace(workspace)==marker
 for n in ['marker-before.json','controller.py','controller-launch.json','controller-result.json','outcome.json','direct-controller-interrupt.json']:
  if (slot/n).is_file():take(slot/n)
 for n in [d.MARKER,'build.gradle','settings.gradle']:take(workspace/n)
 record=m.read_json(slot/'controller-result.json');execution=record['execution'];cleanup=execution['owned_gradle_cleanup']
 assert cleanup['complete'] and cleanup['errors']==[] and cleanup['directory_handle_closed'] and cleanup['temporary_subreaper_restored'] and cleanup['signal_handlers_restored']
 assert len(cleanup['daemons'])==1 and cleanup['client']['java_verified']
 for l in [cleanup['client'],*cleanup['daemons']]:
  assert l['java_verified'] and l['exited'] and l['pid_absent'] and l['handle_closed'] and not Path('/proc',str(l['pid'])).exists();pids.append(l['pid'])
 child=cleanup['daemons'][0];client=cleanup['client'];assert child['parent_pid']==client['pid'] and child['pid']==child['process_group']==child['session'] and child['start_ticks']>=client['start_ticks']
 launch=m.read_json(slot/'controller-launch.json');assert launch['pidfd_pre_post_validated'] and launch['source_sha256']==m.file_sha256(slot/'controller.py') and not Path('/proc',str(launch['process']['pid'])).exists();pids.append(launch['process']['pid'])
 assert cleanup['temporary_subreaper_previous']==0 and child['wait_status'] in ['exact-adopted-daemon-reaped','not-waitable-by-controller'];waits.append(child['wait_status'])
 assert not cleanup['global_process_scan_or_wildcard_wait'] and not cleanup['receipt_pid_used'] and not cleanup['all_descendants_verified']
 runtime=m.read_json(workspace/'build/dependency-integrity/bootstrap/graphs/root/runtime.json')
 # Reuse the exact existing bounded producer schema validator, not a guessed key.
 assert w.runtime_candidate_pid(runtime,marker,'bootstrap')==child['pid']
 if case=='normal':
  assert execution['exit_code']==0 and 'reason' not in execution and record['selected_project_graph_complete'];summary=d.validate_graph_tree(workspace,marker,run_id='bootstrap',mode='bootstrap',entry_root='.')
 else:
  stamp=m.read_json(workspace/'build/dependency-integrity/bootstrap/owned-cancel-ready.json');assert stamp=={'record_type':'owned-cancellation-hold','pid':child['pid'],'hold_milliseconds':60000}
  assert not record['selected_project_graph_complete'] and execution['reason']==('timeout' if case.startswith('timeout') else 'interrupted') and execution['exit_code']!=0
 if case=='timeout-term-resistant':assert child['kill_sent']
 for p in (workspace/'build/dependency-integrity/bootstrap').rglob('*'):
  if p.is_file() and p.suffix in ['.json','.xml','.lockfile']:take(p)
 for n in [m.metadata_path('.'),m.lock_path('.',marker['host'])]:
  if (workspace/n).is_file():take(workspace/n)
 for p in [slot/'controller.log',workspace/'build/dependency-integrity/bootstrap/gradle.log']:
  if p.is_file():log_observations.append({'path':p.relative_to(SRC).as_posix(),'bytes':p.stat().st_size,'sha256':m.file_sha256(p),'console_body_archived':False})
assert len(pids)==len(set(pids))==15
archive=OUT/'original-observations.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for n,raw in sorted(selected.items()):
  info=zipfile.ZipInfo(n,date_time=(2026,10,27,0,0,0));info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
with zipfile.ZipFile(archive) as z:assert {n:m.sha256_bytes(z.read(n)) for n in z.namelist()}=={n:m.sha256_bytes(b) for n,b in selected.items()}
old=ast.parse(subprocess.check_output(['git','show','cebdc8f206a5e34b39e1cb8053b380ba509707c2:scripts/dependencies/runtime_witness.py']).decode());new=ast.parse((ROOT/'scripts/dependencies/gradle_process.py').read_text());names=['WitnessError','require','ProcessIdentity','parse_stat','fields','environment','private_values','client_prefix','daemon_entrypoint']
def bodies(t):return {n.name:ast.dump(n,include_attributes=False) for n in t.body if hasattr(n,'name') and n.name in names}
assert bodies(old)==bodies(new)
for folder,name in [('nativecmpkit-owned-tooling-20261027-001','first-owner-tooling'),('nativecmpkit-owned-tooling-20261027-002','all-dependency-tooling')]:
 source=Path('/dev/shm')/folder;target=OUT/name;target.mkdir()
 for p in source.iterdir():
  if p.is_file():(target/p.name).open('xb').write(p.read_bytes())
log=(OUT/'all-dependency-tooling/all-python-dependency-tests.log').read_text();assert re.search(r'^Ran 380 tests in ',log,re.M) and re.search(r'^OK$',log,re.M)
methods=re.findall(r'^test_[^\n]+\(test_(integrity|runtime_witness|owned_gradle)\.',log,re.M);assert len(methods)==380
counts={n:methods.count(n) for n in ['integrity','runtime_witness','owned_gradle']};assert counts=={'integrity':171,'runtime_witness':148,'owned_gradle':61}
record={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'dirty_source_held_diagnostic':True,'core_checkpoint':w.CHECKPOINT_FILENAME,'core_checkpoint_sha256':w.CHECKPOINT_SHA256,'previous008_manifest_sha256':m.file_sha256(ROOT/'scripts/dependencies/checkpoint-offline-008.json'),'core_inputs':10,'source_files_held_and_rechecked':len(frozen),'actual_gradle_invocations':5,'case_results':result['cases'],'all15_exact_client_daemon_controller_pids_absent_at_review':True,'actual_daemon_wait_outcomes':waits,'owned_daemon_cleanup_performed_by_controller_not_probe':True,'jcmd_attempts':0,'python_tooling_counts':counts,'python_tooling_methods':380,'earlier53_owner_methods_overlap_current61':True,'shared_process_grammar_ast_body_signature_decorator_equivalence':names,'normal_graph_summary':summary,'archive_files':len(selected),'archive_sha256':m.file_sha256(archive),'archive_byte_pairs_all_match':True,'console_observations':log_observations,'original_red_preserved':'docs/development/evidence/build/dependency-fixtures/owned-daemon-timeout-red-20261027/lead-review.json','scope':'Real controlled-single-root Linux installed Gradle9.7.1/JDK17 normal return,20s finite60s hold timeout, SIGINT, SIGTERM and TERM-resistant shutdown escalation. Exact admitted client/daemon pidfds, directory handle, signal handlers and prior subreaper restored. No external daemon cleanup; exact original controller source/results retained. Ordinary wrappers/composites/other hosts/arbitrary descendants/SIGKILL/trust remain unverified.','library_native_or_packaged_consumer_methods_executed':0,'issues_closed':0,'packages_published':False,'release_readiness_certified':False,'review_script_sha256':m.file_sha256(Path(__file__))}
(OUT/'lead-independent-review.json').open('x').write(json.dumps(record,indent=2,sort_keys=True)+'\n')
(OUT/'archive-manifest.json').open('x').write(json.dumps({'original_observations.zip':record['archive_sha256'],'members':{n:m.sha256_bytes(b) for n,b in sorted(selected.items())}},indent=2,sort_keys=True)+'\n')
(OUT/'SHA256SUMS').open('x').write(''.join(f'{m.file_sha256(p)}  {p.relative_to(OUT)}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({k:record[k] for k in ['actual_gradle_invocations','core_inputs','source_files_held_and_rechecked','all15_exact_client_daemon_controller_pids_absent_at_review','python_tooling_counts','archive_files','archive_sha256']}))
