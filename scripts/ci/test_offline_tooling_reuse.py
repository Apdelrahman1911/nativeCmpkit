#!/usr/bin/env python3
"""NEW offline reuse contract models; zero hosted/full-scope/native executions."""
import copy
import datetime as dt
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import zipfile

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("offline_tooling_reuse", Path(__file__).with_name("offline_tooling_reuse.py"))
reuse = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reuse)

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
UPLOAD = "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9"
WORKFLOW_SOURCE = "jobs:\n  tooling:\n    steps:\n      - uses: " + CHECKOUT + "\n      - uses: " + UPLOAD + "\n  library:\n    needs: tooling\n"
NOW = dt.datetime(2026, 11, 4, 0, 0, 14, tzinfo=dt.timezone.utc)


def resign(signature):
    source = signature["source"]
    source["input_count"] = len(source["inputs"])
    source["inputs_sha256"] = reuse.digest(reuse.canonical(source["inputs"]))
    signature["dependency_inputs_sha256"] = source["inputs_sha256"]
    signature["workflow"]["sha256"] = source["inputs"][reuse.WORKFLOW]["sha256"]
    signature["signature_sha256"] = reuse.digest(reuse.canonical({key: value for key, value in signature.items()
                                                               if key != "signature_sha256"}))
    return signature


def model_signature():
    inputs = {path: {"mode": "100644", "sha256": reuse.digest(content.encode())} for path, content in {
        reuse.WORKFLOW: WORKFLOW_SOURCE, "scripts/ci/offline_tooling_reuse.py": "modeled committed owner",
        "scripts/ci/test_offline_tooling_reuse.py": "modeled new controls", "gradle/libs.versions.toml": "exact declarations",
        "calf-share/native/Cargo.lock": "exact lock", "docs/testing/offline-tooling-reuse.md": "modeled docs",
    }.items()}
    result = {"schema": reuse.SCHEMA, "source": {"revision": "a" * 40, "tree": "b" * 40, "inputs": inputs},
              "workflow": {"path": reuse.WORKFLOW, "tooling_actions": reuse.tooling_actions(WORKFLOW_SOURCE)},
              "runtime": {"image_os": "ubuntu24", "image_version": "20261101.1", "system": "Linux",
                          "architecture": "x86_64", "python_implementation": "CPython",
                          "os_release_sha256": "c" * 64, "installed_packages_sha256": "d" * 64,
                          "path_sha256": "e" * 64, "cargo_paths_sha256": "f" * 64,
                          "compiler_configs": {"cargo-config": None, "cargo-config-toml": None, "rustup-settings": "a" * 64},
                          "tools": {name: {"version": name + " modeled version", "executable_sha256": reuse.digest(name.encode()),
                                           "launcher_sha256": reuse.digest((name + "-launcher").encode())} for name in reuse.TOOLS}},
              "recipe_sha256": reuse.RECIPE_SHA256}
    return resign(result)


def green(scope):
    return reuse.scope_summary(scope, 0, b"modeled method ... ok\n\nRan 2 tests in 0.001s\n\nOK\n")


def producer():
    return {"repository": reuse.REPOSITORY, "workflow": reuse.WORKFLOW, "branch": reuse.BRANCH,
            "job_name": "tooling", "run_id": 101, "run_attempt": 1}


def model_receipt(signature):
    return {"schema": reuse.SCHEMA, "signature": copy.deepcopy(signature), "producer": producer(),
            "scope_results": [green(scope) for scope in reuse.SCOPES], "recorded_at_utc": "2026-11-04T00:00:11Z",
            "inputs_held": True, "passed": True, "fresh_scope_execution": True,
            "library_or_native_results_reused": False, "consumer_results_reused": False, "release_readiness_certified": False}


def archive_receipt(receipt, name="receipt.json", mode=stat.S_IFREG | 0o644, extra=False, raw=None):
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        entry = zipfile.ZipInfo(name)
        entry.external_attr = mode << 16
        entry.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(entry, reuse.canonical(receipt) if raw is None else raw)
        if extra:
            archive.writestr("foreign.json", "{}")
    return memory.getvalue()


def model_envelopes(signature, archive):
    base = "https://api.github.com/repos/" + reuse.REPOSITORY + "/actions/"
    run = {"id": 101, "run_attempt": 1, "url": base + "runs/101", "path": reuse.WORKFLOW,
           "event": "workflow_dispatch", "head_branch": reuse.BRANCH, "head_sha": signature["source"]["revision"],
           "status": "completed", "conclusion": "success", "repository": {"id": 1000, "full_name": reuse.REPOSITORY},
           "head_repository": {"id": 1000, "full_name": reuse.REPOSITORY}}
    job = {"id": 202, "run_id": 101, "run_attempt": 1, "url": base + "jobs/202", "run_url": base + "runs/101",
           "head_sha": run["head_sha"], "head_branch": reuse.BRANCH, "name": "tooling", "status": "completed",
           "conclusion": "success", "labels": ["ubuntu-24.04"], "started_at": "2026-11-04T00:00:10Z",
           "completed_at": "2026-11-04T00:00:13Z", "steps": [{"number": number, "name": name,
                "status": "completed", "conclusion": "success"} for number, name in enumerate(reuse.REQUIRED_STEPS, 1)]}
    artifact = {"id": 303, "url": base + "artifacts/303", "archive_download_url": base + "artifacts/303/zip",
                "name": reuse.ARTIFACT_PREFIX + signature["signature_sha256"], "expired": False,
                "size_in_bytes": len(archive), "digest": "sha256:" + reuse.digest(archive),
                "created_at": "2026-11-04T00:00:12Z", "expires_at": "2026-11-11T00:00:12Z",
                "workflow_run": {"id": 101, "repository_id": 1000, "head_repository_id": 1000,
                                 "head_sha": run["head_sha"], "head_branch": reuse.BRANCH}}
    return run, job, artifact


class OfflineToolingReuseControls(unittest.TestCase):
    def setUp(self):
        self.signature = model_signature()
        self.receipt = model_receipt(self.signature)
        self.archive = archive_receipt(self.receipt)
        self.run, self.job, self.artifact = model_envelopes(self.signature, self.archive)

    def candidate(self, current=None, receipt=None, archive=None, run=None, job=None, artifact=None):
        if receipt is not None:
            archive = archive_receipt(receipt)
        archive = self.archive if archive is None else archive
        selected_artifact = copy.deepcopy(self.artifact) if artifact is None else artifact
        if receipt is not None or archive != self.archive:
            selected_artifact["size_in_bytes"] = len(archive)
            selected_artifact["digest"] = "sha256:" + reuse.digest(archive)
        return reuse.check(self.signature if current is None else current, archive, self.run if run is None else run,
                           self.job if job is None else job, selected_artifact, now=NOW)

    def test_complete_candidate_is_offline_only_and_does_not_certify_transport_or_native(self):
        result = self.candidate()
        self.assertIs(True, result["eligible"])
        self.assertEqual(10, result["offline_scopes_reused"])
        self.assertEqual(0, result["new_scope_executions"])
        for key in ("authenticated_transport_by_helper", "library_or_native_results_reused",
                    "consumer_results_reused", "native_failure_waived", "release_readiness_certified"):
            self.assertIs(False, result[key])

    def test_successful_tooling_from_native_red_run_retains_that_failure_explicitly(self):
        run = copy.deepcopy(self.run); run["conclusion"] = "failure"
        result = self.candidate(run=run)
        self.assertEqual("failure", result["producer_workflow_conclusion"])
        self.assertIs(False, result["native_failure_waived"])

    def test_source_dependency_workflow_action_and_runtime_drift_each_rejects_prior_result(self):
        for category in ("source", "dependency", "workflow", "action", "image", "binary", "recipe"):
            with self.subTest(category=category):
                current = copy.deepcopy(self.signature)
                if category == "source":
                    current["source"]["revision"] = "c" * 40
                elif category == "dependency":
                    current["source"]["inputs"]["calf-share/native/Cargo.lock"]["sha256"] = "1" * 64
                elif category == "workflow":
                    current["source"]["inputs"][reuse.WORKFLOW]["sha256"] = "2" * 64
                elif category == "action":
                    current["workflow"]["tooling_actions"][0]["resolved_commit"] = "3" * 40
                elif category == "image":
                    current["runtime"]["image_version"] = "20261102.1"
                elif category == "binary":
                    current["runtime"]["tools"]["node"]["executable_sha256"] = "4" * 64
                else:
                    current["recipe_sha256"] = "5" * 64
                resign(current)
                with self.assertRaises(ValueError):
                    self.candidate(current=current)

    def test_partial_corrupt_unknown_and_nonordinary_signatures_refuse_before_provenance(self):
        for category in ("digest", "schema", "tool", "map", "boolean-count", "path", "mode"):
            with self.subTest(category=category):
                current = copy.deepcopy(self.signature)
                if category == "digest":
                    current["signature_sha256"] = "0" * 64
                elif category == "schema":
                    current["schema"] = "old-tooling-v0"; resign(current)
                elif category == "tool":
                    del current["runtime"]["tools"]["cargo"]; resign(current)
                elif category == "map":
                    del current["source"]["inputs"]["scripts/ci/offline_tooling_reuse.py"]; resign(current)
                elif category == "boolean-count":
                    current["source"]["input_count"] = True
                    current["signature_sha256"] = reuse.digest(reuse.canonical({key: item for key, item in current.items() if key != "signature_sha256"}))
                elif category == "path":
                    current["source"]["inputs"]["a/../foreign"] = {"mode": "100644", "sha256": "0" * 64}; resign(current)
                else:
                    current["source"]["inputs"]["gradle/libs.versions.toml"]["mode"] = "120000"; resign(current)
                with self.assertRaises(ValueError):
                    self.candidate(current=current)

    def test_missing_duplicate_reordered_zero_boolean_red_and_foreign_scope_reports_refuse(self):
        for category in ("missing", "duplicate", "order", "zero", "boolean-tests", "boolean-exit", "red", "unknown",
                         "command", "empty-output", "bad-output-hash", "re-export", "not-held", "broadened"):
            with self.subTest(category=category):
                receipt = copy.deepcopy(self.receipt)
                scopes = receipt["scope_results"]
                if category == "missing": scopes.pop()
                elif category == "duplicate": scopes[1] = copy.deepcopy(scopes[0])
                elif category == "order": scopes[0], scopes[1] = scopes[1], scopes[0]
                elif category == "zero": scopes[0]["tests"] = 0
                elif category == "boolean-tests": scopes[0]["tests"] = True
                elif category == "boolean-exit": scopes[0]["returncode"] = False
                elif category == "red": scopes[0]["returncode"] = 1
                elif category == "unknown": scopes[0]["passed"] = "true"
                elif category == "command": scopes[0]["command"].remove("-v")
                elif category == "empty-output": scopes[0]["output_bytes"] = 0
                elif category == "bad-output-hash": scopes[0]["output_sha256"] = "unknown"
                elif category == "re-export": receipt["fresh_scope_execution"] = False
                elif category == "not-held": receipt["inputs_held"] = False
                else: receipt["consumer_results_reused"] = True
                with self.assertRaises(ValueError):
                    self.candidate(receipt=receipt)

    def test_cancelled_missing_foreign_unknown_and_red_job_metadata_refuses(self):
        mutations = (("run", "status", "queued"), ("run", "conclusion", "cancelled"), ("run", "conclusion", None),
                     ("run", "event", "workflow_call"), ("run", "path", ".github/workflows/other.yml"),
                     ("run", "head_branch", "main"), ("run", "head_sha", "d" * 40), ("run", "id", True),
                     ("job", "conclusion", "failure"), ("job", "status", "in_progress"),
                     ("job", "name", "library"), ("job", "labels", "ubuntu-24.04"),
                     ("job", "url", "https://foreign.invalid/job"))
        for which, key, value in mutations:
            with self.subTest(which=which, key=key):
                run, job = copy.deepcopy(self.run), copy.deepcopy(self.job)
                (run if which == "run" else job)[key] = value
                with self.assertRaises(ValueError):
                    self.candidate(run=run, job=job)
        for field in ("repository", "head_repository"):
            run = copy.deepcopy(self.run); run[field]["full_name"] = "foreign/fork"
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.candidate(run=run)

    def test_scope_log_parser_refuses_empty_skipped_expected_failed_or_ambiguous_results(self):
        for output, code in ((b"", 0), (b"Ran 0 tests in 0.0s\n\nOK\n", 0),
                             (b"Ran 1 test in 0.1s\n\nOK (skipped=1)\n", 0),
                             (b"Ran 1 test in 0.1s\n\nOK (expected failures=1)\n", 0),
                             (b"Ran 1 test in 0.1s\n\nFAILED (errors=1)\n", 0),
                             (b"Ran 1 test in 0.1s\n\nOK\n", 1),
                             (b"Ran 1 test in 0.1s\nOK\nRan 1 test in 0.1s\nOK\n", 0)):
            with self.subTest(output=output, code=code):
                self.assertIs(False, reuse.scope_summary(reuse.SCOPES[0], code, output)["passed"])
        output = b"Ran 1 test in 0.1s\n\nOK\nbuffered public fixture stdout\n"
        self.assertIs(True, reuse.scope_summary(reuse.SCOPES[0], 0, output)["passed"])

    def test_attempts_artifacts_and_required_named_numbered_steps_cannot_be_mixed(self):
        for category in ("job-attempt", "receipt-attempt", "artifact-run", "old-created", "missing-step", "red-step",
                         "duplicate-step", "reordered-step", "boolean-step-number", "legacy-receipt"):
            with self.subTest(category=category):
                job, artifact, receipt = copy.deepcopy(self.job), copy.deepcopy(self.artifact), copy.deepcopy(self.receipt)
                if category == "job-attempt": job["run_attempt"] = 2
                elif category == "receipt-attempt": receipt["producer"]["run_attempt"] = 2
                elif category == "artifact-run": artifact["workflow_run"]["id"] = 99
                elif category == "old-created": artifact["created_at"] = "2026-11-04T00:00:09Z"
                elif category == "missing-step": job["steps"].pop(1)
                elif category == "red-step": job["steps"][2]["conclusion"] = "skipped"
                elif category == "duplicate-step": job["steps"].append(copy.deepcopy(job["steps"][2]))
                elif category == "reordered-step": job["steps"][0], job["steps"][1] = job["steps"][1], job["steps"][0]
                elif category == "boolean-step-number": job["steps"][0]["number"] = True
                else: receipt = {"passed": True, "source_revision": self.signature["source"]["revision"]}
                with self.assertRaises(ValueError):
                    self.candidate(job=job, artifact=artifact, receipt=receipt)

    def test_original_archive_digest_expiry_size_and_literal_api_url_are_required(self):
        for key, value in (("digest", None), ("digest", "sha256:" + "0" * 64), ("expired", True),
                           ("expired", "false"), ("size_in_bytes", 1), ("expires_at", "2026-11-04T00:00:13Z"),
                           ("archive_download_url", "https://foreign.invalid/archive"), ("name", "old-green-reports")):
            with self.subTest(key=key, value=value):
                artifact = copy.deepcopy(self.artifact); artifact[key] = value
                with self.assertRaises(ValueError):
                    self.candidate(artifact=artifact)

    def test_archive_foreign_extra_symlink_encrypted_or_unbounded_members_are_not_extracted(self):
        for category in ("foreign", "extra", "symlink", "encrypted", "unbounded", "not-zip"):
            with self.subTest(category=category):
                archive = archive_receipt(self.receipt, name="../receipt.json") if category == "foreign" else (
                    archive_receipt(self.receipt, extra=True) if category == "extra" else (
                    archive_receipt(self.receipt, mode=stat.S_IFLNK | 0o777) if category == "symlink" else self.archive))
                if category == "encrypted":
                    mutable = bytearray(archive)
                    mutable[mutable.index(b"PK\x01\x02") + 8] |= 1
                    archive = bytes(mutable)
                if category == "not-zip": archive = b"not a zip"
                with patch.object(reuse, "MAX_JSON_BYTES", 128 if category == "unbounded" else reuse.MAX_JSON_BYTES):
                    with self.assertRaises((ValueError, zipfile.BadZipFile)):
                        self.candidate(archive=archive)

    def test_json_duplicate_constants_paths_and_nonordinary_acquired_inputs_refuse(self):
        for raw in (b'{"passed":true,"passed":false}', b'{"count":NaN}', b'{"count":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): reuse.parse_json(raw)
        with tempfile.TemporaryDirectory(prefix="offline-tooling-path-model-") as folder:
            root = Path(folder)
            for relative in ("/foreign", "a/../foreign", "a//foreign", "a\\foreign", "build/ci-tooling-reuse/../foreign"):
                with self.subTest(relative=relative), self.assertRaises(ValueError): reuse.safe_path(root, relative)
            confined = root / "build/ci-tooling-reuse"; confined.mkdir(parents=True)
            data = confined / "ordinary.json"; data.write_text("{}")
            self.assertEqual(b"{}", reuse.read_owned(root, "build/ci-tooling-reuse/ordinary.json"))
            os.link(data, confined / "hardlink.json")
            with self.assertRaises(ValueError): reuse.read_owned(root, "build/ci-tooling-reuse/ordinary.json")
            (root / "linked").symlink_to(confined, target_is_directory=True)
            with self.assertRaises(ValueError): reuse.safe_path(root, "linked/ordinary.json")

    def test_output_is_fresh_and_refuses_before_any_scope_population_execution(self):
        with tempfile.TemporaryDirectory(prefix="offline-tooling-output-model-") as folder:
            root = Path(folder)
            relative = "build/ci-tooling-reuse/retained.json"
            reuse.write_owned(root, relative, {"retained": True})
            with patch.object(reuse, "ROOT", root), patch.object(reuse, "run_scopes") as runner, \
                 patch.object(sys, "argv", ["offline_tooling_reuse.py", "run", "--signature", "missing.json", "--output", relative]):
                with self.assertRaises(ValueError): reuse.main()
                runner.assert_not_called()
            self.assertEqual(b'{"retained":true}\n', (root / relative).read_bytes())
            with self.assertRaises(ValueError): reuse.write_owned(root, "docs/foreign.json", {})

    def test_scope_environment_uses_fresh_home_tmp_without_credentials_or_source_overrides(self):
        parent = {"PATH": "/modeled/bin", "HOME": "/modeled/home", "GH_TOKEN": "synthetic-not-a-credential",
                  "PYTHONPATH": "/foreign/source", "NATIVECMPKIT_CAMERA_UI_ROOT": "/foreign/source"}
        with patch.dict(os.environ, parent, clear=True):
            env = reuse.scope_environment(Path("/fresh/home"), Path("/fresh/tmp"))
        self.assertEqual("/fresh/home", env["HOME"]); self.assertEqual("/fresh/tmp", env["TMPDIR"])
        self.assertEqual("/modeled/bin", env["PATH"]); self.assertEqual("1", env["PYTHONNOUSERSITE"])
        self.assertFalse({"GH_TOKEN", "PYTHONPATH", "NATIVECMPKIT_CAMERA_UI_ROOT"} & set(env))
        self.assertEqual(os.devnull, env["GIT_CONFIG_GLOBAL"])

    def test_named_actions_need_observed_resolution_for_reuse_not_mandatory_execution_pinning(self):
        source = WORKFLOW_SOURCE.replace(CHECKOUT, "actions/checkout@v6")
        with self.assertRaises(ValueError): reuse.tooling_actions(source)
        resolved = reuse.tooling_actions(source, {"actions/checkout@v6": "1" * 40})
        self.assertEqual("actions/checkout@v6", resolved[0]["reference"])
        self.assertEqual("1" * 40, resolved[0]["resolved_commit"])
        with self.assertRaises(ValueError): reuse.tooling_actions(source, {"foreign/action@v1": "2" * 40})
        with self.assertRaises(ValueError): reuse.tooling_actions(WORKFLOW_SOURCE, {CHECKOUT: "2" * 40})
        with self.assertRaises(ValueError): reuse.tooling_actions(WORKFLOW_SOURCE.replace(CHECKOUT, "./foreign/action"))

    def test_action_inventory_inline_comments_never_hide_an_unresolved_named_or_pinned_action(self):
        named = "actions/upload-artifact@v6"
        source = WORKFLOW_SOURCE.replace(UPLOAD, named + " # reviewed upload")
        with self.subTest(case="named_missing_resolution"):
            with self.assertRaises(ValueError): reuse.tooling_actions(source)
        with self.subTest(case="named_observed_resolution"):
            self.assertEqual([
                {"reference": CHECKOUT, "resolved_commit": CHECKOUT.rsplit("@", 1)[1]},
                {"reference": named, "resolved_commit": "1" * 40},
            ], reuse.tooling_actions(source, {named: "1" * 40}))
        with self.subTest(case="both_pinned_inline_comments"):
            source = WORKFLOW_SOURCE.replace(CHECKOUT, CHECKOUT + " # reviewed checkout").replace(
                UPLOAD, UPLOAD + " # reviewed upload")
            self.assertEqual([CHECKOUT, UPLOAD], [item["reference"] for item in reuse.tooling_actions(source)])

    def test_action_inventory_unsupported_yaml_refuses_whole_inventory_not_partial_checkout(self):
        prefix = ("jobs:\n  templates:\n    steps: &shared_steps\n      - &upload_step\n"
                  "        uses: &upload_ref " + UPLOAD + "\n  tooling:\n")
        literal = "    steps:\n      - uses: " + CHECKOUT + "\n"
        suffix = "  library:\n    needs: tooling\n"
        layouts = {
            "double_quoted_uses_key": literal + '      - "uses": ' + UPLOAD + "\n",
            "single_quoted_uses_key": literal + "      - 'uses': " + UPLOAD + "\n",
            "spaced_uses_key": literal + "      - uses : " + UPLOAD + "\n",
            "flow_step": literal + "      - {name: upload, uses: " + UPLOAD + "}\n",
            "step_alias": literal + "      - *upload_step\n",
            "step_merge": literal + "      - name: merged upload\n        <<: *upload_step\n",
            "anchored_step": literal + "      - &new_upload\n        uses: " + UPLOAD + "\n",
            "action_scalar_alias": literal + "      - uses: *upload_ref\n",
            "action_scalar_anchor": literal + "      - uses: &new_ref " + UPLOAD + "\n",
            "literal_action_scalar": literal + "      - uses: |\n          " + UPLOAD + "\n",
            "folded_action_scalar": literal + "      - uses: >-\n          " + UPLOAD + "\n",
            "anchored_steps": literal.replace("    steps:", "    steps: &new_steps"),
            "aliased_steps": "    steps: *shared_steps\n",
            "double_quoted_steps_key": literal.replace("    steps:", '    "steps":'),
            "flow_steps": "    steps: [{uses: " + CHECKOUT + "}, *upload_step]\n",
            "job_merge": "    <<: *upload_step\n" + literal,
            "ambiguous_run_action": literal + "      - run: echo modeled\n        uses: " + UPLOAD + "\n",
            "duplicate_step_key": literal + "      - name: upload\n        name: duplicate\n        uses: " + UPLOAD + "\n",
            "unexpected_step_indentation": literal + "       - uses: " + UPLOAD + "\n",
        }
        for label, body in layouts.items():
            with self.subTest(case=label):
                with self.assertRaises(ValueError): reuse.tooling_actions(prefix + body + suffix)

    def test_action_inventory_explicit_run_literals_are_data_not_actions(self):
        blocks = {
            "literal_heredoc": ("      - name: source data only\n        run: |\n"
                                "          cat <<'YAML'\n          uses: " + UPLOAD + "\n          YAML\n"),
            "folded": "      - run: >-\n          printf '%s'\n          uses: " + UPLOAD + "\n",
        }
        for label, body in blocks.items():
            with self.subTest(case=label):
                source = "jobs:\n  tooling:\n    steps:\n      - uses: " + CHECKOUT + "\n" + body
                self.assertEqual([CHECKOUT], [item["reference"] for item in reuse.tooling_actions(source)])

    def test_action_inventory_current_literal_workflow_compatibility_reads_source_only(self):
        # No run scalar, plan, environment, tool or action is executed here.
        source = (Path(__file__).resolve().parents[2] / reuse.WORKFLOW).read_text()
        self.assertEqual([CHECKOUT, UPLOAD], [item["reference"] for item in reuse.tooling_actions(source)])

    def test_runner_models_exact_ten_once_with_before_after_custody_not_real_discoveries(self):
        with patch.object(reuse, "capture", side_effect=[copy.deepcopy(self.signature), copy.deepcopy(self.signature)]) as capture, \
             patch.object(reuse, "producer_context", return_value=producer()), \
             patch.object(reuse, "execute_scope", side_effect=lambda _root, scope, _seconds: green(scope)) as execute:
            receipt = reuse.run_scopes(Path("/not-executed-model"), self.signature)
        self.assertIs(True, receipt["passed"]); self.assertEqual(2, capture.call_count); self.assertEqual(10, execute.call_count)
        self.assertEqual(list(reuse.SCOPES), [call.args[1] for call in execute.call_args_list])
        for directory, pattern in reuse.SCOPES:
            expected = (["python3", "-B", "scripts/ci/offline_tooling_ci_parallel734.py"]
                        if (directory, pattern) == ("scripts/ci", "test_*.py")
                        else ["python3", "-B", "-m", "unittest", "discover", "-s", directory, "-p", pattern, "-v"])
            self.assertEqual(expected, reuse.scope_command(directory, pattern))
        with self.assertRaises(ValueError): reuse.scope_command("calf-ui", "native*.py")

    def test_runner_retains_first_failure_stops_and_never_seals_drift_as_success(self):
        red = reuse.scope_summary(reuse.SCOPES[1], 1, b"Ran 1 test in 0.1s\nFAILED (errors=1)\n")
        with patch.object(reuse, "capture", side_effect=[self.signature, self.signature]), \
             patch.object(reuse, "producer_context", return_value=producer()), \
             patch.object(reuse, "execute_scope", side_effect=[green(reuse.SCOPES[0]), red]) as execute:
            receipt = reuse.run_scopes(Path("/not-executed-model"), self.signature)
        self.assertIs(False, receipt["passed"]); self.assertEqual(2, execute.call_count)
        self.assertEqual(red, receipt["scope_results"][-1])
        drift = copy.deepcopy(self.signature); drift["runtime"]["image_version"] = "20261102.1"; resign(drift)
        with patch.object(reuse, "capture", side_effect=[self.signature, drift]), \
             patch.object(reuse, "producer_context", return_value=producer()), \
             patch.object(reuse, "execute_scope", side_effect=lambda _root, scope, _seconds: green(scope)):
            receipt = reuse.run_scopes(Path("/not-executed-model"), self.signature)
        self.assertIs(False, receipt["passed"]); self.assertIs(False, receipt["inputs_held"])
        with patch.object(reuse, "capture", return_value=drift), patch.object(reuse, "execute_scope") as execute:
            with self.assertRaises(ValueError): reuse.run_scopes(Path("/not-executed-model"), self.signature)
            execute.assert_not_called()

    def test_source_capture_reads_complete_current_git_bytes_and_refuses_dirty_ancestor_images(self):
        with tempfile.TemporaryDirectory(prefix="offline-tooling-raw-git-model-") as folder:
            root = Path(folder)
            files = {reuse.WORKFLOW: WORKFLOW_SOURCE, "scripts/ci/offline_tooling_reuse.py": "current raw helper",
                     "gradle/libs.versions.toml": "exact declarations", "tests/consumer/ordinary raw fixture.txt": "full raw input"}
            for relative, content in files.items():
                path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
            def git(*args):
                return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout
            git("init", "-q"); git("add", ".")
            git("-c", "user.name=Offline fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "modeled inputs")
            original = reuse.capture_source(root)
            self.assertEqual(set(files), set(original["inputs"]))
            self.assertEqual(reuse.digest(b"full raw input"), original["inputs"]["tests/consumer/ordinary raw fixture.txt"]["sha256"])
            helper = root / "scripts/ci/offline_tooling_reuse.py"; helper.write_text("unknown ancestor-like bytes")
            with self.assertRaises(ValueError): reuse.capture_source(root)
            git("add", "."); git("-c", "user.name=Offline fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "changed inputs")
            changed = reuse.capture_source(root)
            self.assertNotEqual(original["revision"], changed["revision"])
            self.assertEqual(reuse.digest(b"unknown ancestor-like bytes"), changed["inputs"]["scripts/ci/offline_tooling_reuse.py"]["sha256"])
            self.assertNotEqual(original["inputs_sha256"], changed["inputs_sha256"])

    def test_runtime_model_hashes_actual_cargo_rustc_payloads_and_refuses_nonhosted_context(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError): reuse.capture_runtime(Path("/not-executed-model"))
        with tempfile.TemporaryDirectory(prefix="offline-tooling-runtime-model-") as folder:
            root = Path(folder)
            paths = {}
            for name in (*reuse.TOOLS, "rustup", "cargo-payload", "rustc-payload"):
                path = root / name; path.write_text("modeled binary " + name); paths[name] = path
            for name in ("cargo", "rustc"):
                paths[name].unlink(); paths[name].symlink_to(paths["rustup"])
            env = {"PATH": str(root), "HOME": str(root), "GITHUB_ACTIONS": "true",
                   "RUNNER_ENVIRONMENT": "github-hosted", "RUNNER_OS": "Linux",
                   "RUNNER_ARCH": "X64", "ImageOS": "ubuntu24", "ImageVersion": "20261101.1"}
            def observed(_root, *args):
                if len(args) == 3 and args[1] == "which": return str(paths[args[2] + "-payload"]).encode() + b"\n"
                return b"modeled actual version\n"
            with patch.dict(os.environ, env, clear=True), patch.object(reuse.platform, "system", return_value="Linux"), \
                 patch.object(reuse.platform, "machine", return_value="x86_64"), \
                 patch.object(reuse.shutil, "which", side_effect=lambda name: str(paths[name])), \
                 patch.object(reuse.sys, "executable", str(paths["python3"])), \
                 patch.object(reuse, "command", side_effect=observed) as command, \
                 patch.object(reuse, "hash_file", side_effect=lambda path, **_kwargs: reuse.digest(str(path).encode())):
                runtime = reuse.capture_runtime(root)
            for name in ("cargo", "rustc"):
                self.assertEqual(reuse.digest(str(paths[name + "-payload"]).encode()), runtime["tools"][name]["executable_sha256"])
                self.assertEqual(reuse.digest(str(paths["rustup"]).encode()), runtime["tools"][name]["launcher_sha256"])
                self.assertIn((root, str(paths["rustup"]), "which", name), [call.args for call in command.call_args_list])

    def test_masked_worktree_drift_must_match_the_declared_git_blob_not_just_clean_status(self):
        with tempfile.TemporaryDirectory(prefix="offline-tooling-masked-git-model-") as folder:
            root = Path(folder)
            for relative, content in {reuse.WORKFLOW: WORKFLOW_SOURCE,
                                      "scripts/ci/offline_tooling_reuse.py": "committed owner"}.items():
                path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
            def git(*args):
                return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout
            git("init", "-q"); git("add", ".")
            git("-c", "user.name=Offline fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "modeled inputs")
            git("update-index", "--assume-unchanged", "scripts/ci/offline_tooling_reuse.py")
            (root / "scripts/ci/offline_tooling_reuse.py").write_text("foreign bytes hidden by an index flag")
            self.assertEqual(b"", git("status", "--porcelain=v1", "--untracked-files=all"))
            with self.assertRaises(ValueError): reuse.capture_source(root)

    def test_artifact_decoding_is_bounded_and_refuses_understated_uncompressed_size(self):
        raw = reuse.canonical(self.receipt)
        member = zipfile.ZipInfo("receipt.json"); member.file_size = len(raw) - 1
        member.compress_type = zipfile.ZIP_DEFLATED; member.external_attr = (stat.S_IFREG | 0o644) << 16
        observed = []
        class BoundedReader(io.BytesIO):
            def read(self, count=-1):
                self_test.assertGreater(count, 0, "Never decode an unbounded artifact stream")
                self_test.assertLessEqual(count, reuse.MAX_JSON_BYTES + 1)
                observed.append(count)
                return super().read(count)
        class ModeledArchive:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def infolist(self): return [member]
            def open(self, item): return BoundedReader(raw)
            def read(self, item): raise AssertionError("Whole-member unbounded decoding is forbidden")
        self_test = self
        with patch.object(reuse.zipfile, "ZipFile", return_value=ModeledArchive()), self.assertRaises(ValueError):
            self.candidate()
        self.assertEqual([reuse.MAX_JSON_BYTES + 1], observed)

    def test_capture_and_scope_commands_cannot_auto_install_a_missing_rustup_toolchain(self):
        with patch.object(reuse.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"modeled version", b"")) as execute:
            reuse.command(Path("/not-executed-model"), "cargo", "--version")
        self.assertEqual("0", execute.call_args.kwargs.get("env", {}).get("RUSTUP_AUTO_INSTALL"))
        with patch.dict(os.environ, {"PATH": "/modeled/bin", "HOME": "/modeled/home"}, clear=True):
            environment = reuse.scope_environment(Path("/fresh/home"), Path("/fresh/tmp"))
        self.assertEqual("0", environment.get("RUSTUP_AUTO_INSTALL"))


    def test_hosted_job_models_reject_self_hosted_or_unknown_extra_runner_labels(self):
        for labels in (["ubuntu-24.04", "self-hosted"],
                       ["self-hosted", "ubuntu-24.04"],
                       ["ubuntu-24.04", "custom-runner"]):
            with self.subTest(labels=labels):
                job = copy.deepcopy(self.job)
                job["labels"] = labels
                with self.assertRaises(ValueError):
                    self.candidate(job=job)

    def test_runtime_requires_explicit_hosted_environment_before_any_tool_lookup(self):
        for marker in (None, "self-hosted", "unknown"):
            env = {"PATH": "/modeled/bin", "HOME": "/modeled/home", "GITHUB_ACTIONS": "true",
                   "RUNNER_OS": "Linux", "RUNNER_ARCH": "X64", "ImageOS": "ubuntu24",
                   "ImageVersion": "20261101.1"}
            if marker is not None:
                env["RUNNER_ENVIRONMENT"] = marker
            with self.subTest(marker=marker), patch.dict(os.environ, env, clear=True), \
                 patch.object(reuse.platform, "system", return_value="Linux"), \
                 patch.object(reuse.platform, "machine", return_value="x86_64"), \
                 patch.object(reuse.shutil, "which", return_value=None) as lookup, \
                 patch.object(reuse, "command") as command:
                with self.assertRaises(ValueError):
                    reuse.capture_runtime(Path("/not-executed-model"))
                lookup.assert_not_called()
                command.assert_not_called()


    def test_execute_scope_disposes_ipc_ready_owned_descendant_after_leader_exit(self):
        # Isolated Linux runner only: restore its subreaper flag and explicitly
        # reap the one IPC-proven orphan instead of leaving a fixture zombie.
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        previous = ctypes.c_int()
        self.assertEqual(0, libc.prctl(37, ctypes.byref(previous), 0, 0, 0))
        self.assertEqual(0, libc.prctl(36, 1, 0, 0, 0))
        self.lifecycle_observation = {"owned_leader_started": False, "owned_descendant_ipc_ready": False,
                                      "descendant_live_after_helper": None, "independent_cleanup_completed": False}
        leader = {}; descendant = {}; launched = []; outcomes = []; errors = []
        worker = None; connection = None; leader_ready = threading.Event()
        def observe(pid):
            try:
                raw = Path("/proc", str(pid), "stat").read_text()
            except FileNotFoundError:
                return None
            fields = raw.rpartition(")")[2].split()
            return {"pid": pid, "state": fields[0], "parent": int(fields[1]), "group": int(fields[2]),
                    "session": int(fields[3]), "start_ticks": int(fields[19])}
        def same_owner(current, expected):
            return current is not None and current["pid"] == expected["pid"] \
                and current["start_ticks"] == expected["start_ticks"] \
                and current["group"] == current["session"] == leader["pid"]
        try:
            with tempfile.TemporaryDirectory(prefix="offline-owned-group-IPC-") as folder, \
                 socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                address = str(Path(folder) / "ready.sock")
                listener.bind(address); listener.listen(1); listener.settimeout(3)
                child_code = '''import json, os, signal, socket, sys
signal.signal(signal.SIGTERM, signal.SIG_IGN)
with open("/proc/self/stat") as stream: fields = stream.read().rpartition(")")[2].split()
identity = {"pid": os.getpid(), "parent": os.getppid(), "group": os.getpgrp(),
            "session": os.getsid(0), "start_ticks": int(fields[19])}
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
    channel.settimeout(3); channel.connect(sys.argv[1])
    channel.sendall(json.dumps(identity).encode() + b"\\n")
    if channel.recv(1) != b"A": raise SystemExit(2)
os.write(int(sys.argv[2]), b"R"); os.close(int(sys.argv[2]))
while True: signal.pause()
'''
                leader_code = '''import os, select, subprocess, sys
reader, writer = os.pipe()
subprocess.Popen([sys.executable, "-B", "-c", CHILD_CODE, ADDRESS, str(writer)], pass_fds=(writer,))
os.close(writer)
if not select.select([reader], [], [], 3)[0] or os.read(reader, 1) != b"R": raise SystemExit(3)
os.close(reader)
sys.stdout.write("owned fixture ... ok\\n\\nRan 1 test in 0.001s\\n\\nOK\\n"); sys.stdout.flush()
os._exit(0)
'''.replace("CHILD_CODE", repr(child_code)).replace("ADDRESS", repr(address))
                actual_popen = reuse.subprocess.Popen
                def launch(*args, **kwargs):
                    self.assertIs(True, kwargs.get("start_new_session"))
                    process = actual_popen(*args, **kwargs); launched.append(process)
                    identity = observe(process.pid)
                    self.assertIsNotNone(identity)
                    self.assertEqual(os.getpid(), identity["parent"])
                    self.assertEqual(process.pid, identity["group"])
                    self.assertEqual(process.pid, identity["session"])
                    leader.update(identity); leader_ready.set()
                    self.lifecycle_observation["owned_leader_started"] = True
                    return process
                def run():
                    try: outcomes.append(reuse.execute_scope(Path(folder), reuse.SCOPES[0], 4))
                    except BaseException as error: errors.append(error)
                try:
                    with patch.object(reuse, "scope_command", return_value=[sys.executable, "-B", "-c", leader_code]), \
                         patch.object(reuse.subprocess, "Popen", side_effect=launch):
                        worker = threading.Thread(target=run, name="only-owned-offline-fixture")
                        worker.start(); connection, _ = listener.accept(); connection.settimeout(3)
                        raw = b""
                        while not raw.endswith(b"\n") and len(raw) < 2048:
                            block = connection.recv(2048 - len(raw)); self.assertTrue(block); raw += block
                        self.assertTrue(raw.endswith(b"\n"))
                        claimed = json.loads(raw); self.assertTrue(leader_ready.wait(1))
                        current = observe(claimed["pid"])
                        self.assertEqual(leader["pid"], claimed["parent"])
                        self.assertTrue(same_owner(current, claimed))
                        descendant.update(current)
                        self.lifecycle_observation["owned_descendant_ipc_ready"] = True
                        connection.sendall(b"A"); connection.close(); connection = None
                        worker.join(10); self.assertFalse(worker.is_alive())
                    self.assertFalse(errors, "The owned fixture helper failed before its ordinary summary")
                    self.assertEqual(1, len(outcomes)); self.assertIs(True, outcomes[0]["passed"])
                    deadline = time.monotonic() + 1
                    while True:
                        current = observe(descendant["pid"])
                        live = same_owner(current, descendant) and current["state"] not in ("Z", "X")
                        if not live or time.monotonic() >= deadline: break
                        time.sleep(0.01)
                    self.lifecycle_observation["descendant_live_after_helper"] = live
                    self.assertFalse(live, "Owned IPC-ready descendant must not outlive scope-group disposal")
                finally:
                    primary = sys.exc_info()[1]
                    try:
                        if connection is not None: connection.close(); connection = None
                        # Signals require a still-matching original epoch/session
                        # witness; never kill a guessed, reused or foreign group.
                        for expected in (descendant, leader):
                            if expected and same_owner(observe(expected["pid"]), expected):
                                os.killpg(leader["pid"], reuse.signal.SIGKILL)
                                break
                        if worker is not None:
                            worker.join(10); self.assertFalse(worker.is_alive(), "Owned worker must finish bounded cleanup")
                        for process in launched:
                            process.wait(timeout=1)
                        if descendant:
                            deadline = time.monotonic() + 2
                            while True:
                                try: reaped, _ = os.waitpid(descendant["pid"], os.WNOHANG)
                                except ChildProcessError:
                                    self.assertIsNone(observe(descendant["pid"])); break
                                if reaped == descendant["pid"]: break
                                self.assertLess(time.monotonic(), deadline, "Known orphan must be independently reaped")
                                time.sleep(0.01)
                        self.lifecycle_observation["independent_cleanup_completed"] = True
                    except BaseException as cleanup_error:
                        if primary is None: raise
                        primary.add_note("Independent owned fixture cleanup also refused: " + type(cleanup_error).__name__)
        finally:
            primary = sys.exc_info()[1]
            restored = libc.prctl(36, previous.value, 0, 0, 0) == 0
            self.lifecycle_observation["subreaper_prior_state_restored"] = restored
            if not restored:
                if primary is None: self.fail("Own runner subreaper state must be restored")
                primary.add_note("Independent own-runner subreaper restoration refused")

    def test_execute_scope_retains_owned_leader_until_final_group_signal_before_reaping(self):
        events = []
        class Exited:
            si_pid = 24680
        with patch.object(reuse.subprocess, "Popen") as launch:
            process = launch.return_value; process.pid = 24680; process.returncode = None
            def started(*args, **kwargs):
                self.assertIs(True, kwargs.get("start_new_session"))
                kwargs["stdout"].write(b"owned model ... ok\n\nRan 1 test in 0.001s\n\nOK\n")
                kwargs["stdout"].flush(); return process
            launch.side_effect = started
            def retain(kind, pid, flags):
                self.assertEqual(reuse.os.P_PID, kind); self.assertEqual(process.pid, pid)
                self.assertTrue(flags & reuse.os.WNOWAIT); events.append("retained"); return Exited()
            def reap(**kwargs):
                self.assertEqual(5, kwargs.get("timeout")); events.append("reaped"); process.returncode = 0; return 0
            process.wait.side_effect = reap
            with patch.object(reuse.os, "waitid", side_effect=retain), \
                 patch.object(reuse.os, "getpgid", return_value=process.pid), \
                 patch.object(reuse.os, "getsid", return_value=process.pid), \
                 patch.object(reuse.os, "killpg", side_effect=lambda pid, sig: events.append((pid, sig))), \
                 patch.object(reuse.os, "kill") as direct_signal:
                result = reuse.execute_scope(Path("/not-executed-model"), reuse.SCOPES[0], 1)
            process.poll.assert_not_called(); direct_signal.assert_not_called()
        self.assertIs(True, result["passed"])
        self.assertEqual([(24680, reuse.signal.SIGTERM), (24680, reuse.signal.SIGKILL)],
                         [event for event in events if isinstance(event, tuple)])
        self.assertEqual("reaped", events[-1])

    def test_execute_scope_refuses_foreign_group_without_signaling_it_and_retains_primary_error(self):
        with patch.object(reuse.subprocess, "Popen") as launch:
            process = launch.return_value; process.pid = 24681; process.returncode = None
            def reap(**_kwargs): process.returncode = -reuse.signal.SIGKILL; return process.returncode
            process.wait.side_effect = reap
            with patch.object(reuse.os, "waitid", return_value=None), \
                 patch.object(reuse.os, "getpgid", return_value=process.pid), \
                 patch.object(reuse.os, "getsid", return_value=process.pid + 1), \
                 patch.object(reuse.os, "killpg") as group_signal, \
                 patch.object(reuse.os, "kill") as direct_signal, \
                 patch.object(reuse.time, "monotonic", side_effect=(0.0, 1.0)):
                with self.assertRaisesRegex(ValueError, "Offline scope exceeded its total time/output bound") as failure:
                    reuse.execute_scope(Path("/not-executed-model"), reuse.SCOPES[0], 0)
            group_signal.assert_not_called()
            direct_signal.assert_called_once_with(process.pid, reuse.signal.SIGKILL)
            process.poll.assert_not_called(); process.wait.assert_called_once_with(timeout=5)
        self.assertTrue(any("cleanup also refused: ValueError" in note for note in failure.exception.__notes__))


    def test_execute_scope_duration_setup_error_still_disposes_only_its_pinned_owned_group(self):
        class Exited:
            si_pid = 24682
        with patch.object(reuse.subprocess, "Popen") as launch:
            process = launch.return_value; process.pid = 24682; process.returncode = None
            def reap(**_kwargs): process.returncode = 0; return 0
            process.wait.side_effect = reap
            with patch.object(reuse.os, "waitid", return_value=Exited()), \
                 patch.object(reuse.os, "getpgid", return_value=process.pid), \
                 patch.object(reuse.os, "getsid", return_value=process.pid), \
                 patch.object(reuse.os, "killpg") as group_signal, \
                 patch.object(reuse.os, "kill") as direct_signal:
                with self.assertRaises(TypeError):
                    reuse.execute_scope(Path("/not-executed-model"), reuse.SCOPES[0], "not-a-duration")
            self.assertEqual([(process.pid, reuse.signal.SIGTERM), (process.pid, reuse.signal.SIGKILL)],
                             [call.args for call in group_signal.call_args_list])
            direct_signal.assert_not_called(); process.poll.assert_not_called()
            process.wait.assert_called_once_with(timeout=5)


if __name__ == "__main__":
    unittest.main()
