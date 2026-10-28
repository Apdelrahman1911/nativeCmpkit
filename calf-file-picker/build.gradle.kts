// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
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

    sourceSets.androidMain.dependencies {
        implementation(libs.activity.compose)
    }

    sourceSets.webMain.dependencies {
        // Public browser saver overloads accept W3C File and Blob, not private implementation types.
        api(libs.kotlinx.browser)
    }
}

// Shared host/release manifest pipeline; retained task names preserve source-build scripts.
configureNativeLibrary()
