#!/usr/bin/env python3
"""One NEW real AWT peer-generation method through standard verified resources.

No custom Java/JNI/Rust host, modal, old JNI replay, publication or fallback.
Owned process/capture/cleanup and the immutable600s budget are delegated intact
to picker_jni_actual_jvm2. Raw logs and command receipts stay under private/.
Only five named JSON files are public. This is not a trusted-builder sandbox,
Main Thread Checker, actual panel-open or CFRelease-completion certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tomllib
import zipfile

import picker_jni_actual_jvm2 as shared
import picker_awt_prepare_failure as prepare_diagnostics

# The checked-in, side-effect-free native validator; never a downloaded helper.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
import artifacts

library = shared.library
Refusal = shared.Refusal
FOCUS = "picker-awt-generation"
MODULE = "calf-file-picker"
PLATFORM = "macos-arm64"
CLASS = "com.mohamedrejeb.calf.picker.platform.NativeMacOsParentLeaseGenerationTest"
METHOD = "actualAwtPeerReplacementRejectsOldOwnedLeaseBeforeAnyModal"
TEST_SOURCE = "calf-file-picker/src/desktopTest/kotlin/" + CLASS.replace(".", "/") + ".kt"
TEST_RESOURCE = CLASS.replace(".", "/") + ".class"
BRIDGE_RESOURCE = "com/mohamedrejeb/calf/picker/platform/NativeFilePickerBridge.class"
NATIVE_RESOURCE = "native/macos-arm64/libcalf_filepicker_native.dylib"
MANIFEST_RESOURCE = "META-INF/nativecmpkit/native/calf-file-picker/macos-arm64.json"
REQUIRED_RESOURCES = (TEST_RESOURCE, BRIDGE_RESOURCE, NATIVE_RESOURCE, MANIFEST_RESOURCE)
SUCCESS_MARKER = ("NATIVECMPKIT_AWT_GENERATION807 old_refused=true new_scope_returned=true "
                  "registry_and_awt_cleanup_returned=true")
PUBLIC_FILES = ("receipt.json", "inputs-before.json", "inputs-after.json", "runtime-before.json", "runtime-after.json")
MAX_TEXT_BYTES = 128 * 1024
MAX_CLASSPATH_ENTRIES = 256
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_FILES = 50000
MAX_JAR_MEMBERS = 100000
MAX_RESOURCE_BYTES = {TEST_RESOURCE: 1024 * 1024, BRIDGE_RESOURCE: 1024 * 1024,
                      NATIVE_RESOURCE: MAX_FILE_BYTES, MANIFEST_RESOURCE: 1024 * 1024}
GRADLE_STARTUP_ENV = Path("/usr/bin/env")
STANDARD_GRADLE_JVM_ARGS = "-Xmx2048m -Dfile.encoding=UTF-8"
STANDARD_KOTLIN_DAEMON_JVM_ARGS = "-Xmx1536m"
JDK_FILES = ("release", "bin/java", "bin/javap", "lib/modules", "lib/server/libjvm.dylib",
             "lib/libjava.dylib", "lib/libjli.dylib", "lib/libawt.dylib", "lib/libawt_lwawt.dylib")
OWNING_INPUTS = ("scripts/ci/picker_awt_generation.py", "scripts/ci/test_picker_awt_generation.py",
                 "scripts/native/artifacts.py", "convention-plugins/src/main/kotlin/NativeLibraries.kt",
                 "calf-file-picker/build.gradle.kts", "gradle/libs.versions.toml", TEST_SOURCE,
                 "scripts/ci/picker_awt_prepare_failure.py")
PREPARE_TASKS = (":calf-file-picker:desktopProcessResources",
                 ":calf-file-picker:writeNativeTestRuntimeClasspath", ":calf-file-picker:verifyNativeResources")
FRESH_OUTPUTS = ("calf-file-picker/build/native-host", "calf-file-picker/build/native-libs",
                 "calf-file-picker/build/rust", "calf-file-picker/build/native-boundary-runtime/classpath.txt")
SCOPE = ("Exactly one real supported Temurin JDK17/macOS arm64 AWT Window peer replacement before any modal. "
         "Actual production RetainAction/owned parent and returned mismatched-kind NSView scopes; old generation "
         "refused, new scope returned, both recorded registry closes and owned AWT disposal returned. "
         "No Main Thread Checker loading/calibration, panel-open replacement/cancellation, CFRelease completion/balance, "
         "global-ref/VM shutdown, non-macOS/vendor parity, accepted JNI2 replay, whole#58, consumer or release proof.")


def reject_overrides(environment: dict) -> None:
    names = {"JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "JAVA_OPTS", "GRADLE_OPTS", "CLASSPATH",
             "GRADLE_USER_HOME", "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC", "RUSTC_WRAPPER",
             "RUSTC_WORKSPACE_WRAPPER", "CARGO_BUILD_TARGET", "CARGO_TARGET_DIR", "RUSTC_BOOTSTRAP",
             "CFLAGS", "CXXFLAGS", "LDFLAGS"}
    names.update(name for name in environment if name.startswith(("DYLD_", "LD_", "ORG_GRADLE_PROJECT_", "CARGO_PROFILE_"))
                 or (name.startswith("CARGO_TARGET_") and name.endswith(("_RUSTFLAGS", "_LINKER"))))
    if any(environment.get(name) for name in names):
        raise Refusal("inherited-jvm-gradle-native-or-loader-overrides-refused")
    if environment.get("RUSTUP_TOOLCHAIN") not in (None, "", "1.98.0"):
        raise Refusal("inherited-rust-toolchain-override-refused")


def clean_absolute(path: Path) -> Path:
    text = path.as_posix()
    if (not path.is_absolute() or len(text) > 4096 or any(ord(char) < 32 for char in text) or
            "\\" in text or ":" in text or any(part in {".", ".."} for part in path.parts) or
            any(item.is_symlink() for item in (path, *path.parents)) or path.resolve() != path):
        raise Refusal("absolute-canonical-nonsymlink-path-required")
    return path


def _stat9(shape) -> list:
    return [shape.st_dev, shape.st_ino, shape.st_mode, shape.st_nlink, shape.st_uid, shape.st_gid,
            shape.st_size, shape.st_mtime_ns, shape.st_ctime_ns]


def held_file(path: Path, budget, *, limits=None, maximum=MAX_FILE_BYTES, collect=False, allow_empty=False,
              directory_fd=None, name=None, inspect=None) -> tuple[dict, bytes | None, dict]:
    """Hash through one held regular FD; parent-relative reads never follow links."""
    budget.remaining()
    if directory_fd is None:
        clean_absolute(path)
    selected = name if directory_fd is not None else path
    options = {} if directory_fd is None else {"dir_fd": directory_fd}
    with os.fdopen(os.open(selected, os.O_RDONLY | os.O_NOFOLLOW, **options), "rb") as stream:
        shape = os.fstat(stream.fileno())
        if (not stat.S_ISREG(shape.st_mode) or shape.st_nlink != 1 or
                not (0 if allow_empty else 1) <= shape.st_size <= maximum):
            raise Refusal("regular-single-link-nonempty-bounded-file-required")
        if limits is not None:
            limits[0] += 1
            limits[1] += shape.st_size
            if limits[0] > MAX_FILES or limits[1] > MAX_TOTAL_BYTES:
                raise Refusal("classpath-file-count-or-aggregate-byte-limit")
        digest, chunks, size = hashlib.sha256(), [], 0
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            budget.remaining()
            size += len(chunk)
            if size > maximum or size > shape.st_size:
                raise Refusal("held-file-grew-during-capture")
            digest.update(chunk)
            if collect:
                chunks.append(chunk)
        inspected = inspect(stream) if inspect is not None else {}
        final = os.stat(selected, follow_symlinks=False, **options)
        if size != shape.st_size or _stat9(shape) != _stat9(os.fstat(stream.fileno())) or _stat9(shape) != _stat9(final):
            raise Refusal("held-file-descriptor-path-or-payload-changed")
    budget.remaining()
    return {"sha256": digest.hexdigest(), "size": size, "stat9": _stat9(shape)}, b"".join(chunks) if collect else None, inspected


def default_version(root: Path, budget) -> str:
    texts = {}
    for name in ("build.gradle.kts", "gradle.properties", "gradle/libs.versions.toml"):
        _, body, _ = held_file(root / name, budget, maximum=MAX_TEXT_BYTES, collect=True)
        texts[name] = body.decode("utf-8")
    declaration = ('val nativeCmpkitVersion = providers.gradleProperty("nativeCmpkit.version")\n'
                   '    .orElse("${libs.versions.nativecmpkit.get()}-SNAPSHOT")')
    if texts["build.gradle.kts"].count(declaration) != 1 or re.search(
            r"(?m)^\s*(?:nativeCmpkit\.version|nativecmpkitNativePrebuiltDir|nativecmpkitNativeMode|nativecmpkitPython)\s*[=:]",
            texts["gradle.properties"]):
        raise Refusal("source-default-version-or-native-property-contract-refused")
    if (re.findall(r"(?m)^org\.gradle\.jvmargs=([^\r\n]+)$", texts["gradle.properties"]) != [STANDARD_GRADLE_JVM_ARGS] or
            re.findall(r"(?m)^kotlin\.daemon\.jvmargs=([^\r\n]+)$", texts["gradle.properties"]) != [STANDARD_KOTLIN_DAEMON_JVM_ARGS]):
        raise Refusal("source-standard-gradle-and-kotlin-daemon-jvm-args-refused")
    versions = tomllib.loads(texts["gradle/libs.versions.toml"])["versions"]
    if versions.get("java") != "17" or versions.get("junit") != "4.13.2":
        raise Refusal("source-jdk-or-junit-version-contract-refused")
    version = versions.get("nativecmpkit")
    if not isinstance(version, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
        raise Refusal("source-default-version-format-refused")
    return version + "-SNAPSHOT"


def qualify_jdk(context: dict, budget) -> tuple[Path, dict]:
    reject_overrides(dict(os.environ))
    if not os.environ.get("JAVA_HOME"):
        raise Refusal("explicit-qualified-java-home-required")
    home = clean_absolute(Path(os.environ["JAVA_HOME"]))
    if shutil.which("java") != (home / "bin/java").as_posix():
        raise Refusal("path-java-is-not-the-qualified-java-home-binary")
    files, release = {}, None
    for name in JDK_FILES:
        files[name], payload, _ = held_file(home / name, budget, maximum=MAX_TEXT_BYTES if name == "release" else MAX_FILE_BYTES,
                                          collect=name == "release")
        if name in {"bin/java", "bin/javap"} and not files[name]["stat9"][2] & 0o111:
            raise Refusal("qualified-java-tool-is-not-executable")
        if name == "release":
            release = payload.decode("utf-8")
    versions = re.findall(r'^JAVA_VERSION="([^"\r\n]+)"$', release, re.MULTILINE)
    suppliers = re.findall(r'^IMPLEMENTOR="([^"\r\n]+)"$', release, re.MULTILINE)
    if versions != [context["java"]["version"]] or suppliers != ["Eclipse Adoptium"]:
        raise Refusal("qualified-temurin-release-and-captured-jdk-version-mismatch")
    startup_env, _, _ = held_file(GRADLE_STARTUP_ENV, budget)
    if not startup_env["stat9"][2] & 0o111:
        raise Refusal("qualified-gradle-startup-env-is-not-executable")
    return home, {"supplier": "Eclipse Adoptium", "java_version": versions[0], "selected_runtime_files": files,
                  "gradle_startup_env": startup_env}


def inspect_jar(stream, budget) -> dict:
    stream.seek(0)
    resources = {}
    try:
        with zipfile.ZipFile(stream) as archive:
            members = archive.infolist()
            if len(members) > MAX_JAR_MEMBERS:
                raise Refusal("classpath-jar-member-limit")
            seen = set()
            for member in members:
                budget.remaining()
                name = member.filename
                path = PurePosixPath(name)
                if (name in seen or not name or path.is_absolute() or "\\" in name or
                        any(ord(char) < 32 for char in name) or any(part in {".", ".."} for part in path.parts) or
                        name.rstrip("/") != path.as_posix() or stat.S_ISLNK(member.external_attr >> 16)):
                    raise Refusal("classpath-jar-duplicate-traversal-or-symlink-member")
                seen.add(name)
                if any(re.fullmatch(r"META-INF/versions/[0-9]+/" + re.escape(resource), name) for resource in REQUIRED_RESOURCES):
                    raise Refusal("versioned-required-class-or-native-origin-refused")
                if name not in REQUIRED_RESOURCES and name != "META-INF/MANIFEST.MF":
                    continue
                maximum = MAX_TEXT_BYTES if name == "META-INF/MANIFEST.MF" else MAX_RESOURCE_BYTES[name]
                if not 0 < member.file_size <= maximum or member.flag_bits & 1:
                    raise Refusal("bounded-unencrypted-classpath-resource-required")
                digest, size, chunks = hashlib.sha256(), 0, []
                with archive.open(member) as body:
                    for chunk in iter(lambda: body.read(64 * 1024), b""):
                        budget.remaining()
                        size += len(chunk)
                        if size > maximum or size > member.file_size:
                            raise Refusal("classpath-resource-expanded-size-refused")
                        digest.update(chunk)
                        if name == "META-INF/MANIFEST.MF":
                            chunks.append(chunk)
                if size != member.file_size:
                    raise Refusal("classpath-resource-size-mismatch")
                if name == "META-INF/MANIFEST.MF":
                    if re.search(rb"(?im)^Class-Path\s*:", b"".join(chunks)):
                        raise Refusal("jar-manifest-hidden-classpath-refused")
                else:
                    resources[name] = {"sha256": digest.hexdigest(), "size": size}
    except (OSError, RuntimeError, zipfile.BadZipFile, UnicodeError) as error:
        raise Refusal("classpath-jar-inspection-refused") from error
    return resources


def directory_identity(path: Path, budget, limits) -> tuple[dict, dict]:
    files, directories, resources = {}, {}, {}

    def visit(folder: Path, relative: str, *, parent_fd=None, name=None):
        budget.remaining()
        if len(directories) >= MAX_FILES or len(PurePosixPath(relative).parts) > 64:
            raise Refusal("classpath-directory-count-or-depth-limit")
        options = {} if parent_fd is None else {"dir_fd": parent_fd}
        selected = folder if parent_fd is None else name
        descriptor = os.open(selected, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, **options)
        try:
            shape = os.fstat(descriptor)
            if not stat.S_ISDIR(shape.st_mode):
                raise Refusal("classpath-directory-descriptor-required")
            directories[relative] = _stat9(shape)
            children = []
            with os.scandir(descriptor) as scan:
                for child in scan:
                    budget.remaining()
                    children.append(child.name)
                    if len(children) > MAX_FILES:
                        raise Refusal("classpath-directory-child-count-limit")
            for child in sorted(children):
                if not child or child in {".", ".."} or any(ord(char) < 32 for char in child) or "\\" in child:
                    raise Refusal("classpath-directory-child-name-refused")
                key = f"{relative}/{child}" if relative else child
                state = os.stat(child, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISDIR(state.st_mode):
                    visit(folder / child, key, parent_fd=descriptor, name=child)
                elif stat.S_ISREG(state.st_mode):
                    files[key], _, _ = held_file(folder / child, budget, limits=limits, allow_empty=True,
                                               directory_fd=descriptor, name=child)
                    if key in REQUIRED_RESOURCES:
                        if not 0 < files[key]["size"] <= MAX_RESOURCE_BYTES[key]:
                            raise Refusal("bounded-classpath-resource-required")
                        resources[key] = {field: files[key][field] for field in ("sha256", "size")}
                else:
                    raise Refusal("classpath-directory-symlink-or-special-file-refused")
            if _stat9(shape) != _stat9(os.fstat(descriptor)) or _stat9(shape) != _stat9(os.stat(selected, follow_symlinks=False, **options)):
                raise Refusal("classpath-directory-changed-during-capture")
        finally:
            os.close(descriptor)

    visit(path, "")
    return {"files": files, "directories": directories}, resources


def classpath_identity(root: Path, budget) -> tuple[str, dict]:
    identity, payload, _ = held_file(root / "calf-file-picker/build/native-boundary-runtime/classpath.txt", budget,
                                   maximum=MAX_TEXT_BYTES, collect=True)
    text = payload.decode("utf-8")
    lines = text.splitlines()
    if (text != "\n".join(lines) + "\n" or not 1 <= len(lines) <= MAX_CLASSPATH_ENTRIES or
            len(set(lines)) != len(lines)):
        raise Refusal("fresh-bounded-unique-ordered-classpath-required")
    entries, limits, physical, origins = [], [0, 0], set(), {resource: [] for resource in REQUIRED_RESOURCES}
    for index, line in enumerate(lines):
        if not line or line != Path(line).as_posix():
            raise Refusal("canonical-classpath-entry-text-required")
        path = clean_absolute(Path(line))
        if path == root or not path.is_relative_to(root) or "build" not in path.relative_to(root).parts:
            raise Refusal("classpath-entry-outside-owned-build-domain")
        shape = path.lstat()
        key = (shape.st_dev, shape.st_ino)
        if key in physical:
            raise Refusal("duplicate-physical-classpath-entry")
        physical.add(key)
        if stat.S_ISDIR(shape.st_mode):
            content, resources = directory_identity(path, budget, limits)
            kind = "directory"
        elif stat.S_ISREG(shape.st_mode) and path.suffix == ".jar":
            content, _, resources = held_file(path, budget, limits=limits, inspect=lambda stream: inspect_jar(stream, budget))
            kind = "jar"
        else:
            raise Refusal("classpath-entry-is-not-an-owned-directory-or-jar")
        entries.append({"index": index, "path": path.relative_to(root).as_posix(), "kind": kind, "content": content})
        for resource, content in resources.items():
            origins[resource].append({"entry_index": index, **content})
    if any(len(found) != 1 for found in origins.values()):
        raise Refusal("exactly-one-compiled-class-bridge-native-and-manifest-origin-required")
    budget.remaining()
    return os.pathsep.join(lines), {"classpath_file": identity, "ordered_entries": entries,
                                   "file_count": limits[0], "total_bytes": limits[1], "resources": origins}


def native_identity(root: Path, revision: str, version: str, budget) -> dict:
    staged = clean_absolute(root / "calf-file-picker/build/native-libs")
    files = {}
    for name in (NATIVE_RESOURCE, MANIFEST_RESOURCE):
        files[name], _, _ = held_file(staged / name, budget, maximum=MAX_RESOURCE_BYTES[name])
    try:
        records = artifacts.validate_bundle(root, MODULE, staged, [PLATFORM], require_clean=True,
                                            expected_revision=revision, expected_version=version)
    except Exception as error:
        raise Refusal("strict-current-host-native-bundle-validation-refused") from error
    for name in files:
        if held_file(staged / name, budget, maximum=MAX_RESOURCE_BYTES[name])[0] != files[name]:
            raise Refusal("validated-native-stage-changed-during-review")
    budget.remaining()
    record = records[0]
    return {"platform": PLATFORM, "library_version": record["libraryVersion"], "abi_version": record["abiVersion"],
            "source_revision": record["sourceRevision"], "source_sha256": record["sourceSha256"], "files": files}


def require_bundled_identity(classpath: dict, native: dict) -> None:
    for name in (NATIVE_RESOURCE, MANIFEST_RESOURCE):
        origin = classpath["resources"][name]
        if len(origin) != 1 or any(origin[0][key] != native["files"][name][key] for key in ("sha256", "size")):
            raise Refusal("runtime-bundled-native-or-manifest-differs-from-validated-stage")


def _private_domain(root: Path, private: Path) -> None:
    clean_absolute(root)
    clean_absolute(private)
    if not private.is_relative_to(root):
        raise Refusal("exact-owned-private-jvm-directory-domain-required")
    parts = private.relative_to(root).parts
    if (len(parts) != 4 or parts[:2] != ("build", "ci-verification") or parts[3] != "private" or
            not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", parts[2]) or
            not re.fullmatch(r"/[A-Za-z0-9_./-]+", private.as_posix())):
        raise Refusal("exact-owned-private-jvm-directory-domain-required")


def _directory_key(shape) -> list:
    # Creating native cache/tmp children legitimately changes times/link count.
    # Keep inode identity/owner/mode instead, with the original inode held open.
    if not stat.S_ISDIR(shape.st_mode) or stat.S_IMODE(shape.st_mode) != 0o700 or shape.st_uid != os.geteuid():
        raise Refusal("owned-jvm-directory-must-be-current-owner-only-0700")
    return [shape.st_dev, shape.st_ino, shape.st_mode, shape.st_uid, shape.st_gid]


class OwnedJavaDirectories:
    """Exact fresh private Java paths; retained no-follow FDs across all phases.

    No content freeze, deletion, permission repair or filesystem sandbox claim.
    Native cache lookup is user.home/.cache/nativecmpkit-filepicker; its owner
    probe and any private fallback use java.io.tmpdir. Both paths are owned.
    """
    LAYOUT = (("home", "java-home", "private"), ("tmp", "java-tmp", "private"),
              ("gradle", "gradle-home", "private"), ("cache_parent", ".cache", "home"),
              ("native_cache", "nativecmpkit-filepicker", "cache_parent"))

    def __init__(self, root: Path, private: Path, budget):
        _private_domain(root, private)
        self.root, self.private, self.budget = root, private, budget
        self.descriptors, self.entries = {}, {}
        try:
            self._add("output", private.parent)
            self._add("private", private, parent="output", name="private")
            for key, name, parent in self.LAYOUT:
                self._add(key, self.entries[parent]["path"] / name, parent=parent, name=name, create=True)
            self.require()
        except Exception as primary:
            try:
                self.close()
            except Exception:
                primary.add_note("owned-jvm-descriptor-cleanup-unestablished")
            raise

    def _add(self, key: str, path: Path, *, parent=None, name=None, create=False) -> None:
        self.budget.remaining()
        options = {} if parent is None else {"dir_fd": self.descriptors[parent]}
        selected = path if parent is None else name
        if create:
            try:
                os.mkdir(selected, mode=0o700, **options)
            except OSError as error:
                raise Refusal("fresh-owned-jvm-directory-required-no-repair-or-fallback") from error
        descriptor = os.open(selected, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, **options)
        self.descriptors[key] = descriptor
        self.entries[key] = {"path": path, "parent": parent, "name": name,
                             "stat5": _directory_key(os.fstat(descriptor))}

    def require(self) -> None:
        _private_domain(self.root, self.private)
        for key, entry in self.entries.items():
            self.budget.remaining()
            options = {} if entry["parent"] is None else {"dir_fd": self.descriptors[entry["parent"]]}
            selected = entry["path"] if entry["parent"] is None else entry["name"]
            if (_directory_key(os.fstat(self.descriptors[key])) != entry["stat5"] or
                    _directory_key(os.stat(selected, follow_symlinks=False, **options)) != entry["stat5"]):
                raise Refusal("owned-jvm-directory-fd-path-or-owner-custody-changed")

    def identity(self) -> dict:
        return {key: {"path": entry["path"].relative_to(self.root).as_posix(), "stat5": list(entry["stat5"])}
                for key, entry in self.entries.items()}

    def close(self) -> None:
        first = None
        for key in reversed(tuple(self.descriptors)):
            try:
                os.close(self.descriptors.pop(key))
            except OSError as error:
                if first is None:
                    first = error
        if first is not None:
            raise Refusal("owned-jvm-descriptor-cleanup-unestablished") from first


def _jvm_properties(root: Path, private: Path) -> list[str]:
    _private_domain(root, private)
    return ["-Duser.home=" + (private / "java-home").as_posix(),
            "-Djava.io.tmpdir=" + (private / "java-tmp").as_posix()]


def prepare_command(root: Path, private: Path) -> list[str]:
    properties = _jvm_properties(root, private)
    home = private / "gradle-home"
    # Command-local JDK launcher startup options, NOT trailing Gradle -D flags.
    # The inherited controller environment/shared process owner are unchanged.
    # The qualified Java launcher reads these before Gradle client initialization;
    # standard Java children inherit them. This is not Cargo/global hermeticity.
    return [GRADLE_STARTUP_ENV.as_posix(), "JDK_JAVA_OPTIONS=" + " ".join(properties),
            "./gradlew", "--no-daemon", "--console=plain", "--max-workers=2", "--gradle-user-home",
            home.relative_to(root).as_posix(),
            "-Dorg.gradle.jvmargs=" + STANDARD_GRADLE_JVM_ARGS + " " + " ".join(properties),
            "-Pkotlin.daemon.jvmargs=" + STANDARD_KOTLIN_DAEMON_JVM_ARGS + " " + " ".join(properties),
            "-PnativecmpkitNativeMode=host", *PREPARE_TASKS]


def exact_command(java_home: Path, classpath: str, root: Path, private: Path, *, inventory=False) -> list[str]:
    properties = _jvm_properties(root, private)
    if inventory:
        return [(java_home / "bin/javap").as_posix(), *("-J" + item for item in properties),
                "-p", "-v", "-classpath", classpath, CLASS]
    return [(java_home / "bin/java").as_posix(), "-Xcheck:jni", *properties,
            "-Dnativecmpkit.picker.trustSystemLibrary=false", "-cp", classpath, "org.junit.runner.JUnitCore", CLASS]


def review_prepare(body: str) -> dict:
    shared._bounded_text(body)
    tasks = (":calf-file-picker:buildNativeLib", *PREPARE_TASKS)
    if (any(len(re.findall(r"(?m)^> Task " + re.escape(task) + r"$", body)) != 1 for task in tasks) or
            len(re.findall(r"(?m)^BUILD SUCCESSFUL in .+$", body)) != 1 or
            re.search(r"(?m)^> Task \S*(?:desktopTest|connectedAndroidDeviceTest|Test)(?:\s|$)|BUILD FAILED", body)):
        raise Refusal("standard-fresh-host-preparation-task-or-zero-test-contract-refused")
    return {"required_resource_tasks": list(PREPARE_TASKS), "host_native_build_task_returned": True, "executed_tests": 0}


def review_inventory(body: str) -> dict:
    shared._bounded_text(body)
    if (len(re.findall(r"(?m)^public final class " + re.escape(CLASS) + r"$", body)) != 1 or
            len(re.findall(r"(?m)^\s*super_class:.*// java/lang/Object$", body)) != 1 or
            re.search(r"(?m)^\s{4,8}org\.junit\.(?:Ignore|Rule|ClassRule|runner\.RunWith)(?:\(|$)", body)):
        raise Refusal("compiled-class-must-be-final-object-subclass-with-no-ignore-or-custom-runner")
    declaration = body.split("\n{\n", 1)
    if len(declaration) != 2 or "\n}\n" not in declaration[1]:
        raise Refusal("compiled-method-declaration-boundary-refused")
    methods = declaration[1].split("\n}\n", 1)[0]
    starts = list(re.finditer(r"(?m)^  (?:public|protected|private) [^\n]+\);$|^  static \{\};$", methods))
    annotated = []
    for index, start in enumerate(starts):
        section = methods[start.start():starts[index + 1].start() if index + 1 < len(starts) else len(methods)]
        annotations = re.findall(r"(?m)^\s{4,8}org\.junit\.Test(?:\(|$)", section)
        if not annotations:
            continue
        if (len(annotations) != 1 or start.group() != "  public final void " + METHOD + "();" or
                len(re.findall(r"(?m)^    descriptor: \(\)V$", section)) != 1 or
                not re.search(r"(?m)^    flags: .*\bACC_PUBLIC\b.*\bACC_FINAL\b", section) or
                re.search(r"ACC_STATIC|ACC_ABSTRACT", section)):
            raise Refusal("compiled-test-method-descriptor-annotation-or-instance-contract-refused")
        annotated.append(METHOD)
    if annotated != [METHOD] or len(re.findall(r"(?m)^\s{4,8}org\.junit\.Test(?:\(|$)", methods)) != 1:
        raise Refusal("compiled-inventory-must-have-exactly-one-annotated-method")
    return {"classname": CLASS, "method": METHOD, "annotated_tests": 1, "inventory_executed_tests": 0}


def review_junit(body: str) -> dict:
    shared._bounded_text(body)
    lines = [line for line in body.splitlines() if line]
    marker = re.compile(r"^\.?" + re.escape(SUCCESS_MARKER) + r"$")
    selected = [index for index, line in enumerate(lines) if marker.fullmatch(line)]
    times = [index for index, line in enumerate(lines) if re.fullmatch(r"Time: [0-9]+(?:\.[0-9]+)?", line)]
    if (not lines or lines[0] != "JUnit version 4.13.2" or lines.count("JUnit version 4.13.2") != 1 or
            lines[-1] != "OK (1 test)" or sum("OK (" in line for line in lines) != 1 or len(selected) != 1 or
            len(times) != 1 or not selected[0] < times[0] < len(lines) - 1 or
            re.search(r"(?i)FAIL(?:URE|ED|URES)?|ERROR|Exception|Assumption|Ignored|Skipped|timeout|SIG(?:SEGV|ABRT)|"
                      r"FATAL|WARNING[^\r\n]*(?:JNI|native method)|JNI[^\r\n]*(?:WARNING|DETECTED)|"
                      r"Main Thread Checker|Picked up .*OPTIONS|cleanup[^\r\n]*(?:failed|error)", body)):
        raise Refusal("fresh-exact-junit1-post-finally-marker-or-diagnostics-refused")
    return {"classname": CLASS, "name": METHOD, "status": "passed", "post_finally_markers": 1,
            "tests": 1, "failures": 0, "errors": 0, "skipped": 0}


def source_snapshot(root: Path) -> dict:
    inputs = shared.source_snapshot(root)
    if any(name not in inputs for name in OWNING_INPUTS):
        raise Refusal("new-awt-generation-owning-source-input-missing")
    return inputs


def write_public(output: Path, name: str, value: dict) -> None:
    if name not in PUBLIC_FILES:
        raise Refusal("public-receipt-name-is-not-allowlisted")
    library.write_json(output / name, value)


def prepare_failure_diagnostic(root: Path, stage: str, log: Path, result: dict, budget) -> dict | None:
    # Only the observed nonzero complete owned PREPARE exit is eligible. Do not
    # read successful, inventory/JUnit, stopped, incomplete or surviving groups.
    if (stage != "prepare" or result.get("started") is not True or type(result.get("exit_code")) is not int or
            result["exit_code"] == 0 or result.get("capture_complete") is not True or
            result.get("stop_reason") is not None or result.get("post_exit_group_state") != "absent"):
        return None
    try:
        budget.remaining()
    except Exception:
        return prepare_diagnostics.unavailable("remaining_budget_refused")
    size, digest = result.get("captured_bytes"), result.get("private_capture_sha256")
    if (type(size) is not int or size < 0 or type(digest) is not str or
            re.fullmatch(r"[0-9a-f]{64}", digest) is None):
        return prepare_diagnostics.unavailable("capture_identity_refused")
    if size > prepare_diagnostics.MAX_PRIVATE_BYTES:
        return prepare_diagnostics.unavailable("diagnostic_limit")
    try:
        # Unchanged FD/path/stat/size/hash/UTF8 private-log custody owner.
        body = shared.read_private_log(log, result)
    except Refusal as error:
        return prepare_diagnostics.unavailable("UTF8_refused" if isinstance(error.__cause__, UnicodeError)
                                               else "capture_identity_refused")
    except Exception:
        return prepare_diagnostics.unavailable("capture_unavailable")
    try:
        budget.remaining()
    except Exception:
        return prepare_diagnostics.unavailable("remaining_budget_refused")
    try:
        payload = body.encode("utf-8", errors="strict")
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
            return prepare_diagnostics.unavailable("capture_identity_refused")
        diagnostic = prepare_diagnostics.bounded_public(prepare_diagnostics.classify(root, body))
    except UnicodeError:
        return prepare_diagnostics.unavailable("UTF8_refused")
    except Exception:
        return prepare_diagnostics.unavailable("classifier_error")
    try:
        budget.remaining()
    except Exception:
        return prepare_diagnostics.unavailable("remaining_budget_refused")
    return diagnostic


def phase(root: Path, private: Path, stage: str, command: list[str], budget, receipt: dict) -> str:
    if stage not in {"prepare", "inventory", "junit"}:
        raise Refusal("unknown-owned-awt-phase-refused")
    log, saved = private / (stage + ".log"), private / (stage + ".json")
    result = shared.owned_phase(root, command, log, saved, budget)
    receipt["phases"][stage] = {key: result.get(key) for key in ("started", "exit_code", "capture_complete",
                               "captured_bytes", "private_capture_sha256", "post_exit_group_state", "stop_reason", "elapsed_seconds")}
    try:
        shared.require_phase_success(result, budget)
    except Exception:
        # Best effort only. A secondary classifier/assignment refusal must not
        # replace the original phase/deadline exception or its cleanup owner.
        try:
            diagnostic = prepare_failure_diagnostic(root, stage, log, result, budget)
            if diagnostic is not None:
                receipt["prepare_failure_diagnostic"] = diagnostic
        except Exception:
            pass
        raise
    return shared.read_private_log(log, result)


def run(output_argument: Path) -> int:
    root = library.ROOT
    output = library.safe_path(root, output_argument.as_posix())
    allowed = root / "build/ci-verification"
    if output == allowed or not output.is_relative_to(allowed) or output.exists():
        raise Refusal("new-owned-output-below-ci-verification-required")
    output.mkdir(parents=True, mode=0o700)
    private = output / "private"
    private.mkdir(mode=0o700)
    budget = shared.NativeBudget()
    receipt = {"schema_version": 1, "test_focus": FOCUS, "passed": False, "scope": SCOPE,
               "complete_suite_requested": False, "required_classname": CLASS, "required_method": METHOD,
               "native_operation_budget_seconds": shared.NATIVE_BUDGET_SECONDS, "native_processes_requested": 1,
               "tests": 0, "failures": 0, "errors": 0, "skipped": 0, "test_counts_complete": False, "phases": {}}
    before, context, jdk, cp, native, revision = None, None, None, None, None, None
    owned_directories = None
    stage = "source-runtime-before"
    try:
        reject_overrides(dict(os.environ))
        stage = "owned-jvm-directory-preparation"
        owned_directories = OwnedJavaDirectories(root, private, budget)
        stage = "source-runtime-before"
        before = source_snapshot(root)
        revision = library.git_revision(root)
        context = library.runtime_context.capture(expected_arch="arm64", apple=True, require_clean=True)
        shared.require_runtime(context, revision)
        home, jdk = qualify_jdk(context, budget)
        version = default_version(root, budget)
        write_public(output, "inputs-before.json", before)
        write_public(output, "runtime-before.json", {"context": context, "jdk": jdk,
                     "owned_java_directories": owned_directories.identity()})
        receipt.update(source_revision=revision, source_tree_dirty=False, selected_inputs=len(before),
                       inputs_before_sha256=library.input_digest(before), library_version=version)
        for name in FRESH_OUTPUTS:
            if library.safe_path(root, name).exists():
                raise Refusal("fresh-standard-host-output-required-no-delete-or-cache-fallback")
        stage = "prepare"
        owned_directories.require()
        prepared = phase(root, private, stage, prepare_command(root, private), budget, receipt)
        owned_directories.require()
        receipt["preparation"] = review_prepare(prepared)
        if source_snapshot(root) != before or qualify_jdk(context, budget)[1] != jdk:
            raise Refusal("source-or-qualified-jdk-changed-after-standard-preparation")
        native = native_identity(root, revision, version, budget)
        cp_text, cp = classpath_identity(root, budget)
        require_bundled_identity(cp, native)
        runtime_before = {"context": context, "jdk": jdk, "classpath": cp, "native_bundle": native,
                          "owned_java_directories": owned_directories.identity()}
        write_public(output, "runtime-before.json", runtime_before)
        receipt["runtime_before_sha256"] = library.sha256(output / "runtime-before.json")
        for stage, inventory in (("inventory", True), ("junit", False)):
            if (source_snapshot(root) != before or qualify_jdk(context, budget)[1] != jdk or
                    classpath_identity(root, budget)[1] != cp or native_identity(root, revision, version, budget) != native):
                raise Refusal("source-jdk-classpath-or-native-changed-before-exact-phase")
            owned_directories.require()
            body = phase(root, private, stage, exact_command(home, cp_text, root, private, inventory=inventory), budget, receipt)
            owned_directories.require()
            if inventory:
                receipt["compiled_inventory"] = review_inventory(body)
            else:
                receipt["testcase"] = review_junit(body)
                receipt["tests"] = 1
                receipt["test_counts_complete"] = True
        stage = "final-held-source-runtime-and-deadline"
        after = source_snapshot(root)
        context_after = library.runtime_context.capture(expected_arch="arm64", apple=True, require_clean=True)
        shared.require_runtime(context_after, revision)
        jdk_after = qualify_jdk(context_after, budget)[1]
        cp_after = classpath_identity(root, budget)[1]
        native_after = native_identity(root, revision, version, budget)
        owned_directories.require()
        write_public(output, "inputs-after.json", after)
        write_public(output, "runtime-after.json", {"context": context_after, "jdk": jdk_after,
                     "classpath": cp_after, "native_bundle": native_after,
                     "owned_java_directories": owned_directories.identity()})
        receipt.update(held_owned_java_directories=True, held_inputs=before == after, held_jdk=jdk == jdk_after, held_classpath=cp == cp_after,
                       held_native_bundle=native == native_after, inputs_after_sha256=library.input_digest(after),
                       runtime_after_sha256=library.sha256(output / "runtime-after.json"),
                       held_runtime_identity=context["compiler_runtime_fingerprint"] == context_after["compiler_runtime_fingerprint"])
        if (not all(receipt[key] for key in ("held_owned_java_directories", "held_inputs", "held_jdk", "held_classpath", "held_native_bundle", "held_runtime_identity")) or
                library.git_revision(root) != revision or receipt["compiled_inventory"]["annotated_tests"] != 1 or receipt["tests"] != 1):
            raise Refusal("final-held-source-runtime-native-and-exact-one-required")
        budget.remaining()
        receipt["native_operation_elapsed_seconds"] = budget.elapsed()
        receipt["passed"] = True
    except Exception as error:
        receipt.update(failed_stage=stage, error_type=type(error).__name__,
                       reason_code=str(error) if isinstance(error, Refusal) else "verification-error-details-private")
    finally:
        # Passive failure readbacks are separate and never replace the primary.
        if not receipt["passed"] and before is not None:
            try:
                after = source_snapshot(root)
                write_public(output, "inputs-after.json", after)
                receipt.update(held_inputs=before == after, inputs_after_sha256=library.input_digest(after))
            except Exception as error:
                receipt["failure_source_readback_error_type"] = type(error).__name__
        if owned_directories is not None:
            if not receipt["passed"]:
                try:
                    owned_directories.require()
                except Exception as error:
                    receipt["failure_owned_java_directory_readback_error_type"] = type(error).__name__
            try:
                owned_directories.close()
                receipt["owned_java_descriptors_closed"] = True
            except Exception as error:
                if receipt["passed"]:
                    receipt.update(passed=False, failed_stage="owned-jvm-descriptor-cleanup", error_type=type(error).__name__,
                                   reason_code="owned-jvm-descriptor-cleanup-unestablished")
                else:
                    receipt["failure_owned_java_descriptor_cleanup_error_type"] = type(error).__name__
        write_public(output, "receipt.json", receipt)
    print(json.dumps({key: receipt[key] for key in ("test_focus", "passed", "tests", "failed_stage", "reason_code", "scope") if key in receipt}))
    return 0 if receipt["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
