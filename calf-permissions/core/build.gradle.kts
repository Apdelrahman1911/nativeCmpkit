// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
plugins {
    id("compose.multiplatform")
    id("module.publication")
}

kotlin {
    sourceSets.named("androidHostTest").dependencies {
        implementation(libs.junit)
        implementation(libs.robolectric)
        // Real public Gallery aliases; this is test-only, not a core API dependency.
        implementation(projects.calfPermissions.calfPermissionsGallery)
    }

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlinx.coroutines.test)
    }

    sourceSets.commonMain.dependencies {
        implementation(libs.kotlinx.coroutines.core)
        api(libs.compose.foundation)
    }

    sourceSets.androidMain.dependencies {
        implementation(libs.activity.compose)
    }
}
