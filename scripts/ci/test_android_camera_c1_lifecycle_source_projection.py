# SPDX-License-Identifier: Apache-2.0
"""NEW3 finite Camera C1 lifecycle source controls; not host/native results.

Future lead-authorized source execution reads only the named complete proposal
host afterimage, pure inverse, unchanged C9 production/device/fixture inputs and
unchanged current303 manifest. No model scan, ROOT mutation, compiler, Activity,
registry dispatch, external camera or native selector is run by these controls.
The separate NEW2 genuine Robolectric methods remain independently required.

NATIVECMPKIT_C1_LIFECYCLE_SOURCE_TREE may identify a lead-owned finite retained
source tree. It is not assembled, copied or certified here. This source packet
has never imported this module or its target inverse and has executed zero
controls. Original630 live349/cleanup1405 cause and device C1 remain unresolved.
"""
from __future__ import annotations

import hashlib
import os
import re
import unittest
from pathlib import Path
from types import MappingProxyType

import android_camera_c1_lifecycle_source_projection as lifecycle

SOURCE_ROOT = Path(os.environ.get("NATIVECMPKIT_C1_LIFECYCLE_SOURCE_TREE", str(Path(__file__).resolve().parents[2])))
HOST = 'calf-camera-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraLifecycleTest.kt'
PROJECTION = 'scripts/ci/android_camera_c1_lifecycle_source_projection.py'
CONTROL = 'scripts/ci/test_android_camera_c1_lifecycle_source_projection.py'
MANIFEST = 'scripts/ci/fixtures/macos-share-ci668-composition.json'
PRODUCTION = 'calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt'
NATIVE = 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt'
BEFORE = (12987, '726deb93c02a5d5ec06d87efc71e1393c7389afe2d613684053bf5032441dc09')
AFTER = (21978, 'ad0ad04ae9635295d9e73676e00060b78f9d3975c8d3c04939112afbf47cfb61')
PROJECTION_IDENTITY = (15160, 'be6c22095f0ddbf420af6ee80c4c36385e73e66ec8e2873c07af36bc7db4de8e')
MANIFEST_IDENTITY = (518906, '06d04d038b06c00e5aafb9b7defdf39ae069f3df305e4dbc84198bc8ed178a24')
EXISTING5 = ('nonFinishingDestructionRetainsAnActiveOutputAndSavedRequestForRestoration', 'realActivityRecreationRetainsPendingOutputAndCancellationCleansIt', 'liveCompositionRemovalAbandonsCallbacksWithoutUnlinkingTheExternalOutput', 'finishingActivityAbandonsResultButDoesNotDeleteAnInFlightOutput', 'liveContextWrapperReplacementTransfersPendingOwnershipWithoutClearingIt')
NEW2 = ('nonFinishingRestorationThenCallbackSwapDeliversOneReadableResultToCurrentOwner', 'nonFinishingRestorationThenCallbackSwapCancelsOnlyOwnedOutputAndSuppressesOldCallbacks')
NATIVE4 = ('nativeDontKeepActivitiesRestoresOneReadableCapturedFile', 'nativeRotationRecreatesCallerWhileExternalCaptureIsForeground', 'nativeKernelProcessDeathRestoresPendingUriAndExactlyOneSuccess', 'nativeCancelledProcessRestorationRemovesOnlyItsFileAndNeverDeliversStaleUri')
EXISTING_BODY_IDENTITIES = MappingProxyType({'nonFinishingDestructionRetainsAnActiveOutputAndSavedRequestForRestoration': (1843, '78c4b1c655889d3319622a2ef10dd1776018e7bd320520ee26596f8242d7fd90'), 'realActivityRecreationRetainsPendingOutputAndCancellationCleansIt': (935, '0aee2ef2749686c82ca79f908f0130d0cf6d5555db35db53d02cf00ccc241cd8'), 'liveCompositionRemovalAbandonsCallbacksWithoutUnlinkingTheExternalOutput': (1566, 'e713c4f2a4bd40c689aa5a5c2db655479c58453f62900d5f2c43d779957add52'), 'finishingActivityAbandonsResultButDoesNotDeleteAnInFlightOutput': (917, '3c9e2810cfddc336ce03f1077fbd23b031ef683a822aed7e5bb2215c6e13652f'), 'liveContextWrapperReplacementTransfersPendingOwnershipWithoutClearingIt': (1217, '5b510240e970e342b3b2be7456cd772a1c8e550f945942e593c91e3a08a910e2')})
UNCHANGED = MappingProxyType({'calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt': (8245, 'b7094d795bfaa209b254bbf2c549de21a7fff07df636fbb68f4cb1a3baa917a7'), 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt': (29022, '357c8545e35d5fa529a6b38b064a86c1724ea2b0a2d2b7ec46d5ff4c3671a7d0'), 'calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerResult.kt': (3004, 'b7d906813c66604e76a4f64f55306dbea6e92889bf3e77a66cd3aaa13a9891ab'), 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRestorationVerificationActivity.kt': (10832, '8aeb2acf56287c08619c854f4da21c3f0c4f95d7dba19e17ca6ceacff03a0c12'), 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt': (7306, '2010803e066ce0de1a34051ed40a50c9bca08f238a6218dcaabb4e7d0a09bee7'), 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt': (25532, '01771567b969a88094d88a2906dadc6bc4d1e8502e695abc9f145b7ca197e06e'), 'calf-camera-picker/build.gradle.kts': (4391, 'e37eb7a4fab11a6af0ed0ff6af7dea57e081241d41efb9fa7f1dd06f7367192f'), 'calf-camera-picker/src/androidHostTest/AndroidManifest.xml': (267, 'f9c3c1a1b0e59d018fb576defd49771ad8d6faf5129ef8b95bdd8463a93633b5'), 'calf-camera-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraHostFileProvider.kt': (1358, '3802d3cb28b9b8c40c937178de67db0b5614b2f52a2b9de2af055d6570a9d6b6'), 'calf-camera-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRequestTest.kt': (7556, '39ae5998755f2affcfb31b51ff2e24ebc00dc2be87188e1522c632f34404d4bb')})
FIXED_INPUTS = frozenset((HOST, PROJECTION, MANIFEST, *UNCHANGED))


def _digest(payload):
    return hashlib.sha256(payload).hexdigest()


def _read(relative, maximum=65536):
    if type(relative) is not str or relative not in FIXED_INPUTS:
        raise ValueError("Only finite explicitly named Camera source inputs may be read")
    with (SOURCE_ROOT / relative).open("rb") as stream:
        payload = stream.read(maximum + 1)
    if not 0 < len(payload) <= maximum:
        raise ValueError("Named Camera source exceeds its bounded read cap")
    return payload


def _body(payload, name):
    # Brace-slice arithmetic on complete hash-bound fixed source, not Kotlin compilation.
    declaration = ("    @Test fun " + name + "() {").encode()
    if payload.count(declaration) != 1:
        raise ValueError("One exact named fixed host method is required")
    begin = payload.index(declaration)
    depth = 0
    for offset in range(begin + len(declaration) - 1, len(payload)):
        if payload[offset] == ord("{"):
            depth += 1
        elif payload[offset] == ord("}"):
            depth -= 1
            if depth == 0:
                if payload[offset:offset + 2] != b"}\n":
                    raise ValueError("Exact fixed host method closing newline is required")
                return payload[begin:offset + 2]
    raise ValueError("Complete fixed host method body is required")


class AndroidCameraC1LifecycleSourceControls(unittest.TestCase):
    def test_new01_exact_host_inverse_preserves_five_bodies_and_genuine_callback_recreation_structure(self):
        payload = _read(HOST)
        self.assertEqual(AFTER, (len(payload), _digest(payload)))
        projection_source = _read(PROJECTION)
        self.assertEqual(PROJECTION_IDENTITY, (len(projection_source), _digest(projection_source)))
        self.assertEqual((65536, 512), (lifecycle.MAX_SOURCE_BYTES, lifecycle.MAX_PATH_CHARS))
        self.assertEqual(frozenset((HOST,)), lifecycle.BOUND_PATHS)
        self.assertIsInstance(lifecycle._BINDINGS, MappingProxyType)
        self.assertEqual((HOST,), tuple(lifecycle._BINDINGS))
        binding = lifecycle._BINDINGS[HOST]
        self.assertIs(type(binding), tuple)
        self.assertEqual((*BEFORE, *AFTER), binding[:4])
        self.assertIs(type(binding[4]), tuple)
        self.assertEqual(4, len(binding[4]))
        before = lifecycle.current_source_before_c1_lifecycle(HOST, payload)
        self.assertEqual(BEFORE, (len(before), _digest(before)))
        self.assertEqual(before, lifecycle.source_before_c1_lifecycle(HOST, payload))
        self.assertIs(before, lifecycle.source_before_c1_lifecycle(HOST, before))
        self.assertEqual(before, lifecycle.peel_c1_lifecycle_for_history(HOST, payload))
        forward = before
        for old, new, old_digest, new_digest in binding[4]:
            self.assertEqual((old_digest, new_digest), (_digest(old), _digest(new)))
            self.assertEqual(1, forward.count(old))
            forward = forward.replace(old, new, 1)
        self.assertEqual(payload, forward)
        declared = tuple(name.decode() for name in re.findall(rb"(?m)^    @Test fun ([A-Za-z0-9_]+)\(", payload))
        self.assertEqual(EXISTING5 + NEW2, declared)
        for name in EXISTING5:
            with self.subTest(preserved=name):
                old_body, current_body = _body(before, name), _body(payload, name)
                self.assertEqual(old_body, current_body)
                self.assertEqual(EXISTING_BODY_IDENTITIES[name], (len(current_body), _digest(current_body)))
        for anchor in (
            b"class CameraLifecycleTestActivity : ComponentActivity()",
            b"setContent {",
            b"var resultCallback by mutableStateOf<(CameraPickerResult) -> Unit>",
            b"val callback = resultCallback",
            b"rememberCameraPickerResultLauncher(onResult = callback)",
            b"SideEffect { launcher = current; appliedCallback = callback }",
            b"activity.activityResultRegistry.dispatchResult(launched.requestCode, result, Intent())",
            b"if (saved == null) controller.setup() else controller.setup(saved)",
            b"compose.waitUntil(timeoutMillis = 5_000)",
            b"activity.appliedCallback === callback",
        ):
            self.assertIn(anchor, payload)
        for name in NEW2:
            method = _body(payload, name)
            with self.subTest(regression=name):
                for anchor in (
                    b"val saved = Bundle()",
                    b"original.contentResolver.openOutputStream(uri)!!.use { externalWriter ->",
                    b"originalController.pause().saveInstanceState(saved).stop().destroy()",
                    b"assertFalse(original.isFinishing)",
                    b"assertFalse(original.isChangingConfigurations,",
                    b"assertEquals(Lifecycle.State.DESTROYED, disposal.lifecycleState)",
                    b"assertTrue(disposal.retainForRestoration)",
                    b"val restored = createActivity(saved).get()",
                    b"compose.runOnIdle { restored.resultCallback = callbackA }",
                    b"awaitCallback(restored, callbackA)",
                    b"compose.runOnIdle { restored.resultCallback = callbackB }",
                    b"awaitCallback(restored, callbackB)",
                    b"assertSame(restoredOwner, restored.launcher,",
                    b"compose.runOnIdle { originalOwner.launch() }",
                    b"assertNull(shadowOf(original).nextStartedActivityForResult,",
                    b"assertNull(shadowOf(restored).nextStartedActivityForResult,",
                    b"assertEquals(1, callbackBResults.size,",
                    b"assertTrue(callbackAResults.isEmpty(),",
                    b"assertTrue(original.results.isEmpty(),",
                    b"assertTrue(restored.results.isEmpty(),",
                ):
                    self.assertIn(anchor, method)
                self.assertLess(method.index(b".saveInstanceState(saved).stop().destroy()"), method.index(b"createActivity(saved)"))
                self.assertLess(method.index(b"restored.resultCallback = callbackA"), method.index(b"restored.resultCallback = callbackB"))
                self.assertLess(method.index(b"awaitCallback(restored, callbackB)"), method.index(b"deliver(restored, launched,"))
                self.assertNotIn(b"CameraPickerLauncherAndroidImpl(", method)
                self.assertNotIn(b"CameraRequestState(", method)
        success, cancellation = (_body(payload, name) for name in NEW2)
        self.assertEqual(2, success.count(b"deliver(restored, launched, Activity.RESULT_OK)"))
        self.assertIn(b"assertIs<CameraPickerResult.Captured>(callbackBResults.single())", success)
        self.assertIn(b"assertEquals(uri, captured.file.uri)", success)
        self.assertIn(b"restored.contentResolver.openInputStream(captured.file.uri)!!.use", success)
        self.assertIn(b"assertContentEquals(expected, it.readBytes())", success)
        self.assertEqual(2, cancellation.count(b"deliver(restored, launched, Activity.RESULT_CANCELED)"))
        self.assertIn(b"File.createTempFile(\"capture-unrelated-\", \".jpg\", assertNotNull(output.parentFile))", cancellation)
        self.assertIn(b"outputs += it", cancellation)
        self.assertIn(b"assertEquals(CameraPickerResult.Cancelled, callbackBResults.single())", cancellation)
        self.assertIn(b"assertFalse(output.exists(),", cancellation)
        self.assertIn(b"assertContentEquals(unrelatedBytes, unrelated.readBytes(),", cancellation)

    def test_new02_strict_latest_refuses_old_partial_mutated_types_paths_and_overcap_without_enrollment(self):
        payload = _read(HOST)
        self.assertEqual(AFTER, (len(payload), _digest(payload)))
        before = lifecycle.current_source_before_c1_lifecycle(HOST, payload)
        binding = lifecycle._BINDINGS[HOST]
        partial = before.replace(binding[4][0][0], binding[4][0][1], 1)
        self.assertNotEqual(before, partial)
        self.assertNotEqual(payload, partial)
        foreign = bytes((payload[0] ^ 1,)) + payload[1:]
        bad_images = (partial, foreign, payload[:-1], payload + b"\n")
        with self.assertRaises(ValueError):
            lifecycle.current_source_before_c1_lifecycle(HOST, before)
        for image in bad_images:
            with self.subTest(image_hash=_digest(image)):
                with self.assertRaises(ValueError):
                    lifecycle.current_source_before_c1_lifecycle(HOST, image)
                with self.assertRaises(ValueError):
                    lifecycle.source_before_c1_lifecycle(HOST, image)
                self.assertIs(image, lifecycle.peel_c1_lifecycle_for_history(HOST, image))
        self.assertIs(before, lifecycle.peel_c1_lifecycle_for_history(HOST, before))
        unlisted = "scripts/ci/unlisted_c1_lifecycle_data.py"
        unknown = b"Unlisted bounded DATA; not source/native acceptance\n"
        self.assertNotIn(unlisted, lifecycle.BOUND_PATHS)
        transforms = (lifecycle.source_before_c1_lifecycle,
                      lifecycle.current_source_before_c1_lifecycle,
                      lifecycle.peel_c1_lifecycle_for_history)
        for transform in transforms:
            self.assertIs(unknown, transform(unlisted, unknown))

        class BytesSubclass(bytes):
            pass

        class StringSubclass(str):
            pass

        bad_paths = (None, False, 1, HOST.encode(), StringSubclass(HOST), "", "/absolute", "../outside",
                     "a//b", "./a", "a/./b", "a/../b", "a/", "a\\b", "a\x00b", "a?b", "a" * 513)
        bad_payloads = (None, False, 1, payload.decode(), bytearray(payload), memoryview(payload),
                        BytesSubclass(payload), b"", b"x" * (lifecycle.MAX_SOURCE_BYTES + 1))
        for transform in transforms:
            for relative in bad_paths:
                with self.subTest(transform=transform.__name__, path=repr(relative)):
                    with self.assertRaises(ValueError):
                        transform(relative, payload)
            for image in bad_payloads:
                with self.subTest(transform=transform.__name__, payload_type=type(image).__name__):
                    with self.assertRaises(ValueError):
                        transform(HOST, image)
        with self.assertRaises(TypeError):
            lifecycle._BINDINGS[unlisted] = binding
        self.assertEqual((HOST,), tuple(lifecycle._BINDINGS))

    def test_new03_native_production_and_current303_authority_remain_separate_and_unchanged(self):
        contents = {}
        for relative, identity in UNCHANGED.items():
            with self.subTest(unchanged=relative):
                data = _read(relative)
                self.assertEqual(identity, (len(data), _digest(data)))
                contents[relative] = data
        native = contents[NATIVE]
        self.assertEqual(NATIVE4, tuple(item.decode() for item in re.findall(rb"(?m)^    @Test fun ([A-Za-z0-9_]+)\(", native)))
        for anchor in (
            b"nativeDontKeepActivitiesRestoresOneReadableCapturedFile() = capture(dontKeep = true)",
            b"assertEquals(35, Build.VERSION.SDK_INT)",
            b"OwnedAlwaysFinish(pm, instrumentation.uiAutomation, originalFinish)",
            b"external camera, URI grant or registry state/result is injected.",
            b"assertEquals(1, terminal.integer(\"launches\")); assertEquals(1, terminal.integer(\"results\"))",
            b"assertTrue(terminal.integer(\"creates\") >= 2,",
            b"assertContentEquals(expectedBytes, context.contentResolver.openInputStream(uri)!!.use { it.readBytes() })",
            b"assertEquals(before, outputs())",
            b"assertEquals(\"untouched cache sibling\", siblingFile.readText())",
            b"alwaysFinish?.let { owner -> cleanup { owner.restore() } }",
        ):
            self.assertIn(anchor, native)
        production = contents[PRODUCTION]
        for anchor in (
            b"val currentResult by rememberUpdatedState(onResult)",
            b"rememberSaveable(saver = CameraRequestState.Saver)",
            b"owner.value?.handleResult(success)",
            b"if (activity.isFinishing) return false",
            b"lifecycle?.currentState == Lifecycle.State.DESTROYED",
        ):
            self.assertIn(anchor, production)
        for dependency in (b"implementation(libs.robolectric)", b"implementation(libs.androidx.compose.ui.test.junit4)"):
            self.assertIn(dependency, contents["calf-camera-picker/build.gradle.kts"])
        self.assertIn(b"CameraLifecycleTestActivity", contents["calf-camera-picker/src/androidHostTest/AndroidManifest.xml"])
        manifest_data = _read(MANIFEST, 524288)
        self.assertEqual(MANIFEST_IDENTITY, (len(manifest_data), _digest(manifest_data)))
        self.assertEqual(5382, 524288 - len(manifest_data))
        # Local JSON decode only. These controls do not call a source-domain/native plan.
        import json
        manifest = json.loads(manifest_data)
        self.assertEqual(301, len(manifest["raw_inputs"]))
        self.assertIn("joint303", manifest["scope"])
        self.assertEqual({"final_ci175": 175, "producer676_raw190": 190, "cookie609_raw40": 40, "share607": 36},
                         {name: len(values) for name, values in manifest["predecessor_inputs"].items()})
        self.assertNotIn(HOST, manifest["raw_inputs"])
        self.assertNotIn(PROJECTION, manifest["raw_inputs"])
        self.assertNotIn(CONTROL, manifest["raw_inputs"])
        self.assertIn(PRODUCTION, manifest["raw_inputs"])
        self.assertIn(NATIVE, manifest["raw_inputs"])
        self.assertEqual(frozenset((HOST,)), lifecycle.BOUND_PATHS)
        self.assertEqual(13, len(FIXED_INPUTS))
