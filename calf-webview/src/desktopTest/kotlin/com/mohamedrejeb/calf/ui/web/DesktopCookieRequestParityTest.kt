// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import java.net.CookiePolicy
import java.net.URI
import kotlinx.coroutines.runBlocking
import kotlin.test.*

/** NEW real JDK store/header construction. No JavaFX/browser/network/iOS execution claim. */
class DesktopCookieRequestParityTest {
    @Test fun realJdkRequestHeadersAndLibraryResultsKeepDuplicateNamesAcrossPathAndDomainScopes() = runBlocking {
        val native = java.net.CookieManager(null, CookiePolicy.ACCEPT_ALL)
        val manager = CookieManager(native)
        val owner = "https://owner.example.test"
        try {
            for ((path, value) in listOf("/" to "root", "/foo" to "foo", "/foo/child" to "child", "/private" to "private"))
                manager.setCookie("$owner$path", Cookie("scope", value, path = path))
            manager.setCookie("$owner/", Cookie("domain", "yes", domain = "owner.example.test", path = "/"))
            manager.setCookie("$owner/", Cookie("host", "yes", path = "/"))
            manager.setCookie("$owner/", Cookie("secure", "yes", path = "/", isSecure = true))
            manager.setCookie("$owner/", Cookie("expired", "no", path = "/", expiresDate = 0))
            for (url in listOf("$owner/foo", "$owner/foo/child/page", "$owner/foobar", "$owner/private", "$owner/public",
                    "http://owner.example.test/foo/child", "https://sub.owner.example.test/foo/child")) {
                val wire = requestPairs(native, URI(url))
                val actual = pairs(manager.getCookies(url))
                assertEquals(wire, actual, "Actual JDK request-header occurrence parity at $url")
            }
            assertEquals(listOf("child", "foo", "root"), manager.getCookies("$owner/foo/child/page")
                .filter { it.name == "scope" }.map { it.value }.sorted())
            assertEquals(listOf("root"), manager.getCookies("$owner/foobar").filter { it.name == "scope" }.map { it.value })
            assertEquals(listOf("private", "root"), manager.getCookies("$owner/private").filter { it.name == "scope" }.map { it.value }.sorted())
            assertEquals(listOf("root"), manager.getCookies("$owner/public").filter { it.name == "scope" }.map { it.value })
            assertEquals(listOf("domain" to "yes"), pairs(manager.getCookies("https://sub.owner.example.test/foo")))
            assertFalse(manager.getCookies("http://owner.example.test/foo").any { it.name == "secure" })
            assertFalse(manager.getCookies("$owner/foo").any { it.name == "expired" })
        } finally {
            manager.removeAllCookies() // This store is explicitly owned, never an application/native global jar.
            assertTrue(native.cookieStore.cookies.isEmpty())
        }
    }

    @Test fun anOwnedJdkHandlerSelectingOneEqualValueOccurrenceDoesNotInventTwoResults() = runBlocking {
        // Deliberately controlled application-owned request selection. The retained
        // string bytes come from super.get's real JDK serialization, not browser headers.
        val native = object : java.net.CookieManager(null, CookiePolicy.ACCEPT_ALL) {
            override fun get(uri: URI, requestHeaders: Map<String, List<String>>): Map<String, List<String>> =
                super.get(uri, requestHeaders).filterKeys { it.equals("Cookie", true) }.mapValues { (_, values) ->
                    values.take(1).map { it.substringBefore(';') }
                }
        }
        val manager = CookieManager(native)
        val url = "https://owner.example.test/foo/page"
        try {
            manager.setCookie(url, Cookie("scope", "identical", path = "/"))
            manager.setCookie(url, Cookie("scope", "identical", path = "/foo"))
            assertEquals(2, native.cookieStore.cookies.size, "Both distinct path identities really exist in the JDK store")
            val selected = requestPairs(native, URI(url))
            assertEquals(listOf("scope" to "identical"), selected)
            val actual = manager.getCookies(url)
            assertEquals(selected, pairs(actual),
                "sent.any(name,value) must not inflate a single transmitted occurrence into two metadata cookies")
            val ambiguous = actual.single()
            assertNull(ambiguous.path, "The custom header does not identify which equal-value path it selected")
            assertNull(ambiguous.domain, "Do not invent storage metadata for an ambiguous transmitted identity")
            assertNull(ambiguous.expiresDate)
        } finally {
            manager.removeAllCookies()
            assertTrue(native.cookieStore.cookies.isEmpty())
        }
    }

    private fun requestPairs(native: java.net.CookieManager, url: URI): List<Pair<String, String>> =
        pairs(native.get(url, emptyMap()).filterKeys { it.equals("Cookie", true) || it.equals("Cookie2", true) }
            .values.flatten().flatMap(::parseCookieHeader))
    private fun pairs(cookies: List<Cookie>) = cookies.map { it.name to it.value }
        .sortedWith(compareBy<Pair<String, String>> { it.first }.thenBy { it.second })
}
