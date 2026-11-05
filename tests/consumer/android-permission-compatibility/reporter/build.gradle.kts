// SPDX-License-Identifier: Apache-2.0
plugins { alias(libs.plugins.androidApplication) }
android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.verification.permissioncompat.reporter"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    defaultConfig {
        applicationId = namespace
        minSdk = 23
        targetSdk = 37
        versionCode = 1
        versionName = "unpublished-permission-compatibility-reporter"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
dependencies {
    androidTestImplementation(libs.junit)
    androidTestImplementation(libs.kotlin.test)
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.androidx.test.core)
    androidTestImplementation(libs.androidx.test.junit)
}
