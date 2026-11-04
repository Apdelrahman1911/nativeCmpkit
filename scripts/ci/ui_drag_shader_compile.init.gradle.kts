// SPDX-License-Identifier: Apache-2.0
import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.FileCollection
import groovy.json.JsonOutput
import java.security.MessageDigest

// Independent compile-only selection. Ordinary production/source sets, native
// binaries and the older accepted eight controls remain entirely unchanged.
gradle.projectsEvaluated {
    // The init also reaches included plugin builds. They do not own this module
    // or its requested task, so only the actual root may perform admission.
    val project = rootProject.findProject(":calf-ui") ?: return@projectsEvaluated
    check(gradle.startParameter.taskNames == listOf(":calf-ui:compileTestKotlinIosSimulatorArm64")) {
        "Drag/shader compiler accepts only its exact test KLIB task; no native/full/publish task"
    }
    val prefix = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/"
    val paths = listOf(
        prefix + "utils/DampedDragLifecycleRegressionTest.kt",
        prefix + "utils/InteractiveHighlightResourceLifecycleTest.kt",
        prefix + "button/LiquidButtonConstructionTraceTest.kt",
        prefix + "utils/UiDragShaderTestHost.kt",
        prefix + "internal/PointerCancellation.kt",
        prefix + "internal/NativeUiApplicationHost.kt",
        prefix + "internal/NativeObjectIdentity.kt",
    )
    val files = paths.map { relative ->
        val file = rootProject.file(relative)
        check(file.isFile && file.absoluteFile == file.canonicalFile &&
            file.toPath().startsWith(rootProject.projectDir.canonicalFile.toPath())) {
            "Only exact ordinary authored drag/shader/owned-host inputs may be compiled"
        }
        file.canonicalFile
    }
    val compilation = project.tasks.getByName("compileTestKotlinIosSimulatorArm64")
    compilation.javaClass.getMethod("setSource", Array<Any>::class.java)
        .invoke(compilation, files.toTypedArray() as Any)
    val common = compilation.javaClass.getMethod("getCommonSources").invoke(compilation) as ConfigurableFileCollection
    common.setFrom(emptyList<Any>())
    val actual = compilation.javaClass.getMethod("getSources").invoke(compilation) as FileCollection
    fun verifySources() {
        check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common.files.isEmpty()) {
            "Effective drag/shader test sources differ from the exact seven-file admission"
        }
    }
    verifySources()
    compilation.doFirst {
        verifySources()
        val hashes = paths.zip(files).associate { (relative, file) ->
            relative to MessageDigest.getInstance("SHA-256").digest(file.readBytes())
                .joinToString("") { "%02x".format(it.toInt() and 255) }
        }
        val receipt = rootProject.file("build/ci-verification/ui-drag-shader-focused-compilation.json")
        receipt.parentFile.mkdirs()
        receipt.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(mapOf(
            "task" to compilation.path,
            "effective_sources" to paths,
            "common_sources" to emptyList<String>(),
            "source_sha256" to hashes,
            "authored_new_test_methods" to 6,
            "excluded_unrelated_test_sources" to true,
            "production_source_sets_changed" to false,
            "compiler_executions_attested" to 0,
            "apple_links_attested" to 0,
            "native_tests_executed" to 0,
            "scope" to "Precompiler source admission only; process result decides compilation, never native behavior",
        ))) + "\n")
        logger.lifecycle("NATIVECMPKIT_UI_DRAG_SHADER_FOCUSED_COMPILE sources=7 newMethods=6 nativeTestsExecuted=0")
    }
}
