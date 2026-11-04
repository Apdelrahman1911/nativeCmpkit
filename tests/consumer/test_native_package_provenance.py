"""Adversarial packaged ZIP manifests, not compiled libraries or JNI runtime proof.

The small source-inventory oracle is adapted independently; the real packaged
checker reads every payload/manifest from a ZIP. Headers are synthetic and no
Cargo, Gradle, JVM, network, publication or source Git query is executed.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

import verify_artifacts as gate


# Independent intended matrix: do not derive it from the producer's list, which
# could otherwise silently remove an unsupported/missing cell from this test.
PLATFORMS = {
    "linux-x64": ("x86_64-unknown-linux-gnu", "elf", 62),
    "linux-arm64": ("aarch64-unknown-linux-gnu", "elf", 183),
    "macos-x64": ("x86_64-apple-darwin", "macho", 0x01000007),
    "macos-arm64": ("aarch64-apple-darwin", "macho", 0x0100000C),
    "windows-x64": ("x86_64-pc-windows-msvc", "pe", 0x8664),
}
MODULES = {"calf-file-picker": "calf_filepicker_native", "calf-share": "calf_share_native"}
REVISION = "a" * 40
OTHER_REVISION = "b" * 40
VERSION = "0.1.0-preview.1"


def zip_bytes(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, payload in sorted(entries.items()):
            archive.writestr(path, payload)
    return output.getvalue()


class NativePackageProvenanceTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "source"
        self.repository = Path(temporary.name) / "repository"
        self.repository.mkdir()
        (self.root / "docs/migration").mkdir(parents=True)
        (self.root / "docs/migration/identity.json").write_text(json.dumps({"modules": [
            {"new_artifact": name} for name in
            ("nativecmpkit-core", "nativecmpkit-file-picker", "nativecmpkit-share")]}))
        for path in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"):
            (self.root / path).write_text("Synthetic complete notice fixture: " + path)
        self.sources = {}
        for module in MODULES:
            path = self.root / module / "native/Cargo.toml"
            path.parent.mkdir(parents=True)
            path.write_text('[package]\nversion="0.2.0"\npublish=false\n')
            self.sources[module] = {f"{module}/native/Cargo.toml": gate.sha256(path)}
        oracle = self.root / "scripts/native/artifacts.py"
        oracle.parent.mkdir(parents=True)
        oracle.write_text(
            "SUPPORTED_PLATFORMS=" + repr({key: {"rustTarget": spec[0]} for key, spec in PLATFORMS.items()}) + "\n"
            + "def expected_source_files(root,module): return " + repr(self.sources) + "[module]\n"
            + 'def toolchain(root): return "1.98.0"\n'
            + 'def crate_version(root,module): return "0.2.0"\n')

    def verifier(self, *, platforms=("linux-x64",), revision=REVISION, dirty_diagnostic=False,
                 modules=("nativecmpkit-file-picker",)):
        return gate.ArtifactVerifier(self.root, self.repository, VERSION, list(modules), ["desktop"], list(platforms),
            expected_native_revision=revision, allow_dirty_native_diagnostic=dirty_diagnostic)

    def entries(self, module="calf-file-picker", platforms=("linux-x64",), *, revision=REVISION, dirty=False):
        result = {}
        for platform in platforms:
            rust_target, container, machine = PLATFORMS[platform]
            payload = bytearray(128)
            if container == "elf":
                payload[:6] = b"\x7fELF\x02\x01"
                struct.pack_into("<H", payload, 18, machine)
            elif container == "macho":
                payload[:4] = b"\xcf\xfa\xed\xfe"
                struct.pack_into("<I", payload, 4, machine)
            else:
                payload[:2] = b"MZ"
                struct.pack_into("<I", payload, 60, 64)
                payload[64:68] = b"PE\0\0"
                struct.pack_into("<H", payload, 68, machine)
            stem = MODULES[module]
            filename = stem + ".dll" if platform.startswith("windows-") else "lib" + stem + (
                ".dylib" if platform.startswith("macos-") else ".so")
            sources = self.sources[module]
            manifest = {
                "schemaVersion": 1, "module": module, "platform": platform, "filename": filename,
                "rustTarget": rust_target, "abiVersion": 1, "crateVersion": "0.2.0", "libraryVersion": VERSION,
                "rustToolchain": "1.98.0", "rustcVersion": "rustc 1.98.0 (synthetic)",
                "cargoVersion": "cargo 1.98.0 (synthetic)", "cargoProfile": "release", "rustFlags": [],
                "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                "sourceRevision": revision, "sourceTreeDirty": dirty, "sourceFiles": sources,
                "sourceSha256": gate.source_digest(sources),
            }
            result[f"native/{platform}/{filename}"] = bytes(payload)
            result[f"META-INF/nativecmpkit/native/{module}/{platform}.json"] = json.dumps(manifest).encode()
        return result

    def inspect(self, entries, *, module="calf-file-picker", platforms=("linux-x64",), verifier=None):
        verifier = verifier or self.verifier(platforms=platforms)
        with zipfile.ZipFile(io.BytesIO(zip_bytes(entries))) as archive:
            names = gate.archive_names(archive)
            for platform in platforms:
                verifier.native(archive, names, module, platform, "synthetic-package")
        return verifier

    def archive(self, entries, *, module="calf-file-picker", verifier=None):
        coordinate = "nativecmpkit-" + module.removeprefix("calf-") + "-desktop"
        notices = {f"META-INF/nativecmpkit/{module}/{name}": (self.root / name).read_bytes()
                   for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md")}
        package = self.repository / f"{coordinate}-{VERSION}.jar"
        package.write_bytes(zip_bytes(notices | entries))
        verifier = verifier or self.verifier()
        verifier.archive(package, coordinate, "nativecmpkit-" + module.removeprefix("calf-"), "desktop")
        return verifier

    def assert_passes(self, verifier):
        self.assertTrue(verifier.checks)
        self.assertEqual([], [row for row in verifier.checks if not row["passed"]])

    def assert_refuses(self, verifier, suffix):
        checks = [row for row in verifier.checks if row["name"].endswith(suffix)]
        self.assertEqual(1, len(checks), verifier.checks)
        self.assertFalse(checks[0]["passed"], verifier.checks)

    def test_native_desktop_request_without_independent_revision_refuses(self):
        with self.assertRaisesRegex(gate.InvalidArtifact, "independently supplied"):
            self.verifier(revision=None)

    def test_manual_native_call_cannot_bypass_missing_expected_revision(self):
        verifier = self.verifier(modules=("nativecmpkit-core",), revision=None)
        self.assert_refuses(self.inspect(self.entries(), verifier=verifier), ":native-revision:linux-x64")

    def test_clean_both_module_five_slot_manifests_accept_exact_requested_revision(self):
        self.assertEqual(tuple(PLATFORMS), gate.NATIVE_PLATFORMS)
        self.assertEqual(MODULES, gate.NATIVE_NAMES)
        for module in MODULES:
            verifier = self.verifier(platforms=tuple(PLATFORMS),
                modules=("nativecmpkit-" + module.removeprefix("calf-"),))
            self.assert_passes(self.inspect(self.entries(module, tuple(PLATFORMS)),
                module=module, platforms=tuple(PLATFORMS), verifier=verifier))
            self.assertEqual(5, len(verifier.native_receipts))
            self.assertTrue(all(item["expectedSourceRevision"] == REVISION and item["sourceTreeDirty"] is False
                                for item in verifier.native_receipts))

    def test_rehashed_stale_revision_is_not_accepted_as_current_package(self):
        self.assert_refuses(self.inspect(self.entries(revision=OTHER_REVISION)), ":native-revision:linux-x64")

    def test_one_mixed_revision_slot_refuses_even_when_other_four_match(self):
        entries = self.entries(platforms=tuple(PLATFORMS))
        path = "META-INF/nativecmpkit/native/calf-file-picker/linux-arm64.json"
        manifest = json.loads(entries[path])
        manifest["sourceRevision"] = OTHER_REVISION
        entries[path] = json.dumps(manifest).encode()
        verifier = self.inspect(entries, platforms=tuple(PLATFORMS))
        failures = [row["name"] for row in verifier.checks if not row["passed"]]
        self.assertEqual(["synthetic-package:native-revision:linux-arm64"], failures)

    def test_dirty_producer_refuses_by_default_with_matching_hashes_and_revision(self):
        self.assert_refuses(self.inspect(self.entries(dirty=True)), ":native-clean-producer:linux-x64")

    def test_explicit_partial_dirty_diagnostic_retains_truthful_scope(self):
        verifier = self.inspect(self.entries(dirty=True), verifier=self.verifier(dirty_diagnostic=True))
        self.assert_passes(verifier)
        self.assertEqual(True, verifier.native_receipts[0]["sourceTreeDirty"])
        self.assertEqual(True, verifier.native_receipts[0]["dirtyDiagnosticAllowed"])
        self.assertNotEqual(set(PLATFORMS), set(verifier.native_platforms))

    def test_dirty_flag_cannot_be_enabled_for_complete_native_matrix(self):
        with self.assertRaisesRegex(gate.InvalidArtifact, "partial native-platform"):
            self.verifier(platforms=tuple(PLATFORMS), dirty_diagnostic=True)

    def test_invalid_independent_revisions_refuse_before_package_inspection(self):
        for revision in (True, 1, "", "main", "A" * 40, "a" * 39, "a" * 41, REVISION + "\n"):
            with self.subTest(revision=revision), self.assertRaisesRegex(gate.InvalidArtifact, "full Git commit"):
                self.verifier(revision=revision)

    def test_diagnostic_flag_cannot_use_nonboolean_truthiness(self):
        for selected in (1, 0, "false", None):
            with self.subTest(selected=selected), self.assertRaisesRegex(gate.InvalidArtifact, "explicit boolean"):
                self.verifier(dirty_diagnostic=selected)

    def test_full_matrix_missing_slot_is_not_a_pass(self):
        entries = self.entries(platforms=tuple(key for key in PLATFORMS if key != "linux-arm64"))
        verifier = self.inspect(entries, platforms=tuple(PLATFORMS))
        self.assert_refuses(verifier, ":native-present:linux-arm64")

    def test_foreign_module_manifest_without_binary_is_rejected(self):
        entries = self.entries()
        entries["META-INF/nativecmpkit/native/calf-share/linux-x64.json"] = b"{}"
        self.assert_refuses(self.archive(entries), ":native-manifest-module-isolation")

    def test_unclaimed_windows_arm64_manifest_is_not_silent_support(self):
        entries = self.entries()
        entries["META-INF/nativecmpkit/native/calf-file-picker/windows-arm64.json"] = b"{}"
        self.assert_refuses(self.archive(entries), ":native-manifest-module-isolation")

    def test_native_manifest_cannot_hide_in_nonowning_desktop_jar(self):
        verifier = self.verifier(modules=("nativecmpkit-core",), revision=None)
        entries = {"META-INF/nativecmpkit/native/calf-file-picker/linux-x64.json": b"{}"}
        self.assert_refuses(self.archive(entries, module="calf-core", verifier=verifier), ":no-unrelated-native")

    def test_boolean_dirty_provenance_is_not_an_integer_or_null(self):
        for dirty in (0, 1, "false", None):
            with self.subTest(dirty=dirty):
                verifier = self.inspect(self.entries(dirty=dirty))
                self.assert_refuses(verifier, ":native-dirty-flag:linux-x64")
                self.assert_refuses(verifier, ":native-clean-producer:linux-x64")


if __name__ == "__main__":
    unittest.main()
