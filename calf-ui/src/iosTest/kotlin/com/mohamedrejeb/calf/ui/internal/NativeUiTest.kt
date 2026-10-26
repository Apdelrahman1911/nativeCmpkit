package com.mohamedrejeb.calf.ui.internal

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.v2.runComposeUiTest
import platform.Foundation.NSThread
import platform.UIKit.UIDatePicker
import platform.UIKit.UIView
import kotlin.test.assertTrue

/** Runs real UIKit objects on the UI-test application's main thread; no UIKit stand-ins. */
@OptIn(ExperimentalTestApi::class)
internal fun runNativeUiTest(block: () -> Unit) = runComposeUiTest {
    setContent { }
    runOnIdle {
        assertTrue(NSThread.isMainThread)
        block()
    }
}

internal fun UIView.datePickers(): List<UIDatePicker> =
    if (this is UIDatePicker) listOf(this) else subviews.filterIsInstance<UIView>().flatMap { it.datePickers() }

@OptIn(ExperimentalTestApi::class)
internal fun androidx.compose.ui.test.ComposeUiTest.waitForNative(predicate: () -> Boolean) {
    waitUntil(timeoutMillis = 10_000) {
        var satisfied = false
        runOnIdle { satisfied = predicate() }
        satisfied
    }
}
