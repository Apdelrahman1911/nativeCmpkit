// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
import org.jetbrains.kotlin.gradle.plugin.mpp.KotlinNativeTarget
import org.jetbrains.kotlin.gradle.plugin.mpp.NativeBuildType.DEBUG
import org.jetbrains.kotlin.gradle.targets.native.tasks.KotlinNativeHostTest
import java.time.Duration

plugins {
    id("compose.multiplatform")
    id("module.publication")
}

val cameraIosFocus = providers.gradleProperty("nativecmpkitCameraIosFocus").orNull
check(cameraIosFocus == null || cameraIosFocus == "ios-camera-ownership-memory-callback") {
    "Only the exact Camera NEW5 verification focus is allowed"
}

kotlin {
    sourceSets.named("androidHostTest").dependencies {
        implementation(libs.junit)
        implementation(libs.robolectric)
        implementation(libs.androidx.compose.ui.test.junit4)
        implementation(libs.androidx.compose.ui.test.manifest)
    }
    sourceSets.named("androidDeviceTest").dependencies {
        implementation(libs.junit)
        implementation(libs.androidx.test.runner)
        implementation(libs.androidx.test.junit)
        implementation(libs.androidx.test.core)
    }

    sourceSets.commonMain.dependencies {
        implementation(libs.kotlinx.coroutines.core)
        api(projects.calfIo)

        implementation(libs.compose.foundation)
    }

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlinx.coroutines.test)
        implementation(libs.kotlin.test)
    }

    sourceSets.androidMain.dependencies {
        implementation(libs.activity.compose)
    }

    // Opt-in verification-only Camera application; never a sample/public framework.
    // With no focus property, the existing iosSimulatorArm64Test route is untouched.
    if (cameraIosFocus != null) {
        targets.withType<KotlinNativeTarget>().matching { it.name == "iosSimulatorArm64" }.configureEach {
            binaries.test("application", listOf(DEBUG)) {
                freeCompilerArgs += listOf("-entry", "com.mohamedrejeb.calf.camerapicker.internal.nativeCameraApplicationMain")
            }
            val application = binaries.getTest("application", DEBUG)
            tasks.register<KotlinNativeHostTest>("iosSimulatorArm64ApplicationTest") {
                group = "verification"
                description = "Only NEW5 Camera ownership methods in a separately owned UIKit application using KGP's actual JUnit parser."
                executable(rootProject.file("scripts/ci/ios_ui_application.py"))
                dependsOn(application.linkTaskProvider)
                args = listOf("--binary", application.outputFile.absolutePath)
                targetName = "iosSimulatorArm64"
                ignoreFailures = false
                ignoreRunFailures = false
                binaryResultsDirectory.set(layout.buildDirectory.dir("test-results/$name/binary"))
                reports.html.outputLocation.set(layout.buildDirectory.dir("reports/tests/$name"))
                reports.junitXml.required.set(true)
                reports.junitXml.outputLocation.set(layout.buildDirectory.dir("test-results/$name"))
                timeout.set(Duration.ofSeconds(2400))
                outputs.upToDateWhen { false }
                outputs.doNotCacheIf("Camera application requires fresh actual native execution") { true }
                onlyIf("UIKit simulator applications require macOS") { System.getProperty("os.name") == "Mac OS X" }
                doFirst {
                    check(providers.gradleProperty("nativecmpkitCameraIosFocus").orNull == "ios-camera-ownership-memory-callback")
                    val identifier = providers.gradleProperty("nativecmpkitSimulatorDevice").orNull
                        ?: error("Select the actual recorded booted simulator")
                    check(Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(identifier))
                    environment("NATIVECMPKIT_UIKIT_SIMULATOR", identifier)
                    environment("NATIVECMPKIT_UIKIT_RESULT_ROOT",
                        providers.environmentVariable("NATIVECMPKIT_UIKIT_RESULT_ROOT").orNull
                            ?: "build/ci-verification/native-camera-application")
                    logger.lifecycle("NATIVECMPKIT_TEST_SIMULATOR task=$path device=$identifier host=genuine-uikit-application")
                }
            }
        }
    }

}
