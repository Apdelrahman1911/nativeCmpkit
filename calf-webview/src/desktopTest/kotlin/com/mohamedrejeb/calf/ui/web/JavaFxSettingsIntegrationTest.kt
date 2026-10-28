// NativeCmpKit regression: actual AWT producer and JavaFX/native settings consumer.
package com.mohamedrejeb.calf.ui.web

import javafx.application.Platform
import javafx.beans.value.ChangeListener
import kotlinx.coroutines.runBlocking
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlin.test.*

class JavaFxSettingsIntegrationTest {
    @Test fun equalAssignmentsAndNestedBatchesBoundActualNativeApplications() = runBlocking {
        JavaFxWebViewTest.Fixture().use { f ->
            val baseline = onFxThread { f.owner.settingsApplicationCount }
            val userAgents = mutableListOf<String?>()
            val javascriptValues = mutableListOf<Boolean>()
            val userAgentListener = ChangeListener<String> { _, _, value -> userAgents += value }
            val javascriptListener = ChangeListener<Boolean> { _, _, value -> javascriptValues += value }
            onFxThread {
                f.state.webView!!.engine.userAgentProperty().addListener(userAgentListener)
                f.state.webView!!.engine.javaScriptEnabledProperty().addListener(javascriptListener)
            }
            try {
                SwingUtilities.invokeAndWait {
                    repeat(1000) {
                        f.state.settings.javaScriptEnabled = false
                        f.state.settings.desktopSettings.customUserAgent = null
                        f.state.settings.androidSettings.textZoom = 100
                    }
                }
                assertEquals(baseline, onFxThread { f.owner.settingsApplicationCount },
                    "Equal setters must not invoke native settings again")
                SwingUtilities.invokeAndWait {
                    f.state.settings.batch {
                        javaScriptEnabled = true
                        desktopSettings.customUserAgent = "NativeCmpKit-intermediate"
                        batch {
                            androidSettings.textZoom = 125
                            desktopSettings.customUserAgent = "NativeCmpKit-one-complete-batch"
                        }
                    }
                }
                onFxThread {
                    assertEquals(baseline + 1, f.owner.settingsApplicationCount,
                        "The whole nested batch must execute only one actual native application")
                    assertEquals(listOf<String?>("NativeCmpKit-one-complete-batch"), userAgents)
                    assertEquals(listOf(true), javascriptValues)
                    assertEquals(true to "NativeCmpKit-one-complete-batch", f.state.webView!!.engine.let {
                        it.isJavaScriptEnabled to it.userAgent
                    })
                }
            } finally {
                onFxThread {
                    f.state.webView!!.engine.userAgentProperty().removeListener(userAgentListener)
                    f.state.webView!!.engine.javaScriptEnabledProperty().removeListener(javascriptListener)
                }
            }
        }
    }

    @Test fun aThousandCompletedUiNotificationsCoalesceOnTheActualBlockedFxQueue() = runBlocking {
        JavaFxWebViewTest.Fixture().use { f ->
            val blocked = CountDownLatch(1)
            val release = CountDownLatch(1)
            val fxFailure = AtomicReference<Throwable?>()
            val baseline = onFxThread { f.owner.settingsApplicationCount }
            try {
                Platform.runLater {
                    blocked.countDown()
                    try { check(release.await(5, TimeUnit.SECONDS)) { "Owned FX storm gate timed out" } }
                    catch (error: Throwable) { fxFailure.set(error) }
                }
                assertTrue(blocked.await(5, TimeUnit.SECONDS))
                SwingUtilities.invokeAndWait {
                    repeat(1000) { index ->
                        f.state.settings.batch {
                            javaScriptEnabled = index % 2 == 0
                            desktopSettings.customUserAgent = "NativeCmpKit-complete-$index"
                        }
                    }
                }
            } finally { release.countDown() }
            onFxThread {
                fxFailure.get()?.let { throw AssertionError("Actual FX storm gate failed", it) }
                assertEquals(baseline + 1, f.owner.settingsApplicationCount,
                    "A blocked real FX queue must apply the latest completed snapshot once")
                assertEquals(false to "NativeCmpKit-complete-999", f.state.webView!!.engine.let {
                    it.isJavaScriptEnabled to it.userAgent
                })
            }
        }
    }

    @Test fun aPendingFxApplyCannotObserveAnIncompleteAwtSettingsBatch() = runBlocking {
        JavaFxWebViewTest.Fixture().use { f ->
            val fxBlocked = CountDownLatch(1)
            val releaseFx = CountDownLatch(1)
            val partialUiWrite = CountDownLatch(1)
            val finishUiBatch = CountDownLatch(1)
            val uiFinished = CountDownLatch(1)
            val uiFailure = AtomicReference<Throwable?>()
            val fxFailure = AtomicReference<Throwable?>()
            var uiStarted = false
            var observedPending: Pair<Boolean, String?>? = null
            try {
                SwingUtilities.invokeAndWait {
                    f.state.settings.batch {
                        javaScriptEnabled = true
                        desktopSettings.customUserAgent = "NativeCmpKit-stable-A"
                    }
                }
                assertEquals(true to "NativeCmpKit-stable-A", onFxThread {
                    f.state.webView!!.engine.let { it.isJavaScriptEnabled to it.userAgent }
                })
                Platform.runLater {
                    fxBlocked.countDown()
                    try { check(releaseFx.await(5, TimeUnit.SECONDS)) { "Owned FX gate timed out" } }
                    catch (error: Throwable) { fxFailure.set(error) }
                }
                assertTrue(fxBlocked.await(5, TimeUnit.SECONDS), "Actual FX queue must reach the owned gate")
                SwingUtilities.invokeAndWait {
                    f.state.settings.desktopSettings.customUserAgent = "NativeCmpKit-stable-A2"
                } // Queue an application of the COMPLETE A2 settings behind the real FX gate.
                uiStarted = true
                SwingUtilities.invokeLater {
                    try {
                        f.state.settings.batch {
                            javaScriptEnabled = false
                            partialUiWrite.countDown()
                            check(finishUiBatch.await(5, TimeUnit.SECONDS)) { "Owned UI batch gate timed out" }
                            desktopSettings.customUserAgent = "NativeCmpKit-complete-B"
                        }
                    } catch (error: Throwable) { uiFailure.set(error) }
                    finally { uiFinished.countDown() }
                }
                assertTrue(partialUiWrite.await(5, TimeUnit.SECONDS), "AWT must be paused INSIDE the new batch")
                releaseFx.countDown()
                observedPending = onFxThread {
                    assertTrue(Platform.isFxApplicationThread())
                    f.state.webView!!.engine.let { it.isJavaScriptEnabled to it.userAgent }
                }
            } finally {
                releaseFx.countDown()
                finishUiBatch.countDown()
                if (uiStarted) assertTrue(uiFinished.await(5, TimeUnit.SECONDS), "Owned AWT batch must finish")
            }
            fxFailure.get()?.let { throw AssertionError("Actual FX gate failed", it) }
            uiFailure.get()?.let { throw AssertionError("Actual AWT batch failed", it) }
            assertEquals(true to "NativeCmpKit-stable-A2", observedPending,
                "Queued native work must use the last complete notification, not half of a later UI batch")
            assertEquals(false to "NativeCmpKit-complete-B", onFxThread {
                f.state.webView!!.engine.let { it.isJavaScriptEnabled to it.userAgent }
            }, "Completing the batch must deliver the new coherent pair to the same real native owner")
        }
    }
}
