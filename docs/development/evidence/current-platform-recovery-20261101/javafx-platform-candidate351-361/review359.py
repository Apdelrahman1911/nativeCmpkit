from pathlib import Path
import datetime, hashlib, json, os, re, sys, zipfile

D=Path(os.environ['D']); ROOT=Path('/root/projects/nativeCmpKit'); C=D/'checkout'
paths=['scripts/ci/library_tests.py','scripts/ci/android_external328_source_projection.py','scripts/ci/test_android_external328_source_projection.py','tests/dependency/javafx-http2-cancellation/artifacts.json','tests/dependency/javafx-http2-cancellation/probe_runner.py','tests/dependency/javafx-http2-cancellation/build_runtime_candidate.py','tests/dependency/javafx-http2-cancellation/run_library_candidate.py','tests/dependency/javafx-http2-cancellation/library-runtime-candidate.init.gradle.kts','tests/dependency/javafx-http2-cancellation/test_runtime_candidate.py','tests/dependency/javafx-http2-cancellation/test_probe_runner.py','.github/workflows/javafx-library-candidate.yml','.github/workflows/javafx-dependency-regression.yml','scripts/ci/arm64_stop_candidate_source_projection.py','scripts/ci/test_arm64_stop_candidate_source_projection.py','scripts/ci/fixtures/arm64-stop-candidate-source-inverse.json','tests/dependency/javafx-http2-cancellation/test_arm64_candidate.py','tests/dependency/javafx-http2-cancellation/test_macos_candidate.py']
sha=lambda b:hashlib.sha256(b).hexdigest()
checks={}
def check(name, condition):
    checks[name]=bool(condition)
    if not condition: raise AssertionError(name)
def read(p): return json.loads(p.read_bytes())
receipt={'schema_version':1,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'native_executions':0,'compiler_executions_during_review':0,'tests_executed_during_review':0,'scope':'Solo owning source/results review; packaging-only originals reused; no new native, default adoption, corresponding-source/legal/security/consumer/API-ABI/release clearance.'}
try:
    check('exact17_owning_paths_regular_private_sources',len(paths)==len(set(paths))==17 and all((C/p).is_file() and not (C/p).is_symlink() for p in paths))
    held={p:sha((C/p).read_bytes()) for p in paths}; receipt['owning_candidate_inputs']=held
    sys.path.insert(0,str(ROOT/'scripts/ci')); import library_tests as base
    before=base.snapshot_inputs(ROOT); receipt['baseline_library_inputs']=len(before)
    (D/'baseline-library-inputs359.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n')
    actual=read(ROOT/'docs/development/evidence/current-platform-recovery-20261101/desktop-macos-native350-354/actual-inputs353.json')
    check('all1212_actual_library_inputs_unchanged_before_integration',before==actual and len(before)==1212)
    check('all12_existing_owning_paths_have_actual_diffs_and_only_five_new_paths',all((ROOT/p).is_file() and (ROOT/p).read_bytes()!=(C/p).read_bytes() for p in paths[:12]) and all(not (ROOT/p).exists() for p in paths[12:]))
    spec=read(C/'scripts/ci/fixtures/arm64-stop-candidate-source-inverse.json')
    check('exact_inverse_manifest_source_pin',sha((C/'scripts/ci/fixtures/arm64-stop-candidate-source-inverse.json').read_bytes())=='a3b72d71cf22c65dcd39e29d5cec0c2dbc3ebe6648fd0134b1dfb283c4edbf1f' and 'SPEC_SHA256 = "a3b72d71cf22c65dcd39e29d5cec0c2dbc3ebe6648fd0134b1dfb283c4edbf1f"' in (C/'scripts/ci/arm64_stop_candidate_source_projection.py').read_text())
    check('three_inverse_bindings_eight_fragments',set(spec['bindings'])==set(paths[:3]) and sum(len(r['fragments']) for r in spec['bindings'].values())==8)
    for p,row in spec['bindings'].items():
        old=(ROOT/p).read_bytes(); new=(C/p).read_bytes(); good=(sha(old)==row['before_sha256'] and sha(new)==row['after_sha256']); forward=old
        for frag in row['fragments']:
            a,b=frag['before'].encode(),frag['after'].encode(); good &= sha(a)==frag['before_fragment_sha256'] and sha(b)==frag['after_fragment_sha256'] and forward.count(a)==1
            forward=forward.replace(a,b,1)
        reverse=new
        for frag in reversed(row['fragments']):
            a,b=frag['before'].encode(),frag['after'].encode(); good &= reverse.count(b)==1; reverse=reverse.replace(b,a,1)
        check('complete_unique_reversible_source_'+p,good and forward==new and reverse==old)
    old_spec=C/'scripts/ci/fixtures/android-external328-source-inverse.json'
    if not old_spec.exists():
        old_spec=next(p for p in (C/'scripts/ci/fixtures').glob('*.json') if sha(p.read_bytes())=='ec166c161309144efd8ffc2b5726a7fa98cbd0f83a6becbfd37ea539562a2c7a')
    check('all_original_external328_16bindings49fragments_manifest_retained',sha(old_spec.read_bytes())=='ec166c161309144efd8ffc2b5726a7fa98cbd0f83a6becbfd37ea539562a2c7a' and len(read(old_spec)['bindings'])==16 and sum(len(x['fragments']) for x in read(old_spec)['bindings'].values())==49)
    core=(C/'scripts/ci/library_tests.py').read_text(); start='        elif boundary_focus and test_plan["explicit_test_focus"] in WEBVIEW_DESKTOP_REQUEST_FOCUSES:\n'; end='        elif boundary_focus and test_plan["explicit_test_focus"] in WEBVIEW_IDENTITY_FOCUSES:\n'; branch=start+core.split(start,1)[1].split(end,1)[0]
    check('original_native_xml_acceptance_branch_bytes_unchanged',sha(branch.encode())=='b3df23f2636d6c1a420294d9ebdc8d37c8f24c0eb455fd1589dcb4e9447e00ad' and 'arm64_stop_candidate_source_projection' not in core)
    for name, expected in {'DesktopWebViewRequestStateAcceptanceTest.kt':'c08bcdc062d18d24c5a370aaa818a8171c352d06acca35af1202fd4eb2c13f13','DesktopWebViewStopRedirectAcceptanceTest.kt':'8eb3cbe9e91974c423998eb3007ed64ed9d98863dcc27d0b72da901caad411a3','BoundedDesktopAwtWindow.kt':'c7bccc89f020490ea6198b837c7a9e386b051a0926ec22e17b3557699420b082'}.items():
        p='calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/'+name
        check('original_native_source_'+name,sha((ROOT/p).read_bytes())==expected and (ROOT/p).read_bytes()==(C/p).read_bytes())
    pins=read(C/'tests/dependency/javafx-http2-cancellation/artifacts.json'); original=read(ROOT/'tests/dependency/javafx-http2-cancellation/artifacts.json')
    check('original_linux_windows_source_all_metadata_retained',all(pins[k]==v for k,v in original.items() if k!='platforms') and all(pins['platforms'][k]==v for k,v in original['platforms'].items()))
    check('only_three_added_exact_platform_rows',set(pins['platforms'])=={'linux','win','linux-aarch64','mac','mac-aarch64'})
    acquired=[*read(D/'ACQUISITION351.json')['files'],*read(D/'ACQUISITION355.json')['files']]; expected=[r for k in ('linux-aarch64','mac','mac-aarch64') for r in pins['platforms'][k]]
    check('exact15_fixed_official_acquisitions_rehashed_once',len(acquired)==len(expected)==15 and all({k:a[k] for k in ('file','url','bytes','sha256')}==r and a['acquisitions']==1 and a['same_registry_sha1_matches'] and len((D/'official-inputs'/r['file']).read_bytes())==r['bytes'] and sha((D/'official-inputs'/r['file']).read_bytes())==r['sha256'] and hashlib.sha1((D/'official-inputs'/r['file']).read_bytes()).hexdigest()==a['same_registry_sha1'] for a,r in zip(acquired,expected)))
    check('new_classifier_integrity_not_independent_security',pins['same_registry_checksums_are_independent_security_certification'] is False)
    runner=(C/'tests/dependency/javafx-http2-cancellation/run_library_candidate.py').read_text(); builder=(C/'tests/dependency/javafx-http2-cancellation/build_runtime_candidate.py').read_text(); init=(C/'tests/dependency/javafx-http2-cancellation/library-runtime-candidate.init.gradle.kts').read_text()
    check('actual_platform_admission_before_compiler_output_lock',runner.index('probe.need(probe.classifier() == classifier,')<runner.index('descriptor = os.open')<runner.index('manifest = candidate.build'))
    check('candidate_command_actual_host_and_focus_bound', 'probe.need(probe.classifier() == classifier, "Full candidate classifier must match the actual native host")' in runner and 'plan["explicit_test_focus"] == focuses[classifier]' in runner and 'Only the failed original public Stop selector is allowed' in runner)
    check('cross_classifier_is_packaging_only_explicit_zero_native','"cross_classifier_packaging_only": target != compiler_host, "native_executions": 0' in builder and 'target-classifier' in builder and 'subprocess' not in builder.split('target = getattr',1)[0].split('def build(args):',1)[1])
    check('init_exact_original_four_classifiers_and_actual_daemon',all('"'+k+'" to "'+pins['platforms'][k][-1]['sha256']+'"' in init and 'classifier == "'+k+'" && system' in init for k in ('win','linux-aarch64','mac','mac-aarch64')) and 'Runtime.version().feature() == 17' in init)
    check('exact_one_provider_replace_never_shadow_cache_or_route',all(s in init for s in ('webProviders.size == 1','originalFiles.filterNot { it == original } + candidate','candidateDigest(original) == originalSha','candidateDigest(candidate) == expected','outputs.doNotCacheIf','outputs.upToDateWhen { false }')) and 'useHTTP2Loader' not in init and '--patch-module' not in init)
    check('original_class_pins_and_owning_patch_legal_notices_retained',all((C/('tests/dependency/javafx-http2-cancellation/'+n)).read_bytes()==(ROOT/('tests/dependency/javafx-http2-cancellation/'+n)).read_bytes() for n in ('cancel-response-future.patch','NOTICE.md','LICENSE-GPLv2-Classpath.txt','ADDITIONAL_LICENSE_INFO','ASSEMBLY_EXCEPTION')) and '"HTTP2Loader.class": "9e8663af362be84a12111e785b06f2cadf3c1f02e6cd19a9782a2e9f7e4675c2"' in builder)
    for path in ('.github/workflows/javafx-library-candidate.yml','.github/workflows/javafx-dependency-regression.yml'):
        text=(C/path).read_text(); jobifs=[line.strip() for line in text.splitlines() if line.startswith('    if:')]
        check('manual_only_native_readonly_'+Path(path).name,len(jobifs)==1 and "github.event_name == 'workflow_dispatch'" in jobifs[0] and "github.ref == 'refs/heads/development/preview-hardening'" in jobifs[0] and 'permissions:\n  contents: read' in text and '  push:\n    branches: [development/preview-hardening]' in text and not any(s in text for s in ('packages: write','id-token:','gh release create','publishAndRelease','cargo publish','npm publish')))
    workflow=(C/'.github/workflows/javafx-library-candidate.yml').read_text()
    check('one_selected_host_distinct_concurrency_platform_cache',all(s in workflow for s in ('options: [linux-arm64, macos-arm64, macos-x64, windows]','default: linux-arm64',"inputs.platform == 'macos-arm64' && 'macos-26'","inputs.platform == 'macos-x64' && 'macos-26-intel'",'${{ github.ref }}-${{ inputs.platform || \'windows\' }}','${{ env.CANDIDATE_SLOT }}-desktop-')) and 'matrix:' not in workflow and 'actions/cache/save' not in workflow and 'restore-keys:' not in workflow)
    check('reports_only_upload_no_candidate_binary_or_source_package',not any(s in workflow.split('name: Preserve verification receipts only',1)[1] for s in ('*.jar','*.class','*.zip')) and 'persist-credentials: false' in workflow)
    control_batches=['NEW12-controls351','affected4-controls351','history-new6-affected3-351','macos-new5-affected5-355','history-affected3-355']; counts=[12,4,9,10,3]; identities=[]
    for b,n in zip(control_batches,counts):
        text=(D/(b+'.stderr')).read_text(); methods=re.findall(r'^(test_\w+) \(([^)]+)\) \.\.\. ok$',text,re.M); identities.extend(i[1] for i in methods)
        check('completed_control_population_'+b,(D/(b+'.exit-code')).read_text().strip()=='0' and len(methods)==n and f'Ran {n} tests' in text and '\nOK\n' in text)
    check('earlier38_invocations31_unique_controls_not_one_fresh31',len(identities)==38 and len(set(identities))==31)
    red=read(D/'affected-target-red357.json'); green=read(D/'affected-target-green358.json')
    check('stale_classifier_control_red_then_failed_only_green',red['exit_code']==1 and green['exit_code']==0 and red['held'] and green['held'] and 'FAILED (failures=1)' in (D/'affected-target-red357.stderr').read_text() and 'Ran 1 test' in (D/'affected-target-green358.stderr').read_text() and 'target_classifier="mac-aarch32"' in (C/'tests/dependency/javafx-http2-cancellation/test_arm64_candidate.py').read_text())
    check('green_current_source_bindings_exact',all(sha((C/p).read_bytes())==v for p,v in green['inputs_after'].items()))
    receipt['control_summary']={'prior_passing_invocations':38,'prior_unique_controls':31,'later_owning_red_invocations':1,'later_corrected_passing_invocations':1,'owning_invocations_total':40,'unique_accepted_controls':31,'preimport356_owning_methods':0,'red357_wrong_message_shell_assertion_preserved':True,'qualified_clock_seconds':['0.364','0.047','0.201','0.148','0.077','0.001']}
    packages=[]
    for label,target in (('runtime-candidate-arm64','linux-aarch64'),('runtime-candidate-mac','mac'),('runtime-candidate-mac-aarch64','mac-aarch64')):
        P=D/label; m=read(P/'candidate.json'); a=read(P/'inputs-before.json'); b=read(P/'inputs-after.json'); commands=read(P/'commands.json')
        check('held_packaging_maps_'+target,a==b and len(a)==14 and m['held_inputs'] and m['passed'] and m['classifier']==target and m['compiler_host_classifier']=='linux' and m['cross_classifier_packaging_only'] and m['native_executions']==m['library_tests']==0)
        allowed_stage={str(C/'tests/dependency/javafx-http2-cancellation/probe_runner.py'):D/'source-stage351/probe_runner.py',str(C/'tests/dependency/javafx-http2-cancellation/artifacts.json'):D/'artifacts351-before-macos.json'} if target=='linux-aarch64' else {}
        check('exact_current_or_documented_stage_input_bindings_'+target,all(sha(allowed_stage.get(name,Path(name)).read_bytes())==value for name,value in a.items()))
        check('actual_compiler_jdk17_zero_exit_streams_'+target,len(commands)==2 and commands[0]['name']=='java-version' and commands[1]['name']=='compile-owning-source' and all(c['exit_code']==0 and not c['timeout'] and sha((P/(c['name']+'.stdout')).read_bytes())==c['stdout_sha256'] and sha((P/(c['name']+'.stderr')).read_bytes())==c['stderr_sha256'] for c in commands) and b'version "17.0.20"' in (P/'java-version.stderr').read_bytes())
        check('private_full_jar_sources_actual_digests_'+target,sha((P/m['jar_file']).read_bytes())==m['jar_sha256'] and sha((P/m['java_sources_file']).read_bytes())==m['java_sources_sha256'] and sha((P/'source/HTTP2Loader.java').read_bytes())==m['modified_source_sha256'])
        web=D/'official-inputs'/f'javafx-web-21.0.13-{target}.jar'; review=read(P/'jar-member-review.json')
        with zipfile.ZipFile(web) as originaljar, zipfile.ZipFile(P/m['jar_file']) as candidatejar:
            originals=originaljar.namelist(); new=candidatejar.namelist(); changed=[]; retained=[]
            check('full_original_inventory_duplicate_free_'+target,len(originals)==len(set(originals))==548 and len(new)==len(set(new)))
            for name in originals:
                oldpayload=originaljar.read(name); newpayload=candidatejar.read(name)
                if oldpayload!=newpayload: changed.append(name)
                if name in review['retained_payload_sha256']: retained.append(sha(newpayload)==review['retained_payload_sha256'][name] and oldpayload==newpayload)
            check('all542_nonowning_payloads_retained_only_loader_manifest_differ_'+target,len(retained)==542 and all(retained) and set(changed)=={'META-INF/MANIFEST.MF','com/sun/webkit/network/HTTP2Loader.class'} and set(new)-set(originals)==set(review['added_members']))
            check('all_five_owning_class_pins_and_legal_notices_exact_'+target,all(sha(candidatejar.read(name))==v==sha((P/'classes'/name).read_bytes()) for name,v in m['modified_class_sha256'].items()) and all(candidatejar.read('META-INF/nativecmpkit/'+n)==(C/('tests/dependency/javafx-http2-cancellation/'+n)).read_bytes() for n in ('NOTICE.md','LICENSE-GPLv2-Classpath.txt','ADDITIONAL_LICENSE_INFO','ASSEMBLY_EXCEPTION')) and b'NativeCmpKit-Publication-Ready: false' in candidatejar.read('META-INF/MANIFEST.MF'))
        with zipfile.ZipFile(D/'official-inputs/javafx-web-21.0.13-sources.jar') as originalsrc, zipfile.ZipFile(P/m['java_sources_file']) as candidatesrc:
            names=originalsrc.namelist(); entry='com/sun/webkit/network/HTTP2Loader.java'; old=originalsrc.read(entry); modified=candidatesrc.read(entry)
            check('complete_java_source_312members311_unrelated_retained_'+target,len(names)==312 and all(originalsrc.read(name)==candidatesrc.read(name) for name in names if name!=entry) and modified==(P/'source/HTTP2Loader.java').read_bytes() and old[:old.index(b' */')+3]==modified[:modified.index(b' */')+3])
        packages.append({'classifier':target,'elapsed_seconds':m['elapsed_seconds'],'jar_sha256':m['jar_sha256'],'compiler_seconds':commands[1]['elapsed_seconds'],'stage_bindings_current':target!='linux-aarch64','compiler_host':'Linux x64 JDK17.0.20','native_executions':0})
    receipt['packages']=packages
    check('accepted_actionlint_final_source_logs_preserved',(D/'actionlint355.exit-code').read_text().strip()=='0' and (D/'actionlint351-recovery.exit-code').read_text().strip()=='0' and (D/'actionlint351.exit-code').read_text().strip()=='127' and not (D/'actionlint355.stderr').read_bytes())
    check('all_candidate_owning_inputs_held_during_review',held=={p:sha((C/p).read_bytes()) for p in paths})
    check('all_baseline_library_inputs_held_during_review',before==base.snapshot_inputs(ROOT))
    receipt['passed']=True
except Exception as error:
    receipt.update(passed=False,error_type=type(error).__name__,error=str(error)); raise
finally:
    receipt['passive_checks']=len(checks); (D/'REVIEW359.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n'); print(json.dumps({'passed':receipt.get('passed'),'passive_checks':len(checks),'failed':[k for k,v in checks.items() if not v]},indent=2))
