package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Requires an Android emulator/device with a real WebView provider. Not a Robolectric suite. */
@RunWith(AndroidJUnit4::class)
class AndroidWebViewHistoryDeviceTest {
    @get:Rule val compose = createComposeRule()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    @After fun closeScope() { scope.cancel() }

    @Test fun navigatorReplacementReadsRealBrowserHistoryWithoutAnotherPageEvent() {
        val state = WebViewState(WebContent.Data(
            data = "<html><head><title>Local history fixture</title></head><body>history</body></html>",
            baseUrl = "https://nativecmpkit.invalid/fixture",
            historyUrl = "https://nativecmpkit.invalid/fixture",
        )).apply { settings.javaScriptEnabled = true }
        var navigator by mutableStateOf(WebViewNavigator(scope))
        var created = 0
        var disposed = 0
        compose.setContent {
            WebView(state, navigator = navigator, onCreated = { created++ }, onDispose = { disposed++ })
        }
        compose.waitUntil(timeoutMillis = 15_000) {
            compose.runOnUiThread { state.webView != null && state.loadingState == LoadingState.Finished }
        }
        val native = compose.runOnIdle { assertNotNull(state.webView) }
        var scriptResult: String? = null
        compose.runOnIdle {
            native.evaluateJavascript(
                "(function(){history.pushState(null,'','#first');history.pushState(null,'','#second');return 'ready';})()",
            ) { scriptResult = it }
        }
        compose.waitUntil(timeoutMillis = 10_000) { compose.runOnUiThread { scriptResult != null } }
        assertEquals("\"ready\"", compose.runOnUiThread { scriptResult }, "Real history.pushState must succeed")
        compose.runOnIdle { native.goBack() }
        compose.waitUntil(timeoutMillis = 10_000) {
            compose.runOnUiThread { native.canGoBack() && native.canGoForward() && native.url?.endsWith("#first") == true }
        }

        val replacement = WebViewNavigator(scope)
        assertFalse(replacement.canGoBack)
        assertFalse(replacement.canGoForward)
        compose.runOnIdle { navigator = replacement }
        compose.waitForIdle()
        compose.runOnIdle {
            assertSame(native, state.webView)
            assertEquals(native.canGoBack(), replacement.canGoBack)
            assertEquals(native.canGoForward(), replacement.canGoForward)
            assertTrue(replacement.canGoBack)
            assertTrue(replacement.canGoForward)
            assertEquals(1, created)
            assertEquals(0, disposed)
        }
    }
}
