"""Exact, source-bound native JNI scenario eligibility; never a general skip list.

Only two logically host-inapplicable cases may remain skipped. A required macOS
AppKit case must execute with explicit GUI opt-in; headless/opt-out is not N/A.
Single-host evidence cannot establish the complete cross-host native matrix.
The new iOS IO/Coil regressions have no skip/N/A allowance: every exact required
native case must execute on the Apple host with the observed KGP task/target identity.
"""
from __future__ import annotations

MODULE = "calf-share"
CLASS = "com.mohamedrejeb.calf.share.platform.NativeShareBridgeTest"
SOURCE = "calf-share/src/desktopTest/kotlin/com/mohamedrejeb/calf/share/platform/NativeShareBridgeTest.kt"
ALL_HOSTS = (
    "nativeAbiAndDiagnosticsLoadOnTheActualHost",
    "borrowedNativeWindowPointersAreRejectedWithoutDereference",
)
NON_MAC = "unsupportedHostRequestsAndCancellationNeverRetainNativeOwners"
MAC_GUI = "macOsPickerCancellationReleasesRealMainThreadOwners"
REQUIRED_CASES = (*ALL_HOSTS, NON_MAC, MAC_GUI)
DESKTOP_WEBVIEW_STOP_CASES = (
    "stopCancelsRealSlowLoadWithoutFeedbackLoop",
    "repeatedStopsAfterDetachAndReattachCancelOnlyTheCurrentRealLoad",
)
DESKTOP_WEBVIEW_LIFETIME_CASES = (
    "retainedStateCannotRetainRepeatedRealNativeViewsOrEngines",
    "throwingDisposeCannotKeepItsViewOrStopAnotherRealWindow",
    "disposingARealWindowClosesItsSlowConnectionAndStopsTheLiveMediaDocument",
)
ANDROID_WEBVIEW_LIFETIME_CASES = (
    "retainedStateReleasesRepeatedRealActivitiesAndViewsAndRestoresSerializedNativeState",
    "compositionDisposalClosesItsRealSlowConnectionAndStopsTheLiveMediaDocument",
    "throwingNativeReleaseCannotRetainItsActivityViewOrClearTheLiveReplacement",
)
IOS_IO_CASES = {
    "calf-io": tuple(
        ("com.mohamedrejeb.calf.io." + classname, method,
         "calf-io/src/iosTest/kotlin/com/mohamedrejeb/calf/io/" + classname + ".kt")
        for classname, methods in (
            ("NativeReadSafetyTest", (
                "readsARealEmptyNSDataFileWithoutAddressOfZero",
                "realNativeMemcpyAndStreamHaveIdenticalBinaryBytes",
                "missingFileIsNotEmptyOrAFile",
                "readsARealOneByteNSDataFile",
                "unreadableFileIsNotSilentlyConvertedToEmptyData",
            )),
            ("NativeGuardedCopyTest", (
                "emptyFoundationDataNeedsNoPointer",
                "validatedFoundationCopyDoesNotCrossSourceOrDestinationGuardPages",
                "tooSmallGuardedDestinationIsRejectedBeforeAnyNativeWrite",
                "positiveLengthNeedsANonNullDestination",
                "nativeLengthBoundaryRejectsUnrepresentableCountsWithoutAllocation",
            )),
            ("NativeSourceLifecycleTest", (
                "rawNativeSourceOpenReadAndRepeatedCloseReleaseOnlyItsDescriptor",
                "boundedRealNativeSourceClosesOnLimitFailure",
                "cancellationAtTheFirstNativeReadYieldClosesTheActualStream",
                "repeatedNativeSourceAndWholeFileReadsLeaveNoOwnedDescriptors",
                "failureWhileConsumingARealNativeSourceClosesViaUse",
            )),
        ) for method in methods
    ),
    "calf-file-picker-coil": tuple(
        ("com.mohamedrejeb.calf.picker.coil.NativeKmpFileFetcherTest", method,
         "calf-file-picker-coil/src/iosTest/kotlin/com/mohamedrejeb/calf/picker/coil/NativeKmpFileFetcherTest.kt")
        for method in (
            "realCoilStreamingSourceHasExactBytesAndOwnedDescriptor",
            "missingAndUnreadableFilesPropagateThroughActualCoilRequests",
            "nonFileUrlsFailBeforeOpeningMatchingLocalContent",
            "cancelledFetchCannotOpenADescriptor",
            "repeatedImageSourceCloseAndFetchReleaseRealNativeDescriptors",
            "actualCoilDecoderCancellationClosesTransferredNativeSource",
            "actualCoilDecoderFailureClosesTransferredNativeSource",
        )
    ),
}


def ios_io_cases(module: str, cases: list[dict], system: str) -> tuple[list[dict], list[str]]:
    host = canonical_host(system)
    scenarios, errors = [], []
    if host != "macos":
        errors.append("iOS IO/Coil requires actual Apple-host execution; Linux cross-compilation is not a native pass")
    for classname, method, source in IOS_IO_CASES[module]:
        matching = [case for case in cases if case["classname"] == "iosSimulatorArm64Test." + classname
                    and case["name"] == method + "[iosSimulatorArm64]"]
        scenario = {"classname": classname, "method": method, "source": source, "host": host,
                    "required_on_host": True, "task": "iosSimulatorArm64Test", "target": "iosSimulatorArm64"}
        if len(matching) != 1:
            errors.append(f"Native IO/Coil scenario {method} must appear exactly once in fresh iOS XML")
            scenario["disposition"] = "missing-or-duplicate"
        elif host != "macos":
            scenario["disposition"] = "invalid-host-outcome"
        else:
            scenario["disposition"] = "required-executed" if matching[0]["status"] == "passed" else "required-not-passed"
            if matching[0]["status"] != "passed":
                errors.append(f"Required native IO/Coil scenario {method} did not pass; skipped is not N/A")
        scenarios.append(scenario)
    return scenarios, errors


def canonical_host(system: str) -> str:
    aliases = {"linux": "linux", "windows": "windows", "win32": "windows",
               "darwin": "macos", "mac": "macos", "macos": "macos", "mac os x": "macos"}
    if not isinstance(system, str) or system.strip().lower() not in aliases:
        raise ValueError("Unrecognized native scenario host; do not guess applicability")
    return aliases[system.strip().lower()]


PICKER_COMPOSE_CLASS = "com.mohamedrejeb.calf.picker.NativePickerComposeLifetimeTest"
PICKER_COMPOSE_SOURCE = "calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/NativePickerComposeLifetimeTest.kt"
PICKER_COMPOSE_METHODS = (
    "composeDisposalBeforeQueuedJniEntryDoesNotAllocateOrShow",
    "composeDisposalInsideRealJniCreationHandoffClosesExactlyOnce",
    "retainedComposeLauncherSnapshotsLimitsParentsAndLatestCallbackPerNativeSession",
    "firstPublicCompositionLaunchAndSettingsUpdatesUseOneActualNativeDialog",
    "closingComposeWindowWithAnActualDialogVisibleCancelsDeliveryNotNativeOwnership",
    "closingTheRealRegistryIdWhileItsDialogIsVisibleKeepsTheShowLeaseValid",
)
PICKER_LINUX_PORTAL_METHODS = set(PICKER_COMPOSE_METHODS[3:])

PICKER_PORTAL_CLASS = "com.mohamedrejeb.calf.picker.NativeLinuxPortalFunctionalityTest"
PICKER_PORTAL_SOURCE = "calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/NativeLinuxPortalFunctionalityTest.kt"
PICKER_PORTAL_METHODS = (
    "singleAndMultipleOpenReturnExactRealFilesWithoutChangingTheirBytes",
    "folderAndSaveDialogsReturnTheSelectedDirectoryAndExactEmptyAndBinaryFiles",
    "cancellingEachDialogLeavesSourcesUntouchedAndAFreshNativeSessionCanStillOpen",
)


def picker_portal_cases(cases: list[dict], system: str) -> tuple[list[dict], list[str]]:
    host = canonical_host(system)
    scenarios, errors = [], []
    for method in PICKER_PORTAL_METHODS:
        matching = [c for c in cases if c["classname"] == PICKER_PORTAL_CLASS and c["name"] == method + "[desktop]"]
        scenario = {"classname": PICKER_PORTAL_CLASS, "method": method, "source": PICKER_PORTAL_SOURCE,
                    "host": host, "required_on_host": host == "linux", "task": "desktopTest"}
        if len(matching) != 1:
            errors.append(f"Real GTK functionality method {method} must appear exactly once")
            scenario["disposition"] = "missing-or-duplicate"
        elif host != "linux":
            if matching[0]["status"] != "skipped":
                errors.append(f"Linux-only GTK functionality method {method} must be explicit N/A elsewhere")
                scenario["disposition"] = "invalid-host-outcome"
            else:
                matching[0].update(disposition="not-applicable", not_applicable_reason="Real GTK portal scenario is Linux-only")
                scenario["disposition"] = "not-applicable"
        else:
            scenario["disposition"] = "required-executed" if matching[0]["status"] == "passed" else "required-not-passed"
            if matching[0]["status"] != "passed":
                errors.append(f"Real GTK functionality method {method} must pass; missing UI/bus is not N/A")
        scenarios.append(scenario)
    return scenarios, errors


def picker_compose_cases(cases: list[dict], system: str) -> tuple[list[dict], list[str]]:
    host = canonical_host(system)
    scenarios, errors = [], []
    for method in PICKER_COMPOSE_METHODS:
        matching = [c for c in cases if c["classname"] == PICKER_COMPOSE_CLASS and c["name"] == method + "[desktop]"]
        applicable = host == "linux" or method not in PICKER_LINUX_PORTAL_METHODS
        scenario = {"classname": PICKER_COMPOSE_CLASS, "method": method, "source": PICKER_COMPOSE_SOURCE,
                    "host": host, "required_on_host": applicable, "task": "desktopTest"}
        if len(matching) != 1:
            errors.append(f"Picker native lifetime method {method} must appear exactly once")
            scenario["disposition"] = "missing-or-duplicate"
        elif not applicable:
            if matching[0]["status"] != "skipped":
                errors.append(f"Linux-only real GTK portal method {method} must be explicit N/A on this host")
                scenario["disposition"] = "invalid-host-outcome"
            else:
                matching[0].update(disposition="not-applicable", not_applicable_reason="Linux private GTK/FileChooser portal scenario, not a Windows/AppKit UI test")
                scenario["disposition"] = "not-applicable"
        else:
            scenario["disposition"] = "required-executed" if matching[0]["status"] == "passed" else "required-not-passed"
            if matching[0]["status"] != "passed":
                errors.append(f"Required actual Compose/JNI lifetime method {method} failed/errored/skipped; no missing-native waiver")
        scenarios.append(scenario)
    return scenarios, errors


def apply(module: str, suite: str, cases: list[dict], system: str,
          native_ui_opt_in: bool) -> tuple[list[dict], list[str]]:
    if module == "calf-file-picker" and suite == "desktop":
        scenarios, errors = picker_compose_cases(cases, system)
        portal_scenarios, portal_errors = picker_portal_cases(cases, system)
        return scenarios + portal_scenarios, errors + portal_errors
    if suite == "ios" and module in IOS_IO_CASES:
        return ios_io_cases(module, cases, system)
    if module == "calf-webview" and suite == "desktop":
        host = canonical_host(system)
        scenarios, errors = [], []
        classname = "com.mohamedrejeb.calf.ui.web.JavaFxWebViewTest"
        source = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/JavaFxWebViewTest.kt"
        registry = [(classname, method, source) for method in DESKTOP_WEBVIEW_STOP_CASES]
        registry += [("com.mohamedrejeb.calf.ui.web.DesktopWebViewLifetimeTest", method,
                      "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewLifetimeTest.kt")
                     for method in DESKTOP_WEBVIEW_LIFETIME_CASES]
        for classname, method, source in registry:
            matching = [case for case in cases if case["classname"] == classname
                        and case["name"] in {method, method + "[desktop]"}]
            scenario = {"classname": classname, "method": method, "source": source,
                        "host": host, "required_on_host": True, "task": "desktopTest"}
            if len(matching) != 1:
                errors.append(f"Native JavaFX stop scenario {method} must appear exactly once in fresh desktop XML")
                scenario["disposition"] = "missing-or-duplicate"
            else:
                scenario["disposition"] = "required-executed" if matching[0]["status"] == "passed" else "required-not-passed"
                if matching[0]["status"] != "passed":
                    errors.append(f"Required JavaFX window/stop scenario {method} did not pass; headless/skipped is not N/A")
            scenarios.append(scenario)
        return scenarios, errors
    if module == "calf-webview" and suite == "android-device":
        host = canonical_host(system)
        scenarios, errors = [], []
        if host != "linux":
            errors.append("Android device WebView policy requires the explicit Linux enforcing-emulator slot")
        registry = [("com.mohamedrejeb.calf.ui.web.AndroidWebViewHistoryDeviceTest",
                     "navigatorReplacementReadsRealBrowserHistoryWithoutAnotherPageEvent",
                     "calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewHistoryDeviceTest.kt")]
        registry += [("com.mohamedrejeb.calf.ui.web.AndroidWebViewLifetimeDeviceTest", method,
                      "calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewLifetimeDeviceTest.kt")
                     for method in ANDROID_WEBVIEW_LIFETIME_CASES]
        for classname, method, source in registry:
            matching = [c for c in cases if c["classname"] == classname and c["name"] == method]
            scenario = {"classname": classname, "method": method, "source": source, "host": host,
                        "required_on_host": True, "task": "connectedAndroidDeviceTest"}
            if len(matching) != 1:
                errors.append(f"Real Android WebView scenario {method} must appear exactly once")
                scenario["disposition"] = "missing-or-duplicate"
            else:
                scenario["disposition"] = "required-executed" if matching[0]["status"] == "passed" and host == "linux" else "required-not-passed"
                if matching[0]["status"] != "passed":
                    errors.append(f"Real Android WebView scenario {method} failed/errored/skipped; host substitutes are not N/A")
            scenarios.append(scenario)
        return scenarios, errors
    if module != MODULE or suite != "desktop":
        return [], []
    host = canonical_host(system)
    scenarios, errors = [], []
    for method in REQUIRED_CASES:
        matching = [case for case in cases if case["classname"] == CLASS and
                    case["name"] in {method, method + "[desktop]"}]
        applicable = method in ALL_HOSTS or (method == NON_MAC and host != "macos") or (method == MAC_GUI and host == "macos")
        scenario = {"classname": CLASS, "method": method, "source": SOURCE, "host": host,
                    "required_on_host": applicable, "native_ui_opt_in_requested": native_ui_opt_in if method == MAC_GUI and applicable else None}
        if len(matching) != 1:
            errors.append(f"Native scenario {method} must appear exactly once, including explicit host N/A evidence")
            scenario["disposition"] = "missing-or-duplicate"
        else:
            case = matching[0]
            if not applicable:
                if case["status"] != "skipped":
                    errors.append(f"Host-inapplicable native scenario {method} must be reported N/A, not executed or counted passed")
                    scenario["disposition"] = "invalid-host-outcome"
                else:
                    case["disposition"] = "not-applicable"
                    case["not_applicable_reason"] = "AppKit-only scenario on non-macOS" if method == MAC_GUI else "Unavailable-native-sharing contract does not apply to macOS"
                    scenario["disposition"] = "not-applicable"
            else:
                scenario["disposition"] = "required-executed" if case["status"] == "passed" else "required-not-passed"
                if case["status"] != "passed":
                    errors.append(f"Required native scenario {method} did not pass; skipped/headless/opt-out is not N/A")
                if method == MAC_GUI and native_ui_opt_in is not True:
                    errors.append("The required macOS AppKit GUI scenario needs explicit NATIVECMPKIT_NATIVE_UI_TESTS=true")
        scenarios.append(scenario)
    return scenarios, errors
