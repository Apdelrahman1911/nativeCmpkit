// SPDX-License-Identifier: Apache-2.0
import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.FileCollection
import groovy.json.JsonOutput
import java.security.MessageDigest

// Explicit five-case completion/cancellation batch; one compiler/link/Worker invocation only. Keep production, dependency
// graphs and the ordinary/full test source sets unchanged. Native tests still
// execute freshly with the original application host, Worker and JUnit parser.
gradle.projectsEvaluated {
    // Init scripts also visit convention/included builds. They do not own UI's
    // compilation and must not reject their independent plugin-resolution tasks.
    val project = rootProject.findProject(":calf-ui") ?: return@projectsEvaluated
    // Gradle retains task-specific --tests options in startParameter.taskNames.
    // Admit only these five authored native methods, not a filtered approximation.
    val applicationRequest = listOf(":calf-ui:iosSimulatorArm64ApplicationTest") + listOf(
        "com.mohamedrejeb.calf.ui.internal.NativeModalLifecycleReplacementTest.publicCompositionDisposalDuringNativeHideReleasesContentAndCanReopen",
        "com.mohamedrejeb.calf.ui.internal.NativeWorkerBridgeOwnershipTest.replacedPlainCompositionReleasesAnOwnerCreatedOnTheWorker",
        "com.mohamedrejeb.calf.ui.internal.NativeWorkerBridgeOwnershipTest.pooledWorkerBridgePreservesMainResultAndExactThrowableIdentity",
        "com.mohamedrejeb.calf.ui.sheet.NativeSheetCancellationRepeatTest.cancelledShowRepeatsWithANewNativeAnimationAndItsOwnCompletion",
        "com.mohamedrejeb.calf.ui.sheet.NativeSheetCancellationRepeatTest.cancelledHideRepeatsWithANewNativeAnimationAndItsOwnCompletion",
    ).flatMap { identity -> listOf("--tests", identity) }
    val permittedTasks = setOf(
        listOf(":calf-ui:compileTestKotlinIosSimulatorArm64"),
        applicationRequest,
    )
    check(gradle.startParameter.taskNames in permittedTasks) {
        "Focused modal compilation accepts only its exact test compiler or application task"
    }
    val paths = listOf(
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeModalLifecycleReplacementTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeWorkerBridgeOwnershipTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/sheet/NativeSheetCancellationRepeatTest.kt",
    )
    val files = paths.map { relative ->
        val file = rootProject.file(relative)
        check(file.isFile && file.absoluteFile == file.canonicalFile &&
            file.canonicalFile.toPath().startsWith(rootProject.projectDir.canonicalFile.toPath())) {
            "Only the ordinary exact five focused Kotlin sources may be compiled"
        }
        file.canonicalFile
    }
    val compilation = project.tasks.getByName("compileTestKotlinIosSimulatorArm64")
    // Init scripts do not share the later KGP classpath. These are the public
    // source APIs inspected on KGP2.4.20, not replacement compiler internals.
    compilation.javaClass.getMethod("setSource", Array<Any>::class.java)
        .invoke(compilation, files.toTypedArray() as Any)
    val common = compilation.javaClass.getMethod("getCommonSources").invoke(compilation) as ConfigurableFileCollection
    common.setFrom(emptyList<Any>())
    val actual = compilation.javaClass.getMethod("getSources").invoke(compilation) as FileCollection
    check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common.files.isEmpty()) {
        "Effective focused test sources differ from the exact five-file compilation"
    }
    compilation.doFirst {
        check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common.files.isEmpty()) {
            "Effective focused test sources changed before the native compiler"
        }
        val hashes = paths.zip(files).associate { (relative, file) ->
            relative to MessageDigest.getInstance("SHA-256").digest(file.readBytes())
                .joinToString("") { "%02x".format(it.toInt() and 255) }
        }
        val receipt = rootProject.file("build/ci-verification/ios-focused-compilation.json")
        receipt.parentFile.mkdirs()
        receipt.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(mapOf(
            "task" to compilation.path,
            "focus" to "ui-native-modal-completion-cancellation",
            "source_sha256" to hashes,
            "effective_sources" to paths,
            "excluded_unrelated_test_sources" to true,
            "production_source_sets_changed" to false,
            "native_tests_executed" to 0,
            "scope" to "Actual precompiler source admission only; compiler exit and fresh native XML decide outcomes",
        ))) + "\n")
        logger.lifecycle("NATIVECMPKIT_UI_FOCUSED_COMPILE sources=5 nativeTestsExecuted=0 productionChanged=false")
    }
}
