# SPDX-License-Identifier: Apache-2.0
"""NEW pure-content memo hazards only; source prepared, never executed by author.

Requires the lead's separately reviewed final current-ingress composition.
These are not a replay of any accepted CI668/671/producer/714 test methods.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import macos_share_appkit_only_source_projection as appkit
import macos_share_ci668_composition as latest

ROOT = Path(__file__).resolve().parents[2]


def signature(value):
    """Include primitive type, float representation and object insertion order."""
    if type(value) is dict:
        return ("object", tuple((key, signature(child)) for key, child in value.items()))
    if type(value) is list:
        return ("array", tuple(signature(child) for child in value))
    return (type(value).__name__, repr(value))


def outcome(function, payload):
    try:
        return ("value", signature(function(payload)))
    except Exception as error:
        return (type(error), str(error))


def copy_only_document_dependencies(root):
    """Discover only live manifest reads, not a whole fixture/native population."""
    with patch.object(latest, "_ordinary", wraps=latest._ordinary) as reads:
        latest._document(ROOT)
    relatives = tuple(dict.fromkeys(call.args[1] for call in reads.call_args_list))
    for relative in relatives:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
        target.chmod(0o644)
    return relatives


class ShareCIPureJSONContent676Controls(unittest.TestCase):
    def setUp(self):
        latest._cached_json_tree.cache_clear()

    def test01_exact_parser_values_order_types_and_original_refusals_are_equivalent(self):
        ordinary = [
            b"null", b"true", b"false", b"0", b"-0.0", b"1.25", b"1e10000",
            b'"plain"', b'{"z":[],"a":{},"n":[1,true,null,-0.0]}',
            '{"unicode":"\U0001f409\u00e9"}'.encode(), b'{"surrogate":"\\ud800"}',
            '"BOM UTF16"'.encode("utf-16"), b"[" * 64 + b"0" + b"]" * 64,
        ]
        for relative in (latest.SPEC, latest.CI_SPEC, latest.SHARE_SPEC,
                         latest.OBSERVATION_SPEC, latest.COOKIE_SPEC,
                         latest.COOKIE_COMMON_SPEC, latest.CALLBACK_SPEC, latest.PRODUCER_SPEC, latest.ANDROID_SPEC):
            ordinary.append((ROOT / relative).read_bytes())
        for payload in ordinary:
            with self.subTest(payload_bytes=len(payload)):
                before = appkit.json_bytes(payload)
                after = latest._json(payload)
                self.assertEqual(signature(before), signature(after))
                self.assertEqual(json.dumps(before, ensure_ascii=True),
                                 json.dumps(after, ensure_ascii=True))
        for payload in (b'{"a":1,"a":2}', b"NaN", b"Infinity", b"-Infinity",
                        b"[", b"\xff", b"[" * 65 + b"0" + b"]" * 65):
            with self.subTest(refusing_payload=repr(payload)):
                self.assertEqual(outcome(appkit.json_bytes, payload), outcome(latest._json, payload))

    def test02_every_returned_nested_object_is_independent_and_internal_values_are_immutable(self):
        payload = b'{"first":{"rows":[{"x":1},[2,3]]},"empty":{}}'
        first, second = latest._json(payload), latest._json(bytes(bytearray(payload)))
        self.assertEqual(signature(first), signature(second))
        self.assertIsNot(first, second)
        self.assertIsNot(first["first"], second["first"])
        self.assertIsNot(first["first"]["rows"], second["first"]["rows"])
        self.assertIsNot(first["first"]["rows"][0], second["first"]["rows"][0])
        first["first"]["rows"][0]["x"] = "mutated"
        first["first"]["rows"][1].append(99)
        first["empty"]["new"] = []
        self.assertEqual(signature(appkit.json_bytes(payload)), signature(second))
        self.assertEqual(signature(second), signature(latest._json(payload)))
        tree = latest._cached_json_tree(payload, latest._json_parser_context(appkit.json_bytes))
        pending = [tree]
        while pending:
            child = pending.pop()
            if type(child) is tuple:
                pending.extend(child)
            else:
                self.assertIn(type(child), (str, int, float, bool, type(None)))
        self.assertEqual(1, latest._cached_json_tree.cache_info().currsize)

    def test03_keys_are_complete_exact_bytes_not_length_digest_alias_or_mutable_input(self):
        calls = []
        original = appkit.json_bytes

        def parser(payload):
            calls.append(payload)
            return original(payload)

        with patch.object(appkit, "json_bytes", parser):
            self.assertEqual({"x": 1}, latest._json(b'{"x":1}'))
            self.assertEqual({"x": 1}, latest._json(bytes(bytearray(b'{"x":1}'))))
            self.assertEqual({"x": 2}, latest._json(b'{"x":2}'))
            self.assertEqual({"x": 1}, latest._json(b'{ "x":1}'))
        self.assertEqual([b'{"x":1}', b'{"x":2}', b'{ "x":1}'], calls)
        self.assertEqual(3, latest._cached_json_tree.cache_info().currsize)

    def test04_nonexact_empty_and_oversize_keys_refuse_before_cache_hashing_and_failures_never_stick(self):
        class ForeignBytes(bytes):
            def __hash__(self):
                raise AssertionError("nonexact key must never be hashed")

        invalid = (None, {}, [], "{}", bytearray(b"{}"), memoryview(b"{}"),
                   ForeignBytes(b"{}"), b"", b"x" * (latest.MAX_SPEC + 1))
        with patch.object(latest, "_cached_json_tree",
                          side_effect=AssertionError("invalid key reached cache")) as cache:
            for payload in invalid:
                with self.subTest(kind=type(payload).__name__), self.assertRaisesRegex(
                        ValueError, "^bounded-complete-share-CI-manifest-required$"):
                    latest._json(payload)
            cache.assert_not_called()
        for payload in (b'{"a":1,"a":2}', b"NaN", b"[", b"[" * 65 + b"0" + b"]" * 65):
            for _ in range(2):
                self.assertEqual(outcome(appkit.json_bytes, payload), outcome(latest._json, payload))
        self.assertEqual(0, latest._cached_json_tree.cache_info().currsize)

    def test05_capacity_parser_dependency_context_and_foreign_mutable_results_are_safe(self):
        for number in range(20):
            self.assertEqual(number, latest._json(str(number).encode()))
        self.assertEqual(16, latest._cached_json_tree.cache_info().maxsize)
        self.assertEqual(16, latest._cached_json_tree.cache_info().currsize)
        latest._cached_json_tree.cache_clear()
        payload = b'{"x":[]}'
        self.assertEqual({"x": []}, latest._json(payload))
        old_unique = appkit._unique
        calls = []

        def changed_unique(pairs):
            calls.append(True)
            return old_unique(pairs)

        with patch.object(appkit, "_unique", changed_unique):
            self.assertEqual({"x": []}, latest._json(payload))
        self.assertEqual([True], calls)
        self.assertEqual(2, latest._cached_json_tree.cache_info().misses)
        latest._cached_json_tree.cache_clear()
        foreign_calls = []

        def foreign(payload):
            foreign_calls.append(payload)
            return {"mutable": bytearray(b"owned test result")}

        with patch.object(appkit, "json_bytes", foreign):
            first, second = latest._json(payload), latest._json(payload)
        first["mutable"].append(0)
        self.assertNotEqual(first, second)
        self.assertEqual([payload, payload], foreign_calls)
        self.assertEqual(0, latest._cached_json_tree.cache_info().currsize)
        original = appkit.json_bytes

        class UnhashableParser:
            __hash__ = None

            def __call__(self, payload):
                return original(payload)

        with patch.object(appkit, "json_bytes", UnhashableParser()):
            first, second = latest._json(payload), latest._json(payload)
        self.assertEqual(signature(first), signature(second))
        self.assertIsNot(first, second)
        self.assertEqual(0, latest._cached_json_tree.cache_info().currsize)

    def test06_warm_content_still_reads_hashes_and_checks_every_live_document_and_predecessor(self):
        observed = []
        documents = []
        with patch.object(latest, "_ordinary", wraps=latest._ordinary) as reads, \
             patch.object(latest, "sha", wraps=latest.sha) as hashes, \
             patch.object(latest, "_shape", wraps=latest._shape) as shape, \
             patch.object(latest, "_sealed_predecessor_hashes", wraps=latest._sealed_predecessor_hashes) as sealed:
            for _ in range(2):
                reads.reset_mock()
                hashes.reset_mock()
                documents.append(latest._document(ROOT))
                observed.append(([call.args for call in reads.call_args_list],
                                 [call.args for call in hashes.call_args_list]))
            self.assertEqual(2, shape.call_count)
            self.assertEqual(2, sealed.call_count)
        self.assertEqual(observed[0], observed[1])
        relatives = [args[1] for args in observed[1][0]]
        self.assertEqual(latest.SPEC, relatives[0])
        self.assertTrue(set((latest.CI_SPEC, latest.SHARE_SPEC, latest.OBSERVATION_SPEC,
                             latest.COOKIE_SPEC, latest.COOKIE_COMMON_SPEC,
                             latest.CALLBACK_SPEC, latest.PRODUCER_SPEC)) <= set(relatives))
        self.assertEqual(signature(documents[0]), signature(documents[1]))
        self.assertIsNot(documents[0], documents[1])
        self.assertIsNot(documents[0]["raw_inputs"], documents[1]["raw_inputs"])

    def test07_warm_manifest_and_every_predecessor_drift_refuse_and_direct_mutable_schema_is_uncached(self):
        with tempfile.TemporaryDirectory(prefix="share-pure-json676-") as directory:
            root = Path(directory)
            relatives = copy_only_document_dependencies(root)
            latest._document(root)
            for relative in relatives:
                target = root / relative
                raw = target.read_bytes()
                target.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                try:
                    with self.subTest(relative=relative), self.assertRaises(ValueError):
                        latest._document(root)
                finally:
                    target.write_bytes(raw)
                latest._document(root)  # NEW warm-after-restoration hazard, not old fixture replay.
        document = latest._document(ROOT)
        document["scope"] = "same mutable object, changed schema"
        with patch.object(latest, "_sealed_predecessor_hashes", wraps=latest._sealed_predecessor_hashes) as sealed, \
             self.assertRaisesRegex(ValueError, "^finite-four-named-joint-source-views-required$"):
            latest._shape(document, ROOT)
        sealed.assert_not_called()  # Original schema refusal still precedes live predecessors.
        self.assertEqual(latest.SCOPE, latest._document(ROOT)["scope"])

    def test08_warm_portable_reads_close_only_owned_descriptors_and_do_not_hide_aliases(self):
        with tempfile.TemporaryDirectory(prefix="share-pure-json-fd676-") as directory:
            root = Path(directory)
            copy_only_document_dependencies(root)
            latest._document(root)
            original_open, original_close = os.open, os.close
            opened, closed = [], []

            def opening(*args, **kwargs):
                descriptor = original_open(*args, **kwargs)
                opened.append(descriptor)
                return descriptor

            def closing(descriptor):
                closed.append(descriptor)
                return original_close(descriptor)

            with patch.object(latest, "_descriptor_source_io_supported", return_value=False), \
                 patch.object(latest.os, "open", opening), patch.object(latest.os, "close", closing):
                latest._document(root)
            self.assertTrue(opened)
            self.assertEqual(opened, closed)
            target = root / latest.SPEC
            held = target.read_bytes()
            alias = root / "warm-hardlink.json"
            os.link(target, alias)
            try:
                with self.assertRaises(ValueError):
                    latest._document(root)
            finally:
                alias.unlink()
            displaced = target.with_suffix(".held")
            target.rename(displaced)
            target.symlink_to(displaced.name)
            try:
                with self.assertRaises(ValueError):
                    latest._document(root)
            finally:
                target.unlink()
                displaced.rename(target)
            self.assertEqual(held, target.read_bytes())
            latest._document(root)

    def test09_concurrent_hits_and_misses_return_independent_owned_containers(self):
        payload = b'{"owned":[{"value":1}]}'
        barrier = threading.Barrier(6)
        results, failures = [], []
        lock = threading.Lock()

        def caller(number):
            try:
                barrier.wait(timeout=5)
                document = latest._json(payload)
                document["owned"][0]["value"] = number
                with lock:
                    results.append(document)
            except BaseException as error:
                with lock:
                    failures.append(error)

        threads = [threading.Thread(target=caller, args=(number,)) for number in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual([], failures)
        self.assertEqual(6, len(results))
        self.assertEqual(set(range(6)), {document["owned"][0]["value"] for document in results})
        self.assertEqual(6, len({id(document["owned"][0]) for document in results}))
        self.assertEqual({"owned": [{"value": 1}]}, latest._json(payload))
        self.assertEqual(1, latest._cached_json_tree.cache_info().currsize)

    def test10_only_pure_content_is_memoized_and_direct_current_payload_checks_stay_live(self):
        source = (ROOT / latest.OWNER).read_bytes()
        tree = ast.parse(source)
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        caches = [node.name for node in functions.values()
                  if any(isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)
                         and decorator.func.id == "lru_cache" for decorator in node.decorator_list)]
        self.assertEqual(["_cached_source_path_parts", "_cached_json_tree"], caches)
        pure = functions["_cached_json_tree"]
        self.assertFalse(any(isinstance(node, ast.Name) and node.id in {
            "ROOT", "_ordinary", "_shape", "_document", "_sealed_predecessor_hashes",
            "_raw_payload", "_own_payload", "validate_current_sources", "current_input_hashes",
        } for node in ast.walk(pure)))
        document = latest._document(ROOT)
        relative = latest.LIBRARY
        raw = (ROOT / relative).read_bytes()
        latest._json((ROOT / latest.SPEC).read_bytes())
        with patch.object(latest, "sha", wraps=latest.sha) as hashes:
            latest._raw_payload(relative, raw, document)
            latest._raw_payload(relative, raw, document)
            self.assertEqual(2, sum(call.args == (raw,) for call in hashes.call_args_list))
        for payload in (raw[:-1], raw + b"\n", bytearray(raw)):
            with self.subTest(kind=type(payload).__name__, size=len(payload)), self.assertRaises(ValueError):
                latest._raw_payload(relative, payload, document)


if __name__ == "__main__":
    unittest.main()
