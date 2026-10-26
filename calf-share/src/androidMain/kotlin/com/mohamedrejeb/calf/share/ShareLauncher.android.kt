// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share

import android.app.Activity
import android.content.ClipData
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import android.net.Uri
import android.os.Handler
import android.os.Looper
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.FileProvider
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import java.io.File

@ExperimentalCalfApi
@Composable
actual fun rememberShareLauncher(onResult: (ShareResult) -> Unit): ShareLauncher =
    rememberShareOutcomeLauncher { onResult(it.toLegacyResult()) }

@ExperimentalCalfApi
@Composable
actual fun rememberShareOutcomeLauncher(options: ShareOptions, onResult: (ShareOutcome) -> Unit): ShareLauncher {
    val context = LocalContext.current
    val currentResult by rememberUpdatedState(onResult)
    val currentOptions by rememberUpdatedState(options)
    val active = remember(context) { object { var disposed = false } }
    DisposableEffect(active) { onDispose { active.disposed = true } }
    return remember(context, active) {
        ShareLauncher { content ->
            onAndroidShareMain {
                if (!active.disposed) {
                    deliverAndroidShareResult(context, content, currentOptions) { currentResult(it) }
                }
            }
        }
    }
}

@ExperimentalCalfApi
@Stable
actual class ShareLauncher actual constructor(private val onLaunch: (ShareContent) -> Unit) {
    actual fun launch(content: ShareContent) { onLaunch(content.snapshot()) }
}

/** Deliberately outside launchAndroidShare's catch: an application exception is not a failed launch. */
internal fun deliverAndroidShareResult(context: Context, content: ShareContent, options: ShareOptions, onResult: (ShareOutcome) -> Unit) {
    val result = launchAndroidShare(context, content, options)
    onResult(result)
}

internal fun launchAndroidShare(context: Context, content: ShareContent, options: ShareOptions): ShareOutcome {
    content.validationFailure()?.let { return it }
    return try {
        val intent = content.toShareIntent(context, options)
        val chooser = Intent.createChooser(intent, null)
        if (context.findActivity() == null) chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(chooser)
        ShareOutcome.Presented // Android chooser launch is not delivery or even recipient selection.
    } catch (error: Exception) {
        val reason = when (error) {
            is SecurityException -> ShareFailureReason.Permission
            is IllegalArgumentException -> ShareFailureReason.Configuration
            else -> ShareFailureReason.Platform
        }
        ShareOutcome.Failed(reason, error.message ?: "Could not present Android share chooser")
    }
}

internal fun ShareContent.toShareIntent(context: Context, options: ShareOptions): Intent {
    val text = when (this) { is ShareContent.Text -> text; is ShareContent.Url -> url; else -> null }
    val subject = when (this) { is ShareContent.Text -> subject; is ShareContent.Url -> subject; is ShareContent.File -> subject; is ShareContent.Files -> subject }
    if (text != null) return Intent(Intent.ACTION_SEND).apply {
        type = "text/plain"
        putExtra(Intent.EXTRA_TEXT, text)
        subject?.let { putExtra(Intent.EXTRA_SUBJECT, it) }
    }
    val files = when (this) { is ShareContent.File -> listOf(file); is ShareContent.Files -> files; else -> emptyList() }
    require(files.isNotEmpty()) { "At least one file is required" }
    val mime = when (this) { is ShareContent.File -> mimeType; is ShareContent.Files -> mimeType; else -> "application/octet-stream" }
    val uris = files.map { file ->
        when (file.uri.scheme) {
            "content" -> file.uri
            "file" -> {
                val path = requireNotNull(file.uri.path) { "A local file URI needs a path" }
                FileProvider.getUriForFile(context, options.androidFileProviderAuthority ?: "${context.packageName}.provider", File(path))
            }
            else -> throw IllegalArgumentException("Only content:// or FileProvider-convertible file:// URIs can be shared")
        }
    }
    return Intent(if (uris.size == 1) Intent.ACTION_SEND else Intent.ACTION_SEND_MULTIPLE).apply {
        type = mime
        if (uris.size == 1) putExtra(Intent.EXTRA_STREAM, uris.single())
        else putParcelableArrayListExtra(Intent.EXTRA_STREAM, ArrayList(uris))
        subject?.let { putExtra(Intent.EXTRA_SUBJECT, it) }
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        clipData = ClipData.newUri(context.contentResolver, "shared files", uris.first()).also { clip ->
            uris.drop(1).forEach { clip.addItem(ClipData.Item(it)) }
        }
    }
}

private fun onAndroidShareMain(action: () -> Unit) {
    if (Looper.myLooper() == Looper.getMainLooper()) action() else Handler(Looper.getMainLooper()).post(action)
}
private fun Context.findActivity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.takeUnless { it === this }?.findActivity()
    else -> null
}
