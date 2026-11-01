// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import java.io.EOFException
import java.net.InetAddress
import java.net.SocketException
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.attribute.PosixFilePermission
import java.security.KeyStore
import java.security.cert.CertificateException
import java.security.cert.X509Certificate
import java.util.UUID
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.KeyManagerFactory
import javax.net.ssl.SSLContext
import javax.net.ssl.SSLException
import javax.net.ssl.SSLServerSocket
import javax.net.ssl.SSLSocket
import javax.net.ssl.TrustManagerFactory
import javax.net.ssl.X509TrustManager
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

internal enum class DesktopTlsStage(val trusted: Boolean, val leftRgb: Int, val rightRgb: Int) {
    Seed(true, 0xc0392b, 0x2471a3),
    Untrusted(false, 0x884ea0, 0x616a6b),
    Recovery(true, 0x239b56, 0xd4ac0d),
}

/** NEW PRIVATE DRAFT: no fixture key, system trust-store, HTTP client or server is shared with another class/JVM. */
internal class OwnedDesktopTlsFixture private constructor(
    private val certificates: Certificates,
    private val lease: StrictTrustLease,
    private val trusted: Endpoint,
    private val untrusted: Endpoint,
    private val nonce: String,
) : AutoCloseable {
    private val closing = AtomicBoolean()
    private val cleanupFailure = AtomicReference<Throwable>()
    private fun endpoint(stage: DesktopTlsStage) = if (stage.trusted) trusted else untrusted
    fun url(stage: DesktopTlsStage) = endpoint(stage).url(stage)
    fun title(stage: DesktopTlsStage) = "nativecmpkit-tls-$nonce-${stage.name}"
    fun responses(stage: DesktopTlsStage) = endpoint(stage).responses.getValue(stage).get()
    fun httpRequests(stage: DesktopTlsStage) = endpoint(stage).requests.getValue(stage).get()
    fun handshakeAttempts(stage: DesktopTlsStage) = endpoint(stage).handshakeAttempts.get()
    fun successfulHandshakes(stage: DesktopTlsStage) = endpoint(stage).handshakeSuccesses.get()
    fun assertHealthy() { trusted.assertHealthy(); untrusted.assertHealthy() }
    fun assertTrustLease() = lease.assertInstalled()
    // Called only after every original native SSL/error and zero-HTTP assertion.
    // This confirms the endpoint-level witness, never invents a native outcome.
    fun confirmNativeCertificateRejection() {
        assertTrustLease()
        trusted.assertHealthy()
        untrusted.confirmNativeCertificateRejection()
    }
    override fun close() {
        if (!closing.compareAndSet(false, true)) { cleanupFailure.get()?.let { throw it }; return }
        try {
            runWebViewCleanup(null,
                { trusted.close() }, { untrusted.close() },
                { lease.close() }, // Exact original SSLContext/factory, never a guessed default.
                { certificates.close() }, // Only the two owned files and their owned directory.
            )
        } catch (failure: Throwable) { cleanupFailure.set(failure); throw failure }
    }

    companion object {
        fun create(): OwnedDesktopTlsFixture {
            var certificates: Certificates? = null
            var lease: StrictTrustLease? = null
            var trusted: Endpoint? = null
            var untrusted: Endpoint? = null
            try {
                val material = Certificates.create().also { certificates = it }
                val installed = StrictTrustLease.create(material).also { lease = it }
                val nonce = UUID.randomUUID().toString().replace("-", "")
                val good = Endpoint.create(material.serverContext(true), true, nonce).also { trusted = it }
                val bad = Endpoint.create(material.serverContext(false), false, nonce).also { untrusted = it }
                return OwnedDesktopTlsFixture(material, installed, good, bad, nonce)
            } catch (failure: Throwable) {
                runWebViewCleanup(failure,
                    { trusted?.close() }, { untrusted?.close() }, { lease?.close() }, { certificates?.close() })
                throw failure
            }
        }
    }

    /** Both self-signed leafs are valid, RSA/SHA256/serverAuth and localhost/IP SAN-matching.
     * Only the positive leaf is a trust anchor. The negative varies trust, not host/protocol/HTTP transport. */
    private class Certificates private constructor(private val directory: Path) : AutoCloseable {
        private val password = "nativecmpkit-fixture-only".toCharArray() // Authored disposable test material, not a credential.
        private val paths = listOf(directory.resolve("positive.p12"), directory.resolve("untrusted.p12"))
        private val stores = paths.map { file ->
            check(Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS))
            KeyStore.getInstance("PKCS12").apply { Files.newInputStream(file).use { load(it, password) } }
        }
        val positive = stores[0].getCertificate("server") as X509Certificate
        val negative = stores[1].getCertificate("server") as X509Certificate
        init {
            for (certificate in listOf(positive, negative)) {
                certificate.checkValidity()
                certificate.verify(certificate.publicKey)
                assertEquals("RSA", certificate.publicKey.algorithm)
                assertTrue(assertNotNull(certificate.extendedKeyUsage).contains("1.3.6.1.5.5.7.3.1"))
                val sans = assertNotNull(certificate.subjectAlternativeNames)
                assertTrue(sans.any { it[0] == 7 && it[1] == "127.0.0.1" })
                assertTrue(sans.any { it[0] == 2 && it[1] == "localhost" })
            }
            check(!positive.encoded.contentEquals(negative.encoded))
        }
        fun serverContext(trusted: Boolean): SSLContext {
            val keys = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm())
            keys.init(stores[if (trusted) 0 else 1], password)
            return SSLContext.getInstance("TLS").apply { init(keys.keyManagers, null, null) }
        }
        override fun close() {
            runWebViewCleanup(null,
                { Files.deleteIfExists(paths[0]); check(!Files.exists(paths[0], LinkOption.NOFOLLOW_LINKS)) },
                { Files.deleteIfExists(paths[1]); check(!Files.exists(paths[1], LinkOption.NOFOLLOW_LINKS)) },
                { Files.delete(directory); check(!Files.exists(directory, LinkOption.NOFOLLOW_LINKS)) },
                { password.fill('\u0000') },
            )
        }
        companion object {
            fun create(): Certificates {
                val directory = Files.createTempDirectory("nativecmpkit-desktop-tls-")
                try {
                    if (Files.getFileStore(directory).supportsFileAttributeView("posix")) {
                        Files.setPosixFilePermissions(directory, setOf(PosixFilePermission.OWNER_READ,
                            PosixFilePermission.OWNER_WRITE, PosixFilePermission.OWNER_EXECUTE))
                    }
                    val windows = System.getProperty("os.name").startsWith("Windows")
                    val keytool = Path.of(System.getProperty("java.home"), "bin", if (windows) "keytool.exe" else "keytool")
                    check(Files.isRegularFile(keytool, LinkOption.NOFOLLOW_LINKS)) { "Actual owning JDK keytool is unavailable" }
                    for (filename in listOf("positive.p12", "untrusted.p12")) {
                        val process = ProcessBuilder(listOf(keytool.toString(), "-genkeypair", "-alias", "server",
                            "-keyalg", "RSA", "-keysize", "2048", "-sigalg", "SHA256withRSA", "-dname", "CN=localhost",
                            "-ext", "SAN=IP:127.0.0.1,DNS:localhost", "-ext", "EKU=serverAuth", "-startdate", "-1d",
                            "-validity", "3", "-storetype", "PKCS12", "-keystore", directory.resolve(filename).toString(),
                            "-storepass", "nativecmpkit-fixture-only", "-keypass", "nativecmpkit-fixture-only", "-noprompt"))
                            .redirectErrorStream(true).redirectOutput(ProcessBuilder.Redirect.DISCARD).start()
                        var primary: Throwable? = null
                        try {
                            check(process.waitFor(45, TimeUnit.SECONDS)) { "Owned certificate generation timed out" }
                            check(process.exitValue() == 0) { "Owned certificate generation returned nonzero" }
                        } catch (failure: Throwable) { primary = failure; throw failure }
                        finally {
                            runWebViewCleanup(primary, {
                                if (process.isAlive) {
                                    process.destroy()
                                    if (!process.waitFor(5, TimeUnit.SECONDS)) {
                                        process.destroyForcibly()
                                        check(process.waitFor(10, TimeUnit.SECONDS)) { "Owned keytool was not reaped" }
                                    }
                                }
                                check(!process.isAlive) { "Owned keytool remains alive" }
                            })
                        }
                    }
                    return Certificates(directory)
                } catch (failure: Throwable) {
                    // Never recurse through a guessed/shared tree; refusal to remove an
                    // unexpected residual file remains a cleanup failure, not success.
                    runWebViewCleanup(failure,
                        { Files.deleteIfExists(directory.resolve("positive.p12")) },
                        { Files.deleteIfExists(directory.resolve("untrusted.p12")) },
                        { Files.delete(directory) })
                    throw failure
                }
            }
        }
    }

    /** The standard PKIX manager sees exactly ONE owned anchor; no permissive TrustManager,
     * hostname verifier change, disabled algorithm change, JRE cacerts edit or loader override. */
    private class StrictTrustLease private constructor(private val strict: SSLContext) : AutoCloseable {
        private val previousContext = SSLContext.getDefault()
        private val previousFactory = HttpsURLConnection.getDefaultSSLSocketFactory()
        private val previousVerifier = HttpsURLConnection.getDefaultHostnameVerifier()
        private val strictFactory = strict.socketFactory
        private val closing = AtomicBoolean()
        init {
            try {
                SSLContext.setDefault(strict)
                HttpsURLConnection.setDefaultSSLSocketFactory(strictFactory)
                assertInstalled()
            } catch (failure: Throwable) {
                runWebViewCleanup(failure,
                    { SSLContext.setDefault(previousContext) },
                    { HttpsURLConnection.setDefaultSSLSocketFactory(previousFactory) },
                    { assertSame(previousVerifier, HttpsURLConnection.getDefaultHostnameVerifier()) })
            }
        }
        fun assertInstalled() {
            assertSame(strict, SSLContext.getDefault())
            assertSame(strictFactory, HttpsURLConnection.getDefaultSSLSocketFactory())
            assertSame(previousVerifier, HttpsURLConnection.getDefaultHostnameVerifier())
        }
        override fun close() {
            if (!closing.compareAndSet(false, true)) return
            runWebViewCleanup(null,
                { assertInstalled() },
                { SSLContext.setDefault(previousContext) },
                { HttpsURLConnection.setDefaultSSLSocketFactory(previousFactory) },
                { assertSame(previousContext, SSLContext.getDefault()) },
                { assertSame(previousFactory, HttpsURLConnection.getDefaultSSLSocketFactory()) },
                { assertSame(previousVerifier, HttpsURLConnection.getDefaultHostnameVerifier()) },
            )
        }
        companion object {
            fun create(material: Certificates): StrictTrustLease {
                val trust = KeyStore.getInstance("PKCS12").apply { load(null, null); setCertificateEntry("owned-positive", material.positive) }
                assertEquals(listOf("owned-positive"), trust.aliases().toList())
                val factory = TrustManagerFactory.getInstance("PKIX").apply { init(trust) }
                val manager = factory.trustManagers.single() as X509TrustManager
                assertEquals(1, manager.acceptedIssuers.size)
                assertTrue(manager.acceptedIssuers.single().encoded.contentEquals(material.positive.encoded))
                manager.checkServerTrusted(arrayOf(material.positive), "RSA")
                assertFailsWith<CertificateException> { manager.checkServerTrusted(arrayOf(material.negative), "RSA") }
                // Material checks are fixture validation, NEVER the native acceptance oracle.
                val strict = SSLContext.getInstance("TLS").apply { init(null, factory.trustManagers, null) }
                return StrictTrustLease(strict)
            }
        }
    }

    private class Endpoint private constructor(
        private val listener: SSLServerSocket,
        private val workers: ThreadPoolExecutor,
        private val trusted: Boolean,
        private val nonce: String,
    ) : AutoCloseable {
        val requests = DesktopTlsStage.entries.associateWith { AtomicInteger() }
        val responses = DesktopTlsStage.entries.associateWith { AtomicInteger() }
        val handshakeAttempts = AtomicInteger()
        val handshakeSuccesses = AtomicInteger()
        private val sockets = ConcurrentHashMap.newKeySet<SSLSocket>()
        private val closing = AtomicBoolean()
        private val connections = AtomicInteger()
        private enum class FailurePhase { Accept, Handshake, RequestHeaders, ResponseWrite, SocketClose }
        private data class RecordedFailure(val phase: FailurePhase, val error: Throwable)
        private val failure = AtomicReference<RecordedFailure>()
        private val rejectionLock = Any()
        private val pendingFinishedWrites = mutableListOf<Throwable>()
        private var nativeRejectionConfirmed = false // Guarded by rejectionLock; no automatic server-side confirmation.
        private val acceptor = Thread({ accept() }, "nativecmpkit-owned-tls-acceptor").apply { isDaemon = true }
        private fun path(stage: DesktopTlsStage) = "/nativecmpkit-tls-$nonce/${stage.name}"
        fun url(stage: DesktopTlsStage) = "https://127.0.0.1:${listener.localPort}${path(stage)}"
        private fun endpointFailure(error: Throwable, phase: String) = AssertionError(
            "Owned TLS fixture failed: endpoint=${if (trusted) "trusted" else "untrusted"} phase=$phase", error)
        fun assertHealthy() {
            failure.get()?.let { throw endpointFailure(it.error, it.phase.name) }
            synchronized(rejectionLock) {
                if (nativeRejectionConfirmed) assertRejectedEndpointStillZero()
                if (closing.get() && pendingFinishedWrites.isNotEmpty() && !nativeRejectionConfirmed) {
                    throw endpointFailure(pendingFinishedWrites.first(), "UnconfirmedFinishedWrite")
                }
            }
        }
        private fun assertRejectedEndpointStillZero() {
            check(!trusted && handshakeSuccesses.get() == 0 &&
                requests.values.all { it.get() == 0 } && responses.values.all { it.get() == 0 }) {
                "Owned TLS fixture failed: endpoint=untrusted phase=RejectedEndpointTlsOrHttp"
            }
        }
        fun confirmNativeCertificateRejection() {
            assertHealthy()
            synchronized(rejectionLock) {
                check(!trusted && !closing.get() && !nativeRejectionConfirmed) {
                    "Owned TLS fixture failed: endpoint=untrusted phase=InvalidRejectionConfirmation"
                }
                check(handshakeAttempts.get() >= 1) { "Native rejection needs an owned TLS attempt" }
                assertRejectedEndpointStillZero()
                nativeRejectionConfirmed = true
            }
            assertHealthy()
        }
        private fun record(error: Throwable, phase: FailurePhase) {
            if (!closing.get()) failure.compareAndSet(null, RecordedFailure(phase, error))
        }
        private fun observedFinishedWriteAbort(error: Throwable, phase: FailurePhase, handshaken: Boolean): Boolean {
            // Narrowly the original Linux/JDK17 TLS1.3 Finished-write Broken-pipe shape.
            // No other SocketException, trusted endpoint, post-handshake phase or shutdown is quarantined.
            if (trusted || handshaken || phase != FailurePhase.Handshake || closing.get() ||
                Runtime.version().feature() != 17 || error.javaClass != SocketException::class.java ||
                error.message != "Broken pipe") return false
            val frames = error.stackTrace.map { it.className to it.methodName }
            val prefix = listOf(
                "sun.nio.ch.NioSocketImpl" to "implWrite",
                "sun.nio.ch.NioSocketImpl" to "write",
                "sun.nio.ch.NioSocketImpl\$2" to "write",
                "java.net.Socket\$SocketOutputStream" to "write",
                "sun.security.ssl.SSLSocketOutputRecord" to "flush",
                "sun.security.ssl.HandshakeOutStream" to "flush",
                "sun.security.ssl.Finished\$T13FinishedProducer" to "onProduceFinished",
                "sun.security.ssl.Finished\$T13FinishedProducer" to "produce",
            )
            if (frames.take(prefix.size) != prefix) return false
            val caller = listOf(
                "sun.security.ssl.SSLSocketImpl" to "startHandshake",
                "sun.security.ssl.SSLSocketImpl" to "startHandshake",
                "com.mohamedrejeb.calf.ui.web.OwnedDesktopTlsFixture\$Endpoint" to "respond",
            )
            return frames.windowed(caller.size).any { it == caller }
        }
        private fun quarantineFinishedWrite(error: Throwable) {
            synchronized(rejectionLock) {
                if (pendingFinishedWrites.size >= 16) {
                    failure.compareAndSet(null, RecordedFailure(FailurePhase.Handshake, error))
                } else {
                    // Keep every bounded observation; neither adding it nor a prior observation is the native witness.
                    pendingFinishedWrites.add(error)
                }
            }
        }
        private fun closeOwned(socket: SSLSocket) {
            try { socket.close(); check(socket.isClosed); sockets.remove(socket) }
            catch (error: Throwable) {
                // A close/readback error is fatal even during teardown or after a confirmed native rejection.
                failure.compareAndSet(null, RecordedFailure(FailurePhase.SocketClose, error)); throw error
            }
        }
        // A failed close/readback must not skip any independently owned socket.
        private fun closeOwnedSockets() = runWebViewCleanup(stages = sockets.toList().map { socket ->
            { closeOwned(socket) }
        }.toTypedArray())
        private fun accept() {
            while (!closing.get()) {
                var socket: SSLSocket? = null
                try {
                    val owned = (listener.accept() as SSLSocket).also { socket = it; sockets.add(it) }
                    check(connections.incrementAndGet() <= 16) { "Owned TLS connection budget exhausted" }
                    owned.soTimeout = 8_000
                    workers.execute { respond(owned) }
                    socket = null // Ownership transferred to the queued/responding worker.
                } catch (error: Throwable) {
                    record(error, FailurePhase.Accept)
                    socket?.let { runCatching { closeOwned(it) } }
                    if (closing.get()) return
                }
            }
        }
        private fun respond(socket: SSLSocket) {
            var handshaken = false
            var phase = FailurePhase.Handshake
            try {
                handshakeAttempts.incrementAndGet()
                socket.startHandshake() // Default protocols/ciphers and real JDK TLS.
                handshaken = true
                handshakeSuccesses.incrementAndGet()
                phase = FailurePhase.RequestHeaders
                val bytes = ByteArray(16_384)
                var size = 0
                val input = socket.inputStream
                while (true) {
                    check(size < bytes.size) { "Owned TLS HTTP headers exceeded the finite bound" }
                    val next = input.read()
                    if (next == -1) throw EOFException("Owned TLS request ended before headers")
                    bytes[size++] = next.toByte()
                    if (size >= 4 && bytes[size - 4] == 13.toByte() && bytes[size - 3] == 10.toByte() &&
                        bytes[size - 2] == 13.toByte() && bytes[size - 1] == 10.toByte()) break
                }
                val line = String(bytes, 0, size, StandardCharsets.US_ASCII).substringBefore("\r\n").split(' ')
                check(line.size == 3 && line[0] == "GET" && line[2] in setOf("HTTP/1.1", "HTTP/1.0"))
                val stage = DesktopTlsStage.entries.singleOrNull { it.trusted == trusted && line[1] == path(it) }
                val body = if (stage != null) {
                    requests.getValue(stage).incrementAndGet()
                    val left = stage.leftRgb.toString(16).padStart(6, '0')
                    val right = stage.rightRgb.toString(16).padStart(6, '0')
                    """<!doctype html><html><head><title>nativecmpkit-tls-$nonce-${stage.name}</title>
                        <style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000}
                        .patch{position:absolute;top:0;bottom:0;width:50%}#left{left:0;background:#$left}#right{left:50%;background:#$right}</style>
                        </head><body><div id="left" class="patch"></div><div id="right" class="patch"></div></body></html>""".trimIndent()
                } else "" // Incidental favicon does not count as an authored stage.
                val data = body.toByteArray(StandardCharsets.UTF_8)
                val status = if (stage == null) "404 Not Found" else "200 OK"
                val headers = "HTTP/1.1 $status\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: ${data.size}\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n"
                phase = FailurePhase.ResponseWrite
                socket.outputStream.apply { write(headers.toByteArray(StandardCharsets.US_ASCII)); write(data); flush() }
                if (stage != null) responses.getValue(stage).incrementAndGet()
            } catch (error: Throwable) {
                // Keep the original negative pre-handshake SSLException/EOF boundary.
                // The one observed Finished-write abort remains pending until ALL original
                // native SSL/error and zero-HTTP assertions confirm this same owned endpoint.
                // Unknown shapes retain the original fatal branch; no socket-wide suppression.
                if (observedFinishedWriteAbort(error, phase, handshaken)) {
                    quarantineFinishedWrite(error)
                } else if (trusted || handshaken || (error !is SSLException && error !is EOFException)) {
                    record(error, phase)
                }
            } finally { runCatching { closeOwned(socket) } }
        }
        override fun close() {
            closing.set(true) // Close is EXEMPT from the work/connection budget.
            runWebViewCleanup(null,
                { listener.close(); check(listener.isClosed) },
                { closeOwnedSockets() },
                { workers.shutdownNow() },
                { acceptor.join(10_000); check(!acceptor.isAlive) { "Owned TLS acceptor did not terminate" } },
                { check(workers.awaitTermination(10, TimeUnit.SECONDS)) { "Owned TLS workers did not terminate" } },
                { closeOwnedSockets() },
                { check(sockets.isEmpty()) },
                { assertHealthy() },
            )
        }
        companion object {
            fun create(context: SSLContext, trusted: Boolean, nonce: String): Endpoint {
                val listener = context.serverSocketFactory.createServerSocket(0, 8, InetAddress.getByName("127.0.0.1")) as SSLServerSocket
                var workers: ThreadPoolExecutor? = null
                try {
                    val pool = ThreadPoolExecutor(2, 2, 0, TimeUnit.MILLISECONDS, ArrayBlockingQueue<Runnable>(16),
                        { runnable -> Thread(runnable, "nativecmpkit-owned-tls-response").apply { isDaemon = true } },
                        ThreadPoolExecutor.AbortPolicy()).also { workers = it }
                    return Endpoint(listener, pool, trusted, nonce).also { it.acceptor.start() }
                } catch (failure: Throwable) {
                    runWebViewCleanup(failure,
                        { listener.close(); check(listener.isClosed) },
                        { workers?.shutdownNow() },
                        { workers?.let { check(it.awaitTermination(10, TimeUnit.SECONDS)) } })
                    throw failure
                }
            }
        }
    }
}
