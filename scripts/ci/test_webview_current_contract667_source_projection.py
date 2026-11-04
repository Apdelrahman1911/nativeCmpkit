# SPDX-License-Identifier: Apache-2.0
"""Exactly six NEW current-owner/provenance/source-command controls; no builds."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import library_tests as r
import camera_ios_ownership_source_projection as camera_history
import platform_recovery659_source_projection as prior_history
import webview_content_policy_native_focus as policy
import webview_content_policy_source_projection as content_history
import webview_current_contract667_source_projection as history
from test_webview_content_policy_native_focus import copy_model_checkout, native_plan

ROOT = Path(__file__).resolve().parents[2]


class WebViewCurrentContract667Controls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve(); copy_model_checkout(self.root)

    def test_exact_current_owner_contract_binds_reviewed_raw_owner_guard_manifest_and_all_five_focus_identities(self):
        self.assertTrue(history.validate_current_sources(ROOT))
        with patch.object(history, "current_source_before_contract667",
                          wraps=history.current_source_before_contract667) as ingress:
            content_history.current_source_before_content_policy(history.SOURCE, (ROOT / history.SOURCE).read_bytes())
            ingress.assert_called_once_with(history.SOURCE, (ROOT / history.SOURCE).read_bytes())
        with patch.object(history, "validate_current_sources", wraps=history.validate_current_sources) as raw_gate:
            self.assertTrue(camera_history.validate_current_sources(ROOT))
            raw_gate.assert_called_once_with(ROOT)
        expected = history.current_contract_hashes()
        self.assertEqual(history.contract_input_paths(), set(expected))
        for focus in policy.FOCUSES:
            plan = native_plan(self.root, focus); item = plan["expected"][0]
            contract = policy.source_contract(self.root, focus)
            self.assertEqual(contract, item[policy.CONTRACT_FIELD])
            self.assertTrue(r.validate_test_focus(plan))
            self.assertEqual(policy.identities(focus), contract["selected_testcases"])
            self.assertEqual(0, contract["compiler_executions_attested"])
            self.assertEqual(0, contract["native_executions_attested"])
            self.assertTrue(set(expected) <= set(item["test_source_files"]))
            for name, digest in expected.items():
                self.assertEqual(digest, contract["source_hashes"][name])
                self.assertEqual(digest, history.sha((self.root / name).read_bytes()))
            self.assertNotEqual(history._qualified_document()["bindings"][history.SOURCE]["before_sha256"],
                                contract["source_hashes"][history.SOURCE])

    def test_sealed659_predecessor_and_original_webview_added_owner_remain_the_exact_origin(self):
        document = history._qualified_document()
        original, prior = history._sealed_origin_documents()
        owner = document["bindings"][history.SOURCE]
        self.assertEqual(prior["bindings"][history.SOURCE]["after_sha256"], owner["before_sha256"])
        self.assertEqual(prior["bindings"][history.SOURCE]["after_bytes"], owner["before_bytes"])
        self.assertEqual(original["added_inputs"][history.SOURCE],
                         prior["bindings"][history.SOURCE]["before_sha256"])
        self.assertEqual(original["added_inputs"][history.CONTROL_SOURCE],
                         document["bindings"][history.CONTROL_SOURCE]["before_sha256"])
        self.assertEqual(prior["added_inputs"][history.PRIOR_CONTROL],
                         document["bindings"][history.PRIOR_CONTROL]["before_sha256"])
        for name in history.BOUND_PATHS:
            current = (ROOT / name).read_bytes()
            approved = history.source_before_contract667(name, current)
            self.assertEqual(document["bindings"][name]["before_sha256"], history.sha(approved))
            self.assertEqual(approved, history.source_before_contract667(name, approved))
            self.assertEqual(approved, history.current_source_before_contract667(name, current))
            self.assertEqual(approved, history.peel_contract667_for_history(name, current))
        original_owner = prior_history.source_before_platform_recovery659(
            history.SOURCE, history.source_before_contract667(history.SOURCE, (ROOT / history.SOURCE).read_bytes()))
        self.assertEqual(original["added_inputs"][history.SOURCE], history.sha(original_owner))
        for name, digest in history.ORIGIN_MANIFESTS.items():
            self.assertEqual(digest, history.sha((ROOT / name).read_bytes()))
        changed_document = copy.deepcopy(document)
        changed_document["bindings"][history.SOURCE]["before_sha256"] = "a" * 64
        changed_original = copy.deepcopy(original)
        changed_original["added_inputs"][history.SOURCE] = "b" * 64
        changed_prior = copy.deepcopy(prior)
        changed_prior["bindings"][history.SOURCE]["before_sha256"] = "c" * 64
        changed_length = copy.deepcopy(prior)
        changed_length["bindings"][history.SOURCE]["after_bytes"] = True
        for new, old, prior_doc in ((changed_document, original, prior), (document, changed_original, prior),
                                    (document, original, changed_prior), (document, original, changed_length)):
            with self.assertRaises(ValueError): history._check_owner_origin(new, old, prior_doc)

    def test_old_original_and659_owner_images_and_unknown_partial_or_foreign_bytes_refuse_as_current(self):
        path = self.root / history.SOURCE; current = path.read_bytes()
        approved659 = history.source_before_contract667(history.SOURCE, current)
        original = prior_history.source_before_platform_recovery659(history.SOURCE, approved659)
        for payload in (approved659, original, current + b"\n", current[:-1], b"foreign owner source\n"):
            with self.subTest(digest=history.sha(payload)):
                with self.assertRaises(ValueError): history.current_source_before_contract667(history.SOURCE, payload)
                path.write_bytes(payload)
                try:
                    with self.assertRaises(ValueError): policy.source_contract(self.root, policy.JS_FOCUS)
                finally:
                    path.write_bytes(current)
        self.assertEqual(approved659, history.peel_contract667_for_history(history.SOURCE, approved659))
        unknown = current + b"\n"
        self.assertEqual(unknown, history.peel_contract667_for_history(history.SOURCE, unknown))
        with self.assertRaises(ValueError): history.source_before_contract667(history.SOURCE, unknown)
        for relative, payload in ((None, current), ([], current), (history.SOURCE, bytearray(current))):
            with self.assertRaises(ValueError): history.current_source_before_contract667(relative, payload)
        unlisted = "scripts/ci/foreign-contract-owner.py"
        self.assertEqual(current, history.peel_contract667_for_history(unlisted, current))
        self.assertNotIn(unlisted, history.contract_input_paths())  # Pass-through is never certification.

    def test_owner_guard_and_contract_manifest_mutation_missing_symlink_or_hardlink_refuse_before_command(self):
        plan = native_plan(self.root, policy.ANDROID_FOCUS)
        document = history._qualified_document()
        for name in (history.SOURCE, history.SOURCE_RELATIVE, history.SPEC_RELATIVE, history.PRIOR_GUARD):
            path = self.root / name; raw = path.read_bytes()
            for mode in ("mutated", "missing", "symlink", "hardlink"):
                backing = path.with_name(path.name + ".contract667-backing")
                with self.subTest(name=name, mode=mode):
                    path.unlink()
                    try:
                        if mode == "mutated": path.write_bytes(raw + b"\n")
                        elif mode == "symlink": path.symlink_to(ROOT / name)
                        elif mode == "hardlink":
                            backing.write_bytes(raw); path.hardlink_to(backing)
                        with self.assertRaises((OSError, ValueError)):
                            native_plan(self.root, policy.ANDROID_FOCUS)
                        with self.assertRaises((OSError, ValueError)):
                            r.gradle_command("android-device", plan, root=self.root, android_serial="emulator-5588")
                        if name == history.SOURCE_RELATIVE:
                            with self.assertRaises((OSError, ValueError)):
                                history._validate_own_guard(self.root, document)
                    finally:
                        if path.exists() or path.is_symlink(): path.unlink()
                        if backing.exists(): backing.unlink()
                        path.write_bytes(raw)
        self.assertEqual(history.current_contract_hashes(), {
            name: history.sha((self.root / name).read_bytes()) for name in history.contract_input_paths()})

    def test_contract_manifest_and_owner_origin_wrong_path_duplicate_boolean_or_changed_pin_refuse(self):
        document = history._qualified_document()
        variants = []
        for key, value in (("schema_version", True), ("scope", "generic owner refresh"),
                           ("predecessor", "foreign"), ("unrelated", True)):
            bad = copy.deepcopy(document); bad[key] = value; variants.append(bad)
        for key, value in (("before_bytes", True), ("after_bytes", 0), ("before_sha256", False),
                           ("fragments", [])):
            bad = copy.deepcopy(document); bad["bindings"][history.SOURCE][key] = value; variants.append(bad)
        bad = copy.deepcopy(document)
        bad["bindings"]["scripts/ci/foreign-contract-owner.py"] = bad["bindings"].pop(history.SOURCE)
        variants.append(bad)
        bad = copy.deepcopy(document); bad["origin_manifests"][history.ORIGINAL_SPEC] = "a" * 64
        variants.append(bad)
        bad = copy.deepcopy(document); bad["own_guard"]["bytes"] = True; variants.append(bad)
        for bad in variants:
            with self.assertRaises(ValueError): history._shape(bad)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            history._json(b'{"scope":"first","scope":"second"}')
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            history._json(b'{"schema_version":NaN}')
        bad = copy.deepcopy(document)
        bad["bindings"][history.SOURCE]["fragments"][0]["after_fragment_sha256"] = "b" * 64
        with patch.object(history, "_qualified_document", return_value=bad):
            with self.assertRaises(ValueError):
                history.source_before_contract667(history.SOURCE, (ROOT / history.SOURCE).read_bytes())
        bad = copy.deepcopy(document)
        bad["bindings"][history.SOURCE]["fragments"][0]["after"] += "\n"
        bad["bindings"][history.SOURCE]["fragments"][0]["after_fragment_sha256"] = history.sha(
            bad["bindings"][history.SOURCE]["fragments"][0]["after"].encode())
        with patch.object(history, "_qualified_document", return_value=bad):
            with self.assertRaises(ValueError):
                history.source_before_contract667(history.SOURCE, (ROOT / history.SOURCE).read_bytes())
        manifest = self.root / history.SPEC_RELATIVE; raw = manifest.read_bytes()
        manifest.write_bytes(raw + b"\n")
        try:
            with patch.object(history, "SPEC_PATH", manifest):
                with self.assertRaises(ValueError): history._document()
        finally:
            manifest.write_bytes(raw)
        for name in history.ORIGIN_MANIFESTS:
            path = self.root / name; raw = path.read_bytes(); path.write_bytes(raw + b"\n")
            try:
                with patch.object(history, "ROOT", self.root):
                    with self.assertRaises(ValueError): history.current_contract_hashes()
            finally:
                path.write_bytes(raw)

    def test_current_command_revalidates_owner_and_companion_inputs_and_rejects_stale_contracts(self):
        for focus in policy.FOCUSES:
            row = policy.spec(focus); plan = native_plan(self.root, focus)
            options = {"root": self.root}
            if focus == policy.ANDROID_FOCUS: options["android_serial"] = "emulator-5588"
            if focus == policy.IOS_FOCUS: options["simulator"] = "11111111-2222-3333-4444-555555555555"
            command = r.gradle_command(row["suite"], plan, **options)
            self.assertEqual(1, command.count(row["task"]))
            for name in history.contract_input_paths():
                path = self.root / name; raw = path.read_bytes(); path.write_bytes(raw + b"\n")
                try:
                    with self.assertRaises(ValueError): r.gradle_command(row["suite"], plan, **options)
                finally:
                    path.write_bytes(raw)
            original, prior = history._sealed_origin_documents()
            for old_digest in (original["added_inputs"][history.SOURCE],
                               prior["bindings"][history.SOURCE]["after_sha256"]):
                stale = copy.deepcopy(plan)
                stale["expected"][0][policy.CONTRACT_FIELD]["source_hashes"][history.SOURCE] = old_digest
                with self.assertRaises(ValueError): r.validate_test_focus(stale)
                with self.assertRaises(ValueError): r.gradle_command(row["suite"], stale, **options)
            for name in (history.SOURCE_RELATIVE, history.SPEC_RELATIVE):
                missing = copy.deepcopy(plan)
                del missing["expected"][0][policy.CONTRACT_FIELD]["source_hashes"][name]
                with self.assertRaises(ValueError): r.validate_test_focus(missing)
                missing = copy.deepcopy(plan); missing["expected"][0]["test_source_files"].remove(name)
                with self.assertRaises(ValueError): r.validate_test_focus(missing)
