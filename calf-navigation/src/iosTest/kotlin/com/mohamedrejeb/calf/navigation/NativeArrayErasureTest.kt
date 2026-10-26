package com.mohamedrejeb.calf.navigation

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertSame

/** Native erases object-array component types; checks must inspect current elements. */
class NativeArrayErasureTest {
    @Test
    fun emptyErasedObjectArrayIsAcceptedWithoutInventingComponentMetadata() {
        val source = emptyArray<Any>()
        val bundle = AdaptiveBundle().apply { putObject("value", source) }
        assertSame<Any?>(source, bundle.getStringArray("value"))
        assertSame<AdaptiveNavType<*>>(AdaptiveNavType.StringArrayType, AdaptiveNavType.inferFromValueType(source))
        val argument = NavArgument.Builder().setDefaultValue(source).build()
        argument.putDefaultValue("default", bundle)
        assertContentEquals(emptyArray<String>(), bundle.getStringArray("default"))
    }

    @Test
    fun erasedCallerArrayCanChangeButCapturedNavigationPayloadCannot() {
        val source = arrayOf<Any?>("original")
        val bundle = AdaptiveBundle().apply { putObject("value", source) }
        val controller = AdaptiveNavHostController()
        controller.navigateWithValues("home", mapOf("strings" to source))
        source[0] = 7
        assertNull(bundle.getStringArray("value"))
        assertNull(bundle.getCharSequenceArray("value"))
        assertFailsWith<IllegalArgumentException> { AdaptiveNavType.inferFromValueType(source) }
        assertContentEquals(arrayOf("original"),
            assertIs<Array<String>>(controller.currentBackStackEntry!!.arguments["strings"]))
        assertEquals(1, controller.backStackEntries.size)
    }
}
