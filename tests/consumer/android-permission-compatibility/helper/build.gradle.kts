// SPDX-License-Identifier: Apache-2.0
plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.composeMultiplatform)
}
val finiteProfiles = mapOf(
    "android-permission-compat-api23-target23" to (23 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api23-target37" to (37 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api29-target28" to (28 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api29-target37" to (37 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api30-target29" to (29 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api30-target37" to (37 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api31-target30" to (30 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api31-target37" to (37 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api33-target32" to (32 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-compat-api33-target37" to (37 to setOf("fine", "coarse", "pair", "batch")),
    "android-permission-manifest-services-api35" to (37 to setOf("omitted", "batch")),
    "android-permission-camera-revoke-api35" to (37 to setOf("camera")),
    "android-permission-location-revoke-api35" to (37 to setOf("fine")),
    "android-permission-pending-disposal-api35" to (37 to setOf("camera")),
)
val selectedProfile = providers.gradleProperty("nativecmpkitPermissionCompatProfile").get()
val selected = requireNotNull(finiteProfiles[selectedProfile]) { "Only an exact finite permission profile may build" }
android {
    namespace = "io.github.apdelrahman1911.nativecmpkit.verification.permissioncompat"
    compileSdk = libs.versions.android.compileSdk.get().toInt()
    defaultConfig {
        applicationId = namespace
        minSdk = 23
        targetSdk = selected.first
        versionCode = 1
        versionName = "unpublished-compatibility-verification"
        buildConfigField("String", "VERIFICATION_PROFILE", "\"$selectedProfile\"")
    }
    buildFeatures { compose = true; buildConfig = true }
    flavorDimensions += "role"
    productFlavors {
        for (role in listOf("fine", "coarse", "pair", "batch", "omitted", "camera")) {
            create(role) {
                dimension = "role"
                applicationIdSuffix = ".$role"
                buildConfigField("String", "VERIFICATION_ROLE", "\"$role\"")
            }
        }
    }
    sourceSets {
        getByName("main").manifest.srcFile("src/main/AndroidManifest.xml")
        for (role in listOf("fine", "coarse", "pair", "batch", "omitted", "camera")) {
            getByName(role).manifest.srcFile("src/manifests/$role.xml")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
androidComponents {
    beforeVariants(selector().all()) { variant ->
        val role = variant.productFlavors.single().second
        variant.enable = role in selected.second && variant.buildType == "debug"
    }
}
dependencies {
    implementation("verification.nativecmpkit:unpublished-permission-core")
    implementation("verification.nativecmpkit:unpublished-permission-location")
    implementation("verification.nativecmpkit:unpublished-permission-background-location")
    implementation("verification.nativecmpkit:unpublished-permission-camera")
    implementation(libs.activity.compose)
    implementation(libs.compose.foundation)
}
