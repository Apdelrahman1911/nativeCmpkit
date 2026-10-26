package com.mohamedrejeb.calf.ui.web

/** The requested operation cannot be expressed by this platform/store without misleading results. */
class UnsupportedCookieOperationException(message: String) : UnsupportedOperationException(message)

internal fun validateCookie(cookie: Cookie) {
    val separators = "()<>@,;:\\\"/[]?={} \t"
    require(cookie.name.isNotEmpty() && !cookie.name.startsWith('$') && cookie.name.all {
        it.code in 33..126 && it !in separators
    }) { "Cookie name must be an HTTP token" }
    require(cookie.value.all {
        it.code == 0x21 || it.code in 0x23..0x2b || it.code in 0x2d..0x3a ||
            it.code in 0x3c..0x5b || it.code in 0x5d..0x7e
    }) { "Cookie value must contain only cookie-octets; encode arbitrary text first" }
    cookie.domain?.let { domain ->
        require(domain.removePrefix(".").isNotEmpty() && !domain.endsWith('.') && domain.all {
            it in 'a'..'z' || it in 'A'..'Z' || it in '0'..'9' || it == '-' || it == '.'
        }) { "Invalid cookie domain" }
    }
    cookie.path?.let { path ->
        require(path.startsWith('/') && path.all { it.code in 32..126 && it != ';' }) { "Invalid cookie path" }
    }
    cookie.expiresDate?.let { require(it in -62135596800000L..253402300799999L) { "Cookie expiry must be between years 0001 and 9999" } }
    if (cookie.name.startsWith("__Secure-")) require(cookie.isSecure) { "__Secure- cookies require Secure" }
    if (cookie.name.startsWith("__Host-")) {
        require(cookie.isSecure && cookie.domain == null && cookie.path == "/") { "__Host- cookies require Secure, Path=/ and no Domain" }
    }
}

internal fun validateCookieHost(cookie: Cookie, host: String, secure: Boolean) {
    validateCookie(cookie)
    cookie.domain?.removePrefix(".")?.let { domain ->
        require(host.equals(domain, true) || host.lowercase().endsWith(".${domain.lowercase()}")) {
            "Cookie domain does not match the URL"
        }
    }
    require(!cookie.isSecure || secure) { "Secure cookies require an HTTPS URL" }
}

internal fun defaultCookiePath(requestPath: String): String {
    if (!requestPath.startsWith('/')) return "/"
    val lastSlash = requestPath.lastIndexOf('/')
    return if (lastSlash <= 0) "/" else requestPath.substring(0, lastSlash)
}

internal fun cookiePathMatches(requestPath: String, cookiePath: String): Boolean {
    val request = requestPath.ifEmpty { "/" }
    val path = cookiePath.ifEmpty { "/" }
    return request == path || (request.startsWith(path) && (path.endsWith('/') || request.getOrNull(path.length) == '/'))
}

internal fun cookieMatchesRequest(
    requestHost: String,
    requestPath: String,
    requestSecure: Boolean,
    cookieDomain: String,
    cookiePath: String,
    cookieSecure: Boolean,
    hostOnly: Boolean,
): Boolean {
    val domain = cookieDomain.removePrefix(".").lowercase()
    val host = requestHost.lowercase()
    return (host == domain || (!hostOnly && host.endsWith(".$domain"))) &&
        (!cookieSecure || requestSecure) && cookiePathMatches(requestPath, cookiePath)
}

internal fun parseCookieHeader(header: String): List<Cookie> = header.split(';').mapNotNull { part ->
    val text = part.trim()
    val equals = text.indexOf('=')
    if (equals <= 0 || text.startsWith('$')) null
    else Cookie(text.substring(0, equals), text.substring(equals + 1).removeSurrounding("\""))
}

internal fun cookieHeader(cookie: Cookie, expires: String? = null): String = buildString {
    validateCookie(cookie)
    append(cookie.name).append('=').append(cookie.value)
    cookie.domain?.let { append("; Domain=").append(it) }
    cookie.path?.let { append("; Path=").append(it) }
    expires?.let { append("; Expires=").append(it) }
    if (cookie.isSecure) append("; Secure")
    if (cookie.isHttpOnly) append("; HttpOnly")
}
