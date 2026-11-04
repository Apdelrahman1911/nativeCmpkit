#!/usr/bin/env python3
"""Explicit off/fresh-producer/authenticated-acquisition driver for offline scopes.

Default off is NOT reuse eligibility or a pinning policy. Only this driver's fixed
read-only HTTPS acquisition can request reuse; local API envelopes are not inputs.
The unchanged checker does not certify their transport. Native, consumer, fresh
index/profile and security/release gates are outside this driver.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.client
import os
from pathlib import Path
import re
import ssl
import stat
import sys
import time
import types
import urllib.parse

import offline_tooling_reuse as reuse

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "nativecmpkit-offline-tooling-provenance-v1"
API_HOST = "api.github.com"
API_BASE = "/repos/" + reuse.REPOSITORY + "/actions/"
TOKEN_VARIABLE = "NATIVECMPKIT_ACTIONS_READ_TOKEN"
MODES = ("off", "produce", "reuse")
SELECTORS = ("producer_run_id", "producer_attempt", "producer_job_id", "producer_artifact_id")
MAX_JOB_PAGES = 100
MAX_JOBS = 100 * MAX_JOB_PAGES
MAX_ACQUIRED_BYTES = 64 * 1024**2
ACQUISITION_SECONDS = 180
IO_SECONDS = 30
BLOCK_BYTES = 64 * 1024
# Exact header-only origin observation649, SHA256
# 0807b1585c159821b88b2b4ee27b88a2b1e03fabdea4ea9f97fc94d9f0326614.
# This is not a tooling producer/download acceptance. Unknown hosts/routes refuse:
# no wildcard Azure/CDN guess, local URL, env override or redirect auto-admission.
REVIEWED_STORAGE_HOSTS: tuple[str, ...] = ("productionresultssa0.blob.core.windows.net",)
REVIEWED_STORAGE_ROUTE = "/actions-results/"
OPERATIONS = ("run-attempt", "jobs-page", "job", "artifact", "artifact-zip", "storage-zip")
SAFE_LEAF = re.compile(r"[a-z][a-z0-9-]{0,79}\.(?:json|zip)\Z")


def ensure(value: bool) -> None:
    if not value:
        raise ValueError("Offline tooling provenance guard refused")


def selector(value) -> int:
    ensure(type(value) is str and bool(re.fullmatch(r"[1-9][0-9]{0,15}", value)))
    result = int(value)
    ensure(reuse.positive(result))
    return result


def configuration(mode, output, selectors=None, recorded_signature=None, resolved_actions=None) -> dict:
    ensure(type(mode) is str and mode in MODES)
    ensure(type(output) is str and bool(re.fullmatch(r"build/ci-tooling-reuse/[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", output)))
    supplied = {} if selectors is None else selectors
    ensure(type(supplied) is dict and not (set(supplied) - set(SELECTORS)))
    supplied = {key: value for key, value in supplied.items() if value not in (None, "")}
    if mode == "reuse":
        ensure(set(supplied) == set(SELECTORS))
        supplied = {key: selector(supplied[key]) for key in SELECTORS}
    else:
        ensure(not supplied)
    for relative in (recorded_signature, resolved_actions):
        ensure(relative is None or (type(relative) is str and relative.startswith("build/ci-tooling-reuse/")
               and not relative.startswith(output + "/") and relative.endswith(".json")))
    ensure(mode != "off" or (recorded_signature is None and resolved_actions is None))
    return {"mode": mode, "output": output, "selectors": supplied,
            "recorded_signature": recorded_signature, "resolved_actions": resolved_actions}


def identity(observed):
    return (observed.st_dev, observed.st_ino, observed.st_mode, observed.st_nlink,
            observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns)


class OwnedDirectory:
    """Fresh ignored single child, exclusive openat writes and retained identities.

    Cooperative displacement checks, not a sandbox against the same OS principal.
    No reuse of a partial directory, overwrite, alternate path or automatic retry.
    """
    def __init__(self, root: Path, relative: str):
        self.root, self.relative = root, relative
        self.fds, self.chain, self.files = [], [], {}
        self.fd = None
        try:
            path = reuse.safe_path(root, relative)
            ensure(not path.exists())
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            parent = os.open(root, flags)
            self.fds.append(parent)
            for index, part in enumerate(relative.split("/")):
                last = index == 2
                try:
                    os.mkdir(part, mode=0o700, dir_fd=parent)
                except FileExistsError:
                    ensure(not last)
                child = os.open(part, flags, dir_fd=parent)
                self.fds.append(child)
                before = os.fstat(child)
                ensure(stat.S_ISDIR(before.st_mode) and before.st_uid == os.geteuid())
                if last:
                    ensure(stat.S_IMODE(before.st_mode) == 0o700)
                self.chain.append((parent, part, child, (before.st_dev, before.st_ino)))
                parent = child
            self.fd = parent
            self.hold()
        except BaseException:
            self.close(preserve=True)
            raise

    def hold(self) -> None:
        ensure(self.fd is not None)
        for parent, name, child, expected in self.chain:
            found = os.stat(name, dir_fd=parent, follow_symlinks=False)
            opened = os.fstat(child)
            ensure(stat.S_ISDIR(found.st_mode) and (found.st_dev, found.st_ino) == expected
                   and (opened.st_dev, opened.st_ino) == expected)

    def blob(self, name: str):
        self.hold()
        ensure(type(name) is str and bool(SAFE_LEAF.fullmatch(name)) and name not in self.files)
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
        self.files[name] = {"state": "open"}
        try:
            return OwnedBlob(self, name, fd)
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass  # Preserve the original ownership guard, never replace it.
            raise

    def write_json(self, name: str, value) -> dict:
        data = reuse.canonical(value) + b"\n"
        ensure(len(data) <= reuse.MAX_JSON_BYTES)
        blob = self.blob(name)
        try:
            blob.write(data)
            return blob.finish(True)
        except BaseException:
            blob.close(preserve=True)
            raise

    def read_complete(self, name: str, limit: int) -> bytes:
        self.hold()
        expected = self.files.get(name)
        ensure(type(expected) is dict and expected.get("complete") is True)
        raw = reuse.read_owned(self.root, self.relative + "/" + name, limit)
        found = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
        ensure(identity(found) == expected["identity"] and len(raw) == expected["bytes"]
               and reuse.digest(raw) == expected["sha256"])
        return raw

    def close(self, *, preserve=False):
        first = None
        while self.fds:
            fd = self.fds.pop()
            try:
                os.close(fd)
            except BaseException as error:
                if first is None:
                    first = error
        self.fd = None
        if first is not None and not preserve:
            raise first


class OwnedBlob:
    def __init__(self, owner: OwnedDirectory, name: str, fd: int):
        self.owner, self.name, self.fd = owner, name, fd
        self.size, self.digest = 0, hashlib.sha256()
        self.initial = os.fstat(fd)
        ensure(stat.S_ISREG(self.initial.st_mode) and self.initial.st_nlink == 1
               and stat.S_IMODE(self.initial.st_mode) == 0o600 and self.initial.st_size == 0)

    def write(self, data: bytes):
        ensure(type(data) is bytes and self.fd is not None)
        self.owner.hold()
        view = memoryview(data)
        while view:
            count = os.write(self.fd, view)
            ensure(type(count) is int and 0 < count <= len(view))
            self.digest.update(view[:count])
            self.size += count
            view = view[count:]

    def finish(self, complete: bool) -> dict:
        ensure(self.fd is not None and type(complete) is bool)
        self.owner.hold()
        os.fsync(self.fd)
        opened = os.fstat(self.fd)
        found = os.stat(self.name, dir_fd=self.owner.fd, follow_symlinks=False)
        ensure(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1 and opened.st_size == self.size
               and (opened.st_dev, opened.st_ino) == (self.initial.st_dev, self.initial.st_ino)
               and identity(opened) == identity(found))
        value = {"complete": complete, "bytes": self.size, "sha256": self.digest.hexdigest(),
                 "identity": identity(found)}
        self.owner.files[self.name] = value
        self.close()
        return {key: value[key] for key in ("complete", "bytes", "sha256")}

    def close(self, *, preserve=False):
        if self.fd is not None:
            fd, self.fd = self.fd, None
            try:
                os.close(fd)
            except BaseException:
                if not preserve:
                    raise


class State:
    def __init__(self, mode):
        self.mode = mode if type(mode) is str and mode in MODES else "invalid"
        self.stage, self.operation = "preflight", None
        self.ids, self.signature, self.signature_kind = {}, None, "unavailable"
        self.scope_results = None
        self.secondary, self.store, self.journal = [], None, None

    def note(self, operation: str, error: BaseException):
        self.secondary.append({"operation": operation, "refusal": sanitized_error(error)})

    def capsule(self, error: BaseException) -> dict:
        signature = self.signature
        return {"schema": SCHEMA, "outcome": "refused", "mode": self.mode, "stage": self.stage,
                "operation": self.operation, "requested_ids": self.ids,
                "signature_observation": self.signature_kind,
                "signature_sha256": signature["signature_sha256"] if signature is not None else None,
                "source_inputs_sha256": signature["source"]["inputs_sha256"] if signature is not None else None,
                "primary_refusal": sanitized_error(error), "secondary_refusals": self.secondary,
                "offline_scope_results": {"availability": "unavailable"} if self.scope_results is None else
                    {"availability": "observed", "results": self.scope_results},
                "authenticated_reuse_accepted": False, "reusable_producer_certificate": False,
                "library_or_native_results_reused": False, "consumer_results_reused": False,
                "release_readiness_certified": False}


class Journal:
    def __init__(self, store: OwnedDirectory, state: State):
        self.store, self.state = store, state
        self.requests, self.keys = [], set()
        self.ids = state.ids.copy()  # One frozen exact selector context per client.

    def begin(self, operation: str, parameters: dict) -> dict:
        ensure(operation in OPERATIONS and type(parameters) is dict
               and set(self.ids) == set(SELECTORS) and all(reuse.positive(value) for value in self.ids.values())
               and set(parameters) == set(SELECTORS) | ({"page"} if operation == "jobs-page" else set())
               and all(reuse.positive(value) for value in parameters.values())
               and {key: parameters[key] for key in SELECTORS} == self.ids
               and (operation != "jobs-page" or parameters["page"] <= MAX_JOB_PAGES))
        key = (operation, tuple(sorted(parameters.items())))
        ensure(key not in self.keys and len(self.requests) < MAX_JOB_PAGES + 5)
        self.keys.add(key)  # Before any I/O; a refused write/request is not retried.
        entry = {"number": len(self.requests) + 1, "operation": operation, "parameters": parameters.copy(),
                 "channel": "signed-storage" if operation == "storage-zip" else "authenticated-api",
                 "started": True, "completion_attempted": False, "response": None}
        self.requests.append(entry)
        self.state.operation, self.state.stage = operation, "acquire-" + operation
        self.store.write_json("request-" + str(entry["number"]).zfill(3) + "-start.json",
                              {key: entry[key] for key in ("number", "operation", "parameters", "channel", "started")})
        return entry

    def finish(self, entry: dict, response: dict):
        ensure(entry in self.requests and entry["completion_attempted"] is False)
        entry["completion_attempted"] = True
        entry["response"] = response
        self.store.write_json("request-" + str(entry["number"]).zfill(3) + "-result.json", response)

    def summary(self) -> dict:
        return {"schema": SCHEMA, "api_requests_started": sum(item["channel"] == "authenticated-api" for item in self.requests),
                "storage_hops_started": sum(item["channel"] == "signed-storage" for item in self.requests),
                "requests": self.requests, "automatic_retries": False, "automatic_redirects": False,
                "raw_headers_or_signed_urls_exported": False}


def take_token() -> str:
    # Remove the explicit ephemeral credential BEFORE any helper subprocess.
    value = os.environ.pop(TOKEN_VARIABLE, None)
    ensure(type(value) is str and bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,8192}", value)))
    return value


class HTTPSAcquirer:
    """Direct verified-TLS GET only: no urllib proxy/cache/redirect/retry machinery."""
    def __init__(self, token: str, store: OwnedDirectory, journal: Journal, state: State,
                 *, connection_factory=None, clock=None):
        ensure(type(token) is str and bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,8192}", token)))
        self.token, self.store, self.journal, self.state = token, store, journal, state
        self.pending_storage = None
        self.connection_factory = connection_factory or http.client.HTTPSConnection
        self.clock = clock or time.monotonic
        self.deadline = self.clock() + ACQUISITION_SECONDS
        self.acquired_bytes = 0
        self.context = ssl.create_default_context()
        ensure(self.context.verify_mode == ssl.CERT_REQUIRED and self.context.check_hostname is True)

    def remaining(self):
        remaining = self.deadline - self.clock()
        ensure(remaining > 0)
        return min(IO_SECONDS, remaining)

    @staticmethod
    def headers(response) -> dict:
        items = response.getheaders()
        ensure(type(items) is list and len(items) <= 100)
        selected, total = {}, 0
        for key, value in items:
            ensure(type(key) is str and type(value) is str)
            total += len(key) + len(value)
            ensure(total <= 64 * 1024 and not any(char in key + value for char in ("\r", "\n", "\0")))
            key = key.lower()
            if key in {"content-length", "content-type", "content-encoding", "transfer-encoding", "location"}:
                ensure(key not in selected)
                selected[key] = value
        ensure(selected.get("content-encoding", "identity").lower() == "identity")
        ensure(selected.get("transfer-encoding", "chunked").lower() == "chunked")
        ensure(not ("content-length" in selected and "transfer-encoding" in selected))
        return selected

    @staticmethod
    def storage_target(location) -> tuple[str, str]:
        ensure(type(location) is str and 0 < len(location) <= 8192 and location.isascii()
               and not any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in location))
        target = urllib.parse.urlsplit(location)
        ensure(target.scheme == "https" and target.hostname in REVIEWED_STORAGE_HOSTS
               and target.netloc == target.hostname and target.port is None and target.username is None
               and target.password is None and not target.fragment and len(REVIEWED_STORAGE_ROUTE) < len(target.path) <= 4096
               and target.path.startswith(REVIEWED_STORAGE_ROUTE) and 0 < len(target.query) <= 4096)
        path = target.path
        # Only the literal reviewed route, without decoding/normalizing aliases.
        # Unknown escaped blob paths need separate source review, not guessing.
        ensure("%" not in path and "\\" not in path
               and not any(part in ("", ".", "..") for part in path.split("/")[1:]))
        return target.hostname, target.path + "?" + target.query  # In memory only; never journalled.

    def _read(self, connection, response, headers, blob, limit: int) -> bytes:
        length = headers.get("content-length")
        if length is not None:
            ensure(bool(re.fullmatch(r"0|[1-9][0-9]{0,10}", length)) and int(length) <= limit)
        raw = bytearray()
        while True:
            remaining = self.remaining()
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            bound = min(BLOCK_BYTES, limit - len(raw) + 1, MAX_ACQUIRED_BYTES - self.acquired_bytes + 1)
            ensure(bound > 0)
            try:
                block = response.read(bound)
            except http.client.IncompleteRead as error:
                # Only the exact original HTTP exception's returned partial bytes.
                # They stay incomplete; its message/headers/URL are never exported.
                block = error.partial if type(error.partial) is bytes else b""
                if len(raw) + len(block) <= limit and self.acquired_bytes + len(block) <= MAX_ACQUIRED_BYTES:
                    blob.write(block)
                    self.acquired_bytes += len(block)
                raise
            ensure(type(block) is bytes and len(block) <= bound)
            self.remaining()
            if not block:
                break
            ensure(len(raw) + len(block) <= limit and self.acquired_bytes + len(block) <= MAX_ACQUIRED_BYTES)
            blob.write(block)
            raw.extend(block)
            self.acquired_bytes += len(block)
        ensure(raw and (length is None or len(raw) == int(length)))
        return bytes(raw)

    def request(self, operation: str, path: str, parameters: dict, name: str, *, storage_host=None):
        ensure(operation in OPERATIONS)
        if storage_host is None:
            ensure(operation != "storage-zip" and path == api_path(operation, parameters))
            host = API_HOST
        else:
            ensure(operation == "storage-zip" and storage_host in REVIEWED_STORAGE_HOSTS
                   and self.pending_storage == (storage_host, path))
            self.pending_storage = None  # Consume this authenticated response once.
            host = storage_host
        entry = self.journal.begin(operation, parameters)
        connection, blob, response_status, witness, primary = None, None, None, None, None
        try:
            headers = {"Accept": "application/vnd.github+json", "Accept-Encoding": "identity",
                       "User-Agent": "NativeCmpKit-offline-tooling-provenance-v1", "Cache-Control": "no-cache", "Pragma": "no-cache"}
            if storage_host is None:
                ensure(self.token is not None)
                headers.update({"Authorization": "Bearer " + self.token, "X-GitHub-Api-Version": "2022-11-28"})
            else:
                headers["Accept"] = "application/zip, application/octet-stream"
            connection = self.connection_factory(host, port=443, timeout=self.remaining(), context=self.context)
            connection.request("GET", path, headers=headers)
            self.remaining()
            response = connection.getresponse()
            response_status = response.status
            ensure(type(response_status) is int)
            selected = self.headers(response)
            if operation == "artifact-zip" and response_status == 302:
                target = self.storage_target(selected.get("location"))
                self.journal.finish(entry, {"status": 302, "outcome": "approved-storage-redirect", "body": {"availability": "unread"}})
                self.pending_storage = target
                return target
            ensure(response_status == 200 and "location" not in selected)
            is_zip = operation in ("artifact-zip", "storage-zip")
            content_type = selected.get("content-type", "").lower()
            ensure(content_type in ("application/zip", "application/octet-stream") if is_zip else
                   bool(re.fullmatch(r"application/(?:json|vnd\.github\+json)(?:; *charset=utf-8)?", content_type)))
            blob = self.store.blob(name)
            raw = self._read(connection, response, selected, blob, reuse.MAX_ARCHIVE_BYTES if is_zip else reuse.MAX_JSON_BYTES)
            witness = blob.finish(True)
            self.journal.finish(entry, {"status": response_status, "outcome": "complete-original-response", "body": witness})
            return raw
        except BaseException as error:
            primary = error
            if blob is not None and blob.fd is not None:
                try:
                    witness = blob.finish(False)
                except BaseException as later:
                    self.state.note("partial-body-storage", later)
                    blob.close(preserve=True)
            if not entry["completion_attempted"]:
                try:
                    self.journal.finish(entry, {"status": response_status, "outcome": "refused",
                                               "body": witness if witness is not None else {"availability": "unavailable"}})
                except BaseException as later:
                    self.state.note("request-journal-storage", later)
            raise
        finally:
            if connection is not None:
                try:
                    connection.close()
                except BaseException as later:
                    if primary is None:
                        raise
                    self.state.note("https-connection-close", later)

    def json(self, operation, path, parameters, name):
        raw = self.request(operation, path, parameters, name)
        ensure(type(raw) is bytes)
        held = self.store.read_complete(name, reuse.MAX_JSON_BYTES)
        ensure(held == raw)
        return reuse.parse_json(raw)

    def close(self):
        self.token = None
        self.pending_storage = None


def api_path(operation: str, parameters: dict) -> str:
    ensure(operation in OPERATIONS and operation != "storage-zip" and type(parameters) is dict
           and set(parameters) == set(SELECTORS) | ({"page"} if operation == "jobs-page" else set())
           and all(reuse.positive(value) for value in parameters.values()))
    run_id, attempt, job_id, artifact_id = (parameters[key] for key in SELECTORS)
    return {
        "run-attempt": API_BASE + f"runs/{run_id}/attempts/{attempt}",
        "jobs-page": API_BASE + f"runs/{run_id}/attempts/{attempt}/jobs?per_page=100&page={parameters.get('page', 1)}",
        "job": API_BASE + f"jobs/{job_id}",
        "artifact": API_BASE + f"artifacts/{artifact_id}",
        "artifact-zip": API_BASE + f"artifacts/{artifact_id}/zip",
    }[operation]


def fixed_tooling_steps(job: dict) -> None:
    ensure(job.get("name") == "tooling" and job.get("conclusion") == "success"
           and job.get("labels") == ["ubuntu-24.04"])
    steps = job.get("steps")
    ensure(type(steps) is list and all(type(step) is dict and reuse.positive(step.get("number")) for step in steps))
    numbers = [step["number"] for step in steps]
    ensure(numbers == sorted(set(numbers)))
    indices = []
    for name in reuse.REQUIRED_STEPS:
        matches = [(index, step) for index, step in enumerate(steps) if step.get("name") == name]
        ensure(len(matches) == 1 and matches[0][1].get("status") == "completed"
               and matches[0][1].get("conclusion") == "success")
        indices.append(matches[0][0])
    ensure(indices == sorted(indices))


def fixed_job(job: dict, run: dict) -> None:
    ensure(type(job) is dict and reuse.positive(job.get("id"))
           and type(job.get("run_id")) is int and job["run_id"] == run["id"]
           and type(job.get("run_attempt")) is int and job["run_attempt"] == run["run_attempt"]
           and job.get("head_sha") == run["head_sha"] and job.get("head_branch") == reuse.BRANCH
           and job.get("url") == "https://" + API_HOST + API_BASE + "jobs/" + str(job["id"])
           and job.get("run_url") == run["url"] and type(job.get("name")) is str and 0 < len(job["name"]) <= 512
           and job.get("status") == "completed" and job.get("conclusion") in
               ("success", "failure", "neutral", "cancelled", "skipped", "timed_out", "action_required", "stale", "startup_failure"))


def fixed_run(run: dict, current: dict, ids: dict) -> None:
    ensure(type(run) is dict and type(run.get("id")) is int and run["id"] == ids["producer_run_id"]
           and type(run.get("run_attempt")) is int and run["run_attempt"] == ids["producer_attempt"])
    repository, head = run.get("repository"), run.get("head_repository")
    ensure(type(repository) is dict and type(head) is dict and repository.get("full_name") == reuse.REPOSITORY
           and head.get("full_name") == reuse.REPOSITORY and reuse.positive(repository.get("id"))
           and type(head.get("id")) is int and head["id"] == repository["id"])
    ensure(run.get("path") == reuse.WORKFLOW and run.get("event") == "workflow_dispatch"
           and run.get("head_branch") == reuse.BRANCH and run.get("head_sha") == current["source"]["revision"]
           and run.get("status") == "completed" and run.get("conclusion") in ("success", "failure")
           and run.get("url") == "https://" + API_HOST + API_BASE + "runs/" + str(run["id"]))


def fixed_artifact(artifact: dict, run: dict, job: dict, current: dict, ids: dict, now: dt.datetime) -> None:
    ensure(type(artifact) is dict and type(artifact.get("id")) is int and artifact["id"] == ids["producer_artifact_id"]
           and artifact.get("url") == "https://" + API_HOST + API_BASE + "artifacts/" + str(artifact["id"])
           and artifact.get("archive_download_url") == artifact["url"] + "/zip"
           and artifact.get("expired") is False and type(artifact.get("size_in_bytes")) is int
           and 0 < artifact["size_in_bytes"] <= reuse.MAX_ARCHIVE_BYTES
           and type(artifact.get("digest")) is str and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", artifact["digest"]))
           and artifact.get("name") == reuse.ARTIFACT_PREFIX + current["signature_sha256"])
    owner = artifact.get("workflow_run")
    ensure(type(owner) is dict and type(owner.get("id")) is int and owner["id"] == run["id"]
           and type(owner.get("repository_id")) is int and owner["repository_id"] == run["repository"]["id"]
           and type(owner.get("head_repository_id")) is int and owner["head_repository_id"] == run["repository"]["id"]
           and owner.get("head_sha") == run["head_sha"] and owner.get("head_branch") == reuse.BRANCH)
    ensure(reuse.timestamp(job.get("started_at")) <= reuse.timestamp(artifact.get("created_at"))
           <= reuse.timestamp(job.get("completed_at")) <= now < reuse.timestamp(artifact.get("expires_at")))


def acquire(client: HTTPSAcquirer, current: dict, ids: dict, now: dt.datetime):
    run_id, attempt, job_id, artifact_id = (ids[key] for key in SELECTORS)
    run = client.json("run-attempt", API_BASE + f"runs/{run_id}/attempts/{attempt}", ids, "run.json")
    fixed_run(run, current, ids)
    jobs, seen, total, pages, selected = [], set(), None, 1, None
    page = 1
    while page <= pages:
        parameters = {**ids, "page": page}
        envelope = client.json("jobs-page", API_BASE + f"runs/{run_id}/attempts/{attempt}/jobs?per_page=100&page={page}",
                               parameters, "jobs-page-" + str(page).zfill(3) + ".json")
        ensure(type(envelope) is dict and set(envelope) == {"total_count", "jobs"}
               and type(envelope["total_count"]) is int and 0 < envelope["total_count"] <= MAX_JOBS
               and type(envelope["jobs"]) is list)
        if total is None:
            total = envelope["total_count"]
            pages = (total + 99) // 100
        ensure(envelope["total_count"] == total and len(envelope["jobs"]) == min(100, total - 100 * (page - 1)))
        for job in envelope["jobs"]:
            fixed_job(job, run)
            ensure(job["id"] not in seen)
            seen.add(job["id"])
            jobs.append(job)
            if job["name"] == "tooling":
                ensure(selected is None and job["id"] == job_id and job["conclusion"] == "success"
                       and job.get("labels") == ["ubuntu-24.04"] and type(job.get("steps")) is list)
                selected = job
        page += 1
    ensure(len(jobs) == total and selected is not None)
    job = client.json("job", API_BASE + f"jobs/{job_id}", ids, "job.json")
    fixed_job(job, run)
    governing = ("id", "run_id", "run_attempt", "head_sha", "head_branch", "url", "run_url", "name",
                 "status", "conclusion", "labels", "steps", "started_at", "completed_at")
    ensure(all(key in selected and key in job and selected[key] == job[key] for key in governing))
    fixed_tooling_steps(job)
    artifact = client.json("artifact", API_BASE + f"artifacts/{artifact_id}", ids, "artifact.json")
    fixed_artifact(artifact, run, job, current, ids, now)
    original = client.request("artifact-zip", API_BASE + f"artifacts/{artifact_id}/zip", ids, "archive.zip")
    if type(original) is tuple:
        original = client.request("storage-zip", original[1], ids, "archive.zip", storage_host=original[0])
    ensure(type(original) is bytes and len(original) == artifact["size_in_bytes"]
           and "sha256:" + reuse.digest(original) == artifact["digest"])
    held = client.store.read_complete("archive.zip", reuse.MAX_ARCHIVE_BYTES)
    ensure(held == original)
    return original, run, job, artifact


def common_result(mode: str, passed: bool) -> dict:
    return {"schema": SCHEMA, "mode": mode, "outcome": "passed" if passed else "failed",
            "fresh_index_and_profile_checks_reused": False, "library_or_native_results_reused": False,
            "consumer_results_reused": False, "native_failure_waived": False, "release_readiness_certified": False}


def expected_signature(root: Path, config: dict):
    resolutions = reuse.parse_json(reuse.read_owned(root, config["resolved_actions"])) if config["resolved_actions"] else None
    expected = reuse.parse_json(reuse.read_owned(root, config["recorded_signature"])) if config["recorded_signature"] else None
    if expected is not None:
        reuse.validate_signature(expected)
    return expected, resolutions


def run(mode="off", *, root=ROOT, output_dir, selectors=None, recorded_signature=None, resolved_actions=None,
        token_reader=None, client_factory=None, now=None) -> dict:
    """Narrow refusal boundary. Dependency injection is source-only fixture wiring.

    No CLI input accepts API JSON, archive bytes, a decision or a caller URL.
    A passed fixture output is a model, not authenticated hosted acceptance.
    """
    state, client, primary = State(mode), None, None
    try:
        config = configuration(mode, output_dir, selectors, recorded_signature, resolved_actions)
        state.ids = config["selectors"]
        # Resolve all caller-owned inputs before claiming outputs or taking a token.
        reuse.safe_path(root, config["output"])
        for relative in (recorded_signature, resolved_actions):
            if relative is not None:
                reuse.safe_path(root, relative)
        state.store = OwnedDirectory(root, config["output"])
        state.journal = Journal(state.store, state)
        if mode == "off":
            state.stage = "ordinary-offline-scopes"
            results, deadline = [], time.monotonic() + 840
            for scope in reuse.SCOPES:
                result = reuse.execute_scope(root, scope, deadline - time.monotonic())
                results.append(result)
                state.scope_results = results
                if not result["passed"]:
                    break
            passed = len(results) == len(reuse.SCOPES) and all(item["passed"] for item in results)
            result = {**common_result(mode, passed), "scope_results": results, "new_scope_executions": len(results),
                      "reusable_producer_certificate": False, "authentication_requested": False}
            result_leaf = "off-result.json"
        else:
            state.stage = "read-recorded-signature"
            expected, resolutions = expected_signature(root, config)
            if mode == "produce":
                ensure(not os.environ.get(TOKEN_VARIABLE))
                # With a genuinely recorded expected signature, unchanged run_scopes
                # supplies the mandatory fresh before/after boundaries; no duplicate
                # driver capture. Without it, capture once to establish the expected.
                state.signature = expected if expected is not None else reuse.capture(root, resolutions)
                state.signature_kind = "expected-recorded" if expected is not None else "live-current"
                state.store.write_json("signature.json", state.signature)
                state.stage = "fresh-producer-scopes"
                receipt = reuse.run_scopes(root, state.signature, resolutions)
                ensure(type(receipt) is dict and receipt.get("schema") == reuse.SCHEMA
                       and receipt.get("signature") == state.signature and type(receipt.get("passed")) is bool)
                state.scope_results = receipt["scope_results"]
                if receipt["inputs_held"] is True:
                    state.signature_kind = "helper-live-before-and-after-held"
                passed = receipt["passed"] is True
                if passed:
                    ensure(receipt["fresh_scope_execution"] is True and receipt["inputs_held"] is True
                           and len(receipt["scope_results"]) == len(reuse.SCOPES)
                           and all(item["passed"] is True for item in receipt["scope_results"]))
                state.store.write_json("receipt.json" if passed else "scope-result.json", receipt)
                result = {**common_result(mode, passed), "signature_sha256": state.signature["signature_sha256"],
                          "new_scope_executions": len(receipt["scope_results"]), "authentication_requested": False,
                          "reusable_producer_certificate": passed,
                          "artifact_name": reuse.ARTIFACT_PREFIX + state.signature["signature_sha256"] if passed else None}
                result_leaf = "producer-result.json"
            else:
                # Drain the explicit token after path/recorded-input validation,
                # before helper capture() creates Git/tool-version subprocesses.
                # No client/network operation precedes the fresh source check.
                state.stage = "read-ephemeral-token"
                token = (token_reader or take_token)()
                state.stage = "fresh-current-before-acquisition"
                current = reuse.capture(root, resolutions)
                reuse.validate_signature(current)
                ensure(expected is None or current == expected)
                state.signature, state.signature_kind = current, "live-current-before"
                state.store.write_json("signature.json", current)
                state.stage = "create-fixed-authenticated-client"
                client = (client_factory or HTTPSAcquirer)(token, state.store, state.journal, state)
                token = None
                original, producer_run, job, artifact = acquire(client, current, state.ids,
                                                               now or dt.datetime.now(dt.timezone.utc))
                state.stage = "unchanged-offline-consistency-check"
                checked = reuse.check(current, original, producer_run, job, artifact, now=now)
                ensure(checked["eligible"] is True and checked["new_scope_executions"] == 0
                       and checked["authenticated_transport_by_helper"] is False)
                state.stage = "fresh-current-after-check"
                after = reuse.capture(root, resolutions)
                ensure(after == current)
                state.signature_kind = "live-current-before-and-after-held"
                state.store.write_json("signature-after.json", after)
                result = {**common_result(mode, True), "checker_decision": checked, "new_scope_executions": 0,
                          "signature_sha256": current["signature_sha256"], "authenticated_acquisition_completed": True,
                          "reusable_producer_certificate": False, "original_zip_sha256": reuse.digest(original),
                          "original_zip_bytes": len(original)}
                result_leaf = "reuse-decision.json"
        state.stage = "hold-original-acquisition-files"
        for name, observation in state.store.files.copy().items():
            if observation.get("complete") is True:
                state.store.read_complete(name, reuse.MAX_ARCHIVE_BYTES if name == "archive.zip" else reuse.MAX_JSON_BYTES)
        state.store.write_json("acquisition-summary.json", state.journal.summary())
        state.store.write_json(result_leaf, result)
        return result
    except BaseException as error:
        primary = error
        capsule = state.capsule(error)
        if state.store is not None and state.store.fd is not None:
            try:
                state.store.write_json("refusal.json", capsule)
            except BaseException as later:
                state.note("refusal-capsule-storage", later)
                capsule = state.capsule(error)
                print(reuse.canonical(capsule).decode(), file=sys.stderr)
        else:
            print(reuse.canonical(capsule).decode(), file=sys.stderr)
        raise
    finally:
        cleanup_primary = None
        if client is not None:
            if primary is None:
                state.stage = "authenticated-client-close"
            try:
                client.close()
            except BaseException as later:
                if primary is None:
                    cleanup_primary = later
                else:
                    state.note("authenticated-client-close", later)
                    print(reuse.canonical(state.capsule(primary)).decode(), file=sys.stderr)
        if cleanup_primary is not None and state.store is not None and state.store.fd is not None:
            try:
                state.store.write_json("refusal.json", state.capsule(cleanup_primary))
            except BaseException as later:
                state.note("refusal-capsule-storage", later)
                print(reuse.canonical(state.capsule(cleanup_primary)).decode(), file=sys.stderr)
        if state.store is not None:
            try:
                state.store.close()
            except BaseException as later:
                if primary is not None or cleanup_primary is not None:
                    state.note("invocation-directory-close", later)
                    print(reuse.canonical(state.capsule(primary or cleanup_primary)).decode(), file=sys.stderr)
                else:
                    # No alternate output location: closed/displaced storage cannot
                    # certify a successful invocation. Only sanitized stderr remains.
                    print(reuse.canonical(state.capsule(later)).decode(), file=sys.stderr)
                    raise
        if cleanup_primary is not None:
            raise cleanup_primary


def public_code_objects(module) -> set:
    result = set()
    def add(code):
        if type(code) is not types.CodeType or code in result:
            return
        result.add(code)
        for value in code.co_consts:
            add(value)
    for value in vars(module).values():
        if type(value) is types.FunctionType and value.__module__ == module.__name__:
            add(value.__code__)
        elif type(value) is type and value.__module__ == module.__name__:
            for member in vars(value).values():
                if isinstance(member, (staticmethod, classmethod)):
                    member = member.__func__
                if type(member) is types.FunctionType:
                    add(member.__code__)
    return result


PUBLIC_SOURCES = {}


def observe_public_sources():
    PUBLIC_SOURCES.clear()
    observed = {}
    for module, relative in ((sys.modules[__name__], "scripts/ci/offline_tooling_provenance.py"),
                             (reuse, "scripts/ci/offline_tooling_reuse.py")):
        path = Path(module.__file__).resolve()
        ensure(path == ROOT / relative)
        codes = public_code_objects(module)
        ensure(bool(codes))
        observed[relative] = {"path": path, "sha256": reuse.hash_file(path), "codes": codes}
    PUBLIC_SOURCES.update(observed)


def sanitized_error(error: BaseException) -> dict:
    names = {ValueError: "ValueError", OSError: "OSError", TimeoutError: "TimeoutError", RuntimeError: "RuntimeError",
             KeyboardInterrupt: "KeyboardInterrupt", SystemExit: "SystemExit", ssl.SSLError: "SSLError",
             http.client.IncompleteRead: "IncompleteRead", http.client.HTTPException: "HTTPException"}
    category = names.get(type(error), "other-public-or-private-exception")
    frames, trace, visited = [], error.__traceback__, 0
    while trace is not None and visited < 64:
        visited += 1
        for relative, owner in PUBLIC_SOURCES.items():
            if trace.tb_frame.f_code in owner["codes"]:
                try:
                    held = reuse.hash_file(owner["path"]) == owner["sha256"]
                except BaseException:
                    held = False
                if held:
                    frames.append({"owner": relative, "source_sha256": owner["sha256"],
                                   "function": trace.tb_frame.f_code.co_name, "line": trace.tb_lineno,
                                   "instruction_offset": trace.tb_lasti})
        trace = trace.tb_next
    return {"category": category, "public_source_frames": frames,
            "exit_code": error.code if type(error) is SystemExit and type(error.code) is int and -255 <= error.code <= 255 else None,
            "secondary_note_presence_observed": type(getattr(error, "__notes__", None)) is list,
            "secondary_note_details": "unavailable", "exception_messages_chains_locals_exported": False}


class SafeParser(argparse.ArgumentParser):
    def error(self, _message):
        raise ValueError("Offline tooling provenance arguments refused")


def main() -> int:
    parser = SafeParser(description=__doc__)
    parser.add_argument("--mode", default="off")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--recorded-signature")
    parser.add_argument("--resolved-actions")
    for field in SELECTORS:
        parser.add_argument("--" + field.replace("_", "-"))
    args = parser.parse_args()
    result = run(args.mode, output_dir=args.output_dir,
                 selectors={field: getattr(args, field) for field in SELECTORS},
                 recorded_signature=args.recorded_signature, resolved_actions=args.resolved_actions)
    print(reuse.canonical({key: result[key] for key in ("mode", "outcome", "new_scope_executions", "reusable_producer_certificate")}).decode())
    return 0 if result["outcome"] == "passed" else 1


_public_sources_ready = False
try:
    observe_public_sources()
    _public_sources_ready = True
    if __name__ == "__main__":
        exit_code = main()
except BaseException as error:
    print(reuse.canonical({"schema": SCHEMA, "outcome": "refused",
                           "boundary": "driver-main" if _public_sources_ready else "source-observation",
                           "primary_refusal": sanitized_error(error)}).decode(), file=sys.stderr)
    exit_code = error.code if type(error) is SystemExit and type(error.code) is int else 130 if type(error) is KeyboardInterrupt else 2
    if not _public_sources_ready and (exit_code == 0 or not -255 <= exit_code <= 255):
        exit_code = 2  # A missing initialization witness cannot exit successfully.
    if __name__ != "__main__":
        raise SystemExit(exit_code) from None

if __name__ == "__main__":
    raise SystemExit(exit_code)
