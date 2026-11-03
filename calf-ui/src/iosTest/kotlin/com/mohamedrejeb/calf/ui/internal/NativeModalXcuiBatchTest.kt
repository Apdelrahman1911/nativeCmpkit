// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    com.mohamedrejeb.calf.core.InternalCalfApi::class,
    com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi::class)

package com.mohamedrejeb.calf.ui.internal

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.ModalBottomSheetProperties
import androidx.compose.material3.SheetValue
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.SaverScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.ui.dialog.AdaptiveAlertDialog
import com.mohamedrejeb.calf.ui.dialog.AdaptiveBasicAlertDialog
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosAction
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosActionStyle
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosTextField
import com.mohamedrejeb.calf.ui.sheet.AdaptiveBottomSheet
import com.mohamedrejeb.calf.ui.sheet.AdaptiveSheetState
import kotlinx.cinterop.useContents
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import platform.UIKit.*
import kotlin.test.*

/** Missing original interaction criteria across #28/#30/#125/#126, in one batch. */
class NativeModalXcuiBatchTest {
    @Test fun liveAlertCallbacksAndKeyboardUseOnlyCurrentDescriptors() = runApplicationUiTest {
        val case = "liveAlertCallbacksAndKeyboardUseOnlyCurrentDescriptors"
        var parent: UIViewController? = null
        var visible by mutableStateOf(true)
        val oldEdits = mutableListOf<String>()
        val newEdits = mutableListOf<String>()
        val actions = mutableListOf<String>()
        var dismissals = 0
        val initial = AlertDialogIosProperties(title = "Record A", text = "Delete A", animated = false,
            actions = listOf(AlertDialogIosAction("Confirm", AlertDialogIosActionStyle.Default,
                { actions += "A"; visible = false }, enabled = false)),
            textFields = listOf(AlertDialogIosTextField(placeholder = "Owned field", onValueChange = { oldEdits += it })))
        var properties by mutableStateOf(initial)
        setContent {
            parent = LocalUIViewController.current
            if (visible) AdaptiveBasicAlertDialog(onDismissRequest = { dismissals++; visible = false },
                iosProperties = properties, materialContent = {})
        }
        val first = alert({ parent }, "Record A")
        val field = runOnIdle {
            assertFalse(first.actions.filterIsInstance<UIAlertAction>().single().enabled)
            assertNotNull(first.textFields?.filterIsInstance<UITextField>()?.single())
        }
        runOnIdle {
            properties = initial.copy(title = "Record B", text = "Delete B",
                actions = listOf(AlertDialogIosAction("Confirm", AlertDialogIosActionStyle.Default,
                    { actions += "B"; visible = false }, enabled = true)),
                textFields = listOf(initial.textFields.single().copy(onValueChange = { newEdits += it })))
        }
        val current = alert({ parent }, "Record B")
        runOnIdle {
            assertTrue(sameNativeObject(first, current))
            assertTrue(sameNativeObject(field, current.textFields?.filterIsInstance<UITextField>()?.single()))
            assertEquals("Delete B", current.message)
            assertTrue(current.actions.filterIsInstance<UIAlertAction>().single().enabled)
        }
        val input = nativeXcuiInput("alert-field", mapOf("case" to case, "title" to "Record B",
            "label" to "Owned field", "text" to "Changed"))
        runOnIdle {
            assertEquals("Changed", input["value"])
            assertEquals("Changed", field.text)
            assertTrue(oldEdits.isEmpty())
            assertEquals("Changed", newEdits.last())
            assertTrue(actions.isEmpty())
        }
        button(case, "Record B", "Confirm")
        waitForNative { parent?.presentedViewController == null && first.view.window == null }
        runOnIdle { assertEquals(listOf("B"), actions); assertEquals(0, dismissals) }
    }

    @Test fun reorderedAlertActionsAndConfirmCancelRemovalAreExactlyOnce() {
        val case = "reorderedAlertActionsAndConfirmCancelRemovalAreExactlyOnce"
        runApplicationUiTest {
            var parent: UIViewController? = null
            var visible by mutableStateOf(true)
            val actions = mutableListOf<String>()
            var dismissals = 0
            var properties by mutableStateOf(AlertDialogIosProperties(title = "Before reorder", animated = false,
                actions = listOf(
                    AlertDialogIosAction("Save", AlertDialogIosActionStyle.Default, { actions += "Save A" }),
                    AlertDialogIosAction("Cancel", AlertDialogIosActionStyle.Cancel, { actions += "Cancel A" }))))
            setContent {
                parent = LocalUIViewController.current
                if (visible) AdaptiveBasicAlertDialog(onDismissRequest = { dismissals++; visible = false },
                    iosProperties = properties, materialContent = {})
            }
            val first = alert({ parent }, "Before reorder")
            runOnIdle {
                properties = properties.copy(title = "After reorder", actions = listOf(
                    AlertDialogIosAction("Cancel", AlertDialogIosActionStyle.Cancel, { actions += "Cancel B"; visible = false }),
                    AlertDialogIosAction("Save", AlertDialogIosActionStyle.Default, { actions += "Save B"; visible = false })))
            }
            val rebuilt = alert({ parent }, "After reorder")
            runOnIdle {
                assertFalse(sameNativeObject(first, rebuilt)); assertNull(first.view.window)
                assertEquals(listOf("Cancel", "Save"), rebuilt.actions.filterIsInstance<UIAlertAction>().map { it.title })
                assertTrue(actions.isEmpty())
            }
            button(case, "After reorder", "Save")
            waitForNative { parent?.presentedViewController == null && rebuilt.view.window == null }
            runOnIdle { assertEquals(listOf("Save B"), actions); assertEquals(0, dismissals) }
        }
        for (confirm in listOf(true, false)) runApplicationUiTest {
            var parent: UIViewController? = null
            var visible by mutableStateOf(true)
            var reopened by mutableStateOf(false)
            var confirms = 0
            var cancels = 0
            setContent {
                parent = LocalUIViewController.current
                if (visible) AdaptiveAlertDialog(onConfirm = { confirms++; visible = false },
                    onDismiss = { cancels++; visible = false }, confirmText = "Confirm", dismissText = "Cancel",
                    title = if (reopened) "Immediate reopen" else "Semantic owner", text = "Owned callback")
            }
            val first = alert({ parent }, "Semantic owner")
            button(case, "Semantic owner", if (confirm) "Confirm" else "Cancel")
            waitForNative { parent?.presentedViewController == null && first.view.window == null }
            runOnIdle {
                assertEquals(if (confirm) 1 else 0, confirms); assertEquals(if (confirm) 0 else 1, cancels)
                reopened = true; visible = true
            }
            val second = alert({ parent }, "Immediate reopen")
            runOnIdle { assertFalse(sameNativeObject(first, second)); visible = false }
            waitForNative { parent?.presentedViewController == null && second.view.window == null }
            runOnIdle { assertEquals(if (confirm) 1 else 0, confirms); assertEquals(if (confirm) 0 else 1, cancels) }
        }
    }

    @Test fun insideAndOutsideNativeTouchesRespectDismissalProperties() = runApplicationUiTest {
        val case = "insideAndOutsideNativeTouchesRespectDismissalProperties"
        var parent: UIViewController? = null
        var visible by mutableStateOf(true)
        var outside by mutableStateOf(false)
        var dismissals = 0
        val edits = mutableListOf<String>()
        setContent {
            parent = LocalUIViewController.current
            if (visible) AdaptiveBasicAlertDialog(onDismissRequest = { dismissals++; visible = false },
                iosProperties = AlertDialogIosProperties(title = "Inside outside", animated = false,
                    actions = listOf(AlertDialogIosAction("Done", AlertDialogIosActionStyle.Default, {})),
                    textFields = listOf(AlertDialogIosTextField(placeholder = "Inside field", onValueChange = { edits += it }))),
                properties = DialogProperties(dismissOnClickOutside = outside), materialContent = {})
        }
        val current = alert({ parent }, "Inside outside")
        nativeXcuiInput("alert-field", mapOf("case" to case, "title" to "Inside outside",
            "label" to "Inside field", "text" to "Inside"))
        runOnIdle { assertEquals("Inside", edits.last()); assertEquals(0, dismissals) }
        val point = runOnIdle { outsidePoint(current) }
        nativeXcuiInput("tap", mapOf("case" to case) + point)
        runOnIdle { assertEquals(0, dismissals); assertTrue(sameNativeObject(current, parent?.presentedViewController)) }
        runOnIdle { outside = true }
        waitForIdle()
        nativeXcuiInput("tap", mapOf("case" to case) + point)
        waitForNative { parent?.presentedViewController == null && current.view.window == null }
        runOnIdle { assertEquals(1, dismissals) }
    }

    @Test fun animatedAlertDisposalAndPresenterReplacementDoNotNotifyUser() {
        val case = "animatedAlertDisposalAndPresenterReplacementDoNotNotifyUser"
        var priorParent: UIViewController? = null
        for (duringShow in listOf(true, false)) runApplicationUiTest {
            var parent: UIViewController? = null
            var dismissals = 0
            var confirms = 0
            var properties by mutableStateOf(AlertDialogIosProperties(title = "Animated owner", animated = true,
                actions = listOf(AlertDialogIosAction("Old", AlertDialogIosActionStyle.Default, {}))))
            setContent { parent = LocalUIViewController.current }
            waitForIdle()
            runOnIdle {
                if (priorParent != null) assertFalse(sameNativeObject(priorParent, parent))
                setContent {
                    parent = LocalUIViewController.current
                    AdaptiveBasicAlertDialog(onDismissRequest = { dismissals++ }, iosProperties = properties, materialContent = {})
                }
            }
            if (duringShow) waitForNative { parent?.presentedViewController?.isBeingPresented() == true }
            else {
                alert({ parent }, "Animated owner")
                runOnIdle { properties = properties.copy(actions = listOf(AlertDialogIosAction("New", AlertDialogIosActionStyle.Default, {}))) }
                waitForNative { parent?.presentedViewController?.isBeingDismissed() == true }
            }
            val removed = runOnIdle {
                val native = assertNotNull(parent?.presentedViewController)
                assertTrue(if (duringShow) native.isBeingPresented() else native.isBeingDismissed())
                setContent { }
                native
            }
            waitForIdle()
            waitForNative { parent?.presentedViewController == null && removed.view.window == null }
            var reopen by mutableStateOf(true)
            runOnIdle {
                assertEquals(0, dismissals)
                setContent {
                    parent = LocalUIViewController.current
                    if (reopen) AdaptiveAlertDialog(onConfirm = { confirms++; reopen = false },
                        onDismiss = { dismissals++; reopen = false }, confirmText = "Done", dismissText = null,
                        title = "Actual reopen", text = "Retired owners cannot deliver")
                }
            }
            val reopened = alert({ parent }, "Actual reopen")
            button(case, "Actual reopen", "Done")
            waitForNative { parent?.presentedViewController == null && reopened.view.window == null }
            runOnIdle { assertEquals(1, confirms); assertEquals(0, dismissals); priorParent = parent }
        }
    }

    @Test fun nativeDetentDragsAndInteractiveDismissalTrackAllValues() = runApplicationUiTest {
        val case = "nativeDetentDragsAndInteractiveDismissalTrackAllValues"
        val state = state()
        var parent: UIViewController? = null
        var dismissals = 0
        setContent {
            parent = LocalUIViewController.current
            AdaptiveBottomSheet(onDismissRequest = { dismissals++ }, adaptiveSheetState = state) { Spacer(Modifier.height(120.dp)) }
        }
        val medium = sheet(state, { parent }, SheetValue.PartiallyExpanded)
        val middle = runOnIdle { dragOrigin(medium) }
        runOnIdle { assertDetents(medium, false) }
        drag(case, medium, .13)
        val expanded = sheet(state, { parent }, SheetValue.Expanded)
        runOnIdle { assertTrue(sameNativeObject(medium, expanded)); assertEquals(0, dismissals) }
        drag(case, expanded, middle["y"]!!)
        sheet(state, { parent }, SheetValue.PartiallyExpanded)
        drag(case, medium, .97)
        waitForNative { state.currentValue == SheetValue.Hidden && state.targetValue == SheetValue.Hidden && parent?.presentedViewController == null }
        runOnIdle { assertEquals(1, dismissals); assertNotNull(state.iosSheetManager); assertNull(medium.view.window) }
    }

    @Test fun nativeSheetVetoesAndSkipFlagsRespectCurrentPolicies() {
        val case = "nativeSheetVetoesAndSkipFlagsRespectCurrentPolicies"
        runApplicationUiTest {
            var allowExpanded = false
            var allowHidden = false
            var outside by mutableStateOf(false)
            var dismissals = 0
            val confirmations = mutableListOf<SheetValue>()
            val state = state(confirm = { value -> confirmations += value; when (value) {
                SheetValue.Expanded -> allowExpanded; SheetValue.Hidden -> allowHidden; else -> true } })
            var parent: UIViewController? = null
            setContent {
                parent = LocalUIViewController.current
                AdaptiveBottomSheet(onDismissRequest = { dismissals++ }, adaptiveSheetState = state,
                    properties = ModalBottomSheetProperties(shouldDismissOnClickOutside = outside)) { Spacer(Modifier.height(120.dp)) }
            }
            val medium = sheet(state, { parent }, SheetValue.PartiallyExpanded)
            val middle = runOnIdle { dragOrigin(medium) }
            var expandedBefore = 0
            runOnIdle { expandedBefore = confirmations.count { it == SheetValue.Expanded } }
            drag(case, medium, .13)
            waitForNative { confirmations.count { it == SheetValue.Expanded } > expandedBefore &&
                state.currentValue == SheetValue.PartiallyExpanded &&
                medium.sheetPresentationController?.selectedDetentIdentifier == UISheetPresentationControllerDetentIdentifierMedium }
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            try {
                lateinit var vetoed: Job
                runOnIdle { vetoed = scope.launch { state.hide() } }
                waitForNative { vetoed.isCompleted }
                runOnIdle { assertFalse(vetoed.isCancelled); assertEquals(0, dismissals); allowHidden = true }
                val point = runOnIdle { outsidePoint(medium) }
                nativeXcuiInput("tap", mapOf("case" to case) + point)
                runOnIdle { assertEquals(0, dismissals); assertTrue(sameNativeObject(medium, parent?.presentedViewController)) }
                runOnIdle { outside = true; allowHidden = false }
                waitForIdle()
                val outsideHiddenBefore = runOnIdle { confirmations.count { it == SheetValue.Hidden } }
                nativeXcuiInput("tap", mapOf("case" to case) + point)
                waitForNative { confirmations.count { it == SheetValue.Hidden } > outsideHiddenBefore &&
                    state.currentValue == SheetValue.PartiallyExpanded && parent?.presentedViewController != null }
                runOnIdle { assertEquals(0, dismissals) }
                val hiddenBefore = runOnIdle { confirmations.count { it == SheetValue.Hidden } }
                drag(case, medium, .97)
                waitForNative { confirmations.count { it == SheetValue.Hidden } > hiddenBefore && parent?.presentedViewController != null }
                runOnIdle { assertEquals(0, dismissals); allowExpanded = true; allowHidden = true }
                drag(case, medium, .13)
                val expanded = sheet(state, { parent }, SheetValue.Expanded)
                drag(case, expanded, middle["y"]!!)
                sheet(state, { parent }, SheetValue.PartiallyExpanded)
                nativeXcuiInput("tap", mapOf("case" to case) + point)
                waitForNative { state.currentValue == SheetValue.Hidden && parent?.presentedViewController == null }
                runOnIdle { assertEquals(1, dismissals) }
            } finally { runOnIdle { scope.cancel() } }
        }
        runApplicationUiTest {
            val state = state(skipPartial = true, skipHidden = true, initial = SheetValue.Expanded)
            var parent: UIViewController? = null
            var dismissals = 0
            setContent {
                parent = LocalUIViewController.current
                AdaptiveBottomSheet(onDismissRequest = { dismissals++ }, adaptiveSheetState = state) { Spacer(Modifier.height(120.dp)) }
            }
            val expanded = sheet(state, { parent }, SheetValue.Expanded)
            runOnIdle { assertDetents(expanded, true) }
            drag(case, expanded, .97)
            runOnIdle { assertEquals(SheetValue.Expanded, state.currentValue); assertEquals(0, dismissals) }
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            try {
                var refusal: Throwable? = null
                lateinit var hiding: Job
                runOnIdle { hiding = scope.launch { try { state.hide() } catch (error: Throwable) { refusal = error } } }
                waitForNative { hiding.isCompleted }
                runOnIdle { assertIs<IllegalStateException>(refusal); setContent { } }
                waitForIdle()
                waitForNative { parent?.presentedViewController == null && state.iosSheetManager == null }
                runOnIdle { assertEquals(0, dismissals) }
            } finally { runOnIdle { scope.cancel() } }
        }
        runApplicationUiTest {
            var allowExpanded = false
            var allowHidden = false
            val confirmations = mutableListOf<SheetValue>()
            val state = state(skipPartial = true, confirm = { value ->
                confirmations += value
                if (value == SheetValue.Expanded) allowExpanded else allowHidden
            })
            var parent: UIViewController? = null
            setContent {
                parent = LocalUIViewController.current
                AdaptiveBottomSheet(onDismissRequest = {}, adaptiveSheetState = state) { Spacer(Modifier.height(120.dp)) }
            }
            waitForNative { confirmations.contains(SheetValue.Expanded) }
            runOnIdle { assertEquals(SheetValue.Hidden, state.currentValue); assertNull(parent?.presentedViewController); allowExpanded = true }
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            try {
                lateinit var showing: Job
                runOnIdle { showing = scope.launch { state.show() } }
                sheet(state, { parent }, SheetValue.Expanded)
                lateinit var vetoed: Job
                runOnIdle { assertTrue(showing.isCompleted); vetoed = scope.launch { state.hide() } }
                waitForNative { vetoed.isCompleted }
                runOnIdle { assertEquals(SheetValue.Expanded, state.currentValue); assertNotNull(parent?.presentedViewController); allowHidden = true }
                lateinit var hidden: Job
                runOnIdle { hidden = scope.launch { state.hide() } }
                waitForNative { hidden.isCompleted && parent?.presentedViewController == null }
                runOnIdle { assertEquals(SheetValue.Hidden, state.currentValue); assertFalse(hidden.isCancelled) }
            } finally { runOnIdle { scope.cancel() } }
        }
    }

    @Test fun nativeSheetSaveRestoreAndRegularWidthAdaptationRemainConsistent() {
        val case = "nativeSheetSaveRestoreAndRegularWidthAdaptationRemainConsistent"
        val saved = mutableListOf<SheetValue>()
        val saver = AdaptiveSheetState.Saver(false, { 56f }, { 125f }, { true }, false)
        val saveScope = object : SaverScope { override fun canBeSaved(value: Any) = true }
        runApplicationUiTest {
            val state = state()
            var parent: UIViewController? = null
            setContent {
                parent = LocalUIViewController.current
                AdaptiveBottomSheet(onDismissRequest = {}, adaptiveSheetState = state) { Spacer(Modifier.height(120.dp)) }
            }
            val medium = sheet(state, { parent }, SheetValue.PartiallyExpanded)
            runOnIdle { assertDetents(medium, false); saved += assertNotNull(with(saver) { saveScope.save(state) }) }
            drag(case, medium, .13)
            val expanded = sheet(state, { parent }, SheetValue.Expanded)
            runOnIdle { saved += assertNotNull(with(saver) { saveScope.save(state) }) }
            drag(case, expanded, .97)
            waitForNative { state.currentValue == SheetValue.Hidden && parent?.presentedViewController == null }
            runOnIdle { saved += assertNotNull(with(saver) { saveScope.save(state) }) }
        }
        assertEquals(listOf(SheetValue.PartiallyExpanded, SheetValue.Expanded, SheetValue.Hidden), saved)
        for (value in saved) runApplicationUiTest {
            val restored = assertNotNull(saver.restore(value))
            runOnIdle { assertEquals(value, restored.currentValue); assertEquals(value, restored.targetValue); assertNull(restored.iosSheetManager) }
            var parent: UIViewController? = null
            setContent {
                parent = LocalUIViewController.current
                AdaptiveBottomSheet(onDismissRequest = {}, adaptiveSheetState = restored) { Spacer(Modifier.height(120.dp)) }
            }
            val actual = sheet(restored, { parent }, if (value == SheetValue.Hidden) SheetValue.PartiallyExpanded else value)
            runOnIdle {
                assertDetents(actual, false)
                val window = requireOwnedApplicationWindow()
                val width = actual.view.bounds.useContents { size.width }
                val available = window.bounds.useContents { size.width }
                assertTrue(width > 0 && width <= available)
                if (UIDevice.currentDevice.userInterfaceIdiom == UIUserInterfaceIdiomPad) {
                    assertEquals(UIUserInterfaceSizeClassRegular, actual.traitCollection.horizontalSizeClass)
                }
            }
        }
    }

    private fun state(skipPartial: Boolean = false, skipHidden: Boolean = false,
        initial: SheetValue = SheetValue.Hidden, confirm: (SheetValue) -> Boolean = { true }) =
        AdaptiveSheetState(skipPartial, confirm, initial, skipHidden, { 56f }, { 125f })

    private fun NativeApplicationUiTest.alert(parent: () -> UIViewController?, title: String): UIAlertController {
        waitForNative { (parent()?.presentedViewController as? UIAlertController)?.let {
            it.title == title && it.view.window != null && !it.isBeingPresented() && !it.isBeingDismissed() } == true }
        return runOnIdle { assertNotNull(parent()?.presentedViewController as? UIAlertController) }
    }

    private fun NativeApplicationUiTest.sheet(state: AdaptiveSheetState, parent: () -> UIViewController?, value: SheetValue): UIViewController {
        waitForNative { state.currentValue == value && state.targetValue == value &&
            parent()?.presentedViewController?.let { it.view.window != null && !it.isBeingPresented() && !it.isBeingDismissed() } == true }
        return runOnIdle { assertNotNull(parent()?.presentedViewController) }
    }

    private fun button(case: String, title: String, label: String) =
        nativeXcuiInput("alert-button", mapOf("case" to case, "title" to title, "label" to label))

    private fun NativeApplicationUiTest.drag(case: String, controller: UIViewController, targetY: Double) {
        val origin = runOnIdle { dragOrigin(controller) }
        nativeXcuiInput("drag", mapOf("case" to case, "toX" to origin.getValue("x"), "toY" to targetY) + origin)
    }

    private fun dragOrigin(controller: UIViewController): Map<String, Double> {
        val window = requireOwnedApplicationWindow()
        val frame = controller.view.convertRect(controller.view.bounds, toView = window)
        val width = window.bounds.useContents { size.width }
        val height = window.bounds.useContents { size.height }
        return frame.useContents { mapOf("x" to (origin.x + size.width / 2) / width, "y" to (origin.y + 18) / height) }
    }

    private fun outsidePoint(controller: UIViewController): Map<String, Double> {
        val window = requireOwnedApplicationWindow()
        val frame = controller.view.convertRect(controller.view.bounds, toView = window)
        val width = window.bounds.useContents { size.width }
        val height = window.bounds.useContents { size.height }
        val choices = listOf(.04 to .16, .96 to .16, .04 to .86)
        val point = choices.firstOrNull { (x, y) -> frame.useContents {
            x * width < origin.x || x * width > origin.x + size.width || y * height < origin.y || y * height > origin.y + size.height
        } } ?: error("This native presentation has no qualified outside point")
        return mapOf("x" to point.first, "y" to point.second)
    }

    private fun assertDetents(controller: UIViewController, skipPartial: Boolean) {
        val sheet = assertNotNull(controller.sheetPresentationController)
        assertEquals(if (skipPartial) listOf(UISheetPresentationControllerDetentIdentifierLarge) else
            listOf(UISheetPresentationControllerDetentIdentifierMedium, UISheetPresentationControllerDetentIdentifierLarge),
            sheet.detents.filterIsInstance<UISheetPresentationControllerDetent>().map { it.identifier })
    }
}
