"""Offline observer tests: synthetic /proc/jcmd data and tiny owned Python pipes.

No Gradle, jcmd, Java, registry or network is invoked by this suite.
"""
from __future__ import annotations

import copy
from contextlib import ExitStack
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import integrity as driver
import integrity_model as m
import runtime_witness as w


def stat_bytes(pid=303, *, parent=202, group=202, session=202, start=1234, state="S", name="java (worker)"):
    return (f"{pid} ({name}) " + " ".join([state, str(parent), str(group), str(session), *(["0"] * 15), str(start), "0"]) + "\n").encode()


def properties(workspace=Path("/fixture"), pid=303, *, version="17.0.20"):
    expected, _, _ = w.private_values(workspace)
    return (f"{pid}:\n#Synthetic, not actual jcmd\n" + "\n".join(f"{key}={value}" for key, value in expected.items()) +
            f"\njava.version={version}\nnot.selected=NEVER_ARCHIVE_PRIVATE_SENTINEL\n").encode()


class CheckpointTests(unittest.TestCase):
    def test_selected_checkpoint_matches_current_exact_tool_inputs(self):
        # A policy-only README update must get a new explicit immutable
        # checkpoint, not disable checksum verification or silently bless it.
        files = w.checkpoint_files()
        self.assertEqual(6, len(files))
        self.assertIn("scripts/dependencies/README.md", files)
        for name, digest in files.items():
            self.assertEqual(digest, m.file_sha256(w.SOURCE_ROOT / name))

    def test_manifest_checksum_is_not_refreshed_or_ignored(self):
        with mock.patch.object(m, "file_sha256", return_value="0" * 64):
            with self.assertRaisesRegex(w.WitnessError, "checkpoint-changed"):
                w.checkpoint_files()

    def test_documentation_checksum_is_still_enforced(self):
        original = m.file_sha256
        def changed(path):
            return "0" * 64 if path == w.SOURCE_ROOT / "scripts/dependencies/README.md" else original(path)
        with mock.patch.object(m, "file_sha256", side_effect=changed):
            with self.assertRaisesRegex(w.WitnessError, "frozen-input-changed"):
                w.checkpoint_files()


class PropertyTests(unittest.TestCase):
    def test_selected_properties_only(self):
        result = w.selected_properties(properties(), 303, Path("/fixture"))
        self.assertTrue(result["selected_values_match"])
        self.assertEqual(4, len(result["property_matches"]))
        self.assertEqual("17.0.20", result["java_runtime_version"])
        self.assertNotIn("NEVER_ARCHIVE_PRIVATE_SENTINEL", json.dumps(result))

    def test_space_in_candidate_property(self):
        result = w.selected_properties(properties(Path("/fixture with spaces")), 303, Path("/fixture with spaces"))
        self.assertTrue(result["selected_values_match"])

    def test_properties_store_escapes(self):
        self.assertEqual(" /a:b=c!#é\\", w.unescape_property(r"\ /a\:b\=c\!\#\u00e9\\"))

    def test_missing_selected_property(self):
        with self.assertRaisesRegex(w.WitnessError, "selected-property-missing"):
            w.selected_properties(properties().replace(b"user.home=", b"ignored.home="), 303, Path("/fixture"))

    def test_wrong_private_home(self):
        with self.assertRaisesRegex(w.WitnessError, "private-jvm-property-mismatch"):
            w.selected_properties(properties().replace(b"user.home=/fixture", b"user.home=/foreign"), 303, Path("/fixture"))

    def test_duplicate_selected_property(self):
        with self.assertRaisesRegex(w.WitnessError, "duplicate-or-continued"):
            w.selected_properties(properties() + b"user.home=/fixture/.dependency-home\n", 303, Path("/fixture"))

    def test_continued_selected_property_rejected(self):
        with self.assertRaisesRegex(w.WitnessError, "duplicate-or-continued"):
            w.selected_properties(properties().replace(b"user.home=/fixture/.dependency-home\n", b"user.home=/fixture/.dependency-home\\\n"), 303, Path("/fixture"))

    def test_continuation_cannot_inject_missing_selected_key(self):
        raw = properties().replace(b"user.home=/fixture/.dependency-home\n", b"")
        raw += b"unknown=ignored\\\nuser.home=/fixture/.dependency-home\n"
        with self.assertRaisesRegex(w.WitnessError, "selected-property-missing"):
            w.selected_properties(raw, 303, Path("/fixture"))

    def test_wrong_header(self):
        with self.assertRaisesRegex(w.WitnessError, "diagnostic-pid-header-mismatch"):
            w.selected_properties(properties(), 999, Path("/fixture"))

    def test_wrong_jdk(self):
        with self.assertRaisesRegex(w.WitnessError, "observed-jdk-not17"):
            w.selected_properties(properties(version="21.0.12"), 303, Path("/fixture"))

    def test_version_cannot_export_path_or_raw_text(self):
        with self.assertRaisesRegex(w.WitnessError, "observed-jdk-not17"):
            w.selected_properties(properties(version="17.private-secret/path"), 303, Path("/fixture"))

    def test_oversized_output(self):
        with self.assertRaisesRegex(w.WitnessError, "diagnostic-output-limit"):
            w.selected_properties(b"x" * (w.MAX_DIAGNOSTIC + 1), 303, Path("/fixture"))

    def test_invalid_unicode_escape(self):
        with self.assertRaisesRegex(w.WitnessError, "invalid-property-escape"):
            w.unescape_property(r"\uZZZZ")


class ValidationDiagnosticsTests(unittest.TestCase):
    def test_exact_enum_exception_code_is_retained(self):
        self.assertEqual("daemon-ancestry-mismatch", w.failure_reason(w.WitnessError("daemon-ancestry-mismatch")))

    def test_arbitrary_exception_bodies_never_become_reason_codes(self):
        cases = ((w.WitnessError("NEVER_ARCHIVE_PRIVATE_SENTINEL"), "other-validation-failure"),
                 (FileNotFoundError("NEVER_ARCHIVE_PRIVATE_SENTINEL"), "input-disappeared"),
                 (PermissionError("NEVER_ARCHIVE_PRIVATE_SENTINEL"), "input-permission-denied"),
                 (OSError("NEVER_ARCHIVE_PRIVATE_SENTINEL"), "input-os-error"),
                 (m.IntegrityError("NEVER_ARCHIVE_PRIVATE_SENTINEL"), "integrity-validation-failed"),
                 (KeyError("NEVER_ARCHIVE_PRIVATE_SENTINEL"), "required-field-missing"),
                 (ValueError("NEVER_ARCHIVE_PRIVATE_SENTINEL"), "input-value-invalid"),
                 (subprocess.CalledProcessError(1, ["NEVER_ARCHIVE_PRIVATE_SENTINEL"]), "diagnostic-subprocess-error"))
        for failure, code in cases:
            with self.subTest(kind=type(failure).__name__):
                self.assertEqual(code, w.failure_reason(failure))
                self.assertIn(code, w.VALIDATION_REASON_CODES)

    def test_nonstring_or_multiple_exception_arguments_are_not_exported(self):
        for arguments in ((["NEVER_ARCHIVE_PRIVATE_SENTINEL"],), ("daemon-ancestry-mismatch", "NEVER_ARCHIVE_PRIVATE_SENTINEL")):
            self.assertEqual("other-validation-failure", w.failure_reason(w.WitnessError(*arguments)))

    def test_unknown_counter_keys_collapse_to_one_enum_bucket(self):
        state = {}
        for number in range(100):
            w.record_validation_reason(state, "daemon-candidate", f"NEVER_ARCHIVE_PRIVATE_SENTINEL-{number}")
        self.assertEqual({"daemon-candidate": {"other-validation-failure": 100}}, state["validation_reason_counts"])
        self.assertNotIn("NEVER_ARCHIVE_PRIVATE_SENTINEL", json.dumps(state))

    def test_counter_saturates_instead_of_growing(self):
        state = {}
        with mock.patch.object(w, "MAX_REASON_COUNT", 3):
            for _ in range(10):
                w.record_validation_reason(state, "daemon-candidate", "daemon-ancestry-mismatch")
        self.assertEqual(3, state["validation_reason_counts"]["daemon-candidate"]["daemon-ancestry-mismatch"])
        self.assertTrue(state["validation_reason_counts_saturated"])

    def test_stage_must_be_one_of_the_fixed_enum_values(self):
        state = {}
        with self.assertRaisesRegex(w.WitnessError, "invalid-diagnostic-stage"):
            w.record_validation_reason(state, "NEVER_ARCHIVE_PRIVATE_SENTINEL", "daemon-ancestry-mismatch")
        self.assertEqual({}, state)

    def test_maximum_enum_counter_map_is_bounded_below_receipt_limit(self):
        state = {}
        for stage in w.VALIDATION_STAGES:
            for code in w.VALIDATION_REASON_CODES:
                w.record_validation_reason(state, stage, code)
        self.assertEqual(len(w.VALIDATION_STAGES), len(state["validation_reason_counts"]))
        self.assertTrue(all(len(counts) == len(w.VALIDATION_REASON_CODES) for counts in state["validation_reason_counts"].values()))
        self.assertLess(len(json.dumps([state] * len(w.CASE_NAMES)).encode()), w.MAX_RECEIPT)


class ProcParserTests(unittest.TestCase):
    def test_command_name_with_parentheses_and_spaces(self):
        self.assertEqual(w.ProcessIdentity(303, 202, 202, 202, 1234), w.parse_stat(stat_bytes(name="java )) (x worker"), 303))

    def test_wrong_stat_pid(self):
        with self.assertRaises(w.WitnessError):
            w.parse_stat(stat_bytes(), 304)

    def test_short_stat(self):
        with self.assertRaises(w.WitnessError):
            w.parse_stat(b"303 (java) S 1\n", 303)

    def test_zombie_is_not_observed_live(self):
        with self.assertRaisesRegex(w.WitnessError, "process-not-live"):
            w.parse_stat(stat_bytes(state="Z"), 303)

    def test_missing_environment_delimiter(self):
        with self.assertRaises(w.WitnessError):
            w.environment(b"HOME=/private")

    def test_duplicate_environment_key(self):
        with self.assertRaisesRegex(w.WitnessError, "invalid-environment-record"):
            w.environment(b"HOME=/one\0HOME=/two\0")

    def test_environment_equals_inside_value(self):
        self.assertEqual({"KEY": "left=right"}, w.environment(b"KEY=left=right\0"))

    def test_invalid_proc_leaf_cannot_escape(self):
        with self.assertRaisesRegex(w.WitnessError, "unsupported-proc-read"):
            w.proc_bytes(303, "../../private")

    def test_bool_pid_rejected(self):
        with self.assertRaisesRegex(w.WitnessError, "invalid-process-id"):
            w.proc_bytes(True, "stat")

    def test_children_of_non_main_java_thread_are_included(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202"), Path("212")])), \
                mock.patch.object(w, "proc_bytes", side_effect=lambda pid, leaf, limit: b"" if leaf == "task/202/children" else b"303 304 "):
            self.assertEqual(w.ChildInventory((303, 304), complete=True), w.owned_children(client))

    def test_children_de_duplicate_owned_threads(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202"), Path("212")])), \
                mock.patch.object(w, "proc_bytes", return_value=b"303 "):
            self.assertEqual(w.ChildInventory((303,), complete=True), w.owned_children(client))

    def test_child_enumeration_identity_change(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", side_effect=[client, w.ProcessIdentity(202, 101, 202, 202, 1001)]), \
                mock.patch.object(Path, "iterdir", return_value=iter([])):
            with self.assertRaisesRegex(w.WitnessError, "client-children-identity-mismatch"):
                w.owned_children(client)

    def test_missing_children_file_on_live_thread_is_not_known_empty(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202")])), \
                mock.patch.object(w, "proc_bytes", side_effect=FileNotFoundError()), \
                mock.patch.object(Path, "stat", return_value=mock.sentinel.live_thread):
            inventory = w.owned_children(client)
            self.assertFalse(inventory.complete)
            self.assertEqual((), inventory.pids)

    def test_missing_file_of_vanished_thread_is_only_thread_churn(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        def children(pid, leaf, limit):
            if leaf == "task/212/children":
                raise FileNotFoundError()
            return b"303 "
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202"), Path("212")])), \
                mock.patch.object(w, "proc_bytes", side_effect=children), \
                mock.patch.object(Path, "stat", side_effect=FileNotFoundError()):
            self.assertEqual(w.ChildInventory((303,), complete=True), w.owned_children(client))

    def test_partial_unavailable_inventory_retains_known_children(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        def children(pid, leaf, limit):
            if leaf == "task/212/children":
                raise FileNotFoundError()
            return b"303 "
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202"), Path("212")])), \
                mock.patch.object(w, "proc_bytes", side_effect=children), \
                mock.patch.object(Path, "stat", return_value=mock.sentinel.live_thread):
            self.assertEqual(w.ChildInventory((303,), complete=False), w.owned_children(client))

    def test_readable_empty_inventory_is_known_empty(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202")])), \
                mock.patch.object(w, "proc_bytes", return_value=b""):
            self.assertEqual(w.ChildInventory((), complete=True), w.owned_children(client))

    def test_no_readable_threads_of_live_client_is_incomplete(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([])):
            self.assertEqual(w.ChildInventory((), complete=False), w.owned_children(client))

    def test_children_permission_denial_is_not_empty_or_fallback_authority(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202")])), \
                mock.patch.object(w, "proc_bytes", side_effect=PermissionError()):
            with self.assertRaises(PermissionError):
                w.owned_children(client)

    def test_children_thread_inventory_limit_is_retained(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter(Path(str(n)) for n in range(1000, 1257))):
            with self.assertRaisesRegex(w.WitnessError, "client-thread-limit"):
                w.owned_children(client)

    def test_children_invalid_pid_is_not_candidate(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202")])), \
                mock.patch.object(w, "proc_bytes", return_value=b"303 ../foreign"):
            with self.assertRaisesRegex(w.WitnessError, "invalid-child-list"):
                w.owned_children(client)


class TemporaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-runtime-witness-offline-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "candidate"
        self.workspace.mkdir()
        self.jdk = self.root / "jdk17"
        (self.jdk / "bin").mkdir(parents=True)
        (self.jdk / "bin/java").write_text("NOT EXECUTED\n")
        self.gradle = self.root / "gradle-9.7.1"
        (self.gradle / "bin").mkdir(parents=True)
        (self.gradle / "lib").mkdir()
        (self.gradle / "bin/gradle").write_text("NOT EXECUTED\n")
        (self.gradle / "lib/gradle-core-api-9.7.1.jar").write_text("NOT EXECUTED\n")
        init = self.workspace / "scripts/dependencies/resolve-graphs.init.gradle"
        init.parent.mkdir(parents=True)
        init.write_text("NOT EXECUTED\n")
        for relative in set(m.JVM_PRIVATE_PATHS.values()) | set(m.ENV_PRIVATE_PATHS.values()):
            (self.workspace / relative).mkdir(parents=True, exist_ok=True)
        _, env, options = w.private_values(self.workspace)
        self.env = {**env, "JAVA_HOME": str(self.jdk), "JAVA_TOOL_OPTIONS": options, "PATH": str(self.jdk / "bin") + ":/usr/bin"}
        self.suite = w.ProcessIdentity(101, 100, 101, 101, 100)
        self.client = w.ProcessIdentity(202, 101, 202, 202, 101)
        self.daemon = w.ProcessIdentity(303, 202, 202, 202, 102)
        self.marker = {"build_roots": ["."], "kind": "controlled-fixture", "source_input_digest": "a" * 64}
        self.context = {"workspace": self.workspace, "marker": self.marker, "mode": "bootstrap", "jdk_home": self.jdk,
                        "gradle_home": self.gradle, "suite": self.suite}

    def command(self, role):
        if role == "client":
            suffix = driver.build_command(self.workspace, self.marker, entry_root=".", run_id="bootstrap", mode="bootstrap", gradle_home=self.gradle)[1:]
            return [*w.client_prefix(self.jdk, self.gradle), *suffix]
        return [str(self.jdk / "bin/java"), "-Xmx512m", "-cp", str(self.gradle / "lib/gradle-daemon-main-9.7.1.jar"),
                f"-javaagent:{self.gradle}/lib/agents/gradle-instrumentation-agent-9.7.1.jar", w.DAEMON_MAIN, "9.7.1"]

    def check_java(self, role="client", *, arguments=None, identities=None, env=None, executable=None, cwd=None):
        mapping = identities or {101: self.suite, 202: self.client, 303: self.daemon}
        arguments = arguments if arguments is not None else self.command(role)
        env = env if env is not None else self.env
        raw_env = "".join(f"{key}={value}\0" for key, value in env.items()).encode()
        with mock.patch.object(w, "identity", side_effect=lambda pid: mapping[pid]), \
                mock.patch.object(os, "readlink", side_effect=lambda name: str(executable or self.jdk / "bin/java") if name.endswith("/exe") else str(cwd or self.workspace)), \
                mock.patch.object(w, "proc_bytes", side_effect=lambda pid, name, limit=w.MAX_PROC: raw_env if name == "environ" else ("\0".join(arguments) + "\0").encode()):
            return w.check_java(202 if role == "client" else 303, role=role, client=None if role == "client" else self.client, **self.context)


class OwnershipTests(TemporaryTests):
    def test_client_exact_command_ancestry_environment(self):
        self.assertEqual(self.client, self.check_java())

    def test_daemon_exact_command_ancestry_environment(self):
        self.assertEqual(self.daemon, self.check_java("daemon"))

    def test_actual_daemon_self_group_and_session_with_exact_client_parent(self):
        daemon = w.ProcessIdentity(303, self.client.pid, 303, 303, 102)
        mapping = {101: self.suite, 202: self.client, 303: daemon}
        self.assertEqual(daemon, self.check_java("daemon", identities=mapping))

    def test_mixed_or_foreign_daemon_group_session_is_not_observed_shape(self):
        for group, session in ((202, 303), (303, 202), (999, 999), (303, 999), (999, 303)):
            with self.subTest(group=group, session=session):
                mapping = {101: self.suite, 202: self.client,
                           303: w.ProcessIdentity(303, 202, group, session, 102)}
                with self.assertRaisesRegex(w.WitnessError, "daemon-ancestry-mismatch"):
                    self.check_java("daemon", identities=mapping)

    def test_self_group_daemon_is_not_owned_without_exact_client_parent(self):
        mapping = {101: self.suite, 202: self.client, 303: w.ProcessIdentity(303, 999, 303, 303, 102)}
        with self.assertRaisesRegex(w.WitnessError, "daemon-ancestry-mismatch"):
            self.check_java("daemon", identities=mapping)

    def test_self_group_daemon_wrong_start_order_remains_rejected(self):
        mapping = {101: self.suite, 202: self.client, 303: w.ProcessIdentity(303, 202, 303, 303, 99)}
        with self.assertRaisesRegex(w.WitnessError, "daemon-ancestry-mismatch"):
            self.check_java("daemon", identities=mapping)

    def test_client_wrong_parent(self):
        mapping = {101: self.suite, 202: w.ProcessIdentity(202, 999, 202, 202, 101)}
        with self.assertRaisesRegex(w.WitnessError, "client-ancestry-mismatch"):
            self.check_java(identities=mapping)

    def test_daemon_wrong_parent(self):
        mapping = {101: self.suite, 202: self.client, 303: w.ProcessIdentity(303, 999, 202, 202, 102)}
        with self.assertRaisesRegex(w.WitnessError, "daemon-ancestry-mismatch"):
            self.check_java("daemon", identities=mapping)

    def test_daemon_wrong_start_order(self):
        mapping = {101: self.suite, 202: self.client, 303: w.ProcessIdentity(303, 202, 202, 202, 99)}
        with self.assertRaisesRegex(w.WitnessError, "daemon-ancestry-mismatch"):
            self.check_java("daemon", identities=mapping)

    def test_wrong_executable(self):
        with self.assertRaisesRegex(w.WitnessError, "java-executable-mismatch"):
            self.check_java(executable=Path("/foreign/java"))

    def test_foreign_working_directory(self):
        with self.assertRaisesRegex(w.WitnessError, "java-cwd-outside-candidate"):
            self.check_java(cwd=self.root)

    def test_client_other_task_not_allowed(self):
        command = self.command("client")
        command[command.index("nativeCmpkitDependencyGraph")] = "publish"
        with self.assertRaisesRegex(w.WitnessError, "gradle-client-command-mismatch"):
            self.check_java(arguments=command)

    def test_client_wrong_init_script_not_allowed(self):
        command = self.command("client")
        command[command.index("--init-script") + 1] = "/foreign/init.gradle"
        with self.assertRaisesRegex(w.WitnessError, "gradle-client-command-mismatch"):
            self.check_java(arguments=command)

    def test_daemon_non_gradle_main_not_allowed(self):
        command = self.command("daemon")
        command[-2] = "foreign.Main"
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_wrong_distribution(self):
        command = self.command("daemon")
        command[command.index("-cp") + 1] = "/foreign/daemon.jar"
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-classpath-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_home_environment_is_exact(self):
        with self.assertRaisesRegex(w.WitnessError, "private-environment-mismatch"):
            self.check_java(env={**self.env, "HOME": "/shared-home"})

    def test_inherited_jvm_override_rejected(self):
        with self.assertRaisesRegex(w.WitnessError, "inherited-jvm-override"):
            self.check_java(env={**self.env, "_JAVA_OPTIONS": "-Duser.home=/shared-home"})

    def test_generated_tool_options_must_be_exact(self):
        with self.assertRaisesRegex(w.WitnessError, "jvm-environment-mismatch"):
            self.check_java(env={**self.env, "JAVA_TOOL_OPTIONS": self.env["JAVA_TOOL_OPTIONS"] + " -Dextra=1"})

    def test_missing_private_directory(self):
        (self.workspace / ".dependency-home/konan").rmdir()
        with self.assertRaises(m.IntegrityError):
            self.check_java()

    def test_symlink_candidate_rejected(self):
        link = self.root / "linked"
        link.symlink_to(self.workspace, target_is_directory=True)
        with self.assertRaises(w.WitnessError):
            w.plain_absolute(link)

    def test_fixed_fixture_command_has_exactly_four_negatives(self):
        command = w.fixed_arguments(self.workspace, self.gradle)
        self.assertEqual(4, command.count("--case"))
        self.assertEqual(["--total-timeout", "300", "--timeout", "90", "--reserve-mib", "8192"], command[-6:])

    def test_reported_client_foreign_main_before_jar_regression(self):
        expected = self.command("client")
        command = [str(self.jdk / "bin/java"), "-Xmx64m", "-cp", "/foreign/application.jar", "foreign.Main",
                   *expected[expected.index("-jar"):]]
        with self.assertRaisesRegex(w.WitnessError, "gradle-client-command-mismatch"):
            self.check_java(arguments=command)

    def test_reported_daemon_foreign_main_before_gradle_main_regression(self):
        command = self.command("daemon")
        command.insert(-2, "foreign.Main")
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_reported_daemon_overriding_classpath_regression(self):
        command = self.command("daemon")
        command[-2:-2] = ["-cp", "/foreign/application.jar"]
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-classpath-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_duplicate_identical_classpath_rejected(self):
        command = self.command("daemon")
        command[-2:-2] = ["-cp", str(self.gradle / "lib/gradle-daemon-main-9.7.1.jar")]
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-classpath-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_jar_launch_mode_rejected(self):
        command = self.command("daemon")
        command[-2:-2] = ["-jar", "/foreign/application.jar"]
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_module_launch_mode_rejected(self):
        command = self.command("daemon")
        command[-2:-2] = ["--module", "foreign/foreign.Main"]
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_short_module_launch_mode_rejected(self):
        command = self.command("daemon")
        command[-2:-2] = ["-m", "foreign/foreign.Main"]
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_source_launch_mode_rejected(self):
        command = self.command("daemon")
        command[-2:-2] = ["--source", "17", "/foreign/Fixture.java"]
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_argfile_rejected(self):
        command = self.command("daemon")
        command.insert(-2, "@/foreign/arguments.txt")
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_long_classpath_override_rejected(self):
        command = self.command("daemon")
        command.insert(-2, "--class-path=/foreign/application.jar")
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_unknown_option_rejected(self):
        command = self.command("daemon")
        command.insert(-2, "--unknown-option=ignored")
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_foreign_agent_rejected(self):
        command = self.command("daemon")
        command.insert(-2, "-javaagent:/foreign/agent.jar")
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-command-mismatch"):
            self.check_java("daemon", arguments=command)

    def test_daemon_unscoped_system_property_rejected(self):
        command = self.command("daemon")
        command.insert(-2, "-Djava.system.class.loader=foreign.Loader")
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-unknown-option"):
            self.check_java("daemon", arguments=command)

    def test_daemon_repeated_heap_override_rejected(self):
        command = self.command("daemon")
        command.insert(-2, "-Xmx1024m")
        with self.assertRaisesRegex(w.WitnessError, "gradle-daemon-duplicate-option"):
            self.check_java("daemon", arguments=command)

    def test_daemon_scoped_option_grammar_positive_synthetic(self):
        command = self.command("daemon")
        command[1:1] = ["--add-opens=java.base/java.lang=ALL-UNNAMED", "--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED",
                        "--enable-native-access=ALL-UNNAMED", "-XX:MaxMetaspaceSize=384m", "-XX:+HeapDumpOnOutOfMemoryError",
                        "-Xms256m", "-Dfile.encoding=UTF-8", "-Duser.country", "-Duser.language=en", "-Duser.variant",
                        "-Djava.io.tmpdir=" + str(self.workspace / ".dependency-home/tmp")]
        self.assertEqual(self.daemon, self.check_java("daemon", arguments=command))


class AttachGuardTests(TemporaryTests):
    def observe(self, *, check=None, live=None, diagnostic_failure=None, expected=None):
        with mock.patch.object(w, "check_java", side_effect=check, return_value=self.client), \
                mock.patch.object(os, "pidfd_open", return_value=88), mock.patch.object(os, "close") as close, \
                mock.patch.object(w.select, "select", side_effect=live, return_value=([], [], [])), \
                mock.patch.object(w, "diagnostic", side_effect=diagnostic_failure,
                                  return_value=(properties(self.workspace, 202), {"exit_code": 0, "raw_stdout_archived": False})) as diagnostic:
            try:
                result = w.observe_java(202, role="client", client=None, expected_identity=expected or self.client,
                                        deadline=time.monotonic() + 10, **self.context)
            finally:
                self.diagnostic_calls = diagnostic.call_count
                self.closed = close.call_count
            return result

    def test_guarded_capture_returns_selected_values_only(self):
        result = self.observe()
        self.assertTrue(result["observed"])
        self.assertTrue(result["pidfd_live_before_and_after"])
        self.assertFalse(result["actual_cache_consumption_verified"])
        self.assertNotIn("NEVER_ARCHIVE_PRIVATE_SENTINEL", json.dumps(result))
        self.assertEqual((1, 1), (self.diagnostic_calls, self.closed))

    def test_recorded_pid_start_mismatch_prevents_attach(self):
        with self.assertRaisesRegex(w.WitnessError, "java-identity-changed-before-attach"):
            self.observe(expected=w.ProcessIdentity(202, 101, 202, 202, 999))
        self.assertEqual(0, self.diagnostic_calls)

    def test_identity_changes_before_attach(self):
        other = w.ProcessIdentity(202, 101, 202, 202, 999)
        with self.assertRaisesRegex(w.WitnessError, "java-identity-changed-before-attach"):
            self.observe(check=[self.client, other])
        self.assertEqual((0, 1), (self.diagnostic_calls, self.closed))

    def test_identity_changes_after_attach_not_a_pass(self):
        other = w.ProcessIdentity(202, 101, 202, 202, 999)
        with self.assertRaisesRegex(w.WitnessError, "java-identity-changed-after-attach"):
            self.observe(check=[self.client, self.client, other])
        self.assertEqual((1, 1), (self.diagnostic_calls, self.closed))

    def test_pidfd_exit_before_attach(self):
        with self.assertRaisesRegex(w.WitnessError, "java-identity-changed-before-attach"):
            self.observe(live=[([88], [], [])])
        self.assertEqual((0, 1), (self.diagnostic_calls, self.closed))

    def test_pidfd_exit_after_attach(self):
        with self.assertRaisesRegex(w.WitnessError, "java-identity-changed-after-attach"):
            self.observe(live=[([], [], []), ([88], [], [])])
        self.assertEqual((1, 1), (self.diagnostic_calls, self.closed))

    def test_failed_diagnostic_not_retried(self):
        with self.assertRaisesRegex(w.WitnessError, "diagnostic-timeout"):
            self.observe(diagnostic_failure=w.WitnessError("diagnostic-timeout"))
        self.assertEqual((1, 1), (self.diagnostic_calls, self.closed))


class SuiteOwnershipTests(TemporaryTests):
    def check(self, *, parent=100, script=None, extra=None, executable=None, cwd=None, java_home=None, changed=False):
        suite = w.ProcessIdentity(101, parent, 101, 101, 100)
        command = [sys.executable, str(script or w.TOOL_ROOT / "integrity.py"), *w.fixed_arguments(self.workspace, self.gradle)]
        if extra:
            command += extra
        selected_cwd = cwd or w.SOURCE_ROOT
        raw_env = f"JAVA_HOME={java_home or self.jdk}\0".encode()
        second = w.ProcessIdentity(101, parent, 101, 101, 101) if changed else suite
        with mock.patch.object(w, "identity", side_effect=[suite, second]), \
                mock.patch.object(os, "getppid", return_value=100), mock.patch.object(os, "getpid", return_value=999), \
                mock.patch.object(os, "readlink", side_effect=lambda name: str(executable or Path(sys.executable).resolve()) if name.endswith("/exe") else str(selected_cwd)), \
                mock.patch.object(w, "proc_bytes", side_effect=lambda pid, name: raw_env if name == "environ" else ("\0".join(command) + "\0").encode()):
            return w.check_suite(101, self.workspace, self.gradle, self.jdk)

    def test_exact_suite_sibling(self):
        self.assertEqual(self.suite, self.check())

    def test_other_parent_not_owned_sibling(self):
        with self.assertRaisesRegex(w.WitnessError, "suite-not-owned-sibling"):
            self.check(parent=777)

    def test_foreign_suite_executable(self):
        with self.assertRaisesRegex(w.WitnessError, "suite-python-mismatch"):
            self.check(executable=Path("/foreign/python"))

    def test_other_suite_script(self):
        with self.assertRaisesRegex(w.WitnessError, "suite-command-mismatch"):
            self.check(script=Path("/foreign/integrity.py"))

    def test_extra_suite_flag(self):
        with self.assertRaisesRegex(w.WitnessError, "suite-command-mismatch"):
            self.check(extra=["--offline"])

    def test_foreign_suite_checkout(self):
        with self.assertRaisesRegex(w.WitnessError, "suite-checkout-mismatch"):
            self.check(cwd=self.root)

    def test_foreign_suite_jdk(self):
        with self.assertRaisesRegex(w.WitnessError, "suite-jdk-mismatch"):
            self.check(java_home=Path("/foreign/jdk"))

    def test_changed_suite_start_identity(self):
        with self.assertRaisesRegex(w.WitnessError, "suite-identity-changed"):
            self.check(changed=True)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.marker = {"source_input_digest": "a" * 64, "host": "linux-x64",
                       "kind": "controlled-fixture", "build_roots": ["."]}
        self.daemon = {"observed": True, "identity": {"pid": 303}, "java_runtime_version": "17.0.20"}
        self.runtime = {"schema_version": 1, "record_type": "gradle-runtime-observation", "run_id": "check", "mode": "check",
                        "build_root": ".", "source_input_digest": "a" * 64, "host": "linux-x64", "gradle_version": "9.7.1",
                        "runtime_isolation": copy.deepcopy(m.RUNTIME_ISOLATION), "gradle_jvm_process_id": 303, "java_runtime_version": "17.0.20"}
        self.fixture = {"record_type": "actual-gradle-fixtures", "actual_host": "linux-x64", "selected_cases": list(w.CASE_NAMES[1:]),
                        "selected_subset": True, "bootstrap_complete": True, "maximum_gradle_invocations": 6, "total_timeout_seconds": 300,
                        "per_invocation_timeout_seconds": 90, "reserve_mib": 8192, "selected_cases_observed_as_expected": True,
                        "all_cases_observed_as_expected": False,
                        "invocation_attempts": [{"fixture": name, "mode": "bootstrap" if index == 0 else "check", "entry_root": ".",
                                                 "gradle_process_started": True, "exit_code": 0 if index < 2 else 1, "stop_reason": None}
                                                for index, name in enumerate(w.CASE_NAMES)],
                        "cases": [{"case": name, "actual_expected_result_observed": True,
                                   "result_kind": "strict-acceptance" if index == 0 else "exact-lock-state-rejection"}
                                  for index, name in enumerate(w.CASE_NAMES[1:])]}

    def test_runtime_exact_binding(self):
        self.assertTrue(w.runtime_matches(self.runtime, self.marker, "check", self.daemon))

    def test_exact_runtime_receipt_produces_candidate_not_attachment_authority(self):
        self.assertEqual(303, w.runtime_candidate_pid(self.runtime, self.marker, "check"))
        self.assertFalse(w.runtime_matches(self.runtime, self.marker, "check", {"observed": False}))

    def test_candidate_pid_requires_strict_positive_integer_not_json_lookalike(self):
        for value in (True, False, 303.0, "303", None, 1, 0, -1):
            with self.subTest(value=value):
                self.runtime["gradle_jvm_process_id"] = value
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid(self.runtime, self.marker, "check")

    def test_candidate_schema_requires_integer_not_bool_or_float(self):
        for value in (True, 1.0, "1", None, 2):
            with self.subTest(value=value):
                self.runtime["schema_version"] = value
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid(self.runtime, self.marker, "check")

    def test_candidate_receipt_requires_exact_run_and_mode(self):
        for key in ("run_id", "mode"):
            with self.subTest(key=key):
                value = {**self.runtime, key: "bootstrap"}
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid(value, self.marker, "check")
        with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
            w.runtime_candidate_pid({**self.runtime, "mode": "foreign", "run_id": "foreign"}, self.marker, "foreign")

    def test_candidate_receipt_requires_exact_build_root_and_record_type(self):
        for key, value in (("build_root", "included"), ("record_type", "build-graph"), ("gradle_version", "9.7")):
            with self.subTest(key=key):
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid({**self.runtime, key: value}, self.marker, "check")

    def test_candidate_requires_controlled_single_root_not_production_marker(self):
        for marker in ({**self.marker, "kind": "source-snapshot"}, {**self.marker, "build_roots": [".", "included"]}):
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid(self.runtime, marker, "check")

    def test_candidate_source_digest_must_match_current_exact_fixture(self):
        with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
            w.runtime_candidate_pid({**self.runtime, "source_input_digest": "b" * 64}, self.marker, "check")

    def test_candidate_digest_is_not_valid_merely_because_two_invalid_values_equal(self):
        for value in ("short", "A" * 64, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid({**self.runtime, "source_input_digest": value},
                                            {**self.marker, "source_input_digest": value}, "check")

    def test_candidate_host_must_be_actual_controlled_linux_host(self):
        for runtime, marker in (({**self.runtime, "host": "macos-arm64"}, self.marker),
                                ({**self.runtime, "host": "foreign"}, {**self.marker, "host": "foreign"})):
            with self.subTest(host=runtime["host"]):
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid(runtime, marker, "check")

    def test_candidate_runtime_java_version_is_validated_before_proc_or_attach(self):
        for value in ("21.0.20", "17.private/path", 17, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid({**self.runtime, "java_runtime_version": value}, self.marker, "check")

    def test_candidate_runtime_isolation_requires_exact_fields_and_boolean_types(self):
        for key, value in (("wrapper_client_observed", True), ("wrapper_client_observed", 0),
                           ("non_gradle_cache_use_verified", 0), ("scope", "foreign"), ("properties", {})):
            with self.subTest(key=key, value=value):
                runtime = copy.deepcopy(self.runtime)
                runtime["runtime_isolation"][key] = value
                with self.assertRaisesRegex(w.WitnessError, "invalid-runtime-receipt"):
                    w.runtime_candidate_pid(runtime, self.marker, "check")

    def test_runtime_binding_rejects_float_pid_even_when_value_equals_live_daemon(self):
        self.runtime["gradle_jvm_process_id"] = 303.0
        self.assertFalse(w.runtime_matches(self.runtime, self.marker, "check", self.daemon))

    def test_runtime_binding_never_accepts_incomplete_observation(self):
        self.assertFalse(w.runtime_matches(self.runtime, self.marker, "check",
                                          {"observed": True, "identity": {"pid": 303}}))

    def test_runtime_wrong_pid(self):
        self.runtime["gradle_jvm_process_id"] = 999
        self.assertFalse(w.runtime_matches(self.runtime, self.marker, "check", self.daemon))

    def test_runtime_missing_actual_observer(self):
        self.assertFalse(w.runtime_matches(self.runtime, self.marker, "check", {"observed": False}))

    def test_runtime_exaggerated_cache_use(self):
        self.runtime["runtime_isolation"]["non_gradle_cache_use_verified"] = True
        self.assertFalse(w.runtime_matches(self.runtime, self.marker, "check", self.daemon))

    def test_runtime_different_source_digest(self):
        self.runtime["source_input_digest"] = "b" * 64
        self.assertFalse(w.runtime_matches(self.runtime, self.marker, "check", self.daemon))

    def test_runtime_different_java_version(self):
        self.runtime["java_runtime_version"] = "17.0.19"
        self.assertFalse(w.runtime_matches(self.runtime, self.marker, "check", self.daemon))

    def test_fixture_exact_subset(self):
        self.assertTrue(w.fixture_matches(self.fixture))

    def test_fixture_any_nonzero_not_expected_rejection(self):
        self.fixture["invocation_attempts"][2]["exit_code"] = 143
        self.assertFalse(w.fixture_matches(self.fixture))

    def test_fixture_timeout_not_success(self):
        self.fixture["invocation_attempts"][2]["stop_reason"] = "timeout"
        self.assertFalse(w.fixture_matches(self.fixture))

    def test_fixture_bool_is_not_an_exit_code(self):
        self.fixture["invocation_attempts"][2]["exit_code"] = True
        self.assertFalse(w.fixture_matches(self.fixture))

    def test_fixture_wrong_reason_not_success(self):
        self.fixture["cases"][1]["result_kind"] = "generic-failure"
        self.assertFalse(w.fixture_matches(self.fixture))

    def test_fixture_cannot_claim_all_cases(self):
        self.fixture["all_cases_observed_as_expected"] = True
        self.assertFalse(w.fixture_matches(self.fixture))

    def test_fixture_missing_invocation(self):
        self.fixture["invocation_attempts"].pop()
        self.assertFalse(w.fixture_matches(self.fixture))

    def test_fixture_absent_result(self):
        self.assertFalse(w.fixture_matches(None))


class OuterLoopDiagnosticsTests(TemporaryTests):
    """Modeled loop outcomes only: all identity/proc/attach operations are mocked."""

    def exercise(self, *, children=None, candidate_failures=None, observation_failures=None,
                 late_children_failure=None, two_polls=False, all_cases=False,
                 inventory_complete=True, missing_runtime=False, runtime_overrides=None,
                 runtime_changed_during_observation=False):
        destination = self.root / "modeled-suite"
        destination.mkdir()
        output = self.root / "modeled-witness.json"
        names = w.CASE_NAMES if all_cases else ("bootstrap",)
        markers, clients, daemons = {}, {}, {}
        for index, name in enumerate(names):
            mode = "bootstrap" if name == "bootstrap" else "check"
            workspace = destination / name
            run = workspace / f"build/dependency-integrity/{mode}"
            (run / "graphs/root").mkdir(parents=True)
            markers[name] = {**self.marker, "host": "linux-x64"}
            pid, daemon_pid = 202 + index * 10, 303 + index * 10
            clients[name] = w.ProcessIdentity(pid, self.suite.pid, pid, pid, 101 + index * 10)
            daemons[name] = w.ProcessIdentity(daemon_pid, pid, pid, pid, 102 + index * 10)
            (run / "launched-process.json").write_bytes(m.json_bytes({"schema_version": 1,
                "record_type": "launched-command-process", "pid": pid, "process_group": pid, "java_identity_observed": False}))
            runtime = {"schema_version": 1,
                "record_type": "gradle-runtime-observation", "run_id": mode, "mode": mode, "build_root": ".",
                "source_input_digest": "a" * 64, "host": "linux-x64", "gradle_version": "9.7.1",
                "java_runtime_version": "17.0.20", "gradle_jvm_process_id": daemon_pid,
                "runtime_isolation": copy.deepcopy(m.RUNTIME_ISOLATION)}
            runtime.update(runtime_overrides or {})
            if not missing_runtime:
                (run / "graphs/root/runtime.json").write_bytes(m.json_bytes(runtime))
        for path in (self.jdk / "bin/jcmd", self.gradle / "lib/gradle-gradle-cli-main-9.7.1.jar",
                     self.gradle / "lib/gradle-daemon-main-9.7.1.jar"):
            path.write_text("NOT EXECUTED: synthetic offline loop fixture\n")
        fixture = {"record_type": "actual-gradle-fixtures", "actual_host": "linux-x64",
            "selected_cases": list(w.CASE_NAMES[1:]), "selected_subset": True, "bootstrap_complete": True,
            "maximum_gradle_invocations": 6, "total_timeout_seconds": 300, "per_invocation_timeout_seconds": 90,
            "reserve_mib": 8192, "selected_cases_observed_as_expected": all_cases, "all_cases_observed_as_expected": False,
            "invocation_attempts": [{"fixture": name, "mode": "bootstrap" if index == 0 else "check", "entry_root": ".",
                                     "gradle_process_started": True, "exit_code": 0 if index < 2 else 1, "stop_reason": None}
                                    for index, name in enumerate(names)],
            "cases": [{"case": name, "actual_expected_result_observed": True,
                       "result_kind": "strict-acceptance" if index == 0 else "exact-lock-state-rejection"}
                      for index, name in enumerate(names[1:])]}
        final = destination / "fixture-results.json"
        if not two_polls:
            final.write_bytes(m.json_bytes(fixture))

        def finish_on_first_sleep(_):
            self.assertFalse(final.exists(), "Only the single modeled poll boundary is expected")
            final.write_bytes(m.json_bytes(fixture))

        enumeration_calls = 0

        def owned(client):
            nonlocal enumeration_calls
            enumeration_calls += 1
            if enumeration_calls == 2 and late_children_failure is not None:
                raise late_children_failure
            name = next(name for name, identity in clients.items() if identity == client)
            pids = [daemons[name].pid] if children is None else children
            return w.ChildInventory(tuple(pids), complete=inventory_complete)

        def check(pid, *, role, workspace, **_):
            name = workspace.name
            if role == "client":
                self.assertEqual(clients[name].pid, pid)
                return clients[name]
            failure = (candidate_failures or {}).get(pid)
            if failure is not None:
                raise failure
            expected = daemons[name]
            return w.ProcessIdentity(pid, expected.parent, expected.group, expected.session, expected.start_ticks)

        def observe(pid, *, role, workspace, **_):
            failure = (observation_failures or {}).get(role)
            if failure is not None:
                raise failure
            identity = clients[workspace.name] if role == "client" else daemons[workspace.name]
            self.assertEqual(identity.pid, pid)
            if role == "daemon" and runtime_changed_during_observation:
                mode = "bootstrap" if workspace.name == "bootstrap" else "check"
                path = workspace / f"build/dependency-integrity/{mode}/graphs/root/runtime.json"
                value = json.loads(path.read_text())
                value["untrusted_added_field"] = "changed while observing"
                path.write_bytes(m.json_bytes(value))
            return {"observed": True, "identity": identity.public(), "java_runtime_version": "17.0.20",
                    "diagnostic": {"exit_code": 0, "test_only": "Synthetic, no actual jcmd"}}

        with ExitStack() as stack:
            for object_, name, options in (
                (m, "host_key", {"return_value": "linux-x64"}),
                (w, "checkpoint_files", {"return_value": {str(index): "a" * 64 for index in range(6)}}),
                (w, "observer_files", {"return_value": {"synthetic": "b" * 64}}),
                (w, "check_suite", {"return_value": self.suite}),
                (w, "identity", {"return_value": self.suite}),
                (driver, "load_workspace", {"side_effect": lambda workspace: markers[workspace.name]}),
                (w, "check_java", {"side_effect": check}),
                (w, "owned_children", {"side_effect": owned}),
                (w.time, "sleep", {"side_effect": finish_on_first_sleep}),
                (w, "proc_bytes", {"side_effect": AssertionError("No real proc probe in modeled loop test")}),
                (w.subprocess, "Popen", {"side_effect": AssertionError("No process launch in modeled loop test")}),
            ):
                stack.enter_context(mock.patch.object(object_, name, **options))
            observations = stack.enter_context(mock.patch.object(w, "observe_java", side_effect=observe))
            result = w.witness(destination=destination, output=output, suite_pid=self.suite.pid,
                               jdk_home=self.jdk, gradle_home=self.gradle)
        self.assertEqual(result, json.loads(output.read_text()))
        self.assertNotIn("NEVER_ARCHIVE_PRIVATE_SENTINEL", json.dumps(result))
        return result, observations.call_args_list

    def test_rejected_candidate_has_reason_but_is_never_attached(self):
        result, observations = self.exercise(candidate_failures={303: w.WitnessError("daemon-ancestry-mismatch")})
        state = result["cases"][0]
        self.assertEqual(1, state["validation_reason_counts"]["daemon-candidate"]["daemon-ancestry-mismatch"])
        self.assertEqual({"observed": False}, state["daemon"])
        self.assertEqual(["client"], [call.kwargs["role"] for call in observations])
        self.assertFalse(result["fixture_and_runtime_selected_subset_complete"])

    def test_multiple_rejected_candidates_keep_distinct_enum_counts(self):
        result, observations = self.exercise(children=[303, 304], candidate_failures={
            303: w.WitnessError("daemon-ancestry-mismatch"), 304: w.WitnessError("gradle-daemon-unknown-option")})
        self.assertEqual({"daemon-ancestry-mismatch": 1, "gradle-daemon-unknown-option": 1},
                         result["cases"][0]["validation_reason_counts"]["daemon-candidate"])
        self.assertEqual(1, len(observations))

    def test_arbitrary_candidate_error_exports_category_only(self):
        result, observations = self.exercise(candidate_failures={303: ValueError("NEVER_ARCHIVE_PRIVATE_SENTINEL")})
        self.assertEqual({"input-value-invalid": 1}, result["cases"][0]["validation_reason_counts"]["daemon-candidate"])
        self.assertEqual(1, len(observations))

    def test_empty_owned_child_polls_are_not_diagnostic_retries(self):
        result, observations = self.exercise(children=[], missing_runtime=True, two_polls=True)
        self.assertEqual({"no-owned-child-at-poll": 2, "no-eligible-daemon-at-poll": 2},
                         result["cases"][0]["validation_reason_counts"]["daemon-children"])
        self.assertEqual(1, len(observations))
        self.assertEqual(1, result["observation_attempts"])

    def test_exact_runtime_candidate_is_observed_when_children_files_unavailable(self):
        result, observations = self.exercise(children=[], inventory_complete=False, all_cases=True)
        self.assertTrue(result["fixture_and_runtime_selected_subset_complete"])
        self.assertEqual(12, len(observations))
        for state in result["cases"]:
            self.assertEqual({"client-children-unavailable": 1}, state["validation_reason_counts"]["daemon-children"])
            self.assertFalse(state["client_children_inventory_complete"])
            self.assertEqual(["exact-fixture-runtime"], state["daemon_candidate_sources"])

    def test_known_empty_children_can_use_exact_runtime_candidate_once(self):
        result, observations = self.exercise(children=[], two_polls=True)
        self.assertEqual(["client", "daemon"], [call.kwargs["role"] for call in observations])
        self.assertTrue(result["cases"][0]["runtime_receipt_matched"])
        self.assertEqual(1, result["cases"][0]["validation_reason_counts"]["daemon-children"]["no-owned-child-at-poll"])

    def test_receipt_plus_same_child_is_deduplicated_before_eligibility(self):
        result, observations = self.exercise(children=[303])
        self.assertEqual(2, len(observations))
        self.assertEqual(["exact-fixture-runtime", "owned-client-child"], result["cases"][0]["daemon_candidate_sources"])

    def test_receipt_and_different_eligible_child_are_ambiguous_not_arbitrary_choice(self):
        result, observations = self.exercise(children=[304])
        self.assertEqual(1, len(observations))
        self.assertEqual({"ambiguous-gradle-daemon": 1}, result["cases"][0]["validation_reason_counts"]["daemon-children"])
        self.assertFalse(result["cases"][0]["daemon"]["observed"])

    def test_partial_inventory_does_not_discard_known_child_to_avoid_ambiguity(self):
        result, observations = self.exercise(children=[304], inventory_complete=False)
        self.assertEqual(1, len(observations))
        self.assertEqual({"client-children-unavailable": 1, "ambiguous-gradle-daemon": 1},
                         result["cases"][0]["validation_reason_counts"]["daemon-children"])
        self.assertFalse(result["cases"][0]["daemon"]["observed"])

    def test_receipt_pid_still_must_pass_live_identity_gates_before_attach(self):
        result, observations = self.exercise(children=[], inventory_complete=False,
            runtime_overrides={"gradle_jvm_process_id": 999},
            candidate_failures={999: w.WitnessError("daemon-ancestry-mismatch")})
        self.assertEqual(1, len(observations))
        self.assertEqual({"daemon-ancestry-mismatch": 1}, result["cases"][0]["validation_reason_counts"]["daemon-candidate"])
        self.assertFalse(result["cases"][0]["daemon"]["observed"])

    def test_foreign_runtime_receipt_is_not_candidate_when_children_unavailable(self):
        result, observations = self.exercise(children=[], inventory_complete=False,
                                             runtime_overrides={"source_input_digest": "b" * 64})
        self.assertEqual(1, len(observations))
        self.assertEqual({"invalid-runtime-receipt": 1}, result["cases"][0]["validation_reason_counts"]["runtime-candidate"])
        self.assertFalse(result["cases"][0]["runtime_receipt_matched"])

    def test_invalid_runtime_pid_cannot_enter_live_proc_candidate_validation(self):
        result, observations = self.exercise(children=[], inventory_complete=False,
                                             runtime_overrides={"gradle_jvm_process_id": True})
        self.assertEqual(1, len(observations))
        self.assertNotIn("daemon-candidate", result["cases"][0]["validation_reason_counts"])
        self.assertFalse(result["cases"][0]["daemon"]["observed"])

    def test_child_can_be_observed_early_but_no_receipt_is_never_complete_binding(self):
        result, observations = self.exercise(missing_runtime=True)
        self.assertEqual(["client", "daemon"], [call.kwargs["role"] for call in observations])
        self.assertFalse(result["cases"][0]["runtime_receipt_matched"])
        self.assertFalse(result["fixture_and_runtime_selected_subset_complete"])

    def test_candidate_receipt_bytes_must_remain_bound_after_observation(self):
        result, observations = self.exercise(children=[], runtime_changed_during_observation=True)
        self.assertEqual(2, len(observations))
        self.assertTrue(result["cases"][0]["daemon"]["observed"])
        self.assertFalse(result["cases"][0]["runtime_receipt_matched"])
        self.assertFalse(result["fixture_and_runtime_selected_subset_complete"])

    def test_later_process_disappearance_does_not_erase_prior_candidate_reason(self):
        result, observations = self.exercise(candidate_failures={303: w.WitnessError("daemon-ancestry-mismatch")},
            late_children_failure=FileNotFoundError("NEVER_ARCHIVE_PRIVATE_SENTINEL"), two_polls=True)
        state = result["cases"][0]
        self.assertEqual("input-disappeared", state["last_unverified_reason"])
        self.assertEqual(1, state["validation_reason_counts"]["daemon-candidate"]["daemon-ancestry-mismatch"])
        self.assertEqual(1, state["validation_reason_counts"]["daemon-children"]["input-disappeared"])
        self.assertEqual(1, len(observations))

    def test_failed_daemon_diagnostic_is_counted_once_not_retried(self):
        result, observations = self.exercise(observation_failures={"daemon": w.WitnessError("diagnostic-timeout")}, two_polls=True)
        state = result["cases"][0]
        self.assertEqual({"diagnostic-timeout": 1}, state["validation_reason_counts"]["daemon-observation"])
        self.assertTrue(state["daemon"]["attempted"])
        self.assertFalse(state["daemon"]["observed"])
        self.assertEqual(["client", "daemon"], [call.kwargs["role"] for call in observations])
        self.assertFalse(result["fixture_and_runtime_selected_subset_complete"])

    def test_failed_client_diagnostic_is_counted_once_not_retried(self):
        result, observations = self.exercise(observation_failures={"client": ValueError("NEVER_ARCHIVE_PRIVATE_SENTINEL")}, two_polls=True)
        state = result["cases"][0]
        self.assertEqual({"input-value-invalid": 1}, state["validation_reason_counts"]["client-observation"])
        self.assertFalse(state["client"]["observed"])
        self.assertEqual(["client", "daemon"], [call.kwargs["role"] for call in observations])
        self.assertFalse(result["fixture_and_runtime_selected_subset_complete"])

    def test_two_eligible_daemons_remain_ambiguous_and_are_not_attached(self):
        result, observations = self.exercise(children=[303, 304])
        state = result["cases"][0]
        self.assertEqual({"ambiguous-gradle-daemon": 1}, state["validation_reason_counts"]["daemon-children"])
        self.assertEqual({"observed": False}, state["daemon"])
        self.assertEqual(1, len(observations))

    def test_full_synthetic_success_still_requires_twelve_observations_and_bindings(self):
        result, observations = self.exercise(all_cases=True)
        self.assertTrue(result["fixture_and_runtime_selected_subset_complete"])
        self.assertTrue(result["all_six_runtime_observations_complete"])
        self.assertEqual(12, len(observations))
        self.assertTrue(all(not state["validation_reason_counts"] for state in result["cases"]))


class PipeBoundsTests(unittest.TestCase):
    def run_child(self, code, timeout=2):
        command = [sys.executable, "-c", code]
        original = subprocess.Popen
        processes = []

        def spawn(*args, **kwargs):
            child = original(*args, **kwargs)
            processes.append(child)
            return child

        with mock.patch.object(w.subprocess, "Popen", side_effect=spawn):
            try:
                return w.diagnostic(command, {"PATH": os.defpath}, timeout)
            finally:
                self.assertEqual(1, len(processes))
                self.assertIsNotNone(processes[0].poll(), "Owned Python pipe fixture must be reaped")

    def test_scoped_command_capture_no_stderr_export(self):
        raw, result = self.run_child("import sys; print('synthetic stdout'); print('PRIVATE_STDERR_SENTINEL', file=sys.stderr)")
        self.assertEqual(b"synthetic stdout\n", raw)
        self.assertFalse(result["raw_stderr_archived"])
        self.assertNotIn("PRIVATE_STDERR_SENTINEL", json.dumps(result))

    def test_pipe_timeout_reaps_only_owned_child(self):
        began = time.monotonic()
        with self.assertRaisesRegex(w.WitnessError, "diagnostic-timeout"):
            self.run_child("import time; time.sleep(10)", timeout=0.05)
        self.assertLess(time.monotonic() - began, 3)

    def test_output_limit_reaps_only_owned_child(self):
        with self.assertRaisesRegex(w.WitnessError, "diagnostic-output-limit"):
            self.run_child("import sys,time; sys.stdout.write('x'*262144); sys.stdout.flush(); time.sleep(10)")

    def test_nonzero_child_not_success(self):
        with self.assertRaisesRegex(w.WitnessError, "diagnostic-nonzero"):
            self.run_child("raise SystemExit(13)")

    def test_cli_suppresses_arbitrary_exception_body(self):
        output = io.StringIO()
        with mock.patch.object(w, "witness", side_effect=ValueError("NEVER_PRINT_PRIVATE_SENTINEL")), mock.patch("sys.stdout", output):
            status = w.main(["--destination", "/fixture", "--output", "/witness.json", "--suite-pid", "303",
                             "--jdk-home", "/jdk17", "--gradle-home", "/gradle-9.7.1"])
        self.assertEqual(1, status)
        self.assertNotIn("NEVER_PRINT_PRIVATE_SENTINEL", output.getvalue())

    def test_cli_suppresses_unknown_witness_error_body(self):
        output = io.StringIO()
        with mock.patch.object(w, "witness", side_effect=w.WitnessError("NEVER_PRINT_PRIVATE_SENTINEL")), mock.patch("sys.stdout", output):
            status = w.main(["--destination", "/fixture", "--output", "/witness.json", "--suite-pid", "303",
                             "--jdk-home", "/jdk17", "--gradle-home", "/gradle-9.7.1"])
        self.assertEqual(1, status)
        self.assertEqual("other-validation-failure", json.loads(output.getvalue())["reason"])


if __name__ == "__main__":
    unittest.main()
