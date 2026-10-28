import org.gradle.api.Project
import org.gradle.api.file.DuplicatesStrategy
import org.gradle.api.tasks.Copy
import org.gradle.api.tasks.Exec
import org.gradle.api.tasks.testing.Test
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.register
import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension

/** Shared native artifact pipeline. No directory-content heuristic can bypass validation. */
fun Project.configureNativeLibrary() {
    check(name in setOf("calf-file-picker", "calf-share")) { "Unexpected native module $path" }
    val moduleName = name
    val root = rootProject.layout.projectDirectory
    val script = root.file("scripts/native/artifacts.py")
    val platform = nativeHostPlatform()
    val mode = providers.gradleProperty("nativecmpkitNativeMode").orElse("host").get()
    require(mode in setOf("host", "release")) { "nativecmpkitNativeMode must be host or release" }
    val prebuilt = providers.gradleProperty("nativecmpkitNativePrebuiltDir")
    require(mode != "release" || prebuilt.isPresent) {
        "Release assembly requires an explicit -PnativecmpkitNativePrebuiltDir with all five verified module/target payloads"
    }
    val python = providers.gradleProperty("nativecmpkitPython")
        .orElse(if (platform.startsWith("windows-")) "python" else "python3")
    val hostOutput = layout.buildDirectory.dir("native-host")
    val resourceOutput = layout.buildDirectory.dir("native-libs")
    val sourceInput = if (prebuilt.isPresent) rootProject.file(prebuilt.get()).resolve(moduleName)
                      else hostOutput.get().asFile
    val nativeInputs = files(
        fileTree("native") { exclude("target/**", ".git/**", "**/.gitignore") },
        fileTree("src/desktopMain/kotlin"),
        layout.projectDirectory.file("build.gradle.kts"),
        root.file("rust-toolchain.toml"), script,
        root.file("convention-plugins/src/main/kotlin/NativeLibraries.kt"),
        fileTree(root.dir(".cargo")) { include("config", "config.toml") },
        fileTree(layout.projectDirectory.dir(".cargo")) { include("config", "config.toml") },
    )
    val revision = providers.exec {
        workingDir(root)
        commandLine("git", "rev-parse", "HEAD")
    }.standardOutput.asText.map(String::trim)
    val sourceDirty = providers.exec {
        workingDir(root)
        commandLine("git", "status", "--porcelain", "--untracked-files=normal")
    }.standardOutput.asText.map { it.isNotBlank() }
    val legacyNative = fileTree("src/desktopMain/resources/native")
    val commonArguments = listOf(script.asFile.absolutePath, "--root", root.asFile.absolutePath, "--module", moduleName)

    val buildNativeLib = tasks.register<Exec>("buildNativeLib") {
        group = "native"
        description = "Build the actual host with pinned Rust/--locked and emit checked provenance."
        workingDir(root)
        inputs.files(nativeInputs).withPropertyName("nativeSources")
        inputs.property("platform", platform)
        inputs.property("libraryVersion", project.version.toString())
        inputs.property("sourceRevision", revision)
        inputs.property("sourceTreeDirty", sourceDirty)
        inputs.property("python", python)
        // A poisoned override must execute and fail instead of reusing an old UP-TO-DATE result.
        // Names only are recorded; environment values are never retained in task evidence.
        inputs.property("customRustOverrideNames", providers.provider {
            System.getenv().filter { (key, value) ->
                value.isNotEmpty() && (key in setOf("RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC",
                    "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_TARGET", "CARGO_TARGET_DIR",
                    "RUSTC_BOOTSTRAP", "CFLAGS", "CXXFLAGS", "LDFLAGS") || key.startsWith("CARGO_PROFILE_") ||
                    (key.startsWith("CARGO_TARGET_") && (key.endsWith("_RUSTFLAGS") || key.endsWith("_LINKER"))))
            }.keys.sorted().joinToString("\n")
        })
        outputs.dir(hostOutput).withPropertyName("hostNativeResources")
        // Host linker/SDK inputs are not fully hermetic. Incremental execution is supported;
        // remote Gradle caching of compiled native binaries is deliberately not claimed.
        outputs.doNotCacheIf("Native compiler/linker host is not a hermetic build environment") { true }
        commandLine(listOf(python.get()) + commonArguments + listOf("build", "--platform", platform,
            "--output", hostOutput.get().asFile.absolutePath,
            "--cargo-target-dir", layout.buildDirectory.dir("rust").get().asFile.absolutePath,
            "--version", project.version.toString()))
    }

    val prepare = tasks.register<Exec>("prepareNativeResources") {
        group = "native"
        description = "Fail closed on stale/corrupt/foreign/incomplete native inputs, then stage only this module."
        if (!prebuilt.isPresent) dependsOn(buildNativeLib)
        workingDir(root)
        inputs.files(nativeInputs).withPropertyName("nativeSources")
        inputs.dir(sourceInput).withPropertyName("explicitNativeInput")
        inputs.files(legacyNative).withPropertyName("rejectedLegacyInput")
        inputs.property("mode", mode)
        inputs.property("sourceRevision", revision)
        inputs.property("sourceTreeDirty", sourceDirty)
        inputs.property("libraryVersion", project.version.toString())
        outputs.dir(resourceOutput).withPropertyName("verifiedNativeResources")
        doFirst {
            check(legacyNative.isEmpty) {
                "Legacy src/desktopMain/resources/native payloads are forbidden. Use explicit manifest-verified prebuilt inputs."
            }
        }
        val matrixArguments = if (mode == "release") listOf("--full-matrix", "--require-clean")
                              else listOf("--platform", platform)
        commandLine(listOf(python.get()) + commonArguments + listOf("assemble", "--input", sourceInput.absolutePath,
            "--output", resourceOutput.get().asFile.absolutePath, "--version", project.version.toString()) + matrixArguments)
    }

    tasks.register("copyNativeLib") {
        group = "native"
        description = "Compatibility alias for strict prepareNativeResources."
        dependsOn(prepare)
    }
    tasks.register<Exec>("verifyNativeResources") {
        group = "verification"
        description = "Revalidate the resources that will enter this desktop JAR; never claims JNI execution."
        dependsOn(prepare)
        workingDir(root)
        val matrixArguments = if (mode == "release") listOf("--full-matrix", "--require-clean")
                              else listOf("--platform", platform)
        commandLine(listOf(python.get()) + commonArguments + listOf("verify", "--input",
            resourceOutput.get().asFile.absolutePath, "--version", project.version.toString()) + matrixArguments)
    }

    extensions.configure<KotlinMultiplatformExtension> {
        sourceSets.named("desktopMain") { resources.srcDir(resourceOutput) }
    }
    tasks.withType(Test::class.java).matching { it.name == "desktopTest" }.configureEach {
        // Gradle 9.7's test loader is not a URLClassLoader. Child-JVM JNI tests
        // need the task's real runtime files, not java.class.path's worker launcher
        // or reflection into Gradle internals. This property is test-only.
        doFirst { systemProperty("nativecmpkit.test.runtimeClasspath", classpath.asPath) }
    }
    tasks.register("writeNativeTestRuntimeClasspath") {
        group = "verification"
        description = "Prepare real test runtime files for separate privileged native boundary probes; runs no tests."
        dependsOn("desktopTestClasses")
        val destination = layout.buildDirectory.file("native-boundary-runtime/classpath.txt")
        outputs.file(destination)
        outputs.upToDateWhen { false }
        doLast {
            val runtime = (tasks.getByName("desktopTest") as Test).classpath.files
            val output = destination.get().asFile
            output.parentFile.mkdirs()
            output.writeText(runtime.joinToString("\n") { it.absolutePath } + "\n")
        }
    }
    tasks.withType(Copy::class.java).matching { it.name == "desktopProcessResources" }.configureEach {
        dependsOn(prepare)
        duplicatesStrategy = DuplicatesStrategy.FAIL
        // KGP/Compose's overlapping material/nonAndroid source hierarchy can
        // visit one originating resource file more than once. Do not weaken
        // collision checks globally: skip only the identical originating path
        // at the identical destination. Distinct source files targeting the
        // same resource name (even equal bytes) must still fail.
        val originatingFiles = mutableMapOf<String, String>()
        doFirst { originatingFiles.clear() }
        eachFile {
            val destination = relativePath.pathString
            val origin = file.absoluteFile.normalize().path
            val previous = originatingFiles.putIfAbsent(destination, origin)
            if (previous == origin) exclude()
        }
    }
}

private fun nativeHostPlatform(): String {
    val os = System.getProperty("os.name").lowercase()
    val arch = when (System.getProperty("os.arch").lowercase()) {
        "amd64", "x86_64" -> "x64"
        "aarch64", "arm64" -> "arm64"
        else -> error("Unsupported native host architecture")
    }
    return when {
        os.contains("linux") -> "linux-$arch"
        os.contains("mac") -> "macos-$arch"
        os.contains("windows") && arch == "x64" -> "windows-x64"
        else -> error("Unsupported native host. Windows arm64 has no verified packaged runtime; no fallback is provided.")
    }
}
