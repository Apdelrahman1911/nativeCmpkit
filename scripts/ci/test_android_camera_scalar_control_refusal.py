"""Twelve genuinely new scalar-observer controls, not native or accepted-suite executions.

Every payload, argument and exception below is synthetic. None reconstructs the
unlogged 41344349446 getter, key, pattern, bytes or cause. Only the held helper is
imported; no project test module, SDK, process, network, build or native method is
selected. These controls are authored here but must be executed once by the lead.
"""
from __future__ import annotations

from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("NATIVECMPKIT_CAMERA_SCALAR_MODEL_TREE", Path(__file__).resolve().parents[2])).resolve()
HELPER_PATH = TREE / "scripts/ci/android_camera_developer_prerequisite.py"
EXPECTED_HELPER_SHA256 = "0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26"
ATTRIBUTE = "_nativecmpkit_scalar_control_refusal"
WITNESS = "_nativecmpkit_scalar_control_refusal_identity"
MARKER = "synthetic-private-setting-or-process-body"
DECLARED_METHODS = (
    "test_sc01_exact_getter_role_and_both_allowlisted_keys_survive_original_refusal",
    "test_sc02_provider_rows_whitespace_and_unsafe_bytes_never_become_accepted",
    "test_sc03_owner_context_binds_exact_allowlisted_command_and_result_identity",
    "test_sc04_unknown_near_miss_and_cross_result_context_never_guess_a_query",
    "test_sc05_original_result_and_regex_refusals_precede_scalar_observation",
    "test_sc06_secondary_observer_and_publisher_failures_preserve_primary_identity",
    "test_sc07_forged_extra_mistyped_unbounded_and_inconsistent_facts_are_not_published",
    "test_sc08_foreign_origin_copied_exception_and_direct_context_injection_refuse",
    "test_sc09_nonrefusing_scalar_calls_do_not_run_the_observer",
    "test_sc10_original_row_agreement_and_arbitrary_key_guards_are_not_shape_facts",
    "test_sc11_missing_original_cleanup_stays_separate_sticky_and_mutation_free",
    "test_sc12_publication_is_bounded_hash_shape_only_and_has_no_global_registry",
)
FACT_KEYS = {
    "schema", "query", "setting_key", "cap_bytes", "payload_bytes", "payload_sha256",
    "pattern_bytes", "pattern_sha256", "ascii_only", "printable_ascii_or_line_endings_only",
    "lf_bytes", "cr_bytes", "nul_bytes", "escape_bytes", "tab_bytes", "space_bytes",
    "leading_ascii_spaces", "trailing_ascii_spaces", "terminal_lf", "terminal_crlf", "empty",
}
COUNTERS = {"fresh_results": 0, "new_refusal_samples": 0, "publication_samples": 0,
            "privacy_samples": 0, "metadata_refusals": 0, "secondary_failures": 0,
            "missing_original_cleanup_samples": 0, "existing_accepted_test_methods_selected": 0,
            "native_invocations": 0}
FORBIDDEN_ACTIONS = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_binding_digest(path):
    # Current checkout admission is distinct from this preserved scalar stage.
    # Raw held-source/result digests below continue to describe actual bytes.
    if TREE == Path(__file__).resolve().parents[2] and path == HELPER_PATH:
        from android_external328_source_projection import current_source_for_history
        payload = current_source_for_history(path.relative_to(TREE).as_posix(), path.read_bytes())
        return hashlib.sha256(payload).hexdigest()
    return digest(path)  # Explicit private historical fixture, not live admission.


def forbidden(*args, **kwargs):
    FORBIDDEN_ACTIONS.append("forbidden-sdk-process-network-or-native-action")
    raise AssertionError("No process, SDK, network, build or native action is admitted")


def action_guards(stack):
    for module, names in (
        (subprocess, ("Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput")),
        (os, ("kill", "killpg", "system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp",
              "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
              "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe")),
        (socket, ("socket", "socketpair", "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex")),
    ):
        for name in names:
            if hasattr(module, name):
                stack.enter_context(patch.object(module, name, forbidden))


if HELPER_PATH.is_symlink() or source_binding_digest(HELPER_PATH) != EXPECTED_HELPER_SHA256:
    raise AssertionError("Exact scalar-observer helper source binding is changed")
SOURCE_BEFORE = digest(HELPER_PATH)
SPEC = importlib.util.spec_from_file_location("nativecmpkit_camera_scalar_new_controls_helper", HELPER_PATH)
helper = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {SPEC.name: helper}), ExitStack() as import_guards:
    action_guards(import_guards)
    SPEC.loader.exec_module(helper)
if Path(helper.__file__).resolve() != HELPER_PATH or helper.__spec__.origin != str(HELPER_PATH):
    raise AssertionError("Exact private scalar helper import origin changed")


def cp(payload=b"", *, code=0, stderr=b"", args=None):
    COUNTERS["fresh_results"] += 1
    return subprocess.CompletedProcess(args if args is not None else ["synthetic-not-a-device-query"], code, payload, stderr)


def caught(call):
    try:
        call()
    except BaseException as error:
        COUNTERS["new_refusal_samples"] += 1
        return error
    raise AssertionError("The new synthetic refusal control unexpectedly passed")


def row_refusal(payload, key, *, provider=False):
    getter = cp(b"0") if provider else cp(payload)
    query = cp(payload) if provider else cp(b"No result found.")
    return caught(lambda: helper.parse_row(getter, query, key))


def owner_result(arguments, payload, *, foreign_argv=False):
    owner = object.__new__(helper.OwnedDeveloperPrerequisite)
    owner.home = Path("/synthetic-sdk-never-executed")
    owner.events = []
    owner.guest = types.SimpleNamespace(verify_live=lambda: owner.events.append("owned-live-query-guard"))
    owner.action_guard = forbidden

    def run(argv, timeout, limit):
        owner.events.append("inert-requested-control")
        assert timeout == 10 and limit == helper.CONTROL_BYTES
        return cp(payload, args=["foreign-unrequested-executable", "-s", helper.SERIAL, *arguments] if foreign_argv else argv)

    owner.run = run
    return owner, owner.control(*arguments)


def bare_failure_owner():
    owner = object.__new__(helper.OwnedDeveloperPrerequisite)
    owner.closed = False
    owner.original = owner.new_boot = None
    owner.enable_attempted = owner.enable_completed = False
    owner.reboot_attempted = owner.restore_attempted = False
    owner.receiver_prepare_attempted = False
    owner.receiver_cleanup = {"removed": True, "status": "not-installed", "error": False}
    owner.receipt = {"schema": "nativecmpkit.camera-developer-prerequisite.v1", "focus": helper.FOCUS,
        "api_level": 35, "prepare_status": "failed", "cleanup_status": "not-started", "errors": [],
        "master_enable_attempts": 0, "normal_reboot_attempts": 0, "master_restore_attempts": 0,
        "reporter_dispatch_attempted": False, "reporter_removed": False, "receiver_removed": False,
        "reporter_initial_absent": True, "receiver_initial_absent": True,
        "raw_boot_ids_dumps_paths_or_environment_exported": False, "native_acceptance_inferred": False}
    owner.events, owner.published = [], []

    def publish():
        owner.events.append("publish")
        owner.published.append(copy.deepcopy(owner.receipt))

    def cleanup():
        owner.events.append("inert-original-reporter-absence-cleanup")
        owner.receipt.update(reporter_removed=True, reporter_absence_observed=True,
                             reporter_installed_bytes_verified=False)

    owner.publish = publish
    owner.devices = owner.run = owner.control = owner.action_guard = owner.stable = forbidden
    owner.reporter = types.SimpleNamespace(cleanup=cleanup, observe=lambda package=helper.REPORTER: None)
    return owner


class ScalarControlRefusalNewOnlyTests(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        action_guards(self.guards)
        self.guards.enter_context(patch.object(helper, "bounded_run", forbidden))
        self.guards.enter_context(patch.object(helper, "probe_child", forbidden))

    def tearDown(self):
        self.assertEqual(FORBIDDEN_ACTIONS, [])
        self.assertEqual(digest(HELPER_PATH), SOURCE_BEFORE)

    def facts(self, error):
        self.assertIs(type(error), ValueError)
        self.assertEqual(error.args, ("Unknown scalar control shape",))
        origin = helper.require_call_origin(error)
        self.assertEqual(origin["source"], HELPER_PATH.name)
        self.assertEqual(origin["symbol"], "line")
        result = helper.scalar_control_refusal(error, origin)
        self.assertIs(type(result), dict)
        self.assertEqual(set(result), FACT_KEYS)
        self.assertIsNot(result, vars(error)[ATTRIBUTE])
        self.assertIs(vars(error)[WITNESS], error)
        COUNTERS["publication_samples"] += 1
        return result

    def assert_private(self, facts, payload):
        rendered = json.dumps(facts, sort_keys=True)
        self.assertLess(len(rendered), 2048)
        self.assertEqual(facts["payload_bytes"], len(payload))
        self.assertEqual(facts["payload_sha256"], hashlib.sha256(payload).hexdigest())
        for raw in (MARKER, "/synthetic-sdk-never-executed", "synthetic-not-a-device-query", "Row: 0 name="):
            self.assertNotIn(raw, rendered)
        for key in ("stdout", "stderr", "argv", "arguments", "error", "payload", "pattern", "row", "value", "process_body"):
            self.assertNotIn(key, facts)
        COUNTERS["privacy_samples"] += 1

    def test_sc01_exact_getter_role_and_both_allowlisted_keys_survive_original_refusal(self):
        for key in (helper.MASTER, helper.SCALAR):
            payload = (MARKER + "\n").encode()
            error = row_refusal(payload, key)
            facts = self.facts(error)
            self.assertEqual((facts["query"], facts["setting_key"]), ("global-settings-get-user0", key))
            self.assertEqual(facts["cap_bytes"], 512)
            self.assert_private(facts, payload)

    def test_sc02_provider_rows_whitespace_and_unsafe_bytes_never_become_accepted(self):
        for key in (helper.MASTER, helper.SCALAR):
            canonical = ("Row: 0 name=" + key + ", value=0").encode()
            for payload in (b" " + canonical, canonical + b" ", canonical + b"\n" + canonical,
                            b"\t" + canonical, canonical + b"\r", canonical + b"\0", canonical + b"\x1b",
                            canonical + b"\xc2\xa0", b"", b"No result found.\nNo result found."):
                error = row_refusal(payload, key, provider=True)
                facts = self.facts(error)
                self.assertEqual((facts["query"], facts["setting_key"]), ("global-settings-single-row-user0", key))
                self.assert_private(facts, payload)
                self.assertEqual(facts["lf_bytes"], payload.count(b"\n"))
                self.assertEqual(facts["cr_bytes"], payload.count(b"\r"))
                self.assertEqual(facts["nul_bytes"], payload.count(b"\0"))
                self.assertEqual(facts["escape_bytes"], payload.count(b"\x1b"))
                self.assertEqual(facts["tab_bytes"], payload.count(b"\t"))

    def test_sc03_owner_context_binds_exact_allowlisted_command_and_result_identity(self):
        commands = (
            (("emu", "avd", "name"), "owned-avd-name"),
            (("shell", "id", "-u"), "shell-uid"),
            (("shell", "cat", "/proc/sys/kernel/random/boot_id"), "kernel-boot-id"),
            (("shell", "getprop", "ro.build.version.sdk"), "runtime-sdk"),
            (("shell", "getprop", "ro.product.cpu.abi"), "runtime-abi"),
            (("shell", "getprop", "sys.boot_completed"), "runtime-boot-completed"),
            (("shell", "getenforce"), "selinux-enforcement"),
            (("shell", "dumpsys", "package", "check-permission", "android.permission.DUMP", "com.android.shell", "0"),
             "shell-dump-permission-user0"),
            (("shell", "dumpsys", "package", "check-permission", "android.permission.ACCESS_CONTENT_PROVIDERS_EXTERNALLY", "com.android.shell", "0"),
             "shell-content-permission-user0"),
        )
        for arguments, identity in commands:
            payload = (MARKER + " \r\n").encode()
            owner, result = owner_result(arguments, payload)
            error = caught(lambda: helper.line(result, 512, rb"expected-exact-shape"))
            facts = self.facts(error)
            self.assertEqual((facts["query"], facts["setting_key"]), (identity, None))
            self.assertEqual(owner.events, ["owned-live-query-guard", "inert-requested-control"])
            self.assert_private(facts, payload)
        for key in (helper.MASTER, helper.SCALAR):
            arguments = ("shell", "settings", "--user", "0", "get", "global", key)
            owner, result = owner_result(arguments, b"0 ")
            facts = self.facts(caught(lambda: helper.line(result, 512, rb"(?:null|0|1)")))
            self.assertEqual((facts["query"], facts["setting_key"]), ("global-settings-get-user0", key))
        self.assertEqual(helper.scalar_query_identity(("shell", "settings", "--user", "0", "delete", "global", helper.MASTER)),
                         ("global-master-delete-user0", helper.MASTER))
        self.assertIsNone(helper.scalar_query_identity(("shell", "settings", "--user", "0", "delete", "global", helper.SCALAR)))

    def test_sc04_unknown_near_miss_and_cross_result_context_never_guess_a_query(self):
        unknown = (
            ("shell", "settings", "--user", "0", "get", "global", "not-allowlisted"),
            ("shell", "settings", "--user", "1", "get", "global", helper.MASTER),
            ("shell", "content", "query", "--user", "0", "--uri", "content://settings/global/" + helper.MASTER,
             "--projection", "name:value", "--where", "name=anything"),
            ("shell", "dumpsys", "activity", "processes"),
            ("shell", "sha256sum", "/data/app/private-token/base.apk"),
        )
        for arguments in unknown:
            owner, result = owner_result(arguments, MARKER.encode())
            self.assertIsNone(helper.scalar_query_identity(arguments))
            self.assertNotIn("_nativecmpkit_scalar_query_context", vars(result))
            error = caught(lambda: helper.line(result, 512, rb"0"))
            self.assertNotIn(ATTRIBUTE, vars(error))
            self.assertIsNone(helper.scalar_control_refusal(error, helper.require_call_origin(error)))
        arguments = ("shell", "id", "-u")
        _, source = owner_result(arguments, b"bad")
        _, target = owner_result(arguments, b"bad")
        target._nativecmpkit_scalar_query_context = source._nativecmpkit_scalar_query_context
        error = caught(lambda: helper.line(target, 512, rb"2000"))
        self.assertNotIn(ATTRIBUTE, vars(error))
        _, foreign = owner_result(arguments, b"bad", foreign_argv=True)
        self.assertNotIn("_nativecmpkit_scalar_query_context", vars(foreign))
        self.assertIsNone(helper.scalar_query_identity(list(arguments)))

    def test_sc05_original_result_and_regex_refusals_precede_scalar_observation(self):
        for result in (cp(b"0", code=1), cp(b"0", stderr=MARKER.encode()), cp("0"), cp(b"0" * 513)):
            with patch.object(helper, "record_scalar_control_refusal", forbidden):
                error = caught(lambda: helper.line(result, 512, rb"0"))
            self.assertIs(type(error), ValueError)
            self.assertEqual(error.args, ("Unknown or unbounded explicit control result",))
            self.assertEqual(helper.require_call_origin(error)["symbol"], "result_bytes")
            self.assertNotIn(ATTRIBUTE, vars(error))
        _, result = owner_result(("shell", "id", "-u"), b"bad")
        error = caught(lambda: helper.line(result, 512, rb"["))
        self.assertIsInstance(error, helper.re.error)
        self.assertNotIn(ATTRIBUTE, vars(error))

    def test_sc06_secondary_observer_and_publisher_failures_preserve_primary_identity(self):
        for secondary in (RuntimeError, ValueError, KeyboardInterrupt):
            seen = []

            def fail_observer(error, *args):
                seen.append(error)
                raise secondary(MARKER)

            with patch.object(helper, "record_scalar_control_refusal", fail_observer):
                error = row_refusal(b"0 ", helper.MASTER)
            self.assertIs(error, seen[0])
            self.assertIs(type(error), ValueError)
            self.assertEqual(error.args, ("Unknown scalar control shape",))
            self.assertNotIn(ATTRIBUTE, vars(error))
            owner = bare_failure_owner()
            with patch.object(helper, "scalar_control_refusal", side_effect=secondary(MARKER)):
                owner.failure("prepare", error)
            self.assertEqual(owner.events, ["publish"])
            self.assertEqual(len(owner.receipt["errors"]), 1)
            self.assertEqual(owner.receipt["errors"][0]["class"], "ValueError")
            self.assertNotIn("scalar_control_refusal", owner.receipt["errors"][0])
            self.assertNotIn(MARKER, json.dumps(owner.receipt))
            COUNTERS["secondary_failures"] += 1

    def test_sc07_forged_extra_mistyped_unbounded_and_inconsistent_facts_are_not_published(self):
        error = row_refusal(b"0 ", helper.MASTER)
        original = self.facts(error)
        variants = [dict(original, raw_settings=MARKER), {key: value for key, value in original.items() if key != "query"},
                    dict(original, query=MARKER), dict(original, setting_key=MARKER), dict(original, cap_bytes=True),
                    dict(original, payload_bytes=513), dict(original, pattern_bytes=0), dict(original, lf_bytes=-1),
                    dict(original, terminal_lf=1), dict(original, payload_sha256="f" * 64), dict(original, pattern_sha256="F" * 64),
                    dict(original, schema="unknown"), dict(original, ascii_only=not original["ascii_only"]),
                    dict(original, leading_ascii_spaces=original["leading_ascii_spaces"] + 1)]
        for facts in variants:
            setattr(error, ATTRIBUTE, facts)
            self.assertIsNone(helper.scalar_control_refusal(error, helper.require_call_origin(error)))
            owner = bare_failure_owner()
            owner.failure("prepare", error)
            self.assertNotIn("scalar_control_refusal", owner.receipt["errors"][0])
            self.assertNotIn(MARKER, json.dumps(owner.receipt))
            COUNTERS["metadata_refusals"] += 1
        setattr(error, ATTRIBUTE, dict(original))
        copied = self.facts(error)
        copied["query"] = MARKER
        self.assertEqual(vars(error)[ATTRIBUTE], original)

    def test_sc08_foreign_origin_copied_exception_and_direct_context_injection_refuse(self):
        error = row_refusal(b"0 ", helper.SCALAR)
        facts = self.facts(error)
        origin = helper.require_call_origin(error)
        for foreign in (None, {}, dict(origin, extra=MARKER), dict(origin, line=True), dict(origin, line=0),
                        dict(origin, symbol="parse_row"), dict(origin, source="foreign.py"), dict(origin, line=origin["line"] + 1)):
            self.assertIsNone(helper.scalar_control_refusal(error, foreign))
        clone = ValueError("Unknown scalar control shape").with_traceback(error.__traceback__)
        setattr(clone, ATTRIBUTE, facts)
        setattr(clone, WITNESS, error)
        self.assertIsNone(helper.scalar_control_refusal(clone, origin))
        injected = caught(lambda: helper.line(cp(b"0 "), 512, rb"(?:null|0|1)",
            query_identity=("global-settings-get-user0", helper.MASTER)))
        self.assertNotIn(ATTRIBUTE, vars(injected))
        self.assertIsNone(helper.scalar_control_refusal(injected, helper.require_call_origin(injected)))

    def test_sc09_nonrefusing_scalar_calls_do_not_run_the_observer(self):
        with patch.object(helper, "record_scalar_control_refusal", forbidden):
            for key in (helper.MASTER, helper.SCALAR):
                for suffix in (b"", b"\n", b"\r\n"):
                    self.assertEqual(helper.parse_row(cp(b"null" + suffix), cp(b"No result found." + suffix), key), helper.Row(False, None))
                    self.assertEqual(helper.parse_row(cp(b"0" + suffix), cp(("Row: 0 name=" + key + ", value=0").encode() + suffix), key),
                                     helper.Row(True, "0"))

    def test_sc10_original_row_agreement_and_arbitrary_key_guards_are_not_shape_facts(self):
        cases = (
            (cp(b"0"), cp(b"No result found."), helper.MASTER, "Getter and absent-row proof disagree"),
            (cp(b"1"), cp(("Row: 0 name=" + helper.SCALAR + ", value=0").encode()), helper.SCALAR,
             "Getter and single-row value disagree"),
            (cp(b"0"), cp(b"No result found."), "not-an-allowed-key", "No arbitrary settings key"),
        )
        for getter, query, key, message in cases:
            error = caught(lambda: helper.parse_row(getter, query, key))
            self.assertIs(type(error), ValueError)
            self.assertEqual(error.args, (message,))
            self.assertEqual(helper.require_call_origin(error)["symbol"], "parse_row")
            self.assertNotIn(ATTRIBUTE, vars(error))
            self.assertIsNone(helper.scalar_control_refusal(error, helper.require_call_origin(error)))

    def test_sc11_missing_original_cleanup_stays_separate_sticky_and_mutation_free(self):
        primary = row_refusal(b"0 ", helper.MASTER)
        owner = bare_failure_owner()
        seen = []
        original_failure = owner.failure

        def observe_failure(phase, error):
            seen.append((phase, error))
            return original_failure(phase, error)

        owner.failure = observe_failure
        owner.failure("prepare", primary)
        receipt = owner.close()
        self.assertIs(seen[0][1], primary)
        self.assertEqual([phase for phase, _ in seen], ["prepare", "cleanup"])
        cleanup = seen[1][1]
        self.assertIs(type(cleanup), ValueError)
        self.assertEqual(cleanup.args, ("Original exact state was not acquired",))
        self.assertEqual(helper.require_call_origin(cleanup)["symbol"], "close")
        self.assertIsNone(owner.original)
        self.assertEqual((receipt["prepare_status"], receipt["cleanup_status"]), ("failed", "failed"))
        self.assertEqual([receipt[key] for key in ("master_enable_attempts", "normal_reboot_attempts", "master_restore_attempts")], [0, 0, 0])
        self.assertFalse(receipt["reporter_dispatch_attempted"])
        self.assertFalse(receipt["native_acceptance_inferred"])
        self.assertEqual(receipt["errors"][0]["scalar_control_refusal"]["setting_key"], helper.MASTER)
        self.assertNotIn("scalar_control_refusal", receipt["errors"][1])
        count = len(owner.events)
        self.assertEqual(owner.close(), receipt)
        self.assertEqual(len(owner.events), count)
        COUNTERS["missing_original_cleanup_samples"] += 1

    def test_sc12_publication_is_bounded_hash_shape_only_and_has_no_global_registry(self):
        token = helper._SCALAR_QUERY_CONTEXT
        payload = b" " + MARKER.encode() + b"\t\0\x1b\xc2\xa0\r\n"
        error = row_refusal(payload, helper.SCALAR)
        facts = self.facts(error)
        self.assert_private(facts, payload)
        owner = bare_failure_owner()
        owner.failure("prepare", error)
        exported = owner.receipt["errors"][0]["scalar_control_refusal"]
        self.assertEqual(exported, facts)
        self.assertIsNot(exported, vars(error)[ATTRIBUTE])
        self.assertLess(len(json.dumps(owner.receipt)), 4096)
        self.assertFalse(facts["ascii_only"])
        self.assertFalse(facts["printable_ascii_or_line_endings_only"])
        self.assertEqual((facts["terminal_lf"], facts["terminal_crlf"]), (True, True))
        self.assertEqual((facts["leading_ascii_spaces"], facts["trailing_ascii_spaces"]), (1, 0))
        self.assertIs(helper._SCALAR_QUERY_CONTEXT, token)
        self.assertEqual(COUNTERS["existing_accepted_test_methods_selected"], 0)
        self.assertEqual(COUNTERS["native_invocations"], 0)


if {name for name in vars(ScalarControlRefusalNewOnlyTests) if name.startswith("test_")} != set(DECLARED_METHODS):
    raise AssertionError("The exact new scalar-observer method set changed")
