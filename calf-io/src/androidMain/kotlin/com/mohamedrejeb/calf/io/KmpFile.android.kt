// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.io

import android.content.ContentResolver
import android.net.Uri
import android.provider.OpenableColumns
import android.provider.DocumentsContract
import android.webkit.MimeTypeMap
import androidx.documentfile.provider.DocumentFile
import com.mohamedrejeb.calf.core.PlatformContext
import java.io.File
import java.io.FileNotFoundException
import java.io.InputStream
import java.util.Locale

actual class KmpFile(
    val uri: Uri,
) {
    actual companion object
}

actual fun KmpFile.exists(context: PlatformContext): Boolean =
    try {
        if (uri.scheme == ContentResolver.SCHEME_FILE) uri.path?.let(::File)?.exists() == true
        else context.contentResolver.query(metadataUri(context), null, null, null, null)?.use { it.moveToFirst() } == true
    } catch (e: Exception) {
        false
    }

/**
 * Reads the content of the file as a byte array
 *
 * @param context the context to use to open the file
 * @throws FileNotFoundException if the file is not found
 * @return the content of the file as a byte array
 */
@Throws(FileNotFoundException::class)
actual suspend fun KmpFile.readByteArray(context: PlatformContext): ByteArray {
    val inputStream =
        context.contentResolver.openInputStream(uri)
            ?: throw FileNotFoundException("File not found")

    return inputStream.readAndClose()
}

internal fun InputStream.readAndClose(): ByteArray = use { it.readBytes() }

actual fun KmpFile.getName(context: PlatformContext): String? {
    if (uri.scheme == ContentResolver.SCHEME_FILE) return uri.path?.let(::File)?.name
    return documentFile(context)?.name
}

/** A `content:` URI has no file system path, so only `file:` URIs have one. */
actual fun KmpFile.getPath(context: PlatformContext): String? =
    uri.takeIf { it.scheme == ContentResolver.SCHEME_FILE }?.path

actual fun KmpFile.toUriString(): String? = uri.toString()

actual fun KmpFile.Companion.fromUriString(uriString: String): KmpFile? = when {
    uriString.startsWith(PATH_SEPARATOR) -> KmpFile(Uri.fromFile(File(uriString)))
    else -> Uri.parse(uriString).takeIf { it.scheme in FILE_REFERENCE_SCHEMES }?.let(::KmpFile)
}

actual fun KmpFile.getSize(context: PlatformContext): Long? = when (uri.scheme) {
    ContentResolver.SCHEME_FILE -> uri.path?.let(::File)?.takeIf { it.isFile }?.length()
    else -> if (isDirectory(context)) null else queryProviderSize(context)
}

/** Asks the provider; a provider may not know the size, or may refuse the query. */
private fun KmpFile.queryProviderSize(context: PlatformContext): Long? =
    try {
        context.contentResolver.query(metadataUri(context), arrayOf(OpenableColumns.SIZE), null, null, null)?.use { cursor ->
            val column = cursor.getColumnIndex(OpenableColumns.SIZE)
            if (column >= 0 && cursor.moveToFirst() && !cursor.isNull(column)) cursor.getLong(column) else null
        }
    } catch (e: SecurityException) {
        null
    } catch (e: IllegalArgumentException) {
        null
    }

actual fun KmpFile.getMimeType(context: PlatformContext): String? {
    val providerType = if (uri.scheme == ContentResolver.SCHEME_CONTENT) {
        try {
            context.contentResolver.getType(uri)
        } catch (e: SecurityException) {
            null
        }
    } else {
        null
    }
    return providerType ?: mimeTypeFromName(context)
}

private fun KmpFile.mimeTypeFromName(context: PlatformContext): String? {
    val name = if (uri.scheme == ContentResolver.SCHEME_FILE) uri.lastPathSegment else getName(context)
    val extension = name?.substringAfterLast('.', missingDelimiterValue = "")?.lowercase(Locale.ROOT)
    return extension?.takeIf { it.isNotEmpty() }?.let { MimeTypeMap.getSingleton().getMimeTypeFromExtension(it) }
}

private const val PATH_SEPARATOR = "/"

private val FILE_REFERENCE_SCHEMES = setOf(ContentResolver.SCHEME_CONTENT, ContentResolver.SCHEME_FILE)

actual fun KmpFile.isDirectory(context: PlatformContext): Boolean {
    if (uri.scheme == ContentResolver.SCHEME_FILE) return uri.path?.let(::File)?.isDirectory == true
    return try {
        if (DocumentsContract.isDocumentUri(context, uri) || DocumentsContract.isTreeUri(uri)) {
            documentFile(context)?.isDirectory == true
        } else {
            // Openable providers (including FileProvider) need not implement the
            // DocumentsProvider-only mime_type query used by DocumentFile.
            // Their MIME contract is ContentResolver.getType, not that column.
            context.contentResolver.getType(uri) == DocumentsContract.Document.MIME_TYPE_DIR
        }
    } catch (_: SecurityException) {
        false
    } catch (_: IllegalArgumentException) {
        false
    }
}

/** Keep the original tree URI/grant, but query the document represented by that tree. */
private fun KmpFile.documentFile(context: PlatformContext): DocumentFile? = try {
    when {
        // A child /tree/root/document/child is both a tree and a document URI. Do not
        // turn it back into the tree root (fromTreeUri does exactly that).
        DocumentsContract.isDocumentUri(context, uri) -> DocumentFile.fromSingleUri(context, uri)
        DocumentsContract.isTreeUri(uri) && uri.pathSegments.size == 2 -> DocumentFile.fromTreeUri(context, uri)
        else -> DocumentFile.fromSingleUri(context, uri)
    }
} catch (_: SecurityException) {
    null
} catch (_: IllegalArgumentException) {
    null
}

private fun KmpFile.metadataUri(context: PlatformContext): Uri = documentFile(context)?.uri ?: uri

/**
 * Converts this [Uri] to a [KmpFile].
 */
fun Uri.toKmpFile(): KmpFile = KmpFile(this)

/**
 * Converts this [java.io.File] to a [KmpFile] by converting to a file [Uri].
 */
fun java.io.File.toKmpFile(): KmpFile = KmpFile(Uri.fromFile(this))
