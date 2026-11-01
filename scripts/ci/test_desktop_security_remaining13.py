"""Remaining13 workflow models; no native/build/network/Git or acceptance claim.

Original14 native/source metadata remains available only to preserve its exact
receipt/pin contract. The owning workflow excludes the accepted Linux x64 TLS1.
"""
from collections import Counter
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import desktop_security_plan as security
import library_tests as lt
import workflow_matrix as matrix

PROFILE = "webview-desktop-security-regressions"
EXPECTED = (
    ("desktop-macos-arm64", "Darwin", "arm64", "tls-rendering-cookies-policy", ("tls-rendering", "cookie", "policy")),
    ("desktop-windows-x64", "Windows", "AMD64", "tls-rendering-cookies-policy", ("tls-rendering", "cookie", "policy")),
    ("desktop-linux-arm64", "Linux", "aarch64", "tls-rendering-cookies-policy-media", ("tls-rendering", "cookie", "policy", "media")),
    ("desktop-macos-x64", "Darwin", "x86_64", "tls-rendering-cookies-policy", ("tls-rendering", "cookie", "policy")),
)
EXPECTED_SLOTS = tuple(row[0] for row in EXPECTED)
PROFILE_LITERAL = '    "webview-desktop-security-regressions": ("desktop-macos-arm64", "desktop-windows-x64", "desktop-linux-arm64", "desktop-macos-x64"),\n'
BRANCH_LITERAL = '        # Linux x64 TLS1 is accepted; keep original metadata for receipts, not replay.\n        exact = {row["slot"]: row for row in desktop_security_plan.ROWS\n                 if row["slot"] != "desktop-linux-x64"}\n        if PROFILES[profile] != tuple(exact) or [row["slot"] for row in rows] != list(exact):\n            raise ValueError("Desktop security must select exactly four remaining slots; no accepted TLS replay")\n'


def require_remaining_source(source):
    if source.count(PROFILE_LITERAL) != 1 or source.count(BRANCH_LITERAL) != 1:
        raise ValueError("Keep exact finite remaining13 source gates; no accepted replay or partial narrowing")


class DesktopSecurityRemaining13Models(unittest.TestCase):
    def test_profile_selects_four_remaining_hosts_and_exact_original_thirteen_cells(self):
        rows = matrix.matrix(PROFILE)["include"]
        self.assertEqual(list(EXPECTED_SLOTS), [row["slot"] for row in rows])
        self.assertEqual(4, len(rows))
        self.assertFalse(any(row["slot"] == "desktop-linux-x64" for row in rows))
        selected = []
        for row, (slot, system, arch, focus, keys) in zip(rows, EXPECTED):
            with self.subTest(slot=slot):
                self.assertEqual(("desktop", "calf-webview", focus), tuple(row[key] for key in ("suite", "test-modules", "test-focus")))
                self.assertFalse(any(key.startswith("serial-") or key == "android-batch" for key in row))
                owned = security.selection(system, arch)
                self.assertEqual(keys, owned["selected"])
                plan = lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",), focus=focus)
                item, = plan["expected"]
                cases = [{"classname": security.SPECS[key][0], "name": security.SPECS[key][1] + "[desktop]"} for key in keys]
                self.assertEqual(cases, item["required_testcases"])
                self.assertEqual(len(keys), item["required_original_xml"])
                self.assertEqual(security.selected_sources(focus), item["test_source_sha256"])
                self.assertFalse(plan["complete_suite_requested"])
                self.assertEqual(1, plan["desktop_security_fixture"]["max_parallel_forks"])
                self.assertEqual(1, plan["desktop_security_fixture"]["fork_every"])
                with patch("library_tests.platform.system", return_value=system), patch("library_tests.platform.machine", return_value=arch):
                    command = lt.gradle_command("desktop", plan, root=lt.ROOT)
                selectors = [command[i + 1] for i, value in enumerate(command) if value == "--tests"]
                self.assertEqual(list(owned["selectors"]), selectors)
                self.assertEqual(1, command.count(":calf-webview:desktopTest"))
                self.assertEqual(1, command.count("-PnativecmpkitDesktopSecurityFocus=" + focus))
                selected.extend((slot, value) for value in selectors)
        self.assertEqual(13, len(selected))
        self.assertEqual(13, len(set(selected)))
        self.assertEqual(Counter({EXPECTED_SLOTS[0]:3, EXPECTED_SLOTS[1]:3, EXPECTED_SLOTS[2]:4, EXPECTED_SLOTS[3]:3}), Counter(slot for slot, _ in selected))

    def test_exact_source_gate_preserves_original_metadata_full_scopes_request10_and_capacity(self):
        source = (lt.ROOT / "scripts/ci/workflow_matrix.py").read_text()
        require_remaining_source(source)
        self.assertEqual(5, len(security.ROWS))
        self.assertEqual(14, sum(len(row["selected"]) for row in security.ROWS))
        self.assertEqual("desktop-linux-x64", security.ROWS[0]["slot"])
        self.assertEqual(("tls-rendering",), security.ROWS[0]["selected"])
        self.assertEqual(list(matrix.SLOTS), matrix.matrix("all")["include"])
        self.assertEqual(11, len(matrix.SLOTS))
        self.assertTrue(all("test-focus" not in row for row in matrix.matrix("all")["include"]))
        request = matrix.matrix("webview-desktop-request-state")["include"]
        self.assertEqual([row["slot"] for row in security.ROWS], [row["slot"] for row in request])
        self.assertEqual(["webview-desktop-request-state", "webview-desktop-request-state-stop", "webview-desktop-request-state-stop", "webview-desktop-request-state-stop-redirect", "webview-desktop-request-state-stop"], [row["test-focus"] for row in request])
        self.assertEqual(2, security.MAX_PARALLEL)
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)
        library = workflow.split("\n  library-tests:\n", 1)[1].split("\n  webview-consumer:\n", 1)[0]
        self.assertNotIn(PROFILE, next(line for line in library.splitlines() if "max-parallel:" in line))
        self.assertIn("&& 1 || 2 }}", library)
        self.assertNotIn("RequestState", security.SECURITY_CLASS)

    def test_matrix_refuses_accepted_replay_omissions_duplicates_unknown_slots_and_reordering(self):
        variants = (("desktop-linux-x64", *EXPECTED_SLOTS), EXPECTED_SLOTS[:-1], (*EXPECTED_SLOTS, EXPECTED_SLOTS[-1]), tuple(reversed(EXPECTED_SLOTS)), ("foreign-host", *EXPECTED_SLOTS[1:]), (), list(EXPECTED_SLOTS))
        for slots in variants:
            with self.subTest(slots=slots), patch.dict(matrix.PROFILES, {PROFILE:slots}), self.assertRaises(ValueError):
                matrix.matrix(PROFILE)
        for field, value in (("suite", "android-device"), ("runner", "ubuntu-24.04"), ("arch", "x64")):
            slots = tuple(dict(row) for row in matrix.SLOTS)
            next(row for row in slots if row["slot"] == EXPECTED_SLOTS[0])[field] = value
            with self.subTest(field=field), patch.object(matrix, "SLOTS", slots), self.assertRaises(ValueError):
                matrix.matrix(PROFILE)

    def test_source_literal_models_refuse_partial_narrowing_or_replay_filter_changes(self):
        source = (lt.ROOT / "scripts/ci/workflow_matrix.py").read_text()
        require_remaining_source(source)
        variants = (source.replace(PROFILE_LITERAL, PROFILE_LITERAL.replace('(\"desktop-macos-arm64\"', '(\"desktop-linux-x64\", \"desktop-macos-arm64\"'), 1),
                    source.replace('                 if row["slot"] != "desktop-linux-x64"', '', 1),
                    source.replace('if row["slot"] != "desktop-linux-x64"', 'if row["slot"] == "desktop-linux-x64"', 1),
                    source.replace('PROFILES[profile] != tuple(exact) or ', '', 1),
                    source.replace(BRANCH_LITERAL, BRANCH_LITERAL + BRANCH_LITERAL, 1))
        for candidate in variants:
            with self.subTest(candidate_length=len(candidate)), self.assertRaises(ValueError):
                require_remaining_source(candidate)

    def test_remaining_plan_refuses_accepted_host_scope_case_and_fixture_substitution(self):
        focus = EXPECTED[0][3]
        with patch("library_tests.platform.system", return_value="Linux"), patch("library_tests.platform.machine", return_value="x86_64"):
            with self.assertRaises(ValueError):
                lt.gradle_command("desktop", lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",), focus=focus), root=lt.ROOT)
        for suite, modules in (("desktop", None), ("desktop", ("calf-io",)), ("desktop", ("calf-webview", "calf-io")), ("android-device", ("calf-webview",))):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=focus)
        plan = lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",), focus=focus)
        for key, value in (("required_testcases", plan["expected"][0]["required_testcases"][:1]), ("required_original_xml", 1), ("test_filter", "*"), ("task", ":calf-webview:publish")):
            changed = copy.deepcopy(plan); changed["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                lt.validate_test_focus(changed)


if __name__ == "__main__":
    unittest.main()
