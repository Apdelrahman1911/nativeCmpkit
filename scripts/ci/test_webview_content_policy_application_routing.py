# SPDX-License-Identifier: Apache-2.0
"""NEW source/AST and fake-object handoff models; never fixture/native/controller replay."""
import ast
import copy
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import ios_ui_application as application
import library_tests as r
import webview_content_policy_native_focus as policy
import webview_content_policy_source_projection as history
from test_webview_content_policy_native_focus import copy_model_checkout, native_plan

ROOT = Path(__file__).resolve().parents[2]
APP_SOURCE = "scripts/ci/ios_ui_application.py"
LIBRARY_SOURCE = "scripts/ci/library_tests.py"


def functions(name, payload=None):
    source = (ROOT / name).read_bytes() if payload is None else payload
    return {node.name: node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}


def prepare_node():
    return next(node for node in ast.walk(functions(APP_SOURCE)["run"])
                if isinstance(node, ast.If) and ast.unparse(node.test) == "content_fixture_requested")


def cleanup_node():
    return next(node for node in ast.walk(functions(APP_SOURCE)["run"])
                if isinstance(node, ast.If) and ast.unparse(node.test) == "content_fixture is not None")


def validation_node():
    return next(node for node in ast.walk(functions(LIBRARY_SOURCE)["collect_one_ios_application_receipt"])
                if isinstance(node, ast.If) and "content_policy.spec(content_policy.IOS_FOCUS)" in ast.unparse(node.test))


def model(node, namespace):
    """Execute only the NEW ordinary Python block with explicit fake dependencies."""
    document = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)], type_ignores=[]))
    exec(compile(document, "<new-content-routing-source-only-model>", "exec"), namespace)


class FakeContentFixture:
    def __init__(self, events, *, close_error=None, receipt_error=None, bind_error=None):
        self.events = events; self.close_error = close_error; self.receipt_error = receipt_error; self.bind_error = bind_error
        events.append("construct")

    def bind_application(self, root, **identities):
        self.events.append(("bind", root, identities))
        if self.bind_error: raise self.bind_error

    @property
    def nonce_sha256(self):
        self.events.append("nonce"); return "d" * 64

    def launch_environment(self, inherited):
        self.events.append(("environment", inherited.copy()))
        result = dict(inherited); result["SIMCTL_CHILD_NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN"] = "source-model-only"
        return result

    def close(self):
        self.events.append("close")
        if self.close_error: raise self.close_error

    def receipt(self):
        self.events.append("receipt")
        if self.receipt_error: raise self.receipt_error
        return {"source_model_only": True}


class WebViewContentPolicyApplicationRoutingControls(unittest.TestCase):
    def namespace(self, *, close_error=None, receipt_error=None, bind_error=None, validated=True):
        events = []; fixture = FakeContentFixture(events, close_error=close_error, receipt_error=receipt_error, bind_error=bind_error)
        validate = Mock(return_value=validated)
        fake_module = SimpleNamespace(SOURCE=policy.IOS_FIXTURE, NATIVE_SOURCE=policy.spec(policy.IOS_FOCUS)["source"],
                                      NATIVE_HELPER=policy.IOS_HELPER, validate_receipt=validate,
                                      OwnedContentPolicyFixture=lambda: fixture)
        contract = Mock(side_effect=lambda *args: events.append("source-contract"))
        hashes = policy.SOURCE_SHA256
        namespace = {"root": ROOT, "focus": policy.IOS_FOCUS, "content_fixture_requested": True,
                     "content_fixture": None, "content_nonce_hash": None, "native_environment": None,
                     "bundle_id": "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32,
                     "signed_hash": "a" * 64, "plist_hash": "b" * 64, "protocol": SimpleNamespace(observed_launch_pid=321),
                     "receipt": {"transport_passed": True}, "wk_content": fake_module, "os": os,
                     "lt": SimpleNamespace(content_policy=SimpleNamespace(source_contract=contract),
                                           sha256=lambda path: hashes[path.relative_to(ROOT).as_posix()])}
        return namespace, fixture, fake_module, events, validate

    def test_new_fixture_requested_only_by_exact_webview_content_focus_not_generic_or_old_owners(self):
        run = functions(APP_SOURCE)["run"]
        assign = next(node for node in ast.walk(run) if isinstance(node, ast.Assign) and
                      any(isinstance(target, ast.Name) and target.id == "content_fixture_requested" for target in node.targets))
        for module in ("calf-webview", "calf-ui", "calf-share", "calf-file-picker"):
            for focus in (policy.IOS_FOCUS, None, r.IOS_WEBVIEW_REQUEST_FOCUS, r.IOS_WEBVIEW_REQUEST_DNS_FOCUS, r.IOS_WEBVIEW_LIFECYCLE_FOCUS):
                namespace = {"host": {"module": module}, "focus": focus, "lt": SimpleNamespace(content_policy=policy)}
                expression = ast.fix_missing_locations(ast.Expression(copy.deepcopy(assign.value)))
                self.assertIs(module == policy.MODULE and focus == policy.IOS_FOCUS, eval(compile(expression, "<source-only-focus-model>", "eval"), namespace))
        prior = functions(APP_SOURCE, history.source_before_content_policy(APP_SOURCE, (ROOT / APP_SOURCE).read_bytes()))["run"]
        def request(node):
            return next(item for item in ast.walk(node) if isinstance(item, ast.Assign) and
                        any(isinstance(target, ast.Name) and target.id == "request_fixture_requested" for target in item.targets))
        self.assertEqual(ast.dump(request(prior), include_attributes=False), ast.dump(request(run), include_attributes=False))

    def test_new_profile_enables_only_existing_disposable_local_network_ats_and_no_arbitrary_policy(self):
        identifier = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
        information = application.app_information(identifier, "17.0.0", local_webview_requests=True)
        self.assertEqual({"NSAllowsLocalNetworking": True}, information["NSAppTransportSecurity"])
        self.assertNotIn("NSAppTransportSecurity", application.app_information(identifier, "17.0.0"))
        source = (ROOT / APP_SOURCE).read_text()
        self.assertIn("local_webview_requests=request_fixture_requested or content_fixture_requested", source)
        self.assertNotIn("NSAllowsArbitraryLoads", source); self.assertNotIn("NSAllowsArbitraryLoadsInWebContent", source)

    def test_prepare_occurs_after_actual_installed_byte_readback_and_sdk_return_before_original_launch(self):
        run = functions(APP_SOURCE)["run"]
        node = prepare_node(); source = (ROOT / APP_SOURCE).read_text()
        self.assertLess(source.index('receipt["steps"][phase]["installed_owned_bytes_verified"] = installed'), source.index('if content_fixture_requested:'))
        sdk = next(item for item in ast.walk(run) if isinstance(item, ast.If) and ast.unparse(item.test) == "appinfo_shape_only" and
                   any(isinstance(child, ast.Return) for child in ast.walk(item)))
        self.assertLess(sdk.end_lineno, node.lineno)
        launch = next(item for item in ast.walk(run) if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == "forward_application")
        self.assertLess(node.end_lineno, launch.lineno)
        self.assertEqual(1, sum(isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and
                                item.func.attr == "OwnedContentPolicyFixture" for item in ast.walk(run)))

    def test_prepare_binds_actual_caller_hashes_freezes_original_nonce_and_copies_process_environment_once(self):
        namespace, fixture, module, events, validate = self.namespace()
        inherited = {"MODEL_INHERITED": "unchanged"}
        with patch.dict(sys.modules, {"webview_content_policy_fixture": module}), patch.dict(os.environ, inherited, clear=True):
            before = dict(os.environ); model(prepare_node(), namespace)
            self.assertEqual(before, dict(os.environ))
        self.assertIs(fixture, namespace["content_fixture"])
        self.assertEqual(["construct", "source-contract"], events[:2])
        self.assertEqual(("bind", ROOT, {"bundle_id": namespace["bundle_id"], "signed_hash": namespace["signed_hash"], "plist_hash": namespace["plist_hash"]}), events[2])
        self.assertEqual("nonce", events[3]); self.assertEqual(("environment", inherited), events[4])
        self.assertEqual("d" * 64, namespace["content_nonce_hash"])
        self.assertEqual(namespace["content_nonce_hash"], namespace["receipt"]["webview_content_policy_nonce_sha256"])
        self.assertEqual("unchanged", namespace["native_environment"]["MODEL_INHERITED"])
        self.assertEqual(1, len([event for event in events if isinstance(event, tuple) and event[0] == "environment"]))
        validate.assert_not_called()

    def test_prepare_bind_failure_still_leaves_owned_fixture_for_independent_close_and_receipt(self):
        namespace, fixture, module, events, validate = self.namespace(bind_error=ValueError("source-model refusal"))
        with patch.dict(sys.modules, {"webview_content_policy_fixture": module}):
            with self.assertRaises(ValueError): model(prepare_node(), namespace)
        self.assertIs(fixture, namespace["content_fixture"])
        model(cleanup_node(), namespace)
        self.assertIn("close", events); self.assertIn("receipt", events)
        self.assertIsNone(validate.call_args.kwargs["nonce_hash"])

    def test_close_failure_retains_sanitized_receipt_validates_independently_and_cannot_skip_later_cleanup(self):
        namespace, fixture, module, events, validate = self.namespace(close_error=OSError("source-model close refusal"))
        namespace["content_fixture"] = fixture; namespace["content_nonce_hash"] = "d" * 64
        model(cleanup_node(), namespace); events.append("modeled-later-owned-cleanup")
        self.assertEqual(["construct", "close", "receipt", "modeled-later-owned-cleanup"], events)
        self.assertEqual({"source_model_only": True}, namespace["receipt"]["webview_content_policy_fixture"])
        self.assertFalse(namespace["receipt"]["transport_passed"])
        self.assertEqual("OSError", namespace["receipt"]["webview_content_policy_fixture_cleanup_error_type"])
        validate.assert_called_once()

    def test_receipt_failure_and_validation_refusal_preserve_transport_failure_and_independent_continuation(self):
        for kwargs in ({"receipt_error": RuntimeError("source-model receipt refusal")}, {"validated": False}):
            namespace, fixture, module, events, validate = self.namespace(**kwargs)
            namespace["content_fixture"] = fixture; namespace["content_nonce_hash"] = "d" * 64
            model(cleanup_node(), namespace); events.append("modeled-later-owned-cleanup")
            self.assertFalse(namespace["receipt"]["transport_passed"]); self.assertIn("error", namespace["receipt"])
            self.assertEqual("modeled-later-owned-cleanup", events[-1])
            self.assertEqual(["construct", "close", "receipt"], events[:-1])

    def test_cleanup_supplies_actual_protocol_pid_three_current_sources_installed_hashes_and_original_nonce(self):
        namespace, fixture, module, events, validate = self.namespace()
        namespace["content_fixture"] = fixture; namespace["content_nonce_hash"] = "d" * 64
        model(cleanup_node(), namespace)
        self.assertEqual({"bundle_id": namespace["bundle_id"], "signed_hash": namespace["signed_hash"], "plist_hash": namespace["plist_hash"],
                          "native_pid": namespace["protocol"].observed_launch_pid, "fixture_hash": policy.SOURCE_SHA256[policy.IOS_FIXTURE],
                          "native_hash": policy.SOURCE_SHA256[policy.spec(policy.IOS_FOCUS)["source"]],
                          "helper_hash": policy.SOURCE_SHA256[policy.IOS_HELPER], "nonce_hash": "d" * 64}, validate.call_args.kwargs)
        self.assertTrue(namespace["receipt"]["transport_passed"])
        self.assertEqual({"source_model_only": True}, validate.call_args.args[0])

    def test_original_launch_argv_timeout_runtime_sdk_helpers_and_every_old_cleanup_block_are_byte_ast_unchanged(self):
        current = (ROOT / APP_SOURCE).read_bytes(); old = history.source_before_content_policy(APP_SOURCE, current)
        before = functions(APP_SOURCE, old); after = functions(APP_SOURCE, current)
        self.assertEqual(set(before), set(after))
        for name in set(before) - {"run"}:
            self.assertEqual(ast.dump(before[name], include_attributes=False), ast.dump(after[name], include_attributes=False))
        def calls(node, name):
            return [ast.dump(item, include_attributes=False) for item in ast.walk(node) if isinstance(item, ast.Call) and
                    ((isinstance(item.func, ast.Name) and item.func.id == name) or
                     (isinstance(item.func, ast.Attribute) and item.func.attr == name))]
        self.assertEqual(calls(before["run"], "forward_application"), calls(after["run"], "forward_application"))
        self.assertEqual(calls(before["run"], "capture"), calls(after["run"], "capture"))
        old_try = next(node for node in before["run"].body if isinstance(node, ast.Try) and node.finalbody)
        new_try = next(node for node in after["run"].body if isinstance(node, ast.Try) and node.finalbody)
        remaining = [node for node in new_try.finalbody if not (isinstance(node, ast.If) and ast.unparse(node.test) == "content_fixture is not None")]
        self.assertEqual(ast.dump(ast.Module(old_try.finalbody, []), include_attributes=False), ast.dump(ast.Module(remaining, []), include_attributes=False))
        old_collect = functions(LIBRARY_SOURCE, history.source_before_content_policy(LIBRARY_SOURCE, (ROOT / LIBRARY_SOURCE).read_bytes()))["collect_one_ios_application_receipt"]
        new_collect = functions(LIBRARY_SOURCE)["collect_one_ios_application_receipt"]
        original_need = [ast.dump(node, include_attributes=False) for node in ast.walk(old_collect) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "need"]
        current_need = [ast.dump(node, include_attributes=False) for node in ast.walk(new_collect) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "need"]
        self.assertTrue(set(original_need) <= set(current_need))

    def test_new_application_filter_is_exact_four_methods_permutation_not_whole_class_or_partial_registry(self):
        base = sorted(application.TEST_ARGUMENTS); selected = policy.selector(policy.IOS_FOCUS).split(",")
        for methods in (selected, list(reversed(selected))):
            self.assertEqual(policy.IOS_FOCUS, application.application_test_focus(base + ["--ktest_gradle_filter=" + ",".join(methods)]))
        for methods in (selected[:-1], selected + [selected[0]], [policy.spec(policy.IOS_FOCUS)["classname"]], ["*"], [selected[0] + "*", *selected[1:]]):
            with self.assertRaises(ValueError): application.application_test_focus(base + ["--ktest_gradle_filter=" + ",".join(methods)])
        host = application.application_host("calf-webview/build/bin/iosSimulatorArm64/applicationDebugTest/application.kexe", policy.IOS_FOCUS)
        self.assertEqual(policy.MODULE, host["module"])

    def test_native_case_receipt_block_requires_exact_focus_current_source_original_nonce_and_actual_protocol_witnesses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); copy_model_checkout(root); plan = native_plan(root, policy.IOS_FOCUS)
            contract = policy.source_contract(root, policy.IOS_FOCUS); row = policy.spec(policy.IOS_FOCUS)
            validate = Mock(return_value=True)
            fake = SimpleNamespace(SOURCE=policy.IOS_FIXTURE, NATIVE_SOURCE=row["source"], NATIVE_HELPER=policy.IOS_HELPER, validate_receipt=validate)
            document = {"bundle_id": "source-model-bound-app", "signed_application_executable_sha256": "a" * 64,
                        "application_plist_sha256": "b" * 64, "webview_content_policy_nonce_sha256": "d" * 64,
                        "webview_content_policy_fixture": {"source_model_only": True}}
            def need(condition, message):
                if not condition: raise ValueError(message)
            namespace = {"root": root, "test_plan": plan, "expected": plan["expected"][0], "content_policy": policy,
                         "cases": {(row["classname"], method): "passed" for method in row["methods"]}, "need": need,
                         "document": document, "protocol": {"observed_launch_pid": 321}, "re": __import__("re")}
            with patch.dict(sys.modules, {"webview_content_policy_fixture": fake}):
                model(validation_node(), namespace)
                self.assertEqual(contract["source_hashes"][policy.IOS_HELPER], validate.call_args.kwargs["helper_hash"])
                self.assertEqual(321, validate.call_args.kwargs["native_pid"]); self.assertEqual("d" * 64, validate.call_args.kwargs["nonce_hash"])
                for bad in (None, "not-a-hash"):
                    document["webview_content_policy_nonce_sha256"] = bad
                    with self.assertRaises(ValueError): model(validation_node(), namespace)
                document["webview_content_policy_nonce_sha256"] = "d" * 64; validate.return_value = False
                with self.assertRaises(ValueError): model(validation_node(), namespace)

    def test_unfocused_ios_all_source_blocker_is_real_full_generated_admission_without_new_fixture_selectors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); copy_model_checkout(root)
            plan = r.plan(root, "ios", only_modules=(policy.MODULE,)); item = plan["expected"][0]
            self.assertIn(policy.spec(policy.IOS_FOCUS)["source"], item["test_source_files"])
            self.assertNotIn("test_filter", item); self.assertNotIn(policy.CONTRACT_FIELD, item)
        host = (ROOT / "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeWebViewApplicationHost.kt").read_text()
        self.assertIn("testLauncherEntryPoint(it)", host)
        helper = (ROOT / policy.IOS_HELPER).read_text()
        for name in ("NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN", "NATIVECMPKIT_WEBVIEW_CONTENT_ORIGIN_PORT", "NATIVECMPKIT_WEBVIEW_CONTENT_SECOND_PORT"):
            self.assertIn(name, helper)
        namespace = {"content_policy": policy, "cases": {(policy.spec(policy.IOS_FOCUS)["classname"], policy.spec(policy.IOS_FOCUS)["methods"][0]): "passed"},
                     "test_plan": {}, "need": lambda condition, _: condition or (_ for _ in ()).throw(ValueError("generic content admission refused"))}
        with patch.dict(sys.modules, {"webview_content_policy_fixture": SimpleNamespace()}):
            with self.assertRaises(ValueError): model(validation_node(), namespace)
