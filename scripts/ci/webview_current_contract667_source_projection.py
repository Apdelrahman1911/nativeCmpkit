# SPDX-License-Identifier: Apache-2.0
"""Exact current WebView contract667 identities, never old owners as current.

The four finite derivatives restore the approved30db owner/control/guard inputs. The
owner then has its sealed659 predecessor and original WebView added-input
identity. Only source inverse/forward arithmetic is used; restored code, native
selectors, compilers, network and host queries are never executed here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = "scripts/ci/webview_current_contract667_source_projection.py"
SPEC_RELATIVE = "scripts/ci/fixtures/webview-current-contract667-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/webview-current-contract667-source-inverse.json"
SPEC_SHA256 = "56574379b6d9621e8b72009cad3551115401b860250f5c40af23bf3be279f937"
PREDECESSOR = "30db3ed785e13013b5de3939fdd6eb70b6d4b25a"
SOURCE = "scripts/ci/webview_content_policy_native_focus.py"
CONTROL_SOURCE = "scripts/ci/test_webview_content_policy_native_focus.py"
NEW_CONTROL = "scripts/ci/test_webview_current_contract667_source_projection.py"
PRIOR_GUARD = "scripts/ci/platform_recovery659_source_projection.py"
PRIOR_CONTROL = "scripts/ci/test_platform_recovery659_source_projection.py"
PRIOR_GUARD_SHA256 = "cb1af9a9ac2a7bc64afea2038a4055aa369c5d9002e504d52b6943db464e01f1"
ORIGINAL_SPEC = "scripts/ci/fixtures/webview-content-policy-routing-source-inverse.json"
PRIOR_SPEC = "scripts/ci/fixtures/platform-recovery659-source-inverse.json"
ORIGIN_MANIFESTS = {
    ORIGINAL_SPEC: "c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916",
    PRIOR_SPEC: "c9a56d4288e1d6a71914de27b0218d0877840136e9d24d448e2d192fcf7d90e9",
}
BOUND_PATHS = frozenset({SOURCE, CONTROL_SOURCE, PRIOR_GUARD, PRIOR_CONTROL})
ADDED_PATHS = frozenset({NEW_CONTROL})
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_SPEC_BYTES = 128 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SCOPE = "Exact WebView current owner contract667 custody only; no compiler/native acceptance"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate current WebView contract667 manifest field")
        result[key] = value
    return result


def _json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              ValueError("Nonfinite current WebView contract667 manifest")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The complete current WebView contract667 manifest JSON is required") from None


def _shape(document):
    if (type(document) is not dict or set(document) != {
            "schema_version", "scope", "predecessor", "bindings", "added_inputs", "origin_manifests", "own_guard"} or
            type(document["schema_version"]) is not int or document["schema_version"] != 1 or
            document["scope"] != _SCOPE or document["predecessor"] != PREDECESSOR or
            type(document["bindings"]) is not dict or set(document["bindings"]) != BOUND_PATHS or
            type(document["added_inputs"]) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document["origin_manifests"]) is not dict or document["origin_manifests"] != ORIGIN_MANIFESTS or
            type(document["own_guard"]) is not dict or set(document["own_guard"]) != {"template_sha256", "bytes"} or
            type(document["own_guard"]["bytes"]) is not int or
            not 0 < document["own_guard"]["bytes"] <= MAX_SOURCE_BYTES or
            type(document["own_guard"]["template_sha256"]) is not str or
            _DIGEST.fullmatch(document["own_guard"]["template_sha256"]) is None):
        raise ValueError("The exact finite current WebView contract667 manifest schema is required")
    for row in document["bindings"].values():
        if (type(row) is not dict or set(row) != {
                "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} or
                any(type(row[key]) is not int or not 0 < row[key] <= MAX_SOURCE_BYTES
                    for key in ("before_bytes", "after_bytes")) or
                any(type(row[key]) is not str or _DIGEST.fullmatch(row[key]) is None
                    for key in ("before_sha256", "after_sha256")) or
                type(row["fragments"]) is not list or not 0 < len(row["fragments"]) <= 8):
            raise ValueError("Exact complete current WebView contract667 source bindings are required")
        for fragment in row["fragments"]:
            if (type(fragment) is not dict or set(fragment) != {
                    "before", "after", "before_fragment_sha256", "after_fragment_sha256", "obligation"} or
                    any(type(fragment[key]) is not str or not fragment[key] for key in fragment) or
                    any(_DIGEST.fullmatch(fragment[key]) is None
                        for key in ("before_fragment_sha256", "after_fragment_sha256")) or
                    any(len(fragment[key].encode()) > MAX_SOURCE_BYTES for key in ("before", "after"))):
                raise ValueError("Exact finite current WebView contract667 fragments are required")
    if any(type(digest) is not str or _DIGEST.fullmatch(digest) is None
           for digest in document["added_inputs"].values()):
        raise ValueError("Exact current WebView contract667 control hashes are required")
    return document


def _document():
    from ios_popover_anchor_plan import _ordinary_bytes
    before = SPEC_PATH.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_SPEC_BYTES:
        raise ValueError("One ordinary bounded current WebView contract667 manifest is required")
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != SPEC_SHA256:
        raise ValueError("The exact current WebView contract667 source manifest changed")
    return _shape(_json(raw))


def _sealed_origin_documents():
    from ios_popover_anchor_plan import _ordinary_bytes
    documents = {}
    for name, digest in ORIGIN_MANIFESTS.items():
        raw = _ordinary_bytes(ROOT, name)[0]
        if not 0 < len(raw) <= MAX_SPEC_BYTES or sha(raw) != digest:
            raise ValueError("The original sealed WebView/659 manifest changed: " + name)
        documents[name] = _json(raw)
    return documents[ORIGINAL_SPEC], documents[PRIOR_SPEC]


def _check_owner_origin(document, original, prior):
    _shape(document)
    added = original.get("added_inputs") if type(original) is dict else None
    prior_bindings = prior.get("bindings") if type(prior) is dict else None
    prior_owner = prior_bindings.get(SOURCE) if type(prior_bindings) is dict else None
    prior_added = prior.get("added_inputs") if type(prior) is dict else None
    owner = document["bindings"][SOURCE]
    control = document["bindings"][CONTROL_SOURCE]
    if (type(added) is not dict or type(prior_owner) is not dict or type(prior_added) is not dict or
            any(type(added.get(name)) is not str or _DIGEST.fullmatch(added[name]) is None
                for name in (SOURCE, CONTROL_SOURCE)) or
            type(prior_added.get(PRIOR_CONTROL)) is not str or
            _DIGEST.fullmatch(prior_added[PRIOR_CONTROL]) is None or
            prior_owner.get("before_sha256") != added.get(SOURCE) or
            owner["before_sha256"] != prior_owner.get("after_sha256") or
            type(prior_owner.get("after_bytes")) is not int or
            owner["before_bytes"] != prior_owner["after_bytes"] or
            control["before_sha256"] != added.get(CONTROL_SOURCE) or
            document["bindings"][PRIOR_GUARD]["before_sha256"] != PRIOR_GUARD_SHA256 or
            document["bindings"][PRIOR_CONTROL]["before_sha256"] != prior_added[PRIOR_CONTROL]):
        raise ValueError("Current WebView contract667 must retain its exact sealed659/original owner and control origin")
    return document


def _qualified_document():
    document = _document()
    original, prior = _sealed_origin_documents()
    return _check_owner_origin(document, original, prior)


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact WebView contract667 relative identity and ordinary source bytes are required")


def source_before_contract667(relative, payload):
    """Exact complete inverse or its approved30db preimage; never current admission."""
    _identity(relative, payload)
    from ios_ui_split664_source_projection import peel_ui_split664_for_history
    payload = peel_ui_split664_for_history(relative, payload)
    binding = _qualified_document()["bindings"].get(relative)
    if binding is None:
        return payload  # Unlisted bytes are not certified, guessed or executed.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded complete current WebView contract667 source bytes are required")
    observed = sha(payload)
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("WebView contract667 source is not its complete reviewed afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or sha(after) != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique WebView contract667 inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if sha(restored) != binding["before_sha256"] or len(restored) != binding["before_bytes"]:
        raise ValueError("WebView contract667 inverse did not restore its complete approved30db source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique WebView contract667 forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("WebView contract667 complete inverse/forward source roundtrip differs")
    return restored


def current_source_before_contract667(relative, payload):
    """One exact raw current ingress; old/partial/unknown bound images must refuse."""
    _identity(relative, payload)
    from ios_ui_split664_source_projection import current_source_before_ui_split664
    payload = current_source_before_ui_split664(relative, payload)
    binding = _qualified_document()["bindings"].get(relative)
    if binding is not None and (sha(payload) != binding["after_sha256"] or len(payload) != binding["after_bytes"]):
        raise ValueError("An old or unknown image cannot replace exact current WebView contract667 source")
    return source_before_contract667(relative, payload)


def peel_contract667_for_history(relative, payload):
    """Only peel complete latest images; pass-through never certifies current."""
    _identity(relative, payload)
    from ios_ui_split664_source_projection import peel_ui_split664_for_history
    payload = peel_ui_split664_for_history(relative, payload)
    binding = _qualified_document()["bindings"].get(relative)
    if binding is not None and sha(payload) == binding["after_sha256"]:
        return source_before_contract667(relative, payload)
    return payload  # Historical or unknown bytes still face the unchanged next sealed pin.


def _validate_own_guard(root, document):
    """Bind all companion bytes; only its unique manifest-SHA literal is normalized."""
    from ios_popover_anchor_plan import _ordinary_bytes
    raw_current = _ordinary_bytes(root, SOURCE_RELATIVE)[0]
    from ios_ui_split664_source_projection import current_source_before_ui_split664
    raw = current_source_before_ui_split664(SOURCE_RELATIVE, raw_current)
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + "0" * 64 + '"\n').encode()
    if (len(raw) != document["own_guard"]["bytes"] or raw.count(needle) != 1 or
            sha(raw.replace(needle, template, 1)) != document["own_guard"]["template_sha256"]):
        raise ValueError("Current WebView contract667 own guard differs from its exact singleton template")
    return sha(raw_current)  # Exact UI664 raw identity above; the sealed667 ancestor still binds its unchanged template.


def contract_input_paths():
    """Only ordinary source-contract operands; not a native/compiler selection."""
    from ios_ui_split664_source_projection import fixture_inputs as split_fixture_inputs
    return frozenset({SOURCE, SOURCE_RELATIVE, SPEC_RELATIVE, PRIOR_GUARD, *ORIGIN_MANIFESTS}) | split_fixture_inputs()


def current_contract_hashes():
    """Expected raw-current identities, qualified before any checkout equality test."""
    document = _qualified_document()
    guard_digest = _validate_own_guard(ROOT, document)
    from ios_ui_split664_source_projection import current_input_hashes
    split_hashes = current_input_hashes()
    if split_hashes[SOURCE_RELATIVE] != guard_digest:
        raise ValueError("Current UI664 WebView companion identity must equal its separately qualified raw source")
    return {SOURCE: document["bindings"][SOURCE]["after_sha256"],
            PRIOR_GUARD: document["bindings"][PRIOR_GUARD]["after_sha256"],
            SOURCE_RELATIVE: guard_digest, SPEC_RELATIVE: SPEC_SHA256, **ORIGIN_MANIFESTS,
            **split_hashes}


def validate_current_sources(root: Path):
    """Source custody only; nothing here attests compiler or native execution."""
    import ios_ui_split664_source_projection as split
    split.validate_current_sources(root)
    document = _qualified_document()
    _validate_own_guard(root, document)
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | ORIGIN_MANIFESTS | {SPEC_RELATIVE: SPEC_SHA256})
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in expected.items():
        if sha(split.source_before_ui_split664(name, _ordinary_bytes(root, name)[0])) != digest:
            raise ValueError("Current WebView contract667 input differs from its reviewed raw image: " + name)
    return True


def fixture_inputs():
    """The complete finite source-custody union; never fixture/controller execution."""
    return contract_input_paths() | BOUND_PATHS | ADDED_PATHS
