# SPDX-License-Identifier: Apache-2.0
"""NEW finite finalCI ingress controls only; no accepted fixture/provider replay."""
import hashlib
from pathlib import Path
import unittest
import ci668_outer_source_projection as ci668
import tooling_recovery671_source_projection as tooling

ROOT = Path(__file__).resolve().parents[2]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

class Ci668OuterIngressTests(unittest.TestCase):
    def test_exact_five_workflow_spans_and_strict_before_refusal(self):
        raw = (ROOT / ci668.WORKFLOW).read_bytes()
        old = ci668.source_before_ci668(ci668.WORKFLOW, raw)
        self.assertEqual(sha(raw), ci668.WORKFLOW_AFTER_SHA256)
        self.assertEqual(sha(old), ci668.WORKFLOW_BEFORE_SHA256)
        self.assertEqual(ci668.source_before_ci668(ci668.WORKFLOW, old), old)
        self.assertEqual(ci668.current_source_before_ci668(ci668.WORKFLOW, raw), old)
        self.assertEqual(tooling.current_source_before_tooling671(ci668.WORKFLOW, raw), old)
        self.assertEqual(tooling.source_before_tooling671(ci668.WORKFLOW, old), old)
        with self.assertRaisesRegex(ValueError, '^An old or unknown image cannot replace exact current final CI668 source$'):
            tooling.current_source_before_tooling671(ci668.WORKFLOW, old)

    def test_seven671_hooks_restore_original_singleton_guard(self):
        raw = (ROOT / ci668.ORIGINAL671_GUARD).read_bytes()
        old = ci668.current_source_before_ci668(ci668.ORIGINAL671_GUARD, raw)
        self.assertEqual(sha(old), ci668.ORIGINAL671_GUARD_SHA256)
        self.assertEqual(len(old), ci668.ORIGINAL671_GUARD_BYTES)
        self.assertEqual(ci668.source_before_ci668(ci668.ORIGINAL671_GUARD, old), old)
        document = tooling._document()
        needle = ('SPEC_SHA256 = "' + tooling.SPEC_SHA256 + '"\n').encode()
        template = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
        self.assertEqual(old.count(needle), 1)
        self.assertEqual(sha(old.replace(needle, template, 1)), document['own_guard']['template_sha256'])
        self.assertEqual(tooling._validate_own_guard(ROOT, document), sha(raw))
        with self.assertRaises(ValueError):
            ci668.current_source_before_ci668(ci668.ORIGINAL671_GUARD, old)

    def test_current_hash_and_path_apis_report_actual175_not_ancestor_hashes(self):
        hashes = ci668.current_input_hashes()
        sealed175 = ci668.sealed_ci668_175_hashes()
        self.assertEqual(len(sealed175), 175)
        self.assertEqual(set(hashes), ci668.fixture_inputs())
        self.assertEqual(hashes, tooling.current_input_hashes())
        self.assertEqual(set(hashes), tooling.fixture_inputs())
        self.assertTrue(all(sha((ROOT / name).read_bytes()) == digest for name, digest in hashes.items()))
        self.assertEqual(hashes[ci668.WORKFLOW], ci668.WORKFLOW_AFTER_SHA256)
        self.assertNotEqual(hashes[ci668.ORIGINAL671_GUARD], ci668.ORIGINAL671_GUARD_SHA256)

    def test_old_partial_drift_nonbytes_and_wrong_identity_refuse_current(self):
        for relative in sorted(ci668.BOUND_PATHS):
            raw = (ROOT / relative).read_bytes()
            old = ci668.source_before_ci668(relative, raw)
            for variant in (old, raw + b'\n', raw[:-1], bytearray(raw), None):
                with self.subTest(relative=relative, variant=type(variant).__name__, length=len(variant) if variant is not None else None):
                    with self.assertRaises(ValueError):
                        ci668.current_source_before_ci668(relative, variant)
                    with self.assertRaises(ValueError):
                        tooling.current_source_before_tooling671(relative, variant)
            with self.assertRaises(ValueError):
                ci668.current_source_before_ci668(Path(relative), raw)
            with self.assertRaises(ValueError):
                ci668.source_before_ci668(relative, raw + b'\n')

    def test_history_peels_exact_endpoints_only_without_current_readmission(self):
        for relative in sorted(ci668.BOUND_PATHS):
            raw = (ROOT / relative).read_bytes()
            old = ci668.source_before_ci668(relative, raw)
            self.assertEqual(ci668.peel_ci668_for_history(relative, raw), old)
            self.assertEqual(ci668.peel_ci668_for_history(relative, old), old)
            self.assertEqual(tooling.peel_tooling671_for_history(relative, raw), old)
            for variant in (raw + b'\n', raw[:-1], b'historical sealed unrelated bytes'):
                self.assertEqual(ci668.peel_ci668_for_history(relative, variant), variant)
                self.assertEqual(tooling.peel_tooling671_for_history(relative, variant), variant)
        raw = b'unlisted payload is not certification'
        self.assertEqual(ci668.source_before_ci668('unlisted.py', raw), raw)
        self.assertEqual(ci668.peel_ci668_for_history('unlisted.py', raw), raw)

    def test_original_manifests_and_seven_leaf_identity_remain_exact(self):
        document = ci668._document()
        original = ci668._original671_inputs()
        self.assertEqual(len(original), 165)
        self.assertEqual(document['unchanged_inputs'], {name: digest for name, digest in original.items() if name not in ci668.BOUND_PATHS})
        self.assertEqual(len(document['unchanged_inputs']), 159)
        self.assertEqual({name: document['added_inputs'][name] for name in ci668.SEALED_CI_LEAVES}, ci668.SEALED_CI_LEAVES)
        self.assertEqual(sha((ROOT / ci668.ORIGINAL671_SPEC).read_bytes()), ci668.ORIGINAL671_SPEC_SHA256)

    def test_qualified_callback_io_ui_current_guards_keep_final_raw_hashes(self):
        import android_io_remote_routing_source_projection as io
        import android_camera_callback_native_focus as callback
        import ios_ui_split664_source_projection as ui
        import webview_current_contract667_source_projection as webview
        expected = ci668.current_input_hashes()
        for module, api in ((io, 'current_input_hashes'), (callback, 'current_contract_hashes'), (ui, 'current_input_hashes'), (webview, 'current_contract_hashes')):
            with self.subTest(module=module.__name__):
                self.assertTrue(module.validate_current_sources(ROOT))
                hashes = getattr(module, api)()
                self.assertEqual({name: hashes[name] for name in expected}, expected)
        raw = (ROOT / ci668.WORKFLOW).read_bytes()
        qualified = tooling.current_source_before_tooling671(ci668.WORKFLOW, raw)
        self.assertEqual(sha(qualified), ci668.WORKFLOW_BEFORE_SHA256)
        io_view = tooling.source_before_callback_composition680(ci668.WORKFLOW, qualified)
        callback_view = tooling.callback_isolated_after_qualified_tooling671(ci668.WORKFLOW, qualified)
        self.assertEqual(sha(io_view), tooling._composition_document()['callback_above_io'][ci668.WORKFLOW]['after_sha256'])
        self.assertEqual(sha(callback_view), tooling._composition_document()['callback_isolated'][ci668.WORKFLOW]['after_sha256'])

    def test_new_ci_guard_template_and_manifest_partial_drift_refuse(self):
        document = ci668._document()
        raw = (ROOT / ci668.SOURCE_RELATIVE).read_bytes()
        self.assertEqual(ci668.current_source_before_ci668(ci668.SOURCE_RELATIVE, raw),
                         ci668.source_before_ci668(ci668.SOURCE_RELATIVE, raw))
        for variant in (raw + b'\n', raw[:-1]):
            with self.assertRaises(ValueError):
                ci668.current_source_before_ci668(ci668.SOURCE_RELATIVE, variant)
        spec = (ROOT / ci668.SPEC_RELATIVE).read_bytes()
        with self.assertRaises(ValueError):
            ci668.current_source_before_ci668(ci668.SPEC_RELATIVE, spec + b'\n')
        self.assertEqual(ci668._validate_own_guard(ROOT, document), sha(raw))
