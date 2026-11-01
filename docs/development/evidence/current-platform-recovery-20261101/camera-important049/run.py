import ast, hashlib, io, json, os, pathlib, sys, tempfile, time, traceback, unittest
ROOT=pathlib.Path(os.environ['NATIVECMPKIT_IMPORTANT_ROOT']).resolve()
OUT=pathlib.Path(os.environ['NATIVECMPKIT_IMPORTANT_OUT']).resolve()
PRIVATE=pathlib.Path(os.environ['NATIVECMPKIT_IMPORTANT_PRIVATE']).resolve()
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests as lt, sample_platform_verification as sp
H=lambda b:hashlib.sha256(b).hexdigest()
def save(n,v):(OUT/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def canonical(v):return H(json.dumps(v,sort_keys=True,separators=(',',':')).encode())
before_library=lt.snapshot_inputs(ROOT);before_combined=sp.inputs(ROOT)
save('before-library-inputs.json',before_library);save('before-combined-inputs.json',before_combined)
selected=[]
name='test_android_camera_settings_activity_boundary'
for cls in ast.parse((ROOT/'scripts/ci'/(name+'.py')).read_text()).body:
 if isinstance(cls,ast.ClassDef):
  for method in cls.body:
   if isinstance(method,ast.FunctionDef) and method.name.startswith('test_'):selected.append('.'.join((name,cls.name,method.name)))
assert len(selected)==26
selected+=['test_android_camera_developer_prerequisite.LifecycleModels.test_started_settings_activity_new_epoch_gate_refuses_even_with_terminal_nothing','test_android_camera_documented_data_default.DocumentedDataDefaultTests.test_only_new_branch_is_exact_pair_and_fixed_launch_has_no_userdata_overrides']
assert len(selected)==28 and len(set(selected))==28
save('selection.json',{'methods':selected,'count':28,'new_methods':26,'affected_existing_methods':2,'old_fixture_80_not_discovered_or_replayed':True,'desktop8_and_permission3_reused_not_replayed':True,'camera009_C2_C3_reused_not_replayed':True})
blocked=[]
def audit(event,args):
 if event in {'subprocess.Popen','os.system','os.posix_spawn','os.posix_spawnp','os.kill','os.killpg'} or event.startswith('socket.'):
  blocked.append(event);raise AssertionError('Important camera checks prohibit native/process/network actions')
sys.addaudithook(audit)
records={testid:{'test':testid,'status':'not-run'} for testid in selected};problems=[]
def problem(test,exc,kind):
 frames=[]
 for frame in traceback.extract_tb(exc[2]):
  try:rel=pathlib.Path(frame.filename).resolve().relative_to(ROOT).as_posix()
  except ValueError:continue
  if rel.startswith('scripts/ci/'):frames.append({'file':rel,'line':frame.lineno,'function':frame.name})
 return {'test':test.id(),'kind':kind,'exception_type':exc[0].__name__,'message_sha256':H(str(exc[1]).encode()),'public_source_frames':frames}
class Result(unittest.TextTestResult):
 def addSuccess(self,test):
  super().addSuccess(test);records[test.id()]['status']='passed'
 def addFailure(self,test,exc):
  super().addFailure(test,exc);records[test.id()]['status']='failed';problems.append(problem(test,exc,'failure'))
 def addError(self,test,exc):
  super().addError(test,exc);records.setdefault(test.id(),{'test':test.id()})['status']='error';problems.append(problem(test,exc,'error'))
 def addSkip(self,test,reason):
  super().addSkip(test,reason);records[test.id()]['status']='skipped'
 def addSubTest(self,test,subtest,exc):
  super().addSubTest(test,subtest,exc)
  if exc is not None:
   records[test.id()]['status']='failed' if issubclass(exc[0],test.failureException) else 'error';problems.append(problem(test,exc,'subtest'))
stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in selected)
start=time.monotonic();result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite);elapsed=time.monotonic()-start
(PRIVATE/'camera-important.log').write_text(stream.getvalue())
after_library=lt.snapshot_inputs(ROOT);after_combined=sp.inputs(ROOT)
save('after-library-inputs.json',after_library);save('after-combined-inputs.json',after_combined)
report={'schema':1,'tests_run':result.testsRun,'selected':28,'passed':sum(x['status']=='passed' for x in records.values()),'failed':sum(x['status']=='failed' for x in records.values()),'errors':len(result.errors),'failure_records':len(result.failures),'skips':len(result.skipped),'elapsed_seconds':round(elapsed,6),'records':list(records.values()),'problems':problems,'library_inputs':len(before_library),'combined_inputs':len(before_combined),'library_before_after_equal':before_library==after_library,'combined_before_after_equal':before_combined==after_combined,'library_map_sha256':canonical(after_library),'combined_map_sha256':canonical(after_combined),'private_log_sha256':H(stream.getvalue().encode()),'forbidden_actual_action_attempts':blocked,'native_executions':0,'compiler_executions':0,'accepted_test_replays':0,'issue_closures':0,'publishing_security_release_clearance':False}
save('REPORT.json',report)
print(json.dumps({k:report[k] for k in ['tests_run','passed','failed','errors','skips','elapsed_seconds','library_inputs','combined_inputs','library_before_after_equal','combined_before_after_equal','forbidden_actual_action_attempts']},sort_keys=True))
sys.exit(0 if result.wasSuccessful() and result.testsRun==28 and report['passed']==28 and not result.skipped and before_library==after_library and before_combined==after_combined and not blocked else 1)
