"""New UI selector source controls only; old eight controls must not be replayed.

These do not compile Kotlin, run DocumentsUI, select providers or certify native/cloud behavior.
"""
from pathlib import Path
import shutil
import tempfile
import unittest

import android_io_named_system_documents as source
from android_io_named_button_rendering import (
    rendering_present, rendering_preimage, rendering_fixture_postimage,
)


class NamedSystemIoUiSelectorControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-io55-ui-source-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        original = Path(__file__).resolve().parents[2]
        for relative in source.SOURCE_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / relative, target)

    def replace_ui(self, before, after):
        path = self.root / source.UI
        text = path.read_text()
        if rendering_present(text):
            text = rendering_preimage(text)
        self.assertEqual(1, text.count(before), "A selector mutation must address exactly its authored boundary")
        path.write_text(rendering_fixture_postimage(text.replace(before, after, 1)))

    def refuses_ui(self):
        with self.assertRaisesRegex(ValueError, "^System UI ownership, exact controls, ambiguity refusal or flag restoration changed$"):
            source.source_contract(self.root)

    def test_corrected_ui_source_receipt_still_cannot_certify_native_or_cloud(self):
        receipt = source.source_contract(self.root)
        source.validate_source_receipt(receipt)
        self.assertFalse(receipt["native_success_inferred"])
        self.assertFalse(receipt["cloud_provider_coverage"])
        self.assertFalse(receipt["controlled_helper_needed"])

    def test_owned_row_cannot_be_selected_from_toolbar_instead_of_dir_list(self):
        self.replace_ui('textIn(root, resource("dir_list"), folder)',
                        'textIn(root, resource("toolbar"), folder)')
        self.refuses_ui()

    def test_document_row_cannot_use_a_guessed_text_control_id(self):
        self.replace_ui('it.viewIdResourceName == "android:id/title" && it.text?.toString() == folder',
                        'it.viewIdResourceName == "android:id/text1" && it.text?.toString() == folder')
        self.refuses_ui()

    def test_current_directory_cannot_use_unscoped_root_folder_text(self):
        self.replace_ui('textIn(root, resource("toolbar"), folder)',
                        'root.findAccessibilityNodeInfosByText(folder)')
        self.refuses_ui()

    def test_tree_pick_cannot_revert_to_document_action_mode_menu(self):
        self.replace_ui('val pickLabel = stringResource("open_tree_button")',
                        'val pickLabel = resource("action_menu_select")')
        self.refuses_ui()

    def test_tree_pick_must_be_the_enabled_clickable_source_bound_button(self):
        self.replace_ui('it.text?.toString() == pickLabel && it.isEnabled && it.isClickable',
                        'it.text?.toString() == pickLabel')
        self.refuses_ui()

    def test_confirmation_format_cannot_swap_actual_caller_and_owned_folder(self):
        self.replace_ui('stringResource("open_tree_dialog_title", callerLabel, folder)',
                        'stringResource("open_tree_dialog_title", folder, callerLabel)')
        self.refuses_ui()

    def test_positive_query_cannot_accept_only_one_confirmation_string(self):
        self.replace_ui('if (hasExactText(root, dialogTitle) && hasExactText(root, dialogMessage))',
                        'if (hasExactText(root, dialogTitle) || hasExactText(root, dialogMessage))')
        self.refuses_ui()

    def test_allow_action_cannot_use_an_arbitrary_clickable_button(self):
        self.replace_ui('it.text?.toString() == allowLabel && it.isEnabled && it.isClickable',
                        'it.isEnabled && it.isClickable')
        self.refuses_ui()

    def test_runtime_strings_cannot_be_resolved_in_the_id_namespace(self):
        self.replace_ui('qualifiedResource("string", name)',
                        'qualifiedResource("id", name)')
        with self.assertRaisesRegex(ValueError, "^Application-specific DocumentsUI resource admission changed$"):
            source.source_contract(self.root)

    def test_current_directory_container_ambiguity_cannot_be_admitted(self):
        self.replace_ui('check(selectedContainers.size <= 1)', 'check(selectedContainers.size <= 2)')
        self.refuses_ui()

    def test_confirmation_must_match_exact_text_instead_of_a_substring(self):
        self.replace_ui('it.text?.toString() == expected', 'it.text?.toString()?.contains(expected) == true')
        self.refuses_ui()

    def test_acquired_scope_and_confirmation_nodes_must_be_recycled(self):
        for before, after in (
            ('finally { containers.forEach { it.recycle() } }', 'finally { containers.clear() }'),
            ('finally { texts.forEach { it.recycle() } }', 'finally { texts.clear() }'),
        ):
            with self.subTest(boundary=before):
                original = (self.root / source.UI).read_text()
                self.replace_ui(before, after)
                self.refuses_ui()
                (self.root / source.UI).write_text(original)


    def test_acquired_row_parent_must_refresh_before_its_container_identity_is_read(self):
        self.replace_ui('check(candidate.refresh() && candidate.isVisibleToUser && candidate.packageName?.toString() == packageName)',
                        'check(candidate.packageName?.toString() == packageName)')
        self.refuses_ui()

    def test_row_click_cannot_omit_explicit_dir_list_containment(self):
        self.replace_ui('}, enclosingContainer = resource("dir_list"))', '}, enclosingContainer = null)')
        self.refuses_ui()

    def test_parent_ascent_cannot_admit_the_directory_container(self):
        self.replace_ui('check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {\n                                        "An owned DocumentsUI row ascent must not reach dir_list or higher"\n                                    }',
                        'check(enclosingContainer == null || candidate.viewIdResourceName == enclosingContainer) {\n                                        "An owned DocumentsUI row ascent must not reach dir_list or higher"\n                                    }')
        self.refuses_ui()

    def test_refreshed_candidate_cannot_admit_the_directory_container(self):
        self.replace_ui('check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {\n                                    "The refreshed DocumentsUI container is not an owned row action"\n                                }',
                        'check(enclosingContainer == null || candidate.viewIdResourceName == enclosingContainer) {\n                                    "The refreshed DocumentsUI container is not an owned row action"\n                                }')
        self.refuses_ui()

    def test_final_row_containment_refusal_cannot_move_after_the_native_click(self):
        path = self.root / source.UI
        text = path.read_text()
        boundary = '                                check(enclosingContainer == null || candidate.viewIdResourceName != enclosingContainer) {\n                                    "The refreshed DocumentsUI container is not an owned row action"\n                                }\n'
        action = "                                check(candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK))\n"
        self.assertEqual(1, text.count(boundary))
        self.assertEqual(1, text.count(action))
        text = text.replace(boundary, "", 1).replace(action, action + boundary, 1)
        path.write_text(text)
        self.refuses_ui()


if __name__ == "__main__":
    unittest.main()
