"""Offline citation controls; these do not test the Kotlin implementation."""
import unittest

from validate_audit import location_errors


class CitationTests(unittest.TestCase):
    def test_valid_text_ranges(self):
        self.assertEqual([], location_errors({"path": "foo.kt", "lines": "1-2, 3", "symbol": "f"}, b"one\ntwo\nthree\n"))

    def test_invalid_text_bounds(self):
        for lines in ("0", "3", "2-1"):
            self.assertTrue(location_errors({"path": "foo.kt", "lines": lines, "symbol": "f"}, b"one\ntwo\n"))

    def test_symbol_and_line_required(self):
        for data in ({"lines": "1"}, {"symbol": "f"}):
            self.assertTrue(location_errors({"path": "foo.kt", **data}, b"one\n"))

    def test_real_binary_requires_explicit_marker(self):
        blob = b"\x00\x01binary\x00"
        self.assertEqual([], location_errors({"path": "font.ttf", "lines": "binary (entire font file)", "symbol": "Cupertino font"}, blob))
        self.assertTrue(location_errors({"path": "font.ttf", "lines": "1", "symbol": "font"}, blob))

    def test_binary_label_does_not_bypass_text_citation(self):
        self.assertTrue(location_errors({"path": "foo.kt", "lines": "binary", "symbol": "f"}, b"source\n"))

    def test_null_bytes_detect_binary_without_font_suffix(self):
        self.assertEqual([], location_errors({"path": "asset.bin", "lines": "binary", "symbol": "asset"}, b"\x00data"))


if __name__ == "__main__":
    unittest.main()
