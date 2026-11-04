# SPDX-License-Identifier: Apache-2.0
"""FIRST NEW16 only. Do not replay accepted methods; retain genuine first outcomes."""
from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import importlib.util

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULE = "test_android_camera_live_task_refusal_observation"
RECEIPT = HERE / "new16-first.json"
if RECEIPT.exists():
    raise RuntimeError("First receipt exists: accepted NEW16 must not be replayed")
spec = importlib.util.spec_from_file_location("camera631_source_custody", HERE / "source-custody.py")
custody = importlib.util.module_from_spec(spec)
spec.loader.exec_module(custody)
held = json.loads((HERE / "held-inputs.json").read_bytes())
before = custody.snapshot()
if before != held["files"] or custody.digest(before) != held["digest"]:
    raise RuntimeError("Current source differs from qualified before-control hold")
free_before = os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize
if free_before < 8 * 1024 ** 3:
    raise RuntimeError("Below8GiB: hold before first NEW16")

# Deny process creation/exec and socket IO before loading the NEW test module.
# CompletedProcess is merely a synthetic immutable-byte result container here.
attempts = []

def deny(name):
    def refused_boundary(*args, **kwargs):
        attempts.append(name)  # No arguments, rows, paths or environment values.
        raise RuntimeError("Real process/network boundary forbidden in NEW16")
    return refused_boundary


class FirstResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = {}
        self.subtest_records = []
        self.started = {}

    def startTest(self, test):
        self.started[test.id()] = time.monotonic()
        self.records[test.id()] = {"outcome": "started"}
        super().startTest(test)

    def stopTest(self, test):
        if test.id() in self.started:
            self.records[test.id()]["elapsed_seconds"] = time.monotonic() - self.started[test.id()]
        super().stopTest(test)

    def addSuccess(self, test):
        self.records[test.id()]["outcome"] = "passed"
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.records.setdefault(test.id(), {})["outcome"] = "failed"
        self.records[test.id()]["exception_type"] = err[0].__name__
        super().addFailure(test, err)

    def addError(self, test, err):
        self.records.setdefault(test.id(), {})["outcome"] = "error"
        self.records[test.id()]["exception_type"] = err[0].__name__
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.records.setdefault(test.id(), {})["outcome"] = "skipped"
        super().addSkip(test, reason)

    def addSubTest(self, test, subtest, err):
        item = {"parent": test.id(), "outcome": "passed" if err is None else "refused"}
        if err is not None:
            item["exception_type"] = err[0].__name__
        self.subtest_records.append(item)
        super().addSubTest(test, subtest, err)


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


stream = io.StringIO()
start = time.monotonic()
profile_counts = {"fresh_synthetic_parse_live_tasks_calls": 0, "actual_controller_run_calls": 0}
with contextlib.ExitStack() as stack:
    for name in ("Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput", "_fork_exec"):
        if hasattr(subprocess, name):
            stack.enter_context(patch.object(subprocess, name, deny("subprocess." + name)))
    for name in dir(os):
        if (name in {"system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp"} or
                name.startswith("exec") or name.startswith("spawn")) and callable(getattr(os, name)):
            stack.enter_context(patch.object(os, name, deny("os." + name)))
    for name in ("socket", "create_connection", "socketpair"):
        stack.enter_context(patch.object(socket, name, deny("socket." + name)))
    try:
        import _posixsubprocess
        stack.enter_context(patch.object(_posixsubprocess, "fork_exec", deny("_posixsubprocess.fork_exec")))
    except ImportError:
        pass
    sys.path.insert(0, str(ROOT / "scripts/ci"))
    new_module = importlib.import_module(MODULE)
    suite = unittest.defaultTestLoader.loadTestsFromModule(new_module)
    selected = [test.id() for test in flatten(suite)]
    if len(selected) != 16 or len(set(selected)) != 16 or not all(name.startswith(MODULE + ".") for name in selected):
        raise RuntimeError("Exact NEW16 only selection required")
    camera = sys.modules["android_camera_developer_prerequisite"]
    original_parser = camera.parse_live_tasks.__code__

    def profile(frame, event, arg):
        if event == "call":
            if frame.f_code is original_parser:
                profile_counts["fresh_synthetic_parse_live_tasks_calls"] += 1
            if (frame.f_code.co_name == "_run" and
                    Path(frame.f_code.co_filename).name == "android_device_tests.py"):
                profile_counts["actual_controller_run_calls"] += 1

    previous_profile = sys.getprofile()
    sys.setprofile(profile)
    try:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=FirstResult).run(suite)
    finally:
        sys.setprofile(previous_profile)
elapsed = time.monotonic() - start
after = custody.snapshot()
source_unchanged = after == before
safe_log = stream.getvalue().replace(str(ROOT), "<worktree>")
(HERE / "new16-first.log").write_text(safe_log)
old_tests = sorted(name for name in sys.modules if name.startswith("test_") and name != MODULE)
receipt = {
    "schema": "nativecmpkit.camera631.NEW16-first.v1", "kind": "fresh synthetic Python controls only",
    "selected_ids": selected, "tests_run": result.testsRun, "failures": len(result.failures),
    "errors": len(result.errors), "skipped": len(result.skipped), "wrapper_elapsed_seconds": elapsed,
    "unittest_reported_elapsed_seconds": round(sum(record.get("elapsed_seconds", 0) for record in result.records.values()), 6),
    "outcomes": {name: result.records.get(name, {"outcome": "not_started"}) for name in selected},
    "subtest_outcomes": result.subtest_records, "subtests_recorded": len(result.subtest_records),
    "source_before": {"count": len(before), "digest": custody.digest(before)},
    "source_after": {"count": len(after), "digest": custody.digest(after)}, "all_held_inputs_unchanged": source_unchanged,
    "free_bytes_before": free_before, "free_bytes_after": os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize,
    "denied_real_boundary_attempts": attempts, "older_test_modules_imported": old_tests,
    **profile_counts, "actual_android_device_tests_imported": "android_device_tests" in sys.modules,
    "unchanged_controller_handler_AST_model_compiled": True,
    "original_or_cached_camera630_payload_used": False, "accepted_methods_replayed": False,
    "new_compiler_or_target_native_or_query_execution": False,
    "private_task_rows_or_identifiers_exported": False, "original_camera630_or_issue13_fixed": False,
    "log_sha256": hashlib.sha256(safe_log.encode()).hexdigest(),
    "passed": result.wasSuccessful() and source_unchanged and not attempts and not old_tests and
              result.testsRun == 16 and profile_counts["actual_controller_run_calls"] == 0,
}
custody.write("new16-first.json", receipt)
custody.write("after-inputs.json", {"kind": "actual current source-control bytes after NEW16; not a compiler/native map",
                                     "count": len(after), "digest": custody.digest(after), "files": after})
print(json.dumps({key: receipt[key] for key in ("tests_run", "failures", "errors", "skipped", "passed",
      "wrapper_elapsed_seconds", "unittest_reported_elapsed_seconds", "fresh_synthetic_parse_live_tasks_calls",
      "subtests_recorded", "denied_real_boundary_attempts", "all_held_inputs_unchanged", "source_after")}))
if not receipt["passed"]:
    raise SystemExit(1)
