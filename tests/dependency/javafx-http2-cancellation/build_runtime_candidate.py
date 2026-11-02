#!/usr/bin/env python3
"""Build a private full-JAR JavaFX candidate, never edit/publish an upstream JAR.

Ordinary library dependencies remain unchanged. Only the five owning loader
classes and an explicit candidate manifest may replace existing JAR members.
Java sources/notices accompany the candidate; full upstream native corresponding
source, dependency security and redistribution readiness remain separate gates.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import time
import zipfile

import probe_runner as probe

HERE = Path(__file__).resolve().parent
IDENTITY = "21.0.13-nativecmpkit-cancel1-local"
NOTICE = b"// Modified by NativeCmpKit on 2026-11-02: cancel the pending HTTP exchange."
CLASS_PREFIX = "com/sun/webkit/network/"
CLASS_SHA256 = {
    "HTTP2Loader.class": "9e8663af362be84a12111e785b06f2cadf3c1f02e6cd19a9782a2e9f7e4675c2",
    "HTTP2Loader$1.class": "251086066cdba566bf7cf3b69c7109f41a2ca548fbcc91cd5f141415437f7345",
    "HTTP2Loader$1$1.class": "376ee53b07d3053160769c280bb2e3807dbc4a2700a1b94858a50ed05b9c2d04",
    "HTTP2Loader$2.class": "0b3dfffd8396ad3a76c5a480f3573babda6a1f17312270f90f0051635e0e0b1e",
    "HTTP2Loader$3.class": "e5324d3b4643749b6463e83f1027cbceced0f6552022b8b78020f56ca122616d",
}
LEGAL = {
    "LICENSE-GPLv2-Classpath.txt": "4b9abebc4338048a7c2dc184e9f800deb349366bdf28eb23c2677a77b4c87726",
    "ADDITIONAL_LICENSE_INFO": "a69bce275ba7a3570af6579cb0f55682cd75fedfcd49e0e8e9022270c447c916",
    "ASSEMBLY_EXCEPTION": "a44eb7b5caf5534c6ef536b21edb40b4d6babf91bf97d9d45596868618b2c6fb",
}
ORIGINAL_MANIFEST = b"Manifest-Version: 1.0\r\n\r\n"
CANDIDATE_MANIFEST = (b"Manifest-Version: 1.0\r\n"
                      b"Implementation-Title: NativeCmpKit private JavaFX candidate\r\n"
                      b"Implementation-Version: " + IDENTITY.encode() + b"\r\n"
                      b"NativeCmpKit-Publication-Ready: false\r\n\r\n")


def modified_source(original):
    changed = probe.patch_source(original)
    probe.compare_patch(original, changed)
    anchor = b" */\n\npackage com.sun.webkit.network;"
    probe.need(changed.count(anchor) == 1, "Original header boundary changed")
    changed = changed.replace(anchor, b" */\n" + NOTICE + b"\npackage com.sun.webkit.network;", 1)
    probe.need(original[:original.index(b" */") + 3] == changed[:changed.index(b" */") + 3],
               "Original copyright/license header changed")
    probe.need(changed.count(b"\n") == original.count(b"\n") + 3,
               "Modification notice must replace the existing blank line")
    return changed


def checked_entries(archive):
    entries = archive.infolist()
    probe.need(0 < len(entries) <= 4096 and len({e.filename for e in entries}) == len(entries),
               "Archive member inventory is empty, duplicate or unbounded")
    total = 0
    for entry in entries:
        path = PurePosixPath(entry.filename)
        probe.need(not path.is_absolute() and ".." not in path.parts and "\\" not in entry.filename
                   and ":" not in entry.filename and "\x00" not in entry.filename,
                   "Unsafe archive member")
        probe.need(not entry.flag_bits & 1 and entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                   and 0 <= entry.file_size <= 128 * 1024 * 1024, "Encrypted/unknown/unbounded archive member")
        probe.need(not (entry.filename.upper().startswith("META-INF/")
                        and entry.filename.upper().endswith((".SF", ".RSA", ".DSA", ".EC"))),
                   "Signed dependency refused; signatures must not be silently stripped or invalidated")
        probe.need(not entry.filename.startswith("META-INF/nativecmpkit/"), "Already modified candidate refused")
        total += entry.file_size
    probe.need(total <= 192 * 1024 * 1024, "Archive expanded size exceeds candidate bound")
    return entries


def write_archive(original, destination, replacements, additions):
    probe.need(not destination.exists() and not destination.is_symlink(), "Candidate output already exists")
    with zipfile.ZipFile(original) as source:
        entries = checked_entries(source)
        names = {e.filename for e in entries}
        probe.need(set(replacements) <= names and not set(additions) & names,
                   "Replacement missing or added member overlaps upstream")
        for name in additions:
            path = PurePosixPath(name)
            probe.need(not path.is_absolute() and ".." not in path.parts and "\\" not in name
                       and ":" not in name and "\x00" not in name, "Unsafe added archive member")
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
            for entry in entries:
                target.writestr(copy.copy(entry), replacements.get(entry.filename, source.read(entry)),
                                compresslevel=9)
            for name, payload in sorted(additions.items()):
                entry = zipfile.ZipInfo(name, date_time=(2026, 11, 2, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                target.writestr(entry, payload, compresslevel=9)
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(destination) as target:
        actual = target.infolist()
        probe.need(len(actual) == len({e.filename for e in actual}) and
                   {e.filename for e in actual} == names | set(additions), "Candidate member inventory differs")
        retained = {}
        changed = []
        for entry in entries:
            before, after = source.read(entry), target.read(entry.filename)
            if entry.filename in replacements:
                probe.need(after == replacements[entry.filename], "Candidate replacement differs")
                if before != after:
                    changed.append(entry.filename)
            else:
                probe.need(before == after, "An unrelated upstream member changed")
                retained[entry.filename] = probe.digest(after)
        for name, payload in additions.items():
            probe.need(target.read(name) == payload, "Candidate metadata differs")
    return {"original_members": len(entries), "retained_payload_members": len(retained),
            "retained_payload_sha256": retained, "changed_payload_members": changed,
            "added_members": sorted(additions), "all_other_payloads_identical": True}


def build(args):
    target = probe.classifier()
    output = args.output.absolute()
    probe.need(not output.exists() and not output.is_symlink(), "Use a new owned candidate directory")
    output.mkdir(parents=True)
    started = time.monotonic()
    result = {"schema_version": 1, "identity": IDENTITY, "classifier": target, "passed": False,
              "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Private full-JAR dependency candidate; no default adoption, publication or release clearance",
              "full_native_corresponding_source_complete": False, "library_tests": 0}
    commands = []

    def write(name, value):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def command(name, argv):
        start = time.monotonic()
        process = subprocess.Popen(argv, cwd=output, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=os.name != "nt")
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                process.terminate()  # Exact owned java/javac child, not a global process match.
            else:
                import signal
                os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    process.kill()
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
        (output / (name + ".stdout")).write_bytes(stdout)
        (output / (name + ".stderr")).write_bytes(stderr)
        commands.append({"name": name, "command": list(map(str, argv)), "exit_code": process.returncode,
                         "elapsed_seconds": time.monotonic() - start, "timeout": timed_out,
                         "stdout_sha256": probe.digest(stdout), "stderr_sha256": probe.digest(stderr)})
        write("commands.json", commands)
        probe.need(process.returncode == 0 and not timed_out, "Candidate compiler failed; original streams retained")
        return stderr

    try:
        pins = probe.document((HERE / "artifacts.json").read_bytes())
        probe.need(pins["schema_version"] == 1 and pins["version"] == "21.0.13", "Unknown candidate dependency version")
        dependencies = args.artifact_dir.absolute() if args.artifact_dir else output / "dependencies"
        probe.need(not dependencies.is_symlink(), "Candidate dependency directory symlink refused")
        dependencies.mkdir(parents=True, exist_ok=True)
        source_jar = probe.checked_artifact(dependencies, pins["sources"], args.download)
        jars = [probe.checked_artifact(dependencies, row, args.download) for row in pins["platforms"][target]]
        probe.need([r["file"] for r in pins["platforms"][target]] ==
                   [f"javafx-{m}-21.0.13-{target}.jar" for m in probe.MODULES], "Candidate module inventory changed")
        web = jars[-1]
        with zipfile.ZipFile(source_jar) as source:
            checked_entries(source)
            original = source.read(probe.SOURCE_ENTRY)
        changed = modified_source(original)
        with zipfile.ZipFile(web) as archive:
            checked_entries(archive)
            probe.need(archive.read("META-INF/MANIFEST.MF") == ORIGINAL_MANIFEST, "Upstream manifest changed")
        files = [HERE / "build_runtime_candidate.py", HERE / "probe_runner.py", HERE / "artifacts.json",
                 HERE / "cancel-response-future.patch", HERE / "NOTICE.md", source_jar, *jars,
                 *[HERE / name for name in LEGAL]]
        before = {str(f): probe.digest(f.read_bytes()) for f in files}
        write("inputs-before.json", before)
        additions = {}
        for name, expected in LEGAL.items():
            payload = (HERE / name).read_bytes()
            probe.need(probe.digest(payload) == expected, "Preserved upstream legal bytes changed")
            additions["META-INF/nativecmpkit/" + name] = payload
        additions["META-INF/nativecmpkit/NOTICE.md"] = (HERE / "NOTICE.md").read_bytes()
        additions["META-INF/nativecmpkit/CANDIDATE.txt"] = (
            "Private NativeCmpKit JavaFX HTTP2Loader cancellation candidate. NOT PUBLISHED.\n"
            "GPLv2 with Classpath exception retained for the changed source and classes.\n"
            "Only Java corresponding sources are included; full upstream/native source,\n"
            "security, platform consumers, API/ABI and redistribution gates remain.\n").encode()
        additions["META-INF/nativecmpkit/cancel-response-future-with-notice.patch"] = "".join(
            difflib.unified_diff(original.decode().splitlines(keepends=True), changed.decode().splitlines(keepends=True),
                                 fromfile="a/" + probe.SOURCE_ENTRY, tofile="b/" + probe.SOURCE_ENTRY)).encode()
        java, javac = shutil.which("java"), shutil.which("javac")
        probe.need(java is not None and javac is not None, "JDK17 java/javac required")
        version = command("java-version", [java, "-version"])
        probe.need(b'version "17.' in version, "Candidate compiler requires actual JDK17")
        source = output / "source" / "HTTP2Loader.java"
        source.parent.mkdir()
        source.write_bytes(changed)
        classes = output / "classes"
        command("compile-owning-source", [javac, "--release", "17", "--module-path",
                                          os.pathsep.join(map(str, jars)), "--add-modules", "javafx.web",
                                          "--patch-module", "javafx.web=" + str(source.parent),
                                          "-d", str(classes), str(source)])
        # JAR member names are POSIX paths on every compiler host.
        actual_classes = {p.relative_to(classes).as_posix(): p.read_bytes() for p in classes.rglob("*.class")}
        expected_classes = {CLASS_PREFIX + n: d for n, d in CLASS_SHA256.items()}
        probe.need({n: probe.digest(b) for n, b in actual_classes.items()} == expected_classes,
                   "Compiler emits changed/extra owning classes; do not automatically refresh accepted pins")
        jar = output / f"javafx-web-{IDENTITY}-{target}.jar"
        source_candidate = output / f"javafx-web-{IDENTITY}-java-sources.jar"
        jar_review = write_archive(web, jar, {**actual_classes, "META-INF/MANIFEST.MF": CANDIDATE_MANIFEST}, additions)
        source_review = write_archive(source_jar, source_candidate, {probe.SOURCE_ENTRY: changed}, additions)
        write("jar-member-review.json", jar_review)
        write("java-source-member-review.json", source_review)
        after = {str(f): probe.digest(f.read_bytes()) for f in files}
        write("inputs-after.json", after)
        probe.need(before == after and source.read_bytes() == changed and
                   {n: probe.digest((classes / n).read_bytes()) for n in actual_classes} == expected_classes,
                   "Candidate source/dependency/compiled inputs changed during packaging")
        result.update(passed=True,held_inputs=True,jar_file=jar.name,jar_sha256=probe.digest(jar.read_bytes()),
                      java_sources_file=source_candidate.name,java_sources_sha256=probe.digest(source_candidate.read_bytes()),
                      modified_source_sha256=probe.digest(changed),modified_class_sha256=expected_classes,
                      original_web_sha256=pins["platforms"][target][-1]["sha256"],
                      original_java_sources_sha256=pins["sources"]["sha256"],
                      upstream_web_members=jar_review["original_members"],
                      unchanged_nonowning_members=jar_review["retained_payload_members"],
                      default_dependencies_changed=False,cached_JARs_modified=False)
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error))
        raise
    finally:
        result["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result["elapsed_seconds"] = time.monotonic() - started
        write("candidate.json", result)
        print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--download", action="store_true")
    build(parser.parse_args())
