"""Synthetic metadata ownership guards; not packaged Kotlin/native execution."""
from __future__ import annotations

import json
from pathlib import Path

import verify_artifacts as gate
from test_verify_artifacts import RepositoryFixtureBase


class GradleOwningComponentTest(RepositoryFixtureBase):
    ROOT_MODULE = "nativecmpkit-core"
    TARGET_MODULE = "nativecmpkit-core-desktop"

    def metadata_path(self, coordinate: str) -> Path:
        return self.directory(coordinate) / f"{coordinate}-{self.VERSION}.module"

    def read_metadata(self, coordinate: str) -> dict:
        return json.loads(self.metadata_path(coordinate).read_bytes())

    def write_metadata(self, coordinate: str, data: object) -> None:
        self.metadata_path(coordinate).write_text(json.dumps(data))

    def owning_fixture(self) -> None:
        # Actual Gradle9.7.1/KGP target metadata has the owner's coordinates and
        # this canonical back-pointer, NOT the target file's Maven coordinate.
        target = self.read_metadata(self.TARGET_MODULE)
        target["variants"][0]["name"] = "desktopRuntimeElements-published"
        target["variants"][0]["attributes"] = {"org.gradle.usage": "java-runtime"}
        target["component"] = {
            "group": gate.GROUP, "module": self.ROOT_MODULE, "version": self.VERSION,
            "url": f"../../{self.ROOT_MODULE}/{self.VERSION}/{self.ROOT_MODULE}-{self.VERSION}.module",
            "attributes": {"org.gradle.status": "release"},
        }
        root = self.read_metadata(self.ROOT_MODULE)
        root["component"]["attributes"] = {"org.gradle.status": "release"}
        root["variants"][1]["name"] = target["variants"][0]["name"]
        root["variants"][1]["attributes"] = target["variants"][0]["attributes"]
        self.write_metadata(self.ROOT_MODULE, root)
        self.write_metadata(self.TARGET_MODULE, target)

    def target_identity_passes(self) -> bool:
        verifier = gate.ArtifactVerifier(self.root, self.repo, self.VERSION,
                                         targets=["desktop"], native_platforms=["linux-x64"])
        verifier.metadata(self.metadata_path(self.TARGET_MODULE), self.TARGET_MODULE,
                          self.ROOT_MODULE, "desktop")
        identities = [c for c in verifier.checks
                      if c["name"] == self.TARGET_MODULE + ":module-identity"]
        self.assertEqual(1, len(identities))
        return identities[0]["passed"]

    def test_real_shaped_owning_component_and_reciprocal_variants_pass(self):
        self.owning_fixture()
        self.assertTrue(self.target_identity_passes())
        result = self.run_gate()
        self.assertTrue(result["success"], [c for c in result["checks"] if not c["passed"]])
        self.assertFalse(result["complete_declared_artifact_matrix_requested"])
        self.assertFalse(result["release_readiness_certified"])

    def test_direct_target_identity_without_backpointer_still_passes(self):
        self.assertTrue(self.target_identity_passes())

    def test_direct_identity_cannot_hide_a_foreign_backpointer(self):
        target = self.read_metadata(self.TARGET_MODULE)
        target["component"]["url"] = "https://example.invalid/foreign.module"
        self.write_metadata(self.TARGET_MODULE, target)
        self.assertFalse(self.target_identity_passes())

    def test_owning_coordinates_require_the_backpointer(self):
        self.owning_fixture()
        target = self.read_metadata(self.TARGET_MODULE)
        del target["component"]["url"]
        self.write_metadata(self.TARGET_MODULE, target)
        self.assertFalse(self.target_identity_passes())

    def test_owning_coordinates_cannot_change_group_module_or_version(self):
        self.owning_fixture()
        original = self.read_metadata(self.TARGET_MODULE)
        for key, value in [("group", "com.mohamedrejeb.calf"),
                           ("module", "nativecmpkit-io"), ("version", "0.1.0-preview.2")]:
            with self.subTest(key=key):
                target = json.loads(json.dumps(original))
                target["component"][key] = value
                self.write_metadata(self.TARGET_MODULE, target)
                self.assertFalse(self.target_identity_passes())

    def test_only_exact_canonical_owner_url_is_allowed(self):
        self.owning_fixture()
        original = self.read_metadata(self.TARGET_MODULE)
        good = original["component"]["url"]
        for url in ["https://example.invalid/owner.module", "/tmp/owner.module",
                    good + "?query=1", good + "#fragment", good.replace("../", "%2e%2e/", 1),
                    good.replace("../", "%252e%252e/", 1), good.replace("/", "\\"),
                    "../../../outside.module", good.replace(self.ROOT_MODULE, "nativecmpkit-io")]:
            with self.subTest(url=url):
                target = json.loads(json.dumps(original))
                target["component"]["url"] = url
                self.write_metadata(self.TARGET_MODULE, target)
                self.assertFalse(self.target_identity_passes())

    def test_missing_owning_metadata_fails_the_target_identity(self):
        self.owning_fixture()
        self.metadata_path(self.ROOT_MODULE).unlink()
        self.assertFalse(self.target_identity_passes())

    def test_symlinked_owning_metadata_is_not_an_accepted_owner(self):
        self.owning_fixture()
        path = self.metadata_path(self.ROOT_MODULE)
        copy = path.with_suffix(".copy")
        path.rename(copy)
        path.symlink_to(copy.name)
        self.assertFalse(self.target_identity_passes())

    def test_owner_must_have_exact_direct_root_coordinates_and_attributes(self):
        self.owning_fixture()
        original = self.read_metadata(self.ROOT_MODULE)
        mutations = [("group", "com.mohamedrejeb.calf"), ("module", self.TARGET_MODULE),
                     ("version", "0.1.0-preview.2"), ("url", "./self.module"),
                     ("attributes", {"org.gradle.status": "integration"})]
        for key, value in mutations:
            with self.subTest(key=key):
                root = json.loads(json.dumps(original))
                root["component"][key] = value
                self.write_metadata(self.ROOT_MODULE, root)
                self.assertFalse(self.target_identity_passes())

    def test_owner_redirect_must_match_exact_target_coordinate_and_url(self):
        self.owning_fixture()
        original = self.read_metadata(self.ROOT_MODULE)
        for key, value in [("group", "com.mohamedrejeb.calf"), ("module", "nativecmpkit-io-desktop"),
                           ("version", "0.1.0-preview.2"), ("url", "https://example.invalid/target.module")]:
            with self.subTest(key=key):
                root = json.loads(json.dumps(original))
                root["variants"][1]["available-at"][key] = value
                self.write_metadata(self.ROOT_MODULE, root)
                self.assertFalse(self.target_identity_passes())

    def test_owner_and_target_variant_names_and_attributes_must_agree(self):
        self.owning_fixture()
        original = self.read_metadata(self.ROOT_MODULE)
        for field, value in [("name", "foreignRuntime"),
                             ("attributes", {"org.gradle.usage": "java-api"})]:
            with self.subTest(field=field):
                root = json.loads(json.dumps(original))
                root["variants"][1][field] = value
                self.write_metadata(self.ROOT_MODULE, root)
                self.assertFalse(self.target_identity_passes())

    def test_duplicate_or_missing_reciprocal_variants_are_not_accepted(self):
        self.owning_fixture()
        original = self.read_metadata(self.ROOT_MODULE)
        for variants in [original["variants"][:1], original["variants"] + [original["variants"][1]]]:
            with self.subTest(count=len(variants)):
                root = json.loads(json.dumps(original))
                root["variants"] = variants
                self.write_metadata(self.ROOT_MODULE, root)
                self.assertFalse(self.target_identity_passes())

    def test_missing_target_variant_cannot_hide_an_extra_owner_redirect(self):
        self.owning_fixture()
        target = self.read_metadata(self.TARGET_MODULE)
        target["variants"] = []
        self.write_metadata(self.TARGET_MODULE, target)
        self.assertFalse(self.target_identity_passes())

    def test_malformed_components_and_formats_are_rejected_without_crashes(self):
        original = self.read_metadata(self.TARGET_MODULE)
        for component in [None, [], "foreign", 7]:
            with self.subTest(component=component):
                target = json.loads(json.dumps(original))
                target["component"] = component
                self.write_metadata(self.TARGET_MODULE, target)
                self.assertFalse(self.target_identity_passes())
        target = json.loads(json.dumps(original))
        target["formatVersion"] = "99.0"
        self.write_metadata(self.TARGET_MODULE, target)
        self.assertFalse(self.target_identity_passes())

    def test_unstaged_apple_redirects_still_require_independent_candidate_coordinates(self):
        # A partial desktop build must not admit Calf-named Apple redirects just
        # because their native cinterop cannot execute on the producer's host.
        original = self.read_metadata(self.ROOT_MODULE)
        for target, suffix in (("iosArm64", "iosarm64"), ("iosSimulatorArm64", "iossimulatorarm64")):
            root = json.loads(json.dumps(original))
            old = "calf-core-" + suffix
            redirect = {"group": gate.GROUP, "module": old, "version": self.VERSION,
                        "url": f"../../{old}/{self.VERSION}/{old}-{self.VERSION}.module"}
            root["variants"].append({"name": target + "ApiElements-published",
                "attributes": {"org.gradle.usage": "kotlin-api", "org.jetbrains.kotlin.platform.type": "native"},
                "available-at": redirect})
            self.write_metadata(self.ROOT_MODULE, root)
            bad = self.run_gate()
            with self.subTest(target=target):
                self.assertFalse(bad["success"])
                self.assertTrue(any(c["name"].endswith(":available-at:candidate-identity") and not c["passed"]
                                    for c in bad["checks"]))
                new = self.ROOT_MODULE + "-" + suffix
                redirect.update(module=new, url=f"../../{new}/{self.VERSION}/{new}-{self.VERSION}.module")
                self.write_metadata(self.ROOT_MODULE, root)
                fixed = self.run_gate()
                self.assertTrue(fixed["success"], [c for c in fixed["checks"] if not c["passed"]])
                self.assertFalse(fixed["complete_declared_artifact_matrix_requested"])
                self.assertFalse(fixed["release_readiness_certified"])
