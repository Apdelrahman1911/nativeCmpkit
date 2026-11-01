"""Eight new synthetic source controls only; not Android/native/SDK functionality tests."""
from pathlib import Path
import shutil
import tempfile
import unittest

import android_io_named_system_documents as source


class NamedSystemIoSourceControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-io55-named-source-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        original = Path(__file__).resolve().parents[2]
        for relative in source.SOURCE_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / relative, target)

    def replace(self, relative, before, after):
        path = self.root / relative
        value = path.read_text()
        self.assertEqual(1, value.count(before), "A synthetic mutation must address exactly its authored boundary")
        path.write_text(value.replace(before, after, 1))

    def refuses(self):
        with self.assertRaises(ValueError):
            source.source_contract(self.root)

    def test_exact_two_enabled_methods_bind_sources_without_native_or_cloud_certificate(self):
        receipt = source.source_contract(self.root)
        source.validate_source_receipt(receipt)
        self.assertEqual(35, receipt["verification_api_level"])
        self.assertFalse(receipt["native_success_inferred"])
        self.assertFalse(receipt["cloud_provider_coverage"])
        self.assertFalse(receipt["controlled_helper_needed"])

    def test_selected_native_method_cannot_be_disabled(self):
        self.replace(source.TEST, "@Test fun " + source.METHODS[0], "@org.junit.Ignore @Test fun " + source.METHODS[0])
        self.refuses()

    def test_implicit_system_acquisition_cannot_be_replaced_with_injected_uri_grant(self):
        self.replace(source.CALLER, "startActivityForResult(intent, REQUEST_CODE)", "grantUriPermission(packageName, initialParent, 1)")
        self.refuses()

    def test_owned_insertion_receipt_cannot_move_after_the_potentially_failing_write(self):
        self.replace(source.TEST, "row = uri // Retain the actual insertion receipt before any potentially failing operation.",
                     "// Lost insertion ownership before write")
        self.refuses()

    def test_conditional_owned_item_delete_cannot_become_unconditional(self):
        self.replace(source.TEST, "contentResolver.delete(uri, identityWhere, identityArgs)", "contentResolver.delete(uri, null, null)")
        self.refuses()

    def test_wrong_result_authority_cannot_be_queried_before_admission(self):
        self.replace(source.TEST, 'check(tree.scheme == "content" && tree.authority == authority',
                     'check(tree.scheme == "content" && true')
        self.refuses()

    def test_explicit_raw_source_close_owner_and_actual_child_identity_are_required(self):
        self.replace(source.TEST, "child.source(context).use { source ->", "child.source(context).let { source ->")
        self.refuses()

    def test_ambiguous_system_controls_cannot_be_clicked(self):
        self.replace(source.UI, "check(selected.size <= 1)", "check(selected.size <= 2)")
        self.refuses()


if __name__ == "__main__":
    unittest.main()
