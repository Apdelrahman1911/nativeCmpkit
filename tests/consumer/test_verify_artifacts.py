"""Adversarial fixtures for the static gate, not library/native integration tests."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import stat
import struct
import tempfile
import unittest
import warnings
import zipfile

import verify_artifacts as gate
from _native_test_fixtures import metadata_fixture


def zip_bytes(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, data in entries.items():
            archive.writestr(path, data)
    return output.getvalue()


class CupertinoFontResourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.font = (gate.ROOT / "calf-cupertino-icons/src/commonMain/composeResources/font/sf_symbols.ttf").read_bytes()
        cls.license = (gate.ROOT / "licenses/cupertino-icons-MIT.txt").read_bytes()
        cls.provenance = (gate.ROOT / "licenses/cupertino-icons-provenance.json").read_bytes()

    def entries(self, prefix=""):
        root = prefix + gate.CUPERTINO_RESOURCE_PREFIX
        return {root + "font/sf_symbols.ttf": self.font,
                root + "files/nativecmpkit/cupertino-icons-MIT.txt": self.license,
                root + "files/nativecmpkit/cupertino-icons-provenance.json": self.provenance}

    def inspect(self, entries, prefix=""):
        with zipfile.ZipFile(io.BytesIO(zip_bytes(entries))) as archive:
            return gate.cupertino_font_resources(archive, gate.archive_names(archive), self.provenance,
                prefix + gate.CUPERTINO_RESOURCE_PREFIX + "font/sf_symbols.ttf")

    def test_exact_android_and_desktop_apple_browser_resource_layouts(self):
        for platform, prefix in (("Android", "assets/"), ("Desktop", ""), ("iOS device resources", ""),
                                 ("iOS simulator resources", ""), ("JS", ""), ("Wasm", "")):
            with self.subTest(platform=platform):
                rows = self.inspect(self.entries(prefix), prefix)
                self.assertEqual(1, len(rows))
                self.assertEqual(gate.CUPERTINO_FONT_SHA256, rows[0]["font_sha256"])
                self.assertEqual(gate.CUPERTINO_MIT_SHA256, rows[0]["license_sha256"])

    def test_empty_or_misplaced_font_distribution_is_rejected(self):
        for entries in ({}, {"wrong/font/sf_symbols.ttf": self.font}):
            with self.subTest(entries=list(entries)), self.assertRaises(gate.InvalidArtifact):
                self.inspect(entries)

    def test_missing_notice_or_provenance_is_rejected(self):
        complete = self.entries("assets/")
        for path in complete:
            if path.endswith(".ttf"):
                continue
            entries = complete.copy()
            del entries[path]
            with self.subTest(path=path), self.assertRaises(gate.InvalidArtifact):
                self.inspect(entries, "assets/")

    def test_modified_font_truncated_copyright_or_stale_provenance_is_rejected(self):
        for suffix in ("font/sf_symbols.ttf", "files/nativecmpkit/cupertino-icons-MIT.txt",
                       "files/nativecmpkit/cupertino-icons-provenance.json"):
            entries = self.entries()
            path = gate.CUPERTINO_RESOURCE_PREFIX + suffix
            entries[path] = entries[path][:-1]
            with self.subTest(path=path), self.assertRaises(gate.InvalidArtifact):
                self.inspect(entries)

    def test_committed_resource_copies_are_canonical_and_public_font_is_unchanged(self):
        resource = gate.ROOT / "calf-cupertino-icons/src/commonMain/composeResources/files/nativecmpkit"
        self.assertEqual(self.license, (resource / "cupertino-icons-MIT.txt").read_bytes())
        self.assertEqual(self.provenance, (resource / "cupertino-icons-provenance.json").read_bytes())
        self.assertEqual(gate.CUPERTINO_FONT_SHA256, hashlib.sha256(self.font).hexdigest())
        self.assertEqual(gate.CUPERTINO_MIT_SHA256, hashlib.sha256(self.license).hexdigest())

    def test_owning_maven_verifier_rejects_empty_android_and_resource_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            for target, name in (("android", "nativecmpkit-cupertino-icons-android-0.1.0-preview.1.aar"),
                                 ("wasmJs", "nativecmpkit-cupertino-icons-0.1.0-preview.1.kotlin_resources.zip")):
                path = repo / name
                path.write_bytes(zip_bytes({}))
                verifier = gate.ArtifactVerifier(gate.ROOT, repo, "0.1.0-preview.1",
                    modules=["nativecmpkit-cupertino-icons"], targets=[target])
                verifier.archive(path, "nativecmpkit-cupertino-icons" + gate.TARGET_SUFFIXES[target],
                    "nativecmpkit-cupertino-icons", target)
                failures = [c for c in verifier.checks if not c["passed"]]
                with self.subTest(target=target):
                    self.assertTrue(any(c["name"].endswith(":retained-font-resource" if target == "android"
                        else ":valid-archive") for c in failures), failures)


class SafeFormatTest(unittest.TestCase):
    def test_json_duplicate_key_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.load_json_bytes(b'{"version":1,"version":2}')

    def test_json_valid(self):
        self.assertEqual({"version": 1}, gate.load_json_bytes(b'{"version":1}'))

    def test_doctype_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.load_xml(b'<!DOCTYPE project [<!ENTITY p SYSTEM "file:///etc/passwd">]><project>&p;</project>')

    def test_utf16_entity_bypass_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.load_xml('<!DOCTYPE project [<!ENTITY x "x">]><project>&x;</project>'.encode("utf-16"))

    def test_normal_xml_allowed(self):
        self.assertEqual("project", gate.load_xml(b'<?xml version="1.0"?><project/>').tag)

    def test_zip_traversal_rejected(self):
        with zipfile.ZipFile(io.BytesIO(zip_bytes({"../outside": b"x"}))) as archive:
            with self.assertRaises(gate.InvalidArtifact):
                gate.archive_names(archive)

    def test_zip_absolute_path_rejected(self):
        with zipfile.ZipFile(io.BytesIO(zip_bytes({"/absolute": b"x"}))) as archive:
            with self.assertRaises(gate.InvalidArtifact):
                gate.archive_names(archive)

    def test_zip_windows_path_rejected(self):
        with zipfile.ZipFile(io.BytesIO(zip_bytes({"C:\\outside": b"x"}))) as archive:
            with self.assertRaises(gate.InvalidArtifact):
                gate.archive_names(archive)

    def test_zip_symlink_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "../outside")
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            with self.assertRaises(gate.InvalidArtifact):
                gate.archive_names(archive)

    def test_zip_duplicate_entry_rejected(self):
        buffer = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("same", b"1")
                archive.writestr("same", b"2")
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            with self.assertRaises(gate.InvalidArtifact):
                gate.archive_names(archive)

    def test_valid_archive_no_extraction(self):
        with zipfile.ZipFile(io.BytesIO(zip_bytes({"META-INF/nativecmpkit/LICENSE": b"license"}))) as archive:
            self.assertEqual({"META-INF/nativecmpkit/LICENSE"}, gate.archive_names(archive))

    def test_source_digest_is_deterministic(self):
        self.assertEqual(gate.source_digest({"z": "2", "a": "1"}), gate.source_digest({"a": "1", "z": "2"}))
        self.assertNotEqual(gate.source_digest({"a": "1"}), gate.source_digest({"a": "2"}))


class LocalPathTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "nested").mkdir()
        (self.root / "artifact.jar").write_bytes(b"jar")

    def tearDown(self):
        self.temp.cleanup()

    def test_safe_sibling_maven_url(self):
        self.assertEqual(self.root / "artifact.jar", gate.local_file(self.root, self.root / "nested", "../artifact.jar"))

    def test_missing_file_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.local_file(self.root, self.root, "missing.jar")

    def test_absolute_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.local_file(self.root, self.root, str(self.root / "artifact.jar"))

    def test_encoded_escape_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.local_file(self.root, self.root, "%2e%2e/outside")

    def test_double_encoded_escape_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.local_file(self.root, self.root, "%252e%252e/outside")

    def test_remote_repository_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.local_file(self.root, self.root, "https://example.invalid/artifact.jar")

    def test_query_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.local_file(self.root, self.root, "artifact.jar?token=never-read")

    def test_internal_symlink_rejected(self):
        (self.root / "link.jar").symlink_to("artifact.jar")
        with self.assertRaises(gate.InvalidArtifact):
            gate.local_file(self.root, self.root, "link.jar")


class NativeHeaderTest(unittest.TestCase):
    def test_elf_x64_and_arm_mismatch(self):
        data = bytearray(64)
        data[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<H", data, 18, 62)
        self.assertTrue(gate.binary_platform(data, "linux-x64"))
        self.assertFalse(gate.binary_platform(data, "linux-arm64"))

    def test_elf_arm64(self):
        data = bytearray(64)
        data[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<H", data, 18, 183)
        self.assertTrue(gate.binary_platform(data, "linux-arm64"))

    def test_macho_arm64(self):
        data = b"\xcf\xfa\xed\xfe" + struct.pack("<I", 0x0100000C)
        self.assertTrue(gate.binary_platform(data, "macos-arm64"))
        self.assertFalse(gate.binary_platform(data, "macos-x64"))

    def test_pe_x64(self):
        data = bytearray(128)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 0x3C, 80)
        data[80:84] = b"PE\0\0"
        struct.pack_into("<H", data, 84, 0x8664)
        self.assertTrue(gate.binary_platform(data, "windows-x64"))

    def test_short_or_wrong_payload_fails(self):
        for platform in gate.NATIVE_PLATFORMS:
            with self.subTest(platform=platform):
                self.assertFalse(gate.binary_platform(b"not-a-native-library", platform))

    def test_native_name_module_isolation(self):
        self.assertEqual("libcalf_filepicker_native.so", gate.native_filename("calf-file-picker", "linux-x64"))
        self.assertEqual("calf_share_native.dll", gate.native_filename("calf-share", "windows-x64"))


class RepositoryFixtureBase(unittest.TestCase):
    VERSION = "0.1.0-preview.1"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "source"
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        (self.root / "docs/migration").mkdir(parents=True)
        (self.root / "licenses").mkdir()
        (self.root / "docs/migration/identity.json").write_text(json.dumps({"modules": [{"new_artifact": "nativecmpkit-core"}]}))
        for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "licenses/fixture.txt"):
            (self.root / name).write_text("complete fixture notice " + name)
        self.make_publication("nativecmpkit-core", metadata=True)
        self.make_publication("nativecmpkit-core-desktop")

    def tearDown(self):
        self.temp.cleanup()

    def directory(self, coordinate):
        return self.repo / gate.GROUP.replace(".", "/") / coordinate / self.VERSION

    def make_publication(self, coordinate, metadata=False):
        directory = self.directory(coordinate)
        directory.mkdir(parents=True)
        prefix = f"{coordinate}-{self.VERSION}"
        notices = {gate.NOTICE_PREFIX + name: (self.root / name).read_bytes() for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "licenses/fixture.txt")}
        (directory / (prefix + "-notices.zip")).write_bytes(zip_bytes(notices))
        embedded = {name.replace(gate.NOTICE_PREFIX, gate.NOTICE_PREFIX + "calf-core/", 1): data for name, data in notices.items()}
        (directory / (prefix + ".jar")).write_bytes(zip_bytes(embedded | {"fixture.txt": b"artifact-body"}))
        (directory / (prefix + ".pom")).write_text(f'''<project xmlns="http://maven.apache.org/POM/4.0.0">
<groupId>{gate.GROUP}</groupId><artifactId>{coordinate}</artifactId><version>{self.VERSION}</version>
<name>NativeCmpKit - core</name>
<url>{gate.DESTINATION}</url><scm><url>{gate.DESTINATION}</url></scm>
<licenses><license><name>Apache-2.0</name></license></licenses>
<developers><developer><id>Apdelrahman1911</id></developer><developer><id>MohamedRejeb</id></developer></developers>
</project>''')
        artifact = directory / (prefix + ".jar")
        variants = [{"name": "runtimeElements", "files": [{"name": artifact.name, "url": artifact.name,
                     "size": artifact.stat().st_size, "sha256": gate.sha256(artifact)}]}]
        if metadata:
            variants.append({"name": "desktop", "available-at": {"group": gate.GROUP, "module": "nativecmpkit-core-desktop", "version": self.VERSION,
                "url": f"../../nativecmpkit-core-desktop/{self.VERSION}/nativecmpkit-core-desktop-{self.VERSION}.module"}})
        (directory / (prefix + ".module")).write_text(json.dumps({"formatVersion": "1.1", "component": {
            "group": gate.GROUP, "module": coordinate, "version": self.VERSION}, "variants": variants}))

    def run_gate(self):
        return gate.ArtifactVerifier(self.root, self.repo, self.VERSION, targets=["desktop"], native_platforms=["linux-x64"]).run()


class RepositoryFixtureTest(RepositoryFixtureBase):
    def test_current_pom_display_name_is_required_for_root_and_target(self):
        result = self.run_gate()
        checks = [c for c in result["checks"] if c["name"].endswith(":pom-display-name")]
        self.assertEqual(2, len(checks))
        self.assertTrue(all(c["passed"] for c in checks))

    def test_old_wrong_or_missing_pom_display_names_fail_closed(self):
        for coordinate in ("nativecmpkit-core", "nativecmpkit-core-desktop"):
            path = self.directory(coordinate) / f"{coordinate}-{self.VERSION}.pom"
            original = path.read_text()
            for replacement in ("<name>Calf - core</name>", "<name>nativeCmpkit - core</name>",
                                "<name>NativeCmpKit - another-module</name>", ""):
                with self.subTest(coordinate=coordinate, replacement=replacement):
                    path.write_text(original.replace("<name>NativeCmpKit - core</name>", replacement))
                    checks = [c for c in self.run_gate()["checks"]
                              if c["name"] == coordinate + ":pom-display-name"]
                    self.assertEqual(1, len(checks))
                    self.assertFalse(checks[0]["passed"])
            path.write_text(original)

    def test_valid_partial_fixture_passes_but_never_certifies_release(self):
        result = self.run_gate()
        self.assertTrue(result["success"], [c for c in result["checks"] if not c["passed"]])
        self.assertFalse(result["complete_declared_artifact_matrix_requested"])
        self.assertFalse(result["release_readiness_certified"])
        self.assertEqual(8, len(result["artifact_files"]))

    def test_missing_target_fails_closed(self):
        (self.directory("nativecmpkit-core-desktop") / f"nativecmpkit-core-desktop-{self.VERSION}.module").unlink()
        self.assertFalse(self.run_gate()["success"])

    def test_wrong_pom_group_fails(self):
        path = self.directory("nativecmpkit-core") / f"nativecmpkit-core-{self.VERSION}.pom"
        path.write_text(path.read_text().replace(gate.GROUP, "com.mohamedrejeb.calf"))
        self.assertFalse(self.run_gate()["success"])

    def test_missing_companion_notice_fails(self):
        (self.directory("nativecmpkit-core") / f"nativecmpkit-core-{self.VERSION}-notices.zip").unlink()
        self.assertFalse(self.run_gate()["success"])

    def test_truncated_notice_bytes_fail(self):
        path = self.directory("nativecmpkit-core") / f"nativecmpkit-core-{self.VERSION}-notices.zip"
        path.write_bytes(zip_bytes({gate.NOTICE_PREFIX + "LICENSE": b"truncated"}))
        self.assertFalse(self.run_gate()["success"])

    def test_native_payload_in_nonowning_jar_fails(self):
        directory = self.directory("nativecmpkit-core-desktop")
        path = directory / f"nativecmpkit-core-desktop-{self.VERSION}.jar"
        with zipfile.ZipFile(path, "a") as archive:
            archive.writestr("native/linux-x64/libcalf_share_native.so", b"bogus")
        self.assertFalse(self.run_gate()["success"])

    def test_tampered_jar_module_hash_fails(self):
        path = self.directory("nativecmpkit-core-desktop") / f"nativecmpkit-core-desktop-{self.VERSION}.jar"
        with path.open("ab") as stream:
            stream.write(b"unapproved change")
        self.assertFalse(self.run_gate()["success"])

    def test_upstream_transitive_coordinate_fails(self):
        path = self.directory("nativecmpkit-core-desktop") / f"nativecmpkit-core-desktop-{self.VERSION}.module"
        data = json.loads(path.read_text())
        data["variants"][0]["dependencies"] = [{"group": "com.mohamedrejeb.calf", "module": "calf-io", "version": {"requires": "1.0.0"}}]
        path.write_text(json.dumps(data))
        self.assertFalse(self.run_gate()["success"])

    def test_publisher_javafx_classifier_fails(self):
        path = self.directory("nativecmpkit-core-desktop") / f"nativecmpkit-core-desktop-{self.VERSION}.pom"
        text = path.read_text().replace("</project>", '''<dependencies><dependency><groupId>org.openjfx</groupId><artifactId>javafx-web</artifactId>
            <version>21.0.13</version><classifier>linux</classifier></dependency></dependencies></project>''')
        path.write_text(text)
        self.assertFalse(self.run_gate()["success"])

    def test_candidate_dynamic_or_snapshot_versions_rejected(self):
        for version in ("+", "latest.release", "0.1.0-SNAPSHOT", "../x", "0.1.0;echo x"):
            with self.subTest(version=version), self.assertRaises(gate.InvalidArtifact):
                gate.ArtifactVerifier(self.root, self.repo, version)

    def test_unknown_target_or_module_rejected(self):
        with self.assertRaises(gate.InvalidArtifact):
            gate.ArtifactVerifier(self.root, self.repo, self.VERSION, targets=["not-a-target"])
        with self.assertRaises(gate.InvalidArtifact):
            gate.ArtifactVerifier(self.root, self.repo, self.VERSION, modules=["not-a-module"])

    def test_full_matrix_request_cannot_pass_partial_repository(self):
        result = gate.ArtifactVerifier(self.root, self.repo, self.VERSION).run()
        self.assertTrue(result["complete_declared_artifact_matrix_requested"])
        self.assertFalse(result["success"])

    def test_empty_target_variants_cannot_hide_a_missing_library(self):
        path = self.directory("nativecmpkit-core-desktop") / f"nativecmpkit-core-desktop-{self.VERSION}.module"
        data = json.loads(path.read_text())
        data["variants"][0]["files"] = []
        path.write_text(json.dumps(data))
        self.assertFalse(self.run_gate()["success"])

    def test_metadata_listed_companion_still_requires_notices(self):
        directory = self.directory("nativecmpkit-core-desktop")
        companion = directory / f"nativecmpkit-core-desktop-{self.VERSION}-notices.zip"
        companion.write_bytes(zip_bytes({"wrong.txt": b"no notices"}))
        path = directory / f"nativecmpkit-core-desktop-{self.VERSION}.module"
        data = json.loads(path.read_text())
        data["variants"][0]["files"].append({"name": companion.name, "url": companion.name,
            "size": companion.stat().st_size, "sha256": gate.sha256(companion)})
        path.write_text(json.dumps(data))
        self.assertFalse(self.run_gate()["success"])


class NativeContractFixtureTest(RepositoryFixtureBase):
    """Synthetic ELF/oracle/Cargo fixtures. Never counted as native execution."""

    MODULE = "calf-file-picker"
    PLATFORM = "linux-x64"

    def setUp(self):
        super().setUp()
        (self.root / self.MODULE / "native").mkdir(parents=True)
        manifest = self.root / self.MODULE / "native/Cargo.toml"
        lock = self.root / self.MODULE / "native/Cargo.lock"
        manifest.write_text('[package]\nname="calf-filepicker-native"\nversion="0.1.0"\n')
        lock.write_text('''version = 4
[[package]]
name = "calf-filepicker-native"
version = "0.1.0"
[[package]]
name = "example"
version = "1.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "''' + "3" * 64 + '"\n')
        self.sources = {self.MODULE + "/native/Cargo.toml": gate.sha256(manifest)}
        # Only the oracle interface is adapted. Native object and source validation
        # is exercised by the real checker; no native code is executed by this test.
        (self.root / "scripts/native").mkdir(parents=True)
        (self.root / "scripts/native/artifacts.py").write_text(
            'SUPPORTED_PLATFORMS={"linux-x64":{"rustTarget":"x86_64-unknown-linux-gnu"}}\n'
            'def expected_source_files(root,module): return ' + repr(self.sources) + '\n'
            'def toolchain(root): return "1.98.0"\n'
            'def crate_version(root,module): return "0.1.0"\n')
        payload = bytearray(64)
        payload[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<H", payload, 18, 62)
        self.payload = bytes(payload)
        self.manifest = {
            "schemaVersion": 1, "module": self.MODULE, "platform": self.PLATFORM,
            "rustTarget": "x86_64-unknown-linux-gnu", "filename": "libcalf_filepicker_native.so",
            "sha256": hashlib.sha256(self.payload).hexdigest(), "size": len(self.payload),
            "abiVersion": 1, "crateVersion": "0.1.0", "libraryVersion": self.VERSION,
            "rustToolchain": "1.98.0", "rustcVersion": "rustc 1.98.0 (fixture)",
            "cargoVersion": "cargo 1.98.0 (fixture)", "cargoProfile": "release", "rustFlags": [],
            "sourceRevision": "a" * 40, "sourceTreeDirty": True,
            "sourceFiles": self.sources, "sourceSha256": gate.source_digest(self.sources),
        }
        self.metadata = metadata_fixture(manifest_hash=gate.sha256(manifest), lock_hash=gate.sha256(lock))
        self.notice_prefix = "META-INF/nativecmpkit/native-dependencies/" + self.MODULE + "/"
        self.notice_path = self.notice_prefix + "example-1.0.0/LICENSE"
        self.notice_bytes = b"Copyright Example\nPermission is granted.\n"
        self.license_report = {
            "schema_version": 1, "module": self.MODULE,
            "metadata_sha256": hashlib.sha256(json.dumps(self.metadata).encode()).hexdigest(),
            "cargo_toml_sha256": gate.sha256(manifest), "cargo_lock_sha256": gate.sha256(lock),
            "scope": "Synthetic fixture, not legal clearance", "complete_material_collection": True,
            "license_obligations_reviewed": False, "gaps": [],
            "packages": [{key: item[key] for key in ("name", "version", "source_kind", "license", "checksum")}
                         | {"files": []} for item in self.metadata["packages"]],
        }
        self.license_report["packages"][0]["files"] = [{"path": self.notice_path,
            "bytes": len(self.notice_bytes), "sha256": hashlib.sha256(self.notice_bytes).hexdigest()}]

    def verifier(self):
        return gate.ArtifactVerifier(self.root, self.repo, self.VERSION, targets=["desktop"], native_platforms=["linux-x64"])

    def check_native(self, without=None):
        entries = {"native/linux-x64/libcalf_filepicker_native.so": self.payload,
                   f"META-INF/nativecmpkit/native/{self.MODULE}/linux-x64.json": json.dumps(self.manifest).encode()}
        if without:
            entries.pop(without)
        verifier = self.verifier()
        with zipfile.ZipFile(io.BytesIO(zip_bytes(entries))) as archive:
            verifier.native(archive, gate.archive_names(archive), self.MODULE, self.PLATFORM, "fixture")
        return verifier.checks

    def check_notices(self, missing=None, extra=None, rehash_metadata=False):
        raw = json.dumps(self.metadata).encode()
        if rehash_metadata:
            self.license_report["metadata_sha256"] = hashlib.sha256(raw).hexdigest()
        entries = {self.notice_path: self.notice_bytes,
                   self.notice_prefix + "metadata.json": raw,
                   self.notice_prefix + "licenses-report.json": json.dumps(self.license_report).encode()}
        if missing:
            entries.pop(missing)
        if extra:
            entries.update(extra)
        verifier = self.verifier()
        with zipfile.ZipFile(io.BytesIO(zip_bytes(entries))) as archive:
            verifier.native_notices(archive, gate.archive_names(archive), self.MODULE, "fixture")
        return verifier.checks

    def assert_passes(self, checks):
        self.assertTrue(checks)
        self.assertTrue(all(check["passed"] for check in checks), [check for check in checks if not check["passed"]])

    def assert_fails(self, checks, name_part):
        self.assertTrue(any(not check["passed"] and name_part in check["name"] for check in checks), checks)

    def test_complete_synthetic_native_manifest_matches_contract(self):
        self.assert_passes(self.check_native())

    def test_native_manifest_missing_fails(self):
        self.assert_fails(self.check_native(without=f"META-INF/nativecmpkit/native/{self.MODULE}/linux-x64.json"), "native-present")

    def test_native_payload_tampering_fails(self):
        self.payload += b"tamper"
        self.assert_fails(self.check_native(), "native-bytes")

    def test_native_manifest_schema_boolean_not_an_integer(self):
        self.manifest["schemaVersion"] = True
        self.assert_fails(self.check_native(), "native-manifest-identity")

    def test_native_wrong_library_version_fails(self):
        self.manifest["libraryVersion"] = "0.0.1"
        self.assert_fails(self.check_native(), "native-manifest-identity")

    def test_native_source_subset_cannot_fake_completeness(self):
        self.manifest["sourceFiles"] = {"arbitrary-selected-input": "2" * 64}
        self.manifest["sourceSha256"] = gate.source_digest(self.manifest["sourceFiles"])
        self.assert_fails(self.check_native(), "native-source-complete")

    def test_native_wrong_rust_target_fails(self):
        self.manifest["rustTarget"] = "aarch64-apple-darwin"
        self.assert_fails(self.check_native(), "native-rust-target")

    def test_native_claimed_toolchain_differs_from_actual_versions(self):
        self.manifest["cargoVersion"] = "cargo 1.97.0 (fixture)"
        self.assert_fails(self.check_native(), "native-toolchain")

    def test_native_custom_profile_flags_fail(self):
        self.manifest["rustFlags"] = ["unreviewed-flag"]
        self.assert_fails(self.check_native(), "native-release-profile")

    def test_native_source_dirtiness_must_be_explicit(self):
        self.manifest.pop("sourceTreeDirty")
        self.assert_fails(self.check_native(), "native-dirty-flag")

    def test_native_source_oracle_required(self):
        (self.root / "scripts/native/artifacts.py").unlink()
        self.assert_fails(self.check_native(), "native-source-complete")

    def test_complete_dependency_material_is_not_legal_certification(self):
        self.assert_passes(self.check_notices())
        self.assertFalse(self.license_report["license_obligations_reviewed"])

    def test_dependency_metadata_report_missing_fails(self):
        self.assert_fails(self.check_notices(missing=self.notice_prefix + "metadata.json"), "native-license-report")

    def test_dependency_metadata_hash_tampering_fails(self):
        self.license_report["metadata_sha256"] = "0" * 64
        self.assert_fails(self.check_notices(), "native-license-metadata-hash")

    def test_dependency_lock_input_mismatch_fails(self):
        self.license_report["cargo_lock_sha256"] = "0" * 64
        self.assert_fails(self.check_notices(), "native-license-inputs")

    def test_dependency_registry_package_missing_from_notice_report(self):
        self.license_report["packages"].pop(0)
        self.assert_fails(self.check_notices(), "native-license-lock-coverage")

    def test_dependency_metadata_graph_must_match_report(self):
        self.metadata["packages"][0]["license"] = "BSD-3-Clause"
        self.assert_fails(self.check_notices(rehash_metadata=True), "native-license-metadata-packages")

    def test_dependency_duplicate_notice_record_fails(self):
        self.license_report["packages"].append(self.license_report["packages"][0])
        self.assert_fails(self.check_notices(), "native-license-parse")

    def test_dependency_raw_private_metadata_fields_rejected(self):
        self.metadata["packages"][0]["manifest_path"] = "not-a-distributable-field"
        self.assert_fails(self.check_notices(rehash_metadata=True), "native-license-parse")

    def test_dependency_unrecorded_stale_material_fails(self):
        self.assert_fails(self.check_notices(extra={self.notice_prefix + "stale.txt": b"not in graph"}), "native-license-no-stale-material")

    def test_dependency_license_text_loss_fails(self):
        self.assert_fails(self.check_notices(missing=self.notice_path), "entry-path")

    def test_dependency_license_text_tampering_fails(self):
        self.notice_bytes += b"changed"
        self.assert_fails(self.check_notices(), "entry-bytes")

    def test_dependency_spdx_alone_is_not_permission_text(self):
        self.license_report["packages"][0]["files"] = []
        self.assert_fails(self.check_notices(), "text-present")

    def test_dependency_record_cannot_point_outside_owning_crate(self):
        self.license_report["packages"][0]["files"][0]["path"] = self.notice_prefix + "foreign-1.0.0/LICENSE"
        self.assert_fails(self.check_notices(), "entry-path")

    def test_copying_source_code_cannot_satisfy_license_text_gate(self):
        self.notice_path = self.notice_prefix + "example-1.0.0/src/copying.rs"
        self.license_report["packages"][0]["files"][0]["path"] = self.notice_path
        self.assert_fails(self.check_notices(), "entry-kind")


if __name__ == "__main__":
    unittest.main()
