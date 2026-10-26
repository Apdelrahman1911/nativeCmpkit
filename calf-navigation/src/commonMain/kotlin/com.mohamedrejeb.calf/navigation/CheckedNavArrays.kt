package com.mohamedrejeb.calf.navigation

/** A borrowed array reference whose current elements are all non-null Strings. */
internal fun checkedStringArray(value: Any?): Array<String>? =
    checkedObjectArray<Array<String>, String>(value)

/** A borrowed array reference whose current elements are CharSequences or null. */
internal fun checkedCharSequenceArray(value: Any?): Array<CharSequence?>? =
    checkedObjectArray<Array<CharSequence?>, CharSequence?>(value)

/**
 * Scan a star-projected array before giving its elements a type: Array<T>'s
 * component metadata is erased on Native and may be erased in browsers. The
 * reified whole-array safe cast also retains JVM component checks, including for
 * empty arrays, without calling the JVM-only isArrayOf extension.
 *
 * On erased targets an empty Array<Any> cannot be distinguished from an empty
 * Array<String>; it contains no invalid elements and is accepted. This is a
 * read-time check, not a new ownership guarantee: bundle/mMap aliases can still
 * mutate the borrowed array later. Navigation entry/default boundaries copy it.
 */
private inline fun <reified A, reified E> checkedObjectArray(value: Any?): A? {
    val array = value as? Array<*> ?: return null
    if (!array.all { it is E }) return null
    return value as? A
}
