// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import java.io.ByteArrayOutputStream
import java.io.Closeable
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.UUID
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference

/** Identical test-only JVM transport on desktop/Android; no provider interception or URL handler. */
internal class OwnedWebViewContentPolicyHttpFixture private constructor(val method: String) : Closeable {
    companion object {
        const val unicode = "Ελληνικά العربية 漢字 café 🙂"
        const val resourceUnicode = "ресурс 日本語 café 🙂"
        val stages = mapOf(
            "restore" to listOf("url", "navigator", "redirect", "final", "html-recovery", "null-recovery"),
            "replay" to listOf("get", "one-time", "form", "posted", "safe"),
            "headers" to listOf("state", "navigator").flatMap { entry ->
                listOf("initial", "same", "same-final", "cross", "cross-final", "link").map { "$entry-$it" }
            },
            "resources" to listOf("state", "navigator").flatMap { entry -> listOf("utf8", "utf8-alias").map { "$entry-$it" } },
            "unsupported" to listOf("seed", "state-headers", "navigator-headers", "state-base", "navigator-base", "recovery"),
        )
        val counters = listOf("get", "post", "page", "redirect", "script", "style", "image",
            "main_initial", "main_authorization", "script_initial", "script_authorization", "style_initial", "style_authorization",
            "image_initial", "image_authorization", "unexpected_initial", "unexpected_authorization", "response_bytes", "closed", "pending")
        fun create(method: String): OwnedWebViewContentPolicyHttpFixture {
            check(method in stages) { "Unknown finite content-policy method" }
            return OwnedWebViewContentPolicyHttpFixture(method)
        }
        fun inline(title: String, baseUrl: String? = null): String =
            "<!doctype html><meta charset='utf-8'><link rel='icon' href='data:,'><title>$title</title>" +
                "<p id='policy-document'>$unicode</p><p id='relative-resource-text'></p>" +
                if (baseUrl != null) "<link rel='stylesheet' href='probe.css'><script defer src='probe.js'></script>" +
                    "<img id='relative-image' src='probe.svg'>" else ""
    }
    private val token = UUID.randomUUID().toString().replace("-", "")
    private val lock = Any()
    private val counts = stages.getValue(method).associateWith { counters.associateWith { 0 }.toMutableMap() }
    private val listeners = mutableListOf<ServerSocket>()
    private val acceptors = mutableListOf<Thread>()
    private val sockets = ConcurrentHashMap.newKeySet<Socket>()
    private val connections = AtomicInteger()
    private val closing = AtomicBoolean()
    private val failure = AtomicReference<Throwable>()
    private val workers = ThreadPoolExecutor(8, 8, 0, TimeUnit.MILLISECONDS, ArrayBlockingQueue(16),
        { action -> Thread(action, "nativecmpkit-owned-content-policy-worker").apply { isDaemon = true } },
        ThreadPoolExecutor.AbortPolicy())
    private var reported = false
    init {
        try {
            repeat(2) { origin ->
                val listener = ServerSocket(0, 16, InetAddress.getByName("127.0.0.1"))
                listeners += listener
                val acceptor = Thread({ accept(listener, origin) }, "nativecmpkit-owned-content-origin-$origin").apply { isDaemon = true }
                acceptors += acceptor
                acceptor.start()
            }
        } catch (error: Throwable) { runWebViewCleanup(error, { close() }) }
    }
    val initialHeaders: Map<String, String> get() = mapOf("X-NativeCmpKit-Initial" to "fixture-only-$token",
        "Authorization" to "NativeCmpKitFixture $token") // Dummy fixture-only values, never user credentials.
    fun url(stage: String, origin: Int = 0): String = base(stage, origin, "page")
    fun baseUrl(stage: String, origin: Int = 0): String = base(stage, origin, "base") + "/"
    private fun base(stage: String, origin: Int, kind: String): String {
        check(stage in counts && origin in 0..1 && !closing.get()) { "Unknown or closed finite fixture URL" }
        return "http://127.0.0.1:${listeners[origin].localPort}/$token/$kind/$method/$stage"
    }
    fun stats(stage: String): Map<String, Int> = synchronized(lock) {
        assertHealthy()
        counts[stage]?.toMap() ?: error("Unknown finite content-policy stage")
    }
    fun title(stage: String, observed: Map<String, Int> = stats(stage)): String = "$method-$stage-${observed.getValue("page")}" +
        if (method == "headers") "-h${observed.getValue("main_initial")}-a${observed.getValue("main_authorization")}" else ""
    fun assertHealthy() { failure.get()?.let { throw AssertionError("Owned content-policy HTTP fixture failed", it) } }
    fun isIdle(): Boolean = synchronized(lock) { counts.values.all { it.getValue("pending") == 0 } }
    fun report() {
        assertHealthy()
        check(isIdle() && !reported) { "Report only once after actual owned HTTP drains" }
        reported = true
        counts.keys.forEach { stage ->
            val observed = stats(stage)
            // Fixed stage names and numeric facts only: no nonce/URL/header/body/credentials.
            println("NATIVECMPKIT_WEBVIEW_CONTENT_POLICY method=$method stage=$stage " +
                counters.joinToString(" ") { "$it=${observed.getValue(it)}" })
        }
    }
    private fun record(error: Throwable) { failure.compareAndSet(null, error) }
    private fun closeSocket(socket: Socket) {
        try { socket.close(); check(socket.isClosed) { "Owned socket close was not observed" }; sockets -= socket }
        catch (error: Throwable) { record(error) }
    }
    private fun accept(listener: ServerSocket, origin: Int) {
        while (!closing.get()) {
            var acquired: Socket? = null
            try {
                val socket = listener.accept().also { acquired = it; sockets += it }
                check(connections.incrementAndGet() <= 512) { "Owned content connection budget exceeded" }
                workers.execute { serve(socket, origin) }
                acquired = null
            } catch (error: Throwable) {
                acquired?.let(::closeSocket)
                if (!closing.get()) { record(error); return }
            }
        }
    }
    private fun serve(socket: Socket, origin: Int) {
        var owned: MutableMap<String, Int>? = null
        try {
            val input = socket.getInputStream()
            val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(3)
            val raw = ByteArrayOutputStream()
            var tail = 0
            while (tail != 0x0d0a0d0a) {
                val remaining = deadline - System.nanoTime()
                check(remaining > 0 && raw.size() < 8192) { "Owned HTTP header budget exceeded" }
                socket.soTimeout = TimeUnit.NANOSECONDS.toMillis(remaining).coerceIn(1, 3000).toInt()
                val byte = input.read()
                check(byte >= 0 && byte < 128) { "Owned HTTP header is incomplete or non-ASCII" }
                raw.write(byte); tail = (tail shl 8) or byte
            }
            val lines = raw.toString("US-ASCII").split("\r\n")
            val first = lines.first().split(' ')
            check(first.size == 3 && first[0] in listOf("GET", "POST") && first[2] in listOf("HTTP/1.0", "HTTP/1.1")) {
                "Unreviewed owned HTTP request line"
            }
            val headers = mutableMapOf<String, String>()
            lines.drop(1).filter { it.isNotEmpty() }.forEach { line ->
                val colon = line.indexOf(':'); check(colon > 0) { "Invalid owned header" }
                val key = line.take(colon).lowercase(java.util.Locale.ROOT)
                check(Regex("[a-z0-9-]+").matches(key) && key !in headers) { "Duplicate or invalid owned header" }
                val value = line.drop(colon + 1).trim()
                check(value.all { it.code >= 32 || it == '\t' }) { "Invalid owned header byte" }
                headers[key] = value
            }
            check("transfer-encoding" !in headers) { "Chunked fixture ingress is unsupported" }
            val lengthText = headers["content-length"] ?: "0"
            check(Regex("[0-9]{1,4}").matches(lengthText)) { "Invalid finite body size" }
            val size = lengthText.toInt()
            check(size in 0..512 && (first[0] != "GET" || size == 0)) { "Owned HTTP body budget exceeded" }
            val body = ByteArray(size)
            var received = 0
            while (received < size) {
                val remaining = deadline - System.nanoTime()
                check(remaining > 0) { "Owned form deadline exceeded" }
                socket.soTimeout = TimeUnit.NANOSECONDS.toMillis(remaining).coerceIn(1, 3000).toInt()
                val count = input.read(body, received, size - received)
                check(count > 0) { "Incomplete owned form" }; received += count
            }
            val path = first[1]
            check(Regex("/[a-zA-Z0-9./-]+").matches(path) && ".." !in path) { "Unowned route syntax" }
            val parts = path.trim('/').split('/')
            check(parts.size in 4..5 && parts[0] == token && parts[2] == method && parts[3] in counts) { "Foreign or unknown fixture route" }
            val kind = parts[1]; val stage = parts[3]; val asset = parts.getOrNull(4)
            val role = when (asset) { "probe.js" -> "script"; "probe.css" -> "style"; "probe.svg" -> "image"; null -> "main"; else -> error("Unknown relative fixture asset") }
            check((kind == "page" && asset == null) || (kind == "base" && asset != null)) { "Unknown finite fixture route kind" }
            check(first[0] != "POST" || (method == "replay" && stage == "posted" && asset == null && body.contentEquals("nativecmpkit_form=fixture-only".toByteArray()))) {
                "Unsupported owned form submission"
            }
            val (wireBody, mime, status, location) = synchronized(lock) {
                check(!reported) { "A completed native method attempted further fixture work" }
                val count = counts.getValue(stage)
                check(count.getValue("get") + count.getValue("post") < 12) { "Owned stage request budget exceeded" }
                val initial = if (headers["x-nativecmpkit-initial"] == initialHeaders.getValue("X-NativeCmpKit-Initial")) 1 else 0
                val authorization = if (headers["authorization"] == initialHeaders.getValue("Authorization")) 1 else 0
                fun add(key: String, amount: Int = 1) { count[key] = count.getValue(key) + amount }
                add(first[0].lowercase(java.util.Locale.ROOT)); add("pending"); owned = count
                add("${role}_initial", initial); add("${role}_authorization", authorization)
                add("unexpected_initial", if ("x-nativecmpkit-initial" in headers && initial == 0) 1 else 0)
                add("unexpected_authorization", if ("authorization" in headers && authorization == 0) 1 else 0)
                var location: String? = null
                if (method == "restore" && stage == "redirect") location = url("final", origin)
                else if (method == "headers" && (stage.endsWith("-same") || stage.endsWith("-cross")))
                    location = url("$stage-final", if (stage.endsWith("-cross")) 1 else origin)
                when {
                    asset == null && method == "headers" && stage.endsWith("-initial") && (initial == 0 || authorization == 0) ->
                        Reply("Exact dummy fixture authentication is required", "text/plain", 403)
                    asset == "probe.js" -> {
                        add("script")
                        Reply("document.documentElement.setAttribute('data-policy-script','h$initial-a$authorization');" +
                            "document.getElementById('relative-resource-text').textContent='$resourceUnicode';", "application/javascript; charset=utf-8")
                    }
                    asset == "probe.css" -> { add("style"); Reply("#policy-document { color: rgb(17, 34, 51); }", "text/css; charset=utf-8") }
                    asset == "probe.svg" -> { add("image"); Reply("<svg xmlns='http://www.w3.org/2000/svg' width='7' height='9'><rect width='7' height='9' fill='#123'/></svg>", "image/svg+xml") }
                    location != null -> { add("redirect"); Reply("", "text/plain", 302, location) }
                    method == "replay" && stage == "one-time" && count.getValue("get") > 1 -> {
                        record(AssertionError("One-time fixture URL was repeated")); Reply("One-time URL refused", "text/plain", 409)
                    }
                    method == "replay" && stage == "posted" && first[0] != "POST" -> {
                        record(AssertionError("POST-only fixture result was loaded by GET")); Reply("POST result refused", "text/plain", 405)
                    }
                    else -> {
                        add("page")
                        val resources = if (method == "headers") {
                            val base = baseUrl(stage, origin)
                            "<link rel='stylesheet' href='${base}probe.css'><script defer src='${base}probe.js'></script><img id='relative-image' src='${base}probe.svg'>"
                        } else ""
                        val link = when {
                            method == "headers" -> "<a id='policy-link' href='${url(stage.substringBefore('-') + "-link", origin)}'>later link</a>"
                            method == "replay" && stage == "form" -> "<form id='policy-form' method='post' action='${url("posted", origin)}'><input name='nativecmpkit_form' value='fixture-only'><button type='submit'>submit</button></form>"
                            else -> ""
                        }
                        Reply(inline(title(stage, count)) + resources + link, "text/html; charset=utf-8")
                    }
                }
            }
            val payload = wireBody.toByteArray(Charsets.UTF_8)
            val response = ("HTTP/1.1 $status Fixture\r\nContent-Type: $mime\r\nContent-Length: ${payload.size}\r\n" +
                "Connection: close\r\nCache-Control: no-store, no-cache, max-age=0\r\n" +
                (location?.let { "Location: $it\r\n" } ?: "") + "\r\n").toByteArray(Charsets.US_ASCII) + payload
            socket.getOutputStream().apply { write(response); flush() }
            synchronized(lock) { owned?.let { it["response_bytes"] = it.getValue("response_bytes") + response.size } }
        } catch (error: Throwable) {
            if (!closing.get() || error !is java.io.IOException) record(error)
        } finally {
            closeSocket(socket)
            synchronized(lock) { owned?.let { it["pending"] = it.getValue("pending") - 1; it["closed"] = it.getValue("closed") + 1 } }
        }
    }
    private data class Reply(val body: String, val mime: String, val status: Int = 200, val location: String? = null)
    override fun close() {
        if (!closing.compareAndSet(false, true)) { assertHealthy(); return }
        runWebViewCleanup(null,
            *listeners.map { listener -> { listener.close() } }.toTypedArray(),
            { sockets.toList().forEach(::closeSocket) },
            *acceptors.map { thread -> { thread.join(4000); check(!thread.isAlive) { "Owned acceptor survived cleanup" } } }.toTypedArray(),
            { workers.shutdown(); check(workers.awaitTermination(4, TimeUnit.SECONDS)) { "Owned workers survived cleanup" } },
            { check(sockets.isEmpty() && listeners.all { it.isClosed } && isIdle()) { "Owned socket/HTTP leases survived cleanup" } },
            { assertHealthy() },
        )
    }
}
