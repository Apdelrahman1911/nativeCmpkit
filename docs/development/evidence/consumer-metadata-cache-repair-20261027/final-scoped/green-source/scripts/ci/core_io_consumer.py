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
MAX_MODULE_METADATA_BYTES = 2 * 1024**2
CLASSPATHS = frozenset(("compileClasspath", "runtimeClasspath", "testCompileClasspath", "testRuntimeClasspath"))
SCOPE = "PARTIAL Core/IO desktop Maven consumer; not the complete21-root KMP/ABI/native/legal/dependency/release matrix"


class ConsumerEvidenceError(ValueError):
    """Only fixed contract messages; no raw exception/environment/console export."""


def need(condition: object, message: str) -> None:
    if not condition:
        raise ConsumerEvidenceError(message)


def stable_stat(record: os.stat_result) -> tuple:
    # Reads may legitimately update access time. Bind content/owner identity,
    # not atime; still reject size/mtime/ctime/inode/device/link replacements.
    return (record.st_dev, record.st_ino, record.st_size, record.st_mtime_ns,
            record.st_ctime_ns, record.st_nlink, record.st_mode)


def json_document(path: Path, maximum: int = lt.MAX_REPORT_BYTES) -> dict:
    record = path.stat()
    need(path.is_file() and not path.is_symlink() and record.st_nlink == 1 and record.st_size <= maximum,
         "Expected a bounded regular unshared JSON receipt")
    payload = path.read_bytes()
    need(stable_stat(record) == stable_stat(path.stat()), "JSON receipt changed during inspection")

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
        need(stable_stat(before) == stable_stat(path.stat()), "Consumer source changed during snapshot")
    source = root / FIXTURE / "src/test/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt"
    full = lt.safe_path(root, "tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt")
    need(source.read_bytes() == full.read_bytes(), "The original six IO consumer scenarios must remain byte-identical")
    return inputs


def inputs(root: Path) -> dict[str, str]:
    result = lt.snapshot_inputs(root)
    result.update(fixture_inputs(root))
    for relative in ("tests/consumer/verify_artifacts.py", "docs/migration/identity.json",
                     "tests/consumer/build.gradle.kts", "tests/consumer/settings.gradle.kts",
                     "tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt",
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
            need(stable_stat(record) == stable_stat(path.stat()), "Staged Maven bytes changed during capture")
            result[relative] = {"bytes": record.st_size, "sha256": digest}
    need(coordinates == COORDINATES and result, "All four actual staged Maven coordinates must be present")
    return dict(sorted(result.items()))


def module_file_bindings(repository: Path, staged: dict[str, dict]) -> dict[str, dict]:
    """Bind Gradle's display/cache names to canonical Maven URLs and held bytes.

    KGP retains project-based files.name while publishing a nativeCmpkit files.url.
    Only the two known native/retained primary labels are eligible; the ACTUAL
    declared label, root redirect, metadata hash, size and payload hash all bind.
    Never accepts arbitrary aliases, URL traversal, source JARs or POM fallback.
    """
    bindings = {}
    for root in ROOTS:
        module = root + '-desktop'
        directory = GROUP.replace('.', '/') + '/' + module + '/' + VERSION + '/'
        metadata_file = directory + module + '-' + VERSION + '.module'
        root_file = GROUP.replace('.', '/') + '/' + root + '/' + VERSION + '/' + root + '-' + VERSION + '.module'
        need(metadata_file in staged and root_file in staged, "Missing exact target/root Gradle module metadata")
        path = lt.safe_path(repository, metadata_file)
        value = json_document(path, MAX_MODULE_METADATA_BYTES)
        need(lt.sha256(path) == staged[metadata_file]['sha256'] and path.stat().st_size == staged[metadata_file]['bytes'],
             "Module metadata differs from held staged bytes")
        component = value.get('component')
        need(value.get('formatVersion') == '1.1' and isinstance(component, dict)
             and all(component.get(key) == expected for key, expected in
                     (('group', GROUP), ('module', root), ('version', VERSION),
                      ('url', f'../../{root}/{VERSION}/{root}-{VERSION}.module'))),
             "Target metadata must point to the exact independent candidate root")
        variants = value.get('variants')
        need(isinstance(variants, list) and 1 <= len(variants) <= 128, "Missing or unbounded target metadata variants")
        primary, usages = [], []
        canonical = module + '-' + VERSION + '.jar'
        allowed_names = {canonical, module.replace('nativecmpkit-', 'calf-', 1) + '-' + VERSION + '.jar'}
        for variant in variants:
            need(isinstance(variant, dict), "Non-object target metadata variant")
            attributes = variant.get('attributes')
            need(isinstance(attributes, dict), "Missing target metadata variant attributes")
            if attributes.get('org.gradle.category') != 'library':
                continue  # documentation/sources are never primary consumer payloads
            usage = attributes.get('org.gradle.usage')
            need(usage in {'java-api', 'java-runtime'} and attributes.get('org.gradle.libraryelements') == 'jar'
                 and attributes.get('org.jetbrains.kotlin.platform.type') == 'jvm', "Unexpected primary desktop metadata attributes")
            files = variant.get('files')
            need(isinstance(files, list) and len(files) == 1 and isinstance(files[0], dict),
                 "Exactly one primary file per desktop API/runtime metadata variant is required")
            file = files[0]
            need(file.get('name') in allowed_names and file.get('url') == canonical,
                 "Primary metadata name/URL must be the exact known candidate label and canonical Maven filename")
            relative = directory + canonical
            need(relative in staged and type(file.get('size')) is int and file['size'] > 0
                 and file.get('size') == staged[relative]['bytes'] and file.get('sha256') == staged[relative]['sha256'],
                 "Primary module metadata must match the exact staged payload size/hash")
            primary.append({'declared_file_name': file['name'], 'declared_file_url': canonical,
                            'staged_file': relative, 'metadata_file': metadata_file,
                            'metadata_sha256': staged[metadata_file]['sha256'],
                            'bytes': file['size'], 'sha256': file['sha256']})
            usages.append(usage)
        need(sorted(usages) == ['java-api', 'java-runtime'] and len(primary) == 2 and primary[0] == primary[1],
             "Both desktop API/runtime variants must declare the same exact primary payload")
        bindings[module] = primary[0]
    return bindings


def commands(root: Path, consumer: Path) -> tuple[list[str], list[str]]:
    repository = lt.safe_path(root, REPOSITORY)
    wrapper = lt.safe_path(root, "gradlew")
    base = [str(wrapper), "--no-daemon", "--no-parallel", "--no-configuration-cache", "--no-build-cache",
            "--console=plain", "--max-workers=2", "--dependency-verification", "strict",
            "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8", "-Pkotlin.compiler.execution.strategy=in-process"]
    # Gradle init scripts also run in included builds. Bind this adapter to the
    # actual producer directory before any included-root project/task lookup.
    producer = [*base, "-Dnativecmpkit.partialStagingRoot=" + str(root.resolve()),
                "--init-script", str(lt.safe_path(root, "scripts/ci/stage-core-io.init.gradle.kts")),
                "-PnativecmpkitVerification=true", "-PnativecmpkitVerificationTargets=desktop",
                "-PnativeCmpkit.version=" + VERSION, "stageCoreIoVerificationPublications"]
    # The wrapper is toolchain acquisition, not producer source/class substitution.
    # Both cwd and -p point to the independent copied settings/build directory.
    child = [*base, "-p", str(consumer), "-PnativecmpkitRepository=" + str(repository),
             "-PnativecmpkitVersion=" + VERSION, "verifyCandidateResolution", "test"]
    return producer, child


def producer_cache_state(root: Path) -> dict:
    """Observe known candidate payload/descriptor group paths; never delete data.

    This is a narrow cache-export fence, not a scan/certification of ordinary
    dependencies, an OS sandbox, or proof that malicious code cannot write files.
    """
    cache = lt.safe_path(root, GRADLE_HOME + '/caches/modules-2')
    groups = ['files-2.1/' + GROUP]
    if cache.exists():
        need(cache.is_dir(), "Expected a directory for the producer dependency cache")
        entries = list(cache.iterdir())
        need(len(entries) <= 256, "Unbounded producer module-cache root inventory")
        for entry in entries:
            if re.fullmatch(r'metadata-[0-9]+(?:\.[0-9]+)+', entry.name):
                groups.append(entry.name + '/descriptors/' + GROUP)
    observations = {}
    for relative in sorted(groups):
        path = lt.safe_path(cache, relative)
        observations[relative] = path.exists()
    return {'producer_gradle_home': GRADLE_HOME,
            'candidate_group': GROUP, 'candidate_group_paths_present': observations,
            'candidate_payload_group_absent': not any(observations.values()),
            'scope': 'Known candidate group absence in cached producer modules-2 only; no dependency trust or OS isolation certification'}


def environment(root: Path, output: Path, *, consumer: bool = False) -> dict[str, str]:
    need(type(consumer) is bool, "Require the fixed producer or consumer environment")
    jdk = os.environ.get("JAVA_HOME")
    need(bool(jdk) and Path(jdk).is_absolute() and (Path(jdk) / "bin/java").is_file(), "Explicit installed JDK17 is required")
    home = lt.safe_path(output, "consumer-user-home" if consumer else "user-home")
    temporary = lt.safe_path(output, "consumer-temporary" if consumer else "temporary")
    gradle = lt.safe_path(output, "consumer-gradle-home") if consumer else lt.safe_path(root, GRADLE_HOME)
    if consumer:
        need(not gradle.exists(), "The uncached consumer Gradle home must be fresh; preserve any old data")
        need(not gradle.is_relative_to(lt.safe_path(root, GRADLE_HOME)), "Consumer cannot share the cached producer Gradle home")
    else:
        need(producer_cache_state(root)['candidate_payload_group_absent'], "Candidate group in producer cache; do not restore/export this cache")
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


def resolution_contract(document: dict, staged: dict[str, dict], bindings: dict[str, dict]) -> dict:
    need(type(document.get("schema_version")) is int and document["schema_version"] == 2
         and document.get("scope") == "PARTIAL Core/IO desktop Maven consumer"
         and document.get("candidate_group") == GROUP and document.get("candidate_version") == VERSION
         and document.get("publication_roots_requested") == list(ROOTS), "Unexpected independent consumer resolution schema/identity")
    need(document.get("complete_21_root_KMP_matrix_requested") is False and document.get("release_readiness_certified") is False,
         "Partial resolution must not certify the full21-root matrix or release")
    rows = document.get("resolved_artifacts")
    need(isinstance(rows, list) and 1 <= len(rows) <= 4096, "Missing or unbounded independently resolved artifact rows")
    required = {m + "-desktop" for m in ROOTS}
    need(set(bindings) == required, "Both exact module metadata bindings must be present")
    seen = {name: set() for name in CLASSPATHS}
    identities, variants, candidates = set(), set(), []
    for row in rows:
        fields = {"configuration", "group", "module", "version", "file", "bytes", "sha256"}
        if isinstance(row, dict) and row.get('group') == GROUP:
            fields |= {'declared_file_name', 'declared_file_url', 'staged_file', 'metadata_file', 'metadata_sha256'}
        need(isinstance(row, dict) and set(row) == fields,
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
            need(row["module"] in required and row["version"] == VERSION,
                 "Wrong desktop candidate coordinate in independent consumer")
            binding = bindings[row['module']]
            need(all(row[key] == value for key, value in binding.items()) and row['file'] == binding['declared_file_name'],
                 "Resolved artifact must match the actual held metadata label/URL/hash binding")
            relative = binding['staged_file']
            need(staged.get(relative) == {"bytes": row["bytes"], "sha256": row["sha256"]}, "Resolved candidate differs from exact staged bytes")
            need(staged.get(binding['metadata_file'], {}).get('sha256') == binding['metadata_sha256'],
                 "Resolved metadata binding differs from the exact staged metadata hash")
            seen[row["configuration"]].add(row["module"])
            variants.add(row["module"])
            candidates.append(row)
    required = {m + "-desktop" for m in ROOTS}
    need(all(value == required for value in seen.values()), "Both desktop roots must resolve on all four selected classpaths")
    need(document.get("candidate_variants_resolved") == sorted(variants), "Reported candidate variant inventory differs from actual rows")
    return {"classpath_count": len(seen), "candidate_artifact_rows": candidates, "all_resolved_artifact_rows": len(rows)}


def fresh_resolution(consumer: Path, staged: dict, bindings: dict, start: int, end: int) -> tuple[dict, dict]:
    path = lt.safe_path(consumer, "build/reports/partial-consumer-resolution.json")
    record = path.stat()
    need(start - 2_000_000_000 <= record.st_mtime_ns <= end + 2_000_000_000, "Stale or future independent resolution report")
    document = json_document(path)
    return document, {"path": "independent-consumer/build/reports/partial-consumer-resolution.json",
                      "sha256": lt.sha256(path), **resolution_contract(document, staged, bindings)}


def fresh_tests(consumer: Path, output: Path, start: int, end: int, log: Path) -> dict:
    need(log.is_file() and not log.is_symlink() and log.stat().st_nlink == 1 and log.stat().st_size <= 64 * 1024**2,
         "Expected a bounded owned consumer log")
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
        need(stable_stat(record) == stable_stat(path.stat()), "Consumer JUnit file changed during capture")
        parsed = lt.junit_cases(payload)
        cases.extend(parsed)
        target = destination / path.name
        need(not target.exists(), "Duplicate consumer XML evidence filename")
        with target.open("xb") as stream:
            stream.write(payload)
        reports.append({"path": "junit/" + path.name, "sha256": hashlib.sha256(payload).hexdigest(), **lt.case_counts(parsed)})
    observation = {"reports": reports, "testcases": cases, "totals": lt.case_counts(cases),
                   "fresh_task_marker": expected, "scope": "Fresh XML observations; the seven-method acceptance check follows, not implied"}
    write(output / "test-outcomes.json", observation)
    actual = [(c["classname"], c["name"]) for c in cases]
    need(len(actual) == len(set(actual)) and set(actual) == EXPECTED_CASES,
         "Exactly all seven named consumer methods must execute; missing/extra/duplicate methods are not accepted")
    totals = lt.case_counts(cases)
    need(totals["passed"] == totals["executed"] == 7 and not any(totals[k] for k in ("failures", "errors", "skipped")),
         "Every applicable consumer method must pass; no skipped tests")
    return observation


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
    lock_fd, before, staged, copied, producer_home, consumer = None, None, None, None, None, None
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
        cache_before = producer_cache_state(root)
        write(output / 'producer-cache-before.json', cache_before)
        need(cache_before['candidate_payload_group_absent'], "Candidate group in producer cache; no verification command started")
        producer_home = lt.safe_path(root, GRADLE_HOME)
        record['cache_containment'] = {'producer_gradle_home': GRADLE_HOME,
                                       'consumer_gradle_home': relative + '/consumer-gradle-home',
                                       'consumer_home_fresh_and_not_cached': False,
                                       'candidate_payload_group_absent_before': True,
                                       'scope': 'Separate Gradle/HOME/tmp paths and known candidate group fence; not an OS sandbox or ordinary dependency trust/daemon attestation'}
        producer_env = environment(root, output)
        consumer_env = environment(root, output, consumer=True)
        record['cache_containment']['consumer_home_fresh_and_not_cached'] = True
        producer_command, consumer_command = commands(root, consumer)
        phase = "real-producer-staging"
        log = output / "producer.log"
        result = lt.execute(root, producer_command, log, min(3000, timeout - 120), reserve_mib, env=producer_env)
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
        phase = 'actual-module-file-binding'
        bindings = module_file_bindings(repository, staged)
        write(output / 'module-file-bindings.json', bindings)
        phase = "actual-package-static-inspection"
        static_report = verify_static(root, repository)
        write(output / "static-packages.json", static_report)
        static_contract(static_report)
        phase = "independent-packaged-consumer"
        remaining = timeout - int(time.monotonic() - began) - 30
        need(remaining > 0, "No bounded time remains for the independent consumer")
        start_ns = time.time_ns()
        log = output / "consumer.log"
        result = lt.execute(consumer, consumer_command, log, min(1800, remaining), reserve_mib, env=consumer_env)
        end_ns = time.time_ns()
        record["executions"].append({"phase": phase, "command": consumer_command, "execution": result,
                                     "log_sha256": lt.sha256(log) if log.exists() else None})
        record["consumer_started_ns"], record["consumer_ended_ns"] = start_ns, end_ns
        # Preserve fresh XML outcomes even when tests fail. A failing build/report
        # never becomes a success; no counts are invented before complete review.
        phase = "fresh-independent-resolution-and-tests"
        resolution, resolution_review = fresh_resolution(consumer, staged, bindings, start_ns, end_ns)
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
        if staged is not None:
            try:
                observed_staging = staged_inputs(lt.safe_path(root, REPOSITORY))
                path = output / 'staging-after.json'
                if not path.exists():
                    write(path, observed_staging)
                else:
                    need(json_document(path) == observed_staging, "Final staging observations disagree")
                record['staging_inputs_held'] = observed_staging == staged
                need(record['staging_inputs_held'], "Staged package bytes changed during verification")
            except (OSError, ValueError, KeyError, TypeError):
                record['passed'] = False
                record['staging_inputs_held'] = False
                record.setdefault('error', {'phase': 'final-staging-capture', 'type': 'ConsumerEvidenceError',
                                            'contract': 'Unable to verify held final staged package bytes'})
        if copied is not None and consumer is not None:
            try:
                observed_copy = {path: lt.sha256(lt.safe_path(consumer, path)) for path in FIXTURE_FILES}
                write(output / 'fixture-copy-after.json', observed_copy)
                record['independent_fixture_inputs_held'] = observed_copy == copied
                need(record['independent_fixture_inputs_held'], "Independent copied fixture changed during verification")
            except (OSError, ValueError, KeyError, TypeError):
                record['passed'] = False
                record['independent_fixture_inputs_held'] = False
                record.setdefault('error', {'phase': 'final-independent-source-capture', 'type': 'ConsumerEvidenceError',
                                            'contract': 'Unable to verify held final independent fixture bytes'})
        if producer_home is not None:
            try:
                cache_after = producer_cache_state(root)
                write(output / 'producer-cache-after.json', cache_after)
                record['cache_containment']['candidate_payload_group_absent_after'] = cache_after['candidate_payload_group_absent']
                need(cache_after['candidate_payload_group_absent'], "Candidate group entered producer cache; do not export/save this cache")
            except (OSError, ValueError, KeyError, TypeError):
                record['passed'] = False
                record.setdefault('error', {'phase': 'producer-cache-containment', 'type': 'ConsumerEvidenceError',
                                            'contract': 'Unable to verify candidate-group absence in producer cache; no cache-export eligibility'})
        # Failures need the same held-input observation as successes. Do not
        # silently validate a failed command against only its pre-run snapshot.
        if before is not None:
            try:
                observed_after = inputs(root)
                after_path = output / "inputs-after.json"
                if not after_path.exists():
                    write(after_path, observed_after)
                else:
                    need(json_document(after_path) == observed_after, "Final input observations disagree")
                record["source_revision_after"] = lt.git_revision(root)
                record["source_input_count"] = len(before)
                record["inputs_before_sha256"] = lt.input_digest(before)
                record["inputs_after_sha256"] = lt.input_digest(observed_after)
                record["changed_inputs"] = sorted(p for p in set(before) | set(observed_after) if before.get(p) != observed_after.get(p))
                record["source_inputs_held"] = not record["changed_inputs"] and record["source_revision_after"] == record["source_revision"]
                if not record["source_inputs_held"]:
                    record["passed"] = False
                    record.setdefault("error", {"phase": "final-input-capture", "type": "ConsumerEvidenceError", "contract": "Source inputs changed during verification"})
            except (OSError, ValueError, KeyError, TypeError):
                record["passed"] = False
                record.setdefault("error", {"phase": "final-input-capture", "type": "ConsumerEvidenceError", "contract": "Unable to validate held final source inputs"})
        if lock_fd is not None:
            owned_stat = os.fstat(lock_fd)
            os.close(lock_fd)
            try:
                current_stat = lock.stat(follow_symlinks=False)
                need((owned_stat.st_dev, owned_stat.st_ino) == (current_stat.st_dev, current_stat.st_ino), "Refuse removing a replaced consumer lock")
                lock.unlink()
                record["owned_lock_removed"] = True
            except (OSError, ValueError):
                record["passed"] = False
                record["owned_lock_removed"] = False
                record.setdefault("error", {"phase": "owned-lock-cleanup", "type": "ConsumerEvidenceError", "contract": "Own lock cleanup failed; foreign/replaced locks are not deleted"})
        record.update(finished_utc=lt.utc_now(), elapsed_seconds=round(time.monotonic() - began, 3),
                      free_bytes_after=shutil.disk_usage(root).free)
        if not record['passed']:
            record['actual_consumer_methods_verified'] = 0  # keep fresh XML observations, not candidate certification
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
