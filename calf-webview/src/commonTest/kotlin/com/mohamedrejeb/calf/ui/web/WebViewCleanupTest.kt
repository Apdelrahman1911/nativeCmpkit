package com.mohamedrejeb.calf.ui.web

import kotlin.test.*

class WebViewCleanupTest {
    @Test fun primaryFailureSurvivesAndEveryReleaseStageRuns() {
        val primary = IllegalStateException("creation")
        val cleanupFailure = IllegalArgumentException("stop")
        val calls = mutableListOf<Int>()
        val result = assertFailsWith<IllegalStateException> {
            runWebViewCleanup(primary,
                { calls += 1; throw cleanupFailure },
                { calls += 2 },
                { calls += 3 },
            )
        }
        assertSame(primary, result)
        assertEquals(listOf(cleanupFailure), result.suppressedExceptions)
        assertEquals(listOf(1, 2, 3), calls)
    }

    @Test fun firstCleanupFailureIsPreservedAndLaterFailuresAreSuppressed() {
        val first = IllegalStateException("callback")
        val second = IllegalArgumentException("destroy")
        var cleared = false
        val result = assertFailsWith<IllegalStateException> {
            runWebViewCleanup(null, { throw first }, { throw second }, { cleared = true })
        }
        assertSame(first, result)
        assertEquals(listOf(second), result.suppressedExceptions)
        assertTrue(cleared)
    }

    @Test fun repeatingTheSameThrowableNeverSelfSuppressesOrSkipsFinalCleanup() {
        val failure = IllegalStateException("same failure")
        var cleared = false
        val result = assertFailsWith<IllegalStateException> {
            runWebViewCleanup(failure, { throw failure }, { cleared = true })
        }
        assertSame(failure, result)
        assertTrue(result.suppressedExceptions.isEmpty())
        assertTrue(cleared)
    }
}
