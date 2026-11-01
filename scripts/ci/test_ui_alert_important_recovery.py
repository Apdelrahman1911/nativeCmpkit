"""NEW tooling controls; PRIVATE/UNRUN until the lead explicitly executes them.

UIKit/view/throwable/console objects and XML below are synthetic. The bounded
diagnostic model is an exact-source-pinned specification, not execution of
Kotlin, native main dispatch, Foundation suppression or UIKit accessibility.
Real owning Python selection/protocol/collector functions are exercised, but no
accepted test module/body, Gradle, SDK, native payload or network is invoked.
"""
from __future__ import annotations

from collections import Counter, deque
from contextlib import ExitStack
import copy
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

ROOT = Path(os.environ.get("NATIVECMPKIT_ALERT_NEW_CONTROL_TREE", Path(__file__).resolve().parents[2])).resolve()
EXPECTED_SOURCE_SHA256 = {'.github/workflows/gradle.yml': 'edfc2c793ecb47ace202e4e3d271a9dc0c4b399a144fd7f79d766c129f84dae1', 'calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateYearPolicyImportantScenarios.kt': 'a2a13f0dad090ac0b39274911b56f59e6fa7c6a0f11f70ed3e7eea4a0edad5ce', 'calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/MaterialDateYearPolicyImportantTest.kt': 'd5483e084cc528b2e60358e4fa91caafa18a58abc1dc7b21b29d33c4f098f3dc', 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/NativeDateYearPolicyImportantTest.kt': 'e5fb8aa72e6ecdd9f9c71f654f3ee97bbbe6261dd6b8ef0dc681a7672215a066', 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativeAlertImportantRegressionTest.kt': '50ed7c6b1f20aad81d504e528e1bf0a9daf4312e179836559a1ac58ec9d064a5', 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt': 'd3cccfc654399598abf00e04d6f40529a3802e9488448afde120da8180932df0', 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt': '4eb8b1c7cc43de5bc39f0d36ec818d7216054e0b6b262b936826b4efe51fbc65', 'scripts/ci/ios_ui_application.py': '42056448d9f023ab3c136d164956350900117a30610457c91ee0b16de85f3244', 'scripts/ci/library_tests.py': '6b04a654fcd19076ad03ea53340400a544cca398eef5e3bd1c10ba5660dd7cab', 'scripts/ci/test_ui_alert_year_important_focus.py': '9bb04e07fc6f032183c3618c28ab61dcbf3ba94030fee2a9e9e5460b2e83d906', 'scripts/ci/workflow_matrix.py': '5d65440ff6b274866b5ed4c7909a04131a6af821185062aca867f5c65223ba5a'}
NATIVE = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativeAlertImportantRegressionTest.kt"
HOST = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"
PARSER = "scripts/ci/ios_ui_application.py"
MARK = "private fun NativeApplicationUiTest.activateImportantNativeAction"
TIMEOUT = "Timed out awaiting native predicate; actual application state: "
PREFIX = "NATIVECMPKIT_ALERT_ACTION_GATE_TIMEOUT"
PROFILE = "ios-alert-important-recovery"
FOCUS = "ui-native-alert-important-recovery"
ORIGINAL_PREFIX_SHA256 = "5ad33e1836d1e78243e73e2134765922dceaac5786bd13370c49f8865cffc282"
ORIGINAL_GATE_SHA256 = "e52b2169f030cba03b817ca73c245cab47996b0c7a13d3b2a010517944829708"
ORIGINAL_ACTIVATION_SHA256 = "0128f6fffb68a509c85fc9cd3ded10cd39497a7d0c291d54a91cc4e48c99e37f"
CANDIDATE_SAMPLE_SHA256 = "4c0d8d129b78105192fbdce616b210ffdbcc2b23e22916711edcfaad79080af3"
CANDIDATE_DIAGNOSTIC_SHA256 = "c698b02054d7ab245f3ab26a6676345c0fd946059447b94e710627954ae6c350"
CANDIDATE_CATCH_SHA256 = "38ab098864242d51d188e9a7a8dfb2c6ff7374671fe9ae04bec381baf7a4b3d7"
FORBIDDEN_ACTIONS = []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def forbid(*args, **kwargs):
    FORBIDDEN_ACTIONS.append("forbidden-process-network-or-native-action")
    raise AssertionError("No process/network/native action is admitted by these controls")


def guards(stack, *, sockets=True):
    groups = [(subprocess, ("Popen", "run", "check_call", "check_output")),
              (os, ("system", "kill", "killpg")),
              (socket, ("create_connection", "getaddrinfo"))]
    if sockets:
        groups.append((socket, ("socket",)))
    for module, names in groups:
        for name in names:
            stack.enter_context(patch.object(module, name, forbid))


# Exact historical UIKit153 guard maintenance for the separately reviewed Share addendum.
# Whole-source hashes above stay historical. Only these exact authored current images may
# reconstruct them; no accepted-body replay, old-source fallback or arbitrary combined drift.
SHARE_ALERT153_REBASE = {'scripts/ci/library_tests.py': {'original153_sha256': '6b04a654fcd19076ad03ea53340400a544cca398eef5e3bd1c10ba5660dd7cab', 'share_composed_sha256': '072e2163fe2653a14891a7eccc69e1430998ef3cf03e3e062255483250015585', 'fragments': [{'id': 'share-host-sources', 'before': 'IOS_APPLICATION_HOST_SOURCES = {"calf-ui": IOS_APPLICATION_SOURCES,\n', 'after': 'IOS_SHARE_APPLICATION_SOURCES = (\n    "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/internal/NativeShareApplicationHost.kt",\n    "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/internal/NativeShareApplicationHostTest.kt",\n    "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/internal/NativeObjectIdentity.kt",\n)\nIOS_APPLICATION_HOST_SOURCES = {"calf-ui": IOS_APPLICATION_SOURCES,\n', 'before_fragment_sha256': '9dc42b0e68b690b678c63b7d94d4a767c4ba21299824aed55a7079b203a297d7', 'after_fragment_sha256': 'c0b06304c9fa9e8fbdfacfd23790e4fb9eaecf967d1c99a7a322d470067592d7'}, {'id': 'share-host-map-entry', 'before': '                                "calf-file-picker": IOS_PICKER_APPLICATION_SOURCES}\n', 'after': '                                "calf-file-picker": IOS_PICKER_APPLICATION_SOURCES,\n                                "calf-share": IOS_SHARE_APPLICATION_SOURCES}\n', 'before_fragment_sha256': '2aac8f9b2fb30c2008e6e6b9b7bd57ed969108d7c944821b87a31c357573a296', 'after_fragment_sha256': '36fbf6e23b3c3e194c7798d3c2ab8048e7b36113c954ca445977f8fd48581f3e'}, {'id': 'share-finite-13-focus', 'before': 'IOS_WEBVIEW_LIFECYCLE_FOCUS = "webview-ios-native-lifecycle"\n', 'after': '# New owning Share presentation/disposal regressions only. The sample is not a library host;\n# no accepted picker/provider/IO/browser or other-platform methods are selected by this focus.\nIOS_SHARE_PRESENTATION_FOCUS = "share-ios-presentation-disposal"\nIOS_SHARE_PRESENTATION_CLASS = "com.mohamedrejeb.calf.share.IosSharePresentationOwnershipTest"\nIOS_SHARE_PRESENTATION_SOURCE = "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosSharePresentationOwnershipTest.kt"\nIOS_SHARE_PRESENTATION_METHODS = (\n    "realAnimatedShareDisposalWaitsForNativePresentationAndDismissalBeforeLeaseRelease",\n    "deferredNativeSharePresentationRetainsDisposedRequestWhileBothLinksAreNil",\n    "disposalAfterRealPresentationClosesOneRequestAndSuppressesLateActivityCompletion",\n    "disposedPublicShareLaunchersCalledFromDefaultAndIoCannotRestartNativeWork",\n    "publicRememberedShareMainDefaultIoReentryAndDisposalUseCurrentCallbacks",\n)\nIOS_SHARE_REQUEST_CONTROL_CLASS = "com.mohamedrejeb.calf.share.IosShareRequestTest"\nIOS_SHARE_REQUEST_CONTROL_SOURCE = "calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosShareRequestTest.kt"\nIOS_SHARE_REQUEST_CONTROL_METHODS = (\n    "preparedCancellationReleasesOnlyTheNeverPresentedRequestOnce",\n    "nilNativeLinksDuringControlledPresentationCannotReleaseOrDismissTheRequest",\n    "repeatedCancellationDuringDismissalCannotIssueOrCompleteCleanupTwice",\n    "releasedRequestIgnoresLateCompletionsAndThrowingOwnerNotificationCannotRepeatCleanup",\n)\nUI_APPLICATION_FOCUS_SPECS[IOS_SHARE_PRESENTATION_FOCUS] = {\n    "module": "calf-share",\n    "groups": (\n        {"classname": "com.mohamedrejeb.calf.share.internal.NativeShareApplicationHostTest",\n         "source": IOS_SHARE_APPLICATION_SOURCES[1],\n         "methods": ("generatedBodyRunsOnOwnedWorkerWithActiveAttachedApplication",\n                     "nativeObjectIdentityRejectsNullAndEqualButDistinctObjects",\n                     "repeatedRealComposeRootsRecomposeDisposeAndRestoreTheirOwner",\n                     "failedAssertionPreservesCauseAndReleasesRealCompositionAndPresenter")},\n        {"classname": IOS_SHARE_REQUEST_CONTROL_CLASS, "source": IOS_SHARE_REQUEST_CONTROL_SOURCE,\n         "methods": IOS_SHARE_REQUEST_CONTROL_METHODS},\n        {"classname": IOS_SHARE_PRESENTATION_CLASS, "source": IOS_SHARE_PRESENTATION_SOURCE,\n         "methods": IOS_SHARE_PRESENTATION_METHODS},\n    ),\n    "scope": "Thirteen new calf-share library application methods only: four owning UIApplication/Worker/root/cleanup fixtures, four explicitly controlled Request transitions and five real UIKit/public ShareLauncher ownership regressions. Actual animated/deferred presentation and real dismissal callbacks own disposal cleanup; nil backlinks/timers do not. Main/Default/IO dispatch, current callbacks, reentry and stale/disposed suppression use genuine Compose/native controllers but controlled activity-terminal inputs, not user/recipient completion. Real sandbox-file scope objects execute, with no assumed successful security-scope start, bookmark grant, delayed/cross-process recipient access or original native occurrence. Sample saver tests are separate and never library evidence. No accepted picker/provider/IO/browser/other-host replay, #88/#81/#48/#100 closure, Main Thread Checker/concurrency-suite, physical/minimum/iPad/consumer/API-ABI/dependency/security/readiness/publishing certification.",\n}\n\nIOS_SHARE_APPLICATION_REQUIRED_GROUPS = UI_APPLICATION_FOCUS_SPECS[IOS_SHARE_PRESENTATION_FOCUS]["groups"]\n\nIOS_WEBVIEW_LIFECYCLE_FOCUS = "webview-ios-native-lifecycle"\n', 'before_fragment_sha256': 'ef92f827158e592925929483f4d003905755fec43100956f47397976322f7e43', 'after_fragment_sha256': '5b052105139bb81f31d73e53a3afb79902bc19d1519c22164a4908abc52e027e'}, {'id': 'share-enabled-declaration-refusal', 'before': '                raise ValueError("Native date declarations changed; review the exact finite application selection")\n', 'after': '                raise ValueError("Native date declarations changed; review the exact finite application selection")\n            if focus == IOS_SHARE_PRESENTATION_FOCUS and re.search(r"@(Ignore|Disabled|IgnoredTest)\\b", source):\n                raise ValueError("New Share application declarations must remain enabled")\n', 'before_fragment_sha256': '58e6507fbda14ae9530ebcf9076704f4425f1b5464ca946209042b459273bbe8', 'after_fragment_sha256': '749c55a4556a8711a8afc9669574c074056aeb35d271c5fd2a142265ab2d0637'}, {'id': 'share-owning-plan-refusal', 'before': '        application_module = UI_APPLICATION_FOCUS_SPECS[focus].get("module", "calf-ui")\n', 'after': '        if focus == IOS_SHARE_PRESENTATION_FOCUS and (len(expected) != 1 or\n                expected[0].get("project") != ":calf-share" or\n                expected[0].get("report_directory") != "calf-share/build/test-results/" + IOS_APPLICATION_TASK or\n                any(path not in expected[0].get("test_source_files", []) for path in IOS_SHARE_APPLICATION_SOURCES)):\n            raise ValueError("New Share disposal plan requires its exact owning app sources/project/report tree")\n        application_module = UI_APPLICATION_FOCUS_SPECS[focus].get("module", "calf-ui")\n', 'before_fragment_sha256': '9281522897ce26c1dd696a7771bea4a128b9151a46522b818634b55b24b75de5', 'after_fragment_sha256': 'ae46bde19236258d7ea29262aa7bafaefa5714195e8ebddfb34ca2113ea274ec'}, {'id': 'share-full-receipt-required-groups', 'before': '                        "calf-webview": IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS}.get(expected["module"], ()))\n', 'after': '                        "calf-webview": IOS_WEBVIEW_APPLICATION_REQUIRED_GROUPS,\n                        "calf-share": IOS_SHARE_APPLICATION_REQUIRED_GROUPS}.get(expected["module"], ()))\n', 'before_fragment_sha256': '6e186ba8a24cab604ece6fd7dc267c92a399e6d6e82a69e79fecd308af6144b9', 'after_fragment_sha256': 'd51988c7ec5e48c1f5c4653a77428d4b65a1eaaaaa95a36762803a9f2c7dee57'}]}, 'scripts/ci/ios_ui_application.py': {'original153_sha256': '42056448d9f023ab3c136d164956350900117a30610457c91ee0b16de85f3244', 'share_composed_sha256': '92f2ce889f6b5cc31e6319584dd1385c403b416f23ae94db0ba895cc55c9bce6', 'fragments': [{'id': 'share-application-transport-entry', 'before': '    "calf-webview": {"task": ":calf-webview:" + lt.IOS_APPLICATION_TASK,\n                     "binary_directory": "calf-webview/build/bin/iosSimulatorArm64/applicationDebugTest",\n                     "receipt_subdirectory": "native-webview-application"},\n', 'after': '    "calf-webview": {"task": ":calf-webview:" + lt.IOS_APPLICATION_TASK,\n                     "binary_directory": "calf-webview/build/bin/iosSimulatorArm64/applicationDebugTest",\n                     "receipt_subdirectory": "native-webview-application"},\n    "calf-share": {"task": ":calf-share:" + lt.IOS_APPLICATION_TASK,\n                   "binary_directory": "calf-share/build/bin/iosSimulatorArm64/applicationDebugTest",\n                   "receipt_subdirectory": "native-share-application"},\n', 'before_fragment_sha256': 'eb91900ff6f5d148883e1e0e5813d0e7b89b5520b0ba26f08c529dd5236cdd5b', 'after_fragment_sha256': 'de6304049ccce2288121fad3b62d16326905b74680e8441e64d75748ba4ed96a'}, {'id': 'share-owning-result-remap', 'before': '    if host["module"] in {"calf-file-picker", "calf-webview"}:\n', 'after': '    if host["module"] in {"calf-file-picker", "calf-webview", "calf-share"}:\n', 'before_fragment_sha256': 'be57f98e2d07b93748f10e767abff0593c99798ff145145a28ddbf10517b20cd', 'after_fragment_sha256': '21ad526cb2b70a0f006164bf7b8fd85ad83f3bee8a44a5d43a72bd0c96b6a0bf'}]}, 'scripts/ci/workflow_matrix.py': {'original153_sha256': '5d65440ff6b274866b5ed4c7909a04131a6af821185062aca867f5c65223ba5a', 'share_composed_sha256': '81fca40e547a051ba7fbcd44fa7f66e8b34eff77899f0c9943c72984fc943e4c', 'fragments': [{'id': 'share-profile-one-slot', 'before': '    "ios-picker-provider-cancellation": ("ios-iphone",),\n', 'after': '    "ios-picker-provider-cancellation": ("ios-iphone",),\n    "ios-share-presentation-disposal": ("ios-iphone",),\n', 'before_fragment_sha256': '9d8c7575de8c35b2dcefee06ffafe7f4db72ebafdfa64a2b31d7898d52b66bf3', 'after_fragment_sha256': '84a3caca751f1c4f5668094598c7bb4e18b07e4e16656c12a1fdb8928a680c90'}, {'id': 'share-profile-one-module', 'before': '    "ios-picker-provider-cancellation": "calf-file-picker",\n', 'after': '    "ios-picker-provider-cancellation": "calf-file-picker",\n    "ios-share-presentation-disposal": "calf-share",\n', 'before_fragment_sha256': '77fbf4b476f0c31c42d60a99e67c94fba79d75de1dd77ae9a5026e104bf041f6', 'after_fragment_sha256': '1ca6ec84dd79041b45eec2768b48c31f82c4c8ab601fd040f463cc62eed79dac'}, {'id': 'share-profile-exact-row-focus', 'before': '    if profile == "ios-switch-cancellation":\n', 'after': '    if profile == "ios-share-presentation-disposal":\n        canonical = {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",\n                     "python": "python3", "simulator-kind": "iphone", "test-modules": "calf-share"}\n        if (PROFILES[profile] != ("ios-iphone",) or MODULE_SUBSETS.get(profile) != "calf-share" or\n                rows != [canonical]):\n            raise ValueError("New Share disposal profile requires its exact single genuine iPhone library host")\n        rows[0]["test-focus"] = "share-ios-presentation-disposal"\n    if profile == "ios-switch-cancellation":\n', 'before_fragment_sha256': '9417332b9679179e220009141cde1700f72891d86a24b42ec4241856368f6f17', 'after_fragment_sha256': '5868e68584ce2cfba87d1a1a9eec38ae3e740ab38d08aff482dd6b60924fa07a'}]}, '.github/workflows/gradle.yml': {'original153_sha256': 'edfc2c793ecb47ace202e4e3d271a9dc0c4b399a144fd7f79d766c129f84dae1', 'share_composed_sha256': '282254f7af66a47f065693f5fd4b30ae0acf8c44ca589fcc9432857ab473ef09', 'fragments': [{'id': 'share-workflow-profile-choice-token', 'before': 'ios-picker-provider-cancellation, ios-switch-cancellation', 'after': 'ios-picker-provider-cancellation, ios-share-presentation-disposal, ios-switch-cancellation', 'before_fragment_sha256': '36125a02d046ecbbeebad7fe189cef4e453701aee1b2b80530e765bd04bafa78', 'after_fragment_sha256': '616b223fc8a781dfd28dfe4e6ac06677fce6869bef1c8fa38e5df117e3290144'}, {'id': 'share-workflow-bounded-receipt-leaf', 'before': '            build/ci-verification/${{ matrix.slot }}/native-webview-application/*/receipt.json\n', 'after': '            build/ci-verification/${{ matrix.slot }}/native-webview-application/*/receipt.json\n            build/ci-verification/${{ matrix.slot }}/native-share-application/*/receipt.json\n', 'before_fragment_sha256': 'ca1dd07daae655a21b9283d255b36cbd7e2a017209358e6e7da1d139d80f121b', 'after_fragment_sha256': 'e5a36b14d52c7418bb2cca8aec71dbc055d9811b3ca8d4ad2c1ae811898e07ad'}]}}

# The single disjoint Wasm fixture pin is OPTIONAL and must be independently qualified by
# the lead before integration. This lexical reversal does not accept its browser repair.
SHARE_ALERT153_OPTIONAL_WASM_PIN = {'path': 'scripts/ci/library_tests.py', 'share_and_wasm_composed_sha256': 'b333567dff6f85bad734077bb44b2f4028035316ee2c3771cbe82b2019d00dfb', 'share_only_composed_sha256': '072e2163fe2653a14891a7eccc69e1430998ef3cf03e3e062255483250015585', 'before': 'SHARE_CLIPBOARD_NATIVE_FIXTURE_SHA256 = "347953a8c9596091c3923a37f564b51a7cd7f6488169718222ffe7c6c99e53c8"', 'after': 'SHARE_CLIPBOARD_NATIVE_FIXTURE_SHA256 = "e2f95d99ff2dd89fa95bd4de8fbedf9f3b60748284fed87ae6fe2ab3d2278a89"', 'before_fragment_sha256': '790626d0ed4cb1c84644d691680deb87aadf0a2bf3f9eb128372aaa8671e42d9', 'after_fragment_sha256': 'afa9210c1e807c0e5a09e80aacede0ab1b8fa17fd00defb99d0a98db5818eb68'}


def source_before_share_alert153_rebase(relative, current):
    if relative not in SHARE_ALERT153_REBASE:
        return current
    if type(current) is not bytes:
        raise ValueError("Exact Share alert153 source bytes are required")
    binding = SHARE_ALERT153_REBASE[relative]
    if binding["original153_sha256"] != EXPECTED_SOURCE_SHA256[relative]:
        raise ValueError("Original alert153 source hash must stay unchanged")
    optional = SHARE_ALERT153_OPTIONAL_WASM_PIN
    if relative == optional["path"] and digest(current) == optional["share_and_wasm_composed_sha256"]:
        before, after = optional["before"].encode(), optional["after"].encode()
        if (digest(before) != optional["before_fragment_sha256"] or
                digest(after) != optional["after_fragment_sha256"] or
                current.count(after) != 1 or current.count(before) != 0):
            raise ValueError("Only the exact independently owned Wasm pin may precede Share reconstruction")
        current = current.replace(after, before, 1)
        if digest(current) != optional["share_only_composed_sha256"]:
            raise ValueError("Exact optional Wasm pin inverse did not restore the Share-only image")
    if digest(current) != binding["share_composed_sha256"]:
        raise ValueError("Only the exact Share-composed source image may reconstruct alert153")
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (digest(before) != fragment["before_fragment_sha256"] or
                digest(after) != fragment["after_fragment_sha256"] or current.count(after) != 1):
            raise ValueError("The exact unique owning Share inverse fragment is required")
        current = current.replace(after, before, 1)
    if digest(current) != binding["original153_sha256"]:
        raise ValueError("Exact Share inverse did not restore every historical alert153 source byte")
    return current


def source_bindings():
    for relative, expected in EXPECTED_SOURCE_SHA256.items():
        path = ROOT / relative
        if (path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1 or
                digest(source_before_share_alert153_rebase(relative, path.read_bytes())) != expected):
            raise ValueError("Exact new alert-control source binding changed")
    expected_self = os.environ.get("NATIVECMPKIT_ALERT_NEW_CONTROL_EXPECTED_TEST_SHA256")
    if expected_self and digest(Path(__file__).read_bytes()) != expected_self:
        raise ValueError("Exact new alert-control method source binding changed")


# Verify the exact source paths/bytes before importing any candidate utility.
source_bindings()

# No accepted test helper/class is imported. These owning utilities are inert on
# import; subprocess/network entrypoints are denied while importing them too.
with ExitStack() as import_guards:
    guards(import_guards, sockets=False)
    import library_tests as r
    import ios_ui_application as app
    import workflow_matrix as matrix

for module, relative in ((r, "scripts/ci/library_tests.py"), (app, PARSER),
                         (matrix, "scripts/ci/workflow_matrix.py")):
    if Path(module.__file__).resolve() != ROOT / relative:
        raise ValueError("New alert-control owning module origin changed")
if r.ROOT.resolve() != ROOT:
    raise ValueError("New alert-control source root differs from the owning planner")


def native_sections(source):
    prefix, helper = source.split(MARK, 1)
    wrapped = helper.split("        waitForNative {\n", 1)[1].split("    } catch (readinessFailure", 1)[0]
    gate = "        waitForNative {\n" + wrapped
    gate = "\n".join(line[4:] if line.startswith("    ") else line for line in gate.split("\n"))
    activation = "    runOnIdle {\n" + helper.split("    runOnIdle {\n", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    catch = "    } catch (readinessFailure" + helper.split("    } catch (readinessFailure", 1)[1].split("    runOnIdle {\n", 1)[0]
    diagnostic = source.split("private fun recordImportantAlertActionTimeoutDiagnostic", 1)[1].split("/** Read at most2048 views", 1)[0]
    sample = source.split("private fun UIView.importantAlertDiagnosticSample", 1)[1]
    return prefix, gate, activation, catch, diagnostic, sample


def exact_native_contract(source):
    try:
        prefix, gate, activation, catch, diagnostic, sample = native_sections(source)
        required = ((prefix, ORIGINAL_PREFIX_SHA256), (gate, ORIGINAL_GATE_SHA256),
                    (activation, ORIGINAL_ACTIVATION_SHA256), (catch, CANDIDATE_CATCH_SHA256),
                    (diagnostic, CANDIDATE_DIAGNOSTIC_SHA256), (sample, CANDIDATE_SAMPLE_SHA256))
        if any(digest(text.encode()) != expected for text, expected in required):
            raise ValueError("Exact native alert diagnostic fragments changed")
        match = re.search(r"val limit = ([1-9][0-9]*)\n", sample)
        if match is None or int(match[1]) != 2048:
            raise ValueError("Exact native alert hierarchy limit changed")
        return {"catch": catch, "diagnostic": diagnostic, "sample": sample, "limit": int(match[1])}
    except (IndexError, ValueError) as error:
        raise ValueError("Exact native alert diagnostic fragments changed") from error


@dataclass(eq=False)
class SyntheticView:
    label: str | None = None
    button: bool = False
    hidden: bool = False
    alpha: float = 1.0
    window: object | None = None
    children: list = field(default_factory=list)


class SyntheticIllegalState(Exception):
    def __init__(self, message, *, suppression_throws=False):
        super().__init__(message)
        self.suppressed = []
        self.suppression_throws = suppression_throws

    def add_suppressed(self, secondary):
        if self.suppression_throws:
            raise RuntimeError("synthetic-suppression-failure")
        self.suppressed.append(secondary)


def projected_sample(root, limit):
    """Synthetic specification of the exact pinned Kotlin BFS; NOT UIKit."""
    sampled, pending, complete = [], deque([root]), True
    max_owned = 1
    while pending:
        view = pending.popleft()
        sampled.append(view)
        available = limit - len(sampled) - len(pending)
        children = view.children
        if len(children) > available:
            complete = False
        for child in children[:min(len(children), available)]:
            if isinstance(child, SyntheticView):
                pending.append(child)
        max_owned = max(max_owned, len(sampled) + len(pending))
    return sampled, complete, max_owned


def projected_facts(alert, title, window, limit):
    sampled, complete, max_owned = projected_sample(alert.view, limit)
    matching = [action for action in alert.actions if action.title == title]
    action = matching[0] if len(matching) == 1 else None
    labelled = [view for view in sampled if view.label == title]
    buttons = [view for view in labelled if view.button]
    visible = [view for view in buttons if not view.hidden and view.alpha > 0.0]
    eligible = [view for view in visible if view.window is window]
    return {"main_thread": True, "alert_attached": alert.view.window is window,
            "matching_actions": len(matching), "action_unique": action is not None,
            "action_enabled": action is not None and action.enabled is True,
            "sampled_views": len(sampled), "hierarchy_complete": complete,
            "label_matches": len(labelled), "button_trait_matches": len(buttons),
            "visible_matches": len(visible), "eligible_matches": len(eligible)}, max_owned


def projected_console(diagnostic, facts):
    """Render the actual pinned Kotlin literal/interpolation allowlist only."""
    start = diagnostic.split('println("' + PREFIX + ' captured=true ', 1)[1]
    expression = '"' + PREFIX + ' captured=true ' + start.split("\n        }", 1)[0]
    fragments = re.findall(r'"((?:[^"\\]|\\.)*)"', expression)
    template = "".join(fragments)
    expressions = {"platform.Foundation.NSThread.isMainThread": "main_thread",
                   "sameNativeObject(alert.view.window, window)": "alert_attached",
                   "matchingActions.size": "matching_actions", "action != null": "action_unique",
                   "action?.enabled == true": "action_enabled", "sample.size": "sampled_views",
                   "labelled.size": "label_matches", "buttons.size": "button_trait_matches",
                   "visible.size": "visible_matches", "eligible.size": "eligible_matches"}
    def scalar(key):
        value = facts[key]
        if type(value) is bool:
            return "true" if value else "false"
        if type(value) is int and value >= 0:
            return str(value)
        raise ValueError("Numeric/Boolean diagnostic scalar refused")
    def substitute(match):
        if match[1] not in expressions:
            raise ValueError("Unreviewed diagnostic interpolation refused")
        return scalar(expressions[match[1]])
    line = re.sub(r"\$\{([^}]+)\}", substitute, template).replace("$exhaustive", scalar("hierarchy_complete"))
    pairs = line.split(" ")[1:]
    keys = [pair.split("=", 1)[0] for pair in pairs]
    if (line.split(" ")[0] != PREFIX or keys != ["captured", *facts] or
            any(re.fullmatch(r"[a-z_]+=(?:true|false|0|[1-9][0-9]*)", pair) is None for pair in pairs)):
        raise ValueError("Fixed diagnostic field/value grammar refused")
    return line


def projected_capture(primary, read_facts, emit, diagnostic):
    """Synthetic source-pinned fault specification, not native console I/O."""
    try:
        emit(projected_console(diagnostic, read_facts()))
    except BaseException as observation:
        try:
            emit(PREFIX + " captured=false")
        except BaseException:
            pass  # Exact proposed best-effort reporting branch.
        try:
            if observation is not primary:
                primary.add_suppressed(observation)
        except BaseException:
            pass  # Exact proposed best-effort suppression branch.


def projected_gate(wait, observe, activate):
    """Synthetic finally semantics constrained by exact_native_contract."""
    try:
        wait()
    except SyntheticIllegalState as primary:
        try:
            if isinstance(primary.args[0], str) and primary.args[0].startswith(TIMEOUT):
                observe(primary)
        finally:
            raise primary
    activate()


class AlertImportantRecoveryNewOnlyTests(unittest.TestCase):
    def setUp(self):
        source_bindings()
        self.source = (ROOT / NATIVE).read_text()
        self.contract = exact_native_contract(self.source)
        self.actions = ExitStack()
        self.addCleanup(self.actions.close)
        guards(self.actions)

    def tearDown(self):
        self.assertEqual([], FORBIDDEN_ACTIONS)
        source_bindings()

    def raised_same(self, primary, call):
        try:
            call()
        except BaseException as actual:
            self.assertIs(actual, primary)
            self.assertEqual(actual.args, primary.args)
            return
        self.fail("The original primary failure was not rethrown")

    def fake_alert(self):
        window = object()
        title = "SYNTHETIC_PRIVATE_AUTHORED_CONTENT"
        button = SyntheticView(title, True, window=window)
        root = SyntheticView(window=window, children=[button])
        return SimpleNamespace(view=root, actions=[SimpleNamespace(title=title, enabled=True)]), title, window

    def plan(self):
        return r.plan(ROOT, "ios", only_modules=("calf-ui",), focus=FOCUS)

    def test_original_four_bodies_gate_public_activation_deadline_host_and_parser_are_byte_retained(self):
        self.assertEqual(2048, self.contract["limit"])
        self.assertIn('val deadline = NSProcessInfo.processInfo.systemUptime + 10.0', (ROOT / HOST).read_text())
        self.assertIn('awaitMain("native predicate") { predicate() }', (ROOT / HOST).read_text())
        self.assertIn("} finally {", self.contract["catch"])
        self.assertEqual(1, self.contract["catch"].count("recordImportantAlertActionTimeoutDiagnostic("))
        self.assertIn("throw readinessFailure", self.contract["catch"])
        for forbidden in (".activateAction(", ".dismiss(", "performSelector", "valueForKey", "setValue(",
                          "UITouch(", "UIEvent(", "NSClassFromString"):
            self.assertNotIn(forbidden, self.source.split(MARK, 1)[1])

    def test_gate_success_has_no_diagnostic_and_public_activation_once(self):
        calls = []
        projected_gate(lambda: calls.append("wait"), lambda primary: calls.append("observe"), lambda: calls.append("activate"))
        self.assertEqual(["wait", "activate"], calls)

    def test_only_exact_owning_timeout_observes_once_on_model_main_without_activation(self):
        alert, title, window = self.fake_alert()
        primary = SyntheticIllegalState(TIMEOUT + "synthetic-existing-state")
        calls, lines = [], []
        def read():
            calls.append("synthetic-main-read")
            return projected_facts(alert, title, window, self.contract["limit"])[0]
        def observe(actual):
            calls.append("observe")
            self.assertIs(actual, primary)
            projected_capture(actual, read, lines.append, self.contract["diagnostic"])
        self.raised_same(primary, lambda: projected_gate(lambda: (_ for _ in ()).throw(primary), observe,
                                                        lambda: calls.append("activate")))
        self.assertEqual(["observe", "synthetic-main-read"], calls)
        self.assertEqual(1, len(lines))
        self.assertIn("captured=true", lines[0])

    def test_other_failure_types_none_and_nonowning_prefixes_never_emit(self):
        failures = [SyntheticIllegalState(None), SyntheticIllegalState("other phase"),
                    SyntheticIllegalState(TIMEOUT.rstrip()), SyntheticIllegalState("prefix " + TIMEOUT),
                    AssertionError(TIMEOUT), ValueError(TIMEOUT), KeyboardInterrupt(TIMEOUT)]
        for case_id, primary in enumerate(failures):
            with self.subTest(case_id=case_id):
                calls = []
                self.raised_same(primary, lambda: projected_gate(lambda: (_ for _ in ()).throw(primary),
                    lambda actual: calls.append("observe"), lambda: calls.append("activate")))
                self.assertEqual([], calls)

    def test_capture_failure_falls_back_without_content_and_keeps_primary_suppression(self):
        primary = SyntheticIllegalState(TIMEOUT)
        secondary = RuntimeError("SYNTHETIC_PRIVATE_ERROR_CONTENT")
        lines = []
        self.raised_same(primary, lambda: projected_gate(lambda: (_ for _ in ()).throw(primary),
            lambda actual: projected_capture(actual, lambda: (_ for _ in ()).throw(secondary), lines.append,
                                              self.contract["diagnostic"]), lambda: self.fail("No activation on timeout")))
        self.assertEqual([PREFIX + " captured=false"], lines)
        self.assertEqual([secondary], primary.suppressed)
        self.assertNotIn(str(secondary), "\n".join(lines))

    def test_throwing_emitters_suppression_or_unexpected_observer_cannot_replace_primary(self):
        alert, title, window = self.fake_alert()
        for mode in ("both-emissions-throw", "suppression-throws", "unexpected-observer-throws"):
            with self.subTest(mode=mode):
                primary = SyntheticIllegalState(TIMEOUT, suppression_throws=mode == "suppression-throws")
                emission_attempts = []
                def emit(line):
                    emission_attempts.append(line.split(" ", 1)[0])
                    if mode == "both-emissions-throw":
                        raise OSError("synthetic-console-failure")
                def read():
                    if mode == "suppression-throws":
                        raise RuntimeError("synthetic-read-failure")
                    return projected_facts(alert, title, window, self.contract["limit"])[0]
                def observe(actual):
                    if mode == "unexpected-observer-throws":
                        raise RuntimeError("synthetic-unexpected-observer-failure")
                    projected_capture(actual, read, emit, self.contract["diagnostic"])
                self.raised_same(primary, lambda: projected_gate(lambda: (_ for _ in ()).throw(primary), observe,
                                                                lambda: self.fail("No activation on timeout")))
                self.assertLessEqual(len(emission_attempts), 2)
                # Partial writes/failing emitters do NOT promise one physical line.

    def test_fixed_source_formatter_exports_only_numeric_boolean_allowlisted_fields(self):
        alert, title, window = self.fake_alert()
        facts, _ = projected_facts(alert, title, window, self.contract["limit"])
        line = projected_console(self.contract["diagnostic"], facts)
        self.assertNotIn(title, line)
        self.assertNotIn("SYNTHETIC_PRIVATE", line)
        self.assertLess(len(line.encode()), 512)
        for key in facts:
            with self.subTest(key=key):
                changed = dict(facts, **{key: "SYNTHETIC_PRIVATE_SCALAR"})
                with self.assertRaises(ValueError): projected_console(self.contract["diagnostic"], changed)
        changed = self.contract["diagnostic"].replace("${matchingActions.size}", "${title}", 1)
        with self.assertRaises(ValueError): projected_console(changed, facts)

    def test_bounded_sample_leaf_branch_exact_cap_and_wide_deep_cyclic_invalid_children(self):
        limit = self.contract["limit"]
        leaf = SyntheticView()
        exact = SyntheticView(children=[SyntheticView() for _ in range(limit - 1)])
        wide = SyntheticView(children=[SyntheticView() for _ in range(limit + 1)])
        deep = SyntheticView(); current = deep
        for _ in range(limit + 1):
            child = SyntheticView(); current.children = [child]; current = child
        cyclic = SyntheticView(); cyclic.children = [cyclic]
        branching = SyntheticView(children=[SyntheticView(children=[SyntheticView()]), SyntheticView()])
        invalid = SyntheticView(children=[object(), SyntheticView()])
        for case_id, (root, count, complete) in enumerate(((leaf, 1, True), (exact, limit, True),
                (wide, limit, False), (deep, limit, False), (cyclic, limit, False),
                (branching, 4, True), (invalid, 2, True))):
            with self.subTest(case_id=case_id):
                sampled, actual_complete, max_owned = projected_sample(root, limit)
                self.assertEqual(count, len(sampled)); self.assertIs(complete, actual_complete)
                self.assertLessEqual(max_owned, limit)

    def test_complete_synthetic_snapshot_keeps_exact_label_trait_visibility_attachment_chain(self):
        alert, title, window = self.fake_alert()
        alert.view.children += [SyntheticView("other", True, window=window),
            SyntheticView(title, False, window=window), SyntheticView(title, True, hidden=True, window=window),
            SyntheticView(title, True, alpha=0.0, window=window), SyntheticView(title, True, window=object())]
        facts, _ = projected_facts(alert, title, window, self.contract["limit"])
        self.assertEqual((5, 4, 2, 1), tuple(facts[key] for key in
            ("label_matches", "button_trait_matches", "visible_matches", "eligible_matches")))
        self.assertIs(True, facts["hierarchy_complete"])
        alert.actions.append(SimpleNamespace(title=title, enabled=True))
        facts, _ = projected_facts(alert, title, window, self.contract["limit"])
        self.assertEqual(2, facts["matching_actions"])
        self.assertIs(False, facts["action_unique"]); self.assertIs(False, facts["action_enabled"])

    def test_ordinary_diagnostic_advances_only_stream_bytes_not_native_cases_lifecycle_or_failures(self):
        protocol = app.NativeProtocol()
        ordinary = PREFIX + " captured=false"
        for phase in ("before-active", "active-open-failed", "after-completed"):
            if phase == "active-open-failed":
                for line in ("NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2",
                             "##teamcity[testSuiteStarted name='synthetic']",
                             "##teamcity[testStarted name='synthetic']",
                             "##teamcity[testFailed name='synthetic' message='synthetic']"):
                    protocol.feed(line)
            elif phase == "after-completed":
                for line in ("##teamcity[testFinished name='synthetic']", "##teamcity[testSuiteFinished name='synthetic']",
                             "NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true"):
                    protocol.feed(line)
            before = copy.deepcopy(vars(protocol)); previous_bytes = before.pop("stream_bytes")
            protocol.feed(ordinary)
            after = copy.deepcopy(vars(protocol)); self.assertEqual(previous_bytes + len((ordinary + "\n").encode()), after.pop("stream_bytes"))
            self.assertEqual(before, after)
        self.assertEqual("failed", protocol.cases[("synthetic", "synthetic")]["status"])
        with self.assertRaises(ValueError): app.NativeProtocol().feed("NATIVECMPKIT_UIKIT_ALERT_ACTION_GATE_TIMEOUT captured=false")
        refused = app.NativeProtocol(); refused.lifecycle_failure_observation = {"stage": "synthetic-existing-failure"}
        with self.assertRaises(ValueError): refused.feed(ordinary)

    def test_exact_four_plan_gradle_filters_and_native_focus_exclude_date_material_and_old_methods(self):
        plan = self.plan(); self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-ui"], plan["explicit_module_subset"])
        item, = plan["expected"]
        self.assertEqual("genuine-uikit-application", item["native_test_host"])
        self.assertEqual(4, len(item["required_testcases"]))
        groups = r.ui_application_focus_groups(FOCUS)
        self.assertEqual([(r.UI_ALERT_IMPORTANT_CLASS, r.UI_ALERT_IMPORTANT_SOURCE, r.UI_ALERT_IMPORTANT_METHODS)],
                         [(group["classname"], group["source"], group["methods"]) for group in groups])
        filters = [r.UI_ALERT_IMPORTANT_CLASS + "." + method for method in r.UI_ALERT_IMPORTANT_METHODS]
        command = r.gradle_command("ios", plan, simulator="11111111-1111-1111-1111-111111111111")
        self.assertEqual([part for value in filters for part in ("--tests", value)], command[-8:])
        self.assertEqual([":" + "calf-ui:" + r.IOS_APPLICATION_TASK], [part for part in command if part.startswith(":")])
        for selected in (filters, list(reversed(filters))):
            self.assertEqual(FOCUS, app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(selected)]))
        self.assertEqual(app.APP_TIMEOUT_SECONDS, app.application_timeout_seconds(FOCUS))

    def test_missing_duplicate_arbitrary_wildcard_extra_date_or_second_filter_are_refused(self):
        filters = r.ui_application_focus_filter(FOCUS).split(",")
        date = r.UI_DATE_YEAR_NATIVE_CLASS + "." + r.UI_DATE_YEAR_NATIVE_METHODS[0]
        material = r.UI_DATE_YEAR_MATERIAL_CLASS + "." + r.UI_DATE_YEAR_MATERIAL_METHODS[0]
        for case_id, selection in enumerate((filters[:-1], filters + [filters[0]], filters * 2,
                [*filters, date], [*filters, material], [*filters[:-1], "*"], ["*"], ["arbitrary"])):
            with self.subTest(case_id=case_id), self.assertRaises(ValueError):
                app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(selection)])
        with self.assertRaises(ValueError):
            app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(filters), "--ktest_gradle_filter=*"])

    def test_wrong_suite_module_task_host_report_project_scope_or_inventory_never_accepts(self):
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-io",)), ("ios", None),
                               ("ios", ("calf-ui", "calf-io"))):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(ROOT, suite, only_modules=modules, focus=FOCUS)
        for section, key, value in (("plan", "complete_suite_requested", True),
                ("plan", "explicit_module_subset", []), ("item", "module", "calf-io"),
                ("item", "project", ":calf-io"), ("item", "report_directory", "arbitrary"),
                ("item", "task", ":calf-ui:iosSimulatorArm64Test"), ("item", "native_test_host", "synthetic"),
                ("item", "test_filter", "*"), ("item", "required_testcases", []), ("item", "test_source_files", [])):
            plan = copy.deepcopy(self.plan()); (plan if section == "plan" else plan["expected"][0])[key] = value
            with self.subTest(section=section, key=key), self.assertRaises(ValueError): r.validate_test_focus(plan)

    def test_disabled_removed_extra_native_declarations_and_missing_application_host_refuse(self):
        real_read = Path.read_text
        for case_id, changed in enumerate((self.source.replace("@Test fun", "fun", 1),
                self.source.replace("@Test fun", "@Ignore @Test fun", 1),
                self.source.replace("@Test fun", "@Disabled @Test fun", 1),
                self.source + "\n@Test fun arbitraryMethod() {}\n")):
            def read(path, *args, **kwargs):
                return changed if path == ROOT / NATIVE else real_read(path, *args, **kwargs)
            with self.subTest(case_id=case_id), patch.object(Path, "read_text", new=read), self.assertRaises(ValueError): self.plan()
        real_is_file = Path.is_file
        def present(path):
            return False if path == ROOT / HOST else real_is_file(path)
        with patch.object(Path, "is_file", new=present), self.assertRaises(ValueError): self.plan()

    def test_single_canonical_profile_refuses_runner_arch_python_kind_extra_fields_and_keeps_full_slots(self):
        expected = {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
                    "python": "python3", "simulator-kind": "iphone", "test-modules": "calf-ui", "test-focus": FOCUS}
        self.assertEqual({"include": [expected]}, matrix.matrix(PROFILE))
        for key, value in (("runner", "arbitrary"), ("arch", "x64"), ("python", "arbitrary"),
                           ("suite", "desktop"), ("simulator-kind", "ipad"), ("unexpected", "value")):
            slots = tuple({**slot, key: value} if slot["slot"] == "ios-iphone" else dict(slot) for slot in matrix.SLOTS)
            with self.subTest(key=key), patch.object(matrix, "SLOTS", slots), self.assertRaises(ValueError): matrix.matrix(PROFILE)
        with patch.dict(matrix.PROFILES, {PROFILE: ("ios-ipad",)}), self.assertRaises(ValueError): matrix.matrix(PROFILE)
        with patch.dict(matrix.MODULE_SUBSETS, {PROFILE: "calf-io"}), self.assertRaises(ValueError): matrix.matrix(PROFILE)
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        for profile in ("all", "ios", "ios-ui", "extended"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))
        # Passive selection checks only: no previous native/Material body executes.
        self.assertEqual(10, sum(len(group["methods"]) for group in r.ui_application_focus_groups(r.UI_ALERT_DATE_IMPORTANT_FOCUS)))
        self.assertEqual(6, len(r.UI_DATE_YEAR_NATIVE_METHODS)); self.assertEqual(2, len(r.UI_DATE_YEAR_MATERIAL_METHODS))

    def test_mocked_source_only_preflight_is_one_new_cli_not_material_or_second_application(self):
        commands = []
        def source_only(command, **kwargs):
            commands.append(command)
            self.assertEqual("plan", command[3])
            self.assertEqual(["ios", "calf-ui", FOCUS], [command[command.index(flag) + 1] for flag in ("--suite", "--module", "--focus")])
            return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps(self.plan()))
        with patch.object(matrix.subprocess, "run", side_effect=source_only):
            result = matrix.preflight_plans(PROFILE, ROOT)
        self.assertEqual(1, len(commands)); self.assertEqual(1, len(result["slots"]))
        self.assertEqual((True, 0, 0), (result["source_only"], result["Gradle_builds_executed"], result["library_tests_executed"]))
        workflow = (ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertEqual(1, workflow.count(PROFILE)) # Choice only: no additional jobs/steps/permissions.
        self.assertEqual(2, workflow.count("inputs.profile == 'ios-alert-date-important'"))
        self.assertNotIn("serial-test-focus", matrix.matrix(PROFILE)["include"][0])

    def collect(self, cases, *, marker=1, age=0, extra_empty=False, split=False):
        plan = self.plan(); item, = plan["expected"]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); report = root / item["report_directory"]; report.mkdir(parents=True)
            groups = [cases[:2], cases[2:]] if split else [cases]
            if extra_empty:
                groups.append([])
            now = time.time_ns()
            for index, group in enumerate(groups):
                xml = ET.Element("testsuite")
                for case in group:
                    node = ET.SubElement(xml, "testcase", classname=case["classname"], name=case["name"])
                    if case.get("status") in ("failure", "error", "skipped"):
                        ET.SubElement(node, case["status"])
                path = report / ("TEST-explicitly-synthetic-alert4-" + str(index) + ".xml")
                path.write_bytes(ET.tostring(xml)); os.utime(path, ns=(now - age, now - age))
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({item["task"]: marker}), host_system="Darwin")

    def test_only_fresh_exact_four_xml_identities_and_owned_alert_sources_are_qualified_synthetically(self):
        cases = [{**case, "status": "passed"} for case in r.ui_application_focus_identities(FOCUS)]
        result = self.collect(cases)
        self.assertEqual([], result["errors"])
        self.assertEqual(4, result["totals"]["passed"])
        self.assertEqual({NATIVE}, {case["source"] for case in result["modules"][0]["native_scenarios"]})

    def test_missing_duplicate_foreign_date_material_failed_skipped_stale_future_or_zero_xml_refuse(self):
        cases = [{**case, "status": "passed"} for case in r.ui_application_focus_identities(FOCUS)]
        date = r.ui_application_focus_identities(r.UI_ALERT_DATE_IMPORTANT_FOCUS)[4]
        material = r.ui_date_year_material_identities()[0]
        variations = [[], cases[:-1], cases + [cases[0]], [*cases, date], [*cases, material],
                      [{**cases[0], "classname": "synthetic.foreign"}, *cases[1:]],
                      [{**cases[0], "name": cases[0]["name"].replace("[iosSimulatorArm64]", "[iosArm64]")}, *cases[1:]]]
        variations += [[{**cases[0], "status": outcome}, *cases[1:]] for outcome in ("failure", "error", "skipped")]
        for case_id, selected in enumerate(variations):
            with self.subTest(case_id=case_id): self.assertTrue(self.collect(selected)["errors"])
        self.assertTrue(self.collect(cases, extra_empty=True)["errors"])
        self.assertTrue(self.collect(cases, split=True)["errors"])
        for marker in (0, 2):
            with self.subTest(marker=marker): self.assertTrue(self.collect(cases, marker=marker)["errors"])
        for age in (10_000_000_000, -10_000_000_000):
            with self.subTest(age=age): self.assertTrue(self.collect(cases, age=age)["errors"])

    def test_exact_owning_source_mutations_are_refused_before_any_synthetic_behavior_claim(self):
        for case_id, changed in enumerate((self.source.replace("throw readinessFailure", "throw IllegalStateException()", 1),
                self.source.replace("        } finally {", "        }", 1),
                self.source.replace("        } catch (_: Throwable) { /* Suppression failure is never replacement primary. */ }", "        }", 1),
                self.source.replace("val limit = 2048", "val limit = 2049", 1),
                self.source.replace("hierarchy_complete=$exhaustive", "hierarchy_complete=true", 1),
                self.source.replace("${matchingActions.size}", "${title}", 1),
                self.source.replace("sameNativeObject(alert.view.window, window)", "true", 1),
                self.source.replace("accessibilityActivate()", "activateAction()", 1))):
            with self.subTest(case_id=case_id), self.assertRaises(ValueError): exact_native_contract(changed)


if __name__ == "__main__":
    unittest.main()
