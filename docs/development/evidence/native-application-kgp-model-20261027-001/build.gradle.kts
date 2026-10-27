import org.jetbrains.kotlin.gradle.plugin.mpp.KotlinNativeTarget
import org.jetbrains.kotlin.gradle.plugin.mpp.NativeBuildType.DEBUG
import org.jetbrains.kotlin.gradle.targets.native.tasks.KotlinNativeHostTest
import java.time.Duration

plugins { kotlin("multiplatform") version "2.4.20" }
kotlin {
    linuxX64()
    iosSimulatorArm64()
    targets.withType<KotlinNativeTarget>().configureEach {
        binaries.test("application", listOf(DEBUG)) {
            freeCompilerArgs += listOf("-entry", "nativecmpkit.verification.uikit.nativeApplicationMain")
        }
    }
}
val target = kotlin.targets.getByName("iosSimulatorArm64") as KotlinNativeTarget
val application = target.binaries.getTest("application", DEBUG)
tasks.register<KotlinNativeHostTest>("iosSimulatorArm64ApplicationTest") {
    executable(layout.projectDirectory.file("owned-wrapper.py").asFile)
    dependsOn(application.linkTaskProvider)
    args = listOf("--owned-binary", application.outputFile.absolutePath)
    targetName = "iosSimulatorArm64"
    environment("NATIVECMPKIT_MODEL_ONLY", "synthetic-no-device-selected")
    ignoreFailures = false
    ignoreRunFailures = false
    binaryResultsDirectory.set(layout.buildDirectory.dir("test-results/$name/binary"))
    reports.html.outputLocation.set(layout.buildDirectory.dir("reports/tests/$name"))
    reports.junitXml.required.set(true)
    reports.junitXml.outputLocation.set(layout.buildDirectory.dir("test-results/$name"))
    timeout.set(Duration.ofSeconds(120))
}
tasks.register("inspectOwnedApplicationModel") {
    doLast {
        for (native in kotlin.targets.withType<KotlinNativeTarget>()) {
            val extra = native.binaries.getTest("application", DEBUG)
            val normal = native.binaries.getTest(DEBUG)
            check(extra.compilation === normal.compilation)
            check(extra !== normal)
            check(extra.freeCompilerArgs == listOf("-entry", "nativecmpkit.verification.uikit.nativeApplicationMain"))
            check(normal.freeCompilerArgs.isEmpty())
            println("NATIVECMPKIT_KGP_MODEL target=${native.name} extra=${extra.name} normal=${normal.name} link=${extra.linkTaskName} sameCompilation=true unchangedDefault=true")
        }
        val task = tasks.named("iosSimulatorArm64ApplicationTest", KotlinNativeHostTest::class.java).get()
        check(task.targetName == "iosSimulatorArm64")
        check(!task.ignoreFailures && !task.ignoreRunFailures)
        check(task.environment["NATIVECMPKIT_MODEL_ONLY"] == "synthetic-no-device-selected")
        println("NATIVECMPKIT_KGP_MODEL hostTask=${task.name} executable=${task.executable.name} args=${task.args.size} xml=${task.reports.junitXml.outputLocation.get().asFile.name} binary=${task.binaryResultsDirectory.get().asFile.name}")
    }
}
