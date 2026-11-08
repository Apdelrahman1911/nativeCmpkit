plugins {
    id("kotlin.multiplatform")
    id("module.publication")
}

kotlin {
    sourceSets.commonMain.dependencies {
        api(projects.calfCore)
        api(projects.calfIo)
        implementation(libs.coil)
    }

    sourceSets.desktopTest.dependencies {
        implementation(libs.kotlin.test)
        implementation(libs.kotlinx.coroutines.core)
    }
}