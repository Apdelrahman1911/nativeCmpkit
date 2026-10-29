"""Shared real-screen-pair guards; synthetic evidence, not Apple executions."""
from copy import deepcopy
from pathlib import Path
import unittest

import library_tests as tests
import workflow_matrix as matrix


class NativeVectorScreenTests(unittest.TestCase):
    def test_exact_hierarchy_pixels_are_compared_at_the_witnessed_native_screen_density(self):
        source = (tests.ROOT / tests.IOS_VECTOR_THEME_SOURCE).read_text()
        method = source.split("@Test fun " + tests.IOS_VECTOR_THEME_METHODS[0], 1)[1].split("@Test fun ", 1)[0]
        self.assertIn("val nativeDensity = runOnIdle", method)
        self.assertIn("requireOwnedApplicationWindow().screen.scale.toFloat()", method)
        self.assertIn("assertTrue(nativeDensity in listOf(2f, 3f)", method)
        self.assertIn("for (density in listOf(nativeDensity))", method)
        self.assertIn('assertEquals(density.toDouble(), nativeScreenScale, "native-resolution hierarchy capture")', method)
        for original in ("source.indices.forEach { channel ->", "original[channel].toInt() and 255)) <= 3",
                         "for (offset in source.indices step 4)", "actual[offset + channel].toInt() and 255)) <= 3",
                         "UIImageRenderingModeAlwaysOriginal", "UIImageRenderingModeAlwaysTemplate"):
            self.assertIn(original, method)
        self.assertNotIn("return@", method)
        self.assertNotIn("kCAFilterNearest", method)
        self.assertNotIn("Assume.", method)

    def test_both_native_densities_share_one_host_and_compilation_not_accepted_theme_replay(self):
        row, = matrix.matrix("ios-vector-native-screen-pair")["include"]
        self.assertEqual("ios-ipad", row["slot"])
        self.assertEqual("ipad", row["simulator-kind"])
        self.assertEqual("iphone", row["serial-simulator-kind"])
        self.assertEqual("calf-ui", row["test-modules"])
        self.assertEqual(tests.IOS_VECTOR_RENDERING_FOCUS, row["test-focus"])
        self.assertEqual(row["test-focus"], row["serial-test-focus"])
        self.assertEqual(2, len(matrix.preflight_plans("ios-vector-native-screen-pair")["slots"]))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        workflow = (tests.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn('"$PYTHON" scripts/ci/native_vector_screens.py', workflow)
        self.assertIn("steps.serial_runtime.outputs.device", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("packages: write", workflow)

    def rows(self):
        return [dict(density=d, native_screen=d, view=d, layer=d,
                     simulator="device-" + str(d), source_revision="a" * 40,
                     actual_cases=1, passed_cases=1, complete_native_lifecycle=True,
                     original_XML_preserved=True) for d in (2.0, 3.0)]

    def test_pair_requires_two_distinct_exact_native_resolutions_and_complete_actual_results(self):
        import native_vector_screens as screens
        result = screens.validate_pair(self.rows())
        self.assertEqual([2.0, 3.0], result["verified_native_densities"])
        self.assertEqual(2, result["fresh_native_methods"])
        self.assertFalse(result["release_readiness_certified"])

    def test_native_protocol_cannot_pass_without_its_exact_screen_witness(self):
        import ios_ui_application as app
        classname = tests.IOS_VECTOR_THEME_CLASS
        name = tests.IOS_VECTOR_THEME_METHODS[0]
        def protocol():
            p = app.NativeProtocol()
            p.feed("NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2")
            p.feed(f"##teamcity[testSuiteStarted name='{classname}']")
            p.feed(f"##teamcity[testStarted name='{name}']")
            return p
        with self.assertRaises(ValueError): protocol().feed(f"##teamcity[testFinished name='{name}']")
        for density in (2.0, 3.0):
            p = protocol()
            p.feed(f"NATIVECMPKIT_VECTOR_SCALE density={density} nativeScreen={density} view={density} layer={density}")
            p.feed(f"##teamcity[testFinished name='{name}']")
            p.feed(f"##teamcity[testSuiteFinished name='{classname}']")
            p.feed("NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true")
            result = p.finish(0)
            self.assertEqual(1, result["counts"]["passed"])
            self.assertTrue(result["completion"]["worker_terminated"])

    def test_missing_repeated_resampled_failed_or_incomplete_half_cannot_pass(self):
        import native_vector_screens as screens
        bad = [[], self.rows()[:1], self.rows() + self.rows()[:1], list(reversed(self.rows()))]
        for field, value in (("density", 2.0), ("native_screen", 2.0), ("view", 2.0), ("layer", 2.0),
                             ("simulator", "device-2.0"), ("source_revision", "b" * 40),
                             ("passed_cases", 0), ("actual_cases", 0), ("actual_cases", 2),
                             ("complete_native_lifecycle", False), ("original_XML_preserved", False)):
            rows = deepcopy(self.rows()); rows[1][field] = value; bad.append(rows)
        for rows in bad:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                screens.validate_pair(rows)

    def test_unknown_unbounded_boolean_or_nonfinite_scale_fields_are_rejected(self):
        import native_vector_screens as screens
        for field, value in (("density", True), ("density", float("nan")), ("density", 4.0),
                             ("actual_cases", True), ("complete_native_lifecycle", 1),
                             ("source_revision", "main"), ("simulator", "")):
            rows = self.rows(); rows[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                screens.validate_pair(rows)
        rows = self.rows(); rows[0]["unreviewed"] = True
        with self.assertRaises(ValueError): screens.validate_pair(rows)


if __name__ == "__main__":
    unittest.main()
