// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
import org.jetbrains.kotlin.gradle.plugin.mpp.KotlinNativeTarget

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
