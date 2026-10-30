// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.navigation

import android.os.SystemClock
import android.view.InputDevice
import android.view.KeyCharacterMap
import android.view.KeyEvent
import androidx.activity.compose.BackHandler
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Genuine Android input/public host, not a direct callback, sample or predictive-animation test. */
@RunWith(AndroidJUnit4::class)
class AndroidAdaptiveNavigationBackTest {
    @get:Rule val compose = createComposeRule()

    @Test fun nativeSystemBackPopsOneVisitUsesCurrentOwnerAndUnregistersOnDispose() {
        lateinit var original: AdaptiveNavHostController
        lateinit var compatibility: AdaptiveNavHostController
        var replacement by mutableStateOf<AdaptiveNavHostController?>(null)
        var mounted by mutableStateOf(true)
        var appBackCalls = 0
        val disposedVisits = mutableListOf<String>()
        compose.setContent {
            original = rememberAdaptiveNavController()
            compatibility = rememberNavController()
            // A real application callback remains available at the adaptive root/disposal.
            BackHandler { appBackCalls++ }
            if (mounted) {
                val current = replacement ?: original
                AdaptiveNavHost(current, "home") {
                    composable("home") { Text("home") }
                    composable("detail") {
                        Detail(assertNotNull(current.currentBackStackEntry).id, disposedVisits)
                    }
                }
            }
        }
        compose.onNodeWithText("home").assertIsDisplayed()
        compose.runOnIdle {
            assertNotSame(original, compatibility)
            assertFalse(original.canNavigateBack)
            assertNull(compatibility.currentBackStackEntry)
        }
        sendNativeBack()
        compose.runOnIdle { assertEquals(1, appBackCalls); assertEquals("home", original.currentDestination) }

        compose.runOnIdle { original.navigate("detail") }
        compose.onNodeWithText("detail 0").performClick()
        compose.onNodeWithText("detail 1").assertIsDisplayed()
        val firstVisit = compose.runOnIdle { assertNotNull(original.currentBackStackEntry).id }
        compose.runOnIdle { original.navigate("detail") }
        compose.onNodeWithText("detail 0").assertIsDisplayed()
        val poppedVisit = compose.runOnIdle { assertNotNull(original.currentBackStackEntry).id }
        sendNativeBack()
        compose.onNodeWithText("detail 1").assertIsDisplayed()
        compose.runOnIdle {
            assertEquals(firstVisit, original.currentBackStackEntry?.id)
            assertEquals(2, original.backStackEntries.size)
            assertEquals(1, disposedVisits.count { it == poppedVisit })
            assertEquals(1, appBackCalls, "One native BACK must not also reach the app fallback")
        }

        val currentOwner = AdaptiveNavHostController()
        compose.runOnIdle { replacement = currentOwner }
        compose.onNodeWithText("home").assertIsDisplayed()
        compose.runOnIdle { currentOwner.navigate("detail") }
        compose.onNodeWithText("detail 0").assertIsDisplayed()
        sendNativeBack()
        compose.onNodeWithText("home").assertIsDisplayed()
        compose.runOnIdle {
            assertEquals("home", currentOwner.currentDestination)
            assertEquals(firstVisit, original.currentBackStackEntry?.id, "The predecessor must not consume current BACK")
            assertEquals(1, appBackCalls)
            mounted = false
        }
        compose.waitForIdle()
        sendNativeBack()
        compose.runOnIdle {
            assertEquals(2, appBackCalls, "Disposal must unregister the actual adaptive BackHandler")
            assertEquals(1, currentOwner.backStackEntries.size)
            assertEquals(2, original.backStackEntries.size)
        }
    }

    @Composable private fun Detail(id: String, disposed: MutableList<String>) {
        var count by rememberSaveable { mutableStateOf(0) }
        // Plain remember is deliberately not claimed to survive an absent composition.
        val captured = remember(id) { id }
        DisposableEffect(captured) { onDispose { disposed += captured } }
        Button(onClick = { count++ }) { Text("detail $count") }
    }

    private fun sendNativeBack() {
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        val downTime = SystemClock.uptimeMillis()
        for (action in listOf(KeyEvent.ACTION_DOWN, KeyEvent.ACTION_UP)) {
            val event = KeyEvent(downTime, SystemClock.uptimeMillis(), action, KeyEvent.KEYCODE_BACK,
                0, 0, KeyCharacterMap.VIRTUAL_KEYBOARD, 0, KeyEvent.FLAG_FROM_SYSTEM, InputDevice.SOURCE_KEYBOARD)
            assertTrue(automation.injectInputEvent(event, true), "Real Android system BACK input must be delivered")
        }
        compose.waitForIdle()
    }
}
