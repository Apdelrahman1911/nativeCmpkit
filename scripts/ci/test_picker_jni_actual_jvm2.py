"""NEW exact-JVM2 ingress/refusal controls. All processes/JNI are synthetic here.

Temporary files/pipes belong only to these source controls. Native creation,
compilation, VM loading, signals to real processes and real OS pickers never run.
These controls cannot establish real JNI, AppKit, shutdown or resource counts.
"""
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest import mock

import picker_jni_actual_jvm2 as r
import picker_jni_paths as old


def compile_log(root):
    artifact = {"reason": "compiler-artifact", "target": {"name": "calf_filepicker_native",
                "src_path": (root / "calf-file-picker/native/src/lib.rs").as_posix()},
                "profile": {"test": True}, "fresh": False,
                "executable": (root / "build/ci-verification/jvm2/native-build.private" / r.TARGET /
                               "debug/deps/calf_filepicker_native-1234567890abcdef").as_posix()}
    return json.dumps(artifact) + '\n{"reason": "build-finished", "success": true}'


def method_log(method, *, interleaved=True):
    marker = r.METHOD_MARKERS[r.checked_method(method)]
    lines = ["running 1 test"]
    if interleaved:
        lines += [f"test {method} ... {r.JVM_MARKER}", marker, "ok"]
    else:
        lines += [r.JVM_MARKER, marker, f"test {method} ... ok"]
    lines += ["test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 42 filtered out; finished in 0.1s"]
    return "\n".join(lines)


def runtime(revision):
    return {"source_revision": revision, "source_tree_dirty": False,
            "host": {"system": "Darwin", "architecture": "arm64"}, "java": {"major": 17},
            "rust": {"release": "1.98.0", "host": r.TARGET}, "compiler_runtime_fingerprint": "f" * 64}


class SyntheticChild:
    pid = 424242

    def __init__(self, payload=b"", *, exited=False):
        read, write = os.pipe()
        os.write(write, payload)
        os.close(write)
        self.stdout = os.fdopen(read, "rb", buffering=0)
        self.returncode = 0 if exited else None
        self.waits = []

    def poll(self):
        return self.returncode

    def wait(self, timeout):
        self.waits.append(timeout)
        self.returncode = 0
        return self.returncode


def group_absent(pid, sig):
    if sig == 0:
        raise ProcessLookupError


class PickerActualJvm2Receipts(unittest.TestCase):
    def test_new_focus_is_exact_two_macos_only_and_old_domains_keep_their_original_population(self):
        self.assertEqual(2, len(r.expected_methods("Darwin")))
        self.assertEqual(tuple(name.split("::", 1)[1] for name in r.METHODS), old.expected_methods("Darwin", "actual-jvm2"))
        for host in ("Linux", "Windows", "FreeBSD", ""):
            with self.assertRaises(ValueError): r.expected_methods(host)
            with self.assertRaises(ValueError): old.expected_methods(host, "actual-jvm2")
        self.assertEqual((5, 6, 1), tuple(len(old.expected_methods(host)) for host in ("Linux", "Darwin", "Windows")))
        self.assertEqual(old.MACOS_METHODS, old.expected_methods("Darwin", "macos-domain"))
        with self.assertRaises(ValueError): old.review_log(method_log(r.METHODS[0]), "Darwin", "actual-jvm2")

    def test_one_locked_no_run_lib_target_compile_has_no_harness_or_multi_filter_arguments(self):
        root = Path("/synthetic/owned")
        command = r.compile_command(root, root / "build/ci-verification/jvm2/native-build.private")
        self.assertEqual(["cargo", "test", "--manifest-path", "calf-file-picker/native/Cargo.toml",
                          "--locked", "--jobs", "1", "--no-run", "--lib", "--target", r.TARGET,
                          "--target-dir", "build/ci-verification/jvm2/native-build.private", "--message-format=json"], command)
        self.assertTrue(r.review_compile(compile_log(root), root)["profile"]["test"])
        self.assertNotIn("--", command)
        self.assertNotIn("jni_path_tests", command)

    def test_compile_only_missing_duplicate_failed_foreign_or_cached_artifacts_never_pass(self):
        root = Path("/synthetic/owned")
        body = compile_log(root)
        artifact, finished = body.splitlines()
        variants = (artifact, finished, body + "\n" + artifact, body + "\n" + finished,
                    body.replace('"success": true', '"success": false'), body.replace('"test": true', '"test": false'),
                    body.replace('"fresh": false', '"fresh": true'), body.replace('"calf_filepicker_native"', '"foreign"'),
                    body.replace('/src/lib.rs', '/src/foreign.rs'), body + "\n{malformed}",
                    body + "\nrunning 1 test", body + "\n" + r.JVM_MARKER)
        for changed in variants:
            with self.subTest(changed=changed), self.assertRaises(ValueError): r.review_compile(changed, root)

    def test_exact_inventory_is_not_a_pass_and_each_command_has_one_full_name_no_broad_fallback(self):
        binary = Path("build/ci-verification/jvm2/native-build.private/test")
        for name in r.METHODS:
            self.assertEqual([str(binary), name, "--exact", "--list"], r.exact_command(binary, name, inventory=True))
            self.assertEqual([str(binary), name, "--exact", "--nocapture", "--test-threads=1"], r.exact_command(binary, name))
            self.assertEqual(0, r.review_inventory(name + ": test\n\n1 test, 0 benchmarks\n", name)["executed_tests"])
            for wrong in ("", name + ": test\n0 tests, 0 benchmarks", name + ": benchmark\n1 test, 0 benchmarks",
                          name + ": test\n" + name + ": test\n2 tests, 0 benchmarks",
                          "jni_path_tests::foreign: test\n1 test, 0 benchmarks"):
                with self.assertRaises(ValueError): r.review_inventory(wrong, name)
        for name in ("jni_path_tests", "jni_path_tests::actual_jni_", r.METHODS[0] + "," + r.METHODS[1], ""):
            with self.assertRaises(ValueError): r.exact_command(binary, name)

    def test_two_independent_real_method_receipt_shapes_need_one_marker_each_without_file_or_shutdown_claims(self):
        for method in r.METHODS:
            for interleaved in (True, False):
                result = r.review_method(method_log(method, interleaved=interleaved), method)
                self.assertEqual("passed", result["status"])
                self.assertEqual(1, result["fresh_process_vm_marker_count"])
                self.assertEqual(17, result["actual_vm_major"])
                self.assertEqual(42, result["observed_filtered_tests"])
                for flag in ("filesystem_operations_verified", "vm_shutdown_verified", "native_parent_or_release_completion_verified"):
                    self.assertIs(result[flag], False)

    def test_zero_marker_only_foreign_replayed_failed_ignored_duplicate_unfinished_and_wrong_summaries_refuse(self):
        method = r.METHODS[0]
        body = method_log(method)
        for changed in (r.JVM_MARKER + "\n" + r.METHOD_MARKERS[0], body.replace("1 passed", "0 passed"),
                        body.replace("running 1 test", "running 2 tests"), body.replace("0 failed", "1 failed"),
                        body.replace("0 ignored", "1 ignored"), body.replace("0 measured", "1 measured"),
                        body.replace("\nok\n", "\nFAILED\n"), body.replace("\nok\n", "\nignored\n"),
                        body.replace("\nok\n", "\n"), body.replace(method, "jni_path_tests::foreign"),
                        body + "\n" + body.splitlines()[-1], body + f"\ntest {method} ... ok",
                        body + f"\ntest jni_path_tests::{old.METHODS[0]} ... ok",
                        body + "\ntest foreign_研究 ... ok",
                        "\n".join((body.splitlines()[-1], *body.splitlines()[:-1])),
                        "\n".join((body.splitlines()[0], f"test {method} ... ok", r.JVM_MARKER, r.METHOD_MARKERS[0], body.splitlines()[-1])),
                        body + '\n{"reason":"build-finished","success":true}'):
            with self.subTest(changed=changed), self.assertRaises(ValueError): r.review_method(changed, method)
        with self.assertRaises(ValueError): r.review_method(method_log(r.METHODS[1]), method)

    def test_process_runtime_method_checker_and_post_body_cleanup_markers_cannot_be_waived(self):
        for method in r.METHODS:
            body = method_log(method)
            for marker in (r.JVM_MARKER, r.METHOD_MARKERS[r.checked_method(method)]):
                for changed in (body.replace(marker, ""), body + "\n" + marker):
                    with self.assertRaises(ValueError): r.review_method(changed, method)
            for addition in (r.METHOD_MARKERS[1 - r.checked_method(method)], old.MACOS_DOMAIN_MARKER,
                             "WARNING in native method: synthetic", "JNI DETECTED ERROR",
                             "FATAL ERROR in native method", "JNI local refs: 999",
                             "R3 owned JNI frame cleanup failed: synthetic", "R3 owned JNI exception cleanup failed: synthetic"):
                with self.assertRaises(ValueError): r.review_method(body + "\n" + addition, method)
            with self.assertRaises(ValueError): r.review_method(body.replace("major=17", "major=21"), method)
        with self.assertRaises(ValueError): r.review_method("x" * (r.MAX_LOG_BYTES + 1), r.METHODS[0])

    def test_one_600_second_deadline_is_consumed_across_phases_never_reset_or_expanded(self):
        now = [0.0]
        budget = r.NativeBudget(clock=lambda: now[0])
        self.assertEqual(600, budget.remaining())
        now[0] = 240.25
        self.assertEqual(359, budget.remaining())
        now[0] = 550.0
        self.assertEqual(50, budget.remaining())
        now[0] = 600.0
        with self.assertRaises(ValueError): budget.remaining()
        self.assertEqual(600.0, budget.elapsed())
        now[0] = 600.01
        with self.assertRaises(ValueError): budget.elapsed()
        now[0] = -1.0
        with self.assertRaises(ValueError): budget.remaining()
        self.assertEqual(8192 * 1024 * 1024, r.DISK_RESERVE_BYTES)

    def test_capture_is_byte_bounded_keeps_the_permitted_prefix_and_short_write_is_not_complete(self):
        body = io.BytesIO()
        with mock.patch.object(r, "MAX_LOG_BYTES", 8):
            self.assertEqual((5, True), r.append_capture(body, b"first", 0))
            self.assertEqual((8, False), r.append_capture(body, b"second", 5))
        self.assertEqual(b"firstsec", body.getvalue())
        writer = mock.Mock()
        writer.write.return_value = 1
        with self.assertRaises(ValueError): r.append_capture(writer, b"abcd", 0)

    def test_executable_fd_custody_rejects_symlinks_hardlinks_wrong_target_and_changed_postimage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target = root / "native-build.private"
            folder = target / r.TARGET / "debug/deps"
            folder.mkdir(parents=True)
            binary = folder / "calf_filepicker_native-1234567890abcdef"
            binary.write_bytes(b"synthetic-not-a-native-executable")
            binary.chmod(0o700)
            identity = r.executable_identity(binary, target)
            self.assertEqual(hashlib.sha256(binary.read_bytes()).hexdigest(), identity["sha256"])
            alias = folder / "calf_filepicker_native-fedcba0987654321"
            alias.symlink_to(binary)
            with self.assertRaises(ValueError): r.executable_identity(alias, target)
            alias.unlink()
            os.link(binary, alias)
            with self.assertRaises(ValueError): r.executable_identity(binary, target)
            alias.unlink()
            binary.write_bytes(b"changed-synthetic-postimage")
            self.assertNotEqual(identity, r.executable_identity(binary, target))
            binary.chmod(0o600)
            with self.assertRaises(ValueError): r.executable_identity(binary, target)
            with self.assertRaises(ValueError): r.executable_identity(binary, root / "foreign-target")

    def test_source_and_runtime_require_all_nine_exact_r3_endpoints_and_the_new_owner_without_global_enrollment(self):
        self.assertEqual(9, len(r.R3_SOURCE_SHA256))
        for digest in r.R3_SOURCE_SHA256.values(): self.assertRegex(digest, r"^[a-f0-9]{64}$")
        revision = "a" * 40
        context = runtime(revision)
        r.require_runtime(context, revision)
        for section, key, value in (("host", "system", "Linux"), ("host", "architecture", "x64"),
                                    ("java", "major", 21), ("rust", "release", "1.97.0"), ("rust", "host", "foreign")):
            changed = json.loads(json.dumps(context))
            changed[section][key] = value
            with self.assertRaises(ValueError): r.require_runtime(changed, revision)
        with self.assertRaises(ValueError): r.require_runtime({**context, "source_tree_dirty": True}, revision)
        with self.assertRaises(ValueError): r.require_runtime(context, "b" * 40)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workflow = root / r.WORKFLOW
            workflow.parent.mkdir(parents=True)
            workflow.write_bytes(b"synthetic workflow")
            inputs = {**dict.fromkeys(r.OWNING_INPUTS, "0" * 64), **r.R3_SOURCE_SHA256}
            with mock.patch.object(r.library, "snapshot_inputs", return_value=inputs.copy()):
                self.assertEqual(9, len({k: v for k, v in r.source_snapshot(root).items() if k in r.R3_SOURCE_SHA256}))
            for key in (r.OWNING_INPUTS[1], next(iter(r.R3_SOURCE_SHA256))):
                changed = inputs.copy()
                changed.pop(key)
                with mock.patch.object(r.library, "snapshot_inputs", return_value=changed), self.assertRaises(ValueError):
                    r.source_snapshot(root)

    def test_additive_workflow_is_manual_readonly_macos_only_exact2_json_only_and_does_not_replay_old_controls(self):
        workflow = (r.library.ROOT / r.WORKFLOW).read_text()
        self.assertIn("options: [all, picker-jni-macos-domain, native-lock-reproducibility, native-lock-windows-source, picker-jni-actual-jvm2, picker-awt-generation]", workflow)
        job = workflow.split("\n  picker-jni-actual-jvm2:", 1)[1].split("\n  picker-awt-generation:", 1)[0]
        for needed in ("github.repository == 'Apdelrahman1911/nativeCmpkit'", "github.event_name == 'workflow_dispatch'",
                       "inputs.profile == 'picker-jni-actual-jvm2'", "runs-on: macos-26", "timeout-minutes: 15",
                       "persist-credentials: false", "java-version: '17'", "toolchain: '1.98.0'",
                       "--expected-arch arm64 --require-clean --apple", "-p test_picker_jni_actual_jvm2.py -v",
                       "--focus actual-jvm2 --output build/ci-verification/picker-jni-actual-jvm2",
                       "build/ci-verification/picker-jni-actual-jvm2/*.json", "retention-days: 7",
                       "test_picker_jni_paths.PickerJniPathReceipts.test_failure_only_native_workflow"):
            self.assertIn(needed, job)
        for forbidden in ("matrix:", "gradlew", "setup-android", "xvfb", "xdotool", "cargo test", "--focus macos-domain",
                          "-p test_picker_jni_paths.py", "*.log", "target/", ".dylib", "**", "printenv", "set -x"):
            self.assertNotIn(forbidden, job)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotRegex(workflow, r"(?m)^\s*[\w-]+:\s*(?:write|write-all)\s*$")
        self.assertNotIn("library.execute(", (r.library.ROOT / "scripts/ci/picker_jni_actual_jvm2.py").read_text())

    def phase(self, root, child, *, budget=None, group=group_absent, selector_factory=None):
        budget = r.NativeBudget(clock=lambda: 0.0) if budget is None else budget
        with ExitStack() as stack:
            spawn = stack.enter_context(mock.patch.object(r.subprocess, "Popen", return_value=child))
            stack.enter_context(mock.patch.object(r.shutil, "disk_usage", return_value=mock.Mock(free=r.DISK_RESERVE_BYTES + 1)))
            signals = stack.enter_context(mock.patch.object(r.os, "killpg", side_effect=group))
            stack.enter_context(mock.patch.object(r.os, "getsid", return_value=child.pid))
            if selector_factory is not None:
                stack.enter_context(mock.patch.object(r.selectors, "DefaultSelector", return_value=selector_factory))
            result = r.owned_phase(root, ["synthetic-never-spawned"], root / "phase.private.log", root / "phase.json", budget)
            self.assertTrue(spawn.call_args.kwargs["start_new_session"])
            self.assertEqual(r.subprocess.PIPE, spawn.call_args.kwargs["stdout"])
            self.assertEqual(r.subprocess.STDOUT, spawn.call_args.kwargs["stderr"])
            return result, signals.call_args_list, budget

    def test_owned_timeout_cleans_only_the_live_original_leader_and_cannot_pass_the_shared_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            child = SyntheticChild()
            budget = r.NativeBudget(clock=lambda: 0.0)
            budget.remaining = mock.Mock(side_effect=[600, r.Refusal("shared-native-deadline-exhausted-or-clock-invalid")])
            result, calls, budget = self.phase(root, child, budget=budget)
            self.assertIn(mock.call(child.pid, signal.SIGTERM), calls)
            self.assertEqual("owned-leader-reaped", result["live_cleanup"]["status"])
            self.assertEqual("absent", result["post_exit_group_state"])
            self.assertIn("deadline", result["stop_reason"])
            self.assertFalse(result["capture_complete"])
            self.assertTrue(child.stdout.closed)
            with self.assertRaises(ValueError): r.require_phase_success(result, budget)

    def test_owned_capture_overflow_is_refused_retains_only_bounded_prefix_and_cleans_the_live_leader(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            child = SyntheticChild(b"0123456789abcdef")
            with mock.patch.object(r, "MAX_LOG_BYTES", 8):
                result, calls, budget = self.phase(root, child)
            self.assertEqual(8, result["captured_bytes"])
            self.assertEqual(b"01234567", (root / "phase.private.log").read_bytes())
            self.assertEqual("private-capture-limit-refused", result["stop_reason"])
            self.assertIn(mock.call(child.pid, signal.SIGTERM), calls)
            with self.assertRaises(ValueError): r.require_phase_success(result, budget)

    def test_post_exit_group_present_or_unknown_is_readonly_refusal_and_never_signals_reused_or_foreign_groups(self):
        for state in ("present", "unknown"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as directory:
                child = SyntheticChild(exited=True)
                def observe(pid, sig):
                    self.assertEqual(0, sig)
                    if state == "unknown": raise PermissionError
                result, calls, budget = self.phase(Path(directory).resolve(), child, group=observe)
                self.assertEqual(state, result["post_exit_group_state"])
                self.assertEqual([mock.call(child.pid, 0)], calls)
                self.assertNotIn("live_cleanup", result)
                self.assertTrue(child.stdout.closed)
                with self.assertRaises(ValueError): r.require_phase_success(result, budget)
                with mock.patch.object(r.os, "killpg") as signals:
                    self.assertEqual("leader-already-exited-no-signals", r.cleanup_live_owned_leader(child)["status"])
                    signals.assert_not_called()

    def test_primary_capture_exception_is_preserved_while_owned_cleanup_and_selector_close_errors_stay_secondary(self):
        class Primary(Exception): pass
        primary = Primary("synthetic-private-value-never-public")
        class BrokenSelector:
            closed = False
            def register(self, *args): pass
            def select(self, timeout): raise primary
            def close(self):
                self.closed = True
                raise OSError("synthetic-secondary-cleanup-secret")
        selector = BrokenSelector()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            child = SyntheticChild()
            with self.assertRaises(Primary) as error:
                self.phase(root, child, selector_factory=selector)
            self.assertIs(primary, error.exception)
            self.assertTrue(selector.closed)
            self.assertTrue(child.stdout.closed)
            receipt = json.loads((root / "phase.json").read_text())
            self.assertEqual("Primary", receipt["primary_error_type"])
            self.assertEqual(["OSError"], receipt["cleanup_error_types"])
            self.assertEqual("owned-leader-reaped", receipt["live_cleanup"]["status"])
            self.assertNotIn("secret", json.dumps(receipt))
            self.assertNotIn("private-value", json.dumps(receipt))

    def test_positive_owned_capture_requires_complete_eof_absent_group_and_unchanged_descriptor_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            payload = b"synthetic bounded complete output\n"
            result, calls, budget = self.phase(root, SyntheticChild(payload, exited=True))
            r.require_phase_success(result, budget)
            self.assertEqual(payload.decode(), r.read_private_log(root / "phase.private.log", result))
            self.assertEqual([mock.call(SyntheticChild.pid, 0)], calls)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), result["private_capture_sha256"])
            (root / "phase.private.log").write_bytes(payload.replace(b"output", b"OUTPUT"))
            with self.assertRaises(ValueError): r.read_private_log(root / "phase.private.log", result)

    def test_disk_reserve_refusal_never_creates_a_child_or_log_and_cannot_certify_zero_test_green(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with mock.patch.object(r.shutil, "disk_usage", return_value=mock.Mock(free=r.DISK_RESERVE_BYTES - 1)), \
                    mock.patch.object(r.subprocess, "Popen") as spawn:
                budget = r.NativeBudget(clock=lambda: 0.0)
                result = r.owned_phase(root, ["synthetic-never-spawned"], root / "phase.private.log", root / "phase.json", budget)
                spawn.assert_not_called()
                self.assertFalse((root / "phase.private.log").exists())
                self.assertFalse(result["started"])
                with self.assertRaises(ValueError): r.require_phase_success(result, budget)

    def orchestration(self, root, *, mutate=False, final_custody_exhaustion=False):
        revision = "a" * 40
        inputs = {**dict.fromkeys(r.OWNING_INPUTS, "0" * 64), **r.R3_SOURCE_SHA256}
        commands = []
        now, identity_calls = [0.0], [0]
        budget = r.NativeBudget(clock=lambda: now[0])
        def identity(ignored, ignored_target):
            identity_calls[0] += 1
            if final_custody_exhaustion and identity_calls[0] == 10:
                now[0] = 600.01
            return {"sha256": "e" * 64}
        def source_snapshot(ignored):
            if mutate and commands:
                return {**inputs, "synthetic-source-change": "f" * 64}
            return inputs.copy()
        def phase(ignored, command, log_path, receipt_path, budget):
            commands.append(command)
            return {"started": True, "exit_code": 0, "capture_complete": True,
                    "post_exit_group_state": "absent", "stop_reason": None}
        def log(path, execution):
            if path.name == "compile.private.log": return compile_log(root)
            index = int(path.name.split("-", 1)[1].split(".", 1)[0]) - 1
            method = r.METHODS[index]
            return method + ": test\n1 test, 0 benchmarks" if path.name.startswith("inventory-") else method_log(method)
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(r.library, "ROOT", root))
            stack.enter_context(mock.patch.object(r.platform, "system", return_value="Darwin"))
            stack.enter_context(mock.patch.object(r.library, "git_revision", return_value=revision))
            stack.enter_context(mock.patch.object(r, "source_snapshot", side_effect=source_snapshot))
            stack.enter_context(mock.patch.object(r.library.runtime_context, "capture", return_value=runtime(revision)))
            stack.enter_context(mock.patch.object(r, "owned_phase", side_effect=phase))
            stack.enter_context(mock.patch.object(r, "read_private_log", side_effect=log))
            stack.enter_context(mock.patch.object(r, "NativeBudget", return_value=budget))
            stack.enter_context(mock.patch.object(r, "executable_identity", side_effect=identity))
            no_spawn = stack.enter_context(mock.patch.object(r.subprocess, "Popen"))
            no_old_execute = stack.enter_context(mock.patch.object(r.library, "execute"))
            stack.enter_context(mock.patch("builtins.print"))
            result = r.run(Path("build/ci-verification/jvm2"))
            no_spawn.assert_not_called()
            no_old_execute.assert_not_called()
        if final_custody_exhaustion:
            self.assertEqual(10, identity_calls[0])
        return result, commands, json.loads((root / "build/ci-verification/jvm2/receipt.json").read_text())

    def test_controller_synthetic_model_compiles_once_then_lists_and_executes_only_two_individual_names(self):
        with tempfile.TemporaryDirectory() as directory:
            result, commands, receipt = self.orchestration(Path(directory).resolve())
            self.assertEqual(0, result)
            self.assertTrue(receipt["passed"])
            self.assertEqual(2, receipt["tests"])
            self.assertEqual(5, len(commands))
            self.assertIn("--no-run", commands[0])
            self.assertEqual([r.METHODS[0], r.METHODS[0], r.METHODS[1], r.METHODS[1]], [c[1] for c in commands[1:]])
            self.assertEqual([True, False, True, False], ["--list" in c for c in commands[1:]])
            self.assertFalse(receipt["multi_filter_support_assumed"])
            self.assertEqual(0, receipt["compile_only_executed_tests"])

    def test_slow_final_executable_custody_exhausts_shared_deadline_before_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            result, commands, receipt = self.orchestration(Path(directory).resolve(), final_custody_exhaustion=True)
            self.assertEqual(1, result)
            self.assertFalse(receipt["passed"])
            self.assertEqual("final-source-runtime-and-deadline", receipt["failed_stage"])
            self.assertEqual("shared-native-deadline-exhausted-or-clock-invalid", receipt["reason_code"])
            self.assertEqual(2, receipt["tests"])
            self.assertEqual(2, len(receipt["inventories"]))
            self.assertEqual(list(r.METHODS), [testcase["classname"] + "::" + testcase["name"] for testcase in receipt["testcases"]])
            self.assertTrue(all(testcase["status"] == "passed" for testcase in receipt["testcases"]))
            self.assertEqual(5, len(commands))
            self.assertEqual([r.METHODS[0], r.METHODS[0], r.METHODS[1], r.METHODS[1]], [c[1] for c in commands[1:]])
            self.assertEqual(600, receipt["native_operation_budget_seconds"])
            self.assertNotIn("native_operation_elapsed_seconds", receipt)
            self.assertTrue(receipt["held_inputs"])

    def test_changed_source_after_compile_refuses_before_inventory_or_method_and_never_retries_or_broadens(self):
        with tempfile.TemporaryDirectory() as directory:
            result, commands, receipt = self.orchestration(Path(directory).resolve(), mutate=True)
            self.assertEqual(1, result)
            self.assertFalse(receipt["passed"])
            self.assertEqual(0, receipt["tests"])
            self.assertEqual(1, len(commands))
            self.assertEqual("inventory-1", receipt["failed_stage"])
            self.assertFalse(receipt["held_inputs"])


if __name__ == "__main__": unittest.main()
