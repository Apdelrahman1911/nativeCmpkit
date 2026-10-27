@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosAction
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosTextField
import com.mohamedrejeb.calf.ui.dialog.uikit.rememberAlertDialogIosProperties
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotSame
import kotlin.test.assertSame

/** Composition/remember contract only; native alert touches belong to the lifecycle suite. */
class RememberNativeAlertPropertiesTest {
    @Test fun stableInputsRetainIdentityButTextFieldReplacementReachesTheCaller() = runApplicationUiTest {
        val actions = emptyList<AlertDialogIosAction>()
        var firstChanges = 0
        var secondChanges = 0
        val first = AlertDialogIosTextField(placeholder = "First", onValueChange = { firstChanges++ })
        val second = AlertDialogIosTextField(placeholder = "Second", onValueChange = { secondChanges++ })
        var fields by mutableStateOf(listOf(first))
        var unrelated by mutableStateOf(0)
        lateinit var properties: AlertDialogIosProperties
        setContent {
            unrelated // Recompose the caller with the same title/actions and other properties.
            properties = rememberAlertDialogIosProperties(actions = actions, textFields = fields)
        }
        waitForIdle()
        val initial = properties
        runOnIdle { unrelated++ }
        waitForIdle()
        assertSame(initial, properties)

        runOnIdle { fields = listOf(second) }
        waitForIdle()
        assertNotSame(initial, properties)
        assertEquals(listOf(second), properties.textFields)
        properties.textFields.single().onValueChange("current")
        assertEquals(0, firstChanges)
        assertEquals(1, secondChanges)

        val replacement = properties
        runOnIdle { fields = listOf(second); unrelated++ }
        waitForIdle()
        assertSame(replacement, properties)
    }
}
