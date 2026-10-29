// Test-only NativeCmpKit picker application host (2026-10-29).
// Derived from calf-ui's host; retains Worker/cleanup contracts and additionally witnesses UIKit root appearance.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlinx.cinterop.BetaInteropApi::class,
    kotlin.experimental.ExperimentalNativeApi::class, kotlin.native.concurrent.ObsoleteWorkersApi::class,
    androidx.compose.runtime.ExperimentalComposeApi::class)

package com.mohamedrejeb.calf.picker.internal

import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableIntState
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.Recomposer
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.window.ComposeUIViewController
import androidx.compose.ui.uikit.ComposeUIViewControllerDelegate
import kotlinx.cinterop.ExportObjCClass
import kotlinx.cinterop.ObjCObjectBase.OverrideInit
import kotlin.native.concurrent.Future
import kotlin.native.concurrent.FutureState
import kotlin.native.concurrent.TransferMode
import kotlin.native.concurrent.Worker
import kotlin.native.internal.test.GeneratedSuites
import kotlin.native.internal.test.testLauncherEntryPoint
import kotlin.system.exitProcess
import platform.Foundation.NSClassFromString
import platform.Foundation.NSProcessInfo
import platform.Foundation.NSStringFromClass
import platform.Foundation.NSThread
import platform.Foundation.NSTimer
import platform.UIKit.UIApplication
import platform.UIKit.UIApplicationDelegateProtocol
import platform.UIKit.UIApplicationMain
import platform.UIKit.UIApplicationState.UIApplicationStateActive
import platform.UIKit.UIResponder
import platform.UIKit.UIScreen
import platform.UIKit.UIViewController
import platform.UIKit.UIWindow
import platform.darwin.dispatch_get_main_queue
import platform.darwin.dispatch_sync
import platform.posix.usleep

// All application/window/argument state below is accessed on UIKit's main thread.
@kotlin.native.concurrent.ThreadLocal
private var applicationArguments: Array<String> = emptyArray()
@kotlin.native.concurrent.ThreadLocal
private var applicationWindow: UIWindow? = null

internal fun <T> onApplicationMain(action: () -> T): T {
    if (NSThread.isMainThread) return action()
    var result: Result<T>? = null
    dispatch_sync(dispatch_get_main_queue()) { result = runCatching(action) }
    return checkNotNull(result).getOrThrow()
}

internal fun requireOwnedApplicationWindow(): UIWindow {
    check(NSThread.isMainThread)
    check(UIApplication.sharedApplication.applicationState == UIApplicationStateActive) {
        "Native presentation tests require an active UIApplication, not a Skiko-only scene"
    }
    val window = checkNotNull(applicationWindow) { "Use the genuine library application test task" }
    check(window.isKeyWindow() && !window.hidden) { "The owned application window must be visible and key" }
    check(sameNativeObject(window.rootViewController?.view?.window, window)) { "The root must be attached to the owned UIWindow" }
    return window
}

/** Real ComposeUIViewController/window composition; the UIApplication main loop stays live. */
internal class NativeApplicationUiTest {
    private lateinit var window: UIWindow
    private lateinit var previous: UIViewController
    private lateinit var controller: UIViewController
    private lateinit var content: MutableState<@Composable () -> Unit>
    private lateinit var generation: MutableIntState
    private var committedGeneration = -1
    private var rootHasAppeared = false
    private var rootIsAppeared = false
    private var closed = false

    init {
        check(!NSThread.isMainThread) { "Generated tests must run on the owned worker, not block UIApplicationMain" }
        onApplicationMain {
            window = requireOwnedApplicationWindow()
            previous = checkNotNull(window.rootViewController)
            content = mutableStateOf({})
            generation = mutableIntStateOf(0)
            // Test-only public lifecycle witness in the exact configured Compose 1.12.0 API.
            // Deprecated upstream in favor of a containing controller; no production API change
            // or disabled plist/rendering check. Attachment/SideEffect alone precede viewDidAppear.
            @Suppress("DEPRECATION")
            val lifecycle = object : ComposeUIViewControllerDelegate {
                override fun viewDidAppear(animated: Boolean) {
                    check(NSThread.isMainThread)
                    rootHasAppeared = true
                    rootIsAppeared = true
                }
                override fun viewWillDisappear(animated: Boolean) {
                    check(NSThread.isMainThread)
                    rootIsAppeared = false
                }
            }
            @Suppress("DEPRECATION")
            controller = ComposeUIViewController(configure = { delegate = lifecycle }) {
                val composingGeneration = generation.intValue
                content.value()
                SideEffect { committedGeneration = composingGeneration }
            }
            window.rootViewController = controller
        }
    }

    fun setContent(block: @Composable () -> Unit) {
        onApplicationMain {
            check(!closed)
            content.value = block
            generation.intValue++
        }
    }

    fun <T> runOnIdle(block: () -> T): T {
        waitForIdle()
        return onApplicationMain {
            check(!closed)
            try { block() } finally { generation.intValue++ }
        }
    }

    fun waitForIdle() {
        awaitMain("committed attached ComposeUIViewController composition") {
            requireOwnedApplicationWindow()
            check(sameNativeObject(window.rootViewController, controller)) { "Native test no longer owns the root" }
            controller.view.layoutIfNeeded()
            rootHasAppeared && sameNativeObject(controller.view.window, window) && committedGeneration == generation.intValue &&
                Recomposer.runningRecomposers.value.none { it.hasPendingWork }
        }
    }

    internal fun awaitMain(phase: String, predicate: () -> Boolean) {
        check(!NSThread.isMainThread)
        val deadline = NSProcessInfo.processInfo.systemUptime + 10.0
        while (true) {
            if (onApplicationMain(predicate)) return
            if (NSProcessInfo.processInfo.systemUptime >= deadline) {
                val actual = onApplicationMain {
                    "active=${UIApplication.sharedApplication.applicationState}, key=${window.isKeyWindow()}, " +
                        "attached=${sameNativeObject(controller.view.window, window)}, " +
                        "everAppeared=$rootHasAppeared, appeared=$rootIsAppeared, " +
                        "generation=${generation.intValue}, committed=$committedGeneration, " +
                        "pending=${Recomposer.runningRecomposers.value.count { it.hasPendingWork }}"
                }
                error("Timed out awaiting $phase; actual application state: $actual")
            }
            // Poll backoff only: idle is established by actual attachment,
            // native viewDidAppear, SideEffect generation and Recomposer work, never elapsed sleep.
            usleep(1000u)
        }
    }

    internal fun close() {
        if (closed) return
        var failure: Throwable? = null
        fun stage(action: () -> Unit) {
            try { action() } catch (error: Throwable) {
                val prior = failure
                if (prior == null) failure = error else if (prior !== error) prior.addSuppressed(error)
            }
        }
        stage { setContent {} }
        stage { waitForIdle() }
        stage {
            onApplicationMain {
                if (controller.presentedViewController != null) controller.dismissViewControllerAnimated(false, null)
            }
        }
        stage { awaitMain("owned native presenter teardown") { controller.presentedViewController == null } }
        stage { awaitMain("owned root reappearance after presenter teardown") { rootIsAppeared } }
        // Always attempt restoring our root even after a failed presenter/idle
        // check. Never detach another test's or application's replacement root.
        stage {
            onApplicationMain {
                check(sameNativeObject(window.rootViewController, controller)) { "Refuse cleanup of a foreign root" }
                window.rootViewController = previous
                check(controller.view.window == null) { "Owned Compose root is still attached after restoration" }
                requireOwnedApplicationWindow()
            }
        }
        stage { awaitMain("owned root disappearance after restoration") {
            !rootIsAppeared && controller.view.window == null && sameNativeObject(window.rootViewController, previous)
        } }
        closed = true
        failure?.let { throw it }
    }
}

internal fun runApplicationUiTest(block: NativeApplicationUiTest.() -> Unit) {
    val host = NativeApplicationUiTest()
    var failure: Throwable? = null
    try { host.block() } catch (error: Throwable) { failure = error; throw error } finally {
        try { host.close() } catch (cleanup: Throwable) {
            val prior = failure
            if (prior == null) throw cleanup else if (prior !== cleanup) prior.addSuppressed(cleanup)
        }
    }
}

internal fun NativeApplicationUiTest.waitForNative(predicate: () -> Boolean) {
    awaitMain("native predicate") { predicate() }
}

@ExportObjCClass(name = "NativecmpkitPickerLibraryTestDelegate")
class NativePickerApplicationDelegate : UIResponder, UIApplicationDelegateProtocol {
    // UIApplicationMain constructs the exported class through Objective-C
    // alloc/init, not a Kotlin primary constructor. Export the inherited init.
    @OverrideInit
    constructor() : super()

    private var ownedWindow: UIWindow? = null
    private var activationRequested = false
    private var started = false
    private var worker: Worker? = null
    private var runner: Future<Int>? = null
    private var termination: Future<Unit>? = null
    private var runnerExit = 1
    private var timer: NSTimer? = null
    private var startedAt = 0.0

    override fun application(application: UIApplication, didFinishLaunchingWithOptions: Map<Any?, *>?): Boolean {
        check(NSThread.isMainThread)
        ownedWindow = UIWindow(frame = UIScreen.mainScreen.bounds).apply {
            rootViewController = UIViewController()
            makeKeyAndVisible()
        }
        applicationWindow = ownedWindow
        return true
    }

    override fun applicationDidBecomeActive(application: UIApplication) {
        check(NSThread.isMainThread)
        if (activationRequested) return
        activationRequested = true
        startedAt = NSProcessInfo.processInfo.systemUptime
        // Activation is not a guarantee that UIKit has attached the root yet.
        // Return to its main loop; admit the worker only on observed readiness.
        // The timer is a backoff, not evidence, and repeated activations cannot
        // create another timer/worker or extend the startup deadline.
        timer = NSTimer.scheduledTimerWithTimeInterval(0.05, repeats = true) { pollCompletion() }
    }

    private fun awaitApplicationReadiness(): Boolean {
        check(NSThread.isMainThread)
        val window = checkNotNull(ownedWindow)
        window.layoutIfNeeded()
        val attached = window.rootViewController?.view?.window
        val ready = UIApplication.sharedApplication.applicationState == UIApplicationStateActive &&
            window.isKeyWindow() && !window.hidden && sameNativeObject(attached, window)
        if (ready) return true
        if (NSProcessInfo.processInfo.systemUptime - startedAt >= 10.0) {
            // Attachment uses exact native pointers. NSObject value equality is
            // diagnostic only; it can never establish an ownership lease.
            println("NATIVECMPKIT_UIKIT_STARTUP_TIMEOUT " +
                "active=${UIApplication.sharedApplication.applicationState == UIApplicationStateActive} " +
                "key=${window.isKeyWindow()} hidden=${window.hidden} " +
                "rootAttached=${sameNativeObject(attached, window)} rootNativeEqual=${attached == window} workerStarted=false")
            releaseMainLeases()
            exitProcess(2)
        }
        return false
    }

    private fun startGeneratedTests() {
        check(NSThread.isMainThread)
        check(!started && worker == null && runner == null && termination == null)
        requireOwnedApplicationWindow()
        started = true
        startedAt = NSProcessInfo.processInfo.systemUptime
        val arguments = applicationArguments
        val owned = Worker.start(name = "nativecmpkit-owned-uikit-library-tests")
        worker = owned
        println("NATIVECMPKIT_UIKIT_ACTIVE mainWorker=${Worker.current.id} ownedWorker=${owned.id}")
        runner = owned.execute(TransferMode.SAFE, { arguments }) { testLauncherEntryPoint(it) }
    }

    private fun releaseMainLeases() {
        check(NSThread.isMainThread)
        timer?.invalidate()
        timer = null
        applicationWindow = null
        ownedWindow?.rootViewController = null
        ownedWindow?.hidden = true
        ownedWindow = null
    }

    private fun pollCompletion() {
        check(NSThread.isMainThread)
        if (!started) {
            if (!awaitApplicationReadiness()) return
            startGeneratedTests()
        }
        if (NSProcessInfo.processInfo.systemUptime - startedAt > 1800.0) {
            releaseMainLeases()
            println("NATIVECMPKIT_UIKIT_TIMEOUT workerTerminationVerified=false")
            // A stuck test worker cannot be safely declared terminated. The
            // wrapper must fail and clean up this owned app, never invent a pass.
            exitProcess(2)
        }
        val pending = runner
        if (pending != null && pending.state != FutureState.SCHEDULED) {
            runnerExit = try { pending.result } catch (failure: Throwable) {
                println("NATIVECMPKIT_UIKIT_RUNNER_ERROR type=${failure::class.simpleName}")
                1
            }
            runner = null
            termination = checkNotNull(worker).requestTermination()
        }
        val stopping = termination
        if (stopping != null && stopping.state != FutureState.SCHEDULED) {
            try { stopping.result } catch (failure: Throwable) {
                releaseMainLeases()
                println("NATIVECMPKIT_UIKIT_TERMINATION_ERROR type=${failure::class.simpleName}")
                exitProcess(2)
            }
            termination = null
            worker = null
            releaseMainLeases()
            // KGP passes --ktest_no_exit_code: failed tests normally still
            // return0 here. Their real TeamCity/JUnit outcomes decide Gradle.
            println("NATIVECMPKIT_UIKIT_COMPLETED runnerExit=$runnerExit workerTerminated=true")
            exitProcess(runnerExit)
        }
    }
}

fun nativeApplicationMain(arguments: Array<String>) {
    check(NSThread.isMainThread)
    check(GeneratedSuites.suites.isNotEmpty()) { "An empty generated registry is not a library test run" }
    applicationArguments = arguments
    val delegate = checkNotNull(NSClassFromString("NativecmpkitPickerLibraryTestDelegate"))
    UIApplicationMain(0, null, null, NSStringFromClass(delegate))
}
