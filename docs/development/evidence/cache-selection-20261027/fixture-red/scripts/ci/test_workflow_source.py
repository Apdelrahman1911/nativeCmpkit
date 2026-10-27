"""Lexical source guardrails, not a YAML interpreter or proof CI ran successfully."""
import ast
from pathlib import Path
import re
import textwrap
import unittest

import workflow_matrix

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/gradle.yml"


class WorkflowSourceTests(unittest.TestCase):
    def test_each_explicit_python_heredoc_is_syntactically_valid(self):
        source = WORKFLOW.read_text()
        blocks = re.findall(r"(?m)^\s*(?:python3|\"\$PYTHON\") - <<'([A-Z_]+)'\n(.*?)^\s*\1\s*$", source, re.S)
        self.assertGreaterEqual(len(blocks), 5)
        for index, (_, block) in enumerate(blocks):
            with self.subTest(index=index):
                ast.parse(textwrap.dedent(block))

    def test_profile_choices_and_finite_plan_agree(self):
        choices = re.search(r"options: \[([^\n]+)\]", WORKFLOW.read_text()).group(1)
        self.assertEqual(set(workflow_matrix.PROFILES), {value.strip() for value in choices.split(",")})

    def test_instrumentation_uses_the_owned_controller_and_does_not_upload_apks(self):
        source = WORKFLOW.read_text()
        self.assertIn('args=(--api-level "$EMULATOR_API" --output "build/ci-verification/$SLOT")', source)
        self.assertIn('scripts/ci/android_device_tests.py "${args[@]}"', source)
        self.assertIn("/library/*.json", source)
        self.assertIn('"/**/TEST-*.xml"', source)
        upload = source[source.index("- name: Keep receipts and actual selected-task XML"):]
        self.assertNotIn(".apk", upload)
        self.assertNotIn(".aar", upload)
        self.assertNotIn(".jar", upload)

    def test_trusted_host_checkout_disables_implicit_autocrlf_transformations(self):
        source = WORKFLOW.read_text()
        self.assertIn("GIT_CONFIG_COUNT: '1'", source)
        self.assertIn("GIT_CONFIG_KEY_0: core.autocrlf", source)
        self.assertIn("GIT_CONFIG_VALUE_0: 'false'", source)

    def test_failure_capture_keeps_early_native_errors_as_bounded_json_not_binary_uploads(self):
        source = WORKFLOW.read_text()
        self.assertIn('scripts/ci/failure_diagnostics.py --output "build/ci-verification/$SLOT"', source)
        self.assertLess(source.index("scripts/ci/failure_diagnostics.py"),
                        source.index("- name: Keep receipts and actual selected-task XML"))
        upload = source[source.index("- name: Keep receipts and actual selected-task XML"):]
        self.assertIn("/${{ matrix.slot }}/*.json", upload)
        self.assertNotIn("*.pb", upload)
        self.assertNotIn("*.log", upload)

    def test_selected_module_arguments_are_identical_for_discovery_and_execution(self):
        source = WORKFLOW.read_text()
        self.assertIn("TEST_MODULES: ${{ matrix.test-modules }}", source)
        self.assertEqual(3, source.count('for module in "${modules[@]}"; do args+=(--module "$module"); done'))
        self.assertIn('scripts/ci/library_tests.py "${args[@]}" > build/ci-plan/plan.json', source)

    def test_native_desktop_packages_do_not_delay_android_or_browser_suites(self):
        source = WORKFLOW.read_text()
        step = source.split("- name: Linux real UI/native prerequisites", 1)[1].split("- name:", 1)[0]
        self.assertIn("if: runner.os == 'Linux' && matrix.suite == 'desktop'", step)
        self.assertIn("timeout-minutes: 10", step)
        self.assertIn("xvfb xauth", step)

    def test_genuine_uikit_receipt_upload_is_exact_and_does_not_include_apps(self):
        source = WORKFLOW.read_text()
        upload = source[source.index("- name: Keep receipts and actual selected-task XML"):]
        self.assertIn("build/ci-verification/${{ matrix.slot }}/native-ui-application/*/receipt.json", upload)
        self.assertNotIn(".app", upload)
        self.assertNotIn(".kexe", upload)
        self.assertNotIn("native-ui-application/**", upload)

    def test_partial_consumer_job_is_explicit_read_only_bounded_and_not_a_library_matrix_reduction(self):
        source = WORKFLOW.read_text()
        job = source.split("\n  consumer-core-io:\n", 1)[1]
        self.assertIn("if: inputs.profile == 'consumer-core-io'", job)
        self.assertIn("needs: tooling", job)
        self.assertIn("runs-on: ubuntu-24.04", job)
        self.assertIn("--timeout 4200 --reserve-mib 8192", job)
        self.assertIn("scripts/ci/core_io_consumer.py", job)
        self.assertIn("persist-credentials: false", job)
        self.assertNotIn("permissions:", job)
        self.assertNotIn("publish", re.sub(r"#[^\n]*", "", job))
        self.assertNotIn("scripts/ci/library_tests.py run", job)

    def test_partial_consumer_cache_and_upload_never_restore_or_export_producer_outputs(self):
        source = WORKFLOW.read_text()
        job = source.split("\n  consumer-core-io:\n", 1)[1]
        self.assertNotIn("restore-keys:", job)
        self.assertIn("steps.cache-inputs.outputs.digest", job)
        self.assertIn("--scope core-io --output build/ci-runtime/consumer-dependencies.json", job)
        self.assertNotIn("hashFiles(", job)
        self.assertIn("build/ci-consumer-cache/gradle-home/caches/modules-2", job)
        upload = job.split("- name: Keep partial receipts", 1)[1]
        self.assertIn("/junit/TEST-*.xml", upload)
        for pattern in ("verification-repo", ".jar", ".aar", ".apk", ".klib", ".app", ".log", "independent-consumer/**"):
            self.assertNotIn(pattern, upload)

    def test_dependency_caches_use_exact_declaration_runtime_and_slot_not_every_commit(self):
        source = WORKFLOW.read_text()
        keys = re.findall(r"(?m)^\s*key: ([^\n]+)$", source)
        self.assertEqual(2, len(keys))
        for key in keys:
            self.assertNotIn('github.sha', key)
            self.assertNotIn('hashFiles(', key)
            self.assertIn('steps.cache-inputs.outputs.digest', key)
            self.assertIn('steps.runtime.outputs.fingerprint', key)
            self.assertIn('-v2-', key)
        self.assertIn("steps.cache-inputs.outputs.selection", keys[0])
        self.assertNotIn("matrix.test-modules", keys[0])
        self.assertIn('--scope libraries --selection "$TEST_MODULES" --output build/ci-runtime/library-dependencies.json', source)
        self.assertIn('[[ "$selection" =~ ^(all|subset-[0-9a-f]{64})$ ]]', source)
        self.assertNotIn('restore-keys:', source)

    def test_focused_four_runtime_matrix_can_coexist_with_one_native_application_job(self):
        source = WORKFLOW.read_text()
        self.assertIn("max-parallel: " + chr(36) + "{{ inputs.profile == 'navigation-geo-matrix' && 1 || 2 }}", source)
        self.assertIn("fail-fast: false", source)
        self.assertEqual(4, len(workflow_matrix.matrix("navigation-geo-matrix")["include"]))
        self.assertEqual(1, len(workflow_matrix.matrix("ios-ui")["include"]))
        self.assertEqual(11, len(workflow_matrix.matrix("all")["include"]))

    def test_uncached_consumer_home_is_neither_a_cache_nor_uploaded_package_directory(self):
        source = WORKFLOW.read_text()
        job = source.split("\n  consumer-core-io:\n", 1)[1]
        cache = job.split('- name: Exact dependency-input/runtime-keyed producer cache', 1)[1].split('- name:', 1)[0]
        self.assertNotIn('consumer-gradle-home', cache)
        self.assertNotIn('ci-consumer/core-io-desktop', cache)
        self.assertNotIn('consumer-gradle-home', job.split('- name: Keep partial receipts', 1)[1])


if __name__ == "__main__":
    unittest.main()
