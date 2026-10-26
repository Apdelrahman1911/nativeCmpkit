// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

/**
 * A cross-platform cookie manager for managing cookies in the WebView.
 *
 * Each platform wraps its native cookie management API:
 * - Android: `android.webkit.CookieManager`
 * - iOS: `WKHTTPCookieStore`
 * - Desktop: the existing `CookieHandler` (never silently replaced)
 * - JS/WasmJS: host document cookies only (not cross-origin iframe cookies)
 *
 * Invalid cookie tokens/attributes throw IllegalArgumentException. Unsupported operations throw
 * [UnsupportedCookieOperationException] rather than silently claiming success. Cookie write APIs
 * do not prove server authentication; policies may reject a write. Returned metadata varies.
 */
public expect class CookieManager() {
    /**
     * Sets a cookie for the given URL.
     *
     * @param url The URL for which the cookie is to be set.
     * @param cookie The [Cookie] to set.
     */
    public suspend fun setCookie(url: String, cookie: Cookie)

    /**
     * Gets cookies applicable to a request URL, not an unfiltered storage inventory.
     *
     * @param url The URL for which cookies are to be retrieved.
     * @return A list of [Cookie] objects associated with the URL.
     */
    public suspend fun getCookies(url: String): List<Cookie>

    /**
     * Removes all cookies only where the native store supports full enumeration/deletion.
     * Browser JavaScript and generic Desktop handlers throw UnsupportedCookieOperationException;
     * complete server/HttpOnly logout must be implemented by the owning application.
     */
    public suspend fun removeAllCookies()
}
