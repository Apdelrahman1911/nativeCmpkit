// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.Saver
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.viewinterop.UIKitInteropInteractionMode
import androidx.compose.ui.viewinterop.UIKitInteropProperties
import androidx.compose.ui.viewinterop.UIKitView
import platform.UIKit.UISemanticContentAttributeForceLeftToRight
import platform.UIKit.UISemanticContentAttributeForceRightToLeft
import com.mohamedrejeb.calf.ui.web.helper.NSKeyValueObservingProtocol
import kotlinx.cinterop.COpaquePointer
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.ObjCSignatureOverride
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import platform.Foundation.NSKeyValueObservingOptionNew
import platform.Foundation.NSURL
import platform.Foundation.NSMutableURLRequest
import platform.Foundation.NSError
import platform.Foundation.addObserver
import platform.Foundation.removeObserver
import platform.WebKit.*
import platform.darwin.NSObject
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_main_queue
import platform.Foundation.NSThread
import platform.Foundation.setValue
import platform.CoreGraphics.CGRectMake

/**
 * A wrapper around WKWebView to provide a basic WebView composable for iOS.
 *
 * If you require more customisation you are most likely better rolling your own and using this
 * wrapper as an example.
 *
 * @param state The webview state holder where the Uri to load is defined.
 * @param modifier A compose modifier
 * @param captureBackPresses Set to true to have this Composable capture back presses and navigate
 * the WebView back. On iOS this controls the back/forward navigation swipe gesture.
 * @param navigator An optional navigator object that can be used to control the WebView's
 * navigation from outside the composable.
 * @param onCreated Called when the WebView is first created. The underlying WKWebView can be
 * accessed via [WebViewState.webView] for additional configuration.
 * @param onDispose Called when the WebView is destroyed.
 */
@OptIn(ExperimentalForeignApi::class, ExperimentalComposeUiApi::class)
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
        val layoutDirection = LocalLayoutDirection.current
        val currentCreated by rememberUpdatedState(onCreated)
        val currentDisposed by rememberUpdatedState(onDispose)
        val webView = state.webView
        SideEffect {
            state.navigator = navigator
            state.captureBackPresses = captureBackPresses
        }
        webView?.let { view ->
            LaunchedEffect(view, navigator) { navigator.handleNavigationEvents(view, state) }
            LaunchedEffect(view, state) {
                snapshotFlow { state.content }.collect { content ->
                    if (hasSameNativeWebView(state.webView, view)) loadIosContent(view, state, content)
                }
            }
        }
        UIKitView(
            factory = {
                check(state.webView == null) { "A WebViewState may own only one mounted WKWebView" }
                val configuration = WKWebViewConfiguration().apply {
                    allowsInlineMediaPlayback = state.settings.iosSettings.allowsInlineMediaPlayback
                    preferences.javaScriptEnabled = state.settings.javaScriptEnabled
                    defaultWebpagePreferences.allowsContentJavaScript = state.settings.javaScriptEnabled
                    preferences.javaScriptCanOpenWindowsAutomatically = state.settings.javaScriptCanOpenWindowsAutomatically
                }
                val view = WKWebView(frame = CGRectMake(0.0, 0.0, 0.0, 0.0), configuration = configuration)
                try {
                    view.setUserInteractionEnabled(true)
                    state.captureBackPresses = captureBackPresses
                    view.applySettings(state.settings, captureBackPresses)
                    state.navigator = navigator
                    state.webView = view
                    state.initialAllowsInlineMediaPlayback = state.settings.iosSettings.allowsInlineMediaPlayback
                    view.navigationDelegate = state
                    // Retain the observer before registering any key, including partial failures.
                    state.nativeObserver = WKWebViewObserver(state)
                    state.nativeObserver?.startObserving(view)
                    currentCreated()
                    view
                } catch (error: Throwable) {
                    runWebViewCleanup(error, { releaseIosWebView(state, view) {} })
                    throw error
                }
            },
            update = { view ->
                state.captureBackPresses = captureBackPresses
                state.navigator = navigator
                view.applySettings(state.settings, captureBackPresses)
                view.semanticContentAttribute = when (layoutDirection) {
                    LayoutDirection.Rtl -> UISemanticContentAttributeForceRightToLeft
                    else -> UISemanticContentAttributeForceLeftToRight
                }
            },
            properties = UIKitInteropProperties(interactionMode = UIKitInteropInteractionMode.NonCooperative),
            onRelease = { view -> releaseIosWebView(state, view) { currentDisposed() } },
            modifier = modifier,
        )
    }
}

private fun releaseIosWebView(state: WebViewState, view: WKWebView, onDispose: () -> Unit) {
    val observer = state.nativeObserver?.takeIf { hasSameNativeWebView(state.webView, view) }
    runWebViewCleanup(null,
        onDispose,
        { observer?.stopObserving(view) },
        { view.navigationDelegate = null },
        { view.stopLoading() },
        // UIKitView removes its grouping wrapper, not this child. A caller retaining
        // the native view or wrapper must not keep the released child attached until GC.
        // onRelease guarantees that this instance will never be reused by Compose.
        { view.removeFromSuperview() },
        {
            if (hasSameNativeWebView(state.webView, view)) {
                state.nativeObserver = null
                state.webView = null
                state.navigator = null
                state.loadingState = LoadingState.Finished
            }
        },
    )
}

internal fun runOnIosMain(action: () -> Unit) {
    if (NSThread.isMainThread) action() else dispatch_async(dispatch_get_main_queue()) { action() }
}

private fun loadIosContent(view: WKWebView, state: WebViewState, content: WebContent) {
    if (!state.acceptContent(content, WebContentPlatform.Ios)) return
    when (content) {
        is WebContent.Url -> {
            val url = NSURL.URLWithString(content.url)
            if (url == null) {
                state.errorsForCurrentRequest = listOf(WebViewError(-1, "Invalid URL"))
                state.loadingState = LoadingState.Finished
                return
            }
            val request = NSMutableURLRequest().apply {
                setURL(url)
                content.additionalHttpHeaders.forEach { (key, value) -> setValue(value, forHTTPHeaderField = key) }
            }
            view.loadRequest(request)
        }
        is WebContent.Data -> {
            val baseUrl = content.baseUrl?.let { NSURL.URLWithString(it) }
            if (content.baseUrl != null && baseUrl == null) {
                state.errorsForCurrentRequest = listOf(WebViewError(-1, "Invalid base URL"))
                state.loadingState = LoadingState.Finished
            } else {
                // The same Unicode HTML loader serves state and navigator. Unsupported byte
                // encodings/MIME/history options were rejected above, never relabeled as UTF-8.
                view.loadHTMLString(content.data, baseUrl)
            }
        }
        WebContent.NavigatorOnly -> Unit
    }
}

/**
 * A state holder to hold the state for the WebView. In most cases this will be remembered
 * using the rememberWebViewState(uri) function.
 */
@Stable
actual class WebViewState actual constructor(
    webContent: WebContent
) : NSObject(), WKNavigationDelegateProtocol {
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
            applySetting()
        }
    )

    actual val cookieManager: CookieManager = CookieManager()

    actual var errorsForCurrentRequest: List<WebViewError> by mutableStateOf(emptyList())
        internal set

    private fun applySetting() {
        val view = webView ?: return
        runOnIosMain {
            if (!hasSameNativeWebView(webView, view)) return@runOnIosMain
            view.applySettings(settings, captureBackPresses)
            if (initialAllowsInlineMediaPlayback != settings.iosSettings.allowsInlineMediaPlayback) {
                val error = WebViewError(-2, "allowsInlineMediaPlayback is creation-only; remount with a new state")
                if (error !in errorsForCurrentRequest) errorsForCurrentRequest = errorsForCurrentRequest + error
            }
        }
    }

    actual fun evaluateJavascript(script: String, callback: ((String?) -> Unit)?) {
        val view = webView
        runOnIosMain {
            if (view == null || !hasSameNativeWebView(webView, view)) callback?.invoke(null)
            else view.evaluateJavaScript(script) { result, error ->
                callback?.invoke(if (error == null) result?.toString() else null)
            }
        }
    }

    internal var captureBackPresses = true
    internal var initialAllowsInlineMediaPlayback = true
    internal var nativeObserver: WKWebViewObserver? = null

    // We need access to this in the state saver. An internal DisposableEffect or AndroidView
    // onDestroy is called after the state saver and so can't be used.
    var webView by mutableStateOf<WKWebView?>(null)
        internal set

    // Navigator reference for updating canGoBack/canGoForward
    internal var navigator: WebViewNavigator? = null

    @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
    @ObjCSignatureOverride
    override fun webView(webView: WKWebView, didFinishNavigation: WKNavigation?) {
        if (!hasSameNativeWebView(this.webView, webView)) return
        lastLoadedUrl = webView.URL?.absoluteString
        loadingState = LoadingState.Finished
        pageTitle = webView.title
        navigator?.canGoBack = webView.canGoBack
        navigator?.canGoForward = webView.canGoForward
    }

    @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
    @ObjCSignatureOverride
    override fun webView(webView: WKWebView, didStartProvisionalNavigation: WKNavigation?) {
        if (!hasSameNativeWebView(this.webView, webView)) return
        beginRequest(webView.URL?.absoluteString ?: requestedUrl)
    }

    @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
    @ObjCSignatureOverride
    override fun webView(webView: WKWebView, didCommitNavigation: WKNavigation?) {
        if (!hasSameNativeWebView(this.webView, webView)) return
        loadingState = LoadingState.Loading(webView.estimatedProgress.toFloat())
        lastLoadedUrl = webView.URL?.absoluteString
        pageTitle = webView.title
        navigator?.canGoBack = webView.canGoBack
        navigator?.canGoForward = webView.canGoForward
    }

    @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
    @ObjCSignatureOverride
    override fun webView(webView: WKWebView, didFailNavigation: WKNavigation?, withError: NSError) {
        if (!hasSameNativeWebView(this.webView, webView)) return
        loadingState = LoadingState.Finished
        errorsForCurrentRequest = errorsForCurrentRequest + WebViewError(
            code = withError.code.toInt(),
            description = withError.localizedDescription
        )
    }

    @Suppress("PARAMETER_NAME_CHANGED_ON_OVERRIDE")
    @ObjCSignatureOverride
    override fun webView(
        webView: WKWebView,
        didFailProvisionalNavigation: WKNavigation?,
        withError: NSError
    ) {
        if (!hasSameNativeWebView(this.webView, webView)) return
        loadingState = LoadingState.Finished
        errorsForCurrentRequest = errorsForCurrentRequest + WebViewError(
            code = withError.code.toInt(),
            description = withError.localizedDescription
        )
    }
}

private fun WKWebView.applySettings(webSettings: WebSettings, captureBackPresses: Boolean) {
    configuration.defaultWebpagePreferences.allowsContentJavaScript = webSettings.javaScriptEnabled
    configuration.preferences.javaScriptEnabled = webSettings.javaScriptEnabled
    configuration.preferences.javaScriptCanOpenWindowsAutomatically = webSettings.javaScriptCanOpenWindowsAutomatically
    allowsBackForwardNavigationGestures = captureBackPresses && webSettings.iosSettings.allowsBackForwardNavigationGestures
    // allowsInlineMediaPlayback is applied to WKWebViewConfiguration before construction only.
}

internal suspend fun WebViewNavigator.handleNavigationEvents(webView: WKWebView, state: WebViewState): Nothing =
    withContext(Dispatchers.Main) {
        consumeNavigationEvents(onAttached = {
            if (hasSameNativeWebView(state.webView, webView)) {
                canGoBack = webView.canGoBack
                canGoForward = webView.canGoForward
            }
        }) { event ->
            if (hasSameNativeWebView(state.webView, webView)) {
                val content = event.contentOrNull()
                if (content != null) loadIosContent(webView, state, content) else when (event) {
                    WebViewNavigator.NavigationEvent.Back -> if (webView.canGoBack) webView.goBack()
                    WebViewNavigator.NavigationEvent.Forward -> if (webView.canGoForward) webView.goForward()
                    WebViewNavigator.NavigationEvent.Reload -> webView.reload()
                    WebViewNavigator.NavigationEvent.StopLoading -> webView.stopLoading()
                    else -> Unit
                }
            }
        }
    }

actual fun WebViewState.evaluateJavascriptResult(script: String, callback: (JavascriptResult) -> Unit) {
    val view = webView
    runOnIosMain {
        when {
            view == null || !hasSameNativeWebView(webView, view) -> callback(JavascriptResult.Unavailable("WebView is not attached"))
            !settings.javaScriptEnabled -> callback(JavascriptResult.Unavailable("JavaScript is disabled"))
            else -> view.evaluateJavaScript(javascriptResultScript(script)) { value, error ->
                val result = if (error != null) JavascriptResult.Error(error.localizedDescription)
                    else decodeJavascriptResult(value as? String)
                callback(result)
            }
        }
    }
}

/**
 * KVO observer for WKWebView properties.
 * Observes estimatedProgress, title, URL, canGoBack, and canGoForward.
 */
@OptIn(ExperimentalForeignApi::class)
internal class WKWebViewObserver(
    private val state: WebViewState,
) : NSObject(), NSKeyValueObservingProtocol {

    private val observedKeyPaths = listOf(
        "estimatedProgress",
        "loading",
        "title",
        "URL",
        "canGoBack",
        "canGoForward",
    )
    private val registeredKeyPaths = mutableListOf<String>()

    fun startObserving(webView: WKWebView) {
        check(registeredKeyPaths.isEmpty()) { "Observer is already registered" }
        observedKeyPaths.forEach { keyPath ->
            webView.addObserver(
                observer = this,
                forKeyPath = keyPath,
                options = NSKeyValueObservingOptionNew,
                context = null,
            )
            registeredKeyPaths.add(keyPath)
        }
    }

    fun stopObserving(webView: WKWebView) {
        val registered = registeredKeyPaths.toList()
        registeredKeyPaths.clear()
        runWebViewCleanup(stages = registered.map { keyPath ->
            { webView.removeObserver(observer = this, forKeyPath = keyPath) }
        }.toTypedArray())
    }

    override fun observeValueForKeyPath(
        keyPath: String?,
        ofObject: Any?,
        change: Map<Any?, *>?,
        context: COpaquePointer?,
    ) {
        val webView = ofObject as? WKWebView ?: return
        if (!hasSameNativeWebView(state.webView, webView)) return

        when (keyPath) {
            "estimatedProgress" -> {
                val progress = webView.estimatedProgress.toFloat()
                if (state.isLoading) {
                    state.loadingState = LoadingState.Loading(progress)
                }
            }

            "loading" -> {
                if (webView.loading) {
                    state.loadingState = LoadingState.Loading(webView.estimatedProgress.toFloat())
                } else {
                    state.loadingState = LoadingState.Finished
                }
            }

            "title" -> {
                state.pageTitle = webView.title
            }

            "URL" -> {
                state.lastLoadedUrl = webView.URL?.absoluteString
            }

            "canGoBack" -> {
                state.navigator?.canGoBack = webView.canGoBack
            }

            "canGoForward" -> {
                state.navigator?.canGoForward = webView.canGoForward
            }
        }
    }
}

actual val WebStateSaver: Saver<WebViewState, Any> = urlReloadWebStateSaver()
