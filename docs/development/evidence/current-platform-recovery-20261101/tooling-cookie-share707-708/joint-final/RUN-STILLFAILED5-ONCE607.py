"""Authorized stillfailed5 once after independent705 CURRENT Cookie source review, with actual source280 before/after custody."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,stat,subprocess,sys,time
P=Path(__file__).resolve().parent;R=P/'candidate-root';E=P/'STILLFAILED5-EXECUTION607'
assert not E.exists(),'Never overwrite or replay an existing original execution'
sha=lambda b:hashlib.sha256(b).hexdigest()
canonical=lambda o:(json.dumps(o,sort_keys=True,indent=2)+'\n').encode()
seal=json.loads((P/'FINAL-JOINT-CURRENT-SOURCE280-SEAL607.json').read_bytes())
plan=json.loads((P/'STILLFAILED5-ONLY-AUTHORIZED-UNEXECUTED-PLAN607.json').read_bytes())
source=json.loads((P/'PASSIVE-JOINT-CURRENT280-MAP607.json').read_bytes())
assert len(source)==280 and len(plan['test_ids'])==5
assert sha((P/'STILLFAILED5-ONLY-AUTHORIZED-UNEXECUTED-PLAN607.json').read_bytes())==seal['plan_sha256']
applicability=json.loads((P/'PASSIVE-JOINT-CURRENT-ASSERTION20-APPLICABILITY607.json').read_bytes())
raw40=json.loads((P/'PASSIVE-COOKIE-CURRENT40-ACTUAL-ENDPOINTS607.json').read_bytes())
assert all(applicability['current_contract_preflight'].values()) and applicability['previous_passive20_reexecuted']is False
assert raw40['all40_expected_equal_actual']is True and len(raw40['expected_current40'])==40
assert sha((P/'PASSIVE-COOKIE-CURRENT40-ACTUAL-ENDPOINTS607.json').read_bytes())==seal['raw40_expected_actual_receipt_sha256']
all_current=json.loads((P/'PASSIVE-ALL-JOINT-CURRENT-ADMISSIONS607.json').read_bytes())
assert all_current['all7_current_spec_reads_expected_equal_actual']is True
assert all_current['all_raw278_expected_equal_actual']is True and all_current['joint_CURRENT_own_guard_matches_zeroed_final_postimage']is True
assert sha((P/'PASSIVE-ALL-JOINT-CURRENT-ADMISSIONS607.json').read_bytes())==seal['all_joint_current_admissions_receipt_sha256']
gate=json.loads((P/'INDEPENDENT705-SOURCE-REVIEW-GATE607.json').read_bytes())
assert gate['accepted_current_vs_historical_and_exact_source']is True
assert gate['source_seal_sha256']==sha((P/'FINAL-JOINT-CURRENT-SOURCE280-SEAL607.json').read_bytes())
assert gate['current280_map_sha256']==seal['current280_map_sha256']
assert sha(Path(gate['independent_receipt']).read_bytes())==gate['independent_receipt_sha256']
assert seal['onlyfailed5_authorized_UNEXECUTED']is True

def snapshot():
 result={}
 assert R==R.resolve(strict=True)
 for n,expected in source.items():
  f=R/n;before=f.lstat()
  assert stat.S_ISREG(before.st_mode)and before.st_nlink==1 and f==f.resolve(strict=True)and f.is_relative_to(R)
  raw=f.read_bytes();after=f.lstat()
  identity=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  assert identity(before)==identity(after)
  row={'sha256':sha(raw),'bytes':len(raw),'mode':stat.S_IMODE(after.st_mode)}
  assert row==expected,(n,row,expected)
  result[n]=row|{'device':after.st_dev,'inode':after.st_ino,'links':after.st_nlink,
                  'mtime_ns':after.st_mtime_ns,'ctime_ns':after.st_ctime_ns}
 assert sha(canonical({n:r['sha256']for n,r in result.items()}))==seal['current280_map_sha256']
 return result
before=snapshot();E.mkdir();(E/'ACTUAL280-BEFORE607.json').write_bytes(canonical(before))
started={'schema':'failed5 source execution started607/v1','UTC':datetime.now(timezone.utc).isoformat(),
 'source_map_sha256':seal['current280_map_sha256'],'source_seal_sha256':sha((P/'FINAL-JOINT-CURRENT-SOURCE280-SEAL607.json').read_bytes()),
 'test_ids':plan['test_ids'],'original_FIRST13_and_70716_replayed':False,'accepted_FIRST24_19_and_lead9_replayed':False,'compiler_native_ROOT_Git_GitHub_adoption':0,
 'atime_excluded_from_custody_because_read_access_changes_it':True}
(E/'EXECUTION-STARTED607.json').write_bytes(canonical(started))
child=E/'SOURCE-CONTROL-WORKER607.py'
child.write_text('''from pathlib import Path
import json,sys,unittest
P=Path(__file__).resolve().parents[1]
plan=json.loads((P/'STILLFAILED5-ONLY-AUTHORIZED-UNEXECUTED-PLAN607.json').read_bytes())
suite=unittest.defaultTestLoader.loadTestsFromNames(plan['test_ids'])
def flatten(suite):
 for test in suite:
  if isinstance(test,unittest.TestSuite):yield from flatten(test)
  else:yield test.id()
loaded=list(flatten(suite))
if loaded!=plan['test_ids']:
 raise AssertionError('Exactly the original failed5 named real source controls must load, not placeholders')
result=unittest.TextTestRunner(verbosity=2).run(suite)
report={'testsRun':result.testsRun,'loaded_exact_test_ids':loaded,
        'failures':[{'id':t.id(),'traceback':s}for t,s in result.failures],
        'errors':[{'id':t.id(),'traceback':s}for t,s in result.errors],
        'skipped':[{'id':t.id(),'reason':s}for t,s in result.skipped],
        'expectedFailures':[t.id()for t,s in result.expectedFailures],
        'unexpectedSuccesses':[t.id()for t in result.unexpectedSuccesses],
        'wasSuccessful':result.wasSuccessful()}
(Path(__file__).parent/'WORKER-RESULT607.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\\n')
sys.exit(0 if result.wasSuccessful()else1)
'''.replace('else1','else 1'))
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(R/'scripts/ci')+os.pathsep+str(R/'scripts/ci/tests')
t=time.perf_counter();status='unknown';returncode=None
log=E/'ORIGINAL-STILLFAILED5-UNITTEST607.log'
try:
 with log.open('wb')as output:
  process=subprocess.run([sys.executable,'-B',str(child)],cwd=R/'scripts/ci',env=env,
                         stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,timeout=240)
 returncode=process.returncode;status='completed'
except subprocess.TimeoutExpired:
 status='timeout_refused'
except BaseException as error:
 status='wrapper_error_'+type(error).__name__
elapsed=time.perf_counter()-t
after=snapshot();(E/'ACTUAL280-AFTER607.json').write_bytes(canonical(after))
assert before==after,'Actual280 source/control inputs must hold'
worker=json.loads((E/'WORKER-RESULT607.json').read_bytes())if(E/'WORKER-RESULT607.json').is_file()else None
passed=status=='completed'and returncode==0 and worker is not None and worker['wasSuccessful']is True and worker['testsRun']==5 and worker['loaded_exact_test_ids']==plan['test_ids'] and not any(worker[k]for k in['failures','errors','skipped','expectedFailures','unexpectedSuccesses'])
result={'schema':'original stillfailed5 after CURRENT Cookie postimage source result607/v1','UTC':datetime.now(timezone.utc).isoformat(),
 'execution_status':status,'direct_returncode':returncode,'wrapper_elapsed_seconds':elapsed,
 'passed_failed5':passed,'worker':worker,'actual280_before_after_held':before==after,
 'source_map_sha256':seal['current280_map_sha256'],'source_seal_sha256':started['source_seal_sha256'],
 'before_sha256':sha((E/'ACTUAL280-BEFORE607.json').read_bytes()),'after_sha256':sha((E/'ACTUAL280-AFTER607.json').read_bytes()),
 'original_log_sha256':sha(log.read_bytes()),'source_control_scope_only':True,'independent705_receipt_sha256':gate['independent_receipt_sha256'],
 'original_FIRST13_and_70716_populations_replayed':False,'accepted_FIRST24_19_and_lead9_replayed':False,'compiler_native_ROOT_Git_GitHub_adoption':0}
(E/'EXECUTION-RESULT607.json').write_bytes(canonical(result))
print(log.read_text())
print('RESULT',json.dumps({k:v for k,v in result.items()if k!='worker'},sort_keys=True))
sys.exit(0 if passed else 1)
