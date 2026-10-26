package com.mohamedrejeb.calf.navigation

/** Copies the mutable built-in values supported at the navigation boundary. */
internal fun copyNavValue(value: Any?): Any? = when (value) {
    is BooleanArray -> value.copyOf()
    is ByteArray -> value.copyOf()
    is CharArray -> value.copyOf()
    is ShortArray -> value.copyOf()
    is IntArray -> value.copyOf()
    is LongArray -> value.copyOf()
    is FloatArray -> value.copyOf()
    is DoubleArray -> value.copyOf()
    is Array<*> -> value.copyOf()
    else -> value
}

internal fun copyNavValues(values: Map<String, Any?>): Map<String, Any?> =
    values.mapValues { (_, value) -> copyNavValue(value) }

internal fun navValuesEqual(first: Any?, second: Any?): Boolean = when {
    first is BooleanArray && second is BooleanArray -> first.contentEquals(second)
    first is ByteArray && second is ByteArray -> first.contentEquals(second)
    first is CharArray && second is CharArray -> first.contentEquals(second)
    first is ShortArray && second is ShortArray -> first.contentEquals(second)
    first is IntArray && second is IntArray -> first.contentEquals(second)
    first is LongArray && second is LongArray -> first.contentEquals(second)
    first is FloatArray && second is FloatArray -> first.contentEquals(second)
    first is DoubleArray && second is DoubleArray -> first.contentEquals(second)
    first is Array<*> && second is Array<*> -> first.contentDeepEquals(second)
    else -> first == second
}

internal fun navValueHash(value: Any?): Int = when (value) {
    is BooleanArray -> value.contentHashCode()
    is ByteArray -> value.contentHashCode()
    is CharArray -> value.contentHashCode()
    is ShortArray -> value.contentHashCode()
    is IntArray -> value.contentHashCode()
    is LongArray -> value.contentHashCode()
    is FloatArray -> value.contentHashCode()
    is DoubleArray -> value.contentHashCode()
    is Array<*> -> value.contentDeepHashCode()
    else -> value?.hashCode() ?: 0
}

/**
 * Avoids erased generic casts for the built-ins. A custom type must validate its own
 * [AdaptiveNavType.put] implementation; arbitrary objects are not controller-saveable.
 */
@Suppress("UNCHECKED_CAST")
internal fun AdaptiveNavType<*>.acceptsValue(value: Any?): Boolean {
    if (value == null) return isNullableAllowed
    return when (this) {
        AdaptiveNavType.IntType, AdaptiveNavType.ReferenceType -> value is Int
        AdaptiveNavType.LongType -> value is Long
        AdaptiveNavType.FloatType -> value is Float
        AdaptiveNavType.BoolType -> value is Boolean
        AdaptiveNavType.StringType -> value is String
        AdaptiveNavType.IntArrayType -> value is IntArray
        AdaptiveNavType.LongArrayType -> value is LongArray
        AdaptiveNavType.FloatArrayType -> value is FloatArray
        AdaptiveNavType.BoolArrayType -> value is BooleanArray
        AdaptiveNavType.StringArrayType -> checkedStringArray(value) != null
        else -> try {
            (this as AdaptiveNavType<Any?>).put(AdaptiveBundle(), "value", value)
            true
        } catch (_: ClassCastException) {
            false
        } catch (_: IllegalArgumentException) {
            false
        }
    }
}

/** All values persisted by the controller have an explicit built-in codec. */
@Suppress("UNCHECKED_CAST")
internal fun portableNavType(value: Any?): AdaptiveNavType<Any?> =
    if (value == null) AdaptiveNavType.StringType as AdaptiveNavType<Any?>
    else AdaptiveNavType.inferFromValueType(value) as AdaptiveNavType<Any?>
