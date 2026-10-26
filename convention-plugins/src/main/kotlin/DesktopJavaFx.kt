import org.gradle.accessors.dm.LibrariesForLibs
import org.gradle.api.Project
import org.gradle.kotlin.dsl.the

/**
 * Build/test helper only: libraries must NOT publish this producer-host selection.
 * A desktop application selects its own six aligned JavaFX runtime artifacts.
 */
fun Project.javaFxDependencies(): List<String> {
    val os = System.getProperty("os.name").lowercase()
    val arch = System.getProperty("os.arch").lowercase()
    val x64 = arch in setOf("amd64", "x86_64")
    val arm64 = arch in setOf("aarch64", "arm64")
    val classifier = when {
        os.contains("linux") && x64 -> "linux"
        os.contains("linux") && arm64 -> "linux-aarch64"
        os.contains("mac") && x64 -> "mac"
        os.contains("mac") && arm64 -> "mac-aarch64"
        os.contains("windows") && x64 -> "win"
        else -> error("JavaFX desktop runtime is not supported on $os/$arch. " +
            "Supported: Linux x64/arm64, macOS x64/arm64, Windows x64; no classifier fallback.")
    }
    val version = the<LibrariesForLibs>().versions.javafx.get()
    return listOf("base", "graphics", "controls", "media", "web", "swing")
        .map { "org.openjfx:javafx-$it:$version:$classifier" }
}
