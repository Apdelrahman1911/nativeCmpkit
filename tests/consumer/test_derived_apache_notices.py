"""NAV-018 source/history and synthetic archive guards, not real package/native tests.

Git commands below are fixed, read-only object queries against retained Calf history.
Archive fixtures are authored ZIP containers only; no Gradle, compiler, networking,
registry publication, native library loading or legal certification is performed.
Navigation has no publication root; its future archive policy uses a synthetic
identity only during fixture construction. UI uses the unchanged real identity.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

import verify_artifacts as gate


BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
NAV_ROOT = "calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/"
UI_ROOT = "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/"
COMMON_SLIDER = "calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt"
COMMON_SLIDER_ADDITION = "6eb7c66eb01b390353100c63882cd102846c7b8d"
COMMON_SLIDER_PARENT = "94d2492e99d5cbc060409d94d9f88febd06222d5"
INTRODUCTIONS = {
    **{NAV_ROOT + name + ".kt": ("9e1b08df630cea4ed29aeca63a44847154b45a90", NAV_ROOT + name + ".kt")
       for name in ("NavArgument", "AdaptiveNavType", "AdaptiveBaseBundle", "AdaptiveBundle")},
    UI_ROOT + "slider/CupertinoSlider.kt": ("fce1638c011f1d5528cbf0c833bee44b64a97e90", UI_ROOT + "slider/CupertinoSlider.kt"),
    UI_ROOT + "button/LiquidGlassButton.kt": ("caff0465ffd5ffc23741d5e4f21015bceda8a210", UI_ROOT + "button/LiquidGlassButton.kt"),
    UI_ROOT + "slider/LiquidGlassSlider.kt": ("fce1638c011f1d5528cbf0c833bee44b64a97e90", UI_ROOT + "slider/LiquidGlassSlider.kt"),
    UI_ROOT + "utils/DragGestureInspector.kt": ("caff0465ffd5ffc23741d5e4f21015bceda8a210",
        "calf-ui/src/iosArm64Main/kotlin/com/mohamedrejeb/calf/ui/button/DragGestureInspector.kt"),
    UI_ROOT + "utils/DampedDragAnimation.kt": ("01a070e9866fd7cb97424f1d09249378cdec0c28", UI_ROOT + "utils/DampedDragAnimation.kt"),
    UI_ROOT + "utils/InteractiveHighlight.kt": ("caff0465ffd5ffc23741d5e4f21015bceda8a210",
        "calf-ui/src/iosArm64Main/kotlin/com/mohamedrejeb/calf/ui/button/InteractiveHighlight.kt"),
}
APACHE_BODY = ''' * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.'''


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=gate.ROOT, capture_output=True, check=True).stdout


def archive_bytes(entries: dict[str, bytes]) -> bytes:
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return result.getvalue()


class DerivedApacheSourceTest(unittest.TestCase):
    def test_known_ui_copyright_headers_and_calf_change_notices_are_explicit(self):
        paths = {COMMON_SLIDER: "Copyright (c) 2023-2024. Compose Cupertino project and open source contributors.",
                 **{UI_ROOT + "utils/" + name + ".kt": "Copyright 2025 Kyant"
                    for name in ("DragGestureInspector", "DampedDragAnimation", "InteractiveHighlight")}}
        for path, copyright_text in paths.items():
            text = (gate.ROOT / path).read_text()
            with self.subTest(path=path):
                self.assertTrue(text.startswith("/*\n * " + copyright_text + "\n"))
                self.assertIn(APACHE_BODY, text)
                self.assertIn("The exact originally copied revision is unknown", text)
                self.assertIn("licenses/derived-apache-introduction-history.json", text)
                self.assertIn("// Modified for nativeCmpkit (2026-10-24):", text)

    def test_existing_navigation_headers_and_pinned_full_license_bytes_are_retained(self):
        copyrights = {"NavArgument": "Copyright 2018 The Android Open Source Project",
                      "AdaptiveNavType": "Copyright 2018 The Android Open Source Project",
                      "AdaptiveBaseBundle": "Copyright (C) 2014 The Android Open Source Project",
                      "AdaptiveBundle": "Copyright (C) 2007 The Android Open Source Project"}
        for name, copyright_text in copyrights.items():
            text = (gate.ROOT / (NAV_ROOT + name + ".kt")).read_text()
            with self.subTest(source=name):
                self.assertTrue(text.startswith("/*\n * " + copyright_text + "\n"))
                self.assertIn(APACHE_BODY, text)
                self.assertIn("Adapted for Calf and nativeCmpkit. Modified 2026-10-24:", text)
        for path, digest in {
            "LICENSE": "188187b988999fc9f6ecdae6ba6e49e4f53f0488ec5af68acbfff3b2cf0c8722",
            "licenses/compose-cupertino-Apache-2.0.txt": "f9a85c61ba4fe8bacc300053b3384b5fc7d9f585a08dc7b9a465b7c0716c4f50",
            "licenses/android-liquid-glass-Apache-2.0.txt": "4b9f7e7c2821a5a1822a6cf1e4a34e877bba48a99b9bba1f03e5e2eccf6dec56",
        }.items():
            with self.subTest(license=path):
                self.assertEqual(digest, hashlib.sha256((gate.ROOT / path).read_bytes()).hexdigest())
        self.assertIn(b"Copyright 2020-2021 JetBrains s.r.o. and and respective authors and developers.",
                      (gate.ROOT / "licenses/compose-cupertino-Apache-2.0.txt").read_bytes())

    def test_introduction_trace_matches_retained_added_paths_blobs_and_authors(self):
        history = json.loads((gate.ROOT / "licenses/derived-apache-introduction-history.json").read_text())
        self.assertEqual(BASELINE, history["reviewed_calf_baseline"])
        self.assertFalse(history["source_history_rewritten"])
        self.assertFalse(history["exact_original_copy_revisions_established"])
        records = {record["baseline_source_path"]: record for record in history["records"]}
        self.assertEqual(len(INTRODUCTIONS), len(history["records"]))
        self.assertEqual(set(INTRODUCTIONS), set(records))
        for baseline_path, (commit, introduced_path) in INTRODUCTIONS.items():
            record = records[baseline_path]
            with self.subTest(source=baseline_path):
                self.assertEqual(commit, record["introduction_commit"])
                self.assertEqual(introduced_path, record["introduced_source"]["path"])
                current_path = COMMON_SLIDER if baseline_path == UI_ROOT + "slider/CupertinoSlider.kt" else baseline_path
                self.assertEqual(current_path, record["current_source_path"])
                # Only fixed commits/paths above reach Git; JSON cannot inject options.
                self.assertEqual("A\t" + introduced_path,
                    git_bytes("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit,
                              "--", introduced_path).decode().strip())
                metadata = git_bytes("show", "--no-patch", "--format=%H%x00%an%x00%aI%x00%cn%x00%cI%x00%s", commit).decode().rstrip("\n").split("\0")
                self.assertEqual(commit, metadata[0])
                self.assertEqual({"name": metadata[1], "timestamp": metadata[2]}, record["author"])
                self.assertEqual({"name": metadata[3], "timestamp": metadata[4]}, record["committer"])
                self.assertEqual(metadata[5], record["introduction_subject"])
                for revision, path, facts in ((commit, introduced_path, record["introduced_source"]),
                    (BASELINE, baseline_path, record["reviewed_baseline_source"])):
                    self.assertEqual(path, facts["path"])
                    self.assertEqual(git_bytes("rev-parse", revision + ":" + path).decode().strip(), facts["git_blob_oid"])
                    self.assertEqual(hashlib.sha256(git_bytes("show", revision + ":" + path)).hexdigest(), facts["sha256"])
                self.assertIsNone(record["copied_upstream_revision"])
                self.assertIn("not established", record["copy_revision_status"])
                self.assertTrue(record["ancestor_of_reviewed_baseline"])
                self.assertEqual(b"", git_bytes("merge-base", "--is-ancestor", commit, BASELINE))

        # This later path replacement is not rewritten into a Git rename or
        # an original third-party copy revision. Its fixed retained objects
        # independently establish the commonMain A / historical iosMain D.
        baseline_path = UI_ROOT + "slider/CupertinoSlider.kt"
        transition = records[baseline_path]["post_baseline_path_transition"]
        self.assertEqual(COMMON_SLIDER_ADDITION, transition["commit"])
        self.assertEqual(COMMON_SLIDER_PARENT, transition["parent_commit"])
        self.assertFalse(transition["git_follow_reports_rename"])
        self.assertTrue(transition["reviewed_baseline_is_ancestor"])
        self.assertEqual(b"", git_bytes("merge-base", "--is-ancestor", BASELINE, COMMON_SLIDER_ADDITION))
        self.assertEqual([{"status": "A", "paths": [COMMON_SLIDER]},
                          {"status": "D", "paths": [baseline_path]}], transition["path_events"])
        self.assertEqual("A\t" + COMMON_SLIDER + "\nD\t" + baseline_path,
            git_bytes("diff-tree", "--no-commit-id", "--name-status", "-r", "-M",
                COMMON_SLIDER_ADDITION, "--", COMMON_SLIDER, baseline_path).decode().strip())
        self.assertEqual([COMMON_SLIDER_ADDITION, "", "A\t" + COMMON_SLIDER],
            git_bytes("log", "--follow", "--name-status", "--format=%H",
                COMMON_SLIDER_ADDITION, "--", COMMON_SLIDER).decode().strip().splitlines())
        metadata = git_bytes("show", "--no-patch", "--format=%H%x00%an%x00%aI%x00%cn%x00%cI%x00%P%x00%s",
            COMMON_SLIDER_ADDITION).decode().rstrip("\n").split("\0")
        self.assertEqual(COMMON_SLIDER_ADDITION, metadata[0])
        self.assertEqual(COMMON_SLIDER_PARENT, metadata[5])
        # Git 2.56 renders UTC as Z; the retained trace uses equivalent +00:00.
        # Normalize only this terminal spelling, never dates, offsets or names.
        for index in (2, 4):
            if metadata[index].endswith("Z"):
                metadata[index] = metadata[index][:-1] + "+00:00"
        self.assertEqual({"name": metadata[1], "timestamp": metadata[2]}, transition["author"])
        self.assertEqual({"name": metadata[3], "timestamp": metadata[4]}, transition["committer"])
        self.assertEqual(metadata[6], transition["subject"])
        for revision, path, facts in ((COMMON_SLIDER_PARENT, baseline_path, transition["parent_ios_source"]),
            (COMMON_SLIDER_ADDITION, COMMON_SLIDER, transition["added_common_source"])):
            self.assertEqual(path, facts["path"])
            self.assertEqual(git_bytes("rev-parse", revision + ":" + path).decode().strip(), facts["git_blob_oid"])
            source = git_bytes("show", revision + ":" + path)
            self.assertEqual(len(source), facts["bytes"])
            self.assertEqual(hashlib.sha256(source).hexdigest(), facts["sha256"])

    def test_renamed_utility_introductions_cannot_use_the_later_path(self):
        history = json.loads((gate.ROOT / "licenses/derived-apache-introduction-history.json").read_text())
        records = {record["baseline_source_path"]: record for record in history["records"]}
        for name, rename_status in (("DragGestureInspector", "R098"), ("InteractiveHighlight", "R096")):
            baseline_path = UI_ROOT + "utils/" + name + ".kt"
            commit, introduced_path = INTRODUCTIONS[baseline_path]
            record = records[baseline_path]
            with self.subTest(source=name):
                self.assertNotEqual(introduced_path, baseline_path)
                self.assertIn({"status": rename_status, "paths": [introduced_path, baseline_path]},
                    next(event for event in record["followed_path_events"]
                         if event["commit"] == "01a070e9866fd7cb97424f1d09249378cdec0c28")["path_events"])
                refused = subprocess.run(["git", "cat-file", "-e", commit + ":" + baseline_path],
                    cwd=gate.ROOT, capture_output=True)
                self.assertNotEqual(0, refused.returncode)
                self.assertEqual(git_bytes("rev-parse", commit + ":" + introduced_path).decode().strip(),
                    record["introduced_source"]["git_blob_oid"])


class DerivedApacheTimestampRenderingTest(unittest.TestCase):
    """Source-owning rendering models; no Git, fixtures, or legal edits."""

    AUTHOR_TIME = "2026-01-02T03:04:05+00:00"
    COMMITTER_TIME = "2026-01-02T04:05:06+00:00"

    def _metadata(self):
        return [COMMON_SLIDER_ADDITION, "Synthetic author", self.AUTHOR_TIME,
                "Synthetic committer", self.COMMITTER_TIME,
                COMMON_SLIDER_PARENT, "Synthetic transition"]

    def _guard(self, metadata):
        # Execute the actual owning transition assertions, not a second parser.
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        owning_class = next(node for node in tree.body
                            if isinstance(node, ast.ClassDef) and
                            node.name == "DerivedApacheSourceTest")
        owning_method = next(node for node in owning_class.body
                             if isinstance(node, ast.FunctionDef) and
                             node.name == "test_introduction_trace_matches_retained_added_paths_blobs_and_authors")
        starts = [index for index, node in enumerate(owning_method.body)
                  if isinstance(node, ast.Assign) and len(node.targets) == 1 and
                  isinstance(node.targets[0], ast.Name) and node.targets[0].id == "metadata"]
        self.assertEqual(1, len(starts))
        start = starts[0] + 1
        stop = next(index for index, node in enumerate(owning_method.body)
                    if index >= start and isinstance(node, ast.For) and
                    isinstance(node.target, ast.Tuple) and
                    [item.id for item in node.target.elts] == ["revision", "path", "facts"])
        transition = {"author": {"name": "Synthetic author", "timestamp": self.AUTHOR_TIME},
                      "committer": {"name": "Synthetic committer", "timestamp": self.COMMITTER_TIME},
                      "subject": "Synthetic transition"}
        fragment = ast.Module(body=owning_method.body[start:stop], type_ignores=[])
        namespace = {"self": self, "metadata": list(metadata), "transition": transition,
                     "COMMON_SLIDER_ADDITION": COMMON_SLIDER_ADDITION,
                     "COMMON_SLIDER_PARENT": COMMON_SLIDER_PARENT}
        with mock.patch.object(subprocess, "run", side_effect=AssertionError("No Git in rendering models")):
            exec(compile(fragment, __file__, "exec"), namespace)

    def test_git256_terminal_z_matches_existing_trace_positive_zero(self):
        metadata = self._metadata()
        metadata[2] = self.AUTHOR_TIME[:-6] + "Z"
        metadata[4] = self.COMMITTER_TIME[:-6] + "Z"
        self._guard(metadata)

    def test_legacy_positive_zero_rendering_is_unchanged(self):
        self._guard(self._metadata())

    def test_changed_author_instant_is_refused(self):
        metadata = self._metadata()
        metadata[2] = "2026-01-02T03:04:06Z"
        with self.assertRaises(AssertionError):
            self._guard(metadata)

    def test_changed_committer_instant_is_refused(self):
        metadata = self._metadata()
        metadata[4] = "2026-01-02T04:05:07Z"
        with self.assertRaises(AssertionError):
            self._guard(metadata)

    def test_changed_offsets_are_refused_even_at_same_instant(self):
        for index, timestamp in ((2, "2026-01-02T04:04:05+01:00"),
                                 (4, "2026-01-02T05:05:06+01:00")):
            with self.subTest(index=index):
                metadata = self._metadata()
                metadata[index] = timestamp
                with self.assertRaises(AssertionError):
                    self._guard(metadata)

    def test_nonterminal_or_malformed_z_is_refused(self):
        for index in (2, 4):
            for timestamp in ("2026-01-02T03:04:05Zsuffix",
                              "2026-01-02T03:04:05Z+00:00",
                              "2026-01-02T03:04:05+00:00Z",
                              "2026-01-02T03:04:05z",
                              "not-a-timestampZ"):
                with self.subTest(index=index, spelling=timestamp):
                    metadata = self._metadata()
                    metadata[index] = timestamp
                    with self.assertRaises(AssertionError):
                        self._guard(metadata)

    def test_changed_author_name_is_refused(self):
        metadata = self._metadata()
        metadata[1] = "Changed synthetic author"
        with self.assertRaises(AssertionError):
            self._guard(metadata)

    def test_changed_committer_name_is_refused(self):
        metadata = self._metadata()
        metadata[3] = "Changed synthetic committer"
        with self.assertRaises(AssertionError):
            self._guard(metadata)

    def test_negative_zero_offset_is_not_added_as_an_unobserved_alias(self):
        for index in (2, 4):
            with self.subTest(index=index):
                metadata = self._metadata()
                metadata[index] = metadata[index][:-6] + "-00:00"
                with self.assertRaises(AssertionError):
                    self._guard(metadata)

    def test_fixed_revision_parent_subject_assertions_still_refuse_changes(self):
        for index, value in ((0, "0" * 40), (5, "0" * 40),
                             (6, "Changed synthetic transition")):
            with self.subTest(index=index):
                metadata = self._metadata()
                metadata[index] = value
                with self.assertRaises(AssertionError):
                    self._guard(metadata)


class DerivedApacheArtifactTest(unittest.TestCase):
    VERSION = "0.1.0-preview.1"  # Synthetic/local candidate identity, not a published release.

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def verifier(self, module, target="metadata"):
        if module != "nativecmpkit-navigation":
            return gate.ArtifactVerifier(gate.ROOT, self.repository, self.VERSION,
                modules=[module], targets=[target])
        # NAV is an unpublished experiment, not one of the 21 publication roots.
        # Model its future archive policy without changing the real allowlist or
        # mocking archive/metadata parsing and checks after construction.
        identity_bytes = (gate.ROOT / "docs/migration/identity.json").read_bytes()
        identity = gate.load_json_bytes(identity_bytes)
        self.assertNotIn(module, {item["new_artifact"] for item in identity["modules"]})
        fixture_identity = {**identity, "modules": [*identity["modules"],
            {"new_artifact": module, "publication_status": "synthetic-fixture-only"}]}
        with mock.patch.object(gate, "load_json_bytes", return_value=fixture_identity) as load_identity:
            verifier = gate.ArtifactVerifier(gate.ROOT, self.repository, self.VERSION,
                modules=[module], targets=[target])
            load_identity.assert_called_once_with(identity_bytes)
        return verifier

    def test_navigation_model_identity_is_scoped_and_default_rejection_remains(self):
        parser = gate.load_json_bytes
        identity_path = gate.ROOT / "docs/migration/identity.json"
        original = identity_path.read_bytes()
        declared = self.verifier("nativecmpkit-ui").all_modules
        self.assertEqual(21, len(declared))
        self.assertNotIn("nativecmpkit-navigation", declared)
        for phase in ("before", "after"):
            if phase == "after":
                fixture = self.verifier("nativecmpkit-navigation")
                self.assertEqual(set(declared) | {"nativecmpkit-navigation"}, set(fixture.all_modules))
                self.assertIs(parser, gate.load_json_bytes)
            for module in ("nativecmpkit-navigation", "nativecmpkit-fixture-unknown"):
                with self.subTest(phase=phase, module=module):
                    with self.assertRaisesRegex(gate.InvalidArtifact, "Unknown selected module"):
                        gate.ArtifactVerifier(gate.ROOT, self.repository, self.VERSION,
                            modules=[module], targets=["metadata"])
        self.assertEqual(original, identity_path.read_bytes())

    @staticmethod
    def applicable_sources(verifier, module, target):
        return {entry: data for entry, data in verifier.expected_derived_apache_sources[module].items()
            if not entry.startswith("iosMain/") or target in gate.DERIVED_APACHE_ALL_SOURCE_TARGETS}

    @staticmethod
    def notices(verifier, module=None):
        prefix = gate.NOTICE_PREFIX if module is None else gate.NOTICE_PREFIX + "calf-" + module.removeprefix("nativecmpkit-") + "/"
        return {prefix + name: data for name, data in verifier.expected_notices.items()}

    def inspect(self, module, target, kind, entries):
        verifier = self.verifier(module, target)
        coordinate = module + gate.TARGET_SUFFIXES[target]
        suffix = {"sources": "-sources.jar", "jar": ".jar", "aar": ".aar", "notices": "-notices.zip", "klib": ".klib"}[kind]
        path = self.repository / (coordinate + "-" + self.VERSION + suffix)
        path.write_bytes(archive_bytes(entries))
        before = path.read_bytes()
        verifier.archive(path, coordinate, module, target, companion=kind == "notices")
        self.assertEqual(before, path.read_bytes(), "Inspection must not mutate compiler/archive payloads")
        return verifier

    def assert_passes(self, verifier):
        self.assertTrue(verifier.checks)
        self.assertEqual([], [check for check in verifier.checks if not check["passed"]])

    def test_source_archive_inherited_sets_and_notices_for_two_modules_seven_targets(self):
        for module in gate.DERIVED_APACHE_SOURCE_PATHS:
            for target in gate.TARGET_SUFFIXES:
                verifier = self.verifier(module, target)
                expected = self.applicable_sources(verifier, module, target)
                entries = {**self.notices(verifier, module), **expected}
                with self.subTest(module=module, target=target):
                    result = self.inspect(module, target, "sources", entries)
                    self.assert_passes(result)
                    self.assertEqual(len(expected), sum(":derived-apache-source:" in row["name"] for row in result.checks))
                    if module == "nativecmpkit-ui" and target not in gate.DERIVED_APACHE_ALL_SOURCE_TARGETS:
                        self.assertEqual(1, len(expected), "Do not fabricate iOS source applicability on desktop/Android/web")

    def test_missing_or_modified_source_header_and_body_is_rejected(self):
        module = "nativecmpkit-ui"
        verifier = self.verifier(module)
        expected = self.applicable_sources(verifier, module, "metadata")
        entry = "commonMain/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt"
        original = expected[entry]
        for mutated in (None, original.replace(b"Copyright (c) 2023-2024. Compose Cupertino project and open source contributors.", b"", 1), original + b"\n// altered source\n"):
            entries = {**self.notices(verifier, module), **expected}
            if mutated is None:
                del entries[entry]
            else:
                entries[entry] = mutated
            with self.subTest(kind="missing" if mutated is None else "modified"):
                result = self.inspect(module, "metadata", "sources", entries)
                self.assertTrue(any(not check["passed"] and check["name"].endswith(":derived-apache-source:" + entry)
                    for check in result.checks))

    def test_wrong_source_set_path_does_not_satisfy_inherited_source_retention(self):
        module = "nativecmpkit-navigation"
        verifier = self.verifier(module)
        expected = self.applicable_sources(verifier, module, "metadata")
        entry = next(iter(expected))
        entries = {**self.notices(verifier, module), **expected}
        entries[entry.replace("commonMain/", "wrongMain/", 1)] = entries.pop(entry)
        result = self.inspect(module, "metadata", "sources", entries)
        self.assertTrue(any(not check["passed"] and check["name"].endswith(":derived-apache-source:" + entry)
            for check in result.checks))

    def test_source_notice_omission_truncation_and_foreign_module_prefix_fail_closed(self):
        module = "nativecmpkit-ui"
        verifier = self.verifier(module)
        expected = self.applicable_sources(verifier, module, "metadata")
        original = {**self.notices(verifier, module), **expected}
        for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "licenses/compose-cupertino-Apache-2.0.txt",
                     "licenses/android-liquid-glass-Apache-2.0.txt", "licenses/derived-apache-introduction-history.json"):
            entry = gate.NOTICE_PREFIX + "calf-ui/" + name
            for mutation in ("missing", "truncated"):
                entries = original.copy()
                if mutation == "missing":
                    del entries[entry]
                else:
                    entries[entry] = entries[entry][:-1]
                with self.subTest(notice=name, mutation=mutation):
                    result = self.inspect(module, "metadata", "sources", entries)
                    self.assertTrue(any(not check["passed"] and check["name"].endswith(":notice:" + name)
                        for check in result.checks))
        foreign = {**{name.replace("/calf-ui/", "/calf-core/", 1): data
            for name, data in self.notices(verifier, module).items()}, **expected}
        result = self.inspect(module, "metadata", "sources", foreign)
        self.assertTrue(any(not check["passed"] and ":notice:" in check["name"] for check in result.checks))

    def test_jvm_and_android_archive_families_keep_module_scoped_notices(self):
        for module in gate.DERIVED_APACHE_SOURCE_PATHS:
            for target, kind in (("metadata", "jar"), ("desktop", "jar"), ("android", "aar")):
                verifier = self.verifier(module, target)
                entries = self.notices(verifier, module)
                with self.subTest(module=module, target=target):
                    self.assert_passes(self.inspect(module, target, kind, entries))
                    entry = gate.NOTICE_PREFIX + "calf-" + module.removeprefix("nativecmpkit-") + "/licenses/androidx-aosp-NOTICE.txt"
                    del entries[entry]
                    result = self.inspect(module, target, kind, entries)
                    self.assertTrue(any(not row["passed"] and row["name"].endswith(":notice:licenses/androidx-aosp-NOTICE.txt")
                        for row in result.checks))

    def test_compiler_klib_families_use_full_companion_text_without_payload_mutation(self):
        for module in gate.DERIVED_APACHE_SOURCE_PATHS:
            for target in ("js", "wasmJs", "iosArm64", "iosSimulatorArm64"):
                verifier = self.verifier(module, target)
                with self.subTest(module=module, target=target):
                    # This is only a ZIP fixture. It is not a compiled KLIB or execution.
                    self.assert_passes(self.inspect(module, target, "klib", {"default/manifest": b"synthetic-fixture-only\n"}))
                    self.assert_passes(self.inspect(module, target, "notices", self.notices(verifier)))
                    missing = self.notices(verifier)
                    del missing[gate.NOTICE_PREFIX + "licenses/android-liquid-glass-Apache-2.0.txt"]
                    result = self.inspect(module, target, "notices", missing)
                    self.assertTrue(any(not row["passed"] and row["name"].endswith(":notice:licenses/android-liquid-glass-Apache-2.0.txt")
                        for row in result.checks))

    def complete_metadata_fixture(self, module):
        verifier = self.verifier(module)
        directory = self.repository / gate.GROUP.replace(".", "/") / module / self.VERSION
        directory.mkdir(parents=True)
        prefix = module + "-" + self.VERSION
        primary = archive_bytes(self.notices(verifier, module))
        (directory / (prefix + ".jar")).write_bytes(primary)
        (directory / (prefix + "-sources.jar")).write_bytes(archive_bytes({
            **self.notices(verifier, module), **self.applicable_sources(verifier, module, "metadata")}))
        (directory / (prefix + "-notices.zip")).write_bytes(archive_bytes(self.notices(verifier)))
        (directory / (prefix + ".pom")).write_text(f'''<project xmlns="http://maven.apache.org/POM/4.0.0">
<modelVersion>4.0.0</modelVersion><groupId>{gate.GROUP}</groupId><artifactId>{module}</artifactId><version>{self.VERSION}</version>
<name>NativeCmpKit - {module.removeprefix("nativecmpkit-")}</name><url>{gate.DESTINATION}</url>
<licenses><license><name>Apache-2.0</name></license></licenses><scm><url>{gate.DESTINATION}</url></scm>
<developers><developer><id>Apdelrahman1911</id></developer><developer><id>MohamedRejeb</id></developer></developers></project>''')
        # Deliberately omit a sources variant: the owning runner must independently
        # require the publication's source JAR, not rely on producer-selected variants.
        metadata = {"formatVersion": "1.1", "component": {"group": gate.GROUP, "module": module, "version": self.VERSION},
            "variants": [{"name": "metadataApiElements", "attributes": {}, "files": [{
                "name": prefix + ".jar", "url": prefix + ".jar", "size": len(primary), "sha256": hashlib.sha256(primary).hexdigest()}]}]}
        (directory / (prefix + ".module")).write_text(json.dumps(metadata))
        return verifier, directory, prefix

    def test_owning_runner_requires_sources_even_when_metadata_omits_a_sources_variant(self):
        for module in gate.DERIVED_APACHE_SOURCE_PATHS:
            with self.subTest(module=module):
                verifier, directory, prefix = self.complete_metadata_fixture(module)
                accepted = verifier.run()
                self.assertTrue(accepted["success"], accepted["checks"])
                self.assertFalse(accepted["release_readiness_certified"])
                (directory / (prefix + "-sources.jar")).unlink()
                result = self.verifier(module).run()
                self.assertEqual([module + ":derived-apache-sources-present"],
                    [row["name"] for row in result["checks"] if not row["passed"]])

    def test_owning_runner_requires_exact_same_coordinate_companion(self):
        for module in gate.DERIVED_APACHE_SOURCE_PATHS:
            with self.subTest(module=module):
                verifier, directory, prefix = self.complete_metadata_fixture(module)
                self.assertTrue(verifier.run()["success"])
                companion = directory / (prefix + "-notices.zip")
                companion.rename(directory / ("foreign-coordinate-" + self.VERSION + "-notices.zip"))
                result = self.verifier(module).run()
                self.assertEqual([module + ":companion-notices-present"],
                    [row["name"] for row in result["checks"] if not row["passed"]])

    def test_unrelated_core_source_archives_do_not_gain_nav_ui_source_rules(self):
        result = self.inspect("nativecmpkit-core", "metadata", "sources", {"fixture.kt": b"// unchanged unrelated policy\n"})
        self.assert_passes(result)
        self.assertEqual([], [row for row in result.checks if ":derived-apache-" in row["name"]])


if __name__ == "__main__":
    unittest.main()
