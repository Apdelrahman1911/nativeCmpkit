"""Inert, offline dual-origin evidence for the finite objc2 notice review.

This adapter does not implement collector fallback or publication approval. Raw
Git object hashes bind original crate manifests and separate text-origin records; they
are not publisher signatures. A source-reviewed index hash is required. Even
fully matching bytes retain the unresolved attribution/SDK/applicability gaps.
V1 JNI/archive collection and independent publication gates remain unchanged.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from pathlib import Path
import hashlib
import tomllib

from native_license_supplements import (GIT_OID, MAX_CATALOG_BYTES, MAX_FILE_BYTES,
    MAX_MANIFEST_BYTES, Supplement, canonical_path, digest, git_blob_oid,
    regular_bytes, text_bytes, verify_crate_correspondence)
from verify_artifacts import CHECKSUM, CRATE_NAME, CRATE_VERSION, InvalidArtifact, load_json_bytes

SCOPE = "Pending exact objc2 dual-origin material; no legal, publisher or staging clearance"
KIND = "pending-dual-origin-license-material"
REPOSITORY = "https://github.com/madsmtm/objc2"
MATERIAL_REVISION = "ee9a7ada2131f5944b8750428e265c15632f2a19"
MIT_ONLY = frozenset({"block2", "objc2", "objc2-encode", "objc2-foundation"})
SELECTED_NAMES = MIT_ONLY | frozenset({"dispatch2", "objc2-app-kit", "objc2-cloud-kit",
    "objc2-core-data", "objc2-core-foundation", "objc2-core-graphics", "objc2-core-image",
    "objc2-core-text", "objc2-core-video", "objc2-io-surface", "objc2-quartz-core"})
INPUT_PATHS = frozenset(f"{module}/native/{name}" for module in ("calf-file-picker", "calf-share")
                        for name in ("Cargo.toml", "Cargo.lock"))
OR_TERMS = "Zlib OR Apache-2.0 OR MIT"
OBLIGATIONS = {"exact_release_text_applicability": "unreviewed", "contributor_notices": "unreviewed",
    "sdk_source_and_distribution": "unreviewed", "selected_license_option": None,
    "license_obligations_reviewed": False, "complete_material_collection": False,
    "ready_for_staging": False, "publisher_provenance_verified": False}
FILE_FIELDS = {"catalog_path", "bytes", "sha256"}
ORIGIN_FIELDS = {"repository", "revision", "git_commit", "git_trees", "publisher_signature_verified"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidArtifact(message)


def exact(data, fields: set[str]) -> None:
    require(isinstance(data, dict) and set(data) == fields, "Unexpected v2 evidence fields")


def registry_package(package) -> None:
    exact(package, {"id", "name", "version", "checksum", "license", "source_kind", "license_file"})
    require(isinstance(package["name"], str) and CRATE_NAME.fullmatch(package["name"])
            and isinstance(package["version"], str) and CRATE_VERSION.fullmatch(package["version"])
            and isinstance(package["checksum"], str) and CHECKSUM.fullmatch(package["checksum"])
            and package["name"] in SELECTED_NAMES and package["id"] == package["name"] + "@" + package["version"]
            and package["source_kind"] == "crates.io" and package["license_file"] is None,
            "Unexpected exact v2 registry identity")


def version(data, kind: str) -> None:
    require(type(data["schema_version"]) is int and data["schema_version"] == 2
            and data["kind"] == kind and data["scope"] == SCOPE, "Unexpected v2 schema/scope")


def unresolved(data) -> None:
    exact(data, set(OBLIGATIONS))
    require(data == OBLIGATIONS and all(type(data[key]) is type(value) for key, value in OBLIGATIONS.items()),
            "V2 cannot clear unresolved obligations or select a license option")


def oid(kind: str, raw: bytes) -> str:
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class Reader:
    """Capture each bounded no-follow input once; the caller holds public roots."""
    def __init__(self, root: Path):
        self.root = root
        self.contents: dict[str, bytes] = {}

    def file(self, record: dict, extra: set[str] = frozenset()) -> bytes:
        exact(record, FILE_FIELDS | extra)
        local = canonical_path(record["catalog_path"])
        require(type(record["bytes"]) is int and 0 < record["bytes"] <= MAX_FILE_BYTES
                and isinstance(record["sha256"], str) and CHECKSUM.fullmatch(record["sha256"]),
                "Invalid v2 byte/hash binding")
        if local not in self.contents:
            self.contents[local] = regular_bytes(self.root, local)
        raw = self.contents[local]
        require(len(raw) == record["bytes"] and digest(raw) == record["sha256"],
                "V2 bytes differ from the reviewed binding")
        require(sum(map(len, self.contents.values())) <= 4 * MAX_CATALOG_BYTES,
                "V2 catalog exceeds its aggregate bound")
        return raw


def parse_tree(raw: bytes) -> dict[str, tuple[bytes, str]]:
    entries, offset = {}, 0
    while offset < len(raw):
        space, nul = raw.find(b" ", offset), raw.find(b"\0", offset)
        require(offset < space < nul and nul + 21 <= len(raw), "Malformed raw Git tree")
        mode, name = raw[offset:space], raw[space + 1:nul]
        require(mode in (b"40000", b"100644", b"100755", b"120000", b"160000"), "Unknown Git tree mode")
        try:
            name = name.decode("utf-8")
        except UnicodeDecodeError as error:
            raise InvalidArtifact("Unreviewed Git tree path encoding") from error
        require(canonical_path(name) == name and "/" not in name and name not in entries,
                "Unsafe/duplicate raw Git tree entry")
        entries[name] = mode, raw[nul + 1:nul + 21].hex()
        offset = nul + 21
    require(bool(entries), "Empty raw Git tree proof")
    return entries


def origin(reader: Reader, data: dict, files: list[dict], *, license_files: bool = False) -> dict:
    exact(data, ORIGIN_FIELDS)
    require(isinstance(data["revision"], str) and GIT_OID.fullmatch(data["revision"])
            and data["publisher_signature_verified"] is False, "V2 cannot verify a publisher signature")
    raw = reader.file(data["git_commit"], {"git_oid"})
    require(data["git_commit"]["git_oid"] == data["revision"] == oid("commit", raw),
            "V2 requires the authentic raw commit object, not API reconstruction")
    headers, separator, _ = raw.partition(b"\n\n")
    tree_headers = [line[5:] for line in headers.split(b"\n") if line.startswith(b"tree ")]
    require(bool(separator) and len(tree_headers) == 1, "Raw commit has no unique root tree")
    try:
        root_oid = tree_headers[0].decode("ascii")
    except UnicodeDecodeError as error:
        raise InvalidArtifact("Malformed commit root tree") from error
    require(bool(GIT_OID.fullmatch(root_oid)), "Invalid raw commit root tree")
    records = data["git_trees"]
    require(isinstance(records, list) and 1 <= len(records) <= 8, "Bounded complete raw tree proof required")
    trees = {}
    for record in records:
        tree_raw = reader.file(record, {"git_oid"})
        tree_oid = record["git_oid"]
        require(isinstance(tree_oid, str) and GIT_OID.fullmatch(tree_oid)
                and tree_oid == oid("tree", tree_raw) and tree_oid not in trees,
                "Invalid/duplicate raw tree object")
        trees[tree_oid] = parse_tree(tree_raw)
    require(root_oid in trees, "Commit's actual root tree proof is missing")
    require(isinstance(files, list) and 1 <= len(files) <= 8, "Bounded source/text proof list required")
    used, paths = set(), set()
    for record in files:
        extra = {"path", "git_blob_oid"} | ({"license_id", "copyright_literal"} if license_files else set())
        payload = reader.file(record, extra)
        path = canonical_path(record["path"])
        require(path not in paths and record["git_blob_oid"] == git_blob_oid(payload), "Invalid/duplicate Git blob proof")
        paths.add(path)
        current, parts = root_oid, Path(path).parts
        for index, part in enumerate(parts):
            require(current in trees, "Missing intermediate raw tree proof")
            used.add(current)
            require(part in trees[current], "Source/text path absent in the actual commit tree")
            mode, child = trees[current][part]
            if index == len(parts) - 1:
                require(mode in (b"100644", b"100755") and child == record["git_blob_oid"],
                        "Source/text blob is not a regular file in its stated commit")
            else:
                require(mode == b"40000", "Source/text proof traverses a non-tree entry")
                current = child
        text_bytes(payload)
        if license_files:
            require(isinstance(record["copyright_literal"], str) and record["copyright_literal"]
                    and record["copyright_literal"].encode("utf-8") in payload,
                    "Authentic copyright literal is not preserved")
    require(used == set(trees), "Unnecessary/unbound raw tree proof")
    return {"revision": data["revision"], "root_tree_oid": root_oid,
            "embedded_signature_present": any(line.startswith((b"gpgsig ", b"gpgsig-sha256 "))
                                              for line in headers.split(b"\n")),
            "publisher_signature_verified": False}


def resolve_manifests(package: dict, crate: dict[str, bytes], source: dict[str, bytes], path: str) -> dict:
    require(crate["Cargo.toml.orig"] == source[path + "/Cargo.toml"],
            "Original crate manifest differs from the pinned source package")
    try:
        normalized = tomllib.loads(crate["Cargo.toml"].decode("utf-8"))["package"]
        original = tomllib.loads(crate["Cargo.toml.orig"].decode("utf-8"))["package"]
        workspace = tomllib.loads(source["Cargo.toml"].decode("utf-8"))["workspace"]["package"]
        def resolve(field):
            value = original[field]
            if isinstance(value, dict):
                require(set(value) == {"workspace"} and value["workspace"] is True,
                        "Unreviewed Cargo inheritance form")
                return workspace[field]
            return value
        for field in ("name", "version", "license", "repository"):
            expected = REPOSITORY if field == "repository" else package[field]
            require(normalized[field] == resolve(field) == expected,
                    "Exact normalized/package/workspace license or identity does not match")
        require("license-file" not in normalized and "license-file" not in original,
                "Declared license-file needs an independent format decision")
    except (KeyError, TypeError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise InvalidArtifact("Invalid exact Cargo manifest inheritance proof") from error
    return {"original_license_field": original["license"], "resolved_license": package["license"],
            "mode": "workspace-inherited" if isinstance(original["license"], dict) else "package-override"}


def relationship(reader: Reader, record: dict, revision: str) -> None:
    exact(record, {"evidence", "status", "source_is_ancestor_reported", "merge_base_revision", "raw_history_verified"})
    require(record["raw_history_verified"] is False, "Shallow object evidence cannot assert full ancestry")
    data = load_json_bytes(reader.file(record["evidence"]))
    expected_url = "https://api.github.com/repos/madsmtm/objc2/compare/" + revision + "..." + MATERIAL_REVISION
    require(isinstance(data, dict) and isinstance(data.get("base_commit"), dict)
            and isinstance(data.get("merge_base_commit"), dict) and data.get("url") == expected_url
            and data.get("base_commit", {}).get("sha") == revision
            and data.get("status") == record["status"]
            and data.get("merge_base_commit", {}).get("sha") == record["merge_base_revision"],
            "Reported API relationship differs from its preserved exact comparison")
    reported = data.get("status") == "ahead" and data.get("behind_by") == 0 and record["merge_base_revision"] == revision
    require(type(record["source_is_ancestor_reported"]) is bool
            and record["source_is_ancestor_reported"] == reported, "Do not infer ancestry for a divergent source")


def _freeze(value):
    """Own a defensive, recursively read-only snapshot of validated JSON/bytes."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(child) for child in value)
    return value


def _plain(value):
    """Return detached JSON containers, never references to the held snapshot."""
    if isinstance(value, Mapping):
        return {key: _plain(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(child) for child in value]
    return value


@dataclass(frozen=True)
class PendingMaterial:
    identity: str
    manifest: Mapping
    contents: Mapping[str, bytes]
    git_observations: Mapping

    def __post_init__(self) -> None:
        # Frozen dataclasses alone do not prevent nested mutation or caller aliases.
        for name in ("manifest", "contents", "git_observations"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))

    def evidence_record(self) -> dict:
        return _plain({"schema_version": 2, "kind": KIND, "package": self.manifest["package"],
                "manifest_sha256": digest(self.contents[self.identity + "/manifest.json"]),
                "source_origin": self.manifest["source_origin"], "text_origin": self.manifest["text_origin"],
                "relationship": self.manifest["relationship"], "license_resolution": self.manifest["license_resolution"],
                "attribution_lead": self.manifest["attribution_lead"], "obligations": dict(OBLIGATIONS),
                "files": [{"catalog_path": path, "bytes": len(raw), "sha256": digest(raw)}
                          for path, raw in sorted(self.contents.items())]})


def load_material(reader: Reader, record: dict) -> PendingMaterial:
    raw = reader.file(record, {"package"})
    data = load_json_bytes(raw)
    fields = {"schema_version", "kind", "scope", "package", "crate_files", "source_origin", "source_files",
              "path_in_vcs", "text_origin", "policy_file", "license_files", "license_resolution",
              "relationship", "attribution_lead", "research_files", "obligations"}
    exact(data, fields)
    version(data, KIND)
    package = data["package"]
    registry_package(package)
    require(package == record["package"], "V2 package differs from the reviewed index")
    identity = canonical_path(package["name"] + "-" + package["version"])
    require(record["catalog_path"] == identity + "/manifest.json" and len(raw) <= MAX_MANIFEST_BYTES,
            "Unexpected/big per-package v2 manifest")
    expected_license = "MIT" if package["name"] in MIT_ONLY else OR_TERMS
    require(package["license"] == expected_license, "V2 cannot expand original license options")
    unresolved(data["obligations"])
    path = canonical_path(data["path_in_vcs"])
    require(isinstance(data["crate_files"], list) and len(data["crate_files"]) == 3, "Exact three crate proofs required")
    for item in data["crate_files"]:
        exact(item, FILE_FIELDS | {"path"})
        require(canonical_path(item["path"]) in {".cargo_vcs_info.json", "Cargo.toml", "Cargo.toml.orig"},
                "Unexpected exact v2 crate proof path")
    crate = {item["path"]: reader.file(item, {"path"}) for item in data["crate_files"]}
    require(set(crate) == {".cargo_vcs_info.json", "Cargo.toml", "Cargo.toml.orig"}, "Incomplete/duplicate crate proofs")
    exact(data["source_origin"], ORIGIN_FIELDS)
    exact(data["text_origin"], ORIGIN_FIELDS)
    require(data["source_origin"]["repository"] == data["text_origin"]["repository"] == REPOSITORY
            and data["source_origin"]["revision"] != MATERIAL_REVISION
            and data["text_origin"]["revision"] == MATERIAL_REVISION, "Original source and separate text-origin records must remain separate")
    source_observation = origin(reader, data["source_origin"], data["source_files"])
    source = {item["path"]: reader.contents[item["catalog_path"]] for item in data["source_files"]}
    require(set(source) == {"Cargo.toml", path + "/Cargo.toml", "LICENSE.md"}, "Exact root/package/policy proofs required")
    require(load_json_bytes(crate[".cargo_vcs_info.json"]) == {
        "git": {"sha1": data["source_origin"]["revision"]}, "path_in_vcs": path}, "Crate VCS origin/path mismatch")
    require(data["license_resolution"] == resolve_manifests(package, crate, source, path),
            "License inheritance record differs from original source bytes")
    licenses = data["license_files"]
    require(isinstance(licenses, list) and all(isinstance(item, dict) and isinstance(item.get("license_id"), str) for item in licenses)
            and {item.get("license_id") for item in licenses} ==
            ({"MIT"} if expected_license == "MIT" else {"MIT", "Apache-2.0", "Zlib"})
            and len(licenses) == (1 if expected_license == "MIT" else 3), "Original license options must be retained exactly")
    text_observation = origin(reader, data["text_origin"], licenses, license_files=True)
    # Policy is separately bound to the same actual material tree, never called a crate license file.
    origin(reader, data["text_origin"], [data["policy_file"]])
    relationship(reader, data["relationship"], data["source_origin"]["revision"])
    lead = data["attribution_lead"]
    exact(lead, {"origin", "notice_file", "applicability"})
    exact(lead["origin"], ORIGIN_FIELDS)
    require(lead["applicability"] == "unreviewed" and lead["origin"]["repository"] == "https://github.com/SSheldon/rust-objc",
            "Earlier notices are attribution leads, not assigned release notices")
    origin(reader, lead["origin"], [lead["notice_file"]])
    require(isinstance(data["research_files"], list) and 1 <= len(data["research_files"]) <= 8, "Bounded public research context required")
    for item in data["research_files"]:
        reader.file(item)
    # Include shared records already captured for another package as well as new ones.
    referenced = {record["catalog_path"]}
    def collect_paths(value):
        if isinstance(value, dict):
            if "catalog_path" in value:
                referenced.add(value["catalog_path"])
            for child in value.values():
                collect_paths(child)
        elif isinstance(value, list):
            for child in value:
                collect_paths(child)
    collect_paths(data)
    require(all(local in reader.contents for local in referenced), "Uncaptured v2 proof")
    return PendingMaterial(identity, data, {local: reader.contents[local] for local in referenced},
                           {"source": source_observation, "text": text_observation})


def load_material_set(catalog: Path, source_root: Path, *, reviewed_index_sha256: str) -> tuple[PendingMaterial, ...]:
    """Validate only this reviewed finite set; no graph/metadata regeneration or I/O writes."""
    require(isinstance(reviewed_index_sha256, str) and CHECKSUM.fullmatch(reviewed_index_sha256),
            "An independent reviewed v2 index SHA256 is required")
    raw = regular_bytes(catalog, "manifest.json", MAX_MANIFEST_BYTES)
    require(digest(raw) == reviewed_index_sha256, "V2 index differs from independently reviewed source")
    index = load_json_bytes(raw)
    exact(index, {"schema_version", "kind", "scope", "inputs", "packages", "obligations"})
    version(index, KIND + "-set")
    unresolved(index["obligations"])
    reader = Reader(catalog)
    records = index["inputs"]
    require(isinstance(records, list) and len(records) == 4
            and all(isinstance(item, dict) and isinstance(item.get("source_path"), str) for item in records)
            and {item.get("source_path") for item in records} == INPUT_PATHS, "Exact two-module manifest/lock bindings required")
    locks = []
    for item in records:
        payload = reader.file(item, {"source_path"})
        require(payload == regular_bytes(source_root, item["source_path"]), "Source input changed since material review")
        if item["source_path"].endswith("Cargo.lock"):
            try:
                entries = tomllib.loads(payload.decode("utf-8"))["package"]
                require(isinstance(entries, list) and all(isinstance(item, dict) for item in entries), "Invalid lock package list")
                locks.append(entries)
            except (KeyError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
                raise InvalidArtifact("Invalid bound Cargo.lock") from error
    records = index["packages"]
    require(isinstance(records, list) and len(records) == 15
            and all(isinstance(item, dict) and isinstance(item.get("package"), dict)
                    and isinstance(item["package"].get("name"), str) for item in records)
            and {item["package"].get("name") for item in records} == SELECTED_NAMES,
            "V2 requires all fifteen exact selected identities")
    for item in records:
        exact(item, FILE_FIELDS | {"package"})
        package = item["package"]
        registry_package(package)
        for lock in locks:
            matches = [entry for entry in lock if entry.get("name") == package["name"] and entry.get("version") == package["version"]]
            require(len(matches) == 1 and matches[0].get("checksum") == package["checksum"]
                    and matches[0].get("source") == "registry+https://github.com/rust-lang/crates.io-index",
                    "V2 package does not match both current exact registry locks")
    return tuple(load_material(reader, record) for record in records)


def verify_archive(path: Path, material: PendingMaterial) -> None:
    """Reuse the unchanged checksum/path/member proof boundary; no license fallback."""
    verify_crate_correspondence(path, Supplement(material.identity,
        {"package": material.manifest["package"], "crate_files": material.manifest["crate_files"]}, material.contents))


def inspect_evidence(material: PendingMaterial, record: dict, payloads: dict[str, bytes]) -> None:
    """Independent held-catalog comparison; self-rehashed producer reports do not suffice."""
    require(record == material.evidence_record() and payloads == material.contents,
            "Pending evidence differs from the exact independently reviewed origins/proofs/text")


def pending_report(materials: tuple[PendingMaterial, ...]) -> dict:
    return {"schema_version": 2, "kind": KIND + "-report", "scope": SCOPE, **OBLIGATIONS,
            "packages": [item.evidence_record() for item in materials],
            "gaps": [{"package": item.identity, "reason": "Exact-release text applicability, contributor notices and SDK obligations remain unreviewed"}
                     for item in materials]}
