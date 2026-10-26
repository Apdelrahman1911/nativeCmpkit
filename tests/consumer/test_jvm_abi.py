import copy
import unittest

from jvm_abi import compare, parse_javap
from verify_artifacts import InvalidArtifact


SAMPLE = '''Compiled from "Example.kt"
public final class com.mohamedrejeb.calf.Example {
  public static final int FIELD = 3;
    descriptor: I
  public final java.lang.Object read(kotlin.coroutines.Continuation<? super byte[]>);
    descriptor: (Lkotlin/coroutines/Continuation;)Ljava/lang/Object;
  protected com.mohamedrejeb.calf.Example();
    descriptor: ()V
}
Compiled from "Example.kt"
final class com.mohamedrejeb.calf.Hidden {
  public final void hidden();
    descriptor: ()V
}
'''


class JvmAbiTest(unittest.TestCase):
    def snapshot(self):
        return {"expected_source_revision": "1" * 40, "artifacts": {"nativecmpkit-core-desktop": {"classes": parse_javap(SAMPLE)}}}

    def test_extracts_public_and_protected_descriptors_and_constants(self):
        classes = parse_javap(SAMPLE)
        self.assertEqual(["com.mohamedrejeb.calf.Example"], list(classes))
        self.assertEqual(3, len(classes["com.mohamedrejeb.calf.Example"]["members"]))
        self.assertTrue(any("FIELD = 3" in member["declaration"] for member in classes["com.mohamedrejeb.calf.Example"]["members"]))

    def test_missing_descriptor_rejected(self):
        with self.assertRaises(InvalidArtifact):
            parse_javap('public class a.X {\npublic void f();\n}\n')

    def test_duplicate_class_rejected(self):
        with self.assertRaises(InvalidArtifact):
            parse_javap(SAMPLE + SAMPLE)

    def test_identical_snapshot_no_compatibility_overclaim(self):
        result = compare(self.snapshot(), self.snapshot())
        self.assertTrue(result["no_removed_or_changed_exported_surface"])
        self.assertFalse(result["binary_compatibility_certified"])

    def test_removed_artifact_fails(self):
        after = self.snapshot()
        after["artifacts"] = {}
        self.assertFalse(compare(self.snapshot(), after)["no_removed_or_changed_exported_surface"])

    def test_removed_class_fails(self):
        after = self.snapshot()
        after["artifacts"]["nativecmpkit-core-desktop"]["classes"].clear()
        self.assertFalse(compare(self.snapshot(), after)["no_removed_or_changed_exported_surface"])

    def test_removed_method_fails(self):
        after = self.snapshot()
        after["artifacts"]["nativecmpkit-core-desktop"]["classes"]["com.mohamedrejeb.calf.Example"]["members"].pop()
        self.assertFalse(compare(self.snapshot(), after)["no_removed_or_changed_exported_surface"])

    def test_changed_descriptor_fails(self):
        after = self.snapshot()
        after["artifacts"]["nativecmpkit-core-desktop"]["classes"]["com.mohamedrejeb.calf.Example"]["members"][0]["descriptor"] = "J"
        self.assertFalse(compare(self.snapshot(), after)["no_removed_or_changed_exported_surface"])

    def test_changed_class_hierarchy_requires_review(self):
        after = self.snapshot()
        after["artifacts"]["nativecmpkit-core-desktop"]["classes"]["com.mohamedrejeb.calf.Example"]["declaration"] += " extends Other"
        self.assertFalse(compare(self.snapshot(), after)["no_removed_or_changed_exported_surface"])

    def test_additive_api_keeps_old_surface(self):
        after = self.snapshot()
        after["artifacts"]["nativecmpkit-core-desktop"]["classes"]["com.mohamedrejeb.calf.Example"]["members"].append({"declaration": "public void added();", "descriptor": "()V"})
        result = compare(self.snapshot(), after)
        self.assertTrue(result["no_removed_or_changed_exported_surface"])
        self.assertEqual(1, len(result["additions"]))


if __name__ == "__main__":
    unittest.main()
