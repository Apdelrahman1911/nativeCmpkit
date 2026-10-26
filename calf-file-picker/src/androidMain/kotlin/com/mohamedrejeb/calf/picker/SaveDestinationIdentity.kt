package com.mohamedrejeb.calf.picker

import android.content.ContentResolver
import android.net.Uri
import android.provider.DocumentsContract
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import java.io.File
import java.io.IOException

/**
 * Recognizes aliases the platform can identify, not just matching serialized URIs.
 * ACTION_CREATE_DOCUMENT promises a new document; opaque IDs from different providers cannot
 * establish physical identity. A provider violating that contract remains an explicit limitation.
 */
internal fun ContentResolver.saveUrisReferToSameFile(source: Uri, destination: Uri): Boolean {
    if (source == destination) return true
    if (source.scheme == ContentResolver.SCHEME_FILE && destination.scheme == ContentResolver.SCHEME_FILE) {
        val first = source.path?.let(::File) ?: return false
        val second = destination.path?.let(::File) ?: return false
        if (first.canonicalFile == second.canonicalFile) return true
        // stat follows symlinks and also detects hard links on supported Android filesystems.
        // A failed/placeholder identity is not evidence of either equality or difference.
        // Refuse before opening any destination stream. In particular, inode 0 can be a
        // filesystem/adapter's unknown value; treating two zeros as equal invents success,
        // while treating them as different could truncate a hard-linked original.
        val firstStat = Os.stat(first.path)
        if (firstStat.st_ino == 0L) throw IOException("The source file identity is unavailable")
        val secondStat = try {
            Os.stat(second.path)
        } catch (failure: ErrnoException) {
            // Only an absent destination, after the source was identified, permits creation.
            if (failure.errno == OsConstants.ENOENT) return false
            throw failure
        }
        if (secondStat.st_ino == 0L) throw IOException("The destination file identity is unavailable")
        return firstStat.st_dev == secondStat.st_dev && firstStat.st_ino == secondStat.st_ino
    }
    if (source.scheme != ContentResolver.SCHEME_CONTENT || destination.scheme != ContentResolver.SCHEME_CONTENT) return false
    if (source.authority == destination.authority) {
        val firstId = documentId(source)
        val secondId = documentId(destination)
        if (firstId != null && firstId == secondId) return true
    }
    // Some non-SAF providers offer stable canonical identities. Failure or no support is normal.
    val firstCanonical = runCatching { canonicalize(source) }.getOrNull()
    val secondCanonical = runCatching { canonicalize(destination) }.getOrNull()
    return firstCanonical != null && (firstCanonical == destination || firstCanonical == secondCanonical) ||
        secondCanonical != null && secondCanonical == source
}

private fun documentId(uri: Uri): String? =
    runCatching { DocumentsContract.getDocumentId(uri) }.getOrNull()
        ?: runCatching { DocumentsContract.getTreeDocumentId(uri) }.getOrNull()
