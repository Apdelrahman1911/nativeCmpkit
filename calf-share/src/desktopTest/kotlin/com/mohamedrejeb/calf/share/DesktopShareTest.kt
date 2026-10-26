@file:OptIn(com.mohamedrejeb.calf.core.ExperimentalCalfApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.share

import com.mohamedrejeb.calf.io.KmpFile
import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import java.io.File
import kotlin.test.*

class DesktopShareTest {
    @Test fun fileFallbackNeverInvokesAClipboardOrOsOpenHandler() {
        var copies = 0
        val file = KmpFile(File("untrusted-launcher.desktop"))
        assertIs<ShareOutcome.Unavailable>(safeDesktopShareFallback(ShareContent.File(file, "application/octet-stream"), true) { copies++ })
        assertIs<ShareOutcome.Unavailable>(safeDesktopShareFallback(ShareContent.Files(listOf(file), "application/octet-stream"), true) { copies++ })
        assertEquals(0, copies)
    }

    @Test fun urlFallbackOnlyCopiesTheLiteralTextWhenAllowed() {
        val copied = mutableListOf<String>()
        val content = ShareContent.Url("custom-app-scheme:payload", "subject")
        assertIs<ShareOutcome.Unavailable>(safeDesktopShareFallback(content, false) { copied += it })
        assertTrue(copied.isEmpty())
        assertEquals(ShareOutcome.CopiedToClipboard, safeDesktopShareFallback(content, true) { copied += it })
        assertEquals(listOf(content.url), copied)
    }

    @Test fun clipboardFailureIsNotSuccessfulOrRetried() {
        var calls = 0
        val result = safeDesktopShareFallback(ShareContent.Text("text"), true) { calls++; error("clipboard denied") }
        assertIs<ShareOutcome.Failed>(result)
        assertEquals(1, calls)
    }

    @Test fun launcherSnapshotsActualFileListBeforeCallerMutation() {
        val first = KmpFile(File("first.txt"))
        val second = KmpFile(File("second.txt"))
        val source = mutableListOf(first)
        var launched: ShareContent? = null
        val launcher = ShareLauncher { launched = it }
        launcher.launch(ShareContent.Files(source, "text/plain", "subject"))
        source.clear()
        source += second
        val captured = assertIs<ShareContent.Files>(launched)
        assertEquals(listOf(first), captured.files)
        assertEquals("subject", captured.subject)
        assertEquals("text/plain", captured.mimeType)
    }

    @Test fun mimeInjectionIsRejectedForActualFilePayloads() {
        val file = KmpFile(File("first.txt"))
        assertIs<ShareOutcome.Failed>(ShareContent.File(file, "text/plain\r\nInjected: true").validationFailure())
        assertIs<ShareOutcome.Failed>(ShareContent.Files(listOf(file), "\n").validationFailure())
        assertNull(ShareContent.File(file, "text/plain").validationFailure())
    }

    @Test fun throwingResultCallbackIsDeliveredOnceAndDoesNotPoisonTheGate() = runTest {
        val failures = mutableListOf<Throwable>()
        val scope = CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler) + CoroutineExceptionHandler { _, error -> failures += error })
        var callbacks = 0
        val expected = IllegalStateException("application result callback")
        val owner = DesktopShareOwner(scope, { ShareOptions() }, { callbacks++; throw expected }, { _, _ -> ShareOutcome.Completed })
        try {
            owner.launch(ShareContent.Text("one"))
            runCurrent()
            assertEquals(1, callbacks)
            assertEquals<List<Throwable>>(listOf(expected), failures)
            owner.launch(ShareContent.Text("two"))
            runCurrent()
            assertEquals(2, callbacks)
            assertEquals<List<Throwable>>(listOf(expected, expected), failures)
        } finally { scope.cancel() }
    }

    @Test fun cancellationCleansTheOperationWithoutLateResultDelivery() = runTest {
        val scope = CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler))
        var cleaned = false
        val results = mutableListOf<ShareOutcome>()
        val owner = DesktopShareOwner(scope, { ShareOptions() }, { results += it }, { _, _ ->
            try { awaitCancellation() } finally { cleaned = true }
        })
        owner.launch(ShareContent.Text("pending"))
        runCurrent()
        scope.cancel()
        runCurrent()
        assertTrue(cleaned)
        assertTrue(results.isEmpty())
        owner.launch(ShareContent.Text("disposed"))
        runCurrent()
        assertTrue(results.isEmpty())
    }

    @Test fun busyRejectionDoesNotCancelOrCompleteTheOriginalRequest() = runTest {
        val scope = CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler))
        val pending = CompletableDeferred<ShareOutcome>()
        val results = mutableListOf<ShareOutcome>()
        val owner = DesktopShareOwner(scope, { ShareOptions() }, { results += it }, { _, _ -> pending.await() })
        try {
            owner.launch(ShareContent.Text("one"))
            runCurrent()
            owner.launch(ShareContent.Text("two"))
            runCurrent()
            assertEquals<List<ShareOutcome>>(listOf(ShareOutcome.Busy), results)
            pending.complete(ShareOutcome.Completed)
            runCurrent()
            assertEquals<List<ShareOutcome>>(listOf(ShareOutcome.Busy, ShareOutcome.Completed), results)
        } finally { scope.cancel() }
    }
}
