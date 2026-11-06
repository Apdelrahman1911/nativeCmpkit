# SPDX-License-Identifier: Apache-2.0
"""Exact one-path Camera C1 lifecycle DATA inverse, never execution/admission.

The complete frozen C9 host fixture and the complete NEW2 afterimage are bound.
Only actual host Activity/Compose/save-state/callback regressions change: all
five old host bodies and every production/native C1 acceptance source stay
sealed. This module performs no filesystem, registry, controller, manifest,
model, source-plan, compiler, native-selector, Git, query or process operation.

The host fixture is not raw301/current303. Unlisted paths are DATA no-ops,
never enrollment or certification. Strict-current bound DATA refuses old,
partial and unknown images; after-only history still needs its owning old pins.
This inverse alone does not qualify any complete producer/native ingress and
cannot explain or repair original630 live349/cleanup1405.
"""
from __future__ import annotations

import hashlib
from types import MappingProxyType

MAX_SOURCE_BYTES = 65536
MAX_PATH_CHARS = 512
HOST = 'calf-camera-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraLifecycleTest.kt'
BOUND_PATHS = frozenset((HOST,))
# (before size/hash, after size/hash, immutable exact inverse fragments).
_BINDINGS = MappingProxyType({'calf-camera-picker/src/androidHostTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraLifecycleTest.kt': (12987, '726deb93c02a5d5ec06d87efc71e1393c7389afe2d613684053bf5032441dc09', 21978, 'ad0ad04ae9635295d9e73676e00060b78f9d3975c8d3c04939112afbf47cfb61', ((b'    val results = mutableListOf<CameraPickerResult>()\n', b'    val results = mutableListOf<CameraPickerResult>()\n    var resultCallback by mutableStateOf<(CameraPickerResult) -> Unit>({ results += it })\n    var appliedCallback: ((CameraPickerResult) -> Unit)? = null\n', '5bc3c80b9cf21c74273e7b7693a848c7c0aa210621649d176fb714b03db76433', '4aedbb40e67a18f675af6599774686287ad5a2dd97a7d6ff21354fcd9a0df987'), (b'                    val current = rememberCameraPickerResultLauncher { results += it }\n                    SideEffect { launcher = current }\n', b'                    val callback = resultCallback\n                    val current = rememberCameraPickerResultLauncher(onResult = callback)\n                    SideEffect { launcher = current; appliedCallback = callback }\n', '4915f92649f2ab4236fb12602a978bfbbc7bc08abd955e11c758f747f4de445f', '36785e3bdc41f9eac1d840a6b5a0e2ee6978289a6dc8193644fc7398e96c1c46'), (b'    private fun createActivity(saved: Bundle? = null): ActivityController<CameraLifecycleTestActivity> {\n', b'    // NEW2: genuine host Activity/Compose/registry regressions, not device C1 acceptance.\n    @Test fun nonFinishingRestorationThenCallbackSwapDeliversOneReadableResultToCurrentOwner() {\n        val callbackAResults = mutableListOf<CameraPickerResult>()\n        val callbackBResults = mutableListOf<CameraPickerResult>()\n        val callbackA: (CameraPickerResult) -> Unit = { callbackAResults += it }\n        val callbackB: (CameraPickerResult) -> Unit = { callbackBResults += it }\n        val originalController = createActivity()\n        val original = originalController.get()\n        val originalOwner = assertNotNull(original.launcher)\n        compose.runOnIdle { original.resultCallback = callbackA }\n        awaitCallback(original, callbackA)\n        assertSame(originalOwner, original.launcher)\n        val launched = launch(original)\n        val uri = launchUri(launched)\n        val output = output(launched)\n        val expected = byteArrayOf(12, 34, 56, 78)\n        val saved = Bundle()\n        original.contentResolver.openOutputStream(uri)!!.use { externalWriter ->\n            compose.runOnUiThread {\n                originalController.pause().saveInstanceState(saved).stop().destroy()\n            }\n            compose.waitForIdle()\n            assertTrue(original.isDestroyed)\n            assertFalse(original.isFinishing)\n            assertFalse(original.isChangingConfigurations, "This must be non-finishing, not config-only recreation")\n            val disposal = original.disposals.single()\n            assertEquals(Lifecycle.State.DESTROYED, disposal.lifecycleState)\n            assertFalse(disposal.finishing)\n            assertFalse(disposal.changingConfigurations)\n            assertTrue(disposal.retainForRestoration)\n            assertTrue(output.isFile, "The external writer still owns an open output after destruction")\n            externalWriter.write(expected)\n        }\n\n        val restored = createActivity(saved).get()\n        assertNotSame(original, restored)\n        val restoredOwner = assertNotNull(restored.launcher)\n        assertNotSame(originalOwner, restoredOwner)\n        compose.runOnIdle { restored.resultCallback = callbackA }\n        awaitCallback(restored, callbackA)\n        compose.runOnIdle { restored.resultCallback = callbackB }\n        awaitCallback(restored, callbackB)\n        assertSame(restoredOwner, restored.launcher, "A callback update must not replace the saved request owner")\n        assertTrue(output.isFile)\n        assertTrue(callbackAResults.isEmpty())\n        assertTrue(callbackBResults.isEmpty())\n        compose.runOnIdle { originalOwner.launch() }\n        assertNull(shadowOf(original).nextStartedActivityForResult, "A disposed owner cannot launch another camera")\n        assertNull(shadowOf(restored).nextStartedActivityForResult, "Restoration/callback swap must not relaunch")\n\n        // The synthetic writer is closed before actual registry success delivery.\n        deliver(restored, launched, Activity.RESULT_OK)\n        val captured = assertIs<CameraPickerResult.Captured>(callbackBResults.single())\n        assertEquals(uri, captured.file.uri)\n        assertContentEquals(expected, output.readBytes())\n        restored.contentResolver.openInputStream(captured.file.uri)!!.use {\n            assertContentEquals(expected, it.readBytes())\n        }\n        deliver(restored, launched, Activity.RESULT_OK) // Duplicate host registry delivery; no device/native claim.\n        assertEquals(1, callbackBResults.size, "Exactly one terminal result goes to the current callback")\n        assertTrue(callbackAResults.isEmpty(), "Neither the destroyed nor replaced callback receives a result")\n        assertTrue(original.results.isEmpty(), "The old fixture\'s default callback remains silent")\n        assertTrue(restored.results.isEmpty(), "The restored fixture\'s replaced default callback remains silent")\n        assertNull(shadowOf(restored).nextStartedActivityForResult)\n    }\n\n    @Test fun nonFinishingRestorationThenCallbackSwapCancelsOnlyOwnedOutputAndSuppressesOldCallbacks() {\n        val callbackAResults = mutableListOf<CameraPickerResult>()\n        val callbackBResults = mutableListOf<CameraPickerResult>()\n        val callbackA: (CameraPickerResult) -> Unit = { callbackAResults += it }\n        val callbackB: (CameraPickerResult) -> Unit = { callbackBResults += it }\n        val originalController = createActivity()\n        val original = originalController.get()\n        val originalOwner = assertNotNull(original.launcher)\n        compose.runOnIdle { original.resultCallback = callbackA }\n        awaitCallback(original, callbackA)\n        assertSame(originalOwner, original.launcher)\n        val launched = launch(original)\n        val uri = launchUri(launched)\n        val output = output(launched)\n        val unrelatedBytes = byteArrayOf(9, 7, 5, 3)\n        val unrelated = File.createTempFile("capture-unrelated-", ".jpg", assertNotNull(output.parentFile)).also {\n            outputs += it // Register exact teardown ownership before the first write/assertion can fail.\n            it.writeBytes(unrelatedBytes)\n        }\n        assertNotEquals(output.canonicalFile, unrelated.canonicalFile)\n        val saved = Bundle()\n        original.contentResolver.openOutputStream(uri)!!.use { externalWriter ->\n            compose.runOnUiThread {\n                originalController.pause().saveInstanceState(saved).stop().destroy()\n            }\n            compose.waitForIdle()\n            assertTrue(original.isDestroyed)\n            assertFalse(original.isFinishing)\n            assertFalse(original.isChangingConfigurations, "This must be non-finishing, not config-only recreation")\n            val disposal = original.disposals.single()\n            assertEquals(Lifecycle.State.DESTROYED, disposal.lifecycleState)\n            assertFalse(disposal.finishing)\n            assertFalse(disposal.changingConfigurations)\n            assertTrue(disposal.retainForRestoration)\n            assertTrue(output.isFile, "Unregister cannot unlink an output with an external writer")\n            externalWriter.write(byteArrayOf(1, 2, 3, 4))\n        }\n\n        val restored = createActivity(saved).get()\n        assertNotSame(original, restored)\n        val restoredOwner = assertNotNull(restored.launcher)\n        assertNotSame(originalOwner, restoredOwner)\n        compose.runOnIdle { restored.resultCallback = callbackA }\n        awaitCallback(restored, callbackA)\n        compose.runOnIdle { restored.resultCallback = callbackB }\n        awaitCallback(restored, callbackB)\n        assertSame(restoredOwner, restored.launcher, "A callback update must not replace the saved request owner")\n        assertTrue(output.isFile, "The restored pending output remains until terminal cancellation")\n        assertTrue(callbackAResults.isEmpty())\n        assertTrue(callbackBResults.isEmpty())\n        compose.runOnIdle { originalOwner.launch() }\n        assertNull(shadowOf(original).nextStartedActivityForResult, "A disposed owner cannot launch another camera")\n        assertNull(shadowOf(restored).nextStartedActivityForResult, "Restoration/callback swap must not relaunch")\n\n        // The synthetic writer is closed before actual registry cancellation delivery.\n        deliver(restored, launched, Activity.RESULT_CANCELED)\n        assertEquals(CameraPickerResult.Cancelled, callbackBResults.single())\n        assertFalse(output.exists(), "A terminal cancellation deletes only the saved pending output")\n        assertContentEquals(unrelatedBytes, unrelated.readBytes(), "An unrelated owned-pattern sibling must survive")\n        deliver(restored, launched, Activity.RESULT_CANCELED) // Duplicate host registry delivery; no device/native claim.\n        assertEquals(1, callbackBResults.size, "A duplicate result cannot call the current callback twice")\n        assertTrue(callbackAResults.isEmpty(), "Neither the destroyed nor replaced callback receives cancellation")\n        assertTrue(original.results.isEmpty(), "The old fixture\'s default callback remains silent")\n        assertTrue(restored.results.isEmpty(), "The restored fixture\'s replaced default callback remains silent")\n        assertFalse(output.exists())\n        assertContentEquals(unrelatedBytes, unrelated.readBytes())\n        assertNull(shadowOf(restored).nextStartedActivityForResult)\n    }\n\n    private fun createActivity(saved: Bundle? = null): ActivityController<CameraLifecycleTestActivity> {\n', '8b7712c62c3522bd58ef1db3602da4c7a55fbc9de13a07e8683ce7368ed5072f', 'b477a1ee6f15cc0006f4481dcb8beff2b212bfb1c266b50fe8a188b299e1dbd9'), (b'    private fun launch(activity: CameraLifecycleTestActivity): ShadowActivity.IntentForResult {\n', b"    private fun awaitCallback(activity: CameraLifecycleTestActivity, callback: (CameraPickerResult) -> Unit) {\n        // As for composition readiness, drain Robolectric's paused looper after the state write.\n        compose.waitForIdle()\n        compose.waitUntil(timeoutMillis = 5_000) {\n            compose.runOnUiThread { activity.appliedCallback === callback }\n        }\n        compose.waitForIdle()\n    }\n\n    private fun launch(activity: CameraLifecycleTestActivity): ShadowActivity.IntentForResult {\n", '18796cf3775bc2bb0d6274bea8aa119dbe69ba85ac93781a69c67297a565d4ee', 'fa91d099ae417849ee34b80598ffe4d94e4f9e09f5c2ff108011db494fd68589')))})
_PATH_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./-")



def _identity(relative, payload):
    if (type(relative) is not str or not 0 < len(relative) <= MAX_PATH_CHARS or
            relative.startswith("/") or any(char not in _PATH_CHARS for char in relative) or
            any(part in ("", ".", "..") for part in relative.split("/")) or
            type(payload) is not bytes or not 0 < len(payload) <= MAX_SOURCE_BYTES):
        raise ValueError("Bounded ordinary Camera lifecycle relative source DATA bytes are required")


def _digest(payload):
    return hashlib.sha256(payload).hexdigest()


def _inverse_after(payload, binding):
    before_size, before_digest, after_size, after_digest, fragments = binding
    if len(payload) != after_size or _digest(payload) != after_digest:
        raise ValueError("Only the complete exact NEW2 host afterimage may be reversed")
    restored = payload
    for old, new, old_digest, new_digest in reversed(fragments):
        if _digest(old) != old_digest or _digest(new) != new_digest or restored.count(new) != 1:
            raise ValueError("Exact unique sealed host DATA inverse fragments are required")
        restored = restored.replace(new, old, 1)
    if len(restored) != before_size or _digest(restored) != before_digest:
        raise ValueError("Host DATA inverse did not restore the complete exact C9 beforeimage")
    forward = restored
    for old, new, old_digest, new_digest in fragments:
        if _digest(old) != old_digest or _digest(new) != new_digest or forward.count(old) != 1:
            raise ValueError("Exact unique sealed host DATA forward fragments are required")
        forward = forward.replace(old, new, 1)
    if forward != payload:
        raise ValueError("The complete exact host DATA inverse/forward roundtrip differs")
    return restored


def source_before_c1_lifecycle(relative, payload):
    """One exact C9 beforeimage or exact NEW2 inverse; no source admission."""
    _identity(relative, payload)
    binding = _BINDINGS.get(relative)
    if binding is None:
        return payload  # Unlisted DATA earns no certification or membership.
    if len(payload) == binding[0] and _digest(payload) == binding[1]:
        return payload
    return _inverse_after(payload, binding)


def current_source_before_c1_lifecycle(relative, payload):
    """Strict latest bound DATA only; old/partial/unknown cannot be current."""
    _identity(relative, payload)
    binding = _BINDINGS.get(relative)
    if binding is None:
        return payload  # No raw301/current303 enrollment or native claim.
    return _inverse_after(payload, binding)


def peel_c1_lifecycle_for_history(relative, payload):
    """Peel exact NEW2 after only; other DATA still needs its owning old pins."""
    _identity(relative, payload)
    binding = _BINDINGS.get(relative)
    if binding is not None and len(payload) == binding[2] and _digest(payload) == binding[3]:
        return _inverse_after(payload, binding)
    return payload  # Honest historical/unlisted no-op, not a certificate.
