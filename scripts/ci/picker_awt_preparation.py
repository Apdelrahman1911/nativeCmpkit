#!/usr/bin/env python3
"""One standard owned PREPARE only; no inventory/JUnit/native-test replay.

Uses the original AWT generation resource command, immutable600s budget,
runtime/source/JDK/resource custody and directory/process cleanup owners.
Only the same five literal JSON names are public. A prep-only pass is NOT a
native result, consumer/release verification, or a reusable native certificate.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import picker_awt_generation as r

FOCUS = "picker-awt-preparation"
WORKFLOW = ".github/workflows/picker-awt-preparation.yml"
OWNING_INPUTS = ("scripts/ci/picker_awt_preparation.py", "scripts/ci/picker_awt_prepare_failure.py",
                 "scripts/ci/test_picker_awt_prepare_failure_diagnostics.py", WORKFLOW)
SCOPE = ("One fresh standard macOS arm64 Temurin17/Rust1.98.0 PREPARE through the original three resource tasks. "
         "Bounded failure-line observations only, not an established root cause. "
         "No inventory/JUnit/native test or accepted source-control replay, complete compiler counts, native reuse "
         "certificate, whole#58, consumer, package, deployment or release acceptance.")


def source_snapshot(root: Path) -> dict:
    inputs = r.source_snapshot(root)
    if any(name not in inputs for name in OWNING_INPUTS):
        raise r.Refusal("preparation-only-owning-source-input-missing")
    return inputs


def run(output_argument: Path) -> int:
    root = r.library.ROOT
    output = r.library.safe_path(root, output_argument.as_posix())
    allowed = root / "build/ci-verification"
    if output == allowed or not output.is_relative_to(allowed) or output.exists():
        raise r.Refusal("new-owned-output-below-ci-verification-required")
    output.mkdir(parents=True, mode=0o700)
    private = output / "private"
    private.mkdir(mode=0o700)
    budget = r.shared.NativeBudget()
    receipt = {"schema_version": 1, "test_focus": FOCUS, "passed": False, "preparation_passed": False, "scope": SCOPE,
               "complete_suite_requested": False, "native_operation_budget_seconds": r.shared.NATIVE_BUDGET_SECONDS,
               "native_processes_requested": 0, "inventory_processes_requested": 0, "native_JUnit_requested": 0,
               "native_reuse_certificate": False, "cause_established": False,
               "tests": 0, "failures": 0, "errors": 0, "skipped": 0, "test_counts_complete": False, "phases": {}}
    before, context, jdk, cp, native, revision = None, None, None, None, None, None
    owned_directories = None
    stage = "source-runtime-before"
    try:
        r.reject_overrides(dict(os.environ))
        stage = "owned-jvm-directory-preparation"
        owned_directories = r.OwnedJavaDirectories(root, private, budget)
        stage = "source-runtime-before"
        before = source_snapshot(root)
        revision = r.library.git_revision(root)
        context = r.library.runtime_context.capture(expected_arch="arm64", apple=True, require_clean=True)
        r.shared.require_runtime(context, revision)
        _, jdk = r.qualify_jdk(context, budget)
        version = r.default_version(root, budget)
        r.write_public(output, "inputs-before.json", before)
        r.write_public(output, "runtime-before.json", {"context": context, "jdk": jdk,
                       "owned_java_directories": owned_directories.identity()})
        receipt.update(source_revision=revision, source_tree_dirty=False, selected_inputs=len(before),
                       inputs_before_sha256=r.library.input_digest(before), library_version=version)
        for name in r.FRESH_OUTPUTS:
            if r.library.safe_path(root, name).exists():
                raise r.Refusal("fresh-standard-host-output-required-no-delete-or-cache-fallback")
        stage = "prepare"
        owned_directories.require()
        prepared = r.phase(root, private, stage, r.prepare_command(root, private), budget, receipt)
        owned_directories.require()
        receipt["preparation"] = r.review_prepare(prepared)
        if source_snapshot(root) != before or r.qualify_jdk(context, budget)[1] != jdk:
            raise r.Refusal("source-or-qualified-jdk-changed-after-standard-preparation")
        native = r.native_identity(root, revision, version, budget)
        _, cp = r.classpath_identity(root, budget)
        r.require_bundled_identity(cp, native)
        runtime_before = {"context": context, "jdk": jdk, "classpath": cp, "native_bundle": native,
                          "owned_java_directories": owned_directories.identity()}
        r.write_public(output, "runtime-before.json", runtime_before)
        receipt["runtime_before_sha256"] = r.library.sha256(output / "runtime-before.json")
        stage = "final-held-source-runtime-and-deadline"
        after = source_snapshot(root)
        context_after = r.library.runtime_context.capture(expected_arch="arm64", apple=True, require_clean=True)
        r.shared.require_runtime(context_after, revision)
        jdk_after = r.qualify_jdk(context_after, budget)[1]
        cp_after = r.classpath_identity(root, budget)[1]
        native_after = r.native_identity(root, revision, version, budget)
        owned_directories.require()
        r.write_public(output, "inputs-after.json", after)
        r.write_public(output, "runtime-after.json", {"context": context_after, "jdk": jdk_after,
                       "classpath": cp_after, "native_bundle": native_after,
                       "owned_java_directories": owned_directories.identity()})
        receipt.update(held_owned_java_directories=True, held_inputs=before == after, held_jdk=jdk == jdk_after,
                       held_classpath=cp == cp_after, held_native_bundle=native == native_after,
                       inputs_after_sha256=r.library.input_digest(after),
                       runtime_after_sha256=r.library.sha256(output / "runtime-after.json"),
                       held_runtime_identity=context["compiler_runtime_fingerprint"] == context_after["compiler_runtime_fingerprint"])
        if (not all(receipt[key] for key in ("held_owned_java_directories", "held_inputs", "held_jdk", "held_classpath",
                                          "held_native_bundle", "held_runtime_identity")) or
                r.library.git_revision(root) != revision or set(receipt["phases"]) != {"prepare"} or
                receipt["preparation"]["executed_tests"] != 0):
            raise r.Refusal("final-held-preparation-source-runtime-and-zero-test-required")
        budget.remaining()
        receipt["native_operation_elapsed_seconds"] = budget.elapsed()
        receipt.update(passed=True, preparation_passed=True)
    except Exception as error:
        receipt.update(failed_stage=stage, error_type=type(error).__name__,
                       reason_code=str(error) if isinstance(error, r.Refusal) else "verification-error-details-private")
    finally:
        # Original failure readbacks remain secondary; no fabricated runtime-after.
        if not receipt["passed"] and before is not None:
            try:
                after = source_snapshot(root)
                r.write_public(output, "inputs-after.json", after)
                receipt.update(held_inputs=before == after, inputs_after_sha256=r.library.input_digest(after))
            except Exception as error:
                receipt["failure_source_readback_error_type"] = type(error).__name__
        if owned_directories is not None:
            if not receipt["passed"]:
                try:
                    owned_directories.require()
                except Exception as error:
                    receipt["failure_owned_java_directory_readback_error_type"] = type(error).__name__
            try:
                owned_directories.close()
                receipt["owned_java_descriptors_closed"] = True
            except Exception as error:
                if receipt["passed"]:
                    receipt.update(passed=False, preparation_passed=False, failed_stage="owned-jvm-descriptor-cleanup",
                                   error_type=type(error).__name__, reason_code="owned-jvm-descriptor-cleanup-unestablished")
                else:
                    receipt["failure_owned_java_descriptor_cleanup_error_type"] = type(error).__name__
        r.write_public(output, "receipt.json", receipt)
    print(json.dumps({key: receipt[key] for key in ("test_focus", "passed", "preparation_passed", "failed_stage", "reason_code", "scope")
                      if key in receipt}))
    return 0 if receipt["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return run(parser.parse_args().output)


if __name__ == "__main__":
    raise SystemExit(main())
