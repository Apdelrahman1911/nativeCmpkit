@file:OptIn(kotlin.experimental.ExperimentalNativeApi::class,
    kotlin.native.concurrent.ObsoleteWorkersApi::class)
package nativecmpkit.probe

import kotlin.native.concurrent.TransferMode
import kotlin.native.concurrent.Worker
import kotlin.native.internal.test.GeneratedSuites
import kotlin.native.internal.test.testLauncherEntryPoint
import kotlin.test.Test
import kotlin.test.assertTrue
import kotlin.system.exitProcess

@kotlin.native.concurrent.ThreadLocal
private object BodyContext {
    var mainWorker = 0
    var intentionalFailure = false
}

class ActualWorkerGeneratedSuite {
    @Test fun generatedRegistryAndBodyActuallyRunOnOwnedWorker() {
        println("NATIVECMPKIT_WORKER_BODY case=generatedRegistryAndBodyActuallyRunOnOwnedWorker worker=${Worker.current.id} mainWorker=${BodyContext.mainWorker}")
        assertTrue(BodyContext.mainWorker != 0 && Worker.current.id != BodyContext.mainWorker)
        assertTrue(GeneratedSuites.suites.any { it.name == "nativecmpkit.probe.ActualWorkerGeneratedSuite" })
    }
    @Test fun requestedAssertionFailureIsNotSilentSuccess() {
        println("NATIVECMPKIT_WORKER_BODY case=requestedAssertionFailureIsNotSilentSuccess worker=${Worker.current.id} mainWorker=${BodyContext.mainWorker} intentionalFailure=${BodyContext.intentionalFailure}")
        assertTrue(BodyContext.mainWorker != 0 && Worker.current.id != BodyContext.mainWorker)
        assertTrue(!BodyContext.intentionalFailure, "owned diagnostic negative control: intentional assertion failure")
    }
}

private data class Request(val arguments: Array<String>, val mainWorker: Int, val intentionalFailure: Boolean)

fun customMain(arguments: Array<String>) {
    val fail = arguments.contains("--nativecmpkit-probe-fail")
    val request = Request(arguments.filter { it != "--nativecmpkit-probe-fail" }.toTypedArray(), Worker.current.id, fail)
    check(GeneratedSuites.suites.map { it.name }.sorted() == listOf("nativecmpkit.probe.ActualWorkerGeneratedSuite"))
    val worker = Worker.start(name = "nativecmpkit-owned-generated-body-probe")
    println("NATIVECMPKIT_WORKER_CREATED mainWorker=${request.mainWorker} ownedWorker=${worker.id}")
    val exit = try {
        worker.execute(TransferMode.SAFE, { request }) { transferred ->
            BodyContext.mainWorker = transferred.mainWorker
            BodyContext.intentionalFailure = transferred.intentionalFailure
            testLauncherEntryPoint(transferred.arguments)
        }.result
    } finally {
        // Termination must complete before process exit; exitProcess is not a finally unwind.
        worker.requestTermination().result
        println("NATIVECMPKIT_WORKER_TERMINATED")
    }
    println("NATIVECMPKIT_WORKER_RESULT exit=$exit")
    if (exit != 0) exitProcess(exit)
}
