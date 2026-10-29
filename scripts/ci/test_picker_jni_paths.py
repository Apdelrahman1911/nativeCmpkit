"""Finite Cargo/JVM receipt adversarial fixtures. Zero actual JNI executions."""
import json
import unittest

import picker_jni_paths as r


def positive(host="Linux", interleaved=True):
    methods = r.METHODS if host != "Windows" else r.METHODS[:1]
    artifact = {"reason": "compiler-artifact", "target": {"name": "calf_filepicker_native"},
                "profile": {"test": True}, "executable": "/synthetic/owned/test-executable"}
    lines = [json.dumps(artifact), json.dumps({"reason": "build-finished", "success": True}),
             f"running {len(methods)} tests"]
    for index, method in enumerate(methods):
        if index == 0 and interleaved:
            lines += [f"test jni_path_tests::{method} ... {r.JVM_MARKER}", "ok"]
        else:
            lines.append(f"test jni_path_tests::{method} ... ok")
    if not interleaved:
        lines.insert(2, r.JVM_MARKER)
    lines.append(f"test result: ok. {len(methods)} passed; 0 failed; 0 ignored; 0 measured; 8 filtered out; finished in 0.1s")
    return "\n".join(lines)


class PickerJniPathReceipts(unittest.TestCase):
    def test_actual_marker_can_be_interleaved_with_first_method_without_counting_it_as_a_method(self):
        for host in ("Linux", "Darwin", "Windows"):
            for interleaved in (True, False):
                result = r.review_log(positive(host, interleaved), host)
                self.assertEqual(1 if host == "Windows" else 5, result["tests"])
                self.assertEqual(0, result["skipped"])
                self.assertEqual(8, result["filtered_unchanged_tests"])
                self.assertEqual(17, result["actual_jvm_major"])

    def test_missing_renamed_duplicate_foreign_failed_and_ignored_methods_never_pass(self):
        log = positive()
        first = f"test jni_path_tests::{r.METHODS[0]} ... {r.JVM_MARKER}\nok"
        variants = [log.replace(first, r.JVM_MARKER), log.replace(r.METHODS[0], "foreign_method"),
                    log.replace(first, first + f"\ntest jni_path_tests::{r.METHODS[0]} ... ok"),
                    log + "\ntest jni_path_tests::foreign_method ... ok", log.replace("\nok", "\nFAILED", 1),
                    log.replace("\nok", "\nignored", 1)]
        for changed in variants:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                r.review_log(changed, "Linux")

    def test_zero_inconsistent_duplicate_and_failed_summaries_cannot_certify_tests(self):
        log = positive()
        summary = log.splitlines()[-1]
        for changed in (log.replace("5 passed", "0 passed"), log.replace("0 failed", "1 failed"),
                        log.replace("0 ignored", "1 ignored"), log.replace("0 measured", "1 measured"),
                        log.replace(summary, "test result: FAILED. 5 passed; 1 failed;"), log + "\n" + summary):
            with self.assertRaises(ValueError):
                r.review_log(changed, "Linux")

    def test_missing_or_duplicate_jdk17_and_checker_warnings_fail_closed(self):
        log = positive()
        for changed in (log.replace(r.JVM_MARKER, "wrong-runtime"), log.replace("major=17", "major=21"),
                        log + "\n" + r.JVM_MARKER,
                        *(log + "\n" + error for error in ("WARNING in native method: controlled checker warning",
                          "JNI DETECTED ERROR", "FATAL ERROR in native method", "JNI local refs: 999"))):
            with self.assertRaises(ValueError):
                r.review_log(changed, "Linux")

    def test_compile_only_missing_duplicate_or_failed_executable_messages_are_not_a_pass(self):
        log = positive()
        artifact = log.splitlines()[0]
        variants = [artifact, log.replace(artifact + "\n", ""), log + "\n" + artifact,
                    log.replace('"test": true', '"test": false'), log.replace('"executable":', '"not_an_executable":'),
                    log.replace('"success": true', '"success": false'),
                    log + '\n{"reason": "build-finished", "success": true}', log + "\n{malformed-json}"]
        for changed in variants:
            with self.assertRaises(ValueError):
                r.review_log(changed, "Linux")

    def test_unix_methods_are_not_a_windows_na_waiver_and_unknown_host_and_unbounded_input_are_rejected(self):
        with self.assertRaises(ValueError): r.review_log(positive(), "Windows")
        with self.assertRaises(ValueError): r.review_log(positive("Windows"), "Linux")
        for host in ("FreeBSD", "DarwinWindows", ""):
            with self.assertRaises(ValueError): r.review_log(positive(), host)
        with self.assertRaises(ValueError): r.review_log("x" * (8 * 1024 ** 2 + 1), "Linux")

    def test_failed_owning_method_reports_only_finite_outcomes_coordinates_and_os_error_numbers(self):
        log = (f"test jni_path_tests::{r.METHODS[1]} ... \n"
               "thread 'synthetic' panicked at src/jni_path_tests.rs:81:42:\n"
               'called Result::unwrap() on Err: Os { code: 92, kind: Uncategorized, message: "private diagnostic text" }\n'
               "FAILED\n" + r.JVM_MARKER)
        result = r.failure_details(log)
        self.assertEqual([{"name": r.METHODS[1], "status": "failed"}], result["actual_method_outcomes"])
        self.assertEqual([{"path": "src/jni_path_tests.rs", "line": 81, "column": 42}], result["rust_panic_coordinates"])
        self.assertEqual([{"code": 92, "rust_kind": "Uncategorized"}], result["native_os_error_numbers"])
        self.assertTrue(result["actual_jdk17_marker_observed"])
        self.assertNotIn("private diagnostic text", json.dumps(result))

    def test_failure_diagnostics_never_transplant_foreign_method_names_or_raw_transcripts(self):
        log = ('test jni_path_tests::foreign_private_name ... FAILED\n'
               'thread synthetic panicked at /private/secret/path.rs:99:1:\n'
               'authorization=synthetic-private-value\n' + positive("Windows"))
        result = r.failure_details(log)
        self.assertEqual(1, len(result["actual_method_outcomes"]))
        self.assertEqual([], result["rust_panic_coordinates"])
        for private in ("foreign_private_name", "/private/secret", "authorization", "synthetic-private-value"):
            self.assertNotIn(private, json.dumps(result))
        self.assertTrue(r.failure_details("x" * (8 * 1024 ** 2 + 1))["diagnostic_too_large"])


if __name__ == "__main__": unittest.main()
