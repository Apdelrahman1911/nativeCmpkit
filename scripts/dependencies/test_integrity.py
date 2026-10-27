"""Offline parser/path/receipt/fixture tests. These NEVER invoke Gradle.

Synthetic receipts test rejection logic only; passing this suite is not actual
Gradle checksum/locking enforcement, graph acquisition or platform verification.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import integrity as driver
import integrity_model as m
import gradle_fixtures as fixtures


class TemporaryCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-dependency-offline-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def fixture(self, name="candidate", **kwargs):
        root = self.root / name
        marker = fixtures.create(root, **kwargs)
        return root, marker

    def installed_gradle_stub(self):
        root = self.root / "gradle-9.7.1"
        (root / "bin").mkdir(parents=True, exist_ok=True)
        (root / "lib").mkdir(exist_ok=True)
        (root / "bin/gradle").write_text("NOT EXECUTED\n")
        (root / "lib/gradle-core-api-9.7.1.jar").write_bytes(b"synthetic command-construction identity only")
        return root


class MetadataTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.entries = fixtures.known_metadata()
        self.xml = m.metadata_bytes(self.entries)

    def test_exact_sha_metadata_round_trip(self):
        self.assertEqual(self.entries, m.parse_metadata(self.xml))

    def test_metadata_verification_cannot_be_disabled(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(self.xml.replace(b"<verify-metadata>true", b"<verify-metadata>false"))

    def test_no_invented_signature_trust(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(self.xml.replace(b"<verify-signatures>false", b"<verify-signatures>true"))

    def test_no_trusted_artifact_bypass(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(self.xml.replace(b"</configuration>", b'<trusted-artifacts><trust group=".*" regex="true"/></trusted-artifacts></configuration>'))

    def test_dtd_entity_rejected_without_expansion(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(b'<!DOCTYPE verification-metadata [<!ENTITY x SYSTEM "file:///etc/passwd">]>' + self.xml)

    def test_wrong_namespace_rejected(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(self.xml.replace(m.NAMESPACE.encode(), b"https://example.invalid/verification"))

    def test_missing_hash_rejected(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(self.xml.replace(b"<sha256 ", b"<sha1 "))

    def test_invalid_hash_rejected(self):
        value = next(iter(self.entries.values())).encode()
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(self.xml.replace(value, b"not-a-sha256"))

    def test_also_trust_is_rejected(self):
        changed = self.xml.replace(b' />', b'><also-trust value="' + b"0" * 64 + b'"/></sha256>', 1)
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(changed)

    def test_duplicate_component_rejected(self):
        start = self.xml.index(b"<component ")
        end = self.xml.index(b"</component>", start) + len(b"</component>")
        changed = self.xml.replace(b"</components>", self.xml[start:end] + b"</components>")
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(changed)

    def test_artifact_path_escape_rejected(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(self.xml.replace(b'name="extra-1.0.jar"', b'name="../extra-1.0.jar"'))

    def test_external_snapshot_is_not_verified(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_metadata(self.xml.replace(b'version="1.0"', b'version="1.0-SNAPSHOT"'))

    def test_identical_candidates_deduplicate(self):
        self.assertEqual(self.entries, m.merge_metadata([self.entries, dict(self.entries)]))

    def test_conflicting_sha_candidates_fail(self):
        other = dict(self.entries)
        other[next(iter(other))] = "0" * 64
        with self.assertRaises(m.IntegrityError):
            m.merge_metadata([self.entries, other])

    def test_conflicting_merge_leaves_all_inputs_and_output_untouched(self):
        first, second, output = (self.root / name for name in ("first.xml", "second.xml", "output.xml"))
        first.write_bytes(self.xml)
        other = dict(self.entries)
        other[next(iter(other))] = "0" * 64
        second.write_bytes(m.metadata_bytes(other))
        output.write_bytes(b"pre-existing evidence")
        before = {path: path.read_bytes() for path in (first, second, output)}
        with self.assertRaises(m.IntegrityError):
            driver.merge_files([first, second], output)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_merge_never_replaces_input_even_when_compatible(self):
        path = self.root / "policy.xml"
        path.write_bytes(self.xml)
        with self.assertRaises(m.IntegrityError):
            driver.merge_files([path], path)
        self.assertEqual(self.xml, path.read_bytes())

    def test_new_merge_is_deterministic_and_does_not_claim_trust(self):
        path, output = self.root / "policy.xml", self.root / "merged.xml"
        path.write_bytes(self.xml)
        result = driver.merge_files([path], output)
        self.assertEqual(self.xml, output.read_bytes())
        self.assertFalse(result["independent_trust_reviewed"])
        self.assertFalse(result["installed_into_source_checkout"])


class LockTests(unittest.TestCase):
    def test_per_configuration_versions_are_separate(self):
        state = m.parse_lock(b"g:a:1.0=one\ng:a:2.0=two\nempty=three\n")
        m.verify_configuration_lock(state, "one", {("g", "a", "1.0")})
        m.verify_configuration_lock(state, "two", {("g", "a", "2.0")})
        m.verify_configuration_lock(state, "three", set())

    def test_missing_configuration_fails_even_if_empty(self):
        with self.assertRaises(m.IntegrityError):
            m.verify_configuration_lock(m.parse_lock(b"empty=\n"), "missing", set())

    def test_transitive_drift_fails(self):
        with self.assertRaises(m.IntegrityError):
            m.verify_configuration_lock(m.parse_lock(b"g:leaf:1.0=runtime\n"), "runtime", {("g", "leaf", "1.1")})

    def test_dependency_addition_fails(self):
        with self.assertRaises(m.IntegrityError):
            m.verify_configuration_lock(m.parse_lock(b"g:parent:1.0=runtime\n"), "runtime", {("g", "parent", "1.0"), ("g", "leaf", "1.0")})

    def test_dependency_removal_fails(self):
        with self.assertRaises(m.IntegrityError):
            m.verify_configuration_lock(m.parse_lock(b"g:parent:1.0=runtime\ng:leaf:1.0=runtime\n"), "runtime", {("g", "parent", "1.0")})

    def test_conflicting_same_configuration_versions_fail(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_lock(b"g:a:1.0=runtime\ng:a:2.0=runtime\n")

    def test_duplicate_lock_entries_fail(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_lock(b"g:a:1.0=runtime\ng:a:1.0=compile\n")

    def test_duplicate_configuration_names_fail(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_lock(b"g:a:1.0=runtime,runtime\n")

    def test_empty_populated_conflict_fails(self):
        with self.assertRaises(m.IntegrityError):
            m.parse_lock(b"g:a:1.0=runtime\nempty=runtime\n")

    def test_unknown_host_has_no_fallback(self):
        for values in (("Linux", "riscv64"), ("Windows", "arm64"), ("FreeBSD", "amd64"), ("", "")):
            with self.subTest(values=values), self.assertRaises(m.IntegrityError):
                m.host_key(*values)

    def test_actual_supported_host_aliases(self):
        for system, arch, expected in (("Linux", "amd64", "linux-x64"), ("Linux", "aarch64", "linux-arm64"),
                                       ("Darwin", "arm64", "macos-arm64"), ("Mac OS X", "x86_64", "macos-x64"),
                                       ("Windows", "AMD64", "windows-x64")):
            self.assertEqual(expected, m.host_key(system, arch))

    def test_host_routes_remain_owner_local(self):
        self.assertEqual("gradle/dependency-locks/linux-x64.lockfile", m.lock_path(".", "linux-x64"))
        self.assertEqual("convention-plugins/gradle/dependency-locks/macos-arm64.lockfile", m.lock_path("convention-plugins", "macos-arm64"))


class FileAndSnapshotTests(TemporaryCase):
    def test_duplicate_json_keys_fail(self):
        path = self.root / "duplicate.json"
        path.write_text('{"mode":"check","mode":"bootstrap"}')
        with self.assertRaises(m.IntegrityError):
            m.read_json(path)

    def test_nonfinite_json_fails(self):
        path = self.root / "nonfinite.json"
        path.write_text('{"number":NaN}')
        with self.assertRaises(m.IntegrityError):
            m.read_json(path)

    def test_relative_path_escape_and_url_rejected(self):
        for value in ("../outside", "/absolute", "C:/drive", "a//b", "a/./b", "a\\b", "https://host", "a\x00b"):
            with self.subTest(value=value), self.assertRaises(m.IntegrityError):
                m.relative_path(value)

    def test_symlink_read_rejected(self):
        (self.root / "file").write_text("fixture")
        (self.root / "link").symlink_to("file")
        with self.assertRaises(m.IntegrityError):
            m.confined(self.root, "link", must_exist=True)

    def test_new_output_cannot_replace_existing_file(self):
        path = self.root / "output"
        m.write_new(path, b"first")
        with self.assertRaises(m.IntegrityError):
            m.write_new(path, b"second")
        self.assertEqual(b"first", path.read_bytes())

    def test_source_file_drift_fails(self):
        root, marker = self.fixture()
        (root / "build.gradle").write_text("// changed input\n")
        with self.assertRaises(m.IntegrityError):
            driver.check_source(root, marker)

    def test_new_source_file_is_not_silently_omitted(self):
        root, marker = self.fixture()
        (root / "unexpected.gradle").write_text("// new input\n")
        with self.assertRaises(m.IntegrityError):
            driver.check_source(root, marker)

    def test_gradle_candidate_state_is_separate_from_immutable_source(self):
        root, marker = self.fixture()
        path = root / m.lock_path(".", marker["host"])
        path.parent.mkdir(parents=True)
        path.write_text("empty=fixtureClasspath\n")
        state = driver.check_source(root, marker)
        self.assertIn(path.relative_to(root).as_posix(), state)

    def test_reservation_does_not_break_existing_owner_lock(self):
        root, _ = self.fixture()
        with driver.exclusive_workspace(root, "first"):
            with self.assertRaises(m.IntegrityError):
                with driver.exclusive_workspace(root, "second"):
                    self.fail("second owner entered")
            self.assertTrue((root / ".nativecmpkit-dependency-active.json").exists())
        self.assertFalse((root / ".nativecmpkit-dependency-active.json").exists())

    def test_live_git_checkout_is_rejected_before_any_reservation_write(self):
        root, _ = self.fixture()
        (root / ".git").mkdir()
        with self.assertRaises(m.IntegrityError):
            driver.run(root, entry_root=".", run_id="forbidden", mode="bootstrap")
        self.assertFalse((root / ".nativecmpkit-dependency-active.json").exists())

    def test_fixture_marker_cannot_claim_independent_trust(self):
        root, marker = self.fixture()
        marker["independent_trust_reviewed"] = True
        (root / driver.MARKER).write_bytes(m.json_bytes(marker))
        with self.assertRaises(m.IntegrityError):
            driver.load_workspace(root)

    def mini_source(self):
        source = self.root / "source"
        source.mkdir()
        contents = {
            "settings.gradle.kts": 'pluginManagement { includeBuild("convention-plugins") }\ninclude(\n":calf-one",\n":sample:app",\n)\n',
            "build.gradle.kts": "// offline snapshot fixture\n", "gradlew": "NOT EXECUTED\n",
            "gradle/wrapper/gradle-wrapper.properties": "distributionUrl=fixture-only\n",
            "convention-plugins/settings.gradle.kts": 'rootProject.name = "convention-plugins"\n',
            "convention-plugins/build.gradle.kts": "// fixture\n", "calf-one/build.gradle.kts": "// fixture\n",
            "sample/app/build.gradle.kts": "// fixture\n", "scripts/dependencies/resolve-graphs.init.gradle": "// fixture\n",
            "scripts/dependencies/integrity.py": "# fixture\n", "local.properties": "DO_NOT_COPY=fixture-secret\n",
            "calf-one/key.properties": "DO_NOT_COPY=fixture-secret\n",
        }
        for name, data in contents.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
        (source / "calf-one/src/androidDeviceTest").mkdir(parents=True)
        return source

    def test_snapshot_copies_dirty_inputs_not_head_and_preserves_empty_device_topology(self):
        source = self.mini_source()
        destination = self.root / "copy"
        responses = [subprocess.CompletedProcess([], 0, "1" * 40 + "\n", ""),
                     subprocess.CompletedProcess([], 0, " M build.gradle.kts\n", "")]
        with mock.patch.object(driver.subprocess, "run", side_effect=responses) as command:
            result = driver.snapshot(source, destination)
        self.assertEqual(2, command.call_count)
        self.assertTrue(result["source_tree_dirty"])
        self.assertFalse(result["gradle_executed"])
        self.assertTrue((destination / "calf-one/src/androidDeviceTest").is_dir())
        self.assertFalse((destination / "local.properties").exists())
        self.assertFalse((destination / "calf-one/key.properties").exists())
        marker = driver.load_workspace(destination)
        self.assertIn(":sample", marker["expected_projects"]["."])
        self.assertIn("calf-one/src/androidDeviceTest", marker["source_directories"])

    def test_empty_source_directory_topology_drift_fails(self):
        source = self.mini_source()
        files, _, topology, _ = driver.selected_inputs(source, "source-snapshot")
        marker = {"kind": "source-snapshot", "source_files": files, "source_directories": topology,
                  "source_input_digest": driver.source_digest(files, topology)}
        (source / "calf-one/src/androidDeviceTest").rmdir()
        with self.assertRaises(m.IntegrityError):
            driver.check_source(source, marker)

    def test_snapshot_copies_both_stored_yarn_locks_as_immutable_source(self):
        source = self.mini_source()
        expected = {"kotlin-js-store/yarn.lock": b"# synthetic JS lock\n", "kotlin-js-store/wasm/yarn.lock": b"# synthetic Wasm lock\n"}
        for name, data in expected.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        destination = self.root / "copy"
        responses = [subprocess.CompletedProcess([], 0, "1" * 40 + "\n", ""), subprocess.CompletedProcess([], 0, "", "")]
        with mock.patch.object(driver.subprocess, "run", side_effect=responses):
            driver.snapshot(source, destination)
        marker = driver.load_workspace(destination)
        for name, data in expected.items():
            self.assertEqual(data, (destination / name).read_bytes())
            self.assertEqual(m.sha256_bytes(data), marker["source_files"][name])
            self.assertNotIn(name, marker["initial_integrity_files"])

    def test_new_stored_yarn_lock_is_detected_as_source_drift(self):
        source = self.mini_source()
        files, _, topology, _ = driver.selected_inputs(source, "source-snapshot")
        marker = {"kind": "source-snapshot", "source_files": files, "source_directories": topology,
                  "source_input_digest": driver.source_digest(files, topology)}
        path = source / "kotlin-js-store/yarn.lock"
        path.parent.mkdir()
        path.write_bytes(b"# synthetic lock added after snapshot\n")
        with self.assertRaises(m.IntegrityError):
            driver.check_source(source, marker)

    def test_changed_stored_wasm_yarn_lock_is_detected_as_source_drift(self):
        source = self.mini_source()
        path = source / "kotlin-js-store/wasm/yarn.lock"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"# synthetic frozen lock\n")
        files, _, topology, _ = driver.selected_inputs(source, "source-snapshot")
        marker = {"kind": "source-snapshot", "source_files": files, "source_directories": topology,
                  "source_input_digest": driver.source_digest(files, topology)}
        path.write_bytes(b"# changed lock\n")
        with self.assertRaises(m.IntegrityError):
            driver.check_source(source, marker)

    def test_stored_yarn_selection_still_excludes_private_files_and_node_modules(self):
        source = self.mini_source()
        for name in ("kotlin-js-store/.npmrc", "kotlin-js-store/node_modules/fixture.txt"):
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"DO_NOT_COPY synthetic private/cache input\n")
        files, _, _, _ = driver.selected_inputs(source, "source-snapshot")
        self.assertFalse(any(name.startswith("kotlin-js-store/") for name in files))

    def test_computed_include_requires_deliberate_update(self):
        source = self.mini_source()
        with (source / "settings.gradle.kts").open("a") as stream:
            stream.write('include(\nlistOf(":hidden")\n)\n')
        with self.assertRaises(m.IntegrityError):
            driver.expected_source_projects(source)


class CommandAndReviewTests(TemporaryCase):
    def command(self, mode="check", **kwargs):
        root, marker = self.fixture()
        return driver.build_command(root, marker, entry_root=".", run_id="offline-construction", mode=mode,
                                    gradle_home=self.installed_gradle_stub(), **kwargs)

    def test_check_command_has_strict_verification_and_no_writers(self):
        command = self.command()
        self.assertIn("strict", command)
        self.assertIn("--no-configuration-cache", command)
        self.assertIn("--max-workers=1", command)
        self.assertNotIn("--write-locks", command)
        self.assertNotIn("--write-verification-metadata", command)
        self.assertFalse(any("publish" in value.lower() or value == "--scan" for value in command))

    def test_bootstrap_requires_both_explicit_writers(self):
        command = self.command("bootstrap")
        self.assertIn("--write-locks", command)
        self.assertEqual("sha256", command[command.index("--write-verification-metadata") + 1])

    def test_unrecognized_mode_is_not_a_bootstrap_alias(self):
        with self.assertRaises(m.IntegrityError):
            self.command("lenient")

    def test_offline_bootstrap_is_not_allowed(self):
        with self.assertRaises(m.IntegrityError):
            self.command("bootstrap", offline=True)

    def test_installed_distribution_override_is_fixture_only(self):
        root, marker = self.fixture()
        marker["kind"] = "source-snapshot"
        with self.assertRaises(m.IntegrityError):
            driver.build_command(root, marker, entry_root=".", run_id="test", mode="check", gradle_home=self.installed_gradle_stub())

    def test_check_requires_an_explicit_matching_review(self):
        root, marker = self.fixture()
        state = driver.check_source(root, marker)
        with self.assertRaises(m.IntegrityError):
            driver.check_review(root, marker, ".", state)
        fixtures.controlled_review(root, marker)
        review = driver.check_review(root, marker, ".", state)
        self.assertEqual("controlled-fixture", review["trust_level"])

    def test_review_does_not_allow_a_later_checksum_change(self):
        root, marker = self.fixture()
        fixtures.controlled_review(root, marker)
        entries = fixtures.known_metadata()
        entries[next(iter(entries))] = "0" * 64
        (root / "gradle/verification-metadata.xml").write_bytes(m.metadata_bytes(entries))
        with self.assertRaises(m.IntegrityError):
            driver.check_review(root, marker, ".", driver.check_source(root, marker))

    def test_source_review_requires_actual_complete_acquisition(self):
        root, _ = self.fixture()
        with self.assertRaises(m.IntegrityError):
            driver.review(root, entry_root=".", run_ids=["not-executed"], acknowledge_tofu=True)

    def test_environment_omits_credential_and_jvm_override_variables(self):
        root, _ = self.fixture()
        java = self.root / "jdk"
        (java / "bin").mkdir(parents=True)
        (java / "bin/java").write_text("NOT EXECUTED")
        with mock.patch.dict(os.environ, {"JAVA_HOME": str(java), "JAVA_TOOL_OPTIONS": "-Dverification=off",
                                          "GRADLE_OPTS": "sensitive fixture", "ORG_GRADLE_PROJECT_token": "secret fixture"}):
            environment = driver._environment(root, fresh=True)
        for name in ("GRADLE_OPTS", "ORG_GRADLE_PROJECT_token"):
            self.assertNotIn(name, environment)
        self.assertNotIn("verification=off", environment["JAVA_TOOL_OPTIONS"])
        self.assertIn(f'-Duser.home="{root / ".dependency-home"}"', environment["JAVA_TOOL_OPTIONS"])
        self.assertEqual(str(root / ".dependency-cache"), environment["GRADLE_USER_HOME"])

    def test_fresh_cache_requirement_rejects_reuse(self):
        root, _ = self.fixture()
        java = self.root / "jdk"
        (java / "bin").mkdir(parents=True)
        (java / "bin/java").write_text("NOT EXECUTED")
        with mock.patch.dict(os.environ, {"JAVA_HOME": str(java)}):
            driver._environment(root, fresh=True)
            with self.assertRaises(m.IntegrityError):
                driver._environment(root, fresh=True)

    def test_all_explicit_vm_and_native_cache_locations_are_candidate_local(self):
        root, _ = self.fixture()
        java = self.root / "jdk"
        (java / "bin").mkdir(parents=True)
        (java / "bin/java").write_text("NOT EXECUTED")
        with mock.patch.dict(os.environ, {"JAVA_HOME": str(java), "KONAN_DATA_DIR": "/unrelated/konan",
                                         "XDG_CACHE_HOME": "/unrelated/cache", "TMPDIR": "/unrelated/tmp",
                                         "JAVA_OPTS": "not allowed", "_JAVA_OPTIONS": "not allowed", "JDK_JAVA_OPTIONS": "not allowed"}):
            environment = driver._environment(root)
        for key, path in m.ENV_PRIVATE_PATHS.items():
            self.assertEqual(str(root / path), environment[key])
            self.assertTrue((root / path).is_dir())
        self.assertEqual(" ".join(f'-D{key}="{root / value}"' for key, value in m.JVM_PRIVATE_PATHS.items()), environment["JAVA_TOOL_OPTIONS"])
        for key in ("JAVA_OPTS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS"):
            self.assertNotIn(key, environment)

    def test_exact_generated_vm_options_quote_paths_with_spaces(self):
        root, _ = self.fixture("candidate with spaces")
        java = self.root / "jdk"
        (java / "bin").mkdir(parents=True)
        (java / "bin/java").write_text("NOT EXECUTED")
        with mock.patch.dict(os.environ, {"JAVA_HOME": str(java)}):
            environment = driver._environment(root)
        self.assertIn(f'-Duser.home="{root}/.dependency-home"', environment["JAVA_TOOL_OPTIONS"])

    def test_vm_option_injection_path_is_rejected_before_directory_creation(self):
        root, _ = self.fixture('candidate" -Dunrelated=true "')
        java = self.root / "jdk"
        (java / "bin").mkdir(parents=True)
        (java / "bin/java").write_text("NOT EXECUTED")
        with mock.patch.dict(os.environ, {"JAVA_HOME": str(java)}), self.assertRaises(m.IntegrityError):
            driver._environment(root)
        self.assertFalse((root / ".dependency-home").exists())

    def test_symlinked_native_cache_location_is_rejected(self):
        root, _ = self.fixture()
        java = self.root / "jdk"
        (java / "bin").mkdir(parents=True)
        (java / "bin/java").write_text("NOT EXECUTED")
        (root / ".dependency-home").mkdir()
        (root / ".dependency-home/konan").symlink_to(self.root, target_is_directory=True)
        with mock.patch.dict(os.environ, {"JAVA_HOME": str(java)}), self.assertRaises(m.IntegrityError):
            driver._environment(root)

    def test_failed_launch_identity_record_still_cleans_up_own_process(self):
        process = mock.Mock(pid=2345)
        process.poll.return_value = None
        with mock.patch.object(driver.shutil, "disk_usage", return_value=mock.Mock(free=20 * 1024 ** 3)), \
                mock.patch.object(driver.subprocess, "Popen", return_value=process), \
                mock.patch.object(m, "write_new", side_effect=m.IntegrityError("synthetic receipt collision")), \
                mock.patch.object(driver.os, "killpg") as kill, self.assertRaises(m.IntegrityError):
            driver._bounded(["NOT EXECUTED"], workspace=self.root, environment={}, log=self.root / "process.log", timeout=90, reserve_mib=8192)
        kill.assert_called_once_with(2345, driver.signal.SIGTERM)
        process.wait.assert_called_once_with(timeout=10)


class GraphReceiptTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.workspace, self.marker = self.fixture()
        lock = self.workspace / m.lock_path(".", self.marker["host"])
        lock.parent.mkdir(parents=True)
        lock.write_text(f"{fixtures.GROUP}:parent:1.0=fixtureClasspath\n{fixtures.GROUP}:leaf:1.0=fixtureClasspath\nempty=\n")
        inventory = {"scope": "project", "name": "fixtureClasspath", "can_resolve": True,
                     "can_consume": False, "can_declare": True, "extends_from": [], "attributes": {}}
        components = [{"kind": "project", "id": "project::", "project_path": ":", "build_tree_path": ":"}]
        for module in ("parent", "leaf"):
            components.append({"kind": "module", "id": f"module:{fixtures.GROUP}:{module}:1.0", "group": fixtures.GROUP,
                               "module": module, "version": "1.0", "changing": False, "changing_evidence": m.CHANGING_EVIDENCE})
        artifact = {"group": fixtures.GROUP, "module": "leaf", "version": "1.0", "name": "leaf-1.0.jar",
                    "sha256": m.sha256_bytes(fixtures.jar_bytes("leaf", "1.0")), "size": len(fixtures.jar_bytes("leaf", "1.0")),
                    "provenance": "artifact-view-output-unclassified", "variant_attributes": {}, "content_kind": "regular-file"}
        configuration = {"scope": "project", "name": "fixtureClasspath", "inventory": inventory,
                         "status": "resolved", "root_component_id": "project::", "components": components,
                         "edges": [], "artifacts": [artifact],
                         "unresolved": [], "failures": [], "lock_coverage": "strict-project-init-script"}
        self.record = {"schema_version": 1, "record_type": "project-graph", "run_id": "synthetic",
                       "mode": "check", "host": self.marker["host"], "source_input_digest": self.marker["source_input_digest"],
                       "build_root": ".", "project_path": ":", "project_directory": ".", "gradle_version": "9.7.1", "java_major": 17,
                       "runtime_isolation": copy.deepcopy(m.RUNTIME_ISOLATION),
                       "inventory": [inventory], "configurations": [configuration], "inventory_drift": [], "failures": [], "complete": True,
                       "policy": {"project_lock_mode": "STRICT", "project_lock_activation": "init-script-lockAllConfigurations",
                                  "lock_file": m.lock_path(".", self.marker["host"]), "dependency_verification_mode": "strict",
                                  "ignored_dependencies": [], "changing_versions_policy": m.CHANGING_POLICY}}

    def validate(self, record=None):
        return m.validate_project_record(record or self.record, run_id="synthetic", mode="check", host=self.marker["host"],
                                         digest=self.marker["source_input_digest"], build_root=".", workspace=self.workspace, verify_locks=True)

    def test_complete_synthetic_owner_record_parses(self):
        result = self.validate()
        self.assertEqual(1, result["resolved_configurations"])
        self.assertEqual(1, result["artifact_view_outputs"])

    def test_missing_actual_gradle_jvm_cache_observation_is_not_complete(self):
        del self.record["runtime_isolation"]
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_foreign_jvm_home_cannot_be_accepted_from_private_home_environment(self):
        self.record["runtime_isolation"]["properties"]["user.home"] = "unrelated-home"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_foreign_konan_cache_environment_is_not_private_runtime_evidence(self):
        self.record["runtime_isolation"]["environment"]["KONAN_DATA_DIR"] = "unrelated-konan"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_gradle_jvm_observation_cannot_claim_actual_other_cache_usage(self):
        self.record["runtime_isolation"]["non_gradle_cache_use_verified"] = True
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_gradle_jvm_observation_cannot_certify_wrapper_client(self):
        self.record["runtime_isolation"]["wrapper_client_observed"] = True
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_stale_invocation_record_fails(self):
        self.record["run_id"] = "prior-run"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_foreign_host_record_fails(self):
        self.record["host"] = "other-host"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_configuration_omission_fails(self):
        self.record["configurations"] = []
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_duplicate_configuration_fails(self):
        self.record["configurations"] *= 2
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_unresolved_dependency_is_never_empty_success(self):
        self.record["configurations"][0]["unresolved"] = [{"requested": "missing:module:1.0"}]
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_artifact_failure_fails_aggregate(self):
        self.record["configurations"][0]["failures"] = [{"phase": "artifact-read", "types": ["FixtureException"]}]
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_inventory_drift_fails(self):
        self.record["inventory_drift"] = [{"name": "lateConfiguration"}]
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_unclassified_artifact_cannot_be_called_registry_original(self):
        self.record["configurations"][0]["artifacts"][0]["provenance"] = "registry-original"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_script_provider_cannot_inherit_project_strict_claim(self):
        self.record["inventory"][0]["scope"] = "buildscript"
        self.record["configurations"][0]["scope"] = "buildscript"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_script_graph_explicitly_records_lock_gap(self):
        self.record["inventory"][0]["scope"] = "buildscript"
        self.record["configurations"][0]["scope"] = "buildscript"
        self.record["configurations"][0]["lock_coverage"] = "not-covered-buildscript"
        self.assertIsNone(self.validate()["lock_file"])

    def script_root(self):
        source = self.record["inventory"][0]
        source["scope"] = "buildscript"
        item = self.record["configurations"][0]
        item.update(scope="buildscript", status="empty-resolved", lock_coverage="not-covered-buildscript", artifacts=[], edges=[])
        component = {"kind": "script-root", "id": "script-root:::fixtureClasspath", "scope": "buildscript",
                     "project_path": ":", "configuration": "fixtureClasspath",
                     "identity_basis": "public-RootComponentIdentifier-matched-to-resolution-root"}
        item.update(components=[component], root_component_id=component["id"])
        return item, component

    def test_exact_public_script_root_is_an_empty_graph_not_external_module(self):
        self.script_root()
        result = self.validate()
        self.assertEqual([], result["external_modules"])
        self.assertEqual(0, result["artifact_view_outputs"])
        self.assertIsNone(result["lock_file"])

    def test_script_root_with_external_edges_still_acquires_modules(self):
        modules = copy.deepcopy(self.record["configurations"][0]["components"][1:])
        artifacts = copy.deepcopy(self.record["configurations"][0]["artifacts"])
        item, root = self.script_root()
        item["components"].extend(modules)
        item.update(status="resolved", artifacts=artifacts,
                    edges=[{"from": root["id"], "selected": module["id"], "requested": module["module"], "constraint": False}
                           for module in modules])
        self.assertEqual(2, len(self.validate()["external_modules"]))

    def test_script_root_cannot_be_used_for_project_configuration(self):
        item, root = self.script_root()
        item["scope"] = self.record["inventory"][0]["scope"] = "project"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_script_root_cannot_replace_an_unknown_external_node(self):
        item, root = self.script_root()
        item["components"].append({"kind": "opaque", "id": "unknown-external-node"})
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_script_root_requires_exact_owner_configuration_and_root_basis(self):
        for key, value in (("project_path", ":other"), ("configuration", "other"),
                           ("identity_basis", "guessed-unknown-root"), ("module", "hidden-external")):
            with self.subTest(key=key):
                item, root = self.script_root()
                root[key] = value
                with self.assertRaises(m.IntegrityError):
                    self.validate()

    def test_script_root_cannot_be_a_selected_dependency_target(self):
        item, root = self.script_root()
        item["edges"] = [{"from": root["id"], "selected": root["id"], "requested": "not-an-external-dependency", "constraint": False}]
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_script_root_cannot_be_an_unmatched_additional_root(self):
        item, root = self.script_root()
        item["components"].append({"kind": "project", "id": "project::"})
        item["root_component_id"] = "project::"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_missing_resolution_root_is_not_a_complete_graph(self):
        del self.record["configurations"][0]["root_component_id"]
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_owner_must_explicitly_report_complete(self):
        self.record["complete"] = False
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_ignored_dependency_bypass_fails(self):
        self.record["policy"]["ignored_dependencies"] = ["org.example:*"]
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_host_fallback_lock_path_fails(self):
        self.record["policy"]["lock_file"] = "gradle.lockfile"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_changed_external_module_is_rejected(self):
        self.record["configurations"][0]["components"][1]["changing"] = True
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_obsolete_changing_policy_is_rejected(self):
        self.record["policy"]["changing_versions_policy"] = "failOnChangingVersions"
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_changing_guard_basis_cannot_be_omitted(self):
        del self.record["configurations"][0]["components"][1]["changing_evidence"]
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def write_graph(self):
        part = f"build/dependency-integrity/synthetic/graphs/root/parts/{m.part_key(':')}.json"
        m.write_new(m.confined(self.workspace, part), m.json_bytes(self.record))
        graph = {"schema_version": 1, "record_type": "build-graph", "run_id": "synthetic", "mode": "check",
                 "build_root": ".", "host": self.marker["host"], "source_input_digest": self.marker["source_input_digest"],
                 "gradle_version": "9.7.1", "java_major": 17, "complete": True, "parts": [{"project_path": ":", "file": part}],
                 "included_builds": [], "ordinary_build_policy_installed": False, "independent_trust_reviewed": False,
                 "scheduled_tasks": [{"build_root": ".", "project": ":", "task": name} for name in
                                     ("nativeCmpkitDependencyGraphPart", "nativeCmpkitDependencyGraph")],
                 "settings_script_graph_acquired": False, "detached_graph_inventory_complete": False}
        path = m.confined(self.workspace, driver._graph_file("synthetic", "."))
        m.write_new(path, m.json_bytes(graph))
        return path, graph

    def test_complete_synthetic_graph_matches_independent_project_inventory(self):
        self.write_graph()
        result = driver.validate_graph_tree(self.workspace, self.marker, run_id="synthetic", mode="check", entry_root=".")
        self.assertEqual(1, result["projects"])

    def test_omitted_settings_declared_owner_fails(self):
        self.write_graph()
        self.marker["expected_projects"]["."][":omitted"] = "omitted"
        with self.assertRaises(m.IntegrityError):
            driver.validate_graph_tree(self.workspace, self.marker, run_id="synthetic", mode="check", entry_root=".")

    def test_missing_included_build_fails(self):
        self.write_graph()
        self.marker["build_roots"].append("included")
        with self.assertRaises(m.IntegrityError):
            driver.validate_graph_tree(self.workspace, self.marker, run_id="synthetic", mode="check", entry_root=".")

    def test_false_whole_build_trust_claim_fails(self):
        path, graph = self.write_graph()
        graph["independent_trust_reviewed"] = True
        path.write_bytes(m.json_bytes(graph))
        with self.assertRaises(m.IntegrityError):
            driver.validate_graph_tree(self.workspace, self.marker, run_id="synthetic", mode="check", entry_root=".")

    def test_tampered_directory_artifact_manifest_fails(self):
        artifact = self.record["configurations"][0]["artifacts"][0]
        artifact.update(content_kind="directory-tree", size=0, files=[], sha256="0" * 64)
        with self.assertRaises(m.IntegrityError):
            self.validate()

    def test_missing_scheduled_task_inventory_fails(self):
        with self.assertRaises(m.IntegrityError):
            driver.validate_scheduled_tasks(None, self.marker, ".")

    def test_forbidden_scheduled_source_task_fails(self):
        _, graph = self.write_graph()
        graph["scheduled_tasks"].append({"build_root": ".", "project": ":", "task": "compileKotlin"})
        with self.assertRaises(m.IntegrityError):
            driver.validate_scheduled_tasks(graph["scheduled_tasks"], self.marker, ".")

    def test_duplicate_scheduled_task_fails(self):
        _, graph = self.write_graph()
        with self.assertRaises(m.IntegrityError):
            driver.validate_scheduled_tasks(graph["scheduled_tasks"] * 2, self.marker, ".")

    def test_missing_required_owner_task_fails(self):
        _, graph = self.write_graph()
        with self.assertRaises(m.IntegrityError):
            driver.validate_scheduled_tasks(graph["scheduled_tasks"][1:], self.marker, ".")

    def test_convention_compile_allowed_but_publish_still_forbidden(self):
        _, graph = self.write_graph()
        self.marker["kind"] = "source-snapshot"
        self.marker["expected_projects"]["convention-plugins"] = {":": "convention-plugins"}
        tasks = graph["scheduled_tasks"] + [{"build_root": "convention-plugins", "project": ":", "task": "compileKotlin"}]
        driver.validate_scheduled_tasks(tasks, self.marker, ".")
        tasks[-1]["task"] = "publishToMavenLocal"
        with self.assertRaises(m.IntegrityError):
            driver.validate_scheduled_tasks(tasks, self.marker, ".")


class ExactLockClassifierTests(TemporaryCase):
    """Synthetic full receipts, not newly executed Gradle missing/add/remove outcomes.

    Real classify/failure_evidence/file parsing is used without mocking Gradle
    output. The exception templates were read from installed9.7.1 class bytes;
    Actual004's missing-host error pair is reproduced explicitly below. A fresh
    corrected suite and the other three producer paths still need scheduled runs.
    """

    def lock_fixture(self, case):
        baseline, _ = self.fixture(case + "-base")
        lock = baseline / m.lock_path(".", m.host_key())
        lock.parent.mkdir(parents=True)
        lock.write_text(f"{fixtures.GROUP}:leaf:1.0=fixtureClasspath\n{fixtures.GROUP}:parent:1.0=fixtureClasspath\nempty=\n")
        root, marker = self.fixture(case, case=case, base_state=baseline)
        configuration = "newUnrecordedClasspath" if case == "missing-configuration-lock" else "fixtureClasspath"

        def descriptor(scope, name):
            return {"scope": scope, "name": name, "can_resolve": True}

        def project(name, modules):
            return {"scope": "project", "name": name, "inventory": descriptor("project", name), "status": "resolved",
                    "root_component_id": "project::", "lock_coverage": "strict-project-init-script",
                    "components": [{"kind": "project", "id": "project::", "project_path": ":"}] +
                                  [{"kind": "module", "id": f"module:{fixtures.GROUP}:{module}:1.0",
                                    "group": fixtures.GROUP, "module": module, "version": "1.0"} for module in modules],
                    "edges": [], "unresolved": [], "artifacts": [], "failures": []}

        script = {"scope": "buildscript", "name": "classpath", "inventory": descriptor("buildscript", "classpath"),
                  "status": "empty-resolved", "root_component_id": "script-root:::classpath", "components": [],
                  "edges": [], "unresolved": [], "artifacts": [], "failures": []}
        target = project(configuration, ("parent", "leaf", "extra") if case == "added-dependency" else ("parent",))
        target["status"] = "failed"
        if case.startswith("missing-"):
            target["components"] = []
            target["root_component_id"] = None
            target["failures"] = [{"phase": "configuration-resolution", "types": [fixtures.MISSING_LOCK_STATE],
                                   "fixture_messages": [f"Locking strict mode: Configuration ':{configuration}' is locked but does not have lock state."]}]
        else:
            module = f"{fixtures.GROUP}:extra:1.0" if case == "added-dependency" else f"{fixtures.GROUP}:leaf:1.0"
            message = (f"Resolved '{module}' which is not part of the dependency lock state" if case == "added-dependency" else
                       f"Did not resolve '{module}' which is part of the dependency lock state")
            target["failures"] = [{"phase": "artifact-resolution", "types": [fixtures.LOCK_OUT_OF_DATE], "fixture_messages": [message]}]
            target["edges"] = [{"from": "project::", "requested": f"{fixtures.GROUP}:parent:1.0", "constraint": False,
                                "selected": f"module:{fixtures.GROUP}:parent:1.0"}]
            if case == "added-dependency":
                target["edges"] += [{"from": "project::", "requested": module, "constraint": False, "selected": "module:" + module},
                                    {"from": f"module:{fixtures.GROUP}:parent:1.0", "requested": f"{fixtures.GROUP}:leaf:[1.0,2.0)",
                                     "constraint": False, "selected": f"module:{fixtures.GROUP}:leaf:1.0"}]
        configurations = [script, target]
        if case == "missing-configuration-lock":
            configurations.append(project("fixtureClasspath", ("parent", "leaf")))
        owner = {"schema_version": 1, "record_type": "project-graph", "run_id": "check", "mode": "check",
                 "gradle_version": m.GRADLE_VERSION, "java_major": 17, "host": marker["host"],
                 "source_input_digest": marker["source_input_digest"], "build_root": ".", "project_path": ":", "project_directory": ".",
                 "complete": False, "failures": [], "inventory_drift": [], "configurations": configurations,
                 "inventory": [copy.deepcopy(item["inventory"]) for item in configurations],
                 "policy": {"project_lock_mode": "STRICT", "lock_file": m.lock_path(".", marker["host"]),
                            "ignored_dependencies": [], "dependency_verification_mode": "strict"},
                 "test_only": "Synthetic offline parser fixture; no Gradle was run"}
        output = root / "build/dependency-integrity/check"
        (output / "graphs/root/parts").mkdir(parents=True)
        state = driver.check_source(root, marker)
        result = {"record_type": "dependency-invocation", "run_id": "check", "mode": "check", "host": marker["host"],
                  "source_input_digest": marker["source_input_digest"], "integrity_before": state, "integrity_after": state,
                  "execution": {"exit_code": 1}, "test_only": "Synthetic exit for offline parser test, not an executed process"}
        return root, marker, target, owner, result

    def observe(self, case, root, owner, result):
        output = root / "build/dependency-integrity/check"
        (output / "graphs/root/parts/offline-synthetic.json").write_bytes(m.json_bytes(owner))
        (output / "result.json").write_bytes(m.json_bytes(result))
        return fixtures.classify(root, case, result)

    def refresh_integrity(self, root, marker, result):
        result["integrity_before"] = result["integrity_after"] = driver.check_source(root, marker)

    def assert_unverified(self, observed):
        self.assertFalse(observed["actual_expected_result_observed"])
        self.assertEqual("unverified", observed["result_kind"])

    def assert_io_phrase_rejected(self, case):
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"] = [{"phase": "configuration-resolution", "types": ["java.io.IOException"],
                               "fixture_messages": ["Could not read lock state diagnostic: unrelated I/O failure"]}]
        observed = self.observe(case, root, owner, result)
        self.assertTrue(observed["source_and_integrity_identity_unchanged"])
        self.assertEqual(["java.io.IOException"], observed["failure_types"])
        self.assert_unverified(observed)

    def test_missing_host_lock_does_not_accept_unrelated_io_lock_phrase(self):
        self.assert_io_phrase_rejected("missing-host-lock")

    def test_missing_configuration_lock_does_not_accept_unrelated_io_lock_phrase(self):
        self.assert_io_phrase_rejected("missing-configuration-lock")

    def test_added_dependency_does_not_accept_unrelated_io_lock_phrase(self):
        self.assert_io_phrase_rejected("added-dependency")

    def test_removed_dependency_does_not_accept_unrelated_io_lock_phrase(self):
        self.assert_io_phrase_rejected("removed-dependency")

    def test_exact_typed_synthetic_case_shapes_match_only_their_discrepancy(self):
        for case in fixtures.LOCK_CASE_BUILDS:
            with self.subTest(case=case):
                root, _, _, owner, result = self.lock_fixture(case)
                observed = self.observe(case, root, owner, result)
                self.assertTrue(observed["actual_expected_result_observed"])
                self.assertEqual("exact-lock-state-rejection", observed["result_kind"])
                self.assertEqual(7, observed["lock_evidence"]["known_repository_files_confirmed"])

    def actual004_missing_host_fixture(self):
        root, marker, target, owner, result = self.lock_fixture("missing-host-lock")
        # Exact pair from fixture004's preserved project-e7ac0786668e0ff0f02b62bd
        # owner receipt, replayed with a synthetic invocation in this offline test.
        target["failures"] = [{
            "phase": "configuration-resolution",
            "types": ["org.gradle.api.internal.artifacts.ivyservice.TypedResolveException",
                      "org.gradle.internal.locking.MissingLockStateException"],
            "fixture_messages": ["Could not resolve all dependencies for configuration ':fixtureClasspath'.",
                                 "Locking strict mode: Configuration ':fixtureClasspath' is locked but does not have lock state."],
        }]
        return root, marker, target, owner, result

    def test_actual004_paired_typed_resolve_missing_host_error_is_supported(self):
        root, _, _, owner, result = self.actual004_missing_host_fixture()
        observed = self.observe("missing-host-lock", root, owner, result)
        self.assertTrue(observed["actual_expected_result_observed"])
        self.assertEqual("exact-lock-state-rejection", observed["result_kind"])
        self.assertEqual("absent-actual-host-lock-file", observed["lock_evidence"]["lock_discrepancy"])

    def test_actual004_wrapper_rejects_wrong_or_unobserved_message_context(self):
        root, _, target, owner, result = self.actual004_missing_host_fixture()
        for message in ("Could not resolve all dependencies for configuration ':otherClasspath'.",
                        "Could not resolve all dependencies for configuration ':classpath'.",
                        "Could not resolve all files for configuration ':fixtureClasspath'.",
                        "Could not resolve all artifacts for configuration ':fixtureClasspath'.",
                        "Unrelated I/O error reading lock state"):
            with self.subTest(message=message):
                target["failures"][0]["fixture_messages"][0] = message
                self.assert_unverified(self.observe("missing-host-lock", root, owner, result))

    def test_actual004_wrapper_rejects_lookalike_or_unknown_subclass(self):
        root, _, target, owner, result = self.actual004_missing_host_fixture()
        for kind in ("unrelated.example.TypedResolveException", "java.io.IOException",
                     "org.gradle.api.internal.artifacts.ivyservice.OtherResolveException"):
            with self.subTest(kind=kind):
                target["failures"][0]["types"][0] = kind
                self.assert_unverified(self.observe("missing-host-lock", root, owner, result))

    def test_actual004_wrapper_rejects_extra_duplicate_or_unpaired_causes(self):
        root, _, target, owner, result = self.actual004_missing_host_fixture()
        original = copy.deepcopy(target["failures"][0])
        for mutation in ("unknown-prefix", "unknown-suffix", "duplicate-wrapper", "reversed-pair", "missing-message"):
            with self.subTest(mutation=mutation):
                error = copy.deepcopy(original)
                if mutation == "unknown-prefix":
                    error["types"].insert(0, "java.io.IOException")
                    error["fixture_messages"].insert(0, "unrelated I/O failure")
                elif mutation == "unknown-suffix":
                    error["types"].append("java.io.IOException")
                    error["fixture_messages"].append("unrelated I/O failure")
                elif mutation == "duplicate-wrapper":
                    error["types"].insert(0, error["types"][0])
                    error["fixture_messages"].insert(0, error["fixture_messages"][0])
                elif mutation == "reversed-pair":
                    error["fixture_messages"].reverse()
                else:
                    error["fixture_messages"].pop()
                target["failures"] = [error]
                self.assert_unverified(self.observe("missing-host-lock", root, owner, result))

    def test_actual004_wrapper_cannot_mask_unrelated_owner_or_configuration_error(self):
        root, _, _, owner, result = self.actual004_missing_host_fixture()
        unrelated = {"types": ["java.io.IOException"], "fixture_messages": ["unrelated I/O failure"]}
        for location in ("owner", "configuration"):
            with self.subTest(location=location):
                selected = owner if location == "owner" else owner["configurations"][0]
                selected["failures"] = [unrelated]
                self.assert_unverified(self.observe("missing-host-lock", root, owner, result))
                selected["failures"] = []

    def test_actual004_wrapper_cannot_replace_missing_host_state_proof(self):
        root, marker, _, owner, result = self.actual004_missing_host_fixture()
        (root / m.lock_path(".", marker["host"])).write_text("empty=fixtureClasspath\n")
        self.refresh_integrity(root, marker, result)
        self.assert_unverified(self.observe("missing-host-lock", root, owner, result))

    def test_actual004_wrapper_cannot_mask_timeout_or_checksum_failure(self):
        root, _, _, owner, result = self.actual004_missing_host_fixture()
        result["execution"]["reason"] = "timeout"
        self.assert_unverified(self.observe("missing-host-lock", root, owner, result))
        del result["execution"]["reason"]
        (root / "build/dependency-integrity/check/gradle.log").write_text("Dependency verification failed for artifact\n")
        self.assert_unverified(self.observe("missing-host-lock", root, owner, result))

    def actual005_added_dependency_fixture(self):
        root, marker, target, owner, result = self.lock_fixture("added-dependency")
        # The exact unresolved lock-origin edge/cause in the preserved actual005
        # owner receipt. This invocation remains synthetic: no Gradle is run.
        target["unresolved"] = [{
            "from": "project::", "requested": f"{fixtures.GROUP}:extra:1.0", "constraint": True,
            "failure": {
                "phase": "dependency-resolution",
                "types": [fixtures.MODULE_VERSION_FAILURE, fixtures.LOCK_OUT_OF_DATE],
                "fixture_messages": ["Dependency lock state out of date",
                                     f"Resolved '{fixtures.GROUP}:extra:1.0' which is not part of the dependency lock state"],
            },
        }]
        return root, marker, target, owner, result

    def test_actual005_lock_origin_wrapper_message_is_supported(self):
        root, _, _, owner, result = self.actual005_added_dependency_fixture()
        observed = self.observe("added-dependency", root, owner, result)
        self.assertTrue(observed["actual_expected_result_observed"])
        self.assertEqual("extra-resolved-module", observed["lock_evidence"]["lock_discrepancy"])

    def test_actual005_lock_origin_wrapper_cannot_mask_unknown_or_unpaired_causes(self):
        root, _, target, owner, result = self.actual005_added_dependency_fixture()
        original = copy.deepcopy(target["unresolved"][0]["failure"])
        for mutation in ("unknown-wrapper", "wrong-wrapper-message", "wrong-terminal-module", "unpaired-message", "extra-cause"):
            with self.subTest(mutation=mutation):
                error = copy.deepcopy(original)
                if mutation == "unknown-wrapper":
                    error["types"][0] = "unrelated.example.ModuleVersionResolveException"
                elif mutation == "wrong-wrapper-message":
                    error["fixture_messages"][0] += " from an unrelated source"
                elif mutation == "wrong-terminal-module":
                    error["fixture_messages"][1] = error["fixture_messages"][1].replace(":extra:", ":other:")
                elif mutation == "unpaired-message":
                    error["fixture_messages"].pop()
                else:
                    error["types"].append("java.io.IOException")
                    error["fixture_messages"].append("unrelated I/O failure")
                target["unresolved"][0]["failure"] = error
                self.assert_unverified(self.observe("added-dependency", root, owner, result))

    def test_actual005_lock_origin_wrapper_cannot_replace_exact_state_or_owner(self):
        root, marker, _, owner, result = self.actual005_added_dependency_fixture()
        owner["configurations"][0]["failures"] = [{"types": ["java.io.IOException"], "fixture_messages": ["unrelated failure"]}]
        self.assert_unverified(self.observe("added-dependency", root, owner, result))
        owner["configurations"][0]["failures"] = []
        lock = root / m.lock_path(".", marker["host"])
        lock.write_text(lock.read_text().replace("leaf:1.0", "leaf:1.1"))
        self.refresh_integrity(root, marker, result)
        self.assert_unverified(self.observe("added-dependency", root, owner, result))

    def test_actual005_lock_origin_wrapper_cannot_mask_timeout_or_checksum_failure(self):
        root, _, _, owner, result = self.actual005_added_dependency_fixture()
        result["execution"]["reason"] = "timeout"
        self.assert_unverified(self.observe("added-dependency", root, owner, result))
        del result["execution"]["reason"]
        (root / "build/dependency-integrity/check/gradle.log").write_text("Dependency verification failed for artifact\n")
        self.assert_unverified(self.observe("added-dependency", root, owner, result))

    def actual006_removed_dependency_fixture(self):
        root, marker, target, owner, result = self.lock_fixture("removed-dependency")
        # Same exact short wrapper, now actually observed for the missing locked
        # leaf in006. This is a synthetic replay, not a new Gradle execution.
        target["unresolved"] = [{
            "from": "project::", "requested": f"{fixtures.GROUP}:leaf:1.0", "constraint": True,
            "failure": {
                "phase": "dependency-resolution",
                "types": [fixtures.MODULE_VERSION_FAILURE, fixtures.LOCK_OUT_OF_DATE],
                "fixture_messages": ["Dependency lock state out of date",
                                     f"Did not resolve '{fixtures.GROUP}:leaf:1.0' which is part of the dependency lock state"],
            },
        }]
        return root, marker, target, owner, result

    def test_actual006_removed_lock_origin_wrapper_is_supported(self):
        root, _, _, owner, result = self.actual006_removed_dependency_fixture()
        observed = self.observe("removed-dependency", root, owner, result)
        self.assertTrue(observed["actual_expected_result_observed"])
        self.assertEqual("locked-module-not-resolved", observed["lock_evidence"]["lock_discrepancy"])

    def test_lock_origin_rejection_requires_a_true_constraint_edge(self):
        root, _, target, owner, result = self.actual005_added_dependency_fixture()
        for constraint in (False, None, 1, "true"):
            with self.subTest(constraint=constraint):
                target["unresolved"][0]["constraint"] = constraint
                self.assert_unverified(self.observe("added-dependency", root, owner, result))

    def test_actual006_removed_wrapper_does_not_accept_other_lock_causes(self):
        root, _, target, owner, result = self.actual006_removed_dependency_fixture()
        error = target["unresolved"][0]["failure"]
        original = copy.deepcopy(error)
        for mutation in ("wrong-terminal-module", "wrong-wrapper-type", "extra-cause", "wrong-wrapper-message"):
            with self.subTest(mutation=mutation):
                error = copy.deepcopy(original)
                if mutation == "wrong-terminal-module":
                    error["fixture_messages"][1] = error["fixture_messages"][1].replace(":leaf:", ":extra:")
                elif mutation == "wrong-wrapper-type":
                    error["types"][0] = "java.io.IOException"
                elif mutation == "extra-cause":
                    error["types"].append("java.io.IOException")
                    error["fixture_messages"].append("unrelated I/O failure")
                else:
                    error["fixture_messages"][0] += " (unrelated)"
                target["unresolved"][0]["failure"] = error
                self.assert_unverified(self.observe("removed-dependency", root, owner, result))

    def test_exact_type_with_wrong_configuration_message_is_not_a_match(self):
        case = "missing-configuration-lock"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"][0]["fixture_messages"][0] = target["failures"][0]["fixture_messages"][0].replace("newUnrecordedClasspath", "otherClasspath")
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_known_suffix_on_unrelated_exception_is_not_a_match(self):
        case = "missing-host-lock"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"][0]["types"][0] = "unrelated.example.MissingLockStateException"
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_missing_state_message_paired_to_io_type_is_not_a_match(self):
        case = "missing-host-lock"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"][0]["types"][0] = "java.io.IOException"
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_lock_exception_wrapping_unrelated_cause_is_not_a_match(self):
        case = "added-dependency"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"][0]["types"].append("java.io.IOException")
        target["failures"][0]["fixture_messages"].append("unrelated I/O failure")
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_unrecognized_wrapper_before_exact_lock_cause_is_not_a_match(self):
        case = "removed-dependency"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"][0]["types"].insert(0, "java.io.IOException")
        target["failures"][0]["fixture_messages"].insert(0, "unrelated I/O failure")
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_paired_known_module_wrapper_is_synthetic_parser_supported(self):
        case = "added-dependency"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"][0]["types"].insert(0, fixtures.MODULE_VERSION_FAILURE)
        target["failures"][0]["fixture_messages"].insert(0, f"Could not resolve {fixtures.GROUP}:extra:1.0.")
        self.assertTrue(self.observe(case, root, owner, result)["actual_expected_result_observed"])

    def test_message_type_alignment_is_required(self):
        case = "added-dependency"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"][0]["fixture_messages"].append("unpaired lock words")
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_unrelated_configuration_failure_prevents_missing_lock_verdict(self):
        case = "missing-host-lock"
        root, _, _, owner, result = self.lock_fixture(case)
        owner["configurations"][0]["status"] = "failed"
        owner["configurations"][0]["failures"] = [{"types": ["java.io.IOException"], "fixture_messages": ["not a lock failure"]}]
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_unrelated_artifact_failure_prevents_stale_lock_verdict(self):
        case = "added-dependency"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"].append({"phase": "artifact-read", "types": ["java.io.IOException"], "fixture_messages": ["file read failed"]})
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_top_level_owner_failure_prevents_lock_verdict(self):
        case = "removed-dependency"
        root, _, _, owner, result = self.lock_fixture(case)
        owner["failures"] = [{"types": ["java.io.IOException"]}]
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_missing_configuration_inventory_prevents_lock_verdict(self):
        case = "missing-configuration-lock"
        root, _, _, owner, result = self.lock_fixture(case)
        owner["inventory"].pop()
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_other_owner_cannot_supply_expected_configuration_failure(self):
        case = "missing-host-lock"
        root, _, _, owner, result = self.lock_fixture(case)
        owner["project_path"] = ":other"
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_existing_actual_host_lock_cannot_prove_missing_host_lock(self):
        case = "missing-host-lock"
        root, marker, _, owner, result = self.lock_fixture(case)
        (root / m.lock_path(".", marker["host"])).write_text("empty=fixtureClasspath\n")
        self.refresh_integrity(root, marker, result)
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_existing_configuration_entry_cannot_prove_missing_configuration(self):
        case = "missing-configuration-lock"
        root, marker, _, owner, result = self.lock_fixture(case)
        lock = root / m.lock_path(".", marker["host"])
        lock.write_text(lock.read_text().replace("empty=", "empty=newUnrecordedClasspath"))
        self.refresh_integrity(root, marker, result)
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_wrong_locked_module_set_prevents_stale_lock_verdict(self):
        case = "added-dependency"
        root, marker, _, owner, result = self.lock_fixture(case)
        lock = root / m.lock_path(".", marker["host"])
        lock.write_text(lock.read_text().replace("leaf:1.0", "leaf:1.1"))
        self.refresh_integrity(root, marker, result)
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_wrong_selected_module_set_prevents_addition_verdict(self):
        case = "added-dependency"
        root, _, target, owner, result = self.lock_fixture(case)
        target["components"].pop()
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_other_module_cannot_supply_exact_stale_lock_message(self):
        case = "removed-dependency"
        root, _, target, owner, result = self.lock_fixture(case)
        target["failures"][0]["fixture_messages"][0] = target["failures"][0]["fixture_messages"][0].replace(":leaf:", ":other:")
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_graph_with_unrelated_direct_edge_cannot_prove_stale_lock(self):
        case = "added-dependency"
        root, _, target, owner, result = self.lock_fixture(case)
        target["edges"][0]["requested"] = f"{fixtures.GROUP}:other:1.0"
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_changed_known_checksum_prevents_pure_lock_verdict(self):
        case = "removed-dependency"
        root, marker, _, owner, result = self.lock_fixture(case)
        trust = fixtures.known_metadata()
        trust[(fixtures.GROUP, "parent", "1.0", "parent-1.0.pom")] = "0" * 64
        (root / "gradle/verification-metadata.xml").write_bytes(m.metadata_bytes(trust))
        self.refresh_integrity(root, marker, result)
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_checksum_failure_alongside_exact_lock_cause_is_not_a_lock_pass(self):
        case = "missing-host-lock"
        root, _, _, owner, result = self.lock_fixture(case)
        (root / "build/dependency-integrity/check/gradle.log").write_text("Dependency verification failed for artifact\n")
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_timeout_after_exact_lock_message_is_not_a_lock_pass(self):
        case = "missing-host-lock"
        root, _, _, owner, result = self.lock_fixture(case)
        result["execution"]["reason"] = "timeout"
        self.assert_unverified(self.observe(case, root, owner, result))

    def test_unknown_case_cannot_fall_back_to_generic_lock_acceptance(self):
        root, _, _, owner, result = self.lock_fixture("missing-host-lock")
        self.assert_unverified(self.observe("unknown-case", root, owner, result))


class PlannedGradleFixtureTests(TemporaryCase):
    def constrained_fixture(self):
        """Synthetic parser inputs based on archived fixture002, NOT another Gradle run."""
        root, marker = self.fixture(case="transitive-strict-drift")
        lock = root / m.lock_path(".", marker["host"])
        lock.parent.mkdir(parents=True)
        lock.write_text(f"{fixtures.GROUP}:leaf:1.0=fixtureClasspath\n{fixtures.GROUP}:parent:1.0=fixtureClasspath\nempty=\n")
        message = ("Component is the target of multiple version constraints with conflicting requirements:\n"
                   "1.0 - from lock file\n1.1\n")
        error = {"types": ["org.gradle.internal.resolve.ModuleVersionResolveException",
                            "org.gradle.internal.component.resolution.failure.exception.ConflictingConstraintsException"],
                 "fixture_messages": [message]}
        specs = [(f"module:{fixtures.GROUP}:parent:1.0", f"{fixtures.GROUP}:leaf:[1.0,2.0)", False),
                 ("project::", f"{fixtures.GROUP}:leaf:{{strictly 1.0}}", True),
                 ("project::", f"{fixtures.GROUP}:leaf:{{strictly 1.1}}", True)]
        diagnostics = [{"build_root": ".", "project_path": ":", "scope": "project", "name": "fixtureClasspath",
                        "status": "failed", "root_component_id": "project::", "failures": [],
                        "unresolved": [{"from": source, "requested": requested, "constraint": constraint, "failure": copy.deepcopy(error)}
                                       for source, requested, constraint in specs]}]
        return root, marker, diagnostics

    def test_exact_observed_constraint_shape_matches_known_fixture_lock_and_bytes(self):
        root, marker, diagnostics = self.constrained_fixture()
        result = fixtures.transitive_constraint_evidence(root, marker, diagnostics)
        self.assertEqual("1.0", result["locked_version"])
        self.assertEqual("1.1", result["strict_requested_version"])
        self.assertEqual(3, len(result["matched_unresolved_edges"]))
        self.assertEqual(4, result["known_leaf_artifact_and_metadata_hashes_confirmed"])

    def test_constraint_words_without_actual_error_type_are_not_a_match(self):
        root, marker, diagnostics = self.constrained_fixture()
        diagnostics[0]["unresolved"][0]["failure"]["types"] = ["UnrelatedFailure"]
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_conflicting_versions_without_explicit_lock_origin_are_not_a_match(self):
        root, marker, diagnostics = self.constrained_fixture()
        error = diagnostics[0]["unresolved"][0]["failure"]
        error["fixture_messages"] = [value.replace("1.0 - from lock file", "1.0") for value in error["fixture_messages"]]
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_other_component_constraint_is_not_transitive_leaf_evidence(self):
        root, marker, diagnostics = self.constrained_fixture()
        diagnostics[0]["unresolved"][0]["requested"] = f"{fixtures.GROUP}:other:[1.0,2.0)"
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_both_root_constraints_and_actual_transitive_edge_are_required(self):
        root, marker, diagnostics = self.constrained_fixture()
        diagnostics[0]["unresolved"].pop()
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_duplicate_constraint_edge_cannot_substitute_for_missing_selector(self):
        root, marker, diagnostics = self.constrained_fixture()
        diagnostics[0]["unresolved"][2] = copy.deepcopy(diagnostics[0]["unresolved"][1])
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_unrelated_configuration_failure_prevents_exact_lock_verdict(self):
        root, marker, diagnostics = self.constrained_fixture()
        diagnostics.append({"build_root": ".", "project_path": ":", "scope": "buildscript", "name": "classpath",
                            "status": "failed", "failures": [{"types": ["UnrelatedFailure"]}]})
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_actual_lock_must_contain_expected_old_transitive_version(self):
        root, marker, diagnostics = self.constrained_fixture()
        lock = root / m.lock_path(".", marker["host"])
        lock.write_text(lock.read_text().replace("leaf:1.0", "leaf:1.1"))
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_both_version_metadata_and_artifact_hashes_must_be_known(self):
        root, marker, diagnostics = self.constrained_fixture()
        trust = fixtures.known_metadata()
        del trust[(fixtures.GROUP, "leaf", "1.1", "leaf-1.1.pom")]
        (root / "gradle/verification-metadata.xml").write_bytes(m.metadata_bytes(trust))
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_changed_future_leaf_bytes_are_not_counted_as_clean_lock_drift(self):
        root, marker, diagnostics = self.constrained_fixture()
        (root / f"repo/{fixtures.GROUP_DIRECTORY}/leaf/1.1/leaf-1.1.jar").write_bytes(b"not the controlled bytes")
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_unrelated_artifact_failure_prevents_exact_lock_verdict(self):
        root, marker, diagnostics = self.constrained_fixture()
        diagnostics[0]["failures"] = [{"phase": "artifact-resolution", "types": ["UnrelatedFailure"]}]
        self.assertIsNone(fixtures.transitive_constraint_evidence(root, marker, diagnostics))

    def test_negative_subset_always_has_baseline_positive(self):
        self.assertEqual(("baseline-check", "wrong-jar-sha", "transitive-strict-drift"),
                         fixtures.selected_cases(["transitive-strict-drift", "wrong-jar-sha"]))

    def test_fixture_case_typos_and_duplicates_fail(self):
        for cases in ([], ["typo"], ["wrong-jar-sha", "wrong-jar-sha"]):
            with self.subTest(cases=cases), self.assertRaises(m.IntegrityError):
                fixtures.selected_cases(cases)

    def test_unselected_full_suite_is_not_implicitly_skipped(self):
        self.assertEqual(fixtures.ALL_CASES, fixtures.selected_cases(None))

    def test_incompatible_resolution_strategy_is_not_installed(self):
        script = (driver.TOOL_DIRECTORY / "resolve-graphs.init.gradle").read_text()
        self.assertNotIn(".resolutionStrategy.failOnChangingVersions(", script)
        self.assertIn("details.changing", script)
        self.assertIn("dependency.changing", script)
        self.assertIn("configuration.incoming.beforeResolve", script)
        self.assertIn(m.CHANGING_POLICY, script)

    def test_init_guard_has_all_exact_runtime_paths_and_no_other_cache_use_claim(self):
        script = (driver.TOOL_DIRECTORY / "resolve-graphs.init.gradle").read_text()
        for key, value in {**m.JVM_PRIVATE_PATHS, **m.ENV_PRIVATE_PATHS}.items():
            self.assertIn(key, script)
            self.assertIn(value, script)
        self.assertIn('System.getProperty(key)', script)
        self.assertIn('System.getenv(key)', script)
        self.assertIn('new File(value).isAbsolute()', script)
        self.assertIn('wrapper_client_observed: false, non_gradle_cache_use_verified: false', script)

    def test_total_deadline_prevents_even_first_mocked_gradle_invocation(self):
        destination = self.root / "deadline-fixtures"
        with mock.patch.object(fixtures.time, "monotonic", side_effect=[0, 290, 290]), \
                mock.patch.object(driver, "run") as gradle:
            result = fixtures.execute(destination, self.installed_gradle_stub(), total_timeout=300,
                                      cases=["wrong-jar-sha", "transitive-strict-drift"])
        gradle.assert_not_called()
        self.assertFalse(result["bootstrap_complete"])
        self.assertFalse(result["selected_cases_observed_as_expected"])
        self.assertIn("total-timeout", result["stopped_reason"])
        self.assertEqual(4, result["maximum_gradle_invocations"])

    def test_timeout_stops_subset_without_counting_a_negative_pass(self):
        destination = self.root / "timeout-fixtures"
        with mock.patch.object(driver, "run", return_value={"execution": {"exit_code": -15, "reason": "timeout"}}) as gradle:
            result = fixtures.execute(destination, self.installed_gradle_stub(), cases=["wrong-jar-sha"])
        self.assertEqual(1, gradle.call_count)
        self.assertEqual(0, len(result["cases"]))
        self.assertFalse(result["selected_cases_observed_as_expected"])
        self.assertFalse(result["all_cases_observed_as_expected"])

    def test_one_deadline_is_propagated_and_subset_does_not_claim_full_suite(self):
        destination = self.root / "selected-fixtures"
        fake_result = {"execution": {"exit_code": 0, "process_started": True}, "selected_project_graph_complete": True}
        observed = lambda root, case, receipt: {"case": case, "actual_expected_result_observed": True}
        with mock.patch.object(driver, "run", return_value=fake_result) as gradle, \
                mock.patch.object(fixtures, "classify", side_effect=observed):
            result = fixtures.execute(destination, self.installed_gradle_stub(), timeout=90, total_timeout=300,
                                      cases=["wrong-jar-sha", "transitive-strict-drift"])
        self.assertEqual(4, gradle.call_count)
        self.assertEqual(1, len({call.kwargs["deadline"] for call in gradle.call_args_list}))
        self.assertTrue(all(call.kwargs["timeout"] == 90 for call in gradle.call_args_list))
        self.assertTrue(result["selected_cases_observed_as_expected"])
        self.assertFalse(result["all_cases_observed_as_expected"])
        self.assertNotIn("wrong-jar-sha", result["unexecuted_cases"])
        self.assertIn("wrong-pom-sha", result["unexecuted_cases"])

    def test_expired_process_budget_does_not_start_a_subprocess(self):
        with mock.patch.object(driver.time, "monotonic", return_value=295), \
                mock.patch.object(driver.shutil, "disk_usage", return_value=mock.Mock(free=20 * 1024 ** 3)), \
                mock.patch.object(driver.subprocess, "Popen") as process:
            result = driver._bounded(["NOT EXECUTED"], workspace=self.root, environment={},
                                     log=self.root / "not-created.log", timeout=90, reserve_mib=8192, deadline=300)
        process.assert_not_called()
        self.assertFalse(result["process_started"])
        self.assertEqual("total-timeout-before-launch", result["reason"])

    def test_sub_reserve_process_does_not_start(self):
        with mock.patch.object(driver.shutil, "disk_usage", return_value=mock.Mock(free=7 * 1024 ** 3)), \
                mock.patch.object(driver.subprocess, "Popen") as process:
            result = driver._bounded(["NOT EXECUTED"], workspace=self.root, environment={},
                                     log=self.root / "not-created.log", timeout=90, reserve_mib=8192)
        process.assert_not_called()
        self.assertEqual("disk-reserve-unavailable", result["reason"])

    def test_deterministic_harmless_jar_bytes(self):
        self.assertEqual(fixtures.jar_bytes("leaf", "1.0"), fixtures.jar_bytes("leaf", "1.0"))
        self.assertNotEqual(fixtures.jar_bytes("leaf", "1.0"), fixtures.jar_bytes("leaf", "1.1"))

    def test_tamper_case_changes_bytes_not_allowed_checksum(self):
        root, _ = self.fixture(case="wrong-jar-sha")
        policy = m.parse_metadata((root / "gradle/verification-metadata.xml").read_bytes())
        original = policy[(fixtures.GROUP, "leaf", "1.0", "leaf-1.0.jar")]
        actual = m.file_sha256(root / f"repo/{fixtures.GROUP_DIRECTORY}/leaf/1.0/leaf-1.0.jar")
        self.assertNotEqual(original, actual)
        self.assertFalse((root / ".dependency-cache").exists())

    def test_transitive_drift_fixture_preallows_both_checksums(self):
        root, _ = self.fixture(case="transitive-strict-drift")
        policy = m.parse_metadata((root / "gradle/verification-metadata.xml").read_bytes())
        for version in ("1.0", "1.1"):
            self.assertIn((fixtures.GROUP, "leaf", version, f"leaf-{version}.jar"), policy)
        self.assertIn('strictly("1.1")', (root / "build.gradle").read_text())
        self.assertFalse((root / ".dependency-cache").exists())

    def test_dynamic_fixture_changes_repository_not_parent_pom(self):
        first, _ = self.fixture("base")
        later, _ = self.fixture("later", case="dynamic-transitive-frozen")
        parent = f"repo/{fixtures.GROUP_DIRECTORY}/parent/1.0/parent-1.0.pom"
        self.assertEqual((first / parent).read_bytes(), (later / parent).read_bytes())
        self.assertTrue((later / f"repo/{fixtures.GROUP_DIRECTORY}/leaf/1.1/leaf-1.1.jar").exists())

    def test_included_bad_hash_fixture_is_explicit_not_a_trust_merge(self):
        root, marker = self.fixture(included=True, wrong_included_hash=True)
        main = m.parse_metadata((root / "gradle/verification-metadata.xml").read_bytes())
        child = m.parse_metadata((root / "included/gradle/verification-metadata.xml").read_bytes())
        self.assertEqual([".", "included"], marker["build_roots"])
        with self.assertRaises(m.IntegrityError):
            m.merge_metadata([main, child])

    def test_nonzero_timeout_without_gradle_error_is_not_a_tamper_pass(self):
        root, _ = self.fixture(case="wrong-jar-sha")
        output = root / "build/dependency-integrity/check"
        output.mkdir(parents=True)
        (output / "result.json").write_text("{}\n")
        (output / "gradle.log").write_text("fixture process timed out before configuration\n")
        result = fixtures.classify(root, "wrong-jar-sha", {"execution": {"exit_code": 143}})
        self.assertFalse(result["actual_expected_result_observed"])
        self.assertEqual("unverified", result["result_kind"])

    def test_matching_tamper_error_followed_by_timeout_is_still_not_a_pass(self):
        root, _ = self.fixture(case="wrong-jar-sha")
        output = root / "build/dependency-integrity/check"
        output.mkdir(parents=True)
        (output / "result.json").write_text("{}\n")
        expected = fixtures.known_metadata()[(fixtures.GROUP, "leaf", "1.0", "leaf-1.0.jar")]
        actual = m.file_sha256(root / f"repo/{fixtures.GROUP_DIRECTORY}/leaf/1.0/leaf-1.0.jar")
        evidence = {"owner_receipts": 1, "failure_types": ["FixtureDependencyVerificationException"],
                    "text": f"Dependency verification failed leaf-1.0.jar expected {expected} actual {actual}"}
        with mock.patch.object(fixtures, "failure_evidence", return_value=evidence):
            result = fixtures.classify(root, "wrong-jar-sha", {"execution": {"exit_code": -15, "reason": "total-timeout"}})
        self.assertFalse(result["actual_expected_result_observed"])


if __name__ == "__main__":
    unittest.main()
