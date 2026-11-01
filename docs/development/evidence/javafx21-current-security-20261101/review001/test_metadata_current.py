"""Eight new private consistency models; no advisory queries or native evidence."""
import json
from pathlib import Path
import unittest

FACTS=json.loads((Path(__file__).resolve().parent/'review-facts.json').read_text())

class JavaFx21CurrentMetadataModels(unittest.TestCase):
    def test_six_current_metadata_versions_align_and_exclude_global_early_access(self):
        self.assertEqual('21.0.13',FACTS['current_pin'])
        metadata=FACTS['six_module_maven_metadata']
        self.assertEqual(6,len(metadata))
        self.assertEqual({'base','graphics','controls','media','web','swing'},
            {row['module'].split('-')[-1] for row in metadata})
        for row in metadata:
            with self.subTest(module=row['module']):
                self.assertEqual(FACTS['current_pin'],row['highest_stable_21'])
                self.assertIn('21.0.13',row['stable21_versions'])
                self.assertNotIn('28-ea+12',row['stable21_versions'])
                self.assertEqual('28-ea+12',row['global_latest'])
                self.assertFalse(row['available_stable21_0_14'])

    def test_current_development_branch_is_not_a_release_but_still_targets_java17(self):
        source=FACTS['upstream_21_branch']
        self.assertTrue(source['line_is_21'])
        self.assertEqual('21.0.14',source['development_version'])
        self.assertEqual('17',source['minimum_build_jdk'])
        self.assertEqual('17',source['runtime_java_target'])
        self.assertEqual('17',FACTS['required_jdk'])
        self.assertTrue(source['unreleased_branch_is_not_update_candidate'])
        self.assertTrue(source['mutable_branch_not_pinned_release_or_binary_proof'])
        self.assertTrue(FACTS['candidate']['not_using_global_EA_or_development21_0_14'])

    def test_reused_exact_thirty_classifier_artifacts_and_ten_java17_samples_keep_scope(self):
        registry=FACTS['reused_registry']
        self.assertEqual(30,registry['artifact_module_classifier_pairs'])
        self.assertEqual(['linux','linux-aarch64','mac','mac-aarch64','win'],registry['required_classifiers'])
        self.assertEqual((10,61),(registry['classfile_samples'],registry['sampled_major']))
        self.assertEqual(0,registry['new_classifier_HEAD_or_binary_downloads'])
        self.assertTrue(registry['sampled_classfiles_are_not_all_loaded_bytecode_or_native_support'])

    def test_original_media19_advisory_is_low_conditional_and_fixed_on21_branch(self):
        advisory=FACTS['baseline_advisory']
        self.assertEqual('GHSA-47g3-mf24-6559',advisory['id'])
        self.assertEqual('CVE-2024-20925',advisory['cve'])
        self.assertEqual(('LOW','3.1'),(advisory['severity'],advisory['cvss31']))
        self.assertTrue(advisory['old_version19_explicitly_affected'])
        self.assertEqual('21.0.2',advisory['fixed_21_branch_minimum'])
        self.assertTrue(advisory['current21_0_13_outside_this_retained_range'])
        self.assertIn('Successful attacks require human interaction',advisory['details'])
        self.assertIn('rely on the Java sandbox for security',advisory['details'])
        self.assertTrue(advisory['not_proof_of_current_complete_advisory_status'])

    def test_vendor_javafx_matrix_scoping_does_not_confuse_same_cve_other_product(self):
        baseline=[row for row in FACTS['oracle_javafx_risk_matrix_rows']['oracle-cpujan2024']
            if row['cve']=='CVE-2024-20925']
        self.assertEqual(1,len(baseline))
        self.assertEqual(('JavaFX','3.1','Required','See Note 1'),
            tuple(baseline[0][key] for key in ('component','cvss31','user_interaction','notes')))
        current=FACTS['oracle_javafx_risk_matrix_rows']['oracle-cpuoct2026']
        self.assertEqual(7,len(current))
        self.assertEqual(6,sum('21.0.12' in row['supported_versions_affected'] for row in current))
        self.assertFalse(any('21.0.13' in row['supported_versions_affected'] for row in current))
        self.assertTrue(all('Oracle JavaFX' in row['product'] for row in current))
        self.assertFalse(any(row['cve']=='CVE-2024-20925' for row in current))
        self.assertIn('JavaFX (WebKitGTK)',{row['component'] for row in current})
        self.assertIn('JavaFX (gstreamer)',{row['component'] for row in current})

    def test_note2_data_api_applicability_cannot_be_waived_by_a_trusted_java_policy(self):
        notes=FACTS['oracle_Java_SE_notes']['oracle-cpuoct2026']
        self.assertEqual(3,len(notes))
        self.assertIn('does not apply',notes[0])
        self.assertIn('can be exploited by using APIs',notes[1])
        image=[row for row in FACTS['oracle_javafx_risk_matrix_rows']['oracle-cpuoct2026']
            if row['component']=='ImageIO']
        self.assertEqual(1,len(image))
        self.assertEqual('See Note 2',image[0]['notes'])
        self.assertTrue(FACTS['support_policy']['trusted_Java_does_not_blanket_exclude_Oracle_Note2_data_API_advisories'])
        self.assertTrue(FACTS['support_policy']['JavaScript_and_Java_untrusted_execution_are_not_equivalent'])

    def test_accepted_graph_and_osv_observations_are_reused_not_requeried_or_certified(self):
        graph=FACTS['reused_graph']
        self.assertTrue(graph['all_original_archive_hashes_match'])
        self.assertEqual((24,72,142,79),tuple(graph[key] for key in
            ('library_projects','configurations','unique_Maven_coordinates','observed_artifact_identities')))
        self.assertEqual((108,34,0),tuple(graph[key] for key in
            ('runtime_queries_reused','supplementary_queries_reused','new_OSV_requests')))
        self.assertEqual(0,graph['coordinate_matches'])
        self.assertTrue(graph['all_six_modules_aligned_at_current_pin'])
        self.assertFalse(graph['other_host_graph_or_bundled_engine_clearance'])

    def test_no_version_delta_or_closure_is_justified_and_three_original_criteria_remain(self):
        candidate=FACTS['candidate']
        self.assertTrue(candidate['already_current'])
        self.assertFalse(candidate['later_stable_21_available'])
        self.assertFalse(candidate['source_version_update_justified'])
        self.assertEqual([],candidate['source_or_repository_test_delta'])
        self.assertEqual(3,len(FACTS['literal_requirements']))
        self.assertEqual('partially-verified',FACTS['current_disposition'])
        self.assertTrue(FACTS['support_policy']['owner_policy_decision_required_before_adopting_supported_scope'])
        self.assertTrue(FACTS['support_policy']['absence_is_source_observation_not_arbitrary_embedding_or_exploit_proof'])
        fresh=FACTS['fresh_work']
        self.assertEqual(17,fresh['new_public_GETs'])
        for key in ('new_OSV_queries','new_JAR_or_native_downloads','builds','native_tests','Git_network_or_local_operations','live_edits'):
            self.assertEqual(0,fresh[key])
        self.assertFalse(fresh['issue_closure'])

if __name__=='__main__':unittest.main()
