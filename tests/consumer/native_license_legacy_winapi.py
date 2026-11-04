"""Two explicitly reviewed legacy archives; never a general missing-origin waiver.

The public 0.4.0 WinAPI import archives predate Cargo VCS metadata and omitted
license texts. Their complete real payload fingerprints were independently sealed
before this adapter. Pin those exact archive/proof/source bytes, reconstruct the
source Git trees, and recheck the compressed archive identity without rescanning
accepted payloads. This is material correspondence, NOT authenticity/legal review.
"""
from __future__ import annotations

from collections import defaultdict
import gzip
import io
from pathlib import Path
from types import MappingProxyType
import hashlib
import tomllib
import zlib

from native_license_supplements import (MAX_CATALOG_BYTES, MAX_FILE_BYTES,
    Supplement, canonical_path, digest, git_blob_oid,
    regular_bytes, text_bytes)
from verify_artifacts import CHECKSUM, InvalidArtifact, load_json_bytes

SCHEMA = 3  # Separate from v1 and the deliberately inert objc2 v2 research.
KIND = "legacy-winapi-archive-source-correspondence"
SCOPE = ("Two exact reviewed legacy WinAPI archives without Cargo VCS metadata; "
         "pinned complete source correspondence, not authenticity or legal clearance")
REPOSITORY = "https://github.com/retep998/winapi-rs"
REVISION = "9497609ef44cc9bcd16cd2411c0ee6ccaf5483aa"
ROOT_TREE = "8146a2db00f01713763b925d8b5a8f13bf917f7a"
TREE_JSON_SHA256 = "3e74d9f541ba3b4cf45f747cd3586c53e07a0b4eeb4b6bc5e3565dc6cc639411"
MAX_TREE_BYTES = 2 * 1024 * 1024
MAX_TREE_NODES = 6000
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024

# These are reviewed registry/source facts, not replaceable report assertions.
PACKAGES = {
    "winapi-i686-pc-windows-gnu": {
        "checksum": "ac3b87c63620426dd9b991e5ce0329eff545bccbbb34f3be09ff6fb6ab51b7b6",
        "path": "i686", "archive_bytes": 2918815, "members": 1390,
        "uncompressed_bytes": 50931525,
        "fingerprints": "b137358205dc0436953e5d891f2fcc14543fed135016d71e2978b1435eba2940",
        "normalized": "9652222664ffc7e2a26fdcdebdce0917a455b39d8fbcbf451bf0b011a3067bf7",
        "original": "5257d6f5283ab052b6af51f578a8c74e14c31deb53a7c6cd9e6fa16135d57eb3",
    },
    "winapi-x86_64-pc-windows-gnu": {
        "checksum": "712e227841d057c1ee1cd2fb22fa7e5a5461ae8e48fa2ca79ec42cfc1931183f",
        "path": "x86_64", "archive_bytes": 2947998, "members": 1419,
        "uncompressed_bytes": 53158180,
        "fingerprints": "4e71e25276621b0efa2da6aa7b28873bee214a27a9edeadc62cf627580821fa8",
        "normalized": "a88605a11db5def9b6cf73398e83b3edb72228cb43ea935729fac5cd33cec22c",
        "original": "d158846cdb1259d606bfbeb050e386484cb18f14db41478568114eddb76ec43e",
    },
}
COMMON_PROOFS = {
    "vcs/root-Cargo.toml": "6c719d20dbfa589b729470c52903138941121fdad2ba3d9ebe3985e891261b16",
    "LICENSE-MIT": "5b19674a1db628a475850a131956ed49521b744e3dda8f5a94141f9aba681219",
    "LICENSE-APACHE": "b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1",
    "research/source-commit.json": "81f3f74fb2f4d3e7c9bc41bb01bd3d4307bee555205f2d3ec8e544b633d907fe",
    "research/source-tree.json.gz": "82cd7024107ccc64656ca94a6fdb8309d5a21cdb32f02bb4a99601433251e7eb",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidArtifact(message)


def immutable(value):
    if isinstance(value, dict):
        return MappingProxyType({key: immutable(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(immutable(item) for item in value)
    return value


PACKAGES = immutable(PACKAGES)
COMMON_PROOFS = immutable(COMMON_PROOFS)


class LegacyWinapiSupplement(Supplement):
    """Held immutable material; inherited ordinary VCS text records stay explicit."""

    def provenance_payloads(self, prefix: str) -> dict[str, bytes]:
        result = super().provenance_payloads(prefix)
        result.update({prefix + "provenance/" + record["catalog_path"]:
                       self.contents[record["catalog_path"]]
                       for record in self.manifest["provenance_files"]})
        return result

    def material_record(self, prefix: str) -> dict:
        result = super().material_record(prefix)
        result.update(kind=KIND, root_tree_oid=ROOT_TREE,
                      archive_vcs_metadata_present=False,
                      correspondence_sha256=PACKAGES[self.manifest["package"]["name"]]["fingerprints"],
                      source_authenticity_certified=False,
                      license_obligations_reviewed=False)
        return result


def source_tree(payload: bytes) -> dict:
    """Reconstruct every cached source tree; no network or archive payload read."""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as stream:
            raw = stream.read(MAX_TREE_BYTES + 1)
    except (OSError, EOFError, zlib.error) as error:
        raise InvalidArtifact("Invalid legacy source tree envelope") from error
    require(0 < len(raw) <= MAX_TREE_BYTES and digest(raw) == TREE_JSON_SHA256,
            "Legacy source tree differs from independently sealed public bytes")
    data = load_json_bytes(raw)
    require(isinstance(data, dict) and data.get("sha") == ROOT_TREE
            and data.get("truncated") is False and isinstance(data.get("tree"), list)
            and 0 < len(data["tree"]) <= MAX_TREE_NODES,
            "Legacy source tree must be complete and exact")
    entries, groups = {}, defaultdict(list)
    for record in data["tree"]:
        require(isinstance(record, dict), "Invalid legacy Git tree member")
        path = canonical_path(record.get("path"))
        require(path not in entries and record.get("type") in ("tree", "blob")
                and record.get("mode") in ("040000", "100644", "100755"),
                "Invalid/duplicate legacy Git tree path/type/mode")
        oid = record.get("sha")
        require(isinstance(oid, str) and len(oid) == 40
                and all(character in "0123456789abcdef" for character in oid),
                "Invalid legacy Git object identity")
        entries[path] = record
        groups[path.rpartition("/")[0]].append(record)
    for parent, children in groups.items():
        body = bytearray()
        for record in sorted(children, key=lambda value:
                value["path"].rsplit("/", 1)[-1].encode()
                + (b"/" if value["type"] == "tree" else b"")):
            name = record["path"].rsplit("/", 1)[-1]
            body.extend(record["mode"].lstrip("0").encode() + b" " + name.encode()
                        + b"\0" + bytes.fromhex(record["sha"]))
        oid = hashlib.sha1(b"tree " + str(len(body)).encode() + b"\0" + body).hexdigest()
        expected = ROOT_TREE if not parent else entries.get(parent, {}).get("sha")
        require(oid == expected, "Legacy Git tree differs from the pinned commit root")
    return entries


def load_legacy(entry: Path, package: dict, data: dict, raw: bytes) -> LegacyWinapiSupplement:
    """Called only for exact schema3; v1's mandatory Cargo VCS proof is unchanged."""
    keys = {"schema_version", "kind", "scope", "package", "repository", "revision",
            "root_tree_oid", "path_in_vcs", "archive_vcs_metadata_present",
            "source_authenticity_certified", "license_obligations_reviewed",
            "crate_files", "vcs_files", "license_files", "provenance_files"}
    require(isinstance(data, dict) and set(data) == keys
            and type(data["schema_version"]) is int and data["schema_version"] == SCHEMA,
            "Expected exact separately reviewed legacy supplement schema")
    spec = PACKAGES.get(package.get("name"))
    require(spec is not None and package.get("version") == "0.4.0"
            and package.get("checksum") == spec["checksum"]
            and package.get("license") == "MIT/Apache-2.0"
            and package.get("source_kind") == "crates.io"
            and package.get("license_file") is None,
            "No legacy supplement outside the two exact reviewed registry archives")
    require(entry.name == package["name"] + "-0.4.0", "Foreign legacy catalog entry identity")
    expected_package = {key: package[key] for key in ("name", "version", "checksum", "license")}
    require(data["package"] == expected_package and data["kind"] == KIND
            and data["scope"] == SCOPE and data["repository"] == REPOSITORY
            and data["revision"] == REVISION and data["root_tree_oid"] == ROOT_TREE
            and data["path_in_vcs"] == spec["path"]
            and data["archive_vcs_metadata_present"] is False
            and data["source_authenticity_certified"] is False
            and data["license_obligations_reviewed"] is False,
            "Legacy origin/scope differs or falsely asserts VCS/authenticity/legal clearance")
    expected = {
        "crate_files": {"Cargo.toml": "crate/Cargo.toml", "Cargo.toml.orig": "crate/Cargo.toml.orig"},
        "vcs_files": {"Cargo.toml": "vcs/root-Cargo.toml",
                      spec["path"] + "/Cargo.toml": "vcs/package-Cargo.toml"},
        "license_files": {"LICENSE-MIT": "LICENSE-MIT", "LICENSE-APACHE": "LICENSE-APACHE"},
        "provenance_files": {"correspondence.json": "research/correspondence.json",
                             "source-commit.json": "research/source-commit.json",
                             "source-tree.json.gz": "research/source-tree.json.gz"},
    }
    hashes = COMMON_PROOFS | {
        "crate/Cargo.toml": spec["normalized"], "crate/Cargo.toml.orig": spec["original"],
        "vcs/package-Cargo.toml": spec["original"],
        "research/correspondence.json": spec["fingerprints"],
    }
    contents, seen = {"manifest.json": raw}, set()
    for kind, paths in expected.items():
        records = data[kind]
        require(isinstance(records, list) and len(records) == len(paths),
                "Legacy proof/text set is incomplete")
        found = set()
        for record in records:
            git = kind in ("vcs_files", "license_files")
            fields = {"path", "catalog_path", "bytes", "sha256"} | ({"git_blob_oid"} if git else set())
            require(isinstance(record, dict) and set(record) == fields,
                    "Unexpected legacy proof/text record fields")
            path, local = canonical_path(record["path"]), canonical_path(record["catalog_path"])
            require(path in paths and paths[path] == local and path not in found
                    and local not in seen, "Unexpected/duplicate legacy proof/text path")
            found.add(path); seen.add(local)
            require(type(record["bytes"]) is int and 0 < record["bytes"] <= MAX_FILE_BYTES
                    and record["sha256"] == hashes[local],
                    "Legacy proof/text differs from reviewed fixed bytes")
            payload = regular_bytes(entry, local)
            require(len(payload) == record["bytes"] and digest(payload) == hashes[local],
                    "Legacy material was substituted, truncated or self-rehashed")
            if git:
                require(git_blob_oid(payload) == record["git_blob_oid"],
                        "Legacy source text is not its pinned Git blob")
            if kind == "license_files":
                text_bytes(payload)
            contents[local] = payload
        require(found == set(paths), "Legacy complete source/proof coverage is required")
    require(sum(map(len, contents.values())) <= MAX_CATALOG_BYTES,
            "Legacy material exceeds the existing aggregate catalog bound")
    commit = load_json_bytes(contents["research/source-commit.json"])
    require(commit.get("sha") == REVISION and commit.get("tree", {}).get("sha") == ROOT_TREE,
            "Legacy reported source commit/root differ")
    tree = source_tree(contents["research/source-tree.json.gz"])
    for record in data["vcs_files"] + data["license_files"]:
        source = tree.get(record["path"])
        require(source is not None and source["type"] == "blob"
                and source["sha"] == record["git_blob_oid"]
                and source.get("size") == record["bytes"],
                "Legacy source manifest/license is not in the exact commit tree")
    for local in ("crate/Cargo.toml", "crate/Cargo.toml.orig", "vcs/package-Cargo.toml"):
        try:
            fields = tomllib.loads(contents[local].decode("utf-8"))["package"]
        except (UnicodeDecodeError, tomllib.TOMLDecodeError, KeyError, TypeError) as error:
            raise InvalidArtifact("Unreviewed legacy package manifest format") from error
        require(all(fields.get(key) == expected_package[key] for key in ("name", "version", "license"))
                and fields.get("repository") == REPOSITORY,
                "Legacy manifests differ from exact registry identity/license/origin")
    root = tomllib.loads(contents["vcs/root-Cargo.toml"].decode("utf-8"))["package"]
    require(root.get("license") == "MIT/Apache-2.0" and root.get("repository") == REPOSITORY,
            "Legacy shared root does not declare the exact explicit license/origin")
    require(contents["crate/Cargo.toml.orig"] == contents["vcs/package-Cargo.toml"],
            "Legacy original manifest is not the exact source manifest")
    fingerprints = load_json_bytes(contents["research/correspondence.json"])
    rows = fingerprints.get("payload_files")
    require(fingerprints.get("package") == package
            and fingerprints.get("source_revision") == REVISION
            and fingerprints.get("root_tree_sha") == ROOT_TREE
            and fingerprints.get("source_tree_response_sha256") == TREE_JSON_SHA256
            and fingerprints.get("compared_members") == fingerprints.get("matching_members") == spec["members"]
            and fingerprints.get("mismatching_members") == 0
            and fingerprints.get("archive_member_count") == spec["members"] + 1
            and fingerprints.get("archive_uncompressed_bytes") == spec["uncompressed_bytes"]
            and fingerprints.get("license_obligations_reviewed") is False
            and fingerprints.get("source_authenticity_certified") is False
            and isinstance(rows, list) and len(rows) == spec["members"],
            "Legacy complete once-sealed registry/source correspondence is required")
    member_paths, total_bytes = set(), 0
    for row in rows:
        require(isinstance(row, dict), "Invalid legacy payload fingerprint")
        relative = canonical_path(row.get("crate_path"))
        source_path = spec["path"] + "/" + ("Cargo.toml" if relative == "Cargo.toml.orig" else relative)
        source = tree.get(source_path)
        require(relative not in member_paths and relative != ".cargo_vcs_info.json"
                and row.get("source_path") == source_path and row.get("exact_source_match") is True
                and source is not None and source["type"] == "blob" and source["mode"] == "100644"
                and row.get("git_blob_oid") == row.get("source_blob_oid") == source["sha"]
                and type(row.get("bytes")) is int and row["bytes"] == source.get("size")
                and isinstance(row.get("sha256"), str) and CHECKSUM.fullmatch(row["sha256"]),
                "Legacy member is absent/changed or not in the exact source tree")
        member_paths.add(relative); total_bytes += row["bytes"]
    normalized = fingerprints.get("normalized_manifest", {})
    require(normalized.get("sha256") == spec["normalized"]
            and normalized.get("bytes") == len(contents["crate/Cargo.toml"])
            and total_bytes + normalized["bytes"] == spec["uncompressed_bytes"],
            "Legacy normalized manifest/payload coverage differs")
    return LegacyWinapiSupplement(entry.name, immutable(data), MappingProxyType(contents))


def verify_archive(path: Path, supplement: LegacyWinapiSupplement) -> None:
    """Rebind known compressed bytes only; no tar scan/build/execution or waiver."""
    name = supplement.manifest["package"]["name"]
    spec = PACKAGES[name]
    require(path.name == name + "-0.4.0.crate", "Foreign legacy archive filename")
    raw = regular_bytes(path.parent, path.name, MAX_ARCHIVE_BYTES)
    require(len(raw) == spec["archive_bytes"] and digest(raw) == spec["checksum"],
            "Legacy archive differs from the once-reviewed exact locked bytes")
