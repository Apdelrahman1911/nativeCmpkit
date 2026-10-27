// Explicitly PARTIAL standalone consumer; no producer/composite/source fallback.
pluginManagement {
    repositories {
        mavenCentral()
        gradlePluginPortal()
    }
}

rootProject.name = "nativecmpkit-core-io-desktop-consumer"

val candidateRepository = providers.gradleProperty("nativecmpkitRepository").orNull
    ?: error("Pass the exact absolute local -PnativecmpkitRepository")
val candidateDirectory = java.io.File(candidateRepository)
require(candidateDirectory.isAbsolute && candidateDirectory.isDirectory) {
    "nativecmpkitRepository must be an existing absolute local Maven repository directory"
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        exclusiveContent {
            forRepository {
                maven {
                    name = "PartialCoreIoCandidateOnly"
                    url = candidateDirectory.toURI()
                    metadataSources {
                        gradleMetadata()
                        mavenPom()
                    }
                }
            }
            filter { includeGroup("io.github.apdelrahman1911.nativecmpkit") }
        }
        google()
        mavenCentral()
    }
}
