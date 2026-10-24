"""Offline safeguards for the one-purpose destination comment writer."""
import unittest
from copy import deepcopy
import apply_upstream_context as module


class ContextWriterTests(unittest.TestCase):
    def setUp(self):
        marker = "<!-- nativecmpkit-upstream-sync:674932206:27 -->"
        self.operation = {"operation": "create_issue_comment", "repository": module.REPO,
            "issue_number": 151, "source_number": 27, "dedupe_marker": marker,
            "body": marker + "\nhttps://example.invalid/TOKEN/file\n",
            "expected_issue_id": 123, "expected_issue_state": "open",
            "expected_issue_body_sha256": module.sha256("technical finding")}
        self.operation["body_sha256"] = module.sha256(self.operation["body"])
        self.issue = {"id": 123, "number": 151, "body": "technical finding", "state": "open",
                      "html_url": f"https://github.com/{module.REPO}/issues/151"}
        self.body = module.render(self.operation, "TOKEN", "a" * 40)

    def test_valid_draft_is_bound_to_immutable_revision(self):
        self.assertIn("a" * 40, self.body)
        self.assertNotIn("TOKEN", self.body)

    def test_draft_hash_change_is_rejected(self):
        self.operation["body"] += "changed"
        with self.assertRaises(ValueError):
            module.render(self.operation, "TOKEN", "a" * 40)

    def test_no_marker_duplicate_or_cross_repository_operation(self):
        for change in [{"repository": module.SOURCE}, {"dedupe_marker": "wrong"}, {"issue_number": -1}]:
            operation = {**self.operation, **change}
            with self.assertRaises(ValueError):
                module.render(operation, "TOKEN", "a" * 40)

    def test_no_existing_comment_plans_exactly_one(self):
        self.assertIsNone(module.reconcile(self.operation, self.issue, [], self.body))

    def test_identical_existing_comment_is_reused(self):
        comment = {"body": self.body, "id": 7}
        self.assertEqual(comment, module.reconcile(self.operation, self.issue, [comment], self.body))

    def test_edited_comment_is_preserved_by_refusal(self):
        with self.assertRaises(ValueError):
            module.reconcile(self.operation, self.issue, [{"body": self.body + "human edit"}], self.body)

    def test_duplicate_marker_is_rejected(self):
        with self.assertRaises(ValueError):
            module.reconcile(self.operation, self.issue, [{"body": self.body}, {"body": self.body}], self.body)

    def test_changed_issue_body_or_state_or_identity_is_rejected(self):
        for change in [{"body": "human edit"}, {"state": "closed"}, {"id": 999}, {"pull_request": {}}]:
            with self.assertRaises(ValueError):
                module.reconcile(self.operation, {**self.issue, **change}, [], self.body)

    def test_source_api_mutation_is_rejected_before_network(self):
        with self.assertRaises(ValueError):
            module.api(f"repos/{module.SOURCE}/issues/27/comments", "POST", {"body": "invalid"})


if __name__ == "__main__":
    unittest.main()
