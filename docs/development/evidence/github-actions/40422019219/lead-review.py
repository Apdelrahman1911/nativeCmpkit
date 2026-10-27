"""Read-only recount of this exact failed Android workflow; never runs archived code.

Checks immutable Git bytes, bounded inert ZIP members, controller/runner receipts
and the absence of XML. Evidence integrity is not a successful test execution.
"""
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts/ci"))
import library_tests as lt

REVISION = "d849515b2a1f6048ed280e44e677f532a57d4f5f"
RUN = 40422019219
run = json.loads((OUT / "run-final.json").read_text())
jobs = json.loads((OUT / "jobs-final.json").read_text())["jobs"]
artifacts = json.loads((OUT / "artifacts-final.json").read_text())["artifacts"]
assert run["id"] == RUN and run["head_sha"] == REVISION
assert run["repository"]["full_name"] == "Apdelrahman1911/nativeCmpkit"
assert run["event"] == "workflow_dispatch" and run["head_branch"] == "development/preview-hardening"
assert run["status"] == "completed" and run["conclusion"] == "failure"
assert len(artifacts) == 1
artifact = artifacts[0]
assert artifact["id"] == 12699275781 and artifact["name"] == "library-evidence-android-device-api35"
payload = (OUT / "raw/12699275781.zip").read_bytes()
digest = "sha256:" + hashlib.sha256(payload).hexdigest()
assert len(payload) == artifact["size_in_bytes"] <= 64 * 1024 * 1024
assert artifact["digest"] == digest and not artifact["expired"]

records = {}
for row in subprocess.check_output(["git", "ls-tree", "-rz", REVISION], cwd=ROOT).split(b"\0"):
    if row:
        metadata, name = row.split(b"\t", 1)
        records[name.decode()] = metadata.decode().split()

def blob(name):
    mode, kind, oid = records[name]
    assert kind == "blob" and mode in ("100644", "100755")
    return subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT)

with tempfile.TemporaryDirectory(prefix="nativecmpkit-device-evidence-review-") as directory:
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
    prefixes += [f"{module}/{folder}/" for module in projects for folder in ("src", "native", ".cargo", "gradle")]
    exact = set(lt.ROOT_INPUTS) | {f"{module}/{n}" for module in projects for n in ("build.gradle.kts", "gradle.properties", "gradle.lockfile")}
    exact |= {n for n in records if n.startswith("sample/") and n.count("/") == 2 and n.endswith("/build.gradle.kts")}
    for name in records:
        if (name in exact or any(name.startswith(p) for p in prefixes)) and not set(PurePosixPath(name).parts[:-1]) & lt.IGNORED_INPUT_DIRS:
            materialize(name)
    inputs = lt.snapshot_inputs(view)
    # The failed revision incorrectly planned getResultsDir as XML. Preserve that
    # exact original contract; current runner's repaired plan has a different path.
    plan = lt.plan(view, "android-device")
    for item in plan["expected"]:
        item["report_directory"] = item["module"] + "/build/outputs/androidTest-results/connected/androidMain"

    with zipfile.ZipFile(OUT / "raw/12699275781.zip") as archive:
        members = archive.infolist()
        names = [i.filename for i in members]
        assert len(names) == len(set(names)) <= 2000
        assert sum(i.file_size for i in members) <= 64 * 1024 * 1024
        for item in members:
            path = PurePosixPath(item.filename)
            assert not path.is_absolute() and not set(path.parts) & {".", ".."} and "\\" not in item.filename
            assert not item.is_dir() and item.file_size <= lt.MAX_REPORT_BYTES
            assert ((item.external_attr >> 16) & 0o170000) != 0o120000
            assert item.filename.endswith((".json", ".xml"))
        def doc(name):
            return json.loads(archive.read(name))

        base = "build/ci-verification/android-device-api35/"
        controller = doc(base + "controller.json")
        receipt = doc(base + "library/receipt.json")
        runtime = doc(base + "library/runtime.json")
        for prefix in (base, base + "library/"):
            assert doc(prefix + "inputs-before.json") == doc(prefix + "inputs-after.json") == inputs
        assert receipt["inputs_before_sha256"] == receipt["inputs_after_sha256"] == lt.input_digest(inputs)
        for result in (controller, receipt):
            assert result["source_revision"] == result["source_revision_after"] == REVISION
            assert not result["source_tree_dirty"] and not result["changed_inputs"] and not result["passed"]
        assert controller["source_unchanged"] and not controller["test_suite_passed"]
        assert controller["setup_stages"]["apk-assembly"]["exit_code"] == 0
        assert controller["emulator_shutdown"]["exit_code"] == 0
        assert controller["emulator_shutdown"]["clean_shutdown"]
        assert controller["emulator_shutdown"]["graceful_kill_requested"]
        assert not controller["emulator_shutdown"]["forced_owned_group"]
        assert not controller["packages_published"] and not controller["release_readiness_certified"]
        assert doc("build/ci-plan/plan.json") == doc(base + "library/plan.json") == plan
        assert doc(base + "plan.json")["source_suite"] == plan
        assert receipt["command"] == lt.gradle_command("android-device", plan, android_serial="emulator-5588", root=view)
        assert receipt["execution"]["exit_code"] == 1
        assert receipt["runtime_receipt_sha256"] == hashlib.sha256(archive.read(base + "library/runtime.json")).hexdigest()
        assert runtime["source_revision"] == REVISION and not runtime["source_tree_dirty"]
        assert runtime["host"]["system"] == "Linux" and runtime["host"]["architecture"] == "x64"
        assert runtime["java"]["major"] == 17 and runtime["rust"]["release"] == "1.98.0"
        identity = runtime["android_emulator"]
        assert identity == receipt["android_emulator_after"]
        assert identity["serial"] == "emulator-5588" and identity["api_level"] == "35"
        assert identity["boot_completed"] == "1" and identity["selinux"] == "Enforcing"
        assert controller["test_totals"] == receipt["totals"]
        assert all(value == 0 for value in receipt["totals"].values())
        assert not any(n.endswith(".xml") for n in names)
        assert len(receipt["modules"]) == 3
        for module in receipt["modules"]:
            assert not module["reports"] and not module["testcases"]
            assert receipt["task_execution_markers"][module["task"]] == 0
            errors = [e["error"] for e in receipt["errors"] if e["module"] == module["module"]]
            assert errors == ["Expected exactly one fresh task execution marker", "No actual non-skipped library testcases"]
        job = next(j for j in jobs if j["id"] == 121918693849)
        assert job["status"] == "completed" and job["conclusion"] == "failure"
        assert next(j for j in jobs if j["id"] == 121918501026)["conclusion"] == "success"

review = {
    "reviewed_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "run_id": RUN,
    "url": run["html_url"], "source_revision": REVISION, "run_conclusion": "failure",
    "job_id": job["id"], "job_url": job["html_url"], "artifact_id": artifact["id"],
    "artifact_digest": digest, "artifact_members": names, "evidence_integrity_passed": True,
    "source_input_count": len(inputs), "source_inputs_sha256": lt.input_digest(inputs),
    "tests_executed": 0, "xml_reports": 0, "library_passed": False,
    "setup_stages": controller["setup_stages"], "emulator_shutdown": controller["emulator_shutdown"],
    "runtime": runtime, "command": receipt["command"], "execution": receipt["execution"],
    "missing_modules": [m["module"] for m in receipt["modules"]],
    "scope": "Actual owned emulator boot and clean shutdown, APK assembly; zero native library tests after report-path guard failure.",
    "issues_closed": 0, "packages_published": False, "release_created": False,
    "release_readiness_certified": False, "review_script_sha256": lt.sha256(Path(__file__)),
}
(OUT / "lead-independent-review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: review[k] for k in ("run_id", "source_revision", "evidence_integrity_passed", "tests_executed", "xml_reports", "library_passed")}, indent=2))
