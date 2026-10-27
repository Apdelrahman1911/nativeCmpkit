plugins {
    kotlin("multiplatform") version "2.4.20"
    kotlin("plugin.compose") version "2.4.20"
}
kotlin {
    iosSimulatorArm64()
    sourceSets.named("iosSimulatorArm64Main").dependencies {
        implementation("org.jetbrains.compose.ui:ui:1.12.0")
        implementation("org.jetbrains.compose.runtime:runtime:1.12.0")
    }
}
