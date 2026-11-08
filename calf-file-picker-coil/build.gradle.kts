plugins {
    id("kotlin.multiplatform")
    id("module.publication")
}

kotlin {
    sourceSets.commonMain.dependencies {
        api(projects.calfCore)
        api(projects.calfIo)
        implementation(libs.coil)
        // KmpFileFetcher.fetch() checks caller cancellation directly instead of relying on
        // Coil's transitive coroutine graph.
        implementation(libs.kotlinx.coroutines.core)
    }

    sourceSets.desktopTest.dependencies {
        implementation(libs.kotlin.test)
        implementation(libs.kotlinx.coroutines.core)
    }
}