from pathlib import Path
import hashlib,json,re,shutil,subprocess,datetime as dt
ROOT=Path('/root/projects/nativeCmpKit');SOURCE=ROOT/'build/native-worker-entry-probe-20261027-003';OUT=ROOT/'docs/development/evidence/native-worker-entry-contract-20261027-003'
assert not OUT.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((SOURCE/'receipt.json').read_text());a=json.loads((SOURCE/'inputs-before.json').read_text());b=json.loads((SOURCE/'inputs-after.json').read_text())
assert a==b and r['input_bytes_unchanged'] and all(sha(Path(p))==s for p,s in a.items())
assert r['compile']['compile_result']['exit_code']==0 and not r['compile']['compile_result'].get('stop_reason')
assert sha(SOURCE/'compile.log')==r['compile']['compile_log_sha256']
assert len(r['runs'])==2
rows=[]
expected=['generatedRegistryAndBodyActuallyRunOnOwnedWorker','requestedAssertionFailureIsNotSilentSuccess']
for result in r['runs']:
 p=SOURCE/(result['name']+'.log');body=p.read_text();assert sha(p)==result['log_sha256']
 assert result['result']['exit_code']==result['expected_exit'] and not result['result'].get('stop_reason')
 created=re.findall(r'^NATIVECMPKIT_WORKER_CREATED mainWorker=(\d+) ownedWorker=(\d+)$',body,re.M);assert len(created)==1 and created[0][0]!=created[0][1]
 cases=re.findall(r'^NATIVECMPKIT_WORKER_BODY case=(\w+) worker=(\d+) mainWorker=(\d+)(?: intentionalFailure=(true|false))?$',body,re.M)
 assert sorted(c[0] for c in cases)==expected and all(c[1]==created[0][1] and c[2]==created[0][0] for c in cases)
 starts=re.findall(r"^##teamcity\[testStarted name='(\w+)'",body,re.M);ends=re.findall(r"^##teamcity\[testFinished name='(\w+)'",body,re.M);failures=re.findall(r"^##teamcity\[testFailed name='(\w+)'",body,re.M)
 assert sorted(starts)==sorted(ends)==expected and len(starts)==len(set(starts))==2
 assert failures==([] if result['expected_exit']==0 else [expected[1]])
 assert body.count('NATIVECMPKIT_WORKER_TERMINATED\n')==1
 assert body.index('NATIVECMPKIT_WORKER_TERMINATED')<body.index('NATIVECMPKIT_WORKER_RESULT')
 assert f'NATIVECMPKIT_WORKER_RESULT exit={result["expected_exit"]}\n' in body
 assert 'testIgnored' not in body
 rows.append({'name':result['name'],'exit_code':result['result']['exit_code'],'fixture_executions':2,'failed_methods':failures,'passing_methods':[name for name in starts if name not in failures],'main_worker_id':int(created[0][0]),'actual_body_worker_id':int(created[0][1]),'worker_termination_completed_before_result_and_process_exit':True,'log_sha256':sha(p)})
OUT.mkdir(parents=True)
for p in SOURCE.iterdir():
 assert p.is_file() and not p.is_symlink();shutil.copyfile(p,OUT/p.name)
java=json.loads((SOURCE/'java-runtime.json').read_text());assert java['direct_compiler_java_executable'] in r['compile']['compile_command'];assert sha(Path(java['direct_compiler_java_executable']))==java['executable_sha256']
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision_at_execution':r['source_revision'],'probe_inputs_unchanged_at_execution_and_before_archive':True,'actual_generated_worker_fixture_executions':4,'distinct_methods':2,'positive_methods_passed':2,'negative_control_methods_passed':1,'negative_control_intentionally_failed_methods':1,'negative_control_failure_exit_propagated':True,'worker_suite_registration_and_body_execution_verified_on_linux':True,'worker_termination_verified_before_both_process_exits':True,'direct_compiler_jdk17_command_and_executable_digest_verified':True,'reviewed_runs':rows,'genuine_uikit_application_verified':False,'ios_or_library_methods_executed':0,'release_readiness_certified':False,'scope':'Actual Linux Kotlin/Native2.4.20 generated-worker diagnostic, including one intentional assertion-failure control. TeamCity frames are reviewed as native output, not claimed parsed KGP/JUnit reports. No iOS/UIKit/library behavior proof.'}
(OUT/'lead-independent-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n');shutil.copyfile(__file__,OUT/'lead-review.py')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({k:review[k] for k in ['actual_generated_worker_fixture_executions','distinct_methods','negative_control_failure_exit_propagated','worker_termination_verified_before_both_process_exits','genuine_uikit_application_verified','ios_or_library_methods_executed']},indent=2))
