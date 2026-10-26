// Modified for nativeCmpkit migration (2026-10-24); upstream authorship is retained below.
plugins {
    id("com.vanniktech.maven.publish")
}

val localVerification = providers.gradleProperty("nativecmpkitVerification").orNull == "true"

publishing {
    repositories {
        maven {
            name = "NativecmpkitVerification"
            url = uri(rootProject.layout.buildDirectory.dir("verification-repo"))
        }
    }
}

mavenPublishing {
    publishToMavenCentral()
    // The root task guard permits unsigned artifacts ONLY in this exact, isolated
    // file repository mode; remote/Central tasks reject the mode outright.
    if (!localVerification) signAllPublications()

    coordinates(group.toString(), "nativecmpkit-" + project.name.removePrefix("calf-"), version.toString())

    pom {
        name.set("nativeCmpkit - " + project.name.removePrefix("calf-"))
        description.set("Independent Kotlin Multiplatform native component toolkit, derived from Calf under Apache-2.0.")
        url.set("https://github.com/Apdelrahman1911/nativeCmpkit")

        licenses {
            license {
                name.set("Apache-2.0")
                url.set("https://opensource.org/licenses/Apache-2.0")
            }
        }
        developers {
            developer {
                id.set("Apdelrahman1911")
                name.set("abdelrahman fahmy")
                url.set("https://github.com/Apdelrahman1911")
            }
            developer {
                id.set("MohamedRejeb")
                name.set("Mohamed Rejeb")
                email.set("mohamedrejeb445@gmail.com")
            }
        }
        issueManagement {
            system.set("Github")
            url.set("https://github.com/Apdelrahman1911/nativeCmpkit/issues")
        }
        scm {
            connection.set("scm:git:https://github.com/Apdelrahman1911/nativeCmpkit.git")
            developerConnection.set("scm:git:ssh://git@github.com/Apdelrahman1911/nativeCmpkit.git")
            url.set("https://github.com/Apdelrahman1911/nativeCmpkit")
        }
    }
}

configurePublicationNotices()
