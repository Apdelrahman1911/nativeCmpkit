plugins { alias(libs.plugins.androidApplication) }

android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.verification.sharerecipient"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    defaultConfig {
        applicationId = "io.github.apdelrahman1911.nativecmpkit.verification.sharerecipient"
        minSdk = libs.versions.android.minSdk.get().toInt()
        targetSdk = libs.versions.android.compileSdk.get().toInt()
        versionCode = 1
        versionName = "verification-only"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
