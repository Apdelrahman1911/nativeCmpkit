// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import android.webkit.CookieManager as AndroidCookieManager
import android.net.Uri
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlin.coroutines.resume

/**
 * Android implementation of [CookieManager] using [android.webkit.CookieManager].
 */
public actual class CookieManager actual constructor() {

    private val cookieManager: AndroidCookieManager
        get() = AndroidCookieManager.getInstance()

    /**
     * Sets a cookie for the given URL.
     *
     * The cookie is converted to a Set-Cookie header string and passed to
     * [AndroidCookieManager.setCookie].
     *
     * @param url The URL for which the cookie is to be set.
     * @param cookie The [Cookie] to set.
     */
    public actual suspend fun setCookie(url: String, cookie: Cookie) {
        val uri = Uri.parse(url)
        require(uri.host != null && (uri.scheme.equals("http", true) || uri.scheme.equals("https", true))) { "Cookie URL must be absolute HTTP(S)" }
        validateCookieHost(cookie, uri.host!!, uri.scheme.equals("https", true))
        withContext(Dispatchers.Main) {
            val cookieString = buildCookieString(cookie.copy(path = cookie.path ?: defaultCookiePath(uri.path.orEmpty())))
            suspendCancellableCoroutine { continuation ->
                cookieManager.setCookie(url, cookieString) { accepted ->
                    if (continuation.isActive) {
                        if (accepted) continuation.resume(Unit)
                        else continuation.resumeWithException(IllegalStateException("Android rejected the cookie write"))
                    }
                }
            }
            cookieManager.flush()
        }
    }

    /**
     * Gets all cookies for the given URL.
     *
     * @param url The URL for which cookies are to be retrieved.
     * @return A list of [Cookie] objects associated with the URL.
     */
    public actual suspend fun getCookies(url: String): List<Cookie> {
        return withContext(Dispatchers.Main) {
            val cookieString = cookieManager.getCookie(url) ?: return@withContext emptyList()
            parseCookies(cookieString)
        }
    }

    /**
     * Removes all cookies.
     */
    public actual suspend fun removeAllCookies() {
        withContext(Dispatchers.Main) {
            suspendCancellableCoroutine { continuation ->
                cookieManager.removeAllCookies {
                    continuation.resume(Unit)
                }
            }
            cookieManager.flush()
        }
    }
}

/**
 * Builds a Set-Cookie header string from a [Cookie] object.
 */
private fun buildCookieString(cookie: Cookie): String {
    val expires = cookie.expiresDate?.let { epoch ->
        SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss 'GMT'", Locale.US).apply {
            timeZone = TimeZone.getTimeZone("GMT")
        }.format(Date(epoch))
    }
    return cookieHeader(cookie, expires)
}

/**
 * Parses a cookie header string (as returned by [AndroidCookieManager.getCookie])
 * into a list of [Cookie] objects.
 *
 * The cookie string format is "name1=value1; name2=value2; ...".
 */
private fun parseCookies(cookieString: String): List<Cookie> = parseCookieHeader(cookieString)
