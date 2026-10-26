#!/usr/bin/env python3
"""Build and validate explicitly selected native resources, never publish them.

Manifests prove consistency with recorded source and bytes, not trusted-builder
attestation. Release gates must separately verify the producing CI run and real
JNI/runtime tests. Importing this module has no side effects or subprocesses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform as host_platform
import re
import shutil
import struct
import subprocess
import tempfile
import tomllib

SCHEMA_VERSION = 1
ABI_VERSION = 1
SUPPORTED_PLATFORMS = {
    "linux-x64": {"rustTarget": "x86_64-unknown-linux-gnu", "format": "elf", "machine": 62},
    "linux-arm64": {"rustTarget": "aarch64-unknown-linux-gnu", "format": "elf", "machine": 183},
    "macos-x64": {"rustTarget": "x86_64-apple-darwin", "format": "macho", "machine": 0x01000007},
    "macos-arm64": {"rustTarget": "aarch64-apple-darwin", "format": "macho", "machine": 0x0100000C},
    "windows-x64": {"rustTarget": "x86_64-pc-windows-msvc", "format": "pe", "machine": 0x8664},
}
MODULE_STEMS = {"calf-file-picker": "calf_filepicker_native", "calf-share": "calf_share_native"}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?\Z")


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def validate_module(module: str) -> None:
    if module not in MODULE_STEMS:
        raise ValueError(f"Unsupported native module: {module!r}")


def native_filename(module: str, platform: str) -> str:
    validate_module(module)
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported native platform: {platform!r}; Windows arm64 is not advertised")
    stem = MODULE_STEMS[module]
    if platform.startswith("windows-"):
        return stem + ".dll"
    return "lib" + stem + (".dylib" if platform.startswith("macos-") else ".so")


def manifest_relative_path(module: str, platform: str) -> str:
    native_filename(module, platform)
    return f"META-INF/nativecmpkit/native/{module}/{platform}.json"


def binary_relative_path(module: str, platform: str) -> str:
    return f"native/{platform}/{native_filename(module, platform)}"


def safe_file(root: Path, relative: str) -> Path:
    """Reject traversal and every symlink component, including links staying inside root."""
    rel = Path(relative)
    if (not relative or rel.is_absolute() or ".." in rel.parts or "\\" in relative
            or any(ord(char) < 32 for char in relative) or relative != rel.as_posix()):
        raise ValueError(f"Unsafe relative path: {relative!r}")
    resolved_root = root.resolve()
    child = root
    for part in rel.parts:
        child /= part
        if child.is_symlink():
            raise ValueError(f"Symlink is not a native input: {relative}")
    if not child.resolve().is_relative_to(resolved_root):
        raise ValueError(f"Path escapes resource root: {relative}")
    if not child.is_file():
        raise ValueError(f"Required file is missing: {relative}")
    return child


def _regular_files(root: Path, directory: Path, excluded: set[str] | None = None):
    excluded = excluded or set()
    if not directory.exists():
        return
    if directory.is_symlink():
        raise ValueError("Symlink input directory is not permitted")
    for current, directories, files in os.walk(directory, followlinks=False):
        directories[:] = sorted(name for name in directories
                                if name not in excluded or Path(current) != directory)
        for name in directories:
            if (Path(current) / name).is_symlink():
                raise ValueError("Symlink input directory is not permitted")
        for name in sorted(files):
            if name in excluded:
                continue
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            yield relative, safe_file(root, relative)


def expected_source_files(root: Path, module: str) -> dict[str, str]:
    """Complete deterministic source inventory, not a manifest-controlled allowlist.

    All crate sources/config/assets/tests/scripts and desktop JNI Kotlin sources
    are inputs. Native assets must stay below native/; new external build inputs
    require an explicit inventory-rule update. target/.git are build/VCS output;
    .gitignore is packaging policy, not compiler input. The shared implementation
    and module Gradle script are included to bind build-command changes too.
    """
    validate_module(module)
    root = root.resolve()
    files = {}
    for relative, path in _regular_files(root, root / module / "native", {"target", ".git", ".gitignore"}):
        files[relative] = digest(path)
    for relative, path in _regular_files(root, root / module / "src/desktopMain/kotlin"):
        files[relative] = digest(path)
    required = [f"{module}/native/Cargo.toml", f"{module}/native/Cargo.lock", f"{module}/build.gradle.kts",
                "rust-toolchain.toml", "scripts/native/artifacts.py",
                "convention-plugins/src/main/kotlin/NativeLibraries.kt"]
    for relative in required:
        files[relative] = digest(safe_file(root, relative))
    for relative in [".cargo/config", ".cargo/config.toml", f"{module}/.cargo/config", f"{module}/.cargo/config.toml"]:
        if (root / relative).exists() or (root / relative).is_symlink():
            files[relative] = digest(safe_file(root, relative))
    return dict(sorted(files.items()))


def source_digest(files: dict[str, str]) -> str:
    if not files or any(not SHA256.fullmatch(value) for value in files.values()):
        raise ValueError("Source file hashes must be nonempty SHA256 values")
    payload = "".join(f"{files[path]}  {path}\n" for path in sorted(files)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def toolchain(root: Path) -> str:
    with safe_file(root, "rust-toolchain.toml").open("rb") as stream:
        value = tomllib.load(stream)["toolchain"]["channel"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise ValueError("Rust toolchain must be an exact stable version, not a moving channel")
    return value


def crate_version(root: Path, module: str) -> str:
    with safe_file(root, f"{module}/native/Cargo.toml").open("rb") as stream:
        package = tomllib.load(stream)["package"]
    if package.get("publish") is not False:
        raise ValueError("Native crates must retain publish = false")
    value = package["version"]
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise ValueError("Native crate version must be a literal semver")
    return value


def git_provenance(root: Path) -> tuple[str, bool]:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if not GIT_SHA.fullmatch(revision):
        raise ValueError("Native source provenance requires a full Git commit SHA")
    # Store a boolean only, never machine paths or status/terminal transcripts.
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=root))
    return revision, dirty


def current_platform() -> str:
    system = host_platform.system().lower()
    arch = host_platform.machine().lower()
    if arch in {"x86_64", "amd64"}:
        arch = "x64"
    elif arch in {"aarch64", "arm64"}:
        arch = "arm64"
    system = {"darwin": "macos", "windows": "windows", "linux": "linux"}.get(system, system)
    value = f"{system}-{arch}"
    if value not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported native host: {value}; no platform fallback is permitted")
    return value


def validate_binary(path: Path, platform: str) -> None:
    """Check actual container/CPU headers in addition to hashes (not a JNI ABI test)."""
    spec = SUPPORTED_PLATFORMS[platform]
    with path.open("rb") as stream:
        header = stream.read(64)
        if spec["format"] == "elf":
            if len(header) < 64 or header[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", header, 18)[0] != spec["machine"]:
                raise ValueError(f"Expected a 64-bit little-endian ELF for {platform}")
        elif spec["format"] == "macho":
            if len(header) < 32 or header[:4] != b"\xcf\xfa\xed\xfe" or struct.unpack_from("<I", header, 4)[0] != spec["machine"]:
                raise ValueError(f"Expected a single-architecture 64-bit Mach-O for {platform}")
        else:
            if len(header) < 64 or header[:2] != b"MZ":
                raise ValueError("Expected a Windows PE library")
            offset = struct.unpack_from("<I", header, 60)[0]
            if offset < 64 or offset > path.stat().st_size - 24:
                raise ValueError("Invalid Windows PE header offset")
            stream.seek(offset)
            pe = stream.read(24)
            if pe[:4] != b"PE\0\0" or struct.unpack_from("<H", pe, 4)[0] != spec["machine"]:
                raise ValueError(f"Wrong Windows PE architecture for {platform}")


def load_manifest(path: Path) -> dict:
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("Native manifest exceeds bounded size")
    def unique_object(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate native manifest key: {key}")
            result[key] = value
        return result
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream, object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError("Native manifest must be an object")
    return value


def validate_manifest(root: Path, module: str, platform: str, resource_root: Path, *,
                      require_clean: bool = False, expected_revision: str | None = None,
                      expected_version: str | None = None) -> dict:
    binary = safe_file(resource_root, binary_relative_path(module, platform))
    manifest = load_manifest(safe_file(resource_root, manifest_relative_path(module, platform)))
    fixed = {"schemaVersion": SCHEMA_VERSION, "module": module, "platform": platform,
             "rustTarget": SUPPORTED_PLATFORMS[platform]["rustTarget"], "filename": binary.name,
             "abiVersion": ABI_VERSION, "crateVersion": crate_version(root, module),
             "rustToolchain": toolchain(root), "cargoProfile": "release", "rustFlags": []}
    for key, value in fixed.items():
        if manifest.get(key) != value or type(manifest.get(key)) is not type(value):
            raise ValueError(f"Native manifest {key} differs from expected contract")
    if type(manifest.get("size")) is not int or manifest["size"] <= 0 or binary.stat().st_size != manifest["size"]:
        raise ValueError("Native binary size is missing, empty or mismatched")
    if manifest.get("sha256") != digest(binary):
        raise ValueError("Native binary checksum mismatch")
    validate_binary(binary, platform)
    revision = manifest.get("sourceRevision")
    if not isinstance(revision, str) or not GIT_SHA.fullmatch(revision):
        raise ValueError("Missing full source revision")
    if expected_revision is not None and revision != expected_revision:
        raise ValueError("Stale native source revision")
    if type(manifest.get("sourceTreeDirty")) is not bool:
        raise ValueError("Missing truthful sourceTreeDirty provenance")
    if require_clean and manifest["sourceTreeDirty"]:
        raise ValueError("Release native resources must come from a clean source tree")
    version = manifest.get("libraryVersion")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("Missing native library version")
    if expected_version is not None and version != expected_version:
        raise ValueError("Native library version mismatch")
    if not str(manifest.get("rustcVersion", "")).startswith(f"rustc {toolchain(root)} "):
        raise ValueError("Native manifest compiler version differs from pinned toolchain")
    if not str(manifest.get("cargoVersion", "")).startswith(f"cargo {toolchain(root)} "):
        raise ValueError("Native manifest Cargo version differs from pinned toolchain")
    expected = expected_source_files(root, module)
    if manifest.get("sourceFiles") != expected:
        raise ValueError("Native source inventory is incomplete or stale")
    if manifest.get("sourceSha256") != source_digest(expected):
        raise ValueError("Native source aggregate checksum mismatch")
    return manifest


def validate_bundle(root: Path, module: str, resource_root: Path, platforms: list[str], **kwargs) -> list[dict]:
    if not platforms or len(set(platforms)) != len(platforms):
        raise ValueError("Explicit nonempty unique native platform set is required")
    allowed = {path for platform in platforms for path in
               [binary_relative_path(module, platform), manifest_relative_path(module, platform)]}
    actual = {relative for relative, _ in _regular_files(resource_root, resource_root)}
    if actual != allowed:
        raise ValueError(f"Native resource set differs: missing={sorted(allowed - actual)}, unexpected={sorted(actual - allowed)}")
    return [validate_manifest(root, module, platform, resource_root, **kwargs) for platform in platforms]


def _replace_directory(staged: Path, destination: Path) -> None:
    if destination.is_symlink():
        raise ValueError("Native output directory may not be a symlink")
    if destination.exists():
        shutil.rmtree(destination)
    staged.replace(destination)


def _safe_output(root: Path, module: str, destination: Path) -> None:
    allowed = [(root / "build").resolve(), (root / module / "build").resolve()]
    actual = destination.resolve()
    if not any(actual != base and actual.is_relative_to(base) for base in allowed):
        raise ValueError("Native outputs must be a dedicated child of root/module build/, never source or unrelated directories")
    parent = destination
    while parent != root and parent != parent.parent:
        if parent.is_symlink():
            raise ValueError("Native output path may not contain symlinks")
        parent = parent.parent


def assemble(root: Path, module: str, resource_root: Path, destination: Path, platforms: list[str], **kwargs) -> list[dict]:
    _safe_output(root, module, destination)
    if resource_root.resolve() == destination.resolve() or resource_root.resolve().is_relative_to(destination.resolve()):
        raise ValueError("Native output cannot contain its input directory")
    manifests = validate_bundle(root, module, resource_root, platforms, **kwargs)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".native-stage-", dir=destination.parent) as tmp:
        staged = Path(tmp) / "resources"
        staged.mkdir()
        for platform in platforms:
            for relative in [binary_relative_path(module, platform), manifest_relative_path(module, platform)]:
                target = staged / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(safe_file(resource_root, relative), target)
        # Recheck staged bytes to catch changed source inputs during copying.
        validate_bundle(root, module, staged, platforms, **kwargs)
        _replace_directory(staged, destination)
    return manifests


def _build_environment() -> dict[str, str]:
    env = dict(os.environ)
    disallowed = {"RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER",
                  "CARGO_BUILD_TARGET", "CARGO_TARGET_DIR", "RUSTC_BOOTSTRAP", "CFLAGS", "CXXFLAGS", "LDFLAGS"}
    disallowed.update(key for key in env if key.startswith("CARGO_PROFILE_") or
                      (key.startswith("CARGO_TARGET_") and key.endswith(("_RUSTFLAGS", "_LINKER"))))
    if any(env.get(key) for key in disallowed):
        # Never echo environment values, credentials, wrappers or machine paths.
        raise ValueError("Custom Rust compiler/flags/profile/target overrides are unsupported by the native manifest contract")
    env.setdefault("CARGO_BUILD_JOBS", "2")
    return env


def build(root: Path, module: str, platform: str, destination: Path, cargo_target: Path, version: str) -> dict:
    _safe_output(root, module, destination)
    if platform != current_platform():
        raise ValueError("This task builds only its actual host; use the five native builders, not guessed cross-compilation")
    if not VERSION.fullmatch(version):
        raise ValueError("Invalid native library version")
    sources = expected_source_files(root, module)
    revision, dirty = git_provenance(root)
    pinned = toolchain(root)
    env = _build_environment()
    prefix = ["rustup", "run", pinned]
    rustc = subprocess.check_output([*prefix, "rustc", "--version"], cwd=root, env=env, text=True).strip()
    if not rustc.startswith(f"rustc {pinned} "):
        raise ValueError("Actual Rust compiler differs from pinned toolchain")
    cargo_version = subprocess.check_output([*prefix, "cargo", "--version"], cwd=root, env=env, text=True).strip()
    target = SUPPORTED_PLATFORMS[platform]["rustTarget"]
    subprocess.run([*prefix, "cargo", "build", "--locked", "--release", "--target", target,
                    "--target-dir", str(cargo_target)], cwd=root / module / "native", env=env, check=True)
    binary = cargo_target / target / "release" / native_filename(module, platform)
    validate_binary(binary, platform)
    if expected_source_files(root, module) != sources or git_provenance(root) != (revision, dirty):
        raise ValueError("Native build inputs/revision changed during compilation; rebuild stable inputs")
    manifest = {"schemaVersion": SCHEMA_VERSION, "module": module, "platform": platform,
                "rustTarget": target, "filename": binary.name, "sha256": digest(binary), "size": binary.stat().st_size,
                "abiVersion": ABI_VERSION, "crateVersion": crate_version(root, module), "libraryVersion": version,
                "rustToolchain": pinned, "rustcVersion": rustc, "cargoVersion": cargo_version,
                "cargoProfile": "release", "rustFlags": [], "sourceRevision": revision,
                "sourceTreeDirty": dirty, "sourceFiles": sources, "sourceSha256": source_digest(sources)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".native-build-", dir=destination.parent) as tmp:
        staged = Path(tmp) / "resources"
        out_binary = staged / binary_relative_path(module, platform)
        out_binary.parent.mkdir(parents=True)
        shutil.copyfile(binary, out_binary)
        out_manifest = staged / manifest_relative_path(module, platform)
        out_manifest.parent.mkdir(parents=True)
        out_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validate_bundle(root, module, staged, [platform], expected_revision=revision, expected_version=version)
        _replace_directory(staged, destination)
    return manifest


def metadata(root: Path, module: str, output: Path) -> dict:
    validate_module(module)
    with safe_file(root, f"{module}/native/Cargo.lock").open("rb") as stream:
        locked = tomllib.load(stream)["package"]
    checksums = {(item["name"], item["version"], item.get("source")): item.get("checksum") for item in locked}
    raw = json.loads(subprocess.check_output(["rustup", "run", toolchain(root), "cargo", "metadata", "--locked",
                                             "--offline", "--format-version", "1"], cwd=root / module / "native", text=True))
    packages = []
    id_map = {package["id"]: f"{package['name']}@{package['version']}" for package in raw["packages"]}
    if len(set(id_map.values())) != len(id_map):
        raise ValueError("Ambiguous duplicate Cargo package identities")
    for package in raw["packages"]:
        source = package.get("source")
        if source is not None and source != "registry+https://github.com/rust-lang/crates.io-index":
            raise ValueError("Unreviewed non-crates.io native dependency source (details not exported)")
        if source is None and Path(package["manifest_path"]).resolve() != (root / module / "native/Cargo.toml").resolve():
            raise ValueError("Unreviewed additional path dependency (machine paths not exported)")
        checksum = checksums.get((package["name"], package["version"], source))
        if source and (not isinstance(checksum, str) or not SHA256.fullmatch(checksum)):
            raise ValueError("Registry dependency lacks an exact Cargo.lock checksum")
        license_file = package.get("license_file")
        if license_file:
            rel = Path(license_file)
            if rel.is_absolute():
                try:
                    rel = rel.relative_to(Path(package["manifest_path"]).parent)
                except ValueError as exc:
                    raise ValueError("Dependency license_file escapes its package") from exc
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError("Dependency license_file escapes its package")
            license_file = rel.as_posix()
        packages.append({"id": id_map[package["id"]], "name": package["name"], "version": package["version"],
                         "source_kind": "crates.io" if source else "local-root", "checksum": checksum,
                         "license": package.get("license"),
                         "license_file": license_file})
    nodes = [{"id": id_map[node["id"]], "dependencies": sorted(id_map[item] for item in node["dependencies"])}
             for node in raw["resolve"]["nodes"]]
    result = {"schema_version": 1, "module": module, "target_filter": None,
              "scope": "Conservative unfiltered locked Cargo union; no compile or license certification",
              "cargo_toml_sha256": digest(root / module / "native/Cargo.toml"),
              "cargo_lock_sha256": digest(root / module / "native/Cargo.lock"),
              "packages": sorted(packages, key=lambda item: item["id"]),
              "resolve": sorted(nodes, key=lambda item: item["id"])}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory", "build", "verify", "assemble", "metadata"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--module", required=True, choices=sorted(MODULE_STEMS))
    parser.add_argument("--platform", choices=sorted(SUPPORTED_PLATFORMS))
    parser.add_argument("--full-matrix", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cargo-target-dir", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "inventory":
        files = expected_source_files(root, args.module)
        print(json.dumps({"sourceFiles": files, "sourceSha256": source_digest(files)}, indent=2, sort_keys=True))
    elif args.command == "metadata":
        output = args.output or root / "build/native-metadata" / f"{args.module}.json"
        result = metadata(root, args.module, output)
        print(json.dumps({"module": args.module, "packages": len(result["packages"]), "metadata_sha256": digest(output)}))
    elif args.command == "build":
        if args.full_matrix or args.input or not args.output or not args.version:
            parser.error("build requires --output/--version, and never accepts prebuilt/full-matrix inputs")
        result = build(root, args.module, args.platform or current_platform(), args.output.resolve(),
                       (args.cargo_target_dir or root / args.module / "native/target").resolve(), args.version)
        print(json.dumps({"module": args.module, "platform": result["platform"], "sha256": result["sha256"],
                          "sourceSha256": result["sourceSha256"], "sourceTreeDirty": result["sourceTreeDirty"]}))
    else:
        if not args.input or (args.command == "assemble" and not args.output):
            parser.error("verify/assemble requires --input; assemble also requires --output")
        if args.platform and args.full_matrix:
            parser.error("Choose --platform OR --full-matrix, not both")
        platforms = list(SUPPORTED_PLATFORMS) if args.full_matrix else [args.platform or current_platform()]
        revision, dirty = git_provenance(root)
        if args.require_clean and dirty:
            raise ValueError("Full release assembly requires the current checkout to be clean too")
        options = dict(require_clean=args.require_clean, expected_revision=revision, expected_version=args.version)
        if args.command == "assemble":
            result = assemble(root, args.module, args.input.absolute(), args.output.absolute(), platforms, **options)
        else:
            result = validate_bundle(root, args.module, args.input.absolute(), platforms, **options)
        print(json.dumps({"verified": True, "module": args.module, "platforms": [m["platform"] for m in result],
                          "sourceRevision": revision, "require_clean": args.require_clean}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
