#!/usr/bin/env python3
"""Stage the pinned cured web JAR through ordinary PRIVATE Maven metadata.

No download/compiler/native command, shared-cache mutation or publication exists
in this tool. Production CLI admits only an actual generated candidate and fixed
original inputs. Complete native corresponding-source/security/consumer gates
remain unsatisfied. Private per-classifier modules avoid wildcard/self-depending
upstream POMs and preserve the original JAR bytes and JPMS descriptor.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import difflib
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
import xml.etree.ElementTree as ET

import build_runtime_candidate as builder
import probe_runner as probe

HERE = Path(__file__).resolve().parent
GROUP = "nativecmpkit.private.javafx"
VERSION = builder.IDENTITY
UPSTREAM = "21.0.13"
COMPANIONS = ("base", "graphics", "controls", "media", "swing")
CLASSIFIERS = ("linux", "linux-aarch64", "mac", "mac-aarch64", "win")
DEFAULT_BASE = HERE.parents[2] / "build" / "ci-verification" / "private-javafx-maven"
PREFIX = builder.CLASS_PREFIX
WEB_ENGINE = "javafx/scene/web/WebEngine.class"
NATIVE = {"linux": "libjfxwebkit.so", "linux-aarch64": "libjfxwebkit.so",
          "mac": "libjfxwebkit.dylib", "mac-aarch64": "libjfxwebkit.dylib", "win": "jfxwebkit.dll"}
OWNERS = ("build_runtime_candidate.py", "probe_runner.py", "artifacts.json",
          "cancel-response-future.patch", "NOTICE.md", *builder.LEGAL)
MAX_FILE = 64 * 1024 * 1024
MATERIAL_REQUIREMENTS = (
    "Exact retained native payload to upstream source/build identity and build dependencies",
    "Complete preferred corresponding source, interface definitions and build/install/generator scripts",
    "Actual contained third-party source/license/notice/exception obligations",
    "Applicable GPLv2 section3 distribution/source-access or qualifying offer mechanism",
    "Independent provenance/security and ordinary consumer/API-ABI/platform verification",
)
OFFICIAL_ORIGINAL_PINS_SHA256 = "246eb9bef73b24f2df53058f65344ff5ca81ba2b199d958f43997035c0cdf760"
OFFICIAL_COMPANION_SUPPLEMENT_SHA256 = "a2cce99c5ad3a3628c9a042b454bc1e8b3f61eb308b392d78c5534687682e9d2"
OFFICIAL_ORIGIN = "https://repo.maven.apache.org/maven2/org/openjfx/"


class StageError(ValueError):
    """Fixed bounded contract message, never raw private file contents."""


def need(condition, message):
    if not condition:
        raise StageError(message)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def regular(path, limit=MAX_FILE):
    path = Path(path)
    need(path.is_absolute() and ".." not in path.parts, "Absolute nontraversing input required")
    for parent in (path, *path.parents):
        need(not parent.is_symlink(), "Input symlink refused")
    before = path.stat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= limit,
         "Bounded unshared regular input required")
    with path.open("rb") as stream:
        payload = stream.read(limit + 1)
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) and
         len(payload) == before.st_size, "Input changed while reading")
    return payload


def document(payload):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "Duplicate JSON key refused")
            result[key] = value
        return result

    def finite(_):
        raise StageError("Nonfinite JSON refused")

    try:
        return json.loads(payload, object_pairs_hook=unique, parse_constant=finite)
    except (UnicodeError, json.JSONDecodeError):
        raise StageError("Malformed bounded JSON refused") from None


@dataclass(frozen=True)
class ArtifactContract:
    """Production pins, or explicitly labelled synthetic parser-test contract."""
    owners: dict
    originals: dict
    classes: dict
    legal: dict
    modified_source: object
    web_members: int = 548
    source_members: int = 312
    production: bool = True
    # NEW resolution-only pins do not rewrite the candidate's original14 input
    # inventory. Existing no-pin synthetic helpers remain SYNTHETIC, not proof.
    companion_pins: object = None
    companion_pin_inputs: object = None


def companion_pin(row, filename):
    need(isinstance(row, dict) and row.get("file") == filename and
         type(row.get("bytes")) is int and 0 < row["bytes"] <= MAX_FILE and
         isinstance(row.get("sha256"), str) and re.fullmatch("[0-9a-f]{64}", row["sha256"]) is not None,
         "Trusted official companion pin missing or malformed")
    module = filename.split("-" + UPSTREAM, 1)[0]
    need(row.get("url") == OFFICIAL_ORIGIN + module + "/" + UPSTREAM + "/" + filename,
         "Trusted official companion origin differs")
    return {"file": filename, "bytes": row["bytes"], "sha256": row["sha256"], "url": row["url"]}


def trusted_companion_inventory(originals, supplement):
    """Trusted owning documents only; resolution/staging JSON supplies no pins."""
    need(isinstance(supplement, dict) and supplement.get("schema_version") == 1 and
         supplement.get("version") == UPSTREAM and supplement.get("official_origin") == OFFICIAL_ORIGIN and
         supplement.get("original_artifacts_sha256") == OFFICIAL_ORIGINAL_PINS_SHA256 and
         supplement.get("same_registry_checksum_is_independent_security_certification") is False,
         "Trusted official companion supplement boundary differs")
    swing, generic = supplement.get("classified_swing"), supplement.get("generic")
    need(isinstance(swing, dict) and set(swing) == set(CLASSIFIERS) and
         isinstance(generic, dict) and set(generic) == set(COMPANIONS),
         "Trusted official companion pin missing or malformed")
    result = {}
    for target in CLASSIFIERS:
        rows = originals.get(target) if isinstance(originals, dict) else None
        need(isinstance(rows, list) and all(isinstance(row, dict) for row in rows),
             "Trusted official companion pin missing or malformed")
        values = {}
        for module in COMPANIONS:
            filename = f"javafx-{module}-{UPSTREAM}-{target}.jar"
            matched = [row for row in rows if row.get("file") == filename]
            if module == "swing":
                need(not matched, "Trusted classified companion pins duplicated")
                pin = swing[target]
            else:
                need(len(matched) == 1, "Trusted official companion pin missing or malformed")
                pin = matched[0]
            values[filename] = companion_pin(pin, filename)
            generic_filename = f"javafx-{module}-{UPSTREAM}.jar"
            values[generic_filename] = companion_pin(generic[module], generic_filename)
        result[target] = values
    return result


def production_contract():
    original_bytes = regular(builder.HERE / "artifacts.json", 128 * 1024)
    need(digest(original_bytes) == OFFICIAL_ORIGINAL_PINS_SHA256, "Trusted official original pin document differs")
    pins = document(original_bytes)
    need(pins["version"] == UPSTREAM and pins["schema_version"] == 1 and
         set(pins["platforms"]) == set(CLASSIFIERS), "Fixed official platform pin inventory changed")
    owners = {name: digest(regular(builder.HERE / name)) for name in OWNERS}
    originals = {target: [pins["sources"], *pins["platforms"][target]] for target in CLASSIFIERS}
    supplemental_bytes = regular(HERE / "official-companion-supplement.json", 128 * 1024)
    need(digest(supplemental_bytes) == OFFICIAL_COMPANION_SUPPLEMENT_SHA256,
         "Trusted official companion supplement document differs")
    companions = trusted_companion_inventory(originals, document(supplemental_bytes))
    return ArtifactContract(owners, originals,
                            {PREFIX + name: sha for name, sha in builder.CLASS_SHA256.items()},
                            dict(builder.LEGAL), builder.modified_source,
                            companion_pins=companions,
                            companion_pin_inputs={str(builder.HERE / "artifacts.json"): digest(original_bytes),
                                                  str(HERE / "official-companion-supplement.json"): digest(supplemental_bytes)})


def archive(payload):
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as jar:
            entries = jar.infolist()
            need(0 < len(entries) <= 4096 and len({e.filename for e in entries}) == len(entries),
                 "Duplicate or unbounded archive inventory")
            total = 0
            for entry in entries:
                name = PurePosixPath(entry.filename)
                need(not name.is_absolute() and ".." not in name.parts and
                     not any(c in entry.filename for c in ("\\", ":", "\0")), "Unsafe archive path")
                mode = entry.external_attr >> 16
                need(not stat.S_ISLNK(mode) and not entry.flag_bits & 1 and
                     entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) and
                     0 <= entry.file_size <= 128 * 1024 * 1024, "Unsafe archive type/size")
                need(not (entry.filename.upper().startswith("META-INF/") and
                          entry.filename.upper().endswith((".SF", ".RSA", ".DSA", ".EC"))),
                     "Signed archive refused without signature stripping")
                total += entry.file_size
            need(total <= 192 * 1024 * 1024, "Expanded archive limit exceeded")
            return {entry.filename: jar.read(entry) for entry in entries}
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
        raise StageError("Invalid or unsupported archive") from None


def additions(original_source, changed_source, owner_payloads):
    result = {"META-INF/nativecmpkit/" + name: owner_payloads[name] for name in builder.LEGAL}
    result["META-INF/nativecmpkit/NOTICE.md"] = owner_payloads["NOTICE.md"]
    result["META-INF/nativecmpkit/CANDIDATE.txt"] = (
        "Private NativeCmpKit JavaFX HTTP2Loader cancellation candidate. NOT PUBLISHED.\n"
        "GPLv2 with Classpath exception retained for the changed source and classes.\n"
        "Only Java corresponding sources are included; full upstream/native source,\n"
        "security, platform consumers, API/ABI and redistribution gates remain.\n").encode()
    result["META-INF/nativecmpkit/cancel-response-future-with-notice.patch"] = "".join(
        difflib.unified_diff(original_source.decode().splitlines(keepends=True),
                             changed_source.decode().splitlines(keepends=True),
                             fromfile="a/" + probe.SOURCE_ENTRY, tofile="b/" + probe.SOURCE_ENTRY)).encode()
    return result


def check_review(review, original, changed, replacements, extra):
    retained = {name: digest(payload) for name, payload in original.items() if name not in replacements}
    differences = sorted(name for name in original if original[name] != changed[name])
    need(type(review["original_members"]) is int and review["original_members"] == len(original) and
         type(review["retained_payload_members"]) is int and review["retained_payload_members"] == len(retained) and
         review["retained_payload_sha256"] == retained and
         review["changed_payload_members"] == differences and
         review["added_members"] == sorted(extra) and review["all_other_payloads_identical"] is True,
         "Actual archive payloads disagree with producer review")


def inspect_candidate(root, contract):
    root = Path(root)
    need(root.is_absolute() and root.is_dir() and not root.is_symlink(), "Actual absolute candidate directory required")
    watched = {}

    def read(path, limit=MAX_FILE):
        payload = regular(path, limit)
        watched[str(path)] = digest(payload)
        return payload

    result = document(read(root / "candidate.json", 128 * 1024))
    need(isinstance(result, dict), "Candidate JSON object required")
    target = result.get("classifier")
    need(target in CLASSIFIERS and result.get("identity") == VERSION and result.get("schema_version") == 1,
         "Only the fixed private candidate identity/classifier is allowed")
    need(result.get("passed") is True and result.get("held_inputs") is True and
         result.get("default_dependencies_changed") is False and result.get("cached_JARs_modified") is False and
         result.get("full_native_corresponding_source_complete") is False and
         type(result.get("native_executions")) is int and result["native_executions"] == 0 and
         type(result.get("library_tests")) is int and result["library_tests"] == 0,
         "Candidate must retain private incomplete-source packaging-only boundaries")
    before = document(read(root / "inputs-before.json", 128 * 1024))
    after = document(read(root / "inputs-after.json", 128 * 1024))
    need(isinstance(before, dict) and before == after, "Candidate input maps are not held")
    original_pins = contract.originals[target]
    expected = contract.owners | {row["file"]: row["sha256"] for row in original_pins}
    need(len(before) == len(expected) and all(isinstance(name, str) for name in before) and
         {Path(name).name for name in before} == set(expected),
         "Exact original/owning input inventory required")
    original_payloads, owner_payloads = {}, {}
    for name, sha in before.items():
        need(isinstance(name, str) and isinstance(sha, str) and re.fullmatch("[0-9a-f]{64}", sha) is not None and
             expected[Path(name).name] == sha, "Original/owning pin differs")
        payload = read(Path(name))
        need(digest(payload) == sha, "Actual original/owning input differs from held pin")
        (owner_payloads if Path(name).name in contract.owners else original_payloads)[Path(name).name] = payload
    for pin in original_pins:
        need(len(original_payloads[pin["file"]]) == pin["bytes"], "Official input size differs from pin")
    for name, sha in contract.legal.items():
        need(digest(owner_payloads[name]) == sha, "Preserved GPL/exception/legal bytes differ")

    jar_name = f"javafx-web-{VERSION}-{target}.jar"
    source_name = f"javafx-web-{VERSION}-java-sources.jar"
    need(result.get("jar_file") == jar_name and result.get("java_sources_file") == source_name,
         "Fixed generated artifact filenames required")
    jar_bytes, source_bytes = read(root / jar_name), read(root / source_name)
    need(result.get("jar_sha256") == digest(jar_bytes) and result.get("java_sources_sha256") == digest(source_bytes),
         "Actual candidate artifact digest differs")
    original_web = archive(original_payloads[f"javafx-web-{UPSTREAM}-{target}.jar"])
    original_sources = archive(original_payloads[f"javafx-web-{UPSTREAM}-sources.jar"])
    web, sources = archive(jar_bytes), archive(source_bytes)
    need(len(original_web) == contract.web_members and len(original_sources) == contract.source_members,
         "Pinned original member counts differ")
    changed_source = contract.modified_source(original_sources[probe.SOURCE_ENTRY])
    need(read(root / "source" / "HTTP2Loader.java", 128 * 1024) == changed_source and
         result.get("modified_source_sha256") == digest(changed_source), "Actual modified Java source differs")
    extra = additions(original_sources[probe.SOURCE_ENTRY], changed_source, owner_payloads)
    need(set(web) == set(original_web) | set(extra) and set(sources) == set(original_sources) | set(extra) and
         not set(extra) & (set(original_web) | set(original_sources)), "Candidate inventory adds/removes unknown providers")
    need(result.get("modified_class_sha256") == contract.classes and
         {name: digest(web[name]) for name in contract.classes} == contract.classes,
         "Actual owning class payloads differ from accepted pins")
    need(web["META-INF/MANIFEST.MF"] == builder.CANDIDATE_MANIFEST,
         "Private publication-ready=false manifest changed")
    replacements = set(contract.classes) | {"META-INF/MANIFEST.MF"}
    need(all(web[name] == payload for name, payload in original_web.items() if name not in replacements) and
         all(sources[name] == payload for name, payload in original_sources.items() if name != probe.SOURCE_ENTRY) and
         sources[probe.SOURCE_ENTRY] == changed_source and
         all(web[name] == payload and sources[name] == payload for name, payload in extra.items()),
         "Unrelated public/native/JPMS/source/legal payload changed")
    need(sorted(name for name in original_web if original_web[name] != web[name]) ==
         sorted((PREFIX + "HTTP2Loader.class", "META-INF/MANIFEST.MF")) and
         all(web[name] == original_web[name] for name in contract.classes if name != PREFIX + "HTTP2Loader.class"),
         "Only owning loader and manifest may change")
    need(WEB_ENGINE in web and "module-info.class" in web and
         [name for name in web if name.lower().endswith((".dll", ".so", ".dylib", ".jnilib"))] == [NATIVE[target]],
         "Exactly one preserved native web and public/module provider required")
    check_review(document(read(root / "jar-member-review.json", 2 * 1024 * 1024)),
                 original_web, web, replacements, extra)
    check_review(document(read(root / "java-source-member-review.json", 2 * 1024 * 1024)),
                 original_sources, sources, {probe.SOURCE_ENTRY}, extra)
    need(result.get("original_web_sha256") == digest(original_payloads[f"javafx-web-{UPSTREAM}-{target}.jar"]) and
         result.get("original_java_sources_sha256") == digest(original_payloads[f"javafx-web-{UPSTREAM}-sources.jar"]),
         "Original dependency provenance disagrees")
    return {"root": root, "classifier": target, "jar": (root / jar_name, jar_bytes),
            "sources": (root / source_name, source_bytes), "watched": watched,
            "production_contract": contract.production,
            "public_module_native_payload_sha256": {name: digest(web[name]) for name in (WEB_ENGINE, "module-info.class", NATIVE[target])}}


def metadata(classifier, jar_bytes):
    need(classifier in CLASSIFIERS, "Unsupported private runtime classifier")
    module = "javafx-web-" + classifier
    stem = module + "-" + VERSION
    project = ET.Element("project", {"xmlns": "http://maven.apache.org/POM/4.0.0"})
    for tag, value in (("modelVersion", "4.0.0"), ("groupId", GROUP), ("artifactId", module),
                       ("version", VERSION), ("packaging", "jar"),
                       ("name", "NativeCmpKit PRIVATE unpublished cured JavaFX web"),
                       ("description", "Private verification only; Java sources are not complete native corresponding source. NOT PUBLISHED.")):
        ET.SubElement(project, tag).text = value
    license = ET.SubElement(ET.SubElement(project, "licenses"), "license")
    ET.SubElement(license, "name").text = "GPLv2 with Classpath exception; retained upstream/third-party obligations"
    properties = ET.SubElement(project, "properties")
    for tag, value in (("nativecmpkit.private", "true"), ("nativecmpkit.publication-ready", "false"),
                       ("nativecmpkit.native-corresponding-source-complete", "false")):
        ET.SubElement(properties, tag).text = value
    pom = ET.tostring(project, encoding="utf-8", xml_declaration=True) + b"\n"
    attributes = {"org.gradle.category": "library", "org.gradle.libraryelements": "jar",
                  "org.gradle.dependency.bundling": "external", "org.gradle.jvm.version": 17}
    variants = [{"name": name, "attributes": attributes | {"org.gradle.usage": usage},
                 "files": [{"name": stem + ".jar", "url": stem + ".jar", "size": len(jar_bytes), "sha256": digest(jar_bytes)}]}
                for name, usage in (("javaApi", "java-api"), ("javaRuntime", "java-runtime"))]
    module_metadata = {"formatVersion": "1.1", "component": {"group": GROUP, "module": module, "version": VERSION}, "variants": variants}
    return module, stem, pom, (json.dumps(module_metadata, indent=2, sort_keys=True) + "\n").encode()


def new_file(path, payload):
    for parent in path.parents:
        need(not parent.is_symlink(), "Output parent symlink refused")
    with path.open("xb") as output:
        output.write(payload)


def stage_validated(validated, repository, allowed_base):
    repository, allowed_base = Path(repository), Path(allowed_base)
    need(repository.is_absolute() and allowed_base.is_absolute() and ".." not in repository.parts and
         repository.parent == allowed_base,
         "Repository must be a new confined private verification child")
    for parent in (repository, *repository.parents):
        need(not parent.is_symlink(), "Repository symlink refused")
    need(not repository.exists() and allowed_base.is_dir() and not allowed_base.is_symlink(),
         "Fresh private repository required; preserve prior outputs")
    need(not repository.is_relative_to(validated["root"]) and not validated["root"].is_relative_to(repository),
         "Repository must not overlap candidate inputs")
    module, stem, pom, module_bytes = metadata(validated["classifier"], validated["jar"][1])
    repository.mkdir(mode=0o700, parents=False)
    report = {"schema_version": 1, "kind": "private-ordinary-Maven-cured-web", "passed": False,
              "candidate_root": str(validated["root"]),
              "group": GROUP, "module": module, "version": VERSION, "classifier": validated["classifier"],
              "web_dependency": GROUP + ":" + module + ":" + VERSION,
              "official_companion_dependencies": [f"org.openjfx:javafx-{name}:{UPSTREAM}:{validated['classifier']}" for name in COMPANIONS],
              "production_contract": validated["production_contract"], "publication_ready": False,
              "validation_scope": "pinned-production-artifacts" if validated["production_contract"] else "SYNTHETIC regression model only",
              "full_native_corresponding_source_complete": False, "java_sources_only": True,
              "unresolved_corresponding_source_and_distribution_requirements": list(MATERIAL_REQUIREMENTS),
              "native_executions": 0, "consumer_resolution_verified": False, "security_or_API_ABI_clearance": False,
              "public_module_native_payload_sha256": validated["public_module_native_payload_sha256"],
              "scope": "Unpublished private normal-Maven staging only; not ordinary consumer/native/release acceptance"}
    try:
        directory = repository / GROUP.replace(".", "/") / module / VERSION
        directory.mkdir(parents=True, mode=0o700)
        payloads = {stem + ".jar": validated["jar"][1], stem + "-sources.jar": validated["sources"][1],
                    stem + ".pom": pom, stem + ".module": module_bytes}
        files = []
        for name, payload in payloads.items():
            path = directory / name
            new_file(path, payload)
            need(regular(path) == payload, "Actual staged artifact differs")
            files.append({"file": path.relative_to(repository).as_posix(), "bytes": len(payload), "sha256": digest(payload)})
        need(all(digest(regular(Path(path))) == sha for path, sha in validated["watched"].items()),
             "Candidate/original inputs changed during staging")
        report.update(passed=True, held_inputs=True, files=files)
    except (StageError, OSError):
        report["error"] = "Private staging failed; preserve outputs and do not consume"
        raise
    finally:
        new_file(repository / "private-javafx-staging.json", (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    return report


def stage_private_web(candidate_root, repository):
    validated = inspect_candidate(candidate_root, production_contract())
    need(validated["production_contract"] is True, "Production CLI cannot accept a synthetic contract")
    return stage_validated(validated, repository, DEFAULT_BASE)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path,
                        help="Fresh child of build/ci-verification/private-javafx-maven (parent created explicitly)")
    args = parser.parse_args(argv)
    try:
        result = stage_private_web(args.candidate_root, args.repository)
    except (StageError, OSError, KeyError, TypeError, UnicodeError):
        parser.exit(1, "Private JavaFX staging refused; preserve inputs/outputs and review the fixed contract.\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
