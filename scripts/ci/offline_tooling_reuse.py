#!/usr/bin/env python3
"""Prepare/check same-batch offline tooling reuse, never native or CI acceptance.

Only the fixed ten unittest discoveries are eligible. Current history/index checks
and profile preflight remain fresh. The checker is deliberately offline: its API
envelopes MUST be independently acquired over authenticated, read-only GitHub GETs.
It verifies their consistency and the original artifact digest, not their origin.
No fetching, workflow skip output, GitHub mutation, cache, or publication occurs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "Apdelrahman1911/nativeCmpkit"
BRANCH = "development/preview-hardening"
WORKFLOW = ".github/workflows/gradle.yml"
SCHEMA = "nativecmpkit-offline-tooling-reuse-v1"
ARTIFACT_PREFIX = "offline-tooling-scopes-"
SCOPES = tuple((directory, "test_*.py") for directory in (
    "scripts/audit", "scripts/migration", "scripts/development", "scripts/ci",
    "scripts/native", "scripts/dependencies", "scripts/dependencies/yarn",
    "scripts/docs", "tests/consumer")) + (("scripts/development", "upstream_sync_tests.py"),)
REQUIRED_STEPS = (
    "Verify complete history, audit and current development indexes",
    "Record exact offline tooling signature",
    "Offline verification-tool adversarial fixtures (not library passes)",
    "Select only the requested verification profile",
    "Keep successful fixed offline tooling scope receipt",
)
TOOLS = {"python3": ("--version",), "git": ("--version",), "bash": ("--version",),
         "sh": (), "node": ("--version",), "cargo": ("--version",), "rustc": ("-Vv",)}
MAX_JSON_BYTES = 16 * 1024**2
MAX_ARCHIVE_BYTES = 32 * 1024**2
MAX_LOG_BYTES = 16 * 1024**2
# One complete producer is amortized by authenticated same-HEAD reuse. The
# previous CI scope alone reported 771.198s; reserve time for all ten scopes
# and leave a separate five-minute workflow margin for setup/cleanup/evidence.
TOTAL_SCOPE_SECONDS = 1500
SCOPE_HEARTBEAT_SECONDS = 60
MAX_SCOPE_HEARTBEATS = 32
MAX_SCOPE_EVENT_BYTES = 4096
MAX_FAILURE_METADATA_BYTES = 65536
MAX_SOURCE_FILES = 100000
MAX_INPUT_BYTES = 128 * 1024**2
SHA = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ENVIRONMENT_RECIPE = "fresh-home-tmp;fixed-ci-locale;no-source-overrides-user-site-git-global;observed-path-cargo-rustup-v1;ci-whole-module-fork2-private-home-tmp-v1"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def scope_command(directory: str, pattern: str) -> list[str]:
    if (directory, pattern) not in SCOPES:
        raise ValueError("Only an exact fixed offline discovery scope is permitted")
    if (directory, pattern) == ("scripts/ci", "test_*.py"):
        return ["python3", "-B", "scripts/ci/offline_tooling_ci_parallel734.py"]
    return ["python3", "-B", "-m", "unittest", "discover", "-s", directory, "-p", pattern, "-v"]


RECIPE_SHA256 = digest(canonical({"schema": SCHEMA, "environment": ENVIRONMENT_RECIPE,
                                  "commands": [scope_command(*scope) for scope in SCOPES]}))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def positive(value) -> bool:
    return type(value) is int and 0 < value <= 2**53


def safe_path(root: Path, relative: str) -> Path:
    require(type(relative) is str and len(relative) <= 4096, "Expected a bounded relative path")
    parts = relative.split("/")
    require(not relative.startswith("/") and all(part not in ("", ".", "..") for part in parts)
            and "\\" not in relative, "Noncanonical or escaping path refused")
    result = root
    for part in parts:
        result /= part
        require(not result.is_symlink(), "Symlinked input/output refused")
    require(result.resolve().is_relative_to(root.resolve()), "Path leaves the owning checkout")
    return result


def hash_file(path: Path, limit: int = MAX_INPUT_BYTES, *, unshared: bool = True, git_blob_oid: str | None = None) -> str:
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and (not unshared or before.st_nlink == 1) and before.st_size <= limit,
            "Expected a bounded ordinary unshared input")
    result = hashlib.sha256()
    # SHA1 here checks Git's declared blob identity, not dependency/security trust.
    # The independently recorded source map continues to use SHA256.
    blob = hashlib.sha1(b"blob " + str(before.st_size).encode() + b"\0", usedforsecurity=False) if git_blob_oid else None
    def identity(observation):
        # Reading can legitimately update atime; ownership/content identity cannot.
        return (observation.st_dev, observation.st_ino, observation.st_mode, observation.st_nlink,
                observation.st_size, observation.st_mtime_ns, observation.st_ctime_ns)
    with path.open("rb") as stream:
        require(identity(os.fstat(stream.fileno())) == identity(before), "Input displaced before reading")
        for block in iter(lambda: stream.read(1024**2), b""):
            result.update(block)
            if blob is not None:
                blob.update(block)
    require(identity(path.stat()) == identity(before), "Input changed while hashing")
    require(blob is None or blob.hexdigest() == git_blob_oid, "Raw-current bytes do not match the declared committed blob")
    return result.hexdigest()


def command(root: Path, *argv: str) -> bytes:
    # A version/identity observation must not bootstrap a missing compiler.
    result = subprocess.run(argv, cwd=root, env={**os.environ, "RUSTUP_AUTO_INSTALL": "0"},
                            capture_output=True, timeout=30, check=True)
    require(len(result.stdout) <= MAX_JSON_BYTES and len(result.stderr) <= MAX_LOG_BYTES,
            "Command observation exceeds its bound")
    return result.stdout


def capture_source(root: Path) -> dict:
    """Full tracked raw checkout; no historical projection or dependency inference."""
    require(not command(root, "git", "status", "--porcelain=v1", "--untracked-files=all").strip(),
            "An immutable, clean raw-current checkout is required")
    revision = command(root, "git", "rev-parse", "HEAD").decode().strip()
    tree = command(root, "git", "rev-parse", "HEAD^{tree}").decode().strip()
    require(bool(SHA.fullmatch(revision)) and bool(SHA.fullmatch(tree)), "Unknown Git identity")
    inputs = {}
    for entry in command(root, "git", "ls-tree", "-r", "-z", "--full-tree", "HEAD").split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split(" ")
        relative = name.decode("utf-8", errors="strict")
        require(kind == "blob" and mode in ("100644", "100755") and bool(SHA.fullmatch(oid)) and relative not in inputs,
                "Unknown, duplicate or nonordinary tracked source refused")
        path = safe_path(root, relative)
        require(bool(path.stat().st_mode & 0o111) == (mode == "100755"), "Tracked executable mode differs")
        inputs[relative] = {"mode": mode, "sha256": hash_file(path, git_blob_oid=oid)}
    require(0 < len(inputs) <= MAX_SOURCE_FILES, "Missing or unbounded complete input inventory")
    require(WORKFLOW in inputs and "scripts/ci/offline_tooling_reuse.py" in inputs,
            "The new owning helper and workflow must be committed inputs")
    require(command(root, "git", "rev-parse", "HEAD").decode().strip() == revision
            and not command(root, "git", "status", "--porcelain=v1", "--untracked-files=all").strip(),
            "Raw-current checkout changed during observation")
    return {"revision": revision, "tree": tree, "input_count": len(inputs), "inputs": inputs,
            "inputs_sha256": digest(canonical(inputs))}


def tooling_actions(source: str, resolutions: dict | None = None) -> list[dict]:
    """Known literal tooling-job syntax only; named refs may resolve, never guess.

    This is a reuse eligibility restriction, NOT an Actions allowlist/pinning rule.
    Execution under an unresolved named ref remains permitted by owner policy.
    """
    # Inventory all literal step owners, or refuse the ENTIRE recipe. A broad
    # uses regex can omit commented/aliased actions and mistake run data for one.
    require(type(source) is str and "\0" not in source, "Unknown workflow source")
    lines = []
    for line in source.splitlines():
        text = line.lstrip(" ").rstrip(" ")
        if text and not text.startswith("#"):
            lines.append((len(line) - len(line.lstrip(" ")), text))

    def mapping(text):
        item = re.fullmatch(r"([A-Za-z0-9_-]+):(?: +(.*))?", text)
        require(item is not None, "Unsupported nonliteral tooling mapping")
        return item[1], item[2] or ""

    def empty(value):
        return not value or value.startswith("#")

    def scalar(value):
        require(not empty(value) and value[0] not in "&*!{[|>", "Unsupported tooling scalar")

    tops = [(index, *mapping(text)) for index, (indent, text) in enumerate(lines) if indent == 0]
    require(len({key for _, key, _ in tops}) == len(tops), "Duplicate workflow key")
    jobs = [(position, index, value) for position, (index, key, value) in enumerate(tops) if key == "jobs"]
    require(len(jobs) == 1 and empty(jobs[0][2]), "Missing literal jobs mapping")
    position, start, _ = jobs[0]
    end = tops[position + 1][0] if position + 1 < len(tops) else len(lines)
    headers = []
    for index in range(start + 1, end):
        indent, text = lines[index]
        require(indent >= 2, "Unsupported jobs indentation")
        if indent == 2:
            headers.append((index, *mapping(text)))
    require(len({key for _, key, _ in headers}) == len(headers), "Duplicate job key")
    owners = [(position, index, value) for position, (index, key, value) in enumerate(headers) if key == "tooling"]
    require(len(owners) == 1 and empty(owners[0][2]), "Missing literal tooling job")
    position, start, _ = owners[0]
    end = headers[position + 1][0] if position + 1 < len(headers) else end
    fields = []
    for index in range(start + 1, end):
        indent, text = lines[index]
        require(indent >= 4, "Unsupported tooling job indentation")
        if indent == 4:
            fields.append((index, *mapping(text)))
    require(len({key for _, key, _ in fields}) == len(fields), "Duplicate tooling job key")
    step_lines = None
    for position, (index, key, value) in enumerate(fields):
        children = lines[index + 1:fields[position + 1][0] if position + 1 < len(fields) else end]
        if key == "steps":
            require(empty(value), "Only literal tooling steps are eligible")
            step_lines = children
        elif key in {"outputs", "env", "permissions"} and empty(value):
            names = set()
            for indent, text in children:
                require(indent == 6, "Unsupported tooling job data layout")
                name, item = mapping(text)
                require(name not in names, "Duplicate tooling job data key")
                names.add(name)
                scalar(item)
        else:
            require(key in {"name", "if", "runs-on", "needs", "timeout-minutes", "continue-on-error", "permissions"}
                    and not children, "Unsupported tooling job field/layout")
            scalar(value)
    require(step_lines is not None, "Missing literal tooling steps")

    references = []
    keys = None
    nested = None
    block_indent = None
    for indent, text in step_lines:
        if block_indent is not None and indent > block_indent:
            require(indent >= block_indent + 2, "Unsupported tooling scalar indentation")
            continue  # Data ONLY under an explicitly recognized literal owner.
        block_indent = None
        if indent > 8:
            require(indent == 10 and nested is not None, "Unsupported nested tooling step layout")
            key, value = mapping(text)
            require(key not in nested, "Duplicate tooling step data key")
            nested.add(key)
            if re.fullmatch(r"[|>][+-]?(?: +#.*)?", value):
                block_indent = 10
            else:
                scalar(value)
            continue
        if indent == 6:
            require(keys is None or (("uses" in keys) != ("run" in keys)), "Missing/ambiguous tooling step owner")
            require(text.startswith("- "), "Unsupported tooling step sequence")
            text = text[2:]
            keys = set()
        else:
            require(indent == 8 and keys is not None, "Unsupported tooling step indentation")
        key, value = mapping(text)
        require(key in {"name", "id", "if", "uses", "run", "with", "env", "shell", "working-directory",
                        "continue-on-error", "timeout-minutes"} and key not in keys,
                "Unsupported/duplicate tooling step key")
        keys.add(key)
        nested = None
        if key == "uses":
            reference = re.fullmatch(r"([^\s#]+)(?:[ \t]+#.*)?[ \t]*", value)
            require(reference is not None, "Unsupported nonliteral tooling action")
            references.append(reference[1])
        elif key in {"with", "env"}:
            require(empty(value), "Only literal tooling step data mappings are eligible")
            nested = set()
        elif key == "run" and re.fullmatch(r"[|>][+-]?(?: +#.*)?", value):
            block_indent = 8
        else:
            scalar(value)
    require(keys is not None and (("uses" in keys) != ("run" in keys)), "Missing/ambiguous tooling step owner")
    require(references and len(references) == len(set(references)), "Missing/duplicate tooling actions")
    resolutions = {} if resolutions is None else resolutions
    require(type(resolutions) is dict and not (set(resolutions) - set(references)), "Foreign action resolution")
    result = []
    for reference in references:
        require(bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[A-Za-z0-9_./-]+", reference)),
                "Computed/local/container action resolution needs separate review")
        configured = reference.rsplit("@", 1)[1]
        resolved = resolutions.get(reference, configured if SHA.fullmatch(configured) else None)
        require(type(resolved) is str and bool(SHA.fullmatch(resolved)), "Missing actual immutable action resolution")
        require(not SHA.fullmatch(configured) or configured == resolved, "Pinned action resolution drift")
        result.append({"reference": reference, "resolved_commit": resolved})
    return result


def cargo_paths() -> tuple[Path, Path]:
    return (Path(os.environ.get("CARGO_HOME", str(Path.home() / ".cargo"))),
            Path(os.environ.get("RUSTUP_HOME", str(Path.home() / ".rustup"))))


def capture_runtime(root: Path) -> dict:
    require(os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted" and os.environ.get("RUNNER_OS") == "Linux"
            and os.environ.get("RUNNER_ARCH") == "X64" and os.environ.get("ImageOS") == "ubuntu24"
            and platform.system() == "Linux" and platform.machine() in ("x86_64", "AMD64"),
            "V1 reuse requires actual GitHub-hosted Ubuntu24/X64 context")
    image_version = os.environ.get("ImageVersion", "")
    require(bool(re.fullmatch(r"[0-9][0-9A-Za-z._-]{1,127}", image_version)), "Missing exact hosted image version")
    tools = {}
    for name, arguments in TOOLS.items():
        executable = shutil.which(name)
        require(executable is not None, "Required offline scope tool is unavailable")
        path = Path(executable).resolve(strict=True)
        version = command(root, executable, *arguments).decode("utf-8", errors="strict").strip() if arguments else "content-only"
        require(0 < len(version) <= 4096, "Unknown tool version")
        payload = path
        if name in ("cargo", "rustc") and path.name == "rustup":
            # Hash the actual selected toolchain payload, not just its rustup shim.
            payload = Path(command(root, str(path), "which", name).decode().strip()).resolve(strict=True)
        tools[name] = {"version": version, "executable_sha256": hash_file(payload, unshared=False),
                       "launcher_sha256": hash_file(path, unshared=False)}
    require(Path(shutil.which("python3")).resolve() == Path(sys.executable).resolve(),
            "Controller and discovery Python differ")
    cargo_home, rustup_home = cargo_paths()
    configs = {}
    for name, path in (("cargo-config", cargo_home / "config"), ("cargo-config-toml", cargo_home / "config.toml"),
                       ("rustup-settings", rustup_home / "settings.toml")):
        require(not path.is_symlink(), "Displaced compiler configuration refused")
        configs[name] = hash_file(path) if path.exists() else None
    return {"image_os": "ubuntu24", "image_version": image_version, "system": platform.system(),
            "architecture": platform.machine(), "python_implementation": platform.python_implementation(),
            "os_release_sha256": hash_file(Path("/etc/os-release").resolve(), unshared=False),
            "installed_packages_sha256": hash_file(Path("/var/lib/dpkg/status"), unshared=False),
            "path_sha256": digest(os.environ["PATH"].encode()),
            "cargo_paths_sha256": digest(canonical([str(cargo_home), str(rustup_home)])),
            "compiler_configs": configs, "tools": tools}


def capture(root: Path, resolutions: dict | None = None) -> dict:
    source = capture_source(root)
    result = {"schema": SCHEMA, "source": source,
              # Entire source inventory includes ALL tracked declaration/lock/action
              # inputs. Deliberately no narrow dependency/changed-test heuristic.
              "dependency_inputs_sha256": source["inputs_sha256"],
              "workflow": {"path": WORKFLOW, "sha256": source["inputs"][WORKFLOW]["sha256"],
                           "tooling_actions": tooling_actions(safe_path(root, WORKFLOW).read_text(), resolutions)},
              "runtime": capture_runtime(root), "recipe_sha256": RECIPE_SHA256}
    result["signature_sha256"] = digest(canonical(result))
    validate_signature(result)
    return result


def validate_signature(value: dict) -> None:
    require(type(value) is dict and set(value) == {"schema", "source", "dependency_inputs_sha256", "workflow",
            "runtime", "recipe_sha256", "signature_sha256"}, "Unknown/partial signature schema")
    require(value["schema"] == SCHEMA and value["recipe_sha256"] == RECIPE_SHA256, "Foreign scope/environment recipe")
    body = {key: item for key, item in value.items() if key != "signature_sha256"}
    require(value["signature_sha256"] == digest(canonical(body)), "Signature digest does not bind its body")
    source = value["source"]
    require(type(source) is dict and set(source) == {"revision", "tree", "input_count", "inputs", "inputs_sha256"}
            and type(source["revision"]) is str and bool(SHA.fullmatch(source["revision"]))
            and type(source["tree"]) is str and bool(SHA.fullmatch(source["tree"])), "Unknown source identity")
    inputs = source["inputs"]
    require(type(inputs) is dict and positive(source["input_count"]) and source["input_count"] == len(inputs)
            and len(inputs) <= MAX_SOURCE_FILES, "Missing/partial input map")
    for name, item in inputs.items():
        require(type(name) is str and not PurePosixPath(name).is_absolute() and "\\" not in name
                and all(part not in ("", ".", "..") for part in name.split("/")) and type(item) is dict
                and set(item) == {"mode", "sha256"} and item["mode"] in ("100644", "100755")
                and type(item["sha256"]) is str and bool(SHA256.fullmatch(item["sha256"])), "Unknown raw input")
    require(WORKFLOW in inputs and "scripts/ci/offline_tooling_reuse.py" in inputs
            and source["inputs_sha256"] == digest(canonical(inputs))
            and value["dependency_inputs_sha256"] == source["inputs_sha256"], "Complete source/dependency binding missing")
    workflow = value["workflow"]
    require(type(workflow) is dict and set(workflow) == {"path", "sha256", "tooling_actions"}
            and workflow["path"] == WORKFLOW and workflow["sha256"] == inputs[WORKFLOW]["sha256"], "Workflow binding drift")
    actions = workflow["tooling_actions"]
    require(type(actions) is list and 0 < len(actions) <= 16, "Missing action identities")
    references = []
    for action in actions:
        require(type(action) is dict and set(action) == {"reference", "resolved_commit"}
                and type(action["reference"]) is str and type(action["resolved_commit"]) is str
                and bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[A-Za-z0-9_./-]+", action["reference"]))
                and bool(SHA.fullmatch(action["resolved_commit"])), "Unknown action identity")
        configured = action["reference"].rsplit("@", 1)[1]
        require(not SHA.fullmatch(configured) or configured == action["resolved_commit"], "Pinned action identity drift")
        references.append(action["reference"])
    require(len(references) == len(set(references)), "Duplicate action identity")
    runtime = value["runtime"]
    require(type(runtime) is dict and set(runtime) == {"image_os", "image_version", "system", "architecture",
            "python_implementation", "os_release_sha256", "installed_packages_sha256", "path_sha256",
            "cargo_paths_sha256", "compiler_configs", "tools"} and runtime["image_os"] == "ubuntu24"
            and runtime["system"] == "Linux" and runtime["architecture"] in ("x86_64", "AMD64")
            and type(runtime["image_version"]) is str and bool(re.fullmatch(r"[0-9][0-9A-Za-z._-]{1,127}", runtime["image_version"]))
            and runtime["python_implementation"] == "CPython", "Missing actual hosted runtime identity")
    for key in ("os_release_sha256", "installed_packages_sha256", "path_sha256", "cargo_paths_sha256"):
        require(type(runtime[key]) is str and bool(SHA256.fullmatch(runtime[key])), "Partial runtime identity")
    configs = runtime["compiler_configs"]
    require(type(configs) is dict and set(configs) == {"cargo-config", "cargo-config-toml", "rustup-settings"}
            and all(item is None or (type(item) is str and SHA256.fullmatch(item)) for item in configs.values()), "Partial compiler recipe")
    require(type(runtime["tools"]) is dict and set(runtime["tools"]) == set(TOOLS), "Missing actual required scope tools")
    for tool in runtime["tools"].values():
        require(type(tool) is dict and set(tool) == {"version", "executable_sha256", "launcher_sha256"}
                and type(tool["version"]) is str and 0 < len(tool["version"]) <= 4096
                and all(type(tool[key]) is str and SHA256.fullmatch(tool[key])
                        for key in ("executable_sha256", "launcher_sha256")), "Partial tool identity")


def scope_environment(home: Path, temporary: Path) -> dict[str, str]:
    cargo_home, rustup_home = cargo_paths()
    # No credential/source-override environment is inherited. Paths are not
    # exported in receipts; actual PATH/tools/configs are signature-bound.
    return {"PATH": os.environ["PATH"], "HOME": str(home), "TMPDIR": str(temporary),
            "CARGO_HOME": str(cargo_home), "RUSTUP_HOME": str(rustup_home),
            "RUSTUP_AUTO_INSTALL": "0",
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "CI": "true",
            "GITHUB_ACTIONS": "true", "RUNNER_OS": "Linux", "RUNNER_ARCH": "X64",
            "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def scope_summary(scope: tuple[str, str], returncode: int, output: bytes) -> dict:
    require(type(returncode) is int and len(output) <= MAX_LOG_BYTES, "Unbounded/unknown scope outcome")
    text = output.decode("utf-8", errors="replace")
    matches = list(re.finditer(r"(?m)^Ran ([0-9]+) tests? in [0-9.]+s\r?$", text))
    count = int(matches[-1][1]) if len(matches) == 1 else 0
    status_lines = text[matches[0].end():].strip().splitlines() if len(matches) == 1 else []
    # Buffered public fixture stdout may flush after unittest's stderr summary.
    # Only plain OK is eligible; expected-failure/skip decorations are not green.
    passed = returncode == 0 and 0 < count <= MAX_SOURCE_FILES and bool(status_lines) and status_lines[0] == "OK"
    return {"directory": scope[0], "pattern": scope[1], "command": scope_command(*scope), "returncode": returncode,
            "tests": count, "passed": passed, "output_sha256": digest(output), "output_bytes": len(output)}


def emit_scope_event(scope, event, observation=None, *, phase="startup", summary=None):
    """Fixed, nullable metadata only; never a result/receipt or a hard deadline."""
    try:
        if (type(scope) is not tuple or len(scope) != 2 or any(type(value) is not str for value in scope)
                or scope not in SCOPES or type(event) is not str or type(phase) is not str
                or event not in {"started", "heartbeat", "refused", "cleanup-refused", "completed"}
                or phase not in {"startup", "retain-child", "wait-clock", "wait-output", "wait-guard", "wait-sleep", "cleanup", "post-cleanup-summary"}):
            return
        values = observation if type(observation) is dict else {}
        record = {"schema": "nativecmpkit-offline-scope-observation-v1", "diagnostic_only": True,
                  "event": event, "phase": phase, "directory": scope[0], "pattern": scope[1],
                  "original_child_group_disposal_completed": phase == "post-cleanup-summary",
                  "elapsed_excludes_startup_and_cleanup": True,
                  "observations_are_not_cause_inferences": True,
                  "scope_index": SCOPES.index(scope) + 1, "scope_count": len(SCOPES),
                  "bounds_are_cooperative": True, "reusable_certificate": False,
                  "elapsed_seconds": None, "allocated_seconds": None,
                  "time_admitted": None, "output_admitted": None, "guard_output_bytes": None}
        for field in ("elapsed_seconds", "allocated_seconds"):
            value = values.get(field)
            if type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 2**53:
                record[field] = value
        for field in ("time_admitted", "output_admitted"):
            value = values.get(field)
            if type(value) is bool:
                record[field] = value
        value = values.get("guard_output_bytes")
        if type(value) is int and 0 <= value <= 2**63 - 1:
            record["guard_output_bytes"] = value
        value = values.get("heartbeat_count")
        record["heartbeat_count"] = value if type(value) is int and 0 <= value <= MAX_SCOPE_HEARTBEATS else None
        if type(summary) is dict:
            count, passed, returncode = (summary.get(key) for key in ("tests", "passed", "returncode"))
            record["reported_tests"] = count if type(count) is int and 0 <= count <= MAX_SOURCE_FILES else None
            record["summary_passed"] = passed if type(passed) is bool else None
            record["direct_returncode"] = returncode if type(returncode) is int and -255 <= returncode <= 255 else None
        public = "[offline-scope] " + canonical(record).decode("ascii")
        if len(public.encode("ascii")) <= MAX_SCOPE_EVENT_BYTES:
            print(public, file=sys.stderr, flush=True)
    except BaseException:
        pass  # Secondary metadata I/O cannot replace an outcome or owned cleanup.


def emit_scope_failure_inventory(output, *, include_tail=False):
    """One same-execution capped buffer; incomplete inventory is never eligibility."""
    try:
        from offline_tooling_failure_inventory import failure_inventory_line
        inventory = failure_inventory_line(output)
        if (type(inventory) is not str or not inventory.isascii()
                or not inventory.startswith("[offline-failure-inventory] ")
                or len(inventory.encode("ascii")) > MAX_FAILURE_METADATA_BYTES):
            raise ValueError("Bounded fixed inventory metadata is required")
    except BaseException:
        inventory = ('[offline-failure-inventory] {"schema":"nativecmpkit-offline-failure-inventory-v1",'
                     '"diagnostic_only":true,"status":"unknown",'
                     '"reason_codes":["inventory-helper-unavailable"],"records":[]}')
    try:
        print(inventory, file=sys.stderr, flush=True)
    except BaseException:
        pass
    if include_tail:
        try:
            for line in output.decode("utf-8", errors="replace").splitlines()[-100:]:
                print("[redacted diagnostic]" if re.search(r"(?i)password|secret|token|credential|authorization|PRIVATE KEY", line)
                      else line[:2000], file=sys.stderr, flush=True)
        except BaseException:
            pass  # The existing red tail remains secondary to the failed summary.


def emit_scope_failure_progress(scope, output, *, phase, sampled_after_refusal):
    """Secondary lexical metadata from the same failed prefix; never heartbeat work."""
    try:
        if (type(scope) is not tuple or len(scope) != 2 or any(type(value) is not str for value in scope)
                or scope not in SCOPES or type(output) is not bytes or len(output) > MAX_LOG_BYTES + 1
                or type(phase) is not str
                or phase not in {"startup", "retain-child", "wait-clock", "wait-output", "wait-guard", "wait-sleep", "cleanup", "post-cleanup-summary"}
                or type(sampled_after_refusal) is not bool):
            return
        scope = SCOPES[SCOPES.index(scope)]
        progress = None
        try:
            from offline_tooling_failure_evidence711 import observe_progress
            found = observe_progress(output)
            fields = {"qualified_parent_progress_observations", "terminal_token_observations",
                      "unresolved_or_interleaved_progress_observations", "last_qualified_parent_progress",
                      "parsed_prefix_bytes", "limits_observed"}
            limits = {"input_byte_cap", "line_cap", "line_byte_cap", "non_utf8_line",
                      "unqualified_progress", "credential_shaped_id"}
            require(type(found) is dict and set(found) == fields, "Unknown progress metadata")
            count, pending, size = (found[key] for key in ("qualified_parent_progress_observations",
                                   "unresolved_or_interleaved_progress_observations", "parsed_prefix_bytes"))
            require(all(type(value) is int and 0 <= value <= 200000 for value in (count, pending))
                    and type(size) is int and 0 <= size <= min(len(output), 16 * 1024**2), "Unknown progress bounds")
            tokens, capped, last = (found[key] for key in
                                   ("terminal_token_observations", "limits_observed", "last_qualified_parent_progress"))
            require(type(tokens) is dict and set(tokens) == {"ok", "FAIL", "ERROR"}
                    and all(type(value) is int and 0 <= value <= count for value in tokens.values())
                    and sum(tokens.values()) + pending == count
                    and type(capped) is dict and set(capped) == limits
                    and all(type(value) is bool for value in capped.values()), "Unknown progress observations")
            require((last is None and count == 0) or (type(last) is dict and count > 0), "Unknown last progress")
            if last is not None:
                require(set(last) == {"testcase_id", "result_token", "line_number", "byte_offset", "line_terminated"},
                        "Unknown last-progress fields")
                identifier = last["testcase_id"]
                require(type(identifier) is str and len(identifier) <= 384 and identifier.isascii()
                        and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+", identifier)
                        and identifier.rsplit(".", 1)[-1].startswith("test_")
                        and not re.search(r"(?i)github_pat_|gh[pousr]_|(?:^|[._-])sk[-_]", identifier)
                        and type(last["result_token"]) is str
                        and last["result_token"] in {"ok", "FAIL", "ERROR", "unresolved-or-interleaved"}
                        and type(last["line_number"]) is int and 0 < last["line_number"] <= 200000
                        and type(last["byte_offset"]) is int and 0 <= last["byte_offset"] < size
                        and type(last["line_terminated"]) is bool, "Unknown last-progress values")
            progress = found
        except BaseException:
            pass  # Unavailable helper/metadata is not a count, private message or cause.
        record = {"schema": "nativecmpkit-offline-scope-progress711-v1", "diagnostic_only": True,
                  "directory": scope[0], "pattern": scope[1], "scope_index": SCOPES.index(scope) + 1,
                  "phase": phase, "sample_is_after_refusal": sampled_after_refusal,
                  "stream_observation": "original-merged-stdout-stderr-prefix",
                  "progress_observation_available": progress is not None,
                  "progress": progress, "complete_output": False,
                  "counts_are_progress_observations_not_tests": True,
                  "last_progress_is_not_current_test_or_failure_cause": True,
                  "subtest_parameters_raw_output_messages_or_environment_exported": False,
                  "reusable_certificate": False}
        public = "[offline-scope-progress] " + canonical(record).decode("ascii")
        if len(public.encode("ascii")) <= MAX_SCOPE_EVENT_BYTES:
            print(public, file=sys.stderr, flush=True)
    except BaseException:
        pass  # Secondary metadata I/O never replaces the primary or owned cleanup.


def emit_scope_buffer_metadata(scope, output, *, phase, sampled_after_refusal):
    """A capped prefix only; never a completed-log or failure-cause assertion."""
    try:
        if (type(scope) is not tuple or len(scope) != 2 or any(type(value) is not str for value in scope)
                or scope not in SCOPES or type(output) is not bytes or len(output) > MAX_LOG_BYTES + 1
                or type(phase) is not str
                or phase not in {"startup", "retain-child", "wait-clock", "wait-output", "wait-guard", "wait-sleep", "cleanup", "post-cleanup-summary"}
                or type(sampled_after_refusal) is not bool):
            return
        scope = SCOPES[SCOPES.index(scope)]
        sample = {"schema": "nativecmpkit-offline-scope-buffer-v1", "diagnostic_only": True,
                  "directory": scope[0], "pattern": scope[1], "phase": phase,
                  "original_child_group_disposal_completed": phase == "post-cleanup-summary",
                  "buffered_prefix_bytes": len(output), "buffered_prefix_sha256": digest(output),
                  "complete_output": False, "sample_is_after_refusal": sampled_after_refusal,
                  "metadata_recorded_after_refusal": True, "shared_file_offset_changed": False}
        try:
            print("[offline-scope-buffer] " + canonical(sample).decode("ascii"), file=sys.stderr, flush=True)
        except BaseException:
            pass
        emit_scope_failure_inventory(output)
        emit_scope_failure_progress(scope, output, phase=phase,
                                    sampled_after_refusal=sampled_after_refusal)
        try:
            from offline_tooling_failure_parent_ids658 import emit_failure_parent_ids
            emit_failure_parent_ids(output, scope_index=SCOPES.index(scope) + 1,
                                    phase=phase, sampled_after_refusal=sampled_after_refusal,
                                    stream=sys.stderr)
        except BaseException:
            pass
    except BaseException:
        pass


def emit_scope_refusal(log, scope, observation, *, phase, event="refused"):
    """One phased refusal sample without changing the child-shared file offset."""
    try:
        if (type(scope) is not tuple or len(scope) != 2 or any(type(value) is not str for value in scope)
                or scope not in SCOPES or type(event) is not str or event not in {"refused", "cleanup-refused"}
                or type(phase) is not str
                or phase not in {"startup", "retain-child", "wait-clock", "wait-output", "wait-guard", "wait-sleep", "cleanup", "post-cleanup-summary"}):
            return
        scope = SCOPES[SCOPES.index(scope)]  # Export owning constants, never caller-controlled strings.
        emit_scope_event(scope, event, observation, phase=phase)
        # pread is mandatory on this Linux-only owner. A child can still write:
        # this is a capped subsequent prefix sample, not an atomic completed log
        # or a retroactive observation of a short-circuited guard operand.
        output = os.pread(log.fileno(), MAX_LOG_BYTES + 1, 0)
        emit_scope_buffer_metadata(scope, output, phase=phase, sampled_after_refusal=True)
    except BaseException:
        try:
            print('[offline-scope-buffer] {"schema":"nativecmpkit-offline-scope-buffer-v1",'
                  '"diagnostic_only":true,"complete_output":false,"buffer_available":false}',
                  file=sys.stderr, flush=True)
        except BaseException:
            pass


def execute_scope(root: Path, scope: tuple[str, str], seconds: float) -> dict:
    """Cooperatively bound/dispose only the proven original Linux child group."""
    require(platform.system() == "Linux" and all(hasattr(os, name) for name in
            ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT", "getpgid", "getsid", "killpg", "pread")),
            "Owned offline scope disposal requires Linux waitid/WNOWAIT")
    with tempfile.TemporaryDirectory(prefix="offline-tooling-") as private, tempfile.TemporaryFile() as log:
        home, temporary = Path(private) / "home", Path(private) / "tmp"
        home.mkdir(); temporary.mkdir()
        process = subprocess.Popen(scope_command(*scope), cwd=root, env=scope_environment(home, temporary),
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        def retain_child():
            # WNOWAIT pins the direct child/PID even after it exits. Never poll
            # or reap it before the final original-session/group signal.
            require(process.returncode is None, "Direct offline child was collected before disposal")
            observed = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            require(observed is None or observed.si_pid == process.pid, "Unproven direct offline child")
            return observed
        def dispose_group():
            failures = []
            # A leader may exit while its descendants are alive. Both signals
            # require the unreaped direct child's original session/group proof.
            # These are cooperative bounds, not escaped-descendant containment.
            for requested_signal in (signal.SIGTERM, signal.SIGKILL):
                try:
                    retain_child()
                    require(os.getpgid(process.pid) == process.pid and os.getsid(process.pid) == process.pid,
                            "Unproven original offline child session/group")
                    os.killpg(process.pid, requested_signal)
                except BaseException as error:
                    failures.append(error)
            try:
                # Independent direct-child disposal remains safe even if the
                # group proof/refused signal fails; never signal a foreign group.
                if retain_child() is None:
                    os.kill(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            except BaseException as error:
                failures.append(error)
            if failures:
                for later in failures[1:]:
                    failures[0].add_note("Further owned offline cleanup refusal: " + type(later).__name__)
                raise failures[0]
        observation, phase, heartbeats = None, "startup", 0
        try:
            started = time.monotonic()
            allocated = max(0, seconds)
            deadline, heartbeat = started + allocated, started + SCOPE_HEARTBEAT_SECONDS
            observation = {"elapsed_seconds": 0, "allocated_seconds": allocated, "heartbeat_count": heartbeats}
            try:
                emit_scope_event(scope, "started", observation, phase="startup")
            except BaseException:
                pass
            phase = "retain-child"
            while retain_child() is None:
                phase = "wait-clock"
                now = time.monotonic()
                time_admitted = now < deadline
                observation = {"elapsed_seconds": now - started, "allocated_seconds": allocated,
                               "heartbeat_count": heartbeats, "time_admitted": time_admitted,
                               "output_admitted": None, "guard_output_bytes": None}
                output_admitted = None
                if time_admitted:
                    # Retain the original short circuit: an expired time guard
                    # does not observe/admit the output-size operand.
                    phase = "wait-output"
                    output_bytes = os.fstat(log.fileno()).st_size
                    output_admitted = output_bytes <= MAX_LOG_BYTES
                    observation.update(output_admitted=output_admitted, guard_output_bytes=output_bytes)
                phase = "wait-guard"
                require(time_admitted and output_admitted is True,
                        "Offline scope exceeded its total time/output bound")
                if now >= heartbeat:
                    if heartbeats < MAX_SCOPE_HEARTBEATS:
                        heartbeats += 1
                        observation["heartbeat_count"] = heartbeats
                        try:
                            emit_scope_event(scope, "heartbeat", observation, phase="wait-guard")
                        except BaseException:
                            pass
                    heartbeat = now + SCOPE_HEARTBEAT_SECONDS
                phase = "wait-sleep"
                time.sleep(0.05)
                # A next retain/clock refusal must not carry old guard operands
                # as observations of the new failing operation.
                observation = {"allocated_seconds": allocated, "heartbeat_count": heartbeats}
                phase = "retain-child"
        except BaseException:
            try:
                emit_scope_refusal(log, scope, observation, phase=phase)
            except BaseException:
                pass
            raise
        finally:
            primary = sys.exc_info()[1]
            try:
                dispose_group()
            except BaseException as cleanup_error:
                if primary is None:
                    try:
                        emit_scope_refusal(log, scope, None, phase="cleanup", event="cleanup-refused")
                    except BaseException:
                        pass
                    raise
                primary.add_note("Owned offline child-group cleanup also refused: " + type(cleanup_error).__name__)
        log.seek(0)
        output = log.read(MAX_LOG_BYTES + 1)
    # Preserve the original resource ordering: both owned temporary contexts
    # have disposed before summary validation. A context failure still prevents
    # any summary or green result, exactly as before this diagnostic addition.
    try:
        summary = scope_summary(scope, process.returncode, output)
    except BaseException:
        try:
            emit_scope_event(scope, "refused", phase="post-cleanup-summary")
            # The bounded bytes were read before this summary refusal, after
            # child-group disposal. No closed FD is reopened or sampled here.
            emit_scope_buffer_metadata(scope, output, phase="post-cleanup-summary", sampled_after_refusal=False)
        except BaseException:
            pass
        raise
    try:
        # No new duration claim: completion includes disposal, unlike loop clocks.
        emit_scope_event(scope, "completed", {"allocated_seconds": allocated, "heartbeat_count": heartbeats},
                         phase="post-cleanup-summary", summary=summary)
    except BaseException:
        pass
    if not summary["passed"]:
        try:
            emit_scope_failure_inventory(output, include_tail=True)
        except BaseException:
            pass
    return summary

def producer_context(signature: dict) -> dict:
    require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY and os.environ.get("GITHUB_JOB") == "tooling"
            and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
            and os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH
            and os.environ.get("GITHUB_SHA") == signature["source"]["revision"], "Foreign producer context")
    run, attempt = os.environ.get("GITHUB_RUN_ID", ""), os.environ.get("GITHUB_RUN_ATTEMPT", "")
    require(run.isascii() and run.isdigit() and attempt.isascii() and attempt.isdigit(), "Missing exact producer attempt")
    require(positive(int(run)) and positive(int(attempt)), "Unknown producer identity")
    return {"repository": REPOSITORY, "workflow": WORKFLOW, "branch": BRANCH, "job_name": "tooling",
            "run_id": int(run), "run_attempt": int(attempt)}


def run_scopes(root: Path, expected: dict, resolutions: dict | None = None) -> dict:
    validate_signature(expected)
    require(capture(root, resolutions) == expected, "Current source/runtime differs before scope execution")
    producer = producer_context(expected)
    results, deadline = [], time.monotonic() + TOTAL_SCOPE_SECONDS
    for scope in SCOPES:
        result = execute_scope(root, scope, deadline - time.monotonic())
        results.append(result)
        if not result["passed"]:
            break
    held = capture(root, resolutions) == expected
    return {"schema": SCHEMA, "signature": expected, "producer": producer, "scope_results": results,
            "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "inputs_held": held,
            "passed": held and len(results) == len(SCOPES) and all(item["passed"] for item in results),
            "fresh_scope_execution": True, "library_or_native_results_reused": False,
            "consumer_results_reused": False, "release_readiness_certified": False}


def parse_json(raw: bytes):
    require(0 < len(raw) <= MAX_JSON_BYTES, "Missing/unbounded JSON")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key refused")
            result[key] = value
        return result
    def constant(_value):
        raise ValueError("Nonordinary JSON constant refused")
    return json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=pairs, parse_constant=constant)


def timestamp(value) -> dt.datetime:
    require(type(value) is str and len(value) <= 64, "Missing exact timestamp")
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.utcoffset() == dt.timedelta(0), "Non-UTC producer timestamp refused")
    return result


def check(current: dict, archive: bytes, run: dict, job: dict, artifact: dict,
          now: dt.datetime | None = None) -> dict:
    """Consistency check; independently authenticated API/archive acquisition required."""
    validate_signature(current)
    require(type(run) is dict and type(job) is dict and type(artifact) is dict, "Missing producer envelope")
    require(positive(run.get("id")) and positive(run.get("run_attempt")) and positive(job.get("id"))
            and positive(artifact.get("id")), "Unknown producer IDs")
    repository, head_repository = run.get("repository", {}), run.get("head_repository", {})
    require(type(repository) is dict and type(head_repository) is dict and repository.get("full_name") == REPOSITORY
            and head_repository.get("full_name") == REPOSITORY and positive(repository.get("id"))
            and repository["id"] == head_repository.get("id"), "Foreign/fork repository refused")
    require(run.get("path") == WORKFLOW and run.get("event") == "workflow_dispatch" and run.get("head_branch") == BRANCH
            and run.get("head_sha") == current["source"]["revision"] and run.get("status") == "completed"
            and run.get("conclusion") in ("success", "failure"), "Missing/cancelled/foreign producer run")
    require(job.get("run_id") == run["id"] and type(job.get("run_id")) is int
            and job.get("run_attempt") == run["run_attempt"] and type(job.get("run_attempt")) is int
            and job.get("head_sha") == run["head_sha"] and job.get("head_branch") == BRANCH
            and job.get("name") == "tooling" and job.get("status") == "completed"
            and job.get("conclusion") == "success" and type(job.get("labels")) is list
            and job["labels"] == ["ubuntu-24.04"], "Red/missing/foreign tooling job")
    api_base = "https://api.github.com/repos/" + REPOSITORY + "/actions/"
    require(run.get("url") == api_base + "runs/" + str(run["id"])
            and job.get("url") == api_base + "jobs/" + str(job["id"])
            and job.get("run_url") == run["url"]
            and artifact.get("url") == api_base + "artifacts/" + str(artifact["id"])
            and artifact.get("archive_download_url") == artifact["url"] + "/zip", "Foreign API identity")
    steps = job.get("steps")
    require(type(steps) is list and all(type(step) is dict and positive(step.get("number")) for step in steps),
            "Missing original numbered step inventory")
    numbers = [step["number"] for step in steps]
    require(numbers == sorted(set(numbers)), "Original step order/identity drift")
    indices = []
    for name in REQUIRED_STEPS:
        matches = [(index, step) for index, step in enumerate(steps) if type(step) is dict and step.get("name") == name]
        require(len(matches) == 1 and matches[0][1].get("status") == "completed"
                and matches[0][1].get("conclusion") == "success", "Required producer step missing/red/skipped")
        indices.append(matches[0][0])
    require(indices == sorted(indices), "Required producer step order drift")
    require(artifact.get("expired") is False and type(artifact.get("size_in_bytes")) is int
            and artifact["size_in_bytes"] == len(archive) and 0 < len(archive) <= MAX_ARCHIVE_BYTES
            and artifact.get("digest") == "sha256:" + digest(archive)
            and artifact.get("name") == ARTIFACT_PREFIX + current["signature_sha256"], "Missing/expired/foreign artifact or original digest")
    workflow_run = artifact.get("workflow_run", {})
    require(type(workflow_run) is dict and type(workflow_run.get("id")) is int and workflow_run.get("id") == run["id"]
            and positive(workflow_run.get("repository_id")) and workflow_run.get("repository_id") == repository["id"]
            and positive(workflow_run.get("head_repository_id")) and workflow_run.get("head_repository_id") == repository["id"]
            and workflow_run.get("head_sha") == run["head_sha"] and workflow_run.get("head_branch") == BRANCH,
            "Foreign artifact producer")
    now = now or dt.datetime.now(dt.timezone.utc)
    start, created, end = timestamp(job.get("started_at")), timestamp(artifact.get("created_at")), timestamp(job.get("completed_at"))
    require(start <= created <= end <= now < timestamp(artifact.get("expires_at")), "Artifact is not from this completed job attempt")
    with zipfile.ZipFile(io.BytesIO(archive)) as original:
        members = original.infolist()
        require(len(members) == 1 and members[0].filename == "receipt.json" and not members[0].is_dir()
                and members[0].file_size <= MAX_JSON_BYTES and not members[0].flag_bits & 1
                and members[0].compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                and stat.S_IFMT(members[0].external_attr >> 16) in (0, stat.S_IFREG), "Unknown/unbounded artifact member")
        with original.open(members[0]) as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
            require(len(raw) <= MAX_JSON_BYTES and len(raw) == members[0].file_size,
                    "Artifact expansion differs from its bounded declared member")
            require(stream.read(1) == b"", "Artifact expansion exceeds its declared bound")
        receipt = parse_json(raw)
    require(type(receipt) is dict and set(receipt) == {"schema", "signature", "producer", "scope_results", "recorded_at_utc",
            "inputs_held", "passed", "fresh_scope_execution", "library_or_native_results_reused", "consumer_results_reused",
            "release_readiness_certified"} and receipt["schema"] == SCHEMA, "Legacy/partial receipt refused")
    validate_signature(receipt["signature"])
    require(receipt["signature"] == current, "Source/dependency/action/runtime signature drift")
    require(receipt["producer"] == {"repository": REPOSITORY, "workflow": WORKFLOW, "branch": BRANCH, "job_name": "tooling",
            "run_id": run["id"], "run_attempt": run["run_attempt"]}
            and positive(receipt["producer"].get("run_id")) and positive(receipt["producer"].get("run_attempt")), "Foreign/mixed producer attempt")
    require(start <= timestamp(receipt["recorded_at_utc"]) <= created
            and all(receipt[key] is True for key in ("inputs_held", "passed", "fresh_scope_execution"))
            and all(receipt[key] is False for key in ("library_or_native_results_reused", "consumer_results_reused", "release_readiness_certified")),
            "Red/unknown/re-exported receipt or broadened acceptance")
    results = receipt["scope_results"]
    require(type(results) is list and len(results) == len(SCOPES), "Missing/extra offline scope")
    for scope, result in zip(SCOPES, results):
        require(type(result) is dict and set(result) == {"directory", "pattern", "command", "returncode", "tests", "passed",
                "output_sha256", "output_bytes"} and (result["directory"], result["pattern"]) == scope
                and result["command"] == scope_command(*scope) and type(result["returncode"]) is int
                and result["returncode"] == 0 and result["passed"] is True and positive(result["tests"])
                and result["tests"] <= MAX_SOURCE_FILES and positive(result["output_bytes"])
                and result["output_bytes"] <= MAX_LOG_BYTES and type(result["output_sha256"]) is str
                and bool(SHA256.fullmatch(result["output_sha256"])), "Missing/red/zero/foreign offline scope outcome")
    return {"schema": SCHEMA, "eligible": True, "signature_sha256": current["signature_sha256"],
            "producer_run_id": run["id"], "producer_attempt": run["run_attempt"], "producer_job_id": job["id"],
            "producer_artifact_id": artifact["id"], "producer_workflow_conclusion": run["conclusion"],
            "offline_scopes_reused": len(SCOPES), "new_scope_executions": 0, "native_failure_waived": False,
            "library_or_native_results_reused": False, "consumer_results_reused": False,
            "release_readiness_certified": False, "authenticated_transport_by_helper": False}


def read_owned(root: Path, relative: str, limit: int = MAX_JSON_BYTES) -> bytes:
    path = safe_path(root, relative)
    base = safe_path(root, "build/ci-tooling-reuse")
    require(path.is_relative_to(base) and path != base, "Use confined acquired runtime inputs")
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit,
            "Expected a bounded ordinary acquired input")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) ==
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns), "Acquired input displaced")
        data = stream.read(limit + 1)
    after = path.stat()
    require(len(data) <= limit and (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) ==
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns), "Acquired input changed while reading")
    return data


def output_path(root: Path, relative: str) -> Path:
    path = safe_path(root, relative)
    base = safe_path(root, "build/ci-tooling-reuse")
    require(path.is_relative_to(base) and path != base and path.suffix == ".json" and not path.exists(),
            "Use a fresh confined JSON output, never overwrite retained evidence")
    return path


def write_owned(root: Path, relative: str, value: dict) -> None:
    path = output_path(root, relative)
    data = canonical(value) + b"\n"
    require(len(data) <= MAX_JSON_BYTES, "Receipt exceeds its bound")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture", "run", "check"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--signature")
    parser.add_argument("--resolved-actions", help="Optional independently observed named tooling-action resolutions")
    parser.add_argument("--archive")
    parser.add_argument("--run")
    parser.add_argument("--job")
    parser.add_argument("--artifact")
    args = parser.parse_args()
    # Refuse stale/foreign output before executing any successful population.
    output_path(ROOT, args.output)
    resolutions = parse_json(read_owned(ROOT, args.resolved_actions)) if args.resolved_actions else None
    if args.mode == "capture":
        require(not any((args.signature, args.archive, args.run, args.job, args.artifact)), "Foreign capture arguments")
        result = capture(ROOT, resolutions)
    elif args.mode == "run":
        require(args.signature and not any((args.archive, args.run, args.job, args.artifact)), "Missing/foreign run arguments")
        result = run_scopes(ROOT, parse_json(read_owned(ROOT, args.signature)), resolutions)
    else:
        require(all((args.signature, args.archive, args.run, args.job, args.artifact)) and not args.resolved_actions,
                "All independently acquired producer inputs and current signature are required")
        current = parse_json(read_owned(ROOT, args.signature))
        # Recompute, do not accept a caller-labelled stale current signature.
        supplied = {item["reference"]: item["resolved_commit"] for item in current["workflow"]["tooling_actions"]}
        require(capture(ROOT, supplied) == current, "Raw-current source/runtime changed since capture")
        result = check(current, read_owned(ROOT, args.archive, MAX_ARCHIVE_BYTES),
                       *(parse_json(read_owned(ROOT, getattr(args, name))) for name in ("run", "job", "artifact")))
        require(capture(ROOT, supplied) == current, "Raw-current source/runtime changed during candidate check")
    write_owned(ROOT, args.output, result)
    print(json.dumps({key: result[key] for key in ("signature_sha256", "eligible", "passed") if key in result}, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        # No source bodies, environment values, API payloads or terminal transcripts.
        print("Offline tooling reuse refused: " + type(error).__name__, file=sys.stderr)
        raise SystemExit(2)
