#!/usr/bin/env python3
"""Explicit PyPI checksum bootstrap from the isolated, already-tested docs graph.

Run with that environment's Python (packaging is required). This is not independent
checksum trust. It reads only named public distributions and official release
metadata, never runs/extracts a downloaded package, and never freezes unrelated
environment packages. Linux x64 / CPython3.12 is the declared lock scope.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import sys
import urllib.parse
import urllib.request

from packaging.requirements import Requirement
from packaging.tags import sys_tags
from packaging.utils import canonicalize_name, parse_wheel_filename

ROOT = Path(__file__).resolve().parents[2]
PIN = re.compile(r"([a-zA-Z0-9][a-zA-Z0-9_.-]*)==([0-9][a-zA-Z0-9_.+-]*)\Z")


def exact_pins(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN.fullmatch(line)
        if not match:
            raise ValueError("Direct documentation inputs require literal exact versions, not URLs/options/ranges")
        name = canonicalize_name(match.group(1))
        if name in result:
            raise ValueError("Duplicate direct documentation requirement")
        result[name] = match.group(2)
    if not result:
        raise ValueError("Empty direct documentation requirements")
    return result


def installed_graph(roots: dict[str, str]) -> dict[str, str]:
    pending = [Requirement(f"{name}=={version}") for name, version in roots.items()]
    result = {}
    while pending:
        requested = pending.pop()
        if requested.url or requested.extras:
            raise ValueError("Non-registry or extra-bearing dependency requires a deliberate lock-scope update")
        name = canonicalize_name(requested.name)
        dist = metadata.distribution(name)
        if not requested.specifier.contains(dist.version, prereleases=True):
            raise ValueError(f"Installed public distribution does not satisfy the reviewed constraint: {name}")
        if name in result:
            continue
        result[name] = dist.version
        for entry in dist.requires or []:
            dependency = Requirement(entry)
            if not dependency.marker or dependency.marker.evaluate({"extra": ""}):
                pending.append(dependency)
    return dict(sorted(result.items()))


def registry_release(name: str, version: str) -> dict:
    url = f"https://pypi.org/pypi/{urllib.parse.quote(name)}/{urllib.parse.quote(version)}/json"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nativeCmpkit-docs-lock-bootstrap"}), timeout=30) as response:
        payload = response.read(4 * 1024 * 1024 + 1)
    if len(payload) > 4 * 1024 * 1024:
        raise ValueError("Registry metadata exceeds bounded input size")
    release = json.loads(payload)
    if canonicalize_name(release["info"]["name"]) != name or release["info"]["version"] != version:
        raise ValueError("Registry identity differs from the exact requested package")
    return release


def select_artifact(name: str, version: str, release: dict) -> dict:
    supported = {tag: position for position, tag in enumerate(sys_tags())}
    candidates = []
    for item in release["urls"]:
        if item.get("yanked"):
            continue
        url = urllib.parse.urlsplit(item["url"])
        digest = item["digests"]["sha256"]
        if url.scheme != "https" or url.hostname != "files.pythonhosted.org" or url.username or url.password:
            raise ValueError("Unexpected package artifact origin")
        if not re.fullmatch(r"[0-9a-f]{64}", digest) or "/" in item["filename"] or "\\" in item["filename"]:
            raise ValueError("Invalid public package filename/checksum")
        if item["packagetype"] == "bdist_wheel":
            wheel_name, wheel_version, _, tags = parse_wheel_filename(item["filename"])
            if canonicalize_name(wheel_name) != name or str(wheel_version) != version:
                raise ValueError("Wheel identity differs from release identity")
            ranks = [supported[tag] for tag in tags if tag in supported]
            if not ranks:
                continue
            rank = min(ranks)
        elif item["packagetype"] == "sdist":
            rank = 100000
        else:
            continue
        candidates.append((rank, item["filename"], item))
    if not candidates:
        raise ValueError(f"No compatible public artifact for {name}=={version}")
    item = sorted(candidates, key=lambda row: row[:2])[0][2]
    return {"name": name, "version": version, "filename": item["filename"], "url": item["url"],
            "sha256": item["digests"]["sha256"], "packagetype": item["packagetype"],
            "requires_python": item.get("requires_python"), "upload_time_utc": item.get("upload_time_iso_8601")}


def bootstrap() -> dict:
    if platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"} or sys.version_info[:2] != (3, 12):
        raise ValueError("This lock bootstrap is scoped to Linux x64 CPython3.12")
    graph = installed_graph(exact_pins(ROOT / "requirements/docs.in"))
    build = exact_pins(ROOT / "requirements/docs-build.in")
    combined = dict(graph)
    for name, version in build.items():
        if name in combined and combined[name] != version:
            raise ValueError("Bootstrap backend conflicts with the observed runtime graph")
        combined[name] = version
    artifacts = []
    for name, version in sorted(combined.items()):
        release = registry_release(name, version)
        if name in build:
            for text in release["info"].get("requires_dist") or []:
                dependency = Requirement(text)
                if dependency.marker and not dependency.marker.evaluate({"extra": ""}):
                    continue
                if dependency.url or dependency.extras or canonicalize_name(dependency.name) not in build or not dependency.specifier.contains(build[canonicalize_name(dependency.name)], prereleases=True):
                    raise ValueError("The pinned bootstrap backend has an unpinned active dependency")
        artifact = select_artifact(name, version, release)
        artifact["roles"] = [role for role, entries in (("docs", graph), ("build", build)) if name in entries]
        if "build" in artifact["roles"] and artifact["packagetype"] != "bdist_wheel":
            raise ValueError("Bootstrap tools themselves must not need an unpinned source build")
        artifacts.append(artifact)
    return {"schema_version": 1, "observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "scope": "Linux x64 CPython3.12 documentation/build graphs; no publishing authorization",
            "trust": "Checksums acquired from official registry metadata as bootstrap observations, not independently trusted provenance",
            "independent_trust_reviewed": False, "artifacts": artifacts}


def lock_text(result: dict, role: str) -> str:
    lines = ["# Linux x64 / CPython3.12; generated by scripts/docs/bootstrap_lock.py.",
             "# Official-registry checksum bootstrap, NOT independent provenance.",
             "# Use the isolated installer; source-only minifiers need the pinned build backend.", ""]
    lines += [f"{item['name']}=={item['version']} --hash=sha256:{item['sha256']}"
              for item in result["artifacts"] if role in item["roles"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Explicitly replace documentation lock/provenance outputs after reviewing the isolated installed graph")
    args = parser.parse_args()
    result = bootstrap()
    if args.write:
        for role, name in (("docs", "docs-linux-py312.lock"), ("build", "docs-build.lock")):
            path = ROOT / "requirements" / name
            path.write_text(lock_text(result, role))
        result["input_sha256"] = {name: hashlib.sha256((ROOT / "requirements" / name).read_bytes()).hexdigest()
                                   for name in ("docs.in", "docs-build.in", "docs-linux-py312.lock", "docs-build.lock")}
        (ROOT / "requirements/docs-lock-provenance.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"write_requested": args.write, "artifact_count": len(result["artifacts"]),
                      "source_only": [item["name"] for item in result["artifacts"] if item["packagetype"] == "sdist"],
                      "independent_trust_reviewed": False}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
