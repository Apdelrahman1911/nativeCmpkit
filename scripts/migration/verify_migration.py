#!/usr/bin/env python3
"""Read-only migration verification. Network reads occur only with --remote.

Never executes archived code/attachments or modifies project refs/GitHub state.
Bundle restoration uses a temporary, disposable bare repository only.
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
import tempfile
from github_json import json_pages

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
    report = {"checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "remote_reads": args.remote, "checks": checks,
              "required_owner_followups": [],
              "receipt_scope": "Verifies the observed checkout/remote SHA and current files, not the later commit storing this receipt."}

    def check(name, condition, detail):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise AssertionError(f"{name}: {detail}")

    try:
        identity = json.loads((ROOT / "docs/migration/identity.json").read_text())
        report["observed_checkout_sha"] = command("git", "rev-parse", "HEAD").strip()
        report["worktree_porcelain"] = command("git", "status", "--porcelain").splitlines()
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
        recovery = json.loads((archive / "referenced-commits-verification.json").read_text())
        dataset = metadata / "referenced-commits.json"
        candidates = json.loads(dataset.read_text())
        check("referenced_commit_recovery_complete", bool(recovery.get("completed_at_utc")) and recovery.get("candidate_count") == len(candidates),
              {"candidates": len(candidates), "statuses": recovery.get("statuses"), "completed_at_utc": recovery.get("completed_at_utc")})
        check("referenced_commit_dataset_hash", recovery["source_dataset_sha256"] == digest(dataset), digest(dataset))
        check("supplemental_bundle_checksum", supplemental.is_file() and digest(supplemental) == recovery["bundle_sha256"] ==
              (archive / "referenced-commits.bundle.sha256").read_text().split()[0], recovery["bundle_sha256"])
        supplemental_refs = {}
        for line in (archive / "referenced-commit-refs.txt").read_text().splitlines():
            oid, typ, ref = line.split()
            if not SHA.fullmatch(oid) or typ != "commit" or not ref.startswith("refs/archive/upstream/referenced-commits/"):
                raise ValueError("Invalid supplemental ref")
            supplemental_refs[ref] = oid
        bundled_supplemental = dict(line.split()[::-1] for line in command("git", "bundle", "list-heads", str(supplemental)).splitlines())
        check("supplemental_refs_complete", bundled_supplemental == supplemental_refs and len(supplemental_refs) == recovery["archival_refs_count"], len(supplemental_refs))
        # A check inside the existing project could accidentally satisfy missing
        # prerequisites. Restore both archives into an empty object database.
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-bundle-verify-") as temp:
            command("git", "init", "--bare", temp)
            for bundle in (advertised_bundle, supplemental):
                command("git", "--git-dir=" + temp, "bundle", "verify", str(bundle))
                command("git", "--git-dir=" + temp, "fetch", "--no-write-fetch-head", str(bundle), "+refs/*:refs/*")
            restored = dict(line.split()[::-1] for line in command("git", "--git-dir=" + temp, "for-each-ref", "--format=%(objectname) %(refname)").splitlines())
            check("offline_restored_refs_identical", all(restored.get(ref) == oid for ref, oid in {**expected, **supplemental_refs}.items()), len(restored))
            missing = []
            for item in candidates:
                sha = item["sha"]
                if not SHA.fullmatch(sha): raise ValueError("Malformed candidate commit")
                result = subprocess.run(["git", "--git-dir=" + temp, "cat-file", "-t", sha], capture_output=True, text=True)
                if result.returncode or result.stdout.strip() != "commit": missing.append(sha)
            check("all_metadata_commits_restored_offline", not missing, {"candidates": len(candidates), "missing": missing})
            command("git", "--git-dir=" + temp, "fsck", "--full", "--no-dangling")
            check("offline_bundle_restore_integrity", True, {"commits": int(command("git", "--git-dir=" + temp, "rev-list", "--all", "--count")), "network_required": False})

        if args.remote:
            repo = identity["github_repository"]
            if repo != "Apdelrahman1911/nativeCmpkit":
                raise ValueError("Unexpected destination repository")
            state = json.loads(command("gh", "api", "repos/" + repo))
            check("independent_github_repository", state.get("fork") is False and state["full_name"] == repo, {"full_name": state["full_name"], "fork": state.get("fork"), "default_branch": state["default_branch"]})
            incident = json.loads((ROOT / "docs/migration/pages-incident.json").read_text())
            check("legacy_pages_incident_disclosed", incident["repository"] == repo and incident["schema_version"] == 1,
                  "One unintended historical-branch deployment is recorded; not a zero-deployment claim")
            report["pages_configuration_present"] = state.get("has_pages")
            if state.get("has_pages"):
                pages = json.loads(command("gh", "api", f"repos/{repo}/pages"))
                check("legacy_pages_publishing_disabled", pages.get("build_type") == "workflow",
                      "Legacy branch publishing is off; this does not unpublish an existing deployment")
                report["pages_unpublishing_verified"] = False
                report["required_owner_followups"].append(incident["owner_followup"])
            else:
                check("github_pages_configuration_removed", state.get("has_pages") is False,
                      "No Pages configuration reported; CDN/cache expiration is not tested")
                report["pages_unpublishing_verified"] = True
            actions = json.loads(command("gh", "api", f"repos/{repo}/actions/permissions"))
            check("github_actions_disabled", actions.get("enabled") is False, actions)
            releases = json.loads(command("gh", "api", f"repos/{repo}/releases?per_page=100"))
            check("no_releases_created", len(releases) == 0, "Historical release JSON is archived, not republished")
            deployment_pages = json_pages(command("gh", "api", "--paginate", f"repos/{repo}/deployments?per_page=100"))
            if not all(isinstance(page, list) for page in deployment_pages):
                raise ValueError("Unexpected deployment response shape")
            deployments = [deployment for page in deployment_pages for deployment in page]
            known = {item["id"]: item for item in incident["disclosed_deployments"]}
            check("no_undisclosed_deployments", all(
                deployment["id"] in known and
                all(deployment[field] == known[deployment["id"]][field] for field in ("ref", "sha", "environment", "created_at")) and
                deployment["creator"]["login"] == known[deployment["id"]]["creator"]
                for deployment in deployments),
                {"observed_ids": [d["id"] for d in deployments], "disclosed_incident_ids": sorted(known),
                 "scope": "The unintended legacy Pages event is retained, not hidden or recreated as a nativeCmpkit release"})
            pages = json_pages(command("gh", "api", "--paginate", f"repos/{repo}/actions/runs?per_page=100"))
            runs = [run for page in pages for run in page["workflow_runs"]]
            approved = {".github/workflows/gradle.yml", ".github/workflows/build-native-libs.yml"}
            for run in runs:
                check("approved_verification_run_" + str(run["id"]), run["path"] in approved and run["event"] == "workflow_dispatch" and run["status"] == "completed",
                      {k: run[k] for k in ("id", "path", "head_sha", "event", "status", "conclusion")})
                if not SHA.fullmatch(run["head_sha"]): raise ValueError("Invalid workflow revision")
                workflow = command("git", "show", run["head_sha"] + ":" + run["path"])
                check("read_only_executed_workflow_" + str(run["id"]), "contents: read" in workflow and not re.search(r"publishAndRelease|gh-deploy|actions-netlify|contents:\s*write|pull-requests:\s*write|cargo publish", workflow),
                      "Approved workflow source at its executed revision; report artifacts are not releases/packages")
            report["verification_workflow_runs"] = [run["id"] for run in runs]
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
