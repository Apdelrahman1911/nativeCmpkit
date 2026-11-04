"""NEW8 derivative-only source/model controls; never an accepted Cookie/CI replay.

Only the newest helper and current two modified metadata guards are imported.
All ordinary-file providers are replaced by a finite in-memory source provider.
Restored bytes are compared, never imported or executed. Old planners, controls,
source cohorts, compiler/JDK/native and runtime/security acceptance are excluded.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

import cookie_ci668_outer_source_projection as outer
import ci668_outer_source_projection as ci
import cookie_common_jdk_source_projection as cookie


ROOT = Path(__file__).resolve().parents[3]
SHARED_GUARD = "scripts/ci/tooling_recovery671_source_projection.py"
SHARED_FINAL676_SHA256 = "311353d09543805a3e2f9f4b9744a45ad73d59ef7812fd47fb1d5d27857f592d"
NEW_HOOK_FUNCTIONS = {
    ci.SOURCE_RELATIVE: (
        "source_before_ci668", "current_source_before_ci668", "peel_ci668_for_history",
        "_validate_own_guard", "current_input_hashes", "validate_current_sources", "fixture_inputs",
    ),
    cookie.SOURCE_RELATIVE: ("_document", "validate_current_sources"),
}


def _sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _bytes(relative):
    return (ROOT / relative).read_bytes()


def _raw_expectations(document, source_digest):
    """Independent literal raw40 model, not an ancestor/current source API."""
    return (document["accepted_cookie_inputs"] |
            {name: row["after_sha256"] for name, row in document["bindings"].items()} |
            document["new_inputs"] |
            {outer.OWNING_CONTROL_RELATIVE: document["cookie681_control_binding"]["after_sha256"],
             outer.INIT: document["callback672_init_binding"]["after_sha256"],
             outer.CI_SPEC: outer.CI_SPEC_SHA256, outer.CALLBACK_SPEC: outer.CALLBACK_SPEC_SHA256,
             outer.SPEC_RELATIVE: outer.SPEC_SHA256, outer.SOURCE_RELATIVE: source_digest})


def _context():
    document = json.loads(_bytes(outer.SPEC_RELATIVE))
    source_digest = _sha(_bytes(outer.SOURCE_RELATIVE))
    expected = _raw_expectations(document, source_digest)
    payloads = {name: _bytes(name) for name in expected}
    return document, source_digest, expected, payloads


def _provider(payloads):
    """No candidate ordinary-file provider or environmental ownership controls."""
    def read(root, relative, limit=outer.MAX_SOURCE_BYTES):
        if root != ROOT or relative not in payloads or not 0 < len(payloads[relative]) <= limit:
            raise AssertionError("Only the finite sealed in-memory source model is permitted")
        return payloads[relative]
    return read


def _inverse(row, payload):
    """Independent literal arithmetic only; the returned module is never executed."""
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if restored.count(after) != 1:
            raise AssertionError("The complete unique new hook after-fragment is required")
        restored = restored.replace(after, before, 1)
    return restored


def _forward(row, payload):
    forward = payload
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise AssertionError("The complete unique new hook before-fragment is required")
        forward = forward.replace(before, after, 1)
    return forward


def _drift(payload):
    offset = len(payload) // 2
    return payload[:offset] + bytes([payload[offset] ^ 1]) + payload[offset + 1:]


def _functions(relative):
    return {node.name: node for node in ast.parse(_bytes(relative)).body
            if isinstance(node, ast.FunctionDef)}


def _call_line(function, name):
    lines = [node.lineno for node in ast.walk(function)
             if isinstance(node, ast.Call) and ast.unparse(node.func) == name]
    if not lines:
        raise AssertionError("Required newest source hook is absent: " + name)
    return min(lines)


class CookieCi668OuterDerivative609Test(unittest.TestCase):
    def test_new_raw40_finite207_and_modified_cookie_return_actual_hashes(self):
        document, source_digest, expected, payloads = _context()
        self.assertEqual(40, len(expected))
        self.assertEqual(expected, outer._expected(document, source_digest))
        provider = _provider(payloads)
        with (mock.patch.object(outer, "_document", return_value=(document, source_digest)),
              mock.patch.object(outer, "ordinary_bytes", side_effect=provider),
              mock.patch.object(cookie, "ordinary_bytes", side_effect=provider),
              mock.patch.object(cookie, "source_before_cookie", side_effect=lambda name, raw, root: raw) as old_inverse):
            current = cookie.validate_current_sources(ROOT)
        self.assertEqual(34, len(current))
        self.assertEqual({name: _sha(payloads[name]) for name in current}, current)
        self.assertEqual(outer.INIT_CURRENT_SHA256, current[outer.INIT])
        self.assertNotEqual(outer.INIT_OLD_COOKIE_SHA256, current[outer.INIT])
        self.assertEqual(_sha(payloads[cookie.SOURCE_RELATIVE]), current[cookie.SOURCE_RELATIVE])
        self.assertNotEqual(outer.COOKIE_GUARD_BEFORE_SHA256, current[cookie.SOURCE_RELATIVE])
        self.assertEqual(2, old_inverse.call_count)
        ci_document = json.loads(_bytes(ci.SPEC_RELATIVE))
        previous = ({name: row["after_sha256"] for name, row in ci_document["bindings"].items()} |
                    ci_document["added_inputs"] | ci_document["unchanged_inputs"] |
                    {ci.SPEC_RELATIVE: ci.SPEC_SHA256, ci.SOURCE_RELATIVE: _sha(_bytes(ci.SOURCE_RELATIVE))})
        finite = previous | expected
        self.assertEqual(207, len(finite))
        # The original175 metadata remains a named predecessor. Its owning
        # CI fixture is a reviewed descendant, not old-as-current metadata.
        owning = "scripts/ci/test_ci668_outer_source_projection.py"
        actual_finite = {name: _sha(_bytes(name)) for name in finite}
        offline = "scripts/ci/offline_tooling_reuse.py"
        split = "scripts/ci/test_ios_ui_split664_native_routing.py"
        provenance = "scripts/ci/offline_tooling_provenance.py"
        changed = {owning, outer.LIBRARY, offline, split, ci.WORKFLOW, provenance}
        self.assertEqual(changed, {name for name in finite if finite[name] != actual_finite[name]})
        self.assertNotIn(outer.LIBRARY, expected)  # Exact payload ancestry is outside raw40.
        self.assertEqual("8e6d2e76f9de755f5d53bdc6a5a29aeb7161e9777ffcf7b5a0a163164889dfce", previous[owning])
        import macos_share_ci668_composition as joint
        self.assertEqual(previous[owning], _sha(joint.current_source_in_view(owning, _bytes(owning), joint.CI_VIEW, ROOT)))
        self.assertEqual(outer.LIBRARY_BEFORE_SHA256, previous[outer.LIBRARY])
        self.assertEqual(previous[outer.LIBRARY], _sha(joint.current_source_in_view(outer.LIBRARY, _bytes(outer.LIBRARY), joint.CI_VIEW, ROOT)))
        self.assertEqual(outer.LIBRARY_AFTER_SHA256, actual_finite[outer.LIBRARY])
        self.assertEqual({ci.WORKFLOW, provenance}.intersection(expected), set())
        self.assertEqual({ci.WORKFLOW: "7c9af733acf8ac35aad36012870a9ba2895a36646d04743dbf709b911d6d1566",
                          provenance: "dc4811e34272e4b67e1abfb82b9cf0bc9d79a7bf01a9cfad205eb0f007b3f63a"},
                         {name: actual_finite[name] for name in (ci.WORKFLOW, provenance)})
        for name in (offline, split, ci.WORKFLOW, provenance):
            self.assertEqual(previous[name], _sha(joint.current_source_in_view(name, _bytes(name), joint.CI_VIEW, ROOT)))
            self.assertNotEqual(previous[name], actual_finite[name])
        for name in changed:
            finite[name] = actual_finite[name]  # Explicit finite207 current overrides, never repin old175.
        self.assertEqual(actual_finite, finite)
        self.assertEqual(_sha(_bytes(outer.NEW_CONTROL_RELATIVE)), finite[outer.NEW_CONTROL_RELATIVE])

    def test_two_new_hook_inverses_restore_complete_exact_predecessors(self):
        document, source_digest, _, payloads = _context()
        with mock.patch.object(outer, "_document", return_value=(document, source_digest)):
            for name, functions in NEW_HOOK_FUNCTIONS.items():
                row, raw = document["bindings"][name], payloads[name]
                self.assertEqual(len(functions), len(row["fragments"]))
                restored = outer.current_source_before_cookie_outer(name, raw, ROOT)
                self.assertEqual(_inverse(row, raw), restored)
                self.assertEqual(row["before_sha256"], _sha(restored))
                self.assertEqual(row["before_bytes"], len(restored))
                self.assertEqual(raw, _forward(row, restored))
                self.assertEqual(restored, outer.source_before_cookie_outer(name, restored, ROOT))

    def test_old_prehook_and_single_byte_drift_refuse_strict_newest_ingress(self):
        document, source_digest, _, payloads = _context()
        with mock.patch.object(outer, "_document", return_value=(document, source_digest)):
            for name in NEW_HOOK_FUNCTIONS:
                row, raw = document["bindings"][name], payloads[name]
                for refused in (_inverse(row, raw), _drift(raw)):
                    with self.assertRaisesRegex(ValueError, "exact current Cookie outer source"):
                        outer.current_source_before_cookie_outer(name, refused, ROOT)

    def test_after_only_history_never_readmits_restored_guard_as_current(self):
        document, source_digest, _, payloads = _context()
        with mock.patch.object(outer, "_document", return_value=(document, source_digest)):
            for name in NEW_HOOK_FUNCTIONS:
                raw = payloads[name]
                restored = outer.peel_cookie_outer_for_history(name, raw, ROOT)
                self.assertEqual(_inverse(document["bindings"][name], raw), restored)
                self.assertEqual(restored, outer.peel_cookie_outer_for_history(name, restored, ROOT))
                self.assertEqual(_drift(raw), outer.peel_cookie_outer_for_history(name, _drift(raw), ROOT))
                with self.assertRaises(ValueError):
                    outer.current_source_before_cookie_outer(name, restored, ROOT)
            self.assertEqual(b"uncertified", outer.peel_cookie_outer_for_history("unlisted/source.py", b"uncertified", ROOT))

    def test_callback672_named_init_view_only_raw_ci_keeps_e0c82(self):
        document, source_digest, _, payloads = _context()
        row, raw = document["callback672_init_binding"], payloads[outer.INIT]
        ci_document = json.loads(_bytes(ci.SPEC_RELATIVE))
        with (mock.patch.object(outer, "_document", return_value=(document, source_digest)),
              mock.patch.object(ci, "_document", return_value=ci_document)):
            self.assertEqual((9304, outer.INIT_CURRENT_SHA256), (len(raw), _sha(raw)))
            self.assertEqual(raw, outer.peel_cookie_outer_for_history(outer.INIT, raw, ROOT))
            self.assertEqual(raw, ci.current_source_before_ci668(outer.INIT, raw))
            comparison = outer.callback672_init_for_old_cookie_comparison(outer.INIT, raw, ROOT)
            self.assertEqual(_inverse(row, raw), comparison)
            self.assertEqual((7940, outer.INIT_OLD_COOKIE_SHA256), (len(comparison), _sha(comparison)))
            self.assertEqual(raw, outer.callback672_init_for_old_cookie_comparison("unlisted/source.py", raw, ROOT))
            with self.assertRaisesRegex(ValueError, "exact current callback672 init"):
                outer.callback672_init_for_old_cookie_comparison(outer.INIT, comparison, ROOT)
            with self.assertRaises(ValueError):
                ci.current_source_before_ci668(outer.INIT, comparison)

    def test_new_manifest_guard_and_entire_new8_control_tamper_pins(self):
        document, source_digest, _, payloads = _context()
        with mock.patch.object(outer, "ordinary_bytes", side_effect=_provider(payloads)):
            self.assertEqual((document, source_digest), outer._document(ROOT))
        for name, refusal in (
                (outer.NEW_CONTROL_RELATIVE, "complete NEW8 Cookie outer derivative control"),
                (outer.SOURCE_RELATIVE, "complete newest Cookie outer guard template"),
                (outer.SPEC_RELATIVE, "newest Cookie outer manifest"),
                (outer.CALLBACK_SPEC, "Original Cookie/CI/callback manifests")):
            changed = payloads | {name: _drift(payloads[name])}
            with mock.patch.object(outer, "ordinary_bytes", side_effect=_provider(changed)):
                with self.assertRaisesRegex(ValueError, refusal):
                    outer._document(ROOT)

    def test_modified_ci_own_guard_compares_predecessor_but_reports_raw_digest(self):
        document, source_digest, _, payloads = _context()
        ci_document = json.loads(_bytes(ci.SPEC_RELATIVE))
        raw = payloads[ci.SOURCE_RELATIVE]
        restored = _inverse(document["bindings"][ci.SOURCE_RELATIVE], raw)
        line = ('SPEC_SHA256 = "' + ci.SPEC_SHA256 + '"\n').encode()
        zero = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
        self.assertEqual(outer.CI_GUARD_BEFORE_SHA256, _sha(restored))
        self.assertEqual(ci_document["own_guard"]["template_sha256"], _sha(restored.replace(line, zero, 1)))
        with (mock.patch.object(outer, "_document", return_value=(document, source_digest)),
              mock.patch.object(ci, "_ordinary", side_effect=_provider(payloads))):
            returned = ci._validate_own_guard(ROOT, ci_document)
        self.assertEqual(_sha(raw), returned)
        self.assertNotEqual(_sha(restored), returned)

    def test_ast_newest_hook_order_named_callback_and_unchanged_shared676(self):
        ci_functions = _functions(ci.SOURCE_RELATIVE)
        for name, hook in (
                ("source_before_ci668", "cookie_outer.peel_cookie_outer_for_history"),
                ("current_source_before_ci668", "cookie_outer.current_source_before_cookie_outer"),
                ("peel_ci668_for_history", "cookie_outer.peel_cookie_outer_for_history")):
            self.assertLess(_call_line(ci_functions[name], hook), _call_line(ci_functions[name], "_document"))
        self.assertLess(_call_line(ci_functions["_validate_own_guard"], "cookie_outer.current_source_before_cookie_outer"),
                        _call_line(ci_functions["_validate_own_guard"], "_own_guard_payload"))
        self.assertLess(_call_line(ci_functions["validate_current_sources"], "cookie_outer.validate_current_sources"),
                        _call_line(ci_functions["validate_current_sources"], "_document"))
        self.assertIn("current207", ast.get_docstring(ci_functions["current_input_hashes"]))
        self.assertIn("finite207", ast.get_docstring(ci_functions["fixture_inputs"]))
        cookie_functions = _functions(cookie.SOURCE_RELATIVE)
        self.assertLess(_call_line(cookie_functions["_document"], "cookie_outer.current_source_before_cookie_outer"),
                        _call_line(cookie_functions["_document"], "source.replace"))
        self.assertLess(_call_line(cookie_functions["validate_current_sources"], "cookie_outer.validate_current_sources"),
                        _call_line(cookie_functions["validate_current_sources"], "_document"))
        self.assertIn("current[name] = sha(payload)", ast.unparse(cookie_functions["validate_current_sources"]))
        self.assertIn("cookie_outer.callback672_init_for_old_cookie_comparison", ast.unparse(cookie_functions["validate_current_sources"]))
        helper_functions = _functions(outer.SOURCE_RELATIVE)
        history = ast.unparse(helper_functions["peel_cookie_outer_for_history"])
        self.assertNotIn("callback672_init_for_old_cookie_comparison(", history)
        self.assertNotIn("current_source_before_cookie_outer(", history)
        named = ast.unparse(helper_functions["callback672_init_for_old_cookie_comparison"])
        self.assertIn("callback672_init_binding", named)
        self.assertNotIn("IO665", named)
        self.assertEqual(SHARED_FINAL676_SHA256, _sha(_bytes(SHARED_GUARD)))
        shared = _functions(SHARED_GUARD)
        hooks = {
            "source_before_tooling671": "ci668.peel_ci668_for_history",
            "current_source_before_tooling671": "ci668.current_source_before_ci668",
            "peel_tooling671_for_history": "ci668.peel_ci668_for_history",
            "_validate_own_guard": "ci668.current_source_before_ci668",
            "current_input_hashes": "ci668.current_input_hashes",
            "validate_current_sources": "ci668.validate_current_sources",
            "fixture_inputs": "ci668.fixture_inputs",
        }
        actual_hooks = {name for name, node in shared.items()
                        if any(isinstance(item, ast.Import) and any(alias.name == "ci668_outer_source_projection" for alias in item.names)
                               for item in ast.walk(node))}
        self.assertEqual(set(hooks), actual_hooks)
        for name, hook in hooks.items():
            _call_line(shared[name], hook)

