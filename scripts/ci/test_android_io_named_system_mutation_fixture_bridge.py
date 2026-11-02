"""NEW6 unexecuted AST-only wiring controls for the historical fixture bridge.

Never invoke old controls, the admission helper, Kotlin/resource/UI code or a
model. These inspect only exact fixture helpers and retained method bodies.
A passing guard is source wiring evidence, not native/cloud/receipt acceptance.
"""
import ast
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
REFUSAL = "scripts/ci/test_android_io_named_system_resource_refusal.py"
SELECTORS = "scripts/ci/test_android_io_named_system_documents_ui.py"
NATIVE_UI = "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/NamedSystemDocumentsUi.kt"
EXPECTED_REFUSAL = {'setUp': '0aa6dd08bc153170534395a9ae9ea190bdd2423a5ddc61fc934411669da6bceb', 'replace_ui': 'dbadd42f9fd9e2513e686d072aa69c9d8800281a51b420336764e61f93139464', 'admitted_source_contract': '5afe270bc439586729badfb4765a99882073a28094cf301d36ff6f72300f5732', 'refuses_ui': '8604675b7bf5a5abf5f8b36a005bdf7e6d6835a8eb143949ec9aef4995948528', 'mutations_refused': '278092f134238d9f942d779b3db7ce7d4ea3b76ca292907e58fd126389af59e4', 'test_exact_refusal_source_receipt_still_cannot_certify_native_or_cloud': '46b4eb92e0cd2437595e3cd56950303894df7dd220d1a6a967ccd1cf4991789e', 'test_string_original_name_guard_cannot_be_weakened': '1ea4959c20938beb4ab141b39ab62ea7c74ad9508b9cf90d99219c2261838b2c'}
EXPECTED_SELECTORS = {'setUp': 'b07fa98f9c178c5ad089d9e02e2c874127187d28b5ed48a573f459e704496b3d', 'replace_ui': 'd01768f45f070af158ac32f2ab1490fb5a4f51df655d729f33e5d0ccd013e22a', 'refuses_ui': 'a2d25268edcf927f2770b064053dab6bcbc9ba5cbd3c00b132712d7e8737be46', 'test_runtime_strings_cannot_be_resolved_in_the_id_namespace': '446c74161b38c5d8acb1b86b22fec83045044b220ded5bcda15f2120f8b0aabf'}
UNCHANGED_REFUSAL_TESTS = {'test_exact_refusal_source_receipt_still_cannot_certify_native_or_cloud': '46b4eb92e0cd2437595e3cd56950303894df7dd220d1a6a967ccd1cf4991789e', 'test_id_nonzero_and_exact_original_name_guard_cannot_be_weakened': 'bb30668b32b664044d84b8d87cc0543537fab3b157c2a97fa0cf2f30841bde55', 'test_namespace_cannot_be_guessed_from_admitted_application_id': '7fc9d9bba8a9429cdafbfd09196ab6e4587fb663d5e73b8352de8bff54699275', 'test_diagnostic_cannot_add_an_alternative_control_lookup': '72e156b89bd1b04223eee6cc217a6269a6f316c778db1e99668e7ce596b7d64a', 'test_observation_cannot_execute_before_the_original_lazy_refusal': 'aab5cfcb499f2a9af41ddd69baed1f7016790032fefe0d3da25d8875212b669d', 'test_label_capture_cannot_move_before_existing_system_app_admission': 'd64ca71a3ee27f051d3189d6f99aef6644a1cac68e9366650ccad103b7a2dfea', 'test_raw_package_request_identifier_and_resource_names_cannot_be_exported': '31db29560220e0865c36e8f288b05ac1d44b7d9d04e38dce0ed1bb67a6403820', 'test_diagnostic_getter_exception_cannot_replace_original_failure': '43608adbb0841119949ef34cfaf940f2a24be5f37e4847ab61d714b939a7526a', 'test_zero_identifier_cannot_enter_post_refusal_name_getter': '31979a7bc8430f5053bdf9d08ae0612d225558d56b9d5f5f548914edc320878b', 'test_short_circuited_name_comparison_cannot_be_reported_as_observed_or_true': 'fdb518322066ce2d717f2c676c6cd04920715629b41c373d49e5ecb6bd7243ba', 'test_namespace_categories_require_exact_package_delimiters': 'a09806275733fad7e63a97d09b5a4db317b3a96401dc51d928e70449e5e95bfa', 'test_original_failure_message_prefixes_cannot_be_replaced': '63fcc2d6542139a67a303aa8de2e48af303a53808448dbdfe1bcd37dc7ab65a4'}
UNCHANGED_SELECTOR_TESTS = {'test_corrected_ui_source_receipt_still_cannot_certify_native_or_cloud': '476a31c45ac876b9260807d0f9d1da5b37bca532bb8b0aebad442b5e6db173d7', 'test_owned_row_cannot_be_selected_from_toolbar_instead_of_dir_list': '5056f010acbbb94b0b62117e36e172d2e6ec9a5698833118a66d2ee2d524e901', 'test_document_row_cannot_use_a_guessed_text_control_id': '42339a57794fc1679f6781671c2b439073cae2ba07507bbf512521b9613d873f', 'test_current_directory_cannot_use_unscoped_root_folder_text': '1984e068ad3febf69ab86b75e2f987d71c019dd998673f9671d638f3464594c5', 'test_tree_pick_cannot_revert_to_document_action_mode_menu': '16289ba9e2d7b2fcde4aee26a66ec5c0ab56f5c8b4feaf13055634faa221416e', 'test_tree_pick_must_be_the_enabled_clickable_source_bound_button': '6b3217610b9b573190de21629cc5ba293a086692c7e670703176bf312f5e7945', 'test_confirmation_format_cannot_swap_actual_caller_and_owned_folder': '32c20ef72cf1acba6fd3d275311c1c4c76cad4637c209be87619f37ac7c334aa', 'test_positive_query_cannot_accept_only_one_confirmation_string': 'bd7824d54a80144545c9e4aa27cd480d0af8a2fd8a1babd96cb9e25b51c75021', 'test_allow_action_cannot_use_an_arbitrary_clickable_button': '2054ad7703fe2e0969a1216f24574cf1fe828635fb884eda0e17e7c021d04a0e', 'test_current_directory_container_ambiguity_cannot_be_admitted': 'a877694dc47058a0efef3e526cabb3d5b2ab6262d3fdbff23aaf0dc3eebcf808', 'test_confirmation_must_match_exact_text_instead_of_a_substring': 'a43542ac3715c882d5814691e7ea6a672ec0d876c0db0f2700bda24194379004', 'test_acquired_scope_and_confirmation_nodes_must_be_recycled': '3eb5ed8f2e5f45e70d54bf3c69004c98fbc5f15c0aa3bcf50725e4493de122fd', 'test_acquired_row_parent_must_refresh_before_its_container_identity_is_read': '7ed11e40918779a5742e538826622721e1e27f9f003e0c5d7e3732b4ee289818', 'test_row_click_cannot_omit_explicit_dir_list_containment': '8de97c6a7d5f8def1347e796af7ed4be67b9374693a53d778c9227f9e4994cfc', 'test_parent_ascent_cannot_admit_the_directory_container': '73f06456ace6c148da89532c3e24c3be3932693100df2f0dc72ec142c29a47eb', 'test_refreshed_candidate_cannot_admit_the_directory_container': '65e3ec1d02e8592a485acfa08fecec3e034432d865aa03373a7656f86e26cfd1', 'test_final_row_containment_refusal_cannot_move_after_the_native_click': '36c59de144782ebacd5a0da0dc58e09ef9be6ccebc0a52127588f34ba076e429'}

def methods(relative, classname):
    text = (ROOT / relative).read_text()
    matches = [node for node in ast.parse(text).body if isinstance(node, ast.ClassDef) and node.name == classname]
    if len(matches) != 1:
        raise ValueError("Expected exactly the owning fixture class")
    # Source-segment hashes avoid ast.dump field drift between host Python versions.
    return {node.name: ast.get_source_segment(text, node) for node in matches[0].body if isinstance(node, ast.FunctionDef)}


def method_hash(source_segment):
    return hashlib.sha256(source_segment.encode()).hexdigest()


class NamedSystemMutationFixtureBridgeControls(unittest.TestCase):
    def refusal(self):
        return methods(REFUSAL, "NamedSystemResourceRefusalControls")

    def selectors(self):
        return methods(SELECTORS, "NamedSystemIoUiSelectorControls")

    def test_only_mutations_reconstruct_the_exact_historical_preimage(self):
        found = self.refusal()
        for name in ("setUp", "replace_ui"):
            with self.subTest(fixture_helper=name):
                self.assertEqual(EXPECTED_REFUSAL[name], method_hash(found[name]))

    def test_strict_postimage_precedes_contract_and_restores_the_mutant(self):
        found = self.refusal()
        for name in ("admitted_source_contract", "refuses_ui"):
            with self.subTest(fixture_helper=name):
                self.assertEqual(EXPECTED_REFUSAL[name], method_hash(found[name]))

    def test_unmutated_receipt_and_between_mutation_current_reset_are_unchanged(self):
        found = self.refusal()
        for name in ("test_exact_refusal_source_receipt_still_cannot_certify_native_or_cloud", "mutations_refused"):
            with self.subTest(retained_body=name):
                self.assertEqual(EXPECTED_REFUSAL[name], method_hash(found[name]))

    def test_historical_mutation_bodies_stay_exact_except_owned_refusal_stage(self):
        found = self.refusal()
        for name, expected in UNCHANGED_REFUSAL_TESTS.items():
            with self.subTest(retained_body=name):
                self.assertEqual(expected, method_hash(found[name]))
        name = "test_string_original_name_guard_cannot_be_weakened"
        self.assertEqual(EXPECTED_REFUSAL[name], method_hash(found[name]))

    def test_current_string_role_requires_the_exact_admission_refusal(self):
        found = self.selectors()
        name = "test_runtime_strings_cannot_be_resolved_in_the_id_namespace"
        self.assertEqual(EXPECTED_SELECTORS[name], method_hash(found[name]))
        native = (ROOT / NATIVE_UI).read_text()
        self.assertEqual(1, native.count('val (value, _) = qualifiedResource("string", name)'))
        self.assertEqual(0, native.count('resources.getIdentifier(name, "string", namespace)'))

    def test_other_seventeen_selector_bodies_and_fixture_helpers_are_unchanged(self):
        found = self.selectors()
        for name, expected in UNCHANGED_SELECTOR_TESTS.items():
            with self.subTest(retained_body=name):
                self.assertEqual(expected, method_hash(found[name]))
        for name in ("setUp", "replace_ui", "refuses_ui"):
            with self.subTest(retained_fixture_helper=name):
                self.assertEqual(EXPECTED_SELECTORS[name], method_hash(found[name]))


if __name__ == "__main__":
    unittest.main()
