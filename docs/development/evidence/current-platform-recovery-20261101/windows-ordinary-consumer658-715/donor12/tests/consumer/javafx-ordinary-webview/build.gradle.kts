// SPDX-License-Identifier: Apache-2.0
// One NEW public Stop test under ordinary private Maven activation, not old cohorts.
import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import java.io.File
import java.lang.management.ManagementFactory
import java.security.MessageDigest
import java.util.jar.JarFile
import org.gradle.api.artifacts.component.ModuleComponentIdentifier
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.4.20"
    id("org.jetbrains.compose") version "1.12.0"
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.20"
}

val libraryGroup = "io.github.apdelrahman1911.nativecmpkit"
val privateGroup = "nativecmpkit.private.javafx"
val privateVersion = "21.0.13-nativecmpkit-cancel1-local"
val javafxVersion = "21.0.13"
val companions = setOf("base", "graphics", "controls", "media", "swing")
val classpaths = listOf("compileClasspath", "runtimeClasspath", "testCompileClasspath", "testRuntimeClasspath")
val officialOriginalPinsSha256 = "246eb9bef73b24f2df53058f65344ff5ca81ba2b199d958f43997035c0cdf760"
val officialCompanionSupplementSha256 = "a2cce99c5ad3a3628c9a042b454bc1e8b3f61eb308b392d78c5534687682e9d2"
val mode = providers.gradleProperty("nativecmpkitMetadataMode").get()
require(mode in setOf("module", "pom"))
val libraryVersion = providers.gradleProperty("nativecmpkitVersion").get()
require(Regex("""[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?""").matches(libraryVersion)
    && !libraryVersion.endsWith("-SNAPSHOT"))
val libraryRepository = File(providers.gradleProperty("nativecmpkitRepository").get())
val privateRepository = File(providers.gradleProperty("nativecmpkitPrivateJavafxRepository").get())
require(libraryRepository.isAbsolute && libraryRepository.isDirectory && privateRepository.isAbsolute && privateRepository.isDirectory)
val classifier = providers.gradleProperty("nativecmpkitJavafxClassifier").get()
val actualOs = System.getProperty("os.name").lowercase()
val actualArch = System.getProperty("os.arch").lowercase()
val x64 = actualArch in setOf("amd64", "x86_64")
val arm64 = actualArch in setOf("aarch64", "arm64")
val actualClassifier = when {
    actualOs.contains("linux") && x64 -> "linux"
    actualOs.contains("linux") && arm64 -> "linux-aarch64"
    actualOs.contains("mac") && x64 -> "mac"
    actualOs.contains("mac") && arm64 -> "mac-aarch64"
    actualOs.contains("windows") && x64 -> "win"
    else -> error("Unsupported ordinary consumer host/CPU; no classifier fallback")
}
require(classifier == actualClassifier) { "Explicit classifier must equal the actual consuming host" }
require(gradle.startParameter.allInitScripts.isEmpty()) { "No explicit or automatically discovered init-script activation in an ordinary consumer" }
require(gradle.includedBuilds.isEmpty()) { "No composite/project substitution" }
val privateModule = "javafx-web-$classifier"
val privateStem = "$privateModule-$privateVersion"
val privateWeb = privateRepository.resolve("${privateGroup.replace('.', '/')}/$privateModule/$privateVersion/$privateStem.jar")
val privateStageReport = privateRepository.resolve("private-javafx-staging.json")
require(privateWeb.isFile && privateStageReport.isFile)
val stageReport = JsonSlurper().parse(privateStageReport) as Map<*, *>
require(stageReport["passed"] == true && stageReport["production_contract"] == true &&
    stageReport["publication_ready"] == false && stageReport["classifier"] == classifier &&
    stageReport["full_native_corresponding_source_complete"] == false)

kotlin {
    jvmToolchain(17)
    compilerOptions.jvmTarget.set(JvmTarget.JVM_17)
}
dependencies {
    implementation("$libraryGroup:nativecmpkit-webview${if (mode == "pom") "-desktop" else ""}:$libraryVersion")
    implementation(compose.desktop.currentOs)
    implementation("org.jetbrains.compose.material3:material3:1.12.0-alpha03")
    companions.forEach { implementation("org.openjfx:javafx-$it:$javafxVersion:$classifier") }
    implementation("$privateGroup:$privateModule:$privateVersion")
    testImplementation(kotlin("test-junit"))
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.11.0")
}

fun sha256(file: File): String {
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

data class OfficialCompanionPin(val file: String, val bytes: Long, val sha256: String)

fun trustedCompanionPins(): Map<String, OfficialCompanionPin> {
    // Owning checked-in literals, never stage/resolution JSON or a caller pin
    // property. Original candidate14 inputs remain unchanged.699 added only
    // independently acquired Swing5/generic5 metadata, not security clearance.
    val owner = projectDir.parentFile.parentFile.parentFile.resolve("tests/dependency/javafx-http2-cancellation")
    fun document(filename: String, expected: String): Map<*, *> {
        val file = owner.resolve(filename)
        check(file.isFile && file.length() in 1L..131072L) {
            "Trusted official companion pin document missing or changed"
        }
        val payload = file.readBytes()
        val sha = MessageDigest.getInstance("SHA-256").digest(payload).joinToString("") { "%02x".format(it) }
        check(payload.size in 1..131072 && sha == expected) {
            "Trusted official companion pin document missing or changed"
        }
        return JsonSlurper().parseText(payload.toString(Charsets.UTF_8)) as Map<*, *>
    }
    val original = document("artifacts.json", officialOriginalPinsSha256)
    val supplement = document("official-companion-supplement.json", officialCompanionSupplementSha256)
    val targets = setOf("linux", "linux-aarch64", "mac", "mac-aarch64", "win")
    val platforms = original["platforms"] as? Map<*, *>
    check(original["schema_version"] == 1 && original["version"] == javafxVersion && platforms?.keys == targets)
    val origin = "https://repo.maven.apache.org/maven2/org/openjfx/"
    check(supplement["schema_version"] == 1 && supplement["version"] == javafxVersion &&
        supplement["official_origin"] == origin && supplement["original_artifacts_sha256"] == officialOriginalPinsSha256 &&
        supplement["same_registry_checksum_is_independent_security_certification"] == false)
    val swings = supplement["classified_swing"] as? Map<*, *>
    val generic = supplement["generic"] as? Map<*, *>
    check(swings?.keys == targets && generic?.keys == companions) { "Trusted official companion pin missing" }
    val originals = platforms?.get(classifier) as? List<*>
    check(originals != null)
    fun pin(value: Any?, module: String, filename: String): OfficialCompanionPin {
        val row = value as? Map<*, *> ?: error("Trusted official companion pin missing")
        val bytes = row["bytes"] as? Number ?: error("Trusted official companion byte length missing")
        val sha = row["sha256"] as? String ?: error("Trusted official companion digest missing")
        check(row["file"] == filename && bytes.toLong() in 1L..67108864L &&
            bytes.toString() == bytes.toLong().toString() && Regex("[0-9a-f]{64}").matches(sha) &&
            row["url"] == "$origin$module/$javafxVersion/$filename") { "Trusted official companion pin malformed" }
        return OfficialCompanionPin(filename, bytes.toLong(), sha)
    }
    val result = linkedMapOf<String, OfficialCompanionPin>()
    companions.forEach { companion ->
        val module = "javafx-$companion"
        val classifiedFile = "$module-$javafxVersion-$classifier.jar"
        val matches = originals.filter { (it as? Map<*, *>)?.get("file") == classifiedFile }
        val row = if (companion == "swing") {
            check(matches.isEmpty()) { "Duplicate trusted companion pin" }
            swings?.get(classifier)
        } else {
            check(matches.size == 1) { "Trusted official companion pin missing" }
            matches.single()
        }
        result[classifiedFile] = pin(row, module, classifiedFile)
        val genericFile = "$module-$javafxVersion.jar"
        result[genericFile] = pin(generic?.get(companion), module, genericFile)
    }
    return result
}

fun bindLibrary(resolved: File): String {
    val module = "nativecmpkit-webview-desktop"
    val canonical = "$module-$libraryVersion.jar"
    val retained = "calf-webview-desktop-$libraryVersion.jar"
    check(resolved.name in setOf(canonical, retained))
    val directory = "${libraryGroup.replace('.', '/')}/$module/$libraryVersion/"
    val staged = libraryRepository.resolve(directory + canonical)
    check(staged.isFile && staged.length() == resolved.length() && sha256(staged) == sha256(resolved))
    val metadata = JsonSlurper().parse(libraryRepository.resolve(directory + "$module-$libraryVersion.module")) as Map<*, *>
    val component = metadata["component"] as Map<*, *>
    check(metadata["formatVersion"] == "1.1" && component["group"] == libraryGroup &&
        component["module"] == "nativecmpkit-webview" && component["version"] == libraryVersion &&
        component["url"] == "../../nativecmpkit-webview/$libraryVersion/nativecmpkit-webview-$libraryVersion.module")
    val bindings = (metadata["variants"] as List<*>).mapNotNull { entry ->
        val variant = entry as Map<*, *>
        val attributes = variant["attributes"] as Map<*, *>
        if (attributes["org.gradle.category"] != "library") return@mapNotNull null
        val files = variant["files"] as? List<*> ?: return@mapNotNull null
        check(files.size == 1)
        val file = files.single() as Map<*, *>
        check(file["name"] in setOf(canonical, retained) && file["url"] == canonical &&
            file["size"] is Number && (file["size"] as Number).toLong() == resolved.length() && file["sha256"] == sha256(resolved))
        check(resolved.name == if (mode == "module") file["name"] else canonical)
        file["sha256"] as String
    }.distinct()
    check(bindings.size == 1)
    return bindings.single()
}

fun publicWebProviders(file: File): Boolean = file.extension == "jar" && JarFile(file).use { jar ->
    jar.entries().asSequence().any { entry ->
        entry.name == "javafx/scene/web/WebEngine.class" || entry.name.endsWith("/javafx/scene/web/WebEngine.class") ||
            entry.name.substringAfterLast('/').lowercase() in setOf("libjfxwebkit.so", "libjfxwebkit.dylib", "jfxwebkit.dll")
    }
}

fun observedResolution(): List<Map<String, Any>> {
    val officialPins = trustedCompanionPins()
    val result = mutableListOf<Map<String, Any>>()
    classpaths.forEach { name ->
        var cured = 0
        var libraries = 0
        var providers = 0
        val classifiedCompanions = mutableSetOf<String>()
        val identities = mutableSetOf<String>()
        configurations.getByName(name).incoming.artifacts.artifacts.forEach { artifact ->
            val id = artifact.id.componentIdentifier
            check(id is ModuleComponentIdentifier) { "Project/loose artifact substitution in $name" }
            val file = artifact.file
            check(file.isFile && identities.add("${id.group}:${id.module}:${id.version}:${file.name}"))
            val hash = sha256(file)
            val web = publicWebProviders(file)
            if (web) providers++
            check(id.group != "com.mohamedrejeb.calf")
            when (id.group) {
                libraryGroup -> {
                    check(id.module == "nativecmpkit-webview-desktop" && id.version == libraryVersion && !web)
                    check(bindLibrary(file) == hash)
                    libraries++
                }
                privateGroup -> {
                    check(id.module == privateModule && id.version == privateVersion && file.name == "$privateStem.jar" && web)
                    check(file.length() == privateWeb.length() && hash == sha256(privateWeb))
                    cured++
                }
                "org.openjfx" -> {
                    check(id.module.removePrefix("javafx-") in companions && id.version == javafxVersion && !web)
                    check(file.name in setOf("${id.module}-$javafxVersion.jar", "${id.module}-$javafxVersion-$classifier.jar"))
                    val pin = officialPins[file.name] ?: error("Trusted official companion pin missing")
                    check(file.length() == pin.bytes && hash == pin.sha256) { "Trusted official companion byte pin differs" }
                    if (file.name == "${id.module}-$javafxVersion-$classifier.jar") classifiedCompanions += id.module.removePrefix("javafx-")
                }
            }
            result += mapOf("configuration" to name, "component_kind" to "module", "group" to id.group,
                "module" to id.module, "version" to id.version, "file" to file.name, "path" to file.absolutePath,
                "bytes" to file.length(), "sha256" to hash)
        }
        check(cured == 1 && libraries == 1 && providers == 1 && classifiedCompanions == companions)
    }
    result.forEach { row ->
        val file = File(row.getValue("path") as String)
        check(file.length() == row.getValue("bytes") && sha256(file) == row.getValue("sha256")) {
            "Actual admitted artifact changed during resolution observation"
        }
    }
    check(trustedCompanionPins() == officialPins) { "Trusted official companion pin inputs changed" }
    return result.sortedBy { "${it["configuration"]}:${it["group"]}:${it["module"]}:${it["file"]}" }
}

val observePrivateWebResolution = tasks.register("observePrivateWebResolution") {
    group = "verification"
    outputs.upToDateWhen { false }
    doLast {
        check(gradle.gradleVersion == "9.7.1" && JavaVersion.current().majorVersion == "17")
        check(ManagementFactory.getRuntimeMXBean().inputArguments.none { it.startsWith("--patch-module") })
        check(System.getProperty("com.sun.webkit.useHTTP2Loader") == null)
        val report = mapOf("schema_version" to 1, "classifier" to classifier, "metadata_mode" to mode, "java_major" to 17,
            "project_substitution" to false, "runtime_init_scripts" to false, "private_route_override" to false,
            "runtime_module_patch" to false, "resolved_artifacts" to observedResolution())
        val file = layout.buildDirectory.file("reports/private-javafx-ordinary-resolution-$mode.json").get().asFile
        file.parentFile.mkdirs()
        file.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(report)) + "\n")
        println("NATIVECMPKIT_PRIVATE_JAVAFX_RESOLUTION mode=$mode classpaths=4 classifier=$classifier publication=false")
    }
}

// Default test is disabled; an admitted request selects only the genuinely NEW method.
tasks.named<Test>("test") { enabled = false }
tasks.register<Test>("ordinaryCuredWebStop") {
    group = "verification"
    testClassesDirs = sourceSets["test"].output.classesDirs
    classpath = sourceSets["test"].runtimeClasspath
    dependsOn(observePrivateWebResolution)
    maxParallelForks = 1
    maxHeapSize = "512m"
    jvmArgs("-Xcheck:jni")
    filter {
        includeTestsMatching("nativecmpkit.consumer.OrdinaryCuredWebStopConsumerTest.normalMavenActivationBindsCuredPublicStopTransportAndOwnedLifetime")
        isFailOnNoMatchingTests = true
    }
    outputs.upToDateWhen { false }
    val home = layout.buildDirectory.dir("owned-test-home")
    val tmp = layout.buildDirectory.dir("owned-test-tmp")
    val nativePath = layout.buildDirectory.dir("empty-native-path")
    systemProperty("user.home", home.get().asFile.absolutePath)
    systemProperty("java.io.tmpdir", tmp.get().asFile.absolutePath)
    systemProperty("java.library.path", nativePath.get().asFile.absolutePath)
    doFirst {
        check(gradle.gradleVersion == "9.7.1" && JavaVersion.current().majorVersion == "17")
        listOf(home, tmp, nativePath).forEach { it.get().asFile.mkdirs() }
        check(nativePath.get().asFile.listFiles()?.isEmpty() == true)
        val rows = observedResolution().filter { it["configuration"] == "testRuntimeClasspath" }
        val library = rows.single { it["group"] == libraryGroup }
        val web = rows.single { it["group"] == privateGroup }
        val officialPins = trustedCompanionPins()
        companions.forEach { companion ->
            val filename = "javafx-$companion-$javafxVersion-$classifier.jar"
            val pin = officialPins[filename] ?: error("Trusted official companion pin missing")
            val artifact = rows.single { it["group"] == "org.openjfx" && it["module"] == "javafx-$companion" && it["file"] == filename }
            check(artifact["bytes"] == pin.bytes && artifact["sha256"] == pin.sha256)
            // Expectations use fixed official pins; only the admitted actual
            // path comes from the genuine testRuntimeClasspath graph.
            systemProperty("nativecmpkit.expected.javafx.$companion.name", pin.file)
            systemProperty("nativecmpkit.expected.javafx.$companion.bytes", pin.bytes.toString())
            systemProperty("nativecmpkit.expected.javafx.$companion.sha256", pin.sha256)
            systemProperty("nativecmpkit.expected.javafx.$companion.path", artifact.getValue("path"))
        }
        systemProperty("nativecmpkit.expected.webview.name", library.getValue("file"))
        systemProperty("nativecmpkit.expected.webview.sha256", library.getValue("sha256"))
        systemProperty("nativecmpkit.expected.javafx.name", web.getValue("file"))
        systemProperty("nativecmpkit.expected.javafx.sha256", web.getValue("sha256"))
        systemProperty("nativecmpkit.expected.javafx.loader.sha256", "9e8663af362be84a12111e785b06f2cadf3c1f02e6cd19a9782a2e9f7e4675c2")
        systemProperty("nativecmpkit.ordinary.javafx.classifier", classifier)
        println("NATIVECMPKIT_ORDINARY_CURED_STOP task=$path gradle=${gradle.gradleVersion} java=17 mode=$mode classifier=$classifier methods=1")
    }
    testLogging { events("passed", "skipped", "failed") }
}
