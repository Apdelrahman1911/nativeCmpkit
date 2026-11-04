#!/usr/bin/env python3
"""Explicit exact-original notice carry-forward; no registry rescan or release approval.

This is NOT a general resume/merge CLI. Two independently pinned original failed
reports and metadata inputs may carry their already accepted complete public bytes.
Only their known 17/15 missing-text rows receive separately reviewed supplements.
Originals remain failed and untouched. A NEW full report is derived from actual
coverage/output; legal, SDK, native, consumer and publishing gates remain separate.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat

from native_license_material_v2 import INPUT_PATHS, _freeze, _plain
from native_license_objc2_material import REVIEWED_INDEX_SHA256, SELECTED_NAMES
from native_license_supplements import (CATALOG_RELATIVE, MAX_FILE_BYTES, canonical_path,
    digest, load_supplements, regular_bytes, text_bytes, verify_crate_correspondence)
from verify_artifacts import InvalidArtifact, autodiscovered_license_path, load_json_bytes, validate_native_metadata

MAX_ALL_BYTES = 32 * 1024 * 1024
ORIGINAL_SCOPE = ("Exact license texts from checksum-verified crates.io archives in conservative locked target union; not legal clearance; "
                  "explicit pinned-VCS missing-text supplements retain full origin/proofs")
ORIGINALS = _freeze({
    "calf-file-picker": {"report": "306d12e24a5ecaa3a29065ba6aed78dbfc9bd50e55f4222bc84ac6016e1c7ef4",
        "metadata": "e53bd784aae97aab724d887e7256bac6cf7c0497ef7a0ac9387e11c4060d8524", "packages": 93,
        "gaps": 17},
    "calf-share": {"report": "fdb2d36377ad2c2b044087f4d533db949e2922b42381bf49b6865f22d12f473e",
        "metadata": "63e8c694ed7cc4a33e6419b7cd9307ca999b118ccd3d2ed980b202f20cda880a", "packages": 48,
        "gaps": 15},
})


def require(condition, message):
    if not condition:
        raise InvalidArtifact(message)


def directory(path: Path) -> None:
    """Observe existing unlinked ancestors; not a hostile same-UID sandbox."""
    try:
        for current in [*reversed(path.parents), path]:
            require(stat.S_ISDIR(current.lstat().st_mode),
                    "Notice output root/parent must be an unlinked directory")
    except OSError as error:
        raise InvalidArtifact("Notice output parent is unavailable") from error


def output_boundary(output: Path, roots: tuple[Path, ...] = ()) -> None:
    require(output.is_absolute() and ".." not in output.parts and ".git" not in output.parts,
            "Notice output must be a canonical absolute path outside Git metadata")
    for root in roots:
        require(root.is_absolute() and ".." not in root.parts
                and root != output and root not in output.parents and output not in root.parents,
                "New notice output must not overlap original material, source or registry inputs")
    directory(output.parent)
    require(not output.exists() and not output.is_symlink(),
            "New output only; never merge, delete or relabel original failed material")


def inventory(root: Path, files: set[str]) -> None:
    """Reject foreign entries before traversing them; finite owned notice paths only."""
    directories = {parent.as_posix() for file in files for parent in Path(file).parents if parent != Path('.')}
    pending, seen = [root], set()
    require(stat.S_ISDIR(root.lstat().st_mode), "Original notice root must be an unlinked directory")
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                relative = (current / entry.name).relative_to(root).as_posix()
                value = entry.stat(follow_symlinks=False)
                if relative in files:
                    require(stat.S_ISREG(value.st_mode) and value.st_nlink == 1, "Notice input is linked or nonregular")
                    seen.add(relative)
                elif relative in directories:
                    require(stat.S_ISDIR(value.st_mode), "Notice parent is linked or non-directory")
                    pending.append(current / entry.name)
                else:
                    raise InvalidArtifact("Unrecorded original notice file/directory; never silently merge private or stale bytes")
    require(seen == files, "Original notice inventory is incomplete")


@dataclass(frozen=True)
class AcceptedOriginal:
    module: str
    report: dict
    metadata: dict
    payloads: dict[str, bytes]
    current_inputs: dict[str, bytes]

    def __post_init__(self):
        for field in ("report", "metadata", "payloads", "current_inputs"):
            object.__setattr__(self, field, _freeze(getattr(self, field)))


def validate_original(module: str, report_bytes: bytes, metadata_bytes: bytes, read_file,
                      current_inputs: dict[str, bytes]) -> AcceptedOriginal:
    require(module in ORIGINALS, "Only the two independently reviewed original notice reports may be carried")
    pinned = ORIGINALS[module]
    require(digest(report_bytes) == pinned["report"] and digest(metadata_bytes) == pinned["metadata"],
            "Original report/metadata differs from independent fixed review; producer rehashing cannot authorize reuse")
    report, metadata = load_json_bytes(report_bytes), load_json_bytes(metadata_bytes)
    declared = validate_native_metadata(metadata, module)
    require(report.get("module") == module and report.get("schema_version") == 1
            and report.get("scope") == ORIGINAL_SCOPE and report.get("complete_material_collection") is False
            and report.get("license_obligations_reviewed") is False
            and report.get("metadata_sha256") == pinned["metadata"], "Original failed scope/identity/gates differ")
    for name, key in (("Cargo.toml", "cargo_toml_sha256"), ("Cargo.lock", "cargo_lock_sha256")):
        path = module + "/native/" + name
        require(path in current_inputs and digest(current_inputs[path]) == report.get(key) == metadata.get(key),
                "Original notices do not belong to the current exact manifest/lock")
    prefix = "META-INF/nativecmpkit/native-dependencies/" + module + "/"
    paths = {prefix + "licenses-report.json", prefix + "metadata.json"}
    payloads = {prefix + "licenses-report.json": report_bytes, prefix + "metadata.json": metadata_bytes}
    packages, represented = report.get("packages"), {}
    require(isinstance(packages, list) and len(packages) == pinned["packages"], "Original full package count differs")
    expected_gaps = set()
    keys = ("name", "version", "source_kind", "license", "checksum")
    for package in packages:
        identity = package["name"] + "@" + package["version"]
        require(identity not in represented, "Duplicate original package")
        represented[identity] = {key: package.get(key) for key in keys}
        expected = declared.get(identity)
        require(expected is not None, "Foreign original package")
        own = prefix + package["name"] + "-" + package["version"] + "/"
        files = package.get("files")
        require(isinstance(files, list), "Original complete file records required")
        if package["source_kind"] == "local-root":
            require(files == [], "Project root notices are separately packaged")
            continue
        if not files:
            require(package["name"] in SELECTED_NAMES or module == "calf-file-picker"
                    and package["name"] in {"winapi-i686-pc-windows-gnu", "winapi-x86_64-pc-windows-gnu"},
                    "An unknown original gap cannot use this finite carry-forward path")
            expected_gaps.add(package["name"] + "-" + package["version"])
            continue
        records = list(files)
        external = package.get("external_vcs_material")
        if external is not None:
            require(package["name"] == "jni-sys-macros" and isinstance(external, dict)
                    and external.get("kind") == "pinned-vcs", "Only the already accepted original JNI supplement may be carried")
            records.extend(external["provenance_files"])
        for record in records:
            path = canonical_path(record["path"])
            require(path.startswith(own) and path not in paths, "Duplicate/foreign original notice/proof path")
            payload = read_file(path)
            require(type(record["bytes"]) is int and 0 < len(payload) == record["bytes"] <= MAX_FILE_BYTES
                    and digest(payload) == record["sha256"], "Original complete notice/proof bytes differ")
            if record in files:
                require(autodiscovered_license_path(path) or path[len(own):] == expected["license_file"],
                        "Original source implementation cannot become a notice")
                text_bytes(payload)
            paths.add(path)
            payloads[path] = payload
            require(sum(map(len, payloads.values())) <= MAX_ALL_BYTES, "Original carried bytes exceed the bounded public material scope")
    require(represented == {identity: {key: package[key] for key in keys} for identity, package in declared.items()},
            "Original report and sanitized metadata do not cover exactly the same package/lock identities")
    gaps = report.get("gaps")
    require(isinstance(gaps, list) and len(gaps) == len(expected_gaps) == pinned["gaps"]
            and {gap.get("package") for gap in gaps} == expected_gaps
            and all(gap.get("reason") == "No license/copyright/notice text found; SPDX declaration alone is insufficient" for gap in gaps),
            "Only the exact original 17/15 missing-text rows may be replaced")
    return AcceptedOriginal(module, report, metadata, payloads, current_inputs)


def capture_original(root: Path, module: str, source_root: Path) -> AcceptedOriginal:
    prefix = "META-INF/nativecmpkit/native-dependencies/" + module + "/"
    held = validate_original(module, regular_bytes(root, prefix + "licenses-report.json"),
        regular_bytes(root, prefix + "metadata.json"), lambda path: regular_bytes(root, path),
        {path: regular_bytes(source_root, path) for path in sorted(INPUT_PATHS)})
    inventory(root, set(held.payloads))
    return held


def assemble(held: AcceptedOriginal, supplements: dict, archives: dict[str, Path]) -> tuple[dict, dict[str, bytes]]:
    """Only validated known gaps change; already accepted registry/JNI bytes stay held."""
    report = _plain(held.report)
    prefix = "META-INF/nativecmpkit/native-dependencies/" + held.module + "/"
    payloads = dict(held.payloads)
    gaps = {gap["package"] for gap in report["gaps"]}
    replacements = 0
    for package in report["packages"]:
        identity = package["name"] + "-" + package["version"]
        if identity not in gaps:
            continue
        key = package["name"] + "@" + package["version"]
        approved = supplements.get(key)
        require(approved is not None and key in archives, "A known gap lacks genuinely reviewed material and its exact public archive")
        require(approved.manifest.get("schema_version") in (3, 4)
                and all(approved.manifest["package"].get(field) == package.get(field)
                        for field in ("name", "version", "checksum", "license")),
                "A gap requires its own exact original package/checksum/grant, not foreign material")
        verify_crate_correspondence(archives[key], approved)  # schema3/4 compressed identity, no payload replay.
        own = prefix + identity + "/"
        package["files"] = approved.license_entries(own)
        package["external_vcs_material"] = approved.material_record(own)
        require(bool(package["files"]), "A gap cannot be filled with an empty/self-approved report")
        for path, content in (approved.license_payloads(own) | approved.provenance_payloads(own)).items():
            canonical_path(path)
            require(path not in payloads or payloads[path] == content, "Conflicting/overwritten carried public notice path")
            payloads[path] = content
        replacements += 1
        require(sum(map(len, payloads.values())) <= MAX_ALL_BYTES, "Complete new material exceeds its aggregate bound")
    require(replacements == len(gaps) and all(package["files"] for package in report["packages"]
            if package["source_kind"] == "crates.io"), "Actual complete distinct registry notice coverage is required")
    report["gaps"] = []
    report["complete_material_collection"] = True
    report["scope"] = "Exact original accepted public notices plus newly verified finite gap material; not legal, SDK, native, consumer or release clearance"
    report["carry_forward_evidence"] = {"original_report_sha256": ORIGINALS[held.module]["report"],
        "original_metadata_sha256": ORIGINALS[held.module]["metadata"], "original_failed_gaps_retained": replacements,
        "adopted_index_sha256": REVIEWED_INDEX_SHA256, "original_notice_payload_rescans": 0,
        "native_or_consumer_methods_executed": 0, "release_readiness_certified": False}
    payloads[prefix + "licenses-report.json"] = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    require(sum(map(len, payloads.values())) <= MAX_ALL_BYTES,
            "Final serialized report and complete material exceed the aggregate bound")
    return report, payloads


def write_new(output: Path, payloads: dict[str, bytes]) -> None:
    output_boundary(output)
    files = {canonical_path(path) for path in payloads}
    require(files and all(type(content) is bytes and 0 < len(content) <= MAX_FILE_BYTES
                         for content in payloads.values())
            and sum(map(len, payloads.values())) <= MAX_ALL_BYTES,
            "New notice output requires bounded nonempty complete public bytes")
    require(not any(parent.as_posix() in files for path in files for parent in Path(path).parents
                    if parent != Path('.')), "Notice file paths cannot also be output directories")
    output.mkdir()
    for relative, content in sorted(payloads.items()):
        target = output / canonical_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        directory(target.parent)
        with target.open('xb') as stream:
            stream.write(content)
    inventory(output, set(payloads))
    for relative, content in payloads.items():
        require(regular_bytes(output, relative) == content, "New notice output changed or lost complete bytes")


def carry_forward(original: Path, module: str, source_root: Path, cache_roots: list[Path], output: Path) -> dict:
    output_boundary(output, (original, source_root, *cache_roots))
    require(cache_roots and all(root.is_dir() and not root.is_symlink() for root in cache_roots),
            "Explicit public registry cache roots required for known missing rows only")
    held = capture_original(original, module, source_root)
    missing = {gap["package"] for gap in held.report["gaps"]}
    selected = [package for package in _plain(held.metadata)["packages"]
                if package["name"] + "-" + package["version"] in missing]
    supplements = load_supplements(source_root / CATALOG_RELATIVE, selected, source_root=source_root)
    archives = {}
    for package in selected:
        filename = package["name"] + "-" + package["version"] + ".crate"
        found = [root / filename for root in cache_roots if (root / filename).is_file()]
        require(len(found) == 1, "Exactly one original public cached archive for each finite missing row")
        archives[package["id"]] = found[0]
    report, payloads = assemble(held, supplements, archives)
    for path, content in held.current_inputs.items():
        require(regular_bytes(source_root, path) == content, "Current Cargo source changed before writing")
    write_new(output, payloads)
    for path, content in held.current_inputs.items():
        require(regular_bytes(source_root, path) == content, "Current Cargo source changed during writing; preserve refusing output")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-notices', required=True, type=Path)
    parser.add_argument('--module', required=True, choices=tuple(ORIGINALS))
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--registry-cache', required=True, type=Path, action='append')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        report = carry_forward(args.original_notices, args.module, args.source_root, args.registry_cache, args.output)
        print(json.dumps({"module": args.module, "packages": len(report["packages"]), "gaps": len(report["gaps"]),
                          "complete_material_collection": report["complete_material_collection"], "release_readiness_certified": False}))
        return 0
    except (InvalidArtifact, OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"complete_material_collection": False, "error": str(error), "release_readiness_certified": False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
