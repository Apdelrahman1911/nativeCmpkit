plugins { alias(libs.plugins.androidApplication) }
android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    defaultConfig {
        applicationId = namespace
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
// Independent native receiver only. No publication, sample or packaged-library claim.
