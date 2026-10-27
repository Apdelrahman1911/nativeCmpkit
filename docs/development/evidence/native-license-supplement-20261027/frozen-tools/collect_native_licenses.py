#!/usr/bin/env python3
"""Collect exact public Cargo dependency license files from checksum-verified .crate archives.

Input is the sanitized locked metadata produced by scripts/native/artifacts.py.
Only explicit local PUBLIC crates.io registry cache roots are searched. Optional
reviewed VCS supplements must bind the exact locked archive and source/license
proofs; no network, tar extraction, Cargo invocation, build or legal clearance.
Missing/unreviewed material remains fail-closed evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

from verify_artifacts import (CHECKSUM, CRATE_NAME, CRATE_VERSION, InvalidArtifact,
                              autodiscovered_license_path, load_json_bytes, relative_notice_path, sha256,
                              validate_native_metadata)
from native_license_supplements import load_supplement, verify_crate_correspondence

MAX_MEMBERS = 100_000
MAX_NOTICE_BYTES = 1024 * 1024
MAX_CRATE_BYTES = 256 * 1024 * 1024
MAX_CRATE_UNCOMPRESSED = 2 * 1024 * 1024 * 1024
MAX_COLLECTED_BYTES = 32 * 1024 * 1024
MAX_SUPPLEMENT_PACKAGES = 64
MAX_ALL_SUPPLEMENT_BYTES = 32 * 1024 * 1024


class MissingLicenseText(InvalidArtifact):
    """Only this validated archive gap may use a separately reviewed supplement."""


def relative_member(name: str, prefix: str) -> str:
    relative_notice_path(name)
    parts = PurePosixPath(name).parts
    if not parts or parts[0] != prefix or len(parts) < 2:
        raise InvalidArtifact("Crate member is outside expected package prefix")
    return PurePosixPath(*parts[1:]).as_posix()


def collect_archive(path: Path, name: str, version: str, checksum: str,
                    declared_license_file: str | None = None) -> dict[str, bytes]:
    if not all(isinstance(value, str) for value in (name, version, checksum)) or not CRATE_NAME.fullmatch(name) or not CRATE_VERSION.fullmatch(version) or not CHECKSUM.fullmatch(checksum):
        raise InvalidArtifact("Unsafe/incomplete locked package identity")
    if path.is_symlink() or path.stat().st_size > MAX_CRATE_BYTES or sha256(path) != checksum:
        raise InvalidArtifact("Crate archive checksum, size or symlink validation failed")
    if declared_license_file is not None:
        relative_notice_path(declared_license_file)
    result = {}
    seen = set()
    with tarfile.open(path, "r:gz") as archive:
        total_bytes, collected_bytes = 0, 0
        # Check the count while reading headers; getmembers() would first allocate
        # the entire untrusted member list and only then enforce the bound.
        for index, member in enumerate(archive):
            total_bytes += member.size
            if index >= MAX_MEMBERS or total_bytes > MAX_CRATE_UNCOMPRESSED or member.size < 0:
                raise InvalidArtifact("Crate entry count/uncompressed size exceeds limit")
            if member.isdir():
                continue
            relative = relative_member(member.name, name + "-" + version)
            if relative in seen:
                raise InvalidArtifact("Duplicate crate member path")
            seen.add(relative)
            wanted = autodiscovered_license_path(relative) or relative == declared_license_file
            if not wanted:
                continue
            if not member.isfile() or member.issym() or member.islnk():
                raise InvalidArtifact("License entry is not a regular file")
            if not 0 < member.size <= MAX_NOTICE_BYTES:
                raise InvalidArtifact("License text is empty or oversized")
            collected_bytes += member.size
            if collected_bytes > MAX_COLLECTED_BYTES:
                raise InvalidArtifact("Collected license material exceeds per-crate bound")
            stream = archive.extractfile(member)  # Read bounded bytes; NEVER extractall/extract to disk.
            if stream is None:
                raise InvalidArtifact("Unreadable license member")
            with stream:
                data = stream.read(MAX_NOTICE_BYTES + 1)
            if len(data) != member.size:
                raise InvalidArtifact("Truncated/oversized license member")
            # Binary data is not accepted as a readable copyright/permission notice.
            try:
                data.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise InvalidArtifact("License member requires a reviewed text-encoding decision") from exc
            if b"\x00" in data:
                raise InvalidArtifact("Binary license member")
            result[relative] = data
    if declared_license_file and declared_license_file not in result:
        raise InvalidArtifact("Declared license_file not present in checksum-verified crate")
    if not result:
        raise MissingLicenseText("No license/copyright/notice text found; SPDX declaration alone is insufficient")
    return result


def collect(metadata_path: Path, cache_roots: list[Path], output: Path,
            *, vcs_supplements: Path | None = None) -> dict:
    metadata_bytes = metadata_path.read_bytes()
    data = load_json_bytes(metadata_bytes)
    module = data.get("module") if isinstance(data, dict) else None
    validate_native_metadata(data, module)
    if not cache_roots or any(not root.is_dir() or root.is_symlink() for root in cache_roots):
        raise InvalidArtifact("Explicit existing public registry cache roots are required")
    # Reject malformed/private/unbounded catalog inputs BEFORE creating output.
    # Missing entries are not a waiver; the ordinary archive gap remains below.
    supplements, supplement_bytes = {}, 0
    if vcs_supplements is not None:
        if not vcs_supplements.is_dir() or vcs_supplements.is_symlink():
            raise InvalidArtifact("Explicit existing public VCS supplement catalog is required")
        for package in data["packages"]:
            if package["source_kind"] != "crates.io":
                continue
            supplement = load_supplement(vcs_supplements, package)
            if supplement is not None:
                supplements[package["id"]] = supplement
                supplement_bytes += sum(map(len, supplement.contents.values()))
                if len(supplements) > MAX_SUPPLEMENT_PACKAGES or supplement_bytes > MAX_ALL_SUPPLEMENT_BYTES:
                    raise InvalidArtifact("Supplement catalog exceeds package/aggregate byte bounds")
    if output.is_symlink() or (output.exists() and any(output.iterdir())):
        raise InvalidArtifact("Output must be a new/empty directory; stale notices must not be merged silently")
    output.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "module": module, "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
              "cargo_toml_sha256": data["cargo_toml_sha256"], "cargo_lock_sha256": data["cargo_lock_sha256"],
              "scope": "Exact license texts from checksum-verified crates.io archives in conservative locked target union; not legal clearance"
                       + ("; explicit pinned-VCS missing-text supplements retain full origin/proofs" if vcs_supplements is not None else ""),
              "license_obligations_reviewed": False, "packages": [], "gaps": []}
    for package in data["packages"]:
        name, version = package["name"], package["version"]
        identity = name + "-" + version
        record = {key: package.get(key) for key in ("name", "version", "source_kind", "license", "checksum")}
        record["files"] = []
        if package.get("source_kind") == "local-root":
            record["scope"] = "Project LICENSE/NOTICE separately packaged; not a registry dependency"
        else:
            try:
                archives = [root / (identity + ".crate") for root in cache_roots if (root / (identity + ".crate")).is_file()]
                if len(archives) != 1:
                    raise InvalidArtifact("Expected exactly one cached public .crate archive")
                supplement = supplements.get(package["id"])
                external = False
                try:
                    texts = collect_archive(archives[0], name, version, package.get("checksum", ""), package.get("license_file"))
                except MissingLicenseText:
                    if supplement is None:
                        raise
                    # Capture/revalidate actual crate bytes. Never fallback on
                    # checksum, link, traversal, declared-file or encoding errors.
                    verify_crate_correspondence(archives[0], supplement)
                    external = True
                    texts = {}
                if supplement is not None and not external:
                    raise InvalidArtifact("Reviewed missing-text supplement is stale/unnecessary for this archive")
                if not isinstance(package.get("license"), str) or not package["license"].strip():
                    report["gaps"].append({"package": identity, "reason": "License expression missing; collected texts require manual classification"})
                for relative, content in sorted(texts.items()):
                    entry = f"META-INF/nativecmpkit/native-dependencies/{module}/{identity}/{relative}"
                    target = output / entry
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                    record["files"].append({"path": entry, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
                if external:
                    prefix = f"META-INF/nativecmpkit/native-dependencies/{module}/{identity}/"
                    record["files"] = supplement.license_entries(prefix)
                    record["external_vcs_material"] = supplement.material_record(prefix)
                    for entry, content in (supplement.license_payloads(prefix) | supplement.provenance_payloads(prefix)).items():
                        target = output / entry
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(content)
            except (InvalidArtifact, OSError, tarfile.TarError) as exc:
                report["gaps"].append({"package": identity, "reason": str(exc)})
        report["packages"].append(record)
    if not any(item.get("source_kind") == "crates.io" for item in report["packages"]):
        report["gaps"].append({"reason": "No registry dependency packages were provided"})
    report["complete_material_collection"] = not report["gaps"]
    path = output / f"META-INF/nativecmpkit/native-dependencies/{module}/licenses-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    # Preserve only the bytes checked above against the strict sanitized schema,
    # never reread an input that could have changed into raw/private Cargo output.
    (path.parent / "metadata.json").write_bytes(metadata_bytes)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--registry-cache", type=Path, action="append", required=True,
                        help="Explicit public crates.io cache/<index> directory; not a source-tree/environment dump")
    parser.add_argument("--output", type=Path, required=True, help="New/empty build/native-notices/<module> directory, merged at notices ZIP root")
    parser.add_argument("--vcs-supplements", type=Path,
                        help="Explicit reviewed public catalog for missing-text crates only; default remains archive-only")
    args = parser.parse_args()
    try:
        report = collect(args.metadata, args.registry_cache, args.output, vcs_supplements=args.vcs_supplements)
        print(json.dumps({"module": report["module"], "packages": len(report["packages"]), "gaps": len(report["gaps"]),
                          "complete_material_collection": report["complete_material_collection"], "license_obligations_reviewed": False}))
        return 0 if report["complete_material_collection"] else 1
    except (InvalidArtifact, OSError) as exc:
        print(json.dumps({"complete_material_collection": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
