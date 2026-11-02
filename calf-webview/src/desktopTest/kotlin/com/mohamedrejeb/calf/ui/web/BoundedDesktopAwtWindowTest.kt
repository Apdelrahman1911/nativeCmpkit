// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import java.util.concurrent.CountDownLatch
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.concurrent.thread
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Controlled scheduler/objects and real threads; these are not AWT/JavaFX native passes. */
class BoundedDesktopAwtWindowTest {
    private class Queue {
        private val work = LinkedBlockingQueue<() -> Unit>()
        fun schedule(action: () -> Unit) { work.add(action) }
        fun next(): () -> Unit = checkNotNull(work.poll(5, TimeUnit.SECONDS))
        fun drain() { while (true) (work.poll() ?: return).invoke() }
    }

    private fun CountDownLatch.reached() = assertTrue(await(5, TimeUnit.SECONDS), "Owned thread did not reach its gate")
    private fun Thread.finished() { join(5_000); assertFalse(isAlive, "Owned fixture thread must terminate") }

    @Test fun closeBeforeQueuedInitializerEntryPreventsAllAllocations() {
        val queue = Queue()
        val creates = AtomicInteger(); val configurations = AtomicInteger(); val disposals = AtomicInteger()
        val window = BoundedDesktopAwtWindow(queue::schedule,
            { creates.incrementAndGet(); Any() }, { configurations.incrementAndGet() }, { disposals.incrementAndGet() })
        window.close(100)
        queue.drain()
        window.close(100)
        assertFailsWith<IllegalStateException> { window.awaitCreated(100) }
        assertEquals(0, creates.get()); assertEquals(0, configurations.get()); assertEquals(0, disposals.get())
    }

    @Test fun lateFactoryReturnAfterTimeoutDisposesExactlyOnceWithoutConfiguring() {
        val queue = Queue(); val entered = CountDownLatch(1); val returnFactory = CountDownLatch(1)
        val configurations = AtomicInteger(); val disposals = AtomicInteger(); val owned = Any()
        val failure = AtomicReference<Throwable?>()
        val window = BoundedDesktopAwtWindow(queue::schedule,
            { entered.countDown(); returnFactory.reached(); owned },
            { configurations.incrementAndGet() }, { assertSame(owned, it); disposals.incrementAndGet() })
        val worker = thread(name = "nativecmpkit-awt-factory-control") {
            runCatching { queue.next().invoke() }.onFailure { failure.set(it) }
        }
        try {
            entered.reached()
            assertFailsWith<AssertionError> { window.awaitCreated(20) }
            assertEquals(0, disposals.get(), "A still-running constructor is not a disposal barrier")
        } finally { returnFactory.countDown(); worker.finished() }
        window.close(1_000); queue.drain(); window.close(1_000)
        assertNull(failure.get()); assertEquals(0, configurations.get()); assertEquals(1, disposals.get())
    }

    @Test fun nestedDispatchCannotDisposeWhileConfigurationStillOwnsTheWindow() {
        val queue = Queue(); val disposals = AtomicInteger(); val owned = Any()
        val failure = AtomicReference<Throwable?>(); var closer: Thread? = null
        lateinit var window: BoundedDesktopAwtWindow<Any>
        window = BoundedDesktopAwtWindow(queue::schedule, { owned }, {
            closer = thread(name = "nativecmpkit-awt-nested-close-control") {
                runCatching { window.close(5_000) }.onFailure { failure.set(it) }
            }
            queue.next().invoke() // Model an actual nested AWT event dispatch during configure.
            assertEquals(0, disposals.get(), "Reentrant work cannot release the initializer's resource")
        }, { assertSame(owned, it); disposals.incrementAndGet() })
        queue.next().invoke()
        checkNotNull(closer).finished(); window.close(1_000)
        assertNull(failure.get()); assertEquals(1, disposals.get())
    }

    @Test fun configurationFailureRetainsPrimaryAndAttemptsOwnedDisposal() {
        val queue = Queue(); val primary = IllegalArgumentException("controlled configuration failure")
        val cleanup = IllegalStateException("controlled disposal failure"); val disposals = AtomicInteger()
        val window = BoundedDesktopAwtWindow(queue::schedule, { Any() }, { throw primary }, {
            disposals.incrementAndGet(); throw cleanup
        })
        queue.drain()
        assertSame(primary, assertFailsWith<IllegalArgumentException> { window.awaitCreated(100) })
        assertSame(cleanup, assertFailsWith<IllegalStateException> { window.close(100) })
        assertSame(cleanup, assertFailsWith<IllegalStateException> { window.close(100) })
        assertEquals(1, disposals.get())
    }

    @Test fun heldDisposalTimesOutWithoutPretendingReleaseOrRepeatingTheAttempt() {
        val queue = Queue(); val entered = CountDownLatch(1); val finishDisposal = CountDownLatch(1)
        val disposals = AtomicInteger(); val failure = AtomicReference<Throwable?>()
        val window = BoundedDesktopAwtWindow(queue::schedule, { Any() }, {}, {
            disposals.incrementAndGet(); entered.countDown(); finishDisposal.reached()
        })
        queue.drain(); window.awaitCreated(100)
        assertFailsWith<AssertionError> { window.close(20) } // Cleanup is queued, not yet complete.
        val worker = thread(name = "nativecmpkit-awt-disposal-control") {
            runCatching { queue.next().invoke() }.onFailure { failure.set(it) }
        }
        try {
            entered.reached()
            assertFailsWith<AssertionError> { window.close(20) }
            assertEquals(1, disposals.get())
        } finally { finishDisposal.countDown(); worker.finished() }
        window.close(1_000); queue.drain(); window.close(1_000)
        assertNull(failure.get()); assertEquals(1, disposals.get())
    }

    @Test fun queuedThenThrowingSchedulerCannotAllocateAfterTheOriginalFailure() {
        val queue = Queue(); val primary = IllegalStateException("controlled enqueue failure")
        val creates = AtomicInteger(); val disposals = AtomicInteger()
        val window = BoundedDesktopAwtWindow<Any>(
            { action -> queue.schedule(action); throw primary },
            { creates.incrementAndGet(); Any() }, {}, { disposals.incrementAndGet() })
        assertSame(primary, assertFailsWith<IllegalStateException> { window.awaitCreated(100) })
        window.close(100); queue.drain()
        assertEquals(0, creates.get()); assertEquals(0, disposals.get())
    }

    @Test fun normalCompletionUsesTheSameObjectAndDisposesOnlyOnce() {
        val queue = Queue(); val owned = Any(); val configurations = AtomicInteger(); val disposals = AtomicInteger()
        val window = BoundedDesktopAwtWindow(queue::schedule, { owned }, {
            assertSame(owned, it); configurations.incrementAndGet()
        }, { assertSame(owned, it); disposals.incrementAndGet() })
        queue.drain(); window.awaitCreated(100)
        assertEquals(1, configurations.get()); assertEquals(0, disposals.get())
        assertFailsWith<AssertionError> { window.close(20) }
        queue.drain(); window.close(100); window.close(100)
        assertEquals(1, configurations.get()); assertEquals(1, disposals.get())
    }

    @Test fun interruptedCreationWaitCancelsQueuedWorkAndKeepsTheFailureVisible() {
        val queue = Queue(); val waiting = CountDownLatch(1); val result = AtomicReference<Throwable?>()
        val creates = AtomicInteger()
        val window = BoundedDesktopAwtWindow(queue::schedule, { creates.incrementAndGet(); Any() }, {}, {})
        val waiter = thread(name = "nativecmpkit-awt-interrupted-control") {
            waiting.countDown()
            runCatching { window.awaitCreated(5_000) }.onFailure { result.set(it) }
        }
        waiting.reached(); waiter.interrupt(); waiter.finished()
        assertTrue(result.get() is InterruptedException)
        queue.drain(); window.close(100); assertEquals(0, creates.get())
    }

    @Test fun theOwnedHandleIsRetainedDuringDisposalAndAfterFailureButClearedOnReturn() {
        for (throwFromDisposal in listOf(false, true)) {
            val queue = Queue(); val cleanup = IllegalStateException("controlled retained-handle failure")
            val attempts = AtomicInteger()
            lateinit var window: BoundedDesktopAwtWindow<Any>
            window = BoundedDesktopAwtWindow(queue::schedule, { Any() }, {}, {
                assertTrue(window.hasUnreleasedWindow, "Disposal must still own its exact native handle")
                attempts.incrementAndGet()
                if (throwFromDisposal) throw cleanup
            })
            queue.drain(); window.awaitCreated(100)
            assertTrue(window.hasUnreleasedWindow)
            assertFailsWith<AssertionError> { window.close(20) }
            queue.drain()
            if (throwFromDisposal) {
                assertSame(cleanup, assertFailsWith<IllegalStateException> { window.close(100) })
                assertSame(cleanup, assertFailsWith<IllegalStateException> { window.close(100) })
                assertTrue(window.hasUnreleasedWindow, "A throw is not completed native disposal")
            } else {
                window.close(100); window.close(100)
                assertFalse(window.hasUnreleasedWindow)
            }
            assertEquals(1, attempts.get(), "A retained failed handle does not authorize retry")
        }
    }
}
