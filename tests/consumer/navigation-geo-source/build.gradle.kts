// Source-only public common API consumer. No publication plugin or package staging.
import com.android.build.api.dsl.KotlinMultiplatformAndroidLibraryTarget
import org.gradle.api.plugins.ExtensionAware
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("multiplatform") version "2.4.20"
    id("org.jetbrains.compose") version "1.12.0"
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.20"
    id("com.android.kotlin.multiplatform.library") version "9.4.0" apply false
}

val selected = providers.gradleProperty("consumerTargets").orElse("desktop,android,web,ios")
    .get().split(',').toSet()
require(selected.isNotEmpty() && selected.all { it in setOf("desktop", "android", "web", "ios") })
if ("android" in selected) apply(plugin = "com.android.kotlin.multiplatform.library")

kotlin {
    jvmToolchain(17)
    if ("desktop" in selected) jvm("desktop") { compilerOptions.jvmTarget.set(JvmTarget.JVM_17) }
    if ("android" in selected) {
        (this as ExtensionAware).extensions.configure<KotlinMultiplatformAndroidLibraryTarget>("android") {
            namespace = "nativecmpkit.consumer.unpublished"
            compileSdk = 37
            minSdk = 23
            compilerOptions.jvmTarget.set(JvmTarget.JVM_17)
        }
    }
    if ("web" in selected) {
        js { browser() }
        @OptIn(org.jetbrains.kotlin.gradle.ExperimentalWasmDsl::class)
        wasmJs { browser() }
    }
    if ("ios" in selected) { iosArm64(); iosSimulatorArm64() }
    sourceSets.commonMain.dependencies {
        implementation("verification.nativecmpkit:unpublished-navigation")
        implementation("verification.nativecmpkit:unpublished-geo")
        // Normal Compose consumer dependencies; deliberately NO AndroidX navigation dependency.
        implementation(compose.runtime)
        implementation(compose.foundation)
    }
}

// Do not confuse UP-TO-DATE/disabled/NO-SOURCE with a successful new compilation.
val sourceCompileTasks = setOf("compileAndroidMain", "compileKotlinDesktop", "compileKotlinJs",
    "compileKotlinWasmJs", "compileKotlinIosArm64", "compileKotlinIosSimulatorArm64")
tasks.matching { it.name in sourceCompileTasks }.configureEach {
    outputs.upToDateWhen { false }
    outputs.doNotCacheIf("Public source consumer needs a fresh compiler invocation") { true }
    doFirst { logger.lifecycle("NATIVECMPKIT_SOURCE_CONSUMER_BEGIN task=$path") }
    doLast { logger.lifecycle("NATIVECMPKIT_SOURCE_CONSUMER_END task=$path") }
}
