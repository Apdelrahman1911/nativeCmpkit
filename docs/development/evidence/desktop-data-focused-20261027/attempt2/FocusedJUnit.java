import org.junit.runner.*;
public class FocusedJUnit {
 public static void main(String[] args) throws Exception {
  Request request = args.length == 2 ? Request.method(Class.forName(args[0]), args[1]) : Request.classes(java.util.Arrays.stream(args).map(n -> {try{return Class.forName(n);}catch(Exception e){throw new RuntimeException(e);}}).toArray(Class[]::new));
  Result r = new JUnitCore().run(request);
  r.getFailures().forEach(f -> System.out.println("FAILURE " + f.getTestHeader() + " " + f.getException()));
  System.out.println("TEST_COUNTS executed="+r.getRunCount()+" failures="+r.getFailureCount()+" ignored="+r.getIgnoreCount());
  System.exit(r.wasSuccessful()?0:1);
 }
}
