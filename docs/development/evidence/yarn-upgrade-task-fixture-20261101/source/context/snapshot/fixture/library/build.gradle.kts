// Actual KGP JS/Wasm targets, applied LATE in a child; no application/sample or library test claims.
plugins { alias(libs.plugins.kotlinMultiplatform) }
kotlin {
    js { browser() }
    @OptIn(org.jetbrains.kotlin.gradle.ExperimentalWasmDsl::class)
    wasmJs { browser() }
}
