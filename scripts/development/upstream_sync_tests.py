#!/usr/bin/env python3
"""Offline safety and complete-content checks for the 2026-10-24 sync handoff."""

import hashlib
from pathlib import Path
import tempfile
import unittest

import upstream_sync as sync


SNAPSHOT = sync.ROOT / "docs/migration/upstream-updates/20261024T183300Z"
REPORT = sync.ROOT / "docs/development/upstream-sync-20261024T183300Z"


class SyncSafetyTests(unittest.TestCase):
    def test_fence_preserves_arbitrary_original_markdown(self):
        original = "Hello\n````markdown\n<!-- fake marker -->\n````\némoji 🗺️"
        quoted = sync.quoted_markdown(original)
        self.assertEqual(quoted, "`````markdown\n" + original + "\n`````")

    def test_strict_destination_marker(self):
        valid = "<!-- nativecmpkit-item:audit:IO-001 -->\ntext"
        self.assertEqual(sync.managed_key(valid), "audit:IO-001")
        for invalid in ["text " + valid, valid + "\n" + valid, "<!-- nativecmpkit-item:audit:IO-001x -->\ntext"]:
            with self.assertRaises(ValueError):
                sync.managed_key(invalid)

    def test_hash_verifier_rejects_extra_files_and_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "record.json").write_text("[]")
            sync.freeze(path)
            self.assertEqual(sync.verify_frozen(path), 1)
            (path / "unexpected.json").write_text("[]")
            with self.assertRaises(ValueError):
                sync.verify_frozen(path)
            (path / "unexpected.json").unlink()
            (path / "record.json").write_text("{}")
            with self.assertRaises(ValueError):
                sync.verify_frozen(path)

    def test_fresh_snapshot_integrity(self):
        self.assertEqual(sync.verify_frozen(SNAPSHOT), 170)
        receipt = sync.read(SNAPSHOT / "receipt.json")
        self.assertTrue(receipt["complete"])
        self.assertTrue(all(receipt["checks"].values()))
        self.assertEqual(receipt["source_open_issue_count"], 16)
        self.assertEqual(receipt["source_open_pr_numbers"], [551])

    def test_every_original_description_and_comment_preserved(self):
        handoff = sync.read(REPORT / "mutation-handoff.json")
        self.assertEqual(handoff["create_issue_operations"], [])
        self.assertEqual(len(handoff["comment_operations"]), 16)
        source_numbers = {issue["number"] for issue in sync.read(SNAPSHOT / "source/open-issues.json")}
        self.assertEqual({operation["source_number"] for operation in handoff["comment_operations"]}, source_numbers)
        remote = {issue["number"]: issue for issue in sync.read(SNAPSHOT / "destination/issues.json")}
        for operation in handoff["comment_operations"]:
            number = operation["source_number"]
            body = operation["body"]
            self.assertEqual(body.splitlines()[0], operation["dedupe_marker"])
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), operation["body_sha256"])
            self.assertLessEqual(len(body.encode()), 62000)
            original = sync.read(SNAPSHOT / f"source/issues/{number}/detail.json")
            self.assertIn(sync.quoted_markdown(original["body"]), body)
            for label in original["labels"]:
                self.assertIn(f"`{label['name']}`", body)
            for comment in sync.read(SNAPSHOT / f"source/issues/{number}/comments.json"):
                self.assertIn(sync.quoted_markdown(comment["body"]), body)
                self.assertIn(comment["html_url"], body)
                self.assertIn(str(comment["id"]), body)
                self.assertIn(comment["created_at"], body)
            destination = remote[operation["issue_number"]]
            self.assertEqual(destination["id"], operation["expected_issue_id"])
            self.assertEqual(destination["state"], operation["expected_issue_state"])
            self.assertEqual(hashlib.sha256(destination["body"].encode()).hexdigest(), operation["expected_issue_body_sha256"])
            self.assertEqual((REPORT / f"drafts/upstream-{number:04}-comment.md").read_bytes().decode(), body)

    def test_lifecycle_and_observation_differences_explicit(self):
        entries = {item["source_number"]: item for item in sync.read(REPORT / "reconciliation.json")}
        self.assertEqual({number for number, item in entries.items() if item["disposition"] == "already_implemented"}, {288, 344})
        self.assertEqual(entries[344]["primary_destination"]["number"], 75)
        self.assertEqual(entries[288]["primary_destination"]["number"], 77)
        self.assertTrue(all(item["primary_destination"]["state"] == "open" for item in entries.values()))
        self.assertTrue(all(item["original_description_labels_author_and_comments_unchanged"] for item in entries.values()))
        events = [event for item in entries.values() for event in item["added_timeline_entries"]]
        self.assertEqual(len(events), 17)
        self.assertTrue(all(event["event"] == "cross-referenced" and event["source_url"].startswith(f"https://github.com/{sync.DESTINATION}/issues/") for event in events))


if __name__ == "__main__":
    unittest.main()
