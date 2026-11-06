# SPDX-License-Identifier: Apache-2.0
"""Four NEW IO665 strict raw/inverse/history/source-hold controls, not native acceptance.

The final manifest/whole predecessor freeze remains lead-owned. Original source
pins and method bodies below are facts from the adopted corrected leaf and its
preparation predecessor, not guessed future endpoint values or fresh executions.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("NATIVECMPKIT_IO_REMOTE_ROUTING_TREE",
            os.environ.get("NATIVECMPKIT_IO_REMOTE_TREE", Path(__file__).resolve().parents[2]))).resolve()
sys.path.insert(0, str(TREE / "scripts/ci"))
import android_io_remote_routing_source_projection as projection
import android_io_remote_documents as remote
import ci_source_domain740 as source_domain
import ci_source_recovery740_742 as source_recovery

ADOPTED_HELD_INPUTS = {'calf-io/src/androidDeviceTest/AndroidManifest.xml': '26788255756c239bccb8e7c9ee15d0cf67afdb2cd6231defa494e42747f3573d', 'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoRemoteDocumentsTest.kt': '47313a30c844ddbf33a5f776aec7e4afb0ea616dc362bced298e4d1c51739dc4', 'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoRemoteTreeGrantActivity.kt': '1b49ca749a01e8fd276294d5286c83181c70bd7d8b098504dd49fbf669b1e325', 'calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/RemoteIoEndpoint.kt': '769ea4ec7ac11d29b2af4c85b6e3da7c9b74b3670a368df0a8a25bcc78e3ee82', 'docs/development/android-io-controlled-remote-provider.md': '34c9f4d5176e6e3395805aab2425cf4199af02638662b0121aec3c589adeb486', 'tests/consumer/android-io-remote-documents/README.md': '92ef61b5673af421fb48d6812d054fc5c119ac27b9ccf7b7d41d29cfcf083e92', 'tests/consumer/android-io-remote-documents/build.gradle.kts': '55967f734407e4e632a17fb9268879ce26979e3f9f96d8a1152af04da32f4160', 'tests/consumer/android-io-remote-documents/gradle.properties': '9bdf5fc8f73662d4e80072838783cc65fdae29b6b1c6a53de5d4cf8e20c8d44f', 'tests/consumer/android-io-remote-documents/settings.gradle.kts': '31ffb56210c51fc3d8344682b8183c76d55add20e09e5ffb4ea133229be9b981', 'tests/consumer/android-io-remote-documents/src/main/AndroidManifest.xml': 'b32fd120a12987616d7f641640d3779e832397c25396da298d1fc3bcc5ceb8f7', 'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoContract.java': '98bac439bc8e6ea1e6f8de5f4d8192ccc9707331c6e5973b93adcdaa5ed49244', 'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoControlService.java': '731549a3a8cba7647f3e665b0351ca6f804ac48c07c46d1a60545768b0bd7f44', 'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoDocumentsProvider.java': '41a32e36b8f785a9cba3793c253872e15131977d4276f091fa16b18e73a59c3e', 'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoHttpBackend.java': '58e2cb1091f16d81595b8065e23ab532a5f18378df5d48d18d50317014a58d89', 'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoHttpTransport.java': 'd6f6af63da9c2a89bc8a71fa306ee089852402919c256ec7fd7419ea819b65cc', 'tests/consumer/android-io-remote-documents/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/ioremotedocuments/RemoteIoProviderWitnessService.java': 'f6d2e7a107179f3e1992b3868ea6c73075459b9eeb74a59287194416ddb52593'}
ORIGINAL_REMOTE_METHOD_AST = {'test_current_new_source_contract_and_accepted_bytes_are_held_without_native_claims': '2d88dc799809b3c7a01905c631acdaef843567415746763ad37f2c18ce0590c4', 'test_source_and_synthetic_compiled_manifest_have_exact_native_boundaries': '3ca6f296c313e8f80d9e17c930f5ce7f633faaacd16252035a2de5f2d99ed9fe', 'test_normal_internet_only_refuses_broad_storage_and_manage_documents': '393615542a12a91d6e95789edd8a56ad7df0f66d4bac129cfd8027acc5e5cf82', 'test_no_helper_grant_activities_aliases_or_shared_uid': 'be9348a47046253ee799088498b47788e4b3d31f337ccc3778ad063ebd581c60', 'test_signature_control_and_exact_two_process_services_cannot_be_broadened': 'b0415f67e2a073effd448e2e1f25644bef3a9419255105440e244dcb46eebacf', 'test_standard_provider_permission_process_authority_and_grants_are_strict': '06c300e6906e37cbf5ab32626c498e2df9f6c30656f9131120eb576ad5e317bc', 'test_socket_network_security_config_is_not_a_fake_policy_boundary': 'c4adf3cf6878d48f1e83ec6a5e37f109ec77742b62486ae4f7afd7c129deac3a', 'test_dtd_entities_unbounded_and_partial_manifests_refuse': '52fab6a5ef015f730b2bec78069d9453fb4b4f5eb261edecd9ee23a6104ee109', 'test_synthetic_compiled_sdk_and_debug_variant_do_not_imply_api_coverage': '09d783455416c16209914c816e9d43ebaaa170edd18ac97711d7b967939cb5dc', 'test_complete_reporter_inverse_preserves_exact_accepted_original_bytes': '547aa172ca9d72c9c75d35d47c77109ac8151fecee6ff59676b5244a09a16dfa', 'test_partial_duplicate_and_mixed_reporter_unions_cannot_pass': '4827f9bfe948bc43fa957e1a57ff487d8e1ae7fef936e91ee384d4deac282fed', 'test_reporter_inverse_cannot_hide_extra_permissions_or_changed_old_helpers': 'd4fa4852545ab5b02562eede54436d12b476b17348ad897bfc244198d559cf12', 'test_exact_two_new_native_identities_and_missing_only_followups': '0ae4cd50e5e2683c3919e3d057f6627405ff606dd7ab7827af9c692d813df9de', 'test_unknown_empty_full_suite_or_old_populations_refuse_selection': 'd36d30d2fadf995eae5e324c082ba78a8c3d27de0c97de1da57c2b518b225d1d', 'test_actual_loopback_socket_origin_and_header_bounds_cannot_be_removed': '858d939c90329acb42650ca905c162d88db0f33eb7d55718afffb3ec66ef3290', 'test_aggregate_header_deadline_restores_body_timeout_and_preserves_primary_failure': '511e521063465ce633ef4f1c0f255bbf9fa21b73fe751667bfc7fcefef30ad92', 'test_random_payloads_remain_backend_only_and_join_precedes_data_wipe': '17e2fb7912335279c713749ae6eab976a6c75bd8935b98d85f3c1e6e647af336', 'test_live_http_metadata_listing_root_is_child_icon_and_notify_remain': 'cc52e10600b97f0007d6e193bf88c6e9e584eb75c9928ed828f685cfbdd9cf91', 'test_real_first_socket_byte_precedes_all_pipe_allocation_and_return': 'ebbb67db17571fec1dc890026d8da4a57dbacd2110071d715309821bd769bbb8', 'test_fast_producer_start_and_descriptor_commit_share_the_owner_lock': '5042cc7842c96560e1e017e67b6f7780c48ea43a552b761b6c16d1e19a34ff44', 'test_handled_reliable_pipe_producer_error_precedes_any_ordinary_writer_close': 'f970d629ec9b3518ed6884ebd88a9d3df442461b550228bdb6d9c36cdc3b9988', 'test_reliable_pipe_status_order_refuses_twr_early_close_and_the_wrong_end': '6623beab44c426793823d601f596cb63b32c3cb4ba98b6d55aec567f9d9bf787', 'test_reliable_pipe_independent_cleanup_keeps_bare_pfd_primary_suppressed_and_fatal_errors': '03f682d91b6d43094d5b677cc828cd6667da8c8e3f7668a7b53c6546ed0d5e41', 'test_actual_signal_listener_owned_socket_and_operation_canceled_cause_remain': '7f8db8f4dea27ad6dd7c6ed669db33d44a1b864381f5a39a9b2134174ef6e9a0', 'test_public_bounded_digest_eof_and_real_fifo_close_are_not_shadowed': '683ad2c9c7e51897d9088a68648477002510b4c14465a64740540a1b5fc3895f', 'test_actual_native_cancellation_result_and_thread_terminal_cannot_be_skipped': 'bf372a186ad5c18026bacdc1b176f2734ec69fa9651dda547ce79ee51c334a56', 'test_cleanup_keeps_independent_owned_operations_primary_and_suppressed_errors': '0d54dceca1e1559e6db07ca164cc167edfe12895d61a05f673f24a75ba1f384c', 'test_nonce_uid_generation_acknowledged_self_pid_and_actual_binder_death_remain': '90f14eea1513b8820a7103f5d366ab618e6d9c9b154f81829ca1b9dd613527d4', 'test_manual_grants_dns_files_counter_reset_and_raw_console_are_forbidden': 'bd6b3b1d0d0d4b8dc1089d5fa2ebe3d4f7a7a2ff20d80cb458413361a877f3f2', 'test_source_receipt_is_complete_exact_and_cannot_claim_native_compile_acceptance': 'f3ef1932abcb683bb900d1ebf4d224a0cfdb2d425719571fb2c2c87b64904e44', 'test_prepared_schema_needs_actual_exact_installed_bytes_and_api35_private_key': 'e3fd89d06316a991a4dce890223bcaef1da4860e48e0178e1cbbff32ddaab42d', 'test_source_apk_manifest_signer_readback_precede_install_and_reporter_compilation': '6b0e8e06b93f552ae1841378bfe9e4ae80d487c052f25a68e105a576db7c3b09', 'test_new_apk_metadata_pair_is_private_without_broadening_old_allowlist': '859954ab5eec9380247e11c3422bc1a7f7176d8edd10d7c7de44a4d127e44db2', 'test_synthetic_apk_metadata_refuses_split_traversal_duplicates_and_nonfinite_json': '268820f63e9d1894f300713efa53230a6de338701323da9bbf25be03acfd635f', 'test_original_criterion_nonclaims_and_accepted_native_populations_are_not_rewritten': '976dbf837ab2f19cb52ce333f320e585c43ec40601dddb9731cdc5c4b434f01d'}
ORIGINAL_REPORTER_METHOD_AST = {'test_complete_prior_and_exact_named_union_are_source_admitted_without_native_claims': 'd92f09bd4d169672b8a9124e7ceedaf50a4681e9edd2ef745e27de542220ff0c', 'test_partial_query_pairs_and_query_caller_hybrids_cannot_pass': 'd2fb116d4cf8a7d980ee3697ec4c22069ee50da6d558b5e61e0991e028ecf45c', 'test_extra_duplicate_missing_reordered_or_unrecognized_queries_refuse': '7f2881d7048ade13ad06bddda7296953547f7fc12615c82b13f5e1ab2e23aeab', 'test_query_container_package_and_provider_attributes_or_nested_entries_refuse': '7c6ca738dc7c7d0dfe4c6a5ea3cf2939554ed8c345cd264fcffe45706eed3122', 'test_system_provider_authorities_are_one_exact_source_bound_string': 'b89994e60da3abf43e7e560379b5868a6b59efea09d8ff9a0e7d83abec007ee0', 'test_open_tree_visibility_requires_only_the_exact_action_and_no_category_data_or_attributes': 'fc9ec3785b5d319dbd725fafe31a8f3bb6159c79fb2618081c4286954dea507a', 'test_named_caller_has_only_exact_name_nonexported_theme_and_no_extra_attributes': 'db3e3715284ff35ed1ae3ae389df260b988aa5665bbfc3c1b593f529455fa6e4', 'test_named_caller_cannot_gain_children_duplicates_foreign_components_or_old_mode_admission': 'a6ae8e36911259ab052307b3bd7215507b19471e359b4813a98f53fb6da2995b', 'test_original_single_control_permission_and_reporter_uid_process_refusals_remain': '3ab2df5f9ce9bb337deea09e8c6d2861e0d08c3a39f682f2520004262e88783c', 'test_original_grant_callers_and_bookmark_client_stay_private_with_no_extra_routes': '9b9857d90844acc91fb14e26078cae9a2faddf72808df1fa719b11bbcdfe1d82', 'test_original_fileprovider_fixed_authority_process_grant_and_path_metadata_refusals_remain': '9f79863963f2fb5454bf36045edbdb764886d1734cd170adb10fd7f0c8ba8097', 'test_existing_dtd_refusal_and_malformed_xml_do_not_become_union_admission': 'b8176463ee3ecb9b2797b0cfed4d6c5d3dade7ec6a75e05d679b08ad35e8ab0e'}
ORIGINAL_REMOTE_FUNCTION_AST = {'require': '8eb779d9bd8b46190e4bbc2aee14929cb007e3a590a8b7af7e0a8a54175efda4', 'metadata_apk': 'ee5f4c0f017c72bb3243786e41436173d72e05c02c2750a4697c96074b283d4f', 'selected_methods': '3dbac98588919059106c6888ddc3d846f9c4cde0684444b0fbb101df9e578d25', 'required_tests': '5b8baef9ea56f20fe63202b26494bf0a9905790994a1dd90e607a9dbb18fc75b', 'identities': 'bf7754d52999b2d749ae14937c6bad38249edb444ed45c5a30658b6b986b2f37', 'normalize_reporter_manifest': '1c2d470f96e98b1b3697aee50658e33feb6424651d69a04a2c84546868a8c888', 'validate_manifest': '5a46c585b223c08e28aead881830bb5642de9a3f42e8f94591eb8545013b2b8b', 'contains': 'f9cd74a5c8e2b5971e3fdfaf10e0d3ba618804dba41900b824f7a0f1ca55b4ef', 'validate_pump_writer_ownership': '17d534ddb0d56e059693daa1339d370c0546f69bb26dace35bee9aa462418b3b', 'validate_source_receipt': 'e509a85f6f21c383f047ad968373b3f8cc3418694cd6489c73e0ac76cca356bd'}
ORIGINAL_REMOTE_CLASS_AST = {'OwnedRemoteIoDocuments': 'af8dcbefcf21e30054dc9edd0da0af2a53a078b970d0c9e53bc7affbc559a92a'}
ORIGINAL_OLD_IO_FUNCTION_AST = {'require': '8eb779d9bd8b46190e4bbc2aee14929cb007e3a590a8b7af7e0a8a54175efda4', 'validate_manifest': '86e88c2c73664cc0d3c30d8a7b82778faf068bee43fc4d6028e9d475173aafde', 'validate_source_receipt': '196cfaf8a00bcbb390c3836c693bf4d3ec70fbaab54bb37e6317acb89083d2c2', 'validate_reference_sources': 'f61edea55e78e32629bf5f8d34da1e59b1bb1e149197536a11ebb208bd7b1321', 'validate_unavailable_sources': '79c3ea13c204442e6675956bf8ff170813ad529925ddfd7fb214b52e0106fc4b', 'signer_certificate': 'c623c03aa577377645a57e8ac7c389ab418bf05eb67712b31f24356a7ef7cf5f', 'validate_prepared_receipt': '4778fe4cb33d06401f0436272f3efede285882d2f4761de2f5021ca512a9089b'}
ORIGINAL_OLD_IO_CLASS_AST = {'OwnedIoDocuments': 'a11c5a5bc81f16d7990703f6b0e2785d1876dedd36affa617a43988d35c3ed9f'}
ORIGINAL_REMOTE_VALIDATE_SOURCES_AST = '8f40c0069825d1b9ae3138a2e966c4389eaf138c1361d3fb7c709f23a918d0e2'
ORIGINAL_REMOTE_PREPARED_RECEIPT_AST = '83fee5326b7be52043b0b6a361e74e04b1ab8d67f2f727615f06250a8d0d39e1'
UNCHANGED_EXISTING_GUEST_HELPER_SHA256 = '92f8d79d3a0871f1abb619a0a17b36c87568e11151fb3dbefa4f12773de78bdb'


def syntax_hash(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def owner(tree, kind, name):
    values = [node for node in tree.body if isinstance(node, kind) and node.name == name]
    if len(values) != 1:
        raise AssertionError("One exact top-level source owner is required")
    return values[0]


def copy_fixture(root):
    # Dependencies exist physically without becoming current raw-source membership.
    inputs = (projection.fixture_inputs() | source_domain.dependency_inputs() |
              source_recovery.dependency_inputs())
    for relative in inputs:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((TREE / relative).read_bytes())


def historical_digest_assignments(tree):
    result = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and
                type(node.value.value) is str and re.fullmatch(r"[a-f0-9]{64}", node.value.value)):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id in result and result[target.id] != node.value.value:
                        raise AssertionError("Ambiguous historical SHA assignment")
                    result[target.id] = node.value.value
    return result


class AndroidIoRemoteRoutingProjectionControls(unittest.TestCase):
    def setUp(self):
        if Path(projection.__file__).resolve().parents[2] != TREE:
            raise AssertionError("The exact selected remote source projection is required")
        def forbidden(*args, **kwargs):
            raise AssertionError("A source projection control cannot execute an external process")
        for name in ("run", "Popen"):
            control = patch.object(subprocess, name, forbidden)
            control.start()
            self.addCleanup(control.stop)
        control = patch.object(os, "system", forbidden)
        control.start()
        self.addCleanup(control.stop)

    def test_latest_raw_admission_is_once_and_exact_remote_leaf_union_restores_the_frozen_predecessor(self):
        document = projection._document()
        self.assertRegex(document["predecessor"], r"^[a-f0-9]{40}$")
        self.assertEqual(projection.PREDECESSOR, document["predecessor"])
        self.assertEqual(projection.BOUND_PATHS, set(document["bindings"]))
        self.assertEqual(projection.ADDED_PATHS, set(document["added_inputs"]))
        self.assertEqual(projection.UNCHANGED_PATHS, set(document["unchanged_inputs"]))
        self.assertNotIn("30db3ed785e13013b5de3939fdd6eb70b6d4b25a", document["predecessor"],
                         "Preparation base is not the final lead-integrated UI endpoint")
        self.assertTrue(projection.validate_current_sources(TREE))
        self.assertEqual(set(remote.SOURCE_FILES) | {
            "docs/development/android-io-controlled-remote-provider.md", "tests/consumer/android-io-remote-documents/README.md"},
            (projection.BOUND_PATHS | projection.ADDED_PATHS | projection.UNCHANGED_PATHS |
             {projection.SOURCE_RELATIVE, projection.SPEC_RELATIVE}) & (set(remote.SOURCE_FILES) | {
                "docs/development/android-io-controlled-remote-provider.md", "tests/consumer/android-io-remote-documents/README.md"}))
        from tooling_recovery671_source_projection import source_before_tooling671, source_before_callback_composition680
        for relative, row in document["bindings"].items():
            raw = (TREE / relative).read_bytes()
            before = projection.current_source_before_remote_routing(relative, raw)
            owning_raw = source_before_callback_composition680(relative, source_before_tooling671(relative, raw))
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (projection.sha(owning_raw), len(owning_raw)))
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (projection.sha(before), len(before)))
            self.assertIs(before, projection.source_before_remote_routing(relative, before))
            self.assertEqual(before, projection.peel_remote_routing_for_history(relative, raw))
            forward = before
            for fragment in row["fragments"]:
                old, new = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual((projection.sha(old), projection.sha(new)),
                    (fragment["before_fragment_sha256"], fragment["after_fragment_sha256"]))
                self.assertEqual(1, forward.count(old))
                forward = forward.replace(old, new, 1)
            self.assertEqual(owning_raw, forward)
            with self.subTest(double_current_ingress=relative), self.assertRaises(ValueError):
                projection.current_source_before_remote_routing(relative, before)
        reporter = (TREE / remote.REPORTER_MANIFEST).read_bytes()
        self.assertEqual(remote.normalize_reporter_manifest(reporter),
                         projection.current_source_before_remote_routing(remote.REPORTER_MANIFEST, reporter))
        self.assertEqual(remote.OLD_REPORTER_SHA256,
            document["bindings"][remote.REPORTER_MANIFEST]["before_sha256"])

    def test_stale_partial_unknown_mixed_or_drifted_current_union_is_not_current_admission(self):
        document = projection._document()
        for relative, row in document["bindings"].items():
            raw = (TREE / relative).read_bytes()
            before = projection.source_before_remote_routing(relative, raw)
            fragment = row["fragments"][0]["after"].encode()
            displaced = raw.replace(fragment, b"", 1) + fragment
            for bad in (before, raw[:-1], raw + b"\n", displaced, b"", b"unknown", None,
                        bytearray(raw), raw.decode(), b"x" * (projection.MAX_SOURCE_BYTES + 1)):
                with self.subTest(relative=relative, kind=type(bad).__name__), self.assertRaises(ValueError):
                    projection.current_source_before_remote_routing(relative, bad)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            self.assertTrue(projection.validate_current_sources(root))
            for relative in sorted(projection.fixture_inputs()):
                path = root / relative
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b"\n# uncertified finite-source drift\n")
                    with self.subTest(drifted_current_owner=relative), self.assertRaises(ValueError):
                        projection.validate_current_sources(root)
                finally:
                    path.write_bytes(original)
            paths = sorted(document["bindings"])
            for relative in paths[:2]:
                path = root / relative
                path.write_bytes(projection.source_before_remote_routing(relative, path.read_bytes()))
            with self.assertRaises(ValueError):
                projection.validate_current_sources(root)
        with self.assertRaises(ValueError):
            projection._unique([("bindings", {}), ("bindings", {})])
        for reader in (projection.source_before_remote_routing, projection.current_source_before_remote_routing,
                       projection.peel_remote_routing_for_history):
            with self.assertRaises(ValueError):
                reader(Path("foreign-source"), b"unknown")

    def test_history_peels_only_exact_io_afterimages_before_unchanged_predecessor_pins(self):
        document = projection._document()
        hook_owners = set()
        for relative, row in document["bindings"].items():
            raw = (TREE / relative).read_bytes()
            before = projection.peel_remote_routing_for_history(relative, raw)
            self.assertEqual(row["before_sha256"], projection.sha(before))
            self.assertIs(before, projection.peel_remote_routing_for_history(relative, before))
            unknown = before + b"\n# unknown history still needs unchanged strict old pins\n"
            self.assertIs(unknown, projection.peel_remote_routing_for_history(relative, unknown))
            self.assertNotEqual(row["before_sha256"], projection.sha(unknown))
            with self.assertRaises(ValueError):
                projection.source_before_remote_routing(relative, unknown)
            if relative.endswith(".py"):
                prior_pins = historical_digest_assignments(ast.parse(before.decode()))
                current_pins = historical_digest_assignments(ast.parse(raw.decode()))
                for name, digest in prior_pins.items():
                    self.assertEqual(digest, current_pins.get(name), "A historical literal pin cannot be rewritten: " + relative + ":" + name)
                if (b"peel_remote_routing_for_history" in raw or b"current_source_before_remote_routing" in raw):
                    hook_owners.add(relative)
        self.assertEqual({"scripts/ci/ios_ui_split664_source_projection.py"}, hook_owners,
                         "Only the latest UI companion owns the additive remote ingress/history hooks")
        import ios_ui_split664_source_projection as split
        import webview_current_contract667_source_projection as contract
        for module in (split, contract):
            self.assertEqual(TREE, Path(module.__file__).resolve().parents[2])
            self.assertTrue(module.validate_current_sources(TREE))
        split_hashes = split.current_input_hashes()
        remote_hashes = projection.current_input_hashes()
        self.assertEqual(set(split_hashes), split.fixture_inputs())
        self.assertEqual(set(remote_hashes), projection.fixture_inputs())
        self.assertEqual(remote_hashes, {name: split_hashes[name] for name in projection.fixture_inputs()})
        current = contract.current_contract_hashes()
        self.assertEqual(set(current), contract.contract_input_paths())
        self.assertEqual(current, {name: projection.sha((TREE / name).read_bytes()) for name in current})
        self.assertEqual(remote_hashes, {name: current[name] for name in projection.fixture_inputs()})
        split_document = split._document()
        for relative in projection.BOUND_PATHS & split.BOUND_PATHS:
            raw = (TREE / relative).read_bytes()
            ui = projection.current_source_before_remote_routing(relative, raw)
            self.assertEqual(split_document["bindings"][relative]["after_sha256"], projection.sha(ui))
            restored = split.current_source_before_ui_split664(relative, raw)
            self.assertEqual(split_document["bindings"][relative]["before_sha256"], projection.sha(restored))
            self.assertEqual(restored, split.peel_ui_split664_for_history(relative, raw))
            with self.assertRaises(ValueError):
                split.current_source_before_ui_split664(relative, ui)
        contract_document = contract._qualified_document()
        for relative, row in contract_document["bindings"].items():
            raw = (TREE / relative).read_bytes()
            restored = contract.current_source_before_contract667(relative, raw)
            self.assertEqual(row["before_sha256"], projection.sha(restored))
            self.assertEqual(restored, contract.peel_contract667_for_history(relative, raw))
        projection_source = ast.parse((TREE / projection.SOURCE_RELATIVE).read_text())
        for name in ("source_before_remote_routing", "current_source_before_remote_routing", "peel_remote_routing_for_history"):
            node = owner(projection_source, ast.FunctionDef, name)
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    self.assertNotIsInstance(child.func, ast.Lambda)
                    self.assertNotIn(getattr(child.func, "id", None), {"exec", "eval", "compile", "__import__"})
                self.assertNotIsInstance(child, (ast.Import, ast.ImportFrom), "Reconstructed sources never import or execute themselves")
        unknown = b"unlisted pass-through is not current source certification"
        self.assertIs(unknown, projection.peel_remote_routing_for_history("unlisted", unknown))

    def test_native_assertions_original_methods_and_external_side_effect_boundaries_are_unchanged(self):
        for relative, digest in ADOPTED_HELD_INPUTS.items():
            self.assertEqual(digest, projection.sha((TREE / relative).read_bytes()), relative)
        from tooling_recovery671_source_projection import current_source_before_tooling671
        guest_relative = "scripts/ci/android_camera_developer_prerequisite.py"
        guest_raw = (TREE / guest_relative).read_bytes()
        guest_historical = current_source_before_tooling671(guest_relative, guest_raw)
        self.assertEqual(UNCHANGED_EXISTING_GUEST_HELPER_SHA256, projection.sha(guest_historical),
                         "Remote root/FD/process/disposal reuse cannot change the existing Camera ledger or historical schema")
        remote_test = ast.parse((TREE / "scripts/ci/test_android_io_remote_documents.py").read_text())
        methods = {node.name: syntax_hash(node) for node in owner(remote_test, ast.ClassDef, "ControlledRemoteSourceControls").body
                   if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
        self.assertEqual(set(ORIGINAL_REMOTE_METHOD_AST), set(methods))
        changed = "test_exact_two_new_native_identities_and_missing_only_followups"
        for name, digest in ORIGINAL_REMOTE_METHOD_AST.items():
            if name != changed:
                self.assertEqual(digest, methods[name], "Original accepted/refusal assertion body cannot be rewritten: " + name)
        self.assertNotEqual(ORIGINAL_REMOTE_METHOD_AST[changed], methods[changed])
        reporter = ast.parse((TREE / "scripts/ci/test_android_io_reporter_manifest_union.py").read_text())
        methods = {node.name: syntax_hash(node) for node in owner(reporter, ast.ClassDef, "ReporterManifestUnionSourceControls").body
                   if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
        self.assertEqual(ORIGINAL_REPORTER_METHOD_AST, methods)
        new_remote_text = (TREE / "scripts/ci/android_io_remote_documents.py").read_text()
        new_remote = ast.parse(new_remote_text)
        for name, digest in ORIGINAL_REMOTE_FUNCTION_AST.items():
            self.assertEqual(digest, syntax_hash(owner(new_remote, ast.FunctionDef, name)), name)
        for name, digest in ORIGINAL_REMOTE_CLASS_AST.items():
            self.assertEqual(digest, syntax_hash(owner(new_remote, ast.ClassDef, name)), name)
        validator = deepcopy(owner(new_remote, ast.FunctionDef, "validate_sources"))
        calls = [index for index, node in enumerate(validator.body) if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                 and isinstance(node.value.func, ast.Name) and node.value.func.id == "validate_direct_native_population"]
        self.assertEqual(1, len(calls))
        self.assertEqual("test", validator.body[calls[0]].value.args[0].id)
        validator.body.pop(calls[0])
        self.assertEqual(ORIGINAL_REMOTE_VALIDATE_SOURCES_AST, syntax_hash(validator), "Every original native body/refusal validator remains unchanged")
        prepared = ast.get_source_segment(new_remote_text, owner(new_remote, ast.FunctionDef, "validate_prepared_receipt"))
        after = 'receipt.get("prepare_status") == "passed" and type(receipt.get("verification_api_level")) is int and\n            receipt["verification_api_level"] == 35 and'
        before = 'receipt.get("prepare_status") == "passed" and receipt.get("verification_api_level") == 35 and'
        self.assertEqual(1, prepared.count(after))
        prior_prepared = ast.parse(prepared.replace(after, before, 1)).body[0]
        self.assertEqual(ORIGINAL_REMOTE_PREPARED_RECEIPT_AST, syntax_hash(prior_prepared))
        old_io = ast.parse((TREE / "scripts/ci/android_io_documents.py").read_text())
        for name, digest in ORIGINAL_OLD_IO_FUNCTION_AST.items():
            self.assertEqual(digest, syntax_hash(owner(old_io, ast.FunctionDef, name)), "Old helper pair/grant/manifest ownership is not broadened: " + name)
        for name, digest in ORIGINAL_OLD_IO_CLASS_AST.items():
            self.assertEqual(digest, syntax_hash(owner(old_io, ast.ClassDef, name)), name)
        self.assertFalse(remote.source_contract(TREE)["native_or_compile_success_inferred"])

    def test_guest_helper_671_history_is_exact_once_and_rejects_old_or_drift_as_current(self):
        import tooling_recovery671_source_projection as tooling
        relative = "scripts/ci/android_camera_developer_prerequisite.py"
        raw = (TREE / relative).read_bytes()
        row = tooling._document()["bindings"][relative]
        self.assertEqual(1, len(row["fragments"]))
        prior = tooling.current_source_before_tooling671(relative, raw)
        self.assertEqual((UNCHANGED_EXISTING_GUEST_HELPER_SHA256, row["before_bytes"]),
                         (projection.sha(prior), len(prior)))
        self.assertIs(prior, tooling.source_before_tooling671(relative, prior))
        self.assertNotEqual(projection.sha(prior), projection.sha(raw))
        for image in (prior, raw[:-1], raw + b"\n# unowned helper drift\n", b""):
            with self.subTest(bytes=len(image)), self.assertRaises(ValueError):
                tooling.current_source_before_tooling671(relative, image)
        # Existing process/root/FD/disposal/native obligations remain under their old bytes.
