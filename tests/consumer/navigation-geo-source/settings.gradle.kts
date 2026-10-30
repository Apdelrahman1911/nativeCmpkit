// Source integration for two intentionally unpublished modules, NOT Maven evidence.
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "nativecmpkit-unpublished-navigation-geo-consumer"

// Fixed explicit substitutions: no published candidate, mavenLocal or upstream fallback.
includeBuild("../../..") {
    dependencySubstitution {
        substitute(module("verification.nativecmpkit:unpublished-navigation"))
            .using(project(":calf-navigation"))
        substitute(module("verification.nativecmpkit:unpublished-geo"))
            .using(project(":calf-geo"))
    }
}
