"""Important controls for the added failure-only Android snapshot.

These are source/derivative checks, not Android executions or a functional UI
substitute. The previously accepted Local2 population is not imported/replayed.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import android_io_named_gate_details as detail
import android_io_named_system_documents as source
import android_io_named_system_documents_gate_observations as gate

ORIGINAL_OBSERVER_SHA256 = "3f7288affcc1e52b8262a7c3c07fabeb2941c40fff36aa1c456ffd34419ece6e"
ORIGINAL_NATIVE_SHA256 = "1e71a260b1bf501f3f5b7a6121f7cf7dfcc2e6d274cd2733f2f516f8aea5b19f"
STAGED = Path(__file__).resolve().parents[2]


def historical_literals():
    """Read retained author literals as data; do not execute historical tests."""
    values = {}
    for node in ast.parse(Path(gate.__file__).read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {
                    "GATE_FAILURE_ADDITIONS", "GATE_OBSERVATION_POSTIMAGE_DELTAS"
                } and target.id not in values:
                    values[target.id] = ast.literal_eval(node.value)
    return values["GATE_FAILURE_ADDITIONS"], values["GATE_OBSERVATION_POSTIMAGE_DELTAS"]


class NamedSystemIoGateDetailImportantControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-gate-detail-important-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in source.SOURCE_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(STAGED / relative, target)
        self.path = self.root / source.UI
        self.current = self.path.read_text()

    def assert_refused_mutations(self, mutations, message=gate.OBSERVATION_REFUSAL):
        for before, after in mutations:
            with self.subTest(before=before):
                self.assertEqual(1, self.current.count(before), "Mutation must address one exact current fragment")
                self.path.write_text(self.current.replace(before, after, 1))
                with self.assertRaisesRegex(ValueError, "^" + re.escape(message) + "$"):
                    source.source_contract(self.root)
        self.path.write_text(self.current)

    def test_exact_derivative_inverse_retains_authored_observer_and_original_native_bytes(self):
        before = detail.detail_preimage(self.current)
        self.assertEqual(ORIGINAL_OBSERVER_SHA256, hashlib.sha256(before.encode()).hexdigest())
        self.assertEqual(ORIGINAL_NATIVE_SHA256,
                         hashlib.sha256(gate.gate_observation_preimage(self.current).encode()).hexdigest())
        self.assertEqual((gate.GATE_FAILURE_ADDITIONS, gate.GATE_OBSERVATION_POSTIMAGE_DELTAS),
                         detail.detail_images(*historical_literals()))
        receipt = source.source_contract(self.root)
        source.validate_source_receipt(receipt)
        self.assertFalse(receipt["native_success_inferred"])
        self.assertFalse(receipt["cloud_provider_coverage"])

    def test_partial_duplicate_and_edited_detail_never_reach_source_admission(self):
        self.assert_refused_mutations([
            (detail.KOTLIN_DETAIL, ""),
            (detail.KOTLIN_DETAIL, detail.KOTLIN_DETAIL * 2),
            (detail.RETURN_AFTER, detail.RETURN_BEFORE),
            ('detailObservation=AFTER_TIMEOUT_SEPARATE_SNAPSHOT', 'detailObservation=NATIVE_PASSED'),
            ('facts.status = "COMPLETE"\n            } finally { root.recycle() }',
             'facts.status = "COMPLETE"\n            } finally { }'),
        ])

    def test_derivative_factory_and_inverse_refuse_wrong_types_and_ambiguous_anchors(self):
        additions, deltas = historical_literals()
        bad_images = [
            (list(additions), deltas), (additions, list(deltas)),
            (additions[:-1], deltas), (additions, deltas[:-1]),
            (additions[:-1] + (None,), deltas),
            (additions, deltas[:-1] + ((detail.CLOSE_ANCHOR,),)),
            (additions, deltas[:-1] + ((detail.CLOSE_ANCHOR, "changed"),)),
            (additions[:-1] + (additions[-1] + detail.RETURN_BEFORE,), deltas),
        ]
        for values in bad_images:
            with self.subTest(shape=repr(values)[:80]):
                with self.assertRaisesRegex(ValueError, "^" + re.escape(detail.REFUSAL) + "$"):
                    detail.detail_images(*values)
        for value in (None, b"wrong", self.current + detail.KOTLIN_DETAIL,
                      self.current + "\n    private fun gateDetailUnbound() {}\n"):
            with self.subTest(type=type(value).__name__):
                with self.assertRaisesRegex(ValueError, "^" + re.escape(detail.REFUSAL) + "$"):
                    detail.detail_preimage(value)

    def test_separate_cooperative_snapshot_retains_twenty_second_action_deadline(self):
        original = detail.detail_preimage(self.current)
        self.assertEqual(1, original.count("val deadline = SystemClock.elapsedRealtime() + 20_000"))
        self.assertEqual(1, original.count("val deadline = SystemClock.elapsedRealtime() + 1_000"))
        self.assertEqual(2, self.current.count("val deadline = SystemClock.elapsedRealtime() + 1_000"))
        self.assertEqual(1, self.current.count(detail.RETURN_AFTER))
        self.assertIn('detailProbeBudgetMillis=1000', detail.KOTLIN_DETAIL)
        self.assertNotIn("withTimeout", detail.KOTLIN_DETAIL)  # No claimed hard native deadline.
        self.assertIn("try { action() } finally { unavailableGate = previous }", original)

    def test_casing_is_observation_only_and_original_button_admission_remains_strict(self):
        original = detail.detail_preimage(self.current)
        predicate = "it.text?.toString() == pickLabel && it.isEnabled && it.isClickable"
        self.assertIn(predicate, original)
        self.assertNotIn("uppercase(", original)
        self.assertIn("target.expectedText.uppercase(java.util.Locale.ROOT)", detail.KOTLIN_DETAIL)
        self.assertIn("if (text == uppercase && text != target.expectedText)", detail.KOTLIN_DETAIL)
        self.assertIn("if (enabled) facts.enabledButtonIds", detail.KOTLIN_DETAIL)
        self.assertIn("if (clickable) facts.clickableButtonIds", detail.KOTLIN_DETAIL)
        self.assertNotIn("if (enabled && clickable)", detail.KOTLIN_DETAIL)
        current_predicate = ("(it.text?.toString() == pickLabel || it.text?.toString() == renderedPickLabel) &&\n"
                             "                it.isEnabled && it.isClickable")
        self.assert_refused_mutations([
            (current_predicate, "it.text?.toString()?.uppercase(java.util.Locale.ROOT) == pickLabel.uppercase(java.util.Locale.ROOT)"),
        ], "System UI ownership, exact controls, ambiguity refusal or flag restoration changed")

    def test_refreshed_package_and_exact_container_identity_are_not_query_assumptions(self):
        self.assert_refused_mutations([
            ('scope.viewIdResourceName == resource("dir_list")', 'true'),
            ('toolbar.viewIdResourceName == resource("toolbar")', 'true'),
            ('facts.rootPackageExact = root.packageName?.toString() == packageName',
             'facts.rootPackageExact = true'),
            ('node.viewIdResourceName != "android:id/button1") continue', 'false) continue'),
        ])
        for name in ("scope", "toolbar"):
            start = detail.KOTLIN_DETAIL.index(f"filter {{ {name} ->")
            block = detail.KOTLIN_DETAIL[start:detail.KOTLIN_DETAIL.index("\n                            }", start)]
            self.assertEqual(2, block.count("gateProbeTime(deadline)"))
            self.assertIn(f"{name}.refresh() && {name}.isVisibleToUser", block)

    def test_every_query_and_text_is_bounded_and_owned_nodes_have_finally_cleanup(self):
        code = detail.KOTLIN_DETAIL
        for token in ("raw.size > 64", "scopes.size > 64", "toolbars.size > 64",
                      "nativeText.length > 1024", "title.length > 1024", "minOf(scope.childCount, 65)"):
            self.assertIn(token, code)
        for owner in ("raw", "global", "scopes", "toolbars", "labels"):
            self.assertEqual(1, code.count(f"finally {{ {owner}.forEach {{ it.recycle() }} }}"))
        self.assertEqual(1, code.count("finally { root.recycle() }"))
        helper = code[code.index("private fun gateDetailExactTextCount"):]
        self.assertNotIn("recycle()", helper)  # Caller owns each list, avoiding double recycling.
        self.assertIn('throw GateProbeStop("QUERY_BOUND")', helper)
        self.assertIn('throw GateProbeStop("TEXT_BOUND")', helper)

    def test_downloads_title_is_exact_installed_root_downloads_not_root_title_or_navigation(self):
        code = detail.KOTLIN_DETAIL
        self.assertIn('val providerPackage = "com.android.providers.downloads"', code)
        self.assertIn('resources.getIdentifier("root_downloads", "string", providerPackage)', code)
        self.assertIn('resources.getResourceName(titleId) != "$providerPackage:string/root_downloads"', code)
        self.assertNotIn('"root_title"', code)
        self.assertIn("gateDetailExactTextCount(global, target.expectedText, deadline)", code)
        self.assertIn("gateDetailExactTextCount(labels, title, deadline)", code)
        self.assert_refused_mutations([
            ('resources.getIdentifier("root_downloads", "string", providerPackage)',
             'resources.getIdentifier("root_title", "string", providerPackage)'),
            ('val providerPackage = "com.android.providers.downloads"', 'val providerPackage = packageName'),
            ('resources.getResourceName(titleId) != "$providerPackage:string/root_downloads"', 'false'),
        ])

    def test_partial_unknown_fields_are_nullable_and_output_contains_only_fixed_scalars(self):
        code = detail.KOTLIN_DETAIL
        fields = set(re.findall(r"var (\w+): (?:Boolean|Int)\? = null", code))
        self.assertGreaterEqual(len(fields), 16)
        render = code[code.index("fun render():"):code.index("\n    private fun gateDetailObservation")]
        interpolated = set(re.findall(r"\$(\w+)", render))
        self.assertEqual(fields | {"role", "status"}, interpolated)
        self.assertEqual(1, code.count('facts.status = "COMPLETE"'))
        self.assertIn("facts.status = stop.category", code)
        self.assertIn('facts.status = "UNAVAILABLE"', code)
        self.assertIn("gateProbeTime(deadline)\n            if (matches) exact++", code)

    def test_snapshot_cannot_click_grant_read_provider_payload_or_replace_original_failure(self):
        code = detail.KOTLIN_DETAIL
        for forbidden in ("performAction(", ".parent", "getChild(", "contentResolver", "grantUriPermission(",
                          "takePersistableUriPermission(", "executeShellCommand(", "Log.", "println("):
            self.assertNotIn(forbidden, code)
        original = detail.detail_preimage(self.current)
        self.assertIn('";documentsUiGateFailureSchema=1,observation=AFTER_TIMEOUT_ONLY,role=${target.role},status=UNAVAILABLE"',
                      original)

    def test_fixture_overlay_preserves_original_mutation_and_cannot_admit_duplicate_or_native_weakening(self):
        original = detail.detail_preimage(self.current)
        self.assertEqual(self.current, detail.detail_fixture_postimage(original))
        deadline = "val deadline = SystemClock.elapsedRealtime() + 20_000"
        self.assertEqual(1, original.count(deadline))
        mutated = original.replace(deadline, deadline.replace("20_000", "30_000"), 1)
        current = detail.detail_fixture_postimage(mutated)
        self.assertEqual(mutated, detail.detail_preimage(current))
        self.path.write_text(current)
        with self.assertRaisesRegex(ValueError, "^" + re.escape(gate.NATIVE_REFUSAL) + "$"):
            source.source_contract(self.root)
        for value in (None, self.current, original + detail.CLOSE_ANCHOR,
                      original.replace(detail.RETURN_BEFORE, "", 1)):
            with self.subTest(type=type(value).__name__):
                with self.assertRaisesRegex(ValueError, "^" + re.escape(detail.REFUSAL) + "$"):
                    detail.detail_fixture_postimage(value)


if __name__ == "__main__":
    unittest.main()
