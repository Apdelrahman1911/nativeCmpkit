"""Run only named new private controls, recording no error bodies or tracebacks."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import unittest


class FactsOnlyResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.facts = []

    def addSuccess(self, test):
        self.facts.append({"test": test.id(), "status": "passed"})

    def addFailure(self, test, err):
        self.failures.append((test, None))
        self.facts.append({"test": test.id(), "status": "failed", "error_class": type(err[1]).__name__})

    def addError(self, test, err):
        self.errors.append((test, None))
        self.facts.append({"test": test.id(), "status": "error", "error_class": type(err[1]).__name__})

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.errors.append((test, None))
            self.facts.append({"test": test.id(), "status": "subtest-error", "error_class": type(err[1]).__name__})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--test-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--method")
    arguments = parser.parse_args()
    os.environ["CAMERA_REQUIRE_ORIGIN_MODEL_TREE"] = str(arguments.tree.resolve())
    spec = importlib.util.spec_from_file_location("camera_require_origin_new_controls", arguments.test_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if arguments.method:
        suite = unittest.defaultTestLoader.loadTestsFromName(
            "CameraPrerequisiteRequireOriginTests." + arguments.method, module)
    else:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.CameraPrerequisiteRequireOriginTests)
    selected = suite.countTestCases()
    result = FactsOnlyResult()
    start = time.monotonic()
    suite.run(result)
    record = {"schema": "nativecmpkit.private-camera-require-origin-model-results.v1",
              "selected": selected, "executed": result.testsRun, "passed": result.wasSuccessful(),
              "elapsed_seconds": round(time.monotonic() - start, 6), "results": result.facts,
              "python_version": ".".join(map(str, sys.version_info[:3])),
              "helper_sha256": digest(arguments.tree / "scripts/ci/android_camera_developer_prerequisite.py"),
              "controller_sha256": digest(arguments.tree / "scripts/ci/android_device_tests.py"),
              "test_sha256": digest(arguments.test_file), "runner_sha256": digest(Path(__file__)),
              "synthetic_only": True, "accepted_suite_replayed": False, "actual_condition_inferred": False,
              "project_live_module_imported": False, "native_or_sdk_executions": 0,
              "error_bodies_tracebacks_argv_results_environment_or_machine_paths_exported": False}
    arguments.output.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: record[key] for key in ("selected", "executed", "passed", "elapsed_seconds",
                                                   "helper_sha256", "test_sha256")}, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
