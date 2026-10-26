// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share

import androidx.compose.runtime.*
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.share.platform.NativeShareBridge
import kotlinx.coroutines.*
import java.awt.Toolkit
import java.awt.datatransfer.StringSelection

@ExperimentalCalfApi
@Composable
actual fun rememberShareLauncher(onResult: (ShareResult) -> Unit): ShareLauncher =
    rememberShareOutcomeLauncher { onResult(it.toLegacyResult()) }

@ExperimentalCalfApi
@Composable
actual fun rememberShareOutcomeLauncher(options: ShareOptions, onResult: (ShareOutcome) -> Unit): ShareLauncher {
    val scope = rememberCoroutineScope()
    val currentResult by rememberUpdatedState(onResult)
    val currentOptions by rememberUpdatedState(options)
    val owner = remember(scope) { DesktopShareOwner(scope, { currentOptions }, { currentResult(it) }) }
    return remember(owner) { ShareLauncher(owner::launch) }
}

/** UI-confined owner; injectable operation exercises the real admission/callback/cancel boundary. */
internal class DesktopShareOwner(
    private val scope: CoroutineScope,
    private val options: () -> ShareOptions,
    private val onResult: (ShareOutcome) -> Unit,
    private val operation: suspend (ShareContent, ShareOptions) -> ShareOutcome = ::handleDesktopShare,
) {
    private val gate = ShareRequestGate()
    fun launch(content: ShareContent) {
        scope.launch {
            val token = gate.begin()
            if (token == null) { onResult(ShareOutcome.Busy); return@launch }
            val result = try {
                operation(content, options())
            } catch (cancelled: CancellationException) { throw cancelled }
              catch (error: Exception) { ShareOutcome.Failed(ShareFailureReason.Platform, error.message ?: "Desktop sharing failed") }
              catch (error: LinkageError) { ShareOutcome.Unavailable(error.message ?: "Native sharing could not be loaded") }
              finally { gate.finish(token) }
            currentCoroutineContext().ensureActive()
            // Gate release/native cancellation scheduling precedes the callback. On timeout,
            // AppKit cleanup is asynchronous; its own registry remains Busy until Main finishes.
            onResult(result) // Application exceptions never become a second platform outcome.
        }
    }
}

@ExperimentalCalfApi
@Stable
actual class ShareLauncher actual constructor(private val onLaunch: (ShareContent) -> Unit) {
    actual fun launch(content: ShareContent) { onLaunch(content.snapshot()) }
}

private suspend fun handleDesktopShare(content: ShareContent, options: ShareOptions): ShareOutcome {
    content.validationFailure()?.let { return it }
    val supported = try {
        withContext(Dispatchers.IO) { NativeShareBridge.isNativeShareSupported() }
    } catch (cancelled: CancellationException) { throw cancelled }
      catch (_: LinkageError) { false }
      catch (_: Exception) { false }
    if (supported) {
        val native = shareWithNative(content, options)
        // A failed/denied/cancelled native request never implicitly copies/opens content.
        if (native !is ShareOutcome.Unavailable) return native
    }
    return safeDesktopShareFallback(content, options.allowClipboardFallback) { text ->
        val selection = StringSelection(text)
        Toolkit.getDefaultToolkit().systemClipboard.setContents(selection, selection)
    }
}

internal fun safeDesktopShareFallback(content: ShareContent, allowed: Boolean, copyText: (String) -> Unit): ShareOutcome {
    val text = when (content) { is ShareContent.Text -> content.text; is ShareContent.Url -> content.url; else -> null }
    if (!allowed || text == null) return ShareOutcome.Unavailable("No native share sheet; automatic file/URL opening is intentionally disabled")
    return try { copyText(text); ShareOutcome.CopiedToClipboard }
    catch (error: Exception) { ShareOutcome.Failed(ShareFailureReason.Platform, error.message ?: "Clipboard unavailable") }
}

private suspend fun shareWithNative(content: ShareContent, options: ShareOptions): ShareOutcome {
    val text = (content as? ShareContent.Text)?.text
    val url = (content as? ShareContent.Url)?.url
    val files = when (content) {
        is ShareContent.File -> listOf(content.file.file)
        is ShareContent.Files -> content.files.map { it.file }
        else -> emptyList()
    }
    if (files.any { !it.isFile || !it.canRead() }) return ShareOutcome.Failed(ShareFailureReason.InvalidContent, "A shared file is missing or unreadable")
    val subject = when (content) { is ShareContent.Text -> content.subject; is ShareContent.Url -> content.subject; is ShareContent.File -> content.subject; is ShareContent.Files -> content.subject }
    // This JNI call only allocates an ID/schedules Main. It never waits for UI completion, so
    // cancellation cannot lose an operation ID across a dispatcher handoff.
    val id = NativeShareBridge.beginShareSheet(text, url, files.map { it.absolutePath }.toTypedArray(), subject, 0L)
    if (id == NativeShareBridge.REQUEST_BUSY) return ShareOutcome.Busy
    if (id <= 0) return ShareOutcome.Unavailable("No active native window/share service")
    return try {
        withTimeoutOrNull(options.desktopTimeoutMillis) {
            var result: ShareOutcome? = null
            while (result == null) {
                currentCoroutineContext().ensureActive()
                result = when (NativeShareBridge.takeShareResult(id)) {
                    NativeShareBridge.RESULT_PENDING -> null
                    NativeShareBridge.RESULT_SUCCESS -> ShareOutcome.Completed
                    NativeShareBridge.RESULT_DISMISSED -> ShareOutcome.Dismissed
                    NativeShareBridge.RESULT_UNAVAILABLE -> ShareOutcome.Unavailable("No active native window/share service")
                    else -> ShareOutcome.Failed(ShareFailureReason.Platform, "Native sharing failed")
                }
                if (result == null) delay(25)
            }
            result
        } ?: ShareOutcome.Failed(ShareFailureReason.TimedOut, "Native sharing timed out")
    } finally {
        NativeShareBridge.cancelShare(id) // Idempotent even after a consumed completion.
    }
}
