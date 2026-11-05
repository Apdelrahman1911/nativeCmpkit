# SPDX-License-Identifier: Apache-2.0
"""NEW pure path-memoization regression controls; zero native/release acceptance."""
from __future__ import annotations

import concurrent.futures
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import macos_share_appkit_only_source_projection as appkit
import macos_share_ci668_composition as joint

ROOT = Path(__file__).resolve().parents[2]


class SourcePathMemoization714Tests(unittest.TestCase):
    def setUp(self):
        cached = getattr(joint, "_cached_source_path_parts", None)
        if cached is not None:
            cached.cache_clear()

    def tearDown(self):
        cached = getattr(joint, "_cached_source_path_parts", None)
        if cached is not None:
            cached.cache_clear()

    def test01_repeated_immutable_path_uses_one_grammar_validation(self):
        with patch.object(appkit, "_path", wraps=appkit._path) as parser:
            for _ in range(5):
                self.assertIsNone(joint._identity("scripts/ci/library_tests.py", b"source"))
            self.assertEqual(parser.call_count, 1)
        self.assertEqual(joint._cached_source_path_parts.cache_info().currsize, 1)

    def test02_nonexact_unhashable_and_oversized_keys_refuse_before_cache(self):
        class StrSubclass(str):
            pass
        invalid = (None, [], {}, Path("scripts/ci/tool.py"), StrSubclass("scripts/ci/tool.py"),
                   False, 1, b"scripts/ci/tool.py", "", "x" * 4097)
        with patch.object(joint, "_cached_source_path_parts", side_effect=AssertionError("key was hashed")) as cached:
            for value in invalid:
                with self.subTest(kind=type(value).__name__), self.assertRaisesRegex(ValueError, "unsafe-AppKit-source-identity"):
                    joint._identity(value, b"source")
            cached.assert_not_called()

    def test03_invalid_grammar_refusals_are_not_cached(self):
        invalid = ("/absolute", "../escape", "a/../b", "a//b", "a/./b", "a/", "a\\b", "a\x00b", "a\nb")
        for value in invalid:
            for _ in range(2):
                with self.subTest(path=value), self.assertRaisesRegex(ValueError, "unsafe-AppKit-source-identity"):
                    joint._identity(value, b"source")
        self.assertEqual(joint._cached_source_path_parts.cache_info().currsize, 0)

    def test04_valid_unicode_space_and_maximum_grammar_stay_equivalent(self):
        for value in ("scripts/ci/tool.py", "utf8/é.py", "with space/file.py", "x" * 4096, "."):
            with self.subTest(path=value[:40]):
                self.assertIsNone(joint._identity(value, b"source"))
                self.assertEqual(joint._cached_source_path_parts(value), appkit._path(value))
                self.assertIs(type(joint._cached_source_path_parts(value)), tuple)

    def test05_payload_type_and_size_validate_fresh_on_every_hit(self):
        relative = "scripts/ci/tool.py"
        joint._identity(relative, b"source")
        for payload in (None, b"", bytearray(b"source"), memoryview(b"source"), "source", b"x" * (joint.MAX_SOURCE + 1)):
            with self.subTest(kind=type(payload).__name__), self.assertRaisesRegex(ValueError, "bounded-complete-share-CI-source-operands-required"):
                joint._identity(relative, payload)
        self.assertIsNone(joint._identity(relative, b"y" * joint.MAX_SOURCE))

    def test06_cache_is_bounded_and_eviction_is_semantically_transparent(self):
        for index in range(600):
            joint._identity(f"finite/input{index}.py", b"source")
        info = joint._cached_source_path_parts.cache_info()
        self.assertEqual((info.maxsize, info.currsize), (512, 512))
        self.assertEqual(joint._cached_source_path_parts("finite/input0.py"), ("finite", "input0.py"))
        self.assertEqual(joint._cached_source_path_parts.cache_info().currsize, 512)

    def test07_concurrent_pure_hits_are_equivalent_without_exact_once_claim(self):
        names = [f"finite/input{index % 8}.py" for index in range(256)]
        def admit(name):
            joint._identity(name, b"source")
            return joint._cached_source_path_parts(name)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(admit, names))
        self.assertEqual(results, [appkit._path(name) for name in names])
        self.assertLessEqual(joint._cached_source_path_parts.cache_info().currsize, 8)

    def test08_warm_grammar_never_caches_ordinary_file_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="source-path714-file-") as folder:
            root = Path(folder).resolve()
            relative = "nested/source.py"
            target = root / relative
            target.parent.mkdir()
            target.write_bytes(b"first ordinary source")
            joint._identity(relative, b"source")
            first = joint._ordinary(root, relative)[0]
            target.write_bytes(b"second independently read source")
            second = joint._ordinary(root, relative)[0]
            self.assertEqual(first, b"first ordinary source")
            self.assertEqual(second, b"second independently read source")
            self.assertNotEqual(first, second)

    def test09_warm_grammar_never_bypasses_manifest_or_dependency_reads(self):
        document = joint._document(ROOT)
        with patch.object(joint, "_ordinary", wraps=joint._ordinary) as reader:
            fresh = joint._document(ROOT)
        self.assertEqual(fresh, document)
        reads = [call.args[1] for call in reader.call_args_list]
        self.assertIn(joint.SPEC, reads)
        self.assertIn(joint.CI_SPEC, reads)
        self.assertIn(joint.SHARE_SPEC, reads)
        self.assertIn(joint.PRODUCER_SPEC, reads)
        with tempfile.TemporaryDirectory(prefix="source-path714-manifest-") as folder:
            root = Path(folder).resolve()
            target = root / joint.SPEC
            target.parent.mkdir(parents=True)
            target.write_bytes((ROOT / joint.SPEC).read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "exact-share-CI-latest-manifest-required"):
                joint._document(root)

    def test10_actual_historical_projection_retains_exact_prior_result(self):
        from android_external328_source_projection import current_source_for_history
        raw = (ROOT / "scripts/ci/library_tests.py").read_bytes()
        result = current_source_for_history("scripts/ci/library_tests.py", raw)
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()),
                         (412990, "6fdc0947617c41b199f13e63b13056de6c76bb215698e259109c324f219c2127"))
        self.assertEqual((len(result), hashlib.sha256(result).hexdigest()),
                         (356159, "5012c3e2be83e62eba8239a0db12104d5f9f7efb3f262abd3b3080012f7afdc2"))


if __name__ == "__main__":
    unittest.main()
