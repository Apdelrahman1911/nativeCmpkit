# SPDX-License-Identifier: Apache-2.0
"""NEW public admission/private source-order and bounded mocked lifecycle controls.

No SDK, KVM, emulator, Gradle, native library API, compiler or consumer work is
executed. Mocked receipts do not prove native functionality or release readiness.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import android_device_tests as c
from test_android_device_controller import ControllerReceipts


class ControllerAdmissionContextControls(unittest.TestCase):
    def setUp(self):
        self.fixture = ControllerReceipts(methodName="runTest")
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.relative = self.fixture.relative

    def scoped_plan(self):
        return {"suite": "android-device", "expected": [{"project": ":calf-webview", "module": "calf-webview"}],
                "complete_suite_requested": False, "explicit_module_subset": ["calf-webview"],
                "test_bearing_modules_not_requested": ["calf-file-picker", "calf-io"]}

    def test_public_unrestricted_camera_default_refuses_before_host_source_output_sdk_and_lock(self):
        for modules in (None, (), ("calf-camera-picker",)):
            with self.subTest(modules=modules), patch.object(c, "require_host") as host, \
                    patch.object(c.lt, "plan") as plan, patch.object(c.lt, "safe_path") as path, \
                    patch.object(c, "sdk_assets") as sdk, patch.object(c.os, "open") as lock:
                with self.assertRaises(ValueError): c.run(self.root, self.relative, only_modules=modules)
                host.assert_not_called(); plan.assert_not_called(); path.assert_not_called(); sdk.assert_not_called(); lock.assert_not_called()
                self.assertFalse((self.root / "build").exists())

    def test_public_explicit_unfiltered_io_preserves_source_refusal_before_host_output_sdk_and_lock(self):
        refusal = ValueError("synthetic owning IO source refusal, never native output")
        with patch.object(c.lt, "plan", side_effect=refusal) as plan, patch.object(c, "require_host") as host, \
                patch.object(c.lt, "safe_path") as path, patch.object(c, "sdk_assets") as sdk, patch.object(c.os, "open") as lock:
            with self.assertRaises(ValueError) as caught: c.run(self.root, self.relative, only_modules=("calf-io",))
            self.assertIs(refusal, caught.exception)
            plan.assert_called_once_with(self.root, "android-device", only_modules=("calf-io",))
            host.assert_not_called(); path.assert_not_called(); sdk.assert_not_called(); lock.assert_not_called()
            self.assertFalse((self.root / "build").exists())

    def test_direct_private_all_finite_or_unfiltered_source_refusals_precede_paths_and_sdk_lookup(self):
        lifecycle_focus = sorted(c.permission_lifecycle_contract.FOCUSES)[0]
        selections = (("calf-webview", None), ("calf-webview", c.lt.ANDROID_WEBVIEW_REQUEST_FOCUS),
                      ("calf-io", c.lt.ANDROID_IO_REMOTE_FOCUSES[0]), ("calf-permissions/core", lifecycle_focus))
        for module, focus in selections:
            with self.subTest(module=module, focus=focus), patch.object(c.lt, "plan", side_effect=ValueError("synthetic source refusal")) as plan, \
                    patch.object(c.lt, "safe_path") as path, patch.object(c, "sdk_assets") as sdk:
                with self.assertRaises(ValueError):
                    c._run(self.root, self.relative, only_modules=(module,), **({"focus": focus} if focus is not None else {}))
                plan.assert_called_once_with(self.root, "android-device", only_modules=(module,),
                                             **({"focus": focus} if focus is not None else {}))
                path.assert_not_called(); sdk.assert_not_called(); self.assertFalse((self.root / "build").exists())

    def test_direct_private_one_fresh_plan_feeds_source_suite_discovery_assembly_execution_and_receipts(self):
        self.fixture.plan = self.scoped_plan()
        with self.fixture.controlled() as mocks:
            # The controlled fixture normally returns three mocked connected tasks.
            # This one-module case must supply its one exact mocked task instead.
            mocks["command"].return_value = ["./gradlew", "--no-parallel", ":calf-webview:connectedAndroidDeviceTest"]
            result = c._run(self.root, self.relative, only_modules=("calf-webview",))
        mocks["command"].assert_called_once_with("android-device", self.fixture.plan, android_serial=c.SERIAL)
        mocks["plan"].assert_called_once_with(self.root, "android-device", only_modules=("calf-webview",))
        source_suite = json.loads((self.root / self.relative / "plan.json").read_text())["source_suite"]
        self.assertEqual(self.fixture.plan, source_suite)
        self.assertEqual(["./gradlew", "--no-parallel", ":calf-webview:assembleAndroidDeviceTest"],
                         mocks["execute"].call_args_list[0].args[1])
        self.assertEqual(("calf-webview",), mocks["tests"].call_args.kwargs["only_modules"])
        self.assertTrue(result["passed"]); self.assertFalse(result["complete_suite_requested"])
        self.assertFalse(result["packages_published"]); self.assertFalse(result["release_readiness_certified"])

    def test_public_prehost_and_private_plan_are_fresh_independent_and_only_private_result_is_consumed(self):
        first = self.scoped_plan(); first["model-only-prehost-sentinel"] = True
        second = self.scoped_plan(); second["model-only-private-sentinel"] = True
        self.assertIsNot(first, second)
        events = []
        selections = iter((first, second))
        def admitted(*args, **kwargs):
            events.append("source-plan"); return next(selections)
        with self.fixture.controlled() as mocks, patch.object(c, "require_host", side_effect=lambda: events.append("host")), \
                patch.object(c, "sdk_assets", side_effect=lambda *a, **k: events.append("sdk") or {"system_image": c.IMAGE}):
            mocks["plan"].side_effect = admitted
            result = c.run(self.root, self.relative, only_modules=("calf-webview",))
        self.assertEqual(["source-plan", "host", "source-plan", "sdk"], events)
        expected = unittest.mock.call(self.root, "android-device", only_modules=("calf-webview",))
        self.assertEqual([expected, expected], mocks["plan"].call_args_list)
        stored = json.loads((self.root / self.relative / "plan.json").read_text())["source_suite"]
        self.assertEqual(second, stored); self.assertNotIn("model-only-prehost-sentinel", stored)
        self.assertTrue(result["passed"]); self.assertFalse(result["complete_suite_requested"])
        self.assertFalse((self.root / "build/ci-verification/.android-device-controller.lock").exists())

    def test_private_source_plan_precedes_missing_sdk_configuration_without_creating_output(self):
        with patch.object(c.os, "environ", {}), patch.object(c.lt, "plan", return_value=self.scoped_plan()) as plan, \
                patch.object(c, "sdk_assets") as sdk:
            with self.assertRaises(ValueError): c._run(self.root, self.relative, only_modules=("calf-webview",))
        plan.assert_called_once_with(self.root, "android-device", only_modules=("calf-webview",))
        sdk.assert_not_called(); self.assertFalse((self.root / "build").exists())

    def test_focused_public_private_source_refusal_still_releases_only_its_new_output_lock(self):
        focus = c.lt.ANDROID_WEBVIEW_REQUEST_FOCUS
        refusal = ValueError("synthetic current private source refusal")
        with patch.object(c, "require_host") as host, patch.object(c.lt, "plan", side_effect=refusal) as plan, \
                patch.object(c, "sdk_assets") as sdk:
            with self.assertRaises(ValueError) as caught:
                c.run(self.root, self.relative, only_modules=("calf-webview",), focus=focus)
        self.assertIs(refusal, caught.exception); host.assert_called_once()
        plan.assert_called_once_with(self.root, "android-device", only_modules=("calf-webview",), focus=focus)
        sdk.assert_not_called(); self.assertFalse((self.root / self.relative).exists())
        self.assertFalse((self.root / "build/ci-verification/.android-device-controller.lock").exists())


if __name__ == "__main__":
    unittest.main()
