// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import kotlinx.browser.document
import kotlinx.browser.window
import kotlinx.coroutines.*
import kotlinx.coroutines.test.runTest
import org.w3c.xhr.XMLHttpRequest
import kotlin.random.Random
import kotlin.test.*

/** NEW missing-only #69. Each actual engine must execute this body; compilation/Chromium is not WebKit proof. */
class BrowserCookieWireAcceptanceTest {
    @Test fun realScopedDuplicateSessionAndExpiryCookiesRequireServerHttpOnlyLogout() = runTest {
        withContext(Dispatchers.Default) {
            val fixture = BrowserCookieWireFixture()
            val manager = CookieManager()
            val originalHref = window.location.href
            val originalState = window.history.state
            val foreignVisible = document.cookie // In-memory only; never included in assertion output/receipts.
            var primary: Throwable? = null
            try {
                fixture.open()
                fixture.seed()
                for (page in CookieWireContract.pages) {
                    window.history.replaceState(originalState, "", fixture.url(page))
                    assertEquals(CookieWireContract.expected(page, false, false), fixture.read(page),
                        "Real browser HTTP header lost a same-name/path occurrence or scope boundary")
                    assertEquals(CookieWireContract.expected(page, false, false, visibleOnly = true),
                        CookieWireContract.vector(manager.getCookies(fixture.url(page)), fixture.token),
                        "document.cookie visibility differs from the current real document path")
                }
                window.history.replaceState(originalState, "", fixture.url("foo/child"))
                for (page in listOf("foo", "public")) {
                    assertEquals(CookieWireContract.expected(page, true, false), fixture.read(page, subhost = true),
                        "Actual credentialed subdomain request must contain only the explicit Domain cookie")
                }
                assertFailsWith<UnsupportedCookieOperationException> { manager.getCookies(fixture.url("foo")) }
                assertFailsWith<UnsupportedCookieOperationException> { manager.getCookies(fixture.url("foo/child", subhost = true)) }
                assertFailsWith<UnsupportedCookieOperationException> {
                    manager.setCookie(fixture.url("foo"), fixture.managed())
                }

                // Managed session -> future -> past -> session writes use real document.cookie,
                // and each step is witnessed by the server's ACTUAL incoming Cookie header.
                val current = fixture.url("foo/child")
                manager.setCookie(current, fixture.managed())
                assertNull(manager.getCookies(current).single { it.name == fixture.managed().name }.expiresDate)
                fixture.assertManaged(true)
                manager.setCookie(current, fixture.managed().copy(expiresDate = 4_102_444_800_000L))
                fixture.assertManaged(true)
                manager.setCookie(current, fixture.managed().copy(expiresDate = 0))
                fixture.assertManaged(false)
                manager.setCookie(current, fixture.managed())
                fixture.assertManaged(true)

                assertFailsWith<UnsupportedCookieOperationException> {
                    manager.setCookie(current, fixture.managed().copy(isHttpOnly = true))
                }
                for (invalid in listOf(
                    fixture.managed().copy(name = fixture.managed().name + ";injected"),
                    fixture.managed().copy(value = "managed;injected=value"),
                    fixture.managed().copy(value = "managed\r\nSet-Cookie: injected=value"),
                    fixture.managed().copy(domain = fixture.host + ";injected=value"),
                    fixture.managed().copy(path = CookieWireContract.rootPath(fixture.token) + ";injected=value"),
                )) assertFailsWith<IllegalArgumentException> { manager.setCookie(current, invalid) }
                fixture.assertManaged(true)
                assertFailsWith<UnsupportedCookieOperationException> { manager.removeAllCookies() }
                fixture.assertManaged(true) // Unsupported all-jar deletion cannot silently log out or mutate anything.
                manager.removeCookiesSetByThisManager()
                fixture.assertManaged(false) // Server HttpOnly auth remains 1 in this full vector.
                assertEquals(CookieWireContract.expected("foo/child", false, false, visibleOnly = true),
                    CookieWireContract.vector(manager.getCookies(current), fixture.token))

                fixture.logout() // Server expires every OWNED path/domain identity, including HttpOnly.
                for (page in CookieWireContract.pages) {
                    window.history.replaceState(originalState, "", fixture.url(page))
                    assertEquals(CookieWireContract.expected(page, false, false, loggedOut = true), fixture.read(page))
                    assertEquals(List(12) { 0 }, CookieWireContract.vector(manager.getCookies(fixture.url(page)), fixture.token))
                }
                assertEquals(List(12) { 0 }, fixture.read("foo/child", subhost = true))
                fixture.complete()
            } catch (error: Throwable) { primary = error; throw error }
            finally {
                runCookieWireCleanup(primary,
                    { manager.removeCookiesSetByThisManager() },
                    { fixture.close() },
                    { window.history.replaceState(originalState, "", originalHref) },
                    { assertTrue(window.location.href == originalHref, "Restore the exact original document URL") },
                    { assertTrue(document.cookie == foreignVisible, "Foreign visible cookies must remain unchanged; values are not exported") },
                )
            }
        }
    }
}

/** XHR transport uses genuine native credential handling. There is intentionally NO setRequestHeader call. */
private class BrowserCookieWireFixture {
    val token = Random.nextBytes(16).joinToString("") { (it.toInt() and 255).toString(16).padStart(2, '0') }
    private val owner = Random.nextBytes(16).joinToString("") { (it.toInt() and 255).toString(16).padStart(2, '0') }
    val host = window.location.hostname.also {
        assertEquals("http:", window.location.protocol)
        assertTrue(Regex("r[0-9a-f]{32}\\.nativecmpkit\\.test").matches(it), "Missing explicitly owned cookie-wire DNS alias")
        assertTrue(window.location.port.isNotEmpty(), "Missing actual Karma listener port")
    }
    private val origin = window.location.origin
    private var attemptedOpen = false
    private var completed = false
    fun url(page: String, subhost: Boolean = false): String {
        assertTrue(page in CookieWireContract.pages)
        val base = if (subhost) "http://sub.$host:${window.location.port}" else origin
        return base + CookieWireContract.rootPath(token) + page
    }
    fun managed() = Cookie(CookieWireContract.name(token, "managed"), "managed", path = CookieWireContract.rootPath(token))
    suspend fun open() {
        check(!attemptedOpen) { "Never replay an owned cookie session" }
        attemptedOpen = true // A response can fail AFTER the real server acquired its lease.
        control("control/open/$owner", "open")
    }
    suspend fun seed() = control("seed", "seed")
    suspend fun logout() = control("logout", "logout")
    suspend fun complete() { control("control/done/$owner", "done"); completed = true }
    suspend fun close() { if (attemptedOpen && !completed) { control("control/close/$owner", "close"); completed = true } }
    suspend fun read(page: String, subhost: Boolean = false): List<Int> {
        val text = request(url(page, subhost))
        val prefix = "cookie-wire|$token|"
        assertTrue(text.startsWith(prefix), "Missing exact nonce-owned native cookie receipt")
        return CookieWireContract.parseVector(text.removePrefix(prefix))
    }
    suspend fun assertManaged(present: Boolean) {
        assertEquals(CookieWireContract.expected("foo/child", false, false, managed = present), read("foo/child"),
            "Actual browser transport must witness the session/expiry/write/delete transition and retain HttpOnly")
    }
    private suspend fun control(route: String, action: String) {
        val text = request(origin + CookieWireContract.rootPath(token) + route)
        assertTrue(text == "cookie-control|$token|$action|1", "Missing exact nonce-owned control completion")
    }
    private suspend fun request(url: String): String {
        val native = XMLHttpRequest()
        val result = CompletableDeferred<String>()
        val load = browserEventListener { event ->
            if (!event.isTrusted || native.status.toInt() != 200 || native.responseText.length > 2048)
                result.completeExceptionally(AssertionError("Owned cookie request failed its real status/size/trust contract"))
            else result.complete(native.responseText)
        }
        val failure = browserEventListener { result.completeExceptionally(AssertionError("Owned cookie XHR failed or timed out")) }
        var primary: Throwable? = null
        try {
            native.open("GET", url, true)
            native.withCredentials = true
            native.timeout = 3000
            native.addEventListener("load", load)
            for (event in listOf("error", "timeout", "abort")) native.addEventListener(event, failure)
            native.send()
            return withTimeout(5_000) { result.await() }
        } catch (error: Throwable) { primary = error; throw error }
        finally {
            runWebViewCleanup(primary,
                { native.removeEventListener("load", load) },
                { for (event in listOf("error", "timeout", "abort")) native.removeEventListener(event, failure) },
                { if (native.readyState.toInt() != 4) native.abort() },
            )
        }
    }
}
