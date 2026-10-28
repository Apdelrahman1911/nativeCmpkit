// Explicitly PARTIAL standalone WebView consumer; no producer/composite/source fallback.
pluginManagement {
    repositories {
        mavenCentral()
        gradlePluginPortal()
    }
}

rootProject.name = "nativecmpkit-webview-desktop-consumer"

val candidateRepository = providers.gradleProperty("nativecmpkitRepository").orNull
    ?: error("Pass the exact absolute local -PnativecmpkitRepository")
val candidateDirectory = java.io.File(candidateRepository)
require(candidateDirectory.isAbsolute && candidateDirectory.isDirectory) {
    "nativecmpkitRepository must be an existing absolute local Maven repository directory"
}

val metadataMode = providers.gradleProperty("nativecmpkitMetadataMode").get()
require(metadataMode in setOf("module", "pom")) { "Select module or pom explicitly" }

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        exclusiveContent {
            forRepository {
                maven {
                    name = "PartialWebViewCandidateOnly"
                    url = candidateDirectory.toURI()
                    metadataSources {
                        if (metadataMode == "module") gradleMetadata() else {
                            mavenPom()
                            ignoreGradleMetadataRedirection()
                        }
                    }
                }
            }
            filter { includeGroup("io.github.apdelrahman1911.nativecmpkit") }
        }
        google()
        mavenCentral()
    }
}
