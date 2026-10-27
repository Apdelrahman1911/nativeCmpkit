@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlinx.cinterop.BetaInteropApi::class,
    kotlin.experimental.ExperimentalNativeApi::class, kotlin.native.concurrent.ObsoleteWorkersApi::class)
package nativecmpkit.verification.uikit

import kotlinx.cinterop.ExportObjCClass
import kotlinx.cinterop.getObjCClass
import kotlin.native.concurrent.Future
import kotlin.native.concurrent.FutureState
import kotlin.native.concurrent.TransferMode
import kotlin.native.concurrent.Worker
import kotlin.native.internal.test.GeneratedSuites
import kotlin.native.internal.test.testLauncherEntryPoint
import kotlin.system.exitProcess
import kotlin.test.*
import platform.Foundation.*
import platform.UIKit.*
import platform.darwin.*

@kotlin.native.concurrent.ThreadLocal
private var nativeArguments: Array<String> = emptyArray()
@kotlin.native.concurrent.ThreadLocal
private var ownedWindow: UIWindow? = null

private fun <T> onApplicationMain(block: () -> T): T {
    if (NSThread.isMainThread) return block()
    var result: Result<T>? = null
    dispatch_sync(dispatch_get_main_queue()) { result = runCatching(block) }
    return requireNotNull(result).getOrThrow()
}

class GenuineApplicationContract {
    @Test fun generatedBodyRunsOnWorkerWithRealActiveApplicationOnMain() {
        assertFalse(NSThread.isMainThread)
        onApplicationMain {
            assertTrue(NSThread.isMainThread)
            assertEquals(UIApplicationStateActive, UIApplication.sharedApplication.applicationState)
            val window = requireNotNull(ownedWindow)
            assertTrue(window.isKeyWindow())
            assertFalse(window.hidden)
            assertSame(window, requireNotNull(window.rootViewController).view.window)
        }
    }
    @Test fun workerCanObserveTheActualGeneratedRegistry() {
        assertFalse(NSThread.isMainThread)
        assertTrue(GeneratedSuites.suites.any { it.name == "nativecmpkit.verification.uikit.GenuineApplicationContract" })
    }
}

@ExportObjCClass
class UIKitApplicationProbeDelegate : UIResponder(), UIApplicationDelegateProtocol {
    override var window: UIWindow? = null
    private var started = false
    private var worker: Worker? = null
    private var result: Future<Int>? = null
    private var termination: Future<Unit>? = null
    private var exit = 1
    private var timer: NSTimer? = null
    private var startedAt = 0.0

    override fun application(application: UIApplication, didFinishLaunchingWithOptions: Map<Any?, *>?): Boolean {
        check(NSThread.isMainThread)
        window = UIWindow(frame = UIScreen.mainScreen.bounds).apply {
            rootViewController = UIViewController()
            makeKeyAndVisible()
        }
        ownedWindow = window
        return true
    }

    override fun applicationDidBecomeActive(application: UIApplication) {
        check(NSThread.isMainThread)
        if (started) return
        started = true
        startedAt = NSProcessInfo.processInfo.systemUptime
        val args = nativeArguments
        val owned = Worker.start(name = "nativecmpkit-uikit-generated-tests")
        worker = owned
        result = owned.execute(TransferMode.SAFE, { args }) { testLauncherEntryPoint(it) }
        timer = NSTimer.scheduledTimerWithTimeInterval(0.05, repeats = true) { pollCompletion() }
        println("NATIVECMPKIT_UIKIT_ACTIVE mainWorker=${Worker.current.id} ownedWorker=${owned.id}")
    }

    private fun pollCompletion() {
        check(NSThread.isMainThread)
        if (NSProcessInfo.processInfo.systemUptime - startedAt > 1800.0) {
            timer?.invalidate()
            println("NATIVECMPKIT_UIKIT_TIMEOUT")
            exitProcess(2)
        }
        val pending = result
        if (pending != null && pending.state != FutureState.SCHEDULED) {
            exit = try { pending.result } catch (failure: Throwable) {
                println("NATIVECMPKIT_UIKIT_RUNNER_ERROR type=${failure::class.simpleName}")
                1
            }
            result = null
            termination = requireNotNull(worker).requestTermination()
        }
        val stopping = termination
        if (stopping != null && stopping.state != FutureState.SCHEDULED) {
            stopping.result
            timer?.invalidate()
            termination = null
            worker = null
            ownedWindow = null
            window?.rootViewController = null
            window?.hidden = true
            window = null
            println("NATIVECMPKIT_UIKIT_TERMINATED exit=$exit")
            exitProcess(exit)
        }
    }
}

fun nativeApplicationMain(arguments: Array<String>) {
    check(NSThread.isMainThread)
    check(GeneratedSuites.suites.isNotEmpty())
    nativeArguments = arguments
    UIApplicationMain(0, null, null, NSStringFromClass(getObjCClass<UIKitApplicationProbeDelegate>()))
}
