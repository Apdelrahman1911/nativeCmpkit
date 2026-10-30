// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    kotlin.experimental.ExperimentalNativeApi::class, kotlin.native.runtime.NativeRuntimeApi::class,
    kotlin.native.concurrent.ObsoleteWorkersApi::class)

package com.mohamedrejeb.calf.ui.utils

import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.asSkiaBitmap
import com.mohamedrejeb.calf.ui.internal.onApplicationMain
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runNativeUiTest
import kotlinx.cinterop.COpaquePointer
import kotlinx.cinterop.UByteVar
import kotlinx.cinterop.convert
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.usePinned
import kotlinx.cinterop.get
import kotlinx.cinterop.reinterpret
import platform.CoreFoundation.CFStringCompare
import platform.CoreFoundation.kCFCompareEqualTo
import platform.CoreGraphics.CGBitmapContextCreate
import platform.CoreGraphics.CGBitmapContextGetData
import platform.CoreGraphics.CGBlendMode
import platform.CoreGraphics.CGColorSpaceCreateWithName
import platform.CoreGraphics.CGColorSpaceGetName
import platform.CoreGraphics.CGColorSpaceRef
import platform.CoreGraphics.CGColorSpaceRelease
import platform.CoreGraphics.CGContextDrawImage
import platform.CoreGraphics.CGContextRef
import platform.CoreGraphics.CGContextRelease
import platform.CoreGraphics.CGContextSetBlendMode
import platform.CoreGraphics.CGImageAlphaInfo
import platform.CoreGraphics.CGImageGetColorSpace
import platform.CoreGraphics.CGImageGetHeight
import platform.CoreGraphics.CGImageGetWidth
import platform.CoreGraphics.CGImageRef
import platform.CoreGraphics.CGRectMake
import platform.CoreGraphics.kCGBitmapByteOrder32Big
import platform.CoreGraphics.kCGColorSpaceSRGB
import platform.Foundation.NSFileManager
import platform.Foundation.NSProcessInfo
import platform.Foundation.NSThread
import platform.UIKit.UIImage
import platform.posix.usleep
import kotlin.concurrent.AtomicInt
import kotlin.math.abs
import kotlin.native.concurrent.Future
import kotlin.native.concurrent.FutureState
import kotlin.native.concurrent.TransferMode
import kotlin.native.concurrent.Worker
import kotlin.native.runtime.GC
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlin.time.Duration.Companion.seconds
import kotlin.time.TimeSource

/** New real-native cases only; the nine already accepted conversion cases are not duplicated. */
class UIImageMemoryDiagnosticsTest {
    @Test fun oneMegapixelRetainedImageSurvivesGcAtTheActualSnapshotBoundary() = runNativeUiTest {
        val bitmap = ownedBitmap(1024, 1024)
        val gate = GcGate()
        val worker = Worker.start(name = "NativeCmpKit owned image GC diagnostic")
        var future: Future<Int>? = null
        var bitmapClosed = false
        var failure: Throwable? = null
        try {
            future = worker.execute(TransferMode.SAFE, { gate }) { shared ->
                assertFalse(NSThread.isMainThread)
                awaitCondition { shared.snapshot.value != 0 }
                if (shared.snapshot.value != 1) 0 else try {
                    val pressure = List(3) { value -> ByteArray(2 * 1024 * 1024) { value.toByte() } }
                    repeat(3) { GC.collect() }
                    pressure.forEachIndexed { index, bytes ->
                        assertEquals(index.toByte(), bytes[bytes.lastIndex])
                    }
                    3
                } finally { shared.collected.value = 1 }
            }
            val bridge = object : OwnedBridge() {
                override fun createSnapshot(context: CGContextRef): CGImageRef? {
                    assertTrue(NSThread.isMainThread)
                    // The actual native context already contains its copied 4 MiB RGBA buffer.
                    // Gate GC HERE, not before conversion or after an unrelated input allocation.
                    gate.snapshot.value = 1
                    awaitCondition { gate.collected.value == 1 }
                    return super.createSnapshot(context)
                }
            }
            val image = assertNotNull(bitmap.toUIImage(2.0, bridge))
            bridge.assertBalanced()
            assertEquals(3, awaitFuture(assertNotNull(future)))
            future = null // A Native Future's result is consumed exactly once.
            assertEquals(1024uL, CGImageGetWidth(image.CGImage))
            assertEquals(1024uL, CGImageGetHeight(image.CGImage))
            assertEquals(2.0, image.scale)
            assertSrgb(image)
            // Close ONLY this privately created fixture bitmap, never caller/Compose-owned images.
            bitmap.asSkiaBitmap().close()
            bitmapClosed = true
            repeat(5) { GC.collect() }
            assertKnownPixels(image)
        } catch (error: Throwable) {
            failure = error
            throw error
        } finally {
            gate.snapshot.value = -1
            var cleanupFailure: Throwable? = null
            fun cleanup(action: () -> Unit) {
                try { action() } catch (error: Throwable) {
                    val prior = cleanupFailure
                    if (prior == null) cleanupFailure = error else if (prior !== error) prior.addSuppressed(error)
                }
            }
            cleanup { future?.let { awaitFuture(it) } }
            cleanup { awaitFuture(worker.requestTermination(processScheduledJobs = true)) }
            cleanup { if (!bitmapClosed) bitmap.asSkiaBitmap().close() }
            cleanupFailure?.let { error ->
                val prior = failure
                if (prior == null) throw error else if (prior !== error) prior.addSuppressed(error)
            }
        }
    }

    @Test fun repeatedRealNativeFailuresAndSuccessesBalanceEveryOwnedAllocation() = runNativeUiTest {
        val bitmap = ownedBitmap(128, 96)
        try {
            repeat(8) {
                Failure.entries.filter { it != Failure.None }.forEach { failure ->
                    val bridge = OwnedBridge(failure)
                    if (failure.throws) {
                        assertFailsWith<IllegalStateException> { bitmap.toUIImage(1.0, bridge) }
                    } else assertNull(bitmap.toUIImage(1.0, bridge))
                    bridge.assertBalanced()
                }
                val bridge = OwnedBridge()
                val image = assertNotNull(bitmap.toUIImage(3.0, bridge))
                bridge.assertBalanced()
                assertSrgb(image)
                GC.collect()
                assertKnownPixels(image)
            }
        } finally { bitmap.asSkiaBitmap().close() }
    }

    /**
     * Real conversions remain live while the host profiles this exact owned app/PID. The ack only
     * proves the bounded TOOL ATTEMPT completed, not that Instruments produced a usable profile.
     * Its separately reviewed receipt must establish useful allocation/leak evidence; unsupported
     * tools never become a finding/release pass. At most 4096 rounds / 8192 native conversions.
     */
    @Test fun actualLibraryConversionsRemainBoundedDuringOwnedAllocationProfile() {
        assertFalse(NSThread.isMainThread)
        onApplicationMain { requireOwnedApplicationWindow() }
        val environment = NSProcessInfo.processInfo.environment
        for ((name, value) in mapOf("MallocScribble" to "1", "MallocGuardEdges" to "1",
                                   "MallocErrorAbort" to "1", "MallocStackLogging" to "1")) {
            assertEquals(value, environment[name], "The actual native process must observe the requested $name")
        }
        val ack = assertNotNull(environment["NATIVECMPKIT_IMAGE_PROFILE_ACK"] as? String)
        assertTrue(ack.startsWith("/"))
        assertTrue(Regex("nativecmpkit-image-profile-[0-9a-f]{32}\\.ack").matches(ack.substringAfterLast('/')))
        val files = NSFileManager.defaultManager
        assertFalse(files.fileExistsAtPath(ack), "Never reuse a prior tool completion witness")
        // simctl's console launch header can be buffered until application exit. Publish this
        // actual native PID while the workload is open; the host independently verifies the
        // installed app/executable and correlates the eventual simctl PID before accepting it.
        val pid = platform.posix.getpid()
        assertTrue(pid > 0)
        val ready = assertNotNull(environment["NATIVECMPKIT_IMAGE_PROFILE_READY"] as? String)
        assertEquals(ack.removeSuffix(".ack") + ".ready", ready, "Readiness belongs to the exact same private attempt")
        assertFalse(files.fileExistsAtPath(ready), "Never reuse another workload's native readiness")
        val descriptor = platform.posix.open(ready, platform.posix.O_WRONLY or platform.posix.O_CREAT or platform.posix.O_EXCL, 0x180)
        assertTrue(descriptor >= 0, "Exclusively create this private native PID handoff with mode0600")
        var writeFailure: Throwable? = null
        try {
            val bytes = "process_id=$pid\n".encodeToByteArray()
            bytes.usePinned { pinned ->
                assertEquals(bytes.size.toLong(), platform.posix.write(descriptor, pinned.addressOf(0), bytes.size.convert()),
                    "Publish one complete actual native workload identity, not a partial PID")
            }
        } catch (error: Throwable) {
            writeFailure = error
            throw error
        } finally {
            val closed = platform.posix.close(descriptor)
            if (closed != 0) {
                val error = IllegalStateException("Owned native profile readiness descriptor did not close")
                val primary = writeFailure
                if (primary == null) throw error else primary.addSuppressed(error)
            }
        }
        println("NATIVECMPKIT_IMAGE_PROFILE phase=ready process_id=$pid")
        assertEquals(0, platform.posix.fflush(platform.posix.stdout), "Flush only this owned readiness witness")
        val started = TimeSource.Monotonic.markNow()
        var rounds = 0
        while (!files.fileExistsAtPath(ack)) {
            assertTrue(started.elapsedNow() < 210.seconds, "The owned allocation-tool attempt did not complete")
            assertTrue(rounds < 4096, "Native profile allocation work exceeded its explicit bound")
            onApplicationMain {
                val bitmap = ownedBitmap(128, 96)
                try {
                    val failed = OwnedBridge(Failure.Snapshot)
                    assertNull(bitmap.toUIImage(1.0, failed))
                    failed.assertBalanced()
                    val successful = OwnedBridge()
                    val image = assertNotNull(bitmap.toUIImage(1.0, successful))
                    successful.assertBalanced()
                    assertEquals(128uL, CGImageGetWidth(image.CGImage))
                    assertSrgb(image)
                } finally { bitmap.asSkiaBitmap().close() }
            }
            rounds++
            if (rounds % 8 == 0) GC.collect()
            // This is finite profiling workload pacing, NOT UI-idle or tool-readiness evidence.
            usleep(50_000u)
        }
        assertTrue(rounds > 0, "A tool ack cannot substitute for any actual library conversion")
        GC.collect()
        println("NATIVECMPKIT_IMAGE_PROFILE phase=complete rounds=$rounds")
        assertEquals(0, platform.posix.fflush(platform.posix.stdout), "Flush the actual bounded conversion count")
    }

    private class GcGate(val snapshot: AtomicInt = AtomicInt(0), val collected: AtomicInt = AtomicInt(0))

    private enum class Failure(val throws: Boolean = false) {
        None, ColorSpace, Context, Data, Snapshot, Image,
        ContextException(true), DataException(true), SnapshotException(true), ImageException(true),
    }

    /** Every successful allocation and release invokes the actual production native bridge. */
    private open class OwnedBridge(private val failure: Failure = Failure.None) : BitmapImageBridge() {
        private var spaces = 0; private var contexts = 0; private var images = 0
        private var releasedSpaces = 0; private var releasedContexts = 0; private var releasedImages = 0
        override fun createColorSpace(): CGColorSpaceRef? =
            if (failure == Failure.ColorSpace) null else super.createColorSpace().also { if (it != null) spaces++ }
        override fun createContext(width: Int, height: Int, space: CGColorSpaceRef): CGContextRef? {
            if (failure == Failure.ContextException) error("Injected context construction failure")
            return if (failure == Failure.Context) null else super.createContext(width, height, space)
                .also { if (it != null) contexts++ }
        }
        override fun contextData(context: CGContextRef): COpaquePointer? {
            if (failure == Failure.DataException) error("Injected context data failure")
            return if (failure == Failure.Data) null else super.contextData(context)
        }
        override fun createSnapshot(context: CGContextRef): CGImageRef? {
            if (failure == Failure.SnapshotException) error("Injected snapshot failure")
            return if (failure == Failure.Snapshot) null else super.createSnapshot(context)
                .also { if (it != null) images++ }
        }
        override fun createImage(image: CGImageRef, scale: Double): UIImage? {
            if (failure == Failure.ImageException) error("Injected UIImage construction failure")
            return if (failure == Failure.Image) null else super.createImage(image, scale)
        }
        override fun releaseColorSpace(colorSpace: CGColorSpaceRef) { releasedSpaces++; super.releaseColorSpace(colorSpace) }
        override fun releaseContext(context: CGContextRef) { releasedContexts++; super.releaseContext(context) }
        override fun releaseImage(image: CGImageRef) { releasedImages++; super.releaseImage(image) }
        fun assertBalanced() {
            assertEquals(spaces, releasedSpaces, "color spaces/$failure")
            assertEquals(contexts, releasedContexts, "contexts/$failure")
            assertEquals(images, releasedImages, "CGImages/$failure")
        }
    }

    private fun ownedBitmap(width: Int, height: Int): ImageBitmap = ImageBitmap(width, height).also { bitmap ->
        Canvas(bitmap).drawRect(Rect(0f, 0f, width.toFloat(), height.toFloat()), Paint().apply {
            color = Color(0x8040A0E0)
            blendMode = BlendMode.Src
        })
    }

    private fun assertSrgb(image: UIImage) {
        assertTrue(NSThread.isMainThread)
        val space = assertNotNull(CGImageGetColorSpace(assertNotNull(image.CGImage)))
        assertEquals(kCFCompareEqualTo,
            CFStringCompare(assertNotNull(CGColorSpaceGetName(space)), kCGColorSpaceSRGB, 0uL))
    }

    private fun assertKnownPixels(image: UIImage) {
        val native = assertNotNull(image.CGImage)
        val width = CGImageGetWidth(native).toInt(); val height = CGImageGetHeight(native).toInt()
        val space = assertNotNull(CGColorSpaceCreateWithName(kCGColorSpaceSRGB))
        try {
            val context = assertNotNull(CGBitmapContextCreate(null, width.convert(), height.convert(), 8u,
                (width * 4).convert(), space,
                CGImageAlphaInfo.kCGImageAlphaPremultipliedLast.value or kCGBitmapByteOrder32Big))
            try {
                CGContextSetBlendMode(context, CGBlendMode.kCGBlendModeCopy)
                CGContextDrawImage(context, CGRectMake(0.0, 0.0, width.toDouble(), height.toDouble()), native)
                val bytes = assertNotNull(CGBitmapContextGetData(context)).reinterpret<UByteVar>()
                val expected = intArrayOf(32, 80, 112, 128)
                for (index in 0 until width * height * 4) {
                    assertTrue(abs(bytes[index].toInt() - expected[index % 4]) <= 1, "native RGBA mismatch at $index")
                }
            } finally { CGContextRelease(context) }
        } finally { CGColorSpaceRelease(space) }
    }

    companion object {
        private fun awaitCondition(predicate: () -> Boolean) {
            val started = TimeSource.Monotonic.markNow()
            while (!predicate()) {
                assertTrue(started.elapsedNow() < 20.seconds, "Owned GC Worker/future did not complete")
                usleep(1000u)
            }
        }
        private fun <T> awaitFuture(future: Future<T>): T {
            awaitCondition { future.state != FutureState.SCHEDULED }
            val state = future.state
            val result = future.result // Preserve a failed Worker's original exception, not just its state.
            assertEquals(FutureState.COMPUTED, state)
            return result
        }
    }
}
