import com.android.build.api.dsl.KotlinMultiplatformAndroidLibraryTarget
import java.io.File
import java.security.MessageDigest
import org.gradle.api.artifacts.component.ModuleComponentIdentifier
import org.gradle.api.artifacts.component.ProjectComponentIdentifier
import org.gradle.api.plugins.ExtensionAware
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("multiplatform") version "2.4.20"
    id("org.jetbrains.compose") version "1.12.0"
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.20"
    id("com.android.kotlin.multiplatform.library") version "9.4.0" apply false
}

val consumerTargets = providers.gradleProperty("consumerTargets").orElse("desktop")
    .get().split(',').map(String::trim).toSet()
require(consumerTargets.isNotEmpty() && consumerTargets.all { it in setOf("desktop", "android", "web", "ios") }) {
    "consumerTargets must select desktop,android,web,ios (comma separated)"
}
val candidateVersion = providers.gradleProperty("nativecmpkitVersion").orNull
    ?: error("Pass the exact staged -PnativecmpkitVersion (no implicit installed version)")
require(Regex("[0-9]+\\.[0-9]+\\.[0-9]+(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?").matches(candidateVersion)) {
    "nativecmpkitVersion must be an exact version, not a range, path or dynamic selector"
}
val candidateGroup = "io.github.apdelrahman1911.nativecmpkit"

// This list is deliberately independent of the producer's project model. The static validator
// reconciles it with the identity map, so removing an artifact cannot silently shrink the test.
val candidateModules = listOf(
    "camera-picker", "core", "cupertino-icons", "file-picker", "file-picker-coil", "io",
    "permissions", "permissions-background-location", "permissions-bluetooth", "permissions-calendar",
    "permissions-camera", "permissions-contacts", "permissions-core", "permissions-gallery",
    "permissions-location", "permissions-microphone", "permissions-notifications", "permissions-wifi",
    "share", "ui", "webview",
)

if ("android" in consumerTargets) apply(plugin = "com.android.kotlin.multiplatform.library")

fun consumerJavaFxClassifier(): String {
    val os = System.getProperty("os.name").lowercase()
    val arch = System.getProperty("os.arch").lowercase()
    val arm = arch in setOf("aarch64", "arm64")
    require(arm || arch in setOf("amd64", "x86_64")) { "Unsupported consumer CPU: $arch" }
    return when {
        os.contains("mac") || os.contains("darwin") -> if (arm) "mac-aarch64" else "mac"
        os.contains("win") && !arm -> "win"
        os.contains("linux") -> if (arm) "linux-aarch64" else "linux"
        else -> error("No verified nativeCmpkit desktop distribution contract for $os/$arch")
    }
}

kotlin {
    jvmToolchain(17)
    if ("desktop" in consumerTargets) jvm("desktop") {
        compilerOptions.jvmTarget.set(JvmTarget.JVM_17)
    }
    if ("android" in consumerTargets) {
        (this as ExtensionAware).extensions.configure<KotlinMultiplatformAndroidLibraryTarget>("android") {
            namespace = "io.github.apdelrahman1911.nativecmpkit.consumer"
            compileSdk = 37
            minSdk = 23
            compilerOptions.jvmTarget.set(JvmTarget.JVM_17)
            withHostTest {}
        }
    }
    if ("web" in consumerTargets) {
        js {
            binaries.executable()
            browser { testTask { useKarma { useChromeHeadless() } } }
        }
        @OptIn(org.jetbrains.kotlin.gradle.ExperimentalWasmDsl::class)
        wasmJs {
            binaries.executable()
            browser { testTask { useKarma { useChromeHeadless() } } }
        }
    }
    if ("ios" in consumerTargets) {
        iosArm64().binaries.framework { baseName = "NativeCmpkitConsumer"; isStatic = true }
        iosSimulatorArm64().binaries.framework { baseName = "NativeCmpkitConsumer"; isStatic = true }
    }
    applyDefaultHierarchyTemplate()

    sourceSets {
        commonMain.dependencies {
            candidateModules.forEach {
                implementation("$candidateGroup:nativecmpkit-$it:$candidateVersion") {
                    // Local unpublished candidates may be rebuilt with the same draft version.
                    // Re-read only this group instead of needlessly refreshing all third parties.
                    isChanging = true
                }
            }
            // These are deliberate application dependencies for the public Compose/Coil APIs,
            // not substitutes for any nativeCmpkit project or source set.
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation("org.jetbrains.compose.material3:material3:1.12.0-alpha03")
            implementation("io.coil-kt.coil3:coil:3.6.2")
        }
        commonTest.dependencies { implementation(kotlin("test")) }
        if ("desktop" in consumerTargets) {
            named("desktopMain") {
                dependencies {
                    implementation(compose.desktop.currentOs)
                    // JavaFX native selection belongs to THIS consuming host, never the publisher.
                    val classifier = consumerJavaFxClassifier()
                    listOf("base", "graphics", "controls", "media", "web", "swing").forEach {
                        implementation("org.openjfx:javafx-$it:21.0.13:$classifier")
                    }
                }
            }
            named("desktopTest") {
                dependencies { implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.11.0") }
            }
        }
    }
}

configurations.configureEach {
    resolutionStrategy.cacheChangingModulesFor(0, "seconds")
}

fun artifactSha256(file: File): String {
    val digest = MessageDigest.getInstance("SHA-256")
    file.inputStream().use { stream ->
        val buffer = ByteArray(64 * 1024)
        while (true) {
            val read = stream.read(buffer)
            if (read < 0) break
            digest.update(buffer, 0, read)
        }
    }
    return digest.digest().joinToString("") { "%02x".format(it) }
}

tasks.withType<Test>().configureEach {
    maxParallelForks = 1
    // A JNI contract violation must not be hidden by the VM's unchecked fast path.
    jvmArgs("-Xcheck:jni")
    val nativeHome = layout.buildDirectory.dir("isolated-native-home/$name")
    val emptyLibraryPath = layout.buildDirectory.dir("empty-java-library-path/$name")
    // Do not let a developer's separately installed old native library satisfy this test.
    systemProperty("java.library.path", emptyLibraryPath.get().asFile.absolutePath)
    systemProperty("user.home", nativeHome.get().asFile.absolutePath)
    doFirst {
        nativeHome.get().asFile.mkdirs()
        emptyLibraryPath.get().asFile.mkdirs()
        check(emptyLibraryPath.get().asFile.listFiles()?.isEmpty() == true)
    }
    testLogging { events("passed", "skipped", "failed") }
}

// Resolve real published metadata, fail on any substitution into producer projects, and record
// the exact artifact identifiers/files in this standalone build's own output directory.
tasks.register("verifyCandidateResolution") {
    group = "verification"
    description = "Verify all selected consumer classpaths resolve candidate Maven artifacts, not project substitutions"
    val report = layout.buildDirectory.file("reports/consumer-resolution.txt")
    outputs.file(report)
    // Resolution is a verification action; stale output is not accepted as a current receipt.
    outputs.upToDateWhen { false }
    doLast {
        val lines = mutableListOf<String>()
        val candidates = mutableSetOf<String>()
        configurations.filter { it.isCanBeResolved && (it.name.contains("CompileClasspath") || it.name.contains("RuntimeClasspath") || it.name.contains("CompileKlibraries")) }
            .sortedBy { it.name }.forEach { configuration ->
                configuration.incoming.artifacts.artifacts.sortedBy { it.id.displayName }.forEach { artifact ->
                    val id = artifact.id.componentIdentifier
                    check(id !is ProjectComponentIdentifier) { "Project substitution in ${configuration.name}: $id" }
                    if (id is ModuleComponentIdentifier) {
                        check(id.group != "com.mohamedrejeb.calf") { "Unexpected original Calf dependency: $id" }
                        if (id.group == candidateGroup) {
                            check(id.version == candidateVersion) { "Wrong candidate version: $id" }
                            candidates += id.module
                            val staged = file(providers.gradleProperty("nativecmpkitRepository").get())
                                .resolve("${candidateGroup.replace('.', '/')}/${id.module}/$candidateVersion/${artifact.file.name}")
                            check(staged.isFile && artifactSha256(staged) == artifactSha256(artifact.file)) {
                                "Resolved candidate bytes do not directly match staged Maven artifact: $id/${artifact.file.name}"
                            }
                        }
                    }
                    lines += "${configuration.name}\t${id.displayName}\t${artifact.file.name}\t${artifactSha256(artifact.file)}"
                }
            }
        check(candidates.isNotEmpty()) { "No candidate artifact was actually resolved" }
        val missing = candidateModules.filter { name ->
            val root = "nativecmpkit-$name"
            val allowed = setOf(root, "$root-desktop", "$root-android", "$root-js", "$root-wasm-js", "$root-iosarm64", "$root-iossimulatorarm64")
            candidates.none { it in allowed }
        }
        check(missing.isEmpty()) { "Candidate modules missing from resolved classpaths: $missing" }
        report.get().asFile.apply { parentFile.mkdirs(); writeText(lines.joinToString("\n", postfix = "\n")) }
        println("Resolved ${candidates.size} candidate variants from ${candidateModules.size} publication roots")
    }
}
