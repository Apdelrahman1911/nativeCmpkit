// Modified for nativeCmpkit migration (2026-10-24); no publication is authorized by this change.
import org.gradle.api.publish.maven.tasks.PublishToMavenRepository
import org.gradle.api.publish.maven.tasks.PublishToMavenLocal
import java.io.File
import io.github.apdelrahman1911.nativecmpkit.buildlogic.PublicationVersionPolicy
import org.jetbrains.kotlin.gradle.targets.js.nodejs.NodeJsEnvSpec
import org.jetbrains.kotlin.gradle.targets.js.nodejs.NodeJsRootPlugin
import org.jetbrains.kotlin.gradle.targets.js.yarn.YarnLockMismatchReport
import org.jetbrains.kotlin.gradle.targets.js.yarn.YarnPlugin
import org.jetbrains.kotlin.gradle.targets.js.yarn.YarnRootEnvSpec
import org.jetbrains.kotlin.gradle.targets.wasm.nodejs.WasmNodeJsEnvSpec
import org.jetbrains.kotlin.gradle.targets.wasm.nodejs.WasmNodeJsPlugin
import org.jetbrains.kotlin.gradle.targets.wasm.yarn.WasmYarnPlugin
import org.jetbrains.kotlin.gradle.targets.wasm.yarn.WasmYarnRootEnvSpec
import org.jetbrains.kotlin.gradle.targets.web.yarn.BaseYarnRootEnvSpec

plugins {
    alias(libs.plugins.androidApplication).apply(false)
    alias(libs.plugins.androidKotlinMultiplatformLibrary).apply(false)
    alias(libs.plugins.kotlinMultiplatform).apply(false)
    alias(libs.plugins.kotlinJvm).apply(false)
    alias(libs.plugins.kotlinSerialization).apply(false)
    alias(libs.plugins.composeCompiler).apply(false)
    alias(libs.plugins.composeMultiplatform).apply(false)
    alias(libs.plugins.vanniktech.maven.publish).apply(false)
    // Resolve the existing convention classpath without applying its publisher.
    // The root and executable convention tests share one version policy.
    id("module.publication").apply(false)
}

// JS and Wasm have separate KGP environments and lock stores. These exact
// versions preserve the inspected KGP 2.4.20 defaults; pins/registry checksums
// are a TOFU bootstrap, not an independently reviewed supply-chain trust root.
fun BaseYarnRootEnvSpec.freezeNativeCmpkitDependencies() {
    version.set("1.22.22")
    ignoreScripts.set(true)
    yarnLockMismatchReport.set(YarnLockMismatchReport.FAIL)
    yarnLockAutoReplace.set(false)
    reportNewYarnLock.set(true)
}
plugins.withType<NodeJsRootPlugin> {
    extensions.configure<NodeJsEnvSpec> { version.set("24.16.0") }
}
plugins.withType<WasmNodeJsPlugin> {
    extensions.configure<WasmNodeJsEnvSpec> { version.set("24.16.0") }
}
plugins.withType<YarnPlugin> {
    extensions.configure<YarnRootEnvSpec> { freezeNativeCmpkitDependencies() }
}
plugins.withType<WasmYarnPlugin> {
    extensions.configure<WasmYarnRootEnvSpec> { freezeNativeCmpkitDependencies() }
}

val nativeCmpkitVersion = providers.gradleProperty("nativeCmpkit.version")
    .orElse("${libs.versions.nativecmpkit.get()}-SNAPSHOT")
PublicationVersionPolicy.validate(nativeCmpkitVersion.get())

val verificationMode = providers.gradleProperty("nativecmpkitVerification").orElse("false")
require(verificationMode.get() in setOf("true", "false")) { "nativecmpkitVerification must be true or false" }
val verificationRepository = layout.buildDirectory.dir("verification-repo")
val verificationTargets = providers.gradleProperty("nativecmpkitVerificationTargets").orElse("desktop")
require(verificationTargets.get() in setOf("desktop", "all")) { "Verification targets must be desktop or all" }
val stageVerificationPublications = tasks.register("stageVerificationPublications") {
    group = "verification"
    description = "Stage isolated candidate Maven publications only under build/verification-repo; never contact a remote repository."
    doFirst {
        check(verificationMode.get() == "true") { "Local staging requires -PnativecmpkitVerification=true" }
    }
}

allprojects {
    group = "io.github.apdelrahman1911.nativecmpkit"
    version = nativeCmpkitVersion.get()

    // A deliberate local opt-in is a safety interlock, not owner authorization.
    // Publishing still requires an explicit owner request and verified credentials/namespace.
    val allowPublishing = providers.gradleProperty("nativeCmpkit.allowPublishing")
    tasks.withType<PublishToMavenRepository>().configureEach {
        doFirst {
            val destination = repository.url
            val exactVerificationRepository = repository.name == "NativecmpkitVerification" &&
                destination.scheme == "file" && destination.authority.isNullOrEmpty() &&
                File(destination).canonicalFile == verificationRepository.get().asFile.canonicalFile
            if (exactVerificationRepository) {
                check(verificationMode.get() == "true") {
                    "Isolated local staging requires -PnativecmpkitVerification=true."
                }
            } else {
                check(verificationMode.get() != "true") {
                    "Local verification mode forbids ALL remote/arbitrary-repository publication, even with an allowPublishing flag."
                }
                check(allowPublishing.orNull == "true") {
                    "Publishing is disabled. Obtain owner authorization before using -PnativeCmpkit.allowPublishing=true."
                }
                check(providers.gradleProperty("nativecmpkitNativeMode").orNull == "release") {
                    "Remote publication requires explicit full-matrix native release mode and its verification gates."
                }
            }
        }
    }
    tasks.withType<PublishToMavenLocal>().configureEach {
        doFirst { error("Use isolated stageVerificationPublications instead of modifying the user's Maven-local repository.") }
    }
    // Vanniktech also exposes standalone Central deployment/release/drop tasks;
    // those may contact Central without executing PublishToMavenRepository.
    tasks.configureEach {
        if (name.contains("MavenCentral", ignoreCase = true)) {
            doFirst {
                check(verificationMode.get() != "true") {
                    "Maven Central operations are forbidden in local verification mode."
                }
                check(allowPublishing.orNull == "true") {
                    "Maven Central operations are disabled until owner-authorized publishing is explicitly enabled."
                }
            }
        }
    }
}

// KGP/AGP register publications late. Match actual publication tasks, not guessed
// artifact files; the partial desktop mode explicitly leaves other variants unstaged.
gradle.projectsEvaluated {
    val selected = if (verificationTargets.get() == "all")
        setOf("kotlinMultiplatform", "android", "desktop", "js", "wasmJs", "iosArm64", "iosSimulatorArm64")
    else setOf("kotlinMultiplatform", "desktop")
    stageVerificationPublications.configure {
        dependsOn(subprojects.flatMap { subproject ->
            subproject.tasks.withType<PublishToMavenRepository>().filter {
                it.repository.name == "NativecmpkitVerification" && it.publication.name in selected
            }
        })
    }
}
