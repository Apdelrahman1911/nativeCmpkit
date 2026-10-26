// Adapted from MohamedRejeb/Calf PR #551; nativeCmpkit adds single-flight and lost-byte state.
package com.mohamedrejeb.calf.picker

import android.net.Uri
import androidx.compose.runtime.saveable.Saver
import com.mohamedrejeb.calf.io.KmpFile

internal sealed interface SaveSource {
    class Bytes(val bytes: ByteArray) : SaveSource
    class File(val file: KmpFile) : SaveSource
}

/** One ActivityResult request; payload state is shared across recompositions, not in a local var. */
internal class PendingSaveSource {
    private var source: SaveSource? = null
    private var waiting = false
    private var busy = false

    fun set(source: SaveSource) {
        check(!busy) { "A save is already in progress" }
        busy = true
        waiting = true
        this.source = source
    }

    /** Null means a duplicate/unexpected result. A non-null request with no source means lost bytes. */
    fun consume(): Request? {
        if (!waiting) return null
        waiting = false
        return Request(source).also { source = null }
    }

    fun finish() { source = null; waiting = false; busy = false }
    class Request(val source: SaveSource?)

    internal fun savedState(): String = when {
        !waiting -> "idle"
        source is SaveSource.File -> "uri:" + (source as SaveSource.File).file.uri
        else -> "bytes-lost"
    }

    companion object {
        internal fun restore(value: String): PendingSaveSource = PendingSaveSource().apply {
            when {
                value.startsWith("uri:") -> set(SaveSource.File(KmpFile(Uri.parse(value.removePrefix("uri:")))))
                value == "bytes-lost" -> { busy = true; waiting = true }
            }
        }
        // Never place a possibly huge ByteArray in an Activity's saved-state Bundle.
        val Saver: Saver<PendingSaveSource, String> = Saver(
            save = { it.savedState() },
            restore = { restore(it) },
        )
    }
}
