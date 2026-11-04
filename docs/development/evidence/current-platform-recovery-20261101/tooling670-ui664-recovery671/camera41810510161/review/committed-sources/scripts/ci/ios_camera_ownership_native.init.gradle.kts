import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.FileCollection
import groovy.json.JsonOutput
import java.security.MessageDigest

// Exact three-source Camera KLIB/native-task admission, not a native result.
// Only the separate compiler task OR NEW5 application request; no accepted/common
// test compilation, implicit host, publication, unrelated task or generated XML.
gradle.projectsEvaluated {
    val project = rootProject.findProject(":calf-camera-picker") ?: return@projectsEvaluated
    val focus = rootProject.providers.gradleProperty("nativecmpkitCameraIosFocus").orNull
    check(focus == "ios-camera-ownership-memory-callback") { "Explicit exact Camera NEW5 focus is required" }
    val prefix = "com.mohamedrejeb.calf.camerapicker.IosCameraOwnershipAcceptanceTest."
    val methods = listOf(
        "publicOwnerSurvivesOrdinaryRecompositionAndNativeGcAndDeliversToLatestCallback",
        "doubleLaunchDuplicateTerminalInputAndReentrantReplacementKeepOneNativeOwner",
        "compositionDisposalDuringObservedPresentingAndPresentedPhasesFinishesOwnedTeardown",
        "actualSimulatorUnavailableAndCompetingModalOutcomesPreserveForeignPresenter",
        "controlledOriginalNativeImageWritesRealPngAndJpegAndSuccessOutlivesOwner",
    ).map { prefix + it }
    val compilerRequest = listOf(":calf-camera-picker:compileTestKotlinIosSimulatorArm64")
    val applicationRequest = listOf(":calf-camera-picker:iosSimulatorArm64ApplicationTest") +
        methods.flatMap { listOf("--tests", it) }
    check(gradle.startParameter.taskNames in setOf(compilerRequest, applicationRequest)) {
        "Camera accepts only its exact three-input compiler or five native methods, never full/publish/other tasks"
    }
    val nativeTaskRequested = gradle.startParameter.taskNames == applicationRequest
    val simulator = rootProject.providers.gradleProperty("nativecmpkitSimulatorDevice").orNull
    if (nativeTaskRequested) {
        check(System.getProperty("os.name") == "Mac OS X" && System.getProperty("os.arch") in setOf("aarch64", "arm64")) {
            "Actual Camera native execution requires the Arm64 Apple host; Linux KLIB is not native evidence"
        }
        check(simulator != null && Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(simulator)) {
            "Camera native task requires the same explicit recorded simulator as the original transport"
        }
    }
    val paths = listOf(
        "calf-camera-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/camerapicker/IosCameraOwnershipAcceptanceTest.kt",
        "calf-camera-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/camerapicker/internal/NativeCameraApplicationHost.kt",
        "calf-camera-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/camerapicker/internal/NativeCameraObjectIdentity.kt",
    )
    val expectedHashes = mapOf(
        "calf-camera-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/camerapicker/IosCameraOwnershipAcceptanceTest.kt" to "5e5a62825d8a47ad7a5880df2a75807aba01ffd79f4ffd601f04082a89797230",
        "calf-camera-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/camerapicker/internal/NativeCameraApplicationHost.kt" to "9a8a186ce3205a8b3ffb136d92e53c44139059e56775d84c9b21129ad8fa05fc",
        "calf-camera-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/camerapicker/internal/NativeCameraObjectIdentity.kt" to "62cb9f661dea845a7b103b497b3d788cbe3b738a6449e9860855b94575f80f1b",
    )
    val files = paths.map { relative ->
        val file = rootProject.file(relative)
        check(file.isFile && file.absoluteFile == file.canonicalFile &&
            file.toPath().startsWith(rootProject.projectDir.canonicalFile.toPath())) {
            "Only the exact three ordinary Camera authored test/host/identity inputs may be compiled"
        }
        file.canonicalFile
    }
    fun hashes(): Map<String, String> = paths.zip(files).associate { (relative, file) ->
        relative to MessageDigest.getInstance("SHA-256").digest(file.readBytes())
            .joinToString("") { "%02x".format(it.toInt() and 255) }
    }
    val compilation = project.tasks.getByName("compileTestKotlinIosSimulatorArm64")
    compilation.inputs.property("nativecmpkitCameraIosFocus", focus!!)
    // Public KGP source APIs; no replacement compiler or production-source edits.
    compilation.javaClass.getMethod("setSource", Array<Any>::class.java)
        .invoke(compilation, files.toTypedArray() as Any)
    val common = compilation.javaClass.getMethod("getCommonSources").invoke(compilation) as ConfigurableFileCollection
    common.setFrom(emptyList<Any>())
    val actual = compilation.javaClass.getMethod("getSources").invoke(compilation) as FileCollection
    fun verifySources() {
        check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common.files.isEmpty() && hashes() == expectedHashes) {
            "Camera effective compiler sources/hashes differ from exact three; common/accepted/foreign inputs forbidden"
        }
    }
    verifySources()
    fun admit(task: String, nativeTask: Boolean) {
        verifySources()
        check(rootProject.providers.gradleProperty("nativecmpkitCameraIosFocus").orNull == focus)
        if (nativeTask) check(gradle.startParameter.taskNames == applicationRequest &&
            rootProject.providers.gradleProperty("nativecmpkitSimulatorDevice").orNull == simulator)
        val receipt = rootProject.file(if (nativeTask)
            "build/ci-verification/camera-ios-native-source-admission.json"
            else "build/ci-verification/camera-ios-precompiler-source-admission.json")
        receipt.parentFile.mkdirs()
        receipt.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(mapOf(
            "schema_version" to 1, "task" to task, "focus" to focus,
            "phase" to if (nativeTask) "native-task-source-admission" else "precompiler-source-admission",
            "selected_methods" to methods, "effective_sources" to paths, "common_sources" to emptyList<String>(),
            "source_sha256" to hashes(), "excluded_unrelated_test_sources" to true,
            "production_source_sets_changed" to false, "compiler_executions_attested" to 0,
            "apple_links_attested" to 0, "native_tests_executed" to 0,
            "scope" to "Source/selection admission only; compiler result and fresh native XML/runtime/cleanup decide results",
        ))) + "\n")
        logger.lifecycle("NATIVECMPKIT_CAMERA_SOURCE_ADMISSION methods=5 sources=3 common=0 nativeTestsExecuted=0")
    }
    compilation.doFirst { admit(compilation.path, false) }
    // Always a fresh admission before the native task, even if its exact unchanged
    // compiler/link prerequisites are legitimately UP-TO-DATE; never relabel them.
    project.tasks.getByName("iosSimulatorArm64ApplicationTest").doFirst { admit(path, true) }
}
