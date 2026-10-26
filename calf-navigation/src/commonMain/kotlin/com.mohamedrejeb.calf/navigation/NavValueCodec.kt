package com.mohamedrejeb.calf.navigation

private const val HEX = "0123456789ABCDEF"

/** RFC 3986 unreserved characters only; encode UTF-8 bytes, not UTF-16 code units. */
internal fun encodeNavString(value: String): String = buildString {
    // Reject malformed UTF-16 instead of silently replacing it and losing round-trip data.
    val bytes = try {
        value.encodeToByteArray(throwOnInvalidSequence = true)
    } catch (malformed: CharacterCodingException) {
        throw IllegalArgumentException("Malformed Unicode navigation value", malformed)
    }
    bytes.forEach { byte ->
        val unsigned = byte.toInt() and 0xff
        if (unsigned in 65..90 || unsigned in 97..122 || unsigned in 48..57 ||
            unsigned == 45 || unsigned == 46 || unsigned == 95 || unsigned == 126
        ) {
            append(unsigned.toChar())
        } else {
            append('%')
            append(HEX[unsigned ushr 4])
            append(HEX[unsigned and 15])
        }
    }
}

internal fun decodeNavString(value: String): String {
    val bytes = ByteArray(value.length)
    var source = 0
    var target = 0
    while (source < value.length) {
        val char = value[source++]
        val byte = if (char == '%') {
            require(source + 1 < value.length) { "Incomplete percent escape" }
            val high = value[source++].digitToIntOrNull(16)
            val low = value[source++].digitToIntOrNull(16)
            require(high != null && low != null) { "Invalid percent escape" }
            (high shl 4) or low
        } else {
            require(char in 'A'..'Z' || char in 'a'..'z' || char in '0'..'9' ||
                char == '-' || char == '.' || char == '_' || char == '~'
            ) { "Expected an encoded navigation string, not raw URI text" }
            char.code
        }
        bytes[target++] = byte.toByte()
    }
    return try {
        bytes.decodeToString(endIndex = target, throwOnInvalidSequence = true)
    } catch (malformed: CharacterCodingException) {
        throw IllegalArgumentException("Malformed UTF-8 navigation value", malformed)
    }
}

/** Length framing distinguishes null, empty, empty elements and embedded delimiters. */
internal fun encodeNavArray(values: List<String>?): String =
    values?.joinToString(separator = "", prefix = "[", postfix = "]") { "${it.length}:$it" }
        ?: "null"

internal fun decodeNavArray(value: String): List<String>? {
    if (value == "null") return null
    require(value.startsWith('[') && value.endsWith(']')) { "Invalid navigation array framing" }
    val end = value.lastIndex
    var cursor = 1
    val result = mutableListOf<String>()
    while (cursor < end) {
        val colon = value.indexOf(':', cursor)
        require(colon > cursor && colon < end) { "Missing navigation array element length" }
        val lengthText = value.substring(cursor, colon)
        require(lengthText.all { it in '0'..'9' }) { "Invalid navigation array element length" }
        val length = lengthText.toIntOrNull()
        require(length != null && length <= end - colon - 1) { "Invalid navigation array element length" }
        cursor = colon + 1
        result += value.substring(cursor, cursor + length)
        cursor += length
    }
    return result
}
