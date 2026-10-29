// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.Saver
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.SwingPanel
import javafx.application.Platform
import javafx.beans.value.ChangeListener
import javafx.concurrent.Worker
import javafx.embed.swing.JFXPanel
import javafx.scene.Scene
import javafx.scene.web.WebView
import kotlinx.coroutines.suspendCancellableCoroutine
import java.awt.GraphicsEnvironment
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/** Check before rendering on a host which may omit the explicitly required JavaFX runtime. */
fun isDesktopWebViewAvailable(): Boolean = !GraphicsEnvironment.isHeadless() && runCatching {
    listOf("javafx.scene.web.WebView", "javafx.embed.swing.JFXPanel").forEach {
        Class.forName(it, false, WebViewState::class.java.classLoader)
    }
}.isSuccess

/**
 * The host supplies matching JavaFX 21 runtime modules/classifiers. JavaFX startup is deferred to
 * the next AWT event, outside composition, and the toolkit is shared across windows. The host must
 * not call Platform.exit() while a WebView is mounted. A new state owns a new native view.
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
    check(isDesktopWebViewAvailable()) {
        "Desktop WebView needs a graphical session and matching JavaFX 21 base/graphics/controls/" +
            "media/web/swing runtime modules for this host. See docs/development/NATIVE.md."
    }
    key(state) {
        val currentCreated by rememberUpdatedState(onCreated)
        val currentDisposed by rememberUpdatedState(onDispose)
        val currentNavigator by rememberUpdatedState(navigator)
        var panel by remember { mutableStateOf<JFXPanel?>(null) }
        // In particular, do not cold-initialize JFXPanel inside remember/composition (NATIVE-018).
        LaunchedEffect(state) { panel = createPanelOutsideComposition() }
        panel?.let { nativePanel ->
            val owner = remember(state, nativePanel) {
                DesktopWebViewOwner(state, nativePanel, { currentNavigator }, { currentCreated() }, { currentDisposed() })
            }
            DisposableEffect(owner) {
                owner.create()
                onDispose { owner.dispose() }
            }
            LaunchedEffect(owner, navigator) {
                owner.updateHistory()
                navigator.consumeNavigationEvents { owner.navigate(it) }
            }
            LaunchedEffect(owner, state) {
                snapshotFlow { state.content }.collect { owner.load(it) }
            }
            SwingPanel(factory = { nativePanel }, modifier = modifier)
        }
    }
}

private suspend fun createPanelOutsideComposition(): JFXPanel = suspendCancellableCoroutine { continuation ->
    SwingUtilities.invokeLater {
        if (!continuation.isActive) return@invokeLater
        val panel = try { JFXPanel() } catch (error: Throwable) {
            continuation.resumeWithException(IllegalStateException("Could not initialize the JavaFX WebView toolkit", error))
            return@invokeLater
        }
        Platform.setImplicitExit(false)
        // No native WebView/Scene exists yet, so cancellation here cannot retain a page.
        continuation.resume(panel)
    }
}

internal suspend fun <T> onFxThread(action: () -> T): T = suspendCancellableCoroutine { continuation ->
    Platform.runLater {
        if (!continuation.isActive) return@runLater
        val result = runCatching(action)
        result.fold({ continuation.resume(it) }, { continuation.resumeWithException(it) })
    }
}

/** Distinguishes an unavailable native owner from an actual JavaScript/native evaluator failure. */
private class DetachedDesktopWebViewException : IllegalStateException("WebView is not attached")

/** Published only at a completed UI notification, never while a settings batch is in progress. */
internal data class DesktopWebSettingsSnapshot(val javaScriptEnabled: Boolean, val customUserAgent: String?)

/** One native view, its listeners and queued work have exactly one disposable owner. */
internal class DesktopWebViewOwner(
    private val state: WebViewState,
    private val panel: JFXPanel,
    private val navigator: () -> WebViewNavigator,
    private val onCreated: () -> Unit,
    private val onDispose: () -> Unit,
) {
    private val disposed = AtomicBoolean(false)
    private val settingsQueued = AtomicBoolean(false)
    private var native: WebView? = null // FX-thread confined
    private var defaultUserAgent: String? = null
    private var workerListener: ChangeListener<Worker.State>? = null
    private var progressListener: ChangeListener<Number>? = null
    private var titleListener: ChangeListener<String>? = null
    // FX-confined completed native applications, exposed internally for real-queue regression tests.
    internal var settingsApplicationCount = 0
        private set

    fun create() {
        Platform.runLater { createNow() }
    }

    /** Separate only so real-FX tests can observe failures without an uncaught event-loop error. */
    fun createNow() {
        check(Platform.isFxApplicationThread()) { "WebView creation must run on JavaFX Main" }
        if (disposed.get()) return
        check(state.webView == null) { "A WebViewState may own only one mounted WebView" }
        try {
            val view = WebView()
            val engine = view.engine
            native = view
            defaultUserAgent = engine.userAgent
            applySettingsNow(view)
            workerListener = ChangeListener { _, _, status ->
                if (disposed.get() || state.webView !== view) return@ChangeListener
                when (status) {
                    // JavaFX publishes the newly started URL before SCHEDULED. Keeping the
                    // previous requestedUrl here incorrectly attributes native link/history
                    // navigations to the preceding page. Redirects may later change final URL.
                    Worker.State.SCHEDULED -> state.beginRequest(engine.location.takeIf { it.isNotBlank() })
                    Worker.State.RUNNING -> state.loadingState = LoadingState.Loading(0f)
                    Worker.State.SUCCEEDED -> {
                        state.loadingState = LoadingState.Finished
                        state.pageTitle = engine.title
                        state.lastLoadedUrl = engine.location.takeIf { it.isNotBlank() }
                        updateHistoryNow(view)
                    }
                    Worker.State.FAILED -> {
                        state.loadingState = LoadingState.Finished
                        state.errorsForCurrentRequest = listOf(WebViewError(-1, engine.loadWorker.exception?.message ?: "Page load failed"))
                    }
                    Worker.State.CANCELLED -> state.loadingState = LoadingState.Finished
                    else -> Unit
                }
            }
            progressListener = ChangeListener { _, _, progress ->
                if (!disposed.get() && state.webView === view && state.loadingState is LoadingState.Loading) {
                    state.loadingState = LoadingState.Loading(progress.toFloat().coerceIn(0f, 1f))
                }
            }
            titleListener = ChangeListener { _, _, title ->
                if (!disposed.get() && state.webView === view) state.pageTitle = title
            }
            engine.loadWorker.stateProperty().addListener(workerListener)
            engine.loadWorker.progressProperty().addListener(progressListener)
            engine.titleProperty().addListener(titleListener)
            panel.scene = Scene(view)
            state.owner = this
            state.webView = view
            // State and library-owned listeners/settings are installed before customization.
            onCreated()
        } catch (error: Throwable) {
            disposed.set(true)
            // DisposableEffect may not yet have registered or onCreated may have thrown. Release
            // everything allocated so far without reporting a successfully-created lifecycle.
            releaseNow(error, notifyDisposal = false)
            throw error
        }
    }

    fun dispose() {
        if (!disposed.compareAndSet(false, true)) return
        Platform.runLater { releaseNow() }
    }

    private fun releaseNow(primary: Throwable? = null, notifyDisposal: Boolean = true) {
        val view = native
        if (view == null) { primary?.let { throw it }; return }
        val ownsState = state.webView === view
        runWebViewCleanup(primary,
            { if (notifyDisposal) onDispose() },
            { workerListener?.let { view.engine.loadWorker.stateProperty().removeListener(it) } },
            { progressListener?.let { view.engine.loadWorker.progressProperty().removeListener(it) } },
            { titleListener?.let { view.engine.titleProperty().removeListener(it) } },
            { view.engine.loadWorker.cancel() },
            { view.engine.load(null) }, // Release document/media, even if a prior cleanup stage fails.
            { panel.scene = null },
            {
                native = null
                workerListener = null
                progressListener = null
                titleListener = null
            },
            {
                if (state.webView === view) {
                    state.webView = null
                    state.owner = null
                    state.loadingState = LoadingState.Finished
                }
            },
            { if (ownsState) navigator().canGoBack = false },
            { if (ownsState) navigator().canGoForward = false },
        )
    }

    fun settingsChanged() {
        if (disposed.get() || !settingsQueued.compareAndSet(false, true)) return
        Platform.runLater {
            settingsQueued.set(false)
            if (!disposed.get()) native?.let(::applySettingsNow)
        }
    }

    private fun applySettingsNow(view: WebView) {
        val settings = state.desktopSettingsSnapshot.get()
        view.engine.isJavaScriptEnabled = settings.javaScriptEnabled
        view.engine.userAgent = settings.customUserAgent ?: defaultUserAgent
        settingsApplicationCount++
    }

    suspend fun updateHistory() = onFxThread { native?.takeUnless { disposed.get() }?.let(::updateHistoryNow) }

    private fun updateHistoryNow(view: WebView) {
        navigator().canGoBack = view.engine.history.currentIndex > 0
        navigator().canGoForward = view.engine.history.currentIndex < view.engine.history.entries.size - 1
    }

    suspend fun load(content: WebContent) = onFxThread {
        val view = native?.takeUnless { disposed.get() } ?: return@onFxThread
        loadNow(view, content)
    }

    private fun loadNow(view: WebView, content: WebContent) {
        if (!state.acceptContent(content, WebContentPlatform.Desktop)) return
        try {
            when (content) {
                is WebContent.Url -> view.engine.load(content.url)
                is WebContent.Data -> view.engine.loadContent(content.data, content.mimeType ?: "text/html")
                WebContent.NavigatorOnly -> Unit
            }
        } catch (error: Exception) {
            state.errorsForCurrentRequest = listOf(WebViewError(-1, error.message ?: "Invalid WebView content"))
            state.loadingState = LoadingState.Finished
        }
    }

    suspend fun navigate(event: WebViewNavigator.NavigationEvent) = onFxThread {
        val view = native?.takeUnless { disposed.get() } ?: return@onFxThread
        val engine = view.engine
        val content = event.contentOrNull()
        if (content != null) loadNow(view, content) else when (event) {
            WebViewNavigator.NavigationEvent.Back -> if (engine.history.currentIndex > 0) engine.history.go(-1)
            WebViewNavigator.NavigationEvent.Forward -> if (engine.history.currentIndex < engine.history.entries.size - 1) engine.history.go(1)
            WebViewNavigator.NavigationEvent.Reload -> engine.reload()
            WebViewNavigator.NavigationEvent.StopLoading -> engine.loadWorker.cancel() // Never enqueue another command.
            else -> Unit
        }
    }

    fun evaluate(script: String, callback: (Result<Any?>) -> Unit) {
        Platform.runLater {
            val view = native?.takeUnless { disposed.get() }
            val result = if (view == null) Result.failure(DetachedDesktopWebViewException())
                else runCatching { view.engine.executeScript(script) }
            callback(result) // Deliberately outside the platform try/catch.
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
    actual val settings: WebSettings = WebSettings { publishDesktopSettings() }
    // Keep pre-mount notifications too: an FX owner may not yet exist when the UI changes settings.
    internal val desktopSettingsSnapshot = AtomicReference(captureDesktopSettings())
    actual val cookieManager: CookieManager = CookieManager()
    actual var errorsForCurrentRequest: List<WebViewError> by mutableStateOf(emptyList())
        internal set
    actual fun evaluateJavascript(script: String, callback: ((String?) -> Unit)?) {
        val current = owner
        if (current == null) callback?.invoke(null)
        else current.evaluate(script) { callback?.invoke(it.getOrNull()?.toString()) }
    }
    // Snapshot state deliberately retains predecessor records. Storing the native view there
    // keeps the last disposed WebEngine/document alive when callers retain this state. Observe
    // only an invalidation token; the owned handle is always current, never snapshot-historical.
    private val attachedWebView = AtomicReference<WebView?>(null)
    private var attachmentVersion by mutableLongStateOf(0L)
    var webView: WebView?
        get() {
            attachmentVersion // Register Compose reads without retaining native predecessors.
            return attachedWebView.get()
        }
        internal set(value) {
            if (attachedWebView.getAndSet(value) !== value) attachmentVersion++
        }
    @Volatile internal var owner: DesktopWebViewOwner? = null

    private fun captureDesktopSettings() = DesktopWebSettingsSnapshot(
        settings.javaScriptEnabled, settings.desktopSettings.customUserAgent,
    )

    /** All settings writers are UI-confined; only this immutable pair crosses to JavaFX. */
    private fun publishDesktopSettings() {
        desktopSettingsSnapshot.set(captureDesktopSettings())
        owner?.settingsChanged()
    }
}

actual fun WebViewState.evaluateJavascriptResult(script: String, callback: (JavascriptResult) -> Unit) {
    val current = owner
    if (current == null) {
        callback(JavascriptResult.Unavailable("WebView is not attached"))
    } else if (!settings.javaScriptEnabled) {
        callback(JavascriptResult.Unavailable("JavaScript is disabled"))
    } else {
        current.evaluate(javascriptResultScript(script)) { result ->
            callback(result.fold(
                { decodeJavascriptResult(it as? String) },
                {
                    if (it is DetachedDesktopWebViewException) JavascriptResult.Unavailable("WebView is not attached")
                    else JavascriptResult.Error(it.message ?: "Script evaluation failed")
                },
            ))
        }
    }
}

actual val WebStateSaver: Saver<WebViewState, Any> = urlReloadWebStateSaver()
