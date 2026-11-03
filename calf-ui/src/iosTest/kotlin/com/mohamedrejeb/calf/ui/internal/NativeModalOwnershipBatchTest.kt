// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    com.mohamedrejeb.calf.core.InternalCalfApi::class,
    kotlin.experimental.ExperimentalNativeApi::class,
    kotlin.native.runtime.NativeRuntimeApi::class)

package com.mohamedrejeb.calf.ui.internal

import androidx.compose.material3.SheetValue
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.ui.dialog.AlertDialogManager
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosAction
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosActionStyle
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosProperties
import com.mohamedrejeb.calf.ui.sheet.AdaptiveSheetState
import com.mohamedrejeb.calf.ui.sheet.BottomSheetManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.IO
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlin.native.ref.WeakReference
import kotlin.native.runtime.GC
import platform.Foundation.NSThread
import platform.UIKit.UIAlertController
import platform.UIKit.UIAlertAction
import platform.UIKit.UIViewController
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** New shared-owner regressions only; old alert/sheet acceptance methods are not replayed. */
class NativeModalOwnershipBatchTest {
    @Test fun publicHideCancelsAQueuedSheetWithoutDismissingTheActualBlocker() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            runOnIdle { owners.block() }
            waitForNative { owners.blockerIsVisible() }
            lateinit var state: AdaptiveSheetState
            lateinit var showing: Job
            lateinit var hiding: Job
            runOnIdle {
                state = owners.sheet()
                showing = owners.scope.launch { state.show() }
                assertFalse(showing.isCompleted)
                assertEquals(SheetValue.Hidden, state.currentValue)
                assertEquals(SheetValue.PartiallyExpanded, state.targetValue)
                hiding = owners.scope.launch { state.hide() }
            }
            waitForNative { showing.isCancelled && hiding.isCompleted && owners.blockerIsVisible() }
            runOnIdle {
                assertFalse(hiding.isCancelled)
                assertEquals(SheetValue.Hidden, state.currentValue)
                assertEquals(SheetValue.Hidden, state.targetValue)
                owners.unblock()
            }
            waitForNative { parent.presentedViewController == null }
            lateinit var reopened: Job
            runOnIdle { reopened = owners.scope.launch { state.show() } }
            waitForNative { reopened.isCompleted && parent.presentedViewController?.view?.window != null }
            runOnIdle {
                assertFalse(reopened.isCancelled)
                assertEquals(SheetValue.PartiallyExpanded, state.currentValue)
            }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun opposingPublicIntentsDuringNativePresentationCompleteTheirOwnWaiters() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            lateinit var state: AdaptiveSheetState
            lateinit var showing: Job
            lateinit var hiding: Job
            runOnIdle {
                state = owners.sheet()
                showing = owners.scope.launch { state.show() }
                hiding = owners.scope.launch { state.hide() }
                assertFalse(hiding.isCompleted)
                assertEquals(SheetValue.Hidden, state.targetValue)
            }
            waitForNative { showing.isCompleted && hiding.isCompleted && parent.presentedViewController == null }
            runOnIdle {
                assertFalse(showing.isCancelled)
                assertFalse(hiding.isCancelled)
                assertEquals(SheetValue.Hidden, state.currentValue)
                assertEquals(SheetValue.Hidden, state.targetValue)
            }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun cancellingANativeHideWaiterCannotCompleteItsReopenedShowEarly() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            lateinit var state: AdaptiveSheetState
            lateinit var showing: Job
            runOnIdle { state = owners.sheet(); showing = owners.scope.launch { state.show() } }
            waitForNative { showing.isCompleted && parent.presentedViewController?.view?.window != null }
            lateinit var hiding: Job
            lateinit var reopened: Job
            runOnIdle {
                hiding = owners.scope.launch { state.hide() }
                assertFalse(hiding.isCompleted)
                hiding.cancel()
                reopened = owners.scope.launch { state.show() }
                assertFalse(reopened.isCompleted)
                assertEquals(SheetValue.PartiallyExpanded, state.targetValue)
            }
            waitForNative { hiding.isCancelled && reopened.isCompleted &&
                parent.presentedViewController?.view?.window != null }
            runOnIdle {
                assertFalse(reopened.isCancelled)
                assertEquals(SheetValue.PartiallyExpanded, state.currentValue)
            }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun alternatingPublicIntentsCancelOnlyTheUnstartedMiddleTransition() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            lateinit var state: AdaptiveSheetState
            lateinit var firstShow: Job
            lateinit var supersededHide: Job
            lateinit var finalShow: Job
            runOnIdle {
                state = owners.sheet()
                firstShow = owners.scope.launch { state.show() }
                supersededHide = owners.scope.launch { state.hide() }
                finalShow = owners.scope.launch { state.show() }
                assertFalse(firstShow.isCompleted)
                assertFalse(finalShow.isCompleted)
            }
            waitForNative { firstShow.isCompleted && supersededHide.isCancelled && finalShow.isCompleted &&
                parent.presentedViewController?.view?.window != null }
            runOnIdle {
                assertFalse(firstShow.isCancelled)
                assertFalse(finalShow.isCancelled)
                assertEquals(SheetValue.PartiallyExpanded, state.currentValue)
                assertEquals(SheetValue.PartiallyExpanded, state.targetValue)
            }
            lateinit var firstHide: Job
            lateinit var supersededShow: Job
            lateinit var finalHide: Job
            runOnIdle {
                firstHide = owners.scope.launch { state.hide() }
                supersededShow = owners.scope.launch { state.show() }
                finalHide = owners.scope.launch { state.hide() }
                assertFalse(firstHide.isCompleted)
                assertFalse(finalHide.isCompleted)
            }
            waitForNative { firstHide.isCompleted && supersededShow.isCancelled && finalHide.isCompleted &&
                parent.presentedViewController == null }
            runOnIdle {
                assertFalse(firstHide.isCancelled)
                assertFalse(finalHide.isCancelled)
                assertEquals(SheetValue.Hidden, state.currentValue)
                assertEquals(SheetValue.Hidden, state.targetValue)
            }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun hiddenVetoKeepsTheQueuedShowUntilTheCurrentPolicyAllowsCancellation() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            runOnIdle { owners.block() }
            waitForNative { owners.blockerIsVisible() }
            var allowHidden = false
            val confirmations = mutableListOf<SheetValue>()
            lateinit var state: AdaptiveSheetState
            lateinit var showing: Job
            lateinit var vetoed: Job
            runOnIdle {
                state = owners.sheet(confirm = { value -> confirmations += value; value != SheetValue.Hidden || allowHidden })
                showing = owners.scope.launch { state.show() }
                vetoed = owners.scope.launch { state.hide() }
            }
            waitForNative { vetoed.isCompleted }
            lateinit var cancelled: Job
            runOnIdle {
                assertFalse(vetoed.isCancelled)
                assertFalse(showing.isCompleted)
                assertTrue(owners.blockerIsVisible())
                assertEquals(SheetValue.PartiallyExpanded, state.targetValue)
                assertEquals(listOf(SheetValue.PartiallyExpanded, SheetValue.Hidden), confirmations)
                allowHidden = true
                cancelled = owners.scope.launch { state.hide() }
            }
            waitForNative { cancelled.isCompleted && showing.isCancelled }
            runOnIdle {
                assertFalse(cancelled.isCancelled)
                assertEquals(SheetValue.Hidden, state.targetValue)
                assertEquals(listOf(SheetValue.PartiallyExpanded, SheetValue.Hidden, SheetValue.Hidden), confirmations)
                assertTrue(owners.blockerIsVisible())
            }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun concurrentQueuedShowCallersAllCancelAndHiddenCallersAllComplete() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            runOnIdle { owners.block() }
            waitForNative { owners.blockerIsVisible() }
            lateinit var state: AdaptiveSheetState
            lateinit var shows: List<Job>
            lateinit var hides: List<Job>
            runOnIdle {
                state = owners.sheet()
                shows = List(3) { owners.scope.launch { state.show() } }
                assertTrue(shows.all { !it.isCompleted })
                hides = List(3) { owners.scope.launch { state.hide() } }
            }
            waitForNative { shows.all { it.isCancelled } && hides.all { it.isCompleted } }
            runOnIdle {
                assertTrue(hides.none { it.isCancelled })
                assertEquals(SheetValue.Hidden, state.currentValue)
                assertTrue(owners.blockerIsVisible())
                owners.unblock()
            }
            waitForNative { parent.presentedViewController == null }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun queuedDisposalReleasesCapturedContentWithoutRunningUserDismissal() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            runOnIdle { owners.block() }
            waitForNative { owners.blockerIsVisible() }
            lateinit var showing: Job
            var dismissals = 0
            val retained = runOnIdle {
                val contentOwner = ContentOwner()
                val weak = WeakReference(contentOwner)
                val state = owners.sheet(onDismiss = { dismissals++ }, content = { contentOwner.touch() })
                showing = owners.scope.launch { state.show() }
                owners.detach(state)
                weak
            }
            waitForNative { showing.isCancelled }
            repeat(3) { runOnIdle { GC.collect() } }
            runOnIdle {
                assertNull(retained.get(), "Disposed unadmitted content must not be retained by queue/controller callbacks")
                assertEquals(0, dismissals)
                assertTrue(owners.blockerIsVisible())
                owners.unblock()
            }
            waitForNative { parent.presentedViewController == null }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun publicDefaultAndIoOperationsMarshalBothPoliciesAndNativeChangesToMain() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            val policyThreads = mutableListOf<Boolean>()
            val state = runOnIdle { owners.sheet(confirm = { policyThreads += NSThread.isMainThread; true }) }
            val showing = owners.scope.launch(Dispatchers.Default) { state.show() }
            waitForNative { showing.isCompleted && parent.presentedViewController?.view?.window != null }
            val hiding = owners.scope.launch(Dispatchers.IO) { state.hide() }
            waitForNative { hiding.isCompleted && parent.presentedViewController == null }
            runOnIdle {
                assertFalse(showing.isCancelled)
                assertFalse(hiding.isCancelled)
                assertTrue(policyThreads.size >= 2 && policyThreads.all { it })
                assertEquals(SheetValue.Hidden, state.currentValue)
            }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    @Test fun queuedAlertDismissAndStructuralRebuildNeverPresentStaleControllers() = runApplicationUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        val owners = runOnIdle { Owners(parent) }
        try {
            runOnIdle { owners.block() }
            waitForNative { owners.blockerIsVisible() }
            var dismissals = 0
            lateinit var queued: AlertDialogManager
            runOnIdle {
                queued = owners.alert("Queued old", { dismissals++ })
                queued.showAlertDialog()
                queued.dismiss()
                queued.dismiss()
                assertEquals(1, dismissals)
                assertTrue(owners.blockerIsVisible())
                queued.showAlertDialog()
                queued.iosProperties = AlertDialogIosProperties(title = "Queued new", animated = false,
                    actions = listOf(AlertDialogIosAction("Current", AlertDialogIosActionStyle.Default, {})))
                queued.updateDialogProperties()
                assertEquals(1, dismissals)
                assertTrue(owners.blockerIsVisible())
                owners.unblock()
            }
            waitForNative { (parent.presentedViewController as? UIAlertController)?.title == "Queued new" }
            runOnIdle {
                val current = assertNotNull(parent.presentedViewController as? UIAlertController)
                assertNotNull(current.view.window)
                assertEquals(listOf("Current"), current.actions.filterIsInstance<UIAlertAction>().map { it.title })
                assertEquals(1, dismissals)
                queued.dispose()
            }
            waitForNative { parent.presentedViewController == null }
            runOnIdle { assertEquals(1, dismissals) }
        } finally {
            runOnIdle { owners.dispose() }
            waitForNative { parent.presentedViewController == null }
        }
    }

    private class ContentOwner {
        private var calls = 0
        fun touch() { calls++ }
    }

    private class Owners(val parent: UIViewController) {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        private val sheets = mutableListOf<Pair<AdaptiveSheetState, BottomSheetManager>>()
        private val alerts = mutableListOf<AlertDialogManager>()
        private var blocker: AlertDialogManager? = null

        fun alert(title: String, dismissed: () -> Unit = {}) = AlertDialogManager(parent, dismissed,
            AlertDialogIosProperties(title = title, animated = false), DialogProperties()).also { alerts += it }

        fun block() { blocker = alert("Actual modal blocker").also { it.showAlertDialog() } }

        fun blockerIsVisible() = (parent.presentedViewController as? UIAlertController)?.let {
            it.title == "Actual modal blocker" && it.view.window != null
        } == true

        fun unblock() { blocker?.dispose(); blocker = null }

        fun sheet(confirm: (SheetValue) -> Boolean = { true }, onDismiss: () -> Unit = {},
                  content: @Composable () -> Unit = {}): AdaptiveSheetState {
            val state = AdaptiveSheetState(false, confirm, SheetValue.Hidden, false, { 56f }, { 125f })
            val manager = BottomSheetManager(parent, false, Color.White, onDismiss, state::permits,
                { current, target -> state.iosCurrentValue = current; state.iosTargetValue = target }, content)
            state.iosSheetManager = manager
            sheets += state to manager
            return state
        }

        fun detach(state: AdaptiveSheetState) {
            val manager = sheets.single { it.first === state }.second
            state.detach(manager)
            manager.dispose()
        }

        fun dispose() {
            sheets.forEach { (state, manager) -> state.detach(manager); manager.dispose() }
            sheets.clear()
            alerts.forEach { it.dispose() }
            alerts.clear()
            blocker = null
            scope.cancel()
        }
    }
}
