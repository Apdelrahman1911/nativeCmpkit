// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.isActive
import kotlinx.coroutines.sync.Mutex

/**
 * A composable that provides a multiplatform WebView.
 *
 * If you require more customisation you are most likely better rolling your own and using this
 * wrapper as an example.
 *
 * @param state The webview state holder where the Uri to load is defined.
 * @param modifier A compose modifier
 * @param captureBackPresses Set to true to have this Composable capture back presses and navigate
 * the WebView back. On Android this intercepts the back button, on iOS it controls the
 * back/forward swipe gesture.
 * @param navigator An optional navigator object that can be used to control the WebView's
 * navigation from outside the composable.
 * @param onCreated Called when the WebView is first created. The underlying platform WebView
 * can be accessed via the platform-specific property on [WebViewState] for additional
 * configuration.
 * @param onDispose Called when the WebView is destroyed.
 */
@Composable
expect fun WebView(
    state: WebViewState,
    modifier: Modifier = Modifier,
    captureBackPresses: Boolean = true,
    navigator: WebViewNavigator = rememberWebViewNavigator(),
    onCreated: () -> Unit = {},
    onDispose: () -> Unit = {},
)

public sealed class WebContent {
    public data class Url(
        val url: String,
        val additionalHttpHeaders: Map<String, String> = emptyMap(),
    ) : WebContent()

    public data class Data(
        val data: String,
        val baseUrl: String? = null,
        val encoding: String = "utf-8",
        val mimeType: String? = null,
        val historyUrl: String? = null
    ) : WebContent()

    public data object NavigatorOnly : WebContent()
}

internal fun WebContent.withUrl(url: String) = when (this) {
    is WebContent.Url -> copy(url = url)
    else -> WebContent.Url(url)
}

/**
 * Sealed class for constraining possible loading states.
 * See [Loading] and [Finished].
 */
public sealed class LoadingState {
    /**
     * Describes a WebView that has not yet loaded for the first time.
     */
    public object Initializing : LoadingState()

    /**
     * Describes a webview between `onPageStarted` and `onPageFinished` events, contains a
     * [progress] property which is updated by the webview.
     */
    public data class Loading(val progress: Float) : LoadingState()

    /**
     * Describes a webview that has finished loading content.
     */
    public object Finished : LoadingState()
}

/**
 * A state holder to hold the state for the WebView. In most cases this will be remembered
 * using the rememberWebViewState(uri) function.
 */
@Stable
expect class WebViewState(webContent: WebContent) {
    /** Requested URL, distinct from the final URL observable from the native view. */
    public var requestedUrl: String?
        internal set

    public var lastLoadedUrl: String?
        internal set

    /**
     *  The content being loaded by the WebView
     */
    public var content: WebContent

    /**
     * Whether the WebView is currently [LoadingState.Loading] data in its main frame (along with
     * progress) or the data loading has [LoadingState.Finished]. See [LoadingState]
     */
    public var loadingState: LoadingState
        internal set

    /**
     * Whether the webview is currently loading data in its main frame
     */
    public val isLoading: Boolean

    /**
     * The title received from the loaded content of the current page
     */
    public var pageTitle: String?
        internal set

    public val settings: WebSettings

    /**
     * The cookie manager for managing cookies in the WebView.
     */
    public val cookieManager: CookieManager

    /**
     * The last error (if any) that occurred during page loading.
     * Reset to null when a new page starts loading.
     */
    public var errorsForCurrentRequest: List<WebViewError>
        internal set

    /** Legacy native-format result; null means no result/failure. Prefer [evaluateJavascriptResult]. */
    public fun evaluateJavascript(script: String, callback: ((String?) -> Unit)? = null)
}

/**
 * A common representation of a web resource loading error.
 *
 * @param code The error code. On Android this maps to [android.webkit.WebResourceError.getErrorCode],
 * on iOS to NSError codes, and on Desktop to JavaFX WebEngine error states.
 * @param description A human-readable description of the error.
 */
public data class WebViewError(
    val code: Int,
    val description: String,
)

/**
 * Allows control over the navigation of a WebView from outside the composable. E.g. for performing
 * a back navigation in response to the user clicking the "up" button in a TopAppBar.
 *
 * One navigator may be attached to one WebView at a time. Up to 64 commands are retained while
 * detached; exceeding that limit throws rather than silently dropping commands. Commands already
 * received by a disposed owner are not retried. Calls after the owning scope is cancelled are ignored.
 *
 * @see [rememberWebViewNavigator]
 */
@Stable
public class WebViewNavigator(private val coroutineScope: CoroutineScope) {
    internal sealed interface NavigationEvent {
        data object Back : NavigationEvent
        data object Forward : NavigationEvent
        data object Reload : NavigationEvent
        data object StopLoading : NavigationEvent

        data class LoadUrl(
            val url: String,
            val additionalHttpHeaders: Map<String, String> = emptyMap()
        ) : NavigationEvent

        data class LoadHtml(
            val html: String,
            val baseUrl: String? = null,
            val mimeType: String? = null,
            val encoding: String? = "utf-8",
            val historyUrl: String? = null
        ) : NavigationEvent
    }

    // Commands have one owner and are acknowledged by receiving, never replayed to a new view.
    // A bounded queue preserves pre-attachment loads without accumulating suspended sender jobs.
    private val navigationEvents = Channel<NavigationEvent>(capacity = 64)
    private val attachment = Mutex()

    private fun enqueue(event: NavigationEvent) {
        if (!coroutineScope.isActive) return
        check(navigationEvents.trySend(event).isSuccess) {
            "WebViewNavigator has 64 pending commands. Attach a WebView before sending more."
        }
    }

    internal suspend fun consumeNavigationEvents(
        onAttached: () -> Unit = {},
        handle: suspend (NavigationEvent) -> Unit,
    ): Nothing {
        check(attachment.tryLock()) { "A WebViewNavigator can control only one attached WebView." }
        try {
            // A replacement navigator must snapshot existing native history before its first
            // command, but a rejected second owner must not overwrite the active owner's flags.
            onAttached()
            while (true) handle(navigationEvents.receive())
        } finally {
            canGoBack = false
            canGoForward = false
            attachment.unlock()
        }
    }

    /**
     * True when the web view is able to navigate backwards, false otherwise.
     */
    public var canGoBack: Boolean by mutableStateOf(false)
        internal set

    /**
     * True when the web view is able to navigate forwards, false otherwise.
     */
    public var canGoForward: Boolean by mutableStateOf(false)
        internal set

    /** Queued once, including before attachment; headers are copied at the call boundary. */
    public fun loadUrl(url: String, additionalHttpHeaders: Map<String, String> = emptyMap()) {
        enqueue(NavigationEvent.LoadUrl(url, additionalHttpHeaders.toMap()))
    }

    public fun loadHtml(
        html: String,
        baseUrl: String? = null,
        mimeType: String? = null,
        encoding: String? = "utf-8",
        historyUrl: String? = null
    ) {
        enqueue(NavigationEvent.LoadHtml(html, baseUrl, mimeType, encoding, historyUrl))
    }

    /** Queue a single back command. Consumed commands never replay after reattachment. */
    public fun navigateBack() { enqueue(NavigationEvent.Back) }

    public fun navigateForward() { enqueue(NavigationEvent.Forward) }

    public fun reload() { enqueue(NavigationEvent.Reload) }

    public fun stopLoading() { enqueue(NavigationEvent.StopLoading) }

}

/**
 * Creates and remembers a [WebViewNavigator] using the default [CoroutineScope] or a provided
 * override.
 */
@Composable
public fun rememberWebViewNavigator(
    coroutineScope: CoroutineScope = rememberCoroutineScope()
): WebViewNavigator = remember(coroutineScope) { WebViewNavigator(coroutineScope) }

/**
 * Creates a WebView state that is remembered across Compositions.
 *
 * @param url The url to load in the WebView
 * @param additionalHttpHeaders Optional, additional HTTP headers that are passed to [WebView.loadUrl].
 *                              Android/iOS use these for this requested load only; subresources,
 *                              redirects and later navigation are not an authenticated HTTP client.
 *                              Desktop/browser reject non-empty headers as unsupported.
 */
@Composable
public fun rememberWebViewState(
    url: String,
    additionalHttpHeaders: Map<String, String> = emptyMap()
): WebViewState {
    val state = remember {
        WebViewState(
            WebContent.Url(
                url = url,
                additionalHttpHeaders = additionalHttpHeaders
            )
        )
    }

    LaunchedEffect(url, additionalHttpHeaders) {
        state.content = WebContent.Url(
            url = url,
            additionalHttpHeaders = additionalHttpHeaders
        )
    }

    return state
}

/**
 * Creates a WebView state that is remembered across Compositions.
 *
 * @param data The uri to load in the WebView
 */
@Composable
public fun rememberWebViewStateWithHTMLData(
    data: String,
    baseUrl: String? = null,
    encoding: String = "utf-8",
    mimeType: String? = null,
    historyUrl: String? = null
): WebViewState {
    val state = remember {
        WebViewState(WebContent.Data(data, baseUrl, encoding, mimeType, historyUrl))
    }

    LaunchedEffect(data, baseUrl, encoding, mimeType, historyUrl) {
        state.content = WebContent.Data(
            data, baseUrl, encoding, mimeType, historyUrl
        )
    }

    return state
}

/**
 * Creates a WebView state that is remembered across Compositions and saved
 * across activity recreation.
 * When using saved state, you cannot change the URL via recomposition. The only way to load
 * a URL is via a WebViewNavigator.
 * Android preserves its native history Bundle. Other targets reload the latest HTTP(S) URL using
 * a new GET request; headers, inline HTML, POST/form data, scroll and history are not persisted.
 * URLs may contain sensitive data or one-time tokens: use non-saveable state when replay/storage
 * is inappropriate. Settings are not saved; configure them again before rendering.
 */
@Composable
public fun rememberSaveableWebViewState(): WebViewState =
    rememberSaveable(saver = WebStateSaver) {
        WebViewState(WebContent.NavigatorOnly)
    }

expect val WebStateSaver: Saver<WebViewState, Any>
