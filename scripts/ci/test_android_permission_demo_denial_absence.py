# SPDX-License-Identifier: Apache-2.0
"""Exact owning source/refusal guards only; never Kotlin/native success or replay.

Historical guard images remain below the unique approved third-absence reversal.
No candidate import, process-backed model, window/cache/grant/native action is run.
"""
from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import re
import unittest

from native_matrix_declarative_aliases import literal_metadata, native_aliases

TREE = Path(os.environ.get("PERMISSION_DENIAL_ABSENCE_REVIEW_TREE", Path(__file__).resolve().parents[2])).resolve()
CORE = "calf-permissions/core"
KOTLIN = CORE + "/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/"
PROFILE = "android-permission-demo-denial-recovery"
FOCUS_NAME = "ANDROID_PERMISSION_DEMO_DENIAL_RECOVERY_FOCUS"
CLASS = "com.mohamedrejeb.calf.permissions.AndroidPermissionDemoDeviceTest"
DENIAL = "denialThenPermanentDenialKeepsActualRationaleAndOneResultPerRequest"
CALL = "callOnFreshApprovedVariantUsesPublicRequestAndActualSystemGrant"
PICKER = "pickersReadRealDocumentsAndImagesWithoutAllFilesOrSmsPermissions"
METHODS = (CALL, DENIAL, PICKER)
SDK = "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-35;google_apis;x86_64"

ABSENCE_SOURCE_CHANGES = {'PermissionDemoSystemUi.kt': {'before_sha256': '24db0092c0962c91cd84a14c707f3d992f855ee915293d40955c383c0e1f0af9', 'after_sha256': '1875435675cf2449e1cf9f4c8671fceb26e126940c3516203ced823852279982', 'before': '    fun permissionDialogVisible(): Boolean {\n        val root = assertNotNull(automation.rootInActiveWindow, "An unavailable native window is not no dialog")\n        try {\n            val packageName = assertNotNull(root.packageName).toString()\n            assertTrue(packageName == OwnedPermissionDemo.PACKAGE || packageName in PERMISSION,\n                "A foreign active window cannot prove the owned request showed no dialog")\n            assertTrue(root.refresh() && root.isVisibleToUser)\n            return packageName in PERMISSION\n        } finally { root.recycle() }\n    }\n\n', 'after': '    enum class PermissionDialogKind { UNKNOWN, PRESENT, OWNED_VISIBLE_HOST }\n    data class PermissionDialogObservation(\n        val kind: PermissionDialogKind,\n        // 1 null; 2 missing package; 4 owned host; 8 allowed OS; 16 foreign; 32 unrefreshed.\n        val windowKind: Int,\n        // -1 unobserved; 0 observed false; 1 observed true. Never a no-dialog Boolean.\n        val refreshed: Int,\n        val visible: Int,\n    )\n\n    fun permissionDialogObservation(deadline: Long): PermissionDialogObservation {\n        requireObservationDeadline(deadline)\n        // Reacquire the active root each time; do not enumerate windows or clear the OS cache.\n        val root = automation.rootInActiveWindow\n        try {\n            requireObservationDeadline(deadline)\n            if (root == null) return PermissionDialogObservation(PermissionDialogKind.UNKNOWN, 1, -1, -1)\n            val refreshed = root.refresh()\n            // A failed refresh leaves visibility unobserved, not a false absence result.\n            val visible = if (refreshed) root.isVisibleToUser else null\n            requireObservationDeadline(deadline, if (refreshed) 1 else 0, diagnosticBoolean(visible))\n            if (!refreshed) return PermissionDialogObservation(PermissionDialogKind.UNKNOWN, 32, 0, -1)\n            // Read identity only after the cache-bypassing refresh succeeded.\n            val packageName = root.packageName?.toString()\n            val windowKind = when {\n                packageName == null -> 2\n                packageName == OwnedPermissionDemo.PACKAGE -> 4\n                packageName in PERMISSION -> 8\n                else -> 16\n            }\n            val unknown = PermissionDialogObservation(PermissionDialogKind.UNKNOWN, windowKind, 1,\n                diagnosticBoolean(visible))\n            if (visible != true) return unknown\n            if (packageName in PERMISSION) {\n                val app = instrumentation.targetContext.packageManager.getApplicationInfo(checkNotNull(packageName), 0)\n                assertTrue(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0,\n                    "A non-system permission package cannot prove the current native window")\n                requireObservationDeadline(deadline, 1, 1)\n                return unknown.copy(kind = PermissionDialogKind.PRESENT)\n            }\n            requireObservationDeadline(deadline, 1, 1)\n            return if (packageName == OwnedPermissionDemo.PACKAGE)\n                unknown.copy(kind = PermissionDialogKind.OWNED_VISIBLE_HOST) else unknown\n        } finally { root?.recycle() }\n    }\n\n    private fun requireObservationDeadline(deadline: Long, refreshed: Int = -1, visible: Int = -1) {\n        check(SystemClock.elapsedRealtime() < deadline) {\n            "A late native window read cannot certify the original no-dialog deadline; " +\n                "refresh=$refreshed,visible=$visible"\n        }\n    }\n\n'}, 'OwnedPermissionDemo.kt': {'before_sha256': 'cb3a99d39de7b56ae5afe5d36b8652a1bf5423fc5b736edadc6cdbc47a773e2c', 'after_sha256': '6bb014ebf7de5d8aa3bca2667eeca165ef22351f9622dee301ff34f044d6f444', 'before': '    fun request(operation: String): Bundle {\n        assertNotEquals(Looper.getMainLooper(), Looper.myLooper())\n        assertNull(protocolError)\n        val remote = assertNotNull(endpoint)\n        val nonce = UUID.randomUUID().toString().replace("-", "")\n        val reply = Reply()\n        check(pending.put(nonce, reply) == null)\n        val message = Message.obtain().apply {\n            replyTo = responses\n            data = Bundle().apply { putString("nonce", nonce); putString("operation", operation) }\n        }\n        try {\n            remote.send(message)\n            assertTrue(reply.ready.await(20, TimeUnit.SECONDS), "Actual consumer response timed out")\n            assertNull(protocolError)\n            return assertNotNull(reply.data).also {\n                assertEquals(nonce, it.getString("nonce"))\n                assertEquals(owner.uid, it.getInt("uid"))\n                val pid = it.getInt("pid")\n                assertTrue(pid > 0 && pid != Process.myPid())\n                if (nativePid == null) nativePid = pid else assertEquals(nativePid, pid)\n                assertNull(it.getString("probeError"), "A native refusal is not a successful test result")\n                val actual = assertNotNull(it.getString("generation"))\n                assertTrue(actual.matches(Regex("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")))\n                if (generation == null) generation = actual else assertEquals(generation, actual)\n                assertIs<Boolean>(it.get("activityActive"))\n                assertEquals(Build.VERSION.SDK_INT, it.getInt("apiLevel"))\n                if (it.getBoolean("activityActive")) {\n                    assertNotNull(it.getString("activityGeneration"))\n                    for (key in listOf("mounted", "resumed", "focused")) assertIs<Boolean>(it.get(key))\n                    if (it.getBoolean("mounted")) {\n                        // A missing/wrong-typed native read is unknown, never\n                        // a false default accepted as denial or no rationale.\n                        for (permission in listOf("CALL_PHONE", "RECORD_AUDIO", "READ_MEDIA_IMAGES",\n                            "READ_MEDIA_VIDEO", "READ_MEDIA_VISUAL_USER_SELECTED")) {\n                            assertIs<Boolean>(it.get("android.permission.$permission"))\n                            assertIs<Boolean>(it.get("android.permission.$permission.rationale"))\n                        }\n                        for (name in listOf("Call", "RecordAudio", "ReadImage", "ReadVideo")) {\n                            val state = assertNotNull(it.getBundle(name))\n                            for (key in listOf("granted", "rationale")) assertIs<Boolean>(state.get(key))\n                            for (key in listOf("availability", "access", "requestability")) assertIs<String>(state.get(key))\n                            val count = assertIs<Int>(state.get("callbacks"))\n                            assertTrue(count >= 0)\n                            if (count > 0) assertIs<Boolean>(state.get("callbackResult"))\n                            else assertFalse(state.containsKey("callbackResult"))\n                        }\n                    }\n                }\n            }\n        } finally { pending.remove(nonce); message.recycle() }\n    }\n\n', 'after': '    fun request(operation: String): Bundle = request(operation, observationDeadline = null)\n\n    // Only the third-request observation opts into the caller\'s existing absolute deadline.\n    // Ordinary Call/picker/teardown operations retain their original 20-second wait.\n    fun observeBefore(deadline: Long): Bundle = request("observe", observationDeadline = deadline)\n\n    private fun request(operation: String, observationDeadline: Long?): Bundle {\n        assertNotEquals(Looper.getMainLooper(), Looper.myLooper())\n        assertNull(protocolError)\n        val remote = assertNotNull(endpoint)\n        if (observationDeadline != null) {\n            check(operation == "observe") { "The bounded absence read must not perform a native operation" }\n            check(SystemClock.elapsedRealtime() < observationDeadline) { "The original no-dialog deadline expired before native observation" }\n        }\n        val nonce = UUID.randomUUID().toString().replace("-", "")\n        val reply = Reply()\n        check(pending.put(nonce, reply) == null)\n        val message = Message.obtain().apply {\n            replyTo = responses\n            data = Bundle().apply { putString("nonce", nonce); putString("operation", operation) }\n        }\n        try {\n            if (observationDeadline != null) check(SystemClock.elapsedRealtime() < observationDeadline) {\n                "The original no-dialog deadline expired before native send"\n            }\n            remote.send(message)\n            val responseReady = if (observationDeadline == null) reply.ready.await(20, TimeUnit.SECONDS)\n            else {\n                val remaining = observationDeadline - SystemClock.elapsedRealtime()\n                check(remaining > 0) { "A late native send cannot certify the no-dialog observation" }\n                reply.ready.await(remaining, TimeUnit.MILLISECONDS)\n            }\n            assertTrue(responseReady, "Actual consumer response timed out")\n            if (observationDeadline != null) check(SystemClock.elapsedRealtime() < observationDeadline) {\n                "A late native response cannot certify the no-dialog observation"\n            }\n            assertNull(protocolError)\n            return assertNotNull(reply.data).also {\n                assertEquals(nonce, it.getString("nonce"))\n                assertEquals(owner.uid, it.getInt("uid"))\n                val pid = it.getInt("pid")\n                assertTrue(pid > 0 && pid != Process.myPid())\n                if (nativePid == null) nativePid = pid else assertEquals(nativePid, pid)\n                assertNull(it.getString("probeError"), "A native refusal is not a successful test result")\n                val actual = assertNotNull(it.getString("generation"))\n                assertTrue(actual.matches(Regex("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")))\n                if (generation == null) generation = actual else assertEquals(generation, actual)\n                assertIs<Boolean>(it.get("activityActive"))\n                assertEquals(Build.VERSION.SDK_INT, it.getInt("apiLevel"))\n                if (it.getBoolean("activityActive")) {\n                    assertNotNull(it.getString("activityGeneration"))\n                    for (key in listOf("mounted", "resumed", "focused")) assertIs<Boolean>(it.get(key))\n                    if (it.getBoolean("mounted")) {\n                        // A missing/wrong-typed native read is unknown, never\n                        // a false default accepted as denial or no rationale.\n                        for (permission in listOf("CALL_PHONE", "RECORD_AUDIO", "READ_MEDIA_IMAGES",\n                            "READ_MEDIA_VIDEO", "READ_MEDIA_VISUAL_USER_SELECTED")) {\n                            assertIs<Boolean>(it.get("android.permission.$permission"))\n                            assertIs<Boolean>(it.get("android.permission.$permission.rationale"))\n                        }\n                        for (name in listOf("Call", "RecordAudio", "ReadImage", "ReadVideo")) {\n                            val state = assertNotNull(it.getBundle(name))\n                            for (key in listOf("granted", "rationale")) assertIs<Boolean>(state.get(key))\n                            for (key in listOf("availability", "access", "requestability")) assertIs<String>(state.get(key))\n                            val count = assertIs<Int>(state.get("callbacks"))\n                            assertTrue(count >= 0)\n                            if (count > 0) assertIs<Boolean>(state.get("callbackResult"))\n                            else assertFalse(state.containsKey("callbackResult"))\n                        }\n                    }\n                }\n                if (observationDeadline != null) check(SystemClock.elapsedRealtime() < observationDeadline) {\n                    "Late native validation cannot certify the no-dialog observation"\n                }\n            }\n        } finally { pending.remove(nonce); message.recycle() }\n    }\n\n'}, 'AndroidPermissionDemoDeviceTest.kt': {'before_sha256': '1018be28c520de3405ade706bc47dcd9142e34e5599a857801bf75a2388cf1c6', 'after_sha256': '9f57ad10e53b7445a1a1dc6c515bdfc9014b9fd8df7ad3e283e8ef3fd90ae975', 'before': '        consumer.ready()\n        consumer.request("request-microphone")\n        val deadline = SystemClock.elapsedRealtime() + 5000\n        var third: Bundle\n        while (true) {\n            assertFalse(ui.permissionDialogVisible(), "A third request after real permanent denial must not show another permission dialog")\n            third = consumer.request("observe")\n            if (third.getBundle("RecordAudio")?.getInt("callbacks") == 3) break\n            check(SystemClock.elapsedRealtime() < deadline)\n            Thread.sleep(20)\n        }\n', 'after': '        val expectedActivityGeneration = assertNotNull(permanent.getString("activityGeneration"))\n        assertEquals(expectedActivityGeneration, consumer.ready().getString("activityGeneration"))\n        consumer.request("request-microphone")\n        val deadline = SystemClock.elapsedRealtime() + 5000\n        var third: Bundle\n        var samples = 0\n        var windowKinds = 0\n        var refreshKinds = 0 // 1 unobserved; 2 false; 4 true.\n        var visibilityKinds = 0 // Same encoding; unobserved is never false.\n        var lastNativeHostReadiness = -1 // Diagnostic only; not used as an acceptance predicate.\n        fun observationFacts() = "samplesCapped512=$samples,windowKindsMask=$windowKinds," +\n            "refreshKindsMask=$refreshKinds,visibilityKindsMask=$visibilityKinds," +\n            "lastNativeHostReadinessMask=$lastNativeHostReadiness"\n        while (true) {\n            check(SystemClock.elapsedRealtime() < deadline) {\n                "No fresh owned native host/result proved the original no-dialog observation; " + observationFacts()\n            }\n            val observation = ui.permissionDialogObservation(deadline)\n            samples = minOf(samples + 1, 512)\n            windowKinds = windowKinds or observation.windowKind\n            refreshKinds = refreshKinds or (1 shl (observation.refreshed + 1))\n            visibilityKinds = visibilityKinds or (1 shl (observation.visible + 1))\n            assertNotEquals(PermissionDemoSystemUi.PermissionDialogKind.PRESENT, observation.kind,\n                "A third request after real permanent denial must not show another permission dialog; " + observationFacts())\n            if (observation.kind == PermissionDemoSystemUi.PermissionDialogKind.OWNED_VISIBLE_HOST) {\n                val native = consumer.observeBefore(deadline)\n                val active = assertIs<Boolean>(native.get("activityActive"))\n                lastNativeHostReadiness = 0\n                if (active) {\n                    assertEquals(expectedActivityGeneration, native.getString("activityGeneration"),\n                        "A replacement native Activity is not the original third-request host")\n                    val mounted = assertIs<Boolean>(native.get("mounted"))\n                    val resumed = assertIs<Boolean>(native.get("resumed"))\n                    val focused = assertIs<Boolean>(native.get("focused"))\n                    lastNativeHostReadiness = 1 or (if (mounted) 2 else 0) or\n                        (if (resumed) 4 else 0) or (if (focused) 8 else 0)\n                    if (mounted && resumed && focused) {\n                        val state = assertNotNull(native.getBundle("RecordAudio"))\n                        val callbacks = assertIs<Int>(state.get("callbacks"))\n                        assertTrue(callbacks in 2..3, "A rollback or duplicate native result is not the third request")\n                        if (callbacks == 3) {\n                            check(SystemClock.elapsedRealtime() < deadline) {\n                                "A late host/result cannot certify the original no-dialog deadline"\n                            }\n                            third = native\n                            break\n                        }\n                    }\n                }\n            }\n            // Unknown/null/stale/invisible/foreign/unready is never accepted as no dialog.\n            val remaining = deadline - SystemClock.elapsedRealtime()\n            check(remaining > 0) {\n                "No fresh owned native host/result proved the original no-dialog observation; " + observationFacts()\n            }\n            Thread.sleep(minOf(20L, remaining))\n        }\n'}}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def source(name):
    return (TREE / KOTLIN / name).read_text(encoding="utf-8")


def permission_absence_preimage(current, name):
    """Only this exact new source may restore the exact freeze059 fixture image.

    A missing, duplicated, altered fragment or outside mutation refuses BEFORE
    any historical source/annotation/timeout projection is consulted. Never
    accept an old/unknown source, skip a guard, or advance historical hashes.
    """
    require(name in ABSENCE_SOURCE_CHANGES and isinstance(current, str), "Exact owning fixture is required")
    change = ABSENCE_SOURCE_CHANGES[name]
    require(hashlib.sha256(current.encode()).hexdigest() == change["after_sha256"],
            "An unqualified current fixture cannot enter the historical guard projection")
    require(current.count(change["after"]) == 1 and change["before"] not in current,
            "The one exact approved third-absence fragment must be unique")
    prior = current.replace(change["after"], change["before"], 1)
    require(hashlib.sha256(prior.encode()).hexdigest() == change["before_sha256"],
            "The exact approved inverse must restore every historical source byte")
    return prior


def block(text, marker):
    """Narrow brace-balanced text reader; not a Kotlin parser/compiler."""
    require(text.count(marker) == 1, "One exact owning source marker is required")
    start = text.index("{", text.index(marker) + len(marker))
    depth, quote, escaped, comment = 1, None, False, False
    for index in range(start + 1, len(text)):
        char = text[index]
        if comment:
            if char == "\n": comment = False
        elif quote is not None:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == quote: quote = None
        elif char == "/" and text[index:index+2] == "//": comment = True
        elif char in ('"', "'"): quote = char
        elif char == "{": depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0: return text[start+1:index]
    raise AssertionError("Unterminated owning source marker")


def ordered(text, *steps):
    positions = [text.index(token) for token in steps]
    require(positions == sorted(positions), "Original causal observation/native order must remain")


def require_permission_absence_protocol(text):
    permission_absence_preimage(text, "PermissionDemoSystemUi.kt")
    observed = block(text, "fun permissionDialogObservation(deadline: Long)")
    ordered(observed, "requireObservationDeadline(deadline)", "val root = automation.rootInActiveWindow",
            "if (root == null) return PermissionDialogObservation(PermissionDialogKind.UNKNOWN, 1, -1, -1)",
            "val refreshed = root.refresh()", "val visible = if (refreshed) root.isVisibleToUser else null",
            "if (!refreshed) return PermissionDialogObservation(PermissionDialogKind.UNKNOWN, 32, 0, -1)",
            "val packageName = root.packageName?.toString()", "if (visible != true) return unknown",
            "if (packageName in PERMISSION)", "return unknown.copy(kind = PermissionDialogKind.PRESENT)",
            "unknown.copy(kind = PermissionDialogKind.OWNED_VISIBLE_HOST) else unknown")
    for token in ("ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP",
                  "getApplicationInfo(checkNotNull(packageName), 0)",
                  "return if (packageName == OwnedPermissionDemo.PACKAGE)",
                  "finally { root?.recycle() }"):
        require(token in observed, "Keep strict native ownership/presence/cleanup: " + token)
    for forbidden in ("catch (", "?: false", "getWindows(", ".windows", "clearCache", "consumer.",
                      "grantRuntimePermission", "setPackageName", "setVisibleToUser"):
        require(forbidden not in observed, "No unknown/presence/query/focus/grant substitution")
    deadline = block(text, "private fun requireObservationDeadline(")
    require("check(SystemClock.elapsedRealtime() < deadline)" in deadline,
            "A late SDK read must never certify no-dialog evidence")


def require_third_request_protocol(text):
    permission_absence_preimage(text, "AndroidPermissionDemoDeviceTest.kt")
    method = block(text, "@Test fun " + DENIAL + "()")
    ordered(method,
        'ui.permissionButtonAfterRequest(request, Manifest.permission.RECORD_AUDIO, "permission_deny_button")',
        "assertDenied(denied, rationale = true, count = 1)",
        'ui.permissionButton("permission_deny_button", "permission_deny_and_dont_ask_again_button")',
        "assertDenied(permanent, rationale = false, count = 2)",
        'val expectedActivityGeneration = assertNotNull(permanent.getString("activityGeneration"))',
        'assertEquals(expectedActivityGeneration, consumer.ready().getString("activityGeneration"))',
        "val deadline = SystemClock.elapsedRealtime() + 5000",
        "val observation = ui.permissionDialogObservation(deadline)",
        "assertNotEquals(PermissionDemoSystemUi.PermissionDialogKind.PRESENT, observation.kind",
        "if (observation.kind == PermissionDemoSystemUi.PermissionDialogKind.OWNED_VISIBLE_HOST)",
        "val native = consumer.observeBefore(deadline)",
        'val active = assertIs<Boolean>(native.get("activityActive"))',
        'assertEquals(expectedActivityGeneration, native.getString("activityGeneration")',
        "if (mounted && resumed && focused)", 'val callbacks = assertIs<Int>(state.get("callbacks"))',
        "assertTrue(callbacks in 2..3", "if (callbacks == 3)", "third = native", "break",
        "assertDenied(third, rationale = false, count = 3)",
        'assertEquals("Unknown", third.getBundle("RecordAudio")?.getString("requestability"))')
    for key in ("mounted", "resumed", "focused"):
        require('assertIs<Boolean>(native.get("' + key + '"))' in method,
                "Only actual typed ready host fields may admit callback3")
    require(method.count("SystemClock.elapsedRealtime() + 5000") == 1,
            "Never reset or expand the original absolute five-second budget")
    require(method.count("check(SystemClock.elapsedRealtime() < deadline)") == 2,
            "Require initial and final absence-admission deadline checks")
    require("val remaining = deadline - SystemClock.elapsedRealtime()" in method and
            "check(remaining > 0)" in method and "Thread.sleep(minOf(20L, remaining))" in method,
            "No unbounded or late observation/sleep acceptance")
    require(not re.search(r"(?:if|while|check|assertTrue)\s*\([^)]*lastNativeHostReadiness", method),
            "Diagnostic readiness masks must never become an acceptance predicate")


def require_bounded_native_observe(text):
    permission_absence_preimage(text, "OwnedPermissionDemo.kt")
    require('fun request(operation: String): Bundle = request(operation, observationDeadline = null)' in text and
            'fun observeBefore(deadline: Long): Bundle = request("observe", observationDeadline = deadline)' in text,
            "Read-only bounded observe must be opt-in; ordinary requests retain their old contract")
    requested = block(text, "private fun request(operation: String, observationDeadline: Long?)")
    ordered(requested, 'check(operation == "observe")',
            'check(SystemClock.elapsedRealtime() < observationDeadline)',
            'check(pending.put(nonce, reply) == null)', 'remote.send(message)',
            'val remaining = observationDeadline - SystemClock.elapsedRealtime()',
            'check(remaining > 0)', 'reply.ready.await(remaining, TimeUnit.MILLISECONDS)',
            'assertTrue(responseReady', 'A late native response cannot certify',
            'assertEquals(nonce, it.getString("nonce"))', 'assertEquals(owner.uid, it.getInt("uid"))',
            'Late native validation cannot certify')
    require('reply.ready.await(20, TimeUnit.SECONDS)' in requested,
            "Never change ordinary Call/picker/teardown20-second semantics")
    for token in ('assertNull(protocolError)', 'assertEquals(nativePid, pid)',
                  'assertNull(it.getString("probeError")', 'assertEquals(generation, actual)',
                  'assertIs<Boolean>(it.get("activityActive"))',
                  'finally { pending.remove(nonce); message.recycle() }',
                  'Foreign, late or duplicate native response',
                  'assertNotNull(endpoint, "Native teardown cannot infer Activity cleanup from a lost endpoint")',
                  'context.unbindService(connection)', 'thread.quitSafely()', 'check(!thread.isAlive)'):
        require(token in text, "Preserve actual native protocol/identity/refusal/cleanup: " + token)
    require(requested.count('check(SystemClock.elapsedRealtime() < observationDeadline)') == 4,
            "Preserve pre-observe/pre-send/post-wait/post-validation deadline gates")


def assignment(tree, name):
    values = [node for node in tree.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    require(len(values) == 1, "One exact owning AST declaration is required")
    return values[0].value


def spec_value(tree, key):
    value = assignment(tree, "ANDROID_PERMISSION_DEVICE_SPECS")
    selected = [item for name, item in zip(value.keys, value.values)
                if isinstance(name, ast.Name) and name.id == key]
    require(len(selected) == 1, "Exactly one current finite permission spec is required")
    return ast.literal_eval(selected[0])


def validate_denial_route(library, matrix, workflow):
    """AST/literal text only: do not execute the library/controller/CLI or fabricate a plan."""
    lib = ast.parse(library)
    require(ast.literal_eval(assignment(lib, FOCUS_NAME)) == PROFILE, "Only the fixed denial focus is allowed")
    spec = spec_value(lib, FOCUS_NAME)
    require(spec['classname'] == CLASS and spec['source'] == KOTLIN + 'AndroidPermissionDemoDeviceTest.kt' and
            spec['declared_methods'] == METHODS and spec['methods'] == (DENIAL,),
            "Exact original declarations/single-denial identity; accepted Call/picker are excluded")
    for key, selected in (("ANDROID_PERMISSION_DEMO_FOCUS", METHODS),
                          ("ANDROID_PERMISSION_DEMO_RECOVERY_FOCUS", METHODS[:2])):
        require(spec_value(lib, key)['methods'] == selected, "Retain all existing complete/recovery declarations")
    functions = [node for node in lib.body if isinstance(node, ast.FunctionDef) and node.name == 'android_permission_device_filter']
    require(len(functions) == 1, "Keep one owning native selector function")
    fn = functions[0]
    require(isinstance(fn.body[0], ast.Assign) and ast.unparse(fn.body[0].value) == 'ANDROID_PERMISSION_DEVICE_SPECS[focus]',
            "Unknown focus must fail at owning spec lookup, never default to whole class")
    branches = [node for node in fn.body if isinstance(node, ast.If) and ast.unparse(node.test) == 'focus == ' + FOCUS_NAME]
    require(len(branches) == 1 and len(branches[0].body) == 1 and isinstance(branches[0].body[0], ast.Return) and
            ast.unparse(branches[0].body[0].value) == "spec['classname'] + '#' + spec['methods'][0]",
            "Only supported class#single-original-method transport is allowed")
    old = [node for node in fn.body if isinstance(node, ast.If) and
           ast.unparse(node.test) == 'focus == ANDROID_PERMISSION_DEMO_RECOVERY_FOCUS']
    require(len(old) == 1 and len(old[0].body) == 1 and
            ast.unparse(old[0].body[0]) == 'return ANDROID_PERMISSION_DEMO_RECOVERY_ANNOTATION',
            "Retain accepted old annotation selector; never broaden or replay it")
    mat = ast.parse(matrix)
    aliases = native_aliases(mat, lambda relative: (TREE / relative).read_text(encoding="utf-8"))
    profile_nodes = assignment(mat, 'PROFILES')
    require(isinstance(profile_nodes, ast.Dict), "Keep the original declarative profile mapping")
    profile_names = [literal_metadata(key, aliases) for key in profile_nodes.keys]
    require(len(profile_names) == len(set(profile_names)), "No duplicate profile declarations")
    def profile_node(name):
        values = [value for key, value in zip(profile_names, profile_nodes.values) if key == name]
        require(len(values) == 1, "One exact owning profile declaration is required")
        return values[0]
    modules = literal_metadata(assignment(mat, 'MODULE_SUBSETS'), aliases)
    require(ast.literal_eval(profile_node(PROFILE)) == ('android-device-api35',) and modules[PROFILE] == CORE,
            "Only one exact existing API35 host and permission-core module")
    slots = ast.literal_eval(assignment(mat, 'SLOTS'))
    slot_names = tuple(slot['slot'] for slot in slots)
    require(slot_names == ('desktop-linux-x64', 'android-host', 'browser-js', 'browser-wasm',
            'desktop-macos-arm64', 'ios-iphone', 'desktop-windows-x64', 'desktop-linux-arm64',
            'desktop-macos-x64', 'ios-ipad', 'android-device-api35'),
            "Preserve all11 original full matrix slots")
    all_node = profile_node('all')
    require(isinstance(all_node, ast.Call) and isinstance(all_node.func, ast.Name) and all_node.func.id == 'tuple' and
            not all_node.keywords and len(all_node.args) == 1 and isinstance(all_node.args[0], ast.GeneratorExp),
            "Complete all profile must retain the original finite slot generator, not an evaluated replacement")
    generator = all_node.args[0]
    require(len(generator.generators) == 1 and isinstance(generator.elt, ast.Subscript) and
            isinstance(generator.elt.value, ast.Name) and generator.elt.value.id == 'slot' and
            isinstance(generator.elt.slice, ast.Constant) and generator.elt.slice.value == 'slot' and
            isinstance(generator.generators[0].target, ast.Name) and generator.generators[0].target.id == 'slot' and
            isinstance(generator.generators[0].iter, ast.Name) and generator.generators[0].iter.id == 'SLOTS' and
            not generator.generators[0].ifs and generator.generators[0].is_async == 0,
            "Original complete matrix generator must not omit or substitute slots")
    require(ast.literal_eval(profile_node('ios-picker-provider-cancellation')) == ('ios-iphone',) and
            modules['ios-picker-provider-cancellation'] == 'calf-file-picker',
            "Never overwrite the integrated #50 missing-only route")
    require(ast.literal_eval(assignment(lib, 'IOS_PICKER_PROVIDER_CANCELLATION_METHODS')) ==
            ('publicPhotoCancellationStopsAnInFlightNativeProviderCopyAndReleasesEarlierStaging',),
            "Keep the exact missing #50 method identity")
    matrix_functions = [node for node in mat.body if isinstance(node, ast.FunctionDef) and node.name == 'matrix']
    require(len(matrix_functions) == 1, "Keep one owning matrix function")
    denial_branches = [node for node in matrix_functions[0].body if isinstance(node, ast.If) and
                       ast.unparse(node.test) == "profile == '" + PROFILE + "'"]
    expected_branch = ast.parse('if profile == "' + PROFILE + '":\n'
        '    for row in rows:\n'
        '        row.update(slot="android-device-api35-permission-denial-recovery",\n'
        '            **{"test-focus": "android-permission-demo-denial-recovery"})\n').body[0]
    require(len(denial_branches) == 1 and
            ast.dump(denial_branches[0], include_attributes=False) == ast.dump(expected_branch, include_attributes=False),
            "Keep one exact profile-owned denial slot/focus branch without batch/serial/host fallback")
    choices = re.findall(r'(?m)^        options: \[([^\]\n]+)\]$', workflow)
    require(len(choices) == 1, "One strict literal dispatch choice list")
    options = [item.strip() for item in choices[0].split(',')]
    require(len(options) == len(set(options)) and options.count(PROFILE) == 1 and set(options) == set(profile_names),
            "No duplicated, missing or shell-shaped dispatch route")
    packages = re.findall(r"inputs\.profile == '" + re.escape(PROFILE) + r"' && '([^'\n]+)'", workflow)
    require(packages == [SDK], "Only the official API35 image/build-tools36.0.0 branch")
    require('permissions:\n  contents: read' in workflow and 'persist-credentials: false' in workflow,
            "Read-only verification and minimum-required permissions remain")


class AndroidPermissionDemoDenialAbsenceSourceGuards(unittest.TestCase):
    def test_exact_new_source_inverse_restores_every_historical_byte_and_no_old_source_fallback(self):
        for name, change in ABSENCE_SOURCE_CHANGES.items():
            current = source(name)
            previous = permission_absence_preimage(current, name)
            self.assertEqual(change['before_sha256'], hashlib.sha256(previous.encode()).hexdigest())
            with self.subTest(old_source=name), self.assertRaises(AssertionError):
                permission_absence_preimage(previous, name)

    def test_unknown_null_stale_invisible_missing_or_foreign_window_never_certifies_absence(self):
        current = source('PermissionDemoSystemUi.kt')
        require_permission_absence_protocol(current)
        changes = (
            ('PermissionDialogKind.UNKNOWN, 1, -1, -1', 'PermissionDialogKind.OWNED_VISIBLE_HOST, 1, -1, -1'),
            ('PermissionDialogKind.UNKNOWN, 32, 0, -1', 'PermissionDialogKind.OWNED_VISIBLE_HOST, 32, 0, -1'),
            ('val visible = if (refreshed) root.isVisibleToUser else null', 'val visible = true'),
            ('if (visible != true) return unknown', 'if (false) return unknown'),
            ('return if (packageName == OwnedPermissionDemo.PACKAGE)', 'return if (true)'),
        )
        for before, after in changes:
            self.assertIn(before, current)
            with self.subTest(weakened=before), self.assertRaises(AssertionError):
                require_permission_absence_protocol(current.replace(before, after, 1))

    def test_fresh_visible_system_permission_controller_is_immediate_presence_not_no_dialog(self):
        current = source('PermissionDemoSystemUi.kt')
        require_permission_absence_protocol(current)
        for before, after in (
            ('return unknown.copy(kind = PermissionDialogKind.PRESENT)', 'return unknown'),
            ('ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP', '0'),
            ('getApplicationInfo(checkNotNull(packageName), 0)', 'getApplicationInfo(OwnedPermissionDemo.PACKAGE, 0)'),
            ('finally { root?.recycle() }', 'finally {}'),
        ):
            self.assertIn(before, current)
            with self.subTest(weakened=before), self.assertRaises(AssertionError):
                require_permission_absence_protocol(current.replace(before, after, 1))

    def test_fresh_owned_root_original_activity_and_all_typed_ready_fields_admit_only_exact_callback_three(self):
        current = source('AndroidPermissionDemoDeviceTest.kt')
        require_third_request_protocol(current)
        for before, after in (
            ('if (observation.kind == PermissionDemoSystemUi.PermissionDialogKind.OWNED_VISIBLE_HOST)', 'if (true)'),
            ('assertEquals(expectedActivityGeneration, native.getString("activityGeneration")', 'assertNotNull(native.getString("activityGeneration")'),
            ('assertIs<Boolean>(native.get("focused"))', 'native.getBoolean("focused")'),
            ('if (mounted && resumed && focused)', 'if (mounted || resumed || focused)'),
            ('assertTrue(callbacks in 2..3', 'assertTrue(callbacks in 0..4'),
            ('if (callbacks == 3)', 'if (callbacks >= 2)'),
        ):
            self.assertIn(before, current)
            with self.subTest(weakened=before), self.assertRaises(AssertionError):
                require_third_request_protocol(current.replace(before, after, 1))

    def test_first_second_real_deny_and_original_final_denied_unknown_callbacks_stay_exact(self):
        current = source('AndroidPermissionDemoDeviceTest.kt')
        require_third_request_protocol(current)
        for before, after in (
            ('"permission_deny_button")', '"permission_allow_button")'),
            ('assertDenied(denied, rationale = true, count = 1)', 'assertDenied(denied, rationale = false, count = 1)'),
            ('assertDenied(permanent, rationale = false, count = 2)', 'assertDenied(permanent, rationale = false, count = 1)'),
            ('assertDenied(third, rationale = false, count = 3)', 'assertDenied(third, rationale = false, count = 2)'),
            ('assertEquals("Unknown", third.getBundle("RecordAudio")?.getString("requestability"))', 'assertTrue(true)'),
            ('assertFalse(state.getBoolean("callbackResult"))', 'assertTrue(state.getBoolean("callbackResult"))'),
        ):
            self.assertIn(before, current)
            with self.subTest(weakened=before), self.assertRaises(AssertionError):
                require_third_request_protocol(current.replace(before, after, 1))

    def test_original_absolute_five_second_deadline_refuses_late_sdk_send_wait_validation_and_sleeps(self):
        cases = (
            ('PermissionDemoSystemUi.kt', require_permission_absence_protocol,
             'check(SystemClock.elapsedRealtime() < deadline)', 'check(true)'),
            ('AndroidPermissionDemoDeviceTest.kt', require_third_request_protocol,
             'SystemClock.elapsedRealtime() + 5000', 'SystemClock.elapsedRealtime() + 5001'),
            ('AndroidPermissionDemoDeviceTest.kt', require_third_request_protocol,
             'Thread.sleep(minOf(20L, remaining))', 'Thread.sleep(20)'),
            ('OwnedPermissionDemo.kt', require_bounded_native_observe,
             'check(remaining > 0)', 'check(true)'),
            ('OwnedPermissionDemo.kt', require_bounded_native_observe,
             'reply.ready.await(remaining, TimeUnit.MILLISECONDS)', 'reply.ready.await(20, TimeUnit.SECONDS)'),
            ('OwnedPermissionDemo.kt', require_bounded_native_observe,
             'check(SystemClock.elapsedRealtime() < observationDeadline)', 'check(true)'),
        )
        for name, validator, before, after in cases:
            current = source(name)
            validator(current)
            self.assertIn(before, current)
            with self.subTest(weakened=before), self.assertRaises(AssertionError):
                validator(current.replace(before, after, 1))
        # Individually protect every identical pre/post callsite, not only its first occurrence.
        for name, validator, token, expected_sites in (
            ('PermissionDemoSystemUi.kt', require_permission_absence_protocol,
             'requireObservationDeadline(deadline)', 2),
            ('PermissionDemoSystemUi.kt', require_permission_absence_protocol,
             'requireObservationDeadline(deadline, 1, 1)', 2),
            ('OwnedPermissionDemo.kt', require_bounded_native_observe,
             'check(SystemClock.elapsedRealtime() < observationDeadline)', 4),
            ('AndroidPermissionDemoDeviceTest.kt', require_third_request_protocol,
             'check(SystemClock.elapsedRealtime() < deadline)', 2),
        ):
            current = source(name)
            positions = [match.start() for match in re.finditer(re.escape(token), current)]
            self.assertEqual(expected_sites, len(positions))
            for index in positions:
                changed = current[:index] + 'check(true)' + current[index + len(token):]
                with self.subTest(owning_fixture=name, late_gate_offset=index), self.assertRaises(AssertionError):
                    validator(changed)

    def test_bounded_observe_is_read_only_and_ordinary_native_requests_protocol_and_cleanup_remain(self):
        current = source('OwnedPermissionDemo.kt')
        require_bounded_native_observe(current)
        for before, after in (
            ('request("observe", observationDeadline = deadline)', 'request("request-microphone", observationDeadline = deadline)'),
            ('reply.ready.await(20, TimeUnit.SECONDS)', 'reply.ready.await(21, TimeUnit.SECONDS)'),
            ('message.sendingUid != owner.uid', 'message.sendingUid == owner.uid'),
            ('assertEquals(nativePid, pid)', 'assertTrue(true)'),
            ('assertNull(it.getString("probeError")', 'assertNotNull(it.getString("probeError")'),
            ('pending.remove(nonce); message.recycle()', 'message.recycle()'),
            ('context.unbindService(connection)', 'assertTrue(true)'),
            ('check(!thread.isAlive)', 'check(true)'),
        ):
            self.assertIn(before, current)
            with self.subTest(weakened=before), self.assertRaises(AssertionError):
                require_bounded_native_observe(current.replace(before, after, 1))

    def test_unique_fragment_and_outside_source_barriers_refuse_missing_duplicate_mutated_or_broad_waivers(self):
        for name, change in ABSENCE_SOURCE_CHANGES.items():
            current = source(name)
            for label, mutated in (
                ('missing', current.replace(change['after'], '', 1)),
                ('duplicate', current + change['after']),
                ('outside', '// unqualified outside source delta\n' + current),
                ('altered-fragment', current.replace(change['after'], change['after'] + '// unqualified delta\n', 1)),
            ):
                self.assertNotEqual(current, mutated)
                with self.subTest(fixture=name, rejection=label), self.assertRaises(AssertionError):
                    permission_absence_preimage(mutated, name)

    def route_sources(self):
        return tuple((TREE / relative).read_text(encoding='utf-8') for relative in
                     ('scripts/ci/library_tests.py', 'scripts/ci/workflow_matrix.py', '.github/workflows/gradle.yml'))

    def test_one_original_denial_method_and_api35_route_preserve_complete_old_and_ios50_declarations(self):
        validate_denial_route(*self.route_sources())

    def test_route_refuses_class_fallback_accepted_replay_wrong_api_module_or_duplicate_dispatch(self):
        library, matrix, workflow = self.route_sources()
        validate_denial_route(library, matrix, workflow)
        mutations = (
            (0, 'return spec["classname"] + "#" + spec["methods"][0]', 'return spec["classname"]'),
            (0, '"methods": ("' + DENIAL + '",),', '"methods": ("' + CALL + '",),'),
            (1, '"' + PROFILE + '": ("android-device-api35",),', '"' + PROFILE + '": ("android-device-api23",),'),
            (1, '"' + PROFILE + '": "calf-permissions/core",', '"' + PROFILE + '": "calf-io",'),
            (1, 'if profile == "' + PROFILE + '":', 'if profile == "unknown-denial-profile":'),
            (2, PROFILE + ', android-io-permission-storage-api35', PROFILE + ', ' + PROFILE + ', android-io-permission-storage-api35'),
            (2, "inputs.profile == '" + PROFILE + "' && '" + SDK + "'", "inputs.profile == '" + PROFILE + "' && '" + SDK.replace('build-tools;36.0.0 ', '') + "'"),
        )
        for index, before, after in mutations:
            values = [library, matrix, workflow]
            self.assertIn(before, values[index])
            values[index] = values[index].replace(before, after, 1)
            with self.subTest(weakened=before), self.assertRaises((AssertionError, KeyError)):
                validate_denial_route(*values)


if __name__ == '__main__':
    unittest.main()
