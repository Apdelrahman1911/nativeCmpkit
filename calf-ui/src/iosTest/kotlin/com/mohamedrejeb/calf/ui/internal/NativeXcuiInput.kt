// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.internal

import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.Foundation.NSHomeDirectory
import platform.Foundation.NSJSONSerialization
import platform.Foundation.NSNumber
import platform.Foundation.NSProcessInfo
import platform.Foundation.NSThread
import platform.Foundation.create
import platform.Foundation.writeToFile
import platform.posix.usleep

@kotlin.native.concurrent.ThreadLocal
private var nativeInputSequence = 0

/**
 * Test-only rendezvous with an independent XCTest UI runner. Requests never
 * invoke a manager, delegate, private selector or synthetic control callback.
 * The runner attaches to this already-running nonce-bound library application
 * and uses public XCUI tap/type/coordinate input. Missing input is a failure.
 */
internal fun nativeXcuiInput(operation: String, fields: Map<String, Any> = emptyMap()): Map<*, *> {
    check(!NSThread.isMainThread) { "Native input must not block UIKit's main loop" }
    check(operation in setOf("alert-button", "alert-field", "tap", "drag"))
    val token = NSProcessInfo.processInfo.environment["NATIVECMPKIT_NATIVE_INPUT_TOKEN"] as? String
        ?: error("This test requires the independent XCTest native-input profile")
    check(Regex("[0-9a-f]{32}").matches(token))
    val directory = NSHomeDirectory() + "/Documents/NativeCmpKitInput/" + token
    val manager = NSFileManager.defaultManager
    check(manager.createDirectoryAtPath(directory, true, null, null))
    val sequence = ++nativeInputSequence
    check(sequence in 1..96) { "Native input budget exhausted" }
    val requestPath = "$directory/request-$sequence.json"
    val responsePath = "$directory/response-$sequence.json"
    check(!manager.fileExistsAtPath(requestPath) && !manager.fileExistsAtPath(responsePath))
    val request = NSJSONSerialization.dataWithJSONObject(
        mapOf("sequence" to sequence, "operation" to operation) + fields, 0u, null,
    ) ?: error("Native input request is not JSON")
    check(request.length <= 8192uL && request.writeToFile(requestPath, true))
    val deadline = NSProcessInfo.processInfo.systemUptime + 30.0
    while (!manager.fileExistsAtPath(responsePath)) {
        check(NSProcessInfo.processInfo.systemUptime < deadline) {
            "Independent XCTest did not acknowledge native input $sequence/$operation"
        }
        usleep(1000u) // Backoff only; the actual nonce/sequence response admits completion.
    }
    val data = NSData.create(contentsOfFile = responsePath) ?: error("Missing native input response")
    check(data.length <= 8192uL)
    val response = NSJSONSerialization.JSONObjectWithData(data, 0u, null) as? Map<*, *>
        ?: error("Native input response is not JSON")
    val observedSequence = when (val value = response["sequence"]) {
        is NSNumber -> value.intValue
        is Number -> value.toInt()
        else -> null
    }
    check(observedSequence == sequence)
    check(response["status"] == "delivered") {
        "Independent XCTest refused native input $sequence/$operation"
    }
    return response
}
