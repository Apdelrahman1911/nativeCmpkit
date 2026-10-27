"""Read-only immutable Git and bounded report-ZIP review; no archived execution."""
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts/ci"))
import library_tests as lt

SHA = "23fd87aa3c52f89dde9a94d004821850a0459b5a"
RUN = 40440844416
run = json.loads((OUT / "run-final.json").read_text())
jobs = json.loads((OUT / "jobs-final.json").read_text())["jobs"]
artifacts = json.loads((OUT / "artifacts-final.json").read_text())["artifacts"]
assert run["id"] == RUN and run["head_sha"] == SHA
assert run["repository"]["full_name"] == "Apdelrahman1911/nativeCmpkit"
assert run["event"] == "workflow_dispatch" and run["head_branch"] == "development/preview-hardening"
assert run["status"] == "completed" and run["conclusion"] == "failure"
assert len(artifacts) == 1
artifact = artifacts[0]
assert artifact["id"] == 12706715057 and artifact["name"] == "library-evidence-android-device-api35"
payload = (OUT / "raw/12706715057.zip").read_bytes()
digest = "sha256:" + hashlib.sha256(payload).hexdigest()
assert len(payload) == artifact["size_in_bytes"] == 70471
assert digest == artifact["digest"] == "sha256:4ba9c67ab9f682c3e1a1e32ace29ba6dc0400780113666ff8be834917f1bba95"
assert not artifact["expired"]
assert json.loads((OUT / "dispatch-body.json").read_text()) == {
    "ref": "development/preview-hardening", "inputs": {"profile": "android-webview"},
}
dispatch = json.loads((OUT / "dispatch-receipt.json").read_text())
assert dispatch["expected_source_sha"] == SHA and dispatch["exit_code"] == 0
assert not dispatch["dispatch_retried"] and not dispatch["packages_releases_or_deployments_requested"]
assert dispatch["maximum_combined_runtime_slots"] == 2 and dispatch["existing_active_run_ids"] == []
for name in ["branch-before.json", "branch-after.json"]:
    assert json.loads((OUT / name).read_text())["object"]["sha"] == SHA
assert json.loads((OUT / "main-after.json").read_text())["object"]["sha"] == "94d2492e99d5cbc060409d94d9f88febd06222d5"
assert json.loads((OUT / "actions-permissions.json").read_text()) == {
    "enabled": True, "allowed_actions": "all", "sha_pinning_required": False,
}
assert json.loads((OUT / "workflow-permissions.json").read_text()) == {
    "default_workflow_permissions": "read", "can_approve_pull_request_reviews": False,
}
pages = json.loads((OUT / "pages.json").read_text())
assert pages["status"] is None and pages["build_type"] == "workflow"
assert next(j for j in jobs if j["id"] == 121980555929)["conclusion"] == "success"
job = next(j for j in jobs if j["id"] == 121980727565)
assert job["status"] == "completed" and job["conclusion"] == "failure"

records = {}
for row in subprocess.check_output(["git", "ls-tree", "-rz", SHA], cwd=ROOT).split(b"\0"):
    if row:
        metadata, name = row.split(b"\t", 1)
        records[name.decode()] = metadata.decode().split()

def blob(name):
    mode, kind, oid = records[name]
    assert kind == "blob" and mode in {"100644", "100755"}
    return subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT)

with tempfile.TemporaryDirectory(prefix="nativecmpkit-apk-failure-review-", dir="/dev/shm") as directory:
    view = Path(directory)
    def materialize(name):
        target = view / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob(name))

    materialize("settings.gradle.kts")
    for name in records:
        if name.startswith(("calf-", "sample/")) and name.endswith("/build.gradle.kts"):
            materialize(name)
    projects = lt.projects(view)
    prefixes = ["gradle/", "convention-plugins/", "scripts/ci/", "scripts/native/", "kotlin-js-store/"]
    prefixes += [f"{module}/{folder}/" for module in projects for folder in ["src", "native", ".cargo", "gradle"]]
    exact = set(lt.ROOT_INPUTS) | {f"{module}/{n}" for module in projects for n in ["build.gradle.kts", "gradle.properties", "gradle.lockfile"]}
    exact |= {n for n in records if n.startswith("sample/") and n.count("/") == 2 and n.endswith("/build.gradle.kts")}
    for name in records:
        if (name in exact or any(name.startswith(p) for p in prefixes)) and not set(PurePosixPath(name).parts[:-1]) & lt.IGNORED_INPUT_DIRS:
            materialize(name)
    inputs = lt.snapshot_inputs(view)
    assert len(inputs) == 704 and lt.input_digest(inputs) == "b120df04dfeb28c6e857ceee1b5ae20f5198251a7a87beec4fbd446583373c33"
    plan = lt.plan(view, "android-device", only_modules=("calf-webview",))
    assert len(plan["expected"]) == 1 and plan["expected"][0]["module"] == "calf-webview"
    assert not plan["complete_suite_requested"] and plan["test_bearing_modules_not_requested"] == ["calf-file-picker", "calf-io"]
    with zipfile.ZipFile(OUT / "raw/12706715057.zip") as archive:
        members = archive.infolist()
        names = [i.filename for i in members]
        assert len(names) == len(set(names)) == 9
        assert sum(i.file_size for i in members) <= 64 * 1024**2
        for item in members:
            path = PurePosixPath(item.filename)
            assert not path.is_absolute() and not set(path.parts) & {".", ".."} and "\\" not in item.filename
            assert not item.is_dir() and item.file_size <= lt.MAX_REPORT_BYTES
            assert ((item.external_attr >> 16) & 0o170000) != 0o120000
            assert item.filename.endswith(".json")
        def doc(name):
            return json.loads(archive.read(name))

        base = "build/ci-verification/android-device-api35/"
        controller = doc(base + "controller.json")
        runtime = doc(base + "runtime-host.json")
        device_plan = doc(base + "plan.json")
        diagnostics = doc(base + "failure-diagnostics.json")
        assert doc(base + "inputs-before.json") == doc(base + "inputs-after.json") == inputs
        assert controller["source_revision"] == controller["source_revision_after"] == SHA
        assert controller["source_unchanged"] and not controller["source_tree_dirty"] and not controller["changed_inputs"]
        assert not controller["passed"] and not controller["test_suite_passed"]
        assert not controller["complete_suite_requested"] and controller["explicit_module_subset"] == ["calf-webview"]
        assert controller["test_bearing_modules_not_requested"] == ["calf-file-picker", "calf-io"]
        assert set(controller["setup_stages"]) == {"apk-assembly"}
        assert controller["setup_stages"]["apk-assembly"]["exit_code"] == 1
        assert controller["controller_error"] == "RuntimeError" and "emulator_shutdown" not in controller
        assert "android_emulator" not in runtime and runtime["source_revision"] == SHA
        assert runtime["host"]["system"] == "Linux" and runtime["host"]["architecture"] == "x64"
        assert runtime["java"]["major"] == 17 and runtime["rust"]["release"] == "1.98.0"
        assert doc("build/ci-plan/plan.json") == device_plan["source_suite"] == plan
        command = lt.gradle_command("android-device", plan, android_serial="emulator-5588", root=view)
        assert device_plan["assembly_command"] == command[:-1] + [":calf-webview:assembleAndroidDeviceTest"]
        assert device_plan["source_revision"] == SHA and device_plan["serial"] == "emulator-5588"
        assert len(diagnostics["logs"]) == 1 and diagnostics["logs"][0]["name"] == "apk-assembly.log"
        assert diagnostics["logs"][0]["bytes"] == 35165
        assert diagnostics["logs"][0]["sha256"] == "30b296977803e829eb86066c1a2fb5f4af9e3534fc9366a242061888ac5a0a9b"
        assert diagnostics["logs"][0]["excerpts"] == [] and diagnostics["logs"][0]["tail"] == ""
        assert all(not i["exists"] and i["files"] == [] for i in diagnostics["android_result_file_inventories"])
        assert not controller["packages_published"] and not controller["release_readiness_certified"]

review = {
    "reviewed_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "run_id": RUN,
    "url": run["html_url"], "source_revision": SHA, "run_conclusion": "failure",
    "job_id": job["id"], "job_url": job["html_url"], "artifact_id": artifact["id"],
    "artifact_digest": digest, "artifact_members": names, "evidence_integrity_passed": True,
    "source_input_count": len(inputs), "source_inputs_sha256": lt.input_digest(inputs),
    "uploaded_xml_reports": 0, "library_testcases_reported": 0, "library_passed": False,
    "setup_stages": controller["setup_stages"], "runtime": runtime,
    "assembly_command": device_plan["assembly_command"],
    "scope": "Immutable finite WebView-only Android job fails APK assembly before owned AVD creation/launch and connected library execution. All704 Git inputs/plan/subset/report-only ZIP hashes agree. The APK diagnostic collector omitted assembly excerpts; separate bounded CI-console readback and actual same-source local compilation preserve the missing-click-extension error. No emulator/UI/history behavior is certified.",
    "limitations": ["The full hosted APK log was not uploaded; only its original hash and the separately inspected bounded CI-console cause line are retained.", "Runtime/metadata observations do not certify dependency trust or packaged consumers."],
    "issues_closed": 0, "packages_published": False, "release_created": False,
    "release_readiness_certified": False, "review_script_sha256": lt.sha256(Path(__file__)),
}
(OUT / "lead-independent-review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: review[k] for k in ["run_id", "source_revision", "evidence_integrity_passed", "uploaded_xml_reports", "library_passed"]}, indent=2))
