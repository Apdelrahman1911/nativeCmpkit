"""New SDK-selector/install/cleanup guards; tools, link and host all simulated.

No accepted nine-method shape suite or process-helper regression is replayed.
Only tiny owned fixture files are real. No Apple SDK/native/Worker/XML occurs.
"""
import ast
import copy
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apple_appinfo_capability as capability
import apple_appinfo_shape as shape
import apple_appinfo_shape_route as route
import ios_ui_application as application
import library_tests as lt
import workflow_matrix as wm

DEVICE = "11111111-1111-1111-1111-111111111111"
REVISION = "a" * 40
HELP_BYTES = (lt.ROOT / route.HELP_RECEIPT).read_bytes()
ACCEPTED = json.loads(HELP_BYTES)
SOURCE_ROOT = Path(wm.__file__).resolve().parents[2]


def captured_shape():
    return {"status": "observed-bounded-lexical-shape",
            "capability_receipt_sha256": shape.ACCEPTED_HELP_RECEIPT_SHA256,
            "query_attempted": True, "query_count": 1, "owned_private_output_removed": True,
            "registered_container_matches_verified_container": None,
            "registered_executable_identity_verified": None,
            **{key: False for key in route.FALSE_FLAGS}}


def observation():
    return {"operation": "owned-install-appinfo-shape", "status": "observed-bounded-lexical-shape",
            "shape": captured_shape(), "tool_path_resolution": []}


class AppleAppinfoShapeRouteTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-appinfo-route-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.initialise(self.root)
        self.root_patch = patch.object(lt, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.runtime = {"source_revision": REVISION, "source_tree_dirty": False,
                        "host": copy.deepcopy(ACCEPTED["host"]), "xcode": copy.deepcopy(ACCEPTED["xcode"]),
                        "simulator": {"udid": DEVICE, "state": "Booted"}}

    def initialise(self, root, *, binary=True):
        for relative in route.SOURCE_INPUTS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"Synthetic source presence, not producer acceptance\n")
        path = root / route.HELP_RECEIPT
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(HELP_BYTES)
        if binary:
            self.write_binary(root)

    def write_binary(self, root):
        path = root / route.BINARY
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"Synthetic executable bytes, not native Mach-O\n")
        path.chmod(0o755)
        return path

    @contextmanager
    def harness(self, *, root=None, install_exit=0, uninstall_exit=0, observe=None):
        root = root or self.root
        state = {"installed": False, "calls": [], "query_contexts": [], "local": None}
        container = root / "synthetic-installed" / "NativeCmpkitLibraryTests.app"
        def control(argv, timeout=60):
            argv = list(argv)
            state["calls"].append(argv)
            if argv[:3] == ["/usr/bin/codesign", "--force", "--sign"]:
                self.assertEqual(["/usr/bin/codesign", "--force", "--sign", "-"], argv[:4])
                return subprocess.CompletedProcess(argv, 0, b"", b"")
            self.assertEqual(["/usr/bin/xcrun", "simctl"], argv[:2])
            action = argv[2]
            if action == "get_app_container":
                if state["installed"]:
                    return subprocess.CompletedProcess(argv, 0, str(container).encode() + b"\n", b"")
                return subprocess.CompletedProcess(argv, 2, b"", b"(domain=NSPOSIXErrorDomain, code=2)")
            if action == "install":
                state["local"] = Path(argv[4])
                container.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(state["local"], container)
                state["installed"] = True
                return subprocess.CompletedProcess(argv, install_exit, b"", b"")
            if action == "terminate":
                return subprocess.CompletedProcess(argv, 0, b"", b"")
            if action == "uninstall":
                shutil.rmtree(container)
                state["installed"] = False
                return subprocess.CompletedProcess(argv, uninstall_exit, b"", b"")
            raise AssertionError("Unexpected SDK/native control command in synthetic route")
        def owned_observation(context):
            state["query_contexts"].append(context)
            self.assertEqual(root, context.root)
            self.assertEqual(DEVICE, context.device)
            self.assertEqual(REVISION, context.source_revision)
            self.assertEqual(0, context.install.returncode)
            self.assertEqual(context.bundle, context.container.args[4])
            self.assertIs(application.installed_identity(context.container, context.bundle,
                context.signed_hash, context.plist_hash), True)
            return observe(context) if observe else observation()
        with patch.object(lt, "ROOT", root), \
                patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_SIMULATOR": DEVICE,
                    "NATIVECMPKIT_UIKIT_RESULT_ROOT": route.OUTPUT + "/native-ui-application"}), \
                patch.object(application.platform, "system", return_value="Darwin"), \
                patch.object(application.platform, "machine", return_value="arm64"), \
                patch.object(application.runtime, "capture", side_effect=lambda **kwargs: copy.deepcopy(self.runtime)), \
                patch.object(application.shutil, "disk_usage", return_value=type("Disk", (), {"free": 16 * 1024**3})()), \
                patch.object(application, "macho_simulator_identity", return_value={"minimum_os": "15.0.0"}), \
                patch.object(application, "execute_control", side_effect=control), \
                patch.object(route, "observe_owned_install", side_effect=owned_observation), \
                patch.object(application, "forward_application", side_effect=AssertionError("Native launch forbidden")), \
                patch.object(application, "sign_owned_debug_profile_application", side_effect=AssertionError("ADR0012 forbidden")), \
                patch.object(application.simulator_appearance, "AppearanceDriver", side_effect=AssertionError("Appearance prep forbidden")):
            yield state

    def synthetic_document(self):
        return {"sdk_prerequisite_only": True, "sdk_signing_mode": "ordinary-adhoc",
                "transport_passed": False, "native_launch_attempted": False, "native_tests_executed": 0,
                "explicit_test_focus": None, "application_protocol": None,
                "appinfo_shape_prerequisite": observation(),
                "cleanup": {**{key: True for key in route.CLEANUP_FLAGS}, "uninstall_exit_code": 0}}

    def test_internal_sdk_selector_refuses_native_arguments_other_modules_profile_and_non_boolean_mode(self):
        cases = ((route.BINARY, list(application.TEST_ARGUMENTS), None, True),
                 (route.BINARY, ["--ktest_gradle_filter=foreign"], None, True),
                 (route.BINARY, [], "darwin-tools", True),
                 (route.BINARY.replace("calf-ui", "calf-webview"), [], None, True),
                 (route.BINARY, [], None, 1), (route.BINARY, [], None, False))
        with self.harness() as state:
            for binary, arguments, image, mode in cases:
                with self.subTest(binary=binary, mode=mode):
                    with self.assertRaises(ValueError):
                        application.run(binary, arguments, image_diagnostics=image, appinfo_shape_only=mode)
            self.assertEqual([], state["calls"])
            self.assertEqual([], state["query_contexts"])

    def test_current_owned_install_returns_before_native_drivers_and_keeps_ordinary_signer_and_original_cleanup(self):
        with self.harness() as state:
            document = application.run(route.BINARY, [], appinfo_shape_only=True)
        self.assertEqual(1, len(state["query_contexts"]))
        context = state["query_contexts"][0]
        self.assertEqual(["/usr/bin/xcrun", "simctl", "install", DEVICE,
            str(context.output / "NativeCmpkitLibraryTests.app")], context.install.args)
        self.assertEqual(context.output.name, context.token)
        self.assertIn(REVISION[:12], context.bundle)
        self.assertIs(document["transport_passed"], False)
        self.assertIs(document["native_launch_attempted"], False)
        self.assertEqual(0, document["native_tests_executed"])
        self.assertIsNone(document["application_protocol"])
        self.assertIs(route.installation_prerequisite_observed(document), True)
        self.assertFalse(state["installed"])
        self.assertFalse(state["local"].exists())
        actions = [argv[2] for argv in state["calls"] if argv[0] == "/usr/bin/xcrun"]
        self.assertEqual(["get_app_container", "install", "get_app_container",
                          "get_app_container", "terminate", "uninstall", "get_app_container"], actions)
        for name in ("webview_request_fixture", "image_memory_profile", "system_appearance_driver",
                     "application_protocol_partial", "owned_crash_diagnostics", "owned_launch_diagnostics"):
            self.assertNotIn(name, document)

    def test_uncertain_install_and_post_query_binary_drift_keep_cleanup_but_cannot_become_sdk_or_native_success(self):
        with self.harness(install_exit=1) as state:
            document = application.run(route.BINARY, [], appinfo_shape_only=True)
        self.assertEqual([], state["query_contexts"])
        self.assertFalse(state["installed"])
        self.assertIs(route.cleanup_verified(document), True)
        self.assertIs(route.installation_prerequisite_observed(document), False)
        def drift(context):
            (context.root / route.BINARY).write_bytes(b"Changed synthetic linked binary\n")
            return observation()
        with self.harness(observe=drift) as state:
            document = application.run(route.BINARY, [], appinfo_shape_only=True)
        self.assertEqual(1, len(state["query_contexts"]))
        self.assertEqual("post-sdk-prerequisite-runtime-and-binary", document["error"]["phase"])
        self.assertIs(route.cleanup_verified(document), True)
        self.assertIs(route.installation_prerequisite_observed(document), False)
        self.assertIs(document["transport_passed"], False)

    def test_cleanup_and_claim_drift_never_satisfy_dedicated_sdk_availability(self):
        good = self.synthetic_document()
        self.assertIs(route.installation_prerequisite_observed(good), True)
        changes = (("transport_passed", True), ("native_launch_attempted", True),
                   ("native_tests_executed", 1), ("native_tests_executed", False),
                   ("sdk_signing_mode", "profile-debug"), ("explicit_test_focus", lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS),
                   ("application_protocol", {"testcases": []}), ("error", {"type": "ValueError"}))
        for key, value in changes:
            with self.subTest(key=key):
                document = copy.deepcopy(good);document[key] = value
                self.assertIs(route.installation_prerequisite_observed(document), False)
        for key in route.NATIVE_PREPARATION_KEYS:
            with self.subTest(native_preparation=key):
                document = copy.deepcopy(good);document[key] = {}
                self.assertIs(route.installation_prerequisite_observed(document), False)
        for key in route.CLEANUP_FLAGS:
            with self.subTest(cleanup=key):
                document = copy.deepcopy(good);document["cleanup"][key] = False
                self.assertIs(route.installation_prerequisite_observed(document), False)
        for key in route.FALSE_FLAGS:
            with self.subTest(claim=key):
                document = copy.deepcopy(good);document["appinfo_shape_prerequisite"]["shape"][key] = True
                self.assertIs(route.installation_prerequisite_observed(document), False)
        for count in (0, 2, True):
            document = copy.deepcopy(good);document["appinfo_shape_prerequisite"]["shape"]["query_count"] = count
            self.assertIs(route.installation_prerequisite_observed(document), False)

    def test_fixed_tool_resolution_invokes_pinned_collector_once_and_retains_no_raw_selected_paths(self):
        context = type("Context", (), {"root": self.root})()
        paths = {name: Path("/private/synthetic-selected/" + name) for name in ("developer", "simctl", "xcodebuild")}
        calls = []
        def control(argv, root, seconds):
            calls.append((argv, root, seconds))
            name = next(name for name in paths if capability.COMMANDS[name] == tuple(argv))
            return capability.Result(0, str(paths[name]).encode() + b"\n", b"", None)
        with patch.object(capability, "control", side_effect=control), \
                patch.object(shape, "collect", return_value=captured_shape()) as collect:
            result = route.observe_owned_install(context)
        self.assertEqual([capability.COMMANDS[name] for name in paths], [call[0] for call in calls])
        self.assertTrue(all(call[1:] == (self.root, 15) for call in calls))
        collect.assert_called_once()
        self.assertIs(collect.call_args.args[0], context)
        self.assertEqual(HELP_BYTES, collect.call_args.kwargs["capability_bytes"])
        self.assertEqual(Path("/usr/bin/xcrun"), collect.call_args.kwargs["tool_paths"]["xcrun"])
        self.assertEqual(paths["developer"], collect.call_args.kwargs["developer"])
        self.assertEqual("observed-bounded-lexical-shape", result["status"])
        self.assertNotIn("/private/synthetic-selected", json.dumps(result))

    def test_fixed_identity_failure_pinned_receipt_drift_and_budget_exhaustion_never_query_or_fallback(self):
        context = type("Context", (), {"root": self.root})()
        with patch.object(capability, "control", return_value=capability.Result(1, b"", b"/private/unknown path", None)), \
                patch.object(shape, "collect", side_effect=AssertionError("Query forbidden")):
            result = route.observe_owned_install(context)
        self.assertEqual("unavailable", result["status"])
        self.assertNotIn("/private/unknown", json.dumps(result))
        with patch.object(route.time, "monotonic", side_effect=(0, 100, 100)), \
                patch.object(capability, "control", side_effect=AssertionError("Resolution forbidden")), \
                patch.object(shape, "collect", side_effect=AssertionError("Query forbidden")):
            result = route.observe_owned_install(context)
        self.assertEqual("path_resolution_budget_exhausted", result["error_guard"])
        self.assertIs(result["budget_exhausted"], True)
        (self.root / route.HELP_RECEIPT).write_bytes(HELP_BYTES + b"\n")
        with patch.object(capability, "control", side_effect=AssertionError("Resolution forbidden")):
            result = route.observe_owned_install(context)
        self.assertEqual("accepted_actual006_help_bytes_required", result["error_guard"])

    def test_dedicated_read_only_selector_empty_library_matrix_and_cli_cannot_select_or_waive_native_methods(self):
        with patch.object(wm.subprocess, "run", side_effect=AssertionError("No library process")), \
                patch.object(lt, "run", side_effect=AssertionError("No library run")):
            selected = route.plan(self.root)
            preflight = wm.preflight_plans(route.PROFILE, self.root)
        self.assertEqual({"include": []}, wm.matrix(route.PROFILE))
        self.assertNotIn(route.PROFILE, wm.MODULE_SUBSETS)
        self.assertNotIn(route.PROFILE, lt.UI_APPLICATION_FOCUS_SPECS)
        self.assertEqual(11, len(wm.SLOTS))
        self.assertEqual([], selected["selected_native_methods"])
        self.assertIs(selected["mandatory_library_tests_waived"], False)
        self.assertEqual(route.LINK_COMMAND, selected["link_command"])
        self.assertEqual([route.LINK_TASK], [word for word in selected["link_command"] if word.startswith(":")])
        self.assertEqual([], preflight["slots"])
        self.assertEqual(0, preflight["library_tests_executed"])
        self.assertEqual([selected], preflight["sdk_prerequisites"])
        for extra in (("--binary", "foreign.kexe"), ("--focus", "foreign"), ("--help-receipt", "foreign.json")):
            with self.subTest(extra=extra), patch.object(route.sys, "argv", ["selector", "plan", *extra]), \
                    patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                route.main()
        with self.assertRaises(route.RouteError):
            route.run("Booted")

    def test_fixed_link_driver_writes_only_sdk_receipt_after_owned_cleanup_and_refuses_session_retry(self):
        (self.root / route.BINARY).unlink()
        def link(root, command, log, seconds, reserve):
            self.assertEqual(route.LINK_COMMAND, command)
            self.assertEqual((1200, 8192), (seconds, reserve))
            self.write_binary(root)
            log.write_text("> Task " + route.LINK_TASK + "\n")
            return {"exit_code": 0, "elapsed_seconds": 0.001}
        with self.harness() as state, patch.object(lt, "execute", side_effect=link) as linker, \
                patch.object(lt, "snapshot_inputs", return_value={"synthetic-owning-source": "a" * 64}):
            result = route.run(DEVICE)
            with self.assertRaises(FileExistsError):
                route.run(DEVICE)
        self.assertEqual(1, linker.call_count)
        self.assertEqual(1, len(state["query_contexts"]))
        self.assertIs(result["sdk_prerequisite_available"], True)
        self.assertIs(result["transport_passed"], False)
        self.assertEqual(0, result["native_tests_executed"])
        self.assertEqual([], result["selected_native_methods"])
        self.assertIs(result["mandatory_library_tests_waived"], False)
        self.assertFalse(state["local"].exists())
        for key in ("registration_observed", "appinfo_output_schema_observed", "profile_passed",
                    "root_cause_proven", "native_functionality_verified", "subsequent_appinfo_ready",
                    "packages_published", "release_readiness_certified"):
            self.assertIs(result[key], False)
        self.assertEqual(result, json.loads((self.root / route.OUTPUT / "receipt.json").read_bytes()))
        self.assertIsNone(result["registered_container_matches_verified_container"])

    def test_failed_link_changed_source_or_incomplete_cleanup_refuses_sdk_availability_without_native_fallback(self):
        for index, failure in enumerate(("link", "source", "cleanup", "cached-link", "skipped-link",
                                         "no-source-link", "missing-link", "duplicate-link")):
            with self.subTest(failure=failure):
                root = self.root / f"fresh-owned-model-{index}"
                root.mkdir();self.initialise(root, binary=False)
                def link(root, command, log, seconds, reserve):
                    if failure == "link":
                        return {"exit_code": 1, "elapsed_seconds": 0.001}
                    self.write_binary(root)
                    marker = "> Task " + route.LINK_TASK
                    suffixes = {"cached-link": " FROM-CACHE", "skipped-link": " SKIPPED",
                                "no-source-link": " NO-SOURCE"}
                    content = marker + suffixes.get(failure, "") + "\n"
                    if failure == "missing-link":
                        content = "NATIVECMPKIT_TEST_RUNTIME task=" + route.LINK_TASK + " gradle=synthetic\n"
                    elif failure == "duplicate-link":
                        content += marker + "\n"
                    log.write_text(content)
                    return {"exit_code": 0, "elapsed_seconds": 0.001}
                maps = ({"source": "a" * 64}, {"source": ("b" if failure == "source" else "a") * 64})
                with self.harness(root=root, uninstall_exit=1 if failure == "cleanup" else 0) as state, \
                        patch.object(lt, "execute", side_effect=link), \
                        patch.object(lt, "snapshot_inputs", side_effect=maps):
                    result = route.run(DEVICE, root)
                self.assertIs(result["sdk_prerequisite_available"], False)
                self.assertIs(result["transport_passed"], False)
                self.assertEqual(0, result["native_tests_executed"])
                self.assertEqual(1 if failure in {"source", "cleanup"} else 0, len(state["query_contexts"]))

    def test_source_wiring_keeps_WK_finally_and_help_only_job_exact_and_uploads_no_private_log_native_xml_or_bundle(self):
        source = Path(application.__file__).read_text()
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "run")
        owner = next(n for n in node.body if isinstance(n, ast.Try) and n.finalbody)
        wk = owner.finalbody[0]
        self.assertEqual("request_fixture is not None", ast.get_source_segment(source, wk.test))
        body = "".join(source.splitlines(keepends=True)[wk.lineno - 1:wk.end_lineno]).encode()
        self.assertEqual("1e51ca8edf5d2b53d7ff2d5bc8457bb8b9c7963a2edac986db3f5174e2eb720c", hashlib.sha256(body).hexdigest())
        text = (SOURCE_ROOT / ".github/workflows/gradle.yml").read_text()
        job = text.split("\n  apple-appinfo-shape:\n", 1)[1].split("\n  apple-appinfo-capability:\n", 1)[0]
        help_job = text.split("\n  apple-appinfo-capability:\n", 1)[1].split("\n  sample-platforms:\n", 1)[0]
        self.assertNotIn("apple_appinfo_shape_route", help_job)
        self.assertNotIn("simctl install", help_job)
        self.assertIn("inputs.profile == 'ios-appinfo-shape'", job)
        self.assertIn('apple_appinfo_shape_route.py run --simulator "$SELECTED_SIMULATOR"', job)
        self.assertLess(job.index("initial_state=%s"), job.index('simctl boot "$device"'))
        self.assertIn("steps.runtime.outputs.initial_state == 'Shutdown'", job)
        upload = job.split("path: |", 1)[1]
        self.assertEqual({route.OUTPUT + "/receipt.json", route.OUTPUT + "/library-inputs-before.json",
                          route.OUTPUT + "/library-inputs-after.json"}, set(upload.split()))
        for forbidden in ("private-link.log", ".app", ".kexe", "native-ui-application", "test-results", "help appinfo"):
            self.assertNotIn(forbidden, upload)


if __name__ == "__main__":
    unittest.main()
