package com.mohamedrejeb.calf.ui.web

import java.net.CookieHandler
import java.net.URI
import kotlinx.coroutines.runBlocking
import kotlin.test.*

class DesktopCookieManagerTest {
    @Test fun customGlobalHandlerIsNeverReplacedEvenByReads() = runBlocking {
        val original = CookieHandler.getDefault()
        val handler = object : CookieHandler() {
            override fun get(uri: URI, requestHeaders: Map<String, List<String>>): Map<String, List<String>> =
                mapOf("Cookie" to listOf("session=kept"))
            override fun put(uri: URI, responseHeaders: Map<String, List<String>>) = Unit
        }
        try {
            CookieHandler.setDefault(handler)
            assertEquals("kept", CookieManager().getCookies("https://example.test/").single().value)
            assertSame(handler, CookieHandler.getDefault())
            assertFailsWith<UnsupportedCookieOperationException> { CookieManager().removeAllCookies() }
            assertSame(handler, CookieHandler.getDefault())
        } finally { CookieHandler.setDefault(original) }
    }
    @Test fun realJdkStoreAppliesPathAndSecureAndHostOnlyScope() = runBlocking {
        val manager = CookieManager(java.net.CookieManager())
        manager.setCookie("https://example.test/private/page", Cookie("private", "x", path = "/private", isSecure = true))
        assertEquals(listOf("private"), manager.getCookies("https://example.test/private/page").map { it.name })
        assertTrue(manager.getCookies("https://example.test/public").isEmpty())
        assertTrue(manager.getCookies("https://example.test/private-other").isEmpty())
        assertTrue(manager.getCookies("http://example.test/private").isEmpty())
        assertTrue(manager.getCookies("https://sub.example.test/private").isEmpty())
    }
    @Test fun absoluteExpiryDoesNotDriftWithReadTime() = runBlocking {
        val manager = CookieManager(java.net.CookieManager())
        val expiry = System.currentTimeMillis() + 60_000
        manager.setCookie("https://example.test/", Cookie("expiry", "x", expiresDate = expiry))
        val first = manager.getCookies("https://example.test/").single().expiresDate
        Thread.sleep(30)
        assertEquals(expiry, first)
        assertEquals(first, manager.getCookies("https://example.test/").single().expiresDate)
    }
    @Test fun roundTripToAnotherRealJdkStorePreservesTheAbsoluteExpiry() = runBlocking {
        val url = "https://example.test/"
        val sourceStore = java.net.CookieManager()
        val destinationStore = java.net.CookieManager()
        val source = CookieManager(sourceStore)
        val destination = CookieManager(destinationStore)
        val expiry = System.currentTimeMillis() + 60_123
        source.setCookie(url, Cookie("copy", "value", expiresDate = expiry))
        val first = source.getCookies(url).single()
        assertEquals(expiry, first.expiresDate)
        Thread.sleep(30)
        destination.setCookie(url, source.getCookies(url).single())
        Thread.sleep(30)
        val copied = destination.getCookies(url).single()
        assertEquals(expiry, copied.expiresDate)
        assertEquals(first, copied)
        assertNotSame(sourceStore.cookieStore.cookies.single(), destinationStore.cookieStore.cookies.single())
        source.removeAllCookies()
        assertEquals(copied, destination.getCookies(url).single()) // Independent store, not an alias.
    }
    @Test fun sessionPastAndSubsecondExpiryNeverInventOrExtendApiLifetime() = runBlocking {
        val url = "https://example.test/"
        val manager = CookieManager(java.net.CookieManager())
        manager.setCookie(url, Cookie("session", "value"))
        assertNull(manager.getCookies(url).single().expiresDate)
        manager.setCookie(url, Cookie("past", "value", expiresDate = System.currentTimeMillis() - 1))
        manager.setCookie(url, Cookie("epoch", "value", expiresDate = 0))
        assertEquals(listOf("session"), manager.getCookies(url).map { it.name })

        // Deliberately one millisecond past a second boundary. Preserve the exact
        // API deadline even when HttpCookie's native Max-Age has whole-second precision.
        val expiry = (System.currentTimeMillis() / 1000 + 2) * 1000 + 1
        manager.setCookie(url, Cookie("boundary", "value", expiresDate = expiry))
        assertEquals(expiry, manager.getCookies(url).single { it.name == "boundary" }.expiresDate)
        Thread.sleep((expiry - System.currentTimeMillis()).coerceIn(0, 3_000) + 50)
        assertTrue(System.currentTimeMillis() >= expiry, "Actual wall-clock expiry must have elapsed")
        assertEquals(listOf("session"), manager.getCookies(url).map { it.name })
    }
    @Test fun supportedTimestampExtremesAreExactAndOverflowInputsFailBeforeMutation() = runBlocking {
        val url = "https://example.test/"
        val manager = CookieManager(java.net.CookieManager())
        val latest = 253_402_300_799_999L
        manager.setCookie(url, Cookie("latest", "value", expiresDate = latest))
        assertEquals(latest, manager.getCookies(url).single().expiresDate)
        manager.setCookie(url, Cookie("earliest", "value", expiresDate = -62_135_596_800_000L))
        assertEquals(listOf("latest"), manager.getCookies(url).map { it.name })
        for (invalid in listOf(Long.MIN_VALUE, -62_135_596_800_001L, latest + 1, Long.MAX_VALUE)) {
            assertFailsWith<IllegalArgumentException> {
                manager.setCookie(url, Cookie("latest", "changed", expiresDate = invalid))
            }
            val retained = manager.getCookies(url).single()
            assertEquals("value", retained.value)
            assertEquals(latest, retained.expiresDate)
        }
    }
    @Test fun foreignStoreMetadataIsUnknownRatherThanInvented() = runBlocking {
        val native = java.net.CookieManager()
        native.put(URI("https://example.test/"), mapOf("Set-Cookie" to listOf("external=x; Max-Age=300; Path=/")))
        assertNull(CookieManager(native).getCookies("https://example.test/").single().expiresDate)
    }
    @Test fun missingHandlerDoesNotInstallAnEmptyGlobalStore() = runBlocking {
        val original = CookieHandler.getDefault()
        try {
            CookieHandler.setDefault(null)
            assertFailsWith<UnsupportedCookieOperationException> { CookieManager().getCookies("https://example.test/") }
            assertNull(CookieHandler.getDefault())
        } finally { CookieHandler.setDefault(original) }
    }
}
