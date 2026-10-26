// Independent artifact consumer: deliberately no includeBuild, project dependency or mavenLocal.
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

rootProject.name = "nativecmpkit-packaged-consumer"

val candidateRepository = providers.gradleProperty("nativecmpkitRepository").orNull
    ?: error("Pass -PnativecmpkitRepository=/absolute/path/to/verification-repo")
require(java.io.File(candidateRepository).isAbsolute) { "nativecmpkitRepository must be absolute" }
val candidateDirectory = file(candidateRepository)
require(candidateDirectory.isAbsolute && candidateDirectory.isDirectory) {
    "nativecmpkitRepository must name an existing absolute local Maven repository directory"
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        // Missing candidate coordinates MUST fail, not resolve Calf/a previous package remotely.
        exclusiveContent {
            forRepository {
                maven {
                    name = "CandidateArtifactsOnly"
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
