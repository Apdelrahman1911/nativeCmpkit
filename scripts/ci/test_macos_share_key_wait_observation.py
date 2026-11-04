# SPDX-License-Identifier: Apache-2.0
"""NEW source/mock late-snapshot controls; no Cargo, SDK, native child or signals."""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import macos_share_appkit_lifecycle as runner
import macos_share_missing_only as original

ROOT = Path(__file__).resolve().parents[2]
MODULE = "macos_share_key_wait_observation"
CASES = original.CASES_SOURCE
SOURCE_REASON = "Owned AppKit window did not become key"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class KeyWaitPostFailureControls(unittest.TestCase):
    def owner(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE), "NEW exact late-snapshot owner is missing")
        return importlib.import_module(MODULE)

    def panic(self, *, reason=SOURCE_REASON, line=61, source=CASES):
        # Deliberately synthetic text, NOT a download or replay of Share650 stderr.
        return (f"thread 'main' (987654) panicked at {source}:{line}:9:\n{reason}\n"
                "note: source/mock only; private text is never exported\n").encode()

    def marker(self, **changes):
        fields = {"main": "available", "owned": "available", "app_active": "false",
                  "app_running": "false", "policy": "regular", "visible": "true",
                  "key": "false", "can_key": "true", "miniaturized": "false",
                  "app_key": "absent", "loop_main": "true", "mode": "absent"}
        fields.update(changes)
        return ("NATIVECMPKIT_APPKIT_KEY_WAIT_POST_FAILURE version=1 " +
                " ".join(name + "=" + value for name, value in fields.items()) + "\n").encode()

    def snapshot(self, payload=None, **kwargs):
        owner = self.owner()
        return owner.post_failure_snapshot(self.panic() + self.marker() if payload is None else payload,
            source_hash=owner.cases_after_sha256(), failed_case="missing_content_view",
            source_absolute="/source/mock/" + CASES, **kwargs)

    def fixture(self, root):
        owner = self.owner()
        for name in owner.fixture_inputs():
            target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())

    def test01_original_readiness_lines_predicate_deadline_and_every_old_body_are_exact(self):
        owner = self.owner(); current = (ROOT / CASES).read_bytes()
        prior = owner.source_before_key_wait(CASES, current)
        self.assertEqual(original.CASES_SHA, sha(prior))
        lines = current.decode().splitlines()
        self.assertEqual('        assert!(Instant::now() < deadline, "{reason}");', lines[60])
        self.assertEqual('    pump_until("Owned AppKit window did not become key", || {', lines[175])
        self.assertEqual("        window.isKeyWindow()", lines[176])
        self.assertEqual("    body(&window);", lines[178])
        self.assertIn("Instant::now() + Duration::from_secs(10)", current.decode())
        self.assertEqual(prior[:prior.index(b"pub(crate) fn run()")],
                         current[:current.index(b"pub(crate) fn run()")])

    def test02_exact_primary_panic_gate_then_protected_observation_then_independent_cleanup(self):
        source = (ROOT / CASES).read_text()
        self.assertIn("if failed_owned_key_wait(name, &result) {", source)
        hook = source.split("let result = catch_unwind(AssertUnwindSafe(|| autoreleasepool(|_| case())));", 1)[1]
        self.assertLess(hook.index("failed_owned_key_wait(name, &result)"), hook.index("cleanup_owned"))
        self.assertIn("catch_unwind(AssertUnwindSafe(observe_owned_key_wait_post_failure))", hook)
        self.assertIn("result.is_ok() && cleanup.is_ok() && !CONTROL_FAILED.load(AtomicOrdering::Acquire)", hook)
        gate = source.split("fn failed_owned_key_wait", 1)[1].split("fn observed_bool", 1)[0]
        self.assertIn('name != "missing_content_view"', gate)
        self.assertIn("result.as_ref().err()", gate)
        self.assertIn("downcast_ref::<String>()", gate)
        self.assertIn("downcast_ref::<&str>()", gate)
        self.assertIn('Some("Owned AppKit window did not become key")', gate)
        self.assertNotIn("format!", gate)
        self.assertNotIn("NSApplication", gate)

    def test03_native_main_and_owned_reference_guards_precede_readonly_once_only_queries(self):
        source = (ROOT / CASES).read_text()
        self.assertIn("fn observe_owned_key_wait_post_failure()", source)
        observer = source.split("fn observe_owned_key_wait_post_failure()", 1)[1]
        self.assertLess(observer.index("MainThreadMarker::new()"), observer.index("NSApplication::sharedApplication"))
        self.assertRegex(observer, r"owned\s*\.try_borrow\(\)")
        self.assertIn("held.as_ref().cloned()", observer)
        self.assertLess(observer.index("try_borrow()"), observer.index("window.isVisible()"))
        for query in ("app.isActive()", "app.isRunning()", "app.activationPolicy()", "app.keyWindow()",
                      "window.isVisible()", "window.isKeyWindow()", "window.canBecomeKeyWindow()",
                      "window.isMiniaturized()", "NSRunLoop::currentRunLoop()", "NSRunLoop::mainRunLoop()",
                      "current.currentMode()"):
            self.assertEqual(1, observer.count(query), query)
        for forbidden in ("while ", "for ", "nextEvent", "sendEvent", "activate", "makeKey",
                          "setContentView", "orderFront", "windowNumber", "windows()", "to_string()", "{:?}", "{:p}"):
            self.assertNotIn(forbidden, observer)
        self.assertIn('"present-unclassified"', observer)
        self.assertIn('"absent"', observer)
        self.assertIn('"unavailable"', observer)

    def test04_finite_exact_inverse_roundtrip_is_not_old_or_unknown_current_admission(self):
        owner = self.owner(); document = owner._document()
        self.assertEqual(owner.BOUND_PATHS, set(document["bindings"]))
        self.assertEqual(4, len(document["bindings"]))
        for name, row in document["bindings"].items():
            current = (ROOT / name).read_bytes()
            old = owner.current_source_before_key_wait(name, current)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(old), len(old)))
            self.assertIs(old, owner.source_before_key_wait(name, old))
            self.assertIs(old, owner.peel_key_wait_for_history(name, old))
            forward = old
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before)); forward = forward.replace(before, after, 1)
            self.assertEqual(current, forward)
            for wrong in (old, current[:-1], current + b"\n", b"", None, bytearray(current), current.decode(),
                          b"x" * (owner.MAX_SOURCE_BYTES + 1)):
                with self.subTest(name=name, kind=type(wrong).__name__), self.assertRaises(ValueError):
                    owner.current_source_before_key_wait(name, wrong)
        unknown = b"unlisted bytes remain uncertified"
        self.assertIs(unknown, owner.peel_key_wait_for_history("unlisted", unknown))
        self.assertIs(unknown, owner.source_before_key_wait("unlisted", unknown))
        with self.assertRaises(ValueError): owner.source_before_key_wait(Path("unlisted"), unknown)

    def test05_displaced_partial_duplicate_fragment_and_manifest_file_custody_refuse(self):
        owner = self.owner()
        for name, row in owner._document()["bindings"].items():
            raw = (ROOT / name).read_bytes(); fragment = row["fragments"][0]["after"].encode()
            for bad in (raw.replace(fragment, b"", 1), raw + fragment, raw.replace(fragment, b"", 1) + fragment):
                with self.subTest(name=name), self.assertRaises(ValueError): owner.source_before_key_wait(name, bad)
        raw = owner.SPEC_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "spec.json"
            with patch.object(owner, "SPEC_PATH", target):
                for bad in (raw + b"\n", raw.replace(b'"schema_version": 1', b'"schema_version": true', 1),
                            b'{"schema_version":1,"schema_version":1}', b'{"scope":NaN}'):
                    target.write_bytes(bad)
                    with self.assertRaises(ValueError): owner._document()
                target.unlink(); target.symlink_to(ROOT / owner.SPEC_RELATIVE)
                with self.assertRaises(ValueError): owner._document()
                target.unlink(); backing = target.with_name("backing.json"); backing.write_bytes(raw)
                target.hardlink_to(backing)
                with self.assertRaises(ValueError): owner._document()

    def test06_new_native_owning_gate_demands_actual_after_map_and_retains_original_pins(self):
        owner = self.owner()
        current = {name: sha((ROOT / name).read_bytes()) for name in runner.HARNESS_PINS}
        with patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no child or compiler")):
            value = runner.source_contract(ROOT, current)
            self.assertEqual(owner.cases_after_sha256(), value["source_sha256"])
            self.assertEqual(original.CASES_SHA, value["original_harness_sha256"])
            self.assertTrue(value["source_bound_failed_control_gate_verified"])
            self.assertFalse(value["raw_control_flag_exported"])
            self.assertFalse(value["raw_control_flag_independently_observed"])
            with self.assertRaisesRegex(runner.Refusal, "unqualified-native-harness-bytes"):
                runner.source_contract(ROOT, runner.HARNESS_PINS)

    def test07_ordinary_current_leaf_and_added_inputs_are_required_not_symlink_or_hardlink(self):
        owner = self.owner()
        with tempfile.TemporaryDirectory(prefix="appkit-keywait-source-only-") as name:
            root = Path(name); self.fixture(root)
            self.assertTrue(owner.validate_current_sources(root))
            for relative in (CASES, "scripts/ci/macos_share_key_wait_observation.py", owner.SPEC_RELATIVE):
                target = root / relative; raw = target.read_bytes(); target.unlink()
                with self.subTest(relative=relative), self.assertRaises((OSError, ValueError)):
                    owner.validate_current_sources(root)
                target.symlink_to(ROOT / relative)
                with self.assertRaises(ValueError): owner.validate_current_sources(root)
                target.unlink(); backing = target.with_name(target.name + ".backing"); backing.write_bytes(raw)
                target.hardlink_to(backing)
                with self.assertRaises(ValueError): owner.validate_current_sources(root)
                target.unlink(); backing.unlink(); target.write_bytes(raw + b"\n")
                with self.assertRaises(ValueError): owner.validate_current_sources(root)
                target.write_bytes(raw)

    def test08_fixed_late_fields_are_not_the_original_operand_or_native_cause_or_recipient_proof(self):
        value = self.snapshot()
        self.assertTrue(value["available"])
        self.assertEqual("post-original-panic-before-owned-cleanup", value["sampling_phase"])
        self.assertEqual("sequential-read-only-not-atomic", value["sample_consistency"])
        self.assertFalse(value["original_predicate_value_captured"])
        self.assertFalse(value["exact_native_cause_verified"])
        self.assertFalse(value["reader_executed_native_queries"])
        self.assertFalse(value["raw_payload_exported"])
        self.assertFalse(value["recipient_delivery_verified"])
        self.assertEqual(False, value["fields"]["owned_key"])
        self.assertEqual("absent", value["fields"]["app_key_window_relation"])
        self.assertEqual("absent", value["fields"]["current_run_loop_mode"])
        self.assertNotIn("987654", json.dumps(value))
        self.assertNotIn("private text", json.dumps(value))
        self.assertNotIn(SOURCE_REASON, json.dumps(value))

    def test09_missing_main_or_owned_reference_preserves_unavailable_not_false_or_absence(self):
        all_missing = {key: "unavailable" for key in ("main", "owned", "app_active", "app_running", "policy",
                                                    "visible", "key", "can_key", "miniaturized", "app_key", "loop_main", "mode")}
        value = self.snapshot(self.panic() + self.marker(**all_missing))
        self.assertTrue(value["available"])
        self.assertEqual("unavailable", value["fields"]["main"])
        self.assertIsNone(value["fields"]["app_active"])
        self.assertIsNone(value["fields"]["owned_key"])
        self.assertEqual("unavailable", value["fields"]["app_key_window_relation"])
        absent = self.snapshot(self.panic() + self.marker(owned="absent", visible="unavailable", key="unavailable",
                    can_key="unavailable", miniaturized="unavailable", app_key="present-unclassified"))
        self.assertTrue(absent["available"])
        self.assertEqual("absent", absent["fields"]["owned_window"])
        self.assertIsNone(absent["fields"]["owned_key"])
        self.assertEqual("present-unclassified", absent["fields"]["app_key_window_relation"])

    def test10_short_wrong_source_or_phase_duplicate_unknown_or_oversized_stderr_is_unavailable(self):
        owner = self.owner(); valid = self.panic() + self.marker()
        for payload in (b"", self.panic(), self.marker(), self.panic(line=999) + self.marker(),
                        self.panic(reason="private unqualified reason") + self.marker(),
                        self.panic(source="unrelated.rs") + self.marker(), valid + self.marker(),
                        valid + self.panic(), valid.replace(b"policy=regular", b"policy=private-value"),
                        valid.replace(b" key=false", b" key=false foreign=true"), b"\xff",
                        b"x" * (owner.MAX_STDERR + 1)):
            with self.subTest(bytes=len(payload)):
                result = self.snapshot(payload)
                self.assertFalse(result["available"])
                self.assertFalse(result["raw_payload_exported"])
        for source_hash, case in ((original.CASES_SHA, "missing_content_view"), ("0" * 64, "missing_content_view"),
                                 (owner.cases_after_sha256(), "no_key_window")):
            result = owner.post_failure_snapshot(valid, source_hash=source_hash, failed_case=case,
                                                 source_absolute="/source/mock/" + CASES)
            self.assertFalse(result["available"])

    def test11_guard_availability_cannot_infer_fields_and_sequential_values_are_not_atomic(self):
        for changes in ({"main": "unavailable"}, {"owned": "absent"}, {"owned": "unavailable"},
                        {"owned": "absent", "visible": "unavailable", "key": "unavailable", "can_key": "unavailable",
                         "miniaturized": "unavailable", "app_key": "this-owned"}):
            with self.subTest(changes=changes): self.assertFalse(self.snapshot(self.panic() + self.marker(**changes))["available"])
        # Sequential getter reads may legitimately disagree; do not fabricate an atomic snapshot.
        value = self.snapshot(self.panic() + self.marker(key="true", app_key="absent", mode="other"))
        self.assertTrue(value["available"])
        self.assertTrue(value["fields"]["owned_key"])
        self.assertEqual("absent", value["fields"]["app_key_window_relation"])

    def test12_same_owned_stream_custody_adds_late_snapshot_without_repainting_old_catalogue(self):
        owner = self.owner()
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); output = root / "build/ci-verification/new"; output.mkdir(parents=True)
            stream = output / "native.stderr.private.log"; stream.write_bytes(self.panic() + self.marker())
            execution = {"passed": False, "private_logs": [{"relative_path": stream.relative_to(root).as_posix(),
                                                            **runner.file_identity(stream)}]}
            reports = {"testcases": [{"name": "missing_content_view", "status": "failed"}]}
            inputs = {CASES: owner.cases_after_sha256(), original.OPERATION_SOURCE: original.OPERATION_SHA}
            with patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no native query")):
                result = runner.missing_view_failure_observation(root, output, execution, reports, inputs)
                self.assertFalse(result["available"])
                self.assertEqual("unqualified-source-or-failed-case", result["reason"])
                self.assertTrue(result["post_failure_owned_key_wait_snapshot"]["available"])
                stream.write_bytes(b"private changed body")
                refused = runner.missing_view_failure_observation(root, output, execution, reports, inputs)
            self.assertFalse(refused["available"])
            self.assertNotIn("post_failure_owned_key_wait_snapshot", refused)
            self.assertNotIn("private changed body", json.dumps(refused))

    def test13_one_first_missing_source_plan_requests_no_accepted_appkit_or_jni_or_real_execution(self):
        self.owner()
        with patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no process")):
            plan = runner.plan("missing_content_view")
        self.assertEqual(["missing_content_view"], plan["exact_native_cases"])
        self.assertEqual(["<admitted-mh-execute>", "--case=missing_content_view"], plan["native_command"])
        self.assertEqual((1200, 240, 8 * 1024 ** 3), (plan["compile_timeout_seconds"], plan["native_timeout_seconds"],
                                                       plan["disk_reserve_bytes"]))
        self.assertEqual([], plan["publication_commands"])
        self.assertTrue(plan["read_only_plan"])
        self.assertTrue(plan["key_wait_post_failure_snapshot"]["failure_only"])
        self.assertFalse(plan["key_wait_post_failure_snapshot"]["native_cause_verified"])
        self.assertTrue(plan["key_wait_post_failure_snapshot"]["accepted650_jni_timeout_not_requested"])
        self.assertNotIn(original.JNI_METHOD, " ".join(plan["cargo_command"] + plan["native_command"]))

    def test14_exact_original_control_assertions_stay_with_only_the_owning_hash_operand_changed(self):
        owner = self.owner()
        changed = {"scripts/ci/test_macos_share_appkit_lifecycle_runner.py": {
                    "test_exact_reviewed_source_gate_does_not_invent_exported_flag_or_visibility"},
                   "scripts/ci/test_macos_share_missing_only.py": {
                    "test_fixed_native_source_diagnostic_pins_are_unchanged_and_not_native_certification"}}
        for name, affected in changed.items():
            current = (ROOT / name).read_bytes(); before = owner.source_before_key_wait(name, current)
            old = {node.name: node for node in ast.walk(ast.parse(before)) if isinstance(node, ast.FunctionDef)}
            new = {node.name: node for node in ast.walk(ast.parse(current)) if isinstance(node, ast.FunctionDef)}
            self.assertEqual(set(old), set(new))
            for method in set(old) - affected:
                self.assertEqual(ast.dump(old[method], include_attributes=False), ast.dump(new[method], include_attributes=False))
            for method in affected:
                assertions = lambda node: [child.func.attr for child in ast.walk(node) if isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute) and child.func.attr.startswith("assert")]
                self.assertEqual(assertions(old[method]), assertions(new[method]))
        source = (ROOT / "scripts/ci/macos_share_key_wait_observation.py").read_text()
        self.assertNotIn("subprocess", source)
        self.assertNotIn("ctypes", source)
        calls = {ast.unparse(node.func) for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)}
        self.assertFalse(calls.intersection({"eval", "exec", "compile", "os.kill", "os.killpg"}))


if __name__ == "__main__":
    unittest.main()
