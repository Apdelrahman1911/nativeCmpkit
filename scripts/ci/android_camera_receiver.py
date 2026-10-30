"""Exact owned native camera receiver and fresh report preservation. Never publishes."""
from pathlib import Path
import hashlib
import os
import re
import selectors
import subprocess
import time
import xml.etree.ElementTree as ET

import library_tests as lt
from android_geo_probe import installed_path
from android_share_recipient import OwnedShareRecipient

MAX_INSTALLED_APK_BYTES = 256 * 1024**2
INSTALLED_APK_TIMEOUT_SECONDS = 30


def package_path_shape(result: subprocess.CompletedProcess) -> dict:
    """Describe a refusal without exporting command bodies or installed paths.

    Classification is diagnostic only. In particular, a linker/SELinux message
    never becomes a valid path, successful install or permission by this helper.
    """
    stdout, stderr = result.stdout, result.stderr
    bounded = len(stdout) + len(stderr) <= 65536
    lines = stdout.splitlines() if bounded else []
    shapes = []
    for line in lines[:16]:
        value = line.decode("utf-8", errors="replace")
        lower = value.lower()
        row = {"sha256": hashlib.sha256(line).hexdigest(), "bytes": len(line)}
        if "avc:" in lower:
            row["kind"] = "SELinux-diagnostic"
        elif "linker" in lower and "unused DT entry" in value:
            row["kind"] = "linker-unused-DT-entry"
            types = re.findall(r"\btype (0x[0-9a-fA-F]{1,16})\b", value)
            row["dynamic_entry_types"] = types[:4]
        elif "linker" in lower:
            row["kind"] = "linker-diagnostic"
        elif value.startswith("package:"):
            path = value.removeprefix("package:")
            row.update(kind="package-path", strict_base_APK_shape=bool(re.fullmatch(r"/data/app/[A-Za-z0-9_./+=~-]+/base\.apk", path)) and ".." not in path,
                       root_is_data_app=path.startswith("/data/app/"), suffix_is_base_APK=path.endswith("/base.apk"),
                       contains_control_or_internal_space=bool(re.search(r"[\x00-\x20\x7f]", path)))
        else:
            row["kind"] = "other"
        shapes.append(row)
    return {"response_exit_code": result.returncode, "stdout_bytes": len(stdout), "stderr_bytes": len(stderr),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(), "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
            "response_bounded": bounded, "stdout_line_count": len(lines), "lines": shapes,
            "unclassified_additional_lines": max(0, len(lines) - len(shapes)),
            "raw_console_or_installed_paths_uploaded": False, "path_or_install_identity_accepted": False}


class OwnedCameraReceiver(OwnedShareRecipient):
    PACKAGE = "io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver"
    FIXTURE = "tests/consumer/android-camera-receiver"
    OUTPUT = "camera-receiver"

    def __init__(self, *args, api_level: int = 35, **kwargs):
        if type(api_level) is not int or api_level not in (23, 35):
            raise ValueError("Only the explicitly selected API23/35 camera receiver is supported")
        self.api_level = api_level
        super().__init__(*args, **kwargs)
        self.receipt["verification_api_level"] = api_level
        self.receipt["scope"] = "Separate native UID writes only the actual camera Activity EXTRA_OUTPUT using system-created URI grants. Signature-protected finite receiver; synthetic bytes/recipient selection, not camera/vendor UX, physical device, packaged Maven/API-ABI or release certification."

    def readback(self) -> dict | None:
        if self.api_level == 35:
            return super().readback()  # Keep the accepted modern/native checksum route.
        observation = self.control("shell", "pm", "path", self.PACKAGE)
        history = self.receipt.setdefault("package_path_observations", [])
        if len(history) >= 8:
            raise ValueError("No repeated/unbounded package path observation")
        history.append(package_path_shape(observation))
        path = installed_path(observation)  # Keep the rejecting guard until actual response is reviewed.
        if path is None:
            return None
        # Android6's toolbox/toybox contract does not include sha256sum. Choose
        # this explicit API23 route, never a silent fallback after a failed hash.
        # No APK copy is persisted; stream the exact validated installed path.
        if not self.is_owned():
            raise ValueError("Actual selected AVD lease lost before installed-byte read")
        command = [str(self.home / "platform-tools/adb"), "-s", self.serial, "exec-out", "cat", path]
        process = subprocess.Popen(command, cwd=self.root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        digest = hashlib.sha256(); size = 0; error_size = 0
        deadline = time.monotonic() + INSTALLED_APK_TIMEOUT_SECONDS
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ, "bytes")
                selector.register(process.stderr, selectors.EVENT_READ, "error")
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("Owned installed-APK byte read exceeded its deadline")
                    for key, _ in selector.select(min(remaining, 1)):
                        block = os.read(key.fileobj.fileno(), 65536)
                        if not block:
                            selector.unregister(key.fileobj)
                        elif key.data == "bytes":
                            size += len(block)
                            if size > MAX_INSTALLED_APK_BYTES:
                                raise ValueError("Unbounded installed camera receiver APK")
                            digest.update(block)
                        else:
                            error_size += len(block)
                            if error_size > 65536:
                                raise ValueError("Unbounded owned installed-byte error output")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Owned installed-APK byte read exceeded its deadline")
            if process.wait(timeout=remaining) != 0 or error_size or not size:
                raise ValueError("Installed camera receiver APK bytes unavailable")
            if self.digest is not None and self.receipt.get("source_apk_bytes") != size:
                raise ValueError("Installed camera receiver byte length differs from its owned source")
            if not self.is_owned():
                raise ValueError("Actual selected AVD lease lost after installed-byte read")
            return {"apk_sha256": digest.hexdigest(), "apk_bytes": size, "api_level": 23,
                    "byte_read_mechanism": "adb-exec-out-cat-host-SHA256",
                    "exact_one_APK_path_observed": True, "raw_path_uploaded": False}
        finally:
            try:
                if process.poll() is None:
                    lt.terminate_owned(process)
            finally:
                process.stdout.close(); process.stderr.close()

    def prepare(self) -> dict:
        self.receipt["prepare_status"] = "running"
        try:
            super().prepare()
            self.receipt["prepare_status"] = "passed"
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            self.receipt.update(prepare_status="failed", prepare_error=type(error).__name__)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)

    def close(self) -> dict:
        self.receipt["cleanup_status"] = "running"
        try:
            super().close()
            self.receipt["cleanup_status"] = "passed"
            return self.receipt
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            self.receipt.update(cleanup_status="failed", cleanup_error=type(error).__name__, owned_recipient_removed=False)
            raise
        finally:
            lt.write_json(self.output / "receipt.json", self.receipt)


def archive_focused_reports(root: Path, output: Path, receipt: dict, plan: dict) -> dict:
    """Preserve the first actual XML before a serial second API overwrites Gradle's report tree."""
    if (plan.get("explicit_test_focus") not in lt.ANDROID_CAMERA_PROVIDER_FOCUSES or
            not lt.validate_test_focus(plan) or receipt.get("explicit_test_focus") != plan.get("explicit_test_focus") or
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
    # AGP's real AVD XML name contains '(AVD) - 15', not just Java identifiers.
    # This is data, never a command: confinement, no symlinks, bounded immutable
    # bytes, matching hashes, cases and the fresh task marker remain mandatory.
    if not path.is_relative_to(expected) or not re.fullmatch(r"TEST-[A-Za-z0-9_.() -]{1,240}\.xml", path.name):
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
