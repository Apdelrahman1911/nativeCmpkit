# SPDX-License-Identifier: Apache-2.0
"""NEW offline-reader regression controls; zero Gradle or native executions.

Old checks retain their hashes, section comparisons and refusal predicates.
Only exact current bytes can enter the existing policy-stage inverse. The live
native selector still reads the current Kotlin/init sources without projection.
"""
import hashlib
import unittest
from unittest.mock import patch

import desktop_policy_creation_source_projection as history
import desktop_security_plan as security
import library_tests as library
import test_desktop_security_owned_root as owned
import test_webview_identity_recovery as identity


class DesktopPolicyHistoryReaderControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = library.snapshot_inputs(library.ROOT)

    @classmethod
    def tearDownClass(cls):
        if library.snapshot_inputs(library.ROOT) != cls.inputs:
            raise AssertionError("Source inputs changed during NEW history-reader controls")

    def test_owned_init_reader_restores_only_exact_policy_history_and_keeps_all_refusals(self):
        relative = str(owned.SCRIPT.relative_to(owned.ROOT))
        current = owned.SCRIPT.read_bytes()
        previous = history.current_source_before_policy_creation(relative, current)
        self.assertEqual(previous.decode(), owned.current_owned_script_for_history())
        inner = owned.exact_owned_inner(previous.decode())
        self.assertEqual(owned.ORIGINAL_INNER_SHA256, hashlib.sha256(inner.encode()).hexdigest())
        self.assertIn('check(maxParallelForks == 1 && forkEvery == 1L)', inner)
        with self.assertRaises(ValueError):
            owned.exact_owned_inner(current.decode())  # Never rewrite the old checksum.
        ordinary_read = type(owned.SCRIPT).read_bytes
        for bad in (previous, current[:-1], current + b"\n", b"foreign", b""):
            def substituted(file):
                return bad if file == owned.SCRIPT else ordinary_read(file)
            with self.subTest(bytes=len(bad)), patch.object(type(owned.SCRIPT), "read_bytes", autospec=True, side_effect=substituted), self.assertRaisesRegex(ValueError, "historical image"):
                owned.current_owned_script_for_history()
        for old, new in (('rootProject.name == "NativeCmpKit"', 'true'),
                         ('forkEvery == 1L', 'forkEvery >= 1L'),
                         ('maxParallelForks == 1', 'maxParallelForks >= 1')):
            with self.subTest(criterion=old), self.assertRaises(ValueError):
                owned.exact_owned_inner(previous.decode().replace(old, new, 1))

    def test_identity_reader_reverses_exact_desktop_addition_only_and_live_selector_is_current(self):
        relative = security.SOURCE_PATHS["policy"]
        current = (library.ROOT / relative).read_bytes()
        previous = history.current_source_before_policy_creation(relative, current)
        self.assertEqual(previous.decode(), identity.current_identity_source_for_history('desktop', relative))
        self.assertNotIn('host.awaitCreation(owner)', previous.decode())
        self.assertIn('host.awaitCreation(owner)', current.decode())
        ordinary_read = type(library.ROOT).read_bytes
        target = library.ROOT / relative
        for bad in (previous, current[:-1], current + b"\n", b"foreign", b""):
            def substituted(file):
                return bad if file == target else ordinary_read(file)
            with self.subTest(bytes=len(bad)), patch.object(type(library.ROOT), "read_bytes", autospec=True, side_effect=substituted), self.assertRaisesRegex(ValueError, "historical image"):
                identity.current_identity_source_for_history('desktop', relative)
        for suite in ('android-device', 'js'):
            path = library.WEBVIEW_IDENTITY_SPECS[suite]['source']
            self.assertEqual((library.ROOT / path).read_bytes().decode(),
                             identity.current_identity_source_for_history(suite, path))
        self.assertEqual(hashlib.sha256(current).hexdigest(), security.SOURCE_SHA256[relative])
        contract = security.fixture_contract(library.ROOT, security.POLICY_RECOVERY_FOCUS)
        self.assertTrue(contract)
        self.assertEqual(current, (library.ROOT / relative).read_bytes())


if __name__ == '__main__':
    unittest.main()
