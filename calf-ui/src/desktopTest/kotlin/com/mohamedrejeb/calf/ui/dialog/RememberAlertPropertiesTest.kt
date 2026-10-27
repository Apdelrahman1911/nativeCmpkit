package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.runtime.*
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.v2.runComposeUiTest
import com.mohamedrejeb.calf.ui.dialog.uikit.*
import kotlin.test.*

@OptIn(ExperimentalTestApi::class)
class RememberAlertPropertiesTest {
    @Test fun textFieldChangesAreNotHiddenByRememberKeys() = runComposeUiTest {
        val actions = emptyList<AlertDialogIosAction>()
        val first = AlertDialogIosTextField(placeholder = "First", onValueChange = {})
        val second = AlertDialogIosTextField(placeholder = "Second", onValueChange = {})
        var fields by mutableStateOf(listOf(first))
        var unrelated by mutableStateOf(0)
        lateinit var properties: AlertDialogIosProperties
        setContent {
            unrelated // Force an ordinary caller recomposition without changing any helper input.
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
        val replacement = properties
        runOnIdle { fields = listOf(second); unrelated++ }
        waitForIdle()
        assertSame(replacement, properties)
    }
}
