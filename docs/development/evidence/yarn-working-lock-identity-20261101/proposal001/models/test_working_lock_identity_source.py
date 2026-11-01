#!/usr/bin/env python3
"""New source and mocked identity regressions only; this does not execute Kotlin/JDK/Gradle."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path("convention-plugins/src/main/kotlin/io/github/apdelrahman1911/nativecmpkit/buildlogic/DeclaredYarnClosure.kt")
INPUT_RECEIPT = "    data class InputReceipt(val path: String, val bytes: Int, val sha256: String, internal val cap: Int)"
PRIVATE_IDENTITY = "    private data class Input(val data: ByteArray, val receipt: InputReceipt, val fileKey: Any)"
STORED_CAPTURE = '                val fileKey = before.fileKey() ?: refuse("reader-identity-unavailable", relative)'
READ_RETURN = "                return Input(data, receipt, fileKey)"
ALIAS_REFUSAL = '                if (working.fileKey == stored.fileKey) refuse("working-lock-alias", workingLock)'
TARGET_SOURCE = ""
MODE = ""

def source_at(candidate: str) -> str:
    path = ROOT / candidate / SOURCE
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024:
        raise ValueError("owned-source-shape-refused")
    return path.read_text(encoding="utf-8")

def boundary(source: str) -> str:
    start = source.index("        fun requireWorkingLock(")
    end = source.index("    /** Graph-ready lock-only gate", start)
    return source[start:end]

def select_mode(source: str) -> str:
    # This manually scoped model accepts only the exact observed before/after boundary text.
    # Source text is read as data; no Kotlin is evaluated or translated.
    actual = boundary(source)
    if actual == boundary(source_at("before")):
        return "original-byte-only-boundary"
    if actual == boundary(source_at("proposal")):
        return "proposed-identity-boundary"
    raise ValueError("unreviewed-boundary-model-refused")

@dataclass(frozen=True)
class MockNode:
    data: bytes
    file_key: tuple[str, int]

@dataclass(frozen=True)
class MockReceipt:
    path: str
    bytes: int
    sha256: str

class MockRejection(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code

class MockReader:
    def __init__(self, nodes: dict[str, MockNode]):
        self.nodes = dict(nodes)
        self.reads: list[str] = []

    def read(self, path: str) -> tuple[MockNode, MockReceipt]:
        self.reads.append(path)
        if path not in self.nodes:
            raise MockRejection("input-missing")
        node = self.nodes[path]
        return node, MockReceipt(path, len(node.data), hashlib.sha256(node.data).hexdigest())

def require_same(expected: MockReceipt, actual: MockReceipt) -> None:
    if expected != actual:
        raise MockRejection("checked-input-changed")

def modeled_boundary(reader: MockReader, inputs: tuple[MockReceipt, ...], working: str) -> MockReceipt:
    # File I/O, identity acquisition and resource isolation are deliberately mocked.
    for expected in inputs:
        _, actual = reader.read(expected.path)
        require_same(expected, actual)
    if MODE == "proposed-identity-boundary":
        stored, fresh_stored = reader.read(inputs[0].path)
        require_same(inputs[0], fresh_stored)
        node, actual = reader.read(working)
        if node.file_key == stored.file_key:
            raise MockRejection("working-lock-alias")
    elif MODE == "original-byte-only-boundary":
        _, actual = reader.read(working)
    else:
        raise AssertionError("unreviewed-model-mode")
    if actual.bytes != inputs[0].bytes or actual.sha256 != inputs[0].sha256:
        raise MockRejection("working-lock-mismatch")
    return actual

def fixture(working_key: tuple[str, int] | None = None) -> tuple[MockReader, tuple[MockReceipt, ...]]:
    nodes = {
        "store/yarn.lock": MockNode(b"# yarn lockfile v1\n\n", ("mock-volume", 17)),
        "generated/package.json": MockNode(b'{"name":"MockRoot","version":"1.0.0","private":true}', ("mock-volume", 18)),
    }
    if working_key is not None:
        nodes["generated/yarn.lock"] = MockNode(nodes["store/yarn.lock"].data, working_key)
    reader = MockReader(nodes)
    inputs = tuple(reader.read(name)[1] for name in ("store/yarn.lock", "generated/package.json"))
    reader.reads.clear()
    return reader, inputs

class NewWorkingIdentitySourceAndMockTests(unittest.TestCase):
    def test_validated_regular_file_identity_is_retained_privately(self) -> None:
        self.assertIn(INPUT_RECEIPT, TARGET_SOURCE)
        self.assertIn(PRIVATE_IDENTITY, TARGET_SOURCE)
        self.assertIn(STORED_CAPTURE, TARGET_SOURCE)
        self.assertIn(READ_RETURN, TARGET_SOURCE)
        self.assertIn("fileKey != after.fileKey()", TARGET_SOURCE)
        self.assertNotIn("fileKey", INPUT_RECEIPT)

    def test_working_refusal_binds_fresh_stored_identity_before_byte_acceptance(self) -> None:
        action = boundary(TARGET_SOURCE)
        required = [
            "            recheck()",
            "                val stored = reader.read(inputs.first().path, inputs.first().cap)",
            "                requireSame(inputs.first(), stored.receipt)",
            "                val working = reader.read(workingLock, inputs.first().cap)",
            ALIAS_REFUSAL,
            "                val actual = working.receipt",
            "                if (actual.bytes != inputs.first().bytes || actual.sha256 != inputs.first().sha256)",
            '                    refuse("working-lock-mismatch", workingLock)',
        ]
        positions = [action.index(fragment) if fragment in action else -1 for fragment in required]
        self.assertTrue(all(position >= 0 for position in positions), "missing-owning-identity-boundary")
        self.assertEqual(sorted(positions), positions)
        self.assertNotIn("Files.isSameFile", action)

    def test_stored_path_cannot_substitute_for_an_absent_working_copy(self) -> None:
        reader, inputs = fixture()
        before = dict(reader.nodes)
        with self.assertRaises(MockRejection) as caught:
            modeled_boundary(reader, inputs, "store/yarn.lock")
        self.assertEqual("working-lock-alias", caught.exception.code)
        self.assertNotIn("generated/yarn.lock", reader.nodes)
        self.assertEqual(before, reader.nodes)

    def test_distinct_hard_link_paths_cannot_pass_only_by_equal_bytes(self) -> None:
        reader, inputs = fixture(("mock-volume", 17))
        before = dict(reader.nodes)
        self.assertEqual(reader.nodes["store/yarn.lock"].data, reader.nodes["generated/yarn.lock"].data)
        with self.assertRaises(MockRejection) as caught:
            modeled_boundary(reader, inputs, "generated/yarn.lock")
        self.assertEqual("working-lock-alias", caught.exception.code)
        self.assertEqual(before, reader.nodes)

    def test_independent_equal_byte_copies_remain_admitted(self) -> None:
        # The entire provider key is compared: an equal file number on another volume is distinct.
        for key in (("mock-volume", 19), ("other-mock-volume", 17)):
            with self.subTest(mock_key=key):
                reader, inputs = fixture(key)
                before = dict(reader.nodes)
                actual = modeled_boundary(reader, inputs, "generated/yarn.lock")
                self.assertEqual("generated/yarn.lock", actual.path)
                self.assertEqual(inputs[0].sha256, actual.sha256)
                self.assertEqual(before, reader.nodes)
                expected_reads = ["store/yarn.lock", "generated/package.json"]
                if MODE == "proposed-identity-boundary":
                    expected_reads.append("store/yarn.lock")
                expected_reads.append("generated/yarn.lock")
                self.assertEqual(expected_reads, reader.reads)

class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.records: list[dict[str, str]] = []

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        self.records.append({"method": test.id(), "outcome": "pass"})

    def addFailure(self, test: unittest.TestCase, err: tuple) -> None:
        super().addFailure(test, err)
        self.records.append({"method": test.id(), "outcome": "failure"})

    def addError(self, test: unittest.TestCase, err: tuple) -> None:
        super().addError(test, err)
        self.records.append({"method": test.id(), "outcome": "error"})

def denied(*args: object, **kwargs: object) -> None:
    raise AssertionError("real-network-or-child-process-is-forbidden-in-these-models")

def main() -> int:
    global TARGET_SOURCE, MODE
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, choices=("before", "proposal"))
    parser.add_argument("--receipt", required=True, choices=("source-mock-red.json", "source-mock-green.json"))
    args = parser.parse_args()
    TARGET_SOURCE = source_at(args.candidate)
    MODE = select_mode(TARGET_SOURCE)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NewWorkingIdentitySourceAndMockTests)
    stream = io.StringIO()
    started = datetime.now(timezone.utc)
    with patch.object(socket, "socket", denied), patch.object(socket, "create_connection", denied), \
            patch.object(subprocess, "Popen", denied), patch.object(subprocess, "run", denied), \
            patch.object(subprocess, "call", denied), patch.object(subprocess, "check_call", denied), \
            patch.object(subprocess, "check_output", denied):
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordingResult).run(suite)
    finished = datetime.now(timezone.utc)
    receipt = {
        "schema": 1,
        "record_type": "new-Kotlin-source-and-mocked-file-identity-regressions",
        "candidate": args.candidate,
        "source_sha256": hashlib.sha256(TARGET_SOURCE.encode()).hexdigest(),
        "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_mode": MODE,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "elapsed_seconds": (finished-started).total_seconds(),
        "methods": result.records,
        "method_count": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "real_socket_or_child_creation_denied_during_models": True,
        "new_Gradle_Kotlin_JVM_SDK_native_browser_install_or_dispatch": 0,
        "actual_filesystem_identity_or_hardlink_behavior_verified": False,
        "network_RSS_cleanup_dependency_security_or_issue_closure_verified": False,
        "accepted_suite_replayed": False,
    }
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    (results/args.receipt).write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    (results/(args.receipt.removesuffix(".json")+".log")).write_text(stream.getvalue())
    print(json.dumps({key:receipt[key] for key in ("candidate","method_count","failures","errors","skipped","model_mode")}))
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())

