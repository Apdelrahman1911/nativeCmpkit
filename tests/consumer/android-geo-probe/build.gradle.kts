plugins { alias(libs.plugins.androidApplication) }

android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.verification.geoprobe"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    defaultConfig {
        applicationId = "io.github.apdelrahman1911.nativecmpkit.verification.geoprobe"
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

dependencies {
    implementation("verification.nativecmpkit:unpublished-geo")
    // A normal Compose consumer supplies the runtime exposed by State getters.
    implementation("org.jetbrains.compose.runtime:runtime:" + libs.versions.compose.asProvider().get())
}
