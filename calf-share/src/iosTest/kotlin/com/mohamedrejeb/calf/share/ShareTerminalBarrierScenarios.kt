// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, com.mohamedrejeb.calf.core.InternalCalfApi::class)

package com.mohamedrejeb.calf.share

import com.mohamedrejeb.calf.share.internal.onApplicationMain
import platform.UIKit.UIActivityViewController
import kotlin.test.*

/**
 * Four NEW controlled production-Request regression scenarios inside the failed remembered
 * public method. Actual UIActivityViewController objects, but empty scopes and deliberate
 * callbacks, not OS presentation/dismissal or recipient success. The enclosing public method
 * independently requires genuine UIKit presentation/dismissal/Compose/Worker barriers.
 */
internal fun verifyControlledIosShareTerminalBarriers() = onApplicationMain {
    terminalDuringPresentationWaitsForBothCompletionsAndDeduplicates()
    ownerDisposalSuppressesAPendingTerminalResult()
    neverPresentedTerminalReleasesBeforeApplicationCode()
    throwingTerminalCallbackCannotRepeatReleaseOrDelivery()
}

private fun terminalDuringPresentationWaitsForBothCompletionsAndDeduplicates() {
    val controller = UIActivityViewController(listOf("Controlled terminal transition"), null)
    val request = IosShareOwner.Request(controller, emptyList())
    val events = mutableListOf<String>()
    var dismissals = 0
    var dismissal: (() -> Unit)? = null
    request.onReleased = { events += "released" }
    request.beginPresentation { dismissals++; dismissal = it }
    controller.completionWithItemsHandler = { _, _, _, _ -> error("First terminal input must detach the block") }
    request.complete {
        assertEquals(IosShareRequestPhase.Released, request.phase)
        assertNull(controller.completionWithItemsHandler)
        assertTrue(request.dismissalCompletionObserved)
        assertEquals(listOf("released"), events)
        events += "first"
    }
    request.complete { error("A duplicate cannot replace the first terminal result") }
    assertEquals(IosShareRequestPhase.Presenting, request.phase)
    assertFalse(request.presentationCompletionObserved)
    assertFalse(request.dismissalCompletionObserved)
    assertNull(controller.completionWithItemsHandler)
    assertEquals(0, dismissals)
    assertTrue(events.isEmpty())
    request.presentationCompleted()
    assertEquals(IosShareRequestPhase.Dismissing, request.phase)
    assertTrue(request.presentationCompletionObserved)
    assertFalse(request.dismissalCompletionObserved)
    assertEquals(1, dismissals)
    assertTrue(events.isEmpty())
    val complete = assertNotNull(dismissal)
    complete(); complete()
    request.complete { error("Released generations cannot deliver again") }
    request.dispose()
    assertEquals(1, dismissals)
    assertEquals(listOf("released", "first"), events)
}

private fun ownerDisposalSuppressesAPendingTerminalResult() {
    val controller = UIActivityViewController(listOf("Controlled terminal disposal"), null)
    val request = IosShareOwner.Request(controller, emptyList())
    var releases = 0
    var deliveries = 0
    var dismissals = 0
    var dismissal: (() -> Unit)? = null
    request.onReleased = { releases++ }
    request.beginPresentation { dismissals++; dismissal = it }
    request.presentationCompleted()
    request.complete { deliveries++ }
    assertEquals(IosShareRequestPhase.Dismissing, request.phase)
    assertEquals(1, dismissals)
    assertEquals(0, releases)
    request.dispose(); request.dispose()
    request.complete { error("Disposed pending results cannot be reinstated") }
    assertEquals(0, releases)
    assertEquals(0, deliveries)
    val complete = assertNotNull(dismissal)
    complete(); complete()
    assertEquals(IosShareRequestPhase.Released, request.phase)
    assertTrue(request.dismissalCompletionObserved)
    assertEquals(1, dismissals)
    assertEquals(1, releases)
    assertEquals(0, deliveries)
}

private fun neverPresentedTerminalReleasesBeforeApplicationCode() {
    val controller = UIActivityViewController(listOf("Controlled never-presented terminal"), null)
    val request = IosShareOwner.Request(controller, emptyList())
    val events = mutableListOf<String>()
    request.onReleased = { events += "released" }
    request.complete {
        assertEquals(IosShareRequestPhase.Released, request.phase)
        assertEquals(listOf("released"), events)
        assertFalse(request.presentationCompletionObserved)
        assertFalse(request.dismissalCompletionObserved)
        events += "result"
        request.complete { error("Application reentry cannot redeliver this old request") }
    }
    request.complete { error("No second terminal delivery") }
    request.dispose()
    assertEquals(listOf("released", "result"), events)
}

private fun throwingTerminalCallbackCannotRepeatReleaseOrDelivery() {
    val controller = UIActivityViewController(listOf("Controlled throwing terminal"), null)
    val request = IosShareOwner.Request(controller, emptyList())
    val failure = IllegalStateException("Intentional caught terminal callback failure")
    var releases = 0
    var deliveries = 0
    var dismissal: (() -> Unit)? = null
    request.onReleased = { releases++ }
    request.beginPresentation { dismissal = it }
    request.presentationCompleted()
    request.complete {
        deliveries++
        assertEquals(1, releases)
        assertEquals(IosShareRequestPhase.Released, request.phase)
        assertTrue(request.dismissalCompletionObserved)
        assertNull(controller.completionWithItemsHandler)
        throw failure
    }
    val complete = assertNotNull(dismissal)
    assertSame(failure, assertFailsWith<IllegalStateException> { complete() })
    complete()
    request.complete { error("Throwing result cannot retry delivery") }
    request.dispose()
    assertEquals(1, releases)
    assertEquals(1, deliveries)
}
