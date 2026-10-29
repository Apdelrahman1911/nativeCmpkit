// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
plugins {
    id("compose.multiplatform")
    id("desktop.javafx")
}

kotlin {
    sourceSets.commonTest.dependencies {
        implementation(libs.kotlinx.coroutines.test)
    }

    // Actual sample coroutine-owner disposal, not a substitute for library integration suites.
    sourceSets.desktopTest.dependencies {
        implementation(libs.compose.ui.test)
    }

    listOf(
        iosArm64(),
        iosSimulatorArm64(),
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "Common"
            isStatic = true

            // IMPORTANT: Exporting calf-ui is required for some functionalities to work
            export(projects.calfUi)
        }
    }

    sourceSets.commonMain.dependencies {
        api(libs.compose.foundation)
        api(libs.compose.material3)
        implementation(libs.compose.material.icons.extended)

        implementation(libs.kotlinx.datetime)

        // Calf
        api(projects.calfUi)
        implementation(projects.calfFilePicker)
        implementation(projects.calfFilePickerCoil)
        implementation(projects.calfPermissions)
        implementation(projects.calfWebview)
        implementation(projects.calfNavigation)
        implementation(projects.calfCameraPicker)
        implementation(projects.calfShare)
        implementation(projects.calfCupertinoIcons)

        // Coil
        implementation(libs.coil.compose)
        implementation(libs.coil.network.ktor)

        // Ktor
        implementation(libs.ktor.client.core)
    }

    sourceSets.androidMain.dependencies {
        implementation(libs.kotlinx.coroutines.android)
        implementation(libs.ktor.client.okhttp)
    }

    sourceSets.desktopMain.dependencies {
        implementation(compose.desktop.currentOs)

        implementation(libs.kotlinx.coroutines.swing)
        implementation(libs.ktor.client.okhttp)
    }

    sourceSets.iosMain.dependencies {
        implementation(libs.ktor.client.darwin)
    }

    sourceSets.jsMain.dependencies {
        implementation(libs.ktor.client.js)
    }

    sourceSets.wasmJsMain.dependencies {
        implementation(libs.ktor.client.wasm)
    }
}
