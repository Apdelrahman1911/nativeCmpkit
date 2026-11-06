# SPDX-License-Identifier: Apache-2.0
"""One IO665 raw source ingress above the exact accepted667 plus UI664 endpoint.

The predecessor is the lead's real afc0 UI13 integration commit above044d;
complete bound preimages retain exactly its accepted667 plus UI664 source bytes.
Neither that source map nor this finite inverse is a compiler/native map. Only
ordinary bytes and inverse/forward arithmetic are used; restored source is never executed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

# Only the actual current helper module is imported here. The three pure
# inverse/history functions below never import or execute reconstructed code.
import tooling_recovery671_source_projection as tooling671

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/android_io_remote_routing_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/android-io-controlled-remote-routing-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/android-io-controlled-remote-routing-source-inverse.json"
SPEC_SHA256 = "4dee514d6aa6bdfaf5856a24416cfb7a677f67daeed9f7fed9b43215e31e95de"
PREDECESSOR = "afc0a727f60a9278c96cf9721157ba7413229c10"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
# The latest UI companion alone composes these current/history hooks. All
# dated UI/667/659 manifest identities and original assertions stay unchanged.
BOUND_PATHS = {
    ".github/workflows/gradle.yml",
    "calf-io/src/androidDeviceTest/AndroidManifest.xml",
    "scripts/ci/android_device_tests.py",
    "scripts/ci/android_io_documents.py",
    "scripts/ci/ios_ui_split664_source_projection.py",
    "scripts/ci/library_tests.py",
    "scripts/ci/test_android_io_reporter_manifest_union.py",
    "scripts/ci/workflow_matrix.py",
}
ADDED_PATHS = {
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoRemoteDocumentsTest.kt",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoRemoteTreeGrantActivity.kt",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/RemoteIoEndpoint.kt",
    "docs/development/android-io-controlled-remote-provider.md",
    "scripts/ci/android_io_remote_documents.py",
    "scripts/ci/test_android_io_remote_documents.py",
    "scripts/ci/test_android_io_remote_routing.py",
    "scripts/ci/test_android_io_remote_routing_source_projection.py",
    "tests/consumer/android-io-remote-documents/README.md",
    "tests/consumer/android-io-remote-documents/build.gradle.kts",
    "tests/consumer/android-io-remote-documents/gradle.properties",
    "tests/consumer/android-io-remote-documents/settings.gradle.kts",
    "tests/consumer/android-io-remote-documents/src/main/AndroidManifest.xml",
    "tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoContract.java",
    "tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoControlService.java",
    "tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoDocumentsProvider.java",
    "tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoHttpBackend.java",
    "tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoHttpTransport.java",
    "tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoProviderWitnessService.java",
}
UNCHANGED_PATHS = {
    "calf-io/build.gradle.kts",
    "gradle/libs.versions.toml",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoSystemTreeGrantActivity.kt",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/DeviceDescriptorProbe.kt",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/NamedSystemDocumentsUi.kt",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/OwnedIoEndpoint.kt",
    "calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt",
    "calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFileBookmark.android.kt",
    "calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFileSource.android.kt",
    "calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/BoundedRead.kt",
    "scripts/ci/android_geo_probe.py",
    "scripts/ci/android_share_recipient.py",
    "calf-ui/build.gradle.kts",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt",
    "scripts/ci/fixtures/ios-ui-split664-source-inverse.json",
    "scripts/ci/ios_ui_application.py",
    "scripts/ci/ios_ui_related_native_focus.py",
    "scripts/ci/ios_ui_split_native.init.gradle.kts",
    "scripts/ci/test_ios_ui_related_source_projection.py",
    "scripts/ci/test_ios_ui_split664_native_routing.py",
    "scripts/ci/webview_current_contract667_source_projection.py",
}
SCOPE = "Exact controlled-loopback IO routing/source/history custody only; no compiler/native/consumer acceptance"
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_REVISION = re.compile(r"[0-9a-f]{40}\Z")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate remote IO source manifest field")
        result[name] = value
    return result


def _document():
    if _REVISION.fullmatch(PREDECESSOR) is None or SPEC_SHA256 == "0" * 64:
        raise ValueError("The lead-integrated remote IO predecessor/manifest is not frozen")
    from ios_popover_anchor_plan import _ordinary_bytes
    before = SPEC_PATH.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded remote IO source manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact remote IO source manifest changed")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite remote IO source manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("Complete remote IO source manifest JSON is required") from None
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "predecessor", "bindings", "added_inputs", "unchanged_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != SCOPE or document["predecessor"] != PREDECESSOR or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict or set(document["unchanged_inputs"]) != UNCHANGED_PATHS or
            type(document["own_guard"]) is not dict or set(document["own_guard"]) != {"template_sha256", "bytes"} or
            type(document["own_guard"]["bytes"]) is not int or not 0 < document["own_guard"]["bytes"] <= MAX_SOURCE_BYTES or
            type(document["own_guard"]["template_sha256"]) is not str or
            _DIGEST.fullmatch(document["own_guard"]["template_sha256"]) is None or
            BOUND_PATHS & ADDED_PATHS or BOUND_PATHS & UNCHANGED_PATHS or ADDED_PATHS & UNCHANGED_PATHS or
            {SOURCE_RELATIVE, SPEC_RELATIVE} & (BOUND_PATHS | ADDED_PATHS | UNCHANGED_PATHS)):
        raise ValueError("The exact finite remote IO source manifest schema is required")
    for name, row in document["bindings"].items():
        if (type(row) is not dict or set(row) != {"before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 64):
            raise ValueError("Exact complete remote IO source bindings are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                    "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite remote IO source fragment identities are required")
    for rows in (document["added_inputs"], document["unchanged_inputs"]):
        if any(type(name) is not str or type(digest) is not str or _DIGEST.fullmatch(digest) is None
               for name, digest in rows.items()):
            raise ValueError("Exact remote IO ordinary input hashes are required")
    return document


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact remote IO relative identity and ordinary source bytes are required")


def source_before_remote_routing(relative, payload):
    """One exact complete inverse or frozen predecessor; never current admission."""
    _identity(relative, payload)
    payload = tooling671.peel_tooling671_for_history(relative, payload)
    payload = tooling671.peel_callback_composition680_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload  # Unlisted bytes are not certified, reconstructed or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded complete remote IO source bytes are required")
    observed = sha(payload)
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("Remote IO source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact finite unique remote IO inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != binding["before_sha256"] or len(restored) != binding["before_bytes"]:
        raise ValueError("Remote IO inverse did not restore the complete frozen predecessor")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact finite unique remote IO forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Remote IO complete inverse/forward source roundtrip differs")
    return restored


def current_source_before_remote_routing(relative, payload):
    """One strict671 raw ingress, then qualified callback/IO ancestors; never two current admissions."""
    _identity(relative, payload)
    payload = tooling671.current_source_before_tooling671(relative, payload)
    payload = tooling671.source_before_callback_composition680(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and (sha(payload) != binding["after_sha256"] or len(payload) != binding["after_bytes"]):
        raise ValueError("An old or unknown image cannot replace exact current remote IO source")
    return source_before_remote_routing(relative, payload)


def peel_remote_routing_for_history(relative, payload):
    """Peel only exact671/composed680/IO afterimages; older pins own other bytes."""
    _identity(relative, payload)
    payload = tooling671.peel_tooling671_for_history(relative, payload)
    payload = tooling671.peel_callback_composition680_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and sha(payload) == binding["after_sha256"]:
        return source_before_remote_routing(relative, payload)
    return payload  # Unknown/prior pass-through is never current certification.  # Unknown/prior pass-through is never current certification.


def _validate_own_guard(root, document):
    """Qualify exact671 raw executable before the unchanged sealed IO singleton."""
    from ios_popover_anchor_plan import _ordinary_bytes
    raw_current = _ordinary_bytes(root, SOURCE_RELATIVE)[0]
    from tooling_recovery671_source_projection import current_source_before_tooling671
    raw = current_source_before_tooling671(SOURCE_RELATIVE, raw_current)
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + "0" * 64 + '"\n').encode()
    if (not 0 < len(raw) <= MAX_SOURCE_BYTES or len(raw) != document["own_guard"]["bytes"] or
            raw.count(needle) != 1 or sha(raw.replace(needle, template, 1)) != document["own_guard"]["template_sha256"]):
        raise ValueError("Current remote IO own guard differs from its exact singleton template")
    return sha(raw_current)  # Exact current671 identity, not a relabelled historical guard.  # Qualified by the entire exact singleton template above.


def _expected(document):
    return ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})


def current_input_hashes():
    """Finite exact raw671/680/IO identities, with no call into older UI owners."""
    document = _document()
    from tooling_recovery671_source_projection import current_input_hashes as tooling_input_hashes
    return (_expected(document) | tooling_input_hashes() |
            {SOURCE_RELATIVE: _validate_own_guard(ROOT, document)})


def validate_current_sources(root: Path):
    """Qualify raw671 first; compare only complete qualified680/IO ancestor views."""
    # One fresh EXISTING owning custody scope qualifies documents once. Every
    # RAW operand is still read freshly; private row reuse never certifies a source
    # or skips any tooling or successful remote suffix validation below.
    import macos_share_ci668_composition as joint
    import tooling_recovery671_source_projection as tooling
    with joint._source_projection_operation(root) as operation:
        for relative in (*operation._raw_inputs743(root), joint.OWNER, joint.SPEC):
            maximum = joint.MAX_SPEC if relative == joint.SPEC else joint.MAX_SOURCE
            raw = joint._ordinary(root, relative, maximum)[0]
            operation._raw743(relative, raw, root)
        operation._validate_tooling(root)
    document = _document()
    _validate_own_guard(root, document)
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in _expected(document).items():
        payload = tooling.source_before_tooling671(name, _ordinary_bytes(root, name)[0])
        payload = tooling.source_before_callback_composition680(name, payload)
        if sha(payload) != digest:
            raise ValueError("Current remote IO input differs from its complete reviewed raw image: " + name)
    return True


def fixture_inputs():
    """Exactly finite IO plus671 custody; never candidate/compiler/native execution."""
    document = _document()
    from tooling_recovery671_source_projection import fixture_inputs as tooling_fixture_inputs
    return (set(document["bindings"]) | set(document["added_inputs"]) | set(document["unchanged_inputs"]) |
            {SPEC_RELATIVE, SOURCE_RELATIVE} | tooling_fixture_inputs())
