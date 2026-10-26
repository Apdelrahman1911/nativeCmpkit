package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.PlatformContext

/**
 * Releases a library-owned picked-file temporary copy, if this handle owns one (currently iOS).
 * Never removes an original file, an arbitrary URI, a bookmark or another handle's data.
 * Call only after all readers/native consumers are finished. A released handle must not be read.
 * Temporary storage may also be purged by the OS; copy to app permanent storage to retain it.
 * Returns true only when this call removed its owned temporary directory; otherwise false.
 */
expect fun KmpFile.releaseTemporaryCopy(context: PlatformContext): Boolean

fun KmpFile.releaseTemporaryCopy(): Boolean = releaseTemporaryCopy(resolveContext())
