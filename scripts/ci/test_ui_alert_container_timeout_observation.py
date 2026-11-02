"""Six NEW source controls; source-only and UNEXECUTED until lead qualification.

Normal scripts/ci unittest discovery; stdlib only, no private environment or
candidate/historical test-module import. These checks extract only inert guard
function definitions from source and execute them against byte fixtures when
the lead runs this NEW class. No accepted 19 methods are compiled or invoked.
No UIKit/Objective-C/visibility/window/input/runtime acceptance is modeled.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

if __package__:
    from .terminal_awt240_source_projection import source_before_terminal_awt240, text_before_terminal_awt240
else:
    from terminal_awt240_source_projection import source_before_terminal_awt240, text_before_terminal_awt240

ROOT = Path(__file__).resolve().parents[2]
NATIVE = 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativeAlertImportantRegressionTest.kt'
HISTORICAL = 'scripts/ci/test_ui_alert_important_recovery.py'
ACCEPTED_METHODS = {'test_original_four_bodies_gate_public_activation_deadline_host_and_parser_are_byte_retained': {'raw_sha256': 'd78aa60c68c0acc0d2adb7b91b5e4dd082bcd0fdbbc8a35af84fe7d8b638d2fa', 'portable_ast_sha256': '4a05996f85afe46d0abe4770665edb06a69b997d823411d42245794e80df1b70', 'local_ast_dump_sha256': '4b301bfce6588ad7e50a458196c6f83594b02c44e56cabc9cacf91a3e30c4bb8'}, 'test_gate_success_has_no_diagnostic_and_public_activation_once': {'raw_sha256': 'a3bf627885766768ff3088b6b2441bb756c1a138ea7e4421fb674c9be94c9605', 'portable_ast_sha256': 'b17a13612a28679ec02a902a6288af377c4ca1aa7f5e5669e2993525922ed306', 'local_ast_dump_sha256': '30e3e75a83611b71b77e9fa317076cc3bde502c09a49b9c8b860fd26aa38fb36'}, 'test_only_exact_owning_timeout_observes_once_on_model_main_without_activation': {'raw_sha256': '06befa7700445db8b4f98f61cdcf66d255c5202ef0bd4306536cb836caa7c28a', 'portable_ast_sha256': 'e68dc558b0b1676be5b98fff049884abb520c396925116486ebbd3a9ff8beecd', 'local_ast_dump_sha256': 'c1a976cc94f24fafd04e11d08de9b7c3fe3259ce01e1f5e73fc8aa8c77f9d9a0'}, 'test_other_failure_types_none_and_nonowning_prefixes_never_emit': {'raw_sha256': '844722bea686d2a20ce8992bc519ed252bab0978d49ba4947228d4a4b69939ad', 'portable_ast_sha256': '72b997225993b55bcd0451c98038dd2676ad7cac18388d198badba75f78b5a0a', 'local_ast_dump_sha256': '49aa5962a1d58242f3d8131ff199c777ff8d3964df2f1eb7b337f8c3b9f0ccb5'}, 'test_capture_failure_falls_back_without_content_and_keeps_primary_suppression': {'raw_sha256': 'bd8b1f472d71ac9bab44c44c84d0b7a218e26befe8b404dac1d39ae3a907a503', 'portable_ast_sha256': '7e31113648cdf07b12de9581f23cf0bbcd3172235ed0c0a6a66344710c99e41d', 'local_ast_dump_sha256': 'b012a3221adec1613c82607ca2cf18259266f3235b9ddd83fb731654fbb918f0'}, 'test_throwing_emitters_suppression_or_unexpected_observer_cannot_replace_primary': {'raw_sha256': 'fbb91bad317ee32f324b1e77a84a9fd5729651fcdc4c8d2fe1dbffccc02e7feb', 'portable_ast_sha256': 'cdb1d03268eb332184467004c4fad2bc3721439b5f297a92ade4fb746dc4aad6', 'local_ast_dump_sha256': '546391502e26902ee6bfb4a05e2f6f77741657cbe14e2387c2f9e62429447396'}, 'test_fixed_source_formatter_exports_only_numeric_boolean_allowlisted_fields': {'raw_sha256': '37b51be0c21c1b03230a449b8e0c9a402f82339dd4a97c702c6d991e703c8315', 'portable_ast_sha256': '822ed38f5c1a71bfc58dc9151094e047953b118c708ad4d53a38d99d86023ed7', 'local_ast_dump_sha256': '83ec1f2e1b1672aff7f041a402598be95c17c9336d43ea8a073e6b4847ed45cf'}, 'test_bounded_sample_leaf_branch_exact_cap_and_wide_deep_cyclic_invalid_children': {'raw_sha256': '58acf78e6ae19528c5d000e7e4e179d473953751908bb2f965ffd573c9dfa1b4', 'portable_ast_sha256': 'be97a02f881cffe6bf86d7625cac7b087e2977b2f74389763ffbc39d1f405457', 'local_ast_dump_sha256': '73a270eb69d8d04674b9647f4416d254be1170a32c71211c0a66ee45f96a45aa'}, 'test_complete_synthetic_snapshot_keeps_exact_label_trait_visibility_attachment_chain': {'raw_sha256': '7a5bbd8ffd19c46b8bc1c7343c34590cc56f42557b4b0286b50192e61ac9fb3f', 'portable_ast_sha256': '2fee0395d11e2d74972c02812fa33835f104cda6b179c280941b1a96bd240674', 'local_ast_dump_sha256': '5994de88fe36449e349623e2332a0d42358d82df7bae8fd89814fd52a7b003c5'}, 'test_ordinary_diagnostic_advances_only_stream_bytes_not_native_cases_lifecycle_or_failures': {'raw_sha256': 'b973b3d281476205d8d4e27f3fa77bfd79a306c38c42f96cd3ec76032e765082', 'portable_ast_sha256': '67d97ec58e06c35011509d2e60e9cea65547c294e210ff3b72e2da706cb2faee', 'local_ast_dump_sha256': 'a352b67f45fb331096cafff65530aa0d417ae9ae596058068b95c0309ad329e9'}, 'test_exact_four_plan_gradle_filters_and_native_focus_exclude_date_material_and_old_methods': {'raw_sha256': 'b87569fd6da65f9cbe64dda0d6990c6cf4b9b1a3c64ba6d07f98011424d3d2e2', 'portable_ast_sha256': '70d12fe8d2212458848568e81cfe13b36d650da210bc0331bb191508b15c260a', 'local_ast_dump_sha256': 'ffa00ebd940a426a4f2c8332fa8e926e9f0382fdfad7b2dce7f5fb3d54038d50'}, 'test_missing_duplicate_arbitrary_wildcard_extra_date_or_second_filter_are_refused': {'raw_sha256': '8280533440122c9d105cea47e2bd7d6bf679c27ca4fc00c2076942d2a157cfdb', 'portable_ast_sha256': '0b4302380627542025a4ba3fb0b0ef7e6626766790e7ba91fa6ed51ab3ce79f6', 'local_ast_dump_sha256': '371905baaee359b71c695ee06f5db1d15d671140a1f99710ad948ab2b65080a1'}, 'test_wrong_suite_module_task_host_report_project_scope_or_inventory_never_accepts': {'raw_sha256': '80023f5ce683c387c90a12876c3e38ed86bc6312593d85229394337a0f1f047b', 'portable_ast_sha256': '35268bf03a74f11e4e89aad635c53b593f95deb528907e2dc7b73535bfb23b49', 'local_ast_dump_sha256': '985d54fdb09454d2ba4a47cee7e5dc3407fee9dfc7345e5b39013feea79b9319'}, 'test_disabled_removed_extra_native_declarations_and_missing_application_host_refuse': {'raw_sha256': '253d25c06816304a7b318929a49765e4f730ec143616aefb1df08739118db6fc', 'portable_ast_sha256': '0eff7d070d997a711d90b7e181390ade3c8fc01516872296f4fc58b616cb640f', 'local_ast_dump_sha256': 'd6da0dd07659e2753fa25f03534eb8fbadd065db0fe278e3a3bb4854c6ea494e'}, 'test_single_canonical_profile_refuses_runner_arch_python_kind_extra_fields_and_keeps_full_slots': {'raw_sha256': '8c7df5bd3e161035e8b014bd4dd7fab661d3f56c503607989cfb3baf3fbe4744', 'portable_ast_sha256': '4fda638fb7e0b3a879d50473933ddd35b4bd169bcf213ed4442a78fb29507223', 'local_ast_dump_sha256': '3d8b196772d12e557bda74428ee2d98c117dc8316271453ea99a4faab6b579d9'}, 'test_mocked_source_only_preflight_is_one_new_cli_not_material_or_second_application': {'raw_sha256': '4b638933ac5349984035fd4302b3e778ac6dfb0d9c34f4e4e2b4a7b58bfcc878', 'portable_ast_sha256': '9c0437674ef1b4ca1425f42fba95768605ab8ea3d36a3c4894859b774bfd543d', 'local_ast_dump_sha256': 'e72619379bedf6c75ac831b1e1f658a836ce2f62b2543c95948effc70a26318a'}, 'test_only_fresh_exact_four_xml_identities_and_owned_alert_sources_are_qualified_synthetically': {'raw_sha256': 'd2df250bc385a6149651d3bf1ab9934ef4f785414d1b6f5313c8ccde1bd486eb', 'portable_ast_sha256': '3b1b78deef5dacc1b9fed5373c1882fb62d4ff83be6d0b504c58a6f0cc56557c', 'local_ast_dump_sha256': 'd1bfdfb69b4d049fab1a95aa8e2236758782e650d23973efdf59c62b97b561e8'}, 'test_missing_duplicate_foreign_date_material_failed_skipped_stale_future_or_zero_xml_refuse': {'raw_sha256': '07e7ea1c88c7ca6919be3bb48720a75801b257433c82e156bfd220520ca3a80d', 'portable_ast_sha256': '908f049122ff2105ab3d69db95cafc0f33fa1702b7639862ac891d791cdde627', 'local_ast_dump_sha256': '51b3709875cd2c426ba26e52c686cb6d31fa86074a847812736da7f2a9752504'}, 'test_exact_owning_source_mutations_are_refused_before_any_synthetic_behavior_claim': {'raw_sha256': '87175e024732153c37e5ee666fc6bc746511242901484a40533adb7aa3c90e05', 'portable_ast_sha256': '964919cb6ea1e70db3d3616dc37d89ab8b5ee642f2afafa3e52b5d56dcc5e927', 'local_ast_dump_sha256': 'cf940f1ac5169615a4f48d266acb929f38e8b65f9be344a547c79694e739556b'}}
RETAINED_ASSIGNMENTS = {'EXPECTED_SOURCE_SHA256': {'raw_sha256': '85cdcbcd60738f8bbe24c996975be4cdf27910c4a18cb3394647845b44fcc160', 'portable_ast_sha256': '558b7a2a6cbf2d04cb93f618aca9287e062fca2b37c11db2ccc33f98fe4bc5a9'}, 'SHARE_ALERT153_REBASE': {'raw_sha256': '15fe1b466702a178e74cea6540a1af90a6c4da54211ba26b280fe9bc32260612', 'portable_ast_sha256': '93e71f92f942e204e7013ac1a5bf10b39131cd9cae8ec0d61774256e8cdfdd64'}, 'SHARE_ALERT153_OPTIONAL_WASM_PIN': {'raw_sha256': 'f70f4eeb4519d50e68b3de04de610bdbbe2ac81ba52519ab5df6bc74f0765428', 'portable_ast_sha256': 'd24c21bf7aadb2c7e436f81a21970d63ff55fb701c8005343dccb1976a2e661b'}}
RETAINED_FUNCTIONS = {'source_before_share_alert153_rebase': '49f9aa2e9363b648a1cda7aebf6eb465915d2287bbf338f836e40a1db38809fc', 'native_sections': '0cc721fb0ccb42ed26621d9a93afe096e60b8067060f42a75593834c96bf4d22'}
OBSERVATION_DECLARATION = {'raw_sha256': 'f76b9d046ece0cf230b6071d0efff47033a7a64e036b28185340523c9a55ff57', 'portable_ast_sha256': 'fb30469864a3887013b5ac9fa7654cf222a5a9c753819dbb41eec6f8733e5aaf'}
INERT_FUNCTION_PINS = {'digest': {'raw_sha256': '50b76bfffc27cbd7a792c95d031f6fd8e49777b6241b96ed8c4c4773edc356cb', 'portable_ast_sha256': '79110ef6e0fb50133ecb2621c78703d67de17ef6fc108445b38236c3d010f11b'}, 'source_before_alert_container153_observation': {'raw_sha256': '0caacf26af1c4eb4ea617cadba42ebd6a8bc001290716a001f45007f258b82fd', 'portable_ast_sha256': '0a09fdd11c70079e7e5385fd3dc2e7915d104cd4e5e8e5eb6a067cef507939c5'}, 'source_before_share_alert153_rebase': {'raw_sha256': 'c75e77220a26cb77b7686b73dec952adb27dd7e7ad7c97b71454dbf772cccb9e', 'portable_ast_sha256': '2a5ba9afa7dd4455680f88f863d786d3ff98e78a8c347918c9ed3f59c4ad8860'}}
# CI224: qualify only the existing outer Share188 byte guard, not its test class.
# Retained alert/Share153/Wasm declarations and their function pins stay exact.
SHARE188_OUTER_GUARD_PINS = {
    "SHARE188_FAILED_ONLY_REBASE": {
        "raw_sha256": "f72f72aa2789193756e18abaf50768506e31a577cbf7fd138623f0875a7fba0d",
        "portable_ast_sha256": "a0b435e719d67f748b0c3c058be17e7eec27da8eb3091f37113f200a566b95e7",
    },
    "source_before_share188_failed_only_rebase": {
        "raw_sha256": "e3e3150b9d846edba81de820ba4a2d7464b736c94f7ac6c3d4913ae27bb8840a",
        "portable_ast_sha256": "8a5f5fce3f33dbad87fab2e71f97d4a4d8aaf75f2e5726141e3616b097ef8471",
    },
}
PREFIX = "NATIVECMPKIT_ALERT_ACTION_CONTAINER_TIMEOUT"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def portable_ast(value):
    if isinstance(value, ast.AST):
        return {"node": type(value).__name__, "fields": {
            key: portable_ast(item) for key, item in ast.iter_fields(value)
            if key != "type_params" or item}}
    if isinstance(value, list):
        return [portable_ast(item) for item in value]
    return value


def ast_digest(node):
    return digest(json.dumps(portable_ast(node), sort_keys=True, separators=(",", ":")).encode())


def raw_node(source, node):
    start = min([node.lineno] + [item.lineno for item in getattr(node, "decorator_list", [])])
    return "".join(source.splitlines(keepends=True)[start - 1:node.end_lineno]).encode()


def compose_share188_outer_guard(source, parsed, namespace):
    """Apply the qualified current outer inverse before the intact old chain.

    Only one literal and one inert byte-guard function are admitted. Historical
    test classes, imports and top-level statements are never compiled here.
    """
    declaration_name = "SHARE188_FAILED_ONLY_REBASE"
    function_name = "source_before_share188_failed_only_rebase"
    selected = {}
    for name in (declaration_name, function_name):
        matches = [node for node in parsed.body if
                   (isinstance(node, ast.Assign) and len(node.targets) == 1 and
                    isinstance(node.targets[0], ast.Name) and node.targets[0].id == name) or
                   (isinstance(node, ast.FunctionDef) and node.name == name)]
        if len(matches) != 1:
            raise ValueError("An exact unique outer Share188 guard symbol is required")
        node = matches[0]
        expected = SHARE188_OUTER_GUARD_PINS[name]
        if (digest(raw_node(source, node)) != expected["raw_sha256"] or
                ast_digest(node) != expected["portable_ast_sha256"]):
            raise ValueError("The exact outer Share188 byte guard changed before execution")
        selected[name] = node
    namespace[declaration_name] = ast.literal_eval(selected[declaration_name].value)
    exec(compile(ast.Module(body=[selected[function_name]], type_ignores=[]),
                 str(ROOT / HISTORICAL), "exec"), namespace)
    outer = namespace[function_name]
    historical = namespace["source_before_share_alert153_rebase"]

    def combined(relative, current):
        return historical(relative, outer(relative, source_before_terminal_awt240(relative, current)))

    namespace["source_before_share_alert153_rebase"] = combined


def authored_guard_namespace(source):
    source = text_before_terminal_awt240(HISTORICAL, source)
    parsed = ast.parse(source)
    names = {"EXPECTED_SOURCE_SHA256", "ALERT_CONTAINER153_OBSERVATION", "SHARE_ALERT153_REBASE",
             "SHARE_ALERT153_OPTIONAL_WASM_PIN"}
    assignments = {node.targets[0].id: node for node in parsed.body
                   if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
    for name, expected in {**RETAINED_ASSIGNMENTS, "ALERT_CONTAINER153_OBSERVATION": OBSERVATION_DECLARATION}.items():
        node = assignments[name]
        if (digest(raw_node(source, node)) != expected["raw_sha256"] or
                ast_digest(node) != expected["portable_ast_sha256"]):
            raise ValueError("Exact authored guard declarations changed before any extracted function execution")
    namespace = {name: ast.literal_eval(assignments[name].value) for name in names}
    namespace["hashlib"] = hashlib
    function_names = {"digest", "source_before_alert_container153_observation", "source_before_share_alert153_rebase"}
    functions = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in function_names]
    if {node.name for node in functions} != function_names:
        raise ValueError("Only the three exact inert byte-guard definitions may be compiled")
    for node in functions:
        expected = INERT_FUNCTION_PINS[node.name]
        if (digest(raw_node(source, node)) != expected["raw_sha256"] or
                ast_digest(node) != expected["portable_ast_sha256"]):
            raise ValueError("Exact inert guard function source changed before compilation or invocation")
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(ROOT / HISTORICAL), "exec"), namespace)
    compose_share188_outer_guard(source, parsed, namespace)
    return parsed, assignments, namespace


class AlertContainerTimeoutNewSourceControls(unittest.TestCase):
    def setUp(self):
        self.historical = text_before_terminal_awt240(
            HISTORICAL, (ROOT / HISTORICAL).read_text()
        )
        self.parsed, self.assignments, self.namespace = authored_guard_namespace(self.historical)
        self.binding = self.namespace["ALERT_CONTAINER153_OBSERVATION"]
        self.native = (ROOT / NATIVE).read_bytes()
        self.assertEqual(digest(self.native), self.binding["after_sha256"])
        self.original = self.namespace["source_before_alert_container153_observation"](NATIVE, self.native)
        self.observer = self.binding["fragments"][1]["after"].removeprefix(self.binding["fragments"][1]["before"])

    def test_exact_native_inverse_retains_all_four_bodies_both_input_predicates_primary_and_deadline(self):
        self.assertEqual(self.binding["before_sha256"], self.namespace["EXPECTED_SOURCE_SHA256"][NATIVE])
        self.assertEqual(digest(self.original), self.binding["before_sha256"])
        marker = b"/**\n * Failure-only bounded observation, never input delivery or a gate repair."
        self.assertEqual(self.original.split(marker, 1)[0], self.native.split(marker, 1)[0])
        self.assertEqual(4, self.original.count(b"@Test fun "))
        self.assertEqual(2, self.original.count(b"it.accessibilityLabel == title && (it.accessibilityTraits and UIAccessibilityTraitButton) != 0UL &&"))
        self.assertEqual(1, self.original.count(b"eligible.single().accessibilityActivate()"))
        self.assertEqual(1, self.native.count(b"recordImportantAlertContainerTimeoutObservation(alert, title, window, sample)"))
        host = ROOT / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"
        self.assertEqual(digest(host.read_bytes()), self.namespace["EXPECTED_SOURCE_SHA256"][host.relative_to(ROOT).as_posix()])
        self.assertIn("val deadline = NSProcessInfo.processInfo.systemUptime + 10.0", host.read_text())

    def test_all_19_accepted_methods_and_existing_share_wasm_declarations_remain_raw_and_ast_identical(self):
        old_class = next(node for node in self.parsed.body if isinstance(node, ast.ClassDef) and node.name == "AlertImportantRecoveryNewOnlyTests")
        methods = {node.name: node for node in old_class.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
        self.assertEqual(set(ACCEPTED_METHODS), set(methods))
        self.assertEqual(19, len(methods))
        for name, node in methods.items():
            with self.subTest(method=name):
                self.assertEqual(ACCEPTED_METHODS[name]["raw_sha256"], digest(raw_node(self.historical, node)))
                self.assertEqual(ACCEPTED_METHODS[name]["portable_ast_sha256"], ast_digest(node))
        for name, expected in RETAINED_ASSIGNMENTS.items():
            with self.subTest(assignment=name):
                self.assertEqual(expected["raw_sha256"], digest(raw_node(self.historical, self.assignments[name])))
                self.assertEqual(expected["portable_ast_sha256"], ast_digest(self.assignments[name]))
        hooks = {"source_before_share_alert153_rebase": "    current = source_before_alert_container153_observation(relative, current)\n",
                 "native_sections": "    source = source_before_alert_container153_observation(NATIVE, source.encode()).decode()\n"}
        for node in self.parsed.body:
            if isinstance(node, ast.FunctionDef) and node.name in hooks:
                raw = raw_node(self.historical, node)
                self.assertEqual(1, raw.count(hooks[node.name].encode()))
                self.assertEqual(RETAINED_FUNCTIONS[node.name], digest(raw.replace(hooks[node.name].encode(), b"", 1)))

    def test_fixed_scalar_schema_classifies_only_index_origins_and_has_a_small_line_bound(self):
        expression = self.observer.split('println("' + PREFIX + ' captured=true " +\n', 1)[1].split(")\n", 1)[0]
        template = PREFIX + " captured=true " + "".join(re.findall(r'"([^"\n]*)"', expression))
        values = {"mainThread": True, "admitted": True, "attachmentsHeld": True, "unknown": True,
                  "owners.size": 16, "duplicateOwners": 16, "detachedOwners": 16, "countOwners": 16,
                  "negativeCounts": 16, "zeroCounts": 16, "ownerPrefixTruncated": True, "indexTruncated": True,
                  "indexReads": 32, "nilChildren": 32, "unsupportedChildren": 32, "viewChildren": 32,
                  "elementChildren": 32, "otherObjectChildren": 32, "duplicateChildren": 32, "selfChildren": 32,
                  "retained.size": 48, "labelMatches": 32, "buttonMatches": 32, "backlinkSourceOwner": 32,
                  "backlinkNil": 32, "backlinkOther": 32, "backlinkUnsupported": 32}
        seen = []
        def scalar(match):
            key = match[1] or match[2]
            if key not in values:
                raise ValueError("Object/content/error interpolation refused")
            seen.append(key)
            value = values[key]
            return str(value).lower() if type(value) is bool else str(value)
        line = re.sub(r"\$\{([^}]+)\}|\$([A-Za-z_]\w*)", scalar, template)
        self.assertEqual(set(values), set(seen))
        pairs = line.split(" ")[1:]
        self.assertEqual(len(pairs), len({pair.split("=", 1)[0] for pair in pairs}))
        self.assertTrue(all(re.fullmatch(r"[a-z_]+=(?:true|false|0|[1-9][0-9]*)", pair) for pair in pairs))
        self.assertLess(len(line), 2048)
        for key in ("list_observed", "nested_containers_observed", "child_visibility_observed", "child_window_observed"):
            self.assertIn(key + "=false", pairs)
        self.assertEqual(1, self.observer.count('println("' + PREFIX + ' captured=false")'))

    def test_declared_owner_index_retention_and_identity_work_bounds_are_finite_without_graph_expansion(self):
        self.assertIn("val ownerLimit = 16\n", self.observer)
        self.assertIn("val perOwnerIndexLimit = 4L\n", self.observer)
        self.assertIn("val totalIndexLimit = 32\n", self.observer)
        self.assertIn("minOf(count, perOwnerIndexLimit, (totalIndexLimit - indexReads).toLong())", self.observer)
        self.assertIn("while (index < inspectCount)", self.observer)
        self.assertIn("check(retained.size < ownerLimit + totalIndexLimit)", self.observer)
        self.assertIn("owners.any { sameNativeObject(it, owner) }", self.observer)
        self.assertIn("retained.any { sameNativeObject(it, native) }", self.observer)
        self.assertEqual(48, 16 + 32)
        self.assertLessEqual(16 * 15 // 2 + 32 * 48 + 32 + 32, 1720)
        self.assertEqual(1, self.observer.count("owner.accessibilityElementCount()"))
        self.assertEqual(1, self.observer.count("owner.accessibilityElementAtIndex(index)"))
        self.assertEqual(1, self.observer.count("child.accessibilityContainer"))
        for forbidden in ("accessibilityElements", "indexOfAccessibilityElement", "ArrayDeque", "importantAlertDescendants()",
                          "pending", ".superview", ".window.root", "native.window", "child.window", "backlink.accessibility"):
            self.assertNotIn(forbidden, self.observer)

    def test_unknown_throw_and_partial_source_mutations_refuse_before_reconstructing_historical_guards(self):
        self.assertIn("if (count < 0L)", self.observer)
        self.assertIn("null -> { nilChildren++; unknown = true }", self.observer)
        self.assertIn("else -> { unsupportedChildren++; unknown = true }", self.observer)
        self.assertIn("catch (_: Throwable)", self.observer)
        self.assertNotIn("primaryFailure", self.observer)
        for forbidden in ("accessibilityActivate", ".activateAction(", ".dismiss(", "performSelector", "valueForKey",
                          "NSClassFromString", "setValue(", "UITouch(", "UIEvent(", "println(child", "println(native",
                          "Throwable.message", "addSuppressed", "toString()"):
            self.assertNotIn(forbidden, self.observer)
        changes = [(b"val ownerLimit = 16", b"val ownerLimit = 17"),
                   (b"val perOwnerIndexLimit = 4L", b"val perOwnerIndexLimit = 5L"),
                   (b"val totalIndexLimit = 32", b"val totalIndexLimit = 33"),
                   (b"if (count < 0L)", b"if (count < -1L)"),
                   (b"list_observed=false", b"list_observed=true"),
                   (b"$labelMatches", b"$title"),
                   (b"throw readinessFailure", b"return"),
                   (b"eligible.single().accessibilityActivate()", b"true")]
        inverse = self.namespace["source_before_alert_container153_observation"]
        for before, after in changes:
            with self.subTest(mutation=before), self.assertRaises(ValueError):
                inverse(NATIVE, self.native.replace(before, after, 1))
        for value in (self.native + b"\n", self.native + self.observer.encode(), self.original + self.observer.encode(),
                      self.native.replace(self.binding["fragments"][0]["after"].encode(), self.binding["fragments"][0]["before"].encode(), 1),
                      self.native.decode(), None):
            with self.subTest(type=type(value).__name__), self.assertRaises(ValueError):
                inverse(NATIVE, value)
        refused = copy.deepcopy(self.namespace["ALERT_CONTAINER153_OBSERVATION"])
        refused["fragments"][0]["after_fragment_sha256"] = "0" * 64
        self.namespace["ALERT_CONTAINER153_OBSERVATION"] = refused
        with self.assertRaises(ValueError): inverse(NATIVE, self.native)

    def test_native_inverse_composes_with_exact_existing_share_and_optional_wasm_images_without_repinning(self):
        combined = self.namespace["source_before_share_alert153_rebase"]
        self.assertEqual(self.original, combined(NATIVE, self.native))
        self.assertEqual(self.original, combined(NATIVE, self.original))
        for relative, binding in self.namespace["SHARE_ALERT153_REBASE"].items():
            current = (ROOT / relative).read_bytes()
            with self.subTest(relative=relative):
                self.assertEqual(binding["original153_sha256"], digest(combined(relative, current)))
                with self.assertRaises(ValueError): combined(relative, current + b"\n")


if __name__ == "__main__":
    unittest.main()
