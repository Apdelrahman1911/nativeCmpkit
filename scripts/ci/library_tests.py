#!/usr/bin/env python3
"""Fresh, bounded library test runs with source-bound, sanitized JUnit receipts.

This repository-specific runner deliberately has no arbitrary Gradle arguments,
publication command, source fallback, arbitrary skip list, or cached-report
success path. Two exact native host-inapplicable scenarios are reported N/A,
never counted as passed; every applicable native scenario remains required.
It is NOT a sandbox or a trusted-builder attestation. Coordinate other builds;
its lock covers only other invocations of this helper in the same checkout.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import runtime_context
import native_test_policy
import daemon_jvm

ROOT = Path(__file__).resolve().parents[2]
SUITES = {
    "desktop": ("desktopTest", ("commonTest", "materialTest", "nonAndroidTest", "desktopTest")),
    "android-host": ("testAndroidHostTest", ("commonTest", "materialTest", "androidHostTest")),
    "android-device": ("connectedAndroidDeviceTest", ("commonTest", "materialTest", "androidDeviceTest")),
    "js": ("jsBrowserTest", ("commonTest", "materialTest", "nonAndroidTest", "webTest", "jsTest")),
    "wasm": ("wasmJsBrowserTest", ("commonTest", "materialTest", "nonAndroidTest", "webTest", "wasmJsTest")),
    "ios": ("iosSimulatorArm64Test", ("commonTest", "nonAndroidTest", "nativeTest", "appleTest", "iosTest", "iosSimulatorArm64Test")),
}
# Guard the current minimum, independently of discovery, so deleting a module's
# last tests cannot turn a missing suite into a green "not applicable" entry.
PERMISSION_MODULES = tuple("calf-permissions/" + name for name in (
    "core", "camera", "gallery", "location", "background-location", "bluetooth",
    "contacts", "calendar", "notifications", "wifi", "microphone",
))
SHARED_MINIMUM = ("calf-io", "calf-file-picker", "calf-ui", "calf-navigation", "calf-geo",
                  "calf-camera-picker", "calf-share", "calf-webview", *PERMISSION_MODULES)
MINIMUM_MODULES = {suite: SHARED_MINIMUM for suite in SUITES}
MINIMUM_MODULES["desktop"] = (*SHARED_MINIMUM, "calf-file-picker-coil", "calf-cupertino-icons")
MINIMUM_MODULES["ios"] = (*SHARED_MINIMUM, "calf-file-picker-coil")
MINIMUM_MODULES["android-device"] = ("calf-io", "calf-file-picker", "calf-webview", "calf-ui")
KNOWN_TEST_SETS = set(name for _, names in SUITES.values() for name in names) | {"androidDeviceTest", "iosArm64Test"}
ROOT_INPUTS = (
    "build.gradle.kts", "settings.gradle.kts", "gradle.properties", "gradle.lockfile",
    "gradlew", "gradlew.bat", "rust-toolchain.toml", ".cargo/config", ".cargo/config.toml",
    "package.json", "yarn.lock", "package-lock.json", "pnpm-lock.yaml",
)
IGNORED_INPUT_DIRS = {".git", ".gradle", "build", "target", "node_modules", "__pycache__", ".kotlin"}
MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_TOTAL_REPORT_BYTES = 256 * 1024 * 1024
MAX_REPORTS = 10000
MAX_CASES = 200000
COUNTS = ("tests", "failures", "errors", "skipped")
PROJECT_PATH = re.compile(r":[a-z][a-z0-9-]*(?::[a-z][a-z0-9-]*)*\Z")
IOS_APPLICATION_TASK = "iosSimulatorArm64ApplicationTest"
IOS_APPLICATION_SOURCES = (
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHostTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UIImageConversionTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/RememberNativeAlertPropertiesTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/navigation/NativeBarOwnershipTest.kt",
)
IOS_APPLICATION_CASES = (
    ("dialog.NativeAlertLifecycleTest", "presentedAlertUsesLatestActionAndTextFieldCallbacks"),
    ("dialog.NativeAlertLifecycleTest", "disposalDuringPresentationQueuesCleanupAndReplacement"),
    ("dialog.NativeAlertLifecycleTest", "actionSheetHasAPresentingViewPopoverAnchor"),
    ("dialog.NativeAlertLifecycleTest", "outsideDismissRequestsAndDisposalRemainExactlyOnce"),
    ("dropdown.NativeDropDownLifecycleTest", "expandedStateControlsActualMenuAndDismissalIsNotReportedAtOpen"),
    ("sheet.NativeSheetLifecycleTest", "cancellingAShowWaiterDoesNotReuseItsCompletionForHide"),
    ("sheet.NativeSheetLifecycleTest", "disposalDuringShowDetachesOwnerWithoutUserDismissal"),
    ("timepicker.NativeTimePickerTest", "replacingStateReplacesTheNativeOwnerAndNeverWritesToOldState"),
    ("internal.NativeUiApplicationHostTest", "generatedBodyRunsOnOwnedWorkerWithActiveAttachedApplication"),
    ("internal.NativeUiApplicationHostTest", "repeatedRealComposeRootsRecomposeDisposeAndRestoreTheirOwner"),
    ("internal.NativeUiApplicationHostTest", "failedAssertionPreservesCauseAndReleasesRealCompositionAndPresenter"),
    ("internal.NativeUiApplicationHostTest", "nativeObjectIdentityRejectsNullAndEqualButDistinctObjects"),
    ("utils.UIImageConversionTest", "returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected"),
    ("dialog.RememberNativeAlertPropertiesTest", "stableInputsRetainIdentityButTextFieldReplacementReachesTheCaller"),
    ("navigation.NativeBarOwnershipTest", "emptyTabsClearSelectionAndRepopulationClampsIndex"),
    ("navigation.NativeBarOwnershipTest", "selectionUsesCurrentNativeMembershipInsteadOfStaleOrMutableTags"),
)
NATIVE_SHARE_BOUNDARY_FOCUS = "native-share-boundaries"
NATIVE_SHARE_BOUNDARY_MODULE = "calf-share"
NATIVE_SHARE_BOUNDARY_CLASS = "com.mohamedrejeb.calf.share.platform.NativeLoaderBoundaryIntegrationTest"
NATIVE_SHARE_BOUNDARY_SOURCE = "calf-share/src/desktopTest/kotlin/com/mohamedrejeb/calf/share/platform/NativeLoaderBoundaryIntegrationTest.kt"
NATIVE_SHARE_BOUNDARY_METHODS = (
    "missingBundledResourceFailsVisiblyWithoutPublishingOrRetryingANativeImage",
    "explicitExternalPackagerPathLoadsTheRealHostLibraryWithoutTouchingTheHomeCache",
    "homePermissionPolicyFollowsActualPrivateDirectoryCreationRatherThanTheWritableHint",
    "failedCacheDirectoryCreationCannotOverwriteAnExistingOrdinaryFile",
    "redirectedHomeCacheCannotWriteOrLoadThroughTheActualDirectoryAlias",
)
DATE_TRANSACTION_FOCUS = "material-date-transaction"
DATE_TRANSACTION_MODULE = "calf-ui"
DATE_TRANSACTION_CLASS = "com.mohamedrejeb.calf.ui.datepicker.CompactDateTransactionAcceptanceTest"
DATE_TRANSACTION_PACKAGE_PATH = "kotlin/com/mohamedrejeb/calf/ui/datepicker/"
DATE_TRANSACTION_SOURCE_SETS = {
    "desktop": "desktopTest", "android-host": "androidHostTest",
    # webTest is a sibling fragment of materialTest. Leaf test fragments depend
    # on both; put the thin runner wrappers there rather than changing hierarchy.
    "android-device": "androidDeviceTest", "js": "jsTest", "wasm": "wasmJsTest",
}
DATE_TRANSACTION_SCENARIOS_SOURCE = ("calf-ui/src/materialTest/" + DATE_TRANSACTION_PACKAGE_PATH +
                                     "CompactDateTransactionScenarios.kt")
DATE_TRANSACTION_METHODS = (
    "capturedConfirmRevalidatesTheLatestRules",
    "replacementOwnerYearRangeAndRuleStartAnIndependentTransaction",
    "nullInputClearCancelReopenAndConfirmRemainTransactional",
    "noSelectableDateRejectsCommitAndCancelReopenRecovers",
)
ANDROID_IO_OVERSIZE_FOCUS = "io-device-known-oversize"
ANDROID_IO_DEVICE_CLASS = "com.mohamedrejeb.calf.io.KmpFileDeviceTest"
ANDROID_IO_DEVICE_SOURCE = "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/KmpFileDeviceTest.kt"
ANDROID_IO_OVERSIZE_METHOD = "knownOversizeIsRejectedBeforeAnyNativeStreamIsOpened"
ANDROID_IO_DEVICE_METHODS = (
    "nativeDescriptorProbeCountsFilesAndPipeEndsWithoutLeaksOrOffsetChanges",
    "fdInfoParserAcceptsUnsignedInodesAndRejectsInvalidRecords",
    "wholeArrayReadClosesTheActualProviderDescriptor",
    "returnedSourceOwnsItsNativeDescriptorUntilExplicitClose",
    "unknownSizeOverrunThrowsInsteadOfReturningTruncatedDataAndCloses",
    ANDROID_IO_OVERSIZE_METHOD,
    "emptyAndExactLimitFilesReturnAllBytesAndClose",
    "providerReadErrorIsNotEmptySuccessAndClosesTheRealTransferredPipe",
    "boundedReadAlsoClosesOnActualProviderReadError",
    "alreadyCancelledCallerDoesNotOpenAProviderStream",
    "repeatedSuccessAndConsumingFailureDoNotAccumulateDescriptors",
    "contentReferenceRetainsItsUriAndNeverInventsAFilesystemPath",
)
ANDROID_SAVE_IDENTITY_FOCUS = "save-device-identity"
ANDROID_SAVE_IDENTITY_RECOVERY_FOCUS = "save-device-identity-missing"
ANDROID_SAVE_IDENTITY_FOCUSES = (ANDROID_SAVE_IDENTITY_FOCUS, ANDROID_SAVE_IDENTITY_RECOVERY_FOCUS)
ANDROID_SAVE_IDENTITY_ANNOTATION = "com.mohamedrejeb.calf.picker.SaveIdentityAcceptance"
ANDROID_SAVE_CALIBRATION_ANNOTATION = "com.mohamedrejeb.calf.picker.SaveIdentityCalibration"
ANDROID_SAVE_ANNOTATION_SOURCE = "calf-file-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/picker/SaveIdentityAcceptance.kt"
ANDROID_SAVE_IDENTITY_GROUPS = (
    {
        "classname": "com.mohamedrejeb.calf.picker.SaveDestinationDeviceTest",
        "source": "calf-file-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/picker/SaveDestinationDeviceTest.kt",
        "declared_methods": (
            "nativeDescriptorProbeRejectsAKnownOpenFileWithoutChangingItsOffsetOrLeaking",
            "fdInfoParserRejectsMissingDuplicateAndMalformedKernelInodes",
            "distinctNativeInodesCopyAllBytesAndCloseBothFiles",
            "actualHardLinkIsNotTruncatedOrDeleted",
            "actualSymlinkAndCanonicalPathAliasesPreserveTheOriginal",
            "emptyContentDoesNotMeanUnknownOrMatchingNativeIdentity",
            "missingSourceNeverAuthorizesWriteOrCleanupOfAnExistingDestination",
            "onlyMissingDestinationIsCreatedAfterSourceIdentityIsKnown",
            "realNotADirectoryStatErrorIsNotTreatedAsMissingDestination",
            "realTreeAndSingleDocumentAliasesOpenOnlyForReadAndNeverDelete",
            "revokedReadOnAnIdentifiedDocumentAliasCannotTruncateOrDeleteIt",
            "fileProviderToDocumentsProviderCopyUsesRealStreamsAndClosesThem",
            "failedDistinctProviderSourceDeletesOnlyTheNewDocumentWithoutWritingIt",
        ),
        "methods": (
            "nativeDescriptorProbeRejectsAKnownOpenFileWithoutChangingItsOffsetOrLeaking",
            "fdInfoParserRejectsMissingDuplicateAndMalformedKernelInodes",
            "distinctNativeInodesCopyAllBytesAndCloseBothFiles",
            "realNotADirectoryStatErrorIsNotTreatedAsMissingDestination",
            "realTreeAndSingleDocumentAliasesOpenOnlyForReadAndNeverDelete",
            "revokedReadOnAnIdentifiedDocumentAliasCannotTruncateOrDeleteIt",
            "failedDistinctProviderSourceDeletesOnlyTheNewDocumentWithoutWritingIt",
        ),
    },
    {
        "classname": "com.mohamedrejeb.calf.picker.FileSaverActivityDeviceTest",
        "source": "calf-file-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/picker/FileSaverActivityDeviceTest.kt",
        "declared_methods": (
            "byteRequestSurvivesAnActualActivityResultRoundTrip",
            "publicFileOverloadStreamsFromARealFileProviderWithoutMovingTheSource",
            "nullBytesDeliberatelyProduceARealEmptyDocument",
            "frameworkCancellationDeliversOneNullResultAndReleasesTheNextLaunch",
            "overlapReportsOneErrorWithoutReplacingTheAcceptedNativeRequest",
            "originalReturnedUnderATreeAliasIsNeverOpenedForWriteOrDeleted",
            "uriPayloadSurvivesActualHostActivityRecreationBeforeTheResult",
            "lostBytePayloadAfterActualRecreationIsAnErrorNotEmptySuccess",
        ),
        "methods": (
            "publicFileOverloadStreamsFromARealFileProviderWithoutMovingTheSource",
            "uriPayloadSurvivesActualHostActivityRecreationBeforeTheResult",
            "lostBytePayloadAfterActualRecreationIsAnErrorNotEmptySuccess",
        ),
    },
)


def android_save_identity_filter() -> str:
    # ATE1.0.1 serializes its whole argument map as CSV and splits values at
    # commas: class=A#one,A#two silently executes only A#one. Use the standard
    # AndroidJUnitRunner runtime annotation selector, not quoting/URL escaping,
    # a dependency downgrade, a broad class run or a relaxed XML inventory.
    return ANDROID_SAVE_IDENTITY_ANNOTATION


def android_save_identity_identities(focus: str = ANDROID_SAVE_IDENTITY_FOCUS) -> list[dict]:
    if focus not in ANDROID_SAVE_IDENTITY_FOCUSES:
        raise ValueError("Unknown finite native saver selection")
    calibration = ANDROID_SAVE_IDENTITY_GROUPS[0]["methods"][0]
    return [{"classname": group["classname"], "name": method}
            for group in ANDROID_SAVE_IDENTITY_GROUPS for method in group["methods"]
            if focus != ANDROID_SAVE_IDENTITY_RECOVERY_FOCUS or method != calibration]


def validate_save_identity_annotations(root: Path, test_sources: list[str]) -> None:
    """Bind runtime annotation selection to the exact declarations, not just XML."""
    if ANDROID_SAVE_ANNOTATION_SOURCE not in test_sources:
        raise ValueError("Missing native saver runtime annotation source")
    source = safe_path(root, ANDROID_SAVE_ANNOTATION_SOURCE).read_text(encoding="utf-8")
    expected = {"SaveIdentityAcceptance", "SaveIdentityCalibration"}
    actual = re.findall(r"@Target\(AnnotationTarget.FUNCTION\)\s+"
                        r"@Retention\(AnnotationRetention.RUNTIME\)\s+annotation class ([A-Za-z_][A-Za-z0-9_]*)", source)
    if set(actual) != expected or len(actual) != 2 or "package com.mohamedrejeb.calf.picker" not in source:
        raise ValueError("Native saver selector annotations must retain method/runtime contracts")
    annotated, calibrations = [], []
    for relative in test_sources:
        if relative == ANDROID_SAVE_ANNOTATION_SOURCE:
            continue
        text = safe_path(root, relative).read_text(encoding="utf-8")
        if "@SaveIdentityAcceptance" not in text and "@SaveIdentityCalibration" not in text:
            continue
        group = next((g for g in ANDROID_SAVE_IDENTITY_GROUPS if g["source"] == relative), None)
        if group is None:
            raise ValueError("Native saver selection annotation used by an unreviewed source")
        hits = re.findall(r"@SaveIdentityAcceptance\s+(?:@SaveIdentityCalibration\s+)?"
                          r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)
        cal = re.findall(r"@SaveIdentityAcceptance\s+@SaveIdentityCalibration\s+"
                         r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)
        if (len(hits) != text.count("@SaveIdentityAcceptance") or
                len(cal) != text.count("@SaveIdentityCalibration")):
            raise ValueError("Unrecognized native saver selection annotation placement")
        annotated += [{"classname": group["classname"], "name": name} for name in hits]
        calibrations += [{"classname": group["classname"], "name": name} for name in cal]
    identity = lambda cases: Counter((c["classname"], c["name"]) for c in cases)
    if identity(annotated) != identity(android_save_identity_identities()) or identity(calibrations) != identity(android_save_identity_identities()[:1]):
        raise ValueError("Native saver annotation inventory differs from the exact ten/calibration identities")


UNSUPPORTED_PERMISSION_FOCUS = "permission-public-unsupported"
UNSUPPORTED_PERMISSION_MODULE = "calf-permissions/core"
UNSUPPORTED_PERMISSION_CLASS = "com.mohamedrejeb.calf.permissions.UnsupportedPublicFactoryTest"
UNSUPPORTED_PERMISSION_SOURCE_SETS = {"desktop": "desktopTest", "js": "jsTest", "wasm": "wasmJsTest"}
UNSUPPORTED_PERMISSION_FIXTURE = "calf-permissions/core/src/commonTest/kotlin/com/mohamedrejeb/calf/permissions/UnsupportedPublicFactoryFixture.kt"
UNSUPPORTED_PERMISSION_METHODS = (
    "allNamedSingleRequestsCompleteOnceWithoutImplyingAuthorization",
    "publicBatchChildAndEmptyRequestsReturnExactUnsupportedMaps",
    "publicCallbacksFollowRecompositionAndPreserveTheState",
    "publicPermissionChangesCannotLeakThePreviousSelection",
    "throwingAndReentrantCallbacksHaveExactlyOneSynchronousResult",
    "environmentAndLegacyFlagsCannotManufactureAuthorization",
)
IOS_PERMISSION_FOCUS = "permission-ios-factories"
IOS_PERMISSION_MODULE = "calf-permissions/core"
IOS_PERMISSION_CLASS = "com.mohamedrejeb.calf.permissions.IOSPublicPermissionFactoryTest"
IOS_PERMISSION_SOURCE = "calf-permissions/core/src/iosTest/kotlin/com/mohamedrejeb/calf/permissions/IOSPublicPermissionFactoryTest.kt"
IOS_PERMISSION_METHODS = (
    "unknownAndExplicitNoGateHaveDifferentCoherentOutcomes",
    "delayedSingleUsesLatestCallbackAndRealMainQueueWithoutReplacingOwner",
    "delayedChildAndSerialBatchUseLatestCallbacksAndExactRequestedMap",
    "emptyAndNotRequiredPublicRequestsUseLatestCallbackWithoutNativeWork",
    "replacementAndDisposalDropOldNativeResultsAndReleaseLifecycleObservers",
    "nativeRegistryHandlesNameCollisionsConcurrentLookupsAndReentrantFactories",
    "throwingRegisteredFactoryRemainsFailedRatherThanMasqueradingAsUnsupported",
)
IOS_PERMISSION_SAFETY_FOCUS = "permission-ios-safety"
IOS_PERMISSION_SAFETY_CLASS = "com.mohamedrejeb.calf.permissions.IOSPermissionSafetyAcceptanceTest"
IOS_PERMISSION_SAFETY_SOURCE = "calf-permissions/core/src/iosTest/kotlin/com/mohamedrejeb/calf/permissions/IOSPermissionSafetyAcceptanceTest.kt"
IOS_PERMISSION_SAFETY_METHODS = (
    "throwingBackgroundCompletionKeepsThePublicOwnerRecoverableAndStatusCurrent",
    "racedRealBackgroundQueriesAndPendingDisposalNeverPublishObsoleteState",
)
IOS_PERMISSION_BATCH_FOCUS = "permission-ios-empty-batch"
IOS_PERMISSION_BATCH_CLASS = "com.mohamedrejeb.calf.permissions.IOSPermissionBatchSafetyAcceptanceTest"
IOS_PERMISSION_BATCH_SOURCE = "calf-permissions/core/src/iosTest/kotlin/com/mohamedrejeb/calf/permissions/IOSPermissionBatchSafetyAcceptanceTest.kt"
IOS_PERMISSION_BATCH_METHODS = (
    "emptyCallbackFailurePreservesRecompositionLaterRequestsAndDisposal",
)
IOS_PERMISSION_SAFETY_SPECS = {
    IOS_PERMISSION_SAFETY_FOCUS: {
        "classname": IOS_PERMISSION_SAFETY_CLASS, "source": IOS_PERMISSION_SAFETY_SOURCE,
        "methods": IOS_PERMISSION_SAFETY_METHODS,
        "scope": "Two exact real iOS callback-error/query-race/disposal methods only; no privacy UI or unrelated suite pass",
    },
    IOS_PERMISSION_BATCH_FOCUS: {
        "classname": IOS_PERMISSION_BATCH_CLASS, "source": IOS_PERMISSION_BATCH_SOURCE,
        "methods": IOS_PERMISSION_BATCH_METHODS,
        "scope": "One exact real iOS public empty-batch failure/recomposition/replacement/disposal method only; no OS privacy UI or accepted-suite replay",
    },
}
ANDROID_PERMISSION_COMPLETION_FOCUS = "permission-android-completion"
ANDROID_PERMISSION_COMPLETION_CLASS = "com.mohamedrejeb.calf.permissions.AndroidPermissionCompletionAcceptanceTest"
ANDROID_PERMISSION_COMPLETION_SOURCE = "calf-permissions/core/src/androidHostTest/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionCompletionAcceptanceTest.kt"
ANDROID_PERMISSION_COMPLETION_METHODS = (
    "emptyFilteredAndMixedBatchesReturnCompleteMapsIncludingRealNotificationBoundaries",
    "runtimeNotRequiredAndUnknownChildrenUseLatestCallbacksExactlyOnce",
    "destroyedAndRecreatedActivityOwnersCannotDeliverOldOrDuplicateChildResults",
)
UI_DATE_BOUNDS_FOCUS = "ui-native-date-bounds"
UI_DATE_BOUNDS_CLASS = "com.mohamedrejeb.calf.ui.datepicker.NativeDateBoundsAcceptanceTest"
UI_DATE_BOUNDS_SOURCE = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/NativeDateBoundsAcceptanceTest.kt"
UI_DATE_BOUNDS_METHODS = (
    "everyUidatePickerStyleHandlesEmptyIntradayExtremeAndNullBounds",
    "singleAndRangeCalendarsPreserveSafeIntervalsAndRecoverAtYearEndpoints",
    "publicDateAndRangeControlsApplyChangingDisjointAndSameDayRules",
    "publicInlineCalendarKeepsSelectionIndependentFromActualMonthNavigation",
    "nativeMonthNavigationSurvivesRealRootDisposalAndSaverRestoration",
    "publicWheelsAndCompactKeepIndependentMonthIntentDuringNativeEditsAndClear",
)
UI_DATE_REPLACEMENT_FOCUS = "ui-native-date-replacement"
UI_DATE_REPLACEMENT_CLASS = "com.mohamedrejeb.calf.ui.datepicker.NativeDateStateReplacementAcceptanceTest"
UI_DATE_REPLACEMENT_SOURCE = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/NativeDateStateReplacementAcceptanceTest.kt"
UI_DATE_REPLACEMENT_METHODS = (
    "inlineStateReplacementInitializesAllEqualSettings",
    "compactDisabledReplacementInitializesAllEqualSettings",
    "rangeStateReplacementInitializesAllEqualSettings",
)
UI_DATE_IMPORTANT_FOCUS = "ui-native-important-dates"
UI_DATE_COMPACT_FOCUS = "ui-native-compact-replacement"
UI_APPLICATION_FOCUS_SPECS = {
    UI_DATE_BOUNDS_FOCUS: {
        "classname": UI_DATE_BOUNDS_CLASS, "source": UI_DATE_BOUNDS_SOURCE, "methods": UI_DATE_BOUNDS_METHODS,
        "scope": "Six exact attached UIKit bounds/month/Saver/Compose methods only; no unrelated native UI replay or device/release certification",
    },
    UI_DATE_REPLACEMENT_FOCUS: {
        "classname": UI_DATE_REPLACEMENT_CLASS, "source": UI_DATE_REPLACEMENT_SOURCE,
        "methods": UI_DATE_REPLACEMENT_METHODS,
        "scope": "Three exact public UIKit equal-settings state-replacement methods only; no accepted date/UI replay or device/release certification",
    },
    UI_DATE_COMPACT_FOCUS: {
        "groups": (
            {"classname": UI_DATE_REPLACEMENT_CLASS, "source": UI_DATE_REPLACEMENT_SOURCE,
             "methods": (UI_DATE_REPLACEMENT_METHODS[1],), "declared_methods": UI_DATE_REPLACEMENT_METHODS},
        ),
        "scope": "Only the failed compact-disabled replacement with raw UIKit appearance diagnostics; no replay of accepted inline/range/date methods or device/release certification",
    },
    UI_DATE_IMPORTANT_FOCUS: {
        "groups": (
            {"classname": UI_DATE_BOUNDS_CLASS, "source": UI_DATE_BOUNDS_SOURCE,
             "methods": UI_DATE_BOUNDS_METHODS[2:], "declared_methods": UI_DATE_BOUNDS_METHODS},
            {"classname": UI_DATE_REPLACEMENT_CLASS, "source": UI_DATE_REPLACEMENT_SOURCE,
             "methods": UI_DATE_REPLACEMENT_METHODS},
        ),
        "scope": "Four previously failed public date methods and three new state-replacement methods in one real application; two accepted backend methods are not replayed; no device/release certification",
    },
}


def ui_application_focus_groups(focus: str) -> tuple[dict, ...]:
    spec = UI_APPLICATION_FOCUS_SPECS[focus]
    return spec["groups"] if "groups" in spec else (spec,)


def ui_application_focus_filter(focus: str) -> str:
    spec = UI_APPLICATION_FOCUS_SPECS[focus]
    if "groups" not in spec:
        return spec["classname"]
    return ",".join(group["classname"] + "." + method
                    for group in ui_application_focus_groups(focus) for method in group["methods"])


def ui_application_focus_identities(focus: str) -> list[dict]:
    return [{"classname": IOS_APPLICATION_TASK + "." + group["classname"],
             "name": method + "[iosSimulatorArm64]"}
            for group in ui_application_focus_groups(focus) for method in group["methods"]]


def ui_date_bounds_identities() -> list[dict]:
    return ui_application_focus_identities(UI_DATE_BOUNDS_FOCUS)


def android_permission_completion_identities() -> list[dict]:
    # Inspected Robolectric multi-SDK identity: API29 is suffixed, final API33
    # is the unsuffixed method. Missing either SDK is never accepted as 3/3.
    return [{"classname": ANDROID_PERMISSION_COMPLETION_CLASS, "name": method + suffix}
            for method in ANDROID_PERMISSION_COMPLETION_METHODS for suffix in ("[29]", "")]


def ios_permission_identities() -> list[dict]:
    # Inspected KGP 2.4.20 Native JUnit uses a task-prefixed class and the
    # target-suffixed method. The Gradle --tests selector remains the bare class.
    # Match these seven exact identities; never normalize foreign targets/classes.
    return [{"classname": "iosSimulatorArm64Test." + IOS_PERMISSION_CLASS,
             "name": method + "[iosSimulatorArm64]"} for method in IOS_PERMISSION_METHODS]


def ios_permission_safety_identities(focus: str = IOS_PERMISSION_SAFETY_FOCUS) -> list[dict]:
    spec = IOS_PERMISSION_SAFETY_SPECS[focus]
    return [{"classname": "iosSimulatorArm64Test." + spec["classname"],
             "name": method + "[iosSimulatorArm64]"} for method in spec["methods"]]


IOS_SAVE_WRITE_FOCUS = "ios-native-saver-write-failure"
IOS_SAVE_WRITE_SOURCE = "calf-file-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/picker/FileSaverStagingTest.kt"
IOS_SAVE_WRITE_CLASS = "com.mohamedrejeb.calf.picker.FileSaverStagingTest"
IOS_SAVE_WRITE_METHOD = "nativeWriteFalseCleansOnlyPrivateStagingAndNeverReturnsSuccess"
IOS_SAVE_WRITE_DECLARATIONS = (
    "stagedFileKeepsTheRequestedName", "twoStagingsOfTheSameNameDoNotCollide",
    "stagedFileLivesUnderTheTemporaryDirectoryAndIsWritten", "stagingAnExistingFileCopiesItUnderTheRequestedName",
    "stagingAMissingFileFails", "aNonFileUrlCannotStageOrRemoveTheLocalFileWithItsPath",
    "exportCopyRemainsUntilDismissalCompletionButNeverDeletesTheOriginal", IOS_SAVE_WRITE_METHOD,
)


def ios_save_write_identities() -> list[dict]:
    return [{"classname": "iosSimulatorArm64Test." + IOS_SAVE_WRITE_CLASS,
             "name": IOS_SAVE_WRITE_METHOD + "[iosSimulatorArm64]"}]


def allowed_test_focus(suite: str, modules: tuple[str, ...] | None, focus: str) -> bool:
    return ((focus == NATIVE_SHARE_BOUNDARY_FOCUS and suite == "desktop" and
             modules == (NATIVE_SHARE_BOUNDARY_MODULE,)) or
            (focus == DATE_TRANSACTION_FOCUS and suite in DATE_TRANSACTION_SOURCE_SETS and
             modules == (DATE_TRANSACTION_MODULE,)) or
            (focus == ANDROID_IO_OVERSIZE_FOCUS and suite == "android-device" and
             modules == ("calf-io",)) or
            (focus in ANDROID_SAVE_IDENTITY_FOCUSES and suite == "android-device" and
             modules == ("calf-file-picker",)) or
            (focus == UNSUPPORTED_PERMISSION_FOCUS and suite in UNSUPPORTED_PERMISSION_SOURCE_SETS and
             modules == (UNSUPPORTED_PERMISSION_MODULE,)) or
            ((focus == IOS_PERMISSION_FOCUS or focus in IOS_PERMISSION_SAFETY_SPECS) and suite == "ios" and
             modules == (IOS_PERMISSION_MODULE,)) or
            (focus == ANDROID_PERMISSION_COMPLETION_FOCUS and suite == "android-host" and
             modules == (IOS_PERMISSION_MODULE,)) or
            (focus == IOS_SAVE_WRITE_FOCUS and suite == "ios" and modules == ("calf-file-picker",)) or
            (focus in UI_APPLICATION_FOCUS_SPECS and suite == "ios" and modules == ("calf-ui",)))


def unsupported_permission_source(suite: str) -> str:
    return ("calf-permissions/core/src/" + UNSUPPORTED_PERMISSION_SOURCE_SETS[suite] +
            "/kotlin/com/mohamedrejeb/calf/permissions/UnsupportedPublicFactoryTest.kt")


def unsupported_permission_identities() -> list[dict]:
    return [{"classname": UNSUPPORTED_PERMISSION_CLASS, "name": method} for method in UNSUPPORTED_PERMISSION_METHODS]


def unsupported_permission_case_inventory(suite: str, cases: list[dict]) -> bool:
    classname = (SUITES[suite][0] + "." if suite in {"js", "wasm"} else "") + UNSUPPORTED_PERMISSION_CLASS
    actual = []
    for case in cases:
        name, separator, suffix = case["name"].partition("[")
        if case["classname"] != classname:
            return False
        if suite == "desktop":
            if separator + suffix != "[desktop]":
                return False
        else:
            target = "js" if suite == "js" else "wasmJs"
            if not separator or not re.fullmatch(re.escape(target) + r", browser, [^\[\]\r\n]+\]", suffix):
                return False
        actual.append(name)
    return len(actual) == len(UNSUPPORTED_PERMISSION_METHODS) and set(actual) == set(UNSUPPORTED_PERMISSION_METHODS)


def date_transaction_source(suite: str) -> str:
    return ("calf-ui/src/" + DATE_TRANSACTION_SOURCE_SETS[suite] + "/" +
            DATE_TRANSACTION_PACKAGE_PATH + "CompactDateTransactionAcceptanceTest.kt")


def date_transaction_identities() -> list[dict]:
    """Canonical names; actual target/browser suffixes are checked separately."""
    return [{"classname": DATE_TRANSACTION_CLASS, "name": method} for method in DATE_TRANSACTION_METHODS]


def android_io_oversize_identities() -> list[dict]:
    return [{"classname": ANDROID_IO_DEVICE_CLASS, "name": ANDROID_IO_OVERSIZE_METHOD}]


def date_transaction_case_inventory(suite: str, cases: list[dict]) -> bool:
    classname = (SUITES[suite][0] + "." if suite in {"js", "wasm"} else "") + DATE_TRANSACTION_CLASS
    actual = []
    for case in cases:
        name, separator, suffix = case["name"].partition("[")
        if case["classname"] != classname:
            return False
        if suite in {"android-host", "android-device"}:
            if separator:
                return False
        elif suite == "desktop":
            if separator + suffix != "[desktop]":
                return False
        else:
            target = "js" if suite == "js" else "wasmJs"
            if (not separator or not suffix.startswith(target + ", browser, ") or
                    not suffix.endswith("]") or "[" in suffix or "]" in suffix[:-1]):
                return False
        actual.append((DATE_TRANSACTION_CLASS, name))
    required = {(c["classname"], c["name"]) for c in date_transaction_identities()}
    return len(actual) == len(required) and set(actual) == required


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def input_digest(files: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{value}  {name}\n" for name, value in sorted(files.items())).encode()).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    """Reject traversal and symlinks before inspecting or mutating owned outputs."""
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(part in {".", ".."} for part in parts):
        raise ValueError("Expected a confined repository-relative path")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink is outside the test receipt contract: {relative}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError("Test path escapes the checkout")
    return current


def source_files(root: Path, relative: str) -> list[Path]:
    folder = safe_path(root, relative)
    if not folder.exists():
        return []
    if not folder.is_dir():
        raise ValueError(f"Expected source directory: {relative}")
    result = []
    for base, directories, names in os.walk(folder, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in IGNORED_INPUT_DIRS)
        for name in [*directories, *names]:
            path = Path(base) / name
            if path.is_symlink():
                raise ValueError(f"Symlinked source input: {path.relative_to(root).as_posix()}")
        for name in sorted(names):
            path = Path(base) / name
            if not path.is_file():
                raise ValueError("Non-regular source input")
            result.append(path)
    return result


def projects(root: Path) -> dict[str, str]:
    """Read this repository's literal include/rename idiom; fail on changed syntax.

    This is not a general Gradle parser. A computed include/rename or different
    source hierarchy requires a deliberate update and new fixture, not guessing.
    """
    settings = safe_path(root, "settings.gradle.kts").read_text(encoding="utf-8")
    blocks = re.findall(r"(?ms)^include\(\s*(.*?)^\)", settings)
    if len(blocks) != 1:
        raise ValueError("Expected one literal settings include block; review CI project discovery")
    block = re.sub(r"(?m)//[^\n]*", "", blocks[0])
    paths = re.findall(r'"([^"\n]+)"', block)
    remainder = re.sub(r'"[^"\n]+"', "", block)
    if not paths or remainder.strip(" \t\r\n,") or len(paths) != len(set(paths)):
        raise ValueError("Computed or duplicate settings includes require explicit review")
    renames = dict(re.findall(r'(?m)^project\("([^"\n]+)"\)\.name = "([a-z][a-z0-9-]*)"\s*$', settings))
    if len(renames) != len(re.findall(r'(?m)^project\([^\n]+\)\.name\s*=', settings)):
        raise ValueError("Computed or duplicate project renames require explicit review")
    result = {}
    for original in paths:
        if not PROJECT_PATH.fullmatch(original):
            raise ValueError("Unrecognized included Gradle project path")
        if original.startswith(":sample:"):
            continue
        if not original.startswith(":calf-"):
            raise ValueError("Unknown non-sample project; classify its library test coverage explicitly")
        parts = original[1:].split(":")
        module = "/".join(parts)
        if not safe_path(root, module + "/build.gradle.kts").is_file():
            raise ValueError(f"Included library build file is missing: {module}")
        target = ":" + ":".join(renames.get(":" + ":".join(parts[:i + 1]), part)
                                 for i, part in enumerate(parts))
        if target in result.values():
            raise ValueError("Duplicate renamed library Gradle path")
        result[module] = target
    if set(renames) - set(paths):
        raise ValueError("Rename refers to a non-included project")
    return dict(sorted(result.items()))


def plan(root: Path, suite: str, minimum_modules: tuple[str, ...] | None = None,
         only_modules: tuple[str, ...] | None = None, *, focus: str | None = None) -> dict:
    if focus is not None and not allowed_test_focus(suite, only_modules, focus):
        raise ValueError("Test focus requires its exact reviewed suite and single module")
    task_name, inherited = SUITES[suite]
    selected, uncovered = [], []
    for module, project in projects(root).items():
        source_root = safe_path(root, module + "/src")
        if source_root.is_dir():
            unknown = {path.name for path in source_root.iterdir()
                       if path.name.endswith("Test") and path.name not in KNOWN_TEST_SETS
                       and source_files(root, path.relative_to(root).as_posix())}
            if unknown:
                raise ValueError(f"Unknown test source sets in {module}: {sorted(unknown)}; update hierarchy mapping")
        if suite == "android-device" and not any(
                path.suffix in {".kt", ".java"}
                for path in source_files(root, f"{module}/src/androidDeviceTest")):
            uncovered.append({"module": module,
                              "reason": "No authored Android-device test host; common/host tests do not establish instrumented execution"})
            continue
        inputs, source_sets = [], []
        for source_set in inherited:
            files = [path for path in source_files(root, f"{module}/src/{source_set}") if path.suffix in {".kt", ".java"}]
            if files:
                inputs.extend(path.relative_to(root).as_posix() for path in files)
                source_sets.append(source_set)
        if inputs:
            # Actual AGP9.4.0/UTP run40434024680 writes TEST-*.xml in the public
            # getResultsDir tree. Its separately inspected getXmlResultsDirectory
            # is an empty intermediate. Preserve both contracts explicitly;
            # do not discover arbitrary XML or count protobuf inventories as tests.
            actual_task = IOS_APPLICATION_TASK if suite == "ios" and module == "calf-ui" else task_name
            report_directory = (f"{module}/build/outputs/androidTest-results/connected/androidMain"
                                if suite == "android-device" else f"{module}/build/test-results/{actual_task}")
            item = {"module": module, "project": project, "task": f"{project}:{actual_task}",
                    "report_directory": report_directory,
                    "test_source_sets": source_sets, "test_source_files": sorted(inputs)}
            if actual_task == IOS_APPLICATION_TASK:
                if not all(source in inputs for source in IOS_APPLICATION_SOURCES):
                    raise ValueError("Required genuine UIKit application host/tests are missing; a Skiko/zero-suite fallback is not allowed")
                item["native_test_host"] = "genuine-uikit-application"
            if suite == "android-device":
                item["agp_declared_xml_directory"] = f"{module}/build/intermediates/android_test_results/androidMain/{task_name}"
                item["utp_results_directory"] = report_directory
            selected.append(item)
        else:
            uncovered.append({"module": module, "reason": f"No inherited test source files for {suite}; not executed or counted as passing"})
    not_selected = []
    if only_modules:
        if len(only_modules) != len(set(only_modules)):
            raise ValueError("Duplicate explicitly selected module")
        missing_selection = set(only_modules) - {item["module"] for item in selected}
        if missing_selection:
            raise ValueError(f"Selected modules do not have {suite} library test sources: {sorted(missing_selection)}")
        not_selected = sorted(item["module"] for item in selected if item["module"] not in only_modules)
        selected = [item for item in selected if item["module"] in only_modules]
        uncovered = [item for item in uncovered if item["module"] in only_modules]
    minimum = set((only_modules or MINIMUM_MODULES[suite]) if minimum_modules is None else minimum_modules)
    missing = minimum - {item["module"] for item in selected}
    if missing:
        raise ValueError(f"Required {suite} library test modules are absent: {sorted(missing)}")
    if not selected:
        raise ValueError(f"No library test sources for {suite}; a zero-test plan is not success")
    if suite == "android-device":
        # Instrumented suites are serial. Exercise data/descriptor/provider
        # ownership first, so a later UI-engine hang cannot hide its outcomes.
        priorities = {module: index for index, module in enumerate(MINIMUM_MODULES[suite])}
        selected.sort(key=lambda item: (priorities.get(item["module"], len(priorities)), item["module"]))
    if suite == "desktop":
        for item in selected:
            if item["module"] == native_test_policy.MODULE and native_test_policy.SOURCE not in item["test_source_files"]:
                raise ValueError("Required native share scenario source is missing; do not silently reduce native coverage")
    result = {"schema_version": 1, "suite": suite, "inherited_test_source_sets": list(inherited),
            "expected": selected, "uncovered": uncovered,
            "complete_suite_requested": not bool(only_modules), "explicit_module_subset": list(only_modules or ()),
            "test_bearing_modules_not_requested": not_selected,
            "scope": "Library tests only; discovery is source-set-aware, not a promise of native/device integration coverage"}
    if focus in UI_APPLICATION_FOCUS_SPECS:
        spec = UI_APPLICATION_FOCUS_SPECS[focus]
        for group in ui_application_focus_groups(focus):
            source = safe_path(root, group["source"]).read_text(encoding="utf-8")
            methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
            declared = group.get("declared_methods", group["methods"])
            package, classname = group["classname"].rsplit(".", 1)
            if (len(methods) != len(declared) or set(methods) != set(declared) or
                    not set(group["methods"]) <= set(declared) or
                    "class " + classname not in source or "package " + package not in source):
                raise ValueError("Native date declarations changed; review the exact finite application selection")
        result["explicit_test_focus"] = focus
        selected[0]["test_filter"] = ui_application_focus_filter(focus)
        selected[0]["required_testcases"] = ui_application_focus_identities(focus)
        result["scope"] = spec["scope"]
    elif focus in ANDROID_SAVE_IDENTITY_FOCUSES:
        for group in ANDROID_SAVE_IDENTITY_GROUPS:
            source = safe_path(root, group["source"]).read_text(encoding="utf-8")
            methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
            package, classname = group["classname"].rsplit(".", 1)
            if (len(methods) != len(group["declared_methods"]) or
                    set(methods) != set(group["declared_methods"]) or
                    not set(group["methods"]) <= set(group["declared_methods"]) or
                    "class " + classname not in source or "package " + package not in source):
                raise ValueError("Android saver declarations changed; review the exact finite selection")
        result["explicit_test_focus"] = focus
        validate_save_identity_annotations(root, selected[0]["test_source_files"])
        selected[0]["test_filter"] = android_save_identity_filter()
        selected[0]["test_filter_argument"] = "annotation"
        selected[0]["test_exclusion_annotation"] = (ANDROID_SAVE_CALIBRATION_ANNOTATION
                if focus == ANDROID_SAVE_IDENTITY_RECOVERY_FOCUS else None)
        selected[0]["required_testcases"] = android_save_identity_identities(focus)
        result["scope"] = ("Nine missing real Android inode/provider/refusal/Activity-recreation methods; separately accepted descriptor calibration not replayed; "
                if focus == ANDROID_SAVE_IDENTITY_RECOVERY_FOCUS else "Ten exact real Android inode/provider/refusal/Activity-recreation methods only; ") + "original hardlink and full native suite remain separate gates, no policy weakening or process-death/device/release certification"
    elif focus == ANDROID_IO_OVERSIZE_FOCUS:
        source = safe_path(root, ANDROID_IO_DEVICE_SOURCE).read_text(encoding="utf-8")
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
        if (len(methods) != len(ANDROID_IO_DEVICE_METHODS) or
                set(methods) != set(ANDROID_IO_DEVICE_METHODS) or
                "class KmpFileDeviceTest" not in source or
                "package com.mohamedrejeb.calf.io" not in source):
            raise ValueError("Android IO declarations changed; review the exact failed-method selection")
        result["explicit_test_focus"] = focus
        # AndroidJUnitRunner's supported class#method form, not a KGP filter or
        # a new wrapper which could omit the original failed metadata assertion.
        selected[0]["test_filter"] = ANDROID_IO_DEVICE_CLASS + "#" + ANDROID_IO_OVERSIZE_METHOD
        selected[0]["required_testcases"] = android_io_oversize_identities()
        result["scope"] = "Only the failed known-size/no-native-open FileProvider method; no accepted IO/picker/UI replay or device-suite certification"
    elif focus == ANDROID_PERMISSION_COMPLETION_FOCUS:
        source = safe_path(root, ANDROID_PERMISSION_COMPLETION_SOURCE).read_text(encoding="utf-8")
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
        if (len(methods) != len(ANDROID_PERMISSION_COMPLETION_METHODS) or
                set(methods) != set(ANDROID_PERMISSION_COMPLETION_METHODS) or
                "class AndroidPermissionCompletionAcceptanceTest" not in source or
                "@Config(sdk = [29, 33], manifest = Config.NONE)" not in source):
            raise ValueError("Android completion declarations changed; review the exact three methods/two SDKs")
        result["explicit_test_focus"] = focus
        selected[0]["test_filter"] = ANDROID_PERMISSION_COMPLETION_CLASS
        selected[0]["required_testcases"] = android_permission_completion_identities()
        result["scope"] = "Three exact public Android completion methods on API29/33 only; Robolectric grants, not device privacy UI"
    elif focus in IOS_PERMISSION_SAFETY_SPECS:
        spec = IOS_PERMISSION_SAFETY_SPECS[focus]
        source = safe_path(root, spec["source"]).read_text(encoding="utf-8")
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
        package, classname = spec["classname"].rsplit(".", 1)
        if (len(methods) != len(spec["methods"]) or set(methods) != set(spec["methods"]) or
                "class " + classname not in source or "package " + package not in source):
            raise ValueError("iOS permission safety declarations changed; review the exact finite selection")
        result["explicit_test_focus"] = focus
        selected[0]["test_filter"] = spec["classname"]
        selected[0]["required_testcases"] = ios_permission_safety_identities(focus)
        result["scope"] = spec["scope"]
    elif focus == IOS_SAVE_WRITE_FOCUS:
        source = safe_path(root, IOS_SAVE_WRITE_SOURCE).read_text(encoding="utf-8")
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
        if (len(methods) != len(IOS_SAVE_WRITE_DECLARATIONS) or set(methods) != set(IOS_SAVE_WRITE_DECLARATIONS) or
                "class FileSaverStagingTest" not in source or "package com.mohamedrejeb.calf.picker" not in source):
            raise ValueError("iOS saver declarations changed; review the exact native failure selection")
        result["explicit_test_focus"] = focus
        selected[0]["test_filter"] = IOS_SAVE_WRITE_CLASS + "." + IOS_SAVE_WRITE_METHOD
        selected[0]["required_testcases"] = ios_save_write_identities()
        result["scope"] = "One new real Foundation false-write/private-staging cleanup method only; no mocked native result, UIKit sheet, device or release certification"
    elif focus == IOS_PERMISSION_FOCUS:
        source = safe_path(root, IOS_PERMISSION_SOURCE).read_text(encoding="utf-8")
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
        if (len(methods) != len(IOS_PERMISSION_METHODS) or set(methods) != set(IOS_PERMISSION_METHODS) or
                "class IOSPublicPermissionFactoryTest" not in source or
                "package com.mohamedrejeb.calf.permissions" not in source):
            raise ValueError("iOS public permission declarations changed; review the seven-method selection")
        result["explicit_test_focus"] = focus
        selected[0]["test_filter"] = IOS_PERMISSION_CLASS
        selected[0]["required_testcases"] = ios_permission_identities()
        result["scope"] = "Seven exact real iOS public factory/Compose/Darwin queue/registry methods only; no privacy UI or unrelated suite pass"
    elif focus == DATE_TRANSACTION_FOCUS:
        source = safe_path(root, date_transaction_source(suite)).read_text(encoding="utf-8")
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
        if (len(methods) != len(DATE_TRANSACTION_METHODS) or set(methods) != set(DATE_TRANSACTION_METHODS) or
                "class CompactDateTransactionAcceptanceTest" not in source or
                "package com.mohamedrejeb.calf.ui.datepicker" not in source or
                DATE_TRANSACTION_SCENARIOS_SOURCE not in selected[0]["test_source_files"]):
            raise ValueError("Date transaction declarations changed; review the exact four-method selection")
        result["explicit_test_focus"] = focus
        selected[0]["test_filter"] = DATE_TRANSACTION_CLASS
        selected[0]["required_testcases"] = date_transaction_identities()
        result["scope"] = "Four exact public Material date-dialog transactions only; unrelated UI/common suites are not requested or counted"
    elif focus == UNSUPPORTED_PERMISSION_FOCUS:
        source = safe_path(root, unsupported_permission_source(suite)).read_text(encoding="utf-8")
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", source)
        if (len(methods) != len(UNSUPPORTED_PERMISSION_METHODS) or set(methods) != set(UNSUPPORTED_PERMISSION_METHODS) or
                "class UnsupportedPublicFactoryTest" not in source or
                "package com.mohamedrejeb.calf.permissions" not in source or
                UNSUPPORTED_PERMISSION_FIXTURE not in selected[0]["test_source_files"]):
            raise ValueError("Public unsupported permission declarations changed; review the six-method selection")
        result["explicit_test_focus"] = focus
        selected[0]["test_filter"] = UNSUPPORTED_PERMISSION_CLASS
        selected[0]["required_testcases"] = unsupported_permission_identities()
        result["scope"] = "Six exact public nonmobile permission-factory scenarios only; no mobile/service-authorization or unrelated suite pass"
    elif focus is not None:
        source = safe_path(root, NATIVE_SHARE_BOUNDARY_SOURCE).read_text(encoding="utf-8")
        methods = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", source)
        if (len(methods) != len(NATIVE_SHARE_BOUNDARY_METHODS) or
                set(methods) != set(NATIVE_SHARE_BOUNDARY_METHODS) or
                "class NativeLoaderBoundaryIntegrationTest" not in source or
                "package com.mohamedrejeb.calf.share.platform" not in source):
            raise ValueError("Native boundary test declarations changed; review the exact finite selection")
        result["explicit_test_focus"] = focus
        selected[0]["test_filter"] = NATIVE_SHARE_BOUNDARY_CLASS
        selected[0]["required_testcases"] = native_share_boundary_identities()
        result["scope"] = "Five exact actual native loader boundary methods only; other share/JNI suites are NOT requested or counted"
    return result


def native_share_boundary_identities() -> list[dict]:
    return [{"classname": NATIVE_SHARE_BOUNDARY_CLASS, "name": method + "[desktop]"}
            for method in NATIVE_SHARE_BOUNDARY_METHODS]


def validate_test_focus(test_plan: dict) -> bool:
    """No arbitrary Gradle filters, module escape, skip list or broad pass claim."""
    focus = test_plan.get("explicit_test_focus")
    if focus is None:
        if any("test_filter" in item or "required_testcases" in item for item in test_plan["expected"]):
            raise ValueError("Test filters require the finite reviewed focus")
        return False
    expected = test_plan["expected"]
    if focus in ANDROID_SAVE_IDENTITY_FOCUSES:
        if (not allowed_test_focus(test_plan["suite"], tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != "calf-file-picker" or
                expected[0]["task"] != ":calf-file-picker:connectedAndroidDeviceTest" or
                expected[0].get("test_filter") != android_save_identity_filter() or
                expected[0].get("test_filter_argument") != "annotation" or
                expected[0].get("test_exclusion_annotation") != (ANDROID_SAVE_CALIBRATION_ANNOTATION
                        if focus == ANDROID_SAVE_IDENTITY_RECOVERY_FOCUS else None) or
                expected[0].get("required_testcases") != android_save_identity_identities(focus) or
                ANDROID_SAVE_ANNOTATION_SOURCE not in expected[0]["test_source_files"] or
                any(group["source"] not in expected[0]["test_source_files"] for group in ANDROID_SAVE_IDENTITY_GROUPS)):
            raise ValueError("Invalid finite Android saver identity/lifecycle plan")
        return True
    if focus == ANDROID_IO_OVERSIZE_FOCUS:
        if (not allowed_test_focus(test_plan["suite"], tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != "calf-io" or
                expected[0]["task"] != ":calf-io:connectedAndroidDeviceTest" or
                expected[0].get("test_filter") != ANDROID_IO_DEVICE_CLASS + "#" + ANDROID_IO_OVERSIZE_METHOD or
                expected[0].get("required_testcases") != android_io_oversize_identities() or
                ANDROID_IO_DEVICE_SOURCE not in expected[0]["test_source_files"]):
            raise ValueError("Invalid finite Android known-size/no-native-open plan")
        return True
    if focus in UI_APPLICATION_FOCUS_SPECS:
        if (not allowed_test_focus(test_plan["suite"], tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != "calf-ui" or
                expected[0]["task"] != ":calf-ui:" + IOS_APPLICATION_TASK or
                expected[0].get("native_test_host") != "genuine-uikit-application" or
                expected[0].get("test_filter") != ui_application_focus_filter(focus) or
                expected[0].get("required_testcases") != ui_application_focus_identities(focus) or
                any(group["source"] not in expected[0]["test_source_files"]
                    for group in ui_application_focus_groups(focus))):
            raise ValueError("Invalid finite attached UIKit date plan")
        return True
    if focus == ANDROID_PERMISSION_COMPLETION_FOCUS:
        if (not allowed_test_focus(test_plan["suite"], tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != IOS_PERMISSION_MODULE or
                expected[0]["task"] != ":calf-permissions:calf-permissions-core:testAndroidHostTest" or
                expected[0].get("test_filter") != ANDROID_PERMISSION_COMPLETION_CLASS or
                expected[0].get("required_testcases") != android_permission_completion_identities() or
                ANDROID_PERMISSION_COMPLETION_SOURCE not in expected[0]["test_source_files"]):
            raise ValueError("Invalid finite two-SDK Android permission completion plan")
        return True
    if focus in IOS_PERMISSION_SAFETY_SPECS:
        spec = IOS_PERMISSION_SAFETY_SPECS[focus]
        if (not allowed_test_focus(test_plan["suite"], tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != IOS_PERMISSION_MODULE or
                expected[0]["task"] != ":calf-permissions:calf-permissions-core:iosSimulatorArm64Test" or
                expected[0].get("test_filter") != spec["classname"] or
                expected[0].get("required_testcases") != ios_permission_safety_identities(focus) or
                spec["source"] not in expected[0]["test_source_files"]):
            raise ValueError("Invalid finite iOS permission safety plan")
        return True
    if focus == IOS_SAVE_WRITE_FOCUS:
        if (not allowed_test_focus(test_plan["suite"], tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != "calf-file-picker" or
                expected[0]["task"] != ":calf-file-picker:iosSimulatorArm64Test" or
                expected[0].get("test_filter") != IOS_SAVE_WRITE_CLASS + "." + IOS_SAVE_WRITE_METHOD or
                expected[0].get("required_testcases") != ios_save_write_identities() or
                IOS_SAVE_WRITE_SOURCE not in expected[0]["test_source_files"]):
            raise ValueError("Invalid finite iOS native staging failure plan")
        return True
    if focus == IOS_PERMISSION_FOCUS:
        if (not allowed_test_focus(test_plan["suite"], tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != IOS_PERMISSION_MODULE or
                expected[0]["task"] != ":calf-permissions:calf-permissions-core:iosSimulatorArm64Test" or
                expected[0].get("test_filter") != IOS_PERMISSION_CLASS or
                expected[0].get("required_testcases") != ios_permission_identities() or
                IOS_PERMISSION_SOURCE not in expected[0]["test_source_files"]):
            raise ValueError("Invalid finite iOS public permission factory plan")
        return True
    if focus == UNSUPPORTED_PERMISSION_FOCUS:
        suite = test_plan["suite"]
        if (not allowed_test_focus(suite, tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != UNSUPPORTED_PERMISSION_MODULE or
                expected[0]["task"] != ":calf-permissions:calf-permissions-core:" + SUITES[suite][0] or
                expected[0].get("test_filter") != UNSUPPORTED_PERMISSION_CLASS or
                expected[0].get("required_testcases") != unsupported_permission_identities() or
                unsupported_permission_source(suite) not in expected[0]["test_source_files"] or
                UNSUPPORTED_PERMISSION_FIXTURE not in expected[0]["test_source_files"]):
            raise ValueError("Invalid finite public unsupported permission plan")
        return True
    if focus == DATE_TRANSACTION_FOCUS:
        suite = test_plan["suite"]
        if (not allowed_test_focus(suite, tuple(test_plan["explicit_module_subset"]), focus) or
                test_plan["complete_suite_requested"] is not False or len(expected) != 1 or
                expected[0]["module"] != DATE_TRANSACTION_MODULE or
                expected[0]["task"] != ":calf-ui:" + SUITES[suite][0] or
                expected[0].get("test_filter") != DATE_TRANSACTION_CLASS or
                expected[0].get("required_testcases") != date_transaction_identities() or
                date_transaction_source(suite) not in expected[0]["test_source_files"] or
                DATE_TRANSACTION_SCENARIOS_SOURCE not in expected[0]["test_source_files"]):
            raise ValueError("Invalid finite four-method date transaction plan")
        return True
    if (focus != NATIVE_SHARE_BOUNDARY_FOCUS or test_plan["suite"] != "desktop" or
            test_plan["complete_suite_requested"] is not False or
            test_plan["explicit_module_subset"] != [NATIVE_SHARE_BOUNDARY_MODULE] or len(expected) != 1 or
            expected[0]["module"] != NATIVE_SHARE_BOUNDARY_MODULE or expected[0]["task"] != ":calf-share:desktopTest" or
            expected[0].get("test_filter") != NATIVE_SHARE_BOUNDARY_CLASS or
            expected[0].get("required_testcases") != native_share_boundary_identities() or
            NATIVE_SHARE_BOUNDARY_SOURCE not in expected[0]["test_source_files"]):
        raise ValueError("Invalid finite native boundary test plan; no arbitrary selection is allowed")
    return True


def snapshot_inputs(root: Path) -> dict[str, str]:
    inputs = set()
    for relative in ROOT_INPUTS:
        path = safe_path(root, relative)
        if path.is_file():
            inputs.add(path)
    for tree in ("gradle", "convention-plugins", "scripts/ci", "scripts/native", "kotlin-js-store"):
        inputs.update(source_files(root, tree))
    for module in projects(root):
        for relative in (f"{module}/src", f"{module}/native", f"{module}/.cargo", f"{module}/gradle"):
            inputs.update(source_files(root, relative))
        for name in ("build.gradle.kts", "gradle.properties", "gradle.lockfile"):
            path = safe_path(root, f"{module}/{name}")
            if path.is_file():
                inputs.add(path)
    # Sample build configuration is evaluated even in a library-only invocation;
    # sample source/tests are deliberately not substitutes for library execution.
    for path in safe_path(root, "sample").glob("*/build.gradle.kts"):
        inputs.add(safe_path(root, path.relative_to(root).as_posix()))
    result = {}
    for path in sorted(inputs):
        before = path.stat()
        value = sha256(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError("Source input changed while capturing its hash")
        result[path.relative_to(root).as_posix()] = value
    return result


class NoDtdBuilder(ET.TreeBuilder):
    def doctype(self, name, public_id, system_id):
        raise ValueError("DTD/entity declarations are not JUnit evidence")


def junit_cases(payload: bytes) -> list[dict]:
    if len(payload) > MAX_REPORT_BYTES:
        raise ValueError("JUnit report exceeds bounded input size")
    document = ET.fromstring(payload, parser=ET.XMLParser(target=NoDtdBuilder()))

    def visit(suite: ET.Element, depth: int = 0) -> list[dict]:
        if depth > 32:
            raise ValueError("JUnit nesting exceeds bounded report depth")
        if suite.tag not in {"testsuite", "testsuites"}:
            raise ValueError("Unrecognized JUnit root or nested suite")
        cases = []
        for item in suite:
            if item.tag in {"testsuite", "testsuites"}:
                cases.extend(visit(item, depth + 1))
            elif item.tag == "testcase" and suite.tag == "testsuite":
                name, classname = item.get("name", ""), item.get("classname", suite.get("name", ""))
                if not name or not classname or len(name) > 4096 or len(classname) > 4096:
                    raise ValueError("Missing or invalid actual testcase identity")
                statuses = [child.tag for child in item if child.tag in {"skipped", "failure", "error"}]
                if len(statuses) > 1:
                    raise ValueError("Conflicting or duplicate testcase outcome elements")
                if any(child.tag not in {"skipped", "failure", "error", "system-out", "system-err", "properties"} for child in item):
                    raise ValueError("Unrecognized testcase content")
                cases.append({"classname": classname, "name": name,
                              "status": {"failure": "failed", "error": "error", "skipped": "skipped"}.get(next(iter(statuses), ""), "passed")})
            elif item.tag not in {"properties", "system-out", "system-err"}:
                raise ValueError("Unrecognized JUnit suite content")
            if len(cases) > MAX_CASES:
                raise ValueError("JUnit testcase count exceeds bounded input size")
        counts = case_counts(cases)
        for key in COUNTS:
            declared = suite.get(key)
            if declared is not None and (not re.fullmatch(r"[0-9]+", declared) or int(declared) != counts[key]):
                raise ValueError("Declared JUnit summary differs from actual testcase elements")
        return cases

    cases = visit(document)
    identities = [(item["classname"], item["name"]) for item in cases]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate testcase identity in JUnit document")
    return cases


def case_counts(cases: list[dict]) -> dict[str, int]:
    statuses = Counter(case["status"] for case in cases)
    not_applicable = sum(case.get("disposition") == "not-applicable" for case in cases)
    return {"tests": len(cases), "failures": statuses["failed"], "errors": statuses["error"],
            "skipped": statuses["skipped"], "passed": statuses["passed"],
            "executed": len(cases) - statuses["skipped"], "not_applicable": not_applicable,
            "unexpected_skipped": statuses["skipped"] - not_applicable}


def collect_reports(root: Path, test_plan: dict, started_ns: int, ended_ns: int, marker_counts: Counter,
                    host_system: str | None = None, native_ui_opt_in: bool = False) -> dict:
    boundary_focus = validate_test_focus(test_plan)
    modules, errors, total_bytes, file_count = [], [], 0, 0
    for expected in test_plan["expected"]:
        module_cases, identities, reports, cases_by_report = [], set(), [], []
        task = expected["task"]
        if marker_counts[task] != 1:
            errors.append({"module": expected["module"], "error": "Expected exactly one fresh task execution marker", "markers": marker_counts[task]})
        folder = safe_path(root, expected["report_directory"])
        paths = []
        for base, directories, names in os.walk(folder, followlinks=False):
            directories.sort()
            for name in [*directories, *names]:
                safe_path(root, (Path(base) / name).relative_to(root).as_posix())
            paths.extend(Path(base) / name for name in sorted(names) if name.startswith("TEST-") and name.endswith(".xml"))
            if len(paths) + file_count > MAX_REPORTS:
                raise ValueError("JUnit report tree exceeds bounded file count")
        for path in paths:
            relative = path.relative_to(root).as_posix()
            try:
                path = safe_path(root, relative)
                stat = path.stat()
                if not path.is_file() or stat.st_nlink > 1:
                    raise ValueError("Non-regular or hardlinked JUnit evidence")
                if not started_ns - 2_000_000_000 <= stat.st_mtime_ns <= ended_ns + 2_000_000_000:
                    raise ValueError("Stale or future-dated JUnit report")
                total_bytes += stat.st_size
                file_count += 1
                if stat.st_size > MAX_REPORT_BYTES or total_bytes > MAX_TOTAL_REPORT_BYTES or file_count > MAX_REPORTS:
                    raise ValueError("JUnit evidence exceeds bounded input size")
                payload = path.read_bytes()
                after_read = path.stat()
                if (stat.st_size, stat.st_mtime_ns, stat.st_ino) != (after_read.st_size, after_read.st_mtime_ns, after_read.st_ino):
                    raise ValueError("JUnit report changed during evidence capture")
                cases = junit_cases(payload)
                keys = {(item["classname"], item["name"]) for item in cases}
                if keys & identities:
                    raise ValueError("Duplicate testcase identity across reports for one task")
                identities.update(keys)
                module_cases.extend(cases)
                if len(module_cases) > MAX_CASES:
                    raise ValueError("JUnit testcase total exceeds bounded input size")
                reports.append({"path": relative, "sha256": hashlib.sha256(payload).hexdigest(), **case_counts(cases)})
                cases_by_report.append(cases)
            except (OSError, ET.ParseError, ValueError) as error:
                # Do not export XML/system-out/failure bodies or machine paths.
                errors.append({"module": expected["module"], "path": relative, "error": type(error).__name__})
        if boundary_focus and test_plan["explicit_test_focus"] in UI_APPLICATION_FOCUS_SPECS:
            sources = {IOS_APPLICATION_TASK + "." + group["classname"]: group["source"]
                       for group in ui_application_focus_groups(test_plan["explicit_test_focus"])}
            required = {(c["classname"], c["name"]) for c in expected["required_testcases"]}
            actual = {(c["classname"], c["name"]) for c in module_cases}
            policy_errors = ([] if actual == required else
                             [f"Native date XML must contain exactly all {len(required)} selected application methods, no missing or unrelated cases"])
            scenarios = [{**c, "source": sources.get(c["classname"], "unselected"), "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
        elif boundary_focus and test_plan["explicit_test_focus"] in ANDROID_SAVE_IDENTITY_FOCUSES:
            required = {(c["classname"], c["name"]) for c in expected["required_testcases"]}
            actual = {(c["classname"], c["name"]) for c in module_cases}
            policy_errors = ([] if actual == required else
                             [f"Android saver XML must contain exactly all {len(required)} selected methods, no missing or unrelated cases"])
            sources = {group["classname"]: group["source"] for group in ANDROID_SAVE_IDENTITY_GROUPS}
            scenarios = [{**c, "source": sources.get(c["classname"], "unselected"), "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
        elif boundary_focus and test_plan["explicit_test_focus"] == ANDROID_IO_OVERSIZE_FOCUS:
            required = {(c["classname"], c["name"]) for c in expected["required_testcases"]}
            actual = {(c["classname"], c["name"]) for c in module_cases}
            policy_errors = ([] if actual == required else
                             ["Android IO XML must contain exactly the failed known-size/no-native-open method, no missing or unrelated cases"])
            scenarios = [{**c, "source": ANDROID_IO_DEVICE_SOURCE, "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
        elif boundary_focus and test_plan["explicit_test_focus"] == ANDROID_PERMISSION_COMPLETION_FOCUS:
            required = {(c["classname"], c["name"]) for c in expected["required_testcases"]}
            actual = {(c["classname"], c["name"]) for c in module_cases}
            policy_errors = ([] if actual == required else
                             ["Android completion XML must contain exactly all three methods on both API29/33"])
            scenarios = [{**c, "source": ANDROID_PERMISSION_COMPLETION_SOURCE, "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
        elif boundary_focus and test_plan["explicit_test_focus"] == IOS_SAVE_WRITE_FOCUS:
            required = {(c["classname"], c["name"]) for c in expected["required_testcases"]}
            actual = {(c["classname"], c["name"]) for c in module_cases}
            policy_errors = ([] if actual == required else
                             ["iOS saver XML must contain exactly the new native write-failure method, no missing or unrelated cases"])
            scenarios = [{**c, "source": IOS_SAVE_WRITE_SOURCE, "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
        elif boundary_focus and (test_plan["explicit_test_focus"] == IOS_PERMISSION_FOCUS or
                                 test_plan["explicit_test_focus"] in IOS_PERMISSION_SAFETY_SPECS):
            required = {(c["classname"], c["name"]) for c in expected["required_testcases"]}
            actual = {(c["classname"], c["name"]) for c in module_cases}
            policy_errors = ([] if actual == required else
                             [f"iOS public permission XML must contain exactly all {len(required)} methods, no missing or unrelated cases"])
            owning_source = (IOS_PERMISSION_SAFETY_SPECS[test_plan["explicit_test_focus"]]["source"]
                             if test_plan["explicit_test_focus"] in IOS_PERMISSION_SAFETY_SPECS else IOS_PERMISSION_SOURCE)
            scenarios = [{**c, "source": owning_source, "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
        elif boundary_focus and test_plan["explicit_test_focus"] == UNSUPPORTED_PERMISSION_FOCUS:
            policy_errors = ([] if unsupported_permission_case_inventory(test_plan["suite"], module_cases) else
                             ["Public unsupported permission XML must contain exactly all six methods with actual target identities"])
            scenarios = [{**c, "source": UNSUPPORTED_PERMISSION_FIXTURE, "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
        elif boundary_focus and test_plan["explicit_test_focus"] == DATE_TRANSACTION_FOCUS:
            policy_errors = ([] if date_transaction_case_inventory(test_plan["suite"], module_cases) else
                             ["Focused date transaction XML must contain exactly all four declared methods with the actual target identities"])
            scenarios = [{**c, "source": DATE_TRANSACTION_SCENARIOS_SOURCE, "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
        elif boundary_focus:
            required = {(c["classname"], c["name"]) for c in expected["required_testcases"]}
            actual = {(c["classname"], c["name"]) for c in module_cases}
            policy_errors = [] if actual == required else ["Focused native boundary XML must contain exactly all five declared methods, no missing or unrelated cases"]
            scenarios = [{**c, "source": NATIVE_SHARE_BOUNDARY_SOURCE, "required_on_host": True,
                          "disposition": "required-executed" if c["status"] == "passed" else "required-not-passed"}
                         for c in module_cases]
            # Do NOT classify the unrequested AppKit/bridge methods N/A or pass.
            # A full share suite retains its original strict native policy.
        else:
            scenarios, policy_errors = native_test_policy.apply(expected["module"], test_plan["suite"], module_cases,
                                                               host_system or platform.system(), native_ui_opt_in)
        errors.extend({"module": expected["module"], "error": error} for error in policy_errors)
        for report, cases in zip(reports, cases_by_report):
            report.update(case_counts(cases))
        counts = case_counts(module_cases)
        if not reports or not counts["executed"]:
            errors.append({"module": expected["module"], "error": "No actual non-skipped library testcases"})
        if counts["failures"] or counts["errors"] or counts["unexpected_skipped"]:
            errors.append({"module": expected["module"], "error": "Failed, errored or unexpected skipped tests are not accepted by this verification gate"})
        modules.append({"module": expected["module"], "task": task, **counts, "reports": reports,
                        "testcases": module_cases, "native_scenarios": scenarios})
    return {"modules": modules, "errors": errors,
            "native_matrix_scope": "Current host only; exact N/A cases are not passed and do not establish other host scenarios",
            "totals": {key: sum(module[key] for module in modules) for key in (*COUNTS, "passed", "executed", "not_applicable", "unexpected_skipped")}}


def quarantine_reports(root: Path, output: Path, test_plan: dict) -> list[str]:
    """Move only selected generated task-report trees, never caches or sources."""
    paths = []
    for item in test_plan["expected"]:
        source = safe_path(root, item["report_directory"])
        if source.exists() and not source.is_dir():
            raise ValueError("Selected generated report path is not a directory")
        # Validate all existing report-tree entries before the first mutation.
        if source.exists():
            for base, directories, names in os.walk(source, followlinks=False):
                for name in [*directories, *names]:
                    safe_path(root, (Path(base) / name).relative_to(root).as_posix())
        paths.append(source)
    moved = []
    for source in paths:
        if source.exists():
            relative = source.relative_to(root)
            destination = output / "previous-reports" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            moved.append(relative.as_posix())
    return moved


def gradle_command(suite: str, test_plan: dict, simulator: str | None = None, *,
                   kotlin_user_home: str | None = None, root: Path = ROOT,
                   android_serial: str | None = None) -> list[str]:
    boundary_focus = validate_test_focus(test_plan)
    if boundary_focus and suite != test_plan["suite"]:
        raise ValueError("A focused test plan cannot run as another suite")
    if suite == "ios" and (not simulator or not runtime_context.UUID.fullmatch(simulator)):
        raise ValueError("iOS execution requires an explicitly selected, recorded simulator UDID")
    if suite != "ios" and simulator:
        raise ValueError("A simulator must not be supplied to a non-iOS test plan")
    if suite == "android-device":
        runtime_context.validate_emulator_serial(android_serial)
    elif android_serial is not None:
        raise ValueError("An Android emulator must not be supplied to another test suite")
    command = [".\\gradlew.bat" if os.name == "nt" else "./gradlew", "--continue", "--no-daemon",
               "--console=plain", "--no-configuration-cache", f"--max-workers={1 if suite == 'ios' else 2}",
               "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
               "-Pkotlin.compiler.execution.strategy=in-process", "-Pkotlin.native.jvmArgs=-Xmx2048m",
               "--init-script", "scripts/ci/fresh-tests.init.gradle.kts",
               "--init-script", "scripts/ci/daemon-jvm.init.gradle.kts"]
    if simulator:
        command.append(f"-PnativecmpkitSimulatorDevice={simulator}")
    if android_serial:
        # AGP9.4.0's inspected ProjectOptions reads this exact runner-argument
        # prefix. A native hang becomes a reported failure, never a passing skip.
        command.extend(["--no-parallel", "--stacktrace", f"-PnativecmpkitAndroidDeviceSerial={android_serial}",
                        "-Pandroid.testInstrumentationRunnerArguments.timeout_msec=120000"])
        if boundary_focus:
            item = test_plan["expected"][0]
            argument = "annotation" if test_plan["explicit_test_focus"] in ANDROID_SAVE_IDENTITY_FOCUSES else "class"
            command.append("-Pandroid.testInstrumentationRunnerArguments." + argument + "=" + item["test_filter"])
            if test_plan["explicit_test_focus"] == ANDROID_SAVE_IDENTITY_RECOVERY_FOCUS:
                command.append("-Pandroid.testInstrumentationRunnerArguments.notAnnotation=" + ANDROID_SAVE_CALIBRATION_ANNOTATION)
    if kotlin_user_home is not None:
        if suite not in {"js", "wasm"}:
            raise ValueError("A Kotlin user home may only be requested for JS/Wasm runs")
        home = safe_path(root, kotlin_user_home).resolve()
        build = safe_path(root, "build").resolve()
        if home == build or not home.is_relative_to(build):
            raise ValueError("Use a dedicated Kotlin user home strictly below the repository build directory")
        for entry in (home, *home.parents):
            if entry.is_relative_to(build) and entry.exists() and not entry.is_dir():
                raise ValueError("Kotlin user home path components must be directories")
        # Keep prepared contents; this records a request, not effective KGP use,
        # dependency integrity, recursive cache validation or filesystem isolation.
        command.append(f"-Pkotlin.user.home={home}")
    for item in test_plan["expected"]:
        command.append(item["task"])
        if boundary_focus and suite != "android-device":
            # KGP2.4.20 KotlinJsTest inherits AbstractTestTask's --tests filter.
            # Android instrumentation instead consumes its supported class argument.
            # Only the finite native registry permits multiple exact method
            # selectors; KGP joins these into one canonical gradle-filter argument.
            filters = (item["test_filter"].split(",")
                       if test_plan.get("explicit_test_focus") in UI_APPLICATION_FOCUS_SPECS
                       else (item["test_filter"],))
            for selector in filters:
                command.extend(["--tests", selector])
    return command


def terminate_owned(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        # PID belongs to this invocation. /T includes only its descendants.
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    else:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=30)


def execute(root: Path, command: list[str], log_path: Path, timeout: int, reserve_mib: int,
            *, env: dict[str, str] | None = None) -> dict:
    reserve = reserve_mib * 1024 * 1024
    if shutil.disk_usage(root).free < reserve:
        return {"exit_code": 75, "stop_reason": "Disk reserve unavailable; command not started"}
    started = time.monotonic()
    result = {}
    with log_path.open("w", encoding="utf-8") as log:
        kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, env=env, **kwargs)
        try:
            while process.poll() is None:
                if shutil.disk_usage(root).free < reserve:
                    result["stop_reason"] = "Disk reserve reached; terminated only this invocation's process group"
                elif time.monotonic() - started > timeout:
                    result["stop_reason"] = "Timeout; terminated only this invocation's process group"
                if result:
                    terminate_owned(process)
                    break
                time.sleep(1)
        except BaseException:
            terminate_owned(process)
            raise
        result.update(exit_code=process.returncode, elapsed_seconds=round(time.monotonic() - started, 2))
    return result


def execution_markers(log: Path) -> Counter:
    markers = Counter()
    if log.is_file():
        with log.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = re.match(r"^NATIVECMPKIT_TEST_RUNTIME task=(:[a-zA-Z0-9:_-]+) gradle=", line)
                if match:
                    markers[match.group(1)] += 1
    return markers


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_revision(root: Path) -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=30).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Unable to establish full source revision")
    return value


def android_device_environment(serial: str) -> dict[str, str]:
    """Select only the verified emulator in this child, without mutating its caller.

    AGP9.4.0's serial-option ListProperty is immutable but its device filter
    removes matching entries. Its supported ANDROID_SERIAL provider path uses
    a private mutable set instead. Reject conflicting inherited selection before
    report quarantine or process launch; never export the environment to receipts.
    """
    runtime_context.validate_emulator_serial(serial)
    environment = os.environ.copy()
    if environment.get("ANDROID_SERIAL") not in (None, serial):
        raise ValueError("Inherited Android selector differs from the explicitly owned emulator")
    environment["ANDROID_SERIAL"] = serial
    return environment


def ios_application_environment(root: Path, output: Path, test_plan: dict) -> dict[str, str] | None:
    """Only the real calf-ui iOS application task gets a fresh owned child path.

    Never mutate/export the caller's environment or let an inherited receipt path
    point the task at another run. Non-application targets retain their commands.
    """
    if test_plan["suite"] != "ios" or not any(i["module"] == "calf-ui" for i in test_plan["expected"]):
        return None
    relative = (output / "native-ui-application").relative_to(root).as_posix()
    safe_path(root, relative)
    environment = os.environ.copy()
    if environment.get("NATIVECMPKIT_UIKIT_RESULT_ROOT") not in (None, relative):
        raise ValueError("Inherited UIKit receipt selector differs from this fresh owned output")
    environment["NATIVECMPKIT_UIKIT_RESULT_ROOT"] = relative
    return environment


class IosApplicationEvidenceError(ValueError):
    """Only fixed contract messages, not native/exception/environment bodies."""


def collect_ios_application_receipts(root: Path, test_plan: dict, output: Path, started_ns: int, ended_ns: int,
                                     context: dict, modules: list[dict]) -> dict:
    """Cross-check the real app lifecycle against actual KGP XML and runtime.

    This reads the owned transport witness; it is not a trusted-builder attestation.
    Cases are never added to totals here, normalized broadly, synthesized or
    promoted from failed/skipped to passing. The normal JUnit gate still owns
    failures, including KGP's intentional native runner-exit-zero protocol.
    """
    result = {"ios_applications": [], "errors": []}
    if test_plan["suite"] != "ios" or not any(i["module"] == "calf-ui" for i in test_plan["expected"]):
        return result

    def need(condition, message):
        if not condition:
            raise IosApplicationEvidenceError(message)

    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            need(key not in value, "Duplicate JSON keys in application evidence")
            value[key] = item
        return value

    def identities(cases, xml=False):
        need(isinstance(cases, list) and 0 < len(cases) <= MAX_CASES, "Empty or unbounded application testcase set")
        values = {}
        for case in cases:
            need(isinstance(case, dict) and set(case) == {"classname", "name", "status"}, "Invalid application testcase fields")
            classname, name, status = (case[k] for k in ("classname", "name", "status"))
            need(all(isinstance(v, str) and 0 < len(v) <= 4096 and not any(c in v for c in "\r\n")
                     for v in (classname, name)), "Invalid application testcase identity")
            need(status in {"passed", "failed", "error", "skipped"}, "Unknown application testcase status")
            if xml:
                prefix, suffix = IOS_APPLICATION_TASK + ".", "[iosSimulatorArm64]"
                need(classname.startswith(prefix) and name.endswith(suffix), "XML lacks the exact observed KGP task prefix/target suffix")
                classname, name = classname[len(prefix):], name[:-len(suffix)]
            key = (classname, name)
            need(key not in values, "Duplicate application testcase identity")
            values[key] = status
        return values

    path = None
    try:
        expected = next(i for i in test_plan["expected"] if i["module"] == "calf-ui")
        task = ":calf-ui:" + IOS_APPLICATION_TASK
        need(expected["task"] == task and expected.get("native_test_host") == "genuine-uikit-application",
             "The iOS UI plan must use the genuine application task, not a Skiko fallback")
        folder = safe_path(root, (output / "native-ui-application").relative_to(root).as_posix())
        need(folder.is_dir(), "Missing owned UIKit application receipt output")
        sessions = []
        for entry in folder.iterdir():
            need(len(sessions) == 0 and re.fullmatch(r"[0-9a-f]{32}", entry.name), "Expected exactly one fresh application session")
            session = safe_path(root, entry.relative_to(root).as_posix())
            need(session.is_dir(), "Invalid application session directory")
            need([p.name for p in session.iterdir()] == ["receipt.json"], "Receipt missing or disposable app/other files remain")
            sessions.append(session)
        need(len(sessions) == 1, "Missing fresh application session")
        path = safe_path(root, (sessions[0] / "receipt.json").relative_to(root).as_posix())
        stat = path.stat()
        need(path.is_file() and stat.st_nlink == 1 and 0 < stat.st_size <= 2 * 1024**2, "Invalid or unbounded application receipt file")
        need(started_ns - 2_000_000_000 <= stat.st_mtime_ns <= ended_ns + 2_000_000_000, "Stale or future application receipt")
        payload = path.read_bytes()
        after = path.stat()
        need((stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
             "Application receipt changed while reading")
        document = json.loads(payload, object_pairs_hook=unique_object,
                              parse_constant=lambda _: need(False, "Nonfinite JSON number"))
        need(isinstance(document, dict) and type(document.get("schema_version")) is int and
             document["schema_version"] == 1 and document.get("task") == task,
             "Unexpected application receipt schema or task")
        need(document.get("transport_passed") is True and "error" not in document and
             "startup_failure_observation" not in document and "application_protocol_partial" not in document and
             "owned_crash_diagnostics" not in document,
             "Application transport failed or incomplete")
        need(document.get("explicit_test_focus") == test_plan.get("explicit_test_focus"),
             "Application selection differs from its reviewed plan")
        focused_ui = test_plan.get("explicit_test_focus") in UI_APPLICATION_FOCUS_SPECS
        if focused_ui:
            validate_test_focus(test_plan)
        need(document.get("packages_published") is False and document.get("release_readiness_certified") is False,
             "Verification must not claim publication or release certification")
        need(context.get("source_tree_dirty") is False and document.get("source_tree_dirty") is False and
             document.get("source_revision") == context.get("source_revision"), "Application source revision/cleanliness mismatch")
        for when in ("runtime_before", "runtime_after"):
            observed = document.get(when)
            need(isinstance(observed, dict) and observed.get("source_revision") == context["source_revision"] and
                 observed.get("source_tree_dirty") is False, "Application runtime source identity changed")
            for key in ("host", "java", "rust", "xcode", "apple_sdks", "simulator"):
                need(key in context and observed.get(key) == context[key], "Application compiler/SDK/selected-simulator runtime mismatch")
        need(context["host"].get("system") == "Darwin" and context["host"].get("architecture") == "arm64" and
             context["simulator"].get("state") == "Booted" and runtime_context.UUID.fullmatch(context["simulator"].get("udid", "")),
             "A genuine booted Arm64 Apple application runtime is required")
        times = [dt.datetime.fromisoformat(document[key]) for key in ("started_at_utc", "finished_at_utc")]
        need(all(t.utcoffset() is not None for t in times), "Naive application timestamps do not establish freshness")
        start, end = (int(t.timestamp() * 1_000_000_000) for t in times)
        need(started_ns - 2_000_000_000 <= start <= end <= ended_ns + 2_000_000_000, "Application lifecycle lies outside the fresh run")
        token = sessions[0].name
        need(document.get("bundle_id") == "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" +
             context["source_revision"][:12] + ".t" + token, "Application bundle is not this owned source/session")
        # Import after this module is fully loaded; the transport uses the same
        # safe-path/hash contract and the real Mach-O load-command reader.
        import ios_ui_application as app
        binary = safe_path(root, document["binary_path"])
        need(binary.parent == safe_path(root, app.EXPECTED_BINARY_DIRECTORY) and binary.suffix == ".kexe" and
             os.access(binary, os.X_OK), "Wrong linked application binary")
        binary_hash = sha256(binary)
        need(document.get("binary_sha256") == document.get("binary_sha256_after") == binary_hash and
             document.get("macho") == app.macho_simulator_identity(binary), "Linked binary bytes or Mach-O identity changed")
        need(all(isinstance(document.get(k), str) and re.fullmatch(r"[0-9a-f]{64}", document[k])
                 for k in ("signed_application_executable_sha256", "application_plist_sha256")), "Missing installed app-byte identities")
        steps, cleanup = document.get("steps"), document.get("cleanup")
        need(isinstance(steps, dict) and isinstance(cleanup, dict), "Missing application install/cleanup steps")
        need(all(isinstance(steps.get(k), dict) for k in
                 ("foreign-app-preflight", "adhoc-sign-local-verification-app", "install-owned-app")),
             "Invalid application step record shapes")
        need(all(type(steps[k].get("exit_code")) is int for k in
                 ("foreign-app-preflight", "adhoc-sign-local-verification-app", "install-owned-app")),
             "Application control exit codes must be actual integer observations")
        need(steps.get("foreign-app-preflight", {}).get("preexisting_app_absence_verified") is True and
             steps.get("adhoc-sign-local-verification-app", {}).get("exit_code") == 0 and
             steps.get("adhoc-sign-local-verification-app", {}).get("remote_signing_or_publication") is False and
             steps.get("install-owned-app", {}).get("exit_code") == 0 and
             steps.get("install-owned-app", {}).get("installed_owned_bytes_verified") is True, "Owned app install/sign/readback did not pass")
        need(not any("error" in k for k in cleanup) and type(cleanup.get("uninstall_exit_code")) is int and
             cleanup["uninstall_exit_code"] == 0 and all(cleanup.get(k) is True for k in
                 ("owned_app_identity_reverified", "owned_app_stopped_verified", "owned_app_absence_verified", "owned_local_bundle_removed")),
             "Owned app/native/local cleanup did not complete")
        protocol = document.get("application_protocol")
        need(isinstance(protocol, dict) and type(protocol.get("process_exit")) is int and protocol["process_exit"] == 0,
             "App crash or missing real console process exit")
        active, complete = protocol.get("activation"), protocol.get("completion")
        need(isinstance(active, dict) and all(type(active.get(k)) is int and active[k] > 0 for k in ("main_worker", "owned_worker")) and
             active["main_worker"] != active["owned_worker"], "Missing distinct main/owned-worker execution witness")
        need(isinstance(complete, dict) and type(complete.get("runner_exit")) is int and complete["runner_exit"] == 0 and
             complete.get("worker_terminated") is True, "Generated test Worker did not terminate before app completion")
        need(type(protocol.get("stream_bytes")) is int and 0 < protocol["stream_bytes"] <= app.MAX_STREAM_BYTES,
             "Invalid application console byte witness")
        cases = identities(protocol.get("testcases"))
        module = next(m for m in modules if m["module"] == "calf-ui")
        need(module["task"] == task and cases == identities(module["testcases"], xml=True), "Actual KGP XML and app protocol disagree")
        counts = case_counts(protocol["testcases"])
        need(protocol.get("counts") == counts and all(type(v) is int for v in protocol["counts"].values()) and counts["executed"] > 0,
             "Application counts differ from complete actual testcase elements")
        required = ({(group["classname"], name)
                     for group in ui_application_focus_groups(test_plan["explicit_test_focus"])
                     for name in group["methods"]} if focused_ui else
                    {("com.mohamedrejeb.calf.ui." + c, n) for c, n in IOS_APPLICATION_CASES})
        if focused_ui:
            need(cases.keys() == required, "Focused application must execute exactly all selected methods")
        need(required <= cases.keys(), "Required native presenter/host/identity/image-lifetime cases were not discovered")
        if cases.get(app.IMAGE_LIFETIME_CASE) == "passed":
            observation = protocol.get("image_lifetime_observation")
            need(isinstance(observation, dict) and type(observation.get("marker_count")) is int and
                 observation["marker_count"] == len(app.IMAGE_LIFETIME_STEPS) and observation.get("last_phase") == "verified" and
                 observation.get("last_iteration") is None and observation.get("main_thread") is True and
                 observation.get("retained_image_bytes_verified") is True,
                 "Passing image-lifetime case lacks complete finite actual main-thread diagnostics")
        if test_plan.get("explicit_test_focus") == UI_DATE_COMPACT_FOCUS:
            observation = protocol.get("compact_appearance_observation")
            fields = {"background_matches", "tint_matches", "attached", "enabled", "rtl", "dark", "main_thread"}
            need(isinstance(observation, list) and len(observation) == len(app.COMPACT_APPEARANCE_PHASES),
                 "Focused compact case lacks complete actual native appearance diagnostics")
            need(all(isinstance(step, dict) and set(step) == fields | {"phase"} and
                     step["phase"] == app.COMPACT_APPEARANCE_PHASES[index] and
                     all(type(step[k]) is bool for k in fields) and step["main_thread"] is True and
                     step["attached"] == (index in range(2, 7))
                     for index, step in enumerate(observation)),
                 "Focused compact diagnostic shape/order/thread/owned attachment is invalid")
        result["ios_applications"].append({"module": "calf-ui", "task": task, "receipt_path": path.relative_to(root).as_posix(),
            "receipt_sha256": hashlib.sha256(payload).hexdigest(), "protocol_xml_agreement": True,
            "counts": counts, "required_native_cases_found": len(required), "binary_sha256": binary_hash,
            "bundle_id": document["bundle_id"], "selected_simulator": context["simulator"]["udid"],
            "activation": active, "completion": complete,
            "scope": "Same-source real application/Worker/cleanup witness cross-checked against fresh KGP XML; not physical-device, ABI or release certification",
            **({"compact_appearance_observation": protocol["compact_appearance_observation"]}
               if test_plan.get("explicit_test_focus") == UI_DATE_COMPACT_FOCUS else {})})
    except (OSError, ValueError, TypeError, KeyError, StopIteration, RecursionError) as error:
        record = {"module": "calf-ui", "error": "Genuine UIKit application evidence rejected",
                  "contract": str(error) if isinstance(error, IosApplicationEvidenceError) else type(error).__name__}
        if path is not None:
            record["path"] = path.relative_to(root).as_posix()
        result["errors"].append(record)
    return result


def run(root: Path, suite: str, output_relative: str, simulator: str | None, timeout: int, reserve_mib: int,
        only_modules: tuple[str, ...] | None = None, *, kotlin_user_home: str | None = None,
        android_serial: str | None = None, focus: str | None = None) -> dict:
    output = safe_path(root, output_relative)
    allowed = root / "build/ci-verification"
    if output == allowed or not output.is_relative_to(allowed) or output.exists():
        raise ValueError("Use a new, dedicated output directory below build/ci-verification; old evidence must not be overwritten")
    test_plan = plan(root, suite, only_modules=only_modules, **({"focus": focus} if focus is not None else {}))
    command = gradle_command(suite, test_plan, simulator, kotlin_user_home=kotlin_user_home, root=root,
                             android_serial=android_serial)
    execution_environment = android_device_environment(android_serial) if android_serial else None
    application_environment = ios_application_environment(root, output, test_plan)
    if application_environment is not None:
        execution_environment = application_environment
    allowed.mkdir(parents=True, exist_ok=True)
    lock = allowed / ".library-tests.lock"
    # Do not auto-remove an existing lock: another coordinated run may own it.
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, f"{os.getpid()}\n".encode())
        output.mkdir(parents=True)
        revision_before = git_revision(root)
        before = snapshot_inputs(root)
        write_json(output / "inputs-before.json", before)
        write_json(output / "plan.json", test_plan)
        # Every configured Gradle build includes Android projects, including
        # desktop/browser/Apple verification. Match the workflow's official SDK
        # context instead of dropping it from the actual library-run receipt.
        context = runtime_context.capture(apple=suite == "ios", device=simulator,
                                          require_booted=suite == "ios",
                                          android_package="android-37.0",
                                          android_serial=android_serial,
                                          browser=suite in {"js", "wasm"})
        if context["source_revision"] != revision_before:
            raise ValueError("Source revision changed while preparing the test invocation")
        write_json(output / "runtime.json", context)
        moved = quarantine_reports(root, output, test_plan)
        started_ns = time.time_ns()
        started_utc = utc_now()
        execution = execute(root, command, output / "gradle.log", timeout, reserve_mib,
                            **({"env": execution_environment} if execution_environment is not None else {}))
        ended_ns = time.time_ns()
        receipt = {"schema_version": 1, "suite": suite, "started_at_utc": started_utc, "finished_at_utc": utc_now(),
                   "source_revision": context["source_revision"], "source_tree_dirty": context["source_tree_dirty"],
                   "command": command, "execution": execution, "quarantined_prior_reports": moved,
                   "inputs_before_sha256": input_digest(before), "runtime_receipt_sha256": sha256(output / "runtime.json"),
                   "uncovered": test_plan["uncovered"],
                   "complete_suite_requested": test_plan["complete_suite_requested"],
                   "explicit_module_subset": test_plan["explicit_module_subset"],
                   "test_bearing_modules_not_requested": test_plan["test_bearing_modules_not_requested"],
                   "scope": "Fresh source-bound library suite executions; not whole-library/device/ABI/release certification"}
        if focus is not None:
            receipt["explicit_test_focus"] = focus
            receipt["required_focused_testcases"] = test_plan["expected"][0]["required_testcases"]
            receipt["scope"] = test_plan["scope"]
        try:
            after = snapshot_inputs(root)
            write_json(output / "inputs-after.json", after)
            receipt["inputs_after_sha256"] = input_digest(after)
            receipt["changed_inputs"] = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
            receipt["source_revision_after"] = git_revision(root)
            if receipt["source_revision_after"] != revision_before:
                receipt["input_capture_error"] = "Git source revision changed during test invocation"
        except (OSError, ValueError):
            receipt["input_capture_error"] = "Unable to establish unchanged source inputs after execution"
        if android_serial:
            receipt["android_device_selection"] = {"mechanism": "ANDROID_SERIAL", "serial": android_serial,
                                                   "agp_target_serial_options": "empty"}
            try:
                after_context = runtime_context.capture(android_serial=android_serial)
                receipt["android_emulator_after"] = after_context["android_emulator"]
                if receipt["android_emulator_after"] != context["android_emulator"]:
                    receipt["device_context_error"] = "Selected Android emulator identity or security/boot state changed during execution"
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                receipt["device_context_error"] = "Selected Android emulator identity/security state could not be re-established after execution"
        markers = execution_markers(output / "gradle.log")
        receipt["task_execution_markers"] = {item["task"]: markers[item["task"]] for item in test_plan["expected"]}
        receipt.update(collect_reports(root, test_plan, started_ns, ended_ns, markers,
                                       host_system=context["host"]["system"],
                                       native_ui_opt_in=os.environ.get("NATIVECMPKIT_NATIVE_UI_TESTS") == "true"))
        applications = collect_ios_application_receipts(root, test_plan, output, started_ns, ended_ns, context, receipt["modules"])
        receipt["ios_applications"] = applications["ios_applications"]
        receipt["errors"].extend(applications["errors"])
        try:
            receipt["gradle_daemon"] = daemon_jvm.observation(output / "gradle.log")
            if context.get("java", {}).get("major") != receipt["gradle_daemon"]["major"]:
                receipt["errors"].append({"error": "Actual daemon major differs from the recorded setup Java runtime"})
        except (OSError, ValueError, UnicodeError) as error:
            receipt["errors"].append({"error": "Actual root-daemon observation rejected", "reason": type(error).__name__})
        receipt["passed"] = (execution["exit_code"] == 0 and not execution.get("stop_reason") and not receipt["errors"]
                             and not receipt.get("input_capture_error") and not receipt.get("changed_inputs")
                             and not receipt.get("device_context_error"))
        write_json(output / "receipt.json", receipt)
        return receipt
    finally:
        os.close(descriptor)
        lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["plan", "run"])
    parser.add_argument("--suite", choices=sorted(SUITES), required=True)
    parser.add_argument("--module", action="append", help="Explicit module-directory subset for investigation only; never reported as the complete CI suite")
    parser.add_argument("--focus", choices=[NATIVE_SHARE_BOUNDARY_FOCUS, DATE_TRANSACTION_FOCUS, UNSUPPORTED_PERMISSION_FOCUS,
                                           IOS_PERMISSION_FOCUS, IOS_PERMISSION_SAFETY_FOCUS, IOS_PERMISSION_BATCH_FOCUS, IOS_SAVE_WRITE_FOCUS,
                                           ANDROID_PERMISSION_COMPLETION_FOCUS, ANDROID_IO_OVERSIZE_FOCUS, *ANDROID_SAVE_IDENTITY_FOCUSES, UI_DATE_BOUNDS_FOCUS,
                                           UI_DATE_REPLACEMENT_FOCUS, UI_DATE_COMPACT_FOCUS, UI_DATE_IMPORTANT_FOCUS],
                        help="Finite source-reviewed important tests only; never complete suite coverage")
    parser.add_argument("--output", help="A new repository-relative directory below build/ci-verification (run only)")
    parser.add_argument("--simulator", help="The actual selected and booted iOS simulator UDID")
    parser.add_argument("--android-emulator", help="Explicit owned, booted and enforcing emulator serial (Android-device run only)")
    parser.add_argument("--kotlin-user-home", help="JS/Wasm run only: repository-relative directory strictly below build; records an explicit Gradle property request, not proof of effective use; prepared contents are retained")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--reserve-mib", type=int, default=8192)
    args = parser.parse_args()
    if args.timeout < 1 or args.reserve_mib < 1024:
        parser.error("Require a positive timeout and at least a 1GiB disk reserve")
    if args.kotlin_user_home is not None and (args.operation != "run" or args.suite not in {"js", "wasm"}):
        parser.error("--kotlin-user-home is available only for JS/Wasm run")
    if args.android_emulator is not None and (args.operation != "run" or args.suite != "android-device"):
        parser.error("--android-emulator is available only for Android-device run")
    if args.focus is not None and not allowed_test_focus(args.suite, tuple(args.module or ()), args.focus):
        parser.error("--focus requires its exact reviewed suite and single --module")
    if args.operation == "plan":
        if args.output or args.simulator:
            parser.error("plan is read-only and takes neither output nor simulator")
        print(json.dumps(plan(ROOT, args.suite, only_modules=tuple(args.module or ()),
                              **({"focus": args.focus} if args.focus is not None else {})), indent=2, sort_keys=True))
        return 0
    if not args.output:
        parser.error("run requires a new --output directory")
    options = {"kotlin_user_home": args.kotlin_user_home}
    if args.android_emulator is not None:
        options["android_serial"] = args.android_emulator
    if args.focus is not None:
        options["focus"] = args.focus
    receipt = run(ROOT, args.suite, args.output, args.simulator, args.timeout, args.reserve_mib, tuple(args.module or ()),
                  **options)
    print(json.dumps({key: receipt[key] for key in ("suite", "source_revision", "passed", "complete_suite_requested", "explicit_module_subset", "execution", "totals", "errors")}, indent=2, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Library test verification refused: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)
