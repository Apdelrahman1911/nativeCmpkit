# SPDX-License-Identifier: Apache-2.0
"""Important OS-geometry wiring/refusal controls; zero UIKit/native executions."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as library
import workflow_matrix as workflow
import ios_geometry_simulator_source_projection as owned_history

ROOT = Path(__file__).resolve().parents[2]
UDID = "726D52AF-426A-408A-974D-CA8B9BE8A479"


def simulator(kind="iphone"):
    return {"state": "Booted", "udid": UDID, "runtime_version": "26.5",
            "device_type": "com.apple.CoreSimulator.SimDeviceType." +
                           ("iPhone-Air" if kind == "iphone" else "iPad-Pro-13-inch-M5")}


class PopoverGeometryControls(unittest.TestCase):
    def test_nested_manifest_booleans_cannot_be_numeric_zero(self):
        import ios_popover_geometry_plan as geometry
        focus = geometry.FOCUSES[0]
        expected = geometry.application_fixture(ROOT, simulator(), focus)
        self.assertTrue(geometry.validate_application_fixture(expected, ROOT, simulator(), focus))
        paths = (("scene_information", "UIApplicationSceneManifest", "UIApplicationSupportsMultipleScenes"),
                 ("scene_information", "UIRequiresFullScreen"))
        for path in paths:
            for value in (0, 0.0, "false", None):
                changed = copy.deepcopy(expected)
                target = changed
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                self.assertFalse(geometry.validate_application_fixture(changed, ROOT, simulator(), focus), (path, value))

    def test_fixture_top_level_types_extra_fields_and_cycles_refuse(self):
        import ios_popover_geometry_plan as geometry
        focus = geometry.FOCUSES[0]
        expected = geometry.application_fixture(ROOT, simulator(), focus)
        for key, value in (("schema_version", True), ("scene_mode_requested", 1),
                           ("legacy_activation_fallback_allowed", 0), ("packages_published", True),
                           ("real_split_view_verified", True), ("unexpected", False)):
            changed = copy.deepcopy(expected); changed[key] = value
            self.assertFalse(geometry.validate_application_fixture(changed, ROOT, simulator(), focus), (key, value))
        cyclic = copy.deepcopy(expected); cyclic["scene_information"] = cyclic
        self.assertFalse(geometry.validate_application_fixture(cyclic, ROOT, simulator(), focus))
        class Foreign(dict):
            def __eq__(self, other):
                raise AssertionError("Foreign equality must never execute")
        self.assertFalse(geometry.validate_application_fixture(Foreign(expected), ROOT, simulator(), focus))

    def test_each_host_selects_one_new_case_and_no_accepted_bar_methods(self):
        import ios_popover_geometry_plan as geometry
        for index, kind in enumerate(("iphone", "ipad")):
            focus = geometry.FOCUSES[index]
            self.assertEqual({"include": [{"slot": "ios-" + kind, "suite": "ios", "runner": "macos-26",
                "arch": "arm64", "python": "python3", "simulator-kind": kind,
                "test-modules": "calf-ui", "test-focus": focus}]}, workflow.matrix("ios-popover-geometry-" + kind))
            plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=focus)
            self.assertEqual([{"classname": "iosSimulatorArm64ApplicationTest." + geometry.CLASS,
                "name": geometry.METHODS[index] + "[iosSimulatorArm64]"}], plan["expected"][0]["required_testcases"])
            self.assertFalse(plan["complete_suite_requested"])
            self.assertIn("NOT real split view", plan["scope"])
            self.assertIn(geometry.NATIVE, plan["expected"][0]["test_source_files"])
            self.assertIn(geometry.SCENE, plan["expected"][0]["test_source_files"])

    def test_foreign_suite_module_and_modified_host_cannot_select_geometry(self):
        import ios_popover_geometry_plan as geometry
        for focus in geometry.FOCUSES:
            for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-share",)), ("ios", None)):
                self.assertFalse(library.allowed_test_focus(suite, modules, focus))
        for kind in ("iphone", "ipad"):
            profile = "ios-popover-geometry-" + kind
            with patch.dict(workflow.PROFILES, {profile: ("desktop-macos-arm64",)}), self.assertRaises(ValueError):
                workflow.matrix(profile)
            with patch.dict(workflow.MODULE_SUBSETS, {profile: "calf-share"}), self.assertRaises(ValueError):
                workflow.matrix(profile)

    def test_recorded_booted_idiom_and_minimum_native_os_are_required(self):
        import ios_popover_geometry_plan as geometry
        for index, kind in enumerate(("iphone", "ipad")):
            focus = geometry.FOCUSES[index]
            self.assertEqual(kind, geometry.expected_idiom(simulator(kind), focus))
            for key, value in (("state", "Shutdown"), ("device_type", simulator("ipad" if kind == "iphone" else "iphone")["device_type"]),
                               ("runtime_version", "15.9"), ("runtime_version", "26.5junk"), ("runtime_version", True)):
                changed = simulator(kind); changed[key] = value
                with self.assertRaises(ValueError): geometry.expected_idiom(changed, focus)
        with self.assertRaises(ValueError): geometry.expected_idiom(simulator(), "whole-ios")

    def test_scene_manifest_and_launch_mode_are_exact_not_split_view_evidence(self):
        import ios_popover_geometry_plan as geometry
        info = geometry.scene_information()
        self.assertIs(False, info["UIApplicationSceneManifest"]["UIApplicationSupportsMultipleScenes"])
        self.assertIs(False, info["UIRequiresFullScreen"])
        configurations = info["UIApplicationSceneManifest"]["UISceneConfigurations"]
        self.assertEqual([{"UISceneConfigurationName": "NativeCmpKitGeometry", "UISceneClassName": "UIWindowScene",
            "UISceneDelegateClassName": "NativeCmpKitPopoverGeometrySceneDelegate"}],
            configurations["UIWindowSceneSessionRoleApplication"])
        for index, kind in enumerate(("iphone", "ipad")):
            self.assertEqual({"NATIVECMPKIT_OWNED_POPOVER_GEOMETRY": "1", "NATIVECMPKIT_POPOVER_GEOMETRY_IDIOM": kind},
                geometry.launch_environment(simulator(kind), geometry.FOCUSES[index]))
            fixture = geometry.application_fixture(ROOT, simulator(kind), geometry.FOCUSES[index])
            self.assertIs(False, fixture["real_split_view_verified"])
            self.assertIs(False, fixture["legacy_activation_fallback_allowed"])

    def test_process_environment_forwards_only_owned_app_keys_without_mutation(self):
        import ios_popover_geometry_plan as geometry
        original = {"PATH": "/usr/bin", "UNRELATED_SETTING": "synthetic"}
        for index, kind in enumerate(("iphone", "ipad")):
            environment = geometry.process_launch_environment(simulator(kind), geometry.FOCUSES[index], environment=original)
            self.assertEqual(original | {"SIMCTL_CHILD_NATIVECMPKIT_OWNED_POPOVER_GEOMETRY": "1",
                "SIMCTL_CHILD_NATIVECMPKIT_POPOVER_GEOMETRY_IDIOM": kind}, environment)
            environment["PATH"] = "changed copy"
            self.assertEqual({"PATH": "/usr/bin", "UNRELATED_SETTING": "synthetic"}, original)
            fixture = geometry.application_fixture(ROOT, simulator(kind), geometry.FOCUSES[index])
            self.assertNotIn("PATH", fixture["launch_environment"])
            self.assertNotIn("UNRELATED_SETTING", fixture["launch_environment"])

    def test_foreign_inherited_geometry_environment_refuses_instead_of_overriding(self):
        import ios_popover_geometry_plan as geometry
        for key, value in (("SIMCTL_CHILD_NATIVECMPKIT_OWNED_POPOVER_GEOMETRY", "0"),
                           ("SIMCTL_CHILD_NATIVECMPKIT_POPOVER_GEOMETRY_IDIOM", "ipad")):
            with self.assertRaises(ValueError):
                geometry.process_launch_environment(simulator(), geometry.FOCUSES[0], environment={key: value})
        for environment in ([], {"PATH": False}, {1: "/usr/bin"}):
            with self.assertRaises(ValueError):
                geometry.process_launch_environment(simulator(), geometry.FOCUSES[0], environment=environment)

    def test_exact_four_input_compiler_and_one_method_filter(self):
        import ios_popover_geometry_plan as geometry
        source = (ROOT / geometry.INIT_SCRIPT).read_text()
        self.assertEqual(list(geometry.SOURCES), re.findall(r'"(calf-ui/src/ios[^"\n]+\.kt)"', source))
        self.assertIn('common.setFrom(emptyList<Any>())', source)
        self.assertIn('compilation.inputs.property("nativecmpkitPopoverGeometryFocus", focus!!)', source)
        self.assertNotIn('sourceSets.getByName', source)
        for index, focus in enumerate(geometry.FOCUSES):
            plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=focus)
            command = library.gradle_command("ios", plan, UDID)
            self.assertEqual(1, command.count(geometry.INIT_SCRIPT))
            self.assertIn("-PnativecmpkitPopoverGeometryFocus=" + focus, command)
            self.assertEqual([geometry.CLASS + "." + geometry.METHODS[index]],
                [command[i + 1] for i, value in enumerate(command) if value == "--tests"])

    def test_fresh_compiler_receipt_rejects_types_drift_and_extra_execution(self):
        import ios_popover_geometry_plan as geometry
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in geometry.SOURCES:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes())
            receipt = root / geometry.RECEIPT; receipt.parent.mkdir(parents=True, exist_ok=True)
            focus = geometry.FOCUSES[0]
            document = {"task": ":calf-ui:compileTestKotlinIosSimulatorArm64", "focus": focus,
                "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in geometry.SOURCES},
                "effective_sources": list(geometry.SOURCES), "excluded_unrelated_test_sources": True,
                "production_source_sets_changed": False, "native_tests_executed": 0,
                "scope": "Actual precompiler source admission only; compiler exit and fresh native XML decide outcomes"}
            now = time.time_ns()
            def write(value):
                receipt.write_text(json.dumps(value)); os.utime(receipt, ns=(now, now))
            write(document)
            self.assertTrue(geometry.validate_compilation(root, now, now + 1000000000, focus))
            for key, value in (("focus", geometry.FOCUSES[1]), ("native_tests_executed", False), ("native_tests_executed", 1),
                               ("production_source_sets_changed", 0), ("excluded_unrelated_test_sources", 1),
                               ("effective_sources", list(geometry.SOURCES)[:-1]), ("extra", 0)):
                changed = copy.deepcopy(document); changed[key] = value; write(changed)
                self.assertFalse(geometry.validate_compilation(root, now, now + 1000000000, focus), (key, value))
            write(document); (root / geometry.SCENE).write_text("changed source\n")
            self.assertFalse(geometry.validate_compilation(root, now, now + 1000000000, focus))

    def test_stale_duplicate_nonfinite_and_invalid_clock_receipts_refuse(self):
        import ios_popover_geometry_plan as geometry
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in geometry.SOURCES:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes())
            target = root / geometry.RECEIPT; target.parent.mkdir(parents=True, exist_ok=True)
            now = time.time_ns()
            for raw in ('{"focus":"a","focus":"b"}', '{"focus":NaN}', '{}'):
                target.write_text(raw); os.utime(target, ns=(now, now))
                self.assertFalse(geometry.validate_compilation(root, now, now + 1000000000, geometry.FOCUSES[0]))
            for started, ended in ((True, now), (0, now), (now, now - 1), (now, False)):
                self.assertFalse(geometry.validate_compilation(root, started, ended, geometry.FOCUSES[0]))
            os.utime(target, ns=(now - 3000000000, now - 3000000000))
            self.assertFalse(geometry.validate_compilation(root, now, now + 1000000000, geometry.FOCUSES[0]))

    def test_native_inputs_require_real_orientation_traits_and_same_presenter(self):
        import ios_popover_geometry_plan as geometry
        source = (ROOT / geometry.NATIVE).read_text()
        self.assertEqual(list(geometry.METHODS), re.findall(r'@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)', source))
        for token in ("scene.requestGeometryUpdateWithPreferences", "scene.interfaceOrientation == target",
                      "UIWindowSceneGeometryPreferencesIOS", "parent.traitCollection.horizontalSizeClass",
                      "UIUserInterfaceSizeClassRegular", "UIUserInterfaceSizeClassCompact",
                      "sameNativeObject(alert, parent.presentedViewController)", "sameRect(checkNotNull(source).bounds, popover.sourceRect)",
                      "geometry(checkNotNull(originalOrientation))", "1.0, 1.0), rect)"):
            self.assertIn(token, source)
        for token in ("setOverrideTraitCollection", "UIDevice.currentDevice.setValue", "willRepositionPopoverToRect",
                      "performSelector", "setBounds", "@Ignore", "@Disabled"):
            self.assertNotIn(token, source)
        between = source.split("geometry(UIInterfaceOrientationLandscapeLeft)", 1)[1].split("waitForNative", 1)[0]
        self.assertNotIn("manager", between)

    def test_scene_delegate_owns_connection_before_real_activation(self):
        import ios_popover_geometry_plan as geometry
        scene = (ROOT / geometry.SCENE).read_text()
        host = (ROOT / geometry.HOST).read_text()
        self.assertIn('@ExportObjCClass(name = "NativeCmpKitPopoverGeometrySceneDelegate")', scene)
        self.assertLess(scene.index("connected = windowScene"), scene.index("owner().connectOwnedPopoverGeometryScene"))
        self.assertIn("override fun sceneDidBecomeActive(scene: UIScene)", scene)
        self.assertIn("sameNativeObject(connected, scene)", scene)
        self.assertIn("check(NSThread.isMainThread)", scene)
        self.assertNotIn("@Test", scene)
        self.assertIn("if (ownedPopoverGeometryRequested()) return // Do not substitute legacy activation", host)
        self.assertIn("requestGeneratedTestActivation() // Called only by the genuine owned scene", host)
        self.assertIn("check(value == null || value == \"1\")", host)
        self.assertLess(host.index("ownedGeometryScene = scene"), host.index("UIWindow(windowScene = scene)"))

    def test_scene_lifetime_and_geometry_cleanup_keep_original_failures(self):
        import ios_popover_geometry_plan as geometry
        native = (ROOT / geometry.NATIVE).read_text()
        host = (ROOT / geometry.HOST).read_text()
        self.assertIn("attemptedGeometry = true // Own restoration before", native)
        self.assertIn("prior.addSuppressed(failure)", native)
        self.assertIn("manager?.dispose(); source?.removeFromSuperview()", native)
        self.assertIn("waitForNative { parent.presentedViewController == null }", native)
        release = host.split("private fun releaseMainLeases()", 1)[1].split("private fun pollCompletion", 1)[0]
        self.assertIn("ownedGeometryScene = null", release)
        self.assertIn("timer?.invalidate()", release)
        self.assertIn("ownedWindow?.rootViewController = null", release)

    def test_collector_requires_fresh_compiler_and_exact_scene_fixture(self):
        import ios_popover_geometry_plan as geometry
        library_source = (ROOT / "scripts/ci/library_tests.py").read_text()
        application = (ROOT / "scripts/ci/ios_ui_application.py").read_text()
        self.assertIn('geometry_plan.validate_compilation(root, started_ns, ended_ns, test_plan["explicit_test_focus"])', library_source)
        self.assertIn('geometry_plan.validate_application_fixture(document.get("popover_geometry"), root, context["simulator"]', library_source)
        self.assertIn('information.update(geometry_plan.scene_information())', application)
        self.assertIn('receipt["popover_geometry"] = geometry_plan.application_fixture(root, before["simulator"], focus)', application)
        self.assertIn('native_environment = geometry_plan.process_launch_environment(before["simulator"], focus)', application)
        self.assertTrue(geometry.validate_sources(ROOT))

    def test_exact_fragment_roundtrip_preserves_every_existing_input_preimage(self):
        import ios_popover_geometry_source_projection as geometry
        bindings = geometry._bindings()
        self.assertEqual(7, len(bindings))
        self.assertEqual(24, sum(len(b["fragments"]) for b in bindings.values()))
        for name, binding in bindings.items():
            current = owned_history.current_source_before_owned_geometry(name, (ROOT / name).read_bytes())
            previous = geometry.current_source_before_geometry(name, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            forward = previous
            for fragment in binding["fragments"]:
                self.assertEqual(1, forward.count(fragment["before"].encode()))
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(current, forward)

    def test_ordinary_routes_exclude_the_owner_only_opt_in_geometry_tree(self):
        import ios_popover_geometry_plan as geometry
        self.assertNotIn("iosGeometryTest", library.KNOWN_TEST_SETS)
        for suite, focus in (("ios", library.IOS_POPOVER_BAR_RECOVERY_FOCUS),
                             ("desktop", library.DATE_TRANSACTION_FOCUS)):
            plan = library.plan(ROOT, suite, only_modules=("calf-ui",), focus=focus)
            self.assertNotIn(geometry.NATIVE, plan["expected"][0]["test_source_files"])
            self.assertNotIn(geometry.SCENE, plan["expected"][0]["test_source_files"])
            self.assertNotIn("iosGeometryTest", plan["expected"][0]["test_source_sets"])

    def test_historical_partial_foreign_sources_never_admit_as_current(self):
        import ios_popover_geometry_source_projection as geometry
        for name in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml"):
            current = owned_history.current_source_before_owned_geometry(name, (ROOT / name).read_bytes())
            before = geometry.current_source_before_geometry(name, current)
            self.assertEqual(before, geometry.source_before_geometry(name, before))
            for bad in (before, current[:-1], current + b"\n", b"", None, bytearray(current)):
                with self.assertRaises(ValueError): geometry.current_source_before_geometry(name, bad)
        self.assertNotIn("ios_popover_bar_recovery_source_projection", (ROOT / "scripts/ci/ios_popover_geometry_source_projection.py").read_text())

    def test_current_source_validation_refuses_drift_or_symlink(self):
        import ios_popover_geometry_plan as plan
        import ios_popover_geometry_source_projection as geometry
        spec = json.loads(geometry.SPEC_PATH.read_bytes())
        paths = set(spec["bindings"]) | set(spec["added_inputs"])
        owning = owned_history._document()
        paths |= set(owning["bindings"]) | set(owning["added_inputs"])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in paths:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes())
            self.assertTrue(geometry.validate_current_sources(root))
            source = root / plan.SCENE
            original = source.read_bytes(); source.write_bytes(original + b"\n")
            with self.assertRaises(ValueError): geometry.validate_current_sources(root)
            source.unlink(); source.symlink_to(ROOT / plan.SCENE)
            with self.assertRaises(ValueError): geometry.validate_current_sources(root)

    def test_ancestor_projection_reuses_old_pins_without_replaying_native(self):
        import ios_popover_geometry_source_projection as geometry
        import ios_popover_bar_recovery_source_projection as bar
        import ios_popover_anchor_source_projection as anchor
        import ios_worker_completion_source_projection as worker
        for name in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml"):
            current = owned_history.current_source_before_owned_geometry(name, (ROOT / name).read_bytes())
            before = geometry.current_source_before_geometry(name, current)
            self.assertEqual(bar.current_source_before_bar_recovery(name, before), bar.current_source_before_bar_recovery(name, current))
            self.assertEqual(anchor.current_source_before_popover_anchor(name, before), anchor.current_source_before_popover_anchor(name, current))
            self.assertEqual(worker.current_source_before_worker_completion(name, before), worker.current_source_before_worker_completion(name, current))
        self.assertEqual("145287111a3c12354efa3b30c2df93ee3a8120f3a42a37f2193a02d17065544f",
                         hashlib.sha256(anchor.SPEC_PATH.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
