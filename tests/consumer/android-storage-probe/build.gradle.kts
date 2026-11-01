// Disposable static target modes. MANAGE_EXTERNAL_STORAGE exists only in allFiles.
plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
}
android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.verification.storageprobe"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    defaultConfig {
        applicationId = "io.github.apdelrahman1911.nativecmpkit.verification.storageprobe"
        minSdk = libs.versions.android.minSdk.get().toInt()
        targetSdk = 35
        versionCode = 1
        versionName = "verification-only"
    }
    buildFeatures { buildConfig = true }
    flavorDimensions += "storageMode"
    productFlavors {
        for ((mode, sdk) in listOf("legacy28" to 28, "legacyTarget28" to 28,
                "legacy29" to 29, "scoped29" to 29, "modern" to 35, "allFiles" to 35)) {
            create(mode) {
                dimension = "storageMode"
                targetSdk = sdk
                buildConfigField("String", "STORAGE_MODE", "\"" + mode + "\"")
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
dependencies {
    implementation("verification.nativecmpkit:unpublished-permissions-core")
    implementation(libs.activity.compose)
    implementation(libs.compose.ui)
}
