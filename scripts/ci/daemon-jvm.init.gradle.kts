// NativeCmpKit verification: observe the real root daemon, not the shell's java executable.
// No home path, environment dump, credentials, JVM arguments or machine transcript is exported.
import java.nio.file.Files
import java.nio.file.Path

fun daemonJsonString(value: String): String = "\"" + value.flatMap { character ->
    when (character) {
        '"' -> "\\\"".toList()
        '\\' -> "\\\\".toList()
        '\n' -> "\\n".toList()
        '\r' -> "\\r".toList()
        '\t' -> "\\t".toList()
        else -> {
            check(character.code >= 32) { "Unexpected daemon observation control character" }
            listOf(character)
        }
    }
}.joinToString("") + "\""

gradle.settingsEvaluated {
    if (rootProject.name == "NativeCmpKit") {
        val major = Runtime.version().feature()
        check(major == 17) { "NativeCmpKit verification requires an actual JDK17 daemon" }
        val launcherHome = System.getenv("JAVA_HOME")
        val matchesLauncher = launcherHome?.let {
            Files.isSameFile(Path.of(it), Path.of(System.getProperty("java.home")))
        }
        val values = listOf(
            "schema_version" to "1",
            "major" to major.toString(),
            "java_version" to daemonJsonString(System.getProperty("java.version")),
            "java_vendor" to daemonJsonString(System.getProperty("java.vendor")),
            "runtime_version" to daemonJsonString(Runtime.version().toString()),
            "gradle_version" to daemonJsonString(gradle.gradleVersion),
            "launcher_home_configured" to (launcherHome != null).toString(),
            "launcher_home_matches_daemon" to (matchesLauncher?.toString() ?: "null"),
        )
        println("NATIVECMPKIT_DAEMON_JVM " + values.joinToString(",", "{", "}") { (key, value) -> daemonJsonString(key) + ":" + value })
    }
}
