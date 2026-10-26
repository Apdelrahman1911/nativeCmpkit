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
    elif case == "missing-configuration-lock":
        build.write_text(BASE_BUILD + '''configurations {
    newUnrecordedClasspath { canBeResolved = true; canBeConsumed = false }
}
dependencies { add("newUnrecordedClasspath", "org.nativecmpkit.fixture:extra:1.0") }
''')
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
    elif case == "added-dependency":
        build.write_text(BASE_BUILD + 'dependencies { add("fixtureClasspath", "org.nativecmpkit.fixture:extra:1.0") }\n')
    elif case == "removed-dependency":
        build.write_text(BASE_BUILD + 'configurations.fixtureClasspath.exclude(group: "org.nativecmpkit.fixture", module: "leaf")\n')
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
    types: set[str] = set()
    messages: list[str] = []
    count = 0
    graph_root = root / f"build/dependency-integrity/{run_id}/graphs"
    if graph_root.exists():
        for part in sorted(graph_root.glob("*/parts/*.json")):
            record = m.read_json(part)
            m.require(record.get("run_id") == run_id and record.get("gradle_version") == m.GRADLE_VERSION and
                      record.get("java_major") == 17, "Failure did not reach the exact fixture Gradle/JVM")
            count += 1
            for configuration in record.get("configurations", []):
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
    return {"owner_receipts": count, "failure_types": sorted(types), "text": "\n".join(messages)}


def classify(root: Path, case: str, result: dict, run_id: str = "check") -> dict:
    evidence = failure_evidence(root, run_id)
    text = evidence.pop("text")
    actual_exit = result.get("execution", {}).get("exit_code")
    verification_failure = bool(re.search(r"dependency verification failed|checksum verification failed", text, re.I)) or any(
        name.endswith(("DependencyVerificationException", "ComponentVerificationException")) for name in evidence["failure_types"])
    rejected = (actual_exit is not None and actual_exit != 0 and evidence["owner_receipts"] > 0 and
                not result.get("execution", {}).get("reason"))
    record = {"case": case, "gradle_exit_code": actual_exit, "fresh_cache": True, **evidence,
              "actual_expected_result_observed": False, "result_kind": "unverified", "matched_known_values": []}
    if case in {"baseline-check", "dynamic-transitive-frozen", "included-root-check"}:
        good = actual_exit == 0 and result.get("selected_project_graph_complete") is True and result.get("checksum_enforcement_exercised") is True
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
    else:
        locking_failure = any(name.endswith(("MissingLockStateException", "LockOutOfDateException")) for name in evidence["failure_types"])
        locking_message = bool(re.search(r"dependency lock|locked to version|lock state", text, re.I))
        if case == "transitive-strict-drift":
            good = rejected and not verification_failure and locking_message and all(value in text for value in ("leaf", "1.0", "1.1"))
        else:
            good = rejected and not verification_failure and (locking_failure or locking_message)
        record.update(actual_expected_result_observed=good, result_kind="lock-rejection" if good else "unverified")
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
