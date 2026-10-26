"""Bounded read-only payload inspection; writes only new evidence beside this file.

No archive extraction, subprocess, networking, imports from project/build plugins,
artifact execution, or publication. Existing evidence outputs are never replaced.
"""
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import io
import json
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[5]
DEST = Path(__file__).resolve().parent
MIB = 1024 * 1024
LIMITS = {
    "archive_bytes": 16 * MIB,
    "all_archive_bytes": 64 * MIB,
    "entries_per_archive": 2048,
    "all_entries": 8192,
    "entry_uncompressed_bytes": 32 * MIB,
    "archive_uncompressed_bytes": 64 * MIB,
    "all_uncompressed_bytes": 128 * MIB,
    "expansion_ratio": 1000,
    "entry_name_utf8_bytes": 512,
    "selected_text_bytes": MIB,
}
ALGORITHMS = ("sha512", "sha256", "sha1", "md5")
ARCHIVES = {"002": "752dd23858147dd2d84b1a8f0e61aa778822671b4570e7d6a21a918f3301e712",
            "003": "2731bc0c502d1b4b470f4861a03c7f81a26441726a9643a7eb83ba895e745ed6"}


def safe_path(relative):
    rel = PurePosixPath(relative)
    assert not rel.is_absolute() and ".." not in rel.parts
    current = ROOT
    for part in rel.parts:
        current = current / part
        assert not current.is_symlink(), relative
    assert current.resolve().is_relative_to(ROOT), relative
    return current


def bounded_bytes(relative, limit=16 * MIB):
    path = safe_path(relative)
    before = path.stat()
    assert stat.S_ISREG(before.st_mode) and before.st_size <= limit, relative
    with path.open("rb") as stream:
        value = stream.read(limit + 1)
    after = path.stat()
    assert len(value) == before.st_size <= limit
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (
        after.st_size, after.st_mtime_ns, after.st_ino), relative
    return value, before


def digest(value):
    return hashlib.sha256(value).hexdigest()


def load(relative):
    return json.loads(bounded_bytes(relative)[0])


def output(name, value):
    with (DEST / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


assert not (DEST / "receipt.json").exists()
started = dt.datetime.now(dt.timezone.utc).isoformat()
input_path = "docs/development/evidence/io-metadata-observation-003/run/inputs-after.json"
inputs = load(input_path)
assert len(inputs) == 693
assert all(digest(bounded_bytes(p)[0]) == h for p, h in inputs.items())
for run, expected in ARCHIVES.items():
    assert digest(bounded_bytes(f"docs/development/evidence/io-metadata-observation-{run}/archive.json")[0]) == expected

browser_path = "docs/development/evidence/build/browser004-runtime-readback.json"
browser_bytes = bounded_bytes(browser_path)[0]
assert digest(browser_bytes) == "c1d01fed012b9deacef40a93f7660ca15895690d3121dbbaa7ef5e768a194808"
browser_resources = {x["filename"]: x for x in json.loads(browser_bytes)["io_resources"]}
payloads, module_rows, references, entry_lists = [], [], [], []
compared_source_files, compared_notice_files = {}, {}
total_archive_bytes = total_entries = total_uncompressed_bytes = total_selected_bytes = 0

for publication, run in (("desktop", "002"), ("js", "003"), ("wasmJs", "003")):
    module_path = f"docs/development/evidence/io-metadata-observation-{run}/observed-outputs/{publication}/module.json"
    module_bytes = bounded_bytes(module_path)[0]
    module = json.loads(module_bytes)
    archive = load(f"docs/development/evidence/io-metadata-observation-{run}/archive.json")
    observation = next(x for x in archive["observed_outputs"] if x.get("archive") == module_path)
    assert observation["fresh_in_run"] and digest(module_bytes) == observation["sha256"]
    module_rows.append({"publication": publication, "path": module_path,
                        "sha256": digest(module_bytes), "component": module["component"],
                        "variants": module["variants"]})
    distinct = {}
    for variant in module["variants"]:
        for declaration in variant.get("files", []):
            name = declaration["name"]
            assert PurePosixPath(name).name == name and "\\" not in name
            directory = (f"calf-io/build/kotlin-multiplatform-resources/zip-for-publication/{publication}"
                         if name.endswith(".kotlin_resources.zip") else "calf-io/build/libs")
            relative = directory + "/" + name
            references.append({"publication": publication, "variant": variant["name"],
                               "local_path": relative, "declaration": declaration})
            if relative in distinct:
                assert distinct[relative] == declaration
            else:
                distinct[relative] = declaration
    for relative, declaration in distinct.items():
        data, observed = bounded_bytes(relative, LIMITS["archive_bytes"])
        assert len(data) == declaration["size"]
        hashes = {algorithm: hashlib.new(algorithm, data).hexdigest() for algorithm in ALGORITHMS}
        assert all(hashes[k] == declaration[k] for k in ALGORITHMS), relative
        total_archive_bytes += len(data)
        assert total_archive_bytes <= LIMITS["all_archive_bytes"]
        selected, names, entries = [], set(), []
        with zipfile.ZipFile(io.BytesIO(data)) as zipped:
            infos = zipped.infolist()
            assert len(infos) <= LIMITS["entries_per_archive"]
            total_entries += len(infos)
            assert total_entries <= LIMITS["all_entries"]
            uncompressed = sum(info.file_size for info in infos)
            assert uncompressed <= LIMITS["archive_uncompressed_bytes"]
            total_uncompressed_bytes += uncompressed
            assert total_uncompressed_bytes <= LIMITS["all_uncompressed_bytes"]
            for info in infos:
                name = info.filename
                plain = name.rstrip("/")
                assert info.orig_filename == name and "\x00" not in name and "\\" not in name
                assert not PurePosixPath(plain).is_absolute() and ":" not in plain
                assert all(part not in ("", ".", "..") for part in plain.split("/"))
                assert len(name.encode("utf-8")) <= LIMITS["entry_name_utf8_bytes"]
                assert plain not in names and not (info.flag_bits & 1)
                names.add(plain)
                assert not stat.S_ISLNK(info.external_attr >> 16)
                assert info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                assert info.file_size <= LIMITS["entry_uncompressed_bytes"]
                assert info.file_size <= LIMITS["expansion_ratio"] * max(1, info.compress_size)
                row = {"path": name, "bytes": info.file_size, "compressed_bytes": info.compress_size,
                       "crc32": f"{info.CRC:08x}", "directory": info.is_dir()}
                entries.append(row)
            # Read only selected resources, public notices, manifest identifiers,
            # and source entries, with bounds checked before any decompression.
            for info in infos:
                name = info.filename
                notice_prefix = "META-INF/nativecmpkit/calf-io/"
                notice = name.startswith(notice_prefix) and not info.is_dir()
                skiko = name in browser_resources
                kotlin_source = relative.endswith("-sources.jar") and name.endswith(".kt")
                manifest = name == "default/manifest"
                reexports = name == "js-reexport-symbols.mjs"
                if not any((notice, skiko, kotlin_source, manifest, reexports)):
                    continue
                limit = LIMITS["entry_uncompressed_bytes"] if skiko else LIMITS["selected_text_bytes"]
                assert info.file_size <= limit
                with zipped.open(info, "r") as stream:
                    value = stream.read(limit + 1)
                    assert stream.read(1) == b""
                assert len(value) == info.file_size <= limit
                total_selected_bytes += len(value)
                assert total_selected_bytes <= LIMITS["all_uncompressed_bytes"]
                detail = {"path": name, "bytes": len(value), "sha256": digest(value)}
                if notice:
                    original = name.removeprefix(notice_prefix)
                    current = bounded_bytes(original, LIMITS["selected_text_bytes"])[0]
                    assert value == current
                    detail.update({"kind": "embedded_notice", "equals_repository_file": original})
                    compared_notice_files[original] = digest(current)
                elif skiko:
                    expected = browser_resources[name]
                    assert all(file["sha256"] == digest(value) and file["size"] == len(value)
                               for file in expected["files"].values())
                    detail.update({"kind": "skiko_resource", "matches_browser004_recorded_copies": list(expected["files"]),
                                   "runtime_reexecuted": False})
                elif kotlin_source:
                    source_set, suffix = name.split("/", 1)
                    original = f"calf-io/src/{source_set}/kotlin/{suffix}"
                    current = bounded_bytes(original, LIMITS["selected_text_bytes"])[0]
                    assert value == current and inputs[original] == digest(current)
                    detail.update({"kind": "kotlin_source", "equals_frozen_repository_file": original})
                    compared_source_files[original] = digest(current)
                elif manifest:
                    # Never print arbitrary compiler path/options from this file.
                    properties = dict(line.split("=", 1) for line in value.decode("utf-8").splitlines()
                                      if "=" in line and not line.startswith("#"))
                    keys = ("abi_version", "compiler_version", "metadata_version", "builtins_platform", "unique_name", "jsOutputName")
                    detail.update({"kind": "klib_manifest", "selected_identifiers": {k: properties[k] for k in keys if k in properties}})
                else:
                    detail["kind"] = "js_reexports_bytes_only_not_executed"
                selected.append(detail)
        entry_lists.append({"path": relative, "entries": entries})
        payloads.append({"publication": publication, "local_path": relative, "published_url": declaration["url"],
                         "bytes": len(data), "hashes": hashes, "all_declared_hashes_match": True,
                         "mtime_utc": dt.datetime.fromtimestamp(observed.st_mtime, dt.timezone.utc).isoformat(),
                         "entry_count": len(entries), "uncompressed_bytes": uncompressed,
                         "directories": sum(entry["directory"] for entry in entries),
                         "selected_entry_hashes": selected, "payload_archived": False})

assert len(payloads) == 8 and len(references) == 11
resources = [p for p in payloads if p["local_path"].endswith(".kotlin_resources.zip")]
assert len(resources) == 2 and all(p["bytes"] == 380 and p["entry_count"] == p["directories"] == 2 for p in resources)
assert resources[0]["hashes"] == resources[1]["hashes"]
for payload in payloads:
    value = bounded_bytes(payload["local_path"], LIMITS["archive_bytes"])[0]
    assert len(value) == payload["bytes"] and all(hashlib.new(k, value).hexdigest() == v for k, v in payload["hashes"].items())
assert all(digest(bounded_bytes(p)[0]) == h for p, h in inputs.items())
assert all(digest(bounded_bytes(p)[0]) == h for p, h in compared_notice_files.items())
notice_source = "convention-plugins/src/main/kotlin/PublicationNotices.kt"
notice_sha = digest(bounded_bytes(notice_source)[0])
assert notice_sha == inputs[notice_source]
receipt = {
    "schema_version": 1, "reviewer": "audit_build", "started_utc": started,
    "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "scope": "Bounded read-only metadata-to-current-local-archive inspection: Desktop from fresh002 metadata, JS/Wasm from fresh003 metadata. Not staging, package distribution, or consumer execution.",
    "reader_sha256": digest(Path(__file__).read_bytes()), "bounds": LIMITS,
    "source_revision": "94d2492e99d5cbc060409d94d9f88febd06222d5", "dirty_worktree": True,
    "source_input_count": 693, "selected_inputs_unchanged_before_after": True,
    "source_input_archive": input_path, "source_input_archive_sha256": digest(bounded_bytes(input_path)[0]),
    "metadata_archives": ARCHIVES, "metadata": module_rows, "references": references, "payloads": payloads,
    "archive_count": len(payloads), "metadata_file_reference_count": len(references),
    "all_declared_sizes_and_hashes_matched_before_after": True,
    "all_entries_name_type_count_size_ratio_bounds_passed": True,
    "unselected_entry_bytes_not_decompressed_or_executed": True,
    "archive_bytes_total": total_archive_bytes, "entry_count_total": total_entries,
    "uncompressed_bytes_total": total_uncompressed_bytes, "selected_bytes_read": total_selected_bytes,
    "source_jar_files_compared": compared_source_files, "notice_files_compared": compared_notice_files,
    "browser004_resource_readback": {"path": browser_path, "sha256": digest(browser_bytes), "comparison": "Current JS KLIB embedded bytes compared to recorded earlier browser004 size/SHA256; no browser rerun or mutable test-package read here."},
    "publication_notice_source": {"path": notice_source, "sha256": notice_sha,
                                  "lines": "23-62,95-97", "observation": "Source registers canonical/embedded notices and publicationNoticesZip, attaches embedded materials to Jar/AAR tasks and supplementary ZIP to Maven publications. The metadata task graphs did not execute publicationNoticesZip or a publish/staging task. This is not accompanying ZIP distribution proof."},
    "conclusions": [
        "All eight distinct local files (eleven variant references) match metadata sizes and every declared SHA512/SHA256/SHA1/MD5 before and after readback; no renamed/published copies were created.",
        "Both resource variants advertise kotlin-multiplatformresourcesjs and their runtime dependency sets. Each 380-byte local resource ZIP contains exactly two directory entries and zero payload bytes: composeResources/ plus the IO generated namespace directory. Equal resource hashes do not prove Skiko distribution.",
        "The 3,511,274-byte JS KLIB archive contains js-reexport-symbols.mjs and skiko.mjs/skiko.wasm/skikod8.mjs. The three Skiko bytes match earlier browser004 recorded sizes/hashes; the 45,677-byte Wasm KLIB contains no Skiko filenames. Its browser runtime used the separate previously observed official link-sync wiring, not this directory-only resource ZIP.",
        "Desktop JAR and both KLIB publication archives contain module-scoped embedded project notices and license/provenance files, byte-equal to current repository files. Source JARs and resource ZIPs do not contain that embedded notice subtree. No complete transitive-notice or legal clearance follows.",
        "Selected KLIB manifest identifiers, class/linkdata paths and source JAR paths retain com.mohamedrejeb.calf compatibility packages and calf local archive names. Published file URLs use nativecmpkit target identities; group/version/component links are preserved in the metadata inventory.",
        "All target module components reference nativecmpkit-io's root module. Root001 failed on45 uncached metadata artifacts; Android002 failed on lint-gradle32.4.0. Their modules remain unavailable in the final003 archive; no Android AAR or root payload was inspected. Browser-only generation cannot clear those gates."
    ],
    "limits": [
        "A held dirty-source consistency check, not immutable or independently trusted provenance. MD5/SHA1 are checked only as declared interoperability fields, not accepted as security evidence.",
        "Archive listings and selected bytes were read under explicit limits; unselected bytecode/IR was not decoded or executed, and no archive was extracted. Limits passed for these exact files, not all future archives.",
        "No source-bound pre-switch module/payload baseline, forced-fresh compilation, ABI/dependency-neutrality or isolated Maven/Gradle consumer verification.",
        "The supplementary notices ZIP is a source hook only in this observation. Its production/distribution and complete transitive/Skiko licensing obligations were not verified; copying current repository notices is not legal clearance.",
        "No task execution, native/device/browser test, dependency acquisition, network, Gradle/KGP/AGP execution, fixture005, policy/source/helper change, signing, staging or publication in this inspection."
    ],
    "full_kmp_metadata_gate_passed": False, "consumer_gate_passed": False, "release_readiness_certified": False,
}
output("entries.json", entry_lists)
output("receipt.json", receipt)
files = sorted(p for p in DEST.iterdir() if p.is_file())
with (DEST / "SHA256SUMS").open("x", encoding="utf-8") as stream:
    for path in files:
        stream.write(f"{digest(path.read_bytes())}  {path.name}\n")
print(json.dumps({"receipt": str((DEST / "receipt.json").relative_to(ROOT)),
                  "sha256": digest((DEST / "receipt.json").read_bytes()),
                  "archives": len(payloads), "references": len(references),
                  "archive_bytes": total_archive_bytes, "entries": total_entries,
                  "uncompressed_bytes": total_uncompressed_bytes, "selected_bytes_read": total_selected_bytes,
                  "notice_files": len(compared_notice_files), "unique_source_files": len(compared_source_files)}, indent=2))
