# SPDX-License-Identifier: Apache-2.0
"""NEW common-JDK/Content owning seam only; no prior population replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import call, patch

import ci_source_domain740 as domain
import ci_source_recovery740_742 as recovery
import cookie_ci668_outer_source_projection as outer
import cookie_common_jdk_source_projection as common
import macos_share_ci668_composition as joint

ROOT = Path(__file__).resolve().parents[2]
CONTENT = "scripts/ci/webview_content_policy_source_projection.py"
COMMON = "scripts/ci/cookie_common_jdk_source_projection.py"
NEW_CONTROL = "scripts/ci/test_cookie_common_jdk_content_boundary740.py"
COMMON_C6 = ("16fff9aa57e079c0e98d1a88e5196d458fe4375f7b46a225b94263f70cf8261e", 15750)
COMMON_ORIGINAL = ("b5eca01bbbe89e584b18279cb15aa36a8d1e06d205a2c4fcd52d24b271e55774", 15226)
COMMON_SPEC_ORIGINAL = ("9445b6e7835fe81bec5b22f033f8e1c207dd639ff4d6b75df47ee51078e38a90", 20449)
CONTENT_COOKIE = ("ad544703072bd892274a08b29304f313d1915d8c24840f6d136474ea1e560253", 14440)
CONTENT_PRECOOKIE = ("bb0b63b32a41667c0c33401f44873bd20426524ece52caaa3cfa41ffd880f60d", 14011)
CONTENT_R5 = ("d20c4d3e7dd229c29d738ce0f49eb1f29d2c815d8463186db95316e99a67addf", 15891)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


class CookieCommonJdkContentBoundary740Controls(unittest.TestCase):
    def test01_exact_common_jdk_content_current_history_and_own_guard_preserve_original_cookie_pins(self):
        core = recovery._document(ROOT)
        outer_document, _ = outer._document(ROOT)
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
        self.assertIn(COMMON, recovery.MODIFIED)
        self.assertNotIn(COMMON, recovery.ADDED_INPUTS)
        common_binding = core["bindings"][COMMON]
        self.assertEqual(COMMON_C6, (common_binding["before_sha256"], common_binding["before_bytes"]))
        self.assertEqual(4, len(common_binding["fragments"]))
        common_raw = outer.ordinary_bytes(ROOT, COMMON)
        self.assertEqual((sha(common_raw), len(common_raw)),
                         (common_binding["after_sha256"], common_binding["after_bytes"]))
        common_c6 = recovery.current_source_before_recovery(COMMON, common_raw, ROOT)
        self.assertEqual(COMMON_C6, (sha(common_c6), len(common_c6)))
        with patch.object(domain, "current_source_before_domain740",
                          wraps=domain.current_source_before_domain740) as strict:
            common_original = outer.current_source_before_cookie_outer(COMMON, common_raw, ROOT)
            strict.assert_called_once_with(COMMON, common_raw, ROOT)
        self.assertEqual(COMMON_ORIGINAL, (sha(common_original), len(common_original)))
        self.assertEqual(common_original, outer.source_before_cookie_outer(COMMON, common_raw, ROOT))
        self.assertEqual(common_original, outer.peel_cookie_outer_for_history(COMMON, common_raw, ROOT))
        old_common_row = outer_document["bindings"][COMMON]
        self.assertEqual(COMMON_ORIGINAL, (old_common_row["before_sha256"], old_common_row["before_bytes"]))
        self.assertEqual(COMMON_C6, (old_common_row["after_sha256"], old_common_row["after_bytes"]))
        self.assertEqual(2, len(old_common_row["fragments"]))

        # The original common/JDK manifest, Content4 inverse and own-template
        # are unchanged. New raw ownership is a separate outer inverse only.
        common_spec = outer.ordinary_bytes(ROOT, common.SPEC_RELATIVE)
        self.assertEqual(COMMON_SPEC_ORIGINAL, (sha(common_spec), len(common_spec)))
        document = common._document(ROOT)
        self.assertEqual(json.loads(common_spec), document)
        self.assertEqual({"bytes": 15226,
                          "template_sha256": "52c1d71e3004fcddb156d264151450da9241f7ff12c502638b5de0f6d39c031e"},
                         document["own_guard"])
        content_row = document["bindings"][CONTENT]
        self.assertEqual(content_row, outer_document["bindings"][CONTENT])
        self.assertEqual(CONTENT_PRECOOKIE, (content_row["before_sha256"], content_row["before_bytes"]))
        self.assertEqual(CONTENT_COOKIE, (content_row["after_sha256"], content_row["after_bytes"]))
        self.assertEqual(4, len(content_row["fragments"]))
        raw = outer.ordinary_bytes(ROOT, CONTENT)
        content_binding = core["bindings"][CONTENT]
        self.assertEqual((sha(raw), len(raw)),
                         (content_binding["after_sha256"], content_binding["after_bytes"]))
        cookie_image = recovery.current_source_before_recovery(CONTENT, raw, ROOT)
        self.assertEqual(CONTENT_COOKIE, (sha(cookie_image), len(cookie_image)))
        branch = content_binding["fragments"][-1]
        r5 = raw.replace(branch["after"].encode(), branch["before"].encode(), 1)
        # R5 is immutable source DATA; exact later deltas are not its old pin.
        historical_deltas = (
            (b'    from tooling_recovery671_source_projection import current_source_before_tooling671\n    payload = current_source_before_tooling671(relative, payload)\n', b""),
            (b'def _appkit_key_wait_source(relative, payload, *, current):\n    """Only three exact successors restore their unchanged Content/Share pins.\n\n    Current uses the original strict owning ingress. History peels only its exact\n    reviewed afterimage; old/unknown/unlisted data is not a current certificate.\n    Every other key-wait path, native criterion, manifest pin and fixture stays exact.\n    """\n    _identity(relative, payload)\n    if type(current) is not bool:\n        raise ValueError("An exact AppKit content-boundary source mode is required")\n    if relative not in (\n        "calf-share/native/tests/appkit_lifecycle/cases.rs",\n        "scripts/ci/macos_share_appkit_lifecycle.py",\n        "scripts/ci/test_macos_share_missing_only.py",\n    ):\n        return payload  # Unlisted source data remains uncertified.\n    import macos_share_key_wait_observation as key_wait\n    binding = key_wait._document()["bindings"][relative]\n    if _document()["unchanged_inputs"].get(relative) != binding["before_sha256"]:\n        raise ValueError("AppKit key-wait must restore the unchanged original Content/Share source pin")\n    if current:\n        return key_wait.current_source_before_key_wait(relative, payload)\n    return key_wait.peel_key_wait_for_history(relative, payload)', b'def _appkit_key_wait_source(relative, payload, *, current):\n    """Only the exact cases successor crosses the unchanged Content/Share pin.\n\n    Current uses the original strict owning ingress. History peels only its exact\n    reviewed afterimage; old/unknown/unlisted data is not a current certificate.\n    No other key-wait path, native criterion, manifest pin or fixture is widened.\n    """\n    _identity(relative, payload)\n    if type(current) is not bool:\n        raise ValueError("An exact AppKit content-boundary source mode is required")\n    if relative != "calf-share/native/tests/appkit_lifecycle/cases.rs":\n        return payload  # Unlisted source data remains uncertified.\n    import macos_share_key_wait_observation as key_wait\n    binding = key_wait._document()["bindings"][relative]\n    if _document()["unchanged_inputs"].get(relative) != binding["before_sha256"]:\n        raise ValueError("AppKit key-wait must restore the unchanged original Content/Share source pin")\n    if current:\n        return key_wait.current_source_before_key_wait(relative, payload)\n    return key_wait.peel_key_wait_for_history(relative, payload)'),
        )
        for after, before in historical_deltas:
            self.assertEqual(1, r5.count(after))
            r5 = r5.replace(after, before, 1)
        self.assertEqual(CONTENT_R5, (sha(r5), len(r5)))

        # Exactly one strict Content ingress; later inverse work is history.
        # Strict common-guard reads inside _document remain independently fresh.
        with patch.object(domain, "current_source_before_domain740",
                          wraps=domain.current_source_before_domain740) as strict:
            old = common.current_source_before_cookie(CONTENT, raw, ROOT)
            content_calls = [entry for entry in strict.call_args_list if entry.args[0] == CONTENT]
            self.assertEqual([call(CONTENT, raw, ROOT)], content_calls)
        self.assertEqual(CONTENT_PRECOOKIE, (sha(old), len(old)))
        original_current = domain.current_source_before_domain740

        def refuse_content_current(relative, payload, root=ROOT):
            if relative == CONTENT:
                raise AssertionError("History must not run strict Content admission")
            return original_current(relative, payload, root)

        unknown = raw + b"\n# unknown common-JDK Content owner\n"
        with patch.object(domain, "current_source_before_domain740", side_effect=refuse_content_current):
            self.assertEqual(old, common.source_before_cookie(CONTENT, raw, ROOT))
            self.assertEqual(old, common.peel_cookie_for_history(CONTENT, raw, ROOT))
            self.assertEqual(old, common.peel_cookie_for_history(CONTENT, cookie_image, ROOT))
            self.assertIs(old, common.peel_cookie_for_history(CONTENT, old, ROOT))
            self.assertIs(r5, common.peel_cookie_for_history(CONTENT, r5, ROOT))
            self.assertIs(unknown, common.peel_cookie_for_history(CONTENT, unknown, ROOT))
        for bad in (cookie_image, r5, old, raw[:-1], raw + b"\n", b"", None,
                    bytearray(raw), raw.decode(), b"x" * (outer.MAX_SOURCE_BYTES + 1)):
            with self.subTest(content_type=type(bad).__name__), self.assertRaises(ValueError):
                common.current_source_before_cookie(CONTENT, bad, ROOT)
        with self.assertRaises(ValueError):
            common.source_before_cookie(CONTENT, unknown, ROOT)

        # The new helper is common-guard-only, not another Content or foreign
        # current scope. Old/partial/unknown current owners are never borrowed.
        unknown_common = common_raw + b"\n# unknown current common-JDK owner\n"
        self.assertEqual(common_c6, outer._common_jdk_guard_source(COMMON, common_raw, ROOT, current=False))
        for historical in (common_c6, common_original, unknown_common):
            self.assertIs(historical, outer._common_jdk_guard_source(COMMON, historical, ROOT, current=False))
        for bad in (common_c6, common_original, common_raw[:-1], unknown_common,
                    b"", None, bytearray(common_raw), common_raw.decode()):
            with self.subTest(common_type=type(bad).__name__), self.assertRaises(ValueError):
                outer.current_source_before_cookie_outer(COMMON, bad, ROOT)
        for mode in (None, 0, 1, "current"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                outer._common_jdk_guard_source(COMMON, common_raw, ROOT, current=mode)
        for identity in (Path(COMMON), None, [], 1):
            with self.subTest(identity_type=type(identity).__name__), self.assertRaises(ValueError):
                outer._common_jdk_guard_source(identity, common_raw, ROOT, current=True)
        unlisted = b"unlisted data earns no source/current certificate"
        with patch.object(domain, "current_source_before_domain740", side_effect=AssertionError("Foreign current")), \
                patch.object(domain, "peel_domain740_for_history", side_effect=AssertionError("Foreign history")):
            for relative in (CONTENT, outer.SOURCE_RELATIVE, outer.SPEC_RELATIVE, "unlisted-source"):
                for mode in (False, True):
                    self.assertIs(unlisted, outer._common_jdk_guard_source(relative, unlisted, ROOT, current=mode))

        # Raw34 reporting follows the fresh raw40 owning validator. Comparison
        # pins and scope sizes are retained, not rewritten to current hashes.
        current = common.validate_current_sources(ROOT)
        self.assertEqual(34, len(current))
        self.assertEqual(sha(raw), current[CONTENT])
        self.assertEqual(sha(common_raw), current[COMMON])
        self.assertNotEqual(CONTENT_COOKIE[0], current[CONTENT])
        self.assertNotEqual(COMMON_C6[0], current[COMMON])
        self.assertEqual(CONTENT_COOKIE[0], common._document(ROOT)["bindings"][CONTENT]["after_sha256"])
        real_ordinary = common.ordinary_bytes

        def changed_owner(root, relative, limit=common.MAX_SOURCE_BYTES):
            result = real_ordinary(root, relative, limit)
            return result + b"\n# displaced owning image\n" if relative == COMMON else result

        with patch.object(common, "ordinary_bytes", side_effect=changed_owner), self.assertRaises(ValueError):
            common._document(ROOT)

        # Only this new owning leaf exercises the unchanged ordinary provider.
        with tempfile.TemporaryDirectory(prefix="cookie-common-content740-") as temporary:
            root = Path(temporary).resolve()
            target = root / COMMON
            target.parent.mkdir(parents=True)
            target.write_bytes(common_raw)
            self.assertEqual(common_c6, outer._common_jdk_guard_source(
                COMMON, outer.ordinary_bytes(root, COMMON), ROOT, current=True))
            target.unlink()
            with self.assertRaises(FileNotFoundError):
                outer.ordinary_bytes(root, COMMON)
            target.symlink_to(ROOT / COMMON)
            with self.assertRaises((OSError, ValueError)):
                outer.ordinary_bytes(root, COMMON)
            target.unlink()
            backing = target.with_name("common.backing.py")
            backing.write_bytes(common_raw)
            target.hardlink_to(backing)
            with self.assertRaises(ValueError):
                outer.ordinary_bytes(root, COMMON)
            target.unlink()
            backing.unlink()
            target.write_bytes(unknown_common)
            with self.assertRaises(ValueError):
                outer._common_jdk_guard_source(COMMON, outer.ordinary_bytes(root, COMMON), ROOT, current=True)


if __name__ == "__main__":
    unittest.main()
