from pathlib import Path
import datetime as dt, hashlib, json, os, shutil, sys
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/native-cache-tests/green-20261027-001'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
assert not OUT.exists();OUT.mkdir(parents=True)
CACHE=Path('/root/.gradle/caches/modules-2/files-2.1')
def jar(group,artifact,version):
    paths=list((CACHE/group/artifact/version).glob(f'*/{artifact}-{version}.jar'));assert len(paths)==1;return paths[0]
coords=[('org.jetbrains.kotlin','kotlin-stdlib','2.4.20'),('org.jetbrains.kotlin','kotlin-test','2.4.20'),('org.jetbrains.kotlin','kotlin-test-junit','2.4.20'),('junit','junit','4.13.2'),('org.hamcrest','hamcrest-core','1.3'),('org.jetbrains','annotations','13.0')]
runtime=[jar(*c) for c in coords]
compiler_coords=[('org.jetbrains.kotlin','kotlin-compiler-embeddable','2.4.20'),('org.jetbrains.kotlin','kotlin-script-runtime','2.4.20'),('org.jetbrains.kotlin','kotlin-reflect','1.6.10'),('org.jetbrains.kotlin','kotlin-daemon-embeddable','2.4.20'),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm','1.8.0')]
compiler=[jar(*c) for c in compiler_coords]+runtime
sources=['calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCache.kt',
 'calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCacheTest.kt',
 'calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/NativeCacheIsolationTest.kt',
 'calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/NativeFileSystemFixtures.kt',
 'calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibCache.kt',
 'calf-share/src/desktopTest/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibCacheTest.kt',
 'calf-share/src/desktopTest/kotlin/com/mohamedrejeb/calf/share/platform/NativeFileSystemFixtures.kt']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selected=lt.snapshot_inputs(ROOT);lt.write_json(OUT/'inputs-before.json',selected)
for name in sources:
    p=OUT/'source-held'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
java=Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java');javac=java.with_name('javac');assert java.is_file() and javac.is_file()
classes=OUT/'classes';classes.mkdir()
runner=OUT/'RunCacheTests.java'
runner.write_text(r'''import java.nio.file.*;
import java.util.*;
import javax.xml.parsers.*;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.junit.runner.*;
import org.junit.runner.notification.*;
public final class RunCacheTests {
  public static void main(String[] args) throws Exception {
    var doc = DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument();
    var suite = doc.createElement("testsuite"); suite.setAttribute("name", "actual-native-cache-source-tests"); doc.appendChild(suite);
    Map<Description,org.w3c.dom.Element> cases = new LinkedHashMap<>();
    JUnitCore core = new JUnitCore();
    core.addListener(new RunListener() {
      public void testStarted(Description d) {
        var c=doc.createElement("testcase"); c.setAttribute("classname",d.getClassName());c.setAttribute("name",d.getMethodName());suite.appendChild(c);cases.put(d,c);
      }
      public void testFailure(Failure f) {
        var c=cases.get(f.getDescription());if(c==null)throw new AssertionError("Failure outside a started test");
        c.appendChild(doc.createElement("failure"));
        System.out.println("FAILED "+f.getDescription()+": "+f.getMessage());
      }
      public void testAssumptionFailure(Failure f) { cases.get(f.getDescription()).appendChild(doc.createElement("skipped")); }
      public void testIgnored(Description d) { throw new AssertionError("No ignored native filesystem tests are permitted in this selected source suite"); }
    });
    Class<?>[] types = {Class.forName("com.mohamedrejeb.calf.picker.platform.NativeLibCacheTest"),
        Class.forName("com.mohamedrejeb.calf.picker.platform.NativeCacheIsolationTest"),Class.forName("com.mohamedrejeb.calf.share.platform.NativeLibCacheTest")};
    org.junit.runner.Result result=core.run(types);
    suite.setAttribute("tests",Integer.toString(result.getRunCount())); suite.setAttribute("failures",Integer.toString(result.getFailureCount()));
    suite.setAttribute("skipped",Integer.toString(result.getAssumptionFailureCount()));suite.setAttribute("errors","0");
    TransformerFactory.newInstance().newTransformer().transform(new DOMSource(doc),new StreamResult(Path.of(args[0]).toFile()));
    System.out.println("Actual JDK "+System.getProperty("java.runtime.version")+" / "+System.getProperty("os.name")+" / "+System.getProperty("os.arch"));
    System.out.println("Tests run: "+result.getRunCount()+", failures: "+result.getFailureCount()+", assumptions: "+result.getAssumptionFailureCount());
    System.exit(result.wasSuccessful()?0:1);
  }
}
''')
runtime_cp=os.pathsep.join(str(p) for p in runtime)
compiler_cp=os.pathsep.join(str(p) for p in compiler)
commands=[('kotlin-compile',[str(java),'-Xmx512m','-cp',compiler_cp,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-jvm-target','17','-classpath',runtime_cp,'-d',str(classes),*[str(OUT/'source-held'/n) for n in sources]]),
 ('runner-compile',[str(javac),'-classpath',runtime_cp,'-d',str(classes),str(runner)]),
 ('actual-tests',[str(java),'-Xmx256m','-Xcheck:jni','-cp',str(classes)+os.pathsep+runtime_cp,'RunCacheTests',str(OUT/'TEST-native-cache.xml')])]
results=[]
for name,args in commands:
    result=lt.execute(ROOT,args,OUT/(name+'.log'),180,8192);results.append({'name':name,'command':args,'execution':result,'log_sha256':sha(OUT/(name+'.log')) if (OUT/(name+'.log')).is_file() else None})
    if result['exit_code']!=0:break
lt.write_json(OUT/'inputs-after.json',lt.snapshot_inputs(ROOT))
record={'source_revision':lt.git_revision(ROOT),'source_tree_dirty':True,'observed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_input_count':len(selected),'selected_source_unchanged':lt.snapshot_inputs(ROOT)==selected,'results':results,'source_files':{p:sha(ROOT/p) for p in sources},'dependencies':[{'coordinate':':'.join(c),'sha256':sha(jar(*c))} for c in coords+compiler_coords],'runner_sha256':sha(runner),'driver_sha256':sha(Path(__file__)),'scope':'Actual Linux/JDK17 source-level library filesystem tests with Kotlin2.4.20/JUnit4 and real cached dependencies; no stubs. No Gradle packaging, Windows ACL/junction, JNI loading, release or consumer certification.','packages_published':False,'release_gate_cleared':False}
if (OUT/'TEST-native-cache.xml').is_file():
    cases=lt.junit_cases((OUT/'TEST-native-cache.xml').read_bytes());record['cases']=cases;record['totals']=lt.case_counts(cases)
    record['red_defect_reproduced']=len([c for c in cases if c['status']=='failed'])==1 and any(c['classname']=='com.mohamedrejeb.calf.share.platform.NativeLibCacheTest' and c['name']=='foreignWritableCacheIsRejectedWithoutRepairingItsPermissions' and c['status']=='failed' for c in cases)
lt.write_json(OUT/'receipt.json',record)
print(json.dumps({k:record[k] for k in ['source_input_count','selected_source_unchanged','totals','red_defect_reproduced'] if k in record},indent=2))
for row in results:print(row['name'],row['execution'])
sys.exit(results[-1]['execution']['exit_code'] or (0 if record['selected_source_unchanged'] else 2))
