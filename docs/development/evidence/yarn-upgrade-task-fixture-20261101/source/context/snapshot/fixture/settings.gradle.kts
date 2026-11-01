// PRIVATE exact owning-helper fixture. Relative paths resolve only inside this frozen slice.
pluginManagement {
    includeBuild("../convention-plugins")
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositories { google(); mavenCentral() }
    versionCatalogs { create("libs") { from(files("../gradle/libs.versions.toml")) } }
}
rootProject.name = "nativecmpkit-real-kgp-upgrade-denial-fixture"
include(":library")
