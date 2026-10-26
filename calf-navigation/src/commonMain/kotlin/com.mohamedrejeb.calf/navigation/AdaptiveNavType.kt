/*
 * Copyright 2018 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Adapted for Calf and nativeCmpkit. Modified 2026-10-24: portable codecs,
 * checked getters and inference. See licenses/navigation-aosp-provenance.json.
 */
package com.mohamedrejeb.calf.navigation

import kotlin.jvm.JvmField
import kotlin.jvm.JvmStatic

/**
 * AdaptiveNavType denotes the type that can be used in a [NavArgument].
 *
 * Built-ins support Int, Long, Boolean, Float, nullable String and their arrays.
 * ReferenceType is an Int alias, not an Android resource resolver. There is no XML,
 * Parcelable, Serializable or reflective class lookup in this portable module.
 * A custom subclass owns its own validation and codec; controller payloads must
 * still consist of the portable built-in value types.
 *
 * @param T the type of the data that is supported by this AdaptiveNavType
 */
abstract class AdaptiveNavType<T>(
    /**
     * Check if an argument with this type can hold a null value.
     * @return Returns true if this type allows null values, false otherwise.
     */
    open val isNullableAllowed: Boolean
) {

    /**
     * Put a value of this type in the `bundle`
     *
     * @param bundle bundle to put value in
     * @param key    bundle key
     * @param value  value of this type
     */
    abstract fun put(bundle: AdaptiveBundle, key: String, value: T)

    /**
     * Get a value of this type from the `bundle`
     *
     * @param bundle bundle to get value from
     * @param key    bundle key
     * @return value of this type
     */
    abstract operator fun get(bundle: AdaptiveBundle, key: String): T?

    /**
     * Parse a value of this type from a String.
     *
     * Repeatedly appending immutable arrays copies the previous array. For many
     * values use [parseValues], which allocates each built-in result array once.
     *
     * @param value string representation of a value of this type
     * @return parsed value of the type represented by this AdaptiveNavType
     * @throws IllegalArgumentException if value cannot be parsed into this type
     */
    abstract fun parseValue(value: String): T

    /**
     * Parse a value of this type from a String and then combine that
     * parsed value with the given previousValue of the same type to
     * provide a new value that contains both the new and previous value.
     *
     * By default, the given value will replace the previousValue.
     *
     * @param value string representation of a value of this type
     * @param previousValue previously parsed value of this type
     * @return combined parsed value of the type represented by this AdaptiveNavType
     * @throws IllegalArgumentException if value cannot be parsed into this type
     */
    open fun parseValue(value: String, previousValue: T) = parseValue(value)

    /** Parses raw values in one batch. Scalar types require exactly one value. */
    open fun parseValues(values: List<String>): T {
        require(values.size == 1) { "$name expects exactly one raw value" }
        return parseValue(values.single())
    }

    /**
     * The inverse of [serializeAsValue]. Raw [parseValue] deliberately does not
     * URI-decode strings or interpret framed arrays.
     */
    open fun parseSerializedValue(value: String): T = parseValue(value)

    /**
     * Parse a value of this type from a String and put it in a `bundle`
     *
     * @param bundle bundle to put value in
     * @param key    bundle key under which to put the value
     * @param value  string representation of a value of this type
     * @return parsed value of the type represented by this AdaptiveNavType
     * @suppress
     */
    fun parseAndPut(bundle: AdaptiveBundle, key: String, value: String): T {
        val parsedValue = parseValue(value)
        put(bundle, key, parsedValue)
        return parsedValue
    }

    /**
     * Parse a value of this type from a String, combine that parsed value
     * with the given previousValue, and then put that combined parsed
     * value in a `bundle`.
     *
     * @param bundle bundle to put value in
     * @param key    bundle key under which to put the value
     * @param value  string representation of a value of this type
     * @param previousValue previously parsed value of this type
     * @return combined parsed value of the type represented by this AdaptiveNavType
     * @suppress
     */
    fun parseAndPut(bundle: AdaptiveBundle, key: String, value: String?, previousValue: T): T {
        if (!bundle.containsKey(key)) {
            throw IllegalArgumentException("There is no previous value in this bundle.")
        }
        if (value != null) {
            val parsedCombinedValue = parseValue(value, previousValue)
            put(bundle, key, parsedCombinedValue)
            return parsedCombinedValue
        }
        return previousValue
    }

    /**
     * Serialize a value of this AdaptiveNavType into a String.
     *
     * Scalar built-ins use their canonical text. Strings use UTF-8 percent encoding
     * and distinguish null from the literal "null". Arrays use length-framed
     * elements, with "null" for a null array and "[]" for an empty array.
     * Decode with [parseSerializedValue], not the raw [parseValue] API.
     *
     * This method can be override for custom serialization implementation on types such
     * custom AdaptiveNavType classes.
     *
     * @param value a value representing this AdaptiveNavType to be serialized into a String
     * @return serialized String value of [value]
     */
    open fun serializeAsValue(value: T): String {
        return value.toString()
    }

    /**
     * The name of this type.
     *
     * Historic Android-style type name; this module does not parse Navigation XML.
     *
     * @return name of this type
     */
    open val name: String = "nav_type"

    override fun toString(): String {
        return name
    }

    companion object {
        /**
         * Resolve a built-in type name. Custom/reflection-based names are unsupported.
         *
         * @param type        argType string, usually parsed from the Navigation XML file
         * @param packageName retained for source compatibility; unused.
         * @return a AdaptiveNavType representing the type indicated by the argType string.
         * Defaults to StringType for null.
         * @throws IllegalArgumentException if there is no valid argType
         */
        @Suppress("NON_FINAL_MEMBER_IN_OBJECT") // this needs to be open to
        // maintain api compatibility and type cast are unchecked
        @JvmStatic
        open fun fromArgType(type: String?, packageName: String?): AdaptiveNavType<*> {
            when {
                IntType.name == type -> return IntType
                IntArrayType.name == type -> return IntArrayType
                LongType.name == type -> return LongType
                LongArrayType.name == type -> return LongArrayType
                BoolType.name == type -> return BoolType
                BoolArrayType.name == type -> return BoolArrayType
                StringType.name == type -> return StringType
                StringArrayType.name == type -> return StringArrayType
                FloatType.name == type -> return FloatType
                FloatArrayType.name == type -> return FloatArrayType
                ReferenceType.name == type -> return ReferenceType
                !type.isNullOrEmpty() -> throw IllegalArgumentException(
                    "Unsupported navigation type '$type'. Use a built-in integer, long, float, " +
                        "boolean, string, reference, or supported array type."
                )
            }
            return StringType
        }

        /** @suppress */
        @Suppress("UNCHECKED_CAST") // needed for cast to AdaptiveNavType<Any>
        @JvmStatic
        fun inferFromValue(value: String): AdaptiveNavType<Any> {
            // because we allow Long literals without the L suffix at runtime,
            // the order of IntType and LongType parsing has to be reversed compared to Safe Args
            try {
                IntType.parseValue(value)
                return IntType as AdaptiveNavType<Any>
            } catch (e: IllegalArgumentException) {
                // ignored, proceed to check next type
            }
            try {
                LongType.parseValue(value)
                return LongType as AdaptiveNavType<Any>
            } catch (e: IllegalArgumentException) {
                // ignored, proceed to check next type
            }
            try {
                FloatType.parseValue(value)
                return FloatType as AdaptiveNavType<Any>
            } catch (e: IllegalArgumentException) {
                // ignored, proceed to check next type
            }
            try {
                BoolType.parseValue(value)
                return BoolType as AdaptiveNavType<Any>
            } catch (e: IllegalArgumentException) {
                // ignored, proceed to check next type
            }
            return StringType as AdaptiveNavType<Any>
        }

        /** Infer a built-in type; unsupported objects fail without reflection. */
        @Suppress("UNCHECKED_CAST") // needed for cast to AdaptiveNavType<Any>
        @JvmStatic
        fun inferFromValueType(value: Any): AdaptiveNavType<Any> {
            return when {
                value is Int -> IntType as AdaptiveNavType<Any>
                value is IntArray -> IntArrayType as AdaptiveNavType<Any>
                value is Long -> LongType as AdaptiveNavType<Any>
                value is LongArray -> LongArrayType as AdaptiveNavType<Any>
                value is Float -> FloatType as AdaptiveNavType<Any>
                value is FloatArray -> FloatArrayType as AdaptiveNavType<Any>
                value is Boolean -> BoolType as AdaptiveNavType<Any>
                value is BooleanArray -> BoolArrayType as AdaptiveNavType<Any>
                value is String -> StringType as AdaptiveNavType<Any>
                checkedStringArray(value) != null ->
                    StringArrayType as AdaptiveNavType<Any>
                else -> {
                    throw IllegalArgumentException(
                        "Object of type ${value::class.simpleName} is not supported for navigation " +
                                "arguments."
                    )
                }
            }
        }

        /**
         * AdaptiveNavType for storing integer values,
         * corresponding with the "integer" type in a Navigation XML file.
         *
         * Null values are not supported.
         */
        @JvmField
        val IntType: AdaptiveNavType<Int> = object : AdaptiveNavType<Int>(false) {
            override val name: String
                get() = "integer"

            override fun put(bundle: AdaptiveBundle, key: String, value: Int) {
                bundle.putInt(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): Int? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): Int {
                return if (value.startsWith("0x")) {
                    value.substring(2).toInt(16)
                } else {
                    value.toInt()
                }
            }
        }

        /**
         * AdaptiveNavType for storing integer values representing resource ids,
         * corresponding with the "reference" type in a Navigation XML file.
         *
         * Null values are not supported.
         */
        @JvmField
        val ReferenceType: AdaptiveNavType<Int> = object : AdaptiveNavType<Int>(false) {
            override val name: String
                get() = "reference"

            override fun put(bundle: AdaptiveBundle, key: String, value: Int) {
                bundle.putInt(key, value)
            }
            
            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): Int? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): Int {
                return if (value.startsWith("0x")) {
                    value.substring(2).toInt(16)
                } else {
                    value.toInt()
                }
            }
        }

        /**
         * AdaptiveNavType for storing integer arrays,
         * corresponding with the "integer[]" type in a Navigation XML file.
         *
         * Null values are supported.
         * Default values in Navigation XML files are not supported.
         */
        @JvmField
        val IntArrayType: AdaptiveNavType<IntArray?> = object : AdaptiveNavType<IntArray?>(true) {
            override val name: String
                get() = "integer[]"

            override fun put(bundle: AdaptiveBundle, key: String, value: IntArray?) {
                bundle.putIntArray(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): IntArray? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): IntArray {
                return intArrayOf(IntType.parseValue(value))
            }

            override fun parseValue(value: String, previousValue: IntArray?): IntArray {
                return previousValue?.plus(parseValue(value)) ?: parseValue(value)
            }

            override fun parseValues(values: List<String>): IntArray =
                IntArray(values.size) { IntType.parseValue(values[it]) }

            override fun serializeAsValue(value: IntArray?): String =
                encodeNavArray(value?.map { IntType.serializeAsValue(it) })

            override fun parseSerializedValue(value: String): IntArray? =
                decodeNavArray(value)?.let { values ->
                    IntArray(values.size) { IntType.parseSerializedValue(values[it]) }
                }

        }

        /**
         * AdaptiveNavType for storing long values,
         * corresponding with the "long" type in a Navigation XML file.
         *
         * Null values are not supported.
         * Default values for this type in Navigation XML files must always end with an 'L' suffix, e.g.
         * `app:defaultValue="123L"`.
         */
        @JvmField
        val LongType: AdaptiveNavType<Long> = object : AdaptiveNavType<Long>(false) {
            override val name: String
                get() = "long"

            override fun put(bundle: AdaptiveBundle, key: String, value: Long) {
                bundle.putLong(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): Long? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): Long {
                // At runtime the L suffix is optional, contrary to the Safe Args plugin.
                // This is in order to be able to parse long numbers passed as deep link URL
                // parameters
                var localValue = value
                if (value.endsWith("L")) {
                    localValue = localValue.substring(0, value.length - 1)
                }
                return if (value.startsWith("0x")) {
                    localValue.substring(2).toLong(16)
                } else {
                    localValue.toLong()
                }
            }
        }

        /**
         * AdaptiveNavType for storing long arrays,
         * corresponding with the "long[]" type in a Navigation XML file.
         *
         * Null values are supported.
         * Default values in Navigation XML files are not supported.
         */
        @JvmField
        val LongArrayType: AdaptiveNavType<LongArray?> = object : AdaptiveNavType<LongArray?>(true) {
            override val name: String
                get() = "long[]"

            override fun put(bundle: AdaptiveBundle, key: String, value: LongArray?) {
                bundle.putLongArray(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): LongArray? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): LongArray {
                return longArrayOf(LongType.parseValue(value))
            }

            override fun parseValue(value: String, previousValue: LongArray?): LongArray? {
                return previousValue?.plus(parseValue(value)) ?: parseValue(value)
            }

            override fun parseValues(values: List<String>): LongArray =
                LongArray(values.size) { LongType.parseValue(values[it]) }

            override fun serializeAsValue(value: LongArray?): String =
                encodeNavArray(value?.map { LongType.serializeAsValue(it) })

            override fun parseSerializedValue(value: String): LongArray? =
                decodeNavArray(value)?.let { values ->
                    LongArray(values.size) { LongType.parseSerializedValue(values[it]) }
                }

        }

        /**
         * AdaptiveNavType for storing float values,
         * corresponding with the "float" type in a Navigation XML file.
         *
         * Null values are not supported.
         */
        @JvmField
        val FloatType: AdaptiveNavType<Float> = object : AdaptiveNavType<Float>(false) {
            override val name: String
                get() = "float"

            override fun put(bundle: AdaptiveBundle, key: String, value: Float) {
                bundle.putFloat(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): Float? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): Float {
                return value.toFloat()
            }

            // JavaScript Number.toString() drops the sign of negative zero.
            override fun serializeAsValue(value: Float): String =
                if (value == 0f && value.toBits() == Int.MIN_VALUE) "-0.0" else value.toString()
        }

        /**
         * AdaptiveNavType for storing float arrays,
         * corresponding with the "float[]" type in a Navigation XML file.
         *
         * Null values are supported.
         * Default values in Navigation XML files are not supported.
         */
        @JvmField
        val FloatArrayType: AdaptiveNavType<FloatArray?> = object : AdaptiveNavType<FloatArray?>(true) {
            override val name: String
                get() = "float[]"

            override fun put(bundle: AdaptiveBundle, key: String, value: FloatArray?) {
                bundle.putFloatArray(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): FloatArray? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): FloatArray {
                return floatArrayOf(FloatType.parseValue(value))
            }

            override fun parseValue(value: String, previousValue: FloatArray?): FloatArray? {
                return previousValue?.plus(parseValue(value)) ?: parseValue(value)
            }

            override fun parseValues(values: List<String>): FloatArray =
                FloatArray(values.size) { FloatType.parseValue(values[it]) }

            override fun serializeAsValue(value: FloatArray?): String =
                encodeNavArray(value?.map { FloatType.serializeAsValue(it) })

            override fun parseSerializedValue(value: String): FloatArray? =
                decodeNavArray(value)?.let { values ->
                    FloatArray(values.size) { FloatType.parseSerializedValue(values[it]) }
                }

        }

        /**
         * AdaptiveNavType for storing boolean values,
         * corresponding with the "boolean" type in a Navigation XML file.
         *
         * Null values are not supported.
         */
        @JvmField
        val BoolType: AdaptiveNavType<Boolean> = object : AdaptiveNavType<Boolean>(false) {
            override val name: String
                get() = "boolean"

            override fun put(bundle: AdaptiveBundle, key: String, value: Boolean) {
                bundle.putBoolean(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): Boolean? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): Boolean {
                return when (value) {
                    "true" -> true
                    "false" -> false
                    else -> {
                        throw IllegalArgumentException(
                            "A boolean AdaptiveNavType only accepts \"true\" or \"false\" values."
                        )
                    }
                }
            }
        }

        /**
         * AdaptiveNavType for storing boolean arrays,
         * corresponding with the "boolean[]" type in a Navigation XML file.
         *
         * Null values are supported.
         * Default values in Navigation XML files are not supported.
         */
        @JvmField
        val BoolArrayType: AdaptiveNavType<BooleanArray?> = object : AdaptiveNavType<BooleanArray?>(true) {
            override val name: String
                get() = "boolean[]"

            override fun put(bundle: AdaptiveBundle, key: String, value: BooleanArray?) {
                bundle.putBooleanArray(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): BooleanArray? {
                return bundle.getOrNull(key)
            }

            override fun parseValue(value: String): BooleanArray {
                return booleanArrayOf(BoolType.parseValue(value))
            }

            override fun parseValue(value: String, previousValue: BooleanArray?): BooleanArray? {
                return previousValue?.plus(parseValue(value)) ?: parseValue(value)
            }

            override fun parseValues(values: List<String>): BooleanArray =
                BooleanArray(values.size) { BoolType.parseValue(values[it]) }

            override fun serializeAsValue(value: BooleanArray?): String =
                encodeNavArray(value?.map { BoolType.serializeAsValue(it) })

            override fun parseSerializedValue(value: String): BooleanArray? =
                decodeNavArray(value)?.let { values ->
                    BooleanArray(values.size) { BoolType.parseSerializedValue(values[it]) }
                }

        }

        /**
         * AdaptiveNavType for storing String values,
         * corresponding with the "string" type in a Navigation XML file.
         *
         * Null values are supported.
         */
        @JvmField
        val StringType: AdaptiveNavType<String?> = object : AdaptiveNavType<String?>(true) {
            override val name: String
                get() = "string"

            override fun put(bundle: AdaptiveBundle, key: String, value: String?) {
                bundle.putString(key, value)
            }

            @Suppress("DEPRECATION")
            override fun get(bundle: AdaptiveBundle, key: String): String? {
                return bundle.getOrNull(key)
            }

            /**
             * Returns input value by default.
             *
             * If input value is "null", returns null as the reversion of Kotlin standard library
             * serializing null receivers of [kotlin.toString] into "null".
             */
            override fun parseValue(value: String): String? {
                return if (value == "null") null else value
            }

            /** URI-safe serialized representation; literal "null" is escaped. */
            override fun serializeAsValue(value: String?): String = when (value) {
                null -> "null"
                "null" -> "%6Eull"
                else -> encodeNavString(value)
            }

            override fun parseSerializedValue(value: String): String? =
                if (value == "null") null else decodeNavString(value)

        }

        /**
         * AdaptiveNavType for storing String arrays,
         * corresponding with the "string[]" type in a Navigation XML file.
         *
         * Null values are supported.
         * Default values in Navigation XML files are not supported.
         */
        @JvmField
        val StringArrayType: AdaptiveNavType<Array<String>?> = object : AdaptiveNavType<Array<String>?>(
            true
        ) {
            override val name: String
                get() = "string[]"

            override fun put(bundle: AdaptiveBundle, key: String, value: Array<String>?) {
                bundle.putStringArray(key, value)
            }

            override fun get(bundle: AdaptiveBundle, key: String): Array<String>? {
                return bundle.getStringArray(key)
            }

            override fun parseValue(value: String): Array<String> {
                return arrayOf(value)
            }

            override fun parseValue(value: String, previousValue: Array<String>?): Array<String>? {
                return previousValue?.plus(parseValue(value)) ?: parseValue(value)
            }

            override fun parseValues(values: List<String>): Array<String> = values.toTypedArray()

            override fun serializeAsValue(value: Array<String>?): String =
                encodeNavArray(value?.map(StringType::serializeAsValue))

            override fun parseSerializedValue(value: String): Array<String>? =
                decodeNavArray(value)?.map { element ->
                    requireNotNull(StringType.parseSerializedValue(element)) {
                        "String arrays do not support null elements"
                    }
                }?.toTypedArray()

        }
    }
}
