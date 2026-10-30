// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
import org.jetbrains.kotlin.gradle.plugin.mpp.KotlinNativeTarget
import org.jetbrains.kotlin.gradle.plugin.mpp.NativeBuildType.DEBUG
import org.jetbrains.kotlin.gradle.targets.native.tasks.KotlinNativeHostTest
import java.time.Duration

plugins {
    id("compose.multiplatform")
    id("module.publication")
}

val javaFx = project.javaFxDependencies()

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

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlinx.coroutines.test)
    }

    targets.withType<KotlinNativeTarget>()
        .matching { it.konanTarget.family.isAppleFamily }
        .configureEach {
            compilations.getByName("main") {
                cinterops.create("nskeyvalueobserving") {
                    definitionFile = file("src/iosMain/cinterop/nskeyvalueobserving.def")
                }
            }
        }
    // Test-only genuine UIKit host: WebKit/interop lifecycle requires UIApplicationMain,
    // not a command-line KLIB/Skiko scene or the sample app. Public binaries stay unchanged.
    targets.withType<KotlinNativeTarget>().matching { it.name == "iosSimulatorArm64" }.configureEach {
        binaries.test("application", listOf(DEBUG)) {
            freeCompilerArgs += listOf("-entry", "com.mohamedrejeb.calf.ui.web.internal.nativeApplicationMain")
        }
        val application = binaries.getTest("application", DEBUG)
        tasks.register<KotlinNativeHostTest>("iosSimulatorArm64ApplicationTest") {
            group = "verification"
            description = "Actual library WKWebView tests in an owned UIKit application with KGP's real JUnit parser."
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
            outputs.doNotCacheIf("WebView application requires actual fresh native execution") { true }
            onlyIf("UIKit simulator applications require macOS") { System.getProperty("os.name") == "Mac OS X" }
            doFirst {
                val identifier = providers.gradleProperty("nativecmpkitSimulatorDevice").orNull
                    ?: error("Select an actual booted simulator with nativecmpkitSimulatorDevice")
                check(Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(identifier))
                environment("NATIVECMPKIT_UIKIT_SIMULATOR", identifier)
                environment("NATIVECMPKIT_UIKIT_RESULT_ROOT",
                    providers.environmentVariable("NATIVECMPKIT_UIKIT_RESULT_ROOT").orNull
                        ?: "build/ci-verification/native-webview-application")
                logger.lifecycle("NATIVECMPKIT_TEST_SIMULATOR task=$path device=$identifier host=genuine-uikit-application")
            }
        }
    }
    sourceSets.commonMain.dependencies {
        implementation(libs.compose.foundation)
        implementation(libs.compose.material3)
        implementation(libs.kotlinx.coroutines.core)
    }

    sourceSets.androidMain.dependencies {
        implementation(libs.activity.compose)
        implementation(libs.kotlinx.coroutines.android)
    }

    sourceSets.desktopMain.dependencies {
        // Do not encode the publisher's OS in the published POM/module metadata.
        // Applications must supply their explicitly selected JavaFX 21 runtime.
        javaFx.forEach { compileOnly(it) }
        implementation(libs.kotlinx.coroutines.swing)
    }

    sourceSets.desktopTest.dependencies {
        javaFx.forEach { implementation(it) }
        implementation(compose.desktop.currentOs)
    }

    sourceSets.webMain.dependencies {
        implementation(libs.kotlinx.browser)
    }
}
