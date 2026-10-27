@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class,
    com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi::class)

package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.internal.waitForNative
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import platform.UIKit.*
import kotlin.test.*

class NativeDropDownLifecycleTest {
    private fun UIView.menuButtons(): List<DropDownMenuButton> = if (this is DropDownMenuButton) listOf(this)
        else subviews.filterIsInstance<UIView>().flatMap { it.menuButtons() }

    @Test fun expandedStateControlsActualMenuAndDismissalIsNotReportedAtOpen() = runApplicationUiTest {
        var expanded by mutableStateOf(false)
        var dismissals = 0
        lateinit var parent: UIViewController
        val items = listOf(AdaptiveDropDownItem("One", onClick = {}))
        setContent {
            parent = LocalUIViewController.current
            Box(Modifier.size(200.dp, 44.dp)) {
                AdaptiveDropDown(expanded = expanded, onDismissRequest = { dismissals++; expanded = false },
                    iosItems = items) { Text("Fallback") }
            }
        }
        waitForIdle()
        // Composition idle can precede the renderer's UIKit interop transaction.
        // Require the actual unique attached view,
        // not an elapsed delay or an empty-tree assumption.
        waitForNative {
            val button = parent.view.menuButtons().singleOrNull()
            button != null && sameNativeObject(button.window, parent.view.window)
        }
        lateinit var button: DropDownMenuButton
        runOnIdle {
            assertTrue(supportsProgrammaticNativeMenu(UIDevice.currentDevice.systemVersion))
            button = parent.view.menuButtons().single()
            expanded = true
        }
        try {
            waitForNative { button.isMenuPresented }
            assertEquals(0, dismissals)
            runOnIdle { expanded = false }
            waitForNative { !button.isMenuPresented }
            assertEquals(0, dismissals)
            runOnIdle { expanded = true }
            waitForNative { button.isMenuPresented }
            // Calls the public UIKit dismissal API, exercising its real willEnd callback.
            runOnIdle { button.contextMenuInteraction?.dismissMenu() }
            waitForNative { dismissals == 1 && !button.isMenuPresented }
        } finally { runOnIdle { expanded = false; button.dispose() } }
    }
}
