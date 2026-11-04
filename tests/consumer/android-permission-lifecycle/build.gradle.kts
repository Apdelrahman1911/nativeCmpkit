// SPDX-License-Identifier: Apache-2.0
plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.composeMultiplatform)
}
android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.verification.permissionlifecycle"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    defaultConfig {
        applicationId = namespace
        minSdk = 35
        targetSdk = 37
        versionCode = 1
        versionName = "verification-only-api35-permission-lifecycle"
    }
    buildFeatures { compose = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
dependencies {
    implementation("verification.nativecmpkit:unpublished-permission-core")
    implementation("verification.nativecmpkit:unpublished-permission-location")
    implementation("verification.nativecmpkit:unpublished-permission-background-location")
    implementation("verification.nativecmpkit:unpublished-permission-camera")
    implementation("verification.nativecmpkit:unpublished-permission-notifications")
    implementation(libs.activity.compose)
    implementation(libs.compose.foundation)
}
