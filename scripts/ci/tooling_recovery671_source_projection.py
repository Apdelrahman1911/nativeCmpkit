# SPDX-License-Identifier: Apache-2.0
"""Finite671 source/fixture custody, never native or issue acceptance.

Only complete reviewed inverse/forward source arithmetic is performed. The finite
owning tooling/fixture derivatives and composed outer guard retain every original
literal and dated manifest. No restored code, compiler, selector, native tool,
network query, Git operation or historical fixture population is executed here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/tooling_recovery671_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/tooling-recovery671-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/tooling-recovery671-source-inverse.json"
SPEC_SHA256 = "9def6c416e199237600bdcdc2a16a3fd22dc2158796e1116f999b8681c96a110"
PREDECESSOR = 'afc0a727f60a9278c96cf9721157ba7413229c10'
BOUND_PATHS = frozenset({
    'scripts/ci/android_camera_callback_native_focus.py',
    'scripts/ci/android_camera_developer_prerequisite.py',
    'scripts/ci/android_io_remote_routing_source_projection.py',
    'scripts/ci/camera_recents_fixture_source_projection.py',
    'scripts/ci/camera_recents_source_projection.py',
    'scripts/ci/test_android_combined_finite_routing.py',
    'scripts/ci/test_android_geo_ownership.py',
    'scripts/ci/test_android_geo_prerequisites.py',
    'scripts/ci/test_android_geo_provider.py',
    'scripts/ci/test_android_io_default_decode.py',
    'scripts/ci/test_android_share_grants.py',
    'scripts/ci/test_android_storage_probe.py',
    'scripts/ci/test_android_verification_contract.py',
    'scripts/ci/test_android_webview_stop_redirect_recovery.py',
    'scripts/ci/test_apple_image_launcher_source_projection.py',
    'scripts/ci/test_camera_recents_fixture_recovery.py',
    'scripts/ci/test_desktop_webview_literal_matrix.py',
    'scripts/ci/test_desktop_webview_stop_windows_recovery.py',
    'scripts/ci/test_image_profile_readiness.py',
    'scripts/ci/test_ios_webview_current_request_metadata.py',
    'scripts/ci/test_webview_content_policy_source.py',
    'scripts/ci/test_webview_request_focus.py',
})
ADDED_PATHS = frozenset({
    'scripts/ci/fixtures/tooling-recovery671-composed-routing680.json',
    'scripts/ci/test_shared_tooling_recovery671.py',
})
UNCHANGED_PATHS = frozenset({
    '.github/workflows/gradle.yml',
    'build.gradle.kts',
    'calf-camera-picker/build.gradle.kts',
    'calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraCallbackSubstitutionTest.kt',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraProviderTest.kt',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRestorationVerificationActivity.kt',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraVerificationProviders.kt',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedCameraReceiver.kt',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt',
    'calf-camera-picker/src/androidDeviceTest/res/xml/nativecmpkit_camera_device_paths.xml',
    'calf-camera-picker/src/androidDeviceTest/res/xml/nativecmpkit_camera_device_wrong_paths.xml',
    'calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt',
    'calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt',
    'calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerResult.kt',
    'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRequestStateTest.kt',
    'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaseline.kt',
    'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaselineTest.kt',
    'calf-camera-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/camerapicker/IosCameraOwnershipAcceptanceTest.kt',
    'calf-io/build.gradle.kts',
    'calf-io/src/androidDeviceTest/AndroidManifest.xml',
    'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoRemoteDocumentsTest.kt',
    'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoRemoteTreeGrantActivity.kt',
    'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoSystemTreeGrantActivity.kt',
    'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/DeviceDescriptorProbe.kt',
    'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/NamedSystemDocumentsUi.kt',
    'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/OwnedIoEndpoint.kt',
    'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/RemoteIoEndpoint.kt',
    'calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt',
    'calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFileBookmark.android.kt',
    'calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFileSource.android.kt',
    'calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/BoundedRead.kt',
    'calf-ui/build.gradle.kts',
    'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButton.kt',
    'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt',
    'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlight.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/button/LiquidButtonConstructionTraceTest.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/PointerCancellation.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragLifecycleRegressionTest.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlightResourceLifecycleTest.kt',
    'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UiDragShaderTestHost.kt',
    'calf-webview/build.gradle.kts',
    'calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewContentPolicyAcceptanceTest.kt',
    'calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt',
    'calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt',
    'calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebViewContracts.kt',
    'calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt',
    'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewContentPolicyAcceptanceTest.kt',
    'calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt',
    'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewContentPolicyAcceptanceTest.kt',
    'calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt',
    'calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserWebViewContentPolicyAcceptanceTest.kt',
    'convention-plugins/src/main/kotlin/Android.kt',
    'docs/development/android-io-controlled-remote-provider.md',
    'docs/testing/android-camera-callback-substitution.md',
    'gradle.properties',
    'gradle/libs.versions.toml',
    'scripts/ci/android_camera_receiver.py',
    'scripts/ci/android_device_tests.py',
    'scripts/ci/android_geo_probe.py',
    'scripts/ci/android_io_documents.py',
    'scripts/ci/android_io_remote_documents.py',
    'scripts/ci/android_share_recipient.py',
    'scripts/ci/apple_image_launch_readiness.py',
    'scripts/ci/apple_image_sidecar_evidence.py',
    'scripts/ci/fixtures/android-camera-callback672-source-inverse.json',
    'scripts/ci/fixtures/android-io-controlled-remote-routing-source-inverse.json',
    'scripts/ci/fixtures/apple-image-launcher-source-inverse.json',
    'scripts/ci/fixtures/calendar-share-selector-source-inverse.json',
    'scripts/ci/fixtures/camera-boot-busy-source-inverse.json',
    'scripts/ci/fixtures/camera-boot-handoff-source-inverse.json',
    'scripts/ci/fixtures/camera-handoff-fixture-source-inverse.json',
    'scripts/ci/fixtures/camera-home-baseline-source-inverse.json',
    'scripts/ci/fixtures/camera-ios-ownership-routing-source-inverse.json',
    'scripts/ci/fixtures/camera-recents-fixture-source-inverse.json',
    'scripts/ci/fixtures/camera-recents-observation-source-inverse.json',
    'scripts/ci/fixtures/camera-tooling562-source-inverse.json',
    'scripts/ci/fixtures/camera-tooling566-source-inverse.json',
    'scripts/ci/fixtures/ios-ui-related-source-inverse.json',
    'scripts/ci/fixtures/ios-ui-split664-source-inverse.json',
    'scripts/ci/fixtures/platform-recovery659-source-inverse.json',
    'scripts/ci/fixtures/webview-content-policy-routing-source-inverse.json',
    'scripts/ci/fixtures/webview-current-contract667-source-inverse.json',
    'scripts/ci/fresh-tests.init.gradle.kts',
    'scripts/ci/ios_adaptive_controls_native.init.gradle.kts',
    'scripts/ci/ios_adaptive_controls_native_focus.py',
    'scripts/ci/ios_adaptive_controls_runtime.py',
    'scripts/ci/ios_popover_anchor_plan.py',
    'scripts/ci/ios_ui_adaptive_drag_shader_native.init.gradle.kts',
    'scripts/ci/ios_ui_application.py',
    'scripts/ci/ios_ui_related_native_focus.py',
    'scripts/ci/ios_ui_related_source_projection.py',
    'scripts/ci/ios_ui_split664_source_projection.py',
    'scripts/ci/ios_ui_split_native.init.gradle.kts',
    'scripts/ci/library_tests.py',
    'scripts/ci/platform_recovery659_source_projection.py',
    'scripts/ci/runtime_context.py',
    'scripts/ci/test_android_camera_callback_native_focus.py',
    'scripts/ci/test_android_camera_provider.py',
    'scripts/ci/test_android_io_remote_documents.py',
    'scripts/ci/test_android_io_remote_routing.py',
    'scripts/ci/test_android_io_remote_routing_source_projection.py',
    'scripts/ci/test_android_io_reporter_manifest_union.py',
    'scripts/ci/test_apple_image_sidecar_evidence.py',
    'scripts/ci/test_ios_application_receipts.py',
    'scripts/ci/test_ios_ui_related_source_projection.py',
    'scripts/ci/test_ios_ui_split664_native_routing.py',
    'scripts/ci/test_platform_recovery659_source_projection.py',
    'scripts/ci/test_webview_content_policy_native_focus.py',
    'scripts/ci/test_webview_current_contract667_source_projection.py',
    'scripts/ci/webview_content_policy_native_focus.py',
    'scripts/ci/webview_current_contract667_source_projection.py',
    'scripts/ci/workflow_matrix.py',
    'settings.gradle.kts',
    'tests/consumer/android-camera-receiver/build.gradle.kts',
    'tests/consumer/android-camera-receiver/settings.gradle.kts',
    'tests/consumer/android-camera-receiver/src/main/AndroidManifest.xml',
    'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraDelayedReceiverActivity.java',
    'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverActivity.java',
    'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverService.java',
    'tests/consumer/android-io-remote-documents/README.md',
    'tests/consumer/android-io-remote-documents/build.gradle.kts',
    'tests/consumer/android-io-remote-documents/gradle.properties',
    'tests/consumer/android-io-remote-documents/settings.gradle.kts',
    'tests/consumer/android-io-remote-documents/src/main/AndroidManifest.xml',
    'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoContract.java',
    'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoControlService.java',
    'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoDocumentsProvider.java',
    'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoHttpBackend.java',
    'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoHttpTransport.java',
    'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoProviderWitnessService.java',
})
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 256 * 1024

COMPOSITION_RELATIVE = 'scripts/ci/fixtures/tooling-recovery671-composed-routing680.json'
COMPOSITION_SHA256 = 'b853b524177cfa51c175f9c3bc7d3cd301c5db0aec7e335f6739fdca07332871'
MAX_COMPOSITION_BYTES = 512 * 1024
COMPOSITION_SCOPE = 'Exactly seven complete lead680 callback-over-IO/UI byte views; never restored-source execution or native acceptance'
COMPOSITION_PATHS = frozenset({
    '.github/workflows/gradle.yml',
    'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraProviderTest.kt',
    'scripts/ci/android_device_tests.py',
    'scripts/ci/fresh-tests.init.gradle.kts',
    'scripts/ci/library_tests.py',
    'scripts/ci/test_android_camera_provider.py',
    'scripts/ci/workflow_matrix.py',
})
COMPOSITION_ORIGINS = {'scripts/ci/fixtures/android-camera-callback672-source-inverse.json': '1c14d6fcb7dc49716de3688169c9280fde51f62564d1593a6a95707f85f19f7a', 'scripts/ci/fixtures/android-io-controlled-remote-routing-source-inverse.json': '4dee514d6aa6bdfaf5856a24416cfb7a677f67daeed9f7fed9b43215e31e95de', 'scripts/ci/fixtures/ios-ui-split664-source-inverse.json': '1455a8edb3553a87a409f7fc30568ede9f7f52fe97042690b668dc6ebc145f4a'}
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SCOPE = "Exact shared-tooling671 derivative custody only; no compiler/native/issue acceptance"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate tooling671 manifest field")
        value[key] = item
    return value


def _shape(document):
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "predecessor", "bindings", "added_inputs", "unchanged_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != _SCOPE or document["predecessor"] != PREDECESSOR or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict or set(document["unchanged_inputs"]) != UNCHANGED_PATHS or
            type(document["own_guard"]) is not dict or set(document["own_guard"]) != {"template_sha256", "bytes"} or
            type(document["own_guard"]["bytes"]) is not int or
            not 0 < document["own_guard"]["bytes"] <= MAX_SOURCE_BYTES or
            type(document["own_guard"]["template_sha256"]) is not str or
            _DIGEST.fullmatch(document["own_guard"]["template_sha256"]) is None):
        raise ValueError("The exact finite tooling671 manifest schema is required")
    for row in document["bindings"].values():
        if (type(row) is not dict or set(row) != {
                "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES
                    for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None
                    for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 12):
            raise ValueError("Exact complete tooling671 source bindings are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                    "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None
                        for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite unique tooling671 fragment identities are required")
    for rows in (document["added_inputs"], document["unchanged_inputs"]):
        if any(type(digest) is not str or _DIGEST.fullmatch(digest) is None for digest in rows.values()):
            raise ValueError("Exact tooling671 ordinary input hashes are required")
    return document


def _document():
    from ios_popover_anchor_plan import _ordinary_bytes
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded tooling671 manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact tooling671 derivative manifest changed")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite tooling671 manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The complete tooling671 manifest JSON is required") from None
    return _shape(document)


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact tooling671 relative identity and ordinary source bytes are required")


def source_before_tooling671(relative, payload):
    """Complete exact inverse or its one declared predecessor; never current admission."""
    _identity(relative, payload)
    import ci668_outer_source_projection as ci668
    import ci_source_domain740 as domain740
    payload = domain740.peel_domain740_for_history(relative, payload)
    payload = ci668.peel_ci668_for_history(relative, payload)
    payload = domain740.peel_bridge740_for_history(relative, payload)
    return _source_before_tooling671_document(relative, payload, _document())


def _source_before_tooling671_document(relative, payload, document):
    """Exact inverse arithmetic from an already fresh owning document; never admission."""
    _identity(relative, payload)
    binding = document["bindings"].get(relative)
    if binding is None:
        return payload  # Unlisted source bytes are never certified, guessed or reconstructed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded complete tooling671 source bytes are required")
    observed = sha(payload)
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("Tooling671 source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact finite unique tooling671 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != binding["before_sha256"] or len(restored) != binding["before_bytes"]:
        raise ValueError("Tooling671 inverse did not restore the complete declared predecessor")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact finite unique tooling671 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Tooling671 complete inverse/forward source roundtrip differs")
    return restored


def current_source_before_tooling671(relative, payload):
    """One strict raw ingress; declared old, partial, displaced and drift images refuse."""
    _identity(relative, payload)
    import ci668_outer_source_projection as ci668
    import macos_share_ci668_composition as joint
    import ci_source_domain740 as domain740
    if relative in joint.fixture_inputs():
        payload = ci668.current_source_before_ci668(relative, payload)
        payload = domain740.bridge_after_qualified_current_ingress(relative, payload)
    else:
        # Data outside current303 stays unqualified; the original upper owner still checks.
        payload = domain740.current_source_before_domain740(relative, payload)
    document = _document()
    binding = document["bindings"].get(relative)
    digest = (binding["after_sha256"] if binding is not None else
              (document["added_inputs"] | document["unchanged_inputs"]).get(relative))
    if digest is not None and (sha(payload) != digest or binding is not None and len(payload) != binding["after_bytes"]):
        raise ValueError("An old or unknown image cannot replace exact current tooling671 source")
    return source_before_tooling671(relative, payload)


def peel_tooling671_for_history(relative, payload):
    """Peel only a complete latest image; pass-through is not current certification."""
    _identity(relative, payload)
    import ci668_outer_source_projection as ci668
    import ci_source_domain740 as domain740
    payload = domain740.peel_domain740_for_history(relative, payload)
    payload = ci668.peel_ci668_for_history(relative, payload)
    payload = domain740.peel_bridge740_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and sha(payload) == binding["after_sha256"] and len(payload) == binding["after_bytes"]:
        return source_before_tooling671(relative, payload)
    return payload  # Every other image still faces the unchanged next sealed historical pin.


def _composition_document():
    """One sealed finite680 view document; no path search or ancestor-code execution."""
    from ios_popover_anchor_plan import _ordinary_bytes
    path = ROOT / COMPOSITION_RELATIVE
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_COMPOSITION_BYTES:
        raise ValueError("One ordinary bounded composed680 source document is required")
    raw = _ordinary_bytes(ROOT, COMPOSITION_RELATIVE)[0]
    if (not 0 < len(raw) <= MAX_COMPOSITION_BYTES or sha(raw) != COMPOSITION_SHA256 or
            _document()["added_inputs"].get(COMPOSITION_RELATIVE) != COMPOSITION_SHA256):
        raise ValueError("The exact finite composed680 source document changed")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite composed680 document")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("Complete composed680 source JSON is required") from None
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "root_predecessor", "lead_result_sha256", "lead_context_sha256",
            "origin_manifests", "callback_above_io", "callback_isolated"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != COMPOSITION_SCOPE or document["root_predecessor"] != PREDECESSOR or
            document["lead_result_sha256"] != "f1703531c4e54459475e4d6087ad711f8504da9776e7ab71a2454b006e9f3c97" or
            document["lead_context_sha256"] != "4c26c8e8b880c1185a985f1323e0bc704e7484ac008210eab7b620c3aa5d5e4b" or
            type(document["origin_manifests"]) is not dict or document["origin_manifests"] != COMPOSITION_ORIGINS):
        raise ValueError("The exact seven-path composed680 source schema is required")
    for relative, digest in COMPOSITION_ORIGINS.items():
        if sha(_ordinary_bytes(ROOT, relative)[0]) != digest:
            raise ValueError("An original sealed composed680 layer manifest changed: " + relative)
    owning = _document()
    for view in ("callback_above_io", "callback_isolated"):
        rows = document[view]
        if type(rows) is not dict or set(rows) != COMPOSITION_PATHS:
            raise ValueError("Exactly the seven complete composed680 source identities are required")
        for relative, row in rows.items():
            if (type(row) is not dict or set(row) != {
                    "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                    any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES
                        for key in ("before_bytes", "after_bytes")) or
                    any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None
                        for key in ("before_sha256", "after_sha256")) or
                    type(row["fragments"]) is not list or not 0 <= len(row["fragments"]) <= 128 or
                    view == "callback_above_io" and not row["fragments"]):
                raise ValueError("Complete bounded composed680 source bindings are required")
            expected680 = (owning["bindings"][relative]["before_sha256"] if relative in owning["bindings"]
                           else owning["unchanged_inputs"].get(relative))
            if row["before_sha256"] != expected680:
                raise ValueError("The complete680 endpoint must equal its independently sealed671 predecessor")
            for fragment in row["fragments"]:
                if (type(fragment) is not dict or set(fragment) != {
                        "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                        any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                        fragment["before"] == fragment["after"] or
                        any(_DIGEST.fullmatch(fragment[key]) is None
                            for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                        any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                    raise ValueError("Exact finite composed680 fragment identities are required")
    callback_spec = json.loads(_ordinary_bytes(ROOT, "scripts/ci/fixtures/android-camera-callback672-source-inverse.json")[0],
                               object_pairs_hook=_unique)
    if (set(callback_spec["bindings"]) != COMPOSITION_PATHS or
            any(row["after_sha256"] != callback_spec["bindings"][relative]["after_sha256"] or
                row["after_bytes"] != callback_spec["bindings"][relative]["after_bytes"]
                for relative, row in document["callback_isolated"].items())):
        raise ValueError("Every isolated callback view must equal its unchanged original sealed complete afterimage")
    return document


def _complete_composition_view(relative, payload, view):
    """Two explicitly named finite views only; never generic peeling or current admission."""
    _identity(relative, payload)
    if view not in ("callback_above_io", "callback_isolated"):
        raise ValueError("Only the two exact reviewed composed680 byte views are defined")
    row = _composition_document()[view].get(relative)
    return _complete_composition_view_row680(payload, row)


def _complete_composition_view_row680(payload, row):
    """An already owner-qualified finite row; no schema/current/source certification."""
    _identity("", payload)
    if row is None:
        return payload  # Unlisted bytes are not certified, inferred, searched or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Complete bounded composed680 source bytes are required")
    observed = sha(payload)
    if (observed == row["after_sha256"] and len(payload) == row["after_bytes"] and
            row["before_sha256"] != row["after_sha256"]):
        return payload  # One explicitly declared qualified ancestor, not another raw-current ingress.
    if observed != row["before_sha256"] or len(payload) != row["before_bytes"]:
        raise ValueError("Source is neither its complete qualified680 endpoint nor its one declared ancestor view")
    restored = payload
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(before) != 1):
            raise ValueError("Exact unique composed680 source-view fragments are required")
        restored = restored.replace(before, after, 1)
    if sha(restored) != row["after_sha256"] or len(restored) != row["after_bytes"]:
        raise ValueError("The composed680 view did not restore its complete sealed layer source")
    forward = restored
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(after) != 1:
            raise ValueError("Exact unique composed680 source-view reverse fragments are required")
        forward = forward.replace(after, before, 1)
    if forward != payload:
        raise ValueError("Complete composed680 inverse/forward source-view custody differs")
    return restored


def source_before_callback_composition680(relative, payload):
    """Qualified680 callback inverse to IO, or its exact declared IO ancestor only."""
    return _complete_composition_view(relative, payload, "callback_above_io")


def callback_isolated_after_qualified_tooling671(relative, payload):
    """Qualified680 to the exact sealed isolated callback afterimage; no restored code."""
    return _complete_composition_view(relative, payload, "callback_isolated")


def peel_callback_composition680_for_history(relative, payload):
    """Only the complete exact680 endpoint peels; all other images face older pins."""
    _identity(relative, payload)
    row = _composition_document()["callback_above_io"].get(relative)
    if row is not None and sha(payload) == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return source_before_callback_composition680(relative, payload)
    return payload  # No raw-current certificate or generic layer search.


def peel_callback_isolated680_for_history(relative, payload):
    """Only complete exact680 sources yield their sealed isolated callback view."""
    _identity(relative, payload)
    row = _composition_document()["callback_isolated"].get(relative)
    if row is not None and sha(payload) == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return callback_isolated_after_qualified_tooling671(relative, payload)
    return payload  # Every other image still faces the unchanged callback/historical pins.


def _validate_own_guard(root, document):
    from ios_popover_anchor_plan import _ordinary_bytes
    current_raw = _ordinary_bytes(root, SOURCE_RELATIVE)[0]
    import ci668_outer_source_projection as ci668
    raw = ci668.current_source_before_ci668(SOURCE_RELATIVE, current_raw)
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + "0" * 64 + '"\n').encode()
    if (len(raw) != document["own_guard"]["bytes"] or raw.count(needle) != 1 or
            sha(raw.replace(needle, template, 1)) != document["own_guard"]["template_sha256"]):
        raise ValueError("Current tooling671 own guard differs from its exact singleton template")
    return sha(current_raw)


def current_input_hashes():
    """Expected exact current finite custody, including the qualified own executable."""
    import ci668_outer_source_projection as ci668
    validate_current_sources(ROOT)
    document = _document()
    return ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["added_inputs"] | document["unchanged_inputs"] |
            {SPEC_RELATIVE: SPEC_SHA256, SOURCE_RELATIVE: _validate_own_guard(ROOT, document)} |
            ci668.current_input_hashes())


def _validate_current_sources_operation(root: Path, document, operation):
    """Source/model custody only; no native/controller/host or original method replay."""
    import ci668_outer_source_projection as ci668
    operation._validate_ci(root)
    _validate_own_guard(root, document)
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in expected.items():
        if sha(operation._ci_history(name, _ordinary_bytes(root, name)[0])) != digest:
            raise ValueError("Current tooling671 input differs from its complete reviewed raw image: " + name)
    # The existing operation already holds every source and all composition origins.
    # Schema/origin qualification remains fresh once in that exact custody scope;
    # only private inverse arithmetic reuses the already qualified owning documents.
    composition = _composition_document()
    for view in ("callback_above_io", "callback_isolated"):
        for relative, row in composition[view].items():
            raw = operation._ci_history(relative, _ordinary_bytes(root, relative)[0])
            raw = _source_before_tooling671_document(relative, raw, document)
            _complete_composition_view_row680(raw, row)
    return True



def validate_current_sources(root: Path):
    """One fresh tooling/CI owning operation; ZERO native or accepted-test replay."""
    import macos_share_ci668_composition as joint
    with joint._source_projection_operation(root) as operation:
        return operation._validate_tooling(root)

def fixture_inputs():
    """Exactly the finite new/current custody union, never a test/native selection."""
    import ci668_outer_source_projection as ci668
    return BOUND_PATHS | ADDED_PATHS | UNCHANGED_PATHS | {SOURCE_RELATIVE, SPEC_RELATIVE} | ci668.fixture_inputs()
