package com.mohamedrejeb.calf.navigation

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNotSame
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

class CheckedNavArraysTest {
    @Test
    fun typedAndEmptyArrayGettersPreserveBundleReferenceOwnership() {
        val bundle = AdaptiveBundle()
        val strings = arrayOf("a", "b")
        val empty = emptyArray<String>()
        val sequences = arrayOf<CharSequence?>(StringBuilder("c"), null)
        bundle.putStringArray("strings", strings)
        bundle.putObject("empty", empty)
        bundle.putObject("sequences", sequences)
        assertSame(strings, bundle.getStringArray("strings"))
        assertSame(empty, bundle.getStringArray("empty"))
        assertSame(sequences, bundle.getCharSequenceArray("sequences"))
        assertNull(bundle.getStringArray("sequences"))
        assertNull(bundle.getStringArray("missing"))
        strings[0] = "changed"
        assertEquals("changed", bundle.getStringArray("strings")!![0])
        bundle.getStringArray("strings")!![1] = "through getter"
        assertEquals("through getter", strings[1])
    }

    @Test
    fun mixedAndNullStringElementsAreRejectedBeforeTypedAccess() {
        val bundle = AdaptiveBundle()
        val mixed = arrayOf<Any?>("text", 7)
        val nullableStrings = arrayOf<String?>("text", null)
        bundle.mMap["mixed"] = mixed
        bundle.putObject("nullable", nullableStrings)
        assertNull(bundle.getStringArray("mixed"))
        assertNull(bundle.getCharSequenceArray("mixed"))
        assertNull(bundle.getStringArray("nullable"))
        assertSame<Any?>(nullableStrings, bundle.getCharSequenceArray("nullable"))
        assertFailsWith<IllegalArgumentException> { bundle.putObject("invalid", mixed) }
        assertFalse(bundle.containsKey("invalid"))
        for (invalid in listOf(mixed, nullableStrings)) {
            assertFailsWith<IllegalArgumentException> { AdaptiveNavType.inferFromValueType(invalid) }
            assertFailsWith<IllegalArgumentException> {
                NavArgument.Builder().setType(AdaptiveNavType.StringArrayType).setDefaultValue(invalid).build()
            }
        }
        val argument = NavArgument.Builder().setType(AdaptiveNavType.StringArrayType).build()
        assertFalse(argument.verify("mixed", bundle))
        assertFalse(argument.verify("nullable", bundle))
    }

    @Test
    fun checkedGettersRevalidateAfterCallerMutatesNullableArray() {
        val source = arrayOf<String?>("text")
        val bundle = AdaptiveBundle().apply { putObject("value", source) }
        assertContentEquals(arrayOf("text"), bundle.getStringArray("value"))
        source[0] = null
        assertNull(bundle.getStringArray("value"))
        assertSame<Any?>(source, bundle.getCharSequenceArray("value"))
    }

    @Test
    fun stringArrayDefaultsRemainDefensiveIncludingEmptyArrays() {
        for (source in listOf(emptyArray<String>(), arrayOf("a", "b"))) {
            val original = source.copyOf()
            val argument = NavArgument.Builder().setDefaultValue(source).build()
            assertSame<AdaptiveNavType<*>>(AdaptiveNavType.StringArrayType, argument.type)
            if (source.isNotEmpty()) source[0] = "caller mutation"
            val firstRead = assertIs<Array<String>>(argument.defaultValue)
            assertNotSame(source, firstRead)
            assertContentEquals(original, firstRead)
            if (firstRead.isNotEmpty()) firstRead[0] = "getter mutation"
            val bundle = AdaptiveBundle()
            argument.putDefaultValue("value", bundle)
            assertContentEquals(original, bundle.getStringArray("value"))
            assertTrue(argument.verify("value", bundle))
        }
    }

    @Test
    fun controllerCopiesStringArraysAndRestoresEmptyAndNonemptyPayloads() {
        val source = arrayOf("a", "b")
        val controller = AdaptiveNavHostController()
        controller.navigateWithValues("same", mapOf("strings" to source, "empty" to emptyArray<String>()))
        source[0] = "caller mutation"
        val entry = assertNotNull(controller.currentBackStackEntry)
        val firstRead = assertIs<Array<String>>(entry.arguments["strings"])
        assertContentEquals(arrayOf("a", "b"), firstRead)
        firstRead[0] = "getter mutation"
        val restored = assertNotNull(AdaptiveNavHostController.restoreState(controller.saveState()))
        val values = assertNotNull(restored.currentBackStackEntry).arguments
        assertContentEquals(arrayOf("a", "b"), assertIs<Array<String>>(values["strings"]))
        assertContentEquals(emptyArray(), assertIs<Array<String>>(values["empty"]))
        assertEquals(entry.id, restored.currentBackStackEntry!!.id)
        val ids = controller.backStackEntries.map { it.id }
        assertFailsWith<IllegalArgumentException> {
            controller.navigateWithValues("same", mapOf("strings" to arrayOf<Any?>("a", 1)))
        }
        assertEquals(ids, controller.backStackEntries.map { it.id })
    }
}
