#!/usr/bin/env python3
"""Inspect staged Maven artifacts, not producer classes/build-directory substitutes.

Pure standard-library, read-only (apart from the requested JSON receipt). No network,
publication, ZIP extraction or Gradle execution. A successful result certifies these
static checks ONLY, never native GUI/device behavior, ABI compatibility or release readiness.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys
import tomllib
from typing import Any
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
GROUP = "io.github.apdelrahman1911.nativecmpkit"
DESTINATION = "https://github.com/Apdelrahman1911/nativeCmpkit"
TARGET_SUFFIXES = {
    "metadata": "", "android": "-android", "desktop": "-desktop", "js": "-js",
    "wasmJs": "-wasm-js", "iosArm64": "-iosarm64", "iosSimulatorArm64": "-iossimulatorarm64",
}
NATIVE_PLATFORMS = ("linux-x64", "linux-arm64", "macos-x64", "macos-arm64", "windows-x64")
NATIVE_MODULES = {"nativecmpkit-file-picker": "calf-file-picker", "nativecmpkit-share": "calf-share"}
NATIVE_NAMES = {"calf-file-picker": "calf_filepicker_native", "calf-share": "calf_share_native"}
NOTICE_PREFIX = "META-INF/nativecmpkit/"
MAX_METADATA = 8 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 100_000
MAX_ARCHIVE_TOTAL = 1024 * 1024 * 1024
MAX_ARCHIVE_ENTRY = 256 * 1024 * 1024
SAFE_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?\Z")
CRATE_NAME = re.compile(r"[A-Za-z0-9_-]+\Z")
CRATE_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?(?:\+[A-Za-z0-9.-]+)?\Z")
CHECKSUM = re.compile(r"[0-9a-f]{64}\Z")
NATIVE_CRATE_NAMES = {"calf-file-picker": "calf-filepicker-native", "calf-share": "calf-share-native"}
NATIVE_METADATA_SCOPE = "Conservative unfiltered locked Cargo union; no compile or license certification"
NATIVE_LICENSE_NAME = re.compile(r"(?:LICEN[CS]E|COPYING|NOTICE|COPYRIGHT|UNLICENSE)(?:[._ -].*)?\Z", re.I)
SOURCE_EXTENSIONS = {".rs", ".kt", ".kts", ".java", ".c", ".cc", ".cpp", ".h", ".hh", ".hpp",
                     ".m", ".mm", ".go", ".js", ".ts", ".jsx", ".tsx", ".py", ".rb", ".swift",
                     ".cs", ".php", ".sh", ".bat", ".ps1"}


class InvalidArtifact(ValueError):
    pass


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidArtifact(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_bytes(data: bytes) -> Any:
    if len(data) > MAX_METADATA:
        raise InvalidArtifact("JSON metadata exceeds size limit")
    try:
        return json.loads(data, object_pairs_hook=unique_pairs)
    except (ValueError, UnicodeDecodeError) as exc:
        raise InvalidArtifact(f"Invalid JSON: {exc}") from exc


def relative_notice_path(value: Any) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or any(c in value for c in ("\\", ":", "\x00")):
        raise InvalidArtifact("Notice path must be a canonical relative path")
    path = PurePosixPath(value)
    if ".." in path.parts or path.as_posix() != value or not path.parts:
        raise InvalidArtifact("Notice path must be a canonical relative path")
    return value


def autodiscovered_license_path(value: str) -> bool:
    path = PurePosixPath(value)
    # E.g. objc2-foundation/src/copying.rs implements object copying; it is NOT
    # permission text. An explicitly declared license_file is handled separately.
    return bool(NATIVE_LICENSE_NAME.fullmatch(path.name)) and path.suffix.lower() not in SOURCE_EXTENSIONS


def validate_native_metadata(data: Any, module: str) -> dict[str, dict[str, Any]]:
    """Refuse raw Cargo/machine metadata before copying it into distributable notices.

    This validates the build helper's *sanitized* schema, not registry authenticity
    or SPDX obligations. Do not accept unknown fields and accidentally redistribute
    manifest paths, source URLs, environment fields or arbitrary tool output.
    """
    keys = {"schema_version", "module", "target_filter", "scope", "cargo_toml_sha256",
            "cargo_lock_sha256", "packages", "resolve"}
    if not isinstance(data, dict) or set(data) != keys or module not in NATIVE_CRATE_NAMES:
        raise InvalidArtifact("Expected exact sanitized native metadata schema")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1 or data["module"] != module:
        raise InvalidArtifact("Unsupported native metadata module/schema")
    if data["target_filter"] is not None or data["scope"] != NATIVE_METADATA_SCOPE:
        raise InvalidArtifact("Expected explicitly unfiltered sanitized locked target union")
    if any(not isinstance(data[key], str) or not CHECKSUM.fullmatch(data[key])
           for key in ("cargo_toml_sha256", "cargo_lock_sha256")):
        raise InvalidArtifact("Missing exact locked input hashes")
    packages, nodes = data["packages"], data["resolve"]
    if not isinstance(packages, list) or not 1 <= len(packages) <= 10_000 or not isinstance(nodes, list):
        raise InvalidArtifact("Expected bounded sanitized package/resolve records")
    result, local_roots = {}, 0
    package_keys = {"id", "name", "version", "source_kind", "checksum", "license", "license_file"}
    for package in packages:
        if not isinstance(package, dict) or set(package) != package_keys:
            raise InvalidArtifact("Unexpected package metadata fields")
        name, version = package["name"], package["version"]
        if not isinstance(name, str) or not CRATE_NAME.fullmatch(name) or not isinstance(version, str) or not CRATE_VERSION.fullmatch(version):
            raise InvalidArtifact("Invalid sanitized package identity")
        identity = name + "@" + version
        if package["id"] != identity or identity in result:
            raise InvalidArtifact("Duplicate or ambiguous sanitized package identity")
        if package["source_kind"] == "local-root":
            local_roots += 1
            if name != NATIVE_CRATE_NAMES[module] or package["checksum"] is not None:
                raise InvalidArtifact("Unexpected native path/local dependency")
        elif package["source_kind"] == "crates.io":
            if not isinstance(package["checksum"], str) or not CHECKSUM.fullmatch(package["checksum"]):
                raise InvalidArtifact("Registry package lacks locked checksum")
        else:
            raise InvalidArtifact("Unreviewed dependency source kind")
        license_expression = package["license"]
        if license_expression is not None and (not isinstance(license_expression, str)
                or len(license_expression) > 1024 or any(c in license_expression for c in ("\x00", "\n", "\r"))):
            raise InvalidArtifact("Invalid declared license expression")
        if package["license_file"] is not None:
            relative_notice_path(package["license_file"])
        result[identity] = package
    if local_roots != 1:
        raise InvalidArtifact("Exactly the owning native crate must be the local root")
    node_ids = set()
    for node in nodes:
        if not isinstance(node, dict) or set(node) != {"id", "dependencies"}:
            raise InvalidArtifact("Unexpected sanitized dependency graph fields")
        identity, dependencies = node["id"], node["dependencies"]
        if not isinstance(identity, str) or identity not in result or identity in node_ids:
            raise InvalidArtifact("Unknown/duplicate sanitized dependency node")
        if (not isinstance(dependencies, list) or any(not isinstance(dep, str) or dep not in result for dep in dependencies)
                or len(set(dependencies)) != len(dependencies)):
            raise InvalidArtifact("Invalid/unresolved sanitized dependency edge")
        node_ids.add(identity)
    if node_ids != set(result):
        raise InvalidArtifact("Incomplete sanitized dependency node inventory")
    return result


def load_xml(data: bytes) -> ET.Element:
    if len(data) > MAX_METADATA:
        raise InvalidArtifact("XML metadata exceeds size limit")
    # Accept UTF-8 only: encoded declarations must not bypass the DTD/entity rejection.
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidArtifact("Only UTF-8 XML metadata is accepted") from exc
    if "\x00" in text or re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
        raise InvalidArtifact("DTD/entity declarations are forbidden")
    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:
        raise InvalidArtifact(f"Invalid XML: {exc}") from exc


def local_file(repository: Path, base: Path, url: str) -> Path:
    """Allow Maven's ../ sibling URLs, but never remote URLs, credentials or escapes."""
    if not isinstance(url, str) or not url or "\\" in url:
        raise InvalidArtifact("Invalid local artifact URL")
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise InvalidArtifact("Non-local or parameterized artifact URL")
    decoded = unquote(parsed.path)
    if decoded.startswith("/") or "\x00" in decoded or "\\" in decoded or ":" in decoded:
        raise InvalidArtifact("Absolute/invalid artifact URL")
    # Do not allow a second decoder to reinterpret an encoded escape differently.
    if re.search(r"%[0-9a-fA-F]{2}", decoded):
        raise InvalidArtifact("Multiply encoded artifact URL")
    candidate = base / decoded
    resolved = candidate.resolve()
    try:
        resolved.relative_to(repository.resolve())
    except ValueError as exc:
        raise InvalidArtifact("Artifact URL escapes candidate repository") from exc
    # Reject symlinks even if they currently point inside the repository.
    current = candidate
    while current != current.parent and current != repository:
        if current.is_symlink():
            raise InvalidArtifact("Symlinked artifact path")
        current = current.parent
    if not resolved.is_file():
        raise InvalidArtifact("Referenced artifact does not exist")
    return resolved


def archive_names(archive: zipfile.ZipFile) -> set[str]:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_ENTRIES:
        raise InvalidArtifact("Archive entry limit exceeded")
    if sum(entry.file_size for entry in infos) > MAX_ARCHIVE_TOTAL:
        raise InvalidArtifact("Archive uncompressed size limit exceeded")
    names = set()
    for entry in infos:
        name = entry.filename
        parts = PurePosixPath(name).parts
        if not name or name.startswith("/") or "\\" in name or ":" in name or "\x00" in name or ".." in parts:
            raise InvalidArtifact("Unsafe archive entry path")
        if name in names:
            raise InvalidArtifact("Duplicate archive entry path")
        names.add(name)
        if entry.file_size > MAX_ARCHIVE_ENTRY:
            raise InvalidArtifact("Archive entry size limit exceeded")
        if stat.S_ISLNK(entry.external_attr >> 16):
            raise InvalidArtifact("Symlink archive entry")
    return names


def native_filename(module: str, platform: str) -> str:
    name = NATIVE_NAMES[module]
    if platform.startswith("windows-"):
        return name + ".dll"
    return "lib" + name + (".dylib" if platform.startswith("macos-") else ".so")


def binary_platform(data: bytes, platform: str) -> bool:
    """Verify thin object header OS/CPU, not ABI/glibc/SDK compatibility or authenticity."""
    if platform.startswith("linux-"):
        if len(data) < 20 or data[:4] != b"\x7fELF" or data[4] != 2 or data[5] not in (1, 2):
            return False
        machine = struct.unpack_from("<H" if data[5] == 1 else ">H", data, 18)[0]
        return machine == (183 if platform.endswith("arm64") else 62)
    if platform.startswith("macos-"):
        if len(data) < 8 or data[:4] not in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf"):
            return False
        machine = struct.unpack_from("<I" if data[:4] == b"\xcf\xfa\xed\xfe" else ">I", data, 4)[0]
        return machine == (0x0100000C if platform.endswith("arm64") else 0x01000007)
    if platform.startswith("windows-"):
        if len(data) < 64 or data[:2] != b"MZ":
            return False
        offset = struct.unpack_from("<I", data, 0x3C)[0]
        if offset + 6 > len(data) or data[offset:offset + 4] != b"PE\0\0":
            return False
        machine = struct.unpack_from("<H", data, offset + 4)[0]
        return machine == (0xAA64 if platform.endswith("arm64") else 0x8664)
    return False


def source_digest(files: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{files[path]}  {path}\n" for path in sorted(files)).encode()).hexdigest()


class ArtifactVerifier:
    def __init__(self, source_root: Path, repository: Path, version: str,
                 modules: list[str] | None = None, targets: list[str] | None = None,
                 native_platforms: list[str] | None = None):
        self.root = source_root.resolve()
        self.repository = repository.resolve()
        if not self.repository.is_dir():
            raise InvalidArtifact("Candidate Maven repository is not a directory")
        if not SAFE_VERSION.fullmatch(version) or version.endswith("-SNAPSHOT"):
            raise InvalidArtifact("Use an exact non-SNAPSHOT local candidate version; timestamped snapshot repos are not this release gate")
        self.version = version
        identity = load_json_bytes((self.root / "docs/migration/identity.json").read_bytes())
        self.all_modules = sorted(item["new_artifact"] for item in identity["modules"])
        if len(set(self.all_modules)) != len(self.all_modules):
            raise InvalidArtifact("Duplicate identity artifact")
        self.modules = sorted(set(modules or self.all_modules))
        self.targets = list(dict.fromkeys(["metadata", *(targets or TARGET_SUFFIXES)]))
        self.native_platforms = list(dict.fromkeys(native_platforms or NATIVE_PLATFORMS))
        if not set(self.modules).issubset(self.all_modules):
            raise InvalidArtifact("Unknown selected module")
        if not set(self.targets).issubset(TARGET_SUFFIXES):
            raise InvalidArtifact("Unknown selected target")
        if not set(self.native_platforms).issubset(NATIVE_PLATFORMS):
            raise InvalidArtifact("Unsupported selected native platform")
        self.expected_coordinates = {
            module + TARGET_SUFFIXES[target]
            for module in self.modules for target in self.targets
        }
        self.all_coordinates = {
            module + suffix for module in self.all_modules for suffix in TARGET_SUFFIXES.values()
        }
        self.checks: list[dict[str, Any]] = []
        self.files: dict[str, dict[str, Any]] = {}
        self.native_receipts: list[dict[str, Any]] = []
        self.class_owners: dict[str, set[str]] = {}
        self.checked_archives: set[str] = set()
        self.expected_notices = {
            name: (self.root / name).read_bytes()
            for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md")
        }
        for path in sorted((self.root / "licenses").rglob("*")):
            if path.is_file():
                self.expected_notices[path.relative_to(self.root).as_posix()] = path.read_bytes()

    def check(self, name: str, passed: bool, detail: str) -> bool:
        self.checks.append({"name": name, "passed": bool(passed), "detail": detail})
        return bool(passed)

    def record(self, path: Path) -> None:
        relative = path.relative_to(self.repository).as_posix()
        self.files[relative] = {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}

    def file(self, directory: Path, name: str, label: str) -> Path | None:
        try:
            path = local_file(self.repository, directory, name)
            self.record(path)
            return path
        except InvalidArtifact as exc:
            self.check(label, False, str(exc))
            return None

    def dependency(self, group: str | None, artifact: str | None, version: str | None, label: str) -> None:
        self.check(label + ":upstream-independent", group != "com.mohamedrejeb.calf", "No dependency on original Calf artifacts")
        if group == GROUP:
            self.check(label + ":candidate-identity", artifact in self.all_coordinates and version == self.version,
                       "Internal dependency uses a known independently named artifact and exact candidate version")

    def pom(self, path: Path, coordinate: str) -> None:
        try:
            root = load_xml(path.read_bytes())
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            value = lambda field: root.findtext("m:" + field, namespaces=ns)
            self.check(coordinate + ":pom-identity", (value("groupId"), value("artifactId"), value("version")) == (GROUP, coordinate, self.version),
                       "POM group/artifact/version exactly match candidate coordinate")
            # Target POMs use their library root's display name, not a changed
            # Maven artifact ID or retained Gradle project/resource filename.
            roots = [module for module in self.all_modules
                     if coordinate in {module + suffix for suffix in TARGET_SUFFIXES.values()}]
            expected_name = "NativeCmpKit - " + roots[0].removeprefix("nativecmpkit-") if len(roots) == 1 else None
            self.check(coordinate + ":pom-display-name", expected_name is not None and value("name") == expected_name,
                       "Current NativeCmpKit display name and exact owning module; lowercase coordinates remain stable")
            self.check(coordinate + ":pom-license", root.findtext("m:licenses/m:license/m:name", namespaces=ns) == "Apache-2.0", "Apache-2.0 POM declaration")
            self.check(coordinate + ":pom-url", value("url") == DESTINATION, "Independent project URL")
            self.check(coordinate + ":pom-scm", root.findtext("m:scm/m:url", namespaces=ns) == DESTINATION, "Independent SCM URL")
            developers = {node.text for node in root.findall("m:developers/m:developer/m:id", ns)}
            self.check(coordinate + ":pom-attribution", {"Apdelrahman1911", "MohamedRejeb"}.issubset(developers), "Maintainer and upstream author attribution")
            for index, dependency in enumerate(root.findall("m:dependencies/m:dependency", ns)):
                group, artifact, version = (dependency.findtext("m:" + key, namespaces=ns) for key in ("groupId", "artifactId", "version"))
                self.dependency(group, artifact, version, f"{coordinate}:pom-dependency-{index}")
                if group == "org.openjfx":
                    classifier = dependency.findtext("m:classifier", namespaces=ns)
                    self.check(f"{coordinate}:pom-javafx-host-neutral-{index}", classifier is None,
                               "No publisher-selected JavaFX classifier in generic published POM")
        except InvalidArtifact as exc:
            self.check(coordinate + ":pom-parse", False, str(exc))

    def notices(self, archive: zipfile.ZipFile, names: set[str], label: str, prefix: str = NOTICE_PREFIX) -> None:
        for name, data in self.expected_notices.items():
            entry = prefix + name
            self.check(label + ":notice:" + name, entry in names and archive.read(entry) == data,
                       "Complete source notice bytes accompany this coordinate")

    def native(self, archive: zipfile.ZipFile, names: set[str], module: str, platform: str, label: str) -> None:
        filename = native_filename(module, platform)
        payload_path = f"native/{platform}/{filename}"
        manifest_path = f"META-INF/nativecmpkit/native/{module}/{platform}.json"
        if not self.check(label + ":native-present:" + platform, payload_path in names and manifest_path in names,
                          "Exact module native payload and per-platform provenance manifest present"):
            return
        try:
            payload = archive.read(payload_path)
            manifest = load_json_bytes(archive.read(manifest_path))
            self.check(label + ":native-machine:" + platform, binary_platform(payload, platform), "Thin native object OS/CPU header matches slot")
            self.check(label + ":native-manifest-identity:" + platform,
                       type(manifest.get("schemaVersion")) is int and manifest.get("schemaVersion") == 1
                       and manifest.get("module") == module and manifest.get("platform") == platform
                       and type(manifest.get("abiVersion")) is int and manifest.get("abiVersion") == 1
                       and manifest.get("filename") == filename and manifest.get("libraryVersion") == self.version,
                       "Manifest format/module/platform/JNI ABI/filename match expected contract")
            self.check(label + ":native-bytes:" + platform,
                       manifest.get("sha256") == hashlib.sha256(payload).hexdigest()
                       and type(manifest.get("size")) is int and manifest.get("size") == len(payload),
                       "Native payload SHA256 and size equal manifest")
            files = manifest.get("sourceFiles")
            valid_source_map = isinstance(files, dict) and bool(files) and all(isinstance(k, str) and isinstance(v, str) and re.fullmatch("[0-9a-f]{64}", v) for k, v in files.items())
            if self.check(label + ":native-source-map:" + platform, valid_source_map, "Native source inventory is nonempty and hash-addressed"):
                self.check(label + ":native-source-digest:" + platform, manifest.get("sourceSha256") == source_digest(files), "Deterministic source inventory digest matches")
                # Import the repository's pure stdlib inventory oracle; never code from the package.
                contract_path = self.root / "scripts/native/artifacts.py"
                if contract_path.is_file():
                    spec = importlib.util.spec_from_file_location("nativecmpkit_native_artifact_contract", contract_path)
                    contract = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = contract
                    spec.loader.exec_module(contract)
                    expected = contract.expected_source_files(self.root, module)
                    self.check(label + ":native-source-complete:" + platform, files == expected,
                               "Native source inventory equals the complete current contract, not a selected subset")
                    props = contract.SUPPORTED_PLATFORMS[platform]
                    rust_target = props.get("rustTarget", props.get("target")) if isinstance(props, dict) else None
                    if rust_target:
                        self.check(label + ":native-rust-target:" + platform, manifest.get("rustTarget") == rust_target, "Rust target matches platform")
                    pinned = contract.toolchain(self.root)
                    self.check(label + ":native-toolchain:" + platform,
                               manifest.get("rustToolchain") == pinned
                               and str(manifest.get("rustcVersion", "")).startswith(f"rustc {pinned} ")
                               and str(manifest.get("cargoVersion", "")).startswith(f"cargo {pinned} ")
                               and manifest.get("crateVersion") == contract.crate_version(self.root, module),
                               "Actual compiler/Cargo/crate versions match independently configured source contract")
                else:
                    self.check(label + ":native-source-complete:" + platform, False, "Native source completeness oracle missing")
            self.check(label + ":native-release-profile:" + platform, manifest.get("cargoProfile") == "release" and manifest.get("rustFlags") == [], "Unmodified release profile payload")
            self.check(label + ":native-revision:" + platform,
                       isinstance(manifest.get("sourceRevision"), str) and bool(re.fullmatch("[0-9a-f]{40}", manifest["sourceRevision"])),
                       "Full source revision recorded; source-tree dirtiness separately retained")
            self.check(label + ":native-dirty-flag:" + platform, isinstance(manifest.get("sourceTreeDirty"), bool), "Source dirtiness explicitly recorded")
            self.native_receipts.append({"module": module, "platform": platform, "sourceRevision": manifest.get("sourceRevision"),
                                         "sourceTreeDirty": manifest.get("sourceTreeDirty"), "sha256": manifest.get("sha256")})
        except (ValueError, AttributeError, KeyError, TypeError, OSError, ImportError) as exc:
            self.check(label + ":native-manifest-parse:" + platform, False, str(exc))

    def native_notices(self, archive: zipfile.ZipFile, names: set[str], module: str, label: str) -> None:
        prefix = f"META-INF/nativecmpkit/native-dependencies/{module}/"
        report_path, metadata_path = prefix + "licenses-report.json", prefix + "metadata.json"
        if not self.check(label + ":native-license-report", report_path in names and metadata_path in names,
                          "Owning native module includes exact dependency notice report and sanitized locked metadata"):
            return
        try:
            report = load_json_bytes(archive.read(report_path))
            metadata_bytes = archive.read(metadata_path)
            metadata = load_json_bytes(metadata_bytes)
            sanitized_packages = validate_native_metadata(metadata, module)
            if not isinstance(report, dict) or type(report.get("schema_version")) is not int:
                raise InvalidArtifact("Expected a native dependency notice report")
            self.check(label + ":native-license-metadata-hash", report.get("metadata_sha256") == hashlib.sha256(metadata_bytes).hexdigest(),
                       "Dependency notice report binds the accompanying sanitized metadata")
            self.check(label + ":native-license-collection-complete",
                       report.get("schema_version") == 1 and report.get("module") == module
                       and report.get("complete_material_collection") is True and report.get("gaps") == [],
                       "No missing dependency license material; legal clearance still requires separate review")
            self.check(label + ":native-license-metadata-scope", metadata.get("module") == module and metadata.get("target_filter", "absent") is None,
                       "Conservative unfiltered locked native graph, not only publisher host dependencies")
            manifest = self.root / module / "native/Cargo.toml"
            lockfile = self.root / module / "native/Cargo.lock"
            self.check(label + ":native-license-inputs",
                       manifest.is_file() and lockfile.is_file()
                       and report.get("cargo_toml_sha256") == metadata.get("cargo_toml_sha256") == sha256(manifest)
                       and report.get("cargo_lock_sha256") == metadata.get("cargo_lock_sha256") == sha256(lockfile),
                       "Native license graph belongs to the candidate's exact manifest/lockfile")
            lock = tomllib.loads(lockfile.read_text())
            if any(package.get("source") not in (None, "registry+https://github.com/rust-lang/crates.io-index")
                   for package in lock["package"]):
                raise InvalidArtifact("Unreviewed locked native dependency source")
            expected = {(package["name"], package["version"]): package["checksum"] for package in lock["package"]
                        if package.get("source") == "registry+https://github.com/rust-lang/crates.io-index"}
            packages = report.get("packages", [])
            if not isinstance(packages, list) or any(not isinstance(package, dict) for package in packages):
                raise InvalidArtifact("Expected dependency notice package records")
            keys = ("name", "version", "source_kind", "license", "checksum")
            represented = {}
            for package in packages:
                name, version = package.get("name"), package.get("version")
                if not isinstance(name, str) or not CRATE_NAME.fullmatch(name) or not isinstance(version, str) or not CRATE_VERSION.fullmatch(version):
                    raise InvalidArtifact("Invalid dependency license package identity")
                identity = name + "@" + version
                if identity in represented:
                    raise InvalidArtifact("Duplicate dependency notice package record")
                represented[identity] = {key: package.get(key) for key in keys}
                if package.get("source_kind") == "local-root" and package.get("files") != []:
                    raise InvalidArtifact("Root notices are separate; unexpected root dependency license files")
            declared = {identity: {key: package[key] for key in keys} for identity, package in sanitized_packages.items()}
            self.check(label + ":native-license-metadata-packages", represented == declared,
                       "Notice records and sanitized dependency graph contain exactly the same packages/checksums/license declarations")
            actual = {(package.get("name"), package.get("version")): package.get("checksum") for package in packages if package.get("source_kind") == "crates.io"}
            registry_packages = [package for package in packages if package.get("source_kind") == "crates.io"]
            metadata_actual = {(package["name"], package["version"]): package["checksum"]
                               for package in sanitized_packages.values() if package["source_kind"] == "crates.io"}
            self.check(label + ":native-license-lock-coverage", bool(expected) and actual == expected and len(actual) == len(registry_packages),
                       "Every locked registry crate has a distinct same-checksum notice record")
            self.check(label + ":native-license-metadata-lock-coverage", metadata_actual == expected,
                       "Sanitized graph contains the entire conservative locked registry union")
            expected_entries = {report_path, metadata_path}
            for package in registry_packages:
                name, version = package.get("name"), package.get("version")
                package_label = label + ":crate-license:" + str(name) + "@" + str(version)
                entries = package.get("files")
                if not self.check(package_label + ":text-present", isinstance(entries, list) and bool(entries), "SPDX string alone is not permission/copyright text"):
                    continue
                package_prefix = prefix + name + "-" + version + "/"
                for entry in entries:
                    path = relative_notice_path(entry.get("path", ""))
                    safe = path.startswith(package_prefix) and path not in expected_entries
                    if not self.check(package_label + ":entry-path:" + str(path), safe and path in names,
                                      "Unique complete license file at the owning crate's scoped path"):
                        continue
                    expected_entries.add(path)
                    declared_license_file = sanitized_packages[name + "@" + version]["license_file"]
                    self.check(package_label + ":entry-kind:" + path,
                               autodiscovered_license_path(path) or path[len(package_prefix):] == declared_license_file,
                               "License/notice material or explicit author-declared license_file, not a similarly named source implementation")
                    content = archive.read(path)
                    self.check(package_label + ":entry-bytes:" + path,
                               type(entry.get("bytes")) is int and 0 < len(content) <= 1024 * 1024
                               and len(content) == entry["bytes"] and hashlib.sha256(content).hexdigest() == entry.get("sha256"),
                               "Exact complete collected license text bytes/hash, not a truncated summary")
                    try:
                        content.decode("utf-8-sig")
                        readable = b"\x00" not in content
                    except UnicodeDecodeError:
                        readable = False
                    self.check(package_label + ":entry-text:" + path, readable, "Readable complete license text, not binary material")
            actual_entries = {name for name in names if name.startswith(prefix) and not name.endswith("/")}
            self.check(label + ":native-license-no-stale-material", actual_entries == expected_entries,
                       "No missing/unrecorded stale native dependency notice files")
        except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
            self.check(label + ":native-license-parse", False, str(exc))

    def archive(self, path: Path, coordinate: str, module: str, target: str, companion: bool = False) -> None:
        relative = path.relative_to(self.repository).as_posix()
        if relative in self.checked_archives:
            return
        self.checked_archives.add(relative)
        companion = companion or path.name == f"{coordinate}-{self.version}-notices.zip"
        label = coordinate + ":archive:" + path.name
        try:
            with zipfile.ZipFile(path) as archive:
                names = archive_names(archive)
                self.check(label + ":crc", archive.testzip() is None, "Archive CRC check; no extraction")
                primary = path.name == f"{coordinate}-{self.version}.jar" or path.name == f"{coordinate}-{self.version}.aar"
                if companion:
                    self.notices(archive, names, label)
                    if module in NATIVE_MODULES:
                        self.native_notices(archive, names, NATIVE_MODULES[module], label)
                elif primary:
                    retained_module = "calf-" + module.removeprefix("nativecmpkit-")
                    self.notices(archive, names, label, NOTICE_PREFIX + retained_module + "/")
                # KLIBs are not mutated to insert legal text; the verified same-coordinate ZIP accompanies them.
                native_entries = {name for name in names if name.startswith("native/") and not name.endswith("/")}
                if target == "desktop" and primary and module in NATIVE_MODULES:
                    native_module = NATIVE_MODULES[module]
                    permitted = {f"native/{platform}/{native_filename(native_module, platform)}" for platform in NATIVE_PLATFORMS}
                    self.check(label + ":native-module-isolation", native_entries.issubset(permitted), "No foreign module/unknown-platform native payload")
                    for platform in self.native_platforms:
                        self.native(archive, names, native_module, platform, label)
                elif target == "desktop" and primary:
                    self.check(label + ":no-unrelated-native", not native_entries, "Only owning modules package native JNI payloads")
                if target == "desktop" and primary:
                    for name in names:
                        if name.endswith(".class") and not name.startswith("META-INF/"):
                            self.class_owners.setdefault(name, set()).add(coordinate)
                fonts = [name for name in names if name.endswith("/sf_symbols.ttf")]
                if target == "desktop" and primary and module == "nativecmpkit-cupertino-icons":
                    self.check(label + ":retained-font-resource", fonts == [
                        "composeResources/com.mohamedrejeb.calf.calf_cupertino_icons.generated.resources/font/sf_symbols.ttf"],
                        "Exactly the retained generated-resource font path is packaged")
                for font in fonts:
                    self.check(label + ":font-provenance", hashlib.sha256(archive.read(font)).hexdigest() == "67c44fe9183b002e79dde7f6977e2988661c9a3e4a3c5fce968787efdbed823c",
                               "Retained Cupertino font bytes match pinned MIT source (not Apple SF Symbols)")
        except (InvalidArtifact, zipfile.BadZipFile, RuntimeError, OSError) as exc:
            self.check(label + ":valid-archive", False, str(exc))

    @staticmethod
    def metadata_variants(data: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
        variants = data.get("variants")
        if not isinstance(variants, list) or not 1 <= len(variants) <= 10_000:
            return None
        result = {}
        for variant in variants:
            if not isinstance(variant, dict) or not isinstance(variant.get("name"), str) or not variant["name"]:
                return None
            if variant["name"] in result or not isinstance(variant.get("attributes", {}), dict):
                return None
            result[variant["name"]] = variant
        return result

    def module_identity(self, data: Any, path: Path, coordinate: str, module: str, target: str) -> bool:
        """GMM may describe the owning KMP component, not this file's coordinate.

        Gradle9.7.1 writes the owner's coordinates and relative URL into child
        metadata. Admit only an exact same-version canonical root back-pointer
        with reciprocal names/attributes/target redirects; never arbitrary URLs,
        sibling modules, recursive owners or a value-only identity shortcut.
        """
        if not isinstance(data, dict) or data.get("formatVersion") != "1.1":
            return False
        component = data.get("component")
        if not isinstance(component, dict) or not isinstance(component.get("attributes", {}), dict):
            return False
        identity = (component.get("group"), component.get("module"), component.get("version"))
        if identity == (GROUP, coordinate, self.version):
            return "url" not in component and self.metadata_variants(data) is not None
        if target == "metadata" or identity != (GROUP, module, self.version):
            return False
        owner_url = f"../../{module}/{self.version}/{module}-{self.version}.module"
        if component.get("url") != owner_url:
            return False
        owner_path = self.file(path.parent, owner_url, coordinate + ":owning-root-metadata")
        if owner_path is None:
            return False
        owner = load_json_bytes(owner_path.read_bytes())
        if not isinstance(owner, dict) or owner.get("formatVersion") != "1.1":
            return False
        owner_component = owner.get("component")
        if not isinstance(owner_component, dict) or "url" in owner_component:
            return False
        if (owner_component.get("group"), owner_component.get("module"), owner_component.get("version")) != (GROUP, module, self.version):
            return False
        if owner_component.get("attributes", {}) != component.get("attributes", {}):
            return False
        owner_variants, target_variants = self.metadata_variants(owner), self.metadata_variants(data)
        if owner_variants is None or target_variants is None:
            return False
        expected_redirect = {
            "group": GROUP, "module": coordinate, "version": self.version,
            "url": f"../../{coordinate}/{self.version}/{coordinate}-{self.version}.module",
        }
        redirects = {
            name: variant for name, variant in owner_variants.items()
            if isinstance(variant.get("available-at"), dict)
            and variant["available-at"].get("module") == coordinate
        }
        return set(redirects) == set(target_variants) and all(
            redirects[name]["available-at"] == expected_redirect
            and redirects[name].get("attributes", {}) == variant.get("attributes", {})
            for name, variant in target_variants.items()
        )

    def metadata(self, path: Path, coordinate: str, module: str, target: str) -> None:
        try:
            data = load_json_bytes(path.read_bytes())
            if not self.check(coordinate + ":module-identity", self.module_identity(data, path, coordinate, module, target),
                              "Exact direct coordinate, or canonical same-version KMP owner with reciprocal target variants"):
                return
            variants = data.get("variants")
            if not self.check(coordinate + ":module-variants", isinstance(variants, list) and bool(variants), "Nonempty Gradle variant metadata"):
                return
            available = set()
            referenced_primary = False
            extension = ".jar" if target in ("metadata", "desktop") else ".aar" if target == "android" else ".klib"
            primary_name = f"{coordinate}-{self.version}{extension}"
            for index, variant in enumerate(variants):
                label = f"{coordinate}:variant-{index}"
                redirect = variant.get("available-at")
                if redirect:
                    self.dependency(redirect.get("group"), redirect.get("module"), redirect.get("version"), label + ":available-at")
                    available.add(redirect.get("module"))
                    if redirect.get("module") in self.expected_coordinates:
                        self.file(path.parent, redirect.get("url", ""), label + ":redirect-file")
                for dep_index, dependency in enumerate(variant.get("dependencies", [])):
                    version = dependency.get("version", {})
                    self.dependency(dependency.get("group"), dependency.get("module"), version.get("strictly", version.get("requires")), f"{label}:dependency-{dep_index}")
                    if dependency.get("group") == "org.openjfx":
                        selector = dependency.get("thirdPartyCompatibility", {}).get("artifactSelector", {})
                        self.check(f"{label}:javafx-host-neutral-{dep_index}", not selector.get("classifier"), "Generic published module has no producer OS classifier")
                for file_index, entry in enumerate(variant.get("files", [])):
                    file_label = f"{label}:file-{file_index}"
                    artifact_path = self.file(path.parent, entry.get("url", ""), file_label + ":present")
                    if artifact_path is None:
                        continue
                    if artifact_path.parent == path.parent and artifact_path.name == primary_name:
                        referenced_primary = True
                    self.check(file_label + ":size", entry.get("size") == artifact_path.stat().st_size, "Module metadata size matches emitted file")
                    self.check(file_label + ":sha256", entry.get("sha256") == sha256(artifact_path), "Module metadata SHA256 matches emitted file")
                    for algorithm in ("sha512", "sha1", "md5"):
                        if algorithm in entry:
                            digest = hashlib.new(algorithm, artifact_path.read_bytes()).hexdigest()
                            self.check(file_label + ":" + algorithm, entry[algorithm] == digest, "Additional declared checksum matches")
                    if artifact_path.suffix in (".jar", ".aar", ".klib", ".zip"):
                        self.archive(artifact_path, coordinate, module, target)
            self.check(coordinate + ":primary-artifact", referenced_primary,
                       "Variant metadata references this coordinate's real primary library artifact, not only sources/notices or redirects")
            if target == "metadata":
                expected = {module + TARGET_SUFFIXES[name] for name in self.targets if name != "metadata"}
                self.check(coordinate + ":target-redirects", expected.issubset(available), "KMP root points at every requested target publication")
        except (InvalidArtifact, AttributeError, TypeError, OSError) as exc:
            self.check(coordinate + ":metadata-parse", False, str(exc))

    def run(self) -> dict[str, Any]:
        group_path = self.repository / GROUP.replace(".", "/")
        for module in self.modules:
            for target in self.targets:
                coordinate = module + TARGET_SUFFIXES[target]
                directory = group_path / coordinate / self.version
                prefix = f"{coordinate}-{self.version}"
                pom = self.file(directory, prefix + ".pom", coordinate + ":pom-present")
                if pom:
                    self.pom(pom, coordinate)
                metadata = self.file(directory, prefix + ".module", coordinate + ":module-present")
                if metadata:
                    self.metadata(metadata, coordinate, module, target)
                notices = self.file(directory, prefix + "-notices.zip", coordinate + ":companion-notices-present")
                if notices:
                    self.archive(notices, coordinate, module, target, companion=True)
        duplicates = {name: sorted(owners) for name, owners in self.class_owners.items() if len(owners) > 1}
        self.check("desktop-no-duplicate-classes", not duplicates, json.dumps(duplicates, sort_keys=True))
        return {
            "schema_version": 1,
            "observed_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Static staged Maven package inspection; not runtime, ABI or release certification",
            "group": GROUP, "version": self.version, "modules": self.modules, "targets": self.targets,
            "native_platforms_requested": self.native_platforms,
            "complete_declared_artifact_matrix_requested": set(self.modules) == set(self.all_modules)
                and set(self.targets) == set(TARGET_SUFFIXES) and set(self.native_platforms) == set(NATIVE_PLATFORMS),
            "success": bool(self.checks) and all(check["passed"] for check in self.checks),
            "release_readiness_certified": False,
            "check_count": len(self.checks), "failed_check_count": sum(not check["passed"] for check in self.checks),
            "checks": self.checks, "artifact_files": sorted(self.files.values(), key=lambda item: item["path"]),
            "native_provenance_observed": self.native_receipts,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--module", action="append", help="Explicit partial scope; defaults to all 21 identity modules")
    parser.add_argument("--target", action="append", choices=list(TARGET_SUFFIXES), help="Explicit partial scope; metadata always included")
    parser.add_argument("--native-platform", action="append", choices=NATIVE_PLATFORMS, help="Explicit partial scope; defaults to all five intended slots")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = ArtifactVerifier(args.source_root, args.repository, args.version, args.module, args.target, args.native_platform).run()
    except (InvalidArtifact, OSError, KeyError, TypeError) as exc:
        result = {"schema_version": 1, "success": False, "release_readiness_certified": False, "error": str(exc)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ("success", "check_count", "failed_check_count", "release_readiness_certified", "error") if key in result}))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
