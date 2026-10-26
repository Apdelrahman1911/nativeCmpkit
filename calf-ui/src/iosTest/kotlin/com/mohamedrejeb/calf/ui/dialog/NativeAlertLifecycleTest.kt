@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, com.mohamedrejeb.calf.core.InternalCalfApi::class,
    androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.*
import com.mohamedrejeb.calf.ui.internal.waitForNative
import platform.UIKit.*
import kotlin.test.*

class NativeAlertLifecycleTest {
    @Test fun presentedAlertUsesLatestActionAndTextFieldCallbacks() = runComposeUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        var oldAction = 0
        var newAction = 0
        var oldField = 0
        var newField = 0
        var dismissals = 0
        lateinit var manager: AlertDialogManager
        val first = AlertDialogIosProperties(animated = false,
            actions = listOf(AlertDialogIosAction("Save", AlertDialogIosActionStyle.Default, { oldAction++ })),
            textFields = listOf(AlertDialogIosTextField(onValueChange = { oldField++ })))
        runOnIdle {
            manager = AlertDialogManager(parent, { dismissals++ }, first, DialogProperties())
            manager.showAlertDialog()
        }
        try {
            waitForNative { parent.presentedViewController is UIAlertController }
            runOnIdle {
                manager.iosProperties = first.copy(
                    actions = listOf(AlertDialogIosAction("Save", AlertDialogIosActionStyle.Default, { newAction++ })),
                    textFields = listOf(AlertDialogIosTextField(onValueChange = { newField++ })))
                manager.updateDialogProperties()
                val alert = parent.presentedViewController as UIAlertController
                val field = alert.textFields?.first() as UITextField
                field.text = "Changed"
                field.sendActionsForControlEvents(UIControlEventEditingChanged)
                // Exercises the production native action dispatch entrypoint, not synthesized touch.
                manager.activateAction(0)
                manager.activateAction(0)
                assertEquals(0, oldAction)
                assertEquals(1, newAction)
                assertEquals(0, oldField)
                assertEquals(1, newField)
            }
            waitForNative { parent.presentedViewController == null }
            assertEquals(0, dismissals)
        } finally { runOnIdle { manager.dispose() } }
    }

    @Test fun disposalDuringPresentationQueuesCleanupAndReplacement() = runComposeUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        var dismissals = 0
        lateinit var first: AlertDialogManager
        lateinit var second: AlertDialogManager
        runOnIdle {
            first = AlertDialogManager(parent, { dismissals++ }, AlertDialogIosProperties(title = "First"), DialogProperties())
            first.showAlertDialog()
            first.dispose()
            second = AlertDialogManager(parent, { dismissals++ }, AlertDialogIosProperties(title = "Second", animated = false), DialogProperties())
            second.showAlertDialog()
        }
        try {
            waitForNative { (parent.presentedViewController as? UIAlertController)?.title == "Second" }
            runOnIdle { second.dispose() }
            waitForNative { parent.presentedViewController == null }
            assertEquals(0, dismissals)
        } finally { runOnIdle { first.dispose(); second.dispose() } }
    }

    @Test fun actionSheetHasAPresentingViewPopoverAnchor() = runComposeUiTest {
        lateinit var parent: UIViewController
        setContent { parent = LocalUIViewController.current }
        lateinit var manager: AlertDialogManager
        runOnIdle {
            manager = AlertDialogManager(parent, {}, AlertDialogIosProperties(animated = false,
                style = AlertDialogIosStyle.ActionSheet), DialogProperties())
            manager.showAlertDialog()
        }
        try {
            waitForNative { parent.presentedViewController is UIAlertController }
            runOnIdle {
                val popover = requireNotNull((parent.presentedViewController as UIAlertController).popoverPresentationController)
                assertEquals(parent.view, popover.sourceView)
            }
        } finally { runOnIdle { manager.dispose() } }
        waitForNative { parent.presentedViewController == null }
    }
}
