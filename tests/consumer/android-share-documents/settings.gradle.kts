// Disposable third-UID document grant source, never a published package or sample.
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
rootProject.name = "nativecmpkit-owned-android-share-documents"
