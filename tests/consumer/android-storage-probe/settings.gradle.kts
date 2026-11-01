// Source-only native library test support; no publication or sample dependency.
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
    versionCatalogs { create("libs") { from(files("../../../gradle/libs.versions.toml")) } }
}
rootProject.name = "nativecmpkit-owned-android-storage-probe"
includeBuild("../../..") {
    dependencySubstitution {
        substitute(module("verification.nativecmpkit:unpublished-permissions-core"))
            .using(project(":calf-permissions:calf-permissions-core"))
    }
}
