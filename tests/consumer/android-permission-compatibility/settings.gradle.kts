// SPDX-License-Identifier: Apache-2.0
// Unpublished public-library verification only, not a sample or publishing project.
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
    versionCatalogs { create("libs") { from(files("../../../gradle/libs.versions.toml")) } }
}
rootProject.name = "nativecmpkit-owned-permission-compatibility-verification"
include(":helper", ":reporter")
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
    }
}
