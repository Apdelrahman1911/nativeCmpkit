// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference

/**
 * Test-only ownership of one asynchronously created AWT window. Waiting never
 * interrupts AWT or invents native disposal. A timed-out initializer must either
 * be cancelled before entry or release its window when the actual call returns.
 * The scheduler must serialize work as AWT does; it may dispatch reentrantly.
 */
internal class BoundedDesktopAwtWindow<T : Any>(
    private val schedule: (() -> Unit) -> Unit,
    private val create: () -> T,
    private val configure: (T) -> Unit,
    private val dispose: (T) -> Unit,
) {
    private enum class Creation { Queued, Running, Finished, Cancelled }
    private enum class Phase { Queued, Creating, Configuring, Created, Disposing, Disposed, Failed, Cancelled }

    private val creation = AtomicReference(Creation.Queued)
    private val phase = AtomicReference(Phase.Queued)
    private val closing = AtomicBoolean()
    private val disposalAttempted = AtomicBoolean()
    private val ready = CountDownLatch(1)
    private val released = CountDownLatch(1)
    private val creationFailure = AtomicReference<Throwable?>()
    private val disposalFailure = AtomicReference<Throwable?>()
    private val owned = AtomicReference<T?>()
    // Confined to the scheduler; a nested AWT loop must not dispose during configure.
    private var initializing = false

    /** Read-only fixture observation; a failed disposal never relinquishes this handle. */
    internal val hasUnreleasedWindow: Boolean get() = owned.get() != null

    init {
        try {
            schedule(::initialize)
        } catch (error: Throwable) {
            creationFailure.compareAndSet(null, error)
            ready.countDown()
            requestClose()
        }
    }

    private fun initialize() {
        if (!creation.compareAndSet(Creation.Queued, Creation.Running)) return
        initializing = true
        try {
            phase.set(Phase.Creating)
            val window = create()
            owned.set(window)
            if (!closing.get()) {
                phase.set(Phase.Configuring)
                configure(window)
                phase.set(Phase.Created)
            }
        } catch (error: Throwable) {
            creationFailure.compareAndSet(null, error)
            phase.set(Phase.Failed)
            closing.set(true)
        } finally {
            initializing = false
            creation.set(Creation.Finished)
            if (closing.get()) releaseOnAwt()
            ready.countDown()
        }
    }

    fun awaitCreated(timeoutMillis: Long) {
        require(timeoutMillis > 0)
        val completed = try {
            ready.await(timeoutMillis, TimeUnit.MILLISECONDS)
        } catch (error: InterruptedException) {
            requestClose()
            throw error
        }
        if (!completed) {
            reportTimeout("creation")
            requestClose()
            throw AssertionError("Timed out awaiting the actual AWT window initializer")
        }
        creationFailure.get()?.let { throw it }
        check(creation.get() == Creation.Finished && !closing.get()) {
            "AWT window creation was cancelled; no ready native window is inferred"
        }
    }

    private fun requestClose() {
        if (!closing.compareAndSet(false, true)) return
        if (creation.compareAndSet(Creation.Queued, Creation.Cancelled)) {
            phase.set(Phase.Cancelled)
            ready.countDown()
            released.countDown() // The queued initializer can no longer enter create.
            return
        }
        try {
            schedule(::releaseOnAwt)
        } catch (error: Throwable) {
            disposalFailure.compareAndSet(null, error)
            // An initializer already running still releases in its own finally.
            // Failed scheduling is never reported as successful native disposal.
            if (creation.get() != Creation.Running) released.countDown()
        }
    }

    private fun releaseOnAwt() {
        if (initializing || !disposalAttempted.compareAndSet(false, true)) return
        val window = owned.get()
        try {
            phase.set(Phase.Disposing)
            window?.let(dispose)
            // Keep the exact handle throughout native disposal and after a throw.
            // The once-only attempt guard, not early reference removal, prevents reentry.
            if (window != null) check(owned.compareAndSet(window, null))
            phase.set(Phase.Disposed)
        } catch (error: Throwable) {
            disposalFailure.compareAndSet(null, error)
            phase.set(Phase.Failed)
        } finally {
            released.countDown() // Completion of the attempt; callers also check its failure.
        }
    }

    fun close(timeoutMillis: Long) {
        require(timeoutMillis > 0)
        requestClose()
        if (!released.await(timeoutMillis, TimeUnit.MILLISECONDS)) {
            reportTimeout("disposal")
            throw AssertionError("Timed out awaiting actual owned AWT window disposal")
        }
        disposalFailure.get()?.let { throw it }
    }

    private fun reportTimeout(stage: String) {
        // Fixed tokens only. This is an after-timeout observation, not its cause,
        // a historical poll, a hard native deadline or a successful cleanup receipt.
        runCatching {
            System.err.println("NATIVECMPKIT_DESKTOP_AWT_WINDOW_TIMEOUT_V1 " +
                "stage=$stage;phase=${phase.get().name};creation=${creation.get().name};" +
                "closing=${closing.get()};owned=${owned.get() != null};" +
                "disposalAttempted=${disposalAttempted.get()}")
        }
    }
}
