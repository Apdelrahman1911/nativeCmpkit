// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import java.net.CookieHandler
import java.net.HttpCookie
import java.net.URI
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.IdentityHashMap

/**
 * Adapts the existing handler without ever replacing application/JavaFX global state. JavaFX's
 * handler is NOT a java.net.CookieManager. Generic handlers expose request Cookie headers only;
 * their metadata and full-store deletion cannot be recovered through the public CookieHandler API.
 */
public actual class CookieManager actual constructor() {
    private var explicitHandler: CookieHandler? = null
    private data class KnownCookie(val host: String, val hostOnly: Boolean, val expiry: Long?)
    private val known = IdentityHashMap<HttpCookie, KnownCookie>()

    /** Opt-in backend ownership; this does not install the supplied handler globally. */
    constructor(handler: CookieHandler) : this() { explicitHandler = handler }

    private fun handler(): CookieHandler = explicitHandler ?: CookieHandler.getDefault()
        ?: throw UnsupportedCookieOperationException("Initialize JavaFX or explicitly supply a CookieHandler before using desktop cookies")

    public actual suspend fun setCookie(url: String, cookie: Cookie) {
        val uri = requestUri(url)
        validateCookieHost(cookie, uri.host, uri.scheme.equals("https", true))
        val handler = handler()
        synchronized(handler) {
            if (handler is java.net.CookieManager) {
                val native = HttpCookie(cookie.name, cookie.value).apply {
                    version = 0
                    // A null domain preserves host-only ownership in the URI-associated store.
                    domain = cookie.domain?.let { ".${it.removePrefix(".")}" }
                    path = cookie.path ?: defaultCookiePath(uri.path.orEmpty())
                    secure = cookie.isSecure
                    isHttpOnly = cookie.isHttpOnly
                    maxAge = cookie.expiresDate?.let {
                        val remaining = it - System.currentTimeMillis()
                        if (remaining <= 0) 0 else (remaining + 999) / 1000
                    } ?: -1
                }
                handler.cookieStore.add(uri, native)
                pruneKnown(handler)
                known[native] = KnownCookie(uri.host, cookie.domain == null, cookie.expiresDate)
            } else {
                val expiry = cookie.expiresDate?.let {
                    DateTimeFormatter.RFC_1123_DATE_TIME.format(Instant.ofEpochMilli(it).atZone(ZoneOffset.UTC))
                }
                handler.put(uri, mapOf("Set-Cookie" to listOf(cookieHeader(cookie.copy(path = cookie.path ?: defaultCookiePath(uri.path.orEmpty())), expiry))))
            }
        }
    }

    public actual suspend fun getCookies(url: String): List<Cookie> {
        val uri = requestUri(url)
        val handler = handler()
        return synchronized(handler) {
            // The handler applies its own request-path/secure/domain semantics, including JavaFX.
            val sent = handler.get(uri, emptyMap()).filterKeys { it.equals("Cookie", true) || it.equals("Cookie2", true) }
                .values.flatten().flatMap(::parseCookieHeader)
            if (handler !is java.net.CookieManager) return@synchronized sent
            pruneKnown(handler)
            val now = System.currentTimeMillis()
            handler.cookieStore.get(uri).filter { native ->
                val metadata = known[native]
                !native.hasExpired() && (metadata?.expiry == null || metadata.expiry > now) &&
                    sent.any { it.name == native.name && it.value == native.value } &&
                    cookieMatchesRequest(uri.host, uri.path.orEmpty(), uri.scheme.equals("https", true),
                        native.domain ?: metadata?.host ?: uri.host, native.path ?: "/", native.secure,
                        metadata?.hostOnly ?: (native.domain == null))
            }.map { native ->
                Cookie(native.name, native.value, native.domain, native.path,
                    known[native]?.expiry, native.secure, native.isHttpOnly)
            }
        }
    }

    public actual suspend fun removeAllCookies() {
        val handler = handler()
        synchronized(handler) {
            if (handler !is java.net.CookieManager) throw UnsupportedCookieOperationException(
                "The active CookieHandler cannot enumerate/delete its whole store; use its owning application's logout API")
            handler.cookieStore.removeAll()
            known.clear()
        }
    }

    private fun pruneKnown(handler: java.net.CookieManager) {
        val live = handler.cookieStore.cookies
        known.keys.removeAll { key -> live.none { it === key } }
    }
}

private fun requestUri(url: String): URI = URI(url).also {
    require(it.host != null && (it.scheme.equals("https", true) || it.scheme.equals("http", true))) { "Cookie URL must be absolute HTTP(S)" }
}
