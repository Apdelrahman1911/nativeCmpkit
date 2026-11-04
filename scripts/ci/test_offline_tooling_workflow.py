# SPDX-License-Identifier: Apache-2.0
"""Six accepted workflow controls plus NEW2 Rust portability source controls.

The two new literal Python wrappers are exercised in process with disposable
owned files. Shell/action/index/profile source is read only. Existing helper31,
provenance12 and lifecycle results remain separately accepted, not replayed here.
"""
from __future__ import annotations

import ast
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
from unittest.mock import patch

import offline_tooling_provenance as provenance
import test_offline_tooling_reuse as factories  # Factory functions only; no helper TestCase execution.

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ".github/workflows/gradle.yml"
VALIDATE = "Validate explicit offline tooling mode and exact producer selectors"
INDEX = "Verify complete history, audit and current development indexes"
RECORD = "Record exact offline tooling signature"
OFFLINE = "Offline verification-tool adversarial fixtures (not library passes)"
PROFILE = "Select only the requested verification profile"
UPLOAD = "Keep successful fixed offline tooling scope receipt"
RESULT = "build/ci-tooling-reuse/tooling-execution/producer-result.json"
SIGNATURE = "build/ci-tooling-reuse/tooling-record/signature.json"
OUTPUT = "build/ci-tooling-reuse/tooling-execution"
TOKEN = "NATIVECMPKIT_ACTIONS_READ_TOKEN"
ENVIRONMENT = {
    "PRODUCER_RUN_ID": "11", "PRODUCER_ATTEMPT": "1",
    "PRODUCER_JOB_ID": "22", "PRODUCER_ARTIFACT_ID": "33",
}


def workflow():
    return (ROOT / WORKFLOW).read_text(encoding="utf-8")


def tooling(source=None):
    return (workflow() if source is None else source).split("\n  tooling:\n", 1)[1].split("\n  apple-xctest-startup:\n", 1)[0]


def step(name):
    owner = tooling()
    marker = "      - name: " + name + "\n"
    if owner.count(marker) != 1:
        raise AssertionError("Require one literal owning named tooling step")
    start = owner.index(marker)
    next_step = re.search(r"(?m)^      - ", owner[start + len(marker):])
    return owner[start:start + len(marker) + next_step.start()] if next_step else owner[start:]


def python_blocks(owner):
    result = re.findall(r"(?m)^          python3 -B - <<'([A-Z_]+)'\n(.*?)^          \1\n", owner, re.S)
    return [textwrap.dedent(body) for _, body in result]


def inline(code, environment, root=None):
    """Only the actual current literal wrapper; no shell, CLI or whole module."""
    out, err = io.StringIO(), io.StringIO()
    exit_code = 0
    with patch.dict(os.environ, environment, clear=True), patch.object(sys, "path", list(sys.path)), \
            patch.object(provenance, "ROOT", ROOT if root is None else root), redirect_stdout(out), redirect_stderr(err):
        try:
            exec(compile(code, "current-owning-offline-workflow-wrapper", "exec"), {})
        except SystemExit as error:
            exit_code = error.code
    return exit_code, out.getvalue(), err.getvalue()


def producer_model():
    """Explicit modeled wrapper input, never a genuine producer certificate."""
    signature = "a" * 64
    return {"mode": "produce", "outcome": "passed", "reusable_producer_certificate": True,
            "new_scope_executions": 10, "authentication_requested": False,
            "signature_sha256": signature, "artifact_name": provenance.reuse.ARTIFACT_PREFIX + signature}


def reuse_models(storage=False):
    """Four sanitized modeled held files; zero HTTP/acquisition/scope work."""
    reuse = provenance.reuse
    signature = factories.model_signature()
    ids = dict(zip(provenance.SELECTORS, (int(value) for value in ENVIRONMENT.values())))
    checked = {"schema": reuse.SCHEMA, "eligible": True, "signature_sha256": signature["signature_sha256"], **ids,
               "producer_workflow_conclusion": "success", "offline_scopes_reused": 10, "new_scope_executions": 0,
               "native_failure_waived": False, "library_or_native_results_reused": False, "consumer_results_reused": False,
               "release_readiness_certified": False, "authenticated_transport_by_helper": False}
    decision = {**provenance.common_result("reuse", True), "checker_decision": checked, "new_scope_executions": 0,
                "signature_sha256": signature["signature_sha256"], "authenticated_acquisition_completed": True,
                "reusable_producer_certificate": False, "original_zip_sha256": "b" * 64, "original_zip_bytes": 5}
    operations = ["run-attempt", "jobs-page", "job", "artifact", "artifact-zip"] + (["storage-zip"] if storage else [])
    requests = []
    for number, operation in enumerate(operations, 1):
        redirect = operation == "artifact-zip" and storage
        requests.append({"number": number, "operation": operation, "parameters": {**ids, **({"page": 1} if operation == "jobs-page" else {})},
                         "channel": "signed-storage" if operation == "storage-zip" else "authenticated-api", "started": True,
                         "completion_attempted": True, "response": {"status": 302 if redirect else 200,
                         "outcome": "approved-storage-redirect" if redirect else "complete-original-response",
                         "body": {"availability": "unread"} if redirect else {"complete": True, "bytes": 5, "sha256": "b" * 64}}})
    ledger = {"schema": provenance.SCHEMA, "api_requests_started": 5, "storage_hops_started": int(storage), "requests": requests,
              "automatic_retries": False, "automatic_redirects": False, "raw_headers_or_signed_urls_exported": False}
    return signature, signature, decision, ledger


def stage_reuse(root, values, omit=None):
    raw = {}
    for leaf, value in zip(("signature.json", "signature-after.json", "reuse-decision.json", "acquisition-summary.json"), values):
        target = root / OUTPUT / leaf
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()
        if leaf == omit:
            continue
        raw[leaf] = provenance.reuse.canonical(value) + b"\n"
        target.write_bytes(raw[leaf])
    return raw


def reuser_environment(signature, output):
    reuse = provenance.reuse
    return {"TOOLING_MODE": "reuse", **ENVIRONMENT, "GITHUB_OUTPUT": str(output), "GITHUB_REPOSITORY": reuse.REPOSITORY,
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/" + reuse.BRANCH,
            "GITHUB_JOB": "tooling", "GITHUB_SHA": signature["source"]["revision"], "GITHUB_RUN_ID": "44", "GITHUB_RUN_ATTEMPT": "1"}


class OfflineToolingWorkflowControls(unittest.TestCase):
    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("An owning source/wrapper control cannot execute network or external processes")
        for owner, name in ((socket, "socket"), (socket, "create_connection"),
                            (subprocess, "run"), (subprocess, "Popen")):
            guard = patch.object(owner, name, forbidden)
            guard.start()
            self.addCleanup(guard.stop)

    def test_w1_explicit_string_inputs_and_sanitized_preflight_precede_record_and_token(self):
        source = workflow()
        inputs = source.split("\npermissions:\n", 1)[0]
        self.assertEqual(1, inputs.count("options: ["))
        declaration = inputs.split("      offline_tooling_mode:\n", 1)[1].split("      producer_run_id:\n", 1)[0]
        self.assertIn("        type: string\n", declaration)
        self.assertIn("        default: 'off'\n", declaration)
        for name in provenance.SELECTORS:
            declaration = re.search(r"(?ms)^      " + name + r":\n(.*?)(?=^      [a-z][a-z_]*:|\Z)", inputs).group(1)
            self.assertIn("        type: string\n", declaration)
            self.assertIn("        default: ''\n", declaration)
        owner = step(VALIDATE)
        self.assertIn("TOOLING_MODE: ${{ inputs.offline_tooling_mode }}", owner)
        self.assertNotIn("github.token", owner)
        self.assertNotIn(TOKEN, owner)
        self.assertNotIn(" || 'off'", source)
        blocks = python_blocks(owner)
        self.assertEqual(1, len(blocks))
        for mode in ("off", "produce", "reuse"):
            environment = {"TOOLING_MODE": mode, **{key: value if mode == "reuse" else "" for key, value in ENVIRONMENT.items()}}
            self.assertEqual((0, "", ""), inline(blocks[0], environment))
        for environment in ({"TOOLING_MODE": "", **{key: "" for key in ENVIRONMENT}},
                            {"TOOLING_MODE": "reuse", **ENVIRONMENT, "PRODUCER_ARTIFACT_ID": ""}):
            code, out, err = inline(blocks[0], environment)
            self.assertEqual(2, code)
            self.assertEqual("", out)
            capsule = json.loads(err)
            self.assertEqual("workflow-configuration", capsule["boundary"])
            self.assertFalse(capsule["primary_refusal"]["exception_messages_chains_locals_exported"])
            self.assertNotIn(str(ROOT), err)
            self.assertNotIn("Traceback", err)
        names = [INDEX, VALIDATE, RECORD, OFFLINE, PROFILE, UPLOAD]
        positions = [tooling().index("      - name: " + name + "\n") for name in names]
        self.assertEqual(sorted(positions), positions)

    def test_w2_exact_recorded_signature_four_id_mode_branches_have_one_driver_and_no_fallback(self):
        record = step(RECORD)
        self.assertIn("if: inputs.offline_tooling_mode == 'produce' || inputs.offline_tooling_mode == 'reuse'", record)
        self.assertEqual(1, record.count("scripts/ci/offline_tooling_reuse.py capture"))
        self.assertIn("--output " + SIGNATURE, record)
        owner = step(OFFLINE)
        self.assertEqual(1, owner.count('python3 -B scripts/ci/offline_tooling_provenance.py "${arguments[@]}"'))
        self.assertIn('arguments=(--mode "$TOOLING_MODE" --output-dir ' + OUTPUT + ')', owner)
        branches = owner.split('          case "$TOOLING_MODE" in\n', 1)[1].split('          esac\n', 1)[0]
        self.assertIn("            off) ;;\n", branches)
        produce = branches.split("            produce)\n", 1)[1].split("              ;;\n", 1)[0]
        reuse = branches.split("            reuse)\n", 1)[1].split("              ;;\n", 1)[0]
        self.assertEqual('              arguments+=(--recorded-signature ' + SIGNATURE + ')\n', produce)
        self.assertIn("--recorded-signature " + SIGNATURE, reuse)
        for field, variable in zip(provenance.SELECTORS, ENVIRONMENT):
            self.assertEqual(1, reuse.count('--' + field.replace('_', '-') + ' "$' + variable + '"'))
            self.assertNotIn(variable, produce)
        self.assertIn("*) echo 'Unrecognized explicit offline tooling mode' >&2; exit 2 ;;", branches)
        for forbidden in ("--archive", "--run ", "--job ", "--artifact ", "--resolved-actions", "latest", "continue-on-error", "|| true"):
            self.assertNotIn(forbidden, owner)

    def test_w3_minimum_literal_read_scopes_and_ephemeral_token_are_tooling_reuse_only(self):
        source, owner = workflow(), tooling()
        top = source.split("\npermissions:\n", 1)[1].split("\nconcurrency:\n", 1)[0]
        self.assertEqual("  contents: read\n", top.strip("\n") + "\n")
        permissions = owner.split("    permissions:\n", 1)[1].split("    outputs:\n", 1)[0]
        self.assertEqual("      contents: read\n      actions: read\n", permissions)
        self.assertEqual(1, source.count(TOKEN + ":"))
        offline = step(OFFLINE)
        self.assertIn(TOKEN + ": ${{ inputs.offline_tooling_mode == 'reuse' && github.token || '' }}", offline)
        run = offline.split("        run: |\n", 1)[1]
        self.assertEqual(1, run.count(TOKEN))
        self.assertIn('python3 -B scripts/ci/offline_tooling_provenance.py "${arguments[@]}"\n          unset ' + TOKEN + "\n          python3 -B - <<'PYTHON'", run)
        self.assertNotIn("github.token", source.replace(offline, "", 1))
        self.assertIn("persist-credentials: false", owner)
        self.assertIn("no publication/deployment", source.lower())
        self.assertIn("action shas are voluntary, not a required setting", source.lower())

    def test_w4_five_fresh_indexes_and_requested_profile_remain_outside_reused_scopes(self):
        index, profile = step(INDEX), step(PROFILE)
        commands = re.findall(r"(?m)^          python3 ([^\n]+)$", index)
        self.assertEqual(["scripts/migration/verify_migration.py", "scripts/audit/validate_audit.py",
                          "scripts/audit/source_inventory.py --check", "scripts/development/validate_resolutions.py --check",
                          "scripts/development/generate_icon_catalogues.py --check"], commands)
        self.assertNotIn("        if:", index)
        self.assertNotIn("        if:", profile)
        self.assertIn('PROFILE: ${{ inputs.profile }}', profile)
        self.assertIn('python3 scripts/ci/workflow_matrix.py "$PROFILE"', profile)
        self.assertIn('workflow_matrix.preflight_plans(os.environ["PROFILE"])', profile)
        self.assertNotIn("TOOLING_MODE", profile)
        self.assertNotIn(TOKEN, profile)
        self.assertEqual(10, len(provenance.reuse.SCOPES))
        for command in commands:
            self.assertFalse(any(command.split()[0] in provenance.reuse.scope_command(*scope) for scope in provenance.reuse.SCOPES))
        suffix = workflow().split("\n  apple-xctest-startup:\n", 1)[1]
        self.assertNotIn(TOKEN, suffix)
        self.assertNotIn("offline_tooling_provenance.py", suffix)
        self.assertIn("\n  consumer-core-io:\n    needs: tooling\n", suffix)
        self.assertIn("\n  webview-consumer:\n    needs: tooling\n", suffix)
        self.assertIn("\n  library-tests:\n    needs: tooling\n", suffix)

    def test_w5_only_new_passed_producer_emits_signature_name_and_single_receipt_upload(self):
        blocks = python_blocks(step(OFFLINE))
        self.assertEqual(1, len(blocks))
        with tempfile.TemporaryDirectory(prefix="offline-workflow-owned-control-") as private:
            root = Path(private)
            result, output = root / RESULT, root / "github-output-control"
            result.parent.mkdir(parents=True)
            model = producer_model()
            result.write_text(json.dumps(model), encoding="utf-8")
            self.assertEqual((0, "", ""), inline(blocks[0], {"TOOLING_MODE": "produce", "GITHUB_OUTPUT": str(output)}, root))
            self.assertEqual("artifact_name=" + model["artifact_name"] + "\n", output.read_text())
            output.unlink()
            result.unlink()
            self.assertEqual((0, "", ""), inline(blocks[0], {"TOOLING_MODE": "off", "GITHUB_OUTPUT": str(output)}, root))
            self.assertFalse(output.exists())
            for storage in (False, True):
                models = reuse_models(storage)
                raw = stage_reuse(root, models)
                status, out, err = inline(blocks[0], reuser_environment(models[0], output), root)
                self.assertEqual((0, ""), (status, err))
                self.assertLessEqual(len(out.encode()), 8193)  # Fixed <=8192-byte capsule plus its one newline.
                self.assertFalse(output.exists())
                capsule = json.loads(out)
                self.assertEqual("nativecmpkit-offline-reuse-workflow668-review-v1", capsule["schema"])
                self.assertEqual(0, capsule["counts"]["new_scope_executions"])
                self.assertEqual((5, int(storage)), (capsule["counts"]["api_requests_started"], capsule["counts"]["storage_hops_started"]))
                self.assertEqual(44, capsule["reuser"]["run_id"])
                self.assertIsNone(capsule["reuser"]["job_id"])
                for key, value in zip(provenance.SELECTORS, ENVIRONMENT.values()):
                    self.assertEqual(int(value), capsule["producer"][key])
                for leaf in raw:
                    self.assertEqual(provenance.reuse.digest(raw[leaf]), capsule["digests"][leaf])
                for forbidden in (str(root), "https://", '"requests":', "modeled version", "Authorization", "signature.json\":{"):
                    self.assertNotIn(forbidden, out)
        upload = step(UPLOAD)
        self.assertIn("if: success() && inputs.offline_tooling_mode == 'produce'", upload)
        self.assertIn("name: ${{ steps.offline.outputs.artifact_name }}", upload)
        self.assertIn("path: " + OUTPUT + "/receipt.json", upload)
        self.assertIn("if-no-files-found: error", upload)
        self.assertIn("retention-days: 7", upload)
        self.assertEqual(1, tooling().count("uses: actions/upload-artifact@"))
        for forbidden in ("*", "reuse-decision", "archive.zip", "run.json", "job.json", "artifact.json", ".log", ".apk", ".app"):
            self.assertNotIn(forbidden, upload)

    def test_w6_original_wrapper_refusals_are_sanitized_for_partial_unproduced_and_shared_outputs(self):
        code = python_blocks(step(OFFLINE))[0]
        ast.parse(code)
        ast.parse(python_blocks(step(VALIDATE))[0])
        with tempfile.TemporaryDirectory(prefix="PRIVATE-WORKFLOW-CONTROL-") as private:
            root = Path(private)
            result, output = root / RESULT, root / "github-output-control"
            result.parent.mkdir(parents=True)
            variants = [{**producer_model(), "outcome": "failed"}, {**producer_model(), "reusable_producer_certificate": False},
                        {**producer_model(), "new_scope_executions": True}, {**producer_model(), "authentication_requested": True},
                        {**producer_model(), "signature_sha256": "private-invalid-signature\n"}, {"mode": "produce"}, None, "hardlinked"]
            for model in variants:
                if result.exists():
                    result.unlink()
                link = root / "shared-control"
                if link.exists():
                    link.unlink()
                if model is not None:
                    result.write_text(json.dumps(producer_model() if model == "hardlinked" else model), encoding="utf-8")
                if model == "hardlinked":
                    os.link(result, link)
                with self.subTest(kind=type(model).__name__):
                    status, out, err = inline(code, {"TOOLING_MODE": "produce", "GITHUB_OUTPUT": str(output)}, root)
                    self.assertEqual(2, status)
                    self.assertEqual("", out)
                    self.assertFalse(output.exists())
                    capsule = json.loads(err)
                    self.assertEqual("workflow-producer-artifact-name", capsule["boundary"])
                    self.assertFalse(capsule["primary_refusal"]["exception_messages_chains_locals_exported"])
                    for forbidden in (private, "PRIVATE-WORKFLOW-CONTROL", "private-invalid-signature", "Traceback"):
                        self.assertNotIn(forbidden, err)
            link.unlink()
            result.write_text(json.dumps(producer_model()), encoding="utf-8")
            missing_output = root / "PRIVATE-output-parent" / "github-output-control"
            status, out, err = inline(code, {"TOOLING_MODE": "produce", "GITHUB_OUTPUT": str(missing_output)}, root)
            self.assertEqual((2, ""), (status, out))
            self.assertNotIn(str(missing_output), err)
            self.assertNotIn("PRIVATE-output-parent", err)
            self.assertFalse(missing_output.exists())
            for fault in ("private-extra-ledger", "private-extra-decision", "incomplete-body", "duplicate-number", "missing-after"):
                models = list(reuse_models())
                if fault == "private-extra-ledger":
                    models[3]["private-header"] = "PRIVATE-CREDENTIAL-WITNESS"
                elif fault == "private-extra-decision":
                    models[2]["private-header"] = "PRIVATE-CREDENTIAL-WITNESS"
                elif fault == "incomplete-body":
                    models[3]["requests"][0]["response"]["body"]["complete"] = False
                elif fault == "duplicate-number":
                    models[3]["requests"][1]["number"] = 1
                stage_reuse(root, models, "signature-after.json" if fault == "missing-after" else None)
                with self.subTest(reuse_refusal=fault):
                    status, out, err = inline(code, reuser_environment(models[0], output), root)
                    self.assertEqual((2, ""), (status, out))
                    self.assertFalse(output.exists())
                    self.assertEqual("workflow-reuse-review", json.loads(err)["boundary"])
                    for forbidden in (private, "PRIVATE-WORKFLOW-CONTROL", "PRIVATE-CREDENTIAL-WITNESS", "Traceback"):
                        self.assertNotIn(forbidden, err)

    def test_p1_explicit_rust_bootstrap_is_token_free_declared_and_precedes_eligibility_capture(self):
        # Read the real workflow and declaration; never install/observe Rust here.
        name = "Install the exact offline tooling Rust runtime before eligibility capture"
        rust = tomllib.loads((ROOT / "rust-toolchain.toml").read_text())["toolchain"]
        self.assertEqual({"channel": "1.98.0", "profile": "minimal", "components": ["rustfmt", "clippy"]}, rust)
        command = ("rustup toolchain install " + rust["channel"] + " --profile " + rust["profile"]
                   + " --no-self-update" + "".join(" --component " + item for item in rust["components"]))
        bootstrap = step(name)
        self.assertEqual("      - name: " + name + "\n"
                         "        if: inputs.offline_tooling_mode == 'produce' || inputs.offline_tooling_mode == 'reuse'\n"
                         "        run: |\n"
                         "          command -v rustup\n"
                         "          " + command + "\n", bootstrap)
        # This is the existing reviewed ordinary bootstrap, not a new action,
        # downloaded bootstrap script, default-toolchain change or compiler run.
        suffix = workflow().split("\n  apple-xctest-startup:\n", 1)[1]
        self.assertIn("          command -v rustup\n          " + command + "\n", suffix)
        self.assertEqual(1, tooling().count("rustup toolchain install "))
        for forbidden in (TOKEN, "github.token", "uses:", "continue-on-error", "curl", "wget", "sudo", "rustup default",
                          "rustup set", "cargo ", "rustc ", "gradlew", "java ", "kotlinc "):
            self.assertNotIn(forbidden, bootstrap)
        positions = [tooling().index("      - name: " + item + "\n")
                     for item in (INDEX, VALIDATE, name, RECORD, OFFLINE, PROFILE, UPLOAD)]
        self.assertEqual(sorted(positions), positions)
        self.assertNotIn("offline_tooling_mode == 'off'", bootstrap)

    def test_p2_rust_payload_runtime_is_observed_and_jvm_versions_are_tracked_source_only(self):
        # Exact dependency declarations are source inputs, not executed JVM proof.
        catalogue = tomllib.loads((ROOT / "gradle/libs.versions.toml").read_text())
        self.assertEqual(("17", "2.4.20"), (catalogue["versions"]["java"], catalogue["versions"]["kotlin"]))
        wrapper = dict(line.split("=", 1) for line in (ROOT / "gradle/wrapper/gradle-wrapper.properties").read_text().splitlines()
                       if line and not line.startswith("#"))
        self.assertEqual("https\\://services.gradle.org/distributions/gradle-9.7.1-bin.zip", wrapper["distributionUrl"])
        self.assertEqual("acd53f1edaf02f1a8ff99879f8a34b302661a057d9b063ae9e35b552f804d20a", wrapper["distributionSha256Sum"])
        source = (ROOT / "scripts/ci/offline_tooling_reuse.py").read_text()
        tree = ast.parse(source)
        functions = {item.name: ast.get_source_segment(source, item) for item in tree.body if isinstance(item, ast.FunctionDef)}
        tools = ast.literal_eval(next(item.value for item in tree.body if isinstance(item, ast.Assign)
                                     and any(isinstance(target, ast.Name) and target.id == "TOOLS" for target in item.targets)))
        self.assertEqual({"python3", "git", "bash", "sh", "node", "cargo", "rustc"}, set(tools))
        self.assertEqual((("--version",), ("-Vv",)), (tools["cargo"], tools["rustc"]))
        self.assertIn('"RUSTUP_AUTO_INSTALL": "0"', functions["command"])
        self.assertIn('command(root, str(path), "which", name)', functions["capture_runtime"])
        self.assertIn('"executable_sha256": hash_file(payload, unshared=False)', functions["capture_runtime"])
        self.assertIn('"launcher_sha256": hash_file(path, unshared=False)', functions["capture_runtime"])
        self.assertIn('"compiler_configs": configs, "tools": tools', functions["capture_runtime"])
        self.assertIn('"ls-tree", "-r", "-z", "--full-tree", "HEAD"', functions["capture_source"])
        self.assertIn('hash_file(path, git_blob_oid=oid)', functions["capture_source"])
        self.assertIn('"dependency_inputs_sha256": source["inputs_sha256"]', functions["capture"])
        # No Java/Gradle/Kotlin installation or version process is added to the
        # profile-independent tooling job. Their actual compiler/consumer gates
        # remain later independent work, even when declared input hashes agree.
        for forbidden in ("actions/setup-java@", "setup-gradle@", "gradlew --version", "java -version", "kotlinc -version"):
            self.assertNotIn(forbidden, tooling())


if __name__ == "__main__":
    unittest.main()
