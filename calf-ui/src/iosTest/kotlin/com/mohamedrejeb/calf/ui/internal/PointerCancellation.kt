package com.mohamedrejeb.calf.ui.internal

import androidx.compose.ui.InternalComposeUiApi
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.SkikoComposeUiTest

/**
 * ui-test 1.12.2 shares Skiko's no-op enqueueCancel on iOS too. After resetting the injector with
 * TouchInjectionScope.cancel(), call the actual scene API used by ComposeSceneMediator for native
 * touch cancellation. This still needs separate physical UIKit delivery/interoperability tests.
 */
@OptIn(ExperimentalTestApi::class, InternalComposeUiApi::class)
internal fun ComposeUiTest.cancelScenePointerInput() {
    runOnIdle { (this as SkikoComposeUiTest).scene.cancelPointerInput() }
}
