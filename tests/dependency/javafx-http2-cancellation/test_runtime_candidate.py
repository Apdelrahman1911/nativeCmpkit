"""NEW artifact/source/selection guards only; zero JavaFX/native executions."""
from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import build_runtime_candidate as candidate
import probe_runner as probe
import run_library_candidate as library_candidate


class ArtifactCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / "original.jar"
        self.output = self.root / "candidate.jar"
        self.members = {"META-INF/MANIFEST.MF": b"Manifest-Version: 1.0\r\n\r\n",
                        "module-info.class": b"original-module-descriptor",
                        "com/sun/webkit/network/HTTP2Loader.class": b"old-owning-class",
                        "javafx/scene/web/WebEngine.class": b"unchanged-public-api",
                        "jfxwebkit.dll": b"unchanged-native-payload"}
        self.make(self.members)

    def make(self, members):
        with zipfile.ZipFile(self.original, "w") as z:
            for name, payload in members.items(): z.writestr(name, payload)

    def transform(self, replacements=None, additions=None):
        return candidate.write_archive(self.original,self.output,
            replacements if replacements is not None else {"com/sun/webkit/network/HTTP2Loader.class": b"new-owning-class"},
            additions if additions is not None else {"META-INF/nativecmpkit/NOTICE": b"not-published"})

    def test_only_owning_payload_changes_and_original_native_module_api_are_held(self):
        before = self.original.read_bytes()
        result = self.transform()
        self.assertEqual(before,self.original.read_bytes())
        self.assertEqual(result["changed_payload_members"],["com/sun/webkit/network/HTTP2Loader.class"])
        self.assertEqual(result["retained_payload_members"],4)
        with zipfile.ZipFile(self.output) as z:
            for name in ("module-info.class","javafx/scene/web/WebEngine.class","jfxwebkit.dll"):
                self.assertEqual(z.read(name),self.members[name])

    def test_existing_output_is_not_overwritten(self):
        self.output.write_bytes(b"prior evidence")
        with self.assertRaisesRegex(ValueError,"already exists"): self.transform()
        self.assertEqual(self.output.read_bytes(),b"prior evidence")

    def test_missing_replacement_refuses_before_output(self):
        with self.assertRaisesRegex(ValueError,"Replacement missing"):
            self.transform({"unknown.class": b"injected"})
        self.assertFalse(self.output.exists())

    def test_added_original_provider_overlap_refuses(self):
        with self.assertRaisesRegex(ValueError,"overlaps"):
            self.transform(additions={"javafx/scene/web/WebEngine.class": b"shadow"})

    def test_added_traversal_refuses_before_output(self):
        with self.assertRaisesRegex(ValueError,"Unsafe added"):
            self.transform(additions={"../outside": b"x"})
        self.assertFalse(self.output.exists())

    def test_duplicate_upstream_members_are_refused(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore",UserWarning)
            with zipfile.ZipFile(self.original,"a") as z: z.writestr("module-info.class",b"second")
        with self.assertRaisesRegex(ValueError,"duplicate"): self.transform()

    def test_upstream_traversal_is_refused(self):
        self.make({**self.members,"../outside":b"x"})
        with self.assertRaisesRegex(ValueError,"Unsafe archive"): self.transform()

    def test_signed_upstream_is_refused_without_stripping(self):
        self.make({**self.members,"META-INF/ORIGINAL.RSA":b"signature"})
        before = self.original.read_bytes()
        with self.assertRaisesRegex(ValueError,"Signed dependency"): self.transform()
        self.assertEqual(before,self.original.read_bytes())

    def test_already_modified_upstream_is_refused(self):
        self.make({**self.members,"META-INF/nativecmpkit/NOTICE":b"prior"})
        with self.assertRaisesRegex(ValueError,"Already modified"): self.transform()

    def test_unknown_compression_is_refused(self):
        with zipfile.ZipFile(self.original,"w",compression=zipfile.ZIP_BZIP2) as z:
            z.writestr("some.class",b"x")
        with self.assertRaisesRegex(ValueError,"unknown"): self.transform()

    def test_notice_is_dated_header_preserved_and_line_count_unchanged_except_fix(self):
        original = b"/*\n * Original GPL header\n */\n\npackage com.sun.webkit.network;\n"
        fixed = original + b"// added fix line1\n// added fix line2\n// added fix line3\n"
        with patch.object(probe,"patch_source",return_value=fixed),patch.object(probe,"compare_patch"):
            changed = candidate.modified_source(original)
        self.assertIn(candidate.NOTICE,changed)
        self.assertTrue(changed.startswith(b"/*\n * Original GPL header\n */\n"))
        self.assertEqual(changed.count(b"\n"),original.count(b"\n")+3)

    def test_changed_header_boundary_is_refused(self):
        original = b"/* header */\npackage changed;\n"
        with patch.object(probe,"patch_source",return_value=original),patch.object(probe,"compare_patch"):
            with self.assertRaisesRegex(ValueError,"header boundary"): candidate.modified_source(original)

    def test_exact_upstream_source_pin_refuses_unrecognized_source(self):
        with self.assertRaisesRegex(ValueError,"Unexpected upstream source"): candidate.modified_source(b"unknown")

    def test_class_and_legal_inventories_are_fixed(self):
        self.assertEqual(len(candidate.CLASS_SHA256),5)
        self.assertEqual(set(candidate.CLASS_SHA256),{"HTTP2Loader.class","HTTP2Loader$1.class","HTTP2Loader$1$1.class","HTTP2Loader$2.class","HTTP2Loader$3.class"})
        for name,digest in candidate.LEGAL.items():
            self.assertEqual(probe.digest((candidate.HERE/name).read_bytes()),digest)

    def test_manifest_marks_private_not_published_without_changing_jpms_name(self):
        result = self.transform({"META-INF/MANIFEST.MF":candidate.CANDIDATE_MANIFEST})
        self.assertIn(b"NativeCmpKit-Publication-Ready: false",candidate.CANDIDATE_MANIFEST)
        with zipfile.ZipFile(self.output) as z:
            self.assertEqual(z.read("module-info.class"),self.members["module-info.class"])
        self.assertEqual(result["changed_payload_members"],["META-INF/MANIFEST.MF"])


class LibraryCandidateTests(unittest.TestCase):
    def test_exact_current_plan_has_only_original_failed_windows_stop(self):
        plan = library_candidate.focused_plan(library_candidate.ROOT)
        self.assertEqual(plan["expected"][0]["test_filter"],library_candidate.SELECTOR)
        self.assertEqual(len(plan["expected"][0]["required_testcases"]),1)
        self.assertFalse(plan["complete_suite_requested"])

    def test_other_host_refuses_before_library_or_compiler_start(self):
        with patch.object(probe,"classifier",return_value="linux"),patch.object(candidate,"build") as build:
            with self.assertRaisesRegex(ValueError,"only on Windows"):
                library_candidate.run(argparse.Namespace(output="build/ci-verification/test",download=False))
        build.assert_not_called()

    def test_candidate_command_retains_exact_filter_freshness_and_serial_permissions(self):
        root=library_candidate.ROOT
        plan=library_candidate.focused_plan(root)
        manifest={"passed":True,"classifier":"win","identity":candidate.IDENTITY,"jar_sha256":"a"*64}
        with patch.object(library_candidate.library.platform,"system",return_value="Windows"),patch.object(library_candidate.library.platform,"machine",return_value="AMD64"):
            argv=library_candidate.command(root,plan,root/"build/ci-verification/owned",manifest)
        self.assertIn("--max-workers=1",argv); self.assertIn("--no-parallel",argv)
        self.assertIn("--no-build-cache",argv); self.assertIn("--no-configuration-cache",argv)
        self.assertEqual(argv.count("--tests"),1)
        self.assertEqual(argv[argv.index("--tests")+1],library_candidate.SELECTOR)
        self.assertFalse(any("useHTTP2Loader" in v or v=="--patch-module" for v in argv))

    def test_missing_or_duplicate_actual_replacement_marker_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            log=Path(d)/"gradle.log";log.write_text("no native marker\n")
            with self.assertRaisesRegex(ValueError,"marker missing"): library_candidate.marker(log,{"original_web_sha256":"a"*64,"jar_sha256":"b"*64})

    def test_exact_actual_replacement_marker_is_required(self):
        with tempfile.TemporaryDirectory() as d:
            log=Path(d)/"gradle.log"
            row=("NATIVECMPKIT_JAVAFX_CANDIDATE task=:calf-webview:desktopTest originalRemoved=1 candidateCount=1 "
                 "originalSha256="+"a"*64+" candidateSha256="+"b"*64+" runtimeModulePatch=false privateRouteOverride=false\n")
            log.write_text(row)
            self.assertEqual(library_candidate.marker(log,{"original_web_sha256":"a"*64,"jar_sha256":"b"*64})["original_removed"],1)
            log.write_text(row+row)
            with self.assertRaisesRegex(ValueError,"duplicate"): library_candidate.marker(log,{"original_web_sha256":"a"*64,"jar_sha256":"b"*64})

    def test_init_replaces_original_provider_instead_of_shadowing_or_private_module_patch(self):
        text=(library_candidate.ROOT/library_candidate.INIT).read_text()
        self.assertIn("originalFiles.filterNot { it == original } + candidate",text)
        self.assertIn("webProviders.size == 1",text)
        self.assertIn("candidateDigest(original) == originalSha",text)
        self.assertIn("candidateDigest(candidate) == expected",text)
        self.assertIn("original !in classpath.files",text)
        self.assertIn("outputs.doNotCacheIf",text)
        self.assertNotIn('systemProperty("com.sun.webkit.useHTTP2Loader"',text)


class CandidateCacheAndWorkflowTests(unittest.TestCase):
    def test_new_cache_reuses_exact_bytes_without_network_or_source_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);home=root/"home"
            payload=b"cached exact test-only synthetic artifact"
            name="javafx-web-21.0.13-sources.jar"
            file=home/".gradle/caches/modules-2/files-2.1/org.openjfx/javafx-web/21.0.13/owned"/name
            file.parent.mkdir(parents=True);file.write_bytes(payload)
            row={"file":name,"url":"https://repo.maven.apache.org/maven2/org/openjfx/javafx-web/21.0.13/"+name,
                 "bytes":len(payload),"sha256":probe.digest(payload)}
            result=library_candidate.seed_official_cache(root/"out",{"sources":row,"platforms":{"win":[]}},home)
            self.assertEqual(len(result),1);self.assertEqual(file.read_bytes(),payload)
            self.assertEqual((root/"out"/name).read_bytes(),payload)

    def test_changed_restored_cache_refuses_without_deleting_or_refreshing_it(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);home=root/"home";name="javafx-web-21.0.13-sources.jar"
            file=home/".gradle/caches/modules-2/files-2.1/org.openjfx/javafx-web/21.0.13/owned"/name
            file.parent.mkdir(parents=True);file.write_bytes(b"changed")
            row={"file":name,"url":"https://repo.maven.apache.org/maven2/org/openjfx/javafx-web/21.0.13/"+name,
                 "bytes":7,"sha256":"0"*64}
            with self.assertRaisesRegex(ValueError,"Restored official dependency differs"):
                library_candidate.seed_official_cache(root/"out",{"sources":row,"platforms":{"win":[]}},home)
            self.assertEqual(file.read_bytes(),b"changed")

    def test_cache_absence_is_not_claimed_as_a_reused_result(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);name="javafx-web-21.0.13-sources.jar"
            row={"file":name,"url":"https://repo.maven.apache.org/maven2/org/openjfx/javafx-web/21.0.13/"+name,
                 "bytes":1,"sha256":"0"*64}
            self.assertEqual(library_candidate.seed_official_cache(root/"out",{"sources":row,"platforms":{"win":[]}},root/"home"),[])

    def test_task_arguments_include_exact_task_specific_selector_without_full_suite_fallback(self):
        text=(library_candidate.ROOT/library_candidate.INIT).read_text()
        self.assertIn('startParameter.taskNames == listOf(":calf-webview:desktopTest", "--tests", selected)',text)
        self.assertIn("setIncludePatterns(selected)",text)
        self.assertNotIn("startParameter.taskNames.contains",text)

    def test_workflow_has_one_windows_reservation_read_only_no_default_adoption_or_binary_upload(self):
        text=(library_candidate.ROOT/library_candidate.WORKFLOW).read_text()
        self.assertIn("runs-on: windows-2025",text);self.assertIn("contents: read",text)
        self.assertNotIn("packages: write",text);self.assertNotIn("id-token:",text)
        self.assertNotIn("matrix:",text);self.assertIn("persist-credentials: false",text)
        self.assertNotIn("actions/cache/save",text);self.assertNotIn("restore-keys:",text)
        upload=text.split("path: |",1)[1].split("      - name: Validate",1)[0]
        self.assertNotIn("build-cache",upload)
        artifacts=text.split("name: Preserve verification receipts only",1)[1]
        self.assertNotIn("*.jar",artifacts);self.assertNotIn("*.class",artifacts)
        self.assertIn("runtime-candidate/*.json",artifacts)


class JavaSetupContractTests(unittest.TestCase):
    def test_signature_input_uses_the_existing_verified_action_revision_not_v4(self):
        text=(library_candidate.ROOT/library_candidate.WORKFLOW).read_text()
        parent=(library_candidate.ROOT/".github/workflows/gradle.yml").read_text()
        expected="actions/setup-java@b6effb05e454b25005698d916606bdc6ffcbf961"
        self.assertIn(expected,parent);self.assertIn(expected,text)
        self.assertIn("verify-signature: true",text)
        self.assertNotIn("actions/setup-java@v4",text)


if __name__ == "__main__": unittest.main()
