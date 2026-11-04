@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class,
    kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import platform.EventKit.*
import platform.Foundation.*
import platform.UIKit.UIDevice
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_global_queue
import platform.darwin.dispatch_get_main_queue
import kotlin.test.*

/**
 * Real EventKit selectors/status, NSBundle localized configuration, Darwin queues and registered library helpers.
 * The test executable must have fresh NotDetermined privacy and NO calendar purpose keys. No request below may
 * reach native privacy UI; no event/calendar data is read or written. Fixture bundles test configuration only,
 * never substitute for the main bundle in EventKit. This is NOT consent/Settings/old-OS/physical-device proof.
 */
class NativeCalendarConfigurationTest {
    @Test fun nativeSelectorsMatchTheRunningIOSVersionAndSelectedRequestKind() {
        requireMain()
        val major = runningMajorVersion()
        val native = EKEventStore()
        assertTrue(native.respondsToSelector(NSSelectorFromString("requestAccessToEntityType:completion:")))
        val full = native.respondsToSelector(NSSelectorFromString("requestFullAccessToEventsWithCompletion:"))
        val write = native.respondsToSelector(NSSelectorFromString("requestWriteOnlyAccessToEventsWithCompletion:"))
        assertEquals(major >= 17, full, "Actual full-access selector availability, not an injected SDK version")
        assertEquals(major >= 17, write, "Actual write-only selector availability, not an injected SDK version")
        assertEquals(if (major >= 17) CalendarRequestKind.FullAccess else CalendarRequestKind.Legacy,
            calendarRequestKind(major, CalendarAccessMode.Read))
        assertEquals(if (major >= 17) CalendarRequestKind.WriteOnly else CalendarRequestKind.Legacy,
            calendarRequestKind(major, CalendarAccessMode.Write))
    }

    @Test fun passivePublicHelpersMatchActualEventKitWithoutPromptingOrChangingAuthorization() {
        requireMain()
        val before = eventAuthorization()
        val authorization = when (before) {
            EKAuthorizationStatusAuthorized -> CalendarAuthorization.Full
            EKAuthorizationStatusWriteOnly -> CalendarAuthorization.WriteOnly
            EKAuthorizationStatusNotDetermined -> CalendarAuthorization.NotDetermined
            EKAuthorizationStatusDenied -> CalendarAuthorization.Denied
            EKAuthorizationStatusRestricted -> CalendarAuthorization.Restricted
            else -> CalendarAuthorization.Unknown
        }
        for ((permission, mode) in publicModes()) {
            val helper = PermissionDelegateRegistry.getDelegate(permission)
            assertTrue(helper is CalendarPermissionHelper, "Use the actual library registration, not a replacement backend")
            val snapshot = snapshot(helper)
            assertEquals(calendarSnapshot(authorization, mode), snapshot)
            assertNull(snapshot.details.lastRequest, "Passive status reads cannot manufacture a request outcome")
        }
        assertEquals(before, eventAuthorization(), "Passive helper creation/query cannot alter native authorization")
    }

    @Test fun freshUnconfiguredPublicRequestsFailOnceWithoutEnteringEventKitPrivacy() {
        requireMain()
        requireFreshUnconfiguredProcess()
        for ((permission, _) in publicModes()) {
            val helper = PermissionDelegateRegistry.getDelegate(permission)
            val results = mutableListOf<Boolean>()
            helper.launchPermissionRequest { result ->
                requireMain()
                results += result
            }
            assertEquals(listOf(false), results, "A missing purpose key must complete synchronously once on Main")
            val after = snapshot(helper)
            assertFalse(after.status.isGranted)
            assertFalse(after.status.shouldShowRationale, "App configuration is not a permanent OS denial")
            assertEquals(PermissionRequestOutcome.ConfigurationError, after.details.lastRequest)
            assertEquals(PermissionRequestability.PrerequisiteRequired, after.details.requestability)
            assertEquals(EKAuthorizationStatusNotDetermined, eventAuthorization(),
                "A safe configuration refusal must leave actual privacy authorization untouched")
            // Pump a real main-loop barrier so an accidentally deferred second delivery cannot hide.
            var barrier = false
            dispatch_async(dispatch_get_main_queue()) { barrier = true }
            await("native post-refusal main-loop barrier") { barrier }
            assertEquals(listOf(false), results)
        }
    }

    @Test fun backgroundEntryAndReentrantConfigurationFailuresAreMainConfinedAndRecoverable() {
        requireMain()
        requireFreshUnconfiguredProcess()
        val helper = CalendarPermissionHelper(CalendarAccessMode.Write)
        val results = mutableListOf<Boolean>()
        val callbackErrors = mutableListOf<Throwable>()
        val lock = NSLock()
        var actualBackground = false
        var barrier = false
        dispatch_async(dispatch_get_global_queue(0, 0u)) {
            lock.lock()
            try { actualBackground = !NSThread.isMainThread } finally { lock.unlock() }
            helper.launchPermissionRequest { first ->
                try {
                    requireMain()
                    results += first
                    assertEquals(PermissionRequestOutcome.ConfigurationError, snapshot(helper).details.lastRequest)
                    helper.launchPermissionRequest { second ->
                        requireMain()
                        results += second
                        assertEquals(PermissionRequestOutcome.ConfigurationError, snapshot(helper).details.lastRequest)
                    }
                } catch (failure: Throwable) {
                    callbackErrors += failure
                } finally {
                    dispatch_async(dispatch_get_main_queue()) { barrier = true }
                }
            }
        }
        await("actual background-entry/reentrant-request main-loop completion") { barrier }
        callbackErrors.firstOrNull()?.let { throw it }
        lock.lock()
        val observedBackground = try { actualBackground } finally { lock.unlock() }
        assertTrue(observedBackground, "The real Darwin background queue must execute, not an injected dispatcher")
        assertEquals(listOf(false, false), results, "Each reentrant request completes once; neither consumes the next")
        assertEquals(EKAuthorizationStatusNotDetermined, eventAuthorization())
    }

    @Test fun nativeBundleLookupHonorsLocalizedPurposeStringsAndRejectsOtherModeKeys() {
        requireMain()
        val manager = NSFileManager.defaultManager
        val directory = "${NSTemporaryDirectory().removeSuffix("/")}/nativecmpkit-calendar-${NSUUID().UUIDString}.bundle"
        assertTrue(manager.createDirectoryAtPath(directory, false, null, null))
        try {
            assertTrue(manager.createDirectoryAtPath("$directory/en.lproj", false, null, null))
            writeText("$directory/Info.plist", """<?xml version="1.0" encoding="UTF-8"?>
                <plist version="1.0"><dict>
                <key>CFBundleIdentifier</key><string>io.github.apdelrahman1911.nativecmpkit.calendar.configuration-test</string>
                <key>CFBundleDevelopmentRegion</key><string>en</string>
                <key>CFBundlePackageType</key><string>BNDL</string>
                <key>NSCalendarsFullAccessUsageDescription</key><string> </string>
                </dict></plist>""".trimIndent())
            writeText("$directory/en.lproj/InfoPlist.strings",
                "\"NSCalendarsFullAccessUsageDescription\" = \"Read selected synthetic events\";")
            val bundle = assertNotNull(NSBundle.bundleWithPath(directory))
            assertEquals(" ", bundle.infoDictionary?.get("NSCalendarsFullAccessUsageDescription"))
            assertEquals("Read selected synthetic events", bundle.objectForInfoDictionaryKey("NSCalendarsFullAccessUsageDescription"))
            assertTrue(calendarUsageDescriptionConfigured(CalendarRequestKind.FullAccess, bundle),
                "Localized purpose strings must not be rejected by inspecting only the raw plist")
            assertFalse(calendarUsageDescriptionConfigured(CalendarRequestKind.WriteOnly, bundle))
            assertFalse(calendarUsageDescriptionConfigured(CalendarRequestKind.Legacy, bundle))
        } finally {
            assertTrue(manager.removeItemAtPath(directory, null), "Remove only the unique owned fixture bundle")
            assertFalse(manager.fileExistsAtPath(directory))
        }
    }

    private fun publicModes() = listOf(Permission.ReadCalendar to CalendarAccessMode.Read,
        Permission.WriteCalendar to CalendarAccessMode.Write)

    private fun eventAuthorization() = EKEventStore.authorizationStatusForEntityType(EKEntityType.EKEntityTypeEvent)

    private fun runningMajorVersion(): Int = assertNotNull(UIDevice.currentDevice.systemVersion.substringBefore('.').toIntOrNull())
        .also { assertTrue(it > 0, "Unknown native system version is not an old-OS availability witness") }

    private fun requireFreshUnconfiguredProcess() {
        assertEquals(EKAuthorizationStatusNotDetermined, eventAuthorization(),
            "This finite refusal profile requires fresh OS privacy, not a reused granted or denied app")
        for (kind in CalendarRequestKind.entries) {
            assertNull(NSBundle.mainBundle.objectForInfoDictionaryKey(calendarUsageDescriptionKey(kind)),
                "Run in the no-purpose-key native test executable, never a configured sample or existing app")
        }
    }

    private fun snapshot(helper: PermissionHelper): PermissionSnapshot {
        var calls = 0
        var value: PermissionSnapshot? = null
        helper.getPermissionSnapshotCompat { current -> requireMain(); calls++; value = current }
        assertEquals(1, calls, "Main-thread native status must complete exactly once")
        return assertNotNull(value)
    }

    private fun requireMain() { assertTrue(NSThread.isMainThread, "The actual Foundation main queue owns helper state") }

    private fun await(phase: String, complete: () -> Boolean) {
        val deadline = NSProcessInfo.processInfo.systemUptime + 10.0
        do {
            NSRunLoop.mainRunLoop.runUntilDate(NSDate.dateWithTimeIntervalSinceNow(0.002))
            if (complete()) return
        } while (NSProcessInfo.processInfo.systemUptime < deadline)
        error("Timed out awaiting $phase")
    }

    private fun writeText(path: String, value: String) {
        assertTrue(NSString.create(string = value).writeToFile(path, true, NSUTF8StringEncoding, null))
    }
}
