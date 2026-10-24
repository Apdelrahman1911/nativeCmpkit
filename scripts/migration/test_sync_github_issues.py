"""Offline migration issue-sync tests: all GitHub calls and sleeps are fakes.

Run: python3 -m unittest discover -s scripts/migration -p test_sync_github_issues.py -v
No credentials, network requests, actual issue mutations or real audit drafts.
"""

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sync_github_issues as sync


def finding(key="NAV-001", priority="High"):
    return dict(
        id=key, title="Synthetic source-confirmed behavior", priority=priority,
        status="confirmed-source", modules=["fixture-module"],
        locations=[dict(path="fixture source.kt", lines="3-5", symbol="fixture")],
        root_cause="Synthetic ignored input.", impact="Synthetic missing output.",
        recommendation="Validate and forward input.", risks="Preserve compatibility.",
        required_tests=["Verify synthetic input reaches output."],
        evidence=["This is an offline test fixture, not a real finding."],
        upstream_refs=["https://github.com/MohamedRejeb/Calf/issues/34"],
        effort="S", dependencies=[],
    )


def decision(number=34, topic="synthetic-topic", **overrides):
    value = dict(
        upstream_number=number, dedupe_key=topic, priority="Low",
        title=f"Synthetic upstream item {number}", kind="issue", state="open",
        disposition="needs_reproduction", finding_ids=[],
        original_author=f"fixture-author-{number}", original_id=number + 1000,
        original_node_id=f"fixture-node-{number}", created_at="2020-01-01T00:00:00Z",
        updated_at="2021-01-01T00:00:00Z",
        url=f"https://github.com/MohamedRejeb/Calf/issues/{number}",
        rationale="Historical report is not a current reproduction.",
        locations=[dict(path="fixture.kt", lines="1-2", symbol="fixture")],
        recommended_next_step="Run a scoped reproduction, not a rewrite.",
    )
    value.update(overrides)
    return value


class FakeGitHub:
    """Stateful, strict fake of only the REST endpoints used by this script."""

    def __init__(self):
        self.repo = dict(fork=False, owner=dict(login="Apdelrahman1911"), full_name=sync.REPO)
        self.login = "Apdelrahman1911"
        self.labels = {}
        self.issues = []
        self.calls = []
        self.fail_post_after_persist = False
        self.fail_close_after_persist = False

    @property
    def mutations(self):
        return [c for c in self.calls if c[1] != "GET"]

    @property
    def issue_posts(self):
        return [c for c in self.calls if c[:2] == (f"repos/{sync.REPO}/issues", "POST")]

    def __call__(self, endpoint, method="GET", data=None, paginate=False):
        self.calls.append((endpoint, method, copy.deepcopy(data)))
        prefix = f"repos/{sync.REPO}"
        if endpoint == prefix and method == "GET":
            return copy.deepcopy(self.repo)
        if endpoint == "user" and method == "GET":
            return dict(login=self.login)
        if endpoint == prefix + "/labels?per_page=100" and method == "GET":
            assert paginate
            return [copy.deepcopy(list(self.labels.values()))]
        if endpoint == prefix + "/issues?state=all&per_page=100" and method == "GET":
            assert paginate
            # Two pages exercise the --slurp flattening contract, even for tiny fixtures.
            return [copy.deepcopy(self.issues[:1]), copy.deepcopy(self.issues[1:])]
        if endpoint == prefix + "/labels" and method == "POST":
            assert data["name"] not in self.labels, "duplicate label POST"
            self.labels[data["name"]] = copy.deepcopy(data)
            return copy.deepcopy(data)
        if endpoint == prefix + "/issues" and method == "POST":
            number = max((x["number"] for x in self.issues), default=0) + 1
            issue = dict(number=number, title=data["title"], body=data["body"],
                         labels=[dict(name=x) for x in data["labels"]], state="open",
                         html_url=f"https://github.com/{sync.REPO}/issues/{number}",
                         created_at="2026-10-24T00:00:00Z", user=dict(login=self.login))
            self.issues.append(issue)
            if self.fail_post_after_persist:
                self.fail_post_after_persist = False
                raise RuntimeError("Synthetic uncertain POST response after server commit")
            return copy.deepcopy(issue)
        if endpoint.startswith(prefix + "/issues/") and method == "PATCH":
            number = int(endpoint.rsplit("/", 1)[1])
            issue = next(x for x in self.issues if x["number"] == number)
            for key, value in data.items():
                issue[key] = [dict(name=x) for x in value] if key == "labels" else value
            if data.get("state") == "closed" and self.fail_close_after_persist:
                self.fail_close_after_persist = False
                raise RuntimeError("Synthetic uncertain close response after server commit")
            return copy.deepcopy(issue)
        raise AssertionError(f"Unexpected API request: {method} {endpoint}")


class IssueSyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-issue-sync-test-")
        self.root = Path(self.temporary.name)
        (self.root / "docs/audit/findings").mkdir(parents=True)
        (self.root / "docs/migration").mkdir(parents=True)
        self.api = FakeGitHub()
        self.write_inputs()

    def tearDown(self):
        self.temporary.cleanup()

    def write_inputs(self, findings=None, decisions=None, resolutions=None):
        for name, value in [
            ("docs/audit/findings/NAV.json", [finding()] if findings is None else findings),
            ("docs/migration/upstream-actionable-decisions.json", decisions or []),
            ("docs/audit/migration-resolutions.json", resolutions or {}),
        ]:
            (self.root / name).write_text(json.dumps(value))

    def run_sync(self, apply=False, sleep=None):
        argv = ["sync_github_issues.py"] + (["--apply", "--delay", "-1"] if apply else [])
        # Fail closed if a new code path ever bypasses the API fake and starts gh.
        with patch.object(sync, "ROOT", self.root), patch.object(sync, "gh", self.api), \
                patch.object(sync.time, "sleep", side_effect=sleep), \
                patch.object(sync.subprocess, "run", side_effect=AssertionError("No subprocess/network in fixture")), \
                patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()):
            sync.main()
        return json.loads((self.root / "docs/audit/issue-plan.json").read_text())

    def receipt(self):
        return json.loads((self.root / "docs/migration/issue-map.json").read_text())

    def resolution(self):
        return {"NAV-001": dict(state="closed", reason="Synthetic resolved source condition.",
                                verification=["fixture-check.json"], remaining_caution="No release authorized.")}

    def test_default_is_local_only_and_drafts_hash_exact_body(self):
        plan = self.run_sync()
        self.assertEqual(self.api.calls, [])
        self.assertEqual((plan["repository"], plan["baseline"], plan["count"]), (sync.REPO, sync.BASE, 1))
        item = plan["items"][0]
        draft = (self.root / "docs/audit/issue-drafts/audit-NAV-001.md").read_text()
        body = draft.split("\n\n", 1)[1]
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), item["body_sha256"])
        self.assertEqual(sync.managed_key(body), item["key"])
        self.assertIn("/blob/" + sync.BASE + "/fixture%20source.kt#L3-L5", body)

    def test_binary_location_does_not_invent_line_anchor(self):
        link = sync.source_links([dict(path="font file.ttf", lines="binary (entire file)", symbol="font")])
        self.assertIn("font%20file.ttf", link)
        self.assertNotIn("#L", link)

    def test_original_number_map_does_not_import_other_repositories_numbers(self):
        references = [
            "https://github.com/z-galaxy/zbus/issues/2043",
            "https://github.com/MohamedRejeb/Calf/issues/34#comment",
            "https://github.com/MohamedRejeb/Calf/pull/12/files",
            "https://github.com/MohamedRejeb/Calf/issues/34?query=fixture",
            "https://github.com/MohamedRejeb/Calf/issues/99not-a-number",
            "https://not-github.example/MohamedRejeb/Calf/issues/999",
        ]
        self.assertEqual(sync.calf_upstream_numbers(references), [12, 34])
        f = finding()
        f["upstream_refs"] = references
        self.write_inputs(findings=[f])
        self.assertEqual(self.run_sync()["items"][0]["upstream_numbers"], [12, 34])

    def test_markers_must_be_unique_and_at_first_line(self):
        marker = sync.PREFIX + "audit:NAV-001 -->\n"
        self.assertEqual(sync.managed_key(marker + "content"), "audit:NAV-001")
        self.assertIsNone(sync.managed_key(None))
        self.assertIsNone(sync.managed_key("ordinary issue"))
        for body in ["quoted\n" + marker, marker + marker, marker.strip(),
                     sync.PREFIX + "audit:../../elsewhere -->\n"]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                sync.managed_key(body)

    def test_body_limit_stops_before_remote_request(self):
        f = finding()
        f["evidence"] = ["é" * 40000]
        self.write_inputs(findings=[f])
        with self.assertRaises(ValueError):
            self.run_sync(apply=True)
        self.assertEqual(self.api.calls, [])

    def test_duplicate_input_ids_stop_before_remote_request(self):
        self.write_inputs(findings=[finding(), finding()])
        with self.assertRaises(ValueError):
            self.run_sync(apply=True)
        self.assertEqual(self.api.calls, [])

    def test_topic_grouping_is_order_independent_and_retains_all_originals(self):
        a = decision(72, priority="Low")
        b = decision(34, priority="High", disposition="separate_improvement")
        first = sync.inherited_items([a, b])
        self.assertEqual(first, sync.inherited_items([b, a]))
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["upstream_numbers"], [34, 72])
        self.assertIn("priority:high", first[0]["labels"])
        self.assertIn("evidence:unverified", first[0]["labels"])
        self.assertEqual(sync.managed_key(first[0]["body"]), first[0]["key"])
        for d in [a, b]:
            self.assertIn(d["url"], first[0]["body"])
            self.assertIn(d["original_author"], first[0]["body"])
        # Adding a new member cannot change the existing topic identity.
        self.assertEqual(first[0]["key"], sync.inherited_items([a, b, decision(10)])[0]["key"])

    def test_duplicate_upstream_numbers_and_empty_topics_rejected(self):
        for values in [[decision(), decision(topic="different")], [decision(topic="")]]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                sync.inherited_items(values)

    def test_covered_or_nonactionable_upstream_items_are_not_duplicated(self):
        values = [decision(1, finding_ids=["NAV-001"]), decision(2, disposition="implemented"), decision(3)]
        self.assertEqual([x["upstream_numbers"] for x in sync.inherited_items(values)], [[3]])

    def test_first_apply_then_identical_rerun_has_no_mutations(self):
        self.run_sync(apply=True)
        self.assertEqual(len(self.api.issue_posts), 1)
        self.api.calls.clear()
        self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])
        self.assertTrue(self.receipt()["complete"])
        self.assertEqual(len(self.receipt()["items"]), 1)

    def test_delay_is_clamped_to_two_seconds(self):
        delays = []
        self.run_sync(apply=True, sleep=delays.append)
        self.assertTrue(delays)
        self.assertTrue(all(x >= 2 for x in delays))

    def test_rejects_fork_wrong_owner_redirect_and_wrong_authenticated_user(self):
        variants = [dict(fork=True), dict(owner=dict(login="other")),
                    dict(full_name="Apdelrahman1911/another-repository")]
        for variation in variants:
            with self.subTest(variation=variation):
                self.api = FakeGitHub()
                self.api.repo.update(variation)
                with self.assertRaises(RuntimeError):
                    self.run_sync(apply=True)
                self.assertEqual(self.api.mutations, [])
        self.api = FakeGitHub()
        self.api.login = "other"
        with self.assertRaises(RuntimeError):
            self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])

    def test_duplicate_remote_markers_abort_without_issue_mutations(self):
        self.run_sync(apply=True)
        duplicate = copy.deepcopy(self.api.issues[0])
        duplicate["number"] = 100
        self.api.issues.append(duplicate)
        self.api.calls.clear()
        with self.assertRaises(RuntimeError):
            self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])

    def test_marked_pull_requests_are_never_treated_as_issues(self):
        self.run_sync(apply=True)
        pr = copy.deepcopy(self.api.issues[0])
        pr.update(number=100, pull_request=dict(url="fixture"))
        self.api.issues.append(pr)
        self.api.calls.clear()
        self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])

    def test_managed_marker_from_other_author_is_refused(self):
        self.run_sync(apply=True)
        self.api.issues[0]["user"]["login"] = "unrelated-author"
        self.api.calls.clear()
        with self.assertRaises(RuntimeError):
            self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])

    def test_owner_labels_and_closed_state_survive_rerun(self):
        self.run_sync(apply=True)
        self.api.issues[0]["labels"].append(dict(name="owner:triaged"))
        self.api.issues[0]["state"] = "closed"
        self.api.calls.clear()
        self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])
        self.assertIn("owner:triaged", {x["name"] for x in self.api.issues[0]["labels"]})
        self.assertEqual(self.receipt()["items"][0]["actual_state"], "closed")

    def test_known_generator_change_updates_only_unchanged_managed_content(self):
        self.run_sync(apply=True)
        self.api.issues[0]["labels"].append(dict(name="owner:triaged"))
        changed = finding(priority="Medium")
        changed["title"] = "Revised synthetic source diagnosis"
        changed["root_cause"] = "Better documented synthetic cause."
        self.write_inputs(findings=[changed])
        self.api.calls.clear()
        self.run_sync(apply=True)
        self.assertEqual(len(self.api.issue_posts), 0)
        self.assertIn(changed["root_cause"], self.api.issues[0]["body"])
        labels = {x["name"] for x in self.api.issues[0]["labels"]}
        self.assertIn("owner:triaged", labels)
        self.assertIn("priority:medium", labels)
        self.assertNotIn("priority:high", labels)

    def test_owner_edited_body_or_title_is_not_overwritten(self):
        self.run_sync(apply=True)
        original = copy.deepcopy(self.api.issues[0])
        for field in ["title", "body"]:
            self.api.issues[0] = copy.deepcopy(original)
            self.api.issues[0][field] += "\nOwner supplied additional context."
            self.api.calls.clear()
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                self.run_sync(apply=True)
            self.assertEqual(self.api.mutations, [])

    def test_missing_previous_marker_is_not_recreated(self):
        self.run_sync(apply=True)
        self.api.issues[0]["body"] = "Owner rewrote this issue without the managed marker."
        self.api.calls.clear()
        with self.assertRaises(RuntimeError):
            self.run_sync(apply=True)
        self.assertEqual(self.api.issue_posts, [])
        self.assertEqual(len(self.api.issues), 1)

    def test_receipt_issue_number_mismatch_is_rejected(self):
        self.run_sync(apply=True)
        self.api.issues[0]["number"] = 99
        self.api.calls.clear()
        with self.assertRaises(RuntimeError):
            self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])

    def test_interrupted_update_preserves_unprocessed_prior_receipts(self):
        self.write_inputs(findings=[finding(), finding("NAV-002")])
        self.run_sync(apply=True)
        previous = {x["key"]: x for x in self.receipt()["items"]}
        changed = finding()
        changed["root_cause"] = "Revised managed cause for the first issue."
        self.write_inputs(findings=[changed, finding("NAV-002")])
        self.api.issues[1]["body"] += "\nOwner changed the second issue."
        with self.assertRaises(RuntimeError):
            self.run_sync(apply=True)
        saved = self.receipt()
        self.assertFalse(saved["complete"])
        entries = {x["key"]: x for x in saved["items"]}
        self.assertEqual(entries["audit:NAV-002"], previous["audit:NAV-002"])
        self.assertNotEqual(entries["audit:NAV-001"]["body_sha256"], previous["audit:NAV-001"]["body_sha256"])
        self.assertFalse((self.root / "docs/migration/issue-map.json.tmp").exists())

    def test_uncertain_post_is_not_retried_and_rerun_reconciles_by_marker(self):
        self.api.fail_post_after_persist = True
        with self.assertRaises(RuntimeError):
            self.run_sync(apply=True)
        self.assertEqual(len(self.api.issue_posts), 1)
        self.assertEqual(len(self.api.issues), 1)
        self.api.calls.clear()
        self.run_sync(apply=True)
        self.assertEqual(self.api.issue_posts, [])
        self.assertEqual(self.receipt()["items"][0]["number"], self.api.issues[0]["number"])

    def test_initial_resolution_closes_once_and_manual_reopen_is_preserved(self):
        self.write_inputs(resolutions=self.resolution())
        self.run_sync(apply=True)
        self.assertEqual(self.api.issues[0]["state"], "closed")
        self.assertFalse(self.receipt()["items"][0]["pending_initial_close"])
        self.api.issues[0]["state"] = "open"
        self.api.calls.clear()
        self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])
        self.assertEqual(self.api.issues[0]["state"], "open")

    def test_pending_initial_close_survives_interruption_after_successful_post(self):
        self.write_inputs(resolutions=self.resolution())

        def interrupt_after_issue_post(_):
            if self.api.issues:
                raise KeyboardInterrupt("Synthetic interruption after POST receipt")

        with self.assertRaises(KeyboardInterrupt):
            self.run_sync(apply=True, sleep=interrupt_after_issue_post)
        self.assertTrue(self.receipt()["items"][0]["pending_initial_close"])
        self.assertFalse(self.receipt()["complete"])
        self.api.calls.clear()
        self.run_sync(apply=True)
        self.assertEqual(self.api.issue_posts, [])
        self.assertEqual(self.api.issues[0]["state"], "closed")
        self.assertFalse(self.receipt()["items"][0]["pending_initial_close"])

    def test_uncertain_close_is_reconciled_without_a_second_state_patch(self):
        self.write_inputs(resolutions=self.resolution())
        self.api.fail_close_after_persist = True
        with self.assertRaises(RuntimeError):
            self.run_sync(apply=True)
        self.api.calls.clear()
        self.run_sync(apply=True)
        self.assertEqual(self.api.mutations, [])
        self.assertFalse(self.receipt()["items"][0]["pending_initial_close"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
