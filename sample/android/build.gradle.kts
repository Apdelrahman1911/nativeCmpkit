// Modified for nativeCmpkit migration (2026-10-24): sample identity only.
plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.composeMultiplatform)
}

android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.sample"
    compileSdk = libs.versions.android.compileSdk.get().toInt()

    defaultConfig {
        minSdk = libs.versions.android.sample.minSdk.get().toInt()
        targetSdk = libs.versions.android.compileSdk.get().toInt()

        applicationId = "io.github.apdelrahman1911.nativecmpkit.sample"
        versionCode = 1
        versionName = "1.0"
    }

    buildFeatures {
        compose = true
    }
    compileOptions {
        // AGP's built-in Kotlin support derives the Kotlin jvmTarget from targetCompatibility.
        val javaVersion = JavaVersion.toVersion(libs.versions.java.get().toInt())
        sourceCompatibility = javaVersion
        targetCompatibility = javaVersion
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation(projects.sample.common)

    implementation(libs.activity.compose)
    implementation(libs.compose.tooling.preview)
    implementation(libs.appcompat)
    debugImplementation(libs.compose.tooling)
}
