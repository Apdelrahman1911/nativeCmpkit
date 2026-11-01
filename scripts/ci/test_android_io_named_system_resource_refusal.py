"""Historical refusal-only DocumentsUI mutation obligations.

Only a mutation reconstructs the exact old helper text. Its strict postimage
bridge checks current admission before returning a source receipt; old text
is never a runtime admission. Select only the12 failed mutation methods, not
the unchanged accepted receipt control. No Kotlin/resource/provider/native pass.
"""
from pathlib import Path
import hashlib
import shutil
import tempfile
import unittest

import android_io_named_system_documents as source

UI_RESOURCE_REFUSAL_POST154_SHA256 = '03a0ebc37215c4b86043f253f4e83b7db39c7fd52652d9ea735e6e7c106ea1dc'


class NamedSystemResourceRefusalControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-io55-resource-refusal-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        original = Path(__file__).resolve().parents[2]
        for relative in source.SOURCE_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / relative, target)

    def replace_ui(self, before, after):
        path = self.root / source.UI
        # Current mandatory admission is checked before reconstructing old mutation text.
        text = source.resource_admission_preimage(path.read_text())
        self.assertEqual(UI_RESOURCE_REFUSAL_POST154_SHA256, hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(1, text.count(before), "A mutation must address exactly its authored boundary")
        path.write_text(text.replace(before, after, 1))

    def admitted_source_contract(self):
        # Never overwrite an inexact legacy obligation or accept an old-only root.
        path = self.root / source.UI
        historical = path.read_text()
        current = source.resource_admission_postimage(historical)
        path.write_text(current)
        try:
            return source.source_contract(self.root)
        finally:
            path.write_text(historical)

    def refuses_ui(self, message="Refusal-only DocumentsUI resource observations changed"):
        with self.assertRaisesRegex(ValueError, "^" + message + "$"):
            self.admitted_source_contract()

    def mutations_refused(self, pairs):
        path = self.root / source.UI
        original = path.read_text()
        for before, after in pairs:
            with self.subTest(boundary=before):
                self.replace_ui(before, after)
                self.refuses_ui()
                path.write_text(original)

    def test_exact_refusal_source_receipt_still_cannot_certify_native_or_cloud(self):
        receipt = source.source_contract(self.root)
        source.validate_source_receipt(receipt)
        self.assertFalse(receipt["native_success_inferred"])
        self.assertFalse(receipt["cloud_provider_coverage"])
        self.assertFalse(receipt["controlled_helper_needed"])

    def test_id_nonzero_and_exact_original_name_guard_cannot_be_weakened(self):
        self.replace_ui('check(value != 0 && resources.getResourceName(value) == "$namespace:id/$id") {',
                        'check(resources.getResourceName(value) == "$namespace:id/$id") {')
        self.refuses_ui()

    def test_string_original_name_guard_cannot_be_weakened(self):
        self.replace_ui('check(value != 0 && resources.getResourceName(value) == "$namespace:string/$name") {',
                        'check(value != 0) {')
        self.refuses_ui("Refusal-only DocumentsUI resource observations changed")

    def test_namespace_cannot_be_guessed_from_admitted_application_id(self):
        self.replace_ui('        val namespace = "com.android.documentsui"\n        val resources = instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)\n        val value = resources.getIdentifier(id, "id", namespace)',
                        '        val namespace = packageName\n        val resources = instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)\n        val value = resources.getIdentifier(id, "id", namespace)')
        self.refuses_ui()

    def test_diagnostic_cannot_add_an_alternative_control_lookup(self):
        self.replace_ui("        val nonzero = value != 0",
                        '        resources.getIdentifier("dir_list", "id", packageName)\n        val nonzero = value != 0')
        self.refuses_ui()

    def test_observation_cannot_execute_before_the_original_lazy_refusal(self):
        self.replace_ui('        val value = resources.getIdentifier(id, "id", namespace)\n',
                        '        val value = resources.getIdentifier(id, "id", namespace)\n        resourceRefusal("early", resources, value, "id/$id")\n')
        self.refuses_ui()

    def test_label_capture_cannot_move_before_existing_system_app_admission(self):
        boundary = "        check(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)\n        admittedLabelResource = app.labelRes\n"
        self.replace_ui(boundary, "        admittedLabelResource = app.labelRes\n        check(app.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)\n")
        self.refuses_ui()

    def test_raw_package_request_identifier_and_resource_names_cannot_be_exported(self):
        self.mutations_refused((
            ('application=$application,', 'application=$packageName,'),
            ('request=$request,', 'request=$requested,'),
            ('canonicalIdentifierNonzero=$nonzero,', 'canonicalIdentifierNonzero=$value,'),
            ('"canonicalPostRefusalNamespace=${resourceNamespaceCategory(resources, value)},"',
             '"canonicalPostRefusalNamespace=${resources.getResourceName(value)},"'),
        ))

    def test_diagnostic_getter_exception_cannot_replace_original_failure(self):
        self.replace_ui('"UNAVAILABLE" // Preserve the original IllegalStateException and its fixed message prefix.',
                        'error("diagnostic getter failed")')
        self.refuses_ui()

    def test_zero_identifier_cannot_enter_post_refusal_name_getter(self):
        self.replace_ui('        if (value == 0) return "ZERO_IDENTIFIER"\n', "")
        self.refuses_ui()

    def test_short_circuited_name_comparison_cannot_be_reported_as_observed_or_true(self):
        self.mutations_refused((
            ("val nameMatchFromRefusal: Boolean? = if (nonzero) false else null",
             "val nameMatchFromRefusal: Boolean? = if (nonzero) false else false"),
            ("val nameMatchFromRefusal: Boolean? = if (nonzero) false else null",
             "val nameMatchFromRefusal: Boolean? = if (nonzero) true else null"),
        ))

    def test_namespace_categories_require_exact_package_delimiters(self):
        self.mutations_refused((
            ('name.startsWith("com.android.documentsui:")', 'name.startsWith("com.android.documentsui")'),
            ('name.startsWith("com.google.android.documentsui:")', 'name.startsWith("com.google.android.documentsui")'),
            ('name.startsWith("android:")', 'name.startsWith("android")'),
        ))

    def test_original_failure_message_prefixes_cannot_be_replaced(self):
        self.mutations_refused((
            ('resourceRefusal("The exact stock DocumentsUI control resource is unavailable",',
             'resourceRefusal("substitute control accepted",'),
            ('resourceRefusal("The exact stock DocumentsUI string resource is unavailable",',
             'resourceRefusal("substitute string accepted",'),
        ))


if __name__ == "__main__":
    unittest.main()
