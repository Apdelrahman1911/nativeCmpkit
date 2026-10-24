// Modified for nativeCmpkit migration (2026-10-24): retain the public generated resource package.
plugins {
    id("compose.multiplatform")
    id("module.publication")
}

compose.resources {
    packageOfResClass = "com.mohamedrejeb.calf.calf_cupertino_icons.generated.resources"
}

kotlin {
    sourceSets.commonMain.dependencies {
        implementation(libs.compose.foundation)
        implementation(libs.compose.material3)
        implementation(libs.compose.components.resources)
    }
}
