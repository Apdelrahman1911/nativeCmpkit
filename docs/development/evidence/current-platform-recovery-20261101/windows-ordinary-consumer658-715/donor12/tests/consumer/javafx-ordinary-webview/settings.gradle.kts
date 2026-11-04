// PRIVATE ordinary-Maven adoption fixture. No producer/composite/project fallback.
pluginManagement {
    repositories {
        mavenCentral()
        gradlePluginPortal()
    }
}
rootProject.name = "nativecmpkit-private-ordinary-javafx-webview-consumer"

val mode = providers.gradleProperty("nativecmpkitMetadataMode").get()
require(mode in setOf("module", "pom"))
val libraryRepository = java.io.File(providers.gradleProperty("nativecmpkitRepository").get())
val privateRepository = java.io.File(providers.gradleProperty("nativecmpkitPrivateJavafxRepository").get())
for (directory in listOf(libraryRepository, privateRepository)) {
    require(directory.isAbsolute && directory.isDirectory && !java.nio.file.Files.isSymbolicLink(directory.toPath()))
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        exclusiveContent {
            forRepository {
                maven {
                    name = "HeldNativeCmpKitLibraryOnly"
                    url = libraryRepository.toURI()
                    metadataSources {
                        if (mode == "module") gradleMetadata() else {
                            mavenPom()
                            ignoreGradleMetadataRedirection()
                        }
                    }
                }
            }
            filter { includeGroup("io.github.apdelrahman1911.nativecmpkit") }
        }
        exclusiveContent {
            forRepository {
                maven {
                    name = "UnpublishedPrivateCuredWebOnly"
                    url = privateRepository.toURI()
                    metadataSources {
                        if (mode == "module") gradleMetadata() else {
                            mavenPom()
                            ignoreGradleMetadataRedirection()
                        }
                    }
                }
            }
            filter { includeGroup("nativecmpkit.private.javafx") }
        }
        google()
        mavenCentral()
    }
}
