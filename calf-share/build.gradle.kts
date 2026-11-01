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
    sourceSets.named("androidHostTest").dependencies {
        implementation(libs.junit)
        implementation(libs.robolectric)
    }

    sourceSets.matching { it.name == "androidDeviceTest" }.configureEach {
        dependencies {
            implementation(libs.junit)
            implementation(libs.androidx.test.runner)
            implementation(libs.androidx.test.core)
            implementation(libs.androidx.test.junit)
        }
    }

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlinx.coroutines.test)
    }

    sourceSets.commonMain.dependencies {
        implementation(libs.kotlinx.coroutines.core)
        api(projects.calfIo)

        implementation(libs.compose.foundation)
    }

    sourceSets.androidMain.dependencies {
        implementation(libs.activity.compose)
    }

    sourceSets.webMain.dependencies {
        implementation(libs.kotlinx.browser)
    }
    // Verification-only native application, not a sample/published framework.
    // Real Share presentation/disposal tests need UIApplicationMain and a live
    // main loop; KLIB/typechecking or a command-line Skiko scene is not that host.
    targets.withType<KotlinNativeTarget>().matching { it.name == "iosSimulatorArm64" }.configureEach {
        binaries.test("application", listOf(DEBUG)) {
            freeCompilerArgs += listOf("-entry", "com.mohamedrejeb.calf.share.internal.nativeApplicationMain")
        }
        val application = binaries.getTest("application", DEBUG)
        tasks.register<KotlinNativeHostTest>("iosSimulatorArm64ApplicationTest") {
            group = "verification"
            description = "Related library Share tests in an owned UIKit application using KGP's actual JUnit parser."
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
            outputs.doNotCacheIf("Share application requires actual fresh native execution") { true }
            onlyIf("UIKit simulator applications require macOS") { System.getProperty("os.name") == "Mac OS X" }
            doFirst {
                val identifier = providers.gradleProperty("nativecmpkitSimulatorDevice").orNull
                    ?: error("Select an actual booted simulator with nativecmpkitSimulatorDevice")
                check(Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(identifier))
                environment("NATIVECMPKIT_UIKIT_SIMULATOR", identifier)
                environment("NATIVECMPKIT_UIKIT_RESULT_ROOT",
                    providers.environmentVariable("NATIVECMPKIT_UIKIT_RESULT_ROOT").orNull
                        ?: "build/ci-verification/native-share-application")
                logger.lifecycle("NATIVECMPKIT_TEST_SIMULATOR task=$path device=$identifier host=genuine-uikit-application")
            }
        }
    }
}

// Shared host/release manifest pipeline; retained task names preserve source-build scripts.
configureNativeLibrary()
