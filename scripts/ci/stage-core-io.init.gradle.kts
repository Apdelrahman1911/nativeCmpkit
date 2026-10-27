// Explicit partial local staging only; the producer's full staging task is unchanged.
import org.gradle.api.publish.maven.tasks.PublishToMavenRepository
import org.gradle.kotlin.dsl.withType

// Init scripts are inherited by convention/plugin included builds. The caller
// supplies the exact producer directory; never select a build by name alone or
// look up the library projects inside an unrelated included-build root.
val stagingRootFile = java.io.File(checkNotNull(System.getProperty("nativecmpkit.partialStagingRoot")) {
    "Core/IO staging requires an explicit producer-root binding"
})
check(stagingRootFile.isAbsolute && stagingRootFile.isDirectory) {
    "The partial staging producer root must be an existing absolute directory"
}
val stagingRoot = stagingRootFile.canonicalFile

gradle.projectsEvaluated {
    val root = rootProject
    if (root.projectDir.canonicalFile != stagingRoot) return@projectsEvaluated
    check(root.name == "nativeCmpkit") { "Unexpected selected producer build" }
    check(root.providers.gradleProperty("nativecmpkitVerification").orNull == "true") {
        "Core/IO staging requires explicit isolated local verification mode"
    }
    check(root.providers.gradleProperty("nativecmpkitVerificationTargets").orNull == "desktop") {
        "This is a partial metadata+desktop diagnostic, not the full target matrix"
    }
    check(root.providers.gradleProperty("nativeCmpkit.version").orNull == "0.1.0-preview.1") {
        "The contained fixture accepts only the exact unpublished draft version"
    }
    val modules = listOf(root.project(":calf-core"), root.project(":calf-io"))
    val repository = root.layout.buildDirectory.dir("verification-repo").get().asFile.canonicalFile
    val selected = modules.flatMap { module ->
        val publications = module.tasks.withType<PublishToMavenRepository>().filter {
            it.repository.name == "NativecmpkitVerification" &&
                it.publication.name in setOf("kotlinMultiplatform", "desktop")
        }
        check(publications.size == 2) { "Both real Core/IO metadata and desktop publication tasks are required" }
        publications.forEach { task ->
            val url = task.repository.url
            check(url.scheme == "file" && url.authority.isNullOrEmpty() && java.io.File(url).canonicalFile == repository) {
                "Partial staging must use only the producer's exact isolated file repository"
            }
            check(task.publication.groupId == "io.github.apdelrahman1911.nativecmpkit" &&
                task.publication.version == "0.1.0-preview.1") { "Unexpected partial publication identity" }
            val artifactRoot = "nativecmpkit-" + module.name.removePrefix("calf-")
            val expectedArtifact = artifactRoot + if (task.publication.name == "desktop") "-desktop" else ""
            check(task.publication.artifactId == expectedArtifact) { "Unexpected partial publication artifact" }
            task.doLast {
                println("NATIVECMPKIT_PARTIAL_STAGE task=${task.path} group=${task.publication.groupId} version=${task.publication.version}")
            }
        }
        publications
    }
    check(selected.size == 4)
    root.tasks.register("stageCoreIoVerificationPublications") {
        group = "verification"
        description = "PARTIAL: stage only Core/IO metadata+desktop into the isolated local verification repository"
        dependsOn(selected)
        doLast { println("PARTIAL Core/IO local staging: four actual publication tasks; no release or full-matrix certification") }
    }
}
