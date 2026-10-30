// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
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
}

// Shared host/release manifest pipeline; retained task names preserve source-build scripts.
configureNativeLibrary()
