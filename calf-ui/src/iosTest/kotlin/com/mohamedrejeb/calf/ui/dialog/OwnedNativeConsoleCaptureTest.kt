// SPDX-License-Identifier: Apache-2.0
// Modified for NativeCmpKit (2026-11-01): actual FD/capture failure controls, no password emission.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.dialog

import kotlinx.cinterop.alloc
import kotlinx.cinterop.memScoped
import kotlinx.cinterop.ptr
import platform.posix.FD_CLOEXEC
import platform.posix.F_GETFD
import platform.posix.F_SETFD
import platform.posix.fcntl
import platform.posix.fileno
import platform.posix.fputs
import platform.posix.fstat
import platform.posix.stat
import platform.posix.stderr as nativeStderr
import platform.posix.stdout as nativeStdout
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class OwnedNativeConsoleCaptureTest {
    @Test fun bothRealSinksCapturePublicControlsAndRestoreOriginalDescriptorIdentity() {
        val before = originalConsoleIdentity()
        val control = "public-native-console-capture-control\n" // Public non-password test calibration only.
        val capture = captureOwnedNativeConsole {
            check(fputs(control, nativeStdout) >= 0)
            check(fputs(control, nativeStderr) >= 0)
        }
        capture.result.getOrThrow()
        assertTrue(capture.stdoutBytes.containsExactBytes(control.encodeToByteArray()), "Real stdout positive control was not captured")
        assertTrue(capture.stderrBytes.containsExactBytes(control.encodeToByteArray()), "Real stderr positive control was not captured")
        assertTrue(before == originalConsoleIdentity(), "Both original native sink identities must restore")
        assertTrue(!capture.stdoutBytes.containsExactBytes("public-absent-control".encodeToByteArray()))
        assertTrue(!capture.stderrBytes.containsExactBytes("public-absent-control".encodeToByteArray()))
    }

    @Test fun throwingBodyPreservesExactThrowableAndRestoresBothOriginalDescriptors() {
        val before = originalConsoleIdentity()
        val primary = IllegalStateException("Public deliberate capture-body refusal")
        val capture = captureOwnedNativeConsole<Unit> {
            check(fputs("public-before-capture-failure\n", nativeStdout) >= 0)
            check(fputs("public-before-capture-failure\n", nativeStderr) >= 0)
            throw primary
        }
        assertTrue(capture.result.exceptionOrNull() === primary, "Capture must preserve the actual body exception object")
        assertTrue(capture.stdoutBytes.isNotEmpty() && capture.stderrBytes.isNotEmpty())
        assertTrue(before == originalConsoleIdentity(), "A throwing body must restore both original sink identities")
    }

    @Test fun nestedAndOversizeCapturesRefuseBeforeNoLogAcceptanceAndRestoreOriginalSinks() {
        val before = originalConsoleIdentity()
        val nested = captureOwnedNativeConsole {
            assertFailsWith<IllegalStateException> { captureOwnedNativeConsole { } }
        }
        nested.result.getOrThrow()
        assertTrue(before == originalConsoleIdentity(), "Nested refusal must not replace an original sink")
        assertFailsWith<IllegalStateException> {
            captureOwnedNativeConsole(maxBytes = 256) {
                check(fputs("x".repeat(257), nativeStdout) >= 0)
            }
        }
        assertTrue(before == originalConsoleIdentity(), "Oversized capture must restore both original sinks, not truncate to pass")
        val fresh = captureOwnedNativeConsole { } // The failed attempt cannot retain the global capture lease.
        fresh.result.getOrThrow()
        assertTrue(before == originalConsoleIdentity())
    }

    @Test fun inheritedCloseOnExecFlagsRestoreForBothRealDescriptors() {
        withInheritedCloseOnExec {
            val inherited = originalConsoleIdentity()
            assertTrue(inherited.all { (it.last().toInt() and FD_CLOEXEC) == FD_CLOEXEC }, "Both inherited descriptors must deliberately have FD_CLOEXEC=1")
            val control = "public-cloexec-native-console-control\n"
            val capture = captureOwnedNativeConsole {
                check(fputs(control, nativeStdout) >= 0)
                check(fputs(control, nativeStderr) >= 0)
            }
            capture.result.getOrThrow()
            assertTrue(capture.stdoutBytes.containsExactBytes(control.encodeToByteArray()))
            assertTrue(capture.stderrBytes.containsExactBytes(control.encodeToByteArray()))
            assertEquals(inherited, originalConsoleIdentity(), "dup2 restoration must also restore both inherited FD_CLOEXEC flags")
        }
    }

    @Test fun stderrOversizeRefusesWithoutTruncationAndRestoresBothOriginalSinks() {
        val before = originalConsoleIdentity()
        val failure = assertFailsWith<IllegalStateException> {
            captureOwnedNativeConsole(maxBytes = 256) {
                check(fputs("s".repeat(257), nativeStderr) >= 0)
            }
        }
        assertEquals("Unbounded captured output is not a successful no-input-log result", failure.message)
        assertEquals(before, originalConsoleIdentity(), "stderr overflow cannot accept truncated absence or retain a descriptor")
        assertFreshLeaseAndIdentity(before)
    }

    @Test fun controlledShortReadsRefuseAndStillCloseEveryOwnedSink() {
        // The real fread succeeds; the one-byte-short reported result is the
        // controlled refusal. It is not evidence of an actual kernel short read.
        for (read in listOf(OwnedNativeConsoleStage.STDOUT_READ, OwnedNativeConsoleStage.STDERR_READ)) {
            val before = originalConsoleIdentity()
            val control = OwnedNativeConsoleFailureControl(read)
            val failure = assertFailsWith<IllegalStateException> {
                captureOwnedNativeConsoleForControl(control) { writeBothPublicControls() }
            }
            assertEquals("A short captured-output read cannot prove input absence", failure.message)
            assertFullControlledCleanup(control)
            assertEquals(before, originalConsoleIdentity())
            assertFreshLeaseAndIdentity(before)
        }
    }

    @Test fun controlledPartialAcquisitionsRefuseBeforeActionAndReleaseEveryAcquiredHandle() {
        val stages = listOf(
            OwnedNativeConsoleStage.STDERR_FILE_ACQUIRE,
            OwnedNativeConsoleStage.STDOUT_BACKUP_ACQUIRE,
            OwnedNativeConsoleStage.STDERR_BACKUP_ACQUIRE,
        )
        val expectedMessages = listOf(
            "Owned native stderr capture is unavailable",
            "The original native stdout descriptor could not be retained",
            "The original native stderr descriptor could not be retained",
        )
        val expectedSuccessfulStages = listOf(
            listOf(OwnedNativeConsoleStage.STDOUT_FILE_ACQUIRE,
                OwnedNativeConsoleStage.STDOUT_FILE_CLOSE, OwnedNativeConsoleStage.LEASE_RELEASE),
            listOf(OwnedNativeConsoleStage.STDOUT_FILE_ACQUIRE, OwnedNativeConsoleStage.STDERR_FILE_ACQUIRE,
                OwnedNativeConsoleStage.STDOUT_FILE_CLOSE, OwnedNativeConsoleStage.STDERR_FILE_CLOSE,
                OwnedNativeConsoleStage.LEASE_RELEASE),
            listOf(OwnedNativeConsoleStage.STDOUT_FILE_ACQUIRE, OwnedNativeConsoleStage.STDERR_FILE_ACQUIRE,
                OwnedNativeConsoleStage.STDOUT_BACKUP_ACQUIRE, OwnedNativeConsoleStage.STDOUT_FLAGS,
                OwnedNativeConsoleStage.STDOUT_BACKUP_CLOSE, OwnedNativeConsoleStage.STDOUT_FILE_CLOSE,
                OwnedNativeConsoleStage.STDERR_FILE_CLOSE, OwnedNativeConsoleStage.LEASE_RELEASE),
        )
        for (index in stages.indices) {
            val before = originalConsoleIdentity()
            val control = OwnedNativeConsoleFailureControl(stages[index])
            var actionEntered = false
            val failure = assertFailsWith<IllegalStateException> {
                captureOwnedNativeConsoleForControl(control) { actionEntered = true }
            }
            assertEquals(expectedMessages[index], failure.message)
            assertTrue(!actionEntered, "A refused partial acquisition must not run the capture action")
            assertEquals(1, control.refusalCount)
            assertEquals(expectedSuccessfulStages[index], control.successfulStages,
                "Every acquired handle must close independently without a fabricated acquire or redirect")
            assertEquals(before, originalConsoleIdentity())
            assertFreshLeaseAndIdentity(before)
        }
    }

    @Test fun controlledRestoreFlagAndCloseRefusalsStillAttemptAllOtherOwnedCleanup() {
        // Each refusal is AFTER the corresponding successful real operation.
        // No claim follows that an unsuccessful real syscall restored or closed.
        val faults = listOf(
            OwnedNativeConsoleStage.STDOUT_RESTORE, OwnedNativeConsoleStage.STDERR_RESTORE,
            OwnedNativeConsoleStage.STDOUT_FLAGS, OwnedNativeConsoleStage.STDERR_FLAGS,
            OwnedNativeConsoleStage.STDOUT_BACKUP_CLOSE, OwnedNativeConsoleStage.STDERR_BACKUP_CLOSE,
            OwnedNativeConsoleStage.STDOUT_FILE_CLOSE, OwnedNativeConsoleStage.STDERR_FILE_CLOSE,
        )
        for (fault in faults) {
            val before = originalConsoleIdentity()
            val control = OwnedNativeConsoleFailureControl(fault)
            val failure = assertFailsWith<IllegalStateException> {
                captureOwnedNativeConsoleForControl(control) { writeBothPublicControls() }
            }
            assertTrue(failure === control.cleanupRefusal, "Cleanup refusal must stay a failure, not successful no-log bytes")
            assertFullControlledCleanup(control)
            assertEquals(before, originalConsoleIdentity())
            assertFreshLeaseAndIdentity(before)
        }
    }

    @Test fun bodyAndControlledCleanupFailurePreserveExactThrowableAndSuppressedRefusal() {
        val before = originalConsoleIdentity()
        val primary = IllegalStateException("Public controlled capture body-and-cleanup refusal")
        val control = OwnedNativeConsoleFailureControl(OwnedNativeConsoleStage.STDERR_BACKUP_CLOSE)
        val failure = assertFailsWith<IllegalStateException> {
            captureOwnedNativeConsoleForControl<Unit>(control) {
                writeBothPublicControls()
                throw primary
            }
        }
        assertTrue(failure === primary, "The original body Throwable object must remain the primary failure")
        assertEquals(1, primary.suppressedExceptions.size, "Exactly the deliberate cleanup refusal must be suppressed")
        assertTrue(primary.suppressedExceptions.single() === control.cleanupRefusal,
            "Cleanup suppression must retain the exact original controlled Throwable object")
        assertFullControlledCleanup(control)
        assertEquals(before, originalConsoleIdentity())
        assertFreshLeaseAndIdentity(before)
    }

    private fun writeBothPublicControls() {
        // Public positive calibration only; synthetic passwords are never printed.
        check(fputs("public-controlled-native-console-sink\n", nativeStdout) >= 0)
        check(fputs("public-controlled-native-console-sink\n", nativeStderr) >= 0)
    }

    private fun assertFullControlledCleanup(control: OwnedNativeConsoleFailureControl) {
        assertEquals(1, control.refusalCount, "Exactly one fixed refusal must execute")
        assertEquals(OwnedNativeConsoleStage.entries.toList(), control.successfulStages,
            "Every actual acquired/redirect/restore/flag/read/close stage and final lease release must execute exactly once")
    }

    private fun assertFreshLeaseAndIdentity(before: List<List<ULong>>) {
        val fresh = captureOwnedNativeConsole { }
        fresh.result.getOrThrow()
        assertEquals(before, originalConsoleIdentity(), "A refused controlled capture must not retain the global lease or original descriptors")
    }

    private fun withInheritedCloseOnExec(action: () -> Unit) {
        val before = originalConsoleIdentity()
        val descriptors = before.map { it.first().toInt() }
        val flags = before.map { it.last().toInt() }
        var failure: Throwable? = null
        fun failed(error: Throwable) {
            val previous = failure
            if (previous == null) failure = error else if (previous !== error) previous.addSuppressed(error)
        }
        try {
            for (index in descriptors.indices) {
                val requiredFlags = flags[index] or FD_CLOEXEC
                check(fcntl(descriptors[index], F_SETFD, requiredFlags) == 0 &&
                    fcntl(descriptors[index], F_GETFD, 0) == requiredFlags) {
                    "Both inherited close-on-exec flags must actually be set before capture"
                }
            }
            action()
        } catch (error: Throwable) {
            failed(error)
        } finally {
            // Independent best-effort restoration; never let one flags failure
            // skip the other original descriptor or hide an existing primary.
            for (index in descriptors.indices) {
                try {
                    check(fcntl(descriptors[index], F_SETFD, flags[index]) == 0 &&
                        fcntl(descriptors[index], F_GETFD, 0) == flags[index]) {
                        "The inherited-flags control could not restore its original flags"
                    }
                } catch (error: Throwable) { failed(error) }
            }
            try { assertEquals(before, originalConsoleIdentity()) } catch (error: Throwable) { failed(error) }
        }
        failure?.let { throw it }
    }

    private fun originalConsoleIdentity(): List<List<ULong>> = memScoped {
        listOf(fileno(nativeStdout), fileno(nativeStderr)).map { descriptor ->
            val value = alloc<stat>()
            check(fstat(descriptor, value.ptr) == 0) { "Original native console descriptor cannot be observed" }
            val flags = fcntl(descriptor, F_GETFD, 0)
            check(flags >= 0) { "Original native console descriptor flags cannot be observed" }
            listOf(descriptor.toULong(), value.st_dev.toULong(), value.st_ino.toULong(), value.st_mode.toULong(), flags.toULong())
        }
    }
}
