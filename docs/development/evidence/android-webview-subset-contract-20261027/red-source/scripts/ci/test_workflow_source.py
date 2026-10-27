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


if __name__ == "__main__":
    unittest.main()
