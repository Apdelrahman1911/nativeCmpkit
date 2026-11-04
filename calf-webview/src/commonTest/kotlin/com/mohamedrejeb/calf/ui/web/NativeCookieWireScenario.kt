// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import kotlin.test.*

/** Transport implementations MUST load the real library WebView and read authored DOM numeric observations. */
internal interface NativeCookieWireAdapter {
    val token: String
    fun url(page: String, subhost: Boolean, secure: Boolean): String
    suspend fun seed()
    suspend fun observe(page: String, subhost: Boolean, secure: Boolean): NativeCookieWireObservation
    suspend fun logout()
}
internal data class NativeCookieWireObservation(val wire: List<Int>, val visible: List<Int>)

/** NEW common body, but every invocation is an independent actual native-engine test, not a common-model substitute. */
internal suspend fun exerciseNativeCookieWire(manager: CookieManager, fixture: NativeCookieWireAdapter) {
    suspend fun checkPage(page: String, subhost: Boolean, secure: Boolean, managed: Boolean = false, loggedOut: Boolean = false) {
        val native = fixture.observe(page, subhost, secure)
        val expected = CookieWireContract.expected(page, subhost, secure, managed = managed, loggedOut = loggedOut)
        assertEquals(expected, native.wire, "Actual native request cookie occurrences/scopes differ from the independent contract")
        assertEquals(expected, CookieWireContract.vector(manager.getCookies(fixture.url(page, subhost, secure)), fixture.token),
            "Library returned-set occurrence parity differs from the ACTUAL native HTTP(S) Cookie header")
        assertEquals(CookieWireContract.expected(page, subhost, secure, visibleOnly = true, managed = managed, loggedOut = loggedOut),
            native.visible, "Actual document.cookie leaked HttpOnly or lost scoped occurrences")
    }
    suspend fun sweep(loggedOut: Boolean) {
        for (secure in listOf(true, false)) {
            for (page in CookieWireContract.pages) checkPage(page, false, secure, loggedOut = loggedOut)
            for (page in listOf("foo", "public")) checkPage(page, true, secure, loggedOut = loggedOut)
        }
    }
    fixture.seed() // Actual TLS response supplies HttpOnly, Secure, expired and duplicate path cookies.
    sweep(loggedOut = false)
    val current = fixture.url("foo/child", false, true)
    val managed = Cookie(CookieWireContract.name(fixture.token, "managed"), "managed", path = CookieWireContract.rootPath(fixture.token))
    manager.setCookie(current, managed) // Real native session cookie; no Expires attribute.
    assertNull(manager.getCookies(current).single { it.name == managed.name }.expiresDate)
    checkPage("foo/child", false, true, managed = true)
    manager.setCookie(current, managed.copy(expiresDate = 4_102_444_800_000L))
    checkPage("foo/child", false, true, managed = true)
    manager.setCookie(current, managed.copy(expiresDate = 0))
    checkPage("foo/child", false, true, managed = false)
    manager.setCookie(current, managed)
    checkPage("foo/child", false, true, managed = true)
    fixture.logout() // TLS server expires ALL owned paths/domains, including Secure/HttpOnly.
    sweep(loggedOut = true)
}
