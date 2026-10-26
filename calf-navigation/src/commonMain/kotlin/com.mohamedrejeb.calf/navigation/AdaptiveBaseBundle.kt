/*
 * Copyright (C) 2014 The Android Open Source Project
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
 * Adapted for Calf and nativeCmpkit. Modified 2026-10-24: checked accessors and
 * portable map contract. See licenses/navigation-aosp-provenance.json.
 */
package com.mohamedrejeb.calf.navigation

/**
 * An in-memory mutable map from String keys to values. This is not an Android
 * Parcelable/PersistableBundle, has no lazy unparcelling, and is not thread-safe.
 * Setters and [mMap] share value references; they do not make defensive copies.
 */
open class AdaptiveBaseBundle {

    var mMap: MutableMap<String, Any?> = mutableMapOf()

    /** Legacy compatibility flag, unused by this in-memory implementation. */
    @Deprecated("No lazy or parcelled values exist in AdaptiveBaseBundle")
    var mOwnsLazyValues = true

    /** Legacy compatibility flags, unused by this in-memory implementation. */
    @Deprecated("No parcel flags exist in AdaptiveBaseBundle")
    var mFlags = 0
    
    /**
     * Removes all elements from the mapping of this Bundle.
     */
    open fun clear() {
        mMap.clear()
    }

    /**
     * Returns true if the given key is contained in the mapping
     * of this Bundle.
     *
     * @param key a String key
     * @return true if the key is part of the mapping, false otherwise
     */
    fun containsKey(key: String): Boolean {
        return mMap.containsKey(key)
    }

    /**
     * Legacy unchecked access. T is erased: a wrong-type value may throw at the
     * caller's cast. Retained for existing binaries, not used by library validation.
     * Use [getOrNull] or an explicit typed getter instead.
     */
    @Deprecated("Unchecked erased cast; use getOrNull<T>(key) or a typed getter")
    @Suppress("UNCHECKED_CAST")
    operator fun <T> get(key: String): T? {
        return mMap[key] as T?
    }

    /**
     * Returns null for an absent/null value or a mismatched runtime type.
     * Like other reified casts, this cannot verify erased Array/List/Map element types;
     * use the explicitly checked array/list getters for supported containers.
     */
    inline fun <reified T> getOrNull(key: String): T? = mMap[key] as? T

    fun getValue(key: String): Any? {
        return mMap[key]
    }

    /**
     * Removes any entry with the given key from the mapping of this Bundle.
     *
     * @param key a String key
     */
    open fun remove(key: String) {
        mMap.remove(key)
    }

    /**
     * Inserts all mappings from the given Map into this BaseBundle.
     *
     * @param map a Map
     */
    fun putAll(map: Map<String, Any?>) {
        mMap.putAll(map)
    }

    /**
     * Returns a Set containing the Strings used as keys in this Bundle.
     *
     * @return a Set of String keys
     */
    fun keySet(): Set<String> {
        return mMap.keys
    }

    /** {@hide}  */
    open fun putObject(key: String, value: Any?) {
        when (value) {
            null -> putString(key, null)
            is Boolean -> putBoolean(key, value)
            is Byte -> putByte(key, value)
            is Char -> putChar(key, value)
            is Short -> putShort(key, value)
            is Int -> putInt(key, value)
            is Long -> putLong(key, value)
            is Float -> putFloat(key, value)
            is Double -> putDouble(key, value)
            is String -> putString(key, value)
            is CharSequence -> putCharSequence(key, value)
            is BooleanArray -> putBooleanArray(key, value)
            is ByteArray -> putByteArray(key, value)
            is CharArray -> putCharArray(key, value)
            is ShortArray -> putShortArray(key, value)
            is IntArray -> putIntArray(key, value)
            is LongArray -> putLongArray(key, value)
            is FloatArray -> putFloatArray(key, value)
            is DoubleArray -> putDoubleArray(key, value)
            is Array<*> -> {
                require(checkedCharSequenceArray(value) != null) {
                    "Only String/CharSequence object arrays are supported"
                }
                mMap[key] = value
            }
            is ArrayList<*> -> {
                require(value.all { it == null || it is Int } ||
                    value.all { it == null || it is CharSequence }) {
                    "Only Int/String/CharSequence ArrayLists are supported"
                }
                mMap[key] = value
            }
            else -> throw IllegalArgumentException("Unsupported type " + value::class)
        }
    }

    fun getBooleanArray(key: String): BooleanArray? = getOrNull(key)
    fun getByteArray(key: String): ByteArray? = getOrNull(key)
    fun getCharArray(key: String): CharArray? = getOrNull(key)
    fun getShortArray(key: String): ShortArray? = getOrNull(key)
    fun getIntArray(key: String): IntArray? = getOrNull(key)
    fun getLongArray(key: String): LongArray? = getOrNull(key)
    fun getFloatArray(key: String): FloatArray? = getOrNull(key)
    fun getDoubleArray(key: String): DoubleArray? = getOrNull(key)

    /** Checks current elements; returns the borrowed array, not a defensive copy. */
    fun getStringArray(key: String): Array<String>? = checkedStringArray(mMap[key])

    /** Checks current elements; returns the borrowed array, not a defensive copy. */
    fun getCharSequenceArray(key: String): Array<CharSequence?>? = checkedCharSequenceArray(mMap[key])

    @Suppress("UNCHECKED_CAST")
    fun getIntegerArrayList(key: String): ArrayList<Int?>? {
        val value = mMap[key] as? ArrayList<*> ?: return null
        return if (value.all { it == null || it is Int }) value as ArrayList<Int?> else null
    }

    @Suppress("UNCHECKED_CAST")
    fun getStringArrayList(key: String): ArrayList<String?>? {
        val value = mMap[key] as? ArrayList<*> ?: return null
        return if (value.all { it == null || it is String }) value as ArrayList<String?> else null
    }

    @Suppress("UNCHECKED_CAST")
    fun getCharSequenceArrayList(key: String): ArrayList<CharSequence?>? {
        val value = mMap[key] as? ArrayList<*> ?: return null
        return if (value.all { it == null || it is CharSequence }) value as ArrayList<CharSequence?> else null
    }

    /**
     * Inserts a Boolean value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a boolean
     */
    fun putBoolean(key: String, value: Boolean) {
        mMap[key] = value
    }

    /**
     * Inserts a byte value into the mapping of this Bundle, replacing
     * any existing value for the given key.
     *
     * @param key a String
     * @param value a byte
     */
    open fun putByte(key: String, value: Byte) {
        mMap[key] = value
    }

    /**
     * Inserts a char value into the mapping of this Bundle, replacing
     * any existing value for the given key.
     *
     * @param key a String
     * @param value a char
     */
    open fun putChar(key: String, value: Char) {
        mMap[key] = value
    }

    /**
     * Inserts a short value into the mapping of this Bundle, replacing
     * any existing value for the given key.
     *
     * @param key a String
     * @param value a short
     */
    open fun putShort(key: String, value: Short) {
        mMap[key] = value
    }

    /**
     * Inserts an int value into the mapping of this Bundle, replacing
     * any existing value for the given key.
     *
     * @param key a String
     * @param value an int
     */
    fun putInt(key: String, value: Int) {
        mMap[key] = value
    }

    /**
     * Inserts a long value into the mapping of this Bundle, replacing
     * any existing value for the given key.
     *
     * @param key a String
     * @param value a long
     */
    fun putLong(key: String, value: Long) {
        mMap[key] = value
    }

    /**
     * Inserts a float value into the mapping of this Bundle, replacing
     * any existing value for the given key.
     *
     * @param key a String
     * @param value a float
     */
    open fun putFloat(key: String, value: Float) {
        mMap[key] = value
    }

    /**
     * Inserts a double value into the mapping of this Bundle, replacing
     * any existing value for the given key.
     *
     * @param key a String
     * @param value a double
     */
    fun putDouble(key: String, value: Double) {
        mMap[key] = value
    }

    /**
     * Inserts a String value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a String, or null
     */
    fun putString(key: String, value: String?) {
        mMap[key] = value
    }

    /**
     * Inserts a CharSequence value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a CharSequence, or null
     */
    open fun putCharSequence(key: String, value: CharSequence?) {
        mMap[key] = value
    }

    /**
     * Inserts an ArrayList<Integer> value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value an ArrayList<Integer> object, or null
    </Integer></Integer> */
    fun putIntegerArrayList(key: String, value: ArrayList<Int?>?) {
        mMap[key] = value
    }

    /**
     * Inserts an ArrayList<String> value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value an ArrayList<String> object, or null
    </String></String> */
    fun putStringArrayList(key: String, value: ArrayList<String?>?) {
        mMap[key] = value
    }

    /**
     * Inserts an ArrayList<CharSequence> value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value an ArrayList<CharSequence> object, or null
    </CharSequence></CharSequence> */
    fun putCharSequenceArrayList(key: String, value: ArrayList<CharSequence?>?) {
        mMap[key] = value
    }

    /**
     * Inserts a boolean array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a boolean array object, or null
     */
    fun putBooleanArray(key: String, value: BooleanArray?) {
        mMap[key] = value
    }

    /**
     * Inserts a byte array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a byte array object, or null
     */
    open fun putByteArray(key: String, value: ByteArray?) {
        mMap[key] = value
    }

    /**
     * Inserts a short array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a short array object, or null
     */
    open fun putShortArray(key: String, value: ShortArray?) {
        mMap[key] = value
    }

    /**
     * Inserts a char array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a char array object, or null
     */
    open fun putCharArray(key: String, value: CharArray?) {
        mMap[key] = value
    }

    /**
     * Inserts an int array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value an int array object, or null
     */
    fun putIntArray(key: String, value: IntArray?) {
        mMap[key] = value
    }

    /**
     * Inserts a long array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a long array object, or null
     */
    fun putLongArray(key: String, value: LongArray?) {
        mMap[key] = value
    }

    /**
     * Inserts a float array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a float array object, or null
     */
    open fun putFloatArray(key: String, value: FloatArray?) {
        mMap[key] = value
    }

    /**
     * Inserts a double array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a double array object, or null
     */
    fun putDoubleArray(key: String, value: DoubleArray?) {
        mMap[key] = value
    }

    /**
     * Inserts a String array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a String array object, or null
     */
    fun putStringArray(key: String, value: Array<String>?) {
        mMap[key] = value
    }

    /**
     * Inserts a CharSequence array value into the mapping of this Bundle, replacing
     * any existing value for the given key.  Either key or value may be null.
     *
     * @param key a String
     * @param value a CharSequence array object, or null
     */
    open fun putCharSequenceArray(key: String, value: Array<CharSequence?>?) {
        mMap[key] = value
    }

    /**
     * Returns the value associated with the given key, or false if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @return a boolean value
     */
    fun getBoolean(key: String): Boolean {
        return getBoolean(key, false)
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist
     * @return a boolean value
     */
    fun getBoolean(key: String, defaultValue: Boolean): Boolean {
        val o: Any = mMap[key] ?: return defaultValue
        return o as? Boolean ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or (byte) 0 if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @return a byte value
     */
    open fun getByte(key: String): Byte {
        return getByte(key, 0.toByte())
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist
     * @return a byte value
     */
    open fun getByte(key: String, defaultValue: Byte): Byte {
        val o: Any = mMap[key] ?: return defaultValue
        return o as? Byte ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or (char) 0 if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @return a char value
     */
    open fun getChar(key: String): Char {
        return getChar(key, 0.toChar())
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist
     * @return a char value
     */
    open fun getChar(key: String, defaultValue: Char): Char {
        val o: Any = mMap[key] ?: return defaultValue
        return o as? Char ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or (short) 0 if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @return a short value
     */
    open fun getShort(key: String): Short {
        return getShort(key, 0.toShort())
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist
     * @return a short value
     */
    open fun getShort(key: String, defaultValue: Short): Short {
        val o: Any = mMap[key] ?: return defaultValue
        return o as? Short ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or 0 if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @return an int value
     */
    fun getInt(key: String): Int {
        return getInt(key, 0)
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist
     * @return an int value
     */
    fun getInt(key: String, defaultValue: Int): Int {
        val o: Any = mMap[key] ?: return defaultValue
        return o as? Int ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or 0L if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @return a long value
     */
    fun getLong(key: String): Long {
        return getLong(key, 0L)
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist
     * @return a long value
     */
    fun getLong(key: String, defaultValue: Long): Long {
        val o: Any = mMap[key] ?: return defaultValue
        return o as? Long ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or 0.0f if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @return a float value
     */
    open fun getFloat(key: String): Float {
        return getFloat(key, 0.0f)
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist
     * @return a float value
     */
    open fun getFloat(key: String, defaultValue: Float): Float {
        val o: Any = mMap[key] ?: return defaultValue
        return o as? Float ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or 0.0 if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @return a double value
     */
    fun getDouble(key: String): Double {
        return getDouble(key, 0.0)
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist
     * @return a double value
     */
    fun getDouble(key: String, defaultValue: Double): Double {
        val o: Any = mMap[key] ?: return defaultValue
        return o as? Double ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or null if
     * no mapping of the desired type exists for the given key or a null
     * value is explicitly associated with the key.
     *
     * @param key a String
     * @return a String value, or null
     */
    fun getString(key: String): String? {
        val o: Any? = mMap[key]
        return o as? String
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key or if a null
     * value is explicitly associated with the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist or if a null
     * value is associated with the given key.
     * @return the String value associated with the given key, or defaultValue
     * if no valid String object is currently mapped to that key.
     */
    fun getString(key: String, defaultValue: String): String {
        val s = getString(key)
        return s ?: defaultValue
    }

    /**
     * Returns the value associated with the given key, or null if
     * no mapping of the desired type exists for the given key or a null
     * value is explicitly associated with the key.
     *
     * @param key a String
     * @return a CharSequence value, or null
     */
    open fun getCharSequence(key: String): CharSequence? {
        val o: Any? = mMap[key]
        return o as? CharSequence
    }

    /**
     * Returns the value associated with the given key, or defaultValue if
     * no mapping of the desired type exists for the given key or if a null
     * value is explicitly associated with the given key.
     *
     * @param key a String
     * @param defaultValue Value to return if key does not exist or if a null
     * value is associated with the given key.
     * @return the CharSequence value associated with the given key, or defaultValue
     * if no valid CharSequence object is currently mapped to that key.
     */
    open fun getCharSequence(key: String, defaultValue: CharSequence?): CharSequence? {
        val cs = getCharSequence(key)
        return cs ?: defaultValue
    }
}
