// Modified for NativeCmpKit (2026-10-29): actual composition/scope disposal regression.
@file:OptIn(androidx.compose.ui.test.ExperimentalTestApi::class)
package com.mohamedrejeb.calf.sample.utils

import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Job
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Uses the exact owner remembered by FilePickerScreen on the real desktop Compose runtime. */
class SampleStreamingCompositionTest {
    @Test fun navigatingAwayCancelsTheRememberedOwnerAndOldCompletionCannotPublishOrRestart() = runComposeUiTest {
        val visible = mutableStateOf(true)
        var owner: SampleStreamingOwner? = null
        var started = false
        var cleaned = false
        var publications = 0
        lateinit var active: Job
        val delayed = CompletableDeferred<String>()
        setContent {
            if (visible.value) {
                val current = rememberSampleStreamingOwner()
                SideEffect { owner = current }
            }
        }
        runOnIdle {
            active = owner!!.replace(listOf(Unit), {
                started = true
                try { delayed.await() } finally { cleaned = true }
            }, { publications++ })
        }
        waitUntil(timeoutMillis = 5_000) { started }
        runOnIdle { visible.value = false }
        waitForIdle()
        waitUntil(timeoutMillis = 5_000) { cleaned && active.isCancelled }
        assertEquals(0, publications)
        delayed.complete("obsolete completion")
        waitForIdle()
        runOnIdle {
            val afterDisposal = owner!!.replace(listOf(Unit), { "not reachable" }, { publications++ })
            assertTrue(afterDisposal.isCancelled)
        }
        waitForIdle()
        assertEquals(0, publications)
    }
}
