"""NEW tiny SYNTHETIC companion-byte regressions, never real Maven/native proof.

The unchanged predecessor helper is imported for fixture construction only. No
old TestCase is selected. Its fake classes/natives cannot enter the public CLI.
The model adapter can expose the historical no-pin defect without changing the
test bodies; after correction it supplies independently fixed synthetic pins.
"""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import tempfile
import unittest

import private_web_resolution as resolution
import stage_private_web as stage
from test_private_web_adoption import Model, jar


class CompanionModel:
    def __init__(self, directory):
        self.model = Model(directory)
        self.report = self.model.stage()
        self.observations = self.model.observations(self.report)
        self.pins = {}
        # Pins come from known fixture bytes BEFORE observations/tampering, not
        # from an arbitrary success report or refreshed resolver observations.
        for module in stage.COMPANIONS:
            filename = f"javafx-{module}-{stage.UPSTREAM}-linux.jar"
            original = self.model.input_paths.get(filename)
            if original is None:  # Synthetic Swing has its own explicit origin.
                original = directory / "synthetic-official-swing" / filename
                original.parent.mkdir()
                jar(original, {"MODEL.txt": b"SYNTHETIC trusted Swing fixture only"})
            self.pins[filename] = Model.pin(original)
            for row in self.observations["resolved_artifacts"]:
                if row["module"] != "javafx-" + module:
                    continue
                path = directory / "per-classpath" / row["configuration"] / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original.read_bytes())  # Only tiny fake bytes.
                row.update(Model.row(row["configuration"], "org.openjfx", row["module"], stage.UPSTREAM, path))
            filename = f"javafx-{module}-{stage.UPSTREAM}.jar"
            original = directory / "synthetic-official-generic" / filename
            original.parent.mkdir(exist_ok=True)
            jar(original, {"MODEL.txt": b"SYNTHETIC trusted generic fixture " + module.encode()})
            self.pins[filename] = Model.pin(original)
            for configuration in resolution.CLASSPATHS:
                path = directory / "per-classpath" / configuration / filename
                path.write_bytes(original.read_bytes())
                self.observations["resolved_artifacts"].append(Model.row(configuration, "org.openjfx", "javafx-" + module, stage.UPSTREAM, path))

    def verify(self, observations=None, pins=None):
        kwargs = {"model_classes": self.model.contract.classes}
        # Model-only predecessor adapter keeps the RED witness and final test
        # bodies identical. Missing correction support still fails the tamper
        # tests; no production entry point uses this introspection.
        if "model_companion_pins" in inspect.signature(resolution._verify).parameters:
            kwargs["model_companion_pins"] = self.pins if pins is None else pins
        return resolution._verify(self.report, observations or self.observations, self.model.repository, **kwargs)

    def tamper_row(self, row):
        path = Path(row["path"])
        original = path.read_bytes()
        path.write_bytes(original + b"SYNTHETIC refreshed same-coordinate tamper")
        row.update(bytes=path.stat().st_size, sha256=stage.digest(path.read_bytes()))
        return original


class OfficialCompanionProvenanceControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-NEW-SYNTHETIC-companion-pins-")
        self.addCleanup(temporary.cleanup)
        self.model = CompanionModel(Path(temporary.name))

    def refreshed_tamper_matrix(self, classified):
        for mode in ("module", "pom"):
            for configuration in resolution.CLASSPATHS:
                for module in stage.COMPANIONS:
                    observations = copy.deepcopy(self.model.observations)
                    observations["metadata_mode"] = mode
                    filename = f"javafx-{module}-{stage.UPSTREAM}" + ("-linux" if classified else "") + ".jar"
                    row = next(r for r in observations["resolved_artifacts"]
                               if r["configuration"] == configuration and r["file"] == filename)
                    path = Path(row["path"])
                    original = self.model.tamper_row(row)
                    with self.subTest(mode=mode, configuration=configuration, module=module):
                        try:
                            with self.assertRaisesRegex(stage.StageError, "Trusted official companion byte pin differs"):
                                self.model.verify(observations)
                        finally:
                            path.write_bytes(original)

    def test_new_same_identity_classified_tamper_with_refreshed_observations_refuses_in_each_mode_and_classpath(self):
        self.refreshed_tamper_matrix(classified=True)

    def test_new_same_identity_generic_tamper_with_refreshed_observations_refuses_in_each_mode_and_classpath(self):
        self.refreshed_tamper_matrix(classified=False)

    def test_new_fixed_synthetic_pins_admit_both_modes_without_promoting_to_ordinary_or_security_acceptance(self):
        for mode in ("module", "pom"):
            observations = self.model.observations | {"metadata_mode": mode}
            result = self.model.verify(observations)
            self.assertTrue(result["passed"])
            self.assertTrue(result["synthetic_companion_pin_checks"])
            self.assertFalse(result["official_companion_pins_bound"])
            self.assertFalse(result["ordinary_resolution_bytes_bound"])
            self.assertFalse(result["publication_ready"])
            self.assertEqual(result["native_executions"], 0)
            self.assertIn("SYNTHETIC", result["scope"])
        unbound = resolution._verify(self.model.report, self.model.observations, self.model.model.repository,
                                     model_classes=self.model.model.contract.classes)
        self.assertFalse(unbound["synthetic_companion_pin_checks"])
        self.assertFalse(unbound["ordinary_resolution_bytes_bound"])
        self.assertIn("SYNTHETIC", unbound["scope"])

    def test_new_missing_classified_trusted_pin_including_Swing_never_uses_observations(self):
        for mode in ("module", "pom"):
            for module in stage.COMPANIONS:
                pins = copy.deepcopy(self.model.pins)
                del pins[f"javafx-{module}-{stage.UPSTREAM}-linux.jar"]
                with self.subTest(mode=mode, module=module), self.assertRaisesRegex(stage.StageError, "Trusted official companion pin missing"):
                    self.model.verify(self.model.observations | {"metadata_mode": mode}, pins=pins)

    def test_new_missing_generic_pin_does_not_borrow_same_module_classified_pin(self):
        for mode in ("module", "pom"):
            for module in stage.COMPANIONS:
                pins = copy.deepcopy(self.model.pins)
                del pins[f"javafx-{module}-{stage.UPSTREAM}.jar"]
                with self.subTest(mode=mode, module=module), self.assertRaisesRegex(stage.StageError, "Trusted official companion pin missing"):
                    self.model.verify(self.model.observations | {"metadata_mode": mode}, pins=pins)

    def test_new_forged_stage_and_resolution_pin_fields_do_not_authorize_refreshed_companion_bytes(self):
        for mode in ("module", "pom"):
            for classified in (True, False):
                observations = copy.deepcopy(self.model.observations)
                filename = f"javafx-swing-{stage.UPSTREAM}" + ("-linux" if classified else "") + ".jar"
                row = next(r for r in observations["resolved_artifacts"]
                           if r["configuration"] == "testRuntimeClasspath" and r["file"] == filename)
                original = self.model.tamper_row(row)
                supplied = copy.deepcopy(self.model.pins)
                supplied[filename] = {key: row[key] for key in ("file", "bytes", "sha256")}
                observations.update(metadata_mode=mode, official_companion_pins=supplied,
                                    companion_pins=supplied, expected_companion_pins=supplied)
                self.model.report.update(official_companion_pins=supplied, companion_pins=supplied)
                try:
                    with self.subTest(mode=mode, classified=classified), self.assertRaisesRegex(stage.StageError, "Trusted official companion byte pin differs"):
                        self.model.verify(observations)
                finally:
                    Path(row["path"]).write_bytes(original)
                    self.model.report.pop("official_companion_pins"); self.model.report.pop("companion_pins")

    def test_new_trusted_digest_and_length_are_each_required_not_either_or(self):
        filename = f"javafx-base-{stage.UPSTREAM}-linux.jar"
        for key, value in (("bytes", self.model.pins[filename]["bytes"] + 1), ("sha256", "0" * 64)):
            pins = copy.deepcopy(self.model.pins)
            pins[filename][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(stage.StageError, "Trusted official companion byte pin differs"):
                self.model.verify(pins=pins)

    def test_new_model_pin_override_is_refused_before_any_production_candidate_reads(self):
        with self.assertRaisesRegex(stage.StageError, "Synthetic companion pins forbidden in production"):
            resolution._verify(self.model.report, self.model.observations, self.model.model.repository,
                               model_companion_pins=self.model.pins)

    def test_new_trusted_source_metadata_joins_original_four_and_reviewed_Swing_generic_for_all_targets(self):
        original_bytes = (stage.builder.HERE / "artifacts.json").read_bytes()
        supplemental_bytes = (stage.HERE / "official-companion-supplement.json").read_bytes()
        self.assertEqual(stage.digest(original_bytes), stage.OFFICIAL_ORIGINAL_PINS_SHA256)
        self.assertEqual(stage.digest(supplemental_bytes), stage.OFFICIAL_COMPANION_SUPPLEMENT_SHA256)
        originals = json.loads(original_bytes)
        supplement = json.loads(supplemental_bytes)
        joined = stage.trusted_companion_inventory({target: [originals["sources"], *originals["platforms"][target]]
                                                   for target in stage.CLASSIFIERS}, supplement)
        self.assertEqual(set(joined), set(stage.CLASSIFIERS))
        self.assertEqual(supplement["official_acquisition_expected_pins_sha256"],
                         "a93892b96ee4f0a3410b87158c14cc1cf70ddcd3b6e75e23ad046371248880ef")
        for target, values in joined.items():
            self.assertEqual(set(values), {f"javafx-{module}-{stage.UPSTREAM}" + suffix + ".jar"
                                          for module in stage.COMPANIONS for suffix in ("", "-" + target)})
            self.assertEqual(values[f"javafx-swing-{stage.UPSTREAM}-{target}.jar"], supplement["classified_swing"][target])
            for module in stage.COMPANIONS:
                self.assertEqual(values[f"javafx-{module}-{stage.UPSTREAM}.jar"], supplement["generic"][module])

    def test_new_missing_Swing_generic_or_mixed_classifier_source_material_fails_closed(self):
        original = json.loads((stage.builder.HERE / "artifacts.json").read_bytes())
        originals = {target: [original["sources"], *original["platforms"][target]] for target in stage.CLASSIFIERS}
        supplement = json.loads((stage.HERE / "official-companion-supplement.json").read_bytes())
        missing_swing = copy.deepcopy(supplement); del missing_swing["classified_swing"]["win"]
        missing_generic = copy.deepcopy(supplement); del missing_generic["generic"]["swing"]
        mixed = copy.deepcopy(supplement); mixed["classified_swing"]["win"] = mixed["classified_swing"]["linux"]
        for name, value in (("missing-Swing", missing_swing), ("missing-generic", missing_generic), ("mixed-classifier", mixed)):
            with self.subTest(name=name), self.assertRaisesRegex(stage.StageError, "Trusted official companion pin missing or malformed"):
                stage.trusted_companion_inventory(originals, value)


if __name__ == "__main__":
    unittest.main()
