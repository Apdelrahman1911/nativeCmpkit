"""New modeled TOC/refusal controls; no Apple, Instruments or library execution."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import apple_image_profile as profile
import apple_memory_discovery as discovery
import test_apple_image_profile as profile_fixtures
import test_apple_memory_discovery as discovery_fixtures


PRIVATE = "private-toc-metadata-must-not-be-exported"


class AppleAllocationToc608Tests(unittest.TestCase):
    def profile_owner(self):
        # Helpers only: no previously accepted fixture test method is selected.
        owner = profile_fixtures.AppleImageProfileTests(methodName="runTest")
        owner.setUp()
        self.addCleanup(owner.doCleanups)
        return owner

    def discovery_owner(self):
        owner = discovery_fixtures.AppleMemoryDiscoveryTests(methodName="runTest")
        owner.setUp()
        self.addCleanup(owner.doCleanups)
        return owner

    def test_empty_or_other_table_toc_cannot_claim_exported_rows(self):
        for xml, tables in (
            ("<trace-toc/>", 0),
            ('<trace-toc><metadata name="' + PRIVATE + '"/><run number="1"><data>'
             '<table schema="time-profile"/></data></run></trace-toc>', 1),
        ):
            with self.subTest(tables=tables):
                observation = discovery.allocation_toc_observation(ET.fromstring(xml))
                self.assertEqual(tables, observation["tables"])
                self.assertEqual(0, observation["allocation_tables"])
                self.assertEqual([], observation["allocation_schemas"])
                self.assertFalse(observation["recognized_allocation_schema_found"])
                self.assertFalse(observation["exported_allocation_rows_verified"])
                self.assertFalse(observation["root_cause_proven"])
                self.assertNotIn(PRIVATE, json.dumps(observation))
                self.assertNotIn("time-profile", json.dumps(observation))

    def test_only_existing_selector_schema_names_survive_fixed_toc_counts(self):
        tree = ET.fromstring(
            '<trace-toc xmlns="urn:synthetic"><run number="1"><metadata process="' + PRIVATE + '"/>'
            '<data><table schema="allocation-event"/><table schema="time-profile"/>'
            '<table schema="allocation-event"/><table schema="heap-sample"/></data></run></trace-toc>')
        observation = discovery.allocation_toc_observation(tree)
        self.assertEqual((4, 3), (observation["tables"], observation["allocation_tables"]))
        self.assertEqual(["allocation-event", "heap-sample"], observation["allocation_schemas"])
        self.assertEqual(observation["allocation_schemas"], discovery.allocation_schemas(tree))
        self.assertTrue(observation["recognized_allocation_schema_found"])
        self.assertFalse(observation["exported_allocation_rows_verified"])
        self.assertFalse(observation["raw_toc_metadata_uploaded"])
        self.assertNotIn(PRIVATE, json.dumps(observation))

    def test_toc_semantic_bound_refuses_before_schema_selection_or_metadata_export(self):
        tree = ET.fromstring('<trace-toc><metadata name="' + PRIVATE + '"/><table schema="allocation-event"/></trace-toc>')
        with patch.object(discovery, "MAX_XML_ELEMENTS", 2):
            with self.assertRaisesRegex(ValueError, "semantic inspection bound"):
                discovery.allocation_toc_observation(tree)
            with self.assertRaisesRegex(ValueError, "semantic inspection bound"):
                discovery.allocation_schemas(tree)
        invalid = ET.fromstring('<trace-toc><table schema="allocation\' or true()"/></trace-toc>')
        with self.assertRaisesRegex(ValueError, "schema identity"):
            discovery.allocation_toc_observation(invalid)

    def test_library_no_schema_stops_before_exports_and_leaks_and_cleans_its_attempt(self):
        owner = self.profile_owner()
        owner.prepare()

        def execute(*arguments):
            result = owner.execute(*arguments)
            command = arguments[1]
            if "--toc" in command:
                Path(command[-1]).write_text('<trace-toc><table schema="time-profile"/>'
                                            '<metadata name="' + PRIVATE + '"/></trace-toc>')
            return result

        owner.request(execute)
        owner.driver.close()
        receipt = owner.driver.receipt
        self.assertEqual(2, len(owner.commands))
        self.assertFalse(any("--xpath" in command or command[0] == "/usr/bin/leaks" for command in owner.commands))
        self.assertEqual([], receipt["exports"])
        self.assertNotIn("leak_summary", receipt)
        self.assertFalse(receipt["supported"])
        self.assertFalse(receipt["profile_passed"])
        self.assertEqual("select-owned-allocation-schemas", receipt["errors"][0]["failure_stage"])
        self.assertEqual("no-recognized-allocation-schemas", receipt["errors"][0]["failure_reason"])
        self.assertEqual(1, receipt["allocation_toc_observation"]["tables"])
        self.assertTrue(profile.validate_attempt(receipt, profile_fixtures.DEVICE, profile_fixtures.BUNDLE))
        self.assertFalse(owner.driver.private.exists())
        self.assertNotIn(PRIVATE, json.dumps(receipt))

    def test_library_schema_without_owned_rows_preserves_pid_zero_leak_requirement(self):
        owner = self.profile_owner()
        owner.prepare()

        def execute(*arguments):
            result = owner.execute(*arguments)
            if "--xpath" in arguments[1]:
                Path(arguments[1][-1]).write_text(
                    '<trace-query-result><row><frame name="org.example.foreign.ImageUtils.kt"/></row></trace-query-result>')
            return result

        owner.request(execute)
        owner.driver.close()
        receipt = owner.driver.receipt
        self.assertTrue(receipt["allocation_toc_observation"]["recognized_allocation_schema_found"])
        self.assertFalse(receipt["allocation_toc_observation"]["exported_allocation_rows_verified"])
        self.assertEqual(0, receipt["exports"][0]["owned_allocation_rows"])
        self.assertEqual(profile_fixtures.PID, receipt["leak_summary"]["process_id"])
        self.assertEqual((0, 0), (receipt["leak_summary"]["leaks"], receipt["leak_summary"]["leaked_bytes"]))
        self.assertFalse(receipt["supported"])
        self.assertFalse(receipt["profile_passed"])
        self.assertTrue(profile.validate_attempt(receipt, profile_fixtures.DEVICE, profile_fixtures.BUNDLE))

    def test_library_recognized_toc_preserves_selected_target_and_owned_frame_checks(self):
        owner = self.profile_owner()
        owner.prepare()
        owner.request()
        owner.driver.close()
        receipt = owner.driver.receipt
        command = owner.commands[0]
        self.assertEqual(profile_fixtures.DEVICE, command[command.index("--device") + 1])
        self.assertEqual(["--attach", str(profile_fixtures.PID)], command[-2:])
        self.assertEqual(1, receipt["allocation_toc_observation"]["allocation_tables"])
        self.assertFalse(receipt["allocation_toc_observation"]["exported_allocation_rows_verified"])
        self.assertEqual(1, receipt["exports"][0]["owned_allocation_rows"])
        self.assertTrue(receipt["exports"][0]["owned_library_frame_seen"])
        self.assertTrue(receipt["profile_passed"], "Only a modeled positive; tools and native control are mocked")
        self.assertFalse(receipt["ASan_verified"])
        self.assertFalse(receipt["release_readiness_certified"])

    def test_host_no_schema_refusal_keeps_zero_library_executions_and_no_retry(self):
        owner = self.discovery_owner()
        commands = []

        def execute(*arguments):
            commands.append(arguments[1])
            result = owner.execute(*arguments)
            if "--toc" in arguments[1]:
                Path(arguments[1][-1]).write_text('<trace-toc><metadata name="' + PRIVATE + '"/></trace-toc>')
            return result

        receipt = owner.discover(execute)
        self.assertEqual(3, len(commands))
        self.assertFalse(any("--xpath" in command for command in commands))
        self.assertEqual("no-recognized-allocation-schemas", receipt["errors"][0]["failure_reason"])
        self.assertEqual(0, receipt["allocation_toc_observation"]["tables"])
        self.assertEqual([], receipt["exports"])
        self.assertFalse(receipt["supported"])
        self.assertEqual(0, receipt["library_test_executions"])
        self.assertFalse(receipt["UIKit_GC_or_ASan_verified"])
        self.assertTrue(receipt["all_inputs_held"])
        self.assertTrue(receipt["owned_private_tree_removed"])
        self.assertNotIn(PRIVATE, json.dumps(receipt))

    def test_host_recognized_toc_diagnostic_stays_informational(self):
        owner = self.discovery_owner()
        receipt = owner.discover()
        self.assertEqual(1, receipt["allocation_toc_observation"]["tables"])
        self.assertTrue(receipt["allocation_toc_observation"]["recognized_allocation_schema_found"])
        self.assertFalse(receipt["allocation_toc_observation"]["exported_allocation_rows_verified"])
        self.assertEqual(0, receipt["library_test_executions"])
        self.assertFalse(receipt["UIKit_GC_or_ASan_verified"])
        self.assertFalse(receipt["release_readiness_certified"])
        self.assertTrue(receipt["all_inputs_held"])
        self.assertTrue(receipt["owned_private_tree_removed"])


if __name__ == "__main__":
    unittest.main()
