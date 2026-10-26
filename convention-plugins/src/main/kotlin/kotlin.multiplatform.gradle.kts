// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
plugins {
    `kotlin-multiplatform`
    id("com.android.kotlin.multiplatform.library")
}

kotlin {
    applyHierarchyTemplate()
    applyTargets()
}

androidLibrarySetup()
setJvmTarget()
configureLibraryTests()
configureLibraryAbi()
