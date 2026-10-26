"""Offline observer tests: synthetic /proc/jcmd data and tiny owned Python pipes.

No Gradle, jcmd, Java, registry or network is invoked by this suite.
"""
from __future__ import annotations

import copy
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
            self.assertEqual([303, 304], w.owned_children(client))

    def test_children_de_duplicate_owned_threads(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", return_value=client), \
                mock.patch.object(Path, "iterdir", return_value=iter([Path("202"), Path("212")])), \
                mock.patch.object(w, "proc_bytes", return_value=b"303 "):
            self.assertEqual([303], w.owned_children(client))

    def test_child_enumeration_identity_change(self):
        client = w.ProcessIdentity(202, 101, 202, 202, 1000)
        with mock.patch.object(w, "identity", side_effect=[client, w.ProcessIdentity(202, 101, 202, 202, 1001)]), \
                mock.patch.object(Path, "iterdir", return_value=iter([])):
            with self.assertRaisesRegex(w.WitnessError, "client-children-identity-mismatch"):
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
        self.marker = {"source_input_digest": "a" * 64, "host": "linux-x64"}
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


if __name__ == "__main__":
    unittest.main()
