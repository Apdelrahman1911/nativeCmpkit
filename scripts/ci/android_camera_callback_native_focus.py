# SPDX-License-Identifier: Apache-2.0
"""Exact one-method Android callback/delayed-recipient routing and source custody.

Source inverse/forward arithmetic is not compiler or Android execution. The
normally inherited enabled API35-only method makes unrestricted Camera/all
requests refuse before host work; no source pruning, Ignore or implicit skip.
Original provider/restoration methods, defaults and native helpers stay intact.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
FOCUS = "android-camera-callback-substitution"
PROFILE = FOCUS
MODULE = "calf-camera-picker"
PROJECT = ":calf-camera-picker"
TASK = PROJECT + ":connectedAndroidDeviceTest"
CLASS = "com.mohamedrejeb.calf.camerapicker.AndroidCameraCallbackSubstitutionTest"
METHOD = "nativeActiveCaptureDeliversOnceToLatestCallbackWithoutReplacingOwner"
SOURCE = "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraCallbackSubstitutionTest.kt"
PROVIDER_SOURCE = "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraProviderTest.kt"
CONTRACT_KEY = "android_camera_callback_source_contract"
GRADLE_PROPERTY = "nativecmpkitCameraCallbackSubstitution"
RECEIVER = "io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver"
DELAYED_COMPONENT = RECEIVER + ".CameraDelayedReceiverActivity"
REPORT_DIRECTORY = MODULE + "/build/outputs/androidTest-results/connected/androidMain"
DECLARED_XML_DIRECTORY = MODULE + "/build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest"
SOURCE_RELATIVE = "scripts/ci/android_camera_callback_native_focus.py"
SPEC_RELATIVE = "scripts/ci/fixtures/android-camera-callback672-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/android-camera-callback672-source-inverse.json"
SPEC_SHA256 = "1c14d6fcb7dc49716de3688169c9280fde51f62564d1593a6a95707f85f19f7a"
PREDECESSOR = "044d9aa83ad19fa77ddf94f36a7700f3b52de4b1"
SEALED_LEAF_SHA256 = "455bb3c9df8f553e6840325828ee96db9fc268a948703557355b1c9c2b926b8f"
SEALED_PROVIDER_AFTER = "53e355fa832c2fe622eeae1627de3847d224393f8656b50a7c6b2f396b7bfab1"
SEALED_CALLBACK = "4b722312599a0bd23229d36c9c4efbd98a02e147b2a1add4be67a6680d40b0d0"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_SPEC_BYTES = 256 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SCOPE = "Exact callback672 source/routing custody only; no compiler/native acceptance"
SCOPE = ("Only NEW Android NATIVE-020/#76 callback criterion1: one genuine foreign-UID active TakePicture capture, "
         "A-to-B actual Compose commit after native reentry of the SAME caller, stable public launcher across ordinary "
         "recompositions, exactly one Android Main delivery to B and zero to A/default, synthetic native output with one "
         "descriptor open/close, and exact joined capture/task/file/component cleanup. Original provider/restoration and "
         "accepted iOS/host/native populations are not replayed. No iOS owner/GC criteria, Dont-keep/process-death/rotation, "
         "physical/vendor camera, packaged consumer/API-ABI, dependency/legal/security/release certification or issue closure.")

# Generated exact finite sets below, from ordinary root044d inputs, not a full
# library/compiled/native map. All entries are source-contract operands only.
BOUND_PATHS = frozenset({
    PROVIDER_SOURCE,
    "scripts/ci/library_tests.py", "scripts/ci/android_device_tests.py",
    "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml",
    "scripts/ci/fresh-tests.init.gradle.kts", "scripts/ci/test_android_camera_provider.py",
})
ADDED_PATHS = frozenset({SOURCE, "scripts/ci/test_android_camera_callback_native_focus.py",
                         "docs/testing/android-camera-callback-substitution.md"})
IMMUTABLE_PATHS = frozenset(['build.gradle.kts', 'calf-camera-picker/build.gradle.kts', 'calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRestorationVerificationActivity.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraVerificationProviders.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedCameraReceiver.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt', 'calf-camera-picker/src/androidDeviceTest/res/xml/nativecmpkit_camera_device_paths.xml', 'calf-camera-picker/src/androidDeviceTest/res/xml/nativecmpkit_camera_device_wrong_paths.xml', 'calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt', 'calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt', 'calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerResult.kt', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRequestStateTest.kt', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaseline.kt', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaselineTest.kt', 'convention-plugins/src/main/kotlin/Android.kt', 'gradle.properties', 'gradle/libs.versions.toml', 'scripts/ci/android_camera_developer_prerequisite.py', 'scripts/ci/android_camera_receiver.py', 'scripts/ci/android_geo_probe.py', 'scripts/ci/android_share_recipient.py', 'scripts/ci/ios_popover_anchor_plan.py', 'scripts/ci/runtime_context.py', 'settings.gradle.kts', 'tests/consumer/android-camera-receiver/build.gradle.kts', 'tests/consumer/android-camera-receiver/settings.gradle.kts', 'tests/consumer/android-camera-receiver/src/main/AndroidManifest.xml', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraDelayedReceiverActivity.java', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverActivity.java', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverService.java'])
TEST_SOURCES = frozenset(['calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraCallbackSubstitutionTest.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraProviderTest.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRestorationVerificationActivity.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraVerificationProviders.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedCameraReceiver.kt', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRequestStateTest.kt', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaseline.kt', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/SettingsHomeTaskBaselineTest.kt'])
TEST_SOURCE_SETS = ["commonTest", "androidDeviceTest"]


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError("Duplicate callback672 manifest field")
        document[key] = value
    return document


def _json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite callback672 JSON")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("Complete finite callback672 manifest JSON is required") from None


def _shape(document):
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "predecessor", "sealed_leaf_sha256", "bindings", "added_inputs", "immutable_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != _SCOPE or document["predecessor"] != PREDECESSOR or
            document["sealed_leaf_sha256"] != SEALED_LEAF_SHA256 or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["immutable_inputs"]) is not dict or set(document["immutable_inputs"]) != IMMUTABLE_PATHS or
            type(document["own_guard"]) is not dict or set(document["own_guard"]) != {"template_sha256", "bytes"} or
            type(document["own_guard"]["bytes"]) is not int or not 0 < document["own_guard"]["bytes"] <= MAX_SOURCE_BYTES or
            type(document["own_guard"]["template_sha256"]) is not str or
            _DIGEST.fullmatch(document["own_guard"]["template_sha256"]) is None):
        raise ValueError("Exact complete finite callback672 manifest schema is required")
    for row in document["bindings"].values():
        if (type(row) is not dict or set(row) != {
                "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 12):
            raise ValueError("Exact finite callback672 binding and complete byte/hash operands are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                    "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    fragment["before"] == fragment["after"] or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact nonempty callback672 inverse/forward fragments are required")
    if (any(type(digest) is not str or _DIGEST.fullmatch(digest) is None
            for digest in (*document["added_inputs"].values(), *document["immutable_inputs"].values())) or
            document["bindings"][PROVIDER_SOURCE]["after_sha256"] != SEALED_PROVIDER_AFTER or
            document["added_inputs"][SOURCE] != SEALED_CALLBACK):
        raise ValueError("The once-adopted leaf668 and complete immutable/added source hashes must remain exact")
    return document


def _ordinary_bytes(root: Path, relative: str) -> bytes:
    # Existing rejecting ordinary-file reader; only passive bounded source data.
    from ios_popover_anchor_plan import _ordinary_bytes as ordinary
    payload = ordinary(root, relative)[0]
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Complete bounded ordinary callback672 source bytes are required")
    return payload


def _document():
    before = SPEC_PATH.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One bounded ordinary callback672 source manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)
    if len(raw) > MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact callback672 source manifest changed")
    return _shape(_json(raw))


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact relative callback672 identity and complete bytes are required")


def source_before_callback672(relative, payload):
    """Exact complete isolated callback inverse or root044d; never current admission."""
    _identity(relative, payload)
    from tooling_recovery671_source_projection import peel_tooling671_for_history, peel_callback_isolated680_for_history
    payload = peel_tooling671_for_history(relative, payload)
    payload = peel_callback_isolated680_for_history(relative, payload)
    row = _document()["bindings"].get(relative)
    if row is None:
        return payload  # Unlisted data is not certified or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Complete bounded callback672 source bytes are required")
    observed = sha(payload)
    if observed == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return payload
    if observed != row["after_sha256"] or len(payload) != row["after_bytes"]:
        raise ValueError("Callback672 source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or restored.count(after) != 1:
            raise ValueError("Exact unique callback672 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != row["before_sha256"] or len(restored) != row["before_bytes"]:
        raise ValueError("Callback672 inverse did not restore its complete root044d source")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique callback672 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Complete callback672 inverse/forward roundtrip differs")
    return restored


def current_source_before_callback672(relative, payload):
    """One strict671 raw ingress before the qualified isolated callback byte view."""
    _identity(relative, payload)
    from tooling_recovery671_source_projection import current_source_before_tooling671, callback_isolated_after_qualified_tooling671
    payload = current_source_before_tooling671(relative, payload)
    payload = callback_isolated_after_qualified_tooling671(relative, payload)
    document = _document()
    row = document["bindings"].get(relative)
    digest = (row["after_sha256"] if row is not None else
              (document["added_inputs"] | document["immutable_inputs"]).get(relative))
    if digest is not None and (sha(payload) != digest or row is not None and len(payload) != row["after_bytes"]):
        raise ValueError("Old or unknown bytes cannot replace exact current callback672 source")
    return source_before_callback672(relative, payload)


def peel_callback672_for_history(relative, payload):
    """Only exact671/composed680/isolated callback images peel; pass-through is not current."""
    _identity(relative, payload)
    from tooling_recovery671_source_projection import peel_tooling671_for_history, peel_callback_isolated680_for_history
    payload = peel_tooling671_for_history(relative, payload)
    payload = peel_callback_isolated680_for_history(relative, payload)
    row = _document()["bindings"].get(relative)
    if row is not None and sha(payload) == row["after_sha256"]:
        return source_before_callback672(relative, payload)
    return payload  # Unchanged next historical pin owns refusal; no restored code runs.  # Unchanged next historical pin still owns refusal; no restored code runs.


def _own_guard(root, document):
    raw_current = _ordinary_bytes(root, SOURCE_RELATIVE)
    from tooling_recovery671_source_projection import current_source_before_tooling671
    raw = current_source_before_tooling671(SOURCE_RELATIVE, raw_current)
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + "0" * 64 + '"\n').encode()
    if (len(raw) != document["own_guard"]["bytes"] or raw.count(needle) != 1 or
            sha(raw.replace(needle, template, 1)) != document["own_guard"]["template_sha256"]):
        raise ValueError("Callback672 own guard differs from its exact singleton manifest-SHA template")
    return sha(raw_current)  # Qualified exact671 executable above the unchanged isolated callback singleton.


def current_contract_hashes(root: Path = ROOT):
    document = _document()
    from tooling_recovery671_source_projection import current_input_hashes as tooling_input_hashes
    return ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["added_inputs"] | document["immutable_inputs"] | tooling_input_hashes() |
            {SOURCE_RELATIVE: _own_guard(root, document), SPEC_RELATIVE: SPEC_SHA256})


def contract_input_paths():
    from tooling_recovery671_source_projection import fixture_inputs as tooling_fixture_inputs
    return BOUND_PATHS | ADDED_PATHS | IMMUTABLE_PATHS | {SOURCE_RELATIVE, SPEC_RELATIVE} | tooling_fixture_inputs()


def validate_current_sources(root: Path):
    import tooling_recovery671_source_projection as tooling
    tooling.validate_current_sources(root)
    document = _document()
    _own_guard(root, document)
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | document["immutable_inputs"] |
                {SPEC_RELATIVE: SPEC_SHA256})
    for relative, digest in expected.items():
        payload = tooling.source_before_tooling671(relative, _ordinary_bytes(root, relative))
        payload = tooling.callback_isolated_after_qualified_tooling671(relative, payload)
        if sha(payload) != digest:
            raise ValueError("Current callback672 source differs from its exact reviewed raw image: " + relative)
    return True


def input_digest(inputs):
    return sha(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode())


def _contract(inputs):
    return {"schema_version": 1, "focus": FOCUS, "verification_api_level": 35,
            "selector": CLASS + "#" + METHOD, "receiver_package": RECEIVER,
            "receiver_argument": "nativecmpkitOwnedCameraReceiver=true", "delayed_component": DELAYED_COMPONENT,
            "delayed_opt_in": "exact-focus-and-native-nonce-lease; default component remains disabled",
            "source_inputs": inputs, "source_inputs_sha256": input_digest(inputs),
            "source_policy_verified": True, "compiler_or_native_success_inferred": False}


def source_contract(root: Path):
    validate_current_sources(root)
    return _contract(current_contract_hashes(root))


def validate_source_contract(contract):
    if (type(contract) is not dict or type(contract.get("schema_version")) is not int or
            type(contract.get("verification_api_level")) is not int or contract.get("source_policy_verified") is not True or
            contract.get("compiler_or_native_success_inferred") is not False or
            contract != _contract(current_contract_hashes())):
        raise ValueError("Exact current callback672 source/recipient/delayed/selector contract is required")
    return True


def identities():
    return [{"classname": CLASS, "name": METHOD}]


def validate_discovery(suite, modules, focus, reviewed_camera_focuses, *,
                       declared_modules=None, minimum_modules=None):
    if suite != "android-device" or modules and MODULE not in modules or focus in reviewed_camera_focuses:
        return
    # Only library source discovery supplies the complete rejecting literal
    # include/rename/build map. An explicit declared non-Camera fixture minimum
    # cannot admit Camera or a default minimum; deleting its class is no escape.
    # The actual device/API controller supplies neither operand and stays strict.
    fixture_scope = (
        not modules and type(declared_modules) is tuple and bool(declared_modules) and
        all(type(module) is str and module for module in declared_modules) and
        len(declared_modules) == len(set(declared_modules)) and MODULE not in declared_modules and
        type(minimum_modules) is tuple and bool(minimum_modules) and
        all(type(module) is str and module for module in minimum_modules) and
        len(minimum_modules) == len(set(minimum_modules)) and MODULE not in minimum_modules and
        set(minimum_modules) <= set(declared_modules))
    if not fixture_scope:
        raise ValueError("Enabled API35-only callback requires exact finite Camera selection; unrestricted Camera/all discovery refuses before host work")


def validate_api(api, modules):
    if type(api) is not int or api != 35 or type(modules) is not tuple or modules != (MODULE,):
        raise ValueError("Callback substitution requires exact API35 and Camera-only class#method; no API23 or provider replay")


def validate_serial(serial):
    match = re.fullmatch(r"emulator-([1-9][0-9]{3})", serial) if type(serial) is str else None
    if match is None or not 5554 <= int(match[1]) <= 5682 or int(match[1]) % 2:
        raise ValueError("Callback requires the actual captured valid owned-emulator serial, never a guessed device")
    return True


def configure_item(root: Path, item: dict):
    native = _ordinary_bytes(root, SOURCE).decode("utf-8")
    declared = re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", native)
    if (declared != [METHOD] or "class AndroidCameraCallbackSubstitutionTest" not in native or
            "package com.mohamedrejeb.calf.camerapicker" not in native or
            re.search(r"@(Ignore|Disabled|IgnoredTest)\b|\b(?:assumeTrue|assumeFalse|Assume)\b", native) or
            item.get("test_source_files") != sorted(TEST_SOURCES) or item.get("test_source_sets") != TEST_SOURCE_SETS):
        raise ValueError("Callback requires its one enabled normally inherited method and exact complete source inputs; no pruning/skip")
    item["test_filter"] = CLASS + "#" + METHOD
    item["required_testcases"] = identities()
    item["required_original_xml"] = 1
    item[CONTRACT_KEY] = source_contract(root)


def validate_contract_placement(plan, reviewed_camera_focuses):
    focus = plan.get("explicit_test_focus")
    expected = plan.get("expected", [])
    if (focus != FOCUS and any(CONTRACT_KEY in item for item in expected) or
            plan.get("suite") == "android-device" and any(item.get("module") == MODULE for item in expected) and
            focus not in reviewed_camera_focuses):
        raise ValueError("No callback contract or unrestricted Camera discovery on unrelated/default/accepted plans")


def validate_plan(plan):
    expected = plan.get("expected")
    if (plan.get("suite") != "android-device" or plan.get("explicit_test_focus") != FOCUS or
            plan.get("complete_suite_requested") is not False or plan.get("explicit_module_subset") != [MODULE] or
            type(expected) is not list or len(expected) != 1):
        raise ValueError("Callback is one incomplete-suite Camera-only API35 plan")
    item, = expected
    if (item.get("module") != MODULE or item.get("project") != PROJECT or item.get("task") != TASK or
            item.get("report_directory") != REPORT_DIRECTORY or item.get("utp_results_directory") != REPORT_DIRECTORY or
            item.get("agp_declared_xml_directory") != DECLARED_XML_DIRECTORY or
            item.get("test_filter") != CLASS + "#" + METHOD or item.get("test_filter_argument") is not None or
            item.get("test_exclusion_annotation") is not None or item.get("required_original_xml") != 1 or
            type(item.get("required_original_xml")) is not int or item.get("required_testcases") != identities() or
            item.get("test_source_files") != sorted(TEST_SOURCES) or item.get("test_source_sets") != TEST_SOURCE_SETS):
        raise ValueError("Invalid exact callback class#method/source/fresh-report routing; broad/annotation/exclusion/provider substitution refuses")
    return validate_source_contract(item.get(CONTRACT_KEY))


def validate_context(context, serial):
    validate_serial(serial)
    host = context.get("host", {}) if type(context) is dict else {}
    emulator = context.get("android_emulator", {}) if type(context) is dict else {}
    if (type(host) is not dict or type(emulator) is not dict or host.get("system") != "Linux" or
            host.get("architecture") != "x64" or context.get("source_tree_dirty") is not False or
            type(context.get("source_revision")) is not str or re.fullmatch(r"[0-9a-f]{40}", context["source_revision"]) is None or
            emulator.get("serial") != serial or emulator.get("api_level") != "35" or emulator.get("abi") != "x86_64" or
            emulator.get("boot_completed") != "1" or emulator.get("selinux") != "Enforcing"):
        raise ValueError("Callback requires actual clean-source Linux x64 enforcing/booted API35 identity and same captured serial")
    return True


def outcomes(cases, host_system):
    exact = (type(cases) is list and len(cases) == 1 and type(cases[0]) is dict and
             {key: cases[0].get(key) for key in ("classname", "name")} == identities()[0] and cases[0].get("status") == "passed")
    errors = [] if exact else ["Callback XML requires exactly one NEW passed native case; no missing/duplicate/failed/skipped/provider/restoration substitution"]
    if host_system != "Linux":
        errors.append("Callback acceptance requires actual Linux API35 enforcing-emulator slot, never host-inapplicable skip")
    scenarios = [{**case, "source": SOURCE, "required_on_host": True, "verification_api_level": 35,
                  "disposition": "required-executed" if case.get("status") == "passed" else "required-not-passed"}
                 for case in cases]
    return scenarios, errors
