// Disposable source-only API33/34/35 test host; no repository publication.
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
    versionCatalogs { create("libs") { from(files("../../../gradle/libs.versions.toml")) } }
}
rootProject.name = "nativecmpkit-owned-android-permission-demo"
includeBuild("../../..") {
    dependencySubstitution {
        substitute(module("verification.nativecmpkit:unpublished-permission-core"))
            .using(project(":calf-permissions:calf-permissions-core"))
        substitute(module("verification.nativecmpkit:unpublished-permission-gallery"))
            .using(project(":calf-permissions:calf-permissions-gallery"))
        substitute(module("verification.nativecmpkit:unpublished-permission-microphone"))
            .using(project(":calf-permissions:calf-permissions-microphone"))
        substitute(module("verification.nativecmpkit:unpublished-picker"))
            .using(project(":calf-file-picker"))
    }
}
