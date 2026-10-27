"""Explicit reviewed public VCS material; never fetch, extract, execute or clear legal gates.

The source-controlled catalog is an input to review, not an authenticity attestation.
Collection separately binds its proof bytes to the locked .crate. Artifact inspection
compares the complete external-origin record and proof/text bytes to that same reviewed
catalog, rather than trusting a report boolean or substituting an SPDX template.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import os
from pathlib import Path
import re
import stat
import tarfile
import tomllib

from verify_artifacts import (CHECKSUM, InvalidArtifact, autodiscovered_license_path,
                              load_json_bytes, relative_notice_path)

CATALOG_RELATIVE = "licenses/native-dependency-supplements"
SCOPE = "Pinned public VCS license material with checksum-bound crate correspondence; not legal clearance"
MAX_FILE_BYTES = 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_CATALOG_BYTES = 8 * 1024 * 1024
MAX_CRATE_BYTES = 16 * 1024 * 1024
MAX_CRATE_MEMBERS = 50_000
MAX_CRATE_UNCOMPRESSED = 64 * 1024 * 1024
GIT_OID = re.compile(r"[0-9a-f]{40}\Z")
PUBLIC_REPOSITORY = re.compile(r"https://github\.com/[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_path(value) -> str:
    value = relative_notice_path(value)
    if any(ord(character) < 32 for character in value) or ".git" in Path(value).parts:
        raise InvalidArtifact("Invalid public supplement path")
    return value


def regular_bytes(root: Path, relative: str, maximum: int = MAX_FILE_BYTES) -> bytes:
    """Hold bounded regular bytes and reject observed links/replacement/mutation.

    This is not a filesystem sandbox against an independently malicious same-UID
    writer. Source/catalog/cache roots must be explicitly public and held by the
    caller; directory identities and the opened file are checked before/after.
    """
    canonical_path(relative)
    root = root.absolute()
    parents = [*reversed(root.parents), root]
    child = root
    for part in Path(relative).parts[:-1]:
        child /= part
        parents.append(child)
    identities = []
    try:
        for parent in parents:
            value = parent.lstat()
            if not stat.S_ISDIR(value.st_mode):
                raise InvalidArtifact("Supplement root/parent is not an unlinked directory")
            identities.append((parent, value.st_dev, value.st_ino))
        path = root / relative
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= maximum:
            raise InvalidArtifact("Supplement input must be bounded, nonempty and an unshared regular file")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        try:
            stream = os.fdopen(descriptor, "rb")
        except BaseException:
            # No stream received ownership, so its context manager cannot close
            # this descriptor. Construction failure must not leak the raw open.
            os.close(descriptor)
            raise
        with stream:
            opened = os.fstat(stream.fileno())
            fields = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
                                    value.st_ctime_ns, value.st_nlink, value.st_mode)
            if fields(before) != fields(opened):
                raise InvalidArtifact("Supplement input was replaced before opening")
            payload = stream.read(maximum + 1)
            if len(payload) != before.st_size or fields(opened) != fields(os.fstat(stream.fileno())):
                raise InvalidArtifact("Supplement input changed or exceeded its bound")
        if fields(before) != fields(path.lstat()):
            raise InvalidArtifact("Supplement input was replaced while reading")
        for parent, device, inode in identities:
            value = parent.lstat()
            if not stat.S_ISDIR(value.st_mode) or (value.st_dev, value.st_ino) != (device, inode):
                raise InvalidArtifact("Supplement input directory changed while reading")
        return payload
    except OSError as error:
        raise InvalidArtifact("Required public supplement input is unavailable") from error


def text_bytes(payload: bytes) -> None:
    try:
        payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise InvalidArtifact("Supplement text has an unreviewed encoding") from error
    if b"\x00" in payload:
        raise InvalidArtifact("Supplement license material is binary")


def git_blob_oid(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


@dataclass(frozen=True)
class Supplement:
    identity: str
    manifest: dict
    contents: dict[str, bytes]

    def license_entries(self, prefix: str) -> list[dict]:
        return [{"path": prefix + record["path"], "bytes": record["bytes"], "sha256": record["sha256"],
                 "origin": {"kind": "pinned-vcs", "repository": self.manifest["repository"],
                            "revision": self.manifest["revision"], "path": record["path"],
                            "git_blob_oid": record["git_blob_oid"]}}
                for record in self.manifest["license_files"]]

    def license_payloads(self, prefix: str) -> dict[str, bytes]:
        return {prefix + record["path"]: self.contents[record["catalog_path"]]
                for record in self.manifest["license_files"]}

    def provenance_payloads(self, prefix: str) -> dict[str, bytes]:
        paths = {"manifest.json", *(record["catalog_path"] for record in
                                   self.manifest["crate_files"] + self.manifest["vcs_files"])}
        return {prefix + "provenance/" + path: self.contents[path] for path in sorted(paths)}

    def material_record(self, prefix: str) -> dict:
        return {"kind": "pinned-vcs", "catalog_entry": self.identity,
                "manifest_sha256": digest(self.contents["manifest.json"]),
                "repository": self.manifest["repository"], "revision": self.manifest["revision"],
                "path_in_vcs": self.manifest["path_in_vcs"],
                "provenance_files": [{"path": path, "bytes": len(payload), "sha256": digest(payload)}
                                     for path, payload in self.provenance_payloads(prefix).items()]}


def load_supplement(catalog: Path, package: dict) -> Supplement | None:
    """Only the exact requested catalog entry is read; never scan/export other roots."""
    identity = package["name"] + "-" + package["version"]
    canonical_path(identity)
    entry = catalog / identity
    if not entry.exists() and not entry.is_symlink():
        return None
    raw = regular_bytes(entry, "manifest.json", MAX_MANIFEST_BYTES)
    data = load_json_bytes(raw)
    keys = {"schema_version", "package", "repository", "revision", "path_in_vcs", "crate_files",
            "vcs_files", "license_files", "scope", "license_obligations_reviewed"}
    expected_package = {key: package[key] for key in ("name", "version", "checksum", "license")}
    if not isinstance(data, dict) or set(data) != keys or type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise InvalidArtifact("Expected exact public VCS supplement schema")
    if data["package"] != expected_package or package["source_kind"] != "crates.io" or package["license_file"] is not None:
        raise InvalidArtifact("Supplement does not match the exact registry package/checksum/license contract")
    if data["scope"] != SCOPE or data["license_obligations_reviewed"] is not False:
        raise InvalidArtifact("Supplement cannot assert legal clearance")
    if not isinstance(data["repository"], str) or not PUBLIC_REPOSITORY.fullmatch(data["repository"]):
        raise InvalidArtifact("Supplement origin must be a canonical public GitHub repository")
    if not isinstance(data["revision"], str) or not GIT_OID.fullmatch(data["revision"]):
        raise InvalidArtifact("Supplement requires an immutable VCS commit")
    path_in_vcs = canonical_path(data["path_in_vcs"])
    contents, seen_paths = {"manifest.json": raw}, set()
    for kind in ("crate_files", "vcs_files", "license_files"):
        records = data[kind]
        if not isinstance(records, list) or not 1 <= len(records) <= 8:
            raise InvalidArtifact("Supplement proof/text records must be complete and bounded")
        seen_kind = set()
        for record in records:
            fields = {"path", "catalog_path", "bytes", "sha256"} | ({"git_blob_oid"} if kind != "crate_files" else set())
            if not isinstance(record, dict) or set(record) != fields:
                raise InvalidArtifact("Unexpected supplement file record fields")
            path, local = canonical_path(record["path"]), canonical_path(record["catalog_path"])
            if path in seen_kind or local in seen_paths or local == "manifest.json":
                raise InvalidArtifact("Duplicate/overlapping supplement proof/text record")
            seen_kind.add(path)
            seen_paths.add(local)
            if type(record["bytes"]) is not int or not 0 < record["bytes"] <= MAX_FILE_BYTES:
                raise InvalidArtifact("Invalid supplement text/proof byte count")
            if not isinstance(record["sha256"], str) or not CHECKSUM.fullmatch(record["sha256"]):
                raise InvalidArtifact("Supplement requires complete SHA256 file bindings")
            payload = regular_bytes(entry, local)
            if len(payload) != record["bytes"] or digest(payload) != record["sha256"]:
                raise InvalidArtifact("Supplement file bytes do not match their reviewed binding")
            if kind != "crate_files" and (not isinstance(record["git_blob_oid"], str)
                    or not GIT_OID.fullmatch(record["git_blob_oid"]) or git_blob_oid(payload) != record["git_blob_oid"]):
                raise InvalidArtifact("Supplement file differs from its immutable Git blob")
            if kind == "license_files":
                if not autodiscovered_license_path(path) or path.startswith("provenance/"):
                    raise InvalidArtifact("Supplement is not a license/notice text path")
                text_bytes(payload)
            contents[local] = payload
        if kind == "crate_files" and seen_kind != {".cargo_vcs_info.json", "Cargo.toml", "Cargo.toml.orig"}:
            raise InvalidArtifact("Supplement needs exact crate VCS and both manifest proofs")
        if kind == "vcs_files" and seen_kind != {"Cargo.toml", path_in_vcs + "/Cargo.toml"}:
            raise InvalidArtifact("Supplement needs exact root and package VCS manifests")
    if sum(map(len, contents.values())) > MAX_CATALOG_BYTES:
        raise InvalidArtifact("Supplement material exceeds its aggregate bound")
    crate = {record["path"]: contents[record["catalog_path"]] for record in data["crate_files"]}
    vcs = {record["path"]: contents[record["catalog_path"]] for record in data["vcs_files"]}
    info = load_json_bytes(crate[".cargo_vcs_info.json"])
    if info != {"git": {"sha1": data["revision"]}, "path_in_vcs": path_in_vcs}:
        raise InvalidArtifact("Crate VCS proof differs from the reviewed commit/path")
    if crate["Cargo.toml.orig"] != vcs[path_in_vcs + "/Cargo.toml"]:
        raise InvalidArtifact("Crate original manifest is not the exact VCS package manifest")
    try:
        for payload in (crate["Cargo.toml"], crate["Cargo.toml.orig"]):
            original = tomllib.loads(payload.decode("utf-8"))["package"]
            if any(original[key] != expected_package[key] for key in ("name", "version", "license")) or original["repository"] != data["repository"]:
                raise InvalidArtifact("Crate manifest identity/license/origin differs from catalog")
        root_package = tomllib.loads(vcs["Cargo.toml"].decode("utf-8"))["package"]
        if root_package["license"] != expected_package["license"] or root_package["repository"] != data["repository"]:
            raise InvalidArtifact("Shared root license/origin differs from the explicit package contract")
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, KeyError, TypeError) as error:
        raise InvalidArtifact("Supplement manifests need a separately reviewed inheritance/format decision") from error
    return Supplement(identity, data, contents)


def verify_crate_correspondence(path: Path, supplement: Supplement) -> None:
    """Recheck captured exact .crate bytes; fallback cannot hide checksum/link/path errors."""
    raw = regular_bytes(path.parent, path.name, MAX_CRATE_BYTES)
    if digest(raw) != supplement.manifest["package"]["checksum"]:
        raise InvalidArtifact("Supplement crate differs from its locked checksum")
    expected = {record["path"]: supplement.contents[record["catalog_path"]]
                for record in supplement.manifest["crate_files"]}
    seen, found, total = set(), set(), 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for index, member in enumerate(archive):
            total += member.size
            if index >= MAX_CRATE_MEMBERS or total > MAX_CRATE_UNCOMPRESSED or member.size < 0:
                raise InvalidArtifact("Supplement crate exceeds entry/uncompressed bound")
            canonical_path(member.name)
            parts = Path(member.name).parts
            if not parts or parts[0] != supplement.identity:
                raise InvalidArtifact("Supplement crate member has a foreign package prefix")
            if member.isdir():
                continue
            if len(parts) < 2 or not member.isfile():
                raise InvalidArtifact("Supplement crate includes a nonregular member")
            relative = Path(*parts[1:]).as_posix()
            if relative in seen:
                raise InvalidArtifact("Duplicate supplement crate member")
            seen.add(relative)
            if relative in expected:
                if member.size != len(expected[relative]) or member.size > MAX_FILE_BYTES:
                    raise InvalidArtifact("Supplement crate proof has different byte counts")
                stream = archive.extractfile(member)  # Bounded read only; never extract to disk.
                if stream is None:
                    raise InvalidArtifact("Supplement crate proof is unreadable")
                with stream:
                    payload = stream.read(MAX_FILE_BYTES + 1)
                if payload != expected[relative]:
                    raise InvalidArtifact("Supplement proof differs from the locked .crate bytes")
                found.add(relative)
    if found != set(expected):
        raise InvalidArtifact("Supplement crate correspondence proof is incomplete")
