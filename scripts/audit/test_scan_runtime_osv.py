#!/usr/bin/env python3
"""Offline fixtures; no network or Gradle execution."""
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("scan_runtime_osv", Path(__file__).with_name("scan_runtime_osv.py"))
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


class RuntimeOsvTests(unittest.TestCase):
    def graph(self, components):
        return {"schema_version": 1, "configurations": [{"components": components}]}

    def test_exact_sorted_unique_maven_identities_only(self):
        module = {"kind": "module", "group": "example", "module": "library", "version": "1.2.3"}
        graph = self.graph([module, module, {"kind": "project"}, {"kind": "opaque"},
                            {"kind": "module", "group": "a", "module": "b", "version": "2"}])
        self.assertEqual(scan.queries_from_graph(graph), [
            {"package": {"ecosystem": "Maven", "name": "a:b"}, "version": "2"},
            {"package": {"ecosystem": "Maven", "name": "example:library"}, "version": "1.2.3"}])

    def test_empty_or_unknown_graph_is_not_a_clean_scan(self):
        with self.assertRaises(ValueError):
            scan.queries_from_graph(self.graph([]))
        with self.assertRaises(ValueError):
            scan.queries_from_graph({"schema_version": 999})

    def test_invalid_coordinate_rejected(self):
        for value in [None, "", "contains whitespace", "contains/path", "contains:colon"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                scan.queries_from_graph(self.graph([{
                    "kind": "module", "group": "a", "module": "b", "version": value}]))

    def test_batch_alignment_and_request_payload(self):
        submitted = []
        def request(path, payload):
            self.assertEqual(path, "/querybatch")
            submitted.extend(payload["queries"])
            return {"results": [{"fixture": q} for q in payload["queries"]]}
        self.assertEqual(scan.query_batches([1, 2, 3], request, batch_size=2),
                         [{"fixture": 1}, {"fixture": 2}, {"fixture": 3}])
        self.assertEqual(submitted, [1, 2, 3])

    def test_malformed_batch_response_fails(self):
        for reply in [{}, {"results": []}, {"results": [None]}, {"results": [{}, {}]}]:
            with self.subTest(reply=reply), self.assertRaises(ValueError):
                scan.query_batches([1], lambda *_: reply)

    def test_invalid_batch_size_rejected(self):
        for size in [0, -1, 1001]:
            with self.subTest(size=size), self.assertRaises(ValueError):
                scan.query_batches([], batch_size=size)

    def test_paginated_reply_is_not_reported_complete(self):
        with self.assertRaisesRegex(ValueError, "pagination"):
            scan.query_batches([1], lambda *_: {"results": [
                {"vulns": [{"id": "GHSA-fixture"}], "next_page_token": "fixture-page"}]})


if __name__ == "__main__":
    unittest.main()
