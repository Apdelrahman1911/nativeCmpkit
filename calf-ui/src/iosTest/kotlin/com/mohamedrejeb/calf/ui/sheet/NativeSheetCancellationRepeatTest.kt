// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.mohamedrejeb.calf.ui.sheet

import androidx.compose.material3.SheetValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import platform.UIKit.UIViewController
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** UI-018 C2: repeat the SAME cancelled operation, not merely its opposite. */
class NativeSheetCancellationRepeatTest {
    @Test fun cancelledShowRepeatsWithANewNativeAnimationAndItsOwnCompletion() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owner = runOnIdle { Owner(parent) }
        try {
            lateinit var cancelled: Job
            runOnIdle {
                cancelled = owner.scope.launch { owner.state.show() }
                assertFalse(cancelled.isCompleted)
                assertEquals(SheetValue.Hidden, owner.state.currentValue)
                assertEquals(SheetValue.PartiallyExpanded, owner.state.targetValue)
                assertTrue(parent.presentedViewController?.isBeingPresented() == true)
                cancelled.cancel()
            }
            waitForNative { cancelled.isCompleted && cancelled.isCancelled && owner.isShown() }
            val originalController = runOnIdle {
                val noOp = owner.scope.launch { owner.state.show() }
                assertTrue(noOp.isCompleted)
                assertFalse(noOp.isCancelled)
                parent.presentedViewController!!
            }
            lateinit var reset: Job
            runOnIdle { reset = owner.scope.launch { owner.state.hide() } }
            waitForNative { reset.isCompleted && owner.isHidden() }
            lateinit var repeated: Job
            runOnIdle {
                assertFalse(reset.isCancelled)
                repeated = owner.scope.launch { owner.state.show() }
                // This is a new actual presentation after the first animation
                // completed. A stale already-completed deferred would return now.
                assertFalse(repeated.isCompleted)
                assertEquals(SheetValue.Hidden, owner.state.currentValue)
                assertEquals(SheetValue.PartiallyExpanded, owner.state.targetValue)
                assertTrue(parent.presentedViewController?.isBeingPresented() == true)
                assertTrue(sameNativeObject(originalController, parent.presentedViewController))
            }
            waitForNative { repeated.isCompleted && owner.isShown() }
            runOnIdle {
                assertFalse(repeated.isCancelled)
                assertTrue(cancelled.isCancelled)
                assertEquals(0, owner.dismissals)
            }
        } finally {
            runOnIdle { owner.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun cancelledHideRepeatsWithANewNativeAnimationAndItsOwnCompletion() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owner = runOnIdle { Owner(parent) }
        try {
            lateinit var initial: Job
            runOnIdle { initial = owner.scope.launch { owner.state.show() } }
            waitForNative { initial.isCompleted && owner.isShown() }
            lateinit var cancelled: Job
            val originalController = runOnIdle {
                assertFalse(initial.isCancelled)
                val controller = parent.presentedViewController!!
                cancelled = owner.scope.launch { owner.state.hide() }
                assertFalse(cancelled.isCompleted)
                assertEquals(SheetValue.PartiallyExpanded, owner.state.currentValue)
                assertEquals(SheetValue.Hidden, owner.state.targetValue)
                assertTrue(controller.isBeingDismissed())
                cancelled.cancel()
                controller
            }
            waitForNative { cancelled.isCompleted && cancelled.isCancelled && owner.isHidden() }
            runOnIdle {
                val noOp = owner.scope.launch { owner.state.hide() }
                assertTrue(noOp.isCompleted)
                assertFalse(noOp.isCancelled)
            }
            lateinit var reset: Job
            runOnIdle { reset = owner.scope.launch { owner.state.show() } }
            waitForNative { reset.isCompleted && owner.isShown() }
            lateinit var repeated: Job
            runOnIdle {
                assertFalse(reset.isCancelled)
                assertTrue(sameNativeObject(originalController, parent.presentedViewController))
                repeated = owner.scope.launch { owner.state.hide() }
                // A completed first hide must not acknowledge a second native
                // dismissal before its own UIKit completion callback.
                assertFalse(repeated.isCompleted)
                assertEquals(SheetValue.PartiallyExpanded, owner.state.currentValue)
                assertEquals(SheetValue.Hidden, owner.state.targetValue)
                assertTrue(originalController.isBeingDismissed())
            }
            waitForNative { repeated.isCompleted && owner.isHidden() }
            runOnIdle {
                assertFalse(repeated.isCancelled)
                assertTrue(cancelled.isCancelled)
                assertEquals(0, owner.dismissals)
            }
        } finally {
            runOnIdle { owner.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    private class Owner(val parent: UIViewController) {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        val state = AdaptiveSheetState(false, { true }, SheetValue.Hidden, false, { 56f }, { 125f })
        var dismissals = 0
        val manager = BottomSheetManager(parent, false, Color.White, { dismissals++ }, state::permits,
            { current, target -> state.iosCurrentValue = current; state.iosTargetValue = target }, {})
            .also { state.iosSheetManager = it }

        fun isShown(): Boolean = state.currentValue == SheetValue.PartiallyExpanded &&
            state.targetValue == SheetValue.PartiallyExpanded && parent.presentedViewController?.let {
                it.view.window != null && !it.isBeingPresented() && !it.isBeingDismissed()
            } == true

        fun isHidden(): Boolean = state.currentValue == SheetValue.Hidden &&
            state.targetValue == SheetValue.Hidden && parent.presentedViewController == null

        fun dispose() {
            state.detach(manager)
            manager.dispose()
            scope.cancel()
            assertNull(state.iosSheetManager)
            assertEquals(SheetValue.Hidden, state.currentValue)
            assertEquals(0, dismissals)
        }
    }
}
