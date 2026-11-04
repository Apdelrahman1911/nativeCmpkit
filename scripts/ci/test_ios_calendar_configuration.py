"""Important calendar source-contract regressions only; these are NOT EventKit/native privacy executions."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
CALENDAR = ROOT / "calf-permissions/calendar"
HELPER = CALENDAR / "src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionHelper.kt"
POLICY = CALENDAR / "src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/helper/CalendarPermissionPolicy.kt"
NATIVE = CALENDAR / "src/iosTest/kotlin/com/mohamedrejeb/calf/permissions/helper/NativeCalendarConfigurationTest.kt"
COMMON = CALENDAR / "src/commonTest/kotlin/com/mohamedrejeb/calf/permissions/helper/CalendarConfigurationTest.kt"

NATIVE_METHODS = (
    "nativeSelectorsMatchTheRunningIOSVersionAndSelectedRequestKind",
    "passivePublicHelpersMatchActualEventKitWithoutPromptingOrChangingAuthorization",
    "freshUnconfiguredPublicRequestsFailOnceWithoutEnteringEventKitPrivacy",
    "backgroundEntryAndReentrantConfigurationFailuresAreMainConfinedAndRecoverable",
    "nativeBundleLookupHonorsLocalizedPurposeStringsAndRejectsOtherModeKeys",
)


def body(source: str, marker: str) -> str:
    """Extract one unique Kotlin block with balanced braces (owning source has no unmatched string braces)."""
    if source.count(marker) != 1:
        raise ValueError("Use the single owning Kotlin declaration")
    start = source.index("{", source.index(marker))
    depth = 1
    for end in range(start + 1, len(source)):
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1:end]
    raise ValueError("Unbalanced owning Kotlin block")


class IOSCalendarConfigurationControls(unittest.TestCase):
    def test_exact_three_request_keys_are_never_interchangeable(self):
        policy = POLICY.read_text()
        mapping = body(policy, "internal fun calendarUsageDescriptionKey(")
        for mode, key in (("Legacy", "NSCalendarsUsageDescription"),
                          ("FullAccess", "NSCalendarsFullAccessUsageDescription"),
                          ("WriteOnly", "NSCalendarsWriteOnlyAccessUsageDescription")):
            self.assertIn(f'CalendarRequestKind.{mode} -> "{key}"', mapping)
        self.assertEqual(3, len(re.findall(r'-> "NSCalendars\w+"', mapping)))
        self.assertIn("value is String && value.isNotBlank()", policy)

    def test_missing_key_returns_configuration_failure_before_any_native_request(self):
        launch = body(HELPER.read_text(), "override fun launchPermissionRequest(")
        failure = body(launch, "if (!calendarUsageDescriptionConfigured(kind))")
        self.assertIn("outcome = PermissionRequestOutcome.ConfigurationError", failure)
        self.assertIn("onPermissionResult(false)", failure)
        self.assertIn("return@handleLaunchPermissionRequest", failure)
        self.assertNotIn("store.request", failure)
        guard = launch.index("if (!calendarUsageDescriptionConfigured(kind))")
        for request in ("store.requestAccessToEntityType(", "store.requestFullAccessToEventsWithCompletion(",
                        "store.requestWriteOnlyAccessToEventsWithCompletion("):
            self.assertGreater(launch.index(request), guard)
            self.assertEqual(1, launch.count(request))
        self.assertIn("when (kind)", launch)

    def test_requests_snapshots_and_native_completions_are_main_confined(self):
        source = HELPER.read_text()
        launch = body(source, "override fun launchPermissionRequest(").strip()
        observe = body(source, "override fun getPermissionSnapshot(").strip()
        self.assertTrue(launch.startswith("// Direct helper callers"))
        self.assertLess(launch.index("runOnPermissionMainThread {"), launch.index("outcome = null"))
        self.assertTrue(observe.startswith("runOnPermissionMainThread {"))
        completion = body(launch, "val completion:")
        self.assertLess(completion.index("runOnPermissionMainThread {"), completion.index("outcome ="))

    def test_localized_bundle_lookup_is_not_replaced_with_raw_dictionary_or_fallback(self):
        source = HELPER.read_text()
        self.assertIn("bundle: NSBundle = NSBundle.mainBundle", source)
        self.assertIn("bundle.objectForInfoDictionaryKey(calendarUsageDescriptionKey(kind))", source)
        self.assertNotIn("bundle.infoDictionary", source)
        self.assertNotIn("localizedInfoDictionary ?: ", source)
        self.assertNotIn("NSCalendarsUsageDescription", source,
                         "The native guard obtains exactly the selected policy key, never a guessed legacy fallback")

    def test_configuration_error_is_not_reported_as_native_denial_or_permanent_rationale(self):
        observe = body(HELPER.read_text(), "override fun getPermissionSnapshot(")
        self.assertIn("lastRequest = outcome", observe)
        self.assertIn("outcome == PermissionRequestOutcome.ConfigurationError", observe)
        self.assertIn("snapshot.details.requestability == PermissionRequestability.Requestable", observe)
        self.assertIn("PermissionRequestability.PrerequisiteRequired else snapshot.details.requestability", observe)
        self.assertNotIn("PermissionStatus.Denied(true)", observe)

    def test_public_read_write_modes_remain_separate(self):
        source = (CALENDAR / "src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/CalendarPermissions.ios.kt").read_text()
        self.assertIn("CalendarPermissionHelper(CalendarAccessMode.Read)", body(source, "registerReadCalendarPermission("))
        self.assertIn("CalendarPermissionHelper(CalendarAccessMode.Write)", body(source, "registerWriteCalendarPermission("))

    def test_new_native_methods_require_real_undetermined_privacy_and_darwin_execution(self):
        source = NATIVE.read_text()
        self.assertEqual(NATIVE_METHODS, tuple(re.findall(r"@Test fun (\w+)\(", source)))
        self.assertIn("EKEventStore.authorizationStatusForEntityType(", source)
        self.assertIn("native.respondsToSelector(NSSelectorFromString(", source)
        self.assertIn("assertEquals(EKAuthorizationStatusNotDetermined, eventAuthorization()", source)
        self.assertIn("dispatch_async(dispatch_get_global_queue(0, 0u))", source)
        self.assertIn("NSRunLoop.mainRunLoop.runUntilDate(", source)
        self.assertIn("NSBundle.bundleWithPath(directory)", source)
        self.assertIn("manager.removeItemAtPath(directory, null)", source)
        for forbidden in ("Dispatchers.setMain", "mockk(", "simctl privacy", ".requestWriteOnlyAccessToEventsWithCompletion(",
                          ".requestFullAccessToEventsWithCompletion(", "saveEvent(", "eventsMatchingPredicate("):
            self.assertNotIn(forbidden, source)

    def test_new_common_selection_never_replays_accepted_capability_policy_methods(self):
        source = COMMON.read_text()
        self.assertEqual(("everyRequestKindRequiresItsOwnExactPurposeKey",
                          "absentBlankAndNonStringPurposeValuesCannotAuthorizeANativeRequest",
                          "aDifferentAccessKeyCannotSatisfyTheSelectedRequest"),
                         tuple(re.findall(r"@Test fun (\w+)\(", source)))
        self.assertNotIn("CalendarPermissionPolicyTest", source)


if __name__ == "__main__":
    unittest.main()
