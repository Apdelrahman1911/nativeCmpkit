"""UNEXECUTED NEW fixed-candidate qualification controls only.

No Kotlin/resource/runtime/provider/grant/native pass is inferred. Do not select
previously accepted NamedSystemResourceRefusalControls or sibling test classes.
"""
from pathlib import Path
import hashlib
import shutil
import tempfile
import unittest

import android_io_named_system_documents as source

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
UI_BEFORE_SHA256 = '9c33fd0b94ea178e7d40985deecfd3a90fc042c03354df4869c2ae812f153b70'
UI_DIAGNOSTIC_DELTAS = (('            "applicationLabelPostRefusalNamespace=${if (label == null) "UNOBSERVED" else resourceNamespaceCategory(resources, label)}"\n', '            "applicationLabelPostRefusalNamespace=${if (label == null) "UNOBSERVED" else resourceNamespaceCategory(resources, label)}" +\n            "," + fixedCandidateResourceQualification(resources, requested)\n'), ('    private fun textIn(root: AccessibilityNodeInfo, containerId: String, expected: String): List<AccessibilityNodeInfo> {\n', '    // A bounded failure-only candidate observation, never a control/namespace admission.\n    private fun fixedCandidateResourceQualification(resources: android.content.res.Resources,\n        requested: String): String = try {\n        // Same Resources instance from the original canonical check; label observations are not authority.\n        val eligible = requested == "id/dir_list" && packageName == "com.google.android.documentsui"\n        val candidateNamespace = "com.google.android.documentsui"\n        val contracts = arrayOf(\n            Triple("DIR_LIST", "id", "dir_list"),\n            Triple("TOOLBAR", "id", "toolbar"),\n            Triple("OPEN_TREE_BUTTON", "string", "open_tree_button"),\n            Triple("OPEN_TREE_DIALOG_TITLE", "string", "open_tree_dialog_title"),\n            Triple("OPEN_TREE_DIALOG_MESSAGE", "string", "open_tree_dialog_message"),\n            Triple("ALLOW", "string", "allow"),\n        )\n        var identifierLookupCount = 0\n        var nameReadbackCount = 0\n        var identifierNonzeroCount = 0\n        var exactFullNameCount = 0\n        val facts = ArrayList<String>(6)\n        for ((category, type, entry) in contracts) {\n            val identifier: Int? = if (eligible) try {\n                identifierLookupCount += 1\n                resources.getIdentifier(entry, type, candidateNamespace)\n            } catch (_: Throwable) {\n                null\n            } else null\n            val nonzero: Boolean? = identifier?.let { it != 0 }\n            if (nonzero == true) identifierNonzeroCount += 1\n            val exactFullNameMatch: Boolean? = if (identifier != null && identifier != 0) try {\n                nameReadbackCount += 1\n                resources.getResourceName(identifier) == "$candidateNamespace:$type/$entry"\n            } catch (_: Throwable) {\n                null\n            } else null\n            if (exactFullNameMatch == true) exactFullNameCount += 1\n            facts += "candidate${category}IdentifierNonzero=$nonzero," +\n                "candidate${category}ExactFullNameMatch=$exactFullNameMatch"\n        }\n        val scope = if (eligible) "GOOGLE_DIR_LIST_REFUSAL" else "NOT_REQUESTED"\n        val namespaceCategory = if (eligible) "GOOGLE_PACKAGE_CANDIDATE" else "NOT_REQUESTED"\n        "candidateQualificationSchema=1,candidateScope=$scope,candidateNamespace=$namespaceCategory," +\n            "candidateContractCount=6,candidateIdentifierLookupCount=$identifierLookupCount," +\n            "candidateNameReadbackCount=$nameReadbackCount,candidateIdentifierNonzeroCount=$identifierNonzeroCount," +\n            "candidateExactFullNameCount=$exactFullNameCount," + facts.joinToString(",")\n    } catch (_: Throwable) {\n        // A diagnostic failure must not replace the original lazy-check IllegalStateException.\n        "candidateQualificationSchema=1,candidateScope=UNAVAILABLE,candidateNamespace=NOT_REQUESTED," +\n            "candidateContractCount=6,candidateIdentifierLookupCount=-1,candidateNameReadbackCount=-1," +\n            "candidateIdentifierNonzeroCount=-1,candidateExactFullNameCount=-1"\n    }\n\n    private fun textIn(root: AccessibilityNodeInfo, containerId: String, expected: String): List<AccessibilityNodeInfo> {\n'))


class NamedSystemFixedCandidateQualificationControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-io55-fixed-candidate-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in source.SOURCE_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY_ROOT / relative, target)

    def replace_ui(self, before, after):
        path = self.root / source.UI
        text = path.read_text()
        self.assertEqual(1, text.count(before), "Exactly the new authored diagnostic boundary must be addressed")
        path.write_text(text.replace(before, after, 1))

    def mutations_refused(self, pairs):
        path = self.root / source.UI
        original = path.read_text()
        for before, after in pairs:
            with self.subTest(new_diagnostic_boundary=before):
                self.replace_ui(before, after)
                with self.assertRaisesRegex(ValueError, "^Refusal-only DocumentsUI resource observations changed$"):
                    source.source_contract(self.root)
                path.write_text(original)

    def reverse_diagnostic_text(self):
        text = (self.root / source.UI).read_text()
        for before, after in reversed(UI_DIAGNOSTIC_DELTAS):
            self.assertEqual(1, text.count(after))
            text = text.replace(after, before, 1)
        self.assertEqual(UI_BEFORE_SHA256, hashlib.sha256(text.encode()).hexdigest())
        return text

    def test_approved_diagnostic_is_exact_reversible_addition_not_native_or_cloud_acceptance(self):
        self.reverse_diagnostic_text()
        receipt = source.source_contract(self.root)
        source.validate_source_receipt(receipt)
        self.assertFalse(receipt["native_success_inferred"])
        self.assertFalse(receipt["cloud_provider_coverage"])
        self.assertFalse(receipt["controlled_helper_needed"])

    def test_new_append_retains_original_canonical_refusal_schema_and_throw_helpers(self):
        text = (self.root / source.UI).read_text()
        baseline = self.reverse_diagnostic_text()
        for literal in (
            'val namespace = "com.android.documentsui"',
            'check(value != 0 && resources.getResourceName(value) == "$namespace:id/$id") {',
            'check(value != 0 && resources.getResourceName(value) == "$namespace:string/$name") {',
            'documentsUiResourceRefusalSchema=1,request=$request,application=$application,',
            'val nameMatchFromRefusal: Boolean? = if (nonzero) false else null',
        ):
            self.assertEqual(baseline.count(literal), text.count(literal))
        source.source_contract(self.root)

    def test_missing_failure_only_call_is_not_a_qualified_draft(self):
        'New helper cannot silently disappear from the old lazy refusal.'
        self.mutations_refused((('            "applicationLabelPostRefusalNamespace=${if (label == null) "UNOBSERVED" else resourceNamespaceCategory(resources, label)}" +\n            "," + fixedCandidateResourceQualification(resources, requested)\n', '            "applicationLabelPostRefusalNamespace=${if (label == null) "UNOBSERVED" else resourceNamespaceCategory(resources, label)}"\n'),))

    def test_candidate_observation_cannot_run_before_the_canonical_check(self):
        'A new scoped helper is not a precheck or success-path observer.'
        self.mutations_refused((('        val value = resources.getIdentifier(id, "id", namespace)\n', '        val value = resources.getIdentifier(id, "id", namespace)\n        fixedCandidateResourceQualification(resources, "id/$id")\n'),))

    def test_only_dir_list_refusal_can_enable_candidate_lookups(self):
        'Toolbar/string/any-id refusal cannot broaden the finite diagnostic trigger.'
        self.mutations_refused((('requested == "id/dir_list"', 'requested == "id/toolbar"'), ('requested == "id/dir_list"', 'requested.startsWith("id/")')))

    def test_only_admitted_google_package_can_enable_candidate_lookups(self):
        'Label namespace, any accepted application or true cannot authorize lookup.'
        self.mutations_refused((('packageName == "com.google.android.documentsui"', 'true'), ('packageName == "com.google.android.documentsui"', 'admittedLabelResource != null')))

    def test_candidate_namespace_is_literal_and_not_derived_from_any_label(self):
        'Fixed candidate namespace is observational and tied to package admission only.'
        self.mutations_refused((('val candidateNamespace = "com.google.android.documentsui"', 'val candidateNamespace = packageName'), ('val candidateNamespace = "com.google.android.documentsui"', 'val candidateNamespace = "com.android.documentsui"')))

    def test_candidate_uses_only_the_original_admitted_resources_instance(self):
        'A target-context/new/foreign Resources table cannot qualify this installed app.'
        self.mutations_refused((('resources.getIdentifier(entry, type, candidateNamespace)', 'instrumentation.targetContext.resources.getIdentifier(entry, type, candidateNamespace)'), ('resources.getIdentifier(entry, type, candidateNamespace)', 'instrumentation.targetContext.packageManager.getResourcesForApplication("com.android.documentsui").getIdentifier(entry, type, candidateNamespace)')))

    def test_six_contract_table_cannot_lose_duplicate_or_add_a_control(self):
        'Exactly two IDs and four string contracts, once each; no discovery/enumeration.'
        self.mutations_refused((('            Triple("ALLOW", "string", "allow"),\n', ''), ('            Triple("ALLOW", "string", "allow"),\n', '            Triple("ALLOW", "string", "allow"),\n            Triple("OTHER", "id", "extra"),\n')))

    def test_all_six_candidate_types_and_entry_names_are_exact(self):
        'One mutation per required contract; category/lookup identities cannot drift.'
        self.mutations_refused((('            Triple("DIR_LIST", "id", "dir_list"),', '            Triple("DIR_LIST", "id", "dir_list_unqualified"),'), ('            Triple("TOOLBAR", "id", "toolbar"),', '            Triple("TOOLBAR", "id", "toolbar_unqualified"),'), ('            Triple("OPEN_TREE_BUTTON", "string", "open_tree_button"),', '            Triple("OPEN_TREE_BUTTON", "string", "open_tree_button_unqualified"),'), ('            Triple("OPEN_TREE_DIALOG_TITLE", "string", "open_tree_dialog_title"),', '            Triple("OPEN_TREE_DIALOG_TITLE", "string", "open_tree_dialog_title_unqualified"),'), ('            Triple("OPEN_TREE_DIALOG_MESSAGE", "string", "open_tree_dialog_message"),', '            Triple("OPEN_TREE_DIALOG_MESSAGE", "string", "open_tree_dialog_message_unqualified"),'), ('            Triple("ALLOW", "string", "allow"),', '            Triple("ALLOW", "string", "allow_unqualified"),')))

    def test_zero_candidate_identifier_cannot_enter_name_readback(self):
        'A zero identifier yields false/nonobserved name comparison, not a getter.'
        self.mutations_refused((('if (identifier != null && identifier != 0) try {', 'if (identifier != null) try {'),))

    def test_candidate_full_name_equality_is_not_a_prefix_or_entry_only_match(self):
        'The exact package:type/entry comparison is required for every nonzero ID.'
        self.mutations_refused((('resources.getResourceName(identifier) == "$candidateNamespace:$type/$entry"', 'resources.getResourceName(identifier).startsWith("$candidateNamespace:")'), ('resources.getResourceName(identifier) == "$candidateNamespace:$type/$entry"', 'resources.getResourceName(identifier).endsWith("/$entry")')))

    def test_identifier_lookup_exception_stays_unobserved_not_zero_or_message_data(self):
        'Getter failure cannot fabricate a zero/nonzero identifier or export error data.'
        self.mutations_refused((('                resources.getIdentifier(entry, type, candidateNamespace)\n            } catch (_: Throwable) {\n                null\n            } else null\n', '                resources.getIdentifier(entry, type, candidateNamespace)\n            } catch (_: Throwable) {\n                0\n            } else null\n'), ('                resources.getIdentifier(entry, type, candidateNamespace)\n            } catch (_: Throwable) {\n                null\n            } else null\n', '                resources.getIdentifier(entry, type, candidateNamespace)\n            } catch (failure: Throwable) {\n                failure.message?.length\n            } else null\n')))

    def test_name_getter_exception_stays_unobserved_not_match_or_mismatch(self):
        'A getter that throws did not complete its exact-name comparison.'
        self.mutations_refused((('                resources.getResourceName(identifier) == "$candidateNamespace:$type/$entry"\n            } catch (_: Throwable) {\n                null\n            } else null\n', '                resources.getResourceName(identifier) == "$candidateNamespace:$type/$entry"\n            } catch (_: Throwable) {\n                false\n            } else null\n'), ('                resources.getResourceName(identifier) == "$candidateNamespace:$type/$entry"\n            } catch (_: Throwable) {\n                null\n            } else null\n', '                resources.getResourceName(identifier) == "$candidateNamespace:$type/$entry"\n            } catch (_: Throwable) {\n                true\n            } else null\n')))

    def test_identifier_count_records_attempt_before_a_throwing_lookup(self):
        'Attempt count must not lose a call that throws before a result.'
        self.mutations_refused((('                identifierLookupCount += 1\n                resources.getIdentifier(entry, type, candidateNamespace)\n', '                val observed = resources.getIdentifier(entry, type, candidateNamespace)\n                identifierLookupCount += 1\n                observed\n'),))

    def test_no_candidate_retry_fallback_or_namespace_scan(self):
        'At most six fixed identifier lookups and six name readbacks; no extra namespace.'
        self.mutations_refused((('resources.getIdentifier(entry, type, candidateNamespace)', 'resources.getIdentifier(entry, type, candidateNamespace).takeIf { it != 0 } ?: resources.getIdentifier(entry, type, "com.android.documentsui")'), ('for ((category, type, entry) in contracts) {', 'for ((category, type, entry) in contracts + contracts) {')))

    def test_exact_match_count_cannot_count_unknown_as_qualified(self):
        'Only a true completed full-name equality contributes to exact-name count.'
        self.mutations_refused((('if (exactFullNameMatch == true) exactFullNameCount += 1', 'if (exactFullNameMatch != false) exactFullNameCount += 1'), ('if (exactFullNameMatch == true) exactFullNameCount += 1', 'if (eligible) exactFullNameCount += 1')))

    def test_new_export_is_fixed_categories_nullable_booleans_and_bounded_counts_only(self):
        'No raw identifiers/resource names/entry names/namespace values or strings.'
        self.mutations_refused((('"candidate${category}IdentifierNonzero=$nonzero,"', '"candidate${category}IdentifierNonzero=$identifier,"'), ('"candidate${category}ExactFullNameMatch=$exactFullNameMatch"', '"candidate${category}ExactFullNameMatch=${resources.getResourceName(identifier ?: 0)}"'), ('candidateNamespace=$namespaceCategory,', 'candidateNamespace=$candidateNamespace,'), ('"candidate${category}IdentifierNonzero=$nonzero,"', '"candidate${entry}IdentifierNonzero=$nonzero,"')))

    def test_outer_diagnostic_failure_cannot_escape_replace_throw_or_export_body(self):
        'Unexpected diagnostic failure is fixed UNAVAILABLE/-1; original check still throws.'
        self.mutations_refused((('    } catch (_: Throwable) {\n        // A diagnostic failure must not replace the original lazy-check IllegalStateException.\n        "candidateQualificationSchema=1,candidateScope=UNAVAILABLE,candidateNamespace=NOT_REQUESTED," +\n            "candidateContractCount=6,candidateIdentifierLookupCount=-1,candidateNameReadbackCount=-1," +\n            "candidateIdentifierNonzeroCount=-1,candidateExactFullNameCount=-1"\n    }\n', '    } catch (failure: Throwable) {\n        throw failure\n    }\n'), ('    } catch (_: Throwable) {\n        // A diagnostic failure must not replace the original lazy-check IllegalStateException.\n        "candidateQualificationSchema=1,candidateScope=UNAVAILABLE,candidateNamespace=NOT_REQUESTED," +\n            "candidateContractCount=6,candidateIdentifierLookupCount=-1,candidateNameReadbackCount=-1," +\n            "candidateIdentifierNonzeroCount=-1,candidateExactFullNameCount=-1"\n    }\n', '    } catch (failure: Throwable) {\n        failure.message.orEmpty()\n    }\n')))

    def test_unsupported_scope_performs_zero_candidate_resource_lookups(self):
        'Non-Google or non-DIR_LIST scope must leave per-control observations null.'
        self.mutations_refused((('val identifier: Int? = if (eligible) try {', 'val identifier: Int? = if (true) try {'),))

    def test_positive_candidate_counts_cannot_bypass_original_canonical_guard(self):
        'Candidate6/6 is information only, never authority to return a replacement control.'
        self.mutations_refused((('        check(value != 0 && resources.getResourceName(value) == "$namespace:id/$id") {\n            resourceRefusal("The exact stock DocumentsUI control resource is unavailable",\n                resources, value, "id/$id")\n        }\n', '        if (value == 0 && fixedCandidateResourceQualification(resources, "id/$id").contains("candidateExactFullNameCount=6")) {\n            return "com.google.android.documentsui:id/$id"\n        }\n        check(value != 0 && resources.getResourceName(value) == "$namespace:id/$id") {\n            resourceRefusal("The exact stock DocumentsUI control resource is unavailable",\n                resources, value, "id/$id")\n        }\n'),))

    def test_new_observer_cannot_touch_ui_flags_grants_or_cleanup(self):
        'Diagnostics may read fixed resource identity only; no native/UI side effects.'
        self.mutations_refused((('        val facts = ArrayList<String>(6)\n', '        val facts = ArrayList<String>(6)\n        automation.serviceInfo = automation.serviceInfo.apply { flags = 0 }\n'), ('        val facts = ArrayList<String>(6)\n', '        val facts = ArrayList<String>(6)\n        instrumentation.uiAutomation.executeShellCommand("anything")\n')))


if __name__ == "__main__":
    unittest.main()
