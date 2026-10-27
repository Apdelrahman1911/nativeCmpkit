from pathlib import Path
import datetime as dt,hashlib,json,os,re,subprocess
root=Path('/root/projects/nativeCmpKit');out=Path(__file__).parent
cache=Path('/root/.gradle/caches/modules-2/files-2.1')
def jar(group,name,version):
 paths=list((cache/group/name/version).glob('**/'+name+'-'+version+'.jar'));assert len(paths)==1,(group,name,paths);return str(paths[0])
compiler=[jar('org.jetbrains.kotlin',n,'2.4.20') for n in ('kotlin-compiler-embeddable','kotlin-build-tools-api','kotlin-stdlib','kotlin-script-runtime','kotlin-daemon-embeddable')]
compiler += [jar('org.jetbrains.kotlin','kotlin-reflect','1.6.10'),jar('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm','1.8.0'),jar('org.jetbrains','annotations','13.0')]
classpath=[jar('org.jetbrains.kotlin',n,'2.4.20') for n in ('kotlin-stdlib','kotlin-test','kotlin-test-junit')]
classpath += [jar('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm','1.10.2'),jar('junit','junit','4.13.2'),jar('org.hamcrest','hamcrest-core','1.3'),jar('org.jetbrains','annotations','13.0')]
paths=['calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/AtomicSave.kt','calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/SelectedFileSave.kt','calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/AtomicSaveTest.kt','calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/SelectedFileSaveTest.kt']
def snapshot():return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
before=snapshot();records=[]
def run(label,command,expected):
 log=out/(label+'.log');cmd=['python3',str(root/'scripts/audit/run_bounded_build.py'),'--cwd',str(root),'--log',str(log),'--timeout','90','--reserve-mib','8192','--',*command]
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=110)
 (out/(label+'.controller.txt')).write_text(result.stdout+result.stderr)
 receipt=json.loads(log.with_suffix(log.suffix+'.result.json').read_text());records.append({'label':label,'receipt':receipt})
 print(label,'exit',receipt['exit_code'],flush=True)
 if receipt['exit_code']!=expected:
  print(log.read_text()[-14000:],flush=True);raise AssertionError('Unexpected focused command result')
 return log.read_text()
runner=out/'FocusedJUnit.java';runner.write_text('''import org.junit.runner.*;
public class FocusedJUnit {
 public static void main(String[] args) throws Exception {
  Request request = args.length == 2 ? Request.method(Class.forName(args[0]), args[1]) : Request.classes(java.util.Arrays.stream(args).map(n -> {try{return Class.forName(n);}catch(Exception e){throw new RuntimeException(e);}}).toArray(Class[]::new));
  Result r = new JUnitCore().run(request);
  r.getFailures().forEach(f -> System.out.println("FAILURE " + f.getTestHeader() + " " + f.getException()));
  System.out.println("TEST_COUNTS executed="+r.getRunCount()+" failures="+r.getFailureCount()+" ignored="+r.getIgnoreCount());
  System.exit(r.wasSuccessful()?0:1);
 }
}
''')
# Classes mode has three arguments; unused extra non-test class is avoided by a second runner.
run('runner-compile',['javac','-cp',os.pathsep.join(classpath),'-d',str(out),str(runner)],0)
old=out/'old-AtomicSave.kt';old.write_bytes(subprocess.check_output(['git','show','77a5b735:'+paths[0]],cwd=root))
def compile(label,sources):
 target=out/(label+'.jar')
 run(label,['java','-Xmx512m','-cp',os.pathsep.join(compiler),'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-jvm-target','17','-classpath',os.pathsep.join(classpath),'-d',str(target),*map(str,sources)],0)
 return target
def test(label,target,cls,method,expected):
 log=run(label,['java','-Xmx512m','-cp',os.pathsep.join([str(out),str(target),*classpath]),'FocusedJUnit',cls,method],expected)
 counts=re.search(r'TEST_COUNTS executed=(\d+) failures=(\d+) ignored=(\d+)',log);assert counts
 records[-1]['test_counts']={k:int(v) for k,v in zip(['executed','failures','ignored'],counts.groups())}
 assert records[-1]['test_counts']=={'executed':1,'failures':expected,'ignored':0}
oldjar=compile('old-atomic-compile',[old,root/paths[2]])
test('old-atomic-self-suppression-red',oldjar,'com.mohamedrejeb.calf.picker.platform.AtomicSaveTest','repeatedPrimaryFailureDuringCleanupCannotReplaceTheWriteFailure',1)
# A copied old cooperative-dispatch control has no worker interruption. The same
# real blocked stream must fail instead of being relaxed/released to pass.
control=out/'cooperative-SelectedFileSave.kt';text=(root/paths[1]).read_text();assert text.count('runInterruptible(Dispatchers.IO)')==1
control.write_text(text.replace('import kotlinx.coroutines.runInterruptible','import kotlinx.coroutines.withContext').replace('runInterruptible(Dispatchers.IO)','withContext(Dispatchers.IO)'))
controljar=compile('cooperative-copy-compile',[root/paths[0],control,root/paths[3]])
test('cooperative-copy-cancellation-red',controljar,'com.mohamedrejeb.calf.picker.platform.SelectedFileSaveTest','cancellationInterruptsGenuinelyBlockedCopyAndReleasesItsResources',1)
current=compile('current-atomic-selected-compile',[root/p for p in paths])
# Run each class once; the runner with one class argument selects its complete suite.
for cls,count in [('AtomicSaveTest',10),('SelectedFileSaveTest',4)]:
 label='current-'+cls
 log=run(label,['java','-Xmx512m','-cp',os.pathsep.join([str(out),str(current),*classpath]),'FocusedJUnit','com.mohamedrejeb.calf.picker.platform.'+cls],0)
 values=re.search(r'TEST_COUNTS executed=(\d+) failures=(\d+) ignored=(\d+)',log);assert values
 counts={k:int(v) for k,v in zip(['executed','failures','ignored'],values.groups())};assert counts=={'executed':count,'failures':0,'ignored':0};records[-1]['test_counts']=counts
assert snapshot()==before
(out/'receipt.json').write_text(json.dumps({'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_input_hashes':before,'source_unchanged':True,'compiler_version':'2.4.20','JDK_target':17,'coroutines_runtime':'1.10.2','selected_actual_linux_methods':14,'prior_source_failure_tests':1,'copied_old_dispatch_control_failures':1,'records':records,'scope':'Real current Kotlin sources compiled directly with configured2.4.20/JDK17/coroutines1.10.2; real filesystem and genuinely blocked wrapped NIO stream. Narrow held-worktree execution, not full Gradle/native-dialog/other-OS/consumer/ABI/release verification.','stubs_used':False,'root_outputs_created':False,'packages_published':False},indent=2)+'\n')
print('PASSED14 actual current Linux methods; both negative controls fail as required. No full Gradle/native/other-OS claim.',flush=True)
