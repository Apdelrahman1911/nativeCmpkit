// Apache-2.0; disposable source consumer only, never a publishing project.
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
    versionCatalogs { create("libs") { from(files("../../../gradle/libs.versions.toml")) } }
}
rootProject.name = "nativecmpkit-owned-android-permission-lifecycle"
includeBuild("../../..") {
    dependencySubstitution {
        substitute(module("verification.nativecmpkit:unpublished-permission-core"))
            .using(project(":calf-permissions:calf-permissions-core"))
        substitute(module("verification.nativecmpkit:unpublished-permission-location"))
            .using(project(":calf-permissions:calf-permissions-location"))
        substitute(module("verification.nativecmpkit:unpublished-permission-background-location"))
            .using(project(":calf-permissions:calf-permissions-background-location"))
        substitute(module("verification.nativecmpkit:unpublished-permission-camera"))
            .using(project(":calf-permissions:calf-permissions-camera"))
        substitute(module("verification.nativecmpkit:unpublished-permission-notifications"))
            .using(project(":calf-permissions:calf-permissions-notifications"))
    }
}
