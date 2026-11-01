// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

import platform.Foundation.NSMutableURLRequest
import platform.Foundation.NSURL

// Typecheck only; do not execute this function. No network or native test is here.
fun foundationTimeoutSetterSignatureOnly(url: NSURL): Double =
    NSMutableURLRequest().apply {
        setURL(url)
        setTimeoutInterval(2.0)
    }.timeoutInterval
