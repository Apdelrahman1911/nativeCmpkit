"""Synthetic public-probe/tool privacy fixtures; ZERO Apple/library execution."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

import apple_memory_discovery as d

DEVICE = "11111111-1111-1111-1111-111111111111"
PRIVATE_SENTINEL = "synthetic-private-trace-value-never-exported"


class AppleMemoryDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "build.gradle.kts").write_text("// synthetic source fixture\n")
        (self.root / "settings.gradle.kts").write_text('include(\n    ":calf-io",\n)\n')
        module = self.root / "calf-io"
        module.mkdir()
        (module / "build.gradle.kts").write_text("// synthetic included module\n")
        self.runtime = {"source_revision": "a" * 40, "source_tree_dirty": False,
                        "host": {"system": "Darwin"}}

    def execute(self, root, command, log, timeout, reserve_mib):
        self.assertEqual(8192, reserve_mib)
        self.assertEqual("/usr/bin/xcrun", command[0])
        log.write_text(PRIVATE_SENTINEL)
        if command[1] == "clang":
            Path(command[-1]).write_bytes(b"synthetic native binary never executed")
        elif "record" in command:
            trace = Path(command[command.index("--output") + 1])
            trace.mkdir()
            (trace / "private.bin").write_text(PRIVATE_SENTINEL)
        elif "--toc" in command:
            Path(command[-1]).write_text('<trace-toc><run number="1"><data><table schema="allocation-event"/></data></run></trace-toc>')
        else:
            Path(command[-1]).write_text('<trace-query-result><row><frame name="' + d.PROBE_SYMBOL +
                                       '" address="0x1234"/><private>' + PRIVATE_SENTINEL + '</private></row></trace-query-result>')
        return {"exit_code": 0, "elapsed_seconds": 0.01}

    def discover(self, execute=None):
        with (patch.object(d.runtime, "capture", return_value=self.runtime),
              patch.object(d.shutil, "disk_usage", return_value=Mock(free=16 * 1024**3)),
              patch.object(d.lt, "execute", side_effect=execute or self.execute)):
            return d.discover(self.root, DEVICE)

    def test_owning_pipeline_uses_safe_xml_and_reports_no_native_or_library_pass(self):
        receipt = self.discover()
        self.assertTrue(receipt["supported"])
        self.assertTrue(receipt["all_inputs_held"])
        self.assertTrue(receipt["owned_private_tree_removed"])
        self.assertEqual(["allocation-event"], receipt["actual_allocation_schemas"])
        self.assertEqual(1, receipt["exports"][0]["rows"])
        self.assertTrue(receipt["exports"][0]["owned_public_probe_symbol_seen"])
        self.assertEqual(0, receipt["library_test_executions"])
        self.assertFalse(receipt["UIKit_GC_or_ASan_verified"])
        self.assertFalse(receipt["release_readiness_certified"])
        self.assertNotIn(PRIVATE_SENTINEL, json.dumps(receipt))
        self.assertNotIn("0x1234", json.dumps(receipt))
        self.assertFalse((self.root / d.OUTPUT / "private").exists())
        with self.assertRaises(ValueError): self.discover()

    def test_actual_command_failure_is_explicit_unverified_and_is_not_retried(self):
        calls = []
        def failure(root, command, log, timeout, reserve):
            calls.append(command)
            log.write_text(PRIVATE_SENTINEL)
            return {"exit_code": 1, "elapsed_seconds": 0.01}
        receipt = self.discover(failure)
        self.assertFalse(receipt["supported"])
        self.assertEqual(1, len(calls))
        self.assertEqual("RuntimeError", receipt["errors"][0]["error_type"])
        self.assertTrue(receipt["owned_private_tree_removed"])
        self.assertNotIn(PRIVATE_SENTINEL, json.dumps(receipt))

    def test_wrong_host_capacity_device_or_existing_output_never_launches_a_tool(self):
        for host, capacity, device in (("Linux", 16 * 1024**3, DEVICE),
                                      ("Darwin", 8192 * 1024**2 - 1, DEVICE),
                                      ("Darwin", 16 * 1024**3, "foreign-device")):
            with self.subTest(host=host, capacity=capacity, device=device):
                context = {**self.runtime, "host": {"system": host}}
                with (patch.object(d.runtime, "capture", return_value=context),
                      patch.object(d.shutil, "disk_usage", return_value=Mock(free=capacity)),
                      patch.object(d.lt, "execute") as execute):
                    with self.assertRaises((ValueError, OSError)): d.discover(self.root, device)
                    execute.assert_not_called()
        output = self.root / d.OUTPUT
        output.mkdir(parents=True)
        with patch.object(d.lt, "execute") as execute:
            with self.assertRaises(ValueError): d.discover(self.root, DEVICE)
        execute.assert_not_called()

    def test_schema_bound_and_xpath_identity_reject_unreviewed_or_unbounded_tables(self):
        for value in ("allocations' or true()", "$(command)", "", "x" * 129):
            tree = ET.Element("trace-toc"); ET.SubElement(tree, "table", schema=value)
            with self.assertRaises(ValueError): d.allocation_schemas(tree)
        tree = ET.Element("trace-toc")
        for n in range(d.MAX_TABLES + 1): ET.SubElement(tree, "table", schema="allocation-" + str(n))
        with self.assertRaises(ValueError): d.allocation_schemas(tree)
        tree = ET.fromstring('<trace-toc><table schema="allocation-event"/><table schema="allocation-event"/><table schema="time-profile"/></trace-toc>')
        self.assertEqual(["allocation-event"], d.allocation_schemas(tree))

    def test_xml_entities_aliases_and_size_fail_before_any_private_value_export(self):
        path = self.root / "tool.xml"
        path.write_text('<!DOCTYPE foo [<!ENTITY x "private">]><foo>&x;</foo>')
        with self.assertRaises(ValueError): d.allocation_summary(path)
        path.write_text('<trace-query-result/>')
        with patch.object(d, "MAX_XML_BYTES", 2):
            with self.assertRaises(ValueError): d.allocation_summary(path)
        alias = self.root / "redirect.xml"; alias.symlink_to(path)
        with self.assertRaises(ValueError): d.allocation_summary(alias)

    def test_zero_or_unrelated_rows_cannot_be_tool_support_or_memory_evidence(self):
        def execute(root, command, log, timeout, reserve):
            result = self.execute(root, command, log, timeout, reserve)
            if "--xpath" in command:
                Path(command[-1]).write_text('<trace-query-result><row><frame name="unrelated"/></row></trace-query-result>')
            return result
        receipt = self.discover(execute)
        self.assertFalse(receipt["supported"])
        self.assertEqual(1, receipt["exports"][0]["rows"])
        self.assertFalse(receipt["exports"][0]["owned_public_probe_symbol_seen"])

    def test_source_change_is_retained_as_failure_not_a_clean_support_claim(self):
        def execute(root, command, log, timeout, reserve):
            (root / "build.gradle.kts").write_text("// source changed during synthetic tool call\n")
            return self.execute(root, command, log, timeout, reserve)
        receipt = self.discover(execute)
        self.assertFalse(receipt["supported"])
        self.assertFalse(receipt["all_inputs_held"])
        self.assertNotEqual(receipt["input_digest_before"], receipt["input_digest_after"])
        self.assertTrue(receipt["owned_private_tree_removed"])

    def test_private_tree_symlink_is_not_followed_or_removed(self):
        private = self.root / d.OUTPUT / "private"; private.mkdir(parents=True)
        unrelated = self.root / "unrelated"; unrelated.mkdir()
        (unrelated / "preserve.txt").write_text("preserve")
        (private / "redirect").symlink_to(unrelated, target_is_directory=True)
        with self.assertRaises(ValueError): d.private_inventory(self.root, private)
        self.assertEqual("preserve", (unrelated / "preserve.txt").read_text())

    def test_workflow_reuses_the_apple_sample_host_and_exports_only_discovery_json_early(self):
        text = (Path(d.__file__).resolve().parents[2] / ".github/workflows/gradle.yml").read_text()
        job = text.split("\n  sample-platforms:\n", 1)[1].split("\n  library-tests:\n", 1)[0]
        discovery = job.split("- name: Discover Apple allocation tools", 1)[1].split("- name: Shared sample app builds", 1)[0]
        self.assertIn("runner.os == 'macOS' && matrix.build_only", discovery)
        self.assertIn("scripts/ci/apple_memory_discovery.py", discovery)
        self.assertIn('path: build/ci-verification/apple-memory-discovery/discovery.json', discovery)
        self.assertNotIn("permissions:", discovery)
        for forbidden in ("*.log", "*.trace", ".app", ".jar", "private/"):
            self.assertNotIn(forbidden, discovery)


if __name__ == "__main__": unittest.main()
