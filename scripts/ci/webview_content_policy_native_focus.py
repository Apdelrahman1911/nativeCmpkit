# SPDX-License-Identifier: Apache-2.0
"""Five exact WebView source/selector/XML profiles, never compiler/native acceptance.

The author's four classes/fourteen bodies and all older native inputs stay authored.
Android adds one zero-test lossless JUnit Filter for NEW4 plus only affected saver1.
"""
from __future__ import annotations

import hashlib
import re

from ios_popover_anchor_plan import _ordinary_bytes

SOURCE = "scripts/ci/webview_content_policy_native_focus.py"
SPEC_RELATIVE = "scripts/ci/fixtures/webview-content-policy-routing-source-inverse.json"
MODULE = "calf-webview"
DESKTOP_FOCUS = "webview-content-policy-linux"
ANDROID_FOCUS = "webview-content-policy-android"
JS_FOCUS = "webview-content-policy-js"
WASM_FOCUS = "webview-content-policy-wasm"
IOS_FOCUS = "ios-webview-content-policy"
FOCUSES = (DESKTOP_FOCUS, ANDROID_FOCUS, JS_FOCUS, WASM_FOCUS, IOS_FOCUS)
CONTRACT_FIELD = "webview_content_policy_source_contract"
ANDROID_FILTER_CLASS = "com.mohamedrejeb.calf.ui.web.AndroidContentPolicyVerificationFilter"
ANDROID_FILTER_SOURCE = "calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidContentPolicyVerificationFilter.kt"
ANDROID_AFFECTED_CLASS = "com.mohamedrejeb.calf.ui.web.AndroidWebViewLifetimeDeviceTest"
ANDROID_AFFECTED_METHOD = "retainedStateReleasesRepeatedRealActivitiesAndViewsAndRestoresSerializedNativeState"
ANDROID_AFFECTED_SOURCE = "calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewLifetimeDeviceTest.kt"
ANDROID_NETWORK_SOURCES = (
    "calf-webview/src/androidDeviceTest/AndroidManifest.xml",
    "calf-webview/src/androidDeviceTest/res/xml/nativecmpkit_webview_test_network_security.xml",
)
ANDROID_SAVER_SOURCE = "calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt"
IOS_HOST_CONTROL = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeWebViewApplicationHostTest.kt"
IOS_FIXTURE = "scripts/ci/webview_content_policy_fixture.py"
IOS_HELPER = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosContentPolicyFixture.kt"
_METHOD = re.compile(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)")
_DISABLED = re.compile(r"@(Ignore|Disabled|IgnoredTest)\b")

SPECS = {'webview-content-policy-linux': {'profile': 'webview-content-policy-linux',
                                  'focus': 'webview-content-policy-linux',
                                  'slot': 'desktop-linux-x64',
                                  'suite': 'desktop',
                                  'task': ':calf-webview:desktopTest',
                                  'classname': 'com.mohamedrejeb.calf.ui.web.DesktopWebViewContentPolicyAcceptanceTest',
                                  'source': 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewContentPolicyAcceptanceTest.kt',
                                  'methods': ('savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory',
                                              'documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved',
                                              'unsupportedHeadersAndBaseUrlRefuseBeforeNetworkForBothEntryPoints'),
                                  'helpers': ('calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopContentPolicyWindow.kt',
                                              'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedWebViewContentPolicyHttpFixture.kt'),
                                  'report_directory': 'calf-webview/build/test-results/desktopTest'},
 'webview-content-policy-android': {'profile': 'webview-content-policy-android',
                                    'focus': 'webview-content-policy-android',
                                    'slot': 'android-device-api35',
                                    'suite': 'android-device',
                                    'task': ':calf-webview:connectedAndroidDeviceTest',
                                    'classname': 'com.mohamedrejeb.calf.ui.web.AndroidWebViewContentPolicyAcceptanceTest',
                                    'source': 'calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewContentPolicyAcceptanceTest.kt',
                                    'methods': ('savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory',
                                                'documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved',
                                                'initialHeadersRedirectsAndSubresourcesMatchStateAndNavigatorPolicy',
                                                'relativeResourcesPreserveSupportedUnicodeEncoding'),
                                    'helpers': ('calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedWebViewContentPolicyHttpFixture.kt',
                                                'calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewLifetimeDeviceTest.kt'),
                                    'report_directory': 'calf-webview/build/outputs/androidTest-results/connected/androidMain'},
 'webview-content-policy-js': {'profile': 'webview-content-policy-js',
                               'focus': 'webview-content-policy-js',
                               'slot': 'browser-js',
                               'suite': 'js',
                               'task': ':calf-webview:jsBrowserTest',
                               'classname': 'com.mohamedrejeb.calf.ui.web.BrowserWebViewContentPolicyAcceptanceTest',
                               'source': 'calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserWebViewContentPolicyAcceptanceTest.kt',
                               'methods': ('savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory',
                                           'documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved',
                                           'unsupportedHeadersAndBaseUrlRefuseBeforeNetworkForBothEntryPoints'),
                               'helpers': ('calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserContentPolicyFixture.kt',
                                           'calf-webview/karma.config.d/nativecmpkit-content-policy-fixture.js'),
                               'report_directory': 'calf-webview/build/test-results/jsBrowserTest'},
 'webview-content-policy-wasm': {'profile': 'webview-content-policy-wasm',
                                 'focus': 'webview-content-policy-wasm',
                                 'slot': 'browser-wasm',
                                 'suite': 'wasm',
                                 'task': ':calf-webview:wasmJsBrowserTest',
                                 'classname': 'com.mohamedrejeb.calf.ui.web.BrowserWebViewContentPolicyAcceptanceTest',
                                 'source': 'calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserWebViewContentPolicyAcceptanceTest.kt',
                                 'methods': ('savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory',
                                             'documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved',
                                             'unsupportedHeadersAndBaseUrlRefuseBeforeNetworkForBothEntryPoints'),
                                 'helpers': ('calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserContentPolicyFixture.kt',
                                             'calf-webview/karma.config.d/nativecmpkit-content-policy-fixture.js'),
                                 'report_directory': 'calf-webview/build/test-results/wasmJsBrowserTest'},
 'ios-webview-content-policy': {'profile': 'ios-webview-content-policy',
                                'focus': 'ios-webview-content-policy',
                                'slot': 'ios-iphone',
                                'suite': 'ios',
                                'task': ':calf-webview:iosSimulatorArm64ApplicationTest',
                                'classname': 'com.mohamedrejeb.calf.ui.web.IosWebViewContentPolicyAcceptanceTest',
                                'source': 'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewContentPolicyAcceptanceTest.kt',
                                'methods': ('savedRemainingStatesRemountWithoutBlankTitleOrFalseHistory',
                                            'documentedGetReplayAndNonSaveablePostOneTimeOptOutAreObserved',
                                            'initialHeadersRedirectsAndSubresourcesMatchStateAndNavigatorPolicy',
                                            'relativeResourcesPreserveSupportedUnicodeEncoding'),
                                'helpers': ('calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosContentPolicyFixture.kt',
                                            'scripts/ci/webview_content_policy_fixture.py',
                                            'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeWebViewApplicationHost.kt',
                                            'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeObjectIdentity.kt'),
                                'report_directory': 'calf-webview/build/test-results/iosSimulatorArm64ApplicationTest'}}

SOURCE_SHA256 = {'calf-webview/karma.config.d/nativecmpkit-content-policy-fixture.js': 'c78874d7622fa8a507d68735305a989a5fc21b0a072098532473e6c586212d81',
 'calf-webview/src/androidDeviceTest/AndroidManifest.xml': '4bb4a2e939562f0ca2f2973ba2438c52ccdd54be1eb500e8afa78d5a5e1b1966',
 'calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidContentPolicyVerificationFilter.kt': '592151fdea1302aece7c93f8f84d5287af9c68649698df76e6e8bc62d55ca47d',
 'calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewContentPolicyAcceptanceTest.kt': 'd292df9838fd7a208d97db9adf69d1b61466b0a5848955bf5e989f2467ab3564',
 'calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewLifetimeDeviceTest.kt': 'eae30dcbcb7b5df1fc3fb38384b9238e23acdd75d90b8f40c27eef31c8a6db23',
 'calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedWebViewContentPolicyHttpFixture.kt': '6b3b15646abec07088135e0de306c10c7fd577eb20a73fc1b3c2ba21df8b8499',
 'calf-webview/src/androidDeviceTest/res/xml/nativecmpkit_webview_test_network_security.xml': 'd41572dbbaf67ec740c28ed69a8c5fce4223329c4c96d726f1df9a08f95de71d',
 'calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt': 'e7f3e127d3f3293d21f1bc2d84d9dd6761d26f65b1b77102237521197bb045a2',
 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopContentPolicyWindow.kt': 'e90b00f604cc16db8f26a0b8210d0fb815c0faa1af9d1d5edc11aca8ef9eb007',
 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewContentPolicyAcceptanceTest.kt': '79601573fea41ab8d1a78258b2de74153383a2582d9eac031deb6cfbe7e2c683',
 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/OwnedWebViewContentPolicyHttpFixture.kt': '6b3b15646abec07088135e0de306c10c7fd577eb20a73fc1b3c2ba21df8b8499',
 'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosContentPolicyFixture.kt': 'fcb6ab01848cd2b4caaa4ac2274aab6062e16cc3b29103e6da4f748aabcac7c4',
 'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewContentPolicyAcceptanceTest.kt': '36713f1ccec7c2b19ed9abba86dd502f4108485889f7e8bb0719a735f05aead9',
 'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeObjectIdentity.kt': 'f8a5b13a21a0b3adcea5e5c27def54a03ad486574a552e6439a71852f0ba4b42',
 'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeWebViewApplicationHost.kt': '0a98d085f6ce1b97392c0387e6dbbc77a3a41d0e9e3bc707ef1ced462c1bdb7f',
 'calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeWebViewApplicationHostTest.kt': '7fe27bd89424c033d4f2f319fe209d90af8156f2bef7ff3c4cf5da0e328c45c7',
 'calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserContentPolicyFixture.kt': '94e13cf71742536efa828c737861c94063b3a35b8df0ceb9d37bad7f7e80f749',
 'calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserWebViewContentPolicyAcceptanceTest.kt': 'e31efb65ee40ba0f22c6e5c3f7dd39ce88356d35cfa7e469824f28a325e49d2d',
 'scripts/ci/webview_content_policy_fixture.py': '7ef8dfd4e8eee68a8d584e91d3ea231daa46b15a68f36cf762ee4409c8b4d571'}


def spec(focus: str) -> dict:
    if type(focus) is not str or focus not in FOCUSES:
        raise ValueError("Only one of five exact content-policy focuses is allowed")
    return SPECS[focus]


def allowed(suite: str, modules: tuple[str, ...] | None, focus: str) -> bool:
    return (type(focus) is str and focus in FOCUSES and suite == spec(focus)["suite"] and modules == (MODULE,))


def groups(focus: str) -> tuple[dict, ...]:
    row = spec(focus)
    selected = ({"classname": row["classname"], "source": row["source"], "methods": row["methods"]},)
    if focus == ANDROID_FOCUS:
        selected += ({"classname": ANDROID_AFFECTED_CLASS, "source": ANDROID_AFFECTED_SOURCE,
                      "methods": (ANDROID_AFFECTED_METHOD,)},)
    return selected


def identities(focus: str) -> list[dict]:
    row = spec(focus)
    prefix = "iosSimulatorArm64ApplicationTest." if focus == IOS_FOCUS else ""
    suffix = "[iosSimulatorArm64]" if focus == IOS_FOCUS else "[desktop]" if focus == DESKTOP_FOCUS else ""
    return [{"classname": prefix + group["classname"], "name": method + suffix}
            for group in groups(focus) for method in group["methods"]]


def selector(focus: str) -> str:
    row = spec(focus)
    if focus == ANDROID_FOCUS:
        return ANDROID_FILTER_CLASS
    if focus == IOS_FOCUS:
        return ",".join(row["classname"] + "." + method for method in row["methods"])
    return row["classname"]


def sources(focus: str) -> tuple[str, ...]:
    row = spec(focus)
    selected = {row["source"], *row["helpers"]}
    if focus == ANDROID_FOCUS:
        selected.update((*ANDROID_NETWORK_SOURCES, ANDROID_SAVER_SOURCE, ANDROID_FILTER_SOURCE))
    if focus == IOS_FOCUS:
        selected.add(IOS_HOST_CONTROL)
    return tuple(sorted(selected))


def validate_sources(root, focus: str) -> bool:
    row = spec(focus)
    payload = {name: _ordinary_bytes(root, name)[0] for name in sources(focus)}
    for name, raw in payload.items():
        if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256[name]:
            raise ValueError("Exact content-policy native/helper/source image changed: " + name)
    source = payload[row["source"]].decode("utf-8")
    package, classname = row["classname"].rsplit(".", 1)
    if (_METHOD.findall(source) != list(row["methods"]) or _DISABLED.search(source) or
            not re.search(r"(?m)^package\s+" + re.escape(package) + r"\s*$", source) or
            not re.search(r"\bclass\s+" + re.escape(classname) + r"\s*\{", source)):
        raise ValueError("Exact enabled content-policy native declarations are required")
    if focus == ANDROID_FOCUS:
        helper = payload[ANDROID_FILTER_SOURCE].decode("utf-8")
        if (_METHOD.search(helper) or _DISABLED.search(helper) or
                "class AndroidContentPolicyVerificationFilter : Filter()" not in helper):
            raise ValueError("One exact public no-arg zero-test JUnit Filter is required")
    return True


def _contract(focus: str) -> dict:
    import webview_content_policy_source_projection as history
    import webview_current_contract667_source_projection as current
    row = spec(focus)
    pins = {name: SOURCE_SHA256[name] for name in sources(focus)}
    pins.update(current.current_contract_hashes())
    pins[SPEC_RELATIVE] = history.SPEC_SHA256
    return {"schema_version": 1, "focus": focus, "module": MODULE, "suite": row["suite"],
            "task": row["task"], "selected_testcases": identities(focus), "source_hashes": pins,
            "new_methods": len(row["methods"]), "affected_existing_methods": int(focus == ANDROID_FOCUS),
            "compiler_executions_attested": 0, "native_executions_attested": 0}


def source_contract(root, focus: str) -> dict:
    validate_sources(root, focus)
    wanted = _contract(focus)
    for name, digest in wanted["source_hashes"].items():
        if hashlib.sha256(_ordinary_bytes(root, name)[0]).hexdigest() != digest:
            raise ValueError("Current content-policy owner/native manifest identity changed: " + name)
    return wanted


def configure_item(root, item: dict, focus: str) -> None:
    row = spec(focus)
    contract = source_contract(root, focus)
    item.update(test_filter=selector(focus), required_testcases=identities(focus), required_original_xml=1)
    item[CONTRACT_FIELD] = contract
    # Normal Kotlin source-set inheritance is retained, not narrowed or rewritten.
    item["test_source_files"] = sorted(set(item["test_source_files"]) | set(contract["source_hashes"]))
    if focus == ANDROID_FOCUS:
        item.update(test_filter_argument="filter", verification_api_level=35,
                    native_fixture_paths=[*ANDROID_NETWORK_SOURCES, row["helpers"][0],
                                          ANDROID_AFFECTED_SOURCE, ANDROID_FILTER_SOURCE])
    elif focus in (JS_FOCUS, WASM_FOCUS):
        item["browser_http_fixture"] = row["helpers"][1]


def validate_plan(test_plan: dict) -> bool:
    focus = test_plan.get("explicit_test_focus")
    row = spec(focus)
    expected = test_plan.get("expected")
    if (type(expected) is not list or len(expected) != 1 or test_plan.get("suite") != row["suite"] or
            test_plan.get("explicit_module_subset") != [MODULE] or test_plan.get("complete_suite_requested") is not False):
        raise ValueError("Content policy requires one exact finite suite and calf-webview module")
    item = expected[0]; contract = item.get(CONTRACT_FIELD)
    wanted = _contract(focus)
    if (item.get("module") != MODULE or item.get("project") != ":calf-webview" or
            item.get("task") != row["task"] or item.get("report_directory") != row["report_directory"] or
            item.get("test_filter") != selector(focus) or item.get("required_testcases") != identities(focus) or
            type(item.get("required_original_xml")) is not int or item["required_original_xml"] != 1 or
            contract != wanted or type(contract.get("schema_version")) is not int or
            any(type(contract.get(key)) is not int for key in
                ("new_methods", "affected_existing_methods", "compiler_executions_attested", "native_executions_attested")) or
            not set(wanted["source_hashes"]) <= set(item.get("test_source_files", []))):
        raise ValueError("Content policy requires exact task, class, methods, sources and original XML identity")
    if focus == ANDROID_FOCUS:
        if (item.get("test_filter_argument") != "filter" or item.get("test_exclusion_annotation") is not None or
                type(item.get("verification_api_level")) is not int or item["verification_api_level"] != 35 or
                item.get("agp_declared_xml_directory") != "calf-webview/build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest" or
                item.get("utp_results_directory") != row["report_directory"] or
                item.get("native_fixture_paths") != [*ANDROID_NETWORK_SOURCES, row["helpers"][0],
                                                    ANDROID_AFFECTED_SOURCE, ANDROID_FILTER_SOURCE]):
            raise ValueError("Android content policy requires exact lossless filter and API35 native5 report")
    elif focus == IOS_FOCUS:
        if (item.get("native_test_host") != "genuine-uikit-application" or
                item.get("test_filter_argument") is not None or item.get("test_exclusion_annotation") is not None):
            raise ValueError("iOS content policy requires the actual owned UIKit application")
    elif (item.get("native_test_host") is not None or item.get("test_filter_argument") is not None or
          item.get("test_exclusion_annotation") is not None):
        raise ValueError("Content-policy host cannot be replaced by a foreign native application")
    if focus in (JS_FOCUS, WASM_FOCUS) and item.get("browser_http_fixture") != row["helpers"][1]:
        raise ValueError("Browser content policy requires its own unchanged Karma fixture")
    return True


def validate_host(focus: str, system: str, machine: str) -> None:
    spec(focus)
    if focus == DESKTOP_FOCUS and (system != "Linux" or machine.lower() not in ("x86_64", "amd64", "x64")):
        raise ValueError("Desktop content policy is registered only for Linux x64")


def case_inventory(focus: str, cases: list[dict]) -> bool:
    row = spec(focus)
    if type(cases) is not list or len(cases) != len(identities(focus)) or any(type(case) is not dict for case in cases):
        return False
    if focus in (JS_FOCUS, WASM_FOCUS):
        task = row["task"].rsplit(":", 1)[1]
        target = "js" if focus == JS_FOCUS else "wasmJs"
        methods = []
        for case in cases:
            name = case.get("name")
            if type(name) is not str or case.get("classname") != task + "." + row["classname"]:
                return False
            method, separator, suffix = name.partition("[")
            if not separator or not re.fullmatch(re.escape(target) + r", browser, [^\[\]\r\n]+\]", suffix):
                return False
            methods.append(method)
        return len(set(methods)) == len(row["methods"]) and set(methods) == set(row["methods"])
    if any(type(case.get("classname")) is not str or type(case.get("name")) is not str for case in cases):
        return False
    return {(case.get("classname"), case.get("name")) for case in cases} == {
        (case["classname"], case["name"]) for case in identities(focus)}


def scope(focus: str) -> str:
    row = spec(focus)
    return (f"Only NEW{len(row['methods'])}" + (" plus exactly the affected existing Android saver native-history/Reload method" if focus == ANDROID_FOCUS else "") +
            "; actual target-native DOM/document/wire/history observations and one fresh exact original task XML remain mandatory. "
            "iOS separately requires nonce/process/install/source-bound localhost fixture, real Worker/protocol/runtime/binary agreement and independent cleanup. "
            "All other accepted native bodies remain authored and unselected. No unchanged replay, full ios/all admission, issue closure, API-ABI, consumer, dependency, security or release/publication certification.")
