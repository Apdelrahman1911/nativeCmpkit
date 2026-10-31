// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.net.Uri
import android.provider.DocumentsContract

/** Fixed public synthetic values shared with the independent Java source fixture. */
internal object AndroidIoProviderContract {
    const val PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.iodocuments"
    const val AUTHORITY = "$PACKAGE.documents"
    const val PERMISSION = "$PACKAGE.CONTROL_IO"
    const val ROOT = "nativecmpkit-owned-root"
    const val ROOT_NAME = "NativeCmpKit owned IO folder"
    val tree: Uri get() = DocumentsContract.buildTreeDocumentUri(AUTHORITY, ROOT)
    fun child(id: String): Uri {
        require(id in setOf("bookmark.txt", "decoder.bin", "cancel.bin", "survivor.bin"))
        return DocumentsContract.buildDocumentUriUsingTree(tree, id)
    }
    fun bytes(id: String): ByteArray = when (id) {
        "bookmark.txt" -> "NativeCmpKit actual Android bookmark bytes".encodeToByteArray()
        "decoder.bin" -> ByteArray(32771) { (it % 251).toByte() }
        "cancel.bin" -> ByteArray(32779) { (it % 251).toByte() }
        "survivor.bin" -> ByteArray(8199) { (it % 251).toByte() }
        else -> error("Unknown fixed owned document")
    }
}
