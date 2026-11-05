#!/usr/bin/env python3
"""NEW793 narrow configure-once source/order controls; never native acceptance."""
from copy import deepcopy
from pathlib import Path
import ast
import hashlib
import tempfile
import unittest
from types import FunctionType as _FunctionType

import android_camera_callback_native_focus as callback
import ci_source_recovery740_742 as recovery

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "scripts/ci/android_camera_callback_native_focus.py"
BEFORE_SHA256 = "503ca18b83311b557908a50dc9683dec3e74ba1708f23e9515b356c4361459a6"
BEFORE_BYTES = 26749
AFTER_SHA256 = "8e3dd41b60d44d7566280f7309e3a7dabef385755981554990b4ae5ba32d8875"
AFTER_BYTES = 26714
CLI_METHOD_AST_SHA256 = "290521d403822d152b0e0a3227b40bc47ef92a3a319905fdbb9d03b7a9a4c380"
DELETE_BEFORE = 'def configure_item(root: Path, item: dict):\n    validate_current_sources(root)\n    native = _ordinary_bytes(root, SOURCE).decode("utf-8")\n'
DELETE_AFTER = 'def configure_item(root: Path, item: dict):\n    native = _ordinary_bytes(root, SOURCE).decode("utf-8")\n'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def definitions(raw):
    return {node.name: node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef)}

def ast_sha(node):
    return sha(ast.dump(node, include_attributes=False).encode())

class AndroidCameraCallbackConfigureOnce793Controls(unittest.TestCase):
    def test_NEW_only_first_duplicate_validation_removed_preserves_final_public_guards_and_refusal_propagation(self):
        raw = callback._ordinary_bytes(ROOT, SOURCE)
        self.assertEqual((AFTER_SHA256, AFTER_BYTES), (sha(raw), len(raw)))
        document = recovery._document(ROOT)
        row = document["bindings"][SOURCE]
        self.assertEqual((BEFORE_SHA256, BEFORE_BYTES), (row["before_sha256"], row["before_bytes"]))
        self.assertEqual((AFTER_SHA256, AFTER_BYTES), (row["after_sha256"], row["after_bytes"]))
        fragment, = row["fragments"]
        self.assertEqual((DELETE_BEFORE, DELETE_AFTER), (fragment["before"], fragment["after"]))
        old = recovery.current_source_before_recovery(SOURCE, raw, ROOT)
        self.assertEqual((BEFORE_SHA256, BEFORE_BYTES), (sha(old), len(old)))
        prior, current = definitions(old), definitions(raw)
        self.assertEqual(set(prior), set(current))
        expected = deepcopy(prior["configure_item"])
        self.assertEqual("validate_current_sources(root)", ast.unparse(expected.body[0]))
        del expected.body[0]
        self.assertEqual(ast_sha(expected), ast_sha(current["configure_item"]))
        for name in set(prior) - {"configure_item"}:
            self.assertEqual(ast_sha(prior[name]), ast_sha(current[name]), name)
        final = current["configure_item"].body[-1]
        self.assertIsInstance(final, ast.Assign)
        self.assertEqual("item[CONTRACT_KEY]", ast.unparse(final.targets[0]))
        self.assertEqual("source_contract(root)", ast.unparse(final.value))
        self.assertEqual("validate_current_sources(root)", ast.unparse(current["source_contract"].body[0]))
        self.assertEqual("_contract(current_contract_hashes(root))",
                         ast.unparse(current["source_contract"].body[1].value))
        # Separate public/tooling boundaries are still fresh, not erased or cached.
        current_hash_calls = [node.func.id for node in ast.walk(current["current_contract_hashes"])
                              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        self.assertIn("tooling_input_hashes", current_hash_calls)
        self.assertIn("_own_guard", current_hash_calls)
        self.assertIn("current_contract_hashes", [node.func.id
                      for node in ast.walk(current["validate_source_contract"])
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)])
        self.assertEqual("1c14d6fcb7dc49716de3688169c9280fde51f62564d1593a6a95707f85f19f7a",
                         sha(callback._ordinary_bytes(ROOT, callback.SPEC_RELATIVE)))
        self.assertEqual("9def6c416e199237600bdcdc2a16a3fd22dc2158796e1116f999b8681c96a110",
                         sha(callback._ordinary_bytes(ROOT, "scripts/ci/fixtures/tooling-recovery671-source-inverse.json")))
        library_tree = ast.parse(callback._ordinary_bytes(ROOT, "scripts/ci/library_tests.py"))
        call, = [node for node in ast.walk(library_tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == "camera_callback" and node.func.attr == "configure_item"]
        self.assertFalse(any(node.lineno <= call.lineno <= node.end_lineno
                             for node in ast.walk(library_tree) if isinstance(node, ast.Try)))
        android_tree = ast.parse(callback._ordinary_bytes(ROOT, "scripts/ci/android_device_tests.py"))
        main, = [node for node in android_tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"]
        plan, = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == "lt" and node.func.attr == "plan"]
        self.assertFalse(any(node.lineno <= plan.lineno <= node.end_lineno
                             for node in ast.walk(main) if isinstance(node, ast.Try)))
        workflow_tree = ast.parse(callback._ordinary_bytes(ROOT, "scripts/ci/workflow_matrix.py"))
        preflight, = [node for node in workflow_tree.body if isinstance(node, ast.FunctionDef)
                      and node.name == "preflight_plans"]
        run, = [node for node in ast.walk(preflight) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess" and node.func.attr == "run"]
        timeout, = [kw.value for kw in run.keywords if kw.arg == "timeout"]
        self.assertEqual(30, ast.literal_eval(timeout))
        original = ast.parse(callback._ordinary_bytes(ROOT, "scripts/ci/test_android_camera_callback_native_focus.py"))
        cli, = [node for node in ast.walk(original) if isinstance(node, ast.FunctionDef)
                and node.name == "test_genuine_api35_callback_profile_cli_retains_unmocked_source_integration"]
        self.assertEqual(CLI_METHOD_AST_SHA256, ast_sha(cli))
        self.assertEqual(5, len(cli.body))
        self.assertEqual([], cli.decorator_list)

    def test_NEW_strict_current_and_after_only_history_refuse_old_partial_displaced_and_unknown_helper(self):
        raw = callback._ordinary_bytes(ROOT, SOURCE)
        document = recovery._document(ROOT)
        row = document["bindings"][SOURCE]
        old = recovery.current_source_before_recovery(SOURCE, raw, ROOT)
        self.assertEqual((BEFORE_SHA256, BEFORE_BYTES), (sha(old), len(old)))
        self.assertEqual(old, recovery.peel_recovery_for_history(SOURCE, raw, ROOT))
        self.assertIs(old, recovery.peel_recovery_for_history(SOURCE, old, ROOT))
        displaced = raw.replace(DELETE_AFTER.encode(), b"", 1) + DELETE_AFTER.encode()
        self.assertNotEqual(raw, displaced)
        for bad in (old, raw[:-1], raw + b"\n", displaced, b"unknown", b"", None, bytearray(raw), raw.decode()):
            with self.subTest(type=type(bad).__name__), self.assertRaises(ValueError):
                recovery.current_source_before_recovery(SOURCE, bad, ROOT)
        for name in (None, 1, Path(SOURCE), [], "../foreign"):
            with self.subTest(relative=type(name).__name__), self.assertRaises(ValueError):
                recovery.current_source_before_recovery(name, raw, ROOT)
        foreign = b"unlisted source DATA, never current acceptance"
        self.assertIs(foreign, recovery.current_source_before_recovery(
            "scripts/ci/unlisted-callback793.py", foreign, ROOT))
        self.assertIs(foreign, recovery.peel_recovery_for_history(SOURCE, foreign, ROOT))
        # The document ingress owns fragment SHA validation; the private inverse
        # receives an already validated binding and still checks exact endpoints.
        from ci_source_domain740 import _binding as binding740
        forged = deepcopy(row)
        forged["fragments"][0]["before_fragment_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            binding740(forged, recovery.BEFORE[SOURCE], recovery.FRAGMENT_COUNTS[SOURCE])
        forged_inverse = deepcopy(row)
        forged_inverse["after_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            recovery._inverse(raw, forged_inverse)
        self.assertNotIn("scripts/ci/test_android_camera_callback_configure_once793.py", recovery.dependency_inputs())
        self.assertEqual((43, 8, 56), (len(document["bindings"]), len(document["added_inputs"]),
                                     len(recovery.dependency_inputs())))

    def test_NEW_native_shape_refuses_before_item_mutation_and_final_source_refusal_never_returns_a_plan(self):
        native = callback._ordinary_bytes(ROOT, callback.SOURCE)
        base = {"test_source_files": sorted(callback.TEST_SOURCES),
                "test_source_sets": deepcopy(callback.TEST_SOURCE_SETS),
                "test_filter": "sentinel-filter", "required_testcases": ["sentinel-case"],
                "required_original_xml": "sentinel-xml"}
        with tempfile.TemporaryDirectory(prefix="callback-configure-once793-") as temporary:
            root = Path(temporary).resolve()
            target = root / callback.SOURCE
            target.parent.mkdir(parents=True)
            mutations = [
                native.replace(b"class AndroidCameraCallbackSubstitutionTest", b"class ForeignCallbackTest", 1),
                native.replace(b"package com.mohamedrejeb.calf.camerapicker", b"package foreign.caller", 1),
                native + b"\n@Test fun foreignDuplicate() {}\n",
                *[native + b"\n" + token + b"\n"
                  for token in (b"@Ignore", b"@Disabled", b"@IgnoredTest", b"assumeTrue", b"assumeFalse", b"Assume")],
            ]
            for changed in mutations:
                self.assertNotEqual(native, changed)
                target.write_bytes(changed)
                item = deepcopy(base)
                with self.assertRaisesRegex(ValueError, "Callback requires its one enabled normally inherited method"):
                    callback.configure_item(root, item)
                self.assertEqual(base, item)
            target.write_bytes(native)
            for field, value in (("test_source_files", [callback.SOURCE]),
                                 ("test_source_sets", ["androidDeviceTest"])):
                item = deepcopy(base); item[field] = value
                original = deepcopy(item)
                with self.assertRaisesRegex(ValueError, "Callback requires its one enabled normally inherited method"):
                    callback.configure_item(root, item)
                self.assertEqual(original, item)
            # Ordinary/native descriptor refusals also leave the item untouched.
            target.unlink()
            item = deepcopy(base)
            with self.assertRaises((FileNotFoundError, OSError, ValueError)):
                callback.configure_item(root, item)
            self.assertEqual(base, item)
            backing = target.with_name("owned-native-backing.kt")
            backing.write_bytes(native)
            target.symlink_to(backing)
            item = deepcopy(base)
            with self.assertRaises((OSError, ValueError)):
                callback.configure_item(root, item)
            self.assertEqual(base, item)
            target.unlink(); target.hardlink_to(backing)
            item = deepcopy(base)
            with self.assertRaises((OSError, ValueError)):
                callback.configure_item(root, item)
            self.assertEqual(base, item)
            target.unlink(); backing.unlink(); target.write_bytes(native)
            # Matching syntax alone cannot certify an incomplete root. The final
            # genuine validator raises and no contract or returned plan exists.
            # The three preceding local mutations are explicit, not atomicity.
            item = deepcopy(base)
            with self.assertRaises((FileNotFoundError, OSError, ValueError)):
                callback.configure_item(root, item)
            self.assertEqual(callback.CLASS + "#" + callback.METHOD, item["test_filter"])
            self.assertEqual(callback.identities(), item["required_testcases"])
            self.assertEqual(1, item["required_original_xml"])
            self.assertNotIn(callback.CONTRACT_KEY, item)

    def test_NEW_fragment_utf8_content_memo_is_exact_strict_error_uncached_and_capacity_bounded(self):
        import ci_source_domain740 as domain
        encode = domain._fragment_utf8_bytes793
        cache = domain._cached_fragment_utf8_bytes793
        cache.cache_clear()
        try:
            self.assertEqual({"maxsize": 64, "typed": False}, cache.cache_parameters())
            for text in ("plain-ascii", "مرحبا 😀 e\u0301", "\x00\n", "a" * 32768):
                expected = text.encode("utf-8", "strict")
                first = encode(text)
                self.assertIs(type(first), bytes)
                self.assertEqual(expected, first)
                hits = cache.cache_info().hits
                self.assertIs(first, encode(text))
                self.assertEqual(hits + 1, cache.cache_info().hits)
            size = cache.cache_info().currsize
            for unused in range(2):
                with self.assertRaises(UnicodeEncodeError):
                    encode("\ud800")
                self.assertEqual(size, cache.cache_info().currsize)
            class ForeignText(str):
                def encode(self, *args, **kwargs):
                    self.calls += 1
                    return super().encode(*args, **kwargs)
            foreign = ForeignText("foreign exact-str subclass")
            foreign.calls = 0
            for unused in range(2):
                self.assertEqual(b"foreign exact-str subclass", encode(foreign))
            self.assertEqual(2, foreign.calls)
            self.assertEqual(size, cache.cache_info().currsize)
            for text in ("", "b" * 32769):
                for unused in range(2):
                    self.assertEqual(text.encode(), encode(text))
                self.assertEqual(size, cache.cache_info().currsize)
            marker = object()
            prior_str = domain.__dict__.get("str", marker)
            domain.str = ForeignText
            try:
                self.assertEqual(b"changed encoder context", encode("changed encoder context"))
                self.assertEqual(size, cache.cache_info().currsize)
            finally:
                if prior_str is marker:
                    del domain.str
                else:
                    domain.str = prior_str
            # Warm encoding must never turn a changed declared SHA into acceptance.
            before, after = "before-مرحبا", "after-😀"
            row = {"before_sha256": sha(before.encode()), "before_bytes": len(before.encode()),
                   "after_sha256": sha(after.encode()), "after_bytes": len(after.encode()),
                   "fragments": [{"before": before, "after": after,
                                  "before_fragment_sha256": sha(before.encode()),
                                  "after_fragment_sha256": sha(after.encode())}]}
            endpoint = {"sha256": row["before_sha256"], "bytes": row["before_bytes"]}
            domain._binding(row, endpoint, 1)
            forged = deepcopy(row)
            forged["fragments"][0]["before_fragment_sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                domain._binding(forged, endpoint, 1)
            cache.cache_clear()
            for index in range(100):
                text = "bounded-new793-" + str(index)
                self.assertEqual(text.encode("utf-8", "strict"), encode(text))
            self.assertEqual((64, 64), (cache.cache_info().maxsize, cache.cache_info().currsize))
        finally:
            cache.cache_clear()

    def test_NEW_private_bulk_documents_immutable_fresh_public_parity_and_full_custody(self):
        from dataclasses import FrozenInstanceError
        from types import SimpleNamespace
        from unittest.mock import patch
        import os
        import macos_share_ci668_composition as joint
        import ci668_outer_source_projection as ci668
        import producer698_source_fixture_recovery as producer698
        import tooling_recovery671_source_projection as tooling671
        import cookie_ci668_outer_source_projection as cookie_outer
        document = recovery._document(ROOT)
        # C15 owns the actual installed preserved selector binding, not a
        # fake substitute: inspect its unchanged code/metadata and exercise its
        # real facade without covertly replaying the accepted old method body.
        controls = AndroidCameraCallbackConfigureOnce793Controls
        routed = controls.__dict__[_HISTORICAL793_SELECTOR]
        facade = routed.__globals__["recovery"]
        self.assertIsInstance(facade, _Historical43RecoveryFor793)
        self.assertIs(recovery, globals()["recovery"])
        self.assertEqual(_HISTORICAL793_SELECTOR, routed.__name__)
        self.assertEqual(controls.__name__ + "." + _HISTORICAL793_SELECTOR, routed.__qualname__)
        self.assertEqual(__name__, routed.__module__)
        self.assertIsNone(routed.__defaults__)
        self.assertIsNone(routed.__kwdefaults__)
        self.assertIs(routed.__code__, routed.__wrapped__.__code__)
        self.assertIs(recovery, routed.__wrapped__.__globals__["recovery"])
        self.assertIs(routed.__defaults__, routed.__wrapped__.__defaults__)
        with patch.object(recovery, "_ordinary", wraps=recovery._ordinary) as archive_reads:
            first_history = facade._document(ROOT)
            second_history = facade._document(ROOT)
        self.assertIsNot(first_history, second_history)
        self.assertEqual(2, archive_reads.call_count)
        self.assertTrue(all(call.args == (ROOT, _HISTORICAL793_ARCHIVE, 512 * 1024)
                            for call in archive_reads.call_args_list))
        self.assertEqual((43, 8), (len(first_history["bindings"]), len(first_history["added_inputs"])))
        self.assertEqual(7, len(first_history["bindings"]["scripts/ci/macos_share_ci668_composition.py"]["fragments"]))
        self.assertEqual(_HISTORICAL793_INPUTS, facade.dependency_inputs())
        self.assertEqual(56, len(facade.dependency_inputs()))
        self.assertNotIn(_HISTORICAL793_ARCHIVE, facade.dependency_inputs())
        self.assertIn(recovery.SPEC, facade.dependency_inputs())
        for name in ("BEFORE", "FRAGMENT_COUNTS", "current_source_before_recovery",
                     "peel_recovery_for_history", "_inverse"):
            self.assertIs(getattr(recovery, name), getattr(facade, name))
        with self.assertRaisesRegex(ValueError, "exact793-owned-historical-canonical-root-required"):
            facade._document(ROOT.parent)
        ordinary = recovery._ordinary
        def changed_historical_archive(root, relative, maximum=recovery.MAX_SOURCE):
            observed = ordinary(root, relative, maximum)
            if relative == _HISTORICAL793_ARCHIVE:
                return (observed[0] + b"changed", *observed[1:])
            return observed
        with patch.object(recovery, "_ordinary", side_effect=changed_historical_archive):
            with self.assertRaisesRegex(ValueError, "exact793-owned-historical43-archive-required"):
                facade._document(ROOT)
        # These actualcurrent document/guard calls do not go through the archive.
        self.assertEqual((46, 8, 59), (len(document["bindings"]), len(document["added_inputs"]),
                                      len(recovery.dependency_inputs())))
        self.assertTrue(all(set(fragment) == {"before", "after", "before_fragment_sha256",
                                              "after_fragment_sha256"}
                            for row in document["bindings"].values() for fragment in row["fragments"]))
        self.assertEqual((46, 8, 59), (len(document["bindings"]), len(document["added_inputs"]),
                                     len(recovery.dependency_inputs())))
        self.assertTrue({ci668.SOURCE_RELATIVE, producer698.SOURCE_RELATIVE,
                         tooling671.SOURCE_RELATIVE} <= set(document["bindings"]))
        import ci_source_domain740 as domain740
        # Bad inventory bytes fail with each unchanged original owning-spec
        # literal, before any shaped document is used; no held source is changed.
        inventory_refusals = (
            (ROOT, joint.SPEC, "exact-share-CI-latest-manifest-required"),
            (ROOT, domain740.SPEC, "exact740-transition-manifest-required"),
            (ROOT, recovery.SPEC, "exact-finite-recovery-transition-manifest-required"),
            (ci668.SPEC_PATH.parent, ci668.SPEC_PATH.name, "The exact final CI668 manifest changed"),
            (producer698.SPEC_PATH.parent, producer698.SPEC_PATH.name, "The exact producer698 successor manifest changed"),
            (tooling671.SPEC_PATH.parent, tooling671.SPEC_PATH.name, "The exact tooling671 derivative manifest changed"))
        for origin, relative, literal in inventory_refusals:
            with self.subTest(inventory_refusal=relative):
                def changed_inventory(actual_root, name, maximum=joint.MAX_SOURCE):
                    raw = joint._ordinary(actual_root, name, maximum)[0]
                    return raw + b"changed" if (actual_root, name) == (origin, relative) else raw
                with patch.object(joint, "_document", side_effect=AssertionError("shaping-before-inventory-refusal")) as shaped:
                    with self.assertRaises(ValueError) as refused:
                        joint._build_source_projection_operation(ROOT, changed_inventory)
                    self.assertEqual(literal, str(refused.exception))
                    self.assertEqual(0, shaped.call_count)
        paths = (joint.CI_OWNER, joint.PRODUCER_OWNER, joint.WORKFLOW, joint.OFFLINE,
                 joint.CURRENT620_CONTROL, joint.CALLBACK_INIT)
        with patch.object(joint, "_document", wraps=joint._document) as fresh:
            with joint._source_projection_operation(ROOT) as operation:
                first_id = id(operation)
                self.assertEqual(1, fresh.call_count)
                with self.assertRaises(FrozenInstanceError):
                    operation._target_root = ROOT.parent
                frozen = operation._joint_documents[ROOT]
                with self.assertRaises(TypeError):
                    frozen["raw_inputs"][joint.WORKFLOW]["sha256"] = "0" * 64
                self.assertNotIn("named_cookie609_manifest",
                                 joint._operation_projection_document(frozen, joint.WORKFLOW, joint.CI_VIEW))
                for module in (ci668, producer698, tooling671):
                    self.assertIn((module.SPEC_PATH.parent, module.SPEC_PATH.name, module.SPEC_SHA256),
                                  operation._spec_origins)
                for relative in paths:
                    with self.subTest(parity=relative):
                        raw = joint._ordinary(ROOT, relative)[0]
                        current = operation._current(relative, raw, joint.CI_VIEW, ROOT)
                        historical = operation._history(relative, raw, joint.CI_VIEW)
                        count = fresh.call_count
                        self.assertEqual(current, joint.current_source_in_view(relative, raw, joint.CI_VIEW, ROOT))
                        self.assertEqual(count + 1, fresh.call_count)
                        self.assertEqual(historical, joint.peel_for_history(relative, raw, joint.CI_VIEW, ROOT))
                        self.assertEqual(count + 2, fresh.call_count)
                self.assertEqual(b"foreign DATA", operation._history("scripts/ci/foreign-c14.py", b"foreign DATA", joint.CI_VIEW))
                with self.assertRaises(ValueError):
                    operation._current("scripts/ci/foreign-c14.py", b"foreign DATA", joint.CI_VIEW, ROOT)
                with self.assertRaises(ValueError):
                    operation._current(joint.WORKFLOW, b"foreign DATA", joint.CI_VIEW, ROOT)
                with self.assertRaisesRegex(ValueError, "exact-target-root"):
                    operation._current(joint.WORKFLOW, b"foreign DATA", joint.CI_VIEW, ROOT.parent)
                with self.assertRaises(ValueError):
                    operation._history(joint.WORKFLOW, b"foreign DATA", "undeclared")
                prior = fresh.call_count
            with joint._source_projection_operation(ROOT) as operation:
                self.assertNotEqual(first_id, id(operation))
                self.assertEqual(prior + 1, fresh.call_count)
        # The private CI helper retains independent original-current operands and
        # named-CI precedence. No restored Cookie image feeds another branch.
        calls = []
        fake = SimpleNamespace(
            _producer_history=lambda relative, raw: calls.append(("producer", raw)) or b"producer",
            _history=lambda relative, raw, view: calls.append(("named", raw)) or b"named")
        with patch.object(cookie_outer, "peel_cookie_outer_for_history",
                          side_effect=lambda relative, raw: calls.append(("cookie", raw)) or b"cookie"):
            self.assertEqual(b"named", ci668._source_before_ci668_operation(
                "scripts/ci/foreign-c14.py", b"current", {"bindings": {}}, fake))
        self.assertEqual([("cookie", b"current"), ("producer", b"current"), ("named", b"current")], calls)
        # Owned tiny custody probes are not repository models. Actual unchanged
        # ordinary descriptor reads must detect restored bytes/mtime via ctime.
        for kind in ("source-restored", "spec-restored", "parent-restored", "root-restored", "primary-refusal"):
            with self.subTest(custody=kind), tempfile.TemporaryDirectory(prefix="c14-custody-probe-") as temporary:
                parent = Path(temporary).resolve()
                root = parent / "root"
                source = root / "scripts/ci/probe.py"
                spec = root / "scripts/ci/manifest.json"
                source.parent.mkdir(parents=True)
                source.write_bytes(b"source-before")
                spec.write_bytes(b'{"fixed":true}\n')
                original_directories = {path: path.stat() for path, identity in
                                        joint._operation_directories(root, "scripts/ci/probe.py")}
                expected_primary = "primary-C14-refusal" if kind == "primary-refusal" else "source-projection-custody-cleanup-refused"
                with patch.object(joint, "_operation_read", wraps=joint._operation_read) as reads:
                    with self.assertRaisesRegex(ValueError, expected_primary) as refused:
                        with joint._source_projection_custody() as capture:
                            capture(root, "scripts/ci/probe.py")
                            capture(root, "scripts/ci/manifest.json", joint.MAX_SPEC)
                            if kind in ("source-restored", "spec-restored", "primary-refusal"):
                                leaf = spec if kind == "spec-restored" else source
                                before = leaf.stat()
                                raw = leaf.read_bytes()
                                leaf.write_bytes(raw + b"changed")
                                leaf.write_bytes(raw)
                                os.utime(leaf, ns=(before.st_atime_ns, before.st_mtime_ns))
                                self.assertEqual(raw, leaf.read_bytes())
                                self.assertNotEqual(before.st_ctime_ns, leaf.stat().st_ctime_ns)
                            elif kind == "parent-restored":
                                directory = root / "scripts"
                                backing = root / "renamed-scripts"
                                directory.rename(backing)
                                backing.rename(directory)
                            else:
                                backing = parent / "renamed-root"
                                root.rename(backing)
                                root.mkdir()
                                root.rmdir()
                                backing.rename(root)
                            if kind in ("parent-restored", "root-restored"):
                                # Restore every named parent/root mtime; ctime
                                # still invalidates transient replacement.
                                for directory, before in original_directories.items():
                                    os.utime(directory, ns=(before.st_atime_ns, before.st_mtime_ns))
                                    self.assertEqual(before.st_mtime_ns, directory.stat().st_mtime_ns)
                                changed_directory = root / "scripts" if kind == "parent-restored" else root
                                self.assertNotEqual(original_directories[changed_directory].st_ctime_ns,
                                                    changed_directory.stat().st_ctime_ns)
                            if kind == "primary-refusal":
                                raise ValueError("primary-C14-refusal")
                    self.assertEqual(4, reads.call_count)  # Both final reads run even after the first refuses.
                    if kind == "primary-refusal":
                        self.assertTrue(any("custody-cleanup-refused" in note for note in refused.exception.__notes__))
        with tempfile.TemporaryDirectory(prefix="c14-cap-build-probe-") as temporary:
            root = Path(temporary).resolve() / "root"
            source = root / "scripts/ci/probe.py"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"bounded-real-source")
            with patch.object(joint, "_operation_read", wraps=joint._operation_read) as reads:
                with joint._source_projection_custody() as capture:
                    self.assertEqual(b"bounded-real-source", capture(root, "scripts/ci/probe.py", joint.MAX_SOURCE))
                    self.assertEqual(b"bounded-real-source", capture(root, "scripts/ci/probe.py", joint.MAX_SPEC))
                self.assertEqual([joint.MAX_SOURCE, joint.MAX_SPEC, joint.MAX_SPEC],
                                 [call.args[2] for call in reads.call_args_list])
            def build_refuses_before_yield(target_root, capture):
                self.assertEqual(root, target_root)
                self.assertEqual(b"bounded-real-source", capture(root, "scripts/ci/probe.py"))
                raise ValueError("build-before-yield-C14-refusal")
            with patch.object(joint, "_operation_read", wraps=joint._operation_read) as reads, \
                 patch.object(joint, "_build_source_projection_operation", side_effect=build_refuses_before_yield):
                with self.assertRaisesRegex(ValueError, "build-before-yield-C14-refusal"):
                    with joint._source_projection_operation(root):
                        self.fail("A refusing build must not yield its operation")
                self.assertEqual(2, reads.call_count)  # Real capture and real finally read.
        # Acquisition/build/shaping are within the same owned finally scope;
        # there is no public unchecked context parameter or retained global instance.
        tree = ast.parse(joint._ordinary(ROOT, joint.OWNER)[0])
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        for name in ("current_source_in_view", "peel_for_history"):
            self.assertEqual(["relative", "payload", "view", "root"],
                             [arg.arg for arg in functions[name].args.args])
        owning = functions["_source_projection_operation"]
        self.assertIsInstance(owning.body[0], ast.With)
        self.assertEqual("_build_source_projection_operation", owning.body[0].body[0].value.func.id)
        self.assertIsInstance(owning.body[0].body[1].value, ast.Yield)

# Only this preserved owning selector has historical document/dependency
# assertions.  Its original code/strict-current guard calls are unchanged; the
# archive read location is deliberately NOT a historical inventory identity.
_HISTORICAL793_SELECTOR = 'test_NEW_strict_current_and_after_only_history_refuse_old_partial_displaced_and_unknown_helper'
_HISTORICAL793_ARCHIVE = 'scripts/ci/fixtures/ci-source-recovery740-742-historical43-configure-once793.json'
_HISTORICAL793_ARCHIVE_BYTES = 172033
_HISTORICAL793_ARCHIVE_SHA256 = "f3aa277b2e4fefcc5c7602eea094f7f3f3e770dc9137c729a655dbbe50920982"
_HISTORICAL793_NAMESPACE_LITERALS = {'BEFORE': {'scripts/ci/android_camera_callback_native_focus.py': {'sha256': '503ca18b83311b557908a50dc9683dec3e74ba1708f23e9515b356c4361459a6', 'bytes': 26749}, 'scripts/ci/android_device_tests.py': {'sha256': '1cff2352789a500cd24f4bdd68909978da1e64be366a5155ecf4f4431ed7cb45', 'bytes': 57052}, 'scripts/ci/android_external328_source_projection.py': {'sha256': '2d5a75be4b8619c1a9ad23e8ecd1d665aed1fffc214946a2e4d658d4999d9e3b', 'bytes': 6627}, 'scripts/ci/android_io_remote_routing_source_projection.py': {'sha256': 'e54d0d68283ef8b93498bd50e11322fb51b50b8fcb7cd26edd4ae12270796e15', 'bytes': 16076}, 'scripts/ci/ci_source_domain740.py': {'sha256': 'c70a1eaa65d3222860dbb38b50671482cb918ba866d0808d57a66e1853a5735d', 'bytes': 11646}, 'scripts/ci/cookie_ci668_outer_source_projection.py': {'sha256': '0164dd126040791c6e591965562aca7710fbcafed67677968907c49abc3215ff', 'bytes': 22579}, 'scripts/ci/cookie_common_jdk_source_projection.py': {'sha256': '16fff9aa57e079c0e98d1a88e5196d458fe4375f7b46a225b94263f70cf8261e', 'bytes': 15750}, 'scripts/ci/fixtures/cookie-ci668-outer-source-inverse.json': {'sha256': '5fc3e645636f9ab3109933fb9bfa5c8abf243b9ea8d9804d73ce3179fcabb14f', 'bytes': 65107}, 'scripts/ci/library_tests.py': {'sha256': '6fdc0947617c41b199f13e63b13056de6c76bb215698e259109c324f219c2127', 'bytes': 412990}, 'scripts/ci/macos_share_ci668_composition.py': {'sha256': '5f85c26830a280c7c0a12e480e826480b8a92dea6ecbd34422c11bfcb2aa375c', 'bytes': 65610}, 'scripts/ci/test_adaptive_controls_native_matrix_source.py': {'sha256': 'a6507c10742d39d51ae17b4ffd4b66af31e37b8f26bd62107e95015a7e5bf9ae', 'bytes': 7282}, 'scripts/ci/test_android_camera_boot_busy.py': {'sha256': '8d239caff727a0d67cdc1481cb7c5b7fd54d69a7b9a97815710a0e523ba7a11c', 'bytes': 15490}, 'scripts/ci/test_android_camera_callback_native_focus.py': {'sha256': '01d3d4fe37b08ebf78297c2bb249f367a51b5e4975d0a2b6a308ebcc431223d2', 'bytes': 24137}, 'scripts/ci/test_android_camera_developer_prerequisite.py': {'sha256': '4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb', 'bytes': 64964}, 'scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py': {'sha256': '607bb6f4ea621a99832b24447144b95b7b864e25a8f580f04193c74f5e31d7c0', 'bytes': 31320}, 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': {'sha256': '048b40f6976fc6af2160c9934b39d620bbdac466d912edfbb9e315dfa92f8bf7', 'bytes': 14611}, 'scripts/ci/test_android_combined_finite_routing.py': {'sha256': '4c8f7ea5ae5c897c9e004b1aba1ca3f1f752c62dd68e15e6096174afd67816d7', 'bytes': 11306}, 'scripts/ci/test_android_device_controller.py': {'sha256': 'c33606e14a957e149fa17a881b304a04cad216c60dec18f176b874e3152b027f', 'bytes': 34633}, 'scripts/ci/test_android_external328_source_projection.py': {'sha256': '58250b74041b79c187572974d0573f2b907e8219855e3341fc96cc7d27ca9fb1', 'bytes': 16665}, 'scripts/ci/test_android_external337_fixture_recovery.py': {'sha256': '14231760d993e84817368da05f715e661957a5c7a4b236badd5d6833213f152e', 'bytes': 11449}, 'scripts/ci/test_android_io_named_system_resource_admission.py': {'sha256': '603830e5de1768528cfb0d9994996faadba76a9694d0f5441afb0b311d75cf42', 'bytes': 17126}, 'scripts/ci/test_android_io_oversize_focus.py': {'sha256': '186a3de6b625cdb1975a8eaaef9acfffbf3577ac935ccca53fd6ecd8ae972576', 'bytes': 10302}, 'scripts/ci/test_android_io_provider_lifecycle.py': {'sha256': '02e8599d8738e9927093ffd7715c8c56d56394055af1e2018fa8ccbf273786fa', 'bytes': 56102}, 'scripts/ci/test_android_io_remote_routing_source_projection.py': {'sha256': '4b7b3897078ee1bfbfeac2178f1b18337c48fe0bc6caa915e60ce3ea82ab8aa7', 'bytes': 28891}, 'scripts/ci/test_android_kvm_timeline.py': {'sha256': '9eab5e2173ca1bb3520028d11bdeefb03dad8a47a43f1872342d5979d5ca7f32', 'bytes': 21135}, 'scripts/ci/test_android_permission_demo_call_denial_recovery.py': {'sha256': '7afda82f59738a09ce57fa5cfbea9c9a527128eca72ee6ca7ae802ace026837e', 'bytes': 22508}, 'scripts/ci/test_android_permission_demo_selector.py': {'sha256': '600ff97eb5064eca6944efb5a46f5bce7ddd203c0a2946f8098bd3056938985a', 'bytes': 15677}, 'scripts/ci/test_android_share_recipient.py': {'sha256': '5be154bf28092340466ab13cc04ce9d6a49479a32aacf1fde3d8a7fb4b5bd3de', 'bytes': 13813}, 'scripts/ci/test_apple_image_launcher_source_projection.py': {'sha256': 'e9af322336f08c49c6a4456fe60edaa8fa44884c8161dff42f707d94effb4ad7', 'bytes': 22811}, 'scripts/ci/test_calendar_share_selector_source_projection.py': {'sha256': '714e8c7bd6342be0d37c7f0f0e7527b371ae3358400109dca5c982bb9322e792', 'bytes': 13582}, 'scripts/ci/test_camera_home571_fixture_recovery.py': {'sha256': '8550a9b29b24f3f752b33408364df8a8de2f414dbcd126bb5500229727ee9e17', 'bytes': 6701}, 'scripts/ci/test_camera_home_affinity_source_projection.py': {'sha256': 'd894b092b54022a22e297556661a7f4aaf68cf495e1aebb993aa846051711585', 'bytes': 9445}, 'scripts/ci/test_camera_ios_ownership_source_projection.py': {'sha256': '1c45769bbb296e47c2302e7d2c7754efcd916febfccfddd332c817308f306182', 'bytes': 14382}, 'scripts/ci/test_camera_producer698_fixture_recovery.py': {'sha256': '23aafbafb58b4f6822c999693dc932c5ac02975a2dfd8ce29308e30a12978b96', 'bytes': 7741}, 'scripts/ci/test_ci668_outer_source_projection.py': {'sha256': '0f2560146366ae31dd148a396a4236055b9928342d427aa5013f18c356419342', 'bytes': 8675}, 'scripts/ci/test_ci_source_domain740.py': {'sha256': '03111f061f387416a140e4321a69b5d9f3ba14805d0b9c014f1b3ba6afbec8e7', 'bytes': 16201}, 'scripts/ci/test_macos_share_ci668_composition.py': {'sha256': '7f206eaf8a6dd3570e094174fbf689da38025e6e8a9c18c1ea69724c12b71443', 'bytes': 69664}, 'scripts/ci/test_platform_recovery659_source_projection.py': {'sha256': 'c7d3a9239fb5c20bd0cad7a4aaf38261ab50e5e62d26851fee96e9bc27e9070e', 'bytes': 17706}, 'scripts/ci/test_producer698_shared_fixture_recovery676.py': {'sha256': '59d98496da46334866742972b89d2d44d14074835d9122fdabff48419e04ccf1', 'bytes': 38034}, 'scripts/ci/test_source_path_memoization714.py': {'sha256': '1ff8cd6a51d44d8ba8b36ca968a43e46fb4ba79dc3e95f926cf204312750fcfd', 'bytes': 6913}, 'scripts/ci/test_tooling656_fixture_recovery.py': {'sha256': '935bf50eaaa0d07614aa3537d2d27a8fa1794521c2300c02c6f62cf46fcfbf17', 'bytes': 13641}, 'scripts/ci/webview_content_policy_source_projection.py': {'sha256': 'ad544703072bd892274a08b29304f313d1915d8c24840f6d136474ea1e560253', 'bytes': 14440}, 'settings.gradle.kts': {'sha256': '773bee85a4fba6c19262dfd1bf4eca80726b1378dcba79d526ac1a515aa60f7c', 'bytes': 2423}}, 'FRAGMENT_COUNTS': {'scripts/ci/android_camera_callback_native_focus.py': 1, 'scripts/ci/android_device_tests.py': 2, 'scripts/ci/android_external328_source_projection.py': 1, 'scripts/ci/android_io_remote_routing_source_projection.py': 4, 'scripts/ci/ci_source_domain740.py': 6, 'scripts/ci/cookie_ci668_outer_source_projection.py': 13, 'scripts/ci/cookie_common_jdk_source_projection.py': 4, 'scripts/ci/fixtures/cookie-ci668-outer-source-inverse.json': 2, 'scripts/ci/library_tests.py': 1, 'scripts/ci/macos_share_ci668_composition.py': 7, 'scripts/ci/test_adaptive_controls_native_matrix_source.py': 4, 'scripts/ci/test_android_camera_boot_busy.py': 1, 'scripts/ci/test_android_camera_callback_native_focus.py': 8, 'scripts/ci/test_android_camera_developer_prerequisite.py': 2, 'scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py': 1, 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': 1, 'scripts/ci/test_android_combined_finite_routing.py': 5, 'scripts/ci/test_android_device_controller.py': 5, 'scripts/ci/test_android_external328_source_projection.py': 1, 'scripts/ci/test_android_external337_fixture_recovery.py': 1, 'scripts/ci/test_android_io_named_system_resource_admission.py': 3, 'scripts/ci/test_android_io_oversize_focus.py': 2, 'scripts/ci/test_android_io_provider_lifecycle.py': 1, 'scripts/ci/test_android_io_remote_routing_source_projection.py': 2, 'scripts/ci/test_android_kvm_timeline.py': 4, 'scripts/ci/test_android_permission_demo_call_denial_recovery.py': 4, 'scripts/ci/test_android_permission_demo_selector.py': 3, 'scripts/ci/test_android_share_recipient.py': 3, 'scripts/ci/test_apple_image_launcher_source_projection.py': 1, 'scripts/ci/test_calendar_share_selector_source_projection.py': 4, 'scripts/ci/test_camera_home571_fixture_recovery.py': 1, 'scripts/ci/test_camera_home_affinity_source_projection.py': 3, 'scripts/ci/test_camera_ios_ownership_source_projection.py': 1, 'scripts/ci/test_camera_producer698_fixture_recovery.py': 1, 'scripts/ci/test_ci668_outer_source_projection.py': 1, 'scripts/ci/test_ci_source_domain740.py': 5, 'scripts/ci/test_macos_share_ci668_composition.py': 1, 'scripts/ci/test_platform_recovery659_source_projection.py': 1, 'scripts/ci/test_producer698_shared_fixture_recovery676.py': 3, 'scripts/ci/test_source_path_memoization714.py': 1, 'scripts/ci/test_tooling656_fixture_recovery.py': 3, 'scripts/ci/webview_content_policy_source_projection.py': 5, 'settings.gradle.kts': 1}, 'ADDED_INPUTS': {'docs/testing/installed-jdk17-prerequisite.md': {'bytes': 2744, 'sha256': '7be847de00c744b0174d65090b62e6769309cc2eafa579f17794cdf92eea2959'}, 'scripts/ci/android_permission_selected_context.py': {'bytes': 3811, 'sha256': '8e0e35f299a1c93655a719e9b9a143a916bf693337e0b7bb9a782e5c2b7ccccb'}, 'scripts/ci/core_history_import_discovery730_controls.py': {'bytes': 8108, 'sha256': '2dd14827f35ff989482bc1278138d8ac4cff5f3ad9d6fb477ecddb45489bf93c'}, 'scripts/ci/test_android_controller_admission_context.py': {'bytes': 8466, 'sha256': '283a7fdb18d53b3ce43229a29e1060978b869cc88a185d342b80c1e7b72af5c7'}, 'scripts/ci/test_android_permission_selected_context.py': {'bytes': 7040, 'sha256': '3df7a6402e648c146255bd62ef25346c43bbf1191b98d9b7abdd316fbbb8b46a'}, 'scripts/ci/test_external328_337_failed_ingress730.py': {'bytes': 7825, 'sha256': '9af25f0a9bff123207d49f0b6a77f59af0a15a5c62c6d2038fec523305c90b73'}, 'scripts/ci/test_foojay_six_owner_settings_history742.py': {'bytes': 16879, 'sha256': 'd29e2f83ca06423accf17500d80d352acadb81a58a7516579441cbf84612a876'}, 'scripts/ci/test_permission_manifest_kvm_context742.py': {'bytes': 7855, 'sha256': 'a1156c3f94885ef2779a7346f42749e574f7159b3437776dd6b5007631e9d9e8'}}, 'OWNER': 'scripts/ci/ci_source_recovery740_742.py', 'CONTROL': 'scripts/ci/test_ci_source_recovery740_742.py', 'SPEC': 'scripts/ci/fixtures/ci-source-recovery740-742-source-inverse.json', 'CURRENT303_SPEC': 'scripts/ci/fixtures/macos-share-ci668-composition.json', 'CURRENT303_ENDPOINT': {'sha256': '06d04d038b06c00e5aafb9b7defdf39ae069f3df305e4dbc84198bc8ed178a24', 'bytes': 518906}, 'DOMAIN740_SPEC': 'scripts/ci/fixtures/ci-source-domain740-source-inverse.json', 'DOMAIN740_ENDPOINT': {'sha256': '5b450daf9874a62a4b452b0d6502c3a77426e670ec6fd79a6b1ed3a3aecf6e52', 'bytes': 36274}, 'SCOPE': 'Exact742 permission/controller, failed743 screenshot/IO/Camera contexts and installed-JDK17 settings comparison and actual library input membership above accepted740; original730 failed/import and named/history contexts with strict/after-only Android ingress; source-only, ZERO compiler/native/consumer/trust/closure; R4 exact owning IO module-import placement and preserved busy RAW mutation refusal; R5 exact cases-only AppKit successor to unchanged original Content/Share pin; no private472 growth; R6 exact Content-owner740 Cookie comparison and cases-only after/history continuation'}
_HISTORICAL793_INPUTS = frozenset(('docs/testing/installed-jdk17-prerequisite.md', 'scripts/ci/android_camera_callback_native_focus.py', 'scripts/ci/android_device_tests.py', 'scripts/ci/android_external328_source_projection.py', 'scripts/ci/android_io_remote_routing_source_projection.py', 'scripts/ci/android_permission_selected_context.py', 'scripts/ci/ci_source_domain740.py', 'scripts/ci/ci_source_recovery740_742.py', 'scripts/ci/cookie_ci668_outer_source_projection.py', 'scripts/ci/cookie_common_jdk_source_projection.py', 'scripts/ci/core_history_import_discovery730_controls.py', 'scripts/ci/fixtures/ci-source-domain740-source-inverse.json', 'scripts/ci/fixtures/ci-source-recovery740-742-source-inverse.json', 'scripts/ci/fixtures/cookie-ci668-outer-source-inverse.json', 'scripts/ci/fixtures/macos-share-ci668-composition.json', 'scripts/ci/library_tests.py', 'scripts/ci/macos_share_ci668_composition.py', 'scripts/ci/test_adaptive_controls_native_matrix_source.py', 'scripts/ci/test_android_camera_boot_busy.py', 'scripts/ci/test_android_camera_callback_native_focus.py', 'scripts/ci/test_android_camera_developer_prerequisite.py', 'scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py', 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py', 'scripts/ci/test_android_combined_finite_routing.py', 'scripts/ci/test_android_controller_admission_context.py', 'scripts/ci/test_android_device_controller.py', 'scripts/ci/test_android_external328_source_projection.py', 'scripts/ci/test_android_external337_fixture_recovery.py', 'scripts/ci/test_android_io_named_system_resource_admission.py', 'scripts/ci/test_android_io_oversize_focus.py', 'scripts/ci/test_android_io_provider_lifecycle.py', 'scripts/ci/test_android_io_remote_routing_source_projection.py', 'scripts/ci/test_android_kvm_timeline.py', 'scripts/ci/test_android_permission_demo_call_denial_recovery.py', 'scripts/ci/test_android_permission_demo_selector.py', 'scripts/ci/test_android_permission_selected_context.py', 'scripts/ci/test_android_share_recipient.py', 'scripts/ci/test_apple_image_launcher_source_projection.py', 'scripts/ci/test_calendar_share_selector_source_projection.py', 'scripts/ci/test_camera_home571_fixture_recovery.py', 'scripts/ci/test_camera_home_affinity_source_projection.py', 'scripts/ci/test_camera_ios_ownership_source_projection.py', 'scripts/ci/test_camera_producer698_fixture_recovery.py', 'scripts/ci/test_ci668_outer_source_projection.py', 'scripts/ci/test_ci_source_domain740.py', 'scripts/ci/test_ci_source_recovery740_742.py', 'scripts/ci/test_external328_337_failed_ingress730.py', 'scripts/ci/test_foojay_six_owner_settings_history742.py', 'scripts/ci/test_macos_share_ci668_composition.py', 'scripts/ci/test_permission_manifest_kvm_context742.py', 'scripts/ci/test_platform_recovery659_source_projection.py', 'scripts/ci/test_producer698_shared_fixture_recovery676.py', 'scripts/ci/test_source_path_memoization714.py', 'scripts/ci/test_tooling656_fixture_recovery.py', 'scripts/ci/webview_content_policy_source_projection.py', 'settings.gradle.kts'))


def _clone_owned793_callable(function, namespace):
    # Actual trusted, unchanged code only; NEVER compile/restore fixture code.
    cloned = _FunctionType(function.__code__, namespace, function.__name__,
                           function.__defaults__, function.__closure__)
    cloned.__qualname__ = function.__qualname__
    cloned.__module__ = function.__module__
    cloned.__doc__ = function.__doc__
    cloned.__kwdefaults__ = (None if function.__kwdefaults__ is None
                            else function.__kwdefaults__.copy())
    cloned.__annotations__ = function.__annotations__.copy()
    cloned.__dict__.update(function.__dict__)
    return cloned


def _historical793_namespace():
    namespace = recovery._document.__globals__.copy()
    # These are exact sealed C13 schema literals, not data learned from a
    # supplied current payload or a global admission/document cache.
    namespace.update(deepcopy(_HISTORICAL793_NAMESPACE_LITERALS))
    namespace["MODIFIED"] = frozenset(namespace["BEFORE"])
    return namespace


def _historical793_archive_ordinary(root, relative, maximum):
    if (type(root) is not type(ROOT) or root != ROOT or root != recovery.ROOT
            or relative != _HISTORICAL793_ARCHIVE
            or type(maximum) is not int or maximum != 512 * 1024):
        raise ValueError("exact793-owned-historical-archive-root-and-cap-required")
    observed = recovery._ordinary(root, relative, maximum)
    raw = observed[0]
    if (type(raw) is not bytes or len(raw) != _HISTORICAL793_ARCHIVE_BYTES
            or sha(raw) != _HISTORICAL793_ARCHIVE_SHA256):
        raise ValueError("exact793-owned-historical43-archive-required")
    return observed


class _Historical43RecoveryFor793:
    def _document(self, root=ROOT):
        if type(root) is not type(ROOT) or root != ROOT or root != recovery.ROOT:
            raise ValueError("exact793-owned-historical-canonical-root-required")
        namespace = _historical793_namespace()
        namespace["SPEC"] = _HISTORICAL793_ARCHIVE
        namespace["SPEC_SHA256"] = _HISTORICAL793_ARCHIVE_SHA256
        namespace["_ordinary"] = _historical793_archive_ordinary
        # Fresh capped archive read/SHA before the unchanged owning43/joint7
        # schema body.  No module globals or production functions are mutated.
        return _clone_owned793_callable(recovery._document, namespace)(root)

    def dependency_inputs(self):
        self._document(ROOT)  # Fresh exact archive admission, never held DATA.
        namespace = _historical793_namespace()
        # SPEC remains the ORIGINAL C13 identity here, NOT the archive path.
        result = _clone_owned793_callable(recovery.dependency_inputs, namespace)()
        if result != _HISTORICAL793_INPUTS:
            raise ValueError("exact793-owned-historical56-inventory-required")
        return result

    def __getattr__(self, name):
        if name not in {"BEFORE", "FRAGMENT_COUNTS", "current_source_before_recovery",
                        "peel_recovery_for_history", "_inverse"}:
            raise AttributeError(name)
        # Strict-current/history/inverse guards always hit actualcurrent.
        return getattr(recovery, name)


def _install_exact793_historical_binding():
    controls = AndroidCameraCallbackConfigureOnce793Controls
    original = controls.__dict__[_HISTORICAL793_SELECTOR]
    namespace = original.__globals__.copy()
    namespace["recovery"] = _Historical43RecoveryFor793()
    routed = _clone_owned793_callable(original, namespace)
    routed.__wrapped__ = original
    setattr(controls, _HISTORICAL793_SELECTOR, routed)


_install_exact793_historical_binding()



# NEW794 owns only the source-confirmed finite Cookie CI-owner seam.
# These controls do not invoke any accepted793 test method or create a model.
def _cookie_ci_inverse794(payload, row):
    if (len(payload), sha(payload)) != (row["after_bytes"], row["after_sha256"]):
        raise AssertionError("Exact whole owning afterimage DATA is required")
    restored = payload
    for item in reversed(row["fragments"]):
        if set(item) != {"before", "after", "before_fragment_sha256", "after_fragment_sha256"}:
            raise AssertionError("The unchanged four-key source fragment schema is required")
        before, after = item["before"].encode(), item["after"].encode()
        if (sha(before), sha(after)) != (item["before_fragment_sha256"], item["after_fragment_sha256"]):
            raise AssertionError("Both unchanged fragment SHA operands are required")
        if restored.count(after) != 1:
            raise AssertionError("One complete inverse source site is required")
        restored = restored.replace(after, before, 1)
    if (len(restored), sha(restored)) != (row["before_bytes"], row["before_sha256"]):
        raise AssertionError("Exact whole original preimage DATA is required")
    return restored


def _cookie_ci_forward794(payload, row):
    if (len(payload), sha(payload)) != (row["before_bytes"], row["before_sha256"]):
        raise AssertionError("Exact whole original preimage DATA is required")
    result = payload
    for item in row["fragments"]:
        before, after = item["before"].encode(), item["after"].encode()
        if result.count(before) != 1:
            raise AssertionError("One complete forward source site is required")
        result = result.replace(before, after, 1)
    if (len(result), sha(result)) != (row["after_bytes"], row["after_sha256"]):
        raise AssertionError("Exact whole owning afterimage DATA is required")
    return result


class CookieCI668OwnerRoute794Controls(unittest.TestCase):
    def test_NEW_cookie_CI_exact_current_route_preserves_all40_actual_source_digests(self):
        import cookie_ci668_outer_source_projection as outer
        document, source_digest = outer._document(ROOT)
        expected = outer._expected(document, source_digest)
        self.assertEqual(40, len(expected))
        raw = {name: outer.ordinary_bytes(ROOT, name) for name in expected}
        reported = outer.validate_current_sources(ROOT)
        self.assertEqual({name: sha(payload) for name, payload in raw.items()}, reported)
        self.assertEqual(reported, outer.current_input_hashes(ROOT))
        self.assertEqual(sha(raw[outer.SOURCE_RELATIVE]), source_digest)
        recovery_row = recovery._document(ROOT)["bindings"][outer.CI_GUARD]
        owner_after = _cookie_ci_inverse794(raw[outer.CI_GUARD], recovery_row)
        self.assertEqual("41979c2e9eb4b74b7da41da42408ac636d60102fea10269b1d181992df4bea5f", sha(owner_after))
        self.assertEqual(document["bindings"][outer.CI_GUARD]["after_sha256"], sha(owner_after))
        predecessor = _cookie_ci_inverse794(owner_after, document["bindings"][outer.CI_GUARD])
        self.assertEqual(predecessor, outer.current_source_before_cookie_outer(
            outer.CI_GUARD, raw[outer.CI_GUARD], ROOT))
        self.assertEqual(predecessor, outer.source_before_cookie_outer(
            outer.CI_GUARD, raw[outer.CI_GUARD], ROOT))

    def test_NEW_cookie_CI_old_partial_unknown_refuse_current_history_is_after_only(self):
        import cookie_ci668_outer_source_projection as outer
        document, _ = outer._document(ROOT)
        raw = outer.ordinary_bytes(ROOT, outer.CI_GUARD)
        owner_after = _cookie_ci_inverse794(raw, recovery._document(ROOT)["bindings"][outer.CI_GUARD])
        predecessor = _cookie_ci_inverse794(owner_after, document["bindings"][outer.CI_GUARD])
        displaced = raw[1:] + raw[:1]
        self.assertNotEqual(raw, displaced)
        for bad in (owner_after, predecessor, raw[:-1], raw + b"\n", displaced,
                    b"unknown", b"", None, bytearray(raw), raw.decode()):
            with self.subTest(type=type(bad).__name__), self.assertRaises(ValueError):
                outer.current_source_before_cookie_outer(outer.CI_GUARD, bad, ROOT)
        self.assertEqual(predecessor, outer.peel_cookie_outer_for_history(outer.CI_GUARD, raw, ROOT))
        self.assertEqual(predecessor, outer.peel_cookie_outer_for_history(outer.CI_GUARD, owner_after, ROOT))
        self.assertIs(predecessor, outer.peel_cookie_outer_for_history(outer.CI_GUARD, predecessor, ROOT))
        foreign = b"unlisted source DATA is never current certification"
        self.assertIs(foreign, outer.peel_cookie_outer_for_history(outer.CI_GUARD, foreign, ROOT))
        self.assertIs(foreign, outer.current_source_before_cookie_outer("scripts/ci/unlisted-cookie794.py", foreign, ROOT))
        self.assertIs(foreign, outer.peel_cookie_outer_for_history("scripts/ci/unlisted-cookie794.py", foreign, ROOT))

    def test_NEW_cookie_CI_owner_ingress_is_fresh_unlisted_stays_data_and_refusal_propagates(self):
        from unittest.mock import patch
        import ci_source_domain740 as domain740
        import cookie_ci668_outer_source_projection as outer
        raw = outer.ordinary_bytes(ROOT, outer.CI_GUARD)
        prior = _cookie_ci_inverse794(raw, recovery._document(ROOT)["bindings"][outer.CI_GUARD])
        with patch.object(recovery, "_document", wraps=recovery._document) as docs, \
             patch.object(domain740, "current_source_before_domain740",
                          wraps=domain740.current_source_before_domain740) as current:
            first = outer._content_owner_source(outer.CI_GUARD, raw, ROOT, current=True)
            second = outer._content_owner_source(outer.CI_GUARD, raw, ROOT, current=True)
            self.assertEqual((prior, prior), (first, second))
            self.assertEqual(2, current.call_count)
            self.assertEqual(2, docs.call_count)
            self.assertTrue(all(call.args == (outer.CI_GUARD, raw, ROOT) for call in current.call_args_list))
            foreign = b"foreign bounded DATA"
            self.assertIs(foreign, outer._content_owner_source(
                "scripts/ci/unlisted-cookie794.py", foreign, ROOT, current=True))
            self.assertEqual(2, current.call_count)
        marker = ValueError("NEW794-owning-CI-refusal")
        with patch.object(domain740, "current_source_before_domain740", side_effect=marker):
            with self.assertRaises(ValueError) as caught:
                outer._content_owner_source(outer.CI_GUARD, raw, ROOT, current=True)
        self.assertIs(marker, caught.exception)
        with self.assertRaises(ValueError):
            outer._content_owner_source(outer.CI_GUARD, raw, ROOT, current=1)

    def test_NEW_cookie_current_own_template_and_original_inverse_prefixes_stay_exact(self):
        import json
        from unittest.mock import patch
        import cookie_ci668_outer_source_projection as outer
        current = recovery._document(ROOT)
        archived, _ = recovery._ordinary(ROOT, _HISTORICAL793_ARCHIVE, 512 * 1024)
        self.assertEqual((_HISTORICAL793_ARCHIVE_BYTES, _HISTORICAL793_ARCHIVE_SHA256),
                         (len(archived), sha(archived)))
        previous = json.loads(archived)
        for relative, prior_count, tail_count in (
                (outer.SOURCE_RELATIVE, 13, 2), (outer.SPEC_RELATIVE, 2, 1)):
            prior = previous["bindings"][relative]
            row = current["bindings"][relative]
            self.assertEqual(prior_count, len(prior["fragments"]))
            self.assertEqual(prior["fragments"], row["fragments"][:prior_count])
            self.assertEqual(prior_count + tail_count, len(row["fragments"]))
            self.assertEqual((prior["before_bytes"], prior["before_sha256"]),
                             (row["before_bytes"], row["before_sha256"]))
            raw = outer.ordinary_bytes(ROOT, relative)
            original = _cookie_ci_inverse794(raw, row)
            self.assertEqual(raw, _cookie_ci_forward794(original, row))
            prior_current = _cookie_ci_forward794(original, prior)
            if relative == outer.SPEC_RELATIVE:
                old_document = json.loads(prior_current)
        document, reported = outer._document(ROOT)
        self.assertEqual({key: value for key, value in old_document.items() if key != "own_guard"},
                         {key: value for key, value in document.items() if key != "own_guard"})
        self.assertEqual(sha(outer.ordinary_bytes(ROOT, outer.SOURCE_RELATIVE)), reported)
        real = outer.ordinary_bytes
        for relative, literal in (
                (outer.SOURCE_RELATIVE, "Exact complete newest Cookie outer guard template is required"),
                (outer.SPEC_RELATIVE, "Exact newest Cookie outer manifest is required")):
            def changed(root, name, maximum=outer.MAX_SOURCE_BYTES):
                payload = real(root, name, maximum)
                return payload + b"\n" if name == relative else payload
            with self.subTest(relative=relative), patch.object(outer, "ordinary_bytes", side_effect=changed):
                with self.assertRaisesRegex(ValueError, literal):
                    outer._document(ROOT)
        native = callback._ordinary_bytes(ROOT, SOURCE)
        self.assertEqual((26714, "8e3dd41b60d44d7566280f7309e3a7dabef385755981554990b4ae5ba32d8875"),
                         (len(native), sha(native)))

if __name__ == "__main__":
    unittest.main()
