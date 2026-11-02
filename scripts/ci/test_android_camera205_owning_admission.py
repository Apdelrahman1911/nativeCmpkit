"""Six NEW Camera205 source-boundary controls; no accepted module imports/replay.

Only the new outer projection and exact top-level hash-admission statements are
AST-selected into inert namespaces. No scalar/failfast/NEW9 method, helper,
ModelFixture, old projection function or FIRST30 driver is imported or executed.
These controls are not a full import/discovery, native or whole-map acceptance.
The lead executes the six literal selectors once; the author executes none.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

TREE = Path(os.environ.get("NATIVECMPKIT_CAMERA205_SOURCE_TREE", Path(__file__).resolve().parents[2])).resolve()
HELPER = "scripts/ci/android_camera_developer_prerequisite.py"
SCALAR = "scripts/ci/test_android_camera_scalar_control_refusal.py"
FAILFAST = "scripts/ci/test_android_camera_pre_reporter_fail_fast.py"
PROJECTION = "scripts/ci/camera_scalar_failfast_source_projection.py"
CONSOLE = "scripts/ci/test_android_camera_owned_avd_console_name.py"
DRIVER = "scripts/ci/run_android_camera_scalar_failfast_new_only.py"
FIXTURE = "scripts/ci/test_android_camera_developer_prerequisite.py"
FF14 = "test_ff14_full_source_inverses_preserve_original_readers_actions_cleanup_and_single_call"
CN09 = "test_cn09_owning194_and_operational_native_bindings_are_not_rebased"
OUTER = "camera197_helper_source_before_owned_console"
EXPECTED_SHA256 = {
    "scripts/ci/android_camera_developer_prerequisite.py": "0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26",
    "scripts/ci/android_device_tests.py": "daac8786b1b034efcad0687a2f3a995c2216ea1a400116f9c592693d5c6395ec",
    "scripts/ci/camera_scalar_failfast_source_projection.py": "6858fbd343cefad52b709663fbf5e98bccfa52111c2a1b8fd6eff8d8536cdb12",
    "scripts/ci/fixtures/android-camera-scalar-failfast-controller-inverse.json": "9a3479f92b05e1bffda3b408ad9f5833ca655b0c913af813e888209de9b2828c",
    "scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json": "e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953",
    "scripts/ci/fixtures/android-camera-startup-readiness-inverse.json": "43a8963e59a7851e968fbbeeaafa19944956cbc6a6f0b5cb8924a4dba0342e2c",
    "scripts/ci/run_android_camera_scalar_failfast_new_only.py": "6ce3556e0df614757ede6c469ccc0e12a536b0aa9ce86214234e474fd22fc022",
    "scripts/ci/test_android_camera_developer_prerequisite.py": "4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb",
    "scripts/ci/test_android_camera_owned_avd_console_name.py": "f287837b12f41f8b86bb23696c75b6a102d8c604d47968209ba090a4f05d19da",
    "scripts/ci/test_android_camera_pre_reporter_fail_fast.py": "40e8b5450b81a51e45c018d455c7d31fa6b557a82bd809ad2f2472214bdc0676",
    "scripts/ci/test_android_camera_scalar_control_refusal.py": "e0ca6710cf89cb68ec21e91996ae49ee072e477dfc17b0eb0206794872444ffe"
}
DERIVATIVE_SHA256 = {
    "scripts/ci/camera_scalar_failfast_source_projection.py": "6858fbd343cefad52b709663fbf5e98bccfa52111c2a1b8fd6eff8d8536cdb12",
    "scripts/ci/test_android_camera_pre_reporter_fail_fast.py": "40e8b5450b81a51e45c018d455c7d31fa6b557a82bd809ad2f2472214bdc0676",
    "scripts/ci/test_android_camera_scalar_control_refusal.py": "e0ca6710cf89cb68ec21e91996ae49ee072e477dfc17b0eb0206794872444ffe"
}
HISTORICAL_SHA256 = {
    "FROZEN_CONTROLLER_SHA256": "02bb9ab153f147fab13bf58ff9fccaef754cc66f2dfcc067dc3ad2b1d8726640",
    "FROZEN_HELPER_SHA256": "5318d5893457dca141d08f3d269dc1a21078d42931c7846d4d105b7134154af1",
    "HISTORICAL_HELPER_SHA256": "f15163bd0406476d4c8e271aa6fa18c652590c1e1665ee7bb9306ca9140ddfd0",
    "PRE_STARTUP_HELPER_SHA256": "2d2fb89491d5435963b983052a96f7a9e80e02d9b7ed394c0b3d23cf4b194532"
}
UNCHANGED_METHOD_BUNDLES = {
    "scripts/ci/test_android_camera_owned_avd_console_name.py": {
        "methods": 8,
        "omitted": [
            "test_cn09_owning194_and_operational_native_bindings_are_not_rebased"
        ],
        "sha256": "5851ebd4802d5267b0e0a47dd4aed3a26ea968f82044528ed2a15913462bba02"
    },
    "scripts/ci/test_android_camera_pre_reporter_fail_fast.py": {
        "methods": 17,
        "omitted": [
            "test_ff14_full_source_inverses_preserve_original_readers_actions_cleanup_and_single_call"
        ],
        "sha256": "02babb91d2bbd7c2695ed4f2adc2821f94cafcbb337f723a5b2165c6270882b0"
    },
    "scripts/ci/test_android_camera_scalar_control_refusal.py": {
        "methods": 12,
        "omitted": [],
        "sha256": "d2b9ccfdc2b6840f5ad0520896a59c827314ad4f683c718cb54c63340cb506d4"
    }
}
IMPORT_BOUNDARY_SHA256 = {
    "scripts/ci/test_android_camera_pre_reporter_fail_fast.py": "74c468bb970e957e30639214558b7fa12300cff1a07a835176f63162acd8401a",
    "scripts/ci/test_android_camera_scalar_control_refusal.py": "dc3a5241a69bb38eb9e019347a34fcb533edb16b822c9fc6fa7fc93698f41702"
}
ORIGINAL_PROJECTION_BYTES = 1551
ORIGINAL_PROJECTION_SHA256 = '3a0f5a01f30e482af2cf3c6953d68a21aa3d824952eaca54556abe06045ccbbb'
BEFORE47_ASSIGNMENT_SHA256 = '2142056745f0b22d089cc04e3b27b9b63eb2bed121b39fd682eb256d2ceb8939'
BEFORE47_MAPPING_SHA256 = '20c23dab5010380ee878e2167098445fc9dfa0ac94d53bfe1d57b1948b2a02b1'
FF14_TAIL_SHA256 = 'aa53b17974f1d198dd41d60aae1eccd83b6a49d12fc238b0a39c8344f9deb699'
CN09_HISTORICAL_TAIL_SHA256 = 'f2f8f408349c30174c21e2d6ffc07adaf4c8ede6945539360d401172f147a1eb'
DECLARED_METHODS = ('test_ca205_01_current_pins_admit_at_exact_preimport_statements', 'test_ca205_02_missing_stale_mutated_foreign_bytes_and_symlinks_refuse', 'test_ca205_03_outer_inverse_precedes_unchanged_historical_endpoints', 'test_ca205_04_full_source_partial_displaced_suffix_and_type_mutations_refuse', 'test_ca205_05_exact_derivative_closure_keeps_original_before47_and_first30', 'test_ca205_06_existing_bodies_projection_prefix_and_complete_lf_fixture_stay_exact')


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def assignment(source, name):
    found = [n for n in ast.parse(source).body if isinstance(n, ast.Assign) and
             any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(found) != 1:
        raise AssertionError("An exact unique source declaration is required")
    return found[0]


def literal(source, name):
    return ast.literal_eval(assignment(source, name).value)


def function(source, name):
    found = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(found) != 1:
        raise AssertionError("An exact unique source function is required")
    return found[0]


class Camera205OwningAdmissionNewOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payloads = {}
        for relative, expected in EXPECTED_SHA256.items():
            path = TREE / relative
            if path.is_symlink() or not path.is_file():
                raise AssertionError("An exact ordinary Camera205 source input is required")
            payload = path.read_bytes()
            if not 0 < len(payload) <= 4 * 1024 * 1024 or digest(payload) != expected:
                raise AssertionError("An exact Camera205 source input hash is required")
            cls.payloads[relative] = payload
        cls.sources = {relative: payload.decode("utf-8") for relative, payload in cls.payloads.items()}

    def outer(self):
        names = {"CAMERA197_BEFORE_HELPER_SHA256", "CAMERA197_AFTER_HELPER_SHA256", "CAMERA197_SOURCE_BYTES",
                 "CAMERA197_OLD_CONDITION", "CAMERA197_NEW_CONDITION", "CAMERA197_APPEND_HELPER"}
        source = self.sources[PROJECTION]
        selected = [assignment(source, name) for name in sorted(names)] + [function(source, OUTER)]
        module = ast.Module(body=selected, type_ignores=[])
        self.assertFalse(any(isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef)) for n in ast.walk(module)))
        namespace = {"hashlib": hashlib, "__builtins__": {
            "str": str, "type": type, "len": len, "UnicodeError": UnicodeError, "AssertionError": AssertionError}}
        exec(compile(module, "<Camera205-new-outer-only>", "exec"), namespace)
        return namespace

    def boundary(self, relative, tree):
        source = self.sources[relative]
        prefix = ("if HELPER_PATH.is_symlink() or digest(HELPER_PATH)" if relative == SCALAR else
                  "for relative, expected in EXPECTED_INPUT_SHA256.items():")
        found = [n for n in ast.parse(source).body if isinstance(n, (ast.If, ast.For)) and
                 ast.get_source_segment(source, n).startswith(prefix)]
        self.assertEqual(len(found), 1)
        node = found[0]
        self.assertEqual(digest(ast.get_source_segment(source, node).encode()), IMPORT_BOUNDARY_SHA256[relative])
        namespace = {"TREE": tree, "HELPER_PATH": tree / HELPER,
                     "digest": lambda p: digest(p.read_bytes()), "__builtins__": {"AssertionError": AssertionError}}
        if relative == SCALAR:
            namespace["EXPECTED_HELPER_SHA256"] = literal(source, "EXPECTED_HELPER_SHA256")
            self.assertLess(node.lineno, assignment(source, "SPEC").lineno)
        else:
            namespace["EXPECTED_INPUT_SHA256"] = literal(source, "EXPECTED_INPUT_SHA256")
            self.assertLess(node.lineno, function(source, "_load_inert_fixture").lineno)
        exec(compile(ast.Module(body=[node], type_ignores=[]), "<Camera205-exact-preimport-boundary>", "exec"), namespace)

    def assert_closure(self, before, after, declared):
        self.assertEqual(digest(canonical(before)), BEFORE47_MAPPING_SHA256)
        self.assertEqual(len(before), 47)
        self.assertEqual(declared, DERIVATIVE_SHA256)
        self.assertEqual(set(after), set(before))
        self.assertEqual(after, {**before, HELPER: EXPECTED_SHA256[HELPER], **DERIVATIVE_SHA256})
        self.assertEqual({r for r in before if before[r] != after[r]}, {HELPER} | set(DERIVATIVE_SHA256))

    def test_ca205_01_current_pins_admit_at_exact_preimport_statements(self):
        self.assertEqual(literal(self.sources[SCALAR], "EXPECTED_HELPER_SHA256"), EXPECTED_SHA256[HELPER])
        inputs = literal(self.sources[FAILFAST], "EXPECTED_INPUT_SHA256")
        self.assertEqual(len(inputs), 7)
        self.assertEqual(inputs[HELPER], EXPECTED_SHA256[HELPER])
        self.assertEqual(inputs[PROJECTION], EXPECTED_SHA256[PROJECTION])
        for relative, expected in inputs.items():
            self.assertEqual(EXPECTED_SHA256[relative], expected)
        self.boundary(SCALAR, TREE)
        self.boundary(FAILFAST, TREE)

    def test_ca205_02_missing_stale_mutated_foreign_bytes_and_symlinks_refuse(self):
        namespace = self.outer()
        stale_helper = namespace[OUTER](self.sources[HELPER]).encode()
        for owner in (SCALAR, FAILFAST):
            inputs = {HELPER: EXPECTED_SHA256[HELPER]} if owner == SCALAR else literal(self.sources[FAILFAST], "EXPECTED_INPUT_SHA256")
            # At most seven owning inputs plus one synthetic symlink target; no ModelFixture or source-tree write.
            with tempfile.TemporaryDirectory(prefix="nativecmpkit-camera205-source-boundary-") as name:
                scratch = Path(name)
                self.assertFalse(scratch.is_relative_to(TREE) or TREE.is_relative_to(scratch))
                for relative in inputs:
                    path = scratch / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(self.payloads[relative])
                self.boundary(owner, scratch)
                for relative in inputs:
                    original = self.payloads[relative]
                    cases = [("missing", None), ("mutated", original + b"\n"), ("symlink", original)]
                    if relative == HELPER:
                        cases += [("stale-helper", stale_helper), ("foreign-bytes", b"# visibly synthetic foreign source\n")]
                    if relative == PROJECTION:
                        cases += [("stale-projection", original[:ORIGINAL_PROJECTION_BYTES])]
                    for label, payload in cases:
                        with self.subTest(owner=owner, source=relative, refusal=label):
                            path = scratch / relative
                            path.unlink()
                            if label == "symlink":
                                foreign = scratch / "same-byte-synthetic-source.py"
                                foreign.write_bytes(payload)
                                path.symlink_to(foreign)
                            elif payload is not None:
                                path.write_bytes(payload)
                            with self.assertRaises((AssertionError, OSError)):
                                self.boundary(owner, scratch)
                            if path.is_symlink() or path.exists():
                                path.unlink()
                            path.write_bytes(original)
                self.boundary(owner, scratch)

    def test_ca205_03_outer_inverse_precedes_unchanged_historical_endpoints(self):
        namespace = self.outer()
        current = namespace[OUTER](self.sources[HELPER])
        self.assertEqual(digest(current.encode()), namespace["CAMERA197_BEFORE_HELPER_SHA256"])
        self.assertEqual(current.replace(namespace["CAMERA197_OLD_CONDITION"], namespace["CAMERA197_NEW_CONDITION"], 6) +
                         namespace["CAMERA197_APPEND_HELPER"], self.sources[HELPER])
        ff = self.sources[FAILFAST]
        first = function(ff, FF14).body[0]
        expected = ast.parse("current = projection.camera197_helper_source_before_owned_console(HELPER_PATH.read_text())").body[0]
        self.assertEqual(ast.dump(first, include_attributes=False), ast.dump(expected, include_attributes=False))
        self.assertEqual({n: literal(ff, n) for n in HISTORICAL_SHA256}, HISTORICAL_SHA256)
        startup = json.loads(self.payloads["scripts/ci/fixtures/android-camera-startup-readiness-inverse.json"])
        self.assertEqual(len(startup["inverse_fragments"]), 17)
        for fragments, endpoint in ((startup["inverse_fragments"][:11], "FROZEN_HELPER_SHA256"),
                                    (startup["inverse_fragments"][11:], "PRE_STARTUP_HELPER_SHA256")):
            for fragment in fragments:
                self.assertEqual(current.count(fragment["new"]), 1)
                current = current.replace(fragment["new"], fragment["old"], 1)
            self.assertEqual(digest(current.encode()), HISTORICAL_SHA256[endpoint])
        observation = json.loads(self.payloads["scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json"])
        for fragment in observation["inverse_fragments"]:
            self.assertEqual(current.count(fragment["new"]), 1)
            current = current.replace(fragment["new"], fragment["old"], 1)
        self.assertEqual(digest(current.encode()), HISTORICAL_SHA256["HISTORICAL_HELPER_SHA256"])

    def test_ca205_04_full_source_partial_displaced_suffix_and_type_mutations_refuse(self):
        namespace = self.outer()
        project = namespace[OUTER]
        source = self.sources[HELPER]
        old, new, suffix = (namespace[n] for n in ("CAMERA197_OLD_CONDITION", "CAMERA197_NEW_CONDITION", "CAMERA197_APPEND_HELPER"))
        before = project(source)
        guarded = new + '                "Actual AVD ownership changed before action")\n'
        uid = ('        require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000",\n'
               '                "Shell UID changed before action; never mutate as root")\n')
        self.assertEqual(source.count(guarded + uid), 1)
        displaced = source.replace(guarded + uid, uid + guarded, 1)
        self.assertEqual(displaced.count(new), 6)
        self.assertTrue(displaced.endswith(suffix))
        relaxed = source.replace('require(self.original is not None, "Original exact state was not acquired")',
                                 'require(True, "Original exact state was not acquired")', 1)
        cases = (before, source.removesuffix(suffix), source + suffix, source.replace(new, old, 1),
                 source.replace(new, "", 1), displaced, relaxed, source + "\n", source[:-1] + " \n",
                 None, source.encode(), type("SyntheticSourceSubclass", (str,), {})(source),
                 "x" * (namespace["CAMERA197_SOURCE_BYTES"] + 1), source + "\ud800")
        for index, candidate in enumerate(cases):
            with self.subTest(source_contract_case=index):
                self.assertTrue(type(candidate) is not str or candidate != source)
                with self.assertRaises(AssertionError):
                    project(candidate)

    def test_ca205_05_exact_derivative_closure_keeps_original_before47_and_first30(self):
        console = self.sources[CONSOLE]
        before, after, declared = (literal(console, n) for n in
                                  ("BOUND_SOURCE_BEFORE47", "BOUND_SOURCE_AFTER47", "CAMERA205_DERIVATIVE_SOURCE_SHA256"))
        self.assert_closure(before, after, declared)
        self.assertEqual(digest(ast.get_source_segment(console, assignment(console, "BOUND_SOURCE_BEFORE47")).encode()),
                         BEFORE47_ASSIGNMENT_SHA256)
        old_pins = literal(self.sources[DRIVER], "EXPECTED_SOURCE_SHA256")  # Data only; driver remains inert.
        self.assertEqual(len(old_pins), 46)
        self.assertEqual(old_pins[HELPER], literal(console, "BEFORE_HELPER_SHA256"))
        self.assertTrue(all(before[r] == expected for r, expected in old_pins.items()))
        missing = dict(declared); missing.pop(PROJECTION)
        extra = {**declared, "scripts/ci/camera205-foreign.py": "0" * 64}
        foreign = dict(declared); foreign["scripts/ci/camera205-foreign.py"] = foreign.pop(PROJECTION)
        changed = {**declared, PROJECTION: "0" * 64}
        absent_after = dict(after); absent_after.pop(PROJECTION)
        cases = ((before, after, missing), (before, after, extra), (before, after, foreign),
                 (before, after, changed), (before, {**after, PROJECTION: before[PROJECTION]}, declared),
                 (before, absent_after, declared), (before, {**after, ".github/workflows/gradle.yml": "0" * 64}, declared),
                 ({**before, HELPER: EXPECTED_SHA256[HELPER]}, after, declared))
        for index, candidate in enumerate(cases):
            with self.subTest(closure_contract_case=index):
                with self.assertRaises(AssertionError):
                    self.assert_closure(*candidate)

    def test_ca205_06_existing_bodies_projection_prefix_and_complete_lf_fixture_stay_exact(self):
        self.assertEqual(digest(self.payloads[PROJECTION][:ORIGINAL_PROJECTION_BYTES]), ORIGINAL_PROJECTION_SHA256)
        for relative, contract in UNCHANGED_METHOD_BUNDLES.items():
            source = self.sources[relative]
            values = {cls.name + "." + n.name: ast.get_source_segment(source, n)
                      for cls in ast.parse(source).body if isinstance(cls, ast.ClassDef) for n in cls.body
                      if isinstance(n, ast.FunctionDef) and n.name.startswith("test_") and n.name not in contract["omitted"]}
            self.assertEqual(len(values), contract["methods"])
            self.assertEqual(digest(canonical(values)), contract["sha256"])
        ff = self.sources[FAILFAST]; node = function(ff, FF14)
        tail = "".join(ff.splitlines(keepends=True)[node.body[1].lineno - 1:node.end_lineno])
        self.assertEqual(digest(tail.encode()), FF14_TAIL_SHA256)
        cn = self.sources[CONSOLE]
        method = ast.get_source_segment(cn, function(cn, CN09))
        anchor = '        for relative in ("scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py",\n'
        self.assertEqual(method.count(anchor), 1)
        self.assertEqual(digest(method[method.index(anchor):].encode()), CN09_HISTORICAL_TAIL_SHA256)
        self.assertIn('return cp((self.guest.name + "\\nOK\\n").encode())', self.sources[FIXTURE])


if __name__ == "__main__":
    unittest.main()
