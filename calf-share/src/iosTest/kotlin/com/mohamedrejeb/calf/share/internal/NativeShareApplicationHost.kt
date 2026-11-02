// Test-only NativeCmpKit Share application host (2026-11-01).
// Derived from calf-file-picker's genuine UIKit host, not a sample app or picker-acceptance replay.
// Retains Worker/root/cleanup contracts and the actual UIKit root-appearance witness.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlinx.cinterop.BetaInteropApi::class,
    kotlin.experimental.ExperimentalNativeApi::class, kotlin.native.concurrent.ObsoleteWorkersApi::class,
    androidx.compose.runtime.ExperimentalComposeApi::class)

package com.mohamedrejeb.calf.share.internal

import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableIntState
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.Recomposer
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.window.ComposeUIViewController
import androidx.compose.ui.uikit.ComposeUIViewControllerDelegate
import com.mohamedrejeb.calf.share.IosShareOwner
import com.mohamedrejeb.calf.share.IosShareRequestPhase
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
import platform.UIKit.transitionCoordinator
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_main_queue
import platform.darwin.dispatch_sync
import platform.posix.usleep

// All application/window/argument state below is accessed on UIKit's main thread.
@kotlin.native.concurrent.ThreadLocal
private var applicationArguments: Array<String> = emptyArray()
@kotlin.native.concurrent.ThreadLocal
private var applicationWindow: UIWindow? = null
// Strong test-only leases survive a cleanup refusal. They are not production/native hooks.
@kotlin.native.concurrent.ThreadLocal
private val retainedShareTestRoots = mutableListOf<NativeApplicationUiTest>()

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

/** One captured native controller; acknowledgements come only from its actual UIKit callbacks. */
internal class OwnedNativePresentation internal constructor(
    val controller: UIViewController,
    internal val request: IosShareOwner.Request? = null,
) {
    private var presentationCallbackObserved = false
    private var dismissalCallbackObserved = false
    internal val presentationAcknowledged: Boolean
        get() { check(NSThread.isMainThread); return request?.presentationCompletionObserved == true || presentationCallbackObserved }
    internal val dismissalAcknowledged: Boolean
        get() { check(NSThread.isMainThread); return request?.dismissalCompletionObserved == true || dismissalCallbackObserved }
    internal fun presentationCompleted() { check(NSThread.isMainThread); presentationCallbackObserved = true }
    internal fun dismissalCompleted() { check(NSThread.isMainThread); dismissalCallbackObserved = true }
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
    private var rootAppearanceInFlight = false
    private var rootDisappearanceInFlight = false
    private var rootAppearanceCompletions = 0
    private var rootDisappearanceCompletions = 0
    private var closed = false
    private class RetainedShareOwner(val owner: IosShareOwner) {
        val requests = mutableListOf<IosShareOwner.Request>()
    }
    private val shareOwners = mutableListOf<RetainedShareOwner>()
    private val nativeWork = mutableListOf<OwnedNativePresentation>()
    private var terminalInputObservation: ShareTerminalInputObservation? = null

    init {
        check(!NSThread.isMainThread) { "Generated tests must run on the owned worker, not block UIApplicationMain" }
        onApplicationMain {
            window = requireOwnedApplicationWindow()
            terminalInputObservation = ShareTerminalInputObservation.forExactArguments(applicationArguments)
            previous = checkNotNull(window.rootViewController)
            content = mutableStateOf({})
            generation = mutableIntStateOf(0)
            // Test-only public lifecycle witness in the exact configured Compose 1.12.0 API.
            // Deprecated upstream in favor of a containing controller; no production API change
            // or disabled plist/rendering check. Attachment/SideEffect alone precede viewDidAppear.
            @Suppress("DEPRECATION")
            val lifecycle = object : ComposeUIViewControllerDelegate {
                override fun viewWillAppear(animated: Boolean) {
                    check(NSThread.isMainThread)
                    rootAppearanceInFlight = true
                }
                override fun viewDidAppear(animated: Boolean) {
                    check(NSThread.isMainThread)
                    rootHasAppeared = true
                    rootIsAppeared = true
                    rootAppearanceInFlight = false
                    rootDisappearanceInFlight = false
                    rootAppearanceCompletions++
                }
                override fun viewWillDisappear(animated: Boolean) {
                    check(NSThread.isMainThread)
                    rootDisappearanceInFlight = true
                }
                override fun viewDidDisappear(animated: Boolean) {
                    check(NSThread.isMainThread)
                    rootIsAppeared = false
                    rootAppearanceInFlight = false
                    rootDisappearanceInFlight = false
                    rootDisappearanceCompletions++
                }
            }
            @Suppress("DEPRECATION")
            controller = ComposeUIViewController(configure = { delegate = lifecycle }) {
                val composingGeneration = generation.intValue
                content.value()
                SideEffect { committedGeneration = composingGeneration }
            }
            // Retain before installing the root: even a failed setter cannot lose our cleanup lease.
            retainedShareTestRoots += this
            window.rootViewController = controller
        }
    }

    /** Register before launch/dispatch, including a deferred call with no native hierarchy yet. */
    internal fun retainIosShareOwner(owner: IosShareOwner) {
        check(NSThread.isMainThread)
        check(!closed && sameNativeObject(window.rootViewController, controller)) { "Refuse registration for a foreign root" }
        check(sameNativeObject(owner.nativePresenter, controller)) { "Refuse registration of a foreign Share owner" }
        if (shareOwners.none { it.owner === owner }) shareOwners += RetainedShareOwner(owner)
        observeShareRequests()
    }

    /** A non-Share fixture likewise registers its captured controller before the real native call. */
    internal fun retainOwnedNativePresentation(native: UIViewController): OwnedNativePresentation {
        check(NSThread.isMainThread)
        check(!closed && sameNativeObject(window.rootViewController, controller)) { "Refuse registration for a foreign root" }
        check(!sameNativeObject(native, controller) && nativeWork.none { sameNativeObject(it.controller, native) })
        return OwnedNativePresentation(native).also { nativeWork += it }
    }

    /** Called inside that controller's genuine native dismissal completion, before controlled results. */
    internal fun ownedNativeDismissalCompleted(native: UIViewController) {
        check(NSThread.isMainThread)
        observeShareRequests()
        val work = checkNotNull(nativeWork.singleOrNull { sameNativeObject(it.controller, native) }) {
            "Refuse an unregistered native dismissal acknowledgement"
        }
        work.dismissalCompleted()
        terminalInputObservation?.dismissalAcknowledged(work.request)
    }

    private fun observeShareRequests() {
        check(NSThread.isMainThread)
        for (lease in shareOwners) {
            val request = lease.owner.currentRequest ?: continue
            if (lease.requests.none { it === request }) {
                lease.requests += request
                nativeWork += OwnedNativePresentation(request.controller, request)
                terminalInputObservation?.capture(lease.owner, request)
            }
        }
    }

    private fun requestBarriersPassed(): Boolean {
        check(NSThread.isMainThread)
        observeShareRequests()
        return shareOwners.all { it.owner.currentRequest == null && it.requests.all { request -> request.phase == IosShareRequestPhase.Released } }
    }

    private fun nativeIsAbsentAfterAcknowledgement(work: OwnedNativePresentation): Boolean {
        check(NSThread.isMainThread)
        // Nil links are only post-barrier observations, never a completion or a fallback admission.
        if (!work.presentationAcknowledged || !work.dismissalAcknowledged) return false
        val native = work.controller
        return native.presentingViewController == null && !native.isBeingPresented() && !native.isBeingDismissed() &&
            native.view.window == null && !sameNativeObject(controller.presentedViewController, native)
    }

    private fun nativeBarriersPassed(): Boolean = requestBarriersPassed() &&
        nativeWork.all { nativeIsAbsentAfterAcknowledgement(it) } && controller.presentedViewController == null

    /** The file owner must use this even when launch threw before its local request capture. */
    internal fun awaitOwnedIosShareRelease(owner: IosShareOwner) {
        onApplicationMain {
            check(shareOwners.any { it.owner === owner }) { "A pre-launch Share owner obligation is required" }
            observeShareRequests()
        }
        awaitMain("registered Share owner release and actual native acknowledgements") {
            val lease = shareOwners.single { it.owner === owner }
            owner.currentRequest == null && lease.requests.all { it.phase == IosShareRequestPhase.Released } &&
                nativeWork.filter { work -> lease.requests.any { it === work.request } }
                    .all { nativeIsAbsentAfterAcknowledgement(it) }
        }
    }

    private fun dismissOwnedNativePresentation(work: OwnedNativePresentation) {
        check(NSThread.isMainThread)
        check(sameNativeObject(window.rootViewController, controller)) { "Refuse cleanup of a foreign root" }
        check(work.presentationAcknowledged) { "Owned native presentation has no real completion" }
        if (work.dismissalAcknowledged) return
        val native = work.controller
        if (native.isBeingDismissed()) {
            val registered = native.transitionCoordinator?.animateAlongsideTransition(null) { context ->
                if (context != null && !context.isCancelled()) work.dismissalCompleted()
                else dispatch_async(dispatch_get_main_queue()) { dismissOwnedNativePresentation(work) }
            } == true
            check(registered) { "An in-flight owned dismissal requires its actual native completion" }
            return
        }
        // No nil/no-op fallback: this must still be the real captured controller under our root.
        check(sameNativeObject(native.presentingViewController, controller) && !native.isBeingPresented() &&
            sameNativeObject(native.view.window, window)) { "Owned native dismissal lacks its real controller or acknowledgement" }
        native.dismissViewControllerAnimated(false) { work.dismissalCompleted() }
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
            var primary: Throwable? = null
            try { block() } catch (failure: Throwable) {
                primary = failure
                throw failure
            } finally {
                try { observeShareRequests() } catch (cleanup: Throwable) {
                    val prior = primary
                    if (prior == null) throw cleanup else if (prior !== cleanup) prior.addSuppressed(cleanup)
                } finally { generation.intValue++ }
            }
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
            if (onApplicationMain { observeShareRequests(); predicate() }) return
            if (NSProcessInfo.processInfo.systemUptime >= deadline) {
                val actual = onApplicationMain {
                    "active=${UIApplication.sharedApplication.applicationState}, key=${window.isKeyWindow()}, " +
                        "attached=${sameNativeObject(controller.view.window, window)}, " +
                        "everAppeared=$rootHasAppeared, appeared=$rootIsAppeared, " +
                        "appearanceInFlight=$rootAppearanceInFlight, disappearanceInFlight=$rootDisappearanceInFlight, " +
                        "appearanceCompletions=$rootAppearanceCompletions, disappearanceCompletions=$rootDisappearanceCompletions, " +
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

    internal fun emitActivityTerminalFailureObservation() {
        try { onApplicationMain { terminalInputObservation?.emitFailure() } }
        catch (_: Throwable) { /* Observation cannot replace the original assertion/refusal. */ }
    }

    internal fun close() {
        if (onApplicationMain { closed }) return
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
                check(sameNativeObject(window.rootViewController, controller)) { "Refuse cleanup of a foreign root" }
                observeShareRequests()
                shareOwners.forEach { it.owner.dispose() }
                observeShareRequests()
            }
        }
        stage { awaitMain("actual registered Share Request Released/no-active barrier") { requestBarriersPassed() } }
        if (failure == null) stage {
            awaitMain("actual captured native presentation completions") { nativeWork.all { it.presentationAcknowledged } }
        }
        if (failure == null) stage {
            onApplicationMain {
                check(sameNativeObject(window.rootViewController, controller)) { "Refuse cleanup of a foreign root" }
                val presented = controller.presentedViewController
                check(presented == null || nativeWork.any { sameNativeObject(it.controller, presented) }) {
                    "Refuse cleanup of an unregistered native controller"
                }
                nativeWork.forEach { dismissOwnedNativePresentation(it) }
            }
        }
        if (failure == null) stage {
            awaitMain("actual owned native dismissal and released-request barriers") { nativeBarriersPassed() }
        }
        if (failure == null) stage {
            awaitMain("completed owned root appearance after real native teardown") {
                nativeBarriersPassed() && rootHasAppeared && rootIsAppeared && rootAppearanceCompletions > 0 &&
                    !rootAppearanceInFlight && !rootDisappearanceInFlight && sameNativeObject(controller.view.window, window)
            }
        }
        var disappearanceBeforeRestoration = -1
        // A failed/unresolved stage cannot authorize root restoration or detach. Keep all leases.
        if (failure == null) stage {
            onApplicationMain {
                check(sameNativeObject(window.rootViewController, controller)) { "Refuse cleanup of a foreign root" }
                check(nativeBarriersPassed() && rootIsAppeared && !rootAppearanceInFlight && !rootDisappearanceInFlight)
                disappearanceBeforeRestoration = rootDisappearanceCompletions
                window.rootViewController = previous
                requireOwnedApplicationWindow()
            }
        }
        if (failure == null) stage {
            awaitMain("actual completed owned root disappearance after restoration") {
                rootDisappearanceCompletions > disappearanceBeforeRestoration && !rootIsAppeared &&
                    !rootAppearanceInFlight && !rootDisappearanceInFlight && controller.view.window == null &&
                    sameNativeObject(window.rootViewController, previous) && sameNativeObject(previous.view.window, window) &&
                    nativeBarriersPassed()
            }
        }
        if (failure == null) stage {
            onApplicationMain {
                check(rootDisappearanceCompletions > disappearanceBeforeRestoration && !rootIsAppeared &&
                    controller.view.window == null && sameNativeObject(window.rootViewController, previous) && nativeBarriersPassed())
                check(retainedShareTestRoots.count { it === this } == 1) { "Exact retained root lease is required" }
                // Only actual owner/native/root barriers release these test-only retaining leases.
                terminalInputObservation?.closeAfterVerifiedTeardown()
                terminalInputObservation = null
                closed = true
                nativeWork.clear()
                shareOwners.clear()
                retainedShareTestRoots.remove(this)
            }
        }
        failure?.let { throw it }
    }
}

internal fun runApplicationUiTest(block: NativeApplicationUiTest.() -> Unit) {
    val host = NativeApplicationUiTest()
    var failure: Throwable? = null
    try { host.block() } catch (error: Throwable) {
        failure = error
        host.emitActivityTerminalFailureObservation()
        throw error
    } finally {
        try { host.close() } catch (cleanup: Throwable) {
            val prior = failure
            if (prior == null) throw cleanup else if (prior !== cleanup) prior.addSuppressed(cleanup)
        }
    }
}

internal fun NativeApplicationUiTest.waitForNative(predicate: () -> Boolean) {
    awaitMain("native predicate") { predicate() }
}

@ExportObjCClass(name = "NativecmpkitShareLibraryTestDelegate")
class NativeShareApplicationDelegate : UIResponder, UIApplicationDelegateProtocol {
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
        check(worker == null && runner == null && termination == null) { "Unverified worker termination retains main leases" }
        check(retainedShareTestRoots.isEmpty()) { "Unresolved owned root/native work retains main leases" }
        val window = ownedWindow
        check(window == null || sameNativeObject(applicationWindow, window)) { "Refuse release of a foreign application window" }
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
            println("NATIVECMPKIT_UIKIT_TIMEOUT workerTerminationVerified=false mainLeasesRetained=true")
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
                println("NATIVECMPKIT_UIKIT_TERMINATION_ERROR type=${failure::class.simpleName} mainLeasesRetained=true")
                exitProcess(2)
            }
            termination = null
            worker = null
            try { releaseMainLeases() } catch (failure: Throwable) {
                println("NATIVECMPKIT_UIKIT_MAIN_LEASE_REFUSAL type=${failure::class.simpleName} workerTerminated=true mainLeasesRetained=true")
                exitProcess(2)
            }
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
    val delegate = checkNotNull(NSClassFromString("NativecmpkitShareLibraryTestDelegate"))
    UIApplicationMain(0, null, null, NSStringFromClass(delegate))
}
