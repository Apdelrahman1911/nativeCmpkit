"""Offline source-remote safety checks; no Git/GitHub mutation or network calls."""
import unittest
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import call, patch

import verify_migration as module


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
