"""Private finite proposal, not an executable native controller or acceptance receipt.

No process/SDK acquisition, grant, dispatch or protected operation is performed.
Synthetic consistency checks here cannot establish actual Android execution.
"""
from __future__ import annotations

from dataclasses import dataclass

MODULE = "calf-permissions/core"
PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.storageprobe"
REPORTER = "com.mohamedrejeb.calf.calfpermissions.calfpermissionscore.test"
CLASS = "com.mohamedrejeb.calf.permissions.AndroidStorageCompatibilityTest"


@dataclass(frozen=True)
class StorageRow:
    profile: str
    api: int
    flavor: str
    target: int
    legacy: bool
    declares_write: bool
    declares_all_files: bool
    method: str


ROWS = (
    StorageRow("android-storage-api28", 28, "legacy28", 28, True, True, False,
               "api28LegacyPermissionControlsSharedStorage"),
    StorageRow("android-storage-api29-target28", 29, "legacyTarget28", 28, True, True, False,
               "api29Target28LegacyAccessStillNeedsNativeWriteDespiteNotRequiredHelper"),
    StorageRow("android-storage-api29-legacy", 29, "legacy29", 29, True, True, False,
               "api29Target29LegacyAccessStillNeedsNativeWriteDespiteNotRequiredHelper"),
    StorageRow("android-storage-api29-scoped", 29, "scoped29", 29, False, True, False,
               "api29ScopedAccessStaysBoundedWithNativeWriteGrant"),
    StorageRow("android-storage-api30-normal", 30, "modern", 35, False, False, False,
               "modernAppScopedAndSafDoNotNeedAllFiles"),
    StorageRow("android-storage-api30-all-files", 30, "allFiles", 35, False, False, True,
               "modernManifestAloneDoesNotGrantAllFilesAndOwnedSettingRestores"),
    StorageRow("android-storage-api35-normal", 35, "modern", 35, False, False, False,
               "modernAppScopedAndSafDoNotNeedAllFiles"),
    StorageRow("android-storage-api35-all-files", 35, "allFiles", 35, False, False, True,
               "modernManifestAloneDoesNotGrantAllFilesAndOwnedSettingRestores"),
)


def row_for(profile: str, *, module: str = MODULE) -> StorageRow:
    matches = [row for row in ROWS if row.profile == profile]
    if module != MODULE or len(matches) != 1:
        raise ValueError("Unknown storage profile or library module")
    return matches[0]


def proposed_plan(profile: str, *, module: str = MODULE) -> dict:
    row = row_for(profile, module=module)
    return {
        "module": MODULE, "api": row.api, "target_sdk": row.target,
        "owned_probe_package": PACKAGE, "owned_reporter_package": REPORTER,
        "fixture_flavor": row.flavor,
        "fixture_task": "assemble" + row.flavor[0].upper() + row.flavor[1:] + "Debug",
        "test_filter": CLASS + "#" + row.method,
        "required_cases": [{"classname": CLASS, "name": row.method}],
        "declares_write": row.declares_write,
        "declares_all_files": row.declares_all_files,
        "all_files_modes": ["default", "allow", "default"] if row.declares_all_files else [],
        "source_freeze_required": True,
        "native_tests_executed": 0,
        "native_or_compile_success_inferred": False,
    }


def check_modeled_observation(profile: str, witness: dict) -> dict:
    """Check consistency only. Even a complete model is never a native pass."""
    row = row_for(profile)
    required = {"api", "target", "package", "uid", "installed_uid", "pid", "reporter_uid",
                "signature_match", "legacy", "declares_all_files", "manager", "appop",
                "write_granted", "availability", "access", "result_granted", "native_launches",
                "app_scoped_bytes_match", "saf_bytes_match", "saf_framework_result",
                "saf_persisted_read", "saf_release_verified", "raw_allowed", "raw_errno",
                "descriptor_cleanup_verified", "all_files_restored"}
    if not isinstance(witness, dict) or set(witness) != required:
        raise ValueError("Missing or unexpected modeled observation fields")
    if (witness["api"] != row.api or witness["target"] != row.target or
            witness["package"] != PACKAGE or
            any(type(witness[key]) is not int for key in ("uid", "installed_uid", "reporter_uid", "pid")) or
            witness["pid"] <= 0 or witness["installed_uid"] < 10000 or
            witness["uid"] != witness["installed_uid"] or witness["uid"] == witness["reporter_uid"] or
            witness["signature_match"] is not True or witness["legacy"] is not row.legacy or
            witness["declares_all_files"] is not row.declares_all_files):
        raise ValueError("Modeled installed/SDK/signature/legacy identity mismatch")
    expected_availability = "Available" if row.api == 28 else "NotRequired"
    expected_access = "Full" if row.api == 28 else "Unknown"
    if (witness["availability"] != expected_availability or witness["access"] != expected_access or
            witness["result_granted"] is not True or witness["native_launches"] != 0 or
            witness["write_granted"] is not row.declares_write):
        raise ValueError("NotRequired cannot imply a native permission request or unrestricted access")
    if row.api >= 30:
        if row.declares_all_files:
            if (witness["appop"], witness["manager"]) not in ((3, False), (0, True)):
                raise ValueError("All-files declaration/mode requires actual manager readback")
            if witness["all_files_restored"] is not True:
                raise ValueError("Owned all-files mode was not restored")
        elif witness["manager"] is not False or witness["appop"] != 3:
            raise ValueError("Normal variant must have no all-files declaration or grant")
    elif witness["manager"] is not None or witness["appop"] is not None:
        raise ValueError("Do not call or invent Android30 special-access state below API30")
    allowed = row.legacy or witness["manager"] is True
    if (witness["raw_allowed"] is not allowed or
            (witness["raw_errno"] != 0 if allowed else witness["raw_errno"] not in (1, 13))):
        raise ValueError("Unknown/other file error is not a scoped-storage denial or success")
    if not all(witness[key] is True for key in (
            "app_scoped_bytes_match", "saf_bytes_match", "saf_framework_result",
            "saf_persisted_read", "saf_release_verified", "descriptor_cleanup_verified")):
        raise ValueError("Missing actual-operation boundary/closure requirements")
    return {"modeled_contract_consistent": True, "native_success_inferred": False}
