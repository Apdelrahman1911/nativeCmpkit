#!/usr/bin/env python3
"""Nine real Linux child-JVM executions at privileged, owned native-cache boundaries.

Requires explicit prepared desktopTestClasses/classpath, root and mount/chown capability.
Runs no dialogs, packages or releases. No emulation/fake native bridge, or default
JUnit skip/pass: an unavailable fixture or failed child is a failed command.
Private arguments/logs/witness paths remain under the requested output/test roots.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PROBE = "com.mohamedrejeb.calf.picker.platform.NativeLoaderBoundaryProbe"
MODES = ("foreign-cache", "noexec", "loaded", "read-only-home", "missing-home", "bad-abi", "bundled-preference")


def command(argv: list[str], cwd: Path, log: Path, timeout: int = 30) -> dict:
    started = dt.datetime.now(dt.timezone.utc)
    with log.open("xb") as output:
        process = subprocess.Popen(argv, cwd=cwd, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
    return {"exit_code": code, "pid": process.pid, "started_utc": started.isoformat(),
            "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "private_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}


def mount_options(path: Path) -> set[str]:
    lines = [line.split() for line in Path("/proc/self/mountinfo").read_text().splitlines()]
    matches = [parts for parts in lines if parts[4] == str(path)]
    assert len(matches) == 1, "Require exactly the actual owned mount, not an ancestor/guessed flag"
    return set(matches[0][5].split(","))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classpath-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert os.geteuid() == 0 and Path("/proc/self/mountinfo").is_file(), "Explicit real Linux privileged fixtures are required"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chmod(output, 0o700)
    cpfile = args.classpath_file.resolve(strict=True)
    assert cpfile.stat().st_size < 4 * 1024 * 1024
    paths = [Path(line) for line in cpfile.read_text().splitlines()]
    assert paths and all(path.is_absolute() for path in paths)
    paths = [path for path in paths if path.exists()]
    assert any((path / (PROBE.replace(".", "/") + ".class")).is_file() for path in paths if path.is_dir())
    classpath = os.pathsep.join(map(str, paths))
    arch = {"x86_64": "x64", "aarch64": "arm64"}[os.uname().machine]
    resource = f"native/linux-{arch}/libcalf_filepicker_native.so"
    payload = None
    for path in paths:
        if path.is_dir() and (path / resource).is_file():
            payload = (path / resource).read_bytes()
            break
        if path.is_file() and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                if resource in archive.namelist():
                    payload = archive.read(resource)
                    break
    assert payload is not None and payload.startswith(b"\x7fELF"), "Actual compiled host resource is required"
    digest = hashlib.sha256(payload).hexdigest()
    identity = f"libcalf_filepicker_native-{digest[:16]}.so"
    root = Path(tempfile.mkdtemp(prefix="nativecmpkit-picker-boundaries-", dir="/tmp")).resolve()
    shared = root / "shared-temp"
    shared.mkdir(mode=0o700)
    os.chmod(shared, 0o1777)
    legacy = shared / ".cache/calf-filepicker"
    legacy.mkdir(parents=True)
    sentinel = legacy / "not-a-library"
    sentinel.write_bytes(b"legacy-untrusted-data-must-stay-unchanged")
    external = root / "empty-system-path"
    external.mkdir(mode=0o700)
    mount = root / "owned-mount"
    mount.mkdir(mode=0o700)
    runs = []
    fixtures = []
    passed = False
    mounted = False
    cleanup_ok = False
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

    def jvm(mode: str, label: str, home: Path, system: Path = external, trust: bool = False) -> dict:
        assert mode in MODES
        witness = root / f"{label}.properties"
        argfile = root / f"{label}.java-args"
        argv = ["-Xmx128m", "-Xcheck:jni", "-ea", f"-Duser.home={home}", f"-Djava.io.tmpdir={shared}",
                f"-Djava.library.path={system}", f"-Dnativecmpkit.picker.trustSystemLibrary={str(trust).lower()}",
                "-classpath", classpath, PROBE, mode, str(witness)]
        quote = lambda value: '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
        argfile.write_text("\n".join(map(quote, argv)) + "\n")
        result = command(["java", "@" + str(argfile)], ROOT, output / f"{label}.private.log")
        assert result["exit_code"] == 0, f"{label}: actual native probe failed; inspect retained owned diagnostic"
        log = (output / f"{label}.private.log").read_text()
        assert log.strip() == f"NATIVECMPKIT_PICKER_BOUNDARY {mode} verified"
        props = dict(line.split("=", 1) for line in witness.read_text().splitlines() if line and not line.startswith("#"))
        assert props["mode"] == mode and props["digest"] == digest and props["pid"] == str(result["pid"])
        result.update(mode=mode, label=label, actual_JVM=True, actual_production_loader=True,
                      native_image_sha256=digest, fake_bridge=False)
        if "path" in props:
            image = Path(props["path"])
            assert image.is_file() and not image.is_symlink() and image.read_bytes() == payload
            result["private_image_path"] = str(image)
            result["actual_image_inode"] = image.stat().st_ino
            if mode in {"read-only-home", "missing-home"}:
                assert image.parent.parent == shared and image.parent.name.startswith("nativecmpkit-filepicker-")
                assert image.parent.stat().st_mode & 0o777 == 0o700
                assert image.stat().st_uid == image.parent.stat().st_uid == os.geteuid()
                result["actual_private_fallback_owner_and_mode"] = True
        runs.append(result)
        return result

    try:
        foreign_home = root / "foreign-home"
        foreign_cache = foreign_home / ".cache/nativecmpkit-filepicker"
        foreign_cache.mkdir(parents=True, mode=0o700)
        os.chown(foreign_cache, 65534, 65534)
        assert foreign_cache.stat().st_uid != os.geteuid()
        jvm("foreign-cache", "foreign-cache", foreign_home)
        assert not list(foreign_cache.iterdir())
        os.chown(foreign_cache, os.geteuid(), os.getegid())

        result = command(["mount", "-t", "tmpfs", "-o", "noexec,size=32m,mode=0700",
                          "nativecmpkit-owned-native-fixture", str(mount)], ROOT, output / "mount.private.log", 10)
        assert result["exit_code"] == 0
        mounted = True
        assert os.path.ismount(mount) and "noexec" in mount_options(mount)
        fixtures.append({"kind": "actual-owned-noexec-tmpfs", "size_limit_mib": 32, "options": sorted(mount_options(mount))})
        noexec_home = mount / "noexec-home"
        noexec_home.mkdir(mode=0o700)
        denied = jvm("noexec", "noexec", noexec_home)
        assert (noexec_home / ".cache/nativecmpkit-filepicker" / identity).is_file()
        result = command(["mount", "-o", "remount,exec", str(mount)], ROOT, output / "exec-remount.private.log", 10)
        assert result["exit_code"] == 0 and "noexec" not in mount_options(mount)
        recovered = jvm("loaded", "exec-recovery", noexec_home)
        assert denied["private_image_path"] == recovered["private_image_path"]
        assert denied["actual_image_inode"] == recovered["actual_image_inode"]

        ro_home = mount / "readonly-home"
        ro_home.mkdir(mode=0o700)
        result = command(["mount", "-o", "remount,ro", str(mount)], ROOT, output / "ro-remount.private.log", 10)
        assert result["exit_code"] == 0 and "ro" in mount_options(mount)
        try:
            (ro_home / "real-readonly-precondition").write_bytes(b"test-only")
            raise AssertionError("Actual root must not bypass a read-only mount")
        except OSError as error:
            assert error.errno == 30
        fixtures.append({"kind": "actual-owned-readonly-tmpfs", "write_errno": 30, "root_did_not_bypass": True,
                         "options": sorted(mount_options(mount))})
        ro_one = jvm("read-only-home", "readonly-first", ro_home)
        ro_two = jvm("read-only-home", "readonly-second", ro_home)
        assert ro_one["private_image_path"] != ro_two["private_image_path"]
        assert not (ro_home / ".cache").exists()

        absent_home = root / "absent-home"
        absent_home.mkdir(mode=0o700)
        one = jvm("missing-home", "missing-first", absent_home)
        two = jvm("missing-home", "missing-second", absent_home)
        assert one["private_image_path"] != two["private_image_path"]
        assert sentinel.read_bytes() == b"legacy-untrusted-data-must-stay-unchanged" and len(list(legacy.iterdir())) == 1

        source = ROOT / "calf-file-picker/src/desktopTest/resources/NativeRejectedAbiPayload.rs"
        channel = re.search(r'(?m)^channel\s*=\s*"([0-9.]+)"', (ROOT / "rust-toolchain.toml").read_text()).group(1)
        rust = command(["rustc", "--version"], ROOT, output / "rust-version.private.log", 10)
        assert rust["exit_code"] == 0 and (output / "rust-version.private.log").read_text().startswith("rustc " + channel + " ")
        bad = root / "bad-system-path"
        bad.mkdir(mode=0o700)
        library = bad / "libcalf_filepicker_native.so"
        compiled = command(["rustc", "--edition=2021", "--crate-type=cdylib", "--crate-name", "nativecmpkit_bad_abi_fixture",
                            "-C", "panic=abort", "-C", "opt-level=2", str(source), "-o", str(library)], ROOT,
                           output / "bad-abi-rust.private.log")
        assert compiled["exit_code"] == 0 and library.read_bytes().startswith(b"\x7fELF")
        fixtures.append({"kind": "real-independently-compiled-ABI2-JNI-test-payload", "rust": channel,
                         "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                         "payload_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
                         "not_a_released_payload": True})
        bad_home = root / "bad-abi-home"
        bad_home.mkdir(mode=0o700)
        jvm("bad-abi", "bad-abi", bad_home, bad, True)
        bundled = root / "bundled-preference-home"
        bundled.mkdir(mode=0o700)
        jvm("bundled-preference", "bundled-preference", bundled, bad, False)
        assert len(runs) == 9 and len({r["pid"] for r in runs}) == 9
        passed = True
    finally:
        if mounted:
            unmounted = command(["umount", str(mount)], ROOT, output / "unmount.private.log", 10)
            cleanup_ok = unmounted["exit_code"] == 0 and not os.path.ismount(mount)
        else:
            cleanup_ok = not os.path.ismount(mount)
        receipt = {"source_revision": revision, "passed": passed and cleanup_ok, "actual_child_JVM_executions": len(runs),
                   "distinct_authored_scenarios": len({r["mode"] for r in runs}), "JUnit_executions": 0,
                   "fixture_root_private_name": root.name, "owned_mount_unmounted": cleanup_ok,
                   "existing_mounts_changed": False, "fixtures": fixtures, "runs": runs,
                   "raw_logs_arguments_paths_private": True, "packages_releases_deployments_published": False}
        (output / "receipt.private.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if passed and cleanup_ok:
            import shutil
            shutil.rmtree(root)
        else:
            print("Native boundary failure retained in its owned private test/output roots; no native/release gate passed.")
    assert passed and cleanup_ok
    print(json.dumps({k: receipt[k] for k in ("source_revision", "passed", "actual_child_JVM_executions", "distinct_authored_scenarios", "JUnit_executions", "owned_mount_unmounted", "packages_releases_deployments_published")}, indent=2))
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    raise SystemExit(main())
