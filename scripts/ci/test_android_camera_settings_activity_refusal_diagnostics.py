"""New inert Settings absence-refusal diagnostics controls; no native/SDK/process operations."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("camera_settings_absence_diagnostics_under_test",
                                              Path(__file__).with_name("android_camera_developer_prerequisite.py"))
helper = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = helper
SPEC.loader.exec_module(helper)
ATTRIBUTE = "_nativecmpkit_settings_activity_absence_refusal"


# Only this four-fragment observational addition may be reversed. Entire current
# and historical helper bytes are checked; no arbitrary AST definitions are stripped.
OBSERVATION_INVERSE_SHA256 = 'e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953'

def historical_helper_source(source: str) -> str:
    contract_path = Path(__file__).parent / "fixtures/android-camera-settings-absence-observation-inverse.json"
    payload = contract_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != OBSERVATION_INVERSE_SHA256:
        raise AssertionError("Exact owning observation-inverse fixture is changed")
    contract = json.loads(payload)
    if type(source) is not str or hashlib.sha256(source.encode()).hexdigest() != contract["after_sha256"]:
        raise AssertionError("Full current helper bytes differ from the qualified afterimage")
    restored = source
    for fragment in contract["inverse_fragments"]:
        if restored.count(fragment["new"]) != 1:
            raise AssertionError("The exact owning observation inverse is missing or ambiguous")
        restored = restored.replace(fragment["new"], fragment["old"], 1)
    if hashlib.sha256(restored.encode()).hexdigest() != contract["before_sha256"]:
        raise AssertionError("Full historical helper bytes were not exactly restored")
    return restored


class SettingsActivityObservationInverseTest(unittest.TestCase):
    def test_exact_four_fragment_inverse_retains_entire_historical_source_and_refuses_mutations(self):
        source = Path(__file__).with_name("android_camera_developer_prerequisite.py").read_text()
        restored = historical_helper_source(source)
        self.assertNotEqual(restored, source)
        self.assertNotIn("def record_settings_activity_absence_refusal(", restored)
        self.assertNotIn("def settings_activity_absence_refusal(", restored)
        self.assertIn('require(display is not None, "Settings Activity absence traversal is unproved")', restored)
        for mutation in (source + "\nrequire(True, 'unexpected')\n", source.replace("raise ValueError(message)", "return", 1),
                         source.replace("for row_index, row in enumerate(rows[1:-1], 1):", "for row in rows[1:-1]:", 1)):
            self.assertNotEqual(mutation, source)
            with self.assertRaises(AssertionError):
                historical_helper_source(mutation)


class SettingsActivityRefusalDiagnosticsTest(unittest.TestCase):
    def refusal(self, row):
        payload = (helper.ACTIVITIES_HEADER + "\nDisplay #0 (activities from top to bottom):\n" + row + "\n  (nothing)\n").encode()
        try:
            helper.parse_settings_activity_absence(subprocess.CompletedProcess(["synthetic-only"], 0, payload, b""))
        except ValueError as error:
            self.assertEqual(str(error), "Settings Activity absence traversal is unproved")
            return error, payload
        self.fail("The unchanged display-row require must refuse")

    def observation(self, error):
        return helper.settings_activity_absence_refusal(error, helper.require_call_origin(error))

    def publisher(self):
        owner = object.__new__(helper.OwnedDeveloperPrerequisite)
        owner.receipt = {"errors": []}
        publications = []
        owner.publish = lambda: publications.append(copy.deepcopy(owner.receipt))
        return owner, publications

    def test_blank_row_refuses_with_only_bounded_hash_shape_counts(self):
        error, payload = self.refusal("")
        facts = self.observation(error)
        self.assertIsNotNone(facts)
        self.assertEqual((facts["row_count"], facts["interior_row_count"], facts["rejected_row_index"]), (4, 2, 2))
        self.assertEqual((facts["payload_bytes"], facts["row_bytes"]), (len(payload), 0))
        self.assertEqual(facts["payload_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(facts["row_sha256"], hashlib.sha256(b"").hexdigest())
        self.assertTrue(facts["row_empty"] and facts["row_ascii_whitespace_only"])
        self.assertEqual((facts["interior_display_shape_rows"], facts["interior_ascii_blank_shape_rows"],
                          facts["interior_other_shape_rows"], facts["interior_activity_record_marker_rows"]), (1, 1, 0, 0))

    def test_space_tab_row_is_observed_but_never_accepted(self):
        error, _ = self.refusal(" \t ")
        facts = self.observation(error)
        self.assertTrue(facts["row_ascii_whitespace_only"] and facts["row_contains_tab"])
        self.assertEqual((facts["row_leading_ascii_spaces"], facts["row_trailing_ascii_spaces"]), (1, 1))

    def test_nested_activity_row_marker_does_not_export_its_text(self):
        error, _ = self.refusal("    * Hist #7: ActivityRecord{synthetic-private-marker u0 com.android.settings/.Synthetic t7}")
        facts = self.observation(error)
        self.assertTrue(facts["row_activity_record_marker"])
        self.assertEqual((facts["interior_other_shape_rows"], facts["interior_activity_record_marker_rows"]), (1, 1))
        owner, publications = self.publisher()
        owner.failure("prepare", error)
        self.assertEqual(len(publications), 1)
        output = json.dumps(publications)
        for secret in ("synthetic-private-marker", "Hist #7", "com.android.settings/.Synthetic", "t7"):
            self.assertNotIn(secret, output)

    def test_indented_display_shape_refuses_without_normalization(self):
        error, _ = self.refusal("  Display #1 (activities from top to bottom):")
        facts = self.observation(error)
        self.assertTrue(facts["row_indented_display_prefix"])
        self.assertFalse(facts["row_display_prefix"])
        self.assertEqual(facts["row_leading_ascii_spaces"], 2)

    def test_noncanonical_display_shape_refuses_without_relaxation(self):
        error, _ = self.refusal("Display #01 (activities from top to bottom):")
        self.assertTrue(self.observation(error)["row_display_prefix"])

    def test_nonascii_unknown_row_has_bounded_utf8_digest_only(self):
        error, _ = self.refusal("synthetic-\u03b1")
        facts = self.observation(error)
        self.assertFalse(facts["row_ascii_only"])
        self.assertEqual(facts["row_bytes"], len("synthetic-\u03b1".encode()))
        self.assertNotIn("synthetic-\u03b1", json.dumps(facts))

    def test_complete_empty_display_traversal_keeps_unchanged_success(self):
        payload = (helper.ACTIVITIES_HEADER + "\nDisplay #0 (activities from top to bottom):\n  (nothing)\n").encode()
        self.assertIsNone(helper.parse_settings_activity_absence(subprocess.CompletedProcess([], 0, payload, b"")))

    def test_earlier_transport_bytes_and_header_refusals_do_not_attach_row_facts(self):
        for payload in (b"unsafe\0", b"\xff", b"unknown\n  (nothing)\n"):
            with self.subTest(payload_bytes=len(payload)):
                try:
                    helper.parse_settings_activity_absence(subprocess.CompletedProcess([], 0, payload, b""))
                except ValueError as error:
                    self.assertIsNone(self.observation(error))
                except UnicodeDecodeError as error:
                    self.assertIsNone(self.observation(error))
                else:
                    self.fail("Earlier unchanged guard must refuse")

    def test_duplicate_and_out_of_range_display_guards_are_not_row_diagnostics(self):
        for displays in (("0", "0"), ("2147483648",)):
            payload = (helper.ACTIVITIES_HEADER + "\n" + "\n".join("Display #" + n + " (activities from top to bottom):" for n in displays) + "\n  (nothing)\n").encode()
            with self.subTest(displays=displays):
                try:
                    helper.parse_settings_activity_absence(subprocess.CompletedProcess([], 0, payload, b""))
                except ValueError as error:
                    self.assertEqual(str(error), "Unknown or duplicate Settings Activity display traversal")
                    self.assertIsNone(self.observation(error))
                else:
                    self.fail("Original integer/uniqueness guard must refuse")

    def test_capture_observation_error_cannot_replace_original_valueerror(self):
        for secondary in (RuntimeError, KeyboardInterrupt, SystemExit):
            with self.subTest(secondary=secondary.__name__), patch.object(helper, "record_settings_activity_absence_refusal", side_effect=secondary):
                error, _ = self.refusal("synthetic-unknown")
                self.assertIs(type(error), ValueError)
                self.assertIsNone(self.observation(error))
                self.assertEqual(helper.require_call_origin(error)["symbol"], "parse_settings_activity_absence")

    def test_publication_observation_error_keeps_primary_entry_and_one_publish(self):
        error, _ = self.refusal("synthetic-unknown")
        owner, publications = self.publisher()
        with patch.object(helper, "settings_activity_absence_refusal", side_effect=KeyboardInterrupt):
            owner.failure("prepare", error)
        self.assertEqual(len(publications), 1)
        entry = publications[0]["errors"][0]
        self.assertEqual((entry["phase"], entry["class"]), ("prepare", "ValueError"))
        self.assertEqual(entry["require_call_origin"]["symbol"], "parse_settings_activity_absence")
        self.assertNotIn("settings_activity_absence_refusal", entry)

    def test_unknown_keys_types_and_unbounded_shapes_are_never_exported(self):
        error, _ = self.refusal("synthetic-unknown")
        original = copy.deepcopy(vars(error)[ATTRIBUTE])
        variants = [dict(original, raw_row="synthetic-private-marker"), dict(original, payload_bytes=True),
                    dict(original, row_empty=1), dict(original, payload_bytes=helper.CONTROL_BYTES + 1),
                    dict(original, row_count=2), dict(original, row_count=helper.CONTROL_BYTES + 2),
                    dict(original, rejected_row_index=0), dict(original, row_bytes=helper.CONTROL_BYTES + 1),
                    dict(original, row_sha256="unsafe/path"), dict(original, row_leading_ascii_spaces=-1),
                    dict(original, interior_display_shape_rows=999), dict(original, interior_other_shape_rows=-1),
                    dict(original, interior_activity_record_marker_rows=999)]
        for facts in variants:
            setattr(error, ATTRIBUTE, facts)
            self.assertIsNone(self.observation(error))
        setattr(error, ATTRIBUTE, original)
        self.assertIsNotNone(self.observation(error))

    def test_unavailable_foreign_origin_and_valueerror_subclass_are_never_exported(self):
        error, _ = self.refusal("synthetic-unknown")
        valid_origin = helper.require_call_origin(error)
        for origin in (None, {}, dict(valid_origin, source="foreign.py"), dict(valid_origin, symbol="close"),
                       dict(valid_origin, line=True), dict(valid_origin, line=20000)):
            self.assertIsNone(helper.settings_activity_absence_refusal(error, origin))
        class Foreign(ValueError):
            pass
        foreign = Foreign("synthetic-private-marker")
        setattr(foreign, ATTRIBUTE, copy.deepcopy(vars(error)[ATTRIBUTE]))
        self.assertIsNone(helper.settings_activity_absence_refusal(foreign, valid_origin))

    def test_missing_diagnostic_does_not_suppress_original_refusal_publication(self):
        error, _ = self.refusal("synthetic-unknown")
        delattr(error, ATTRIBUTE)
        owner, publications = self.publisher()
        owner.failure("prepare", error)
        self.assertEqual(len(publications), 1)
        self.assertEqual(publications[0]["errors"][0]["class"], "ValueError")
        self.assertNotIn("settings_activity_absence_refusal", publications[0]["errors"][0])

    def test_capture_helper_is_bounded_and_ignores_nonowned_shapes(self):
        error = ValueError("synthetic-private-marker")
        for payload, rows, index in ((b"x", ["x"], 0), (b"x" * (helper.CONTROL_BYTES + 1), ["x", "x", "x"], 1),
                                    (b"abc", ["a", "b", "c"], True), (b"abc", ["a", 7, "c"], 1)):
            helper.record_settings_activity_absence_refusal(error, payload, rows, index)
            self.assertNotIn(ATTRIBUTE, vars(error))


if __name__ == "__main__":
    unittest.main()
