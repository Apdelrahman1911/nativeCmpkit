import org.junit.runner.*;
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
}