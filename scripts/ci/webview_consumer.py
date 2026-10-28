#!/usr/bin/env python3
"""Fixed, independent packaged WebView consumers; no sample/source/native substitute.

Stages two local Maven publications once, then runs module-metadata and POM-only
consumers in separate uncached Gradle/HOME/tmp trees. Preserves stale staging and
failures. Bounded process groups are not an OS sandbox or release/dependency trust.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import sys
import time
import xml.etree.ElementTree as ET

import daemon_jvm
import failure_diagnostics
import library_tests as lt
import runtime_context

ROOT = Path(__file__).resolve().parents[2]
GROUP = "io.github.apdelrahman1911.nativecmpkit"
VERSION = "0.1.0-preview.1"
MODULE = "nativecmpkit-webview"
COORDINATES = {MODULE, MODULE + "-desktop"}
MODES = ("module", "pom")
FIXTURE = "tests/consumer/webview-desktop"
FILES = ("README.md", "settings.gradle.kts", "build.gradle.kts", "gradle.properties",
         "src/test/kotlin/nativecmpkit/consumer/PublishedWebViewConsumerTest.kt")
CLASS = "nativecmpkit.consumer.PublishedWebViewConsumerTest"
METHODS = {"loadedPublicClassesComeFromTheExactStagedJar", "publicComposableLoadsEvaluatesAndReleasesTheRealNativeView"}
CLASSPATHS = {"compileClasspath", "runtimeClasspath", "testCompileClasspath", "testRuntimeClasspath"}
FX_MODULES = {"base", "graphics", "controls", "media", "web", "swing"}
HOSTS = {
    "linux-x64": ("Linux", "x64", "linux"), "linux-arm64": ("Linux", "arm64", "linux-aarch64"),
    "macos-x64": ("Darwin", "x64", "mac"), "macos-arm64": ("Darwin", "arm64", "mac-aarch64"),
    "windows-x64": ("Windows", "x64", "win"),
}
CACHE = "build/ci-consumer-cache/webview-producer-gradle"
SCOPE = "PARTIAL WebView desktop Maven consumer; no full21-root/device/ABI/security/release certification"


class EvidenceError(ValueError):
    """Fixed contract messages only, never raw environment or exception text."""


def workflow_matrix(profile):
    slots = (
        {'host': 'linux-x64', 'runner': 'ubuntu-24.04', 'arch': 'x64', 'python': 'python3'},
        {'host': 'linux-arm64', 'runner': 'ubuntu-24.04-arm', 'arch': 'arm64', 'python': 'python3'},
        {'host': 'macos-arm64', 'runner': 'macos-26', 'arch': 'arm64', 'python': 'python3'},
        {'host': 'macos-x64', 'runner': 'macos-26-intel', 'arch': 'x64', 'python': 'python3'},
        {'host': 'windows-x64', 'runner': 'windows-2025', 'arch': 'x64', 'python': 'python'},
    )
    if profile == 'consumer-webview':
        return {'include': list(slots)}
    if profile in {'consumer-webview-' + host for host in HOSTS}:
        return {'include': [slot for slot in slots if profile == 'consumer-webview-' + slot['host']]}
    return {'include': []}


def need(condition, message):
    if not condition:
        raise EvidenceError(message)


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write("\n")


def read_json(path: Path):
    before = path.stat()
    need(path.is_file() and not path.is_symlink() and before.st_nlink == 1 and before.st_size <= 16 * 1024**2,
         "Expected bounded unshared JSON evidence")
    payload = path.read_bytes()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
         (path.stat().st_dev, path.stat().st_ino, path.stat().st_size, path.stat().st_mtime_ns, path.stat().st_ctime_ns),
         "JSON evidence changed during reading")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def finite(_):
        raise EvidenceError("Nonfinite JSON number")

    return json.loads(payload, object_pairs_hook=unique, parse_constant=finite)


def inputs(root: Path):
    result = lt.snapshot_inputs(root)
    paths = lt.source_files(root, FIXTURE)
    need({p.relative_to(root / FIXTURE).as_posix() for p in paths} == set(FILES), "Unexpected WebView consumer source inventory")
    for path in paths:
        need(path.stat().st_nlink == 1 and path.stat().st_size < 2 * 1024**2, "Unbounded or shared fixture input")
        result[path.relative_to(root).as_posix()] = lt.sha256(path)
    for name in ("tests/consumer/verify_artifacts.py", "docs/migration/identity.json", "LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"):
        result[name] = lt.sha256(lt.safe_path(root, name))
    for path in lt.source_files(root, "licenses"):
        result[path.relative_to(root).as_posix()] = lt.sha256(path)
    return dict(sorted(result.items()))


def cache_state(root: Path):
    cache = lt.safe_path(root, CACHE + "/caches/modules-2")
    candidates = ["files-2.1/" + GROUP]
    if cache.exists():
        entries = list(cache.iterdir())
        need(cache.is_dir() and len(entries) <= 256, "Unexpected producer cache inventory")
        candidates += [p.name + "/descriptors/" + GROUP for p in entries if re.fullmatch(r"metadata-[0-9]+(?:\.[0-9]+)+", p.name)]
    presence = {name: lt.safe_path(cache, name).exists() for name in candidates}
    return {"candidate_group_paths_present": presence, "candidate_group_absent": not any(presence.values()),
            "scope": "Known producer candidate payload/descriptor fence only; no ordinary dependency trust or OS sandbox"}


def environment(root: Path, output: Path, mode=None):
    jdk = os.environ.get("JAVA_HOME")
    launcher = "java.exe" if platform.system() == "Windows" else "java"
    need(jdk and Path(jdk).is_absolute() and (Path(jdk) / "bin" / launcher).is_file(), "Explicit installed JDK17 required")
    private = output / ("producer-private" if mode is None else mode + "-private")
    need(not private.exists(), "Private consumer HOME/tmp must be fresh")
    home, temporary = private / "home", private / "tmp"
    gradle = lt.safe_path(root, CACHE) if mode is None else private / "gradle"
    need(mode is None or not gradle.exists(), "Consumer Gradle home must be fresh and uncached")
    for path in (home, temporary, gradle):
        need(not any(char in str(path) for char in ('"', '\n', '\r')), "Unsafe JVM home argument")
        path.mkdir(parents=True, exist_ok=True)
    for name in ("init.d", "init.gradle", "init.gradle.kts", "gradle.properties"):
        need(not lt.safe_path(gradle, name).exists(), "Unreviewed private Gradle user configuration")
    value = {"JAVA_HOME": jdk, "PATH": str(Path(jdk) / "bin") + os.pathsep + os.environ.get("PATH", os.defpath),
             "HOME": str(home), "GRADLE_USER_HOME": str(gradle), "TMPDIR": str(temporary), "TEMP": str(temporary), "TMP": str(temporary),
             "XDG_CONFIG_HOME": str(home / ".config"), "XDG_CACHE_HOME": str(home / ".cache"), "TZ": "UTC",
             "JAVA_TOOL_OPTIONS": f'-Duser.home="{home}" -Djava.io.tmpdir="{temporary}"'}
    # Only public tool/display context, never tokens, repository credentials or user configuration.
    for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT", "CARGO_HOME", "RUSTUP_HOME", "DISPLAY", "XAUTHORITY",
                 "SystemRoot", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT"):
        if os.environ.get(name):
            value[name] = os.environ[name]
    return value


def diagnostics(root: Path, output: Path):
    """Finite public build-error excerpts only; never full child logs or test evidence."""
    base = lt.safe_path(root, 'build/ci-webview-consumer')
    need(output != base and output.is_relative_to(base) and output.is_dir(), "Confined WebView diagnostics required")
    logs = []
    for name in ('producer.log', 'module/consumer.log', 'pom/consumer.log'):
        path = lt.safe_path(root, (output / name).relative_to(root).as_posix())
        if not path.exists():
            continue
        before = path.stat()
        need(path.is_file() and before.st_nlink == 1, "Unshared regular diagnostic log required")
        if before.st_size > failure_diagnostics.MAX_LOG_BYTES:
            logs.append({'name': name, 'bytes': before.st_size, 'inspected': False,
                         'limit': 'Log exceeds bounded diagnostic input size'})
            continue
        payload = path.read_bytes()
        after = path.stat()
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Diagnostic log changed during readback')
        excerpts = failure_diagnostics.sections(payload.decode('utf-8', errors='replace').splitlines())
        logs.append({'name': name, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                     'inspected': True, 'excerpts': excerpts,
                     'excerpt_limit_may_omit_sections': len(excerpts) == failure_diagnostics.MAX_EXCERPTS})
    return {'schema_version': 1, 'recorded_utc': lt.utc_now(), 'logs': logs, 'test_success_inferred': False,
            'full_logs_uploaded': False, 'scope': 'Bounded reviewed public-fixture build errors only; not a general secret scrubber, test execution or release certification'}


def staged_inputs(repository: Path):
    need(repository.is_dir() and not repository.is_symlink(), "Missing fixed local staging repository")
    result, coordinates, total = {}, set(), 0
    prefix = tuple(GROUP.split('.'))
    for base, directories, files in os.walk(repository, followlinks=False):
        for name in sorted([*directories, *files]):
            path = lt.safe_path(repository, (Path(base) / name).relative_to(repository).as_posix())
            parts = path.relative_to(repository).parts
            need(parts[:min(len(parts), len(prefix))] == prefix[:min(len(parts), len(prefix))], "Foreign staged Maven group")
            before = path.stat(follow_symlinks=False)
            if len(parts) > len(prefix):
                need(parts[len(prefix)] in COORDINATES, "Unselected staged Maven coordinate")
                coordinates.add(parts[len(prefix)])
            if path.is_dir():
                continue
            need(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_nlink == 1, "Invalid staged file ownership/type")
            need((len(parts) == len(prefix) + 3 and parts[-2] == VERSION) or
                 (len(parts) == len(prefix) + 2 and re.fullmatch(r"maven-metadata\.xml(?:\.(?:md5|sha1|sha256|sha512))?", parts[-1])),
                 "Unexpected staged version/file layout")
            total += before.st_size
            need(total <= 256 * 1024**2 and len(result) < 1024, "Unbounded staged package inventory")
            digest = lt.sha256(path)
            after = path.stat()
            need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                 (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), "Staged file changed during hashing")
            result[path.relative_to(repository).as_posix()] = {"bytes": before.st_size, "sha256": digest}
    need(coordinates == COORDINATES and result, "Both actual WebView publications must be present")
    return dict(sorted(result.items()))


def selectors(repository: Path):
    """Compare dependencies only, not timestamps/file names or a host-specific blanket normalization."""
    result = {}
    for module in sorted(COORDINATES):
        directory = repository / GROUP.replace('.', '/') / module / VERSION
        base = module + '-' + VERSION
        pom = (directory / (base + '.pom')).read_bytes()
        need(len(pom) <= 2 * 1024**2, "Unbounded generated POM")
        xml = ET.fromstring(pom, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
        ns = {'p': 'http://maven.apache.org/POM/4.0.0'}
        rows = []
        for dependency in xml.findall('p:dependencies/p:dependency', ns):
            row = {key: dependency.findtext('p:' + key, default='', namespaces=ns)
                   for key in ('groupId', 'artifactId', 'version', 'classifier', 'type', 'scope', 'optional')}
            need(row['groupId'] != 'org.openjfx', "Producer-host JavaFX selector leaked into generated POM")
            rows.append(row)
        result[module + '.pom'] = sorted(rows, key=lambda r: json.dumps(r, sort_keys=True))
        metadata = read_json(directory / (base + '.module'))
        variants = metadata.get('variants')
        need(isinstance(variants, list) and 1 <= len(variants) <= 128, "Missing generated module variants")
        selected = []
        for variant in variants:
            need(isinstance(variant, dict) and isinstance(variant.get('name'), str), "Invalid generated module variant")
            dependencies = variant.get('dependencies', [])
            need(isinstance(dependencies, list), "Invalid generated dependency selectors")
            for dependency in dependencies:
                need(isinstance(dependency, dict) and dependency.get('group') != 'org.openjfx', "Producer-host JavaFX selector leaked into module metadata")
            selected.append({'variant': variant['name'], 'dependencies': dependencies})
        result[module + '.module'] = sorted(selected, key=lambda r: r['variant'])
    return result


def resolution_contract(document, staged, host, mode):
    need(mode in MODES and host in HOSTS, "Unsupported finite consumer mode/host")
    need(document.get('schema_version') == 2 and document.get('scope') == 'PARTIAL WebView desktop Maven consumer' and
         document.get('candidate_group') == GROUP and document.get('candidate_version') == VERSION and
         document.get('publication_roots_requested') == [MODULE] and document.get('metadata_mode') == mode and
         document.get('complete_21_root_KMP_matrix_requested') is False and document.get('release_readiness_certified') is False,
         "Consumer resolution scope/identity mismatch")
    rows = document.get('resolved_artifacts')
    need(isinstance(rows, list) and 1 <= len(rows) <= 4096, "Missing independent Maven resolution")
    seen = {name: set() for name in CLASSPATHS}
    fx = {name: set() for name in CLASSPATHS}
    identities = set()
    for row in rows:
        need(isinstance(row, dict) and row.get('configuration') in CLASSPATHS and all(isinstance(row.get(k), str) and row[k]
             for k in ('group', 'module', 'version', 'file', 'sha256')), "Invalid resolved Maven row")
        need(type(row.get('bytes')) is int and row['bytes'] > 0 and re.fullmatch(r'[0-9a-f]{64}', row['sha256']), "Invalid resolved artifact size/hash")
        need(row['group'] != 'com.mohamedrejeb.calf' and row['file'] == PurePosixPath(row['file']).name and '\\' not in row['file'], "Original/source/path substitute in consumer")
        identity = tuple(row[k] for k in ('configuration', 'group', 'module', 'version', 'file'))
        need(identity not in identities, "Duplicate consumer artifact row")
        identities.add(identity)
        if row['group'] == GROUP:
            target = MODULE + '-desktop'
            canonical = target + '-' + VERSION + '.jar'
            allowed_labels = {canonical, 'calf-webview-desktop-' + VERSION + '.jar'}
            need(row['module'] == target and row['version'] == VERSION and row.get('declared_file_name') in allowed_labels and
                 row.get('declared_file_url') == canonical and row.get('resolved_file_name') == row['file'] and
                 row['file'] == (row['declared_file_name'] if mode == 'module' else canonical), "Wrong candidate metadata/Maven-name binding")
            relative = GROUP.replace('.', '/') + '/' + target + '/' + VERSION + '/'
            need(row.get('staged_file') == relative + canonical and staged.get(row['staged_file']) == {'bytes': row['bytes'], 'sha256': row['sha256']},
                 "Resolved candidate bytes do not match exact held staged Maven bytes")
            need(row.get('metadata_file') == relative + target + '-' + VERSION + '.module' and
                 staged.get(row['metadata_file'], {}).get('sha256') == row.get('metadata_sha256'), "Wrong held module metadata hash")
            seen[row['configuration']].add(target)
        if row['group'] == 'org.openjfx':
            need(row['module'].startswith('javafx-') and row['module'][7:] in FX_MODULES and row['version'] == '21.0.13', "Misaligned/unknown JavaFX dependency")
            generic = row['module'] + '-21.0.13.jar'
            expected = row['module'] + '-21.0.13-' + HOSTS[host][2] + '.jar'
            need(row['file'] in (generic, expected), "Foreign-host JavaFX native classifier")
            if row['file'] == expected:
                fx[row['configuration']].add(row['module'][7:])
    need(all(value == {MODULE + '-desktop'} for value in seen.values()), "Packaged WebView must resolve on all four classpaths")
    need(all(value == FX_MODULES for value in fx.values()), "All six explicit consuming-host JavaFX classifiers must resolve")
    need(document.get('candidate_variants_resolved') == [MODULE + '-desktop'], "Incorrect candidate variant inventory")
    return {'classpath_count': 4, 'aligned_consuming_host_javafx_modules': sorted(FX_MODULES), 'native_classifier': HOSTS[host][2], 'resolved_rows': len(rows)}


def fresh_tests(consumer: Path, output: Path, mode: str, start: int, end: int, log: Path):
    lines = log.read_text(errors='replace').splitlines()
    expected = f'NATIVECMPKIT_WEBVIEW_CONSUMER_TEST task=:test gradle=9.7.1 java=17 mode={mode}'
    need(Counter(line for line in lines if line.startswith('NATIVECMPKIT_WEBVIEW_CONSUMER_TEST ')) == {expected: 1}, "Missing fresh actual Gradle9.7.1/JDK17 consumer test task")
    files = [p for p in lt.source_files(consumer, 'build/test-results/test') if p.name.startswith('TEST-') and p.suffix == '.xml']
    cases, reports = [], []
    for path in files:
        record = path.stat()
        need(record.st_nlink == 1 and start - 2_000_000_000 <= record.st_mtime_ns <= end + 2_000_000_000, "Stale/foreign consumer JUnit XML")
        payload = path.read_bytes()
        need((record.st_dev, record.st_ino, record.st_size, record.st_mtime_ns, record.st_ctime_ns) ==
             (path.stat().st_dev, path.stat().st_ino, path.stat().st_size, path.stat().st_mtime_ns, path.stat().st_ctime_ns), "JUnit evidence changed during capture")
        target = output / mode / 'junit' / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as saved:
            saved.write(payload)
        parsed = lt.junit_cases(payload)
        cases += parsed
        reports.append({'path': target.relative_to(output).as_posix(), 'sha256': hashlib.sha256(payload).hexdigest(), **lt.case_counts(parsed)})
    observation = {'reports': reports, 'testcases': cases, 'totals': lt.case_counts(cases), 'metadata_mode': mode}
    write(output / mode / 'test-outcomes.json', observation)
    need(len(files) == 1 and {(c['classname'], c['name']) for c in cases} == {(CLASS, method) for method in METHODS} and len(cases) == 2,
         "Exactly both consumer methods must execute; no missing/extra/duplicate cases")
    need(observation['totals']['passed'] == observation['totals']['executed'] == 2 and not any(observation['totals'][k] for k in ('failures', 'errors', 'skipped')),
         "Both actual native consumer methods must pass without skips")
    return observation


def commands(root: Path, consumer: Path | None, mode=None):
    wrapper = root / ('gradlew.bat' if os.name == 'nt' else 'gradlew')
    base = [str(wrapper), '--no-daemon', '--no-parallel', '--no-configuration-cache', '--no-build-cache', '--console=plain', '--max-workers=2',
            '--dependency-verification', 'strict', '-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8', '-Pkotlin.compiler.execution.strategy=in-process',
            '--init-script', str(root / ('scripts/ci/daemon-jvm.init.gradle.kts' if consumer is None else 'scripts/ci/webview-consumer-daemon.init.gradle.kts'))]
    if consumer is None:
        return [*base, '-Dnativecmpkit.webviewStagingRoot=' + str(root), '--init-script', str(root / 'scripts/ci/stage-webview.init.gradle.kts'),
                '-PnativecmpkitVerification=true', '-PnativecmpkitVerificationTargets=desktop', '-PnativeCmpkit.version=' + VERSION,
                'stageWebViewVerificationPublications']
    need(mode in MODES, "Only module/POM consumer commands allowed")
    return [*base, '-p', str(consumer), '-PnativecmpkitRepository=' + str(root / 'build/verification-repo'), '-PnativecmpkitVersion=' + VERSION,
            '-PnativecmpkitMetadataMode=' + mode, 'verifyCandidateResolution', 'test']


def run(root: Path, relative: str, host: str, timeout=4200):
    need(host in HOSTS and 600 <= timeout <= 4800, "Finite actual host and bounded timeout required")
    output = lt.safe_path(root, relative)
    base = lt.safe_path(root, 'build/ci-webview-consumer')
    need(output != base and output.is_relative_to(base) and not output.exists(), "Fresh confined WebView consumer output required")
    output.mkdir(parents=True)
    record = {'schema_version': 1, 'scope': SCOPE, 'passed': False, 'source_revision': lt.git_revision(root), 'host': host,
              'candidate_group': GROUP, 'candidate_version': VERSION, 'metadata_modes_requested': list(MODES), 'started_utc': lt.utc_now(),
              'packages_published': False, 'release_created': False, 'release_readiness_certified': False, 'ordinary_dependency_trust_certified': False,
              'process_cleanup_scope': 'Owned bounded process groups only; not detached-process/OS sandbox attestation', 'executions': [], 'modes': {}}
    began, phase, before, staged = time.monotonic(), 'preflight', None, None
    copies = {}
    repository = root / 'build/verification-repo'
    lock = base / '.webview-consumer.lock'
    lock_fd = None
    try:
        lock_fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        need(shutil.disk_usage(root).free >= 8192 * 1024**2, "8GiB reserve unavailable; no build started")
        runtime = runtime_context.capture(expected_arch=HOSTS[host][1], android_package='android-37.0', require_clean=True)
        need(runtime['host']['system'] == HOSTS[host][0] and runtime['source_revision'] == record['source_revision'], "Actual host/source mismatch")
        write(output / 'runtime-before.json', runtime)
        before = inputs(root)
        write(output / 'inputs-before.json', before)
        need(not repository.exists() and not repository.is_symlink(), "Refuse stale staging; preserve old artifacts")
        cache = cache_state(root)
        write(output / 'producer-cache-before.json', cache)
        need(cache['candidate_group_absent'], "Candidate in producer cache; no build/export allowed")
        phase = 'actual-local-producer-staging'
        producer_log = output / 'producer.log'
        command = commands(root, None)
        result = lt.execute(root, command, producer_log, min(2400, timeout - 120), 8192, env=environment(root, output))
        record['executions'].append({'phase': phase, 'command': command, 'execution': result, 'log_sha256': lt.sha256(producer_log)})
        need(result['exit_code'] == 0 and not result.get('stop_reason'), "Actual two-publication staging failed")
        record['producer_daemon'] = daemon_jvm.observation(producer_log)
        markers = re.findall(r'(?m)^NATIVECMPKIT_WEBVIEW_STAGE task=(\S+) group=' + re.escape(GROUP) + r' version=' + re.escape(VERSION) + '$', producer_log.read_text(errors='replace'))
        expected = {':calf-webview:publish' + name + 'PublicationToNativecmpkitVerificationRepository' for name in ('KotlinMultiplatform', 'Desktop')}
        need(len(markers) == 2 and set(markers) == expected, "Exactly two actual WebView staging task markers required")
        record['actual_publication_tasks'] = sorted(markers)
        staged = staged_inputs(repository)
        write(output / 'staging-before.json', staged)
        phase = 'static-package-and-selector-inspection'
        sys.path.insert(0, str(root / 'tests/consumer'))
        import verify_artifacts
        static_report = verify_artifacts.ArtifactVerifier(root, repository, VERSION, [MODULE], ['desktop'], [host]).run()
        write(output / 'static-packages.json', static_report)
        need(static_report.get('success') is True and static_report.get('modules') == [MODULE] and static_report.get('targets') == ['metadata', 'desktop'] and
             static_report.get('release_readiness_certified') is False, "Actual WebView package inspection failed")
        write(output / 'dependency-selectors.json', selectors(repository))
        for mode in MODES:
            phase = 'independent-consumer-' + mode
            consumer = output / mode / 'independent-consumer'
            consumer.mkdir(parents=True)
            copied = {}
            for name in FILES:
                source, target = root / FIXTURE / name, consumer / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as saved:
                    saved.write(source.read_bytes())
                copied[name] = lt.sha256(target)
                need(copied[name] == before[FIXTURE + '/' + name], "Independent consumer copy differs from held source")
            copies[mode] = (consumer, copied)
            write(output / mode / 'fixture-copy.json', copied)
            command = commands(root, consumer, mode)
            log = output / mode / 'consumer.log'
            remaining = timeout - int(time.monotonic() - began) - 30
            need(remaining > 0, "No bounded time remains for consumer")
            start = time.time_ns()
            result = lt.execute(consumer, command, log, min(1500, remaining), 8192, env=environment(root, output, mode))
            end = time.time_ns()
            record['executions'].append({'phase': phase, 'command': command, 'execution': result, 'log_sha256': lt.sha256(log)})
            record['modes'][mode] = {'gradle_daemon': daemon_jvm.observation(log)}
            # Preserve actual failed test XML before resolution/build acceptance.
            record['modes'][mode]['tests'] = fresh_tests(consumer, output, mode, start, end, log)
            resolution = consumer / 'build/reports/webview-consumer-resolution.json'
            need(start - 2_000_000_000 <= resolution.stat().st_mtime_ns <= end + 2_000_000_000, "Stale independent resolution")
            document = read_json(resolution)
            write(output / mode / 'resolution.json', document)
            record['modes'][mode]['resolution'] = resolution_contract(document, staged, host, mode)
            need(result['exit_code'] == 0 and not result.get('stop_reason'), "Actual independent consumer build failed")
        runtime_after = runtime_context.capture(expected_arch=HOSTS[host][1], android_package='android-37.0', require_clean=True)
        write(output / 'runtime-after.json', runtime_after)
        need(all(runtime_after.get(k) == runtime.get(k) for k in ('source_revision', 'source_tree_dirty', 'host', 'java', 'rust', 'android_platform', 'compiler_runtime_fingerprint')), 'Actual runtime/source identity changed during consumption')
        record['passed'] = True
    except (EvidenceError, OSError, ValueError, KeyError, TypeError) as failure:
        record['error'] = {'phase': phase, 'type': type(failure).__name__, 'contract': str(failure) if isinstance(failure, EvidenceError)
                           else 'Verification phase failed; inspect owned public-fixture logs'}
    finally:
        checks = []
        if before is not None:
            try:
                after = inputs(root)
                write(output / 'inputs-after.json', after)
                held = before == after and lt.git_revision(root) == record['source_revision']
                record.update(source_input_count=len(before), source_inputs_held=held, inputs_before_sha256=lt.input_digest(before), inputs_after_sha256=lt.input_digest(after))
                checks.append(held)
            except (OSError, ValueError):
                checks.append(False)
        if staged is not None:
            try:
                after_staged = staged_inputs(repository)
                write(output / 'staging-after.json', after_staged)
                record['staged_package_inputs_held'] = staged == after_staged
                checks.append(record['staged_package_inputs_held'])
            except (OSError, ValueError):
                checks.append(False)
        for mode, (consumer, copied) in copies.items():
            try:
                after_copy = {name: lt.sha256(consumer / name) for name in FILES}
                write(output / mode / 'fixture-copy-after.json', after_copy)
                checks.append(copied == after_copy)
            except (OSError, ValueError):
                checks.append(False)
        try:
            cache = cache_state(root)
            write(output / 'producer-cache-after.json', cache)
            checks.append(cache['candidate_group_absent'])
        except (OSError, ValueError):
            checks.append(False)
        if lock_fd is not None:
            owned = os.fstat(lock_fd)
            os.close(lock_fd)
            try:
                current = lock.stat(follow_symlinks=False)
                need((owned.st_dev, owned.st_ino) == (current.st_dev, current.st_ino), "Replaced consumer lock not deleted")
                lock.unlink()
                record['owned_lock_removed'] = True
            except (OSError, ValueError):
                record['owned_lock_removed'] = False
                checks.append(False)
        record['passed'] = record['passed'] and all(checks)
        if not all(checks):
            record.setdefault('error', {'phase': 'held-input-cache-cleanup-review', 'contract': 'Final held-input/cache/ownership check failed'})
        record.update(finished_utc=lt.utc_now(), elapsed_seconds=round(time.monotonic() - began, 3), free_bytes_after=shutil.disk_usage(root).free)
        if not record['passed']:
            try:
                write(output / 'failure-diagnostics.json', diagnostics(root, output))
            except (OSError, ValueError):
                record['diagnostics_capture_refused'] = True
        write(output / 'receipt.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=tuple(HOSTS), required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout', type=int, default=4200)
    args = parser.parse_args()
    result = run(ROOT, args.output, args.host, args.timeout)
    print(json.dumps({key: result[key] for key in ('passed', 'scope', 'host', 'error') if key in result}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
