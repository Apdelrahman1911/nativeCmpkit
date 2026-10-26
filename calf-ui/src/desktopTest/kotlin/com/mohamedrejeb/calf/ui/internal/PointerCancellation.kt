package com.mohamedrejeb.calf.ui.internal

import androidx.compose.ui.InternalComposeUiApi
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.SkikoComposeUiTest

/**
 * ui-test 1.12.2's Skiko TouchInjectionScope.cancel() only clears injector bookkeeping: its
 * enqueueCancel implementation delivers no event. Send the real scene cancellation as well.
 * This is the same production scene API called by iOS ComposeSceneMediator.onCancelAllTouches,
 * not a fake interaction or a forced call into the slider's callbacks.
 */
@OptIn(ExperimentalTestApi::class, InternalComposeUiApi::class)
internal fun ComposeUiTest.cancelScenePointerInput() {
    runOnIdle { (this as SkikoComposeUiTest).scene.cancelPointerInput() }
}
