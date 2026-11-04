// SPDX-License-Identifier: Apache-2.0
@file:Suppress("DEPRECATION")
package com.mohamedrejeb.calf.camerapicker

import android.app.ActivityManager
import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.os.Process
import android.provider.MediaStore
import androidx.lifecycle.Lifecycle
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import java.util.concurrent.CopyOnWriteArrayList
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/**
 * One API35 public Compose consumer changes A to B during a genuine foreign-UID
 * capture. Native task reentry lets the SAME caller commit recompositions while
 * the owned delayed Activity still holds its actual EXTRA_OUTPUT/result request.
 * Only that Activity writes/closes the synthetic output and returns Android's
 * ActivityResult; no handleResult, registry/result injection or second capture.
 * Targets NATIVE-020's callback criterion, not its iOS owner/GC criteria,
 * physical-camera/vendor UX, restoration, packaged consumers or API/ABI readiness.
 * Enabled and normally inherited: an unfiltered API23 suite must not claim this
 * API35-only method passed or silently hide it with Ignore/assumptions.
 */
@RunWith(AndroidJUnit4::class)
class AndroidCameraCallbackSubstitutionTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val pm get() = context.packageManager
    private val manager get() = context.getSystemService(ActivityManager::class.java)
    private val client = ComponentName(context, CameraProviderVerificationActivity::class.java)
    private val delayed = ComponentName(OwnedCameraReceiver.PACKAGE, "${OwnedCameraReceiver.PACKAGE}.CameraDelayedReceiverActivity")
    private val callerLeaseKey = "nativecmpkit.callbackCallerLease"
    private val expectedBytes = "NativeCmpKit synthetic native camera output".encodeToByteArray()

    /** Identity is joined from native returned observations, never a completion input fabricated by this test. */
    private data class NativeCapture(
        val uri: Uri, val file: File, val packet: String, val callerPacket: String,
        val generation: String, val recipientPid: Int, val intents: Int,
    )

    @Test fun nativeActiveCaptureDeliversOnceToLatestCallbackWithoutReplacingOwner() {
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedCameraReceiver"))
        assertEquals(35, Build.VERSION.SDK_INT); assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        assertEquals("com.mohamedrejeb.calf.calfcamerapicker.test", context.packageName)
        assertEquals(0, Process.myUid() / 100_000)
        assertTrue(pm.hasSystemFeature(PackageManager.FEATURE_CAMERA_ANY), "Require the selected owned emulated camera")
        val clientInfo = pm.getActivityInfo(client, 0)
        assertEquals(Process.myUid(), clientInfo.applicationInfo.uid)
        assertEquals(context.applicationInfo.processName, clientInfo.processName)
        assertFalse(clientInfo.exported); assertNull(clientInfo.permission)
        assertTrue(clientTaskSnapshots().isEmpty(), "Refuse a pre-existing own callback caller task")
        val before = outputs()
        val originalDelayed = pm.getComponentEnabledSetting(delayed)
        assertEquals(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT, originalDelayed)
        assertFalse(pm.getActivityInfo(delayed, PackageManager.MATCH_DISABLED_COMPONENTS).enabled)
        val lease = UUID.randomUUID().toString().replace("-", "")
        val deliveredA = CopyOnWriteArrayList<Pair<CameraPickerResult, Boolean>>()
        val deliveredB = CopyOnWriteArrayList<Pair<CameraPickerResult, Boolean>>()
        val callbackA: (CameraPickerResult) -> Unit = { result ->
            deliveredA.add(result to (Looper.myLooper() == Looper.getMainLooper()))
        }
        val callbackB: (CameraPickerResult) -> Unit = { result ->
            deliveredB.add(result to (Looper.myLooper() == Looper.getMainLooper()))
        }
        var receiver: OwnedCameraReceiver? = null
        var scenario: ActivityScenario<CameraProviderVerificationActivity>? = null
        var caller: CameraProviderVerificationActivity? = null
        var callerTaskId: Int? = null
        var sibling: File? = null
        var capture: NativeCapture? = null
        var beforeIntents = -1
        var changedDelayed = false
        var captureAttempted = false
        var externalTerminated = false
        var tasksGone = false
        var primaryFailure: Throwable? = null
        try {
            val siblingFile = File.createTempFile("nativecmpkit-callback-sibling-", ".txt", context.cacheDir)
            sibling = siblingFile
            siblingFile.writeText("untouched cache sibling")
            val ownerReceiver = OwnedCameraReceiver()
            receiver = ownerReceiver // Retain a partial binding before connect can fail.
            ownerReceiver.connect()
            val cleared = ownerReceiver.request("clear") // Refuses any live/unowned capture or component lease.
            assertFalse(cleared.getBoolean("received")); assertFalse(cleared.getBoolean("holdingActivity"))
            beforeIntents = cleared.getInt("intents").also { check(it >= 0) }
            changedDelayed = true // Retain the exact lease before its native mutation/reply can fail.
            val armed = ownerReceiver.armDelayed(lease)
            assertDelayedControl(ownerReceiver, armed, lease, armed = true)
            assertEquals(cleared.getString("generation"), armed.getString("generation"))
            assertEquals(cleared.getInt("pid"), armed.getInt("pid"))
            assertEquals(PackageManager.COMPONENT_ENABLED_STATE_ENABLED, pm.getComponentEnabledSetting(delayed))
            assertDelayedRecipient(ownerReceiver)

            // A fresh native task lease is only caller custody, not an output/receiver packet.
            // MULTIPLE_TASK avoids reusing or clearing an unrelated existing task.
            val entry = Intent(context, CameraProviderVerificationActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_MULTIPLE_TASK)
                .putExtra(callerLeaseKey, lease)
            val currentScenario = ActivityScenario.launch<CameraProviderVerificationActivity>(entry)
            scenario = currentScenario
            currentScenario.onActivity { caller = it }
            val activity = assertNotNull(caller)
            callerTaskId = onMain {
                assertEquals(client, activity.componentName)
                assertEquals(lease, activity.intent.getStringExtra(callerLeaseKey))
                assertFalse(activity.delayedCallbackCapture)
                assertFalse(activity.missingHandler); assertFalse(activity.implicitCamera); assertFalse(activity.cancel)
                activity.taskId.also { check(it > 0) }
            }
            val taskId = assertNotNull(callerTaskId)
            waitUntil("initial native caller/composition") {
                activity.launcher != null && callerForeground(activity) && foregroundPackage() == context.packageName &&
                    leasedCallerTasks(lease).singleOrNull()?.second?.topActivity == client
            }
            assertEquals(taskId, nativeTask(lease, taskId).second.taskId)
            onMain { activity.resultCallback = callbackA; activity.recompositionTick = 1; activity.delayedCallbackCapture = true }
            awaitAppliedCallback(activity, callbackA, 1)
            val publicOwner = assertNotNull(activity.launcher)
            assertTrue(deliveredA.isEmpty()); assertTrue(deliveredB.isEmpty()); assertTrue(activity.results.isEmpty())
            onMain { captureAttempted = true; publicOwner.launch() } // The sole public capture launch.

            waitUntil("genuine owned delayed capture and external foreground") {
                check(deliveredA.isEmpty() && deliveredB.isEmpty() && activity.results.isEmpty()) {
                    "The delayed capture delivered a result before callback substitution"
                }
                val report = ownerReceiver.request("snapshot")
                if (report.getBoolean("received")) {
                    val joined = joinCapture(ownerReceiver, activity, report, before, beforeIntents)
                    assertEquals(cleared.getString("generation"), joined.generation)
                    assertEquals(cleared.getInt("pid"), joined.recipientPid)
                    capture?.let { assertEquals(it, joined) }
                    capture = joined
                }
                capture != null && report.getBoolean("holdingActivity") &&
                    nativeTask(lease, taskId).second.topActivity == delayed &&
                    foregroundPackage() == OwnedCameraReceiver.PACKAGE && onMain {
                        !activity.lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED) && !activity.hasWindowFocus()
                    }
            }
            val held = assertNotNull(capture)
            assertActiveCapture(ownerReceiver, activity, held, before, beforeIntents)
            assertTrue(deliveredA.isEmpty()); assertTrue(deliveredB.isEmpty()); assertTrue(activity.results.isEmpty())

            // A stopped caller's Compose clock need not commit B. Ask Android to
            // reorder the ORIGINAL Activity, not recreate it or inject a callback.
            // The delayed capture stays active behind it until native completion.
            onMain {
                assertFalse(activity.isDestroyed); assertFalse(activity.isFinishing)
                activity.startActivity(Intent(activity, CameraProviderVerificationActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT).putExtra(callerLeaseKey, lease))
            }
            waitUntil("same original caller native foreground reentry") {
                callerForeground(activity) && foregroundPackage() == context.packageName &&
                    nativeTask(lease, taskId).second.topActivity == client
            }
            currentScenario.onActivity { assertSame(activity, it); assertEquals(taskId, it.taskId) }
            onMain { assertSame(publicOwner, activity.launcher) }
            assertActiveCapture(ownerReceiver, activity, held, before, beforeIntents)
            assertTrue(deliveredA.isEmpty()); assertTrue(deliveredB.isEmpty()); assertTrue(activity.results.isEmpty())

            onMain { activity.resultCallback = callbackB; activity.recompositionTick = 2 }
            awaitAppliedCallback(activity, callbackB, 2)
            for (tick in 2..5) {
                if (tick > 2) {
                    onMain { activity.recompositionTick = tick } // Ordinary recomposition, callback unchanged.
                    awaitAppliedCallback(activity, callbackB, tick)
                }
                onMain {
                    assertSame(publicOwner, activity.launcher)
                    assertEquals(taskId, activity.taskId)
                    assertEquals(held.uri, activity.outputUri); assertEquals(held.callerPacket, activity.packet)
                    assertEquals(1, activity.externalLaunches)
                }
                assertTrue(callerForeground(activity)); assertEquals(context.packageName, foregroundPackage())
                assertEquals(client, nativeTask(lease, taskId).second.topActivity)
                assertActiveCapture(ownerReceiver, activity, held, before, beforeIntents)
                assertTrue(deliveredA.isEmpty()); assertTrue(deliveredB.isEmpty()); assertTrue(activity.results.isEmpty())
            }

            // The receiver generates its OWN packet. Complete only the joined
            // returned packet, never activity.packet or a fabricated result.
            val done = ownerReceiver.complete(held.packet, cancel = false)
            assertEquals(held, joinCapture(ownerReceiver, activity, done, before, beforeIntents))
            assertTrue(done.getBoolean("completed")); assertFalse(done.getBoolean("holdingActivity"))
            assertFalse(done.getBoolean("cancelled")); assertNull(done.getString("writeError"))
            assertEquals(1, done.getInt("opens")); assertEquals(1, done.getInt("closes"))
            waitUntil("one genuine Android result to latest callback B") {
                check(deliveredA.isEmpty()) { "Stale callback A received the active capture result" }
                check(deliveredB.size <= 1) { "The active capture was delivered more than once" }
                check(activity.results.isEmpty()) { "The default callback unexpectedly received this capture" }
                deliveredB.size == 1
            }
            val delivery = deliveredB.single()
            assertTrue(delivery.second, "Actual callback must arrive on Android Main")
            val captured = assertIs<CameraPickerResult.Captured>(delivery.first)
            assertEquals(held.uri, captured.file.uri)
            assertContentEquals(expectedBytes, context.contentResolver.openInputStream(captured.file.uri)!!.use { it.readBytes() })
            assertTrue(held.file.isFile, "Successful output remains caller-owned after native completion")
            assertEquals(setOf(held.file.name), outputs() - before)
            waitUntil("native external termination and same caller focus") {
                !ownerReceiver.request("snapshot").getBoolean("holdingActivity") && callerForeground(activity) &&
                    foregroundPackage() == context.packageName && nativeTask(lease, taskId).second.topActivity == client
            }
            externalTerminated = true
            instrumentation.waitForIdleSync()
            currentScenario.onActivity { assertSame(activity, it); assertEquals(taskId, it.taskId); assertSame(publicOwner, it.launcher) }
            val idle = ownerReceiver.request("snapshot")
            assertEquals(held, joinCapture(ownerReceiver, activity, idle, before, beforeIntents))
            assertTrue(idle.getBoolean("completed")); assertFalse(idle.getBoolean("holdingActivity"))
            assertEquals(1, idle.getInt("opens")); assertEquals(1, idle.getInt("closes"))
            assertTrue(deliveredA.isEmpty()); assertEquals(1, deliveredB.size); assertTrue(activity.results.isEmpty())
            assertTrue(held.file.isFile); assertEquals("untouched cache sibling", siblingFile.readText())
        } catch (failure: Throwable) {
            primaryFailure = failure
            throw failure
        } finally {
            val primary = primaryFailure
            var cleanupFailure: Throwable? = null
            fun cleanup(action: () -> Unit) {
                try { action() } catch (failure: Throwable) {
                    if (primary != null) { if (failure !== primary) primary.addSuppressed(failure) }
                    else { val prior = cleanupFailure; if (prior == null) cleanupFailure = failure else prior.addSuppressed(failure) }
                }
            }
            cleanup {
                val activity = caller
                if (!captureAttempted || activity != null && onMain { activity.externalLaunches == 0 }) {
                    externalTerminated = true // No native external launch entered; do not touch an unknown capture.
                } else {
                    val owner = assertNotNull(receiver)
                    val actualCaller = assertNotNull(activity)
                    val taskId = assertNotNull(callerTaskId)
                    nativeTask(lease, taskId) // Native lease/task ownership before any external mutation.
                    val report = owner.request("snapshot")
                    val joined = joinCapture(owner, actualCaller, report, before, beforeIntents)
                    capture?.let { assertEquals(it, joined) }
                    capture = joined // Retain exact output custody before later cleanup assertions can fail.
                    if (report.getBoolean("holdingActivity")) {
                        val cancelled = owner.complete(joined.packet, cancel = true)
                        assertEquals(joined, joinCapture(owner, actualCaller, cancelled, before, beforeIntents))
                        assertTrue(cancelled.getBoolean("completed")); assertTrue(cancelled.getBoolean("cancelled"))
                        assertFalse(cancelled.getBoolean("holdingActivity"))
                    }
                    waitUntil("only the joined external capture terminates during cleanup") {
                        val terminal = owner.request("snapshot")
                        assertEquals(joined, joinCapture(owner, actualCaller, terminal, before, beforeIntents))
                        !terminal.getBoolean("holdingActivity") && nativeTask(lease, taskId).second.topActivity != delayed
                    }
                    externalTerminated = true
                }
            }
            cleanup {
                check(externalTerminated) { "Do not close a caller with an unknown/unjoined external capture" }
                scenario?.close()
            }
            cleanup {
                check(externalTerminated) { "Do not remove a task with an unverified live external capture" }
                for ((task, info) in leasedCallerTasks(lease)) {
                    callerTaskId?.let { assertEquals(it, info.taskId) }
                    task.finishAndRemoveTask() // Only the exact fresh own caller task, never other app tasks.
                }
                waitUntil("exact own callback caller task cleanup") { leasedCallerTasks(lease).isEmpty() }
                caller?.let { activity -> waitUntil("original callback caller destruction") { onMain { activity.isDestroyed } } }
                tasksGone = true
            }
            if (changedDelayed) cleanup {
                val owner = assertNotNull(receiver)
                assertDelayedControl(owner, owner.restoreDelayed(lease), lease, armed = false)
                assertEquals(originalDelayed, pm.getComponentEnabledSetting(delayed))
                assertFalse(pm.getActivityInfo(delayed, PackageManager.MATCH_DISABLED_COMPONENTS).enabled)
                assertTrue(pm.queryIntentActivities(delayedIntent(), PackageManager.MATCH_DEFAULT_ONLY).isEmpty())
            }
            cleanup { receiver?.close() } // Independent unbind/thread close even after an earlier restoration failure.
            cleanup {
                capture?.file?.let { file ->
                    if (file.exists()) {
                        check(tasksGone && externalTerminated) { "Do not unlink an unverified in-flight output" }
                        assertTrue(file.delete()) // Only the joined output, never a cache-diff sweep.
                    }
                }
                assertEquals(before, outputs())
            }
            cleanup { sibling?.let { assertEquals("untouched cache sibling", it.readText()) } }
            cleanup { sibling?.let { if (it.exists()) assertTrue(it.delete()) } }
            cleanupFailure?.let { throw it }
        }
    }

    private fun joinCapture(owner: OwnedCameraReceiver, activity: CameraProviderVerificationActivity,
        report: Bundle, before: Set<String>, beforeIntents: Int): NativeCapture {
        for (key in setOf("received", "holdingActivity", "caller", "uri", "packet", "action", "activityPid",
            "uid", "pid", "generation", "intents", "flags", "readGranted", "writeGranted", "clipMatches")) {
            assertTrue(report.containsKey(key), "Missing genuine native capture observation: $key")
        }
        assertTrue(report.getBoolean("received")); assertEquals(context.packageName, report.getString("caller"))
        assertEquals(MediaStore.ACTION_IMAGE_CAPTURE, report.getString("action"))
        assertEquals(owner.recipientUid, report.getInt("uid")); assertNotEquals(Process.myUid(), report.getInt("uid"))
        val pid = report.getInt("pid").also { check(it > 0 && it != Process.myPid()) }
        assertEquals(pid, report.getInt("activityPid"))
        val packet = assertNotNull(report.getString("packet")).also { check(it.matches(Regex("[a-f0-9]{32}"))) }
        val generation = assertNotNull(report.getString("generation")).also { check(it.matches(Regex("[a-f0-9-]{36}"))) }
        assertTrue(beforeIntents >= 0); assertEquals(beforeIntents + 1, report.getInt("intents"))
        val uri = Uri.parse(assertNotNull(report.getString("uri")))
        val callerPacket = onMain {
            assertEquals(uri, activity.outputUri); assertEquals(1, activity.externalLaunches)
            assertNotNull(activity.packet).also { check(it.matches(Regex("[a-f0-9]{32}"))) }
        }
        return NativeCapture(uri, outputFor(uri, before), packet, callerPacket, generation, pid, report.getInt("intents"))
    }

    private fun assertActiveCapture(owner: OwnedCameraReceiver, activity: CameraProviderVerificationActivity,
        capture: NativeCapture, before: Set<String>, beforeIntents: Int) {
        val report = owner.request("snapshot")
        assertEquals(capture, joinCapture(owner, activity, report, before, beforeIntents))
        assertTrue(report.getBoolean("holdingActivity")); assertFalse(report.getBoolean("completed"))
        assertFalse(report.getBoolean("cancelled")); assertNull(report.getString("writeError"))
        assertTrue(report.getBoolean("readGranted")); assertTrue(report.getBoolean("writeGranted")); assertTrue(report.getBoolean("clipMatches"))
        assertEquals(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
            report.getInt("flags") and (Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION))
        assertEquals(0, report.getInt("opens")); assertEquals(0, report.getInt("closes"))
        assertTrue(capture.file.isFile); assertEquals(0L, capture.file.length())
        assertEquals(setOf(capture.file.name), outputs() - before)
    }

    private fun awaitAppliedCallback(activity: CameraProviderVerificationActivity, callback: (CameraPickerResult) -> Unit, tick: Int) {
        waitUntil("actual Compose callback/tick commit") { activity.appliedCallback === callback && activity.appliedTick == tick }
        instrumentation.waitForIdleSync()
    }
    private fun callerForeground(activity: CameraProviderVerificationActivity): Boolean = onMain {
        check(!activity.isDestroyed && !activity.isFinishing) { "The original callback caller must survive native reentry" }
        activity.lifecycle.currentState == Lifecycle.State.RESUMED && activity.hasWindowFocus()
    }
    private fun foregroundPackage(): String? {
        val root = instrumentation.uiAutomation.rootInActiveWindow ?: return null // Unavailable is not admission/absence.
        return try { root.packageName?.toString() } finally { root.recycle() }
    }

    private fun clientTaskSnapshots(): List<Pair<ActivityManager.AppTask, ActivityManager.RecentTaskInfo>> =
        manager.appTasks.map { task ->
            // SDK37 permits null. Refuse unavailable information, including during preflight.
            task to assertNotNull(task.taskInfo, "Unknown native task; do not infer absence")
        }.filter { (_, info) -> info.baseIntent.component == client }

    private fun leasedCallerTasks(lease: String): List<Pair<ActivityManager.AppTask, ActivityManager.RecentTaskInfo>> {
        check(lease.matches(Regex("[a-f0-9]{32}")))
        return clientTaskSnapshots().also { tasks ->
            check(tasks.size <= 1) { "Refuse competing native callback caller tasks" }
            check(tasks.all { (_, info) -> info.baseIntent.getStringExtra(callerLeaseKey) == lease }) {
                "Refuse an unknown native callback caller task lease"
            }
        }
    }
    private fun nativeTask(lease: String, taskId: Int): Pair<ActivityManager.AppTask, ActivityManager.RecentTaskInfo> {
        check(taskId > 0)
        return leasedCallerTasks(lease).single().also { (_, info) -> assertEquals(taskId, info.taskId) }
    }

    // These strict receiver lease/recipient and output-path bodies retain the
    // existing restoration primitives; no new grant/component/path authority.
    private fun assertDelayedControl(owner: OwnedCameraReceiver, reply: android.os.Bundle, lease: String, armed: Boolean) {
        for (key in setOf("delayedControlVerified", "componentOwnerUid", "componentState",
            "originalComponentState", "manifestComponentEnabled", "nativeHandlerCount")) {
            assertTrue(reply.containsKey(key), "Missing native component readback: $key")
        }
        assertTrue(reply.getBoolean("delayedControlVerified"))
        assertEquals(delayed.flattenToString(), reply.getString("controlledComponent"))
        assertEquals(lease, reply.getString("controlledLease"))
        assertEquals(if (armed) "arm-delayed" else "restore-delayed", reply.getString("controlledOperation"))
        assertEquals(owner.recipientUid, reply.getInt("componentOwnerUid"))
        assertEquals(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT, reply.getInt("originalComponentState"))
        assertEquals(if (armed) PackageManager.COMPONENT_ENABLED_STATE_ENABLED else PackageManager.COMPONENT_ENABLED_STATE_DEFAULT,
            reply.getInt("componentState"))
        assertFalse(reply.getBoolean("manifestComponentEnabled"))
        assertEquals(if (armed) 1 else 0, reply.getInt("nativeHandlerCount"))
    }
    private fun delayedIntent() = Intent(MediaStore.ACTION_IMAGE_CAPTURE).setPackage(OwnedCameraReceiver.PACKAGE)
    private fun assertDelayedRecipient(owner: OwnedCameraReceiver) {
        // A package-scoped query is the correct native recipient precondition.
        // Unqualified implicit IMAGE_CAPTURE is system-only on Android15 absent DPC
        // persistent preference; enabling our third-party component cannot change it.
        val matches = pm.queryIntentActivities(delayedIntent(), PackageManager.MATCH_DEFAULT_ONLY)
        assertEquals(1, matches.size)
        val info = matches.single().activityInfo
        assertEquals(delayed, ComponentName(info.packageName, info.name))
        assertEquals(owner.recipientUid, info.applicationInfo.uid)
        assertEquals(OwnedCameraReceiver.PERMISSION, info.permission); assertTrue(info.exported)
        val resolved = assertNotNull(pm.resolveActivity(delayedIntent(), PackageManager.MATCH_DEFAULT_ONLY)).activityInfo
        assertEquals(delayed, ComponentName(resolved.packageName, resolved.name))
        assertEquals(owner.recipientUid, resolved.applicationInfo.uid)
    }
    private fun outputs() = File(context.cacheDir, "nativecmpkit-camera").listFiles().orEmpty().map { it.name }.toSet()
    private fun outputFor(uri: Uri, before: Set<String>): File {
        assertEquals("content", uri.scheme); assertEquals("${context.packageName}.camera-files", uri.authority)
        assertEquals(2, uri.pathSegments.size); assertEquals("camera", uri.pathSegments[0])
        val name = uri.pathSegments[1]
        check(name.matches(Regex("capture-[A-Za-z0-9._-]+\\.jpg")) && ".." !in name && name !in before)
        val directory = File(context.cacheDir, "nativecmpkit-camera").canonicalFile
        return File(directory, name).also { check(it.canonicalFile == it && it.parentFile == directory) }
    }
    private fun waitUntil(label: String, predicate: () -> Boolean) {
        val start = System.nanoTime()
        while (!predicate()) {
            check(System.nanoTime() - start < 20_000_000_000L) { "Native callback verification timed out: $label" }
            Thread.sleep(20)
        }
    }
    private fun <T> onMain(action: () -> T): T {
        var result: Result<T>? = null
        instrumentation.runOnMainSync { result = runCatching(action) }
        return checkNotNull(result).getOrThrow()
    }
}
