import javax.net.ssl.HttpsURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.HexFormat;
public class TlsProbe {
 public static void main(String[] args) throws Exception {
  System.out.println("java="+System.getProperty("java.version")+" protocol="+System.getProperty("https.protocols","default"));
  HttpsURLConnection c=(HttpsURLConnection)new URL(args[0]).openConnection();
  c.setConnectTimeout(10000);c.setReadTimeout(10000);
  int status=c.getResponseCode();System.out.println("status="+status+" cipher="+c.getCipherSuite());
  try(var s=c.getInputStream()){byte[] bytes=s.readAllBytes();System.out.println("bytes="+bytes.length+" sha256="+HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));}
 }
}
