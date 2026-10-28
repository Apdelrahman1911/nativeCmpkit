"""Offline artifact-integrity tests; synthetic headers are NOT native/JNI runtime proof."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import artifacts as a


class NativeArtifactsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.module = "calf-file-picker"
        self.resources = self.root / "build/input"
        self.platform = "linux-x64"
        self.revision = "a" * 40
        for module in a.MODULE_STEMS:
            self.write(f'{module}/native/Cargo.toml', '[package]\nname="' + module + '"\nversion="0.2.0"\npublish=false\n')
            self.write(f"{module}/native/Cargo.lock", "version = 4\n")
            self.write(f"{module}/native/src/lib.rs", "pub fn a() {}\n")
            self.write(f"{module}/build.gradle.kts", "// fixture build configuration\n")
            self.write(f"{module}/src/desktopMain/kotlin/Bridge.kt", "// fixture JNI declaration\n")
        self.write("rust-toolchain.toml", '[toolchain]\nchannel="1.98.0"\n')
        self.write("scripts/native/artifacts.py", "# fixture implementation\n")
        self.write("convention-plugins/src/main/kotlin/NativeLibraries.kt", "// fixture implementation\n")

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def header(self, platform):
        spec = a.SUPPORTED_PLATFORMS[platform]
        data = bytearray(128)
        if spec["format"] == "elf":
            data[:6] = b"\x7fELF\x02\x01"
            struct.pack_into("<H", data, 18, spec["machine"])
        elif spec["format"] == "macho":
            data[:4] = b"\xcf\xfa\xed\xfe"
            struct.pack_into("<I", data, 4, spec["machine"])
        else:
            data[:2] = b"MZ"
            struct.pack_into("<I", data, 60, 64)
            data[64:68] = b"PE\0\0"
            struct.pack_into("<H", data, 68, spec["machine"])
        return bytes(data)

    def bundle(self, platform=None, module=None, dirty=False):
        platform = platform or self.platform
        module = module or self.module
        binary = self.resources / a.binary_relative_path(module, platform)
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(self.header(platform))
        files = a.expected_source_files(self.root, module)
        manifest = {"schemaVersion": 1, "module": module, "platform": platform,
                    "rustTarget": a.SUPPORTED_PLATFORMS[platform]["rustTarget"], "filename": binary.name,
                    "abiVersion": 1, "sha256": a.digest(binary), "size": binary.stat().st_size,
                    "crateVersion": "0.2.0", "libraryVersion": "0.1.0-preview.1", "rustToolchain": "1.98.0",
                    "cargoProfile": "release", "rustFlags": [], "rustcVersion": "rustc 1.98.0 (fixture)",
                    "cargoVersion": "cargo 1.98.0 (fixture)", "sourceRevision": self.revision,
                    "sourceTreeDirty": dirty, "sourceFiles": files, "sourceSha256": a.source_digest(files)}
        path = self.resources / a.manifest_relative_path(module, platform)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path, manifest, binary

    def validate(self, **kwargs):
        return a.validate_bundle(self.root, self.module, self.resources, [self.platform],
                                 expected_revision=self.revision, expected_version="0.1.0-preview.1", **kwargs)

    def test_complete_host_manifest_accepted(self):
        self.bundle()
        self.assertEqual(self.validate()[0]["module"], self.module)

    def test_empty_and_irrelevant_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "resource set"):
            self.validate()
        self.write("build/input/native/linux-x64/irrelevant.txt", "not a library")
        with self.assertRaisesRegex(ValueError, "unexpected"):
            self.validate()

    def test_missing_binary_fails(self):
        _, _, binary = self.bundle()
        binary.unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            self.validate()

    def test_wrong_platform_does_not_fall_back(self):
        self.bundle("macos-arm64")
        with self.assertRaisesRegex(ValueError, "resource set"):
            self.validate()

    def test_foreign_module_binaries_are_rejected(self):
        self.bundle()
        self.bundle(module="calf-share")
        with self.assertRaisesRegex(ValueError, "unexpected"):
            self.validate()

    def test_each_module_and_platform_rejects_the_other_modules_payload(self):
        for module in a.MODULE_STEMS:
            other = next(candidate for candidate in a.MODULE_STEMS if candidate != module)
            for platform in a.SUPPORTED_PLATFORMS:
                with self.subTest(module=module, platform=platform):
                    self.resources = self.root / "build/scoped" / module / platform
                    self.bundle(platform=platform, module=module)
                    accepted = a.validate_bundle(self.root, module, self.resources, [platform],
                                                 expected_revision=self.revision)
                    self.assertEqual([module], [item["module"] for item in accepted])
                    self.bundle(platform=platform, module=other)
                    with self.assertRaisesRegex(ValueError, "unexpected"):
                        a.validate_bundle(self.root, module, self.resources, [platform],
                                          expected_revision=self.revision)

    def test_missing_module_cannot_use_the_other_modules_complete_bundle(self):
        for module in a.MODULE_STEMS:
            other = next(candidate for candidate in a.MODULE_STEMS if candidate != module)
            for platform in a.SUPPORTED_PLATFORMS:
                with self.subTest(module=module, platform=platform):
                    self.resources = self.root / "build/missing-module" / module / platform
                    self.bundle(platform=platform, module=other)
                    with self.assertRaisesRegex(ValueError, "missing.*unexpected"):
                        a.validate_bundle(self.root, module, self.resources, [platform],
                                          expected_revision=self.revision)

    def test_corrupt_binary_rejected_even_with_same_size(self):
        _, _, binary = self.bundle()
        data = bytearray(binary.read_bytes()); data[-1] ^= 1; binary.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.validate()

    def test_wrong_architecture_rejected_even_if_hash_updated(self):
        path, manifest, binary = self.bundle()
        binary.write_bytes(self.header("linux-arm64"))
        manifest["sha256"] = a.digest(binary)
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "ELF"):
            self.validate()

    def test_bad_identity_version_toolchain_and_abi_rejected(self):
        replacements = {"abiVersion": 2, "module": "calf-share", "platform": "linux-arm64",
                        "schemaVersion": 2, "filename": "unrelated.so", "rustToolchain": "stable",
                        "crateVersion": "4.0.0", "libraryVersion": "2.0.0", "cargoProfile": "debug",
                        "rustTarget": "aarch64-unknown-linux-gnu", "rustFlags": ["-C"]}
        for key, value in replacements.items():
            with self.subTest(key=key):
                path, manifest, _ = self.bundle()
                manifest[key] = value
                path.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    self.validate()

    def test_stale_revision_rejected(self):
        path, manifest, _ = self.bundle()
        manifest["sourceRevision"] = "b" * 40
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.validate()

    def test_dirty_developer_source_is_explicit_not_release_eligible(self):
        self.bundle(dirty=True)
        self.assertTrue(self.validate()[0]["sourceTreeDirty"])
        with self.assertRaisesRegex(ValueError, "clean"):
            self.validate(require_clean=True)

    def test_bool_cannot_masquerade_as_size_or_abi(self):
        for field in ("size", "abiVersion"):
            path, manifest, _ = self.bundle()
            manifest[field] = True
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                self.validate()

    def test_source_omission_rejected_even_with_recomputed_aggregate(self):
        path, manifest, _ = self.bundle()
        manifest["sourceFiles"].pop(f"{self.module}/native/src/lib.rs")
        manifest["sourceSha256"] = a.source_digest(manifest["sourceFiles"])
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.validate()

    def test_each_source_lock_toolchain_jni_and_build_input_invalidates(self):
        inputs = [f"{self.module}/native/src/lib.rs", f"{self.module}/native/Cargo.lock",
                  f"{self.module}/src/desktopMain/kotlin/Bridge.kt", f"{self.module}/build.gradle.kts",
                  "scripts/native/artifacts.py", "convention-plugins/src/main/kotlin/NativeLibraries.kt"]
        for relative in inputs:
            with self.subTest(relative=relative):
                self.bundle()
                path = self.root / relative
                original = path.read_text()
                path.write_text(original + "// changed\n")
                with self.assertRaisesRegex(ValueError, "inventory"):
                    self.validate()
                path.write_text(original)
        self.bundle()
        self.write("rust-toolchain.toml", '[toolchain]\nchannel="1.99.0"\n')
        with self.assertRaisesRegex(ValueError, "rustToolchain"):
            self.validate()

    def test_included_assets_config_and_nested_target_source_are_inventoried(self):
        before = a.expected_source_files(self.root, self.module)
        paths = [f"{self.module}/native/assets/help.bin", f"{self.module}/native/src/target/mod.rs",
                 f"{self.module}/.cargo/config.toml", ".cargo/config.toml"]
        for path in paths:
            self.write(path, "fixture")
        after = a.expected_source_files(self.root, self.module)
        self.assertTrue(set(paths) <= set(after))
        self.assertNotEqual(a.source_digest(before), a.source_digest(after))

    def test_target_cache_and_gitignore_do_not_change_source_fingerprint(self):
        before = a.expected_source_files(self.root, self.module)
        self.write(f"{self.module}/native/target/release/lib.so", "generated")
        self.write(f"{self.module}/native/.gitignore", "/target\n")
        self.assertEqual(before, a.expected_source_files(self.root, self.module))

    def test_source_digest_rule_is_sorted_exact_utf8(self):
        entries = {"z/file": "b" * 64, "a/file": "a" * 64}
        expected = hashlib.sha256(("a" * 64 + "  a/file\n" + "b" * 64 + "  z/file\n").encode()).hexdigest()
        self.assertEqual(expected, a.source_digest(entries))

    def test_full_matrix_requires_all_five_and_matching_modules(self):
        self.bundle()
        with self.assertRaisesRegex(ValueError, "missing"):
            a.validate_bundle(self.root, self.module, self.resources, list(a.SUPPORTED_PLATFORMS))
        for platform in a.SUPPORTED_PLATFORMS:
            self.bundle(platform)
        self.assertEqual(5, len(a.validate_bundle(self.root, self.module, self.resources,
                                                list(a.SUPPORTED_PLATFORMS), expected_revision=self.revision)))

    def test_duplicate_json_keys_rejected(self):
        path, _, _ = self.bundle()
        path.write_text('{"module":"calf-share","module":"calf-file-picker"}')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.validate()

    def test_path_traversal_and_symlinks_rejected(self):
        for relative in ("../outside", "/absolute", "a/../outside", "a\\b", "a\nb", "a//b"):
            with self.assertRaises(ValueError):
                a.safe_file(self.root, relative)
        _, _, binary = self.bundle()
        alternate = self.resources / "actual.so"
        binary.rename(alternate)
        try:
            binary.symlink_to(alternate)
        except OSError:
            self.skipTest("Host account cannot create symlinks")
        with self.assertRaisesRegex(ValueError, "Symlink"):
            self.validate()

    def test_assembly_replaces_only_verified_per_module_resources(self):
        self.bundle()
        destination = self.root / self.module / "build/resources"
        self.write(f"{self.module}/build/resources/stale.so", "old unrelated output")
        a.assemble(self.root, self.module, self.resources, destination, [self.platform], expected_revision=self.revision)
        self.assertFalse((destination / "stale.so").exists())
        self.assertEqual(2, sum(path.is_file() for path in destination.rglob("*")))

    def test_invalid_assembly_preserves_old_output(self):
        self.bundle()
        self.write("build/input/foreign.so", "not permitted")
        destination = self.root / self.module / "build/resources"
        original = self.write(f"{self.module}/build/resources/prior-output", "keep")
        with self.assertRaises(ValueError):
            a.assemble(self.root, self.module, self.resources, destination, [self.platform])
        self.assertEqual("keep", original.read_text())

    def test_assembly_cannot_destroy_source_or_unrelated_directory(self):
        self.bundle()
        for destination in (self.root, self.root / "calf-io", self.root / "build", self.root / self.module):
            with self.assertRaisesRegex(ValueError, "dedicated child"):
                a.assemble(self.root, self.module, self.resources, destination, [self.platform])

    def test_host_mapping_aliases_and_unsupported_windows_arm64(self):
        for system, arch, expected in [("Linux", "AMD64", "linux-x64"), ("Darwin", "arm64", "macos-arm64"),
                                      ("Windows", "AMD64", "windows-x64"), ("Linux", "aarch64", "linux-arm64")]:
            with patch.object(a.host_platform, "system", return_value=system), patch.object(a.host_platform, "machine", return_value=arch):
                self.assertEqual(expected, a.current_platform())
        with patch.object(a.host_platform, "system", return_value="Windows"), patch.object(a.host_platform, "machine", return_value="ARM64"):
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                a.current_platform()

    def test_custom_rust_environment_is_not_silently_accepted(self):
        with patch.dict(os.environ, {"RUSTFLAGS": "sensitive-value-not-for-logs"}, clear=True):
            with self.assertRaises(ValueError) as error:
                a._build_environment()
            self.assertNotIn("sensitive-value", str(error.exception))
        with patch.dict(os.environ, {"CARGO_BUILD_JOBS": "1"}, clear=True):
            self.assertEqual("1", a._build_environment()["CARGO_BUILD_JOBS"])


if __name__ == "__main__":
    unittest.main()
