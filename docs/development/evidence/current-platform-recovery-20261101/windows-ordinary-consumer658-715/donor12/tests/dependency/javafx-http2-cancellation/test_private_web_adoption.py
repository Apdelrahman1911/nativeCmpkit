"""NEW small synthetic staging/resolution controls, not real Java/native artifacts.

Only this file is selected. Existing native/control cohorts are not replayed.
Fake .class/native bytes are conspicuously nonexecutable and production CLI pins
must reject them. Model-positive results never become ordinary consumer evidence.
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile
import xml.etree.ElementTree as ET

import stage_private_web as stage
import private_web_resolution as resolution


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def jar(path, members):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as output:
        for name, payload in members.items():
            output.writestr(name, payload)


def review(original, changed, replaced, extra):
    retained = {name: stage.digest(payload) for name, payload in original.items() if name not in replaced}
    return {"original_members": len(original), "retained_payload_members": len(retained),
            "retained_payload_sha256": retained,
            "changed_payload_members": sorted(name for name in original if original[name] != changed[name]),
            "added_members": sorted(extra), "all_other_payloads_identical": True}


class Model:
    def __init__(self, directory, classifier="linux"):
        self.directory, self.classifier = directory, classifier
        self.root = directory / "candidate"
        self.root.mkdir(parents=True)
        originals = directory / "originals"
        owners = directory / "owners"
        originals.mkdir(); owners.mkdir()
        self.owner_payloads = {name: b"SYNTHETIC model owner only: " + name.encode() for name in stage.OWNERS}
        self.input_paths = {}
        for name, payload in self.owner_payloads.items():
            (owners / name).write_bytes(payload)
            self.input_paths[name] = owners / name
        self.classes = {stage.PREFIX + name: b"NOT_A_JVM_CLASS synthetic " + name.encode()
                        for name in stage.builder.CLASS_SHA256}
        self.original_web = {**self.classes, stage.PREFIX + "HTTP2Loader.class": b"OLD_NOT_A_JVM_CLASS",
                             "META-INF/MANIFEST.MF": stage.builder.ORIGINAL_MANIFEST,
                             stage.WEB_ENGINE: b"SYNTHETIC nonexecutable public class",
                             "module-info.class": b"SYNTHETIC nonexecutable JPMS descriptor",
                             stage.NATIVE[classifier]: b"SYNTHETIC nonloadable native payload"}
        self.original_source = {stage.probe.SOURCE_ENTRY: b"synthetic original source\n",
                                "Other.java": b"synthetic held other source\n", "SOURCE.txt": b"synthetic source marker\n"}
        self.changed_source = self.original_source[stage.probe.SOURCE_ENTRY] + b"synthetic cancellation delta\n"
        self.extra = stage.additions(self.original_source[stage.probe.SOURCE_ENTRY], self.changed_source, self.owner_payloads)
        self.web = self.original_web | self.classes | {"META-INF/MANIFEST.MF": stage.builder.CANDIDATE_MANIFEST} | self.extra
        self.sources = self.original_source | {stage.probe.SOURCE_ENTRY: self.changed_source} | self.extra
        original_rows = []
        name = f"javafx-web-{stage.UPSTREAM}-sources.jar"
        jar(originals / name, self.original_source)
        self.input_paths[name] = originals / name
        original_rows.append(self.pin(originals / name))
        for module in stage.probe.MODULES:
            name = f"javafx-{module}-{stage.UPSTREAM}-{classifier}.jar"
            jar(originals / name, self.original_web if module == "web" else {"MODEL.txt": b"synthetic companion " + module.encode()})
            self.input_paths[name] = originals / name
            original_rows.append(self.pin(originals / name))
        self.contract = stage.ArtifactContract(
            {name: stage.digest(payload) for name, payload in self.owner_payloads.items()},
            {classifier: original_rows}, {name: stage.digest(payload) for name, payload in self.classes.items()},
            {name: stage.digest(self.owner_payloads[name]) for name in stage.builder.LEGAL},
            lambda original: original + b"synthetic cancellation delta\n",
            web_members=len(self.original_web), source_members=len(self.original_source), production=False)
        self.jar = self.root / f"javafx-web-{stage.VERSION}-{classifier}.jar"
        self.source_jar = self.root / f"javafx-web-{stage.VERSION}-java-sources.jar"
        jar(self.jar, self.web); jar(self.source_jar, self.sources)
        (self.root / "source").mkdir()
        (self.root / "source" / "HTTP2Loader.java").write_bytes(self.changed_source)
        inputs = {str(path): stage.digest(path.read_bytes()) for path in self.input_paths.values()}
        dump(self.root / "inputs-before.json", inputs); dump(self.root / "inputs-after.json", inputs)
        self.result = {"schema_version": 1, "identity": stage.VERSION, "classifier": classifier, "passed": True,
                       "held_inputs": True, "default_dependencies_changed": False, "cached_JARs_modified": False,
                       "full_native_corresponding_source_complete": False, "native_executions": 0, "library_tests": 0,
                       "jar_file": self.jar.name, "java_sources_file": self.source_jar.name,
                       "jar_sha256": stage.digest(self.jar.read_bytes()), "java_sources_sha256": stage.digest(self.source_jar.read_bytes()),
                       "modified_source_sha256": stage.digest(self.changed_source), "modified_class_sha256": self.contract.classes,
                       "original_web_sha256": original_rows[-1]["sha256"], "original_java_sources_sha256": original_rows[0]["sha256"],
                       "fixture_scope": "SYNTHETIC ONLY; NOT real Java/native/consumer evidence"}
        self.save()
        dump(self.root / "jar-member-review.json", review(self.original_web, self.web,
             set(self.classes) | {"META-INF/MANIFEST.MF"}, self.extra))
        dump(self.root / "java-source-member-review.json", review(self.original_source, self.sources,
             {stage.probe.SOURCE_ENTRY}, self.extra))
        self.base = directory / "owned-private-repositories"
        self.base.mkdir()
        self.repository = self.base / "fresh"

    @staticmethod
    def pin(path):
        payload = path.read_bytes()
        return {"file": path.name, "bytes": len(payload), "sha256": stage.digest(payload)}

    def save(self):
        dump(self.root / "candidate.json", self.result)

    def inspect(self):
        return stage.inspect_candidate(self.root, self.contract)

    def stage(self):
        return stage.stage_validated(self.inspect(), self.repository, self.base)

    def mutate_web(self, name, payload):
        self.web[name] = payload
        jar(self.jar, self.web)
        self.result["jar_sha256"] = stage.digest(self.jar.read_bytes())
        self.save()

    def observations(self, report, mode="module"):
        data = {"schema_version": 1, "classifier": self.classifier, "metadata_mode": mode,
                "java_major": 17, "project_substitution": False, "runtime_init_scripts": False,
                "private_route_override": False, "runtime_module_patch": False, "resolved_artifacts": []}
        staged_web = self.repository / next(row["file"] for row in report["files"] if row["file"].endswith(stage.VERSION + ".jar"))
        runtime = self.directory / "resolved"
        runtime.mkdir()
        for configuration in resolution.CLASSPATHS:
            data["resolved_artifacts"].append(self.row(configuration, stage.GROUP, report["module"], stage.VERSION, staged_web))
            for module in stage.COMPANIONS:
                path = runtime / f"javafx-{module}-{stage.UPSTREAM}-{self.classifier}.jar"
                if not path.exists():
                    jar(path, {"MODEL.txt": b"synthetic normal companion " + module.encode()})
                data["resolved_artifacts"].append(self.row(configuration, "org.openjfx", "javafx-" + module, stage.UPSTREAM, path))
        return data

    @staticmethod
    def row(configuration, group, module, version, path):
        payload = path.read_bytes()
        return {"configuration": configuration, "component_kind": "module", "group": group, "module": module,
                "version": version, "file": path.name, "path": str(path), "bytes": len(payload), "sha256": stage.digest(payload)}

    def verify(self, report, observations):
        return resolution._verify(report, observations, self.repository, model_classes=self.contract.classes)


class PrivateWebStagingControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-NEW-private-web-model-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.model = Model(self.directory)

    def reject(self, text):
        with self.assertRaisesRegex((stage.StageError, OSError), text):
            self.model.inspect()
        self.assertFalse(self.model.repository.exists())

    def test_new_model_stages_standard_POM_and_module_without_original_self_dependency(self):
        report = self.model.stage()
        self.assertTrue(report["passed"])
        self.assertFalse(report["production_contract"])
        self.assertIn("SYNTHETIC", report["validation_scope"])
        pom = next(self.model.repository / row["file"] for row in report["files"] if row["file"].endswith(".pom"))
        self.assertIsNone(ET.fromstring(pom.read_bytes()).find("{http://maven.apache.org/POM/4.0.0}dependencies"))
        module = next(self.model.repository / row["file"] for row in report["files"] if row["file"].endswith(".module"))
        metadata = json.loads(module.read_bytes())
        self.assertEqual(metadata["component"], {"group": stage.GROUP, "module": "javafx-web-linux", "version": stage.VERSION})
        self.assertEqual({v["attributes"]["org.gradle.usage"] for v in metadata["variants"]}, {"java-api", "java-runtime"})
        self.assertTrue(all(v["attributes"]["org.gradle.jvm.version"] == 17 and "dependencies" not in v for v in metadata["variants"]))

    def test_new_copy_preserves_model_runtime_JPMS_native_and_Java_source_bytes_without_clearance(self):
        report = self.model.stage()
        for suffix, expected in ((stage.VERSION + ".jar", self.model.jar.read_bytes()), ("-sources.jar", self.model.source_jar.read_bytes())):
            path = self.model.repository / next(row["file"] for row in report["files"] if row["file"].endswith(suffix))
            self.assertEqual(path.read_bytes(), expected)
        self.assertFalse(report["publication_ready"])
        self.assertFalse(report["full_native_corresponding_source_complete"])
        self.assertTrue(report["java_sources_only"])
        self.assertEqual(report["native_executions"], 0)
        self.assertEqual(len(report["unresolved_corresponding_source_and_distribution_requirements"]), 5)
        self.assertEqual(report["official_companion_dependencies"], [f"org.openjfx:javafx-{m}:{stage.UPSTREAM}:linux" for m in stage.COMPANIONS])

    def test_new_all_five_explicit_classifier_models_have_distinct_private_modules_without_host_inference(self):
        names = set()
        for target in stage.CLASSIFIERS:
            directory = self.directory / target; directory.mkdir()
            report = Model(directory, target).stage()
            self.assertFalse(report["production_contract"])
            self.assertEqual(report["classifier"], target)
            names.add(report["module"])
        self.assertEqual(names, {"javafx-web-" + target for target in stage.CLASSIFIERS})

    def test_new_existing_repository_is_preserved_not_deleted_or_overwritten(self):
        self.model.repository.mkdir()
        sentinel = self.model.repository / "prior-evidence"; sentinel.write_bytes(b"keep")
        with self.assertRaisesRegex(stage.StageError, "Fresh private repository"):
            stage.stage_validated(self.model.inspect(), self.model.repository, self.model.base)
        self.assertEqual(sentinel.read_bytes(), b"keep")

    def test_new_repository_outside_owned_direct_child_or_overlapping_inputs_refuses(self):
        validated = self.model.inspect()
        for repository, base in ((self.directory / "outside", self.model.base), (self.model.base / "nested" / "leaf", self.model.base),
                                 (self.model.root / "child", self.model.root)):
            with self.subTest(repository=repository.name), self.assertRaises(stage.StageError):
                stage.stage_validated(validated, repository, base)

    def test_new_repository_symlink_refuses_without_touching_foreign_directory(self):
        foreign = self.directory / "foreign"; foreign.mkdir()
        self.model.repository.symlink_to(foreign, target_is_directory=True)
        with self.assertRaisesRegex(stage.StageError, "symlink"):
            stage.stage_validated(self.model.inspect(), self.model.repository, self.model.base)
        self.assertEqual(list(foreign.iterdir()), [])

    def test_new_missing_real_JAR_is_not_supplied_by_successful_JSON(self):
        self.model.jar.unlink()
        self.reject("No such file")

    def test_new_stale_candidate_JAR_digest_refuses_before_staging(self):
        with self.model.jar.open("ab") as output: output.write(b"changed")
        self.reject("artifact digest differs")

    def test_new_artifact_filename_traversal_and_public_or_unknown_identity_refuse(self):
        original = dict(self.model.result)
        for key, value in (("jar_file", "../outside.jar"), ("identity", "21.0.13-public"), ("classifier", "win-aarch64")):
            self.model.result = original | {key: value}; self.model.save()
            with self.subTest(key=key): self.reject("identity/classifier|filenames")

    def test_new_changed_or_mismatched_input_maps_refuse(self):
        after = json.loads((self.model.root / "inputs-after.json").read_bytes())
        after[next(iter(after))] = "0" * 64
        dump(self.model.root / "inputs-after.json", after)
        self.reject("input maps are not held")

    def test_new_actual_owning_file_changes_cannot_be_hidden_by_held_maps(self):
        self.model.input_paths["NOTICE.md"].write_bytes(b"changed synthetic notice")
        self.reject("input differs from held pin")

    def test_new_symlink_and_hardlink_original_input_refuse(self):
        path = self.model.input_paths["NOTICE.md"]
        foreign = self.directory / "foreign-notice"; foreign.write_bytes(path.read_bytes())
        path.unlink(); path.symlink_to(foreign)
        self.reject("symlink")
        path.unlink(); path.hardlink_to(foreign)
        self.reject("unshared")

    def test_new_java_source_only_cannot_be_promoted_to_full_source_or_native_completion(self):
        original = dict(self.model.result)
        for key, value in (("full_native_corresponding_source_complete", True), ("native_executions", False),
                           ("library_tests", True), ("default_dependencies_changed", True), ("cached_JARs_modified", True)):
            self.model.result = original | {key: value}; self.model.save()
            with self.subTest(key=key): self.reject("packaging-only boundaries")

    def test_new_changed_owning_class_with_refreshed_producer_JAR_hash_refuses(self):
        self.model.mutate_web(stage.PREFIX + "HTTP2Loader.class", b"different nonexecutable synthetic class")
        self.reject("class payloads differ")

    def test_new_changed_native_public_or_JPMS_payload_with_refreshed_hash_refuses(self):
        original = dict(self.model.web)
        for name in (stage.NATIVE["linux"], stage.WEB_ENGINE, "module-info.class"):
            self.model.web = dict(original)
            self.model.mutate_web(name, b"changed held model payload")
            with self.subTest(name=name): self.reject("public/native/JPMS")

    def test_new_extra_shadow_provider_traversal_and_signed_archive_refuse(self):
        original = dict(self.model.web)
        for name in ("nested/javafx/scene/web/WebEngine.class", "../outside", "META-INF/FORGERY.SF"):
            self.model.web = dict(original)
            self.model.mutate_web(name, b"synthetic unknown provider")
            with self.subTest(name=name): self.reject("unknown providers|Unsafe archive path|Signed archive")

    def test_new_duplicate_archive_entry_refuses_even_with_refreshed_hash(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.model.jar, "a") as output:
                output.writestr(stage.WEB_ENGINE, b"duplicate model provider")
        self.model.result["jar_sha256"] = stage.digest(self.model.jar.read_bytes()); self.model.save()
        self.reject("Duplicate")

    def test_new_changed_nonowning_source_JAR_or_modification_source_refuses(self):
        self.model.sources["Other.java"] = b"altered unrelated model source"
        jar(self.model.source_jar, self.model.sources)
        self.model.result["java_sources_sha256"] = stage.digest(self.model.source_jar.read_bytes()); self.model.save()
        self.reject("public/native/JPMS/source")

    def test_new_producer_retained_member_review_is_checked_against_actual_original_payloads(self):
        path = self.model.root / "jar-member-review.json"
        data = json.loads(path.read_bytes()); data["retained_payload_sha256"][stage.WEB_ENGINE] = "0" * 64
        dump(path, data)
        self.reject("disagree with producer review")

    def test_new_input_change_during_staging_preserves_failed_receipt_not_success(self):
        validated = self.model.inspect()
        original_write = stage.new_file

        def write_then_change(path, payload):
            original_write(path, payload)
            if path.name.endswith(stage.VERSION + ".jar"):
                self.model.input_paths["NOTICE.md"].write_bytes(b"changed after stage began")

        with patch.object(stage, "new_file", side_effect=write_then_change), self.assertRaisesRegex(stage.StageError, "changed during staging"):
            stage.stage_validated(validated, self.model.repository, self.model.base)
        receipt = json.loads((self.model.repository / "private-javafx-staging.json").read_bytes())
        self.assertFalse(receipt["passed"])
        self.assertNotIn("held_inputs", receipt)
        self.assertTrue(self.model.repository.exists())

    def test_new_production_contract_rejects_nonexecutable_synthetic_model_without_real_payload_staging(self):
        with self.assertRaisesRegex(stage.StageError, "pin differs"):
            stage.inspect_candidate(self.model.root, stage.production_contract())
        self.assertFalse(self.model.repository.exists())

    def test_new_CLI_has_no_coordinate_release_publish_download_or_model_override(self):
        for option in ("--group", "--version", "--publish", "--download", "--model-contract"):
            with self.subTest(option=option), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                stage.main(["--candidate-root", str(self.model.root), "--repository", str(self.model.repository), option, "forbidden"])
            self.assertEqual(caught.exception.code, 2)

    def test_new_duplicate_nonfinite_JSON_or_boolean_member_counts_refuse(self):
        for payload in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.subTest(payload=payload), self.assertRaises(stage.StageError): stage.document(payload)
        path = self.model.root / "jar-member-review.json"
        data = json.loads(path.read_bytes()); data["original_members"] = True
        dump(path, data)
        self.reject("producer review")

    def test_new_nonobject_candidate_JSON_is_a_bounded_refusal_not_an_attribute_error(self):
        for value in ([], None, "synthetic nonobject", 1, False):
            dump(self.model.root / "candidate.json", value)
            with self.subTest(kind=type(value).__name__): self.reject("Candidate JSON object")


class PrivateWebResolutionControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-NEW-resolution-model-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.model = Model(self.directory)
        self.report = self.model.stage()
        self.observations = self.model.observations(self.report)

    def reject(self, text):
        with self.assertRaisesRegex(stage.StageError, text):
            self.model.verify(self.report, self.observations)

    def test_new_both_metadata_modes_bind_four_model_classpaths_but_claim_zero_native_or_genuine_consumers(self):
        for mode in ("module", "pom"):
            self.observations["metadata_mode"] = mode
            result = self.model.verify(self.report, self.observations)
            self.assertTrue(result["passed"])
            self.assertFalse(result["ordinary_resolution_bytes_bound"])
            self.assertEqual((result["classpath_count"], result["native_executions"]), (4, 0))
            self.assertIn("SYNTHETIC", result["scope"])

    def test_new_original_upstream_web_dependency_is_refused_even_for_a_generic_empty_JAR(self):
        path = self.directory / f"javafx-web-{stage.UPSTREAM}.jar"; jar(path, {"MODEL.txt": b"empty upstream stub model"})
        self.observations["resolved_artifacts"].append(Model.row("testRuntimeClasspath", "org.openjfx", "javafx-web", stage.UPSTREAM, path))
        self.reject("Original web")

    def test_new_foreign_public_or_nested_native_shadow_provider_is_refused(self):
        base = list(self.observations["resolved_artifacts"])
        for member in (stage.WEB_ENGINE, "nested/platform/" + stage.NATIVE["linux"]):
            path = self.directory / "shadow.jar"; jar(path, {member: b"SYNTHETIC foreign provider"})
            self.observations["resolved_artifacts"] = base + [Model.row("runtimeClasspath", "foreign.model", "shadow", "1", path)]
            with self.subTest(member=member): self.reject("exactly one cured web")

    def test_new_wrong_private_module_or_observed_resolved_hash_is_refused(self):
        original = copy.deepcopy(self.observations)
        for key, value in (("module", "javafx-web-mac"), ("sha256", "0" * 64)):
            self.observations = copy.deepcopy(original)
            self.observations["resolved_artifacts"][0][key] = value
            with self.subTest(key=key): self.reject("identity/provenance|bytes differ")

    def test_new_mixed_companion_version_or_foreign_classifier_refuses(self):
        original = copy.deepcopy(self.observations)
        self.observations["resolved_artifacts"][1]["version"] = "22.0.2"
        self.reject("mixed")
        self.observations = original
        path = self.directory / f"javafx-base-{stage.UPSTREAM}-mac.jar"; jar(path, {"MODEL.txt": b"foreign classifier model"})
        self.observations["resolved_artifacts"][1] = Model.row("compileClasspath", "org.openjfx", "javafx-base", stage.UPSTREAM, path)
        self.reject("Foreign classifier")

    def test_new_generic_official_companion_stubs_do_not_substitute_for_explicit_classifier(self):
        rows = self.observations["resolved_artifacts"]
        path = self.directory / f"javafx-base-{stage.UPSTREAM}.jar"; jar(path, {"MODEL.txt": b"generic stub model"})
        rows[1] = Model.row("compileClasspath", "org.openjfx", "javafx-base", stage.UPSTREAM, path)
        self.reject("five explicit companion classifiers")

    def test_new_legitimate_generic_companion_stub_beside_explicit_classifier_is_not_a_web_provider(self):
        path = self.directory / f"javafx-base-{stage.UPSTREAM}.jar"; jar(path, {"MODEL.txt": b"generic stub model"})
        self.observations["resolved_artifacts"].append(Model.row("compileClasspath", "org.openjfx", "javafx-base", stage.UPSTREAM, path))
        result = self.model.verify(self.report, self.observations)
        self.assertFalse(result["production_pins_required"])
        self.assertEqual(result["resolved_rows"], 25)

    def test_new_missing_classpath_or_duplicate_observation_does_not_shrink_or_expand_acceptance(self):
        original = list(self.observations["resolved_artifacts"])
        self.observations["resolved_artifacts"] = [r for r in original if r["configuration"] != "testCompileClasspath"]
        self.reject("Every classpath")
        self.observations["resolved_artifacts"] = original + [dict(original[0])]
        self.reject("Duplicate resolved")

    def test_new_project_substitution_route_init_module_patch_or_wrong_JDK_refuse(self):
        original = copy.deepcopy(self.observations)
        for key, value in (("project_substitution", True), ("runtime_init_scripts", True), ("private_route_override", True),
                           ("runtime_module_patch", True), ("java_major", True), ("java_major", 21)):
            self.observations = original | {key: value}
            with self.subTest(key=key, value=value): self.reject("JDK17 resolution")
        self.observations = copy.deepcopy(original)
        self.observations["resolved_artifacts"][0]["component_kind"] = "project"
        self.reject("Project/loose")

    def test_new_refreshed_POM_hash_cannot_hide_copied_upstream_web_self_dependency(self):
        row = next(row for row in self.report["files"] if row["file"].endswith(".pom"))
        path = self.model.repository / row["file"]
        payload = path.read_bytes().replace(b"</project>", b"<dependencies><dependency><groupId>org.openjfx</groupId><artifactId>javafx-web</artifactId></dependency></dependencies></project>")
        path.write_bytes(payload); row.update(bytes=len(payload), sha256=stage.digest(payload))
        self.reject("self-dependency")

    def test_new_actual_staged_or_resolved_file_change_refuses_without_relabeling_old_hash(self):
        path = Path(self.observations["resolved_artifacts"][1]["path"])
        with path.open("ab") as output: output.write(b"changed model artifact")
        self.reject("bytes differ")

    def test_new_actual_candidate_origin_is_required_not_a_forged_staging_success_JSON(self):
        self.assertEqual(self.report["candidate_root"], str(self.model.root))
        self.report.pop("candidate_root")
        self.reject("Actual candidate origin")

    def test_new_refreshed_staged_source_hash_cannot_hide_a_different_candidate_source(self):
        row = next(row for row in self.report["files"] if row["file"].endswith("-sources.jar"))
        path = self.model.repository / row["file"]
        jar(path, {"FAKE.txt": b"SYNTHETIC sources not corresponding to candidate"})
        payload = path.read_bytes(); row.update(bytes=len(payload), sha256=stage.digest(payload))
        self.reject("candidate/staged runtime or Java-source")

    def test_new_versioned_public_or_uppercase_nested_native_shadow_provider_refuses(self):
        original = list(self.observations["resolved_artifacts"])
        for member in ("META-INF/versions/17/" + stage.WEB_ENGINE, "nested/" + stage.NATIVE["linux"].upper()):
            path = self.directory / "versioned-shadow.jar"
            jar(path, {member: b"SYNTHETIC foreign versioned provider"})
            self.observations["resolved_artifacts"] = original + [Model.row("runtimeClasspath", "foreign.model", "shadow", "1", path)]
            with self.subTest(member=member): self.reject("exactly one cured web")

    def test_new_original_Calf_module_is_not_a_packaged_independent_dependency(self):
        path = self.directory / "calf-old.jar"; jar(path, {"MODEL.txt": b"SYNTHETIC original-source fallback"})
        self.observations["resolved_artifacts"].append(Model.row("compileClasspath", "com.mohamedrejeb.calf", "calf-webview", "0.9.1", path))
        self.reject("Original Calf/source fallback")

    def test_new_candidate_changes_after_staging_refuse_without_consuming_a_forged_receipt(self):
        jar(self.model.source_jar, {"MODEL.txt": b"SYNTHETIC candidate changed after staging"})
        self.reject("candidate/staged runtime or Java-source")

    def test_new_resolution_reads_inventory_from_the_same_captured_bytes_it_hashes(self):
        # If the verifier reopened an inspected path, this would be a producer-
        #controlled time-of-check/use gap. Every JAR read uses captured bytes.
        original_zipfile = resolution.zipfile.ZipFile
        def from_captured_bytes(file, *args, **kwargs):
            self.assertIsInstance(file, io.BytesIO)
            return original_zipfile(file, *args, **kwargs)
        with patch.object(resolution.zipfile, "ZipFile", side_effect=from_captured_bytes):
            result = self.model.verify(self.report, self.observations)
        self.assertFalse(result["ordinary_resolution_bytes_bound"])

    def test_new_nonobject_staging_or_resolution_JSON_cannot_claim_a_graph_or_throw_raw_attribute_errors(self):
        for value in ([], None, "synthetic nonobject", 1, False):
            for report, observation in ((value, self.observations), (self.report, value)):
                with self.subTest(kind=type(value).__name__), self.assertRaisesRegex(stage.StageError, "JSON objects"):
                    self.model.verify(report, observation)

    def test_new_production_resolution_entry_cannot_promote_synthetic_model_to_genuine_artifacts(self):
        with self.assertRaisesRegex(stage.StageError, "staging boundary"):
            resolution.verify_private_resolution(self.report, self.observations, self.model.repository)
        promoted = self.report | {"production_contract": True}
        with self.assertRaisesRegex(stage.StageError, "owning class"):
            resolution.verify_private_resolution(promoted, self.observations, self.model.repository)


if __name__ == "__main__":
    unittest.main()
