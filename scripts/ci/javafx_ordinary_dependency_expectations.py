# SPDX-License-Identifier: Apache-2.0
"""Pure pre-freeze expectation rendering; never acquire, approve or refresh trust.

Only a separately source-reviewed manifest digest can authorize these inputs.
Publisher/signature/source review and accepted local staging are external gates,
not JSON booleans or a hash recomputed from the dependencies being admitted.
No network, Gradle, subprocess, filesystem write or public publication exists.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re
import xml.etree.ElementTree as ET

MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_ARTIFACTS = 4096
NS = "https://schema.gradle.org/dependency-verification"
SOURCE_RECIPE_AUTHORITY = "a27e4de4f217af01269d41d9bd45938b25fe0036afbfa04489f2d910782faf3f"
LIBRARY_GROUP = "io.github.apdelrahman1911.nativecmpkit"
LIBRARY_VERSION = "0.1.0-preview.1"
LIBRARY_MODULES = ("nativecmpkit-webview", "nativecmpkit-webview-desktop")
PRIVATE_GROUP = "nativecmpkit.private.javafx"
PRIVATE_MODULE = "javafx-web-win"
PRIVATE_VERSION = "21.0.13-nativecmpkit-cancel1-local"
MODES = ("module", "pom")
CLASSPATHS = ("compileClasspath", "runtimeClasspath", "testCompileClasspath", "testRuntimeClasspath")
COMPANIONS = ("base", "graphics", "controls", "media", "swing")
PRODUCER_SCOPES = ("settings", "buildscript", "included-convention", "selected-producer-task")
CONSUMER_SCOPES = ("plugins", "compiler", "metadata", *CLASSPATHS)
METADATA_PATHS = {"producer": "gradle/verification-metadata.xml",
                  "consumer": "tests/consumer/javafx-ordinary-webview/gradle/verification-metadata.xml"}
EXTERNAL_ORIGINS = ("https://repo.maven.apache.org/maven2/",
                    "https://dl.google.com/dl/android/maven2/", "https://plugins.gradle.org/m2/")
EXTERNAL_BASES = ("publisher-signature", "independent-publisher-digest", "reproducible-source-build")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,255}\Z")


class ExpectationError(ValueError):
    """Bounded fixed diagnostic; never include manifest/dependency payloads."""


def need(value, message):
    if not value:
        raise ExpectationError(message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sha256(value):
    return type(value) is str and DIGEST.fullmatch(value) is not None


def token(value):
    return type(value) is str and TOKEN.fullmatch(value) is not None and value not in (".", "..")


def path_parts(value):
    need(type(value) is str and 0 < len(value) <= 4096 and "\\" not in value and ":" not in value,
         "Exact nontraversing staged Maven identity required")
    parts = PurePosixPath(value).parts
    need(parts and not value.startswith("/") and "/".join(parts) == value and all(token(part) for part in parts),
         "Exact relative staged Maven identity required")
    return parts


def endpoint(value):
    need(type(value) is dict and set(value) == {"bytes", "sha256"} and
         type(value["bytes"]) is int and 0 < value["bytes"] <= 256 * 1024 * 1024 and sha256(value["sha256"]),
         "Reviewed exact artifact digest and byte length required")
    return value


def _stage_identity(kind, path):
    parts = path_parts(path)
    group, modules, version = ((LIBRARY_GROUP, LIBRARY_MODULES, LIBRARY_VERSION) if kind == "library" else
                               (PRIVATE_GROUP, (PRIVATE_MODULE,), PRIVATE_VERSION))
    prefix = tuple(group.split("."))
    need(parts[:len(prefix)] == prefix and len(parts) == len(prefix) + 3 and
         parts[-3] in modules and parts[-2] == version and
         parts[-1].startswith(parts[-3] + "-" + version) and
         parts[-1].endswith((".jar", ".pom", ".module", ".klib", ".aar")),
         "Only exact reviewed primary local package identities required")
    return parts[-3], parts[-1]


def _coverage(value):
    need(type(value) is dict and set(value) == {"producer", "consumer"}, "Both independent invocation closures required")
    producer, consumer = value["producer"], value["consumer"]
    need(type(producer) is dict and set(producer) == set(PRODUCER_SCOPES) and all(sha256(v) for v in producer.values()),
         "Settings buildscript composite and selected-producer closure evidence required")
    need(type(consumer) is dict and set(consumer) == set(MODES), "Separate module and POM closure evidence required")
    for mode in MODES:
        need(type(consumer[mode]) is dict and set(consumer[mode]) == set(CONSUMER_SCOPES) and
             all(sha256(v) for v in consumer[mode].values()),
             "Plugins compiler descriptors and all four mode-specific classpath closure evidence required")


def _artifact(row, staging):
    need(type(row) is dict and set(row) == {"root", "group", "module", "version", "name", "bytes", "sha256", "contexts", "provenance"},
         "Exact finite expectation artifact schema required")
    need(type(row["root"]) is str and row["root"] in METADATA_PATHS and all(token(row[k]) for k in ("group", "module", "version", "name")) and
         not row["version"].endswith("-SNAPSHOT") and not row["version"].lower().startswith("latest."),
         "Exact nonchanging component and artifact identities required")
    endpoint({"bytes": row["bytes"], "sha256": row["sha256"]})
    contexts = row["contexts"]
    allowed = set(PRODUCER_SCOPES) if row["root"] == "producer" else {f"{m}:{s}" for m in MODES for s in CONSUMER_SCOPES}
    need(type(contexts) is list and contexts and all(type(v) is str for v in contexts) and
         contexts == sorted(set(contexts)) and set(contexts) <= allowed, "Exact separately named artifact usage contexts required")
    provenance = row["provenance"]
    need(type(provenance) is dict and provenance.get("kind") in ("external", "local-library", "local-private") and
         sha256(provenance.get("evidence_sha256")), "Separately reviewed provenance evidence identity required")
    if provenance["kind"] == "external":
        need(set(provenance) == {"kind", "url", "basis", "evidence_sha256"} and provenance["basis"] in EXTERNAL_BASES,
             "Registry sidecars self-observed digests and blanket TOFU cannot authorize expectations")
        relative = f'{row["group"].replace(".", "/")}/{row["module"]}/{row["version"]}/{row["name"]}'
        need(provenance["url"] in tuple(origin + relative for origin in EXTERNAL_ORIGINS) and
             row["group"] not in (LIBRARY_GROUP, PRIVATE_GROUP), "Exact reviewed official artifact origin required")
    else:
        need(set(provenance) == {"kind", "path", "evidence_sha256"} and row["root"] == "consumer",
             "Local exports are not producer dependencies or blanket group exceptions")
        kind = "library" if provenance["kind"] == "local-library" else "private"
        module, staged_name = _stage_identity(kind, provenance["path"])
        need(row["group"] == (LIBRARY_GROUP if kind == "library" else PRIVATE_GROUP) and row["module"] == module and
             row["version"] == (LIBRARY_VERSION if kind == "library" else PRIVATE_VERSION), "Exact local component identity required")
        alias = (kind == "library" and module == "nativecmpkit-webview-desktop" and
                 staged_name == f"nativecmpkit-webview-desktop-{LIBRARY_VERSION}.jar" and
                 row["name"] == f"calf-webview-desktop-{LIBRARY_VERSION}.jar")
        need(row["name"] == staged_name or alias, "Only the reviewed byte-identical desktop JAR metadata alias is allowed")
        need(not alias or all(v.startswith("module:") for v in contexts), "The metadata alias cannot replace a POM artifact identity")
        need(staging[kind].get(provenance["path"]) == {"bytes": row["bytes"], "sha256": row["sha256"]},
             "Local expectations must match separately accepted staging payload identities")
    need(not (row["root"] == "consumer" and row["group"] == "org.openjfx" and row["module"] == "javafx-web"),
         "Original official web cannot replace or accompany the cured consumer provider")
    return row["root"], row["group"], row["module"], row["version"], row["name"]


def _consumer_matrix(rows):
    consumer = [row for row in rows if row["root"] == "consumer"]
    for mode in MODES:
        for name in CLASSPATHS:
            selected = [row for row in consumer if f"{mode}:{name}" in row["contexts"]]
            libraries = [row for row in selected if row["provenance"]["kind"] == "local-library" and
                         row["module"] == "nativecmpkit-webview-desktop" and row["name"] in
                         (f"nativecmpkit-webview-desktop-{LIBRARY_VERSION}.jar", f"calf-webview-desktop-{LIBRARY_VERSION}.jar")]
            cured = [row for row in selected if row["provenance"]["kind"] == "local-private" and
                     row["name"] == f"{PRIVATE_MODULE}-{PRIVATE_VERSION}.jar"]
            companions = [row["module"] for row in selected if row["group"] == "org.openjfx" and row["version"] == "21.0.13" and
                          row["name"] == f'{row["module"]}-21.0.13-win.jar']
            need(len(libraries) == len(cured) == 1 and sorted(companions) == sorted("javafx-" + c for c in COMPANIONS),
                 "Every actual module and POM classpath requires exactly one library one cured web and five aligned Windows companions")
    required = {(LIBRARY_GROUP, m, LIBRARY_VERSION, f"{m}-{LIBRARY_VERSION}.module", "module:metadata") for m in LIBRARY_MODULES}
    required |= {(PRIVATE_GROUP, PRIVATE_MODULE, PRIVATE_VERSION, f"{PRIVATE_MODULE}-{PRIVATE_VERSION}.module", "module:metadata"),
                 (LIBRARY_GROUP, "nativecmpkit-webview-desktop", LIBRARY_VERSION,
                  f"nativecmpkit-webview-desktop-{LIBRARY_VERSION}.pom", "pom:metadata"),
                 (PRIVATE_GROUP, PRIVATE_MODULE, PRIVATE_VERSION, f"{PRIVATE_MODULE}-{PRIVATE_VERSION}.pom", "pom:metadata")}
    observed = {(row["group"], row["module"], row["version"], row["name"], context) for row in consumer for context in row["contexts"]}
    need(required <= observed, "Both actual local POM and module descriptor modes require exact explicit expectations")


def parse_reviewed_manifest(payload, reviewed_sha256):
    """Expected digest must be separately source-adopted, never supplied by the data itself."""
    need(sha256(reviewed_sha256) and type(payload) is bytes and 0 < len(payload) <= MAX_MANIFEST_BYTES and
         digest(payload) == reviewed_sha256, "Separately reviewed exact manifest digest required; unapproved metadata stays blocked")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "Duplicate expectation manifest field refused")
            result[key] = value
        return result
    try:
        document = json.loads(payload, object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ExpectationError("Nonfinite expectation manifest refused")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ExpectationError("One complete bounded expectation JSON required") from None
    need(type(document) is dict and set(document) == {"schema_version", "source_recipe_authority_sha256", "review_basis_sha256", "coverage", "staging_inputs", "artifacts"} and
         type(document["schema_version"]) is int and document["schema_version"] == 1 and
         document["source_recipe_authority_sha256"] == SOURCE_RECIPE_AUTHORITY and sha256(document["review_basis_sha256"]),
         "Exact source-recipe and independently reviewed expectation schema required")
    _coverage(document["coverage"])
    staging = document["staging_inputs"]
    need(type(staging) is dict and set(staging) == {"library", "private"}, "Two separately accepted local staging maps required")
    for kind in ("library", "private"):
        need(type(staging[kind]) is dict and 0 < len(staging[kind]) <= 1024, "Bounded explicit local primary staging map required")
        for path, value in staging[kind].items():
            _stage_identity(kind, path)
            endpoint(value)
    private_stem = f'{PRIVATE_GROUP.replace(".", "/")}/{PRIVATE_MODULE}/{PRIVATE_VERSION}/{PRIVATE_MODULE}-{PRIVATE_VERSION}'
    need(set(staging["private"]) == {private_stem + suffix for suffix in (".jar", "-sources.jar", ".pom", ".module")},
         "Exact four-file private production staging expectation required")
    rows = document["artifacts"]
    need(type(rows) is list and 0 < len(rows) <= MAX_ARTIFACTS, "Bounded complete explicit dependency expectation rows required")
    identities = [_artifact(row, staging) for row in rows]
    need(len(identities) == len(set(identities)) and identities == sorted(identities) and
         {row["root"] for row in rows} == set(METADATA_PATHS), "Distinct sorted rows for both invocation roots required")
    _consumer_matrix(rows)
    return document


def metadata_payloads(payload, reviewed_sha256):
    """Revalidate immutable approved bytes; no mutable parsed dictionary can approve XML."""
    document = parse_reviewed_manifest(payload, reviewed_sha256)
    result = {}
    for invocation, path in METADATA_PATHS.items():
        root = ET.Element("verification-metadata", {"xmlns": NS})
        configuration = ET.SubElement(root, "configuration")
        ET.SubElement(configuration, "verify-metadata").text = "true"
        # Cryptographic/publisher/source review precedes manifest adoption.
        # This renderer does not invent keys or turn checksums into signer proof.
        ET.SubElement(configuration, "verify-signatures").text = "false"
        components = ET.SubElement(root, "components")
        selected = [row for row in document["artifacts"] if row["root"] == invocation]
        by_component = {}
        for row in selected:
            by_component.setdefault((row["group"], row["module"], row["version"]), []).append(row)
        for (group, module, version), artifacts in sorted(by_component.items()):
            component = ET.SubElement(components, "component", {"group": group, "name": module, "version": version})
            for row in sorted(artifacts, key=lambda item: item["name"]):
                artifact = ET.SubElement(component, "artifact", {"name": row["name"]})
                ET.SubElement(artifact, "sha256", {"value": row["sha256"]})
        result[path] = ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
    return result


def _primary_library_inventory(actual):
    """Do not compare timestamped registry listings as reproducible package bytes.

    Existing full staging before/after maps still hold EVERY physical file.
    No checksum sidecar/listing is admitted as a Gradle-resolved dependency or
    used to approve a digest. Exact fixed-version primary artifacts all compare.
    """
    result = {}
    prefix = tuple(LIBRARY_GROUP.split("."))
    for path, value in actual.items():
        parts = path_parts(path)
        endpoint(value)
        administrative = (parts[:len(prefix)] == prefix and len(parts) == len(prefix) + 2 and parts[-2] in LIBRARY_MODULES and
                          re.fullmatch(r"maven-metadata\.xml(?:\.(?:md5|sha1|sha256|sha512))?", parts[-1]) is not None)
        if administrative:
            continue
        if parts[-1].endswith((".md5", ".sha1", ".sha256", ".sha512")):
            parent_path = path.rsplit(".", 1)[0]
            _stage_identity("library", parent_path)
            need(parent_path in actual, "Checksum sidecar without its exact held primary artifact refused")
            continue
        _stage_identity("library", path)
        result[path] = value
    return result


def compare_staging(payload, reviewed_sha256, library, private):
    """Revalidate PRIOR approved bytes, never a mutated dictionary or current digest."""
    document = parse_reviewed_manifest(payload, reviewed_sha256)
    need(type(library) is dict and type(private) is dict and 0 < len(library) <= 1024 and len(private) == 4,
         "Actual bounded library and private staging maps required")
    primary = _primary_library_inventory(library)
    for path, value in private.items():
        _stage_identity("private", path)
        endpoint(value)
    need(primary == document["staging_inputs"]["library"] and private == document["staging_inputs"]["private"],
         "Rebuilt local bytes differ from independently accepted expectations; preserve failure and never refresh checksums")
    return {"primary_library_files": len(primary), "private_files": len(private), "staging_expectations_held": True,
            "all_physical_files_still_require_existing_before_after_custody": True,
            "independent_trust_certified": False, "graph_completeness_certified": False,
            "publication_ready": False}
