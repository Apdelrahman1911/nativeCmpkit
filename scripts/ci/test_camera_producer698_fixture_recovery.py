# SPDX-License-Identifier: Apache-2.0
"""NEW exact Camera fixture regressions only; no controller, compiler or native work."""
import ast
import copy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import ios_ui_application as application
import ios_ui_split664_source_projection as split
import camera_ios_ownership_native_focus as camera
import camera_home_affinity_source_projection as affinity
import camera_scalar_failfast_source_projection as scalar
import test_camera_ios_ownership_application_routing as routing
import test_camera_tooling566_source_projection as tooling

ROOT = Path(__file__).resolve().parents[2]
APP = "scripts/ci/ios_ui_application.py"
HOME = "scripts/ci/android_camera_developer_prerequisite.py"
RECENTS = "scripts/ci/camera_recents_fixture_source_projection.py"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(raw):
    return {node.name: node for node in ast.parse(raw).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


class CameraProducer698FixtureRecoveryControls(unittest.TestCase):
    def test_exact_ui664_predecessor_preserves_camera_deadline_and_nine_untouched_helpers(self):
        raw = (ROOT / APP).read_bytes()
        import macos_share_ci668_composition as latest
        # This old UI664 AFTER pin owns the named producer190 source image.
        named_producer190 = latest.current_source_in_view(APP, raw, latest.PRODUCER_VIEW, ROOT)
        qualified = split.current_source_before_ui_split664(APP, raw)
        self.assertEqual("b3d0f2c2986e42a5e662ba8c2521393f7564916e27084b9473c354b7328b9605", sha(named_producer190))
        self.assertEqual("b3fb8e7a88c19c10ac0e8f8af674c7228f59d3c7c80269e3078ef97258a0d52c", sha(qualified))
        now, old = functions(raw), functions(qualified)
        for name in ("NativeProtocol", "execute_control", "control_status", "installed_identity", "stopped_app",
                     "forward_application", "macho_simulator_identity", "profile_debug_entitlements", "provider_c3_observation_route"):
            self.assertEqual(ast.dump(now[name], include_attributes=False), ast.dump(old[name], include_attributes=False), name)
        self.assertNotEqual(ast.dump(now["application_timeout_seconds"], include_attributes=False),
                            ast.dump(old["application_timeout_seconds"], include_attributes=False))
        self.assertEqual(1920, application.application_timeout_seconds(camera.FOCUS))
        self.assertEqual(1920, application.APP_TIMEOUT_SECONDS)
        self.assertEqual(300, application.SLIDER_TIMEOUT_SECONDS)

    def test_ui664_current_ingress_refuses_older_partial_or_deadline_and_split_wiring_mutation(self):
        raw = (ROOT / APP).read_bytes()
        older = split.source_before_ui_split664(APP, raw)
        for bad in (older, raw[:-1], raw + b"\n", b"", bytearray(raw),
                    raw.replace(b"APP_TIMEOUT_SECONDS = 1920", b"APP_TIMEOUT_SECONDS = 1921", 1),
                    raw.replace(b"lt.ui_related.SPLIT_FOCUSES", b"lt.ui_related.ALL_FOCUSES", 1)):
            self.assertTrue(type(bad) is not bytes or raw != bad)
            with self.assertRaises(ValueError):
                split.current_source_before_ui_split664(APP, bad)

    def test_exact_recents_wrapper_reaches_only_the_named_ancestor_helper(self):
        source = (ROOT / RECENTS).read_text()
        node = tooling.qualified_nested_reader(source, "current_source_before_recents_fixture")
        self.assertEqual("recents_fixture_after_qualified_outer_ingress", node.name)
        calls = {n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("peel_current_tooling566_for_older_history", calls)
        self.assertIn("peel_current_tooling_for_older_history", calls)
        self.assertIn("peel_current_boot_busy_for_older_history", calls)
        self.assertNotIn("current_source_before_tooling566", calls)
        self.assertNotIn("current_source_before_tooling", calls)
        self.assertNotIn("current_source_before_platform_recovery659", calls)
        wrapper = functions(source)["current_source_before_recents_fixture"]
        invocations = [ast.unparse(n.func) for n in ast.walk(wrapper) if isinstance(n, ast.Call)]
        self.assertEqual(1, invocations.count("current_source_before_platform_recovery659"))
        self.assertEqual(1, invocations.count("recents_fixture_after_qualified_outer_ingress"))

    def test_recents_wrapper_refuses_removed_outer_admission_wrong_hop_or_reversed_composition(self):
        source = (ROOT / RECENTS).read_text()
        exact = functions(source)["current_source_before_recents_fixture"]
        for mode in ("missing_outer", "wrong_hop", "raw_return", "wrong_outer", "extra_raw_readmission"):
            document = ast.parse(source)
            wrapper = next(n for n in document.body if isinstance(n, ast.FunctionDef) and n.name == exact.name)
            if mode == "missing_outer":
                wrapper.body = [n for n in wrapper.body if not isinstance(n, ast.Assign)]
            elif mode == "wrong_hop":
                wrapper.body[-1].value.func.id = "source_before_recents_fixture"
            elif mode == "raw_return":
                wrapper.body[-1].value = ast.Name(id="payload", ctx=ast.Load())
            elif mode == "wrong_outer":
                next(n for n in ast.walk(wrapper) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and
                     n.func.id == "current_source_before_platform_recovery659").func.id = "peel_platform_recovery659_for_history"
            else:
                wrapper.body.insert(-1, copy.deepcopy(next(n for n in wrapper.body if isinstance(n, ast.Assign))))
            mutated = ast.unparse(ast.fix_missing_locations(document))
            with self.assertRaises(ValueError):
                tooling.qualified_nested_reader(mutated, exact.name)

    def test_current_home_is_admitted_once_before_original_camera197_hash_and_inverse(self):
        raw = (ROOT / HOME).read_bytes()
        with patch.object(affinity, "current_source_before_home_affinity", wraps=affinity.current_source_before_home_affinity) as newest:
            stage = affinity.current_source_before_home_affinity(HOME, raw)
            newest.assert_called_once_with(HOME, raw)
        self.assertEqual("c61d385634dddc3aac39ce8346f93f2fcd4f7e4df6330ba81528247fba2f5800", sha(raw))
        self.assertEqual("92f8d79d3a0871f1abb619a0a17b36c87568e11151fb3dbefa4f12773de78bdb", sha(stage))
        prior = scalar.camera197_helper_source_before_owned_console(stage.decode())
        self.assertEqual("da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4", sha(prior.encode()))
        self.assertNotIn("parse_recent_home_baseline", prior)
        self.assertEqual("0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26", scalar.CAMERA197_AFTER_HELPER_SHA256)
        self.assertEqual("da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4", scalar.CAMERA197_BEFORE_HELPER_SHA256)

    def test_current_home_unknown_or_older_bytes_never_replace_exact_camera197_admission(self):
        raw = (ROOT / HOME).read_bytes()
        stage = affinity.current_source_before_home_affinity(HOME, raw)
        for bad in (stage, raw[:-1], raw + b"\n", b"", bytearray(raw),
                    raw.replace(b"action_boot = self.boot_id()", b"action_boot = 'foreign'", 1)):
            self.assertTrue(type(bad) is not bytes or raw != bad)
            with self.assertRaises(ValueError):
                affinity.current_source_before_home_affinity(HOME, bad)
        for bad in (stage.decode() + "\n", stage.decode().replace("action_boot = self.boot_id()", "action_boot = 'foreign'", 1)):
            self.assertNotEqual(stage.decode(), bad)
            with self.assertRaises(AssertionError):
                scalar.camera197_helper_source_before_owned_console(bad)


if __name__ == "__main__":
    unittest.main()
