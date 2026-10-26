// Task-owned selected-property probe, not Gradle/Kotlin/Native execution.
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

class RuntimePathProbe {
    public static void main(String[] arguments) {
        Path root = Path.of(arguments[0]).toAbsolutePath();
        Map<String, String> properties = Map.of(
            "user.home", ".dependency-home",
            "java.io.tmpdir", ".dependency-home/tmp",
            "gradle.user.home", ".dependency-cache",
            "kotlin.daemon.runFilesPath", ".dependency-home/kotlin-daemon");
        Map<String, String> environment = Map.of(
            "HOME", ".dependency-home", "GRADLE_USER_HOME", ".dependency-cache",
            "KONAN_DATA_DIR", ".dependency-home/konan", "TMPDIR", ".dependency-home/tmp",
            "TMP", ".dependency-home/tmp", "TEMP", ".dependency-home/tmp",
            "XDG_CACHE_HOME", ".dependency-home/cache", "XDG_CONFIG_HOME", ".dependency-home/config",
            "XDG_DATA_HOME", ".dependency-home/data", "XDG_STATE_HOME", ".dependency-home/state");
        Map<String, Boolean> result = new LinkedHashMap<>();
        properties.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry ->
            result.put("property:" + entry.getKey(), root.resolve(entry.getValue()).toString().equals(System.getProperty(entry.getKey()))));
        environment.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry ->
            result.put("environment:" + entry.getKey(), root.resolve(entry.getValue()).toString().equals(System.getenv(entry.getKey()))));
        result.put("jdk17", Runtime.version().feature() == 17);
        System.out.println("{");
        int index = 0;
        for (Map.Entry<String, Boolean> entry : result.entrySet()) {
            System.out.println("  \"" + entry.getKey() + "\": " + entry.getValue() + (++index < result.size() ? "," : ""));
        }
        System.out.println("}");
        if (result.containsValue(false)) throw new IllegalStateException("Selected private runtime location did not match");
    }
}
