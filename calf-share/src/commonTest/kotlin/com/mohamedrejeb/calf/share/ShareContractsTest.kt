@file:OptIn(com.mohamedrejeb.calf.core.ExperimentalCalfApi::class)

package com.mohamedrejeb.calf.share

import com.mohamedrejeb.calf.io.KmpFile
import kotlin.test.*

class ShareContractsTest {
    @Test fun anOverlappingLaunchCannotReplaceItsActiveRequest() {
        val gate = ShareRequestGate()
        val first = assertNotNull(gate.begin())
        assertNull(gate.begin())
        assertTrue(gate.finish(first))
        assertNotNull(gate.begin())
    }

    @Test fun oldAndDuplicateResultsCannotReleaseANewOwner() {
        val gate = ShareRequestGate()
        val first = assertNotNull(gate.begin())
        assertTrue(gate.finish(first))
        val second = assertNotNull(gate.begin())
        assertFalse(gate.finish(first))
        assertNull(gate.begin())
        assertTrue(gate.finish(second))
    }

    @Test fun abandonmentInvalidatesAnOutstandingCallbackToken() {
        val gate = ShareRequestGate()
        val old = assertNotNull(gate.begin())
        gate.abandon()
        val replacement = assertNotNull(gate.begin())
        assertFalse(gate.finish(old))
        assertTrue(gate.finish(replacement))
    }

    @Test fun oldResultSealedCasesRemainAnExplicitLossyAdapter() {
        listOf(ShareOutcome.Presented, ShareOutcome.Selected, ShareOutcome.Completed, ShareOutcome.CopiedToClipboard)
            .forEach { assertEquals(ShareResult.Success, it.toLegacyResult()) }
        assertEquals(ShareResult.Dismissed, ShareOutcome.Dismissed.toLegacyResult())
        listOf(ShareOutcome.Busy, ShareOutcome.Unavailable("test"), ShareOutcome.Failed(ShareFailureReason.Platform, "test"))
            .forEach { assertEquals(ShareResult.Unavailable, it.toLegacyResult()) }
    }

    @Test fun emptyFilesAndBlankUrlAreRejectedWithoutNativeLaunch() {
        assertEquals(ShareFailureReason.InvalidContent, ShareContent.Files(emptyList(), "image/png").validationFailure()?.reason)
        assertEquals(ShareFailureReason.InvalidContent, ShareContent.Url("  ").validationFailure()?.reason)
        assertNull(ShareContent.Text("", "subject").validationFailure())
    }

    @Test fun desktopDeadlineIsFiniteAndValidated() {
        assertFailsWith<IllegalArgumentException> { ShareOptions(desktopTimeoutMillis = 999) }
        assertFailsWith<IllegalArgumentException> { ShareOptions(desktopTimeoutMillis = 600_001) }
        assertEquals(1_000L, ShareOptions(desktopTimeoutMillis = 1_000).desktopTimeoutMillis)
        assertEquals(600_000L, ShareOptions(desktopTimeoutMillis = 600_000).desktopTimeoutMillis)
    }

    @Test fun snapshotDoesNotRetainAnApplicationMutableList() {
        val files = mutableListOf<KmpFile>()
        val original = ShareContent.Files(files, "image/png", "title")
        val copied = original.snapshot() as ShareContent.Files
        assertNotSame(files, copied.files)
        assertEquals(original, copied)
        assertEquals("title", copied.subject)
    }

    @Test fun launcherDoesNotCatchOrRepeatApplicationLaunchExceptions() {
        var calls = 0
        val expected = IllegalStateException("application onLaunch")
        val launcher = ShareLauncher { calls++; throw expected }
        assertSame(expected, assertFailsWith<IllegalStateException> { launcher.launch(ShareContent.Text("test")) })
        assertEquals(1, calls)
    }
}
