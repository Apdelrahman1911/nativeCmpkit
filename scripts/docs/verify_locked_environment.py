#!/usr/bin/env python3
"""Download/check exact docs artifacts, install offline, and reject a wrong hash.

Scope: Linux x64 CPython3.12. New project-owned output only; no deployment,
system Python changes, shared cache writes, or implicit lock regeneration.
Registry-bootstrap hashes are TOFU, not independent provenance review.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
LOCK = re.compile(r"([a-z0-9][a-z0-9.-]*)==([0-9][a-zA-Z0-9_.+-]*) --hash=sha256:([0-9a-f]{64})\Z")
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_entries(path: Path) -> dict[str, tuple[str, str]]:
    result = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = LOCK.fullmatch(line)
        if not match or match[1] in result:
            raise ValueError("Expected unique exact package pins with one SHA256 each")
        result[match[1]] = (match[2], match[3])
    if not result:
        raise ValueError("Empty hash lock")
    return result


def validate_provenance(root: Path = ROOT) -> dict:
    data = json.loads((root / "requirements/docs-lock-provenance.json").read_text())
    if data.get("schema_version") != 1 or data.get("independent_trust_reviewed") is not False:
        raise ValueError("Unexpected bootstrap provenance schema/trust claim")
    required_inputs = {"docs.in", "docs-build.in", "docs-linux-py312.lock", "docs-build.lock"}
    if set(data.get("input_sha256", {})) != required_inputs:
        raise ValueError("Incomplete/unexpected provenance inputs")
    for name, expected in data["input_sha256"].items():
        if digest(root / "requirements" / name) != expected:
            raise ValueError("Documentation input changed without explicit lock bootstrap")
    artifacts = data.get("artifacts", [])
    if not 1 <= len(artifacts) <= 100:
        raise ValueError("Unexpected artifact count")
    seen_names, seen_files = set(), set()
    for item in artifacts:
        name, filename = item["name"], item["filename"]
        url = urllib.parse.urlsplit(item["url"])
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", name) or name in seen_names:
            raise ValueError("Unsafe/duplicate package name")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", filename) or filename in seen_files:
            raise ValueError("Unsafe/duplicate artifact filename")
        if url.scheme != "https" or url.netloc != "files.pythonhosted.org" or url.query or url.fragment or urllib.parse.unquote(url.path.rsplit("/", 1)[-1]) != filename:
            raise ValueError("Artifact must be the exact official HTTPS registry URL")
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise ValueError("Invalid artifact digest")
        if item["packagetype"] not in {"bdist_wheel", "sdist"} or not item["roles"] or set(item["roles"]) - {"build", "docs"}:
            raise ValueError("Unknown artifact type/role")
        if "build" in item["roles"] and item["packagetype"] != "bdist_wheel":
            raise ValueError("Build-tool bootstrap cannot execute source packages")
        seen_names.add(name)
        seen_files.add(filename)
    for role, filename in (("docs", "docs-linux-py312.lock"), ("build", "docs-build.lock")):
        actual = lock_entries(root / "requirements" / filename)
        expected = {x["name"]: (x["version"], x["sha256"]) for x in artifacts if role in x["roles"]}
        if actual != expected:
            raise ValueError("Lock graph and provenance differ")
    return data


def verify_bytes(path: Path, expected: str) -> None:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_ARTIFACT_BYTES:
        raise ValueError("Unsafe/oversized documentation artifact")
    if digest(path) != expected:
        raise ValueError("Documentation artifact SHA256 mismatch; no installation attempted")


def download(item: dict, destination: Path) -> dict:
    request = urllib.request.Request(item["url"], headers={"User-Agent": "nativeCmpkit-docs-hash-verification"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.geturl() != item["url"]:
            raise ValueError("Unexpected artifact redirect")
        with destination.open("xb") as output:
            total = 0
            while chunk := response.read(256 * 1024):
                total += len(chunk)
                if total > MAX_ARTIFACT_BYTES:
                    raise ValueError("Artifact exceeds download budget")
                output.write(chunk)
    verify_bytes(destination, item["sha256"])
    return {"name": item["name"], "version": item["version"], "filename": item["filename"], "bytes": total, "sha256": item["sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New directory below build/docs-verification/")
    parser.add_argument("--build", action="store_true", help="Also run local strict MkDocs build; never deploy")
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"} or sys.version_info[:2] != (3, 12):
        raise ValueError("Lock scope is Linux x64 CPython3.12 only")
    allowed = ROOT / "build/docs-verification"
    allowed.mkdir(parents=True, exist_ok=True)
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(allowed.resolve()) or output == allowed.resolve() or output.exists():
        raise ValueError("Verification output must be a new project-owned build/docs-verification child")
    data = validate_provenance()
    output.mkdir(parents=True)
    wheelhouse = output / "wheelhouse"
    wheelhouse.mkdir()
    receipt = {"schema_version": 1, "scope": data["scope"], "independent_trust_reviewed": False,
               "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "result": "failed",
               "strict_mkdocs_build_requested": args.build,
               "input_sha256": {**data["input_sha256"], "docs-lock-provenance.json": digest(ROOT / "requirements/docs-lock-provenance.json")},
               "artifacts": [], "commands": []}
    (output / "home").mkdir()
    (output / "tmp").mkdir()
    # Source-only minifiers execute their hashed build backend. Do not hand that
    # code arbitrary caller credentials/config/environment or shared pip caches.
    # These controls are not a network/process security sandbox.
    env = {"PATH": str(output / "venv/bin") + os.pathsep + os.defpath,
           "HOME": str(output / "home"), "TMPDIR": str(output / "tmp"), "LANG": "C.UTF-8",
           "PIP_CONFIG_FILE": os.devnull, "PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PYTHONNOUSERSITE": "1"}
    started = time.monotonic()

    def run(name: str, command: list[str], expected: int = 0) -> str:
        remaining = max(1, int(300 - (time.monotonic() - started)))
        with (output / f"{name}.log").open("w") as log:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                receipt["commands"].append({"name": name, "exit_code": process.returncode, "timed_out": True})
                raise RuntimeError(f"{name} reached the bounded documentation verification timeout")
        receipt["commands"].append({"name": name, "exit_code": process.returncode, "expected_exit_code": expected})
        text = (output / f"{name}.log").read_text()
        if process.returncode != expected:
            raise RuntimeError(f"{name} failed: inspect retained log (exit {process.returncode})")
        return text

    try:
        for item in data["artifacts"]:
            if time.monotonic() - started > 240 or shutil.disk_usage(ROOT).free < 8 * 1024**3:
                raise RuntimeError("Documentation download time/disk reserve reached")
            receipt["artifacts"].append(download(item, wheelhouse / item["filename"]))
        run("venv", [sys.executable, "-I", "-m", "venv", str(output / "venv")])
        python = str(output / "venv/bin/python")
        pip = [python, "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "--no-cache-dir"]
        offline = ["--no-index", "--find-links", str(wheelhouse), "--require-hashes"]
        run("build-tools-install", [*pip, "install", *offline, "--only-binary=:all:", "-r", str(ROOT / "requirements/docs-build.lock")])
        run("docs-install", [*pip, "install", *offline, "--no-build-isolation", "-r", str(ROOT / "requirements/docs-linux-py312.lock")])
        run("pip-check", [*pip, "check"])
        # Actual pip rejection, not a synthetic return code or corrupted shared cache.
        probe = next(x for x in data["artifacts"] if x["packagetype"] == "bdist_wheel" and "docs" in x["roles"])
        wrong = output / "wrong-hash.lock"
        wrong.write_text(f"{probe['name']}=={probe['version']} --hash=sha256:{'0' * 64}\n")
        text = run("wrong-hash-rejection", [*pip, "download", *offline, "--no-deps", "--dest", str(output / "tamper-download"), "-r", str(wrong)], expected=1)
        if "THESE PACKAGES DO NOT MATCH THE HASHES" not in text or probe["sha256"] not in text:
            raise RuntimeError("Pip failed for another reason; hash rejection NOT established")
        receipt["actual_pip_wrong_hash_rejected"] = True
        versions = run("installed-versions", [python, "-I", "-c", "import importlib.metadata as m,json;print(json.dumps({d.metadata['Name'].lower().replace('_','-'):d.version for d in m.distributions()},sort_keys=True))"])
        receipt["installed_versions"] = json.loads(versions)
        expected_versions = {x["name"]: x["version"] for x in data["artifacts"]}
        if receipt["installed_versions"] != expected_versions:
            raise RuntimeError("Installed isolated environment differs from exact locked graph")
        if args.build:
            run("mkdocs-strict", [python, "-I", "-m", "mkdocs", "build", "--strict", "--site-dir", str(output / "site")])
        receipt["result"] = "passed"
    finally:
        after = {name: digest(ROOT / "requirements" / name) for name in receipt["input_sha256"]}
        receipt["inputs_unchanged"] = after == receipt["input_sha256"]
        if not receipt["inputs_unchanged"]:
            receipt["result"] = "failed"
        receipt["elapsed_seconds"] = round(time.monotonic() - started, 2)
        receipt["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    if not receipt["inputs_unchanged"]:
        raise RuntimeError("Documentation lock/provenance changed during verification")
    print(json.dumps({"result": receipt["result"], "artifacts": len(receipt["artifacts"]), "actual_pip_wrong_hash_rejected": receipt.get("actual_pip_wrong_hash_rejected", False), "independent_trust_reviewed": False}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
