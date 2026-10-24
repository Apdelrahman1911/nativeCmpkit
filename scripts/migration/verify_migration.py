#!/usr/bin/env python3
"""Read-only migration verification. Network reads occur only with --remote.

Never executes archived code/attachments or modifies Git refs/GitHub state.
Run from any directory; stdout is a machine-readable verification receipt.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SHA = re.compile(r"^[0-9a-f]{40}$")
HEX256 = re.compile(r"^[0-9a-f]{64}$")


def command(*args: str) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{args[0]} {args[1] if len(args)>1 else ''} failed (exit {result.returncode}): {result.stderr.strip()[:2000]}")
    return result.stdout


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_child(parent: Path, relative: str) -> Path:
    path = parent / relative
    if path.is_symlink() or not path.resolve().is_relative_to(parent.resolve()):
        raise ValueError(f"Unsafe archive path: {relative}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", action="store_true", help="Also read destination refs/settings using git and gh; no writes")
    parser.add_argument("--output", type=Path, help="Write the same receipt to this explicit output path")
    args = parser.parse_args()
    checks: list[dict] = []
    report = {"checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "remote_reads": args.remote, "checks": checks}

    def check(name, condition, detail):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise AssertionError(f"{name}: {detail}")

    try:
        identity = json.loads((ROOT / "docs/migration/identity.json").read_text())
        baseline = identity["source_baseline"]
        check("baseline_sha_shape", bool(SHA.fullmatch(baseline)), baseline)
        command("git", "cat-file", "-e", baseline + "^{commit}")
        command("git", "merge-base", "--is-ancestor", baseline, "HEAD")
        check("baseline_ancestry", True, "Original main is an ancestor of the checked-out migration branch")
        original_license = subprocess.check_output(["git", "show", baseline + ":LICENSE"], cwd=ROOT)
        check("apache_license_unchanged", (ROOT / "LICENSE").read_bytes() == original_license,
              "LICENSE is byte-identical to the upstream baseline")
        for name in ("NOTICE", "THIRD_PARTY_NOTICES.md", "AGENTS.md"):
            check("required_notice_" + name, (ROOT / name).is_file(), name)
        check("root_identity", 'rootProject.name = "nativeCmpkit"' in (ROOT / "settings.gradle.kts").read_text(), "Root Gradle project name")
        check("maven_identity", 'group = "io.github.apdelrahman1911.nativecmpkit"' in (ROOT / "build.gradle.kts").read_text(), "Prospective independent Maven group (not publication validation)")
        check("resource_namespace_pinned", 'packageOfResClass = "com.mohamedrejeb.calf.calf_cupertino_icons.generated.resources"' in (ROOT / "calf-cupertino-icons/build.gradle.kts").read_text(), "Retain Compose resource imports across Maven group rename")
        check("no_git_alternates", not (ROOT / ".git/objects/info/alternates").exists(), "Local checkout does not require another clone's object store")
        check("coordinate_uniqueness", len({m['new_artifact'] for m in identity['modules']}) == len(identity['modules']), f"{len(identity['modules'])} planned artifacts; no publication implied")
        for module in identity["modules"]:
            source = safe_child(ROOT, module["source_directory"]) / "build.gradle.kts"
            check("publishable_module_" + module["new_artifact"], 'id("module.publication")' in source.read_text(), module["source_directory"])

        archive = ROOT / "docs/migration/git"
        expected = {}
        kinds = {}
        for line in (archive / "upstream-refs.txt").read_text().splitlines():
            oid, typ, ref = line.split()
            check("ref_shape_" + ref, bool(SHA.fullmatch(oid)) and ref.startswith("refs/"), typ)
            expected[ref] = oid
            kind = ref.split("/")[1]
            kinds[kind] = kinds.get(kind, 0) + 1
        advertised_bundle = archive / "upstream.bundle"
        checksum = (archive / "upstream.bundle.sha256").read_text().split()[0]
        check("git_bundle_sha256", digest(advertised_bundle) == checksum, checksum)
        bundled = {}
        for line in command("git", "bundle", "list-heads", str(advertised_bundle)).splitlines():
            oid, ref = line.split()
            bundled[ref] = oid
        check("all_advertised_refs_bundled", all(bundled.get(ref) == oid for ref, oid in expected.items()), kinds)
        command("git", "bundle", "verify", str(advertised_bundle))
        check("git_bundle_complete", True, "Git verified the self-contained advertised-ref bundle")
        command("git", "fsck", "--full", "--no-dangling")
        check("git_objects_integrity", True, "git fsck --full --no-dangling passed for local repository")

        metadata = ROOT / "docs/migration/upstream-metadata"
        sums_file = metadata / "SHA256SUMS"
        check("metadata_integrity_manifest_present", sums_file.is_file(), "SHA256SUMS required; exporter must have finished")
        seen = set()
        for line in sums_file.read_text().splitlines():
            if not line.strip():
                continue
            expected_hash, filename = line.split(maxsplit=1)
            filename = filename.lstrip("*")
            if filename.startswith("./"):
                filename = filename[2:]
            if not HEX256.fullmatch(expected_hash):
                raise ValueError("Invalid metadata checksum format")
            path = safe_child(metadata, filename)
            if not path.is_file() or digest(path) != expected_hash:
                raise AssertionError("Metadata checksum mismatch: " + filename)
            seen.add(filename)
        actual = {str(p.relative_to(metadata)) for p in metadata.rglob("*") if p.is_file() and p != sums_file}
        check("metadata_all_files_verified", actual == seen, {"hashed_files": len(seen), "unlisted": sorted(actual-seen)[:20], "missing": sorted(seen-actual)[:20]})
        for f in ("issues.json", "pull-requests.json", "issue-comments.json", "review-comments.json", "releases.json", "repository.json", "manifest.json", "validation.json", "referenced-commits.json"):
            json.loads((metadata / f).read_text())
        check("metadata_json_readable", True, "Required raw datasets and final exporter manifest parse")

        for workflow in (ROOT / ".github/workflows").glob("*.yml"):
            source = workflow.read_text()
            check("read_only_workflow_" + workflow.name,
                  not re.search(r"publishAndRelease|gh-deploy|actions-netlify|contents:\s*write|pull-requests:\s*write", source),
                  "No inherited publishing/deployment or write-token permissions")
            for action in re.findall(r"uses:\s*([^\s]+)", source):
                if not action.startswith("./"):
                    check("pinned_action_" + action, bool(re.search(r"@[0-9a-f]{40}$", action)), workflow.name)

        supplemental = archive / "referenced-commits.bundle"
        if supplemental.exists():
            command("git", "bundle", "verify", str(supplemental))
            check("supplemental_bundle", True, digest(supplemental))

        if args.remote:
            repo = identity["github_repository"]
            if repo != "Apdelrahman1911/nativeCmpkit":
                raise ValueError("Unexpected destination repository")
            state = json.loads(command("gh", "api", "repos/" + repo))
            check("independent_github_repository", state.get("fork") is False and state["full_name"] == repo, {"full_name": state["full_name"], "fork": state.get("fork"), "default_branch": state["default_branch"]})
            actions = json.loads(command("gh", "api", f"repos/{repo}/actions/permissions"))
            check("github_actions_disabled", actions.get("enabled") is False, actions)
            releases = json.loads(command("gh", "api", f"repos/{repo}/releases?per_page=100"))
            check("no_releases_created", len(releases) == 0, "Historical release JSON is archived, not republished")
            runs = json.loads(command("gh", "api", f"repos/{repo}/actions/runs?per_page=1"))
            check("no_workflows_executed", runs.get("total_count") == 0, runs.get("total_count"))
            remote = dict(line.split()[::-1] for line in command("git", "ls-remote", "--refs", f"https://github.com/{repo}.git").splitlines())
            preserved = {ref: oid for ref, oid in expected.items() if ref.startswith(("refs/heads/", "refs/tags/")) and ref != "refs/heads/main"}
            check("historical_remote_refs_identical", all(remote.get(ref) == oid for ref, oid in preserved.items()), f"{len(preserved)} non-main heads/tags are byte-identical object IDs")
            check("remote_main_matches_checkout", remote.get("refs/heads/main") == command("git", "rev-parse", "HEAD").strip(), remote.get("refs/heads/main"))
            check("source_remote_push_disabled", command("git", "remote", "get-url", "--push", "upstream").strip() == "DISABLED_READ_ONLY_UPSTREAM", "Local upstream remote is push-disabled")
        report["passed"] = True
    except Exception as exc:
        report["passed"] = False
        report["error"] = str(exc)
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(output)
    sys.stdout.write(output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
