"""Only NEW/owning controlled-remote source controls; ZERO Android/compiler/network/CI execution.

Manifest/APK-metadata/receipt fixtures below are explicitly synthetic parser data,
not real APKs or platform outcomes. Actual production/controller functions are used.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

TREE = Path(os.environ.get("NATIVECMPKIT_IO_REMOTE_TREE", Path(__file__).resolve().parents[2])).resolve()
sys.path.insert(0, str(TREE / "scripts/ci"))
import android_io_remote_documents as remote


class ControlledRemoteSourceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if Path(remote.__file__).resolve().parents[2] != TREE:
            raise AssertionError("Controls must read the exact selected NEW controller, not another worktree's module")
        cls.texts = {relative: (TREE / relative).read_text(encoding="utf-8") for relative in remote.SOURCE_FILES}
        cls.source_manifest = (TREE / remote.FIXTURE / "src/main/AndroidManifest.xml").read_bytes()
        cls.reporter = (TREE / remote.REPORTER_MANIFEST).read_bytes()

    def source_mutation_refused(self, path, before, after, message):
        texts = dict(self.texts)
        self.assertIn(before, texts[path], "Mutation must target actual owning source, not an invented fixture")
        texts[path] = texts[path].replace(before, after, 1)
        with self.assertRaisesRegex(ValueError, re.escape(message)):
            remote.validate_sources(texts)

    def manifest_refused(self, root, message, *, compiled=False):
        with self.assertRaisesRegex(ValueError, re.escape(message)):
            remote.validate_manifest(ET.tostring(root), compiled=compiled)

    def compiled_manifest(self):
        root = ET.fromstring(self.source_manifest)
        root.set("package", remote.PACKAGE)
        ET.SubElement(root, "uses-sdk", {remote.ANDROID + "minSdkVersion": "23", remote.ANDROID + "targetSdkVersion": "37"})
        root.find("application").set(remote.ANDROID + "debuggable", "true")
        root.find("application/provider").set(remote.ANDROID + "authorities", remote.AUTHORITY)
        return root

    def source_receipt(self):
        inputs = {relative: hashlib.sha256(self.texts[relative].encode("utf-8")).hexdigest() for relative in remote.SOURCE_FILES}
        return {"source_policy_verified": True, "source_inputs": inputs, "source_inputs_sha256": remote.lt.input_digest(inputs),
                "native_or_compile_success_inferred": False, "scope": "controlled-loopback-source-only"}

    def prepared_receipt(self):
        # Synthetic schema-only data, never a real native/helper/consumer acceptance receipt.
        digest, certificate = "d" * 64, "c" * 64
        return {"package": remote.PACKAGE, "source_fixture": remote.FIXTURE, "prepare_status": "passed", "verification_api_level": 35,
            "recipient_installed": True, "manual_URI_grant": False, "automatic_runtime_permission_grant": False,
            "native_or_consumer_success_inferred": False, "source_apk_sha256": digest,
            "installed_readback": {"apk_sha256": digest, "exact_one_APK_path_observed": True},
            "source_contract": self.source_receipt(), "apk_policy": {
                "compiled_manifest_inspected": True, "content_requires_android_grant": True, "signature_control_only": True,
                "INTERNET_only": True, "no_helper_grant_activity": True, "native_or_consumer_success_inferred": False,
                "certificate_sha256": certificate, "private_key_certificate_sha256": certificate,
                "apk_signer_revision": remote.SIGNER_REVISION, "signature_verification_min_sdk_version": 35,
                "signature_verification_max_sdk_version": 35}}

    def test_current_new_source_contract_and_accepted_bytes_are_held_without_native_claims(self):
        receipt = remote.source_contract(TREE)
        remote.validate_source_receipt(receipt)
        self.assertFalse(receipt["native_or_compile_success_inferred"])
        self.assertEqual(set(receipt["source_inputs"]), set(remote.SOURCE_FILES))
        for path, digest in remote.REUSED_PINS.items():
            self.assertEqual(receipt["source_inputs"][path], digest)

    def test_source_and_synthetic_compiled_manifest_have_exact_native_boundaries(self):
        for compiled, payload in ((False, self.source_manifest), (True, ET.tostring(self.compiled_manifest()))):
            with self.subTest(compiled_parser_fixture=compiled):
                result = remote.validate_manifest(payload, compiled=compiled)
                self.assertTrue(result["content_requires_android_grant"])
                self.assertTrue(result["signature_control_only"])
                self.assertTrue(result["INTERNET_only"])
                self.assertFalse(result["native_or_consumer_success_inferred"])

    def test_normal_internet_only_refuses_broad_storage_and_manage_documents(self):
        for permission in ("android.permission.MANAGE_DOCUMENTS", "android.permission.MANAGE_EXTERNAL_STORAGE", "android.permission.READ_EXTERNAL_STORAGE"):
            root = ET.fromstring(self.source_manifest)
            ET.SubElement(root, "uses-permission", {remote.ANDROID + "name": permission})
            with self.subTest(permission=permission):
                self.manifest_refused(root, "Only normal INTERNET")

    def test_no_helper_grant_activities_aliases_or_shared_uid(self):
        for tag in ("activity", "activity-alias", "receiver"):
            root = ET.fromstring(self.source_manifest)
            ET.SubElement(root.find("application"), tag, {remote.ANDROID + "name": ".ForeignGrant"})
            with self.subTest(extra_component=tag):
                self.manifest_refused(root, "No helper grant Activity")
        root = ET.fromstring(self.source_manifest); root.set(remote.ANDROID + "sharedUserId", remote.REPORTER)
        self.manifest_refused(root, "Exact remote package without shared-UID")

    def test_signature_control_and_exact_two_process_services_cannot_be_broadened(self):
        root = ET.fromstring(self.source_manifest); root.find("permission").set(remote.ANDROID + "protectionLevel", "normal")
        self.manifest_refused(root, "Exact signature control")
        root = ET.fromstring(self.source_manifest)
        root.findall("application/service")[1].set(remote.ANDROID + "process", ":other")
        self.manifest_refused(root, "Exact signature-service/process")

    def test_standard_provider_permission_process_authority_and_grants_are_strict(self):
        for field, value in (("permission", remote.PERMISSION), ("process", None), ("authorities", "foreign.documents"), ("grantUriPermissions", "false")):
            root = ET.fromstring(self.source_manifest); provider = root.find("application/provider")
            if value is None:
                provider.attrib.pop(remote.ANDROID + field)
            else:
                provider.set(remote.ANDROID + field, value)
            with self.subTest(native_boundary=field):
                self.manifest_refused(root, "Only standard MANAGE_DOCUMENTS/grant-capable")
        root = ET.fromstring(self.source_manifest)
        ET.SubElement(root.find("application/provider"), "grant-uri-permission", {remote.ANDROID + "pathPrefix": "/"})
        self.manifest_refused(root, "Only standard MANAGE_DOCUMENTS/grant-capable")

    def test_socket_network_security_config_is_not_a_fake_policy_boundary(self):
        for field, value in (("networkSecurityConfig", "@xml/anything"), ("usesCleartextTraffic", "true")):
            root = ET.fromstring(self.source_manifest); root.find("application").set(remote.ANDROID + field, value)
            with self.subTest(inapplicable_http_policy=field):
                self.manifest_refused(root, "No app-wide bypass or fake Socket HTTP-policy claim")

    def test_dtd_entities_unbounded_and_partial_manifests_refuse(self):
        for payload in (b"", b"x" * 65537, b"<manifest>", b'<!DOCTYPE manifest [<!ENTITY x "foreign">]><manifest>&x;</manifest>'):
            with self.subTest(parser_shape=hashlib.sha256(payload).hexdigest()[:8]):
                with self.assertRaises(ValueError):
                    remote.validate_manifest(payload, compiled=False)

    def test_synthetic_compiled_sdk_and_debug_variant_do_not_imply_api_coverage(self):
        for field, value in (("minSdkVersion", "24"), ("targetSdkVersion", "35"), ("maxSdkVersion", "35")):
            root = self.compiled_manifest(); root.find("uses-sdk").set(remote.ANDROID + field, value)
            with self.subTest(compiled_sdk=field):
                self.manifest_refused(root, "Exact compile37/min23 debug helper", compiled=True)
        root = self.compiled_manifest(); root.find("application").set(remote.ANDROID + "debuggable", "false")
        self.manifest_refused(root, "Exact compile37/min23 debug helper", compiled=True)

    def test_complete_reporter_inverse_preserves_exact_accepted_original_bytes(self):
        old = remote.normalize_reporter_manifest(self.reporter)
        self.assertEqual(hashlib.sha256(old).hexdigest(), remote.OLD_REPORTER_SHA256)
        self.assertNotIn(remote.PACKAGE.encode(), old)
        self.assertEqual(self.reporter.count(b"AndroidIoRemoteTreeGrantActivity"), 1)

    def test_partial_duplicate_and_mixed_reporter_unions_cannot_pass(self):
        for fragment in remote.REPORTER_FRAGMENTS:
            for payload in (self.reporter.replace(fragment, b"", 1), self.reporter.replace(fragment, fragment + fragment, 1)):
                with self.subTest(removed_or_duplicated_fragment=hashlib.sha256(fragment).hexdigest()[:8]):
                    with self.assertRaisesRegex(ValueError, "complete union"):
                        remote.normalize_reporter_manifest(payload)
        with self.assertRaisesRegex(ValueError, "complete union"):
            remote.normalize_reporter_manifest(remote.normalize_reporter_manifest(self.reporter))

    def test_reporter_inverse_cannot_hide_extra_permissions_or_changed_old_helpers(self):
        for payload in (self.reporter.replace(b"<queries>", b'<uses-permission android:name="android.permission.INTERNET" /><queries>', 1),
                        self.reporter.replace(b'android:exported="false"', b'android:exported="true"', 1)):
            with self.subTest(unrelated_delta=hashlib.sha256(payload).hexdigest()[:8]):
                with self.assertRaises(ValueError):
                    remote.normalize_reporter_manifest(payload)

    def test_exact_two_new_native_identities_and_missing_only_followups(self):
        self.assertEqual(remote.selected_methods("android-io-controlled-remote"), remote.METHODS)
        self.assertEqual(remote.selected_methods("android-io-controlled-remote-positive"), remote.METHODS[:1])
        self.assertEqual(remote.selected_methods("android-io-controlled-remote-cancel"), remote.METHODS[1:])
        for focus in remote.FOCUSES:
            identities = remote.identities(focus)
            self.assertTrue(identities); self.assertEqual(len(identities), len(remote.selected_methods(focus)))
            self.assertTrue(all(record["classname"] == remote.CLASS for record in identities))
            expected_filter = remote.CLASS if focus == "android-io-controlled-remote" else remote.CLASS + "#" + identities[0]["name"]
            self.assertEqual(remote.instrumentation_filter(focus), expected_filter)
            self.assertEqual(len(remote.required_tests(focus)), len(identities))

    def test_unknown_empty_full_suite_or_old_populations_refuse_selection(self):
        for focus in ("", None, [], "android-io", "android-io-named-providers", "all", "android-io-controlled-remote-retry-all"):
            with self.subTest(refused_type=type(focus).__name__):
                with self.assertRaises(ValueError):
                    remote.instrumentation_filter(focus)

    def test_actual_loopback_socket_origin_and_header_bounds_cannot_be_removed(self):
        path = remote.JAVA + "RemoteIoHttpTransport.java"
        for before, after in (('InetAddress.getByAddress(new byte[] {127, 0, 0, 1})', 'InetAddress.getByName("localhost")'),
                              ('owner.register(socket); registered = true;', 'registered = true;'),
                              ('lf != \'\\n\'', 'lf != 10'), ('"HTTP/1.1 200 OK".equals(reply.first)', 'true')):
            with self.subTest(native_transport_guard=before[:25]):
                self.source_mutation_refused(path, before, after, "Strict native loopback/endpoints/HTTP")

    def test_aggregate_header_deadline_restores_body_timeout_and_preserves_primary_failure(self):
        path = remote.JAVA + "RemoteIoHttpTransport.java"
        for before, after in (('long remaining = deadline - System.nanoTime()', 'long remaining = RemoteIoContract.READ_MS'),
                              ('socket.setSoTimeout(originalTimeout)', 'socket.setSoTimeout(1)'),
                              ('if (primary != null) primary.addSuppressed(cleanup); else throw cleanup;', 'throw cleanup;')):
            with self.subTest(aggregate_deadline_guard=before[:30]):
                self.source_mutation_refused(path, before, after, "Bounded HTTP aggregate header budget")

    def test_random_payloads_remain_backend_only_and_join_precedes_data_wipe(self):
        path = remote.JAVA + "RemoteIoHttpBackend.java"
        self.source_mutation_refused(path, 'random.nextBytes(payload); random.nextBytes(held)', 'java.util.Arrays.fill(payload, (byte) 7)',
                                     "Backend alone must own random bytes")
        texts = dict(self.texts)
        texts[path] = texts[path].replace('thread.join(RemoteIoContract.JOIN_MS)', 'Arrays.fill(payload, (byte) 0); thread.join(RemoteIoContract.JOIN_MS)', 1)
        with self.assertRaisesRegex(ValueError, "Nonce data wipe must follow"):
            remote.validate_sources(texts)

    def test_live_http_metadata_listing_root_is_child_icon_and_notify_remain(self):
        path = remote.JAVA + "RemoteIoDocumentsProvider.java"
        for before, after in (('String body = owned.metadata("metadata", id)', 'String body = "canned"'),
                              ('String body = owned.metadata("children", id)', 'String body = "L\\n"'),
                              ('DocumentsContract.Root.FLAG_SUPPORTS_IS_CHILD', '0'),
                              ('DocumentsContract.Root.COLUMN_ICON, android.R.drawable.ic_menu_upload', 'DocumentsContract.Root.COLUMN_ICON, 0')):
            with self.subTest(live_provider_guard=before[:30]):
                self.source_mutation_refused(path, before, after, "HTTP-provisioned cache only/live metadata")

    def test_real_first_socket_byte_precedes_all_pipe_allocation_and_return(self):
        path = remote.JAVA + "RemoteIoDocumentsProvider.java"
        texts = dict(self.texts)
        texts[path] = texts[path].replace('int first = exchange.input.read();', 'transfer.pipe = ParcelFileDescriptor.createReliablePipe();\n            int first = exchange.input.read();', 1)
        with self.assertRaisesRegex(ValueError, "Real held first socket byte must precede"):
            remote.validate_sources(texts)

    def test_fast_producer_start_and_descriptor_commit_share_the_owner_lock(self):
        path = remote.JAVA + "RemoteIoDocumentsProvider.java"
        before = 'synchronized (owned) {\n                transfer.worker.start();\n                transfer.descriptorReturned = true; owned.descriptorReturns++;\n            }'
        after = 'transfer.worker.start();\n            synchronized (owned) { transfer.descriptorReturned = true; owned.descriptorReturns++; }'
        self.source_mutation_refused(path, before, after, "Actual producer start/descriptor commit must share")

    def test_handled_reliable_pipe_producer_error_precedes_any_ordinary_writer_close(self):
        # This owning source regression is first run RED on the actual TWR bug, not a native pipe model.
        path = remote.JAVA + "RemoteIoDocumentsProvider.java"
        remote.validate_pump_writer_ownership(self.texts[path])

    def test_reliable_pipe_status_order_refuses_twr_early_close_and_the_wrong_end(self):
        path = remote.JAVA + "RemoteIoDocumentsProvider.java"
        for before, after in (
            ('try {\n            output = new ParcelFileDescriptor.AutoCloseOutputStream(transfer.pipe[1]);',
             'try (OutputStream output = new ParcelFileDescriptor.AutoCloseOutputStream(transfer.pipe[1])) {'),
            ('try { transfer.pipe[1].closeWithError("Owned remote producer failed"); }',
             'try { output.close(); transfer.pipe[1].closeWithError("Owned remote producer failed"); }'),
            ('transfer.pipe[1].closeWithError("Owned remote producer failed")',
             'transfer.pipe[0].closeWithError("Owned remote producer failed")'),
        ):
            with self.subTest(handled_pipe_failure_guard=before[:36]):
                self.source_mutation_refused(path, before, after, "Handled reliable pipe producer error must precede")

    def test_reliable_pipe_independent_cleanup_keeps_bare_pfd_primary_suppressed_and_fatal_errors(self):
        path = remote.JAVA + "RemoteIoDocumentsProvider.java"
        for before, after in (
            ('if (output != null) output.close(); else transfer.pipe[1].close();',
             'if (output != null) output.close();'),
            ('if (failure != cleanup) failure.addSuppressed(cleanup);', '/* swallowed error-status cleanup */'),
            ('if (primary == null) { primary = cleanup; transfer.failed(cleanup); }',
             'if (primary == null) { /* swallowed ordinary-close failure */ }'),
            ('else if (primary != cleanup) primary.addSuppressed(cleanup);', 'else primary = cleanup;'),
            ('catch (Error failure) { primary = failure; throw failure; }', 'catch (Error failure) { /* swallowed fatal error */ }'),
            ('if (primary == cleanup && cleanup instanceof Error) throw (Error) cleanup;', '/* swallowed fatal close error */'),
            ('} finally { transfer.finish(primary); }', '}\n            transfer.finish(primary);'),
        ):
            with self.subTest(independent_pipe_cleanup_guard=before[:36]):
                self.source_mutation_refused(path, before, after, "Reliable pipe writer cleanup must be independent")

    def test_actual_signal_listener_owned_socket_and_operation_canceled_cause_remain(self):
        path = remote.JAVA + "RemoteIoDocumentsProvider.java"
        for before, after in (('signal.setOnCancelListener(() ->', 'new Thread(() ->'),
                              ('ownSocket.close()', 'Thread.yield()'), ('cancelled.addSuppressed(failure)', '/* discarded IO cause */')):
            with self.subTest(cancellation_guard=before):
                self.source_mutation_refused(path, before, after, "HTTP-provisioned cache only/live metadata")

    def test_public_bounded_digest_eof_and_real_fifo_close_are_not_shadowed(self):
        path = remote.KOTLIN + "AndroidIoRemoteDocumentsTest.kt"
        for before, after in (('DeviceDescriptorIdentity.fromProvider(', 'DeviceDescriptorIdentity.fromProviderRegularFile('),
                              ('assertEquals(owner.payloadHash, digest)', 'check(digest.isNotEmpty())'),
                              ('assertEquals(-1L, it.readAtMostTo(tail, 1)); assertEquals(0L, tail.size)', 'it.close()')):
            with self.subTest(source_native_guard=before[:30]):
                self.source_mutation_refused(path, before, after, "Actual public bounded source/hash/EOF")

    def test_actual_native_cancellation_result_and_thread_terminal_cannot_be_skipped(self):
        path = remote.KOTLIN + "AndroidIoRemoteDocumentsTest.kt"
        for before, after in (('context.contentResolver.openFileDescriptor(uri, "r", signal)', 'context.contentResolver.openFileDescriptor(uri, "r")'),
                              ('assertIs<OperationCanceledException>(failure)', 'check(failure is Throwable)'),
                              ('assertFalse(assertNotNull(nativeThread).isAlive', 'assertTrue(true')):
            with self.subTest(native_result_guard=before[:25]):
                self.source_mutation_refused(path, before, after, "Cancellation must follow native pending admission")

    def test_cleanup_keeps_independent_owned_operations_primary_and_suppressed_errors(self):
        path = remote.KOTLIN + "AndroidIoRemoteDocumentsTest.kt"
        for before, after in (('first.addSuppressed(failure)', '/* swallowed cleanup */'), ('attempt { ui?.close() }', 'ui = null'),
                              ('attempt { control?.close() }', '/* leaked control replies */')):
            with self.subTest(cleanup_guard=before):
                self.source_mutation_refused(path, before, after, "Independent unconditional native/source/grant/UI/process/thread cleanup")

    def test_nonce_uid_generation_acknowledged_self_pid_and_actual_binder_death_remain(self):
        path = remote.KOTLIN + "RemoteIoEndpoint.kt"
        for before, after in (('message.sendingUid != owner.uid', 'false'), ('binder.linkToDeath(deathRecipient, 0)', '/* simulated disconnect */'),
                              ('assertFalse(binder.isBinderAlive', 'assertTrue(true'), ('thread.quitSafely(); thread.join(10_000); check(!thread.isAlive)', 'thread.quitSafely()')):
            with self.subTest(binder_identity_guard=before[:25]):
                self.source_mutation_refused(path, before, after, "NEW typed UID/generation/nonce endpoint")

    def test_manual_grants_dns_files_counter_reset_and_raw_console_are_forbidden(self):
        path = remote.JAVA + "RemoteIoDocumentsProvider.java"
        for added in ('grantUriPermission(', 'Runtime.getRuntime', 'getByName(', 'new File(', 'clearJournal', 'System.out.'):
            texts = dict(self.texts); texts[path] += "\n/* refused addition: " + added + " */\n"
            with self.subTest(forbidden_source=added):
                with self.assertRaisesRegex(ValueError, "Manual grants/DNS/host shell/body-file fallback"):
                    remote.validate_sources(texts)

    def test_source_receipt_is_complete_exact_and_cannot_claim_native_compile_acceptance(self):
        valid = self.source_receipt(); remote.validate_source_receipt(valid)
        for change in ("missing", "extra", "digest", "native"):
            receipt = deepcopy(valid)
            if change == "missing": receipt["source_inputs"].pop(remote.SOURCE_FILES[0])
            elif change == "extra": receipt["source_inputs"]["foreign"] = "f" * 64
            elif change == "digest": receipt["source_inputs_sha256"] = "e" * 64
            else: receipt["native_or_compile_success_inferred"] = True
            with self.subTest(source_receipt_refusal=change):
                with self.assertRaises(ValueError): remote.validate_source_receipt(receipt)

    def test_prepared_schema_needs_actual_exact_installed_bytes_and_api35_private_key(self):
        valid = self.prepared_receipt(); remote.validate_prepared_receipt(valid, valid["source_contract"])
        for change in ("installed", "key", "sdk", "bool_sdk", "native", "grant", "source"):
            receipt = deepcopy(valid)
            if change == "installed": receipt["installed_readback"]["apk_sha256"] = "e" * 64
            elif change == "key": receipt["apk_policy"]["private_key_certificate_sha256"] = "a" * 64
            elif change == "sdk": receipt["apk_policy"]["signature_verification_max_sdk_version"] = 37
            elif change == "bool_sdk": receipt["apk_policy"]["signature_verification_min_sdk_version"] = True
            elif change == "native": receipt["native_or_consumer_success_inferred"] = True
            elif change == "grant": receipt["manual_URI_grant"] = True
            else: receipt["source_contract"]["source_inputs_sha256"] = "f" * 64
            with self.subTest(preparation_schema_refusal=change):
                with self.assertRaises(ValueError): remote.validate_prepared_receipt(receipt)

    def test_source_apk_manifest_signer_readback_precede_install_and_reporter_compilation(self):
        source = (TREE / "scripts/ci/android_io_remote_documents.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        owner = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "OwnedRemoteIoDocuments")
        prepare = next(node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == "prepare")
        text = ast.get_source_segment(source, prepare)
        self.assertLess(text.index('source_contract(self.root)'), text.index('self.inspectors()'))
        self.assertLess(text.index('self.readback() is None'), text.index('lt.execute('))
        self.assertLess(text.index('self.inspect_apk(apk)'), text.index('self.install_attempted = True'))
        self.assertLess(text.index('self.install_attempted = True'), text.index('self.control("install"'))
        self.assertLess(text.index('self.control("install"'), text.index('actual = self.readback()'))
        self.assertNotIn('"-g"', text); self.assertNotIn('"-r"', text)
        self.assertIn('"--min-sdk-version", "35", "--max-sdk-version", "35"', source)
        self.assertNotIn('connectedAndroidDeviceTest', text) # NEW helper cannot start the reporter or a native suite itself.

    def test_new_apk_metadata_pair_is_private_without_broadening_old_allowlist(self):
        old = (TREE / "scripts/ci/android_geo_probe.py").read_text(encoding="utf-8")
        self.assertNotIn(remote.PACKAGE, old)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for pair in (("tests/consumer/android-io-documents", "io.github.apdelrahman1911.nativecmpkit.verification.iodocuments"),
                         (remote.FIXTURE, "foreign.package")):
                with self.subTest(foreign_pair=pair[0]):
                    with self.assertRaisesRegex(ValueError, "Only the reviewed NEW remote fixture/package pair"):
                        remote.metadata_apk(root, fixture=pair[0], package=pair[1])

    def test_synthetic_apk_metadata_refuses_split_traversal_duplicates_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); base = root / remote.FIXTURE / "build/outputs/apk/debug"; base.mkdir(parents=True)
            apk = base / "source-debug.apk"; apk.write_bytes(b"synthetic-reader-only-not-an-APK")
            path = base / "output-metadata.json"
            valid = {"artifactType": {"type": "APK"}, "applicationId": remote.PACKAGE, "variantName": "debug",
                     "elements": [{"type": "SINGLE", "filters": [], "outputFile": apk.name}]}
            path.write_text(json.dumps(valid)); self.assertEqual(remote.metadata_apk(root), apk)
            for change in ("split", "traversal", "foreign", "duplicate", "nonfinite"):
                data = deepcopy(valid)
                if change == "split": data["elements"][0]["filters"] = ["x86_64"]
                elif change == "traversal": data["elements"][0]["outputFile"] = "../source-debug.apk"
                elif change == "foreign": data["applicationId"] = "foreign"
                payload = json.dumps(data)
                if change == "duplicate": payload = payload.replace('"variantName": "debug"', '"variantName": "debug", "variantName": "release"')
                elif change == "nonfinite": payload = payload[:-1] + ', "bad": NaN}'
                path.write_text(payload)
                with self.subTest(synthetic_metadata_refusal=change):
                    with self.assertRaises(ValueError): remote.metadata_apk(root)

    def test_original_criterion_nonclaims_and_accepted_native_populations_are_not_rewritten(self):
        doc = (TREE / "docs/development/android-io-controlled-remote-provider.md").read_text(encoding="utf-8")
        fixture = (TREE / remote.FIXTURE / "README.md").read_text(encoding="utf-8")
        for token in ("Downloads remains source-refused, not N/A", "Activity destruction is not process", "Cancellation is not unavailable provider",
                      "41510126699", "41245152018", "41265408309", "41294135981", "whole-issue"):
            self.assertIn(token, doc)
        self.assertIn("No production/library/public API change", fixture)
        self.assertIn("NetworkSecurityConfig", fixture)
        self.assertIn("No native execution is implied", fixture)


if __name__ == "__main__":
    unittest.main()
