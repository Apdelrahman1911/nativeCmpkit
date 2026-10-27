package com.mohamedrejeb.calf.ui.internal

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.v2.runComposeUiTest
import platform.Foundation.NSThread
import platform.UIKit.UIDatePicker
import platform.UIKit.UIView
import kotlin.test.assertTrue

/**
 * Runs real UIKit objects on the Skiko test scene's main thread; no UIKit stand-ins.
 * Compose v2 does not itself host UIApplication/ComposeUIViewController. Native
 * presentation tests still require a genuine application host; see
 * docs/development/native-ui-application-host.md.
 */
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
