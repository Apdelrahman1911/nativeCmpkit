// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
import java.time.Duration
import org.jetbrains.kotlin.gradle.plugin.mpp.KotlinNativeTarget
import org.jetbrains.kotlin.gradle.plugin.mpp.NativeBuildType.DEBUG
import org.jetbrains.kotlin.gradle.targets.native.tasks.KotlinNativeHostTest

plugins {
    id("compose.multiplatform")
    id("module.publication")
}

kotlin {
    sourceSets.commonMain.dependencies {
        implementation(projects.calfCore)
        implementation(libs.compose.foundation)
        implementation(libs.compose.material3)
        implementation(libs.kotlinx.coroutines.core)
    }

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlin.test)
        implementation(libs.kotlinx.coroutines.test)
    }

    // Shared library-level Material dialog scenarios, not sample application tests.
    sourceSets.named("materialTest").dependencies {
        implementation(libs.compose.ui.test)
    }

    sourceSets.named("androidHostTest").dependencies {
        implementation(libs.junit)
        implementation(libs.robolectric)
        implementation(libs.androidx.compose.ui.test.junit4)
        implementation(libs.androidx.compose.ui.test.manifest)
    }

    sourceSets.matching { it.name == "androidDeviceTest" }.configureEach {
        dependencies {
            implementation(libs.junit)
            implementation(libs.androidx.test.runner)
            implementation(libs.androidx.test.core)
            implementation(libs.androidx.test.junit)
            implementation(libs.androidx.compose.ui.test.junit4)
            implementation(libs.androidx.compose.ui.test.manifest)
        }
    }

    sourceSets.iosTest.dependencies {
        implementation(libs.compose.ui.test)
    }

    sourceSets.desktopTest.dependencies {
        implementation(libs.compose.ui.test)
        implementation(compose.desktop.currentOs)
    }

    sourceSets.androidMain.dependencies {
        implementation(libs.activity.compose)
        implementation(libs.kotlinx.coroutines.android)
    }

    sourceSets.desktopMain.dependencies {
        implementation(libs.kotlinx.coroutines.swing)
    }

    sourceSets.iosMain.dependencies {
        implementation(libs.kyant.backdrop)
        implementation(libs.kyant.shapes)
    }

    // Test-only application executable shares the real generated suites. Keep
    // default debugTest/public binaries unchanged; simctl spawn is not an app.
    targets.withType<KotlinNativeTarget>().matching { it.name == "iosSimulatorArm64" }.configureEach {
        binaries.test("application", listOf(DEBUG)) {
            freeCompilerArgs += listOf("-entry", "com.mohamedrejeb.calf.ui.internal.nativeApplicationMain")
        }
        val application = binaries.getTest("application", DEBUG)
        tasks.register<KotlinNativeHostTest>("iosSimulatorArm64ApplicationTest") {
            group = "verification"
            description = "Fresh library tests in an owned genuine UIKit simulator application, with KGP's real JUnit parser."
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
            outputs.doNotCacheIf("UIKit test application requires actual fresh execution") { true }
            onlyIf("UIKit simulator applications require macOS") { System.getProperty("os.name") == "Mac OS X" }
            doFirst {
                val identifier = providers.gradleProperty("nativecmpkitSimulatorDevice").orNull
                    ?: error("Select an actual booted simulator with nativecmpkitSimulatorDevice")
                check(Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(identifier)) {
                    "Use the task-recorded UDID, not a default device alias"
                }
                environment("NATIVECMPKIT_UIKIT_SIMULATOR", identifier)
                environment("NATIVECMPKIT_UIKIT_RESULT_ROOT",
                    providers.environmentVariable("NATIVECMPKIT_UIKIT_RESULT_ROOT").orNull
                        ?: "build/ci-verification/native-ui-application")
                logger.lifecycle("NATIVECMPKIT_TEST_SIMULATOR task=$path device=$identifier host=genuine-uikit-application")
            }
        }
    }
}
