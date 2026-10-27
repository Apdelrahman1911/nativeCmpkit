package com.mohamedrejeb.calf.navigation

import com.sun.management.ThreadMXBean
import java.lang.management.ManagementFactory
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/** Bounded library-level work/allocation checks; never a wall-clock release budget. */
class NavArrayParsingWorkTest {
    @Test
    fun bulkParsersReadEachBoundedInputOnceForEveryBuiltInArray() {
        for (size in listOf(0, 1, 16, 256, 4096)) {
            val numeric = List(size) { it.toString() }
            val booleans = List(size) { (it % 2 == 0).toString() }
            checkReads(numeric) { source ->
                assertContentEquals(IntArray(size) { it }, AdaptiveNavType.IntArrayType.parseValues(source))
            }
            checkReads(numeric) { source ->
                assertContentEquals(LongArray(size) { it.toLong() }, AdaptiveNavType.LongArrayType.parseValues(source))
            }
            checkReads(numeric) { source ->
                assertContentEquals(FloatArray(size) { it.toFloat() }, AdaptiveNavType.FloatArrayType.parseValues(source))
            }
            checkReads(booleans) { source ->
                assertContentEquals(BooleanArray(size) { it % 2 == 0 }, AdaptiveNavType.BoolArrayType.parseValues(source))
            }
            checkReads(numeric) { source ->
                val result = requireNotNull(AdaptiveNavType.StringArrayType.parseValues(source))
                assertContentEquals(numeric.toTypedArray(), result)
                if (result.isNotEmpty()) result[0] = "result mutation"
            }
        }
    }

    @Test
    fun boundedIntArrayProbeRecordsActualAllocationWithoutTimingAssertions() {
        val bean = assertNotNull(
            ManagementFactory.getThreadMXBean() as? ThreadMXBean,
            "This JVM allocation probe requires the actual JDK management bean; unsupported is not a passing skip",
        )
        assertTrue(bean.isThreadAllocatedMemorySupported, "Thread allocation counters are required for this probe")
        val previouslyEnabled = bean.isThreadAllocatedMemoryEnabled
        try {
            if (!previouslyEnabled) bean.isThreadAllocatedMemoryEnabled = true
            val thread = Thread.currentThread().id
            // Finite warm-up, independent of the measured input lists. No GC call,
            // wall-clock ratio, heap-size assumption or global benchmark baseline.
            repeat(4) {
                val warm = List(64) { it.toString() }
                assertContentEquals(incremental(warm), AdaptiveNavType.IntArrayType.parseValues(warm))
            }
            for (size in listOf(128, 512, 2048, 4096)) {
                val values = List(size) { it.toString() }
                val expected = IntArray(size) { it }
                repeat(3) { trial ->
                    val bulk = observe(bean, thread) { AdaptiveNavType.IntArrayType.parseValues(values) }
                    val legacy = observe(bean, thread) { incremental(values) }
                    assertContentEquals(expected, bulk.result)
                    assertContentEquals(expected, legacy.result)
                    assertTrue(bulk.bytes >= 0 && legacy.bytes >= 0, "Actual thread counters must not regress")
                    // This is the source algorithm's bounded allocation contract,
                    // not a machine-speed assertion. Both results escape to real
                    // content assertions; incremental appends copy prior arrays.
                    if (size == 4096) assertTrue(legacy.bytes > bulk.bytes)
                    println(
                        "nativecmpkit-nav-array-probe:" +
                            "{\"elements\":$size,\"trial\":$trial," +
                            "\"bulk_bytes\":${bulk.bytes},\"legacy_bytes\":${legacy.bytes}," +
                            "\"bulk_ns\":${bulk.nanos},\"legacy_ns\":${legacy.nanos}}",
                    )
                }
            }
        } finally {
            if (bean.isThreadAllocatedMemoryEnabled != previouslyEnabled) {
                bean.isThreadAllocatedMemoryEnabled = previouslyEnabled
            }
        }
    }

    private fun checkReads(values: List<String>, parseAndAssert: (List<String>) -> Unit) {
        val original = values.toList()
        val source = CountingList(values)
        parseAndAssert(source)
        assertContentEquals(IntArray(values.size) { 1 }, source.reads)
        assertEquals(original, values)
    }

    private class CountingList(private val values: List<String>) : AbstractList<String>() {
        val reads = IntArray(values.size)
        override val size: Int get() = values.size
        override fun get(index: Int): String {
            reads[index]++
            return values[index]
        }
    }

    private data class Observation(val result: IntArray, val bytes: Long, val nanos: Long)

    private fun observe(bean: ThreadMXBean, thread: Long, parse: () -> IntArray): Observation {
        val bytesBefore = bean.getThreadAllocatedBytes(thread)
        assertTrue(bytesBefore >= 0, "Actual thread allocation must be observable")
        val started = System.nanoTime()
        val result = parse()
        val elapsed = System.nanoTime() - started
        val bytesAfter = bean.getThreadAllocatedBytes(thread)
        assertTrue(bytesAfter >= bytesBefore, "Actual thread allocation counter regressed")
        return Observation(result, bytesAfter - bytesBefore, elapsed)
    }

    private fun incremental(values: List<String>): IntArray {
        var result = intArrayOf()
        for (value in values) result = requireNotNull(AdaptiveNavType.IntArrayType.parseValue(value, result))
        return result
    }
}
