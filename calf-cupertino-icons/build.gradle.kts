// Modified for nativeCmpkit migration (2026-10-24): retain the public generated resource package.
import java.security.MessageDigest

plugins {
    id("compose.multiplatform")
    id("module.publication")
}

compose.resources {
    packageOfResClass = "com.mohamedrejeb.calf.calf_cupertino_icons.generated.resources"
}

// Compose resource ZIPs are distributed separately from KLIBs; JVM META-INF
// notices alone do not accompany a copied Apple/browser font resource bundle.
val verifyCupertinoResourceNotices = tasks.register("verifyCupertinoResourceNotices") {
    group = "verification"
    description = "Keep the unchanged Cupertino font and its full pinned MIT notice/provenance together."
    val font = layout.projectDirectory.file("src/commonMain/composeResources/font/sf_symbols.ttf")
    val canonicalLicense = rootProject.layout.projectDirectory.file("licenses/cupertino-icons-MIT.txt")
    val canonicalProvenance = rootProject.layout.projectDirectory.file("licenses/cupertino-icons-provenance.json")
    val resourceLicense = layout.projectDirectory.file("src/commonMain/composeResources/files/nativecmpkit/cupertino-icons-MIT.txt")
    val resourceProvenance = layout.projectDirectory.file("src/commonMain/composeResources/files/nativecmpkit/cupertino-icons-provenance.json")
    inputs.files(font, canonicalLicense, canonicalProvenance, resourceLicense, resourceProvenance)
    doLast {
        fun sha256(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }
        check(sha256(font.asFile.readBytes()) == "67c44fe9183b002e79dde7f6977e2988661c9a3e4a3c5fce968787efdbed823c") {
            "The retained public font resource differs from its pinned Flutter source."
        }
        val license = canonicalLicense.asFile.readBytes()
        check(sha256(license) == "310d6ab6483280280c9db122bded0a63c09558bc5743720f61dbcbb494db370a" &&
            resourceLicense.asFile.readBytes().contentEquals(license)) {
            "Compose resource distributions require the complete, unchanged pinned Cupertino MIT notice."
        }
        check(resourceProvenance.asFile.readBytes().contentEquals(canonicalProvenance.asFile.readBytes())) {
            "The accompanying font provenance must equal the canonical reviewed record."
        }
    }
}

tasks.matching {
    it.name.startsWith("prepareComposeResourcesTaskFor") ||
        it.name == "check" || it.name == "verifyPublicationNotices"
}.configureEach {
    dependsOn(verifyCupertinoResourceNotices)
}

kotlin {
    sourceSets.desktopTest.dependencies {
        implementation(libs.compose.ui.test)
        implementation(compose.desktop.currentOs)
    }

    sourceSets.commonMain.dependencies {
        implementation(libs.compose.foundation)
        implementation(libs.compose.material3)
        implementation(libs.compose.components.resources)
    }
}
