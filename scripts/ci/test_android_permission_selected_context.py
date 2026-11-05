# SPDX-License-Identifier: Apache-2.0
"""NEW selected-dependency source/models; no library/controller/native execution."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import android_permission_selected_context as context
import test_android_permission_demo_call_denial_recovery as recovery
import test_android_permission_demo_selector as selector


class PermissionSelectedContextControls(unittest.TestCase):
    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("Selected dependency source/models cannot launch external processes")
        for operation in ("run", "Popen"):
            guard = patch.object(subprocess, operation, forbidden)
            guard.start(); self.addCleanup(guard.stop)

    def test_both_contexts_keep_actual_lifecycle_specs_and_single_method_filters_without_demo_fallback(self):
        lifecycle = context.permission_lifecycle_context(recovery.source_at)
        environments = (recovery.owning_environment(), selector.owning_environment()[1])
        self.assertEqual(3, len(lifecycle.FOCUSES))
        for env in environments:
            self.assertEqual(lifecycle.SPECS, {focus: env["ANDROID_PERMISSION_DEVICE_SPECS"][focus]
                for focus in lifecycle.FOCUSES})
            for focus in sorted(lifecycle.FOCUSES):
                with self.subTest(environment=env["android_permission_device_filter"].__code__.co_filename, focus=focus):
                    spec = lifecycle.SPECS[focus]
                    self.assertEqual(lifecycle.CLASS + "#" + spec["methods"][0], env["android_permission_device_filter"](focus))
                    self.assertEqual(1, len(env["android_permission_device_identities"](focus)))
                    self.assertEqual(spec["declared_methods"], lifecycle.METHODS)
            self.assertEqual(recovery.CLASS, env["android_permission_device_filter"](env["ANDROID_PERMISSION_DEMO_FOCUS"]))
            self.assertEqual(recovery.METHODS + (recovery.PICKER,),
                env["ANDROID_PERMISSION_DEVICE_SPECS"][recovery.PROFILE]["declared_methods"])
            with self.assertRaises(KeyError): env["android_permission_device_filter"]("unknown-selected-context")

    def test_selected_pure_lifecycle_plan_validator_retains_exact_source_receipt_and_foreign_contract_refusals(self):
        lifecycle = context.permission_lifecycle_context(recovery.source_at)
        inputs = {relative: "1" * 64 for relative in lifecycle.SOURCE_FILES}
        digest = hashlib.sha256("".join(p + "\0" + inputs[p] + "\n" for p in sorted(inputs)).encode()).hexdigest()
        receipt = {"schema_version": 1, "source_inputs": inputs, "source_inputs_sha256": digest,
                   "source_policy_verified": True, "verification_api_level": lifecycle.API,
                   "native_or_compile_success_inferred": False}
        focus = sorted(lifecycle.FOCUSES)[0]
        plan = {"suite": "android-device", "explicit_test_focus": focus,
                "explicit_module_subset": [lifecycle.MODULE], "complete_suite_requested": False,
                "android_permission_lifecycle": {"package": lifecycle.PACKAGE, "source_fixture": lifecycle.FIXTURE,
                    "verification_api_level": lifecycle.API, "source_contract": receipt}}
        self.assertIsNone(lifecycle.validate_plan(plan))
        for name, mutate in (
            ("unrelated-focus", lambda p: p.update(explicit_test_focus=recovery.PROFILE)),
            ("default-focus", lambda p: p.update(explicit_test_focus=None)),
            ("foreign-module", lambda p: p.update(explicit_module_subset=["calf-io"])),
            ("complete-claim", lambda p: p.update(complete_suite_requested=True)),
            ("native-inference", lambda p: p["android_permission_lifecycle"]["source_contract"].update(native_or_compile_success_inferred=True)),
            ("missing-source", lambda p: p["android_permission_lifecycle"]["source_contract"]["source_inputs"].pop(lifecycle.SOURCE_FILES[0])),
            ("digest-drift", lambda p: p["android_permission_lifecycle"]["source_contract"].update(source_inputs_sha256="0" * 64)),
        ):
            with self.subTest(refusal=name), self.assertRaises(ValueError):
                changed = deepcopy(plan); mutate(changed); lifecycle.validate_plan(changed)
        env = recovery.owning_environment()
        demo = recovery.plan_model(env)
        self.assertIsNone(env["validate_android_permission_demo_plan"](demo))
        self.assertTrue(env["android_permission_demo_required"](demo))
        demo["android_permission_lifecycle"] = plan["android_permission_lifecycle"]
        with self.assertRaises(ValueError): env["validate_android_permission_demo_plan"](demo)

    def test_actual_lifecycle_alias_keeps_unrelated_matrix_and_three_exact_api35_permission_rows(self):
        env = recovery.matrix_environment()
        self.assertEqual(11, len(env["matrix"]("all")["include"]))
        for focus in sorted(env["permission_lifecycle"].FOCUSES):
            with self.subTest(focus=focus):
                row, = env["matrix"](focus)["include"]
                self.assertEqual({"slot": "android-device-api35", "suite": "android-device", "runner": "ubuntu-24.04",
                    "arch": "x64", "python": "python3", "emulator-api": "35", "test-modules": recovery.CORE,
                    "test-focus": focus}, row)
                self.assertFalse(any(key.startswith("serial-") or key == "android-batch" for key in row))

    def test_selected_actual_camera_admission_is_not_noop_and_dependency_ambiguity_refuses(self):
        camera = context.camera_callback_admission_context(recovery.source_at)
        self.assertIsNone(camera.validate_discovery("android-device", (recovery.CORE,), recovery.PROFILE, (camera.FOCUS,)))
        self.assertIsNone(camera.validate_discovery("android-device", (camera.MODULE,), camera.FOCUS, (camera.FOCUS,)))
        for modules in (None, (), (camera.MODULE,)):
            with self.subTest(unrestricted_modules=modules), self.assertRaises(ValueError):
                camera.validate_discovery("android-device", modules, None, (camera.FOCUS,))
        source = recovery.source_at(context.LIFECYCLE_SOURCE)
        for mutation in (source + "\nMODULE = 'foreign'\n", source.replace("def validate_plan(", "def missing_validate_plan(", 1),
                         "", "x" * (context.MAX_CONTEXT_SOURCE_BYTES + 1)):
            with self.subTest(mutated_source_bytes=len(mutation.encode())), self.assertRaises(ValueError):
                context.permission_lifecycle_context(lambda _: mutation)
        tree = recovery.syntax()
        extension = context.permission_spec_extension(tree)
        self.assertEqual("ANDROID_PERMISSION_DEVICE_SPECS", extension.value.func.value.id)
        tree.body.append(deepcopy(extension))
        with self.assertRaises(ValueError): context.permission_spec_extension(tree)


if __name__ == "__main__":
    unittest.main()
