"""Offline issue-postcondition tests; deliberately no live GitHub calls."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import verify_github_issues as module


class IssueVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs/audit").mkdir(parents=True)
        (self.root / "docs/migration").mkdir(parents=True)
        self.body = "<!-- nativecmpkit-item:audit:IO-001 -->\nEvidence\n"
        self.item = {"key": "audit:IO-001", "title": "A finding", "body_sha256": hashlib.sha256(self.body.encode()).hexdigest(), "labels": ["audit"]}
        self.receipt = {**self.item, "number": 1, "url": "https://github.com/Apdelrahman1911/nativeCmpkit/issues/1", "actual_state": "open", "github_author": "Apdelrahman1911", "github_created_at": "2026-10-24T16:00:00Z", "pending_initial_close": False}
        self.issue = {"number": 1, "html_url": self.receipt["url"], "body": self.body, "title": self.item["title"], "labels": [{"name": "audit"}], "state": "open", "user": {"login": "Apdelrahman1911"}, "created_at": self.receipt["github_created_at"]}
        self.remote = [self.issue]

    def run_check(self):
        (self.root / "docs/audit/issue-plan.json").write_text(json.dumps({"repository": module.REPO, "items": [self.item]}))
        (self.root / "docs/migration/issue-map.json").write_text(json.dumps({"repository": module.REPO, "complete": True, "items": [self.receipt]}))
        def fake_gh(endpoint, method="GET", data=None, paginate=False):
            self.assertEqual("GET", method)
            self.assertIsNone(data)
            if endpoint == "repos/" + module.REPO:
                return {"full_name": module.REPO, "fork": False}
            self.assertIn("/issues?state=all&per_page=100", endpoint)
            self.assertTrue(paginate)
            return [self.remote]
        output = io.StringIO()
        with patch.object(module, "ROOT", self.root), patch.object(module, "gh", fake_gh), patch("sys.argv", ["verify"]), redirect_stdout(output):
            status = module.main()
        return status, json.loads(output.getvalue())

    def test_complete_matching_remote_passes(self):
        status, report = self.run_check()
        self.assertEqual(0, status)
        self.assertEqual({"open": 1}, report["states"])

    def test_changed_body_does_not_pass(self):
        self.issue["body"] += "edited"
        status, report = self.run_check()
        self.assertEqual(1, status)
        self.assertIn("audit:IO-001: body_hash", report["errors"])

    def test_missing_issue_is_reported(self):
        self.remote.clear()
        status, report = self.run_check()
        self.assertEqual(1, status)
        self.assertIn("Plan/remote managed key sets differ", report["errors"])

    def test_unmanaged_issues_remain_unmodified(self):
        self.remote.append({"number": 2, "body": "Owner's own issue"})
        status, report = self.run_check()
        self.assertEqual(0, status)
        self.assertEqual(1, report["unmanaged_issues_untouched"])

    def test_duplicate_managed_marker_fails(self):
        self.remote.append(dict(self.issue, number=2))
        status, report = self.run_check()
        self.assertEqual(1, status)
        self.assertIn("Duplicate remote marker: audit:IO-001", report["errors"])

    def test_pending_closure_fails(self):
        self.receipt["pending_initial_close"] = True
        status, report = self.run_check()
        self.assertEqual(1, status)
        self.assertIn("audit:IO-001: no_pending_initial_closure", report["errors"])


if __name__ == "__main__":
    unittest.main()
