"""Offline source-remote safety checks; no Git/GitHub mutation or network calls."""
import unittest
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import call, patch

import verify_migration as module


class VerificationActionsPolicyTests(unittest.TestCase):
    def setUp(self):
        self.actions = {"enabled": True, "allowed_actions": "all", "sha_pinning_required": False}
        self.token = {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
        self.workflow = """name: verification
on:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  checks:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - run: python3 scripts/audit/validate_audit.py
"""

    def test_explicit_owner_settings_pass(self):
        self.assertTrue(module.approved_actions_configuration(self.actions, self.token))

    def test_disabled_restricted_or_required_pinning_is_not_current_policy(self):
        for name, value in (("enabled", False), ("allowed_actions", "selected"),
                            ("allowed_actions", "local_only"), ("sha_pinning_required", True)):
            with self.subTest(name=name, value=value):
                self.assertFalse(module.approved_actions_configuration({**self.actions, name: value}, self.token))

    def test_missing_or_wrong_typed_api_settings_fail_closed(self):
        for name in self.actions:
            with self.subTest(name=name):
                self.assertFalse(module.approved_actions_configuration(
                    {key: value for key, value in self.actions.items() if key != name}, self.token))
        for name, value in (("enabled", "true"), ("enabled", 1),
                            ("sha_pinning_required", "false"), ("sha_pinning_required", 0)):
            with self.subTest(name=name, value=value):
                self.assertFalse(module.approved_actions_configuration({**self.actions, name: value}, self.token))
        for name in self.token:
            self.assertFalse(module.approved_actions_configuration(
                self.actions, {key: value for key, value in self.token.items() if key != name}))

    def test_write_default_or_pull_request_approval_is_rejected(self):
        for name, value in (("default_workflow_permissions", "write"),
                            ("can_approve_pull_request_reviews", True),
                            ("can_approve_pull_request_reviews", "false")):
            self.assertFalse(module.approved_actions_configuration(self.actions, {**self.token, name: value}))

    def test_named_action_versions_branches_and_optional_sha_are_accepted(self):
        for reference in ("actions/checkout@v6", "owner/action@main", "owner/action@release/v2",
                          "gradle/actions/setup-gradle@" + "a" * 40,
                          "owner/repository/.github/workflows/check.yml@v2",
                          "./.github/actions/verify", "docker://alpine:3.22"):
            with self.subTest(reference=reference):
                self.assertTrue(module.explicit_action_reference(reference))

    def test_missing_or_interpolated_action_reference_is_rejected(self):
        for reference in ("actions/checkout", "actions/checkout@", "${{ inputs.action }}",
                          "./../outside", "docker://alpine", "owner/action@v1\nother", ""):
            with self.subTest(reference=reference):
                self.assertFalse(module.explicit_action_reference(reference))

    def test_read_only_tag_based_workflow_is_allowed(self):
        self.assertTrue(module.read_only_verification_workflow(self.workflow))

    def test_write_scopes_cannot_hide_in_job_or_inline_permissions(self):
        for scope in ("contents", "packages", "pages", "id-token", "deployments", "issues", "pull-requests"):
            for permission in (f"    permissions:\n      {scope}: write\n", f'    permissions: {{"{scope}": "write"}}\n'):
                with self.subTest(scope=scope, permission=permission):
                    self.assertFalse(module.read_only_verification_workflow(self.workflow + permission))
        self.assertFalse(module.read_only_verification_workflow(self.workflow + "    permissions: write-all\n"))

    def test_missing_explicit_read_only_default_does_not_pass(self):
        self.assertFalse(module.read_only_verification_workflow(self.workflow.replace("permissions:\n  contents: read\n", "")))
        self.assertFalse(module.read_only_verification_workflow(self.workflow.replace("permissions:\n  contents: read\n", "# permissions:\n#   contents: read\n")))

    def test_known_publication_deployment_and_privileged_triggers_are_rejected(self):
        for command in ("./gradlew publishAndReleaseToMavenCentral", "mkdocs gh-deploy", "cargo publish",
                        "npm publish", "gh release create preview", "gh api --method POST repos/x/y/deployments"):
            with self.subTest(command=command):
                self.assertFalse(module.read_only_verification_workflow(self.workflow + "      - run: " + command + "\n"))
        for action in ("actions/deploy-pages@v4", "nwtgck/actions-netlify@v3"):
            self.assertFalse(module.read_only_verification_workflow(self.workflow + "      - uses: " + action + "\n"))
        for event in ("pull_request_target", "workflow_run"):
            self.assertFalse(module.read_only_verification_workflow(self.workflow.replace("workflow_dispatch:", event + ":")))

    def test_in_progress_approved_run_is_not_a_control_policy_failure(self):
        run = {"path": ".github/workflows/gradle.yml", "event": "workflow_dispatch", "status": "in_progress"}
        self.assertTrue(module.approved_verification_run(run))
        for status in ("queued", "completed", "waiting", "pending", "requested"):
            self.assertTrue(module.approved_verification_run({**run, "status": status}))
        self.assertFalse(module.approved_verification_run({**run, "status": "unknown"}))

    def test_unreviewed_workflow_or_event_remains_rejected(self):
        run = {"path": ".github/workflows/gradle.yml", "event": "workflow_dispatch", "status": "completed"}
        self.assertFalse(module.approved_verification_run({**run, "path": ".github/workflows/deploy.yml"}))
        self.assertFalse(module.approved_verification_run({**run, "event": "pull_request_target"}))
        self.assertFalse(module.approved_verification_run({**run, "event": "push"}))


class PagesResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        names = ["pages.json", "public-http-checks.json", "gh-pages.json"]
        for name in names:
            (self.root / name).write_text("{}\n")
        self.receipt = {
            "repository": "Apdelrahman1911/nativeCmpkit", "verified": True,
            "owner_reported_unpublish_complete": True,
            "checks": dict.fromkeys(["correct_independent_repository", "pages_endpoint_accessible",
                "no_current_pages_build", "legacy_publishing_disabled", "published_routes_return_404",
                "preserved_historical_branch", "actions_disabled_at_observation"], True),
            "evidence_sha256": {name: module.digest(self.root / name) for name in names},
        }

    def evaluate(self, current=None):
        path = self.root / "verification.json"
        path.write_text(json.dumps(self.receipt))
        incident = {"resolution": {"verified": True, "receipt": path.name,
                                   "receipt_sha256": module.digest(path)}}
        with patch.object(module, "ROOT", self.root):
            return module.verified_pages_resolution(incident, {"status": None} if current is None else current)

    def test_hashed_complete_receipt_and_null_current_status_pass(self):
        self.assertTrue(self.evaluate())

    def test_new_build_or_missing_status_is_not_unpublished(self):
        self.assertFalse(self.evaluate({"status": "built"}))
        self.assertFalse(self.evaluate({}))

    def test_unresolved_migration_snapshot_is_not_assumed_complete(self):
        self.assertFalse(module.verified_pages_resolution({}, {"status": None}))

    def test_missing_owner_confirmation_fails(self):
        self.receipt["owner_reported_unpublish_complete"] = False
        self.assertFalse(self.evaluate())

    def test_false_or_missing_required_check_fails(self):
        self.receipt["checks"]["published_routes_return_404"] = False
        self.assertFalse(self.evaluate())
        del self.receipt["checks"]["published_routes_return_404"]
        self.assertFalse(self.evaluate())

    def test_changed_evidence_is_not_accepted(self):
        (self.root / "pages.json").write_text('{"status":"built"}')
        self.assertFalse(self.evaluate())

    def test_missing_evidence_hash_is_not_accepted(self):
        del self.receipt["evidence_sha256"]["public-http-checks.json"]
        self.assertFalse(self.evaluate())

    def test_path_escape_rejected(self):
        self.receipt["evidence_sha256"]["../outside.json"] = "0" * 64
        with self.assertRaises(ValueError):
            self.evaluate()


class UpstreamPushSafetyTests(unittest.TestCase):
    def test_fresh_clone_without_upstream_passes_without_url_lookup(self):
        with patch.object(module, "command", return_value="origin\n") as command:
            safe, detail = module.upstream_push_safety()
        self.assertTrue(safe)
        self.assertIn("No local upstream", detail)
        command.assert_called_once_with("git", "remote")

    def test_existing_explicit_interlock_passes(self):
        with patch.object(module, "command", side_effect=["origin\nupstream\n", "DISABLED_READ_ONLY_UPSTREAM\n"]) as command:
            safe, detail = module.upstream_push_safety()
        self.assertTrue(safe)
        self.assertIn("Every configured upstream push URL is disabled", detail)
        self.assertEqual(command.call_args_list, [call("git", "remote"), call("git", "remote", "get-url", "--push", "--all", "upstream")])

    def test_second_unsafe_push_url_is_not_hidden_by_first_interlock(self):
        url = "https://example.invalid/source.git"
        with patch.object(module, "command", side_effect=["origin\nupstream\n", "DISABLED_READ_ONLY_UPSTREAM\n" + url + "\n"]):
            safe, detail = module.upstream_push_safety()
        self.assertFalse(safe)
        self.assertNotIn(url, detail)

    def test_multiple_interlocked_push_urls_pass(self):
        with patch.object(module, "command", side_effect=["upstream\n", "DISABLED_READ_ONLY_UPSTREAM\nDISABLED_READ_ONLY_UPSTREAM\n"]):
            safe, _ = module.upstream_push_safety()
        self.assertTrue(safe)

    def test_empty_push_url_list_does_not_vacuously_pass(self):
        with patch.object(module, "command", side_effect=["upstream\n", ""]):
            safe, _ = module.upstream_push_safety()
        self.assertFalse(safe)

    def test_configured_unsafe_upstream_fails_without_echoing_url(self):
        url = "https://example.invalid/source.git"
        with patch.object(module, "command", side_effect=["upstream\norigin\n", url + "\n"]):
            safe, detail = module.upstream_push_safety()
        self.assertFalse(safe)
        self.assertNotIn(url, detail)
        self.assertIn("URL omitted", detail)

    def test_lookup_failure_is_not_silently_accepted(self):
        with patch.object(module, "command", side_effect=["origin\nupstream\n", RuntimeError("lookup failed")]):
            with self.assertRaisesRegex(RuntimeError, "lookup failed"):
                module.upstream_push_safety()


if __name__ == "__main__":
    unittest.main()
