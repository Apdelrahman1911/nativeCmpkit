"""Regression controls for CI213's exact camera source-history admission.

No native commands, model fixtures, historical test classes or accepted test
methods are imported or replayed. The current closure prefix and the closure
assertion utility are selected from their pinned source into inert namespaces.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

if __package__:
    from . import camera_ci213_source_projection as projection
else:
    import camera_ci213_source_projection as projection


ROOT = Path(__file__).resolve().parents[2]
PROJECTION = "scripts/ci/camera_ci213_source_projection.py"
CONSOLE = "scripts/ci/test_android_camera_owned_avd_console_name.py"
OWNING = "scripts/ci/test_android_camera205_owning_admission.py"
EXPECTED = {
    PROJECTION: "060376f53d3beaff8ad48941fa998fe3917403b46be750e08dbd25c1375aa60b",
    CONSOLE: "71709ee20947d4f97df38a75c4c591bf12db319f327840b51440c07c3e2c0f33",
    OWNING: "172f39bf8c9af2a7827107bb64a0184cf8f14bf26e9913218dda37e16151b81d",
    "scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py":
        "048b40f6976fc6af2160c9934b39d620bbdac466d912edfbb9e315dfa92f8bf7",
    "scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py":
        "9c2ee35603ccc5c30a49fd91d438fa88584386637bb550ab2557d44760d1bbe5",
    "scripts/ci/test_android_camera_startup_readiness.py":
        "239bbde00bd8deb728119aa2d76395f4e01615ab25092a3fe2a6dd57f8a274bf",
}
# Exact terminal/AWT240 metadata derivatives; the original EXPECTED literal and
# all five method bodies remain historical and byte-identical. No live hash is
# computed into this allowlist and the actual current bytes still require it.
CURRENT_TERMINAL_AWT240_SOURCE_SHA256 = {
    CONSOLE: "623fc7d14b47e048f0060836a726a662fa57678e9104b2191990bda0f3637952",
    OWNING: "cbb64e0e7c79b120919b7be0e9511ba317d9bdd59ef96e883b2c2fc6c594d9cb",
}
EXPECTED.update(CURRENT_TERMINAL_AWT240_SOURCE_SHA256)
HISTORICAL_TAIL = "f2f8f408349c30174c21e2d6ffc07adaf4c8ede6945539360d401172f147a1eb"
OWNING_METHODS = "aa32d21b11bdfd92b0e866ddc2aef31d7d2162a352756b6c02179aadeb444f74"


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def literal(source, name):
    matches = [n for n in ast.parse(source).body if isinstance(n, ast.Assign) and
               any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(matches) != 1:
        raise AssertionError("An exact unique source declaration is required")
    return ast.literal_eval(matches[0].value)


def function(source, name):
    matches = [n for n in ast.walk(ast.parse(source))
               if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1:
        raise AssertionError("An exact unique source function is required")
    return matches[0]


class CameraCI213ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payloads = {}
        for relative, expected in EXPECTED.items():
            path = ROOT / relative
            if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
                raise AssertionError("An ordinary owning source input is required")
            from android_external328_source_projection import current_source_for_history
            try:
                payload = current_source_for_history(relative, path.read_bytes())
            except ValueError as error:
                raise AssertionError("An exact bounded owning source input is required") from error
            if not 0 < len(payload) <= 4 * 1024 * 1024 or digest(payload) != expected:
                raise AssertionError("An exact bounded owning source input is required")
            cls.payloads[relative] = payload
        cls.sources = {r: b.decode("utf-8") for r, b in cls.payloads.items()}

    @classmethod
    def tearDownClass(cls):
        from android_external328_source_projection import read_current_source_for_history
        try:
            changed = any(read_current_source_for_history(ROOT / r, ROOT) != b for r, b in cls.payloads.items())
        except ValueError as error:
            raise AssertionError("The owning source changed during these controls") from error
        if changed:
            raise AssertionError("The owning source changed during these controls")

    def test_ci213_01_three_exact_inverses_retain_all_historical_method_bodies(self):
        self.assertEqual(set(projection.REPAIRS), set(EXPECTED) - {PROJECTION, CONSOLE, OWNING})
        for relative, binding in projection.REPAIRS.items():
            with self.subTest(relative=relative):
                payload = self.payloads[relative]
                restored = projection.historical_source_before_camera213(relative, payload)
                self.assertEqual(digest(restored), binding["before_sha256"])
                self.assertNotEqual(restored, payload)
                before, after = (ast.parse(s) for s in (restored, payload))
                test_bodies = lambda tree: {
                    c.name + "." + n.name: ast.dump(n, include_attributes=False)
                    for c in tree.body if isinstance(c, ast.ClassDef)
                    for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                }
                self.assertEqual(test_bodies(before), test_bodies(after))
                for fragment in binding["fragments"]:
                    old, new = fragment["before"].encode(), fragment["after"].encode()
                    self.assertEqual(restored.count(old), 1)
                    restored = restored.replace(old, new, 1)
                self.assertEqual(restored, payload)

    def test_ci213_02_identity_types_bounds_old_and_mutated_sources_refuse(self):
        for relative in projection.REPAIRS:
            payload = self.payloads[relative]
            old = projection.historical_source_before_camera213(relative, payload)
            bad_payloads = (None, payload.decode(), bytearray(payload), b"", old,
                            payload + b"\n", payload[:-1], b"x" * (4 * 1024 * 1024 + 1),
                            type("SyntheticBytes", (bytes,), {})(payload))
            for candidate in bad_payloads:
                with self.subTest(relative=relative, candidate_type=type(candidate).__name__):
                    with self.assertRaises(ValueError):
                        projection.historical_source_before_camera213(relative, candidate)
            for identity in (None, Path(relative), relative + ".foreign", "../" + relative):
                with self.assertRaises(ValueError):
                    projection.historical_source_before_camera213(identity, payload)

    def test_ci213_03_missing_ambiguous_and_corrupted_inverse_contracts_refuse(self):
        # Controlled contract mutations are confined to memory; never rewrite source.
        for relative, binding in projection.REPAIRS.items():
            payload = self.payloads[relative]
            changed = copy.deepcopy(binding)
            changed["fragments"][0]["after"] = "# visibly synthetic missing fragment\n"
            bad_history = copy.deepcopy(binding)
            bad_history["before_sha256"] = "0" * 64
            duplicate = payload + binding["fragments"][0]["after"].encode()
            ambiguous = copy.deepcopy(binding)
            ambiguous["after_sha256"] = digest(duplicate)
            for contract, candidate in ((changed, payload), (bad_history, payload), (ambiguous, duplicate)):
                with patch.dict(projection.REPAIRS, {relative: contract}):
                    with self.assertRaises(ValueError):
                        projection.historical_source_before_camera213(relative, candidate)
            self.assertEqual(projection.REPAIRS[relative], binding)

    def test_ci213_04_owning_closure_admits_only_current_derivatives_and_keeps_six_bodies(self):
        console, owning = self.sources[CONSOLE], self.sources[OWNING]
        before, after = (literal(console, n) for n in ("BOUND_SOURCE_BEFORE47", "BOUND_SOURCE_AFTER47"))
        current = {r: EXPECTED[r] for r in projection.REPAIRS}
        self.assertEqual(literal(console, "CAMERA213_DERIVATIVE_SOURCE_SHA256"), current)
        self.assertEqual(literal(owning, "CAMERA213_DERIVATIVE_SOURCE_SHA256"), current)
        constants = {n: literal(owning, n) for n in (
            "DERIVATIVE_SHA256", "EXPECTED_SHA256", "CAMERA205_SHARE188_SHARED_SOURCE_SHA256",
            "CAMERA213_DERIVATIVE_SOURCE_SHA256", "CAMERA224_DERIVATIVE_SOURCE_SHA256",
            "BEFORE47_MAPPING_SHA256", "HELPER", "FAILFAST")}
        utility = function(owning, "assert_closure")
        namespace = {**constants, "digest": digest,
                     "canonical": lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")).encode()}
        exec(compile(ast.Module(body=[utility], type_ignores=[]), "<ci213-owning-closure-utility-only>", "exec"), namespace)
        declared = literal(console, "CAMERA205_DERIVATIVE_SOURCE_SHA256")
        namespace["assert_closure"](self, before, after, declared)
        for relative in current:
            stale = {**after, relative: before[relative]}
            missing = dict(after); missing.pop(relative)
            for candidate in (stale, missing, {**after, relative: "0" * 64}):
                with self.assertRaises(AssertionError):
                    namespace["assert_closure"](self, before, candidate, declared)
        methods = {c.name + "." + n.name: ast.get_source_segment(owning, n)
                   for c in ast.parse(owning).body if isinstance(c, ast.ClassDef)
                   for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
        self.assertEqual(len(methods), 6)
        self.assertEqual(digest(json.dumps(methods, sort_keys=True, separators=(",", ":")).encode()), OWNING_METHODS)

    def test_ci213_05_current_closure_has_instance_local_history_and_exact_original_tail(self):
        source = self.sources[CONSOLE]
        method = function(source, "test_cn09_owning194_and_operational_native_bindings_are_not_rebased")
        anchor = '        for relative in ("scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py",\n'
        raw = ast.get_source_segment(source, method)
        self.assertEqual(raw.count(anchor), 1)
        self.assertEqual(digest(raw[raw.index(anchor):].encode()), HISTORICAL_TAIL)
        prefix = []
        for statement in method.body:
            if isinstance(statement, ast.For):
                break
            prefix.append(statement)
        self.assertTrue(prefix and isinstance(prefix[-1], ast.Expr))
        pins = literal(source, "BOUND_SOURCE_AFTER47")
        from android_external328_source_projection import read_current_source_for_history
        payloads = {r: read_current_source_for_history(ROOT / r, ROOT) for r in pins}
        self.assertEqual({r: digest(b) for r, b in payloads.items()}, pins)
        # The unchanged historical tail is hashed above, not executed again.
        holder_type = type("CI213CurrentClosureOnly", (unittest.TestCase,), {"source_payloads": payloads})
        holder = holder_type()
        names = ("BOUND_SOURCE_BEFORE47", "BOUND_SOURCE_AFTER47", "CAMERA205_DERIVATIVE_SOURCE_SHA256",
                 "CAMERA205_SHARE188_SHARED_SOURCE_SHA256", "CAMERA213_DERIVATIVE_SOURCE_SHA256",
                 "CAMERA224_DERIVATIVE_SOURCE_SHA256", "HELPER_RELATIVE_PATH")
        namespace = {n: literal(source, n) for n in names}
        namespace["self"] = holder
        try:
            exec(compile(ast.Module(body=prefix, type_ignores=[]), "<ci213-current-closure-prefix-only>", "exec"), namespace)
            self.assertIsNot(holder.source_payloads, payloads)
            for relative, binding in projection.REPAIRS.items():
                self.assertEqual(digest(holder.source_payloads[relative]), binding["before_sha256"])
            self.assertIs(holder_type.source_payloads, payloads)
            self.assertEqual({r: digest(b) for r, b in payloads.items()}, pins)
        finally:
            self.assertTrue(holder.doCleanups())
        self.assertNotIn("source_payloads", holder.__dict__)
        self.assertIs(holder.source_payloads, payloads)


if __name__ == "__main__":
    unittest.main()
