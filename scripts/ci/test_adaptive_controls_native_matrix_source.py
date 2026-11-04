"""NEW lexical ownership/matrix controls only; not library, iOS or native executions."""
import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "calf-ui/src"


def source(relative):
    return (BASE / relative).read_text()


def methods(text):
    return re.findall(r"@Test\s+fun\s+(\w+)\s*\(", text)


class AdaptiveControlsNativeMatrixSourceTests(unittest.TestCase):
    def test_common_thumb_uses_all_four_current_caller_colors_without_new_public_api(self):
        text = source("commonMain/kotlin/com/mohamedrejeb/calf/ui/toggle/CupertinoSwitch.kt")
        self.assertIn("CompositionLocalProvider(LocalContentColor provides iconColor)", text)
        for field in ("checkedIconColor", "uncheckedIconColor", "disabledCheckedIconColor", "disabledUncheckedIconColor"):
            self.assertIn("colors." + field, text)
        self.assertIn("if (thumbContent != null)", text)
        self.assertIn("fun CupertinoSwitch(", text)
        self.assertNotIn("remember { iconColor", text)

    def test_real_os_host_requires_main_owned_application_and_fails_wrong_branch(self):
        text = source("iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlNativeHost.kt")
        self.assertIn("val version = onApplicationMain", text)
        self.assertIn("requireOwnedApplicationWindow()", text)
        self.assertIn("UIDevice.currentDevice.systemVersion", text)
        self.assertIn("assertNotNull(version.split('.').firstOrNull()?.toIntOrNull()", text)
        self.assertIn("assertTrue(major > 0", text)
        self.assertIn("major < 26 else major >= 26", text)
        self.assertNotIn("?: 0", text)
        self.assertNotIn("@Test", text)

    def test_slider_selects_only_public_real_inputs_for_all_twelve_rows_and_negative_contract(self):
        text = source("iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt")
        self.assertEqual([
            "pre26PublicStepsTapDragAndAccessibilityMatrix", "ios26PublicStepsTapDragAndAccessibilityMatrix",
            "pre26PublicNegativeStepsAreRejected", "ios26PublicNegativeStepsAreRejected",
        ], methods(text))
        for fragment in ("listOf(0, 1, 3)", "listOf(-2f..2f, 4f..12f)",
                         "listOf(LayoutDirection.Ltr, LayoutDirection.Rtl)", "AdaptiveSlider(value.value",
                         "valueRange = range, steps = steps", "interactionSource = source",
                         "performTouchInput", "swipe(", "SemanticsActions.SetProgress",
                         "ProgressBarRangeInfo", "requested.all { it in allowed }",
                         "assertEquals(\"steps should be >= 0\", failure.message"):
            self.assertIn(fragment, text)
        self.assertNotIn("CupertinoSlider(", text)
        self.assertNotIn("LiquidGlassSliderImpl(", text)
        self.assertNotIn("SliderValueDomain(", text)
        negative = text.split("private fun rejectsNegativeSteps", 1)[1]
        self.assertLess(negative.index("requireAdaptiveControlHost(branch)"), negative.index("assertFailsWith<IllegalArgumentException>"))

    def test_slider_requires_positive_paired_drag_and_finite_bounded_callbacks(self):
        text = source("iosTest/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSliderNativeMatrixTest.kt")
        for fragment in ("events.filterIsInstance<DragInteraction.Start>().size == 1",
                         "events.filterIsInstance<DragInteraction.Stop>().size == 1",
                         "requested.size > beforeDrag", "it.start === drag",
                         "requested.all { it.isFinite() && it in range }",
                         "assertFalse(it(target)", "assertFalse(it(Float.NaN)"):
            self.assertIn(fragment, text)
        self.assertNotIn("down(", text)  # Complete swipe, no held-pointer assertion teardown.

    def test_customization_uses_both_real_branches_and_actual_pixels_text_and_supplied_sources(self):
        text = source("iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/AdaptiveControlCustomizationMatrixTest.kt")
        self.assertEqual([
            "pre26CustomColorsContentAndInteractionsSurviveDarkAndLargeText",
            "ios26CustomColorsContentAndInteractionsSurviveDarkAndLargeText",
        ], methods(text))
        for fragment in ("requireAdaptiveControlHost(branch)", "listOf(false, true)", "row(branch, dark, 1f)",
                         "row(branch, dark, 2f)", "Density(originalDensity, fontScale)", "label.height",
                         "AdaptiveButton(", "AdaptiveIconButton(", "AdaptiveSlider(", "AdaptiveSwitch(",
                         "shape = RectangleShape", "contentPadding = PaddingValues", "thumbContent =",
                         "captureToImage().toPixelMap()", "PressInteraction.Release", "DragInteraction.Stop",
                         "assertThumbGlyph(Color.Blue", "Disabled custom controls cannot emit"):
            self.assertIn(fragment, text)

    def test_toolbar_proves_only_its_authored_material_rows_and_owning_desktop_regression_is_new(self):
        toolbar = source("iosTest/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbarFallbackNativeTest.kt")
        self.assertEqual([
            "pre26EmptyAndPopulatedItemsRenderMaterialSlotsAndCallerPlacement",
            "ios26EmptyItemsRenderMaterialSlotsAndCallerPlacement",
        ], methods(toolbar))
        for fragment in ("includePopulatedItems = true", "includePopulatedItems = false", "AdaptiveToolbar(expanded.value",
                         "UIKitUIBarButtonItem.title", "expanded.value = false", "mainCompositions > beforeCollapsed",
                         "toolbarBounds.bottom <= bottomBounds.top", "assertWidthIsEqualTo(268.dp)"):
            self.assertIn(fragment, toolbar)
        desktop = source("desktopTest/kotlin/com/mohamedrejeb/calf/ui/toggle/CupertinoSwitchThumbContentColorTest.kt")
        self.assertEqual(2, len(methods(desktop)))
        for fragment in ("CupertinoSwitch(checked.value", "listOf(false, true)", "assertEquals(inherited, siblingColor",
                         "fontScale = 2f", "captureToImage().toPixelMap()"):
            self.assertIn(fragment, desktop)

    def test_accepted_first_eight_liquid_bodies_are_byte_identical_and_compile_script_is_opt_in(self):
        text = source("iosTest/kotlin/com/mohamedrejeb/calf/ui/controls/LiquidGlassControlTest.kt")
        prefix = text.split("    @Test fun cancellationAcceptanceSecondPointerHandoffCommitsOnlyAtTheFinalUp()", 1)[0]
        self.assertEqual("e6d841ab255b36ea60652d1df04ee49c49cd8ab86d0c291f63305637c0f40e91",
                         hashlib.sha256(prefix.encode()).hexdigest())
        self.assertEqual(8, len(methods(prefix)))
        init = (ROOT / "scripts/ci/adaptive_controls_compile.init.gradle.kts").read_text()
        self.assertIn("getCommandLineIncludePatterns", init)
        self.assertIn("gradle.startParameter.taskNames == desktopRequest", init)
        self.assertIn("listOf(\":calf-ui:compileTestKotlinIosSimulatorArm64\")", init)
        self.assertIn("actual.files.map { it.canonicalFile }.toSet() == files.toSet()", init)
        self.assertNotIn("binaries.test", init)
        self.assertNotIn("dependsOn(", init)


if __name__ == "__main__":
    unittest.main()
