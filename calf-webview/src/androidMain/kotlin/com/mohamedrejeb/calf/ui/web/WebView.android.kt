// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import android.content.Context
import android.graphics.Bitmap
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Message
import android.view.ViewGroup
import android.view.ViewGroup.LayoutParams
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.runtime.key
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.mapSaver
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONTokener
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference

/**
 * A wrapper around the Android [android.webkit.WebView] to provide a basic WebView composable.
 *
 * If you require more customisation you are most likely better rolling your own and using this
 * wrapper as an example.
 *
 * The WebView attempts to set the layoutParams based on the Compose modifier passed in. If it
 * is incorrectly sizing, use the layoutParams composable function instead.
 *
 * @param state The webview state holder where the Uri to load is defined.
 * @param modifier A compose modifier
 * @param captureBackPresses Set to true to have this Composable capture back presses and navigate
 * the WebView back via the system back button.
 * @param navigator An optional navigator object that can be used to control the WebView's
 * navigation from outside the composable.
 * @param onCreated Called when the WebView is first created. The underlying Android WebView
 * can be accessed via [WebViewState.webView] for additional configuration.
 * @param onDispose Called when the WebView is destroyed.
 */
@Composable
actual fun WebView(
    state: WebViewState,
    modifier: Modifier,
    captureBackPresses: Boolean,
    navigator: WebViewNavigator,
    onCreated: () -> Unit,
    onDispose: () -> Unit,
) {
    key(state) {
        val client = remember { AccompanistWebViewClient() }
        val chromeClient = remember { AccompanistWebChromeClient() }
        BoxWithConstraints(modifier) {
            val width = if (constraints.hasFixedWidth) LayoutParams.MATCH_PARENT else LayoutParams.WRAP_CONTENT
            val height = if (constraints.hasFixedHeight) LayoutParams.MATCH_PARENT else LayoutParams.WRAP_CONTENT
            WebView(
                state = state,
                layoutParams = FrameLayout.LayoutParams(width, height),
                captureBackPresses = captureBackPresses,
                navigator = navigator,
                onCreated = { view ->
                    view.settings.standardFontFamily = "sans-serif"
                    view.settings.defaultFontSize = 16
                    view.settings.minimumFontSize = 8
                    view.settings.minimumLogicalFontSize = 8
                    onCreated()
                },
                onDispose = { onDispose() },
                client = client,
                chromeClient = chromeClient,
            )
        }
    }
}

/**
 * Internal Android WebView composable with additional parameters for layout and client customization.
 *
 * @param state The webview state holder where the Uri to load is defined.
 * @param layoutParams A FrameLayout.LayoutParams object to custom size the underlying WebView.
 * @param modifier A compose modifier
 * @param captureBackPresses Set to true to have this Composable capture back presses and navigate
 * the WebView back via the system back button.
 * @param navigator An optional navigator object that can be used to control the WebView's
 * navigation from outside the composable.
 * @param onCreated Called when the WebView is first created with the native Android WebView instance.
 * WebChromeClient and WebViewClient should not be set here as they will be
 * library-owned; settings and clients are installed before this lambda is called.
 * Native customizations may be overwritten by a later common settings update.
 * @param onDispose Called when the WebView is destroyed.
 * @param client Provides access to WebViewClient via subclassing.
 * @param chromeClient Provides access to WebChromeClient via subclassing.
 * @param factory An optional WebView factory for using a custom subclass of WebView.
 */
@Composable
internal fun WebView(
    state: WebViewState,
    layoutParams: FrameLayout.LayoutParams,
    modifier: Modifier = Modifier,
    captureBackPresses: Boolean = true,
    navigator: WebViewNavigator = rememberWebViewNavigator(),
    onCreated: (WebView) -> Unit = {},
    onDispose: (WebView) -> Unit = {},
    client: AccompanistWebViewClient = remember { AccompanistWebViewClient() },
    chromeClient: AccompanistWebChromeClient = remember { AccompanistWebChromeClient() },
    factory: ((Context) -> WebView)? = null,
) {
    val currentCreated by rememberUpdatedState(onCreated)
    val currentDisposed by rememberUpdatedState(onDispose)
    val webView = state.webView
    BackHandler(captureBackPresses && navigator.canGoBack) { webView?.goBack() }
    webView?.let { view ->
        LaunchedEffect(view, navigator) { navigator.handleNavigationEvents(view, state) }
        LaunchedEffect(view, state) {
            snapshotFlow { state.content }.collect { content ->
                if (state.webView === view) loadAndroidContent(view, state, content)
            }
        }
    }
    client.state = state
    client.navigator = navigator
    chromeClient.state = state
    key(state) {
        AndroidView(
            factory = { context ->
                createAndroidWebView(
                    state = state,
                    create = { factory?.invoke(context) ?: WebView(context) },
                    configure = { view ->
                        view.layoutParams = layoutParams
                        view.applySettings(state.settings)
                        view.webChromeClient = chromeClient
                        view.webViewClient = client
                    },
                    onCreated = { currentCreated(it) },
                )
            },
            update = { it.layoutParams = layoutParams },
            modifier = modifier,
            onRelease = { view -> releaseAndroidWebView(state, view) { currentDisposed(view) } },
        )
    }
}

/** AndroidView has no ownership until its factory returns; unwind partial creation ourselves. */
internal fun createAndroidWebView(
    state: WebViewState,
    create: () -> WebView,
    configure: (WebView) -> Unit,
    onCreated: (WebView) -> Unit,
): WebView {
    check(state.webView == null) { "A WebViewState may own only one mounted WebView" }
    val view = create()
    try {
        configure(view)
        state.webView = view
        state.viewState?.let { view.restoreState(it) }
        onCreated(view)
        return view
    } catch (error: Throwable) {
        // A failed creation has no completed application lifecycle; do not fabricate onDispose.
        runWebViewCleanup(error, { releaseAndroidWebView(state, view, saveState = false) {} })
        throw error
    }
}

internal fun releaseAndroidWebView(
    state: WebViewState,
    view: WebView,
    saveState: Boolean = true,
    onDispose: () -> Unit,
) {
    runWebViewCleanup(
        stages = arrayOf(
            {
                if (saveState && state.webView === view) {
                    val saved = Bundle()
                    if (view.saveState(saved) != null) state.viewState = saved
                }
            },
            onDispose,
            { view.stopLoading() },
            { view.webChromeClient = null },
            { view.webViewClient = WebViewClient() },
            { (view.parent as? ViewGroup)?.removeView(view) },
            { view.removeAllViews() },
            { view.destroy() },
            {
            if (state.webView === view) {
                state.webView = null
                state.loadingState = LoadingState.Finished
            }
            },
        ),
    )
}

internal fun runOnAndroidMain(action: () -> Unit) {
    if (Looper.myLooper() == Looper.getMainLooper()) action()
    else Handler(Looper.getMainLooper()).post(action)
}

internal fun loadAndroidContent(view: WebView, state: WebViewState, content: WebContent) {
    if (!state.acceptContent(content, WebContentPlatform.Android)) return
    try {
        when (content) {
            is WebContent.Url -> view.loadUrl(content.url, content.additionalHttpHeaders)
            is WebContent.Data -> view.loadDataWithBaseURL(content.baseUrl, content.data, content.mimeType, content.encoding, content.historyUrl)
            WebContent.NavigatorOnly -> Unit
        }
    } catch (error: Exception) {
        state.errorsForCurrentRequest = listOf(WebViewError(-1, error.message ?: "Invalid WebView content"))
        state.loadingState = LoadingState.Finished
    }
}

/**
 * Applies the settings from the WebSettings object to the WebView
 */
private fun WebView.applySettings(webSettings: WebSettings) {
    settings.javaScriptEnabled = webSettings.javaScriptEnabled
    settings.javaScriptCanOpenWindowsAutomatically = webSettings.javaScriptCanOpenWindowsAutomatically
    settings.allowFileAccess = webSettings.androidSettings.allowFileAccess
    settings.allowContentAccess = webSettings.androidSettings.allowContentAccess
    settings.blockNetworkImage = webSettings.androidSettings.blockNetworkImage
    settings.blockNetworkLoads = webSettings.androidSettings.blockNetworkLoads
    settings.databaseEnabled = webSettings.androidSettings.databaseEnabled
    settings.domStorageEnabled = webSettings.androidSettings.domStorageEnabled
    settings.loadsImagesAutomatically = webSettings.androidSettings.loadsImagesAutomatically
    settings.useWideViewPort = webSettings.androidSettings.useWideViewPort
    settings.loadWithOverviewMode = webSettings.androidSettings.loadWithOverviewMode
    settings.mediaPlaybackRequiresUserGesture = webSettings.androidSettings.mediaPlaybackRequiresUserGesture
    settings.setSupportMultipleWindows(webSettings.androidSettings.supportMultipleWindows)
    settings.setSupportZoom(webSettings.androidSettings.supportZoom)
    settings.displayZoomControls = webSettings.androidSettings.displayZoomControls
    settings.setGeolocationEnabled(webSettings.androidSettings.setGeolocationEnabled)
    settings.textZoom = webSettings.androidSettings.textZoom
    settings.builtInZoomControls = webSettings.androidSettings.builtInZoomControls
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        settings.safeBrowsingEnabled = webSettings.androidSettings.safeBrowsingEnabled
    }
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        settings.isAlgorithmicDarkeningAllowed = webSettings.androidSettings.isAlgorithmicDarkeningAllowed
    }
}

/**
 * AccompanistWebViewClient
 *
 * A parent class implementation of WebViewClient that can be subclassed to add custom behaviour.
 *
 * As Accompanist Web needs to set its own web client to function, it provides this intermediary
 * class that can be overriden if further custom behaviour is required.
 */
public open class AccompanistWebViewClient : WebViewClient() {
    public open lateinit var state: WebViewState
        internal set
    public open lateinit var navigator: WebViewNavigator
        internal set

    override fun onPageStarted(view: WebView, url: String?, favicon: Bitmap?) {
        super.onPageStarted(view, url, favicon)
        if (state.webView !== view) return
        state.beginRequest(url)
        state.pageIcon = null
    }

    override fun onPageFinished(view: WebView, url: String?) {
        super.onPageFinished(view, url)
        if (state.webView !== view) return
        state.lastLoadedUrl = url
        state.loadingState = LoadingState.Finished
    }

    override fun doUpdateVisitedHistory(view: WebView, url: String?, isReload: Boolean) {
        super.doUpdateVisitedHistory(view, url, isReload)

        if (state.webView !== view) return
        navigator.canGoBack = view.canGoBack()
        navigator.canGoForward = view.canGoForward()
    }

    override fun onReceivedError(
        view: WebView,
        request: WebResourceRequest?,
        error: WebResourceError?
    ) {
        super.onReceivedError(view, request, error)

        if (state.webView !== view) return
        if (error != null) {
            val code = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) error.errorCode else -1
            val description = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) error.description?.toString() ?: "Unknown error" else "Unknown error"
            state.mutableErrorsForCurrentRequest.add(WebViewError(code, description))
        }
    }
}

/**
 * AccompanistWebChromeClient
 *
 * A parent class implementation of WebChromeClient that can be subclassed to add custom behaviour.
 *
 * As Accompanist Web needs to set its own web client to function, it provides this intermediary
 * class that can be overriden if further custom behaviour is required.
 */
public open class AccompanistWebChromeClient : WebChromeClient() {
    public open lateinit var state: WebViewState
        internal set

    /** The wrapper owns no child windows: reject rather than launch untrusted external handlers. */
    override fun onCreateWindow(view: WebView, isDialog: Boolean, isUserGesture: Boolean, resultMsg: Message?): Boolean = false

    override fun onReceivedTitle(view: WebView, title: String?) {
        super.onReceivedTitle(view, title)
        if (state.webView === view) state.pageTitle = title
    }

    override fun onReceivedIcon(view: WebView, icon: Bitmap?) {
        super.onReceivedIcon(view, icon)
        if (state.webView === view) state.pageIcon = icon
    }

    override fun onProgressChanged(view: WebView, newProgress: Int) {
        super.onProgressChanged(view, newProgress)
        if (state.webView !== view || state.loadingState is LoadingState.Finished) return
        state.loadingState = LoadingState.Loading(newProgress / 100.0f)
    }
}

/**
 * A state holder to hold the state for the WebView. In most cases this will be remembered
 * using the rememberWebViewState(uri) function.
 */
@Stable
actual class WebViewState actual constructor(webContent: WebContent) {
    actual var requestedUrl: String? by mutableStateOf(null)
        internal set

    actual var lastLoadedUrl: String? by mutableStateOf(null)
        internal set

    /**
     *  The content being loaded by the WebView
     */
    actual var content: WebContent by mutableStateOf(webContent)

    /**
     * Whether the WebView is currently [LoadingState.Loading] data in its main frame (along with
     * progress) or the data loading has [LoadingState.Finished]. See [LoadingState]
     */
    actual var loadingState: LoadingState by mutableStateOf(LoadingState.Initializing)
        internal set

    /**
     * Whether the webview is currently loading data in its main frame
     */
    actual val isLoading: Boolean
        get() = loadingState !is LoadingState.Finished

    /**
     * The title received from the loaded content of the current page
     */
    actual var pageTitle: String? by mutableStateOf(null)
        internal set

    actual val settings: WebSettings = WebSettings(
        onSettingsChanged = {
            applySettings()
        }
    )

    actual val cookieManager: CookieManager = CookieManager()

    private fun applySettings() {
        val view = webView ?: return
        runOnAndroidMain { if (webView === view) view.applySettings(settings) }
    }

    @JavascriptInterface
    actual fun evaluateJavascript(script: String, callback: ((String?) -> Unit)?) {
        val view = webView
        runOnAndroidMain {
            if (view == null || webView !== view) callback?.invoke(null)
            else evaluateAndroidJavascript(view, script, { webView === view }) { callback?.invoke(it.getOrNull()) }
        }
    }

    /**
     * the favicon received from the loaded content of the current page
     */
    public var pageIcon: Bitmap? by mutableStateOf(null)
        internal set

    /**
     * A list for errors captured in the last load. Reset when a new page is loaded.
     * Errors could be from any resource (iframe, image, etc.), not just for the main page.
     * For more fine grained control use the OnError callback of the WebView.
     */
    // SnapshotStateList updates are observed without copying every preceding resource error.
    internal val mutableErrorsForCurrentRequest = mutableStateListOf<WebViewError>()
    actual var errorsForCurrentRequest: List<WebViewError>
        get() = mutableErrorsForCurrentRequest
        internal set(value) {
            if (value === mutableErrorsForCurrentRequest) return
            mutableErrorsForCurrentRequest.clear()
            mutableErrorsForCurrentRequest.addAll(value)
        }

    /**
     * The saved view state from when the view was destroyed last. To restore state,
     * use the navigator and only call loadUrl if the bundle is null.
     * See WebViewSaveStateSample.
     */
    public var viewState: Bundle? = null
        internal set

    // We need access to this in the state saver. An internal DisposableEffect or AndroidView
    // onDestroy is called after the state saver and so can't be used.
    // Compose snapshots retain predecessor values even after the current value is null. A
    // retained WebViewState must not retain a destroyed native view (and its Activity) through
    // those records. Observe a token while storing only the current native owner outside MVCC.
    private val attachedWebView = AtomicReference<WebView?>(null)
    private var attachmentVersion by mutableLongStateOf(0L)
    var webView: WebView?
        get() {
            attachmentVersion // Keep existing Compose consumers reactive to attachment changes.
            return attachedWebView.get()
        }
        internal set(value) {
            if (attachedWebView.getAndSet(value) !== value) attachmentVersion++
        }
}

// Commands and all native UI work stay on Android's main thread.
internal suspend fun WebViewNavigator.handleNavigationEvents(webView: WebView, state: WebViewState): Nothing =
    withContext(Dispatchers.Main) {
        consumeNavigationEvents(onAttached = {
            if (state.webView === webView) {
                canGoBack = webView.canGoBack()
                canGoForward = webView.canGoForward()
            }
        }) { event ->
            if (state.webView === webView) {
                val content = event.contentOrNull()
                if (content != null) loadAndroidContent(webView, state, content) else when (event) {
                    WebViewNavigator.NavigationEvent.Back -> if (webView.canGoBack()) webView.goBack()
                    WebViewNavigator.NavigationEvent.Forward -> if (webView.canGoForward()) webView.goForward()
                    WebViewNavigator.NavigationEvent.Reload -> webView.reload()
                    WebViewNavigator.NavigationEvent.StopLoading -> webView.stopLoading()
                    else -> Unit
                }
            }
        }
    }

actual fun WebViewState.evaluateJavascriptResult(script: String, callback: (JavascriptResult) -> Unit) {
    val view = webView
    runOnAndroidMain {
        if (view == null || webView !== view) {
            callback(JavascriptResult.Unavailable("WebView is not attached"))
        } else if (!view.settings.javaScriptEnabled) {
            callback(JavascriptResult.Unavailable("JavaScript is disabled"))
        } else {
            evaluateAndroidJavascript(view, javascriptResultScript(script), { webView === view }) { nativeResult ->
                val result = nativeResult.fold(
                    { raw ->
                        try { decodeJavascriptResult(JSONTokener(raw ?: "null").nextValue() as? String) }
                        catch (error: Exception) { JavascriptResult.Error(error.message ?: "Invalid native JavaScript result") }
                    },
                    {
                        if (it is DetachedAndroidWebViewException) JavascriptResult.Unavailable("WebView is not attached")
                        else JavascriptResult.Error(it.message ?: "Native JavaScript evaluation failed")
                    },
                )
                callback(result) // Outside both platform invocation and result-decoding catches.
            }
        }
    }
}

private class DetachedAndroidWebViewException : IllegalStateException("WebView is not attached")

/** One native invocation owns one settlement, including a synchronous callback followed by throw. */
private fun evaluateAndroidJavascript(
    view: WebView,
    script: String,
    isCurrent: () -> Boolean,
    onResult: (Result<String?>) -> Unit,
) {
    val settled = AtomicBoolean(false)
    fun complete(result: Result<String?>) = runOnAndroidMain {
        if (!settled.compareAndSet(false, true)) return@runOnAndroidMain
        onResult(if (isCurrent()) result else Result.failure(DetachedAndroidWebViewException()))
    }
    try {
        view.evaluateJavascript(script) { complete(Result.success(it)) }
    } catch (error: Exception) {
        // A callback may have run synchronously and thrown application code, or native code may
        // have thrown after successful settlement. Never reinterpret either as a second result.
        if (settled.get()) throw error
        complete(Result.failure(error))
        // If the native call queued a callback and then threw, that later callback is now ignored.
    }
}


actual val WebStateSaver: Saver<WebViewState, Any> = run {
    val pageTitleKey = "pagetitle"
    val lastLoadedUrlKey = "lastloaded"
    val stateBundle = "bundle"

    mapSaver(
        save = {
            val viewState = it.webView?.let { view -> Bundle().also { saved -> view.saveState(saved) } } ?: it.viewState
            mapOf(
                pageTitleKey to it.pageTitle,
                lastLoadedUrlKey to it.lastLoadedUrl,
                stateBundle to viewState
            )
        },
        restore = {
            WebViewState(WebContent.NavigatorOnly).apply {
                this.pageTitle = it[pageTitleKey] as String?
                this.lastLoadedUrl = it[lastLoadedUrlKey] as String?
                this.viewState = it[stateBundle] as Bundle?
            }
        }
    )
}
