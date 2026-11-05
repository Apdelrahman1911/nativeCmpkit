# SPDX-License-Identifier: Apache-2.0
"""Exact newest Cookie source composition before final CI668 and shared671.

Only complete literal source inverses are returned, never imported or executed.
The callback672 init inverse is a separately named old-Cookie comparison view;
actual init/compiler bytes and final CI175's current e0c82 pin remain untouched.
One named original681 owning-control comparison preserves its exact29da pin
after newest raw40 qualification; generic history never peels that control.
This source-only derivative does not qualify execution, native, issues or release.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/cookie_ci668_outer_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/cookie-ci668-outer-source-inverse.json"
NEW_CONTROL_RELATIVE = "scripts/ci/tests/test_cookie_ci668_outer_scope609.py"
OWNING_CONTROL_RELATIVE = "scripts/ci/tests/test_cookie_common_jdk_scope681.py"
OWNING_CONTROL_BEFORE_SHA256 = "29da5e6de99b7a91cae2603b09f2f02fc3433982f3bebf5a69b21658977dbc42"
SPEC_SHA256 = "5fc3e645636f9ab3109933fb9bfa5c8abf243b9ea8d9804d73ce3179fcabb14f"
COOKIE_GUARD = "scripts/ci/cookie_common_jdk_source_projection.py"
COOKIE_GUARD_BEFORE_SHA256 = "b5eca01bbbe89e584b18279cb15aa36a8d1e06d205a2c4fcd52d24b271e55774"
COOKIE_SPEC = "scripts/ci/fixtures/cookie-common-jdk-source-inverse.json"
COOKIE_SPEC_SHA256 = "9445b6e7835fe81bec5b22f033f8e1c207dd639ff4d6b75df47ee51078e38a90"
CI_GUARD = "scripts/ci/ci668_outer_source_projection.py"
CI_GUARD_BEFORE_SHA256 = "57ea22a07713ee542a14f8d57338767f57e6cab4e2133a14b8096f9269e18337"
CI_SPEC = "scripts/ci/fixtures/ci668-outer-source-inverse.json"
CI_SPEC_SHA256 = "bbfdb2454182ce8c1fc90e793c3552e49f317b35437b61fcd3e8743b86f9d86e"
LIBRARY = "scripts/ci/library_tests.py"
LIBRARY_BEFORE_SHA256 = "ddd7b38615bef7ec99bfefddb625bf0816d9c90c297604d7baaea898a6e90aa6"
LIBRARY_AFTER_SHA256 = "038ffa83f883f24396b35103edafa47a9b4a13fe4df6faf88175e56768819299"
LIBRARY_BINDING_SHA256 = "75af51470b712c646d68d22d40ee5a315b077266babe52cc42c96de4eb809fb3"
CALLBACK_SPEC = "scripts/ci/fixtures/android-camera-callback672-source-inverse.json"
CALLBACK_SPEC_SHA256 = "1c14d6fcb7dc49716de3688169c9280fde51f62564d1593a6a95707f85f19f7a"
INIT = "scripts/ci/fresh-tests.init.gradle.kts"
INIT_OLD_COOKIE_SHA256 = "bc14e3ac5105e6a337c896f4f7e88dd565e8862b2b2dc0d8ff055f40ab8cb9d4"
INIT_CURRENT_SHA256 = "e0c82a5c9c2461e5e18ce4e71e495c5cbdf5f3694d2bd19bbfbe855134112ffb"
READER = "scripts/ci/webview_content_policy_fixture.py"
READER_SHA256 = "7ef8dfd4e8eee68a8d584e91d3ea231daa46b15a68f36cf762ee4409c8b4d571"
COOKIE_BOUND_PATHS = frozenset({
    "calf-webview/build.gradle.kts",
    "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt",
    "scripts/ci/ios_ui_application.py",
    "scripts/ci/webview_content_policy_source_projection.py",
})
OUTER_FRAGMENT_COUNTS = {CI_GUARD: 7, COOKIE_GUARD: 2}
BOUND_PATHS = COOKIE_BOUND_PATHS | set(OUTER_FRAGMENT_COUNTS)
CONTEXT_RECEIPTS = {
    "original_cookie671_seal_sha256": "52bd4d7b6606d26cd43107eba5c591e8e1d9341f487f913322fe61ad4b68f2a3",
    "original_cookie671_inventory_sha256": "6eba191a671d6cb8b8851d297aaf5562421699fc52460d7453087a62cfc6a4f6",
    "accepted_cookie681_seal_sha256": "17c34286f45f25d9fc3e2dc84527a319b5b6863dabf1d19cc387b7b273883a69",
    "accepted_cookie681_inventory_sha256": "717fb1aeef1825778c4d4ec8c762483bf53d4d8ea4d68bae0861dedb666439ec",
    "final_ci676_recipe_sha256": "3f451e495617c830a7cadcbacffd2fc4061ba0b95ea5372c11726fefc6bb1a51",
    "lead680_existing_integration_result_sha256": "f1703531c4e54459475e4d6087ad711f8504da9776e7ab71a2454b006e9f3c97",
    "accepted_prerequisites609_seal_sha256": "73d7202190911173fdeb82e8add2b380c2f72e7cd53c716bcdb969cd3c6da27b",
    "accepted_prerequisites609_new8_result_sha256": "f17b616dc177d26645daeb21a11c8dcd90bb85ba8e9fea4e002989b3d990e56a",
    "share607_library_source_seal_sha256": "32b60ee8cff7d6cea93ffd65906fa082cbfbd0b6c4ddef7628a0cc14a035970d",
    "share607_library_source_manifest_sha256": "fb8de8c2c61e2263d1d1221fa168877d077f251043d91b5ba05df4a40d6362f7",
}
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SCOPE = "Exact Cookie681 after-only source peel before final CI668/shared671 and exact Share607 library payload ancestry, plus named callback672 init and owning-control681 comparisons after strict raw40 custody; no runtime/native/results/closure acceptance"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def ordinary_bytes(root: Path, relative: str, limit: int = MAX_SOURCE_BYTES) -> bytes:
    """One bounded stable ordinary checkout file; no symlink/hardlink fallback."""
    if (not isinstance(root, Path) or not root.is_absolute() or root != root.resolve(strict=True) or
            type(relative) is not str or not relative or Path(relative).is_absolute() or
            any(part in ("", ".", "..") for part in relative.split("/")) or
            type(limit) is not int or not 0 < limit <= MAX_SOURCE_BYTES):
        raise ValueError("Exact ordinary cookie checkout path is required")
    flags = getattr(os, "O_NOFOLLOW", None)
    directories = getattr(os, "O_DIRECTORY", None)
    if flags is None or directories is None or os.name != "posix":
        raise ValueError("Cookie source lease requires a separately qualified platform file provider")
    fds = []
    entries = []
    failure = None
    try:
        fds.append(os.open(root, os.O_RDONLY | flags | directories))
        parts = relative.split("/")
        for part in parts[:-1]:
            parent = fds[-1]
            fds.append(os.open(part, os.O_RDONLY | flags | directories, dir_fd=parent))
            entries.append((parent, part, fds[-1]))
        parent = fds[-1]
        fd = os.open(parts[-1], os.O_RDONLY | flags, dir_fd=parent)
        fds.append(fd)
        entries.append((parent, parts[-1], fd))
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_uid != os.getuid() or
                not 0 < before.st_size <= limit):
            raise ValueError("One owned regular bounded cookie source file is required")
        payload = bytearray()
        while len(payload) <= limit:
            part = os.read(fd, min(65536, limit + 1 - len(payload)))
            if not part:
                break
            payload.extend(part)
        after = os.fstat(fd)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mode, s.st_uid,
                              s.st_nlink, s.st_mtime_ns, s.st_ctime_ns)
        if identity(before) != identity(after) or len(payload) != before.st_size or len(payload) > limit:
            raise ValueError("Stable complete cookie source bytes are required")
        path_identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_uid)
        if path_identity(root.lstat()) != path_identity(os.fstat(fds[0])):
            raise ValueError("Cookie checkout root ownership changed during the read")
        for parent, component, opened in entries:
            if path_identity(os.stat(component, dir_fd=parent, follow_symlinks=False)) != path_identity(os.fstat(opened)):
                raise ValueError("Cookie source path ownership changed during the read")
        return bytes(payload)
    except BaseException as error:
        failure = error
        raise
    finally:
        cleanup = None
        for fd in reversed(fds):
            try:
                os.close(fd)
            except BaseException as error:
                if failure is not None:
                    failure.add_note("Independent cookie source descriptor cleanup also failed: " + type(error).__name__)
                elif cleanup is None:
                    cleanup = error
                else:
                    cleanup.add_note("Independent cookie source descriptor cleanup also failed: " + type(error).__name__)
        if failure is None and cleanup is not None:
            raise cleanup


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate exact Cookie outer field")
        result[key] = value
    return result


def _parse(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite Cookie outer field")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("Complete finite Cookie outer JSON is required") from None


def _row_shape(row, *, fragment_count=None, callback=False):
    if (type(row) is not dict or set(row) != {
            "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
            any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None
                for key in ("before_sha256", "after_sha256")) or
            any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES
                for key in ("before_bytes", "after_bytes")) or
            type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 8 or
            fragment_count is not None and len(row["fragments"]) != fragment_count):
        raise ValueError("Exact finite Cookie outer source endpoints are required")
    fields = {"before", "after", "before_fragment_sha256", "after_fragment_sha256"}
    if callback:
        fields.add("obligation")
    for fragment in row["fragments"]:
        if (type(fragment) is not dict or set(fragment) != fields or
                any(type(value) is not str or not value for value in fragment.values()) or
                fragment["before"] == fragment["after"] or
                any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after")) or
                any(_DIGEST.fullmatch(fragment[key]) is None
                    for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                sha(fragment["before"].encode()) != fragment["before_fragment_sha256"] or
                sha(fragment["after"].encode()) != fragment["after_fragment_sha256"]):
            raise ValueError("Exact bounded Cookie outer fragment identities are required")


def _document(root: Path = ROOT):
    raw = ordinary_bytes(root, SPEC_RELATIVE, MAX_SPEC_BYTES)
    if sha(raw) != SPEC_SHA256:
        raise ValueError("Exact newest Cookie outer manifest is required")
    document = _parse(raw)
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "context_receipts", "accepted_cookie_inputs",
            "bindings", "callback672_init_binding", "cookie681_control_binding", "share607_library_binding", "new_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != _SCOPE or document["context_receipts"] != CONTEXT_RECEIPTS or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["accepted_cookie_inputs"]) is not dict or
            type(document["new_inputs"]) is not dict or set(document["new_inputs"]) != {NEW_CONTROL_RELATIVE} or
            any(type(digest) is not str or _DIGEST.fullmatch(digest) is None
                for digest in document["new_inputs"].values())):
        raise ValueError("Exact newest finite Cookie outer schema is required")
    old_raw = ordinary_bytes(root, COOKIE_SPEC, MAX_SPEC_BYTES)
    callback_raw = ordinary_bytes(root, CALLBACK_SPEC, MAX_SPEC_BYTES)
    ci_raw = ordinary_bytes(root, CI_SPEC, MAX_SPEC_BYTES)
    if (sha(old_raw) != COOKIE_SPEC_SHA256 or sha(callback_raw) != CALLBACK_SPEC_SHA256 or
            sha(ci_raw) != CI_SPEC_SHA256):
        raise ValueError("Original Cookie/CI/callback manifests must remain byte-exact")
    cookie = _parse(old_raw)
    callback = _parse(callback_raw)
    accepted = ({name: row["after_sha256"] for name, row in cookie["bindings"].items()} |
                cookie["added_inputs"] | cookie["unchanged_inputs"] |
                {COOKIE_SPEC: COOKIE_SPEC_SHA256, COOKIE_GUARD: COOKIE_GUARD_BEFORE_SHA256})
    if (len(accepted) != 34 or document["accepted_cookie_inputs"] != accepted or
            set(cookie["bindings"]) != COOKIE_BOUND_PATHS or
            accepted[READER] != READER_SHA256 or accepted[INIT] != INIT_OLD_COOKIE_SHA256):
        raise ValueError("The unchanged original Cookie34 and full reader pins are required")
    for relative, row in document["bindings"].items():
        _row_shape(row, fragment_count=OUTER_FRAGMENT_COUNTS.get(relative))
        if relative in COOKIE_BOUND_PATHS and row != cookie["bindings"][relative]:
            raise ValueError("Original Cookie4/10 inverse rows cannot be rewritten")
    for relative, digest in ((COOKIE_GUARD, COOKIE_GUARD_BEFORE_SHA256), (CI_GUARD, CI_GUARD_BEFORE_SHA256)):
        if document["bindings"][relative]["before_sha256"] != digest:
            raise ValueError("Only exact accepted Cookie/final CI guard hook preimages are declared")
    library = document["share607_library_binding"]
    _row_shape(library, fragment_count=2)
    library_raw = (json.dumps(library, indent=2, sort_keys=True) + "\n").encode()
    if (sha(library_raw) != LIBRARY_BINDING_SHA256 or
            library["before_sha256"] != LIBRARY_BEFORE_SHA256 or
            library["after_sha256"] != LIBRARY_AFTER_SHA256):
        raise ValueError("Only exact independently sealed Share607 library payload ancestry is declared")
    init = document["callback672_init_binding"]
    _row_shape(init, fragment_count=1, callback=True)
    if (init != callback["bindings"].get(INIT) or init["before_sha256"] != INIT_OLD_COOKIE_SHA256 or
            init["after_sha256"] != INIT_CURRENT_SHA256 or init["before_bytes"] != 7940 or
            init["after_bytes"] != 9304):
        raise ValueError("Only the exact named callback672 init comparison is declared")
    control = document["cookie681_control_binding"]
    _row_shape(control, fragment_count=3)
    if (accepted.get(OWNING_CONTROL_RELATIVE) != OWNING_CONTROL_BEFORE_SHA256 or
            control["before_sha256"] != OWNING_CONTROL_BEFORE_SHA256 or
            control["before_bytes"] != 14205):
        raise ValueError("Only the exact named original681 owning-control predecessor is declared")
    source = ordinary_bytes(root, SOURCE_RELATIVE)
    own = document["own_guard"]
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"').encode()
    zero = b'SPEC_SHA256 = "' + b'0' * 64 + b'"'
    if (type(own) is not dict or set(own) != {"bytes", "template_sha256"} or
            type(own["bytes"]) is not int or own["bytes"] != len(source) or
            type(own["template_sha256"]) is not str or _DIGEST.fullmatch(own["template_sha256"]) is None or
            source.count(needle) != 1 or sha(source.replace(needle, zero, 1)) != own["template_sha256"]):
        raise ValueError("Exact complete newest Cookie outer guard template is required")
    if sha(ordinary_bytes(root, NEW_CONTROL_RELATIVE)) != document["new_inputs"][NEW_CONTROL_RELATIVE]:
        raise ValueError("Exact complete NEW8 Cookie outer derivative control source is required")
    return document, sha(source)


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact Cookie outer relative identity and source bytes are required")


def _restore(row, payload):
    if sha(payload) == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return payload
    if sha(payload) != row["after_sha256"] or len(payload) != row["after_bytes"]:
        raise ValueError("Only an exact complete Cookie outer endpoint can restore its source pin")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or
                sha(after) != fragment["after_fragment_sha256"] or restored.count(after) != 1):
            raise ValueError("Exact unique Cookie outer inverse fragment is required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != row["before_sha256"] or len(restored) != row["before_bytes"]:
        raise ValueError("Cookie outer inverse must restore the complete declared preimage")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique Cookie outer forward fragment is required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Whole Cookie outer inverse/forward source roundtrip is required")
    return restored


def source_before_cookie_outer(relative, payload, root: Path = ROOT):
    """Exact Cookie/hook inverse or its one historical preimage, not admission."""
    _identity(relative, payload)
    if relative == LIBRARY:
        from macos_share_ci668_composition import peel_android_lifecycle_for_history
        payload = peel_android_lifecycle_for_history(relative, payload, root)
    document, _ = _document(root)
    row = (document["share607_library_binding"] if relative == LIBRARY
           else document["bindings"].get(relative))
    return payload if row is None else _restore(row, payload)


def _expected(document, source_digest):
    # Original34 is held as historical context; these values are current RAW40.
    return (document["accepted_cookie_inputs"] |
            {name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["new_inputs"] |
            {OWNING_CONTROL_RELATIVE: document["cookie681_control_binding"]["after_sha256"],
             INIT: document["callback672_init_binding"]["after_sha256"],
             CI_SPEC: CI_SPEC_SHA256, CALLBACK_SPEC: CALLBACK_SPEC_SHA256,
             SPEC_RELATIVE: SPEC_SHA256, SOURCE_RELATIVE: source_digest})


def current_source_before_cookie_outer(relative, payload, root: Path = ROOT):
    """One strict newest raw ingress; old Cookie or pre-hook current refuses."""
    _identity(relative, payload)
    if relative == LIBRARY:
        from macos_share_ci668_composition import source_before_android_lifecycle
        payload = source_before_android_lifecycle(relative, payload, root)
    document, source_digest = _document(root)
    row = (document["share607_library_binding"] if relative == LIBRARY
           else document["bindings"].get(relative))
    digest = (row["after_sha256"] if relative == LIBRARY
              else _expected(document, source_digest).get(relative))
    if digest is not None and (sha(payload) != digest or row is not None and len(payload) != row["after_bytes"]):
        raise ValueError("Old or unknown bytes cannot substitute for exact current Cookie outer source")
    return payload if row is None else _restore(row, payload)


def peel_cookie_outer_for_history(relative, payload, root: Path = ROOT):
    """After-only Cookie/hook peel; callback init is deliberately NOT peeled."""
    _identity(relative, payload)
    if relative == LIBRARY:
        from macos_share_ci668_composition import peel_android_lifecycle_for_history
        payload = peel_android_lifecycle_for_history(relative, payload, root)
    document, _ = _document(root)
    row = (document["share607_library_binding"] if relative == LIBRARY
           else document["bindings"].get(relative))
    if row is not None and sha(payload) == row["after_sha256"] and len(payload) == row["after_bytes"]:
        return _restore(row, payload)
    return payload  # Pass-through is not source/current certification.


def callback672_init_for_old_cookie_comparison(relative, payload, root: Path = ROOT):
    """Only e0c82 RAW init -> bc14 old Cookie view after current qualification."""
    _identity(relative, payload)
    if relative != INIT:
        return payload  # No other source/IO/callback layer is searched or certified.
    document, _ = _document(root)
    row = document["callback672_init_binding"]
    if sha(payload) != row["after_sha256"] or len(payload) != row["after_bytes"]:
        raise ValueError("Only exact current callback672 init can serve an old Cookie comparison")
    return _restore(row, payload)


def cookie681_control_for_old_cookie_comparison(relative, payload, root: Path = ROOT):
    """Only current owning control -> exact29da predecessor after raw40 custody.

    This is not a generic peel or current admission. Returned literal bytes are
    never imported/executed. Callback init and every other source pass unchanged.
    """
    _identity(relative, payload)
    if relative != OWNING_CONTROL_RELATIVE:
        return payload  # No other control/source/init is searched or certified.
    validate_current_sources(root)
    document, _ = _document(root)
    row = document["cookie681_control_binding"]
    if sha(payload) != row["after_sha256"] or len(payload) != row["after_bytes"]:
        raise ValueError("Only exact current Cookie681 owning control can serve its predecessor comparison")
    return _restore(row, payload)


def validate_current_sources(root: Path = ROOT):
    """Only strict complete raw40 source custody; no API/test/native replay."""
    document, source_digest = _document(root)
    expected = _expected(document, source_digest)
    if len(expected) != 40:
        raise ValueError("Only the exact finite current Cookie40 context is declared")
    for relative, digest in expected.items():
        raw = ordinary_bytes(root, relative)
        if sha(raw) != digest:
            raise ValueError("Exact current Cookie outer input changed: " + relative)
    for relative, row in document["bindings"].items():
        _restore(row, ordinary_bytes(root, relative))
    _restore(document["cookie681_control_binding"], ordinary_bytes(root, OWNING_CONTROL_RELATIVE))
    callback672_init_for_old_cookie_comparison(INIT, ordinary_bytes(root, INIT), root)
    return expected


def current_input_hashes(root: Path = ROOT):
    """Return actual current raw40 pins, never old Cookie/init hashes as current."""
    return validate_current_sources(root)


def fixture_inputs():
    """Only finite current40 source inputs, never a native/engine/test selector."""
    document, source_digest = _document()
    return set(_expected(document, source_digest))
