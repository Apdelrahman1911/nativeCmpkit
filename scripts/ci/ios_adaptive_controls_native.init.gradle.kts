import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.FileCollection
import groovy.json.JsonOutput
import java.security.MessageDigest

// Native-only opt-in for four exact public adaptive methods on one real OS branch.
// This is distinct from adaptive_controls_compile.init.gradle.kts; that script
// remains compile-only for iOS. Original application/Worker/XML/custody/cleanup
// transport still rejects this selection until the lead registers its spec.
gradle.projectsEvaluated {
    val project = rootProject.findProject(":calf-ui") ?: return@projectsEvaluated
    val focus = rootProject.providers.gradleProperty("nativecmpkitAdaptiveControlsFocus").orNull
    val prefix = "com.mohamedrejeb.calf.ui."
    val branches = mapOf(
        "ui-native-adaptive-pre26" to listOf(
            prefix + "slider.AdaptiveSliderNativeMatrixTest.pre26PublicStepsTapDragAndAccessibilityMatrix",
            prefix + "slider.AdaptiveSliderNativeMatrixTest.pre26PublicNegativeStepsAreRejected",
            prefix + "controls.AdaptiveControlCustomizationMatrixTest.pre26CustomColorsContentAndInteractionsSurviveDarkAndLargeText",
            prefix + "toolbar.AdaptiveToolbarFallbackNativeTest.pre26EmptyAndPopulatedItemsRenderMaterialSlotsAndCallerPlacement",
        ),
        "ui-native-adaptive-ios26plus" to listOf(
            prefix + "slider.AdaptiveSliderNativeMatrixTest.ios26PublicStepsTapDragAndAccessibilityMatrix",
            prefix + "slider.AdaptiveSliderNativeMatrixTest.ios26PublicNegativeStepsAreRejected",
            prefix + "controls.AdaptiveControlCustomizationMatrixTest.ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText",
            prefix + "toolbar.AdaptiveToolbarFallbackNativeTest.ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement",
        ),
    )
    check(focus in branches) { "Explicit adaptive OS-branch focus required; no default host or broad test selection" }
    val selectors = branches.getValue(focus!!)
    val applicationRequest = listOf(":calf-ui:iosSimulatorArm64ApplicationTest") +
        selectors.flatMap { listOf("--tests", it) }
    check(gradle.startParameter.taskNames == applicationRequest) {
        "Adaptive native init accepts only its exact four application methods; no standalone compiler/full/publish task"
    }
    check(System.getProperty("os.name") == "Mac OS X" && System.getProperty("os.arch") in setOf("aarch64", "arm64")) {
        "Adaptive native execution requires the actual Arm64 Apple host, never a skipped Linux compile substitute"
    }
    val simulator = rootProject.providers.gradleProperty("nativecmpkitSimulatorDevice").orNull
    check(simulator != null && Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(simulator)) {
        "Adaptive native execution requires the same explicit recorded simulator UDID as the original transport"
    }
    val paths = listOf(
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
    )
    val files = paths.map { relative ->
        val file = rootProject.file(relative)
        check(file.isFile && file.absoluteFile == file.canonicalFile &&
            file.toPath().startsWith(rootProject.projectDir.canonicalFile.toPath())) {
            "Only the exact six ordinary authored adaptive/owned-host inputs may be compiled"
        }
        file.canonicalFile
    }
    val compilation = project.tasks.getByName("compileTestKotlinIosSimulatorArm64")
    // Public KGP source APIs already qualified by the separate compiler-only run.
    // Do not invalidate the compiler cache solely because the actual OS focus
    // differs: both branches use the same six sources and generated test suites.
    compilation.javaClass.getMethod("setSource", Array<Any>::class.java).invoke(compilation, files.toTypedArray() as Any)
    val common = compilation.javaClass.getMethod("getCommonSources").invoke(compilation) as ConfigurableFileCollection
    common.setFrom(emptyList<Any>())
    val actual = compilation.javaClass.getMethod("getSources").invoke(compilation) as FileCollection
    fun verifySources() {
        check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common.files.isEmpty()) {
            "Effective adaptive native sources differ from the exact six-file admission"
        }
    }
    verifySources()
    compilation.doFirst { verifySources() }
    // Fresh source admission is recorded before the owning native task, even if
    // its unchanged compiler/link prerequisites are legitimately UP-TO-DATE.
    // This receipt makes NO claim that a compiler, link or native test executed.
    project.tasks.getByName("iosSimulatorArm64ApplicationTest").doFirst {
        verifySources()
        check(gradle.startParameter.taskNames == applicationRequest &&
            rootProject.providers.gradleProperty("nativecmpkitSimulatorDevice").orNull == simulator)
        val hashes = paths.zip(files).associate { (relative, file) ->
            relative to MessageDigest.getInstance("SHA-256").digest(file.readBytes())
                .joinToString("") { "%02x".format(it.toInt() and 255) }
        }
        val receipt = rootProject.file("build/ci-verification/adaptive-controls-native-source-admission.json")
        receipt.parentFile.mkdirs()
        receipt.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(mapOf(
            "task" to path, "focus" to focus, "selected_methods" to selectors,
            "effective_sources" to paths, "source_sha256" to hashes,
            "excluded_unrelated_test_sources" to true, "production_source_sets_changed" to false,
            "compiler_executions_attested" to 0, "apple_links_attested" to 0, "native_tests_executed" to 0,
            "scope" to "Source/selection admission only; original fresh native XML/runtime/cleanup decide results",
        ))) + "\n")
        logger.lifecycle("NATIVECMPKIT_ADAPTIVE_NATIVE_ADMISSION methods=4 sources=6 nativeTestsExecuted=0")
    }
}
