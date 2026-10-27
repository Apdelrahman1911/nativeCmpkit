"""Read-only immutable-source/ZIP/XML recount, never executes archived payloads.

Evidence integrity can pass while the real Android library suite remains failed.
"""
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts/ci"))
import library_tests as lt

REVISION = "e259798e1bfdcacc0e6dd97bd85fb91f70de1726"
RUN = 40444608544
run = json.loads((OUT / "run-final.json").read_text())
jobs = json.loads((OUT / "jobs-final.json").read_text())["jobs"]
artifacts = json.loads((OUT / "artifacts-final.json").read_text())["artifacts"]
assert run["id"] == RUN and run["head_sha"] == REVISION
assert run["repository"]["full_name"] == "Apdelrahman1911/nativeCmpkit"
assert run["event"] == "workflow_dispatch" and run["head_branch"] == "development/preview-hardening"
assert run["status"] == "completed" and run["conclusion"] == "failure"
assert len(artifacts) == 1
artifact = artifacts[0]
assert artifact["id"] == 12708166286 and artifact["name"] == "library-evidence-android-device-api35"
payload = (OUT / "raw/12708166286.zip").read_bytes()
digest = "sha256:" + hashlib.sha256(payload).hexdigest()
assert len(payload) == artifact["size_in_bytes"] <= 64 * 1024 * 1024
assert digest == artifact["digest"] == "sha256:fef2c3025fe52cdbb76efe27bd42f478d2448b3c4d3403d30f059647355f78df"
assert not artifact["expired"]
assert json.loads((OUT / "dispatch-body.json").read_text()) == {
    "ref": "development/preview-hardening", "inputs": {"profile": "android-webview"},
}
dispatch = json.loads((OUT / "dispatch-receipt.json").read_text())
assert dispatch["expected_source_sha"] == REVISION and dispatch["exit_code"] == 0
assert not dispatch["dispatch_retried"] and not dispatch["packages_releases_or_deployments_requested"]
assert dispatch["maximum_combined_runtime_slots"] == 2 and dispatch["existing_active_run_ids"] == []
for name in ("branch-before.json", "branch-after.json"):
    assert json.loads((OUT / name).read_text())["object"]["sha"] == REVISION
assert json.loads((OUT / "main-after.json").read_text())["object"]["sha"] == "94d2492e99d5cbc060409d94d9f88febd06222d5"
assert json.loads((OUT / "actions-permissions.json").read_text()) == {
    "enabled": True, "allowed_actions": "all", "sha_pinning_required": False,
}
assert json.loads((OUT / "workflow-permissions.json").read_text()) == {
    "default_workflow_permissions": "read", "can_approve_pull_request_reviews": False,
}
pages = json.loads((OUT / "pages.json").read_text())
assert pages["status"] is None and pages["build_type"] == "workflow"

records = {}
for row in subprocess.check_output(["git", "ls-tree", "-rz", REVISION], cwd=ROOT).split(b"\0"):
    if row:
        metadata, name = row.split(b"\t", 1)
        records[name.decode()] = metadata.decode().split()

def blob(name):
    mode, kind, oid = records[name]
    assert kind == "blob" and mode in ("100644", "100755")
    return subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT)

with tempfile.TemporaryDirectory(prefix="nativecmpkit-device-xml-review-", dir="/dev/shm") as directory:
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
    assert len(inputs) == 705 and lt.input_digest(inputs) == "d23acb010140abf77ae250523f16f8500a957c3a03434bf31839babfa2da40b5"
    assert b"build/outputs/androidTest-results/connected/androidMain" in blob("scripts/ci/library_tests.py")
    assert b"build/intermediates/android_test_results/androidMain/{task_name}" in blob("scripts/ci/library_tests.py")
    plan = lt.plan(view, "android-device", only_modules=("calf-webview",))

    with zipfile.ZipFile(OUT / "raw/12708166286.zip") as archive:
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
        assert controller["emulator_shutdown"]["clean_shutdown"] and controller["emulator_shutdown"]["graceful_kill_requested"]
        assert not controller["emulator_shutdown"]["forced_owned_group"]
        assert not controller["packages_published"] and not controller["release_readiness_certified"]
        assert doc("build/ci-plan/plan.json") == doc(base + "library/plan.json") == plan
        assert doc(base + "plan.json")["source_suite"] == plan
        assert receipt["command"] == lt.gradle_command("android-device", plan, android_serial="emulator-5588", root=view)
        assert receipt["android_device_selection"] == {"mechanism": "ANDROID_SERIAL", "serial": "emulator-5588", "agp_target_serial_options": "empty"}
        assert receipt["execution"]["exit_code"] == 1 and not receipt["execution"].get("stop_reason")
        assert receipt["quarantined_prior_reports"] == []
        assert receipt["runtime_receipt_sha256"] == hashlib.sha256(archive.read(base + "library/runtime.json")).hexdigest()
        assert runtime["source_revision"] == REVISION and not runtime["source_tree_dirty"]
        assert runtime["host"]["system"] == "Linux" and runtime["host"]["architecture"] == "x64"
        assert runtime["java"]["major"] == 17 and runtime["rust"]["release"] == "1.98.0"
        identity = runtime["android_emulator"]
        assert identity == receipt["android_emulator_after"]
        assert identity["serial"] == "emulator-5588" and identity["api_level"] == "35" and identity["abi"] == "x86_64"
        assert identity["boot_completed"] == "1" and identity["selinux"] == "Enforcing"
        assert len(receipt["modules"]) == 1
        module_reviews, failures, all_xml = [], [], []
        for expected in plan["expected"]:
            module = next(m for m in receipt["modules"] if m["module"] == expected["module"])
            assert module["task"] == expected["task"] and receipt["task_execution_markers"][module["task"]] == 1
            xml_names = [n for n in names if n.startswith(expected["report_directory"] + "/") and PurePosixPath(n).name.startswith("TEST-") and n.endswith(".xml")]
            assert len(xml_names) == 1 and set(xml_names) == {r["path"] for r in module["reports"]}
            cases = []
            for name in xml_names:
                data = archive.read(name)
                parsed = lt.junit_cases(data)
                recorded = next(r for r in module["reports"] if r["path"] == name)
                assert recorded["sha256"] == hashlib.sha256(data).hexdigest()
                counts = lt.case_counts(parsed)
                assert all(recorded[k] == v for k, v in counts.items())
                document = ET.fromstring(data, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
                timestamp = dt.datetime.fromisoformat(document.attrib["timestamp"]).replace(tzinfo=dt.timezone.utc)
                assert dt.datetime.fromisoformat(receipt["started_at_utc"]) <= timestamp <= dt.datetime.fromisoformat(receipt["finished_at_utc"])
                for case in document.iter("testcase"):
                    for outcome in case:
                        if outcome.tag not in {"failure", "error"}:
                            continue
                        body = outcome.text or ""
                        assert len(body.encode()) <= 8192
                        failures.append({"module": module["module"], "classname": case.attrib["classname"], "name": case.attrib["name"], "outcome": outcome.tag, "body": body})
                cases += parsed
                all_xml.append(name)
            assert cases == module["testcases"] and len(cases) == len({(c["classname"], c["name"]) for c in cases})
            counts = lt.case_counts(cases)
            assert all(module[k] == v for k, v in counts.items())
            assert not module["native_scenarios"]
            module_reviews.append({"module": module["module"], "task": module["task"], "reports": module["reports"], **counts})
        assert set(all_xml) == {n for n in names if n.endswith(".xml")}
        totals = {k: sum(m[k] for m in module_reviews) for k in receipt["totals"]}
        assert totals == receipt["totals"] == controller["test_totals"]
        assert totals == {"tests": 25, "passed": 24, "executed": 25, "failures": 1, "errors": 0, "skipped": 0, "not_applicable": 0, "unexpected_skipped": 0}
        assert Counter((f["module"], f["name"]) for f in failures) == Counter({
            ("calf-webview", "navigatorReplacementReadsRealBrowserHistoryWithoutAnotherPageEvent"): 1,
        })
        assert "backward/forward history precondition timed out" in failures[0]["body"]
        assert "url=https://nativecmpkit.invalid/fixture, back=true, forward=true, index=1, size=3" in failures[0]["body"]
        assert "AndroidWebViewHistoryDeviceTest.kt:80" in failures[0]["body"]
        assert "ComposeTimeoutException" in failures[0]["body"]
        assert len(receipt["errors"]) == 1 and receipt["errors"][0]["error"] == "Failed, errored or unexpected skipped tests are not accepted by this verification gate"
        source = blob("calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidWebViewHistoryDeviceTest.kt").decode()
        assert source.index('assertEquals("true"') < source.index('native.goBack()') < source.index('val replacement =')
        assert 'window.fixtureActivated === true && window.fixtureClicks === 1 && location.hash ===' in source
        assert 'native.url?.endsWith("#first") == true' in source
        job = next(j for j in jobs if j["id"] == 121992956280)
        assert job["status"] == "completed" and job["conclusion"] == "failure"
        assert next(j for j in jobs if j["id"] == 121992785634)["conclusion"] == "success"

review = {
    "reviewed_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "run_id": RUN,
    "url": run["html_url"], "source_revision": REVISION, "run_conclusion": "failure",
    "job_id": job["id"], "job_url": job["html_url"], "artifact_id": artifact["id"],
    "artifact_digest": digest, "artifact_members": names, "evidence_integrity_passed": True,
    "source_input_count": len(inputs), "source_inputs_sha256": lt.input_digest(inputs),
    "uploaded_xml_reports": len(all_xml), "totals": totals, "modules": module_reviews,
    "failures": failures, "library_passed": False,
    "setup_stages": controller["setup_stages"], "emulator_shutdown": controller["emulator_shutdown"],
    "runtime": runtime, "command": receipt["command"], "execution": receipt["execution"],
    "scope": "25 fresh actual WebView executions on the owned Enforcing API35/x86_64 emulator:24pass/1fail. Real touch, active user activation, DOM click count1 and JS #second assertions precede goBack and passed. The native backward/forward capabilities and index1/size3 were observed, but native.url remained the inline base URL so the #first native-URL predicate timed out before navigator replacement. Inline URL semantics and the earlier script-activation hypothesis are not proven production causes. No issue closure, native-feature/ABI/consumer or release success inferred.",
    "issues_closed": 0, "packages_published": False, "release_created": False,
    "release_readiness_certified": False, "review_script_sha256": lt.sha256(Path(__file__)),
}
(OUT / "lead-independent-review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: review[k] for k in ("run_id", "source_revision", "evidence_integrity_passed", "totals", "uploaded_xml_reports", "library_passed")}, indent=2))
