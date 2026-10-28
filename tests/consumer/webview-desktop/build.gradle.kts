// Independent WebView-only artifact consumer; original Core/IO fixture is unchanged.
import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import java.io.File
import java.security.MessageDigest
import org.gradle.api.artifacts.component.ModuleComponentIdentifier
import org.gradle.api.artifacts.component.ProjectComponentIdentifier
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.4.20"
    id("org.jetbrains.compose") version "1.12.0"
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.20"
}

val candidateGroup = "io.github.apdelrahman1911.nativecmpkit"
val candidateVersion = providers.gradleProperty("nativecmpkitVersion").orNull
    ?: error("Pass the exact staged -PnativecmpkitVersion")
require(Regex("[0-9]+\\.[0-9]+\\.[0-9]+(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?").matches(candidateVersion)
    && !candidateVersion.endsWith("-SNAPSHOT")) {
    "nativecmpkitVersion must be an exact non-SNAPSHOT candidate version"
}
// Fixed WebView-only scope. Never replace the full21-root or successful Core/IO consumers.
val candidateRoots = listOf("nativecmpkit-webview")
val metadataMode = providers.gradleProperty("nativecmpkitMetadataMode").get()
require(metadataMode in setOf("module", "pom"))
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
        implementation("$candidateGroup:${root + if (metadataMode == "pom") "-desktop" else ""}:$candidateVersion") { isChanging = true }
    }
    implementation(compose.desktop.currentOs)
    implementation("org.jetbrains.compose.material3:material3:1.12.0-alpha03")
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
        else -> error("Unsupported consumer OS/architecture: no classifier fallback")
    }
    listOf("base", "graphics", "controls", "media", "web", "swing").forEach {
        implementation("org.openjfx:javafx-$it:21.0.13:$classifier")
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

/** Exact metadata-to-Maven binding; a retained Gradle display name is not a Maven URL. */
fun bindCandidateArtifact(id: ModuleComponentIdentifier, resolved: File): Map<String, Any> {
    val suffixes = setOf("", "-desktop", "-android", "-js", "-wasm-js", "-iosarm64", "-iossimulatorarm64")
    val matchingRoots = candidateRoots.filter { root -> suffixes.any { id.module == root + it } }
    check(id.group == candidateGroup && id.version == candidateVersion && matchingRoots.size == 1) {
        "Unselected candidate coordinate: $id"
    }
    val root = matchingRoots.single()
    check(resolved.isFile && resolved.extension in setOf("jar", "aar", "klib")) {
        "Only directly published primary candidate files are eligible: $id/${resolved.name}"
    }
    val relativeDirectory = "${candidateGroup.replace('.', '/')}/${id.module}/$candidateVersion/"
    val metadataRelative = relativeDirectory + "${id.module}-$candidateVersion.module"
    val metadataFile = candidateRepository.resolve(metadataRelative)
    check(metadataFile.isFile && metadataFile.length() in 1..(2L * 1024 * 1024))
    val metadata = JsonSlurper().parse(metadataFile) as? Map<*, *> ?: error("Invalid module metadata: $id")
    val component = metadata["component"] as? Map<*, *> ?: error("Missing metadata component: $id")
    check(metadata["formatVersion"] == "1.1" && component["group"] == candidateGroup &&
        component["module"] == root && component["version"] == candidateVersion)
    val rootMetadataRelative = "${candidateGroup.replace('.', '/')}/$root/$candidateVersion/$root-$candidateVersion.module"
    check(candidateRepository.resolve(rootMetadataRelative).isFile)
    val rootUrl = if (id.module == root) null else "../../$root/$candidateVersion/$root-$candidateVersion.module"
    check(component["url"] == rootUrl) { "Module metadata redirects outside the exact candidate root: $id" }
    val canonicalName = "${id.module}-$candidateVersion.${resolved.extension}"
    // These explicit roots/target suffixes map to the retained public Calf Gradle project names.
    // Never accept an arbitrary filename, another group/module, sources or a URL/path alias.
    val retainedName = "calf-${id.module.removePrefix("nativecmpkit-")}-$candidateVersion.${resolved.extension}"
    val variants = metadata["variants"] as? List<*> ?: error("Missing metadata variants: $id")
    check(variants.size in 1..128)
    val primaryBindings = variants.mapNotNull { entry ->
        val variant = entry as? Map<*, *> ?: error("Invalid metadata variant: $id")
        val attributes = variant["attributes"] as? Map<*, *> ?: error("Missing variant attributes: $id")
        if (attributes["org.gradle.category"] != "library") return@mapNotNull null
        // KMP root available-at variants have no local files; they are not payload substitutions.
        val files = variant["files"] as? List<*> ?: return@mapNotNull null
        check(files.size == 1)
        val declared = files.single() as? Map<*, *> ?: error("Invalid primary metadata file: $id")
        check(declared["name"] in setOf(canonicalName, retainedName) && (if (metadataMode == "module") declared["name"] else canonicalName) == resolved.name &&
            declared["url"] == canonicalName) { "Resolved name/metadata URL do not bind to the exact candidate: $id" }
        val stagedRelative = relativeDirectory + canonicalName
        val staged = candidateRepository.resolve(stagedRelative)
        val hash = artifactSha256(resolved)
        check(staged.isFile && artifactSha256(staged) == hash && staged.length() == resolved.length()) {
            "Resolved candidate bytes do not match the actual staged Maven file: $id/${resolved.name}"
        }
        check((declared["size"] is Int || declared["size"] is Long) &&
            (declared["size"] as Number).toLong() == resolved.length() && declared["sha256"] == hash) {
            "Module metadata size/hash does not match staged/resolved bytes: $id"
        }
        mapOf("declared_file_name" to (declared["name"] as String), "resolved_file_name" to resolved.name, "declared_file_url" to canonicalName,
            "staged_file" to stagedRelative, "metadata_file" to metadataRelative,
            "metadata_sha256" to artifactSha256(metadataFile), "bytes" to resolved.length(), "sha256" to hash)
    }.distinct()
    check(primaryBindings.size == 1) { "Missing or conflicting primary metadata bindings: $id" }
    return primaryBindings.single()
}

val verifyCandidateResolution = tasks.register("verifyCandidateResolution") {
    group = "verification"
    description = "Verify the explicit two-root desktop Maven scope and exact resolved bytes"
    val report = layout.buildDirectory.file("reports/webview-consumer-resolution.json")
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
                        seen += id.module
                        candidateVariants += id.module
                    }
                    rows += mapOf("configuration" to name, "group" to id.group, "module" to id.module,
                        "version" to id.version, "file" to artifact.file.name, "bytes" to artifact.file.length(),
                        "sha256" to hash) + (if (id.group == candidateGroup) bindCandidateArtifact(id, artifact.file) else emptyMap())
                }
                check(candidateRoots.all { it in seen || "$it-desktop" in seen }) {
                    "The WebView root must resolve from Maven on every selected classpath: $name/$seen"
                }
            }
        val result = mapOf("schema_version" to 2, "scope" to "PARTIAL WebView desktop Maven consumer",
            "candidate_group" to candidateGroup, "candidate_version" to candidateVersion,
            "publication_roots_requested" to candidateRoots,
            "metadata_mode" to providers.gradleProperty("nativecmpkitMetadataMode").get(),
            "candidate_variants_resolved" to candidateVariants.sorted(),
            "complete_21_root_KMP_matrix_requested" to false, "release_readiness_certified" to false,
            "resolved_artifacts" to rows)
        report.get().asFile.apply {
            parentFile.mkdirs()
            writeText(JsonOutput.prettyPrint(JsonOutput.toJson(result)) + "\n")
        }
        println("PARTIAL consumer resolved ${candidateVariants.size} variants from the explicit WebView root; no release certification")
    }
}

tasks.withType<Test>().configureEach {
    dependsOn(verifyCandidateResolution)
    maxParallelForks = 1
    maxHeapSize = "512m"
    jvmArgs("-Xcheck:jni")
    filter {
        includeTestsMatching("nativecmpkit.consumer.PublishedWebViewConsumerTest")
        isFailOnNoMatchingTests = true
    }
    // Always execute both methods; an old XML/test task result is not evidence.
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
            val id = artifact.id.componentIdentifier as ModuleComponentIdentifier
            val binding = bindCandidateArtifact(id, artifact.file)
            val expectedName = binding.getValue("resolved_file_name") as String
            val staged = candidateRepository.resolve(binding.getValue("staged_file") as String)
            check(staged.isFile && artifactSha256(staged) == artifactSha256(artifact.file))
            val suffix = root.removePrefix("nativecmpkit-")
            systemProperty("nativecmpkit.expected.$suffix.name", expectedName)
            systemProperty("nativecmpkit.expected.$suffix.sha256", artifactSha256(staged))
        }
        println("NATIVECMPKIT_WEBVIEW_CONSUMER_TEST task=$path gradle=${gradle.gradleVersion} java=${JavaVersion.current().majorVersion} mode=${providers.gradleProperty("nativecmpkitMetadataMode").get()}")
    }
    testLogging { events("passed", "skipped", "failed") }
}
