// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.share

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri

/** Native negative control: owning caller can query, but no URI may be granted. */
class GrantlessShareProvider : ContentProvider() {
    override fun onCreate() = true
    override fun getType(uri: Uri): String {
        if (uri.lastPathSegment == "throw") throw SecurityException("Intentional synthetic provider exception")
        return "application/octet-stream"
    }
    override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor =
        MatrixCursor(arrayOf("_display_name", "_size"))
    override fun insert(uri: Uri, values: ContentValues?): Uri? = throw SecurityException("No fixture mutation")
    override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?) = throw SecurityException("No fixture mutation")
    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?) = throw SecurityException("No fixture mutation")
}
