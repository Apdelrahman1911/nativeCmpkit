"""Failure-only owned Android heap capture; raw heaps/parser binaries NEVER leave the runner.

Only the exact library test APK on the controller's live, name-verified AVD is
read. Output contains class/field/root identities and hashes, not heap values.
The parser hash is an earlier registry observation, NOT independent trust or a
release/supply-chain clearance. No device assertion is skipped or made green.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import urllib.request

PACKAGE = "com.mohamedrejeb.calf.calfwebview.test"
MARKER = "cache/nativecmpkit-owned-webview-heap/unmounted-media.complete.json"
DUMP = "cache/nativecmpkit-owned-webview-heap/unmounted-media.hprof"
PARSER_URL = "https://repo.maven.apache.org/maven2/org/graalvm/visualvm/modules/org-graalvm-visualvm-lib-jfluid-heap/2.2/org-graalvm-visualvm-lib-jfluid-heap-2.2.jar"
PARSER_SHA256 = "f34e6c97d3d5ff6fe5a6e206f2e6983ef8c8d23af6afd520bac9540d85a33dae"
PARSER_BYTES = 339684
MAX_DUMP_BYTES = 256 * 1024 * 1024
SOURCE = "scripts/ci/OwnedAndroidWebViewRoots.java"


def unique_json(raw: bytes) -> dict:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate diagnostic JSON key")
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite diagnostic JSON")))


def marker(raw: bytes) -> dict:
    if not 1 <= len(raw) <= 4096:
        raise ValueError("Bounded complete diagnostic marker required")
    value = unique_json(raw)
    if (not isinstance(value, dict) or set(value) != {"file", "bytes", "sha256"} or
            value["file"] != "unmounted-media.hprof" or type(value["bytes"]) is not int or
            not 32 <= value["bytes"] <= MAX_DUMP_BYTES or
            not isinstance(value["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"])):
        raise ValueError("Unexpected owned diagnostic marker; no arbitrary app/path reads")
    return value


def reviewed_analysis(raw: bytes) -> dict:
    if not 1 <= len(raw) <= 262144:
        raise ValueError("Unbounded or empty reviewed root identities")
    value = unique_json(raw)
    if (not isinstance(value, dict) or set(value) != {"schema_version", "scope", "raw_ids_or_values_exported", "targets"} or
            value["schema_version"] != 1 or value["raw_ids_or_values_exported"] is not False or
            value["scope"] != "Nearest heap root paths only; not all paths or native allocations" or
            not isinstance(value["targets"], list) or len(value["targets"]) > 32):
        raise ValueError("Unexpected class/field-only profiler output")
    identity = re.compile(r"[A-Za-z0-9_$/.;<>\[\]-]{1,512}\Z")
    for target in value["targets"]:
        if (not isinstance(target, dict) or set(target) != {"target_class", "nearest_path", "root_reached", "weak_reference_edge", "root_kinds"} or
                target["target_class"] not in {"android.webkit.WebView", "com.mohamedrejeb.calf.ui.web.WebViewLifetimeActivity"} or
                type(target["root_reached"]) is not bool or type(target["weak_reference_edge"]) is not bool or
                not isinstance(target["root_kinds"], list) or len(target["root_kinds"]) > 32 or
                not all(isinstance(kind, str) and re.fullmatch(r"[A-Za-z _-]{1,64}", kind) for kind in target["root_kinds"]) or
                not isinstance(target["nearest_path"], list) or len(target["nearest_path"]) > 64):
            raise ValueError("Unexpected native target/root shape")
        for edge in target["nearest_path"]:
            if (not isinstance(edge, dict) or set(edge) != {"child_class", "parent_class", "fields"} or
                    not all(isinstance(edge[k], str) and identity.fullmatch(edge[k]) for k in ("child_class", "parent_class")) or
                    not isinstance(edge["fields"], list) or len(edge["fields"]) > 128 or
                    not all(isinstance(field, str) and identity.fullmatch(field) for field in edge["fields"])):
                raise ValueError("Unexpected class/field edge; no arbitrary heap value export")
    return value


class OwnedHeap:
    def __init__(self, root: Path, output: Path, home: Path, serial: str, process, name: str, read_name):
        self.root, self.output, self.home = root.resolve(), output, home
        self.serial, self.process, self.name, self.read_name = serial, process, name, read_name
        if serial != "emulator-5588" or not re.fullmatch(r"nativecmpkit-api35-[0-9a-f]{12}", name):
            raise ValueError("Only the exact controller slot and freshly owned AVD name are permitted")
        self.stop = threading.Event()
        self.thread = None
        self.private = output / "private-webview-heap"
        self.record = {"schema_version": 1, "requested": True, "package": PACKAGE,
                       "raw_heap_or_parser_uploaded": False, "capture_found": False,
                       "scope": "Failure diagnostic only; never a passing native/memory/release gate"}

    def prepare(self) -> "OwnedHeap":
        allowed = self.root / "build/ci-verification"
        if (not self.private.resolve().is_relative_to(allowed) or
                any(p.is_symlink() for p in (self.private, *self.private.parents)) or self.private.exists()):
            raise ValueError("A new confined private diagnostic directory is required")
        if shutil.disk_usage(self.root).free < 8192 * 1024 * 1024:
            raise ValueError("Diagnostic must preserve the 8 GiB disk reserve")
        converter = self.home / "platform-tools/hprof-conv"
        if not converter.is_file() or not os.access(converter, os.X_OK):
            raise ValueError("Official installed Android heap converter is required")
        self.private.mkdir(mode=0o700)
        with urllib.request.urlopen(PARSER_URL, timeout=30) as response:
            if response.geturl() != PARSER_URL:
                raise ValueError("Unexpected parser acquisition redirect")
            payload = response.read(PARSER_BYTES + 1)
        if len(payload) != PARSER_BYTES or hashlib.sha256(payload).hexdigest() != PARSER_SHA256:
            raise ValueError("Observed parser size/hash mismatch; never execute it")
        parser = self.private / "parser.jar"
        parser.write_bytes(payload)
        source = self.root / SOURCE
        if not source.is_file() or source.is_symlink():
            raise ValueError("Current owned profiler source is missing")
        command = [str(Path(os.environ["JAVA_HOME"]) / "bin/javac"), "-cp", str(parser), "-d", str(self.private), str(source)]
        subprocess.run(command, check=True, capture_output=True, timeout=30)
        self.record.update(parser_sha256=PARSER_SHA256, parser_bytes=PARSER_BYTES,
                           parser_provenance="Earlier registry-observed exact bytes; not independent trust",
                           profiler_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                           installed_converter_sha256=hashlib.sha256(converter.read_bytes()).hexdigest())
        return self

    def owned(self) -> None:
        if self.process.poll() is not None or self.read_name(self.home) != self.name:
            raise ValueError("AVD ownership changed; never read a foreign device/app")

    def app_command(self, *arguments: str) -> list[str]:
        return [str(self.home / "platform-tools/adb"), "-s", self.serial, "shell", "run-as", PACKAGE, *arguments]

    def capture(self) -> None:
        try:
            while not self.stop.is_set():
                self.owned()
                result = subprocess.run(self.app_command("head", "-c", "4097", MARKER), capture_output=True, timeout=10)
                if result.returncode == 0:
                    value = marker(result.stdout)
                    self.owned()
                    dump = self.private / "owned-android.hprof"
                    with dump.open("xb") as stream:
                        transfer = subprocess.run(self.app_command("head", "-c", str(value["bytes"] + 1), DUMP),
                                                  stdout=stream, stderr=subprocess.DEVNULL, timeout=20)
                    if (transfer.returncode != 0 or dump.stat().st_size != value["bytes"] or
                            hashlib.sha256(dump.read_bytes()).hexdigest() != value["sha256"]):
                        raise ValueError("Incomplete or changed private heap transfer")
                    self.owned()
                    self.record.update(capture_found=True, dump_bytes=value["bytes"], dump_sha256=value["sha256"],
                                       owned_avd_verified_before_and_after=True)
                    return
                self.stop.wait(0.5) # The owned APK/marker may not have been installed/written yet.
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.record["capture_error"] = type(error).__name__ # No private stderr/body export.

    def start(self) -> "OwnedHeap":
        self.owned()
        self.thread = threading.Thread(target=self.capture, name="nativecmpkit-owned-heap-monitor", daemon=False)
        self.thread.start()
        return self

    def close(self) -> dict:
        self.stop.set()
        if self.thread is not None:
            self.thread.join(30)
        self.record["clean_monitor_shutdown"] = self.thread is None or not self.thread.is_alive()
        if self.record.get("capture_found") and not self.record.get("analysis_attempted"):
            self.record["analysis_attempted"] = True
            try:
                converter = self.home / "platform-tools/hprof-conv"
                converted = self.private / "converted.hprof"
                if converted.exists():
                    raise ValueError("Never overwrite a previous heap diagnostic")
                subprocess.run([str(converter), str(self.private / "owned-android.hprof"), str(converted)],
                               check=True, capture_output=True, timeout=30)
                command = [str(Path(os.environ["JAVA_HOME"]) / "bin/java"), "-Xmx1024m", "-cp",
                           str(self.private) + os.pathsep + str(self.private / "parser.jar"),
                           "OwnedAndroidWebViewRoots", str(converted)]
                result = subprocess.run(command, check=True, capture_output=True, timeout=120)
                self.record["analysis"] = reviewed_analysis(result.stdout)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                self.record["analysis_error"] = type(error).__name__
        if not self.record["clean_monitor_shutdown"]:
            self.record["capture_error"] = "OwnedMonitorShutdownTimeout"
        return self.record
