import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import org.junit.Assert.*
import org.junit.Test

/** Actual owning Kotlin normalizer; synthetic metadata, not consumer/native execution. */
class PublicationCoordinatesTest {
    private val group = "io.github.apdelrahman1911.nativecmpkit"
    private val version = "0.1.0-preview.1"
    private val schema = IndependentPublicationCoordinates("calf-webview", group, version)

    private fun redirect(module: String) = mutableMapOf<String, Any>(
        "group" to group, "module" to module, "version" to version,
        "url" to "../../$module/$version/$module-$version.module",
    )

    private fun document(vararg modules: String) = mutableMapOf<String, Any>(
        "formatVersion" to "1.1",
        "component" to mutableMapOf("group" to group, "module" to "nativecmpkit-webview", "version" to version),
        "createdBy" to mapOf("gradle" to mapOf("version" to "9.7.1")),
        "variants" to modules.map { mutableMapOf<String, Any>("name" to "$it-published", "available-at" to redirect(it)) },
    )

    @Test fun unavailableAppleTargetsReceiveExactIndependentCoordinates() {
        val actual = document("calf-webview-iosarm64", "calf-webview-iossimulatorarm64")
        assertTrue(schema.normalize(actual))
        val variants = actual["variants"] as List<*>
        for ((index, suffix) in listOf("iosarm64", "iossimulatorarm64").withIndex()) {
            assertEquals(redirect("nativecmpkit-webview-$suffix"), (variants[index] as Map<*, *>)["available-at"])
        }
        assertFalse(schema.normalize(actual))
    }

    @Test fun alreadyIndependentMetadataIsLeftUnchanged() {
        val actual = document("nativecmpkit-webview-desktop", "nativecmpkit-webview-iosarm64")
        val bytes = JsonOutput.toJson(actual)
        assertFalse(schema.normalize(actual))
        assertEquals(bytes, JsonOutput.toJson(actual))
    }

    @Test fun normalizationPreservesEveryNoncoordinateFieldAndTheOwningRoot() {
        val actual = document("calf-webview-iosarm64")
        @Suppress("UNCHECKED_CAST")
        val variants = actual["variants"] as MutableList<MutableMap<String, Any>>
        variants.add(mutableMapOf("name" to "desktopRuntimeElements-published",
            "attributes" to mapOf("org.gradle.category" to "library"),
            "dependencies" to listOf(mapOf("group" to "org.jetbrains.compose.ui", "module" to "ui", "version" to mapOf("requires" to "1.12.0"))),
            "files" to listOf(mapOf("name" to "calf-webview-desktop-$version.jar", "url" to "nativecmpkit-webview-desktop-$version.jar", "sha256" to "a".repeat(64)))))
        val expected = JsonSlurper().parseText(JsonOutput.toJson(actual)) as MutableMap<*, *>
        @Suppress("UNCHECKED_CAST")
        val expectedFirst = (expected["variants"] as List<*>).first() as MutableMap<String, Any>
        expectedFirst["available-at"] = redirect("nativecmpkit-webview-iosarm64")
        assertTrue(schema.normalize(actual))
        assertEquals(expected, actual)
    }

    @Test fun foreignUnknownVersionAndUrlAliasesFailClosed() {
        for ((key, bad) in listOf("group" to "com.mohamedrejeb.calf", "version" to "0.1.0-preview.2",
                "module" to "calf-webview-iosx64", "url" to "../../foreign/metadata.module")) {
            val actual = document("calf-webview-iosarm64")
            @Suppress("UNCHECKED_CAST")
            val target = ((actual["variants"] as List<*>).first() as Map<*, *>)["available-at"] as MutableMap<String, Any>
            target[key] = bad
            assertThrows("$key must reject rather than guess", IllegalStateException::class.java) { schema.normalize(actual) }
        }
    }

    @Test fun changedFormatOrOwningComponentRequiresExplicitReview() {
        val format = document("calf-webview-iosarm64")
        format["formatVersion"] = "99.0"
        assertThrows(IllegalStateException::class.java) { schema.normalize(format) }
        val root = document("calf-webview-iosarm64")
        @Suppress("UNCHECKED_CAST")
        val component = root["component"] as MutableMap<String, Any>
        component["module"] = "calf-webview"
        assertThrows(IllegalStateException::class.java) { schema.normalize(root) }
    }

    @Test fun allSixDeclaredTargetNamesHaveAnExactMapping() {
        val suffixes = listOf("android", "desktop", "js", "wasm-js", "iosarm64", "iossimulatorarm64")
        assertEquals(suffixes.size, schema.renamedTargets.size)
        val actual = document(*suffixes.map { "calf-webview-$it" }.toTypedArray())
        assertTrue(schema.normalize(actual))
        assertEquals(suffixes.map { redirect("nativecmpkit-webview-$it") },
            (actual["variants"] as List<*>).map { (it as Map<*, *>)["available-at"] })
    }
}
