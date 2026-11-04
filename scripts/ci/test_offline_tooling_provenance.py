#!/usr/bin/env python3
"""NEW8 + two origin/startup groups each: in-process models, not hosted passes.

The accepted helper's fixture factories are reused; none of its31 TestCase bodies
is run by this module. No actual network, subprocess, process population, compiler,
XML/native/consumer invocation, GitHub mutation, package, release or upload occurs.
"""
import copy
import datetime as dt
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stderr, redirect_stdout

import offline_tooling_provenance as driver
import test_offline_tooling_reuse as factories

reuse = driver.reuse
IDS = dict(zip(driver.SELECTORS, (101, 1, 202, 303)))
STR_IDS = {key: str(value) for key, value in IDS.items()}
FIXTURE_TOKEN = "fixture-only-not-an-owner-credential"
STORAGE = "fixture-artifact-storage.invalid"
STORAGE_PATH = "/actions-results/fixture-artifact.zip"
SIGNED_QUERY = "fixture-signed-query-never-export"
NOW = factories.NOW


def signature():
    value = factories.model_signature()
    for owner in ("scripts/ci/offline_tooling_provenance.py", "scripts/ci/test_offline_tooling_provenance.py",
                  "docs/testing/offline-tooling-provenance.md"):
        value["source"]["inputs"][owner] = {"mode": "100644", "sha256": reuse.digest(("modeled " + owner).encode())}
    return factories.resign(value)


class Response:
    def __init__(self, raw=b"", *, status=200, content_type="application/json; charset=utf-8", headers=None, parts=None):
        self.status = status
        self.headers = [("Content-Type", content_type)] + ([] if headers is None else list(headers))
        self.parts = [raw] if parts is None else list(parts)
        self.read_calls = 0

    def getheaders(self):
        return list(self.headers)

    def read(self, amount):
        self.read_calls += 1
        if not self.parts:
            return b""
        value = self.parts.pop(0)
        if isinstance(value, BaseException):
            raise value
        if len(value) > amount:
            self.parts.insert(0, value[amount:])
            value = value[:amount]
        return value


class SocketModel:
    def __init__(self):
        self.timeouts = []

    def settimeout(self, value):
        if not (0 < value <= driver.IO_SECONDS):
            raise AssertionError("Unknown modeled socket timeout")
        self.timeouts.append(value)


class Connection:
    def __init__(self, owner, host, port, timeout, context):
        self.owner, self.host = owner, host
        self.sock = SocketModel()
        self.context = context
        if port != 443 or not (0 < timeout <= driver.IO_SECONDS) or context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
            raise AssertionError("Verified TLS/port/bound contract is required")
        self.expected = owner.script.pop(0)
        if host != self.expected[0]:
            raise AssertionError("Unapproved modeled origin")
        self.closed = False

    def request(self, method, path, *, headers):
        self.owner.requests.append((self.host, method, path, dict(headers)))
        if method != "GET" or path != self.expected[1]:
            raise AssertionError("Not the exact modeled once-only GET")

    def getresponse(self):
        value = self.expected[2]
        if isinstance(value, BaseException):
            raise value
        return value

    def close(self):
        self.closed = True
        if self.owner.close_error is not None:
            raise self.owner.close_error


class ScriptedHTTPS:
    def __init__(self, script, *, close_error=None):
        self.script, self.close_error = list(script), close_error
        self.requests, self.connections = [], []

    def __call__(self, host, *, port, timeout, context):
        if not self.script:
            raise AssertionError("Unexpected extra modeled request or retry")
        value = Connection(self, host, port, timeout, context)
        self.connections.append(value)
        return value

    def driver_factory(self, token, store, journal, state):
        return driver.HTTPSAcquirer(token, store, journal, state, connection_factory=self, clock=lambda: 0.0)


def model_records(current, *, jobs=1, redirect=False, storage_host=STORAGE):
    receipt = factories.model_receipt(current)
    original = factories.archive_receipt(receipt)
    run, selected, artifact = factories.model_envelopes(current, original)
    others = []
    for index in range(jobs - 1):
        item = copy.deepcopy(selected)
        item.update(id=1000 + index, name="modeled-skipped-platform-" + str(index), conclusion="skipped", steps=[], labels=["windows-2025"])
        item["url"] = "https://" + driver.API_HOST + driver.API_BASE + "jobs/" + str(item["id"])
        others.append(item)
    inventory = others + [selected]
    pages = [{"total_count": jobs, "jobs": inventory[index:index + 100]} for index in range(0, jobs, 100)]
    values = [run, *pages, selected, artifact]
    operations = [("run-attempt", IDS), *[("jobs-page", {**IDS, "page": index + 1}) for index in range(len(pages))],
                  ("job", IDS), ("artifact", IDS)]
    script = [(driver.API_HOST, driver.api_path(operation, parameters), Response(reuse.canonical(value)))
              for (operation, parameters), value in zip(operations, values)]
    if redirect:
        script += [(driver.API_HOST, driver.api_path("artifact-zip", IDS), Response(status=302, headers=[
            ("Location", "https://" + storage_host + STORAGE_PATH + "?" + SIGNED_QUERY)])),
                   (storage_host, STORAGE_PATH + "?" + SIGNED_QUERY, Response(original, content_type="application/zip"))]
    else:
        script += [(driver.API_HOST, driver.api_path("artifact-zip", IDS), Response(original, content_type="application/zip"))]
    return script, values, original


class OfflineToolingProvenanceControls(unittest.TestCase):
    """Eight original, two origin and two startup groups; no real populations."""
    def setUp(self):
        self.private = tempfile.TemporaryDirectory(prefix="provenance607-model-")
        self.addCleanup(self.private.cleanup)
        self.root = Path(self.private.name)
        self.current = signature()
        self.serial = 0
        self.addCleanup(patch.stopall)
        patch.object(socket, "create_connection", side_effect=AssertionError("Actual network is prohibited")).start()
        patch.object(subprocess, "Popen", side_effect=AssertionError("Actual process execution is prohibited")).start()
        patch.object(subprocess, "run", side_effect=AssertionError("Actual process execution is prohibited")).start()
        # Nonempty explicit read credentials must not be forwarded by producer.
        patch.dict(os.environ, {driver.TOKEN_VARIABLE: ""}).start()

    def output(self):
        self.serial += 1
        return "build/ci-tooling-reuse/model-" + str(self.serial)

    def recorded(self, current=None):
        relative = self.output() + "/signature.json"
        reuse.write_owned(self.root, relative, self.current if current is None else current)
        return relative

    def read(self, output, leaf):
        return json.loads((self.root / output / leaf).read_bytes())

    def run_reuse(self, *, current=None, after=None, script=None, output=None, selectors=None, recorded=None, client_factory=None):
        current = self.current if current is None else current
        script = model_records(current)[0] if script is None else script
        https = ScriptedHTTPS(script)
        output = self.output() if output is None else output
        capture = Mock(side_effect=[current, current if after is None else after])
        factory = https.driver_factory if client_factory is None else client_factory
        with patch.object(reuse, "capture", capture), patch.object(reuse, "run_scopes", side_effect=AssertionError("Reuse cannot run scopes")), \
                patch.object(reuse, "execute_scope", side_effect=AssertionError("Reuse cannot run scopes")):
            result = driver.run("reuse", root=self.root, output_dir=output, selectors=STR_IDS if selectors is None else selectors,
                                recorded_signature=recorded, token_reader=lambda: FIXTURE_TOKEN,
                                client_factory=factory, now=NOW)
        return result, https, output, capture

    def refused_reuse(self, script, *, after=None, current=None, client_factory=None, recorded=None):
        supplied = getattr(client_factory, "__self__", None) if client_factory is not None else None
        https = supplied if type(supplied) is ScriptedHTTPS else ScriptedHTTPS(script)
        output = self.output()
        capture = Mock(side_effect=[self.current if current is None else current,
                                   self.current if after is None else after])
        with redirect_stderr(io.StringIO()) as stderr, patch.object(reuse, "capture", capture), \
                patch.object(reuse, "run_scopes", side_effect=AssertionError("Refusal cannot start fresh tooling")), \
                patch.object(reuse, "execute_scope", side_effect=AssertionError("Refusal cannot start fresh tooling")):
            with self.assertRaises(BaseException) as caught:
                driver.run("reuse", root=self.root, output_dir=output, selectors=STR_IDS,
                           recorded_signature=recorded, token_reader=lambda: FIXTURE_TOKEN,
                           client_factory=https.driver_factory if client_factory is None else client_factory, now=NOW)
        capsule = self.read(output, "refusal.json") if (self.root / output / "refusal.json").exists() else None
        self.assertFalse((self.root / output / "receipt.json").exists())
        self.assertFalse((self.root / output / "scope-result.json").exists())
        self.assertEqual(len(https.requests), len({(host, path) for host, _, path, _ in https.requests}))
        return https, capsule, caught.exception, output, stderr.getvalue(), capture

    def test_p1_modes_ids_and_fresh_owned_outputs_refuse_before_token_network_or_scopes(self):
        for mode, supplied in (("latest", STR_IDS), ("reuse", {}), ("produce", STR_IDS), ("off", STR_IDS)):
            with self.subTest(mode=mode):
                output = self.output()
                forbidden = Mock(side_effect=AssertionError("Preflight must stop"))
                with redirect_stderr(io.StringIO()), patch.object(reuse, "capture", forbidden), patch.object(reuse, "execute_scope", forbidden):
                    with self.assertRaises(ValueError):
                        driver.run(mode, root=self.root, output_dir=output, selectors=supplied,
                                   token_reader=forbidden, client_factory=forbidden)
                self.assertEqual(0, forbidden.call_count)
                self.assertFalse((self.root / output).exists())
        for value in (True, 1, 1.0, "0", "-1", "+1", "01", "1.0", "1e2", "１", "9007199254740993", "latest"):
            with self.subTest(selector=value):
                with self.assertRaises(ValueError):
                    driver.configuration("reuse", self.output(), {**STR_IDS, "producer_attempt": value})
        for output in ("/private/source", "build/ci-tooling-reuse/../escape", "build/ci-tooling-reuse/nested/output", "build/elsewhere/output"):
            with self.subTest(path_kind=output.split("/")[-1]):
                with self.assertRaises(ValueError):
                    driver.configuration("off", output)
        stale = self.output()
        (self.root / stale).mkdir(parents=True)
        (self.root / stale / "kept.json").write_bytes(b"retained model evidence")
        linked = self.output()
        (self.root / linked).symlink_to(self.root / stale, target_is_directory=True)
        for output in (stale, linked):
            forbidden = Mock(side_effect=AssertionError("Stale ownership must stop before token"))
            with redirect_stderr(io.StringIO()), patch.object(reuse, "capture", forbidden), patch.object(reuse, "execute_scope", forbidden):
                with self.assertRaises((ValueError, FileExistsError)):
                    driver.run("reuse", root=self.root, output_dir=output, selectors=STR_IDS,
                               token_reader=forbidden, client_factory=forbidden)
            self.assertEqual(0, forbidden.call_count)
        self.assertEqual(b"retained model evidence", (self.root / stale / "kept.json").read_bytes())
        with self.assertRaises(ValueError):
            driver.configuration("off", self.output(), recorded_signature="build/ci-tooling-reuse/model/signature.json")
        with self.assertRaises(ValueError):
            driver.configuration("reuse", self.output(), {**STR_IDS, "archive_url": "https://fixture.invalid"})

    def test_p2_fresh_producer_calls_once_reuse_calls_zero_and_never_reexports_receipt(self):
        for recorded in (None, self.recorded()):
            with self.subTest(recorded=recorded is not None):
                output = self.output()
                capture = Mock(return_value=self.current)
                scope = Mock(side_effect=[factories.green(item) for item in reuse.SCOPES])
                original_runner = reuse.run_scopes
                forbidden = Mock(side_effect=AssertionError("Producer cannot fetch"))
                with patch.object(reuse, "capture", capture), patch.object(reuse, "producer_context", return_value=factories.producer()), \
                        patch.object(reuse, "execute_scope", scope), patch.object(reuse, "run_scopes", wraps=original_runner) as runner:
                    result = driver.run("produce", root=self.root, output_dir=output, recorded_signature=recorded,
                                        token_reader=forbidden, client_factory=forbidden, now=NOW)
                self.assertEqual(1, runner.call_count)
                self.assertEqual(10, scope.call_count)
                self.assertEqual(3 if recorded is None else 2, capture.call_count)
                self.assertEqual(0, forbidden.call_count)
                receipt = self.read(output, "receipt.json")
                self.assertEqual(reuse.SCHEMA, receipt["schema"])
                self.assertEqual(11, len(receipt))  # Existing exact schema; no driver fields.
                self.assertTrue(receipt["fresh_scope_execution"])
                self.assertEqual(10, result["new_scope_executions"])
                self.assertEqual(reuse.ARTIFACT_PREFIX + self.current["signature_sha256"], result["artifact_name"])
        result, https, output, capture = self.run_reuse(recorded=self.recorded())
        self.assertEqual(2, capture.call_count)
        self.assertEqual(5, len(https.requests))
        self.assertEqual(0, result["new_scope_executions"])
        self.assertTrue(result["authenticated_acquisition_completed"])
        self.assertFalse(result["checker_decision"]["authenticated_transport_by_helper"])
        self.assertFalse(result["reusable_producer_certificate"])
        self.assertFalse((self.root / output / "receipt.json").exists())
        self.assertFalse((self.root / output / "producer-result.json").exists())
        output = self.output()
        red = reuse.scope_summary(reuse.SCOPES[0], 1, b"Ran 1 test in 0.1s\n\nFAILED (failures=1)\n")
        with patch.object(reuse, "capture", return_value=self.current), patch.object(reuse, "producer_context", return_value=factories.producer()), \
                patch.object(reuse, "execute_scope", return_value=red) as scope:
            result = driver.run("produce", root=self.root, output_dir=output, now=NOW)
        self.assertEqual(1, scope.call_count)
        self.assertEqual("failed", result["outcome"])
        self.assertFalse((self.root / output / "receipt.json").exists())
        self.assertEqual(red, self.read(output, "scope-result.json")["scope_results"][0])

    def test_p3_all_attempt_pages_and_sole_direct_job_are_exact_once_or_refused(self):
        script, _, _ = model_records(self.current, jobs=101)
        result, https, output, _ = self.run_reuse(script=script)
        self.assertEqual("passed", result["outcome"])
        expected_paths = [item[1] for item in script]
        self.assertEqual(expected_paths, [item[2] for item in https.requests])
        self.assertEqual(6, len(https.requests))
        summary = self.read(output, "acquisition-summary.json")
        self.assertEqual(6, summary["api_requests_started"])
        self.assertEqual(0, summary["storage_hops_started"])
        cases = ("run-id", "attempt", "fork", "run-pending", "boolean-count", "total-drift", "short-page", "duplicate-id",
                 "mixed-attempt", "pending-other-job", "no-tooling", "two-tooling", "red-tooling", "label-drift",
                 "direct-step-drift", "missing-required-step")
        for case in cases:
            with self.subTest(case=case):
                script, values, original = model_records(self.current, jobs=101)
                run, page1, page2, selected, artifact = copy.deepcopy(values)
                if case == "run-id": run["id"] = 999
                elif case == "attempt": run["run_attempt"] = 2
                elif case == "fork": run["head_repository"]["full_name"] = "fixture-fork/nativeCmpkit"
                elif case == "run-pending": run["status"] = "in_progress"
                elif case == "boolean-count": page1["total_count"] = True
                elif case == "total-drift": page2["total_count"] = 102
                elif case == "short-page": page1["jobs"].pop()
                elif case == "duplicate-id": page1["jobs"][1] = copy.deepcopy(page1["jobs"][0])
                elif case == "mixed-attempt": page1["jobs"][0]["run_attempt"] = 2
                elif case == "pending-other-job": page1["jobs"][0]["status"] = "queued"
                elif case == "no-tooling": page2["jobs"][0]["name"] = "not-tooling"
                elif case == "two-tooling": page1["jobs"][0] = copy.deepcopy(selected)
                elif case == "red-tooling": page2["jobs"][0]["conclusion"] = "failure"
                elif case == "label-drift": page2["jobs"][0]["labels"] = ["ubuntu-latest"]
                elif case == "direct-step-drift": selected["steps"][1]["number"] = 50
                elif case == "missing-required-step":
                    selected["steps"].pop(1)
                    page2["jobs"][0] = copy.deepcopy(selected)
                changed = (run, page1, page2, selected, artifact)
                for index, value in enumerate(changed):
                    script[index] = (script[index][0], script[index][1], Response(reuse.canonical(value)))
                https, capsule, _, _, _, _ = self.refused_reuse(script)
                self.assertLess(len(https.requests), 6)
                self.assertFalse(capsule["authenticated_reuse_accepted"])
                self.assertEqual("unavailable", capsule["offline_scope_results"]["availability"])

    def test_p4_verified_tls_fixed_origins_no_storage_token_redirect_retry_proxy_or_unbounded_io(self):
        with patch.dict(os.environ, {"HTTPS_PROXY": "https://fixture-proxy.invalid", "HTTP_PROXY": "http://fixture-proxy.invalid"}), \
                patch.object(driver, "REVIEWED_STORAGE_HOSTS", (STORAGE,)):
            script, _, _ = model_records(self.current, redirect=True)
            result, https, output, _ = self.run_reuse(script=script)
        self.assertEqual("passed", result["outcome"])
        self.assertEqual(6, len(https.requests))
        for host, method, path, headers in https.requests:
            self.assertEqual("GET", method)
            if host == driver.API_HOST:
                self.assertEqual("Bearer " + FIXTURE_TOKEN, headers["Authorization"])
            else:
                self.assertEqual(STORAGE, host)
                self.assertNotIn("Authorization", headers)
                self.assertNotIn("X-GitHub-Api-Version", headers)
        exported = b"\n".join(path.read_bytes() for path in (self.root / output).iterdir() if path.suffix == ".json")
        for private in (FIXTURE_TOKEN, SIGNED_QUERY, "Location", "Authorization"):
            self.assertNotIn(private.encode(), exported)
        self.assertEqual(1, self.read(output, "acquisition-summary.json")["storage_hops_started"])
        for location in ("https://unreviewed.invalid/original.zip?private-query", "http://" + STORAGE + "/original.zip?q",
                         "https://owner@" + STORAGE + "/original.zip?q", "https://" + STORAGE + ":443/original.zip?q",
                         "https://" + STORAGE + "/../original.zip?q", "https://" + STORAGE + "/original.zip?q#fragment"):
            with self.subTest(origin_kind=location.split(":", 1)[0]), patch.object(driver, "REVIEWED_STORAGE_HOSTS", (STORAGE,)):
                script, _, _ = model_records(self.current)
                script[-1] = (driver.API_HOST, driver.api_path("artifact-zip", IDS), Response(status=302, headers=[("Location", location)]))
                https, capsule, _, _, _, _ = self.refused_reuse(script)
                self.assertEqual(5, len(https.requests))
                self.assertFalse(any(item[0] != driver.API_HOST for item in https.requests))
        with self.assertRaises(ValueError):
            driver.HTTPSAcquirer.storage_target("https://" + STORAGE + STORAGE_PATH + "?q")  # Fixture is NOT built-in approved.
        for status in (401, 403, 404, 429, 500):
            with self.subTest(status=status):
                script, _, _ = model_records(self.current)
                response = Response(b"fixture status body must not be exported", status=status)
                script[0] = (script[0][0], script[0][1], response)
                https, capsule, _, _, _, _ = self.refused_reuse(script)
                self.assertEqual(1, len(https.requests))
                self.assertEqual(0, response.read_calls)
        script, _, _ = model_records(self.current)
        response = Response(headers=[("Content-Length", str(reuse.MAX_JSON_BYTES + 1))])
        script[0] = (script[0][0], script[0][1], response)
        https, _, _, _, _, _ = self.refused_reuse(script)
        self.assertEqual(0, response.read_calls)
        self.assertEqual(1, len(https.requests))
        output = self.output()
        store = driver.OwnedDirectory(self.root, output)
        state = driver.State("reuse")
        state.store, state.ids = store, IDS
        journal = driver.Journal(store, state)
        https = ScriptedHTTPS([])
        client = driver.HTTPSAcquirer(FIXTURE_TOKEN, store, journal, state, connection_factory=https, clock=lambda: 0.0)
        try:
            with self.assertRaises(ValueError):
                client.request("run-attempt", driver.API_BASE + "other-route", IDS, "run.json")
            with patch.object(driver, "REVIEWED_STORAGE_HOSTS", (STORAGE,)):
                with self.assertRaises(ValueError):
                    client.request("storage-zip", "/caller.zip?private", IDS, "archive.zip", storage_host=STORAGE)
            self.assertEqual([], https.requests)
            self.assertEqual([], journal.requests)
        finally:
            client.close()
            store.close()
        # Duplicate logical requests stop before a second connection; explicit
        # deadline/aggregate-byte bounds are exercised without clocks or sockets.
        for case in ("duplicate", "mixed-request-selectors", "deadline", "aggregate-bytes", "storage-redirect"):
            with self.subTest(boundary=case), patch.object(driver, "REVIEWED_STORAGE_HOSTS", (STORAGE,)):
                output = self.output()
                store = driver.OwnedDirectory(self.root, output)
                state = driver.State("reuse")
                state.store, state.ids = store, IDS
                journal = driver.Journal(store, state)
                if case == "storage-redirect":
                    script = [(driver.API_HOST, driver.api_path("artifact-zip", IDS), Response(status=302, headers=[
                        ("Location", "https://" + STORAGE + STORAGE_PATH + "?q")])),
                              (STORAGE, STORAGE_PATH + "?q", Response(status=302, headers=[
                        ("Location", "https://unreviewed.invalid/next.zip?q")]))]
                else:
                    script = [(driver.API_HOST, driver.api_path("run-attempt", IDS), Response(b"12345"))]
                    if case == "mixed-request-selectors":
                        script += [(driver.API_HOST, driver.api_path("run-attempt", IDS), Response(b"12345"))]
                https = ScriptedHTTPS(script)
                times = iter((0.0, 200.0))
                client = driver.HTTPSAcquirer(FIXTURE_TOKEN, store, journal, state, connection_factory=https,
                                               clock=times.__next__ if case == "deadline" else lambda: 0.0)
                try:
                    if case == "storage-redirect":
                        target = client.request("artifact-zip", driver.api_path("artifact-zip", IDS), IDS, "archive.zip")
                        with self.assertRaises(ValueError):
                            client.request("storage-zip", target[1], IDS, "archive.zip", storage_host=target[0])
                        self.assertEqual(2, len(https.requests))
                    elif case == "duplicate":
                        client.request("run-attempt", driver.api_path("run-attempt", IDS), IDS, "run.json")
                        with self.assertRaises(ValueError):
                            client.request("run-attempt", driver.api_path("run-attempt", IDS), IDS, "run.json")
                        self.assertEqual(1, len(https.requests))
                    elif case == "mixed-request-selectors":
                        client.request("run-attempt", driver.api_path("run-attempt", IDS), IDS, "run.json")
                        different = {**IDS, "producer_job_id": 999}
                        with self.assertRaises(ValueError):
                            client.request("run-attempt", driver.api_path("run-attempt", different), different, "run-second.json")
                        self.assertEqual(1, len(https.requests))
                    elif case == "deadline":
                        with self.assertRaises(ValueError):
                            client.request("run-attempt", driver.api_path("run-attempt", IDS), IDS, "run.json")
                        self.assertEqual(0, len(https.requests))
                    else:
                        with patch.object(driver, "MAX_ACQUIRED_BYTES", 4):
                            with self.assertRaises(ValueError):
                                client.request("run-attempt", driver.api_path("run-attempt", IDS), IDS, "run.json")
                        self.assertFalse(journal.requests[-1]["response"]["body"]["complete"])
                        self.assertEqual(1, len(https.requests))
                finally:
                    client.close()
                    self.assertIsNone(client.token)
                    store.close()
        with patch.dict(os.environ, {driver.TOKEN_VARIABLE: FIXTURE_TOKEN}):
            forbidden = Mock(side_effect=AssertionError("Producer cannot forward an explicit read token"))
            with patch.object(reuse, "capture", forbidden), patch.object(reuse, "execute_scope", forbidden):
                with self.assertRaises(ValueError):
                    driver.run("produce", root=self.root, output_dir=self.output())
            self.assertEqual(0, forbidden.call_count)
        output = self.output()
        with patch.dict(os.environ, {driver.TOKEN_VARIABLE: FIXTURE_TOKEN}):
            observed = []
            script, _, _ = model_records(self.current)
            https = ScriptedHTTPS(script)
            def capture(_root, _resolutions):
                observed.append(driver.TOKEN_VARIABLE in os.environ)
                return self.current
            with patch.object(reuse, "capture", side_effect=capture):
                driver.run("reuse", root=self.root, output_dir=output, selectors=STR_IDS, client_factory=https.driver_factory, now=NOW)
            self.assertEqual([False, False], observed)

    def test_o1_header_observed_host_and_literal_route_only_no_alias_pattern_or_environment_override(self):
        host = "productionresultssa0.blob.core.windows.net"
        path = "/actions-results/fixture-artifact.zip"
        self.assertEqual((host,), driver.REVIEWED_STORAGE_HOSTS)
        self.assertEqual("/actions-results/", driver.REVIEWED_STORAGE_ROUTE)
        self.assertEqual((host, path + "?" + SIGNED_QUERY),
                         driver.HTTPSAcquirer.storage_target("https://" + host + path + "?" + SIGNED_QUERY))
        origins = (
            "productionresultssa1.blob.core.windows.net", "productionresultssa0.blob.core.windows.net.attacker.invalid",
            "attacker.productionresultssa0.blob.core.windows.net", "productionresultssa0.blob.core.windows.net.",
            "PRODUCTIONRESULTSSA0.blob.core.windows.net", "productionresultssa0%2eblob.core.windows.net", STORAGE,
        )
        routes = (
            "/", "/actions-results", "/actions-results/", "/actions-results-other/fixture.zip",
            "/Actions-results/fixture.zip", "//actions-results/fixture.zip", "/actions%2Dresults/fixture.zip",
            "/actions-results//fixture.zip", "/actions-results/a/", "/actions-results/./fixture.zip",
            "/actions-results/a/../fixture.zip", "/actions-results/%2e%2e/fixture.zip",
            "/actions-results/a%2ffixture.zip", "/actions-results/a%252ffixture.zip",
            "/actions-results/a%5cfixture.zip", "/actions-results/a\\fixture.zip",
            "/actions-results/a%00fixture.zip", "/actions-results/a%3ffixture.zip", "/actions-results/a%ZZ.zip",
        )
        with patch.dict(os.environ, {"NATIVECMPKIT_STORAGE_HOST": STORAGE, "NATIVECMPKIT_REVIEWED_STORAGE_HOSTS": STORAGE}):
            for origin in origins:
                with self.subTest(unreviewed_origin=origin), self.assertRaises(ValueError):
                    driver.HTTPSAcquirer.storage_target("https://" + origin + path + "?" + SIGNED_QUERY)
        for route in routes:
            with self.subTest(nonliteral_route=route), self.assertRaises(ValueError):
                driver.HTTPSAcquirer.storage_target("https://" + host + route + "?" + SIGNED_QUERY)
        for location in (
            "http://" + host + path + "?q", "https://owner@" + host + path + "?q",
            "https://" + host + ":443" + path + "?q", "https://" + host + path + "?q#fragment",
            "https://" + host + path, "https://" + host + path + "?", "https://" + host + path + "?q\n",
        ):
            with self.subTest(noncanonical_location=location), self.assertRaises(ValueError):
                driver.HTTPSAcquirer.storage_target(location)

    def test_o2_observed_origin_remains_api_minted_exact_once_token_free_and_unknown_origin_refuses(self):
        host = "productionresultssa0.blob.core.windows.net"
        script, _, original = model_records(self.current, redirect=True, storage_host=host)
        result, https, output, capture = self.run_reuse(script=script)
        self.assertEqual("passed", result["outcome"])
        self.assertEqual(0, result["new_scope_executions"])
        self.assertEqual(2, capture.call_count)
        self.assertEqual(original, (self.root / output / "archive.zip").read_bytes())
        self.assertEqual(5, self.read(output, "acquisition-summary.json")["api_requests_started"])
        self.assertEqual(1, self.read(output, "acquisition-summary.json")["storage_hops_started"])
        self.assertEqual([driver.API_HOST] * 5 + [host], [request[0] for request in https.requests])
        headers = https.requests[-1][3]
        self.assertNotIn("Authorization", headers)
        self.assertNotIn("X-GitHub-Api-Version", headers)
        self.assertFalse((self.root / output / "receipt.json").exists())
        exported = b"\n".join(path.read_bytes() for path in (self.root / output).iterdir() if path.suffix == ".json")
        for private in (FIXTURE_TOKEN, SIGNED_QUERY, "Location", "Authorization"):
            self.assertNotIn(private.encode(), exported)
        # The actual built-in origin still requires this client's API-issued
        # capability, not merely a syntactically approved caller URL.
        store = driver.OwnedDirectory(self.root, self.output())
        state = driver.State("reuse")
        state.store, state.ids = store, IDS
        journal = driver.Journal(store, state)
        path = STORAGE_PATH + "?" + SIGNED_QUERY
        responses = [(driver.API_HOST, driver.api_path("artifact-zip", IDS), Response(status=302, headers=[
            ("Location", "https://" + host + path)])),
                     (host, path, Response(original, content_type="application/zip"))]
        connection = ScriptedHTTPS(responses)
        client = driver.HTTPSAcquirer(FIXTURE_TOKEN, store, journal, state, connection_factory=connection, clock=lambda: 0.0)
        try:
            with self.assertRaises(ValueError):
                client.request("storage-zip", path, IDS, "archive.zip", storage_host=host)
            self.assertEqual([], connection.requests)
            self.assertEqual([], journal.requests)
            target = client.request("artifact-zip", driver.api_path("artifact-zip", IDS), IDS, "archive.zip")
            self.assertEqual((host, path), target)
            with self.assertRaises(ValueError):
                client.request("storage-zip", path + "&caller-change=1", IDS, "archive.zip", storage_host=host)
            self.assertEqual(1, len(connection.requests))
            self.assertEqual(original, client.request("storage-zip", path, IDS, "archive.zip", storage_host=host))
            with self.assertRaises(ValueError):
                client.request("storage-zip", path, IDS, "archive-again.zip", storage_host=host)
            self.assertEqual(2, len(connection.requests))
            self.assertEqual(2, len(journal.requests))
        finally:
            client.close()
            self.assertIsNone(client.token)
            store.close()
        script, _, _ = model_records(self.current, redirect=True, storage_host="productionresultssa1.blob.core.windows.net")
        https, capsule, _, output, _, capture = self.refused_reuse(script)
        self.assertEqual(5, len(https.requests))
        self.assertEqual([driver.API_HOST] * 5, [request[0] for request in https.requests])
        self.assertEqual(1, capture.call_count)
        self.assertEqual("acquire-artifact-zip", capsule["stage"])
        self.assertFalse(capsule["authenticated_reuse_accepted"])
        self.assertFalse((self.root / output / "archive.zip").exists())
        self.assertFalse((self.root / output / "reuse-decision.json").exists())

    def test_p5_original_zip_and_metadata_custody_partial_witnesses_and_non_tooling_artifacts(self):
        script, _, original = model_records(self.current)
        _, _, output, _ = self.run_reuse(script=script)
        self.assertEqual(original, (self.root / output / "archive.zip").read_bytes())
        summary = self.read(output, "acquisition-summary.json")
        body = summary["requests"][-1]["response"]["body"]
        self.assertTrue(body["complete"])
        self.assertEqual(len(original), body["bytes"])
        self.assertEqual(hashlib.sha256(original).hexdigest(), body["sha256"])
        prefix = b'{"id":'
        failure = TimeoutError("fixture timeout private message")
        script, _, _ = model_records(self.current)
        script[0] = (script[0][0], script[0][1], Response(parts=[prefix, failure]))
        https, capsule, caught, output, _, _ = self.refused_reuse(script)
        self.assertIs(failure, caught)
        self.assertEqual(prefix, (self.root / output / "run.json").read_bytes())
        body = self.read(output, "request-001-result.json")["body"]
        self.assertFalse(body["complete"])
        self.assertEqual(len(prefix), body["bytes"])
        self.assertEqual(reuse.digest(prefix), body["sha256"])
        self.assertEqual("unavailable", capsule["offline_scope_results"]["availability"])
        for case in ("native-name", "package-name", "foreign-run", "foreign-repository", "foreign-url", "missing-digest",
                     "expired", "old-attempt-window", "size-drift", "zip-extra-member", "legacy-receipt"):
            with self.subTest(case=case):
                script, values, original = model_records(self.current)
                artifact = copy.deepcopy(values[-1])
                if case == "native-name": artifact["name"] = "native-results"
                elif case == "package-name": artifact["name"] = "preview-packages"
                elif case == "foreign-run": artifact["workflow_run"]["id"] = 999
                elif case == "foreign-repository": artifact["workflow_run"]["repository_id"] = 999
                elif case == "foreign-url": artifact["archive_download_url"] = "https://fixture.invalid/original.zip"
                elif case == "missing-digest": artifact["digest"] = None
                elif case == "expired": artifact["expired"] = True
                elif case == "old-attempt-window": artifact["created_at"] = "2026-11-04T00:00:09Z"
                elif case == "size-drift": artifact["size_in_bytes"] += 1
                elif case == "zip-extra-member": original = factories.archive_receipt(factories.model_receipt(self.current), extra=True)
                elif case == "legacy-receipt": original = factories.archive_receipt({"passed": True})
                if case in ("zip-extra-member", "legacy-receipt"):
                    artifact["size_in_bytes"], artifact["digest"] = len(original), "sha256:" + reuse.digest(original)
                script[-2] = (script[-2][0], script[-2][1], Response(reuse.canonical(artifact)))
                script[-1] = (script[-1][0], script[-1][1], Response(original, content_type="application/zip"))
                https, capsule, _, output, _, _ = self.refused_reuse(script)
                self.assertFalse((self.root / output / "reuse-decision.json").exists())
                self.assertLessEqual(len(https.requests), 5)
        script, _, _ = model_records(self.current)
        output = self.output()
        original_check = reuse.check
        def corrupt_after_check(*args, **kwargs):
            result = original_check(*args, **kwargs)
            (self.root / output / "archive.zip").write_bytes(b"displaced after the one modeled check")
            return result
        with patch.object(reuse, "check", side_effect=corrupt_after_check):
            with self.assertRaises(ValueError):
                self.run_reuse(script=script, output=output)
        self.assertFalse((self.root / output / "reuse-decision.json").exists())

    def test_p6_sanitized_original_raised_frames_unavailable_counts_and_secondary_primary_preservation(self):
        private = "fixture-message-query-token-locals-never-export"
        try:
            reuse.require(False, private)
        except ValueError as error:
            error.add_note(private)
            evidence = driver.sanitized_error(error)
        serialized = reuse.canonical(evidence)
        self.assertNotIn(private.encode(), serialized)
        self.assertEqual("ValueError", evidence["category"])
        self.assertTrue(evidence["secondary_note_presence_observed"])
        self.assertEqual("unavailable", evidence["secondary_note_details"])
        frames = evidence["public_source_frames"]
        self.assertEqual(1, len(frames))
        self.assertEqual("scripts/ci/offline_tooling_reuse.py", frames[0]["owner"])
        self.assertEqual("require", frames[0]["function"])
        self.assertEqual(reuse.hash_file(Path(reuse.__file__)), frames[0]["source_sha256"])
        self.assertTrue(type(frames[0]["line"]) is int and type(frames[0]["instruction_offset"]) is int)
        failure = TimeoutError(private)
        secondary = OSError(private)
        script, _, _ = model_records(self.current)
        script[0] = (script[0][0], script[0][1], failure)
        https = ScriptedHTTPS(script, close_error=secondary)
        _, capsule, caught, output, _, _ = self.refused_reuse(script, client_factory=https.driver_factory)
        self.assertIs(failure, caught)
        self.assertEqual("unavailable", capsule["offline_scope_results"]["availability"])
        self.assertFalse(capsule["reusable_producer_certificate"])
        self.assertEqual("https-connection-close", capsule["secondary_refusals"][0]["operation"])
        serialized = reuse.canonical(capsule)
        for forbidden in (private, FIXTURE_TOKEN, "Authorization", "f_locals", "__cause__", "__context__", "/private/"):
            self.assertNotIn(forbidden.encode(), serialized)
        self.assertNotIn("tests", capsule["offline_scope_results"])
        self.assertNotIn("output_sha256", capsule["offline_scope_results"])
        output = self.output()
        failure = RuntimeError(private)
        with redirect_stderr(io.StringIO()) as stderr, patch.object(reuse, "execute_scope", side_effect=failure):
            with self.assertRaises(RuntimeError) as caught:
                driver.run("off", root=self.root, output_dir=output)
        self.assertIs(failure, caught.exception)
        capsule = self.read(output, "refusal.json")
        self.assertEqual("unavailable", capsule["offline_scope_results"]["availability"])
        self.assertTrue(any(frame["owner"] == "scripts/ci/offline_tooling_provenance.py" for frame in capsule["primary_refusal"]["public_source_frames"]))
        self.assertNotIn(private, (self.root / output / "refusal.json").read_text())
        output = self.output()
        (self.root / output).mkdir()
        kept = self.root / output / "refusal.json"
        kept.write_bytes(b"original must never be overwritten")
        with redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(ValueError):
                driver.run("off", root=self.root, output_dir=output)
        self.assertEqual(b"original must never be overwritten", kept.read_bytes())
        self.assertIn('"availability":"unavailable"', stderr.getvalue())
        self.assertNotIn(private, stderr.getvalue())

    def test_p7_live_before_after_source_runtime_action_recipe_and_requested_drift_have_no_fallback(self):
        for case in ("commit", "input-byte", "mode", "runtime", "action-resolution", "recipe", "dependency"):
            with self.subTest(case=case):
                after = copy.deepcopy(self.current)
                if case == "commit": after["source"]["revision"] = "f" * 40
                elif case == "input-byte": after["source"]["inputs"]["docs/testing/offline-tooling-provenance.md"]["sha256"] = "f" * 64
                elif case == "mode": after["source"]["inputs"]["scripts/ci/offline_tooling_provenance.py"]["mode"] = "100755"
                elif case == "runtime": after["runtime"]["image_version"] = "20261104.99"
                elif case == "action-resolution": after["workflow"]["tooling_actions"][0]["resolved_commit"] = "f" * 40
                elif case == "recipe": after["recipe_sha256"] = "f" * 64
                elif case == "dependency": after["dependency_inputs_sha256"] = "f" * 64
                if case != "dependency": factories.resign(after)
                script, _, _ = model_records(self.current)
                https, capsule, _, output, _, capture = self.refused_reuse(script, after=after)
                self.assertEqual(5, len(https.requests))
                self.assertEqual(2, capture.call_count)
                self.assertEqual("fresh-current-after-check", capsule["stage"])
                self.assertFalse((self.root / output / "reuse-decision.json").exists())
        expected = copy.deepcopy(self.current)
        expected["source"]["revision"] = "f" * 40
        factories.resign(expected)
        recorded = self.recorded(expected)
        factory = Mock(side_effect=AssertionError("Drift must refuse before constructing the client"))
        script, _, _ = model_records(self.current)
        https, capsule, _, _, _, capture = self.refused_reuse(script, recorded=recorded, client_factory=factory)
        self.assertEqual([], https.requests)
        self.assertEqual(0, factory.call_count)
        self.assertEqual(1, capture.call_count)
        self.assertFalse(capsule["authenticated_reuse_accepted"])

    def test_p8_off_is_unpinned_policy_compatible_and_never_reuses_independent_gates(self):
        output = self.output()
        forbidden = Mock(side_effect=AssertionError("Off must not request signature eligibility/authentication"))
        with patch.object(reuse, "capture", forbidden), patch.object(reuse, "run_scopes", forbidden), \
                patch.object(reuse, "tooling_actions", forbidden), patch.object(reuse, "execute_scope", side_effect=[factories.green(scope) for scope in reuse.SCOPES]) as scope:
            result = driver.run("off", root=self.root, output_dir=output, token_reader=forbidden, client_factory=forbidden)
        self.assertEqual(0, forbidden.call_count)
        self.assertEqual(10, scope.call_count)
        self.assertEqual(10, result["new_scope_executions"])
        self.assertFalse(result["reusable_producer_certificate"])
        self.assertFalse(result["authentication_requested"])
        self.assertFalse((self.root / output / "receipt.json").exists())
        self.assertFalse((self.root / output / "signature.json").exists())
        for key in ("fresh_index_and_profile_checks_reused", "library_or_native_results_reused", "consumer_results_reused",
                    "native_failure_waived", "release_readiness_certified"):
            self.assertFalse(result[key])
        self.assertEqual(10, len(reuse.SCOPES))
        for fresh in ("verify_migration.py", "validate_audit.py", "source_inventory.py", "validate_resolutions.py", "generate_icon_catalogues.py", "workflow_matrix.py"):
            self.assertFalse(any(fresh in reuse.scope_command(*scope) for scope in reuse.SCOPES))
        with self.assertRaises(ValueError):
            reuse.tooling_actions("jobs:\n  tooling:\n    steps:\n      - uses: actions/checkout@v4\n")
        self.assertEqual("off", driver.configuration("off", self.output())["mode"])
        documentation = Path(driver.__file__).resolve().parents[2] / "docs/testing/offline-tooling-provenance.md"
        text = documentation.read_text()
        for required in ("no mandatory SHA pinning", "five fresh index checks", "requested profile preflight", "actions: read", "contents: read", "EMPTY", "No publication"):
            self.assertIn(required, text)
        self.assertNotIn("urllib.request", Path(driver.__file__).read_text())
        self.assertNotIn("_create_unverified_context", Path(driver.__file__).read_text())

    def startup_fixture(self, entry, refusal_owner):
        """Load actual public source in process; refuse real shared temporary files.

        The observer and hash guard are not mocked. No helper CLI, discovery,
        socket or subprocess is executed. A profile trap also catches any main,
        credential, capture or acquisition call before the denial is asserted.
        """
        self.serial += 1
        package = self.root / ("startup-private-fixture-" + str(self.serial))
        sources = package / "scripts/ci"
        sources.mkdir(parents=True)
        paths = {}
        for owner in ("offline_tooling_provenance.py", "offline_tooling_reuse.py"):
            path = sources / owner
            path.write_bytes(Path(driver.__file__).with_name(owner).read_bytes())
            paths[owner] = path
        helper = types.ModuleType("offline_tooling_reuse")
        helper.__file__ = str(paths["offline_tooling_reuse.py"])
        exec(compile(paths["offline_tooling_reuse.py"].read_bytes(), helper.__file__, "exec"), helper.__dict__)
        if refusal_owner in paths:
            os.link(paths[refusal_owner], package / "shared-source-inode")
        elif refusal_owner == "helper-owner-path":
            other = package / "unrelated-helper-owner.py"
            other.write_bytes(paths["offline_tooling_reuse.py"].read_bytes())
            helper.__file__ = str(other)
        name = "__main__" if entry == "cli" else "offline_tooling_provenance_startup_fixture"
        module = types.ModuleType(name)
        module.__file__ = str(paths["offline_tooling_provenance.py"])
        code = compile(paths["offline_tooling_provenance.py"].read_bytes(), module.__file__, "exec")
        calls, hashes = [], []
        watched = {str(path) for path in paths.values()}
        forbidden = {"main", "run", "take_token", "acquire", "capture", "capture_source", "capture_runtime",
                     "run_scopes", "execute_scope", "producer_context", "command", "request"}
        def observe(frame, event, _argument):
            if event == "call" and frame.f_code.co_filename in watched:
                function = frame.f_code.co_name
                if function == "hash_file":
                    hashes.append(Path(frame.f_locals["path"]).name)
                if function in forbidden:
                    calls.append(function)
                    raise AssertionError("Startup denial must precede execution work")
        previous = sys.getprofile()
        caught = None
        with patch.dict(sys.modules, {name: module, "offline_tooling_reuse": helper}), \
                patch.dict(os.environ, {driver.TOKEN_VARIABLE: FIXTURE_TOKEN}), \
                redirect_stderr(io.StringIO()) as stderr, redirect_stdout(io.StringIO()) as stdout:
            try:
                sys.setprofile(observe)
                exec(code, module.__dict__)
            except BaseException as error:
                caught = error
            finally:
                sys.setprofile(previous)
            self.assertEqual(FIXTURE_TOKEN, os.environ[driver.TOKEN_VARIABLE])
        self.assertEqual([], calls)
        self.assertEqual("", stdout.getvalue())
        return module, caught, stderr.getvalue(), hashes, package

    def assert_startup_refusal(self, entry, observation):
        module, error, stderr, hashes, package = observation
        self.assertIs(type(error), SystemExit)
        self.assertIs(type(error.code), int)
        self.assertNotEqual(0, error.code)
        if entry == "import":
            self.assertTrue(error.__suppress_context__)
        self.assertEqual({}, module.PUBLIC_SOURCES)
        self.assertEqual(1, len(stderr.splitlines()))
        capsule = json.loads(stderr)
        self.assertEqual(driver.SCHEMA, capsule["schema"])
        self.assertEqual("refused", capsule["outcome"])
        self.assertEqual("source-observation", capsule["boundary"])
        refusal = capsule["primary_refusal"]
        self.assertEqual("ValueError", refusal["category"])
        self.assertEqual([], refusal["public_source_frames"])
        self.assertFalse(refusal["exception_messages_chains_locals_exported"])
        for private in (str(package), FIXTURE_TOKEN, "Traceback (most recent call last)",
                        "Expected a bounded ordinary unshared input", "Offline tooling provenance guard refused"):
            self.assertNotIn(private, stderr)
        self.assertIn("offline_tooling_provenance.py", hashes)

    def test_s1_cli_real_source_hash_refusal_precedes_main_token_network_and_sanitizes_startup(self):
        for owner in ("offline_tooling_provenance.py", "offline_tooling_reuse.py"):
            with self.subTest(refusal_owner=owner):
                observation = self.startup_fixture("cli", owner)
                self.assert_startup_refusal("cli", observation)
                expected = ["offline_tooling_provenance.py"]
                if owner == "offline_tooling_reuse.py":
                    expected.append(owner)
                self.assertEqual(expected, observation[3])

    def test_s2_import_source_ownership_refuses_without_partial_registration_or_private_traceback(self):
        module, error, stderr, hashes, package = self.startup_fixture("import", None)
        self.assertIsNone(error)
        self.assertEqual("", stderr)
        self.assertEqual(["offline_tooling_provenance.py", "offline_tooling_reuse.py"], hashes)
        self.assertEqual({"scripts/ci/offline_tooling_provenance.py", "scripts/ci/offline_tooling_reuse.py"},
                         set(module.PUBLIC_SOURCES))
        for owner, witness in module.PUBLIC_SOURCES.items():
            self.assertEqual(package / owner, witness["path"])
            self.assertEqual(reuse.digest((package / owner).read_bytes()), witness["sha256"])
            self.assertTrue(witness["codes"])
        for owner in ("offline_tooling_provenance.py", "offline_tooling_reuse.py", "helper-owner-path"):
            with self.subTest(refusal_owner=owner):
                self.assert_startup_refusal("import", self.startup_fixture("import", owner))


if __name__ == "__main__":
    unittest.main()
