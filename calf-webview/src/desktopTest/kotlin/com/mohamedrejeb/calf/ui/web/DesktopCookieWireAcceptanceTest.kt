// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import kotlinx.coroutines.runBlocking
import kotlin.test.Test

/** NEW native-header parity; finite isolated worker/owned DNS/TLS fixture required, never ordinary Desktop fallback. */
class DesktopCookieWireAcceptanceTest {
    @Test fun realJavaFxScopedCookieHeadersKeepNativeMultiplicityAcrossHttpAndTrustedHttps() = runBlocking<Unit> {
        val fixture = DesktopCookieWireFixture.create()
        var primary: Throwable? = null
        try {
            exerciseNativeCookieWire(fixture.manager, fixture)
            fixture.complete()
        } catch (error: Throwable) { primary = error; throw error }
        finally { runWebViewCleanup(primary, { fixture.close() }) }
    }
}
