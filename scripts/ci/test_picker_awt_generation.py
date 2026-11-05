"""Eight essential NEW source controls; all host/process/native inputs synthetic.

No Gradle, Java, JNI, Rust, AWT, AppKit, Git, real runtime capture or signalling
occurs here. These controls do not execute807 or the accepted actual-JVM2 pair.
"""
from contextlib import ExitStack, redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

import picker_awt_generation as r


def budget(clock=None):
    return r.shared.NativeBudget(clock=(lambda: 0) if clock is None else clock)


def inventory():
    return ("Classfile /synthetic/owned.class\npublic final class " + r.CLASS + "\n"
            "  super_class: #4 // java/lang/Object\nConstant pool:\n"
            "  #5 = Utf8 Lorg/junit/Test;\n{\n  public " + r.CLASS + "();\n"
            "    descriptor: ()V\n    flags: (0x0001) ACC_PUBLIC\n"
            "  public final void " + r.METHOD + "();\n    descriptor: ()V\n"
            "    flags: (0x0011) ACC_PUBLIC, ACC_FINAL\n    RuntimeVisibleAnnotations:\n"
            "      0: #5()\n        org.junit.Test\n"
            "  private final void closeOwned();\n    descriptor: ()V\n    flags: (0x0012) ACC_PRIVATE, ACC_FINAL\n}\n")


def junit():
    return "JUnit version 4.13.2\n." + r.SUCCESS_MARKER + "\nTime: 0.125\n\nOK (1 test)\n"


def preparation():
    return "\n".join("> Task " + task for task in (":calf-file-picker:buildNativeLib", *r.PREPARE_TASKS)) + "\nBUILD SUCCESSFUL in 1s\n"


def good_phase():
    return {"started": True, "exit_code": 0, "capture_complete": True, "captured_bytes": 9,
            "private_capture_sha256": "a" * 64, "post_exit_group_state": "absent", "stop_reason": None,
            "elapsed_seconds": 0.1, "command": ["PRIVATE_SYNTHETIC_OPERAND"]}


def runtime(revision):
    return {"source_revision": revision, "source_tree_dirty": False, "host": {"system": "Darwin", "architecture": "arm64"},
            "java": {"major": 17, "version": "17.0.20"}, "rust": {"release": "1.98.0", "host": r.shared.TARGET},
            "compiler_runtime_fingerprint": "b" * 64}


class PickerAwtGenerationSourceControls(unittest.TestCase):
    def test_exact_standard_prepare_inventory_and_junit_have_one_target_no_custom_host_or_old_replay(self):
        root, java = Path("/qualified-root"), Path("/qualified-jdk")
        private = root / "build/ci-verification/new/private"
        properties = ["-Duser.home=" + (private / "java-home").as_posix(),
                      "-Djava.io.tmpdir=" + (private / "java-tmp").as_posix()]
        environment = dict(os.environ)
        self.assertEqual(["/usr/bin/env", "JDK_JAVA_OPTIONS=" + " ".join(properties), "./gradlew", "--no-daemon",
                          "--console=plain", "--max-workers=2", "--gradle-user-home",
                          "build/ci-verification/new/private/gradle-home",
                          "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8 " + " ".join(properties),
                          "-Pkotlin.daemon.jvmargs=-Xmx1536m " + " ".join(properties),
                          "-PnativecmpkitNativeMode=host", *r.PREPARE_TASKS],
                         r.prepare_command(root, private))
        self.assertEqual(["/qualified-jdk/bin/javap", *("-J" + item for item in properties),
                          "-p", "-v", "-classpath", "/held/classpath", r.CLASS],
                         r.exact_command(java, "/held/classpath", root, private, inventory=True))
        self.assertEqual(["/qualified-jdk/bin/java", "-Xcheck:jni", *properties,
                          "-Dnativecmpkit.picker.trustSystemLibrary=false", "-cp", "/held/classpath",
                          "org.junit.runner.JUnitCore", r.CLASS], r.exact_command(java, "/held/classpath", root, private))
        self.assertEqual(environment, dict(os.environ))
        self.assertEqual(600, r.shared.NATIVE_BUDGET_SECONDS)
        self.assertEqual(0, r.review_prepare(preparation())["executed_tests"])
        for changed in (preparation().replace("buildNativeLib\n", "buildNativeLib UP-TO-DATE\n"),
                        preparation().replace(r.PREPARE_TASKS[0], ":calf-file-picker:desktopTest"),
                        preparation() + "\nBUILD FAILED\n", preparation() + "\n> Task :calf-share:desktopTest\n"):
            with self.assertRaises(r.Refusal):
                r.review_prepare(changed)
        for wrong in (Path("/elsewhere/private/gradle-home"), root / "build/ci-verification/new/public/gradle-home",
                      root / "build/ci-verification/new/private/java-home", root / "build/ci-verification/unsafe name/private"):
            with self.assertRaises(r.Refusal):
                r.prepare_command(root, wrong)
            with self.assertRaises(r.Refusal):
                r.exact_command(java, "/held/classpath", root, wrong)
        source = (r.library.ROOT / "scripts/ci/picker_awt_generation.py").read_text()
        for required in ("shared.owned_phase(", "shared.read_private_log(", "shared.require_runtime(", "shared.require_phase_success(",
                         '"JDK_JAVA_OPTIONS=" + " ".join(properties)', '"-Duser.home="', '"-Djava.io.tmpdir="',
                         '*("-J" + item for item in properties)', "os.O_DIRECTORY | os.O_NOFOLLOW"):
            self.assertIn(required, source)
        self.assertEqual(1, source.count("budget = shared.NativeBudget()"))
        for forbidden in ("subprocess.Popen", "subprocess.run", "library.execute(", "--rerun-tasks", "--add-opens", "-XstartOnFirstThread",
                          'os.environ["JDK_JAVA_OPTIONS"] ='):
            self.assertNotIn(forbidden, source)

    def test_source_default_version_qualified_jdk_and_inherited_overrides_refuse_without_echoing_values(self):
        for name in ("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "JAVA_OPTS", "GRADLE_OPTS", "GRADLE_USER_HOME",
                     "ORG_GRADLE_PROJECT_nativeCmpkit.version", "DYLD_INSERT_LIBRARIES", "RUSTC_WRAPPER", "CARGO_PROFILE_RELEASE_LTO"):
            with self.subTest(name=name), self.assertRaises(r.Refusal) as caught:
                r.reject_overrides({name: "PRIVATE_VALUE_DO_NOT_ECHO"})
            self.assertNotIn("PRIVATE_VALUE", str(caught.exception))
        r.reject_overrides({"JAVA_HOME": "/qualified", "RUSTUP_TOOLCHAIN": "1.98.0", "JAVA_TOOL_OPTIONS": ""})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "gradle").mkdir()
            (root / "build.gradle.kts").write_text('val nativeCmpkitVersion = providers.gradleProperty("nativeCmpkit.version")\n'
                                                   '    .orElse("${libs.versions.nativecmpkit.get()}-SNAPSHOT")\n')
            standard_args = "org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8\nkotlin.daemon.jvmargs=-Xmx1536m\n"
            (root / "gradle.properties").write_text(standard_args)
            catalog = root / "gradle/libs.versions.toml"
            catalog.write_text('[versions]\njava = "17"\njunit = "4.13.2"\nnativecmpkit = "0.1.0"\n')
            self.assertEqual("0.1.0-SNAPSHOT", r.default_version(root, budget()))
            (root / "gradle.properties").write_text("nativeCmpkit.version=9.9.9\n")
            with self.assertRaises(r.Refusal): r.default_version(root, budget())
            (root / "gradle.properties").write_text(standard_args.replace("-Xmx2048m", "-Xmx1024m"))
            with self.assertRaises(r.Refusal): r.default_version(root, budget())
            (root / "gradle.properties").write_text(standard_args)
            catalog.write_text(catalog.read_text().replace('junit = "4.13.2"', 'junit = "4.13.1"'))
            with self.assertRaises(r.Refusal): r.default_version(root, budget())
            home = root / "jdk"
            for name in r.JDK_FILES:
                path = home / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic runtime bytes")
                if name in {"bin/java", "bin/javap"}: path.chmod(0o755)
            (home / "release").write_text('JAVA_VERSION="17.0.20"\nIMPLEMENTOR="Eclipse Adoptium"\n')
            startup_env = home / "bin/startup-env"
            startup_env.write_bytes(b"synthetic launcher env bytes; never executed")
            startup_env.chmod(0o755)
            with mock.patch.dict(os.environ, {"JAVA_HOME": home.as_posix()}, clear=True), mock.patch.object(r.shutil, "which", return_value=(home / "bin/java").as_posix()), mock.patch.object(r, "GRADLE_STARTUP_ENV", startup_env):
                selected, identity = r.qualify_jdk(runtime("a" * 40), budget())
                self.assertEqual(home, selected)
                self.assertEqual(set(r.JDK_FILES), set(identity["selected_runtime_files"]))
                self.assertEqual(len(startup_env.read_bytes()), identity["gradle_startup_env"]["size"])
                startup_env.chmod(0o644)
                with self.assertRaises(r.Refusal): r.qualify_jdk(runtime("a" * 40), budget())
                startup_env.chmod(0o755)
                (home / "release").write_text('JAVA_VERSION="17.0.20"\nIMPLEMENTOR="Unqualified vendor"\n')
                with self.assertRaises(r.Refusal): r.qualify_jdk(runtime("a" * 40), budget())

    def test_full_ordered_classpath_holds_every_byte_and_refuses_duplicate_missing_hidden_or_changed_origins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            owned = root / "build/classes"
            for resource in r.REQUIRED_RESOURCES:
                path = owned / resource
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(("synthetic " + resource).encode())
            (owned / "empty-ordinary-resource").write_bytes(b"")
            jar = root / "build/cache/library.jar"
            jar.parent.mkdir()
            with zipfile.ZipFile(jar, "w") as archive:
                archive.writestr("ordinary.txt", "held unrelated dependency member")
                archive.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n\n")
            textfile = root / "calf-file-picker/build/native-boundary-runtime/classpath.txt"
            textfile.parent.mkdir(parents=True)
            original = owned.as_posix() + "\n" + jar.as_posix() + "\n"
            textfile.write_text(original)
            cp_text, first = r.classpath_identity(root, budget())
            self.assertEqual(os.pathsep.join((owned.as_posix(), jar.as_posix())), cp_text)
            self.assertEqual(6, first["file_count"])
            self.assertEqual(first, r.classpath_identity(root, budget())[1])
            native = {"files": {name: first["resources"][name][0] for name in (r.NATIVE_RESOURCE, r.MANIFEST_RESOURCE)}}
            r.require_bundled_identity(first, native)
            forged = copy.deepcopy(native)
            forged["files"][r.NATIVE_RESOURCE]["sha256"] = "0" * 64
            with self.assertRaises(r.Refusal): r.require_bundled_identity(first, forged)
            with zipfile.ZipFile(jar, "a") as archive: archive.writestr("new-unrelated.txt", "changed byte held too")
            self.assertNotEqual(first, r.classpath_identity(root, budget())[1])
            duplicate = root / "build/duplicate"
            (duplicate / r.TEST_RESOURCE).parent.mkdir(parents=True)
            (duplicate / r.TEST_RESOURCE).write_bytes(b"synthetic duplicate test origin")
            for changed in (original + duplicate.as_posix() + "\n", original + owned.as_posix() + "\n",
                            original.rstrip("\n"), original.replace("\n", "\r\n"), original.replace(owned.as_posix(), root.as_posix())):
                textfile.write_text(changed)
                with self.assertRaises(r.Refusal): r.classpath_identity(root, budget())
            textfile.write_text(original)
            with zipfile.ZipFile(jar, "w") as archive: archive.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nClass-Path: foreign.jar\n")
            with self.assertRaises(r.Refusal): r.classpath_identity(root, budget())
            with zipfile.ZipFile(jar, "w") as archive: archive.writestr("META-INF/versions/17/" + r.TEST_RESOURCE, b"hidden versioned origin")
            with self.assertRaises(r.Refusal): r.classpath_identity(root, budget())

    def test_fd_path_symlink_hardlink_byte_count_and_directory_bounds_do_not_certify_changed_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / "owned.bin"
            path.write_bytes(b"1234")
            identity, body, _ = r.held_file(path, budget(), maximum=4, collect=True)
            self.assertEqual(b"1234", body)
            self.assertEqual(4, identity["size"])
            with self.assertRaises(r.Refusal): r.held_file(path, budget(), maximum=3)
            with mock.patch.object(r, "MAX_TOTAL_BYTES", 3), self.assertRaises(r.Refusal): r.held_file(path, budget(), limits=[0, 0])
            linked = root / "linked.bin"
            linked.symlink_to(path)
            with self.assertRaises(r.Refusal): r.held_file(linked, budget())
            linked.unlink()
            os.link(path, linked)
            with self.assertRaises(r.Refusal): r.held_file(path, budget())
            linked.unlink()
            original_stat = path.stat()
            changed = SimpleNamespace(**{name: getattr(original_stat, name) for name in (
                "st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid", "st_size", "st_mtime_ns", "st_ctime_ns")})
            changed.st_ino += 1
            with mock.patch.object(r.os, "stat", return_value=changed), self.assertRaises(r.Refusal): r.held_file(path, budget())
            folder = root / "classes"
            folder.mkdir()
            (folder / "foreign-link").symlink_to(path)
            with self.assertRaises(r.Refusal): r.directory_identity(folder, budget(), [0, 0])
            (folder / "foreign-link").unlink()
            with mock.patch.object(r, "MAX_FILES", 0), self.assertRaises(r.Refusal): r.directory_identity(folder, budget(), [0, 0])

            private = root / "build/ci-verification/owned/private"
            private.mkdir(parents=True, mode=0o700)
            private.parent.chmod(0o700)
            owned = r.OwnedJavaDirectories(root, private, budget())
            try:
                first = owned.identity()
                self.assertEqual({"output", "private", "home", "tmp", "gradle", "cache_parent", "native_cache"}, set(first))
                self.assertEqual("build/ci-verification/owned/private/java-home/.cache/nativecmpkit-filepicker", first["native_cache"]["path"])
                self.assertTrue(all(item["stat5"][2] & 0o7777 == 0o700 for item in first.values()))
                cache_payload = private / "java-home/.cache/nativecmpkit-filepicker/synthetic-extraction"
                cache_payload.write_bytes(b"owned synthetic cache content can change")
                (private / "java-tmp/owned-native-fallback").mkdir(mode=0o700)
                owned.require()
                self.assertEqual(first, owned.identity())
                cache = private / "java-home/.cache/nativecmpkit-filepicker"
                cache.chmod(0o750)
                with self.assertRaises(r.Refusal): owned.require()
                cache.chmod(0o700)
                owner = os.geteuid()
                with mock.patch.object(r.os, "geteuid", return_value=owner + 1), self.assertRaises(r.Refusal): owned.require()
                temporary = private / "java-tmp"
                held = private / "java-tmp-held"
                temporary.rename(held)
                temporary.mkdir(mode=0o700)
                with self.assertRaises(r.Refusal): owned.require()
                temporary.rmdir()
                temporary.symlink_to(held, target_is_directory=True)
                with self.assertRaises(r.Refusal): owned.require()
                temporary.unlink()
                held.rename(temporary)
                owned.require()
                self.assertEqual(first, owned.identity())
            finally:
                owned.close()
            self.assertEqual({}, owned.descriptors)
            self.assertTrue(cache_payload.is_file())
            occupied = root / "build/ci-verification/occupied/private"
            occupied.mkdir(parents=True, mode=0o700)
            occupied.parent.chmod(0o700)
            (occupied / "java-home").symlink_to(folder, target_is_directory=True)
            with self.assertRaises(r.Refusal): r.OwnedJavaDirectories(root, occupied, budget())
            self.assertTrue((occupied / "java-home").is_symlink())

    def test_javap_inventory_is_exactly_one_compiled_instance_annotation_not_constant_pool_or_inheritance(self):
        body = inventory()
        self.assertEqual({"classname": r.CLASS, "method": r.METHOD, "annotated_tests": 1, "inventory_executed_tests": 0}, r.review_inventory(body))
        test_section = body.split("  public final void ", 1)[1].split("  private final void ", 1)[0]
        duplicate = body.replace("  private final void closeOwned();", "  public final void " + test_section + "  private final void closeOwned();")
        variants = (body.replace("        org.junit.Test\n", ""), duplicate,
                    body.replace(r.METHOD, "foreignMethod"), body.replace("descriptor: ()V", "descriptor: (J)V"),
                    body.replace("ACC_PUBLIC, ACC_FINAL", "ACC_PUBLIC, ACC_FINAL, ACC_STATIC"),
                    body.replace("org.junit.Test\n", "org.junit.Test\n        org.junit.Ignore\n"),
                    body + "    org.junit.runner.RunWith(\n", body.replace("// java/lang/Object", "// synthetic/InheritedTests"),
                    body.replace("public final class " + r.CLASS, "public final class " + r.CLASS + " extends ForeignRunner"))
        for changed in variants:
            with self.subTest(variant=variants.index(changed)), self.assertRaises(r.Refusal): r.review_inventory(changed)

    def test_junit_ok1_needs_one_post_finally_marker_and_no_failure_assumption_native_warning_or_cleanup_error(self):
        self.assertEqual(1, r.review_junit(junit())["tests"])
        marker = "." + r.SUCCESS_MARKER + "\n"
        variants = (junit().replace(marker, ".\n"), junit().replace(marker, marker + marker), junit() + "OK (1 test)\n",
                    junit().replace("OK (1 test)", "OK (0 tests)"), junit().replace("Time: 0.125\n", ""),
                    junit().replace(marker, "AssumptionViolatedException: no macOS\n"),
                    junit().replace(marker, "FAILURES!!!\n" + marker), junit().replace(marker, "WARNING in native method\n" + marker),
                    junit().replace(marker, "JNI DETECTED ERROR\n" + marker), junit() + "cleanup failed after summary\n",
                    junit().replace("JUnit version 4.13.2", "JUnit version 4.13.1"))
        for changed in variants:
            with self.subTest(variant=variants.index(changed)), self.assertRaises(r.Refusal): r.review_junit(changed)
        source = (r.library.ROOT / r.TEST_SOURCE).read_text()
        self.assertEqual(1, source.count(r.SUCCESS_MARKER))
        boundary = "        } finally {\n            closeOwned(handles, window, primary)\n        }\n"
        self.assertIn(boundary, source)
        self.assertLess(source.index(boundary), source.index('        println("' + r.SUCCESS_MARKER + '")'))
        self.assertIn("if (primary == null) throw failure", source)
        self.assertIn('assertEquals("Requested native parent generation was replaced", stale.message)', source)
        self.assertNotIn("showDirectoryDialog(", source)

    def test_new_phase_and_controller_delegate_owned_cleanup_and_one_deadline_then_refuse_changed_or_exhausted_final_custody(self):
        root, private = Path("/owned-root"), Path("/owned-root/build/ci-verification/new/private")
        selected_budget = budget()
        with mock.patch.object(r.shared, "owned_phase", return_value=good_phase()) as owned, mock.patch.object(r.shared, "read_private_log", return_value="synthetic") as read:
            receipt = {"phases": {}}
            self.assertEqual("synthetic", r.phase(root, private, "inventory", ["synthetic-only"], selected_budget, receipt))
            self.assertEqual(selected_budget, owned.call_args.args[-1])
            self.assertEqual(private, owned.call_args.args[2].parent)
            self.assertEqual(private, owned.call_args.args[3].parent)
            self.assertNotIn("command", receipt["phases"]["inventory"])
            self.assertEqual(1, read.call_count)
        for key, value in (("exit_code", 1), ("capture_complete", False), ("post_exit_group_state", "unknown"),
                           ("post_exit_group_state", "present"), ("stop_reason", "shared-native-deadline-exhausted-or-clock-invalid")):
            with mock.patch.object(r.shared, "owned_phase", return_value={**good_phase(), key: value}), mock.patch.object(r.shared, "read_private_log") as read, self.assertRaises(r.Refusal):
                r.phase(root, private, "junit", ["synthetic-only"], selected_budget, {"phases": {}})
            read.assert_not_called()

        for mode in ("positive", "changed-classpath", "final-deadline", "changed-owned-directory"):
            with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                synthetic_root = Path(directory).resolve()
                clock = [0]
                selected_budget = budget(lambda: clock[0])
                revision, source = "a" * 40, {"synthetic-source": "c" * 64}
                native = {"files": {name: {"sha256": "d" * 64, "size": 1} for name in (r.NATIVE_RESOURCE, r.MANIFEST_RESOURCE)}}
                cp = {"resources": {name: [{"entry_index": 0, "sha256": "d" * 64, "size": 1}] for name in r.REQUIRED_RESOURCES}}
                snapshots = [("synthetic-cp", cp)] * 4
                if mode == "changed-classpath": snapshots[1] = ("synthetic-cp", {**cp, "changed": True})
                calls = []
                def synthetic_phase(root, private, stage, command, passed_budget, receipt):
                    self.assertIs(selected_budget, passed_budget)
                    calls.append(stage)
                    expected = (r.prepare_command(root, private) if stage == "prepare" else
                                r.exact_command(Path("/synthetic-jdk"), "synthetic-cp", root, private, inventory=stage == "inventory"))
                    self.assertEqual(expected, command)
                    if stage == "prepare":
                        (private / "java-tmp/owned-owner-probe").write_bytes(b"owned synthetic temp write")
                        (private / "java-home/.cache/nativecmpkit-filepicker/owned-cache").write_bytes(b"owned synthetic extraction")
                    if stage == "inventory" and mode == "changed-owned-directory":
                        (private / "java-home/.cache/nativecmpkit-filepicker").chmod(0o750)
                    receipt["phases"][stage] = {key: value for key, value in good_phase().items() if key != "command"}
                    if stage == "junit" and mode == "final-deadline": clock[0] = 601
                    return {"prepare": preparation(), "inventory": inventory(), "junit": junit()}[stage]
                stack.enter_context(mock.patch.dict(os.environ, {}, clear=True))
                stack.enter_context(mock.patch.object(r.library, "ROOT", synthetic_root))
                stack.enter_context(mock.patch.object(r, "source_snapshot", return_value=source.copy()))
                stack.enter_context(mock.patch.object(r.library, "git_revision", return_value=revision))
                stack.enter_context(mock.patch.object(r.library.runtime_context, "capture", return_value=runtime(revision)))
                stack.enter_context(mock.patch.object(r, "qualify_jdk", return_value=(Path("/synthetic-jdk"), {"synthetic": "jdk"})))
                stack.enter_context(mock.patch.object(r, "default_version", return_value="0.1.0-SNAPSHOT"))
                stack.enter_context(mock.patch.object(r, "native_identity", return_value=native))
                stack.enter_context(mock.patch.object(r, "classpath_identity", side_effect=snapshots))
                stack.enter_context(mock.patch.object(r, "phase", side_effect=synthetic_phase))
                stack.enter_context(mock.patch.object(r.shared, "NativeBudget", return_value=selected_budget))
                with redirect_stdout(io.StringIO()): result = r.run(Path("build/ci-verification/synthetic"))
                output = synthetic_root / "build/ci-verification/synthetic"
                receipt = json.loads((output / "receipt.json").read_text())
                self.assertEqual(mode == "positive", receipt["passed"])
                self.assertEqual(0 if mode == "positive" else 1, result)
                expected_calls = (["prepare"] if mode == "changed-classpath" else
                                  ["prepare", "inventory"] if mode == "changed-owned-directory" else ["prepare", "inventory", "junit"])
                self.assertEqual(expected_calls, calls)
                self.assertTrue(receipt["owned_java_descriptors_closed"])
                self.assertLessEqual({path.name for path in output.glob("*.json")}, set(r.PUBLIC_FILES))
                if mode == "positive":
                    self.assertTrue(receipt["held_owned_java_directories"])
                    before = json.loads((output / "runtime-before.json").read_text())["owned_java_directories"]
                    after = json.loads((output / "runtime-after.json").read_text())["owned_java_directories"]
                    self.assertEqual(before, after)
                if mode == "final-deadline": self.assertEqual("shared-native-deadline-exhausted-or-clock-invalid", receipt["reason_code"])
                if mode == "changed-owned-directory": self.assertEqual("owned-jvm-directory-must-be-current-owner-only-0700", receipt["reason_code"])

    def test_additive_manual_macos_profile_uploads_only_five_named_json_and_keeps_old_scope_assertions(self):
        workflow = (r.library.ROOT / r.shared.WORKFLOW).read_text()
        self.assertIn("options: [all, picker-jni-macos-domain, native-lock-reproducibility, native-lock-windows-source, picker-jni-actual-jvm2, picker-awt-generation]", workflow)
        job = workflow.split("\n  picker-awt-generation:", 1)[1]
        for required in ("github.repository == 'Apdelrahman1911/nativeCmpkit'", "github.event_name == 'workflow_dispatch'",
                         "inputs.profile == 'picker-awt-generation'", "runs-on: macos-26", "timeout-minutes: 15",
                         "persist-credentials: false", "distribution: temurin", "java-version: '17'", "toolchain: '1.98.0'",
                         "verify-signature: true",
                         "--output build/ci-verification/picker-awt-generation", "if: always()", "retention-days: 7"):
            self.assertIn(required, job)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotRegex(workflow, r"(?m)^\s*[\w-]+:\s*(?:write|write-all)\s*$")
        uploads = job.split("          path: |\n", 1)[1].splitlines()
        self.assertEqual(["            build/ci-verification/picker-awt-generation/" + name for name in r.PUBLIC_FILES], uploads)
        for forbidden in ("unittest", "test_picker_", "PickerActualJvm2Receipts.", "PickerJniPathReceipts.",
                          "matrix:", "cargo test", "--focus actual-jvm2", "--focus macos-domain", "-p test_picker_jni_actual_jvm2.py",
                          "-p test_picker_jni_paths.py", "*.json", "*.log", "**", ".dylib", "target/", "private/", "printenv", "set -x"):
            self.assertNotIn(forbidden, job)
        jvm2 = (r.library.ROOT / "scripts/ci/test_picker_jni_actual_jvm2.py").read_text()
        paths = (r.library.ROOT / "scripts/ci/test_picker_jni_paths.py").read_text()
        self.assertIn('.split("\\n  picker-awt-generation:", 1)[0]', jvm2)
        self.assertIn(".split('\\n  picker-jni-actual-jvm2:', 1)[0]", paths)
        self.assertIn("self.assertNotIn(forbidden, job)", jvm2)
        self.assertIn("self.assertNotIn(forbidden, recovery)", paths)


if __name__ == "__main__":
    unittest.main()
