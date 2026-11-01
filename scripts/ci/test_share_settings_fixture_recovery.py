"""Owning source-fixture recovery only; no accepted8/9 test replay or native work."""
import ast
import hashlib
from pathlib import Path
import tempfile
import unittest

import library_tests as lt

ROOT = Path(__file__).resolve().parents[2]
GUARD = "scripts/ci/test_ios_share_owned_root_barriers.py"
FOCUS = "scripts/ci/test_ios_share_presentation_focus.py"
GUARD_SHA256 = '71467292fa2d21fb68615aea5dc4f4f17f291cfe550b2939200b5343f1287f24'
FOCUS_SHA256 = "edcc6f136b1d786358dc547946680b9f4ea8d82af339ca31213cfa47d72bfb6f"


_GUARD_COMPILER_REPAIR_172 = {'after_sha256': '7f06ae1ecaf0beacd2ffbe24f95c6baa1d4b764b28a2023eb1ae4153dba0407b', 'before': 'def _read_sources():\n    return {relative: _support_before_fixture_repair169(relative, (ROOT / relative).read_bytes().decode("utf-8"))\n            for relative in (*_SPEC["changed_paths"], *_SPEC["support_paths"])}', 'after': '_COMPILER_SOURCE_REPAIRS_172 = {\'calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosSharePresentationOwnershipTest.kt\': {\'before_sha256\': \'0ca8ef9a5b0c3cfd8922c40a248058efe4f521e560b2752267d2048ce54ec0a6\', \'after_sha256\': \'250b536388c872d6fd975ad009ca47a750575df28b1eb0d1981ba6d124d63b9d\', \'fragments\': [{\'before\': \'import kotlinx.coroutines.Dispatchers\\n\', \'after\': \'import kotlinx.coroutines.Dispatchers\\nimport kotlinx.coroutines.IO\\n\'}, {\'before\': \'assertEquals((1..index + 1).map { it to ShareOutcome.Completed }, deliveries)\', \'after\': \'assertEquals<List<Pair<Int, ShareOutcome>>>((1..index + 1).map { it to ShareOutcome.Completed }, deliveries)\'}, {\'before\': \'assertEquals((1..3).map { it to ShareOutcome.Completed }, deliveries)\', \'after\': \'assertEquals<List<Pair<Int, ShareOutcome>>>((1..3).map { it to ShareOutcome.Completed }, deliveries)\'}]}, \'calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/internal/NativeShareApplicationHost.kt\': {\'before_sha256\': \'f6917c04e5f9a39ec8a74a1953c67a82d27c7cb02f27cb69287534a84106754d\', \'after_sha256\': \'e2b6affcea3a3a34b9d1b95f5d60e5d492efbca55f8a02ab38ac459cf23fb953\', \'fragments\': [{\'before\': \'import platform.UIKit.UIWindow\\n\', \'after\': \'import platform.UIKit.UIWindow\\nimport platform.UIKit.transitionCoordinator\\n\'}]}}\n\n\ndef _source_before_compiler_repair172(relative, text):\n    """Only exact missing-import/type-inference repairs reconstruct the reviewed fixture."""\n    if relative not in _COMPILER_SOURCE_REPAIRS_172:\n        return text\n    binding = _COMPILER_SOURCE_REPAIRS_172[relative]\n    if _sha256(text) != binding["after_sha256"]:\n        raise ValueError("Exact owning compiler fixture repair is required")\n    for fragment in reversed(binding["fragments"]):\n        if text.count(fragment["after"]) != 1:\n            raise ValueError("Exact unique compiler inverse is required")\n        text = text.replace(fragment["after"], fragment["before"], 1)\n    if _sha256(text) != binding["before_sha256"]:\n        raise ValueError("Compiler inverse changed the reviewed native assertion bytes")\n    return text\n\n\ndef _read_sources():\n    return {relative: _support_before_fixture_repair169(relative,\n                _source_before_compiler_repair172(relative, (ROOT / relative).read_bytes().decode("utf-8")))\n            for relative in (*_SPEC["changed_paths"], *_SPEC["support_paths"])}'}


def guard_before_compiler_repair172(raw):
    """Exact disjoint compiler admission addition; original NEW2 bindings stay unchanged."""
    if hashlib.sha256(raw).hexdigest() != _GUARD_COMPILER_REPAIR_172["after_sha256"]:
        raise ValueError("Exact compiler-composed guard image required")
    before = _GUARD_COMPILER_REPAIR_172["before"].encode()
    after = _GUARD_COMPILER_REPAIR_172["after"].encode()
    if raw.count(after) != 1:
        raise ValueError("Exact unique compiler guard inverse required")
    historical = raw.replace(after, before, 1)
    if hashlib.sha256(historical).hexdigest() != GUARD_SHA256:
        raise ValueError("Disjoint compiler addition changed original NEW2 guard helpers")
    return historical


def selected_inverse():
    raw = guard_before_compiler_repair172((ROOT / GUARD).read_bytes())
    if hashlib.sha256(raw).hexdigest() != GUARD_SHA256:
        raise ValueError("Exact owning guard correction bytes required")
    tree = ast.parse(raw)
    names = {"_FOCUS_FIXTURE_REPAIRED_SHA256", "_FOCUS_FIXTURE_BEFORE", "_FOCUS_FIXTURE_AFTER", "FOCUS_GUARD", "_SPEC"}
    nodes = [n for n in tree.body
             if isinstance(n, ast.FunctionDef) and n.name in {"_sha256", "_support_before_fixture_repair169"}
             or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets)]
    namespace = {"hashlib": hashlib}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<only-owning-fixture-inverse>", "exec"), namespace)
    return namespace


class ShareSettingsFixtureRecoveryTests(unittest.TestCase):
    def test_fixture_matches_the_literal_repository_include_contract_without_parser_relaxation(self):
        source = (ROOT / FOCUS).read_bytes()
        self.assertEqual(FOCUS_SHA256, hashlib.sha256(source).hexdigest())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "calf-share").mkdir()
            (root / "calf-share/build.gradle.kts").write_text("// synthetic\n")
            settings = root / "settings.gradle.kts"
            settings.write_text('include(":calf-share")\n')
            with self.assertRaisesRegex(ValueError, "literal settings include block"):
                lt.projects(root)
            settings.write_text('include(\n    ":calf-share",\n)\n')
            self.assertEqual({"calf-share": ":calf-share"}, lt.projects(root))

    def test_support_inverse_admits_only_the_exact_owning_repair_and_rejects_drift(self):
        namespace = selected_inverse()
        inverse = namespace["_support_before_fixture_repair169"]
        source = (ROOT / FOCUS).read_text()
        historical = inverse(FOCUS, source)
        expected = namespace["_SPEC"]["support_sha256"][FOCUS]
        self.assertEqual(expected, hashlib.sha256(historical.encode()).hexdigest())
        for changed in (historical, source + "\n", source.replace(namespace["_FOCUS_FIXTURE_AFTER"], "", 1),
                        source + namespace["_FOCUS_FIXTURE_AFTER"]):
            with self.subTest(shape=len(changed)), self.assertRaises(ValueError):
                inverse(FOCUS, changed)
        self.assertEqual("unchanged", inverse("other-support", "unchanged"))
