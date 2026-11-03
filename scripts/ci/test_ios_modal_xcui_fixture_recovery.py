# SPDX-License-Identifier: Apache-2.0
"""Two new source-fixture regressions; ZERO SDK/compiler/native work."""
import ast
import unittest

from test_apple_appinfo_shape_route import unique_finally_guard


class ModalXcuiFixtureRecoveryControls(unittest.TestCase):
    def test_wk_cleanup_selection_survives_unrelated_guards_before_and_after_it(self):
        for guards in (
            "if request_fixture is not None: request_fixture.close()",
            "if native_input_driver is not None: native_input_driver.close()\n"
            "if request_fixture is not None: request_fixture.close()\n"
            "if appearance_driver is not None: appearance_driver.restore()",
        ):
            source = "try:\n    pass\nfinally:\n" + "\n".join("    " + line for line in guards.splitlines()) + "\n"
            finalbody = ast.parse(source).body[0].finalbody
            selected = unique_finally_guard(source, finalbody, "request_fixture is not None")
            self.assertEqual("request_fixture.close()", ast.get_source_segment(source, selected.body[0]))

    def test_missing_duplicate_nested_or_changed_wk_guards_never_select_another_owner(self):
        for guards in (
            "if native_input_driver is not None: native_input_driver.close()",
            "if request_fixture is not None: request_fixture.close()\n"
            "if request_fixture is not None: request_fixture.close()",
            "if native_input_driver is not None:\n    if request_fixture is not None: request_fixture.close()",
            "if request_fixture is None: request_fixture.close()",
        ):
            source = "try:\n    pass\nfinally:\n" + "\n".join("    " + line for line in guards.splitlines()) + "\n"
            with self.subTest(guards=guards), self.assertRaisesRegex(ValueError, "One exact authored cleanup guard required"):
                unique_finally_guard(source, ast.parse(source).body[0].finalbody, "request_fixture is not None")


if __name__ == "__main__":
    unittest.main()
