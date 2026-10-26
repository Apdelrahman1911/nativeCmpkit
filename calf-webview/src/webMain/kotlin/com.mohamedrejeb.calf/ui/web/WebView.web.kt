// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.Saver
import androidx.compose.ui.Modifier
import kotlinx.browser.document
import org.w3c.dom.HTMLIFrameElement
import org.w3c.dom.events.EventListener

/**
 * An iframe, not a native browser. Isolated (opaque-origin) content is the default, even with
 * JavaScript enabled. Opt into BrowserSandboxPolicy.Trusted only for host-controlled content.
 * A load event means navigation ended, not that framing/CSP/network authentication succeeded.
 * Cross-origin/isolated title, final URL, evaluation and history are explicitly unavailable.
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
        val currentCreated by rememberUpdatedState(onCreated)
        val currentDisposed by rememberUpdatedState(onDispose)
        val currentNavigator by rememberUpdatedState(navigator)
        val owner = remember(state) {
            BrowserWebViewOwner(state, { currentNavigator }, { currentCreated() }, { currentDisposed() })
        }
        DisposableEffect(owner) { onDispose { owner.dispose() } }
        state.iframe?.let { iframe ->
            LaunchedEffect(owner, iframe, navigator) {
                navigator.consumeNavigationEvents { owner.navigate(it) }
            }
            LaunchedEffect(owner, iframe, state) {
                snapshotFlow { state.content }.collect { owner.load(it) }
            }
        }
        CalfWebElementView(factory = owner::create, modifier = modifier, update = { owner.applySettings() })
    }
}

internal class BrowserWebViewOwner(
    private val state: WebViewState,
    private val navigator: () -> WebViewNavigator,
    private val onCreated: () -> Unit,
    private val onDispose: () -> Unit,
) {
    private var iframe: HTMLIFrameElement? = null
    private var disposed = false
    private var lastContent: WebContent = WebContent.NavigatorOnly
    private val loadListener: EventListener = browserEventListener {
        val frame = iframe?.takeUnless { disposed } ?: return@browserEventListener
        if (state.iframe !== frame) return@browserEventListener
        state.loadingState = LoadingState.Finished
        // Clear stale same-origin metadata before attempting an inaccessible destination.
        state.pageTitle = null
        state.lastLoadedUrl = null
        try {
            state.pageTitle = frame.contentDocument?.title
            state.lastLoadedUrl = frame.contentWindow?.location?.href
        } catch (_: Throwable) { /* A normal opaque/cross-origin security boundary. */ }
        // HTML history exposes no trustworthy cross-origin back/forward capability.
        navigator().canGoBack = false
        navigator().canGoForward = false
    }
    private val errorListener: EventListener = browserEventListener {
        if (disposed || state.iframe !== iframe) return@browserEventListener
        state.loadingState = LoadingState.Finished
        state.errorsForCurrentRequest = listOf(WebViewError(-1, "The iframe reported a load error"))
    }

    fun create(): HTMLIFrameElement {
        check(!disposed) { "Cannot create a disposed WebView owner" }
        check(state.iframe == null) { "A WebViewState may own only one mounted iframe" }
        val frame = (document.createElement("iframe") as HTMLIFrameElement).apply {
            style.border = "none"
            width = "100%"
            height = "100%"
            addEventListener("load", loadListener)
            addEventListener("error", errorListener)
        }
        iframe = frame
        state.iframe = frame
        state.owner = this
        try {
            applySettings()
            onCreated()
            return frame
        } catch (error: Throwable) {
            disposed = true
            releaseFrame(frame, error, notifyDisposal = false)
            throw error
        }
    }

    fun dispose() {
        if (disposed) return
        disposed = true
        val frame = iframe ?: return
        releaseFrame(frame)
    }

    private fun releaseFrame(frame: HTMLIFrameElement, primary: Throwable? = null, notifyDisposal: Boolean = true) {
        runWebViewCleanup(primary,
            { if (notifyDisposal) onDispose() },
            { frame.removeEventListener("load", loadListener) },
            { frame.removeEventListener("error", errorListener) },
            { frame.setAttribute("sandbox", "") },
            { frame.removeAttribute("srcdoc") },
            { frame.src = "about:blank" },
            {
                if (state.iframe === frame) {
                    state.iframe = null
                    state.owner = null
                    state.loadingState = LoadingState.Finished
                }
            },
            { iframe = null },
            { navigator().canGoBack = false },
            { navigator().canGoForward = false },
        )
    }

    fun applySettings() {
        if (disposed) return
        iframe?.applySettings(state.settings)
    }

    fun load(content: WebContent) {
        val frame = iframe?.takeUnless { disposed } ?: return
        if (!state.acceptContent(content, WebContentPlatform.Browser)) return
        lastContent = content
        frame.applySettings(state.settings)
        when (content) {
            is WebContent.Url -> {
                frame.removeAttribute("srcdoc") // srcdoc otherwise wins over src, including state loads.
                frame.src = content.url
            }
            is WebContent.Data -> {
                frame.removeAttribute("src")
                frame.srcdoc = content.data
            }
            WebContent.NavigatorOnly -> Unit
        }
    }

    fun navigate(event: WebViewNavigator.NavigationEvent) {
        val frame = iframe?.takeUnless { disposed } ?: return
        val content = event.contentOrNull()
        if (content != null) { load(content); return }
        try {
            when (event) {
                WebViewNavigator.NavigationEvent.Back -> frame.contentWindow?.history?.back()
                WebViewNavigator.NavigationEvent.Forward -> frame.contentWindow?.history?.forward()
                WebViewNavigator.NavigationEvent.Reload -> {
                    state.beginRequest(state.requestedUrl)
                    try { frame.contentWindow?.location?.reload() } catch (_: Throwable) { load(lastContent) }
                }
                WebViewNavigator.NavigationEvent.StopLoading -> {
                    frame.contentWindow?.stop()
                    state.loadingState = LoadingState.Finished
                }
                else -> Unit
            }
        } catch (_: Throwable) {
            state.errorsForCurrentRequest = listOf(WebViewError(-3, "This iframe operation is unavailable across an isolated/cross-origin boundary"))
        }
    }
}

internal fun HTMLIFrameElement.applySettings(settings: WebSettings) {
    when (settings.browserSandboxPolicy) {
        BrowserSandboxPolicy.Isolated -> {
            val permissions = buildList {
                if (settings.javaScriptEnabled) add("allow-scripts")
                if (settings.javaScriptEnabled && settings.javaScriptCanOpenWindowsAutomatically) add("allow-popups")
            }
            setAttribute("sandbox", permissions.joinToString(" ")) // Never allow-same-origin with scripts.
        }
        BrowserSandboxPolicy.Trusted -> if (settings.javaScriptEnabled) {
            removeAttribute("sandbox") // Deliberate, explicit trust escalation by the host.
        } else {
            setAttribute("sandbox", "allow-same-origin allow-forms")
        }
    }
}

@Stable
actual class WebViewState actual constructor(webContent: WebContent) {
    actual var requestedUrl: String? by mutableStateOf(null)
        internal set
    actual var lastLoadedUrl: String? by mutableStateOf(null)
        internal set
    actual var content: WebContent by mutableStateOf(webContent)
    actual var loadingState: LoadingState by mutableStateOf(LoadingState.Initializing)
        internal set
    actual val isLoading: Boolean get() = loadingState !is LoadingState.Finished
    actual var pageTitle: String? by mutableStateOf(null)
        internal set
    actual val settings: WebSettings = WebSettings { owner?.applySettings() }
    actual val cookieManager: CookieManager = CookieManager()
    actual var errorsForCurrentRequest: List<WebViewError> by mutableStateOf(emptyList())
        internal set
    actual fun evaluateJavascript(script: String, callback: ((String?) -> Unit)?) {
        val result = try { iframe?.contentWindow?.evaluateScript(script)?.toString() } catch (_: Throwable) { null }
        callback?.invoke(result) // Never interpret a user callback exception as a script exception.
    }
    var iframe by mutableStateOf<HTMLIFrameElement?>(null)
        internal set
    internal var owner: BrowserWebViewOwner? = null
}

actual fun WebViewState.evaluateJavascriptResult(script: String, callback: (JavascriptResult) -> Unit) {
    val frame = iframe
    val result = when {
        frame == null -> JavascriptResult.Unavailable("WebView is not attached")
        !settings.javaScriptEnabled -> JavascriptResult.Unavailable("JavaScript is disabled")
        settings.browserSandboxPolicy == BrowserSandboxPolicy.Isolated -> JavascriptResult.Unavailable("The iframe is isolated")
        else -> try {
            decodeJavascriptResult(frame.contentWindow?.evaluateScript(javascriptResultScript(script))?.toString())
        } catch (_: Throwable) { JavascriptResult.Unavailable("The iframe is cross-origin or evaluation is blocked by CSP") }
    }
    callback(result)
}

actual val WebStateSaver: Saver<WebViewState, Any> = urlReloadWebStateSaver()
