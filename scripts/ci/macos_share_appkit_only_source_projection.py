# SPDX-License-Identifier: Apache-2.0
"""Exact AppKit-only successor bytes; never restored-code or native execution.

The reviewed609 observations are a separate unchanged prerequisite. This layer
holds full importing source bytes and separates raw current admission from exact
ancestor peeling. Its own source/control hashes are independent seal operands.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SPEC = "scripts/ci/fixtures/macos-share-appkit-only-source-inverse.json"
OWNER = "scripts/ci/macos_share_appkit_only_source_projection.py"
SPEC_SHA256 = "fb8de8c2c61e2263d1d1221fa168877d077f251043d91b5ba05df4a40d6362f7"
SCOPE = "Exact AppKit6-only current CLI/source custody; zero native/JNI/Gradle acceptance"
BOUND = {"scripts/ci/library_tests.py", "scripts/ci/macos_share_appkit_lifecycle.py", "scripts/ci/macos_share_key_wait_observation.py"}
ADDED = {"scripts/ci/macos_share_appkit_only_route.py", "scripts/ci/test_macos_share_appkit_only_route607.py", "docs/testing/macos-share650-appkit-only.md"}
MAX_SOURCE = 4 * 1024 * 1024
MAX_READ = 64 * 1024 * 1024
MAX_SPEC = 512 * 1024
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def need(value, code):
    if not value:
        raise ValueError(code)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _path(relative):
    need(type(relative) is str and 0 < len(relative) <= 4096 and "\\" not in relative and
         not any(ord(c) < 32 for c in relative), "unsafe-AppKit-source-identity")
    path = PurePosixPath(relative)
    need(not path.is_absolute() and path.as_posix() == relative and
         all(part not in {"", ".", ".."} for part in path.parts), "unsafe-AppKit-source-identity")
    return path.parts


def _identity(value):
    return tuple(getattr(value, key) for key in
                 ("st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid", "st_size", "st_mtime_ns", "st_ctime_ns"))


def directory_identity(metadata):
    return tuple(getattr(metadata, key) for key in
                 ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid"))


def close_owned(descriptors, primary):
    """Each owned descriptor is independent; preserve any primary refusal."""
    failures = []
    for descriptor in reversed(descriptors):
        try:
            os.close(descriptor)
        except BaseException as error:
            failures.append(error)
    if failures:
        if primary is None:
            raise ValueError("owned-AppKit-descriptor-cleanup-refused") from None
        primary.add_note("Owned AppKit descriptor cleanup also refused; primary error preserved")


def open_directory(root: Path, relative: str, descriptors):
    """Descriptor-rooted ordinary existing directories; caller closes all FDs."""
    need(type(root) is type(Path()) and root.is_absolute() and root == root.resolve(strict=True),
         "ordinary-canonical-AppKit-root-required")
    parts = _path(relative) if relative else ()
    before = root.lstat()
    need(stat.S_ISDIR(before.st_mode), "ordinary-AppKit-root-required")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    descriptors.append(descriptor)
    need(directory_identity(before) == directory_identity(os.fstat(descriptor)), "AppKit-root-replaced")
    chain = [(root, descriptor, directory_identity(before))]
    path = root
    for component in parts:
        metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
        need(stat.S_ISDIR(metadata.st_mode), "ordinary-AppKit-parent-required")
        child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
        descriptors.append(child)
        need(directory_identity(metadata) == directory_identity(os.fstat(child)), "AppKit-parent-replaced")
        descriptor = child
        path = path / component
        chain.append((path, descriptor, directory_identity(metadata)))
    return descriptor, chain


def verify_directories(root, chain):
    need(root == root.resolve(strict=True), "AppKit-root-path-custody-changed")
    for path, descriptor, identity in chain:
        current = path.lstat()
        need(stat.S_ISDIR(current.st_mode) and
             directory_identity(current) == identity == directory_identity(os.fstat(descriptor)),
             "AppKit-directory-path-custody-changed")


def ordinary_bytes(root: Path, relative: str, maximum: int = MAX_SOURCE):
    """Stable descriptor-rooted read; recheck every parent and close owned FDs."""
    need(type(maximum) is int and 0 < maximum <= MAX_READ, "bounded-AppKit-read-required")
    parts, descriptors = _path(relative), []
    primary = None
    try:
        parent_relative = "/".join(parts[:-1])
        parent, chain = open_directory(root, parent_relative, descriptors)
        before = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
             "bounded-ordinary-unaliased-AppKit-file-required")
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        descriptors.append(leaf)
        need(_identity(before) == _identity(os.fstat(leaf)), "AppKit-file-replaced-before-read")
        chunks, total = [], 0
        while True:
            piece = os.read(leaf, min(131072, maximum + 1 - total))
            if not piece:
                break
            chunks.append(piece)
            total += len(piece)
            need(total <= maximum, "AppKit-file-read-bound-exceeded")
        payload = b"".join(chunks)
        after = os.fstat(leaf)
        final = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        path_after = (root / relative).lstat()
        verify_directories(root, chain)
        need(_identity(before) == _identity(after) == _identity(final) == _identity(path_after) and
             len(payload) == before.st_size, "AppKit-read-path-or-file-custody-changed")
        identity = {"device": before.st_dev, "inode": before.st_ino, "mode": before.st_mode,
                    "size": len(payload), "mtime_ns": before.st_mtime_ns, "sha256": sha(payload)}
        return payload, identity
    except BaseException as error:
        primary = error
        raise
    finally:
        close_owned(descriptors, primary)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "duplicate-AppKit-source-manifest-field")
        result[key] = value
    return result


def json_bytes(payload):
    try:
        value = json.loads(payload, object_pairs_hook=_unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite-AppKit-JSON")))
        pending = [(value, 0)]
        while pending:
            child, depth = pending.pop()
            need(depth <= 64, "bounded-AppKit-JSON-depth-required")
            if type(child) is dict:
                pending.extend((item, depth + 1) for item in child.values())
            elif type(child) is list:
                pending.extend((item, depth + 1) for item in child)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("bounded-complete-AppKit-JSON-required") from None


def _document(root=ROOT):
    raw = ordinary_bytes(root, SPEC, MAX_SPEC)[0]
    need(0 < len(raw) <= MAX_SPEC and sha(raw) == SPEC_SHA256, "exact-AppKit-only-manifest-required")
    document = json_bytes(raw)
    need(type(document) is dict and set(document) == {"schema_version", "scope", "bindings", "added_inputs", "unchanged_inputs", "predecessor609"} and
         type(document["schema_version"]) is int and document["schema_version"] == 1 and
         document["scope"] == SCOPE and type(document["bindings"]) is dict and set(document["bindings"]) == BOUND and
         type(document["added_inputs"]) is dict and set(document["added_inputs"]) == ADDED and
         type(document["unchanged_inputs"]) is dict and 0 < len(document["unchanged_inputs"]) <= 64,
         "finite-complete-AppKit-only-manifest-required")
    predecessor = document["predecessor609"]
    need(predecessor == {"seal_sha256": "7a1d599ee6b1d79e215fb2dea1d1802bcd49ac2373e870be908517c5248133b3",
                        "manifest_sha256": "dd5872cb1a7e23beb064dfcad7ef10544e0b547d734498b564dd73ae5ee3a0e6",
                        "native_cause_verified": False, "native_readiness_fix_included": False},
         "exact-observation609-predecessor-required")
    need(type(predecessor["native_cause_verified"]) is bool and type(predecessor["native_readiness_fix_included"]) is bool,
         "exact-observation609-Boolean-gates-required")
    for name, row in document["bindings"].items():
        _path(name)
        need(type(row) is dict and set(row) == {"before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} and
             all(type(row[k]) is str and DIGEST.fullmatch(row[k]) for k in ("before_sha256", "after_sha256")) and
             all(type(row[k]) is int and 0 < row[k] <= MAX_SOURCE for k in ("before_bytes", "after_bytes")) and
             type(row["fragments"]) is list and 0 < len(row["fragments"]) <= 12,
             "exact-AppKit-only-bindings-required")
        for fragment in row["fragments"]:
            need(type(fragment) is dict and set(fragment) == {"before", "after", "before_fragment_sha256", "after_fragment_sha256"} and
                 all(type(fragment[k]) is str and 0 < len(fragment[k].encode()) <= MAX_SOURCE for k in fragment) and
                 all(DIGEST.fullmatch(fragment[k]) for k in ("before_fragment_sha256", "after_fragment_sha256")),
                 "exact-AppKit-only-fragments-required")
    for mapping in (document["added_inputs"], document["unchanged_inputs"]):
        for name, digest in mapping.items():
            _path(name)
            need(type(digest) is str and DIGEST.fullmatch(digest), "exact-AppKit-only-input-digest-required")
    need(not (set(document["bindings"]) & set(document["added_inputs"]) or
              set(document["bindings"]) & set(document["unchanged_inputs"]) or
              set(document["added_inputs"]) & set(document["unchanged_inputs"])), "disjoint-AppKit-only-inputs-required")
    return document


def source_before_appkit_only(relative, payload, root=ROOT):
    need(type(relative) is str and type(payload) is bytes, "exact-AppKit-only-source-operand-required")
    import macos_share_ci668_composition as latest
    payload = latest.peel_for_history(relative, payload, latest.SHARE_VIEW, root)
    row = _document(root)["bindings"].get(relative)
    if row is None:
        return payload
    if sha(payload) == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return payload
    need(sha(payload) == row["after_sha256"] and len(payload) == row["after_bytes"], "complete-AppKit-only-postimage-required")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        need(sha(before) == fragment["before_fragment_sha256"] and sha(after) == fragment["after_fragment_sha256"] and
             restored.count(after) == 1, "unique-AppKit-only-inverse-required")
        restored = restored.replace(after, before, 1)
    need(sha(restored) == row["before_sha256"] and len(restored) == row["before_bytes"], "complete-AppKit-only-preimage-required")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        need(forward.count(before) == 1, "unique-AppKit-only-forward-required")
        forward = forward.replace(before, after, 1)
    need(forward == payload, "complete-AppKit-only-roundtrip-required")
    return restored


def current_source_before_appkit_only(relative, payload, root=ROOT):
    import macos_share_ci668_composition as latest
    payload = latest.current_source_in_view(relative, payload, latest.SHARE_VIEW, root)
    row = _document(root)["bindings"].get(relative)
    if row is not None:
        need(type(payload) is bytes and sha(payload) == row["after_sha256"] and len(payload) == row["after_bytes"],
             "old-or-unknown-AppKit-only-source-is-not-current")
    return source_before_appkit_only(relative, payload, root)


def peel_appkit_only_for_history(relative, payload, root=ROOT):
    need(type(relative) is str and type(payload) is bytes, "exact-AppKit-only-history-operand-required")
    import macos_share_ci668_composition as latest
    payload = latest.peel_for_history(relative, payload, latest.SHARE_VIEW, root)
    row = _document(root)["bindings"].get(relative)
    if row is not None and sha(payload) == row["after_sha256"]:
        return source_before_appkit_only(relative, payload, root)
    return payload


def expected_inputs(root=ROOT):
    document = _document(root)
    return ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["added_inputs"] | document["unchanged_inputs"] | {SPEC: SPEC_SHA256})


def validate_current_sources(root=ROOT):
    import macos_share_ci668_composition as latest
    latest.validate_current_sources(root)
    expected = expected_inputs(root)
    for name, digest in expected.items():
        raw = ordinary_bytes(root, name)[0]
        accepted = latest.current_source_in_view(name, raw, latest.SHARE_VIEW, root)
        need(sha(accepted) == digest, "complete-current-AppKit-only-source-input-differs")
    # The newest own guard is sealed before its exact independently sealed607 ancestor.
    raw = ordinary_bytes(root, OWNER)[0]
    latest.current_source_in_view(OWNER, raw, latest.SHARE_VIEW, root)
    return latest.current_input_hashes(root)


def fixture_inputs(root=ROOT):
    import macos_share_ci668_composition as latest
    return set(expected_inputs(root)) | {OWNER} | latest.fixture_inputs(root)
