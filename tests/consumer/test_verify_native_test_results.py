"""Real file/descriptor and synthetic XML controls; zero compiled/native methods."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

import verify_native_test_results as gate


CLASS = "nativecmpkit.consumer.PublishedNativeConsumerTest"
METHODS = (
    "pickerNativeLibraryLoadsAndInitializes", "packagedPickerCreatesAndReleasesValidHandles",
    "shareNativeLibraryLoadsAndReportsActualHostCapability",
)
INVOCATION = "12345678-1234-4234-8234-123456789abc"


class NativeFocusedResultTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.results = self.root / "native-focused" / INVOCATION
        self.results.mkdir(parents=True)
        self.path = self.results / f"TEST-{CLASS}.xml"
        self.suite = ET.Element("testsuite", {"name": CLASS, "tests": "3", "failures": "0", "errors": "0", "skipped": "0"})
        for method in METHODS:
            ET.SubElement(self.suite, "testcase", {"name": method, "classname": CLASS})
        self.write()

    def write(self):
        self.path.write_bytes(ET.tostring(self.suite, encoding="utf-8", xml_declaration=True))

    def refused(self, message=None):
        with self.assertRaisesRegex(gate.InvalidNativeResults, message or ".+"):
            gate.verify(self.results, INVOCATION)

    def test_exact_three_synthetic_reports_pass_without_native_or_release_claim(self):
        receipt = gate.verify(self.results, INVOCATION)
        self.assertTrue(receipt["success"])
        self.assertEqual(list(METHODS), receipt["methods"])
        self.assertEqual(3, receipt["reported_method_count"])
        self.assertFalse(receipt["release_readiness_certified"])
        self.assertIn("not native authenticity", receipt["scope"])

    def test_missing_and_empty_no_source_results_refuse(self):
        self.path.unlink()
        self.refused("Exactly one")
        self.results.rmdir()
        self.refused("missing")

    def test_foreign_suite_or_class_cannot_satisfy_native_methods(self):
        self.suite.set("name", "foreign.Suite")
        self.write()
        self.refused("exact native consumer class")
        self.suite.set("name", CLASS)
        self.suite[0].set("classname", "foreign.Suite")
        self.write()
        self.refused("exact native method")

    def test_duplicate_missing_and_foreign_native_methods_refuse(self):
        for replacement in (METHODS[1], "foreignNativeMethod"):
            with self.subTest(replacement=replacement):
                self.suite[0].set("name", replacement)
                self.write()
                self.refused("exact native method")
        self.suite.remove(self.suite[0])
        self.write()
        self.refused("exact native method")

    def test_failure_error_skip_counters_and_hidden_elements_refuse(self):
        for count in ("failures", "errors", "skipped"):
            with self.subTest(counter=count):
                self.suite.set(count, "1")
                self.write()
                self.refused("zero failures/errors/skips")
                self.suite.set(count, "0")
        for tag in ("failure", "error", "skipped"):
            with self.subTest(tag=tag):
                child = ET.SubElement(self.suite[0], tag)
                self.write()
                self.refused("hide behind")
                self.suite[0].remove(child)

    def test_stale_or_invalid_invocation_cannot_rebind_existing_xml(self):
        for invocation in ("main", "", INVOCATION.upper(), "12345678-1234-4234-8234-000000000000", None, 0, True):
            with self.subTest(invocation=invocation), self.assertRaises(gate.InvalidNativeResults):
                gate.verify(self.results, invocation)

    def test_extra_nested_or_linked_xml_refuses(self):
        extra = self.results / "foreign.xml"
        extra.write_bytes(self.path.read_bytes())
        self.refused("foreign results")
        extra.unlink()
        nested = self.results / "foreign"
        nested.mkdir()
        (nested / "foreign.xml").write_bytes(self.path.read_bytes())
        self.refused("flat")
        (nested / "foreign.xml").unlink()
        nested.rmdir()
        original = self.root / "held.xml"
        self.path.rename(original)
        self.path.symlink_to(original)
        self.refused("nonlinked")

    def test_hardlinked_xml_is_not_fresh_task_owned_output(self):
        os.link(self.path, self.root / "held.xml")
        self.refused("nonlinked file")

    def test_malformed_utf8_dtd_and_oversized_reports_refuse(self):
        for payload in (b"\xff", b"not XML", b'<!DOCTYPE testsuite [<!ENTITY x "value">]><testsuite/>'):
            with self.subTest(payload=payload):
                self.path.write_bytes(payload)
                self.refused()
        self.write()
        with mock.patch.object(gate, "MAX_XML_BYTES", 16):
            self.refused("bounded")

    def test_unknown_suite_and_testcase_elements_refuse(self):
        child = ET.SubElement(self.suite, "foreign")
        self.write()
        self.refused("Unrecognized focused suite")
        self.suite.remove(child)
        ET.SubElement(self.suite[0], "foreign")
        self.write()
        self.refused("Unrecognized focused testcase")

    def test_nested_foreign_suite_case_or_namespace_cannot_hide_in_properties(self):
        properties = ET.SubElement(self.suite, "properties")
        for tag in ("testsuite", "testcase", "{foreign}testcase"):
            with self.subTest(tag=tag):
                child = ET.SubElement(properties, tag)
                self.write()
                self.refused("foreign JUnit")
                properties.remove(child)

    def test_xml_reader_closes_descriptor_on_success_and_parse_failure(self):
        streams = []
        original = os.fdopen
        def observed(*args, **kwargs):
            stream = original(*args, **kwargs)
            streams.append(stream)
            return stream
        with mock.patch.object(gate.os, "fdopen", side_effect=observed):
            gate.verify(self.results, INVOCATION)
            self.path.write_bytes(b"not XML")
            self.refused()
        self.assertEqual(2, len(streams))
        self.assertTrue(all(stream.closed for stream in streams))

    def test_raw_descriptor_closes_if_stream_construction_fails(self):
        opened = []
        original = os.open
        def observed(*args, **kwargs):
            descriptor = original(*args, **kwargs)
            opened.append(descriptor)
            return descriptor
        try:
            with mock.patch.object(gate.os, "open", side_effect=observed), \
                    mock.patch.object(gate.os, "fdopen", side_effect=OSError("Synthetic stream construction refusal")):
                self.refused("Could not read")
            self.assertEqual(1, len(opened))
            for descriptor in opened:
                with self.assertRaises(OSError):
                    os.fstat(descriptor)
        finally:
            for descriptor in opened:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    def test_mutation_during_read_refuses_and_stream_still_closes(self):
        original = os.fdopen
        streams = []
        target = self.path
        class MutatingStream:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): self.stream.__enter__(); return self
            def __exit__(self, *args): return self.stream.__exit__(*args)
            def fileno(self): return self.stream.fileno()
            def read(self, bound):
                payload = self.stream.read(bound)
                target.write_bytes(payload + b"changed during held read")
                return payload
        def observed(*args, **kwargs):
            stream = original(*args, **kwargs)
            streams.append(stream)
            return MutatingStream(stream)
        with mock.patch.object(gate.os, "fdopen", side_effect=observed):
            self.refused("changed or exceeded")
        self.assertEqual(1, len(streams))
        self.assertTrue(streams[0].closed)

    def test_cli_reports_missing_and_exact_synthetic_results_honestly(self):
        args = ["--results-dir", str(self.results), "--invocation-id", INVOCATION]
        accepted = self.root / "accepted.json"
        self.assertEqual(0, gate.main(args + ["--output", str(accepted)]))
        self.assertTrue(json.loads(accepted.read_text())["success"])
        self.path.unlink()
        refused = self.root / "refused.json"
        self.assertEqual(1, gate.main(args + ["--output", str(refused)]))
        self.assertFalse(json.loads(refused.read_text())["success"])
        self.assertFalse(json.loads(refused.read_text())["release_readiness_certified"])

    def test_cli_preserves_existing_receipt_and_directory_size_is_bounded(self):
        output = self.root / "preserved.json"
        output.write_bytes(b"Preserve an original receipt")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1, gate.main(["--results-dir", str(self.results), "--invocation-id", INVOCATION, "--output", str(output)]))
        self.assertEqual(b"Preserve an original receipt", output.read_bytes())
        for index in range(17):
            (self.results / f"foreign-{index}.txt").write_bytes(b"unclaimed")
        self.refused("bounded")


if __name__ == "__main__":
    unittest.main()
