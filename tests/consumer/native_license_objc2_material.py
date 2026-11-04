"""Explicit finite schema4 public material adoption; never publication/legal approval.

Inert v2 stays inert. Only its bounded raw-object/workspace primitives are reused.
The independently reviewed index binds all fifteen original locked releases and
four current Cargo inputs. Full known notice texts and the genuine Rust credit
are preserved; generated SDK source and API-reported Rust origins are not promoted
into raw source, publisher, all-contributor or release attestations.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from native_license_material_v2 import (INPUT_PATHS, MIT_ONLY, SELECTED_NAMES,
    Reader, _freeze, _plain, exact, oid, origin, parse_tree, registry_package,
    require, resolve_manifests)
from native_license_supplements import (MAX_CATALOG_BYTES, MAX_FILE_BYTES,
    Supplement, canonical_path, digest, git_blob_oid, regular_bytes, text_bytes)
from verify_artifacts import InvalidArtifact, load_json_bytes

SCHEMA = 4
KIND = "adopted-public-objc2-material"
SCOPE = "Exact fifteen original objc2 package grants and known public notices; not legal, SDK, native or release clearance"
INDEX_PATH = "objc2-reviewed/manifest.json"
REVIEWED_INDEX_SHA256 = "4f10a64a9a62c07484cd1d45512141ea91b5652078b004b6e30e39988b218131"
OBLIGATIONS = {"license_obligations_reviewed": False, "publisher_provenance_verified": False,
    "SDK_source_and_distribution": "unreviewed", "all_contributor_copyright_exhaustively_verified": False,
    "release_readiness_certified": False}
RUST_REVISION = "1e5719bdc40bb553089ce83525f07dfe0b2e71e9"
RUST_MERGE = "349fbba24f0158c1ed293658c31de5c8a0954e5a"
RUST_HEAD = "846d6a4466813f3ad12e2bf15db4071f22b8ae0b"
INDEX_FIELDS = {"schema_version", "kind", "scope", "inputs", "packages", "mads", "steven", "rust",
                "source_classification", "research_files", "obligations"}
ROW_FIELDS = {"package", "path_in_vcs", "crate_files", "source_files", "source_origin", "archive_bytes",
              "license_options", "additional_notices"}


def referenced(value) -> set[str]:
    result = set()
    if isinstance(value, dict):
        if "catalog_path" in value:
            result.add(canonical_path(value["catalog_path"]))
        for child in value.values():
            result.update(referenced(child))
    elif isinstance(value, list):
        for child in value:
            result.update(referenced(child))
    return result


def original_text(record: dict) -> dict:
    """Output filenames do not replace actual source paths or original blob IDs."""
    exact(record, {"catalog_path", "bytes", "sha256", "path", "git_blob_oid", "license_id",
                   "copyright_literal", "output_path"})
    canonical_path(record["output_path"])
    return {key: value for key, value in record.items() if key != "output_path"}


def inputs(reader: Reader, records: list, source_root: Path) -> list[list[dict]]:
    require(isinstance(records, list) and len(records) == 4
            and {record.get("source_path") for record in records if isinstance(record, dict)} == INPUT_PATHS,
            "Schema4 requires exactly the two current module manifests and locks")
    locks = []
    for record in records:
        payload = reader.file(record, {"source_path"})
        require(payload == regular_bytes(source_root, record["source_path"]),
                "Current Cargo input differs from the independently reviewed material index")
        if record["source_path"].endswith("Cargo.lock"):
            try:
                entries = tomllib.loads(payload.decode("utf-8"))["package"]
                require(isinstance(entries, list) and all(isinstance(entry, dict) for entry in entries),
                        "Invalid exact Cargo.lock package records")
                locks.append(entries)
            except (KeyError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
                raise InvalidArtifact("Invalid bound schema4 lock") from error
    return locks


def rust_notices(reader: Reader, data: dict) -> list[dict]:
    exact(data, {"origin", "notice_files", "copy_source", "copy_origin"})
    stated = data["origin"]
    exact(stated, {"kind", "repository", "revision", "root_tree_oid", "commit_api", "tree_api",
                  "raw_commit_verified", "publisher_signature_verified", "PR_head_revision",
                  "PR_merge_revision", "fixed_revision_equals_PR_head_or_merge"})
    require(stated["kind"] == "public-api-reported-copied-source-notices"
            and stated["repository"] == "https://github.com/rust-lang/rust"
            and stated["revision"] == RUST_REVISION and stated["PR_head_revision"] == RUST_HEAD
            and stated["PR_merge_revision"] == RUST_MERGE
            and stated["raw_commit_verified"] is False and stated["publisher_signature_verified"] is False
            and stated["fixed_revision_equals_PR_head_or_merge"] is False,
            "Reported Rust source cannot become a raw-commit, merged-source or publisher attestation")
    commit = load_json_bytes(reader.file(stated["commit_api"]))
    tree = load_json_bytes(reader.file(stated["tree_api"]))
    require(isinstance(commit, dict) and commit.get("sha") == RUST_REVISION
            and commit.get("tree", {}).get("sha") == stated["root_tree_oid"]
            and isinstance(tree, dict) and tree.get("sha") == stated["root_tree_oid"]
            and tree.get("truncated") is False, "Rust API-reported fixed revision/root differs")
    entries = tree.get("tree")
    require(isinstance(entries, list) and all(isinstance(entry, dict) for entry in entries),
            "Invalid reported Rust root entries")
    by_path = {entry["path"]: entry for entry in entries}
    require(len(by_path) == len(entries), "Duplicate reported Rust tree path")
    files = data["notice_files"]
    require(isinstance(files, list) and len(files) == 3
            and {item.get("path") for item in files if isinstance(item, dict)} == {"LICENSE-MIT", "LICENSE-APACHE", "COPYRIGHT"},
            "Rust holderless MIT must retain its full COPYRIGHT and Apache policy")
    for item in files:
        payload = reader.file(item, {"path", "git_blob_oid", "output_path"})
        canonical_path(item["output_path"])
        expected = by_path.get(item["path"], {})
        require(git_blob_oid(payload) == item["git_blob_oid"] == expected.get("sha")
                and expected.get("type") == "blob" and expected.get("mode") in ("100644", "100755"),
                "Rust notice differs from the reported fixed source tree/blob")
        text_bytes(payload)
        if item["path"] == "COPYRIGHT":
            require(b"Copyrights in the Rust project are retained by their contributors." in payload
                    and b"Rust is\nlicensed under the Apache License" in payload,
                    "Actual Rust contributor copyright and grant policy is required")
    origin(reader, data["copy_origin"], [data["copy_source"]])
    copied = reader.contents[data["copy_source"]["catalog_path"]]
    require(copied.startswith(b"//! Heavily copied from:\n//! <https://github.com/rust-lang/rust/pull/138944>")
            and RUST_REVISION.encode() in copied, "Actual published Rust-copy credit must remain")
    return files


def source_classification(reader: Reader, data: dict, rows: list[dict]) -> None:
    exact(data, {"original_payload_report", "raw_source_custody", "new_public_operations", "raw_tree_routes",
                 "raw_trees", "source_blobs", "Git_generated_directory_symlink_targets_verified",
                 "generated_SDK_source_equivalence_verified", "Cargo_lock_generation_provenance_verified",
                 "gitignore_is_generated_exclusion_proof"})
    for key in ("Git_generated_directory_symlink_targets_verified", "generated_SDK_source_equivalence_verified",
                "Cargo_lock_generation_provenance_verified", "gitignore_is_generated_exclusion_proof"):
        require(data[key] is False, "Unverified generated/SDK/lock provenance cannot be cleared")
    report = load_json_bytes(reader.file(data["original_payload_report"]))
    require(report.get("totals") == {"archives": 15, "compressed_bytes": 1911956, "generated_metadata_matches": 30,
            "notice_hit_lines": 136, "regular_files": 1130, "retained_source_notice_files": 16,
            "source_absent": 789, "source_matches": 309, "source_mismatches": 2, "tar_bytes": 15882240},
            "Exact once-qualified released source inventory differs")
    by_package = {row["package"]["id"]: row for row in report["rows"]}
    require(len(by_package) == len(report["rows"]) == 15, "Incomplete/duplicate released source inventory")
    for row in rows:
        held = by_package.get(row["package"]["id"])
        require(held is not None and held["package"] == row["package"]
                and held["compressed_bytes"] == row["archive_bytes"]
                and held["publishing_revision"] == row["source_origin"]["revision"]
                and held["source_path_in_vcs"] == row["path_in_vcs"], "Published archive/source identity differs")
        for file in held["files"]:
            path = canonical_path(file["archive_relative_path"])
            if file["class"] == "source-path-absent":
                require(path == "Cargo.lock" or path.startswith("src/generated/"),
                        "Unknown absent source path cannot be treated as generated material")
            elif file["class"] == "source-mismatch":
                require(row["package"]["name"] in {"dispatch2", "objc2-core-foundation"}
                        and path == "src/retained/forwarding_impls.rs"
                        and file["git_blob_oid"] == "d4c61a21974f4952d77cb63c9600c7d8a18cc0fe",
                        "Unreviewed source mismatch cannot be admitted")
            else:
                require(file["class"] in {"source-match", "generated-published-metadata"},
                        "Unknown released source class")
    reader.file(data["raw_source_custody"])
    reader.file(data["new_public_operations"])
    route_data = load_json_bytes(reader.file(data["raw_tree_routes"]))
    require(isinstance(route_data.get("routes"), list) and len(route_data["routes"]) == 7,
            "Exact seven independent original raw-tree routes required")
    trees = {}
    for record in data["raw_trees"]:
        payload = reader.file(record, {"git_oid"})
        require(record["git_oid"] == oid("tree", payload) and record["git_oid"] not in trees,
                "Malformed/duplicate source route raw tree")
        trees[record["git_oid"]] = parse_tree(payload)
    commits = {row["source_origin"]["revision"]: row["source_origin"]["git_commit"] for row in rows}
    for route in route_data["routes"]:
        root_headers = [line[5:].decode("ascii") for line in reader.contents[commits[route["revision"]]["catalog_path"]]
                        .split(b"\n\n", 1)[0].splitlines() if line.startswith(b"tree ")]
        require(len(root_headers) == 1, "Source route has no unique raw commit root")
        current = root_headers[0]
        require(len(route["steps"]) == len(canonical_path(route["path"]).split("/")), "Incomplete raw path route")
        for step, part in zip(route["steps"], route["path"].split("/")):
            require(step["tree_oid"] == current and step["component"] == part and current in trees
                    and part in trees[current], "Raw-tree route differs from the stated source path")
            mode, child = trees[current][part]
            require(mode.decode() == step["selected_mode"] and child == step["selected_oid"],
                    "Actual raw source tree edge differs")
            current = child
        require(current == route["expected_blob_oid"] and mode.decode() == route["expected_mode"],
                "Raw-tree route does not reach the exact source blob/mode")
    for record in data["source_blobs"]:
        payload = reader.file(record, {"path", "git_blob_oid"})
        require(git_blob_oid(payload) == record["git_blob_oid"], "Public source-classification blob differs")
        if record["path"] == "symlink-target":
            require(payload == b"../../../../crates/objc2/src/rc/retained_forwarding_impls.rs",
                    "Actual source symlink target differs")


def validate_set(reader: Reader, data: dict, source_root: Path) -> tuple[list[dict], list[dict]]:
    exact(data, INDEX_FIELDS)
    require(type(data["schema_version"]) is int and data["schema_version"] == SCHEMA
            and data["kind"] == KIND and data["scope"] == SCOPE, "Unexpected active schema4 identity/scope")
    exact(data["obligations"], set(OBLIGATIONS))
    require(data["obligations"] == OBLIGATIONS
            and all(type(data["obligations"][key]) is type(value) for key, value in OBLIGATIONS.items()),
            "Active notice material cannot clear legal/publisher/SDK/release gates")
    locks = inputs(reader, data["inputs"], source_root)
    rows = data["packages"]
    require(isinstance(rows, list) and len(rows) == 15
            and {row.get("package", {}).get("name") for row in rows if isinstance(row, dict)} == SELECTED_NAMES,
            "All fifteen original locked identities required, not a partial/foreign set")
    for row in rows:
        exact(row, ROW_FIELDS)
        package = row["package"]
        registry_package(package)
        options = ["MIT"] if package["name"] in MIT_ONLY else ["Zlib", "Apache-2.0", "MIT"]
        require(row["license_options"] == options and package["license"] == ("MIT" if options == ["MIT"] else "Zlib OR Apache-2.0 OR MIT"),
                "Four MIT-only and eleven trio grants cannot be expanded, selected or dropped")
        require(row["additional_notices"] == ["steven"] + (["rust"] if package["name"] == "objc2" else []),
                "Genuine inherited and copied-source notices must be retained")
        require(type(row["archive_bytes"]) is int and 0 < row["archive_bytes"] <= 16 * 1024 * 1024,
                "Invalid reviewed compressed archive bound")
        for lock in locks:
            matches = [item for item in lock if item.get("name") == package["name"] and item.get("version") == package["version"]]
            require(len(matches) == 1 and matches[0].get("checksum") == package["checksum"]
                    and matches[0].get("source") == "registry+https://github.com/rust-lang/crates.io-index",
                    "Adopted identity differs from both current exact registry locks")
        require(isinstance(row["crate_files"], list) and len(row["crate_files"]) == 3,
                "Three original published manifest/VCS proofs required")
        crate = {item["path"]: reader.file(item, {"path"}) for item in row["crate_files"]}
        require(set(crate) == {"Cargo.toml", "Cargo.toml.orig", ".cargo_vcs_info.json"},
                "Incomplete/duplicate original crate proofs")
        path = canonical_path(row["path_in_vcs"])
        require(row["source_origin"]["repository"] == "https://github.com/madsmtm/objc2"
                and row["source_origin"]["revision"] != data["mads"]["origin"]["revision"],
                "Publishing source and later populated text origins must remain distinct")
        origin(reader, row["source_origin"], row["source_files"])
        source = {item["path"]: reader.contents[item["catalog_path"]] for item in row["source_files"]}
        require(set(source) == {"Cargo.toml", path + "/Cargo.toml", "LICENSE.md"}, "Exact root/package/policy source proofs required")
        require(load_json_bytes(crate[".cargo_vcs_info.json"]) == {"git": {"sha1": row["source_origin"]["revision"]}, "path_in_vcs": path},
                "Published VCS pointer differs from original source")
        resolve_manifests(package, crate, source, path)
    exact(data["mads"], {"origin", "license_files", "policy_file"})
    mads = data["mads"]["license_files"]
    require(isinstance(mads, list) and len(mads) == 3
            and {item.get("license_id") for item in mads if isinstance(item, dict)} == {"MIT", "Apache-2.0", "Zlib"},
            "Three genuine populated Mads option texts required")
    require(data["mads"]["origin"]["repository"] == "https://github.com/madsmtm/objc2"
            and data["mads"]["origin"]["revision"] == "ee9a7ada2131f5944b8750428e265c15632f2a19", "Wrong original complete-text origin")
    origin(reader, data["mads"]["origin"], [original_text(item) for item in mads], license_files=True)
    origin(reader, data["mads"]["origin"], [data["mads"]["policy_file"]])
    exact(data["steven"], {"origin", "notice_file"})
    steven = data["steven"]["notice_file"]
    require(steven["copyright_literal"] == "Copyright (c) Steven Sheldon" and steven["license_id"] == "MIT"
            and data["steven"]["origin"]["repository"] == "https://github.com/SSheldon/rust-objc",
            "Original Steven notice is yearless, not maintainer-only or an invented relicensing permission")
    origin(reader, data["steven"]["origin"], [original_text(steven)], license_files=True)
    rust_notices(reader, data["rust"])
    source_classification(reader, data["source_classification"], rows)
    require(isinstance(data["research_files"], list) and len(data["research_files"]) == 5, "Exact preserved public discussion/PR context required")
    research = {Path(item["catalog_path"]).name: load_json_bytes(reader.file(item)) for item in data["research_files"]}
    require(len(research["objc2-issue23-comments.json"]) == 5 and len(research["objc2-issue826-comments.json"]) == 11,
            "Original issue23 has five comments; issue826 has eleven, not twelve")
    require(research["rust-PR138944.json"].get("merge_commit_sha") == RUST_MERGE
            and research["rust-PR138944.json"].get("head", {}).get("sha") == RUST_HEAD,
            "Original Rust PR head/merge differs from preserved distinct context")
    require(referenced(data) <= set(reader.contents), "Required source/text/context proof was not captured")
    return rows, mads


@dataclass(frozen=True)
class AdoptedObjc2Supplement(Supplement):
    """Owned immutable exact set; shared proof pool is emitted once per module."""
    def __post_init__(self):
        object.__setattr__(self, "manifest", _freeze(self.manifest))
        object.__setattr__(self, "contents", _freeze(self.contents))

    def license_entries(self, prefix: str) -> list[dict]:
        return [{"path": prefix + item["output_path"], "bytes": item["bytes"], "sha256": item["sha256"],
                 "origin": _plain(item["origin"])} for item in self.manifest["license_files"]]

    def license_payloads(self, prefix: str) -> dict[str, bytes]:
        return {prefix + item["output_path"]: self.contents[item["catalog_path"]]
                for item in self.manifest["license_files"]}

    def provenance_payloads(self, prefix: str) -> dict[str, bytes]:
        require(prefix.endswith(self.identity + "/"), "Owning adopted package prefix required")
        shared = prefix[:-len(self.identity + "/")] + "_reviewed-objc2/"
        return {shared + path: payload for path, payload in sorted(self.contents.items())}

    def material_record(self, prefix: str) -> dict:
        return _plain({"schema_version": SCHEMA, "kind": KIND, "catalog_entry": self.identity,
                "reviewed_index_sha256": REVIEWED_INDEX_SHA256, "source_origin": self.manifest["source_origin"],
                "path_in_vcs": self.manifest["path_in_vcs"], "license_options": self.manifest["license_options"],
                "obligations": self.manifest["obligations"], "generated_source_and_Rust_API_limits_retained": True,
                "provenance_files": [{"path": path, "bytes": len(payload), "sha256": digest(payload)}
                                     for path, payload in self.provenance_payloads(prefix).items()]})


def load_adopted_set(catalog: Path, source_root: Path | None) -> dict[str, AdoptedObjc2Supplement]:
    group = catalog / "objc2-reviewed"
    if not group.exists() and not group.is_symlink():
        return {}
    require(source_root is not None, "Active schema4 requires an explicit current source root")
    raw = regular_bytes(catalog, INDEX_PATH, MAX_CATALOG_BYTES)
    require(digest(raw) == REVIEWED_INDEX_SHA256, "Active index differs from independently reviewed source, not a producer-selected digest")
    data = load_json_bytes(raw)
    reader = Reader(group)
    reader.contents["manifest.json"] = raw
    rows, mads = validate_set(reader, data, source_root)
    require(set(reader.contents) == {"manifest.json"} | referenced(data), "Unexpected public material capture")
    result = {}
    for row in rows:
        files = []
        for item in [*([item for item in mads if item["license_id"] in row["license_options"]]), data["steven"]["notice_file"]]:
            inherited = item is data["steven"]["notice_file"]
            stated = data["steven"]["origin"] if inherited else data["mads"]["origin"]
            files.append(item | {"origin": {"kind": "pinned-vcs", "repository": stated["repository"],
                "revision": stated["revision"], "path": item["path"], "git_blob_oid": item["git_blob_oid"],
                "role": "retained-inherited-attribution" if inherited else "original-license-option"}})
        if row["package"]["name"] == "objc2":
            for item in data["rust"]["notice_files"]:
                files.append(item | {"origin": {"kind": "public-api-reported-copied-source-notices",
                    "repository": "https://github.com/rust-lang/rust", "revision": RUST_REVISION,
                    "path": item["path"], "git_blob_oid": item["git_blob_oid"], "role": "retained-copied-source-notice",
                    "raw_commit_verified": False, "fixed_revision_equals_PR_head_or_merge": False}})
        identity = row["package"]["name"] + "-" + row["package"]["version"]
        manifest = row | {"schema_version": SCHEMA, "license_files": files, "obligations": dict(OBLIGATIONS)}
        result[row["package"]["id"]] = AdoptedObjc2Supplement(identity, manifest, reader.contents)
    return result


def verify_archive(path: Path, supplement: AdoptedObjc2Supplement) -> None:
    """Rebind already once-qualified locked compressed bytes; NEVER rescan payloads."""
    require(isinstance(supplement, AdoptedObjc2Supplement), "Unreviewed schema4 implementation")
    payload = regular_bytes(path.parent, path.name, 16 * 1024 * 1024)
    require(len(payload) == supplement.manifest["archive_bytes"]
            and digest(payload) == supplement.manifest["package"]["checksum"],
            "Adopted archive differs from its exact once-qualified locked size/checksum")
