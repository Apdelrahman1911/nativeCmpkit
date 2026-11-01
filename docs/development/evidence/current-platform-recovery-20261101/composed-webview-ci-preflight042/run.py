import ast, hashlib, io, json, os, pathlib, shutil, sys, time, traceback, unittest
import sitecustomize as gate
ROOT = pathlib.Path(os.environ['NATIVECMPKIT_PREFLIGHT_ROOT']).resolve()
OUT = pathlib.Path(os.environ['NATIVECMPKIT_PREFLIGHT_PRIVATE']).resolve()
EVIDENCE = ROOT/'docs/development/evidence/current-platform-recovery-20261101'
def save(name,value):
    (OUT/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
baseline=json.loads((EVIDENCE/'shared-guard-freeze029/combined-inputs.json').read_text())
paths=set(baseline)
for folder in (ROOT/'scripts/ci', ROOT/'calf-webview'):
    for current,dirs,files in os.walk(folder):
        dirs[:]=[name for name in dirs if name not in {'.git','.gradle','build','target','node_modules','__pycache__','.kotlin'}]
        for name in files:
            file=pathlib.Path(current)/name
            if file.suffix in {'.py','.kts','.kt','.xml','.toml','.json','.properties','.md','.txt'}:
                paths.add(file.relative_to(ROOT).as_posix())
anchors=('android-held-start-integration031/results/after-owning-guards.json',
         'ios-weak-identity-integration033/author-packet/proof/NEW-OUTCOMES.json',
         'ios-weak-identity-integration033/author-packet/proof/PHASE-MODEL-REUSE.json')
anchor_hashes={rel:hashlib.sha256((EVIDENCE/rel).read_bytes()).hexdigest() for rel in anchors}
def freeze(copy=False):
    data={}
    for rel in sorted(paths):
        file=ROOT/rel
        if file.is_symlink() or not file.is_file():
            raise ValueError('Frozen input missing or symlinked: '+rel)
        raw=file.read_bytes(); data[rel]=hashlib.sha256(raw).hexdigest()
        if copy:
            target=OUT/'snapshot'/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
    return data
before=freeze(True)
save('before-inputs.json',before)
save('before-summary.json',{'files':len(before),'canonical_map_sha256':digest(before),'source_only_passive_freeze':True,'git_binding_claim':False,'reference_map_keys':len(baseline),'anchor_sha256':anchor_hashes})
accepted_android={r['test'] for r in json.loads((EVIDENCE/anchors[0]).read_text())['records'] if r['status']=='passed'}
selected=[]
for name in ('test_android_webview_request_state','test_android_webview_request_selector'):
    tree=ast.parse((ROOT/'scripts/ci'/ (name+'.py')).read_text())
    for cls in tree.body:
        if isinstance(cls,ast.ClassDef):
            for method in cls.body:
                if isinstance(method,ast.FunctionDef) and method.name.startswith('test_'):
                    testid='.'.join((name,cls.name,method.name))
                    if testid not in accepted_android:selected.append(testid)
assert len(selected)==26
for method in ('test_registered_profile_reaches_real_source_only_cli_on_exact_existing_rows',
               'test_owning_command_emits_fourteen_finite_selectors_with_exact_fixture_property',
               'test_owning_source_command_readback_refuses_changed_isolation_init_and_fixture',
               'test_owning_plan_mutations_cannot_broaden_case_source_task_or_worker_contract',
               'test_security_fixture_is_absent_from_ordinary_and_existing_request_commands'):
    selected.append('test_desktop_security_routing.DesktopSecurityRoutingModels.'+method)
for name in ('test_ios_webview_request_focus','test_ios_webview_request_dns_focus'):
    tree=ast.parse((ROOT/'scripts/ci'/(name+'.py')).read_text())
    for cls in tree.body:
        if isinstance(cls,ast.ClassDef):
            for method in cls.body:
                if isinstance(method,ast.FunctionDef) and method.name.startswith('test_'):
                    selected.append('.'.join((name,cls.name,method.name)))
assert len(selected)==46 and len(set(selected))==46
assert not (set(selected)&accepted_android)
reuse={'android_accepted_exact_ids':sorted(accepted_android),'ios_author_green_methods':14,
       'ios_prior_phase_model_methods':16,'desktop_tls_new_guard_methods':8,
       'native_results_replayed':False,'accepted_reporter_compile_replayed':False,
       'worker_parser_xml_unchanged_desktop_methods_replayed':False,
       'git_backed_methods_excluded':['test_webview_final_interop_release.WebViewFinalInteropReleaseTests.test_normalization_recovers_exact_prior_host_not_changed_worker_or_test_bytes',
                                      'test_ios_webview_native_identity.IosWebViewNativeIdentityTests.test_four_previously_accepted_host_methods_and_helpers_are_byte_identical',
                                      'test_webview_identity_recovery.WebViewIdentityRecoveryTests.test_accepted_method_bodies_and_other_engine_helpers_remain_exactly_unchanged'],
       'rationale':'Only current Android selector/request consumers, changed TLS source-bound security plan/command consumers, and iOS request/full-composition routing/receipt consumers. Old iOS phase source blocks and model helpers are author-verified exact; native TLS, DNS, request and reporter compilation are not replayed. No broad CI audit or unrelated platform execution.'}
save('selection.json',{'tests':selected,'count':len(selected),'reuse':reuse})
records={testid:{'test':testid,'status':'not-run'} for testid in selected}
problems=[]
def safe_problem(test,exc,kind):
    entry={'test':test.id(),'kind':kind,'exception_type':exc[0].__name__,'message_sha256':hashlib.sha256(str(exc[1]).encode()).hexdigest(), 'public_source_frames':[]}
    for frame in traceback.extract_tb(exc[2]):
        try: rel=pathlib.Path(frame.filename).resolve().relative_to(ROOT).as_posix()
        except ValueError:continue
        if rel.startswith('scripts/ci/'):
            entry['public_source_frames'].append({'file':rel,'line':frame.lineno,'function':frame.name})
    return entry
class Result(unittest.TextTestResult):
    def addSuccess(self,test):
        super().addSuccess(test); records[test.id()]['status']='passed'
    def addFailure(self,test,exc):
        super().addFailure(test,exc); records.get(test.id(),{})['status']='failed'; problems.append(safe_problem(test,exc,'failure'))
    def addError(self,test,exc):
        super().addError(test,exc); records.get(test.id(),{})['status']='error'; problems.append(safe_problem(test,exc,'error'))
    def addSkip(self,test,reason):
        super().addSkip(test,reason); records.get(test.id(),{})['status']='skipped'
    def addSubTest(self,test,subtest,exc):
        super().addSubTest(test,subtest,exc)
        if exc is not None:
            records[test.id()]['status']='failed' if issubclass(exc[0],test.failureException) else 'error'
            problems.append(safe_problem(test,exc,'subtest'))
stream=io.StringIO(); suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(testid) for testid in selected)
start=time.monotonic(); result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite); elapsed=time.monotonic()-start
(OUT/'run.log').write_text(stream.getvalue())
results={'selected_methods':len(selected),'tests_run':result.testsRun,'passed_methods':sum(x['status']=='passed' for x in records.values()),'failed_methods':sum(x['status']=='failed' for x in records.values()),'errored_methods':sum(x['status']=='error' for x in records.values()),'skipped_methods':len(result.skipped),'failures':len(result.failures),'errors':len(result.errors),'elapsed_seconds':round(elapsed,6),'records':list(records.values()),'problems':problems,'log_sha256':hashlib.sha256(stream.getvalue().encode()).hexdigest(),'accepted_exact_ids_excluded':19,'native_build_compiler_git_network_acquisitions':0,'full_ci_suite_executed':False}
save('results.json',results)
plans=[]
import workflow_matrix as matrix
import library_tests as lt
for profile in ('android-webview-request-state','ios-webview-request-state'):
    started=time.monotonic()
    try:
        plan=matrix.preflight_plans(profile,root=ROOT)
        row,=matrix.matrix(profile)['include']
        full=lt.plan(ROOT,row['suite'],only_modules=('calf-webview',),focus=row['test-focus'])
        cases=full['expected'][0]['required_testcases']
        assert len(cases)==2
        plans.append({'profile':profile,'status':'passed','elapsed_seconds':round(time.monotonic()-started,6),'preflight':plan,'required_testcases':cases,'plan_sha256':digest(full),'plan':full})
    except Exception as exc:
        plans.append({'profile':profile,'status':'failed','exception_type':type(exc).__name__,'message_sha256':hashlib.sha256(str(exc).encode()).hexdigest()})
save('request2-plans.json',plans)
after=freeze()
save('after-inputs.json',after)
changes=[rel for rel in sorted(paths) if before[rel]!=after[rel]]
save('after-summary.json',{'files':len(after),'canonical_map_sha256':digest(after),'before_after_equal':before==after,'changed_files':changes,'anchor_after_equal':all(hashlib.sha256((EVIDENCE/rel).read_bytes()).hexdigest()==v for rel,v in anchor_hashes.items()),'child_source_plans':gate.EVENTS,'native_build_compiler_git_network_acquisitions':0})
print(json.dumps({key:results[key] for key in ('selected_methods','tests_run','passed_methods','failed_methods','errored_methods','skipped_methods','failures','errors','elapsed_seconds')},sort_keys=True))
print(json.dumps({'freeze_files':len(before),'before_after_equal':before==after,'map_sha256':digest(after),'plans':[{'profile':x['profile'],'status':x['status']} for x in plans],'allowed_plan_children':len(gate.EVENTS),'problems':problems},sort_keys=True))
