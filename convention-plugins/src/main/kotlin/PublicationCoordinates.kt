import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import org.gradle.api.Project
import org.gradle.api.publish.tasks.GenerateModuleMetadata
import org.gradle.kotlin.dsl.withType

/**
 * Normalize KGP's fallback coordinates at the owning metadata-generation boundary.
 * A target with local cinterop has no MavenPublication on an incompatible host:
 * KGP 2.4.20 falls back to project.name even though its root metadata advertises
 * that target. Configuring the publication container cannot rename this fallback.
 * Use the public generation task, not private KGP state or fabricated publications.
 * Target availability, dependency selectors and compiler/native identities stay
 * unchanged. Signing/checksums/publication consume this task's final output.
 */
fun Project.configureIndependentPublicationCoordinates() {
    val coordinates = IndependentPublicationCoordinates(name, group.toString(), version.toString())

    tasks.withType<GenerateModuleMetadata>().configureEach {
        inputs.property("nativecmpkitIndependentCoordinateSchema", 1)
        inputs.property("nativecmpkitIndependentCoordinates", coordinates.renamedTargets)
        inputs.property("nativecmpkitIndependentCoordinateGroup", coordinates.group)
        inputs.property("nativecmpkitIndependentCoordinateVersion", coordinates.version)
        doLast {
            val output = outputFile.get().asFile
            val document = JsonSlurper().parse(output, "UTF-8") as MutableMap<*, *>
            // Do not rewrite already-correct host metadata or any artifacts,
            // dependencies, file display labels, hashes, attributes or variants.
            if (coordinates.normalize(document)) {
                output.writeText(JsonOutput.prettyPrint(JsonOutput.toJson(document)) + "\n", Charsets.UTF_8)
            }
        }
    }
}

/** Pure, finite schema; failures occur before the generation task writes its output. */
internal class IndependentPublicationCoordinates(oldBase: String, val group: String, val version: String) {
    private val base = "nativecmpkit-" + oldBase.removePrefix("calf-")
    val renamedTargets = listOf("-android", "-desktop", "-js", "-wasm-js", "-iosarm64", "-iossimulatorarm64")
        .associate { (oldBase + it) to (base + it) }
    private val independentTargets = renamedTargets.values.toSet()

    fun normalize(document: MutableMap<*, *>): Boolean {
        check(document["formatVersion"] == "1.1") { "Review the new Gradle metadata format before publishing" }
        val component = document["component"] as Map<*, *>
        check(component["group"] == group && component["version"] == version) {
            "Unexpected NativeCmpKit owning component coordinates"
        }
        check(component["module"] == base || component["module"] in independentTargets) {
            "Unexpected NativeCmpKit owning component identity"
        }
        var changed = false
        for (variant in document["variants"] as List<*>) {
            val redirect = (variant as Map<*, *>)["available-at"] as? MutableMap<*, *> ?: continue
            check(redirect["group"] == group && redirect["version"] == version) {
                "Foreign NativeCmpKit target redirect"
            }
            val module = redirect["module"] as String
            val independent = renamedTargets[module] ?: module
            check(independent in independentTargets) { "Unknown NativeCmpKit target redirect: $module" }
            check(redirect["url"] == "../../$module/$version/$module-$version.module") {
                "Unexpected NativeCmpKit target metadata URL"
            }
            if (independent != module) {
                @Suppress("UNCHECKED_CAST")
                val values = redirect as MutableMap<String, Any?>
                values["module"] = independent
                values["url"] = "../../$independent/$version/$independent-$version.module"
                changed = true
            }
        }
        return changed
    }
}
