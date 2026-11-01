// SPDX-License-Identifier: Apache-2.0
// Modified for NativeCmpKit (2026-11-01): bounded serial console ownership and explicit safe failure controls.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.dialog

import kotlinx.cinterop.CPointer
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.convert
import kotlinx.cinterop.usePinned
import platform.Foundation.NSLock
import platform.posix.FILE
import platform.posix.F_GETFD
import platform.posix.F_SETFD
import platform.posix.SEEK_END
import platform.posix.SEEK_SET
import platform.posix.close
import platform.posix.dup
import platform.posix.dup2
import platform.posix.fclose
import platform.posix.fflush
import platform.posix.fcntl
import platform.posix.fileno
import platform.posix.fread
import platform.posix.fseek
import platform.posix.ftell
import platform.posix.stderr as nativeStderr
import platform.posix.stdout as nativeStdout
import platform.posix.tmpfile

/** Fixed single-process test lease, never a library logging API or a system-log capture. */
private val consoleCaptureLease = NSLock()
private const val MAX_CAPTURE_BYTES = 64 * 1024

/** No toString/output conversion of the captured bytes or the synthetic inputs. */
internal class CapturedNativeConsole<T>(
    val result: Result<T>,
    val stdoutBytes: ByteArray,
    val stderrBytes: ByteArray,
)

internal fun ByteArray.containsExactBytes(needle: ByteArray): Boolean {
    require(needle.isNotEmpty()) { "An empty log probe cannot verify input absence" }
    if (needle.size > size) return false
    for (start in 0..size - needle.size) {
        if (needle.indices.all { this[start + it] == needle[it] }) return true
    }
    return false
}

/** Public fixed stages only; never captured output or input values in a control receipt. */
internal enum class OwnedNativeConsoleStage {
    STDOUT_FILE_ACQUIRE, STDERR_FILE_ACQUIRE, STDOUT_BACKUP_ACQUIRE, STDERR_BACKUP_ACQUIRE,
    STDOUT_REDIRECT, STDERR_REDIRECT, STDOUT_RESTORE, STDERR_RESTORE,
    STDOUT_FLAGS, STDERR_FLAGS, STDOUT_READ, STDERR_READ,
    STDOUT_BACKUP_CLOSE, STDERR_BACKUP_CLOSE, STDOUT_FILE_CLOSE, STDERR_FILE_CLOSE,
    LEASE_RELEASE,
}

/**
 * One-use iosTest-only controlled refusal, never passed by the genuine input/no-log method.
 * Acquisition controls refuse BEFORE the selected syscall: no acquired fd/FILE is hidden.
 * Short-read controls report one fewer byte only AFTER a genuine successful full fread.
 * Cleanup controls throw AFTER a genuine successful restore/flags/close operation. This
 * exercises independent fail-closed cleanup and exception ownership WITHOUT sabotaging
 * original process descriptors. It does NOT prove recovery from a truly failed kernel
 * syscall, a foreign writer, another thread, a child process or an OS/unified-log sink.
 */
internal class OwnedNativeConsoleFailureControl(val refuseAt: OwnedNativeConsoleStage) {
    private val completed = mutableListOf<OwnedNativeConsoleStage>()
    private var started = false
    val successfulStages: List<OwnedNativeConsoleStage> get() = completed.toList()
    var refusalCount: Int = 0
        private set
    val cleanupRefusal = IllegalStateException("Public controlled native console cleanup refusal at ${refuseAt.name}")

    init {
        require(refuseAt in setOf(
            OwnedNativeConsoleStage.STDERR_FILE_ACQUIRE,
            OwnedNativeConsoleStage.STDOUT_BACKUP_ACQUIRE,
            OwnedNativeConsoleStage.STDERR_BACKUP_ACQUIRE,
            OwnedNativeConsoleStage.STDOUT_READ, OwnedNativeConsoleStage.STDERR_READ,
            OwnedNativeConsoleStage.STDOUT_RESTORE, OwnedNativeConsoleStage.STDERR_RESTORE,
            OwnedNativeConsoleStage.STDOUT_FLAGS, OwnedNativeConsoleStage.STDERR_FLAGS,
            OwnedNativeConsoleStage.STDOUT_BACKUP_CLOSE, OwnedNativeConsoleStage.STDERR_BACKUP_CLOSE,
            OwnedNativeConsoleStage.STDOUT_FILE_CLOSE, OwnedNativeConsoleStage.STDERR_FILE_CLOSE,
        )) { "Select only a fixed public controlled console failure stage" }
    }

    internal fun begin() {
        check(!started && completed.isEmpty() && refusalCount == 0) { "A controlled console refusal is one-use" }
        started = true
    }

    internal fun completed(stage: OwnedNativeConsoleStage) {
        check(started && completed.size < OwnedNativeConsoleStage.entries.size && stage !in completed) {
            "Controlled console receipts require finite unique actual successful stages"
        }
        completed.add(stage)
    }

    internal fun refuses(stage: OwnedNativeConsoleStage): Boolean {
        check(started) { "A controlled console refusal requires its owning capture" }
        if (stage != refuseAt || refusalCount != 0) return false
        refusalCount = 1
        return true
    }

    internal fun afterSuccessful(stage: OwnedNativeConsoleStage) {
        completed(stage)
        if (refuses(stage)) throw cleanupRefusal
    }
}

private fun capturedBytes(
    file: CPointer<FILE>,
    maxBytes: Int,
    readStage: OwnedNativeConsoleStage,
    failureControl: OwnedNativeConsoleFailureControl?,
): ByteArray {
    check(fflush(file) == 0) { "Owned native capture could not flush" }
    check(fseek(file, 0, SEEK_END) == 0) { "Owned native capture could not seek" }
    val length = ftell(file)
    check(length in 0..maxBytes.toLong()) { "Unbounded captured output is not a successful no-input-log result" }
    check(fseek(file, 0, SEEK_SET) == 0) { "Owned native capture could not rewind" }
    val bytes = ByteArray(length.toInt())
    if (bytes.isNotEmpty()) bytes.usePinned { pinned ->
        val actualRead = fread(pinned.addressOf(0), 1.convert(), bytes.size.convert(), file)
        val fullRealRead = actualRead == bytes.size.toULong()
        if (fullRealRead) failureControl?.completed(readStage)
        val reportedRead = if (fullRealRead && failureControl?.refuses(readStage) == true) actualRead - 1UL else actualRead
        check(reportedRead == bytes.size.toULong()) {
            "A short captured-output read cannot prove input absence"
        }
    }
    return bytes
}

/**
 * Capture just the current process's two original stdout/stderr descriptors.
 * Anonymous tmpfile handles avoid a blocking pipe; every acquired close/restore is independently attempted.
 * The lease is intended to refuse overlapping capture before descriptor mutation.
 * The retained nested control is same-thread only: no concurrent-thread coverage
 * is claimed. Run the generated native application test serially; this is not an
 * OS/unified-log hook. A real restore failure remains failure, not guaranteed
 * restoration. Successful restore stages precede exposing the action Result.
 */
internal fun <T> captureOwnedNativeConsole(
    maxBytes: Int = MAX_CAPTURE_BYTES,
    action: () -> T,
): CapturedNativeConsole<T> = captureOwnedNativeConsoleImpl(maxBytes, null, action)

/** Dedicated controlled-test entry: never a successful no-input-log acceptance seam. */
internal fun <T> captureOwnedNativeConsoleForControl(
    failureControl: OwnedNativeConsoleFailureControl,
    maxBytes: Int = MAX_CAPTURE_BYTES,
    action: () -> T,
): CapturedNativeConsole<T> = captureOwnedNativeConsoleImpl(maxBytes, failureControl, action)

private fun <T> captureOwnedNativeConsoleImpl(
    maxBytes: Int,
    failureControl: OwnedNativeConsoleFailureControl?,
    action: () -> T,
): CapturedNativeConsole<T> {
    require(maxBytes in 1..MAX_CAPTURE_BYTES) { "Use a bounded native console capture" }
    failureControl?.begin()
    var outputFile: CPointer<FILE>? = null
    var errorFile: CPointer<FILE>? = null
    var savedOutput = -1
    var savedError = -1
    var originalOutputFlags = -1
    var originalErrorFlags = -1
    var outputRedirected = false
    var errorRedirected = false
    var actionResult: Result<T>? = null
    var captureFailure: Throwable? = null
    var output = ByteArray(0)
    var errors = ByteArray(0)
    var outputDescriptor = -1
    var errorDescriptor = -1
    fun failed(error: Throwable) {
        val previous = captureFailure
        if (previous == null) captureFailure = error else if (previous !== error) previous.addSuppressed(error)
    }
    fun stage(block: () -> Unit) {
        try { block() } catch (error: Throwable) { failed(error) }
    }
    // Base bookkeeping/zero-byte allocations precede the lease. Optional finite
    // test receipts never acquire descriptors. Every native acquired handle and
    // all descriptor changes remain inside the owning finally.
    check(consoleCaptureLease.tryLock()) { "A native stdout/stderr capture is already active" }
    try {
        outputDescriptor = fileno(nativeStdout)
        errorDescriptor = fileno(nativeStderr)
        check(outputDescriptor >= 0 && errorDescriptor >= 0 && outputDescriptor != errorDescriptor) {
            "Expected two distinct original native console descriptors"
        }
        originalOutputFlags = fcntl(outputDescriptor, F_GETFD, 0)
        originalErrorFlags = fcntl(errorDescriptor, F_GETFD, 0)
        check(originalOutputFlags >= 0 && originalErrorFlags >= 0) {
            "Original native console descriptor flags could not be retained"
        }
        check(fflush(nativeStdout) == 0) { "Original native stdout could not flush" }
        check(fflush(nativeStderr) == 0) { "Original native stderr could not flush" }
        outputFile = checkNotNull(tmpfile()) { "Owned native stdout capture is unavailable" }
        failureControl?.completed(OwnedNativeConsoleStage.STDOUT_FILE_ACQUIRE)
        errorFile = checkNotNull(if (failureControl?.refuses(OwnedNativeConsoleStage.STDERR_FILE_ACQUIRE) == true) null else tmpfile()) {
            "Owned native stderr capture is unavailable"
        }
        failureControl?.completed(OwnedNativeConsoleStage.STDERR_FILE_ACQUIRE)
        savedOutput = if (failureControl?.refuses(OwnedNativeConsoleStage.STDOUT_BACKUP_ACQUIRE) == true) -1 else dup(outputDescriptor)
        check(savedOutput >= 0) { "The original native stdout descriptor could not be retained" }
        failureControl?.completed(OwnedNativeConsoleStage.STDOUT_BACKUP_ACQUIRE)
        savedError = if (failureControl?.refuses(OwnedNativeConsoleStage.STDERR_BACKUP_ACQUIRE) == true) -1 else dup(errorDescriptor)
        check(savedError >= 0) { "The original native stderr descriptor could not be retained" }
        failureControl?.completed(OwnedNativeConsoleStage.STDERR_BACKUP_ACQUIRE)
        check(dup2(fileno(checkNotNull(outputFile)), outputDescriptor) == outputDescriptor) {
            "Owned native stdout could not be redirected"
        }
        outputRedirected = true
        failureControl?.completed(OwnedNativeConsoleStage.STDOUT_REDIRECT)
        check(dup2(fileno(checkNotNull(errorFile)), errorDescriptor) == errorDescriptor) {
            "Owned native stderr could not be redirected"
        }
        errorRedirected = true
        failureControl?.completed(OwnedNativeConsoleStage.STDERR_REDIRECT)
        actionResult = runCatching(action)
    } catch (error: Throwable) {
        failed(error)
    } finally {
        // Independent stages: a failure on one sink cannot skip the other restore
        // or any acquired handle. Flush before restore so buffered test output is
        // not emitted afterwards into the original KGP transport.
        if (outputRedirected) stage {
            check(fflush(nativeStdout) == 0) { "Captured native stdout could not flush before restore" }
        }
        if (errorRedirected) stage {
            check(fflush(nativeStderr) == 0) { "Captured native stderr could not flush before restore" }
        }
        if (outputRedirected) stage {
            check(dup2(savedOutput, outputDescriptor) == outputDescriptor) { "The exact original native stdout did not restore" }
            outputRedirected = false
            failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDOUT_RESTORE)
        }
        if (errorRedirected) stage {
            check(dup2(savedError, errorDescriptor) == errorDescriptor) { "The exact original native stderr did not restore" }
            errorRedirected = false
            failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDERR_RESTORE)
        }
        // dup2 clears FD_CLOEXEC: file/inode equality alone is not an exact
        // descriptor restoration. Restore each original FD-specific flag too.
        if (!outputRedirected && savedOutput >= 0) stage {
            check(fcntl(outputDescriptor, F_SETFD, originalOutputFlags) == 0 &&
                fcntl(outputDescriptor, F_GETFD, 0) == originalOutputFlags) {
                "Original native stdout descriptor flags did not restore"
            }
            failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDOUT_FLAGS)
        }
        if (!errorRedirected && savedError >= 0) stage {
            check(fcntl(errorDescriptor, F_SETFD, originalErrorFlags) == 0 &&
                fcntl(errorDescriptor, F_GETFD, 0) == originalErrorFlags) {
                "Original native stderr descriptor flags did not restore"
            }
            failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDERR_FLAGS)
        }
        outputFile?.let { file -> stage {
            output = capturedBytes(file, maxBytes, OwnedNativeConsoleStage.STDOUT_READ, failureControl)
        } }
        errorFile?.let { file -> stage {
            errors = capturedBytes(file, maxBytes, OwnedNativeConsoleStage.STDERR_READ, failureControl)
        } }
        if (savedOutput >= 0) stage {
            check(close(savedOutput) == 0) { "Owned original stdout backup did not close" }
            failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDOUT_BACKUP_CLOSE)
        }
        if (savedError >= 0) stage {
            check(close(savedError) == 0) { "Owned original stderr backup did not close" }
            failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDERR_BACKUP_CLOSE)
        }
        outputFile?.let { file -> stage {
            check(fclose(file) == 0) { "Owned anonymous stdout capture did not close" }
            failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDOUT_FILE_CLOSE)
        } }
        errorFile?.let { file -> stage {
            check(fclose(file) == 0) { "Owned anonymous stderr capture did not close" }
            failureControl?.afterSuccessful(OwnedNativeConsoleStage.STDERR_FILE_CLOSE)
        } }
        consoleCaptureLease.unlock()
        stage { failureControl?.completed(OwnedNativeConsoleStage.LEASE_RELEASE) }
    }
    captureFailure?.let { captureError ->
        val bodyError = actionResult?.exceptionOrNull()
        if (bodyError != null) {
            if (bodyError !== captureError) bodyError.addSuppressed(captureError)
            throw bodyError
        }
        throw captureError
    }
    check(!outputRedirected && !errorRedirected) { "A console ownership lease remained active" }
    check(failureControl == null) { "A controlled console attempt cannot certify input absence" }
    return CapturedNativeConsole(checkNotNull(actionResult), output, errors)
}
