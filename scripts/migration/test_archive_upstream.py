"""Offline exporter regression tests; no GitHub requests and no token access.

Run from the project root:
  python3 -m unittest discover -s scripts/migration -p test_archive_upstream.py -v
"""

import argparse
import contextlib
import hashlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import archive_upstream as exporter


class ExporterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.args = argparse.Namespace(
            output=str(self.root), repository="owner/repo", baseline=exporter.BASELINE,
            workers=2, verify=False, attachment_total_mib=1, attachment_max_mib=1,
            retry_skipped_attachments=False,
        )
        self.archive = exporter.Archive(self.args)

    def tearDown(self):
        self.temporary.cleanup()

    def test_link_header(self):
        headers = {
            "link": '<https://api.github.com/items?page=2>; rel="next", '
                    '<https://api.github.com/items?page=9>; rel="last"'
        }
        self.assertEqual(exporter.next_link(headers), "https://api.github.com/items?page=2")
        self.assertIsNone(exporter.next_link({}))

    def test_rest_all_pages(self):
        seen = []

        def fake_request(path, endpoint, **kwargs):
            seen.append(endpoint)
            if len(seen) == 1:
                return [1, 2], {
                    "success": True,
                    "headers": {"link": '<https://api.github.com/p2>; rel="next"'},
                }
            return [3], {"success": True, "headers": {}}

        self.archive.request = fake_request
        self.assertEqual(self.archive.pages("example", "first"), [1, 2, 3])
        self.assertEqual(seen, ["first", "https://api.github.com/p2"])
        self.assertEqual(self.archive.progress["example"]["pages"], 2)
        self.assertTrue(self.archive.progress["example"]["complete"])

    def test_rest_denial_not_empty_success(self):
        self.archive.request = lambda *args, **kwargs: (
            {"message": "Forbidden"}, {"success": False, "headers": {}}
        )
        self.assertEqual(self.archive.pages("denied", "denied"), [])
        self.assertFalse(self.archive.progress["denied"]["complete"])

    def test_graphql_nested_pagination(self):
        cursors = []

        def fake_request(*args, variables, **kwargs):
            cursors.append(variables["cursor"])
            index = len(cursors)
            return {
                "connection": {
                    "nodes": [index], "totalCount": 3,
                    "pageInfo": {"hasNextPage": index < 3, "endCursor": str(index)},
                }
            }, {"success": True}

        self.archive.request = fake_request
        self.assertEqual(self.archive.graphql_connection("g", "query", {}, lambda result: result["connection"]), [1, 2, 3])
        self.assertEqual(cursors, [None, "1", "2"])
        self.assertTrue(self.archive.progress["graphql/g"]["complete"])

    def test_graphql_count_mismatch(self):
        self.archive.request = lambda *args, **kwargs: (
            {"connection": {"nodes": [1], "totalCount": 2, "pageInfo": {"hasNextPage": False}}},
            {"success": True},
        )
        self.archive.graphql_connection("g", "query", {}, lambda result: result["connection"])
        self.assertFalse(self.archive.progress["graphql/g"]["complete"])

    def test_api_host_allowlist(self):
        for endpoint in ["https://example.com/x", "http://api.github.com/x", "//example.com/x"]:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                self.archive.request("x.json", endpoint)

    def test_verbatim_response_and_cache(self):
        body = b'[ {"body":"\\u00e9", "lines":"a\\nb"} ]\n'
        output = b"HTTP/2.0 200 OK\nContent-Type: application/json\r\nX-Ratelimit-Remaining: 999\r\n\r\n" + body
        response = subprocess.CompletedProcess([], 0, stdout=output, stderr=b"")
        with patch.object(exporter.subprocess, "run", return_value=response) as run:
            data, metadata = self.archive.request("x.json", "repos/owner/repo/issues")
            self.assertTrue(metadata["success"])
            self.assertEqual(data[0]["body"], "é")
            self.assertEqual((self.root / "x.json").read_bytes(), body)
            self.archive.request("x.json", "repos/owner/repo/issues")
            self.assertEqual(run.call_count, 1)
        self.assertEqual(metadata["response_sha256"], hashlib.sha256(body).hexdigest())

    def test_cache_rejects_endpoint_change(self):
        exporter.dump(self.root / "x.json", [])
        exporter.dump(self.root / "x.http.json", {"endpoint": "first"})
        with self.assertRaises(ValueError):
            self.archive.request("x.json", "second")

    def test_cache_rejects_query_change(self):
        exporter.dump(self.root / "x.json", {})
        exporter.dump(self.root / "x.http.json", {"endpoint": "graphql"})
        exporter.dump(self.root / "x.query.json", {"query": "old", "variables": {}})
        with self.assertRaises(ValueError):
            self.archive.request("x.json", "graphql", query="new")

    def test_commit_references_exclude_blob_shas(self):
        data = {
            "head": {"ref": "main", "sha": "a" * 40},
            "file": {"sha": "b" * 40, "url": "https://api.github.com/repos/o/r/contents/file"},
            "original_commit_id": "c" * 40,
            "deployment": {"sha": "d" * 40, "environment": "github-pages", "statuses_url": "https://api.github.com/repos/o/r/deployments/1/statuses"},
            "tree": {"sha": "b" * 40, "url": "https://api.github.com/repos/o/r/git/trees/" + "b" * 40},
        }
        exporter.dump(self.root / "raw.json", data)
        exporter.dump(self.root / "raw.http.json", {
            "success": True, "endpoint": "repos/o/r/pulls/1", "response_body": "raw.json",
        })
        with contextlib.redirect_stdout(io.StringIO()):
            self.archive.references()
        self.assertEqual([item["sha"] for item in exporter.read(self.root / "referenced-commits.json")], ["a" * 40, "c" * 40, "d" * 40])

    def create_manifest(self):
        exporter.dump(self.root / "validation.json", {"checks": {"test": True}})
        lines = [
            f"{exporter.sha256(path)}  {path.relative_to(self.root)}\n"
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and path.name != "SHA256SUMS"
        ]
        (self.root / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")

    def test_integrity_and_tamper(self):
        self.create_manifest()
        with contextlib.redirect_stdout(io.StringIO()):
            exporter.verify_archive(self.root)
        (self.root / "observation.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            exporter.verify_archive(self.root)

    def test_integrity_unlisted_file(self):
        self.create_manifest()
        (self.root / "extra.txt").write_text("unexpected", encoding="utf-8")
        with self.assertRaises(ValueError):
            exporter.verify_archive(self.root)

    def test_rate_reserve_keeps_completed_response(self):
        output = b"HTTP/2.0 200 OK\nX-Ratelimit-Remaining: 79\r\n\r\n[]"
        with patch.object(exporter.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout=output, stderr=b"")):
            with self.assertRaises(RuntimeError):
                self.archive.request("x.json", "repos/owner/repo/issues")
        self.assertTrue((self.root / "x.json").exists())
        self.assertTrue(exporter.read(self.root / "x.http.json")["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
