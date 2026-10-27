@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    kotlin.native.concurrent.ObsoleteWorkersApi::class,
    kotlin.experimental.ExperimentalNativeApi::class)

package com.mohamedrejeb.calf.ui.internal

import androidx.compose.material3.Text
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.uikit.LocalUIViewController
import kotlin.native.concurrent.Worker
import kotlin.native.internal.test.GeneratedSuites
import platform.Foundation.NSThread
import platform.UIKit.UIAlertAction
import platform.UIKit.UIAlertActionStyleDefault
import platform.UIKit.UIAlertController
import platform.UIKit.UIAlertControllerStyleAlert
import platform.UIKit.UIApplication
import platform.UIKit.UIApplicationState.UIApplicationStateActive
import platform.UIKit.UIViewController
import kotlin.test.*

/** Genuine application/Worker/window/composition leases, not a Skiko host claim. */
class NativeUiApplicationHostTest {
    @Test fun generatedBodyRunsOnOwnedWorkerWithActiveAttachedApplication() {
        assertFalse(NSThread.isMainThread)
        val worker = Worker.current.id
        assertTrue(GeneratedSuites.suites.isNotEmpty())
        onApplicationMain {
            assertTrue(NSThread.isMainThread)
            assertNotEquals(worker, Worker.current.id)
            assertEquals(UIApplicationStateActive, UIApplication.sharedApplication.applicationState)
            val window = requireOwnedApplicationWindow()
            assertTrue(window.isKeyWindow())
            assertFalse(window.hidden)
            assertSame(window, window.rootViewController?.view?.window)
        }
    }

    @Test fun repeatedRealComposeRootsRecomposeDisposeAndRestoreTheirOwner() {
        val prior = onApplicationMain { requireNotNull(requireOwnedApplicationWindow().rootViewController) }
        repeat(2) {
            val text = mutableStateOf("before")
            var committed = ""
            var disposals = 0
            lateinit var parent: UIViewController
            runApplicationUiTest {
                setContent {
                    parent = LocalUIViewController.current
                    DisposableEffect(Unit) { onDispose { assertTrue(NSThread.isMainThread); disposals++ } }
                    Text(text.value)
                    SideEffect { committed = text.value }
                }
                runOnIdle {
                    assertTrue(NSThread.isMainThread)
                    assertSame(parent, requireOwnedApplicationWindow().rootViewController)
                    assertSame(requireOwnedApplicationWindow(), parent.view.window)
                    assertEquals("before", committed)
                    text.value = "after"
                }
                waitForIdle()
                runOnIdle { assertEquals("after", committed); assertEquals(0, disposals) }
            }
            onApplicationMain {
                assertEquals(1, disposals)
                assertSame(prior, requireOwnedApplicationWindow().rootViewController)
                assertNull(parent.view.window)
                assertNull(prior.presentedViewController)
            }
        }
    }

    @Test fun failedAssertionPreservesCauseAndReleasesRealCompositionAndPresenter() {
        val prior = onApplicationMain { requireNotNull(requireOwnedApplicationWindow().rootViewController) }
        var disposals = 0
        lateinit var parent: UIViewController
        val failure = assertFailsWith<OwnedHostProbeFailure> {
            runApplicationUiTest {
                setContent {
                    parent = LocalUIViewController.current
                    DisposableEffect(Unit) { onDispose { disposals++ } }
                }
                runOnIdle {
                    val alert = UIAlertController.alertControllerWithTitle("Owned library fixture", null, UIAlertControllerStyleAlert)
                    alert.addAction(UIAlertAction.actionWithTitle("Close", UIAlertActionStyleDefault) {})
                    parent.presentViewController(alert, animated = false, completion = null)
                }
                waitForNative { parent.presentedViewController is UIAlertController }
                throw OwnedHostProbeFailure()
            }
        }
        assertTrue(failure.suppressedExceptions.isEmpty(), "Cleanup must not be silently hidden behind the primary assertion")
        onApplicationMain {
            assertEquals(1, disposals)
            assertNull(parent.presentedViewController)
            assertNull(parent.view.window)
            assertSame(prior, requireOwnedApplicationWindow().rootViewController)
        }
        // A failed fixture cannot poison the next native presentation lease.
        runApplicationUiTest { setContent { }; runOnIdle { requireOwnedApplicationWindow() } }
    }

    private class OwnedHostProbeFailure : IllegalStateException("Intentional caught host-cleanup fixture")
}
