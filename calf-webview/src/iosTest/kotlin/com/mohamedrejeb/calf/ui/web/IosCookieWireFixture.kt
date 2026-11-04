// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)
package com.mohamedrejeb.calf.ui.web

import com.mohamedrejeb.calf.ui.web.internal.*
import kotlinx.cinterop.*
import kotlinx.coroutines.*
import platform.Foundation.*
import platform.WebKit.WKWebsiteDataStore
import platform.posix.getpid
import kotlin.coroutines.resume
import kotlin.test.*

/** The lead owns loopback/TLS/DNS/ATS/simulator leases. This helper never handles a private key or trust challenge. */
internal class IosCookieWireFixture : NativeCookieWireAdapter {
    private val environment = NSProcessInfo.processInfo.environment
    override val token = assertNotNull(environment["NATIVECMPKIT_COOKIE_WIRE_TOKEN"] as? String).also { CookieWireContract.prefix(it) }
    private val host = assertNotNull(environment["NATIVECMPKIT_COOKIE_WIRE_HOST"] as? String).also {
        assertTrue(it == "r$token.nativecmpkit.test", "Missing exact nonce-owned native DNS alias")
    }
    private val ports = listOf("HTTP", "HTTPS").map { kind ->
        assertNotNull((environment["NATIVECMPKIT_COOKIE_WIRE_${kind}_PORT"] as? String)?.toIntOrNull())
            .also { assertTrue(it in 1..65535) }
    }
    private val pid = getpid()
    private val numbers = mutableMapOf<String, Int>()
    private var ui: NativeApplicationUiTest? = null
    private var state: WebViewState? = null
    private var navigator: WebViewNavigator? = null
    init {
        assertFalse(NSThread.isMainThread)
        assertNotEquals(ports[0], ports[1])
        assertTrue((environment["NATIVECMPKIT_COOKIE_WIRE_SELECTOR"] as? String) ==
            "com.mohamedrejeb.calf.ui.web.IosCookieWireAcceptanceTest.realWkScopedCookieHeadersKeepNativeMultiplicityAcrossHttpAndTrustedHttps")
        assertEquals(1, control("open").getValue("open"))
    }
    fun bind(ui: NativeApplicationUiTest, state: WebViewState, navigator: WebViewNavigator) {
        check(this.ui == null) { "Never replay a native cookie composition lease" }
        this.ui = ui; this.state = state; this.navigator = navigator
        ui.runOnIdle {
            assertTrue(sameNativeObject(assertNotNull(state.webView).configuration.websiteDataStore, WKWebsiteDataStore.defaultDataStore()),
                "The actual native WebView and public CookieManager must share the real default store")
        }
    }
    override fun url(page: String, subhost: Boolean, secure: Boolean): String {
        check(page in CookieWireContract.pages)
        return base(subhost, secure) + CookieWireContract.rootPath(token) + page
    }
    private fun base(subhost: Boolean, secure: Boolean) = "${if (secure) "https" else "http"}://${if (subhost) "sub." else ""}$host:${ports[if (secure) 1 else 0]}"
    private fun stage(page: String, subhost: Boolean, secure: Boolean) =
        "${if (secure) "https" else "http"}-${if (subhost) "sub" else "root"}-${page.replace('/', '-')}"
    override suspend fun seed() = load(base(false, true) + CookieWireContract.rootPath(token) + "seed", "cookie-seed-1")
    override suspend fun logout() = load(base(false, true) + CookieWireContract.rootPath(token) + "logout", "cookie-logout-1")
    override suspend fun observe(page: String, subhost: Boolean, secure: Boolean): NativeCookieWireObservation {
        val stage = stage(page, subhost, secure)
        val number = (numbers[stage] ?: 0) + 1; numbers[stage] = number
        load(url(page, subhost, secure), "cookie-$stage-$number")
        return NativeCookieWireObservation(vector("cookie-wire"), vector("cookie-visible"))
    }
    private fun load(url: String, title: String) {
        val ui = checkNotNull(ui); val state = checkNotNull(state); val navigator = checkNotNull(navigator)
        ui.runOnIdle { navigator.loadUrl(url) }
        ui.waitForNative {
            val native = state.webView
            native != null && !native.loading && native.title == title && native.URL?.absoluteString == url &&
                state.pageTitle == title && state.lastLoadedUrl == url && state.loadingState == LoadingState.Finished &&
                sameNativeObject(native.window, requireOwnedApplicationWindow())
        }
        assertTrue(evaluate("document.title") == JavascriptResult.Value(quoteJavascript(title)), "Read the actual loaded native title")
        assertEquals(JavascriptResult.Value("\"text/html\""), evaluate("document.contentType"))
        ui.runOnIdle { assertTrue(state.errorsForCurrentRequest.isEmpty(), "Native DNS/ATS/TLS errors cannot be hidden by a count-vector assertion") }
    }
    private fun vector(element: String): List<Int> {
        check(element in listOf("cookie-wire", "cookie-visible"))
        val result = evaluate("document.getElementById('$element').textContent")
        assertTrue(result is JavascriptResult.Value, "Missing actual native document cookie count vector")
        val json = (result as JavascriptResult.Value).json
        assertTrue(Regex("\"[0-3](,[0-3]){11}\"").matches(json), "Native document cookie receipt must contain only fixed numeric counts")
        return CookieWireContract.parseVector(json.removeSurrounding("\""))
    }
    private fun evaluate(script: String): JavascriptResult {
        assertFalse(NSThread.isMainThread)
        val ui = checkNotNull(ui); val state = checkNotNull(state)
        var result: JavascriptResult? = null
        var calls = 0
        var offMain = false
        state.evaluateJavascriptResult(script) { if (!NSThread.isMainThread) offMain = true; calls++; result = it }
        ui.waitForNative { result != null || offMain }
        return onApplicationMain { assertFalse(offMain); assertEquals(1, calls); assertNotNull(result) }
    }
    fun complete() { assertEquals(1, control("done").getValue("done")) }
    private fun control(action: String): Map<String, Int> = memScoped {
        assertFalse(NSThread.isMainThread, "Never block UIApplicationMain with native fixture control")
        check(action in listOf("open", "stats", "done"))
        val response = alloc<ObjCObjectVar<NSURLResponse?>>().apply { value = null }
        val failure = alloc<ObjCObjectVar<NSError?>>().apply { value = null }
        val request = NSMutableURLRequest().apply {
            setURL(assertNotNull(NSURL.URLWithString("http://localhost:${ports[0]}${CookieWireContract.rootPath(token)}control/$action/$pid")))
            setTimeoutInterval(2.0)
        }
        val data = NSURLConnection.sendSynchronousRequest(request, response.ptr, failure.ptr)
        assertTrue(failure.value == null, "Owned cookie control failed; nativeCode=${failure.value?.code}")
        assertEquals(200L, (response.value as? NSHTTPURLResponse)?.statusCode, "Owned native cookie process control refused")
        val body = assertNotNull(data)
        assertTrue(body.length in 1uL..2048uL)
        val text = assertNotNull(body.bytes).reinterpret<ByteVar>().readBytes(body.length.toInt()).decodeToString()
        val result = mutableMapOf<String, Int>()
        text.trimEnd('\n').split('\n').forEach { line ->
            assertTrue(Regex("[a-z_]+=[0-9]{1,10}").matches(line), "Unreviewed native cookie process record")
            val (key, value) = line.split('=')
            assertTrue(key !in result, "Duplicate native cookie process record")
            result[key] = assertNotNull(value.toIntOrNull())
        }
        assertEquals(setOf(action, "pid", "fixture_error", "pending"), result.keys)
        assertEquals(pid, result.getValue("pid")); assertEquals(0, result.getValue("fixture_error"))
        result
    }
    private suspend fun allCookies(): List<NSHTTPCookie> = withTimeout(5_000) { withContext(Dispatchers.Main) {
        suspendCancellableCoroutine { continuation ->
            WKWebsiteDataStore.defaultDataStore().httpCookieStore.getAllCookies { cookies ->
                if (continuation.isActive) continuation.resume(cookies.orEmpty().filterIsInstance<NSHTTPCookie>())
            }
        }
    } }
    suspend fun foreignStoreSnapshot(requireFresh: Boolean = false): List<ForeignCookieIdentity> {
        val current = allCookies()
        if (requireFresh) assertTrue(current.none { it.name.startsWith(CookieWireContract.prefix(token)) },
            "Refuse reusing a cookie namespace already present anywhere in the full native store")
        return current.filterNot { owned(it) }.map { native -> ForeignCookieIdentity(native.name, native.value, native.domain, native.path,
            native.expiresDate?.timeIntervalSince1970, native.isSecure(), native.isHTTPOnly()) }
        .sortedWith(compareBy<ForeignCookieIdentity> { it.name }.thenBy { it.domain }.thenBy { it.path }.thenBy { it.value })
    }
    private fun owned(cookie: NSHTTPCookie): Boolean = cookie.name.startsWith(CookieWireContract.prefix(token)) &&
        cookie.domain.removePrefix(".") in listOf(host, "sub.$host") &&
        cookie.path.startsWith(CookieWireContract.rootPath(token))
    suspend fun removeOwnedCookies() = withContext(NonCancellable) {
        var failure: Throwable? = null
        for (cookie in allCookies().filter { owned(it) }) {
            try { withTimeout(5_000) { withContext(Dispatchers.Main) {
                suspendCancellableCoroutine<Unit> { continuation ->
                    WKWebsiteDataStore.defaultDataStore().httpCookieStore.deleteCookie(cookie) {
                        if (continuation.isActive) continuation.resume(Unit)
                    }
                }
            } } } catch (error: Throwable) { if (failure == null) failure = error else if (failure !== error) failure.addSuppressed(error) }
        }
        try { assertTrue(allCookies().none { owned(it) }, "Exact nonce-owned native cookie deletion did not actually complete") }
        catch (error: Throwable) { if (failure == null) failure = error else if (failure !== error) failure.addSuppressed(error) }
        failure?.let { throw it }
    }
}

/** Private in-memory equality only; never interpolate or export these fields in a failure/receipt. */
internal data class ForeignCookieIdentity(val name: String, val value: String, val domain: String, val path: String,
                                        val expiry: Double?, val secure: Boolean, val httpOnly: Boolean)
