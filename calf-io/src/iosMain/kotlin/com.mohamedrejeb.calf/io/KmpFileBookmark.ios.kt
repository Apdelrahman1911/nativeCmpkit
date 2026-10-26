@file:OptIn(com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.core.PlatformContext
import kotlinx.cinterop.ExperimentalForeignApi
import platform.Foundation.NSData
import platform.Foundation.NSURL
import platform.Foundation.base64EncodedStringWithOptions
import platform.Foundation.create

/**
 * A bookmark of the location the user picked. iOS needs no bookmark flags for this: the
 * security-scope flags exist only on macOS.
 */
@OptIn(ExperimentalForeignApi::class, InternalCalfApi::class)
actual fun KmpFile.createBookmark(context: PlatformContext): String? {
    if (!originalUrl.isFileURL()) return null
    val data = originalUrl.withSecurityScopedAccess {
        originalUrl.bookmarkDataWithOptions(
            options = 0u,
            includingResourceValuesForKeys = null,
            relativeToURL = null,
            error = null,
        )
    } ?: return null
    return data.base64EncodedStringWithOptions(0u)
}

/**
 * The reopened file starts its security-scoped access at once and holds it until
 * [releaseBookmark]. Starting access per operation on paths rebuilt from the URL is not enough
 * after a device restart, while access held on the resolved URL covers the files inside a folder.
 */
@OptIn(ExperimentalForeignApi::class)
actual fun KmpFile.Companion.fromBookmark(bookmark: String, context: PlatformContext): KmpFile? {
    if (bookmark.isEmpty()) return null
    val data = NSData.create(base64EncodedString = bookmark, options = 0u) ?: return null
    val url = NSURL.URLByResolvingBookmarkData(
        bookmarkData = data,
        options = 0u,
        relativeToURL = null,
        bookmarkDataIsStale = null,
        error = null,
    ) ?: return null
    if (!url.isFileURL()) return null
    val access = url.acquireSecurityScopedAccess()
    val file = KmpFile(url, access)
    if (!file.exists(context)) {
        access.close()
        return null
    }
    return file
}

actual fun KmpFile.releaseBookmark(context: PlatformContext) {
    bookmarkAccess?.close()
}
