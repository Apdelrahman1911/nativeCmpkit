"""UNEXECUTED NEW application-specific resource-admission source controls only.

No Android Resources lookup, Kotlin compilation, provider/UI/grant/native pass or
cloud coverage is inferred. The isolated runner selects only this new class; it
never imports or executes the historical accepted resource22 class.
"""
from pathlib import Path
import ast
import hashlib
import shutil
import tempfile
import unittest

import android_io_named_system_documents as source

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ORIGINAL154_UI_SHA256 = "03a0ebc37215c4b86043f253f4e83b7db39c7fd52652d9ea735e6e7c106ea1dc"
HISTORICAL_BASE_UI_SHA256 = "9c33fd0b94ea178e7d40985deecfd3a90fc042c03354df4869c2ae812f153b70"
HISTORICAL_CONTROLS = "scripts/ci/test_android_io_named_system_resource_qualification.py"
FROZEN_RETAINED_SOURCE_SHA256 = {
    source.TEST: "ec15772e36b8d5676d9d98a5742f38c3b97b85c51123f27637f50a7238ca4909",
    source.CALLER: "760634c61aa94ffb04b16f94fc20ceb67f4c58aa06477ee6dde14c3dda24fdde",
    source.DESCRIPTOR: "941c43e90bd8d32f113b3dc0b863b4885459a4f17716825eb26ffbf8b320a78a",
    source.MANIFEST: "397d45d9201637e6a696b3c4148376bb02fe5c4bb1070c541616bdcdaefeeb19",
}
ROLES = (
    ("DIR_LIST", "id", "dir_list"),
    ("TOOLBAR", "id", "toolbar"),
    ("OPEN_TREE_BUTTON", "string", "open_tree_button"),
    ("OPEN_TREE_DIALOG_TITLE", "string", "open_tree_dialog_title"),
    ("OPEN_TREE_DIALOG_MESSAGE", "string", "open_tree_dialog_message"),
    ("ALLOW", "string", "allow"),
)


class NamedSystemResourceAdmissionControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-io55-admission-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in source.SOURCE_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY_ROOT / relative, target)

    def current_ui(self):
        return (self.root / source.UI).read_text()

    def mutations_refused(self, pairs):
        path = self.root / source.UI
        original = path.read_text()
        for before, after in pairs:
            with self.subTest(admission_boundary=before):
                self.assertEqual(1, original.count(before), "Exactly one new admission fragment must be targeted")
                path.write_text(original.replace(before, after, 1))
                try:
                    with self.assertRaisesRegex(ValueError, "^Application-specific DocumentsUI resource admission changed$"):
                        source.source_contract(self.root)
                finally:
                    path.write_text(original)

    def test_complete_literal_app_contract_is_source_only_not_native_or_cloud(self):
        ui = self.current_ui()
        self.assertEqual(6, len(ROLES))
        for request, kind, entry in ROLES:
            self.assertEqual(1, ui.count(f'            Triple("{request}", "{kind}", "{entry}"),'))
        receipt = source.source_contract(self.root)
        source.validate_source_receipt(receipt)
        self.assertFalse(receipt["native_success_inferred"])
        self.assertFalse(receipt["cloud_provider_coverage"])
        self.assertFalse(receipt["controlled_helper_needed"])

    def test_no_missing_duplicate_or_extra_role_in_complete_contract(self):
        self.mutations_refused((
            ('            Triple("ALLOW", "string", "allow"),\n', ''),
            ('            Triple("ALLOW", "string", "allow"),\n',
             '            Triple("ALLOW", "string", "allow"),\n            Triple("ALLOW", "string", "allow"),\n'),
            ('            Triple("ALLOW", "string", "allow"),\n',
             '            Triple("ALLOW", "string", "allow"),\n            Triple("OTHER", "id", "extra"),\n'),
        ))

    def test_each_six_role_type_and_entry_is_exact(self):
        pairs = []
        for request, kind, entry in ROLES:
            before = f'            Triple("{request}", "{kind}", "{entry}"),'
            pairs.append((before, f'            Triple("{request}", "{kind}_wrong", "{entry}"),'))
            pairs.append((before, f'            Triple("{request}", "{kind}", "{entry}_wrong"),'))
        self.mutations_refused(pairs)

    def test_app_namespace_mapping_cannot_mix_or_swap_complete_contracts(self):
        self.mutations_refused((
            ('            "com.android.documentsui" -> "com.android.documentsui"',
             '            "com.android.documentsui" -> "com.google.android.documentsui"'),
            ('            "com.google.android.documentsui" -> "com.google.android.documentsui"',
             '            "com.google.android.documentsui" -> "com.android.documentsui"'),
            ('        val namespace = when (packageName) {', '        val namespace = packageName; when (packageName) {'),
        ))

    def test_unknown_application_is_refused_before_any_resources_lookup(self):
        ui = self.current_ui()
        self.assertLess(ui.index('else -> error("DocumentsUI resource application refused;application=OTHER_REFUSED")'),
                        ui.index('getResourcesForApplication(packageName)'))
        self.mutations_refused((
            ('            else -> error("DocumentsUI resource application refused;application=OTHER_REFUSED")',
             '            else -> "com.google.android.documentsui"'),
        ))

    def test_label_framework_or_prefix_namespace_is_never_admission_authority(self):
        ui = self.current_ui()
        self.assertNotIn('admittedLabelResource', ui)
        self.assertNotIn('app.labelRes', ui)
        self.mutations_refused((
            ('            "com.google.android.documentsui" -> "com.google.android.documentsui"',
             '            "com.google.android.documentsui" -> "android"'),
            ('        val namespace = when (packageName) {',
             '        val namespace = instrumentation.targetContext.packageManager.getApplicationInfo(packageName, 0).labelRes.toString(); when (packageName) {'),
        ))

    def test_same_resources_object_no_foreign_table_retry_or_namespace_scan(self):
        self.mutations_refused((
            ('instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)',
             'instrumentation.targetContext.resources'),
            ('instrumentation.targetContext.packageManager.getResourcesForApplication(packageName)',
             'instrumentation.targetContext.packageManager.getResourcesForApplication("com.android.documentsui")'),
            ('            resources.getIdentifier(entry, type, namespace)',
             '            resources.getIdentifier(entry, type, namespace).takeIf { it != 0 } ?: resources.getIdentifier(entry, type, "com.android.documentsui")'),
        ))

    def test_zero_or_throwing_identifier_cannot_be_admitted(self):
        self.mutations_refused((
            ('        check(nonzero == true && exactFullNameMatch == true) {',
             '        check(exactFullNameMatch != false) {'),
            ('            resources.getIdentifier(entry, type, namespace)\n        } catch (_: Throwable) {\n            null\n',
             '            resources.getIdentifier(entry, type, namespace)\n        } catch (_: Throwable) {\n            1\n'),
            ('        val nonzero: Boolean? = value?.let { it != 0 }',
             '        val nonzero: Boolean? = value?.let { true }'),
        ))

    def test_full_package_type_entry_equality_not_prefix_suffix_or_entry_only(self):
        self.mutations_refused((
            ('        val exactFullNameMatch: Boolean? = fullName?.let { it == "$namespace:$type/$entry" }',
             '        val exactFullNameMatch: Boolean? = fullName?.let { it.startsWith("$namespace:") }'),
            ('        val exactFullNameMatch: Boolean? = fullName?.let { it == "$namespace:$type/$entry" }',
             '        val exactFullNameMatch: Boolean? = fullName?.let { it.endsWith("/$entry") }'),
            ('        val exactFullNameMatch: Boolean? = fullName?.let { it == "$namespace:$type/$entry" }',
             '        val exactFullNameMatch: Boolean? = fullName?.let { it == entry }'),
        ))

    def test_zero_missing_or_throwing_name_readback_remains_unqualified(self):
        self.mutations_refused((
            ('        val fullName: String? = if (nonzero == true) try {',
             '        val fullName: String? = if (true) try {'),
            ('            resources.getResourceName(checkNotNull(value))\n        } catch (_: Throwable) {\n            null\n',
             '            resources.getResourceName(checkNotNull(value))\n        } catch (_: Throwable) {\n            "$namespace:$type/$entry"\n'),
            ('        check(nonzero == true && exactFullNameMatch == true) {',
             '        check(nonzero != false && exactFullNameMatch != false) {'),
        ))

    def test_only_all_six_completed_checks_publish_the_owned_contract(self):
        self.mutations_refused((
            ('        for ((request, type, entry) in contracts) {\n            readQualifiedResource(resources, namespace, request, type, entry)\n        }',
             '        admittedResourceContract = ResourceContract(resources, namespace)\n        for ((request, type, entry) in contracts) {\n            readQualifiedResource(resources, namespace, request, type, entry)\n        }'),
            ('        for ((request, type, entry) in contracts) {\n            readQualifiedResource(resources, namespace, request, type, entry)\n        }',
             '        for ((request, type, entry) in contracts.take(1)) {\n            readQualifiedResource(resources, namespace, request, type, entry)\n        }'),
            ('        check(admittedResourceContract == null) { "DocumentsUI resource contract was already qualified" }',
             '        if (admittedResourceContract != null) return'),
        ))

    def test_qualification_has_constructed_finally_owner_before_any_ui_selection(self):
        ui = self.current_ui()
        test = (self.root / source.TEST).read_text()
        self.assertLess(test.index('ui = NamedSystemDocumentsUi('), test.index('ui.selectOwnedFolder(seed.folder)'))
        self.assertIn('attempt { ui?.close() }', test)
        self.assertLess(ui.index('        qualifyResourceContract()'), ui.index('        click({ root ->'))
        old = source._RESOURCE_ADMISSION_SELECT_SOURCE
        moved = old.replace('        qualifyResourceContract()\n', '')
        self.mutations_refused(((old, moved),))
        original = self.current_ui()
        path = self.root / source.UI
        path.write_text(original.replace('        qualifyResourceContract()\n', '', 1).replace('    init {\n', '    init {\n        qualifyResourceContract()\n', 1))
        try:
            with self.assertRaisesRegex(ValueError, "^Application-specific DocumentsUI resource admission changed$"):
                source.source_contract(self.root)
        finally:
            path.write_text(original)

    def test_each_consumer_rechecks_only_the_complete_admitted_resources_and_role(self):
        self.mutations_refused((
            ('        val contract = checkNotNull(admittedResourceContract) { "DocumentsUI resource contract is unqualified" }',
             '        val contract = admittedResourceContract ?: ResourceContract(instrumentation.targetContext.resources, packageName)'),
            ('        return readQualifiedResource(contract.resources, contract.namespace, request, type, entry)',
             '        return readQualifiedResource(contract.resources, "com.android.documentsui", request, type, entry)'),
            ('            else -> error("DocumentsUI resource role refused;request=OTHER_REFUSED")',
             '            else -> "DIR_LIST"'),
            ('    private fun resource(id: String): String = qualifiedResource("id", id).second',
             '    private fun resource(id: String): String = "com.google.android.documentsui:id/$id"'),
        ))

    def test_formatted_strings_keep_arguments_blank_and_size_refusals(self):
        self.mutations_refused((
            ('            resources.getString(value, *arguments)', '            resources.getString(value)'),
            ('            check(it.isNotBlank() && it.length <= 1024) { "Exact admitted DocumentsUI string value refused" }',
             '            check(it.length <= 4096) { "Exact admitted DocumentsUI string value refused" }'),
            ('            error("Exact admitted DocumentsUI string unavailable;request=STRING_VALUE")',
             '            "Allow"'),
        ))

    def test_new_refusal_is_fixed_categories_booleans_no_raw_ids_names_or_bodies(self):
        self.mutations_refused((
            ('            "declaredNamespace=$declaredNamespace,identifierNonzero=$nonzero,"',
             '            "declaredNamespace=$namespace,identifierNonzero=$nonzero,"'),
            ('            "exactFullNameMatch=$exactFullNameMatch"',
             '            "exactFullNameMatch=$request:$namespace"'),
            ('            resources.getIdentifier(entry, type, namespace)\n        } catch (_: Throwable) {\n            null\n',
             '            resources.getIdentifier(entry, type, namespace)\n        } catch (failure: Throwable) {\n            failure.message?.length\n'),
            ('            resourceAdmissionRefusal(request, namespace, nonzero, exactFullNameMatch)',
             '            "raw=$value,name=$fullName"'),
        ))

    def test_original_native_selectors_callback_grants_IO_and_cleanup_are_exact_bytes(self):
        original154 = source.resource_admission_preimage(self.current_ui())
        self.assertEqual(ORIGINAL154_UI_SHA256, hashlib.sha256(original154.encode()).hexdigest())
        for relative, expected in FROZEN_RETAINED_SOURCE_SHA256.items():
            self.assertEqual(expected, hashlib.sha256((self.root / relative).read_bytes()).hexdigest())
        self.assertEqual(self.current_ui(), source.resource_admission_postimage(original154))
        # No historical tests are executed by this exact-byte preservation control.
        self.assertIn('flags = originalFlags', original154)
        self.assertIn('candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK)', original154)

    def test_historical22_reconstruction_retains_original_canonical_hash_and_mutations(self):
        original154 = source.resource_admission_preimage(self.current_ui())
        tree = ast.parse((REPOSITORY_ROOT / HISTORICAL_CONTROLS).read_text())
        constants = {}
        historical_methods = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in {"UI_BEFORE_SHA256", "UI_RESOURCE_REFUSAL_POST154_SHA256", "UI_DIAGNOSTIC_DELTAS"}:
                    constants[node.targets[0].id] = ast.literal_eval(node.value)
            if isinstance(node, ast.ClassDef) and node.name == "NamedSystemFixedCandidateQualificationControls":
                historical_methods = [item.name for item in node.body if isinstance(item, ast.FunctionDef) and item.name.startswith("test_")]
        self.assertEqual(22, len(historical_methods))
        self.assertEqual(HISTORICAL_BASE_UI_SHA256, constants["UI_BEFORE_SHA256"])
        self.assertEqual(ORIGINAL154_UI_SHA256, constants["UI_RESOURCE_REFUSAL_POST154_SHA256"])
        baseline = original154
        for before, after in reversed(constants["UI_DIAGNOSTIC_DELTAS"]):
            self.assertEqual(1, baseline.count(after))
            baseline = baseline.replace(after, before, 1)
        self.assertEqual(HISTORICAL_BASE_UI_SHA256, hashlib.sha256(baseline.encode()).hexdigest())
        canonical = 'check(value != 0 && resources.getResourceName(value) == "$namespace:id/$id")'
        self.assertEqual(1, original154.count(canonical))
        with self.assertRaisesRegex(ValueError, "^Refusal-only DocumentsUI resource observations changed$"):
            source.resource_admission_postimage(original154.replace(canonical, 'check(true)', 1))
        # ast inspection only: the historical class is never imported or executed.

    def test_old_only_and_partial_or_duplicate_admission_shapes_are_refused(self):
        path = self.root / source.UI
        current = path.read_text()
        original154 = source.resource_admission_preimage(current)
        partial = original154.replace(source.RESOURCE_ADMISSION_DELTAS[0][0], source.RESOURCE_ADMISSION_DELTAS[0][1], 1)
        for candidate in (original154, partial, current + source._RESOURCE_ADMISSION_SOURCE):
            with self.subTest(shape="old-only-partial-duplicate"):
                path.write_text(candidate)
                try:
                    with self.assertRaisesRegex(ValueError, "^Application-specific DocumentsUI resource admission changed$"):
                        source.source_contract(self.root)
                finally:
                    path.write_text(current)


if __name__ == "__main__":
    unittest.main()
