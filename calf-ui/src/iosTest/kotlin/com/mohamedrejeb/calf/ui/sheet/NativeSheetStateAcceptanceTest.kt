// Modified for NativeCmpKit (2026-10-29): real presentation, policy/density and registry restoration acceptance.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.sheet

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.SheetValue
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.LocalSaveableStateRegistry
import androidx.compose.runtime.saveable.SaveableStateRegistry
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import kotlinx.coroutines.*
import platform.UIKit.*
import kotlin.test.*

class NativeSheetStateAcceptanceTest {
    @Test fun visibleRememberedSheetKeepsIdentityAndUsesTheNewPolicyAfterDensityChanges() = runApplicationUiTest {
        var density by mutableStateOf(Density(1f))
        var callsA = 0
        var callsB = 0
        var confirm by mutableStateOf<(SheetValue) -> Boolean>({ callsA++; true })
        lateinit var state: AdaptiveSheetState
        lateinit var parent: UIViewController
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        try {
            setContent {
                CompositionLocalProvider(LocalDensity provides density) {
                    parent = LocalUIViewController.current
                    state = rememberAdaptiveSheetState(confirmValueChange = confirm)
                    AdaptiveBottomSheet(onDismissRequest = {}, adaptiveSheetState = state) { Spacer(Modifier.height(100.dp)) }
                }
            }
            waitForIdle()
            waitForNative { state.currentValue == SheetValue.PartiallyExpanded && parent.presentedViewController?.view?.window != null }
            lateinit var initial: AdaptiveSheetState
            lateinit var controller: UIViewController
            var firstPolicyCalls = -1
            runOnIdle {
                initial = state
                controller = assertNotNull(parent.presentedViewController)
                firstPolicyCalls = callsA
                confirm = { callsB++; it != SheetValue.Hidden }
                density = Density(2f, 1.3f)
            }
            waitForIdle()
            lateinit var vetoed: Job
            runOnIdle {
                assertSame(initial, state)
                assertTrue(sameNativeObject(controller, parent.presentedViewController))
                assertEquals(SheetValue.PartiallyExpanded, state.currentValue)
                assertEquals(SheetValue.PartiallyExpanded, state.targetValue)
                vetoed = scope.launch { state.hide() }
            }
            waitForNative { vetoed.isCompleted }
            runOnIdle {
                assertFalse(vetoed.isCancelled)
                assertEquals(firstPolicyCalls, callsA)
                assertEquals(1, callsB)
                assertSame(initial, state)
                assertEquals(SheetValue.PartiallyExpanded, state.currentValue)
                assertTrue(sameNativeObject(controller, parent.presentedViewController))
                confirm = { callsB++; true }
            }
            waitForIdle()
            lateinit var hidden: Job
            runOnIdle { hidden = scope.launch { state.hide() } }
            waitForNative { hidden.isCompleted && parent.presentedViewController == null }
            runOnIdle {
                assertFalse(hidden.isCancelled)
                assertSame(initial, state)
                assertEquals(firstPolicyCalls, callsA)
                assertEquals(2, callsB)
                assertEquals(SheetValue.Hidden, state.currentValue)
            }
        } finally { runOnIdle { scope.cancel() } }
    }

    @Test fun realSaveableRegistryRestoresTheVisibleSheetAndStructuralSkipChangesReplaceOnlyItsOwner() {
        var saved: Map<String, List<Any?>>? = null
        val registry = SaveableStateRegistry(restoredValues = null) { true }
        runApplicationUiTest {
            lateinit var state: AdaptiveSheetState
            lateinit var parent: UIViewController
            setContent {
                CompositionLocalProvider(LocalSaveableStateRegistry provides registry) {
                    parent = LocalUIViewController.current
                    state = rememberAdaptiveSheetState()
                    AdaptiveBottomSheet(onDismissRequest = {}, adaptiveSheetState = state) { Spacer(Modifier.height(100.dp)) }
                }
            }
            waitForIdle()
            waitForNative { state.currentValue == SheetValue.PartiallyExpanded && parent.presentedViewController?.view?.window != null }
            runOnIdle { saved = registry.performSave(); assertTrue(assertNotNull(saved).isNotEmpty()) }
        }
        val restoredRegistry = SaveableStateRegistry(restoredValues = assertNotNull(saved)) { true }
        runApplicationUiTest {
            var skip by mutableStateOf(false)
            var density by mutableStateOf(Density(2f, 1.2f))
            var confirmations = 0
            lateinit var state: AdaptiveSheetState
            lateinit var parent: UIViewController
            setContent {
                CompositionLocalProvider(LocalSaveableStateRegistry provides restoredRegistry, LocalDensity provides density) {
                    parent = LocalUIViewController.current
                    state = rememberAdaptiveSheetState(skipPartiallyExpanded = skip) { confirmations++; true }
                    AdaptiveBottomSheet(onDismissRequest = {}, adaptiveSheetState = state) { Spacer(Modifier.height(100.dp)) }
                }
            }
            waitForIdle()
            waitForNative { state.currentValue == SheetValue.PartiallyExpanded && parent.presentedViewController?.view?.window != null }
            lateinit var restored: AdaptiveSheetState
            lateinit var priorController: UIViewController
            runOnIdle {
                restored = state
                priorController = assertNotNull(parent.presentedViewController)
                assertEquals(SheetValue.PartiallyExpanded, restored.currentValue)
                assertEquals(SheetValue.PartiallyExpanded, restored.targetValue)
                assertTrue(confirmations > 0)
                density = Density(3f, 1.5f)
            }
            waitForIdle()
            runOnIdle {
                assertSame(restored, state)
                assertTrue(sameNativeObject(priorController, parent.presentedViewController))
                skip = true // Deliberate structural change, not callback/density identity churn.
            }
            waitForIdle()
            waitForNative { state !== restored && state.currentValue == SheetValue.Expanded &&
                parent.presentedViewController?.view?.window != null && priorController.view.window == null }
            runOnIdle {
                assertNotSame(restored, state)
                assertNull(restored.iosSheetManager)
                assertEquals(SheetValue.Hidden, restored.currentValue)
                val replacement = assertNotNull(parent.presentedViewController)
                assertFalse(sameNativeObject(priorController, replacement))
                val sheet = assertNotNull(replacement.sheetPresentationController)
                assertEquals(1, sheet.detents.size)
                assertEquals(UISheetPresentationControllerDetentIdentifierLarge, sheet.selectedDetentIdentifier)
                assertEquals(SheetValue.Expanded, state.targetValue)
            }
        }
    }
}
