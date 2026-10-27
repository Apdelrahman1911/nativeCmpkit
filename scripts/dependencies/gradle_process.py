"""Shared exact Gradle9.7.1/JDK17 process grammars (no process control).

Extracted unchanged from the passive witness to avoid a weaker duplicated
command parser in the owning fixture runner. Raw arguments/environment stay
in bounded memory; this module never starts, attaches, signals or reaps a PID.
"""
from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path
import re
import integrity_model as m

DAEMON_MAIN = "org.gradle.launcher.daemon.bootstrap.GradleDaemon"
FORBIDDEN_ENVIRONMENT = ("JAVA_OPTS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "GRADLE_OPTS")

class WitnessError(ValueError):
    """Only fixed, non-sensitive reason codes are emitted."""


def require(condition: object, code: str) -> None:
    if not condition:
        raise WitnessError(code)


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

