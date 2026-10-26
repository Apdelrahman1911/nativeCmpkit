// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share

internal enum class WebShareResult { Completed, Dismissed, Unavailable, Failed }
internal expect fun isWebShareSupported(): Boolean
internal expect fun isClipboardSupported(): Boolean
internal expect fun webShareText(text: String, title: String?, onResult: (WebShareResult) -> Unit)
internal expect fun webShareUrl(url: String, title: String?, onResult: (WebShareResult) -> Unit)
internal expect fun webShareFile(file: org.w3c.files.File, title: String?, onResult: (WebShareResult) -> Unit)
internal expect fun webShareFiles(files: List<org.w3c.files.File>, title: String?, onResult: (WebShareResult) -> Unit)
/** Completes only when writeText's Promise settles; rejection is always observed. */
internal expect fun copyToClipboard(text: String, onResult: (Boolean) -> Unit)
