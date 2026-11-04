// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)
package com.mohamedrejeb.calf.ui.web

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import com.mohamedrejeb.calf.ui.web.internal.*
import kotlinx.coroutines.*
import platform.Foundation.NSThread
import kotlin.test.*

/** NEW actual library UIApplication/WKWebView/default-store native-header parity; never a JVM or model substitute. */
class IosCookieWireAcceptanceTest {
    @Test fun realWkScopedCookieHeadersKeepNativeMultiplicityAcrossHttpAndTrustedHttps() {
        assertFalse(NSThread.isMainThread)
        val fixture = IosCookieWireFixture()
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
        val state = WebViewState(WebContent.NavigatorOnly).apply { settings.javaScriptEnabled = true }
        val navigator = WebViewNavigator(scope)
        var foreign: List<ForeignCookieIdentity>? = null
        var mayOwnCookies = false
        var primary: Throwable? = null
        try {
            foreign = runBlocking { fixture.foreignStoreSnapshot(requireFresh = true) }
            runApplicationUiTest {
                setContent { WebView(state, Modifier.fillMaxSize(), navigator = navigator) }
                waitForIdle()
                fixture.bind(this, state, navigator)
                mayOwnCookies = true // Cleanup must run even if seed commits before a native response failure.
                runBlocking { exerciseNativeCookieWire(CookieManager(), fixture) }
                fixture.complete()
            }
        } catch (error: Throwable) { primary = error; throw error }
        finally {
            runWebViewCleanup(primary,
                { if (mayOwnCookies) runBlocking { fixture.removeOwnedCookies() } },
                { if (foreign != null) assertTrue(runBlocking { fixture.foreignStoreSnapshot() } == foreign,
                    "The full foreign WK store must remain unchanged; no raw names/values are exported") },
                { scope.cancel() },
                { onApplicationMain { assertNull(state.webView); assertNull(state.nativeObserver); assertNull(state.navigator) } },
            )
        }
    }
}
