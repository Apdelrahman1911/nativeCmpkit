#!/usr/bin/env python3
"""Supplemental JVM artifact ABI snapshot/diff using the installed JDK's javap.

Kotlin internal declarations may be JVM-public, so this is intentionally an
over-approximation. No Kotlin metadata/default/inline semantics, Apple/Swift,
Android-specific API or native ABI compatibility is certified by this tool.
Use compiler ABI dumps and real old-consumer/new-artifact tests as additional gates.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from verify_artifacts import InvalidArtifact, archive_names, load_json_bytes, sha256


def parse_javap(text: str) -> dict[str, dict]:
    classes = {}
    current = None
    member = None
    exported = False
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if line.startswith("Compiled from ") or not line:
            continue
        if line.endswith("{") and re.search(r"\b(?:class|interface|enum)\s", line):
            match = re.search(r"\b(?:class|interface|enum)\s+([\w.$]+)", line)
            if not match:
                raise InvalidArtifact("Unrecognized javap class header")
            current = match.group(1)
            exported = line.startswith(("public ", "protected "))
            if exported:
                if current in classes:
                    raise InvalidArtifact("Duplicate class in javap output")
                classes[current] = {"declaration": line[:-1].rstrip(), "members": []}
            member = None
        elif line == "}":
            current, member, exported = None, None, False
        elif exported and current and line.startswith(("public ", "protected ")):
            member = {"declaration": line, "descriptor": None}
            classes[current]["members"].append(member)
        elif exported and line.startswith("descriptor:"):
            if member is None:
                raise InvalidArtifact("javap descriptor without member")
            member["descriptor"] = line.partition(":")[2].strip()
    for name, cls in classes.items():
        if any(not member["descriptor"] for member in cls["members"]):
            raise InvalidArtifact("Incomplete javap descriptor for " + name)
        cls["members"].sort(key=lambda member: (member["declaration"], member["descriptor"]))
    return dict(sorted(classes.items()))


def snapshot_jars(jars: dict[str, Path], revision: str, provenance: str, javap: str = "javap") -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise InvalidArtifact("A full expected source commit is required; it is not automatically proven by JAR bytes")
    if not jars:
        raise InvalidArtifact("No artifacts selected")
    artifacts = {}
    version = subprocess.run([javap, "-version"], capture_output=True, text=True, check=True, timeout=30)
    for artifact, path in sorted(jars.items()):
        path = path.resolve()
        with zipfile.ZipFile(path) as archive:
            names = archive_names(archive)
        classes = sorted(name[:-6].replace("/", ".") for name in names
                         if name.endswith(".class") and not name.startswith("META-INF/")
                         and name.startswith(("com/mohamedrejeb/calf/", "jodd/")))
        if not classes:
            # Some valid aggregation artifacts contain no own classes; retain explicit zero count.
            api = {}
        else:
            text = []
            # Bound argument size without losing descriptor members across chunks.
            for start in range(0, len(classes), 100):
                result = subprocess.run([javap, "-classpath", str(path), "-protected", "-s", "-constants", *classes[start:start + 100]],
                                        capture_output=True, text=True, timeout=180)
                if result.returncode:
                    raise InvalidArtifact("javap failed for " + artifact)
                text.append(result.stdout)
            api = parse_javap("\n".join(text))
        artifacts[artifact] = {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path),
                               "class_count_inspected": len(classes), "exported_class_count": len(api), "classes": api}
    return {"schema_version": 1, "expected_source_revision": revision, "provenance": provenance,
            "observed_utc": datetime.now(timezone.utc).isoformat(), "javap_version": version.stdout.strip(),
            "scope": __doc__.strip(), "artifacts": artifacts}


def compare(before: dict, after: dict) -> dict:
    removals, additions, changes = [], [], []
    before_artifacts, after_artifacts = before["artifacts"], after["artifacts"]
    for artifact in sorted(set(before_artifacts) | set(after_artifacts)):
        if artifact not in after_artifacts:
            removals.append({"artifact": artifact, "kind": "artifact"})
            continue
        if artifact not in before_artifacts:
            additions.append({"artifact": artifact, "kind": "artifact"})
            continue
        old, new = before_artifacts[artifact]["classes"], after_artifacts[artifact]["classes"]
        for name in sorted(set(old) | set(new)):
            symbol = {"artifact": artifact, "class": name}
            if name not in new:
                removals.append(symbol | {"kind": "class"})
                continue
            if name not in old:
                additions.append(symbol | {"kind": "class"})
                continue
            if old[name]["declaration"] != new[name]["declaration"]:
                changes.append(symbol | {"kind": "class-declaration", "before": old[name]["declaration"], "after": new[name]["declaration"]})
            old_members = {(item["declaration"], item["descriptor"]) for item in old[name]["members"]}
            new_members = {(item["declaration"], item["descriptor"]) for item in new[name]["members"]}
            for declaration, descriptor in sorted(old_members - new_members):
                removals.append(symbol | {"kind": "member", "declaration": declaration, "descriptor": descriptor})
            for declaration, descriptor in sorted(new_members - old_members):
                additions.append(symbol | {"kind": "member", "declaration": declaration, "descriptor": descriptor})
    return {"schema_version": 1, "scope": "JVM javap exported-surface delta requiring review; not complete KMP compatibility",
            "before_revision": before.get("expected_source_revision"), "after_revision": after.get("expected_source_revision"),
            "removals": removals, "additions": additions, "declaration_changes": changes,
            "no_removed_or_changed_exported_surface": not removals and not changes,
            "binary_compatibility_certified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("snapshot")
    capture.add_argument("--jar", action="append", required=True, help="artifact-name=/absolute/file.jar, repeat for each artifact")
    capture.add_argument("--revision", required=True)
    capture.add_argument("--provenance", required=True, help="Inspected build/source receipt or explicitly supplemental preexisting-output scope")
    capture.add_argument("--javap", default="javap")
    capture.add_argument("--output", type=Path, required=True)
    diff = sub.add_parser("compare")
    diff.add_argument("--before", type=Path, required=True)
    diff.add_argument("--after", type=Path, required=True)
    diff.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            pairs = [argument.partition("=") for argument in args.jar]
            if any(not separator or not artifact or not filename for artifact, separator, filename in pairs):
                raise InvalidArtifact("--jar requires artifact=path")
            if len({artifact for artifact, _, _ in pairs}) != len(pairs):
                raise InvalidArtifact("Duplicate selected artifact")
            result = snapshot_jars({artifact: Path(filename) for artifact, _, filename in pairs}, args.revision, args.provenance, args.javap)
            status = 0
        else:
            result = compare(load_json_bytes(args.before.read_bytes()), load_json_bytes(args.after.read_bytes()))
            # Additions remain reviewable but do not remove the previous JVM surface.
            status = 0 if result["no_removed_or_changed_exported_surface"] else 1
    except (InvalidArtifact, OSError, subprocess.SubprocessError, zipfile.BadZipFile, KeyError, TypeError) as exc:
        result, status = {"error": str(exc), "binary_compatibility_certified": False}, 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"exit": status, "output": str(args.output), "binary_compatibility_certified": False}))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
