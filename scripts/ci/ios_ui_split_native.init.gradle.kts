// SPDX-License-Identifier: Apache-2.0
import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.FileCollection
import groovy.json.JsonOutput
import java.security.MessageDigest
import java.time.Duration

// Exact UI650 nine/one isolation only. The legacy ten/pre26 init scripts and
// original native bodies remain unchanged. No full/compiler/publish fallback.
gradle.projectsEvaluated {
    val project = rootProject.findProject(":calf-ui") ?: return@projectsEvaluated
    val focus = rootProject.providers.gradleProperty("nativecmpkitUiSplitFocus").orNull
    val branches = mapOf(
        "ui-native-related-nine-ios26plus" to listOf(
            "com.mohamedrejeb.calf.ui.slider.AdaptiveSliderNativeMatrixTest.ios26PublicStepsTapDragAndAccessibilityMatrix",
            "com.mohamedrejeb.calf.ui.slider.AdaptiveSliderNativeMatrixTest.ios26PublicNegativeStepsAreRejected",
            "com.mohamedrejeb.calf.ui.toolbar.AdaptiveToolbarFallbackNativeTest.ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement",
            "com.mohamedrejeb.calf.ui.utils.DampedDragLifecycleRegressionTest.cancellationFromActualStartAndStopCallbacksCannotRecreateFeedbackAndNextGestureRecovers",
            "com.mohamedrejeb.calf.ui.utils.DampedDragLifecycleRegressionTest.removingAnActiveActualModifierLeavesNoReleaseWorkInTheCallerScopeAndRangeReplacementRecovers",
            "com.mohamedrejeb.calf.ui.utils.DampedDragLifecycleRegressionTest.thousandSustainedUpdatesTraceActualJobTreesAcrossFramesAndRepressWithoutCancellingSiblingWork",
            "com.mohamedrejeb.calf.ui.utils.InteractiveHighlightResourceLifecycleTest.disposingAPressedRetainedModifierClosesItsRealBuilderStopsPixelsAndNeverRestartsItsJobs",
            "com.mohamedrejeb.calf.ui.utils.InteractiveHighlightResourceLifecycleTest.removingAnActualPressedHighlightClosesItsBuilderAndNewCompositionUsesANewOwnedResource",
            "com.mohamedrejeb.calf.ui.button.LiquidButtonConstructionTraceTest.hundredActualPublicButtonsKeepOptionalShaderConstructionAtZeroThroughInputDisableAndRecreation",
        ),
        "ui-native-adaptive-customization-ios26plus" to listOf(
            "com.mohamedrejeb.calf.ui.controls.AdaptiveControlCustomizationMatrixTest.ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText",
        ),
    )
    val taskNames = mapOf(
        "ui-native-related-nine-ios26plus" to "iosSimulatorArm64UiNineApplicationTest",
        "ui-native-adaptive-customization-ios26plus" to "iosSimulatorArm64AdaptiveCustomizationApplicationTest",
    )
    val receipts = mapOf(
        "ui-native-related-nine-ios26plus" to "build/ci-verification/ui-nine-native-source-admission.json",
        "ui-native-adaptive-customization-ios26plus" to "build/ci-verification/adaptive-customization-native-source-admission.json",
    )
    val receiptSubdirectories = mapOf(
        "ui-native-related-nine-ios26plus" to "native-ui-nine-application",
        "ui-native-adaptive-customization-ios26plus" to "native-adaptive-customization-application",
    )
    val transportTimeouts = mapOf(
        "ui-native-related-nine-ios26plus" to 1920,
        "ui-native-adaptive-customization-ios26plus" to 600,
    )
    val sourcePaths = mapOf(
        "ui-native-related-nine-ios26plus" to listOf(
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UiDragShaderTestHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/PointerCancellation.kt",
        ),
        "ui-native-adaptive-customization-ios26plus" to listOf(
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
        ),
    )
    check(focus in branches) { "Select exactly the independent UI650 nine or customization one, never a default/broad request" }
    val selectedFocus = focus!!
    val selectors = branches.getValue(selectedFocus)
    val taskName = taskNames.getValue(selectedFocus)
    val applicationRequest = listOf(":calf-ui:$taskName") + selectors.flatMap { listOf("--tests", it) }
    check(gradle.startParameter.taskNames == applicationRequest) {
        "Split UI init accepts only its exact dedicated task and ordered nine/one method selectors"
    }
    check(rootProject.providers.gradleProperty("nativecmpkitImageMemoryDiagnostics").orNull == null) {
        "Split UI cannot reuse another application's diagnostic signing/runtime fixture"
    }
    check(System.getProperty("os.name") == "Mac OS X" && System.getProperty("os.arch") in setOf("aarch64", "arm64")) {
        "Split UI native execution requires the actual Arm64 Apple host, never a skipped Linux substitute"
    }
    val simulator = rootProject.providers.gradleProperty("nativecmpkitSimulatorDevice").orNull
    check(simulator != null && Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(simulator)) {
        "Split UI requires the same explicit recorded simulator UDID as the original transport"
    }
    val paths = sourcePaths.getValue(selectedFocus)
    val files = paths.map { relative ->
        val file = rootProject.file(relative)
        check(file.isFile && file.absoluteFile == file.canonicalFile &&
            file.toPath().startsWith(rootProject.projectDir.canonicalFile.toPath())) {
            "Only the exact ordinary authored ten/four split UI inputs may be compiled"
        }
        file.canonicalFile
    }
    val compilation = project.tasks.getByName("compileTestKotlinIosSimulatorArm64")
    compilation.javaClass.getMethod("setSource", Array<Any>::class.java).invoke(compilation, files.toTypedArray() as Any)
    val common = compilation.javaClass.getMethod("getCommonSources").invoke(compilation) as ConfigurableFileCollection
    common.setFrom(emptyList<Any>())
    val actual = compilation.javaClass.getMethod("getSources").invoke(compilation) as FileCollection
    fun verifySources() {
        check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common.files.isEmpty()) {
            "Effective split UI sources differ from their exact ten/four-file common0 admission"
        }
    }
    verifySources()
    compilation.doFirst { verifySources() }
    // No compiler/link/native execution is claimed by this fresh source receipt.
    // Its independent task-specific XML/runtime/Worker/cleanup decide results.
    val nativeTask = project.tasks.getByName(taskName)
    check(nativeTask.timeout.get() == Duration.ofSeconds(2400)) {
        "Each split task requires its independent unchanged2400s native-task bound"
    }
    nativeTask.doFirst {
        verifySources()
        check(gradle.startParameter.taskNames == applicationRequest &&
            rootProject.providers.gradleProperty("nativecmpkitSimulatorDevice").orNull == simulator &&
            nativeTask.timeout.get() == Duration.ofSeconds(2400))
        val hashes = paths.zip(files).associate { (relative, file) ->
            relative to MessageDigest.getInstance("SHA-256").digest(file.readBytes())
                .joinToString("") { "%02x".format(it.toInt() and 255) }
        }
        val receipt = rootProject.file(receipts.getValue(selectedFocus))
        receipt.parentFile.mkdirs()
        receipt.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(mapOf(
            "task" to path, "focus" to selectedFocus, "selected_methods" to selectors,
            "effective_sources" to paths, "common_sources" to emptyList<String>(), "source_sha256" to hashes,
            "receipt_subdirectory" to receiptSubdirectories.getValue(selectedFocus),
            "transport_timeout_seconds" to transportTimeouts.getValue(selectedFocus), "native_task_timeout_seconds" to 2400,
            "excluded_unrelated_test_sources" to true, "production_source_sets_changed" to false,
            "compiler_executions_attested" to 0, "apple_links_attested" to 0, "native_tests_executed" to 0,
            "scope" to "Source/selection admission only; original fresh native XML/runtime/cleanup decide results",
        ))) + "\n")
        logger.lifecycle("NATIVECMPKIT_UI_SPLIT_NATIVE_ADMISSION task=$path methods=${selectors.size} sources=${paths.size} nativeTestsExecuted=0")
    }
}
