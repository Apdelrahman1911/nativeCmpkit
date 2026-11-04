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
RECIPE_PATH = BASE / "FINAL-CI668-EXACT-OUTER-SOURCE-RECIPE676.json"
PLAN_PATH = BASE / "FINAL-CI668-EXECUTION-PLAN676.json"
STAGES = {"source-api": "FINAL-CI668-API-FIRST676", "selected12": "FINAL-CI668-SELECTED12-FIRST676"}
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
    require(len(reference) == 200 and len(finite) == 175 and imports["count"] == 25
            and reference == finite | imports["inputs"] and not set(finite) & set(imports["inputs"]),
            "Exact sparse200 is only finite175 plus literal25 import custody")
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
        require(api_receipt["source_api_passed"] is True and api_receipt["source_recipe_sha256"] == RECIPE_SHA
                and api_receipt["execution_plan_sha256"] == args.plan_sha256 and api_receipt["runner_sha256"] == runner_sha
                and api_receipt["source_inputs_held"] is True and api_receipt["source_input_count"] == 200
                and api_receipt["selected_method_bodies_executed"] == 0
                and not api_receipt["external_forbidden_attempts"] and not api_receipt["forbidden_write_attempts"],
                "Original matching complete API qualification must pass first")
    else:
        require(args.source_api_results is None and args.source_api_results_sha256 is None, "API stage has no reused execution receipt")
    before, before_state = snapshot()
    require(before == reference, "Actual sparse source differs from its exact200 sealed reference")
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
    if args.phase == "source-api":
        api_started = time.monotonic()
        with redirect_stdout(api_output), redirect_stderr(api_output):
            current_step = "ci668/tooling671-current-validation-and-actual175-hash-path-APIs"
            ci = importlib.import_module("ci668_outer_source_projection")
            tooling = importlib.import_module("tooling_recovery671_source_projection")
            require(ci.validate_current_sources(ROOT) and tooling.validate_current_sources(ROOT), "Strict final current validation failed")
            require(ci.current_input_hashes() == tooling.current_input_hashes() == finite
                    and ci.fixture_inputs() == tooling.fixture_inputs() == set(finite), "Actual175 API custody differs")
            document = ci._document()
            require(len(document["bindings"]) == 6 and sum(len(row["fragments"]) for row in document["bindings"].values()) == 16
                    and len(document["unchanged_inputs"]) == 159, "Final six/16/159 source domain differs")
            events.append({"api": current_step, "outcome": "pass", "current_finite_inputs": 175})
            current_step = "six-exact-current-ancestor-history-bindings-and-required-refusals"
            negative_count = 0
            for relative, row in document["bindings"].items():
                raw = (ROOT / relative).read_bytes()
                old = ci.current_source_before_ci668(relative, raw)
                require((sha(old), len(old)) == (row["before_sha256"], row["before_bytes"]), "Exact predecessor differs")
                require(tooling.current_source_before_tooling671(relative, raw) == old
                        and ci.source_before_ci668(relative, old) is old
                        and ci.peel_ci668_for_history(relative, raw) == old
                        and tooling.peel_tooling671_for_history(relative, raw) == old, "One exact outer ingress/history differs")
                for bad in (old, raw + b"\n", raw[:-1], bytearray(raw), None):
                    for api in (ci.current_source_before_ci668, tooling.current_source_before_tooling671):
                        try:
                            api(relative, bad)
                        except ValueError:
                            negative_count += 1
                        else:
                            raise AssertionError("Old/partial/drift/nonbytes current image admitted: " + relative)
                for bad in (raw + b"\n", raw[:-1], b"unrelated historical bytes"):
                    require(ci.peel_ci668_for_history(relative, bad) is bad
                            and tooling.peel_tooling671_for_history(relative, bad) is bad, "History peeled an unknown endpoint")
                try:
                    ci.current_source_before_ci668(Path(relative), raw)
                except ValueError:
                    negative_count += 1
                else:
                    raise AssertionError("Wrong relative identity admitted")
            events.append({"api": current_step, "outcome": "pass", "mandatory_refusals": negative_count})
            current_step = "original671-singleton-and-new-CI-own-guard-template"
            shared_raw = (ROOT / ci.ORIGINAL671_GUARD).read_bytes()
            restored = ci.source_before_ci668(ci.ORIGINAL671_GUARD, shared_raw)
            original_document = tooling._document()
            needle = ('SPEC_SHA256 = "' + tooling.SPEC_SHA256 + '"\n').encode()
            template = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
            require(sha(restored) == ci.ORIGINAL671_GUARD_SHA256 and len(restored) == ci.ORIGINAL671_GUARD_BYTES
                    and restored.count(needle) == 1
                    and sha(restored.replace(needle, template, 1)) == original_document["own_guard"]["template_sha256"]
                    and tooling._validate_own_guard(ROOT, original_document) == sha(shared_raw)
                    and ci._validate_own_guard(ROOT, document) == finite[ci.SOURCE_RELATIVE], "Current/ancestor singleton identity differs")
            events.append({"api": current_step, "outcome": "pass", "restored_code_executed": False})
            current_step = "dependent-IO-callback-UI-shared667-current-source-hash-path-APIs"
            loaded = {}
            for name, hash_api, path_api in (
                    ("android_io_remote_routing_source_projection", "current_input_hashes", "fixture_inputs"),
                    ("android_camera_callback_native_focus", "current_contract_hashes", "contract_input_paths"),
                    ("ios_ui_split664_source_projection", "current_input_hashes", "fixture_inputs"),
                    ("webview_current_contract667_source_projection", "current_contract_hashes", "fixture_inputs")):
                module = importlib.import_module(name)
                loaded[name] = module
                require(module.validate_current_sources(ROOT), "Dependent strict current source validation failed")
                hashes, paths = getattr(module, hash_api)(), set(getattr(module, path_api)())
                require(set(finite) <= set(hashes) <= paths <= set(reference)
                        and {relative: hashes[relative] for relative in finite} == finite
                        and all(before[relative] == digest for relative, digest in hashes.items()), "Dependent actual raw custody differs")
                events.append({"api": name + ".validate_current_sources/" + hash_api + "/" + path_api,
                               "outcome": "pass", "hash_inputs": len(hashes), "path_inputs": len(paths)})
            current_step = "exact-seven-IO-callback-composition-views-after-newest-CI-ingress"
            composition = tooling._composition_document()
            for relative, row in composition["callback_above_io"].items():
                qualified = tooling.current_source_before_tooling671(relative, (ROOT / relative).read_bytes())
                io_view = tooling.source_before_callback_composition680(relative, qualified)
                callback_view = tooling.callback_isolated_after_qualified_tooling671(relative, qualified)
                require(sha(io_view) == row["after_sha256"]
                        and sha(callback_view) == composition["callback_isolated"][relative]["after_sha256"], "Exact owning composition view differs")
            events.append({"api": current_step, "outcome": "pass", "qualified_source_views": 7})
            current_step = "callback-and-remote-source-only-contract-APIs"
            callback = loaded["android_camera_callback_native_focus"]
            contract = callback.source_contract(ROOT)
            require(callback.validate_source_contract(contract)
                    and contract["compiler_or_native_success_inferred"] is False
                    and {name: contract["source_inputs"][name] for name in finite} == finite, "Exact callback source-only contract differs")
            remote = importlib.import_module("android_io_remote_documents")
            receipt = remote.source_contract(ROOT)
            remote.validate_source_receipt(receipt)
            require(receipt["native_or_compile_success_inferred"] is False
                    and all(before[name] == digest for name, digest in receipt["source_inputs"].items()), "Exact remote source-only receipt differs")
            write_json(OUT / "callback-source-contract.json", contract)
            write_json(OUT / "remote-source-contract.json", receipt)
            events.append({"api": current_step, "outcome": "pass", "callback_inputs": len(contract["source_inputs"]),
                           "remote_inputs": len(receipt["source_inputs"])})
            current_step = "only-required-IO-three-source-plans-and-mandatory-unfiltered-refusal"
            library = importlib.import_module("library_tests")
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
        refusal = "Complete actual200 source/file-state custody was not held"
    with (OUT / "source-api-or-captured-output.log").open("x", encoding="utf-8") as stream:
        stream.write(api_output.getvalue())
    with (OUT / "unittest.log").open("x", encoding="utf-8") as stream:
        stream.write(unittest_output.getvalue())
    report = {"stage": STAGES[args.phase], "phase": args.phase, "execution_started_utc": execution_started_utc,
        "scope": "Sparse finite current source/API/NEW8+changed4 only; zero ROOT/compiler/APK/Apple/native/browser/CI-leaf/provider/issue acceptance",
        "source_inventory": "Actual sparse200 = finite175 + literal25 import custody; not canonical ROOT/consumer/compiler/native totals",
        "source_recipe_sha256": RECIPE_SHA, "execution_plan_sha256": args.plan_sha256, "runner_sha256": runner_sha,
        "source_acceptance_sha256": args.source_acceptance_sha256,
        "source_api_original_results_sha256": args.source_api_results_sha256,
        "source_input_count": len(before) if before is not None else 0, "finite_current_input_count": 175,
        "source_inputs_held": held, "source_api_passed": args.phase == "source-api" and refusal is None and held,
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
    print(json.dumps({key: report[key] for key in ("stage", "source_api_passed", "selected12_passed",
        "tests_run", "selected_method_bodies_executed", "failures", "errors", "skipped", "source_input_count",
        "source_inputs_held", "api_monotonic_seconds", "unittest_suite_seconds", "envelope_seconds")}, indent=2))
    if refusal:
        print(refusal)
raise SystemExit(0 if refusal is None and held else 1)
