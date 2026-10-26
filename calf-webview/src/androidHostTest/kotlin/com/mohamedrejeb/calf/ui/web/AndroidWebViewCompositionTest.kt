package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.junit4.createComposeRule
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import kotlin.test.*

/** Real Android composition/view binding; history itself is explicitly supplied by Robolectric. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class AndroidWebViewCompositionTest {
    @get:Rule val compose = createComposeRule()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    @After fun closeScope() { scope.cancel() }

    @Test fun replacingOnlyNavigatorSnapshotsExistingNativeHistoryWithoutRecreatingView() {
        val state = WebViewState(WebContent.NavigatorOnly)
        var navigator by mutableStateOf(WebViewNavigator(scope))
        var created = 0
        var disposed = 0
        compose.setContent {
            WebView(state, navigator = navigator, onCreated = { created++ }, onDispose = { disposed++ })
        }
        val native = compose.runOnIdle { assertNotNull(state.webView) }
        compose.runOnIdle {
            // No real Chromium navigation is claimed by this host test. The device test creates
            // the equivalent history through actual page JavaScript instead of shadow methods.
            shadowOf(native).pushEntryToHistory("https://history.invalid/first")
            shadowOf(native).pushEntryToHistory("https://history.invalid/middle")
            shadowOf(native).pushEntryToHistory("https://history.invalid/last")
            native.goBack()
            assertTrue(native.canGoBack())
            assertTrue(native.canGoForward())
        }
        val replacement = WebViewNavigator(scope)
        assertFalse(replacement.canGoBack)
        assertFalse(replacement.canGoForward)
        compose.runOnIdle { navigator = replacement }
        compose.waitForIdle()
        compose.runOnIdle {
            assertSame(native, state.webView)
            assertEquals(WebContent.NavigatorOnly, state.content, "Capabilities must not be inferred from a content URL")
            assertEquals(native.canGoBack(), replacement.canGoBack)
            assertEquals(native.canGoForward(), replacement.canGoForward)
            assertTrue(replacement.canGoBack)
            assertTrue(replacement.canGoForward)
            assertEquals(1, created)
            assertEquals(0, disposed)
        }
    }
}
