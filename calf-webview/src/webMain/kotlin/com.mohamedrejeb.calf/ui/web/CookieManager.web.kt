// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import kotlinx.browser.document
import kotlinx.browser.window
import org.w3c.dom.url.URL

/** document.cookie is scoped to the host document, not the embedded iframe's origin. */
public actual class CookieManager actual constructor() {
    private data class OwnedCookie(val origin: String, val cookie: Cookie)
    private val owned = mutableMapOf<Triple<String, String?, String>, OwnedCookie>()

    public actual suspend fun setCookie(url: String, cookie: Cookie) {
        val request = documentRequest(url)
        validateCookieHost(cookie, request.hostname, request.protocol == "https:")
        if (cookie.isHttpOnly) throw UnsupportedCookieOperationException("JavaScript cannot create or update HttpOnly cookies")
        val resolved = cookie.copy(path = cookie.path ?: defaultCookiePath(request.pathname))
        val expiry = resolved.expiresDate?.let { cookieHttpDate(it.toDouble()) }
        document.cookie = cookieHeader(resolved, expiry)
        owned[Triple(resolved.name, resolved.domain, resolved.path!!)] = OwnedCookie(request.origin, resolved)
        // Browsers may still reject writes due to user/third-party policies. document.cookie has no
        // acknowledgement API; this does not claim the server accepted the cookie or a login worked.
    }

    public actual suspend fun getCookies(url: String): List<Cookie> {
        documentRequest(url)
        return parseCookieHeader(document.cookie)
    }

    public actual suspend fun removeAllCookies(): Unit = throw UnsupportedCookieOperationException(
        "Browsers cannot enumerate/delete every domain/path/HttpOnly cookie. Use server logout; " +
            "removeCookiesSetByThisManager() is the explicit limited alternative")

    /** Deletes only identities set through this manager; this is not an all-cookie logout API. */
    public suspend fun removeCookiesSetByThisManager() {
        val origin = window.location.origin
        if (owned.values.any { it.origin != origin }) throw UnsupportedCookieOperationException("The document origin changed")
        owned.values.forEach { (_, cookie) ->
            document.cookie = cookieHeader(cookie.copy(value = "", expiresDate = 0), "Thu, 01 Jan 1970 00:00:00 GMT")
        }
        owned.clear()
    }
}

private fun documentRequest(url: String): URL {
    val current = URL(window.location.href)
    val requested = URL(url, current.href)
    if (requested.origin != current.origin || requested.pathname != current.pathname) {
        throw UnsupportedCookieOperationException("document.cookie can only describe the current document's origin and request path")
    }
    require(requested.protocol == "https:" || requested.protocol == "http:") { "Cookie URL must be HTTP(S)" }
    return requested
}

internal expect fun cookieHttpDate(epochMillis: Double): String
