# SPDX-License-Identifier: Apache-2.0
"""NEW cookie4 source/model controls only; zero native/network/compiler actions."""
from pathlib import Path
import ast
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/ci"))
import cookie_common_jdk_plan as plan
import cookie_common_jdk_source_projection as history


class CookieCommonJdkScope681Tests(unittest.TestCase):
    def test_new_four_literal_methods_are_the_only_command_selectors(self):
        result = plan.plan(ROOT)
        self.assertEqual(4, len(result["selectors"]))
        self.assertEqual(["--tests"] * 4, [v for v in result["command"] if v == "--tests"])
        self.assertEqual(list(plan.SELECTORS), [result["command"][i + 1] for i, v in enumerate(result["command"]) if v == "--tests"])
        self.assertEqual(2, result["common_methods_requested"])
        self.assertEqual(2, result["jdk_methods_requested"])
        self.assertEqual(0, result["native_methods_requested"])
        self.assertFalse(any(owner in selector for owner in plan.PARKED for selector in result["selectors"]))

    def test_new_unknown_focus_module_and_wire_labels_refuse_before_source_planning(self):
        for focus, module in [("all", plan.MODULE), ("remaining-v1", plan.MODULE), ("common-jdk4", "calf-ui"),
                              (True, plan.MODULE), (None, plan.MODULE)]:
            with self.subTest(focus=focus, module=module), self.assertRaises(ValueError):
                plan.plan(ROOT, focus, module)

    def test_new_plan_is_source_only_and_requires_two_fresh_xml_classes(self):
        result = plan.plan(ROOT)
        self.assertEqual(2, result["required_original_xml"])
        self.assertEqual(4, len(result["required_testcases"]))
        for key in ["compiler_executions_attested", "test_executions_attested"]:
            self.assertEqual(0, result[key])
        self.assertFalse(result["compiler_input_map_complete"])
        self.assertFalse(result["ROOT_shared671_CI668_composition_qualified"])
        self.assertEqual(plan.TASK, result["task"])
        self.assertEqual("--max-workers=1", result["command"][3])

    def test_new_four_bound_endpoints_inverse_and_forward_preserve_complete_bytes(self):
        document = history._document(ROOT)
        self.assertEqual(4, len(document["bindings"]))
        for name, row in document["bindings"].items():
            current = history.ordinary_bytes(ROOT, name)
            old = history.source_before_cookie(name, current)
            self.assertEqual(row["before_sha256"], history.sha(old))
            self.assertEqual(old, history.source_before_cookie(name, old))
            self.assertEqual(old, history.current_source_before_cookie(name, current))
            self.assertEqual(old, history.peel_cookie_for_history(name, current))
            rebuilt = old
            for fragment in row["fragments"]:
                rebuilt = rebuilt.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(current, rebuilt)

    def test_new_current_ingress_refuses_historical_and_partial_bound_images(self):
        for name in history.PREIMAGES:
            current = history.ordinary_bytes(ROOT, name)
            old = history.source_before_cookie(name, current)
            with self.subTest(path=name), self.assertRaises(ValueError):
                history.current_source_before_cookie(name, old)
            with self.subTest(path=name), self.assertRaises(ValueError):
                history.source_before_cookie(name, current + b"\n# unknown derivative\n")

    def test_new_history_is_idempotent_but_unlisted_bytes_are_not_certified(self):
        for name in history.PREIMAGES:
            old = history.source_before_cookie(name, history.ordinary_bytes(ROOT, name))
            self.assertEqual(old, history.peel_cookie_for_history(name, old))
            self.assertEqual(b"foreign", history.peel_cookie_for_history(name, b"foreign"))
        self.assertEqual(b"unlisted", history.source_before_cookie("unlisted.py", b"unlisted"))
        with self.assertRaises(ValueError):
            history.current_source_before_cookie(next(iter(history.PREIMAGES)), bytearray(b"bad"))

    def test_new_original_webview_manifest_production_and_build_pins_are_never_rewritten(self):
        raw = history.ordinary_bytes(ROOT, history.ORIGINAL_SPEC)
        self.assertEqual(history.ORIGINAL_SPEC_SHA256, history.sha(raw))
        original = json.loads(raw)
        for name in ["calf-webview/build.gradle.kts",
                     "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt"]:
            self.assertEqual(history.PREIMAGES[name], original["unchanged_inputs"][name])
        self.assertNotIn("AGENTS.md", history.fixture_inputs())

    def test_new_full_imported_reader_and_finite_cookie_definition_buckets_are_bound(self):
        document = history._document(ROOT)
        self.assertEqual(history.READER_SHA256, document["unchanged_inputs"][history.READER])
        self.assertEqual(history.READER_SHA256, history.sha(history.ordinary_bytes(ROOT, history.READER)))
        spec = json.loads(history.ordinary_bytes(ROOT, "scripts/ci/fixtures/cookie-wire-v1.json"))
        self.assertEqual(14, len(spec["cookies"]))
        self.assertEqual(12, len(spec["groups"]))
        self.assertEqual(["foo", "foo/child", "foobar", "private", "public"], spec["paths"])
        native = history.ordinary_bytes(ROOT, "scripts/ci/cookie_native_wire_fixture.py").decode()
        self.assertIn("from webview_content_policy_fixture import", native)
        self.assertIn(history.READER, history.fixture_inputs())

    def test_new_full_reader_tamper_outside_small_fixture_witness_refuses(self):
        import cookie_ci668_outer_source_projection as cookie_outer
        with tempfile.TemporaryDirectory(prefix="cookie-scope-model-") as directory:
            owned = Path(directory).resolve()
            for name in cookie_outer.fixture_inputs():
                target = owned / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            path = owned / history.READER
            path.write_bytes(path.read_bytes() + b"\n# NEW unknown full-reader tail\n")
            with self.assertRaisesRegex(ValueError, r"\AExact current Cookie outer input changed: scripts/ci/webview_content_policy_fixture\.py\Z"):
                history.validate_current_sources(owned)

    def test_new_ordinary_reader_refuses_symlink_hardlink_and_foreign_paths(self):
        with tempfile.TemporaryDirectory(prefix="cookie-reader-model-") as directory:
            owned = Path(directory).resolve()
            (owned / "source.py").write_bytes(b"dummy model source\n")
            (owned / "symlink.py").symlink_to(owned / "source.py")
            with self.assertRaises((ValueError, OSError)):
                history.ordinary_bytes(owned, "symlink.py")
            os.link(owned / "source.py", owned / "hardlink.py")
            with self.assertRaises(ValueError):
                history.ordinary_bytes(owned, "hardlink.py")
            for relative in ["../source.py", "/source.py", "./source.py", "source.py/../source.py"]:
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    history.ordinary_bytes(owned, relative)

    def test_new_each_platform_excludes_only_its_one_environment_dependent_class(self):
        build = history.ordinary_bytes(ROOT, "calf-webview/build.gradle.kts").decode()
        self.assertIn('tasks.withType<Test>().matching { it.name == "desktopTest" }', build)
        self.assertIn('tasks.withType<KotlinNativeTest>().configureEach', build)
        self.assertIn('tasks.withType<KotlinJsTest>().configureEach', build)
        for owner in plan.PARKED:
            self.assertEqual(1, build.count('excludeTestsMatching("' + owner + '.*")'))
        for selector in plan.SELECTORS:
            self.assertEqual(1, build.count('"' + selector + '"'))
        self.assertNotIn("@Ignore", build)
        self.assertNotIn('enabled = false', build)
        self.assertNotIn('setSrcDirs', build)

    def test_new_native_argument_view_preserves_original_unrelated_protocol_exactly(self):
        original = ["--ktest_logger=TEAMCITY", "--ktest_no_exit_code"]
        self.assertIs(original, plan.native_argument_view(original))
        selected = original + ["--ktest_gradle_filter=old.exact.Method"]
        self.assertEqual(selected, plan.native_argument_view(selected + [plan.NATIVE_EXCLUSION]))
        foreign = original + ["--ktest_negative_gradle_filter=foreign.*"]
        self.assertIs(foreign, plan.native_argument_view(foreign))
        # That unchanged old parser, not this source helper, must refuse foreign flags.
        plan.validate_native_exclusion_owner("calf-ui", original)
        with self.assertRaises(ValueError):
            plan.validate_native_exclusion_owner("calf-webview", original)

    def test_new_native_cookie_exclusion_cannot_be_duplicated_or_lent_to_foreign_owners(self):
        arguments = ["--ktest_logger=TEAMCITY", "--ktest_no_exit_code", plan.NATIVE_EXCLUSION]
        plan.validate_native_exclusion_owner("calf-webview", arguments)
        for module in ["calf-ui", "calf-share", True, None]:
            with self.subTest(module=module), self.assertRaises(ValueError):
                plan.validate_native_exclusion_owner(module, arguments)
        for values in [arguments + [plan.NATIVE_EXCLUSION], arguments + [arguments[0]], [True], tuple(arguments)]:
            with self.subTest(values=type(values).__name__), self.assertRaises(ValueError):
                plan.native_argument_view(values)

    def test_new_launcher_derivative_keeps_original_selection_parser_body_unchanged(self):
        name = "scripts/ci/ios_ui_application.py"
        current = history.ordinary_bytes(ROOT, name)
        old = history.source_before_cookie(name, current)
        def function(payload):
            return next(node for node in ast.parse(payload).body
                        if isinstance(node, ast.FunctionDef) and node.name == "application_test_focus")
        before, after = function(old), function(current)
        self.assertIsInstance(after.body[0], ast.Import)
        self.assertIsInstance(after.body[1], ast.Assign)
        self.assertEqual([ast.dump(node) for node in before.body], [ast.dump(node) for node in after.body[2:]])
        self.assertIn('cookie_scope.validate_native_exclusion_owner(host["module"], arguments)', current.decode())
        self.assertNotIn(b"cookie_scope", old)

    def test_new_future_xml_requires_exact_four_passed_no_duplicate_skip_or_malformed_success(self):
        cases = [{"classname": owner, "name": method + "[desktop]", "status": "passed"}
                 for owner, methods in plan.GROUPS for method in methods]
        self.assertTrue(plan.case_inventory(cases))
        self.assertFalse(plan.case_inventory(cases[:-1]))
        self.assertFalse(plan.case_inventory([cases[0]] * 4))
        self.assertFalse(plan.case_inventory([{**cases[0], "status": "skipped"}, *cases[1:]]))
        self.assertFalse(plan.case_inventory([{**cases[0], "name": []}, *cases[1:]]))
        self.assertFalse(plan.case_inventory([{**cases[0], "classname": plan.PARKED[0]}, *cases[1:]]))

    def test_new_duplicate_manifest_fields_and_unknown_guard_source_refuse(self):
        with self.assertRaises(ValueError):
            history._unique([("schema_version", 1), ("schema_version", 1)])
        import cookie_ci668_outer_source_projection as cookie_outer
        with tempfile.TemporaryDirectory(prefix="cookie-guard-model-") as directory:
            owned = Path(directory).resolve()
            for name in cookie_outer.fixture_inputs():
                target = owned / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            source = owned / history.SOURCE_RELATIVE
            source.write_bytes(source.read_bytes() + b"\n# unknown guard body\n")
            with self.assertRaisesRegex(ValueError, r"\AOld or unknown bytes cannot substitute for exact current Cookie outer source\Z"):
                history._document(owned)

    def test_new_file_reader_path_replacement_cannot_admit_stale_descriptor_bytes(self):
        with tempfile.TemporaryDirectory(prefix="cookie-replacement-model-") as directory:
            owned = Path(directory).resolve()
            source = owned / "source.py"
            source.write_bytes(b"dummy original model bytes\n")
            original_read = os.read
            replaced = False
            def read(fd, size):
                nonlocal replaced
                payload = original_read(fd, size)
                if not replaced:
                    replaced = True
                    source.rename(owned / "old-source.py")
                    source.write_bytes(b"dummy foreign model bytes\n")
                return payload
            with mock.patch.object(history.os, "read", side_effect=read), self.assertRaisesRegex(ValueError, "path ownership changed"):
                history.ordinary_bytes(owned, "source.py")
            self.assertEqual(b"dummy foreign model bytes\n", source.read_bytes())

    def test_new_source_descriptor_cleanup_retains_primary_and_attempts_every_owned_fd(self):
        with tempfile.TemporaryDirectory(prefix="cookie-close-model-") as directory:
            owned = Path(directory).resolve()
            source = owned / "source.py"
            source.write_bytes(b"dummy model source\n")
            os.link(source, owned / "hardlink.py")
            closed = []
            original_close = os.close
            def close(fd):
                original_close(fd)
                closed.append(fd)
                if len(closed) == 1:
                    raise OSError("dummy model close reporting failure after real close")
            with mock.patch.object(history.os, "close", side_effect=close), self.assertRaisesRegex(ValueError, "regular bounded") as caught:
                history.ordinary_bytes(owned, "source.py")
            self.assertEqual(2, len(closed))
            self.assertEqual(2, len(set(closed)))
            self.assertTrue(any("descriptor cleanup" in note for note in caught.exception.__notes__))


class CookieCopiedFixtureSuccessor609Tests(unittest.TestCase):
    """Genuinely NEW owning-fixture successor controls; not accepted681/609 replay."""

    def test_new_stale34_and_pair_fixture_envelopes_refuse_on_missing_outer_manifest(self):
        import cookie_ci668_outer_source_projection as cookie_outer
        current = cookie_outer.fixture_inputs()
        original = history.fixture_inputs()
        self.assertEqual(40, len(current))
        self.assertEqual(34, len(original))
        self.assertEqual({cookie_outer.CI_GUARD, cookie_outer.CI_SPEC, cookie_outer.CALLBACK_SPEC,
                          cookie_outer.SOURCE_RELATIVE, cookie_outer.SPEC_RELATIVE,
                          cookie_outer.NEW_CONTROL_RELATIVE}, current - original)
        for inputs, relative, tail, call in [
                (original, history.READER, b"\n# NEW unknown full-reader tail\n", history.validate_current_sources),
                ({history.SOURCE_RELATIVE, history.SPEC_RELATIVE}, history.SOURCE_RELATIVE,
                 b"\n# unknown guard body\n", history._document)]:
            with tempfile.TemporaryDirectory(prefix="cookie-stale-envelope609-") as directory:
                owned = Path(directory).resolve()
                for name in inputs:
                    target = owned / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / name, target)
                target = owned / relative
                target.write_bytes(target.read_bytes() + tail)
                self.assertFalse((owned / cookie_outer.SPEC_RELATIVE).exists())
                with self.assertRaises(FileNotFoundError) as caught:
                    call(owned)
                self.assertEqual(Path(cookie_outer.SPEC_RELATIVE).name, caught.exception.filename)

    def test_new_control_source_named_predecessor_roundtrip_never_admits_old_as_current(self):
        import cookie_ci668_outer_source_projection as cookie_outer
        current = cookie_outer.ordinary_bytes(ROOT, cookie_outer.OWNING_CONTROL_RELATIVE)
        document, _ = cookie_outer._document(ROOT)
        row = document["cookie681_control_binding"]
        old = cookie_outer.cookie681_control_for_old_cookie_comparison(cookie_outer.OWNING_CONTROL_RELATIVE, current, ROOT)
        self.assertEqual(cookie_outer.OWNING_CONTROL_BEFORE_SHA256, cookie_outer.sha(old))
        self.assertNotEqual(old, current)
        forward = old
        for fragment in row["fragments"]:
            self.assertEqual(1, forward.count(fragment["before"].encode()))
            forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
        self.assertEqual(current, forward)
        self.assertEqual(current, cookie_outer.source_before_cookie_outer(cookie_outer.OWNING_CONTROL_RELATIVE, current, ROOT))
        self.assertEqual(current, cookie_outer.peel_cookie_outer_for_history(cookie_outer.OWNING_CONTROL_RELATIVE, current, ROOT))
        self.assertEqual(current, cookie_outer.current_source_before_cookie_outer(cookie_outer.OWNING_CONTROL_RELATIVE, current, ROOT))
        with self.assertRaisesRegex(ValueError, r"\AOld or unknown bytes cannot substitute for exact current Cookie outer source\Z"):
            cookie_outer.current_source_before_cookie_outer(cookie_outer.OWNING_CONTROL_RELATIVE, old, ROOT)
        with self.assertRaisesRegex(ValueError, r"\AOnly exact current Cookie681 owning control can serve its predecessor comparison\Z"):
            cookie_outer.cookie681_control_for_old_cookie_comparison(cookie_outer.OWNING_CONTROL_RELATIVE, old, ROOT)
        init = cookie_outer.ordinary_bytes(ROOT, cookie_outer.INIT)
        self.assertEqual(init, cookie_outer.cookie681_control_for_old_cookie_comparison(cookie_outer.INIT, init, ROOT))
        self.assertEqual(init, cookie_outer.peel_cookie_outer_for_history(cookie_outer.INIT, init, ROOT))

    def test_new_raw40_and_cookie_current_hashes_bind_entire_successor_control_source(self):
        import cookie_ci668_outer_source_projection as cookie_outer
        raw = cookie_outer.current_input_hashes(ROOT)
        cookie = history.validate_current_sources(ROOT)
        current = cookie_outer.ordinary_bytes(ROOT, cookie_outer.OWNING_CONTROL_RELATIVE)
        actual = cookie_outer.sha(current)
        self.assertEqual(40, len(raw))
        self.assertEqual(34, len(cookie))
        self.assertEqual(actual, raw[cookie_outer.OWNING_CONTROL_RELATIVE])
        self.assertEqual(actual, cookie[cookie_outer.OWNING_CONTROL_RELATIVE])
        self.assertNotEqual(cookie_outer.OWNING_CONTROL_BEFORE_SHA256, actual)
        self.assertEqual(cookie_outer.INIT_CURRENT_SHA256, raw[cookie_outer.INIT])
        self.assertEqual(cookie_outer.INIT_CURRENT_SHA256, cookie[cookie_outer.INIT])
        with tempfile.TemporaryDirectory(prefix="cookie-current-control609-") as directory:
            owned = Path(directory).resolve()
            for name in cookie_outer.fixture_inputs():
                target = owned / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            target = owned / cookie_outer.OWNING_CONTROL_RELATIVE
            target.write_bytes(target.read_bytes() + b"\n# unknown successor control body\n")
            message = "Exact current Cookie outer input changed: " + cookie_outer.OWNING_CONTROL_RELATIVE
            with self.assertRaises(ValueError) as caught:
                history.validate_current_sources(owned)
            self.assertEqual(message, str(caught.exception))
            with self.assertRaises(ValueError) as caught:
                cookie_outer.cookie681_control_for_old_cookie_comparison(cookie_outer.OWNING_CONTROL_RELATIVE, current, owned)
            self.assertEqual(message, str(caught.exception))
