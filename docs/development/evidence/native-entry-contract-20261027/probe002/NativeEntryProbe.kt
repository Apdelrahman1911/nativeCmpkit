@file:OptIn(kotlin.experimental.ExperimentalNativeApi::class,
    kotlin.native.concurrent.ObsoleteWorkersApi::class)

package nativecmpkit.probe

import kotlin.native.concurrent.TransferMode
import kotlin.native.concurrent.Worker
import kotlin.native.internal.test.GeneratedSuites
import kotlin.native.internal.test.testLauncherEntryPoint
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import kotlin.system.exitProcess

class ActualGeneratedSuite {
    @Test fun actualGeneratedBodyRuns() {
        println("NATIVECMPKIT_ENTRY_PROBE_BODY worker=${Worker.current.id} case=actualGeneratedBodyRuns")
        assertEquals(4, 2 + 2)
    }
    @Test fun actualGeneratedRegistryIsNonEmptyOnExecutionThread() {
        println("NATIVECMPKIT_ENTRY_PROBE_BODY worker=${Worker.current.id} case=actualGeneratedRegistryIsNonEmptyOnExecutionThread")
        assertTrue(GeneratedSuites.suites.any { it.name == "nativecmpkit.probe.ActualGeneratedSuite" })
    }
}

fun customMain(args: Array<String>) {
    val mainNames = GeneratedSuites.suites.map { it.name }.sorted()
    println("NATIVECMPKIT_ENTRY_PROBE_CUSTOM mainWorker=${Worker.current.id} suites=$mainNames")
    check(mainNames == listOf("nativecmpkit.probe.ActualGeneratedSuite"))
    val worker = Worker.start(name = "nativecmpkit-entry-contract-probe")
    try {
        val names = worker.execute(TransferMode.SAFE, { Unit }) {
            GeneratedSuites.suites.map { it.name }.sorted()
        }.result
        println("NATIVECMPKIT_ENTRY_PROBE_WORKER suites=$names")
        val result = testLauncherEntryPoint(args)
        println("NATIVECMPKIT_ENTRY_PROBE_RESULT exit=$result")
        if (result != 0) exitProcess(result)
    } finally {
        worker.requestTermination().result
    }
}
