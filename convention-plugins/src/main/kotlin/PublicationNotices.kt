import groovy.json.JsonSlurper
import java.security.MessageDigest
import org.gradle.api.Project
import org.gradle.api.file.DuplicatesStrategy
import org.gradle.api.publish.PublishingExtension
import org.gradle.api.publish.maven.MavenPublication
import org.gradle.api.publish.maven.tasks.PublishToMavenRepository
import org.gradle.api.tasks.Sync
import org.gradle.api.tasks.bundling.Jar
import org.gradle.api.tasks.bundling.Zip
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.register
import org.gradle.kotlin.dsl.withType

/** Accompany every published coordinate, including KLIBs, without mutating compiler output. */
fun Project.configurePublicationNotices() {
    val moduleName = name
    val root = rootProject.layout.projectDirectory
    val isNative = moduleName in setOf("calf-file-picker", "calf-share")
    val nativeNotices = rootProject.layout.buildDirectory.dir("native-notices/$moduleName")
    val canonical = layout.buildDirectory.dir("publication-notices/canonical")
    val embedded = layout.buildDirectory.dir("publication-notices/embedded")
    val rootNotices = listOf("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md").map(root::file)

    val prepareCanonical = tasks.register<Sync>("preparePublicationNotices") {
        group = "verification"
        description = "Prepare complete accompanying license/attribution materials, never alter compiled KLIBs."
        into(canonical)
        from(rootNotices) { into("META-INF/nativecmpkit") }
        from(root.dir("licenses")) { into("META-INF/nativecmpkit/licenses") }
        if (isNative) from(nativeNotices)
        duplicatesStrategy = DuplicatesStrategy.FAIL
    }
    val prepareEmbedded = tasks.register<Sync>("prepareEmbeddedPublicationNotices") {
        group = "verification"
        description = "Use module-scoped JVM/AAR notice paths to avoid cross-library packaging collisions."
        into(embedded)
        from(rootNotices) { into("META-INF/nativecmpkit/$moduleName") }
        from(root.dir("licenses")) { into("META-INF/nativecmpkit/$moduleName/licenses") }
        if (isNative) from(nativeNotices)
        duplicatesStrategy = DuplicatesStrategy.FAIL
    }
    val noticeZip = tasks.register<Zip>("publicationNoticesZip") {
        group = "verification"
        archiveBaseName.set("nativecmpkit-" + moduleName.removePrefix("calf-"))
        archiveVersion.set(project.version.toString())
        archiveClassifier.set("notices")
        destinationDirectory.set(layout.buildDirectory.dir("publication-notices/archives"))
        from(prepareCanonical)
        isPreserveFileTimestamps = false
        isReproducibleFileOrder = true
        duplicatesStrategy = DuplicatesStrategy.FAIL
    }

    tasks.withType<Jar>().configureEach { from(prepareEmbedded) }
    // AGP 9.4's public BundleAar task extends Zip. Keep the match narrow so
    // independent resource/source archives are not silently rewritten.
    tasks.withType<Zip>().matching { it.name.endsWith("Aar") }.configureEach { from(prepareEmbedded) }
    extensions.configure<PublishingExtension> {
        publications.withType<MavenPublication>().configureEach {
            artifact(noticeZip) { classifier = "notices"; extension = "zip" }
        }
    }

    val verifyNotices = tasks.register("verifyPublicationNotices") {
        group = "verification"
        description = "Reject candidate publications with absent/stale/incomplete native dependency notice collection."
        dependsOn(noticeZip)
        doLast {
            rootNotices.forEach { check(it.asFile.isFile) { "A required project notice is missing" } }
            if (isNative) {
                val report = nativeNotices.get().file(
                    "META-INF/nativecmpkit/native-dependencies/$moduleName/licenses-report.json"
                ).asFile
                check(report.isFile) {
                    "Collect checksum-verified native crate license materials before staging/publication; see tests/consumer/collect_native_licenses.py."
                }
                val data = JsonSlurper().parse(report) as Map<*, *>
                check(data["module"] == moduleName && data["complete_material_collection"] == true &&
                    (data["gaps"] as? List<*>)?.isEmpty() == true) {
                    "Native license materials are incomplete or belong to a different module; no publication permitted."
                }
                fun sha256(relative: String): String = MessageDigest.getInstance("SHA-256")
                    .digest(layout.projectDirectory.file(relative).asFile.readBytes())
                    .joinToString("") { "%02x".format(it) }
                check(data["cargo_toml_sha256"] == sha256("native/Cargo.toml") &&
                    data["cargo_lock_sha256"] == sha256("native/Cargo.lock")) {
                    "Native notice materials were collected for different manifest/lock inputs."
                }
                // Complete material collection is NOT legal clearance: the separate
                // consumer/release review checks texts, obligations and actual archives.
            }
        }
    }
    tasks.withType<PublishToMavenRepository>().configureEach {
        dependsOn(verifyNotices)
        if (isNative && name.startsWith("publishDesktopPublication")) dependsOn("verifyNativeResources")
    }
}
