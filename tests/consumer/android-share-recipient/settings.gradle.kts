// Disposable URI-grant recipient, not a published package or sample application.
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
rootProject.name = "nativecmpkit-owned-android-share-recipient"
