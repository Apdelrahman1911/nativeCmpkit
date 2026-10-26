#!/usr/bin/env python3
"""Offline fixture tests. No repository ledgers, source, network or build is changed."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import validate_resolutions as validator


FINDINGS = f"{validator.FINDING_DIR}/fixture.json"
LEDGER = f"{validator.LEDGER_DIR}/fixture.json"


def fixtures(count: int = 3) -> dict[str, object]:
    baselines, resolutions, issues, plans = [], [], [], []
    for index in range(1, count + 1):
        fid = f"FIX-{index:03d}"
        deps = [f"FIX-{index - 1:03d}"] if index > 1 else []
        baseline = {
            "id": fid, "title": f"Fixture finding {index}", "priority": "High",
            "status": "confirmed-source", "modules": ["fixture-module"],
            "locations": [{"path": "fixture-module/src/OldFile.kt", "lines": "10-20", "symbol": "example"}],
            "root_cause": "Fixture only; no real code evaluated.",
            "impact": "An unproven runtime outcome.", "recommendation": "Run the original acceptance checks.",
            "risks": "Source changes do not prove the platform behavior.",
            "required_tests": [f"Original runtime acceptance {index}.", "Literal | <tag> [brackets] `code` & Unicode λ\nSecond line."],
            "evidence": ["Baseline source review, not runtime evidence."], "upstream_refs": [],
            "effort": "M", "dependencies": deps,
        }
        owner = {
            "id": fid, "status": "implemented", "changes": ["Owner-described source change."],
            "affected_paths": ["fixture-module/src/Replacement.kt"],
            "tests": [{"command": "fixture command, never executed", "result": "PASS prose is not independent proof.", "evidence": []}],
            "remaining": ["Owner records a different acceptance description."],
            "compatibility": "Retained compatibility, not certified.",
        }
        number = 1000 + index  # Issue numbers and roadmap order must not be conflated.
        issue = {
            "key": f"audit:{fid}", "finding_ids": [fid], "number": number,
            "url": f"https://github.com/{validator.REPOSITORY}/issues/{number}",
            "title": f"[High][{fid}] Fixture finding {index}", "state": "open",
            "actual_state": "closed" if index == 1 else "open", "upstream_numbers": [],
        }
        plan = {
            "order": index, "key": issue["key"], "finding": fid, "title": baseline["title"],
            "phase": 1, "priority": baseline["priority"], "evidence_status": baseline["status"],
            "effort": baseline["effort"], "dependencies": list(deps), "modules": baseline["modules"][:],
            "workstream": "Fixture workstream", "state": issue["state"], "issue_url": issue["url"],
            "required_tests": baseline["required_tests"][:],
        }
        baselines.append(baseline)
        resolutions.append(owner)
        issues.append(issue)
        plans.append(plan)
    # Six original-history topics are separate from the audited finding denominator.
    # Like the real archive, these have triage-first effort and omit `modules`/`finding`.
    for index in range(1, 7):
        number = 2000 + index
        issue = {
            "key": f"upstream-topic:fixture-{index}", "finding_ids": [], "number": number,
            "url": f"https://github.com/{validator.REPOSITORY}/issues/{number}",
            "title": f"Historical topic {index}", "state": "open", "upstream_numbers": [index],
        }
        issues.append(issue)
        plans.append({
            "order": count + index, "key": issue["key"], "title": issue["title"], "phase": 3,
            "priority": "Low", "evidence_status": "improvement", "effort": "triage-first",
            "dependencies": [], "upstream_numbers": [index], "workstream": "Historical requests",
            "state": "open", "issue_url": issue["url"], "required_tests": ["Triage before implementation."],
        })
    return {
        FINDINGS: baselines, LEDGER: resolutions,
        validator.ISSUE_MAP: {
            "schema_version": 1, "repository": validator.REPOSITORY, "baseline": validator.BASELINE,
            "complete": True, "items": issues,
        },
        validator.ROADMAP: {
            "baseline": validator.BASELINE, "ordering": "Original dependency-respecting order.",
            "phases": {"1": "Before preview", "3": "Historical topics"}, "items": plans,
        },
    }


class ResolutionFixtures(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-resolution-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = fixtures()
        self.save()

    def save(self) -> None:
        for relative, data in self.data.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(validator.canonical(data))

    def snapshot(self) -> dict[str, object]:
        return validator.build_snapshot(self.root, expected_count=3)

    def invalid(self, pattern: str = ".") -> None:
        self.save()
        with self.assertRaisesRegex(validator.ValidationError, pattern):
            self.snapshot()

    def reset(self) -> None:
        self.data = fixtures()

    def test_valid_snapshot_keeps_all_requirements_and_entire_owner_record(self) -> None:
        owner = self.data[LEDGER][0]
        owner["verification_scope"] = "One host only."
        owner["extra_evidence_context"] = {"new_optional_field": "Retained unchanged."}
        owner["tests"][0].update(test_count=0, report_count=0, failures=0, errors=0, skipped=0)
        self.save()
        model = self.snapshot()
        self.assertEqual(3, model["counts"]["baseline_findings"])
        self.assertEqual(3, model["counts"]["unique_resolution_ids"])
        self.assertEqual(3, model["counts"]["mapped_findings"])
        for index, item in enumerate(model["items"]):
            self.assertEqual(self.data[FINDINGS][index]["required_tests"], item["original_required_tests"])
            self.assertEqual(self.data[LEDGER][index], item["owner_record"])
            self.assertEqual(self.data[FINDINGS][index]["dependencies"], item["original_dependencies"])
            self.assertEqual(index + 1, item["original_order"])
            self.assertEqual(index + 1001, item["issue"]["number"])
            self.assertFalse(item["closure_or_release_authorized_by_index"])
        self.assertEqual(0, model["counts"]["status_promotions"])
        self.assertEqual(0, model["counts"]["automatic_closures"])

    def test_legal_statuses_are_copied_without_inference(self) -> None:
        for status in validator.STATUSES:
            with self.subTest(status=status):
                self.reset()
                owner = self.data[LEDGER][0]
                owner["status"] = status
                if status == "verified":
                    owner["remaining"] = []
                    owner["tests"][0]["evidence"] = ["Human must still review this reference."]
                self.save()
                model = self.snapshot()
                self.assertEqual(status, model["items"][0]["reported_status"])
                self.assertEqual(1 if status != "implemented" else 3, model["counts"]["reported_statuses"][status])

    def test_empty_changes_or_tests_are_legal_when_not_claiming_verified(self) -> None:
        self.data[LEDGER][0]["changes"] = []
        self.data[LEDGER][0]["tests"] = []
        self.data[LEDGER][0]["status"] = "unresolved"
        self.save()
        self.assertEqual("unresolved", self.snapshot()["items"][0]["reported_status"])

    def test_compatibility_and_evidence_support_string_or_string_array(self) -> None:
        for compatibility in ("Compatibility scope.", ["First scope.", "Second scope."]):
            for evidence in ([], ["methodName"], "not-an-existing-evidence-file"):
                with self.subTest(compatibility=compatibility, evidence=evidence):
                    self.data[LEDGER][0]["compatibility"] = compatibility
                    self.data[LEDGER][0]["tests"][0]["evidence"] = evidence
                    self.save()
                    self.assertEqual(self.data[LEDGER][0], self.snapshot()["items"][0]["owner_record"])

    def test_pass_prose_and_historically_closed_issue_do_not_promote(self) -> None:
        model = self.snapshot()
        item = model["items"][0]
        self.assertEqual("closed", item["issue"]["historical_mapping_state"])
        self.assertEqual("implemented", item["reported_status"])
        self.assertEqual(0, model["counts"]["reported_statuses"]["verified"])

    def test_verified_requires_explicit_evidence_not_just_pass_prose(self) -> None:
        for tests in ([], [{"command": "command", "result": "PASS all tests", "evidence": []}]):
            with self.subTest(tests=tests):
                self.reset()
                self.data[LEDGER][0].update(status="verified", remaining=[], tests=tests)
                self.invalid("require explicit nonempty")

    def test_verified_requires_empty_remaining_checks(self) -> None:
        self.data[LEDGER][0]["status"] = "verified"
        self.data[LEDGER][0]["tests"][0]["evidence"] = "Explicit but not certified."
        self.invalid("no remaining checks")

    def test_verified_evidence_is_structural_not_a_certified_pass(self) -> None:
        self.data[LEDGER][0]["status"] = "verified"
        self.data[LEDGER][0]["remaining"] = []
        self.data[LEDGER][0]["tests"][0].update(result="FAIL prose deliberately retained for human review", evidence=["an unreviewed reference"])
        self.save()
        model = self.snapshot()
        self.assertEqual("verified", model["items"][0]["reported_status"])
        self.assertIn("not independently validated", model["verified_schema_policy"])

    def test_missing_duplicate_unknown_owner_ids_are_rejected(self) -> None:
        mutations = (
            (lambda rows: rows.pop(), "missing resolution IDs"),
            (lambda rows: rows.append(copy.deepcopy(rows[0])), "duplicate resolution ID"),
            (lambda rows: rows[0].update(id="FIX-999"), "unknown resolution ID"),
            (lambda rows: rows[0].update(id="malformed"), "invalid stable finding ID"),
        )
        for change, expected in mutations:
            with self.subTest(expected=expected):
                self.reset()
                change(self.data[LEDGER])
                self.invalid(expected)

    def test_cross_file_duplicate_owner_ids_are_rejected(self) -> None:
        self.data[f"{validator.LEDGER_DIR}/second.json"] = [copy.deepcopy(self.data[LEDGER][0])]
        self.invalid("duplicate resolution ID")

    def test_owner_required_fields_and_illegal_status(self) -> None:
        for key in ("id", "status", "changes", "affected_paths", "tests", "remaining", "compatibility"):
            with self.subTest(missing=key):
                self.reset()
                del self.data[LEDGER][0][key]
                self.invalid("missing required fields")
        self.reset()
        self.data[LEDGER][0]["status"] = "passed"
        self.invalid("expected one of")

    def test_owner_field_types_and_empty_strings(self) -> None:
        for key, value in (("changes", "text"), ("changes", [None]), ("affected_paths", []),
                           ("tests", {}), ("remaining", "none"), ("compatibility", []),
                           ("compatibility", "  "), ("compatibility", [""]),
                           ("verification_scope", []), ("priority", "Low"), ("title", "different")):
            with self.subTest(key=key, value=value):
                self.reset()
                self.data[LEDGER][0][key] = value
                self.invalid()

    def test_test_record_required_fields_and_types(self) -> None:
        for key in ("command", "result", "evidence"):
            with self.subTest(missing=key):
                self.reset()
                del self.data[LEDGER][0]["tests"][0][key]
                self.invalid("missing required fields")
        for key, value in (("command", ""), ("result", None), ("evidence", "  "),
                           ("evidence", [""]), ("evidence", {}), ("scope", 3), ("scoped_tasks", "task")):
            with self.subTest(key=key, value=value):
                self.reset()
                self.data[LEDGER][0]["tests"][0][key] = value
                self.invalid()

    def test_optional_numeric_counts_are_nonnegative_integers_not_booleans(self) -> None:
        for key in ("test_count", "report_count", "failures", "errors", "skipped"):
            for value in (-1, True, 1.5, "1"):
                with self.subTest(key=key, value=value):
                    self.reset()
                    self.data[LEDGER][0]["tests"][0][key] = value
                    self.invalid("expected an integer")

    def test_historical_or_deleted_paths_need_not_exist(self) -> None:
        self.assertFalse((self.root / self.data[FINDINGS][0]["locations"][0]["path"]).exists())
        self.assertFalse((self.root / self.data[LEDGER][0]["affected_paths"][0]).exists())
        self.snapshot()

    def test_unsafe_reference_paths_are_rejected(self) -> None:
        for value in ("/absolute.kt", "../escape.kt", "src/../../escape.kt", "C:\\file.kt", "nul\0byte"):
            for path_kind in ("baseline", "owner"):
                with self.subTest(value=value, path_kind=path_kind):
                    self.reset()
                    if path_kind == "baseline":
                        self.data[FINDINGS][0]["locations"][0]["path"] = value
                    else:
                        self.data[LEDGER][0]["affected_paths"][0] = value
                    self.invalid("repository-relative")

    def test_baseline_id_count_duplicates_and_schema(self) -> None:
        self.data[FINDINGS].pop()
        self.invalid("expected exactly 3")
        self.reset()
        self.data[FINDINGS].append(copy.deepcopy(self.data[FINDINGS][0]))
        self.invalid("duplicate baseline ID")
        self.reset()
        self.data[f"{validator.FINDING_DIR}/second.json"] = [copy.deepcopy(self.data[FINDINGS][0])]
        self.invalid("duplicate baseline ID")

    def test_baseline_required_fields_and_schema_types(self) -> None:
        for key in self.data[FINDINGS][0]:
            with self.subTest(missing=key):
                self.reset()
                del self.data[FINDINGS][0][key]
                self.invalid("missing required fields")
        for key, value in (("priority", "Severe"), ("status", "fixed"), ("effort", "triage-first"),
                           ("modules", []), ("required_tests", []), ("locations", []),
                           ("evidence", "evidence"), ("upstream_refs", [False]), ("dependencies", ["bad"])):
            with self.subTest(key=key, value=value):
                self.reset()
                self.data[FINDINGS][0][key] = value
                self.invalid()

    def test_missing_duplicate_self_and_cyclic_dependencies(self) -> None:
        for dependencies, expected in ((["FIX-999"], "unknown dependencies"),
                                       (["FIX-001"], "self dependency"),
                                       (["FIX-002", "FIX-002"], "duplicate dependency"),
                                       (["FIX-003"], "dependency cycle")):
            with self.subTest(dependencies=dependencies):
                self.reset()
                self.data[FINDINGS][0]["dependencies"] = dependencies
                self.invalid(expected)

    def test_json_duplicate_keys_nonfinite_and_malformed_input(self) -> None:
        for raw in (b'{"id": 1, "id": 2}', b'[NaN]', b'[Infinity]', b'[-Infinity]', b'[1e999]',
                    b'[', b'\xff', b'[{"nested": {"key": 1, "key": 2}}]', b'["\\ud800"]'):
            with self.subTest(raw=raw):
                (self.root / LEDGER).write_bytes(raw)
                with self.assertRaisesRegex(validator.ValidationError, "invalid JSON"):
                    self.snapshot()
        self.save()

    def test_inputs_must_be_arrays_or_metadata_objects(self) -> None:
        for relative in (FINDINGS, LEDGER, validator.ISSUE_MAP, validator.ROADMAP):
            with self.subTest(relative=relative):
                self.reset()
                self.data[relative] = {} if relative in (FINDINGS, LEDGER) else []
                self.invalid()

    def test_issue_map_metadata_is_pinned_and_complete(self) -> None:
        for key, value in (("schema_version", 2), ("schema_version", True),
                           ("repository", "other/repository"), ("baseline", "0" * 40),
                           ("complete", False), ("complete", 1), ("items", {})):
            with self.subTest(key=key, value=value):
                self.reset()
                self.data[validator.ISSUE_MAP][key] = value
                self.invalid()

    def test_issue_map_missing_duplicate_unknown_and_mismatched_ids(self) -> None:
        cases = (
            (lambda rows: rows.pop(0), "unmapped finding IDs"),
            (lambda rows: rows.append(copy.deepcopy(rows[0])), "duplicate issue mapping key"),
            (lambda rows: rows[1].update(number=rows[0]["number"]), "duplicate issue number"),
            (lambda rows: rows[0].update(finding_ids=["FIX-002"]), "one matching finding ID"),
            (lambda rows: rows[0].update(finding_ids=[]), "one matching finding ID"),
            (lambda rows: rows[0].update(key="audit:FIX-999", finding_ids=["FIX-999"]), "unknown mapped finding ID"),
            (lambda rows: rows[0].update(finding_ids=["FIX-001", "FIX-002"]), "one matching finding ID"),
        )
        for change, expected in cases:
            with self.subTest(expected=expected):
                self.reset()
                change(self.data[validator.ISSUE_MAP]["items"])
                self.invalid(expected)

    def test_issue_urls_statuses_numbers_and_topic_mapping_are_validated(self) -> None:
        for index, key, value in ((0, "url", "https://github.com/other/repo/issues/1001"),
                                  (0, "url", "https://github.com/Apdelrahman1911/nativeCmpkit/issues/9999"),
                                  (0, "number", True), (0, "number", 0), (0, "state", "done"),
                                  (0, "actual_state", "DONE"), (3, "finding_ids", ["FIX-001"]),
                                  (3, "key", "unexpected-topic:example")):
            with self.subTest(index=index, key=key, value=value):
                self.reset()
                self.data[validator.ISSUE_MAP]["items"][index][key] = value
                self.invalid()

    def test_roadmap_preserves_priority_effort_requirements_dependencies_modules_and_title(self) -> None:
        for key, value in (("priority", "Low"), ("effort", "S"), ("title", "changed"),
                           ("evidence_status", "risk"), ("dependencies", []),
                           ("modules", ["another-module"]), ("required_tests", ["Owner PASS instead of original requirement"])):
            with self.subTest(key=key, value=value):
                self.reset()
                self.data[validator.ROADMAP]["items"][1][key] = value
                self.invalid("differs from")
        self.reset()
        self.data[validator.ROADMAP]["items"][0]["required_tests"].reverse()
        self.invalid("differs from")

    def test_roadmap_requires_modules_for_findings_not_historical_topics(self) -> None:
        model = self.snapshot()
        self.assertEqual(6, model["counts"]["imported_topics_without_finding_ids"])
        self.assertEqual(self.data[validator.ROADMAP]["items"][3:], model["imported_topics_without_resolution_ids"])
        del self.data[validator.ROADMAP]["items"][0]["modules"]
        self.invalid("missing required fields: modules")

    def test_roadmap_metadata_mapping_order_and_phases(self) -> None:
        for key, value in (("baseline", "wrong"), ("ordering", ""), ("phases", {}),
                           ("phases", {"invalid": "Phase"}), ("items", {})):
            with self.subTest(key=key, value=value):
                self.reset()
                self.data[validator.ROADMAP][key] = value
                self.invalid()
        for index, key, value in ((1, "order", 1), (0, "order", True), (0, "phase", 99),
                                  (0, "key", "audit:FIX-999"), (1, "key", "audit:FIX-001"),
                                  (0, "issue_url", "https://github.com/other/repo/issues/1001"),
                                  (0, "finding", "FIX-999"), (1, "finding", "FIX-001"),
                                  (0, "effort", "triage-first"), (3, "dependencies", ["FIX-999"])):
            with self.subTest(index=index, key=key, value=value):
                self.reset()
                self.data[validator.ROADMAP]["items"][index][key] = value
                self.invalid()

    def test_roadmap_coverage_and_missing_finding_tag(self) -> None:
        self.data[validator.ROADMAP]["items"].pop(0)
        self.invalid("coverage differ")
        self.reset()
        del self.data[validator.ROADMAP]["items"][0]["finding"]
        self.invalid("missing roadmap finding ID")

    def test_dependency_must_precede_dependent_in_original_order(self) -> None:
        items = self.data[validator.ROADMAP]["items"]
        items[0]["order"], items[1]["order"] = items[1]["order"], items[0]["order"]
        self.invalid("follows its dependent")

    def test_input_file_order_cannot_replace_original_roadmap_order(self) -> None:
        self.data[LEDGER].reverse()
        self.data[FINDINGS].reverse()
        self.data[validator.ISSUE_MAP]["items"].reverse()
        self.data[validator.ROADMAP]["items"].reverse()
        self.save()
        self.assertEqual(["FIX-001", "FIX-002", "FIX-003"], [item["id"] for item in self.snapshot()["items"]])

    def test_rendering_is_deterministic_and_documentation_is_not_evidence(self) -> None:
        first = self.snapshot()
        second = self.snapshot()
        self.assertEqual(validator.rendered_outputs(first), validator.rendered_outputs(second))
        md = validator.render_markdown(first).decode()
        self.assertIn("not a new test result or issue-closure decision", md)
        self.assertIn("not test executions", md)
        self.assertIn("not auto-dispositioned", md)
        self.assertIn("Literal \\| &lt;tag&gt; \\[brackets\\] \\`code\\` &amp; Unicode λ<br>Second line.", md)
        self.assertIn("(resolutions/fixture.json)", md)
        self.assertIn("(../audit/findings/fixture.json)", md)

    def test_documentation_links_do_not_traverse_out_of_the_docs_root(self) -> None:
        paths = {
            "docs/migration/issue-map.json": "../migration/issue-map.json",
            "docs/roadmap/backlog.json": "../roadmap/backlog.json",
            "docs/audit/findings/fixture.json": "../audit/findings/fixture.json",
            "docs/index.md": "../index.md",
        }
        for path, relative in paths.items():
            with self.subTest(path=path):
                self.assertEqual(f"[{path}]({relative})", validator.doc_link(path))

    def test_repository_links_keep_the_repository_root_relative_path(self) -> None:
        for path in ("AGENTS.md", "scripts/development/validate_resolutions.py", "calf-io/src/File.kt"):
            with self.subTest(path=path):
                self.assertTrue(validator.doc_link(path).endswith(f"(../../{path})"))

    def test_sibling_documentation_links_still_encode_special_characters(self) -> None:
        link = validator.doc_link("docs/architecture/diagram ) [odd] #?.md")
        self.assertTrue(link.endswith("(../architecture/diagram%20%29%20%5Bodd%5D%20%23%3F.md)"))

    def test_markdown_links_encode_special_filename_characters(self) -> None:
        name = "owner ) [odd] #?.json"
        (self.root / LEDGER).rename(self.root / validator.LEDGER_DIR / name)
        md = validator.render_markdown(self.snapshot()).decode()
        self.assertIn("(resolutions/owner%20%29%20%5Bodd%5D%20%23%3F.json)", md)

    def test_generated_outputs_roundtrip_and_detect_edits_or_deletion(self) -> None:
        model = self.snapshot()
        self.assertEqual([validator.OUTPUT_JSON, validator.OUTPUT_MD], validator.check_outputs(self.root, model))
        validator.write_outputs(self.root, model)
        self.assertEqual([], validator.check_outputs(self.root, model))
        self.assertEqual(model, json.loads((self.root / validator.OUTPUT_JSON).read_bytes()))
        for relative in (validator.OUTPUT_JSON, validator.OUTPUT_MD):
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                self.assertEqual([relative], validator.check_outputs(self.root, model))
                path.unlink()
                self.assertEqual([relative], validator.check_outputs(self.root, model))
                path.write_bytes(original)

    def test_ledger_edit_whitespace_and_new_input_set_make_snapshot_stale(self) -> None:
        original = self.snapshot()
        validator.write_outputs(self.root, original)
        for relative in (LEDGER, FINDINGS, validator.ISSUE_MAP, validator.ROADMAP):
            with self.subTest(whitespace_change=relative):
                path = self.root / relative
                raw = path.read_bytes()
                path.write_bytes(raw + b"\n")
                changed = self.snapshot()
                self.assertNotEqual(original["input_fingerprint"], changed["input_fingerprint"])
                self.assertEqual(2, len(validator.check_outputs(self.root, changed)))
                path.write_bytes(raw)
        self.data[LEDGER][0]["remaining"].append("A new runtime gate.")
        self.save()
        self.assertEqual(2, len(validator.check_outputs(self.root, self.snapshot())))
        self.reset()
        self.save()
        new_input = self.root / validator.LEDGER_DIR / "additional-empty-ledger.json"
        new_input.write_text("[]\n")
        self.assertEqual(2, len(validator.check_outputs(self.root, self.snapshot())))
        new_input.unlink()
        self.assertEqual([], validator.check_outputs(self.root, self.snapshot()))

    def test_removing_or_renaming_input_files_is_detected(self) -> None:
        empty = self.root / validator.LEDGER_DIR / "empty.json"
        empty.write_text("[]\n")
        validator.write_outputs(self.root, self.snapshot())
        empty.unlink()
        self.assertEqual(2, len(validator.check_outputs(self.root, self.snapshot())))
        (self.root / LEDGER).rename(self.root / validator.LEDGER_DIR / "renamed.json")
        self.assertEqual(2, len(validator.check_outputs(self.root, self.snapshot())))

    def test_generator_hash_changes_make_existing_outputs_stale(self) -> None:
        original = self.snapshot()
        validator.write_outputs(self.root, original)
        actual_read_bytes = Path.read_bytes

        def with_generator_change(path: Path) -> bytes:
            raw = actual_read_bytes(path)
            return raw + b"\n# simulated generator update\n" if path == Path(validator.__file__) else raw

        with mock.patch.object(Path, "read_bytes", with_generator_change):
            with self.assertRaisesRegex(validator.StaleSnapshotError, "generator changed"):
                validator.check_outputs(self.root, original)
            changed = self.snapshot()
            self.assertNotEqual(original["generator"]["sha256"], changed["generator"]["sha256"])
            self.assertEqual(2, len(validator.check_outputs(self.root, changed)))

    def test_race_is_reported_before_check_or_write_without_replacing_outputs(self) -> None:
        original = self.snapshot()
        validator.write_outputs(self.root, original)
        before = {relative: (self.root / relative).read_bytes() for relative in (validator.OUTPUT_MD, validator.OUTPUT_JSON)}
        self.data[LEDGER][0]["remaining"].append("New gate during generation.")
        self.save()
        for operation in (validator.check_outputs, validator.write_outputs):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(validator.StaleSnapshotError):
                    operation(self.root, original)
                for relative, expected in before.items():
                    self.assertEqual(expected, (self.root / relative).read_bytes())

    def test_validate_and_check_are_read_only_even_for_edited_outputs(self) -> None:
        model = self.snapshot()
        self.assertFalse((self.root / validator.OUTPUT_JSON).exists())
        self.assertFalse((self.root / validator.OUTPUT_MD).exists())
        validator.write_outputs(self.root, model)
        changed = self.root / validator.OUTPUT_MD
        changed.write_text("Manual edit must not be overwritten by --check.\n")
        validator.check_outputs(self.root, self.snapshot())
        self.assertEqual("Manual edit must not be overwritten by --check.\n", changed.read_text())

    def test_external_input_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-outside-fixture-") as outside:
            external = Path(outside) / "ledger.json"
            external.write_bytes((self.root / LEDGER).read_bytes())
            (self.root / LEDGER).unlink()
            (self.root / LEDGER).symlink_to(external)
            with self.assertRaisesRegex(validator.ValidationError, "escapes repository root"):
                self.snapshot()

    def test_external_directory_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-outside-fixture-") as outside:
            (self.root / LEDGER).unlink()
            (self.root / validator.LEDGER_DIR).rmdir()
            (self.root / validator.LEDGER_DIR).symlink_to(Path(outside), target_is_directory=True)
            with self.assertRaisesRegex(validator.ValidationError, "escapes repository root"):
                self.snapshot()

    def test_output_symlink_or_directory_is_rejected_before_any_replacement(self) -> None:
        model = self.snapshot()
        for target in (self.root / LEDGER, self.root.parent / "outside-output.json"):
            with self.subTest(target=target):
                link = self.root / validator.OUTPUT_MD
                link.symlink_to(target)
                with self.assertRaises(validator.ValidationError):
                    validator.write_outputs(self.root, model)
                with self.assertRaises(validator.ValidationError):
                    validator.check_outputs(self.root, model)
                self.assertFalse((self.root / validator.OUTPUT_JSON).exists())
                link.unlink()
        (self.root / validator.OUTPUT_MD).mkdir()
        with self.assertRaisesRegex(validator.ValidationError, "expected a file output"):
            validator.write_outputs(self.root, model)
        self.assertFalse((self.root / validator.OUTPUT_JSON).exists())

    def test_input_symlink_loop_is_a_validation_error_not_a_traceback(self) -> None:
        path = self.root / LEDGER
        path.unlink()
        path.symlink_to(path.name)
        with self.assertRaisesRegex(validator.ValidationError, "cannot resolve"):
            self.snapshot()


class CommandLineFixtures(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-resolution-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative, data in fixtures(164).items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(validator.canonical(data))

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, str(Path(validator.__file__).resolve()), "--root", str(self.root), *args],
                              capture_output=True, text=True, timeout=30, env=environment, check=False)

    def test_cli_default_write_current_stale_and_invalid_are_distinct(self) -> None:
        result = self.cli()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("164/164", result.stdout)
        self.assertFalse((self.root / validator.OUTPUT_JSON).exists())
        missing = self.cli("--check")
        self.assertEqual(2, missing.returncode, missing.stderr)
        self.assertFalse((self.root / validator.OUTPUT_JSON).exists())
        written = self.cli("--write")
        self.assertEqual(0, written.returncode, written.stderr)
        current = self.cli("--check")
        self.assertEqual(0, current.returncode, current.stderr)
        self.assertIn("CURRENT", current.stdout)
        before = {relative: (self.root / relative).read_bytes() for relative in (validator.OUTPUT_MD, validator.OUTPUT_JSON)}
        path = self.root / LEDGER
        path.write_bytes(path.read_bytes() + b"\n")
        stale = self.cli("--check")
        self.assertEqual(2, stale.returncode, stale.stderr)
        self.assertIn("STALE:", stale.stderr)
        path.write_text("invalid json\n")
        invalid = self.cli("--check")
        self.assertEqual(1, invalid.returncode, invalid.stderr)
        self.assertIn("STALE / INVALID INPUT", invalid.stderr)
        failed_write = self.cli("--write")
        self.assertEqual(1, failed_write.returncode, failed_write.stderr)
        for relative, expected in before.items():
            self.assertEqual(expected, (self.root / relative).read_bytes())

    def test_cli_cannot_reduce_the_164_finding_requirement(self) -> None:
        (self.root / FINDINGS).write_bytes(validator.canonical(fixtures()[FINDINGS]))
        result = self.cli()
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("expected exactly 164", result.stderr)
        self.assertFalse((self.root / validator.OUTPUT_JSON).exists())

    def test_cli_rejects_mutually_exclusive_modes(self) -> None:
        result = self.cli("--write", "--check")
        self.assertEqual(2, result.returncode)
        self.assertFalse((self.root / validator.OUTPUT_JSON).exists())

    def test_main_reports_inflight_race_as_stale(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(validator, "build_snapshot", side_effect=validator.StaleSnapshotError("fixture race")):
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(2, validator.main(["--root", str(self.root), "--check"]))
        self.assertIn("STALE: fixture race", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
