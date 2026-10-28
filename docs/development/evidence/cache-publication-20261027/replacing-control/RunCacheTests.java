import java.nio.file.*;
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
    org.junit.runner.Result result;
    if(args.length>1) {
      var selection = org.junit.runner.Request.classes(types).filterWith(new org.junit.runner.manipulation.Filter() {
        public boolean shouldRun(Description d) {
          if(d.isSuite()) { for(var child:d.getChildren()) if(shouldRun(child)) return true;return false; }
          return "latePublisherCannotReplaceAnIdentityAlreadyReturnedToAnOpenReader".equals(d.getMethodName());
        }
        public String describe() { return "Two exact late-publisher native-cache controls only"; }
      });
      result=core.run(selection);
    } else result=core.run(types);
    suite.setAttribute("tests",Integer.toString(result.getRunCount())); suite.setAttribute("failures",Integer.toString(result.getFailureCount()));
    suite.setAttribute("skipped",Integer.toString(result.getAssumptionFailureCount()));suite.setAttribute("errors","0");
    TransformerFactory.newInstance().newTransformer().transform(new DOMSource(doc),new StreamResult(Path.of(args[0]).toFile()));
    System.out.println("Actual JDK "+System.getProperty("java.runtime.version")+" / "+System.getProperty("os.name")+" / "+System.getProperty("os.arch"));
    System.out.println("Tests run: "+result.getRunCount()+", failures: "+result.getFailureCount()+", assumptions: "+result.getAssumptionFailureCount());
    System.exit(result.wasSuccessful()?0:1);
  }
}
