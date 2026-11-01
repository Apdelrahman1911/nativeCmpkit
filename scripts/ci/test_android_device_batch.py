"""Finite route/source and injected receipt models; no SDK, Gradle or native work."""
from collections import Counter
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import android_device_batch as batch
import android_device_batch_plan as fixed
import library_tests as lt
import workflow_matrix as workflow

ROOT = Path(__file__).resolve().parents[2]
REVISION = "1" * 40
INPUTS = {"synthetic-source-input": "2" * 64}


class AndroidDeviceBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plans = {name: batch.plan(ROOT, name) for name in (
            "android-io-permission-storage-api35", "android-permission-storage-compatibility")}

    def test_exact_twelve_routes_and_sixteen_target_executions_thirteen_original_methods(self):
        expected = {
            "android-io-reference-regressions", "android-permission-demo",
            "android-storage-api35-normal", "android-storage-api35-all-files",
            "android-media-selection-api33", "android-media-selection-api34",
            "android-storage-api28", "android-storage-api29-target28",
            "android-storage-api29-legacy", "android-storage-api29-scoped",
            "android-storage-api30-normal", "android-storage-api30-all-files",
        }
        routes = [route for plan in self.plans.values() for route in plan["routes"]]
        self.assertEqual(expected, {route["profile"] for route in routes})
        self.assertEqual(12, len(routes))
        self.assertEqual([4, 8], [len(plan["routes"]) for plan in self.plans.values()])
        self.assertEqual(16, sum(plan["requested_target_executions"] for plan in self.plans.values()))
        identities = [(case["classname"], case["name"]) for route in routes
            for case in route["source_suite"]["expected"][0]["required_testcases"]]
        self.assertEqual(13, len(set(identities)))
        self.assertEqual([1] * 10 + [2] * 3, sorted(Counter(identities).values()))
        for route in routes:
            original, = workflow.matrix(route["profile"])["include"]
            self.assertEqual(route["api_level"], int(original["emulator-api"]))
            self.assertEqual(route["module"], original["test-modules"])
            self.assertEqual(route["focus"], original["test-focus"])
            self.assertEqual(lt.plan(ROOT, "android-device", only_modules=(route["module"],),
                focus=route["focus"]), route["source_suite"])

    def test_original_profiles_and_all_eleven_complete_slots_are_preserved(self):
        self.assertEqual(11, len(workflow.matrix("all")["include"]))
        for name, modules in fixed.MODULES.items():
            row, = workflow.matrix(name)["include"]
            self.assertEqual("android-device", row["suite"])
            self.assertEqual("ubuntu-24.04", row["runner"])
            self.assertEqual("x64", row["arch"])
            self.assertEqual(name, row["android-batch"])
            self.assertEqual(modules, row["test-modules"])
            self.assertNotIn("emulator-api", row)
            self.assertNotIn("test-focus", row)

    def test_readonly_real_batch_cli_plans_never_create_outputs_or_run_native_work(self):
        output = ROOT / "build"
        before = sorted(output.rglob("*")) if output.exists() else []
        for name in self.plans:
            result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/ci/android_device_batch.py"),
                "plan", "--batch", name], cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stderr)
            document = json.loads(result.stdout)
            self.assertEqual(self.plans[name], document)
            self.assertIs(document["source_only"], True)
            self.assertEqual(0, document["native_tests_executed"])
            self.assertEqual(0, document["Gradle_builds_executed"])
            receipt = workflow.preflight_plans(name, root=ROOT)
            self.assertEqual(1, len(receipt["slots"]))
            self.assertIn("android_device_batch.py", receipt["slots"][0]["command"][2])
        self.assertEqual(before, sorted(output.rglob("*")) if output.exists() else [])

    def test_invalid_batch_or_route_expansion_is_refused_before_process_launch(self):
        for name in ("", "all", "android-device", "self-hosted", "$(env)", "api35;true"):
            with self.subTest(name=name), self.assertRaises(ValueError), patch.object(lt, "execute") as execute:
                batch.plan(ROOT, name)
            execute.assert_not_called()
        name = next(iter(fixed.BATCHES))
        original = workflow.matrix
        for change in ({"test-modules": "calf-io,calf-webview"}, {"emulator-api": "23"},
                       {"runner": "self-hosted"}, {"serial-emulator-api": "23"},
                       {"test-focus": "android-io-default-decode"}):
            def changed(profile):
                value = original(profile)
                if profile == fixed.BATCHES[name][0]:
                    value["include"][0].update(change)
                return value
            with self.subTest(change=change), patch.object(workflow, "matrix", side_effect=changed), self.assertRaises(ValueError):
                batch.plan(ROOT, name)

    def synthetic_route(self, root, relative, route, *, failed=False, bad_cleanup=None,
                        bad_xml=None, no_library=False):
        output = root / relative
        output.mkdir(parents=True)
        (output / "avd").mkdir()
        (output / "android-user").mkdir()
        (output / "android-user/debug.keystore").write_text("inert synthetic signer placeholder; never a real key")
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        controller = {"source_revision": REVISION, "source_revision_after": REVISION,
            "source_tree_dirty": False, "source_unchanged": True, "changed_inputs": [],
            "explicit_test_focus": route["focus"], "test_suite_passed": not failed,
            "passed": not failed, "emulator_shutdown": {"clean_shutdown": True,
                "owned_adb_transport_removed": True, "exit_code": 0,
                "graceful_kill_requested": True, "forced_owned_group": False}}
        for key, directory in batch.HELPERS.items():
            if key in route["source_suite"]:
                contract = route["source_suite"][key]
                helper = {"package": contract["package"], "source_fixture": contract["source_fixture"],
                    "verification_api_level": route["api_level"], "cleanup_status": "passed",
                    "owned_recipient_removed": True}
                if key == "android_storage_probe":
                    helper["profile"] = route["profile"]
                controller[key.removeprefix("android_")] = helper
                folder = output / directory
                folder.mkdir()
                (folder / "receipt.json").write_text(json.dumps(helper))
        plan = {"source_revision": REVISION, "api_level": route["api_level"],
            "serial": "emulator-5588", "avd_name": f"nativecmpkit-api{route['api_level']}-" + hashlib.sha256(relative.encode()).hexdigest()[:12],
            "source_suite": route["source_suite"]}
        (output / "plan.json").write_text(json.dumps(plan))
        if bad_cleanup == "transport":
            controller["emulator_shutdown"]["owned_adb_transport_removed"] = False
        elif bad_cleanup == "helper":
            controller[next(key.removeprefix("android_") for key in batch.HELPERS if key in route["source_suite"])]["cleanup_status"] = "failed"
        elif bad_cleanup == "source":
            controller["source_unchanged"] = False
        elif bad_cleanup == "shutdown":
            controller["emulator_shutdown"]["forced_owned_group"] = True
        elif bad_cleanup == "local":
            foreign = root / "foreign-avd"
            foreign.mkdir()
            (foreign / "retained.txt").write_text("synthetic foreign data")
            (output / "avd").rmdir()
            (output / "avd").symlink_to(foreign, target_is_directory=True)
        if not no_library:
            expected, = route["source_suite"]["expected"]
            xml = ET.Element("testsuite")
            for index, case in enumerate(expected["required_testcases"]):
                child = ET.SubElement(xml, "testcase", {"classname": case["classname"], "name": case["name"]})
                if failed and index == 0:
                    ET.SubElement(child, "failure", {"message": "synthetic model failure"})
            body = ET.tostring(xml)
            cases = lt.junit_cases(body)
            totals = lt.case_counts(cases)
            path = root / expected["report_directory"] / "TEST-synthetic.xml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            controller["test_totals"] = totals
            receipt = {"source_revision": REVISION, "source_revision_after": REVISION,
                "source_tree_dirty": False, "changed_inputs": [], "suite": "android-device",
                "explicit_test_focus": route["focus"], "required_focused_testcases": expected["required_testcases"],
                "inputs_before_sha256": lt.input_digest(INPUTS), "inputs_after_sha256": lt.input_digest(INPUTS),
                "started_at_utc": now, "finished_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "execution": {"exit_code": 1 if failed else 0}, "passed": not failed,
                "task_execution_markers": {expected["task"]: 1}, "totals": totals,
                "modules": [{"module": route["module"], "task": expected["task"], **totals,
                    "reports": [{"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(body).hexdigest(), **totals}],
                    "testcases": cases}]}
            if bad_xml == "hash":
                receipt["modules"][0]["reports"][0]["sha256"] = "0" * 64
            elif bad_xml == "stale":
                receipt["started_at_utc"] = "2027-01-01T00:00:00+00:00"
                receipt["finished_at_utc"] = "2027-01-01T00:00:01+00:00"
            elif bad_xml == "marker":
                receipt["task_execution_markers"][expected["task"]] = 0
            elif bad_xml == "foreign":
                receipt["modules"][0]["reports"][0]["path"] = "build/old/TEST-synthetic.xml"
            library = output / "library"
            library.mkdir()
            for filename, value in (("receipt.json", receipt), ("plan.json", route["source_suite"]),
                ("inputs-before.json", INPUTS), ("inputs-after.json", INPUTS)):
                (library / filename).write_text(json.dumps(value))
        else:
            controller.update(passed=False, test_suite_passed=False, controller_error="ValueError")
        (output / "controller.json").write_text(json.dumps(controller))

    def modeled_run(self, *, bad_cleanup=None, bad_xml=None, failed=False, no_library=False):
        name = next(iter(fixed.BATCHES))
        selection = self.plans[name]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            events = []
            def execute(_, command, log, timeout, reserve_mib):
                route = selection["routes"][len(events)]
                relative = command[command.index("--output") + 1]
                if events:
                    previous = root / events[-1]["relative"]
                    self.assertTrue((previous / "fresh-reports.json").is_file())
                    self.assertFalse((previous / "avd").exists())
                    self.assertFalse((previous / "android-user").exists())
                    if not no_library:
                        self.assertEqual(1, len(list((previous / "fresh-reports").glob("*.xml"))))
                self.assertEqual(str(root / "scripts/ci/android_device_tests.py"), command[2])
                self.assertEqual(["-B", "run"], [command[1], command[3]])
                self.assertEqual("8192", str(reserve_mib))
                self.synthetic_route(root, relative, route, failed=failed and not events,
                    bad_cleanup=bad_cleanup if not events else None, bad_xml=bad_xml if not events else None,
                    no_library=no_library and not events)
                events.append({"profile": route["profile"], "relative": relative})
                return {"exit_code": 1 if not events[:-1] and (failed or no_library) else 0, "elapsed_seconds": 0.01}
            with patch.object(batch, "plan", return_value=copy.deepcopy(selection)), patch.object(batch, "control_inputs", return_value={"synthetic-workflow": "3" * 64}), \
                    patch.object(lt, "snapshot_inputs", return_value=INPUTS), \
                    patch.object(lt, "git_revision", return_value=REVISION), patch.object(lt, "execute", side_effect=execute):
                result = batch.run(root, name, "build/ci-verification/synthetic-batch")
            return result, events

    def test_independent_routes_continue_after_test_failure_with_certified_cleanup_and_sticky_red(self):
        result, events = self.modeled_run(failed=True)
        self.assertEqual(list(next(iter(fixed.BATCHES.values()))), [event["profile"] for event in events])
        self.assertIs(result["passed"], False)
        self.assertIs(result["routes"][0]["passed"], False)
        self.assertTrue(all(route["passed"] for route in result["routes"][1:]))
        self.assertEqual(8, result["actual_target_executions"])
        self.assertEqual(1, result["routes"][0]["archive"]["actual_totals"]["failures"])

    def test_uncertified_cleanup_refuses_all_remaining_routes_without_erasing_first_receipt(self):
        for cause in ("transport", "helper", "source", "shutdown"):
            with self.subTest(cause=cause):
                result, events = self.modeled_run(bad_cleanup=cause)
                self.assertEqual(1, len(events))
                self.assertFalse(result["passed"])
                self.assertEqual(3, len(result["refused_profiles"]))
                self.assertFalse(result["routes"][0]["cleanup_certified"])
                self.assertTrue(result["routes"][0]["controller_sha256"])

    def test_stale_foreign_bad_hash_or_missing_fresh_task_xml_cannot_be_reused_or_hidden_by_next_route(self):
        for cause in ("hash", "stale", "marker", "foreign"):
            with self.subTest(cause=cause):
                result, events = self.modeled_run(bad_xml=cause)
                self.assertEqual(1, len(events))
                self.assertFalse(result["passed"])
                self.assertEqual(3, len(result["refused_profiles"]))
                self.assertIn("archive_error", result["routes"][0])

    def test_certified_early_setup_failure_keeps_zero_native_count_and_independent_routes_can_continue(self):
        result, events = self.modeled_run(no_library=True)
        self.assertEqual(4, len(events))
        self.assertFalse(result["passed"])
        self.assertEqual(5, result["actual_target_executions"])
        self.assertEqual(0, result["routes"][0]["archive"]["actual_totals"]["executed"])
        self.assertFalse(result["original_XML_execution_count_complete"])

    def test_all_success_model_requires_every_exact_route_and_original_archives(self):
        result, events = self.modeled_run()
        self.assertTrue(result["passed"])
        self.assertEqual(4, len(events))
        self.assertEqual(8, result["actual_target_executions"])
        self.assertEqual(8, result["actual_distinct_methods"])
        self.assertFalse(result["native_acceptance_or_issue_closure_inferred"])

    def test_failed_owned_local_state_reclamation_retains_original_result_and_refuses_remaining_routes(self):
        result, events = self.modeled_run(bad_cleanup="local")
        self.assertEqual(1, len(events))
        self.assertFalse(result["passed"])
        self.assertTrue(result["routes"][0]["cleanup_certified"])
        self.assertEqual("failed", result["routes"][0]["local_state_cleanup"]["status"])
        self.assertEqual(3, len(result["refused_profiles"]))
        self.assertTrue(result["routes"][0]["archive"]["original_result_preserved"])

    def test_reclamation_never_deletes_evidence_compilation_caches_or_foreign_private_trees(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route = next(iter(self.plans.values()))["routes"][0]
            relative = "build/ci-verification/own/routes/" + route["profile"]
            self.synthetic_route(root, relative, route)
            output = root / relative
            for name in ("avd", "android-user", "fresh-reports", "library"):
                (output / name).mkdir(parents=True, exist_ok=True)
                (output / name / "retained.txt").write_text("inert owned model data")
            (output / "fresh-reports.json").write_text(json.dumps({"original_result_preserved": True}))
            lock = root / "build/ci-verification/.android-device-batch.lock"
            lock.write_text(str(__import__("os").getpid()) + "\n")
            foreign = root / "unrelated/android-user"
            foreign.mkdir(parents=True)
            (foreign / "retained.txt").write_text("synthetic foreign data")
            cached = root / "calf-permissions/core/build/compiled.txt"
            cached.parent.mkdir(parents=True)
            cached.write_text("synthetic unchanged compilation")
            result = batch.reclaim_owned_state(root, relative, route, REVISION)
            self.assertEqual("passed", result["status"])
            self.assertEqual(["avd", "android-user"], result["removed_directories"])
            for path in (foreign / "retained.txt", cached, output / "fresh-reports/retained.txt",
                         output / "library/retained.txt", output / "fresh-reports.json"):
                self.assertTrue(path.is_file(), str(path))

    def test_existing_output_or_foreign_batch_lock_is_refused_without_mutation(self):
        name = next(iter(fixed.BATCHES))
        with tempfile.TemporaryDirectory() as folder, patch.object(batch, "plan", return_value=self.plans[name]):
            root = Path(folder)
            base = root / "build/ci-verification"
            base.mkdir(parents=True)
            for relative in ("build/ci-verification", "build/ci-verification/existing"):
                (root / relative).mkdir(exist_ok=True)
                with self.subTest(relative=relative), self.assertRaises(ValueError), patch.object(lt, "execute") as execute:
                    batch.run(root, name, relative)
                execute.assert_not_called()
            lock = base / ".android-device-batch.lock"
            lock.write_text("synthetic foreign owner\n")
            with self.assertRaises(FileExistsError), patch.object(lt, "execute") as execute:
                batch.run(root, name, "build/ci-verification/new")
            self.assertEqual("synthetic foreign owner\n", lock.read_text())
            execute.assert_not_called()

    def generated_agp_archive_model(self, root, route, *, report_name=None, failed=False):
        """Synthetic bytes only; model the native AGP filename, never recover actual XML."""
        relative = "build/ci-verification/generated/routes/" + route["profile"]
        self.synthetic_route(root, relative, route, failed=failed)
        output = root / relative
        plan = json.loads((output / "plan.json").read_text())
        release = {28: "9", 29: "10", 30: "11", 33: "13", 34: "14", 35: "15"}[route["api_level"]]
        boot = {"api_level": str(route["api_level"]), "serial": plan["serial"],
            "boot_completed": "1", "selinux": "Enforcing", "release": release}
        (output / "boot.json").write_text(json.dumps(boot))
        receipt_path = output / "library/receipt.json"
        receipt = json.loads(receipt_path.read_text())
        row, = receipt["modules"][0]["reports"]
        original = root / row["path"]
        body = original.read_bytes()
        name = report_name or f"TEST-{plan['avd_name']}(AVD) - {release}.xml"
        report = original.with_name(name)
        original.rename(report)
        row["path"] = report.relative_to(root).as_posix()
        receipt_path.write_text(json.dumps(receipt))
        return relative, report, body, receipt, json.loads((output / "controller.json").read_text())

    def test_generated_owned_agp_names_archive_exact_synthetic_bytes_for_all_fixed_routes(self):
        for route in (route for selection in self.plans.values() for route in selection["routes"]):
            with self.subTest(profile=route["profile"]), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                relative, report, body, receipt, controller = self.generated_agp_archive_model(root, route)
                with patch.object(lt, "snapshot_inputs", return_value=INPUTS):
                    result = batch.archive_route(root, relative, route, INPUTS, REVISION, controller)
                archived, = result["original_reports"]
                self.assertEqual(report.relative_to(root).as_posix(), archived["original_path"])
                self.assertEqual(body, report.read_bytes())
                self.assertEqual(body, (root / archived["archived_path"]).read_bytes())
                self.assertEqual(hashlib.sha256(body).hexdigest(), archived["sha256"])
                self.assertEqual(receipt["totals"], result["actual_totals"])
                self.assertTrue(result["original_XML_execution_count_complete"])
                self.assertFalse(result["native_success_inferred_from_archival"])

    def test_generated_agp_name_spoofing_is_not_a_broad_parenthesis_or_space_exception(self):
        route = next(iter(self.plans.values()))["routes"][0]
        names = ("TEST-foreign(AVD) - 15.xml", "TEST-nativecmpkit-api35-000000000000(AVD) - 15.xml",
            "TEST-nativecmpkit-api35-.*(AVD) - 15.xml", "TEST-owned(AVD) - 15.xml",
            "TEST-owned(AVD) - 15.xml.extra", "TEST-owned(AVD) - 15\n.xml",
            "TEST-owned (AVD) - 15.xml", "TEST-owned(AVD)  - 15.xml")
        for name in names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                relative, _, _, _, controller = self.generated_agp_archive_model(root, route, report_name=name)
                with patch.object(lt, "snapshot_inputs", return_value=INPUTS), self.assertRaises(ValueError):
                    batch.archive_route(root, relative, route, INPUTS, REVISION, controller)
                self.assertFalse((root / relative / "fresh-reports").exists())

    def test_generated_agp_names_require_exact_owned_plan_and_actual_boot_identity(self):
        route = next(iter(self.plans.values()))["routes"][0]
        changes = (("plan.json", "source_revision", "0" * 40), ("plan.json", "api_level", "35"),
            ("plan.json", "api_level", True), ("plan.json", "serial", "emulator-5590"),
            ("plan.json", "avd_name", "nativecmpkit-api35-000000000000"),
            ("plan.json", "avd_name", "nativecmpkit-api35-.*"), ("plan.json", "avd_name", None),
            ("boot.json", "api_level", "34"), ("boot.json", "serial", "emulator-5590"),
            ("boot.json", "boot_completed", "0"), ("boot.json", "selinux", "Permissive"),
            ("boot.json", "release", "14"), ("boot.json", "release", "15.*"),
            ("boot.json", "release", "15/../15"), ("boot.json", "release", None))
        for filename, key, value in changes:
            with self.subTest(filename=filename, key=key, value=value), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                relative, _, _, _, controller = self.generated_agp_archive_model(root, route)
                path = root / relative / filename
                document = json.loads(path.read_text())
                document[key] = value
                path.write_text(json.dumps(document))
                with patch.object(lt, "snapshot_inputs", return_value=INPUTS), self.assertRaises(ValueError):
                    batch.archive_route(root, relative, route, INPUTS, REVISION, controller)
                self.assertFalse((root / relative / "fresh-reports").exists())

    def test_generated_agp_spelling_preserves_hash_freshness_confinement_and_failed_outcomes(self):
        route = next(iter(self.plans.values()))["routes"][0]
        for cause in ("hash", "stale", "marker", "foreign", "symlink", "hardlink", "changed-input", "failed"):
            with self.subTest(cause=cause), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                relative, report, body, receipt, controller = self.generated_agp_archive_model(root, route, failed=cause == "failed")
                row, = receipt["modules"][0]["reports"]
                if cause == "hash":
                    row["sha256"] = "0" * 64
                elif cause == "stale":
                    receipt["started_at_utc"] = "2027-01-01T00:00:00+00:00"
                    receipt["finished_at_utc"] = "2027-01-01T00:00:01+00:00"
                elif cause == "marker":
                    receipt["task_execution_markers"][route["source_suite"]["expected"][0]["task"]] = 0
                elif cause == "foreign":
                    row["path"] = "build/old/" + report.name
                elif cause == "symlink":
                    original = report.with_name("retained-original.xml")
                    report.rename(original)
                    report.symlink_to(original)
                elif cause == "hardlink":
                    __import__("os").link(report, report.with_name("shared-original.xml"))
                elif cause == "changed-input":
                    receipt["changed_inputs"] = ["synthetic-source-input"]
                (root / relative / "library/receipt.json").write_text(json.dumps(receipt))
                with patch.object(lt, "snapshot_inputs", return_value=INPUTS):
                    if cause != "failed":
                        with self.assertRaises(ValueError):
                            batch.archive_route(root, relative, route, INPUTS, REVISION, controller)
                        self.assertFalse((root / relative / "fresh-reports").exists())
                    else:
                        result = batch.archive_route(root, relative, route, INPUTS, REVISION, controller)
                        self.assertEqual(1, result["actual_totals"]["failures"])
                        self.assertTrue(result["original_result_preserved"])
                        self.assertFalse(result["native_success_inferred_from_archival"])
                        self.assertEqual(body, (root / result["original_reports"][0]["archived_path"]).read_bytes())


    def test_failed_child_origin_is_retained_before_missing_controller_without_laundering_failure(self):
        selection = next(iter(self.plans.values()))
        name = selection["batch"]
        marker = "NATIVECMPKIT_ANDROID_PREFLIGHT_ORIGIN "
        origin = {"source": "android_device_tests.py", "symbol": "validate_api_selection",
            "line": batch.device.validate_api_selection.__code__.co_firstlineno}
        for exit_code in (2, 0, True, None):
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                public_source = root / "scripts/ci/android_device_tests.py"
                public_source.parent.mkdir(parents=True)
                public_source.write_bytes((ROOT / "scripts/ci/android_device_tests.py").read_bytes())
                events = []
                def execute(_, command, log, timeout, reserve_mib):
                    events.append(command)
                    log.write_text("PRIVATE_CHILD_BODY /private/path NEVER EXPORT\n" + marker + json.dumps(origin) + "\n")
                    return {"exit_code": exit_code, "elapsed_seconds": 0.01}
                with patch.object(batch, "plan", return_value=copy.deepcopy(selection)), \
                        patch.object(batch, "control_inputs", return_value={"synthetic-workflow": "3" * 64}), \
                        patch.object(lt, "snapshot_inputs", return_value=INPUTS), \
                        patch.object(lt, "git_revision", return_value=REVISION), patch.object(lt, "execute", side_effect=execute):
                    result = batch.run(root, name, "build/ci-verification/failed-child")
                self.assertEqual(1, len(events))
                self.assertFalse(result["passed"])
                first, = result["routes"]
                self.assertEqual("FileNotFoundError", first["adapter_error"])
                self.assertEqual(3, len(result["refused_profiles"]))
                self.assertEqual(0, result["actual_target_executions"])
                if type(exit_code) is int and exit_code != 0:
                    diagnostic = first["failed_child_origin"]
                    self.assertEqual("retained", diagnostic["status"])
                    self.assertEqual(origin, diagnostic["origin"])
                    self.assertFalse(diagnostic["raw_log_uploaded"])
                    self.assertFalse(diagnostic["native_success_inferred"])
                else:
                    self.assertNotIn("failed_child_origin", first)
                self.assertNotIn("PRIVATE_CHILD_BODY", json.dumps(result))
                self.assertNotIn("/private/path", json.dumps(result))

    def test_failed_child_origin_rejects_duplicates_foreign_paths_malformed_types_and_unbounded_logs(self):
        marker = "NATIVECMPKIT_ANDROID_PREFLIGHT_ORIGIN "
        origin = {"source": "android_device_tests.py", "symbol": "validate_api_selection",
            "line": batch.device.validate_api_selection.__code__.co_firstlineno}
        valid = marker + json.dumps(origin) + "\n"
        invalid = [valid + valid, "prefix " + valid, marker.rstrip() + ":" + json.dumps(origin),
            marker + "not JSON\n", marker + "[]\n", marker + '{"source":"android_device_tests.py","source":"android_device_tests.py","symbol":"validate_api_selection","line":1}\n',
            "x" * (64 * 1024) + "\n" + valid, marker + " " * 513 + json.dumps(origin)]
        for key, value in (("source", "foreign.py"), ("source", "/private/android_device_tests.py"),
            ("source", "../android_device_tests.py"), ("source", ["android_device_tests.py"]),
            ("symbol", "PRIVATE_TOKEN_NEVER_EXPORT"), ("symbol", "/private/path"),
            ("symbol", "validate_api_selection\nPRIVATE_BODY"), ("line", True), ("line", 0),
            ("line", -1), ("line", 20000), ("line", "1"), ("line", float("nan")),
            ("body", "PRIVATE_CHILD_BODY")):
            changed = {**origin, key: value}
            invalid.append(marker + json.dumps(changed) + "\n")
        for index, payload in enumerate(invalid):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                source = root / "scripts/ci/android_device_tests.py"
                source.parent.mkdir(parents=True)
                source.write_bytes((ROOT / "scripts/ci/android_device_tests.py").read_bytes())
                log = root / "child.log"
                log.write_text(payload)
                result = batch.failed_child_origin(root, "child.log")
                self.assertEqual("refused", result["status"])
                self.assertNotIn("origin", result)
                self.assertNotIn("PRIVATE_", json.dumps(result))
                self.assertNotIn("/private", json.dumps(result))
        for cause in ("symlink", "hardlink", "traversal", "missing", "unavailable"):
            with self.subTest(cause=cause), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                log = root / "child.log"
                log.write_text(valid)
                relative = "child.log"
                if cause == "symlink":
                    log.rename(root / "retained.log")
                    log.symlink_to(root / "retained.log")
                elif cause == "hardlink":
                    __import__("os").link(log, root / "shared.log")
                elif cause == "traversal":
                    relative = "../child.log"
                elif cause == "missing":
                    log.unlink()
                elif cause == "unavailable":
                    log.write_text(marker + json.dumps({"source": "unavailable", "symbol": "unavailable", "line": 0}) + "\n")
                result = batch.failed_child_origin(root, relative)
                self.assertEqual("unavailable" if cause in ("missing", "unavailable") else "refused", result["status"])
                self.assertNotIn("origin", result)


    def test_workflow_routes_batches_through_fixed_adapter_with_bounded_json_xml_uploads(self):
        source = (ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("ANDROID_BATCH: ${{ matrix.android-batch }}", source)
        self.assertIn('scripts/ci/android_device_batch.py plan --batch "$ANDROID_BATCH"', source)
        self.assertIn('scripts/ci/android_device_batch.py run --batch "$ANDROID_BATCH"', source)
        self.assertEqual("read", source.split("permissions:\n  contents: ")[1].splitlines()[0])
        upload = source.split("- name: Keep receipts and actual selected-task XML", 1)[1].split("\n  webview-consumer:", 1)[0]
        expected = {
            "build/ci-verification/${{ matrix.slot }}/routes/*/*.json",
            "build/ci-verification/${{ matrix.slot }}/routes/*/library/*.json",
            "build/ci-verification/${{ matrix.slot }}/routes/*/io-documents/receipt.json",
            "build/ci-verification/${{ matrix.slot }}/routes/*/permission-demo/receipt.json",
            "build/ci-verification/${{ matrix.slot }}/routes/*/storage-probe/receipt.json",
            "build/ci-verification/${{ matrix.slot }}/routes/*/fresh-reports/*.xml",
        }
        self.assertEqual(expected, {line.strip() for line in upload.splitlines() if "/routes/" in line})
        self.assertNotIn("routes/**", upload)
        for forbidden in (".apk", ".aar", ".jar", ".keystore", "android-user/", "avd/", "*.log"):
            self.assertNotIn(forbidden, upload)
        self.assertEqual(5, source.count("\n          key:"))
        for name, packages in fixed.SDK_PACKAGES.items():
            self.assertEqual([packages], __import__("re").findall(
                r"inputs\.profile == '" + name + r"' && '([^']+)'", source))


if __name__ == "__main__":
    unittest.main()
