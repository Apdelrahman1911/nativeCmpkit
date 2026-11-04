// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)
package com.mohamedrejeb.calf.ui.web

import kotlinx.cinterop.*
import platform.Foundation.*
import platform.posix.getpid
import platform.posix.usleep
import kotlin.test.*

/** Synchronous numeric control stays on the generated Worker; UIKit's real main loop stays live. */
internal class IosContentPolicyFixture(val method: String) {
    companion object {
        const val unicode = "Ελληνικά العربية 漢字 café 🙂"
        const val resourceUnicode = "ресурс 日本語 café 🙂"
        fun inline(title: String, relativeResources: Boolean = false): String =
            "<!doctype html><meta charset='utf-8'><link rel='icon' href='data:,'><title>$title</title>" +
                "<p id='policy-document'>$unicode</p><p id='relative-resource-text'></p>" +
                if (relativeResources) "<link rel='stylesheet' href='probe.css'><script defer src='probe.js'></script><img id='relative-image' src='probe.svg'>" else ""
    }
    private val environment = NSProcessInfo.processInfo.environment
    private val token = assertNotNull(environment["NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN"] as? String).also {
        assertTrue(Regex("[0-9a-f]{32}").matches(it), "Missing fresh nonce-owned content fixture")
    }
    private val ports = listOf(port("NATIVECMPKIT_WEBVIEW_CONTENT_ORIGIN_PORT"), port("NATIVECMPKIT_WEBVIEW_CONTENT_SECOND_PORT"))
    private val pid = getpid()
    init {
        assertFalse(NSThread.isMainThread)
        assertTrue(method in listOf("restore", "replay", "headers", "resources"))
        assertNotEquals(ports[0], ports[1])
        assertEquals(pid, control("open/$method/$pid").getValue("pid"))
    }
    val initialHeaders get() = mapOf("X-NativeCmpKit-Initial" to "fixture-only-$token", "Authorization" to "NativeCmpKitFixture $token")
    fun url(stage: String, origin: Int = 0) = base(stage, origin, "page")
    fun baseUrl(stage: String) = base(stage, 0, "base") + "/"
    private fun base(stage: String, origin: Int, kind: String): String {
        assertTrue(Regex("[a-z0-9-]{1,40}").matches(stage) && origin in 0..1)
        return "http://localhost:${ports[origin]}/$token/$kind/$method/$stage"
    }
    fun stats(stage: String) = control("stats/$method/$stage/$pid")
    fun title(stage: String, counts: Map<String, Int>) = "$method-$stage-${counts.getValue("page")}" +
        if (method == "headers") "-h${counts.getValue("main_initial")}-a${counts.getValue("main_authorization")}" else ""
    fun awaitStage(stage: String, predicate: (Map<String, Int>) -> Boolean): Map<String, Int> {
        assertFalse(NSThread.isMainThread)
        val deadline = NSProcessInfo.processInfo.systemUptime + 10.0
        while (true) {
            val observed = stats(stage)
            if (predicate(observed)) return observed
            check(NSProcessInfo.processInfo.systemUptime < deadline) { "Timed out awaiting fixed content-policy HTTP counters" }
            usleep(50_000u)
        }
    }
    fun complete() { assertEquals(1, control("done/$method/$pid").getValue("done")) }
    private fun port(name: String) = assertNotNull((environment[name] as? String)?.toIntOrNull()).also {
        assertTrue(it in 1..65535, "Missing owned loopback content-policy port")
    }
    private fun control(action: String): Map<String, Int> = memScoped {
        assertFalse(NSThread.isMainThread, "Never block UIApplicationMain with fixture control")
        assertTrue(Regex("[a-z0-9/-]{1,120}").matches(action))
        val response = alloc<ObjCObjectVar<NSURLResponse?>>().apply { value = null }
        val failure = alloc<ObjCObjectVar<NSError?>>().apply { value = null }
        val request = NSMutableURLRequest().apply {
            setURL(assertNotNull(NSURL.URLWithString("http://localhost:${ports[0]}/$token/control/$action")))
            setTimeoutInterval(2.0)
        }
        val data = NSURLConnection.sendSynchronousRequest(request, response.ptr, failure.ptr)
        assertTrue(failure.value == null, "Owned content control failed; nativeCode=${failure.value?.code}")
        assertEquals(200L, (response.value as? NSHTTPURLResponse)?.statusCode)
        val body = assertNotNull(data)
        assertTrue(body.length in 1uL..2048uL, "Control response exceeds finite numeric protocol")
        val text = assertNotNull(body.bytes).reinterpret<ByteVar>().readBytes(body.length.toInt()).decodeToString()
        val result = mutableMapOf<String, Int>()
        text.trimEnd('\n').split('\n').forEach { line ->
            assertTrue(Regex("[a-z_]+=[0-9]{1,10}").matches(line), "Unreviewed content control record")
            val (key, value) = line.split('=')
            assertTrue(key !in result, "Duplicate owned content counter")
            result[key] = assertNotNull(value.toIntOrNull())
        }
        result
    }
}
