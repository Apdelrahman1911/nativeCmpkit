package com.mohamedrejeb.calf.navigation

import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.SaverScope
import androidx.compose.runtime.snapshots.Snapshot
import androidx.compose.runtime.snapshots.SnapshotStateList
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

class AdaptiveNavControllerTest {
    @Test
    fun duplicateRoutesAndPayloadsHaveIndependentEntryIdentity() {
        val controller = AdaptiveNavHostController()
        controller.navigate("same", mapOf("id" to NavArgument.Builder().setDefaultValue(1).build()))
        val first = assertNotNull(controller.currentBackStackEntry)
        controller.navigateWithValues("same", mapOf("id" to 2))
        val second = assertNotNull(controller.currentBackStackEntry)
        assertNotEquals(first.id, second.id)
        assertEquals(1, first.arguments["id"])
        assertEquals(2, second.arguments["id"])
        assertTrue(controller.canNavigateBack)
        assertTrue(controller.popBackStack())
        assertSame(first, controller.currentBackStackEntry)
        assertFalse(controller.popBackStack())
        assertFalse(controller.canNavigateBack)
    }

    @Test
    fun popAndRevisitWithinOneSnapshotCreatesFreshEntry() {
        val controller = AdaptiveNavHostController()
        controller.navigate("home")
        controller.navigate("detail")
        val original = controller.currentBackStackEntry!!.id
        Snapshot.withMutableSnapshot {
            assertTrue(controller.popBackStack())
            controller.navigate("detail")
        }
        assertNotEquals(original, controller.currentBackStackEntry!!.id)
        assertEquals(listOf("home", "detail"), controller.backStackEntries.map { it.route })
    }

    @Test
    fun callerMutationsCannotChangeCapturedPayloads() {
        val values = intArrayOf(1, 2)
        val map = mutableMapOf<String, Any?>("ids" to values)
        val controller = AdaptiveNavHostController()
        controller.navigateWithValues("detail", map)
        values[0] = 99
        map["extra"] = 5
        val entry = controller.currentBackStackEntry!!
        assertContentEquals(intArrayOf(1, 2), entry.arguments["ids"] as IntArray)
        assertFalse("extra" in entry.arguments)
        (entry.arguments["ids"] as IntArray)[0] = -1
        assertContentEquals(intArrayOf(1, 2), entry.arguments["ids"] as IntArray)
    }

    @Test
    fun graphMergesDefaultsAndRejectsMissingWrongTypeNullAndUnknownRoutes() {
        val controller = AdaptiveNavHostController()
        val destination = NavDestination("detail", mapOf(
            "id" to NavArgument.Builder().setType(AdaptiveNavType.IntType).build(),
            "title" to NavArgument.Builder().setDefaultValue("default").build(),
            "optional" to NavArgument.Builder().setType(AdaptiveNavType.StringType).setIsNullable(true).build(),
        )) {}
        val owner = Any()
        controller.attachGraph(owner)
        controller.updateGraph(owner, mapOf("detail" to destination))
        assertFailsWith<IllegalArgumentException> { controller.navigate("detail") }
        assertFailsWith<IllegalArgumentException> { controller.navigateWithValues("detail", mapOf("id" to "42")) }
        assertFailsWith<IllegalArgumentException> { controller.navigateWithValues("detail", mapOf("id" to null)) }
        assertFailsWith<IllegalArgumentException> { controller.navigate("unknown") }
        assertTrue(controller.backStackEntries.isEmpty())
        controller.navigateWithValues("detail", mapOf("id" to 42, "extra" to "value"))
        val resolved = destination.resolveArguments(controller.currentBackStackEntry!!)
        assertEquals(42, resolved.getValue("id").defaultValue)
        assertEquals("default", resolved.getValue("title").defaultValue)
        assertNull(resolved.getValue("optional").defaultValue)
        assertEquals("value", resolved.getValue("extra").defaultValue)
    }

    @Test
    fun unsupportedPayloadsAndSchemaOnlyNavigationArgumentsFailBeforeMutation() {
        val controller = AdaptiveNavHostController()
        assertFailsWith<IllegalArgumentException> { controller.navigateWithValues("detail", mapOf("object" to Any())) }
        // A prior JS rebuild emitted a lone-surrogate string literal as '?'.
        val malformedUtf16 = charArrayOf(0xD800.toChar()).concatToString()
        assertEquals(1, malformedUtf16.length)
        assertEquals(0xD800, malformedUtf16[0].code)
        assertFailsWith<IllegalArgumentException> { controller.navigateWithValues("detail", mapOf("string" to malformedUtf16)) }
        assertFailsWith<IllegalArgumentException> { controller.navigate(" ") }
        assertFailsWith<IllegalArgumentException> { controller.navigateWithValues("detail", mapOf(" " to 1)) }
        assertFailsWith<IllegalArgumentException> {
            controller.navigate("detail", mapOf("id" to NavArgument.Builder().setType(AdaptiveNavType.IntType).build()))
        }
        assertTrue(controller.backStackEntries.isEmpty())
    }

    @Test
    fun graphRejectsDuplicateAndBlankRoutesAndSnapshotsItsArgumentMap() {
        val graph = NavGraphBuilder()
        graph.composable("home") {}
        assertFailsWith<IllegalArgumentException> { graph.composable("home") {} }
        assertFailsWith<IllegalArgumentException> { graph.composable(" ") {} }
        val schema = mutableMapOf("value" to NavArgument.Builder().setDefaultValue(1).build())
        val destination = NavDestination("detail", schema) {}
        schema.clear()
        assertEquals(setOf("value"), destination.arguments.keys)
    }

    @Test
    fun aControllerHasOneGraphOwnerAndDetachesWithoutLosingStack() {
        val controller = AdaptiveNavHostController()
        val owner = Any()
        controller.attachGraph(owner)
        controller.updateGraph(owner, mapOf("home" to NavDestination("home") {}))
        controller.navigate("home")
        assertFailsWith<IllegalStateException> { controller.attachGraph(Any()) }
        controller.detachGraph(Any()) // Must not detach another host's graph.
        assertFailsWith<IllegalArgumentException> { controller.navigate("other") }
        controller.detachGraph(owner)
        controller.navigate("other")
        assertEquals(listOf("home", "other"), controller.backStackEntries.map { it.route })
    }

    @Test
    @Suppress("DEPRECATION")
    fun exactLegacyGetterTypeAndObservedChangesKeepOnlyCommonPrefix() {
        val controller = AdaptiveNavHostController()
        val legacy: SnapshotStateList<String> = controller.backStack // Compile fixture for getter type.
        controller.navigateWithValues("a", mapOf("keep" to true))
        controller.navigateWithValues("b", mapOf("drop" to true))
        controller.navigate("a")
        val original = controller.backStackEntries
        legacy.removeAt(1)
        val imported = controller.backStackEntries
        assertEquals(listOf("a", "a"), imported.map { it.route })
        assertEquals(original[0].id, imported[0].id)
        assertNotEquals(original[2].id, imported[1].id)
        assertTrue(imported[1].arguments.isEmpty())
        legacy.clear()
        assertTrue(controller.backStackEntries.isEmpty())
        legacy.add("a")
        assertNotEquals(original[0].id, controller.currentBackStackEntry!!.id)
    }

    @Test
    @Suppress("DEPRECATION")
    fun saverImportsLegacyEditsBeforePersistingSequence() {
        val controller = AdaptiveNavHostController()
        controller.backStack.addAll(listOf("a", "a"))
        val restored = assertNotNull(AdaptiveNavHostController.restoreState(controller.saveState()))
        assertEquals(controller.backStackEntries.map { it.id }, restored.backStackEntries.map { it.id })
        assertEquals(listOf("a", "a"), restored.backStackEntries.map { it.route })
    }

    @Test
    fun versionedSaverRoundTripsIdentityEveryPortablePayloadAndFurtherPops() {
        val controller = AdaptiveNavHostController()
        controller.navigate("a")
        val values = mapOf<String, Any?>(
            "int" to 1, "long" to 2L, "float" to 3f, "boolean" to true,
            "string" to "null/a?😀", "null" to null,
            "ints" to intArrayOf(1, 2), "longs" to longArrayOf(3, 4),
            "floats" to floatArrayOf(5f), "booleans" to booleanArrayOf(false),
            "strings" to arrayOf("", "null", "a/b"),
        )
        controller.navigateWithValues("a", values)
        val restored = assertNotNull(AdaptiveNavHostController.restoreState(controller.saveState()))
        assertEquals(controller.backStackEntries.map { it.id }, restored.backStackEntries.map { it.id })
        val restoredValues = restored.currentBackStackEntry!!.arguments
        values.forEach { (name, value) -> assertTrue(navValuesEqual(value, restoredValues[name]), name) }
        val oldIds = restored.backStackEntries.map { it.id }
        assertTrue(restored.popBackStack())
        assertEquals(oldIds.first(), restored.currentBackStackEntry!!.id)
        restored.navigate("a")
        assertTrue(restored.currentBackStackEntry!!.id !in oldIds)
    }

    @Test
    @Suppress("UNCHECKED_CAST")
    fun publicSaverUsesTheSameRoundTripAndAcceptsLegacyRouteArray() {
        val saver = AdaptiveNavHostController.Saver() as Saver<AdaptiveNavHostController, Any>
        val scope = object : SaverScope { override fun canBeSaved(value: Any): Boolean = true }
        val controller = AdaptiveNavHostController().apply { navigateWithValues("a", mapOf("id" to 1)) }
        val saved = with(saver) { scope.save(controller) }
        val restored = assertNotNull(saver.restore(assertNotNull(saved)))
        assertEquals(controller.currentBackStackEntry!!.id, restored.currentBackStackEntry!!.id)
        val legacy = assertNotNull(saver.restore(arrayOf("a", "b", "a")))
        assertEquals(listOf("a", "b", "a"), legacy.backStackEntries.map { it.route })
        assertEquals(3, legacy.backStackEntries.map { it.id }.toSet().size)
        assertTrue(legacy.backStackEntries.all { it.arguments.isEmpty() })
    }

    @Test
    fun invalidOrUnknownSavedFormatsAreRejectedWithoutPartialRestore() {
        assertNull(AdaptiveNavHostController.restoreState(listOf(99, "x", 0L, emptyList<Any>())))
        assertNull(AdaptiveNavHostController.restoreState(arrayOf<Any>("a", 1)))
        assertNull(AdaptiveNavHostController.restoreState(listOf(1, "x", -1L, emptyList<Any>())))
        assertNull(AdaptiveNavHostController.restoreState(listOf(1, "x", 1L, listOf(
            listOf("x:0", "a", emptyList<Any>()), listOf("x:0", "a", emptyList<Any>())))))
        assertNull(AdaptiveNavHostController.restoreState(listOf(1, "x", 1L, listOf(
            listOf("x:0", "a", listOf(listOf("value", "not-a-type", "x")))))))
        assertNull(AdaptiveNavHostController.restoreState(listOf(1, "x", 1L, listOf(
            listOf("x:2", "a", emptyList<Any>())))))
        assertNull(AdaptiveNavHostController.restoreState(listOf(1, "x", 1L, listOf(
            listOf("x:0", "a", listOf(listOf("value", "string", "%FF")))))))
        assertNull(AdaptiveNavHostController.restoreState(listOf(1, "x", 1L, listOf(
            listOf("x:0", "a", listOf(listOf("value", "", "text")))))))
    }

    @Test
    @Suppress("DEPRECATION")
    fun legacyErasedGetterRemainsCallableForCorrectlyTypedConsumers() {
        fun <T> legacyForward(bundle: AdaptiveBundle, key: String): T? = bundle[key]
        val bundle = AdaptiveBundle().apply { putInt("id", 42) }
        assertEquals(42, legacyForward<Int>(bundle, "id"))
        assertEquals(42, bundle.getOrNull<Int>("id"))
    }
}
