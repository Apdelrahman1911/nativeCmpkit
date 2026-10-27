from pathlib import Path
import hashlib,json,re,shutil,sys,datetime as dt
ROOT=Path('/root/projects/nativeCmpKit');DEST=ROOT/'docs/development/evidence/kgp-native-worker-parser-20261027';assert not DEST.exists()
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lib

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reviews=[]
for number in ['001','002','003']:
 base=ROOT/f'build/kgp-native-worker-parser-20261027-{number}'
 r=json.loads((base/'receipt.json').read_bytes());before=json.loads((base/'inputs-before.json').read_bytes());after=json.loads((base/'inputs-after.json').read_bytes())
 assert before==after and r['probe_inputs_unchanged_at_execution'] and all(sha(Path(p))==h for p,h in before.items())
 b=json.loads((base/'library-build-inputs-before.json').read_bytes());a=json.loads((base/'library-build-inputs-after.json').read_bytes());assert b==a==lib.snapshot_inputs(ROOT)
 assert r['source_revision']==lib.git_revision(ROOT) and r['library_methods_executed']==r['ios_methods_executed']==0
 if number!='003':
  assert r['compile']['result']['exit_code']==0 and sha(base/'compile.log')==r['compile']['log_sha256']
  assert all(x['actual_fixture_executions']==0 and x['result']['exit_code']==1 and not x['reports'] for x in r['runs'])
  phrase='Unresolved reference' if number=='001' else "property 'binaryResultsDirectory'"
  assert phrase in (base/'nativeWorkerPositive.log').read_text()
 else:
  assert r['compile_repeated']==False and sha(ROOT/r['source_bound_binary_reused_from'])==before[str(ROOT/r['source_bound_binary_reused_from'])]
  assert len(r['runs'])==2
  for run in r['runs']:
   log=base/(run['task']+'.log');txt=log.read_text();assert sha(log)==run['log_sha256'] and run['result']['exit_code']==run['expected_gradle_exit']
   assert run['binary_unchanged'] and run['actual_fixture_executions']==2 and len(run['reports'])==1
   report=run['reports'][0];path=base/report['path'];assert sha(path)==report['sha256']
   cases=lib.junit_cases(path.read_bytes());assert cases==report['testcases']
   assert {c['name'].split('[')[0] for c in cases}=={'generatedRegistryAndBodyActuallyRunOnOwnedWorker','requestedAssertionFailureIsNotSilentSuccess'}
   assert all('nativecmpkit.probe.ActualWorkerGeneratedSuite' in c['classname'] and c['name'].endswith('[linuxNativeParserDiagnostic]') for c in cases)
   assert txt.count('NATIVECMPKIT_WORKER_TERMINATED')==1 and txt.count('NATIVECMPKIT_WORKER_CREATED mainWorker=1 ownedWorker=2')==1
   assert txt.index('NATIVECMPKIT_WORKER_TERMINATED')<txt.index('NATIVECMPKIT_WORKER_RESULT exit=')
   assert 'worker=2 mainWorker=1' in path.read_text()
   if run['expected_gradle_exit']==0:assert all(c['status']=='passed' for c in cases) and 'NATIVECMPKIT_WORKER_RESULT exit=0' in txt
   else:assert [c['status'] for c in cases]==['passed','failed'] and 'NATIVECMPKIT_WORKER_RESULT exit=1' in txt
 reviews.append({'attempt':number,'actual_generated_fixture_executions':sum(x['actual_fixture_executions'] for x in r['runs']),'runtime_gradle_exits':[x['result']['exit_code'] for x in r['runs']],'probe_and_library_build_inputs_unchanged_at_execution_and_before_archive':True,'source_build_input_count':len(b),'scope':'Fresh real KGP host parsing, positive/negative fixture contract satisfied' if number=='003' else 'Native compile succeeded but KGP configuration failed before any native methods; not a positive/negative behavior result','test_reports':[report for run in r['runs'] for report in run['reports']]})
DEST.mkdir(parents=True)
for number in ['001','002','003']:
 base=ROOT/f'build/kgp-native-worker-parser-20261027-{number}';target=DEST/number;target.mkdir()
 for p in base.rglob('*'):
  if not p.is_file() or p.suffix=='.kexe':continue
  assert not p.is_symlink();out=target/p.relative_to(base);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':lib.git_revision(ROOT),'attempts':reviews,'actual_generated_native_fixture_executions':4,'distinct_methods':2,'positive_methods_passed':2,'negative_control_methods_passed':1,'negative_control_intentionally_failed_methods':1,'actual_kgp_teamcity_junit_parser_verified_on_linux':True,'worker_bodies_and_termination_before_both_process_exits_verified_on_linux':True,'library_or_ios_methods_executed':0,'genuine_uikit_application_verified':False,'release_readiness_certified':False,'binary_digest_independently_checked_from_origin_before_archive':True,'binary_not_retained_in_documentation_archive':True,'limitations':['Setup attempts001/002 run zero native methods; their Gradle failures are retained, not negative-control success.','Attempt003 reuses the successful same-source compiled binary from002 and executes both tasks fresh in a new owned temporary project with fresh XML; no cached testcase result is reused.','Diagnostic native executable bytes are not copied into the documentation archive. KGP tool/dependency hashes are source/provenance observations, not independent supply-chain trust.','No Apple application bundle, launch wrapper, UIKit lifecycle, library native behavior, physical device or release verification is proved by Linux parsing.']}
(DEST/'lead-independent-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n');shutil.copyfile(Path(__file__),DEST/'collector.py')
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in sorted(DEST.rglob('*')) if p.is_file()))
print(json.dumps({'archive':str(DEST.relative_to(ROOT)),'actual_kgp_native_fixture_executions':4,'library_or_ios_methods':0,'positive_and_negative_contracts_verified':True}))
