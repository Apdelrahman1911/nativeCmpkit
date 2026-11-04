# SPDX-License-Identifier: Apache-2.0
"""NEW source/model composition controls; no accepted control/native replay.

All temporary trees below contain copies of the finite candidate source only;
there are no native runtimes, commands, results, PIDs, XML or Github mutations.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import macos_share_ci668_composition as latest
import ci668_outer_source_projection as ci668
import macos_share_appkit_only_source_projection as appkit
import tooling_recovery671_source_projection as tooling
import cookie_ci668_outer_source_projection as cookie_outer

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@contextmanager
def source_model():
    with tempfile.TemporaryDirectory(prefix="share-ci668-composition-model-") as folder:
        root = Path(folder).resolve()
        for relative in latest.fixture_inputs(ROOT):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)
        yield root


class ShareCi668CompositionTests(unittest.TestCase):
    def test01_actual_raw_union_is231_not_either_predecessor(self):
        # The historical identifier231 is retained; actual joint282 has711 before unchanged707; accepted264 stays historical.
        hashes = latest.current_input_hashes(ROOT)
        self.assertEqual(len(hashes), 282)
        self.assertEqual(set(hashes), latest.fixture_inputs(ROOT))
        self.assertTrue(all(sha((ROOT / name).read_bytes()) == digest for name, digest in hashes.items()))
        self.assertEqual(hashes[latest.WORKFLOW], "7c9af733acf8ac35aad36012870a9ba2895a36646d04743dbf709b911d6d1566")
        self.assertEqual(hashes[latest.LIBRARY], "038ffa83f883f24396b35103edafa47a9b4a13fe4df6faf88175e56768819299")
        self.assertEqual(len(latest.predecessor_input_hashes(latest.CI_VIEW)), 175)
        self.assertEqual(len(latest.predecessor_input_hashes(latest.COOKIE_VIEW)), 40)
        self.assertEqual(len(latest.predecessor_input_hashes(latest.SHARE_VIEW)), 36)
        self.assertNotEqual(hashes[latest.LIBRARY], latest.predecessor_input_hashes(latest.CI_VIEW)[latest.LIBRARY])
        self.assertNotEqual(hashes[latest.WORKFLOW], latest.predecessor_input_hashes(latest.SHARE_VIEW)[latest.WORKFLOW])

    def test02_two_named_views_have_exact_inverse_forward_custody(self):
        # The old identifier is historical; only four explicitly named views exist; accepted264 had three.
        document = latest._document(ROOT)
        self.assertEqual(set(document["views"]), {"final_ci175", "cookie609_raw40", "share607", "producer676_raw190"})
        self.assertEqual({name: len(rows) for name, rows in document["views"].items()},
                         {"final_ci175": 7, "cookie609_raw40": 4, "share607": 3, "producer676_raw190": 8})
        for view, rows in document["views"].items():
            for relative, row in rows.items():
                raw = (ROOT / relative).read_bytes()
                ancestor = latest.current_source_in_view(relative, raw, view, ROOT)
                self.assertEqual((sha(ancestor), len(ancestor)), (row["after_sha256"], row["after_bytes"]))
                forward = ancestor
                for fragment in reversed(row["fragments"]):
                    self.assertEqual(forward.count(fragment["after"].encode()), 1)
                    forward = forward.replace(fragment["after"].encode(), fragment["before"].encode(), 1)
                if relative in latest.BUDGET707_FRAGMENT_COUNTS:
                    for fragment in document["derivative_bindings"][relative]["fragments"]:
                        self.assertEqual(forward.count(fragment["before"].encode()), 1)
                        forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
                if relative == latest.OFFLINE:
                    for fragment in document["failure711_bindings"][relative]["fragments"]:
                        self.assertEqual(forward.count(fragment["before"].encode()), 1)
                        forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
                self.assertEqual(forward, raw)
        library = (ROOT / latest.LIBRARY).read_bytes()
        workflow = (ROOT / latest.WORKFLOW).read_bytes()
        self.assertEqual(latest.current_source_in_view(latest.LIBRARY, library, latest.SHARE_VIEW), library)
        self.assertEqual(sha(latest.current_source_in_view(latest.WORKFLOW, workflow, latest.CI_VIEW)),
                         "47878318993f0ca28899f782b1ba8780fe1c6e210e187ef097acfaa4fb1d19f8")

    def test03_guard_and_owning_fixture_descendants_restore_distinct_ancestors(self):
        document = latest._document(ROOT)
        self.assertEqual(set(document["derivative_bindings"]), set(latest.BOUND_FRAGMENT_COUNTS))
        self.assertEqual(sum(len(row["fragments"]) for name, row in document["derivative_bindings"].items()
                             if name in latest.HISTORICAL_DERIVATIVE_FRAGMENT_COUNTS), 39)
        self.assertEqual(sum(len(document["derivative_bindings"][name]["fragments"])
                             for name in latest.BUDGET707_FRAGMENT_COUNTS), 6)
        for relative, row in document["derivative_bindings"].items():
            raw = (ROOT / relative).read_bytes()
            if relative == latest.OFFLINE:
                raw = latest._failure711_to_budget707(raw, document)
            self.assertEqual((sha(raw), len(raw)), (row["after_sha256"], row["after_bytes"]))
            restored = raw
            for fragment in reversed(row["fragments"]):
                self.assertEqual(restored.count(fragment["after"].encode()), 1)
                restored = restored.replace(fragment["after"].encode(), fragment["before"].encode(), 1)
            self.assertEqual((sha(restored), len(restored)), (row["before_sha256"], row["before_bytes"]))
        self.assertEqual(sha(latest.current_source_in_view(latest.CI_OWNER, (ROOT / latest.CI_OWNER).read_bytes(), latest.CI_VIEW)), latest.CI_OWNER_ANCESTOR_SHA256)
        self.assertEqual(sha(latest.current_source_in_view(latest.SHARE_OWNER, (ROOT / latest.SHARE_OWNER).read_bytes(), latest.SHARE_VIEW)), latest.SHARE_OWNER_ANCESTOR_SHA256)

    def test04_every_declared_ancestor_refuses_strict_current_admission(self):
        document = latest._document(ROOT)
        for view, rows in document["views"].items():
            for relative in rows:
                ancestor = latest.current_source_in_view(relative, (ROOT / relative).read_bytes(), view)
                with self.subTest(view=view, path=relative), self.assertRaises(ValueError):
                    latest.current_source_in_view(relative, ancestor, view)
                with self.assertRaises(ValueError):
                    ci668.current_source_before_ci668(relative, ancestor)
                with self.assertRaises(ValueError):
                    appkit.current_source_before_appkit_only(relative, ancestor, ROOT)

    def test05_current_partial_tail_type_alias_and_unknown_identity_refuse(self):
        relative = latest.LIBRARY
        raw = (ROOT / relative).read_bytes()
        for payload in (raw[:-1], raw + b"\n# outside reviewed spans\n", bytearray(raw), None, b""):
            with self.subTest(kind=type(payload).__name__), self.assertRaises(ValueError):
                latest.current_source_in_view(relative, payload, latest.CI_VIEW)
        for name in (Path(relative), "unlisted-current-input.py", "../library_tests.py", "scripts//ci/library_tests.py", "scripts\\ci\\library_tests.py"):
            with self.subTest(identity=str(name)), self.assertRaises(ValueError):
                latest.current_source_in_view(name, raw, latest.CI_VIEW)

    def test06_history_peels_only_exact_named_descendants_not_unknown_or_other_view(self):
        sealed_comparisons = {latest.NEW_COOKIE_CONTROL, latest.OWNING_COOKIE_CONTROL, latest.CALLBACK_INIT}
        for view, rows in latest._document(ROOT)["views"].items():
            for relative in rows:
                raw = (ROOT / relative).read_bytes()
                ancestor = latest.current_source_in_view(relative, raw, view)
                expected = raw if relative in sealed_comparisons else ancestor
                self.assertEqual(latest.peel_for_history(relative, raw, view), expected)
                self.assertEqual(latest.peel_for_history(relative, ancestor, view), ancestor)
                for payload in (raw[:-1], raw + b"\n", b"unrelated historical bytes"):
                    self.assertEqual(latest.peel_for_history(relative, payload, view), payload)
            for relative in sealed_comparisons:
                raw = (ROOT / relative).read_bytes()
                self.assertEqual(latest.peel_for_history(relative, raw, view), raw)
        unknown = b"pass-through is not certification"
        self.assertEqual(latest.peel_for_history("unlisted-source.py", unknown, latest.CI_VIEW), unknown)
        library = (ROOT / latest.LIBRARY).read_bytes()
        self.assertEqual(latest.peel_for_history(latest.LIBRARY, library, latest.SHARE_VIEW), library)

    def test07_no_generic_layer_or_third_view_is_accepted(self):
        raw = (ROOT / latest.LIBRARY).read_bytes()
        for view in (None, False, "latest", "CI", "share609", "callback_above_io"):
            with self.subTest(view=view), self.assertRaises(ValueError):
                latest.current_source_in_view(latest.LIBRARY, raw, view)
            with self.assertRaises(ValueError):
                latest.peel_for_history(latest.LIBRARY, raw, view)
            with self.assertRaises(ValueError):
                latest.predecessor_input_hashes(view)

    def test08_all_old_source_manifests_remain_exact_and_named(self):
        expected = {
            latest.CI_SPEC: latest.CI_SPEC_SHA256,
            latest.SHARE_SPEC: latest.SHARE_SPEC_SHA256,
            latest.OBSERVATION_SPEC: latest.OBSERVATION_SPEC_SHA256,
            "scripts/ci/fixtures/tooling-recovery671-source-inverse.json": "9def6c416e199237600bdcdc2a16a3fd22dc2158796e1116f999b8681c96a110",
            "scripts/ci/fixtures/tooling-recovery671-composed-routing680.json": "b853b524177cfa51c175f9c3bc7d3cd301c5db0aec7e335f6739fdca07332871",
        }
        self.assertTrue(expected.keys() <= latest.fixture_inputs(ROOT))
        for relative, digest in expected.items():
            self.assertEqual(sha((ROOT / relative).read_bytes()), digest)
        document = latest._document(ROOT)
        self.assertFalse(document["predecessor_custody"]["native_cause_verified"])
        self.assertFalse(document["predecessor_custody"]["JNI_execution_revived"])

    def test09_whole_current_validation_rejects_guard_library_and_unrelated_tail(self):
        for relative in (latest.CI_OWNER, latest.SHARE_OWNER, latest.LIBRARY,
                         "calf-share/native/tests/appkit_lifecycle/cases.rs"):
            with source_model() as root:
                target = root / relative
                target.write_bytes(target.read_bytes() + b"\n# unknown complete-source tail\n")
                with self.subTest(path=relative), self.assertRaises(ValueError):
                    latest.validate_current_sources(root)

    def test10_new_manifest_drift_duplicate_fields_and_depth_refuse(self):
        with source_model() as root:
            target = root / latest.SPEC
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "exact-share-CI-latest-manifest-required"):
                latest.validate_current_sources(root)
        for payload in (b'{"x":1,"x":2}', b'{"x":NaN}', b"[" * 66 + b"0" + b"]" * 66):
            with self.subTest(payload_kind=payload[:12]), self.assertRaises(ValueError):
                latest._json(payload)

    def test11_new_own_guard_template_cannot_be_replaced_by_old_or_tailed_bytes(self):
        document = latest._document(ROOT)
        raw = (ROOT / latest.OWNER).read_bytes()
        self.assertEqual(latest._own_payload(raw, document), sha(raw))
        for payload in (raw[:-1], raw + b"\n", (ROOT / latest.CI_OWNER).read_bytes(),
                        raw.replace(latest.SPEC_SHA256.encode(), b"0" * 64, 1)):
            with self.assertRaises(ValueError):
                latest._own_payload(payload, document)

    def test12_inverse_duplicate_fragments_and_full_tail_checks_are_mandatory(self):
        row = copy.deepcopy(latest._document(ROOT)["views"][latest.CI_VIEW][latest.LIBRARY])
        raw = (ROOT / latest.LIBRARY).read_bytes()
        with self.assertRaises(ValueError):
            latest._inverse_to_ancestor(raw + b"\n# tail\n", row)
        bad_hash = copy.deepcopy(row)
        bad_hash["fragments"][0]["before_fragment_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "complete-share-CI-fragment-hashes-required"):
            latest._inverse_to_ancestor(raw, bad_hash)
        duplicate = raw + row["fragments"][0]["before"].encode()
        row["before_sha256"], row["before_bytes"] = sha(duplicate), len(duplicate)
        with self.assertRaisesRegex(ValueError, "unique-share-CI-view-inverse-fragment-required"):
            latest._inverse_to_ancestor(duplicate, row)

    def test13_CI_current_and_history_precede_unchanged671_680_library_views(self):
        raw = (ROOT / latest.LIBRARY).read_bytes()
        ci = latest.current_source_in_view(latest.LIBRARY, raw, latest.CI_VIEW)
        self.assertEqual(sha(ci), "ddd7b38615bef7ec99bfefddb625bf0816d9c90c297604d7baaea898a6e90aa6")
        self.assertEqual(ci668.current_source_before_ci668(latest.LIBRARY, raw), ci)
        self.assertEqual(ci668.source_before_ci668(latest.LIBRARY, raw), ci)
        self.assertEqual(ci668.peel_ci668_for_history(latest.LIBRARY, raw), ci)
        self.assertEqual(tooling.current_source_before_tooling671(latest.LIBRARY, raw), ci)
        self.assertEqual(tooling.source_before_tooling671(latest.LIBRARY, raw), ci)
        self.assertEqual(tooling.peel_tooling671_for_history(latest.LIBRARY, raw), ci)
        self.assertEqual(sha(tooling.source_before_callback_composition680(latest.LIBRARY, ci)), "50649230981349294a9aac3dd51b14d629d3596818c2a527d95ea2cf2c48c80d")
        self.assertEqual(sha(tooling.callback_isolated_after_qualified_tooling671(latest.LIBRARY, ci)), "f106cf3fe4ed33a5ec5e681b080b0732d9310727878a03bcefc649e22fe0b183")
        self.assertEqual(sha((ROOT / tooling.SOURCE_RELATIVE).read_bytes()), "311353d09543805a3e2f9f4b9744a45ad73d59ef7812fd47fb1d5d27857f592d")

    def test14_dependent_current_hash_path_and_owner_APIs_return_actual_latest_union(self):
        hashes = latest.current_input_hashes(ROOT)
        self.assertEqual(ci668.current_input_hashes(), hashes)
        self.assertEqual(tooling.current_input_hashes(), hashes)
        self.assertEqual(appkit.validate_current_sources(ROOT), hashes)
        self.assertEqual(ci668.fixture_inputs(), set(hashes))
        self.assertEqual(tooling.fixture_inputs(), set(hashes))
        self.assertEqual(appkit.fixture_inputs(ROOT), set(hashes))
        self.assertEqual(ci668._validate_own_guard(ROOT, ci668._document()), hashes[ci668.SOURCE_RELATIVE])
        self.assertEqual(tooling._validate_own_guard(ROOT, tooling._document()), hashes[tooling.SOURCE_RELATIVE])

    def test15_separate609_owner_and_lifecycle_restore_after_one_Share_view(self):
        import macos_share_key_wait_observation as observation
        lifecycle = "scripts/ci/macos_share_appkit_lifecycle.py"
        raw = (ROOT / lifecycle).read_bytes()
        self.assertEqual(sha(raw), "6c9deafdb60a1103d16425446a10073fec2abde53f3381a7987041b87cf9c6be")
        self.assertEqual(observation.OWNER_SHA256, "da9f07cf9cebf56133186d6310850325b29dd70cfc94d98153bfc49ea9ad988a")
        self.assertEqual(sha(observation.current_source_before_key_wait(lifecycle, raw)), "b04a67a0a8b80e6d335ee6408e6149db0f3616f353b38b984b6cf39406415455")
        self.assertTrue(observation.validate_current_sources(ROOT))
        self.assertEqual(observation.fixture_inputs(), latest.fixture_inputs(ROOT))

    def test16_passive_route_selects_six_only_and_original_native_readiness_remains(self):
        import macos_share_appkit_only_route as route
        with patch("subprocess.run", side_effect=AssertionError("ZERO new native commands")), \
             patch("subprocess.Popen", side_effect=AssertionError("ZERO new native processes")):
            value = route.plan(ROOT)
        self.assertEqual([row["name"] for row in value["expected"][0]["required_testcases"]], [
            "missing_content_view", "real_picker_cancel", "controlled_picker_dismissal",
            "controlled_success_duplicate_late", "controlled_service_failure", "bounded_concurrent_requests"])
        self.assertEqual(value["Gradle_tasks"], [])
        self.assertEqual(value["JNI_tests_executed_here"], 0)
        self.assertFalse(value["native_cause_verified"])
        self.assertFalse(value["release_ready"])
        cases = (ROOT / "calf-share/native/tests/appkit_lifecycle/cases.rs").read_bytes()
        self.assertEqual(sha(cases), "2ee076e833b1cdc619a5aa94194d5d23e3b62d2da1a9797ebe37ac377361b790")
        self.assertIn(b'pump_until("Owned AppKit window did not become key", || {', cases)
        self.assertIn(b'let deadline = Instant::now() + Duration::from_secs(10);', cases)
        self.assertIn(b'assert!(Instant::now() < deadline, "{reason}");', cases)

    def test17_retired_nine_input_reader_is_not_a_composed_current_certificate(self):
        import macos_share_missing_ci as historical
        self.assertEqual(len(historical.SOURCE_SHA256), 9)
        self.assertEqual(historical.SOURCE_SHA256["scripts/ci/macos_share_appkit_lifecycle.py"], "b04a67a0a8b80e6d335ee6408e6149db0f3616f353b38b984b6cf39406415455")
        self.assertEqual(historical.SOURCE_SHA256["calf-share/native/tests/appkit_lifecycle/cases.rs"], "9e038b83b4e2e4d3d4718869ec05c9eaa198ce1f3c886a38b97b7c13ff83842b")
        self.assertEqual(historical.SOURCE_SHA256["scripts/ci/fresh-tests.init.gradle.kts"], "bc14e3ac5105e6a337c896f4f7e88dd565e8862b2b2dc0d8ff055f40ab8cb9d4")
        with self.assertRaisesRegex(ValueError, "The unchanged Share630 recovery input differs: scripts/ci/macos_share_appkit_lifecycle.py"):
            historical.source_contract(ROOT, [historical.SOURCE])
        source = (ROOT / latest.LIBRARY).read_text()
        tree = ast.parse(source)
        plan = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "plan")
        run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        self.assertIn("share_missing.source_contract", ast.get_source_segment(source, plan))
        self.assertIn("AppKit6-only CLI reference", ast.get_source_segment(source, run))
        self.assertIn("main_for_existing_profile", ast.get_source_segment(source, main))
        # Inspect current source; do not execute retired plan/run, JNI, or restored code.

    def test18_fixture_ancestor_metadata_is_not_relabelled_current_source(self):
        document = latest._document(ROOT)
        ci_control = "scripts/ci/test_ci668_outer_source_projection.py"
        share_control = "scripts/ci/test_macos_share_appkit_only_route607.py"
        for relative, view, digest in (
            (ci_control, latest.CI_VIEW, "8e6d2e76f9de755f5d53bdc6a5a29aeb7161e9777ffcf7b5a0a163164889dfce"),
            (share_control, latest.SHARE_VIEW, "d1e4624ca07d5fa6af3bb892f41c628e9b9d12a5951ba02f2023bbd784af8734"),
        ):
            raw = (ROOT / relative).read_bytes()
            ancestor = latest.current_source_in_view(relative, raw, view)
            self.assertEqual(sha(ancestor), digest)
            self.assertNotEqual(sha(raw), digest)
            self.assertEqual(document["raw_inputs"][relative]["sha256"], sha(raw))
            self.assertEqual(document["predecessor_inputs"][view][relative]["sha256"], digest)
        ci_body = (ROOT / ci_control).read_text()
        self.assertIn("len(latest.predecessor_input_hashes(latest.CI_VIEW)), 175", ci_body)
        self.assertIn("self.assertEqual(hashes, latest.current_input_hashes())", ci_body)

    def test19_new_current_ingress_rejects_manifest_hardlink_and_parent_alias(self):
        with source_model() as root:
            target = root / latest.SPEC
            (target.parent / "duplicate-manifest.json").hardlink_to(target)
            with self.assertRaises(ValueError):
                latest.validate_current_sources(root)
        with source_model() as root:
            scripts = root / "scripts"
            renamed = root / "actual-scripts"
            scripts.rename(renamed)
            scripts.symlink_to(renamed, target_is_directory=True)
            with self.assertRaises(ValueError):
                latest.validate_current_sources(root)

    def test20_new_guard_has_no_native_workflow_or_restored_code_execution(self):
        text = (ROOT / latest.OWNER).read_text()
        tree = ast.parse(text)
        forbidden = {"subprocess", "socket", "urllib", "requests", "importlib", "marshal"}
        imports = {alias.name.split(".")[0] for node in ast.walk(tree)
                   if isinstance(node, (ast.Import, ast.ImportFrom))
                   for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module or "")])}
        self.assertFalse(imports & forbidden)
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertFalse(calls & {"exec", "eval", "compile", "__import__"})
        custody = latest._document(ROOT)["predecessor_custody"]
        self.assertEqual(custody["separate609_packet_sha256"], "7a1d599ee6b1d79e215fb2dea1d1802bcd49ac2373e870be908517c5248133b3")
        self.assertTrue(custody["original_missing_terminal_receipt_retained"])
        self.assertTrue(custody["original_uncaptured_console_retained"])
        self.assertFalse(custody["JNI_execution_revived"])


    def test21_no_POSIX_primitives_route_qualifies_actual_current_source_map(self):
        # A controlled source feature route, NOT an executed Windows/native host.
        with patch.object(latest, "_descriptor_source_io_supported", return_value=False):
            hashes = latest.current_input_hashes(ROOT)
        self.assertEqual(len(hashes), 282)
        self.assertTrue(all(sha((ROOT / name).read_bytes()) == digest for name, digest in hashes.items()))
        self.assertEqual(hashes[latest.LIBRARY], "038ffa83f883f24396b35103edafa47a9b4a13fe4df6faf88175e56768819299")
        self.assertEqual(hashes[latest.WORKFLOW], "7c9af733acf8ac35aad36012870a9ba2895a36646d04743dbf709b911d6d1566")

    def test22_portable_route_retains_tail_hardlink_parent_and_read_bounds_refusals(self):
        for mutation in ("tail", "hardlink", "parent-alias"):
            with source_model() as root:
                if mutation == "tail":
                    file = root / latest.LIBRARY
                    file.write_bytes(file.read_bytes() + b"\n# unknown tail\n")
                elif mutation == "hardlink":
                    file = root / latest.SPEC
                    (file.parent / "duplicate-source.json").hardlink_to(file)
                else:
                    scripts = root / "scripts"
                    actual = root / "actual-scripts"
                    scripts.rename(actual)
                    scripts.symlink_to(actual, target_is_directory=True)
                with patch.object(latest, "_descriptor_source_io_supported", return_value=False), \
                     self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    latest.validate_current_sources(root)
        with patch.object(latest, "_descriptor_source_io_supported", return_value=False):
            for maximum in (True, 0, 1, latest.MAX_SOURCE + 1):
                with self.subTest(maximum=maximum), self.assertRaises(ValueError):
                    latest._ordinary(ROOT, latest.LIBRARY, maximum)

    def test23_feature_probe_and_portable_success_close_only_owned_file_descriptor(self):
        with patch.object(latest.os, "supports_dir_fd", set()):
            self.assertFalse(latest._descriptor_source_io_supported())
        close = os.close
        with patch.object(latest, "_descriptor_source_io_supported", return_value=False), \
             patch.object(latest.os, "close", wraps=close) as closing:
            raw, identity = latest._ordinary(ROOT, latest.LIBRARY)
        closing.assert_called_once()
        self.assertEqual(raw, (ROOT / latest.LIBRARY).read_bytes())
        self.assertEqual(identity["sha256"], sha(raw))
        self.assertEqual(identity["size"], len(raw))

    def test24_portable_open_replacement_refuses_before_foreign_read_and_closes_owned_FD(self):
        with source_model() as root:
            foreign = root / "foreign-model-source.bin"
            foreign.write_bytes(b"synthetic foreign fixture bytes must not be read")
            descriptor = os.open(foreign, os.O_RDONLY | getattr(os, "O_BINARY", 0))
            with patch.object(latest.os, "open", return_value=descriptor), \
                 patch.object(latest.os, "read", side_effect=AssertionError("no foreign descriptor read")) as reading, \
                 self.assertRaisesRegex(ValueError, "share-CI-source-file-replaced-before-read"):
                latest._portable_ordinary(root, latest.LIBRARY, latest.MAX_SOURCE)
            reading.assert_not_called()
            with self.assertRaises(OSError):
                os.fstat(descriptor)



class CookieShareCi668JointSuccessor607Tests(unittest.TestCase):
    def test25_library_payload_and_guard_views_have_distinct_exact_ancestry(self):
        raw = (ROOT / latest.LIBRARY).read_bytes()
        cookie_document, _ = cookie_outer._document(ROOT)
        self.assertNotIn(latest.LIBRARY, cookie_document["bindings"])
        self.assertNotIn(latest.LIBRARY, cookie_outer.current_input_hashes(ROOT))
        ancestor = cookie_outer.current_source_before_cookie_outer(latest.LIBRARY, raw, ROOT)
        self.assertEqual(sha(ancestor), "ddd7b38615bef7ec99bfefddb625bf0816d9c90c297604d7baaea898a6e90aa6")
        self.assertEqual(latest.current_source_in_view(latest.LIBRARY, raw, latest.CI_VIEW), ancestor)
        self.assertEqual(latest.current_source_in_view(latest.LIBRARY, raw, latest.SHARE_VIEW), raw)
        # NEW dual-raw ingress: the Cookie inverse is never re-admitted by joint.
        self.assertEqual(ci668.current_source_before_ci668(latest.LIBRARY, raw), ancestor)
        self.assertEqual(ci668.source_before_ci668(latest.LIBRARY, raw), ancestor)
        self.assertEqual(ci668.peel_ci668_for_history(latest.LIBRARY, raw), ancestor)
        fixture = "scripts/ci/test_ci668_outer_source_projection.py"
        fixture_raw = (ROOT / fixture).read_bytes()
        fixture_old = latest.current_source_in_view(fixture, fixture_raw, latest.CI_VIEW)
        self.assertEqual(sha(fixture_old), "8e6d2e76f9de755f5d53bdc6a5a29aeb7161e9777ffcf7b5a0a163164889dfce")
        self.assertEqual(ci668.current_source_before_ci668(fixture, fixture_raw), fixture_old)
        self.assertEqual(ci668.source_before_ci668(fixture, fixture_raw), fixture_old)
        self.assertEqual(ci668.peel_ci668_for_history(fixture, fixture_raw), fixture_old)
        with self.assertRaises(ValueError):
            ci668.current_source_before_ci668(fixture, fixture_old)
        guard = (ROOT / latest.CI_OWNER).read_bytes()
        self.assertEqual(sha(latest.current_source_in_view(latest.CI_OWNER, guard, latest.CI_VIEW)), latest.CI_OWNER_ANCESTOR_SHA256)
        self.assertEqual(sha(latest.current_source_in_view(latest.CI_OWNER, guard, latest.COOKIE_VIEW)), latest.COOKIE_CI_OWNER_SHA256)
        self.assertEqual(sha(cookie_outer.current_source_before_cookie_outer(latest.CI_OWNER, guard, ROOT)), latest.CI_OWNER_ANCESTOR_SHA256)
        for payload in (ancestor, raw[:-1], raw + b"\n"):
            with self.assertRaises(ValueError):
                cookie_outer.current_source_before_cookie_outer(latest.LIBRARY, payload, ROOT)

    def test26_noncurrent_Share_CI_sibling_is_data_not_admission_or_history(self):
        document = latest._document(ROOT)
        row = document["noncurrent_sibling_bindings"][latest.CI_OWNER]
        encoded = (json.dumps(row, indent=2, sort_keys=True) + "\n").encode()
        self.assertEqual(sha(encoded), latest.NONCURRENT_SIBLING_BINDING_SHA256)
        raw = (ROOT / latest.CI_OWNER).read_bytes()
        sibling = latest.current_source_in_view(latest.CI_OWNER, raw, latest.CI_VIEW)
        for fragment in row["fragments"]:
            self.assertEqual(sibling.count(fragment["before"].encode()), 1)
            sibling = sibling.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
        self.assertEqual((sha(sibling), len(sibling)), (row["after_sha256"], row["after_bytes"]))
        self.assertNotEqual(sibling, raw)
        for view in latest.VIEWS:
            with self.assertRaises(ValueError):
                latest.current_source_in_view(latest.CI_OWNER, sibling, view)
            self.assertEqual(latest.peel_for_history(latest.CI_OWNER, sibling, view), sibling)
        with self.assertRaises(ValueError):
            cookie_outer.current_source_before_cookie_outer(latest.CI_OWNER, sibling, ROOT)
        with self.assertRaises(ValueError):
            ci668.current_source_before_ci668(latest.CI_OWNER, sibling)

    def test27_actual_Cookie40_and_CI264_are_separate_current_certificates(self):
        cookie40 = cookie_outer.current_input_hashes(ROOT)
        joint264 = latest.current_input_hashes(ROOT)
        self.assertEqual((len(cookie40), len(joint264)), (40, 282))  # Identifier264 is historical, never new-map custody.
        self.assertEqual({name: joint264[name] for name in cookie40}, cookie40)
        self.assertEqual(ci668.current_input_hashes(), joint264)
        self.assertEqual(ci668.fixture_inputs(), set(joint264))
        self.assertEqual(cookie_outer.fixture_inputs(), set(cookie40))
        self.assertTrue(all(sha((ROOT / name).read_bytes()) == digest for name, digest in joint264.items()))
        self.assertTrue({latest.LIBRARY, latest.SHARE_OWNER, latest.OWNER, latest.SPEC}.isdisjoint(cookie40))
        old40 = latest.predecessor_input_hashes(latest.COOKIE_VIEW)
        self.assertEqual(len(old40), 40)
        self.assertEqual(set(old40), set(cookie40))
        changed = {name for name in old40 if old40[name] != cookie40[name]}
        self.assertEqual(changed, {latest.CI_OWNER, latest.COOKIE_OWNER, latest.COOKIE_SPEC, latest.NEW_COOKIE_CONTROL})

    def test28_original_Cookie_four_ten_fragments_remain_literal_source_only(self):
        current, _ = cookie_outer._document(ROOT)
        original = json.loads((ROOT / cookie_outer.COOKIE_SPEC).read_bytes())
        self.assertEqual(set(original["bindings"]), set(cookie_outer.COOKIE_BOUND_PATHS))
        self.assertEqual(sum(len(row["fragments"]) for row in original["bindings"].values()), 10)
        for relative, row in original["bindings"].items():
            self.assertEqual(current["bindings"][relative], row)
            raw = (ROOT / relative).read_bytes()
            restored = cookie_outer.current_source_before_cookie_outer(relative, raw, ROOT)
            self.assertEqual((sha(restored), len(restored)), (row["before_sha256"], row["before_bytes"]))
            forward = restored
            for fragment in row["fragments"]:
                self.assertEqual(forward.count(fragment["before"].encode()), 1)
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(forward, raw)
        # Literal current source arithmetic only: no Cookie engine/native body ran.

    def test29_control_init_explicit_comparisons_never_become_generic_history(self):
        for relative in (latest.NEW_COOKIE_CONTROL, latest.OWNING_COOKIE_CONTROL, latest.CALLBACK_INIT):
            raw = (ROOT / relative).read_bytes()
            self.assertEqual(cookie_outer.peel_cookie_outer_for_history(relative, raw, ROOT), raw)
            for view in latest.VIEWS:
                self.assertEqual(latest.peel_for_history(relative, raw, view), raw)
        control = (ROOT / latest.OWNING_COOKIE_CONTROL).read_bytes()
        original = cookie_outer.cookie681_control_for_old_cookie_comparison(latest.OWNING_COOKIE_CONTROL, control, ROOT)
        self.assertEqual(sha(original), cookie_outer.OWNING_CONTROL_BEFORE_SHA256)
        self.assertNotEqual(original, control)
        init = (ROOT / latest.CALLBACK_INIT).read_bytes()
        old_init = cookie_outer.callback672_init_for_old_cookie_comparison(latest.CALLBACK_INIT, init, ROOT)
        self.assertEqual(sha(old_init), cookie_outer.INIT_OLD_COOKIE_SHA256)
        self.assertEqual(sha(init), cookie_outer.INIT_CURRENT_SHA256)
        with self.assertRaises(ValueError):
            cookie_outer.cookie681_control_for_old_cookie_comparison(latest.OWNING_COOKIE_CONTROL, original, ROOT)
        with self.assertRaises(ValueError):
            cookie_outer.callback672_init_for_old_cookie_comparison(latest.CALLBACK_INIT, old_init, ROOT)
        with self.assertRaises(ValueError):
            latest.current_source_in_view(latest.OWNING_COOKIE_CONTROL, original, latest.COOKIE_VIEW)

    def test30_copied_Cookie40_remains_self_contained_but_not_a_joint264_certificate(self):
        actual = cookie_outer.current_input_hashes(ROOT)
        with tempfile.TemporaryDirectory(prefix="cookie40-joint-source-model-") as folder:
            root = Path(folder).resolve()
            for relative in actual:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            self.assertFalse((root / latest.LIBRARY).exists())
            self.assertFalse((root / latest.OWNER).exists())
            self.assertEqual(cookie_outer.current_input_hashes(root), actual)
            text = (root / latest.NEW_COOKIE_CONTROL).read_text()
            tree = ast.parse(text)
            model = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_raw_expectations")
            body = ast.get_source_segment(text, model)
            self.assertIn('outer.OWNING_CONTROL_RELATIVE: document["cookie681_control_binding"]["after_sha256"]', body)
            current_control = actual[latest.OWNING_COOKIE_CONTROL]
            document, _ = cookie_outer._document(root)
            self.assertEqual(current_control, document["cookie681_control_binding"]["after_sha256"])
            self.assertNotEqual(current_control, document["accepted_cookie_inputs"][latest.OWNING_COOKIE_CONTROL])
        for relative in (latest.LIBRARY, latest.SHARE_OWNER):
            with source_model() as root:
                target = root / relative
                target.write_bytes(target.read_bytes() + b"\n# unqualified joint-only drift\n")
                self.assertEqual(cookie_outer.current_input_hashes(root), actual)
                with self.assertRaises(ValueError):
                    latest.validate_current_sources(root)

    def test31_old_snapshot_sibling_future_flags_and_three_view_shape_are_sealed(self):
        document = latest._document(ROOT)
        cases = []
        fourth = copy.deepcopy(document)
        fourth["views"]["noncurrent_share_CI_sibling"] = {}
        cases.append(fourth)
        old = copy.deepcopy(document)
        old["named_cookie609_manifest"]["scope"] += " unknown ancestor tail"
        cases.append(old)
        sibling = copy.deepcopy(document)
        sibling["noncurrent_sibling_bindings"][latest.CI_OWNER]["after_sha256"] = "0" * 64
        cases.append(sibling)
        future = copy.deepcopy(document)
        future["predecessor_custody"]["future_diagnostics_endpoints_adopted"] = False
        cases.append(future)
        for changed in cases:
            with self.assertRaises(ValueError):
                latest._shape(changed, ROOT)
        custody = document["predecessor_custody"]
        self.assertTrue(custody["original_missing_terminal_receipt_retained"])
        self.assertTrue(custody["original_uncaptured_console_retained"])
        self.assertFalse(custody["native_cause_verified"])
        self.assertFalse(custody["JNI_execution_revived"])
        self.assertTrue(custody["future_diagnostics_endpoints_adopted"])
        self.assertFalse(custody["joint279_source_proposal_adopted"])
        self.assertFalse(custody["producer_or_reuse_runtime_accepted"])


class CookieShareProducerSourceSuccessor2eeTests(unittest.TestCase):
    def test32_actual279_and_original190_175_40_36_are_distinct_complete_source_custody(self):
        import producer698_source_fixture_recovery as producer
        hashes = latest.current_input_hashes(ROOT)
        views = {view: latest.predecessor_input_hashes(view) for view in latest.VIEWS}
        self.assertEqual(282, len(hashes))
        self.assertEqual({"final_ci175": 175, "cookie609_raw40": 40, "share607": 36,
                          "producer676_raw190": 190}, {v: len(m) for v, m in views.items()})
        self.assertEqual(hashes, producer.current_input_hashes(ROOT))
        self.assertEqual(hashes, ci668.current_input_hashes())
        self.assertEqual(views[latest.PRODUCER_VIEW], producer.original_producer190_input_hashes(ROOT))
        self.assertEqual(views[latest.CI_VIEW], ci668.sealed_ci668_175_hashes())
        self.assertEqual("6bbb65c800811d36703d018381aa3bd15178348a6c5709cb26fabc9fa35f4dfa",
                         latest.PREDECESSOR_CUSTODY["accepted_joint264_source_map_sha256"])
        self.assertFalse(latest.PREDECESSOR_CUSTODY["joint279_source_proposal_adopted"])
        self.assertFalse(latest.PREDECESSOR_CUSTODY["producer_or_reuse_runtime_accepted"])
        self.assertTrue(all(sha((ROOT / n).read_bytes()) == d for n, d in hashes.items()))

    def test33_original645_27_rows_and_original_own_guard_remain_exact_while_new_raw_guard_refuses_old(self):
        import producer698_source_fixture_recovery as producer
        raw_spec = (ROOT / latest.PRODUCER_SPEC).read_bytes()
        self.assertEqual("64538883def9615a5c92060dcdc121404165b23278666c947e016b8eb67145d8", sha(raw_spec))
        original = producer._document()
        self.assertEqual((12, 27), (len(original["bindings"]),
                         sum(len(r["fragments"]) for r in original["bindings"].values())))
        raw = (ROOT / latest.PRODUCER_OWNER).read_bytes()
        old = latest.current_source_in_view(latest.PRODUCER_OWNER, raw, latest.PRODUCER_VIEW)
        self.assertNotEqual(raw, old)
        self.assertEqual(latest.PRODUCER_OWNER_ANCESTOR_SHA256, sha(old))
        self.assertEqual(sha(old), producer._own_guard_payload(old, original))
        with self.assertRaises(ValueError):
            producer._own_guard_payload(raw, original)
        with self.assertRaises(ValueError):
            producer.current_source_before_producer698(latest.PRODUCER_OWNER, old)
        for name, row in original["bindings"].items():
            current = (ROOT / name).read_bytes()
            named = latest.current_source_in_view(name, current, latest.PRODUCER_VIEW)
            ancestor = producer.current_source_before_producer698(name, current)
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (sha(named), len(named)))
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(ancestor), len(ancestor)))
            forward = ancestor
            for f in row["fragments"]:
                self.assertEqual(1, forward.count(f["before"].encode()))
                forward = forward.replace(f["before"].encode(), f["after"].encode(), 1)
            self.assertEqual(named, forward)

    def test34_Cookie_producer_and_CI_qualify_only_original_raw_not_a_restored_inverse(self):
        import producer698_source_fixture_recovery as producer
        for relative in (latest.LIBRARY, latest.CI_OWNER, latest.CI_CONTROL,
                         latest.OFFLINE, latest.UI_SPLIT_CONTROL):
            raw = (ROOT / relative).read_bytes()
            with patch.object(cookie_outer, "current_source_before_cookie_outer",
                              wraps=cookie_outer.current_source_before_cookie_outer) as cookie_entry, \
                 patch.object(producer, "current_source_before_producer698",
                              wraps=producer.current_source_before_producer698) as producer_entry, \
                 patch.object(latest, "current_source_in_view", wraps=latest.current_source_in_view) as named_entry:
                actual = ci668.current_source_before_ci668(relative, raw)
            self.assertEqual([(relative, raw)], [c.args[:2] for c in cookie_entry.call_args_list])
            self.assertEqual([(relative, raw)], [c.args[:2] for c in producer_entry.call_args_list])
            self.assertTrue(named_entry.call_args_list)
            self.assertTrue(all(c.args[0] == relative and c.args[1] == raw for c in named_entry.call_args_list))
            self.assertEqual({latest.CI_VIEW, latest.PRODUCER_VIEW}, {c.args[2] for c in named_entry.call_args_list})
            expected = latest.current_source_in_view(relative, raw, latest.CI_VIEW)
            if relative == latest.UI_SPLIT_CONTROL:
                expected = ci668.source_before_ci668(relative, expected)
            self.assertEqual(expected, actual)

    def test35_diagnostics_fixed_split_and_Cookie_controls_keep_narrow_distinct_source_views(self):
        import producer698_source_fixture_recovery as producer
        exact = {
            latest.OFFLINE: "6126390c11769f3ea3b111510b7220f5a2d0956171e767c88b50b5def6e74757",
            "scripts/ci/offline_tooling_failure_inventory.py": "2df6e8e67fe614b189b5109ddf0a9272cf140372f2236e9b985926200ce1693d",
            "scripts/ci/test_offline_tooling_failure_inventory.py": "c15d05979c26976f07e8a71e0002d0ca394b0633b8c3467cf2c8e700771ecab9",
        }
        for relative, digest in exact.items():
            named = latest.current_source_in_view(relative, (ROOT / relative).read_bytes(), latest.PRODUCER_VIEW)
            self.assertEqual(digest, sha(named))  # Original190 identity, not current707 relabelling.
        raw = (ROOT / latest.OFFLINE).read_bytes()
        self.assertNotEqual(raw, latest.current_source_in_view(latest.OFFLINE, raw, latest.PRODUCER_VIEW))
        self.assertEqual("9bd6b6d8daa7d8e6270fc874c28a8b7692f815334d4d77130fb3d81c35d7897b",
                         sha(latest.current_source_in_view(latest.OFFLINE, raw, latest.CI_VIEW)))
        for relative in (latest.NEW_COOKIE_CONTROL, latest.OWNING_COOKIE_CONTROL, latest.CALLBACK_INIT):
            raw = (ROOT / relative).read_bytes()
            self.assertEqual(raw, producer.peel_producer698_for_history(relative, raw))
            for view in latest.VIEWS:
                self.assertEqual(raw, latest.peel_for_history(relative, raw, view))
        with source_model() as root:
            file = root / "scripts/ci/offline_tooling_failure_inventory.py"
            file.write_bytes(file.read_bytes() + b"\n# unqualified helper tail\n")
            with self.assertRaises(ValueError):
                latest.validate_current_sources(root)

    def test36_fourth_named_producer_view_never_admits_a_sibling_unknown_view_or_unverified_runtime(self):
        raw = (ROOT / latest.CI_OWNER).read_bytes()
        ancestor = latest.current_source_in_view(latest.CI_OWNER, raw, latest.PRODUCER_VIEW)
        self.assertEqual("f8bcba4d15a87f0f83b6c0ec3eee640d93704a4ed6d5508a5b4b405bc3ab75c9", sha(ancestor))
        with self.assertRaises(ValueError):
            latest.current_source_in_view(latest.CI_OWNER, ancestor, latest.PRODUCER_VIEW)
        for view in ("producer-latest", "joint264", "producer698", "noncurrent_share_CI_sibling"):
            with self.assertRaises(ValueError):
                latest.current_source_in_view(latest.CI_OWNER, raw, view)
        bad = copy.deepcopy(latest._document(ROOT))
        bad["predecessor_custody"]["producer_or_reuse_runtime_accepted"] = True
        with self.assertRaises(ValueError):
            latest._shape(bad, ROOT)
        bad = copy.deepcopy(latest._document(ROOT))
        bad["predecessor_inputs"][latest.PRODUCER_VIEW][latest.OFFLINE]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            latest._shape(bad, ROOT)




class CookieShareBudget707SourceSuccessorTests(unittest.TestCase):
    def test37_exact707_three_path_prelude_preserves_original175_190_9bd_and_share_ancestry(self):
        document = latest._document(ROOT)
        current = latest.current_input_hashes(ROOT)
        expected = latest.BUDGET707_CURRENT_SHA256
        self.assertEqual(set(expected), set(latest.BUDGET707_FRAGMENT_COUNTS))
        self.assertEqual(6, sum(len(document["derivative_bindings"][n]["fragments"]) for n in expected))
        for relative, digest in expected.items():
            raw = (ROOT / relative).read_bytes()
            self.assertEqual(current[relative], sha(raw))
            budget_raw = latest._failure711_to_budget707(raw, document) if relative == latest.OFFLINE else raw
            self.assertEqual(digest, sha(budget_raw))  # Original707 endpoint is not repinned to actual711.
            self.assertEqual(document["derivative_bindings"][relative]["after_bytes"], len(budget_raw))
            for view in latest.VIEWS:
                named = latest.current_source_in_view(relative, raw, view, ROOT)
                if relative not in document["predecessor_inputs"][view]:
                    self.assertEqual(raw, named)  # Cookie40 owns no budget leaf.
                else:
                    endpoint = document["predecessor_inputs"][view][relative]
                    self.assertEqual((endpoint["sha256"], endpoint["bytes"]), (sha(named), len(named)))
            old190 = latest.current_source_in_view(relative, raw, latest.PRODUCER_VIEW, ROOT)
            self.assertNotEqual(raw, old190)
            with self.assertRaises(ValueError):
                latest.current_source_in_view(relative, old190, latest.PRODUCER_VIEW, ROOT)
            for malformed in (raw + b"\n# unknown budget tail\n", raw[:-1], raw + raw):
                with self.assertRaises(ValueError):
                    latest.current_source_in_view(relative, malformed, latest.PRODUCER_VIEW, ROOT)
        raw = (ROOT / latest.OFFLINE).read_bytes()
        self.assertEqual("6126390c11769f3ea3b111510b7220f5a2d0956171e767c88b50b5def6e74757",
                         sha(latest.current_source_in_view(latest.OFFLINE, raw, latest.PRODUCER_VIEW, ROOT)))
        self.assertEqual("9bd6b6d8daa7d8e6270fc874c28a8b7692f815334d4d77130fb3d81c35d7897b",
                         sha(latest.current_source_in_view(latest.OFFLINE, raw, latest.CI_VIEW, ROOT)))
        self.assertEqual("64538883def9615a5c92060dcdc121404165b23278666c947e016b8eb67145d8",
                         sha((ROOT / latest.PRODUCER_SPEC).read_bytes()))

    def test38_budget_Cookie_producer_CI_ingress_uses_only_original_raw_and_never_readmits_named_inverse(self):
        import producer698_source_fixture_recovery as producer
        for relative in latest.BUDGET707_FRAGMENT_COUNTS:
            raw = (ROOT / relative).read_bytes()
            with patch.object(cookie_outer, "current_source_before_cookie_outer",
                              wraps=cookie_outer.current_source_before_cookie_outer) as cookie_entry, \
                 patch.object(producer, "current_source_before_producer698",
                              wraps=producer.current_source_before_producer698) as producer_entry, \
                 patch.object(latest, "current_source_in_view", wraps=latest.current_source_in_view) as named_entry:
                observed = ci668.current_source_before_ci668(relative, raw)
            self.assertEqual([(relative, raw)], [c.args[:2] for c in cookie_entry.call_args_list])
            self.assertEqual([(relative, raw)], [c.args[:2] for c in producer_entry.call_args_list])
            self.assertTrue(named_entry.call_args_list)
            self.assertTrue(all(c.args[0] == relative and c.args[1] == raw for c in named_entry.call_args_list))
            self.assertEqual({latest.CI_VIEW, latest.PRODUCER_VIEW}, {c.args[2] for c in named_entry.call_args_list})
            named_ci175 = latest.current_source_in_view(relative, raw, latest.CI_VIEW, ROOT)
            self.assertEqual(latest.predecessor_input_hashes(latest.CI_VIEW, ROOT)[relative], sha(named_ci175))
            expected_before668 = ci668.source_before_ci668(relative, named_ci175)
            self.assertEqual(expected_before668, observed)
            ci_row = ci668._document()["bindings"].get(relative)
            expected_hash = ci_row["before_sha256"] if ci_row is not None else sha(named_ci175)
            self.assertEqual(expected_hash, sha(observed))
            old190 = latest.current_source_in_view(relative, raw, latest.PRODUCER_VIEW, ROOT)
            self.assertEqual(old190, latest.peel_for_history(relative, old190, latest.CI_VIEW, ROOT))
            with self.assertRaises(ValueError):
                ci668.current_source_before_ci668(relative, old190)

    def test39_new707_control_is_actual_new_input_not_any_historical_domain_or_native_reuse_receipt(self):
        document = latest._document(ROOT)
        relative = latest.BUDGET707_CONTROL
        raw = (ROOT / relative).read_bytes()
        self.assertEqual("128e215ccbe2077b8089930fea4f0bb3f989208f645f1f047d079b8b15d7d496", sha(raw))
        self.assertIn(relative, document["raw_inputs"])
        self.assertIn(relative, latest.ADDED_INPUTS)
        self.assertNotIn(relative, document["derivative_bindings"])
        for view in latest.VIEWS:
            self.assertNotIn(relative, document["predecessor_inputs"][view])
            self.assertNotIn(relative, document["views"][view])
            self.assertEqual(raw, latest.peel_for_history(relative, raw, view, ROOT))
        self.assertFalse(latest.PREDECESSOR_CUSTODY["budget707_source_proposal_adopted"])
        self.assertFalse(latest.PREDECESSOR_CUSTODY["budget707_runtime_or_reuse_accepted"])
        bad = copy.deepcopy(document)
        bad["derivative_bindings"][latest.OFFLINE]["after_sha256"] = "339aad499e7d4f68ae0a40416e3f145cf40b9fb3346f416c28c99436c4fa3731"
        with self.assertRaises(ValueError):
            latest._shape(bad, ROOT)
        self.assertLessEqual(len((ROOT / latest.SPEC).read_bytes()), 512 * 1024)

    def test40_narrow_budget707_projection_reads_only_repository_transition_and_never_named_ancestors(self):
        document = latest._document(ROOT)
        for relative in latest.BUDGET707_FRAGMENT_COUNTS:
            raw = (ROOT / relative).read_bytes()
            with patch.object(latest, "_document", side_effect=AssertionError("no whole ancestor traversal")), \
                 patch.object(latest, "_view", side_effect=AssertionError("no named ancestor view")), \
                 patch.object(latest, "_ordinary", wraps=latest._ordinary) as read:
                before = latest.peel_budget707_for_history(relative, raw, ROOT)
            self.assertEqual([(ROOT, latest.SPEC, latest.MAX_SPEC)], [c.args for c in read.call_args_list])
            row = document["derivative_bindings"][relative]
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(before), len(before)))
            self.assertEqual(before, latest.peel_budget707_for_history(relative, before, ROOT))
            unknown = raw + b"\n# unknown diagnostic tail\n"
            self.assertEqual(unknown, latest.peel_budget707_for_history(relative, unknown, ROOT))
        raw = (ROOT / latest.BUDGET707_CONTROL).read_bytes()
        with patch.object(latest, "_ordinary", side_effect=AssertionError("new control is not a transition")):
            self.assertEqual(raw, latest.peel_budget707_for_history(latest.BUDGET707_CONTROL, raw, ROOT))


class CookieShareFailure711SourceSuccessorTests(unittest.TestCase):
    def test41_actual282_reports_new711_bytes_and_only_two_new_raw_paths(self):
        document = latest._document(ROOT)
        hashes = latest.current_input_hashes(ROOT)
        self.assertEqual((280, 282), (len(document["raw_inputs"]), len(hashes)))
        self.assertEqual(set(hashes), latest.fixture_inputs(ROOT))
        self.assertEqual({latest.NEW_CONTROL, latest.NEW_DOC, latest.BUDGET707_CONTROL,
                          latest.FAILURE711_HELPER, latest.FAILURE711_CONTROL}, latest.ADDED_INPUTS)
        old_names = set().union(*(set(rows) for rows in document["predecessor_inputs"].values()))
        old_names.update(latest.IMPORT_CLOSURE24)
        self.assertEqual(275, len(old_names))
        self.assertEqual(set(document["raw_inputs"]), old_names | latest.ADDED_INPUTS)
        self.assertEqual("58f08f3fcda1e490743a8d28f7881473a28f5fcd1a3127abfffce35d6e7b2cb5", hashes[latest.OFFLINE])
        self.assertEqual("6a4c6509ce1c205f590456789c63fe99b475dc0e83242e751aef08e274fa087c",
                         document["derivative_bindings"][latest.OFFLINE]["after_sha256"])
        self.assertNotEqual(hashes[latest.OFFLINE], latest.BUDGET707_CURRENT_SHA256[latest.OFFLINE])
        self.assertTrue(all(sha((ROOT / name).read_bytes()) == digest for name, digest in hashes.items()))
        for relative, endpoint in latest.FAILURE711_ADDITION_ENDPOINTS.items():
            self.assertEqual(endpoint, document["raw_inputs"][relative])
            self.assertEqual(endpoint["sha256"], hashes[relative])
            for view in latest.VIEWS:
                self.assertNotIn(relative, document["predecessor_inputs"][view])
                self.assertNotIn(relative, document["views"][view])
                raw = (ROOT / relative).read_bytes()
                self.assertEqual(raw, latest.peel_for_history(relative, raw, view, ROOT))
                self.assertEqual(raw, latest.current_source_in_view(relative, raw, view, ROOT))

    def test42_explicit711_then_unchanged707_then_named_175_190_order_roundtrips(self):
        document = latest._document(ROOT)
        raw = (ROOT / latest.OFFLINE).read_bytes()
        row = document["failure711_bindings"][latest.OFFLINE]
        budget = latest._failure711_to_budget707(raw, document)
        self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(budget), len(budget)))
        forward = budget
        for fragment in row["fragments"]:
            self.assertEqual(1, forward.count(fragment["before"].encode()))
            forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
        self.assertEqual(raw, forward)
        real711, real707 = latest._failure711_to_budget707, latest._budget707_in_named_domain
        for view in (latest.CI_VIEW, latest.PRODUCER_VIEW):
            calls = []
            def observe711(payload, doc):
                calls.append(("711", sha(payload)))
                return real711(payload, doc)
            def observe707(named_view, relative, payload, doc):
                calls.append(("707", sha(payload)))
                return real707(named_view, relative, payload, doc)
            with patch.object(latest, "_failure711_to_budget707", side_effect=observe711), \
                 patch.object(latest, "_budget707_in_named_domain", side_effect=observe707):
                named = latest.current_source_in_view(latest.OFFLINE, raw, view, ROOT)
            self.assertEqual([("711", row["after_sha256"]), ("707", row["before_sha256"])], calls)
            endpoint = document["predecessor_inputs"][view][latest.OFFLINE]
            self.assertEqual((endpoint["sha256"], endpoint["bytes"]), (sha(named), len(named)))
        self.assertEqual("6126390c11769f3ea3b111510b7220f5a2d0956171e767c88b50b5def6e74757",
                         sha(real707(latest.PRODUCER_VIEW, latest.OFFLINE, budget, document)))
        self.assertEqual("9bd6b6d8daa7d8e6270fc874c28a8b7692f815334d4d77130fb3d81c35d7897b",
                         sha(latest.current_source_in_view(latest.OFFLINE, raw, latest.CI_VIEW, ROOT)))
        for view in (latest.COOKIE_VIEW, latest.SHARE_VIEW):
            with patch.object(latest, "_failure711_to_budget707", side_effect=AssertionError("not this domain")):
                self.assertEqual(raw, latest.current_source_in_view(latest.OFFLINE, raw, view, ROOT))

    def test43_separately_sealed_two_fragment711_binding_refuses_mutants_without_repinning707(self):
        document = latest._document(ROOT)
        row = latest._failure711_binding(document)
        self.assertEqual({latest.OFFLINE}, set(document["failure711_bindings"]))
        self.assertEqual(2, len(row["fragments"]))
        self.assertEqual(latest.FAILURE711_BINDING_SHA256,
                         sha((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()))
        for relative, digest in latest.BUDGET707_BINDING_SHA256.items():
            old = document["derivative_bindings"][relative]
            self.assertEqual(digest, sha((json.dumps(old, sort_keys=True, separators=(",", ":")) + "\n").encode()))
            self.assertEqual(latest.BUDGET707_CURRENT_SHA256[relative], old["after_sha256"])
        for key, value in (("before_sha256", "0" * 64), ("after_sha256", row["before_sha256"]),
                           ("after_bytes", row["after_bytes"] - 1)):
            bad = copy.deepcopy(document)
            bad["failure711_bindings"][latest.OFFLINE][key] = value
            with self.assertRaises(ValueError):
                latest._failure711_binding(bad)
        bad = copy.deepcopy(document)
        bad["failure711_bindings"][latest.OFFLINE]["fragments"].reverse()
        with self.assertRaises(ValueError):
            latest._failure711_binding(bad)
        bad = copy.deepcopy(document)
        fragment = bad["failure711_bindings"][latest.OFFLINE]["fragments"][0]
        fragment["after"] += "# unknown711 fragment tail\n"
        fragment["after_fragment_sha256"] = sha(fragment["after"].encode())
        with self.assertRaises(ValueError):
            latest._failure711_binding(bad)
        for bad in ({}, {"failure711_bindings": {}},
                    {"failure711_bindings": {latest.OFFLINE: row, latest.WORKFLOW: row}}):
            with self.assertRaises(ValueError):
                latest._failure711_binding(bad)
        bad = copy.deepcopy(document)
        bad["raw_inputs"][latest.OFFLINE] = {"sha256": row["before_sha256"], "bytes": row["before_bytes"]}
        with self.assertRaises(ValueError):
            latest._shape(bad, ROOT)
        bad = copy.deepcopy(document)
        bad["raw_inputs"][latest.FAILURE711_HELPER]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            latest._shape(bad, ROOT)

    def test44_old707_partial_tailed_unknown_and_named_bytes_never_enter_new_current_or_history_chain(self):
        document = latest._document(ROOT)
        raw = (ROOT / latest.OFFLINE).read_bytes()
        row = document["failure711_bindings"][latest.OFFLINE]
        old707 = latest._failure711_to_budget707(raw, document)
        fragment = row["fragments"][0]
        self.assertEqual(1, old707.count(fragment["before"].encode()))
        partial = old707.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
        named190 = latest.current_source_in_view(latest.OFFLINE, raw, latest.PRODUCER_VIEW, ROOT)
        named175 = latest.current_source_in_view(latest.OFFLINE, raw, latest.CI_VIEW, ROOT)
        bad_images = (old707, partial, raw[:-1], raw + b"\n# unknown711 tail\n", raw + raw, named190, named175)
        self.assertTrue(all(image != raw for image in bad_images))
        for view in (latest.CI_VIEW, latest.PRODUCER_VIEW):
            with patch.object(latest, "_view", side_effect=AssertionError("old/unknown must not enter new chain")):
                for image in bad_images:
                    with self.assertRaises(ValueError):
                        latest.current_source_in_view(latest.OFFLINE, image, view, ROOT)
                    self.assertEqual(image, latest.peel_for_history(latest.OFFLINE, image, view, ROOT))

    def test45_narrow711_707_data_peel_reads_only_repository_transition_no_named_ancestors(self):
        document = latest._document(ROOT)
        for relative in latest.BUDGET707_FRAGMENT_COUNTS:
            raw = (ROOT / relative).read_bytes()
            row = document["derivative_bindings"][relative]
            with patch.object(latest, "_document", side_effect=AssertionError("no whole ancestor traversal")), \
                 patch.object(latest, "_view", side_effect=AssertionError("no named view")), \
                 patch.object(latest, "_sealed_predecessor_hashes", side_effect=AssertionError("no named manifests")), \
                 patch.object(latest, "_ordinary", wraps=latest._ordinary) as read:
                before = latest.peel_budget707_for_history(relative, raw, ROOT)
            self.assertEqual([(ROOT, latest.SPEC, latest.MAX_SPEC)], [call.args for call in read.call_args_list])
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(before), len(before)))
        raw = (ROOT / latest.OFFLINE).read_bytes()
        old707 = latest._failure711_to_budget707(raw, document)
        old190 = latest.current_source_in_view(latest.OFFLINE, raw, latest.PRODUCER_VIEW, ROOT)
        old175 = latest.current_source_in_view(latest.OFFLINE, raw, latest.CI_VIEW, ROOT)
        for image in (old707, old190, old175, raw + b"\n# unrecognized diagnostic tail\n"):
            with patch.object(latest, "_document", side_effect=AssertionError("no layer search")), \
                 patch.object(latest, "_view", side_effect=AssertionError("no named view")), \
                 patch.object(latest, "_ordinary", wraps=latest._ordinary) as read:
                self.assertEqual(image, latest.peel_budget707_for_history(latest.OFFLINE, image, ROOT))
            self.assertEqual([(ROOT, latest.SPEC, latest.MAX_SPEC)], [call.args for call in read.call_args_list])
        for relative in (latest.FAILURE711_HELPER, latest.FAILURE711_CONTROL, latest.BUDGET707_CONTROL):
            raw_control = (ROOT / relative).read_bytes()
            with patch.object(latest, "_ordinary", side_effect=AssertionError("new source is not a transition")):
                self.assertEqual(raw_control, latest.peel_budget707_for_history(relative, raw_control, ROOT))
        bad = copy.deepcopy(document)
        bad["failure711_bindings"][latest.OFFLINE]["after_bytes"] -= 1
        fake = (json.dumps(bad, indent=2, sort_keys=True) + "\n").encode()
        with patch.object(latest, "SPEC_SHA256", sha(fake)), \
             patch.object(latest, "_ordinary", return_value=(fake, {})), \
             patch.object(latest, "_document", side_effect=AssertionError("no named traversal")):
            with self.assertRaises(ValueError):
                latest.peel_budget707_for_history(latest.OFFLINE, raw, ROOT)

    def test46_714_path_only_cache_fresh_custody_512k_template_and_original_new10_bytes_hold(self):
        source = (ROOT / latest.OWNER).read_bytes()
        tree = ast.parse(source)
        nodes = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        unchanged714_ast_sha256 = {'_binding': '6ba592ce270a9a706935c244451647c876378efded71479ca6feedbb8b2641d2', '_budget707_in_named_domain': 'c84509a2b4a51cb7ec23baca441531dcdceb8366023d4304937b25a27bc00b39', '_cached_source_path_parts': '5835654a0ba8aad1e7af3cfc78ca8e62f763c9c651941be8753a8abd87962110', '_descriptor_source_io_supported': '27ac006fc5cf879f981e92e92127c2f63dc8708bc4c61ac6155eb7372045752e', '_endpoint': '540a530093decfec67d9a59a4d50627a1fc13a22ebba189f4512181fdec640d9', '_identity': '74b6a95e82827ed5d196df0000c94134b8c01baffc7e6c49d37c28f33173ccf2', '_inverse_to_ancestor': 'bd084e93798ef6194dce5ce46ea1be4ff4f6c7541decf5dc72dda6490a19e9fa', '_ordinary': '86ae381abd3132f59d5eba89dd600bf4f32e9b2fc3eebb897f8d6c8393335df2', '_own_payload': 'ecf4bcaa7bdb2110948a48e4c18d96b9bcab2c627ef461720e2993764e4dc7e9', '_portable_ordinary': 'b718e70eb8d21ae27fda58fa9187d3d2353c96ce6c074a8942ed08b79666de93', '_raw_payload': '1cfaf674f3a8ac70ec573a7b6e78884bc09301a6c58142634b107ac95592aced', '_sealed_predecessor_hashes': 'a5663d25777af4094b751a4f094b48bb7ce531bd886fe6d19f09ad0accdd4e2e'}
        for name, digest in unchanged714_ast_sha256.items():
            self.assertEqual(digest, sha(ast.dump(nodes[name], include_attributes=False).encode()), name)
        decorated_cache = [node.name for node in nodes.values()
                           if any(isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)
                                  and decorator.func.id == "lru_cache" for decorator in node.decorator_list)]
        self.assertEqual(["_cached_source_path_parts"], decorated_cache)
        document = latest._document(ROOT)
        needle = ('SPEC_SHA256 = "' + latest.SPEC_SHA256 + '"\n').encode()
        self.assertEqual(1, source.count(needle))
        template = source.replace(needle, ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode(), 1)
        self.assertEqual(document["own_guard"]["template_sha256"], sha(template))
        self.assertEqual(document["own_guard"]["bytes"], len(source))
        self.assertEqual(512 * 1024, latest.MAX_SPEC)
        self.assertLessEqual(len((ROOT / latest.SPEC).read_bytes()), 512 * 1024)
        self.assertEqual("c82a70f4890b4a7d2bddfa60ef2273dfb4a41c9005871234282363e745fed14f",
                         sha((ROOT / latest.FAILURE711_CONTROL).read_bytes()))
        self.assertEqual("3bcb54e114807b6ffd4c2337367407354412312b1adecaba356ad57cdb5ccd28",
                         sha((ROOT / latest.FAILURE711_HELPER).read_bytes()))
        self.assertEqual("128e215ccbe2077b8089930fea4f0bb3f989208f645f1f047d079b8b15d7d496",
                         sha((ROOT / latest.BUDGET707_CONTROL).read_bytes()))


if __name__ == "__main__":
    unittest.main()
