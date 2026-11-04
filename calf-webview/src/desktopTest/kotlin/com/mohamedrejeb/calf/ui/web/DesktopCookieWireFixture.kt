// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import java.net.CookieHandler
import java.net.HttpURLConnection
import java.net.URI
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.security.KeyStore
import java.security.MessageDigest
import java.security.cert.CertificateFactory
import java.security.cert.X509Certificate
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManagerFactory
import kotlinx.coroutines.*
import kotlin.test.*

/** Owns only the library owner and strict process-local TLS lease. The lead owns servers/DNS/certificate material. */
internal class DesktopCookieWireFixture private constructor(
    override val token: String,
    private val host: String,
    private val ports: List<Int>,
    private val trust: CookieStrictTrustLease,
    private val view: JavaFxWebViewTest.Fixture,
    private val handler: CookieHandler,
) : NativeCookieWireAdapter, AutoCloseable {
    val manager = CookieManager() // Exercise the real public DEFAULT native handler path.
    private val cleanupManager = CookieManager(handler) // Cleanup cannot be redirected to a foreign replacement.
    private val pid = ProcessHandle.current().pid()
    private val numbers = mutableMapOf<String, Int>()
    private val knownUrls = listOf(false, true).flatMap { secure -> listOf(false, true).flatMap { subhost ->
        CookieWireContract.pages.map { url(it, subhost, secure) }
    } }
    // Relevant request-jar snapshots only: generic JavaFX CookieHandler cannot enumerate ALL domains.
    // No foreign raw names/values are ever included in assertion output or public receipts.
    private val foreignBefore = knownUrls.map { foreignPairs(it) }
    private var closed = false
    init {
        check(pid in 1 until Int.MAX_VALUE.toLong()) { "Missing canonical actual native JVM process" }
        for (url in knownUrls) assertTrue(handler.get(URI(url), emptyMap()).filterKeys {
            it.equals("Cookie", true) || it.equals("Cookie2", true)
        }.values.flatten().flatMap(::parseCookieHeader).none { it.name.startsWith(CookieWireContract.prefix(token)) },
            "Refuse reusing a cookie namespace already present in the native request jar")
        control("open")
    }
    override fun url(page: String, subhost: Boolean, secure: Boolean): String {
        require(page in CookieWireContract.pages)
        return base(subhost, secure) + CookieWireContract.rootPath(token) + page
    }
    private fun base(subhost: Boolean, secure: Boolean) = "${if (secure) "https" else "http"}://${if (subhost) "sub." else ""}$host:${ports[if (secure) 1 else 0]}"
    private fun stage(page: String, subhost: Boolean, secure: Boolean) =
        "${if (secure) "https" else "http"}-${if (subhost) "sub" else "root"}-${page.replace('/', '-')}"
    override suspend fun seed() = load(base(false, true) + CookieWireContract.rootPath(token) + "seed", "cookie-seed-1")
    override suspend fun logout() = load(base(false, true) + CookieWireContract.rootPath(token) + "logout", "cookie-logout-1")
    override suspend fun observe(page: String, subhost: Boolean, secure: Boolean): NativeCookieWireObservation {
        val stage = stage(page, subhost, secure)
        val number = (numbers[stage] ?: 0) + 1
        numbers[stage] = number
        load(url(page, subhost, secure), "cookie-$stage-$number")
        val text = onFxThread {
            val engine = assertNotNull(view.state.webView).engine
            listOf("cookie-wire", "cookie-visible").map { name ->
                engine.executeScript("document.getElementById('$name').textContent") as? String
                    ?: error("Missing authored actual native cookie count vector")
            }
        }
        return NativeCookieWireObservation(CookieWireContract.parseVector(text[0]), CookieWireContract.parseVector(text[1]))
    }
    private suspend fun load(url: String, title: String) {
        trust.assertInstalled()
        assertSame(handler, CookieHandler.getDefault(), "Public cookie reads must preserve the actual native global handler")
        view.state.settings.javaScriptEnabled = true
        view.owner.load(WebContent.Url(url))
        withTimeout(10_000) {
            while (!onFxThread {
                val engine = assertNotNull(view.state.webView).engine
                view.state.loadingState == LoadingState.Finished && view.state.lastLoadedUrl == url &&
                    engine.title == title && view.state.pageTitle == title && engine.executeScript("document.title") == title
            }) delay(10)
        }
        assertEquals("text/html", onFxThread { assertNotNull(view.state.webView).engine.executeScript("document.contentType") })
        assertTrue(view.state.errorsForCurrentRequest.isEmpty(), "Actual HTTP(S) cookie page must not hide native navigation/TLS errors")
        trust.assertInstalled()
        assertSame(handler, CookieHandler.getDefault())
    }
    fun complete() { assertEquals(1, control("done").getValue("done")); assertSame(handler, CookieHandler.getDefault()) }
    private fun control(action: String): Map<String, Int> {
        check(action in listOf("open", "stats", "done"))
        val connection = URI("http://localhost:${ports[0]}${CookieWireContract.rootPath(token)}control/$action/$pid")
            .toURL().openConnection() as HttpURLConnection
        var primary: Throwable? = null
        try {
            connection.requestMethod = "GET"
            connection.connectTimeout = 2000; connection.readTimeout = 2000; connection.instanceFollowRedirects = false
            assertEquals(200, connection.responseCode, "Owned native cookie process control refused")
            val bytes = connection.inputStream.use { it.readNBytes(2049) }
            assertTrue(bytes.size in 1..2048, "Owned native control exceeds its numeric protocol")
            val rows = mutableMapOf<String, Int>()
            bytes.toString(Charsets.US_ASCII).trimEnd('\n').split('\n').forEach { line ->
                assertTrue(Regex("[a-z_]+=[0-9]{1,10}").matches(line), "Unreviewed native cookie process record")
                val (key, value) = line.split('=')
                assertTrue(key !in rows, "Duplicate native cookie process record")
                rows[key] = assertNotNull(value.toIntOrNull())
            }
            assertEquals(setOf(action, "pid", "fixture_error", "pending"), rows.keys)
            assertEquals(pid, rows.getValue("pid").toLong()); assertEquals(0, rows.getValue("fixture_error"))
            return rows
        } catch (error: Throwable) { primary = error; throw error }
        finally { runWebViewCleanup(primary, { connection.disconnect() }) }
    }
    private fun foreignPairs(url: String): List<Pair<String, String>> = handler.get(URI(url), emptyMap())
        .filterKeys { it.equals("Cookie", true) || it.equals("Cookie2", true) }.values.flatten().flatMap(::parseCookieHeader)
        .filterNot { it.name.startsWith(CookieWireContract.prefix(token)) }.map { it.name to it.value }
        .sortedWith(compareBy<Pair<String, String>> { it.first }.thenBy { it.second })
    override fun close() {
        if (closed) return
        closed = true
        runWebViewCleanup(null,
            { runBlocking { cleanupCookies() } },
            { assertTrue(knownUrls.map { foreignPairs(it) } == foreignBefore, "Relevant foreign request-jar values must remain unchanged; no raw values are exported") },
            { view.close() },
            { assertNull(view.state.webView); assertEquals(1, view.disposedCalls) },
            { assertSame(handler, CookieHandler.getDefault(), "Disposal must not replace any application global cookie handler") },
            { trust.close() },
        )
    }
    private suspend fun cleanupCookies() {
        val root = CookieWireContract.rootPath(token)
        val entries = listOf(
            Cookie("scope", "", path = root), Cookie("scope", "", path = root + "foo"), Cookie("scope", "", path = root + "foo/child"),
            Cookie("scope", "", path = root + "private"),
            Cookie("host", "", path = root), Cookie("domain", "", domain = ".$host", path = root),
            Cookie("auth", "", path = root, isHttpOnly = true), Cookie("session", "", path = root),
            Cookie("future", "", path = root), Cookie("past", "", path = root), Cookie("secure", "", path = root, isSecure = true),
            Cookie("managed", "", path = root), Cookie("equal", "", path = root), Cookie("equal", "", path = root + "foo"),
        )
        var failure: Throwable? = null
        for (cookie in entries) {
            try { cleanupManager.setCookie(url("foo/child", false, true), cookie.copy(name = CookieWireContract.name(token, cookie.name), expiresDate = 0)) }
            catch (error: Throwable) { if (failure == null) failure = error else if (failure !== error) failure.addSuppressed(error) }
        }
        for (url in knownUrls) {
            try { assertTrue(cleanupManager.getCookies(url).none { it.name.startsWith(CookieWireContract.prefix(token)) }, "Owned native cookie deletion did not actually complete") }
            catch (error: Throwable) { if (failure == null) failure = error else if (failure !== error) failure.addSuppressed(error) }
        }
        failure?.let { throw it }
    }
    companion object {
        fun create(): DesktopCookieWireFixture {
            check(System.getProperty("nativecmpkit.desktop.cookie-wire.worker") == "one-selected-class") {
                "Native cookie TLS requires a fresh one-selected-class worker, not an ordinary shared Desktop profile"
            }
            val environment = System.getenv()
            check(environment["NATIVECMPKIT_COOKIE_WIRE_SELECTOR"] ==
                "com.mohamedrejeb.calf.ui.web.DesktopCookieWireAcceptanceTest.realJavaFxScopedCookieHeadersKeepNativeMultiplicityAcrossHttpAndTrustedHttps")
            val token = checkNotNull(environment["NATIVECMPKIT_COOKIE_WIRE_TOKEN"])
            CookieWireContract.prefix(token)
            val host = checkNotNull(environment["NATIVECMPKIT_COOKIE_WIRE_HOST"])
            check(host == "r$token.nativecmpkit.test") { "Missing exact nonce-owned native DNS alias" }
            val ports = listOf("HTTP", "HTTPS").map { kind ->
                checkNotNull(environment["NATIVECMPKIT_COOKIE_WIRE_${kind}_PORT"]?.toIntOrNull()).also { check(it in 1..65535) }
            }
            check(ports[0] != ports[1])
            var trust: CookieStrictTrustLease? = null
            var view: JavaFxWebViewTest.Fixture? = null
            try {
                val installed = CookieStrictTrustLease.create(environment).also { trust = it } // BEFORE JavaFX/HTTP2Loader initialization.
                val created = JavaFxWebViewTest.Fixture().also { view = it }
                val handler = assertNotNull(CookieHandler.getDefault())
                assertEquals("com.sun.webkit.network.CookieManager", handler.javaClass.name, "Use the genuine native JavaFX store")
                return DesktopCookieWireFixture(token, host, ports, installed, created, handler)
            } catch (primary: Throwable) {
                runWebViewCleanup(primary, { view?.close() }, { trust?.close() })
                throw primary
            }
        }
    }
}

/** Standard PKIX over ONE owned CA, unchanged hostname verification; restoration never overwrites a foreign replacement. */
private class CookieStrictTrustLease private constructor(private val strict: SSLContext) : AutoCloseable {
    private val originalContext = SSLContext.getDefault()
    private val originalFactory = HttpsURLConnection.getDefaultSSLSocketFactory()
    private val originalVerifier = HttpsURLConnection.getDefaultHostnameVerifier()
    private val installedFactory = strict.socketFactory
    private var contextInstalled = false
    private var factoryInstalled = false
    private var closed = false
    init {
        try {
            SSLContext.setDefault(strict); contextInstalled = true
            HttpsURLConnection.setDefaultSSLSocketFactory(installedFactory); factoryInstalled = true
            assertInstalled()
        } catch (primary: Throwable) { runWebViewCleanup(primary, { close() }) }
    }
    fun assertInstalled() {
        assertSame(strict, SSLContext.getDefault()); assertSame(installedFactory, HttpsURLConnection.getDefaultSSLSocketFactory())
        assertSame(originalVerifier, HttpsURLConnection.getDefaultHostnameVerifier(), "Never replace or disable hostname verification")
    }
    override fun close() {
        if (closed) return
        closed = true
        runWebViewCleanup(null,
            { if (contextInstalled) {
                check(SSLContext.getDefault() === strict) { "Preserve a foreign replacement SSLContext; refuse restoration" }
                SSLContext.setDefault(originalContext); assertSame(originalContext, SSLContext.getDefault())
            } },
            { if (factoryInstalled) {
                check(HttpsURLConnection.getDefaultSSLSocketFactory() === installedFactory) { "Preserve a foreign replacement socket factory; refuse restoration" }
                HttpsURLConnection.setDefaultSSLSocketFactory(originalFactory); assertSame(originalFactory, HttpsURLConnection.getDefaultSSLSocketFactory())
            } },
            { assertSame(originalVerifier, HttpsURLConnection.getDefaultHostnameVerifier()) },
        )
    }
    companion object {
        fun create(environment: Map<String, String>): CookieStrictTrustLease {
            val path = Path.of(checkNotNull(environment["NATIVECMPKIT_COOKIE_WIRE_CA"]))
            check(path.isAbsolute && Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(path) && Files.size(path) in 1L..16384L)
            val bytes = Files.readAllBytes(path)
            val expected = checkNotNull(environment["NATIVECMPKIT_COOKIE_WIRE_CA_SHA256"])
            check(Regex("[0-9a-f]{64}").matches(expected))
            val actual = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
            check(actual == expected) { "Owned CA bytes do not match the process-local original handoff" }
            val ca = bytes.inputStream().use { CertificateFactory.getInstance("X.509").generateCertificate(it) as X509Certificate }
            ca.checkValidity(); ca.verify(ca.publicKey)
            check(ca.basicConstraints >= 0 && ca.keyUsage?.getOrNull(5) == true) { "Owned anchor must be a genuine keyCertSign CA" }
            val anchors = KeyStore.getInstance(KeyStore.getDefaultType()).apply { load(null, null); setCertificateEntry("owned-cookie-fixture", ca) }
            val managers = TrustManagerFactory.getInstance("PKIX").apply { init(anchors) }
            val strict = SSLContext.getInstance("TLS").apply { init(null, managers.trustManagers, null) }
            return CookieStrictTrustLease(strict)
        }
    }
}
