from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).parent;J=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin');C=Path('/root/.gradle/caches/modules-2/files-2.1')
OWNER='calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/DialogHandleOwner.kt';TEST='calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/DialogHandleCancellationTest.kt';PLATFORM='calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt';sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def jar(g,a,v):
 matches=list((C/g/a/v).glob(f'*/{a}-{v}.jar'));assert len(matches)==1,(g,a,v,matches);return matches[0]
jars=[jar(*x) for x in [('org.jetbrains.kotlin','kotlin-stdlib','2.4.20'),('org.jetbrains.kotlin','kotlin-test','2.4.20'),('org.jetbrains.kotlin','kotlin-test-junit','2.4.20'),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm','1.11.0'),('junit','junit','4.13.2'),('org.hamcrest','hamcrest-core','1.3'),('org.jetbrains','annotations','13.0')]]
compiler=jar('org.jetbrains.kotlin','kotlin-compiler-embeddable','2.4.20');cp=os.pathsep.join(map(str,jars));ccp=os.pathsep.join([str(compiler),cp,'/opt/gradle/gradle-9.7.1/lib/*']);assert (J/'java').is_file()
before={p:h(R/p) for p in [OWNER,TEST,PLATFORM]};assert 'withActiveDialogHandle(' in (R/PLATFORM).read_text() and (R/PLATFORM).read_text().count('withActiveDialogHandle(')==2
expected={'cancelledBeforeAllocationDoesNotCreateOrEnterUse','cancellationDuringRealWorkerCreationClosesOnceWithoutEnteringUse','cancellationDuringUseClosesAndRejectsTheUnclaimedResult','creationFailureNeverDestroysAnUnclaimedHandle','activeAndFailedUseEachCloseTheClaimedHandleExactlyOnce'}
runner='''import org.junit.runner.*;
import org.junit.runner.notification.*;
import java.util.*;
public final class ImportantJUnit {
 public static void main(String[] args) throws Exception {
  JUnitCore core=new JUnitCore(); Map<Description,String> statuses=new HashMap<>();
  core.addListener(new RunListener(){
   public void testStarted(Description d){statuses.put(d,"passed");}
   public void testFailure(Failure f){statuses.put(f.getDescription(),"failed");System.out.println("NC_FAILURE|"+f.getDescription().getMethodName()+"|"+f.getMessage());}
   public void testAssumptionFailure(Failure f){statuses.put(f.getDescription(),"skipped");}
   public void testIgnored(Description d){System.out.println("NC_CASE|"+d.getClassName()+"|"+d.getMethodName()+"|skipped");}
   public void testFinished(Description d){System.out.println("NC_CASE|"+d.getClassName()+"|"+d.getMethodName()+"|"+statuses.get(d));}
  });
  Result result=core.run(Class.forName(args[0]));
  System.out.println("NC_TOTAL|"+result.getRunCount()+"|"+result.getFailureCount()+"|"+result.getIgnoreCount());
  System.exit(result.wasSuccessful()?0:1);
 }
}'''
results=[]
for name in ['control001','green002']:
 out=O/name;out.mkdir(exist_ok=False);classes=out/'classes';classes.mkdir()
 # Exact old ownership body plus an admission wrapper without checks is a
 # semantically held negative control, NOT a claim the old source exposed this new API.
 src=out/'DialogHandleOwner.kt';test=out/'DialogHandleCancellationTest.kt';test.write_bytes((R/TEST).read_bytes())
 if name=='control001':
  old=subprocess.check_output(['git','show',sha+':'+OWNER],cwd=R);src.write_bytes(old+b'\ninternal inline fun <T> withActiveDialogHandle(context: kotlin.coroutines.CoroutineContext, create: () -> Long, destroy: (Long) -> Unit, use: (Long) -> T): T = withDialogHandle(create, destroy, use)\n')
 else:src.write_bytes((R/OWNER).read_bytes())
 commands=[]
 def run(cmd,label,limit=120):
  start=time.monotonic();p=subprocess.run(cmd,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit,env={**os.environ,'TMPDIR':str(out)});(out/(label+'.log')).write_text(p.stdout);e={'command':cmd,'exit_code':p.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'log_sha256':h(out/(label+'.log'))};commands.append(e);return p
 p=run([str(J/'java'),'-Xmx384m','-Djava.io.tmpdir='+str(out),'-cp',ccp,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-version','-no-stdlib','-no-reflect','-jvm-target','17','-classpath',cp,'-d',str(classes),str(src),str(test)],'compile');assert p.returncode==0,p.stdout
 java=out/'ImportantJUnit.java';java.write_text(runner);p=run([str(J/'javac'),'-classpath',cp,'-d',str(classes),str(java)],'runner-compile');assert p.returncode==0,p.stdout
 p=run([str(J/'java'),'-Xmx128m','-Djava.io.tmpdir='+str(out),'-cp',str(classes)+os.pathsep+cp,'ImportantJUnit','com.mohamedrejeb.calf.picker.platform.DialogHandleCancellationTest'],'test',60)
 cases=[]
 for line in p.stdout.splitlines():
  if line.startswith('NC_CASE|'):
   _,cl,method,status=line.split('|');cases.append({'classname':cl,'name':method,'status':status})
 assert len(cases)==5 and {c['name'] for c in cases}==expected and all(c['status'] in ['passed','failed'] for c in cases),p.stdout
 failed=sum(c['status']=='failed' for c in cases);assert p.returncode==(1 if failed else 0)
 if name=='control001':assert failed==3,(failed,p.stdout)
 else:assert failed==0,p.stdout
 suite=ET.Element('testsuite',name='com.mohamedrejeb.calf.picker.platform.DialogHandleCancellationTest',tests='5',failures=str(failed),errors='0',skipped='0')
 for c in cases:
  node=ET.SubElement(suite,'testcase',classname=c['classname'],name=c['name'])
  if c['status']=='failed':ET.SubElement(node,'failure',message='Owning admission assertion failed; inspect original JUnit log')
 ET.ElementTree(suite).write(out/'TEST-DialogHandleCancellationTest.xml',encoding='UTF-8',xml_declaration=True)
 receipt={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_revision':sha,'source_tree_dirty':True,'scope':'Standalone actual owned helper/Kotlin2.4.20/coroutines1.11.0/JDK17/JUnit4 execution. Real IO worker/cancellation; counted configuration handles, not actual JNI/live dialogs/full-module Gradle compilation/immutable release acceptance. Negative control adds only a new unguarded wrapper to the exact old helper body.','owning_inputs_before':before,'owning_inputs_after':{p:h(R/p) for p in before},'copied_owner_sha256':h(src),'copied_test_sha256':h(test),'dependencies':[{'name':p.name,'sha256':h(p)} for p in [compiler,*jars]],'commands':commands,'testcases':cases,'tests':5,'passed':5-failed,'failed':failed,'errors':0,'skipped':0,'xml_sha256':h(out/'TEST-DialogHandleCancellationTest.xml'),'packages_published':False,'issues_closed':0}
 assert receipt['owning_inputs_before']==receipt['owning_inputs_after'];(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');results.append(receipt);print(name,'5 executions;',5-failed,'passed,',failed,'failed;',commands[-1]['elapsed_seconds'],'seconds',flush=True)
assert before=={p:h(R/p) for p in before};(O/'review.json').write_text(json.dumps({'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'important_finding':'IO-003','source_confirmed_gap':'IO admission was checked only by withContext, not between blocking JNI creation and synchronous native show. Cancellation at creation could still open a modal after composition disposal.','control_failed':3,'green_passed':5,'negative_control_is_not_the_original_new_api':True,'all_inputs_held':True,'root_filesystem_outputs_written':False,'no_gradle_or_downloads':True,'remaining':['Full module/JNI/native parent/Compose disposal/live-dialog/minimum-platform verification and the original IO-003 acceptance matrix remain open.'],'no_issue_closure':True},indent=2)+'\n')
