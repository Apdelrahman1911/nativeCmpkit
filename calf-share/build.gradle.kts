plugins {
    id("compose.multiplatform")
    id("module.publication")
}

kotlin {
    withBrowserTestBundling()

    sourceSets.commonMain.dependencies {
        api(projects.calfIo)

        implementation(libs.compose.foundation)
    }

    sourceSets.androidMain.dependencies {
        implementation(libs.activity.compose)
    }

    sourceSets.commonTest.dependencies {
        implementation(libs.kotlin.test)
    }

    sourceSets.webMain.dependencies {
        implementation(libs.kotlinx.browser)
    }
}

// Shared host/release manifest pipeline. No directory-content heuristic may
// bypass validation, and legacy unmanifested resource payloads are rejected.
configureNativeLibrary()
