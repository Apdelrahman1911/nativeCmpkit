// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.picker.coil

import coil3.ImageLoader
import coil3.decode.DataSource
import coil3.decode.ImageSource
import coil3.fetch.FetchResult
import coil3.fetch.Fetcher
import coil3.fetch.SourceFetchResult
import coil3.request.Options
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.source
import com.mohamedrejeb.calf.io.getSize
import com.mohamedrejeb.calf.io.getMimeType
import com.mohamedrejeb.calf.core.PlatformContext
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.io.IOException
import kotlinx.io.okio.asOkioSource
import okio.buffer

expect fun coil3.PlatformContext.toCalfPlatformContext(): PlatformContext
internal expect val browserFileBuffering: Boolean

class KmpFileFetcher(
    private val file: KmpFile,
    private val options: Options,
) : Fetcher {
    private var maxInMemoryBytes: Int = DEFAULT_BROWSER_MAX_BYTES

    /** Native/JVM sources stream. Browsers must buffer, so they have an explicit configurable cap. */
    constructor(file: KmpFile, options: Options, maxInMemoryBytes: Int) : this(file, options) {
        require(maxInMemoryBytes >= 0) { "maxInMemoryBytes must not be negative" }
        this.maxInMemoryBytes = maxInMemoryBytes
    }

    override suspend fun fetch(): FetchResult {
        val context = options.context.toCalfPlatformContext()
        currentCoroutineContext().ensureActive()
        if (browserFileBuffering) {
            val size = file.getSize(context)
            if (size == null || size < 0 || size > maxInMemoryBytes) {
                throw IOException("Browser image exceeds the $maxInMemoryBytes byte in-memory limit")
            }
        }
        val source = file.source(context).asOkioSource().buffer()
        try {
            currentCoroutineContext().ensureActive()
            return SourceFetchResult(
                source = ImageSource(source = source, fileSystem = options.fileSystem),
                mimeType = file.getMimeType(context),
                dataSource = if (browserFileBuffering) DataSource.MEMORY else DataSource.DISK,
            ) // Coil now owns/ closes the stream, including its iOS security-scope lease.
        } catch (failure: Throwable) {
            try { source.close() } catch (cleanup: Throwable) { failure.addSuppressed(cleanup) }
            throw failure
        }
    }

    class Factory() : Fetcher.Factory<KmpFile> {
        private var maxInMemoryBytes: Int = DEFAULT_BROWSER_MAX_BYTES

        constructor(maxInMemoryBytes: Int) : this() {
            require(maxInMemoryBytes >= 0) { "maxInMemoryBytes must not be negative" }
            this.maxInMemoryBytes = maxInMemoryBytes
        }
        override fun create(
            data: KmpFile,
            options: Options,
            imageLoader: ImageLoader,
        ): Fetcher {
            return KmpFileFetcher(data, options, maxInMemoryBytes)
        }
    }

    companion object {
        /** Browsers have no synchronous streaming File source; caller can lower/raise this cap. */
        const val DEFAULT_BROWSER_MAX_BYTES: Int = 64 * 1024 * 1024
    }
}
