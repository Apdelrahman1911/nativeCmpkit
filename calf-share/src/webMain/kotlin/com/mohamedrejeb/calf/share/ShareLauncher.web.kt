// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share

import androidx.compose.runtime.*
import com.mohamedrejeb.calf.core.ExperimentalCalfApi

@ExperimentalCalfApi
@Composable
actual fun rememberShareLauncher(onResult: (ShareResult) -> Unit): ShareLauncher =
    rememberShareOutcomeLauncher { onResult(it.toLegacyResult()) }

@ExperimentalCalfApi
@Composable
actual fun rememberShareOutcomeLauncher(options: ShareOptions, onResult: (ShareOutcome) -> Unit): ShareLauncher {
    val currentResult by rememberUpdatedState(onResult)
    val currentOptions by rememberUpdatedState(options)
    val owner = remember { BrowserShareOwner({ currentOptions }, { currentResult(it) }) }
    DisposableEffect(owner) { onDispose { owner.dispose() } }
    return remember(owner) { ShareLauncher(owner::launch) }
}

@ExperimentalCalfApi
@Stable
actual class ShareLauncher actual constructor(private val onLaunch: (ShareContent) -> Unit) {
    actual fun launch(content: ShareContent) { onLaunch(content.snapshot()) }
}

internal class BrowserShareOwner(private val options: () -> ShareOptions, private val onResult: (ShareOutcome) -> Unit) {
    private val gate = ShareRequestGate()
    private var disposed = false
    fun launch(content: ShareContent) {
        if (disposed) return
        val token = gate.begin()
        if (token == null) { onResult(ShareOutcome.Busy); return }
        // Do not dispatch/suspend before navigator.share(): transient user activation must survive.
        handleWebShare(content, options()) { result ->
            if (gate.finish(token) && !disposed) onResult(result)
        }
    }
    fun dispose() { disposed = true; gate.abandon() }
}

internal fun handleWebShare(content: ShareContent, options: ShareOptions, onResult: (ShareOutcome) -> Unit) {
    content.validationFailure()?.let { onResult(it); return }
    if (isWebShareSupported()) {
        val settled: (WebShareResult) -> Unit = { result ->
            onResult(when (result) {
                WebShareResult.Completed -> ShareOutcome.Completed
                WebShareResult.Dismissed -> ShareOutcome.Dismissed
                WebShareResult.Unavailable -> ShareOutcome.Unavailable("The browser cannot share this payload")
                WebShareResult.Failed -> ShareOutcome.Failed(ShareFailureReason.Platform, "The browser rejected the share operation")
            })
        }
        when (content) {
            is ShareContent.Text -> webShareText(content.text, content.subject, settled)
            is ShareContent.Url -> webShareUrl(content.url, content.subject, settled)
            is ShareContent.File -> webShareFile(content.file.file, content.subject, settled)
            is ShareContent.Files -> webShareFiles(content.files.map { it.file }, content.subject, settled)
        }
        return
    }
    val text = when (content) { is ShareContent.Text -> content.text; is ShareContent.Url -> content.url; else -> null }
    if (text == null || !options.allowClipboardFallback || !isClipboardSupported()) {
        onResult(ShareOutcome.Unavailable("No supported share mechanism or allowed clipboard fallback"))
    } else {
        copyToClipboard(text) { success ->
            onResult(if (success) ShareOutcome.CopiedToClipboard else ShareOutcome.Failed(ShareFailureReason.Platform, "Clipboard write was rejected"))
        }
    }
}
