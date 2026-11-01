"""Owning synthetic capture refusals only; no Gradle/native/network/Git calls.

Graph and log data below are explicitly synthetic, not historical/host receipts.
These tests must never call the native runner or use an accepted graph as a pass.
"""
from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

import desktop_dependency_capture as capture
import library_tests as lt


class DesktopDependencyCaptureModels(unittest.TestCase):
    DEFAULT = "desktop-macos-arm64"
    REVISION = "1" * 40
    INPUTS = ("build.gradle.kts", "calf-io/src/commonTest/explicitly-synthetic.kt")
    MACHINES = {"desktop-macos-arm64": "arm64", "desktop-windows-x64": "AMD64",
                "desktop-linux-arm64": "aarch64", "desktop-macos-x64": "x86_64"}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-explicitly-synthetic-graphs-",
                                                     dir=os.environ.get("NATIVECMPKIT_SOURCE_MODEL_TMP"))
        self.addCleanup(self.temporary.cleanup)
        self.sequence, self.calls, self.raw = 0, [], {}
        self.before = self.after = self.mutate_graph = self.mutate_raw = self.mutate_log = None
        self.returns, self.active = {}, False

    def fixture(self, slot=DEFAULT):
        self.sequence += 1
        root = Path(self.temporary.name) / str(self.sequence)
        root.mkdir()
        for relative in (*self.INPUTS, capture.RUNTIME):
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
        for relative in self.INPUTS:
            (root / relative).write_text("// Explicitly synthetic configured input\n")
        for relative in (capture.WORKFLOW, *(item["source"] for item in capture.COLLECTORS)):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(lt.ROOT / relative, path)
        selected = capture.ROUTES[slot]
        context = {"schema_version": 1, "source_revision": self.REVISION, "source_tree_dirty": False,
                   "host": {"system": selected[0], "architecture": selected[1], "python": "explicitly-synthetic"}}
        (root / capture.RUNTIME).write_text(json.dumps(context) + "\n")
        environment = {"SLOT": slot, "SUITE": "desktop", "TEST_MODULES": "calf-webview", "TEST_FOCUS": selected[3]}
        return root, environment

    def synthetic_graph(self, item):
        module = {"group": "example.explicitly.synthetic", "name": "ordinary", "version": "1.0"}
        artifactless = {"group": "org.jetbrains.compose.desktop", "name": "desktop-jvm-explicitly-synthetic", "version": "1.12.0"}
        unexpected = {"group": "example.explicitly.synthetic", "name": "unexpected-artifactless", "version": "9.3+synthetic"}
        artifact = {**module, "filename": "explicitly-synthetic.jar", "bytes": 7, "sha256": "2" * 64}
        rows = [{"project": project, "configuration": name, "modules": copy.deepcopy([module, artifactless, unexpected]),
                 "artifacts": [copy.deepcopy(artifact)], "unresolved": [], "complete": True}
                for project in capture.PROJECTS for name in item["configurations"]]
        return {"scope": item["scope"], "configurations": rows, "complete": True, "packages_published": False}

    def execute(self, root, argv, log, timeout, reserve, **kwargs):
        self.assertFalse(self.active, "The two acquisition invocations must be serial")
        self.active = True
        try:
            item = next(item for item in capture.COLLECTORS if Path(argv[-2]).stem == item["phase"])
            index = next(index for index, candidate in enumerate(capture.COLLECTORS) if candidate is item)
            self.calls.append((root, list(argv), log, timeout, reserve))
            self.assertEqual((600, 8192, {}), (timeout, reserve, kwargs))
            self.assertEqual(item["sha256"], hashlib.sha256(Path(argv[-2]).read_bytes()).hexdigest())
            if self.before:
                self.before(root, item, index)
            data = self.synthetic_graph(item)
            if self.mutate_graph:
                self.mutate_graph(index, data)
            raw = (json.dumps(data, indent=1) + "\n").encode()
            if self.mutate_raw:
                raw = self.mutate_raw(index, raw)
            (root / item["graph"]).write_bytes(raw)
            self.raw[(root, item["phase"])] = raw
            lines = ["EXPLICITLY_SYNTHETIC_PRIVATE_LOG_SENTINEL_DO_NOT_UPLOAD",
                     "> Task :" + capture.TASK,
                     "NATIVECMPKIT_DESKTOP_GRAPH configurations=" + str(24 * len(item["configurations"])) + " external-coordinates=3"]
            if self.mutate_log:
                lines = self.mutate_log(index, lines)
            log.write_text("\n".join(lines) + "\n")
            if self.after:
                self.after(root, item, index)
            result = self.returns.get(index, {"exit_code": 0, "elapsed_seconds": 0.001})
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            self.active = False

    def invoke(self, root, environment, *, profile=capture.PROFILE, slot=None, system=None, machine=None, revisions=None):
        slot = environment["SLOT"] if slot is None else slot
        selected = capture.ROUTES.get(slot, capture.ROUTES[self.DEFAULT])
        with patch.object(capture.platform, "system", return_value=selected[0] if system is None else system), \
                patch.object(capture.platform, "machine", return_value=self.MACHINES.get(slot, "arm64") if machine is None else machine), \
                patch.object(lt, "snapshot_inputs", side_effect=lambda current: {
                    relative: hashlib.sha256((current / relative).read_bytes()).hexdigest() for relative in self.INPUTS}), \
                patch.object(lt, "git_revision", **({"side_effect": revisions} if revisions else {"return_value": self.REVISION})), \
                patch.object(lt, "execute", side_effect=self.execute), \
                patch.object(lt, "run", side_effect=AssertionError("Native controller must never be called")):
            return capture.run(root, profile, slot, environment=environment)

    def test_four_routes_eight_exact_serial_commands_and_288_rows_leave_native_root_absent(self):
        rows = 0
        for slot, selected in capture.ROUTES.items():
            with self.subTest(slot=slot):
                root, environment = self.fixture(slot)
                result = self.invoke(root, environment)
                self.assertTrue(result["capture_complete"])
                self.assertEqual((0, 0, False), (result["native_methods_requested"], result["advisory_queries_requested"], result["packages_published"]))
                self.assertTrue(result["native_slot_output_absent"])
                self.assertFalse((root / "build/ci-verification" / slot).exists())
                self.assertFalse((root / capture.PRIVATE / "init").exists())
                self.assertEqual(selected[2], result["javafx_classifier_for_independent_review"])
                for item, phase, invocation in zip(capture.COLLECTORS, result["phases"], self.calls[-2:]):
                    argv = invocation[1]
                    expected = [".\\gradlew.bat" if selected[0] == "Windows" else "./gradlew", "--no-daemon",
                                "--no-configuration-cache", "--max-workers=2", "--no-parallel", "--console=plain",
                                "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
                                "-Pkotlin.compiler.execution.strategy=in-process", "--init-script", argv[9], capture.TASK]
                    self.assertEqual(expected, argv)
                    self.assertEqual(1, argv.count(capture.TASK))
                    self.assertEqual("<owned-private-init>", phase["command"][9])
                    rows += phase["observed_graph"]["configurations"]
                before = json.loads((root / (capture.FLAT + "inputs-before.json")).read_text())
                after = json.loads((root / (capture.FLAT + "inputs-after.json")).read_text())
                self.assertEqual(before, after)
                self.assertEqual(set(self.INPUTS) | {capture.WORKFLOW, *(item["source"] for item in capture.COLLECTORS)}, set(before))
        self.assertEqual((8, 288), (len(self.calls), rows))

    def test_artifactless_unexpected_allcomponents_and_exact_raw_graph_bytes_are_retained(self):
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        for item, phase in zip(capture.COLLECTORS, result["phases"]):
            copy_path = root / (capture.FLAT + item["phase"] + "-graph.json")
            self.assertEqual(self.raw[(root, item["phase"])], copy_path.read_bytes())
            self.assertEqual((root / item["graph"]).read_bytes(), copy_path.read_bytes())
            row = json.loads(copy_path.read_bytes())["configurations"][0]
            names = {module["name"] for module in row["modules"]}
            artifact_names = {artifact["name"] for artifact in row["artifacts"]}
            self.assertEqual({"desktop-jvm-explicitly-synthetic", "unexpected-artifactless"}, names - artifact_names)
            self.assertEqual(3, phase["observed_graph"]["external_coordinates"])
        self.assertNotIn("predicted", json.dumps(result))

    def test_foreign_profiles_slots_and_accepted_linux_x64_refuse_before_execution(self):
        for profile, slot in (("webview-desktop", self.DEFAULT), (capture.PROFILE, "desktop-linux-x64"),
                              (capture.PROFILE, "desktop-foreign"), ("tooling", "desktop-windows-x64")):
            with self.subTest(profile=profile, slot=slot):
                root, environment = self.fixture()
                with self.assertRaises(ValueError):
                    self.invoke(root, environment, profile=profile, slot=slot)
                self.assertFalse((root / capture.PRIVATE).exists())
        self.assertEqual([], self.calls)

    def test_foreign_suite_modules_focus_or_slot_environment_refuse_before_execution(self):
        for key, value in (("SUITE", "android-device"), ("TEST_MODULES", "calf-io"),
                           ("TEST_MODULES", "calf-webview,calf-io"), ("TEST_MODULES", ""),
                           ("TEST_FOCUS", "tls-rendering"), ("TEST_FOCUS", "tls-rendering-cookies-policy-media"),
                           ("SLOT", "desktop-macos-x64")):
            with self.subTest(key=key, value=value):
                root, environment = self.fixture()
                environment[key] = value
                with self.assertRaises(ValueError):
                    self.invoke(root, environment, slot=self.DEFAULT)
        self.assertEqual([], self.calls)

    def test_wrong_current_host_arch_and_runtime_source_identity_refuse_before_execution(self):
        for system, machine in (("Linux", "arm64"), ("Darwin", "x86_64"), ("Darwin", "foreign")):
            root, environment = self.fixture()
            with self.subTest(system=system, machine=machine), self.assertRaises(ValueError):
                self.invoke(root, environment, system=system, machine=machine)
        for field, value in (("source_revision", "3" * 40), ("source_tree_dirty", True),
                             ("source_tree_dirty", 0), ("schema_version", True), ("schema_version", 2),
                             ("host", {"system": "Linux", "architecture": "arm64"}),
                             ("host", {"system": "Darwin", "architecture": "x64"})):
            root, environment = self.fixture()
            context = json.loads((root / capture.RUNTIME).read_text())
            context[field] = value
            (root / capture.RUNTIME).write_text(json.dumps(context))
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.invoke(root, environment)
        self.assertEqual([], self.calls)

    def test_duplicate_runtime_and_graph_json_keys_are_refused(self):
        root, environment = self.fixture()
        file = root / capture.RUNTIME
        file.write_text(file.read_text().replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'))
        with self.assertRaises(ValueError):
            self.invoke(root, environment)
        self.assertEqual([], self.calls)
        self.mutate_raw = lambda index, raw: raw.replace(b'"scope":', b'"scope": "duplicate", "scope":', 1) if index == 0 else raw
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        self.assertFalse(result["capture_complete"])
        self.assertFalse(result["phases"][0]["capture_complete"])
        self.assertTrue(result["phases"][1]["capture_complete"])
        self.assertEqual(2, len(self.calls))

    def test_archived_collector_pin_change_refuses_before_execution(self):
        for item in capture.COLLECTORS:
            root, environment = self.fixture()
            file = root / item["source"]
            file.write_bytes(file.read_bytes() + b"// explicitly synthetic change\n")
            with self.subTest(phase=item["phase"]), self.assertRaises(ValueError):
                self.invoke(root, environment)
        self.assertEqual([], self.calls)

    def test_source_runtime_and_archival_symlink_hardlink_nonregular_substitutions_refuse(self):
        for relative in (self.INPUTS[0], capture.RUNTIME, capture.WORKFLOW, capture.COLLECTORS[0]["source"]):
            for kind in ("symlink", "hardlink", "directory"):
                root, environment = self.fixture()
                file = root / relative
                original = file.with_name(file.name + ".explicitly-synthetic-preserved")
                file.rename(original)
                if kind == "symlink":
                    file.symlink_to(original)
                elif kind == "hardlink":
                    os.link(original, file)
                else:
                    file.mkdir()
                with self.subTest(relative=relative, kind=kind), self.assertRaises((ValueError, OSError)):
                    self.invoke(root, environment)
                self.assertTrue(original.exists())
                self.assertFalse((root / capture.PRIVATE).exists())
        self.assertEqual([], self.calls)

    def test_every_existing_flat_native_fixed_or_private_output_is_preserved_before_execution(self):
        paths = [capture.FLAT + name + ".json" for name in
                 ("inputs-before", "inputs-after", "runtime-graph", "compile-test-graph", "receipt")]
        paths += [capture.PRIVATE, "build/ci-verification/" + self.DEFAULT]
        paths += [str(Path(item["graph"]).parent) for item in capture.COLLECTORS]
        for relative in paths:
            root, environment = self.fixture()
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative.endswith(".json"):
                path.write_text("Preserve explicitly synthetic previous evidence")
                sentinel = path
            else:
                path.mkdir()
                sentinel = path / "preserved-sentinel"
                sentinel.write_text("Preserve explicitly synthetic previous evidence")
            before = sentinel.read_bytes()
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                self.invoke(root, environment)
            self.assertEqual(before, sentinel.read_bytes())
        self.assertEqual([], self.calls)

    def test_symlinked_output_file_and_parent_do_not_mutate_their_targets(self):
        for relative in (capture.FLAT + "receipt.json", "build/ci-verification"):
            root, environment = self.fixture()
            target = root / "explicitly-synthetic-unowned-target"
            target.mkdir()
            sentinel = target / "sentinel"
            sentinel.write_text("untouched")
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(sentinel if relative.endswith(".json") else target, target_is_directory=not relative.endswith(".json"))
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                self.invoke(root, environment)
            self.assertEqual("untouched", sentinel.read_text())
        self.assertEqual([], self.calls)

    def test_nonregular_and_linked_generated_graphs_are_never_copied_as_success(self):
        for kind in ("symlink", "hardlink", "directory"):
            def mutate(root, item, index):
                if index != 0:
                    return
                file = root / item["graph"]
                original = file.with_name("explicitly-synthetic-preserved.json")
                file.rename(original)
                if kind == "symlink":
                    file.symlink_to(original)
                elif kind == "hardlink":
                    os.link(original, file)
                else:
                    file.mkdir()
            self.after = mutate
            root, environment = self.fixture()
            with self.subTest(kind=kind):
                result = self.invoke(root, environment)
                self.assertFalse(result["capture_complete"])
                self.assertTrue(result["phases"][1]["capture_complete"])
                self.assertFalse((root / (capture.FLAT + "runtime-graph.json")).exists())
                self.assertTrue((root / capture.COLLECTORS[0]["graph"]).with_name("explicitly-synthetic-preserved.json").exists())

    def test_changed_private_init_after_first_execution_fails_and_preserves_it_while_second_runs(self):
        def mutate(root, item, index):
            if index == 0:
                file = root / capture.PRIVATE / "init/runtime.gradle"
                file.write_bytes(file.read_bytes() + b"// explicitly synthetic changed init\n")
        self.after = mutate
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        self.assertFalse(result["capture_complete"])
        self.assertEqual(2, len(self.calls))
        self.assertTrue(result["phases"][1]["capture_complete"])
        self.assertTrue((root / capture.PRIVATE / "init/runtime.gradle").exists())
        self.assertTrue(any(error.startswith("private-init-cleanup-refused:") for error in result["errors"]))

    def test_changed_private_init_before_execution_cannot_launch_that_phase(self):
        original_write = capture.write
        def corrupted_write(root, relative, value):
            result = original_write(root, relative, value)
            if relative == capture.PRIVATE + "/init/runtime.gradle":
                (root / relative).write_bytes(value + b"// explicitly synthetic tamper\n")
            return result
        root, environment = self.fixture()
        with patch.object(capture, "write", side_effect=corrupted_write):
            result = self.invoke(root, environment)
        self.assertFalse(result["capture_complete"])
        self.assertEqual(1, len(self.calls))
        self.assertEqual("compile-test.gradle", Path(self.calls[0][1][9]).name)
        self.assertTrue(result["phases"][1]["capture_complete"])

    def test_missing_incomplete_unresolved_duplicate_foreign_rows_modules_and_artifacts_refuse(self):
        mutations = {
            "missing-row": lambda data: data["configurations"].pop(),
            "duplicate-row": lambda data: data["configurations"].__setitem__(1, copy.deepcopy(data["configurations"][0])),
            "foreign-project": lambda data: data["configurations"][0].__setitem__("project", ":sample"),
            "foreign-configuration": lambda data: data["configurations"][0].__setitem__("configuration", "androidRuntimeClasspath"),
            "unresolved": lambda data: data["configurations"][0].__setitem__("unresolved", [{"type": "explicitly.synthetic.Failure"}]),
            "incomplete": lambda data: data.__setitem__("complete", False),
            "incomplete-row": lambda data: data["configurations"][0].__setitem__("complete", False),
            "published": lambda data: data.__setitem__("packages_published", True),
            "foreign-scope": lambda data: data.__setitem__("scope", "foreign"),
            "duplicate-module": lambda data: data["configurations"][0]["modules"].append(copy.deepcopy(data["configurations"][0]["modules"][0])),
            "duplicate-artifact": lambda data: data["configurations"][0]["artifacts"].append(copy.deepcopy(data["configurations"][0]["artifacts"][0])),
            "foreign-artifact": lambda data: data["configurations"][0]["artifacts"][0].__setitem__("name", "foreign"),
            "artifact-traversal": lambda data: data["configurations"][0]["artifacts"][0].__setitem__("filename", "../foreign.jar"),
            "artifact-windows-path": lambda data: data["configurations"][0]["artifacts"][0].__setitem__("filename", "C:\\foreign.jar"),
            "artifact-hash": lambda data: data["configurations"][0]["artifacts"][0].__setitem__("sha256", "wrong"),
            "artifact-length-bool": lambda data: data["configurations"][0]["artifacts"][0].__setitem__("bytes", True),
        }
        for name, mutate in mutations.items():
            self.mutate_graph = lambda index, data: mutate(data) if index == 0 else None
            root, environment = self.fixture()
            with self.subTest(name=name):
                result = self.invoke(root, environment)
                self.assertFalse(result["capture_complete"])
                self.assertFalse(result["phases"][0]["capture_complete"])
                self.assertTrue(result["phases"][1]["capture_complete"])
                self.assertEqual(self.raw[(root, "runtime")], (root / (capture.FLAT + "runtime-graph.json")).read_bytes())

    def test_missing_graph_and_invalid_json_remain_failure_with_second_phase_independent(self):
        def remove(root, item, index):
            if index == 0:
                (root / item["graph"]).unlink()
        self.after = remove
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        self.assertFalse(result["capture_complete"])
        self.assertTrue(result["phases"][1]["capture_complete"])
        self.after = None
        self.mutate_raw = lambda index, raw: b"EXPLICITLY SYNTHETIC INVALID JSON\n" if index == 0 else raw
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        self.assertFalse(result["capture_complete"])
        self.assertTrue(result["phases"][1]["capture_complete"])

    def test_exact_task_summary_order_count_and_fresh_log_markers_are_required(self):
        mutations = (
            lambda lines: lines[:1] + lines[2:],
            lambda lines: lines + [lines[1]],
            lambda lines: [line.replace(capture.TASK, "foreignGraphTask") for line in lines],
            lambda lines: [line + " UP-TO-DATE" if line.startswith("> Task") else line for line in lines],
            lambda lines: lines[:-1], lambda lines: lines + [lines[-1]],
            lambda lines: [line.replace("configurations=24", "configurations=23") for line in lines],
            lambda lines: [line.replace("external-coordinates=3", "external-coordinates=2") for line in lines],
            lambda lines: [lines[0], lines[2], lines[1]],
        )
        for number, mutate in enumerate(mutations):
            self.mutate_log = lambda index, lines: mutate(lines) if index == 0 else lines
            root, environment = self.fixture()
            with self.subTest(number=number):
                result = self.invoke(root, environment)
                self.assertFalse(result["capture_complete"])
                self.assertTrue(result["phases"][1]["capture_complete"])
        self.mutate_log = None
        def stale(root, item, index):
            if index == 0:
                old = time.time_ns() - 20_000_000_000
                os.utime(root / capture.PRIVATE / "runtime.log", ns=(old, old))
        self.after = stale
        root, environment = self.fixture()
        self.assertFalse(self.invoke(root, environment)["capture_complete"])

    def test_first_exit_or_exception_failure_is_retained_and_second_executes_once_without_retry(self):
        cases = ({"exit_code": 1, "elapsed_seconds": 0.2},
                 {"exit_code": 75, "stop_reason": "Disk reserve unavailable; command not started"},
                 RuntimeError("EXPLICITLY_SYNTHETIC_SECRET_BODY /private/absolute/path"))
        for failed in cases:
            self.returns = {0: failed}
            root, environment = self.fixture()
            count = len(self.calls)
            with self.subTest(kind=type(failed).__name__):
                result = self.invoke(root, environment)
                self.assertEqual(2, len(self.calls) - count)
                self.assertFalse(result["phases"][0]["capture_complete"])
                self.assertTrue(result["phases"][1]["capture_complete"])
                self.assertFalse(result["capture_complete"])
                self.assertNotIn("EXPLICITLY_SYNTHETIC_SECRET_BODY", json.dumps(result))

    def test_unknown_execution_fields_or_boolean_exit_do_not_become_success_or_leak(self):
        for failed in ({"exit_code": True}, {"exit_code": 0, "elapsed_seconds": -1},
                       {"exit_code": 0, "stop_reason": "EXPLICITLY_SYNTHETIC_SECRET_BODY"},
                       {"exit_code": 0, "secret": "EXPLICITLY_SYNTHETIC_SECRET_BODY"}):
            self.returns = {0: failed}
            root, environment = self.fixture()
            result = self.invoke(root, environment)
            self.assertFalse(result["capture_complete"])
            self.assertTrue(result["phases"][1]["capture_complete"])
            self.assertNotIn("EXPLICITLY_SYNTHETIC_SECRET_BODY", json.dumps(result))

    def test_changed_full_inputs_are_recorded_after_failure_not_cache_subset_filtered(self):
        def mutate(root, item, index):
            if index == 0:
                (root / self.INPUTS[1]).write_text("// Explicitly synthetic changed other-library input\n")
        self.after = mutate
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        self.assertFalse(result["capture_complete"])
        before = json.loads((root / (capture.FLAT + "inputs-before.json")).read_text())
        after = json.loads((root / (capture.FLAT + "inputs-after.json")).read_text())
        self.assertNotEqual(before[self.INPUTS[1]], after[self.INPUTS[1]])
        self.assertIn("inputs_after", result)
        self.assertEqual(2, len(self.calls))

    def test_runtime_bytes_or_identity_and_source_revision_change_fail_enclosing_capture(self):
        def mutate(root, item, index):
            if index == 0:
                file = root / capture.RUNTIME
                file.write_bytes(file.read_bytes() + b" \n")
        self.after = mutate
        root, environment = self.fixture()
        self.assertFalse(self.invoke(root, environment)["capture_complete"])
        self.after = None
        root, environment = self.fixture()
        self.assertFalse(self.invoke(root, environment, revisions=[self.REVISION, "3" * 40])["capture_complete"])
        def replace(root, item, index):
            if index == 0:
                file = root / capture.RUNTIME
                value = file.read_bytes()
                file.rename(file.with_name("explicitly-synthetic-previous-runtime.json"))
                file.write_bytes(value)
        self.after = replace
        root, environment = self.fixture()
        self.assertFalse(self.invoke(root, environment)["capture_complete"])

    def test_graph_copy_log_changes_or_native_output_creation_fail_final_binding_without_deletion(self):
        for relative in (capture.COLLECTORS[0]["graph"], capture.FLAT + "runtime-graph.json",
                         capture.PRIVATE + "/runtime.log", "build/ci-verification/" + self.DEFAULT):
            def mutate(root, item, index):
                if index == 1:
                    file = root / relative
                    if relative.endswith(self.DEFAULT):
                        file.mkdir()
                        (file / "preserved-sentinel").write_text("unowned native output")
                    else:
                        file.write_bytes(file.read_bytes() + b" \n")
            self.after = mutate
            root, environment = self.fixture()
            with self.subTest(relative=relative):
                result = self.invoke(root, environment)
                self.assertFalse(result["capture_complete"])
                self.assertTrue((root / relative).exists())

    def test_generated_flat_copy_log_and_private_init_links_are_refused_and_preserved(self):
        for relative in (capture.FLAT + "runtime-graph.json", capture.PRIVATE + "/runtime.log",
                         capture.PRIVATE + "/init/runtime.gradle"):
            for kind in ("symlink", "hardlink"):
                def mutate(root, item, index):
                    if index == 1:
                        file = root / relative
                        original = file.with_name(file.name + ".explicitly-synthetic-preserved")
                        file.rename(original)
                        if kind == "symlink":
                            file.symlink_to(original)
                        else:
                            os.link(original, file)
                self.after = mutate
                root, environment = self.fixture()
                with self.subTest(relative=relative, kind=kind):
                    result = self.invoke(root, environment)
                    self.assertFalse(result["capture_complete"])
                    self.assertTrue((root / relative).exists())
                    self.assertTrue((root / relative).with_name(Path(relative).name + ".explicitly-synthetic-preserved").exists())

    def test_unowned_private_init_addition_is_preserved_not_recursively_removed(self):
        def mutate(root, item, index):
            if index == 0:
                (root / capture.PRIVATE / "init/unowned-sentinel").write_text("preserve unowned addition")
        self.after = mutate
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        self.assertFalse(result["capture_complete"])
        self.assertEqual(2, len(self.calls))
        self.assertEqual("preserve unowned addition", (root / capture.PRIVATE / "init/unowned-sentinel").read_text())
        self.assertTrue((root / capture.PRIVATE / "init/runtime.gradle").exists())

    def test_private_directory_symlink_substitution_cannot_execute_again_or_delete_target(self):
        def mutate(root, item, index):
            if index == 0:
                private = root / capture.PRIVATE
                private.rename(private.with_name("explicitly-synthetic-owned-old"))
                target = root / "explicitly-synthetic-unowned-private"
                target.mkdir()
                (target / "sentinel").write_text("preserve unowned directory")
                private.symlink_to(target, target_is_directory=True)
        self.after = mutate
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        self.assertFalse(result["capture_complete"])
        self.assertEqual(1, len(self.calls))
        self.assertEqual("preserve unowned directory", (root / "explicitly-synthetic-unowned-private/sentinel").read_text())

    def test_final_receipt_collision_is_preserved_and_never_replaced_with_success(self):
        def mutate(root, item, index):
            if index == 1:
                (root / (capture.FLAT + "receipt.json")).write_text("preserve unowned receipt")
        self.after = mutate
        root, environment = self.fixture()
        with self.assertRaises(ValueError):
            self.invoke(root, environment)
        self.assertEqual("preserve unowned receipt", (root / (capture.FLAT + "receipt.json")).read_text())

    def test_private_paths_and_transcripts_do_not_appear_in_flat_receipt_or_main_exception_output(self):
        root, environment = self.fixture()
        result = self.invoke(root, environment)
        value = (root / (capture.FLAT + "receipt.json")).read_text()
        self.assertNotIn(str(root), value)
        self.assertNotIn("EXPLICITLY_SYNTHETIC_PRIVATE_LOG_SENTINEL_DO_NOT_UPLOAD", value)
        self.assertNotIn("PRIVATE_LOG_SENTINEL", json.dumps(result))
        stream = io.StringIO()
        with patch.object(capture.sys, "argv", ["capture", "--profile", capture.PROFILE, "--slot", self.DEFAULT]), \
                patch.object(capture, "run", side_effect=RuntimeError("EXPLICITLY_SYNTHETIC_SECRET_BODY /private/path")), \
                redirect_stdout(stream), redirect_stderr(stream):
            self.assertEqual(1, capture.main())
        self.assertNotIn("EXPLICITLY_SYNTHETIC_SECRET_BODY", stream.getvalue())
        self.assertNotIn("/private/path", stream.getvalue())
        self.assertEqual("RuntimeError", json.loads(stream.getvalue())["error_type"])

    def test_workflow_capture_is_security_only_before_unchanged_independent_native_step_and_flat_allowlist(self):
        workflow = (lt.ROOT / capture.WORKFLOW).read_text()
        anchor = "      - name: Capture missing-host Desktop dependency graphs without native replay\n"
        self.assertEqual(1, workflow.count(anchor))
        start = workflow.index(anchor)
        end = workflow.index("      - name: Related real JVM/JNI path tests", start)
        step = workflow[start:end]
        self.assertIn("if: ${{ !cancelled() && steps.plan.outcome == 'success' && (inputs.profile == 'webview-desktop-security-regressions' || inputs.profile == 'webview-desktop-security-linux-arm64-windows-pair' || inputs.profile == 'webview-desktop-security-macos-pair') }}", step)
        self.assertIn('"$PYTHON" scripts/ci/desktop_dependency_capture.py \\\n            --profile webview-desktop-security-regressions --slot "$SLOT"', step)
        self.assertNotIn("continue-on-error", step)
        self.assertNotIn("--focus", step)
        self.assertLess(workflow.index("      - name: Source-set-aware expected library tests"), start)
        native = workflow[workflow.index("      - name: Fresh actual library suite with strict nonzero receipts"):]
        self.assertIn("if: ${{ !cancelled() && steps.plan.outcome == 'success' }}", native.split("        env:", 1)[0])
        self.assertIn("permissions:\n  contents: read\n", workflow)
        upload = workflow[workflow.index("      - name: Keep receipts and actual selected-task XML only; never packages"):]
        self.assertIn("            build/ci-runtime/*.json\n", upload)
        self.assertNotIn(capture.PRIVATE, upload)
        self.assertNotIn("desktop-dependency-audit", upload)
        self.assertNotIn("*.log", upload)


if __name__ == "__main__":
    unittest.main()
