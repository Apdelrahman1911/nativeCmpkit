// Modified for NativeCmpKit (2026-10-28): DEX-compatible test names, assertions unchanged.
package com.mohamedrejeb.calf.ui.dialog

import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosActionStyle
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class AdaptiveAlertDialogActionsTest {

    @Test
    fun buildsOnlyTheConfirmActionWhenDismissTextIsNull() {
        val actions = adaptiveAlertDialogIosActions(
            confirmText = "OK",
            dismissText = null,
            onConfirm = {},
            onDismiss = {},
            confirmStyle = AlertDialogIosActionStyle.Default,
            dismissStyle = AlertDialogIosActionStyle.Cancel,
            confirmIsPreferred = false,
        )

        assertEquals(listOf("OK"), actions.map { it.title })
    }

    @Test
    fun buildsOnlyTheConfirmActionWhenDismissTextIsBlank() {
        val actions = adaptiveAlertDialogIosActions(
            confirmText = "OK",
            dismissText = "   ",
            onConfirm = {},
            onDismiss = {},
            confirmStyle = AlertDialogIosActionStyle.Default,
            dismissStyle = AlertDialogIosActionStyle.Cancel,
            confirmIsPreferred = false,
        )

        assertEquals(listOf("OK"), actions.map { it.title })
    }

    @Test
    fun buildsConfirmThenDismissActionWhenDismissTextIsProvided() {
        val actions = adaptiveAlertDialogIosActions(
            confirmText = "OK",
            dismissText = "Cancel",
            onConfirm = {},
            onDismiss = {},
            confirmStyle = AlertDialogIosActionStyle.Default,
            dismissStyle = AlertDialogIosActionStyle.Destructive,
            confirmIsPreferred = true,
        )

        assertEquals(listOf("OK", "Cancel"), actions.map { it.title })
        assertEquals(
            listOf(AlertDialogIosActionStyle.Default, AlertDialogIosActionStyle.Destructive),
            actions.map { it.style },
        )
        assertEquals(listOf(true, false), actions.map { it.isPreferred })
    }

    @Test
    fun wiresConfirmAndDismissCallbacksToTheirOwnActions() {
        var confirmed = false
        var dismissed = false
        val actions = adaptiveAlertDialogIosActions(
            confirmText = "OK",
            dismissText = "Cancel",
            onConfirm = { confirmed = true },
            onDismiss = { dismissed = true },
            confirmStyle = AlertDialogIosActionStyle.Default,
            dismissStyle = AlertDialogIosActionStyle.Cancel,
            confirmIsPreferred = false,
        )

        actions[0].onClick()
        assertTrue(confirmed)
        assertFalse(dismissed)

        actions[1].onClick()
        assertTrue(dismissed)
    }
}
