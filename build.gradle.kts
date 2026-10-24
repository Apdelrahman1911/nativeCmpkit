// Modified for nativeCmpkit migration (2026-10-24); no publication is authorized by this change.
import org.gradle.api.publish.maven.tasks.PublishToMavenRepository

plugins {
    alias(libs.plugins.androidApplication).apply(false)
    alias(libs.plugins.androidKotlinMultiplatformLibrary).apply(false)
    alias(libs.plugins.kotlinMultiplatform).apply(false)
    alias(libs.plugins.kotlinJvm).apply(false)
    alias(libs.plugins.kotlinSerialization).apply(false)
    alias(libs.plugins.composeCompiler).apply(false)
    alias(libs.plugins.composeMultiplatform).apply(false)
    alias(libs.plugins.vanniktech.maven.publish).apply(false)
}

val nativeCmpkitVersion = providers.gradleProperty("nativeCmpkit.version")
    .orElse("${libs.versions.nativecmpkit.get()}-SNAPSHOT")

allprojects {
    group = "io.github.apdelrahman1911.nativecmpkit"
    version = nativeCmpkitVersion.get()

    // A deliberate local opt-in is a safety interlock, not owner authorization.
    // Publishing still requires an explicit owner request and verified credentials/namespace.
    val allowPublishing = providers.gradleProperty("nativeCmpkit.allowPublishing")
    tasks.withType<PublishToMavenRepository>().configureEach {
        doFirst {
            check(allowPublishing.orNull == "true") {
                "Publishing is disabled. Obtain owner authorization before using -PnativeCmpkit.allowPublishing=true."
            }
        }
    }
    // Vanniktech also exposes standalone Central deployment/release/drop tasks;
    // those may contact Central without executing PublishToMavenRepository.
    tasks.configureEach {
        if (name.contains("MavenCentral", ignoreCase = true)) {
            doFirst {
                check(allowPublishing.orNull == "true") {
                    "Maven Central operations are disabled until owner-authorized publishing is explicitly enabled."
                }
            }
        }
    }
}
