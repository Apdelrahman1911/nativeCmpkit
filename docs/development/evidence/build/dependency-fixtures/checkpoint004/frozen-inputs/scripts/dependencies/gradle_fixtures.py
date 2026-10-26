"""Scheduled REAL Gradle fixtures, never called by the offline unittest suite.

Every case has a fresh cache and only a task-owned, deterministic local Maven
repository. Failure classification requires the actual Gradle error, not merely
nonzero exit. No production/shared caches, locks or repositories are modified.
"""
from __future__ import annotations

import io
from pathlib import Path
import re
import subprocess
import time
import zipfile

import integrity_model as m
import integrity as driver

GROUP = "org.nativecmpkit.fixture"
GROUP_DIRECTORY = GROUP.replace(".", "/")
BASE_BUILD = '''repositories { maven { url = uri("repo") } }
configurations {
    fixtureClasspath {
        canBeResolved = true
        canBeConsumed = false
    }
}
dependencies { add("fixtureClasspath", "org.nativecmpkit.fixture:parent:1.0") }
'''
CASES = (
    "baseline-check", "wrong-jar-sha", "wrong-pom-sha", "missing-hash", "missing-host-lock",
    "missing-configuration-lock", "transitive-strict-drift", "dynamic-transitive-frozen",
    "added-dependency", "removed-dependency",
)
CONTEXT_CASES = ("included-root-check", "standalone-wrong-hash")
ALL_CASES = CASES + CONTEXT_CASES
CONFLICTING_CONSTRAINTS = "org.gradle.internal.component.resolution.failure.exception.ConflictingConstraintsException"
MODULE_VERSION_FAILURE = "org.gradle.internal.resolve.ModuleVersionResolveException"
CONSTRAINT_MESSAGE = "Component is the target of multiple version constraints with conflicting requirements:"
MISSING_LOCK_STATE = "org.gradle.internal.locking.MissingLockStateException"
LOCK_OUT_OF_DATE = "org.gradle.internal.locking.LockOutOfDateException"
LOCK_CASE_BUILDS = {
    "missing-host-lock": BASE_BUILD,
    "missing-configuration-lock": BASE_BUILD + '''configurations {
    newUnrecordedClasspath { canBeResolved = true; canBeConsumed = false }
}
dependencies { add("newUnrecordedClasspath", "org.nativecmpkit.fixture:extra:1.0") }
''',
    "added-dependency": BASE_BUILD + 'dependencies { add("fixtureClasspath", "org.nativecmpkit.fixture:extra:1.0") }\n',
    "removed-dependency": BASE_BUILD + 'configurations.fixtureClasspath.exclude(group: "org.nativecmpkit.fixture", module: "leaf")\n',
}


def selected_cases(cases: list[str] | None) -> tuple[str, ...]:
    """An explicitly selected negative still requires a known-good check first."""
    if cases is None:
        return ALL_CASES
    m.require(isinstance(cases, list) and cases and all(isinstance(case, str) for case in cases),
              "At least one exact fixture case name is required")
    m.require(len(cases) == len(set(cases)) and set(cases) <= set(ALL_CASES),
              "Unknown or duplicate fixture case; see scripts/dependencies/README.md")
    return ("baseline-check",) + tuple(case for case in ALL_CASES if case != "baseline-check" and case in cases)


def jar_bytes(module: str, version: str) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        info = zipfile.ZipInfo("fixture.txt", date_time=(2000, 1, 1, 0, 0, 0))
        info.external_attr = 0o100644 << 16
        archive.writestr(info, f"Harmless deterministic fixture: {module}:{version}\n")
    return output.getvalue()


def pom_bytes(module: str, version: str) -> bytes:
    dependency = ""
    if module == "parent":
        dependency = ("<dependencies><dependency><groupId>" + GROUP + "</groupId><artifactId>leaf</artifactId>"
                      "<version>[1.0,2.0)</version></dependency></dependencies>")
    return (f'<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>'
            f"<groupId>{GROUP}</groupId><artifactId>{module}</artifactId><version>{version}</version>"
            f"{dependency}</project>\n").encode()


def artifact_files(module: str, version: str) -> dict[str, bytes]:
    prefix = f"repo/{GROUP_DIRECTORY}/{module}/{version}/{module}-{version}"
    return {prefix + ".jar": jar_bytes(module, version), prefix + ".pom": pom_bytes(module, version)}


def known_metadata() -> dict[m.ArtifactKey, str]:
    result = {}
    for module, version in (("parent", "1.0"), ("leaf", "1.0"), ("leaf", "1.1"), ("extra", "1.0")):
        for name, data in artifact_files(module, version).items():
            result[(GROUP, module, version, Path(name).name)] = m.sha256_bytes(data)
    return result


def version_metadata(versions: list[str]) -> bytes:
    return (f"<metadata><groupId>{GROUP}</groupId><artifactId>leaf</artifactId><versioning>"
            f"<latest>{versions[-1]}</latest><release>{versions[-1]}</release><versions>" +
            "".join(f"<version>{value}</version>" for value in versions) +
            "</versions><lastUpdated>20000101000000</lastUpdated></versioning></metadata>\n").encode()


def put(root: Path, name: str, data: bytes) -> None:
    target = m.confined(root, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    m.require(not target.exists(), "Fixture creation must not overwrite existing files")
    target.write_bytes(data)


def add_future_leaf(root: Path) -> None:
    for name, data in artifact_files("leaf", "1.1").items():
        put(root, name, data)
    m.confined(root, f"repo/{GROUP_DIRECTORY}/leaf/maven-metadata.xml", must_exist=True).write_bytes(version_metadata(["1.0", "1.1"]))


def write_marker(root: Path, *, included: bool = False) -> dict:
    files, integrity, topology, _ = driver.selected_inputs(root, "controlled-fixture")
    projects = {".": {":": "."}}
    if included:
        projects["included"] = {":": "included"}
    marker = {"schema_version": 1, "kind": "controlled-fixture", "created_utc": driver.utc_now(),
              "host": m.host_key(), "source_revision": None, "source_tree_dirty": None,
              "source_files": files, "source_directories": topology, "source_input_digest": driver.source_digest(files, topology),
              "initial_integrity_files": integrity, "build_roots": sorted(projects), "expected_projects": projects,
              "independent_trust_reviewed": False,
              "provenance": "Task-generated deterministic bytes, not acquisition/trust evidence for the real project"}
    m.write_new(root / driver.MARKER, m.json_bytes(marker))
    return marker


def create(root: Path, *, case: str = "baseline-check", base_state: Path | None = None,
           included: bool = False, wrong_included_hash: bool = False) -> dict:
    driver._new_workspace_path(root)
    root.mkdir(parents=True)
    for source in driver.TOOL_DIRECTORY.iterdir():
        if source.is_file() and source.suffix in {".py", ".gradle", ".md"}:
            put(root, "scripts/dependencies/" + source.name, source.read_bytes())
    settings = 'rootProject.name = "nativecmpkit-dependency-fixture"\n'
    if included:
        settings += 'includeBuild("included")\n'
    put(root, "settings.gradle", settings.encode())
    put(root, "build.gradle", BASE_BUILD.encode())
    for module, version in (("parent", "1.0"), ("leaf", "1.0"), ("extra", "1.0")):
        for name, data in artifact_files(module, version).items():
            put(root, name, data)
    put(root, f"repo/{GROUP_DIRECTORY}/leaf/maven-metadata.xml", version_metadata(["1.0"]))
    trust = known_metadata()
    if case == "missing-hash":
        del trust[(GROUP, "leaf", "1.0", "leaf-1.0.jar")]
    put(root, "gradle/verification-metadata.xml", m.metadata_bytes(trust))
    if base_state:
        _, state, _, _ = driver.selected_inputs(base_state, "controlled-fixture")
        for name in state:
            if name.endswith(".lockfile"):
                put(root, name, m.read_regular(m.confined(base_state, name, must_exist=True), m.MAX_LOCK))
    build = root / "build.gradle"
    if case == "wrong-jar-sha":
        path = root / f"repo/{GROUP_DIRECTORY}/leaf/1.0/leaf-1.0.jar"
        path.write_bytes(path.read_bytes() + b"intentional controlled tamper\n")
    elif case == "wrong-pom-sha":
        path = root / f"repo/{GROUP_DIRECTORY}/parent/1.0/parent-1.0.pom"
        path.write_bytes(path.read_bytes() + b"<!-- intentional controlled metadata tamper -->\n")
    elif case == "missing-host-lock":
        lock = root / m.lock_path(".", m.host_key())
        m.require(lock.is_file(), "A real baseline lock must exist before the missing-state fixture")
        lock.unlink()
    elif case in LOCK_CASE_BUILDS:
        build.write_text(LOCK_CASE_BUILDS[case])
    elif case == "transitive-strict-drift":
        add_future_leaf(root)
        build.write_text(BASE_BUILD + '''dependencies {
    constraints {
        add("fixtureClasspath", "org.nativecmpkit.fixture:leaf:1.1") {
            version { strictly("1.1") }
        }
    }
}
''')
    elif case == "dynamic-transitive-frozen":
        add_future_leaf(root)
    elif case not in {"baseline-check", "missing-hash"}:
        raise m.IntegrityError("Unknown controlled fixture case")
    if included:
        put(root, "included/settings.gradle", b'rootProject.name = "nativecmpkit-fixture-included"\n')
        put(root, "included/build.gradle", b'''repositories { maven { url = uri("../repo") } }
configurations { fixtureClasspath { canBeResolved = true; canBeConsumed = false } }
dependencies { add("fixtureClasspath", "org.nativecmpkit.fixture:extra:1.0") }
''')
        child_trust = dict(trust)
        if wrong_included_hash:
            child_trust[(GROUP, "extra", "1.0", "extra-1.0.jar")] = "0" * 64
        put(root, "included/gradle/verification-metadata.xml", m.metadata_bytes(child_trust))
    return write_marker(root, included=included)


def controlled_review(root: Path, marker: dict, entry_root: str = ".") -> None:
    state = driver.check_source(root, marker)
    review = {"schema_version": 1, "record_type": "candidate-review", "entry_root": entry_root,
              "host": marker["host"], "source_input_digest": marker["source_input_digest"],
              "integrity_files": state, "trust_level": "controlled-fixture", "independent_trust_reviewed": False,
              "recorded_utc": driver.utc_now(),
              "review_note": "Intentionally selected deterministic/tampered fixture state; not real-project trust acceptance"}
    m.write_new(m.confined(root, driver._review_path(entry_root)), m.json_bytes(review))


def failure_evidence(root: Path, run_id: str) -> dict:
    marker = driver.load_workspace(root)
    m.require(marker["kind"] == "controlled-fixture", "Negative classification is restricted to controlled fixtures")
    types: set[str] = set()
    messages: list[str] = []
    diagnostics = []
    owners = []
    count = 0
    graph_root = root / f"build/dependency-integrity/{run_id}/graphs"
    if graph_root.exists():
        for part in sorted(graph_root.glob("*/parts/*.json")):
            record = m.read_json(part)
            m.require(record.get("run_id") == run_id and record.get("gradle_version") == m.GRADLE_VERSION and
                      record.get("java_major") == 17 and record.get("mode") == "check" and
                      record.get("source_input_digest") == marker["source_input_digest"] and record.get("host") == marker["host"],
                      "Failure did not reach the exact fixture Gradle/JVM/input identity")
            count += 1
            owners.append(record)
            for configuration in record.get("configurations", []):
                diagnostics.append({"build_root": record.get("build_root"), "project_path": record.get("project_path"),
                                    **{key: configuration.get(key) for key in ("scope", "name", "status", "root_component_id", "unresolved", "failures",
                                                                             "components", "edges", "artifacts", "inventory", "lock_coverage")}})
                errors = list(configuration.get("failures", []))
                errors += [value.get("failure", {}) for value in configuration.get("unresolved", [])]
                for error in errors:
                    types.update(error.get("types", []))
                    messages.extend(error.get("fixture_messages", []))
    log = root / f"build/dependency-integrity/{run_id}/gradle.log"
    if log.is_file():
        messages.append(m.read_regular(log, 16 * 1024 * 1024).decode("utf-8", errors="replace"))
    # Gradle's HTML report contains the exact expected/actual hashes. Keep it local;
    # the final fixture receipt exports only specifically matched known values.
    for base in (root / "build", root / "included/build"):
        if not base.is_dir():
            continue
        for report in base.glob("reports/dependency-verification/**/*.html"):
            messages.append(m.read_regular(report, 16 * 1024 * 1024).decode("utf-8", errors="replace"))
    return {"owner_receipts": count, "failure_types": sorted(types), "text": "\n".join(messages),
            "_marker": marker, "_integrity_files": driver.check_source(root, marker),
            "_configuration_diagnostics": diagnostics, "_owner_diagnostics": owners}


def transitive_constraint_evidence(root: Path, marker: dict, diagnostics: list[dict]) -> dict | None:
    """Match the exact controlled transitive/locked/strict conflict, never generic failure text."""
    candidates = [item for item in diagnostics if item.get("build_root") == "." and item.get("project_path") == ":" and
                  item.get("scope") == "project" and item.get("name") == "fixtureClasspath"]
    if len(candidates) != 1:
        return None
    target = candidates[0]
    if target.get("status") != "failed" or target.get("root_component_id") != "project::":
        return None
    if any(item is not target and (item.get("failures") or item.get("unresolved") or
                                   item.get("status") not in {"resolved", "empty-resolved", "non-resolvable"}) for item in diagnostics):
        return None
    required = {(f"module:{GROUP}:parent:1.0", f"{GROUP}:leaf:[1.0,2.0)", False),
                ("project::", f"{GROUP}:leaf:{{strictly 1.0}}", True),
                ("project::", f"{GROUP}:leaf:{{strictly 1.1}}", True)}

    def conflict(error: dict) -> bool:
        if not {CONFLICTING_CONSTRAINTS, MODULE_VERSION_FAILURE} <= set(error.get("types", [])):
            return False
        for message in error.get("fixture_messages", []):
            lines = message.splitlines()
            if len(lines) == 3 and lines[0] == CONSTRAINT_MESSAGE and set(lines[1:]) == {"1.0 - from lock file", "1.1"}:
                return True
        return False

    unresolved = target.get("unresolved", [])
    if len(unresolved) != len(required):
        return None
    observed = set()
    for edge in unresolved:
        if type(edge.get("constraint")) is not bool or not conflict(edge.get("failure", {})):
            return None
        observed.add((edge.get("from"), edge.get("requested"), edge["constraint"]))
    if observed != required:
        return None
    requests = {value[1] for value in required}
    for error in target.get("failures", []):
        if error.get("phase") != "artifact-resolution" or not conflict(error) or not any(
            message.splitlines() and message.splitlines()[0] in {f"Could not resolve {value}." for value in requests}
            for message in error.get("fixture_messages", [])
        ):
            return None
    lock = m.parse_lock(m.read_regular(root / m.lock_path(".", marker["host"]), m.MAX_LOCK))
    expected_modules = {(GROUP, "parent", "1.0"), (GROUP, "leaf", "1.0")}
    if lock.get("fixtureClasspath") != expected_modules:
        return None
    trust = m.parse_metadata(m.read_regular(root / "gradle/verification-metadata.xml", m.MAX_XML))
    known = known_metadata()
    expected_keys = [(GROUP, "leaf", version, f"leaf-{version}.{extension}")
                     for version in ("1.0", "1.1") for extension in ("jar", "pom")]
    if any(trust.get(key) != known[key] or m.file_sha256(root / f"repo/{GROUP_DIRECTORY}/leaf/{key[2]}/{key[3]}") != known[key]
           for key in expected_keys):
        return None
    return {"build_root": ".", "project_path": ":", "configuration": "fixtureClasspath",
            "component": f"{GROUP}:leaf", "locked_version": "1.0", "strict_requested_version": "1.1",
            "matched_exception_type": CONFLICTING_CONSTRAINTS, "matched_lock_message": "1.0 - from lock file",
            "matched_unresolved_edges": [{"from": source, "requested": requested, "constraint": constraint}
                                          for source, requested, constraint in sorted(required)],
            "exact_configuration_lock_confirmed": True, "known_leaf_artifact_and_metadata_hashes_confirmed": len(expected_keys)}


def _exact_lock_error(error: dict, exception: str, message: str, configuration: str, module: str | None) -> bool:
    """Match paired cause types/messages, never a phrase in a log or unrelated cause.

    Templates come from read-only Gradle9.7.1 class inspection. Until a scheduled
    fixture exercises them, the accepted producer shapes are runtime-unverified.
    Unknown wrappers, messages or additional causes deliberately fail closed.
    """
    types, messages = error.get("types"), error.get("fixture_messages")
    if (not isinstance(types, list) or not isinstance(messages, list) or not 1 <= len(types) <= 3 or
            len(types) != len(messages) or len(types) != len(set(types)) or
            types[-1] != exception or messages[-1] != message):
        return False
    wrappers = {
        "org.gradle.api.artifacts.ResolveException": {
            f"Could not resolve all dependencies for configuration ':{configuration}'.",
        },
        "org.gradle.api.internal.artifacts.ivyservice.DefaultLenientConfiguration$ArtifactResolveException": {
            f"Could not resolve all files for configuration ':{configuration}'.",
            f"Could not resolve all artifacts for configuration ':{configuration}'.",
        },
    }
    if module is not None:
        wrappers[MODULE_VERSION_FAILURE] = {f"Could not resolve {module}."}
    return all(value in wrappers.get(kind, set()) for kind, value in zip(types[:-1], messages[:-1]))


def _fixture_selected_modules(configuration: dict) -> set[tuple[str, str, str]] | None:
    components = configuration.get("components")
    if not isinstance(components, list) or configuration.get("root_component_id") != "project::":
        return None
    roots = [item for item in components if item.get("kind") == "project"]
    if len(roots) != 1 or roots[0].get("id") != "project::" or roots[0].get("project_path") != ":":
        return None
    modules = set()
    for item in components:
        if item in roots:
            continue
        coordinate = (item.get("group"), item.get("module"), item.get("version"))
        if (item.get("kind") != "module" or coordinate in modules or any(not isinstance(value, str) for value in coordinate) or
                item.get("id") != "module:" + ":".join(coordinate)):
            return None
        modules.add(coordinate)
    return modules


def exact_lock_case_evidence(root: Path, case: str, marker: dict, diagnostics: list[dict], owners: list[dict]) -> dict | None:
    """Four exact controlled missing/stale-lock cases; no generic lock rejection.

    This matcher is intentionally narrower than all possible Gradle diagnostics.
    Positive synthetic parser coverage is not an actual Gradle fixture result.
    """
    if case not in LOCK_CASE_BUILDS or marker.get("build_roots") != ["."] or marker.get("expected_projects") != {".": {":": "."}}:
        return None
    lock_name = m.lock_path(".", marker["host"])
    if len(owners) != 1:
        return None
    owner = owners[0]
    policy = owner.get("policy", {})
    if (owner.get("record_type") != "project-graph" or owner.get("build_root") != "." or owner.get("project_path") != ":" or
            owner.get("project_directory") != "." or owner.get("complete") is not False or
            owner.get("failures") != [] or owner.get("inventory_drift") != [] or
            policy.get("project_lock_mode") != "STRICT" or policy.get("lock_file") != lock_name or
            policy.get("ignored_dependencies") != [] or policy.get("dependency_verification_mode") != "strict"):
        return None
    configuration = "newUnrecordedClasspath" if case == "missing-configuration-lock" else "fixtureClasspath"
    expected_configurations = {("buildscript", "classpath"), ("project", "fixtureClasspath")}
    if case == "missing-configuration-lock":
        expected_configurations.add(("project", configuration))
    if (len(diagnostics) != len(expected_configurations) or
            {(item.get("scope"), item.get("name")) for item in diagnostics} != expected_configurations or
            any(item.get("build_root") != "." or item.get("project_path") != ":" for item in diagnostics)):
        return None
    inventory = owner.get("inventory", [])
    if (len(inventory) != len(expected_configurations) or
            {(item.get("scope"), item.get("name")) for item in inventory} != expected_configurations or
            any(item.get("can_resolve") is not True for item in inventory)):
        return None
    target = next(item for item in diagnostics if (item.get("scope"), item.get("name")) == ("project", configuration))
    if target.get("status") != "failed" or target.get("lock_coverage") != "strict-project-init-script":
        return None
    if any(item is not target and (item.get("failures") != [] or item.get("unresolved") != [] or
                                   item.get("status") not in {"resolved", "empty-resolved"}) for item in diagnostics):
        return None
    # Check exact current bytes as well as recorded input identity. These cases
    # cannot use missing/corrupt metadata or an altered fixture as lock evidence.
    repository = {name: data for module in ("parent", "leaf", "extra") for name, data in artifact_files(module, "1.0").items()}
    repository[f"repo/{GROUP_DIRECTORY}/leaf/maven-metadata.xml"] = version_metadata(["1.0"])
    if {name for name in marker.get("source_files", {}) if name.startswith("repo/")} != set(repository):
        return None
    baseline_modules = {(GROUP, "parent", "1.0"), (GROUP, "leaf", "1.0")}
    try:
        if (m.read_regular(root / "build.gradle", 64 * 1024) != LOCK_CASE_BUILDS[case].encode() or
                m.read_regular(root / "settings.gradle", 64 * 1024) != b'rootProject.name = "nativecmpkit-dependency-fixture"\n' or
                any(m.read_regular(root / name, 64 * 1024) != data for name, data in repository.items()) or
                m.parse_metadata(m.read_regular(root / "gradle/verification-metadata.xml", m.MAX_XML)) != known_metadata()):
            return None
        lock_file = m.confined(root, lock_name)
        if case == "missing-host-lock":
            if lock_file.exists():
                return None
        elif m.parse_lock(m.read_regular(lock_file, m.MAX_LOCK)) != {"fixtureClasspath": baseline_modules}:
            return None
    except (m.IntegrityError, OSError):
        return None
    if case.startswith("missing-"):
        exception = MISSING_LOCK_STATE
        message = f"Locking strict mode: Configuration ':{configuration}' is locked but does not have lock state."
        # Missing lock state is raised before a graph root/artifact result exists.
        # A different producer shape stays unverified until separately inspected.
        if (target.get("root_component_id") is not None or any(target.get(name) != [] for name in ("components", "edges", "artifacts", "unresolved")) or
                len(target.get("failures", [])) != 1 or target["failures"][0].get("phase") != "configuration-resolution" or
                not _exact_lock_error(target["failures"][0], exception, message, configuration, None)):
            return None
        if case == "missing-configuration-lock":
            baseline = next(item for item in diagnostics if (item.get("scope"), item.get("name")) == ("project", "fixtureClasspath"))
            if baseline.get("status") != "resolved" or _fixture_selected_modules(baseline) != baseline_modules:
                return None
        discrepancy = "absent-actual-host-lock-file" if case == "missing-host-lock" else "absent-exact-configuration-entry"
    else:
        exception = LOCK_OUT_OF_DATE
        module = f"{GROUP}:extra:1.0" if case == "added-dependency" else f"{GROUP}:leaf:1.0"
        message = (f"Resolved '{module}' which is not part of the dependency lock state" if case == "added-dependency" else
                   f"Did not resolve '{module}' which is part of the dependency lock state")
        expected_selected = baseline_modules | {(GROUP, "extra", "1.0")} if case == "added-dependency" else {(GROUP, "parent", "1.0")}
        if _fixture_selected_modules(target) != expected_selected:
            return None
        required_direct = {("project::", f"{GROUP}:parent:1.0", False, f"module:{GROUP}:parent:1.0")}
        if case == "added-dependency":
            required_direct |= {("project::", module, False, "module:" + module),
                                (f"module:{GROUP}:parent:1.0", f"{GROUP}:leaf:[1.0,2.0)", False, f"module:{GROUP}:leaf:1.0")}
        allowed_constraints = {("project::", f"{group}:{name}:{{strictly {version}}}", True, f"module:{group}:{name}:{version}")
                               for group, name, version in baseline_modules & expected_selected}
        edges = target.get("edges", [])
        if any(type(edge.get("constraint")) is not bool for edge in edges):
            return None
        observed_edges = {(edge.get("from"), edge.get("requested"), edge.get("constraint"), edge.get("selected")) for edge in edges}
        if len(observed_edges) != len(edges) or not required_direct <= observed_edges <= required_direct | allowed_constraints:
            return None
        failures = target.get("failures", [])
        unresolved = target.get("unresolved", [])
        if not failures or len(failures) > 2 or len(unresolved) > 1:
            return None
        if any(error.get("phase") != "artifact-resolution" or
               not _exact_lock_error(error, exception, message, configuration, module) for error in failures):
            return None
        if any(edge.get("from") != "project::" or edge.get("requested") != module or type(edge.get("constraint")) is not bool or
               edge.get("failure", {}).get("phase") != "dependency-resolution" or
               not _exact_lock_error(edge["failure"], exception, message, configuration, module) for edge in unresolved):
            return None
        discrepancy = "extra-resolved-module" if case == "added-dependency" else "locked-module-not-resolved"
    return {"build_root": ".", "project_path": ":", "configuration": configuration, "actual_host_lock": lock_name,
            "matched_exception_type": exception, "matched_message": message, "lock_discrepancy": discrepancy,
            "exact_fixture_state_confirmed": True, "known_repository_files_confirmed": len(repository),
            "unrelated_owner_configuration_or_artifact_failure": False}


def classify(root: Path, case: str, result: dict, run_id: str = "check") -> dict:
    evidence = failure_evidence(root, run_id)
    text = evidence.pop("text")
    marker = evidence.pop("_marker", {})
    state = evidence.pop("_integrity_files", {})
    diagnostics = evidence.pop("_configuration_diagnostics", [])
    owners = evidence.pop("_owner_diagnostics", [])
    actual_exit = result.get("execution", {}).get("exit_code")
    unchanged = (bool(state) and result.get("record_type") == "dependency-invocation" and result.get("mode") == "check" and
                 result.get("run_id") == run_id and result.get("source_input_digest") == marker.get("source_input_digest") and
                 result.get("host") == marker.get("host") and result.get("integrity_before") == state == result.get("integrity_after"))
    verification_failure = bool(re.search(r"dependency verification failed|checksum verification failed", text, re.I)) or any(
        name.endswith(("DependencyVerificationException", "ComponentVerificationException")) for name in evidence["failure_types"])
    rejected = (actual_exit is not None and actual_exit != 0 and evidence["owner_receipts"] > 0 and unchanged and
                not result.get("execution", {}).get("reason"))
    record = {"case": case, "gradle_exit_code": actual_exit, "fresh_cache": True, **evidence,
              "source_and_integrity_identity_unchanged": unchanged,
              "actual_expected_result_observed": False, "result_kind": "unverified", "matched_known_values": []}
    if case in {"baseline-check", "dynamic-transitive-frozen", "included-root-check"}:
        good = (actual_exit == 0 and unchanged and not result.get("execution", {}).get("reason") and
                result.get("selected_project_graph_complete") is True and result.get("checksum_enforcement_exercised") is True)
        if case == "dynamic-transitive-frozen":
            selected = {tuple(value) for value in result.get("graph_summary", {}).get("external_modules", [])}
            good = good and (GROUP, "leaf", "1.0") in selected and (GROUP, "leaf", "1.1") not in selected
        record.update(actual_expected_result_observed=good, result_kind="strict-acceptance" if good else "unverified")
    elif case in {"wrong-jar-sha", "wrong-pom-sha", "standalone-wrong-hash"}:
        module = "parent" if case == "wrong-pom-sha" else "extra" if case == "standalone-wrong-hash" else "leaf"
        extension = ".pom" if case == "wrong-pom-sha" else ".jar"
        name = f"{module}-1.0{extension}"
        expected = "0" * 64 if case == "standalone-wrong-hash" else known_metadata()[(GROUP, module, "1.0", name)]
        actual = m.file_sha256(root / f"repo/{GROUP_DIRECTORY}/{module}/1.0/{name}")
        matched = [value for value in (name, expected, actual) if value in text]
        good = rejected and verification_failure and len(matched) == 3 and expected != actual
        record.update(actual_expected_result_observed=good, result_kind="exact-checksum-rejection" if good else "unverified", matched_known_values=matched)
    elif case == "missing-hash":
        good = rejected and verification_failure and "leaf-1.0.jar" in text and bool(re.search(r"(?:checksum.{0,120}missing|missing.{0,120}checksum|not listed)", text, re.I | re.S))
        record.update(actual_expected_result_observed=good, result_kind="missing-checksum-rejection" if good else "unverified")
    elif case == "transitive-strict-drift":
        constraint = transitive_constraint_evidence(root, marker, diagnostics) if rejected and not verification_failure else None
        record.update(actual_expected_result_observed=constraint is not None,
                      result_kind="exact-transitive-lock-rejection" if constraint is not None else "unverified")
        if constraint is not None:
            record["constraint_evidence"] = constraint
    elif case in LOCK_CASE_BUILDS:
        locking = exact_lock_case_evidence(root, case, marker, diagnostics, owners) if rejected and not verification_failure else None
        record.update(actual_expected_result_observed=locking is not None,
                      result_kind="exact-lock-state-rejection" if locking is not None else "unverified")
        if locking is not None:
            record["lock_evidence"] = locking
    record["invocation_result_sha256"] = m.file_sha256(root / f"build/dependency-integrity/{run_id}/result.json")
    return record


def execute(destination: Path, gradle_home: Path, timeout: int = 300, reserve_mib: int = 8192,
            total_timeout: int = 300, cases: list[str] | None = None) -> dict:
    chosen = selected_cases(cases)
    m.require(1 <= timeout <= 3600 and 20 <= total_timeout <= 3600 and reserve_mib >= 8192,
              "Fixture slots require <=1h per/total limits, >=20s total, and >=8GiB reserve")
    started = time.monotonic()
    deadline = started + total_timeout
    destination = driver._new_workspace_path(destination)
    destination.mkdir(parents=True)
    baseline = destination / "bootstrap"
    result = {"schema_version": 1, "record_type": "actual-gradle-fixtures", "observed_at_utc": driver.utc_now(),
              "gradle_version_required": m.GRADLE_VERSION, "actual_host": m.host_key(),
              "bootstrap_complete": False, "cases": [], "selected_cases": list(chosen),
              "selected_cases_observed_as_expected": False, "selected_subset": chosen != ALL_CASES,
              "total_timeout_seconds": total_timeout, "per_invocation_timeout_seconds": timeout,
              "reserve_mib": reserve_mib, "invocation_attempts": [],
              "maximum_gradle_invocations": len(chosen) + 1 + int(bool(set(chosen) & set(CONTEXT_CASES))),
              "all_cases_observed_as_expected": False, "production_dependencies_verified": False,
              "independent_trust_reviewed": False,
              "remaining_gates": ["Real root/convention source acquisition and ordinary-build policy installation",
                                  "Strict buildscript/settings/detached version-lock coverage",
                                  "Other host runtimes and all library/release gates"]}

    def invoke(root: Path, *, mode: str, entry_root: str = ".") -> dict:
        m.require(time.monotonic() < deadline - 12, "total-timeout-before-next-invocation")
        receipt = driver.run(root, entry_root=entry_root, run_id=mode, mode=mode, timeout=timeout,
                             reserve_mib=reserve_mib, gradle_home=gradle_home, fresh_cache=True, deadline=deadline)
        execution = receipt.get("execution", {})
        result["invocation_attempts"].append({"fixture": root.name, "mode": mode, "entry_root": entry_root,
                                               "gradle_process_started": execution.get("process_started", False),
                                               "exit_code": execution.get("exit_code"),
                                               "stop_reason": execution.get("reason")})
        m.require(not execution.get("reason"), "Fixture slot stopped: " + str(execution.get("reason")))
        return receipt

    def observe(root: Path, case: str, receipt: dict) -> None:
        observed = classify(root, case, receipt)
        result["cases"].append(observed)
        m.require(observed["actual_expected_result_observed"],
                  "Expected fixture result not established for " + case + "; preserve evidence instead of retrying")

    try:
        create(baseline)
        bootstrap = invoke(baseline, mode="bootstrap")
        result["bootstrap_complete"] = bootstrap["selected_project_graph_complete"]
        m.require(result["bootstrap_complete"],
                  "Known-good fixture acquisition failed; no tamper case can be counted as passed")
        for case in (value for value in chosen if value in CASES):
            root = destination / case
            marker = create(root, case=case, base_state=baseline)
            controlled_review(root, marker)
            observe(root, case, invoke(root, mode="check"))
        context_cases = [case for case in chosen if case in CONTEXT_CASES]
        if context_cases:
            included_base = destination / "included-bootstrap"
            create(included_base, included=True, wrong_included_hash=True)
            included = invoke(included_base, mode="bootstrap")
            result["included_bootstrap_complete"] = included["selected_project_graph_complete"]
            m.require(result["included_bootstrap_complete"], "Known-good included-build fixture acquisition failed")
        for case in context_cases:
            entry_root = "included" if case == "standalone-wrong-hash" else "."
            root = destination / case
            marker = create(root, base_state=included_base, included=True, wrong_included_hash=True)
            controlled_review(root, marker, entry_root)
            observe(root, case, invoke(root, mode="check", entry_root=entry_root))
    except (m.IntegrityError, OSError, subprocess.SubprocessError) as failure:
        result["stopped_reason"] = (str(failure) if isinstance(failure, m.IntegrityError) else
                                    "Local fixture preparation/process failure; inspect task-owned evidence")
        result["error_type"] = type(failure).__name__
    except KeyboardInterrupt:
        result["stopped_reason"] = "Interrupted; no remaining fixture was started"
    finally:
        observed = {case["case"] for case in result["cases"] if case["actual_expected_result_observed"]}
        result["selected_cases_observed_as_expected"] = (result["bootstrap_complete"] and
                                                         observed == set(chosen) and "stopped_reason" not in result)
        result["all_cases_observed_as_expected"] = (result["selected_cases_observed_as_expected"] and chosen == ALL_CASES)
        result["unexecuted_cases"] = [case for case in ALL_CASES if case not in {value["case"] for value in result["cases"]}]
        result["remaining_selected_cases"] = [case for case in chosen if case not in observed]
        result["finished_utc"] = driver.utc_now()
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
        m.write_new(destination / "fixture-results.json", m.json_bytes(result))
    return result
