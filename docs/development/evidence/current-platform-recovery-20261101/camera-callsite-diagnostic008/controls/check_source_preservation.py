"""Source-only preservation controls; never import project modules or execute variants."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

AREA = Path(__file__).resolve().parents[1]
RELATIVE = "scripts/ci/android_camera_developer_prerequisite.py"
BASE = (AREA / "frozen/tree" / RELATIVE).read_text()
POST = (AREA / "work/tree" / RELATIVE).read_text()
INSERTION = ('        try:\n'
             '            self.receipt["errors"][-1]["require_call_origin"] = require_call_origin(error)\n'
             '        except BaseException:\n'
             '            pass  # Observation must never replace the already-recorded primary refusal.\n')


def method(tree, owner, name):
    container = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == owner)
    return next(node for node in container.body if isinstance(node, ast.FunctionDef) and node.name == name)


def function(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def segment(source, node):
    return ast.get_source_segment(source, node)


def normalized_tree(tree):
    normalized = copy.deepcopy(tree)
    normalized.body = [node for node in normalized.body
                       if not (isinstance(node, ast.FunctionDef) and node.name == "require_call_origin")]
    failure = method(normalized, "OwnedDeveloperPrerequisite", "failure")
    failure.body = [node for node in failure.body if not isinstance(node, ast.Try)]
    return normalized


def permitted_delta(source):
    try:
        tree = ast.parse(source)
        observer = function(tree, "require_call_origin")
        failure = method(tree, "OwnedDeveloperPrerequisite", "failure")
        if sum(isinstance(node, ast.Try) for node in failure.body) != 1:
            return False
        if source.count(INSERTION) != 1:
            return False
        prefix = source[:source.index("\n\n\ndef require_call_origin(")]
        if prefix.replace(INSERTION, "", 1) + "\n" != BASE:
            return False
        if ast.dump(normalized_tree(tree), include_attributes=False) != ast.dump(ast.parse(BASE), include_attributes=False):
            return False
        dictionaries = [node for node in ast.walk(observer) if isinstance(node, ast.Dict)]
        if len(dictionaries) != 2:
            return False
        for node in dictionaries:
            if [item.value for item in node.keys] != ["source", "symbol", "line"]:
                return False
            if not isinstance(node.values[0], ast.Constant) or node.values[0].value not in (
                    "unavailable", "android_camera_developer_prerequisite.py"):
                return False
        return True
    except (StopIteration, SyntaxError, ValueError, AttributeError, TypeError):
        return False


def main():
    base, post = ast.parse(BASE), ast.parse(POST)
    checks = []

    def record(name, passed):
        checks.append({"control": name, "passed": bool(passed)})

    identities = json.loads((AREA / "frozen/input-identities.json").read_bytes())
    record("held_git_blob_bytes_match_frozen_identities", all(
        hashlib.sha256((AREA / "frozen/tree" / row["path"]).read_bytes()).hexdigest() == row["sha256"]
        for row in identities["inputs"]))
    record("only_four_failure_lines_and_appended_observer_change_source", permitted_delta(POST))
    record("all_existing_ast_statements_are_identical_after_diagnostic_removal",
           ast.dump(normalized_tree(post), include_attributes=False) == ast.dump(base, include_attributes=False))
    old_require, new_require = function(base, "require"), function(post, "require")
    record("generic_require_body_and_valueerror_raise_line47_are_unchanged",
           segment(BASE, old_require) == segment(POST, new_require) and new_require.body[0].body[0].lineno == 47)
    original_guards = [ast.dump(node, include_attributes=False) for node in ast.walk(base)
                       if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "require"]
    proposed_guards = [ast.dump(node, include_attributes=False) for node in ast.walk(post)
                       if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "require"]
    record("every_original_require_condition_message_and_call_count_is_identical", original_guards == proposed_guards)
    for name in ("prepare", "close", "control", "action_guard", "mark_reporter_dispatch"):
        record("owning_" + name + "_body_is_byte_identical",
               segment(BASE, method(base, "OwnedDeveloperPrerequisite", name)) ==
               segment(POST, method(post, "OwnedDeveloperPrerequisite", name)))
    record("native_acceptance_predicate_is_byte_identical",
           segment(BASE, function(base, "accepted")) == segment(POST, function(post, "accepted")))
    record("existing_controller_and_generic_origin_are_byte_identical",
           (AREA / "frozen/tree/scripts/ci/android_device_tests.py").read_bytes() ==
           (AREA / "work/tree/scripts/ci/android_device_tests.py").read_bytes())
    calls = [node for node in ast.walk(post) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "require_call_origin"]
    failure = method(post, "OwnedDeveloperPrerequisite", "failure")
    record("sole_observer_invocation_is_inside_existing_failure_only_boundary",
           len(calls) == 1 and failure.lineno <= calls[0].lineno <= failure.end_lineno)
    observation = next(node for node in failure.body if isinstance(node, ast.Try))
    record("diagnostic_error_catch_cannot_change_original_append_publish_or_retry",
           len(observation.body) == 1 and len(observation.handlers) == 1 and
           isinstance(observation.handlers[0].type, ast.Name) and observation.handlers[0].type.id == "BaseException" and
           len(observation.handlers[0].body) == 1 and isinstance(observation.handlers[0].body[0], ast.Pass) and
           not observation.orelse and not observation.finalbody and len(failure.body) == 3)
    observer = function(post, "require_call_origin")
    attributes = {node.attr for node in ast.walk(observer) if isinstance(node, ast.Attribute)}
    names = {node.id for node in ast.walk(observer) if isinstance(node, ast.Name)}
    record("observer_never_reads_or_formats_error_bodies_locals_results_or_environment",
           not attributes.intersection({"args", "f_locals", "f_globals", "environ", "stdout", "stderr"}) and
           not names.intersection({"str", "repr", "print", "locals", "traceback", "subprocess", "os"}))
    record("observer_has_fixed_64_frame_bound_and_registered_owning_code_identity",
           "range(64)" in segment(POST, observer) and "node.tb_next is not None" in segment(POST, observer) and
           "node.tb_frame.f_code is require.__code__" in segment(POST, observer) and
           "getattr(function, \"__code__\", None) is caller" in segment(POST, observer) and
           "caller.co_lines()" in segment(POST, observer))
    registered = {"Journal", "OwnedFreshGuest", "Reporter", "OwnedDeveloperPrerequisite"}
    guarded_classes = {node.name for node in base.body if isinstance(node, ast.ClassDef) and any(
        isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "require"
        for call in ast.walk(node))}
    record("explicit_class_registry_covers_every_current_owning_guard_container", guarded_classes <= registered)
    run = json.loads((AREA / "evidence/new-controls001.json").read_bytes())
    baseline = json.loads((AREA / "evidence/baseline-red001.json").read_bytes())
    record("one_baseline_red_and15_new_models_are_bound_to_exact_test_and_final_postimage",
           baseline["selected"] == baseline["executed"] == 1 and baseline["passed"] is False and
           run["selected"] == run["executed"] == 15 and run["passed"] is True and
           run["helper_sha256"] == hashlib.sha256(POST.encode()).hexdigest() and
           baseline["test_sha256"] == run["test_sha256"] == hashlib.sha256(
               (AREA / "work/tree/scripts/ci/test_android_camera_prerequisite_require_origin.py").read_bytes()).hexdigest())
    variants = {
        "original_guard_condition_weakening": POST.replace('require(self.original is not None, "Original exact state was not acquired")',
                                                            'require(True, "Original exact state was not acquired")', 1),
        "original_valueerror_class_replacement": POST.replace("raise ValueError(message)", "raise RuntimeError(message)", 1),
        "raw_error_body_export": POST.replace('self.receipt["errors"][-1]["require_call_origin"] = require_call_origin(error)',
                                               'self.receipt["errors"][-1]["require_call_origin"] = str(error)', 1),
        "unfixed_private_source_export": POST.replace('return {"source": "android_camera_developer_prerequisite.py", "symbol": symbol, "line": number}',
                                                       'return {"source": __file__, "symbol": symbol, "line": number}', 1),
    }
    refusals = [{"control": name, "variant_is_changed": source != POST, "refused": not permitted_delta(source)}
                for name, source in variants.items()]
    result = {"schema": "nativecmpkit.private-camera-require-origin-source-controls.v1",
              "source_checks": checks, "modeled_source_refusals": refusals, "original_require_call_count": len(original_guards),
              "base_sha256": hashlib.sha256(BASE.encode()).hexdigest(), "postimage_sha256": hashlib.sha256(POST.encode()).hexdigest(),
              "passed": all(row["passed"] for row in checks) and all(row["variant_is_changed"] and row["refused"] for row in refusals),
              "source_only": True, "variants_executed": False, "actual_caller_or_condition_inferred": False,
              "native_sdk_build_dispatch_or_live_project_imports": 0}
    (AREA / "evidence/source-controls001.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"source_checks": len(checks), "modeled_source_refusals": len(refusals),
                      "original_require_call_count": len(original_guards), "passed": result["passed"]}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
