#!/usr/bin/env python3
"""Explicit, nonactivated JavaFX dependency regression; not a library consumer.

Only the exact pinned 21.0.13 dependency is patched in an owned test directory.
Shared caches, NativeCmpKit dependencies and JavaFX route properties are untouched.
"""
from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
CASES = ("zero-header", "plain-body", "gzip-body", "concurrent")
MODULES = ("base", "controls", "graphics", "media", "web")
CLASSIFIERS = ("linux", "win", "linux-aarch64", "mac", "mac-aarch64")
SOURCE_ENTRY = "com/sun/webkit/network/HTTP2Loader.java"
BEFORE = b"        canceled = true;\n    }\n\n    private void callBackIfNotCanceled"
AFTER = b"        canceled = true;\n        if (response != null) {\n            response.cancel(true);\n        }\n    }\n\n    private void callBackIfNotCanceled"
MAX_ARTIFACT = 100 * 1024 * 1024


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def document(payload):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            need(key not in value, "Duplicate JSON key")
            value[key] = item
        return value

    def invalid(_):
        raise ValueError("Nonfinite JSON number")

    return json.loads(payload, object_pairs_hook=unique, parse_constant=invalid)


def selection(value):
    selected = list(CASES) if value == "all" else value.split(",")
    need(0 < len(selected) <= len(CASES) and len(set(selected)) == len(selected)
         and all(case in CASES for case in selected), "Unknown or duplicate case selection")
    return selected


def classifier():
    architecture = platform.machine().lower()
    value = {("Linux", "x86_64"): "linux", ("Linux", "amd64"): "linux",
             ("Windows", "x86_64"): "win", ("Windows", "amd64"): "win",
             ("Linux", "aarch64"): "linux-aarch64", ("Linux", "arm64"): "linux-aarch64",
             ("Darwin", "x86_64"): "mac", ("Darwin", "amd64"): "mac",
             ("Darwin", "aarch64"): "mac-aarch64", ("Darwin", "arm64"): "mac-aarch64"}.get(
                 (platform.system(), architecture))
    need(value is not None, "This diagnostic has no artifact pin for the current OS")
    return value


def validate_row(row):
    need(set(row) == {"file", "url", "bytes", "sha256"}, "Unexpected dependency fields")
    name = row["file"]
    need(type(name) is str and name.startswith("javafx-") and name.endswith(".jar")
         and "/" not in name and "\\" not in name and ".." not in name, "Unsafe dependency filename")
    need(type(row["bytes"]) is int and 0 < row["bytes"] <= MAX_ARTIFACT, "Invalid dependency size")
    need(type(row["sha256"]) is str and len(row["sha256"]) == 64
         and all(c in "0123456789abcdef" for c in row["sha256"]), "Invalid dependency SHA256")
    module = name.split("-")[1]
    allowed = {f"javafx-{m}-21.0.13-{kind}.jar" for m in MODULES for kind in CLASSIFIERS}
    allowed.add("javafx-web-21.0.13-sources.jar")
    need(name in allowed, "Unpinned version/classifier/source filename")
    expected = f"https://repo.maven.apache.org/maven2/org/openjfx/javafx-{module}/21.0.13/{name}"
    need(module in MODULES and row["url"] == expected, "Only the fixed official Maven dependency path is allowed")


def checked_artifact(root, row, download):
    validate_row(row)
    file = root / row["file"]
    need(not file.is_symlink(), "Dependency symlink refused")
    if file.exists():
        need(file.is_file() and file.stat().st_size == row["bytes"], "Cached dependency size/type changed")
        payload = file.read_bytes()
    else:
        need(download, "Pinned dependency is absent; --download is required for acquisition")
        with urllib.request.urlopen(row["url"], timeout=120) as response:
            need(response.geturl() == row["url"], "Dependency redirect refused")
            payload = response.read(row["bytes"] + 1)
        need(len(payload) == row["bytes"] and digest(payload) == row["sha256"], "Downloaded dependency differs from the pin")
        with file.open("xb") as output:
            output.write(payload)
    need(len(payload) == row["bytes"] and digest(payload) == row["sha256"], "Dependency differs from the pin")
    return file


def patch_source(payload):
    need(digest(payload) == "e2413d1ac8cb78be77f97fc6add5e17bee1859e1c5fcbb97481444eb62eac43f", "Unexpected upstream source")
    need(payload.count(BEFORE) == 1, "Cancellation source anchor changed")
    changed = payload.replace(BEFORE, AFTER, 1)
    need(changed[:changed.index(b"package ")] == payload[:payload.index(b"package ")], "Upstream license header changed")
    return changed


def compare_patch(original, changed):
    diff = "".join(difflib.unified_diff(original.decode().splitlines(keepends=True),
                                     changed.decode().splitlines(keepends=True),
                                     fromfile="a/modules/javafx.web/src/main/java/com/sun/webkit/network/HTTP2Loader.java",
                                     tofile="b/modules/javafx.web/src/main/java/com/sun/webkit/network/HTTP2Loader.java"))
    need(diff.encode() == (HERE / "cancel-response-future.patch").read_bytes(), "Stored patch differs from the exact source delta")


def case_results(stdout, selected):
    rows = [document(line) for line in stdout.splitlines() if line.startswith('{"case":') or line.startswith('{"summary":')]
    need(len(rows) == len(selected) + 1, "Missing or duplicate native case/summary rows")
    for row, expected in zip(rows[:-1], selected):
        numbers = ("peerEofs", "cancellations", "responseBytes", "sameEngineRecoveryRequests", "caseElapsedNanos")
        need(all(type(row[key]) is int for key in numbers) and row["caseElapsedNanos"] > 0,
             "Native witness integers must not be Boolean or nonpositive clocks")
        need(row["case"] == expected and row["passed"] is True and type(row["peerEofs"]) is int
             and row["peerEofs"] == 1 and row["cancellations"] == 1
             and row["cleanupBeganBeforeEof"] is False and row["sameEngineRecoveryRequests"] == 1,
             "Native cancellation/EOF/recovery witness differs")
        need(type(row["responseBytes"]) is int and (row["responseBytes"] == 0 if expected in ("zero-header", "concurrent")
                                                   else row["responseBytes"] > 0), "Held-response byte witness differs")
        if expected in ("plain-body", "gzip-body"):
            need(row["parsedNativeTitle"] is True, "Native streaming body was not parsed")
        if expected != "concurrent":
            need(type(row["cancelToPeerNanos"]) is int and row["cancelToPeerNanos"] > 0,
                 "Cancellation-to-EOF clock missing")
        if expected == "concurrent":
            need(type(row["repeatedIdleCancels"]) is int and row["repeatedIdleCancels"] == 3
                 and row["independentRequestPassed"] is True and type(row["otherCancellations"]) is int
                 and row["otherCancellations"] == 0, "Concurrent isolation witness differs")
    need(type(rows[-1]["scenarioCount"]) is int and type(rows[-1]["passed"]) is int
         and type(rows[-1]["libraryTests"]) is int, "Native summary count type differs")
    need(rows[-1] == {"summary": True, "scenarioCount": len(selected), "passed": len(selected),
                      "libraryTests": 0, "privateRouteOverride": False}, "Native summary differs")
    return rows


def run(args):
    selected = selection(args.cases)
    target = classifier()
    output = args.output.absolute()
    need(not output.exists(), "Output already exists; preserve results and select a new owned directory")
    output.mkdir(parents=True)
    commands = []
    result = {"schema_version": 1, "selected": selected, "classifier": target,
              "revision": os.environ.get("GITHUB_SHA"), "library_tests": 0, "unmodified_baseline_replayed": False,
              "scope": "Explicit JavaFX dependency module patch; not NativeCmpKit/public Stop/consumer/security/release acceptance",
              "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "passed": False}

    def write(name, value):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def command(name, argv, timeout=120):
        start = time.monotonic()
        process = subprocess.Popen(argv, cwd=output, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=os.name != "nt")
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                process.terminate()  # The owned java/javac child, never a system-wide process match.
            else:
                import signal
                os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    process.kill()
                else:
                    import signal
                    os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
        (output / (name + ".stdout")).write_bytes(stdout)
        (output / (name + ".stderr")).write_bytes(stderr)
        row = {"name": name, "command": list(map(str, argv)), "exit_code": process.returncode,
               "elapsed_seconds": time.monotonic() - start, "timeout": timed_out,
               "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr),
               "stdout_bytes": len(stdout), "stderr_bytes": len(stderr)}
        commands.append(row)
        write("commands.json", commands)
        need(process.returncode == 0 and not timed_out, f"{name} failed; original logs retained")
        return stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    try:
        pins = document((HERE / "artifacts.json").read_bytes())
        need(pins["schema_version"] == 1 and pins["version"] == "21.0.13", "Unknown dependency manifest")
        artifacts = args.artifact_dir.absolute() if args.artifact_dir else output / "dependencies"
        artifacts.mkdir(parents=True, exist_ok=True)
        source_jar = checked_artifact(artifacts, pins["sources"], args.download)
        jars = [checked_artifact(artifacts, row, args.download) for row in pins["platforms"][target]]
        need([row["file"] for row in pins["platforms"][target]] ==
             [f"javafx-{module}-21.0.13-{target}.jar" for module in MODULES], "Dependency module inventory changed")
        with zipfile.ZipFile(source_jar) as archive:
            entries = [entry for entry in archive.infolist() if entry.filename == SOURCE_ENTRY]
            need(len(entries) == 1 and entries[0].file_size == 24544, "Expected source member absent or duplicated")
            original = archive.read(entries[0])
        changed = patch_source(original)
        compare_patch(original, changed)
        source = output / "source" / "HTTP2Loader.java"
        source.parent.mkdir()
        source.write_bytes(changed)
        files = [HERE / "JavaFxPublicCancellationProbe.java", HERE / "artifacts.json", HERE / "cancel-response-future.patch",
                 HERE / "probe_runner.py", source, source_jar, *jars]
        before = {str(file): digest(file.read_bytes()) for file in files}
        write("source-bindings.json", before)
        java = shutil.which("java")
        javac = shutil.which("javac")
        need(java is not None and javac is not None, "Install the JDK17 java/javac tools")
        _, version = command("java-version", [java, "-version"])
        need('version "17.' in version, "The diagnostic requires JDK17")
        module_path = os.pathsep.join(map(str, jars))
        probe_classes, patched = output / "probe-classes", output / "patched-module"
        command("compile-probe", [javac, "--module-path", module_path, "--add-modules", "javafx.controls,javafx.web",
                                  "-d", str(probe_classes), str(HERE / "JavaFxPublicCancellationProbe.java")])
        command("compile-patch", [javac, "--module-path", module_path, "--add-modules", "javafx.web",
                                  "--patch-module", "javafx.web=" + str(source.parent), "-d", str(patched), str(source)])
        binary_files = sorted([*probe_classes.rglob("*.class"), *patched.rglob("*.class")])
        need(binary_files, "Compilers emitted no classes")
        binary_before = {str(file): digest(file.read_bytes()) for file in binary_files}
        write("binary-bindings.json", binary_before)
        (output / "tmp").mkdir()
        java_command = [java, "--module-path", module_path, "--add-modules", "javafx.controls,javafx.web",
                        "--patch-module", "javafx.web=" + str(patched), "-Djava.io.tmpdir=" + str(output / "tmp"),
                        "-cp", str(probe_classes), "JavaFxPublicCancellationProbe", ",".join(selected)]
        if target in ("linux", "linux-aarch64"):
            need(shutil.which("xvfb-run") is not None, "Install Xvfb for this owned visible-Stage diagnostic")
            java_command = [shutil.which("xvfb-run"), "-a", *java_command]
        stdout, _ = command("native-cases", java_command)
        rows = case_results(stdout, selected)
        write("case-results.json", rows)
        after = {str(file): digest(file.read_bytes()) for file in files}
        need(before == after, "Source/dependency bytes changed during execution")
        need(binary_before == {str(file): digest(file.read_bytes()) for file in binary_files},
             "Compiled probe/patch bytes changed during execution")
        result.update(passed=True, cases_passed=len(selected), held_inputs=True)
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        result["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        write("results.json", result)
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="all", help="Explicit all or comma-separated failed/unseen cases")
    parser.add_argument("--output", required=True, type=Path, help="New owned result directory; never overwritten")
    parser.add_argument("--artifact-dir", type=Path, help="Optional previously acquired pinned registry JARs only")
    parser.add_argument("--download", action="store_true", help="Acquire missing fixed pinned registry dependencies")
    run(parser.parse_args())
