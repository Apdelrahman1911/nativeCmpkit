# SPDX-License-Identifier: Apache-2.0
"""Passive stdlib/Git custody, not an old test/planner/compiler/native execution."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = Path(__file__).resolve().parent
BASE = "0188ae9adc9ccda8ced8d1483965c88b8bcf1d27"
FROZEN630 = "6fb368eb77a0863cd3d725f75e85d59b41caee71"
OBSERVER = "scripts/ci/android_camera_recents_observation.py"
ADDED = {"scripts/ci/android_camera_live_task_refusal_observation.py",
         "scripts/ci/test_android_camera_live_task_refusal_observation.py"}
UNCHANGED = {
    "scripts/ci/android_camera_developer_prerequisite.py": "92f8d79d3a0871f1abb619a0a17b36c87568e11151fb3dbefa4f12773de78bdb",
    "scripts/ci/android_device_tests.py": "f096609a3731628c02966b7f6edd40641d7c0ff8119d0922605f6c7e6e99d7d8",
    "scripts/ci/android_camera_home_baseline.py": "e710e5f1c7d048b0b32e00f2a261443f6dcbd24aa51ec1fc46bfbe27ab47e3b5",
    "scripts/ci/android_camera_home_refusal_observation.py": "1ad4888609d470e591d212cf5a370bc5ed900aa80c181e84d0277f6c9095287c",
}
DISPATCH = ('    if error.args == ("Unknown live leaf task",):\n'
            '        from android_camera_live_task_refusal_observation import live_task_refusal\n'
            '        return live_task_refusal(error)\n')
BASE_OBSERVER_SHA256 = "0fba4e83307511dada22ed28f5ad98e9e97fb15f5fc0521af858ca954901d304"


def sha(body):
    return hashlib.sha256(body).hexdigest()


def digest(files):
    return sha("".join(f"{value}  {name}\n" for name, value in sorted(files.items())).encode())


def write(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def safe(relative):
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(part in {".", ".."} for part in parts):
        raise ValueError("Confined relative source required")
    path = ROOT
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlinked source refused")
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Escaping source refused")
    return path


def snapshot():
    # Reconstruct ONLY the unchanged snapshot_inputs input scope, using its AST
    # literal tuples and the repository's inspected literal include idiom.
    tree = ast.parse(safe("scripts/ci/library_tests.py").read_text())
    literals = {node.targets[0].id: node.value for node in tree.body
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and
                isinstance(node.targets[0], ast.Name)}
    root_inputs = ast.literal_eval(literals["ROOT_INPUTS"])
    ignored = ast.literal_eval(literals["IGNORED_INPUT_DIRS"])
    owner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "snapshot_inputs")
    scope_trees = ast.literal_eval(next(node.iter for node in owner.body if isinstance(node, ast.For) and
                                      isinstance(node.target, ast.Name) and node.target.id == "tree"))
    inputs = set()

    def collect(relative):
        folder = safe(relative)
        if not folder.exists():
            return
        if not folder.is_dir():
            raise ValueError("Source tree must be a directory")
        for base, directories, names in os.walk(folder, followlinks=False):
            directories[:] = sorted(name for name in directories if name not in ignored)
            for name in [*directories, *names]:
                if (Path(base) / name).is_symlink():
                    raise ValueError("Symlinked source input refused")
            for name in sorted(names):
                path = Path(base) / name
                if not path.is_file():
                    raise ValueError("Nonregular source refused")
                inputs.add(path)

    for name in root_inputs:
        path = safe(name)
        if path.is_file():
            inputs.add(path)
    for name in scope_trees:
        collect(name)
    settings = safe("settings.gradle.kts").read_text()
    blocks = re.findall(r"(?ms)^include\(\s*(.*?)^\)", settings)
    if len(blocks) != 1:
        raise ValueError("One inspected literal include block required")
    block = re.sub(r"(?m)//[^\n]*", "", blocks[0])
    paths = re.findall(r'"([^"\n]+)"', block)
    remainder = re.sub(r'"[^"\n]+"', "", block)
    if not paths or remainder.strip(" \t\r\n,") or len(paths) != len(set(paths)):
        raise ValueError("Computed or duplicate includes refused")
    for original in paths:
        if re.fullmatch(r":[a-z][a-z0-9-]*(?::[a-z][a-z0-9-]*)*", original) is None:
            raise ValueError("Unrecognized literal project path")
        if original.startswith(":sample:"):
            continue
        if not original.startswith(":calf-"):
            raise ValueError("Unclassified nonsample project")
        module = original[1:].replace(":", "/")
        if not safe(module + "/build.gradle.kts").is_file():
            raise ValueError("Missing library build input")
        for suffix in ("src", "native", ".cargo", "gradle", "karma.config.d"):
            collect(module + "/" + suffix)
        for name in ("build.gradle.kts", "gradle.properties", "gradle.lockfile"):
            path = safe(module + "/" + name)
            if path.is_file():
                inputs.add(path)
    for path in safe("sample").glob("*/build.gradle.kts"):
        inputs.add(safe(path.relative_to(ROOT).as_posix()))
    seam = ('sourceSets.getByName("iosTest").kotlin.srcDir(rootProject.file("'
            'sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/alertinput"))')
    if safe("calf-ui/build.gradle.kts").read_text().count(seam) != 1:
        raise ValueError("Unchanged configured secure-alert held provenance seam required")
    for name in ("sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/alertinput/SampleAlertDialogInputFields.kt",
                 "sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/AlertDialogScreen.kt"):
        inputs.add(safe(name))
    result = {}
    for path in sorted(inputs):
        before = path.stat()
        body = path.read_bytes()
        after = path.stat()
        if ((before.st_size, before.st_mtime_ns, before.st_ino) !=
                (after.st_size, after.st_mtime_ns, after.st_ino)):
            raise ValueError("Source changed while hashing")
        result[path.relative_to(ROOT).as_posix()] = sha(body)
    return result


def git_blobs(revision, names):
    # Local existing Git objects only; no network or history mutation.
    specs = [f"{revision}:{name}" for name in names]
    result = subprocess.run(["git", "cat-file", "--batch"], cwd=ROOT, input=("\n".join(specs) + "\n").encode(),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if result.stderr:
        raise ValueError("Unexpected local Git object diagnostics")
    values, offset = {}, 0
    for name in names:
        end = result.stdout.index(b"\n", offset)
        fields = result.stdout[offset:end].split()
        if len(fields) != 3 or fields[1] != b"blob":
            raise ValueError("Existing ordinary Git blob required")
        size = int(fields[2])
        offset = end + 1
        values[name] = result.stdout[offset:offset + size]
        offset += size
        if result.stdout[offset:offset + 1] != b"\n":
            raise ValueError("Malformed local Git batch framing")
        offset += 1
    if offset != len(result.stdout):
        raise ValueError("Unexpected extra local Git bytes")
    return values


def main():
    checks = []

    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})
        if not condition:
            write("source-review-first-refusal.json", {"checks": checks})
            raise AssertionError(name)

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    check("approved immutable base0188", head == BASE)
    current = snapshot()
    names = sorted(set(current) - ADDED)
    bindings, manifest_maps = set(), {}
    manifests = sorted((ROOT / "scripts/ci/fixtures").glob("*source-inverse.json"))
    for path in manifests:
        body = path.read_bytes()
        document = json.loads(body)
        manifest_maps[path.relative_to(ROOT).as_posix()] = sha(body)
        if type(document) is dict and type(document.get("bindings")) is dict:
            bindings.update(document["bindings"])
    extra = sorted(bindings - set(names))
    blobs = git_blobs(BASE, [*names, *extra])
    base = {name: sha(blobs[name]) for name in names}
    changed = sorted(name for name in names if base[name] != current[name])
    check("exact one existing source input modified", changed == [OBSERVER])
    check("exact two newly added source-control inputs", set(current) - set(base) == ADDED)
    tracked = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().rstrip("\0").split("\0"))
    check("all previous held inputs are tracked base files", set(names) <= tracked)
    check("old inverse binding count remains greater than10", len(manifests) > 10)
    check("observer and new helper unlisted by all old bindings", not ({OBSERVER, *ADDED} & bindings))
    for path in manifests:
        name = path.relative_to(ROOT).as_posix()
        check("unchanged inverse specification: " + name, path.read_bytes() == blobs[name])
    for name in sorted(bindings):
        check("unchanged current bound source bytes: " + name, safe(name).read_bytes() == blobs[name])
    frozen = git_blobs(FROZEN630, sorted(UNCHANGED))
    for name, expected in UNCHANGED.items():
        check("exact original630/current0188 action source: " + name,
              current[name] == base[name] == sha(frozen[name]) == expected)
    observer = safe(OBSERVER).read_bytes()
    check("approved original observer hash", base[OBSERVER] == BASE_OBSERVER_SHA256)
    check("exact one three-line insertion", len(DISPATCH.splitlines()) == 3 and observer.count(DISPATCH.encode()) == 1)
    stripped = observer.replace(DISPATCH.encode(), b"", 1)
    check("whole-source reverse restoration", stripped == blobs[OBSERVER])
    anchor = b'    if error.args != ("Settings recent task absence is unproved",):\n'
    check("whole-source forward roundtrip", stripped.count(anchor) == 1 and
          stripped.replace(anchor, DISPATCH.encode() + anchor, 1) == observer)
    parser = ast.parse(safe("scripts/ci/android_camera_developer_prerequisite.py").read_text())
    owner = next(node for node in parser.body if isinstance(node, ast.FunctionDef) and node.name == "parse_live_tasks")
    guards = [node for node in ast.walk(owner) if isinstance(node, ast.Call) and
              isinstance(node.func, ast.Name) and node.func.id == "require" and len(node.args) == 2 and
              isinstance(node.args[1], ast.Constant) and node.args[1].value == "Unknown live leaf task"]
    check("one unchanged literal three-term live-leaf require at349", len(guards) == 1 and guards[0].lineno == 349 and
          ast.unparse(guards[0].args[0]) == "child is not None and child[1] not in children and (child[2] != 'unknown')")
    check("current calendar-share projection bf22 bytes unchanged", current["scripts/ci/calendar_share_selector_source_projection.py"] ==
          "bf22ff7bf51de408042052693afc5cf970206e511becb7faf8b8cd361e1f194c")
    check("reserve at least8GiB before NEW16", os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize >= 8 * 1024 ** 3)
    write("base-inputs.json", {"kind": "approved0188 local immutable Git-source input scope, not a compiler/native map",
                               "source_commit": BASE, "count": len(base), "digest": digest(base), "files": base})
    write("held-inputs.json", {"kind": "current actual source-control bytes; passive stdlib reconstruction of unchanged library input scope",
                               "source_base_commit": BASE, "compiler_or_native_execution": False,
                               "count": len(current), "digest": digest(current), "files": current})
    write("source-review.json", {"checks": checks, "passive_check_count": len(checks), "all_passed": True,
                                 "existing_modified": changed, "new_tooling_inputs": sorted(ADDED),
                                 "inverse_manifest_count": len(manifests), "old_binding_path_count": len(bindings),
                                 "inverse_spec_sha256": manifest_maps,
                                 "current_bound_source_sha256": {name: sha(blobs[name]) for name in sorted(bindings)},
                                 "binding_changes": [], "pin_changes": [], "existing_test_body_changes": [],
                                 "native_or_query_or_compiler_execution": False})
    print(json.dumps({"passive_checks": len(checks), "base_count": len(base), "held_count": len(current),
                      "held_digest": digest(current), "inverse_manifests": len(manifests),
                      "bound_paths": len(bindings), "original_sources_unchanged": True}))


if __name__ == "__main__":
    main()
