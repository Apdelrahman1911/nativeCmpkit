// NativeCmpKit SAMPLE graph evidence only. No publishing, signing or library-test replacement.
import org.gradle.api.NamedDomainObjectCollection
import org.gradle.api.artifacts.component.ModuleComponentIdentifier
import org.gradle.api.artifacts.result.UnresolvedDependencyResult
import org.gradle.api.execution.TaskExecutionListener
import org.gradle.api.provider.Provider
import org.gradle.api.tasks.TaskState
import java.nio.file.Files
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import java.util.concurrent.TimeUnit

val sampleRootFile = java.io.File(checkNotNull(System.getProperty("nativecmpkit.sampleProducerRoot")) {
    "Sample verification requires an explicit producer-root binding"
})
check(sampleRootFile.isAbsolute && sampleRootFile.isDirectory)
val sampleRoot = sampleRootFile.canonicalFile

fun sampleJson(value: Any?): String = when (value) {
    null -> "null"
    is Boolean, is Number -> value.toString()
    is String -> "\"" + value.flatMap { character ->
        when (character) {
            '"' -> "\\\"".toList()
            '\\' -> "\\\\".toList()
            '\n' -> "\\n".toList()
            '\r' -> "\\r".toList()
            '\t' -> "\\t".toList()
            else -> { check(character.code >= 32); listOf(character) }
        }
    }.joinToString("") + "\""
    is Map<*, *> -> value.entries.joinToString(",", "{", "}") { sampleJson(it.key) + ":" + sampleJson(it.value) }
    is Iterable<*> -> value.joinToString(",", "[", "]") { sampleJson(it) }
    else -> error("Unreviewed sample dependency receipt field")
}

gradle.projectsEvaluated {
    if (rootProject.projectDir.canonicalFile != sampleRoot) return@projectsEvaluated
    check(rootProject.name == "NativeCmpKit")
    val mode = rootProject.providers.gradleProperty("nativecmpkitSampleMode").get()
    val names = when (mode) {
        "linux" -> setOf("android", "desktop", "js", "wasmJs")
        "apple" -> setOf("iosArm64", "iosSimulatorArm64")
        else -> error("Unknown fixed sample target mode")
    }
    val buildTasks = when (mode) {
        "linux" -> listOf(":sample:android:assembleDebug", ":sample:desktop:jvmJar",
            ":sample:web-js:jsBrowserProductionWebpack", ":sample:web-js:jsBrowserDistribution",
            ":sample:web-wasm:wasmJsBrowserProductionWebpack", ":sample:web-wasm:wasmJsBrowserDistribution")
        else -> listOf(":sample:common:linkDebugFrameworkIosArm64", ":sample:common:linkDebugFrameworkIosSimulatorArm64")
    }
    fun freshReceipt(name: String, fields: Map<String, Any?>) {
        val destination = rootProject.layout.buildDirectory.file("ci-verification/sample-platforms-$mode/$name").get().asFile
        destination.parentFile.mkdirs()
        Files.writeString(destination.toPath(), sampleJson(fields) + "\n", StandardOpenOption.CREATE_NEW)
    }
    // Public Gradle task outcomes survive an unrelated later target failure.
    // Cached/up-to-date compilations may be reused; they are NEVER test passes.
    @Suppress("DEPRECATION")
    gradle.taskGraph.addTaskExecutionListener(object : TaskExecutionListener {
        override fun beforeExecute(task: org.gradle.api.Task) = Unit
        override fun afterExecute(task: org.gradle.api.Task, state: TaskState) {
            if (task.project.rootProject.projectDir.canonicalFile != sampleRoot) return
            val index = buildTasks.indexOf(task.path)
            if (index < 0) return
            freshReceipt("task-build-$index.json", mapOf("schema_version" to 1, "task" to task.path,
                "executed" to state.executed, "failed" to (state.failure != null), "skipped" to state.skipped,
                "skip_message" to state.skipMessage, "up_to_date" to state.upToDate, "no_source" to state.noSource,
                "observed_epoch_ms" to System.currentTimeMillis(), "test_success_inferred" to false))
        }
    })
    if (mode == "linux") {
        val web = listOf(Triple(":sample:web-js:jsBrowserProductionWebpack", "js", "org.jetbrains.kotlin.gradle.targets.js.nodejs.NodeJsEnvSpec"),
            Triple(":sample:web-wasm:wasmJsBrowserProductionWebpack", "wasm", "org.jetbrains.kotlin.gradle.targets.wasm.nodejs.WasmNodeJsEnvSpec"))
        for ((taskPath, target, specClassName) in web) {
            rootProject.project(taskPath.substringBeforeLast(':')).tasks.named(taskPath.substringAfterLast(':')).configure {
                doFirst {
                    val task = this
                    // The inspected public KGP class/Companion/getter APIs;
                    // never inspect private webpack fields or substitute PATH node.
                    val specClass = task.javaClass.classLoader.loadClass(specClassName)
                    val companion = specClass.getField("Companion").get(null)
                    val extensionName = companion.javaClass.getMethod("getEXTENSION_NAME").invoke(companion) as String
                    val rows = listOf(rootProject, task.project).map { project ->
                        val spec = project.extensions.getByName(extensionName)
                        @Suppress("UNCHECKED_CAST")
                        val configuredVersion = (spec.javaClass.getMethod("getVersion").invoke(spec) as Provider<String>).get()
                        @Suppress("UNCHECKED_CAST")
                        val executable = (spec.javaClass.getMethod("getExecutable").invoke(spec) as Provider<String>).get()
                        val binary = java.io.File(executable)
                        check(binary.isAbsolute && binary.isFile && binary.canExecute()) { "Selected project Node executable is unavailable" }
                        val process = ProcessBuilder(executable, "--version").redirectErrorStream(true).start()
                        if (!process.waitFor(30, TimeUnit.SECONDS)) {
                            process.destroyForcibly()
                            check(process.waitFor(10, TimeUnit.SECONDS)) { "Owned Node version probe did not terminate" }
                            error("Selected project Node version probe timed out")
                        }
                        val body = process.inputStream.use { it.readNBytes(256) }
                        check(body.size < 256) { "Unexpectedly large Node version output" }
                        val observedVersion = body.toString(Charsets.UTF_8).trim()
                        val digest = MessageDigest.getInstance("SHA-256")
                        binary.inputStream().use { stream ->
                            val buffer = ByteArray(8192)
                            while (true) {
                                val size = stream.read(buffer)
                                if (size < 0) break
                                digest.update(buffer, 0, size)
                            }
                        }
                        mapOf("project" to project.path, "extension" to extensionName,
                            "configured_version" to configuredVersion, "executable" to executable,
                            "executable_sha256" to digest.digest().joinToString("") { "%02x".format(it) },
                            "version_exit_code" to process.exitValue(), "observed_version" to observedVersion,
                            "passed" to (configuredVersion == "24.16.0" && process.exitValue() == 0 && observedVersion == "v24.16.0"))
                    }
                    freshReceipt("node-webpack-$target.json", mapOf("schema_version" to 1, "task" to task.path,
                        "observed_epoch_ms" to System.currentTimeMillis(), "environments" to rows,
                        "test_success_inferred" to false))
                    check(rows.all { it["passed"] == true } && rows.map { it["executable"] }.distinct().size == 1) {
                        "Root setup and actual webpack project must use the same pinned Node executable/version"
                    }
                }
            }
        }
    }
    val sample = rootProject.project(":sample:common")
    val kotlin = sample.extensions.getByName("kotlin")
    @Suppress("UNCHECKED_CAST")
    val targets = kotlin.javaClass.getMethod("getTargets").invoke(kotlin) as NamedDomainObjectCollection<Any>
    val selected = targets.filter { target -> target.javaClass.getMethod("getName").invoke(target) in names }
    check(selected.size == names.size) { "Every actual selected sample target must exist" }
    rootProject.tasks.register("nativecmpkitSampleCompileDependencies") {
        group = "verification"
        description = "Record actual selected SAMPLE main compilation dependency graphs without publishing"
        doLast {
            val rows = selected.map { target ->
                val targetName = target.javaClass.getMethod("getName").invoke(target) as String
                @Suppress("UNCHECKED_CAST")
                val compilations = target.javaClass.getMethod("getCompilations").invoke(target) as NamedDomainObjectCollection<Any>
                val main = compilations.getByName("main")
                val configurationName = main.javaClass.getMethod("getCompileDependencyConfigurationName").invoke(main) as String
                val compileTask = main.javaClass.getMethod("getCompileKotlinTaskName").invoke(main) as String
                val configuration = sample.configurations.getByName(configurationName)
                val result = configuration.incoming.resolutionResult
                val unresolved = result.allDependencies.count { it is UnresolvedDependencyResult }
                val modules = result.allComponents.mapNotNull { component ->
                    (component.id as? ModuleComponentIdentifier)?.let { id ->
                        mapOf("group" to id.group, "name" to id.module, "version" to id.version)
                    }
                }.sortedBy { it.getValue("group") + ":" + it.getValue("name") }
                val direct = configuration.allDependencies.map { dependency ->
                    mapOf("group" to dependency.group, "name" to dependency.name, "version" to dependency.version)
                }.sortedBy { it["group"].orEmpty() + ":" + it.getValue("name").orEmpty() }
                mapOf("target" to targetName, "compilation" to "main", "configuration" to configurationName,
                      "compile_task" to sample.path + ":" + compileTask, "direct_dependencies" to direct,
                      "resolved_modules" to modules, "unresolved_dependencies" to unresolved)
            }.sortedBy { it.getValue("target") as String }
            val output = rootProject.layout.buildDirectory.file("ci-verification/sample-platforms-$mode/compile-dependencies.json").get().asFile
            check(!output.exists()) { "Actual dependency receipts must be fresh, never overwritten" }
            output.parentFile.mkdirs()
            output.writeText(sampleJson(mapOf("schema_version" to 1, "mode" to mode, "project" to sample.path,
                "sample_minSdk_lowered" to false, "compilations" to rows)) + "\n")
            println("NATIVECMPKIT_SAMPLE_DEPENDENCIES mode=$mode targets=${rows.size}")
            check(rows.all { it["unresolved_dependencies"] == 0 }) { "Actual sample compilation dependencies unresolved" }
        }
    }
}
