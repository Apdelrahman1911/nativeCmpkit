"""NEW Local2 gate diagnostic controls only; no accepted populations are imported/run.

The synthetic data model is a source-linked specification, not Android execution,
installed DocumentsUI attribution, historical poll operands, or native success.
Run this one class only after the lead stages the exact owning candidate.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

import android_io_named_system_documents as source
import android_io_named_system_documents_gate_observations as gate

BASE_UI_SHA256 = "1e71a260b1bf501f3f5b7a6121f7cf7dfcc2e6d274cd2733f2f516f8aea5b19f"
ROLES = {"OWNED_FOLDER_ROW", "OPEN_TREE_BUTTON"}
COUNT_NAMES = ("visited", "refreshed", "visible", "packageExact", "idExact", "textExact",
               "idAndText", "textAndEnabled", "textEnabledClickable", "originalPredicate")


def _counts(nodes: list[dict], role: str, limit: int | None = None) -> tuple[dict, str]:
    counts = dict.fromkeys(COUNT_NAMES, 0)
    for index, node in enumerate(nodes):
        if limit is not None and index >= limit:
            return counts, "TIME_BOUND"
        if node.get("readFailure"):
            return counts, "UNAVAILABLE"  # Failed nodes never commit a synthetic completed count.
        refreshed = node.get("refreshed", True) is True
        visible = refreshed and node.get("visible", True) is True
        same = visible and node.get("packageExact", True) is True
        exact_id = same and node.get("idExact", True) is True
        exact_text = same and node.get("textExact", True) is True
        enabled = same and node.get("enabled", True) is True
        clickable = same and node.get("clickable", True) is True
        counts["visited"] += 1
        counts["refreshed"] += int(refreshed)
        counts["visible"] += int(visible)
        counts["packageExact"] += int(same)
        counts["idExact"] += int(exact_id)
        counts["textExact"] += int(exact_text)
        counts["idAndText"] += int(exact_id and exact_text)
        counts["textAndEnabled"] += int(exact_text and enabled)
        counts["textEnabledClickable"] += int(exact_text and enabled and clickable)
        original = (exact_id and exact_text) if role == "OWNED_FOLDER_ROW" else (exact_text and enabled and clickable)
        counts["originalPredicate"] += int(original)
    return counts, "COMPLETE"


def probe_model(role: str, root: dict | None, nodes: list[dict] | None = None,
                scopes: list[dict] | None = None, node_limit: int | None = None) -> dict:
    """Finite synthetic specification; no UI calls, strings, paths, grants or actions."""
    if role not in ROLES:
        raise ValueError("Unknown fixed synthetic diagnostic role")
    facts = {"documentsUiGateFailureSchema": 1, "observation": "AFTER_TIMEOUT_ONLY", "role": role,
             "status": "UNAVAILABLE", "rootPresent": root is not None, "rootRefreshed": None,
             "rootVisible": None, "rootPackageExact": None, "rawContainersCapped65": None,
             "rawNodesCapped65": None, "containers": None, "nodes": None}
    if root is None:
        facts["status"] = "ROOT_UNAVAILABLE"
        return facts
    facts["rootRefreshed"] = root.get("refreshed", True) is True
    if not facts["rootRefreshed"]:
        facts["status"] = "ROOT_REFUSED"
        return facts
    facts["rootVisible"] = root.get("visible", True) is True
    if not facts["rootVisible"]:
        facts["status"] = "ROOT_REFUSED"
        return facts
    facts["rootPackageExact"] = root.get("packageExact", True) is True
    if not facts["rootPackageExact"]:
        facts["status"] = "ROOT_REFUSED"
        return facts
    if role == "OWNED_FOLDER_ROW":
        scopes = [{}] if scopes is None else scopes
        facts["rawContainersCapped65"] = min(len(scopes), 65)
        if len(scopes) > 64:
            facts["status"] = "QUERY_BOUND"
            return facts
        counts, status = _counts(scopes, role)
        facts["containers"] = {key: counts[key] for key in ("visited", "refreshed", "visible", "packageExact")}
        if status != "COMPLETE":
            facts["status"] = status
            return facts
        if counts["packageExact"] != 1:
            facts["status"] = "NO_ELIGIBLE_CONTAINER" if counts["packageExact"] == 0 else "AMBIGUOUS_CONTAINER"
            return facts
    nodes = [] if nodes is None else nodes
    facts["rawNodesCapped65"] = min(len(nodes), 65)
    if len(nodes) > 64:
        facts["status"] = "QUERY_BOUND"
        return facts
    facts["nodes"], facts["status"] = _counts(nodes, role, node_limit)
    return facts


class NamedSystemIoGateObservationNewControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-local2-gate-NEW-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        staged = Path(__file__).resolve().parents[2]
        for relative in source.SOURCE_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(staged / relative, target)

    def ui(self):
        return (self.root / source.UI).read_text()

    def replace_once(self, before, after):
        text = self.ui()
        self.assertEqual(1, text.count(before), "Each NEW mutation must address one exact candidate fragment")
        (self.root / source.UI).write_text(text.replace(before, after, 1))

    def refuses(self, message=gate.OBSERVATION_REFUSAL):
        with self.assertRaisesRegex(ValueError, "^" + message + "$"):
            source.source_contract(self.root)

    def test_new_complete_inverse_preserves_original_and_cannot_certify_native(self):
        original = gate.gate_observation_preimage(self.ui())
        self.assertEqual(BASE_UI_SHA256, hashlib.sha256(original.encode()).hexdigest())
        receipt = source.source_contract(self.root)
        source.validate_source_receipt(receipt)
        self.assertFalse(receipt["native_success_inferred"])
        self.assertFalse(receipt["cloud_provider_coverage"])

    def test_new_two_scopes_preserve_native_body_and_clear_target_on_all_exits(self):
        text = self.ui()
        self.assertEqual(1, text.count("withGateFailureObservation(GateFailureRole.OWNED_FOLDER_ROW, folder)"))
        self.assertEqual(1, text.count("withGateFailureObservation(GateFailureRole.OPEN_TREE_BUTTON, pickLabel)"))
        self.assertIn("try { action() } finally { unavailableGate = previous }", text)
        self.assertNotIn("gateFailure", gate.gate_observation_preimage(text))

    def test_new_diagnostic_bridge_is_mandatory_before_original_resource_admission(self):
        owner = Path(source.__file__).read_text()
        self.assertLess(owner.index("observed_ui = gate_observation_preimage(live_ui)"),
                        owner.index("ui = resource_admission_preimage(observed_ui)"))
        (self.root / source.UI).write_text(gate.gate_observation_preimage(self.ui()))
        self.refuses()

    def test_new_missing_field_scope_helper_or_suffix_refuses_partial_shape(self):
        baseline = self.ui()
        cases = (gate.GATE_FAILURE_ADDITIONS[0], gate.GATE_FAILURE_ADDITIONS[1],
                 gate.GATE_FAILURE_ADDITIONS[4], gate.GATE_FAILURE_ADDITIONS[-1],
                 gate.GATE_FAILURE_ERROR_AFTER)
        for addition in cases:
            with self.subTest(fragment=addition[:60]):
                self.assertEqual(1, baseline.count(addition))
                (self.root / source.UI).write_text(baseline.replace(addition, "", 1))
                self.refuses()
        (self.root / source.UI).write_text(baseline)

    def test_new_direct_historical_resource_bridge_retains_original154_hash_without_old_test_replay(self):
        historical = source.resource_admission_preimage(self.ui())
        self.assertEqual("03a0ebc37215c4b86043f253f4e83b7db39c7fd52652d9ea735e6e7c106ea1dc",
                         hashlib.sha256(historical.encode()).hexdigest())
        self.assertEqual(self.ui(), source.resource_admission_postimage(historical))
        canonical = 'check(value != 0 && resources.getResourceName(value) == "$namespace:id/$id")'
        self.assertEqual(1, historical.count(canonical))
        with self.assertRaisesRegex(ValueError, "^Refusal-only DocumentsUI resource observations changed$"):
            source.resource_admission_postimage(historical.replace(canonical, "check(true)", 1))
        # New edge-only text control, never import/execute the historical accepted fixture classes.

    def test_new_direct_resource_bridge_cannot_silently_strip_partial_diagnostic(self):
        complete = self.ui()
        partial = complete.replace(gate.GATE_FAILURE_ADDITIONS[0], "", 1)
        with self.assertRaisesRegex(ValueError, "^" + gate.OBSERVATION_REFUSAL + "$"):
            source.resource_admission_preimage(partial)

    def test_new_text_bridge_is_not_runtime_admission_and_never_overwrites_native_deadline(self):
        preimage = gate.gate_observation_preimage(self.ui())
        self.assertFalse(gate.gate_observation_present(preimage))
        self.assertEqual(self.ui(), gate.gate_observation_postimage(preimage))
        (self.root / source.UI).write_text(preimage)
        self.refuses()
        changed = preimage.replace("val deadline = SystemClock.elapsedRealtime() + 20_000",
                                   "val deadline = SystemClock.elapsedRealtime() + 30_000", 1)
        with self.assertRaisesRegex(ValueError, "^" + gate.NATIVE_REFUSAL + "$"):
            gate.gate_observation_postimage(changed)

    def test_new_bare_resource_shape_preserves_old_resource_refusal_but_never_admits_missing_diagnostic(self):
        current_without_diagnostic = gate.gate_observation_preimage(self.ui())
        historical_without_admission = source.resource_admission_preimage(self.ui())
        (self.root / source.UI).write_text(historical_without_admission)
        self.refuses("Application-specific DocumentsUI resource admission changed")
        (self.root / source.UI).write_text(current_without_diagnostic)
        self.refuses()
        # NEW missing-diagnostic composition edges only; no historical control method is imported/run.

    def test_new_original_twenty_second_native_deadline_cannot_be_changed(self):
        self.replace_once("val deadline = SystemClock.elapsedRealtime() + 20_000",
                          "val deadline = SystemClock.elapsedRealtime() + 30_000")
        self.refuses(gate.NATIVE_REFUSAL)

    def test_new_actual_native_click_return_cannot_be_ignored(self):
        self.replace_once("check(candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK))",
                          "candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK)")
        self.refuses(gate.NATIVE_REFUSAL)

    def test_new_row_and_button_original_predicates_stay_strict(self):
        baseline = self.ui()
        cases = (("it.viewIdResourceName == \"android:id/title\" && it.text?.toString() == folder",
                  "it.text?.toString() == folder"),
                 ("it.text?.toString() == pickLabel && it.isEnabled && it.isClickable",
                  "it.text?.toString() == pickLabel"))
        for before, after in cases:
            with self.subTest(before=before):
                (self.root / source.UI).write_text(baseline)
                self.replace_once(before, after)
                self.refuses(gate.NATIVE_REFUSAL)
        (self.root / source.UI).write_text(baseline)

    def test_new_read_only_probe_cannot_perform_an_action(self):
        self.replace_once("                if (originalPredicate) counts.originalPredicate += 1\n",
                          "                if (originalPredicate) probeNode.performAction(AccessibilityNodeInfo.ACTION_CLICK)\n")
        self.refuses()

    def test_new_probe_node_and_container_bounds_cannot_expand(self):
        baseline = self.ui()
        for before in ("if (scopes.size > 64)", "if (raw.size > 64)"):
            with self.subTest(bound=before):
                (self.root / source.UI).write_text(baseline)
                self.replace_once(before, before.replace("64", "65"))
                self.refuses()
        (self.root / source.UI).write_text(baseline)

    def test_new_probe_budget_and_post_timeout_provenance_are_not_last_poll(self):
        baseline = self.ui()
        cases = (("val deadline = SystemClock.elapsedRealtime() + 1_000", "val deadline = SystemClock.elapsedRealtime() + 8_000"),
                 ("fun render(): String = \"documentsUiGateFailureSchema=1,observation=AFTER_TIMEOUT_ONLY,\"",
                  "fun render(): String = \"documentsUiGateFailureSchema=1,observation=LAST_POLL,\""))
        for before, after in cases:
            with self.subTest(before=before):
                (self.root / source.UI).write_text(baseline)
                self.replace_once(before, after)
                self.refuses()
        (self.root / source.UI).write_text(baseline)

    def test_new_unobserved_counts_cannot_be_coerced_into_observed_zero(self):
        self.replace_once("var rawNodesCapped65: Int? = null", "var rawNodesCapped65: Int? = 0")
        self.refuses()

    def test_new_diagnostic_exception_cannot_disclose_expected_label(self):
        self.replace_once(";documentsUiGateFailureSchema=1,observation=AFTER_TIMEOUT_ONLY,role=${target.role},status=UNAVAILABLE\"",
                          ";documentsUiGateFailureSchema=1,observation=AFTER_TIMEOUT_ONLY,role=${target.role},status=${target.expectedText}\"")
        self.refuses()

    def test_new_synthetic_unobserved_query_is_not_observed_empty(self):
        unavailable = probe_model("OPEN_TREE_BUTTON", None)
        refused = probe_model("OPEN_TREE_BUTTON", {"refreshed": False})
        empty = probe_model("OPEN_TREE_BUTTON", {}, [])
        self.assertIsNone(unavailable["rawNodesCapped65"])
        self.assertIsNone(refused["rawNodesCapped65"])
        self.assertIsNone(refused["rootVisible"])
        self.assertEqual(0, empty["rawNodesCapped65"])
        self.assertEqual(0, empty["nodes"]["originalPredicate"])
        self.assertEqual("COMPLETE", empty["status"])

    def test_new_synthetic_button_counts_keep_text_enabled_clickable_operands_distinct(self):
        nodes = [{"textExact": False}, {"enabled": False}, {"clickable": False}, {"idExact": False}]
        facts = probe_model("OPEN_TREE_BUTTON", {}, nodes)
        counts = facts["nodes"]
        self.assertEqual(4, facts["rawNodesCapped65"])
        self.assertEqual(3, counts["textExact"])
        self.assertEqual(2, counts["textAndEnabled"])
        self.assertEqual(1, counts["textEnabledClickable"])
        self.assertEqual(1, counts["originalPredicate"])
        self.assertEqual(3, counts["idExact"])
        # This preserves the original button predicate; the query supplies ID identity, not a new gate.

    def test_new_synthetic_row_identity_does_not_conflate_parent_action_eligibility(self):
        nodes = [{"enabled": False, "clickable": False}, {"idExact": False}, {"visible": False},
                 {"packageExact": False}, {"refreshed": False}]
        facts = probe_model("OWNED_FOLDER_ROW", {}, nodes)
        self.assertEqual(5, facts["rawNodesCapped65"])
        self.assertEqual(2, facts["nodes"]["packageExact"])
        self.assertEqual(1, facts["nodes"]["idAndText"])
        self.assertEqual(1, facts["nodes"]["originalPredicate"])
        self.assertEqual(1, facts["nodes"]["textEnabledClickable"])
        # The original row may ascend to its exact native parent later; this probe never does so.

    def test_new_synthetic_partial_time_or_exception_is_not_absence_or_historical_failure(self):
        partial = probe_model("OPEN_TREE_BUTTON", {}, [{}, {}], node_limit=1)
        failed = probe_model("OPEN_TREE_BUTTON", {}, [{}, {"readFailure": "private-placeholder"}])
        self.assertEqual("TIME_BOUND", partial["status"])
        self.assertEqual(1, partial["nodes"]["visited"])
        self.assertEqual(2, partial["rawNodesCapped65"])
        self.assertEqual("UNAVAILABLE", failed["status"])
        self.assertEqual(1, failed["nodes"]["visited"])
        self.assertNotIn("private-placeholder", repr(failed))
        self.assertEqual("AFTER_TIMEOUT_ONLY", failed["observation"])
        self.assertNotIn("maxVisibleMatches", failed)

    def test_new_synthetic_ambiguous_missing_or_oversize_scope_never_queries_owned_text(self):
        for scopes, status in (([], "NO_ELIGIBLE_CONTAINER"), ([{}, {}], "AMBIGUOUS_CONTAINER"),
                               ([{}] * 65, "QUERY_BOUND")):
            with self.subTest(status=status):
                facts = probe_model("OWNED_FOLDER_ROW", {}, [{}], scopes=scopes)
                self.assertEqual(status, facts["status"])
                self.assertIsNone(facts["rawNodesCapped65"])
                self.assertIsNone(facts["nodes"])

    def test_new_synthetic_node_query_bound_commits_no_eligible_counts(self):
        facts = probe_model("OPEN_TREE_BUTTON", {}, [{}] * 66)
        self.assertEqual(65, facts["rawNodesCapped65"])
        self.assertIsNone(facts["nodes"])
        self.assertEqual("QUERY_BOUND", facts["status"])


if __name__ == "__main__":
    unittest.main()
