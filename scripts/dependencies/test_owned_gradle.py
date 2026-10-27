"""Offline ownership regressions. No Gradle, Java, jcmd or registry is invoked.

Synthetic PID/fd proofs and private directory entries test the controller, not
native/library behavior. The separately scheduled real fixture exercises the
original detached-daemon leak on timeout, interruption and normal completion.
"""
from __future__ import annotations

from contextlib import ExitStack
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest import mock

import gradle_process as g
import gradle_fixtures as f
import integrity as d
import integrity_model as m
import owned_gradle as o
import owned_cleanup_fixtures as actual


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nativecmpkit-owner-offline-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "project"
        self.workspace.mkdir()
        self.jdk = self.root / "jdk17"
        self.gradle = self.root / "gradle-9.7.1"
        for path in (self.jdk / "bin/java", self.gradle / "bin/gradle", self.gradle / "lib/gradle-core-api-9.7.1.jar"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("NOT EXECUTED\n")
        for relative in set(m.JVM_PRIVATE_PATHS.values()) | set(m.ENV_PRIVATE_PATHS.values()):
            (self.workspace / relative).mkdir(parents=True, exist_ok=True)
        _, env, options = g.private_values(self.workspace)
        self.env = {**env, "JAVA_HOME": str(self.jdk), "JAVA_TOOL_OPTIONS": options,
                    "PATH": str(self.jdk / "bin") + ":/usr/bin"}
        self.command = [str(self.gradle / "bin/gradle"), "nativeCmpkitDependencyGraph", "--no-daemon"]
        self.owner = o.OwnedGradle(self.command, self.workspace, self.env, self.gradle)
        self.controller = g.ProcessIdentity(101, 100, 101, 101, 100)
        self.client = g.ProcessIdentity(202, 101, 202, 202, 101)
        self.daemon = g.ProcessIdentity(303, 202, 303, 303, 102)
        self.owner.controller = self.controller
        self.owner.client = o.Lease(self.client, 88, "client", java_verified=True)

    def client_command(self):
        return [*g.client_prefix(self.jdk, self.gradle), *self.command[1:]]

    def daemon_command(self):
        return [str(self.jdk / "bin/java"), "-Xmx512m", "-cp",
                str(self.gradle / "lib/gradle-daemon-main-9.7.1.jar"),
                f"-javaagent:{self.gradle}/lib/agents/gradle-instrumentation-agent-9.7.1.jar",
                g.DAEMON_MAIN, "9.7.1"]

    def check(self, role="daemon", *, record=None, argv=None, env=None, exe=None, cwd=None, cleanup=False):
        record = record or (self.client if role == "client" else self.daemon)
        argv = argv or (self.client_command() if role == "client" else self.daemon_command())
        raw_env = "".join(f"{k}={v}\0" for k, v in (self.env if env is None else env).items()).encode()
        records = {101: self.controller, 202: self.client, record.pid: record}
        with mock.patch.object(os, "getpid", return_value=101), \
                mock.patch.object(o, "identity", side_effect=lambda pid: records[pid]), \
                mock.patch.object(o, "exited", return_value=False), \
                mock.patch.object(os, "readlink", side_effect=lambda p: str(exe or self.jdk / "bin/java") if p.endswith("/exe") else str(cwd or self.workspace)), \
                mock.patch.object(o, "proc_bytes", side_effect=lambda pid, leaf: raw_env if leaf == "environ" else ("\0".join(argv) + "\0").encode()):
            return self.owner._java(record.pid, role, cleanup=cleanup)

    def close_directory(self):
        if self.owner.directory_handle is not None:
            os.close(self.owner.directory_handle)
            self.owner.directory_handle = None


class LiveProofTests(Fixture):
    def test_exact_client_is_verified(self):
        self.assertEqual(self.client, self.check("client"))

    def test_exact_self_session_daemon_is_verified(self):
        self.assertEqual(self.daemon, self.check())

    def test_exact_inherited_session_daemon_is_verified(self):
        record = g.ProcessIdentity(303, 202, 202, 202, 102)
        self.assertEqual(record, self.check(record=record))

    def test_foreign_daemon_parent_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "daemon-ancestry-mismatch"):
            self.check(record=g.ProcessIdentity(303, 999, 303, 303, 102))

    def test_foreign_group_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "daemon-ancestry-mismatch"):
            self.check(record=g.ProcessIdentity(303, 202, 404, 303, 102))

    def test_foreign_session_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "daemon-ancestry-mismatch"):
            self.check(record=g.ProcessIdentity(303, 202, 303, 404, 102))

    def test_preexisting_start_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "daemon-ancestry-mismatch"):
            self.check(record=g.ProcessIdentity(303, 202, 303, 303, 99))

    def test_own_reparenting_is_allowed_only_during_cleanup(self):
        record = g.ProcessIdentity(303, 101, 303, 303, 102)
        with self.assertRaisesRegex(g.WitnessError, "daemon-ancestry-mismatch"):
            self.check(record=record)
        self.assertEqual(record, self.check(record=record, cleanup=True))

    def test_unverified_client_cannot_authorize_a_daemon(self):
        self.owner.client.java_verified = False
        with self.assertRaisesRegex(g.WitnessError, "owned-live-client-required"):
            self.check()

    def test_foreign_jdk_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "java-executable-mismatch"):
            self.check(exe=Path("/foreign/bin/java"))

    def test_foreign_cwd_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "java-cwd-outside-candidate"):
            self.check(cwd=self.root)

    def test_client_nested_cwd_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "owned-client-changed"):
            self.check("client", cwd=self.workspace / ".dependency-cache")

    def test_client_extra_application_argument_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "gradle-client-command-mismatch"):
            self.check("client", argv=[*self.client_command(), "--scan"])

    def test_daemon_unknown_option_is_rejected(self):
        args = self.daemon_command()
        args.insert(-2, "-Djava.system.class.loader=foreign.Loader")
        with self.assertRaisesRegex(g.WitnessError, "gradle-daemon-unknown-option"):
            self.check(argv=args)

    def test_daemon_duplicate_classpath_is_rejected(self):
        args = self.daemon_command()
        args[1:1] = ["-cp", "/foreign/fake.jar"]
        with self.assertRaisesRegex(g.WitnessError, "gradle-daemon-classpath-mismatch"):
            self.check(argv=args)

    def test_daemon_duplicate_heap_is_rejected(self):
        args = self.daemon_command()
        args.insert(-2, "-Xmx2048m")
        with self.assertRaisesRegex(g.WitnessError, "gradle-daemon-duplicate-option"):
            self.check(argv=args)

    def test_changed_private_environment_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "private-environment-mismatch"):
            self.check(env={**self.env, "HOME": "/foreign"})

    def test_inherited_jvm_override_is_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "inherited-jvm-override"):
            self.check(env={**self.env, "GRADLE_OPTS": "-Dunsafe=true"})

    def test_wrong_java_options_are_rejected(self):
        with self.assertRaisesRegex(g.WitnessError, "jvm-environment-mismatch"):
            self.check(env={**self.env, "JAVA_TOOL_OPTIONS": "-Duser.home=/foreign"})


class DiscoveryTests(Fixture):
    def setUp(self):
        super().setUp()
        self.owner.client = None  # These tests own no actual or synthetic fd.
        self.directory = self.owner.daemon_directory
        self.directory.mkdir(parents=True)
        self.addCleanup(self.close_directory)

    def test_discovery_does_not_read_log_bodies_or_signal(self):
        (self.directory / "daemon-303.out.log").write_text("UNTRUSTED_DO_NOT_READ")
        with mock.patch.object(Path, "open", side_effect=AssertionError("Log body read")), \
                mock.patch.object(os, "pidfd_open") as pin, mock.patch.object(signal, "pidfd_send_signal") as send:
            self.assertEqual(["daemon-303.out.log"], [n for n, _ in self.owner._directory_files()])
        pin.assert_not_called()
        send.assert_not_called()

    def test_non_pid_names_are_not_candidates(self):
        for name in ("registry.bin", "daemon-0.out.log", "daemon-303.out.log.backup", "arbitrary.txt"):
            (self.directory / name).write_text("NOT READ")
        self.assertEqual([], self.owner._directory_files())

    def test_symlink_log_is_rejected(self):
        target = self.root / "foreign.log"
        target.write_text("NOT READ")
        (self.directory / "daemon-303.out.log").symlink_to(target)
        with self.assertRaisesRegex(g.WitnessError, "owned-daemon-log-not-private-regular"):
            self.owner._directory_files()

    def test_hardlink_log_is_rejected(self):
        target = self.root / "foreign.log"
        target.write_text("NOT READ")
        os.link(target, self.directory / "daemon-303.out.log")
        with self.assertRaisesRegex(g.WitnessError, "owned-daemon-log-not-private-regular"):
            self.owner._directory_files()

    def test_directory_entry_count_is_bounded(self):
        for n in range(o.MAX_DIRECTORY_ENTRIES + 1):
            (self.directory / f"ignored-{n}").touch()
        with self.assertRaisesRegex(g.WitnessError, "owned-daemon-directory-limit"):
            self.owner._directory_files()

    def test_daemon_log_count_is_bounded(self):
        for n in range(1, o.MAX_DAEMONS + 2):
            (self.directory / f"daemon-{n}.out.log").touch()
        with self.assertRaisesRegex(g.WitnessError, "owned-daemon-log-limit"):
            self.owner._directory_files()

    def test_replaced_directory_is_rejected(self):
        self.owner._directory_files()
        self.directory.rename(self.directory.with_name("replaced"))
        self.directory.mkdir()
        with self.assertRaisesRegex(g.WitnessError, "owned-daemon-directory-replaced"):
            self.owner._directory_files()

    def test_disappeared_directory_is_rejected(self):
        self.owner._directory_files()
        self.directory.rmdir()
        with self.assertRaisesRegex(g.WitnessError, "owned-daemon-directory-disappeared"):
            self.owner._directory_files()


class PinAndSignalTests(Fixture):
    def candidates(self, extra=False):
        result = [("daemon-303.out.log", (1, 3, 0, 0o100600, 1))]
        if extra:
            result += [("daemon-304.out.log", (1, 4, 0, 0o100600, 1))]
        return result

    def test_preexisting_log_name_never_nominates_a_process(self):
        self.owner.baseline_names = {"daemon-303.out.log"}
        with mock.patch.object(self.owner, "_directory_files", return_value=self.candidates()), \
                mock.patch.object(self.owner, "_java") as check, mock.patch.object(os, "pidfd_open") as pin:
            self.owner.poll()
        check.assert_not_called()
        pin.assert_not_called()

    def test_fresh_candidate_requires_pre_and_post_pin_proofs(self):
        with mock.patch.object(self.owner, "_directory_files", return_value=self.candidates()), \
                mock.patch.object(self.owner, "_java", return_value=self.daemon) as check, \
                mock.patch.object(o, "exited", return_value=False), \
                mock.patch.object(os, "pidfd_open", return_value=89) as pin, \
                mock.patch.object(signal, "pidfd_send_signal") as send:
            self.owner.poll()
        self.assertEqual(2, check.call_count)
        pin.assert_called_once_with(303, 0)
        send.assert_not_called()
        self.assertEqual(self.daemon, self.owner.daemons[303].process)

    def test_changed_post_pin_identity_closes_unadmitted_fd(self):
        other = g.ProcessIdentity(303, 202, 303, 303, 999)
        with mock.patch.object(self.owner, "_directory_files", return_value=self.candidates()), \
                mock.patch.object(self.owner, "_java", side_effect=[self.daemon, other]), \
                mock.patch.object(o, "exited", return_value=False), \
                mock.patch.object(os, "pidfd_open", return_value=89), mock.patch.object(os, "close") as close:
            with self.assertRaisesRegex(g.WitnessError, "owned-daemon-pin-changed"):
                self.owner.poll()
        close.assert_called_once_with(89)
        self.assertEqual({}, self.owner.daemons)

    def test_changed_log_identity_closes_unadmitted_fd(self):
        with mock.patch.object(self.owner, "_directory_files", side_effect=[self.candidates(), [("daemon-303.out.log", (9, 9, 0, 0o100600, 1))]]), \
                mock.patch.object(self.owner, "_java", return_value=self.daemon), \
                mock.patch.object(o, "exited", return_value=False), \
                mock.patch.object(os, "pidfd_open", return_value=89), mock.patch.object(os, "close") as close:
            with self.assertRaisesRegex(g.WitnessError, "owned-daemon-pin-changed"):
                self.owner.poll()
        close.assert_called_once_with(89)

    def test_ambiguity_keeps_all_proven_leases_for_cleanup(self):
        records = {303: self.daemon, 304: g.ProcessIdentity(304, 202, 304, 304, 103)}
        with mock.patch.object(self.owner, "_directory_files", return_value=self.candidates(extra=True)), \
                mock.patch.object(self.owner, "_java", side_effect=lambda pid, role: records[pid]), \
                mock.patch.object(o, "exited", return_value=False), \
                mock.patch.object(os, "pidfd_open", side_effect=[89, 90]), \
                mock.patch.object(signal, "pidfd_send_signal") as send:
            with self.assertRaisesRegex(g.WitnessError, "ambiguous-gradle-daemon"):
                self.owner.poll()
        self.assertEqual({303, 304}, set(self.owner.daemons))
        send.assert_not_called()

    def test_live_signal_uses_exact_pinned_fd_not_group_or_pid(self):
        lease = o.Lease(self.daemon, 89, "daemon", java_verified=True)
        with mock.patch.object(o, "exited", return_value=False), \
                mock.patch.object(self.owner, "_java", return_value=self.daemon), \
                mock.patch.object(signal, "pidfd_send_signal") as send, \
                mock.patch.object(os, "killpg", side_effect=AssertionError("Group signal forbidden")):
            self.owner._signal(lease, signal.SIGTERM)
        send.assert_called_once_with(89, signal.SIGTERM)
        self.assertTrue(lease.term_sent)

    def test_exited_pidfd_never_signals_reused_numeric_pid(self):
        lease = o.Lease(self.daemon, 89, "daemon", java_verified=True)
        with mock.patch.object(o, "exited", return_value=True), \
                mock.patch.object(self.owner, "_java") as check, mock.patch.object(signal, "pidfd_send_signal") as send:
            self.owner._signal(lease, signal.SIGTERM)
        check.assert_not_called()
        send.assert_not_called()

    def test_failed_live_revalidation_never_escalates_to_kill(self):
        lease = o.Lease(self.daemon, 89, "daemon", java_verified=True)
        with mock.patch.object(o, "exited", return_value=False), \
                mock.patch.object(self.owner, "_java", side_effect=g.WitnessError("java-command-mismatch")), \
                mock.patch.object(signal, "pidfd_send_signal") as send:
            self.owner._signal(lease, signal.SIGTERM)
            self.owner._signal(lease, signal.SIGKILL)
        send.assert_not_called()
        self.assertFalse(lease.signal_permitted)
        self.assertIn("owned-signal-revalidation-failed", self.owner.errors)

    def test_start_pin_changed_closes_fd_before_fallback_cleanup(self):
        self.owner.client = None
        process = mock.Mock(pid=202)
        other = g.ProcessIdentity(202, 101, 202, 202, 999)
        with mock.patch.object(os, "getpid", return_value=101), \
                mock.patch.object(o, "identity", side_effect=[self.client, other]), \
                mock.patch.object(o, "exited", return_value=False), \
                mock.patch.object(os, "pidfd_open", return_value=88), mock.patch.object(os, "close") as close:
            with self.assertRaisesRegex(g.WitnessError, "owned-launcher-pin-changed"):
                self.owner.start(process)
        close.assert_called_once_with(88)
        self.assertIs(process, self.owner.process)


class CleanupTests(Fixture):
    def run_cleanup(self, *, absent=True, wait_failure=None, alive=False, cleanup_error=None):
        self.owner.daemons = {303: o.Lease(self.daemon, 89, "daemon", java_verified=True)}
        self.owner.process = mock.Mock(pid=202)
        self.owner.process.poll.return_value = 143
        self.owner.previous_subreaper = 0
        self.owner.previous_signals = {signal.SIGINT: signal.default_int_handler, signal.SIGTERM: signal.SIG_DFL}
        with ExitStack() as stack:
            send = stack.enter_context(mock.patch.object(self.owner, "_signal", side_effect=cleanup_error))
            stack.enter_context(mock.patch.object(self.owner, "_wait_until"))
            stack.enter_context(mock.patch.object(o, "exited", return_value=not alive))
            wait = stack.enter_context(mock.patch.object(os, "waitpid", return_value=(303, 0), side_effect=wait_failure))
            close = stack.enter_context(mock.patch.object(os, "close"))
            signals = stack.enter_context(mock.patch.object(signal, "signal"))
            sub = stack.enter_context(mock.patch.object(self.owner, "_subreaper", return_value=0))
            stack.enter_context(mock.patch.object(Path, "exists", return_value=not absent))
            result = self.owner.cleanup()
        return result, send, wait, close, signals, sub

    def test_cleanup_reaps_only_exact_adopted_daemon_and_popen_child(self):
        result, _, wait, close, _, sub = self.run_cleanup()
        self.assertTrue(result["complete"])
        wait.assert_called_once_with(303, os.WNOHANG)
        self.owner.process.wait.assert_called_once()
        self.assertEqual([mock.call(89), mock.call(88)], close.call_args_list)
        sub.assert_called_once_with(0)
        self.assertEqual("exact-adopted-daemon-reaped", result["daemons"][0]["wait_status"])

    def test_already_parent_reaped_daemon_requires_actual_absence(self):
        result, _, _, _, _, _ = self.run_cleanup(wait_failure=ChildProcessError())
        self.assertTrue(result["complete"])
        self.assertEqual("not-waitable-by-controller", result["daemons"][0]["wait_status"])

    def test_pid_absence_failure_never_succeeds(self):
        result, _, _, _, _, _ = self.run_cleanup(absent=False)
        self.assertFalse(result["complete"])
        self.assertIn("owned-process-absence-unverified", result["errors"])

    def test_running_process_never_succeeds(self):
        result, _, wait, close, _, _ = self.run_cleanup(alive=True)
        self.assertFalse(result["complete"])
        wait.assert_not_called()
        self.assertEqual(2, close.call_count)
        self.assertIn("owned-process-still-running", result["errors"])

    def test_cleanup_error_still_closes_and_restores_leases(self):
        result, _, _, close, signals, sub = self.run_cleanup(cleanup_error=ValueError())
        self.assertFalse(result["complete"])
        self.assertEqual(2, close.call_count)
        self.assertTrue(result["temporary_subreaper_restored"])
        self.assertTrue(result["signal_handlers_restored"])
        self.assertEqual(4, signals.call_count)
        sub.assert_called_once_with(0)

    def test_cleanup_is_idempotent_and_never_resignals(self):
        first, _, _, _, _, _ = self.run_cleanup()
        with mock.patch.object(signal, "pidfd_send_signal") as send, mock.patch.object(os, "close") as close:
            self.assertIs(first, self.owner.cleanup())
        send.assert_not_called()
        close.assert_not_called()

    def test_no_daemon_or_client_proof_is_not_success(self):
        self.owner.client = None
        with mock.patch.object(signal, "pidfd_send_signal") as send:
            result = self.owner.cleanup()
        self.assertFalse(result["complete"])
        send.assert_not_called()

    def test_prior_ambiguity_cannot_be_erased_by_successful_cleanup(self):
        self.owner._error("ambiguous-gradle-daemon")
        result, _, _, _, _, _ = self.run_cleanup()
        self.assertFalse(result["complete"])
        self.assertEqual(["ambiguous-gradle-daemon"], result["errors"])

    def test_cleanup_reports_no_wrapper_descendant_or_release_claim(self):
        result, _, _, _, _, _ = self.run_cleanup()
        for key in ("ordinary_wrapper_or_other_host_verified", "all_descendants_verified",
                    "global_process_scan_or_wildcard_wait", "release_readiness_certified",
                    "receipt_pid_used", "log_bodies_read"):
            self.assertFalse(result[key])


class ScopeTests(Fixture):
    def test_other_host_preflight_starts_no_process(self):
        self.owner.client = None
        with mock.patch.object(o.sys, "platform", "darwin"), mock.patch.object(o, "identity") as check:
            with self.assertRaisesRegex(g.WitnessError, "owned-linux-pidfd-required"):
                self.owner.begin()
        check.assert_not_called()

    def test_missing_pidfd_preflight_starts_no_process(self):
        self.owner.client = None
        with mock.patch.object(o.sys, "platform", "linux"), mock.patch.object(os, "pidfd_open", new=None):
            with self.assertRaisesRegex(g.WitnessError, "owned-linux-pidfd-required"):
                self.owner.begin()

    def test_concurrent_controller_is_rejected(self):
        with mock.patch.object(o, "_ACTIVE", True):
            with self.assertRaisesRegex(g.WitnessError, "owned-dedicated-controller-required"):
                self.owner.begin()

    def test_multi_thread_controller_is_rejected_before_subreaper(self):
        stream = mock.MagicMock()
        stream.__enter__.return_value = iter([object(), object()])
        with mock.patch.object(os, "scandir", return_value=stream), \
                mock.patch.object(self.owner, "_subreaper") as sub:
            with self.assertRaisesRegex(g.WitnessError, "owned-single-thread-required"):
                self.owner.begin()
        sub.assert_not_called()

    def test_wrapper_preflight_is_rejected_before_subreaper(self):
        self.owner.command[0] = str(self.workspace / "gradlew")
        with mock.patch.object(self.owner, "_subreaper") as sub:
            with self.assertRaisesRegex(g.WitnessError, "owned-installed-gradle-command-required"):
                self.owner.begin()
        sub.assert_not_called()

    def test_expired_deadline_does_not_construct_owner_or_process(self):
        with mock.patch.object(d.time, "monotonic", return_value=295), \
                mock.patch.object(d.shutil, "disk_usage", return_value=mock.Mock(free=20 * 1024 ** 3)), \
                mock.patch.object(o, "OwnedGradle") as owner, mock.patch.object(d.subprocess, "Popen") as process:
            result = d._bounded(self.command, workspace=self.workspace, environment=self.env,
                                log=self.workspace / "not-created.log", timeout=90, reserve_mib=8192,
                                deadline=300, owned_gradle_home=self.gradle)
        owner.assert_not_called()
        process.assert_not_called()
        self.assertEqual("total-timeout-before-launch", result["reason"])

    def test_owner_preflight_failure_never_becomes_command_success(self):
        self.owner.client = None
        with mock.patch.object(d.shutil, "disk_usage", return_value=mock.Mock(free=20 * 1024 ** 3)), \
                mock.patch.object(o.sys, "platform", "darwin"), mock.patch.object(d.subprocess, "Popen") as process:
            result = d._bounded(self.command, workspace=self.workspace, environment=self.env,
                                log=self.workspace / "not-created.log", timeout=90, reserve_mib=8192,
                                owned_gradle_home=self.gradle)
        process.assert_not_called()
        self.assertFalse(result["process_started"])
        self.assertEqual(75, result["exit_code"])
        self.assertIsNone(result["log_sha256"])
        self.assertFalse(result["owned_gradle_cleanup"]["complete"])

    def test_only_single_root_installed_linux_fixture_selects_owner(self):
        root = self.root / "controlled"
        f.create(root)
        with mock.patch.dict(os.environ, {"JAVA_HOME": str(self.jdk)}), \
                mock.patch.object(d.sys, "platform", "linux"), \
                mock.patch.object(d, "_bounded", return_value={"exit_code": 1, "reason": "synthetic"}) as run:
            d.run(root, entry_root=".", run_id="bootstrap", mode="bootstrap", gradle_home=self.gradle)
        self.assertEqual(self.gradle, run.call_args.kwargs["owned_gradle_home"])

    def test_composite_fixture_has_explicit_unsupported_owner_scope(self):
        root = self.root / "composite"
        f.create(root, included=True)
        with mock.patch.dict(os.environ, {"JAVA_HOME": str(self.jdk)}), \
                mock.patch.object(d.sys, "platform", "linux"), \
                mock.patch.object(d, "_bounded", return_value={"exit_code": 1, "reason": "synthetic"}) as run:
            d.run(root, entry_root=".", run_id="bootstrap", mode="bootstrap", gradle_home=self.gradle)
        self.assertIsNone(run.call_args.kwargs["owned_gradle_home"])

    def test_interrupt_between_popen_and_pin_keeps_direct_child_for_cleanup(self):
        owner = mock.Mock(process=None)
        owner.start.side_effect = KeyboardInterrupt
        owner.cleanup.return_value = {"complete": False}
        process = mock.Mock(pid=202, returncode=-15)
        with mock.patch.object(d.shutil, "disk_usage", return_value=mock.Mock(free=20 * 1024 ** 3)), \
                mock.patch.object(o, "OwnedGradle", return_value=owner), \
                mock.patch.object(d.subprocess, "Popen", return_value=process):
            result = d._bounded(self.command, workspace=self.workspace, environment=self.env,
                                log=self.workspace / "interrupt.log", timeout=90, reserve_mib=8192,
                                owned_gradle_home=self.gradle)
        self.assertIs(owner.process, process)
        owner.cleanup.assert_called_once_with()
        self.assertEqual("interrupted", result["reason"])
        self.assertEqual(-15, result["exit_code"])

    def test_failed_popen_restores_prelaunch_owner_without_success(self):
        owner = mock.Mock(process=None)
        owner.cleanup.return_value = {"complete": False}
        with mock.patch.object(d.shutil, "disk_usage", return_value=mock.Mock(free=20 * 1024 ** 3)), \
                mock.patch.object(o, "OwnedGradle", return_value=owner), \
                mock.patch.object(d.subprocess, "Popen", side_effect=OSError("DO_NOT_REPORT_RAW_MESSAGE")):
            result = d._bounded(self.command, workspace=self.workspace, environment=self.env,
                                log=self.workspace / "failed-popen.log", timeout=90, reserve_mib=8192,
                                owned_gradle_home=self.gradle)
        self.assertFalse(result["process_started"])
        self.assertEqual(75, result["exit_code"])
        self.assertEqual("owned-process-os-error", result["reason"])
        owner.cleanup.assert_called_once_with()
        self.assertNotIn("DO_NOT_REPORT_RAW_MESSAGE", str(result))


class ActualFixturePreparationTests(Fixture):
    def test_exact_finite_hold_never_signals_its_recorded_pid(self):
        root = self.root / "hold"
        marker = actual.create(root, "timeout")
        script = (root / "build.gradle").read_text()
        self.assertIn('graph.hasTask(":nativeCmpkitDependencyGraph")', script)
        self.assertIn("Thread.sleep(60000)", script)
        self.assertIn('hold_milliseconds: 60000', script)
        self.assertIn('ProcessHandle.current().pid()', script)
        self.assertEqual(["."], marker["build_roots"])
        self.assertFalse(marker["independent_trust_reviewed"])

    def test_normal_fixture_has_no_delay_or_shutdown_hook(self):
        root = self.root / "normal"
        actual.create(root, "normal")
        script = (root / "build.gradle").read_text()
        self.assertEqual(f.BASE_BUILD, script)

    def test_resistant_fixture_has_finite_not_infinite_shutdown_hold(self):
        root = self.root / "resistant"
        actual.create(root, "timeout-term-resistant")
        script = (root / "build.gradle").read_text()
        self.assertIn("Thread.sleep(30000)", script)
        self.assertIn("Thread.sleep(60000)", script)
        self.assertNotIn("while", script)

    def test_generated_controller_uses_owning_runner_and_private_fresh_cache(self):
        code = actual.controller_bytes(self.workspace, self.root / "result.json", self.jdk, self.gradle, 20).decode()
        self.assertIn("d.run(", code)
        self.assertIn("fresh_cache=True", code)
        self.assertIn("reserve_mib=8192", code)
        self.assertIn("timeout=20", code)
        self.assertNotIn("killpg", code)
        self.assertNotIn("waitpid", code)

    def test_actual_cases_cover_both_interrupt_signals_and_escalation(self):
        self.assertEqual(("normal", "timeout", "sigint", "sigterm", "timeout-term-resistant"), actual.CASES)


if __name__ == "__main__":
    unittest.main()
