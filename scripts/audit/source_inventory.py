#!/usr/bin/env python3
"""Reproduce a source-level inventory without executing the project build.

The input is an immutable Git tree, not the (possibly concurrently edited) worktree.
Declaration extraction is deliberately lexical, NOT a Kotlin compiler, API dump,
control-flow analysis, or evidence of semantic review. Comments and literal strings
are masked first. Local declarations and primary-constructor properties are included;
anonymous functions/objects, implicit accessors and generated build output are not.
Expect/actual links are same-module/name candidates, not compiler-verified pairings.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tomllib


BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
ROOT = Path(__file__).resolve().parents[2]
TARGETS = ["android", "desktop", "js", "wasmJs", "iosArm64", "iosSimulatorArm64"]
SOURCE_TARGETS = {
    "commonMain": TARGETS,
    "commonTest": TARGETS,
    "materialMain": ["android", "desktop", "js", "wasmJs"],
    "nonAndroidMain": ["desktop", "js", "wasmJs", "iosArm64", "iosSimulatorArm64"],
    "webMain": ["js", "wasmJs"],
    "iosMain": ["iosArm64", "iosSimulatorArm64"],
    "androidMain": ["android"],
    "desktopMain": ["desktop"],
    "desktopTest": ["desktop"],
    "jsMain": ["js"],
    "wasmJsMain": ["wasmJs"],
}
AREA = {
    "audit_ui": "calf-ui",
    "audit_io_picker": "calf-io calf-file-picker calf-file-picker-coil",
    "audit_permissions_geo": "calf-permissions calf-geo",
    "audit_native_features": "calf-webview calf-camera-picker calf-share calf-maps calf-media calf-notifications",
    "audit_navigation_core_icons": "calf-core calf-navigation calf-cupertino-icons sample",
}
SOURCE_EXTENSIONS = {".kt", ".kts", ".rs", ".swift", ".h", ".m", ".c", ".cpp"}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def masked(text: str) -> str:
    """Mask Kotlin/Rust comments and string literals while retaining offsets/lines."""
    result = list(text)
    i, n = 0, len(text)
    while i < n:
        end = i
        if text.startswith("//", i):
            end = text.find("\n", i)
            if end < 0:
                end = n
        elif text.startswith("/*", i):
            depth, end = 1, i + 2
            while end < n and depth:
                if text.startswith("/*", end):
                    depth, end = depth + 1, end + 2
                elif text.startswith("*/", end):
                    depth, end = depth - 1, end + 2
                else:
                    end += 1
        elif text.startswith('"""', i):
            close = text.find('"""', i + 3)
            end = n if close < 0 else close + 3
        elif text[i] == '"':
            end = i + 1
            while end < n:
                if text[end] == "\\":
                    end += 2
                elif text[end] == '"':
                    end += 1
                    break
                else:
                    end += 1
        elif text[i] == "'":
            # Kotlin char literal, not a Rust lifetime such as 'a or 'static.
            m = re.match(r"'(?:\\(?:u[0-9a-fA-F]{4}|.)|[^'\n\\])'", text[i:])
            if m:
                end = i + len(m.group())
        if end > i:
            for j in range(i, min(end, n)):
                if result[j] not in "\r\n":
                    result[j] = " "
            i = end
        else:
            i += 1
    return "".join(result)


def declarations(text: str, suffix: str) -> list[dict]:
    clean = masked(text)
    newline_offsets = [-1] + [m.start() for m in re.finditer("\n", clean)]
    result = []
    if suffix in {".kt", ".kts"}:
        pattern = r"\b(fun\s+interface|enum\s+class|annotation\s+class|class|interface|object|typealias|fun|val|var)\b"
    elif suffix == ".rs":
        pattern = r"\b(fn|struct|enum|trait|type|const|static|mod)\b"
    else:
        return result
    for match in re.finditer(pattern, clean):
        kind = " ".join(match.group().split())
        after = clean[match.end():]
        if kind in {"fun", "fn"}:
            op = after.find("(")
            if op < 0 or op > 400:
                continue
            prefix = after[:op]
            # Drop generic brackets before selecting the final function identifier.
            previous = None
            while prefix != previous:
                previous = prefix
                prefix = re.sub(r"<[^<>]*>", " ", prefix)
            names = re.findall(r"`[^`]+`|[A-Za-z_$][\w$]*", prefix)
            if not names or "=" in prefix or "{" in prefix:
                continue
            name = names[-1]
        elif kind in {"val", "var"}:
            prefix = re.split(r"[:=\n]|\bby\b", after, maxsplit=1)[0]
            if "(" in prefix:
                continue  # destructuring is not a single named declaration
            names = re.findall(r"`[^`]+`|[A-Za-z_$][\w$]*", prefix)
            if not names:
                continue
            name = names[-1]
        else:
            name_match = re.match(r"\s*(`[^`]+`|[A-Za-z_$][\w$]*)", after)
            if not name_match:
                # An unnamed companion object is still a named JVM/Kotlin concept.
                before = clean[max(0, match.start()-20):match.start()]
                if kind == "object" and re.search(r"\bcompanion\s*$", before):
                    name = "Companion"
                else:
                    continue
            else:
                name = name_match.group(1)
        line = bisect.bisect_left(newline_offsets, match.start())
        start = newline_offsets[line - 1] + 1
        stop = text.find("\n", match.start())
        if stop < 0:
            stop = len(text)
        before = clean[start:match.start()]
        # Exclude ::class, which is a class literal rather than a declaration.
        if kind == "class" and before.rstrip().endswith("::"):
            continue
        modifiers = re.findall(r"\b(?:expect|actual|public|internal|private|protected|suspend|inline|override|abstract|open|data|sealed|const|lateinit|operator|infix|companion|external)\b", before)
        result.append({
            "kind": kind,
            "name": name,
            "line": line,
            "modifiers": modifiers,
            "declaration_line": text[start:stop].strip(),
        })
    return result


def module_for(path: str, build_dirs: list[str]) -> str:
    if path.startswith("sample/ios/"):
        return "sample/ios"
    for directory in sorted(build_dirs, key=len, reverse=True):
        if directory and path.startswith(directory + "/"):
            return directory
    return "."


def owner_for(path: str) -> str:
    if path.endswith((".gradle.kts", "Cargo.toml")) or path.startswith(("convention-plugins/", ".github/", "gradle/")) or path in {"gradle.properties", "gradlew", "gradlew.bat", "cleanup.sh", "renovate.json"}:
        return "audit_build"
    for owner, modules in AREA.items():
        if path.split("/")[0] in modules.split():
            return owner
    return "audit_history_architecture"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=BASELINE)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/audit/source-inventory.json")
    parser.add_argument("--check", action="store_true", help="Compare with the existing inventory instead of writing it")
    args = parser.parse_args()
    commit = git("rev-parse", f"{args.ref}^{{commit}}").decode().strip()
    entries = []
    for entry in git("ls-tree", "-r", "-z", commit).split(b"\0"):
        if not entry:
            continue
        meta, path_bytes = entry.split(b"\t", 1)
        mode, object_type, object_id = meta.decode().split()
        entries.append((path_bytes.decode(), mode, object_type, object_id))
    # One cat-file batch avoids executing 607 separate commands.
    batch = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "--batch"],
        input="".join(f"{e[3]}\n" for e in entries).encode(),
        stdout=subprocess.PIPE, check=True,
    ).stdout
    blobs, pos = {}, 0
    for path, _, object_type, _ in entries:
        end = batch.index(b"\n", pos)
        header = batch[pos:end].decode().split()
        size = int(header[2])
        blobs[path] = batch[end + 1:end + 1 + size]
        pos = end + size + 2
        if object_type != "blob":
            raise ValueError(f"Unsupported non-blob tree entry: {path}")
    build_dirs = [str(Path(p).parent) for p in blobs if p.endswith("build.gradle.kts")]
    build_dirs = ["" if p == "." else p for p in build_dirs]
    settings = blobs["settings.gradle.kts"].decode()
    include_block = re.search(r"include\(\s*(.*?)\n\)", settings, re.S).group(1)
    included = {x.strip(":").replace(":", "/") for x in re.findall(r'"(:[^"]+)"', include_block)}
    included.add("convention-plugins")
    catalog = tomllib.loads(blobs["gradle/libs.versions.toml"].decode())
    files = []
    for path, mode, object_type, object_id in entries:
        data = blobs[path]
        try:
            body = data.decode("utf-8")
            is_text = "\0" not in body
        except UnicodeDecodeError:
            body, is_text = "", False
        module = module_for(path, build_dirs)
        parts = path.split("/")
        source_set = parts[parts.index("src") + 1] if "src" in parts and parts.index("src") + 2 < len(parts) else None
        suffix = Path(path).suffix
        is_source = suffix in SOURCE_EXTENSIONS
        item = {
            "path": path,
            "git_blob": object_id,
            "sha256": hashlib.sha256(data).hexdigest(),
            "git_mode": mode,
            "bytes": len(data),
            "text": is_text,
            "lines": len(body.splitlines()) if is_text else None,
            "module": module,
            "included_in_gradle": module in included or module == ".",
            "source_set": source_set,
            "targets_inferred_from_conventions": SOURCE_TARGETS.get(source_set, []),
            "language": {".kt": "kotlin", ".kts": "kotlin-script", ".rs": "rust", ".swift": "swift"}.get(suffix, suffix.lstrip(".")),
            "generated_marker_in_source": bool(re.search(r"(?:file is generated|auto[- ]generated)", body[:3000], re.I)),
            "is_source": is_source,
            "is_test_source": bool(source_set and "test" in source_set.lower()),
            "review_owner": owner_for(path),
            "review_status": "indexed-lexically; semantic-review-evidence-is-in-area-reports",
        }
        if is_source:
            package = re.search(r"^\s*package\s+([\w.]+)", body, re.M)
            item["package"] = package.group(1) if package else None
            item["imports"] = re.findall(r"^\s*import\s+([^\r\n;]+)", body, re.M)
            item["declarations"] = declarations(body, suffix)
            item["test_annotation_count"] = len(re.findall(r"@Test\b", masked(body)))
        files.append(item)
    modules = []
    for directory in sorted(build_dirs):
        path = (directory + "/" if directory else "") + "build.gradle.kts"
        body = blobs[path].decode()
        members = [f for f in files if f["module"] == (directory or ".")]
        modules.append({
            "path": directory or ".",
            "build_file": path,
            "included": directory in included or not directory,
            "publication_plugin_in_build_file": 'id("module.publication")' in body,
            "plugins": re.findall(r'(?:id\("([^\"]+)"\)|alias\(([^)]+)\))', body.split("kotlin {")[0]),
            "project_dependency_declarations": re.findall(r"\b(api|implementation)\(projects\.([\w.]+)\)", body),
            "catalog_dependency_declarations": re.findall(r"\b(api|implementation)\(libs\.([\w.]+)\)", body),
            "literal_dependency_declarations": re.findall(r'\b(api|implementation)\("([^\"]+)"\)', body),
            "source_sets_with_tracked_files": sorted({f["source_set"] for f in members if f["source_set"]}),
            "tracked_files": len(members),
            "source_files": sum(f["is_source"] for f in members),
            "source_lines": sum(f["lines"] or 0 for f in members if f["is_source"]),
        })
    xcode_members = [f for f in files if f["module"] == "sample/ios"]
    modules.append({
        "path": "sample/ios",
        "build_file": "sample/ios/Calf.xcodeproj/project.pbxproj",
        "build_system": "Xcode (not a Gradle subproject)",
        "included": False,
        "publication_plugin_in_build_file": False,
        "tracked_files": len(xcode_members),
        "source_files": sum(f["is_source"] for f in xcode_members),
        "source_lines": sum(f["lines"] or 0 for f in xcode_members if f["is_source"]),
    })
    expectations = []
    actuals = collections.defaultdict(list)
    for file in files:
        for decl in file.get("declarations", []):
            if "actual" in decl["modifiers"]:
                actuals[(file["module"], decl["name"])].append({"path": file["path"], "line": decl["line"], "kind": decl["kind"], "source_set": file["source_set"]})
    for file in files:
        for decl in file.get("declarations", []):
            if "expect" in decl["modifiers"]:
                expectations.append({"name": decl["name"], "kind": decl["kind"], "path": file["path"], "line": decl["line"], "actual_name_candidates": actuals[(file["module"], decl["name"])]})
    counts = collections.Counter(f["language"] for f in files if f["is_source"])
    output = {
        "schema_version": 1,
        "baseline_commit": commit,
        "method": "Git ls-tree/cat-file hashes + masked lexical declaration extraction; no Gradle, compiler, network, or semantic review claim",
        "limitations": [
            "Declaration candidates include local variables and constructor properties; exclude anonymous declarations, implicit getters/setters and generated build outputs.",
            "String-template expressions are masked with their enclosing literal; overloaded function signatures are not compiler-resolved.",
            "Expect/actual links use module/name only, can include similarly named members, and do not establish compatibility or successful compilation.",
            "Target lists come from the baseline source hierarchy, not execution; excluded/stub modules and native host restrictions need the platform matrix.",
            "Review ownership is assignment, not proof a file passed review. Read the area reports and verification evidence.",
        ],
        "counts": {
            "tracked_files": len(files),
            "source_files": sum(f["is_source"] for f in files),
            "source_lines": sum(f["lines"] or 0 for f in files if f["is_source"]),
            "kotlin_kts_rust_lines": sum(f["lines"] or 0 for f in files if f["language"] in {"kotlin", "kotlin-script", "rust"}),
            "source_files_by_language": dict(sorted(counts.items())),
            "generated_marker_files": sum(f["generated_marker_in_source"] for f in files),
            "generated_marker_source_lines": sum(f["lines"] or 0 for f in files if f["is_source"] and f["generated_marker_in_source"]),
            "test_source_files": sum(f["is_test_source"] and f["is_source"] for f in files),
            "test_annotations": sum(f.get("test_annotation_count", 0) for f in files),
            "declaration_candidates": sum(len(f.get("declarations", [])) for f in files),
            "explicit_expect_candidates": len(expectations),
        },
        "version_catalog": catalog,
        "source_set_targets": SOURCE_TARGETS,
        "modules": modules,
        "expect_actual_name_index": expectations,
        "files": files,
    }
    serialized = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if args.output.read_text() != serialized:
            raise SystemExit(f"Inventory differs: {args.output}")
        print(f"Inventory matches {commit}: {output['counts']}")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
        print(f"Wrote {args.output}: {output['counts']}")


if __name__ == "__main__":
    main()
