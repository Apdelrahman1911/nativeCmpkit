// SPDX-License-Identifier: Apache-2.0
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.surfaceColorAtElevation
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.layout.LayoutCoordinates
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.*
import androidx.compose.ui.unit.*
import androidx.compose.ui.window.PopupProperties
import androidx.navigationevent.NavigationEventInput
import androidx.navigationevent.compose.LocalNavigationEventDispatcherOwner
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import kotlin.test.*

/** Android uses real native window positions/keyboard/pointer APIs. Skiko uses its
 * actual scene raster/pointer APIs and public navigation input, not OS key routing. */
internal expect fun dropdownPosition(coordinates: LayoutCoordinates): Offset
internal expect fun ComposeUiTest.captureDropdown(position: Offset): ImageBitmap
internal expect fun ComposeUiTest.dropdownBack(input: DropdownBackInput)
internal expect fun ComposeUiTest.dropdownOutside()

/** Complete back through the actual dependency dispatcher, never the menu callback.
 * A semantics Escape key bypasses Compose1.12's host navigation-event bridge. */
internal class DropdownBackInput : NavigationEventInput() {
    fun completeBack() = dispatchOnBackCompleted()
}

@OptIn(ExperimentalTestApi::class, ExperimentalCalfUiApi::class)
private class MenuFixture(private val test: ComposeUiTest) {
    var expanded by mutableStateOf(true)
    var reference by mutableStateOf(false)
    var direction by mutableStateOf(LayoutDirection.Ltr)
    var offset by mutableStateOf(DpOffset.Zero)
    var properties by mutableStateOf(PopupProperties(focusable = true))
    var styled by mutableStateOf(true)
    var long by mutableStateOf(false)
    val scroll = ScrollState(0)
    val backInput = DropdownBackInput()
    var position: Offset? = null
    var expectedSurfaceArgb = 0
    var dismissals = 0

    fun mount() = test.setContent {
        val dispatcher = checkNotNull(LocalNavigationEventDispatcherOwner.current).navigationEventDispatcher
        DisposableEffect(dispatcher) {
            val input = backInput
            dispatcher.addInput(input)
            onDispose { dispatcher.removeInput(input) }
        }
        MaterialTheme(colorScheme = lightColorScheme(surface = Color(0xFF53A02D), surfaceTint = Color.Blue)) {
            expectedSurfaceArgb = MaterialTheme.colorScheme.surfaceColorAtElevation(7.dp).toArgb()
            CompositionLocalProvider(LocalLayoutDirection provides direction) {
                Box(Modifier.fillMaxSize().background(Color.White).testTag("dropdown-underlay")) {
                    Box(Modifier.padding(40.dp).width(180.dp).height(80.dp)) {
                        val modifier = Modifier.testTag("dropdown-menu")
                            .onGloballyPositioned { position = dropdownPosition(it) }
                        val shape = if (styled) RoundedCornerShape(28.dp) else RoundedCornerShape(0.dp)
                        val color = if (styled) Color(0xFF53A02D) else Color.White
                        val border = if (styled) BorderStroke(3.dp, Color(0xFFD132B4)) else null
                        val content: @Composable ColumnScope.() -> Unit = {
                            if (long) repeat(100) { Text("Item $it", Modifier.testTag("dropdown-item-$it")) }
                            else Box(Modifier.width(128.dp).height(80.dp))
                        }
                        val dismiss = { dismissals++; expanded = false }
                        // An independent call to the actual dependency is the reference, not
                        // a mirrored/recording substitute for the library's implementation.
                        key(reference) {
                            if (reference) DropdownMenu(expanded = expanded, onDismissRequest = dismiss,
                                modifier = modifier, offset = offset, scrollState = scroll, properties = properties,
                                shape = shape, containerColor = color, tonalElevation = 7.dp, shadowElevation = 9.dp,
                                border = border, content = content)
                            else AdaptiveDropDown(expanded = expanded, onDismissRequest = dismiss, iosItems = emptyList(),
                                modifier = modifier, offset = offset, scrollState = scroll, properties = properties,
                                shape = shape, containerColor = color, tonalElevation = 7.dp, shadowElevation = 9.dp,
                                border = border, iosSections = emptyList(), materialContent = content)
                        }
                    }
                }
            }
        }
    }

    fun ready() {
        test.onNodeWithTag("dropdown-menu").assertIsDisplayed()
        test.waitForIdle()
        assertNotNull(position)
    }
}

@OptIn(ExperimentalTestApi::class)
internal fun ComposeUiTest.dropdownOffsetTracksLiveLtrAndRtlInputs() {
    val fixture = MenuFixture(this)
    fixture.mount()
    fixture.ready()
    val ltr = runOnIdle { assertNotNull(fixture.position) }
    runOnIdle { fixture.offset = DpOffset(12.dp, 8.dp) }
    fixture.ready()
    val shifted = runOnIdle { assertNotNull(fixture.position) }
    assertEquals(with(density) { 12.dp.roundToPx().toFloat() }, shifted.x - ltr.x, .5f)
    assertEquals(with(density) { 8.dp.roundToPx().toFloat() }, shifted.y - ltr.y, .5f)
    runOnIdle { fixture.direction = LayoutDirection.Rtl; fixture.offset = DpOffset.Zero }
    fixture.ready()
    val rtl = runOnIdle { assertNotNull(fixture.position) }
    runOnIdle { fixture.offset = DpOffset(12.dp, 8.dp) }
    fixture.ready()
    val rtlShifted = runOnIdle { assertNotNull(fixture.position) }
    assertEquals(-with(density) { 12.dp.roundToPx().toFloat() }, rtlShifted.x - rtl.x, .5f)
    assertEquals(with(density) { 8.dp.roundToPx().toFloat() }, rtlShifted.y - rtl.y, .5f)
}

@OptIn(ExperimentalTestApi::class)
internal suspend fun ComposeUiTest.dropdownCallerScrollControlsActualLongContents() {
    val fixture = MenuFixture(this).apply { long = true }
    fixture.mount()
    fixture.ready()
    val end = runOnIdle { fixture.scroll.maxValue }
    assertTrue(end > 0, "The actual popup must constrain, not expand, the long list")
    fixture.scroll.scrollTo(end)
    onNodeWithTag("dropdown-item-99").assertIsDisplayed()
    assertEquals(end, runOnIdle { fixture.scroll.value })
    fixture.scroll.scrollTo(0)
    onNodeWithTag("dropdown-item-0").assertIsDisplayed()
}

@OptIn(ExperimentalTestApi::class)
internal fun ComposeUiTest.dropdownStylePixelsMatchTheIndependentMaterialCall() {
    val fixture = MenuFixture(this)
    fixture.mount()
    fixture.ready()
    val actual = captureDropdown(runOnIdle { assertNotNull(fixture.position) }).toPixelMap()
    runOnIdle { fixture.reference = true }
    fixture.ready()
    val expected = captureDropdown(runOnIdle { assertNotNull(fixture.position) }).toPixelMap()
    assertEquals(expected.width, actual.width)
    assertEquals(expected.height, actual.height)
    assertTrue(actual.width > 0 && actual.height > 0)
    var matchedContainer = 0
    var matchedBorder = 0
    var differences = 0
    for (y in 0 until actual.height) for (x in 0 until actual.width) {
        if (actual[x, y] != expected[x, y]) differences++
        if (expected[x, y].toArgb() == fixture.expectedSurfaceArgb) matchedContainer++
        if (expected[x, y].toArgb() == Color(0xFFD132B4).toArgb()) matchedBorder++
    }
    assertTrue(matchedContainer > 100, "This must really capture the custom surface")
    assertTrue(matchedBorder > 10, "This must really capture the nondefault border")
    assertEquals(0, differences, "Shape/color/elevations/border must render like the same actual Material call")
    runOnIdle { fixture.reference = false; fixture.styled = false }
    fixture.ready()
    val changed = captureDropdown(runOnIdle { assertNotNull(fixture.position) }).toPixelMap()
    assertEquals(actual.width, changed.width)
    assertEquals(actual.height, changed.height)
    var changedPixels = 0
    for (y in 0 until actual.height) for (x in 0 until actual.width) {
        if (actual[x, y] != changed[x, y]) changedPixels++
    }
    assertTrue(changedPixels > 100, "A live caller style change must change the actual raster")
}

@OptIn(ExperimentalTestApi::class)
internal fun ComposeUiTest.dropdownFocusBackAndOutsidePoliciesControlRealEvents() {
    val fixture = MenuFixture(this).apply {
        properties = PopupProperties(focusable = false, dismissOnBackPress = true, dismissOnClickOutside = false)
    }
    fixture.mount()
    fixture.ready()
    dropdownBack(fixture.backInput)
    fixture.ready()
    assertEquals(0, runOnIdle { fixture.dismissals }, "A nonfocusable popup cannot consume the back key")
    runOnIdle { fixture.properties = PopupProperties(focusable = true, dismissOnBackPress = false, dismissOnClickOutside = false) }
    fixture.ready()
    dropdownBack(fixture.backInput)
    dropdownOutside()
    fixture.ready()
    assertEquals(0, runOnIdle { fixture.dismissals }, "Caller-disabled dismissal cannot invoke the callback")
    runOnIdle { fixture.properties = PopupProperties(focusable = true, dismissOnBackPress = true, dismissOnClickOutside = false) }
    fixture.ready()
    dropdownBack(fixture.backInput)
    onAllNodesWithTag("dropdown-menu").assertCountEquals(0)
    assertEquals(1, runOnIdle { fixture.dismissals })
    runOnIdle {
        fixture.properties = PopupProperties(focusable = true, dismissOnBackPress = false, dismissOnClickOutside = true)
        fixture.expanded = true
    }
    fixture.ready()
    dropdownOutside()
    onAllNodesWithTag("dropdown-menu").assertCountEquals(0)
    assertEquals(2, runOnIdle { fixture.dismissals }, "One outside click must deliver one dismissal")
}
