import java.nio.file.Files
import java.nio.file.Path

gradle.settingsEvaluated {
    if (rootProject.name == "NativeCmpKit") {
        check(providers.gradleProperty("org.gradle.java.installations.auto-download").orNull == "false")
        check(providers.gradleProperty("org.gradle.java.installations.auto-detect").orNull == "false")
        val requested = providers.gradleProperty("org.gradle.java.installations.paths").get()
        check(!requested.contains(','))
        check(Files.isSameFile(Path.of(requested), Path.of(System.getProperty("java.home"))))
        println("NATIVECMPKIT_JDK_PROVISIONING {\"schema_version\":1,\"auto_download\":false,\"auto_detect\":false,\"only_requested_installation_matches_daemon\":true}")
    }
}
