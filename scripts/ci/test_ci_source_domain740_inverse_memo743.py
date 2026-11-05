# SPDX-License-Identifier: Apache-2.0
"""NEW743 pure inverse controls; unregistered, source-only, no timing assertions."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import ci_source_domain740 as stage


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(before, after, fragments):
    return {"before_sha256": digest(before), "after_sha256": digest(after),
            "before_bytes": len(before), "after_bytes": len(after),
            "fragments": [{"before": old, "after": new,
                           "before_fragment_sha256": digest(old.encode()),
                           "after_fragment_sha256": digest(new.encode())}
                          for old, new in fragments]}


def fixture(prefix=b"prefix "):
    before, after = prefix + b"BEGIN middle END suffix", prefix + b"FIRST middle LAST suffix"
    return before, after, binding(before, after, (("BEGIN", "FIRST"), ("END", "LAST")))


def changed_sha(payload):
    return "0" * 64


def changed_need(condition, diagnostic):
    raise ValueError("fresh743-mutated-need")


def changed_inverse(payload, row):
    return b"fresh743-mutated-inverse"


@contextmanager
def owned_code_patch743(function, replacement):
    """Restore a function descriptor explicitly; mock.patch would delete it."""
    original = function.__code__
    try:
        function.__code__ = replacement
        yield
    finally:
        function.__code__ = original


class CiSourceDomain740InverseMemo743Controls(unittest.TestCase):
    def setUp(self):
        stage._inverse_cached743.cache_clear()
        self.addCleanup(stage._inverse_cached743.cache_clear)
        self.assertTrue(stage._inverse_context743(), "normal trusted CPython source context required")

    def test01_success_is_exact_immutable_roundtrip_and_does_not_mutate_row(self):
        before, after, row = fixture()
        snapshot = json.dumps(row, sort_keys=True)
        self.assertEqual(before, stage._inverse_uncached743(after, row))
        first, second = stage._inverse(after, row), stage._inverse(bytes(bytearray(after)), row)
        self.assertIs(type(first), bytes)
        self.assertEqual((before, before), (first, second))
        self.assertEqual(snapshot, json.dumps(row, sort_keys=True))
        info = stage._inverse_cached743.cache_info()
        self.assertEqual((1, 1, 1, 16), (info.hits, info.misses, info.currsize, info.maxsize))
        frozen = stage._inverse_key743(after, row)
        self.assertIs(type(frozen), tuple)
        self.assertIs(type(frozen[-1]), tuple)
        self.assertTrue(all(type(part) is tuple and all(type(value) is str for value in part)
                            for part in frozen[-1]))

    def test02_complete_fresh_row_changes_never_borrow_an_old_hit(self):
        before, after, row = fixture()
        self.assertEqual(before, stage._inverse(after, row))
        row["fragments"][0]["before_fragment_sha256"] = "0" * 64
        # The original arithmetic ignores this field, but the full key must not.
        self.assertEqual(before, stage._inverse(after, row))
        info = stage._inverse_cached743.cache_info()
        self.assertEqual((0, 2, 2), (info.hits, info.misses, info.currsize))
        for field, replacement in (("after_sha256", "1" * 64),
                                   ("before_sha256", "2" * 64),
                                   ("before_bytes", len(before) + 1),
                                   ("after_bytes", len(after) + 1)):
            fake = json.loads(json.dumps(row))
            fake[field] = replacement
            with self.assertRaises(ValueError) as original:
                stage._inverse_uncached743(after, fake)
            with self.assertRaises(ValueError) as current:
                stage._inverse(after, fake)
            self.assertEqual(str(original.exception), str(current.exception))
        self.assertEqual(0, stage._inverse_cached743.cache_info().hits)
        self.assertEqual(2, stage._inverse_cached743.cache_info().currsize)

    def test03_foreign_unhashable_and_oversized_inputs_use_original_uncached_behavior(self):
        class UnhashableBytes(bytes):
            __hash__ = None
        class UnhashableText(str):
            __hash__ = None
        before, after, row = fixture()
        cases = [(UnhashableBytes(after), row)]
        text_row = json.loads(json.dumps(row))
        text_row["after_sha256"] = UnhashableText(text_row["after_sha256"])
        cases.append((after, text_row))
        tuple_row = json.loads(json.dumps(row))
        tuple_row["fragments"] = tuple(tuple_row["fragments"])
        cases.append((after, tuple_row))
        foreign_row = json.loads(json.dumps(row))
        foreign_row["unlisted"] = True
        cases.append((after, foreign_row))
        padding = b"p" * (stage.MAX_INVERSE_CACHE_PAYLOAD743 + 1)
        wide_before, wide_after = padding + b"A", padding + b"B"
        cases.append((wide_after, binding(wide_before, wide_after, (("A", "B"),))))
        fragment = "A" * (stage.MAX_INVERSE_CACHE_KEY_CHARS743 + 1)
        long_before, long_after = b"p" + fragment.encode() + b"q", b"pBq"
        cases.append((long_after, binding(long_before, long_after, ((fragment, "B"),))))
        fragments = tuple((f"P{i:02}", f"Q{i:02}") for i in range(17))
        many_before = " ".join(old for old, new in fragments).encode()
        many_after = " ".join(new for old, new in fragments).encode()
        cases.append((many_after, binding(many_before, many_after, fragments)))
        for payload, candidate in cases:
            with self.subTest(kind=type(payload).__name__, size=len(payload)):
                self.assertIsNone(stage._inverse_key743(payload, candidate))
                self.assertEqual(stage._inverse_uncached743(payload, candidate), stage._inverse(payload, candidate))
        info = stage._inverse_cached743.cache_info()
        self.assertEqual((0, 0, 0, 16), (info.hits, info.misses, info.currsize, info.maxsize))

    def test04_entry_payload_result_and_key_bounds_hold_under_owned_threads(self):
        fixtures = [fixture(f"row{i:02} ".encode()) for i in range(24)]
        for before, after, row in fixtures:
            key = stage._inverse_key743(after, row)
            self.assertLessEqual(len(key[0]), 512 * 1024)
            self.assertLessEqual(key[3], 512 * 1024)
            characters = len(key[1]) + len(key[2]) + sum(len(value) for part in key[-1] for value in part)
            self.assertLessEqual(characters, 128 * 1024)
            self.assertEqual(before, stage._inverse(after, row))
        self.assertEqual(16, stage._inverse_cached743.cache_info().currsize)
        before, after, row = fixtures[0]  # Evicted above: no exactly-once miss assertion.
        with ThreadPoolExecutor(max_workers=4) as workers:
            outputs = list(workers.map(lambda _: stage._inverse(after, row), range(16)))
        self.assertEqual([before] * 16, outputs)
        self.assertEqual(16, stage._inverse_cached743.cache_info().currsize)
        self.assertTrue(all(type(output) is bytes for output in outputs))

    def test05_errors_and_encoding_refusals_are_never_retained(self):
        before, after, row = fixture()
        row["after_sha256"] = "0" * 64
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, "complete740-current-source-afterimage-required"):
                stage._inverse(after, row)
        info = stage._inverse_cached743.cache_info()
        self.assertEqual((0, 2, 0), (info.hits, info.misses, info.currsize))
        row = binding(before, after, (("BEGIN", "FIRST"), ("END", "LAST")))
        row["fragments"][0]["before"] = "\ud800"
        for _ in range(2):
            with self.assertRaises(UnicodeEncodeError):
                stage._inverse(after, row)
        self.assertEqual(0, stage._inverse_cached743.cache_info().currsize)

    def test06_warm_helper_crypto_and_original_code_changes_run_fresh_uncached(self):
        before, after, row = fixture()
        self.assertEqual(before, stage._inverse(after, row))
        baseline = stage._inverse_cached743.cache_info()
        primitive = stage._INVERSE_DIGEST743
        crypto = Mock(wraps=primitive)
        with patch.object(stage.hashlib, "sha256", crypto):
            self.assertFalse(stage._inverse_context743())
            self.assertEqual(before, stage._inverse(after, row))
            self.assertEqual(2, crypto.call_count)
        with patch.object(stage, "sha", changed_sha):
            with self.assertRaisesRegex(ValueError, "complete740-current-source-afterimage-required"):
                stage._inverse(after, row)
        with owned_code_patch743(stage.sha, changed_sha.__code__):
            self.assertFalse(stage._inverse_context743())
            with self.assertRaisesRegex(ValueError, "complete740-current-source-afterimage-required"):
                stage._inverse(after, row)
        self.assertIs(stage._INVERSE_SHA_CODE743, stage.sha.__code__)
        with owned_code_patch743(stage.need, changed_need.__code__):
            self.assertFalse(stage._inverse_context743())
            with self.assertRaisesRegex(ValueError, "fresh743-mutated-need"):
                stage._inverse(after, row)
        self.assertIs(stage._INVERSE_NEED_CODE743, stage.need.__code__)
        with owned_code_patch743(stage._inverse_uncached743, changed_inverse.__code__):
            self.assertFalse(stage._inverse_context743())
            self.assertEqual(b"fresh743-mutated-inverse", stage._inverse(after, row))
        self.assertIs(stage._INVERSE_CODE743, stage._inverse_uncached743.__code__)
        with patch.object(stage, "_INVERSE_BUILTIN_DIGEST743", False):
            self.assertEqual(before, stage._inverse(after, row))
        self.assertEqual(baseline, stage._inverse_cached743.cache_info())
        self.assertTrue(stage._inverse_context743())

    def test07_warm_builtin_name_overrides_cannot_return_a_stale_success(self):
        before, after, row = fixture()
        self.assertEqual(before, stage._inverse(after, row))
        baseline = stage._inverse_cached743.cache_info()
        with patch.object(stage, "reversed", lambda values: iter(()), create=True):
            self.assertFalse(stage._inverse_context743())
            with self.assertRaisesRegex(ValueError, "complete740-original-source-preimage-required"):
                stage._inverse(after, row)
        with patch.object(stage, "len", lambda value: len(value) + 1, create=True):
            self.assertFalse(stage._inverse_context743())
            with self.assertRaisesRegex(ValueError, "complete740-current-source-afterimage-required"):
                stage._inverse(after, row)
        self.assertEqual(baseline, stage._inverse_cached743.cache_info())

    def test08_warm_inverse_retains_fresh_real_document_binding_filesystem_and_root_checks(self):
        import ci_source_recovery740_742 as recovery
        import macos_share_appkit_only_source_projection as appkit
        import macos_share_ci668_composition as joint
        raw = (stage.ROOT / stage.SPEC).read_bytes()
        document = json.loads(raw)
        relative = "scripts/ci/tooling_recovery671_source_projection.py"
        row = document["bindings"][relative]
        payload = recovery.current_source_before_recovery(relative, (stage.ROOT / relative).read_bytes(), stage.ROOT)
        self.assertEqual((row["after_sha256"], row["after_bytes"]), (digest(payload), len(payload)))
        expected = stage._inverse_uncached743(payload, row)
        stage._inverse_cached743.cache_clear()
        reader = appkit.ordinary_bytes if joint._descriptor_source_io_supported() else joint._portable_ordinary
        with tempfile.TemporaryDirectory() as name:
            container = Path(name).resolve()
            root = container / "tree"
            target = root / stage.SPEC
            target.parent.mkdir(parents=True)
            target.write_bytes(raw)
            with patch.object(stage, "_ordinary", wraps=reader) as ordinary, \
                 patch.object(stage, "_binding", wraps=stage._binding) as bindings, \
                 patch.object(recovery, "current_source_before_recovery", lambda relative, payload, root: payload):
                self.assertEqual(expected, stage.current_source_before_domain740(relative, payload, root))
                self.assertEqual(expected, stage.current_source_before_domain740(relative, payload, root))
                self.assertEqual(2, ordinary.call_count)
                self.assertEqual(14, bindings.call_count)
                baseline = stage._inverse_cached743.cache_info()
                self.assertEqual((1, 1, 1), (baseline.hits, baseline.misses, baseline.currsize))
                target.write_bytes(raw + b"\n")
                with self.assertRaisesRegex(ValueError, "exact740-transition-manifest-required"):
                    stage.current_source_before_domain740(relative, payload, root)
                fake = json.loads(raw)
                fake["bindings"][relative]["fragments"][0]["after_fragment_sha256"] = "0" * 64
                encoded = (json.dumps(fake, sort_keys=True, separators=(",", ":")) + "\n").encode()
                target.write_bytes(encoded)
                with patch.object(stage, "SPEC_SHA256", digest(encoded)), \
                     self.assertRaisesRegex(ValueError, "exact740-unique-reversible-source-fragments-required"):
                    stage.current_source_before_domain740(relative, payload, root)
                target.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, "ordinary-canonical-.*-root-required"):
                    stage.current_source_before_domain740(relative, payload, root / ".." / "tree")
                target.unlink()
                backing = target.with_name("backing743.json")
                backing.write_bytes(raw)
                target.hardlink_to(backing)
                with self.assertRaisesRegex(ValueError, "bounded-ordinary-unaliased-.*-file-required"):
                    stage.current_source_before_domain740(relative, payload, root)
                self.assertEqual(baseline, stage._inverse_cached743.cache_info())
        self.assertFalse(container.exists())

    def test09_owned_function_code_patch_restores_after_body_failure_and_success(self):
        def original(value):
            return value
        def changed(value):
            return ("changed743", value)
        code = original.__code__
        with owned_code_patch743(original, changed.__code__):
            self.assertIs(changed.__code__, original.__code__)
            self.assertEqual(("changed743", b"source-only"), original(b"source-only"))
        self.assertIs(code, original.__code__)
        self.assertEqual(b"source-only", original(b"source-only"))
        with self.assertRaisesRegex(RuntimeError, "owned743-body-refusal"):
            with owned_code_patch743(original, changed.__code__):
                self.assertIs(changed.__code__, original.__code__)
                raise RuntimeError("owned743-body-refusal")
        self.assertIs(code, original.__code__)
        self.assertEqual(b"source-only", original(b"source-only"))
        with self.assertRaises(TypeError):
            with owned_code_patch743(original, None):
                self.fail("invalid code assignment must not enter the body")
        self.assertIs(code, original.__code__)
        self.assertTrue(stage._inverse_context743())



if __name__ == "__main__":
    unittest.main()
