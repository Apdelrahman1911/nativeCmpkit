package com.mohamedrejeb.calf.ui.web

import com.sun.net.httpserver.HttpServer
import kotlinx.coroutines.*
import java.net.CookieHandler
import java.net.InetSocketAddress
import java.net.URI
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.test.*

/** Real production JavaFX owner/engine, loopback HTTP and native cookie jar.
 * No real-account login, HTTPS network/TLS certificate or browser-isolation claim. */
class JavaFxCookieIntegrationTest {
    private class HttpFixture(val authenticated: Boolean = false) : AutoCloseable {
        val view = JavaFxWebViewTest.Fixture()
        val handler = assertNotNull(CookieHandler.getDefault(), "Real JavaFX must have initialized its native cookie handler")
        val manager = CookieManager(handler)
        val id = UUID.randomUUID().toString().replace("-", "")
        val path = "/nativecmpkit-cookies-$id/"
        val sessionName = "session_$id"
        val visibleName = "visible_$id"
        val secureName = "secure_$id"
        val readHeaders = ConcurrentLinkedQueue<String>()
        private val ownedNames = mutableSetOf<String>()
        private val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        private val executor = Executors.newFixedThreadPool(2) { runnable ->
            Thread(runnable, "nativecmpkit-cookie-response").apply { isDaemon = true }
        }
        val base = "http://127.0.0.1:${server.address.port}$path"
        val readUrl = base + "read"
        val secureUrl = readUrl.replace("http:", "https:")
        init {
            server.executor = executor
            server.createContext(path + "login") { exchange ->
                try {
                    exchange.responseHeaders.add("Set-Cookie", "$sessionName=authenticated; Path=$path; HttpOnly")
                    exchange.responseHeaders.add("Set-Cookie", "$visibleName=public; Path=$path")
                    val bytes = "<html><title>login</title><body>authenticated fixture</body></html>".toByteArray()
                    exchange.responseHeaders.add("Content-Type", "text/html; charset=utf-8")
                    exchange.responseHeaders.add("Cache-Control", "no-store")
                    exchange.sendResponseHeaders(200, bytes.size.toLong())
                    exchange.responseBody.use { it.write(bytes) }
                } finally { exchange.close() }
            }
            server.createContext(path + "read") { exchange ->
                try {
                    val raw = exchange.requestHeaders.getFirst("Cookie").orEmpty()
                    readHeaders.add(raw)
                    val allowed = !authenticated || cookieValues(raw)[sessionName] == "authenticated"
                    val title = if (allowed) "read" else "denied"
                    val bytes = "<html><title>$title</title><body>native request</body></html>".toByteArray()
                    exchange.responseHeaders.add("Content-Type", "text/html; charset=utf-8")
                    exchange.responseHeaders.add("Cache-Control", "no-store")
                    exchange.sendResponseHeaders(if (allowed) 200 else 401, bytes.size.toLong())
                    exchange.responseBody.use { it.write(bytes) }
                } finally { exchange.close() }
            }
            server.start()
        }
        fun own(vararg names: String) { ownedNames.addAll(names) }
        suspend fun load(url: String, title: String) {
            view.state.settings.javaScriptEnabled = true
            view.owner.load(WebContent.Url(url))
            // A completed worker and title notifications are independent native events.
            withTimeout(10_000) {
                while (!onFxThread {
                    val engine = assertNotNull(view.state.webView).engine
                    view.state.loadingState == LoadingState.Finished && view.state.lastLoadedUrl == url &&
                        engine.executeScript("document.title") == title && engine.title == title && view.state.pageTitle == title
                }) delay(10)
            }
            assertEquals("text/html", onFxThread {
                assertNotNull(view.state.webView).engine.executeScript("document.contentType")
            }, "The fixture must really serve/render HTML, not an octet-stream download")
        }
        suspend fun documentCookies(): Map<String, String> = onFxThread {
            cookieValues(assertNotNull(view.state.webView).engine.executeScript("document.cookie") as String)
        }
        override fun close() {
            try {
                // Delete only this fixture's cookie identities, never the application's jar.
                runBlocking {
                    ownedNames.forEach { manager.setCookie(secureUrl, Cookie(it, "", path = path, expiresDate = 0)) }
                    assertTrue(manager.getCookies(secureUrl).none { it.name in ownedNames }, "Owned cookie cleanup must really complete")
                }
            } finally {
                server.stop(0)
                executor.shutdownNow()
                try { assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS), "Owned HTTP threads must terminate") }
                finally { view.close() }
            }
        }
    }

    @Test fun realNativeLoginSurvivesLibraryCookieReadsAndHttpOnlyNeverLeaksIntoDocumentCookie() = runBlocking<Unit> {
        HttpFixture(authenticated = true).use { fixture ->
            assertEquals("com.sun.webkit.network.CookieManager", fixture.handler.javaClass.name, "Exercise the actual JavaFX jar, not a JDK replacement")
            fixture.own(fixture.sessionName, fixture.visibleName, fixture.secureName)
            fixture.load(fixture.base + "login", "login")
            val manager = CookieManager() // Default-handler path that formerly replaced the native jar.
            val cookies = manager.getCookies(fixture.readUrl).associate { it.name to it.value }
            assertEquals("authenticated", cookies[fixture.sessionName])
            assertEquals("public", cookies[fixture.visibleName])
            assertSame(fixture.handler, CookieHandler.getDefault())
            manager.setCookie(fixture.secureUrl, Cookie(fixture.secureName, "secure", path = fixture.path, isSecure = true, isHttpOnly = true))
            assertFalse(manager.getCookies(fixture.readUrl).any { it.name == fixture.secureName })
            assertEquals("secure", manager.getCookies(fixture.secureUrl).single { it.name == fixture.secureName }.value)
            fixture.load(fixture.readUrl, "read") // Server requires the original real login cookie.
            val sent = cookieValues(assertNotNull(fixture.readHeaders.poll()))
            assertEquals("authenticated", sent[fixture.sessionName])
            assertEquals("public", sent[fixture.visibleName])
            assertFalse(fixture.secureName in sent, "Native HTTP request must not send a Secure cookie")
            val script = fixture.documentCookies()
            assertEquals("public", script[fixture.visibleName])
            assertFalse(fixture.sessionName in script, "HttpOnly session must stay unavailable to actual WebEngine JavaScript")
            assertFalse(fixture.secureName in script)
            assertSame(fixture.handler, CookieHandler.getDefault())
        }
    }

    @Test fun customHandlerInstalledBeforeANewNativeViewIsNeverReplacedByCreationReadsOrDisposal() = runBlocking<Unit> {
        // Initialize JavaFX under its ordinary jar first; this test covers a new view,
        // not a claim about a completely fresh JVM's dependency initialization.
        JavaFxWebViewTest.Fixture().use {
            val original = CookieHandler.getDefault()
            val jar = java.net.CookieManager()
            val custom = object : CookieHandler() {
                override fun get(uri: URI, headers: Map<String, List<String>>) = jar.get(uri, headers)
                override fun put(uri: URI, headers: Map<String, List<String>>) = jar.put(uri, headers)
            }
            try {
                CookieHandler.setDefault(custom)
                JavaFxWebViewTest.Fixture().use { second ->
                    assertSame(custom, CookieHandler.getDefault(), "Native view creation must preserve the application's handler")
                    val manager = CookieManager()
                    manager.setCookie("https://example.test/", Cookie("custom", "retained", path = "/"))
                    assertEquals("retained", manager.getCookies("https://example.test/").single().value)
                    second.owner.load(WebContent.Data("<html><title>custom</title><body>fixture</body></html>"))
                    onFxThread { assertNotNull(second.state.webView) }
                    assertSame(custom, CookieHandler.getDefault())
                    assertFailsWith<UnsupportedCookieOperationException> { manager.removeAllCookies() }
                    assertSame(custom, CookieHandler.getDefault())
                }
                assertSame(custom, CookieHandler.getDefault(), "Disposal must not swap the application's handler either")
            } finally { CookieHandler.setDefault(original) }
        }
    }

    @Test fun twoLibraryManagersConcurrentlyShareTheNativeJarAndActualEngineRequestsKeepEveryValue() = runBlocking<Unit> {
        HttpFixture().use { fixture ->
            val expected = (0 until 32).associate { "concurrent_${fixture.id}_$it" to "value_$it" }
            fixture.own(*expected.keys.toTypedArray())
            val managers = listOf(CookieManager(), CookieManager())
            coroutineScope {
                val start = CompletableDeferred<Unit>()
                val ready = CountDownLatch(2)
                val threads = ConcurrentHashMap.newKeySet<Long>()
                val writes = managers.mapIndexed { index, manager -> async(Dispatchers.Default) {
                    start.await()
                    threads.add(Thread.currentThread().id)
                    ready.countDown()
                    assertTrue(ready.await(5, TimeUnit.SECONDS), "Both real worker threads must overlap before cookie operations")
                    repeat(16) { local ->
                        val number = index * 16 + local
                        val name = "concurrent_${fixture.id}_$number"
                        manager.setCookie(fixture.readUrl, Cookie(name, "value_$number", path = fixture.path))
                        assertEquals("value_$number", manager.getCookies(fixture.readUrl).single { it.name == name }.value)
                        assertSame(fixture.handler, CookieHandler.getDefault())
                    }
                } }
                start.complete(Unit)
                writes.awaitAll()
                assertEquals(2, threads.size, "Two managers must really execute on distinct concurrently active workers")
            }
            for (manager in managers) {
                assertEquals(expected, manager.getCookies(fixture.readUrl).filter { it.name in expected }.associate { it.name to it.value })
            }
            fixture.load(fixture.readUrl, "read")
            val sent = cookieValues(assertNotNull(fixture.readHeaders.poll()))
            assertEquals(expected, sent.filterKeys { it in expected }, "Actual native HTTP headers must contain all concurrently stored values")
            assertEquals(expected, fixture.documentCookies().filterKeys { it in expected })
            assertSame(fixture.handler, CookieHandler.getDefault())
        }
    }
}

private fun cookieValues(raw: String): Map<String, String> = raw.split(';').mapNotNull { part ->
    val fields = part.trim().split('=', limit = 2)
    if (fields.size == 2) fields[0] to fields[1] else null
}.toMap()
