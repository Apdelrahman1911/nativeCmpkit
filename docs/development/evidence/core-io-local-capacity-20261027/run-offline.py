"""Bounded actual two-root Kotlin Maven consumer; never a full release gate."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/ci'));import library_tests as lt
prepared=json.loads((O/'prepared-inputs.json').read_bytes());inputs=prepared['input_hashes'];assert all(lt.sha256(R/n)==h for n,h in inputs.items())
assert all(lt.sha256(O/'project'/Path(n).relative_to('tests/consumer/io-desktop'))==h for n,h in inputs.items() if n.startswith('tests/consumer/io-desktop/'))
assert json.loads((O/'partial-static-before.json').read_bytes())['success'] is True
assert not (O/'project/build').exists() and not (O/'gradle-user-home').exists()
for n,h in prepared['candidate_files'].items():
 p=O/'candidate-maven'/n;assert lt.sha256(p)==h['sha256'] and p.stat().st_size==h['size_bytes']
assert shutil.disk_usage(R).free>=8192*1024**2 and shutil.disk_usage(O).free>=8192*1024**2
jdk=Path('/usr/lib/jvm/java-17-openjdk-amd64');assert (jdk/'bin/java').is_file()
gradles=list(Path('/root/.gradle/wrapper/dists/gradle-9.7.1-bin').glob('*/gradle-9.7.1/bin/gradle'));assert len(gradles)==1;gradle=gradles[0]
native=R/'build/consumer-native-runtime/core-io-desktop-20261027-001';assert not native.exists();(native/'tmp').mkdir(parents=True)
(O/'private-home').mkdir();env={'PATH':os.environ['PATH'],'JAVA_HOME':str(jdk),'HOME':str(O/'private-home'),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','GRADLE_USER_HOME':str(O/'gradle-user-home'),'GRADLE_RO_DEP_CACHE':str(O/'readonly-dependencies'),'TMPDIR':str(native/'tmp')}
args=[str(gradle),'--no-daemon','--no-parallel','--no-configuration-cache','--max-workers=2','--console=plain','-Dorg.gradle.native.dir='+str(native/'gradle-native'),'-Djava.io.tmpdir='+str(native/'tmp')]
before={'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(R),'dirty_staged_source_held':True,'input_hashes':inputs,'prepared_receipt_sha256':lt.sha256(O/'prepared-inputs.json'),'driver_sha256':lt.sha256(Path(__file__)),'actual_cwd_guarded':str(R),'isolated_project':str(O/'project'),'candidate_source_not_current_release_candidate':True,'root_free_bytes':shutil.disk_usage(R).free,'tmpfs_free_bytes':shutil.disk_usage(O).free,'scope':'Two-root desktop Kotlin Maven diagnostic using separately copied readonly dependencies, fresh private Gradle user home and copied test fixture. No producer/composite source fallback.'}
(O/'inputs-before-execution.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n')
versions=lt.execute(R,args+['--version'],O/'gradle-version.log',60,8192,env=env);assert versions['exit_code']==0 and not versions.get('stop_reason')
v=(O/'gradle-version.log').read_text();assert 'Gradle 9.7.1' in v and '17.0.' in v
java=subprocess.run([str(jdk/'bin/java'),'-version'],env=env,capture_output=True,timeout=30);(O/'java-version.log').write_bytes(java.stdout+java.stderr);assert java.returncode==0
command=args+['-p',str(O/'project'),'--offline','verifyCandidateResolution','test','-PnativecmpkitRepository='+str(O/'candidate-maven'),'-PnativecmpkitVersion=0.1.0-preview.1']
(O/'command.json').write_text(json.dumps({'recorded_utc':lt.utc_now(),'command':command,'version_execution':versions,'candidate_modules':prepared['candidate_modules'],'offline':True,'environment_names_only':sorted(env),'publication_requested':False},indent=2)+'\n')
result=lt.execute(R,command,O/'gradle.log',420,8192,env=env)
(O/'original-gradle-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
xmls=sorted((O/'project/build/test-results/test').glob('TEST-*.xml'));cases=[];reports=[]
for p in xmls:
 parsed=lt.junit_cases(p.read_bytes());cases.extend(parsed);reports.append({'path':p.relative_to(O).as_posix(),'sha256':lt.sha256(p),'cases':len(parsed)})
unchanged=all(lt.sha256(R/n)==h for n,h in inputs.items()) and all(lt.sha256(O/'candidate-maven'/n)==h['sha256'] for n,h in prepared['candidate_files'].items())
r={'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(R),'dirty_staged_source_held':True,'original_Gradle_result':result,'command':command,'captured_inputs_and_candidate_bytes_unchanged':unchanged,'xml_reports':reports,'cases':cases,'actual_Kotlin_consumer_case_count':len(cases),'root_free_bytes':shutil.disk_usage(R).free,'tmpfs_free_bytes':shutil.disk_usage(O).free,'release_readiness_certified':False,'complete21_root_KMP_consumer':False,'scope':'Actual partial Core/IO desktop Maven consumer. Missing/failed XML or nonzero original Gradle exit is not a passing consumer. Original producer staging is dirty and failed outside selected roots.'}
(O/'execution-review-required.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['original_Gradle_result','captured_inputs_and_candidate_bytes_unchanged','actual_Kotlin_consumer_case_count','root_free_bytes','tmpfs_free_bytes']}))
raise SystemExit(result['exit_code'] if result['exit_code'] else (0 if unchanged and len(cases)==6 and not result.get('stop_reason') else 1))
