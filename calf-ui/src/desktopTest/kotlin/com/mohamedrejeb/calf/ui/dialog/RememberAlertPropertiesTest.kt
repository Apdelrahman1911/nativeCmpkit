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
        lateinit var properties: AlertDialogIosProperties
        setContent { properties = rememberAlertDialogIosProperties(actions = actions, textFields = fields) }
        waitForIdle()
        runOnIdle { fields = listOf(second) }
        waitForIdle()
        assertEquals(listOf(second), properties.textFields)
    }
}
