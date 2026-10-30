// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
plugins {
    id("compose.multiplatform")
    id("module.publication")
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

}
