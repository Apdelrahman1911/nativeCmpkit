"""Private synthetic guard models only. No SDK/native/library builds or tests."""
from copy import deepcopy
import unittest

import android_storage_compatibility_plan as plan


def model(profile: str, *, manager: bool = False) -> dict:
    row = plan.row_for(profile)
    allowed = row.legacy or manager
    return {
        "api": row.api, "target": row.target, "package": plan.PACKAGE,
        "uid": 10123, "installed_uid": 10123, "pid": 987, "reporter_uid": 10124,
        "signature_match": True, "legacy": row.legacy,
        "declares_all_files": row.declares_all_files,
        "manager": manager if row.api >= 30 else None,
        "appop": (0 if manager else 3) if row.api >= 30 else None,
        "write_granted": row.declares_write,
        "availability": "Available" if row.api == 28 else "NotRequired",
        "access": "Full" if row.api == 28 else "Unknown",
        "result_granted": True, "native_launches": 0,
        "app_scoped_bytes_match": True, "saf_bytes_match": True,
        "saf_framework_result": True, "saf_persisted_read": True,
        "saf_release_verified": True, "raw_allowed": allowed,
        "raw_errno": 0 if allowed else 13,
        "descriptor_cleanup_verified": True, "all_files_restored": True,
    }


class StorageCompatibilityProposalModels(unittest.TestCase):
    def test_shell_uid_cannot_supply_the_measured_file_operation(self):
        data = model("android-storage-api30-normal")
        data["uid"] = 2000
        with self.assertRaises(ValueError):
            plan.check_modeled_observation("android-storage-api30-normal", data)

    def test_same_uid_reporter_cannot_impersonate_the_separate_target(self):
        data = model("android-storage-api30-normal")
        data["reporter_uid"] = data["uid"]
        with self.assertRaises(ValueError):
            plan.check_modeled_observation("android-storage-api30-normal", data)

    def test_finite_api_target_matrix_has_no_sample_or_arbitrary_scope(self):
        self.assertEqual(8, len(plan.ROWS))
        self.assertEqual({28, 29, 30, 35}, {row.api for row in plan.ROWS})
        self.assertEqual({(28, True), (29, True), (29, False)},
                         {(row.target, row.legacy) for row in plan.ROWS if row.api == 29})
        descriptor = plan.proposed_plan("android-storage-api30-normal")
        self.assertIs(True, descriptor["source_freeze_required"])
        self.assertNotIn("source_inputs_frozen", descriptor)
        for name in ("android-storage-api23", "all", "sample-platforms-linux", "android-camera-restoration"):
            with self.assertRaises(ValueError):
                plan.proposed_plan(name)
        with self.assertRaises(ValueError):
            plan.proposed_plan("android-storage-api30-normal", module="sample/android")

    def test_not_required_unknown_access_and_denied_shared_io_can_coexist(self):
        name = "android-storage-api29-scoped"
        self.assertEqual({"modeled_contract_consistent": True, "native_success_inferred": False},
                         plan.check_modeled_observation(name, model(name)))
        for key, value in (("access", "Full"), ("availability", "Available"),
                           ("native_launches", 1), ("raw_allowed", True), ("raw_errno", 2)):
            data = model(name); data[key] = value
            with self.assertRaises(ValueError):
                plan.check_modeled_observation(name, data)

    def test_api29_legacy_native_write_is_separate_from_the_noop_library_request(self):
        for name in ("android-storage-api29-target28", "android-storage-api29-legacy"):
            data = model(name)
            self.assertFalse(plan.proposed_plan(name)["declares_all_files"])
            self.assertTrue(plan.check_modeled_observation(name, data)["modeled_contract_consistent"])
            data["write_granted"] = False
            with self.assertRaises(ValueError):
                plan.check_modeled_observation(name, data)

    def test_all_files_manifest_alone_is_denied_and_allow_needs_manager_readback(self):
        name = "android-storage-api30-all-files"
        for manager in (False, True):
            self.assertTrue(plan.check_modeled_observation(name, model(name, manager=manager))["modeled_contract_consistent"])
        data = model(name); data["appop"] = 0
        with self.assertRaises(ValueError):
            plan.check_modeled_observation(name, data)
        data = model(name); data["raw_allowed"] = True
        with self.assertRaises(ValueError):
            plan.check_modeled_observation(name, data)

    def test_normal_variant_cannot_silently_gain_all_files(self):
        for name in ("android-storage-api30-normal", "android-storage-api35-normal"):
            self.assertEqual([], plan.proposed_plan(name)["all_files_modes"])
            with self.assertRaises(ValueError):
                plan.check_modeled_observation(name, model(name, manager=True))

    def test_saf_grant_and_descriptor_or_setting_cleanup_cannot_be_inferred(self):
        name = "android-storage-api35-all-files"
        for key in ("saf_framework_result", "saf_persisted_read", "saf_release_verified",
                    "descriptor_cleanup_verified", "all_files_restored"):
            data = model(name); data[key] = False
            with self.assertRaises(ValueError):
                plan.check_modeled_observation(name, data)

    def test_complete_models_remain_synthetic_not_native_passes(self):
        for row in plan.ROWS:
            result = plan.check_modeled_observation(row.profile, model(row.profile))
            self.assertIs(False, result["native_success_inferred"])
            data = deepcopy(model(row.profile)); data["native_passed"] = True
            with self.assertRaises(ValueError):
                plan.check_modeled_observation(row.profile, data)


if __name__ == "__main__":
    unittest.main()
