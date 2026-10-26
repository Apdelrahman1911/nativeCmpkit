package com.mohamedrejeb.calf.picker.platform

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class DialogHandleOwnerTest {
    @Test fun showFailureStillClosesExactlyOnce() {
        var closes = 0
        assertFailsWith<IllegalStateException> {
            withDialogHandle({ 7 }, { assertEquals(7L, it); closes++ }) { error("show failed") }
        }
        assertEquals(1, closes)
    }
    @Test fun aCancelledWorkerResultCannotLeakTheHandle() = runTest {
        var closes = 0
        val job = Job()
        assertFailsWith<CancellationException> {
            withContext(Dispatchers.Default + job) {
                withDialogHandle({ 8 }, { closes++ }) {
                    currentCoroutineContext().cancel()
                    "result lost at dispatch boundary"
                }
            }
        }
        assertEquals(1, closes)
    }
    @Test fun zeroHandleIsRejectedWithoutDestroyingAnArbitraryPointer() {
        var closes = 0
        assertFailsWith<IllegalStateException> { withDialogHandle({ 0 }, { closes++ }) { "invalid" } }
        assertEquals(0, closes)
    }
}
