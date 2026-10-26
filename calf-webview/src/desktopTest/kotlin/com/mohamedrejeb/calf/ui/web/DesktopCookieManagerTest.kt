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
