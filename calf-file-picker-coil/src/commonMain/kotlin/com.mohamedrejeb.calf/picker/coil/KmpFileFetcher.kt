// Modified for NativeCmpKit (2026-11-08): stream KmpFile content through an owned bounded adapter.
package com.mohamedrejeb.calf.picker.coil

import coil3.ImageLoader
import coil3.decode.DataSource
import coil3.decode.ImageSource
import coil3.fetch.FetchResult
import coil3.fetch.Fetcher
import coil3.fetch.SourceFetchResult
import coil3.request.Options
import com.mohamedrejeb.calf.core.PlatformContext
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.source
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.io.IOException
import kotlinx.io.RawSource
import kotlinx.io.readByteArray
import okio.Buffer
import okio.BufferedSource
import okio.Source
import okio.Timeout
import okio.buffer

expect fun coil3.PlatformContext.toCalfPlatformContext(): PlatformContext

class KmpFileFetcher internal constructor(
    private val file: KmpFile,
    private val options: Options,
    private val openSource: suspend (KmpFile, PlatformContext) -> RawSource,
    private val wrapSource: (BufferedSource) -> ImageSource,
) : Fetcher {

    constructor(file: KmpFile, options: Options) : this(
        file = file,
        options = options,
        openSource = { target, context -> target.source(context) },
        wrapSource = { source -> ImageSource(source = source, fileSystem = options.fileSystem) },
    )

    override suspend fun fetch(): FetchResult {
        // Do not open an owned source for a caller that is already cancelled.
        currentCoroutineContext().ensureActive()
        val rawSource = openSource(file, options.context.toCalfPlatformContext())
        try {
            // Opening may have suspended. Re-check before handing ownership to Coil, and keep
            // this check inside the cleanup block so a cancelled open closes the raw source once.
            currentCoroutineContext().ensureActive()
            val source = KmpFileOkioSource(rawSource = rawSource).buffer()
            return SourceFetchResult(
                source = wrapSource(source),
                mimeType = null,
                dataSource = DataSource.MEMORY,
            )
        } catch (failure: Throwable) {
            try {
                rawSource.close()
            } catch (cleanup: Throwable) {
                failure.addSuppressed(cleanup)
            }
            throw failure
        }
    }

    class Factory : Fetcher.Factory<KmpFile> {
        override fun create(
            data: KmpFile,
            options: Options,
            imageLoader: ImageLoader,
        ): Fetcher {
            return KmpFileFetcher(data, options)
        }
    }
}

/**
 * Adapts a [RawSource] to [okio.Source] for Coil while bounding every underlying read to
 * [READ_BUFFER_SIZE] bytes. Closing this source closes the raw source exactly once, so the
 * successful [SourceFetchResult] can hand ownership to Coil without retaining a second copy.
 *
 * A raw read that appends bytes and then throws leaves those bytes buffered here. The next
 * read delivers them before touching the raw source again, so no successfully read bytes are
 * lost and the returned count always matches the bytes appended to the caller's sink.
 */
internal class KmpFileOkioSource(
    private val rawSource: RawSource,
    private val readBufferSize: Int = READ_BUFFER_SIZE,
) : Source {

    private val chunk = kotlinx.io.Buffer()
    private var closed = false

    init {
        require(readBufferSize > 0) { "readBufferSize must be positive" }
    }

    override fun read(sink: Buffer, byteCount: Long): Long {
        check(!closed) { "closed" }
        require(byteCount >= 0L) { "byteCount < 0: $byteCount" }
        if (byteCount == 0L) return 0L

        if (chunk.size > 0L) {
            // Deliver bytes retained by a previous raw read that appended them and then threw.
            val retainedCount = minOf(byteCount, chunk.size, readBufferSize.toLong())
            val retained = chunk.readByteArray(retainedCount.toInt())
            sink.write(retained)
            return retained.size.toLong()
        }

        val requested = minOf(byteCount, readBufferSize.toLong())
        val read = rawSource.readAtMostTo(chunk, requested)
        when {
            read == -1L -> return -1L
            read == 0L -> {
                // A positive request must either make progress or report EOF. Returning zero
                // here would make buffered callers spin on the same request forever.
                throw IOException("RawSource returned 0 bytes for a positive read request")
            }
            read < 0L -> throw IOException("RawSource returned an invalid read count: $read")
        }
        if (chunk.size < read) {
            throw IOException(
                "RawSource returned $read bytes but appended only ${chunk.size}",
            )
        }
        val copied = minOf(read, byteCount)
        sink.write(chunk.readByteArray(copied.toInt()))
        return copied
    }

    override fun timeout(): Timeout = Timeout.NONE

    override fun close() {
        if (closed) return
        closed = true
        rawSource.close()
    }

    internal companion object {
        internal const val READ_BUFFER_SIZE: Int = 8 * 1024
    }
}
