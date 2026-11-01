"""New after-refusal models only; no SDK, Gradle, emulator or device execution."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("NATIVECMPKIT_CAMERA_MUTABLE_PATH_SOURCE_ROOT",
                           Path(__file__).resolve().parents[2])).resolve()
PRIVATE = Path(os.environ.get("NATIVECMPKIT_CAMERA_MUTABLE_PATH_MODEL_TMP",
                              tempfile.gettempdir())).resolve()
HELPER = TREE / "scripts/ci/android_camera_developer_prerequisite.py"
SPEC = importlib.util.spec_from_file_location("camera_mutable_path_diagnostic_helper", HELPER)
camera = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {SPEC.name: camera}):
    SPEC.loader.exec_module(camera)

REFUSAL = "Actual supplied mutable path confinement is unproved"
OPERANDS = {"is_absolute", "is_relative_to_owned_avd", "has_no_parent_component"}
CATEGORIES = {"key_is_skin_path", "key_has_disk_prefix", "key_has_hw_prefix",
              "key_has_snapshot_prefix", "key_contains_path", "key_ends_dir",
              "key_ends_file", "key_ends_filename"}
DIAGNOSTIC_KEYS = OPERANDS | CATEGORIES | {"schema_version", "observation_phase", "native_success_inferred"}
PRIVATE_VALUE = "synthetic-unpublished-mutable-value"


def forbidden(*args, **kwargs):
    raise AssertionError("No SDK, build, subprocess, signal or native action is allowed")


class GuestFixture:
    """Use the real exclusive FD roots, bounded config reader, Journal and disposal."""
    def __enter__(self):
        PRIVATE.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="camera-mutable-path-model-", dir=PRIVATE)
        self.root = Path(self.temporary.name)
        self.output = self.root / "build/ci-verification/fresh-owned-guest"
        self.output.mkdir(mode=0o700, parents=True)
        self.home = self.root / "nonexistent-synthetic-sdk"
        environment = {"ANDROID_SERIAL": camera.SERIAL,
                       "ANDROID_AVD_HOME": str(self.output / "avd"),
                       "ANDROID_EMULATOR_HOME": str(self.output / "avd"),
                       "ANDROID_USER_HOME": str(self.output / "android-user")}
        self.guest = camera.OwnedFreshGuest(self.root, self.output, "nativecmpkit-api35-012345abcdef",
                                          environment, child_probe=forbidden)
        self.guest.create()
        self.directory = self.output / "avd" / (self.guest.name + ".avd")
        self.directory.mkdir(mode=0o700)
        definition = self.output / "avd" / (self.guest.name + ".ini")
        definition.write_text("path=" + str(self.directory) + "\n", encoding="utf-8")
        self.config = self.directory / "config.ini"
        self.set_config({"hw.cpu.ncore": "2"})
        self.disposal = None
        return self

    def set_config(self, values):
        self.config.write_text("".join(key + "=" + value + "\n" for key, value in values.items()), encoding="utf-8")

    def journal_payload(self):
        return json.loads((self.output / "camera-fresh-guest.json").read_bytes())

    def dispose(self):
        self.disposal = self.guest.dispose(engine_exited=False, transport_absent=False, clean_shutdown=False)
        return self.disposal

    def __exit__(self, *error):
        try:
            if not self.guest.closed:
                self.dispose()
        finally:
            self.temporary.cleanup()


class Probe:
    def __init__(self, *, absolute=None, relative=None, parts=("leaf",), label="", events=None):
        self.absolute, self.relative, self.path_parts = absolute, relative, parts
        self.label, self.events = label, events

    def answer(self, value, suffix):
        if self.events is not None:
            self.events.append(self.label + "-" + suffix)
        if isinstance(value, BaseException):
            raise value
        return value

    def is_absolute(self):
        return self.answer(self.absolute, "absolute")

    def is_relative_to(self, directory):
        return self.answer(self.relative, "relative")

    @property
    def parts(self):
        return self.answer(self.path_parts, "parts")


class CameraMutablePathDiagnosticTests(unittest.TestCase):
    def setUp(self):
        # Import is inert and no model is allowed to execute a runtime command.
        self.runtime_guards = [patch.object(camera.subprocess, name, forbidden)
                               for name in ("Popen", "run", "check_output", "check_call")]
        self.runtime_guards += [patch.object(camera.os, name, forbidden) for name in ("kill", "killpg")]
        for guard in self.runtime_guards:
            guard.start()
            self.addCleanup(guard.stop)

    def capture_refusal(self, fixture):
        try:
            fixture.guest.capture_avd(fixture.home)
        except ValueError as error:
            self.assertIs(type(error), ValueError)
            self.assertEqual(str(error), REFUSAL)
            origin = traceback.extract_tb(error.__traceback__)[-1]
            self.assertEqual((origin.name, origin.lineno), ("require", 47))
            self.assertFalse(fixture.guest.launch_attempted)
            self.assertNotIn("mutable_paths_confined", fixture.guest.receipt)
            self.assertEqual(fixture.guest.avd_files, {})
            return error
        self.fail("The original supplied-mutable-path refusal was not preserved")

    def assert_diagnostic(self, fixture, *, absolute, relative, no_parent):
        diagnostic = fixture.guest.receipt["mutable_path_refusal"]
        self.assertEqual(set(diagnostic), DIAGNOSTIC_KEYS)
        self.assertIs(type(diagnostic["schema_version"]), int)
        self.assertEqual(diagnostic["schema_version"], 1)
        self.assertEqual(diagnostic["observation_phase"], "after-refusal")
        self.assertIs(diagnostic["native_success_inferred"], False)
        for key in CATEGORIES:
            self.assertIs(type(diagnostic[key]), bool)
        for key in OPERANDS:
            self.assertTrue(diagnostic[key] is None or type(diagnostic[key]) is bool)
        self.assertIs(diagnostic["is_absolute"], absolute)
        self.assertIs(diagnostic["is_relative_to_owned_avd"], relative)
        self.assertIs(diagnostic["has_no_parent_component"], no_parent)
        return diagnostic

    def assert_disposed_without_native_success(self, fixture):
        receipt = fixture.dispose()
        self.assertEqual(receipt["disposal_status"], "passed")
        self.assertEqual(receipt["errors"], [])
        self.assertIs(receipt["roots_absent"], True)
        self.assertIs(receipt["identity_confined_disposal"], True)
        self.assertIs(receipt["launch_attempted"], False)
        self.assertIs(receipt["clean_shutdown"], False)
        self.assertTrue(fixture.guest.closed)
        for name in ("avd", "android-user"):
            self.assertFalse((fixture.output / name).exists())
        return receipt

    def test_relative_refusal_observes_each_operand_without_changing_primary_require(self):
        with GuestFixture() as fixture:
            fixture.set_config({"skin.path": PRIVATE_VALUE})
            self.capture_refusal(fixture)
            diagnostic = self.assert_diagnostic(fixture, absolute=False, relative=False, no_parent=True)
            self.assertIs(diagnostic["key_is_skin_path"], True)
            self.assertEqual(fixture.journal_payload()["mutable_path_refusal"], diagnostic)
            self.assert_disposed_without_native_success(fixture)

    def test_external_absolute_refusal_keeps_ownership_false_and_external_data_untouched(self):
        with GuestFixture() as fixture:
            external = fixture.root / "foreign-synthetic-data"
            external.write_bytes(b"synthetic-foreign-data-untouched")
            fixture.set_config({"disk.synthetic.path": str(external)})
            self.capture_refusal(fixture)
            self.assert_diagnostic(fixture, absolute=True, relative=False, no_parent=True)
            self.assert_disposed_without_native_success(fixture)
            self.assertEqual(external.read_bytes(), b"synthetic-foreign-data-untouched")

    def test_owned_parent_component_refusal_keeps_lexical_and_parent_facts_separate(self):
        with GuestFixture() as fixture:
            supplied = str(fixture.directory / ".." / PRIVATE_VALUE)
            fixture.set_config({"snapshot.synthetic.path": supplied})
            self.capture_refusal(fixture)
            self.assert_diagnostic(fixture, absolute=True, relative=True, no_parent=False)
            self.assert_disposed_without_native_success(fixture)

    def test_confined_success_adds_no_diagnostic_and_still_requires_original_digest_guard(self):
        with GuestFixture() as fixture:
            fixture.set_config({"disk.synthetic.path": str(fixture.directory / "new-synthetic-data")})
            fixture.guest.capture_avd(fixture.home)
            self.assertIs(fixture.guest.receipt["mutable_paths_confined"], True)
            self.assertEqual(len(fixture.guest.avd_files), 2)
            self.assertNotIn("mutable_path_refusal", fixture.guest.receipt)
            self.assertNotIn("mutable_path_refusal", fixture.journal_payload())
            fixture.guest.verify_config()
            fixture.config.write_text(fixture.config.read_text() + "changed.synthetic=1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Owned AVD configuration changed"):
                fixture.guest.before_launch()
            self.assertFalse(fixture.guest.launch_attempted)
            self.assert_disposed_without_native_success(fixture)

    def test_fixed_key_projection_never_exports_adversarial_key_value_or_paths(self):
        variants = (
            ("skin.path", {"key_is_skin_path", "key_contains_path"}),
            ("disk.synthetic-unpublished-key.path", {"key_has_disk_prefix", "key_contains_path"}),
            ("hw.synthetic-unpublished-key.path", {"key_has_hw_prefix", "key_contains_path"}),
            ("snapshot.synthetic-unpublished-key.path", {"key_has_snapshot_prefix", "key_contains_path"}),
            ("unknown.synthetic-unpublished-key.dir", {"key_ends_dir"}),
            ("unknown.synthetic-unpublished-key.file", {"key_ends_file"}),
            ("unknown.synthetic-unpublished-key.filename", {"key_ends_filename"}),
            ("UPPER.synthetic-unpublished-key.PATH", {"key_contains_path"}),
        )
        for key, enabled in variants:
            with self.subTest(category_projection=sorted(enabled)), GuestFixture() as fixture:
                fixture.set_config({key: PRIVATE_VALUE})
                self.capture_refusal(fixture)
                diagnostic = self.assert_diagnostic(fixture, absolute=False, relative=False, no_parent=True)
                self.assertEqual({name for name in CATEGORIES if diagnostic[name]}, enabled)
                for payload in (json.dumps(diagnostic, sort_keys=True),
                                json.dumps(fixture.journal_payload(), sort_keys=True)):
                    for private in (key, PRIVATE_VALUE, str(fixture.root),
                                    hashlib.sha256(PRIVATE_VALUE.encode()).hexdigest()):
                        self.assertNotIn(private, payload)
                self.assert_disposed_without_native_success(fixture)

    def test_probe_errors_and_interrupts_are_null_and_do_not_replace_primary(self):
        with GuestFixture() as fixture:
            fixture.set_config({"hw.synthetic.path": PRIVATE_VALUE})
            probes = [Probe(absolute=False), Probe(absolute=ValueError(PRIVATE_VALUE)),
                      Probe(relative=True), Probe(parts=KeyboardInterrupt(PRIVATE_VALUE))]
            with patch.object(camera, "Path", side_effect=probes) as constructor:
                self.capture_refusal(fixture)
            self.assertEqual(constructor.call_count, 4)
            self.assert_diagnostic(fixture, absolute=None, relative=True, no_parent=None)
            self.assertNotIn(PRIVATE_VALUE, json.dumps(fixture.journal_payload()))
            self.assert_disposed_without_native_success(fixture)
        with GuestFixture() as fixture:
            fixture.set_config({"hw.synthetic.path": PRIVATE_VALUE})
            primary = ValueError(PRIVATE_VALUE)
            probes = [Probe(absolute=primary), Probe(absolute=False), Probe(relative=False), Probe()]
            with patch.object(camera, "Path", side_effect=probes):
                try:
                    fixture.guest.capture_avd(fixture.home)
                except ValueError as error:
                    self.assertIs(error, primary)
                else:
                    self.fail("An original operand exception was replaced or suppressed")
            self.assert_diagnostic(fixture, absolute=False, relative=False, no_parent=True)
            self.assertNotIn(PRIVATE_VALUE, json.dumps(fixture.journal_payload()))
            self.assert_disposed_without_native_success(fixture)

    def test_nonboolean_probe_results_remain_null_not_false(self):
        with GuestFixture() as fixture:
            fixture.set_config({"unknown.synthetic.file": PRIVATE_VALUE})
            probes = [Probe(absolute=False), Probe(absolute=1), Probe(relative="true"), Probe()]
            with patch.object(camera, "Path", side_effect=probes) as constructor:
                self.capture_refusal(fixture)
            self.assertEqual(constructor.call_count, 4)
            self.assert_diagnostic(fixture, absolute=None, relative=None, no_parent=True)
            self.assert_disposed_without_native_success(fixture)

    def test_refusal_is_latched_before_independent_probes_and_journal_once(self):
        with GuestFixture() as fixture:
            fixture.set_config({"unknown.synthetic.dir": PRIVATE_VALUE})
            events, primary = [], []
            require, write = camera.require, fixture.guest.journal.write

            def record_require(condition, message):
                try:
                    return require(condition, message)
                except ValueError as error:
                    if message == REFUSAL:
                        events.append("original-refusal")
                        primary.append(error)
                        self.assertNotIn("mutable_path_refusal", fixture.guest.receipt)
                    raise

            def record_write(receipt):
                self.assertNotIn("mutable_path_refusal", fixture.journal_payload())
                self.assertEqual(receipt["mutable_path_refusal"]["observation_phase"], "after-refusal")
                events.append("diagnostic-journal")
                write(receipt)

            probes = [Probe(absolute=False, label="original", events=events),
                      Probe(absolute=False, label="diagnostic", events=events),
                      Probe(relative=False, label="diagnostic", events=events),
                      Probe(label="diagnostic", events=events)]
            with patch.object(camera, "Path", side_effect=probes), \
                    patch.object(camera, "require", record_require), \
                    patch.object(fixture.guest.journal, "write", record_write) as checkpoint:
                error = self.capture_refusal(fixture)
            self.assertEqual(len(primary), 1)
            self.assertIs(error, primary[0])
            self.assertEqual(events, ["original-absolute", "original-refusal", "diagnostic-absolute",
                                      "diagnostic-relative", "diagnostic-parts", "diagnostic-journal"])
            self.assert_diagnostic(fixture, absolute=False, relative=False, no_parent=True)
            self.assert_disposed_without_native_success(fixture)

    def journal_failure(self, failure):
        with GuestFixture() as fixture:
            fixture.set_config({"unknown.synthetic.path": PRIVATE_VALUE})
            primary = []
            require = camera.require

            def record_require(condition, message):
                try:
                    return require(condition, message)
                except ValueError as error:
                    if message == REFUSAL:
                        primary.append(error)
                    raise

            with patch.object(camera, "require", record_require), \
                    patch.object(fixture.guest.journal, "write", side_effect=failure) as checkpoint:
                error = self.capture_refusal(fixture)
            self.assertEqual(len(primary), 1)
            self.assertIs(error, primary[0])
            self.assertEqual(checkpoint.call_count, 1)
            self.assert_diagnostic(fixture, absolute=False, relative=False, no_parent=True)
            self.assertNotIn("mutable_path_refusal", fixture.journal_payload())
            self.assertEqual(fixture.guest.receipt["errors"], [])
            receipt = self.assert_disposed_without_native_success(fixture)
            self.assertEqual(fixture.journal_payload()["mutable_path_refusal"], receipt["mutable_path_refusal"])
            self.assertNotIn(PRIVATE_VALUE, json.dumps(fixture.journal_payload()))

    def test_journal_oserror_cannot_replace_the_exact_original_exception(self):
        self.journal_failure(OSError(PRIVATE_VALUE))

    def test_journal_keyboard_interrupt_cannot_replace_the_exact_original_exception(self):
        self.journal_failure(KeyboardInterrupt(PRIVATE_VALUE))

    def test_diagnostic_does_not_suppress_a_real_disposal_refusal(self):
        with GuestFixture() as fixture:
            fixture.set_config({"unknown.synthetic.path": PRIVATE_VALUE})
            self.capture_refusal(fixture)
            with patch.object(fixture.guest, "_remove_contents", side_effect=OSError(PRIVATE_VALUE)):
                receipt = fixture.dispose()
            self.assertEqual(receipt["disposal_status"], "failed")
            self.assertEqual(receipt["errors"], [{"phase": "disposal", "class": "OSError"}])
            self.assertIs(receipt["roots_absent"], False)
            self.assertIs(receipt["launch_attempted"], False)
            self.assertIs(receipt["clean_shutdown"], False)
            self.assertTrue(fixture.guest.closed)
            self.assertTrue((fixture.output / "avd").is_dir())
            self.assertNotIn(PRIVATE_VALUE, json.dumps(fixture.journal_payload()))

    def test_image_readonly_empty_and_skin_branches_have_no_diagnostic(self):
        variants = (
            ({"image.sysdir.1": "wrong-synthetic-image"}, "Image reference differs from fixed selected SDK input"),
            ({"kernel.path": "relative-synthetic-kernel"}, "Readonly image input escaped the selected SDK image"),
            ({"skin.path": "_no_skin"}, None),
            ({"unknown.path": "", "unknown.note": PRIVATE_VALUE}, None),
        )
        for values, refusal in variants:
            with self.subTest(original_branch="refusal" if refusal else "bypass"), GuestFixture() as fixture:
                if refusal is None:
                    fixture.set_config(values)
                    fixture.guest.capture_avd(fixture.home)
                    self.assertIs(fixture.guest.receipt["mutable_paths_confined"], True)
                else:
                    fixture.set_config(values)
                    with self.assertRaises(ValueError) as raised:
                        fixture.guest.capture_avd(fixture.home)
                    self.assertEqual(str(raised.exception), refusal)
                    self.assertNotIn("mutable_paths_confined", fixture.guest.receipt)
                self.assertNotIn("mutable_path_refusal", fixture.guest.receipt)
                self.assertNotIn("mutable_path_refusal", fixture.journal_payload())
                self.assert_disposed_without_native_success(fixture)


if __name__ == "__main__":
    unittest.main()
