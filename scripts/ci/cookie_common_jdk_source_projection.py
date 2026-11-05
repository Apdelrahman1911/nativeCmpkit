# SPDX-License-Identifier: Apache-2.0
"""Finite cookie4 source/inverse custody. Never execute restored/native code.

This newest layer preserves the original WebView production/build pins and
680 launcher endpoint. Full imported HTTP-reader bytes are owning inputs, not
merely the cookie fixture's partial8+3 source witness. Compiler/native/ROOT
composition is deliberately not attested by this source-only context.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/cookie_common_jdk_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/cookie-common-jdk-source-inverse.json"
SPEC_SHA256 = "9445b6e7835fe81bec5b22f033f8e1c207dd639ff4d6b75df47ee51078e38a90"
ORIGINAL_SPEC = "scripts/ci/fixtures/webview-content-policy-routing-source-inverse.json"
ORIGINAL_SPEC_SHA256 = "c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916"
READER = "scripts/ci/webview_content_policy_fixture.py"
READER_SHA256 = "7ef8dfd4e8eee68a8d584e91d3ea231daa46b15a68f36cf762ee4409c8b4d571"
PREIMAGES = {
    "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt":
        "e1150ad896682e8ab1cc94042cace63917ab1e84d52dc7d70d840ea69ea4800f",
    "calf-webview/build.gradle.kts": "6e924d26f988f960ff828383a41901b79d7692d3eea6a07cb38230866b86e908",
    "scripts/ci/ios_ui_application.py": "b3d0f2c2986e42a5e662ba8c2521393f7564916e27084b9473c354b7328b9605",
    "scripts/ci/webview_content_policy_source_projection.py":
        "bb0b63b32a41667c0c33401f44873bd20426524ece52caaa3cfa41ffd880f60d",
}
ADDED_PATHS = frozenset({
    "calf-webview/karma.config.d/nativecmpkit-cookie-wire-fixture.js",
    "calf-webview/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/web/CookieHeaderMultiplicityTest.kt",
    "calf-webview/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/web/CookieWireContract.kt",
    "calf-webview/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/web/NativeCookieWireScenario.kt",
    "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopCookieRequestParityTest.kt",
    "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopCookieWireAcceptanceTest.kt",
    "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopCookieWireFixture.kt",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosCookieWireAcceptanceTest.kt",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosCookieWireFixture.kt",
    "calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserCookieWireAcceptanceTest.kt",
    "scripts/ci/cookie_native_wire_fixture.py", "scripts/ci/cookie_wire_material.py",
    "scripts/ci/fixtures/cookie-wire-v1.json",
    "scripts/ci/tests/test_cookie_wire_fixtures671.py",
    "scripts/ci/tests/test_cookie_wire_middleware671.cjs",
    "scripts/ci/cookie_common_jdk_plan.py", "scripts/ci/tests/test_cookie_common_jdk_scope681.py",
})
UNCHANGED_PATHS = frozenset({
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/Cookie.kt",
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieRules.kt",
    "calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt",
    "gradle/libs.versions.toml", "scripts/ci/test_webview_content_policy_fixture.py", READER,
    ORIGINAL_SPEC, "scripts/ci/fresh-tests.init.gradle.kts", "gradlew",
    "gradle/wrapper/gradle-wrapper.jar", "gradle/wrapper/gradle-wrapper.properties",
})
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 256 * 1024
_SCOPE = "Exact cookie common/JDK4 source custody and parked native/browser bodies; no compiler/native acceptance"
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


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
            raise ValueError("Duplicate cookie context field")
        result[key] = value
    return result


def _document(root: Path = ROOT):
    raw = ordinary_bytes(root, SPEC_RELATIVE, MAX_SPEC_BYTES)
    if sha(raw) != SPEC_SHA256:
        raise ValueError("Exact sealed cookie inverse manifest is required")
    try:
        document = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite cookie field")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("Complete finite cookie inverse JSON is required") from None
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "bindings", "added_inputs", "unchanged_inputs", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != _SCOPE or type(document["bindings"]) is not dict or
            set(document["bindings"]) != set(PREIMAGES) or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["unchanged_inputs"]) is not dict or set(document["unchanged_inputs"]) != UNCHANGED_PATHS):
        raise ValueError("Exact finite cookie inverse schema is required")
    for name, row in document["bindings"].items():
        if (type(row) is not dict or set(row) != {"before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                row["before_sha256"] != PREIMAGES[name] or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None
                    for key in ("before_sha256", "after_sha256")) or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES
                    for key in ("before_bytes", "after_bytes")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 8):
            raise ValueError("Exact owning cookie endpoint and finite fragments are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {"before", "after", "before_fragment_sha256", "after_fragment_sha256"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None for key in ("before_fragment_sha256", "after_fragment_sha256"))):
                raise ValueError("Exact nonempty cookie inverse fragments are required")
    for rows in (document["added_inputs"], document["unchanged_inputs"]):
        if any(type(digest) is not str or _DIGEST.fullmatch(digest) is None for digest in rows.values()):
            raise ValueError("Exact full cookie input hashes are required")
    if (document["unchanged_inputs"][READER] != READER_SHA256 or
            document["unchanged_inputs"][ORIGINAL_SPEC] != ORIGINAL_SPEC_SHA256):
        raise ValueError("Original WebView manifest and full imported reader pins must remain")
    own = document["own_guard"]
    source = ordinary_bytes(root, SOURCE_RELATIVE)
    import cookie_ci668_outer_source_projection as cookie_outer
    source = cookie_outer.current_source_before_cookie_outer(SOURCE_RELATIVE, source, root)
    line = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"').encode()
    if (type(own) is not dict or set(own) != {"bytes", "template_sha256"} or
            type(own["bytes"]) is not int or own["bytes"] != len(source) or
            type(own["template_sha256"]) is not str or _DIGEST.fullmatch(own["template_sha256"]) is None or
            source.count(line) != 1 or sha(source.replace(line, b'SPEC_SHA256 = "' + b'0' * 64 + b'"', 1)) != own["template_sha256"]):
        raise ValueError("Exact complete cookie guard source is required")
    return document


def source_before_cookie(relative: str, payload: bytes, root: Path = ROOT) -> bytes:
    """Exact inverse or its one historical preimage; never current admission."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact cookie relative identity and source bytes are required")
    import cookie_ci668_outer_source_projection as cookie_outer
    payload = cookie_outer._content_owner_source(relative, payload, root, current=False)
    row = _document(root)["bindings"].get(relative)
    if row is None:
        return payload  # Unlisted bytes are not certified.
    observed = sha(payload)
    if observed == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return payload
    if observed != row["after_sha256"] or len(payload) != row["after_bytes"]:
        raise ValueError("Only the complete cookie postimage can restore its original pin")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique cookie inverse fragment is required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != row["before_sha256"] or len(restored) != row["before_bytes"]:
        raise ValueError("Cookie inverse must restore the whole sealed preimage")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique cookie forward fragment is required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Whole cookie inverse/forward byte roundtrip is required")
    return restored


def current_source_before_cookie(relative: str, payload: bytes, root: Path = ROOT) -> bytes:
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact cookie current source identity is required")
    import cookie_ci668_outer_source_projection as cookie_outer
    payload = cookie_outer._content_owner_source(relative, payload, root, current=True)
    row = _document(root)["bindings"].get(relative)
    if row is not None and (sha(payload) != row["after_sha256"] or len(payload) != row["after_bytes"]):
        raise ValueError("Old or unknown bytes cannot substitute for current cookie source")
    return source_before_cookie(relative, payload, root)


def peel_cookie_for_history(relative: str, payload: bytes, root: Path = ROOT) -> bytes:
    """Transparent exact newest peel; no old/unknown current admission or replay."""
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact cookie history source identity is required")
    import cookie_ci668_outer_source_projection as cookie_outer
    payload = cookie_outer._content_owner_source(relative, payload, root, current=False)
    row = _document(root)["bindings"].get(relative)
    if row is not None and sha(payload) == row["after_sha256"]:
        return source_before_cookie(relative, payload, root)
    return payload  # Old/unknown bytes still require the caller's unchanged strict pin.


def validate_current_sources(root: Path = ROOT) -> dict:
    import cookie_ci668_outer_source_projection as cookie_outer
    cookie_outer.validate_current_sources(root)
    document = _document(root)
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})
    current = {}
    for name, digest in expected.items():
        payload = ordinary_bytes(root, name)
        comparison = cookie_outer._content_owner_source(name, payload, root, current=True)
        comparison = cookie_outer.cookie681_control_for_old_cookie_comparison(name, comparison, root)
        comparison = cookie_outer.callback672_init_for_old_cookie_comparison(name, comparison, root)
        if sha(comparison) != digest:
            raise ValueError("Exact current cookie source input changed: " + name)
        current[name] = sha(payload)
    original = json.loads(ordinary_bytes(root, ORIGINAL_SPEC))
    for name in ("calf-webview/build.gradle.kts",
                 "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt"):
        if original["unchanged_inputs"].get(name) != PREIMAGES[name]:
            raise ValueError("Cookie context cannot rewrite original WebView production/build pins")
        source_before_cookie(name, ordinary_bytes(root, name), root)
    return current | {SOURCE_RELATIVE: sha(ordinary_bytes(root, SOURCE_RELATIVE))}


def fixture_inputs() -> set[str]:
    return set(PREIMAGES) | set(ADDED_PATHS) | set(UNCHANGED_PATHS) | {SOURCE_RELATIVE, SPEC_RELATIVE}
