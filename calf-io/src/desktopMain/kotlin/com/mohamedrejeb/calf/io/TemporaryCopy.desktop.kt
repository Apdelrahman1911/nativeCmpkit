package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.PlatformContext

actual fun KmpFile.releaseTemporaryCopy(context: PlatformContext): Boolean = false
