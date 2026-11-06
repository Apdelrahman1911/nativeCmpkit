# SPDX-License-Identifier: Apache-2.0
"""Four NEW source-only inherited Kotlin TestFilter property controls.

No Gradle/JVM/native/browser/network/compiler calls or source discovery. Full
current ingress requires the separately owned joint existing730 qualification.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import unittest
import cookie_ci668_outer_source_projection as outer

ROOT = Path(__file__).resolve().parents[3]
BUILD = "calf-webview/build.gradle.kts"
BEFORE = (9474, "01801ef71db7b6b404a663eaf3a4585745b7e9fa8decad81dcb601f2b11d66c8")
AFTER = (9466, "8e369014dc60efb7a91d7fffe61e6d431bf573dc560ceda5d519fc32b2f19822")
IOS_BEFORE = b'    filter { excludeTestsMatching("com.mohamedrejeb.calf.ui.web.IosCookieWireAcceptanceTest.*") }\n'
IOS_AFTER = b'    filter.excludeTestsMatching("com.mohamedrejeb.calf.ui.web.IosCookieWireAcceptanceTest.*")\n'
JS_BEFORE = b'    filter { excludeTestsMatching("com.mohamedrejeb.calf.ui.web.BrowserCookieWireAcceptanceTest.*") }\n'
JS_AFTER = b'    filter.excludeTestsMatching("com.mohamedrejeb.calf.ui.web.BrowserCookieWireAcceptanceTest.*")\n'
FRAGMENTS = ((IOS_BEFORE, IOS_AFTER), (JS_BEFORE, JS_AFTER))
JVM_ACTION = b'    filter { excludeTestsMatching("com.mohamedrejeb.calf.ui.web.DesktopCookieWireAcceptanceTest.*") }\n'


def _identity(payload):
    return len(payload), hashlib.sha256(payload).hexdigest()


def _build():
    return outer.ordinary_bytes(ROOT, BUILD)


def _independent_inverse(payload):
    result = payload
    for before, after in reversed(FRAGMENTS):
        if result.count(after) != 1:
            raise AssertionError("Independent two-call inverse needs one exact occurrence")
        result = result.replace(after, before, 1)
    return result


class WebViewKotlinTestFilterApi777Tests(unittest.TestCase):
    def test_native_inherited_filter_property_preserves_exact_ios_class_and_jvm_action(self):
        payload = _build()
        self.assertEqual(AFTER, _identity(payload))
        native = b"tasks.withType<KotlinNativeTest>().configureEach {\n" + IOS_AFTER + b"}\n"
        self.assertEqual(1, payload.count(native))
        self.assertEqual(0, payload.count(IOS_BEFORE))
        self.assertEqual(1, payload.count(JVM_ACTION))
        # Both original desktop matching headers remain; neither material fragment touches them.
        self.assertEqual(2, payload.count(b'tasks.withType<Test>().matching { it.name == "desktopTest" }'))
        self.assertEqual(1, payload.count(b'"com.mohamedrejeb.calf.ui.web.IosCookieWireAcceptanceTest.*"'))
        self.assertNotIn(b"excludePatterns.add", payload)

    def test_js_inherited_filter_property_preserves_exact_browser_class_and_other_tests(self):
        payload = _build()
        self.assertEqual(AFTER, _identity(payload))
        js = b"tasks.withType<KotlinJsTest>().configureEach {\n" + JS_AFTER + b"}\n"
        self.assertEqual(1, payload.count(js))
        self.assertEqual(0, payload.count(JS_BEFORE))
        self.assertEqual(1, payload.count(b'"com.mohamedrejeb.calf.ui.web.BrowserCookieWireAcceptanceTest.*"'))
        self.assertEqual(1, payload.count(JVM_ACTION))
        self.assertIn(b'cookieCommonJdkFocus == "common-jdk4"', payload)
        for forbidden in (b"@Ignore", b"enabled = false", b"setSrcDirs", b"excludePatterns.add"):
            self.assertNotIn(forbidden, payload)

    def test_complete_current_build_peels_to_exact_original_with_independent_roundtrip(self):
        payload = _build()
        self.assertEqual(AFTER, _identity(payload))
        original = outer._content_owner_source(BUILD, payload, ROOT, current=True)
        self.assertEqual(BEFORE, _identity(original))
        self.assertEqual(_independent_inverse(payload), original)
        rebuilt = original
        for before, after in FRAGMENTS:
            self.assertEqual(1, rebuilt.count(before))
            rebuilt = rebuilt.replace(before, after, 1)
        self.assertEqual(payload, rebuilt)
        self.assertEqual(original, outer._content_owner_source(BUILD, payload, ROOT, current=False))
        self.assertEqual(1, original.count(JVM_ACTION))
        self.assertEqual(1, payload.count(JVM_ACTION))

    def test_current_old_partial_duplicate_drift_and_wrong_types_refuse_history_is_uncertified(self):
        payload = _build()
        self.assertEqual(AFTER, _identity(payload))
        original = _independent_inverse(payload)
        self.assertEqual(BEFORE, _identity(original))
        first_partial = original.replace(IOS_BEFORE, IOS_AFTER, 1)
        second_partial = original.replace(JS_BEFORE, JS_AFTER, 1)
        duplicate = payload + JS_AFTER
        drift = payload.replace(b'"common-jdk4"', b'"common-jdk5"', 1)
        self.assertNotEqual(payload, drift)
        for data in (original, first_partial, second_partial, duplicate, drift, b"unknown"):
            with self.subTest(identity=_identity(data)):
                with self.assertRaises(ValueError):
                    outer._content_owner_source(BUILD, data, ROOT, current=True)
                self.assertIs(data, outer._content_owner_source(BUILD, data, ROOT, current=False))
        self.assertEqual(original, outer._content_owner_source(BUILD, payload, ROOT, current=False))
        for mode in (None, 0, 1, "current", b"current"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                outer._content_owner_source(BUILD, payload, ROOT, current=mode)
        for relative, data in ((None, payload), (Path(BUILD), payload), (BUILD, "source"), (BUILD, bytearray(payload))):
            with self.subTest(relative=relative, payload_type=type(data).__name__), self.assertRaises(ValueError):
                outer._content_owner_source(relative, data, ROOT, current=True)
        foreign = b"unlisted source is not certification"
        for mode in (True, False):
            self.assertIs(foreign, outer._content_owner_source("unlisted/build.gradle.kts", foreign, ROOT, current=mode))
