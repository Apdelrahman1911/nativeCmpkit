import unittest
from github_json import json_pages


class PaginationTests(unittest.TestCase):
    def test_adjacent_pretty_array_pages(self):
        self.assertEqual([[{"n": 1}], [{"n": 2}]], json_pages('[\n {"n":1}\n]\n[{"n":2}]\n'))

    def test_object_pages_and_nested_quoted_braces(self):
        self.assertEqual([{"runs": [{"body": "[]{}"}]}, {"runs": []}], json_pages('{"runs":[{"body":"[]{}"}]}\n{"runs":[]}'))

    def test_empty_stream_and_empty_page_are_distinct(self):
        self.assertEqual([], json_pages(" \n"))
        self.assertEqual([[]], json_pages("[]"))

    def test_invalid_or_scalar_pages_are_rejected(self):
        for source in ('[]oops', '[', '"text"', '123'):
            with self.assertRaises(ValueError): json_pages(source)


if __name__ == "__main__":
    unittest.main()
