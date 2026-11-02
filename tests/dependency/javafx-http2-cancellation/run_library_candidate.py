#!/usr/bin/env python3
"""Only one failed NativeCmpKit public Stop case, using a full candidate JAR.

Compose the existing finite source plan, fresh XML collector, runtime/daemon
observations, disk/process guard and checkout-local lock. No sample tests, default
dependency mutation, private route property, runtime module patch or publication.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time

import build_runtime_candidate as candidate
import probe_runner as probe

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts/ci"))
import daemon_jvm
import library_tests as library
import runtime_context

FOCUS = "webview-desktop-stop-windows-recovery"
PLATFORMS = {"windows": ("win", FOCUS),
             "linux-arm64": ("linux-aarch64", "webview-desktop-stop-linux-arm64-recovery"),
             "macos-arm64": ("mac-aarch64", "webview-desktop-stop-macos-recovery"),
             "macos-x64": ("mac", "webview-desktop-stop-macos-recovery")}
INIT = "tests/dependency/javafx-http2-cancellation/library-runtime-candidate.init.gradle.kts"
WORKFLOW = ".github/workflows/javafx-library-candidate.yml"
SELECTOR = ("com.mohamedrejeb.calf.ui.web.DesktopWebViewStopRedirectAcceptanceTest."
            "publicStopCancelsOneHeldNativeRequestBeforeAnyResponseAndRecoversOnTheSameOwner")


def seed_official_cache(destination, pins, home, classifier="win"):
    probe.need(classifier in {value[0] for value in PLATFORMS.values()}, "Unknown candidate cache classifier")
    probe.need(not destination.exists() and not destination.is_symlink(), "Use a new owned official-input directory")
    destination.mkdir()
    copied = []
    for row in [pins["sources"], *pins["platforms"][classifier]]:
        probe.validate_row(row)
        module = row["file"].split("-")[1]
        base = home / ".gradle/caches/modules-2/files-2.1/org.openjfx" / ("javafx-" + module) / "21.0.13"
        matches = sorted(base.glob("*/" + row["file"]))
        for file in matches:
            probe.need(not file.is_symlink() and file.is_file() and file.stat().st_size == row["bytes"]
                       and probe.digest(file.read_bytes()) == row["sha256"],
                       "Restored official dependency differs; no deletion or pin refresh")
        if matches:
            shutil.copyfile(matches[0], destination / row["file"])
            copied.append({"file": row["file"], "sha256": row["sha256"], "reused_exact_cache_bytes": True})
    return copied


def focused_plan(root, focus=FOCUS):
    probe.need(focus in {value[1] for value in PLATFORMS.values()}, "Unknown failed-only candidate focus")
    plan = library.plan(root, "desktop", only_modules=("calf-webview",), focus=focus)
    probe.need(library.validate_test_focus(plan) and plan["explicit_test_focus"] == focus and len(plan["expected"]) == 1
               and plan["expected"][0]["test_filter"] == SELECTOR
               and plan["expected"][0]["task"] == ":calf-webview:desktopTest",
               "Existing finite library selection changed")
    return plan


def command(root, plan, output, manifest):
    argv = library.gradle_command("desktop", plan, root=root)
    probe.need(argv.count("--tests") == 1 and argv[argv.index("--tests") + 1] == SELECTOR,
               "Only the failed original public Stop selector is allowed")
    classifier = manifest.get("classifier")
    focuses = {value[0]: value[1] for value in PLATFORMS.values()}
    probe.need(manifest["passed"] is True and classifier in focuses
               and plan["explicit_test_focus"] == focuses[classifier]
               and manifest["identity"] == candidate.IDENTITY, "Invalid full-artifact candidate")
    probe.need(probe.classifier() == classifier, "Full candidate classifier must match the actual native host")
    argv = ["--max-workers=1" if s == "--max-workers=2" else s for s in argv]
    argv += ["--no-parallel", "--no-build-cache", "--init-script", INIT,
             "-PnativecmpkitJavaFxCandidateRoot=" + (output / "runtime-candidate").relative_to(root).as_posix(),
             "-PnativecmpkitJavaFxCandidateSha256=" + manifest["jar_sha256"],
             "-PnativecmpkitJavaFxCandidateClassifier=" + classifier]
    if classifier == "linux-aarch64":
        display = shutil.which("xvfb-run")
        probe.need(display is not None, "Linux ARM64 candidate requires the owned Xvfb prerequisite")
        argv = [display, "-a", *argv]
    return argv


def marker(log, manifest):
    rows = [line.split("NATIVECMPKIT_JAVAFX_CANDIDATE ", 1)[1]
            for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if "NATIVECMPKIT_JAVAFX_CANDIDATE " in line]
    expected = ("task=:calf-webview:desktopTest originalRemoved=1 candidateCount=1 "
                "originalSha256=" + manifest["original_web_sha256"] + " candidateSha256=" + manifest["jar_sha256"]
                + " runtimeModulePatch=false privateRouteOverride=false")
    probe.need(rows == [expected], "Actual one-provider full-JAR replacement marker missing/duplicate/different")
    return {"original_removed": 1, "candidate_providers": 1, "jar_sha256": manifest["jar_sha256"],
            "runtime_module_patch": False, "private_route_override": False}


def run(args):
    platform = getattr(args, "platform", "windows")
    probe.need(platform in PLATFORMS, "Unknown explicit missing-only candidate platform")
    classifier, focus = PLATFORMS[platform]
    probe.need(probe.classifier() == classifier,
               "This missing-only library candidate runs only on Windows x64 or the explicitly selected Linux ARM64/macOS host")
    probe.need(not any(os.environ.get(k) for k in ("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVAC_OPTIONS")),
               "Inherited JVM/compiler options refused for the exact candidate")
    root = ROOT.resolve()
    allowed = root / "build/ci-verification"
    output = library.safe_path(root, args.output)
    probe.need(output.is_relative_to(allowed) and output != allowed and not output.exists(),
               "Use a new owned build/ci-verification candidate output")
    allowed.mkdir(parents=True, exist_ok=True)
    lock = allowed / ".library-tests.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    receipt = {"schema_version": 1, "passed": False, "library_tests": 0,
               "platform": platform, "classifier": classifier, "focus": focus,
               "scope": "One failed original public Stop method on the exact selected host, full private dependency artifact; no default adoption/security/consumer/API-ABI/legal/release clearance",
               "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}

    def write(name, value):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    try:
        os.write(descriptor, f"{os.getpid()}\n".encode())
        output.mkdir(parents=True)
        probe.need(shutil.disk_usage(root).free >= 8192 * 1024 * 1024, "Retain the 8GiB disk reserve")
        revision = library.git_revision(root)
        before = library.snapshot_inputs(root)
        own_files = [p for p in HERE.iterdir() if p.is_file()] + [root / WORKFLOW]
        own_before = {p.relative_to(root).as_posix(): probe.digest(p.read_bytes()) for p in own_files}
        write("inputs-before.json", before)
        write("candidate-inputs-before.json", own_before)
        plan = focused_plan(root, focus)
        write("plan.json", plan)
        context = runtime_context.capture(android_package="android-37.0", require_clean=True)
        library.validate_webview_desktop_request_host(context["host"]["system"], context["host"]["architecture"], focus)
        probe.need(context["source_revision"] == revision and not context["source_tree_dirty"],
                   "Candidate requires the exact clean immutable development source")
        write("runtime.json", context)
        pins = probe.document((HERE / "artifacts.json").read_bytes())
        artifacts = output / "official-inputs"
        write("cache-reuse.json", seed_official_cache(artifacts, pins, Path.home(), classifier))
        manifest = candidate.build(argparse.Namespace(output=output / "runtime-candidate", artifact_dir=artifacts,
                                                      download=args.download))
        argv = command(root, plan, output, manifest)
        jar = output / "runtime-candidate" / manifest["jar_file"]
        moved = library.quarantine_reports(root, output, plan)
        receipt.update(source_revision=revision,command=argv,quarantined_prior_reports=moved,
                       candidate_manifest=manifest)
        started_ns = time.time_ns()
        execution = library.execute(root, argv, output / "gradle.log", 1800, 8192)
        ended_ns = time.time_ns()
        receipt.update(execution=execution,actual_jar_sha256_after=probe.digest(jar.read_bytes()))
        after = library.snapshot_inputs(root)
        own_after = {p.relative_to(root).as_posix(): probe.digest(p.read_bytes()) for p in own_files}
        write("inputs-after.json", after)
        write("candidate-inputs-after.json", own_after)
        receipt["held_inputs"] = (before == after and own_before == own_after and library.git_revision(root) == revision
                                  and receipt["actual_jar_sha256_after"] == manifest["jar_sha256"])
        markers = library.execution_markers(output / "gradle.log")
        receipt.update(library.collect_reports(root, plan, started_ns, ended_ns, markers,
                                               host_system=context["host"]["system"],native_ui_opt_in=False))
        receipt["library_tests"] = sum(m["executed"] for m in receipt["modules"])
        for module in receipt["modules"]:
            for report in module["reports"]:
                path = library.safe_path(root, report["path"])
                destination = output / "reports" / path.name
                destination.parent.mkdir(exist_ok=True)
                probe.need(not destination.exists(), "Duplicate original XML filename")
                shutil.copyfile(path, destination)
        receipt["full_JAR_runtime_replacement"] = marker(output / "gradle.log", manifest)
        receipt["gradle_daemon"] = daemon_jvm.observation(output / "gradle.log")
        probe.need(receipt["gradle_daemon"]["major"] == context["java"]["major"] == 17,
                   "Actual root daemon and setup Java majors differ")
        receipt["passed"] = (execution["exit_code"] == 0 and not execution.get("stop_reason") and
                             not receipt["errors"] and receipt["held_inputs"] and receipt["library_tests"] == 1)
    except Exception as error:
        receipt.update(passed=False,error_type=type(error).__name__,error=str(error))
        raise
    finally:
        receipt["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if output.is_dir():
            write("receipt.json", receipt)
        os.close(descriptor)
        lock.unlink()
        print(json.dumps(receipt, sort_keys=True))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New relative build/ci-verification output")
    parser.add_argument("--download", action="store_true", help="Acquire only missing fixed pinned official inputs")
    parser.add_argument("--platform", choices=PLATFORMS, default="windows",
                        help="Explicit failed-only host; never an architecture or route override")
    result = run(parser.parse_args())
    raise SystemExit(0 if result["passed"] else 1)
