// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
import org.jetbrains.kotlin.gradle.plugin.mpp.KotlinNativeTarget
import org.jetbrains.kotlin.gradle.plugin.mpp.NativeBuildType.DEBUG
import org.jetbrains.kotlin.gradle.targets.native.tasks.KotlinNativeHostTest
import java.time.Duration

plugins {
    id("compose.multiplatform")
    id("module.publication")
}

kotlin {
    sourceSets.matching { it.name == "androidDeviceTest" }.configureEach {
        dependencies {
            implementation(libs.junit)
            implementation(libs.androidx.test.runner)
            implementation(libs.androidx.test.core)
            implementation(libs.androidx.test.junit)
            implementation(libs.androidx.core)
            implementation(libs.androidx.compose.ui.test.junit4)
            implementation(libs.androidx.compose.ui.test.manifest)
        }
    }

    sourceSets.named("androidHostTest").dependencies {
        implementation(libs.junit)
        implementation(libs.robolectric)
        implementation(libs.androidx.compose.ui.test.junit4)
        implementation(libs.androidx.compose.ui.test.manifest)
    }

    sourceSets.commonMain.dependencies {
        api(projects.calfIo)

        implementation(libs.compose.foundation)
        implementation(libs.kotlinx.coroutines.core)
    }

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlinx.coroutines.test)
        implementation(libs.kotlin.test)
    }

    sourceSets.desktopTest.dependencies {
        // Real Compose-window library tests need the actual host renderer.
        // Test-only: never publish a host-classified Skiko runtime to consumers.
        implementation(compose.desktop.currentOs)
    }

    sourceSets.androidMain.dependencies {
        implementation(libs.activity.compose)
    }

    sourceSets.webMain.dependencies {
        // Public browser saver overloads accept W3C File and Blob, not private implementation types.
        api(libs.kotlinx.browser)
    }

    // Verification-only native application, not a sample/published framework.
    // UTType and real picker lifecycle tests need UIApplicationMain and a live
    // main loop; command-line simctl spawn cannot establish those contracts.
    targets.withType<KotlinNativeTarget>().matching { it.name == "iosSimulatorArm64" }.configureEach {
        binaries.test("application", listOf(DEBUG)) {
            freeCompilerArgs += listOf("-entry", "com.mohamedrejeb.calf.picker.internal.nativeApplicationMain")
        }
        val application = binaries.getTest("application", DEBUG)
        tasks.register<KotlinNativeHostTest>("iosSimulatorArm64ApplicationTest") {
            group = "verification"
            description = "Related library picker tests in an owned UIKit application using KGP's actual JUnit parser."
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
            outputs.doNotCacheIf("Picker application requires actual fresh native execution") { true }
            onlyIf("UIKit simulator applications require macOS") { System.getProperty("os.name") == "Mac OS X" }
            doFirst {
                val identifier = providers.gradleProperty("nativecmpkitSimulatorDevice").orNull
                    ?: error("Select an actual booted simulator with nativecmpkitSimulatorDevice")
                check(Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(identifier))
                environment("NATIVECMPKIT_UIKIT_SIMULATOR", identifier)
                environment("NATIVECMPKIT_UIKIT_RESULT_ROOT",
                    providers.environmentVariable("NATIVECMPKIT_UIKIT_RESULT_ROOT").orNull
                        ?: "build/ci-verification/native-picker-application")
                logger.lifecycle("NATIVECMPKIT_TEST_SIMULATOR task=$path device=$identifier host=genuine-uikit-application")
            }
        }
    }
}

// Shared host/release manifest pipeline; retained task names preserve source-build scripts.
configureNativeLibrary()
