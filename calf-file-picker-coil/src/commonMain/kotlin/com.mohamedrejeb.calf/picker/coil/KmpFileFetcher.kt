// Modified for nativeCmpkit (2026-11-08): stream KmpFile content through an owned bounded adapter.
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
import kotlinx.io.IOException
import kotlinx.io.RawSource
import okio.Buffer
import okio.BufferedSource
import okio.Source
import okio.Timeout

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
        val rawSource = openSource(file, options.context.toCalfPlatformContext())
        val source = try {
            KmpFileOkioSource(rawSource = rawSource).buffer()
        } catch (failure: Throwable) {
            try {
                rawSource.close()
            } catch (cleanup: Throwable) {
                failure.addSuppressed(cleanup)
            }
            throw failure
        }
        try {
            return SourceFetchResult(
                source = wrapSource(source),
                mimeType = null,
                dataSource = DataSource.MEMORY,
            )
        } catch (failure: Throwable) {
            try {
                source.close()
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
        sink.write(chunk.readByteArray())
        return read
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
