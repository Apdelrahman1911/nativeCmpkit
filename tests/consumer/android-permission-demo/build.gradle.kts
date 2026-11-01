plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.composeMultiplatform)
}
android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.verification.permissiondemo"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    defaultConfig {
        applicationId = namespace
        minSdk = 33
        targetSdk = libs.versions.android.compileSdk.get().toInt()
        versionCode = 1
        versionName = "verification-only-approved-call-variant"
    }
    buildFeatures { compose = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
dependencies {
    implementation("verification.nativecmpkit:unpublished-permission-core")
    implementation("verification.nativecmpkit:unpublished-permission-gallery")
    implementation("verification.nativecmpkit:unpublished-permission-microphone")
    implementation("verification.nativecmpkit:unpublished-picker")
    implementation(libs.activity.compose)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.compose.foundation)
}
