// SPDX-License-Identifier: Apache-2.0
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.isSpecified
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.layout.LayoutCoordinates
import androidx.compose.ui.test.*
import androidx.compose.ui.unit.dp
import kotlin.test.*
import android.graphics.Bitmap
import android.os.SystemClock
import android.view.KeyCharacterMap
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.InputDevice
import androidx.compose.ui.graphics.asImageBitmap
import androidx.test.platform.app.InstrumentationRegistry
import kotlin.math.ceil
import kotlin.math.floor

internal actual fun dropdownPosition(coordinates: LayoutCoordinates): Offset =
    coordinates.localToScreen(Offset.Zero).also { assertTrue(it.isSpecified, "Real popup screen coordinates are required") }

@OptIn(ExperimentalTestApi::class)
internal actual fun ComposeUiTest.captureDropdown(position: Offset): ImageBitmap {
    val screen = assertNotNull(InstrumentationRegistry.getInstrumentation().uiAutomation.takeScreenshot(),
        "A missing actual native screenshot is a failure, not a blank golden")
    try {
        val bounds = onNodeWithTag("dropdown-menu").fetchSemanticsNode().boundsInRoot
        val margin = with(density) { 24.dp.toPx() }
        val left = floor(position.x - margin).toInt().coerceAtLeast(0)
        val top = floor(position.y - margin).toInt().coerceAtLeast(0)
        val right = ceil(position.x + bounds.width + margin).toInt().coerceAtMost(screen.width)
        val bottom = ceil(position.y + bounds.height + margin).toInt().coerceAtMost(screen.height)
        assertTrue(right > left && bottom > top)
        // Include the real native shadow, but exclude dynamic system bars. No screenshot
        // bytes, user data, binaries or packages are written/uploaded by this fixture.
        return Bitmap.createBitmap(screen, left, top, right - left, bottom - top).asImageBitmap()
    } finally { screen.recycle() }
}

internal actual fun ComposeUiTest.dropdownBack(input: DropdownBackInput) {
    val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
    // Native input needs current monotonic times and a real keyboard identity;
    // the two-argument KeyEvent constructor sets both timestamps and source to zero.
    val downTime = SystemClock.uptimeMillis()
    for (action in listOf(KeyEvent.ACTION_DOWN, KeyEvent.ACTION_UP)) {
        val event = KeyEvent(downTime, SystemClock.uptimeMillis(), action, KeyEvent.KEYCODE_ESCAPE,
            0, 0, KeyCharacterMap.VIRTUAL_KEYBOARD, 0, KeyEvent.FLAG_FROM_SYSTEM, InputDevice.SOURCE_KEYBOARD)
        assertTrue(automation.injectInputEvent(event, true), "The actual native keyboard event must be delivered")
    }
    waitForIdle()
}

internal actual fun ComposeUiTest.dropdownOutside() {
    // Click the real screen away from every popup (below status bars, outside the
    // menu's >120dp top). UiAutomation, not a direct onDismissRequest invocation.
    val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
    val time = SystemClock.uptimeMillis()
    for (action in listOf(MotionEvent.ACTION_DOWN, MotionEvent.ACTION_UP)) {
        val event = MotionEvent.obtain(time, SystemClock.uptimeMillis(),
            action, 5f, with(density) { 90.dp.toPx() }, 0)
        event.source = InputDevice.SOURCE_TOUCHSCREEN
        try { assertTrue(automation.injectInputEvent(event, true)) } finally { event.recycle() }
    }
    waitForIdle()
}
