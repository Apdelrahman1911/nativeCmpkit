// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.ui.test.ExperimentalTestApi::class)

package com.mohamedrejeb.calf.ui.utils

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asSkiaBitmap
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.onNodeWithTag
import com.mohamedrejeb.calf.ui.internal.onApplicationMain
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob

/** Wrong/spawned/non-application hosts fail rather than silently replacing native coverage. */
internal fun requireUiDragShaderApplication() {
    onApplicationMain { requireOwnedApplicationWindow(); Unit }
}

/** Real composition dispatcher/frame clock, but a caller-owned Job unaffected by node removal.
 * Every owning test MUST cancel this independent Job in finally.
 */
@Composable
internal fun rememberCallerOwnedAnimationScope(): CoroutineScope {
    val composition = rememberCoroutineScope()
    return remember(composition) {
        CoroutineScope(composition.coroutineContext.minusKey(Job) + SupervisorJob())
    }
}

internal fun ownedDescendants(owner: Job): List<Job> = owner.children.toList().flatMap { child ->
    listOf(child) + ownedDescendants(child)
}

/** Close only this freshly created test screenshot, not any persistent caller/Compose bitmap. */
internal fun ComposeUiTest.captureOwnedCenterColor(tag: String): Color {
    val screenshot = onNodeWithTag(tag).captureToImage()
    try {
        val pixels = screenshot.toPixelMap()
        return pixels[pixels.width / 2, pixels.height / 2]
    } finally {
        screenshot.asSkiaBitmap().close()
    }
}

/** Try every test-owned close/cancel, retaining both assertion and cleanup failures. */
internal fun closeOwnedUiDragShaderResources(primary: Throwable?, vararg actions: () -> Unit) {
    var cleanup: Throwable? = null
    for (action in actions) {
        try { action() } catch (error: Throwable) {
            val previous = cleanup
            if (previous == null) cleanup = error else if (previous !== error) previous.addSuppressed(error)
        }
    }
    cleanup?.let { error ->
        if (primary == null) throw error else if (primary !== error) primary.addSuppressed(error)
    }
}
