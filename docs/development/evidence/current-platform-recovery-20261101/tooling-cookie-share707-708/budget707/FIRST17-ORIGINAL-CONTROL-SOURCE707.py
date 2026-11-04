"""Changed offline-owner regressions; models plus one real Linux child timeout.

No library, device, browser, consumer, authenticated reuse or release acceptance.
"""
import ast
from contextlib import ExitStack, redirect_stderr
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import offline_tooling_reuse as reuse

SCOPE = reuse.SCOPES[3]
GREEN = b"test_control (owner.Control.test_control) ... ok\n\nRan 1 test in 0.001s\n\nOK\n"


def records(output, prefix):
    return [json.loads(line[len(prefix):]) for line in output.splitlines() if line.startswith(prefix)]


class ScopeObservation707Tests(unittest.TestCase):
    def model(self, payload=GREEN, *, seconds=1, clocks=(0, 1), alive=1, foreign=False,
              hooks=(), wait_failure=None, stderr=None, temporary_file=None):
        """Known owned-process model; no modeled PID is ever sent to the kernel."""
        events, failures, result, calls = [], [], None, 0
        process = Mock(pid=24680, returncode=None)
        stream = stderr if stderr is not None else io.StringIO()

        def launch(*args, **kwargs):
            self.assertIs(True, kwargs["start_new_session"])
            kwargs["stdout"].write(payload)
            kwargs["stdout"].flush()
            events.append("started")
            return process

        def retained(kind, pid, flags):
            nonlocal calls
            self.assertEqual(reuse.os.P_PID, kind)
            self.assertEqual(process.pid, pid)
            self.assertTrue(flags & reuse.os.WNOWAIT)
            calls += 1
            if wait_failure is not None and calls == wait_failure:
                raise OSError("controlled retain failure")
            return None if calls <= alive else SimpleNamespace(si_pid=process.pid)

        def reaped(*, timeout):
            self.assertEqual(5, timeout)
            events.append("reaped")
            process.returncode = 0
            return 0

        process.wait.side_effect = reaped
        with ExitStack() as stack:
            stack.enter_context(redirect_stderr(stream))
            stack.enter_context(patch.object(reuse.subprocess, "Popen", side_effect=launch))
            stack.enter_context(patch.object(reuse, "scope_environment", return_value={"PATH": "modeled-fixed-path"}))
            stack.enter_context(patch.object(reuse.os, "waitid", side_effect=retained))
            stack.enter_context(patch.object(reuse.os, "getpgid", return_value=process.pid))
            stack.enter_context(patch.object(reuse.os, "getsid", return_value=process.pid + int(foreign)))
            group = stack.enter_context(patch.object(reuse.os, "killpg", side_effect=lambda pid, sig: events.append((pid, sig))))
            direct = stack.enter_context(patch.object(reuse.os, "kill"))
            stack.enter_context(patch.object(reuse.time, "monotonic", side_effect=clocks))
            stack.enter_context(patch.object(reuse.time, "sleep"))
            if temporary_file is not None:
                stack.enter_context(patch.object(reuse.tempfile, "TemporaryFile", side_effect=temporary_file))
            for hook in hooks:
                stack.enter_context(hook)
            try:
                result = reuse.execute_scope(Path("/not-executed-owned-model"), SCOPE, seconds)
            except BaseException as error:
                failures.append(error)
        process.poll.assert_not_called()
        process.wait.assert_called_once_with(timeout=5)
        return {"result": result, "errors": failures, "stderr": stream.getvalue() if hasattr(stream, "getvalue") else "",
                "events": events, "group": group, "direct": direct}

    def assert_bound_refusal(self, actual):
        self.assertIsNone(actual["result"])
        self.assertEqual(1, len(actual["errors"]))
        self.assertIs(type(actual["errors"][0]), ValueError)
        self.assertEqual("Offline scope exceeded its total time/output bound", str(actual["errors"][0]))
        self.assertEqual("reaped", actual["events"][-1])

    def test_timeout_keeps_short_circuited_output_unknown_and_disposes_owned_group(self):
        actual = self.model(seconds=0)
        self.assert_bound_refusal(actual)
        values = records(actual["stderr"], "[offline-scope] ")
        self.assertEqual(["started", "refused"], [item["event"] for item in values])
        self.assertEqual("wait-guard", values[-1]["phase"])
        self.assertIs(False, values[-1]["time_admitted"])
        self.assertIsNone(values[-1]["output_admitted"])
        self.assertIsNone(values[-1]["guard_output_bytes"])
        self.assertEqual([(24680, reuse.signal.SIGTERM), (24680, reuse.signal.SIGKILL)],
                         [item for item in actual["events"] if isinstance(item, tuple)])
        sampled = records(actual["stderr"], "[offline-scope-buffer] ")[0]
        self.assertIs(True, sampled["sample_is_after_refusal"])
        self.assertIs(False, sampled["complete_output"])
        self.assertIs(False, sampled["original_child_group_disposal_completed"])

    def test_output_refusal_observes_original_guard_bytes_and_never_a_green_result(self):
        actual = self.model(b"x" * 65, clocks=(0, 0.1), hooks=(patch.object(reuse, "MAX_LOG_BYTES", 64),))
        self.assert_bound_refusal(actual)
        refused = records(actual["stderr"], "[offline-scope] ")[-1]
        self.assertIs(True, refused["time_admitted"])
        self.assertIs(False, refused["output_admitted"])
        self.assertEqual(65, refused["guard_output_bytes"])
        self.assertNotIn('"summary_passed":true', actual["stderr"])

    def test_expired_time_does_not_call_fstat_or_claim_an_oversized_output_operand(self):
        actual = self.model(b"x" * 100, seconds=0, hooks=(
            patch.object(reuse, "MAX_LOG_BYTES", 64),
            patch.object(reuse.os, "fstat", side_effect=AssertionError("short-circuited fstat must not run")),
        ))
        self.assert_bound_refusal(actual)
        refused = records(actual["stderr"], "[offline-scope] ")[-1]
        self.assertIsNone(refused["guard_output_bytes"])
        self.assertEqual(65, records(actual["stderr"], "[offline-scope-buffer] ")[0]["buffered_prefix_bytes"])

    def test_broken_stderr_keeps_primary_and_foreign_group_cleanup_note(self):
        class Broken:
            def write(self, _value):
                raise OSError("controlled stderr refusal")
            def flush(self):
                raise OSError("controlled flush refusal")
        actual = self.model(seconds=0, foreign=True, stderr=Broken())
        self.assert_bound_refusal(actual)
        actual["group"].assert_not_called()
        self.assertTrue(any("cleanup also refused: ValueError" in note for note in actual["errors"][0].__notes__))

    def test_buffer_read_failure_is_secondary_and_does_not_replace_the_timeout(self):
        actual = self.model(seconds=0, hooks=(patch.object(reuse.os, "pread", side_effect=OSError("controlled read failure")),))
        self.assert_bound_refusal(actual)
        self.assertIs(False, records(actual["stderr"], "[offline-scope-buffer] ")[0]["buffer_available"])

    def test_miswired_refusal_emitter_cannot_replace_primary_or_skip_group_disposal(self):
        actual = self.model(seconds=0, hooks=(patch.object(reuse, "emit_scope_refusal", side_effect=MemoryError("controlled emitter failure")),))
        self.assert_bound_refusal(actual)
        self.assertEqual(2, actual["group"].call_count)

    def test_finite_heartbeats_are_flushed_without_early_signaling_and_no_completion_clock_claim(self):
        class Flushed(io.StringIO):
            def __init__(self):
                super().__init__(); self.flushes = 0
            def flush(self):
                self.flushes += 1
                return super().flush()
        stream = Flushed()
        actual = self.model(seconds=10000, alive=4, clocks=(0, 61, 122, 183, 244), stderr=stream,
                            hooks=(patch.object(reuse, "MAX_SCOPE_HEARTBEATS", 2),))
        self.assertEqual([], actual["errors"])
        self.assertIs(True, actual["result"]["passed"])
        values = records(actual["stderr"], "[offline-scope] ")
        self.assertEqual(["started", "heartbeat", "heartbeat", "completed"], [item["event"] for item in values])
        self.assertEqual([1, 2], [item["heartbeat_count"] for item in values if item["event"] == "heartbeat"])
        self.assertIsNone(values[-1]["elapsed_seconds"])
        self.assertIsNone(values[-1]["time_admitted"])
        self.assertIs(True, values[-1]["original_child_group_disposal_completed"])
        self.assertGreaterEqual(stream.flushes, 4)
        self.assertEqual(2, actual["group"].call_count)

    def test_fast_success_preserves_exact_summary_despite_all_event_emitter_failures(self):
        actual = self.model(alive=0, clocks=(0,), hooks=(patch.object(reuse, "emit_scope_event", side_effect=OSError("controlled metadata failure")),))
        self.assertEqual([], actual["errors"])
        self.assertEqual(reuse.scope_summary(SCOPE, 0, GREEN), actual["result"])
        self.assertEqual(2, actual["group"].call_count)

    def test_complete_red_summary_stays_red_and_incomplete_headers_do_not_become_metadata_success(self):
        output = b"FAIL: test_failure (owner.Control.test_failure)\nRan 1 test in 0.001s\nFAILED (failures=1)\n"
        actual = self.model(output, alive=0, clocks=(0,))
        self.assertEqual([], actual["errors"])
        self.assertIs(False, actual["result"]["passed"])
        completed = records(actual["stderr"], "[offline-scope] ")[-1]
        self.assertIs(False, completed["summary_passed"])
        self.assertIn("[offline-failure-inventory] ", actual["stderr"])

    def test_refusal_pread_preserves_shared_child_offset_and_never_exports_raw_private_values(self):
        output = b"token=PRIVATE_BUFFER\nFAIL: test_case (test_safe.Control.test_case) (token='PRIVATE_PARAMETER')\n"
        with tempfile.TemporaryFile() as log, redirect_stderr(io.StringIO()) as stream:
            log.write(output); log.seek(2)
            reuse.emit_scope_refusal(log, SCOPE, {}, phase="wait-guard")
            self.assertEqual(2, log.tell())
            log.write(b"Z"); log.seek(0)
            self.assertEqual(output[:2] + b"Z" + output[3:], log.read())
        public = stream.getvalue()
        self.assertNotIn("PRIVATE_BUFFER", public)
        self.assertNotIn("PRIVATE_PARAMETER", public)
        sampled = records(public, "[offline-scope-buffer] ")[0]
        self.assertEqual(hashlib.sha256(output).hexdigest(), sampled["buffered_prefix_sha256"])
        self.assertEqual(len(output), sampled["buffered_prefix_bytes"])
        self.assertIs(False, sampled["shared_file_offset_changed"])

    def test_unknown_scope_phase_and_event_cannot_read_or_export_caller_strings(self):
        with redirect_stderr(io.StringIO()) as stream, patch.object(reuse.os, "pread") as read:
            for scope, phase, event in (
                (("token=PRIVATE_SCOPE", "test_*.py"), "wait-guard", "refused"),
                (list(SCOPE), "wait-guard", "refused"),
                (SCOPE, "token=PRIVATE_PHASE", "refused"),
                (SCOPE, "wait-guard", "token=PRIVATE_EVENT"),
            ):
                reuse.emit_scope_event(scope, event, phase=phase)
                reuse.emit_scope_refusal(Mock(), scope, {}, phase=phase, event=event)
            read.assert_not_called()
            self.assertEqual("", stream.getvalue())

    def test_completed_oversize_keeps_original_disposal_order_and_uses_no_closed_fd(self):
        with patch.object(reuse.os, "pread", side_effect=AssertionError("post-context pread must not run")) as read:
            actual = self.model(GREEN * 2, alive=0, clocks=(0,), hooks=(patch.object(reuse, "MAX_LOG_BYTES", 64),))
        self.assertIs(type(actual["errors"][0]), ValueError)
        self.assertEqual("Unbounded/unknown scope outcome", str(actual["errors"][0]))
        self.assertEqual(2, actual["group"].call_count)
        read.assert_not_called()
        refused = records(actual["stderr"], "[offline-scope] ")[-1]
        self.assertEqual("post-cleanup-summary", refused["phase"])
        self.assertIs(True, refused["original_child_group_disposal_completed"])
        self.assertIs(False, records(actual["stderr"], "[offline-scope-buffer] ")[0]["sample_is_after_refusal"])

    def test_next_retain_refusal_does_not_report_prior_loop_operands_as_current(self):
        actual = self.model(alive=1, clocks=(0, 0.1), wait_failure=2)
        self.assertIs(type(actual["errors"][0]), OSError)
        refused = records(actual["stderr"], "[offline-scope] ")[-1]
        self.assertEqual("retain-child", refused["phase"])
        for key in ("time_admitted", "output_admitted", "guard_output_bytes", "elapsed_seconds"):
            self.assertIsNone(refused[key])
        self.assertEqual(2, actual["group"].call_count)

    def test_event_and_inventory_public_caps_reject_unqualified_helper_output(self):
        helper = SimpleNamespace(failure_inventory_line=lambda _output: "[offline-failure-inventory] " + "x" * 65537)
        with redirect_stderr(io.StringIO()) as stream, patch.dict(sys.modules, {"offline_tooling_failure_inventory": helper}):
            reuse.emit_scope_failure_inventory(b"controlled bytes")
        self.assertIn('"status":"unknown"', stream.getvalue())
        self.assertNotIn("x" * 100, stream.getvalue())
        with redirect_stderr(io.StringIO()) as stream, patch.object(reuse, "MAX_SCOPE_EVENT_BYTES", 64):
            reuse.emit_scope_event(SCOPE, "started", {"elapsed_seconds": float("nan"), "allocated_seconds": float("inf")})
        self.assertEqual("", stream.getvalue())

    def test_owned_temporary_context_failure_precedes_summary_validation_as_before(self):
        actual_file = tempfile.TemporaryFile
        class RefusingContext:
            def __init__(self):
                self.file = actual_file()
            def __enter__(self):
                return self.file
            def __exit__(self, *_args):
                self.file.close()
                raise OSError("controlled owned-context refusal")
        with patch.object(reuse, "scope_summary", side_effect=AssertionError("context disposal must precede summary")) as summary:
            actual = self.model(alive=0, clocks=(0,), temporary_file=RefusingContext)
        self.assertIs(type(actual["errors"][0]), OSError)
        summary.assert_not_called()
        self.assertEqual(2, actual["group"].call_count)
        self.assertNotIn('"event":"completed"', actual["stderr"])

    def test_shared_budget_preserves_all_ten_scopes_and_changes_only_tooling_timeout(self):
        self.assertEqual(1500, reuse.TOTAL_SCOPE_SECONDS)
        self.assertEqual(16 * 1024**2, reuse.MAX_LOG_BYTES)
        self.assertEqual(32, reuse.MAX_SCOPE_HEARTBEATS)
        self.assertEqual(10, len(reuse.SCOPES))
        self.assertEqual(tuple((path, "test_*.py") for path in (
            "scripts/audit", "scripts/migration", "scripts/development", "scripts/ci", "scripts/native",
            "scripts/dependencies", "scripts/dependencies/yarn", "scripts/docs", "tests/consumer"))
            + (("scripts/development", "upstream_sync_tests.py"),), reuse.SCOPES)
        root = Path(reuse.__file__).resolve().parents[2]
        provenance = ast.parse((root / "scripts/ci/offline_tooling_provenance.py").read_bytes())
        self.assertTrue(any(isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                            and node.value.id == "reuse" and node.attr == "TOTAL_SCOPE_SECONDS" for node in ast.walk(provenance)))
        workflow = (root / ".github/workflows/gradle.yml").read_text()
        self.assertIn("  tooling:\n", workflow)
        self.assertIn("    runs-on: ubuntu-24.04\n    timeout-minutes: 30\n", workflow)
        self.assertEqual(300, 30 * 60 - reuse.TOTAL_SCOPE_SECONDS)

    def test_real_linux_child_timeout_reports_scope_and_reaps_original_owned_child(self):
        self.assertEqual("Linux", reuse.platform.system())
        launched = []
        original = subprocess.Popen
        def launch(*args, **kwargs):
            child = original(*args, **kwargs)
            launched.append(child)
            return child
        command = [sys.executable, "-B", "-c", "import time; print('controlled child ready', flush=True); time.sleep(30)"]
        with tempfile.TemporaryDirectory(prefix="scope707-real-") as root, redirect_stderr(io.StringIO()) as stream, \
                patch.object(reuse, "scope_command", return_value=command), \
                patch.object(reuse.subprocess, "Popen", side_effect=launch):
            with self.assertRaisesRegex(ValueError, "Offline scope exceeded its total time/output bound"):
                reuse.execute_scope(Path(root), SCOPE, 0.15)
        self.assertEqual(1, len(launched))
        self.assertIsInstance(launched[0].returncode, int)
        self.assertLess(launched[0].returncode, 0)
        refused = records(stream.getvalue(), "[offline-scope] ")[-1]
        self.assertEqual(SCOPE[0], refused["directory"])
        self.assertIs(False, refused["time_admitted"])
        self.assertNotIn('"event":"completed"', stream.getvalue())


if __name__ == "__main__":
    unittest.main()
