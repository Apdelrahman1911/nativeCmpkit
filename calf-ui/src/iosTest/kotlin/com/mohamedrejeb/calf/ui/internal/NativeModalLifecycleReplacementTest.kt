// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    kotlin.experimental.ExperimentalNativeApi::class,
    kotlin.native.runtime.NativeRuntimeApi::class)

package com.mohamedrejeb.calf.ui.internal

import androidx.compose.material3.SheetValue
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.ui.sheet.AdaptiveBottomSheet
import com.mohamedrejeb.calf.ui.sheet.AdaptiveSheetState
import com.mohamedrejeb.calf.ui.sheet.BottomSheetManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlin.native.ref.WeakReference
import kotlin.native.runtime.GC
import platform.UIKit.UIViewController
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Missing lifecycle criteria only; the accepted sheet and queued-modal methods are not selected. */
class NativeModalLifecycleReplacementTest {
    @Test fun publicCompositionDisposalDuringNativeHideReleasesContentAndCanReopen() = runApplicationUiTest {
        var parent: UIViewController? = null
        val state = newState()
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        var dismissals = 0
        val content = installOwnedSheet(state, { dismissals++ }) { parent = it }
        try {
            waitForNative { state.currentValue == SheetValue.PartiallyExpanded && parent?.presentedViewController?.view?.window != null }
            lateinit var hiding: Job
            var dismissedController: UIViewController? = null
            runOnIdle {
                dismissedController = assertNotNull(parent?.presentedViewController)
                hiding = scope.launch { state.hide() }
                assertFalse(hiding.isCompleted, "Dispose during this admitted native animation, not after it")
                assertTrue(assertNotNull(dismissedController).isBeingDismissed())
                setContent { }
            }
            waitForIdle()
            waitForNative { hiding.isCancelled && parent?.presentedViewController == null && dismissedController?.view?.window == null }
            runOnIdle {
                assertNull(state.iosSheetManager)
                assertEquals(SheetValue.Hidden, state.currentValue)
                assertEquals(SheetValue.Hidden, state.targetValue)
                assertEquals(0, dismissals)
                dismissedController = null // Do not keep the retired composition alive through this test.
            }
            assertCollected(content)
            installOwnedSheet(state, { dismissals++ }) { parent = it }
            waitForNative { state.currentValue == SheetValue.PartiallyExpanded && parent?.presentedViewController?.view?.window != null }
            runOnIdle { assertEquals(0, dismissals); setContent { } }
            waitForIdle()
            waitForNative { parent?.presentedViewController == null && state.iosSheetManager == null }
        } finally { runOnIdle { setContent { }; scope.cancel() } }
    }

    @Test fun hoistedStateReattachesToANewRealPresenterAndStaleOwnersCannotDetachItsReplacement() {
        val held = newState()
        var firstParent: UIViewController? = null
        var firstManager: BottomSheetManager? = null
        var dismissals = 0
        runApplicationUiTest {
            installOwnedSheet(held, { dismissals++ }) { firstParent = it }
            waitForNative { held.currentValue == SheetValue.PartiallyExpanded && firstParent?.presentedViewController?.view?.window != null }
            runOnIdle { firstManager = assertNotNull(held.iosSheetManager); setContent { } }
            waitForIdle()
            waitForNative { firstParent?.presentedViewController == null && held.iosSheetManager == null }
        }
        // A second genuine ComposeUIViewController/window attachment replaces the first
        // presenter; no fake controller local or foreign application root is installed.
        runApplicationUiTest {
            var current by mutableStateOf(held)
            var secondParent: UIViewController? = null
            val replacement = newState()
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            try {
                setContent {
                    secondParent = LocalUIViewController.current
                    AdaptiveBottomSheet(onDismissRequest = { dismissals++ }, adaptiveSheetState = current) { }
                }
                waitForNative { held.currentValue == SheetValue.PartiallyExpanded && secondParent?.presentedViewController?.view?.window != null }
                var priorController: UIViewController? = null
                runOnIdle {
                    assertFalse(sameNativeObject(firstParent, secondParent))
                    assertNull(assertNotNull(firstParent).view.window)
                    val newManager = assertNotNull(held.iosSheetManager)
                    assertTrue(newManager !== firstManager)
                    held.detach(assertNotNull(firstManager))
                    assertSame(newManager, held.iosSheetManager, "Retired owner must not detach the new one")
                    assertEquals(SheetValue.PartiallyExpanded, held.currentValue)
                    priorController = assertNotNull(secondParent?.presentedViewController)
                    current = replacement
                }
                waitForIdle()
                waitForNative { held.iosSheetManager == null && held.currentValue == SheetValue.Hidden &&
                    replacement.currentValue == SheetValue.PartiallyExpanded && priorController?.view?.window == null &&
                    secondParent?.presentedViewController?.view?.window != null }
                lateinit var obsoleteCalls: Job
                runOnIdle {
                    assertFalse(sameNativeObject(priorController, secondParent?.presentedViewController))
                    val replacementManager = assertNotNull(replacement.iosSheetManager)
                    held.detach(assertNotNull(firstManager))
                    assertSame(replacementManager, replacement.iosSheetManager)
                    obsoleteCalls = scope.launch { held.show(); held.hide() }
                }
                waitForNative { obsoleteCalls.isCompleted }
                runOnIdle {
                    assertFalse(obsoleteCalls.isCancelled)
                    assertEquals(SheetValue.Hidden, held.currentValue)
                    assertEquals(SheetValue.PartiallyExpanded, replacement.currentValue)
                    assertNotNull(secondParent?.presentedViewController?.view?.window)
                    assertEquals(0, dismissals)
                    priorController = null
                    setContent { }
                }
                waitForIdle()
                waitForNative { secondParent?.presentedViewController == null && replacement.iosSheetManager == null }
            } finally { runOnIdle { setContent { }; scope.cancel() } }
        }
    }

    @Test fun repeatedDisposalDuringBothNativeAnimationsLeavesNoWaiterOrCapturedContent() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        var dismissals = 0
        try {
            repeat(4) { cycle ->
                lateinit var state: AdaptiveSheetState
                lateinit var manager: BottomSheetManager
                lateinit var showing: Job
                val content = runOnIdle {
                    val owner = ContentOwner()
                    state = newState()
                    manager = BottomSheetManager(parent, false, Color.White, { dismissals++ }, state::permits,
                        { value, target -> state.iosCurrentValue = value; state.iosTargetValue = target }, { owner.touch() })
                    state.iosSheetManager = manager
                    showing = scope.launch { state.show() }
                    assertFalse(showing.isCompleted)
                    if (cycle % 2 == 0) {
                        assertTrue(assertNotNull(parent.presentedViewController).isBeingPresented())
                        state.detach(manager)
                        manager.dispose()
                    }
                    WeakReference(owner)
                }
                var hiding: Job? = null
                if (cycle % 2 != 0) {
                    waitForNative { showing.isCompleted && parent.presentedViewController?.view?.window != null }
                    runOnIdle {
                        assertFalse(showing.isCancelled)
                        hiding = scope.launch { state.hide() }
                        assertFalse(assertNotNull(hiding).isCompleted)
                        assertTrue(assertNotNull(parent.presentedViewController).isBeingDismissed())
                        state.detach(manager)
                        manager.dispose()
                    }
                }
                waitForNative { parent.presentedViewController == null &&
                    (if (cycle % 2 == 0) showing.isCancelled else hiding?.isCancelled == true) }
                runOnIdle {
                    assertNull(state.iosSheetManager)
                    assertEquals(SheetValue.Hidden, state.currentValue)
                    assertEquals(SheetValue.Hidden, state.targetValue)
                    assertEquals(0, dismissals)
                    manager.dispose() // Repeated cleanup must remain idempotent.
                }
                assertCollected(content)
            }
        } finally { runOnIdle { scope.cancel() } }
    }

    private class ContentOwner {
        private var calls = 0
        fun touch() { calls++ }
    }

    private fun newState() = AdaptiveSheetState(false, { true }, SheetValue.Hidden, false, { 56f }, { 125f })

    private fun NativeApplicationUiTest.installOwnedSheet(
        state: AdaptiveSheetState,
        onDismiss: () -> Unit,
        onParent: (UIViewController) -> Unit,
    ): WeakReference<ContentOwner> {
        val owner = ContentOwner()
        setContent {
            onParent(LocalUIViewController.current)
            AdaptiveBottomSheet(onDismissRequest = onDismiss, adaptiveSheetState = state) { owner.touch() }
        }
        return WeakReference(owner)
    }

    private fun NativeApplicationUiTest.assertCollected(owner: WeakReference<ContentOwner>) {
        repeat(3) { runOnIdle { GC.collect() } }
        runOnIdle { assertNull(owner.get(), "Retired native sheet/composition must release its captured owner") }
    }
}
