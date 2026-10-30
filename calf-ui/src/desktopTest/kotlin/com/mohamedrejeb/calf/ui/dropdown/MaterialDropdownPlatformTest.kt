// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.dropdown

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.isSpecified
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.layout.LayoutCoordinates
import androidx.compose.ui.test.*
import kotlin.test.*

internal actual fun dropdownPosition(coordinates: LayoutCoordinates): Offset =
    coordinates.localToWindow(Offset.Zero).also { assertTrue(it.isSpecified) }

@OptIn(ExperimentalTestApi::class)
internal actual fun ComposeUiTest.captureDropdown(position: Offset): ImageBitmap =
    onNodeWithTag("dropdown-underlay").captureToImage()

@OptIn(ExperimentalTestApi::class)
internal actual fun ComposeUiTest.dropdownBack(input: DropdownBackInput) {
    runOnIdle { input.completeBack() }
    waitForIdle()
}

@OptIn(ExperimentalTestApi::class)
internal actual fun ComposeUiTest.dropdownOutside() {
    onNodeWithTag("dropdown-underlay").performTouchInput { click(Offset(5f, 5f)) }
    waitForIdle()
}
