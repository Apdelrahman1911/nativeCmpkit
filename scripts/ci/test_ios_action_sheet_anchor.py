"""Finite source contracts for #29; these do not execute Kotlin or UIKit."""

import os
from pathlib import Path
import re
import unittest


SOURCE_ROOT = Path(
    os.environ.get(
        "NATIVECMPKIT_ISSUE29_SOURCE_ROOT",
        str(Path(__file__).resolve().parents[2]),
    )
)
DIALOG_ROOT = Path("calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog")
NATIVE_TEST = Path(
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/"
    "NativePopoverAnchorGeometryTest.kt"
)
MANUAL_MATRIX = Path("docs/testing/ios-action-sheet-anchor.md")


def function_body(source, signature):
    opening = source.index("{", source.index(signature))
    depth = 1
    cursor = opening + 1
    while cursor < len(source):
        character = source[cursor]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1 : cursor]
        cursor += 1
    raise AssertionError(f"Unclosed source function: {signature}")


class IosActionSheetAnchorSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = (SOURCE_ROOT / DIALOG_ROOT / "AlertDialogManager.kt").read_text()
        cls.anchor = (
            SOURCE_ROOT / DIALOG_ROOT / "uikit/AlertDialogIosPopoverAnchor.kt"
        ).read_text()
        cls.adaptive = (
            SOURCE_ROOT / DIALOG_ROOT / "AdaptiveAlertDialog.ios.kt"
        ).read_text()
        cls.native_test = (SOURCE_ROOT / NATIVE_TEST).read_text()
        cls.manual_matrix = (SOURCE_ROOT / MANUAL_MATRIX).read_text()

    def test_request_and_uikit_prepare_both_resolve_current_anchor(self):
        show = function_body(self.manager, "fun showAlertDialog(")
        self.assertLess(
            show.index("configurePopoverPresentation()"),
            show.index("parentUIViewController.presentViewController("),
        )
        prepare = function_body(self.manager, "override fun prepareForPopoverPresentation(")
        self.assertLess(
            prepare.index("if (!ownsPopover(popoverPresentationController)) return"),
            prepare.index("applyPopoverAnchor("),
        )
        self.assertIn("requireMain()", prepare)
        self.assertIn("popoverAnchor.resolveFor(parentUIViewController)", prepare)

    def test_reposition_validates_ownership_and_complete_pointer_pair(self):
        reposition = function_body(self.manager, "override fun popoverPresentationController(")
        self.assertLess(
            reposition.index("if (!ownsPopover(popoverPresentationController)) return"),
            reposition.index("popoverAnchor.resolveFor(parentUIViewController)"),
        )
        self.assertLess(
            reposition.index("willRepositionPopoverToRect == null || inView == null"),
            reposition.index("willRepositionPopoverToRect.pointed"),
        )
        self.assertIn("inView.pointed.value = anchor.view", reposition)

    def test_resolver_rejects_foreign_windows_and_missing_sources(self):
        resolution = function_body(self.anchor, "internal fun AlertDialogIosPopoverAnchor?.resolveFor(")
        self.assertIn("NSThread.isMainThread", resolution)
        self.assertIn("window != null", resolution)
        self.assertIn("view.window?.objcPtr() == window.objcPtr()", resolution)
        self.assertIn("validRectInBounds(rect, bounds)", resolution)
        self.assertIn("item.customView == null || inCurrentWindow(item.customView)", resolution)
        self.assertIn("rect = fallbackCenterRect(presenter.bounds())", resolution)
        self.assertIn("arrows = 0uL", resolution)

    def test_geometry_validation_keeps_finite_nonempty_local_bounds(self):
        validation = function_body(self.anchor, "private fun validRectInBounds(")
        for expression in (
            "!left.isFinite()",
            "!bottom.isFinite()",
            "size.width > 0.0",
            "size.height > 0.0",
            "origin.x >= left",
            "origin.y >= top",
            "origin.x + size.width <= right",
            "origin.y + size.height <= bottom",
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, validation)

    def test_selected_action_updates_modal_policy_before_user_callback(self):
        action = function_body(self.manager, "internal fun actionInvoked(")
        self.assertLess(action.index("actionChosen ="), action.index("configureActionSheetDismissal()"))
        self.assertLess(action.index("configureActionSheetDismissal()"), action.index("action.onClick()"))
        dismissal = function_body(self.manager, "internal fun configureActionSheetDismissal(")
        self.assertIn(
            "dialogUIViewController.modalInPresentation=!actionChosen&&!properties.dismissOnClickOutside",
            re.sub(r"\s+", "", dismissal),
        )
        selected = function_body(
            self.native_test,
            "fun chosenActionSheetActionDoesNotEmitAnAdditionalDismissCallback(",
        )
        self.assertLess(
            selected.index("assertTrue(manager.dialogUIViewController.modalInPresentation)"),
            selected.index("manager.actionInvoked("),
        )
        self.assertGreater(
            selected.index("assertFalse(manager.dialogUIViewController.modalInPresentation)"),
            selected.index("manager.actionInvoked("),
        )

    def test_alert_style_cannot_acquire_action_sheet_delegation(self):
        for signature in (
            "internal fun configurePopoverPresentation(",
            "internal fun configureActionSheetDismissal(",
        ):
            with self.subTest(signature=signature):
                body = function_body(self.manager, signature)
                self.assertLess(
                    body.index("if (iosProperties.style != AlertDialogIosStyle.ActionSheet) return"),
                    body.index("configureActionSheetDismissal()")
                    if "configureActionSheetDismissal()" in body
                    else body.index("dialogUIViewController.modalInPresentation"),
                )

    def test_both_adaptive_composables_propagate_anchor_on_create_and_update(self):
        self.assertEqual(2, self.adaptive.count("val popoverAnchor = LocalAlertDialogIosPopoverAnchor.current"))
        self.assertEqual(2, self.adaptive.count("it.popoverAnchor = popoverAnchor"))
        self.assertEqual(2, self.adaptive.count("alertDialogManager.popoverAnchor = popoverAnchor"))

    def test_new_native_regressions_remain_controlled_not_presented(self):
        for name in (
            "prepareRevalidatesChangedBoundsAndDetachedSourcesBeforePresentation",
            "prepareIgnoresForeignPopoversWithoutChangingEitherAnchor",
            "foreignWindowSourceUsesTheCurrentPresentersFallback",
        ):
            with self.subTest(name=name):
                self.assertIn(f"fun {name}()", self.native_test)
        self.assertEqual(17, len(re.findall(r"@Test\s+fun\s+", self.native_test)))
        self.assertNotIn(".presentViewController(", self.native_test)
        self.assertNotIn(".showAlertDialog(", self.native_test)

    def test_original_manual_matrix_and_unproven_native_status_remain(self):
        for phrase in (
            "Portrait, regular width",
            "Landscape, regular width",
            "Split View",
            "compact width",
            "Missing/detached source",
            "No alert\nis presented",
            "Until then `#29` remains open",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.manual_matrix)


if __name__ == "__main__":
    unittest.main()
