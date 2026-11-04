#!/usr/bin/env python3
"""Prepare a bounded independent consumer and inert original material context.

No Gradle, library/native/JNI, collector, license loader, registry/network or
publication execution. The source must be an explicitly reviewed clean Git
checkout. Only exact consumer/checker sources and the separately pinned original
schema3 context are copied. The latter is NOT a producer source checkout,
complete current metadata/notice collection, publisher attestation or clearance.
This is not an OS sandbox against independently malicious same-UID/Git writers.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import MappingProxyType

from native_license_supplements import canonical_path, digest, git_blob_oid, regular_bytes
from verify_artifacts import InvalidArtifact

CONSUMER_FILES = (
    "README.md", "build.gradle.kts", "settings.gradle.kts", "gradle.properties",
    "verify_artifacts.py", "native_license_supplements.py", "native_license_legacy_winapi.py",
    "native_license_objc2_material.py", "native_license_material_v2.py",
    "collect_native_licenses.py", "verify_native_test_results.py",
    "src/commonMain/kotlin/nativecmpkit/consumer/PublicApiConsumer.kt",
    "src/commonTest/kotlin/nativecmpkit/consumer/PublishedCommonContractTest.kt",
    "src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt",
    "src/desktopTest/kotlin/nativecmpkit/consumer/PublishedNativeConsumerTest.kt",
)
CHECKER_MODULES = (
    "verify_artifacts", "native_license_supplements", "native_license_legacy_winapi",
    "native_license_objc2_material", "native_license_material_v2",
    "collect_native_licenses", "verify_native_test_results",
)
MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_RECEIPT_BYTES = 64 * 1024
METADATA_ORIGIN_REVISION = "7d6b6d5b43f93ae085dc66a3377b3c7967400bf7"
SCOPE = "Independent full consumer source/checker carriage with inert exact original schema3 context; not execution or readiness"

# Preserve the reviewed full21/17-method configuration and original Kotlin bodies.
PRESERVED_CONSUMER_INPUTS = MappingProxyType({
    'build.gradle.kts': 'e565f80c844ed09d7c0eb14fbbade6434a2b19da9d234806386941bb1071237f',
    'settings.gradle.kts': '876b0ba5574957bae968ff73d126a5a3a38bfe0c70a8d529b88e3aacf3727da4',
    'gradle.properties': 'bf8bbec28b310adfdc5b6d3319217bc2cf8657f44cdba2f38214eca4035ddf3b',
    'src/commonMain/kotlin/nativecmpkit/consumer/PublicApiConsumer.kt': '58d79b3b90efa303736b76496298eada17842aabb296f4287c768b436100fb3a',
    'src/commonTest/kotlin/nativecmpkit/consumer/PublishedCommonContractTest.kt': '75df0776f4ab714c6bcbdede1adf73671279ea13af13b56928fb5a930bc3709e',
    'src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt': '95c4089c0f065eee7d0b9dbbf003d42b003e6c01bd7d2f60ca5ef6337bcf3f10',
    'src/desktopTest/kotlin/nativecmpkit/consumer/PublishedNativeConsumerTest.kt': 'cf09cfd8cab360f12d825ba0b06374d2ef012e9802d611960fcebae78ca569e7',
})

# Exact663 catalog/f510 metadata originals, not a mutable producer-report waiver.
MATERIAL_INPUTS = {
    'docs/development/evidence/current-platform-recovery-20261101/native-stage-prerequisites20261104/metadata-current606/calf-file-picker.json': 'e53bd784aae97aab724d887e7256bac6cf7c0497ef7a0ac9387e11c4060d8524',
    'docs/development/evidence/current-platform-recovery-20261101/native-stage-prerequisites20261104/metadata-current606/calf-share.json': '63e8c694ed7cc4a33e6419b7cd9307ca999b118ccd3d2ed980b202f20cda880a',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/LICENSE-APACHE': 'b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/LICENSE-MIT': '5b19674a1db628a475850a131956ed49521b744e3dda8f5a94141f9aba681219',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/crate/Cargo.toml': '9652222664ffc7e2a26fdcdebdce0917a455b39d8fbcbf451bf0b011a3067bf7',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/crate/Cargo.toml.orig': '5257d6f5283ab052b6af51f578a8c74e14c31deb53a7c6cd9e6fa16135d57eb3',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/manifest.json': '09a89e05cbc563396aca1446e7b5ec722626094732aaf1c7ed87e1a71941e085',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/research/correspondence.json': 'b137358205dc0436953e5d891f2fcc14543fed135016d71e2978b1435eba2940',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/research/source-commit.json': '81f3f74fb2f4d3e7c9bc41bb01bd3d4307bee555205f2d3ec8e544b633d907fe',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/research/source-tree.json.gz': '82cd7024107ccc64656ca94a6fdb8309d5a21cdb32f02bb4a99601433251e7eb',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/vcs/package-Cargo.toml': '5257d6f5283ab052b6af51f578a8c74e14c31deb53a7c6cd9e6fa16135d57eb3',
    'licenses/native-dependency-supplements/winapi-i686-pc-windows-gnu-0.4.0/vcs/root-Cargo.toml': '6c719d20dbfa589b729470c52903138941121fdad2ba3d9ebe3985e891261b16',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/LICENSE-APACHE': 'b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/LICENSE-MIT': '5b19674a1db628a475850a131956ed49521b744e3dda8f5a94141f9aba681219',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/crate/Cargo.toml': 'a88605a11db5def9b6cf73398e83b3edb72228cb43ea935729fac5cd33cec22c',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/crate/Cargo.toml.orig': 'd158846cdb1259d606bfbeb050e386484cb18f14db41478568114eddb76ec43e',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/manifest.json': '0084f3d123a0bb3000a74cae263da549ceb7be925433918b94a8bd57fd709f35',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/research/correspondence.json': '4e71e25276621b0efa2da6aa7b28873bee214a27a9edeadc62cf627580821fa8',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/research/source-commit.json': '81f3f74fb2f4d3e7c9bc41bb01bd3d4307bee555205f2d3ec8e544b633d907fe',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/research/source-tree.json.gz': '82cd7024107ccc64656ca94a6fdb8309d5a21cdb32f02bb4a99601433251e7eb',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/vcs/package-Cargo.toml': 'd158846cdb1259d606bfbeb050e386484cb18f14db41478568114eddb76ec43e',
    'licenses/native-dependency-supplements/winapi-x86_64-pc-windows-gnu-0.4.0/vcs/root-Cargo.toml': '6c719d20dbfa589b729470c52903138941121fdad2ba3d9ebe3985e891261b16',
}
MATERIAL_INPUTS = MappingProxyType(MATERIAL_INPUTS)


@dataclass(frozen=True)
class Input:
    source: str
    target: str
    payload: bytes

    def record(self) -> dict:
        return {"source": self.source, "target": self.target,
                "bytes": len(self.payload), "sha256": digest(self.payload)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidArtifact(message)


def directory(path: Path) -> None:
    """Existing ancestors must be unlinked directories; never resolve aliases."""
    try:
        for current in [*reversed(path.parents), path]:
            require(stat.S_ISDIR(current.lstat().st_mode), "Carriage root/parent is not an unlinked directory")
    except OSError as error:
        raise InvalidArtifact("Carriage directory is unavailable") from error


def git(root: Path, *arguments: str) -> str:
    try:
        command = ["git", "-c", "core.fsmonitor=false", "-C", str(root), *arguments]
        result = subprocess.run(command, capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise InvalidArtifact("Independent source Git observation is unavailable") from error
    require(result.returncode == 0 and len(result.stdout) <= MAX_RECEIPT_BYTES,
            "Independent source Git observation failed or exceeded its bound")
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidArtifact("Unreviewed source Git observation encoding") from error


def source_revision(root: Path, expected: str) -> None:
    require(root.is_absolute() and isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{40}", expected),
            "An explicit absolute source root and independently reviewed full revision are required")
    directory(root)
    require(git(root, "rev-parse", "--show-toplevel").strip() == str(root),
            "Supplied source root is not the exact independent Git checkout")
    require(git(root, "rev-parse", "HEAD").strip() == expected, "Independent source differs from reviewed revision")
    require(git(root, "status", "--porcelain", "--untracked-files=normal") == "",
            "Independent carriage source must be clean, not a dirty diagnostic")


def snapshot(root: Path, expected: str) -> tuple[Input, ...]:
    source_revision(root, expected)
    held = []
    for path in CONSUMER_FILES:
        relative = "tests/consumer/" + canonical_path(path)
        payload = regular_bytes(root, relative)
        if path in PRESERVED_CONSUMER_INPUTS:
            require(digest(payload) == PRESERVED_CONSUMER_INPUTS[path],
                    "Full consumer configuration/original Kotlin bodies differ from reviewed source")
        held.append(Input(relative, "independent-consumer/" + path, payload))
    for relative, expected_hash in sorted(MATERIAL_INPUTS.items()):
        payload = regular_bytes(root, relative)
        require(digest(payload) == expected_hash, "Original material/metadata differs from its reviewed fixed bytes")
        if relative.startswith("licenses/"):
            target = "inert-material-context/" + relative
        else:
            target = "inert-material-context/metadata/" + Path(relative).name
        held.append(Input(relative, target, payload))
    require(len(held) == 37 and len({item.target for item in held}) == len(held)
            and sum(len(item.payload) for item in held) <= MAX_INPUT_BYTES,
            "Carriage source/material inventory differs or exceeds its bound")
    # Clean status alone must not admit ignored/untracked input or an edited
    # tracked file hidden by assume-unchanged/skip-worktree flags. Bind this
    # finite inventory to the explicitly supplied committed tree, without
    # reading another archive, collector, native producer or material loader.
    rows = git(root, "ls-tree", "-z", "--full-tree", expected, "--", *(item.source for item in held))
    committed = {}
    for row in rows.split("\0"):
        if not row:
            continue
        match = re.fullmatch(r"(100644|100755) blob ([0-9a-f]{40})\t([^\0\n]+)", row)
        require(match is not None and match[3] not in committed,
                "Carriage source inventory is not an exact committed regular-file tree")
        committed[match[3]] = match[2]
    require(committed == {item.source: git_blob_oid(item.payload) for item in held},
            "Carriage inputs differ from the independently supplied committed source tree")
    return tuple(held)


def receipt(expected: str, inputs: tuple[Input, ...]) -> dict:
    return {"schema_version": 1, "scope": SCOPE, "carrier_source_revision": expected,
            "preserved_native_metadata_producer_revision": METADATA_ORIGIN_REVISION,
            "consumer_source_count": 15, "inert_original_material_count": 22,
            "files": [item.record() for item in inputs],
            "full21_consumer_dependencies_preserved": True,
            "original17_desktop_consumer_methods_preserved": True,
            "consumer_or_native_methods_executed": 0, "collector_or_legacy_loader_executions": 0,
            "crate_payload_scans": 0, "stage_executions": 0,
            "inert_context_is_native_producer_source_root": False,
            "complete_current_native_material_collection": False,
            "source_authenticity_certified": False, "license_obligations_reviewed": False,
            "release_readiness_certified": False}


def encoded(value: dict) -> bytes:
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    require(0 < len(raw) <= MAX_RECEIPT_BYTES, "Carriage receipt exceeds its bound")
    return raw


def verify_material(output: Path, inputs: tuple[Input, ...]) -> None:
    directory(output)
    for item in inputs:
        require(regular_bytes(output, item.target) == item.payload,
                "Copied consumer/helper/material changed or is unavailable")


def exact_output_inventory(output: Path, inputs: tuple[Input, ...], *, receipt_present: bool) -> None:
    """Reject extras before entering them; scan only the finite owned path set."""
    directory(output)
    files = {item.target for item in inputs}
    if receipt_present:
        files.add("carriage.json")
    directories = {parent.as_posix() for relative in files for parent in Path(relative).parents
                   if parent != Path(".")}
    seen_files, seen_directories = set(), set()
    pending = [output]
    try:
        while pending:
            current = pending.pop()
            with os.scandir(current) as entries:
                for entry in entries:
                    relative = (current / entry.name).relative_to(output).as_posix()
                    value = entry.stat(follow_symlinks=False)
                    if relative in files:
                        require(stat.S_ISREG(value.st_mode) and value.st_nlink == 1,
                                "Copied inventory contains a linked or nonregular file")
                        seen_files.add(relative)
                    elif relative in directories:
                        require(stat.S_ISDIR(value.st_mode), "Copied inventory contains a linked/non-directory parent")
                        seen_directories.add(relative)
                        pending.append(current / entry.name)
                    else:
                        raise InvalidArtifact("Copied inventory contains an unrecorded file or directory")
        require(seen_files == files and seen_directories == directories, "Copied inventory is incomplete")
    except OSError as error:
        raise InvalidArtifact("Copied inventory is unavailable") from error


def independent_paths(root: Path, output: Path) -> None:
    require(root.is_absolute() and output.is_absolute()
            and ".." not in root.parts and ".." not in output.parts and ".git" not in output.parts,
            "Carriage source/output must be canonical absolute paths outside Git metadata")
    require(root != output and root not in output.parents and output not in root.parents,
            "Independent output must be outside the source checkout and cannot contain it")
    directory(output.parent)


def prepare(root: Path, output: Path, *, expected_source_revision: str) -> dict:
    """Copy only this explicit finite inventory; keep any refusing partial output."""
    independent_paths(root, output)
    require(not output.exists() and not output.is_symlink(), "Carriage output must be new; never merge or delete preexisting files")
    before = snapshot(root, expected_source_revision)
    output.mkdir()
    for item in before:
        destination = output / canonical_path(item.target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        directory(destination.parent)
        with destination.open("xb") as stream:
            stream.write(item.payload)
    exact_output_inventory(output, before, receipt_present=False)
    verify_material(output, before)
    require(before == snapshot(root, expected_source_revision), "Independent source changed during carriage")
    report = receipt(expected_source_revision, before)
    with (output / "carriage.json").open("xb") as stream:
        stream.write(encoded(report))
    exact_output_inventory(output, before, receipt_present=True)
    return report


def verify(root: Path, output: Path, *, expected_source_revision: str) -> dict:
    """Compare with independent source, never merely trust a self-rehashed receipt."""
    independent_paths(root, output)
    before = snapshot(root, expected_source_revision)
    exact_output_inventory(output, before, receipt_present=True)
    verify_material(output, before)
    expected = receipt(expected_source_revision, before)
    require(regular_bytes(output, "carriage.json", MAX_RECEIPT_BYTES) == encoded(expected),
            "Carriage receipt differs from independent source or falsely clears execution/readiness gates")
    require(before == snapshot(root, expected_source_revision), "Independent source changed during carriage verification")
    return expected


SMOKE_SOURCE = r'''
import hashlib, importlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
assert root.is_absolute() and root.is_dir()
sys.path.insert(0, str(root))
modules = ("verify_artifacts", "native_license_supplements", "native_license_legacy_winapi",
           "native_license_objc2_material", "native_license_material_v2",
           "collect_native_licenses", "verify_native_test_results")
records = {}
for name in modules:
    module = importlib.import_module(name)
    path = pathlib.Path(module.__file__)
    assert path.parent == root and path.name == name + ".py"
    raw = path.read_bytes()
    records[path.name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
print(json.dumps({"copied_checker_imports": records, "material_loader_executions": 0,
                  "native_or_consumer_methods_executed": 0, "release_readiness_certified": False}, sort_keys=True))
'''


def smoke_command(checker: Path) -> list[str]:
    """Command recipe only; tests/imports are separately authorized and recorded."""
    require(checker.is_absolute(), "Smoke checker path must be absolute")
    return [sys.executable, "-I", "-S", "-B", "-c", SMOKE_SOURCE, str(checker)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--expected-source-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        report = (verify if args.verify_only else prepare)(args.source_root, args.output,
            expected_source_revision=args.expected_source_revision)
        print(json.dumps({"carrier_source_revision": report["carrier_source_revision"],
                          "consumer_source_count": 15, "inert_original_material_count": 22,
                          "release_readiness_certified": False}, sort_keys=True))
        return 0
    except (InvalidArtifact, OSError) as error:
        print(json.dumps({"carriage_complete": False, "error": str(error), "release_readiness_certified": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
