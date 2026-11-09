package com.mohamedrejeb.calf.share

import androidx.compose.runtime.Immutable
import com.mohamedrejeb.calf.io.KmpFile

/**
 * Represents content that can be shared using [ShareLauncher].
 *
 * Subject support depends on the platform and receiving application. On iOS, a
 * non-null subject is supplied through each activity item's subject selector. On
 * the web, it becomes the Web Share API's `title` for text, URLs and files, not a
 * guaranteed email subject. Null omits this metadata; an empty string is supplied
 * unchanged. Receiving applications may ignore either kind of metadata.
 *
 * Desktop subjects are unsupported by both the native JNI share sheet and the
 * clipboard/browse/open fallbacks. The web clipboard fallback also has no subject
 * channel. These routes preserve the original payload without inserting a subject
 * into its text, URL or filename. A successful result is not proof of subject delivery.
 *
 * Web file sharing forwards the original browser `File` objects, including their
 * names and MIME types. [File.mimeType] and [Files.mimeType] do not override those
 * objects' metadata. The web API does not provide separate email subject, recipient
 * or per-file title fields.
 */
@Immutable
sealed interface ShareContent {

    /**
     * Share plain text.
     *
     * @param text The text to share.
     * @param subject Optional subject metadata; see [ShareContent] for platform support.
     */
    data class Text(
        val text: String,
        val subject: String? = null,
    ) : ShareContent

    /**
     * Share a URL. On iOS, this may show a rich link preview.
     *
     * @param url The URL string to share.
     * @param subject Optional subject metadata; see [ShareContent] for platform support.
     */
    data class Url(
        val url: String,
        val subject: String? = null,
    ) : ShareContent

    /**
     * Share a single file.
     *
     * @param file The file to share.
     * @param mimeType The MIME type of the file (e.g., "image/png", "application/pdf").
     * @param subject Optional subject metadata; see [ShareContent] for platform support.
     */
    data class File(
        val file: KmpFile,
        val mimeType: String,
        val subject: String? = null,
    ) : ShareContent

    /**
     * Share multiple files.
     *
     * @param files The files to share.
     * @param mimeType The MIME type of the files (e.g., `image/\*`).
     * @param subject Optional subject metadata; see [ShareContent] for platform support.
     */
    data class Files(
        val files: List<KmpFile>,
        val mimeType: String,
        val subject: String? = null,
    ) : ShareContent
}
