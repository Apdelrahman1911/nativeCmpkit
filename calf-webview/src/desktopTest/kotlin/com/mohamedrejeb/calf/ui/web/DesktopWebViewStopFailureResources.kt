// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import javafx.scene.web.WebEngine
import java.lang.management.ManagementFactory
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import java.util.jar.JarFile

private const val STOP_FAILURE_RESOURCE_PREFIX = "NATIVECMPKIT_WINDOWS_STOP_RESOURCES_V1 "
private const val STOP_FAILURE_RESOURCE_MAX_ARCHIVE_BYTES = 67_108_864L
private const val STOP_FAILURE_RESOURCE_MAX_ENTRY_BYTES = 98_304
private const val STOP_FAILURE_RESOURCE_MAX_RECORD_CHARS = 2_048
private const val STOP_FAILURE_RESOURCE_READ_BUDGET_NANOS = 250_000_000L
private const val STOP_FAILURE_RESOURCE_SCOPE = "anchor-code-source-base-entries-only"
private val STOP_FAILURE_RESOURCE_ENTRIES = listOf(
    "WebView" to "javafx/scene/web/WebView.class",
    "WebEngine" to "javafx/scene/web/WebEngine.class",
    "LoadWorker" to "javafx/scene/web/WebEngine\$LoadWorker.class",
    "WebPage" to "com/sun/webkit/WebPage.class",
    "NetworkContext" to "com/sun/webkit/network/NetworkContext.class",
    "URLLoader" to "com/sun/webkit/network/URLLoader.class",
    "HTTP2Loader" to "com/sun/webkit/network/HTTP2Loader.class",
    "HTTP2BodySubscriber" to "com/sun/webkit/network/HTTP2Loader\$3.class",
)

private const val STOP_FAILURE_FRAME_THREAD_CAP = 256
private const val STOP_FAILURE_FRAME_DEPTH_CAP = 32
private const val STOP_FAILURE_FRAME_TOTAL_CAP = 8_192
private const val STOP_FAILURE_FRAME_RECORD_CAP = 640
private const val STOP_FAILURE_FRAME_SCOPE = "executing-method-names-only"
private data class StopFailureFrameTarget(val label: String, val className: String, val methodName: String)
private val STOP_FAILURE_FRAME_TARGETS = listOf(
    StopFailureFrameTarget("urlRun", "com.sun.webkit.network.URLLoader", "run"),
    StopFailureFrameTarget("urlResponse", "com.sun.webkit.network.URLLoader", "receiveResponse"),
    StopFailureFrameTarget("urlClose", "com.sun.webkit.network.URLLoader", "close"),
    StopFailureFrameTarget("urlCancel", "com.sun.webkit.network.URLLoader", "fwkCancel"),
    StopFailureFrameTarget("http2Cancel", "com.sun.webkit.network.HTTP2Loader", "fwkCancel"),
    StopFailureFrameTarget("http2Subscribe", "com.sun.webkit.network.HTTP2Loader\$3", "onSubscribe"),
    StopFailureFrameTarget("http2Next", "com.sun.webkit.network.HTTP2Loader\$3", "onNext"),
    StopFailureFrameTarget("http2Demand", "com.sun.webkit.network.HTTP2Loader\$3", "requestIfNotCancelled"),
    StopFailureFrameTarget("responseCode", "java.net.HttpURLConnection", "getResponseCode"),
)

/**
 * Unapplied test-only proposal, called only after the original public Stop refusal.
 * The native WebView class and WebEngine have already been used by that fixture.
 * Hashes only fixed base entries in their same-file, file-scheme code-source archive;
 * class literals do not inspect private fields or create another engine/loader.
 *
 * These are resource fingerprints, NOT transformed loaded code, native DLL hashes,
 * a complete JAR digest, the active loader branch, or a cancellation/cause witness.
 * Properties below are failure-time observations, not NetworkContext's initial choice.
 * The cooperative 250ms read budget cannot preempt blocking file I/O or stderr output.
 * Failure-frame queries share that same cooperative budget and likewise cannot preempt a
 * blocking public management call. The frame record is a method-name observation only:
 * not a loaded-Class origin, a unique held-request association, or cancellation history.
 * Missing frames stay unknown; an asynchronous pre-header HTTP2 request may have none.
 * The caller must retain its runCatching wrapper and original refusal/cause/cleanup.
 */
internal fun captureWindowsStopFailureResources(nativeType: Class<*>) {
    var phase = "windows-gate"
    val record = try {
        val os = System.getProperty("os.name")
        if (os == null || os.length > 64 || !os.startsWith("Windows", ignoreCase = true)) return
        val startedAt = System.nanoTime()
        phase = "anchors"
        check(nativeType.name == "javafx.scene.web.WebView")
        val engineType = WebEngine::class.java
        check(nativeType.classLoader === engineType.classLoader)
        val archive = stopFailureResourceArchive(nativeType)
        val engineArchive = stopFailureResourceArchive(engineType)
        check(Files.isSameFile(archive, engineArchive))
        val before = Files.readAttributes(archive, BasicFileAttributes::class.java, NOFOLLOW_LINKS)
        check(before.isRegularFile && before.size() in 1L..STOP_FAILURE_RESOURCE_MAX_ARCHIVE_BYTES)
        checkStopFailureResourceBudget(startedAt)
        phase = "archive-resources"
        val resources = JarFile(archive.toFile(), false, JarFile.OPEN_READ, JarFile.baseVersion()).use { jar ->
            STOP_FAILURE_RESOURCE_ENTRIES.map { (label, name) ->
                checkStopFailureResourceBudget(startedAt)
                val entry = checkNotNull(jar.getJarEntry(name))
                check(!entry.isDirectory && entry.size in 1L..STOP_FAILURE_RESOURCE_MAX_ENTRY_BYTES.toLong())
                val digest = MessageDigest.getInstance("SHA-256")
                var count = 0
                val buffer = ByteArray(8_192)
                jar.getInputStream(entry).use { input ->
                    while (true) {
                        checkStopFailureResourceBudget(startedAt)
                        val read = input.read(buffer)
                        if (read < 0) break
                        check(read > 0 && read <= STOP_FAILURE_RESOURCE_MAX_ENTRY_BYTES - count)
                        count += read
                        digest.update(buffer, 0, read)
                    }
                }
                check(count.toLong() == entry.size)
                val sha256 = digest.digest().joinToString("") { (it.toInt() and 0xff).toString(16).padStart(2, '0') }
                "{\"name\":\"$label\",\"bytes\":$count,\"sha256\":\"$sha256\"}"
            }
        }
        phase = "metadata-stability"
        val after = Files.readAttributes(archive, BasicFileAttributes::class.java, NOFOLLOW_LINKS)
        check(after.isRegularFile && before.size() == after.size() &&
            before.lastModifiedTime() == after.lastModifiedTime() && before.creationTime() == after.creationTime() &&
            before.fileKey() == after.fileKey())
        checkStopFailureResourceBudget(startedAt)
        phase = "record"
        val runtimeVersion = stopFailureResourceVersionProperty()
        val http2Property = stopFailureResourceHttp2Property()
        val javaFeature = Runtime.version().feature()
        check(javaFeature in 1..99)
        checkStopFailureResourceBudget(startedAt)
        val frameSnapshot = stopFailureThreadSnapshot(startedAt)
        val json = "{\"schema\":1,\"capture\":\"captured\",\"scope\":\"$STOP_FAILURE_RESOURCE_SCOPE\"," +
            "\"anchorCodeSourcesSameFile\":true,\"metadataStable\":true,\"fileKeyAvailable\":${before.fileKey() != null}," +
            "\"archiveBytes\":${before.size()},\"javaFeature\":$javaFeature,\"javafxRuntimeVersionProperty\":\"$runtimeVersion\"," +
            "\"http2LoaderPropertyAtFailure\":\"$http2Property\",\"resources\":[${resources.joinToString(",")}],\"frameSnapshot\":$frameSnapshot }"
        check(json.length + STOP_FAILURE_RESOURCE_PREFIX.length <= STOP_FAILURE_RESOURCE_MAX_RECORD_CHARS)
        json
    } catch (_: Throwable) {
        "{\"schema\":1,\"capture\":\"refused\",\"scope\":\"$STOP_FAILURE_RESOURCE_SCOPE\",\"phase\":\"$phase\"}"
    }
    // At most one bounded emission attempt; no arbitrary path/property/exception text.
    try {
        if (record.length + STOP_FAILURE_RESOURCE_PREFIX.length <= STOP_FAILURE_RESOURCE_MAX_RECORD_CHARS) {
            System.err.println(STOP_FAILURE_RESOURCE_PREFIX + record)
        }
    } catch (_: Throwable) { /* Never mask or suppress into the original owning refusal. */ }
}

private fun stopFailureResourceArchive(type: Class<*>): Path {
    val location = checkNotNull(type.protectionDomain?.codeSource?.location)
    check(location.protocol == "file")
    val uri = location.toURI()
    check(uri.authority.isNullOrEmpty() && uri.query == null && uri.fragment == null)
    return Paths.get(uri).normalize().also { check(it.isAbsolute) }
}

private fun checkStopFailureResourceBudget(startedAt: Long) {
    check(System.nanoTime() - startedAt <= STOP_FAILURE_RESOURCE_READ_BUDGET_NANOS)
}

private fun stopFailureResourceVersionProperty(): String = try {
    val value = System.getProperty("javafx.runtime.version")
    when {
        value == null -> "absent"
        value.length <= 32 && Regex("[0-9]{1,3}(\\.[0-9]{1,3}){1,3}(\\+[0-9]{1,6})?").matches(value) -> value
        else -> "noncanonical"
    }
} catch (_: Throwable) { "unavailable" }

private fun stopFailureResourceHttp2Property(): String = try {
    when (val value = System.getProperty("com.sun.webkit.useHTTP2Loader")) {
        null -> "absent"
        else -> when {
            value.equals("true", ignoreCase = true) -> "true"
            value.equals("false", ignoreCase = true) -> "false"
            else -> "noncanonical"
        }
    }
} catch (_: Throwable) { "unavailable" }

/**
 * One public-JDK existing-thread snapshot after the original owning refusal. Counts are
 * frame occurrences, not callback/event counts. Same-stack pairs are observations of
 * method names in one returned stack, not direct call-edge or unique request proofs.
 *
 * A URLLoader response/close plus getResponseCode frame can narrow a response-code
 * API-phase hypothesis, conditional on the used bodies. No flag/private-field reads,
 * Class.forName, thread action, transport action, raw stack or originating path occurs.
 * Normal HTTP2 body Subscription cancellation remains in the unchanged JavaFX code;
 * no observed frame does not mean no loader, no cancellation, or no pending request.
 */
private fun stopFailureThreadSnapshot(startedAt: Long): String {
    var phase = "bean"
    return try {
        checkStopFailureResourceBudget(startedAt)
        val bean = ManagementFactory.getThreadMXBean()
        phase = "thread-ids"
        checkStopFailureResourceBudget(startedAt)
        val ids = bean.allThreadIds
        if (ids.size > STOP_FAILURE_FRAME_THREAD_CAP) {
            return "{\"capture\":\"refused\",\"scope\":\"$STOP_FAILURE_FRAME_SCOPE\",\"phase\":\"thread-cap\"}"
        }
        phase = "stack-query"
        checkStopFailureResourceBudget(startedAt)
        val rows = bean.getThreadInfo(ids, STOP_FAILURE_FRAME_DEPTH_CAP)
        check(rows.size == ids.size)
        val counts = IntArray(STOP_FAILURE_FRAME_TARGETS.size)
        var available = 0
        var unavailable = 0
        var examined = 0
        var responseWithCode = 0
        var closeWithCode = 0
        phase = "scan"
        for (row in rows) {
            checkStopFailureResourceBudget(startedAt)
            if (row == null) { unavailable++; continue }
            available++
            val stack = row.stackTrace
            check(stack.size <= STOP_FAILURE_FRAME_DEPTH_CAP)
            check(stack.size <= STOP_FAILURE_FRAME_TOTAL_CAP - examined)
            examined += stack.size
            var responseSeen = false
            var closeSeen = false
            var codeSeen = false
            for (frame in stack) {
                checkStopFailureResourceBudget(startedAt)
                for (index in STOP_FAILURE_FRAME_TARGETS.indices) {
                    val target = STOP_FAILURE_FRAME_TARGETS[index]
                    if (frame.className == target.className && frame.methodName == target.methodName) {
                        counts[index]++
                        when (target.label) {
                            "urlResponse" -> responseSeen = true
                            "urlClose" -> closeSeen = true
                            "responseCode" -> codeSeen = true
                        }
                    }
                }
            }
            if (responseSeen && codeSeen) responseWithCode++
            if (closeSeen && codeSeen) closeWithCode++
        }
        phase = "record"
        checkStopFailureResourceBudget(startedAt)
        check(counts.all { it in 0..STOP_FAILURE_FRAME_TOTAL_CAP })
        val values = STOP_FAILURE_FRAME_TARGETS.indices.joinToString(",") { index ->
            "\"${STOP_FAILURE_FRAME_TARGETS[index].label}\":${counts[index]}"
        }
        val json = "{\"capture\":\"captured\",\"scope\":\"$STOP_FAILURE_FRAME_SCOPE\",\"threads\":${ids.size}," +
            "\"available\":$available,\"unavailable\":$unavailable,\"examined\":$examined," +
            "\"occurrences\":{$values},\"responseWithCode\":$responseWithCode,\"closeWithCode\":$closeWithCode}"
        check(json.length <= STOP_FAILURE_FRAME_RECORD_CAP)
        json
    } catch (_: Throwable) {
        "{\"capture\":\"refused\",\"scope\":\"$STOP_FAILURE_FRAME_SCOPE\",\"phase\":\"$phase\"}"
    }
}
