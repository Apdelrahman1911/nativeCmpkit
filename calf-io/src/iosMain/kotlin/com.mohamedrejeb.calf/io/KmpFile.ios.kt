// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
// Modified for NativeCmpKit (2026-10-27): checked copying keeps the Foundation data receiver alive.
@file:OptIn(com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.core.PlatformContext
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.io.IOException
import kotlinx.io.files.FileNotFoundException
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.Foundation.NSURL
import platform.Foundation.NSFileSize
import platform.Foundation.NSFileType
import platform.Foundation.NSFileTypeRegular
import platform.Foundation.NSNumber
import platform.Foundation.NSURLIsDirectoryKey
import platform.UniformTypeIdentifiers.UTType
import platform.Foundation.dataWithContentsOfURL
import kotlin.concurrent.AtomicInt

/**
 * A wrapper class for a file in the platform-specific implementation.
 *
 * @property url The readable location. Picker copies live in app temporary storage, not permanent
 * storage: call [releaseTemporaryCopy] when finished, and copy elsewhere for long-term storage.
 * It keeps the picked file's name, and [getPath] returns its path.
 * @property originalUrl The original URL returned by the file picker. May become inaccessible
 * due to iOS security scoping — use for metadata only ([getName], [toUriString]).
 *
 * Content and filesystem metadata require a `file:` [url]. The public NSURL constructor is
 * retained, but wrapping an HTTP or other non-file URL does not download it or grant access to
 * a local file with the same path. For such URLs, reads throw, [exists]/[isDirectory] return
 * false, and [getPath]/[getSize] return null; original name/URI metadata remains available.
 */
actual class KmpFile @InternalCalfApi constructor(
    val url: NSURL,
    val originalUrl: NSURL,
) {
    @OptIn(InternalCalfApi::class)
    constructor(url: NSURL) : this(originalUrl = url, url = url)

    /** The access held by a file reopened from a bookmark; given up by [releaseBookmark]. */
    internal var bookmarkAccess: SecurityScopedAccess? = null
        private set

    internal constructor(url: NSURL, bookmarkAccess: SecurityScopedAccess) : this(url) {
        this.bookmarkAccess = bookmarkAccess
    }

    private var temporaryCopyRelease: (() -> Boolean)? = null
    private val temporaryCopyReleased = AtomicInt(0)

    /** Only the picker attaches ownership of a library-created temporary directory. */
    @InternalCalfApi
    constructor(url: NSURL, originalUrl: NSURL, releaseTemporaryCopy: () -> Boolean) : this(url, originalUrl) {
        temporaryCopyRelease = releaseTemporaryCopy
    }

    internal fun releaseOwnedTemporaryCopy(): Boolean {
        val release = temporaryCopyRelease ?: return false
        if (!temporaryCopyReleased.compareAndSet(0, 1)) return false
        return release()
    }

    actual companion object
}

@OptIn(InternalCalfApi::class)
actual fun KmpFile.exists(context: PlatformContext): Boolean {
    val path = getPath(context) ?: return false
    return url.withSecurityScopedAccess { NSFileManager.defaultManager.fileExistsAtPath(path) }
}

@OptIn(ExperimentalForeignApi::class, InternalCalfApi::class)
actual suspend fun KmpFile.readByteArray(context: PlatformContext): ByteArray {
    requireFilePath(context) // Never let NSData reinterpret a non-file URL as a network read.
    val data = url.withSecurityScopedAccess { NSData.dataWithContentsOfURL(url) }
        ?: throw IOException("Could not read the file")
    return data.toCheckedByteArray()
}

actual fun KmpFile.getName(context: PlatformContext): String? =
    originalUrl.lastPathComponent

/**
 * The path of [KmpFile.url], the copy the app can read, so the path can be opened directly; a
 * picked file's copy keeps the picked file's name. Only a `file:` URL has a path, and
 * [NSURL.path] is already percent-decoded.
 */
actual fun KmpFile.getPath(context: PlatformContext): String? =
    url.takeIf { it.isFileURL() }?.path

/** One authority check for both native whole-file and streaming reads. */
internal fun KmpFile.requireFilePath(context: PlatformContext): String =
    getPath(context) ?: throw FileNotFoundException("iOS KmpFile content requires a file: URL with a filesystem path")

/** The URL of the original file, for example to reopen a picked folder later. */
actual fun KmpFile.toUriString(): String? = originalUrl.absoluteString

actual fun KmpFile.Companion.fromUriString(uriString: String): KmpFile? {
    val url = when {
        uriString.startsWith(FILE_URL_PREFIX) -> NSURL(string = uriString)
        uriString.startsWith(PATH_SEPARATOR) -> NSURL.fileURLWithPath(uriString)
        else -> null
    }
    return url?.takeIf { it.isFileURL() }?.let(::KmpFile)
}

/** The size of the readable file; a directory has none. */
@OptIn(ExperimentalForeignApi::class, InternalCalfApi::class)
actual fun KmpFile.getSize(context: PlatformContext): Long? {
    val path = getPath(context) ?: return null
    val attributes = url.withSecurityScopedAccess {
        NSFileManager.defaultManager.attributesOfItemAtPath(path, error = null)
    } ?: return null
    if (attributes[NSFileType] != NSFileTypeRegular) return null
    return (attributes[NSFileSize] as? NSNumber)?.longLongValue
}

/** The MIME type registered for the original file's extension. */
@OptIn(ExperimentalForeignApi::class)
actual fun KmpFile.getMimeType(context: PlatformContext): String? {
    val extension = originalUrl.pathExtension?.lowercase()?.takeIf { it.isNotEmpty() } ?: return null
    return UTType.typeWithFilenameExtension(extension)?.preferredMIMEType
}

private const val FILE_URL_PREFIX = "file:"
private const val PATH_SEPARATOR = "/"

@OptIn(ExperimentalForeignApi::class, InternalCalfApi::class)
actual fun KmpFile.isDirectory(context: PlatformContext): Boolean {
    if (getPath(context) == null) return false
    val result = url.withSecurityScopedAccess {
        url.resourceValuesForKeys(listOf(NSURLIsDirectoryKey), error = null)
    }
    return result?.get(NSURLIsDirectoryKey) == true
}

/**
 * Runs a synchronous [block] under a balanced security scope. A URL that is not security
 * scoped is accessed as is. This does not acquire a missing grant and must not return a stream
 * or another operation that needs the scope after the block returns; use [acquireSecurityScopedAccess].
 */
@InternalCalfApi
inline fun <T> NSURL.withSecurityScopedAccess(block: () -> T): T {
    val access = acquireSecurityScopedAccess()
    try {
        return block()
    } finally {
        access.close()
    }
}

/**
 * Converts this [NSURL] to a [KmpFile].
 */
fun NSURL.toKmpFile(): KmpFile = KmpFile(this)
