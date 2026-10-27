#!/usr/bin/env python3
"""Explicitly partial, fresh Core/IO desktop Maven consumer verification.

Stage four real publications into the producer's isolated FILE repository, then
copy the standalone fixture and resolve/execute it independently. Never uploads
packages, selects arbitrary tasks, substitutes producer projects/classes, or
certifies the full21-root/native/ABI/legal/dependency/release matrix. This is a
bounded process-group controller, not an OS sandbox, trusted-builder attestation,
or the narrowly supported controlled dependency-fixture daemon owner.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import time

import library_tests as lt
import runtime_context

ROOT = Path(__file__).resolve().parents[2]
GROUP = "io.github.apdelrahman1911.nativecmpkit"
VERSION = "0.1.0-preview.1"
ROOTS = ("nativecmpkit-core", "nativecmpkit-io")
COORDINATES = frozenset(module + suffix for module in ROOTS for suffix in ("", "-desktop"))
FIXTURE = "tests/consumer/io-desktop"
FIXTURE_FILES = (
    "README.md", "build.gradle.kts", "gradle.properties", "settings.gradle.kts",
    "src/test/kotlin/nativecmpkit/consumer/PublishedArtifactOriginTest.kt",
    "src/test/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt",
)
IO_METHODS = (
    "emptyFileReadsThroughBothPublicOverloads", "boundaryAndLargeStreamsPreserveAllBytes",
    "concurrentSourcesHaveIndependentPositions", "existingDirectoryAndMissingFileAreNotRegularFiles",
    "extensionlessFileAndUnicodeNameArePreserved", "repeatedStreamUseLeavesSourceReadableAndDeletable",
)
EXPECTED_CASES = frozenset(
    [("nativecmpkit.consumer.PublishedIoConsumerTest", method) for method in IO_METHODS]
    + [("nativecmpkit.consumer.PublishedArtifactOriginTest", "runtimeLibraryClassesComeFromExactStagedDesktopJars")]
)
REPOSITORY = "build/verification-repo"
GRADLE_HOME = "build/ci-consumer-cache/gradle-home"
MAX_REPOSITORY_BYTES = 512 * 1024**2
MAX_REPOSITORY_FILES = 2048
MAX_FIXTURE_BYTES = 2 * 1024**2
CLASSPATHS = frozenset(("compileClasspath", "runtimeClasspath", "testCompileClasspath", "testRuntimeClasspath"))
SCOPE = "PARTIAL Core/IO desktop Maven consumer; not the complete21-root KMP/ABI/native/legal/dependency/release matrix"


class ConsumerEvidenceError(ValueError):
    """Only fixed contract messages; no raw exception/environment/console export."""


def need(condition: object, message: str) -> None:
    if not condition:
        raise ConsumerEvidenceError(message)


def json_document(path: Path, maximum: int = lt.MAX_REPORT_BYTES) -> dict:
    record = path.stat()
    need(path.is_file() and not path.is_symlink() and record.st_nlink == 1 and record.st_size <= maximum,
         "Expected a bounded regular unshared JSON receipt")
    payload = path.read_bytes()
    need(record == path.stat(), "JSON receipt changed during inspection")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "Duplicate JSON receipt key")
            result[key] = value
        return result

    def nonfinite(_):
        raise ConsumerEvidenceError("Nonfinite JSON receipt number")

    result = json.loads(payload, object_pairs_hook=unique, parse_constant=nonfinite)
    need(isinstance(result, dict), "Expected an object JSON receipt")
    return result


def fixture_inputs(root: Path) -> dict[str, str]:
    files = lt.source_files(root, FIXTURE)
    need({p.relative_to(root / FIXTURE).as_posix() for p in files} == set(FIXTURE_FILES),
         "Standalone partial fixture files differ from the deliberately reviewed scope")
    need(sum(p.stat().st_size for p in files) <= MAX_FIXTURE_BYTES, "Fixture exceeds bounded source size")
    inputs = {}
    for path in files:
        before = path.stat()
        need(before.st_nlink == 1, "Hardlinked consumer source is not accepted")
        inputs[path.relative_to(root).as_posix()] = lt.sha256(path)
        need(before == path.stat(), "Consumer source changed during snapshot")
    source = root / FIXTURE / "src/test/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt"
    full = lt.safe_path(root, "tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt")
    need(source.read_bytes() == full.read_bytes(), "The original six IO consumer scenarios must remain byte-identical")
    return inputs


def inputs(root: Path) -> dict[str, str]:
    result = lt.snapshot_inputs(root)
    result.update(fixture_inputs(root))
    for relative in ("tests/consumer/verify_artifacts.py", "docs/migration/identity.json",
                     "LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"):
        path = lt.safe_path(root, relative)
        need(path.is_file(), "Missing selected package-inspection source input")
        result[relative] = lt.sha256(path)
    for path in lt.source_files(root, "licenses"):
        result[path.relative_to(root).as_posix()] = lt.sha256(path)
    return dict(sorted(result.items()))


def copy_fixture(root: Path, output: Path) -> tuple[Path, dict]:
    before = fixture_inputs(root)
    destination = output / "independent-consumer"
    need(not destination.exists() and not destination.is_symlink(), "Independent consumer directory must be fresh")
    destination.mkdir()
    copied = {}
    for relative in FIXTURE_FILES:
        source = lt.safe_path(root, FIXTURE + "/" + relative)
        target = lt.safe_path(destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        copied[relative] = lt.sha256(target)
        need(copied[relative] == before[FIXTURE + "/" + relative], "Copied consumer source bytes changed")
    need(before == fixture_inputs(root), "Original consumer changed during independent copying")
    return destination, copied


def staged_inputs(repository: Path) -> dict[str, dict]:
    """No extraction; reject wrong coordinates, links, special and oversized files."""
    need(repository.is_dir() and not repository.is_symlink(), "Missing isolated staged Maven repository")
    group_parts = tuple(GROUP.split('.'))
    result, total, coordinates = {}, 0, set()
    for base, directories, files in os.walk(repository, followlinks=False):
        directories.sort()
        for name in [*directories, *sorted(files)]:
            path = lt.safe_path(repository, (Path(base) / name).relative_to(repository).as_posix())
            relative = path.relative_to(repository).as_posix()
            parts = PurePosixPath(relative).parts
            need(parts[:min(len(parts), len(group_parts))] == group_parts[:min(len(parts), len(group_parts))],
                 "Foreign group in the four-coordinate staging repository")
            if len(parts) > len(group_parts):
                coordinate = parts[len(group_parts)]
                need(coordinate in COORDINATES, "Unselected publication coordinate in partial staging")
                coordinates.add(coordinate)
            record = path.stat()
            if stat.S_ISDIR(record.st_mode):
                if len(parts) > len(group_parts) + 1:
                    need(len(parts) == len(group_parts) + 2 and parts[-1] == VERSION,
                         "Foreign version or nested directory in staged publication")
                continue
            need(stat.S_ISREG(record.st_mode) and record.st_nlink == 1, "Non-regular or hardlinked staged Maven file")
            # Exact-version payloads and Gradle's coordinate-level metadata/checksums only.
            need((len(parts) == len(group_parts) + 3 and parts[-2] == VERSION)
                 or (len(parts) == len(group_parts) + 2 and re.fullmatch(r"maven-metadata\.xml(?:\.(?:md5|sha1|sha256|sha512))?", parts[-1])),
                 "Unexpected staged Maven file layout")
            total += record.st_size
            need(record.st_size <= MAX_REPOSITORY_BYTES and total <= MAX_REPOSITORY_BYTES and len(result) < MAX_REPOSITORY_FILES,
                 "Partial Maven staging exceeds bounded input size")
            digest = lt.sha256(path)
            need(record == path.stat(), "Staged Maven bytes changed during capture")
            result[relative] = {"bytes": record.st_size, "sha256": digest}
    need(coordinates == COORDINATES and result, "All four actual staged Maven coordinates must be present")
    return dict(sorted(result.items()))


def commands(root: Path, consumer: Path) -> tuple[list[str], list[str]]:
    repository = lt.safe_path(root, REPOSITORY)
    wrapper = lt.safe_path(root, "gradlew")
    base = [str(wrapper), "--no-daemon", "--no-parallel", "--no-configuration-cache", "--no-build-cache",
            "--console=plain", "--max-workers=2", "--dependency-verification", "strict",
            "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8", "-Pkotlin.compiler.execution.strategy=in-process"]
    producer = [*base, "--init-script", str(lt.safe_path(root, "scripts/ci/stage-core-io.init.gradle.kts")),
                "-PnativecmpkitVerification=true", "-PnativecmpkitVerificationTargets=desktop",
                "-PnativeCmpkit.version=" + VERSION, "stageCoreIoVerificationPublications"]
    # The wrapper is toolchain acquisition, not producer source/class substitution.
    # Both cwd and -p point to the independent copied settings/build directory.
    child = [*base, "-p", str(consumer), "-PnativecmpkitRepository=" + str(repository),
             "-PnativecmpkitVersion=" + VERSION, "verifyCandidateResolution", "test"]
    return producer, child


def environment(root: Path, output: Path) -> dict[str, str]:
    jdk = os.environ.get("JAVA_HOME")
    need(bool(jdk) and Path(jdk).is_absolute() and (Path(jdk) / "bin/java").is_file(), "Explicit installed JDK17 is required")
    home = output / "user-home"
    temporary = output / "temporary"
    gradle = lt.safe_path(root, GRADLE_HOME)
    for path in (home, temporary, gradle):
        need(not any(c in str(path) for c in ('"', "'", '\\', '\n', '\r')), "Private JVM path cannot be represented safely")
        path.mkdir(parents=True, exist_ok=True)
    # Only wrapper/registry dependency bytes may be restored. Foreign user
    # properties/init scripts are never inherited. Cache bytes remain untrusted.
    for relative in ("init.d", "init.gradle", "init.gradle.kts", "gradle.properties"):
        path = lt.safe_path(gradle, relative)
        need(not path.exists(), "Private Gradle home contains unreviewed user configuration")
    value = {"JAVA_HOME": jdk, "PATH": str(Path(jdk) / "bin") + os.pathsep + os.environ.get("PATH", os.defpath),
             "HOME": str(home), "GRADLE_USER_HOME": str(gradle), "TMPDIR": str(temporary),
             "XDG_CONFIG_HOME": str(home / ".config"), "XDG_CACHE_HOME": str(home / ".cache"),
             "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
             "JAVA_TOOL_OPTIONS": f'-Duser.home="{home}" -Djava.io.tmpdir="{temporary}"'}
    for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT", "CARGO_HOME", "RUSTUP_HOME"):
        if os.environ.get(name):
            value[name] = os.environ[name]
    return value


def verify_static(root: Path, repository: Path) -> dict:
    # The exact existing gate, with a deliberately explicit two-root filter;
    # its default full21-root behavior and required target/native matrix stay intact.
    sys.path.insert(0, str(ROOT / "tests/consumer"))
    import verify_artifacts
    result = verify_artifacts.ArtifactVerifier(root, repository, VERSION, list(ROOTS), ["desktop"], ["linux-x64"]).run()
    return result


def static_contract(document: dict) -> None:
    need(document.get("success") is True and type(document.get("check_count")) is int and document["check_count"] > 0
         and document.get("failed_check_count") == 0, "Actual staged Core/IO static inspection failed")
    need(document.get("group") == GROUP and document.get("version") == VERSION and document.get("modules") == list(ROOTS)
         and document.get("targets") == ["metadata", "desktop"] and document.get("native_platforms_requested") == ["linux-x64"],
         "Static package report does not describe the exact partial scope")
    need(document.get("complete_declared_artifact_matrix_requested") is False and document.get("release_readiness_certified") is False,
         "A partial static report must not certify the full matrix or release")


def resolution_contract(document: dict, staged: dict[str, dict]) -> dict:
    need(type(document.get("schema_version")) is int and document["schema_version"] == 1
         and document.get("scope") == "PARTIAL Core/IO desktop Maven consumer"
         and document.get("candidate_group") == GROUP and document.get("candidate_version") == VERSION
         and document.get("publication_roots_requested") == list(ROOTS), "Unexpected independent consumer resolution schema/identity")
    need(document.get("complete_21_root_KMP_matrix_requested") is False and document.get("release_readiness_certified") is False,
         "Partial resolution must not certify the full21-root matrix or release")
    rows = document.get("resolved_artifacts")
    need(isinstance(rows, list) and 1 <= len(rows) <= 4096, "Missing or unbounded independently resolved artifact rows")
    seen = {name: set() for name in CLASSPATHS}
    identities, variants, candidates = set(), set(), []
    for row in rows:
        need(isinstance(row, dict) and set(row) == {"configuration", "group", "module", "version", "file", "bytes", "sha256"},
             "Unexpected resolved artifact row fields")
        need(row["configuration"] in CLASSPATHS and all(isinstance(row[k], str) and row[k] for k in ("group", "module", "version", "file", "sha256")),
             "Invalid resolved Maven identity or selected classpath")
        need(row["group"] != "com.mohamedrejeb.calf", "Original Calf artifact in independent consumer")
        need(type(row["bytes"]) is int and row["bytes"] > 0 and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
             "Invalid resolved artifact byte identity")
        identity = tuple(row[k] for k in ("configuration", "group", "module", "version", "file"))
        need(identity not in identities, "Duplicate resolved artifact row")
        identities.add(identity)
        need(Path(row["file"]).name == row["file"] and '/' not in row["file"] and '\\' not in row["file"]
             and row["file"] not in {'.', '..'}, "Noncanonical resolved artifact filename")
        if row["group"] == GROUP:
            need(row["module"] in {m + "-desktop" for m in ROOTS} and row["version"] == VERSION,
                 "Wrong desktop candidate coordinate in independent consumer")
            need(row["file"] == row["module"] + "-" + VERSION + ".jar", "Consumer must resolve actual primary desktop JARs")
            relative = GROUP.replace('.', '/') + '/' + row["module"] + '/' + VERSION + '/' + row["file"]
            need(staged.get(relative) == {"bytes": row["bytes"], "sha256": row["sha256"]}, "Resolved candidate differs from exact staged bytes")
            seen[row["configuration"]].add(row["module"])
            variants.add(row["module"])
            candidates.append(row)
    required = {m + "-desktop" for m in ROOTS}
    need(all(value == required for value in seen.values()), "Both desktop roots must resolve on all four selected classpaths")
    need(document.get("candidate_variants_resolved") == sorted(variants), "Reported candidate variant inventory differs from actual rows")
    return {"classpath_count": len(seen), "candidate_artifact_rows": candidates, "all_resolved_artifact_rows": len(rows)}


def fresh_resolution(consumer: Path, staged: dict, start: int, end: int) -> tuple[dict, dict]:
    path = lt.safe_path(consumer, "build/reports/partial-consumer-resolution.json")
    record = path.stat()
    need(start - 2_000_000_000 <= record.st_mtime_ns <= end + 2_000_000_000, "Stale or future independent resolution report")
    document = json_document(path)
    return document, {"path": "independent-consumer/build/reports/partial-consumer-resolution.json",
                      "sha256": lt.sha256(path), **resolution_contract(document, staged)}


def fresh_tests(consumer: Path, output: Path, start: int, end: int, log: Path) -> dict:
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    markers = Counter(line for line in lines if line.startswith("NATIVECMPKIT_PARTIAL_CONSUMER_TEST "))
    expected = "NATIVECMPKIT_PARTIAL_CONSUMER_TEST task=:test gradle=9.7.1 java=17"
    need(markers == {expected: 1}, "Expected exactly one fresh independent Gradle9.7.1/JDK17 test-task marker")
    folder = lt.safe_path(consumer, "build/test-results/test")
    files = lt.source_files(consumer, "build/test-results/test")
    xmls = [p for p in files if p.name.startswith("TEST-") and p.suffix == ".xml"]
    need(folder.is_dir() and len(xmls) == 2, "Both explicit consumer classes must produce fresh JUnit XML")
    cases, reports = [], []
    # Save only original XML to the evidence directory; no consumer binaries.
    destination = output / "junit"
    need(not destination.exists(), "Consumer XML evidence directory must be fresh")
    destination.mkdir()
    for path in xmls:
        record = path.stat()
        need(path.is_file() and record.st_nlink == 1 and record.st_size <= lt.MAX_REPORT_BYTES, "Invalid consumer JUnit file")
        need(start - 2_000_000_000 <= record.st_mtime_ns <= end + 2_000_000_000, "Stale or future consumer JUnit report")
        payload = path.read_bytes()
        need(record == path.stat(), "Consumer JUnit file changed during capture")
        parsed = lt.junit_cases(payload)
        cases.extend(parsed)
        target = destination / path.name
        need(not target.exists(), "Duplicate consumer XML evidence filename")
        with target.open("xb") as stream:
            stream.write(payload)
        reports.append({"path": "junit/" + path.name, "sha256": hashlib.sha256(payload).hexdigest(), **lt.case_counts(parsed)})
    actual = [(c["classname"], c["name"]) for c in cases]
    need(len(actual) == len(set(actual)) and set(actual) == EXPECTED_CASES,
         "Exactly all seven named consumer methods must execute; missing/extra/duplicate methods are not accepted")
    totals = lt.case_counts(cases)
    need(totals["passed"] == totals["executed"] == 7 and not any(totals[k] for k in ("failures", "errors", "skipped")),
         "Every applicable consumer method must pass; no skipped tests")
    return {"reports": reports, "testcases": cases, "totals": totals, "fresh_task_marker": expected}


def write(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def run(root: Path, relative: str, timeout: int = 4200, reserve_mib: int = 8192) -> dict:
    need(600 <= timeout <= 4800 and reserve_mib >= 8192, "Require bounded600–4800s execution and an8GiB reserve")
    output = lt.safe_path(root, relative)
    base = lt.safe_path(root, "build/ci-consumer")
    need(output != base and output.is_relative_to(base) and not output.exists(), "Use a fresh confined partial consumer output directory")
    output.mkdir(parents=True)
    record = {"schema_version": 1, "scope": SCOPE, "passed": False, "source_revision": lt.git_revision(root),
              "started_utc": lt.utc_now(), "candidate_group": GROUP, "candidate_version": VERSION,
              "publication_roots_requested": list(ROOTS), "target": "desktop", "native_platform": "linux-x64",
              "complete_21_root_KMP_matrix_requested": False, "release_readiness_certified": False,
              "packages_published": False, "release_created": False, "ordinary_dependency_trust_certified": False,
              "process_cleanup_scope": "Bounded owned process group only; detached Gradle/other descendant cleanup is not attested by this controller",
              "executions": [], "actual_consumer_methods_verified": 0}
    lock = base / ".core-io-consumer.lock"
    lock_fd, before, staged, copied = None, None, None, None
    began, phase = time.monotonic(), "preflight"
    try:
        lock_fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        record["free_bytes_before"] = shutil.disk_usage(root).free
        need(record["free_bytes_before"] >= reserve_mib * 1024**2, "Disk reserve unavailable; no Java/Gradle command started")
        runtime = runtime_context.capture(expected_arch="x64", android_package="android-37.0", require_clean=True)
        need(runtime["host"]["system"] == "Linux" and runtime["source_revision"] == record["source_revision"],
             "This fixed diagnostic requires the real immutable Linux/x64 runtime")
        record["source_tree_dirty"] = runtime["source_tree_dirty"]
        write(output / "runtime-before.json", runtime)
        before = inputs(root)
        write(output / "inputs-before.json", before)
        repository = lt.safe_path(root, REPOSITORY)
        need(not repository.exists(), "Refuse stale producer staging; no package/cache deletion is authorized")
        consumer, copied = copy_fixture(root, output)
        write(output / "fixture-copy.json", copied)
        env = environment(root, output)
        producer_command, consumer_command = commands(root, consumer)
        phase = "real-producer-staging"
        log = output / "producer.log"
        result = lt.execute(root, producer_command, log, min(3000, timeout - 120), reserve_mib, env=env)
        record["executions"].append({"phase": phase, "command": producer_command, "execution": result,
                                     "log_sha256": lt.sha256(log) if log.exists() else None})
        need(result["exit_code"] == 0 and not result.get("stop_reason"), "Actual four-publication producer staging did not pass")
        markers = re.findall(r"(?m)^NATIVECMPKIT_PARTIAL_STAGE task=(:[A-Za-z0-9:-]+) group=" + re.escape(GROUP) + r" version=" + re.escape(VERSION) + r"$", log.read_text(errors="replace"))
        expected_tasks = {f':calf-{module}:publish{publication}PublicationToNativecmpkitVerificationRepository'
                          for module in ('core', 'io') for publication in ('KotlinMultiplatform', 'Desktop')}
        need(len(markers) == 4 and set(markers) == expected_tasks, "Exactly four actual Core/IO publication-task markers are required")
        record["actual_publication_task_markers"] = sorted(markers)
        staged = staged_inputs(repository)
        write(output / "staging-before.json", staged)
        phase = "actual-package-static-inspection"
        static_report = verify_static(root, repository)
        write(output / "static-packages.json", static_report)
        static_contract(static_report)
        phase = "independent-packaged-consumer"
        remaining = timeout - int(time.monotonic() - began) - 30
        need(remaining > 0, "No bounded time remains for the independent consumer")
        start_ns = time.time_ns()
        log = output / "consumer.log"
        result = lt.execute(consumer, consumer_command, log, min(1800, remaining), reserve_mib, env=env)
        end_ns = time.time_ns()
        record["executions"].append({"phase": phase, "command": consumer_command, "execution": result,
                                     "log_sha256": lt.sha256(log) if log.exists() else None})
        record["consumer_started_ns"], record["consumer_ended_ns"] = start_ns, end_ns
        # Preserve fresh XML outcomes even when tests fail. A failing build/report
        # never becomes a success; no counts are invented before complete review.
        phase = "fresh-independent-resolution-and-tests"
        resolution, resolution_review = fresh_resolution(consumer, staged, start_ns, end_ns)
        write(output / "resolution.json", resolution)
        record["resolution_review"] = resolution_review
        record["consumer_tests"] = fresh_tests(consumer, output, start_ns, end_ns, log)
        need(result["exit_code"] == 0 and not result.get("stop_reason"), "Independent consumer Gradle execution did not pass")
        phase = "source-artifact-runtime-held-review"
        after_staging = staged_inputs(repository)
        write(output / "staging-after.json", after_staging)
        need(after_staging == staged, "Staged Maven artifact bytes changed during consumption")
        copy_after = {p: lt.sha256(lt.safe_path(consumer, p)) for p in FIXTURE_FILES}
        need(copy_after == copied, "Independent copied fixture changed during execution")
        after = inputs(root)
        write(output / "inputs-after.json", after)
        need(before == after and record["source_revision"] == lt.git_revision(root), "Producer/consumer source revision or bytes changed during verification")
        runtime_after = runtime_context.capture(expected_arch="x64", android_package="android-37.0", require_clean=True)
        write(output / "runtime-after.json", runtime_after)
        need(all(runtime_after.get(k) == runtime.get(k) for k in ("source_revision", "source_tree_dirty", "host", "java", "rust", "android_platform", "compiler_runtime_fingerprint")),
             "Runtime compiler/SDK/source identity changed during verification")
        record.update(passed=True, actual_consumer_methods_verified=7, source_input_count=len(before),
                      inputs_before_sha256=lt.input_digest(before), inputs_after_sha256=lt.input_digest(after),
                      staged_file_count=len(staged), staged_total_bytes=sum(v['bytes'] for v in staged.values()))
    except (ConsumerEvidenceError, OSError, ValueError, KeyError, TypeError) as failure:
        record["error"] = {"phase": phase, "type": type(failure).__name__,
                           "contract": str(failure) if isinstance(failure, ConsumerEvidenceError) else "Verification phase failed; inspect bounded public fixture diagnostics"}
    finally:
        if lock_fd is not None:
            owned_stat = os.fstat(lock_fd)
            os.close(lock_fd)
            current_stat = lock.stat(follow_symlinks=False)
            need((owned_stat.st_dev, owned_stat.st_ino) == (current_stat.st_dev, current_stat.st_ino), "Refuse removing a replaced consumer lock")
            lock.unlink()
        record.update(finished_utc=lt.utc_now(), elapsed_seconds=round(time.monotonic() - began, 3),
                      free_bytes_after=shutil.disk_usage(root).free)
        write(output / "receipt.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="build/ci-consumer/core-io-desktop")
    parser.add_argument("--timeout", type=int, default=4200)
    parser.add_argument("--reserve-mib", type=int, default=8192)
    args = parser.parse_args()
    result = run(ROOT, args.output, args.timeout, args.reserve_mib)
    print(json.dumps({k: result[k] for k in ("scope", "passed", "actual_consumer_methods_verified", "release_readiness_certified", "error") if k in result}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
