#!/usr/bin/env python3
"""Bind ordinary PRIVATE Maven resolution observations to actual cured web bytes.

No Gradle/native execution or publication. A verified graph is not a public Stop
or full-source/security/consumer/release result. CLI requires production class
pins; explicitly marked small synthetic tests use the private model entry point.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

import stage_private_web as stage

CLASSPATHS = ("compileClasspath", "runtimeClasspath", "testCompileClasspath", "testRuntimeClasspath")


def _verify(stage_report, resolution, repository, *, model_classes=None, model_companion_pins=None):
    production = model_classes is None
    stage.need(not production or model_companion_pins is None, "Synthetic companion pins forbidden in production verification")
    stage.need(isinstance(stage_report, dict) and isinstance(resolution, dict), "Staging/resolution JSON objects required")
    stage.need(stage_report.get("schema_version") == 1 and stage_report.get("kind") == "private-ordinary-Maven-cured-web" and
               stage_report.get("passed") is True and stage_report.get("held_inputs") is True and
               stage_report.get("production_contract") is production and stage_report.get("publication_ready") is False and
               stage_report.get("full_native_corresponding_source_complete") is False,
               "Actual private staging boundary required")
    target = stage_report.get("classifier")
    stage.need(target in stage.CLASSIFIERS, "Unsupported resolution classifier")
    module = "javafx-web-" + target
    stem = module + "-" + stage.VERSION
    stage.need((stage_report.get("group"), stage_report.get("module"), stage_report.get("version")) ==
               (stage.GROUP, module, stage.VERSION), "Wrong private Maven staging identity")
    expected_companions = [f"org.openjfx:javafx-{name}:{stage.UPSTREAM}:{target}" for name in stage.COMPANIONS]
    stage.need(stage_report.get("official_companion_dependencies") == expected_companions and
               stage_report.get("web_dependency") == f"{stage.GROUP}:{module}:{stage.VERSION}",
               "Exactly five aligned official modules plus cured web required")
    repository = Path(repository)
    stage.need(repository.is_absolute() and repository.is_dir() and not repository.is_symlink(), "Actual private repository required")
    directory = stage.GROUP.replace(".", "/") + "/" + module + "/" + stage.VERSION + "/"
    expected_files = {directory + stem + suffix for suffix in (".jar", "-sources.jar", ".pom", ".module")}
    files = stage_report.get("files")
    stage.need(isinstance(files, list) and len(files) == 4 and
               {row.get("file") for row in files if isinstance(row, dict)} == expected_files,
               "Exact staged Maven payload/metadata inventory required")
    staged = {}
    for row in files:
        name = row["file"]
        stage.need(not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts,
                   "Unsafe staged metadata path")
        payload = stage.regular(repository / name)
        stage.need(type(row.get("bytes")) is int and row["bytes"] == len(payload) and row.get("sha256") == stage.digest(payload),
                   "Actual staged metadata/payload differs")
        staged[name] = payload
    jar = staged[directory + stem + ".jar"]
    _, _, expected_pom, expected_module = stage.metadata(target, jar)
    stage.need(staged[directory + stem + ".pom"] == expected_pom and staged[directory + stem + ".module"] == expected_module,
               "Private POM/module self-dependency or metadata substitution refused")
    members = stage.archive(jar)
    classes = model_classes if not production else {stage.PREFIX + name: sha for name, sha in stage.builder.CLASS_SHA256.items()}
    stage.need({name: stage.digest(members.get(name, b"")) for name in classes} == classes and
               members.get("META-INF/MANIFEST.MF") == stage.builder.CANDIDATE_MANIFEST,
               "Cured owning class/private manifest pins differ")
    stage.need(stage_report.get("public_module_native_payload_sha256") ==
               {name: stage.digest(members[name]) for name in (stage.WEB_ENGINE, "module-info.class", stage.NATIVE[target])},
               "Public/module/native provenance differs")
    # Bind the observed staged bytes to the actual candidate, not a forged success
    # JSON. Production independently rechecks original/class/source/legal pins.
    candidate_root = stage_report.get("candidate_root")
    stage.need(isinstance(candidate_root, str), "Actual candidate origin required")
    if production:
        contract = stage.production_contract()
        candidate = stage.inspect_candidate(Path(candidate_root), contract)
        stage.need(candidate["classifier"] == target, "Candidate origin classifier differs")
        candidate_files = {str(path): sha for path, sha in candidate["watched"].items()}
        candidate_jar, candidate_sources = candidate["jar"][1], candidate["sources"][1]
        expected_companion_pins = contract.companion_pins[target]
        companion_pin_inputs = contract.companion_pin_inputs
    else:
        # Tiny explicitly synthetic controls cannot enter the production CLI.
        candidate_files = {}
        candidate_jar = stage.regular(Path(candidate_root) / f"javafx-web-{stage.VERSION}-{target}.jar")
        candidate_sources = stage.regular(Path(candidate_root) / f"javafx-web-{stage.VERSION}-java-sources.jar")
        # Fixed synthetic expectations exercise the NEW owning pin comparison.
        # Historical no-pin helpers remain explicitly SYNTHETIC and cannot enter
        # verify_private_resolution()/CLI or claim official companion identity.
        expected_companion_pins = model_companion_pins
        companion_pin_inputs = {}
    stage.need(jar == candidate_jar and staged[directory + stem + "-sources.jar"] == candidate_sources,
               "Actual candidate/staged runtime or Java-source bytes differ")
    stage.need(resolution.get("schema_version") == 1 and resolution.get("classifier") == target and
               resolution.get("metadata_mode") in ("module", "pom") and
               type(resolution.get("java_major")) is int and resolution["java_major"] == 17 and
               all(resolution.get(key) is False for key in ("project_substitution", "runtime_init_scripts",
                   "private_route_override", "runtime_module_patch")), "Ordinary explicit-host/JDK17 resolution observations required")
    rows = resolution.get("resolved_artifacts")
    stage.need(isinstance(rows, list) and 0 < len(rows) <= 4096, "Bounded actual Maven resolution rows required")
    providers = {name: [] for name in CLASSPATHS}
    companions = {name: set() for name in CLASSPATHS}
    cured = {name: 0 for name in CLASSPATHS}
    identities, inspected = set(), {}
    for row in rows:
        stage.need(isinstance(row, dict) and row.get("configuration") in CLASSPATHS and
                   row.get("component_kind") == "module" and
                   all(isinstance(row.get(key), str) and row[key] for key in ("group", "module", "version", "file", "path", "sha256")),
                   "Project/loose/invalid resolution row refused")
        configuration = row["configuration"]
        identity = tuple(row[key] for key in ("configuration", "group", "module", "version", "file"))
        stage.need(identity not in identities, "Duplicate resolved artifact row")
        identities.add(identity)
        path = Path(row["path"])
        stage.need(row["file"] == path.name and row["file"] == PurePosixPath(row["file"]).name,
                   "Resolved file label/path differs")
        if str(path) not in inspected:
            payload = stage.regular(path)
            web = []
            if path.suffix == ".jar":
                try:
                    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                        names = archive.namelist()
                        stage.need(len(names) <= 65536 and len(set(names)) == len(names), "Duplicate/unbounded consumer JAR entries")
                        web = [name for name in names if name == stage.WEB_ENGINE or
                               name.endswith("/" + stage.WEB_ENGINE) or
                               PurePosixPath(name).name.lower() in set(stage.NATIVE.values())]
                except zipfile.BadZipFile:
                    raise stage.StageError("Invalid resolved consumer JAR") from None
            inspected[str(path)] = (len(payload), stage.digest(payload), web)
        size, sha, web = inspected[str(path)]
        stage.need(type(row.get("bytes")) is int and row["bytes"] == size and row["sha256"] == sha,
                   "Actual resolved artifact bytes differ from observations")
        if web:
            providers[configuration].append(path)
        stage.need(row["group"] != "com.mohamedrejeb.calf", "Original Calf/source fallback refused")
        if row["group"] == "org.openjfx":
            stage.need(row["module"] in {"javafx-" + name for name in stage.COMPANIONS} and row["version"] == stage.UPSTREAM,
                       "Original web/mixed or unknown official JavaFX dependency refused")
            generic = row["module"] + "-" + stage.UPSTREAM + ".jar"
            classified = row["module"] + "-" + stage.UPSTREAM + "-" + target + ".jar"
            stage.need(row["file"] in (generic, classified) and not web, "Foreign classifier or companion web provider refused")
            if production or expected_companion_pins is not None:
                pin = expected_companion_pins.get(row["file"]) if isinstance(expected_companion_pins, dict) else None
                stage.need(isinstance(pin, dict) and pin.get("file") == row["file"] and
                           type(pin.get("bytes")) is int and 0 < pin["bytes"] <= stage.MAX_FILE and
                           isinstance(pin.get("sha256"), str) and re.fullmatch("[0-9a-f]{64}", pin["sha256"]) is not None,
                           "Trusted official companion pin missing or malformed")
                stage.need((size, sha) == (pin["bytes"], pin["sha256"]),
                           "Trusted official companion byte pin differs")
            if row["file"] == classified:
                companions[configuration].add(row["module"][7:])
        if row["group"] == stage.GROUP:
            stage.need((row["module"], row["version"], row["file"]) == (module, stage.VERSION, stem + ".jar") and
                       sha == stage.digest(jar) and size == len(jar) and
                       set(web) == {stage.WEB_ENGINE, stage.NATIVE[target]}, "Cured Maven identity/provenance/provider differs")
            cured[configuration] += 1
    stage.need(all(cured[name] == 1 and companions[name] == set(stage.COMPANIONS) and
                   len(providers[name]) == 1 for name in CLASSPATHS),
               "Every classpath requires exactly one cured web and five explicit companion classifiers")
    for path, (size, sha, _) in inspected.items():
        payload = stage.regular(Path(path))
        stage.need((len(payload), stage.digest(payload)) == (size, sha), "Resolved input changed during verification")
    stage.need(all(stage.regular(repository / name) == payload for name, payload in staged.items()),
               "Staged metadata/payload changed during resolution verification")
    stage.need(stage.regular(Path(candidate_root) / f"javafx-web-{stage.VERSION}-{target}.jar") == candidate_jar and
               stage.regular(Path(candidate_root) / f"javafx-web-{stage.VERSION}-java-sources.jar") == candidate_sources and
               all(stage.digest(stage.regular(Path(path))) == sha for path, sha in candidate_files.items()),
               "Actual candidate/original inputs changed during resolution verification")
    stage.need(all(stage.digest(stage.regular(Path(path))) == sha for path, sha in companion_pin_inputs.items()),
               "Trusted official companion pin inputs changed during verification")
    return {"schema_version": 1, "passed": True, "classifier": target, "metadata_mode": resolution["metadata_mode"],
            "classpath_count": 4, "resolved_rows": len(rows), "production_pins_required": production,
            "ordinary_resolution_bytes_bound": production, "native_executions": 0, "publication_ready": False,
            "official_companion_pins_bound": production,
            "synthetic_companion_pin_checks": not production and expected_companion_pins is not None,
            "scope": "Observed normal-Maven bytes/provider binding only; no Gradle/native/full-source/security/release execution" if production
                     else "SYNTHETIC resolution regression model only; no genuine ordinary consumer acceptance"}


def verify_private_resolution(stage_report, resolution, repository):
    return _verify(stage_report, resolution, repository)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--resolution", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify_private_resolution(stage.document(stage.regular(args.repository / "private-javafx-staging.json")),
                                          stage.document(stage.regular(args.resolution)), args.repository)
    except (stage.StageError, OSError, KeyError, TypeError):
        parser.exit(1, "Private JavaFX ordinary-resolution verification refused; preserve evidence.\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
