// PRIVATE actual-KGP U1/U2/U3/U4 fixture; not ordinary frozen-install adoption.
import groovy.json.JsonOutput
import io.github.apdelrahman1911.nativecmpkit.buildlogic.OrdinaryYarnUpgradeTaskGate
import io.github.apdelrahman1911.nativecmpkit.buildlogic.RefuseOrdinaryYarnUpgradeTask
import java.nio.file.Files
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import org.gradle.BuildResult
import org.gradle.api.Action
import org.gradle.api.Task
import org.gradle.api.execution.TaskExecutionGraph
import org.jetbrains.kotlin.gradle.targets.js.nodejs.NodeJsEnvSpec
import org.jetbrains.kotlin.gradle.targets.js.nodejs.NodeJsPlugin
import org.jetbrains.kotlin.gradle.targets.js.npm.tasks.KotlinNpmInstallTask
import org.jetbrains.kotlin.gradle.targets.js.yarn.YarnLockMismatchReport
import org.jetbrains.kotlin.gradle.targets.js.yarn.YarnLockUpgradeTask
import org.jetbrains.kotlin.gradle.targets.js.yarn.YarnPlugin
import org.jetbrains.kotlin.gradle.targets.js.yarn.YarnRootEnvSpec
import org.jetbrains.kotlin.gradle.targets.wasm.nodejs.WasmNodeJsEnvSpec
import org.jetbrains.kotlin.gradle.targets.wasm.nodejs.WasmNodeJsPlugin
import org.jetbrains.kotlin.gradle.targets.wasm.yarn.WasmYarnPlugin
import org.jetbrains.kotlin.gradle.targets.wasm.yarn.WasmYarnRootEnvSpec
import org.jetbrains.kotlin.gradle.targets.web.yarn.BaseYarnRootEnvSpec

plugins {
    alias(libs.plugins.kotlinMultiplatform).apply(false)
    id("module.publication").apply(false)
}

fun BaseYarnRootEnvSpec.freezeNativeCmpkitDependencies() {
    version.set("1.22.22")
    ignoreScripts.set(true)
    yarnLockMismatchReport.set(YarnLockMismatchReport.FAIL)
    yarnLockAutoReplace.set(false)
    reportNewYarnLock.set(true)
}
allprojects {
    plugins.withType<NodeJsPlugin> {
        extensions.configure<NodeJsEnvSpec> { version.set("24.16.0") }
    }
    plugins.withType<WasmNodeJsPlugin> {
        extensions.configure<WasmNodeJsEnvSpec> { version.set("24.16.0") }
    }
}
plugins.withType<YarnPlugin> {
    extensions.configure<YarnRootEnvSpec> { freezeNativeCmpkitDependencies() }
}
plugins.withType<WasmYarnPlugin> {
    extensions.configure<WasmYarnRootEnvSpec> { freezeNativeCmpkitDependencies() }
}

// Exactly the independent reviewed helper, registered before the child's late KGP targets.
val prototypeOptIn = providers.gradleProperty("nativecmpkit.yarnUpgradeTaskPrototype").orElse("false").get()
require(prototypeOptIn in setOf("true", "false")) { "NCYB-invalid-prototype-opt-in" }
require(prototypeOptIn == "true") { "NCYB-explicit-upgrade-prototype-required" }
OrdinaryYarnUpgradeTaskGate.install(rootProject)

fun requiredFixtureProperty(name: String): String = providers.gradleProperty(name).orNull
    ?: error("NCYB-required-fixture-property-missing")
val caseId = requiredFixtureProperty("nativecmpkit.upgradeFixtureCase")
val runId = requiredFixtureProperty("nativecmpkit.fixtureRunId")
val inputSha256 = requiredFixtureProperty("nativecmpkit.fixtureInputSha256")
require(caseId in setOf("U1", "U2", "U3", "U4")) { "NCYB-invalid-fixture-case" }
require(Regex("U[1-4]-[0-9a-f]{16}").matches(runId) && runId.startsWith("$caseId-")) { "NCYB-invalid-run-id" }
require(Regex("[0-9a-f]{64}").matches(inputSha256)) { "NCYB-invalid-input-digest" }
require(requiredFixtureProperty("nativecmpkit.fixtureCase") == "standard") { "NCYB-only-standard-upgrade-fixture" }
require(gradle.gradleVersion == "9.7.1" && JavaVersion.current() == JavaVersion.VERSION_17) { "NCYB-runtime-mismatch" }
require(libs.versions.kotlin.get() == "2.4.20") { "NCYB-configured-kgp-version-mismatch" }
val expectedRequests = when (caseId) {
    "U1" -> listOf("kotlinUpgradeYarnLock", "nativeCmpkitActionSentinel")
    "U2" -> listOf("nativeCmpkitIndirectWasmUpgrade", "nativeCmpkitActionSentinel")
    "U3" -> listOf("nativeCmpkitIndirectJsUpgrade", "nativeCmpkitIndirectWasmUpgrade", "nativeCmpkitActionSentinel")
    else -> listOf("nativeCmpkitActionSentinel")
}
require(gradle.startParameter.taskNames == expectedRequests) { "NCYB-exact-case-task-selection-required" }

fun digest(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes)
    .joinToString("") { "%02x".format(it.toInt() and 255) }
val helperSource = rootDir.parentFile.resolve("convention-plugins/src/main/kotlin/io/github/apdelrahman1911/nativecmpkit/buildlogic/OrdinaryYarnUpgradeTaskGate.kt")
val helperSha256 = digest(helperSource.readBytes())
require(helperSha256 == "6473a953ad6c95e0eb00f0e79e2275aac0731976db06356b73bcfa6abfac0f14") { "NCYB-reviewed-helper-source-changed" }
val resultDirectory = layout.buildDirectory.dir("upgrade-fixture/$runId").get().asFile.toPath()
require(!Files.exists(resultDirectory)) { "NCYB-run-directory-already-exists" }
Files.createDirectories(resultDirectory)
fun writeFresh(name: String, data: Map<String, Any?>): String {
    val bytes = (JsonOutput.prettyPrint(JsonOutput.toJson(data)) + "\n").toByteArray(Charsets.UTF_8)
    require(bytes.size <= 256 * 1024) { "NCYB-receipt-size-cap" }
    Files.write(resultDirectory.resolve(name), bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
    return digest(bytes)
}
fun identityFields(): Map<String, Any?> = mapOf(
    "schema" to 1, "case_id" to caseId, "run_id" to runId, "input_sha256" to inputSha256,
    "helper_sha256" to helperSha256, "gradle_version" to gradle.gradleVersion, "java_major" to 17,
    "configured_kgp_version" to libs.versions.kotlin.get()
)

val sentinel = tasks.register("nativeCmpkitActionSentinel") {
    doLast {
        writeFresh("sentinel.json", identityFields() + mapOf("record_type" to "sentinel-action", "ran" to true))
        logger.lifecycle("NCYB-FIXTURE-SENTINEL-RAN")
    }
}
val indirectJs = tasks.register("nativeCmpkitIndirectJsUpgrade")
val indirectWasm = tasks.register("nativeCmpkitIndirectWasmUpgrade")
val observedActions = mutableListOf<String>()
var rootGraphTasks: List<Task> = emptyList()
var graphSha256: String? = null
var bindingData: Map<String, Boolean> = emptyMap()

// Public TaskState failures are narrowed to the exact constant; no exception bodies are serialized.
fun hasExactDenial(failure: Throwable?): Boolean {
    var current = failure
    val seen = mutableSetOf<Throwable>()
    repeat(16) {
        val value = current ?: return false
        if (!seen.add(value)) return false
        if (value.message == "NCYUG-actual-upgrade-forbidden-before-root-task-actions") return true
        current = value.cause
    }
    return false
}
fun kind(task: Task): String = when (task) {
    is RefuseOrdinaryYarnUpgradeTask -> "denial"
    is YarnLockUpgradeTask -> "upgrade"
    is KotlinNpmInstallTask -> "primary"
    else -> "other"
}

gradle.projectsEvaluated {
    // Bind actual KGP registrations. No synthetic YarnLockUpgradeTask is registered by this fixture.
    val jsUpgradeProvider = tasks.named("kotlinUpgradeYarnLock", YarnLockUpgradeTask::class.java)
    val wasmUpgradeProvider = tasks.named("kotlinWasmUpgradeYarnLock", YarnLockUpgradeTask::class.java)
    val jsPrimaryProvider = tasks.named("kotlinNpmInstall", KotlinNpmInstallTask::class.java)
    val wasmPrimaryProvider = tasks.named("kotlinWasmNpmInstall", KotlinNpmInstallTask::class.java)
    val gateProvider = tasks.named("nativeCmpkitRefuseOrdinaryYarnUpgrade", RefuseOrdinaryYarnUpgradeTask::class.java)
    val jsUpgrade = jsUpgradeProvider.get()
    val wasmUpgrade = wasmUpgradeProvider.get()
    val jsPrimary = jsPrimaryProvider.get()
    val wasmPrimary = wasmPrimaryProvider.get()
    val gate = gateProvider.get()
    indirectJs.configure { dependsOn(jsUpgradeProvider) }
    indirectWasm.configure { dependsOn(wasmUpgradeProvider) }
    bindingData = mapOf(
        "js_upgrade_typed_provider_identity" to (jsUpgrade === tasks.named("kotlinUpgradeYarnLock").get()),
        "wasm_upgrade_typed_provider_identity" to (wasmUpgrade === tasks.named("kotlinWasmUpgradeYarnLock").get()),
        "js_primary_typed_provider_identity" to (jsPrimary === tasks.named("kotlinNpmInstall").get()),
        "wasm_primary_typed_provider_identity" to (wasmPrimary === tasks.named("kotlinWasmNpmInstall").get()),
        "gate_typed_provider_identity" to (gate === tasks.named("nativeCmpkitRefuseOrdinaryYarnUpgrade").get()),
        "js_upgrade_depends_on_primary" to jsUpgrade.taskDependencies.getDependencies(jsUpgrade).contains(jsPrimary),
        "wasm_upgrade_depends_on_primary" to wasmUpgrade.taskDependencies.getDependencies(wasmUpgrade).contains(wasmPrimary),
        "js_upgrade_depends_on_gate" to jsUpgrade.taskDependencies.getDependencies(jsUpgrade).contains(gate),
        "wasm_upgrade_depends_on_gate" to wasmUpgrade.taskDependencies.getDependencies(wasmUpgrade).contains(gate),
        "indirect_js_depends_on_actual_upgrade" to indirectJs.get().taskDependencies.getDependencies(indirectJs.get()).contains(jsUpgrade),
        "indirect_wasm_depends_on_actual_upgrade" to indirectWasm.get().taskDependencies.getDependencies(indirectWasm.get()).contains(wasmUpgrade),
        "gate_dependency_free" to gate.taskDependencies.getDependencies(gate).isEmpty()
    )
    gradle.taskGraph.whenReady(object : Action<TaskExecutionGraph> {
        override fun execute(graph: TaskExecutionGraph) {
            rootGraphTasks = graph.allTasks.filter { it.project.rootProject === rootProject }
            require(rootGraphTasks.size <= 128) { "NCYB-root-graph-cap" }
            require(rootGraphTasks.all { Regex(":[A-Za-z0-9_:-]+").matches(it.path) }) { "NCYB-unexpected-public-task-path" }
            val upgrades = rootProject.allprojects.flatMap { it.tasks.withType(YarnLockUpgradeTask::class.java).toList() }
            val allOrdered = rootGraphTasks.filter { it !== gate }.all { it.mustRunAfter.getDependencies(it).contains(gate) }
            graphSha256 = writeFresh("graph.json", identityFields() + mapOf(
                "record_type" to "actual-kgp-upgrade-graph", "requested_tasks" to expectedRequests,
                "bindings" to bindingData,
                "registered_upgrade_paths" to upgrades.map { it.path }.sorted(),
                "root_tasks" to rootGraphTasks.map { mapOf("path" to it.path, "kind" to kind(it)) },
                "all_root_non_gate_tasks_ordered_after_gate" to allOrdered,
                "gate_selected_by_actual_object" to graph.hasTask(gate),
                "included_build_actions_in_scope" to false
            ))
            // Fixture-only tripwire, not a substitute for the helper: record and stop any unexpected
            // action before its body. An unrelated tripwire error can never pass U1/U2/U3.
            rootGraphTasks.forEach { task ->
                task.doFirst(object : Action<Task> {
                    override fun execute(target: Task) {
                        require(observedActions.size < 128) { "NCYB-action-cap" }
                        observedActions.add(target.path)
                        val allowed = target === (if (caseId == "U4") sentinel.get() else gate)
                        writeFresh("action-%04d.json".format(observedActions.size), identityFields() + mapOf(
                            "record_type" to "root-task-action", "sequence" to observedActions.size,
                            "path" to target.path, "allowed_by_fixture_tripwire" to allowed
                        ))
                        target.logger.lifecycle("NCYB-FIXTURE-ACTION path={}", target.path)
                        if (!allowed) throw org.gradle.api.GradleException("NCYB-unexpected-root-task-action")
                    }
                })
            }
        }
    })
}

// Called only on normal Gradle completion; timeout/crash leaves no acceptable result receipt.
gradle.buildFinished(object : Action<BuildResult> {
    override fun execute(result: BuildResult) {
        writeFresh("result.json", identityFields() + mapOf(
            "record_type" to "actual-kgp-upgrade-result", "graph_sha256" to graphSha256,
            "build_failed" to (result.failure != null), "observed_actions" to observedActions.toList(),
            "root_task_states" to rootGraphTasks.map { task ->
                mapOf("path" to task.path, "kind" to kind(task), "executed" to task.state.executed,
                    "failed" to (task.state.failure != null), "skipped" to task.state.skipped,
                    "up_to_date" to task.state.upToDate, "no_source" to task.state.noSource,
                    "exact_denial_in_failure_chain" to hasExactDenial(task.state.failure))
            }, "included_build_actions_in_scope" to false
        ))
    }
})
