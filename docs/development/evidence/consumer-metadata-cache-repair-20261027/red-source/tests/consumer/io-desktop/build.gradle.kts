import groovy.json.JsonOutput
import java.io.File
import java.security.MessageDigest
import org.gradle.api.artifacts.component.ModuleComponentIdentifier
import org.gradle.api.artifacts.component.ProjectComponentIdentifier
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.4.20"
}

val candidateGroup = "io.github.apdelrahman1911.nativecmpkit"
val candidateVersion = providers.gradleProperty("nativecmpkitVersion").orNull
    ?: error("Pass the exact staged -PnativecmpkitVersion")
require(Regex("[0-9]+\\.[0-9]+\\.[0-9]+(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?").matches(candidateVersion)
    && !candidateVersion.endsWith("-SNAPSHOT")) {
    "nativecmpkitVersion must be an exact non-SNAPSHOT candidate version"
}
// Fixed, independently declared PARTIAL scope. Never replace the 21-root consumer.
val candidateRoots = listOf("nativecmpkit-core", "nativecmpkit-io")
val allowedCandidates = candidateRoots.flatMap { listOf(it, "$it-desktop") }.toSet()
// The JVM plugin supplies a `java` DSL accessor; do not resolve packages through it.
val candidateRepository = File(providers.gradleProperty("nativecmpkitRepository").get())
require(candidateRepository.isAbsolute && candidateRepository.isDirectory)

kotlin {
    jvmToolchain(17)
    compilerOptions.jvmTarget.set(JvmTarget.JVM_17)
}

dependencies {
    candidateRoots.forEach { root ->
        implementation("$candidateGroup:$root:$candidateVersion") { isChanging = true }
    }
    testImplementation(kotlin("test-junit"))
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.11.0")
}

configurations.configureEach { resolutionStrategy.cacheChangingModulesFor(0, "seconds") }

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

val verifyCandidateResolution = tasks.register("verifyCandidateResolution") {
    group = "verification"
    description = "Verify the explicit two-root desktop Maven scope and exact resolved bytes"
    val report = layout.buildDirectory.file("reports/partial-consumer-resolution.json")
    outputs.file(report)
    outputs.upToDateWhen { false }
    doLast {
        val rows = mutableListOf<Map<String, Any>>()
        val candidateVariants = mutableSetOf<String>()
        listOf("compileClasspath", "runtimeClasspath", "testCompileClasspath", "testRuntimeClasspath")
            .forEach { name ->
                val configuration = configurations.getByName(name)
                check(configuration.isCanBeResolved)
                val seen = mutableSetOf<String>()
                configuration.incoming.artifacts.artifacts.sortedBy { it.id.displayName }.forEach { artifact ->
                    val id = artifact.id.componentIdentifier
                    check(id !is ProjectComponentIdentifier) { "Project substitution in $name: $id" }
                    check(id is ModuleComponentIdentifier) { "Non-Maven artifact in $name: $id" }
                    check(id.group != "com.mohamedrejeb.calf") { "Original Calf dependency in $name: $id" }
                    val hash = artifactSha256(artifact.file)
                    if (id.group == candidateGroup) {
                        check(id.version == candidateVersion && id.module in allowedCandidates) {
                            "Wrong candidate coordinate in the partial consumer: $id"
                        }
                        val staged = candidateRepository.resolve(
                            "${candidateGroup.replace('.', '/')}/${id.module}/$candidateVersion/${artifact.file.name}"
                        )
                        check(staged.isFile && artifactSha256(staged) == hash) {
                            "Resolved candidate bytes do not match the actual staged Maven file: $id/${artifact.file.name}"
                        }
                        seen += id.module
                        candidateVariants += id.module
                    }
                    rows += mapOf("configuration" to name, "group" to id.group, "module" to id.module,
                        "version" to id.version, "file" to artifact.file.name, "bytes" to artifact.file.length(),
                        "sha256" to hash)
                }
                check(candidateRoots.all { it in seen || "$it-desktop" in seen }) {
                    "Both Core and IO must resolve from Maven on every selected classpath: $name/$seen"
                }
            }
        val result = mapOf("schema_version" to 1, "scope" to "PARTIAL Core/IO desktop Maven consumer",
            "candidate_group" to candidateGroup, "candidate_version" to candidateVersion,
            "publication_roots_requested" to candidateRoots,
            "candidate_variants_resolved" to candidateVariants.sorted(),
            "complete_21_root_KMP_matrix_requested" to false, "release_readiness_certified" to false,
            "resolved_artifacts" to rows)
        report.get().asFile.apply {
            parentFile.mkdirs()
            writeText(JsonOutput.prettyPrint(JsonOutput.toJson(result)) + "\n")
        }
        println("PARTIAL consumer resolved ${candidateVariants.size} variants from exactly two roots; no release certification")
    }
}

tasks.withType<Test>().configureEach {
    dependsOn(verifyCandidateResolution)
    maxParallelForks = 1
    maxHeapSize = "512m"
    jvmArgs("-Xcheck:jni")
    filter {
        includeTestsMatching("nativecmpkit.consumer.PublishedIoConsumerTest")
        includeTestsMatching("nativecmpkit.consumer.PublishedArtifactOriginTest")
        isFailOnNoMatchingTests = true
    }
    // Always execute all seven methods; an old XML/test task result is not evidence.
    outputs.upToDateWhen { false }
    val ownHome = layout.buildDirectory.dir("test-home/$name")
    val ownTmp = layout.buildDirectory.dir("test-tmp/$name")
    val emptyNativePath = layout.buildDirectory.dir("empty-java-library-path/$name")
    systemProperty("user.home", ownHome.get().asFile.absolutePath)
    systemProperty("java.io.tmpdir", ownTmp.get().asFile.absolutePath)
    systemProperty("java.library.path", emptyNativePath.get().asFile.absolutePath)
    doFirst {
        ownHome.get().asFile.mkdirs()
        ownTmp.get().asFile.mkdirs()
        emptyNativePath.get().asFile.mkdirs()
        check(emptyNativePath.get().asFile.listFiles()?.isEmpty() == true)
        val runtime = configurations.getByName("testRuntimeClasspath").incoming.artifacts.artifacts
        candidateRoots.forEach { root ->
            val artifact = runtime.single { entry ->
                val id = entry.id.componentIdentifier
                id is ModuleComponentIdentifier && id.group == candidateGroup &&
                    id.version == candidateVersion && id.module in setOf(root, "$root-desktop")
            }
            val expectedName = "$root-desktop-$candidateVersion.jar"
            check(artifact.file.name == expectedName)
            val staged = candidateRepository.resolve(
                "${candidateGroup.replace('.', '/')}/$root-desktop/$candidateVersion/$expectedName"
            )
            check(staged.isFile && artifactSha256(staged) == artifactSha256(artifact.file))
            val suffix = root.removePrefix("nativecmpkit-")
            systemProperty("nativecmpkit.expected.$suffix.name", expectedName)
            systemProperty("nativecmpkit.expected.$suffix.sha256", artifactSha256(staged))
        }
        println("NATIVECMPKIT_PARTIAL_CONSUMER_TEST task=$path gradle=${gradle.gradleVersion} java=${JavaVersion.current().majorVersion}")
    }
    testLogging { events("passed", "skipped", "failed") }
}
