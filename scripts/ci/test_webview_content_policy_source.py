#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""NEW finite source controls. Passing these never substitutes for target compilation/native execution."""
from pathlib import Path
import ast
import hashlib
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "com.mohamedrejeb.calf.ui.web."
PREFIX = "calf-webview/src/{set}/kotlin/com/mohamedrejeb/calf/ui/web/"
CORE_METHODS = (
    "savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory",
    "documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved",
)
MOBILE_METHODS = CORE_METHODS + (
    "initialHeadersRedirectsAndSubresourcesMatchStateAndNavigatorPolicy",
    "relativeResourcesPreserveSupportedUnicodeEncoding",
)
OTHER_METHODS = CORE_METHODS + ("unsupportedHeadersAndBaseUrlRefuseBeforeNetworkForBothEntryPoints",)
CLASSES = {
    "IosWebViewContentPolicyAcceptanceTest": ("iosTest", MOBILE_METHODS),
    "AndroidWebViewContentPolicyAcceptanceTest": ("androidDeviceTest", MOBILE_METHODS),
    "DesktopWebViewContentPolicyAcceptanceTest": ("desktopTest", OTHER_METHODS),
    "BrowserWebViewContentPolicyAcceptanceTest": ("webTest", OTHER_METHODS),
}
ANDROID_SOURCE = "calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt"
ANDROID_PREIMAGE_SHA256 = "3d32645991c56f523087a3cf60a5aba5bbd567b9c9686768157cf7e01875b9f7"
ANDROID_PREIMAGE = "                this.pageTitle = it[pageTitleKey] as String?\n                this.lastLoadedUrl = it[lastLoadedUrlKey] as String?\n"
ANDROID_POSTIMAGE = "                // Native history is not a displayed document. Actual native callbacks\n                // repopulate metadata; never paint an old title/URL over a new blank view.\n"
UNCHANGED_INPUTS = {
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebViewContracts.kt": "4a87aa4a7a17252f817f8bdc9b8de8fcda62fb6093bfed624db0bc5c6875647f",
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt": "36891159184df5bcd03b724b81070698c878022796a5b563994c58591c763791",
    "calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt": "508c28c1fe336e01537e8ff62bd6249712c3d0eaa4fb591c89b1289f972b773f",
    "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt": "598bd8a18431882e68b96a28ff70f65c641bf2a1d36486aeff0aae12b999ae39",
    "calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt": "798710ff9b6ce32685e25f3cd13042d13e3568fc36d5e1438bf2e6df6991727f",
    "scripts/ci/ios_webview_request_fixture.py": "a5b4780ab39822a4ee261c07d434bacb9ce9fe72943c1924eeaddcbbeb1e17a7",
    "calf-webview/build.gradle.kts": "6e924d26f988f960ff828383a41901b79d7692d3eea6a07cb38230866b86e908",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeWebViewApplicationHost.kt": "0a98d085f6ce1b97392c0387e6dbbc77a3a41d0e9e3bc707ef1ced462c1bdb7f",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeWebViewApplicationHostTest.kt": "7fe27bd89424c033d4f2f319fe209d90af8156f2bef7ff3c4cf5da0e328c45c7",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeObjectIdentity.kt": "f8a5b13a21a0b3adcea5e5c27def54a03ad486574a552e6439a71852f0ba4b42",
    "calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewLifetimeDeviceTest.kt": "eae30dcbcb7b5df1fc3fb38384b9238e23acdd75d90b8f40c27eef31c8a6db23",
}


def source(klass):
    return (ROOT / (PREFIX.format(set=CLASSES[klass][0]) + klass + ".kt")).read_text()


def proposal():
    return json.loads((ROOT / "docs/testing/webview-content-policy-focuses.json").read_text())


class WebViewContentPolicySourceTest(unittest.TestCase):
    def test_android_saver_restoration_does_not_paint_saved_metadata_before_native_document(self):
        path = ROOT / "calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt"
        source = path.read_text()
        saver = source.split("actual val WebStateSaver: Saver<WebViewState, Any> = run {", 1)[1]
        restore = saver.split("restore = {", 1)[1]
        self.assertIn("WebViewState(WebContent.NavigatorOnly)", restore)
        self.assertIn("this.viewState = it[stateBundle] as Bundle?", restore)
        self.assertNotRegex(restore, r"this\.(?:pageTitle|lastLoadedUrl)\s*=\s*it\[",
            "The public saver restores stale title/final URL before any real remounted document witness")


class WebViewContentPolicyNewSourceTest(unittest.TestCase):
    """Source/inventory/ownership controls only; never claim target API/DOM compilation."""
    def test_exact_four_enabled_class_inventory_is_fourteen_authored_seventeen_target_cases(self):
        count = 0
        for klass, (_, methods) in CLASSES.items():
            text = source(klass)
            self.assertIn("package " + PACKAGE.rstrip("."), text)
            self.assertIn("class " + klass, text)
            self.assertEqual(list(methods), re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", text))
            self.assertNotRegex(text, r"@(Ignore|Disabled|IgnoredTest)\b")
            count += len(methods)
        plan = proposal()
        self.assertEqual((4, 14, 17), (len(CLASSES), count, sum(row["required_native_cases"] for row in plan["profiles"])))

    def test_proposal_has_exact_five_single_host_tasks_and_no_all_host_alias(self):
        expected = (
            ("webview-content-policy-linux", "desktop-linux-x64", "desktop", ":calf-webview:desktopTest", "DesktopWebViewContentPolicyAcceptanceTest"),
            ("webview-content-policy-android", "android-device-api35", "android-device", ":calf-webview:connectedAndroidDeviceTest", "AndroidWebViewContentPolicyAcceptanceTest"),
            ("webview-content-policy-js", "browser-js", "js", ":calf-webview:jsBrowserTest", "BrowserWebViewContentPolicyAcceptanceTest"),
            ("webview-content-policy-wasm", "browser-wasm", "wasm", ":calf-webview:wasmJsBrowserTest", "BrowserWebViewContentPolicyAcceptanceTest"),
            ("ios-webview-content-policy", "ios-iphone", "ios", ":calf-webview:iosSimulatorArm64ApplicationTest", "IosWebViewContentPolicyAcceptanceTest"),
        )
        plan = proposal()
        self.assertEqual("finite-source-proposal-not-runner-registration", plan["kind"])
        self.assertEqual([66, 73], plan["issues"])
        self.assertEqual("calf-webview", plan["module"])
        self.assertEqual(len(expected), len(plan["profiles"]))
        for row, (focus, slot, suite, task, klass) in zip(plan["profiles"], expected, strict=True):
            self.assertEqual((focus, focus, slot, suite, task, PACKAGE + klass),
                             tuple(row[key] for key in ("profile", "focus", "slot", "suite", "task", "classname")))
            self.assertEqual(list(CLASSES[klass][1]), row["methods"])
            self.assertEqual(PREFIX.format(set=CLASSES[klass][0]) + klass + ".kt", row["source"])
            self.assertEqual(len(row["methods"]), row["required_native_cases"])
            self.assertTrue(all((ROOT / path).is_file() for path in row["helpers"]))
        self.assertEqual(0, plan["compiler_executions_by_this_patch"])
        self.assertEqual(0, plan["native_executions_by_this_patch"])

    def test_android_production_diff_is_only_exact_metadata_restore_inverse(self):
        text = (ROOT / ANDROID_SOURCE).read_text()
        self.assertEqual(1, text.count(ANDROID_POSTIMAGE))
        reconstructed = text.replace(ANDROID_POSTIMAGE, ANDROID_PREIMAGE, 1).encode()
        self.assertEqual(ANDROID_PREIMAGE_SHA256, hashlib.sha256(reconstructed).hexdigest())
        for value in ('val pageTitleKey = "pagetitle"', 'val lastLoadedUrlKey = "lastloaded"', 'val stateBundle = "bundle"',
                      "view.saveState(saved)", "pageTitleKey to it.pageTitle", "lastLoadedUrlKey to it.lastLoadedUrl",
                      "this.viewState = it[stateBundle] as Bundle?"):
            self.assertIn(value, text)

    def test_owning_common_native_and_accepted_fixture_helper_bytes_remain_unchanged(self):
        from platform_recovery659_source_projection import current_source_before_platform_recovery659
        for path, digest in UNCHANGED_INPUTS.items():
            original = current_source_before_platform_recovery659(path, (ROOT / path).read_bytes())
            self.assertEqual(digest, hashlib.sha256(original).hexdigest(), path)

    def test_authored_native_tests_never_inject_callbacks_loading_title_url_errors_or_saver_results(self):
        forbidden = (r"\.(?:pageTitle|lastLoadedUrl|loadingState|errorsForCurrentRequest)\s*=(?!=)",
                     r"\.(?:onPageFinished|onReceivedError|didFinishNavigation|didFailProvisionalNavigation)\s*\(",
                     r"\b(?:WebResourceResponse|shouldInterceptRequest|WKURLSchemeHandler|NSURLProtocol)\b",
                     r"@(Ignore|Disabled|IgnoredTest)\b")
        for klass in CLASSES:
            text = source(klass)
            evaluator_owner = (ROOT / (PREFIX.format(set="desktopTest") + "DesktopContentPolicyWindow.kt")).read_text() if klass == "DesktopWebViewContentPolicyAcceptanceTest" else text
            for expression in forbidden:
                self.assertNotRegex(text + evaluator_owner, expression, klass)
            self.assertIn("WebStateSaver.restore", text)
            self.assertIn("WebStateSaver", text)
            self.assertIn("evaluateJavascriptResult", evaluator_owner)
            self.assertIn("document.title", text)
            self.assertIn("document.getElementById('policy-form').submit()", text)

    def test_non_android_restore_rows_remount_real_owners_and_keep_explicit_non_saveable_opt_out(self):
        for klass in ("IosWebViewContentPolicyAcceptanceTest", "DesktopWebViewContentPolicyAcceptanceTest", "BrowserWebViewContentPolicyAcceptanceTest"):
            text = source(klass)
            self.assertIn('listOf("url", "html", "navigator", "redirect", "null")', text)
            self.assertIn("assertNotSame(state, restored)", text)
            self.assertIn("assertNull(restored.pageTitle)", text)
            self.assertIn('if (row == "redirect") "final" else row', text)
            self.assertIn("assertBlank", text)
            self.assertIn('"html-recovery"', text)
            self.assertIn('"null-recovery"', text)
            self.assertIn('val sensitive = policyState(WebContent.NavigatorOnly)', text)
            self.assertIn('val fresh = policyState(WebContent.NavigatorOnly)', text)
            self.assertNotRegex(text, r"(?:restorableWebUrl|token)\s*\.\s*(?:contains|startsWith|endsWith)")

    def test_android_restoration_uses_real_parcel_bundle_and_dom_metadata_before_bounded_reload(self):
        text = source("AndroidWebViewContentPolicyAcceptanceTest")
        self.assertIn('listOf("html", "navigator", "redirect", "null")', text)
        for value in ("Parcel.obtain()", "parcel.writeValue(saved)", "parcel.readValue(WebViewState::class.java.classLoader)",
                      "parcel.recycle()", "copyBackForwardList().currentItem?.url", "fixture.navigator.reload()",
                      "assertMetadataMatchesRealDocument(current, fixture.navigator)",
                      "assertMetadataMatchesRealDocument(saved, fixture.navigator)", "document.location.href",
                      'page in minimum..(minimum + 1)', 'getValue("get") in minimum..(minimum + 1)'):
            self.assertIn(value, text)
        self.assertIn('exact(server, "url", "get" to 0)', text)
        self.assertIn('assertEquals(native.canGoBack(), navigator.canGoBack)', text)

    def test_mobile_main_header_counts_include_three_real_relative_gets_and_actual_redirect_parity(self):
        for klass in ("IosWebViewContentPolicyAcceptanceTest", "AndroidWebViewContentPolicyAcceptanceTest"):
            text = source(klass)
            for value in ('listOf("state", "navigator")', 'listOf("initial", "same", "cross")',
                          '"get" to if (route == "initial") 4 else 1', '"main_initial" to 1', '"main_authorization" to 1',
                          'document.getElementById(\'policy-link\').click()', 'observations["state-$route"]', 'observations["navigator-$route"]',
                          '"script_initial" to 0', '"script_authorization" to 0', '"style_initial" to 0', '"image_authorization" to 0'):
                self.assertIn(value, text)
            self.assertIn('assertTrue(value in 0..1)', text)

    def test_mobile_relative_resource_evidence_is_real_dom_computed_style_decoded_image_unicode_and_aliases(self):
        for klass in ("IosWebViewContentPolicyAcceptanceTest", "AndroidWebViewContentPolicyAcceptanceTest"):
            text = source(klass)
            for value in ('"utf8" to "utf-8", "utf8-alias" to "utf8"', "baseUrl =", "navigator.loadHtml",
                          "relative-resource-text", "getComputedStyle", "rgb(17, 34, 51)", "naturalWidth === 7", "naturalHeight === 9",
                          '"get" to 3, "page" to 0, "script" to 1, "style" to 1, "image" to 1'):
                self.assertIn(value, text)

    def test_desktop_browser_unsupported_both_entry_points_preserve_current_dom_with_zero_real_requests(self):
        from platform_recovery659_source_projection import current_source_before_platform_recovery659
        for klass in ("DesktopWebViewContentPolicyAcceptanceTest", "BrowserWebViewContentPolicyAcceptanceTest"):
            relative = PREFIX.format(set=CLASSES[klass][0]) + klass + ".kt"
            text = current_source_before_platform_recovery659(relative, (ROOT / relative).read_bytes()).decode()
            for value in ('listOf("state", "navigator")', '"additionalHttpHeaders"', '"baseUrl"', 'it.code == -2',
                          '"$entry-headers", "get" to 0', '"$entry-base", "get" to 0, "script" to 0, "style" to 0, "image" to 0',
                          'listOf("utf-8", "utf8")', 'assertSame(native, state.'):
                self.assertIn(value, text)
            self.assertIn("outerHTML", text)

    def test_jvm_transport_helpers_are_byte_identical_finite_owned_sockets_and_main_only_authentication(self):
        name = "OwnedWebViewContentPolicyHttpFixture.kt"
        desktop = (ROOT / (PREFIX.format(set="desktopTest") + name)).read_bytes()
        android = (ROOT / (PREFIX.format(set="androidDeviceTest") + name)).read_bytes()
        self.assertEqual(desktop, android)
        text = desktop.decode()
        self.assertNotIn("@Test", text)
        for value in ('InetAddress.getByName("127.0.0.1")', "repeat(2)", "ArrayBlockingQueue(16)",
                      "ThreadPoolExecutor(8, 8", "connections.incrementAndGet() <= 512", "raw.size() < 8192",
                      'size in 0..512', 'count.getValue("get") + count.getValue("post") < 12',
                      'asset == null && method == "headers" && stage.endsWith("-initial")', "403",
                      "sockets.toList().forEach(::closeSocket)", "workers.awaitTermination(4, TimeUnit.SECONDS)", "assertHealthy()"):
            self.assertIn(value, text)
        counter_block = text.split("val counters = listOf(", 1)[1].split("fun create(", 1)[0]
        self.assertEqual(20, len(re.findall(r'"([a-z_]+)"', counter_block)))

    def test_python_native_transport_binds_source_actual_process_and_private_environment_without_system_mutation(self):
        text = (ROOT / "scripts/ci/webview_content_policy_fixture.py").read_text()
        tree = ast.parse(text)
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        self.assertFalse(set(imports) & {"subprocess", "os", "ios_ui_application", "ios_webview_request_fixture", "library_tests"})
        for value in ("def bind_application(", "def launch_environment(", "def validate_receipt(", "self.methods != IOS_METHODS",
                      "self._process not in (None, pid)", '"SIMCTL_CHILD_" + name', "environment = dict(inherited)",
                      "complete_native_stages(document[\"methods\"])", "process_sha256(native_pid)",
                      'listener.bind(("127.0.0.1", 0))', '"native_helper_sha256"', '"owned_workers_terminated"',
                      "independent(close_listener)", "independent(close_workers)"):
            self.assertIn(value, text)
        self.assertNotRegex(text, r"(?:os\.environ|sys\.environ)\s*(?:\[|\.update)")

    def test_browser_receipts_require_real_origin_source_trust_and_actual_public_owner_disconnect_cleanup(self):
        helper = (ROOT / (PREFIX.format(set="webTest") + "BrowserContentPolicyFixture.kt")).read_text()
        for value in ("message.source === native.contentWindow", "message.origin == origin", "message.isTrusted",
                      'window.location.hostname in listOf("localhost", "127.0.0.1")', "own.dispose()",
                      'window.removeEventListener("message", listener)', "native.remove()"):
            self.assertIn(value, helper)
        text = source("BrowserWebViewContentPolicyAcceptanceTest")
        self.assertIn("state.iframe == null && state.owner == null && native?.isConnected != true", text)
        self.assertIn("BrowserSandboxPolicy.Trusted", text)
        middleware = (ROOT / "calf-webview/karma.config.d/nativecmpkit-content-policy-fixture.js").read_text()
        for value in ("Object.prototype.hasOwnProperty.call", "!owns(stages, method)", "!owns(session.rows, action)",
                      "owns(session.rows, extra)", "session.pending.size >= 16", "++session.connections > 512", "counts.get + counts.post >= 12",
                      "lease.response.destroy()", "Promise.all(pending.map(lease => lease.closed))", ", 2000)",
                      "window.location.origin)"):
            self.assertIn(value, middleware)
        self.assertNotRegex(middleware, r"(?:server|process)\.(?:close|kill|exit)\s*\(")

    def test_documentation_separates_original_criteria_source_red_transport_controls_and_pending_native_acceptance(self):
        text = (ROOT / "docs/testing/webview-content-policy.md").read_text()
        for value in ("source preparation", "14 methods", "17 executions", "stale-metadata source hazard",
                      "not a failure observed on a device", "transport ownership only", "protocol.observed_launch_pid",
                      "No OS process-death execution", "not yet registered", "at least 8 GiB free",
                      "including", "not an observed provider fact", "Unchanged"):
            if value == "Unchanged":
                self.assertIn("unchanged", text)
            else:
                self.assertIn(value, text)
        self.assertIn(proposal()["important_affected_existing_saver_seam"].split(PACKAGE, 1)[1], text)


if __name__ == "__main__":
    unittest.main()
