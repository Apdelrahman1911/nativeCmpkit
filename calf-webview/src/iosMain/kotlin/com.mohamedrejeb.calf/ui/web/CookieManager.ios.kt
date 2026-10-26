// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import platform.Foundation.*
import platform.WebKit.WKHTTPCookieStore
import platform.WebKit.WKWebsiteDataStore
import kotlin.coroutines.resume

/** Owns no global store; all WKHTTPCookieStore operations are confined to the main dispatcher. */
public actual class CookieManager actual constructor() {
    private val httpCookieStore: WKHTTPCookieStore
        get() = WKWebsiteDataStore.defaultDataStore().httpCookieStore

    public actual suspend fun setCookie(url: String, cookie: Cookie): Unit = withContext(Dispatchers.Main) {
        val request = cookieUrl(url)
        validateCookieHost(cookie, request.host!!, request.scheme.equals("https", true))
        val expires = cookie.expiresDate?.let { epoch ->
            NSDateFormatter().apply {
                locale = NSLocale(localeIdentifier = "en_US_POSIX")
                timeZone = NSTimeZone.timeZoneForSecondsFromGMT(0)
                dateFormat = "EEE, dd MMM yyyy HH:mm:ss 'GMT'"
            }.stringFromDate(NSDate.dateWithTimeIntervalSince1970(epoch / 1000.0))
        }
        val header = cookieHeader(cookie.copy(path = cookie.path ?: defaultCookiePath(request.path.orEmpty())), expires)
        val native = NSHTTPCookie.cookiesWithResponseHeaderFields(mapOf("Set-Cookie" to header), request)
            .filterIsInstance<NSHTTPCookie>().singleOrNull()
            ?: throw IllegalArgumentException("Foundation rejected the cookie attributes")
        suspendCancellableCoroutine<Unit> { continuation ->
            httpCookieStore.setCookie(native) { if (continuation.isActive) continuation.resume(Unit) }
        }
    }

    public actual suspend fun getCookies(url: String): List<Cookie> = withContext(Dispatchers.Main) {
        val request = cookieUrl(url)
        val now = NSDate().timeIntervalSince1970
        allCookies().filter { native ->
            // Apple does not expose an independent RFC host-only flag here. A leading-dot domain
            // permits suffixes; a bare domain is conservatively exact, never over-exposes cookies.
            cookieMatchesRequest(request.host!!, request.path.orEmpty(), request.scheme.equals("https", true),
                native.domain, native.path, native.isSecure(), !native.domain.startsWith('.')) &&
                (native.expiresDate?.timeIntervalSince1970?.let { it > now } ?: true)
        }.map { native ->
            Cookie(native.name, native.value, native.domain, native.path,
                native.expiresDate?.timeIntervalSince1970?.let { (it * 1000).toLong() }, native.isSecure(), native.isHTTPOnly())
        }
    }

    public actual suspend fun removeAllCookies(): Unit = withContext(Dispatchers.Main) {
        allCookies().forEach { cookie ->
            suspendCancellableCoroutine<Unit> { continuation ->
                httpCookieStore.deleteCookie(cookie) { if (continuation.isActive) continuation.resume(Unit) }
            }
        }
    }

    private suspend fun allCookies(): List<NSHTTPCookie> = suspendCancellableCoroutine { continuation ->
        httpCookieStore.getAllCookies { cookies ->
            if (continuation.isActive) continuation.resume(cookies.filterIsInstance<NSHTTPCookie>())
        }
    }
}

private fun cookieUrl(url: String): NSURL {
    val parsed = NSURL.URLWithString(url)
    require(parsed?.host != null && (parsed.scheme.equals("https", true) || parsed.scheme.equals("http", true))) {
        "Cookie URL must be absolute HTTP(S)"
    }
    return parsed
}
