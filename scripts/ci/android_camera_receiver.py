"""Exact owned native camera receiver and fresh report preservation. Never publishes."""
from pathlib import Path
import hashlib
import re
import xml.etree.ElementTree as ET

import library_tests as lt
from android_share_recipient import OwnedShareRecipient


class OwnedCameraReceiver(OwnedShareRecipient):
    PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver"
    FIXTURE = "tests/consumer/android-camera-receiver"
    OUTPUT = "camera-receiver"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.receipt["scope"] = "Separate native UID writes only the actual camera Activity EXTRA_OUTPUT using system-created URI grants. Signature-protected finite receiver; synthetic bytes/recipient selection, not camera/vendor UX, physical device, packaged Maven/API-ABI or release certification."


def archive_focused_reports(root: Path, output: Path, receipt: dict, plan: dict) -> dict:
    """Preserve the first actual XML before a serial second API overwrites Gradle's report tree."""
    if (plan.get("explicit_test_focus") != lt.ANDROID_CAMERA_PROVIDER_FOCUS or
            not lt.validate_test_focus(plan) or receipt.get("explicit_test_focus") != lt.ANDROID_CAMERA_PROVIDER_FOCUS or
            receipt.get("suite") != "android-device" or receipt.get("source_tree_dirty") is not False or
            receipt.get("source_revision_after") != receipt.get("source_revision") or receipt.get("changed_inputs") != []):
        raise ValueError("Only unchanged-source finite camera results can be archived")
    destination = lt.safe_path(root, (output / "fresh-reports").relative_to(root).as_posix())
    base = lt.safe_path(root, "build/ci-verification")
    if destination.exists() or not destination.is_relative_to(base) or len(receipt.get("modules", [])) != 1:
        raise ValueError("Use one new owned camera evidence directory")
    module = receipt["modules"][0]
    if module.get("module") != "calf-camera-picker" or len(module.get("reports", [])) != 1:
        raise ValueError("Expected exactly one nonempty actual camera XML")
    row, = module["reports"]
    path = lt.safe_path(root, row["path"])
    expected = lt.safe_path(root, plan["expected"][0]["report_directory"])
    if not path.is_relative_to(expected) or not re.fullmatch(r"TEST-[A-Za-z0-9_.-]+\.xml", path.name):
        raise ValueError("Wrong camera report location")
    before = path.stat()
    if not path.is_file() or before.st_nlink != 1 or not 0 < before.st_size < 8 * 1024**2:
        raise ValueError("Expected bounded unshared native XML")
    payload = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("Native XML changed during archival")
    cases = lt.junit_cases(payload)
    if (hashlib.sha256(payload).hexdigest() != row["sha256"] or cases != module["testcases"] or
            lt.case_counts(cases) != receipt["totals"] or
            receipt.get("task_execution_markers") != {plan["expected"][0]["task"]: 1}):
        raise ValueError("Actual native XML/task receipt disagrees")
    document = ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
    for parent in document.iter():
        for child in list(parent):
            if child.tag in {"system-out", "system-err", "properties"}: parent.remove(child)
    sanitized = ET.tostring(document, encoding="utf-8", xml_declaration=True)
    if lt.junit_cases(sanitized) != cases:
        raise ValueError("Sanitizing console/properties changed native outcomes")
    destination.mkdir()
    target = destination / path.name
    with target.open("xb") as stream: stream.write(sanitized)
    digest = hashlib.sha256(sanitized).hexdigest()
    if lt.sha256(target) != digest: raise ValueError("Archived XML readback disagrees")
    result = {"source_revision": receipt["source_revision"], "original_path": row["path"],
              "original_sha256": row["sha256"], "archived_path": target.relative_to(root).as_posix(),
              "archived_sha256": digest, "actual_testcases": cases, "original_passed": receipt["passed"],
              "console_properties_removed_only": True, "native_success_inferred_from_archival": False}
    lt.write_json(output / "fresh-reports.json", result)
    return result
