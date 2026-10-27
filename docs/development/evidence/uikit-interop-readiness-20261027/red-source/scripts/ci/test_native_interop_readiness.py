"""Guards for two observed UIKit fixture failures; zero native tests executed."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
DROPDOWN = ROOT / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dropdown/NativeDropDownLifecycleTest.kt"
TIME = ROOT / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/timepicker/NativeTimePickerTest.kt"


class NativeInteropReadinessTest(unittest.TestCase):
    def test_dropdown_waits_for_one_real_attached_interop_view_before_lookup(self):
        source = DROPDOWN.read_text()
        self.assertIn("val button = parent.view.menuButtons().singleOrNull()", source)
        self.assertIn("button != null && sameNativeObject(button.window, parent.view.window)", source)
        self.assertLess(source.index("waitForNative {"), source.index("button = parent.view.menuButtons().single()"))

    def test_time_picker_waits_for_real_attached_initial_and_replacement_views(self):
        source = TIME.read_text()
        self.assertIn("picker != null && sameNativeObject(picker.window, parent.view.window)", source)
        self.assertLess(source.index("waitForNative {"), source.index("oldPicker = parent.view.datePickers().single()"))
        self.assertIn("!sameNativeObject(oldPicker, picker) && oldPicker?.window == null", source)
        self.assertLess(source.index("!sameNativeObject(oldPicker, picker)"), source.index("val components = calendar.components"))

    def test_native_pointer_identity_and_detachment_strengthen_existing_assertions(self):
        source = TIME.read_text()
        self.assertIn("assertFalse(sameNativeObject(oldPicker, picker))", source)
        self.assertIn("assertNull(oldPicker?.window)", source)
        self.assertIn("assertNotSame(oldPicker, picker)", source)

    def test_intended_real_menu_and_value_changed_functionality_is_not_removed(self):
        dropdown, time = DROPDOWN.read_text(), TIME.read_text()
        for call in ("button.isMenuPresented", "expanded = false", "expanded = true",
                     "button.contextMenuInteraction?.dismissMenu()", "dismissals == 1 && !button.isMenuPresented"):
            self.assertIn(call, dropdown)
        for call in ("picker.sendActionsForControlEvents(UIControlEventValueChanged)",
                     "assertEquals(1, first.hour)", "assertEquals(2, first.minute)",
                     "assertEquals(14, second.hour)", "assertEquals(35, second.minute)"):
            self.assertIn(call, time)

    def test_tests_still_use_the_real_application_and_fail_closed(self):
        for path in (DROPDOWN, TIME):
            source = path.read_text()
            self.assertIn("= runApplicationUiTest {", source)
            for forbidden in ("Thread.sleep(", "delay(", "@Ignore", "Assume.", "mockk(", "return@runApplicationUiTest"):
                self.assertNotIn(forbidden, source)
        helper = (ROOT / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt").read_text()
        self.assertIn('awaitMain("native predicate") { predicate() }', helper)
        self.assertIn('error("Timed out awaiting $phase;', helper)


if __name__ == "__main__":
    unittest.main()
