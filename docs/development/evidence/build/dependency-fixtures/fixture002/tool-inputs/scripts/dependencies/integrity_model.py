"""Strict, standard-library-only dependency receipt/lock/checksum primitives.

These checks establish consistency, not independent artifact trust. No Gradle,
network, publishing or implicit trust-update operation occurs in this module.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import tempfile
import xml.etree.ElementTree as ET

SCHEMA = 1
GRADLE_VERSION = "9.7.1"
CHANGING_POLICY = "component-metadata-and-declared-changing-rejection"
CHANGING_EVIDENCE = "public-metadata-and-declaration-guards"
HOSTS = ("linux-x64", "linux-arm64", "macos-x64", "macos-arm64", "windows-x64")
NAMESPACE = "https://schema.gradle.org/dependency-verification"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COORDINATE = re.compile(r"[A-Za-z0-9_.+\-]{1,240}\Z")
CONFIGURATION = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]{0,239}\Z")
RUN_ID = re.compile(r"[a-z][a-z0-9\-]{0,79}\Z")
PROJECT_PATH = re.compile(r":(?:[A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)*)?\Z")
MAX_JSON = 64 * 1024 * 1024
MAX_XML = 32 * 1024 * 1024
MAX_LOCK = 16 * 1024 * 1024
MAX_ENTRIES = 250_000
COVERAGE_GAPS = (
    "Policy is installed by an explicit init script, not ordinary project build files.",
    "Buildscript configurations are acquired but their versions are not locked by project LockMode.STRICT.",
    "Settings-script/plugin and detached configurations have no complete per-configuration version-lock inventory.",
    "Locally produced/project/file artifacts and downloads outside Gradle dependency resolution are not checksum-verified by this helper.",
    "No independent artifact trust, advisory clearance, platform runtime, release or stable CI gate is established.",
    "Other required host profiles need their own actual acquisition and verification; there is no fallback.",
    "Changing-module rejection observes public component metadata and dependency declarations; it is not an internal Gradle flag attestation or hostile-build sandbox.",
)


class IntegrityError(ValueError):
    """An unsafe, incomplete, inconsistent or unsupported input fails closed."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise IntegrityError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def checked_sha(value: object) -> str:
    require(isinstance(value, str) and SHA256.fullmatch(value), "Expected lowercase SHA256")
    return value


def relative_path(value: object) -> str:
    require(isinstance(value, str) and value and "\\" not in value and "\x00" not in value,
            "Expected a nonempty POSIX-relative path")
    parts = value.split("/")
    require(not PurePosixPath(value).is_absolute() and all(part not in {"", ".", ".."} for part in parts),
            "Path must be relative without empty/dot/parent segments")
    require(not any(ord(char) < 32 for char in value) and ":" not in value,
            "Control characters and drive/URL paths are forbidden")
    return value


def confined(root: Path, value: str, *, must_exist: bool = False) -> Path:
    relative_path(value)
    require(root.is_dir() and not root.is_symlink(), "Workspace root must be a regular directory")
    root = root.resolve()
    current = root
    for part in value.split("/"):
        current = current / part
        require(not current.is_symlink(), "Symlink in an integrity path")
    require(current.resolve().is_relative_to(root), "Integrity path escapes its root")
    if must_exist:
        require(current.exists(), f"Required integrity path is missing: {value}")
    return current


def read_regular(path: Path, limit: int) -> bytes:
    require(not path.is_symlink() and path.is_file(), "Expected a regular non-symlink file")
    before = path.stat()
    require(before.st_size <= limit, "Input exceeds the bounded parser limit")
    with path.open("rb") as stream:
        value = stream.read(limit + 1)
    after = path.stat()
    require(len(value) <= limit and (before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), "Input changed while reading")
    return value


def file_sha256(path: Path) -> str:
    require(not path.is_symlink() and path.is_file(), "Cannot hash a missing/nonregular/symlink input")
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), "Input changed while hashing")
    return digest.hexdigest()


def manifest_digest(files: dict[str, str]) -> str:
    for name, value in files.items():
        relative_path(name)
        checked_sha(value)
    return sha256_bytes("".join(f"{value}  {name}\n" for name, value in sorted(files.items())).encode())


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON object key")
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    try:
        value = json.loads(read_regular(path, MAX_JSON), object_pairs_hook=_unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(IntegrityError("Nonfinite JSON number")))
    except (UnicodeError, json.JSONDecodeError) as failure:
        raise IntegrityError("Malformed JSON input") from failure
    require(isinstance(value, dict), "Expected a JSON object")
    return value


def write_new(path: Path, data: bytes) -> None:
    """Refuse replacement. Link a same-directory temporary file atomically."""
    require(not path.exists() and not path.is_symlink(), "Refusing to overwrite an existing output")
    # Callers select task-owned roots; nevertheless reject symlinked ancestors.
    require(not any(parent.is_symlink() for parent in path.absolute().parents), "Symlink output ancestor")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".dependency-write-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    except FileExistsError as failure:
        raise IntegrityError("Output appeared concurrently; refusing replacement") from failure
    finally:
        Path(temporary).unlink(missing_ok=True)


def host_key(system: str | None = None, machine: str | None = None) -> str:
    system = (platform.system() if system is None else system).lower()
    machine = (platform.machine() if machine is None else machine).lower()
    os_name = {"linux": "linux", "darwin": "macos", "mac os x": "macos", "macos": "macos",
               "windows": "windows"}.get(system)
    arch = {"amd64": "x64", "x86_64": "x64", "x64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(machine)
    result = f"{os_name}-{arch}"
    require(result in HOSTS, "Unsupported actual host; no fallback profile exists")
    return result


def lock_path(project_directory: str, host: str) -> str:
    require(host in HOSTS, "Unknown lock host profile")
    require(project_directory == "." or relative_path(project_directory), "Invalid project directory")
    prefix = "" if project_directory == "." else project_directory + "/"
    return prefix + f"gradle/dependency-locks/{host}.lockfile"


def build_key(build_root: str) -> str:
    if build_root == ".":
        return "root"
    relative_path(build_root)
    return "build-" + sha256_bytes(build_root.encode())[:24]


def part_key(project: str) -> str:
    require(isinstance(project, str) and PROJECT_PATH.fullmatch(project), "Invalid Gradle project path")
    return "project-" + sha256_bytes(project.encode())[:24]


def metadata_path(build_root: str) -> str:
    prefix = "" if build_root == "." else relative_path(build_root) + "/"
    return prefix + "gradle/verification-metadata.xml"


def gav(group: object, module: object, version: object) -> tuple[str, str, str]:
    require(all(isinstance(value, str) and COORDINATE.fullmatch(value) for value in (group, module, version)),
            "Malformed resolved external module coordinate")
    require(not version.upper().endswith("-SNAPSHOT"), "External changing/SNAPSHOT module is outside verified scope")
    return group, module, version


def parse_lock(data: bytes) -> dict[str, frozenset[tuple[str, str, str]]]:
    require(len(data) <= MAX_LOCK, "Lockfile exceeds size limit")
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeError as failure:
        raise IntegrityError("Lockfile is not UTF-8") from failure
    result: dict[str, set[tuple[str, str, str]]] = {}
    empty: set[str] = set()
    seen: set[str] = set()
    for line in lines:
        if not line or line.startswith("#"):
            continue
        require(line == line.strip() and line.count("=") == 1, "Malformed lock line")
        key, names = line.split("=")
        require(key not in seen, "Duplicate lock entry")
        seen.add(key)
        configurations = names.split(",") if names else []
        require(len(configurations) == len(set(configurations)) and
                all(CONFIGURATION.fullmatch(name) for name in configurations), "Invalid/duplicate lock configuration")
        if key == "empty":
            empty.update(configurations)
            for name in configurations:
                result.setdefault(name, set())
        else:
            coordinates = key.split(":")
            require(len(coordinates) == 3 and configurations, "Malformed module lock entry")
            coordinate = gav(*coordinates)
            for name in configurations:
                selected = result.setdefault(name, set())
                require(not any(old[:2] == coordinate[:2] and old != coordinate for old in selected),
                        "Conflicting versions for one locked configuration")
                selected.add(coordinate)
        require(len(seen) <= MAX_ENTRIES, "Too many lock entries")
    require(all(not result[name] for name in empty), "Configuration is both empty and populated in lock state")
    return {key: frozenset(value) for key, value in result.items()}


def verify_configuration_lock(lock: dict, name: str, modules: set[tuple[str, str, str]]) -> None:
    require(name in lock, f"Missing configuration lock state: {name}")
    require(lock[name] == modules, f"Resolved module set differs from exact lock state: {name}")


ArtifactKey = tuple[str, str, str, str]


def parse_metadata(data: bytes) -> dict[ArtifactKey, str]:
    require(len(data) <= MAX_XML, "Verification XML exceeds size limit")
    require(not re.search(br"<!\s*(?:DOCTYPE|ENTITY)", data, re.I), "DTD/entities are forbidden")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as failure:
        raise IntegrityError("Malformed verification XML") from failure
    tag = lambda value: f"{{{NAMESPACE}}}{value}"
    require(root.tag == tag("verification-metadata"), "Wrong verification XML namespace/root")
    require(set(root.attrib) <= {f"{{{XSI}}}schemaLocation"}, "Unexpected verification root attributes")
    require([child.tag for child in root] == [tag("configuration"), tag("components")],
            "Expected exactly configuration and components, without trust bypasses")
    configuration, components = list(root)
    require(not configuration.attrib and not components.attrib, "Unexpected XML container attributes")
    require([child.tag for child in configuration] == [tag("verify-metadata"), tag("verify-signatures")],
            "Only checksum verification with metadata is supported; no trusted/ignored exceptions")
    values = list(configuration)
    require(all(not child.attrib and not list(child) for child in values) and
            values[0].text == "true" and values[1].text == "false", "Metadata verification is required; no invented signing trust")
    result: dict[ArtifactKey, str] = {}
    seen_components: set[tuple[str, str, str]] = set()
    for component in components:
        require(component.tag == tag("component") and set(component.attrib) == {"group", "name", "version"},
                "Malformed verification component")
        coordinates = gav(component.get("group"), component.get("name"), component.get("version"))
        require(coordinates not in seen_components and len(component), "Duplicate or empty verification component")
        seen_components.add(coordinates)
        for artifact in component:
            require(artifact.tag == tag("artifact") and set(artifact.attrib) == {"name"}, "Malformed verification artifact")
            name = artifact.get("name")
            relative_path(name)
            require("/" not in name and len(name) <= 512, "Artifact identity must be a bounded filename")
            require(len(artifact) == 1 and artifact[0].tag == tag("sha256"), "Exactly one SHA256 is required per artifact")
            checksum = artifact[0]
            require(not len(checksum) and set(checksum.attrib) <= {"value", "origin", "reason"},
                    "Alternative hashes/trust constructs are forbidden")
            value = checked_sha(checksum.get("value"))
            key = (*coordinates, name)
            require(key not in result, "Duplicate artifact verification entry")
            result[key] = value
            require(len(result) <= MAX_ENTRIES, "Too many verification artifacts")
    return result


def merge_metadata(inputs: list[dict[ArtifactKey, str]]) -> dict[ArtifactKey, str]:
    require(bool(inputs), "At least one candidate is required")
    result: dict[ArtifactKey, str] = {}
    for incoming in inputs:
        for key, value in incoming.items():
            require(len(key) == 4, "Malformed artifact key")
            gav(*key[:3])
            relative_path(key[3])
            require("/" not in key[3], "Artifact key contains a path")
            checked_sha(value)
            require(key not in result or result[key] == value,
                    "Conflicting SHA256 for one coordinate/artifact; no alternative trust is permitted")
            result[key] = value
    return dict(sorted(result.items()))


def metadata_bytes(entries: dict[ArtifactKey, str]) -> bytes:
    entries = merge_metadata([entries])
    ET.register_namespace("", NAMESPACE)
    ET.register_namespace("xsi", XSI)
    tag = lambda value: f"{{{NAMESPACE}}}{value}"
    root = ET.Element(tag("verification-metadata"), {f"{{{XSI}}}schemaLocation":
        NAMESPACE + " " + NAMESPACE + "/dependency-verification-1.4.xsd"})
    policy = ET.SubElement(root, tag("configuration"))
    ET.SubElement(policy, tag("verify-metadata")).text = "true"
    ET.SubElement(policy, tag("verify-signatures")).text = "false"
    components = ET.SubElement(root, tag("components"))
    previous = None
    for (group, module, version, artifact_name), checksum in entries.items():
        coordinate = (group, module, version)
        if coordinate != previous:
            component = ET.SubElement(components, tag("component"), {"group": group, "name": module, "version": version})
            previous = coordinate
        artifact = ET.SubElement(component, tag("artifact"), {"name": artifact_name})
        ET.SubElement(artifact, tag("sha256"), {"value": checksum, "origin": "Explicit candidate reconciliation; trust level recorded separately"})
    ET.indent(root, space="   ")
    result = ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
    require(parse_metadata(result) == entries, "Internal metadata serialization mismatch")
    return result


def validate_artifact(artifact: dict, modules: set[tuple[str, str, str]]) -> None:
    require(isinstance(artifact, dict), "Artifact receipt must be an object")
    coordinate = gav(artifact.get("group"), artifact.get("module"), artifact.get("version"))
    require(coordinate in modules, "Artifact is not owned by a selected external component")
    name = relative_path(artifact.get("name"))
    require("/" not in name, "Artifact-view filename must not expose a path")
    require(artifact.get("provenance") == "artifact-view-output-unclassified",
            "Artifact-view hashes cannot be presented as registry-original provenance")
    checked_sha(artifact.get("sha256"))
    require(type(artifact.get("size")) is int and artifact["size"] >= 0, "Invalid artifact size")
    require(isinstance(artifact.get("variant_attributes"), dict), "Missing artifact variant attributes")
    kind = artifact.get("content_kind")
    require(kind in {"regular-file", "directory-tree"}, "Unknown artifact content kind")
    if kind == "directory-tree":
        entries = artifact.get("files")
        require(isinstance(entries, list) and len(entries) <= MAX_ENTRIES, "Missing/bounded directory artifact entries")
        hashes: dict[str, str] = {}
        size = 0
        for entry in entries:
            name = relative_path(entry.get("path"))
            require(name not in hashes, "Duplicate directory artifact path")
            hashes[name] = checked_sha(entry.get("sha256"))
            require(type(entry.get("size")) is int and entry["size"] >= 0, "Invalid tree file size")
            size += entry["size"]
        require(manifest_digest(hashes) == artifact["sha256"] and size == artifact["size"], "Directory artifact manifest mismatch")


def validate_project_record(record: dict, *, run_id: str, mode: str, host: str, digest: str,
                            build_root: str, workspace: Path, verify_locks: bool) -> dict:
    """Validate a completed owner's fresh graph. Failed records remain evidence, never success."""
    require(record.get("schema_version") == SCHEMA and record.get("record_type") == "project-graph", "Wrong project receipt schema")
    require(record.get("run_id") == run_id and record.get("mode") == mode and record.get("host") == host and
            record.get("source_input_digest") == digest and record.get("build_root") == build_root,
            "Foreign/stale project receipt identity")
    require(record.get("gradle_version") == GRADLE_VERSION and record.get("java_major") == 17, "Unexpected actual Gradle/JVM runtime")
    require(record.get("complete") is True, "Owner receipt explicitly lacks complete acquisition")
    project = record.get("project_path")
    part_key(project)
    directory = record.get("project_directory")
    require(directory == "." or relative_path(directory), "Invalid owner directory")
    if directory != ".":
        confined(workspace, directory, must_exist=True)
    policy = record.get("policy", {})
    require(isinstance(policy, dict), "Project policy must be an object")
    require(policy.get("project_lock_mode") == "STRICT" and policy.get("project_lock_activation") == "init-script-lockAllConfigurations" and
            policy.get("dependency_verification_mode") == "strict" and policy.get("ignored_dependencies") == [] and
            policy.get("changing_versions_policy") == CHANGING_POLICY,
            "Project locking/checksum policy is not strict")
    expected_lock = lock_path(directory, host)
    require(policy.get("lock_file") == expected_lock, "Lock routing must use the actual owner/host; no fallback")
    inventory = record.get("inventory")
    configurations = record.get("configurations")
    require(isinstance(inventory, list) and isinstance(configurations, list) and len(inventory) <= MAX_ENTRIES,
            "Missing/bounded configuration inventory")
    require(not record.get("inventory_drift") and not record.get("failures"), "Owner inventory drift or failure")
    expected: dict[tuple[str, str], dict] = {}
    for item in inventory:
        require(isinstance(item, dict) and item.get("scope") in {"project", "buildscript"} and
                isinstance(item.get("name"), str) and CONFIGURATION.fullmatch(item["name"]), "Invalid configuration identity")
        key = (item["scope"], item["name"])
        require(key not in expected and type(item.get("can_resolve")) is bool and
                type(item.get("can_consume")) is bool and type(item.get("can_declare")) is bool and
                isinstance(item.get("attributes"), dict) and isinstance(item.get("extends_from"), list),
                "Duplicate/malformed configuration inventory")
        expected[key] = item
    observed: set[tuple[str, str]] = set()
    locked = None
    if verify_locks and any(item["scope"] == "project" and item["can_resolve"] for item in inventory):
        locked = parse_lock(read_regular(confined(workspace, expected_lock, must_exist=True), MAX_LOCK))
    modules_union: set[tuple[str, str, str]] = set()
    artifact_count = 0
    resolved_count = 0
    for item in configurations:
        require(isinstance(item, dict), "Configuration result must be an object")
        key = (item.get("scope"), item.get("name"))
        require(key in expected and key not in observed, "Omitted, duplicate or unclassified configuration")
        observed.add(key)
        source = expected[key]
        require(item.get("inventory") == source, "Configuration attributes/roles changed during acquisition")
        require(not item.get("failures") and not item.get("unresolved"), "Unresolved configuration or artifact failures")
        if not source["can_resolve"]:
            require(item.get("status") == "non-resolvable" and not item.get("components") and not item.get("artifacts"),
                    "Non-resolvable configuration falsely presented as resolved")
            continue
        require(item.get("status") in {"resolved", "empty-resolved"}, "Required configuration is incomplete")
        components = item.get("components")
        artifacts = item.get("artifacts")
        edges = item.get("edges")
        require(isinstance(components, list) and isinstance(artifacts, list) and isinstance(edges, list), "Missing graph or artifacts")
        modules = set()
        component_ids = set()
        script_root_ids = set()
        for component in components:
            require(isinstance(component, dict) and component.get("kind") in {"module", "project", "script-root"},
                    "Unknown component coverage")
            identity = component.get("id")
            require(isinstance(identity, str) and identity and identity not in component_ids, "Missing/duplicate component ID")
            component_ids.add(identity)
            if component["kind"] == "module":
                require(component.get("changing") is False and component.get("changing_evidence") == CHANGING_EVIDENCE,
                        "Changing/unknown external component or unsupported observation basis")
                modules.add(gav(component.get("group"), component.get("module"), component.get("version")))
            elif component["kind"] == "script-root":
                require(source["scope"] == "buildscript" and component.get("scope") == "buildscript" and
                        component.get("configuration") == source["name"] and component.get("project_path") == project and
                        component.get("identity_basis") == "public-RootComponentIdentifier-matched-to-resolution-root" and
                        identity == f"script-root:{project}:{source['name']}" and
                        not any(key in component for key in ("group", "module", "version")),
                        "Synthetic script root is not an explicitly matched owner/configuration root")
                script_root_ids.add(identity)
        require(item.get("root_component_id") in component_ids and len(script_root_ids) <= 1 and
                (not script_root_ids or script_root_ids == {item["root_component_id"]}),
                "Missing resolution root or synthetic root used as an arbitrary graph node")
        for edge in edges:
            require(isinstance(edge, dict) and edge.get("from") in component_ids and edge.get("selected") in component_ids and
                    edge.get("selected") not in script_root_ids and isinstance(edge.get("requested"), str) and
                    type(edge.get("constraint")) is bool,
                    "Malformed or disconnected dependency edge")
        seen_artifacts = set()
        for artifact in artifacts:
            validate_artifact(artifact, modules)
            identity = json.dumps({key: artifact[key] for key in ("group", "module", "version", "name", "variant_attributes", "sha256")}, sort_keys=True)
            require(identity not in seen_artifacts, "Duplicate artifact receipt")
            seen_artifacts.add(identity)
        require((item["status"] == "empty-resolved") == (not modules and not artifacts), "Incorrect empty-configuration claim")
        if source["scope"] == "project":
            require(item.get("lock_coverage") == "strict-project-init-script", "Missing project lock coverage")
            if verify_locks:
                verify_configuration_lock(locked, source["name"], modules)
        else:
            require(item.get("lock_coverage") == "not-covered-buildscript", "Project locking cannot be claimed for a script provider")
        modules_union.update(modules)
        artifact_count += len(artifacts)
        resolved_count += 1
    require(observed == set(expected), "Configuration inventory is not completely accounted for")
    return {"project": project, "project_directory": directory, "configurations": len(expected),
            "resolved_configurations": resolved_count, "artifact_view_outputs": artifact_count,
            "external_modules": sorted(modules_union), "lock_file": expected_lock if locked is not None else None}
