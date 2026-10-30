"""Synthetic installer/ownership adversarial fixtures: zero Android or library executions."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import android_share_recipient as p
import android_geo_probe as geo


class AndroidShareRecipientOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "build/ci-verification/synthetic"
        self.output.mkdir(parents=True)
        self.env = {"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(self.output/"android-user"),
                    "PRIVATE_SYNTHETIC_SIGNING_CONTEXT": "not-for-receipts"}
        self.owner = p.OwnedShareRecipient(self.root, self.output, Path("/synthetic/sdk"), "emulator-5588",
                                         lambda: True, environment=self.env)

    def apk(self):
        base = self.root / p.FIXTURE / "build/outputs/apk/debug"
        base.mkdir(parents=True)
        apk = base/"recipient-debug.apk"
        apk.write_bytes(b"synthetic-APK-bytes-not-native-evidence")
        (base/"output-metadata.json").write_text(json.dumps({"applicationId": p.PACKAGE, "variantName": "debug",
            "artifactType": {"type": "APK"}, "elements": [{"type": "SINGLE", "filters": [], "outputFile": apk.name}]}))
        return apk

    def result(self, code=0, body=b"", error=b""):
        return subprocess.CompletedProcess([], code, body, error)

    def test_only_exact_reviewed_fixture_package_pairs_are_accepted_with_geo_default_unchanged(self):
        apk = self.apk()
        self.assertEqual(apk, geo.metadata_apk(self.root, fixture=p.FIXTURE, package=p.PACKAGE))
        for fixture, package in [(p.FIXTURE, geo.PACKAGE), (geo.FIXTURE, p.PACKAGE), ("../escape", p.PACKAGE),
                                  ("tests/consumer/arbitrary", "foreign.package")]:
            with self.assertRaises(ValueError): geo.metadata_apk(self.root, fixture=fixture, package=package)
        with self.assertRaises(ValueError): geo.metadata_apk(self.root)

    def test_lost_native_avd_lease_cannot_execute_any_control_or_foreign_cleanup(self):
        self.owner.is_owned = lambda: False
        with patch.object(p.subprocess, "run") as run, self.assertRaises(ValueError):
            self.owner.control("uninstall", p.PACKAGE)
        run.assert_not_called()

    def test_third_uid_document_fixture_has_its_own_exact_metadata_package_and_receipt_only_output(self):
        documents = p.OwnedShareDocuments(self.root, self.output, Path("/synthetic/sdk"), "emulator-5588",
                                          lambda: True, environment=self.env)
        base = self.root / documents.FIXTURE / "build/outputs/apk/debug"; base.mkdir(parents=True)
        apk = base/"source-debug.apk"; apk.write_bytes(b"synthetic-third-UID-not-native")
        (base/"output-metadata.json").write_text(json.dumps({"applicationId": documents.PACKAGE, "variantName": "debug",
            "artifactType": {"type": "APK"}, "elements": [{"type": "SINGLE", "filters": [], "outputFile": apk.name}]}))
        self.assertEqual(apk, geo.metadata_apk(self.root, fixture=documents.FIXTURE, package=documents.PACKAGE))
        self.assertNotEqual(self.owner.PACKAGE, documents.PACKAGE)
        self.assertEqual(self.output/"share-documents", documents.output)
        self.assertIn("Activity-result grant", documents.receipt["scope"])

    def test_preexisting_app_refuses_assembly_install_and_cleanup_mutation(self):
        with patch.object(self.owner, "readback", return_value={"apk_sha256": "f"*64}), \
                patch.object(p.lt, "execute") as execute, patch.object(self.owner, "control") as control:
            with self.assertRaises(ValueError): self.owner.prepare()
            receipt = self.owner.close()
        execute.assert_not_called(); control.assert_not_called()
        self.assertTrue(receipt["foreign_or_preexisting_recipient_mutated"] is False)

    def test_failed_assembly_receives_copied_private_signing_environment_without_export(self):
        self.env["PRIVATE_SYNTHETIC_SIGNING_CONTEXT"] = "later-parent-change"
        with patch.object(self.owner, "readback", return_value=None), \
                patch.object(p.lt, "execute", return_value={"exit_code": 1}) as execute, \
                patch.object(self.owner, "control") as control:
            with self.assertRaises(RuntimeError): self.owner.prepare()
            self.owner.close()
        self.assertEqual("not-for-receipts", execute.call_args.kwargs["env"]["PRIVATE_SYNTHETIC_SIGNING_CONTEXT"])
        control.assert_not_called()
        self.assertNotIn("PRIVATE_SYNTHETIC_SIGNING_CONTEXT", json.dumps(self.owner.receipt))
        self.assertNotIn("not-for-receipts", (self.owner.output/"receipt.json").read_text())

    def test_install_has_no_permission_autogrant_or_replace_and_cleanup_reverifies_exact_bytes(self):
        apk = self.apk(); digest = p.lt.sha256(apk)
        identity = {"apk_sha256": digest, "exact_one_APK_path_observed": True, "raw_path_uploaded": False}
        with patch.object(self.owner, "readback", side_effect=[None, identity, identity, None]), \
                patch.object(p.lt, "execute", return_value={"exit_code": 0}), \
                patch.object(self.owner, "control", side_effect=[self.result(body=b"Success\n"), self.result(), self.result()]) as control:
            self.owner.prepare(); receipt = self.owner.close()
        self.assertEqual(("install", "-t", str(apk)), control.call_args_list[0].args)
        self.assertEqual(("shell", "am", "force-stop", p.PACKAGE), control.call_args_list[1].args)
        self.assertEqual(("uninstall", p.PACKAGE), control.call_args_list[2].args)
        self.assertTrue(receipt["recipient_installed"]); self.assertTrue(receipt["owned_recipient_removed"])
        self.assertFalse(receipt["automatic_runtime_permission_grant"]); self.assertFalse(receipt["manual_URI_grant"])
        self.assertTrue(receipt["native_signature_UID_and_URI_reads_still_required"])
        self.assertEqual(receipt, json.loads((self.owner.output/"receipt.json").read_text()))

    def test_uncertain_failed_install_is_reconciled_and_only_exact_owned_app_is_removed(self):
        apk = self.apk(); identity = {"apk_sha256": p.lt.sha256(apk)}
        with patch.object(self.owner, "readback", side_effect=[None, identity, identity, None]), \
                patch.object(p.lt, "execute", return_value={"exit_code": 0}), \
                patch.object(self.owner, "control", side_effect=[self.result(1, b"uncertain"), self.result(), self.result()]) as control:
            with self.assertRaises(RuntimeError): self.owner.prepare()
            receipt = self.owner.close()
        self.assertEqual(1, receipt["install_exit_code"])
        self.assertTrue(receipt["owned_identity_reverified"]); self.assertTrue(receipt["owned_recipient_removed"])
        self.assertEqual(3, control.call_count, "One install only; no retry or blind uninstall")

    def test_changed_installed_bytes_never_authorize_foreign_uninstall(self):
        self.owner.install_attempted = True; self.owner.digest = "a"*64
        with patch.object(self.owner, "readback", return_value={"apk_sha256": "b"*64}), \
                patch.object(self.owner, "control") as control, self.assertRaises(ValueError): self.owner.close()
        control.assert_not_called(); self.assertFalse(self.owner.receipt["owned_recipient_removed"])

    def test_failed_uninstall_or_remaining_owned_app_cannot_claim_cleanup_success(self):
        self.owner.install_attempted = True; self.owner.digest = "a"*64
        with patch.object(self.owner, "readback", return_value={"apk_sha256": "a"*64}), \
                patch.object(self.owner, "control", return_value=self.result()), self.assertRaises(ValueError): self.owner.close()
        self.assertFalse(self.owner.receipt["owned_recipient_removed"])


class AndroidShareControllerOwnershipTests(unittest.TestCase):
    def setUp(self):
        # Compose the existing bounded mocked controller without replaying its methods.
        from test_android_device_controller import ControllerReceipts
        self.fixture = ControllerReceipts(methodName="runTest")
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.fixture.plan.update(suite="android-device", expected=[{"project": ":calf-share", "module": "calf-share"}],
                                 explicit_test_focus=p.lt.ANDROID_SHARE_GRANT_FOCUS)

    def test_recipient_prepares_after_boot_shares_exact_signing_environment_and_uninstalls_before_shutdown(self):
        import android_device_tests as c
        order = []
        with self.fixture.controlled() as mocks, patch.object(c.android_share_recipient, "OwnedShareDocuments") as documents_factory, \
                patch.object(c.android_share_recipient, "OwnedShareRecipient") as factory:
            documents_factory.return_value.prepare.return_value = {"recipient_installed": True}
            documents_factory.return_value.close.return_value = {"owned_recipient_removed": True}
            recipient = factory.return_value
            mocks["boot"].side_effect = lambda *a: order.append("boot") or {"serial": c.SERIAL}
            recipient.prepare.side_effect = lambda: order.append("recipient") or {"recipient_installed": True}
            mocks["tests"].side_effect = lambda *a, **k: order.append("tests") or self.fixture.receipt
            recipient.close.side_effect = lambda: order.append("remove") or {"owned_recipient_removed": True}
            mocks["shutdown"].side_effect = lambda *a: order.append("shutdown") or {"clean_shutdown": True}
            result = c.run(self.fixture.root, self.fixture.relative, only_modules=("calf-share",), focus=c.lt.ANDROID_SHARE_GRANT_FOCUS)
        self.assertTrue(result["passed"]); self.assertEqual(["boot", "recipient", "tests", "remove", "shutdown"], order)
        self.assertEqual(mocks["execute"].call_args_list[0].kwargs["env"], factory.call_args.kwargs["environment"])
        self.assertEqual(c.SERIAL, factory.call_args.args[3]); self.assertTrue(callable(factory.call_args.args[4]))
        self.assertEqual(c.lt.ANDROID_SHARE_GRANT_FOCUS, mocks["tests"].call_args.kwargs["focus"])

    def test_prepare_failure_never_executes_library_but_still_cleans_owned_recipient_and_engine(self):
        import android_device_tests as c
        with self.fixture.controlled() as mocks, patch.object(c.android_share_recipient, "OwnedShareDocuments") as documents_factory, \
                patch.object(c.android_share_recipient, "OwnedShareRecipient") as factory:
            documents_factory.return_value.prepare.return_value = {"recipient_installed": True}
            documents_factory.return_value.close.return_value = {"owned_recipient_removed": True}
            recipient = factory.return_value; recipient.prepare.side_effect = RuntimeError("SYNTHETIC_PRIVATE_ERROR")
            recipient.close.return_value = {"owned_recipient_removed": True}
            result = self.fixture.invoke()
        self.assertFalse(result["passed"]); mocks["tests"].assert_not_called()
        recipient.close.assert_called_once(); mocks["shutdown"].assert_called_once()
        self.assertNotIn("SYNTHETIC_PRIVATE_ERROR", json.dumps(result))

    def test_cleanup_failure_preserves_native_passes_without_promoting_controller_or_skipping_shutdown(self):
        import android_device_tests as c
        with self.fixture.controlled() as mocks, patch.object(c.android_share_recipient, "OwnedShareDocuments") as documents_factory, \
                patch.object(c.android_share_recipient, "OwnedShareRecipient") as factory:
            documents_factory.return_value.prepare.return_value = {"recipient_installed": True}
            documents_factory.return_value.close.return_value = {"owned_recipient_removed": True}
            recipient = factory.return_value; recipient.prepare.return_value = {"recipient_installed": True}
            recipient.close.side_effect = ValueError("SYNTHETIC_PRIVATE_ERROR")
            result = self.fixture.invoke()
        self.assertTrue(result["test_suite_passed"]); self.assertFalse(result["passed"])
        self.assertFalse(result["share_recipient"]["owned_recipient_removed"])
        self.assertEqual("ValueError", result["share_recipient"]["cleanup_error"])
        mocks["shutdown"].assert_called_once(); self.assertNotIn("SYNTHETIC_PRIVATE_ERROR", json.dumps(result))
        documents_factory.return_value.close.assert_called_once()

    def test_document_cleanup_failure_cannot_promote_native_passes_or_skip_other_owned_cleanup(self):
        import android_device_tests as c
        with self.fixture.controlled() as mocks, patch.object(c.android_share_recipient, "OwnedShareDocuments") as documents_factory, \
                patch.object(c.android_share_recipient, "OwnedShareRecipient") as factory:
            documents_factory.return_value.prepare.return_value = {"recipient_installed": True}
            documents_factory.return_value.close.side_effect = ValueError("SYNTHETIC_PRIVATE_DOCUMENT_ERROR")
            factory.return_value.prepare.return_value = {"recipient_installed": True}
            factory.return_value.close.return_value = {"owned_recipient_removed": True}
            result = self.fixture.invoke()
        self.assertTrue(result["test_suite_passed"]); self.assertFalse(result["passed"])
        self.assertFalse(result["share_documents"]["owned_recipient_removed"])
        factory.return_value.close.assert_called_once(); mocks["shutdown"].assert_called_once()
        self.assertNotIn("SYNTHETIC_PRIVATE_DOCUMENT_ERROR", json.dumps(result))


if __name__ == "__main__": unittest.main()
