package com.mohamedrejeb.calf.navigation

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

class NavArgumentAndBundleTest {
    @Test
    fun typedRequiredArgumentHasNoDefault() {
        val argument = NavArgument.Builder().setType(AdaptiveNavType.IntType).build()
        assertFalse(argument.defaultValuePresent)
        assertNull(argument.defaultValue)
        assertEquals(listOf("id"), mapOf("id" to argument).missingRequiredArguments { true })
        assertTrue(mapOf("id" to argument).missingRequiredArguments { false }.isEmpty())
        assertTrue(argument.verify("id", AdaptiveBundle())) // Missing-key policy is separate.
    }

    @Test
    fun nullableDefaultDistinguishesExplicitNullFromAbsence() {
        val explicit = NavArgument.Builder().setType(AdaptiveNavType.StringType)
            .setIsNullable(true).setDefaultValue(null).build()
        val absent = NavArgument.Builder().setType(AdaptiveNavType.StringType)
            .setIsNullable(true).build()
        assertTrue(explicit.defaultValuePresent)
        assertFalse(absent.defaultValuePresent)
        val bundle = AdaptiveBundle()
        absent.putDefaultValue("absent", bundle)
        explicit.putDefaultValue("explicit", bundle)
        assertFalse(bundle.containsKey("absent"))
        assertTrue(bundle.containsKey("explicit"))
        assertNull(bundle.getString("explicit"))
        assertTrue(explicit.verify("explicit", bundle))
    }

    @Test
    fun invalidDefaultsFailAtConstruction() {
        assertFailsWith<IllegalArgumentException> { NavArgument.Builder().build() }
        assertFailsWith<IllegalArgumentException> {
            NavArgument.Builder().setType(AdaptiveNavType.IntType).setDefaultValue("42").build()
        }
        assertFailsWith<IllegalArgumentException> {
            NavArgument.Builder().setType(AdaptiveNavType.IntType).setDefaultValue(null).build()
        }
        assertFailsWith<IllegalArgumentException> {
            NavArgument.Builder().setType(AdaptiveNavType.IntType).setIsNullable(true).build()
        }
        assertFailsWith<IllegalArgumentException> {
            NavArgument.Builder().setType(AdaptiveNavType.StringType).setDefaultValue(null).build()
        }
    }

    @Test
    fun everyBuiltInDefaultIsValidatedAndRoundTripsInBundle() {
        val values = listOf<Any>(
            12, 45L, 1.5f, true, "value", intArrayOf(1, 2), longArrayOf(3, 4),
            floatArrayOf(1.5f), booleanArrayOf(true, false), arrayOf("a", "b"),
        )
        values.forEach { value ->
            val argument = NavArgument.Builder().setDefaultValue(value).build()
            val bundle = AdaptiveBundle()
            argument.putDefaultValue("value", bundle)
            assertTrue(argument.verify("value", bundle))
            assertTrue(navValuesEqual(value, bundle.getValue("value")))
            bundle.putObject("value", Any().toString())
            if (value !is String) assertFalse(argument.verify("value", bundle))
        }
    }

    @Test
    fun everyDeclaredBuiltInValidatesDefaultsAndRequiredPresenceWithoutInference() {
        // Inference always selects IntType, so it cannot cover ReferenceType.
        // Exercise every declared type (including that public Int alias) through
        // the builder, default insertion and value verification contracts.
        val cases = listOf<Pair<AdaptiveNavType<*>, Any>>(
            AdaptiveNavType.IntType to 12,
            AdaptiveNavType.ReferenceType to 0x7f010001,
            AdaptiveNavType.LongType to 45L,
            AdaptiveNavType.FloatType to 1.5f,
            AdaptiveNavType.BoolType to true,
            AdaptiveNavType.StringType to "value",
            AdaptiveNavType.IntArrayType to intArrayOf(1, 2),
            AdaptiveNavType.LongArrayType to longArrayOf(3, 4),
            AdaptiveNavType.FloatArrayType to floatArrayOf(1.5f),
            AdaptiveNavType.BoolArrayType to booleanArrayOf(true, false),
            AdaptiveNavType.StringArrayType to arrayOf("a", "b"),
        )
        for ((type, value) in cases) {
            val required = NavArgument.Builder().setType(type).build()
            assertSame(type, required.type)
            assertFalse(required.defaultValuePresent, type.name)
            assertNull(required.defaultValue, type.name)
            assertEquals(listOf("value"), mapOf("value" to required).missingRequiredArguments { true })
            assertTrue(mapOf("value" to required).missingRequiredArguments { false }.isEmpty())
            assertTrue(required.verify("value", AdaptiveBundle()))

            val argument = NavArgument.Builder().setType(type).setDefaultValue(value).build()
            assertSame(type, argument.type)
            assertTrue(argument.defaultValuePresent, type.name)
            assertTrue(navValuesEqual(value, argument.defaultValue), type.name)
            assertTrue(mapOf("value" to argument).missingRequiredArguments { true }.isEmpty())
            val bundle = AdaptiveBundle()
            argument.putDefaultValue("value", bundle)
            assertTrue(bundle.containsKey("value"), type.name)
            assertTrue(argument.verify("value", bundle), type.name)
            assertTrue(navValuesEqual(value, bundle.getValue("value")), type.name)

            val wrongValue: Any = if (type === AdaptiveNavType.StringType) 42 else "wrong"
            assertFailsWith<IllegalArgumentException>(type.name) {
                NavArgument.Builder().setType(type).setDefaultValue(wrongValue).build()
            }
            bundle.putObject("value", wrongValue)
            assertFalse(argument.verify("value", bundle), type.name)
            assertFailsWith<IllegalArgumentException>(type.name) {
                NavArgument.Builder().setType(type).setDefaultValue(null).build()
            }

            if (type.isNullableAllowed) {
                val optional = NavArgument.Builder().setType(type).setIsNullable(true).build()
                assertFalse(optional.defaultValuePresent, type.name)
                assertTrue(mapOf("value" to optional).missingRequiredArguments { true }.isEmpty())
                val explicitNull = NavArgument.Builder().setType(type).setIsNullable(true)
                    .setDefaultValue(null).build()
                assertTrue(explicitNull.defaultValuePresent, type.name)
                explicitNull.putDefaultValue("value", bundle)
                assertTrue(bundle.containsKey("value"), type.name)
                assertNull(bundle.getValue("value"), type.name)
                assertTrue(explicitNull.verify("value", bundle), type.name)
            } else {
                assertFailsWith<IllegalArgumentException>(type.name) {
                    NavArgument.Builder().setType(type).setIsNullable(true).build()
                }
            }
        }
    }

    @Test
    fun nullableArrayDefaultsAndDefensiveCopies() {
        val source = intArrayOf(1, 2)
        val argument = NavArgument.Builder().setDefaultValue(source).build()
        source[0] = 99
        assertContentEquals(intArrayOf(1, 2), argument.defaultValue as IntArray)
        (argument.defaultValue as IntArray)[0] = 42
        val bundle = AdaptiveBundle()
        argument.putDefaultValue("ids", bundle)
        assertContentEquals(intArrayOf(1, 2), bundle.getIntArray("ids"))
        bundle.getIntArray("ids")!![0] = -1
        assertContentEquals(intArrayOf(1, 2), argument.defaultValue as IntArray)
        val same = NavArgument.Builder().setDefaultValue(intArrayOf(1, 2)).build()
        assertEquals(argument, same)
        assertEquals(argument.hashCode(), same.hashCode())
        val nullable = NavArgument.Builder().setType(AdaptiveNavType.IntArrayType)
            .setIsNullable(true).setDefaultValue(null).build()
        nullable.putDefaultValue("nulls", bundle)
        assertTrue(nullable.verify("nulls", bundle))
    }

    @Test
    fun checkedAccessDoesNotCoerceOrThrowForWrongScalarType() {
        val bundle = AdaptiveBundle()
        bundle.putString("text", "42")
        bundle.putInt("number", 42)
        assertNull(bundle.getOrNull<Int>("text"))
        assertNull(bundle.getString("number"))
        assertEquals("fallback", bundle.getString("number", "fallback"))
        assertEquals(9, bundle.getInt("text", 9))
        assertNull(AdaptiveNavType.IntType[bundle, "text"])
        assertNull(AdaptiveNavType.StringType[bundle, "number"])
        assertNull(bundle.getOrNull<String>("missing"))
        bundle.putAll(mapOf("null" to null))
        assertTrue(bundle.containsKey("null"))
        assertNull(bundle.getOrNull<String>("null"))
    }

    @Test
    fun genericInsertionCoversExplicitScalarAndArraySetterFamilies() {
        val values = listOf<Any?>(
            null, true, 1.toByte(), 'a', 2.toShort(), 3, 4L, 5f, 6.0, "s", StringBuilder("cs"),
            booleanArrayOf(true), byteArrayOf(1), charArrayOf('a'), shortArrayOf(2),
            intArrayOf(3), longArrayOf(4), floatArrayOf(5f), doubleArrayOf(6.0),
            arrayOf("text"), arrayOf<CharSequence?>(StringBuilder("s"), null),
            arrayListOf(1, null), arrayListOf("s", null), arrayListOf<CharSequence?>(StringBuilder("s")),
        )
        val bundle = AdaptiveBundle()
        values.forEachIndexed { index, value ->
            bundle.putObject("$index", value)
            assertTrue(bundle.containsKey("$index"))
            assertTrue(navValuesEqual(value, bundle.getValue("$index")))
            if (value is IntArray || value is Array<*> || value is ArrayList<*> || value is StringBuilder) {
                assertSame(value, bundle.getValue("$index")) // Mutable references are intentionally shared.
            }
        }
        assertFailsWith<IllegalArgumentException> { bundle.putObject("bad", Any()) }
        assertFailsWith<IllegalArgumentException> { bundle.putObject("bad", arrayListOf(1, "s")) }
        assertFailsWith<IllegalArgumentException> { bundle.putObject("bad", arrayOf(Any())) }
    }

    @Test
    fun collectionGettersValidateElementsAndPreserveSupportedReferences() {
        val bundle = AdaptiveBundle()
        val ints = arrayListOf<Int?>(1, null)
        val strings = arrayListOf<String?>("x", null)
        bundle.putIntegerArrayList("ints", ints)
        bundle.putStringArrayList("strings", strings)
        bundle.mMap["mixed"] = arrayListOf(1, "wrong")
        bundle.mMap["mixedArray"] = arrayOf<Any>("x", 1)
        assertSame(ints, bundle.getIntegerArrayList("ints"))
        assertSame(strings, bundle.getStringArrayList("strings"))
        assertNull(bundle.getStringArrayList("ints"))
        assertNull(bundle.getIntegerArrayList("mixed"))
        assertNull(bundle.getStringArray("mixedArray"))
        assertNull(bundle.getCharSequenceArray("mixedArray"))
        assertNull(bundle.getIntArray("strings"))
    }

    @Test
    fun primitiveTypedFallbacksRemainConsistent() {
        val bundle = AdaptiveBundle().apply { putString("wrong", "value") }
        assertEquals(true, bundle.getBoolean("wrong", true))
        assertEquals(2.toByte(), bundle.getByte("wrong", 2))
        assertEquals('x', bundle.getChar("wrong", 'x'))
        assertEquals(3.toShort(), bundle.getShort("wrong", 3))
        assertEquals(4, bundle.getInt("wrong", 4))
        assertEquals(5L, bundle.getLong("wrong", 5L))
        assertEquals(6f, bundle.getFloat("wrong", 6f))
        assertEquals(7.0, bundle.getDouble("wrong", 7.0))
        assertNull(bundle.getCharSequence("missing"))
    }
}
