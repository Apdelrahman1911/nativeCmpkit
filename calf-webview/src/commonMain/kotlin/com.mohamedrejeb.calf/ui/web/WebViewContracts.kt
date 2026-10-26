package com.mohamedrejeb.calf.ui.web

import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.mapSaver

/** JSON values are serialized consistently; undefined is distinct from JSON null. */
sealed interface JavascriptResult {
    data class Value(val json: String) : JavascriptResult
    data object Undefined : JavascriptResult
    data class Error(val message: String) : JavascriptResult
    data class Unavailable(val reason: String) : JavascriptResult
}

/**
 * Evaluates synchronously within the page on its UI thread. It does not
 * await returned JavaScript promises. Cyclic/non-JSON values report [JavascriptResult.Error].
 * The callback is outside platform error handling: exceptions in application code are not a
 * second evaluation result. An invocation that cannot start on an unattached/disposed/isolated
 * view reports Unavailable. Result delivery cannot be guaranteed if the native platform drops
 * an already-pending callback when its view is destroyed.
 */
expect fun WebViewState.evaluateJavascriptResult(script: String, callback: (JavascriptResult) -> Unit)

internal fun quoteJavascript(value: String): String = buildString {
    append('"')
    value.forEach { c ->
        when (c) {
            '"' -> append("\\\"")
            '\\' -> append("\\\\")
            '\n' -> append("\\n")
            '\r' -> append("\\r")
            '\t' -> append("\\t")
            else -> if (c.code < 32 || c == '\u2028' || c == '\u2029') {
                append("\\u").append(c.code.toString(16).padStart(4, '0'))
            } else append(c)
        }
    }
    append('"')
}

// A string envelope avoids depending on each native bridge's treatment of null/undefined/objects.
internal fun javascriptResultScript(script: String): String =
    "(function(){try{var v=(0,eval)(${quoteJavascript(script)});" +
        "var j=JSON.stringify(v);return j===undefined?'u':'v'+j;}" +
        "catch(e){return 'e'+String(e&&e.message||e);}})()"

internal fun decodeJavascriptResult(envelope: String?): JavascriptResult = when {
    envelope == "u" -> JavascriptResult.Undefined
    envelope?.startsWith("v") == true -> JavascriptResult.Value(envelope.drop(1))
    envelope?.startsWith("e") == true -> JavascriptResult.Error(envelope.drop(1))
    else -> JavascriptResult.Error("The native evaluator returned no valid result envelope")
}

internal fun WebViewState.beginRequest(url: String? = null) {
    requestedUrl = url
    lastLoadedUrl = null
    pageTitle = null
    errorsForCurrentRequest = emptyList()
    loadingState = LoadingState.Loading(0f)
}

internal fun WebViewNavigator.NavigationEvent.contentOrNull(): WebContent? = when (this) {
    is WebViewNavigator.NavigationEvent.LoadUrl -> WebContent.Url(url, additionalHttpHeaders)
    is WebViewNavigator.NavigationEvent.LoadHtml ->
        WebContent.Data(html, baseUrl, encoding ?: "utf-8", mimeType, historyUrl)
    else -> null
}

internal enum class WebContentPlatform { Android, Ios, Desktop, Browser }

/** Reject options we cannot implement instead of silently making a different network request. */
internal fun WebContent.unsupportedOptions(platform: WebContentPlatform): List<String> = buildList {
    if (platform == WebContentPlatform.Android) return@buildList
    when (val content = this@unsupportedOptions) {
        is WebContent.Url -> if (platform != WebContentPlatform.Ios && content.additionalHttpHeaders.isNotEmpty()) {
            add("additionalHttpHeaders")
        }
        is WebContent.Data -> {
            if (platform != WebContentPlatform.Ios && content.baseUrl != null) add("baseUrl")
            if (!content.encoding.equals("utf-8", true) && !content.encoding.equals("utf8", true)) add("encoding")
            if (content.historyUrl != null) add("historyUrl")
            if (content.mimeType != null && !content.mimeType.equals("text/html", true)) add("mimeType")
        }
        WebContent.NavigatorOnly -> Unit
    }
}

internal fun WebViewState.acceptContent(content: WebContent, platform: WebContentPlatform): Boolean {
    if (content == WebContent.NavigatorOnly) return false
    beginRequest((content as? WebContent.Url)?.url)
    val unsupported = content.unsupportedOptions(platform)
    if (unsupported.isEmpty()) return true
    errorsForCurrentRequest = listOf(WebViewError(-2, "Unsupported on $platform: ${unsupported.joinToString()}"))
    loadingState = LoadingState.Finished
    return false
}

internal fun restorableWebUrl(url: String?): String? = url?.takeIf {
    it.startsWith("https://", true) || it.startsWith("http://", true)
}

/**
 * Persist the accepted pending request during loading, and the observed terminal URL afterwards.
 * Only the never-attached/initial state falls back to declarative content: after navigator HTML
 * loads, that content may still contain a previous URL and must not resurrect it. A known final
 * non-HTTP URL is not replaced with the old HTTP request merely to make it saveable.
 */
internal fun WebViewState.urlForGetRestoration(): String? = restorableWebUrl(
    when (loadingState) {
        LoadingState.Initializing -> requestedUrl ?: (content as? WebContent.Url)?.url
        is LoadingState.Loading -> requestedUrl
        LoadingState.Finished -> lastLoadedUrl?.takeIf { it.isNotBlank() } ?: requestedUrl
    }
)

/** Native history is unavailable: persist only an HTTP(S) GET URL, never authentication headers. */
internal fun urlReloadWebStateSaver(): Saver<WebViewState, Any> = mapSaver(
    save = { state ->
        mapOf("requestedUrl" to state.urlForGetRestoration())
    },
    restore = { saved ->
        // Accept old metadata-only saves, but do not paint a stale title over a blank native view.
        val url = restorableWebUrl((saved["requestedUrl"] ?: saved["lastloaded"]) as? String)
        WebViewState(url?.let { WebContent.Url(it) } ?: WebContent.NavigatorOnly)
    },
)

/** Run every independent release stage. A callback/native failure must not skip later cleanup. */
internal fun runWebViewCleanup(primary: Throwable? = null, vararg stages: () -> Unit) {
    var failure = primary
    stages.forEach { stage ->
        try { stage() } catch (error: Throwable) {
            val original = failure
            if (original == null) failure = error
            else if (original !== error) original.addSuppressed(error)
        }
    }
    failure?.let { throw it }
}
