"""Passive, Linux-only witness for a separately scheduled six-invocation fixture.

This helper NEVER starts/stops Gradle or inspects arbitrary JVMs. Its exact
fixture-suite sibling must already be running under the same parent. Only that
suite's recorded clients and their verified Java daemon children are eligible
for one bounded jcmd request each. Raw properties/environment stay in bounded
memory, never reports/stdout. A missed/exited/reused process is not a pass.

jcmd is a diagnostic attach, not an OS sandbox: HotSpot may create its attach
socket. It does not establish actual compiler/native cache consumption. The
existing frozen driver, not this passive witness, owns Gradle's time/cleanup
bound. See runtime-witness.md before the lead schedules an actual invocation.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from itertools import islice
import json
import os
from pathlib import Path
import re
import select
import selectors
import subprocess
import sys
import time

import integrity as driver
import integrity_model as m

CHECKPOINT_SHA256 = "42df397c9ddc0a7c6419cb1d109a680e2204dba54e78250b3a4e6b8f49fd6f46"
NEGATIVE_CASES = ("missing-host-lock", "missing-configuration-lock", "added-dependency", "removed-dependency")
CASE_NAMES = ("bootstrap", "baseline-check", *NEGATIVE_CASES)
FORBIDDEN_ENVIRONMENT = ("JAVA_OPTS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "GRADLE_OPTS")
DAEMON_MAIN = "org.gradle.launcher.daemon.bootstrap.GradleDaemon"
MAX_PROC = 256 * 1024
MAX_DIAGNOSTIC = 128 * 1024
MAX_RECEIPT = 1024 * 1024
JDK_VERSION = re.compile(r"17(?:\.[0-9]+)+(?:[+\-][0-9A-Za-z.+_\-]+)?\Z")
TOOL_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = TOOL_ROOT.parent.parent
MAX_REASON_COUNT = 1024
VALIDATION_STAGES = frozenset({
    "context", "client-observation", "daemon-children", "daemon-candidate",
    "daemon-observation", "runtime-binding",
})
# An explicit enum, never arbitrary exception text, paths or dynamic keys.
# Counter events are polls/validation outcomes, NOT distinct processes/attaches.
VALIDATION_REASON_CODES = frozenset({
    "ambiguous-gradle-daemon", "checkpoint006-changed", "checkpoint006-input-count",
    "client-ancestry-mismatch", "client-children-identity-mismatch", "client-cwd-mismatch",
    "client-identity-changed", "client-thread-limit", "continued-selected-property",
    "daemon-ancestry-mismatch", "diagnostic-nonzero", "diagnostic-output-limit",
    "diagnostic-pid-header-mismatch", "diagnostic-subprocess-error", "diagnostic-timeout",
    "diagnostic-timeout-limit", "duplicate-or-continued-selected-property", "expected-directory",
    "fixture-inside-git", "foreign-fixture-marker", "foreign-process-user", "frozen006-input-changed",
    "gradle-client-command-mismatch", "gradle-daemon-agent-mismatch", "gradle-daemon-classpath-mismatch",
    "gradle-daemon-command-mismatch", "gradle-daemon-duplicate-option", "gradle-daemon-option-mismatch",
    "gradle-daemon-private-option-mismatch", "gradle-daemon-unknown-option", "inherited-jvm-override",
    "input-disappeared", "input-os-error", "input-permission-denied", "input-value-invalid",
    "integrity-validation-failed", "invalid-child-list", "invalid-client-thread", "invalid-diagnostic-stage",
    "invalid-environment-record", "invalid-java-role", "invalid-launch-receipt", "invalid-nul-record",
    "invalid-process-id", "invalid-process-identity", "invalid-process-stat", "invalid-property-escape",
    "java-command-mismatch", "java-cwd-outside-candidate", "java-executable-mismatch", "java-identity-changed",
    "java-identity-changed-after-attach", "java-identity-changed-before-attach", "jdk-path-mismatch",
    "jvm-environment-mismatch", "missing-path", "no-eligible-daemon-at-poll", "no-owned-child-at-poll",
    "noncanonical-path", "nonfinite-json", "nonobject-receipt", "observed-jdk-not17",
    "observer-deadline-before-attach", "observer-input-changed", "observer-timeout-limit",
    "other-validation-failure", "pidfd-unavailable", "private-directory-missing",
    "private-environment-mismatch", "private-jvm-property-mismatch", "proc-input-limit", "process-not-live",
    "required-field-missing", "selected-property-missing", "suite-checkout-mismatch", "suite-command-mismatch",
    "suite-identity-changed", "suite-jdk-mismatch", "suite-not-owned-sibling", "suite-python-mismatch",
    "symlink-path", "unsafe-observer-output", "unsafe-option-path", "unsupported-observer-host",
    "unsupported-proc-read",
})


class WitnessError(ValueError):
    """Only fixed, non-sensitive reason codes are emitted."""


def require(condition: object, code: str) -> None:
    if not condition:
        raise WitnessError(code)


def failure_reason(failure: BaseException) -> str:
    """Return one enum value without formatting any exception or attached data."""
    if type(failure) is WitnessError:
        if (len(failure.args) == 1 and type(failure.args[0]) is str and
                failure.args[0] in VALIDATION_REASON_CODES):
            return failure.args[0]
        return "other-validation-failure"
    for kind, code in ((FileNotFoundError, "input-disappeared"), (PermissionError, "input-permission-denied"),
                       (OSError, "input-os-error"), (m.IntegrityError, "integrity-validation-failed"),
                       (KeyError, "required-field-missing"), (ValueError, "input-value-invalid"),
                       (subprocess.SubprocessError, "diagnostic-subprocess-error")):
        if isinstance(failure, kind):
            return code
    return "other-validation-failure"


def record_validation_reason(state: dict, stage: str, code: str) -> str:
    """Fixed stage/code keys and saturated counts; no PID/argument/raw message log."""
    require(type(stage) is str and stage in VALIDATION_STAGES, "invalid-diagnostic-stage")
    code = code if type(code) is str and code in VALIDATION_REASON_CODES else "other-validation-failure"
    counts = state.setdefault("validation_reason_counts", {}).setdefault(stage, {})
    previous = counts.get(code, 0)
    counts[code] = min(MAX_REASON_COUNT, previous + 1)
    if previous >= MAX_REASON_COUNT:
        state["validation_reason_counts_saturated"] = True
    return code


def fixed_arguments(destination: Path, gradle_home: Path) -> list[str]:
    result = ["fixtures", "--destination", str(destination), "--gradle-home", str(gradle_home)]
    for case in NEGATIVE_CASES:
        result.extend(["--case", case])
    return [*result, "--total-timeout", "300", "--timeout", "90", "--reserve-mib", "8192"]


def plain_absolute(path: Path, *, existing: bool = True) -> Path:
    require(path.is_absolute() and path == path.resolve(strict=False), "noncanonical-path")
    require(not path.is_symlink() and not any(parent.is_symlink() for parent in path.parents), "symlink-path")
    require(not any(char in str(path) for char in ('"', "'", "\\")) and
            not any(ord(char) < 32 for char in str(path)), "unsafe-option-path")
    if existing:
        require(path.exists(), "missing-path")
    return path


def checked_json(path: Path) -> dict:
    # Files.write in Gradle may be observed before the small receipt is complete;
    # the polling caller retries reads, never a failed diagnostic attachment.
    plain_absolute(path)
    raw = m.read_regular(path, MAX_RECEIPT)
    value = json.loads(raw, object_pairs_hook=m._unique_object,
                       parse_constant=lambda _: (_ for _ in ()).throw(WitnessError("nonfinite-json")))
    require(isinstance(value, dict), "nonobject-receipt")
    return value


def checkpoint_files() -> dict[str, str]:
    path = TOOL_ROOT / "checkpoint-offline-006.json"
    require(m.file_sha256(path) == CHECKPOINT_SHA256, "checkpoint006-changed")
    expected = checked_json(path)["input_files_sha256"]
    require(len(expected) == 6, "checkpoint006-input-count")
    for name, digest in expected.items():
        require(m.file_sha256(m.confined(SOURCE_ROOT, name, must_exist=True)) == digest, "frozen006-input-changed")
    return dict(expected)


def observer_files() -> dict[str, str]:
    return {name: m.file_sha256(TOOL_ROOT / name)
            for name in ("runtime_witness.py", "test_runtime_witness.py", "runtime-witness.md")}


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    parent: int
    group: int
    session: int
    start_ticks: int

    def public(self) -> dict:
        return {"pid": self.pid, "parent_pid": self.parent, "process_group": self.group,
                "session": self.session, "start_ticks": self.start_ticks}


def parse_stat(raw: bytes, pid: int) -> ProcessIdentity:
    value = raw.decode("utf-8", "strict")
    prefix, separator, tail = value.rpartition(") ")
    fields = tail.split()
    require(separator and prefix.split(" (", 1)[0] == str(pid) and len(fields) >= 20, "invalid-process-stat")
    require(fields[0] not in {"Z", "X", "x"}, "process-not-live")
    try:
        result = ProcessIdentity(pid, int(fields[1]), int(fields[2]), int(fields[3]), int(fields[19]))
    except ValueError as failure:
        raise WitnessError("invalid-process-stat") from failure
    require(result.start_ticks > 0 and min(result.parent, result.group, result.session) > 0, "invalid-process-identity")
    return result


def proc_bytes(pid: int, name: str, limit: int = MAX_PROC) -> bytes:
    require(type(pid) is int and pid > 1, "invalid-process-id")
    require(name in {"stat", "cmdline", "environ"} or re.fullmatch(r"task/[1-9][0-9]*/children", name), "unsupported-proc-read")
    with (Path("/proc") / str(pid) / name).open("rb") as stream:
        result = stream.read(limit + 1)
    require(len(result) <= limit, "proc-input-limit")
    return result


def identity(pid: int) -> ProcessIdentity:
    require((Path("/proc") / str(pid)).stat().st_uid == os.getuid(), "foreign-process-user")
    return parse_stat(proc_bytes(pid, "stat", 8192), pid)


def owned_children(client: ProcessIdentity) -> list[int]:
    # Linux children lists are PER THREAD. Gradle can fork from an executor
    # thread, so consulting only task/<process-pid>/children can miss the daemon.
    require(identity(client.pid) == client, "client-identity-changed")
    children = set()
    threads = list(islice((Path("/proc") / str(client.pid) / "task").iterdir(), 257))
    require(len(threads) <= 256, "client-thread-limit")
    for thread in threads:
        require(re.fullmatch(r"[1-9][0-9]*", thread.name), "invalid-client-thread")
        try:
            values = proc_bytes(client.pid, f"task/{thread.name}/children", 4096).decode("ascii").split()
        except FileNotFoundError:
            continue  # This owned thread can finish between enumeration/read.
        require(len(values) <= 16 and all(re.fullmatch(r"[1-9][0-9]*", value) for value in values), "invalid-child-list")
        children.update(map(int, values))
    require(len(children) <= 16 and identity(client.pid) == client, "client-children-identity-mismatch")
    return sorted(children)


def fields(raw: bytes) -> list[str]:
    require(raw and raw.endswith(b"\0"), "invalid-nul-record")
    return raw[:-1].decode("utf-8", "strict").split("\0")


def environment(raw: bytes) -> dict[str, str]:
    result = {}
    for item in fields(raw):
        key, separator, value = item.partition("=")
        require(separator and key and key not in result, "invalid-environment-record")
        result[key] = value
    return result


def private_values(workspace: Path) -> tuple[dict[str, str], dict[str, str], str]:
    properties = {key: str(workspace / relative) for key, relative in m.JVM_PRIVATE_PATHS.items()}
    environ = {key: str(workspace / relative) for key, relative in m.ENV_PRIVATE_PATHS.items()}
    options = " ".join(f'-D{key}="{value}"' for key, value in properties.items())
    return properties, environ, options


def check_environment(actual: dict[str, str], workspace: Path, jdk_home: Path) -> None:
    _, expected, options = private_values(workspace)
    require(all(actual.get(key) == value for key, value in expected.items()), "private-environment-mismatch")
    require(actual.get("JAVA_TOOL_OPTIONS") == options and actual.get("JAVA_HOME") == str(jdk_home), "jvm-environment-mismatch")
    require(not any(key in actual for key in FORBIDDEN_ENVIRONMENT), "inherited-jvm-override")
    require(actual.get("PATH", "").startswith(str(jdk_home / "bin") + os.pathsep), "jdk-path-mismatch")
    for relative in set(m.JVM_PRIVATE_PATHS.values()) | set(m.ENV_PRIVATE_PATHS.values()):
        require(m.confined(workspace, relative, must_exist=True).is_dir(), "private-directory-missing")


def check_suite(pid: int, destination: Path, gradle_home: Path, jdk_home: Path) -> ProcessIdentity:
    first = identity(pid)
    require(pid not in {os.getpid(), os.getppid()} and first.parent == os.getppid(), "suite-not-owned-sibling")
    require(Path(os.readlink(f"/proc/{pid}/exe")) == Path(sys.executable).resolve(), "suite-python-mismatch")
    cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
    require(cwd == SOURCE_ROOT, "suite-checkout-mismatch")
    arguments = fields(proc_bytes(pid, "cmdline"))
    require(len(arguments) >= 3 and (cwd / arguments[1]).resolve() == TOOL_ROOT / "integrity.py" and
            arguments[2:] == fixed_arguments(destination, gradle_home), "suite-command-mismatch")
    require(environment(proc_bytes(pid, "environ")).get("JAVA_HOME") == str(jdk_home), "suite-jdk-mismatch")
    require(identity(pid) == first, "suite-identity-changed")
    return first


def client_prefix(jdk_home: Path, gradle_home: Path) -> list[str]:
    # Exact installed Linux bin/gradle DEFAULT_JVM_OPTS and set -- sequence.
    # A matching '-jar' later in APPLICATION arguments is not a JVM entrypoint.
    return [str(jdk_home / "bin/java"), "-Xmx64m", "-Xms64m",
            f"-javaagent:{gradle_home}/lib/agents/gradle-instrumentation-agent-9.7.1.jar",
            "-Dorg.gradle.appname=gradle", "-jar", str(gradle_home / "lib/gradle-gradle-cli-main-9.7.1.jar")]


def daemon_entrypoint(arguments: list[str], gradle_home: Path, workspace: Path) -> None:
    """Consume EVERY JVM argument before the one expected main class.

    Intentionally limited to this plugin-free Gradle9.7.1/JDK17 fixture.
    Alternate launch modes, argfiles, unknown options and repeated/overridden
    classpaths fail, even when a later suffix resembles a Gradle invocation.
    """
    require(3 <= len(arguments) <= 256 and all(isinstance(arg, str) and len(arg) <= 8192 and
            not any(ord(char) < 32 for char in arg) for arg in arguments), "gradle-daemon-command-mismatch")
    seen = set()
    classpath_seen = False
    agent_seen = False
    expected_agent = f"-javaagent:{gradle_home}/lib/agents/gradle-instrumentation-agent-9.7.1.jar"
    expected_properties, _, _ = private_values(workspace)
    index = 1
    while index < len(arguments):
        token = arguments[index]
        if token == DAEMON_MAIN:
            require(index == len(arguments) - 2 and arguments[index + 1] == "9.7.1" and classpath_seen and agent_seen,
                    "gradle-daemon-command-mismatch")
            return
        if token == "-cp":
            require(not classpath_seen and index + 1 < len(arguments) and
                    arguments[index + 1] == str(gradle_home / "lib/gradle-daemon-main-9.7.1.jar"),
                    "gradle-daemon-classpath-mismatch")
            classpath_seen = True
            index += 2
            continue
        if token == expected_agent:
            require(not agent_seen, "gradle-daemon-agent-mismatch")
            agent_seen = True
            index += 1
            continue
        option_key = token
        if token.startswith("-D"):
            key, _, value = token[2:].partition("=")
            option_key = "-D" + key
            if key in expected_properties:
                require(value == expected_properties[key], "gradle-daemon-private-option-mismatch")
            elif key == "file.encoding":
                require(value in {"UTF-8", "UTF8"}, "gradle-daemon-option-mismatch")
            elif key in {"user.language", "user.country", "user.variant"}:
                require(re.fullmatch(r"[A-Za-z0-9_\-]{0,32}", value), "gradle-daemon-option-mismatch")
            else:
                raise WitnessError("gradle-daemon-unknown-option")
        elif re.fullmatch(r"-Xm[sx][1-9][0-9]{0,5}[kKmMgG]?", token):
            option_key = token[:4]
        elif re.fullmatch(r"-XX:MaxMetaspaceSize=[1-9][0-9]{0,5}[kKmMgG]?", token):
            option_key = "-XX:MaxMetaspaceSize"
        elif token in {"-server", "-ea", "-XX:+HeapDumpOnOutOfMemoryError", "--enable-native-access=ALL-UNNAMED"}:
            pass
        elif re.fullmatch(r"--add-(?:opens|exports)=[A-Za-z0-9_.]+/[A-Za-z0-9_.]+=ALL-UNNAMED", token):
            pass
        else:
            raise WitnessError("gradle-daemon-command-mismatch")
        require(option_key not in seen, "gradle-daemon-duplicate-option")
        seen.add(option_key)
        index += 1
    raise WitnessError("gradle-daemon-command-mismatch")


def check_java(pid: int, *, role: str, workspace: Path, marker: dict, mode: str,
               jdk_home: Path, gradle_home: Path, suite: ProcessIdentity,
               client: ProcessIdentity | None) -> ProcessIdentity:
    first = identity(pid)
    require(identity(suite.pid) == suite, "suite-identity-changed")
    require(Path(os.readlink(f"/proc/{pid}/exe")) == jdk_home / "bin/java", "java-executable-mismatch")
    cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
    require(cwd.is_relative_to(workspace), "java-cwd-outside-candidate")
    arguments = fields(proc_bytes(pid, "cmdline"))
    require(arguments[0] == str(jdk_home / "bin/java"), "java-command-mismatch")
    if role == "client":
        require(first.parent == suite.pid and first.group == pid == first.session and first.start_ticks >= suite.start_ticks,
                "client-ancestry-mismatch")
        require(cwd == workspace, "client-cwd-mismatch")
        expected = driver.build_command(workspace, marker, entry_root=".", run_id=mode, mode=mode, gradle_home=gradle_home)[1:]
        require(arguments == [*client_prefix(jdk_home, gradle_home), *expected], "gradle-client-command-mismatch")
    elif role == "daemon":
        require(client is not None and identity(client.pid) == client and pid != client.pid and
                first.parent == client.pid and first.group == client.group and first.session == client.session and
                first.start_ticks >= client.start_ticks, "daemon-ancestry-mismatch")
        daemon_entrypoint(arguments, gradle_home, workspace)
    else:
        raise WitnessError("invalid-java-role")
    check_environment(environment(proc_bytes(pid, "environ")), workspace, jdk_home)
    require(identity(pid) == first, "java-identity-changed")
    return first


def unescape_property(value: str) -> str:
    result = []
    index = 0
    escapes = {"t": "\t", "n": "\n", "r": "\r", "f": "\f"}
    while index < len(value):
        char = value[index]
        index += 1
        if char == "\\":
            require(index < len(value), "continued-selected-property")
            char = value[index]
            index += 1
            if char == "u":
                chunk = value[index:index + 4]
                require(len(chunk) == 4 and re.fullmatch("[0-9a-fA-F]{4}", chunk), "invalid-property-escape")
                char = chr(int(chunk, 16))
                index += 4
            else:
                char = escapes.get(char, char)
        result.append(char)
    return "".join(result)


def selected_properties(raw: bytes, pid: int, workspace: Path) -> dict:
    require(len(raw) <= MAX_DIAGNOSTIC, "diagnostic-output-limit")
    lines = raw.decode("utf-8", "strict").splitlines()
    require(lines and lines[0] == f"{pid}:", "diagnostic-pid-header-mismatch")
    wanted = {*m.JVM_PRIVATE_PATHS, "java.version"}
    values = {}
    continuation = False
    for line in lines[1:]:
        # Never interpret continuation text from an unrelated property as a key.
        skip = continuation
        continuation = (len(line) - len(line.rstrip("\\"))) % 2 == 1
        if skip or not line or line.startswith(("#", "!")):
            continue
        key, separator, value = line.partition("=")
        if separator and key in wanted:
            require(key not in values and not continuation, "duplicate-or-continued-selected-property")
            values[key] = unescape_property(value)
    require(set(values) == wanted, "selected-property-missing")
    expected, _, _ = private_values(workspace)
    matched = {key: values[key] == value for key, value in expected.items()}
    require(all(matched.values()), "private-jvm-property-mismatch")
    require(JDK_VERSION.fullmatch(values["java.version"]), "observed-jdk-not17")
    return {"properties": dict(m.JVM_PRIVATE_PATHS), "property_matches": matched,
            "java_runtime_version": values["java.version"], "selected_values_match": True}


def diagnostic(command: list[str], env: dict[str, str], timeout: float) -> tuple[bytes, dict]:
    """Bounded pipe capture; only this newly launched jcmd may be terminated."""
    require(0 < timeout <= 5, "diagnostic-timeout-limit")
    began = time.monotonic()
    chunks = {"stdout": bytearray(), "stderr": bytearray()}
    reason = None
    process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        with selectors.DefaultSelector() as selector:
            for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            while selector.get_map():
                remaining = timeout - (time.monotonic() - began)
                if remaining <= 0:
                    reason = "diagnostic-timeout"
                    break
                for key, _ in selector.select(min(remaining, 0.05)):
                    block = os.read(key.fileobj.fileno(), 8192)
                    if not block:
                        selector.unregister(key.fileobj)
                        continue
                    chunks[key.data].extend(block)
                    if sum(map(len, chunks.values())) > MAX_DIAGNOSTIC:
                        reason = "diagnostic-output-limit"
                        break
                if reason:
                    break
            if process.poll() is None and not reason:
                try:
                    process.wait(timeout=max(0.001, timeout - (time.monotonic() - began)))
                except subprocess.TimeoutExpired:
                    reason = "diagnostic-timeout"
    finally:
        if process.poll() is None:
            process.kill()  # Popen-owned jcmd only, never its inspected target.
        process.wait(timeout=2)
        process.stdout.close()
        process.stderr.close()
    require(reason is None and process.returncode == 0, reason or "diagnostic-nonzero")
    return bytes(chunks["stdout"]), {"exit_code": process.returncode,
        "elapsed_seconds": round(time.monotonic() - began, 3), "stdout_bytes": len(chunks["stdout"]),
        "stderr_bytes": len(chunks["stderr"]), "raw_stdout_archived": False, "raw_stderr_archived": False}


def observe_java(pid: int, *, deadline: float, expected_identity: ProcessIdentity, **context) -> dict:
    before = check_java(pid, **context)
    require(before == expected_identity, "java-identity-changed-before-attach")
    require(hasattr(os, "pidfd_open"), "pidfd-unavailable")
    handle = os.pidfd_open(pid, 0)
    try:
        require(not select.select([handle], [], [], 0)[0] and check_java(pid, **context) == before,
                "java-identity-changed-before-attach")
        workspace, jdk_home = context["workspace"], context["jdk_home"]
        _, private_environment, options = private_values(workspace)
        env = {**private_environment, "JAVA_HOME": str(jdk_home), "PATH": str(jdk_home / "bin") + os.pathsep + os.defpath,
               "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "JAVA_TOOL_OPTIONS": options}
        timeout = min(5.0, deadline - time.monotonic() - 2)
        require(timeout > 0, "observer-deadline-before-attach")
        raw, command = diagnostic([str(jdk_home / "bin/jcmd"), "-J-Xms16m", "-J-Xmx64m", str(pid), "VM.system_properties"], env, timeout)
        require(not select.select([handle], [], [], 0)[0] and check_java(pid, **context) == before,
                "java-identity-changed-after-attach")
        selected = selected_properties(raw, pid, workspace)
        return {"observed": True, "identity": before.public(), **selected,
                "environment": dict(m.ENV_PRIVATE_PATHS), "environment_values_matched": True,
                "executable_and_gradle_command_checked": True, "pidfd_live_before_and_after": True,
                "diagnostic": command, "actual_cache_consumption_verified": False}
    finally:
        os.close(handle)


def runtime_matches(value: dict, marker: dict, mode: str, daemon: dict) -> bool:
    return (value.get("schema_version") == 1 and value.get("record_type") == "gradle-runtime-observation" and
            value.get("run_id") == mode == value.get("mode") and value.get("build_root") == "." and
            value.get("source_input_digest") == marker["source_input_digest"] and value.get("host") == marker["host"] and
            value.get("gradle_version") == "9.7.1" and value.get("runtime_isolation") == m.RUNTIME_ISOLATION and
            daemon.get("observed") is True and value.get("gradle_jvm_process_id") == daemon["identity"]["pid"] and
            value.get("java_runtime_version") == daemon["java_runtime_version"])


def bind_runtime(state: dict, context: dict) -> None:
    path = context["workspace"] / f"build/dependency-integrity/{context['mode']}/graphs/root/runtime.json"
    if path.is_file():
        runtime = checked_json(path)
        state["runtime_receipt_sha256"] = m.file_sha256(path)
        state["runtime_receipt_matched"] = runtime_matches(runtime, context["marker"], context["mode"], state["daemon"])


def fixture_matches(value: dict | None) -> bool:
    if not value:
        return False
    expected_cases = ["baseline-check", *NEGATIVE_CASES]
    attempts = value.get("invocation_attempts", [])
    cases = value.get("cases", [])
    return (value.get("record_type") == "actual-gradle-fixtures" and value.get("actual_host") == "linux-x64" and
            value.get("selected_cases") == expected_cases and value.get("selected_subset") is True and
            value.get("bootstrap_complete") is True and value.get("maximum_gradle_invocations") == 6 and
            value.get("total_timeout_seconds") == 300 and value.get("per_invocation_timeout_seconds") == 90 and
            value.get("reserve_mib") == 8192 and "stopped_reason" not in value and
            value.get("selected_cases_observed_as_expected") is True and value.get("all_cases_observed_as_expected") is False and
            isinstance(attempts, list) and len(attempts) == 6 and all(isinstance(item, dict) for item in attempts) and
            all(item.get("fixture") == name and item.get("mode") == ("bootstrap" if name == "bootstrap" else "check") and
                item.get("entry_root") == "." and item.get("gradle_process_started") is True and
                type(item.get("exit_code")) is int and item.get("exit_code") == (0 if index < 2 else 1) and item.get("stop_reason") is None
                for index, (name, item) in enumerate(zip(CASE_NAMES, attempts))) and
            isinstance(cases, list) and len(cases) == 5 and all(isinstance(item, dict) for item in cases) and
            all(item.get("case") == name and item.get("actual_expected_result_observed") is True and
                item.get("result_kind") == ("strict-acceptance" if index == 0 else "exact-lock-state-rejection")
                for index, (name, item) in enumerate(zip(expected_cases, cases))))


def witness(*, destination: Path, output: Path, suite_pid: int, jdk_home: Path, gradle_home: Path,
            timeout: int = 320) -> dict:
    began = time.monotonic()
    require(sys.platform == "linux" and m.host_key() == "linux-x64", "unsupported-observer-host")
    require(1 <= timeout <= 330, "observer-timeout-limit")
    for path in (jdk_home, gradle_home, output.parent):
        plain_absolute(path)
        require(path.is_dir(), "expected-directory")
    plain_absolute(destination, existing=False)
    plain_absolute(output, existing=False)
    require(not output.exists() and not output.is_relative_to(destination), "unsafe-observer-output")
    require(not any((path / ".git").exists() for path in [destination, *destination.parents]), "fixture-inside-git")
    inputs = checkpoint_files()
    observer_inputs = observer_files()
    suite = check_suite(suite_pid, destination, gradle_home, jdk_home)
    deadline = began + timeout
    result = {"schema_version": 1, "record_type": "passive-fixture005-runtime-witness", "started_utc": driver.utc_now(),
              "scope": "Actual installed-distribution client and distinct Gradle daemon selected runtime paths only",
              "checkpoint006_sha256": CHECKPOINT_SHA256, "frozen006_inputs": inputs,
              "observer_inputs_sha256": observer_inputs,
              "suite_identity": suite.public(), "timeout_seconds": timeout, "maximum_jcmd_attempts": 12,
              "jcmd_timeout_seconds": 5, "diagnostic_output_limit_bytes": MAX_DIAGNOSTIC,
              "jcmd_executable_sha256": m.file_sha256(jdk_home / "bin/jcmd"),
              "java_executable_sha256": m.file_sha256(jdk_home / "bin/java"),
              "gradle_cli_jar_sha256": m.file_sha256(gradle_home / "lib/gradle-gradle-cli-main-9.7.1.jar"),
              "gradle_daemon_jar_sha256": m.file_sha256(gradle_home / "lib/gradle-daemon-main-9.7.1.jar"),
              "helper_sha256": m.file_sha256(Path(__file__)), "cases": [],
              "raw_properties_or_environment_archived": False, "wrapper_client_observed": False,
              "non_gradle_cache_use_verified": False, "gradle_started_or_stopped_by_witness": False,
              "validation_diagnostics": {"count_limit_per_stage_reason": MAX_REASON_COUNT,
                  "maximum_stages_per_case": len(VALIDATION_STAGES), "maximum_reasons_per_stage": len(VALIDATION_REASON_CODES),
                  "counts_are_poll_events_not_unique_processes": True, "raw_exception_messages_archived": False,
                  "counters_do_not_change_acceptance": True},
              "all_six_runtime_observations_complete": False, "fixture_and_runtime_selected_subset_complete": False}
    states = {name: {"case": name, "client": {"observed": False}, "daemon": {"observed": False},
                     "runtime_receipt_matched": False, "validation_reason_counts": {},
                     "validation_reason_counts_saturated": False} for name in CASE_NAMES}
    contexts = {}
    suite_receipt = None
    try:
        while time.monotonic() < deadline - 2:
            for name, state in states.items():
                workspace = destination / name
                mode = "bootstrap" if name == "bootstrap" else "check"
                stage = "context"
                try:
                    if name not in contexts:
                        launch_path = workspace / f"build/dependency-integrity/{mode}/launched-process.json"
                        if not launch_path.is_file():
                            continue
                        marker = driver.load_workspace(workspace)
                        require(marker["kind"] == "controlled-fixture" and marker["build_roots"] == ["."], "foreign-fixture-marker")
                        launch = checked_json(launch_path)
                        require(launch.get("schema_version") == 1 and launch.get("record_type") == "launched-command-process" and
                                type(launch.get("pid")) is int and launch["pid"] > 1 and launch.get("process_group") == launch["pid"] and
                                launch.get("java_identity_observed") is False, "invalid-launch-receipt")
                        context = {"workspace": workspace, "marker": marker, "mode": mode, "jdk_home": jdk_home,
                                   "gradle_home": gradle_home, "suite": suite}
                        client = check_java(launch["pid"], role="client", client=None, **context)
                        contexts[name] = (context, client)
                        state["launcher_receipt_sha256"] = m.file_sha256(launch_path)
                        state["source_input_digest"] = marker["source_input_digest"]
                    context, client = contexts[name]
                    if "attempted" not in state["client"]:
                        state["client"]["attempted"] = True
                        try:
                            state["client"].update(observe_java(client.pid, role="client", client=None, deadline=deadline,
                                                               expected_identity=client, **context))
                        except (WitnessError, m.IntegrityError, OSError, ValueError, subprocess.SubprocessError) as failure:
                            state["client"]["reason"] = record_validation_reason(state, "client-observation", failure_reason(failure))
                    if "attempted" not in state["daemon"]:
                        # Inspect only a verified client's children, not all /proc JVMs.
                        stage = "daemon-children"
                        eligible = []
                        children = owned_children(client)
                        if not children:
                            record_validation_reason(state, "daemon-children", "no-owned-child-at-poll")
                        for child in children:
                            try:
                                observed_identity = check_java(child, role="daemon", client=client, **context)
                                eligible.append(observed_identity)
                            except (WitnessError, m.IntegrityError, OSError, ValueError) as failure:
                                record_validation_reason(state, "daemon-candidate", failure_reason(failure))
                                continue
                        require(len(eligible) <= 1, "ambiguous-gradle-daemon")
                        if eligible:
                            state["daemon"]["attempted"] = True
                            try:
                                state["daemon"].update(observe_java(eligible[0].pid, role="daemon", client=client, deadline=deadline,
                                                                   expected_identity=eligible[0], **context))
                            except (WitnessError, m.IntegrityError, OSError, ValueError, subprocess.SubprocessError) as failure:
                                state["daemon"]["reason"] = record_validation_reason(state, "daemon-observation", failure_reason(failure))
                        else:
                            record_validation_reason(state, "daemon-children", "no-eligible-daemon-at-poll")
                    stage = "runtime-binding"
                    bind_runtime(state, context)
                except (WitnessError, m.IntegrityError, OSError, ValueError, KeyError) as failure:
                    # Missing/short-lived/partially written inputs can become ready.
                    # No diagnostic is retried; incompleteness stays visible at end.
                    state["last_unverified_reason"] = record_validation_reason(state, stage, failure_reason(failure))
                    continue
            final_path = destination / "fixture-results.json"
            if final_path.is_file():
                try:
                    suite_receipt = checked_json(final_path)
                    result["fixture_result_sha256"] = m.file_sha256(final_path)
                    # Final receipt can appear just after the last runtime read.
                    # Refresh only receipt binding, never start a late/retry attach.
                    for name, (context, _) in contexts.items():
                        bind_runtime(states[name], context)
                    break
                except (WitnessError, m.IntegrityError, OSError, ValueError):
                    pass
            try:
                require(identity(suite.pid) == suite, "suite-identity-changed")
            except (WitnessError, OSError, ValueError):
                result["stop_reason"] = "suite-ended-without-final-receipt"
                break
            time.sleep(0.05)
        else:
            result["stop_reason"] = "observer-timeout"
        require(checkpoint_files() == inputs, "frozen006-input-changed")
        require(observer_files() == observer_inputs, "observer-input-changed")
        result["frozen006_inputs_unchanged"] = True
        result["observer_inputs_unchanged"] = True
        result["cases"] = list(states.values())
        result["observation_attempts"] = sum(item.get("attempted", False) for state in states.values() for item in (state["client"], state["daemon"]))
        result["completed_jcmd_commands"] = sum("diagnostic" in item for state in states.values() for item in (state["client"], state["daemon"]))
        result["all_six_runtime_observations_complete"] = all(state["client"].get("observed") and state["daemon"].get("observed") and
                                                              state["runtime_receipt_matched"] for state in states.values())
        result["fixture_selected_subset_matched"] = fixture_matches(suite_receipt)
        result["fixture_and_runtime_selected_subset_complete"] = bool(result["all_six_runtime_observations_complete"] and
            result["fixture_selected_subset_matched"] and "stop_reason" not in result)
        for state in states.values():
            if state["client"].get("observed") and state["daemon"].get("observed") and state["runtime_receipt_matched"]:
                state.pop("last_unverified_reason", None)
    except KeyboardInterrupt:
        result["stop_reason"] = "observer-interrupted-no-gradle-signal-sent"
    except (WitnessError, m.IntegrityError, OSError, ValueError, KeyError) as failure:
        result["stop_reason"] = failure_reason(failure)
    finally:
        result["cases"] = list(states.values())
        result["finished_utc"] = driver.utc_now()
        result["elapsed_seconds"] = round(time.monotonic() - began, 3)
        m.write_new(output, m.json_bytes(result))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suite-pid", type=int, required=True)
    parser.add_argument("--jdk-home", type=Path, required=True)
    parser.add_argument("--gradle-home", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=320)
    try:
        result = witness(**vars(parser.parse_args(argv)))
    except (WitnessError, m.IntegrityError, OSError, ValueError, KeyError, subprocess.SubprocessError) as failure:
        print(json.dumps({"observed": False, "reason": failure_reason(failure)}))
        return 1
    complete = result["fixture_and_runtime_selected_subset_complete"]
    print(json.dumps({"fixture_and_runtime_selected_subset_complete": complete,
                      "all_six_runtime_observations_complete": result["all_six_runtime_observations_complete"],
                      "elapsed_seconds": result["elapsed_seconds"], "gradle_started_or_stopped_by_witness": False}))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
