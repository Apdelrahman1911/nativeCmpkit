package com.mohamedrejeb.calf.share

import androidx.compose.runtime.Composable
import com.mohamedrejeb.calf.core.ExperimentalCalfApi

/** Additive result contract: presentation/selection/copy are not proof of completed delivery. */
sealed interface ShareOutcome {
    data object Presented : ShareOutcome
    data object Selected : ShareOutcome
    /** The platform reports completion; this is not proof that a remote recipient read the content. */
    data object Completed : ShareOutcome
    data object CopiedToClipboard : ShareOutcome
    data object Dismissed : ShareOutcome
    data object Busy : ShareOutcome
    data class Unavailable(val reason: String) : ShareOutcome
    data class Failed(val reason: ShareFailureReason, val message: String) : ShareOutcome
}
enum class ShareFailureReason { InvalidContent, Configuration, Permission, Platform, TimedOut }

data class ShareOptions(
    /** API24+ local files require this host FileProvider; null retains ${'$'}{applicationId}.provider. */
    val androidFileProviderAuthority: String? = null,
    /** Desktop/browser fallback is clipboard-only for text/URLs. Files are never opened/executed. */
    val allowClipboardFallback: Boolean = true,
    /** Desktop native operations are cancellable and do not block an IO thread while waiting. */
    val desktopTimeoutMillis: Long = 300_000,
) {
    init { require(desktopTimeoutMillis in 1_000..600_000) { "Desktop timeout must be between 1 and 600 seconds" } }
}

/**
 * Uses the latest callback. Android reports Presented, not Completed. Desktop/browser may report
 * CopiedToClipboard. Browser launch must remain directly inside a user gesture. Disposal cancels
 * owned work/suppresses late results; it cannot retract content already handed to another app.
 */
@ExperimentalCalfApi
@Composable
expect fun rememberShareOutcomeLauncher(
    options: ShareOptions = ShareOptions(),
    onResult: (ShareOutcome) -> Unit,
): ShareLauncher

internal fun ShareOutcome.toLegacyResult(): ShareResult = when (this) {
    ShareOutcome.Presented, ShareOutcome.Selected, ShareOutcome.Completed, ShareOutcome.CopiedToClipboard -> ShareResult.Success
    ShareOutcome.Dismissed -> ShareResult.Dismissed
    ShareOutcome.Busy, is ShareOutcome.Unavailable, is ShareOutcome.Failed -> ShareResult.Unavailable
}

internal fun ShareContent.snapshot(): ShareContent = when (this) {
    is ShareContent.Files -> copy(files = files.toList())
    else -> this
}

internal fun ShareContent.validationFailure(): ShareOutcome.Failed? {
    val message = when (this) {
        is ShareContent.Files -> when {
            files.isEmpty() -> "At least one file is required"
            mimeType.isBlank() || mimeType.any { it == '\r' || it == '\n' } -> "A valid MIME type is required"
            else -> null
        }
        is ShareContent.File -> if (mimeType.isBlank() || mimeType.any { it == '\r' || it == '\n' }) "A valid MIME type is required" else null
        is ShareContent.Url -> if (url.isBlank()) "A non-empty URL is required" else null
        is ShareContent.Text -> null
    }
    return message?.let { ShareOutcome.Failed(ShareFailureReason.InvalidContent, it) }
}

/** Main/UI-thread-confined ownership token; late/duplicate completions cannot clear a new request. */
internal class ShareRequestGate {
    class Token
    private var active: Token? = null
    fun begin(): Token? = if (active != null) null else Token().also { active = it }
    fun finish(token: Token): Boolean = if (active !== token) false else { active = null; true }
    fun abandon() { active = null }
}
