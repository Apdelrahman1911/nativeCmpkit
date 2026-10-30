// Disposable source-only native integration host, never an uploaded package.
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
    versionCatalogs {
        create("libs") { from(files("../../../gradle/libs.versions.toml")) }
    }
}
rootProject.name = "nativecmpkit-owned-android-geo-probe"
includeBuild("../../..") {
    dependencySubstitution {
        substitute(module("verification.nativecmpkit:unpublished-geo")).using(project(":calf-geo"))
    }
}
