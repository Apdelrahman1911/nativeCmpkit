@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class,
    androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.sheet

import androidx.compose.material3.SheetValue
import androidx.compose.ui.graphics.Color
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.ui.internal.runNativeUiTest
import com.mohamedrejeb.calf.ui.internal.waitForNative
import kotlinx.coroutines.*
import platform.UIKit.UIViewController
import kotlin.test.*

class NativeSheetLifecycleTest {
    private fun newState(skipPartial: Boolean = false, skipHidden: Boolean = false,
        initial: SheetValue = SheetValue.Hidden, confirm: (SheetValue) -> Boolean = { true }) =
        AdaptiveSheetState(skipPartial, confirm, initial, skipHidden, { 56f }, { 125f })

    private fun newManager(parent: UIViewController, state: AdaptiveSheetState, onDismiss: () -> Unit) =
        BottomSheetManager(parent, false, Color.White, onDismiss, state::permits,
            { current, target -> state.iosCurrentValue = current; state.iosTargetValue = target }, {})
            .also { state.iosSheetManager = it }

    @Test fun transitionPolicyIncludesSkipFlagsAndCurrentConfirmation() = runNativeUiTest {
        var calls = 0
        val state = newState(skipPartial = true, skipHidden = true, initial = SheetValue.Expanded) { calls++; true }
        assertFalse(state.permits(SheetValue.PartiallyExpanded))
        assertFalse(state.permits(SheetValue.Hidden))
        assertEquals(0, calls)
        assertTrue(state.permits(SheetValue.Expanded))
        assertEquals(1, calls)
        val veto = newState(confirm = { false })
        assertFalse(veto.permits(SheetValue.PartiallyExpanded))
    }

    @Test fun cancellingAShowWaiterDoesNotReuseItsCompletionForHide() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val state = newState()
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        lateinit var manager: BottomSheetManager
        lateinit var showing: Job
        lateinit var hiding: Job
        runOnIdle {
            manager = newManager(parent, state, {})
            showing = scope.launch { state.show() }
            showing.cancel()
        }
        try {
            waitForNative { state.currentValue == SheetValue.PartiallyExpanded }
            runOnIdle {
                hiding = scope.launch { state.hide() }
                assertFalse(hiding.isCompleted)
                assertEquals(SheetValue.Hidden, state.targetValue)
            }
            waitForNative { hiding.isCompleted && parent.presentedViewController == null }
            assertEquals(SheetValue.Hidden, state.currentValue)
            assertTrue(showing.isCancelled)
        } finally { runOnIdle { state.detach(manager); manager.dispose(); scope.cancel() } }
    }

    @Test fun disposalDuringShowDetachesOwnerWithoutUserDismissal() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val state = newState()
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        var dismissals = 0
        lateinit var manager: BottomSheetManager
        runOnIdle {
            manager = newManager(parent, state) { dismissals++ }
            scope.launch { state.show() }
            scope.launch { state.hide() }
            state.detach(manager)
            manager.dispose()
        }
        try {
            waitForNative { parent.presentedViewController == null }
            assertNull(state.iosSheetManager)
            assertEquals(SheetValue.Hidden, state.currentValue)
            assertEquals(0, dismissals)
        } finally { runOnIdle { manager.dispose(); scope.cancel() } }
    }
}
