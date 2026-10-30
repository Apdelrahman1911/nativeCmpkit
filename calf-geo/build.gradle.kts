// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
plugins {
    id("compose.multiplatform")
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
        implementation(libs.compose.foundation)
    }
    sourceSets.androidMain.dependencies {
        implementation(libs.kotlinx.coroutines.android)
        // Retained public Android bind signatures expose FragmentManager/Lifecycle,
        // and LocationTracker extends LocationCallback with a LocationResult override.
        // Export the existing dependencies; do not require hidden consumer declarations.
        api(libs.appcompat)
        api(libs.lifecycle.extensions)
        api(libs.play.services.location)
    }
}
