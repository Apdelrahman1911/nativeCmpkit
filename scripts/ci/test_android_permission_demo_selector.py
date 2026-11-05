# SPDX-License-Identifier: Apache-2.0
"""Owning permission annotation source guards only; no module import/build/device/native work."""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch
from test_android_permission_demo_denial_absence import permission_absence_preimage
from android_permission_selected_context import permission_lifecycle_context, permission_spec_extension

TREE = Path(os.environ.get("PERMISSION_SELECTOR_REVIEW_TREE", Path(__file__).resolve().parents[2])).resolve()
PROFILE = "android-permission-demo-call-denial-recovery"
CORE = "calf-permissions/core"
CLASS = "com.mohamedrejeb.calf.permissions.AndroidPermissionDemoDeviceTest"
SOURCE = CORE + "/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionDemoDeviceTest.kt"
ANNOTATION = "com.mohamedrejeb.calf.permissions.AndroidPermissionDemoCallDenialVerification"
NAME = ANNOTATION.rsplit(".", 1)[1]
METHODS = ("callOnFreshApprovedVariantUsesPublicRequestAndActualSystemGrant",
           "denialThenPermanentDenialKeepsActualRationaleAndOneResultPerRequest")
PICKER = "pickersReadRealDocumentsAndImagesWithoutAllFilesOrSmsPermissions"
DECLARATION = "@Target(AnnotationTarget.FUNCTION)\n@Retention(AnnotationRetention.RUNTIME)\nannotation class " + NAME + "\n\n"
MARKER = "    @" + NAME + "\n"
ORIGINAL_NATIVE_SOURCE_SHA256 = "06ab71c08cb881d17af0228f8a50c7df543ed22cf56682ccf2ac0a58e7507f07"


def source(relative):
    return (TREE / relative).read_text(encoding="utf-8")


def function(tree, name):
    matches = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1:
        raise AssertionError("Exactly the named owning function is required")
    return matches[0]


def permission_branch(tree, name):
    matches = [n for n in ast.walk(function(tree, name)) if isinstance(n, ast.If) and any(
        isinstance(v, ast.Name) and v.id == "ANDROID_PERMISSION_DEVICE_SPECS" for v in ast.walk(n.test))]
    if len(matches) != 1:
        raise AssertionError("Exactly the existing permission branch is required")
    return matches[0]


def compile_nodes(nodes, env):
    node = ast.fix_missing_locations(ast.Module(body=deepcopy(nodes), type_ignores=[]))
    exec(compile(node, "selected-pure-owning-permission-source", "exec"), env)


def owning_environment():
    tree = ast.parse(source("scripts/ci/library_tests.py"))
    names = {"ANDROID_PERMISSION_DEMO_FOCUS", "ANDROID_PERMISSION_DEMO_RECOVERY_FOCUS",
             "ANDROID_PERMISSION_DEMO_DENIAL_RECOVERY_FOCUS",
             "ANDROID_PERMISSION_DEMO_RECOVERY_ANNOTATION", "ANDROID_MEDIA_SELECTION_FOCUS",
             "ANDROID_PERMISSION_DEVICE_SPECS", "ANDROID_SAVE_IDENTITY_FOCUS",
             "ANDROID_SAVE_IDENTITY_RECOVERY_FOCUS", "ANDROID_SAVE_IDENTITY_FOCUSES",
             "ANDROID_GEO_PREREQUISITES_FOCUS", "ANDROID_WEBVIEW_REQUEST_FOCUS"}
    nodes = [n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in names for t in n.targets)]
    functions = ("android_permission_device_filter", "android_permission_device_identities",
                 "validate_android_permission_demo_recovery_annotation")
    nodes += [permission_spec_extension(tree)]
    nodes += [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in functions]
    env = {"Path": Path, "re": re, "safe_path": lambda root, relative: root / relative,
           "content_policy": types.SimpleNamespace(ANDROID_FOCUS="webview-content-policy-android"),
           "permission_lifecycle": permission_lifecycle_context(source)}
    compile_nodes(nodes, env)
    selected = ast.parse("def selected_source(root, focus, selected, result):\n    pass\n").body[0]
    selected.body = deepcopy(permission_branch(tree, "plan").body) + ast.parse("return result, selected\n").body
    compile_nodes([selected], env)
    validate = ast.parse("def validated_plan(test_plan):\n    focus = test_plan['explicit_test_focus']\n    expected = test_plan['expected']\n").body[0]
    validate.body += deepcopy(permission_branch(tree, "validate_test_focus").body)
    env["allowed_test_focus"] = lambda suite, modules, focus: suite == "android-device" and modules == (CORE,) and focus == PROFILE
    compile_nodes([validate], env)
    command = function(tree, "gradle_command")
    arguments = [n for n in ast.walk(command) if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "argument" for t in n.targets) and "ANDROID_SAVE_IDENTITY_FOCUSES" in ast.unparse(n)]
    appends = [n for n in ast.walk(command) if isinstance(n, ast.Expr) and "android.testInstrumentationRunnerArguments." in ast.unparse(n)
               and "+ argument +" in ast.unparse(n)]
    if len(arguments) != 1 or len(appends) != 1:
        raise AssertionError("The existing exact selector-property emission is required")
    emit = ast.parse("def selector_property(focus, item):\n    test_plan = {'explicit_test_focus': focus}\n    command = []\n").body[0]
    emit.body += deepcopy(arguments + appends) + ast.parse("return command\n").body
    compile_nodes([emit], env)
    return tree, env


def annotation_projection(native):
    if native.count(DECLARATION) != 1 or native.count(MARKER) != 2 or native.count(NAME) != 3:
        raise ValueError("Only the exact declaration and two selector lines may be removed")
    return native.replace(DECLARATION, "", 1).replace(MARKER, "")


class AndroidPermissionDemoSelectorGuards(unittest.TestCase):
    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("Source guards may not execute external processes")
        for method in ("run", "Popen"):
            control = patch.object(subprocess, method, forbidden)
            control.start(); self.addCleanup(control.stop)
        self.native = source(SOURCE)

    def plan(self):
        tree, env = owning_environment()
        result, expected = env["selected_source"](TREE, PROFILE, [{"test_source_files": [SOURCE]}], {})
        expected[0].update(module=CORE, project=":calf-permissions:calf-permissions-core",
                           task=":calf-permissions:calf-permissions-core:connectedAndroidDeviceTest",
                           report_directory=CORE + "/build/outputs/androidTest-results/connected/androidMain")
        return env, {"suite": "android-device", "explicit_test_focus": result["explicit_test_focus"],
            "explicit_module_subset": [CORE], "complete_suite_requested": False, "expected": expected}

    def validate_source(self, native, *, foreign=None):
        _, env = owning_environment()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / SOURCE; path.parent.mkdir(parents=True); path.write_text(native)
            sources = [SOURCE]
            if foreign:
                relative, text = foreign
                path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
                sources.append(relative)
            return env["validate_android_permission_demo_recovery_annotation"](root, sources)

    def test_recovery_route_is_one_lossless_annotation_with_original_two_identities(self):
        _, env = owning_environment()
        # Owning baseline red is the actual comma selector, not missing test wiring.
        self.assertEqual(ANNOTATION, env["android_permission_device_filter"](PROFILE))
        env, plan = self.plan()
        expected, = plan["expected"]
        self.assertEqual("annotation", expected["test_filter_argument"])
        self.assertEqual([{"classname": CLASS, "name": m} for m in METHODS], expected["required_testcases"])
        argv = env["selector_property"](PROFILE, expected)
        self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.annotation=" + ANNOTATION], argv)
        self.assertNotIn(",", expected["test_filter"])
        self.assertNotIn(PICKER, expected["test_filter"])

    def test_inline_selector_is_top_level_function_runtime_and_only_two_method_uses(self):
        self.validate_source(self.native)
        self.assertEqual(1, self.native.count(DECLARATION))
        self.assertEqual(3, self.native.count(NAME))
        self.assertNotRegex(self.native[:self.native.index(DECLARATION)], r"[{}]")
        selected = re.findall(r"@" + NAME + r"\s+@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", self.native)
        self.assertEqual(list(METHODS), selected)
        self.assertNotRegex(self.native, r"@" + NAME + r"\s+(?:@RunWith[^\n]*\s+)?class\b")

    def test_recovery_plan_refuses_class_missing_wrong_or_exclusion_selector_fields(self):
        env, plan = self.plan()
        self.assertTrue(env["validated_plan"](plan))
        mutations = (
            lambda p: p['expected'][0].pop('test_filter_argument'),
            lambda p: p['expected'][0].update(test_filter_argument='class'),
            lambda p: p['expected'][0].update(test_filter_argument='notAnnotation'),
            lambda p: p['expected'][0].update(test_filter=CLASS),
            lambda p: p['expected'][0].update(test_filter=','.join(CLASS+'#'+m for m in METHODS)),
            lambda p: p['expected'][0].update(test_filter=ANNOTATION+'Foreign'),
            lambda p: p['expected'][0].update(test_exclusion_annotation=ANNOTATION),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(selector_mutation=index):
                changed = deepcopy(plan); mutate(changed)
                with self.assertRaises(ValueError): env['validated_plan'](changed)

    def test_missing_duplicate_moved_nested_wrong_retention_or_target_annotations_refuse(self):
        variants = (
            self.native.replace(MARKER, '', 1),
            self.native.replace(MARKER, ''),
            self.native.replace(MARKER, MARKER+MARKER, 1),
            self.native.replace(MARKER+'    @Test', '    @Test\n'+MARKER.strip(), 1),
            self.native.replace(MARKER, '    @'+ANNOTATION+'\n', 1),
            self.native.replace(DECLARATION, DECLARATION+DECLARATION, 1),
            self.native.replace(DECLARATION, 'class ForeignContainer {\n'+DECLARATION+'}\n\n', 1),
            self.native.replace('AnnotationRetention.RUNTIME', 'AnnotationRetention.BINARY', 1),
            self.native.replace('AnnotationRetention.RUNTIME', 'AnnotationRetention.SOURCE', 1),
            self.native.replace('AnnotationTarget.FUNCTION', 'AnnotationTarget.CLASS', 1),
            self.native.replace('AnnotationTarget.FUNCTION', 'AnnotationTarget.FUNCTION, AnnotationTarget.CLASS', 1),
        )
        for index, native in enumerate(variants):
            with self.subTest(declaration_mutation=index), self.assertRaises(ValueError):
                self.validate_source(native)

    def test_picker_class_helper_alias_and_foreign_common_or_device_uses_refuse(self):
        for index, native in enumerate((
            self.native.replace('    @Test fun '+PICKER, MARKER+'    @Test fun '+PICKER, 1),
            self.native.replace('@RunWith(AndroidJUnit4::class)', '@'+NAME+'\n@RunWith(AndroidJUnit4::class)', 1),
            self.native+'\n@'+NAME+'\nfun unreviewedHelper() {}\n',
            self.native.replace('import org.junit.Test', 'import '+ANNOTATION+' as Other\nimport org.junit.Test', 1),
        )):
            with self.subTest(broadened_source=index), self.assertRaises(ValueError): self.validate_source(native)
        for source_set in ('commonTest', 'androidDeviceTest'):
            relative = CORE+'/src/'+source_set+'/kotlin/ForeignSelector.kt'
            for text in ('@'+NAME+' @Test fun foreign() {}\n',
                         'import '+ANNOTATION+' as Other\n@Other @Test fun foreign() {}\n'):
                with self.subTest(foreign_source_set=source_set), self.assertRaises(ValueError):
                    self.validate_source(self.native, foreign=(relative, text))

    def test_removing_only_selection_metadata_restores_every_original_source_byte(self):
        # Exact approved absence inverse precedes the unchanged old annotation-only hash.
        prior = permission_absence_preimage(self.native, "AndroidPermissionDemoDeviceTest.kt")
        original = annotation_projection(prior)
        self.assertEqual(ORIGINAL_NATIVE_SOURCE_SHA256, hashlib.sha256(original.encode()).hexdigest())
        self.assertEqual(list(METHODS)+( [PICKER]), re.findall(r'@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)', original))
        changed = self.native.replace('assertFalse(initial.getBoolean(Manifest.permission.CALL_PHONE))',
                                     'assertTrue(initial.getBoolean(Manifest.permission.CALL_PHONE))', 1)
        self.assertNotEqual(self.native, changed)
        with self.assertRaises(AssertionError):
            permission_absence_preimage(changed, "AndroidPermissionDemoDeviceTest.kt")
        prior_changed = prior.replace('assertFalse(initial.getBoolean(Manifest.permission.CALL_PHONE))',
                                      'assertTrue(initial.getBoolean(Manifest.permission.CALL_PHONE))', 1)
        self.assertNotEqual(ORIGINAL_NATIVE_SOURCE_SHA256, hashlib.sha256(annotation_projection(prior_changed).encode()).hexdigest())

    def test_new_annotation_does_not_change_final_full_class_three_method_or_media_selection(self):
        _, env = owning_environment()
        full = env['ANDROID_PERMISSION_DEMO_FOCUS']; media = env['ANDROID_MEDIA_SELECTION_FOCUS']
        self.assertEqual(CLASS, env['android_permission_device_filter'](full))
        self.assertEqual(env['ANDROID_PERMISSION_DEVICE_SPECS'][media]['classname'], env['android_permission_device_filter'](media))
        self.assertEqual(METHODS+(PICKER,), env['ANDROID_PERMISSION_DEVICE_SPECS'][full]['methods'])
        self.assertEqual(METHODS+(PICKER,), env['ANDROID_PERMISSION_DEVICE_SPECS'][PROFILE]['declared_methods'])
        self.assertRegex(self.native, r'(?m)^class AndroidPermissionDemoDeviceTest\s*\{')
        self.assertNotRegex(self.native, r'(?m)^\s*(?:open|abstract) class AndroidPermissionDemoDeviceTest\b')
        self.assertEqual(list(METHODS)+[PICKER], re.findall(r'@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)', self.native))
        full_argv = env['selector_property'](full, {'test_filter':CLASS})
        self.assertEqual(['-Pandroid.testInstrumentationRunnerArguments.class='+CLASS], full_argv)

    def test_new_selector_retains_exact_xml_nonzero_and_live_comma_refusal_contracts(self):
        tree, env = owning_environment()
        body = ast.Module(body=permission_branch(tree, 'collect_reports').body, type_ignores=[])
        text = ast.unparse(body)
        self.assertIn("len(reports) == 1 and actual == required", text)
        self.assertIn("len(module_cases) == len(required)", text)
        self.assertIn("expected['required_testcases']", text)
        self.assertIn('Native permission XML must contain exactly every new selected method in one fresh report', text)
        collector = ast.unparse(function(tree, 'collect_reports'))
        self.assertIn("not reports or not counts['executed']", collector)
        self.assertIn("counts['failures'] or counts['errors'] or counts['unexpected_skipped']", collector)
        fresh = source('scripts/ci/fresh-tests.init.gradle.kts')
        self.assertIn("check(requestedSelectors.values.none { ',' in it })", fresh)
        self.assertIn('ATE1.0.1 cannot transport comma-containing selection values losslessly', fresh)
        self.assertIn('runnerArguments.filterKeys { it in selectorKeys } == requestedSelectors', fresh)
        self.assertNotIn(NAME, fresh)
        self.assertEqual([{'classname':CLASS, 'name':m} for m in METHODS], env['android_permission_device_identities'](PROFILE))


if __name__ == '__main__':
    unittest.main()
