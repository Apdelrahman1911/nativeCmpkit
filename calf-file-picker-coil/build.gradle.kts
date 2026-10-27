// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
plugins {
    id("kotlin.multiplatform")
    id("module.publication")
}

kotlin {
    sourceSets.named("androidHostTest").dependencies {
        implementation(libs.junit)
        implementation(libs.robolectric)
    }

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlinx.coroutines.test)
    }

    sourceSets.commonMain.dependencies {
        implementation(libs.kotlinx.coroutines.core)
        api(projects.calfCore)
        api(projects.calfIo)
        implementation(libs.coil)
        implementation(libs.kotlinx.io.okio)
    }
}
