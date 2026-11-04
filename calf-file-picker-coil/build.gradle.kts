// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
plugins {
    id("compose.multiplatform")
    id("module.publication")
}

// Coil/IO brings Skiko to browser tests. Use the owning Compose runtime-resource
// wiring rather than copying files/polyfilling Node or adding test-only DOM deps.
// No Coil source declares Composables; keep its production transformations off.
composeCompiler {
    targetKotlinPlatforms.set(emptySet())
}

kotlin {
    sourceSets.named("androidHostTest").dependencies {
        implementation(libs.junit)
        implementation(libs.robolectric)
    }

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlinx.coroutines.test)
    }

    sourceSets.desktopTest.dependencies {
        // The real default JVM Coil decoder needs the host Skiko native runtime.
        // Test-only: do not publish a host-classified runtime to library consumers.
        runtimeOnly(compose.desktop.currentOs)
    }

    sourceSets.commonMain.dependencies {
        implementation(libs.kotlinx.coroutines.core)
        api(projects.calfCore)
        api(projects.calfIo)
        implementation(libs.coil)
        implementation(libs.kotlinx.io.okio)
    }
}
