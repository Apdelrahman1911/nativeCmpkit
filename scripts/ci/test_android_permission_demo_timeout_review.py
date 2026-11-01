"""New observation-only source/scalar models; no Kotlin build, native UI or actual replay."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import unittest

TREE = Path(os.environ.get("PERMISSION_TIMEOUT_REVIEW_TREE", Path(__file__).resolve().parents[2])).resolve()
KOTLIN = "calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/"
UI_BEFORE_SHA256 = "5391623a81d9ca2d18d1ebe35e7931ce3c0ba4f56e737da5f2272a76ceae6ffd"
NATIVE_BEFORE_SHA256 = "e55b84ffd061767e66ae128b57ea9262c4f6e0c2af2446ebd6a53231e9d569cf"

UI_DELTAS = (('import android.Manifest\n'
  'import android.os.Bundle\n'
  'import android.accessibilityservice.AccessibilityServiceInfo\n',
  'import android.accessibilityservice.AccessibilityServiceInfo\n'),
 ('    fun permissionButton(vararg ids: String) = clickId(PERMISSION, *ids)\n'
  '    fun permissionButtonAfterRequest(request: Bundle, permission: String, vararg ids: String) =\n'
  '        clickId(PERMISSION, *ids, requestFacts = requestReplyFacts(request, permission))\n',
  '    fun permissionButton(vararg ids: String) = clickId(PERMISSION, *ids)\n'),
 ('    // This is the already validated reply immediately after the public method returned,\n'
  '    // not proof of native dispatch, a later callback, a visible dialog or a grant.\n'
  '    private fun requestReplyFacts(request: Bundle, permission: String): String {\n'
  '        val kind = when (permission) {\n'
  '            Manifest.permission.CALL_PHONE -> 1\n'
  '            Manifest.permission.RECORD_AUDIO -> 2\n'
  '            else -> error("Only the two owned permission request observations are allowed")\n'
  '        }\n'
  '        val state = request.get(if (kind == 1) "Call" else "RecordAudio") as? Bundle\n'
  '        val callbacks = (state?.get("callbacks") as? Int)?.let {\n'
  '            if (it >= 0) minOf(it, 4) else -1\n'
  '        } ?: -1\n'
  '        return "requestReplyKind=$kind,requestReplyReturned=1," +\n'
  '            "requestReplyGrant=${diagnosticBoolean(request.get(permission))}," +\n'
  '            "requestReplyRationale=${diagnosticBoolean(request.get(permission + ".rationale"))}," +\n'
  '            "requestReplyCallbacksCapped4=$callbacks," +\n'
  '            "requestReplyResumed=${diagnosticBoolean(request.get("resumed"))}," +\n'
  '            "requestReplyFocused=${diagnosticBoolean(request.get("focused"))}"\n'
  '    }\n'
  '    private fun diagnosticBoolean(value: Any?): Int = when (value as? Boolean) {\n'
  '        true -> 1\n'
  '        false -> 0\n'
  '        null -> -1\n'
  '    }\n'
  '\n'
  '    fun permissionDialogVisible(): Boolean {\n',
  '    fun permissionDialogVisible(): Boolean {\n'),
 ('    private fun clickId(packages: Set<String>, vararg ids: String,\n'
  '        requestFacts: String = "requestReplyReturned=-1") = click(packages, { root ->\n'
  '        val packageName = assertNotNull(root.packageName).toString()\n'
  '        ids.flatMap { root.findAccessibilityNodeInfosByViewId("$packageName:id/$it") }\n'
  '    }, requestFacts = requestFacts)\n',
  '    private fun clickId(packages: Set<String>, vararg ids: String) = click(packages, { root ->\n'
  '        val packageName = assertNotNull(root.packageName).toString()\n'
  '        ids.flatMap { root.findAccessibilityNodeInfosByViewId("$packageName:id/$it") }\n'
  '    })\n'),
 ('    private fun click(packages: Set<String>, nodes: (AccessibilityNodeInfo) -> '
  'List<AccessibilityNodeInfo>,\n'
  '        selected: (AccessibilityNodeInfo) -> Boolean = { true },\n'
  '        requestFacts: String = "requestReplyReturned=-1") {\n',
  '    private fun click(packages: Set<String>, nodes: (AccessibilityNodeInfo) -> '
  'List<AccessibilityNodeInfo>,\n'
  '        selected: (AccessibilityNodeInfo) -> Boolean = { true }) {\n'),
 ('        val deadline = SystemClock.elapsedRealtime() + 20000\n'
  '        var samples = 0\n'
  '        var windowKinds = 0 // 1 null root; 2 missing package; 4 owned app; 8 allowed OS; 16 other.\n'
  '        var exactQueries = 0\n'
  '        var maxExactQueryNodes = -1 // Unknown is not an observed empty query.\n'
  '        var maxVisibleMatches = -1\n',
  '        val deadline = SystemClock.elapsedRealtime() + 20000\n'),
 ('        while (SystemClock.elapsedRealtime() < deadline) {\n'
  '            samples = minOf(samples + 1, 512)\n'
  '            val root = automation.rootInActiveWindow\n',
  '        while (SystemClock.elapsedRealtime() < deadline) {\n'
  '            val root = automation.rootInActiveWindow\n'),
 ('                    val packageName = root.packageName?.toString()\n'
  '                    windowKinds = windowKinds or when {\n'
  '                        packageName == null -> 2\n'
  '                        packageName in packages -> 8\n'
  '                        packageName == OwnedPermissionDemo.PACKAGE -> 4\n'
  '                        else -> 16\n'
  '                    }\n',
  '                    val packageName = root.packageName?.toString()\n'),
 ('                            assertTrue(acquired.size <= 128, "The exact bounded node query returned an '
  'unexpected inventory")\n'
  '                            exactQueries = minOf(exactQueries + 1, 512)\n'
  '                            maxExactQueryNodes = maxOf(maxExactQueryNodes, acquired.size)\n',
  '                            assertTrue(acquired.size <= 128, "The exact bounded node query returned an '
  'unexpected inventory")\n'),
 ('                            assertTrue(matches.size <= 1, "An ambiguous visible OS control must not be '
  'clicked")\n'
  '                            maxVisibleMatches = maxOf(maxVisibleMatches, matches.size)\n',
  '                            assertTrue(matches.size <= 1, "An ambiguous visible OS control must not be '
  'clicked")\n'),
 ('                } finally { root.recycle() }\n'
  '            } else {\n'
  '                windowKinds = windowKinds or 1\n'
  '            }\n'
  '            Thread.sleep(40)\n',
  '                } finally { root.recycle() }\n            }\n            Thread.sleep(40)\n'),
 ('        fail("The exact required native OS control was not observed within the bound; " +\n'
  '            "samplesCapped512=$samples,windowKindsMask=$windowKinds,exactQueriesCapped512=$exactQueries," '
  '+\n'
  '            "maxExactQueryNodes=$maxExactQueryNodes,maxVisibleMatches=$maxVisibleMatches;$requestFacts")\n',
  '        fail("The exact required native OS control was not observed within the bound")\n'))
NATIVE_DELTAS = (('        val request = consumer.request("request-call")\n'
  '        ui.permissionButtonAfterRequest(request, Manifest.permission.CALL_PHONE, '
  '"permission_allow_button")\n',
  '        consumer.request("request-call")\n        ui.permissionButton("permission_allow_button")\n'),
 ('        val request = consumer.request("request-microphone")\n'
  '        ui.permissionButtonAfterRequest(request, Manifest.permission.RECORD_AUDIO, '
  '"permission_deny_button")\n',
  '        consumer.request("request-microphone")\n        ui.permissionButton("permission_deny_button")\n'))


def reverse_observation_only(source, deltas, expected):
    for after, before in reversed(deltas):
        if source.count(after) != 1:
            raise AssertionError("Missing or ambiguous owning observation-only delta")
        source = source.replace(after, before, 1)
    if hashlib.sha256(source.encode()).hexdigest() != expected:
        raise AssertionError("A non-observation selector, native criterion or cleanup changed")
    return source


def diagnostic_boolean(value):
    """Mirror of the new tri-state Kotlin projection, not an Android observation."""
    return 1 if value is True else 0 if value is False else -1


def request_reply_model(request, permission):
    choices = {"android.permission.CALL_PHONE": (1, "Call"),
               "android.permission.RECORD_AUDIO": (2, "RecordAudio")}
    if permission not in choices:
        raise ValueError("Not one of the two fixed modeled permission requests")
    kind, name = choices[permission]
    state = request.get(name)
    state = state if type(state) is dict else {}
    count = state.get("callbacks")
    count = min(count, 4) if type(count) is int and count >= 0 else -1
    return {"requestReplyKind": kind, "requestReplyReturned": 1,
        "requestReplyGrant": diagnostic_boolean(request.get(permission)),
        "requestReplyRationale": diagnostic_boolean(request.get(permission + ".rationale")),
        "requestReplyCallbacksCapped4": count,
        "requestReplyResumed": diagnostic_boolean(request.get("resumed")),
        "requestReplyFocused": diagnostic_boolean(request.get("focused"))}


def window_query_model(records):
    """Existing exact-query observations only; never a selector, click or success model."""
    result = {"samplesCapped512": 0, "windowKindsMask": 0, "exactQueriesCapped512": 0,
              "maxExactQueryNodes": -1, "maxVisibleMatches": -1}
    for kind, acquired, visible in records:
        if type(kind) is not int or kind not in (1, 2, 4, 8, 16):
            raise ValueError("Not a fixed modeled root class")
        result["samplesCapped512"] = min(result["samplesCapped512"] + 1, 512)
        result["windowKindsMask"] |= kind
        if acquired is None and visible is None:
            continue
        if (kind != 8 or type(acquired) is not int or type(visible) is not int or
            not 0 <= acquired <= 128 or not 0 <= visible <= 1 or visible > acquired):
            raise ValueError("Unknown/foreign/unbounded/ambiguous queries remain refusals")
        result["exactQueriesCapped512"] = min(result["exactQueriesCapped512"] + 1, 512)
        result["maxExactQueryNodes"] = max(result["maxExactQueryNodes"], acquired)
        result["maxVisibleMatches"] = max(result["maxVisibleMatches"], visible)
    return result


class AndroidPermissionDemoTimeoutReviewTests(unittest.TestCase):
    def source(self, name):
        return (TREE / KOTLIN / name).read_text()

    def test_timeout_delta_preserves_every_original_selector_action_refusal_and_resource_cleanup(self):
        source = self.source("PermissionDemoSystemUi.kt")
        original = reverse_observation_only(source, UI_DELTAS, UI_BEFORE_SHA256)
        self.assertIn("SystemClock.elapsedRealtime() + 20000", original)
        self.assertIn("Thread.sleep(40)", original)
        for old, changed in (
            ("acquired.size <= 128", "acquired.size <= 129"),
            ("matches.size <= 1", "matches.size <= 2"),
            ("if (packageName in packages)", "if (true)"),
            ("node.performAction(AccessibilityNodeInfo.ACTION_CLICK)", "true"),
            ("flags = originalFlags", "flags = 0"),
        ):
            self.assertEqual(1, source.count(old))
            with self.subTest(owning_mutation=old), self.assertRaises(AssertionError):
                reverse_observation_only(source.replace(old, changed, 1), UI_DELTAS, UI_BEFORE_SHA256)

    def test_two_first_click_replies_are_observation_only_and_picker_and_later_criteria_remain_byte_exact(self):
        source = self.source("AndroidPermissionDemoDeviceTest.kt")
        original = reverse_observation_only(source, NATIVE_DELTAS, NATIVE_BEFORE_SHA256)
        self.assertEqual(original.count('consumer.request("request-call")'), source.count('consumer.request("request-call")'))
        self.assertEqual(original.count('consumer.request("request-microphone")'), source.count('consumer.request("request-microphone")'))
        for old, changed in (
            ('assertTrue(native.getBoolean(Manifest.permission.CALL_PHONE))', 'assertTrue(true)'),
            ('assertDenied(denied, rationale = true, count = 1)', 'assertDenied(denied, rationale = false, count = 1)'),
            ('assertDenied(permanent, rationale = false, count = 2)', 'assertDenied(permanent, rationale = false, count = 1)'),
            ('assertFalse(ui.permissionDialogVisible(),', 'assertTrue(ui.permissionDialogVisible(),'),
            ('assertTrue(read.getBoolean("sourcePreserved"))', 'assertTrue(true)'),
        ):
            self.assertEqual(1, source.count(old))
            with self.subTest(criterion_mutation=old), self.assertRaises(AssertionError):
                reverse_observation_only(source.replace(old, changed, 1), NATIVE_DELTAS, NATIVE_BEFORE_SHA256)

    def test_approved_call_denial_marker_is_the_only_new_pre_observation_hash_delta(self):
        source = self.source("AndroidPermissionDemoDeviceTest.kt")
        baseline = reverse_observation_only(source, NATIVE_DELTAS, NATIVE_BEFORE_SHA256)
        name = "AndroidPermissionDemoCallDenialVerification"
        declaration = ("@Target(AnnotationTarget.FUNCTION)\n"
            "@Retention(AnnotationRetention.RUNTIME)\nannotation class " + name + "\n\n")
        marker = "    @" + name + "\n"
        self.assertEqual(1, baseline.count(declaration))
        self.assertEqual(2, baseline.count(marker))
        self.assertEqual(3, baseline.count(name))
        for method in ("callOnFreshApprovedVariantUsesPublicRequestAndActualSystemGrant",
                       "denialThenPermanentDenialKeepsActualRationaleAndOneResultPerRequest"):
            self.assertEqual(1, baseline.count(marker + "    @Test fun " + method + "() {"))
        original = baseline.replace(declaration, "", 1).replace(marker, "")
        self.assertEqual("ce60b4bb2b430b70726c5ff8a41838e9a015a18adb338bc5a099cfaf13813736",
            hashlib.sha256(original.encode()).hexdigest())
        original_source = source.replace(declaration, "", 1).replace(marker, "")
        self.assertEqual("06ab71c08cb881d17af0228f8a50c7df543ed22cf56682ccf2ac0a58e7507f07",
            hashlib.sha256(original_source.encode()).hexdigest())

    def test_advanced_hash_refuses_unapproved_annotation_and_new_deadline_callback_changes(self):
        source = self.source("AndroidPermissionDemoDeviceTest.kt")
        name = "AndroidPermissionDemoCallDenialVerification"
        declaration = ("@Target(AnnotationTarget.FUNCTION)\n"
            "@Retention(AnnotationRetention.RUNTIME)\nannotation class " + name + "\n\n")
        marker = "    @" + name + "\n"
        call = "    @Test fun callOnFreshApprovedVariantUsesPublicRequestAndActualSystemGrant() {"
        picker = "    @Test fun pickersReadRealDocumentsAndImagesWithoutAllFilesOrSmsPermissions() {"
        variants = (
            ("missing-declaration", source.replace(declaration, "", 1)),
            ("missing-call-marker", source.replace(marker, "", 1)),
            ("missing-both-markers", source.replace(marker, "")),
            ("duplicate-declaration", source.replace(declaration, declaration + declaration, 1)),
            ("duplicate-call-marker", source.replace(marker, marker + marker, 1)),
            ("source-retention", source.replace("AnnotationRetention.RUNTIME", "AnnotationRetention.SOURCE", 1)),
            ("binary-retention", source.replace("AnnotationRetention.RUNTIME", "AnnotationRetention.BINARY", 1)),
            ("class-target", source.replace("AnnotationTarget.FUNCTION", "AnnotationTarget.CLASS", 1)),
            ("broader-target", source.replace("AnnotationTarget.FUNCTION", "AnnotationTarget.FUNCTION, AnnotationTarget.CLASS", 1)),
            ("marker-after-Test", source.replace(marker + call, "    @Test\n" + marker + call.replace("    @Test ", "    "), 1)),
            ("marker-moved-to-picker", source.replace(marker, "", 1).replace(picker, marker + picker, 1)),
            ("marker-moved-to-class", source.replace(marker, "", 1).replace("@RunWith(AndroidJUnit4::class)", "@" + name + "\n@RunWith(AndroidJUnit4::class)", 1)),
            ("nested-declaration", source.replace(declaration, "", 1).replace("class AndroidPermissionDemoDeviceTest {", "class AndroidPermissionDemoDeviceTest {\n" + declaration, 1)),
            ("declaration-before-imports", source.replace(declaration, "", 1).replace("import android.Manifest\n", declaration + "import android.Manifest\n", 1)),
            ("fully-qualified-marker", source.replace(marker, "    @com.mohamedrejeb.calf.permissions." + name + "\n", 1)),
            ("foreign-helper-marker", source + "\n@" + name + "\nfun foreignSelectorHelper() {}\n"),
            ("foreign-annotation-name", source.replace(name, name + "Foreign")),
            ("foreign-alias", source.replace("import org.junit.Test\n", "import com.mohamedrejeb.calf.permissions." + name + " as Foreign\nimport org.junit.Test\n", 1)),
            ("changed-third-request-deadline", source.replace("SystemClock.elapsedRealtime() + 5000", "SystemClock.elapsedRealtime() + 5001", 1)),
            ("changed-third-callback-count", source.replace('?.getInt("callbacks") == 3', '?.getInt("callbacks") == 4', 1)),
        )
        for label, changed in variants:
            with self.subTest(new_changed_input=label):
                self.assertNotEqual(source, changed)
                with self.assertRaises(AssertionError):
                    reverse_observation_only(changed, NATIVE_DELTAS, NATIVE_BEFORE_SHA256)

    def test_request_reply_projection_is_unknown_safe_saturating_and_excludes_raw_bundle_or_ui_data(self):
        source = self.source("PermissionDemoSystemUi.kt")
        projection = source.split("private fun requestReplyFacts(", 1)[1].split("fun permissionDialogVisible()", 1)[0]
        for token in ('request.get(if (kind == 1) "Call" else "RecordAudio") as? Bundle',
            'state?.get("callbacks") as? Int', 'if (it >= 0) minOf(it, 4) else -1',
            'when (value as? Boolean)', 'null -> -1'):
            self.assertIn(token, projection)
        for forbidden in (".getBoolean(", ".toString()", "rootInActiveWindow", "findAccessibility", "launch(",
            "performAction", '"nonce"', '"generation"', '"uid"', '"pid"', '"probeError"'):
            self.assertNotIn(forbidden, projection)
        native = "android.permission.CALL_PHONE"
        for value in (None, False, True, 0, 1, -1, 1.0, "synthetic-not-for-output", b"synthetic-not-for-output", []):
            request = {native: value, native + ".rationale": value, "resumed": value, "focused": value,
                "Call": {"callbacks": value}, "nonce": "synthetic-not-for-output",
                "probeError": "synthetic-not-for-output", "arbitrary": "synthetic-not-for-output"}
            before = deepcopy(request)
            facts = request_reply_model(request, native)
            self.assertEqual(before, request)
            expected = diagnostic_boolean(value)
            self.assertEqual([expected] * 4, [facts[key] for key in (
                "requestReplyGrant", "requestReplyRationale", "requestReplyResumed", "requestReplyFocused")])
            self.assertTrue(all(type(field) is int for field in facts.values()))
            self.assertNotIn("synthetic-not-for-output", json.dumps(facts))
            self.assertLess(len(json.dumps(facts)), 512)
        self.assertEqual(-1, request_reply_model({"Call": []}, native)["requestReplyCallbacksCapped4"])
        self.assertEqual(4, request_reply_model({"Call": {"callbacks": 2**31 - 1}}, native)["requestReplyCallbacksCapped4"])
        self.assertEqual(2, request_reply_model({}, "android.permission.RECORD_AUDIO")["requestReplyKind"])
        for unknown in ("android.permission.CAMERA", "android.permission.READ_MEDIA_IMAGES", "", None):
            with self.subTest(unreviewed_permission=unknown), self.assertRaises(ValueError):
                request_reply_model({}, unknown)

    def test_window_query_models_distinguish_unknown_window_empty_exact_query_and_hidden_matches(self):
        unknown = window_query_model([(1, None, None)])
        owned = window_query_model([(4, None, None)])
        empty = window_query_model([(8, 0, 0)])
        hidden = window_query_model([(8, 1, 0)])
        self.assertEqual(-1, unknown["maxExactQueryNodes"])
        self.assertEqual(-1, owned["maxVisibleMatches"])
        self.assertEqual(0, empty["maxExactQueryNodes"])
        self.assertEqual(1, hidden["maxExactQueryNodes"])
        self.assertEqual(0, hidden["maxVisibleMatches"])
        self.assertEqual(4, len({json.dumps(value, sort_keys=True) for value in (unknown, owned, empty, hidden)}))
        maximum = window_query_model([(kind, None, None) for kind in (1, 2, 4, 8, 16)] + [(8, 128, 0)] * 1024)
        self.assertEqual({"samplesCapped512": 512, "windowKindsMask": 31, "exactQueriesCapped512": 512,
            "maxExactQueryNodes": 128, "maxVisibleMatches": 0}, maximum)
        for record in ((16, 1, 0), (1, 0, 0), (8, 129, 0), (8, 2, 2), (8, -1, 0), (8, True, 0), (8, 0, 1), (0, None, None)):
            with self.subTest(refused_record=record), self.assertRaises(ValueError):
                window_query_model([record])

    def test_timeout_facts_cannot_become_a_selector_click_or_native_success_fallback(self):
        source = self.source("PermissionDemoSystemUi.kt")
        original = reverse_observation_only(source, UI_DELTAS, UI_BEFORE_SHA256)
        for token in ("rootInActiveWindow", "findAccessibilityNodeInfosByViewId", "findAccessibilityNodeInfosByText", "performAction("):
            self.assertEqual(original.count(token), source.count(token))
        for forbidden in ("takeScreenshot", "getWindows(", ".windows", "viewIdResourceName", "getChild(", "getChildCount(",
            "grantRuntimePermission", "adoptShellPermissionIdentity", "Log.", "println("):
            self.assertNotIn(forbidden, source)
        self.assertEqual(1, source.count('fail("The exact required native OS control was not observed within the bound; "'))
        self.assertIn('"maxExactQueryNodes=$maxExactQueryNodes,maxVisibleMatches=$maxVisibleMatches;$requestFacts")', source)
        self.assertIn('requestFacts: String = "requestReplyReturned=-1"', source)
        # These facts have no pass/grant inference field even with an observed control or a true grant.
        fields = {**window_query_model([(8, 1, 1)]), **request_reply_model({"android.permission.CALL_PHONE": True},
            "android.permission.CALL_PHONE")}
        self.assertNotIn("passed", fields)
        self.assertNotIn("nativeDispatchSucceeded", fields)
        self.assertNotIn("nativeSuccessInferred", fields)


if __name__ == "__main__":
    unittest.main()
