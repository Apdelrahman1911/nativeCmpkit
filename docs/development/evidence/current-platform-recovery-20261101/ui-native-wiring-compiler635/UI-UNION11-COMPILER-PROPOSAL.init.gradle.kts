// SPDX-License-Identifier: Apache-2.0
import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.FileCollection
import groovy.json.JsonOutput
import java.security.MessageDigest

// External source-only proposal, NOT executed by the producer. Lead review and fresh
// serial-local eight-GiB reserve precede one exact union11 test KLIB compilation.
// Both real adaptive bands remain authored (8) plus drag/shader6: declarations14;
// later native iOS26+ selects10, separate genuine pre26 selects4. No native proof.
gradle.projectsEvaluated {
    // The init also reaches included plugin builds. They do not own this module
    // or its requested task, so only the actual root may perform admission.
    val project = rootProject.findProject(":calf-ui") ?: return@projectsEvaluated
    check(gradle.startParameter.taskNames == listOf(":calf-ui:compileTestKotlinIosSimulatorArm64")) {
        "Related UI union compiler accepts only its exact test KLIB task; no native/full/publish task"
    }
    val paths = listOf(
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UiDragShaderTestHost.kt",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/PointerCancellation.kt",
    )
    val expectedHashes = mapOf(
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt" to "5132474a968f50ce40e161049b32700c28d1709d0e6b1bbd6fecb239f6fd9e20",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt" to "9ed073effcf3b5399f4838887d271a1b893a2a9bb123afc6771fcd15d2ca87d4",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt" to "c792203a97cc8bdea914856b5cd53195f7a623170820fbc3f91a4ef9fd55d61d",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt" to "c7cfac7363f93e1fa880378f5e38c7289faa9e0b3570e3999c9fe11b2bdc2207",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt" to "ea18a76b5270fee0c95e953e6a4d280cc00b4fc2b64538a6ca23f7097ca43a0f",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt" to "d3cccfc654399598abf00e04d6f40529a3802e9488448afde120da8180932df0",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt" to "d1e96296dce57bb817a08abca87a2943d9924745d1208fd7591751ed9d5dd3e8",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt" to "9ded1ba61f6702ef2b6f28312b6971a37a112564c1d030dbe22b0f25419fefbf",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt" to "1b417a078d26c7d2f09dcaa5c5e17ac9be0806fd4f8a88dffb5e616978207954",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UiDragShaderTestHost.kt" to "7ce8cef67a1d4df0430852e77d37967574d42fd039b76a0a6ebb347f93b8cb8c",
        "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/PointerCancellation.kt" to "5e9aef0d114a3e4b9d992ce3be2fd5fd96951443a527e68f1c6f87f78d6a1b2b",
    )
    val files = paths.map { relative ->
        val file = rootProject.file(relative)
        check(file.isFile && file.absoluteFile == file.canonicalFile &&
            file.toPath().startsWith(rootProject.projectDir.canonicalFile.toPath()) &&
            (java.nio.file.Files.getAttribute(file.toPath(), "unix:nlink") as Number).toLong() == 1L) {
            "Only exact ordinary eleven-file adaptive/drag/shader/owned-host inputs may be compiled"
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
            "Effective related UI test sources differ from the exact eleven-file admission"
        }
    }
    verifySources()
    compilation.doFirst {
        verifySources()
        val hashes = paths.zip(files).associate { (relative, file) ->
            relative to MessageDigest.getInstance("SHA-256").digest(file.readBytes())
                .joinToString("") { "%02x".format(it.toInt() and 255) }
        }
        check(hashes == expectedHashes) { "Union11 source hashes differ from the reviewed compiler proposal" }
        val receipt = rootProject.file("build/ci-verification/ui-related-union11-focused-compilation.json")
        receipt.parentFile.mkdirs()
        receipt.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(mapOf(
            "task" to compilation.path,
            "effective_sources" to paths,
            "common_sources" to emptyList<String>(),
            "source_sha256" to hashes,
            "authored_test_methods" to 14,
            "excluded_unrelated_test_sources" to true,
            "production_source_sets_changed" to false,
            "compiler_executions_attested" to 0,
            "apple_links_attested" to 0,
            "native_tests_executed" to 0,
            "scope" to "Precompiler source admission only; process result decides compilation, never native behavior",
        ))) + "\n")
        logger.lifecycle("NATIVECMPKIT_UI_RELATED_UNION_COMPILE sources=11 authoredMethods=14 nativeTestsExecuted=0")
    }
}
