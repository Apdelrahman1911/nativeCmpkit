// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import java.net.SocketException
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Actual Kotlin classifier regressions; synthetic stacks, not native TLS executions. */
class DesktopTlsFinishedWriteClassifierTest {
    private val abort = "An established connection was aborted by the software in your host machine"
    private val prefix = listOf(
        "sun.nio.ch.NioSocketImpl" to "implWrite",
        "sun.nio.ch.NioSocketImpl" to "write",
        "sun.nio.ch.NioSocketImpl\$2" to "write",
        "java.net.Socket\$SocketOutputStream" to "write",
        "sun.security.ssl.SSLSocketOutputRecord" to "flush",
        "sun.security.ssl.HandshakeOutStream" to "flush",
        "sun.security.ssl.Finished\$T13FinishedProducer" to "onProduceFinished",
        "sun.security.ssl.Finished\$T13FinishedProducer" to "produce",
    )
    private val caller = listOf(
        "sun.security.ssl.SSLSocketImpl" to "startHandshake",
        "sun.security.ssl.SSLSocketImpl" to "startHandshake",
        "com.mohamedrejeb.calf.ui.web.OwnedDesktopTlsFixture\$Endpoint" to "respond",
    )
    private val frames = prefix + listOf("sun.security.ssl.SSLHandshake" to "produce") + caller
    private fun error(message: String, stack: List<Pair<String, String>> = frames): SocketException =
        SocketException(message).apply {
            stackTrace = stack.map { (owner, method) -> StackTraceElement(owner, method, "synthetic.java", 1) }.toTypedArray()
        }

    @Test fun windowsAbortRequiresTheObservedHostJavaClassMessageAndFinishedFrames() {
        assertTrue(observedDesktopTlsFinishedWrite(error(abort), windows = true, javaFeature = 17))
        assertFalse(observedDesktopTlsFinishedWrite(error(abort), windows = false, javaFeature = 17))
        for (version in listOf(8, 11, 21, 25)) {
            assertFalse(observedDesktopTlsFinishedWrite(error(abort), windows = true, javaFeature = version))
        }
        for (message in listOf("Connection reset", "Software caused connection abort", abort.lowercase(), "$abort ")) {
            assertFalse(observedDesktopTlsFinishedWrite(error(message), windows = true, javaFeature = 17))
        }
        val wrongClass = object : SocketException(abort) {}.apply { stackTrace = error(abort).stackTrace }
        assertFalse(observedDesktopTlsFinishedWrite(wrongClass, windows = true, javaFeature = 17))
    }

    @Test fun originalBrokenPipeShapeRetainsItsExactJava17Classification() {
        for (windows in listOf(false, true)) {
            assertTrue(observedDesktopTlsFinishedWrite(error("Broken pipe"), windows, 17))
        }
        assertFalse(observedDesktopTlsFinishedWrite(error("broken pipe"), false, 17))
        assertFalse(observedDesktopTlsFinishedWrite(error("Broken pipe"), false, 21))
    }

    @Test fun missingReorderedAlteredOrUnownedStackFramesRemainFatalCandidates() {
        for (index in (prefix.indices.toList() + (prefix.size + 1 until frames.size).toList())) {
            val missing = frames.filterIndexed { i, _ -> i != index }
            val altered = frames.mapIndexed { i, frame -> if (i == index) "foreign.Owner" to frame.second else frame }
            assertFalse(observedDesktopTlsFinishedWrite(error(abort, missing), true, 17))
            assertFalse(observedDesktopTlsFinishedWrite(error(abort, altered), true, 17))
        }
        for (invalid in listOf(emptyList(), frames.reversed(), caller + prefix, prefix + caller.take(2))) {
            assertFalse(observedDesktopTlsFinishedWrite(error(abort, invalid), true, 17))
        }
    }
}
