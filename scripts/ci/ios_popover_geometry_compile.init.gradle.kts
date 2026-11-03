import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.FileCollection
import groovy.json.JsonOutput
import java.security.MessageDigest

// Four opt-in library OS-geometry inputs only, one fresh selected method.
// Ordinary source sets, production/dependencies and previous native bodies stay unchanged.
// The original application/Worker/XML/custody/cleanup gates remain mandatory.
gradle.projectsEvaluated {
    // Init scripts also visit convention/included builds. They do not own UI's
    // compilation and must not reject their independent plugin-resolution tasks.
    val project = rootProject.findProject(":calf-ui") ?: return@projectsEvaluated
    // Gradle retains task-specific --tests options in startParameter.taskNames.
    // Admit only the explicit authored phone-portrait OR iPad-rotation method.
    val focus = rootProject.providers.gradleProperty("nativecmpkitPopoverGeometryFocus").orNull
    val methods = mapOf(
        "ui-native-popover-portrait-traits" to "nativePortraitTraitsAndViewLocalAnchorUseTheOwnedScene",
        "ui-native-popover-os-rotation" to "nativeOSRotationRefreshesOwnedAnchorsAndRestoresTheOriginalOrientation",
    )
    check(focus in methods) { "Select the exact native OS geometry focus; no implicit/default host" }
    val applicationRequest = listOf(":calf-ui:iosSimulatorArm64ApplicationTest", "--tests",
        "com.mohamedrejeb.calf.ui.dialog.NativePopoverGeometryTest." + methods.getValue(focus!!))
    check(gradle.startParameter.taskNames in setOf(listOf(":calf-ui:compileTestKotlinIosSimulatorArm64"), applicationRequest)) {
        "OS geometry compilation accepts only its exact test compiler or one native method"
    }
    val paths = listOf(
        "calf-ui/src/iosGeometryTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativePopoverGeometryTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
        "calf-ui/src/iosGeometryTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativePopoverGeometryScene.kt",
    )
    val files = paths.map { relative ->
        val file = rootProject.file(relative)
        check(file.isFile && file.absoluteFile == file.canonicalFile &&
            file.canonicalFile.toPath().startsWith(rootProject.projectDir.canonicalFile.toPath())) {
            "Only the ordinary exact four focused Kotlin sources may be compiled"
        }
        file.canonicalFile
    }
    val compilation = project.tasks.getByName("compileTestKotlinIosSimulatorArm64")
    compilation.inputs.property("nativecmpkitPopoverGeometryFocus", focus!!)
    // Init scripts do not share the later KGP classpath. These are the public
    // source APIs inspected on KGP2.4.20, not replacement compiler internals.
    compilation.javaClass.getMethod("setSource", Array<Any>::class.java)
        .invoke(compilation, files.toTypedArray() as Any)
    val common = compilation.javaClass.getMethod("getCommonSources").invoke(compilation) as ConfigurableFileCollection
    common.setFrom(emptyList<Any>())
    val actual = compilation.javaClass.getMethod("getSources").invoke(compilation) as FileCollection
    check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common.files.isEmpty()) {
        "Effective focused test sources differ from the exact four-file compilation"
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
            "focus" to focus,
            "source_sha256" to hashes,
            "effective_sources" to paths,
            "excluded_unrelated_test_sources" to true,
            "production_source_sets_changed" to false,
            "native_tests_executed" to 0,
            "scope" to "Actual precompiler source admission only; compiler exit and fresh native XML decide outcomes",
        ))) + "\n")
        logger.lifecycle("NATIVECMPKIT_UI_FOCUSED_COMPILE sources=4 nativeTestsExecuted=0 productionChanged=false")
    }
}
