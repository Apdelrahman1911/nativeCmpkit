"""Small regression tests for the lexical inventory, not library runtime tests."""

import json
import unittest

import source_inventory as inventory


class SourceInventoryTest(unittest.TestCase):
    def test_mask_preserves_offsets_and_nested_comments(self):
        source = '''// class Fake
/* outer val hidden = 1 /* nested fun hidden() */ still comment */
val visible = "fun notCode()" + """class NotCode""" + 'x'
'''
        clean = inventory.masked(source)
        self.assertEqual(len(source), len(clean))
        self.assertEqual(
            [i for i, char in enumerate(source) if char == "\n"],
            [i for i, char in enumerate(clean) if char == "\n"],
        )
        self.assertEqual(
            [(d["kind"], d["name"], d["line"]) for d in inventory.declarations(source, ".kt")],
            [("val", "visible", 3)],
        )

    def test_generic_extension_function(self):
        result = inventory.declarations(
            "public inline fun <T : Any> List<T>.choose(index: Int): T = this[index]", ".kt"
        )
        self.assertEqual(result[0]["name"], "choose")
        self.assertEqual(result[0]["modifiers"], ["public", "inline"])

    def test_extension_property(self):
        result = inventory.declarations("val List<String>.firstSize: Int get() = first().length", ".kt")
        self.assertEqual([(d["kind"], d["name"]) for d in result], [("val", "firstSize")])

    def test_actual_typealias(self):
        result = inventory.declarations("actual typealias PlatformContext = Context", ".kt")
        self.assertEqual(result[0]["kind"], "typealias")
        self.assertEqual(result[0]["name"], "PlatformContext")
        self.assertEqual(result[0]["modifiers"], ["actual"])

    def test_class_literal_is_not_a_class_declaration(self):
        result = inventory.declarations("val type = String::class\nclass Real", ".kt")
        self.assertEqual([(d["kind"], d["name"]) for d in result], [("val", "type"), ("class", "Real")])

    def test_unnamed_companion_object(self):
        result = inventory.declarations("class Host {\n companion object { }\n}", ".kt")
        self.assertEqual(result[1]["kind"], "object")
        self.assertEqual(result[1]["name"], "Companion")
        self.assertIn("companion", result[1]["modifiers"])

    def test_xcode_shell_is_not_the_sample_root_project(self):
        self.assertEqual(
            inventory.module_for("sample/ios/iosApp/ContentView.swift", ["", "sample", "sample/common"]),
            "sample/ios",
        )

    def test_build_manifests_and_native_implementation_have_separate_owners(self):
        self.assertEqual(inventory.owner_for("calf-file-picker/native/Cargo.toml"), "audit_build")
        self.assertEqual(inventory.owner_for("calf-file-picker/native/src/lib.rs"), "audit_io_picker")

    def test_baseline_rust_and_xcode_classification(self):
        data = json.loads((inventory.ROOT / "docs/audit/source-inventory.json").read_text())
        files = {item["path"]: item for item in data["files"]}
        self.assertIsNone(files["calf-file-picker/native/src/lib.rs"]["source_set"])
        xcode = [item for item in files.values() if item["path"].startswith("sample/ios/")]
        self.assertTrue(xcode)
        self.assertTrue(all(item["module"] == "sample/ios" and not item["included_in_gradle"] for item in xcode))


if __name__ == "__main__":
    unittest.main()
