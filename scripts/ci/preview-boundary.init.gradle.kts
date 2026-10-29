import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import org.gradle.api.publish.PublishingExtension
import org.gradle.api.publish.maven.MavenPublication

// Verification-only actual Gradle model checks. No publication/staging task is
// selected or invoked. Resolve the existing model, not a copied settings parser.
gradle.projectsEvaluated {
    rootProject.tasks.register("verifyPreviewBoundaryBatch") {
        group = "verification"
        description = "Verify actual independent publication identities and excluded prototype boundaries without publishing."
        doLast {
            val identity = JsonSlurper().parse(rootProject.file("docs/migration/identity.json")) as Map<*, *>
            val modules = identity["modules"] as List<*>
            val expected = modules.associate { value ->
                val module = value as Map<*, *>
                (module["gradle_project"] as String) to (module["new_artifact"] as String)
            }
            check(expected.size == 21 && modules.size == 21)
            val publishers = rootProject.allprojects.filter { project ->
                project.extensions.findByType(PublishingExtension::class.java)
                    ?.publications?.withType(MavenPublication::class.java)?.isNotEmpty() == true
            }
            check(publishers.map { it.path }.toSet() == expected.keys) {
                "Actual Maven publication projects differ from the explicit independent identity map"
            }
            val excluded = listOf("calf-maps", "calf-media", "calf-notifications")
                .map { rootProject.file(it).canonicalFile }
            val records = publishers.sortedBy { it.path }.map { project ->
                val kotlin = checkNotNull(project.extensions.findByName("kotlin"))
                val sourceSets = kotlin.javaClass.getMethod("getSourceSets").invoke(kotlin) as Iterable<*>
                val actualSourceDirectories = sourceSets.flatMap { sourceSet ->
                    val source = checkNotNull(sourceSet)
                    val files = source.javaClass.getMethod("getKotlin").invoke(source)
                    @Suppress("UNCHECKED_CAST")
                    (files.javaClass.getMethod("getSrcDirs").invoke(files) as Set<java.io.File>).toList()
                }
                check(actualSourceDirectories.none { directory ->
                    excluded.any { directory.canonicalFile.toPath().startsWith(it.toPath()) }
                }) { "An incomplete prototype is wired into a published source set" }
                val publications = project.extensions.getByType(PublishingExtension::class.java)
                    .publications.withType(MavenPublication::class.java).sortedBy { it.name }
                check(publications.any { it.name == "kotlinMultiplatform" && it.artifactId == expected[project.path] })
                check(publications.all { it.groupId == identity["maven_group"] && it.version == rootProject.version.toString() })
                mapOf("project" to project.path, "root_artifact" to expected[project.path],
                    "source_directories_checked" to actualSourceDirectories.size,
                    "publications" to publications.map { publication ->
                        mapOf("name" to publication.name, "group" to publication.groupId,
                            "artifact" to publication.artifactId, "version" to publication.version)
                    })
            }
            check(rootProject.findProject(":calf-maps") != null)
            check(rootProject.findProject(":calf-media") == null && rootProject.findProject(":calf-notifications") == null)
            check(rootProject.findProject(":calf-maps")?.extensions?.findByType(PublishingExtension::class.java) == null)
            val output = rootProject.layout.buildDirectory.file("ci-verification/preview-boundary-model.json").get().asFile
            output.parentFile.mkdirs()
            output.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(mapOf(
                "passed" to true, "configured_publishers" to records,
                "independent_maven_group" to identity["maven_group"], "version" to rootProject.version.toString(),
                "maps_included_but_unpublished" to true, "media_and_scheduler_excluded" to true,
                "experimental_source_reuse_rejected" to true,
                "scope" to "Actual configured Gradle publication/source-set model only; no built/published packages, native execution, full ABI/consumer or release certification",
            ))) + "\n")
            logger.lifecycle("NATIVECMPKIT_PREVIEW_BOUNDARY publishers=${records.size} prototypeApisExcluded=true noPublication=true")
        }
    }
}
