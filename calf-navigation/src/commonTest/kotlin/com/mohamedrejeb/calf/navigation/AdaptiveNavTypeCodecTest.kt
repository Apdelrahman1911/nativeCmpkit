package com.mohamedrejeb.calf.navigation

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFails
import kotlin.test.assertFailsWith
import kotlin.test.assertNotEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

class AdaptiveNavTypeCodecTest {
    @Test
    fun stringArrayInferenceIncludesEmptyAndRejectsMixedValues() {
        assertSame<AdaptiveNavType<*>>(AdaptiveNavType.StringArrayType, AdaptiveNavType.inferFromValueType(arrayOf("a")))
        assertSame<AdaptiveNavType<*>>(AdaptiveNavType.StringArrayType, AdaptiveNavType.inferFromValueType(emptyArray<String>()))
        assertFailsWith<IllegalArgumentException> { AdaptiveNavType.inferFromValueType(arrayOf<Any>("a", 1)) }
        assertFailsWith<IllegalArgumentException> { AdaptiveNavType.inferFromValueType(Any()) }
    }

    @Test
    fun stringsRoundTripNullLiteralDelimitersAndUnicode() {
        val type = AdaptiveNavType.StringType
        listOf(null, "", "null", "%6Eull", "a/b?x=1&n=2#frag", "a+b c", "عربي/猫/😀", "\u0000")
            .forEach { value -> assertEquals(value, type.parseSerializedValue(type.serializeAsValue(value))) }
        assertNotEquals(type.serializeAsValue(null), type.serializeAsValue("null"))
        assertEquals("a%2Fb%3Fx%3D1%26n%3D2%23frag", type.serializeAsValue("a/b?x=1&n=2#frag"))
        assertEquals("a/b?raw=true", type.parseValue("a/b?raw=true"))
        assertNull(type.parseValue("null")) // Documented raw compatibility, not encoded parsing.
        assertEquals("%2F", type.parseValue("%2F"))
    }

    @Test
    fun malformedEncodedStringsAreRejected() {
        listOf("%", "%A", "%GG", "unescaped space", "+", "/", "%FF", "%C0%80")
            .forEach { value -> assertFails("Expected '$value' to fail") { AdaptiveNavType.StringType.parseSerializedValue(value) } }
        // A prior JS rebuild emitted a lone-surrogate string literal as '?'.
        val malformedUtf16 = charArrayOf(0xD800.toChar()).concatToString()
        assertEquals(1, malformedUtf16.length)
        assertEquals(0xD800, malformedUtf16[0].code)
        assertFails { AdaptiveNavType.StringType.serializeAsValue(malformedUtf16) }
    }

    @Test
    fun primitiveArraysRoundTripNullEmptyAndValues() {
        assertArrayRoundTrip(AdaptiveNavType.IntArrayType, null)
        assertArrayRoundTrip(AdaptiveNavType.IntArrayType, intArrayOf())
        assertArrayRoundTrip(AdaptiveNavType.IntArrayType, intArrayOf(Int.MIN_VALUE, 0, Int.MAX_VALUE))
        assertArrayRoundTrip(AdaptiveNavType.LongArrayType, null)
        assertArrayRoundTrip(AdaptiveNavType.LongArrayType, longArrayOf())
        assertArrayRoundTrip(AdaptiveNavType.LongArrayType, longArrayOf(Long.MIN_VALUE, Long.MAX_VALUE))
        assertArrayRoundTrip(AdaptiveNavType.FloatArrayType, null)
        assertArrayRoundTrip(AdaptiveNavType.FloatArrayType, floatArrayOf())
        assertArrayRoundTrip(AdaptiveNavType.FloatArrayType, floatArrayOf(-0f, 1.5f, Float.NaN, Float.POSITIVE_INFINITY))
        assertArrayRoundTrip(AdaptiveNavType.BoolArrayType, null)
        assertArrayRoundTrip(AdaptiveNavType.BoolArrayType, booleanArrayOf())
        assertArrayRoundTrip(AdaptiveNavType.BoolArrayType, booleanArrayOf(true, false))
    }

    @Test
    fun floatScalarRoundTripsSignedZeroAndSpecialValues() {
        val type = AdaptiveNavType.FloatType
        val negativeZero = Float.fromBits(Int.MIN_VALUE)
        val positiveZero = Float.fromBits(0)
        assertEquals(Int.MIN_VALUE, negativeZero.toBits())
        assertEquals(0, positiveZero.toBits())
        assertEquals("-0.0", type.serializeAsValue(negativeZero))
        assertNotEquals(type.serializeAsValue(negativeZero), type.serializeAsValue(positiveZero))

        floatArrayOf(negativeZero, positiveZero, -1.5f, 1.5f, Float.MIN_VALUE, -Float.MIN_VALUE,
            Float.MAX_VALUE, -Float.MAX_VALUE, Float.NaN, Float.NEGATIVE_INFINITY, Float.POSITIVE_INFINITY)
            .forEach { value ->
                val restored = type.parseSerializedValue(type.serializeAsValue(value))
                assertEquals(value.toBits(), restored.toBits(), "Float codec changed bits for $value")
            }
    }

    @Test
    fun floatArrayRoundTripsSignedZeroAndSpecialValues() {
        val type = AdaptiveNavType.FloatArrayType
        val values = floatArrayOf(Float.fromBits(Int.MIN_VALUE), Float.fromBits(0), -1.5f, 1.5f,
            Float.MIN_VALUE, -Float.MIN_VALUE, Float.MAX_VALUE, -Float.MAX_VALUE, Float.NaN,
            Float.NEGATIVE_INFINITY, Float.POSITIVE_INFINITY)
        assertEquals(Int.MIN_VALUE, values[0].toBits())
        assertEquals(0, values[1].toBits())

        val restored = assertNotNull(type.parseSerializedValue(type.serializeAsValue(values)))
        assertContentEquals(IntArray(values.size) { values[it].toBits() },
            IntArray(restored.size) { restored[it].toBits() })
    }

    @Test
    fun stringArrayFramingDistinguishesAllEmptyAndLiteralCases() {
        val type = AdaptiveNavType.StringArrayType
        listOf<Array<String>?>(null, emptyArray(), arrayOf(""), arrayOf("", ""), arrayOf("null"),
            arrayOf("[]", ":", "1:a", "a,b", "\u0000", "عربي", "😀"))
            .forEach { assertContentEquals(it, type.parseSerializedValue(type.serializeAsValue(it))) }
        assertNotEquals(type.serializeAsValue(emptyArray()), type.serializeAsValue(arrayOf("")))
        assertFailsWith<IllegalArgumentException> { type.parseSerializedValue("[4:null]") }
    }

    @Test
    fun malformedArrayFramesFailRatherThanSilentlyTruncating() {
        listOf("", "[", "]", "[a:x]", "[-1:x]", "[4:a]", "[999999999999999:x]", "[1:aextra]", "[0:0]")
            .forEach { assertFails { AdaptiveNavType.StringArrayType.parseSerializedValue(it) } }
    }

    @Test
    fun bulkParsingHasOneResultPerInputAndPreservesRawCompatibility() {
        val values = List(10_000) { it.toString() }
        assertContentEquals(IntArray(10_000) { it }, AdaptiveNavType.IntArrayType.parseValues(values))
        assertContentEquals(longArrayOf(1, 2), AdaptiveNavType.LongArrayType.parseValues(listOf("1L", "0x2")))
        assertContentEquals(floatArrayOf(1f, 2.5f), AdaptiveNavType.FloatArrayType.parseValues(listOf("1", "2.5")))
        assertContentEquals(booleanArrayOf(true, false), AdaptiveNavType.BoolArrayType.parseValues(listOf("true", "false")))
        assertContentEquals(arrayOf("null", "a/b"), AdaptiveNavType.StringArrayType.parseValues(listOf("null", "a/b")))
        assertContentEquals(intArrayOf(1, 2), AdaptiveNavType.IntArrayType.parseValue("2", intArrayOf(1)))
        assertFailsWith<IllegalArgumentException> { AdaptiveNavType.IntType.parseValues(emptyList()) }
        assertFailsWith<IllegalArgumentException> { AdaptiveNavType.IntType.parseValues(listOf("1", "2")) }
    }

    @Test
    fun builtInNameResolutionAndScalarCodecsAreTruthful() {
        val types = listOf(AdaptiveNavType.IntType, AdaptiveNavType.ReferenceType, AdaptiveNavType.LongType,
            AdaptiveNavType.FloatType, AdaptiveNavType.BoolType, AdaptiveNavType.StringType,
            AdaptiveNavType.IntArrayType, AdaptiveNavType.LongArrayType, AdaptiveNavType.FloatArrayType,
            AdaptiveNavType.BoolArrayType, AdaptiveNavType.StringArrayType)
        types.forEach { assertSame(it, AdaptiveNavType.fromArgType(it.name, "ignored")) }
        assertSame(AdaptiveNavType.StringType, AdaptiveNavType.fromArgType(null, null))
        val error = assertFailsWith<IllegalArgumentException> { AdaptiveNavType.fromArgType(".Custom", "sample") }
        assertTrue(error.message.orEmpty().contains("Unsupported navigation type"))
        assertEquals(12, AdaptiveNavType.IntType.parseSerializedValue(AdaptiveNavType.IntType.serializeAsValue(12)))
        assertEquals(13L, AdaptiveNavType.LongType.parseSerializedValue(AdaptiveNavType.LongType.serializeAsValue(13L)))
        assertEquals(1.5f, AdaptiveNavType.FloatType.parseSerializedValue(AdaptiveNavType.FloatType.serializeAsValue(1.5f)))
        assertEquals(false, AdaptiveNavType.BoolType.parseSerializedValue(AdaptiveNavType.BoolType.serializeAsValue(false)))
    }

    private fun <T> assertArrayRoundTrip(type: AdaptiveNavType<T>, value: T) {
        assertTrue(navValuesEqual(value, type.parseSerializedValue(type.serializeAsValue(value))))
    }
}
