import hashlib,importlib.util,json,os,pathlib,re,subprocess,sys,time
PRODUCTION=pathlib.Path('/root/projects/nativeCmpKit')
WORK=PRODUCTION/'build/native-incremental-important-worktree'
OUT=pathlib.Path('/dev/shm/nativecmpkit-native-incremental-important-20261028')
MODULES=('calf-file-picker','calf-share')
sys.path.insert(0,str(WORK/'scripts/native'));import artifacts as a
sys.path.insert(0,str(WORK/'scripts/ci'));import library_tests as tests;import daemon_jvm
REVISION=subprocess.run(['git','rev-parse','HEAD'],cwd=WORK,text=True,capture_output=True,check=True).stdout.strip()
assert REVISION=='1ceb9d686aebfcc5893a5f90325296be41075ed0'
for path in ['convention-plugins/src/main/kotlin/NativeLibraries.kt','scripts/native/artifacts.py']:
 assert (WORK/path).read_bytes()==subprocess.run(['git','show',REVISION+':'+path],cwd=WORK,capture_output=True,check=True).stdout
ENV=dict(os.environ);ENV['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64';ENV['ANDROID_HOME']='/opt/android-sdk';ENV['ANDROID_SDK_ROOT']='/opt/android-sdk';ENV['PATH']='/root/.cargo/bin:'+ENV['JAVA_HOME']+'/bin:'+ENV['PATH'];ENV['CARGO_BUILD_JOBS']='1';ENV['CARGO_NET_OFFLINE']='true'
BASE=['./gradlew','--offline','--no-daemon','--console=plain','--no-configuration-cache','--max-workers=2','-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8','-Pkotlin.compiler.execution.strategy=in-process','-PnativecmpkitNativeMode=host','--init-script','scripts/ci/daemon-jvm.init.gradle.kts']
RESOURCE=[f':{m}:desktopProcessResources' for m in MODULES]
PHASES=[]
def snapshot():
 revision,dirty=a.git_provenance(WORK);assert revision==REVISION and dirty
 return {'revision':revision,'sourceTreeDirty':dirty,'sourceFiles':{m:a.expected_source_files(WORK,m) for m in MODULES}}
def phase(label,build_modules=(),only_picker=False,test=False):
 p=OUT/label;p.mkdir(exist_ok=True);before=snapshot();(p/'inputs-before.json').write_text(json.dumps(before,indent=2)+'\n')
 cmd=BASE+(['--init-script','scripts/ci/fresh-tests.init.gradle.kts',':calf-file-picker:desktopTest','--tests','com.mohamedrejeb.calf.picker.PickerContractTest'] if test else RESOURCE)
 started=time.time_ns()
 print('RUN '+label,flush=True)
 if label=='baseline001' and (p/'gradle.log.result.json').is_file():
  execution=json.loads((p/'gradle.log.result.json').read_text());assert execution['command']==cmd and execution['exit_code']==0
  assert json.loads((p/'inputs-after.json').read_text())==before
  print('REUSE actual baseline command/source results; controller-only recovery',flush=True)
 else:
  result=subprocess.run([sys.executable,str(PRODUCTION/'scripts/audit/run_bounded_build.py'),'--cwd',str(WORK),'--log',str(p/'gradle.log'),'--timeout','600','--reserve-mib','8192','--',*cmd],cwd=PRODUCTION,env=ENV,capture_output=True,text=True)
  execution=json.loads((p/'gradle.log.result.json').read_text());assert result.returncode==execution['exit_code']==0,(label,execution)
 after=snapshot();assert before==after;(p/'inputs-after.json').write_text(json.dumps(after,indent=2)+'\n')
 log=(p/'gradle.log').read_text();daemons=[daemon_jvm.observation(p/'gradle.log')]
 assert daemons[0]['launcher_home_matches_daemon'] is True
 tasks={}
 for line in log.splitlines():
  match=re.fullmatch(r'> Task (:[^ ]+)(?: (UP-TO-DATE|FROM-CACHE|NO-SOURCE|SKIPPED|FAILED))?',line)
  if match:
   assert match[1] not in tasks,(label,match[1]);tasks[match[1]]=match[2] or 'EXECUTED'
 expected_modules=('calf-file-picker',) if test else MODULES
 manifests=[]
 for module in expected_modules:
  expected='EXECUTED' if module in build_modules else 'UP-TO-DATE'
  for task in ['buildNativeLib','prepareNativeResources']:
   assert tasks.get(f':{module}:{task}')==expected,(label,module,task,tasks.get(f':{module}:{task}'),expected)
  manifest=a.validate_bundle(WORK,module,WORK/module/'build/native-libs',['linux-x64'],expected_revision=REVISION,expected_version='0.1.0-SNAPSHOT')[0]
  assert manifest['sourceTreeDirty'] is True
  (p/(module+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n');manifests.append({'module':module,'platform':manifest['platform'],'rustTarget':manifest['rustTarget'],'sourceSha256':manifest['sourceSha256'],'binarySha256':manifest['sha256'],'rustcVersion':manifest['rustcVersion']})
 assert not any(re.search(r'(windows|macos|ios|android|js|wasm)',key,re.I) and re.search(r'(buildNativeLib|Test|compile|ProcessResources|link)',key) for key in tasks),list(tasks)
 cases=[]
 if test:
  reports=list((WORK/'calf-file-picker/build/test-results/desktopTest').glob('TEST-*.xml'));assert len(reports)==1,reports
  report=reports[0];assert report.stat().st_mtime_ns>=started
  cases=tests.junit_cases(report.read_bytes());assert len(cases)==4 and all(x['status']=='passed' for x in cases)
  assert all(x['classname']=='com.mohamedrejeb.calf.picker.PickerContractTest' for x in cases)
  (p/'PickerContractTest.xml').write_bytes(report.read_bytes())
 row={'phase':label,'execution':execution,'native_task_states':{k:v for k,v in tasks.items() if re.search(r'(buildNativeLib|prepareNativeResources|desktopProcessResources|desktopTest)$',k)},'actual_daemon':daemons[0],'input_state':{'sourceRevision':REVISION,'sourceTreeDirty':True,'unchanged_before_after':True,'module_counts':{k:len(v) for k,v in before['sourceFiles'].items()}},'manifests':manifests,'fresh_cases':cases,'no_irrelevant_platform_compile_test_or_native_build_tasks':True}
 (p/'review.json').write_text(json.dumps(row,indent=2)+'\n');PHASES.append(row);(OUT/'accepted-phases.json').write_text(json.dumps(PHASES,indent=2)+'\n')
 print('PASS '+label+' '+json.dumps({'seconds':execution['elapsed_seconds'],'native':row['native_task_states'],'fresh_tests':len(cases)}),flush=True)
phase('baseline001',MODULES)
phase('reuse002')
mutations=[('source','calf-file-picker/native/src/lib.rs',b'\n// Important incremental fixture: Rust source bytes independently changed.\n',('calf-file-picker',)),('lock','calf-file-picker/native/Cargo.lock',b'\n# Important incremental fixture: lockfile bytes independently changed, locked graph unchanged.\n',('calf-file-picker',)),('toolchain','rust-toolchain.toml',b'\n# Important incremental fixture: declared toolchain bytes independently changed, pinned compiler unchanged.\n',MODULES)]
recipes=[]
for index,(name,path,addition,modules) in enumerate(mutations):
 file=WORK/path;original=file.read_bytes();recipes.append({'kind':name,'path':path,'before_sha256':hashlib.sha256(original).hexdigest(),'addition_utf8':addition.decode(),'after_sha256':hashlib.sha256(original+addition).hexdigest(),'semantic_graph_or_compiler_change':False})
 try:
  file.write_bytes(original+addition);phase(name+'-change00'+str(3+2*index),modules)
 finally:file.write_bytes(original)
 phase(name+'-restore00'+str(4+2*index),modules)
phase('jvm-picker-contract009',test=True)
(OUT/'fixture-recipes.json').write_text(json.dumps({'revision':REVISION,'dirty_flag_control':'Only append a documented harmless README comment before all runs to hold sourceTreeDirty=true. Each native mutation is isolated/restored; owning build code remains own Git blobs.','mutations':recipes},indent=2)+'\n')
(OUT/'acceptance-review.json').write_text(json.dumps({'finding':'BUILD-010','issue':145,'accepted':True,'original_requirements':3,'accepted_gradle_invocations':len(PHASES),'fresh_library_methods':4,'native_resource_productions':'Local Linux-x64 only, manifest validated, not published or full-matrix packages/JNI/device/release evidence.','mutation_scope':'Nonsemantic independent source/lock/toolchain byte changes prove invalidation; no new dependency graph/compiler version or performance certification.','phases':PHASES},indent=2)+'\n')
print('IMPORTANT ACCEPTANCE READY:9 actual Gradle invocations,4 fresh library methods, all3 original requirements reviewed by assertions; inspect before closing.',flush=True)
