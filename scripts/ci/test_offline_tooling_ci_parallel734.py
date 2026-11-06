"""NEW fixed CI fork2 controls; synthetic source fixtures, not native results."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import sys
import types
import unittest
from unittest.mock import patch

import offline_tooling_ci_parallel734 as p
import offline_tooling_reuse as reuse


@unittest.skipUnless(sys.platform == "linux" and all(hasattr(os, name) for name in
                     ("fork", "waitid", "WNOWAIT", "pread", "pwrite")), "Linux owned source control")
class FixedCiParallel734Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ci-fork2-control734-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        directory = self.root / "scripts/ci"
        directory.mkdir(parents=True)
        (directory / "offline_tooling_ci_parallel734.py").write_bytes(Path(p.__file__).read_bytes())

    def run_fixture(self, left, right, seconds=5):
        directory = self.root / "scripts/ci"
        (directory / "test_left.py").write_text(left, encoding="utf-8")
        (directory / "test_right.py").write_text(right, encoding="utf-8")
        outputs = []
        original = reuse.scope_summary

        def capture(*args):
            outputs.append(args[2])
            return original(*args)

        # Negative inner scopes may print their raw unittest footer in failure
        # diagnostics. Isolate both Python streams; keep the complete child bytes
        # in outputs[0], unchanged, for the owning assertions below.
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), \
                patch.object(reuse, "scope_summary", side_effect=capture):
            result = reuse.execute_scope(self.root, ("scripts/ci", "test_*.py"), seconds)
        return result, outputs[0]

    def write_trace_fixture(self):
        (self.root / "scripts/ci/fixture_trace734.py").write_text("""import json
from pathlib import Path
events, calls = [], []
def record(event):
    events.append(event)
    (Path(__file__).resolve().parents[2] / 'fixture-trace734.json').write_text(
        json.dumps({'events': events, 'load_tests': calls}), encoding='utf-8')
""", encoding="utf-8")

    def test_existing_recipe_keeps_ten_scopes_nine_commands_and_1500_seconds(self):
        self.assertEqual(10, len(reuse.SCOPES))
        self.assertEqual(1500, reuse.TOTAL_SCOPE_SECONDS)
        self.assertEqual(2, p.WORKERS)
        for directory, pattern in reuse.SCOPES:
            wanted = (["python3", "-B", "scripts/ci/offline_tooling_ci_parallel734.py"]
                      if (directory, pattern) == ("scripts/ci", "test_*.py")
                      else ["python3", "-B", "-m", "unittest", "discover", "-s", directory, "-p", pattern, "-v"])
            self.assertEqual(wanted, reuse.scope_command(directory, pattern))
        self.assertIn("ci-whole-module-fork2-private-home-tmp-v1", reuse.ENVIRONMENT_RECIPE)
        with self.assertRaises(ValueError):
            reuse.scope_command("scripts/ci", "test_selected_only.py")

    def test_plan_preserves_nested_load_tests_and_whole_defining_modules(self):
        a = type("A", (unittest.TestCase,), {"__module__": "synthetic_a", "test_one": lambda self: None})
        b = type("B", (unittest.TestCase,), {"__module__": "synthetic_b", "test_one": lambda self: None})
        module = types.ModuleType("synthetic_load_tests")
        calls = []
        module.load_tests = lambda loader, tests, pattern: (calls.append(pattern) or unittest.TestSuite(
            [unittest.TestSuite([a("test_one")]), unittest.TestSuite([b("test_one")])]))
        loaded = unittest.TestLoader().loadTestsFromModule(module)
        suite = unittest.TestSuite([loaded, unittest.TestSuite([a("test_one")])])
        plan = p._plan(suite)
        self.assertEqual([None], calls)
        self.assertEqual(3, sum(count for _, _, count in plan))
        self.assertEqual([0, 1], sorted(i for indexes, _, _ in plan for i in indexes))
        # The load_tests subtree is never split; overlapping defining modules
        # connect complete module units rather than filtering their cases.
        self.assertEqual(1, len(plan))
        cyclic = unittest.TestSuite()
        cyclic.addTest(cyclic)
        with self.assertRaises(ValueError):
            p._plan(unittest.TestSuite([cyclic]))

    def test_two_workers_share_original_group_and_get_fresh_owned_home_tmp(self):
        template = """import os, time, unittest
from pathlib import Path
class Fixture(unittest.TestCase):
    def test_body(self):
        self.assertEqual(os.getpgid(0), os.getsid(0))
        self.assertNotEqual(os.getpid(), os.getpgid(0))
        self.assertTrue(Path(os.environ['HOME']).name.startswith('ci-fork2-home-'))
        self.assertTrue(Path(os.environ['TMPDIR']).name.startswith('ci-fork2-tmp-'))
        self.assertNotIn('SECRET_FOR_CI_FORK2_CONTROL', os.environ)
        shared = Path(os.environ['TMPDIR']).parent
        (shared / '{name}-started').write_text('owned-source-control')
        deadline = time.monotonic() + 3
        while not (shared / '{other}-started').exists():
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.01)
"""
        entry_check = """import errno, os, sys
_dispatch = sys.modules['__main__']
_result_fds = []
_original_file = _dispatch.tempfile.TemporaryFile
def tracked_file(*args, **kwargs):
    result_file = _original_file(*args, **kwargs)
    _result_fds.append(result_file.fileno())
    return result_file
_dispatch.tempfile.TemporaryFile = tracked_file
_original_worker = _dispatch._worker
def checked_worker(lane, indexes, suite, expected, home, temporary, descriptor, leader):
    if len(_result_fds) != 2 or descriptor != _result_fds[lane]:
        raise AssertionError('foreign worker-entry result descriptor')
    os.fstat(descriptor)
    for other in _result_fds:
        if other != descriptor:
            try:
                os.fstat(other)
            except OSError as error:
                if error.errno != errno.EBADF:
                    raise
            else:
                raise AssertionError('nonassigned result writer inherited')
    probe = b'assigned-writer-usable'
    if os.pwrite(descriptor, probe, 0) != len(probe):
        raise AssertionError('assigned result writer unusable')
    os.ftruncate(descriptor, 0)
    print('worker-entry-result-fds-isolated-' + str(lane), flush=True)
    _original_worker(lane, indexes, suite, expected, home, temporary, descriptor, leader)
_dispatch._worker = checked_worker
"""
        with patch.dict(os.environ, {"SECRET_FOR_CI_FORK2_CONTROL": "must-not-inherit"}):
            result, output = self.run_fixture(entry_check + template.format(name="left", other="right"),
                                              template.format(name="right", other="left"))
        self.assertTrue(result["passed"])
        self.assertEqual(2, result["tests"])
        self.assertEqual(1, output.count(b"\nRan "))
        for lane in range(2):
            self.assertEqual(1, output.count(b"worker-entry-result-fds-isolated-" + str(lane).encode()))
        self.assertNotIn(b"must-not-inherit", output)

    def test_load_tests_and_class_module_fixtures_are_preserved(self):
        left = """import unittest
events = []
def setUpModule(): events.append('module-start')
def tearDownModule(): events.append('module-stop')
class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls): events.append('class-start')
    @classmethod
    def tearDownClass(cls): events.append('class-stop')
    def test_first(self): self.assertEqual(['module-start', 'class-start'], events)
    def test_second(self): self.assertEqual(['module-start', 'class-start'], events)
    def test_not_selected_by_load_tests(self): self.fail('load_tests was ignored')
def load_tests(loader, tests, pattern):
    return unittest.TestSuite([unittest.TestSuite([Fixture('test_first'), Fixture('test_second')])])
"""
        right = "import unittest\nclass Fixture(unittest.TestCase):\n def test_body(self): self.assertTrue(True)\n"
        result, _ = self.run_fixture(left, right)
        self.assertTrue(result["passed"])
        self.assertEqual(3, result["tests"])

    def test_borrowed_case_load_tests_preserves_A_B_A_fixture_transitions(self):
        self.write_trace_fixture()
        directory = self.root / "scripts/ci"
        owner_source = """import unittest
from fixture_trace734 import calls, events, record
LABEL = LABEL_VALUE
def setUpModule(): record(LABEL + '-module-start')
def tearDownModule(): record(LABEL + '-module-stop')
class BorrowedCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls): record(LABEL + '-class-start')
    @classmethod
    def tearDownClass(cls): record(LABEL + '-class-stop')
    def test_first(self):
        self.assertEqual(['left', 'middle', 'right'], calls)
        record(LABEL + '-first')
    def test_middle(self):
        self.assertEqual(['A-module-start', 'A-class-start', 'A-first',
                          'A-class-stop', 'A-module-stop', 'B-module-start', 'B-class-start'], events)
        record(LABEL + '-middle')
    def test_last(self):
        self.assertEqual(['A-module-start', 'A-class-start', 'A-first', 'A-class-stop', 'A-module-stop',
                          'B-module-start', 'B-class-start', 'B-middle', 'B-class-stop', 'B-module-stop',
                          'A-module-start', 'A-class-start'], events)
        record(LABEL + '-last')
"""
        for label in ("A", "B"):
            (directory / ("fixture_case_" + label.lower() + "734.py")).write_text(
                owner_source.replace("LABEL_VALUE", repr(label)), encoding="utf-8")
        unit = """import fixture_case_OWNER734 as owner
from fixture_trace734 import calls
import unittest
def load_tests(loader, tests, pattern):
    calls.append('UNIT')
    return unittest.TestSuite([unittest.TestSuite([owner.BorrowedCase('test_METHOD')])])
"""
        left = unit.replace("OWNER", "a").replace("UNIT", "left").replace("METHOD", "first")
        middle = unit.replace("OWNER", "b").replace("UNIT", "middle").replace("METHOD", "middle")
        right = unit.replace("OWNER", "a").replace("UNIT", "right").replace("METHOD", "last")
        (directory / "test_middle.py").write_text(middle, encoding="utf-8")
        result, output = self.run_fixture(left, right)
        self.assertTrue(result["passed"])
        self.assertEqual(3, result["tests"])
        self.assertEqual(1, output.count(b"\nRan "))
        trace = json.loads((self.root / "fixture-trace734.json").read_text(encoding="utf-8"))
        self.assertEqual(["left", "middle", "right"], trace["load_tests"])
        self.assertEqual(["A-module-start", "A-class-start", "A-first", "A-class-stop", "A-module-stop",
                          "B-module-start", "B-class-start", "B-middle", "B-class-stop", "B-module-stop",
                          "A-module-start", "A-class-start", "A-last", "A-class-stop", "A-module-stop"],
                         trace["events"])

    def test_borrowed_function_subclass_keeps_actual_type_fixture_owner(self):
        self.write_trace_fixture()
        directory = self.root / "scripts/ci"
        (directory / "fixture_function_owner734.py").write_text("""import unittest
from fixture_trace734 import record
def setUpModule(): record('F-module-start')
def tearDownModule(): record('F-module-stop')
class BorrowedFunction(unittest.FunctionTestCase):
    @classmethod
    def setUpClass(cls): record('F-class-start')
    @classmethod
    def tearDownClass(cls): record('F-class-stop')
""", encoding="utf-8")
        (directory / "borrowed_left734.py").write_text("""from fixture_trace734 import events, record
def borrowed():
    if events != ['F-module-start', 'F-class-start']:
        raise AssertionError('borrowed function lost actual fixture owner')
    record('left-function')
""", encoding="utf-8")
        (directory / "borrowed_right734.py").write_text("""from fixture_trace734 import events, record
def borrowed():
    if events != ['F-module-start', 'F-class-start', 'left-function']:
        raise AssertionError('borrowed function subclass fixture was split')
    record('right-function')
""", encoding="utf-8")
        unit = """import borrowed_SIDE734 as function_source
import fixture_function_owner734 as owner
from fixture_trace734 import calls
import unittest
def load_tests(loader, tests, pattern):
    calls.append('SIDE')
    return unittest.TestSuite([unittest.TestSuite([owner.BorrowedFunction(function_source.borrowed)])])
"""
        result, output = self.run_fixture(unit.replace("SIDE", "left"), unit.replace("SIDE", "right"))
        self.assertTrue(result["passed"])
        self.assertEqual(2, result["tests"])
        self.assertEqual(1, output.count(b"\nRan "))
        trace = json.loads((self.root / "fixture-trace734.json").read_text(encoding="utf-8"))
        self.assertEqual(["left", "right"], trace["load_tests"])
        self.assertEqual(["F-module-start", "F-class-start", "left-function", "right-function",
                          "F-class-stop", "F-module-stop"], trace["events"])
        # Different actual type owners still conservatively share a borrowed callable origin.
        def borrowed(): pass
        borrowed.__module__ = "synthetic_callable_origin734"
        left_type = type("LeftFunction", (unittest.FunctionTestCase,), {"__module__": "synthetic_owner_left734"})
        right_type = type("RightFunction", (unittest.FunctionTestCase,), {"__module__": "synthetic_owner_right734"})
        plan = p._plan(unittest.TestSuite([unittest.TestSuite([left_type(borrowed)]),
                                          unittest.TestSuite([right_type(borrowed)])]))
        self.assertEqual(1, len(plan))
        self.assertEqual([0, 1], plan[0][0])

    def test_fixture_setup_and_teardown_failures_propagate_without_green(self):
        pass_case = "import unittest\nclass Fixture(unittest.TestCase):\n def test_body(self): self.assertTrue(True)\n"
        for fixture in ("setUpModule", "tearDownModule", "setUpClass", "tearDownClass"):
            with self.subTest(fixture=fixture):
                if fixture.endswith("Module"):
                    source = ("import unittest\ndef " + fixture + "():\n"
                              " raise RuntimeError('synthetic " + fixture + " failure')\n"
                              "class Fixture(unittest.TestCase):\n def test_body(self): self.assertTrue(True)\n")
                else:
                    source = ("import unittest\nclass Fixture(unittest.TestCase):\n @classmethod\n def "
                              + fixture + "(cls):\n  raise RuntimeError('synthetic " + fixture + " failure')\n"
                              " def test_body(self): self.assertTrue(True)\n")
                result, output = self.run_fixture(source, pass_case)
                self.assertFalse(result["passed"])
                self.assertEqual(1 if fixture.startswith("setUp") else 2, result["tests"])
                self.assertEqual(1, output.count(b"\nRan "))
                self.assertIn(b"ERROR: " + fixture.encode() + b" (", output)
                self.assertIn(b"synthetic " + fixture.encode() + b" failure", output)
                self.assertIn(b"\nFAILED (errors=1)", output)
                self.assertNotIn(b"\nOK", output)

    def test_abrupt_worker_without_packet_disposes_live_peer_and_never_summarizes(self):
        abrupt = """import os, sys, time, unittest
from pathlib import Path
_dispatch = sys.modules['__main__']
_original_dispose = _dispatch._dispose
def observed_dispose(pids, leader):
    live = [pid for pid in pids if _dispatch._retain(pid) is None]
    if len(live) != 1:
        raise AssertionError('no unique still-running owned peer')
    print('peer-live-before-owned-disposal', flush=True)
    _original_dispose(pids, leader)
    for pid in pids:
        try:
            os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            pass
        else:
            raise AssertionError('direct owned worker not reaped')
    print('all-direct-workers-reaped', flush=True)
_dispatch._dispose = observed_dispose
class Fixture(unittest.TestCase):
    def test_body(self):
        shared = Path(os.environ['TMPDIR']).parent
        deadline = time.monotonic() + 3
        while not (shared / 'peer-started').exists():
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.01)
        os._exit(7)  # Abrupt terminal worker: no result packet.
"""
        peer = """import os, time, unittest
from pathlib import Path
class Fixture(unittest.TestCase):
    def test_body(self):
        (Path(os.environ['TMPDIR']).parent / 'peer-started').write_text('owned-source-control')
        time.sleep(30)
"""
        result, output = self.run_fixture(abrupt, peer)
        self.assertFalse(result["passed"])
        self.assertEqual(2, result["returncode"])
        self.assertEqual(0, result["tests"])
        self.assertEqual(1, output.count(b"peer-live-before-owned-disposal"))
        self.assertEqual(1, output.count(b"all-direct-workers-reaped"))
        self.assertIn(b"Fixed CI parallel scope refused: ValueError", output)
        self.assertNotIn(b"\nRan ", output)
        self.assertNotIn(b"\nOK", output)

    def test_worker_packet_refuses_missing_duplicate_foreign_or_incomplete_green(self):
        good = {"schema": p.RESULT_SCHEMA, "lane": 0, "units": [0], "assigned_tests": 2,
                "tests_run": 2, "complete": True, "passed": True, **{name: 0 for name in p.METRICS}}
        raw = lambda value: json.dumps(value, separators=(",", ":")).encode("ascii")
        self.assertTrue(p._packet(raw(good), 0, [0], 2, 0)["passed"])
        bads = [{**good, "lane": True}, {**good, "units": [0, 0]}, {**good, "schema": "foreign"},
                {**good, "complete": False}, {**good, "tests_run": 1}, {**good, "expected_failures": 1},
                {key: value for key, value in good.items() if key != "errors"}]
        for value in bads:
            with self.subTest(fields=sorted(value)):
                with self.assertRaises(ValueError):
                    p._packet(raw(value), 0, [0], 2, 0)
        with self.assertRaises(ValueError):
            p._packet(raw(good), 0, [0], 2, 1)
        with self.assertRaises(ValueError):
            p._packet(raw(good)[:-1] + b',"lane":0}', 0, [0], 2, 0)
        with patch.object(p.threading, "active_count", return_value=2):
            with self.assertRaisesRegex(ValueError, "single-threaded"):
                p._run([([0], unittest.TestSuite(), 0)], self.root, self.root)
        packets = []

        def retain_packet(descriptor, data, offset):
            packets.append(json.loads(data))
            return len(data)

        def stop_process(code):
            raise SystemExit(code)

        inner = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
        with patch.dict(os.environ, {}), patch.object(tempfile, "tempdir", None), \
                patch.object(unittest.TextTestResult, "stopTestRun", side_effect=RuntimeError("controlled stop failure")), \
                patch.object(p.os, "pwrite", side_effect=retain_packet), \
                patch.object(p.os, "_exit", side_effect=stop_process):
            with self.assertRaises(SystemExit) as stopped:
                p._worker(0, [0], inner, 1, self.root, self.root, -1, os.getpgid(0))
        self.assertEqual(1, stopped.exception.code)
        self.assertFalse(packets[0]["complete"])
        self.assertFalse(packets[0]["passed"])

    def test_full_failure_skip_expected_failure_and_unexpected_success_aggregation(self):
        pass_case = "import unittest\nclass Fixture(unittest.TestCase):\n def test_body(self): self.assertTrue(True)\n"
        cases = {
            "failure": "import unittest\nclass Fixture(unittest.TestCase):\n def test_body(self): self.fail('synthetic owning failure')\n",
            "skip": "import unittest\nclass Fixture(unittest.TestCase):\n @unittest.skip('synthetic skip')\n def test_body(self): pass\n",
            "expected": "import unittest\nclass Fixture(unittest.TestCase):\n @unittest.expectedFailure\n def test_body(self): self.fail('synthetic expected failure')\n",
            "unexpected": "import unittest\nclass Fixture(unittest.TestCase):\n @unittest.expectedFailure\n def test_body(self): pass\n",
        }
        for mode, source in cases.items():
            with self.subTest(mode=mode):
                result, output = self.run_fixture(source, source if mode == "failure" else pass_case)
                self.assertFalse(result["passed"])
                self.assertEqual(2, result["tests"])
                self.assertEqual(1, output.count(b"\nRan "))
                self.assertIn(b"\nFAILED (", output)
                if mode == "failure":
                    self.assertEqual(2, output.count(b"FAIL: test_body"))

    def test_fake_extra_summary_is_not_admitted(self):
        left = "import unittest\nclass Fixture(unittest.TestCase):\n def test_body(self): print('\\nRan 999 tests in 0.01s\\n\\nOK', flush=True)\n"
        right = "import unittest\nclass Fixture(unittest.TestCase):\n def test_body(self): self.assertTrue(True)\n"
        result, output = self.run_fixture(left, right)
        self.assertFalse(result["passed"])
        self.assertEqual(0, result["tests"])
        self.assertEqual(2, output.count(b"Ran "))
        self.assertIn(b"\nRan 999 tests in 0.01s\n\nOK\n", output)

    def test_inner_negative_scope_streams_are_isolated_and_full_raw_output_retained(self):
        negative = """import sys, unittest
class Fixture(unittest.TestCase):
    def test_body(self):
        print('raw-inner-stdout-marker', flush=True)
        print('raw-inner-stderr-marker', file=sys.stderr, flush=True)
        self.fail('synthetic isolated inner failure')
"""
        positive = "import unittest\nclass Fixture(unittest.TestCase):\n def test_body(self): self.assertTrue(True)\n"
        outer_stdout, outer_stderr = io.StringIO(), io.StringIO()
        original_execute = reuse.execute_scope

        def noisy_execute(*args):
            print("\nRan 901 tests in 0.001s\n\nFAILED (inner stdout diagnostic)", flush=True)
            print("\nRan 902 tests in 0.001s\n\nFAILED (inner stderr diagnostic)", file=sys.stderr, flush=True)
            return original_execute(*args)

        with redirect_stdout(outer_stdout), redirect_stderr(outer_stderr), \
                patch.object(reuse, "execute_scope", side_effect=noisy_execute):
            result, output = self.run_fixture(negative, positive)
        self.assertEqual("", outer_stdout.getvalue())
        self.assertEqual("", outer_stderr.getvalue())
        self.assertFalse(result["passed"])
        self.assertEqual(2, result["tests"])
        self.assertEqual(len(output), result["output_bytes"])
        self.assertEqual(reuse.digest(output), result["output_sha256"])
        self.assertIn(b"raw-inner-stdout-marker", output)
        self.assertIn(b"raw-inner-stderr-marker", output)
        self.assertIn(b"FAIL: test_body", output)
        self.assertEqual(1, output.count(b"\nRan "))
        self.assertIn(b"\nFAILED (failures=1)", output)
        self.assertNotIn(b"Ran 901", output)
        self.assertNotIn(b"Ran 902", output)
        self.assertNotIn(b"\nOK", output)

    def test_outer_timeout_refuses_without_a_green_summary(self):
        slow = "import time, unittest\nclass Fixture(unittest.TestCase):\n def test_body(self): time.sleep(30)\n"
        with patch.object(reuse, "scope_summary", side_effect=AssertionError("summary after refusal")):
            with self.assertRaisesRegex(ValueError, "total time/output bound"):
                self.run_fixture(slow, slow, seconds=0.15)


if __name__ == "__main__":
    unittest.main()
