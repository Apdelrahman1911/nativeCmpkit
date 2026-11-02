// Explicit test-only artifact adoption. No ordinary Gradle build loads this file.
// Replace one original web JAR; never add duplicate/shadow classes or route flags.
import java.security.MessageDigest
import java.util.jar.JarFile
import org.gradle.api.tasks.testing.Test

fun candidateDigest(file: java.io.File): String {
    val digest = MessageDigest.getInstance("SHA-256")
    file.inputStream().use { input ->
        val buffer = ByteArray(65536)
        while (true) {
            val count = input.read(buffer)
            if (count < 0) break
            digest.update(buffer, 0, count)
        }
    }
    return digest.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
}

gradle.projectsEvaluated {
    if (rootProject.name == "NativeCmpKit") {
        val selected = "com.mohamedrejeb.calf.ui.web.DesktopWebViewStopRedirectAcceptanceTest." +
            "publicStopCancelsOneHeldNativeRequestBeforeAnyResponseAndRecoversOnTheSameOwner"
        // Gradle9.7.1 getTaskNames flattens TaskExecutionRequest.args, including
        // task-specific --tests and its value; it is not a task-path-only list.
        check(startParameter.taskNames == listOf(":calf-webview:desktopTest", "--tests", selected)) {
            "Private JavaFX candidate permits only the failed library Desktop Stop task"
        }
        val project = rootProject.project(":calf-webview")
        val directory = project.providers.gradleProperty("nativecmpkitJavaFxCandidateRoot").get()
        val expected = project.providers.gradleProperty("nativecmpkitJavaFxCandidateSha256").get()
        val classifier = project.providers.gradleProperty("nativecmpkitJavaFxCandidateClassifier").orElse("win").get()
        val originalDigests = mapOf(
            "win" to "0f9bd11152b5b64c6753ba81db96ba9b6b6f16bbc5149a979bab18ef97540224",
            "linux-aarch64" to "762e3bd7dfbabb418e65e3107e48fcfe7bd43437afeadd641855708f109503af",
            "mac" to "c6cc19654dbe20cad85dda8df4731f0151c7abcdb16a91b2116d92a16fbf4255",
            "mac-aarch64" to "7a25cc46dc6c5ebb16a4d1d43b8d25d4f6503cefcd7a9071e69802ca1f1ea494",
        )
        check(classifier in originalDigests) { "Only an exact failed-host candidate classifier is allowed" }
        check(Regex("[0-9a-f]{64}").matches(expected)) { "Missing exact generated artifact SHA256" }
        val root = rootProject.file(directory).canonicalFile
        val allowed = rootProject.file("build/ci-verification").canonicalFile
        check(root.toPath().startsWith(allowed.toPath()) && root != allowed) {
            "Candidate must belong to the owned verification output, not a dependency cache"
        }
        val candidate = java.io.File(root, "javafx-web-21.0.13-nativecmpkit-cancel1-local-$classifier.jar")
        project.tasks.named("desktopTest", Test::class.java).configure {
            inputs.file(candidate)
            inputs.property("nativecmpkitJavaFxCandidateSha256", expected)
            inputs.property("nativecmpkitJavaFxCandidateClassifier", classifier)
            outputs.upToDateWhen { false }
            outputs.doNotCacheIf("Private dependency candidate requires actual fresh native execution") { true }
            maxParallelForks = 1
            forkEvery = 1L
            filter {
                setIncludePatterns(selected)
                isFailOnNoMatchingTests = true
            }
            doFirst {
                val system = System.getProperty("os.name")
                val architecture = System.getProperty("os.arch").lowercase()
                check((classifier == "win" && system.startsWith("Windows") && architecture in setOf("amd64", "x86_64")) ||
                    (classifier == "linux-aarch64" && system == "Linux" && architecture in setOf("aarch64", "arm64")) ||
                    (classifier == "mac" && system.startsWith("Mac") && architecture in setOf("amd64", "x86_64")) ||
                    (classifier == "mac-aarch64" && system.startsWith("Mac") && architecture in setOf("aarch64", "arm64"))) {
                    "Candidate classifier must match the actual Windows x64, Linux ARM64 or macOS daemon; never an override"
                }
                check(Runtime.version().feature() == 17) { "Candidate library test requires JDK17" }
                check(candidate.isFile && candidateDigest(candidate) == expected) {
                    "Generated candidate artifact changed or is absent"
                }
                check(allJvmArgs.none { it.contains("useHTTP2Loader") || it.startsWith("--patch-module") }) {
                    "No runtime route override or module patch: test the complete replacement JAR"
                }
                val originalFiles = classpath.files.toList()
                val webProviders = originalFiles.filter { file ->
                    if (file.isDirectory) java.io.File(file, "javafx/scene/web/WebEngine.class").exists()
                    else if (file.extension == "jar") JarFile(file).use {
                        it.getJarEntry("javafx/scene/web/WebEngine.class") != null
                    } else false
                }
                check(webProviders.size == 1 && webProviders.single().name == "javafx-web-21.0.13-$classifier.jar") {
                    "Exactly one original pinned web class provider must be replaced; no shadow classpath"
                }
                val original = webProviders.single()
                val originalSha = originalDigests.getValue(classifier)
                check(candidateDigest(original) == originalSha && candidate.canonicalFile != original.canonicalFile) {
                    "Original JavaFX dependency changed or candidate would overwrite it"
                }
                classpath = project.files(originalFiles.filterNot { it == original } + candidate)
                check(classpath.files.count { it == candidate } == 1 && original !in classpath.files) {
                    "Candidate replacement did not remove the original provider"
                }
                logger.lifecycle("NATIVECMPKIT_JAVAFX_CANDIDATE task=$path originalRemoved=1 candidateCount=1 " +
                    "originalSha256=$originalSha candidateSha256=$expected runtimeModulePatch=false privateRouteOverride=false")
            }
        }
    }
}
