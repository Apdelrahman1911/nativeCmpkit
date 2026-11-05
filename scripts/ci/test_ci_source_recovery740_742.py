# SPDX-License-Identifier: Apache-2.0
"""Genuinely NEW central finite-source controls; no accepted method replay.

No compiler, native/runtime, network, Git, publication or issue action executes.
Historical source is comparison data, never imported or written as current code.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

import ci_source_recovery740_742 as recovery
import ci_source_domain740 as domain740
import macos_share_ci668_composition as joint

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def definitions(raw):
    return {node.name: node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef)}


class CentralSourceRecovery740742Controls(unittest.TestCase):
    def test01_outer_complete_roundtrips_reject_old_drift_types_and_unlisted_enrollment(self):
        document = recovery._document(ROOT)
        self.assertEqual(set(recovery.BEFORE), set(document["bindings"]))
        self.assertLessEqual(len((ROOT / recovery.SPEC).read_bytes()), 512 * 1024)
        for relative, row in document["bindings"].items():
            raw = (ROOT / relative).read_bytes()
            old = recovery.current_source_before_recovery(relative, raw, ROOT)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(old), len(old)), relative)
            forward = old
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(before), relative)
                forward = forward.replace(before, after, 1)
            self.assertEqual(raw, forward, relative)
            self.assertEqual(old, recovery.peel_recovery_for_history(relative, raw, ROOT))
            self.assertEqual(old, recovery.peel_recovery_for_history(relative, old, ROOT))
            for bad in (old, raw[:-1], raw + b"\n", b"", None, bytearray(raw), raw.decode()):
                with self.subTest(relative=relative, type=type(bad).__name__), self.assertRaises(ValueError):
                    recovery.current_source_before_recovery(relative, bad, ROOT)
            unknown = raw + b"\n# unqualified central context\n"
            self.assertEqual(unknown, recovery.peel_recovery_for_history(relative, unknown, ROOT))
        for relative in recovery.ADDED_INPUTS:
            raw = (ROOT / relative).read_bytes()
            self.assertEqual(raw, recovery.current_source_before_recovery(relative, raw, ROOT))
            self.assertNotIn(relative, joint.fixture_inputs(ROOT))
            with self.assertRaises(ValueError):
                joint.current_source_in_view(relative, raw, joint.CI_VIEW, ROOT)
        raw = b"unqualified-identity-data"
        self.assertEqual(raw, recovery.current_source_before_recovery("unlisted-source", raw, ROOT))
        for relative in (Path("unlisted-source"), "../foreign", "/foreign", "a/../foreign"):
            with self.subTest(relative=str(relative)), self.assertRaises(ValueError):
                recovery.current_source_before_recovery(relative, raw, ROOT)

    def test02_fresh_actual303_hashes_and_named175_190_40_36_remain_distinct(self):
        document = joint._document(ROOT)
        self.assertEqual(301, len(document["raw_inputs"]))
        self.assertEqual((518906, recovery.CURRENT303_ENDPOINT["sha256"]),
                         (len((ROOT / joint.SPEC).read_bytes()), sha((ROOT / joint.SPEC).read_bytes())))
        self.assertEqual((36274, recovery.DOMAIN740_ENDPOINT["sha256"]),
                         (len((ROOT / domain740.SPEC).read_bytes()), sha((ROOT / domain740.SPEC).read_bytes())))
        actual = joint.current_input_hashes(ROOT)
        original = {relative: row["sha256"] for relative, row in document["raw_inputs"].items()}
        self.assertEqual(303, len(actual))
        self.assertEqual(set(original) | {joint.OWNER, joint.SPEC}, set(actual))
        self.assertEqual({relative: sha((ROOT / relative).read_bytes()) for relative in actual}, actual)
        changed = (domain740.MODIFIED | recovery.MODIFIED) & set(original)
        for relative in set(original) - changed:
            self.assertEqual(original[relative], actual[relative], relative)
        for relative in changed:
            self.assertNotEqual(original[relative], actual[relative], relative)
            current = (ROOT / relative).read_bytes()
            qualified = domain740.current_source_before_domain740(relative, current, ROOT)
            self.assertEqual((document["raw_inputs"][relative]["sha256"], document["raw_inputs"][relative]["bytes"]),
                             (sha(qualified), len(qualified)), relative)
        self.assertEqual(sha((ROOT / joint.OWNER).read_bytes()), actual[joint.OWNER])
        for relative in recovery.dependency_inputs() - joint.fixture_inputs(ROOT):
            self.assertNotIn(relative, actual)
        for view, count in ((joint.CI_VIEW, 175), (joint.PRODUCER_VIEW, 190),
                            (joint.COOKIE_VIEW, 40), (joint.SHARE_VIEW, 36)):
            expected = {relative: row["sha256"] for relative, row in document["predecessor_inputs"][view].items()}
            self.assertEqual(count, len(expected))
            self.assertEqual(expected, joint.predecessor_input_hashes(view, ROOT))
        self.assertEqual(512 * 1024, joint.MAX_SPEC)
        self.assertEqual(512 * 1024, domain740.MAX_SPEC)
        self.assertEqual(512 * 1024, recovery.MAX_SPEC)

    def test03_separate_model_dependencies_are_fresh_ordinary_and_removed_without303_enrollment(self):
        from test_macos_share_ci668_composition import source_model
        expected = joint.fixture_inputs(ROOT) | domain740.dependency_inputs() | recovery.dependency_inputs()
        with source_model() as root:
            model_name = root
            actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(expected, actual)
            self.assertEqual(303, len(joint.fixture_inputs(root)))
            for relative in actual:
                metadata = (root / relative).lstat()
                self.assertTrue(stat.S_ISREG(metadata.st_mode), relative)
                self.assertEqual(1, metadata.st_nlink, relative)
                self.assertEqual((ROOT / relative).read_bytes(), (root / relative).read_bytes(), relative)
            self.assertTrue(recovery.validate_current_sources(root))
            self.assertTrue(domain740.validate_current_sources(root))
            document = joint._document(root)
            for relative in recovery.MODIFIED & set(document["raw_inputs"]):
                raw = (root / relative).read_bytes()
                self.assertEqual(domain740.current_source_before_domain740(relative, raw, root),
                                 joint._raw_payload(relative, raw, document, root), relative)
            for relative in set(recovery.ADDED_INPUTS) | {recovery.OWNER, recovery.CONTROL, recovery.SPEC}:
                self.assertNotIn(relative, joint.fixture_inputs(root))
        self.assertFalse(model_name.exists())

    def test04_finite_manifest_original_authority_fragments_and_aliases_refuse(self):
        original = recovery._document(ROOT)
        selected = recovery.SETTINGS
        changes = (
            lambda doc: doc["original_current303"].update(sha256="0" * 64),
            lambda doc: doc["original740"].update(sha256="0" * 64),
            lambda doc: doc["bindings"][selected].update(before_sha256="0" * 64),
            lambda doc: doc["bindings"][selected].update(after_bytes=True),
            lambda doc: doc["bindings"][selected]["fragments"][0].update(after_fragment_sha256="0" * 64),
            lambda doc: doc["bindings"][selected]["fragments"].append(copy.deepcopy(doc["bindings"][selected]["fragments"][0])),
            lambda doc: doc["added_inputs"].update({"foreign-dependency": {"sha256": "0" * 64, "bytes": 1}}),
        )
        for change in changes:
            fake = copy.deepcopy(original); change(fake)
            encoded = (json.dumps(fake, sort_keys=True, separators=(",", ":")) + "\n").encode()
            with tempfile.TemporaryDirectory(prefix="central-recovery-grammar-") as folder:
                root = Path(folder)
                target = root / recovery.SPEC
                target.parent.mkdir(parents=True)
                target.write_bytes(encoded)
                with patch.object(recovery, "SPEC_SHA256", sha(encoded)), self.assertRaises(ValueError):
                    recovery._document(root)
            self.assertFalse(root.exists())
        raw = (ROOT / recovery.SPEC).read_bytes()
        with tempfile.TemporaryDirectory(prefix="central-recovery-alias-") as folder:
            root = Path(folder); target = root / recovery.SPEC
            target.parent.mkdir(parents=True)
            target.write_bytes(raw + b"\n")
            with self.assertRaises(ValueError): recovery._document(root)
            target.unlink(); backing = target.with_name("backing.json"); backing.write_bytes(raw)
            target.symlink_to(backing)
            with self.assertRaises(ValueError): recovery._document(root)
            target.unlink(); target.hardlink_to(backing)
            with self.assertRaises(ValueError): recovery._document(root)
            target.unlink(); backing.unlink()
        self.assertFalse(root.exists())

    def test05_generic_exclusions_and_pure676_714_keep_actual_and_original_ast_bodies(self):
        document = joint._document(ROOT)
        for relative in recovery.GENERIC_EXCLUSIONS | {joint.NEW_CONTROL, joint.NEW_COOKIE_CONTROL,
                joint.OWNING_COOKIE_CONTROL, joint.CALLBACK_INIT, joint.BUDGET707_CONTROL,
                joint.FAILURE711_HELPER, joint.FAILURE711_CONTROL, joint.FAILURE658_HELPER,
                joint.FAILURE658_CONTROL, joint.PURE676_CONTROL, joint.CURRENT620_CONTROL}:
            raw = (ROOT / relative).read_bytes()
            for view in joint.VIEWS:
                self.assertEqual(raw, joint.peel_for_history(relative, raw, view, ROOT), (relative, view))
        raw = (ROOT / joint.OWNER).read_bytes()
        qualified = domain740.current_source_before_domain740(joint.OWNER, raw, ROOT)
        self.assertEqual(sha(raw), joint._own_payload(raw, document, ROOT))
        for bad in (qualified, raw[:-1], raw + b"\n"):
            with self.assertRaises(ValueError): joint._own_payload(bad, document, ROOT)
        old, current = definitions(qualified), definitions(raw)
        unchanged = ("_binding", "_shape", "_identity", "_ordinary", "_portable_ordinary", "_endpoint",
                     "_descriptor_source_io_supported", "_cached_source_path_parts", "_sealed_predecessor_hashes",
                     "_inverse_to_ancestor", "_freeze_json_content", "_thaw_json_content", "_json_parser_context",
                     "_cached_json_tree", "_json")
        for name in unchanged:
            self.assertEqual(ast.dump(old[name], include_attributes=False),
                             ast.dump(current[name], include_attributes=False), name)
        decorated = [node.name for node in current.values() if any(isinstance(item, ast.Call)
                     and isinstance(item.func, ast.Name) and item.func.id == "lru_cache" for item in node.decorator_list)]
        self.assertEqual(["_cached_source_path_parts", "_cached_json_tree"], decorated)
        self.assertEqual(document["own_guard"]["bytes"], len(qualified))
        needle = ('SPEC_SHA256 = "' + joint.SPEC_SHA256 + '"\n').encode()
        self.assertEqual(1, qualified.count(needle))
        self.assertEqual(document["own_guard"]["template_sha256"],
                         sha(qualified.replace(needle, ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode(), 1)))


    def test06_real_library_snapshot_doc_membership_drift_custody_and_absence_behavior(self):
        import library_tests as lt
        self.assertEqual(ROOT, lt.ROOT)
        self.assertEqual(1, lt.ROOT_INPUTS.count(recovery.INSTALLED_JDK17))
        doc_payload = (ROOT / recovery.INSTALLED_JDK17).read_bytes()
        document = recovery._document(ROOT)
        self.assertEqual(document["added_inputs"][recovery.INSTALLED_JDK17],
                         {"sha256": sha(doc_payload), "bytes": len(doc_payload)})
        current_settings = (ROOT / recovery.SETTINGS).read_bytes()
        old_settings = recovery.current_source_before_recovery(recovery.SETTINGS, current_settings, ROOT)
        # Explicit calf-core discovery fixture permits a tiny real snapshot.
        # It is NOT admitted as current settings or a native/consumer checkout.
        # Mandatory core admission below receives the actual RAW settings operand.
        discovery_settings = b'include(\n    ":calf-core",\n)\n'
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-jdk17-real-snapshot-") as folder:
            root = Path(folder)
            payloads = {recovery.SETTINGS: discovery_settings,
                        "calf-core/build.gradle.kts": b"// Snapshot discovery only; never compiled or executed.\n",
                        recovery.INSTALLED_JDK17: doc_payload,
                        recovery.SPEC: (ROOT / recovery.SPEC).read_bytes()}
            for relative, payload in payloads.items():
                path = root / relative
                path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                path.write_bytes(payload); path.chmod(0o644)
                metadata = path.lstat()
                self.assertTrue(stat.S_ISREG(metadata.st_mode))
                self.assertEqual(1, metadata.st_nlink)
            expected = {relative: sha(payload) for relative, payload in payloads.items()}
            # Real discovery, safe_path, file hashing and snapshot logic execute;
            # neither projects nor snapshot_inputs nor current admission is mocked.
            before = lt.snapshot_inputs(root)
            self.assertEqual(expected, before)
            self.assertEqual(old_settings, recovery.current_source_before_recovery(
                recovery.SETTINGS, current_settings, root))
            doc_path = root / recovery.INSTALLED_JDK17
            drift = bytes([doc_payload[0] ^ 1]) + doc_payload[1:]
            doc_path.write_bytes(drift)
            changed = lt.snapshot_inputs(root)
            self.assertEqual(set(before), set(changed))
            self.assertEqual({recovery.INSTALLED_JDK17},
                             {relative for relative in before if before[relative] != changed[relative]})
            self.assertNotEqual(lt.input_digest(before), lt.input_digest(changed))
            with self.assertRaises(ValueError):
                recovery.current_source_before_recovery(recovery.SETTINGS, current_settings, root)
            doc_path.unlink()
            # Preserve legacy synthetic snapshots' absent-file behavior, WITHOUT
            # waiving the mandatory current-core missing-doc refusal.
            absent = lt.snapshot_inputs(root)
            self.assertEqual({relative: value for relative, value in expected.items()
                              if relative != recovery.INSTALLED_JDK17}, absent)
            with self.assertRaises((ValueError, OSError)):
                recovery.current_source_before_recovery(recovery.SETTINGS, current_settings, root)
            doc_path.write_bytes(doc_payload); doc_path.chmod(0o644)
            real_sha256 = lt.sha256

            def hash_then_append_to_owned_doc(path):
                value = real_sha256(path)  # Actual hash, never a fabricated result.
                if path == doc_path:
                    with path.open("ab") as stream:
                        self.assertEqual(1, stream.write(b"\n"))
                return value

            with patch.object(lt, "sha256", side_effect=hash_then_append_to_owned_doc):
                with self.assertRaisesRegex(ValueError, "Source input changed while capturing its hash"):
                    lt.snapshot_inputs(root)
            self.assertEqual(doc_payload + b"\n", doc_path.read_bytes())
            doc_path.write_bytes(doc_payload); doc_path.chmod(0o644)
            self.assertEqual(expected, lt.snapshot_inputs(root))
            self.assertEqual(set(payloads), {path.relative_to(root).as_posix()
                             for path in root.rglob("*") if path.is_file()})
            self.assertEqual(old_settings, recovery.current_source_before_recovery(
                recovery.SETTINGS, current_settings, root))
        self.assertFalse(root.exists())


    def test07_real_latest_android_raw_qualifies_core_once_before_the_unchanged_inverse(self):
        controller = "scripts/ci/android_device_tests.py"
        context620 = "scripts/ci/test_producer698_batch_source_fixture_recovery.py"
        self.assertIn(controller, joint.ANDROID_BOUND_PATHS)
        self.assertNotIn(controller, joint.CURRENT_CONTEXT620_PATHS)
        self.assertIn(context620, joint.ANDROID_BOUND_PATHS & joint.CURRENT_CONTEXT620_PATHS)
        document = recovery._document(ROOT)
        android = joint._android_transition(ROOT)
        for relative in (controller, context620):
            raw = (ROOT / relative).read_bytes()
            with patch.object(domain740, "current_source_before_domain740",
                              wraps=domain740.current_source_before_domain740) as newest:
                with patch.object(joint, "source_before_current_context620",
                                  wraps=joint.source_before_current_context620) as context:
                    old = joint.source_before_android_lifecycle(relative, raw, ROOT)
                    newest.assert_called_once_with(relative, raw, ROOT)
                    if relative == context620:
                        context.assert_called_once_with(relative, raw, ROOT)
                    else:
                        context.assert_not_called()
            row = (android["original_bindings"] | android["current_context_bindings"])[relative]
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(old), len(old)))
            for bad in (old, raw[:-1], raw + b"\n"):
                with patch.object(joint, "_android_before",
                                  side_effect=AssertionError("Unqualified RAW crossed the Android inverse")) as nested:
                    with self.assertRaises(ValueError):
                        joint.source_before_android_lifecycle(relative, bad, ROOT)
                    nested.assert_not_called()
        raw = (ROOT / controller).read_bytes()
        original_core = recovery._inverse(raw, document["bindings"][controller])
        with patch.object(joint, "_android_before",
                          side_effect=AssertionError("Old core endpoint crossed current admission")) as nested:
            with self.assertRaises(ValueError):
                joint.source_before_android_lifecycle(controller, original_core, ROOT)
            nested.assert_not_called()
        unbound = b"Unlisted source DATA is never current303 enrollment"
        with patch.object(domain740, "current_source_before_domain740",
                          side_effect=AssertionError("Unbound DATA crossed current admission")) as newest:
            with patch.object(joint, "_android_transition",
                              side_effect=AssertionError("Unbound DATA read an Android recipe")) as recipe:
                self.assertIs(unbound, joint.source_before_android_lifecycle("unlisted-source", unbound, ROOT))
                newest.assert_not_called()
                recipe.assert_not_called()

    def test08_android_history_is_after_only_and_preserves_old_unknown_and_excluded_data(self):
        controller = "scripts/ci/android_device_tests.py"
        context620 = "scripts/ci/test_producer698_batch_source_fixture_recovery.py"
        document = recovery._document(ROOT)
        android = joint._android_transition(ROOT)
        for relative in (controller, context620):
            raw = (ROOT / relative).read_bytes()
            # Calculate only declared source arithmetic. No strict current API
            # is invoked on an already-peeled endpoint to build expectations.
            before_core = (recovery._inverse(raw, document["bindings"][relative])
                           if relative in document["bindings"] else raw)
            if relative in domain740.MODIFIED:
                before_core = domain740._inverse(before_core, domain740._document(ROOT)["bindings"][relative])
            android_after = (joint._current_context620_before(relative, before_core,
                              joint._transition620_document(ROOT))
                             if relative in joint.CURRENT_CONTEXT620_PATHS else before_core)
            old = joint._android_before(relative, android_after, android)
            with patch.object(domain740, "peel_domain740_for_history",
                              wraps=domain740.peel_domain740_for_history) as after_only:
                with patch.object(domain740, "current_source_before_domain740",
                                  side_effect=AssertionError("History strictly readmitted source DATA")):
                    with patch.object(joint, "source_before_current_context620",
                                      side_effect=AssertionError("History strictly readmitted context620")):
                        with patch.object(joint, "current_source_in_view",
                                          side_effect=AssertionError("History traversed a named current view")):
                            observed = joint.peel_android_lifecycle_for_history(relative, raw, ROOT)
                            after_only.assert_called_once_with(relative, raw, ROOT)
                            self.assertEqual(old, observed)
                            self.assertEqual(old, joint.peel_android_lifecycle_for_history(relative, old, ROOT))
                            expected_android_after = (android_after if relative in joint.CURRENT_CONTEXT620_PATHS else old)
                            self.assertEqual(expected_android_after,
                                             joint.peel_android_lifecycle_for_history(relative, android_after, ROOT))
                            for unknown in (raw[:-1], raw + b"\n", b"unknown bounded source DATA"):
                                self.assertIs(unknown, joint.peel_android_lifecycle_for_history(relative, unknown, ROOT))
        for relative, raw in (("unlisted-source", b"unqualified source DATA"),
                              (joint.NEW_COOKIE_CONTROL, (ROOT / joint.NEW_COOKIE_CONTROL).read_bytes())):
            with patch.object(domain740, "peel_domain740_for_history",
                              side_effect=AssertionError("Unbound/excluded DATA crossed history peeling")) as after_only:
                with patch.object(joint, "_android_transition",
                                  side_effect=AssertionError("Unbound/excluded DATA read an Android recipe")) as recipe:
                    self.assertIs(raw, joint.peel_android_lifecycle_for_history(relative, raw, ROOT))
                    after_only.assert_not_called()
                    recipe.assert_not_called()
        helper = definitions((ROOT / joint.OWNER).read_bytes())
        calls = [node.func.id for node in ast.walk(helper["peel_android_lifecycle_for_history"])
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        self.assertEqual(1, calls.count("peel_domain740_for_history"))
        for forbidden in ("current_source_before_domain740", "source_before_current_context620",
                          "current_source_in_view", "_view", "_raw_payload", "current_source_before_recovery"):
            self.assertNotIn(forbidden, calls)


    def test09_exact_io_owning_import_placement_and_new_outer_binding_are_not303_enrollment(self):
        # Genuinely NEW R4 owner only: never replay the accepted previous33.
        relative = "scripts/ci/android_io_remote_routing_source_projection.py"
        document = recovery._document(ROOT)
        row = document["bindings"][relative]
        self.assertEqual(38, len(recovery.MODIFIED - recovery.FIXTURE_SUCCESSORS742 - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(41, len(recovery.MODIFIED - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(39, len(recovery.MODIFIED - recovery.FIXTURE_SUCCESSORS742 - {"scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(42, len(recovery.MODIFIED - {"scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(43, len(recovery.MODIFIED))
        self.assertEqual(4, len(row["fragments"]))
        self.assertEqual(("e54d0d68283ef8b93498bd50e11322fb51b50b8fcb7cd26edd4ae12270796e15", 16076),
                         (row["before_sha256"], row["before_bytes"]))
        self.assertNotIn(relative, recovery.ADDED_INPUTS)
        self.assertIn(relative, joint.fixture_inputs(ROOT))
        self.assertEqual(303, len(joint.fixture_inputs(ROOT)))
        raw = (ROOT / relative).read_bytes()
        self.assertEqual(("da51c70226edceedddbc6176c8244680f1fa6a3350e7adab56fe6faf982c0cc0", 15979),
                         (sha(raw), len(raw)))
        old = recovery.current_source_before_recovery(relative, raw, ROOT)
        self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(old), len(old)))
        forward = old
        for fragment in row["fragments"]:
            before, after = fragment["before"].encode(), fragment["after"].encode()
            self.assertEqual(fragment["before_fragment_sha256"], sha(before))
            self.assertEqual(fragment["after_fragment_sha256"], sha(after))
            self.assertEqual(1, forward.count(before))
            forward = forward.replace(before, after, 1)
        self.assertEqual(raw, forward)
        self.assertEqual(old, recovery.peel_recovery_for_history(relative, raw, ROOT))
        self.assertIs(old, recovery.peel_recovery_for_history(relative, old, ROOT))
        for bad in (old, raw[:-1], raw + b"\n", b"", None, bytearray(raw), raw.decode()):
            with self.subTest(type=type(bad).__name__), self.assertRaises(ValueError):
                recovery.current_source_before_recovery(relative, bad, ROOT)
        unknown = raw + b"\n# unqualified owning IO source\n"
        self.assertIs(unknown, recovery.peel_recovery_for_history(relative, unknown, ROOT))
        latest = joint._document(ROOT)
        self.assertEqual((row["before_sha256"], row["before_bytes"]),
                         (latest["raw_inputs"][relative]["sha256"], latest["raw_inputs"][relative]["bytes"]))
        with patch.object(recovery, "current_source_before_recovery",
                          wraps=recovery.current_source_before_recovery) as ingress:
            qualified = joint._raw_payload(relative, raw, latest, ROOT)
            ingress.assert_called_once_with(relative, raw, ROOT)
        self.assertEqual(old, qualified)
        tree = ast.parse(raw)
        imports = [(alias.name, alias.asname) for node in tree.body if isinstance(node, ast.Import)
                   for alias in node.names if alias.name == "tooling_recovery671_source_projection"]
        self.assertEqual([("tooling_recovery671_source_projection", "tooling671")], imports)
        current, prior = definitions(raw), definitions(old)
        changed = {"source_before_remote_routing", "current_source_before_remote_routing",
                   "peel_remote_routing_for_history"}
        self.assertEqual(set(prior), set(current))
        for name in set(current) - changed:
            self.assertEqual(ast.dump(prior[name], include_attributes=False),
                             ast.dump(current[name], include_attributes=False), name)
        for name in changed:
            self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom))
                                 for node in ast.walk(current[name])), name)
            delegates = [node.func.attr for node in ast.walk(current[name])
                         if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                         and isinstance(node.func.value, ast.Name) and node.func.value.id == "tooling671"]
            self.assertEqual(2, len(delegates), name)
            for forbidden in ("exec", "eval", "compile", "__import__"):
                self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                                     and node.func.id == forbidden for node in ast.walk(current[name])), name)


if __name__ == "__main__":
    unittest.main()
