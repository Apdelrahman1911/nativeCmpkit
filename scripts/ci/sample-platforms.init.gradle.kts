// NativeCmpKit SAMPLE graph evidence only. No publishing, signing or library-test replacement.
import org.gradle.api.NamedDomainObjectCollection
import org.gradle.api.artifacts.component.ModuleComponentIdentifier
import org.gradle.api.artifacts.result.UnresolvedDependencyResult

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
