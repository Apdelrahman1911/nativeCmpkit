// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.InternalCalfApi
import com.mohamedrejeb.calf.core.PlatformContext
import kotlinx.io.RawSource
import kotlinx.io.Buffer
import kotlinx.io.files.Path
import kotlinx.io.files.SystemFileSystem

/** The returned stream owns its security-scope lease until close, including failure/cancellation cleanup. */
@OptIn(InternalCalfApi::class)
actual suspend fun KmpFile.source(context: PlatformContext): RawSource {
    val path = requireFilePath(context)
    val access = url.acquireSecurityScopedAccess()
    val source = try {
        SystemFileSystem.source(Path(path))
    } catch (failure: Throwable) {
        access.close()
        throw failure
    }
    return object : RawSource {
        override fun readAtMostTo(sink: Buffer, byteCount: Long): Long = source.readAtMostTo(sink, byteCount)
        override fun close() {
            try {
                source.close()
            } finally {
                access.close()
            }
        }
    }
}
