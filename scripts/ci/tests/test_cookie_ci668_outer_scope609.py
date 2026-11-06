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


def _current_comparison(relative, payload):
    """Explicit scoped current-to-row DATA; no generic old/current shortcut."""
    comparison = outer._common_jdk_guard_source(relative, payload, ROOT, current=True)
    return outer._content_owner_source(relative, comparison, ROOT, current=True)


def _finite207_predecessors():
    """Exact owning BEFORE metadata only; no inventory, whitelist or raw admission."""
    import ci_fixture_successor730 as successor
    import ci_source_recovery740_742 as recovery742
    import ci_source_domain740 as domain740
    return (successor.FAILURE_BEFORE | successor.RELATED_BEFORE |
            successor.ORDINARY_FIXTURE_BEFORE | successor.BEFORE |
            {successor.CAPACITY: successor.CAPACITY_BEFORE, successor.REMOTE: successor.REMOTE_BEFORE} |
            recovery742.BEFORE | domain740.BEFORE)


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
        device = "scripts/ci/android_device_tests.py"
        matrix = "scripts/ci/workflow_matrix.py"
        changed = {owning, outer.LIBRARY, offline, split, ci.WORKFLOW, provenance, device, matrix}
        self.assertEqual(8, len(changed))  # Preserve the original finite207 difference base.
        added_changes = {"calf-webview/build.gradle.kts", outer.NEW_CONTROL_RELATIVE,
                          outer.OWNING_CONTROL_RELATIVE, cookie.SOURCE_RELATIVE}
        self.assertEqual(4, len(added_changes))  # Exact original recovery-owned common guard is the fourth descendant.
        self.assertFalse(changed & added_changes)
        for name in added_changes:
            comparison = _current_comparison(name, _bytes(name))
            self.assertEqual(finite[name], _sha(comparison))
            self.assertNotEqual(finite[name], actual_finite[name])
        # Only finite endpoints equal to a named BEFORE row are historical.
        # Derive their owners independently; never whitelist the observed drift.
        predecessors = _finite207_predecessors()
        owned = {name for name, pin in predecessors.items()
                 if name in finite and name not in changed | added_changes and finite[name] == pin["sha256"]}
        self.assertEqual(13, len(owned))
        import ci_source_domain740 as domain740
        for name in owned:
            comparison = domain740.current_source_before_domain740(name, _bytes(name), ROOT)
            self.assertEqual((predecessors[name]["bytes"], finite[name]), (len(comparison), _sha(comparison)))
            self.assertNotEqual(finite[name], actual_finite[name])
        # R4 adds exactly one owner outside the unchanged old8+4+13 tables.
        # Derive it from its declared BEFORE pin, not from observed actual drift.
        import ci_fixture_successor730 as successor
        platform_owner = "scripts/ci/platform_recovery659_source_projection.py"
        platform_owned = {name for name, pin in successor.PLATFORM_CUSTODY_BEFORE743.items()
                          if name in successor.PLATFORM_CUSTODY_MODIFIED743 and name in finite
                          and name not in changed | added_changes | owned and finite[name] == pin["sha256"]}
        self.assertEqual({platform_owner}, platform_owned)
        self.assertFalse(platform_owned & (changed | added_changes | owned))
        platform_before = {"bytes": 12858,
                           "sha256": "4505c503a7cf2b354e7d18dbf9129a43071ffc9a0fbb8e2093dfbca8f179960a"}
        self.assertEqual(platform_before, successor.PLATFORM_CUSTODY_BEFORE743[platform_owner])
        platform_raw = _bytes(platform_owner)
        platform_row = successor._document(ROOT)["platform_custody_bindings743"][platform_owner]
        self.assertEqual((platform_row["after_bytes"], platform_row["after_sha256"]),
                         (len(platform_raw), actual_finite[platform_owner]))
        platform_comparison = successor.current_source_before_fixture_successor(platform_owner, platform_raw, ROOT)
        self.assertEqual(platform_before, {"bytes": len(platform_comparison), "sha256": _sha(platform_comparison)})
        self.assertEqual(finite[platform_owner], _sha(platform_comparison))
        self.assertNotEqual(finite[platform_owner], actual_finite[platform_owner])
        self.assertEqual(changed | added_changes | owned | platform_owned,
                         {name for name in finite if finite[name] != actual_finite[name]})
        self.assertNotIn(outer.LIBRARY, expected)  # Exact payload ancestry is outside raw40.
        self.assertEqual("8e6d2e76f9de755f5d53bdc6a5a29aeb7161e9777ffcf7b5a0a163164889dfce", previous[owning])
        import macos_share_ci668_composition as joint
        self.assertEqual(previous[owning], _sha(joint.current_source_in_view(owning, _bytes(owning), joint.CI_VIEW, ROOT)))
        self.assertEqual(outer.LIBRARY_BEFORE_SHA256, previous[outer.LIBRARY])
        self.assertEqual(previous[outer.LIBRARY], _sha(joint.current_source_in_view(outer.LIBRARY, _bytes(outer.LIBRARY), joint.CI_VIEW, ROOT)))
        # The immutable6fdc Library is recovery DATA, not raw finite207 output.
        self.assertEqual("6fdc0947617c41b199f13e63b13056de6c76bb215698e259109c324f219c2127",
                         _sha(domain740.current_source_before_domain740(outer.LIBRARY, _bytes(outer.LIBRARY), ROOT)))
        self.assertEqual("3387f2bb32e8bb7db910284bc8306934cbf47e624bf872b1c050fbcfa416dcf3", actual_finite[outer.LIBRARY])
        # The original Share library remains an explicit predecessor, never raw current.
        self.assertEqual(outer.LIBRARY_AFTER_SHA256, _sha(joint.source_before_android_lifecycle(outer.LIBRARY, _bytes(outer.LIBRARY), ROOT)))
        self.assertEqual({ci.WORKFLOW, provenance}.intersection(expected), set())
        self.assertEqual({ci.WORKFLOW: "a1ea0950a96472e6c602e3a776f74ce519cb8bdadf78920512a1ee6649961d5b",
                          provenance: "dc4811e34272e4b67e1abfb82b9cf0bc9d79a7bf01a9cfad205eb0f007b3f63a"},
                         {name: actual_finite[name] for name in (ci.WORKFLOW, provenance)})
        for name in (offline, split, ci.WORKFLOW, provenance, device, matrix):
            self.assertEqual(previous[name], _sha(joint.current_source_in_view(name, _bytes(name), joint.CI_VIEW, ROOT)))
            self.assertNotEqual(previous[name], actual_finite[name])
        for name in changed | added_changes | owned | platform_owned:
            finite[name] = actual_finite[name]  # Explicit finite207 current overrides, never repin old175.
        self.assertEqual(actual_finite, finite)
        self.assertEqual(_sha(_bytes(outer.NEW_CONTROL_RELATIVE)), finite[outer.NEW_CONTROL_RELATIVE])

    def test_new_library_raw_recovery_data_and_sealed_v2_remain_distinct(self):
        import copy
        import ci_fixture_successor730 as successor
        import ci_source_domain740 as domain740
        import ci_source_recovery740_742 as recovery742
        raw = _bytes(outer.LIBRARY)
        row = recovery742._document(ROOT)["bindings"][outer.LIBRARY]
        self.assertEqual({'after_bytes': 413042, 'after_sha256': '3387f2bb32e8bb7db910284bc8306934cbf47e624bf872b1c050fbcfa416dcf3', 'before_bytes': 412990, 'before_sha256': '6fdc0947617c41b199f13e63b13056de6c76bb215698e259109c324f219c2127', 'fragments': [{'after': '    "package.json", "yarn.lock", "package-lock.json", "pnpm-lock.yaml",\n    "docs/testing/installed-jdk17-prerequisite.md",\n)\n', 'after_fragment_sha256': '4ab7012fc437540ed8a81d44dfd1ce3ed25e664afacc4d10761bd416fa1c2334', 'before': '    "package.json", "yarn.lock", "package-lock.json", "pnpm-lock.yaml",\n)\n', 'before_fragment_sha256': 'b4856c15daca7256d5a8c349897fed6aa2f7f7b5e0b0cad0cb2b3a47c2b074ca'}]}, row)
        self.assertEqual((413042, "3387f2bb32e8bb7db910284bc8306934cbf47e624bf872b1c050fbcfa416dcf3"),
                         (len(raw), _sha(raw)))
        before = _inverse(row, raw)
        self.assertEqual((412990, "6fdc0947617c41b199f13e63b13056de6c76bb215698e259109c324f219c2127"),
                         (len(before), _sha(before)))
        self.assertEqual(before, domain740.current_source_before_domain740(outer.LIBRARY, raw, ROOT))
        self.assertEqual(raw, _forward(row, before))
        self.assertNotEqual(_sha(raw), _sha(before))
        for bad in (before, raw[:-1], raw + b"\n", raw + raw, b"", None, bytearray(raw), raw.decode()):
            with self.subTest(operand=type(bad).__name__), self.assertRaises(ValueError):
                domain740.current_source_before_domain740(outer.LIBRARY, bad, ROOT)

        # Reconstruct sealed failed V2 as DATA; never import or execute that source.
        active743 = successor._document(ROOT)
        document = copy.deepcopy(successor._platform_previous_document743(active743))
        self.assertEqual({"bytes": 45027, "path": "scripts/ci/test_ci_fixture_successor730.py",
                          "sha256": "b346d227ecd18fdd00a7b79a0826e70fb424293d9e9a5c39be897274f7b1ae5c"},
                         document["control"])
        relative = outer.NEW_CONTROL_RELATIVE
        failure = document["failure_bindings"][relative]
        self.assertEqual(16, len(failure["fragments"]))
        # Peel only these two disclosed current609 fixes before immutable R4 DATA.
        r2_current609 = successor._inverse(_bytes(relative), active743["platform_custody_bindings743"][relative])
        r4_prior609 = _inverse({"fragments": failure["fragments"][14:]}, r2_current609)
        self.assertEqual((27312, "78a545e87d4493f194e11db462c82d4482946e5395610a86dc1cebfbea95fe0f"),
                         (len(r4_prior609), _sha(r4_prior609)))
        failure["fragments"] = failure["fragments"][:14]
        failure["after_bytes"], failure["after_sha256"] = len(r4_prior609), _sha(r4_prior609)
        self.assertEqual(14, len(failure["fragments"]))
        prior609 = _inverse({"fragments": failure["fragments"][8:]}, r4_prior609)
        self.assertEqual((18934, "5f4da499d2a9a605131e7921a5e648125e47506949407abdb6144d8895730928"),
                         (len(prior609), _sha(prior609)))
        failure["fragments"] = failure["fragments"][:8]
        failure["after_bytes"], failure["after_sha256"] = len(prior609), _sha(prior609)
        document["own_guard"] = {"bytes": 26071, "template_sha256": "a6a14a0072373827c6e12477c25420cde87d3f2bdc9b2f0fb49f2fc169935d7d"}
        # Historical control metadata is DATA, not the current R1 control above.
        document["control"] = {"bytes": 33750, "path": "scripts/ci/test_ci_fixture_successor730.py",
                                "sha256": "f10540c87c70d18e89fda37d0d0b21d9508acb46e27971fed3ba42952b8461a1"}
        self.assertEqual({"bytes": 33750, "path": "scripts/ci/test_ci_fixture_successor730.py",
                          "sha256": "f10540c87c70d18e89fda37d0d0b21d9508acb46e27971fed3ba42952b8461a1"},
                         document["control"])
        encoded = (json.dumps(document, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual((103004, "6db5d2e2d26044d474d28f51af0553f4fce5bd9402d4fbbe45c20cea748ceafa"),
                         (len(encoded), _sha(encoded)))

    def test_new_owned13_finite207_predecessors_refuse_old_drift_and_preserve_sealed_r3(self):
        import copy
        import ci_fixture_successor730 as successor
        import ci_source_domain740 as domain740
        document, source_digest, expected, payloads = _context()
        ci_document = json.loads(_bytes(ci.SPEC_RELATIVE))
        previous = ({name: row["after_sha256"] for name, row in ci_document["bindings"].items()} |
                    ci_document["added_inputs"] | ci_document["unchanged_inputs"] |
                    {ci.SPEC_RELATIVE: ci.SPEC_SHA256, ci.SOURCE_RELATIVE: _sha(_bytes(ci.SOURCE_RELATIVE))})
        finite = previous | expected
        self.assertEqual((175, 40, 207), (len(previous), len(expected), len(finite)))
        changed = {"scripts/ci/test_ci668_outer_source_projection.py", outer.LIBRARY,
                   "scripts/ci/offline_tooling_reuse.py", "scripts/ci/test_ios_ui_split664_native_routing.py",
                   ci.WORKFLOW, "scripts/ci/offline_tooling_provenance.py",
                   "scripts/ci/android_device_tests.py", "scripts/ci/workflow_matrix.py"}
        added = {"calf-webview/build.gradle.kts", outer.NEW_CONTROL_RELATIVE,
                 outer.OWNING_CONTROL_RELATIVE, cookie.SOURCE_RELATIVE}
        self.assertEqual((8, 4), (len(changed), len(added)))
        predecessors = _finite207_predecessors()
        owned = {name for name, pin in predecessors.items()
                 if name in finite and name not in changed | added and finite[name] == pin["sha256"]}
        self.assertEqual(13, len(owned))
        self.assertFalse(owned & (changed | added))
        # Actual raw self/spec metadata does not become a historical comparison.
        for raw_current in (outer.SOURCE_RELATIVE, outer.SPEC_RELATIVE):
            self.assertNotIn(raw_current, owned)
            self.assertEqual(finite[raw_current], _sha(_bytes(raw_current)))
        for name in owned:
            raw = _bytes(name)
            before = domain740.current_source_before_domain740(name, raw, ROOT)
            self.assertEqual(predecessors[name], {"bytes": len(before), "sha256": _sha(before)})
            self.assertEqual(finite[name], _sha(before))
            self.assertNotEqual(finite[name], _sha(raw))
            for bad in (before, _drift(raw)):
                with self.subTest(relative=name, operand=_sha(bad)), self.assertRaises(ValueError):
                    domain740.current_source_before_domain740(name, bad, ROOT)

        # The R4 Platform owner is a separate singleton, never a fourteenth
        # member of the sealed owned13 table or an observed-drift whitelist.
        platform_owner = "scripts/ci/platform_recovery659_source_projection.py"
        platform_owned = {name for name, pin in successor.PLATFORM_CUSTODY_BEFORE743.items()
                          if name in successor.PLATFORM_CUSTODY_MODIFIED743 and name in finite
                          and name not in changed | added | owned and finite[name] == pin["sha256"]}
        self.assertEqual({platform_owner}, platform_owned)
        self.assertFalse(platform_owned & (changed | added | owned))
        platform_before = {"bytes": 12858,
                           "sha256": "4505c503a7cf2b354e7d18dbf9129a43071ffc9a0fbb8e2093dfbca8f179960a"}
        self.assertEqual(platform_before, successor.PLATFORM_CUSTODY_BEFORE743[platform_owner])
        platform_raw = _bytes(platform_owner)
        platform_row = successor._document(ROOT)["platform_custody_bindings743"][platform_owner]
        self.assertEqual((platform_row["after_bytes"], platform_row["after_sha256"]),
                         (len(platform_raw), _sha(platform_raw)))
        platform_prior = successor.current_source_before_fixture_successor(platform_owner, platform_raw, ROOT)
        self.assertEqual(platform_before, {"bytes": len(platform_prior), "sha256": _sha(platform_prior)})
        self.assertEqual(finite[platform_owner], _sha(platform_prior))
        self.assertNotEqual(finite[platform_owner], _sha(platform_raw))
        for bad in (platform_prior, _drift(platform_raw)):
            with self.subTest(relative=platform_owner, operand=_sha(bad)), self.assertRaises(ValueError):
                successor.current_source_before_fixture_successor(platform_owner, bad, ROOT)

        # Restore sealed R3 SOURCE/DATA without executing that failed predecessor.
        active743 = successor._document(ROOT)
        current = copy.deepcopy(successor._platform_previous_document743(active743))
        self.assertEqual({"bytes": 45027, "path": "scripts/ci/test_ci_fixture_successor730.py",
                          "sha256": "b346d227ecd18fdd00a7b79a0826e70fb424293d9e9a5c39be897274f7b1ae5c"},
                         current["control"])
        relative = outer.NEW_CONTROL_RELATIVE
        failure = current["failure_bindings"][relative]
        self.assertEqual(16, len(failure["fragments"]))
        # Peel only these two disclosed current609 fixes before immutable R4 DATA.
        r2_current609 = successor._inverse(_bytes(relative), active743["platform_custody_bindings743"][relative])
        r4_prior609 = _inverse({"fragments": failure["fragments"][14:]}, r2_current609)
        self.assertEqual((27312, "78a545e87d4493f194e11db462c82d4482946e5395610a86dc1cebfbea95fe0f"),
                         (len(r4_prior609), _sha(r4_prior609)))
        failure["fragments"] = failure["fragments"][:14]
        failure["after_bytes"], failure["after_sha256"] = len(r4_prior609), _sha(r4_prior609)
        self.assertEqual(14, len(failure["fragments"]))
        prior609 = _inverse({"fragments": failure["fragments"][10:]}, r4_prior609)
        self.assertEqual((22470, "5797728d46a2ecf94673d748f8db120c746ff1aa00f492af959771af7dfcd130"),
                         (len(prior609), _sha(prior609)))
        failure["fragments"] = failure["fragments"][:10]
        failure["after_bytes"], failure["after_sha256"] = len(prior609), _sha(prior609)
        current["own_guard"] = {'bytes': 26072, 'template_sha256': 'afe934679ac7c68010a87f6735079473ebb8c1043c9232980911346ef68327bc'}
        # Historical control metadata is DATA, not the current R1 control above.
        current["control"] = {"bytes": 33750, "path": "scripts/ci/test_ci_fixture_successor730.py",
                                "sha256": "f10540c87c70d18e89fda37d0d0b21d9508acb46e27971fed3ba42952b8461a1"}
        encoded = (json.dumps(current, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual((107669, "76a5e3402d8471312ca3db52f991cc98c7609cd77643511a560e8a46c980577c"),
                         (len(encoded), _sha(encoded)))

    def test_two_new_hook_inverses_restore_complete_exact_predecessors(self):
        document, source_digest, _, payloads = _context()
        with mock.patch.object(outer, "_document", return_value=(document, source_digest)):
            for name, functions in NEW_HOOK_FUNCTIONS.items():
                row, raw = document["bindings"][name], payloads[name]
                self.assertEqual(len(functions), len(row["fragments"]))
                restored = outer.current_source_before_cookie_outer(name, raw, ROOT)
                comparison = _current_comparison(name, raw)
                self.assertEqual(_inverse(row, comparison), restored)
                self.assertEqual(row["before_sha256"], _sha(restored))
                self.assertEqual(row["before_bytes"], len(restored))
                self.assertEqual(comparison, _forward(row, restored))
                self.assertEqual(restored, outer.source_before_cookie_outer(name, restored, ROOT))

    def test_old_prehook_and_single_byte_drift_refuse_strict_newest_ingress(self):
        document, source_digest, _, payloads = _context()
        with mock.patch.object(outer, "_document", return_value=(document, source_digest)):
            for name in NEW_HOOK_FUNCTIONS:
                row, raw = document["bindings"][name], payloads[name]
                for refused in (_inverse(row, _current_comparison(name, raw)), _drift(raw)):
                    with self.assertRaisesRegex(ValueError, "exact current Cookie outer source"):
                        outer.current_source_before_cookie_outer(name, refused, ROOT)

    def test_after_only_history_never_readmits_restored_guard_as_current(self):
        document, source_digest, _, payloads = _context()
        with mock.patch.object(outer, "_document", return_value=(document, source_digest)):
            for name in NEW_HOOK_FUNCTIONS:
                raw = payloads[name]
                restored = outer.peel_cookie_outer_for_history(name, raw, ROOT)
                self.assertEqual(_inverse(document["bindings"][name], _current_comparison(name, raw)), restored)
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
        restored = _inverse(document["bindings"][ci.SOURCE_RELATIVE], _current_comparison(ci.SOURCE_RELATIVE, raw))
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

