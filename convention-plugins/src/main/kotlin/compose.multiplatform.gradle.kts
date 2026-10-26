// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
plugins {
    id("kotlin.multiplatform")
    id("org.jetbrains.compose")
    `kotlin-composecompiler`
}

configureBrowserTestBundles()
skipComposeUiTestCheckWithoutTestSources()
