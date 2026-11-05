# SPDX-License-Identifier: Apache-2.0
"""NEW exact Content-owner/Cookie source control; no accepted population replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ci_source_domain740 as domain
import ci_source_recovery740_742 as recovery
import cookie_ci668_outer_source_projection as cookie
import macos_share_ci668_composition as joint

ROOT = Path(__file__).resolve().parents[2]
CONTENT = 'scripts/ci/webview_content_policy_source_projection.py'
NEW_CONTROL = 'scripts/ci/test_cookie_content_owner_successor740.py'
CONTENT_ORIGINAL = ('ad544703072bd892274a08b29304f313d1915d8c24840f6d136474ea1e560253', 14440)
CONTENT_R5 = ('d20c4d3e7dd229c29d738ce0f49eb1f29d2c815d8463186db95316e99a67addf', 15891)
COOKIE_ORIGINAL = ('0164dd126040791c6e591965562aca7710fbcafed67677968907c49abc3215ff', 22579)
COOKIE_SPEC_ORIGINAL = ('5fc3e645636f9ab3109933fb9bfa5c8abf243b9ea8d9804d73ce3179fcabb14f', 65107)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


class CookieContentOwnerSuccessor740Controls(unittest.TestCase):
    def test01_exact_content_owner_successor_preserves_cookie40_pins_and_strict_refusals(self):
        document, source_digest = cookie._document(ROOT)
        core = recovery._document(ROOT)
        self.assertEqual(38, len(recovery.MODIFIED - recovery.FIXTURE_SUCCESSORS742 - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(51, len(recovery.dependency_inputs() - recovery.FIXTURE_SUCCESSORS742 - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(41, len(recovery.MODIFIED - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(54, len(recovery.dependency_inputs() - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(42, len(recovery.MODIFIED - {"scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(55, len(recovery.dependency_inputs() - {"scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(43, len(recovery.MODIFIED))
        self.assertEqual(56, len(recovery.dependency_inputs()))
        self.assertEqual(303, len(joint.fixture_inputs(ROOT)))
        self.assertNotIn(NEW_CONTROL, recovery.dependency_inputs())
        self.assertNotIn(NEW_CONTROL, joint.fixture_inputs(ROOT))
        content_binding = core['bindings'][CONTENT]
        self.assertEqual(CONTENT_ORIGINAL,
                         (content_binding['before_sha256'], content_binding['before_bytes']))
        self.assertEqual(5, len(content_binding['fragments']))
        raw = cookie.ordinary_bytes(ROOT, CONTENT)
        self.assertEqual((sha(raw), len(raw)),
                         (content_binding['after_sha256'], content_binding['after_bytes']))
        original = recovery.current_source_before_recovery(CONTENT, raw, ROOT)
        self.assertEqual(CONTENT_ORIGINAL, (sha(original), len(original)))
        branch = content_binding['fragments'][-1]
        self.assertEqual(1, raw.count(branch['after'].encode()))
        r5 = raw.replace(branch['after'].encode(), branch['before'].encode(), 1)
        # R5 is immutable source DATA; exact later deltas are not its old pin.
        historical_deltas = (
            (b'    from tooling_recovery671_source_projection import current_source_before_tooling671\n    payload = current_source_before_tooling671(relative, payload)\n', b""),
            (b'def _appkit_key_wait_source(relative, payload, *, current):\n    """Only three exact successors restore their unchanged Content/Share pins.\n\n    Current uses the original strict owning ingress. History peels only its exact\n    reviewed afterimage; old/unknown/unlisted data is not a current certificate.\n    Every other key-wait path, native criterion, manifest pin and fixture stays exact.\n    """\n    _identity(relative, payload)\n    if type(current) is not bool:\n        raise ValueError("An exact AppKit content-boundary source mode is required")\n    if relative not in (\n        "calf-share/native/tests/appkit_lifecycle/cases.rs",\n        "scripts/ci/macos_share_appkit_lifecycle.py",\n        "scripts/ci/test_macos_share_missing_only.py",\n    ):\n        return payload  # Unlisted source data remains uncertified.\n    import macos_share_key_wait_observation as key_wait\n    binding = key_wait._document()["bindings"][relative]\n    if _document()["unchanged_inputs"].get(relative) != binding["before_sha256"]:\n        raise ValueError("AppKit key-wait must restore the unchanged original Content/Share source pin")\n    if current:\n        return key_wait.current_source_before_key_wait(relative, payload)\n    return key_wait.peel_key_wait_for_history(relative, payload)', b'def _appkit_key_wait_source(relative, payload, *, current):\n    """Only the exact cases successor crosses the unchanged Content/Share pin.\n\n    Current uses the original strict owning ingress. History peels only its exact\n    reviewed afterimage; old/unknown/unlisted data is not a current certificate.\n    No other key-wait path, native criterion, manifest pin or fixture is widened.\n    """\n    _identity(relative, payload)\n    if type(current) is not bool:\n        raise ValueError("An exact AppKit content-boundary source mode is required")\n    if relative != "calf-share/native/tests/appkit_lifecycle/cases.rs":\n        return payload  # Unlisted source data remains uncertified.\n    import macos_share_key_wait_observation as key_wait\n    binding = key_wait._document()["bindings"][relative]\n    if _document()["unchanged_inputs"].get(relative) != binding["before_sha256"]:\n        raise ValueError("AppKit key-wait must restore the unchanged original Content/Share source pin")\n    if current:\n        return key_wait.current_source_before_key_wait(relative, payload)\n    return key_wait.peel_key_wait_for_history(relative, payload)'),
        )
        for after, before in historical_deltas:
            self.assertEqual(1, r5.count(after))
            r5 = r5.replace(after, before, 1)
        self.assertEqual(CONTENT_R5, (sha(r5), len(r5)))

        # Exact Cookie owner and own-template manifest derivatives are separate
        # common inverses. Their original endpoints and all old rows remain held.
        old_documents = {}
        for relative, endpoint in ((cookie.SOURCE_RELATIVE, COOKIE_ORIGINAL),
                                   (cookie.SPEC_RELATIVE, COOKIE_SPEC_ORIGINAL)):
            binding = core['bindings'][relative]
            self.assertEqual(endpoint, (binding['before_sha256'], binding['before_bytes']))
            current = cookie.ordinary_bytes(ROOT, relative)
            previous = recovery.current_source_before_recovery(relative, current, ROOT)
            self.assertEqual(endpoint, (sha(previous), len(previous)))
            self.assertEqual(previous, recovery.peel_recovery_for_history(relative, current, ROOT))
            for bad in (previous, current[:-1], current + b'\n', b'', None,
                        bytearray(current), current.decode()):
                with self.subTest(relative=relative, kind=type(bad).__name__), self.assertRaises(ValueError):
                    recovery.current_source_before_recovery(relative, bad, ROOT)
            if relative == cookie.SPEC_RELATIVE:
                old_documents[relative] = json.loads(previous)
        old_document = old_documents[cookie.SPEC_RELATIVE]
        self.assertEqual(set(old_document), set(document))
        for field in set(document) - {'own_guard'}:
            self.assertEqual(old_document[field], document[field], field)
        original_cookie_row = document['bindings'][CONTENT]
        self.assertEqual(CONTENT_ORIGINAL,
                         (original_cookie_row['after_sha256'], original_cookie_row['after_bytes']))
        self.assertEqual(4, len(original_cookie_row['fragments']))

        # Strict raw Content ingress occurs once at the existing740 seam. The
        # returned source is its original Cookie predecessor, not new admission.
        with patch.object(domain, 'current_source_before_domain740',
                          wraps=domain.current_source_before_domain740) as strict:
            cookie_previous = cookie.current_source_before_cookie_outer(CONTENT, raw, ROOT)
            strict.assert_called_once_with(CONTENT, raw, ROOT)
        self.assertEqual((original_cookie_row['before_sha256'], original_cookie_row['before_bytes']),
                         (sha(cookie_previous), len(cookie_previous)))
        self.assertEqual(cookie_previous, cookie.source_before_cookie_outer(CONTENT, raw, ROOT))
        self.assertEqual(cookie_previous, cookie.peel_cookie_outer_for_history(CONTENT, raw, ROOT))
        unknown = raw + b'\n# unqualified current Content owner\n'
        for historical in (original, r5, unknown):
            self.assertIs(historical, cookie._content_owner_source(CONTENT, historical, ROOT, current=False))
        displaced = raw.replace(branch['after'].encode(), b'', 1) + branch['after'].encode()
        self.assertNotEqual(raw, displaced)
        for bad in (original, r5, cookie_previous, raw[:-1], raw + b'\n', displaced,
                    b'', None, bytearray(raw), raw.decode(), b'x' * (cookie.MAX_SOURCE_BYTES + 1)):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(ValueError):
                cookie.current_source_before_cookie_outer(CONTENT, bad, ROOT)
        with self.assertRaises(ValueError):
            cookie.source_before_cookie_outer(CONTENT, unknown, ROOT)
        self.assertIs(unknown, cookie.peel_cookie_outer_for_history(CONTENT, unknown, ROOT))
        for identity in (Path(CONTENT), None, [], 1):
            with self.subTest(identity=type(identity).__name__), self.assertRaises(ValueError):
                cookie._content_owner_source(identity, raw, ROOT, current=True)
        for mode in (None, 0, 1, 'current'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                cookie._content_owner_source(CONTENT, raw, ROOT, current=mode)
        unlisted = b'unlisted source data earns no current certificate'
        with patch.object(domain, 'current_source_before_domain740', side_effect=AssertionError('Foreign current scope')), \
                patch.object(domain, 'peel_domain740_for_history', side_effect=AssertionError('Foreign history scope')):
            for relative in ('unlisted-source', 'calf-share/native/tests/appkit_lifecycle/cases.rs',
                             cookie.SOURCE_RELATIVE, cookie.SPEC_RELATIVE):
                for mode in (False, True):
                    self.assertIs(unlisted, cookie._content_owner_source(relative, unlisted, ROOT, current=mode))

        # Original comparison pins are not overwritten with new raw hashes.
        # The owning validator reports actual current raw40 only after strict
        # qualification; this is one NEW control, not original Cookie replay.
        comparison = cookie._expected(document, source_digest)
        self.assertEqual(40, len(comparison))
        self.assertEqual(CONTENT_ORIGINAL[0], comparison[CONTENT])
        current_pins = cookie.current_input_hashes(ROOT)
        self.assertEqual(set(comparison), set(current_pins))
        self.assertEqual(sha(raw), current_pins[CONTENT])
        self.assertNotEqual(comparison[CONTENT], current_pins[CONTENT])
        self.assertEqual(core['bindings'][cookie.COOKIE_GUARD]['before_sha256'],
                         comparison[cookie.COOKIE_GUARD])
        self.assertEqual(sha(cookie.ordinary_bytes(ROOT, cookie.COOKIE_GUARD)),
                         current_pins[cookie.COOKIE_GUARD])
        self.assertNotEqual(comparison[cookie.COOKIE_GUARD], current_pins[cookie.COOKIE_GUARD])
        for relative in set(comparison) - {CONTENT, cookie.COOKIE_GUARD}:
            self.assertEqual(comparison[relative], current_pins[relative], relative)
        self.assertEqual(CONTENT_ORIGINAL[0], cookie._document(ROOT)[0]['bindings'][CONTENT]['after_sha256'])

        # Only the changed owner leaf exercises the unchanged ordinary provider.
        with tempfile.TemporaryDirectory(prefix='cookie-content-owner740-') as temporary:
            root = Path(temporary).resolve()
            target = root / CONTENT
            target.parent.mkdir(parents=True)
            target.write_bytes(raw)
            self.assertEqual(original, cookie._content_owner_source(
                CONTENT, cookie.ordinary_bytes(root, CONTENT), ROOT, current=True))
            target.unlink()
            with self.assertRaises(FileNotFoundError):
                cookie.ordinary_bytes(root, CONTENT)
            target.symlink_to(ROOT / CONTENT)
            with self.assertRaises((OSError, ValueError)):
                cookie.ordinary_bytes(root, CONTENT)
            target.unlink()
            backing = target.with_name('owner.backing.py')
            backing.write_bytes(raw)
            target.hardlink_to(backing)
            with self.assertRaises(ValueError):
                cookie.ordinary_bytes(root, CONTENT)
            target.unlink(); backing.unlink()
            target.write_bytes(unknown)
            with self.assertRaises(ValueError):
                cookie._content_owner_source(CONTENT, cookie.ordinary_bytes(root, CONTENT), ROOT, current=True)


if __name__ == '__main__':
    unittest.main()
