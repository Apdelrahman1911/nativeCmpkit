"""Offline regression tests for current catalogue generation, not OS font availability."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("icon_catalogues", Path(__file__).with_name("generate_icon_catalogues.py"))
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class IconCatalogueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.cupertino, cls.symbols = generator.load_inputs()
        cls.glyphs = generator.unicode_glyphs((generator.ROOT / cls.manifest["font"]["path"]).read_bytes())

    def test_generated_current_sources_match_reviewed_inputs(self):
        for path, text in generator.render(self.cupertino, self.symbols).items():
            self.assertEqual((generator.ROOT / path).read_bytes(), text.encode(), str(path))

    def test_generated_sample_keeps_categories_used_by_the_catalogue_screen(self):
        output = generator.render(self.cupertino, self.symbols)[generator.SAMPLE]
        categories = sorted({entry["category"] for entry in self.cupertino})
        expected = "internal val IconCategories: List<String> = listOf(\n" + "".join(
            f'    "{category}",\n' for category in categories
        ) + ")\n"
        self.assertIn(expected, output)
        self.assertEqual(1, output.count("internal val IconCategories:"))
        baseline = subprocess.check_output(
            ["git", "show", self.manifest["baseline"] + ":" + str(generator.SAMPLE)],
            cwd=generator.ROOT,
        ).decode()
        self.assertIn(expected, baseline)

    def test_all_generated_outputs_preserve_exact_modification_notice_once(self):
        notice = "// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.\n"
        outputs = generator.render(self.cupertino, self.symbols)
        self.assertEqual({generator.CUPERTINO, generator.SAMPLE, generator.SF}, set(outputs))
        for path, text in outputs.items():
            with self.subTest(path=str(path)):
                self.assertTrue(text.startswith(notice + "@file:"))
                self.assertEqual(1, text.count(notice))

    def test_every_original_public_constant_is_retained_exactly(self):
        for path, pattern in [(generator.CUPERTINO, r"const val (`?\w+`?): Int = (0x[0-9A-F]+)"),
                              (generator.SF, r'const val (`?\w+`?) = "([^"]+)"')]:
            baseline = subprocess.check_output(["git", "show", self.manifest["baseline"] + ":" + str(path)], cwd=generator.ROOT).decode()
            self.assertEqual(re.findall(pattern, baseline), re.findall(pattern, (generator.ROOT / path).read_text()))

    def test_each_cupertino_mapping_has_an_actual_nonzero_unicode_glyph(self):
        self.assertEqual(1322, len(self.cupertino))
        self.assertEqual(1234, len({entry["codepoint"] for entry in self.cupertino}))
        self.assertTrue(all(entry["codepoint"] in self.glyphs for entry in self.cupertino))

    def test_duplicate_identifier_and_missing_glyph_are_rejected(self):
        data = copy.deepcopy(self.cupertino)
        data[1]["identifier"] = data[0]["identifier"]
        with self.assertRaises(ValueError):
            generator.validate_records(data, self.symbols, self.glyphs)
        data = copy.deepcopy(self.cupertino)
        data[0]["codepoint"] = 0x10ffff
        with self.assertRaises(ValueError):
            generator.validate_records(data, self.symbols, self.glyphs)

    def test_missing_catalogue_assignment_is_rejected(self):
        data = copy.deepcopy(self.cupertino)
        data[1]["catalogue_index"] = data[0]["catalogue_index"]
        with self.assertRaises(ValueError):
            generator.validate_records(data, self.symbols, self.glyphs)

    def test_kotlin_injection_or_invalid_system_name_is_rejected(self):
        data = copy.deepcopy(self.symbols)
        data[0]["identifier"] = "bad;fun injected()"
        with self.assertRaises(ValueError):
            generator.validate_records(self.cupertino, data, self.glyphs)
        data = copy.deepcopy(self.symbols)
        data[0]["system_name"] = '" + secret + "'
        with self.assertRaises(ValueError):
            generator.validate_records(self.cupertino, data, self.glyphs)

    def test_unverified_os_versions_cannot_turn_into_support_promises(self):
        self.assertEqual(6984, len(self.symbols))
        self.assertTrue(all(entry["introduced_ios"] is None for entry in self.symbols))
        data = copy.deepcopy(self.symbols)
        data[0]["introduced_ios"] = "13.0"
        with self.assertRaises(ValueError):
            generator.validate_records(self.cupertino, data, self.glyphs)

    def test_modified_input_is_rejected_before_generation(self):
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-catalogue-test-") as tmp:
            root = Path(tmp)
            shutil.copytree(generator.ROOT / generator.INPUTS, root / generator.INPUTS)
            path = root / generator.INPUTS / "cupertino.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "Input hash mismatch"):
                generator.load_inputs(root)


if __name__ == "__main__":
    unittest.main()
