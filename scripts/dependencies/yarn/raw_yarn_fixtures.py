#!/usr/bin/env python3
"""Bounded, isolated RAW Yarn Classic characterization with synthetic packages.

No Gradle, arbitrary registry, inherited user configuration, tool installation or
shared-cache mutation. This is not a kernel/network sandbox. A raw acceptance
counterexample is never reported as a security-enforcement pass.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tarfile
import threading
import time
from urllib.parse import urlsplit


REPO = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
EVIDENCE = REPO / "docs/development/evidence/build/yarn-fixtures"
NODE = Path("/root/.gradle/nodejs/node-v24.16.0-linux-x64/bin/node")
YARN_HOME = Path("/root/.gradle/yarn/yarn-v1.22.22")
YARN = YARN_HOME / "bin/yarn.js"
PINS = {
    NODE: "b2959781cc5a74c357ffa02367efa8a0330cbb1c9cb347732fdfaaaca381cbcd",
    YARN: "148e19db309ec9eaf7720b28df811337906eea8a1758deaa54afee60a6305e04",
    YARN_HOME / "lib/cli.js": "443ed69e76443b89afddccfc9faec1ff16eb5e500979cc079c696dec4c3d94ee",
    YARN_HOME / "lib/v8-compile-cache.js": "ec1d7229ff64232637f255f2f042daf9aeb59b3dd3c66db64e2c2b75cb4562d6",
    YARN_HOME / "package.json": "9533b84eaaeea708ab99bcf92772bc81c7389f90a04f8b0188c163f9b3b621c3",
}
PARENT = "nativecmpkit-fixture-parent"
LEAF = "nativecmpkit-fixture-leaf"
ROOT_MARKER = "root-script-ran.txt"
LEAF_MARKER = "dependency-script-ran.txt"
FROZEN_ERROR = "Your lockfile needs to be updated, but yarn was run with `--frozen-lockfile`."
MAX_LOG_BYTES = 4 * 1024 * 1024
MIN_RESERVE = 8192 * 1024 * 1024
CASES = (
    "YF001-positive", "YF002-missing-lock", "YF003-direct-drift",
    "YF004-wrong-sri", "YF005-changed-tarball", "YF006-incomplete-transitive",
    "YF008-script-control", "YF008-scripts-suppressed",
)
EXPECTED_CATEGORIES = {
    "bootstrap": "unfrozen-bootstrap-succeeded",
    "YF001-positive": "frozen-install-succeeded",
    "YF002-missing-lock": "accepted-without-lock-counterexample",
    "YF003-direct-drift": "frozen-lock-rejection",
    "YF004-wrong-sri": "tarball-integrity-rejection",
    "YF005-changed-tarball": "tarball-integrity-rejection",
    "YF006-incomplete-transitive": "accepted-incomplete-transitive-lock-counterexample",
    "YF008-script-control": "scripts-control-succeeded",
    "YF008-scripts-suppressed": "frozen-install-scripts-suppressed",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def sri(data: bytes, algorithm: str = "sha512") -> str:
    return algorithm + "-" + base64.b64encode(hashlib.new(algorithm, data).digest()).decode("ascii")


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def no_symlinks(path: Path) -> None:
    require(path.is_absolute() and ".." not in path.parts, "Expected absolute non-traversing path")
    for part in (path, *path.parents):
        require(not part.is_symlink(), "Refusing path through symlink: " + part.name)


def write_new(path: Path, data: bytes) -> None:
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def snapshot(path: Path) -> dict:
    no_symlinks(path)
    if not path.exists():
        return {"exists": False, "sha256": None, "bytes": 0}
    require(path.is_file(), "Expected regular input: " + path.name)
    data = path.read_bytes()
    return {"exists": True, "sha256": digest(data), "bytes": len(data)}


def free_bytes(path: Path) -> int:
    stats = os.statvfs(path)
    return stats.f_bavail * stats.f_frsize


def validate_limits(total: int, per_process: int, reserve_mib: int) -> None:
    require(30 <= total <= 300, "Total timeout must be 30..300 seconds")
    require(1 <= per_process <= 60, "Per-process timeout must be 1..60 seconds")
    require(reserve_mib >= 8192, "At least 8192 MiB reserve is required")


class Budget:
    def __init__(self, root: Path, total: int, per_process: int, reserve_mib: int):
        validate_limits(total, per_process, reserve_mib)
        self.root = root
        self.started = time.monotonic()
        self.deadline = self.started + total
        self.per_process = per_process
        self.reserve = reserve_mib * 1024 * 1024

    def reason(self) -> str | None:
        if free_bytes(self.root) < self.reserve:
            return "disk-reserve"
        # Leave time for child termination, server shutdown and receipts.
        if time.monotonic() >= self.deadline - 12:
            return "total-timeout"
        return None


def marker_script(name: str) -> bytes:
    require(name in {ROOT_MARKER, LEAF_MARKER}, "Unknown marker")
    return ("'use strict';\nrequire('fs').writeFileSync(" + json.dumps(name)
            + ", 'self-authored harmless fixture marker\\n', {flag: 'wx'});\n").encode()


def package_files(name: str, version: str, *, changed: bool = False) -> dict[str, bytes]:
    require((name, version) in {(PARENT, "1.0.0"), (PARENT, "2.0.0"), (LEAF, "1.0.0")},
            "Unknown synthetic package")
    require(not changed or name == LEAF, "Only leaf payload can change")
    manifest = {"name": name, "version": version, "license": "Apache-2.0", "main": "index.js"}
    files = {"index.js": b"'use strict';\nmodule.exports = 'inert synthetic fixture';\n",
             "payload.txt": ("changed valid payload\n" if changed else "original valid payload\n").encode()}
    if name == PARENT:
        manifest["dependencies"] = {LEAF: "1.0.0"}
    else:
        manifest["scripts"] = {"postinstall": "node marker.js"}
        files["marker.js"] = marker_script(LEAF_MARKER)
    files["package.json"] = json_bytes(manifest)
    return files


def tarball(files: dict[str, bytes]) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, data in sorted(files.items()):
            require(re.fullmatch(r"[a-z][a-z0-9.-]*", name) is not None, "Unsafe package member")
            info = tarfile.TarInfo("package/" + name)
            info.size = len(data)
            info.mode = 0o644
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", filename="", mtime=0) as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def root_files(version: str = "1.0.0") -> dict[str, bytes]:
    require(version in {"1.0.0", "2.0.0"}, "Unknown root dependency version")
    return {
        "package.json": json_bytes({"name": "nativecmpkit-raw-yarn-fixture", "version": "1.0.0",
                                    "private": True, "license": "Apache-2.0",
                                    "dependencies": {PARENT: version},
                                    "scripts": {"postinstall": "node root-marker.js"}}),
        "root-marker.js": marker_script(ROOT_MARKER),
    }


def lock_blocks(text: str) -> dict[str, str]:
    """Narrow seed-lock parser; not a general-purpose Yarn lock validator."""
    require(len(text.encode()) <= 1024 * 1024, "Oversized seed lock")
    require("# yarn lockfile v1\n" in text and "\r" not in text, "Unexpected seed lock header/EOL")
    starts = list(re.finditer(r"(?m)^([^\s#][^\n]*):\n", text))
    blocks = {}
    for index, match in enumerate(starts):
        key = match.group(1)
        if key.startswith('"'):
            key = json.loads(key)
        require(key in {PARENT + "@1.0.0", LEAF + "@1.0.0"}, "Unexpected seed lock key")
        require(key not in blocks, "Duplicate seed lock key")
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        blocks[key] = text[match.start():end]
    require(bool(blocks), "No seed lock blocks")
    return blocks


def lock_field(block: str, name: str) -> str:
    matches = re.findall(r"(?m)^  " + re.escape(name) + r" ([^\n]+)$", block)
    require(len(matches) == 1, "Missing/duplicate seed lock field: " + name)
    return json.loads(matches[0]) if matches[0].startswith('"') else matches[0]


def mutate_lock(seed: str, case: str) -> str | None:
    require(case in CASES, "Unknown fixture case")
    blocks = lock_blocks(seed)
    require(set(blocks) == {PARENT + "@1.0.0", LEAF + "@1.0.0"}, "Seed needs exact graph")
    leaf = blocks[LEAF + "@1.0.0"]
    if case == "YF002-missing-lock":
        return None
    if case == "YF006-incomplete-transitive":
        return seed.replace(leaf, "", 1)
    if case == "YF004-wrong-sri":
        wrong = "sha512-" + base64.b64encode(bytes(64)).decode("ascii")
        old = lock_field(leaf, "integrity")
        require(old != wrong and old.startswith("sha512-"), "Unexpected seed integrity")
        changed, count = re.subn(r"(?m)^  integrity [^\n]+$", "  integrity " + wrong, leaf)
        require(count == 1, "Wrong number of integrity fields")
        return seed.replace(leaf, changed, 1)
    return seed


def isolated_env(case: Path) -> dict[str, str]:
    # Construct from constants; deliberately never copy os.environ.
    return {
        "PATH": str(NODE.parent) + ":/usr/bin:/bin",
        "HOME": str(case / "home"), "TMPDIR": str(case / "tmp"),
        "XDG_CACHE_HOME": str(case / "xdg-cache"), "XDG_CONFIG_HOME": str(case / "xdg-config"),
        "XDG_DATA_HOME": str(case / "xdg-data"),
        "YARN_CACHE_FOLDER": str(case / "cache"), "YARN_GLOBAL_FOLDER": str(case / "global"),
        "npm_config_userconfig": str(case / "empty.npmrc"),
        "YARN_IGNORE_PATH": "1", "DISABLE_V8_COMPILE_CACHE": "1",
        "YARN_DISABLE_SELF_UPDATE_CHECK": "true", "CI": "1", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
    }


def validate_registry(base: str) -> None:
    parsed = urlsplit(base)
    require(parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port is not None
            and 1 <= parsed.port <= 65535,
            "Registry must be explicit IPv4 loopback")
    require(parsed.username is None and parsed.password is None and parsed.path == "/registry"
            and not parsed.query and not parsed.fragment, "Invalid synthetic registry URL")
    require(base == "http://127.0.0.1:" + str(parsed.port) + "/registry", "Noncanonical registry URL")


def yarn_argv(case: Path, registry: str, *, frozen: bool, scripts: bool) -> list[str]:
    validate_registry(registry)
    result = [str(NODE), str(YARN), "install", "--json", "--non-interactive", "--no-progress",
              "--no-default-rc", "--use-yarnrc", str(case / "fixture.yarnrc"),
              "--registry", registry, "--cache-folder", str(case / "cache"),
              "--global-folder", str(case / "global"), "--modules-folder", str(case / "node_modules"),
              "--link-folder", str(case / "links"),
              "--network-concurrency", "1", "--network-timeout", "5000",
              "--mutex", "file:" + str(case / "yarn-mutex")]
    if frozen:
        result.append("--frozen-lockfile")
    if not scripts:
        result.append("--ignore-scripts")
    return result


def validate_execution(argv: list[str], cwd: Path, env: dict[str, str]) -> None:
    no_symlinks(cwd)
    require(env == isolated_env(cwd), "Only the constant isolated environment is permitted")
    if argv in ([str(NODE), "--version"], [str(NODE), str(YARN), "--no-default-rc", "--version"]):
        return
    require(argv.count("--registry") == 1, "Only exact synthetic install/version commands are permitted")
    index = argv.index("--registry")
    require(index + 1 < len(argv), "Missing synthetic registry")
    registry = argv[index + 1]
    require(any(argv == yarn_argv(cwd, registry, frozen=frozen, scripts=scripts)
                for frozen in (False, True) for scripts in (False, True)),
            "Only exact synthetic install/version commands are permitted")


class Registry:
    """Only exact self-authored routes; no proxy, forwarding or file serving."""
    def __init__(self):
        self.lock = threading.Lock()
        self.active_case = "not-started"
        self.changed = False
        self.requests: list[dict] = []
        self.packages = {(name, version): tarball(package_files(name, version))
                         for name, version in [(PARENT, "1.0.0"), (PARENT, "2.0.0"), (LEAF, "1.0.0")]}
        self.changed_leaf = tarball(package_files(LEAF, "1.0.0", changed=True))
        self.http: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.base = ""

    def metadata(self, name: str) -> bytes:
        require(name in {PARENT, LEAF}, "Unknown metadata route")
        versions = {}
        for (package, version), data in self.packages.items():
            if package != name:
                continue
            manifest = json.loads(package_files(package, version)["package.json"])
            manifest["dist"] = {"tarball": self.url(package, version), "shasum": digest(data, "sha1"),
                                "integrity": sri(data)}
            versions[version] = manifest
        return json_bytes({"name": name, "dist-tags": {"latest": max(versions)}, "versions": versions})

    def url(self, name: str, version: str) -> str:
        require((name, version) in self.packages, "Unknown synthetic tarball")
        return self.base + "/" + name + "/-/" + name + "-" + version + ".tgz"

    def response(self, path: str, method: str, host: str, auth: bool, client: str) -> tuple[int, bytes, str]:
        if client != "127.0.0.1" or host != urlsplit(self.base).netloc or auth or method != "GET":
            return 403, b"fixture request rejected\n", "text/plain"
        if path in {"/registry/" + PARENT, "/registry/" + LEAF}:
            return 200, self.metadata(path.rsplit("/", 1)[1]), "application/json"
        for (name, version), data in self.packages.items():
            if path == urlsplit(self.url(name, version)).path:
                if self.changed and name == LEAF:
                    data = self.changed_leaf
                return 200, data, "application/octet-stream"
        return 404, b"unknown synthetic route\n", "text/plain"

    def expected_responses(self) -> dict[str, str]:
        paths = ["/registry/" + name for name in (PARENT, LEAF)]
        paths += [urlsplit(self.url(name, version)).path for name, version in self.packages]
        host = urlsplit(self.base).netloc
        return {path: digest(self.response(path, "GET", host, False, "127.0.0.1")[1]) for path in paths}

    def start(self) -> None:
        registry = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                pass

            def serve(self):
                auth_present = "Authorization" in self.headers or "Proxy-Authorization" in self.headers
                with registry.lock:
                    code, body, content_type = registry.response(
                        self.path, self.command, self.headers.get("Host", ""),
                        auth_present, self.client_address[0])
                    record = {"case": registry.active_case, "method": self.command, "path": self.path,
                              "status": code, "response_bytes": len(body), "response_sha256": digest(body),
                              "auth_header_present": auth_present,
                              "host_allowed": self.headers.get("Host", "") == urlsplit(registry.base).netloc,
                              "client_allowed": self.client_address[0] == "127.0.0.1",
                              "started_utc": utc(), "write_complete": False}
                    registry.requests.append(record)
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                try:
                    self.wfile.write(body)
                    self.wfile.flush()
                    record["write_complete"] = True
                except (BrokenPipeError, ConnectionResetError):
                    pass

            do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = do_PATCH = do_CONNECT = do_TRACE = serve

        self.http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.http.daemon_threads = True
        self.base = "http://127.0.0.1:" + str(self.http.server_port) + "/registry"
        self.thread = threading.Thread(target=self.http.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def close(self) -> None:
        if self.http:
            self.http.shutdown()
            self.http.server_close()
        if self.thread:
            self.thread.join(timeout=2)

    def select(self, case: str) -> None:
        with self.lock:
            self.active_case = case
            self.changed = case == "YF005-changed-tarball"

    def records(self, case: str) -> list[dict]:
        with self.lock:
            return [dict(r) for r in self.requests if r["case"] == case]


def group_exists(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def terminate_group(process: subprocess.Popen) -> dict:
    """Terminate this runner's new-session group, including a departed leader's children."""
    record = {"signals": [], "leader_reaped": False, "group_gone": False}
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
            record["signals"].append(signal.Signals(sig).name)
        except ProcessLookupError:
            break
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            continue
        if not group_exists(process.pid):
            break
    try:
        process.wait(timeout=2)
        record["leader_reaped"] = True
    except subprocess.TimeoutExpired:
        pass
    record["group_gone"] = not group_exists(process.pid)
    return record


def run_process(argv: list[str], cwd: Path, env: dict[str, str], logs: Path, budget: Budget) -> dict:
    validate_execution(argv, cwd, env)
    no_symlinks(logs)
    started = time.monotonic()
    record = {"argv": argv, "cwd": str(cwd), "started_utc": utc(), "environment_policy": "constant-allowlist-no-inheritance",
              "environment_keys": sorted(env), "free_bytes_before": free_bytes(cwd), "reason": None,
              "exit_code": None, "pid": None, "timeout_seconds": budget.per_process,
              "cleanup": None, "runner_error": None}
    process = None
    with (logs / "stdout.log").open("xb") as stdout, (logs / "stderr.log").open("xb") as stderr:
        reason = budget.reason()
        if reason:
            record["reason"] = reason + "-before-start"
        else:
            try:
                process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                record["pid"] = process.pid
                while process.poll() is None:
                    reason = budget.reason()
                    if not reason and time.monotonic() - started > budget.per_process:
                        reason = "process-timeout"
                    if not reason and (os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > MAX_LOG_BYTES):
                        reason = "log-size-limit"
                    if reason:
                        record["reason"] = reason
                        break
                    time.sleep(0.05)
            except (KeyboardInterrupt, InterruptedError):
                record["reason"] = "interrupted"
            except Exception as exc:
                record["reason"] = "process-start-failure" if process is None else "runner-error"
                record["runner_error"] = type(exc).__name__ + ": " + str(exc)
            finally:
                if process:
                    if process.poll() is None or group_exists(process.pid):
                        record["reason"] = record["reason"] or "child-group-survived-leader"
                        record["cleanup"] = terminate_group(process)
                    record["exit_code"] = process.returncode
    record.update(ended_utc=utc(), elapsed_seconds=round(time.monotonic() - started, 4),
                  free_bytes_after=free_bytes(cwd), reason=record["reason"] or "completed",
                  stdout=snapshot(logs / "stdout.log"), stderr=snapshot(logs / "stderr.log"))
    write_new(logs / "process.json", json_bytes(record))
    return record


def error_messages(logs: Path) -> list[str]:
    errors = []
    for name in ("stdout.log", "stderr.log"):
        for line in (logs / name).read_text(errors="strict").splitlines():
            if not line.startswith("{"):
                continue  # Node deprecation warnings are retained, not used to classify a rejection.
            value = json.loads(line)
            require(isinstance(value, dict) and isinstance(value.get("type"), str), "Unknown JSON reporter record")
            if value["type"] == "error":
                require(isinstance(value.get("data"), str), "Unknown error payload")
                errors.append(value["data"])
    return errors


def integrity_error_matches(message: str, url: str, actual: bytes) -> bool:
    # Exactly one known message, with only Yarn's source-confirmed URL prefix allowed.
    if message.startswith(url + ": "):
        message = message[len(url) + 2:]
    pattern = (r'^Integrity check failed for ' + re.escape(json.dumps(LEAF))
               + r' \(computed integrity doesn\x27t match our records, got ("[^"\\]*")\)$')
    match = re.fullmatch(pattern, message)
    if not match:
        return False
    tokens = json.loads(match.group(1)).split(" ")
    known = {sri(actual, "sha1"), sri(actual, "sha512")}
    return bool(tokens) and len(tokens) == len(set(tokens)) and set(tokens) <= known and sri(actual) in tokens


def installed_graph(case: Path) -> dict:
    result = {}
    for name in (PARENT, LEAF):
        directory = case / "node_modules" / name
        package = directory / "package.json"
        no_symlinks(package)
        if not package.exists():
            result[name] = {"exists": False}
            continue
        value = json.loads(package.read_text())
        files = {p.name: snapshot(p) for p in sorted(directory.iterdir()) if p.is_file() and p.name in package_files(name, value["version"])}
        unexpected = sorted(p.name for p in directory.iterdir()
                            if p.name not in package_files(name, value["version"])
                            and not (name == LEAF and p.name == LEAF_MARKER))
        result[name] = {"exists": True, "name": value.get("name"), "version": value.get("version"),
                        "files": files, "unexpected_entries": unexpected}
    return result


def graph_matches(graph: dict) -> bool:
    for name in (PARENT, LEAF):
        current = graph.get(name, {})
        if current.get("name") != name or current.get("version") != "1.0.0":
            return False
        if current.get("unexpected_entries"):
            return False
        expected = package_files(name, "1.0.0")
        if set(current.get("files", {})) != set(expected):
            return False
        if any(current["files"][file]["sha256"] != digest(data) for file, data in expected.items()):
            return False
    return True


def classify(case: str, process: dict, errors: list[str], *, lock_before: dict, lock_after: dict,
             inputs_unchanged: bool, requests: list[dict], graph_ok: bool, markers_ok: bool,
             leaf_url: str, leaf_bytes: bytes, known_responses: dict[str, str]) -> dict:
    require(case in CASES or case == "bootstrap", "Unknown classification case")
    result = {"case": case, "observed_category": "unexpected-or-inconclusive", "observation_matched": False,
              "security_enforcement_pass": False, "counterexample": False,
              "expected_category": EXPECTED_CATEGORIES[case],
              "expected_exit_code": 1 if case in {"YF003-direct-drift", "YF004-wrong-sri", "YF005-changed-tarball"} else 0}
    transport_ok = bool(requests) and all(
        r["status"] == 200 and r["write_complete"] and r["method"] == "GET"
        and r["case"] == case and not r["auth_header_present"] and r["host_allowed"] and r["client_allowed"]
        and r["path"] in known_responses and r["response_sha256"] == known_responses[r["path"]]
        for r in requests)
    common = process["reason"] == "completed" and inputs_unchanged and transport_ok and markers_ok
    if not common:
        return result
    if case == "YF003-direct-drift":
        good = (process["exit_code"] == 1 and errors == [FROZEN_ERROR] and lock_before["exists"]
                and lock_before == lock_after and any(r["path"] == "/registry/" + PARENT for r in requests))
        result.update(observation_matched=good, observed_category="frozen-lock-rejection" if good else result["observed_category"])
    elif case in {"YF004-wrong-sri", "YF005-changed-tarball"}:
        served = any(r["path"] == urlsplit(leaf_url).path and r["response_sha256"] == digest(leaf_bytes) for r in requests)
        good = (process["exit_code"] == 1 and len(errors) == 1 and lock_before["exists"] and lock_before == lock_after and served
                and integrity_error_matches(errors[0], leaf_url, leaf_bytes))
        result.update(observation_matched=good, observed_category="tarball-integrity-rejection" if good else result["observed_category"])
    else:
        package_paths = {"/registry/" + name + "/-/" + name + "-1.0.0.tgz" for name in (PARENT, LEAF)}
        good = (process["exit_code"] == 0 and not errors and graph_ok
                and package_paths <= {r["path"] for r in requests})
        if case == "bootstrap":
            good = good and not lock_before["exists"] and lock_after["exists"]
        elif case == "YF002-missing-lock":
            good = good and not lock_before["exists"] and not lock_after["exists"]
        elif case == "YF006-incomplete-transitive":
            good = good and lock_before["exists"] and lock_before == lock_after
        else:
            good = good and lock_before["exists"] and lock_before == lock_after
        result.update(observation_matched=good, observed_category=EXPECTED_CATEGORIES[case] if good else result["observed_category"],
                      counterexample=good and case in {"YF002-missing-lock", "YF006-incomplete-transitive"})
    return result


def verify_pins() -> list[dict]:
    result = []
    for path, expected in PINS.items():
        require(path.is_file() and not path.is_symlink(), "Pinned tool is absent or symlinked")
        actual = digest(path.read_bytes())
        require(actual == expected, "Pinned tool hash mismatch: " + path.name)
        result.append({"path": str(path), "sha256": actual})
    require(json.loads((YARN_HOME / "package.json").read_text())["version"] == "1.22.22", "Yarn version mismatch")
    return result


def source_hashes() -> dict[str, str]:
    return {str(path.relative_to(REPO)): digest(path.read_bytes()) for path in sorted(SOURCE.iterdir())
            if path.is_file() and path.suffix in {".py", ".md"}}


def prepare_case(work: Path, archive: Path, registry: Registry, case: str, seed: str | None) -> tuple[Path, dict[str, str]]:
    require(case in EXPECTED_CATEGORIES, "Unknown fixture directory")
    require((seed is None) == (case == "bootstrap"), "Only bootstrap may omit the seed")
    no_symlinks(work)
    no_symlinks(archive)
    cwd = work / case
    cwd.mkdir()
    archive.mkdir()
    for directory in ("home", "tmp", "cache", "global", "links", "xdg-cache", "xdg-config", "xdg-data"):
        (cwd / directory).mkdir()
    for name, data in root_files("2.0.0" if case == "YF003-direct-drift" else "1.0.0").items():
        write_new(cwd / name, data)
        write_new(archive / "inputs" / name, data)
    rc = ('registry ' + json.dumps(registry.base) + '\ndisable-self-update-check true\nstrict-ssl true\n').encode()
    write_new(cwd / "fixture.yarnrc", rc)
    write_new(cwd / "empty.npmrc", b"")
    write_new(archive / "inputs/fixture.yarnrc", rc)
    write_new(archive / "inputs/empty.npmrc", b"")
    if seed is not None:
        lock = mutate_lock(seed, case)
        if lock is not None:
            write_new(cwd / "yarn.lock", lock.encode())
            write_new(archive / "inputs/yarn.lock", lock.encode())
    return cwd, isolated_env(cwd)


def validate_seed(seed: str, registry: Registry) -> None:
    blocks = lock_blocks(seed)
    require(set(blocks) == {PARENT + "@1.0.0", LEAF + "@1.0.0"}, "Bootstrap seed graph differs")
    for name in (PARENT, LEAF):
        block = blocks[name + "@1.0.0"]
        data = registry.packages[(name, "1.0.0")]
        require(lock_field(block, "version") == "1.0.0", "Seed version mismatch")
        require(lock_field(block, "resolved") == registry.url(name, "1.0.0") + "#" + digest(data, "sha1"), "Seed origin/hash mismatch")
        require(lock_field(block, "integrity") == sri(data), "Seed SRI mismatch")
    require('    ' + LEAF + ' "1.0.0"' in blocks[PARENT + "@1.0.0"], "Seed transitive dependency missing")


def execute_case(run: Path, registry: Registry, budget: Budget, case: str, seed: str | None) -> dict:
    archive = run / "cases" / case
    cwd, env = prepare_case(run / "work", archive, registry, case, seed)
    inputs = {name: snapshot(cwd / name) for name in ("package.json", "root-marker.js", "fixture.yarnrc", "empty.npmrc")}
    before = snapshot(cwd / "yarn.lock")
    scripts = case == "YF008-script-control"
    argv = yarn_argv(cwd, registry.base, frozen=case != "bootstrap", scripts=scripts)
    registry.select(case)
    known_responses = registry.expected_responses()
    write_new(archive / "case-plan.json", json_bytes({
        "case": case, "expected_category": EXPECTED_CATEGORIES[case], "argv": argv,
        "inputs_before": inputs, "lock_before": before, "expected_response_sha256": known_responses,
        "root_marker_before": snapshot(cwd / ROOT_MARKER),
        "dependency_marker_before": snapshot(cwd / "node_modules" / LEAF / LEAF_MARKER),
        "environment_policy": "constant-allowlist-no-inheritance",
        "fresh_directories": {directory: not any((cwd / directory).iterdir()) for directory in
            ("home", "tmp", "cache", "global", "links", "xdg-cache", "xdg-config", "xdg-data")},
        "node_modules_absent_before": not (cwd / "node_modules").exists(),
    }))
    process = run_process(argv, cwd, env, archive, budget)
    after = snapshot(cwd / "yarn.lock")
    after_inputs = {name: snapshot(cwd / name) for name in inputs}
    if after["exists"]:
        write_new(archive / "outputs/yarn.lock", (cwd / "yarn.lock").read_bytes())
    write_new(archive / "outputs/package.json", (cwd / "package.json").read_bytes())
    markers = {"root": snapshot(cwd / ROOT_MARKER), "dependency": snapshot(cwd / "node_modules" / LEAF / LEAF_MARKER)}
    marker_data = b"self-authored harmless fixture marker\n"
    markers_ok = all(value["exists"] == scripts and (not scripts or value["sha256"] == digest(marker_data)) for value in markers.values())
    for key, path in [("root", cwd / ROOT_MARKER), ("dependency", cwd / "node_modules" / LEAF / LEAF_MARKER)]:
        if markers[key]["exists"]:
            write_new(archive / "outputs" / (key + "-marker.txt"), path.read_bytes())
    graph = installed_graph(cwd)
    errors = error_messages(archive)
    requests = registry.records(case)
    actual_leaf = registry.changed_leaf if case == "YF005-changed-tarball" else registry.packages[(LEAF, "1.0.0")]
    classification = classify(case, process, errors, lock_before=before, lock_after=after,
                              inputs_unchanged=inputs == after_inputs, requests=requests,
                              graph_ok=graph_matches(graph), markers_ok=markers_ok,
                              leaf_url=registry.url(LEAF, "1.0.0"), leaf_bytes=actual_leaf,
                              known_responses=known_responses)
    before_blocks = lock_blocks((archive / "inputs/yarn.lock").read_text()) if before["exists"] else {}
    result = {"case": case, "layer": "raw-yarn-only", "bootstrap": case == "bootstrap", "frozen": case != "bootstrap",
              "scripts_enabled": scripts, "fresh_home_cache_tmp_modules": True, "process": process,
              "inputs_before": inputs, "inputs_after": after_inputs, "lock_before": before, "lock_after": after,
              "markers": markers, "installed_graph": graph, "actual_errors": errors,
              "server_requests": requests, "expected_response_sha256": known_responses, "classification": classification,
              "served_leaf_tarball_expectation": {"sha256": digest(actual_leaf), "sha512_sri": sri(actual_leaf)},
              "lock_leaf_integrity_before": lock_field(before_blocks[LEAF + "@1.0.0"], "integrity") if LEAF + "@1.0.0" in before_blocks else None,
              "seed_leaf_integrity": sri(registry.packages[(LEAF, "1.0.0")]),
              "review_source_prediction": "raw acceptance is a counterexample, not enforcement" if case in {"YF002-missing-lock", "YF006-incomplete-transitive"} else None}
    write_new(archive / "receipt.json", json_bytes(result))
    return result


def reserve_run(run_id: str) -> Path:
    require(re.fullmatch(r"raw[0-9]{3}", run_id) is not None, "Run ID must be rawNNN")
    no_symlinks(EVIDENCE)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    run = EVIDENCE / run_id
    require(not run.exists() and not run.is_symlink(), "Run directory exists; never overwrite a receipt")
    run.mkdir()
    return run


def run_suite(run_id: str, total: int, per_process: int, reserve_mib: int) -> tuple[Path, dict]:
    validate_limits(total, per_process, reserve_mib)
    require(os.name == "posix", "Only the inspected POSIX process-group runner is supported")
    require(free_bytes(REPO) >= reserve_mib * 1024 * 1024, "Disk reserve unavailable before reservation")
    tools_before = verify_pins()
    inputs_before = source_hashes()
    run = reserve_run(run_id)
    budget = Budget(run, total, per_process, reserve_mib)
    summary = {"schema_version": 1, "run_id": run_id, "layer": "raw-yarn-only", "started_utc": utc(),
               "limits": {"total_timeout_seconds": total, "per_process_timeout_seconds": per_process, "reserve_mib": reserve_mib},
               "tool_inputs_before": tools_before, "harness_inputs_before": inputs_before,
               "kernel_or_egress_sandbox": False, "egress_guarantee": False,
               "network_scope": "only configured synthetic IPv4 loopback registry; no forwarding; no inherited config/auth/proxy",
               "no_gradle_or_live_policy_changes": True, "security_enforcement_complete": False,
               "planned_cases": ["bootstrap", *CASES], "attempted_cases": [], "cases": [], "harness_error": None}
    registry = Registry()
    write_new(run / "reservation.json", json_bytes(summary))
    try:
        (run / "work").mkdir()
        (run / "cases").mkdir()
        for path in sorted(SOURCE.iterdir()):
            if path.is_file() and path.suffix in {".py", ".md"}:
                write_new(run / "harness-inputs" / path.name, path.read_bytes())
        registry.start()
        summary["registry"] = registry.base
        for (name, version), data in registry.packages.items():
            write_new(run / "registry" / (name + "-" + version + ".tgz"), data)
        write_new(run / "registry" / (LEAF + "-1.0.0-changed.tgz"), registry.changed_leaf)
        for name in (PARENT, LEAF):
            write_new(run / "registry" / (name + ".json"), registry.metadata(name))
        # Node/Yarn version observations use a fresh task-owned environment too.
        version_root = run / "work/versions"
        version_root.mkdir()
        for value in ("home", "tmp", "cache", "global", "links", "xdg-cache", "xdg-config", "xdg-data"):
            (version_root / value).mkdir()
        write_new(version_root / "empty.npmrc", b"")
        summary["version_commands"] = []
        for name, argv, expected in [("node", [str(NODE), "--version"], "v24.16.0"),
                                     ("yarn", [str(NODE), str(YARN), "--no-default-rc", "--version"], "1.22.22")]:
            logs = run / "versions" / name
            logs.mkdir(parents=True)
            result = run_process(argv, version_root, isolated_env(version_root), logs, budget)
            result["observed_stdout"] = (logs / "stdout.log").read_text().strip()
            summary["version_commands"].append(result)
            require(result["exit_code"] == 0 and result["reason"] == "completed" and result["observed_stdout"] == expected,
                    "Pinned runtime version observation failed")
        seed = None
        for case in ["bootstrap", *CASES]:
            require(budget.reason() is None, "Bound reached before " + case)
            summary["attempted_cases"].append(case)
            result = execute_case(run, registry, budget, case, seed)
            summary["cases"].append({"case": case, "receipt": "cases/" + case + "/receipt.json", **result["classification"]})
            require(result["classification"]["observation_matched"], "Unexpected/inconclusive outcome: " + case)
            if case == "bootstrap":
                seed = (run / "cases/bootstrap/outputs/yarn.lock").read_text()
                validate_seed(seed, registry)
                write_new(run / "seed/yarn.lock", seed.encode())
        # The suppressed-script observation is meaningful only with the real control.
        require(any(c["case"] == "YF008-script-control" and c["observation_matched"] for c in summary["cases"]), "Script control absent")
    except (Exception, KeyboardInterrupt) as exc:
        summary["harness_error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        registry.close()
        write_new(run / "server-requests.json", json_bytes(registry.requests))
        try:
            summary["tool_inputs_after"] = verify_pins()
            summary["tool_inputs_unchanged"] = tools_before == summary["tool_inputs_after"]
        except Exception as exc:
            summary["tool_inputs_unchanged"] = False
            summary["tool_verification_error"] = type(exc).__name__ + ": " + str(exc)
        summary["harness_inputs_after"] = source_hashes()
        summary["harness_inputs_unchanged"] = inputs_before == summary["harness_inputs_after"]
        summary["ended_utc"] = utc()
        summary["elapsed_seconds"] = round(time.monotonic() - budget.started, 4)
        summary["free_bytes_after"] = free_bytes(run)
        summary["unexecuted_cases"] = [c for c in summary["planned_cases"] if c not in summary["attempted_cases"]]
        summary["incomplete_case_receipts"] = [c for c in summary["attempted_cases"] if c not in {v["case"] for v in summary["cases"]}]
        summary["counterexamples"] = [c["case"] for c in summary["cases"] if c["counterexample"]]
        summary["all_selected_observations_matched"] = (not summary["harness_error"] and not summary["unexecuted_cases"]
            and not summary["incomplete_case_receipts"]
            and summary["tool_inputs_unchanged"] and summary["harness_inputs_unchanged"])
        summary["exit_code"] = 0 if summary["all_selected_observations_matched"] else 1
        summary["archived_file_hashes"] = {str(p.relative_to(run)): digest(p.read_bytes())
            for p in sorted(run.rglob("*")) if p.is_file() and "work" not in p.relative_to(run).parts}
        write_new(run / "summary.json", json_bytes(summary))
    return run, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--total-timeout", type=int, default=300)
    parser.add_argument("--per-process-timeout", type=int, default=30)
    parser.add_argument("--reserve-mib", type=int, default=8192)
    args = parser.parse_args()
    def interrupted(_signum, _frame):
        raise InterruptedError("Runner interrupted")
    signal.signal(signal.SIGTERM, interrupted)
    run, result = run_suite(args.run_id, args.total_timeout, args.per_process_timeout, args.reserve_mib)
    print(json.dumps({"receipt": str(run / "summary.json"), "exit_code": result["exit_code"],
                      "elapsed_seconds": result["elapsed_seconds"], "counterexamples": result["counterexamples"],
                      "harness_error": result["harness_error"], "unexecuted_cases": result["unexecuted_cases"]}, indent=2))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
