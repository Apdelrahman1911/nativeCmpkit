// SPDX-License-Identifier: Apache-2.0
@file:Suppress("DEPRECATION")
package com.mohamedrejeb.calf.camerapicker

import android.app.ActivityManager
import android.app.UiAutomation
import android.content.ComponentName
import android.content.Intent
import android.content.pm.ActivityInfo
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.net.Uri
import android.os.Build
import android.os.ParcelFileDescriptor
import android.os.Process
import android.os.SystemClock
import android.provider.MediaStore
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import android.system.StructPollfd
import android.util.Xml
import android.view.WindowManager
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.util.UUID
import org.junit.Test
import org.junit.runner.RunWith
import org.xmlpull.v1.XmlPullParser
import kotlin.test.*

/**
 * Real public TakePicture launcher/Android registry, external foreground Activity,
 * don't-keep-activities, display rotation and kernel process death/restoration.
 * Reporter survives in another process; Android alone saves/delivers the result.
 * Bytes/recipient are synthetic, not a hardware photo, vendor UI or physical device.
 */
@RunWith(AndroidJUnit4::class)
class AndroidCameraRestorationTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val pm get() = context.packageManager
    private val manager get() = context.getSystemService(ActivityManager::class.java)
    private val client = ComponentName(context, CameraRestorationVerificationActivity::class.java)
    private val delayed = ComponentName(OwnedCameraReceiver.PACKAGE, "${OwnedCameraReceiver.PACKAGE}.CameraDelayedReceiverActivity")
    private val processName get() = "${context.packageName}:nativecmpkit_camera_client"
    private val expectedBytes = "NativeCmpKit synthetic native camera output".encodeToByteArray()

    @Test fun nativeDontKeepActivitiesRestoresOneReadableCapturedFile() = capture(dontKeep = true)
    @Test fun nativeRotationRecreatesCallerWhileExternalCaptureIsForeground() = capture(rotate = true)
    @Test fun nativeKernelProcessDeathRestoresPendingUriAndExactlyOneSuccess() = capture(kill = true)
    @Test fun nativeCancelledProcessRestorationRemovesOnlyItsFileAndNeverDeliversStaleUri() = capture(kill = true, cancel = true)

    private fun capture(dontKeep: Boolean = false, rotate: Boolean = false, kill: Boolean = false, cancel: Boolean = false) {
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedCameraReceiver"))
        assertEquals(35, Build.VERSION.SDK_INT); assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        assertEquals("com.mohamedrejeb.calf.calfcamerapicker.test", context.packageName)
        assertTrue(pm.hasSystemFeature(PackageManager.FEATURE_CAMERA_ANY)); assertEquals(0, Process.myUid() / 100_000)
        val clientInfo = pm.getActivityInfo(client, 0)
        assertFalse(clientInfo.exported); assertEquals(processName, clientInfo.processName)
        assertEquals(0, clientInfo.configChanges and (ActivityInfo.CONFIG_ORIENTATION or ActivityInfo.CONFIG_SCREEN_SIZE))
        val nonce = UUID.randomUUID().toString().replace("-", "")
        val prefName = "nativecmpkit-camera-restoration-$nonce"
        assertFalse(preferenceFile(prefName).exists()); assertTrue(tasks(nonce).isEmpty())
        val before = outputs()
        val originalFinish = setting("global", "always_finish_activities", setOf("null", "0", "1"))
        val originalAutoRotate = setting("system", "accelerometer_rotation", setOf("null", "0", "1"))
        val originalUserRotation = setting("system", "user_rotation", setOf("null", "0", "1", "2", "3"))
        val originalRotation = context.getSystemService(WindowManager::class.java).defaultDisplay.rotation.also { check(it in 0..3) }
        val originalDelayed = pm.getComponentEnabledSetting(delayed)
        assertEquals(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT, originalDelayed)
        assertFalse(pm.getActivityInfo(delayed, PackageManager.MATCH_DISABLED_COMPONENTS).enabled)
        var receiver: OwnedCameraReceiver? = null
        var sibling: File? = null
        var ownedOutput: File? = null
        var tasksGone = false
        var externalTerminated = false
        var changedDelayed = false
        var changedFinish = false
        var changedRotation = false
        var primaryFailure: Throwable? = null
        try {
            val siblingFile = File.createTempFile("nativecmpkit-restoration-sibling-", ".txt", context.cacheDir)
            sibling = siblingFile
            siblingFile.writeText("untouched cache sibling")
            val currentReceiver = OwnedCameraReceiver()
            receiver = currentReceiver // Retain a partial binding before connect can fail.
            currentReceiver.connect(); currentReceiver.request("clear")
            changedDelayed = true
            assertDelayedControl(currentReceiver, currentReceiver.armDelayed(nonce), nonce, armed = true)
            assertEquals(PackageManager.COMPONENT_ENABLED_STATE_ENABLED, pm.getComponentEnabledSetting(delayed))
            assertDelayedRecipient(currentReceiver)
            if (dontKeep) {
                changedFinish = true
                assertEquals("", shell("settings put global always_finish_activities 1"))
                assertEquals("1", setting("global", "always_finish_activities", setOf("1")))
            }
            // The reporter survives in a background process. Start only this fixed
            // nonce-bound owned Activity through Android's native shell entry; no
            // external camera, URI grant or registry state/result is injected.
            val entry = shell("am start -W --user 0 -n ${client.flattenToString()} --es nativecmpkit.nonce $nonce -f 0x18000000")
            assertEquals(listOf("Status: ok"), entry.lines().filter { it.startsWith("Status:") })
            assertEquals(listOf("Activity: ${client.flattenToString()}"), entry.lines().filter { it.startsWith("Activity:") })
            var observed = "no native receipt/caller snapshot observed"
            waitUntil(failureDetails = { "Owned camera receipt/caller-save condition did not complete: $observed" }) {
                val report = currentReceiver.request("snapshot")
                val caller = snapshot(prefName)
                val kind = caller["kind"]?.let { assertIs<String>(it) } ?: "none"
                check(kind in setOf("none", "captured", "cancelled", "busy", "unavailable", "failed-configuration", "failed-permission", "failed-io", "failed-launch"))
                observed = "creates=${caller.integer("creates")},pidObserved=${caller.integer("pid") > 0}," +
                    "launches=${caller.integer("launches")},resumes=${caller.integer("resumes")},draws=${caller.integer("draws")}," +
                    "saves=${caller.integer("saves")},stops=${caller.integer("stops")},externalLaunches=${caller.integer("externalLaunches")}," +
                    "receivedField=${report.containsKey("received")},received=${report.getBoolean("received")}," +
                    "holding=${report.getBoolean("holdingActivity")},kind=$kind"
                check(caller.integer("results") == 0) { "Unexpected early owned camera terminal result: $kind" }
                if (report.getBoolean("received")) {
                    assertEquals(context.packageName, report.getString("caller"))
                    ownedOutput = outputFor(Uri.parse(assertNotNull(report.getString("uri"))), before)
                }
                report.getBoolean("received") && caller.integer("saves") > 0
            }
            val held = currentReceiver.request("snapshot")
            assertEquals(MediaStore.ACTION_IMAGE_CAPTURE, held.getString("action")); assertEquals(context.packageName, held.getString("caller"))
            assertTrue(held.getBoolean("holdingActivity")); assertTrue(held.getBoolean("readGranted"))
            assertTrue(held.getBoolean("writeGranted")); assertTrue(held.getBoolean("clipMatches"))
            assertEquals(0, held.getInt("opens")); assertEquals(0, held.getInt("closes"))
            val uri = Uri.parse(assertNotNull(held.getString("uri")))
            assertEquals(assertNotNull(ownedOutput), outputFor(uri, before))
            val started = snapshot(prefName)
            assertEquals(nonce, started["nonce"]); assertEquals(Process.myUid(), started.integer("uid"))
            assertTrue(started.integer("orientation") in setOf(Configuration.ORIENTATION_PORTRAIT, Configuration.ORIENTATION_LANDSCAPE))
            val firstPid = started.integer("pid")
            assertTrue(firstPid > 0); assertNotEquals(Process.myPid(), firstPid); assertNotEquals(held.getInt("activityPid"), firstPid)
            assertEquals(1, started.integer("launches")); assertEquals(0, started.integer("results")); assertTrue(started.integer("stops") > 0)
            assertEquals(1, started.integer("externalLaunches")); assertEquals(currentReceiver.recipientUid, started.integer("selectionUid"))
            assertTrue(started.integer("selectionRequestCode") > 0)
            assertEquals(true, started["foregroundLaunch"])
            assertTrue(started.integer("resumes") > 0 && started.integer("draws") > 0)
            assertEquals(delayed, assertNotNull(tasks(nonce).single().taskInfo).topActivity, "External native capture is really foreground")
            if (dontKeep) {
                waitUntil { snapshot(prefName).integer("destroys") > 0 }
                assertEquals(true, snapshot(prefName)["nonFinishingDestroyed"])
            }
            if (rotate) {
                changedRotation = true
                val wasPortrait = started.integer("orientation") == Configuration.ORIENTATION_PORTRAIT
                assertTrue(instrumentation.uiAutomation.setRotation(if (wasPortrait) UiAutomation.ROTATION_FREEZE_90 else UiAutomation.ROTATION_FREEZE_0))
                waitUntil { context.resources.configuration.orientation != started.integer("orientation") }
                assertEquals(delayed, assertNotNull(tasks(nonce).single().taskInfo).topActivity)
            }
            if (kill) {
                killOwnedClient(firstPid) // Actual same-UID SIGKILL, never reporter or a foreign process.
                assertEquals(delayed, assertNotNull(tasks(nonce).single().taskInfo).topActivity)
                assertEquals(0, snapshot(prefName).integer("results"))
            }
            val done = currentReceiver.complete(assertNotNull(held.getString("packet")), cancel)
            assertTrue(done.getBoolean("completed")); assertFalse(done.getBoolean("holdingActivity"))
            assertEquals(cancel, done.getBoolean("cancelled")); assertNull(done.getString("writeError"))
            assertEquals(if (cancel) 0 else 1, done.getInt("opens")); assertEquals(done.getInt("opens"), done.getInt("closes"))
            waitUntil { snapshot(prefName).integer("results") == 1 }
            val terminal = snapshot(prefName)
            assertEquals(1, terminal.integer("launches")); assertEquals(1, terminal.integer("results"))
            assertEquals(1, terminal.integer("externalLaunches")); assertEquals(currentReceiver.recipientUid, terminal.integer("selectionUid"))
            assertEquals(started.integer("selectionRequestCode"), terminal.integer("selectionRequestCode"))
            assertTrue(terminal.integer("creates") >= 2, "Caller Activity really recreated, not an injected restored callback")
            if (kill) assertNotEquals(firstPid, terminal.integer("pid"))
            if (rotate) assertNotEquals(started.integer("orientation"), terminal.integer("orientation"))
            if (cancel) {
                assertEquals("cancelled", terminal["kind"]); assertEquals("", terminal["uri"]); assertEquals(before, outputs())
                assertFailsWith<java.io.FileNotFoundException> { context.contentResolver.openInputStream(uri)!!.use { it.read() } }
            } else {
                assertEquals("captured", terminal["kind"]); assertEquals(uri.toString(), terminal["uri"])
                assertContentEquals(expectedBytes, context.contentResolver.openInputStream(uri)!!.use { it.readBytes() })
                assertEquals(setOf(assertNotNull(ownedOutput).name), outputs() - before)
            }
            waitUntil { tasks(nonce).isEmpty() }; instrumentation.waitForIdleSync()
            assertEquals(1, snapshot(prefName).integer("results")); assertEquals("untouched cache sibling", siblingFile.readText())
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
                for (task in tasks(nonce)) task.finishAndRemoveTask()
                waitUntil { tasks(nonce).isEmpty() }; tasksGone = true
            }
            cleanup {
                receiver?.let { owner ->
                    check(tasksGone)
                    waitUntil { !owner.request("snapshot").getBoolean("holdingActivity") }; externalTerminated = true
                }
            }
            if (changedDelayed) cleanup {
                val owner = assertNotNull(receiver)
                assertDelayedControl(owner, owner.restoreDelayed(nonce), nonce, armed = false)
                assertEquals(originalDelayed, pm.getComponentEnabledSetting(delayed))
                assertFalse(pm.getActivityInfo(delayed, PackageManager.MATCH_DISABLED_COMPONENTS).enabled)
                assertTrue(pm.queryIntentActivities(delayedIntent(), PackageManager.MATCH_DEFAULT_ONLY).isEmpty())
            }
            cleanup { receiver?.close() }
            cleanup {
                val pid = snapshot(prefName).integer("pid")
                if (pid > 0 && processState(pid) == "present") killOwnedClient(pid)
            }
            cleanup {
                // Only this nonce-bound actual EXTRA_OUTPUT, never sweep a cache diff.
                ownedOutput?.let { file ->
                    if (file.exists()) {
                        check(tasksGone && externalTerminated) { "Do not unlink an unverified in-flight external output" }
                        assertTrue(file.delete())
                    }
                }
                assertEquals(before, outputs())
            }
            cleanup { sibling?.let { if (it.exists()) assertTrue(it.delete()) } }
            cleanup { if (preferenceFile(prefName).exists()) assertTrue(context.deleteSharedPreferences(prefName)) }
            if (changedRotation) {
                cleanup { assertTrue(instrumentation.uiAutomation.setRotation(originalRotation)) }
                cleanup { assertTrue(instrumentation.uiAutomation.setRotation(UiAutomation.ROTATION_UNFREEZE)) }
                cleanup { restoreSetting("system", "accelerometer_rotation", originalAutoRotate) }
                cleanup { restoreSetting("system", "user_rotation", originalUserRotation) }
                cleanup { waitUntil { context.getSystemService(WindowManager::class.java).defaultDisplay.rotation == originalRotation } }
            }
            if (changedFinish) cleanup { restoreSetting("global", "always_finish_activities", originalFinish) }
            cleanupFailure?.let { throw it }
        }
    }

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

    private fun tasks(nonce: String): List<ActivityManager.AppTask> {
        // TaskInfo may strip intent extras. Use the real same-UID Activity's committed
        // nonce/task ID, plus exact own component; never guess a task or rely on extras.
        val state = snapshot("nativecmpkit-camera-restoration-$nonce")
        if (state.isEmpty()) return emptyList()
        assertEquals(nonce, state["nonce"]); assertEquals(Process.myUid(), state.integer("uid"))
        val id = state.integer("task").also { check(it > 0) }
        return manager.appTasks.filter { task ->
            // SDK37 explicitly permits null. Never count unavailable information as
            // task absence; read each native snapshot once, not twice across a race.
            val info = assertNotNull(task.taskInfo, "Unknown native task; do not infer absence")
            info.taskId == id && info.baseIntent.component == client
        }
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
    private fun Map<String, Any>.integer(key: String) = get(key)?.let { assertIs<Int>(it) } ?: 0
    private fun preferenceFile(name: String): File {
        check(name.matches(Regex("nativecmpkit-camera-restoration-[a-f0-9]{32}")))
        val root = File(context.applicationInfo.dataDir).canonicalFile.also { check(it.isDirectory) }
        val directory = File(root, "shared_prefs").also {
            check(it.canonicalFile == it); if (it.exists()) check(it.isDirectory)
        }
        return File(directory, "$name.xml").also { check(it.canonicalFile == it) }
    }

    /** Read actual committed native preferences, not cached cross-process SharedPreferences. */
    private fun snapshot(name: String): Map<String, Any> {
        val file = preferenceFile(name)
        if (!file.exists()) return emptyMap()
        check(file.isFile && file.length() in 1..16384)
        val bytes = file.inputStream().use { input ->
            val result = ByteArrayOutputStream(); val block = ByteArray(4096)
            while (true) {
                val n = input.read(block); if (n < 0) break
                check(result.size() + n <= 16384); result.write(block, 0, n)
            }
            result.toByteArray()
        }
        val text = bytes.decodeToString(throwOnInvalidSequence = true)
        check(!text.contains("<!DOCTYPE", ignoreCase = true) && !text.contains("<!ENTITY", ignoreCase = true))
        val allowed = setOf("nonce", "pid", "uid", "task", "creates", "orientation", "results", "kind", "uri", "launches", "saves", "stops", "destroys", "configurationDestroyed", "nonFinishingDestroyed", "externalLaunches", "selectionUid", "selectionRequestCode", "foregroundLaunch", "resumes", "draws", "windowFocused")
        val result = mutableMapOf<String, Any>()
        ByteArrayInputStream(bytes).use { input ->
            val xml = Xml.newPullParser().apply { setInput(input, "UTF-8") }
            var event = xml.eventType
            while (event != XmlPullParser.END_DOCUMENT) {
                check(event != XmlPullParser.DOCDECL)
                if (event == XmlPullParser.START_TAG) {
                    if (xml.depth == 1) check(xml.name == "map")
                    else {
                        check(xml.depth == 2)
                        val key = checkNotNull(xml.getAttributeValue(null, "name")); check(key in allowed && key !in result)
                        result[key] = when (xml.name) {
                            "string" -> xml.nextText()
                            "int" -> checkNotNull(xml.getAttributeValue(null, "value")).toInt()
                            "boolean" -> checkNotNull(xml.getAttributeValue(null, "value")).toBooleanStrict()
                            else -> error("Unknown owned native preference type")
                        }
                    }
                }
                event = xml.next()
            }
        }
        return result
    }
    private fun processState(pid: Int): String {
        check(pid > 0 && pid != Process.myPid())
        return try {
            check(OsConstants.S_ISDIR(Os.stat("/proc/$pid").st_mode))
            "present"
        } catch (failure: ErrnoException) {
            // File.exists()/isDirectory() hide EACCES as false. Refuse all unknown
            // native errors; only actual kernel absence can satisfy the death check.
            if (failure.errno == OsConstants.ENOENT || failure.errno == OsConstants.ESRCH) "absent"
            else throw failure
        }
    }
    private fun killOwnedClient(pid: Int) {
        check(pid > 0 && pid != Process.myPid())
        assertEquals(processName, ownedClientCommandline(pid))
        Process.killProcess(pid)
        waitUntil { processState(pid) == "absent" }
    }
    private fun ownedClientCommandline(pid: Int): String {
        check(pid > 0 && pid != Process.myPid())
        val commandline = File("/proc/$pid/cmdline")
        assertEquals(Process.myUid(), Os.stat(commandline.path).st_uid, "Refuse a foreign/reused native PID")
        val bytes = commandline.inputStream().use { input ->
            val result = ByteArrayOutputStream(); val block = ByteArray(256)
            while (true) {
                val n = input.read(block); if (n < 0) break
                check(n > 0 && result.size() + n <= 4096) { "Unbounded owned native process name" }
                result.write(block, 0, n)
            }
            result.toByteArray()
        }
        check(bytes.isNotEmpty()) { "Unknown native process name" }
        return bytes.decodeToString(throwOnInvalidSequence = true).trimEnd('\u0000')
    }
    private fun setting(namespace: String, key: String, allowed: Set<String>) = shell("settings get $namespace $key").also { check(it in allowed) }
    private fun restoreSetting(namespace: String, key: String, value: String) {
        if (value == "null") assertEquals("Deleted 1 rows", shell("settings delete $namespace $key"))
        else assertEquals("", shell("settings put $namespace $key $value"))
        assertEquals(value, shell("settings get $namespace $key"))
    }
    private fun shell(command: String): String {
        val descriptor = instrumentation.uiAutomation.executeShellCommand(command)
        return ParcelFileDescriptor.AutoCloseInputStream(descriptor).use { input ->
            val result = ByteArrayOutputStream(); val block = ByteArray(4096)
            val deadline = SystemClock.uptimeMillis() + 10_000
            val poll = StructPollfd().apply { fd = descriptor.fileDescriptor; events = (OsConstants.POLLIN or OsConstants.POLLHUP).toShort() }
            while (true) {
                val remaining = deadline - SystemClock.uptimeMillis(); check(remaining > 0) { "Owned camera control read timed out" }
                check(Os.poll(arrayOf(poll), remaining.toInt()) > 0) { "Owned camera control read timed out" }
                check(poll.revents.toInt() and (OsConstants.POLLERR or OsConstants.POLLNVAL) == 0)
                val n = input.read(block); if (n < 0) break
                check(n > 0 && result.size() + n <= 65536) { "Unbounded owned camera control reply" }
                result.write(block, 0, n)
            }
            result.toByteArray().decodeToString(throwOnInvalidSequence = true).trim()
        }
    }
    private fun waitUntil(failureDetails: () -> String = { "Owned native camera condition did not complete" }, condition: () -> Boolean) {
        val start = System.nanoTime()
        while (!condition()) { check(System.nanoTime() - start < 30_000_000_000L) { failureDetails() }; Thread.sleep(30) }
    }
}
