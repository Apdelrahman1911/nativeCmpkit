"""Initially unexecuted finite alias source models; no builds, native, network or acceptance.

The full parent branches/selectors remain authoritative and unchanged. These new
methods qualify only the additive alias wiring; they never execute native methods
or import/replay existing accepted test modules.
"""
from collections import Counter
import ast
import copy
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import dependency_cache_inputs as cache
import desktop_security_plan as security
import library_tests as lt
import workflow_matrix as matrix

ALIASES = {
    "webview-desktop-request-state-linux-pair": ("webview-desktop-request-state", ("desktop-linux-x64", "desktop-linux-arm64")),
    "webview-desktop-request-state-macos-pair": ("webview-desktop-request-state", ("desktop-macos-arm64", "desktop-macos-x64")),
    "webview-desktop-request-state-windows-single": ("webview-desktop-request-state", ("desktop-windows-x64",)),
    "webview-desktop-security-linux-arm64-windows-pair": ("webview-desktop-security-regressions", ("desktop-windows-x64", "desktop-linux-arm64")),
    "webview-desktop-security-macos-pair": ("webview-desktop-security-regressions", ("desktop-macos-arm64", "desktop-macos-x64")),
}
REQUEST = tuple(name for name, (parent, _) in ALIASES.items() if parent == "webview-desktop-request-state")
SECURITY = tuple(name for name in ALIASES if name not in REQUEST)
REQUEST_FOCI = {
    "desktop-linux-x64": "webview-desktop-request-state",
    "desktop-macos-arm64": "webview-desktop-request-state-stop",
    "desktop-windows-x64": "webview-desktop-request-state-stop",
    "desktop-linux-arm64": "webview-desktop-request-state-stop-redirect",
    "desktop-macos-x64": "webview-desktop-request-state-stop",
}
REQUEST_COUNTS = {"desktop-linux-x64": (1, 1), "desktop-macos-arm64": (2, 2),
                  "desktop-windows-x64": (2, 2), "desktop-linux-arm64": (3, 2), "desktop-macos-x64": (2, 2)}
REQUEST_CASES = (
    ("com.mohamedrejeb.calf.ui.web.DesktopWebViewRequestStateAcceptanceTest", "twoHeldNativeTransportFailuresResetOldErrorsAndRecoverOnTheSameOwner[desktop]"),
    ("com.mohamedrejeb.calf.ui.web.DesktopWebViewStopRedirectAcceptanceTest", "publicStopCancelsOneHeldNativeRequestBeforeAnyResponseAndRecoversOnTheSameOwner[desktop]"),
    ("com.mohamedrejeb.calf.ui.web.DesktopWebViewStopRedirectAcceptanceTest", "actual302RedirectAndPublicReloadKeepNativeRequestAndTerminalMetadataDistinct[desktop]"),
)
CAPTURE = "if: ${{ !cancelled() && steps.plan.outcome == 'success' && (inputs.profile == 'webview-desktop-security-regressions' || inputs.profile == 'webview-desktop-security-linux-arm64-windows-pair' || inputs.profile == 'webview-desktop-security-macos-pair') }}"


def alias_mapping_source(source):
    tree = ast.parse(source)
    owner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "matrix")
    nodes = [node for node in ast.walk(owner) if isinstance(node, ast.Assign) and
             any(isinstance(target, ast.Name) and target.id == "aliases" for target in node.targets)]
    if len(nodes) != 1 or not isinstance(nodes[0].value, ast.Dict):
        raise ValueError("One literal finite alias-parent mapping is required")
    keys = [ast.literal_eval(key) for key in nodes[0].value.keys]
    if len(keys) != 5 or len(set(keys)) != 5 or ast.literal_eval(nodes[0].value) != ALIASES:
        raise ValueError("Keep exact five canonical alias parents/slot tuples; no broad or arbitrary route")
    return ast.get_source_segment(source, nodes[0].value)


class DesktopFiniteAliasModels(unittest.TestCase):
    def test_five_aliases_have_exact_literal_parents_slots_and_all_inherited_row_fields(self):
        source = (lt.ROOT / "scripts/ci/workflow_matrix.py").read_text()
        alias_mapping_source(source)
        original = {row["slot"]: row for row in security.ROWS}
        for name, (parent, slots) in ALIASES.items():
            with self.subTest(alias=name):
                self.assertEqual(slots, matrix.PROFILES[name])
                self.assertEqual("calf-webview", matrix.MODULE_SUBSETS[name])
                rows = matrix.matrix(name)["include"]
                inherited = [row for row in matrix.matrix(parent)["include"] if row["slot"] in slots]
                self.assertEqual(inherited, rows)
                self.assertEqual(slots, tuple(row["slot"] for row in rows))
                self.assertLessEqual(len(rows), 2)
                for row in rows:
                    self.assertEqual("desktop", row["suite"])
                    self.assertEqual("calf-webview", row["test-modules"])
                    self.assertEqual(original[row["slot"]]["runner"], row["runner"])
                    self.assertEqual(original[row["slot"]]["arch"], row["arch"])
                    expected = REQUEST_FOCI[row["slot"]] if name in REQUEST else original[row["slot"]]["focus"]
                    self.assertEqual(expected, row["test-focus"])
                    self.assertFalse(any(key.startswith("serial-") or key == "android-batch" for key in row))

    def test_request_three_aliases_partition_only_ten_missing_cells_and_nine_original_xml(self):
        selected, xml = [], []
        for name in REQUEST:
            cells = []
            reports = 0
            for row in matrix.matrix(name)["include"]:
                plan = lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",), focus=row["test-focus"])
                item, = plan["expected"]
                count, expected_xml = REQUEST_COUNTS[row["slot"]]
                expected_cases = REQUEST_CASES[:count]
                self.assertEqual(list(expected_cases), [(case["classname"], case["name"]) for case in item["required_testcases"]])
                self.assertEqual(":calf-webview:desktopTest", item["task"])
                self.assertNotIn("required_original_xml", item)
                self.assertEqual(expected_xml, len({case["classname"] for case in item["required_testcases"]}))
                self.assertFalse(plan["complete_suite_requested"])
                self.assertEqual(["calf-webview"], plan["explicit_module_subset"])
                cells.extend((row["slot"], *case) for case in expected_cases)
                reports += expected_xml
            selected.extend(cells)
            xml.append(reports)
            self.assertEqual((4, 4, 2)[REQUEST.index(name)], len(cells))
        self.assertEqual([3, 4, 2], xml)
        self.assertEqual(10, len(selected))
        self.assertEqual(10, len(set(selected)))
        self.assertEqual({slot for slot in REQUEST_COUNTS}, {cell[0] for cell in selected})
        full = [(row["slot"], *case) for row in matrix.matrix("webview-desktop-request-state")["include"]
                for case in REQUEST_CASES[:REQUEST_COUNTS[row["slot"]][0]]]
        self.assertCountEqual(full, selected)
        # Accepted Linux x64 Stop and four-host redirect/Reload cells are not in this exact union.
        self.assertNotIn(("desktop-linux-x64", *REQUEST_CASES[1]), selected)
        self.assertEqual({"desktop-linux-arm64"}, {cell[0] for cell in selected if cell[1:] == REQUEST_CASES[2]})

    def test_security_two_aliases_partition_remaining_thirteen_and_never_accepted_linux_tls(self):
        original = {row["slot"]: row for row in security.ROWS}
        selected = []
        for name in SECURITY:
            cells = []
            for row in matrix.matrix(name)["include"]:
                self.assertNotEqual("desktop-linux-x64", row["slot"])
                required = original[row["slot"]]
                plan = lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",), focus=row["test-focus"])
                item, = plan["expected"]
                expected = [(security.SPECS[key][0], security.SPECS[key][1] + "[desktop]") for key in required["selected"]]
                self.assertEqual(expected, [(case["classname"], case["name"]) for case in item["required_testcases"]])
                self.assertEqual(len(expected), item["required_original_xml"])
                self.assertEqual(":calf-webview:desktopTest", item["task"])
                self.assertEqual(1, plan["desktop_security_fixture"]["max_parallel_forks"])
                self.assertEqual(1, plan["desktop_security_fixture"]["fork_every"])
                self.assertFalse(plan["complete_suite_requested"])
                cells.extend((row["slot"], *case) for case in expected)
            self.assertEqual((7, 6)[SECURITY.index(name)], len(cells))
            selected.extend(cells)
        self.assertEqual(13, len(selected))
        self.assertEqual(13, len(set(selected)))
        self.assertEqual(Counter({"desktop-macos-arm64": 3, "desktop-windows-x64": 3,
                                  "desktop-linux-arm64": 4, "desktop-macos-x64": 3}), Counter(cell[0] for cell in selected))
        full = [(row["slot"], security.SPECS[key][0], security.SPECS[key][1] + "[desktop]")
                for row in security.ROWS if row["slot"] != "desktop-linux-x64" for key in row["selected"]]
        self.assertCountEqual(full, selected)
        self.assertFalse(set(cell[1:] for cell in selected) & set(REQUEST_CASES))

    def test_alias_tuple_mutations_refuse_extra_unknown_duplicate_missing_list_and_reordering(self):
        for name, (_, slots) in ALIASES.items():
            variants = [slots[:-1], (*slots, slots[-1]), ("foreign-host", *slots[1:]),
                        (*slots, "desktop-linux-x64"), list(slots)]
            if len(slots) == 2:
                variants.extend([(), tuple(reversed(slots))])
            for changed in variants:
                with self.subTest(alias=name, changed=changed), patch.dict(matrix.PROFILES, {name: changed}), self.assertRaises(ValueError):
                    matrix.matrix(name)

    def test_alias_module_and_selected_suite_runner_architecture_drift_are_refused(self):
        for name, (parent, slots) in ALIASES.items():
            for value in ("calf-io", None, "calf-webview,calf-io"):
                with self.subTest(alias=name, module=value), patch.dict(matrix.MODULE_SUBSETS, {name: value}), self.assertRaises(ValueError):
                    matrix.matrix(name)
            with self.subTest(alias=name, canonical_parent_module=True), patch.dict(matrix.MODULE_SUBSETS, {parent: "calf-io"}), self.assertRaises(ValueError):
                matrix.matrix(name)
            for field, value in (("suite", "android-device"), ("runner", "self-hosted"), ("arch", "foreign-arch")):
                changed = tuple(dict(row) for row in matrix.SLOTS)
                next(row for row in changed if row["slot"] == slots[0])[field] = value
                with self.subTest(alias=name, field=field), patch.object(matrix, "SLOTS", changed), self.assertRaises(ValueError):
                    matrix.matrix(name)
            if len(slots) == 2:
                with self.subTest(alias=name, inherited_slot_order=True), patch.object(matrix, "SLOTS", tuple(reversed(matrix.SLOTS))), self.assertRaises(ValueError):
                    matrix.matrix(name)

    def test_literal_parent_slot_mapping_mutations_refuse_and_full_security_source_gate_stays_exact(self):
        source = (lt.ROOT / "scripts/ci/workflow_matrix.py").read_text()
        literal = alias_mapping_source(source)
        variants = [literal.replace('"webview-desktop-request-state"', '"webview-desktop-security-regressions"', 1),
                    literal.replace('"desktop-linux-arm64"', '"desktop-windows-x64"', 1),
                    literal.replace('("desktop-linux-x64", "desktop-linux-arm64")', '["desktop-linux-x64", "desktop-linux-arm64"]', 1),
                    literal[:-1] + '"foreign-alias": ("webview-desktop-request-state", ())}']
        for changed in variants:
            self.assertNotEqual(literal, changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                alias_mapping_source(source.replace(literal, changed, 1))
        # Inspect accepted full-route source expectations, never import/run its methods.
        guard = ast.parse((lt.ROOT / "scripts/ci/test_desktop_security_remaining13.py").read_text())
        for name in ("PROFILE_LITERAL", "BRANCH_LITERAL"):
            node = next(node for node in guard.body if isinstance(node, ast.Assign) and
                        any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
            self.assertEqual(1, source.count(ast.literal_eval(node.value)))
        self.assertEqual(5, len(matrix.matrix("webview-desktop-request-state")["include"]))
        self.assertEqual(4, len(matrix.matrix("webview-desktop-security-regressions")["include"]))
        for name in ("webview-desktop-request-state-foreign-pair", "webview-desktop-security-foreign-pair"):
            with self.subTest(unknown=name), self.assertRaises(ValueError):
                matrix.matrix(name)

    def test_returned_alias_rows_cannot_mutate_all_parent_or_later_alias_calls(self):
        before = {parent: copy.deepcopy(matrix.matrix(parent)) for parent in {parent for parent, _ in ALIASES.values()}}
        complete = copy.deepcopy(matrix.matrix("all"))
        for name, (parent, _) in ALIASES.items():
            original = copy.deepcopy(matrix.matrix(name))
            changed = matrix.matrix(name)
            changed["include"][0]["runner"] = "self-hosted"
            changed["include"][0]["test-focus"] = "foreign-focus"
            changed["include"].append({"slot": "foreign-host"})
            self.assertEqual(original, matrix.matrix(name))
            self.assertEqual(before[parent], matrix.matrix(parent))
            self.assertEqual(complete, matrix.matrix("all"))
        self.assertEqual(11, len(complete["include"]))

    def test_workflow_has_only_five_choices_and_security_capture_aliases_with_unchanged_capacity(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        options = re.search(r"options: \[([^\n]+)\]", workflow).group(1)
        choices = [name.strip() for name in options.split(",")]
        self.assertEqual(set(matrix.PROFILES), set(choices))
        self.assertEqual(len(choices), len(set(choices)))
        for name in ALIASES:
            self.assertEqual(1, choices.count(name))
        start = workflow.index("      - name: Capture missing-host Desktop dependency graphs without native replay\n")
        end = workflow.index("      - name: Related real JVM/JNI path tests", start)
        step = workflow[start:end]
        self.assertIn(CAPTURE, step)
        self.assertEqual({security.PROFILE, *SECURITY}, set(re.findall(r"inputs.profile == '([^']+)'", step)))
        for name in (*REQUEST, "foreign-security-profile"):
            self.assertNotIn(name, step)
        self.assertIn('"$PYTHON" scripts/ci/desktop_dependency_capture.py \\\n            --profile webview-desktop-security-regressions --slot "$SLOT"', step)
        for text in ("continue-on-error", "--focus", "matrix.test-focus", "serial-test-focus"):
            self.assertNotIn(text, step)
        library = workflow.split("\n  library-tests:\n", 1)[1].split("\n  webview-consumer:\n", 1)[0]
        expression = next(line for line in library.splitlines() if "max-parallel:" in line)
        for name in ALIASES:
            self.assertNotIn(name, expression)
        self.assertTrue(expression.endswith("&& 1 || 2 }}"))
        self.assertIn("fail-fast: false", library)
        self.assertIn("permissions:\n  contents: read\n", workflow)
        self.assertIn("persist-credentials: false", library)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)
        native = workflow.split("      - name: Fresh actual library suite with strict nonzero receipts", 1)[1].split("        env:", 1)[0]
        self.assertIn("if: ${{ !cancelled() && steps.plan.outcome == 'success' }}", native)
        upload = library.split("      - name: Keep receipts and actual selected-task XML only; never packages", 1)[1]
        for forbidden in ("*.jar", "*.aar", "*.apk", "*.app", "*.log", "desktop-dependency-capture-private"):
            self.assertNotIn(forbidden, upload)

    def test_alias_cache_keys_equal_inherited_slot_keys_without_new_graph_or_trust_claims(self):
        selection = cache.selection_contract(lt.ROOT, "calf-webview")
        self.assertEqual(["calf-webview"], selection["modules"])
        self.assertRegex(selection["cache_key"], r"\Asubset-[0-9a-f]{64}\Z")
        systems = {"ubuntu-24.04": "Linux", "ubuntu-24.04-arm": "Linux", "macos-26": "macOS",
                   "macos-26-intel": "macOS", "windows-2025": "Windows"}
        def key(row):
            return "nativecmpkit-deps-v2-" + "-".join((systems[row["runner"]], row["arch"], row["slot"], row["suite"],
                selection["cache_key"], "a" * 64, "b" * 64))
        for name, (parent, slots) in ALIASES.items():
            rows = matrix.matrix(name)["include"]
            inherited = [row for row in matrix.matrix(parent)["include"] if row["slot"] in slots]
            self.assertEqual([key(row) for row in inherited], [key(row) for row in rows])
            for row in rows:
                self.assertLessEqual(len(key(row)), 512)
                self.assertRegex(key(row), r"\A[A-Za-z0-9_-]+\Z")
                self.assertNotIn("calf-webview", key(row))


if __name__ == "__main__":
    unittest.main()
