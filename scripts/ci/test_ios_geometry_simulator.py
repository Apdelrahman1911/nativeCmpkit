# SPDX-License-Identifier: Apache-2.0
"""Synthetic command/lifecycle controls, never actual macOS/simulator passes."""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

import ios_geometry_simulator as owned
import runtime_context

SOURCE = "11111111-1111-1111-1111-111111111111"
OTHER = "33333333-3333-3333-3333-333333333333"
CREATED = "22222222-2222-2222-2222-222222222222"
RUNTIME = "com.apple.CoreSimulator.SimRuntime.iOS-26-5"
ENVIRONMENT = {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": "Apdelrahman1911/nativeCmpkit",
    "GITHUB_REF": "refs/heads/development/preview-hardening", "GITHUB_EVENT_NAME": "workflow_dispatch",
    "GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "41700000000", "GITHUB_RUN_ATTEMPT": "1"}


class SimulatedInventory:
    """In-memory fake simctl: no SDK, process, device or native library operation."""
    def __init__(self, kind="iphone"):
        self.rows = {
            SOURCE: {"udid": SOURCE, "name": "PRIVATE ORIGINAL USER NAME", "state": "Shutdown",
                "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType." +
                    ("iPhone-Air" if kind == "iphone" else "iPad-mini-A17-Pro"), "dataPath": "/private/fixture/data"},
            OTHER: {"udid": OTHER, "name": "PRIVATE OTHER USER NAME", "state": "Shutdown",
                "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
        }
        self.runtime_rows = {"runtimes": [{"identifier": RUNTIME, "version": "26.5",
            "buildversion": "23F77", "isAvailable": True, "bundlePath": "/private/fixture/runtime"}]}
        self.calls = []
        self.failure = None
        self.terminal_mode = "finished"
        self.created_type = None
        self.returned_uuid = CREATED
        self.post_boot_state = "Booted"

    def documents(self):
        return {"devices": {RUNTIME: list(copy.deepcopy(self.rows).values())}}, copy.deepcopy(self.runtime_rows)

    def execute(self, arguments, timeout):
        self.calls.append((arguments, timeout))
        verb = arguments[2]
        if self.failure == verb:
            raise subprocess.TimeoutExpired(arguments, timeout, output=b"PRIVATE FAILURE BODY")
        stdout = b""
        if verb == "list":
            stdout = json.dumps(self.documents()[0 if arguments[3] == "devices" else 1]).encode()
        elif verb == "create":
            self.rows[CREATED] = {"udid": CREATED, "name": arguments[3], "state": "Shutdown", "isAvailable": True,
                "deviceTypeIdentifier": self.created_type or arguments[4]}
            stdout = (self.returned_uuid + "\n").encode()
        elif verb == "boot":
            self.rows[arguments[3]]["state"] = self.post_boot_state
        elif verb == "bootstatus":
            header = f"Monitoring boot status for {self.rows[CREATED]['name']} ({CREATED}).\n"
            if self.terminal_mode == "already":
                body = "Device already booted, skipping.\n"
            elif self.terminal_mode == "failed":
                body = "[2026-11-04 01:20:00 +0000] Status=3, isTerminal=YES, Elapsed=01:27.\n\tData Migration Failed\n"
            else:
                body = "[2026-11-04 01:20:00 +0000] Status=4294967295, isTerminal=YES, Elapsed=01:43.\n\tFinished\n"
            stdout = (header + body).encode()
        elif verb == "shutdown":
            self.rows[arguments[3]]["state"] = "Shutdown"
        elif verb == "delete":
            del self.rows[arguments[3]]
        else:
            raise AssertionError("A foreign SDK operation reached the fake")
        return subprocess.CompletedProcess(arguments, 0, stdout, b"")


class OwnedGeometryLifecycleControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.addCleanup(patch.stopall)
        patch.object(owned.platform, "system", return_value="Darwin").start()
        patch.object(owned.platform, "machine", return_value="arm64").start()
        patch.dict(os.environ, ENVIRONMENT, clear=True).start()
        self.fake = SimulatedInventory()
        patch.object(owned, "execute", side_effect=lambda *args: self.fake.execute(*args)).start()
        self.write_selection()

    def write_selection(self, kind="iphone"):
        documents = self.fake.documents()
        source = runtime_context.simulator(*documents, kind=kind, udid=SOURCE)
        selection = {"schema_version": 1, "source_revision": "a" * 40, "source_tree_dirty": False,
            "host": {"system": "Darwin", "architecture": "arm64"}, "java": {"major": 17}, "simulator": source}
        target = self.root / owned.SELECTION
        target.parent.mkdir(parents=True, exist_ok=True); target.write_text(json.dumps(selection))

    def controller(self, index=0):
        return owned.OwnedGeometrySimulator(self.root, tuple(owned.FOCUSES)[index])

    def lease(self):
        return json.loads((self.root / owned.LEASE).read_bytes())

    def write_lease(self, document):
        (self.root / owned.LEASE).write_text(json.dumps(document))

    def mutations(self):
        return [args for args, _ in self.fake.calls if args[2] != "list"]

    def test_same_type_runtime_new_uuid_and_cleanup_preserve_every_original_device(self):
        original = copy.deepcopy(self.fake.rows)
        controller = self.controller(); record = controller.prepare()
        self.assertTrue(record["prepared"]); self.assertEqual(CREATED, record["owned_udid"])
        self.assertFalse(record["boot_terminal"]["readiness_verified"])
        self.assertNotIn("PRIVATE", json.dumps(record)); self.assertNotIn("/private", json.dumps(record))
        result = self.controller().cleanup()
        self.assertTrue(result["cleanup_passed"]); self.assertTrue(result["owned_deleted"])
        self.assertEqual(original, self.fake.rows)
        self.assertEqual(["create", "boot", "bootstatus", "shutdown", "delete"], [a[2] for a in self.mutations()])
        self.assertEqual(SOURCE, self.lease()["source_simulator"]["udid"])
        for arguments in self.mutations()[1:]: self.assertEqual(CREATED, arguments[3])

    def test_ipad_uses_exact_recorded_type_runtime_not_a_phone_or_source_uuid(self):
        self.fake = SimulatedInventory("ipad"); self.write_selection("ipad")
        record = self.controller(1).prepare()
        create = self.mutations()[0]
        self.assertEqual("com.apple.CoreSimulator.SimDeviceType.iPad-mini-A17-Pro", create[4])
        self.assertEqual(RUNTIME, create[5]); self.assertEqual(CREATED, record["owned_udid"])
        self.assertTrue(self.controller(1).cleanup()["cleanup_passed"])

    def test_zero_exit_terminal_migration_failure_preserves_primary_and_runs_only_owned_disposal(self):
        self.fake.terminal_mode = "failed"; self.fake.post_boot_state = "Booting"
        with self.assertRaisesRegex(ValueError, "Terminal simulator boot failed despite command exit zero"):
            self.controller().prepare()
        record = self.lease(); self.assertFalse(record["prepared"])
        self.assertEqual(3, record["boot_terminal"]["terminal_status"])
        self.assertTrue(record["boot_terminal"]["data_migration_failed"])
        self.assertEqual("bootstatus", record["primary_failure"]["phase"])
        primary = copy.deepcopy(record["primary_failure"])
        self.assertTrue(self.controller().cleanup()["cleanup_passed"])
        self.assertEqual(primary, self.lease()["primary_failure"])
        self.assertFalse(self.lease()["prepared"])

    def test_finished_and_already_booted_words_still_require_actual_booted_inventory(self):
        self.fake.terminal_mode = "already"
        self.assertTrue(self.controller().prepare()["prepared"])
        self.assertTrue(self.controller().cleanup()["cleanup_passed"])
        with tempfile.TemporaryDirectory() as directory:
            self.root = Path(directory); self.fake = SimulatedInventory(); self.write_selection()
            self.fake.post_boot_state = "Shutdown"
            with self.assertRaisesRegex(ValueError, "Actual owned Booted state"):
                self.controller().prepare()
            self.assertFalse(self.lease()["prepared"])
            self.assertTrue(self.controller().cleanup()["cleanup_passed"])

    def test_expired_boot_is_not_retried_or_replaced_and_owned_cleanup_keeps_failure(self):
        self.fake.failure = "bootstatus"
        with self.assertRaises(subprocess.TimeoutExpired): self.controller().prepare()
        self.assertEqual(1, sum(a[2] == "bootstatus" for a, _ in self.fake.calls))
        self.assertEqual(1, sum(a[2] == "create" for a, _ in self.fake.calls))
        self.assertTrue(next(c for c in self.lease()["commands"] if c["command"] == "bootstatus")["timed_out"])
        self.fake.failure = None
        self.assertTrue(self.controller().cleanup()["cleanup_passed"])
        self.assertEqual("TimeoutExpired", self.lease()["primary_failure"]["type"])

    def test_unacknowledged_creation_never_guesses_a_uuid_from_inventory_for_cleanup(self):
        self.fake.returned_uuid = ""
        with self.assertRaisesRegex(ValueError, "Creation must return one new"):
            self.controller().prepare()
        self.assertFalse(self.lease()["creation_returned"])
        count = len(self.fake.calls)
        with self.assertRaisesRegex(ValueError, "Unknown, preinstalled or unacknowledged"):
            self.controller().cleanup()
        self.assertEqual(count, len(self.fake.calls))

    def test_preexisting_returned_uuid_cannot_be_booted_shutdown_or_deleted(self):
        self.fake.returned_uuid = SOURCE
        with self.assertRaises(ValueError): self.controller().prepare()
        self.assertEqual(["create"], [a[2] for a in self.mutations()])
        with self.assertRaises(ValueError): self.controller().cleanup()
        self.assertIn(SOURCE, self.fake.rows); self.assertIn(OTHER, self.fake.rows)

    def test_foreign_created_identity_cannot_silently_substitute_platform_or_cleanup_target(self):
        self.fake.created_type = "com.apple.CoreSimulator.SimDeviceType.iPad-mini-A17-Pro"
        with self.assertRaises(ValueError): self.controller().prepare()
        before = len(self.mutations())
        with self.assertRaises(ValueError): self.controller().cleanup()
        self.assertEqual(before, len(self.mutations()))

    def test_original_state_drift_fails_acceptance_but_safe_owned_disposal_is_independent(self):
        self.controller().prepare(); self.fake.rows[OTHER]["state"] = "Booted"
        result = self.controller().cleanup()
        self.assertTrue(result["owned_deleted"]); self.assertFalse(result["cleanup_passed"])
        self.assertFalse(result["nonowned_preserved"]); self.assertIn(OTHER, self.fake.rows)
        self.assertEqual("Booted", self.fake.rows[OTHER]["state"])

    def test_changed_or_boolean_scope_and_forged_baseline_refuse_before_cleanup_commands(self):
        self.controller().prepare(); original = self.lease(); count = len(self.fake.calls)
        for field, value in (("run_id", 41700000001), ("run_attempt", True), ("source_sha", "b" * 40), ("kind", "ipad")):
            changed = copy.deepcopy(original); changed["scope"][field] = value; self.write_lease(changed)
            with self.assertRaises(ValueError): self.controller().cleanup()
            self.assertEqual(count, len(self.fake.calls))
        changed = copy.deepcopy(original); changed["baseline"]["devices"][CREATED] = changed["baseline"]["devices"][SOURCE]
        self.write_lease(changed)
        with self.assertRaises(ValueError): self.controller().cleanup()
        self.assertEqual(count, len(self.fake.calls))
        self.write_lease(original); self.assertTrue(self.controller().cleanup()["cleanup_passed"])

    def test_second_prepare_and_cleanup_cannot_overwrite_or_replay_an_existing_lease(self):
        self.controller().prepare(); record = (self.root / owned.LEASE).read_bytes(); count = len(self.fake.calls)
        with self.assertRaises(ValueError): self.controller().prepare()
        self.assertEqual(record, (self.root / owned.LEASE).read_bytes()); self.assertEqual(count, len(self.fake.calls))
        self.assertTrue(self.controller().cleanup()["cleanup_passed"]); count = len(self.fake.calls)
        with self.assertRaises(ValueError): self.controller().cleanup()
        self.assertEqual(count, len(self.fake.calls))

    def test_no_lease_admits_no_cleanup_actions_or_native_acceptance(self):
        result = self.controller().cleanup()
        self.assertEqual("no-owned-lease", result["status"]); self.assertFalse(result["native_acceptance"])
        self.assertEqual([], self.fake.calls)

    def test_only_exact_lifecycle_commands_are_allowed_and_each_mutation_is_one_shot(self):
        controller = self.controller(); controller.prepare(); count = len(self.fake.calls)
        for kind, args in (("erase", (owned.XCRUN, "simctl", "erase", CREATED)),
                           ("delete", (owned.XCRUN, "simctl", "delete", SOURCE)),
                           ("boot", (owned.XCRUN, "simctl", "boot", CREATED)),
                           ("list-devices", (owned.XCRUN, "simctl", "list", "devices")),
                           ("list-devices", [owned.XCRUN, "simctl", "list", "devices", "--json"])):
            with self.assertRaises(ValueError): controller.command(kind, args)
            self.assertEqual(count, len(self.fake.calls))

    def test_all_command_budgets_remain_finite_and_existing_runtime_checks_are_not_widened(self):
        self.controller().prepare(); self.controller().cleanup()
        for arguments, timeout in self.fake.calls:
            name = "list-" + arguments[3] if arguments[2] == "list" else arguments[2]
            self.assertEqual(owned.BUDGETS[name], timeout)
        with patch.object(runtime_context.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "", "")
            runtime_context.command("git", "status", "--porcelain", "--untracked-files=normal")
            self.assertEqual(60, run.call_args.kwargs["timeout"])

    def test_dirty_preboot_source_or_wrong_kind_fails_before_any_simulator_mutation(self):
        path = self.root / owned.SELECTION; selection = json.loads(path.read_bytes())
        changed = copy.deepcopy(selection); changed["source_tree_dirty"] = True; path.write_text(json.dumps(changed))
        with self.assertRaises(ValueError): self.controller().prepare()
        self.assertEqual([], self.fake.calls)
        path.write_text(json.dumps(selection))
        with self.assertRaises(ValueError): self.controller(1).prepare()
        self.assertEqual([], self.mutations())

    def test_foreign_ci_scope_cannot_create_an_owned_controller(self):
        for key, value in (("GITHUB_REPOSITORY", "MohamedRejeb/Calf"), ("GITHUB_REF", "refs/heads/main"),
                           ("GITHUB_EVENT_NAME", "push"), ("GITHUB_RUN_ATTEMPT", "0"), ("GITHUB_SHA", "unknown")):
            with patch.dict(os.environ, {key: value}), self.assertRaises(ValueError): self.controller()
        self.assertEqual([], self.fake.calls)

    def test_concurrent_cleanup_claim_allows_only_one_disposal_sequence(self):
        self.controller().prepare(); original_open = os.open; barrier = threading.Barrier(2)
        def synchronized_open(path, flags, mode):
            if Path(path).name == Path(owned.CLEANUP_CLAIM).name:
                barrier.wait(timeout=3)
            return original_open(path, flags, mode)
        def cleanup(_):
            try:
                return self.controller().cleanup()["cleanup_passed"]
            except FileExistsError:
                return None
        with patch.object(owned.os, "open", side_effect=synchronized_open), ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual([True, None], list(pool.map(cleanup, (1, 2))))
        self.assertEqual(1, sum(a[2] == "shutdown" for a in self.mutations()))
        self.assertEqual(1, sum(a[2] == "delete" for a in self.mutations()))
        self.assertTrue(self.lease()["cleanup"]["cleanup_passed"])

    def test_interrupted_cleanup_claim_is_not_retried_after_its_primary_error(self):
        self.controller().prepare(); self.fake.failure = "shutdown"
        with self.assertRaises(subprocess.TimeoutExpired): self.controller().cleanup()
        count = len(self.fake.calls)
        self.assertEqual("TimeoutExpired", self.lease()["cleanup"]["error"]["type"])
        self.assertFalse(self.lease()["cleanup"]["cleanup_passed"])
        with self.assertRaises(ValueError): self.controller().cleanup()
        self.assertEqual(count, len(self.fake.calls)); self.assertIn(CREATED, self.fake.rows)
        # Even an externally restored old receipt cannot replay a claimed action.
        old = self.lease(); old["cleanup"] = None; self.write_lease(old)
        with self.assertRaises(FileExistsError): self.controller().cleanup()
        self.assertEqual(count, len(self.fake.calls))

    def test_lease_symlinks_hardlinks_or_duplicate_fields_refuse_before_commands(self):
        self.controller().prepare(); path = self.root / owned.LEASE; original = path.read_bytes()
        count = len(self.fake.calls); backing = path.with_name("backing.json"); backing.write_bytes(original)
        path.unlink(); path.symlink_to(backing)
        with self.assertRaises(ValueError): self.controller().cleanup()
        self.assertEqual(count, len(self.fake.calls)); path.unlink(); path.hardlink_to(backing)
        with self.assertRaises(ValueError): self.controller().cleanup()
        self.assertEqual(count, len(self.fake.calls)); path.unlink(); backing.unlink()
        path.write_bytes(original.replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'))
        with self.assertRaises(ValueError): self.controller().cleanup()
        self.assertEqual(count, len(self.fake.calls)); path.write_bytes(original)
        self.assertTrue(self.controller().cleanup()["cleanup_passed"])


class OwnedGeometryPureControls(unittest.TestCase):
    def test_terminal_failure_partial_foreign_multiple_and_old_failure_then_finished_cannot_pass(self):
        name = "nativecmpkit-geometry-41700000000-1-iphone"
        header = f"Monitoring boot status for {name} ({CREATED}).\n"
        success = "[2026-11-04 01:20:00 +0000] Status=4294967295, isTerminal=YES, Elapsed=01:43.\nFinished\n"
        failure = "[2026-11-04 01:20:00 +0000] Status=3, isTerminal=YES, Elapsed=01:27.\nData Migration Failed\n"
        self.assertTrue(owned.boot_terminal((header + success).encode(), CREATED, name)["successful"])
        self.assertFalse(owned.boot_terminal((header + failure).encode(), CREATED, name)["successful"])
        for text in ("Finished\n", header + success.replace("Finished\n", ""), header + failure + success,
                     header.replace(CREATED, SOURCE) + success, header + success + "unknown tail\n"):
            with self.assertRaises(ValueError): owned.boot_terminal(text.encode(), CREATED, name)
        self.assertFalse(owned.boot_terminal((header + "Data Migration Failed\n" + success).encode(), CREATED, name)["successful"])

    def test_inventory_names_private_paths_duplicate_ids_and_nonboolean_availability_are_not_admitted(self):
        fake = SimulatedInventory(); documents = fake.documents(); result = owned.inventory_snapshot(*documents)
        self.assertNotIn("PRIVATE", json.dumps(result)); self.assertNotIn("/private", json.dumps(result))
        for value in (1, "true", None):
            changed = copy.deepcopy(documents[0]); changed["devices"][RUNTIME][0]["isAvailable"] = value
            with self.assertRaises(ValueError): owned.inventory_snapshot(changed, documents[1])
        changed = copy.deepcopy(documents[0]); changed["devices"][RUNTIME].append(changed["devices"][RUNTIME][0])
        with self.assertRaises(ValueError): owned.inventory_snapshot(changed, documents[1])

    def test_json_duplicate_nonfinite_empty_and_nonordinary_inputs_refuse(self):
        for raw in (b'{"scope":1,"scope":2}', b'{"scope":NaN}', b"", bytearray(b"{}"), b"x" * (owned.MAX_BYTES + 1)):
            with self.assertRaises(ValueError): owned._json(raw)

    def test_first_lease_creation_is_exclusive_even_when_both_writers_pass_the_existence_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / owned.LEASE).parent.mkdir(parents=True)
            original_open = os.open; barrier = threading.Barrier(2)
            def synchronized_open(path, flags, mode):
                barrier.wait(timeout=3)
                return original_open(path, flags, mode)
            def write(number):
                try:
                    owned._write(root, {"writer": number}, exclusive=True)
                    return number
                except FileExistsError:
                    return None
            with patch.object(owned.os, "open", side_effect=synchronized_open), ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(write, (1, 2)))
            winner = next(result for result in results if result is not None)
            self.assertEqual(1, results.count(None))
            self.assertEqual({"writer": winner}, owned._read(root, owned.LEASE))


if __name__ == "__main__":
    unittest.main()
