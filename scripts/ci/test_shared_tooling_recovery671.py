# SPDX-License-Identifier: Apache-2.0
"""NEW6 finite source/fixture regressions, never native or issue acceptance."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CAMERA_BUILD = "calf-camera-picker/build.gradle.kts"
CONTRACTS = "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebViewContracts.kt"
DESKTOP = "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt"
DESKTOP_TEST = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewContentPolicyAcceptanceTest.kt"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def method(relative, name):
    source = (ROOT / relative).read_text()
    matches = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError("One exact owning method required")
    return ast.get_source_segment(source, matches[0])


class SharedToolingRecovery671Controls(unittest.TestCase):
    def test_current_camera_build_is_qualified_before_unchanged_namespace_pins(self):
        import camera_ios_ownership_source_projection as current
        text = method("scripts/ci/android_camera_developer_prerequisite.py", "freeze")
        self.assertIn("current_source_before_camera_ios_ownership", text)
        self.assertLess(text.index("current_source_before_camera_ios_ownership"), text.index("CONVENTION_SHA256"))
        actual = (ROOT / CAMERA_BUILD).read_bytes()
        prior = current.current_source_before_camera_ios_ownership(CAMERA_BUILD, actual)
        self.assertEqual("e37eb7a4fab11a6af0ed0ff6af7dea57e081241d41efb9fa7f1dd06f7367192f", sha(actual))
        self.assertEqual("f074767f7042ac6e07955b361400e672ae43209f99b17986acd27cf5078428c7", sha(prior))
        for payload in (prior, actual + b"\n", actual[:-1], bytearray(actual), None):
            with self.subTest(kind=type(payload).__name__), self.assertRaises(ValueError):
                current.current_source_before_camera_ios_ownership(CAMERA_BUILD, payload)
        self.assertEqual("204b7b0bb30e33144794ffda1d993f925f670cac87c809155d81fe9f09f7a256",
                         sha((ROOT / "convention-plugins/src/main/kotlin/Android.kt").read_bytes()))
        for literal in ("CONVENTION_SHA256", "MODULE_SHA256", "Namespace-generating source changed; no classname package guess"):
            self.assertIn(literal, text)

    def test_recents_current_and_ancestor_ingress_precede_unchanged_tooling_history(self):
        import camera_recents_fixture_source_projection as recents
        current_method = method("scripts/ci/camera_recents_fixture_source_projection.py", "current_source_before_recents_fixture")
        self.assertIn("current_source_before_platform_recovery659", current_method)
        self.assertLess(current_method.index("current_source_before_platform_recovery659"),
                        current_method.index("recents_fixture_after_qualified_outer_ingress"))
        ancestor = method("scripts/ci/camera_recents_fixture_source_projection.py", "source_before_recents_fixture")
        self.assertLess(ancestor.index("peel_platform_recovery659_for_history"),
                        ancestor.index("peel_current_tooling566_for_older_history"))
        nested = method("scripts/ci/camera_recents_fixture_source_projection.py", "recents_fixture_after_qualified_outer_ingress")
        self.assertIn("peel_current_tooling566_for_older_history", nested)
        self.assertNotIn("current_source_before_platform_recovery659", nested)
        caller = method("scripts/ci/camera_recents_source_projection.py", "current_source_before_recents_observation")
        self.assertLess(caller.index("peel_content_policy_for_history"),
                        caller.index("recents_fixture_after_qualified_outer_ingress"))
        self.assertNotIn("current_source_before_recents_fixture", caller)
        relative = "scripts/ci/test_android_external337_fixture_recovery.py"
        actual = (ROOT / relative).read_bytes()
        previous = recents.current_source_before_recents_fixture(relative, actual)
        self.assertEqual(recents._bindings()[relative]["before_sha256"], sha(previous))
        for payload in (previous, actual + b"\n", actual[:-1], bytearray(actual), None):
            with self.subTest(kind=type(payload).__name__), self.assertRaises(ValueError):
                recents.current_source_before_recents_fixture(relative, payload)
        control = method("scripts/ci/test_camera_recents_fixture_recovery.py",
                         "test_current_callers_admit_actual_bytes_before_older_roundtrip_or_message_checks")
        self.assertIn("source_before_platform_recovery659", control)
        for message in ("A historical image cannot replace exact current recents-fixture source", "Unreviewed recents-fixture postimage"):
            self.assertIn(message, (ROOT / "scripts/ci/camera_recents_fixture_source_projection.py").read_text())

    def test_current_webview_sources_restore_exact_legacy_hash_and_literal_operands(self):
        import platform_recovery659_source_projection as current
        controls = (
            ("scripts/ci/test_android_webview_stop_redirect_recovery.py", "test_public_source_keeps_requested_navigation_independent_of_declarative_content"),
            ("scripts/ci/test_desktop_webview_literal_matrix.py", "test_owning_fixture_bounds_cleanup_and_preserved_old_method_and_production_hashes_are_source_pinned"),
            ("scripts/ci/test_desktop_webview_stop_windows_recovery.py", "test_sole_fixture_insertion_accepted_bodies_production_and_evidence_pipeline_are_unchanged"),
            ("scripts/ci/test_ios_webview_current_request_metadata.py", "test_original_common_api_and_all_native_method_bodies_remain_byte_identical"),
            ("scripts/ci/test_webview_content_policy_source.py", "test_owning_common_native_and_accepted_fixture_helper_bytes_remain_unchanged"),
            ("scripts/ci/test_webview_content_policy_source.py", "test_desktop_browser_unsupported_both_entry_points_preserve_current_dom_with_zero_real_requests"),
        )
        for relative, name in controls:
            self.assertIn("source_before_platform_recovery659", method(relative, name), (relative, name))
        for relative, expected in ((CONTRACTS, "4a87aa4a7a17252f817f8bdc9b8de8fcda62fb6093bfed624db0bc5c6875647f"),
                                   (DESKTOP, "598bd8a18431882e68b96a28ff70f65c641bf2a1d36486aeff0aae12b999ae39")):
            actual = (ROOT / relative).read_bytes()
            prior = current.current_source_before_platform_recovery659(relative, actual)
            self.assertEqual(expected, sha(prior))
            for payload in (prior, actual + b"\n", actual[:-1], bytearray(actual), None):
                with self.subTest(relative=relative, kind=type(payload).__name__), self.assertRaises(ValueError):
                    current.current_source_before_platform_recovery659(relative, payload)
        original = current.current_source_before_platform_recovery659(DESKTOP_TEST, (ROOT / DESKTOP_TEST).read_bytes()).decode()
        self.assertIn('listOf("utf-8", "utf8")', original)
        self.assertIn('listOf("utf-8", "utf8", "UTF-8", "UTF8")', (ROOT / DESKTOP_TEST).read_text())

    def test_image_duplicate_site_refusal_model_uses_the_exact_owning_layer_image(self):
        import apple_image_launcher_source_projection as image
        import ios_ui_related_source_projection as ui
        text = method("scripts/ci/test_apple_image_launcher_source_projection.py",
                      "test_fragment_hashes_unique_sites_and_complete_restoration_are_mandatory")
        self.assertIn("ui_history.peel_ui_related_for_history", text)
        self.assertLess(text.index("ui_history.peel_ui_related_for_history"), text.index("copy.deepcopy"))
        actual = (ROOT / image.LAUNCHER).read_bytes()
        owned = ui.peel_ui_related_for_history(image.LAUNCHER, actual)
        binding = image._document()["bindings"][image.LAUNCHER]
        self.assertEqual(binding["after_sha256"], sha(owned))
        fragment = binding["fragments"][0]
        ambiguous = owned.replace(fragment["after"].encode(), b"import json\n", 1)
        self.assertGreater(ambiguous.count(b"import json\n"), 1)
        changed = copy.deepcopy(image._document()); row = changed["bindings"][image.LAUNCHER]
        row["fragments"][0].update(before="import json\n", before_fragment_sha256=sha(b"import json\n"))
        row.update(before_sha256=sha(ambiguous), before_bytes=len(ambiguous))
        from unittest.mock import patch
        with patch.object(image, "_document", return_value=changed), self.assertRaises(ValueError):
            image.source_before_image_launch(image.LAUNCHER, owned)

    def test_image_profile_model_retains_one_bound_sidecar_without_weakening_native_cleanup(self):
        text = method("scripts/ci/test_image_profile_readiness.py",
                      "test_profile_receipt_requires_exact_native_header_file_and_tool_pid_plus_original_cleanup")
        self.assertIn("retain_owned_image_sidecar_model", text)
        import test_image_profile_readiness as owner
        import test_ios_application_receipts as receipts
        import apple_image_sidecar_evidence as sidecar
        fixture = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(fixture.doCleanups); fixture.setUp()
        owner.retain_owned_image_sidecar_model(fixture)
        record = fixture.document["owned_image_launch_readiness"]
        path = fixture.receipt_path.with_name(sidecar.RECORD_NAME)
        self.assertEqual(record, json.loads(path.read_bytes()))
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertEqual(fixture.context["source_revision"], record["source_revision"])
        self.assertEqual(sha(fixture.document["bundle_id"].encode()), record["bundle_identifier_sha256"])
        for key in ("launch_readiness_verified", "root_cause_proven", "native_functionality_verified", "profile_passed"):
            self.assertIs(record[key], False)
        for token in ("observed_launch_pid", "native_readiness_file_sha256", "owned_readiness_removed", "owned_app_stopped_verified"):
            self.assertIn(token, text)

    def test_finite671_source_roundtrip_preserves_original_pins_and_contract_custody(self):
        current = importlib.import_module("tooling_recovery671_source_projection")
        document = current._document()
        self.assertTrue(current.validate_current_sources(ROOT))
        for relative, binding in document["bindings"].items():
            actual = (ROOT / relative).read_bytes()
            prior = current.current_source_before_tooling671(relative, actual)
            self.assertEqual(binding["before_sha256"], sha(prior))
            forward = prior
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(before)); forward = forward.replace(before, after, 1)
            self.assertEqual(actual, forward)
            for payload in (prior, actual + b"\n", actual[:-1], bytearray(actual), None):
                with self.subTest(relative=relative, kind=type(payload).__name__), self.assertRaises(ValueError):
                    current.current_source_before_tooling671(relative, payload)
            def pins(raw):
                source = raw.decode()
                return {ast.get_source_segment(source, node) for node in ast.parse(source).body
                        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                            "SHA256" in target.id for target in node.targets)}
            self.assertEqual(pins(prior), pins(actual), relative)
        import webview_current_contract667_source_projection as prior_guard
        hashes = prior_guard.current_contract_hashes()
        self.assertTrue({current.SOURCE_RELATIVE, current.SPEC_RELATIVE} <= set(hashes))
        self.assertEqual(current.current_input_hashes(), {name: hashes[name] for name in current.current_input_hashes()})
        for name, expected in document["unchanged_inputs"].items():
            raw_current_unchanged = (ROOT / name).read_bytes()
            qualified_unchanged = current.current_source_before_tooling671(name, raw_current_unchanged)
            self.assertEqual(expected, sha(current.source_before_tooling671(name, qualified_unchanged)), name)
        composition = current._composition_document()
        self.assertEqual(7, len(composition["callback_above_io"]))
        self.assertEqual(set(composition["callback_above_io"]), set(composition["callback_isolated"]))
        for relative, row in composition["callback_above_io"].items():
            raw = (ROOT / relative).read_bytes()
            qualified = current.current_source_before_tooling671(relative, raw)
            io_view = current.source_before_callback_composition680(relative, qualified)
            callback_view = current.callback_isolated_after_qualified_tooling671(relative, qualified)
            self.assertEqual(row["after_sha256"], sha(io_view))
            self.assertEqual(composition["callback_isolated"][relative]["after_sha256"], sha(callback_view))
            self.assertEqual(io_view, current.source_before_callback_composition680(relative, io_view))
            self.assertEqual(callback_view, current.callback_isolated_after_qualified_tooling671(relative, callback_view))
            for payload in (raw + b"\n", raw[:-1], bytearray(raw), None):
                with self.subTest(relative=relative, kind=type(payload).__name__), self.assertRaises(ValueError):
                    current.current_source_before_tooling671(relative, payload)
            if io_view != raw:
                with self.assertRaises(ValueError):
                    current.current_source_before_tooling671(relative, io_view)
        import android_io_remote_routing_source_projection as remote_guard
        import android_camera_callback_native_focus as callback_guard
        import ios_ui_split664_source_projection as ui_guard
        self.assertTrue(remote_guard.validate_current_sources(ROOT))
        self.assertTrue(callback_guard.validate_current_sources(ROOT))
        self.assertTrue(ui_guard.validate_current_sources(ROOT))
        self.assertTrue(prior_guard.validate_current_sources(ROOT))
        expected = current.current_input_hashes()
        for hashes in (remote_guard.current_input_hashes(), callback_guard.current_contract_hashes(ROOT),
                       ui_guard.current_input_hashes(), prior_guard.current_contract_hashes()):
            self.assertEqual(expected, {name: hashes[name] for name in expected})
            for name, digest in hashes.items():
                self.assertEqual(digest, sha((ROOT / name).read_bytes()), name)
        contract = callback_guard.source_contract(ROOT)
        self.assertTrue(callback_guard.validate_source_contract(contract))
        self.assertIs(contract["compiler_or_native_success_inferred"], False)
        self.assertEqual(expected, {name: contract["source_inputs"][name] for name in expected})
