import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.FileCollection
import org.gradle.api.tasks.testing.Test
import groovy.json.JsonOutput
import java.security.MessageDigest

// Independent opt-in compiler selection only; no ordinary source-set/routing/policy change.
gradle.projectsEvaluated {
    val project = rootProject.findProject(":calf-ui") ?: return@projectsEvaluated
    val desktopClass = "com.mohamedrejeb.calf.ui.toggle.CupertinoSwitchThumbContentColorTest"
    val desktopMethods = listOf(
        "currentCallerIconColorsFollowEveryStateAndDoNotLeakToSiblingContent",
        "disabledCustomThumbInDarkLargeTextActuallyDrawsTheSuppliedIconColor",
    )
    val desktopRequest = listOf(":calf-ui:desktopTest") + desktopMethods.flatMap { listOf("--tests", "$desktopClass.$it") }
    val desktop = gradle.startParameter.taskNames == desktopRequest
    val paths: List<String>
    val taskName: String
    if (desktop) {
        paths = listOf("calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/toggle/CupertinoSwitchThumbContentColorTest.kt")
        taskName = "compileTestKotlinDesktop"
        project.tasks.withType<Test>().matching { it.name == "desktopTest" }.configureEach {
            doFirst {
                check(filter.includePatterns.isEmpty() && filter.excludePatterns.isEmpty())
                // Inspected Gradle9.7.1 keeps --tests separately from configured includePatterns.
                @Suppress("UNCHECKED_CAST")
                val commandLine = filter.javaClass.getMethod("getCommandLineIncludePatterns").invoke(filter) as Set<String>
                check(commandLine == desktopMethods.map { "$desktopClass.$it" }.toSet())
                check(filter.isFailOnNoMatchingTests && !ignoreFailures && maxParallelForks == 1)
            }
        }
    } else {
        check(gradle.startParameter.taskNames == listOf(":calf-ui:compileTestKotlinIosSimulatorArm64")) {
            "Adaptive controls compiler accepts only its exact Desktop2 or iOS test compiler; no default/full native execution"
        }
        paths = listOf(
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
        )
        taskName = "compileTestKotlinIosSimulatorArm64"
    }
    val files = paths.map { relative ->
        val file = rootProject.file(relative)
        check(file.isFile && file.absoluteFile == file.canonicalFile &&
            file.toPath().startsWith(rootProject.projectDir.canonicalFile.toPath())) {
            "Only exact ordinary authored test inputs may be compiled"
        }
        file.canonicalFile
    }
    val compilation = project.tasks.getByName(taskName)
    compilation.javaClass.getMethod("setSource", Array<Any>::class.java).invoke(compilation, files.toTypedArray() as Any)
    // KGP's native compiler exposes public commonSources; its JVM KotlinCompile does not.
    // The JVM path is admitted by its exact public source collection, not guessed reflection.
    val common = if (desktop) null else
        compilation.javaClass.getMethod("getCommonSources").invoke(compilation) as ConfigurableFileCollection
    common?.setFrom(emptyList<Any>())
    val actual = compilation.javaClass.getMethod("getSources").invoke(compilation) as FileCollection
    check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common?.files.orEmpty().isEmpty())
    compilation.doFirst {
        check(actual.files.map { it.canonicalFile }.toSet() == files.toSet() && common?.files.orEmpty().isEmpty())
        val hashes = paths.zip(files).associate { (relative, file) ->
            relative to MessageDigest.getInstance("SHA-256").digest(file.readBytes())
                .joinToString("") { "%02x".format(it.toInt() and 255) }
        }
        val receipt = rootProject.file("build/ci-verification/adaptive-controls-focused-compilation.json")
        receipt.parentFile.mkdirs()
        receipt.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(mapOf(
            "task" to compilation.path, "effective_sources" to paths, "source_sha256" to hashes,
            "excluded_unrelated_test_sources" to true, "production_source_sets_changed" to false,
            "native_tests_executed" to 0,
            "scope" to "Precompiler admission only; process exit and fresh XML decide results",
        ))) + "\n")
        logger.lifecycle("NATIVECMPKIT_ADAPTIVE_FOCUSED_COMPILE sources=${paths.size} nativeTestsExecuted=0")
    }
}
