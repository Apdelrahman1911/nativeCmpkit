"""Sealed final CI668 source APIs, then exactly NEW8 plus four changed bodies.

Never discover tests, execute restored code, run CI leaves, or write current
candidate/accepted sources. Each first stage has one immutable output directory.
"""
import argparse
import ast
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time
import traceback
import unittest

BASE = Path(__file__).resolve().parent
ROOT = BASE / "candidate-root"
RECIPE_SHA = "3f451e495617c830a7cadcbacffd2fc4061ba0b95ea5372c11726fefc6bb1a51"
RECIPE_PATH = BASE.parent / "FINAL-CI668-EXACT-OUTER-SOURCE-RECIPE676.json"
PLAN_PATH = BASE / "FINAL-CI668-PLAN-RECOVERY-EXECUTION-PLAN676.json"
STAGES = {"source-plan-recovery": "FINAL-CI668-SOURCE-PLAN-ONLYFAILED-FIRST676", "selected12": "FINAL-CI668-SELECTED12-FIRST676"}
FORBIDDEN = {
    "subprocess.Popen", "os.system", "os.posix_spawn", "os.posix_spawnp",
    "os.fork", "os.forkpty", "os.kill", "os.killpg", "socket.connect",
    "socket.bind", "socket.getaddrinfo", "socket.sendto", "ctypes.dlopen",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_ref(row):
    raw = Path(row["path"]).read_bytes()
    require(sha(raw) == row["sha256"], "Sealed reference differs: " + row["path"])
    return raw


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def physical_method(raw, classname, method):
    classes = [node for node in ast.parse(raw).body if isinstance(node, ast.ClassDef) and node.name == classname]
    require(len(classes) == 1, "One exact owning class is required")
    methods = [node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == method]
    require(len(methods) == 1, "One exact physical selected body is required")
    node = methods[0]
    return b"".join(raw.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])


parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=tuple(STAGES))
parser.add_argument("--plan-sha256", required=True)
parser.add_argument("--source-acceptance", required=True, type=Path)
parser.add_argument("--source-acceptance-sha256", required=True)
parser.add_argument("--source-api-results", type=Path)
parser.add_argument("--source-api-results-sha256")
args = parser.parse_args()
require(sys.dont_write_bytecode, "Use python3 -B")
OUT = BASE / STAGES[args.phase]
require(not OUT.exists(), "An existing first-stage receipt must never be overwritten or replayed")
envelope_started = time.monotonic()
OUT.mkdir(mode=0o700)
external_attempts, write_attempts, unapproved_bodies, body_invocations = [], [], [], []
events, current_step, refusal = [], "launch-custody", None
before, before_state, after, after_state, reference = None, None, None, None, None
names, result, suite_seconds, suite_monotonic, api_seconds = [], None, None, None, None
runner_raw = Path(__file__).read_bytes()
runner_sha = sha(runner_raw)
execution_started_utc = datetime.now(timezone.utc).isoformat()
api_output, unittest_output = io.StringIO(), io.StringIO()


def inside_output(path, *, follow=False, dir_fd=None):
    if isinstance(path, int):
        path = os.readlink("/proc/self/fd/" + str(path))
    if not isinstance(path, (str, bytes, os.PathLike)):
        return False
    path = os.fsdecode(path)
    if not os.path.isabs(path) and isinstance(dir_fd, int) and dir_fd >= 0:
        path = os.path.join(os.readlink("/proc/self/fd/" + str(dir_fd)), path)
    absolute = os.path.abspath(path)
    if follow:
        absolute = os.path.realpath(absolute)
    return absolute == str(OUT) or absolute.startswith(str(OUT) + os.sep)


def audit(event, arguments):
    if event in FORBIDDEN or event.startswith("os.exec"):
        external_attempts.append(event)
        raise AssertionError("External process/native/network/Git work is forbidden")
    if event == "open":
        path, mode, flags = arguments
        writable = (isinstance(mode, str) and any(letter in mode for letter in "wax+")) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writable and not inside_output(path, follow=True):
            write_attempts.append(event)
            raise AssertionError("Only this new receipt and its disposable fixtures may be written")
    elif event in {"os.mkdir", "os.remove", "os.rmdir"}:
        dir_fd = arguments[2] if event == "os.mkdir" else arguments[1]
        if not inside_output(arguments[0], dir_fd=dir_fd):
            write_attempts.append(event)
            raise AssertionError("Mutation outside this new receipt is forbidden")
    elif event in {"os.rename", "os.link"}:
        if not (inside_output(arguments[0], dir_fd=arguments[2])
                and inside_output(arguments[1], dir_fd=arguments[3])):
            write_attempts.append(event)
            raise AssertionError("Rename/link outside this new receipt is forbidden")
    elif event == "os.symlink":
        if not inside_output(arguments[1], dir_fd=arguments[2]):
            write_attempts.append(event)
            raise AssertionError("Symlink destination outside this disposable receipt is forbidden")
    elif event in {"os.chmod", "os.chown", "os.utime", "os.truncate"}:
        dir_fd = arguments[-1] if event != "os.truncate" else None
        if not inside_output(arguments[0], follow=True, dir_fd=dir_fd):
            write_attempts.append(event)
            raise AssertionError("Metadata mutation outside this new receipt is forbidden")
    elif event == "exec":
        filename = arguments[0].co_filename
        if isinstance(filename, str) and filename.startswith(("/root/projects/", "/root/nativecmpkit-worktrees/")):
            external_attempts.append("noncandidate-source-execution")
            raise AssertionError("ROOT/accepted worktree source execution is forbidden")


sys.addaudithook(audit)


def snapshot():
    hashes, state = {}, {}
    for relative in sorted(reference):
        path = ROOT / relative
        require(relative == path.relative_to(ROOT).as_posix() and ".." not in Path(relative).parts,
                "An exact relative source identity is required")
        for parent in (path, *path.parents):
            if parent == ROOT.parent:
                break
            require(not parent.is_symlink(), "Linked current source/parent refuses")
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= 4 * 1024 * 1024,
                "One ordinary finite current source is required: " + relative)
        hashes[relative] = sha(path.read_bytes())
        state[relative] = {field: getattr(info, field) for field in (
            "st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")}
    return hashes, state


def profile(frame, event, argument):
    if event != "call" or not frame.f_code.co_name.startswith("test_"):
        return
    if not frame.f_code.co_filename.startswith(str(ROOT / "scripts/ci") + os.sep):
        return
    instance = frame.f_locals.get("self")
    if not isinstance(instance, unittest.TestCase):
        return
    identity = instance.id()
    if args.phase != "selected12" or identity not in names or identity in body_invocations:
        unapproved_bodies.append(identity)
        raise AssertionError("Unapproved or repeated unittest body refused: " + identity)
    body_invocations.append(identity)


def local_import_custody():
    origins = {}
    for name, module in tuple(sys.modules.items()):
        filename = getattr(module, "__file__", None)
        if filename is None:
            continue
        path = Path(filename).resolve()
        if path.is_relative_to(ROOT):
            relative = path.relative_to(ROOT).as_posix()
            require(relative in reference and sha(path.read_bytes()) == reference[relative],
                    "Uninventoried or displaced sparse source import: " + name)
            origins[name] = relative
    return origins


class ExactResult(unittest.TextTestResult):
    def startTest(self, test):
        require(test.id() in names, "An ineligible test case was loaded")
        super().startTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        events.append({"identity": test.id(), "outcome": "pass"})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        events.append({"identity": test.id(), "outcome": "failure", "traceback": self._exc_info_to_string(error, test)})

    def addError(self, test, error):
        super().addError(test, error)
        events.append({"identity": test.id(), "outcome": "error", "traceback": self._exc_info_to_string(error, test)})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        events.append({"identity": test.id(), "outcome": "skip", "reason": reason})

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error is not None:
            events.append({"identity": test.id(), "subtest": subtest.id(), "outcome": "subtest-refusal",
                           "traceback": self._exc_info_to_string(error, test)})


try:
    plan_raw = PLAN_PATH.read_bytes()
    require(sha(plan_raw) == args.plan_sha256, "Exact reviewed execution plan changed")
    plan = json.loads(plan_raw)
    require(read_ref(plan["runner"]) == runner_raw, "Exact reviewed runner changed")
    require(sha(RECIPE_PATH.read_bytes()) == RECIPE_SHA == plan["source_recipe"]["sha256"], "Final source recipe changed")
    recipe = json.loads(read_ref(plan["source_recipe"]))
    gate = json.loads(read_ref({"path": str(args.source_acceptance), "sha256": args.source_acceptance_sha256}))
    require(gate["verdict"] == "PASSIVE_SOURCE_ACCEPTED" and gate["source_recipe_sha256"] == RECIPE_SHA
            and gate["execution_plan_sha256"] == args.plan_sha256 and gate["runner_sha256"] == runner_sha,
            "Matching independent passive source/runner/plan acceptance is required")
    reference = json.loads(read_ref(plan["actual_sparse_source_map"]))
    finite = json.loads(read_ref(plan["current_finite_source_map"]))
    imports = json.loads(read_ref(plan["named_import_dependencies"]))
    eligibility = json.loads(read_ref(plan["eligibility"]))
    body_custody = json.loads(read_ref(plan["body_custody"]))
    original_sparse = json.loads(read_ref(plan["original_sparse_source_map"]))
    prerequisite = json.loads(read_ref(plan["include_build_prerequisites"]))
    original_result = json.loads(read_ref(plan["original_nine_API_results"]))
    read_ref(plan["original_nine_independent_review"])
    require(len(original_sparse) == 200 and original_sparse == finite | imports["inputs"]
            and len(finite) == 175 and imports["count"] == 25
            and len(reference) == 220 and len(prerequisite["added_inputs"]) == 20
            and reference == original_sparse | prerequisite["added_inputs"]
            and not set(original_sparse) & set(prerequisite["added_inputs"]),
            "Expanded220 is exact original200 plus literal included-build20 only")
    require(original_result["source_api_passed"] is False and original_result["source_inputs_held"] is True
            and original_result["source_input_count"] == 200 and original_result["selected_method_bodies_executed"] == 0
            and original_result["first_refusal_step"] == "only-required-IO-three-source-plans-and-mandatory-unfiltered-refusal"
            and len(original_result["events"]) == 9 and all(row["outcome"] == "pass" for row in original_result["events"])
            and not original_result["external_forbidden_attempts"] and not original_result["forbidden_write_attempts"],
            "Exactly nine original accepted API events must be reused, not replayed")
    names = eligibility["selected"]
    require(len(names) == len(set(names)) == eligibility["count"] == 12
            and names == eligibility["new_methods"] + eligibility["changed_owning_methods"],
            "Only exact never-executed NEW8 and four genuinely changed bodies are eligible")
    for row in body_custody:
        module, classname, method = row["identity"].split(".")
        raw = (ROOT / row["relative"]).read_bytes()
        require(row["identity"] in names and sha(raw) == row["after_module_sha256"]
                and sha(physical_method(raw, classname, method)) == row["after_body_sha256"],
                "An owning physical body/module seal changed")
    if args.phase == "selected12":
        require(args.source_api_results is not None and args.source_api_results_sha256 is not None,
                "Accepted original API receipt is required before bodies load")
        api_receipt = json.loads(read_ref({"path": str(args.source_api_results), "sha256": args.source_api_results_sha256}))
        require(api_receipt["source_plan_recovery_passed"] is True and api_receipt["source_recipe_sha256"] == RECIPE_SHA
                and api_receipt["execution_plan_sha256"] == args.plan_sha256 and api_receipt["runner_sha256"] == runner_sha
                and api_receipt["source_inputs_held"] is True and api_receipt["source_input_count"] == 220
                and api_receipt["original_nine_API_results_sha256"] == plan["original_nine_API_results"]["sha256"]
                and api_receipt["selected_method_bodies_executed"] == 0
                and not api_receipt["external_forbidden_attempts"] and not api_receipt["forbidden_write_attempts"],
                "Only-failed source-plan recovery plus original accepted nine must qualify first")
    else:
        require(args.source_api_results is None and args.source_api_results_sha256 is None, "API stage has no reused execution receipt")
    before, before_state = snapshot()
    require(before == reference, "Actual expanded source differs from its exact220 sealed reference")
    write_json(OUT / "source-inputs-before.json", before)
    write_json(OUT / "source-file-state-before.json", before_state)
    write_json(OUT / "launch-custody.json", {"phase": args.phase, "source_recipe_sha256": RECIPE_SHA,
        "execution_plan_sha256": args.plan_sha256, "runner_sha256": runner_sha,
        "source_acceptance": {"path": str(args.source_acceptance), "sha256": args.source_acceptance_sha256},
        "source_api_results": str(args.source_api_results) if args.source_api_results is not None else None,
        "source_api_results_sha256": args.source_api_results_sha256, "selected_identities": names})
    temporary = OUT / "disposable-fixtures"
    temporary.mkdir()
    tempfile.tempdir = str(temporary)
    os.environ["NATIVECMPKIT_IO_REMOTE_ROUTING_TREE"] = str(ROOT)
    os.environ["NATIVECMPKIT_IO_REMOTE_TREE"] = str(ROOT)
    sys.path.insert(0, str(ROOT / "scripts/ci"))
    sys.setprofile(profile)
    if args.phase == "source-plan-recovery":
        api_started = time.monotonic()
        with redirect_stdout(api_output), redirect_stderr(api_output):
            current_step = "only-required-IO-three-source-plans-and-mandatory-unfiltered-refusal"
            library = importlib.import_module("library_tests")
            remote = importlib.import_module("android_io_remote_documents")
            workflow = importlib.import_module("workflow_matrix")
            for focus in remote.FOCUSES:
                selected = library.plan(ROOT, "android-device", only_modules=("calf-io",), focus=focus)
                expected_count = 2 if focus == "android-io-controlled-remote" else 1
                require(selected["explicit_module_subset"] == ["calf-io"] and selected["complete_suite_requested"] is False
                        and len(selected["expected"]) == 1
                        and len(selected["expected"][0]["required_testcases"]) == expected_count
                        and len(workflow.matrix(focus)["include"]) == 1, "Exact IO setup source plan differs")
                write_json(OUT / (focus + ".source-plan.json"), selected)
                events.append({"api": "library_tests.plan/workflow_matrix.matrix", "focus": focus,
                               "outcome": "pass", "source_only_case_references": expected_count})
            try:
                library.plan(ROOT, "android-device")
            except ValueError as error:
                require(str(error) == "Enabled API35-only callback requires exact finite Camera selection; unrestricted Camera/all discovery refuses before host work",
                        "Unfiltered refusal changed")
                events.append({"api": "library_tests.plan unfiltered", "outcome": "mandatory exact refusal"})
            else:
                raise AssertionError("Unfiltered aggregate discovery admitted")
        api_seconds = time.monotonic() - api_started
    else:
        current_step = "exact12-loading-without-discovery-or-API-replay"
        suite = unittest.TestSuite()
        for identity in names:
            module_name, classname, method_name = identity.split(".")
            module = importlib.import_module(module_name)
            require(Path(module.__file__).resolve() == ROOT / "scripts/ci" / (module_name + ".py"), "Selected module displaced")
            klass = getattr(module, classname)
            require(issubclass(klass, unittest.TestCase) and method_name in klass.__dict__, "Exact owning case/method is required")
            test = klass(method_name)
            require(test.id() == identity, "Selected exact identity differs")
            suite.addTest(test)
        require(suite.countTestCases() == 12, "Exactly12 selected cases are required")
        current_step = "exact12-once"
        with redirect_stdout(api_output), redirect_stderr(api_output):
            suite_started = time.monotonic()
            result = unittest.TextTestRunner(stream=unittest_output, verbosity=2, resultclass=ExactResult).run(suite)
            suite_monotonic = time.monotonic() - suite_started
        matched = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", unittest_output.getvalue())
        require(matched is not None and int(matched[1]) == result.testsRun, "Original unittest suite clock is required")
        suite_seconds = float(matched[2])
        require(result.wasSuccessful() and result.testsRun == len(body_invocations) == 12
                and body_invocations == names and not result.skipped, "Some eligible cases failed, errored, skipped or did not execute")
    current_step = "final-import-custody-and-source-readback"
    origins = local_import_custody()
    write_json(OUT / "actual-imported-source-origins.json", origins)
    require(not external_attempts and not write_attempts and not unapproved_bodies, "A forbidden boundary was attempted")
except BaseException:
    refusal = traceback.format_exc()
    with (OUT / "first-refusal.log").open("x", encoding="utf-8") as stream:
        stream.write(refusal)
finally:
    sys.setprofile(None)
    if reference is not None:
        try:
            after, after_state = snapshot()
            write_json(OUT / "source-inputs-after.json", after)
            write_json(OUT / "source-file-state-after.json", after_state)
        except BaseException:
            snapshot_refusal = traceback.format_exc()
            with (OUT / "source-readback-refusal.log").open("x", encoding="utf-8") as stream:
                stream.write(snapshot_refusal)
            refusal = (refusal or "") + snapshot_refusal
    held = before is not None and before == after == reference and before_state == after_state
    if not held and refusal is None:
        refusal = "Complete actual220 source/file-state custody was not held"
    with (OUT / "source-api-or-captured-output.log").open("x", encoding="utf-8") as stream:
        stream.write(api_output.getvalue())
    with (OUT / "unittest.log").open("x", encoding="utf-8") as stream:
        stream.write(unittest_output.getvalue())
    report = {"stage": STAGES[args.phase], "phase": args.phase, "execution_started_utc": execution_started_utc,
        "scope": "Only failed IO source plans, then first NEW8+changed4; zero ROOT/compiler/APK/Apple/native/browser/CI-leaf/provider/issue acceptance",
        "source_inventory": "Expanded source220 = exact original sparse200 + twenty literal include-build prerequisites; finite175 unchanged; not canonical ROOT/consumer/compiler/native totals",
        "source_recipe_sha256": RECIPE_SHA, "execution_plan_sha256": args.plan_sha256, "runner_sha256": runner_sha,
        "source_acceptance_sha256": args.source_acceptance_sha256,
        "source_api_original_results_sha256": args.source_api_results_sha256,
        "source_input_count": len(before) if before is not None else 0, "finite_current_input_count": 175,
        "source_inputs_held": held, "source_api_passed": False,
        "source_plan_recovery_passed": args.phase == "source-plan-recovery" and refusal is None and held,
        "original_nine_API_results_sha256": plan["original_nine_API_results"]["sha256"],
        "original_nine_API_groups_reused_not_replayed": 9,
        "selected12_passed": args.phase == "selected12" and refusal is None and held,
        "envelope_seconds": time.monotonic() - envelope_started,
        "api_monotonic_seconds": api_seconds, "unittest_suite_seconds": suite_seconds,
        "unittest_suite_monotonic_seconds": suite_monotonic,
        "selected_count": 12 if args.phase == "selected12" else 0,
        "tests_run": result.testsRun if result is not None else 0,
        "failures": len(result.failures) if result is not None else 0,
        "errors": len(result.errors) if result is not None else 0,
        "skipped": len(result.skipped) if result is not None else 0,
        "selected_method_bodies_executed": len(body_invocations), "method_body_identities": body_invocations,
        "eligible_identities": names, "events": events, "first_refusal_step": current_step if refusal is not None else None,
        "refusal": refusal, "external_forbidden_attempts": external_attempts,
        "forbidden_write_attempts": write_attempts, "unapproved_or_repeated_body_attempts": unapproved_bodies,
        "accepted111_other_than_changedNEW6_provider_CI_leaf_populations_replayed": False,
        "restored_source_code_executed": False}
    write_json(OUT / "results.json", report)
    print(json.dumps({key: report[key] for key in ("stage", "source_plan_recovery_passed", "selected12_passed",
        "tests_run", "selected_method_bodies_executed", "failures", "errors", "skipped", "source_input_count",
        "source_inputs_held", "api_monotonic_seconds", "unittest_suite_seconds", "envelope_seconds")}, indent=2))
    if refusal:
        print(refusal)
raise SystemExit(0 if refusal is None and held else 1)
