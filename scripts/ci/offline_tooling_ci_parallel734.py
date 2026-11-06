#!/usr/bin/env python3
"""Only the fixed CI unittest discovery, in at most two owned Linux workers.

This changes source-suite execution capacity, not trust or native acceptance.
The existing outer scope owns the one deadline, merged log, original group and
private directory. No worker starts a new group/session or resets that budget.
"""
from __future__ import annotations

from contextlib import ExitStack
import json
import os
from pathlib import Path
import signal
import stat
import sys
import tempfile
import threading
import time
import unittest
import warnings

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY, PATTERN = "scripts/ci", "test_*.py"
WORKERS = 2
MAX_TESTS = 100000
MAX_MODULE_SUITES = 4096
MAX_NODES = 200000
MAX_RESULT_BYTES = 65536
RESULT_SCHEMA = "nativecmpkit-ci-fork2-worker734-v1"
METRICS = ("failures", "errors", "skipped", "expected_failures", "unexpected_successes")


def require(value, message):
    if not value:
        raise ValueError(message)


def _plan(suite):
    """Keep subtrees and order; shared fixture-owner intervals stay whole."""
    require(isinstance(suite, unittest.TestSuite), "Unknown discovery suite")
    units = list(suite)
    require(0 < len(units) <= MAX_MODULE_SUITES, "Missing or unbounded module suites")
    nodes = 0

    def walk(test, active, depth):
        nonlocal nodes
        nodes += 1
        require(nodes <= MAX_NODES and depth <= 64 and id(test) not in active,
                "Cyclic or unbounded discovery tree")
        if isinstance(test, unittest.TestCase):
            # unittest module/class fixtures follow the actual testcase type,
            # including FunctionTestCase subclasses with borrowed callables.
            modules = [type(test).__module__]
            if isinstance(test, unittest.FunctionTestCase):
                modules.append(test._testFunc.__module__)  # Conservative callable ownership too.
            require(all(type(module) is str and 0 < len(module) <= 4096 for module in modules),
                    "Unknown defining module")
            return 1, set(modules)
        require(isinstance(test, unittest.TestSuite), "Non-unittest discovery node")
        count, modules = 0, set()
        for child in test:
            size, names = walk(child, active | {id(test)}, depth + 1)
            count += size
            modules.update(names)
        require(count == test.countTestCases(), "Discovery count does not match its complete tree")
        return count, modules

    sizes, names = zip(*(walk(unit, {id(suite)}, 1) for unit in units))
    total = sum(sizes)
    require(0 < total <= MAX_TESTS and total == suite.countTestCases(),
            "Missing or inconsistent complete discovery count")
    parents = list(range(len(units)))

    def owner(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    first = {}
    for index, modules in enumerate(names):
        for module in modules:
            if module in first:
                parents[owner(index)] = owner(first[module])
            else:
                first[module] = index
    groups = {}
    for index in range(len(units)):
        groups.setdefault(owner(index), []).append(index)
    # Close every shared-owner component over its original discovery interval.
    # Otherwise A -> B -> A could become adjacent A -> A in one lane and lose
    # both unittest fixture transitions. Overlapping intervals close together.
    intervals = sorted((indexes[0], indexes[-1]) for indexes in groups.values())
    closed = []
    for start, stop in intervals:
        if closed and start <= closed[-1][-1]:
            closed[-1].extend(range(closed[-1][-1] + 1, stop + 1))
        else:
            closed.append(list(range(start, stop + 1)))
    components = sorted(closed, key=lambda indexes: (-sum(sizes[i] for i in indexes), indexes[0]))
    lanes = [[] for _ in range(min(WORKERS, len(components)))]
    weights = [0] * len(lanes)
    for indexes in components:
        lane = min(range(len(lanes)), key=lambda i: (weights[i], i))
        lanes[lane].extend(indexes)
        weights[lane] += sum(sizes[i] for i in indexes)
    require(sorted(i for lane in lanes for i in lane) == list(range(len(units))),
            "Missing or repeated module suite")
    return [(sorted(indexes), unittest.TestSuite(units[i] for i in sorted(indexes)), weights[lane])
            for lane, indexes in enumerate(lanes)]


class _Stream:
    """Raw unittest output, without a per-worker global summary."""
    def __init__(self, stream):
        self.stream = stream

    def write(self, value):
        return self.stream.write(value)

    def flush(self):
        return self.stream.flush()

    def writeln(self, value=""):
        self.write(value)
        self.write("\n")


def _worker(lane, indexes, suite, expected, home, temporary, descriptor, leader):
    result = unittest.TextTestResult(_Stream(sys.stderr), True, 2)
    result.failfast = result.buffer = result.tb_locals = False
    complete = False
    try:
        require(os.getpgid(0) == leader and os.getsid(0) == leader, "Worker left the original scope group")
        os.environ["HOME"], os.environ["TMPDIR"] = str(home), str(temporary)
        tempfile.tempdir = None
        with warnings.catch_warnings():
            if not sys.warnoptions:
                warnings.simplefilter("default")
                warnings.filterwarnings("module", category=DeprecationWarning,
                                        message=r"Please use assert\w+ instead.")
            result.startTestRun()
            try:
                suite.run(result)
                require(os.getpgid(0) == leader and os.getsid(0) == leader,
                        "Worker left the original scope group during its suite")
                complete = True
            finally:
                result.stopTestRun()
        result.printErrors()
    except BaseException as error:
        complete = False
        try:
            print("CI module worker refused: " + type(error).__name__, file=sys.stderr, flush=True)
        except BaseException:
            pass
    metrics = {name: len(getattr(result, {"expected_failures": "expectedFailures",
                                        "unexpected_successes": "unexpectedSuccesses"}.get(name, name)))
               for name in METRICS}
    passed = complete and result.testsRun == expected and not any(metrics.values())
    packet = {"schema": RESULT_SCHEMA, "lane": lane, "units": indexes, "assigned_tests": expected,
              "tests_run": result.testsRun, "complete": complete, "passed": passed, **metrics}
    try:
        raw = json.dumps(packet, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        require(len(raw) <= MAX_RESULT_BYTES, "Worker result exceeds its bound")
        sys.stdout.flush()
        sys.stderr.flush()
        require(os.pwrite(descriptor, raw, 0) == len(raw), "Incomplete worker result write")
    except BaseException:
        os._exit(2)
    os._exit(0 if passed else 1)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate worker result field")
        result[key] = value
    return result


def _packet(raw, lane, indexes, expected, exitcode):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_RESULT_BYTES, "Missing or unbounded worker result")
    value = json.loads(raw.decode("ascii"), object_pairs_hook=_pairs,
                       parse_constant=lambda token: require(False, "Nonfinite worker result"))
    fields = {"schema", "lane", "units", "assigned_tests", "tests_run", "complete", "passed", *METRICS}
    require(type(value) is dict and set(value) == fields and value["schema"] == RESULT_SCHEMA,
            "Unknown worker result")
    require(type(value["lane"]) is int and value["lane"] == lane
            and type(value["units"]) is list and all(type(i) is int for i in value["units"])
            and value["units"] == indexes and type(value["assigned_tests"]) is int
            and value["assigned_tests"] == expected, "Foreign or incomplete worker assignment")
    require(type(value["tests_run"]) is int and 0 <= value["tests_run"] <= expected
            and all(type(value[name]) is int and 0 <= value[name] <= MAX_TESTS + MAX_MODULE_SUITES
                    for name in METRICS)
            and type(value["complete"]) is bool and type(value["passed"]) is bool,
            "Unknown worker outcome")
    passed = value["complete"] and value["tests_run"] == expected and not any(value[name] for name in METRICS)
    require(value["passed"] is passed and type(exitcode) is int and (exitcode == 0) is passed,
            "Worker exit/result disagreement")
    return value


def _retain(pid):
    observed = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    require(observed is None or observed.si_pid == pid, "Unproven direct CI worker")
    return observed


def _dispose(pids, leader):
    """Only pinned direct workers; the outer owner disposes their original group."""
    failures = []
    for pid in pids:
        try:
            observed = _retain(pid)
            same_group = os.getpgid(pid) == leader and os.getsid(pid) == leader
            if observed is None:
                # Parentage plus WNOWAIT pins this direct PID even if a group
                # check refuses. Never signal an unproven or foreign group.
                os.kill(pid, signal.SIGKILL)
            deadline = time.monotonic() + 5
            while _retain(pid) is None:
                require(time.monotonic() < deadline, "Owned CI worker did not terminate")
                time.sleep(0.01)
            require(os.waitpid(pid, 0)[0] == pid, "Owned CI worker reap differs")
            require(same_group, "Direct CI worker left the original scope group")
        except BaseException as error:
            failures.append(error)
    if failures:
        for later in failures[1:]:
            failures[0].add_note("Further owned CI worker cleanup refusal: " + type(later).__name__)
        raise failures[0]


def _run(plan, home, temporary):
    require(type(plan) is list and 1 <= len(plan) <= WORKERS, "Unknown or unbounded CI worker plan")
    require(threading.active_count() == 1 and threading.current_thread() is threading.main_thread(),
            "CI module fork requires a fresh single-threaded dispatcher")
    leader = os.getpid()
    require(os.getpgid(0) == leader and os.getsid(0) == leader, "CI dispatcher is not the original scope leader")
    pids, outcomes = [], {}
    with ExitStack() as stack:
        files = [stack.enter_context(tempfile.TemporaryFile(dir=temporary)) for _ in plan]
        try:
            for lane, (indexes, suite, expected) in enumerate(plan):
                worker_home, worker_tmp = home / ("ci-fork2-home-" + str(lane)), temporary / ("ci-fork2-tmp-" + str(lane))
                worker_home.mkdir()
                worker_tmp.mkdir()
                sys.stdout.flush()
                sys.stderr.flush()
                pid = os.fork()
                if pid == 0:
                    try:
                        # A child must not retain another lane's result writer.
                        for other_lane, result_file in enumerate(files):
                            if other_lane != lane:
                                result_file.close()
                        _worker(lane, indexes, suite, expected, worker_home, worker_tmp, files[lane].fileno(), leader)
                    except BaseException:
                        os._exit(2)  # Never enter the parent cleanup path from a failed fork child.
                pids.append(pid)
            while len(outcomes) != len(pids):
                for lane, pid in enumerate(pids):
                    if lane in outcomes:
                        continue
                    observed = _retain(pid)
                    if observed is None:
                        continue
                    require(os.getpgid(pid) == leader and os.getsid(pid) == leader,
                            "Direct CI worker left the original scope group")
                    descriptor = files[lane].fileno()
                    before = os.fstat(descriptor)
                    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 0
                            and before.st_size <= MAX_RESULT_BYTES, "Nonordinary or unbounded worker result file")
                    raw = os.pread(descriptor, MAX_RESULT_BYTES + 1, 0)
                    after = os.fstat(descriptor)
                    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_uid, s.st_gid,
                                          s.st_size, s.st_mtime_ns, s.st_ctime_ns)
                    require(identity(before) == identity(after) and len(raw) == before.st_size,
                            "Worker result changed during its fresh read")
                    code = observed.si_status if observed.si_code == os.CLD_EXITED else -observed.si_status
                    indexes, _, expected = plan[lane]
                    outcomes[lane] = _packet(raw, lane, indexes, expected, code)
                if len(outcomes) != len(pids):
                    time.sleep(0.05)
        finally:
            primary = sys.exc_info()[1]
            try:
                _dispose(pids, leader)
            except BaseException as error:
                if primary is None:
                    raise
                primary.add_note("Owned CI worker cleanup also refused: " + type(error).__name__)
    return [outcomes[lane] for lane in range(len(plan))]


def main():
    require(len(sys.argv) == 1, "Foreign fixed CI discovery arguments")
    require(sys.platform == "linux" and all(hasattr(os, name) for name in
            ("fork", "waitid", "WNOWAIT", "getpgid", "getsid", "pread", "pwrite")), "Linux owned CI workers required")
    require(Path.cwd().resolve() == ROOT, "Foreign CI discovery checkout")
    home, temporary = Path(os.environ["HOME"]), Path(os.environ["TMPDIR"])
    require(home.is_absolute() and temporary.is_absolute() and home.is_dir() and temporary.is_dir()
            and not home.is_symlink() and not temporary.is_symlink()
            and home.parent == temporary.parent and home != temporary, "Missing original private scope HOME/tmp")
    started = time.monotonic()
    # Exactly the original discovery, once. load_tests and import-error suites
    # are kept, not guessed from filenames or filtered testcase identifiers.
    discovered = unittest.TestLoader().discover(str(ROOT / DIRECTORY), pattern=PATTERN)
    plan = _plan(discovered)
    outcomes = _run(plan, home, temporary)
    total = sum(value["tests_run"] for value in outcomes)
    totals = {name: sum(value[name] for value in outcomes) for name in METRICS}
    refused = sum(not value["complete"] for value in outcomes)
    passed = total == discovered.countTestCases() and all(value["passed"] for value in outcomes)
    print("\nRan " + str(total) + " tests in " + format(time.monotonic() - started, ".3f") + "s", file=sys.stderr)
    if passed:
        print("\nOK", file=sys.stderr, flush=True)
    else:
        labels = ", ".join(name + "=" + str(count) for name, count in (*totals.items(), ("worker_refusals", refused)) if count)
        print("\nFAILED (" + (labels or "incomplete discovery") + ")", file=sys.stderr, flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print("Fixed CI parallel scope refused: " + type(error).__name__, file=sys.stderr, flush=True)
        raise SystemExit(2)
